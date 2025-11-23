"""Unit tests for agent invoker module.

This module tests the agent invocation logic including message formatting,
error handling, and logging behavior.
"""

import pytest
import logging
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock

from app.event_planning.agent_invoker import (
    invoke_agent_streaming,
    invoke_agent,
    AgentInvocationError
)


# Mock agent classes for testing

class MockAgent:
    """Mock ADK agent for testing."""
    
    def __init__(self, response: str = "Test response", should_fail: bool = False):
        self.response = response
        self.should_fail = should_fail
        self.last_input = None
        self.call_count = 0
    
    def query(self, input: str) -> Dict[str, Any]:
        """Mock query method that returns a complete response."""
        self.last_input = input
        self.call_count += 1
        
        if self.should_fail:
            raise Exception("Mock agent failure")
        
        return {"output": self.response}
    
    def stream_query(self, input: str):
        """Mock stream_query method that yields response chunks."""
        self.last_input = input
        self.call_count += 1
        
        if self.should_fail:
            raise Exception("Mock agent failure")
        
        # Yield response in chunks
        words = self.response.split()
        for word in words:
            yield {"output": word + " "}


class MockAgentNoStream:
    """Mock agent without stream_query support."""
    
    def __init__(self, response: str = "Test response"):
        self.response = response
        self.last_input = None
    
    def query(self, input: str) -> Dict[str, Any]:
        """Mock query method."""
        self.last_input = input
        return {"output": self.response}





# Tests for invoke_agent

@patch('app.event_planning.agent_invoker.invoke_agent_streaming')
def test_invoke_agent_success(mock_streaming):
    """Test successful agent invocation."""
    # Mock streaming to return text items
    mock_streaming.return_value = iter([
        {'type': 'text', 'content': 'Test '},
        {'type': 'text', 'content': 'response'}
    ])
    
    mock_agent = Mock()
    
    response = invoke_agent(mock_agent, "Hello", session_id="test_session")
    
    assert response == "Test response"
    mock_streaming.assert_called_once()


@patch('app.event_planning.agent_invoker.invoke_agent_streaming')
def test_invoke_agent_new_session(mock_streaming):
    """Test agent invocation with new session."""
    mock_streaming.return_value = iter([
        {'type': 'text', 'content': 'First response'}
    ])
    
    mock_agent = Mock()
    response = invoke_agent(mock_agent, "First message", session_id="new_session")
    
    assert response == "First response"


@patch('app.event_planning.agent_invoker.invoke_agent_streaming')
def test_invoke_agent_filters_tool_calls(mock_streaming):
    """Test that tool calls are filtered out from final response."""
    mock_streaming.return_value = iter([
        {'type': 'tool_call', 'name': 'test_tool'},
        {'type': 'text', 'content': 'Response '},
        {'type': 'tool_call', 'name': 'another_tool'},
        {'type': 'text', 'content': 'text'}
    ])
    
    mock_agent = Mock()
    response = invoke_agent(mock_agent, "Test", session_id="test_session")
    
    # Should only include text, not tool calls
    assert response == "Response text"


@patch('app.event_planning.agent_invoker.invoke_agent_streaming')
def test_invoke_agent_raises_on_failure(mock_streaming):
    """Test that AgentInvocationError is raised on failure."""
    mock_streaming.side_effect = AgentInvocationError("Mock agent failure")
    
    mock_agent = Mock()
    
    with pytest.raises(AgentInvocationError) as exc_info:
        invoke_agent(mock_agent, "Test", session_id="test_session")
    
    assert "Mock agent failure" in str(exc_info.value)


@patch('app.event_planning.agent_invoker.invoke_agent_streaming')
def test_invoke_agent_logs_invocation(mock_streaming, caplog):
    """Test that invocations are logged."""
    mock_streaming.return_value = iter([
        {'type': 'text', 'content': 'Test'}
    ])
    
    with caplog.at_level(logging.INFO):
        mock_agent = Mock()
        invoke_agent(mock_agent, "Test message", session_id="test_session")
        
        assert "Invoking agent for message" in caplog.text
        assert "Agent invocation completed successfully" in caplog.text


@patch('app.event_planning.agent_invoker.invoke_agent_streaming')
def test_invoke_agent_logs_errors(mock_streaming, caplog):
    """Test that errors are logged."""
    mock_streaming.side_effect = Exception("Test error")
    
    with caplog.at_level(logging.ERROR):
        mock_agent = Mock()
        
        with pytest.raises(AgentInvocationError):
            invoke_agent(mock_agent, "Test", session_id="test_session")
        
        assert "Agent invocation failed" in caplog.text


# Tests for invoke_agent_streaming

