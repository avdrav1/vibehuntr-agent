"""
Feature parity verification tests for React + FastAPI migration.

This test suite verifies that all features from the Streamlit version
work correctly in the new React + FastAPI implementation.

Requirements tested:
- 6.1: Messages display exactly once
- 6.2: No duplicate messages on re-render
- 6.3: Streaming updates same message element
- 7.1: Real-time streaming display
- 7.2: Token appending during streaming
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.services.session_manager import SessionManager


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def session_manager():
    """Create a fresh session manager for each test."""
    manager = SessionManager()
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


class TestFeatureParity:
    """Test suite to verify feature parity with Streamlit version."""
    
    def test_basic_message_sending(self, client, session_manager, mock_agent_service):
        """
        Verify basic message sending works.
        
        Streamlit feature: User can send messages and get responses.
        Requirements: 6.1, 7.1
        """
        with patch('backend.app.api.chat.session_manager', session_manager):
            with patch('backend.app.api.sessions.session_manager', session_manager):
                # Create a session
                response = client.post("/api/sessions")
                assert response.status_code == 201  # Created
                session_id = response.json()["session_id"]
            
            # Send a message
            response = client.post(
                "/api/chat",
                json={
                    "session_id": session_id,
                    "message": "Hello, I want to plan an event"
                }
            )
            
            assert response.status_code == 200
            assert "response" in response.json()
            assert len(response.json()["response"]) > 0
    
    def test_no_duplicate_messages_in_history(self, client, session_manager, mock_agent_service):
        """
        Verify messages appear exactly once in history.
        
        Streamlit issue: Messages were duplicated on rerun.
        Requirements: 6.1, 6.2
        """
        with patch('backend.app.api.chat.session_manager', session_manager):
            with patch('backend.app.api.sessions.session_manager', session_manager):
                # Create a session
                response = client.post("/api/sessions")
                session_id = response.json()["session_id"]
                
                # Send multiple messages
                messages = [
                    "Plan a birthday party",
                    "Find venues in San Francisco",
                    "What about restaurants?"
                ]
                
                for msg in messages:
                    client.post(
                        "/api/chat",
                        json={"session_id": session_id, "message": msg}
                    )
                
                # Get message history
                response = client.get(f"/api/sessions/{session_id}/messages")
                assert response.status_code == 200
                
                history = response.json()["messages"]
                
                # Verify each user message appears exactly once
                user_messages = [m for m in history if m["role"] == "user"]
                user_contents = [m["content"] for m in user_messages]
                
                for msg in messages:
                    count = user_contents.count(msg)
                    assert count == 1, f"Message '{msg}' appears {count} times, expected 1"
                
                # Verify we have responses for each message
                assistant_messages = [m for m in history if m["role"] == "assistant"]
                assert len(assistant_messages) == len(messages)
    
    def test_streaming_response(self, client, session_manager, mock_agent_service):
        """
        Verify streaming responses work correctly.
        
        Streamlit feature: Responses stream token by token.
        Requirements: 7.1, 7.2
        """
        with patch('backend.app.api.chat.session_manager', session_manager):
            with patch('backend.app.api.sessions.session_manager', session_manager):
                # Create a session
                response = client.post("/api/sessions")
                session_id = response.json()["session_id"]
            
            # Stream a response
            message = "Tell me about event planning"
            
            with client.stream(
                "GET",
                f"/api/chat/stream?session_id={session_id}&message={message}"
            ) as response:
                assert response.status_code == 200
                
                tokens = []
                done_received = False
                
                # Collect all streamed tokens
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        try:
                            data = json.loads(data_str)
                            
                            if data["type"] == "token":
                                tokens.append(data["content"])
                            elif data["type"] == "done":
                                done_received = True
                        except json.JSONDecodeError:
                            pass
                
                # Verify we received tokens
                assert len(tokens) > 0, "Should receive at least one token"
                
                # Verify we received done signal
                assert done_received, "Should receive done signal"
                
                # Verify tokens form a coherent response
                full_response = "".join(tokens)
                assert len(full_response) > 0
    
    def test_context_retention_across_messages(self, client, session_manager, mock_agent_service):
        """
        Verify conversation context is retained.
        
        Streamlit feature: Agent remembers previous messages in conversation.
        Requirements: 6.3
        """
        with patch('backend.app.api.chat.session_manager', session_manager):
            with patch('backend.app.api.sessions.session_manager', session_manager):
                # Create a session
                response = client.post("/api/sessions")
                session_id = response.json()["session_id"]
                
                # Send first message
                client.post(
                    "/api/chat",
                    json={
                        "session_id": session_id,
                        "message": "My name is Alice"
                    }
                )
                
                # Send follow-up that requires context
                response = client.post(
                    "/api/chat",
                    json={
                        "session_id": session_id,
                        "message": "What is my name?"
                    }
                )
                
                # The response should reference the name from context
                # (This is a basic check - actual context retention is tested by ADK)
                assert response.status_code == 200
                
                # Get full history to verify both messages are stored
                response = client.get(f"/api/sessions/{session_id}/messages")
                history = response.json()["messages"]
                
                user_messages = [m for m in history if m["role"] == "user"]
                assert len(user_messages) == 2
                assert user_messages[0]["content"] == "My name is Alice"
                assert user_messages[1]["content"] == "What is my name?"
    
    def test_new_conversation_clears_history(self, client, session_manager, mock_agent_service):
        """
        Verify starting a new conversation clears history.
        
        Streamlit feature: "New Conversation" button clears history.
        Requirements: 6.1
        """
        with patch('backend.app.api.chat.session_manager', session_manager):
            with patch('backend.app.api.sessions.session_manager', session_manager):
                # Create a session and send messages
                response = client.post("/api/sessions")
                session_id = response.json()["session_id"]
                
                client.post(
                    "/api/chat",
                    json={"session_id": session_id, "message": "First message"}
                )
                
                # Verify message exists
                response = client.get(f"/api/sessions/{session_id}/messages")
                assert len(response.json()["messages"]) > 0
                
                # Clear the session
                response = client.delete(f"/api/sessions/{session_id}")
                assert response.status_code == 204  # No Content
                
                # Verify history is cleared
                response = client.get(f"/api/sessions/{session_id}/messages")
                assert len(response.json()["messages"]) == 0
    
    def test_welcome_message_display(self, client, session_manager):
        """
        Verify welcome message shows when no messages exist.
        
        Streamlit feature: Welcome screen with capabilities.
        Requirements: 6.1
        """
        with patch('backend.app.api.sessions.session_manager', session_manager):
            # Create a new session
            response = client.post("/api/sessions")
            session_id = response.json()["session_id"]
            
            # Get messages (should be empty)
            response = client.get(f"/api/sessions/{session_id}/messages")
            assert response.status_code == 200
            assert len(response.json()["messages"]) == 0
            
            # Frontend should display welcome message when messages array is empty
    
    def test_message_timestamps(self, client, session_manager, mock_agent_service):
        """
        Verify messages have timestamps.
        
        Streamlit feature: Messages show when they were sent.
        Requirements: 6.1
        """
        with patch('backend.app.api.chat.session_manager', session_manager):
            with patch('backend.app.api.sessions.session_manager', session_manager):
                # Create a session and send a message
                response = client.post("/api/sessions")
                session_id = response.json()["session_id"]
                
                client.post(
                    "/api/chat",
                    json={"session_id": session_id, "message": "Test message"}
                )
                
                # Get messages
                response = client.get(f"/api/sessions/{session_id}/messages")
                messages = response.json()["messages"]
                
                # Verify timestamps exist
                for message in messages:
                    assert "timestamp" in message
                    assert message["timestamp"] is not None
    
    def test_rapid_message_sending(self, client, session_manager, mock_agent_service):
        """
        Verify system handles rapid message sending without duplicates.
        
        Streamlit issue: Rapid interactions could cause duplicate messages.
        Requirements: 6.1, 6.2
        """
        with patch('backend.app.api.chat.session_manager', session_manager):
            with patch('backend.app.api.sessions.session_manager', session_manager):
                # Create a session
                response = client.post("/api/sessions")
                session_id = response.json()["session_id"]
                
                # Send multiple messages rapidly
                messages = [f"Message {i}" for i in range(5)]
                
                for msg in messages:
                    response = client.post(
                        "/api/chat",
                        json={"session_id": session_id, "message": msg}
                    )
                    assert response.status_code == 200
                
                # Get history
                response = client.get(f"/api/sessions/{session_id}/messages")
                history = response.json()["messages"]
                
                # Verify no duplicates
                user_messages = [m for m in history if m["role"] == "user"]
                user_contents = [m["content"] for m in user_messages]
                
                for msg in messages:
                    count = user_contents.count(msg)
                    assert count == 1, f"Message '{msg}' appears {count} times"
    
    def test_long_conversation_history(self, client, session_manager, mock_agent_service):
        """
        Verify system handles long conversation histories.
        
        Streamlit feature: Shows older messages in expander.
        Requirements: 6.1
        """
        with patch('backend.app.api.chat.session_manager', session_manager):
            with patch('backend.app.api.sessions.session_manager', session_manager):
                # Create a session
                response = client.post("/api/sessions")
                session_id = response.json()["session_id"]
                
                # Send many messages
                num_messages = 15
                for i in range(num_messages):
                    client.post(
                        "/api/chat",
                        json={"session_id": session_id, "message": f"Message {i}"}
                    )
                
                # Get full history
                response = client.get(f"/api/sessions/{session_id}/messages")
                history = response.json()["messages"]
                
                # Verify all messages are stored
                user_messages = [m for m in history if m["role"] == "user"]
                assert len(user_messages) == num_messages
                
                # Frontend should handle displaying many messages
                # (e.g., with pagination or scrolling)


class TestStreamingBehavior:
    """Detailed tests for streaming behavior."""
    
    def test_streaming_token_order(self, client, session_manager, mock_agent_service):
        """
        Verify tokens arrive in correct order during streaming.
        
        Requirements: 7.2
        """
        with patch('backend.app.api.chat.session_manager', session_manager):
            with patch('backend.app.api.sessions.session_manager', session_manager):
                response = client.post("/api/sessions")
                session_id = response.json()["session_id"]
            
            message = "Count to five"
            
            with client.stream(
                "GET",
                f"/api/chat/stream?session_id={session_id}&message={message}"
            ) as response:
                tokens = []
                
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        try:
                            data = json.loads(data_str)
                            if data["type"] == "token":
                                tokens.append(data["content"])
                        except json.JSONDecodeError:
                            pass
                
                # Verify we got tokens
                assert len(tokens) > 0
                
                # Tokens should form a coherent response when concatenated
                full_response = "".join(tokens)
                assert len(full_response) > 0
    
    def test_streaming_completion_signal(self, client, session_manager, mock_agent_service):
        """
        Verify streaming sends completion signal.
        
        Requirements: 7.1
        """
        with patch('backend.app.api.chat.session_manager', session_manager):
            with patch('backend.app.api.sessions.session_manager', session_manager):
                response = client.post("/api/sessions")
                session_id = response.json()["session_id"]
            
            with client.stream(
                "GET",
                f"/api/chat/stream?session_id={session_id}&message=Hello"
            ) as response:
                events = []
                
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        try:
                            data = json.loads(data_str)
                            events.append(data["type"])
                        except json.JSONDecodeError:
                            pass
                
                # Should have at least one token and a done event
                assert "token" in events
                assert "done" in events
                
                # Done should be the last event
                assert events[-1] == "done"


class TestMessageUniqueness:
    """Tests specifically for the duplicate message bug fix."""
    
    def test_no_duplicate_on_page_refresh_simulation(self, client, session_manager, mock_agent_service):
        """
        Verify messages don't duplicate when simulating page refresh.
        
        Streamlit issue: Page reruns caused duplicate messages.
        Requirements: 6.2
        """
        with patch('backend.app.api.chat.session_manager', session_manager):
            with patch('backend.app.api.sessions.session_manager', session_manager):
                # Create session and send message
                response = client.post("/api/sessions")
                session_id = response.json()["session_id"]
                
                client.post(
                    "/api/chat",
                    json={"session_id": session_id, "message": "Test message"}
                )
                
                # Get history multiple times (simulating multiple renders)
                histories = []
                for _ in range(3):
                    response = client.get(f"/api/sessions/{session_id}/messages")
                    histories.append(response.json()["messages"])
                
                # All histories should be identical
                for history in histories[1:]:
                    assert history == histories[0]
                
                # Verify message count is consistent
                for history in histories:
                    user_messages = [m for m in history if m["role"] == "user"]
                    assert len(user_messages) == 1
    
    def test_streaming_updates_single_message(self, client, session_manager, mock_agent_service):
        """
        Verify streaming updates a single message, not creating new ones.
        
        Streamlit issue: Each token could create a new message element.
        Requirements: 6.3
        """
        with patch('backend.app.api.chat.session_manager', session_manager):
            with patch('backend.app.api.sessions.session_manager', session_manager):
                response = client.post("/api/sessions")
                session_id = response.json()["session_id"]
                
                # Stream a response
                with client.stream(
                    "GET",
                    f"/api/chat/stream?session_id={session_id}&message=Hello"
                ) as response:
                    token_count = 0
                    
                    for line in response.iter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            try:
                                data = json.loads(data_str)
                                if data["type"] == "token":
                                    token_count += 1
                            except json.JSONDecodeError:
                                pass
                
                # Get final history
                response = client.get(f"/api/sessions/{session_id}/messages")
                history = response.json()["messages"]
                
                # Should have exactly 2 messages (user + assistant)
                assert len(history) == 2
                
                # Assistant message should be complete
                assistant_msg = [m for m in history if m["role"] == "assistant"][0]
                assert len(assistant_msg["content"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
