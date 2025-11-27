"""Session management service for maintaining conversation state and history.

This module provides in-memory session storage for managing chat conversations.
Each session maintains a list of messages with their roles and timestamps.
"""

from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class Message:
    """Represents a single message in a conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str


class SessionManager:
    """Manages conversation sessions and message history.
    
    This class provides in-memory storage for chat sessions, allowing
    creation, retrieval, and management of conversation histories.
    
    Attributes:
        sessions: Dictionary mapping session IDs to lists of messages
    """
    
    def __init__(self):
        """Initialize the session manager with empty session storage."""
        self.sessions: Dict[str, List[Message]] = {}
    
    def create_session(self, session_id: str) -> None:
        """Create a new session with the given ID.
        
        Args:
            session_id: Unique identifier for the session
        """
        self.sessions[session_id] = []
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to a session.
        
        If the session doesn't exist, it will be created automatically.
        
        This method includes duplicate prevention: if the last message in the
        session has the same role and content, the new message will not be added.
        This prevents accidental duplicate storage while still allowing legitimate
        repeated messages (e.g., user sends "hello" twice in different turns).
        
        Args:
            session_id: Unique identifier for the session
            role: Role of the message sender ('user' or 'assistant')
            content: Content of the message
        """
        if session_id not in self.sessions:
            self.create_session(session_id)
        
        # Duplicate prevention: Check if the last message is identical
        # This prevents accidental duplicate storage from bugs in the calling code
        if self.sessions[session_id]:
            last_message = self.sessions[session_id][-1]
            if last_message.role == role and last_message.content == content:
                # This is a duplicate of the last message - skip adding it
                # Log this for debugging purposes
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Prevented duplicate message storage in session {session_id}: "
                    f"role={role}, content_length={len(content)}"
                )
                return
        
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat()
        )
        self.sessions[session_id].append(message)
    
    def get_messages(self, session_id: str) -> List[Dict[str, str]]:
        """Get all messages for a session.
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            List of message dictionaries with role, content, and timestamp.
            Returns empty list if session doesn't exist.
        """
        messages = self.sessions.get(session_id, [])
        return [asdict(msg) for msg in messages]
    
    def clear_session(self, session_id: str) -> None:
        """Clear all messages from a session.
        
        The session ID remains valid but its message history is emptied.
        
        Args:
            session_id: Unique identifier for the session
        """
        if session_id in self.sessions:
            self.sessions[session_id] = []
    
    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists.
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            True if the session exists, False otherwise
        """
        return session_id in self.sessions
    
    def get_session_count(self) -> int:
        """Get the total number of sessions.
        
        Returns:
            Number of active sessions
        """
        return len(self.sessions)
    
    def get_all_sessions(self) -> List[Dict[str, any]]:
        """Get summaries of all sessions.
        
        Returns a list of session summaries with id, preview, timestamp,
        and messageCount for each session.
        
        Returns:
            List of session summary dictionaries
            
        Requirements: 1.1, 1.4
        """
        summaries = []
        for session_id, messages in self.sessions.items():
            # Get preview from first message (truncated to 100 chars)
            preview = ""
            if messages:
                first_msg = messages[0]
                preview = first_msg.content[:100] if len(first_msg.content) > 100 else first_msg.content
            
            # Get timestamp from last message, or empty string if no messages
            timestamp = ""
            if messages:
                timestamp = messages[-1].timestamp
            
            summaries.append({
                "id": session_id,
                "preview": preview,
                "timestamp": timestamp,
                "messageCount": len(messages)
            })
        
        # Sort by timestamp descending (newest first)
        summaries.sort(key=lambda x: x["timestamp"] or "", reverse=True)
        return summaries
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session completely.
        
        Unlike clear_session which keeps the session ID valid,
        this method removes the session entirely.
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            True if session was deleted, False if it didn't exist
            
        Requirements: 1.6
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False


# Global session manager instance
session_manager = SessionManager()
