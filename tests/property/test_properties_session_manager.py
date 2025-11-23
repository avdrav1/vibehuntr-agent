"""Property-based tests for session manager operations.

This module tests the correctness properties for session management,
including message persistence, agent caching, and history pagination.
"""

import sys
import os
from hypothesis import given, strategies as st, settings
from hypothesis.strategies import composite
import pytest

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.event_planning.session_manager import SessionManager


# Custom strategies for generating test data

@composite
def message_strategy(draw: st.DrawFn) -> dict:
    """Generate a valid message dictionary."""
    role = draw(st.sampled_from(["user", "assistant"]))
    content = draw(st.text(min_size=1, max_size=500))
    return {"role": role, "content": content}


@composite
def message_list_strategy(draw: st.DrawFn, min_size: int = 0, max_size: int = 50) -> list:
    """Generate a list of valid messages."""
    return draw(st.lists(message_strategy(), min_size=min_size, max_size=max_size))


# Mock session state for testing
class MockSessionState(dict):
    """Mock Streamlit session state for testing."""
    pass


# Property Tests

# Feature: adk-playground-integration, Property 1: Message persistence in session
@given(message_strategy())
@settings(max_examples=100)
def test_property_1_message_persistence_in_session(message: dict) -> None:
    """
    Feature: adk-playground-integration, Property 1: Message persistence in session
    
    For any user message sent during a session, that message should appear in the
    session's chat history after submission.
    
    Validates: Requirements 3.1
    """
    # Create a fresh session manager with mock session state
    mock_state = MockSessionState()
    session_manager = SessionManager(session_state=mock_state)
    
    # Add the message
    session_manager.add_message(message["role"], message["content"])
    
    # Retrieve messages
    messages = session_manager.get_messages()
    
    # Verify the message appears in history
    assert len(messages) == 1
    assert messages[0]["role"] == message["role"]
    assert messages[0]["content"] == message["content"]


# Feature: adk-playground-integration, Property 2: Agent response persistence
@given(st.text(min_size=1, max_size=500))
@settings(max_examples=100)
def test_property_2_agent_response_persistence(response_content: str) -> None:
    """
    Feature: adk-playground-integration, Property 2: Agent response persistence
    
    For any agent response generated, that response should be appended to the
    session's chat history after completion.
    
    Validates: Requirements 3.2
    """
    # Create a fresh session manager with mock session state
    mock_state = MockSessionState()
    session_manager = SessionManager(session_state=mock_state)
    
    # Add a user message first
    session_manager.add_message("user", "Test question")
    
    # Add agent response
    session_manager.add_message("assistant", response_content)
    
    # Retrieve messages
    messages = session_manager.get_messages()
    
    # Verify both messages are in history
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == response_content


# Feature: adk-playground-integration, Property 4: Fresh session on refresh
@given(message_list_strategy(min_size=1, max_size=20))
@settings(max_examples=100)
def test_property_4_fresh_session_on_refresh(messages: list) -> None:
    """
    Feature: adk-playground-integration, Property 4: Fresh session on refresh
    
    For any page refresh, the system should initialize a new session with empty
    chat history.
    
    Validates: Requirements 3.4
    """
    # Simulate first session with messages
    mock_state_1 = MockSessionState()
    session_manager_1 = SessionManager(session_state=mock_state_1)
    
    # Add messages to first session
    for msg in messages:
        session_manager_1.add_message(msg["role"], msg["content"])
    
    # Verify messages exist in first session
    assert len(session_manager_1.get_messages()) == len(messages)
    
    # Simulate page refresh by creating new session with fresh state
    mock_state_2 = MockSessionState()
    session_manager_2 = SessionManager(session_state=mock_state_2)
    
    # Verify new session has empty history
    assert len(session_manager_2.get_messages()) == 0


# Feature: adk-playground-integration, Property 11: Recent messages display limit
@given(message_list_strategy(min_size=15, max_size=50))
@settings(max_examples=100)
def test_property_11_recent_messages_display_limit(messages: list) -> None:
    """
    Feature: adk-playground-integration, Property 11: Recent messages display limit
    
    For any conversation with more than 10 messages, the default view should display
    only the 10 most recent messages.
    
    Validates: Requirements 1.1
    """
    # Create a session manager with mock session state
    mock_state = MockSessionState()
    session_manager = SessionManager(session_state=mock_state)
    
    # Add all messages
    for msg in messages:
        session_manager.add_message(msg["role"], msg["content"])
    
    # Get recent messages only (default 10)
    recent_messages = session_manager.get_messages(recent_only=True, recent_count=10)
    
    # Verify only 10 messages are returned
    assert len(recent_messages) == 10
    
    # Verify they are the most recent 10 (last 10 from the list)
    all_messages = session_manager.get_all_messages()
    expected_recent = all_messages[-10:]
    
    assert recent_messages == expected_recent


