"""Unit tests for error scenarios across the system.

This module tests various error scenarios including agent loading errors,
agent invocation errors, streaming errors, and session state errors.
Tests verify that error messages are user-friendly and the system handles
errors gracefully.
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from typing import Generator

from app.event_planning.agent_loader import get_agent, clear_agent_cache
from app.event_planning.agent_invoker import (
    invoke_agent_streaming,
    invoke_agent,
    AgentInvocationError
)
from app.event_planning.session_manager import SessionManager


# Test Agent Loading Errors

def test_agent_loading_error_full_agent_missing():
    """
    Test agent loading error when full agent module is missing.
    
    Validates: Requirements 7.1, 7.2, 7.3, 7.4
    """
    # Clear cache to force reload
    clear_agent_cache()
    
    # Mock environment to use full agent
    with patch.dict('os.environ', {'USE_DOCUMENT_RETRIEVAL': 'true'}):
        # Mock the import to fail
        with patch('builtins.__import__', side_effect=ImportError("Module not found")):
            # The agent loader wraps ImportError in RuntimeError
            with pytest.raises((ImportError, RuntimeError)) as exc_info:
                get_agent()
            
            # Verify error message is informative
            error_msg = str(exc_info.value)
            assert "Failed to import" in error_msg or "Module not found" in error_msg or "Unexpected error" in error_msg


def test_agent_loading_error_simple_agent_missing():
    """
    Test agent loading error when simple agent module is missing.
    
    Validates: Requirements 7.1, 7.2, 7.3, 7.4
    """
    # Clear cache to force reload
    clear_agent_cache()
    
    # Mock environment to use simple agent
    with patch.dict('os.environ', {'USE_DOCUMENT_RETRIEVAL': 'false'}):
        # Mock the import to fail for simple agent
        with patch('builtins.__import__', side_effect=ImportError("Simple agent not found")):
            with pytest.raises((ImportError, RuntimeError)) as exc_info:
                get_agent()
            
            # Verify error is raised (system doesn't crash silently)
            assert exc_info.value is not None


def test_agent_loading_logs_errors(caplog):
    """
    Test that agent loading errors are logged with context.
    
    Validates: Requirements 7.1, 7.5
    """
    clear_agent_cache()
    
    with caplog.at_level(logging.ERROR):
        with patch.dict('os.environ', {'USE_DOCUMENT_RETRIEVAL': 'true'}):
            # Mock import to fail
            with patch('builtins.__import__', side_effect=ImportError("Test import error")):
                try:
                    get_agent()
                except (ImportError, RuntimeError):
                    pass  # Expected
        
        # Verify error was logged
        assert "Failed to import" in caplog.text or "error" in caplog.text.lower()


# Test Agent Invocation Errors

def test_agent_invocation_error_api_failure():
    """
    Test agent invocation error when API call fails.
    
    Validates: Requirements 7.1, 7.2, 7.4
    """
    mock_agent = Mock()
    
    # Mock the session service and runner
    with patch('app.event_planning.agent_invoker._session_service') as mock_session_service:
        with patch('app.event_planning.agent_invoker.Runner') as mock_runner_class:
            # Setup mock session
            mock_session = Mock()
            mock_session.id = "test_session"
            mock_session_service.get_session_sync.return_value = mock_session
            
            # Setup mock runner to raise API error
            mock_runner = Mock()
            mock_runner.run.side_effect = Exception("API rate limit exceeded")
            mock_runner_class.return_value = mock_runner
            
            # Attempt invocation
            with pytest.raises(AgentInvocationError) as exc_info:
                list(invoke_agent_streaming(mock_agent, "Test message", []))
            
            # Verify error is wrapped properly
            assert "Agent invocation failed" in str(exc_info.value)
            assert "API rate limit exceeded" in str(exc_info.value)


def test_agent_invocation_error_timeout():
    """
    Test agent invocation error when request times out.
    
    Validates: Requirements 7.1, 7.2, 7.4
    """
    mock_agent = Mock()
    
    # Mock the session service and runner
    with patch('app.event_planning.agent_invoker._session_service') as mock_session_service:
        with patch('app.event_planning.agent_invoker.Runner') as mock_runner_class:
            # Setup mock session
            mock_session = Mock()
            mock_session.id = "test_session"
            mock_session_service.get_session_sync.return_value = mock_session
            
            # Setup mock runner to raise timeout error
            mock_runner = Mock()
            mock_runner.run.side_effect = TimeoutError("Request timed out after 30s")
            mock_runner_class.return_value = mock_runner
            
            # Attempt invocation
            with pytest.raises(AgentInvocationError) as exc_info:
                list(invoke_agent_streaming(mock_agent, "Test message", []))
            
            # Verify error is wrapped
            assert "Agent invocation failed" in str(exc_info.value)


def test_agent_invocation_error_tool_execution_failure():
    """
    Test agent invocation error when tool execution fails.
    
    Validates: Requirements 7.2, 7.4
    """
    mock_agent = Mock()
    
    # Mock the session service and runner
    with patch('app.event_planning.agent_invoker._session_service') as mock_session_service:
        with patch('app.event_planning.agent_invoker.Runner') as mock_runner_class:
            # Setup mock session
            mock_session = Mock()
            mock_session.id = "test_session"
            mock_session_service.get_session_sync.return_value = mock_session
            
            # Setup mock runner to raise tool error
            mock_runner = Mock()
            mock_runner.run.side_effect = Exception("Tool 'search_venues' failed: Invalid API key")
            mock_runner_class.return_value = mock_runner
            
            # Attempt invocation
            with pytest.raises(AgentInvocationError) as exc_info:
                list(invoke_agent_streaming(mock_agent, "Find venues", []))
            
            # Verify error includes tool context
            error_str = str(exc_info.value)
            assert "Agent invocation failed" in error_str


def test_agent_invocation_error_logs_with_context(caplog):
    """
    Test that agent invocation errors are logged with full context.
    
    Validates: Requirements 7.1, 7.5
    """
    mock_agent = Mock()
    
    with caplog.at_level(logging.ERROR):
        # Mock the session service and runner
        with patch('app.event_planning.agent_invoker._session_service') as mock_session_service:
            with patch('app.event_planning.agent_invoker.Runner') as mock_runner_class:
                # Setup mock session
                mock_session = Mock()
                mock_session.id = "test_session"
                mock_session_service.get_session_sync.return_value = mock_session
                
                # Setup mock runner to fail
                mock_runner = Mock()
                mock_runner.run.side_effect = Exception("Test error")
                mock_runner_class.return_value = mock_runner
                
                # Attempt invocation
                try:
                    list(invoke_agent_streaming(mock_agent, "Test message", []))
                except AgentInvocationError:
                    pass  # Expected
        
        # Verify error was logged with context
        assert "Agent invocation failed" in caplog.text
        assert "ERROR" in caplog.text


# Test Streaming Errors

def test_streaming_error_connection_interruption():
    """
    Test streaming error when connection is interrupted mid-stream.
    
    Validates: Requirements 7.1, 7.4
    """
    mock_agent = Mock()
    
    # Mock the session service and runner
    with patch('app.event_planning.agent_invoker._session_service') as mock_session_service:
        with patch('app.event_planning.agent_invoker.Runner') as mock_runner_class:
            # Setup mock session
            mock_session = Mock()
            mock_session.id = "test_session"
            mock_session_service.get_session_sync.return_value = mock_session
            
            # Create a generator that fails mid-stream
            def failing_generator():
                class MockEvent:
                    def __init__(self, text):
                        self.content = Mock()
                        self.content.parts = [Mock(text=text)]
                
                yield MockEvent("First token")
                yield MockEvent("Second token")
                raise ConnectionError("Connection lost")
            
            # Setup mock runner
            mock_runner = Mock()
            mock_runner.run.return_value = failing_generator()
            mock_runner_class.return_value = mock_runner
            
            # Attempt streaming
            with pytest.raises(AgentInvocationError) as exc_info:
                list(invoke_agent_streaming(mock_agent, "Test", []))
            
            # Verify error is raised
            assert "Agent invocation failed" in str(exc_info.value)


def test_streaming_error_partial_response():
    """
    Test handling of partial response when streaming fails.
    
    Validates: Requirements 7.4
    """
    mock_agent = Mock()
    
    # Mock the session service and runner
    with patch('app.event_planning.agent_invoker._session_service') as mock_session_service:
        with patch('app.event_planning.agent_invoker.Runner') as mock_runner_class:
            # Setup mock session
            mock_session = Mock()
            mock_session.id = "test_session"
            mock_session_service.get_session_sync.return_value = mock_session
            
            # Create a generator that yields some tokens then fails
            def partial_generator():
                class MockEvent:
                    def __init__(self, text):
                        self.content = Mock()
                        self.content.parts = [Mock(text=text)]
                
                yield MockEvent("Partial ")
                yield MockEvent("response ")
                raise Exception("Stream interrupted")
            
            # Setup mock runner
            mock_runner = Mock()
            mock_runner.run.return_value = partial_generator()
            mock_runner_class.return_value = mock_runner
            
            # Attempt streaming - should raise error
            with pytest.raises(AgentInvocationError):
                list(invoke_agent_streaming(mock_agent, "Test", []))


# Test Session State Errors

def test_session_state_error_corrupted_messages():
    """
    Test handling of corrupted message data in session state.
    
    Validates: Requirements 7.3, 7.4
    """
    # Create session manager with corrupted state
    mock_state = {"messages": "not a list"}  # Invalid type
    session_manager = SessionManager(session_state=mock_state)
    
    # Should handle gracefully and return empty list or fix the state
    messages = session_manager.get_messages()
    
    # Verify system doesn't crash
    assert isinstance(messages, list)


def test_session_state_error_missing_keys():
    """
    Test handling of missing keys in session state.
    
    Validates: Requirements 7.3, 7.4
    """
    # Create session manager with empty state
    mock_state = {}
    session_manager = SessionManager(session_state=mock_state)
    
    # Should initialize missing keys
    messages = session_manager.get_messages()
    
    # Verify system handles missing keys gracefully
    assert isinstance(messages, list)
    assert len(messages) == 0


def test_session_state_error_invalid_message_format():
    """
    Test handling of invalid message format in session state.
    
    Validates: Requirements 7.3, 7.4
    """
    # Create session manager with invalid messages
    mock_state = {
        "messages": [
            {"role": "user", "content": "Valid"},
            "invalid message",  # Not a dict
            {"role": "assistant"},  # Missing content
            {"content": "Missing role"},  # Missing role
        ]
    }
    session_manager = SessionManager(session_state=mock_state)
    
    # Should handle gracefully
    messages = session_manager.get_messages()
    
    # Verify system doesn't crash and returns valid messages
    assert isinstance(messages, list)
    # At least the valid message should be there
    assert len(messages) >= 1


# Test Error Message User-Friendliness

def test_error_messages_are_user_friendly():
    """
    Test that error messages are user-friendly and not technical.
    
    Validates: Requirements 7.4
    """
    mock_agent = Mock()
    
    # Mock the session service and runner
    with patch('app.event_planning.agent_invoker._session_service') as mock_session_service:
        with patch('app.event_planning.agent_invoker.Runner') as mock_runner_class:
            # Setup mock session
            mock_session = Mock()
            mock_session.id = "test_session"
            mock_session_service.get_session_sync.return_value = mock_session
            
            # Setup mock runner to fail
            mock_runner = Mock()
            mock_runner.run.side_effect = Exception("Internal server error 500")
            mock_runner_class.return_value = mock_runner
            
            # Attempt invocation
            with pytest.raises(AgentInvocationError) as exc_info:
                list(invoke_agent_streaming(mock_agent, "Test", []))
            
            # Verify error message exists and contains context
            error_msg = str(exc_info.value)
            assert len(error_msg) > 0
            assert "Agent invocation failed" in error_msg


def test_error_includes_error_type():
    """
    Test that error messages include the error type for debugging.
    
    Validates: Requirements 7.5
    """
    mock_agent = Mock()
    
    # Mock the session service and runner
    with patch('app.event_planning.agent_invoker._session_service') as mock_session_service:
        with patch('app.event_planning.agent_invoker.Runner') as mock_runner_class:
            # Setup mock session
            mock_session = Mock()
            mock_session.id = "test_session"
            mock_session_service.get_session_sync.return_value = mock_session
            
            # Setup mock runner to raise specific error type
            mock_runner = Mock()
            mock_runner.run.side_effect = ValueError("Invalid parameter")
            mock_runner_class.return_value = mock_runner
            
            # Attempt invocation
            with pytest.raises(AgentInvocationError) as exc_info:
                list(invoke_agent_streaming(mock_agent, "Test", []))
            
            # Verify error type is included
            error_msg = str(exc_info.value)
            assert "ValueError" in error_msg


# Test System Doesn't Crash

def test_system_continues_after_error():
    """
    Test that the system remains functional after an error.
    
    Validates: Requirements 7.4
    """
    mock_agent = Mock()
    
    # Mock the session service and runner
    with patch('app.event_planning.agent_invoker._session_service') as mock_session_service:
        with patch('app.event_planning.agent_invoker.Runner') as mock_runner_class:
            # Setup mock session
            mock_session = Mock()
            mock_session.id = "test_session"
            mock_session_service.get_session_sync.return_value = mock_session
            
            # First call fails
            mock_runner_fail = Mock()
            mock_runner_fail.run.side_effect = Exception("First error")
            mock_runner_class.return_value = mock_runner_fail
            
            # Attempt first invocation - should fail
            with pytest.raises(AgentInvocationError):
                list(invoke_agent_streaming(mock_agent, "First", []))
            
            # Second call succeeds
            class MockEvent:
                def __init__(self, text):
                    self.content = Mock()
                    self.content.parts = [Mock(text=text)]
            
            mock_runner_success = Mock()
            mock_runner_success.run.return_value = iter([MockEvent("Success")])
            mock_runner_class.return_value = mock_runner_success
            
            # Attempt second invocation - should succeed
            tokens = list(invoke_agent_streaming(mock_agent, "Second", []))
            
            # Verify system recovered
            assert len(tokens) > 0
            # Tokens are strings extracted from mock events
            assert any("Success" in str(token) for token in tokens)


def test_multiple_errors_dont_accumulate():
    """
    Test that multiple errors don't accumulate or cause cascading failures.
    
    Validates: Requirements 7.4
    """
    mock_agent = Mock()
    
    # Mock the session service and runner
    with patch('app.event_planning.agent_invoker._session_service') as mock_session_service:
        with patch('app.event_planning.agent_invoker.Runner') as mock_runner_class:
            # Setup mock session
            mock_session = Mock()
            mock_session.id = "test_session"
            mock_session_service.get_session_sync.return_value = mock_session
            
            # Setup mock runner to always fail
            mock_runner = Mock()
            mock_runner.run.side_effect = Exception("Persistent error")
            mock_runner_class.return_value = mock_runner
            
            # Attempt multiple invocations - all should fail independently
            for i in range(3):
                with pytest.raises(AgentInvocationError) as exc_info:
                    list(invoke_agent_streaming(mock_agent, f"Message {i}", []))
                
                # Each error should be independent
                assert "Agent invocation failed" in str(exc_info.value)


# Test Error Logging with Timestamp

def test_error_logging_includes_timestamp(caplog):
    """
    Test that error logs include timestamp information.
    
    Validates: Requirements 7.5
    """
    mock_agent = Mock()
    
    with caplog.at_level(logging.ERROR):
        # Mock the session service and runner
        with patch('app.event_planning.agent_invoker._session_service') as mock_session_service:
            with patch('app.event_planning.agent_invoker.Runner') as mock_runner_class:
                # Setup mock session
                mock_session = Mock()
                mock_session.id = "test_session"
                mock_session_service.get_session_sync.return_value = mock_session
                
                # Setup mock runner to fail
                mock_runner = Mock()
                mock_runner.run.side_effect = Exception("Test error")
                mock_runner_class.return_value = mock_runner
                
                # Attempt invocation
                try:
                    list(invoke_agent_streaming(mock_agent, "Test", []))
                except AgentInvocationError:
                    pass
        
        # Verify error was logged (timestamp is added by logging framework)
        assert len(caplog.records) > 0
        # Check that log record has timestamp
        for record in caplog.records:
            if record.levelname == "ERROR":
                assert record.created > 0  # Unix timestamp
