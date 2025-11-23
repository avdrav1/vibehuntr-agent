"""Agent service wrapper for FastAPI integration.

This module provides async wrappers around the existing agent_invoker and agent_loader
modules to integrate with FastAPI's async architecture. It maintains backward compatibility
with the existing ADK agent implementation while providing async interfaces for the backend.
"""

import logging
from typing import AsyncGenerator, Any, Dict, TYPE_CHECKING
import asyncio
from functools import partial
import sys
import os
from pathlib import Path

# Add parent directory to path to import main app modules
# This allows backend to import from the main app directory
# backend/app/services/agent_service.py -> go up 3 levels to project root
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Also ensure PYTHONPATH includes project root for imports
if 'PYTHONPATH' not in os.environ:
    os.environ['PYTHONPATH'] = str(project_root)
else:
    if str(project_root) not in os.environ['PYTHONPATH']:
        os.environ['PYTHONPATH'] = f"{project_root}:{os.environ['PYTHONPATH']}"

# Lazy imports to avoid import-time errors
# These will be imported when actually needed
if TYPE_CHECKING:
    from app.event_planning.agent_loader import get_agent, clear_agent_cache
    from app.event_planning.agent_invoker import (
        invoke_agent_streaming,
        invoke_agent,
        AgentInvocationError
    )


# Define AgentInvocationError as a re-export
# This allows tests to import it without triggering the full import chain
class AgentInvocationError(Exception):
    """Custom exception for agent invocation failures.
    
    This exception is raised when agent invocation fails due to API errors,
    timeout errors, tool execution failures, or other issues.
    """
    pass


# Configure logging
logger = logging.getLogger(__name__)


class AgentService:
    """
    Async wrapper service for ADK agent invocation.
    
    This service wraps the existing synchronous agent_invoker functions with
    async interfaces suitable for FastAPI. It reuses all existing agent logic,
    tools, and configuration without modification.
    
    Requirements:
    - 11.1: Uses existing agent_invoker module
    - 11.2: Uses existing event planning tools via agent_invoker
    - 11.4: Uses existing agent_loader module
    """
    
    def __init__(self):
        """Initialize the agent service."""
        self._agent = None
        logger.info("AgentService initialized")
    
    def _get_agent(self) -> Any:
        """
        Get the agent instance, loading it if necessary.
        
        Returns:
            Agent: The ADK agent instance
            
        Raises:
            RuntimeError: If agent loading fails
        """
        if self._agent is None:
            try:
                from app.event_planning.agent_loader import get_agent
                self._agent = get_agent()
                logger.info("Agent loaded successfully")
            except Exception as e:
                error_msg = f"Failed to load agent: {type(e).__name__}: {e}"
                logger.error(error_msg, exc_info=True)
                raise RuntimeError(error_msg) from e
        return self._agent
    
    async def stream_agent(
        self,
        message: str,
        session_id: str,
        user_id: str = "web_user",
        yield_tool_calls: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream agent response tokens asynchronously.
        
        This method wraps the synchronous invoke_agent_streaming function to provide
        an async generator interface for FastAPI SSE streaming. It runs the synchronous
        generator in a thread pool to avoid blocking the event loop.
        
        Args:
            message: User's input message
            session_id: Session identifier for conversation continuity
            user_id: User identifier (defaults to "web_user")
            yield_tool_calls: If True, yield tool call information in addition to text
            
        Yields:
            Dict[str, Any]: Dictionary with 'type' key ('text' or 'tool_call') and data
            
        Raises:
            AgentInvocationError: If agent invocation fails
            
        Example:
            >>> service = AgentService()
            >>> async for item in service.stream_agent("Hello", "session_123"):
            ...     if item['type'] == 'text':
            ...         print(item['content'], end='')
        """
        try:
            from app.event_planning.agent_invoker import invoke_agent_streaming
            
            agent = self._get_agent()
            
            # Create a partial function with all arguments bound
            stream_func = partial(
                invoke_agent_streaming,
                agent=agent,
                message=message,
                session_id=session_id,
                user_id=user_id,
                yield_tool_calls=yield_tool_calls
            )
            
            # Run the synchronous generator in a thread pool
            loop = asyncio.get_event_loop()
            
            # We need to iterate the generator in the thread pool
            # and yield results back to the async context
            def sync_generator_wrapper():
                """Wrapper to collect items from sync generator."""
                return list(stream_func())
            
            # Run the entire streaming operation in thread pool
            items = await loop.run_in_executor(None, sync_generator_wrapper)
            
            # Yield items asynchronously
            for item in items:
                yield item
                
        except AgentInvocationError:
            # Re-raise our AgentInvocationError
            raise
        except Exception as e:
            error_msg = f"Agent streaming failed: {type(e).__name__}: {e}"
            logger.error(error_msg, exc_info=True)
            # Raise our local AgentInvocationError
            raise AgentInvocationError(error_msg) from e
    
    async def invoke_agent_async(
        self,
        message: str,
        session_id: str,
        user_id: str = "web_user"
    ) -> str:
        """
        Invoke agent and return complete response asynchronously.
        
        This method wraps the synchronous invoke_agent function to provide an
        async interface for FastAPI. It runs the synchronous function in a
        thread pool to avoid blocking the event loop.
        
        Args:
            message: User's input message
            session_id: Session identifier for conversation continuity
            user_id: User identifier (defaults to "web_user")
            
        Returns:
            str: Complete agent response
            
        Raises:
            AgentInvocationError: If agent invocation fails
            
        Example:
            >>> service = AgentService()
            >>> response = await service.invoke_agent_async("Hello", "session_123")
            >>> print(response)
        """
        try:
            from app.event_planning.agent_invoker import invoke_agent
            
            agent = self._get_agent()
            
            # Create a partial function with all arguments bound
            invoke_func = partial(
                invoke_agent,
                agent=agent,
                message=message,
                session_id=session_id,
                user_id=user_id
            )
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, invoke_func)
            
            return result
            
        except AgentInvocationError:
            # Re-raise our AgentInvocationError
            raise
        except Exception as e:
            error_msg = f"Agent invocation failed: {type(e).__name__}: {e}"
            logger.error(error_msg, exc_info=True)
            # Raise our local AgentInvocationError
            raise AgentInvocationError(error_msg) from e
    
    def clear_cache(self) -> None:
        """
        Clear the agent cache.
        
        This is useful when the environment configuration changes and you need
        to reload the agent with new settings.
        """
        from app.event_planning.agent_loader import clear_agent_cache
        self._agent = None
        clear_agent_cache()
        logger.info("Agent cache cleared")


# Global agent service instance
_agent_service: AgentService | None = None


def get_agent_service() -> AgentService:
    """
    Get the global agent service instance.
    
    This function provides a singleton pattern for the agent service,
    ensuring only one instance is created and reused across requests.
    
    Returns:
        AgentService: The global agent service instance
    """
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service