# Feature: adk-playground-integration, Property 12: Complete history availability
@given(message_list_strategy(min_size=15, max_size=50))
@settings(max_examples=100)
def test_property_12_complete_history_availability(messages: list) -> None:
    """
    Feature: adk-playground-integration, Property 12: Complete history availability
    
    For any conversation with more than 10 messages, all older messages should be
    accessible through the "Show Older Messages" section.
    
    Validates: Requirements 3.5
    """
    # Create a session manager with mock session state
    mock_state = MockSessionState()
    session_manager = SessionManager(session_state=mock_state)
    
    # Add all messages
    for msg in messages:
        session_manager.add_message(msg["role"], msg["content"])
    
    # Get all messages
    all_messages = session_manager.get_all_messages()
    
    # Verify all messages are accessible
    assert len(all_messages) == len(messages)
    
    # Verify messages are in chronological order
    for i, msg in enumerate(messages):
        assert all_messages[i]["role"] == msg["role"]
        assert all_messages[i]["content"] == msg["content"]
    
    # Verify should_show_history_button returns True when > 10 messages
    assert session_manager.should_show_history_button(recent_count=10) == True
    
    # Verify get_older_messages returns correct older messages
    older_messages = session_manager.get_older_messages(recent_count=10)
    expected_older = all_messages[:-10]
    
    assert older_messages == expected_older


# Additional property test: Message order preservation
@given(message_list_strategy(min_size=2, max_size=30))
@settings(max_examples=100)
def test_property_message_order_preservation(messages: list) -> None:
    """
    For any sequence of messages added to a session, they should be retrievable
    in the same chronological order they were added.
    
    Validates: Requirements 3.5 (chronological order)
    """
    # Create a session manager with mock session state
    mock_state = MockSessionState()
    session_manager = SessionManager(session_state=mock_state)
    
    # Add messages in order
    for msg in messages:
        session_manager.add_message(msg["role"], msg["content"])
    
    # Retrieve all messages
    retrieved_messages = session_manager.get_all_messages()
    
    # Verify order is preserved
    assert len(retrieved_messages) == len(messages)
    for i, msg in enumerate(messages):
        assert retrieved_messages[i]["role"] == msg["role"]
        assert retrieved_messages[i]["content"] == msg["content"]


# Additional property test: Clear messages completeness
@given(message_list_strategy(min_size=1, max_size=30))
@settings(max_examples=100)
def test_property_clear_messages_completeness(messages: list) -> None:
    """
    For any session with messages, clearing the messages should result in an
    empty message list.
    
    Validates: Requirements 8.2
    """
    # Create a session manager with mock session state
    mock_state = MockSessionState()
    session_manager = SessionManager(session_state=mock_state)
    
    # Add messages
    for msg in messages:
        session_manager.add_message(msg["role"], msg["content"])
    
    # Verify messages exist
    assert len(session_manager.get_messages()) == len(messages)
    
    # Clear messages
    session_manager.clear_messages()
    
    # Verify all messages are removed
    assert len(session_manager.get_messages()) == 0
    assert len(session_manager.get_all_messages()) == 0


# Additional property test: Agent caching
def test_property_agent_caching() -> None:
    """
    For any session, setting an agent should cache it and make it retrievable
    from the session state.
    
    Validates: Agent caching functionality
    """
    # Create a session manager with mock session state
    mock_state = MockSessionState()
    session_manager = SessionManager(session_state=mock_state)
    
    # Initially, no agent should be cached
    assert session_manager.get_agent() is None
    
    # Create a mock agent (just use a simple object for testing)
    class MockAgent:
        def __init__(self, name: str):
            self.name = name
    
    mock_agent = MockAgent("test_agent")
    
    # Cache the agent
    session_manager.set_agent(mock_agent)
    
    # Verify agent is retrievable
    cached_agent = session_manager.get_agent()
    assert cached_agent is not None
    assert cached_agent.name == "test_agent"
    assert cached_agent is mock_agent  # Same instance
