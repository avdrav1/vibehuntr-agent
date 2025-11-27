"""Planning session API endpoints for group coordination.

This module provides REST API endpoints for planning session management:
- POST /api/planning-sessions - Create a new planning session
- GET /api/planning-sessions/{session_id} - Get session details
- POST /api/planning-sessions/join/{token} - Join via invite token
- POST /api/planning-sessions/{session_id}/revoke - Revoke invite link
- POST /api/planning-sessions/{session_id}/finalize - Finalize session

Requirements: 1.1, 1.2, 1.5, 4.3
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Path, Body
from pydantic import BaseModel, Field

from app.event_planning.services.planning_session_service import (
    SessionNotFoundError,
    SessionExpiredError,
    SessionFinalizedError,
    InviteRevokedError,
    NotOrganizerError,
    DuplicateParticipantError,
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/planning-sessions", tags=["planning-sessions"])

# Import shared service instances
from backend.app.services.group_coordination import (
    session_service as _session_service,
    itinerary_manager as _itinerary_manager,
)


# Request/Response Models

class CreateSessionRequest(BaseModel):
    """Request model for creating a planning session."""
    organizer_id: str = Field(..., description="ID of the user creating the session")
    name: str = Field(..., min_length=1, max_length=200, description="Name for the planning session")
    expiry_hours: int = Field(72, ge=1, le=168, description="Hours until invite expires (1-168)")


class SessionResponse(BaseModel):
    """Response model for session details."""
    id: str
    name: str
    organizer_id: str
    invite_token: str
    invite_expires_at: str
    invite_revoked: bool
    status: str
    created_at: str
    updated_at: str
    participant_ids: list[str]


class ParticipantResponse(BaseModel):
    """Response model for participant details."""
    id: str
    session_id: str
    display_name: str
    joined_at: str
    is_organizer: bool


class JoinSessionRequest(BaseModel):
    """Request model for joining a session."""
    display_name: str = Field(..., min_length=1, max_length=50, description="Display name for the participant")
    participant_id: Optional[str] = Field(None, description="Optional participant ID")


class RevokeInviteRequest(BaseModel):
    """Request model for revoking an invite."""
    organizer_id: str = Field(..., description="ID of the organizer")


class FinalizeSessionRequest(BaseModel):
    """Request model for finalizing a session."""
    organizer_id: str = Field(..., description="ID of the organizer")


class SessionSummaryResponse(BaseModel):
    """Response model for session summary."""
    session_id: str
    session_name: str
    finalized_at: str
    participants: list[ParticipantResponse]
    itinerary: list[dict]
    share_url: str


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str
    error_code: str
    details: Optional[dict] = None


# Endpoints

@router.post(
    "",
    response_model=SessionResponse,
    status_code=201,
    responses={
        500: {"model": ErrorResponse, "description": "Session creation failed"},
    },
)
async def create_session(request: CreateSessionRequest) -> SessionResponse:
    """
    Create a new planning session with a unique invite token.
    
    Generates a cryptographically secure invite token and sets the expiry time.
    The organizer is automatically added as the first participant.
    
    Args:
        request: Session creation parameters
    
    Returns:
        SessionResponse with session details including invite token
    
    Raises:
        HTTPException: 500 if session creation fails
    
    Requirements:
    - 1.1: Generate unique invite link with cryptographically secure token
    """
    try:
        logger.info(
            f"Creating planning session: name={request.name}, "
            f"organizer={request.organizer_id}"
        )
        
        session = _session_service.create_session(
            organizer_id=request.organizer_id,
            name=request.name,
            expiry_hours=request.expiry_hours,
        )
        
        logger.info(f"Planning session created: {session.id}")
        
        return SessionResponse(
            id=session.id,
            name=session.name,
            organizer_id=session.organizer_id,
            invite_token=session.invite_token,
            invite_expires_at=session.invite_expires_at.isoformat(),
            invite_revoked=session.invite_revoked,
            status=session.status.value,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            participant_ids=session.participant_ids,
        )
        
    except Exception as e:
        logger.error(
            f"Failed to create planning session: {type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create planning session: {str(e)}"
        )


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
        500: {"model": ErrorResponse, "description": "Failed to retrieve session"},
    },
)
async def get_session(
    session_id: str = Path(..., description="Planning session ID")
) -> SessionResponse:
    """
    Get planning session details by ID.
    
    Args:
        session_id: ID of the planning session
    
    Returns:
        SessionResponse with session details
    
    Raises:
        HTTPException: 404 if session not found, 500 on other errors
    """
    try:
        logger.info(f"Retrieving planning session: {session_id}")
        
        session = _session_service.get_session(session_id)
        
        return SessionResponse(
            id=session.id,
            name=session.name,
            organizer_id=session.organizer_id,
            invite_token=session.invite_token,
            invite_expires_at=session.invite_expires_at.isoformat(),
            invite_revoked=session.invite_revoked,
            status=session.status.value,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            participant_ids=session.participant_ids,
        )
        
    except SessionNotFoundError as e:
        logger.warning(f"Session not found: {session_id}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            f"Failed to retrieve session {session_id}: {type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve session: {str(e)}"
        )


@router.post(
    "/join/{token}",
    response_model=ParticipantResponse,
    status_code=201,
    responses={
        404: {"model": ErrorResponse, "description": "Invalid or expired invite token"},
        400: {"model": ErrorResponse, "description": "Invite revoked or session finalized"},
        409: {"model": ErrorResponse, "description": "Participant already in session"},
        500: {"model": ErrorResponse, "description": "Failed to join session"},
    },
)
async def join_session(
    token: str = Path(..., description="Invite token from shareable link"),
    request: JoinSessionRequest = Body(...),
) -> ParticipantResponse:
    """
    Join a planning session via invite token.
    
    Validates that the token exists, is not expired, and is not revoked.
    Creates a new participant record with the provided display name.
    
    Args:
        token: Invite token from the shareable link
        request: Join session parameters including display name
    
    Returns:
        ParticipantResponse with participant details
    
    Raises:
        HTTPException: 404 if token invalid/expired, 400 if revoked/finalized,
                      409 if duplicate, 500 on other errors
    
    Requirements:
    - 1.2: Allow user to join as participant with display name
    - 1.3: Display error message for expired links
    """
    try:
        logger.info(
            f"Joining session via token: token={token[:8]}..., "
            f"display_name={request.display_name}"
        )
        
        participant = _session_service.join_session(
            invite_token=token,
            display_name=request.display_name,
            participant_id=request.participant_id,
        )
        
        logger.info(
            f"Participant joined session: participant={participant.id}, "
            f"session={participant.session_id}"
        )
        
        return ParticipantResponse(
            id=participant.id,
            session_id=participant.session_id,
            display_name=participant.display_name,
            joined_at=participant.joined_at.isoformat(),
            is_organizer=participant.is_organizer,
        )
        
    except SessionNotFoundError as e:
        logger.warning(f"Invalid invite token: {token[:8]}...")
        raise HTTPException(
            status_code=404,
            detail="Invalid or expired invite link"
        )
    except SessionExpiredError as e:
        logger.warning(f"Expired invite token: {token[:8]}...")
        raise HTTPException(
            status_code=404,
            detail="This invite link has expired"
        )
    except InviteRevokedError as e:
        logger.warning(f"Revoked invite token: {token[:8]}...")
        raise HTTPException(
            status_code=400,
            detail="This invite link has been revoked"
        )
    except SessionFinalizedError as e:
        logger.warning(f"Session finalized: {e.details.get('session_id')}")
        raise HTTPException(
            status_code=400,
            detail="This planning session has been finalized and is no longer accepting new participants"
        )
    except DuplicateParticipantError as e:
        logger.warning(
            f"Duplicate participant: {e.details.get('participant_id')}"
        )
        raise HTTPException(
            status_code=409,
            detail="You are already a participant in this session"
        )
    except Exception as e:
        logger.error(
            f"Failed to join session: {type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to join session: {str(e)}"
        )


@router.post(
    "/{session_id}/revoke",
    status_code=204,
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
        403: {"model": ErrorResponse, "description": "Not authorized (not organizer)"},
        500: {"model": ErrorResponse, "description": "Failed to revoke invite"},
    },
)
async def revoke_invite(
    session_id: str = Path(..., description="Planning session ID"),
    request: RevokeInviteRequest = Body(...),
) -> None:
    """
    Revoke the invite link for a planning session.
    
    Only the organizer can revoke the invite. Existing participants are preserved.
    
    Args:
        session_id: ID of the planning session
        request: Revoke parameters including organizer ID
    
    Returns:
        None: 204 No Content on success
    
    Raises:
        HTTPException: 404 if session not found, 403 if not organizer,
                      500 on other errors
    
    Requirements:
    - 1.5: Invalidate link and prevent new joins while preserving existing participants
    """
    try:
        logger.info(
            f"Revoking invite: session={session_id}, "
            f"organizer={request.organizer_id}"
        )
        
        _session_service.revoke_invite(
            session_id=session_id,
            organizer_id=request.organizer_id,
        )
        
        logger.info(f"Invite revoked: session={session_id}")
        # Return 204 No Content
        
    except SessionNotFoundError as e:
        logger.warning(f"Session not found: {session_id}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except NotOrganizerError as e:
        logger.warning(
            f"Not organizer: user={request.organizer_id}, session={session_id}"
        )
        raise HTTPException(
            status_code=403,
            detail="Only the organizer can revoke the invite link"
        )
    except Exception as e:
        logger.error(
            f"Failed to revoke invite for session {session_id}: "
            f"{type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to revoke invite: {str(e)}"
        )


@router.post(
    "/{session_id}/finalize",
    response_model=SessionSummaryResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
        403: {"model": ErrorResponse, "description": "Not authorized (not organizer)"},
        400: {"model": ErrorResponse, "description": "Session already finalized"},
        500: {"model": ErrorResponse, "description": "Failed to finalize session"},
    },
)
async def finalize_session(
    session_id: str = Path(..., description="Planning session ID"),
    request: FinalizeSessionRequest = Body(...),
) -> SessionSummaryResponse:
    """
    Finalize the planning session and generate summary.
    
    Sets the session status to FINALIZED, which prevents any further modifications.
    Generates a comprehensive summary with all venues, times, addresses, and participants.
    
    Args:
        session_id: ID of the planning session
        request: Finalize parameters including organizer ID
    
    Returns:
        SessionSummaryResponse with complete session summary
    
    Raises:
        HTTPException: 404 if session not found, 403 if not organizer,
                      400 if already finalized, 500 on other errors
    
    Requirements:
    - 4.3: Lock session and generate shareable summary
    """
    try:
        logger.info(
            f"Finalizing session: session={session_id}, "
            f"organizer={request.organizer_id}"
        )
        
        # Get itinerary items for the summary
        itinerary_items = _itinerary_manager.get_itinerary(session_id)
        
        # Finalize the session
        summary = _session_service.finalize_session(
            session_id=session_id,
            organizer_id=request.organizer_id,
            itinerary_items=itinerary_items,
        )
        
        logger.info(f"Session finalized: {session_id}")
        
        # Convert participants to response format
        participants = [
            ParticipantResponse(
                id=p.id,
                session_id=p.session_id,
                display_name=p.display_name,
                joined_at=p.joined_at.isoformat(),
                is_organizer=p.is_organizer,
            )
            for p in summary.participants
        ]
        
        # Convert itinerary items to dict format
        itinerary = [item.to_dict() for item in summary.itinerary]
        
        return SessionSummaryResponse(
            session_id=summary.session_id,
            session_name=summary.session_name,
            finalized_at=summary.finalized_at.isoformat(),
            participants=participants,
            itinerary=itinerary,
            share_url=summary.share_url,
        )
        
    except SessionNotFoundError as e:
        logger.warning(f"Session not found: {session_id}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except NotOrganizerError as e:
        logger.warning(
            f"Not organizer: user={request.organizer_id}, session={session_id}"
        )
        raise HTTPException(
            status_code=403,
            detail="Only the organizer can finalize the session"
        )
    except SessionFinalizedError as e:
        logger.warning(f"Session already finalized: {session_id}")
        raise HTTPException(
            status_code=400,
            detail="This session has already been finalized"
        )
    except Exception as e:
        logger.error(
            f"Failed to finalize session {session_id}: "
            f"{type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to finalize session: {str(e)}"
        )
