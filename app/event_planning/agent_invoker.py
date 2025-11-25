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
from app.event_planning.response_tracker import ResponseTracker
from app.event_planning.duplicate_detector import DuplicateDetector, PipelineStage
from app.event_planning.duplication_metrics import get_metrics_instance

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
        # Initialize enhanced duplicate detection with error handling
        try:
            duplicate_detector = DuplicateDetector(similarity_threshold=0.95)
        except Exception as detector_error:
            logger.error(
                f"Failed to initialize DuplicateDetector, using fallback: {type(detector_error).__name__}: {detector_error}",
                exc_info=True
            )
            # Create a minimal fallback detector
            duplicate_detector = None
        
        # Initialize response tracker for comprehensive logging with error handling
        try:
            tracker = ResponseTracker(session_id=session_id, user_id=user_id)
        except Exception as tracker_error:
            logger.error(
                f"Failed to initialize ResponseTracker, using fallback: {type(tracker_error).__name__}: {tracker_error}",
                exc_info=True
            )
            # Create a minimal fallback tracker
            tracker = None
        
        token_index = 0
        
        # Get metrics instance with error handling
        try:
            metrics = get_metrics_instance()
        except Exception as metrics_error:
            logger.error(
                f"Failed to get metrics instance, using fallback: {type(metrics_error).__name__}: {metrics_error}",
                exc_info=True
            )
            metrics = None
        
        # Set initial pipeline stage with error handling
        if duplicate_detector:
            try:
                duplicate_detector.set_pipeline_stage(PipelineStage.EVENT_PROCESSING)
            except Exception as stage_error:
                logger.error(
                    f"Failed to set pipeline stage: {type(stage_error).__name__}: {stage_error}",
                    exc_info=True
                )
        
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
                            try:
                                # Get accumulated text with error handling
                                accumulated_text = ""
                                if duplicate_detector:
                                    try:
                                        accumulated_text = duplicate_detector.get_accumulated_text()
                                    except Exception as acc_error:
                                        logger.error(
                                            f"Failed to get accumulated text: {type(acc_error).__name__}: {acc_error}",
                                            exc_info=True
                                        )
                                
                                # Check if this is new content or a duplicate
                                if part.text.startswith(accumulated_text):
                                    # This is an accumulated message, only yield the new part
                                    new_content = part.text[len(accumulated_text):]
                                    if new_content:
                                        # Set pipeline stage for token yielding with error handling
                                        if duplicate_detector:
                                            try:
                                                duplicate_detector.set_pipeline_stage(PipelineStage.TOKEN_YIELDING)
                                            except Exception as stage_error:
                                                logger.error(
                                                    f"Failed to set pipeline stage: {type(stage_error).__name__}: {stage_error}",
                                                    exc_info=True
                                                )
                                        
                                        # Use enhanced duplicate detection with stage tracking and error handling
                                        is_duplicate = False
                                        if duplicate_detector:
                                            try:
                                                is_duplicate = duplicate_detector.is_duplicate(new_content, PipelineStage.TOKEN_YIELDING)
                                            except Exception as dup_error:
                                                logger.error(
                                                    f"Duplicate detection failed, assuming not duplicate: {type(dup_error).__name__}: {dup_error}",
                                                    exc_info=True
                                                )
                                                is_duplicate = False
                                        
                                        if not is_duplicate:
                                            # Track chunk with ResponseTracker with error handling
                                            if tracker:
                                                try:
                                                    is_unique = tracker.track_chunk(new_content)
                                                except Exception as track_error:
                                                    logger.error(
                                                        f"Chunk tracking failed: {type(track_error).__name__}: {track_error}",
                                                        exc_info=True
                                                    )
                                            
                                            # Add to duplicate detector with error handling
                                            if duplicate_detector:
                                                try:
                                                    duplicate_detector.add_chunk(new_content)
                                                    duplicate_detector.update_accumulated_text(part.text)
                                                except Exception as add_error:
                                                    logger.error(
                                                        f"Failed to add chunk to detector: {type(add_error).__name__}: {add_error}",
                                                        exc_info=True
                                                    )
                                            
                                            logger.debug(f"Yielding new content: {len(new_content)} chars")
                                            
                                            # Log token yield event with error handling
                                            if tracker:
                                                try:
                                                    tracker.log_token_yield(new_content, token_index)
                                                except Exception as log_error:
                                                    # Don't let logging failures affect yielding
                                                    pass
                                            token_index += 1
                                            
                                            yield {'type': 'text', 'content': new_content}
                                        else:
                                            # This is a duplicate chunk - skip it
                                            logger.warning(f"Detected and skipped duplicate chunk: {len(new_content)} chars")
                                            # Track as duplicate with error handling
                                            if tracker:
                                                try:
                                                    tracker.track_chunk(new_content)
                                                except Exception as track_error:
                                                    logger.error(
                                                        f"Failed to track duplicate: {type(track_error).__name__}: {track_error}",
                                                        exc_info=True
                                                    )
                                            # Increment metrics counter with error handling
                                            if metrics:
                                                try:
                                                    metrics.increment_duplicate_detected(session_id)
                                                except Exception as metrics_error:
                                                    logger.error(
                                                        f"Failed to increment duplicate counter: {type(metrics_error).__name__}: {metrics_error}",
                                                        exc_info=True
                                                    )
                                    else:
                                        # No new content, this is a duplicate - skip it
                                        logger.debug(f"Skipping duplicate content: {len(part.text)} chars")
                                else:
                                    # This is completely new content (shouldn't happen, but handle it)
                                    logger.warning(f"Unexpected: part.text doesn't start with accumulated_text")
                                    
                                    # Set pipeline stage for token yielding with error handling
                                    if duplicate_detector:
                                        try:
                                            duplicate_detector.set_pipeline_stage(PipelineStage.TOKEN_YIELDING)
                                        except Exception as stage_error:
                                            logger.error(
                                                f"Failed to set pipeline stage: {type(stage_error).__name__}: {stage_error}",
                                                exc_info=True
                                            )
                                    
                                    # Use enhanced duplicate detection with stage tracking and error handling
                                    is_duplicate = False
                                    if duplicate_detector:
                                        try:
                                            is_duplicate = duplicate_detector.is_duplicate(part.text, PipelineStage.TOKEN_YIELDING)
                                        except Exception as dup_error:
                                            logger.error(
                                                f"Duplicate detection failed, assuming not duplicate: {type(dup_error).__name__}: {dup_error}",
                                                exc_info=True
                                            )
                                            is_duplicate = False
                                    
                                    if not is_duplicate:
                                        # Track chunk with ResponseTracker with error handling
                                        if tracker:
                                            try:
                                                is_unique = tracker.track_chunk(part.text)
                                            except Exception as track_error:
                                                logger.error(
                                                    f"Chunk tracking failed: {type(track_error).__name__}: {track_error}",
                                                    exc_info=True
                                                )
                                        
                                        # Add to duplicate detector with error handling
                                        if duplicate_detector:
                                            try:
                                                duplicate_detector.add_chunk(part.text)
                                                accumulated_text = duplicate_detector.get_accumulated_text()
                                                duplicate_detector.update_accumulated_text(accumulated_text + part.text)
                                            except Exception as add_error:
                                                logger.error(
                                                    f"Failed to add chunk to detector: {type(add_error).__name__}: {add_error}",
                                                    exc_info=True
                                                )
                                        
                                        # Log token yield event with error handling
                                        if tracker:
                                            try:
                                                tracker.log_token_yield(part.text, token_index)
                                            except Exception as log_error:
                                                # Don't let logging failures affect yielding
                                                pass
                                        token_index += 1
                                        
                                        yield {'type': 'text', 'content': part.text}
                                    else:
                                        logger.warning(f"Detected and skipped duplicate unexpected chunk: {len(part.text)} chars")
                                        # Track as duplicate with error handling
                                        if tracker:
                                            try:
                                                tracker.track_chunk(part.text)
                                            except Exception as track_error:
                                                logger.error(
                                                    f"Failed to track duplicate: {type(track_error).__name__}: {track_error}",
                                                    exc_info=True
                                                )
                                        # Increment metrics counter with error handling
                                        if metrics:
                                            try:
                                                metrics.increment_duplicate_detected(session_id)
                                            except Exception as metrics_error:
                                                logger.error(
                                                    f"Failed to increment duplicate counter: {type(metrics_error).__name__}: {metrics_error}",
                                                    exc_info=True
                                                )
                            except Exception as part_error:
                                # If processing this part fails, log error and continue
                                logger.error(
                                    f"Failed to process text part: {type(part_error).__name__}: {part_error}",
                                    exc_info=True
                                )
                                # Yield the content anyway (graceful degradation)
                                yield {'type': 'text', 'content': part.text}
            
            # Update context with agent's response (with error handling)
            accumulated_text = duplicate_detector.get_accumulated_text()
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
            
            # Get and log final metrics with error handling
            response_metadata = None
            if tracker:
                try:
                    response_metadata = tracker.get_metrics()
                except Exception as metrics_error:
                    logger.error(
                        f"Failed to get response metrics: {type(metrics_error).__name__}: {metrics_error}",
                        exc_info=True
                    )
            
            # Get duplication summary from detector with error handling
            dup_summary = {"total_duplications": 0, "by_source": {}, "by_stage": {}, "by_method": {}}
            if duplicate_detector:
                try:
                    dup_summary = duplicate_detector.get_duplication_summary()
                except Exception as summary_error:
                    logger.error(
                        f"Failed to get duplication summary: {type(summary_error).__name__}: {summary_error}",
                        exc_info=True
                    )
            
            # Record response quality in metrics with error handling
            if metrics and response_metadata:
                try:
                    metrics.record_response_quality(
                        session_id=session_id,
                        total_chunks=response_metadata.total_chunks,
                        duplicate_chunks=response_metadata.duplicate_chunks
                    )
                except Exception as record_error:
                    logger.error(
                        f"Failed to record response quality: {type(record_error).__name__}: {record_error}",
                        exc_info=True
                    )
            
            # Check if duplication is resolved (clean response after previous duplicates) with error handling
            if metrics and response_metadata and response_metadata.duplicate_chunks == 0:
                try:
                    metrics.log_resolution_confirmation(session_id)
                except Exception as resolution_error:
                    logger.error(
                        f"Failed to log resolution confirmation: {type(resolution_error).__name__}: {resolution_error}",
                        exc_info=True
                    )
            
            # Check if threshold is exceeded with error handling
            if metrics:
                try:
                    metrics.check_threshold_exceeded(session_id, threshold=0.1)
                except Exception as threshold_error:
                    logger.error(
                        f"Failed to check threshold: {type(threshold_error).__name__}: {threshold_error}",
                        exc_info=True
                    )
            
            # Log completion with error handling
            try:
                logger.info(
                    "Agent invocation completed successfully",
                    extra={
                        "timestamp": datetime.now().isoformat(),
                        "session_id": session_id,
                        "response_id": tracker.response_id if tracker else "unknown",
                        "total_chunks": response_metadata.total_chunks if response_metadata else 0,
                        "duplicate_chunks": response_metadata.duplicate_chunks if response_metadata else 0,
                        "duplication_rate": response_metadata.duplication_rate if response_metadata else 0.0,
                        "duplication_summary": dup_summary
                    }
                )
            except Exception as log_error:
                # Fallback to basic logging
                print(
                    f"Info: Agent invocation completed successfully for session {session_id}",
                    file=__import__('sys').stderr
                )
            
            # Log duplication source tracking if duplicates were detected with error handling
            if dup_summary["total_duplications"] > 0:
                try:
                    logger.warning(
                        f"Duplication detected during response generation",
                        extra={
                            "timestamp": datetime.now().isoformat(),
                            "session_id": session_id,
                            "response_id": tracker.response_id if tracker else "unknown",
                            "total_duplications": dup_summary["total_duplications"],
                            "by_source": dup_summary["by_source"],
                            "by_stage": dup_summary["by_stage"],
                            "by_method": dup_summary["by_method"]
                        }
                    )
                except Exception as log_error:
                    # Fallback to basic logging
                    print(
                        f"Warning: Duplication detected during response generation for session {session_id}",
                        file=__import__('sys').stderr
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
