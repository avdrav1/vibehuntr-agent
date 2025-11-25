"""Session manager module for managing conversation state and chat history.

This module provides session management functionality using Streamlit's session state
to maintain conversation context and chat history for UI display. ADK's session service
automatically maintains conversation history for the agent.

HYBRID APPROACH: Streamlit state manages UI display, ADK session service manages agent context.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from google.adk.agents import Agent

# Configure logging
logger = logging.getLogger(__name__)


class SessionError(Exception):
    """Custom exception for session-related errors.
    
    This exception is raised when session operations fail, such as
    state corruption, initialization failures, or message retrieval errors.
    """
    pass


class SessionManager:
    """Manages conversation sessions and chat history using Streamlit session state.
    
    This class provides a clean interface for managing chat messages, agent instances,
    and session state in a Streamlit application. It handles message persistence,
    history pagination, and agent caching.
    
    In the hybrid approach, this manages UI state while ADK's session service handles
    agent context automatically.
    
    Attributes:
        session_state: Reference to Streamlit's session state object
        
    Example:
        >>> import streamlit as st
        >>> session_manager = SessionManager()
        >>> session_manager.add_message("user", "Hello!")
        >>> messages = session_manager.get_messages()
    """
    
    def __init__(self, session_state=None):
        """Initialize session manager with Streamlit session state.
        
        Args:
            session_state: Streamlit session state object. If None, will attempt
                          to import and use st.session_state
        """
        if session_state is None:
            try:
                import streamlit as st
                self.session_state = st.session_state
            except ImportError:
                # For testing without Streamlit, use a simple dict
                logger.warning("Streamlit not available, using dict for session state")
                self.session_state = {}
        else:
            self.session_state = session_state
            
        # Initialize session state keys if they don't exist
        self._initialize_session_state()
    
    def _initialize_session_state(self) -> None:
        """Initialize session state keys if they don't exist."""
        if "messages" not in self.session_state:
            self.session_state["messages"] = []
            logger.debug("Initialized empty messages list in session state")
            
        if "agent" not in self.session_state:
            self.session_state["agent"] = None
            logger.debug("Initialized agent cache in session state")
    
    def get_messages(self, recent_only: bool = False, recent_count: int = 10) -> List[Dict[str, str]]:
        """Get chat history from Streamlit session state with optional pagination.
        
        Args:
            recent_only: If True, return only recent messages
            recent_count: Number of recent messages to return when recent_only=True
            
        Returns:
            List of message dictionaries with 'role' and 'content' keys
            
        Example:
            >>> # Get all messages
            >>> all_messages = session_manager.get_messages()
            >>> # Get only last 10 messages
            >>> recent = session_manager.get_messages(recent_only=True, recent_count=10)
        """
        messages = self.session_state.get("messages", [])
        
        if recent_only and len(messages) > recent_count:
            return messages[-recent_count:]
        
        return messages
    
    def get_all_messages(self) -> List[Dict[str, str]]:
        """Get complete chat history.
        
        Returns:
            List of all message dictionaries in chronological order
            
        Raises:
            SessionError: If session state is corrupted beyond recovery
            
        Example:
            >>> all_messages = session_manager.get_all_messages()
        """
        # Delegate to get_messages with recent_only=False
        return self.get_messages(recent_only=False)
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to chat history in Streamlit session state.
        
        This method includes duplicate prevention: if the last message in the
        history has the same role and content, the new message will not be added.
        This prevents accidental duplicate storage while still allowing legitimate
        repeated messages (e.g., user sends "hello" twice in different turns).
        
        Args:
            role: Message role, typically "user" or "assistant"
            content: Message content/text
            
        Example:
            >>> session_manager.add_message("user", "Hello!")
            >>> session_manager.add_message("assistant", "Hi there!")
        """
        if "messages" not in self.session_state:
            self.session_state["messages"] = []
        
        # Duplicate prevention: Check if the last message is identical
        # This prevents accidental duplicate storage from bugs in the calling code
        if self.session_state["messages"]:
            last_message = self.session_state["messages"][-1]
            if last_message["role"] == role and last_message["content"] == content:
                # This is a duplicate of the last message - skip adding it
                session_id = self.session_state.get("adk_session_id", "unknown")
                logger.warning(
                    f"Prevented duplicate message storage in session {session_id}: "
                    f"role={role}, content_length={len(content)}"
                )
                return
        
        message = {"role": role, "content": content}
        self.session_state["messages"].append(message)
        
        # Enhanced logging for session history updates
        session_id = self.session_state.get("adk_session_id", "unknown")
        logger.info(
            f"Session history updated - {role} message added",
            extra={
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "role": role,
                "content_length": len(content) if isinstance(content, str) else 0,
                "total_messages": len(self.session_state['messages']),
                "message_index": len(self.session_state['messages']) - 1
            }
        )
    
    def clear_messages(self) -> None:
        """Clear all messages from Streamlit session state.
        
        Example:
            >>> session_manager.clear_messages()
            >>> assert len(session_manager.get_messages()) == 0
        """
        self.session_state["messages"] = []
        logger.info(
            "Cleared all messages from Streamlit state",
            extra={
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def clear_session(self) -> str:
        """Clear session and create a new session ID.
        
        This starts a completely new conversation by:
        1. Clearing all messages from history
        2. Generating a new session ID for ADK
        
        The agent cache is preserved to avoid reloading.
        
        Returns:
            New session ID (UUID string)
            
        Raises:
            SessionError: If session cannot be cleared
        
        Example:
            >>> new_session_id = session_manager.clear_session()
            >>> assert len(session_manager.get_messages()) == 0
            >>> assert new_session_id != old_session_id
        """
        try:
            import uuid
            
            # Clear messages
            self.clear_messages()
            
            # Generate new session ID
            new_session_id = str(uuid.uuid4())
            
            # Store in session state if using Streamlit
            if "adk_session_id" in self.session_state:
                old_session_id = self.session_state.get("adk_session_id", "unknown")
                self.session_state["adk_session_id"] = new_session_id
                logger.info(
                    f"Created new session: {new_session_id} (previous: {old_session_id})",
                    extra={
                        "timestamp": datetime.now().isoformat(),
                        "old_session_id": old_session_id,
                        "new_session_id": new_session_id
                    }
                )
            else:
                logger.info(
                    f"Created new session: {new_session_id}",
                    extra={
                        "timestamp": datetime.now().isoformat(),
                        "new_session_id": new_session_id
                    }
                )
            
            return new_session_id
            
        except Exception as e:
            error_msg = f"Failed to clear session: {type(e).__name__}: {e}"
            logger.error(
                error_msg,
                extra={
                    "timestamp": datetime.now().isoformat()
                },
                exc_info=True
            )
            raise SessionError(error_msg) from e
    
    def get_agent(self) -> Optional[Agent]:
        """Get cached agent instance from session state.
        
        Returns:
            Agent instance if cached, None otherwise
            
        Example:
            >>> agent = session_manager.get_agent()
            >>> if agent is None:
            >>>     agent = load_agent()
            >>>     session_manager.set_agent(agent)
        """
        return self.session_state.get("agent")
    
    def set_agent(self, agent: Agent) -> None:
        """Cache agent instance in session state.
        
        Args:
            agent: Agent instance to cache
            
        Example:
            >>> from app.event_planning.agent_loader import get_agent
            >>> agent = get_agent()
            >>> session_manager.set_agent(agent)
        """
        self.session_state["agent"] = agent
        logger.debug("Cached agent instance in session state")
    
    def should_show_history_button(self, recent_count: int = 10) -> bool:
        """Check if there are older messages beyond the recent count.
        
        This is useful for determining whether to show a "Show Older Messages"
        button or expander in the UI.
        
        Args:
            recent_count: Number of recent messages displayed by default
            
        Returns:
            True if there are more than recent_count messages, False otherwise
            
        Example:
            >>> if session_manager.should_show_history_button():
            >>>     st.expander("Show Older Messages")
        """
        messages = self.session_state.get("messages", [])
        return len(messages) > recent_count
    
    def get_older_messages(self, recent_count: int = 10) -> List[Dict[str, str]]:
        """Get messages that are older than the recent count.
        
        This returns all messages except the most recent ones, useful for
        displaying in a "Show Older Messages" section.
        
        Args:
            recent_count: Number of recent messages to exclude
            
        Returns:
            List of older message dictionaries
            
        Example:
            >>> older = session_manager.get_older_messages(recent_count=10)
            >>> for msg in older:
            >>>     display_message(msg)
        """
        messages = self.session_state.get("messages", [])
        
        if len(messages) <= recent_count:
            return []
        
        return messages[:-recent_count]
