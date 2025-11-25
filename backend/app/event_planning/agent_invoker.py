"""Agent invoker module for handling agent invocation with streaming support.

This module provides functions for invoking ADK agents with proper error handling,
logging, and streaming response support. The ADK session service automatically
maintains conversation history and provides it to the agent.
"""

import logging
from typing import Dict, List, Generator, Any
from datetime import datetime
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types

# Configure logging
logger = logging.getLogger(__name__)

# Global session service for managing conversations
_session_service = InMemorySessionService()


class AgentInvocationError(Exception):
    """Custom exception for agent invocation failures.
    
    This exception is raised when agent invocation fails due to API errors,
    timeout errors, tool execution failures, or other issues.
    """
    pass





def invoke_agent_streaming(
    agent: Any,
    message: str,
    session_id: str = "default_session",
    user_id: str = "default_user",
    yield_tool_calls: bool = False
) -> Generator[Dict[str, Any], None, None]:
    """
    Invoke agent with streaming response using ADK Runner.
    
    This function invokes the ADK agent and yields response tokens as they are
    generated, providing real-time feedback to the user. The ADK session service
    automatically maintains and provides conversation history to the agent - no
    manual history passing is required.
    
    Args:
        agent: The ADK agent instance
        message: User's input message
        session_id: Session identifier for conversation continuity (ADK uses this
                   to automatically retrieve and provide conversation history)
        user_id: User identifier
        yield_tool_calls: If True, yield tool call information in addition to text
        
    Yields:
        Dict[str, Any]: Dictionary with 'type' key ('text' or 'tool_call') and corresponding data
        
    Raises:
        AgentInvocationError: If agent invocation fails
        
    Example:
        >>> agent = get_agent()
        >>> for item in invoke_agent_streaming(agent, "Hello", session_id="my_session"):
        ...     if item['type'] == 'text':
        ...         print(item['content'], end='')
    
    Note:
        ADK Runner automatically uses the session service to retrieve conversation
        history and provide it to the agent. You do not need to manually pass
        chat_history - the session_id is sufficient for context continuity.
    """
    try:
        logger.info(
            f"Invoking agent with streaming for message: {message[:50]}...",
            extra={
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "user_id": user_id,
                "message_length": len(message)
            }
        )
        logger.debug(f"Session ID: {session_id}, User ID: {user_id}")
        
        # Get or create session with automatic recovery
        try:
            session = _session_service.get_session_sync(
                session_id=session_id,
                app_name="vibehuntr_playground",
                user_id=user_id
            )
            logger.debug(f"Retrieved existing session: {session_id}")
        except Exception as session_error:
            # Create new session with the SAME session_id if it doesn't exist
            logger.warning(
                f"Session retrieval failed, creating new session with same ID: {session_error}",
                extra={
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id,
                    "error_type": type(session_error).__name__
                }
            )
            try:
                session = _session_service.create_session_sync(
                    session_id=session_id,  # Use the provided session_id
                    user_id=user_id,
                    app_name="vibehuntr_playground"
                )
                logger.info(
                    f"Successfully created new ADK session: {session_id}",
                    extra={
                        "timestamp": datetime.now().isoformat(),
                        "session_id": session_id
                    }
                )
            except Exception as create_error:
                # Check if it's an AlreadyExistsError - if so, try to get it again
                error_type_name = type(create_error).__name__
                if "AlreadyExists" in error_type_name:
                    logger.info(
                        f"Session {session_id} already exists, retrieving it",
                        extra={
                            "timestamp": datetime.now().isoformat(),
                            "session_id": session_id
                        }
                    )
                    try:
                        session = _session_service.get_session_sync(
                            session_id=session_id,
                            app_name="vibehuntr_playground",
                            user_id=user_id
                        )
                        logger.debug(f"Successfully retrieved existing session: {session_id}")
                    except Exception as get_error:
                        error_msg = f"Failed to retrieve existing session: {type(get_error).__name__}: {get_error}"
                        logger.error(
                            error_msg,
                            extra={
                                "timestamp": datetime.now().isoformat(),
                                "session_id": session_id
                            },
                            exc_info=True
                        )
                        raise AgentInvocationError(error_msg) from get_error
                else:
                    error_msg = f"Failed to create session: {error_type_name}: {create_error}"
                    logger.error(
                        error_msg,
                        extra={
                            "timestamp": datetime.now().isoformat(),
                            "user_id": user_id
                        },
                        exc_info=True
                    )
                    raise AgentInvocationError(error_msg) from create_error
        
        # Get and update conversation context with error handling
        from app.event_planning.context_manager import get_context
        
        enhanced_message = message  # Default to original message
        
        try:
            context = get_context(session_id)
            
            # Log context extraction
            logger.info(
                f"Extracting context from user message",
                extra={
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id,
                    "message_preview": message[:50] if len(message) > 50 else message
                }
            )
            
            context.update_from_user_message(message)
            
            # Log extracted context
            logger.debug(
                f"Context extracted from user message",
                extra={
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id,
                    "location": context.location,
                    "search_query": context.search_query,
                    "num_venues": len(context.recent_venues)
                }
            )
            
            # Get context string to inject
            context_string = context.get_context_string()
            
            # Inject context into message if available
            if context_string:
                enhanced_message = f"[CONTEXT: {context_string}]\n\n{message}"
                logger.info(
                    f"Injecting context into message",
                    extra={
                        "timestamp": datetime.now().isoformat(),
                        "session_id": session_id,
                        "context_string": context_string,
                        "context_length": len(context_string)
                    }
                )
            else:
                logger.debug(
                    f"No context to inject",
                    extra={
                        "timestamp": datetime.now().isoformat(),
                        "session_id": session_id
                    }
                )
        except Exception as context_error:
            # Log error but continue with original message (graceful degradation)
            logger.error(
                f"Context extraction/injection failed, continuing with original message: {type(context_error).__name__}: {context_error}",
                extra={
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id,
                    "exception_type": type(context_error).__name__
                },
                exc_info=True
            )
            # enhanced_message already set to message above
        
        # Create runner
        try:
            runner = Runner(
                agent=agent,
                session_service=_session_service,
                app_name="vibehuntr_playground"
            )
            logger.debug("Created ADK Runner successfully")
        except Exception as runner_error:
            error_msg = f"Failed to create ADK Runner: {type(runner_error).__name__}: {runner_error}"
            logger.error(
                error_msg,
                extra={
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id,
                    "exception_type": type(runner_error).__name__
                },
                exc_info=True
            )
            raise AgentInvocationError(error_msg) from runner_error
        
        # Create message content (use enhanced message with context)
        try:
            content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=enhanced_message)]
            )
        except Exception as content_error:
            error_msg = f"Failed to create message content: {type(content_error).__name__}: {content_error}"
            logger.error(
                error_msg,
                extra={
                    "timestamp": datetime.now().isoformat(),
                    "message_length": len(message),
                    "exception_type": type(content_error).__name__
                },
                exc_info=True
            )
            raise AgentInvocationError(error_msg) from content_error
        
        # Run agent with streaming
        try:
            # Log context information for verification
            logger.debug(
                f"Running agent with session context",
                extra={
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id,
                    "user_id": user_id,
                    "message_preview": message[:50] if len(message) > 50 else message
                }
            )
            
            events = runner.run(
                new_message=content,
                user_id=user_id,
                session_id=session_id,
                run_config=RunConfig(streaming_mode=StreamingMode.SSE)
            )
        except Exception as run_error:
            error_msg = f"Agent invocation failed: {type(run_error).__name__}: {run_error}"
            logger.error(
                error_msg,
                extra={
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id,
                    "user_id": user_id,
                    "exception_type": type(run_error).__name__
                },
                exc_info=True
            )
            raise AgentInvocationError(error_msg) from run_error
        
        # Yield text and optionally tool calls from events
        # Track accumulated text to avoid sending duplicates
        accumulated_text = ""
        
        try:
            for event in events:
                # Check for tool calls if requested
                if yield_tool_calls and hasattr(event, 'function_calls') and event.function_calls:
                    for func_call in event.function_calls:
                        tool_info = {
                            'type': 'tool_call',
                            'name': func_call.name if hasattr(func_call, 'name') else 'unknown',
                            'args': str(func_call.args) if hasattr(func_call, 'args') else '{}'
                        }
                        logger.info(
                            f"Tool invoked: {tool_info['name']}",
                            extra={
                                "timestamp": datetime.now().isoformat(),
                                "tool_name": tool_info['name']
                            }
                        )
                        yield tool_info
                
                # Yield text content (only new content, not duplicates)
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            # Check if this is new content or a duplicate
                            if part.text.startswith(accumulated_text):
                                # This is an accumulated message, only yield the new part
                                new_content = part.text[len(accumulated_text):]
                                if new_content:
                                    accumulated_text = part.text
                                    logger.debug(f"Yielding new content: {len(new_content)} chars")
                                    yield {'type': 'text', 'content': new_content}
                                else:
                                    # No new content, this is a duplicate - skip it
                                    logger.debug(f"Skipping duplicate content: {len(part.text)} chars")
                            else:
                                # This is completely new content (shouldn't happen, but handle it)
                                logger.warning(f"Unexpected: part.text doesn't start with accumulated_text")
                                accumulated_text += part.text
                                yield {'type': 'text', 'content': part.text}
            
            # Update context with agent's response (with error handling)
            if accumulated_text:
                try:
                    logger.info(
                        f"Extracting entities from agent response",
                        extra={
                            "timestamp": datetime.now().isoformat(),
                            "session_id": session_id,
                            "response_length": len(accumulated_text)
                        }
                    )
                    
                    # Store venues count before update
                    venues_before = len(context.recent_venues)
                    
                    context.update_from_agent_message(accumulated_text)
                    
                    # Log entity storage
                    venues_after = len(context.recent_venues)
                    if venues_after > venues_before:
                        logger.info(
                            f"Stored {venues_after - venues_before} new venue(s) in context",
                            extra={
                                "timestamp": datetime.now().isoformat(),
                                "session_id": session_id,
                                "venues_added": venues_after - venues_before,
                                "total_venues": venues_after
                            }
                        )
                except Exception as entity_error:
                    # Log error but continue (graceful degradation)
                    logger.error(
                        f"Entity extraction from agent response failed: {type(entity_error).__name__}: {entity_error}",
                        extra={
                            "timestamp": datetime.now().isoformat(),
                            "session_id": session_id,
                            "exception_type": type(entity_error).__name__
                        },
                        exc_info=True
                    )
            
            logger.info(
                "Agent invocation completed successfully",
                extra={
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id
                }
            )
        except Exception as stream_error:
            error_msg = f"Agent invocation failed during streaming: {type(stream_error).__name__}: {stream_error}"
            logger.error(
                error_msg,
                extra={
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id,
                    "exception_type": type(stream_error).__name__
                },
                exc_info=True
            )
            raise AgentInvocationError(error_msg) from stream_error
        
    except AgentInvocationError:
        # Re-raise our custom errors without wrapping
        raise
    except Exception as e:
        error_msg = f"Agent invocation failed: {type(e).__name__}: {e}"
        logger.error(
            error_msg,
            extra={
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "exception_type": type(e).__name__
            },
            exc_info=True
        )
        raise AgentInvocationError(error_msg) from e


