"""Session coordinator for group coordination.

This service coordinates between all group coordination services and provides
unified access to session state for synchronization.
"""

from typing import Optional

from app.event_planning.services.planning_session_service import PlanningSessionService
from app.event_planning.services.vote_manager import VoteManager
from app.event_planning.services.itinerary_manager import ItineraryManager
from app.event_planning.services.comment_service import CommentService
from app.event_planning.services.broadcast_service import (
    BroadcastService,
    SessionState,
)


class SessionCoordinator:
    """
    Coordinator service that manages all group coordination services.
    
    This service provides a unified interface for accessing session state
    and coordinates real-time updates across all services.
    
    Validates: Requirements 3.4
    """
    
    def __init__(
        self,
        session_service: Optional[PlanningSessionService] = None,
        vote_manager: Optional[VoteManager] = None,
        itinerary_manager: Optional[ItineraryManager] = None,
        comment_service: Optional[CommentService] = None,
        broadcast_service: Optional[BroadcastService] = None,
    ):
        """
        Initialize the session coordinator.
        
        Args:
            session_service: Planning session service
            vote_manager: Vote manager service
            itinerary_manager: Itinerary manager service
            comment_service: Comment service
            broadcast_service: Broadcast service for real-time updates
        """
        self.session_service = session_service or PlanningSessionService()
        self.broadcast_service = broadcast_service or BroadcastService()
        self.vote_manager = vote_manager or VoteManager(self.broadcast_service)
        self.itinerary_manager = itinerary_manager or ItineraryManager(self.broadcast_service)
        self.comment_service = comment_service or CommentService(self.broadcast_service)
    
    def get_session_state(self, session_id: str) -> SessionState:
        """
        Get the complete state of a planning session.
        
        This method gathers state from all services to provide a complete
        snapshot of the session for synchronization purposes.
        
        Args:
            session_id: ID of the planning session
        
        Returns:
            SessionState with all session data
        
        Validates: Requirements 3.4
        """
        # Get session info
        session = self.session_service.get_session(session_id)
        
        # Get participants
        participants = self.session_service.get_participants(session_id)
        participants_data = [p.to_dict() for p in participants]
        
        # Get venues
        venues = self.vote_manager.get_venues(session_id)
        venues_data = [v.to_dict() for v in venues]
        
        # Get itinerary
        itinerary = self.itinerary_manager.get_itinerary(session_id)
        itinerary_data = [item.to_dict() for item in itinerary]
        
        # Get votes for all venues
        votes_data = {}
        for venue in venues:
            tally = self.vote_manager.get_votes(session_id, venue.id)
            votes_data[venue.id] = tally.to_dict()
        
        # Get comments for all venues
        comments_data = {}
        for venue in venues:
            comments = self.comment_service.get_comments(session_id, venue.id)
            comments_data[venue.id] = [c.to_dict() for c in comments]
        
        return SessionState(
            session_id=session_id,
            participants=participants_data,
            venues=venues_data,
            itinerary=itinerary_data,
            votes=votes_data,
            comments=comments_data,
            status=session.status.value,
        )
    
    async def sync_participant(
        self,
        session_id: str,
        participant_id: str
    ) -> None:
        """
        Synchronize a participant's state after reconnection.
        
        This method gathers the full session state and sends it to the
        participant via the broadcast service.
        
        Args:
            session_id: ID of the planning session
            participant_id: ID of the participant to sync
        
        Validates: Requirements 3.4
        """
        state = self.get_session_state(session_id)
        await self.broadcast_service.sync_state(session_id, participant_id, state)