@patch('app.event_planning.agent_invoker.Runner')
@patch('app.event_planning.agent_invoker._session_service')
def test_invoke_agent_streaming_success(mock_session_service, mock_runner_class):
    """Test successful streaming invocation."""
    # Mock session
    mock_session = Mock()
    mock_session.id = "test_session"
    mock_session_service.get_session_sync.return_value = mock_session
    
    # Mock events with text content
    mock_event1 = Mock()
    mock_event1.content = Mock()
    mock_part1 = Mock()
    mock_part1.text = "Hello "
    mock_event1.content.parts = [mock_part1]
    mock_event1.function_calls = None
    
    mock_event2 = Mock()
    mock_event2.content = Mock()
    mock_part2 = Mock()
    mock_part2.text = "world"
    mock_event2.content.parts = [mock_part2]
    mock_event2.function_calls = None
    
    # Mock runner
    mock_runner = Mock()
    mock_runner.run.return_value = iter([mock_event1, mock_event2])
    mock_runner_class.return_value = mock_runner
    
    mock_agent = Mock()
    
    items = list(invoke_agent_streaming(mock_agent, "Test", session_id="test_session"))
    
    # Verify items were yielded
    assert len(items) == 2
    assert items[0] == {'type': 'text', 'content': 'Hello '}
    assert items[1] == {'type': 'text', 'content': 'world'}


@patch('app.event_planning.agent_invoker.Runner')
@patch('app.event_planning.agent_invoker._session_service')
def test_invoke_agent_streaming_with_tool_calls(mock_session_service, mock_runner_class):
    """Test streaming with tool call tracking."""
    # Mock session
    mock_session = Mock()
    mock_session.id = "test_session"
    mock_session_service.get_session_sync.return_value = mock_session
    
    # Mock event with tool call
    mock_event1 = Mock()
    mock_func_call = Mock()
    mock_func_call.name = "test_tool"
    mock_func_call.args = {"arg1": "value1"}
    mock_event1.function_calls = [mock_func_call]
    mock_event1.content = None
    
    # Mock event with text
    mock_event2 = Mock()
    mock_event2.content = Mock()
    mock_part = Mock()
    mock_part.text = "Result"
    mock_event2.content.parts = [mock_part]
    mock_event2.function_calls = None
    
    # Mock runner
    mock_runner = Mock()
    mock_runner.run.return_value = iter([mock_event1, mock_event2])
    mock_runner_class.return_value = mock_runner
    
    mock_agent = Mock()
    
    items = list(invoke_agent_streaming(mock_agent, "Test", session_id="test_session", yield_tool_calls=True))
    
    # Should yield both tool call and text
    assert len(items) == 2
    assert items[0]['type'] == 'tool_call'
    assert items[0]['name'] == 'test_tool'
    assert items[1]['type'] == 'text'
    assert items[1]['content'] == 'Result'


@patch('app.event_planning.agent_invoker.Runner')
@patch('app.event_planning.agent_invoker._session_service')
def test_invoke_agent_streaming_creates_session_if_not_exists(mock_session_service, mock_runner_class):
    """Test that a new session is created if it doesn't exist."""
    # Mock session creation
    mock_session_service.get_session_sync.side_effect = Exception("Session not found")
    mock_new_session = Mock()
    mock_new_session.id = "new_session"
    mock_session_service.create_session_sync.return_value = mock_new_session
    
    # Mock runner with empty events
    mock_runner = Mock()
    mock_runner.run.return_value = iter([])
    mock_runner_class.return_value = mock_runner
    
    mock_agent = Mock()
    
    list(invoke_agent_streaming(mock_agent, "Test", session_id="test_session"))
    
    # Verify session was created
    mock_session_service.create_session_sync.assert_called_once()


@patch('app.event_planning.agent_invoker.Runner')
@patch('app.event_planning.agent_invoker._session_service')
def test_invoke_agent_streaming_raises_on_failure(mock_session_service, mock_runner_class):
    """Test that AgentInvocationError is raised on streaming failure."""
    mock_session = Mock()
    mock_session.id = "test_session"
    mock_session_service.get_session_sync.return_value = mock_session
    
    # Mock runner to raise exception
    mock_runner = Mock()
    mock_runner.run.side_effect = Exception("Mock failure")
    mock_runner_class.return_value = mock_runner
    
    mock_agent = Mock()
    
    with pytest.raises(AgentInvocationError) as exc_info:
        list(invoke_agent_streaming(mock_agent, "Test", session_id="test_session"))
    
    assert "Agent invocation failed" in str(exc_info.value)


