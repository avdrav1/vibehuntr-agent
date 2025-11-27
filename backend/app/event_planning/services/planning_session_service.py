"""Planning session service for group coordination.

This service manages the lifecycle of planning sessions including creation,
joining, participant management, and finalization.
"""

import secrets
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.event_planning.models.planning_session import (
    PlanningSession,
    Participant,
    SessionStatus,
)
from app.event_planning.models.session_summary import SessionSummary
from app.event_planning.exceptions import (
    BusinessLogicError,
    EntityNotFoundError,
    ValidationError,
)


class SessionNotFoundError(EntityNotFoundError):
    """Raised when a planning session is not found."""
    
    def __init__(self, session_id: str):
        super().__init__("PlanningSession", session_id)
        self.error_code = "SESSION_NOT_FOUND"


class SessionExpiredError(BusinessLogicError):
    """Raised when an invite link has expired."""
    
    def __init__(self, session_id: str):
        message = f"Invite link for session {session_id} has expired"
        details = {"session_id": session_id}
        super().__init__(message, "SESSION_EXPIRED", details)


class SessionFinalizedError(BusinessLogicError):
    """Raised when attempting to modify a finalized session."""
    
    def __init__(self, session_id: str):
        message = f"Planning session {session_id} has been finalized and cannot be modified"
        details = {"session_id": session_id}
        super().__init__(message, "SESSION_FINALIZED", details)


class InviteRevokedError(BusinessLogicError):
    """Raised when an invite link has been revoked."""
    
    def __init__(self, session_id: str):
        message = f"Invite link for session {session_id} has been revoked"
        details = {"session_id": session_id}
        super().__init__(message, "INVITE_REVOKED", details)


class NotOrganizerError(BusinessLogicError):
    """Raised when a non-organizer attempts an organizer-only action."""
    
    def __init__(self, user_id: str, session_id: str):
        message = f"User {user_id} is not the organizer of session {session_id}"
        details = {"user_id": user_id, "session_id": session_id}
        super().__init__(message, "NOT_ORGANIZER", details)


class DuplicateParticipantError(BusinessLogicError):
    """Raised when a participant is already in the session."""
    
    def __init__(self, participant_id: str, session_id: str):
        message = f"Participant {participant_id} is already in session {session_id}"
        details = {"participant_id": participant_id, "session_id": session_id}
        super().__init__(message, "DUPLICATE_PARTICIPANT", details)


