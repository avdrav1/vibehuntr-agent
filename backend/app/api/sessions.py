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

from ..models.schemas import (
    SessionResponse,
    MessagesResponse,
    ErrorResponse,
    SessionListResponse,
    SessionSummary,
    DeleteSessionResponse,
)
from ..services.session_manager import session_manager


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
    "",
    response_model=SessionListResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Failed to retrieve sessions"},
    },
)
async def list_sessions() -> SessionListResponse:
    """
    List all conversation sessions.
    
    This endpoint returns a list of all sessions with preview, timestamp,
    and message count for each. Sessions are sorted by timestamp descending
    (newest first).
    
    Returns:
        SessionListResponse: List of session summaries
        
    Raises:
        HTTPException: 500 if retrieval fails
        
    Requirements:
    - 1.1: Display a collapsible sidebar showing a list of past conversation sessions
    - 1.4: Show a preview of the first message and the session timestamp
    """
    try:
        logger.info("Retrieving all sessions")
        
        # Get all session summaries from session manager
        session_data = session_manager.get_all_sessions()
        
        # Convert to SessionSummary models
        sessions = [
            SessionSummary(
                id=s["id"],
                preview=s["preview"],
                timestamp=s["timestamp"],
                messageCount=s["messageCount"]
            )
            for s in session_data
        ]
        
        logger.info(f"Retrieved {len(sessions)} sessions")
        return SessionListResponse(sessions=sessions)
        
    except Exception as e:
        logger.error(
            f"Failed to retrieve sessions: {type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve sessions: {str(e)}"
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
        
        # Get messages from ADK session service (the source of truth)
        # The ADK session service automatically stores all messages during agent invocation
        try:
            from app.event_planning.agent_invoker import _session_service
            adk_session = _session_service.get_session_sync(
                session_id=session_id,
                app_name="vibehuntr_playground",
                user_id="web_user"
            )
            
            # Convert ADK messages to our format
            messages = []
            if hasattr(adk_session, 'history') and adk_session.history:
                for msg in adk_session.history:
                    # ADK stores messages as Content objects with parts
                    role = msg.role if hasattr(msg, 'role') else 'unknown'
                    content_text = ''
                    if hasattr(msg, 'parts') and msg.parts:
                        # Extract text from all parts
                        content_text = ''.join(
                            part.text for part in msg.parts 
                            if hasattr(part, 'text') and part.text
                        )
                    
                    messages.append({
                        'role': role,
                        'content': content_text,
                        'timestamp': ''  # ADK doesn't store timestamps
                    })
            
            logger.info(
                f"Retrieved {len(messages)} messages from ADK session {session_id}"
            )
        except Exception as adk_error:
            logger.warning(
                f"Failed to get messages from ADK session, falling back to session_manager: {adk_error}"
            )
            # Fallback to session_manager if ADK fails
            messages = session_manager.get_messages(session_id)
            logger.info(
                f"Retrieved {len(messages)} messages from session_manager for {session_id}"
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
    response_model=DeleteSessionResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
        500: {"model": ErrorResponse, "description": "Failed to delete session"},
    },
)
async def delete_session(
    session_id: str = Path(..., description="Session identifier")
) -> DeleteSessionResponse:
    """
    Delete a session completely.
    
    This endpoint removes the session and all its messages from storage.
    The session ID will no longer be valid after deletion.
    
    Args:
        session_id: Unique identifier for the session
        
    Returns:
        DeleteSessionResponse: Success status
        
    Raises:
        HTTPException: 404 if session doesn't exist, 500 on other errors
        
    Requirements:
    - 1.6: Remove the session from the list and delete its data from storage
    """
    try:
        logger.info(f"Deleting session: {session_id}")
        
        # Check if session exists
        if not session_manager.session_exists(session_id):
            logger.warning(f"Session not found: {session_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        # Delete session completely
        success = session_manager.delete_session(session_id)
        
        # Also try to delete from ADK session service
        try:
            from app.event_planning.agent_invoker import _session_service
            _session_service.delete_session_sync(
                session_id=session_id,
                app_name="vibehuntr_playground",
                user_id="web_user"
            )
            logger.debug(f"Deleted ADK session: {session_id}")
        except Exception as adk_error:
            logger.warning(
                f"Failed to delete ADK session (may not exist): {adk_error}"
            )
        
        logger.info(f"Session deleted successfully: {session_id}")
        return DeleteSessionResponse(success=success)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            f"Failed to delete session {session_id}: "
            f"{type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete session: {str(e)}"
        )