@patch('app.event_planning.agent_invoker.Runner')
@patch('app.event_planning.agent_invoker._session_service')
def test_invoke_agent_streaming_logs_invocation(mock_session_service, mock_runner_class, caplog):
    """Test that streaming invocations are logged."""
    mock_session = Mock()
    mock_session.id = "test_session"
    mock_session_service.get_session_sync.return_value = mock_session
    
    mock_runner = Mock()
    mock_runner.run.return_value = iter([])
    mock_runner_class.return_value = mock_runner
    
    with caplog.at_level(logging.INFO):
        mock_agent = Mock()
        list(invoke_agent_streaming(mock_agent, "Test message", session_id="test_session"))
        
        assert "Invoking agent with streaming" in caplog.text
        assert "Agent invocation completed successfully" in caplog.text


# Integration-style tests

@patch('app.event_planning.agent_invoker.invoke_agent_streaming')
def test_invoke_agent_with_session(mock_streaming):
    """Test agent invocation with session ID."""
    mock_streaming.return_value = iter([
        {'type': 'text', 'content': 'Complex response'}
    ])
    
    mock_agent = Mock()
    
    response = invoke_agent(mock_agent, "Message 4", session_id="complex_session")
    
    assert response == "Complex response"
    mock_streaming.assert_called_once()


@patch('app.event_planning.agent_invoker.invoke_agent_streaming')
def test_streaming_and_non_streaming_consistency(mock_streaming):
    """Test that streaming and non-streaming produce same result."""
    # Mock streaming to return consistent response
    mock_streaming.return_value = iter([
        {'type': 'text', 'content': 'Consistent '},
        {'type': 'text', 'content': 'test '},
        {'type': 'text', 'content': 'response'}
    ])
    
    mock_agent = Mock()
    
    # Non-streaming (uses streaming internally)
    complete_response = invoke_agent(mock_agent, "Test", session_id="test_session")
    
    # Should contain the complete content
    assert complete_response == "Consistent test response"


@patch('app.event_planning.agent_invoker.invoke_agent_streaming')
def test_error_handling_preserves_context(mock_streaming):
    """Test that error messages include context information."""
    mock_streaming.side_effect = ValueError("Specific error message")
    
    mock_agent = Mock()
    
    with pytest.raises(AgentInvocationError) as exc_info:
        invoke_agent(mock_agent, "Test message", session_id="test_session")
    
    error_str = str(exc_info.value)
    assert "Agent invocation failed" in error_str
    assert "ValueError" in error_str
    assert "Specific error message" in error_str



# Tests for context injection functionality

@patch('app.event_planning.agent_invoker.Runner')
@patch('app.event_planning.agent_invoker._session_service')
@patch('app.event_planning.context_manager.get_context')
def test_context_injection_flow(mock_get_context, mock_session_service, mock_runner_class):
    """Test that context is properly injected into messages."""
    # Mock session
    mock_session = Mock()
    mock_session.id = "test_session"
    mock_session_service.get_session_sync.return_value = mock_session
    
    # Mock context with data
    mock_context = Mock()
    mock_context.location = "Philadelphia"
    mock_context.search_query = "italian"
    mock_context.recent_venues = []
    mock_context.get_context_string.return_value = "User is looking for: italian | Location: Philadelphia"
    mock_context.update_from_user_message = Mock()
    mock_context.update_from_agent_message = Mock()
    mock_get_context.return_value = mock_context
    
    # Track the message sent to runner
    message_sent = []
    
    def capture_run(**kwargs):
        new_message = kwargs.get('new_message')
        if new_message:
            message_sent.append(new_message.parts[0].text)
        
        # Return empty events
        return iter([])
    
    # Mock runner
    mock_runner = Mock()
    mock_runner.run = capture_run
    mock_runner_class.return_value = mock_runner
    
    mock_agent = Mock()
    
    # Invoke agent
    list(invoke_agent_streaming(mock_agent, "Show me restaurants", session_id="test_session"))
    
    # Verify context was injected
    assert len(message_sent) == 1
    assert message_sent[0].startswith("[CONTEXT: ")
    assert "italian" in message_sent[0]
    assert "Philadelphia" in message_sent[0]
    assert "Show me restaurants" in message_sent[0]
    
    # Verify context methods were called
    mock_context.update_from_user_message.assert_called_once_with("Show me restaurants")
    mock_context.get_context_string.assert_called_once()


@patch('app.event_planning.agent_invoker.Runner')
@patch('app.event_planning.agent_invoker._session_service')
@patch('app.event_planning.context_manager.get_context')
def test_context_extraction_from_agent_response(mock_get_context, mock_session_service, mock_runner_class):
    """Test that entities are extracted from agent responses."""
    # Mock session
    mock_session = Mock()
    mock_session.id = "test_session"
    mock_session_service.get_session_sync.return_value = mock_session
    
    # Mock context
    mock_context = Mock()
    mock_context.recent_venues = []
    mock_context.get_context_string.return_value = ""
    mock_context.update_from_user_message = Mock()
    mock_context.update_from_agent_message = Mock()
    mock_get_context.return_value = mock_context
    
    # Mock event with venue information
    mock_event = Mock()
    mock_event.content = Mock()
    mock_part = Mock()
    mock_part.text = "I found **Test Restaurant**. Place ID: ChIJtest123"
    mock_event.content.parts = [mock_part]
    mock_event.function_calls = None
    
    # Mock runner
    mock_runner = Mock()
    mock_runner.run.return_value = iter([mock_event])
    mock_runner_class.return_value = mock_runner
    
    mock_agent = Mock()
    
    # Invoke agent
    list(invoke_agent_streaming(mock_agent, "Find restaurants", session_id="test_session"))
    
    # Verify entity extraction was called with agent response
    mock_context.update_from_agent_message.assert_called_once()
    call_args = mock_context.update_from_agent_message.call_args[0]
    assert "Test Restaurant" in call_args[0]
    assert "ChIJtest123" in call_args[0]


