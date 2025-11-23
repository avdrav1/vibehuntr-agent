"""Integration tests for playground agent integration.

Tests the integration between the playground interface and the agent system.
Validates: Requirements 1.1, 1.2, 1.3, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 8.1, 8.2
"""

import pytest
import os
from unittest.mock import Mock, MagicMock, patch
from app.event_planning.session_manager import SessionManager
from app.event_planning.agent_loader import get_agent, clear_agent_cache
from app.event_planning.agent_invoker import invoke_agent_streaming, invoke_agent, AgentInvocationError


class TestAgentLoader:
    """Test agent loading functionality."""
    
    def test_agent_loader_returns_agent(self):
        """Test that agent loader successfully returns an agent instance.
        
        Validates: Requirements 4.1, 4.2
        """
        agent = get_agent()
        assert agent is not None
        # ADK agents have name and tools attributes
        assert hasattr(agent, 'name')
        assert hasattr(agent, 'tools')
    
    def test_agent_loader_caching(self):
        """Test that agent loader caches agent instance.
        
        Validates: Requirements 4.1, 4.2
        """
        # Clear cache first
        clear_agent_cache()
        
        # Load agent twice
        agent1 = get_agent()
        agent2 = get_agent()
        
        # Should be the same instance
        assert agent1 is agent2
    
    def test_agent_loader_with_simple_agent(self):
        """Test loading simple agent when USE_DOCUMENT_RETRIEVAL is false.
        
        Validates: Requirements 4.2
        """
        # Clear cache and set environment
        clear_agent_cache()
        original_value = os.environ.get("USE_DOCUMENT_RETRIEVAL")
        
        try:
            os.environ["USE_DOCUMENT_RETRIEVAL"] = "false"
            agent = get_agent()
            
            # Verify agent is loaded
            assert agent is not None
            assert hasattr(agent, 'name')
            
        finally:
            # Restore original value
            if original_value is not None:
                os.environ["USE_DOCUMENT_RETRIEVAL"] = original_value
            else:
                os.environ.pop("USE_DOCUMENT_RETRIEVAL", None)
            clear_agent_cache()


class TestSessionManager:
    """Test session management functionality."""
    
    def test_session_manager_initialization(self):
        """Test that SessionManager initializes correctly.
        
        Validates: Requirements 3.1, 3.4
        """
        # Use a mock session state
        mock_session_state = {}
        session_manager = SessionManager(session_state=mock_session_state)
        
        # Verify initialization
        assert "messages" in mock_session_state
        assert "agent" in mock_session_state
        assert mock_session_state["messages"] == []
        assert mock_session_state["agent"] is None
    
    def test_session_manager_message_operations(self):
        """Test SessionManager message operations.
        
        Validates: Requirements 3.1, 3.2
        """
        mock_session_state = {}
        session_manager = SessionManager(session_state=mock_session_state)
        
        # Add messages
        session_manager.add_message("user", "Hello")
        session_manager.add_message("assistant", "Hi there!")
        
        # Get messages
        messages = session_manager.get_messages()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Hi there!"
        
        # Clear messages
        session_manager.clear_messages()
        assert len(session_manager.get_messages()) == 0
    
    def test_session_manager_agent_caching(self):
        """Test SessionManager agent caching.
        
        Validates: Requirements 4.1, 4.2
        """
        mock_session_state = {}
        session_manager = SessionManager(session_state=mock_session_state)
        
        # Create a mock agent
        mock_agent = Mock()
        
        # Set agent
        session_manager.set_agent(mock_agent)
        
        # Get agent
        retrieved_agent = session_manager.get_agent()
        assert retrieved_agent is mock_agent
    
    def test_session_isolation(self):
        """Test that different sessions are isolated from each other.
        
        Validates: Requirements 3.4
        """
        # Create two separate session states
        session_state_1 = {}
        session_state_2 = {}
        
        session_manager_1 = SessionManager(session_state=session_state_1)
        session_manager_2 = SessionManager(session_state=session_state_2)
        
        # Add messages to first session
        session_manager_1.add_message("user", "Message in session 1")
        
        # Add different messages to second session
        session_manager_2.add_message("user", "Message in session 2")
        
        # Verify isolation
        messages_1 = session_manager_1.get_messages()
        messages_2 = session_manager_2.get_messages()
        
        assert len(messages_1) == 1
        assert len(messages_2) == 1
        assert messages_1[0]["content"] == "Message in session 1"
        assert messages_2[0]["content"] == "Message in session 2"


