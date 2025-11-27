"""Real-time broadcast service for group coordination.

This service manages WebSocket connections and broadcasts events to all
participants in a planning session.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of session events that can be broadcast."""
    PARTICIPANT_JOINED = "participant_joined"
    PARTICIPANT_LEFT = "participant_left"
    VENUE_ADDED = "venue_added"
    VOTE_CAST = "vote_cast"
    ITINERARY_UPDATED = "itinerary_updated"
    ITINERARY_ITEM_ADDED = "itinerary_item_added"
    ITINERARY_ITEM_REMOVED = "itinerary_item_removed"
    COMMENT_ADDED = "comment_added"
    SESSION_FINALIZED = "session_finalized"
    STATE_SYNC = "state_sync"


@dataclass
class SessionEvent:
    """Represents an event that occurred in a planning session."""
    
    event_type: EventType
    session_id: str
    timestamp: datetime
    data: Dict
    participant_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "event_type": self.event_type.value,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "participant_id": self.participant_id,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string for WebSocket transmission."""
        return json.dumps(self.to_dict())


@dataclass
class SessionState:
    """Represents the complete state of a planning session for synchronization."""
    
    session_id: str
    participants: List[Dict]
    venues: List[Dict]
    itinerary: List[Dict]
    votes: Dict[str, List[Dict]]  # venue_id -> list of votes
    comments: Dict[str, List[Dict]]  # venue_id -> list of comments
    status: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "participants": self.participants,
            "venues": self.venues,
            "itinerary": self.itinerary,
            "votes": self.votes,
            "comments": self.comments,
            "status": self.status,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class BroadcastService:
    """
    Service for managing WebSocket connections and broadcasting events.
    
    This service tracks WebSocket connections per session and handles
    real-time event broadcasting to all connected participants.
    
    Validates: Requirements 3.1, 3.4, 6.3
    """
    
    def __init__(self):
        """Initialize the broadcast service."""
        # Track connections: session_id -> participant_id -> WebSocket
        self._connections: Dict[str, Dict[str, WebSocket]] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
    
    async def connect(
        self,
        session_id: str,
        participant_id: str,
        websocket: WebSocket
    ) -> None:
        """
        Register a WebSocket connection for a participant.
        
        Tracks the connection so that events can be broadcast to this
        participant. Multiple connections per participant are not supported;
        a new connection will replace any existing connection.
        
        Args:
            session_id: ID of the planning session
            participant_id: ID of the participant connecting
            websocket: The WebSocket connection
        
        Validates: Requirements 3.1
        """
        async with self._lock:
            if session_id not in self._connections:
                self._connections[session_id] = {}
            
            # Replace any existing connection for this participant
            if participant_id in self._connections[session_id]:
                old_ws = self._connections[session_id][participant_id]
                try:
                    await old_ws.close()
                except Exception as e:
                    logger.warning(
                        f"Error closing old WebSocket for participant {participant_id}: {e}"
                    )
            
            self._connections[session_id][participant_id] = websocket
            
            logger.info(
                f"WebSocket connected: session={session_id}, "
                f"participant={participant_id}, "
                f"total_connections={len(self._connections[session_id])}"
            )
    
    async def disconnect(
        self,
        session_id: str,
        participant_id: str
    ) -> None:
        """
        Remove a WebSocket connection.
        
        Cleans up the connection tracking when a participant disconnects.
        
        Args:
            session_id: ID of the planning session
            participant_id: ID of the participant disconnecting
        
        Validates: Requirements 3.1
        """
        async with self._lock:
            if session_id in self._connections:
                if participant_id in self._connections[session_id]:
                    del self._connections[session_id][participant_id]
                    
                    logger.info(
                        f"WebSocket disconnected: session={session_id}, "
                        f"participant={participant_id}, "
                        f"remaining_connections={len(self._connections[session_id])}"
                    )
                    
                    # Clean up empty session entries
                    if not self._connections[session_id]:
                        del self._connections[session_id]
    
    async def broadcast(
        self,
        session_id: str,
        event: SessionEvent
    ) -> None:
        """
        Broadcast an event to all connected participants in a session.
        
        Sends the event to all WebSocket connections for the given session.
        Failed sends (e.g., due to closed connections) are logged but do not
        prevent other participants from receiving the event.
        
        Args:
            session_id: ID of the planning session
            event: The event to broadcast
        
        Validates: Requirements 3.1, 6.3
        """
        if session_id not in self._connections:
            logger.debug(f"No connections for session {session_id}, skipping broadcast")
            return
        
        # Get a snapshot of connections to avoid holding lock during sends
        async with self._lock:
            connections = dict(self._connections[session_id])
        
        # Prepare the message
        message = event.to_json()
        
        # Track failed connections for cleanup
        failed_participants: Set[str] = set()
        
        # Broadcast to all connected participants
        for participant_id, websocket in connections.items():
            try:
                await websocket.send_text(message)
                logger.debug(
                    f"Broadcast sent: session={session_id}, "
                    f"participant={participant_id}, "
                    f"event_type={event.event_type.value}"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to send to participant {participant_id} "
                    f"in session {session_id}: {e}"
                )
                failed_participants.add(participant_id)
        
        # Clean up failed connections
        if failed_participants:
            async with self._lock:
                for participant_id in failed_participants:
                    if (session_id in self._connections and
                        participant_id in self._connections[session_id]):
                        del self._connections[session_id][participant_id]
                
                # Clean up empty session entries
                if session_id in self._connections and not self._connections[session_id]:
                    del self._connections[session_id]
    
    async def sync_state(
        self,
        session_id: str,
        participant_id: str,
        state: SessionState
    ) -> None:
        """
        Send full session state to a specific participant for reconnection sync.
        
        This is used when a participant reconnects to ensure they have the
        current state of the session.
        
        Args:
            session_id: ID of the planning session
            participant_id: ID of the participant to sync
            state: The complete session state
        
        Validates: Requirements 3.4
        """
        if session_id not in self._connections:
            logger.warning(f"No connections for session {session_id}")
            return
        
        if participant_id not in self._connections[session_id]:
            logger.warning(
                f"Participant {participant_id} not connected to session {session_id}"
            )
            return
        
        websocket = self._connections[session_id][participant_id]
        
        # Create a state sync event
        event = SessionEvent(
            event_type=EventType.STATE_SYNC,
            session_id=session_id,
            timestamp=datetime.now(),
            data=state.to_dict(),
            participant_id=participant_id,
        )
        
        try:
            await websocket.send_text(event.to_json())
            logger.info(
                f"State sync sent: session={session_id}, participant={participant_id}"
            )
        except Exception as e:
            logger.error(
                f"Failed to sync state for participant {participant_id} "
                f"in session {session_id}: {e}"
            )
            # Clean up failed connection
            await self.disconnect(session_id, participant_id)
    
    def get_connected_participants(self, session_id: str) -> List[str]:
        """
        Get list of currently connected participant IDs for a session.
        
        Args:
            session_id: ID of the planning session
        
        Returns:
            List of participant IDs that are currently connected
        """
        if session_id not in self._connections:
            return []
        return list(self._connections[session_id].keys())
    
    def get_connection_count(self, session_id: str) -> int:
        """
        Get the number of active connections for a session.
        
        Args:
            session_id: ID of the planning session
        
        Returns:
            Number of active WebSocket connections
        """
        if session_id not in self._connections:
            return 0
        return len(self._connections[session_id])
