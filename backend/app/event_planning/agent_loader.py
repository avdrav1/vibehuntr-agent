"""Agent loader module for selecting and caching the appropriate agent.

This module provides centralized agent loading logic that selects between
the full agent (with document retrieval) and the simple agent (event planning only)
based on environment configuration.
"""

import os
import logging
from typing import Optional
from google.adk.agents import Agent

# Configure logging
logger = logging.getLogger(__name__)

# Cache for agent instance to avoid reloading
_agent_cache: Optional[Agent] = None


def get_agent() -> Agent:
    """
    Load and return the appropriate agent based on environment configuration.
    
    The agent selection is controlled by the USE_DOCUMENT_RETRIEVAL environment
    variable:
    - If "true": Uses the full agent from app.agent (includes document retrieval)
    - If "false" or unset: Uses the simple agent from app.event_planning.simple_agent
    
    The agent instance is cached after first load to avoid reloading on every call.
    
    Returns:
        Agent: Either the full agent (with document retrieval) or simple agent
        
    Raises:
        ImportError: If agent modules cannot be loaded
        RuntimeError: If agent initialization fails
        
    Example:
        >>> agent = get_agent()
        >>> response = agent.run("Help me plan an event")
    """
    global _agent_cache
    
    # Return cached agent if available
    if _agent_cache is not None:
        logger.debug("Returning cached agent instance")
        return _agent_cache
    
    # Check environment variable for agent selection
    use_document_retrieval = os.getenv("USE_DOCUMENT_RETRIEVAL", "false").lower() == "true"
    
    try:
        if use_document_retrieval:
            logger.info("Loading full agent with document retrieval from app.agent")
            try:
                from app.agent import root_agent
                _agent_cache = root_agent
                logger.info("Successfully loaded full agent")
            except ImportError as e:
                error_msg = (
                    "Failed to import full agent from app.agent. "
                    "This may be due to missing dependencies for document retrieval. "
                    "Please ensure all required packages are installed and GCP is configured. "
                    f"Error: {e}"
                )
                logger.error(error_msg)
                raise ImportError(error_msg) from e
        else:
            logger.info("Loading simple agent (event planning only) from app.event_planning.simple_agent")
            try:
                from app.event_planning.simple_agent import event_planning_agent
                _agent_cache = event_planning_agent
                logger.info("Successfully loaded simple agent")
            except ImportError as e:
                error_msg = (
                    "Failed to import simple agent from app.event_planning.simple_agent. "
                    "Please ensure the module exists and all dependencies are installed. "
                    f"Error: {e}"
                )
                logger.error(error_msg)
                raise ImportError(error_msg) from e
                
    except Exception as e:
        error_msg = f"Unexpected error during agent initialization: {type(e).__name__}: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
    
    if _agent_cache is None:
        error_msg = "Agent initialization failed: agent is None after loading"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    return _agent_cache


def clear_agent_cache() -> None:
    """
    Clear the cached agent instance.
    
    This is useful when the environment configuration changes and you need
    to reload the agent with new settings.
    
    Example:
        >>> clear_agent_cache()
        >>> agent = get_agent()  # Will load fresh agent
    """
    global _agent_cache
    _agent_cache = None
    logger.info("Agent cache cleared")
