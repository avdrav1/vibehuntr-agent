"""Comment service for group coordination.

This service handles comments on venue options including adding comments
with validation and retrieving comments in chronological order.
"""

import uuid
from datetime import datetime
from typing import Dict, List

from app.event_planning.models.itinerary import Comment, COMMENT_MAX_LENGTH
from app.event_planning.models.planning_session import SessionStatus
from app.event_planning.exceptions import (
    BusinessLogicError,
    EntityNotFoundError,
    ValidationError,
)


class VenueNotFoundError(EntityNotFoundError):
    """Raised when a venue option is not found."""
    
    def __init__(self, venue_id: str):
        super().__init__("VenueOption", venue_id)
        self.error_code = "VENUE_NOT_FOUND"


class SessionFinalizedError(BusinessLogicError):
    """Raised when attempting to modify a finalized session."""
    
    def __init__(self, session_id: str):
        message = f"Planning session {session_id} has been finalized and cannot be modified"
        details = {"session_id": session_id}
        super().__init__(message, "SESSION_FINALIZED", details)


class CommentTooLongError(ValidationError):
    """Raised when a comment exceeds the character limit."""
    
    def __init__(self, length: int):
        message = f"Comment exceeds maximum length of {COMMENT_MAX_LENGTH} characters (got {length})"
        details = {"max_length": COMMENT_MAX_LENGTH, "actual_length": length}
        super().__init__(message, "text", details)
        self.error_code = "COMMENT_TOO_LONG"


class CommentService:
    """Service for managing comments on venue options."""
    
    def __init__(self, broadcast_service=None):
        """
        Initialize the comment service with in-memory storage.
        
        Args:
            broadcast_service: Optional BroadcastService for real-time updates
        """
        # session_id -> {venue_id -> [Comment]}
        self._comments: Dict[str, Dict[str, List[Comment]]] = {}
        # session_id -> SessionStatus (for finalization checks)
        self._session_status: Dict[str, SessionStatus] = {}
        # session_id -> set of venue_ids (to track valid venues)
        self._venues: Dict[str, set] = {}
        # Optional broadcast service for real-time updates
        self._broadcast_service = broadcast_service
    
    def set_session_status(self, session_id: str, status: SessionStatus) -> None:
        """Set the session status for finalization checks."""
        self._session_status[session_id] = status
    
    def register_venue(self, session_id: str, venue_id: str) -> None:
        """Register a venue as valid for comments."""
        if session_id not in self._venues:
            self._venues[session_id] = set()
        self._venues[session_id].add(venue_id)
    
    def _check_session_not_finalized(self, session_id: str) -> None:
        """Check if session is finalized and raise error if so."""
        status = self._session_status.get(session_id, SessionStatus.ACTIVE)
        if status == SessionStatus.FINALIZED:
            raise SessionFinalizedError(session_id)
    
    def _check_venue_exists(self, session_id: str, venue_id: str) -> None:
        """Check if venue exists and raise error if not."""
        venues = self._venues.get(session_id, set())
        if venue_id not in venues:
            raise VenueNotFoundError(venue_id)
    
    def add_comment(
        self,
        session_id: str,
        venue_id: str,
        participant_id: str,
        text: str,
        comment_id: str | None = None,
        created_at: datetime | None = None,
    ) -> Comment:
        """
        Add a comment to a venue.
        
        Validates the 500 character limit and stores the comment with
        participant name and timestamp.
        
        Args:
            session_id: ID of the planning session
            venue_id: ID of the venue to comment on
            participant_id: ID of the participant adding the comment
            text: Comment text (max 500 characters)
            comment_id: Optional comment ID (generated if not provided)
            created_at: Optional creation timestamp (uses current time if not provided)
        
        Returns:
            The created Comment
        
        Raises:
            SessionFinalizedError: If session is finalized
            VenueNotFoundError: If venue doesn't exist
            CommentTooLongError: If comment exceeds 500 characters
        
        Validates: Requirements 6.1, 6.4
        """
        self._check_session_not_finalized(session_id)
        self._check_venue_exists(session_id, venue_id)
        
        # Validate character limit
        if len(text) > COMMENT_MAX_LENGTH:
            raise CommentTooLongError(len(text))
        
        # Generate comment ID if not provided
        if comment_id is None:
            comment_id = str(uuid.uuid4())
        
        # Use current time if not provided
        if created_at is None:
            created_at = datetime.now()
        
        comment = Comment(
            id=comment_id,
            session_id=session_id,
            venue_id=venue_id,
            participant_id=participant_id,
            text=text,
            created_at=created_at,
        )
        
        # Validate the comment (this also checks for empty text)
        comment.validate()
        
        # Initialize storage if needed
        if session_id not in self._comments:
            self._comments[session_id] = {}
        if venue_id not in self._comments[session_id]:
            self._comments[session_id][venue_id] = []
        
        # Store comment
        self._comments[session_id][venue_id].append(comment)
        
        # Broadcast comment added event if broadcast service is available
        if self._broadcast_service is not None:
            import asyncio
            from app.event_planning.services.broadcast_service import SessionEvent, EventType
            event = SessionEvent(
                event_type=EventType.COMMENT_ADDED,
                session_id=session_id,
                timestamp=created_at,
                data={
                    "comment": comment.to_dict(),
                    "venue_id": venue_id,
                },
                participant_id=participant_id,
            )
            # Run broadcast in background if in async context
            try:
                asyncio.create_task(self._broadcast_service.broadcast(session_id, event))
            except RuntimeError:
                # Not in async context, skip broadcast
                pass
        
        return comment
    
    def get_comments(self, session_id: str, venue_id: str) -> List[Comment]:
        """
        Get comments for a venue in chronological order.
        
        Returns comments sorted by created_at timestamp in ascending order.
        
        Args:
            session_id: ID of the planning session
            venue_id: ID of the venue
        
        Returns:
            List of Comments sorted by created_at ascending
        
        Raises:
            VenueNotFoundError: If venue doesn't exist
        
        Validates: Requirements 6.2
        """
        self._check_venue_exists(session_id, venue_id)
        
        comments = self._comments.get(session_id, {}).get(venue_id, [])
        
        # Sort by created_at ascending (chronological order)
        return sorted(comments, key=lambda c: c.created_at)
