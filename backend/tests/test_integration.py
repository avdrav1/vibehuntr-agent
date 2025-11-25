"""Integration tests for React + FastAPI migration.

This module tests the full message flow, streaming end-to-end, and session management
to ensure all components work together correctly.

Requirements: 12.3, 12.5
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from app.main import app
from app.services.session_manager import session_manager


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_sessions():
    """Clear all sessions before and after each test."""
    session_manager.sessions.clear()
    yield
    session_manager.sessions.clear()


@pytest.fixture
def mock_agent_service():
    """Mock the agent service for integration testing."""
    with patch('backend.app.api.chat.get_agent_service') as mock:
        service = MagicMock()
        
        # Mock invoke_agent_async to return a response
        async def mock_invoke(*args, **kwargs):
            message = kwargs.get('message', args[0] if args else '')
            return f"Agent response to: {message}"
        service.invoke_agent_async = mock_invoke
        
        # Mock stream_agent to yield tokens
        async def mock_stream(*args, **kwargs):
            message = kwargs.get('message', args[0] if args else '')
            tokens = ["Agent ", "response ", "to: ", message]
            for token in tokens:
                yield {"type": "text", "content": token}
        service.stream_agent = mock_stream
        
        mock.return_value = service
        yield service



class TestFullMessageFlow:
    """
    Test complete message flow from user input to agent response.
    
    Requirements: 12.3 - Integration tests for full flow
    """
    
    def test_complete_message_flow_non_streaming(self, client, mock_agent_service):
        """Test full message flow with non-streaming endpoint."""
        # 1. Create a session
        create_response = client.post("/api/sessions")
        assert create_response.status_code == 201
        session_id = create_response.json()["session_id"]
        
        # 2. Send a message
        chat_response = client.post(
            "/api/chat",
            json={
                "session_id": session_id,
                "message": "Hello, agent!"
            }
        )
        assert chat_response.status_code == 200
        response_data = chat_response.json()
        assert "response" in response_data
        assert "Hello, agent!" in response_data["response"]
        
        # 3. Verify messages were stored in session
        history_response = client.get(f"/api/sessions/{session_id}/messages")
        assert history_response.status_code == 200
        messages = history_response.json()["messages"]
        
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello, agent!"
        assert messages[1]["role"] == "assistant"
        assert "Hello, agent!" in messages[1]["content"]
        
        # 4. Send another message to test conversation continuity
        chat_response2 = client.post(
            "/api/chat",
            json={
                "session_id": session_id,
                "message": "How are you?"
            }
        )
        assert chat_response2.status_code == 200
        
        # 5. Verify both exchanges are in history
        history_response2 = client.get(f"/api/sessions/{session_id}/messages")
        messages2 = history_response2.json()["messages"]
        assert len(messages2) == 4
        
    def test_complete_message_flow_with_streaming(self, client, mock_agent_service):
        """Test full message flow with streaming endpoint."""
        # 1. Create a session
        create_response = client.post("/api/sessions")
        assert create_response.status_code == 201
        session_id = create_response.json()["session_id"]
        
        # 2. Stream a message
        with client.stream(
            "GET",
            "/api/chat/stream",
            params={
                "session_id": session_id,
                "message": "Stream test"
            }
        ) as response:
            assert response.status_code == 200
            
            # Collect all events
            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    events.append(json.loads(data))
            
            # Verify we got tokens and done event
            token_events = [e for e in events if e.get("type") == "token"]
            done_events = [e for e in events if e.get("type") == "done"]
            
            assert len(token_events) > 0
            assert len(done_events) == 1
            
            # Reconstruct full response
            full_response = "".join(e["content"] for e in token_events)
            assert "Stream test" in full_response
        
        # 3. Verify messages were stored
        history_response = client.get(f"/api/sessions/{session_id}/messages")
        messages = history_response.json()["messages"]
        
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Stream test"
        assert messages[1]["role"] == "assistant"
        assert "Stream test" in messages[1]["content"]
    
    def test_multiple_sessions_isolation(self, client, mock_agent_service):
        """Test that multiple sessions maintain separate message histories."""
        # Create two sessions
        session1_response = client.post("/api/sessions")
        session1_id = session1_response.json()["session_id"]
        
        session2_response = client.post("/api/sessions")
        session2_id = session2_response.json()["session_id"]
        
        # Send different messages to each session
        client.post(
            "/api/chat",
            json={"session_id": session1_id, "message": "Session 1 message"}
        )
        
        client.post(
            "/api/chat",
            json={"session_id": session2_id, "message": "Session 2 message"}
        )
        
        # Verify each session has only its own messages
        history1 = client.get(f"/api/sessions/{session1_id}/messages")
        messages1 = history1.json()["messages"]
        assert len(messages1) == 2
        assert messages1[0]["content"] == "Session 1 message"
        
        history2 = client.get(f"/api/sessions/{session2_id}/messages")
        messages2 = history2.json()["messages"]
        assert len(messages2) == 2
        assert messages2[0]["content"] == "Session 2 message"




class TestStreamingEndToEnd:
    """
    Test streaming functionality end-to-end.
    
    Requirements: 12.3, 12.5 - Integration tests for streaming
    """
    
    def test_streaming_token_delivery(self, client, mock_agent_service):
        """Test that tokens are delivered correctly via SSE."""
        # Create session
        create_response = client.post("/api/sessions")
        session_id = create_response.json()["session_id"]
        
        # Start streaming
        with client.stream(
            "GET",
            "/api/chat/stream",
            params={"session_id": session_id, "message": "Test"}
        ) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]
            
            # Collect events in order
            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    events.append(data)
            
            # Verify event sequence
            assert len(events) > 0
            
            # All events except last should be tokens
            for event in events[:-1]:
                assert event["type"] == "token"
                assert "content" in event
            
            # Last event should be done
            assert events[-1]["type"] == "done"
    
    def test_streaming_with_multiple_messages(self, client, mock_agent_service):
        """Test streaming multiple messages in sequence."""
        # Create session
        create_response = client.post("/api/sessions")
        session_id = create_response.json()["session_id"]
        
        messages_to_send = ["First message", "Second message", "Third message"]
        
        for msg in messages_to_send:
            with client.stream(
                "GET",
                "/api/chat/stream",
                params={"session_id": session_id, "message": msg}
            ) as response:
                assert response.status_code == 200
                
                # Verify we get events
                events = []
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        events.append(json.loads(line[6:]))
                
                assert len(events) > 0
                assert events[-1]["type"] == "done"
        
        # Verify all messages are in history
        history = client.get(f"/api/sessions/{session_id}/messages")
        messages = history.json()["messages"]
        
        # Should have 6 messages (3 user + 3 assistant)
        assert len(messages) == 6
        
        # Verify order
        for i, msg in enumerate(messages_to_send):
            assert messages[i * 2]["role"] == "user"
            assert messages[i * 2]["content"] == msg
            assert messages[i * 2 + 1]["role"] == "assistant"
    
    def test_streaming_error_handling(self, client):
        """Test error handling during streaming."""
        # Create session
        create_response = client.post("/api/sessions")
        session_id = create_response.json()["session_id"]
        
        # Mock agent service to raise error
        with patch('backend.app.api.chat.get_agent_service') as mock:
            service = MagicMock()
            
            async def mock_stream_error(*args, **kwargs):
                yield {"type": "text", "content": "Start"}
                raise Exception("Streaming error")
            
            service.stream_agent = mock_stream_error
            mock.return_value = service
            
            # Start streaming
            with client.stream(
                "GET",
                "/api/chat/stream",
                params={"session_id": session_id, "message": "Test"}
            ) as response:
                assert response.status_code == 200
                
                # Collect events
                events = []
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        events.append(json.loads(line[6:]))
                
                # Should have at least one error event
                error_events = [e for e in events if e.get("type") == "error"]
                assert len(error_events) > 0
    
    def test_streaming_to_nonexistent_session(self, client, mock_agent_service):
        """Test streaming to a session that doesn't exist."""
        with client.stream(
            "GET",
            "/api/chat/stream",
            params={"session_id": "nonexistent", "message": "Test"}
        ) as response:
            assert response.status_code == 200
            
            # Collect events
            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    events.append(json.loads(line[6:]))
            
            # Should get error event
            assert len(events) > 0
            assert events[0]["type"] == "error"
            assert "does not exist" in events[0]["content"]




