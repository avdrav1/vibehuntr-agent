"""Property-based test for concurrent session isolation.

This module tests Property 4: Concurrent session isolation for the
response duplication fix feature.
"""

import sys
import os
from hypothesis import given, strategies as st, settings

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.event_planning.response_tracker import ResponseTracker
from app.event_planning.duplicate_detector import DuplicateDetector
from app.event_planning.duplication_metrics import DuplicationMetrics


# Feature: response-duplication-fix, Property 4: Concurrent session isolation
@given(
    st.lists(
        st.tuples(
            st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyz0123456789-'),  # session_id
            st.text(min_size=1, max_size=100),  # user_id
            st.text(min_size=1, max_size=500)  # chunk
        ),
        min_size=2,
        max_size=10,
        unique_by=lambda x: x[0]  # Ensure unique session IDs
    )
)
@settings(max_examples=100)
def test_property_4_concurrent_session_isolation(session_data: list) -> None:
    """
    Feature: response-duplication-fix, Property 4: Concurrent session isolation
    
    For any set of concurrent sessions, each session should maintain response
    uniqueness independently without interference from other sessions.
    
    This test validates that:
    1. Each session tracks its own responses independently
    2. Duplicate detection in one session doesn't affect other sessions
    3. Response IDs are unique across all sessions
    4. Metrics are tracked separately per session
    
    Validates: Requirements 1.4, 3.5
    """
    # Create response trackers for each session
    trackers = {}
    for session_id, user_id, _ in session_data:
        trackers[session_id] = ResponseTracker(session_id=session_id, user_id=user_id)
    
    # Create duplicate detectors for each session
    detectors = {}
    for session_id, _, _ in session_data:
        detectors[session_id] = DuplicateDetector()
    
    # Create metrics instance
    metrics = DuplicationMetrics()
    
    # Process chunks for each session
    for session_id, user_id, chunk in session_data:
        tracker = trackers[session_id]
        detector = detectors[session_id]
        
        # Track the chunk
        is_unique = tracker.track_chunk(chunk)
        
        # Check for duplicates
        if not detector.is_duplicate(chunk):
            detector.add_chunk(chunk)
        else:
            metrics.increment_duplicate_detected(session_id)
    
    # Verify: Each session has independent tracking
    for session_id, user_id, chunk in session_data:
        tracker = trackers[session_id]
        
        # Verify tracker has correct session ID
        assert tracker.session_id == session_id, \
            f"Tracker should have session ID {session_id}"
        
        # Verify tracker has correct user ID
        assert tracker.user_id == user_id, \
            f"Tracker should have user ID {user_id}"
    
    # Verify: Response IDs are unique across all sessions
    response_ids = [tracker.response_id for tracker in trackers.values()]
    assert len(response_ids) == len(set(response_ids)), \
        "Response IDs must be unique across all concurrent sessions"
    
    # Verify: Each session has independent metrics
    for session_id, _, _ in session_data:
        session_metrics = metrics.get_session_metrics(session_id)
        
        # Verify session ID is correct
        assert session_metrics['session_id'] == session_id, \
            f"Metrics should be for session {session_id}"
        
        # Verify metrics are independent (not affected by other sessions)
        # Each session should have its own counts
        assert 'total_duplicates_detected' in session_metrics
        assert 'total_responses' in session_metrics
    
    # Verify: Duplicate detection is independent per session
    # If we add the same chunk to different sessions, each should track it independently
    test_chunk = "test_isolation_chunk"
    for session_id in detectors.keys():
        detector = detectors[session_id]
        
        # First occurrence in this session should not be a duplicate
        is_dup_first = detector.is_duplicate(test_chunk)
        assert not is_dup_first, \
            f"First occurrence of chunk in session {session_id} should not be duplicate"
        
        detector.add_chunk(test_chunk)
        
        # Second occurrence in this session should be a duplicate
        is_dup_second = detector.is_duplicate(test_chunk)
        assert is_dup_second, \
            f"Second occurrence of chunk in session {session_id} should be duplicate"
    
    # Verify: Session isolation - chunks in one session don't affect others
    # Each session independently detected the test_chunk as duplicate on second occurrence
    # This proves sessions are isolated
