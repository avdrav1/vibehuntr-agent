"""Property-based tests for Chat UX improvements.

This module tests the correctness properties for the chat UX improvements feature,
including session management, typing indicators, retry functionality, and message editing.

Feature: chat-ux-improvements
"""

import sys
import os
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite
import pytest

# Add the project root and backend to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

from app.services.session_manager import SessionManager


# Custom strategies for generating test data

@composite
def session_id_strategy(draw: st.DrawFn) -> str:
    """Generate a valid session ID (UUID-like string)."""
    return draw(st.uuids().map(str))


@composite
def message_content_strategy(draw: st.DrawFn) -> str:
    """Generate valid message content."""
    return draw(st.text(min_size=1, max_size=500, alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'S', 'Z'),
        blacklist_characters='\x00'
    )))


@composite
def session_with_messages_strategy(draw: st.DrawFn) -> tuple:
    """Generate a session ID with a list of messages to add."""
    session_id = draw(session_id_strategy())
    num_messages = draw(st.integers(min_value=1, max_value=10))
    messages = []
    for _ in range(num_messages):
        role = draw(st.sampled_from(["user", "assistant"]))
        content = draw(message_content_strategy())
        messages.append({"role": role, "content": content})
    return session_id, messages


# Property Tests

# Feature: chat-ux-improvements, Property 3: Deleted sessions are removed
@given(
    session_ids=st.lists(session_id_strategy(), min_size=2, max_size=10, unique=True),
    delete_index=st.integers(min_value=0)
)
@settings(max_examples=100)
def test_property_3_deleted_sessions_are_removed(
    session_ids: list,
    delete_index: int
) -> None:
    """
    **Feature: chat-ux-improvements, Property 3: Deleted sessions are removed**
    
    *For any* session that is deleted, querying the session list should not 
    include that session ID.
    
    **Validates: Requirements 1.6**
    """
    # Create a fresh session manager
    session_manager = SessionManager()
    
    # Create all sessions
    for session_id in session_ids:
        session_manager.create_session(session_id)
        # Add at least one message so the session has content
        session_manager.add_message(session_id, "user", f"Hello from {session_id}")
    
    # Verify all sessions exist
    all_sessions_before = session_manager.get_all_sessions()
    assert len(all_sessions_before) == len(session_ids)
    
    # Pick a session to delete (use modulo to ensure valid index)
    session_to_delete = session_ids[delete_index % len(session_ids)]
    
    # Delete the session
    result = session_manager.delete_session(session_to_delete)
    assert result is True, "delete_session should return True for existing session"
    
    # Get all sessions after deletion
    all_sessions_after = session_manager.get_all_sessions()
    
    # Verify the deleted session is not in the list
    session_ids_after = [s["id"] for s in all_sessions_after]
    assert session_to_delete not in session_ids_after, \
        f"Deleted session {session_to_delete} should not appear in session list"
    
    # Verify the count decreased by 1
    assert len(all_sessions_after) == len(session_ids) - 1
    
    # Verify all other sessions still exist
    for session_id in session_ids:
        if session_id != session_to_delete:
            assert session_id in session_ids_after, \
                f"Non-deleted session {session_id} should still be in the list"


# Feature: chat-ux-improvements, Property 3 (variant): Delete non-existent session
@given(session_id=session_id_strategy())
@settings(max_examples=100)
def test_property_3_delete_nonexistent_session_returns_false(session_id: str) -> None:
    """
    **Feature: chat-ux-improvements, Property 3: Deleted sessions are removed (edge case)**
    
    *For any* session ID that doesn't exist, delete_session should return False.
    
    **Validates: Requirements 1.6**
    """
    # Create a fresh session manager (no sessions)
    session_manager = SessionManager()
    
    # Try to delete a non-existent session
    result = session_manager.delete_session(session_id)
    
    # Should return False
    assert result is False, "delete_session should return False for non-existent session"


# Feature: chat-ux-improvements, Property 3 (variant): Session no longer exists after deletion
@given(session_id=session_id_strategy())
@settings(max_examples=100)
def test_property_3_session_not_exists_after_deletion(session_id: str) -> None:
    """
    **Feature: chat-ux-improvements, Property 3: Deleted sessions are removed**
    
    *For any* session that is deleted, session_exists should return False.
    
    **Validates: Requirements 1.6**
    """
    # Create a fresh session manager
    session_manager = SessionManager()
    
    # Create the session
    session_manager.create_session(session_id)
    assert session_manager.session_exists(session_id) is True
    
    # Delete the session
    session_manager.delete_session(session_id)
    
    # Verify session no longer exists
    assert session_manager.session_exists(session_id) is False
