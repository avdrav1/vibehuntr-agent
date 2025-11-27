"""WebSocket API endpoint for group coordination.

This module provides WebSocket endpoint for real-time updates:
- WS /api/planning-sessions/{session_id}/ws - Real-time connection

Requirements: 3.1, 3.4
"""

import logging
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Path, Query
from typing import Optional

from app.event_planning.services.broadcast_service import SessionState
from app.event_planning.services.planning_session_service import SessionNotFoundError

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/planning-sessions", tags=["websocket"])

# Import shared service instances
from app.services.group_coordination import (
    broadcast_service as _broadcast_service,
    session_service as _session_service,
    vote_manager as _vote_manager,
    itinerary_manager as _itinerary_manager,
    comment_service as _comment_service,
)


async def get_session_state(session_id: str) -> SessionState:
    """
    Build the complete session state for synchronization.
    
    Args:
        session_id: ID of the planning session
    
    Returns:
        SessionState with all current data
    """
    # Get session
    session = _session_service.get_session(session_id)
    
    # Get participants
    participants = _session_service.get_participants(session_id)
    participants_data = [
        {
            "id": p.id,
            "session_id": p.session_id,
            "display_name": p.display_name,
            "joined_at": p.joined_at.isoformat(),
            "is_organizer": p.is_organizer,
        }
        for p in participants
    ]
    
    # Get venues
    venues = _vote_manager.get_venues(session_id)
    venues_data = [
        {
            "id": v.id,
            "session_id": v.session_id,
            "place_id": v.place_id,
            "name": v.name,
            "address": v.address,
            "rating": v.rating,
            "price_level": v.price_level,
            "photo_url": v.photo_url,
            "suggested_at": v.suggested_at.isoformat(),
            "suggested_by": v.suggested_by,
        }
        for v in venues
    ]
    
    # Get itinerary
    itinerary = _itinerary_manager.get_itinerary(session_id)
    itinerary_data = [
        {
            "id": item.id,
            "session_id": item.session_id,
            "venue_id": item.venue_id,
            "scheduled_time": item.scheduled_time.isoformat(),
            "added_at": item.added_at.isoformat(),
            "added_by": item.added_by,
            "order": item.order,
        }
        for item in itinerary
    ]
    
    # Get votes for all venues
    votes_data = {}
    for venue in venues:
        tally = _vote_manager.get_votes(session_id, venue.id)
        votes_data[venue.id] = [
            {
                "venue_id": tally.venue_id,
                "upvotes": tally.upvotes,
                "downvotes": tally.downvotes,
                "neutral": tally.neutral,
                "voters": tally.voters,
                "net_score": tally.net_score,
                "total_votes": tally.total_votes,
            }
        ]
    
    # Get comments for all venues
    comments_data = {}
    for venue in venues:
        _comment_service.register_venue(session_id, venue.id)
        comments = _comment_service.get_comments(session_id, venue.id)
        comments_data[venue.id] = [
            {
                "id": c.id,
                "session_id": c.session_id,
                "venue_id": c.venue_id,
                "participant_id": c.participant_id,
                "text": c.text,
                "created_at": c.created_at.isoformat(),
            }
            for c in comments
        ]
    
    return SessionState(
        session_id=session_id,
        participants=participants_data,
        venues=venues_data,
        itinerary=itinerary_data,
        votes=votes_data,
        comments=comments_data,
        status=session.status.value,
    )


@router.websocket("/{session_id}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str = Path(..., description="Planning session ID"),
    participant_id: str = Query(..., description="Participant ID"),
):
    """
    WebSocket endpoint for real-time session updates.
    
    Establishes a WebSocket connection for a participant in a planning session.
    The connection receives real-time updates about:
    - New participants joining
    - Venue options being added
    - Votes being cast
    - Itinerary changes
    - Comments being added
    - Session finalization
    
    On connection, the full session state is sent for synchronization.
    
    Args:
        websocket: The WebSocket connection
        session_id: ID of the planning session
        participant_id: ID of the participant connecting
    
    Requirements:
    - 3.1: Broadcast updates to all connected participants within 2 seconds
    - 3.4: Synchronize full current itinerary state on reconnection
    """
    # Verify session exists
    try:
        _session_service.get_session(session_id)
    except SessionNotFoundError:
        logger.warning(
            f"WebSocket connection rejected: session {session_id} not found"
        )
        await websocket.close(code=1008, reason="Session not found")
        return
    
    # Accept the WebSocket connection
    await websocket.accept()
    
    logger.info(
        f"WebSocket connection accepted: session={session_id}, "
        f"participant={participant_id}"
    )
    
    # Register the connection
    await _broadcast_service.connect(session_id, participant_id, websocket)
    
    try:
        # Send initial state synchronization
        state = await get_session_state(session_id)
        await _broadcast_service.sync_state(session_id, participant_id, state)
        
        logger.info(
            f"Initial state sync sent: session={session_id}, "
            f"participant={participant_id}"
        )
        
        # Keep connection alive and handle incoming messages
        # In this implementation, we primarily use the WebSocket for
        # server-to-client broadcasting, but we keep the connection
        # open to detect disconnections
        while True:
            # Wait for any message from client (mostly just keepalive)
            data = await websocket.receive_text()
            
            # Echo back to confirm connection is alive
            # In a full implementation, you might handle client commands here
            logger.debug(
                f"Received message from participant {participant_id}: {data}"
            )
            
    except WebSocketDisconnect:
        logger.info(
            f"WebSocket disconnected: session={session_id}, "
            f"participant={participant_id}"
        )
    except Exception as e:
        logger.error(
            f"WebSocket error: session={session_id}, "
            f"participant={participant_id}, {type(e).__name__}: {e}",
            exc_info=True
        )
    finally:
        # Clean up the connection
        await _broadcast_service.disconnect(session_id, participant_id)
        logger.info(
            f"WebSocket connection cleaned up: session={session_id}, "
            f"participant={participant_id}"
        )
