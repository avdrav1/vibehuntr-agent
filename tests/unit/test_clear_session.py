"""Unit tests for clear_session functionality.

This module tests the new conversation functionality that clears messages
and creates a new session ID.
"""

import sys
import os
import pytest

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.event_planning.session_manager import SessionManager, SessionError


class MockSessionState(dict):
    """Mock Streamlit session state for testing."""
    pass


def test_clear_session_clears_messages():
    """Test that clear_session clears all messages."""
    # Create session manager with mock state
    mock_state = MockSessionState()
    mock_state["adk_session_id"] = "old-session-id"
    session_manager = SessionManager(session_state=mock_state)
    
    # Add some messages
    session_manager.add_message("user", "Hello")
    session_manager.add_message("assistant", "Hi there!")
    session_manager.add_message("user", "How are you?")
    
    # Verify messages exist
    assert len(session_manager.get_messages()) == 3
    
    # Clear session
    new_session_id = session_manager.clear_session()
    
    # Verify messages are cleared
    assert len(session_manager.get_messages()) == 0
    
    # Verify new session ID was returned
    assert new_session_id is not None
    assert isinstance(new_session_id, str)
    assert len(new_session_id) > 0


def test_clear_session_creates_new_session_id():
    """Test that clear_session creates a new session ID."""
    # Create session manager with mock state
    mock_state = MockSessionState()
    old_session_id = "old-session-id-12345"
    mock_state["adk_session_id"] = old_session_id
    session_manager = SessionManager(session_state=mock_state)
    
    # Add some messages
    session_manager.add_message("user", "Test message")
    
    # Clear session
    new_session_id = session_manager.clear_session()
    
    # Verify new session ID is different from old one
    assert new_session_id != old_session_id
    
    # Verify new session ID is stored in session state
    assert mock_state["adk_session_id"] == new_session_id


def test_clear_session_preserves_agent():
    """Test that clear_session preserves the cached agent."""
    # Create session manager with mock state
    mock_state = MockSessionState()
    mock_state["adk_session_id"] = "test-session-id"
    session_manager = SessionManager(session_state=mock_state)
    
    # Create a mock agent
    class MockAgent:
        pass
    
    mock_agent = MockAgent()
    
    # Cache the agent
    session_manager.set_agent(mock_agent)
    
    # Add some messages
    session_manager.add_message("user", "Test")
    
    # Clear session
    session_manager.clear_session()
    
    # Verify agent is still cached
    assert session_manager.get_agent() is mock_agent


def test_clear_session_with_empty_history():
    """Test that clear_session works even with empty history."""
    # Create session manager with mock state
    mock_state = MockSessionState()
    mock_state["adk_session_id"] = "test-session-id"
    session_manager = SessionManager(session_state=mock_state)
    
    # Don't add any messages
    assert len(session_manager.get_messages()) == 0
    
    # Clear session should still work
    new_session_id = session_manager.clear_session()
    
    # Verify it worked
    assert new_session_id is not None
    assert len(session_manager.get_messages()) == 0


def test_clear_session_without_adk_session_id():
    """Test that clear_session works even without adk_session_id in state."""
    # Create session manager with mock state (no adk_session_id)
    mock_state = MockSessionState()
    session_manager = SessionManager(session_state=mock_state)
    
    # Add some messages
    session_manager.add_message("user", "Test")
    
    # Clear session should still work
    new_session_id = session_manager.clear_session()
    
    # Verify it worked
    assert new_session_id is not None
    assert len(session_manager.get_messages()) == 0


def test_clear_session_returns_valid_uuid():
    """Test that clear_session returns a valid UUID string."""
    import uuid
    
    # Create session manager with mock state
    mock_state = MockSessionState()
    mock_state["adk_session_id"] = "old-id"
    session_manager = SessionManager(session_state=mock_state)
    
    # Clear session
    new_session_id = session_manager.clear_session()
    
    # Verify it's a valid UUID
    try:
        uuid.UUID(new_session_id)
        is_valid_uuid = True
    except ValueError:
        is_valid_uuid = False
    
    assert is_valid_uuid, f"Returned session ID is not a valid UUID: {new_session_id}"
