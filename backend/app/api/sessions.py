"""Session API endpoints for managing conversation sessions.

This module provides REST API endpoints for session management:
- POST /api/sessions: Create a new session
- GET /api/sessions/{session_id}/messages: Get message history
- DELETE /api/sessions/{session_id}: Clear session history

Requirements: 3.1, 3.5, 4.3, 4.4, 4.5
"""

import logging
import uuid
from fastapi import APIRouter, HTTPException, Path

from backend.app.models.schemas import (
    SessionResponse,
    MessagesResponse,
    ErrorResponse,
)
from backend.app.services.session_manager import session_manager


# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post(
    "",
    response_model=SessionResponse,
    status_code=201,
    responses={
        500: {"model": ErrorResponse, "description": "Session creation failed"},
    },
)
async def create_session() -> SessionResponse:
    """
    Create a new conversation session.
    
    This endpoint generates a unique session ID and initializes an empty
    message history. The session ID should be used in subsequent chat
    requests to maintain conversation context.
    
    Returns:
        SessionResponse: Contains the newly created session_id
        
    Raises:
        HTTPException: 500 if session creation fails
        
    Requirements:
    - 3.1: Backend creates unique session ID when new conversation starts
    - 4.4: POST /api/sessions endpoint for creating new sessions
    """
    try:
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        logger.info(f"Creating new session: {session_id}")
        
        # Create session in session manager
        session_manager.create_session(session_id)
        
        # Also create session in ADK session service so agent_invoker can use it
        try:
            from app.event_planning.agent_invoker import _session_service
            _session_service.create_session_sync(
                session_id=session_id,
                user_id="web_user",
                app_name="vibehuntr_playground"
            )
            logger.debug(f"Created ADK session: {session_id}")
        except Exception as adk_error:
            logger.warning(
                f"Failed to create ADK session (will be created on first use): {adk_error}"
            )
        
        logger.info(f"Session created successfully: {session_id}")
        return SessionResponse(session_id=session_id)
        
    except Exception as e:
        logger.error(
            f"Failed to create session: {type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get(
    "/{session_id}/messages",
    response_model=MessagesResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
        500: {"model": ErrorResponse, "description": "Failed to retrieve messages"},
    },
)
async def get_messages(
    session_id: str = Path(..., description="Session identifier")
) -> MessagesResponse:
    """
    Get all messages for a session.
    
    This endpoint retrieves the complete message history for a given session,
    including both user and assistant messages with timestamps.
    
    Args:
        session_id: Unique identifier for the session
        
    Returns:
        MessagesResponse: List of all messages in the session
        
    Raises:
        HTTPException: 404 if session doesn't exist, 500 on other errors
        
    Requirements:
    - 3.4: Backend returns all messages for session when user requests history
    - 4.3: GET /api/sessions/{session_id}/messages endpoint for history
    """
    try:
        logger.info(f"Retrieving messages for session: {session_id}")
        
        # Check if session exists
        if not session_manager.session_exists(session_id):
            logger.warning(f"Session not found: {session_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        # Get messages from session manager
        messages = session_manager.get_messages(session_id)
        
        logger.info(
            f"Retrieved {len(messages)} messages for session {session_id}"
        )
        return MessagesResponse(messages=messages)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            f"Failed to retrieve messages for session {session_id}: "
            f"{type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve messages: {str(e)}"
        )


@router.delete(
    "/{session_id}",
    status_code=204,
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
        500: {"model": ErrorResponse, "description": "Failed to clear session"},
    },
)
async def clear_session(
    session_id: str = Path(..., description="Session identifier")
) -> None:
    """
    Clear a session's message history.
    
    This endpoint removes all messages from a session while keeping the
    session ID valid. This is useful for starting a new conversation
    without creating a new session.
    
    Args:
        session_id: Unique identifier for the session
        
    Returns:
        None: 204 No Content on success
        
    Raises:
        HTTPException: 404 if session doesn't exist, 500 on other errors
        
    Requirements:
    - 3.5: Backend creates new session ID when user starts new conversation
    - 4.5: DELETE /api/sessions/{session_id} endpoint for clearing sessions
    """
    try:
        logger.info(f"Clearing session: {session_id}")
        
        # Check if session exists
        if not session_manager.session_exists(session_id):
            logger.warning(f"Session not found: {session_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        # Clear session history
        session_manager.clear_session(session_id)
        
        logger.info(f"Session cleared successfully: {session_id}")
        # Return 204 No Content (no response body)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            f"Failed to clear session {session_id}: "
            f"{type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear session: {str(e)}"
        )