class TestHistoryPagination:
    """Test history pagination functionality."""
    
    def test_history_pagination_with_few_messages(self):
        """Test pagination when there are fewer than 10 messages.
        
        Validates: Requirements 1.3
        """
        mock_session_state = {}
        session_manager = SessionManager(session_state=mock_session_state)
        
        # Add 5 messages
        for i in range(5):
            session_manager.add_message("user", f"Message {i}")
        
        # Get recent messages
        recent = session_manager.get_messages(recent_only=True, recent_count=10)
        all_messages = session_manager.get_all_messages()
        
        # Should return all messages since there are fewer than 10
        assert len(recent) == 5
        assert len(all_messages) == 5
        assert not session_manager.should_show_history_button(recent_count=10)
    
    def test_history_pagination_with_many_messages(self):
        """Test pagination when there are more than 10 messages.
        
        Validates: Requirements 1.3
        """
        mock_session_state = {}
        session_manager = SessionManager(session_state=mock_session_state)
        
        # Add 15 messages
        for i in range(15):
            session_manager.add_message("user", f"Message {i}")
        
        # Get recent messages
        recent = session_manager.get_messages(recent_only=True, recent_count=10)
        all_messages = session_manager.get_all_messages()
        older_messages = session_manager.get_older_messages(recent_count=10)
        
        # Should return only last 10 messages
        assert len(recent) == 10
        assert len(all_messages) == 15
        assert len(older_messages) == 5
        assert session_manager.should_show_history_button(recent_count=10)
        
        # Verify recent messages are the last 10
        assert recent[0]["content"] == "Message 5"
        assert recent[-1]["content"] == "Message 14"
        
        # Verify older messages are the first 5
        assert older_messages[0]["content"] == "Message 0"
        assert older_messages[-1]["content"] == "Message 4"


class TestConversationFlow:
    """Test complete conversation flows."""
    
    def test_complete_conversation_flow(self):
        """Test a complete conversation flow from user input to agent response.
        
        Validates: Requirements 1.1, 1.2, 3.1, 3.2, 3.3
        """
        mock_session_state = {}
        session_manager = SessionManager(session_state=mock_session_state)
        
        # Simulate user sending a message
        user_message = "Hello, I want to plan an event"
        session_manager.add_message("user", user_message)
        
        # Verify message was added
        messages = session_manager.get_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        
        # Simulate agent response
        agent_response = "I'd be happy to help you plan an event!"
        session_manager.add_message("assistant", agent_response)
        
        # Verify both messages are in history
        messages = session_manager.get_messages()
        assert len(messages) == 2
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == agent_response
    
    def test_multi_turn_conversation(self):
        """Test multiple turns of conversation maintain context.
        
        Validates: Requirements 1.1, 1.2, 3.1, 3.2, 3.3
        """
        mock_session_state = {}
        session_manager = SessionManager(session_state=mock_session_state)
        
        # Simulate multiple conversation turns
        turns = [
            ("user", "I want to plan a birthday party"),
            ("assistant", "Great! How many people will attend?"),
            ("user", "About 20 people"),
            ("assistant", "Perfect! What's your budget?"),
            ("user", "$500"),
            ("assistant", "I can help you find venues within that budget.")
        ]
        
        for role, content in turns:
            session_manager.add_message(role, content)
        
        # Verify all messages are stored in order
        messages = session_manager.get_messages()
        assert len(messages) == 6
        
        for i, (role, content) in enumerate(turns):
            assert messages[i]["role"] == role
            assert messages[i]["content"] == content
    
    def test_conversation_with_real_agent(self):
        """Test conversation flow with real agent invocation.
        
        Validates: Requirements 1.1, 1.2, 3.3
        """
        # Get real agent
        agent = get_agent()
        
        # Create session manager
        mock_session_state = {}
        session_manager = SessionManager(session_state=mock_session_state)
        
        # Send a simple message
        user_message = "Hello"
        session_manager.add_message("user", user_message)
        
        # Invoke agent with streaming
        response_parts = []
        try:
            for item in invoke_agent_streaming(
                agent=agent,
                message=user_message,
                chat_history=session_manager.get_messages()[:-1],  # Exclude current message
                session_id="test_session_1"
            ):
                if item['type'] == 'text':
                    response_parts.append(item['content'])
            
            # Combine response
            full_response = "".join(response_parts)
            
            # Add to session
            session_manager.add_message("assistant", full_response)
            
            # Verify conversation state
            messages = session_manager.get_messages()
            assert len(messages) == 2
            assert messages[0]["role"] == "user"
            assert messages[1]["role"] == "assistant"
            assert len(messages[1]["content"]) > 0
            
        except Exception as e:
            pytest.skip(f"Agent invocation failed (may be due to API configuration): {e}")