class PlanningSessionService:
    """Service for managing planning sessions with business logic."""
    
    def __init__(self):
        """Initialize the planning session service with in-memory storage."""
        self._sessions: Dict[str, PlanningSession] = {}
        self._sessions_by_token: Dict[str, str] = {}  # token -> session_id
        self._participants: Dict[str, Dict[str, Participant]] = {}  # session_id -> {participant_id -> Participant}
    
    def create_session(
        self,
        organizer_id: str,
        name: str,
        expiry_hours: int = 72
    ) -> PlanningSession:
        """
        Create a new planning session with a unique invite token.
        
        Uses secrets.token_urlsafe(32) for 256-bit cryptographically secure tokens.
        
        Args:
            organizer_id: ID of the user creating the session
            name: Name for the planning session
            expiry_hours: Hours until invite link expires (default 72)
        
        Returns:
            The created PlanningSession
        
        Validates: Requirements 1.1
        """
        session_id = str(uuid.uuid4())
        invite_token = secrets.token_urlsafe(32)  # 256-bit token
        
        now = datetime.now()
        invite_expires_at = now + timedelta(hours=expiry_hours)
        
        session = PlanningSession(
            id=session_id,
            name=name,
            organizer_id=organizer_id,
            invite_token=invite_token,
            invite_expires_at=invite_expires_at,
            invite_revoked=False,
            status=SessionStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            participant_ids=[organizer_id],
        )
        
        session.validate()
        
        # Store session
        self._sessions[session_id] = session
        self._sessions_by_token[invite_token] = session_id
        self._participants[session_id] = {}
        
        # Create organizer as first participant
        organizer_participant = Participant(
            id=organizer_id,
            session_id=session_id,
            display_name=f"Organizer-{organizer_id[:8]}",
            joined_at=now,
            is_organizer=True,
        )
        self._participants[session_id][organizer_id] = organizer_participant
        
        return session

    
    def join_session(
        self,
        invite_token: str,
        display_name: str,
        participant_id: Optional[str] = None
    ) -> Participant:
        """
        Join a session via invite link.
        
        Validates that the token exists, is not expired, and is not revoked.
        
        Args:
            invite_token: The invite token from the shareable link
            display_name: Display name for the participant
            participant_id: Optional ID for the participant (generated if not provided)
        
        Returns:
            The created Participant
        
        Raises:
            SessionNotFoundError: If token doesn't match any session
            SessionExpiredError: If invite link has expired
            InviteRevokedError: If invite link has been revoked
            DuplicateParticipantError: If participant already in session
        
        Validates: Requirements 1.2, 1.3
        """
        # Look up session by token
        session_id = self._sessions_by_token.get(invite_token)
        if session_id is None:
            raise SessionNotFoundError(f"token:{invite_token[:8]}...")
        
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)
        
        # Check if invite is revoked
        if session.invite_revoked:
            raise InviteRevokedError(session_id)
        
        # Check if invite has expired
        if datetime.now() > session.invite_expires_at:
            raise SessionExpiredError(session_id)
        
        # Check if session is finalized
        if session.status == SessionStatus.FINALIZED:
            raise SessionFinalizedError(session_id)
        
        # Generate participant ID if not provided
        if participant_id is None:
            participant_id = str(uuid.uuid4())
        
        # Check for duplicate participant
        if participant_id in self._participants.get(session_id, {}):
            raise DuplicateParticipantError(participant_id, session_id)
        
        # Create participant
        now = datetime.now()
        participant = Participant(
            id=participant_id,
            session_id=session_id,
            display_name=display_name,
            joined_at=now,
            is_organizer=False,
        )
        
        participant.validate()
        
        # Add participant to session
        self._participants[session_id][participant_id] = participant
        session.participant_ids.append(participant_id)
        session.updated_at = now
        
        return participant
    
    def get_session(self, session_id: str) -> PlanningSession:
        """
        Retrieve session by ID.
        
        Args:
            session_id: ID of the session to retrieve
        
        Returns:
            The PlanningSession
        
        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)
        return session
    
    def get_session_by_token(self, invite_token: str) -> PlanningSession:
        """
        Retrieve session by invite token.
        
        Args:
            invite_token: The invite token
        
        Returns:
            The PlanningSession
        
        Raises:
            SessionNotFoundError: If token doesn't match any session
        """
        session_id = self._sessions_by_token.get(invite_token)
        if session_id is None:
            raise SessionNotFoundError(f"token:{invite_token[:8]}...")
        return self.get_session(session_id)

    
    def get_participants(self, session_id: str) -> List[Participant]:
        """
        Get all participants in a session.
        
        Args:
            session_id: ID of the session
        
        Returns:
            List of Participants with their display names
        
        Raises:
            SessionNotFoundError: If session doesn't exist
        
        Validates: Requirements 1.4
        """
        if session_id not in self._sessions:
            raise SessionNotFoundError(session_id)
        
        participants = self._participants.get(session_id, {})
        return list(participants.values())
    
    def revoke_invite(self, session_id: str, organizer_id: str) -> bool:
        """
        Revoke the invite link for a session.
        
        Only the organizer can revoke the invite. Existing participants are preserved.
        
        Args:
            session_id: ID of the session
            organizer_id: ID of the user attempting to revoke
        
        Returns:
            True if revocation was successful
        
        Raises:
            SessionNotFoundError: If session doesn't exist
            NotOrganizerError: If user is not the organizer
        
        Validates: Requirements 1.5
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)
        
        if session.organizer_id != organizer_id:
            raise NotOrganizerError(organizer_id, session_id)
        
        # Revoke the invite (preserves existing participants)
        session.invite_revoked = True
        session.updated_at = datetime.now()
        
        return True
    
    def finalize_session(
        self,
        session_id: str,
        organizer_id: str,
        itinerary_items: Optional[List] = None,
        venues: Optional[List] = None,
    ) -> SessionSummary:
        """
        Finalize the session and generate summary.
        
        Sets the session status to FINALIZED, which prevents any further
        modifications to the session (adding venues, casting votes, adding
        to itinerary, adding comments).
        
        Args:
            session_id: ID of the session to finalize
            organizer_id: ID of the user attempting to finalize
            itinerary_items: Optional list of itinerary items for the summary
            venues: Optional list of venue options for the summary
        
        Returns:
            SessionSummary with all required fields including venues, times,
            addresses, and participant list
        
        Raises:
            SessionNotFoundError: If session doesn't exist
            NotOrganizerError: If user is not the organizer
            SessionFinalizedError: If session is already finalized
        
        Validates: Requirements 3.5, 4.3
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)
        
        if session.organizer_id != organizer_id:
            raise NotOrganizerError(organizer_id, session_id)
        
        if session.status == SessionStatus.FINALIZED:
            raise SessionFinalizedError(session_id)
        
        # Finalize the session - set status to FINALIZED
        now = datetime.now()
        session.status = SessionStatus.FINALIZED
        session.updated_at = now
        
        # Get participants
        participants = self.get_participants(session_id)
        
        # Generate shareable URL
        share_url = self.generate_share_url(session_id)
        
        # Create summary with all required fields
        summary = SessionSummary(
            session_id=session_id,
            session_name=session.name,
            finalized_at=now,
            participants=participants,
            itinerary=itinerary_items or [],
            share_url=share_url,
        )
        
        return summary
    
    def generate_share_url(self, session_id: str) -> str:
        """
        Generate a shareable URL for a session summary.
        
        Args:
            session_id: ID of the session
        
        Returns:
            Shareable URL string
        
        Validates: Requirements 4.5
        """
        return f"https://vibehuntr.app/sessions/{session_id}/summary"
    
    def is_session_finalized(self, session_id: str) -> bool:
        """
        Check if a session is finalized.
        
        Args:
            session_id: ID of the session to check
        
        Returns:
            True if session is finalized, False otherwise
        
        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)
        return session.status == SessionStatus.FINALIZED
    
    def generate_summary(
        self,
        session_id: str,
        itinerary_items: Optional[List] = None,
    ) -> SessionSummary:
        """
        Generate a comprehensive summary for a session.
        
        This method generates a summary that includes all venues, times,
        addresses, and participant list as required by Requirements 4.5.
        
        The summary can be generated for both active and finalized sessions,
        but the share_url is only meaningful for finalized sessions.
        
        Args:
            session_id: ID of the session
            itinerary_items: Optional list of itinerary items to include
        
        Returns:
            SessionSummary with all required fields:
            - session_id and session_name
            - finalized_at timestamp (or current time if not finalized)
            - participants list with display names
            - itinerary with venues, times, and addresses
            - shareable URL
        
        Raises:
            SessionNotFoundError: If session doesn't exist
        
        Validates: Requirements 4.5
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)
        
        # Get participants
        participants = self.get_participants(session_id)
        
        # Determine finalized_at timestamp
        if session.status == SessionStatus.FINALIZED:
            finalized_at = session.updated_at
        else:
            finalized_at = datetime.now()
        
        # Generate shareable URL
        share_url = self.generate_share_url(session_id)
        
        # Create summary with all required fields
        summary = SessionSummary(
            session_id=session_id,
            session_name=session.name,
            finalized_at=finalized_at,
            participants=participants,
            itinerary=itinerary_items or [],
            share_url=share_url,
        )
        
        return summary
