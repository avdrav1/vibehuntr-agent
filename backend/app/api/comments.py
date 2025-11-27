"""Comments API endpoints for group coordination.

This module provides REST API endpoints for venue comments:
- POST /api/planning-sessions/{session_id}/venues/{venue_id}/comments - Add comment
- GET /api/planning-sessions/{session_id}/venues/{venue_id}/comments - Get comments

Requirements: 6.1, 6.2
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Path, Body
from pydantic import BaseModel, Field

from app.event_planning.models.itinerary import COMMENT_MAX_LENGTH
from app.event_planning.services.comment_service import (
    VenueNotFoundError,
    SessionFinalizedError,
    CommentTooLongError,
)
from app.event_planning.services.planning_session_service import (
    SessionNotFoundError,
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/planning-sessions", tags=["comments"])

# Import shared service instances
from ..services.group_coordination import (
    comment_service as _comment_service,
    session_service as _session_service,
)


# Request/Response Models

class AddCommentRequest(BaseModel):
    """Request model for adding a comment."""
    participant_id: str = Field(..., description="ID of the participant adding the comment")
    text: str = Field(
        ...,
        min_length=1,
        max_length=COMMENT_MAX_LENGTH,
        description=f"Comment text (max {COMMENT_MAX_LENGTH} characters)"
    )


class CommentResponse(BaseModel):
    """Response model for comment details."""
    id: str
    session_id: str
    venue_id: str
    participant_id: str
    text: str
    created_at: str


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str
    error_code: str
    details: Optional[dict] = None


# Endpoints

@router.post(
    "/{session_id}/venues/{venue_id}/comments",
    response_model=CommentResponse,
    status_code=201,
    responses={
        404: {"model": ErrorResponse, "description": "Session or venue not found"},
        400: {"model": ErrorResponse, "description": "Session finalized or comment too long"},
        500: {"model": ErrorResponse, "description": "Failed to add comment"},
    },
)
async def add_comment(
    session_id: str = Path(..., description="Planning session ID"),
    venue_id: str = Path(..., description="Venue ID"),
    request: AddCommentRequest = Body(...),
) -> CommentResponse:
    """
    Add a comment to a venue.
    
    Validates the 500 character limit and stores the comment with
    participant name and timestamp. The comment is broadcast to all
    connected participants.
    
    Args:
        session_id: ID of the planning session
        venue_id: ID of the venue to comment on
        request: Comment details including participant ID and text
    
    Returns:
        CommentResponse with comment details
    
    Raises:
        HTTPException: 404 if session/venue not found, 400 if finalized or too long,
                      500 on other errors
    
    Requirements:
    - 6.1: Display comment with participant name and timestamp
    - 6.4: Reject comments exceeding 500 characters
    """
    try:
        logger.info(
            f"Adding comment: session={session_id}, venue={venue_id}, "
            f"participant={request.participant_id}, length={len(request.text)}"
        )
        
        # Verify session exists and set status
        try:
            session = _session_service.get_session(session_id)
            _comment_service.set_session_status(session_id, session.status)
        except SessionNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        # Register venue (this allows comment service to validate venue exists)
        _comment_service.register_venue(session_id, venue_id)
        
        comment = _comment_service.add_comment(
            session_id=session_id,
            venue_id=venue_id,
            participant_id=request.participant_id,
            text=request.text,
        )
        
        logger.info(f"Comment added: {comment.id}")
        
        return CommentResponse(
            id=comment.id,
            session_id=comment.session_id,
            venue_id=comment.venue_id,
            participant_id=comment.participant_id,
            text=comment.text,
            created_at=comment.created_at.isoformat(),
        )
        
    except VenueNotFoundError as e:
        logger.warning(f"Venue not found: {venue_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Venue {venue_id} not found in session {session_id}"
        )
    except SessionFinalizedError as e:
        logger.warning(f"Session finalized: {session_id}")
        raise HTTPException(
            status_code=400,
            detail="This session has been finalized and cannot be modified"
        )
    except CommentTooLongError as e:
        logger.warning(
            f"Comment too long: {e.details.get('actual_length')} characters"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Comment exceeds maximum length of {COMMENT_MAX_LENGTH} characters"
        )
    except Exception as e:
        logger.error(
            f"Failed to add comment: session={session_id}, venue={venue_id}, "
            f"{type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add comment: {str(e)}"
        )


@router.get(
    "/{session_id}/venues/{venue_id}/comments",
    response_model=list[CommentResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Session or venue not found"},
        500: {"model": ErrorResponse, "description": "Failed to retrieve comments"},
    },
)
async def get_comments(
    session_id: str = Path(..., description="Planning session ID"),
    venue_id: str = Path(..., description="Venue ID"),
) -> list[CommentResponse]:
    """
    Get comments for a venue in chronological order.
    
    Returns all comments for the venue sorted by created_at timestamp
    in ascending order (oldest first).
    
    Args:
        session_id: ID of the planning session
        venue_id: ID of the venue
    
    Returns:
        List of CommentResponse sorted by created_at
    
    Raises:
        HTTPException: 404 if session/venue not found, 500 on other errors
    
    Requirements:
    - 6.2: Display comments in chronological order
    """
    try:
        logger.info(f"Retrieving comments: session={session_id}, venue={venue_id}")
        
        # Verify session exists
        try:
            _session_service.get_session(session_id)
        except SessionNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        # Register venue (this allows comment service to validate venue exists)
        _comment_service.register_venue(session_id, venue_id)
        
        # Get comments (already sorted chronologically)
        comments = _comment_service.get_comments(session_id, venue_id)
        
        result = [
            CommentResponse(
                id=comment.id,
                session_id=comment.session_id,
                venue_id=comment.venue_id,
                participant_id=comment.participant_id,
                text=comment.text,
                created_at=comment.created_at.isoformat(),
            )
            for comment in comments
        ]
        
        logger.info(f"Retrieved {len(result)} comments")
        
        return result
        
    except VenueNotFoundError as e:
        logger.warning(f"Venue not found: {venue_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Venue {venue_id} not found in session {session_id}"
        )
    except Exception as e:
        logger.error(
            f"Failed to retrieve comments: session={session_id}, venue={venue_id}, "
            f"{type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve comments: {str(e)}"
        )