def invoke_agent(
    agent: Any,
    message: str,
    session_id: str = "default_session",
    user_id: str = "default_user"
) -> str:
    """
    Invoke agent and return complete response.
    
    This function invokes the ADK agent and returns the complete response once
    generation is finished. Use this when you don't need streaming and want the
    full response at once. The ADK session service automatically maintains and
    provides conversation history to the agent - no manual history passing is required.
    
    Args:
        agent: The ADK agent instance
        message: User's input message
        session_id: Session identifier for conversation continuity (ADK uses this
                   to automatically retrieve and provide conversation history)
        user_id: User identifier
        
    Returns:
        str: Complete agent response
        
    Raises:
        AgentInvocationError: If agent invocation fails
        
    Example:
        >>> agent = get_agent()
        >>> response = invoke_agent(agent, "Hello", session_id="my_session")
        >>> print(response)
    
    Note:
        ADK Runner automatically uses the session service to retrieve conversation
        history and provide it to the agent. You do not need to manually pass
        chat_history - the session_id is sufficient for context continuity.
    """
    try:
        logger.info(
            f"Invoking agent for message: {message[:50]}...",
            extra={
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "user_id": user_id
            }
        )
        
        # Collect all text tokens from streaming (filter out tool calls)
        items = list(invoke_agent_streaming(agent, message, session_id, user_id, yield_tool_calls=False))
        tokens = [item['content'] for item in items if item['type'] == 'text']
        result = "".join(tokens)
        
        logger.info(
            "Agent invocation completed successfully",
            extra={
                "timestamp": datetime.now().isoformat(),
                "response_length": len(result),
                "session_id": session_id
            }
        )
        logger.debug(f"Response length: {len(result)} characters")
        
        return result
        
    except AgentInvocationError:
        # Re-raise our custom errors without wrapping
        raise
    except Exception as e:
        error_msg = f"Agent invocation failed: {type(e).__name__}: {e}"
        logger.error(
            error_msg,
            extra={
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "exception_type": type(e).__name__
            },
            exc_info=True
        )
        raise AgentInvocationError(error_msg) from e
