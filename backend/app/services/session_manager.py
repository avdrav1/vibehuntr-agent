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
        
        Args:
            session_id: Unique identifier for the session
            role: Role of the message sender ('user' or 'assistant')
            content: Content of the message
        """
        if session_id not in self.sessions:
            self.create_session(session_id)
        
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


# Global session manager instance
session_manager = SessionManager()
