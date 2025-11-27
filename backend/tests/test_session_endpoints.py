"""Tests for session API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.session_manager import session_manager


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
    """Test getting messages from a session with history.
    
    Note: This test patches the ADK import to raise an exception,
    forcing the endpoint to fall back to session_manager.
    """
    from unittest.mock import patch
    
    # Create a session
    create_response = client.post("/api/sessions")
    session_id = create_response.json()["session_id"]
    
    # Add some messages directly to session manager
    session_manager.add_message(session_id, "user", "Hello")
    session_manager.add_message(session_id, "assistant", "Hi there!")
    session_manager.add_message(session_id, "user", "How are you?")
    
    # Patch the ADK import to raise an exception, forcing fallback to session_manager
    with patch.dict("sys.modules", {"app.event_planning.agent_invoker": None}):
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


def test_delete_session(client):
    """Test deleting a session completely.
    
    Requirements: 1.6
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
    
    # Delete session
    response = client.delete(f"/api/sessions/{session_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Verify session no longer exists
    assert not session_manager.session_exists(session_id)


def test_delete_nonexistent_session(client):
    """Test deleting a session that doesn't exist."""
    response = client.delete("/api/sessions/nonexistent-session-id")
    
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "not found" in data["error"].lower()


def test_session_workflow(client):
    """Test complete session workflow: create, use, get history, delete."""
    from unittest.mock import patch
    
    # 1. Create session
    create_response = client.post("/api/sessions")
    assert create_response.status_code == 201
    session_id = create_response.json()["session_id"]
    
    # 2. Add messages
    session_manager.add_message(session_id, "user", "First message")
    session_manager.add_message(session_id, "assistant", "First response")
    
    # 3. Get history (patch ADK to force fallback to session_manager)
    with patch.dict("sys.modules", {"app.event_planning.agent_invoker": None}):
        history_response = client.get(f"/api/sessions/{session_id}/messages")
        assert history_response.status_code == 200
        assert len(history_response.json()["messages"]) == 2
    
    # 4. Delete session
    delete_response = client.delete(f"/api/sessions/{session_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["success"] is True
    
    # 5. Verify session no longer exists
    final_history = client.get(f"/api/sessions/{session_id}/messages")
    assert final_history.status_code == 404


def test_list_sessions_empty(client):
    """Test listing sessions when none exist.
    
    Requirements: 1.1
    """
    response = client.get("/api/sessions")
    
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert data["sessions"] == []


def test_list_sessions_with_data(client):
    """Test listing sessions with data.
    
    Requirements: 1.1, 1.4
    """
    # Create sessions and add messages
    create_response1 = client.post("/api/sessions")
    session_id1 = create_response1.json()["session_id"]
    session_manager.add_message(session_id1, "user", "Hello from session 1")
    
    create_response2 = client.post("/api/sessions")
    session_id2 = create_response2.json()["session_id"]
    session_manager.add_message(session_id2, "user", "Hello from session 2")
    session_manager.add_message(session_id2, "assistant", "Response in session 2")
    
    # List sessions
    response = client.get("/api/sessions")
    
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert len(data["sessions"]) == 2
    
    # Verify session summaries have required fields
    for session in data["sessions"]:
        assert "id" in session
        assert "preview" in session
        assert "timestamp" in session
        assert "messageCount" in session


def test_list_sessions_preview_matches_first_message(client):
    """Test that session preview matches first message content.
    
    Requirements: 1.4
    """
    # Create a session with a specific first message
    create_response = client.post("/api/sessions")
    session_id = create_response.json()["session_id"]
    first_message = "This is my first message in the conversation"
    session_manager.add_message(session_id, "user", first_message)
    session_manager.add_message(session_id, "assistant", "This is a response")
    
    # List sessions
    response = client.get("/api/sessions")
    
    assert response.status_code == 200
    sessions = response.json()["sessions"]
    
    # Find our session
    our_session = next(s for s in sessions if s["id"] == session_id)
    
    # Preview should contain the first message content
    assert first_message in our_session["preview"] or our_session["preview"] in first_message


def test_deleted_session_not_in_list(client):
    """Test that deleted sessions don't appear in the list.
    
    Requirements: 1.6
    """
    # Create two sessions
    create_response1 = client.post("/api/sessions")
    session_id1 = create_response1.json()["session_id"]
    session_manager.add_message(session_id1, "user", "Session 1 message")
    
    create_response2 = client.post("/api/sessions")
    session_id2 = create_response2.json()["session_id"]
    session_manager.add_message(session_id2, "user", "Session 2 message")
    
    # Verify both sessions are in the list
    list_response = client.get("/api/sessions")
    session_ids = [s["id"] for s in list_response.json()["sessions"]]
    assert session_id1 in session_ids
    assert session_id2 in session_ids
    
    # Delete session 1
    delete_response = client.delete(f"/api/sessions/{session_id1}")
    assert delete_response.status_code == 200
    
    # Verify session 1 is no longer in the list
    list_response2 = client.get("/api/sessions")
    session_ids2 = [s["id"] for s in list_response2.json()["sessions"]]
    assert session_id1 not in session_ids2
    assert session_id2 in session_ids2
