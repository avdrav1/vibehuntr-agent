"""Chat API endpoints for message handling and streaming.

This module provides REST API endpoints for chat functionality:
- POST /api/chat: Send a message and receive complete response
- GET /api/chat/stream: Send a message and stream response via SSE

Requirements: 2.1, 2.2, 2.3, 4.1, 4.2
"""

import logging
import json
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException, Query
from sse_starlette.sse import EventSourceResponse

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    StreamEvent,
)
from app.services.session_manager import session_manager
from app.services.agent_service import get_agent_service, AgentInvocationError


# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Agent invocation failed"},
    },
)
async def send_message(request: ChatRequest) -> ChatResponse:
    """
    Send a message and receive complete response (non-streaming).
    
    This endpoint accepts a user message, invokes the agent, and returns
    the complete response. The message and response are stored in the
    session history.
    
    Args:
        request: ChatRequest containing session_id and message
        
    Returns:
        ChatResponse: Complete agent response
        
    Raises:
        HTTPException: 400 if request is invalid, 500 if agent fails
        
    Requirements:
    - 2.1: Backend invokes ADK agent when frontend sends message
    - 4.1: POST /api/chat endpoint for sending messages
    """
    try:
        logger.info(
            f"Received chat request for session {request.session_id}: "
            f"{request.message[:50]}..."
        )
        
        # Validate session exists
        if not session_manager.session_exists(request.session_id):
            logger.warning(f"Session {request.session_id} does not exist")
            raise HTTPException(
                status_code=400,
                detail=f"Session {request.session_id} does not exist. "
                       "Please create a session first."
            )
        
        # Add user message to session
        session_manager.add_message(
            session_id=request.session_id,
            role="user",
            content=request.message
        )
        logger.debug(f"Added user message to session {request.session_id}")
        
        # Get agent service and invoke
        agent_service = get_agent_service()
        
        try:
            response = await agent_service.invoke_agent_async(
                message=request.message,
                session_id=request.session_id,
                user_id="web_user"
            )
            logger.info(
                f"Agent response received for session {request.session_id}: "
                f"{len(response)} characters"
            )
        except AgentInvocationError as e:
            logger.error(
                f"Agent invocation failed for session {request.session_id}: {e}",
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail=f"Agent invocation failed: {str(e)}"
            )
        
        # Add assistant response to session
        session_manager.add_message(
            session_id=request.session_id,
            role="assistant",
            content=response
        )
        logger.debug(f"Added assistant response to session {request.session_id}")
        
        return ChatResponse(response=response)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error in send_message: {type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/chat/stream")
async def stream_chat(
    session_id: str = Query(..., description="Session identifier"),
    message: str = Query(..., min_length=1, description="User message")
) -> EventSourceResponse:
    """
    Stream agent response via Server-Sent Events.
    
    This endpoint accepts a user message and streams the agent's response
    token by token using SSE. The frontend can display tokens as they arrive
    for a real-time experience.
    
    Args:
        session_id: Session identifier for conversation continuity
        message: User's message content
        
    Returns:
        EventSourceResponse: SSE stream with token events
        
    Event Types:
        - message: Contains StreamEvent with type='token' and content
        - message: Contains StreamEvent with type='done' when complete
        - error: Contains StreamEvent with type='error' and error message
        
    Requirements:
    - 2.2: Backend streams tokens via Server-Sent Events
    - 2.3: System sends each token as it arrives during streaming
    - 2.4: Backend sends completion event when streaming completes
    - 4.2: GET /api/chat/stream endpoint for SSE streaming
    """
    
    async def event_generator() -> AsyncGenerator[dict, None]:
        """
        Generate SSE events for streaming response.
        
        Yields:
            dict: SSE event with 'event' and 'data' keys
        """
        try:
            logger.info(
                f"Starting stream for session {session_id}: {message[:50]}..."
            )
            
            # Validate session exists
            if not session_manager.session_exists(session_id):
                logger.warning(f"Session {session_id} does not exist")
                error_event = StreamEvent(
                    type="error",
                    content=f"Session {session_id} does not exist. "
                            "Please create a session first."
                )
                yield {
                    "event": "error",
                    "data": error_event.model_dump_json()
                }
                return
            
            # NOTE: Do NOT add user message to session_manager here
            # The ADK session service automatically stores messages during agent invocation
            # Adding it here would create duplicates
            # session_manager.add_message(
            #     session_id=session_id,
            #     role="user",
            #     content=message
            # )
            logger.debug(f"User message will be stored by ADK session service for {session_id}")
            
            # Get agent service
            agent_service = get_agent_service()
            
            # Accumulate response for session storage
            full_response = []
            
            try:
                # Stream agent response
                async for item in agent_service.stream_agent(
                    message=message,
                    session_id=session_id,
                    user_id="web_user",
                    yield_tool_calls=False
                ):
                    # Only yield text tokens
                    if item.get('type') == 'text':
                        token = item.get('content', '')
                        full_response.append(token)
                        
                        # Send token event
                        token_event = StreamEvent(type="token", content=token)
                        yield {
                            "event": "message",
                            "data": token_event.model_dump_json()
                        }
                
                logger.info(
                    f"Stream completed for session {session_id}: "
                    f"{len(full_response)} tokens"
                )
                
                # NOTE: Do NOT add assistant response to session_manager here
                # The ADK session service automatically stores messages during agent invocation
                # Adding it here would create duplicates
                # complete_response = ''.join(full_response)
                # session_manager.add_message(
                #     session_id=session_id,
                #     role="assistant",
                #     content=complete_response
                # )
                logger.debug(f"Assistant response stored by ADK session service for {session_id}")
                
                # Send completion event
                done_event = StreamEvent(type="done")
                yield {
                    "event": "message",
                    "data": done_event.model_dump_json()
                }
                
            except AgentInvocationError as e:
                logger.error(
                    f"Agent streaming failed for session {session_id}: {e}",
                    exc_info=True
                )
                error_event = StreamEvent(
                    type="error",
                    content=f"Agent invocation failed: {str(e)}"
                )
                yield {
                    "event": "error",
                    "data": error_event.model_dump_json()
                }
                
        except Exception as e:
            logger.error(
                f"Unexpected error in stream_chat: {type(e).__name__}: {e}",
                exc_info=True
            )
            error_event = StreamEvent(
                type="error",
                content=f"Internal server error: {str(e)}"
            )
            yield {
                "event": "error",
                "data": error_event.model_dump_json()
            }
    
    return EventSourceResponse(event_generator())
