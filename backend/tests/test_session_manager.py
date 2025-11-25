"""Tests for session manager service."""

import pytest
from app.services.session_manager import SessionManager, Message


def test_create_session():
    """Test creating a new session."""
    manager = SessionManager()
    session_id = "test-session-1"
    
    manager.create_session(session_id)
    
    assert manager.session_exists(session_id)
    assert len(manager.get_messages(session_id)) == 0


def test_add_message():
    """Test adding a message to a session."""
    manager = SessionManager()
    session_id = "test-session-2"
    
    manager.add_message(session_id, "user", "Hello")
    
    messages = manager.get_messages(session_id)
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello"
    assert "timestamp" in messages[0]


def test_add_message_creates_session_if_not_exists():
    """Test that adding a message creates session automatically."""
    manager = SessionManager()
    session_id = "test-session-3"
    
    # Session doesn't exist yet
    assert not manager.session_exists(session_id)
    
    # Add message should create session
    manager.add_message(session_id, "user", "Hello")
    
    assert manager.session_exists(session_id)
    assert len(manager.get_messages(session_id)) == 1


def test_get_messages():
    """Test retrieving messages from a session."""
    manager = SessionManager()
    session_id = "test-session-4"
    
    manager.add_message(session_id, "user", "Hello")
    manager.add_message(session_id, "assistant", "Hi there!")
    manager.add_message(session_id, "user", "How are you?")
    
    messages = manager.get_messages(session_id)
    assert len(messages) == 3
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[2]["role"] == "user"


def test_get_messages_nonexistent_session():
    """Test getting messages from a session that doesn't exist."""
    manager = SessionManager()
    
    messages = manager.get_messages("nonexistent-session")
    
    assert messages == []


def test_clear_session():
    """Test clearing a session's message history."""
    manager = SessionManager()
    session_id = "test-session-5"
    
    manager.add_message(session_id, "user", "Hello")
    manager.add_message(session_id, "assistant", "Hi!")
    
    assert len(manager.get_messages(session_id)) == 2
    
    manager.clear_session(session_id)
    
    assert len(manager.get_messages(session_id)) == 0
    assert manager.session_exists(session_id)  # Session still exists


def test_clear_nonexistent_session():
    """Test clearing a session that doesn't exist."""
    manager = SessionManager()
    
    # Should not raise an error
    manager.clear_session("nonexistent-session")


def test_get_session_count():
    """Test getting the total number of sessions."""
    manager = SessionManager()
    
    assert manager.get_session_count() == 0
    
    manager.create_session("session-1")
    assert manager.get_session_count() == 1
    
    manager.create_session("session-2")
    assert manager.get_session_count() == 2