@patch('app.event_planning.agent_invoker.Runner')
@patch('app.event_planning.agent_invoker._session_service')
@patch('app.event_planning.context_manager.get_context')
def test_error_handling_in_context_extraction(mock_get_context, mock_session_service, mock_runner_class, caplog):
    """Test that context extraction errors are handled gracefully."""
    # Mock session
    mock_session = Mock()
    mock_session.id = "test_session"
    mock_session_service.get_session_sync.return_value = mock_session
    
    # Mock context that raises error on update
    mock_context = Mock()
    mock_context.update_from_user_message.side_effect = Exception("Context extraction failed")
    mock_get_context.return_value = mock_context
    
    # Mock runner
    mock_runner = Mock()
    mock_runner.run.return_value = iter([])
    mock_runner_class.return_value = mock_runner
    
    mock_agent = Mock()
    
    with caplog.at_level(logging.ERROR):
        # Should not raise, should continue with original message
        list(invoke_agent_streaming(mock_agent, "Test message", session_id="test_session"))
        
        # Verify error was logged
        assert "Context extraction/injection failed" in caplog.text


@patch('app.event_planning.agent_invoker.Runner')
@patch('app.event_planning.agent_invoker._session_service')
@patch('app.event_planning.context_manager.get_context')
def test_error_handling_in_entity_extraction(mock_get_context, mock_session_service, mock_runner_class, caplog):
    """Test that entity extraction errors are handled gracefully."""
    # Mock session
    mock_session = Mock()
    mock_session.id = "test_session"
    mock_session_service.get_session_sync.return_value = mock_session
    
    # Mock context that raises error on agent message update
    mock_context = Mock()
    mock_context.recent_venues = []
    mock_context.get_context_string.return_value = ""
    mock_context.update_from_user_message = Mock()
    mock_context.update_from_agent_message.side_effect = Exception("Entity extraction failed")
    mock_get_context.return_value = mock_context
    
    # Mock event
    mock_event = Mock()
    mock_event.content = Mock()
    mock_part = Mock()
    mock_part.text = "Response"
    mock_event.content.parts = [mock_part]
    mock_event.function_calls = None
    
    # Mock runner
    mock_runner = Mock()
    mock_runner.run.return_value = iter([mock_event])
    mock_runner_class.return_value = mock_runner
    
    mock_agent = Mock()
    
    with caplog.at_level(logging.ERROR):
        # Should not raise, should continue normally
        list(invoke_agent_streaming(mock_agent, "Test", session_id="test_session"))
        
        # Verify error was logged
        assert "Entity extraction from agent response failed" in caplog.text


@patch('app.event_planning.agent_invoker.Runner')
@patch('app.event_planning.agent_invoker._session_service')
@patch('app.event_planning.context_manager.get_context')
def test_no_context_injection_when_empty(mock_get_context, mock_session_service, mock_runner_class):
    """Test that no context is injected when context is empty."""
    # Mock session
    mock_session = Mock()
    mock_session.id = "test_session"
    mock_session_service.get_session_sync.return_value = mock_session
    
    # Mock context with no data
    mock_context = Mock()
    mock_context.get_context_string.return_value = ""  # Empty context
    mock_context.update_from_user_message = Mock()
    mock_context.update_from_agent_message = Mock()
    mock_get_context.return_value = mock_context
    
    # Track the message sent to runner
    message_sent = []
    
    def capture_run(**kwargs):
        new_message = kwargs.get('new_message')
        if new_message:
            message_sent.append(new_message.parts[0].text)
        return iter([])
    
    # Mock runner
    mock_runner = Mock()
    mock_runner.run = capture_run
    mock_runner_class.return_value = mock_runner
    
    mock_agent = Mock()
    
    # Invoke agent
    list(invoke_agent_streaming(mock_agent, "Test message", session_id="test_session"))
    
    # Verify message was not modified (no context prefix)
    assert len(message_sent) == 1
    assert message_sent[0] == "Test message"
    assert not message_sent[0].startswith("[CONTEXT: ")
