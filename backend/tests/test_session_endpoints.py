"""Tests for session API endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.session_manager import session_manager


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_sessions():
    """Clear all sessions before each test."""
    session_manager.sessions.clear()
    yield
    session_manager.sessions.clear()


def test_create_session(client):
    """Test creating a new session.
    
    Requirements: 3.1, 4.4
    """
    response = client.post("/api/sessions")
    
    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data
    assert isinstance(data["session_id"], str)
    assert len(data["session_id"]) > 0
    
    # Verify session was created in session manager
    assert session_manager.session_exists(data["session_id"])


def test_create_multiple_sessions(client):
    """Test creating multiple sessions generates unique IDs."""
    response1 = client.post("/api/sessions")
    response2 = client.post("/api/sessions")
    
    assert response1.status_code == 201
    assert response2.status_code == 201
    
    session_id1 = response1.json()["session_id"]
    session_id2 = response2.json()["session_id"]
    
    # Session IDs should be unique
    assert session_id1 != session_id2


def test_get_messages_empty_session(client):
    """Test getting messages from an empty session.
    
    Requirements: 3.4, 4.3
    """
    # Create a session first
    create_response = client.post("/api/sessions")
    session_id = create_response.json()["session_id"]
    
    # Get messages
    response = client.get(f"/api/sessions/{session_id}/messages")
    
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert data["messages"] == []


def test_get_messages_with_history(client):
    """Test getting messages from a session with history."""
    # Create a session
    create_response = client.post("/api/sessions")
    session_id = create_response.json()["session_id"]
    
    # Add some messages directly to session manager
    session_manager.add_message(session_id, "user", "Hello")
    session_manager.add_message(session_id, "assistant", "Hi there!")
    session_manager.add_message(session_id, "user", "How are you?")
    
    # Get messages
    response = client.get(f"/api/sessions/{session_id}/messages")
    
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert len(data["messages"]) == 3
    
    # Verify message content
    messages = data["messages"]
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Hi there!"
    assert messages[2]["role"] == "user"
    assert messages[2]["content"] == "How are you?"
    
    # Verify timestamps are present
    for msg in messages:
        assert "timestamp" in msg


def test_get_messages_nonexistent_session(client):
    """Test getting messages from a session that doesn't exist."""
    response = client.get("/api/sessions/nonexistent-session-id/messages")
    
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "not found" in data["error"].lower()


def test_clear_session(client):
    """Test clearing a session's message history.
    
    Requirements: 3.5, 4.5
    """
    # Create a session
    create_response = client.post("/api/sessions")
    session_id = create_response.json()["session_id"]
    
    # Add some messages
    session_manager.add_message(session_id, "user", "Hello")
    session_manager.add_message(session_id, "assistant", "Hi!")
    
    # Verify messages exist
    messages_before = session_manager.get_messages(session_id)
    assert len(messages_before) == 2
    
    # Clear session
    response = client.delete(f"/api/sessions/{session_id}")
    
    assert response.status_code == 204
    assert response.content == b""  # No content in response
    
    # Verify messages were cleared
    messages_after = session_manager.get_messages(session_id)
    assert len(messages_after) == 0
    
    # Verify session still exists
    assert session_manager.session_exists(session_id)


def test_clear_nonexistent_session(client):
    """Test clearing a session that doesn't exist."""
    response = client.delete("/api/sessions/nonexistent-session-id")
    
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "not found" in data["error"].lower()


def test_session_workflow(client):
    """Test complete session workflow: create, use, get history, clear."""
    # 1. Create session
    create_response = client.post("/api/sessions")
    assert create_response.status_code == 201
    session_id = create_response.json()["session_id"]
    
    # 2. Add messages
    session_manager.add_message(session_id, "user", "First message")
    session_manager.add_message(session_id, "assistant", "First response")
    
    # 3. Get history
    history_response = client.get(f"/api/sessions/{session_id}/messages")
    assert history_response.status_code == 200
    assert len(history_response.json()["messages"]) == 2
    
    # 4. Clear session
    clear_response = client.delete(f"/api/sessions/{session_id}")
    assert clear_response.status_code == 204
    
    # 5. Verify cleared
    final_history = client.get(f"/api/sessions/{session_id}/messages")
    assert final_history.status_code == 200
    assert len(final_history.json()["messages"]) == 0