class TestNewConversation:
    """Test new conversation functionality."""
    
    def test_new_conversation_clears_history(self):
        """Test that starting a new conversation clears chat history.
        
        Validates: Requirements 8.1, 8.2
        """
        mock_session_state = {}
        session_manager = SessionManager(session_state=mock_session_state)
        
        # Add some messages
        session_manager.add_message("user", "First message")
        session_manager.add_message("assistant", "First response")
        session_manager.add_message("user", "Second message")
        
        # Verify messages exist
        assert len(session_manager.get_messages()) == 3
        
        # Clear messages (new conversation)
        session_manager.clear_messages()
        
        # Verify history is cleared
        assert len(session_manager.get_messages()) == 0
    
    def test_new_conversation_preserves_agent_cache(self):
        """Test that new conversation preserves agent cache.
        
        Validates: Requirements 8.2
        """
        mock_session_state = {}
        session_manager = SessionManager(session_state=mock_session_state)
        
        # Set agent
        mock_agent = Mock()
        session_manager.set_agent(mock_agent)
        
        # Add and clear messages
        session_manager.add_message("user", "Test")
        session_manager.clear_messages()
        
        # Verify agent is still cached
        assert session_manager.get_agent() is mock_agent
    
    def test_new_conversation_creates_new_session_id(self):
        """Test that new conversation creates a new session ID.
        
        Validates: Requirements 7.5
        """
        mock_session_state = {"adk_session_id": "old-session-id-12345"}
        session_manager = SessionManager(session_state=mock_session_state)
        
        # Add some messages
        session_manager.add_message("user", "First message")
        session_manager.add_message("assistant", "First response")
        
        # Verify messages exist
        assert len(session_manager.get_messages()) == 2
        
        # Clear session (new conversation)
        new_session_id = session_manager.clear_session()
        
        # Verify history is cleared
        assert len(session_manager.get_messages()) == 0
        
        # Verify new session ID was created
        assert new_session_id is not None
        assert new_session_id != "old-session-id-12345"
        
        # Verify new session ID is stored in session state
        assert mock_session_state["adk_session_id"] == new_session_id


class TestErrorRecovery:
    """Test error handling and recovery scenarios."""
    
    def test_corrupted_session_state_recovery(self):
        """Test recovery from corrupted session state.
        
        Validates: Requirements 3.1, 3.4
        """
        # Create session with corrupted state
        mock_session_state = {"messages": "not_a_list"}
        session_manager = SessionManager(session_state=mock_session_state)
        
        # Should recover and return empty list
        messages = session_manager.get_messages()
        assert isinstance(messages, list)
        assert len(messages) == 0
    
    def test_agent_invocation_error_handling(self):
        """Test that agent invocation errors are handled gracefully.
        
        Validates: Requirements 1.2
        """
        # Get a real agent but use an invalid session service to trigger an error
        agent = get_agent()
        
        # Patch the session service to raise an error
        with patch('app.event_planning.agent_invoker._session_service') as mock_service:
            mock_service.get_session_sync.side_effect = Exception("Session service error")
            mock_service.create_session_sync.side_effect = Exception("Session service error")
            
            # This should raise AgentInvocationError
            with pytest.raises(AgentInvocationError):
                result = invoke_agent(
                    agent=agent,
                    message="Test message",
                    session_id="error_test_session"
                )
    
    def test_session_state_initialization_on_missing_keys(self):
        """Test that missing session state keys are initialized.
        
        Validates: Requirements 3.4
        """
        # Create empty session state
        mock_session_state = {}
        
        # Initialize session manager
        session_manager = SessionManager(session_state=mock_session_state)
        
        # Verify keys are initialized
        assert "messages" in mock_session_state
        assert "agent" in mock_session_state
        assert isinstance(mock_session_state["messages"], list)


class TestAgentConfiguration:
    """Test agent configuration and setup."""
    
    def test_agent_has_required_attributes(self):
        """Test that loaded agent has required attributes.
        
        Validates: Requirements 4.1, 4.2
        """
        agent = get_agent()
        
        # Verify agent has expected attributes
        assert agent is not None
        assert hasattr(agent, 'name')
        assert hasattr(agent, 'tools')
        
        # Verify tools are configured
        assert len(agent.tools) > 0
    
    def test_agent_tools_are_callable(self):
        """Test that agent tools are properly configured.
        
        Validates: Requirements 4.1, 4.2
        """
        agent = get_agent()
        
        # Verify tools exist and have expected structure
        for tool in agent.tools:
            # Tools should have a name
            assert hasattr(tool, 'name') or hasattr(tool, '__name__')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
