"""Tests for chat API endpoints.

This module tests the chat endpoints including both non-streaming
and SSE streaming functionality.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import json

from backend.app.main import app
from backend.app.services.session_manager import SessionManager


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def session_manager():
    """Create a fresh session manager for each test."""
    manager = SessionManager()
    # Create a test session
    manager.create_session("test-session-123")
    return manager


@pytest.fixture
def mock_agent_service():
    """Mock the agent service for testing."""
    with patch('backend.app.api.chat.get_agent_service') as mock:
        service = MagicMock()
        
        # Mock invoke_agent_async to return a simple response
        async def mock_invoke(*args, **kwargs):
            return "This is a test response from the agent."
        service.invoke_agent_async = mock_invoke
        
        # Mock stream_agent to yield tokens
        async def mock_stream(*args, **kwargs):
            tokens = ["This ", "is ", "a ", "streaming ", "response."]
            for token in tokens:
                yield {"type": "text", "content": token}
        service.stream_agent = mock_stream
        
        mock.return_value = service
        yield service


def test_send_message_success(client, session_manager, mock_agent_service):
    """Test successful non-streaming message send."""
    # Patch the global session_manager
    with patch('backend.app.api.chat.session_manager', session_manager):
        response = client.post(
            "/api/chat",
            json={
                "session_id": "test-session-123",
                "message": "Hello, agent!"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["response"] == "This is a test response from the agent."
    
    # Verify messages were added to session
    messages = session_manager.get_messages("test-session-123")
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello, agent!"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "This is a test response from the agent."


def test_send_message_invalid_session(client, session_manager, mock_agent_service):
    """Test sending message to non-existent session."""
    with patch('backend.app.api.chat.session_manager', session_manager):
        response = client.post(
            "/api/chat",
            json={
                "session_id": "non-existent-session",
                "message": "Hello!"
            }
        )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "does not exist" in data["error"]


def test_send_message_empty_message(client, session_manager, mock_agent_service):
    """Test sending empty message."""
    with patch('backend.app.api.chat.session_manager', session_manager):
        response = client.post(
            "/api/chat",
            json={
                "session_id": "test-session-123",
                "message": ""
            }
        )
    
    # Should fail validation
    assert response.status_code == 422


def test_stream_chat_success(client, session_manager, mock_agent_service):
    """Test successful SSE streaming."""
    with patch('backend.app.api.chat.session_manager', session_manager):
        with client.stream(
            "GET",
            "/api/chat/stream",
            params={
                "session_id": "test-session-123",
                "message": "Stream this!"
            }
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            
            # Collect events
            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    events.append(json.loads(data))
            
            # Should have token events and a done event
            assert len(events) > 0
            
            # Check token events
            token_events = [e for e in events if e.get("type") == "token"]
            assert len(token_events) == 5  # We yield 5 tokens in mock
            
            # Check done event
            done_events = [e for e in events if e.get("type") == "done"]
            assert len(done_events) == 1
    
    # Verify messages were added to session
    messages = session_manager.get_messages("test-session-123")
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Stream this!"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "This is a streaming response."


def test_stream_chat_invalid_session(client, session_manager, mock_agent_service):
    """Test streaming to non-existent session."""
    with patch('backend.app.api.chat.session_manager', session_manager):
        with client.stream(
            "GET",
            "/api/chat/stream",
            params={
                "session_id": "non-existent-session",
                "message": "Hello!"
            }
        ) as response:
            assert response.status_code == 200  # SSE always returns 200
            
            # Collect events
            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    events.append(json.loads(data))
            
            # Should have an error event
            assert len(events) > 0
            error_events = [e for e in events if e.get("type") == "error"]
            assert len(error_events) == 1
            assert "does not exist" in error_events[0]["content"]


def test_stream_chat_missing_message(client, session_manager, mock_agent_service):
    """Test streaming without message parameter."""
    with patch('backend.app.api.chat.session_manager', session_manager):
        response = client.get(
            "/api/chat/stream",
            params={
                "session_id": "test-session-123"
            }
        )
    
    # Should fail validation
    assert response.status_code == 422