class TestSessionManagement:
    """
    Test session management integration.
    
    Requirements: 12.3, 12.5 - Integration tests for session management
    """
    
    def test_session_lifecycle(self, client, mock_agent_service):
        """Test complete session lifecycle: create, use, clear."""
        # 1. Create session
        create_response = client.post("/api/sessions")
        assert create_response.status_code == 201
        session_id = create_response.json()["session_id"]
        
        # 2. Verify session is empty
        history = client.get(f"/api/sessions/{session_id}/messages")
        assert history.status_code == 200
        assert len(history.json()["messages"]) == 0
        
        # 3. Add messages via chat
        client.post(
            "/api/chat",
            json={"session_id": session_id, "message": "Message 1"}
        )
        client.post(
            "/api/chat",
            json={"session_id": session_id, "message": "Message 2"}
        )
        
        # 4. Verify messages exist
        history = client.get(f"/api/sessions/{session_id}/messages")
        assert len(history.json()["messages"]) == 4
        
        # 5. Clear session
        clear_response = client.delete(f"/api/sessions/{session_id}")
        assert clear_response.status_code == 204
        
        # 6. Verify session is empty again
        history = client.get(f"/api/sessions/{session_id}/messages")
        assert len(history.json()["messages"]) == 0
    
    def test_session_persistence_across_requests(self, client, mock_agent_service):
        """Test that session data persists across multiple requests."""
        # Create session
        create_response = client.post("/api/sessions")
        session_id = create_response.json()["session_id"]
        
        # Send messages in separate requests
        for i in range(5):
            client.post(
                "/api/chat",
                json={"session_id": session_id, "message": f"Message {i}"}
            )
        
        # Verify all messages are stored
        history = client.get(f"/api/sessions/{session_id}/messages")
        messages = history.json()["messages"]
        
        assert len(messages) == 10  # 5 user + 5 assistant
        
        # Verify order is maintained
        for i in range(5):
            assert messages[i * 2]["content"] == f"Message {i}"
    
    def test_session_timestamps(self, client, mock_agent_service):
        """Test that messages have timestamps."""
        # Create session and send message
        create_response = client.post("/api/sessions")
        session_id = create_response.json()["session_id"]
        
        client.post(
            "/api/chat",
            json={"session_id": session_id, "message": "Test"}
        )
        
        # Get messages
        history = client.get(f"/api/sessions/{session_id}/messages")
        messages = history.json()["messages"]
        
        # Verify timestamps exist and are valid
        for msg in messages:
            assert "timestamp" in msg
            assert msg["timestamp"] is not None
            # Verify timestamp format (ISO 8601)
            assert "T" in msg["timestamp"]
    
    def test_concurrent_sessions(self, client, mock_agent_service):
        """Test handling multiple concurrent sessions."""
        # Create multiple sessions
        session_ids = []
        for i in range(3):
            response = client.post("/api/sessions")
            session_ids.append(response.json()["session_id"])
        
        # Send messages to all sessions
        for i, session_id in enumerate(session_ids):
            client.post(
                "/api/chat",
                json={"session_id": session_id, "message": f"Session {i} message"}
            )
        
        # Verify each session has correct messages
        for i, session_id in enumerate(session_ids):
            history = client.get(f"/api/sessions/{session_id}/messages")
            messages = history.json()["messages"]
            
            assert len(messages) == 2
            assert messages[0]["content"] == f"Session {i} message"
    
    def test_session_clear_preserves_session(self, client, mock_agent_service):
        """Test that clearing a session preserves the session ID."""
        # Create session
        create_response = client.post("/api/sessions")
        session_id = create_response.json()["session_id"]
        
        # Add messages
        client.post(
            "/api/chat",
            json={"session_id": session_id, "message": "Test"}
        )
        
        # Clear session
        client.delete(f"/api/sessions/{session_id}")
        
        # Verify we can still use the session
        response = client.post(
            "/api/chat",
            json={"session_id": session_id, "message": "After clear"}
        )
        assert response.status_code == 200
        
        # Verify only new message is in history
        history = client.get(f"/api/sessions/{session_id}/messages")
        messages = history.json()["messages"]
        assert len(messages) == 2
        assert messages[0]["content"] == "After clear"




