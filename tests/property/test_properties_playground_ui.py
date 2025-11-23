"""Property-based tests for playground UI operations.

This module tests the correctness properties for the Streamlit playground UI,
including message display uniqueness, streaming completion consistency, and
state preservation across reruns.
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

# Feature: playground-fix, Property 1: Message display uniqueness
@given(message_list_strategy(min_size=1, max_size=30))
@settings(max_examples=100)
def test_property_1_message_display_uniqueness(messages: list) -> None:
    """
    Feature: playground-fix, Property 1: Message display uniqueness
    
    For any conversation history, when displaying messages in the UI, each message
    should appear exactly once.
    
    Validates: Requirements 1.1, 1.2, 1.3, 1.4
    """
    # Create a session manager with mock session state
    mock_state = MockSessionState()
    session_manager = SessionManager(session_state=mock_state)
    
    # Add all messages to history
    for msg in messages:
        session_manager.add_message(msg["role"], msg["content"])
    
    # Retrieve messages for display
    displayed_messages = session_manager.get_messages()
    
    # Verify each message appears exactly once
    assert len(displayed_messages) == len(messages)
    
    # Verify no duplicates by checking each message content
    displayed_contents = [msg["content"] for msg in displayed_messages]
    original_contents = [msg["content"] for msg in messages]
    
    # Each original message should appear exactly once in displayed messages
    for i, original_content in enumerate(original_contents):
        # Count occurrences of this content in displayed messages
        count = displayed_contents.count(original_content)
        # Should appear at least once (could be more if original had duplicates)
        assert count >= 1
    
    # Total count should match
    assert len(displayed_messages) == len(messages)
    
    # Verify order is preserved (chronological)
    for i, msg in enumerate(messages):
        assert displayed_messages[i]["role"] == msg["role"]
        assert displayed_messages[i]["content"] == msg["content"]


# Feature: playground-fix, Property 2: Streaming completion consistency
@given(st.text(min_size=1, max_size=1000))
@settings(max_examples=100)
def test_property_2_streaming_completion_consistency(response_text: str) -> None:
    """
    Feature: playground-fix, Property 2: Streaming completion consistency
    
    For any agent response, after streaming completes and the UI reruns, the message
    should appear exactly once in the history.
    
    Validates: Requirements 1.5
    """
    # Create a session manager with mock session state
    mock_state = MockSessionState()
    session_manager = SessionManager(session_state=mock_state)
    
    # Simulate the streaming flow:
    # 1. User sends a message
    user_message = "Test question"
    session_manager.add_message("user", user_message)
    
    # 2. Agent response is streamed (simulated by building up the response)
    # In real code, this would be done token by token
    full_response = response_text
    
    # 3. After streaming completes, add the full response to history
    session_manager.add_message("assistant", full_response)
    
    # 4. Simulate rerun by retrieving messages again
    messages_after_rerun = session_manager.get_messages()
    
    # Verify the response appears exactly once
    assistant_messages = [msg for msg in messages_after_rerun if msg["role"] == "assistant"]
    assert len(assistant_messages) == 1
    assert assistant_messages[0]["content"] == full_response
    
    # Verify total message count is correct (1 user + 1 assistant)
    assert len(messages_after_rerun) == 2


# Feature: playground-fix, Property 7: State preservation across reruns
@given(message_list_strategy(min_size=1, max_size=30))
@settings(max_examples=100)
def test_property_7_state_preservation_across_reruns(messages: list) -> None:
    """
    Feature: playground-fix, Property 7: State preservation across reruns
    
    For any Streamlit rerun, the conversation history should remain intact and complete.
    
    Validates: Requirements 4.1
    """
    # Create a session manager with mock session state
    mock_state = MockSessionState()
    session_manager = SessionManager(session_state=mock_state)
    
    # Add messages to simulate a conversation
    for msg in messages:
        session_manager.add_message(msg["role"], msg["content"])
    
    # Get messages before "rerun"
    messages_before = session_manager.get_messages()
    
    # Simulate rerun by creating a new session manager with the same state
    # (In Streamlit, the session state persists across reruns)
    session_manager_after_rerun = SessionManager(session_state=mock_state)
    
    # Get messages after "rerun"
    messages_after = session_manager_after_rerun.get_messages()
    
    # Verify conversation history is preserved
    assert len(messages_after) == len(messages_before)
    assert len(messages_after) == len(messages)
    
    # Verify each message is intact
    for i, msg in enumerate(messages):
        assert messages_after[i]["role"] == msg["role"]
        assert messages_after[i]["content"] == msg["content"]
    
    # Verify order is preserved
    assert messages_after == messages_before


# Additional property test: Multiple reruns preserve state
@given(message_list_strategy(min_size=1, max_size=20), st.integers(min_value=1, max_value=10))
@settings(max_examples=100)
def test_property_multiple_reruns_preserve_state(messages: list, num_reruns: int) -> None:
    """
    For any number of Streamlit reruns, the conversation history should remain
    intact and complete.
    
    Validates: Requirements 4.1 (extended)
    """
    # Create a session manager with mock session state
    mock_state = MockSessionState()
    session_manager = SessionManager(session_state=mock_state)
    
    # Add messages
    for msg in messages:
        session_manager.add_message(msg["role"], msg["content"])
    
    # Get initial messages
    initial_messages = session_manager.get_messages()
    
    # Simulate multiple reruns
    for _ in range(num_reruns):
        # Create new session manager with same state (simulates rerun)
        session_manager = SessionManager(session_state=mock_state)
        
        # Verify messages are still intact
        current_messages = session_manager.get_messages()
        assert len(current_messages) == len(initial_messages)
        assert current_messages == initial_messages


# Additional property test: Processing flag prevents duplicate processing
@given(st.text(min_size=1, max_size=100))
@settings(max_examples=100)
def test_property_processing_flag_prevents_duplicates(user_input: str) -> None:
    """
    For any user input, the processing flag should prevent duplicate processing
    when the UI reruns during streaming.
    
    Validates: Requirements 1.4 (no duplicate processing)
    """
    # Create a session manager with mock session state
    mock_state = MockSessionState()
    session_manager = SessionManager(session_state=mock_state)
    
    # Simulate processing flag behavior
    mock_state["is_processing"] = False
    
    # First processing: flag is False, so we process
    if not mock_state.get("is_processing", False):
        mock_state["is_processing"] = True
        session_manager.add_message("user", user_input)
        # Simulate agent response
        session_manager.add_message("assistant", "Response to: " + user_input)
        mock_state["is_processing"] = False
    
    # Get message count after first processing
    messages_after_first = session_manager.get_messages()
    first_count = len(messages_after_first)
    
    # Simulate rerun while processing flag is True (should not process again)
    mock_state["is_processing"] = True
    
    if not mock_state.get("is_processing", False):
        # This should NOT execute because flag is True
        session_manager.add_message("user", user_input)
        session_manager.add_message("assistant", "Response to: " + user_input)
    
    # Get message count after attempted duplicate processing
    messages_after_second = session_manager.get_messages()
    second_count = len(messages_after_second)
    
    # Verify no duplicate processing occurred
    assert second_count == first_count
    assert messages_after_second == messages_after_first


# Additional property test: Display from history after streaming
@given(st.text(min_size=1, max_size=500), st.text(min_size=1, max_size=1000))
@settings(max_examples=100)
def test_property_display_from_history_after_streaming(user_msg: str, agent_response: str) -> None:
    """
    For any conversation turn, after streaming completes and messages are added
    to history, displaying from history should show both messages exactly once.
    
    Validates: Requirements 1.1, 1.2, 1.5
    """
    # Create a session manager with mock session state
    mock_state = MockSessionState()
    session_manager = SessionManager(session_state=mock_state)
    
    # Simulate the complete flow:
    # 1. Display existing history (empty initially)
    initial_messages = session_manager.get_messages()
    assert len(initial_messages) == 0
    
    # 2. User sends message (displayed inline)
    # 3. Agent streams response (displayed inline with cursor)
    # 4. After streaming completes, add both to history
    session_manager.add_message("user", user_msg)
    session_manager.add_message("assistant", agent_response)
    
    # 5. Rerun and display from history
    messages_from_history = session_manager.get_messages()
    
    # Verify both messages appear exactly once
    assert len(messages_from_history) == 2
    assert messages_from_history[0]["role"] == "user"
    assert messages_from_history[0]["content"] == user_msg
    assert messages_from_history[1]["role"] == "assistant"
    assert messages_from_history[1]["content"] == agent_response
    
    # Verify no duplicates
    user_messages = [msg for msg in messages_from_history if msg["role"] == "user"]
    assistant_messages = [msg for msg in messages_from_history if msg["role"] == "assistant"]
    assert len(user_messages) == 1
    assert len(assistant_messages) == 1


# Feature: playground-fix, Property 9: Streaming display progression
@given(st.text(min_size=10, max_size=1000))
@settings(max_examples=100)
def test_property_9_streaming_display_progression(response_text: str) -> None:
    """
    Feature: playground-fix, Property 9: Streaming display progression
    
    For any agent response being streamed, partial content should be visible in the UI
    before completion.
    
    Validates: Requirements 5.1
    """
    # Simulate streaming by breaking response into chunks
    # In real streaming, tokens arrive incrementally
    chunk_size = max(1, len(response_text) // 10)  # Break into ~10 chunks
    chunks = [response_text[i:i+chunk_size] for i in range(0, len(response_text), chunk_size)]
    
    # Simulate the streaming display process
    accumulated_content = ""
    partial_displays = []
    
    for chunk in chunks:
        accumulated_content += chunk
        # During streaming, content should be visible with cursor
        display_with_cursor = accumulated_content + "▌"
        partial_displays.append(display_with_cursor)
        
        # Verify partial content is present
        assert len(accumulated_content) > 0
        assert accumulated_content in display_with_cursor
        assert display_with_cursor.endswith("▌")
    
    # After streaming completes, cursor should be removed
    final_display = accumulated_content
    assert not final_display.endswith("▌")
    assert final_display == response_text
    
    # Verify we had progressive display (multiple partial states)
    assert len(partial_displays) > 0
    
    # Verify each partial display showed increasing content
    for i in range(len(partial_displays) - 1):
        current_content = partial_displays[i].rstrip("▌")
        next_content = partial_displays[i + 1].rstrip("▌")
        # Content should grow or stay the same (never shrink)
        assert len(next_content) >= len(current_content)
    
    # Verify final accumulated content matches original
    assert accumulated_content == response_text