class TestErrorHandlingIntegration:
    """
    Test error handling across the full stack.
    
    Requirements: 12.3 - Integration tests including error scenarios
    """
    
    def test_invalid_session_error_flow(self, client, mock_agent_service):
        """Test error handling when using invalid session."""
        # Try to send message to non-existent session
        response = client.post(
            "/api/chat",
            json={"session_id": "invalid-session", "message": "Test"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "does not exist" in data["error"]
    
    def test_empty_message_validation(self, client):
        """Test validation of empty messages."""
        # Create session
        create_response = client.post("/api/sessions")
        session_id = create_response.json()["session_id"]
        
        # Try to send empty message
        response = client.post(
            "/api/chat",
            json={"session_id": session_id, "message": ""}
        )
        
        # Should fail validation
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client):
        """Test validation when required fields are missing."""
        # Missing message field
        response = client.post(
            "/api/chat",
            json={"session_id": "test"}
        )
        assert response.status_code == 422
        
        # Missing session_id field
        response = client.post(
            "/api/chat",
            json={"message": "test"}
        )
        assert response.status_code == 422
    
    def test_agent_error_propagation(self, client):
        """Test that agent errors are properly propagated to client."""
        # Create session
        create_response = client.post("/api/sessions")
        session_id = create_response.json()["session_id"]
        
        # Mock agent service to raise error
        with patch('backend.app.api.chat.get_agent_service') as mock:
            from app.services.agent_service import AgentInvocationError
            
            service = MagicMock()
            
            async def mock_invoke_error(*args, **kwargs):
                raise AgentInvocationError("Agent failed")
            
            service.invoke_agent_async = mock_invoke_error
            mock.return_value = service
            
            # Send message
            response = client.post(
                "/api/chat",
                json={"session_id": session_id, "message": "Test"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "error" in data
            assert "Agent" in data["error"]




class TestHealthAndMetadata:
    """Test health check and metadata endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "docs" in data
        assert "health" in data


class TestCORSConfiguration:
    """Test CORS configuration for frontend-backend communication."""
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses."""
        # Make a request with Origin header
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:5173"}
        )
        
        assert response.status_code == 200
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers
    
    def test_preflight_request(self, client):
        """Test CORS preflight request handling."""
        response = client.options(
            "/api/chat",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type"
            }
        )
        
        # Should allow the request
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers

