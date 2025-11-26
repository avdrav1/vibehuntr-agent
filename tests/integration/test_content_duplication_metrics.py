"""
Integration test for content duplication metrics.

This test verifies that content-level duplication is properly tracked in metrics,
logged with ContentDuplicationEvent details, and included in response metadata.

**Validates: Requirement 2.4 - Content-level duplication statistics in response metadata**
"""

import pytest
import uuid
import logging
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock, Mock
from app.event_planning.duplication_metrics import DuplicationMetrics, get_metrics_instance
from app.event_planning.duplicate_detector import DuplicateDetector


class LogCapture:
    """Helper class to capture log records during tests."""
    
    def __init__(self):
        self.records: List[logging.LogRecord] = []
    
    def __call__(self, record: logging.LogRecord) -> bool:
        """Capture log record."""
        self.records.append(record)
        return True
    
    def get_warnings(self) -> List[logging.LogRecord]:
        """Get all WARNING level records."""
        return [r for r in self.records if r.levelno == logging.WARNING]
    
    def get_errors(self) -> List[logging.LogRecord]:
        """Get all ERROR level records."""
        return [r for r in self.records if r.levelno == logging.ERROR]
    
    def find_records_with_text(self, text: str) -> List[logging.LogRecord]:
        """Find records containing specific text."""
        return [r for r in self.records if text.lower() in r.getMessage().lower()]
    
    def find_records_with_extra(self, key: str) -> List[logging.LogRecord]:
        """Find records with specific extra field."""
        return [r for r in self.records if hasattr(r, key)]


class TestContentDuplicationMetrics:
    """Test content duplication metrics tracking and logging.
    
    **Validates: Requirement 2.4**
    """
    
    def test_content_duplicate_increments_metrics(self):
        """
        Test that content-level duplicates increment the metrics counter.
        
        This test simulates content-level duplication and verifies that the
        metrics counter is incremented correctly.
        
        **Validates: Requirement 2.4**
        """
        # Arrange
        metrics = DuplicationMetrics(enable_logging=False)
        session_id = f"test_metrics_{uuid.uuid4()}"
        
        # Act - increment content duplicate counter
        metrics.increment_content_duplicate_detected(session_id, count=1)
        metrics.increment_content_duplicate_detected(session_id, count=2)
        
        # Assert - verify metrics are tracked
        session_metrics = metrics.get_session_metrics(session_id)
        assert session_metrics['total_content_duplicates_detected'] == 3, \
            f"Expected 3 content duplicates, got {session_metrics['total_content_duplicates_detected']}"
        
        # Verify global metrics
        global_metrics = metrics.get_global_metrics()
        assert global_metrics['total_content_duplicates_detected'] == 3, \
            f"Expected 3 global content duplicates, got {global_metrics['total_content_duplicates_detected']}"
    
    def test_content_duplicate_separate_from_chunk_duplicates(self):
        """
        Test that content-level duplicates are tracked separately from chunk-level duplicates.
        
        **Validates: Requirement 2.4**
        """
        # Arrange
        metrics = DuplicationMetrics(enable_logging=False)
        session_id = f"test_separate_{uuid.uuid4()}"
        
        # Act - increment both types of duplicates
        metrics.increment_duplicate_detected(session_id, count=5)  # Chunk-level
        metrics.increment_content_duplicate_detected(session_id, count=3)  # Content-level
        
        # Assert - verify they are tracked separately
        session_metrics = metrics.get_session_metrics(session_id)
        assert session_metrics['total_duplicates_detected'] == 5, \
            f"Expected 5 chunk duplicates, got {session_metrics['total_duplicates_detected']}"
        assert session_metrics['total_content_duplicates_detected'] == 3, \
            f"Expected 3 content duplicates, got {session_metrics['total_content_duplicates_detected']}"
        
        # Verify global metrics
        global_metrics = metrics.get_global_metrics()
        assert global_metrics['total_duplicates_detected'] == 5
        assert global_metrics['total_content_duplicates_detected'] == 3
    
    def test_content_duplicate_logging(self):
        """
        Test that content-level duplicates are logged with proper details.
        
        **Validates: Requirement 2.4**
        """
        # Arrange
        metrics = DuplicationMetrics(enable_logging=True)
        session_id = f"test_logging_{uuid.uuid4()}"
        
        # Set up log capture
        log_capture = LogCapture()
        logger = logging.getLogger('app.event_planning.duplication_metrics')
        logger.addFilter(log_capture)
        
        try:
            # Act - increment content duplicate (should log on 1st, 6th, 11th, etc.)
            metrics.increment_content_duplicate_detected(session_id, count=1)
            
            # Assert - verify warning was logged
            warnings = log_capture.get_warnings()
            assert len(warnings) > 0, "Expected at least one warning log"
            
            # Verify log contains expected information
            warning_messages = [w.getMessage() for w in warnings]
            assert any('content-level duplicate' in msg.lower() for msg in warning_messages), \
                "Expected log message about content-level duplicate"
            
            # Verify extra fields in log record
            content_dup_records = [r for r in warnings if 'content-level duplicate' in r.getMessage().lower()]
            if content_dup_records:
                record = content_dup_records[0]
                assert hasattr(record, 'session_id'), "Log record should have session_id"
                assert hasattr(record, 'content_duplicates_in_session'), \
                    "Log record should have content_duplicates_in_session"
        finally:
            logger.removeFilter(log_capture)
    
    def test_duplicate_detector_logs_content_duplication_event(self):
        """
        Test that DuplicateDetector logs ContentDuplicationEvent details.
        
        This test verifies that when content-level duplication is detected,
        the detector logs the event with all required details:
        - duplicate_sentence_preview
        - similar_sentence_preview
        - similarity_score
        - position
        
        **Validates: Requirement 2.4**
        """
        # Arrange
        detector = DuplicateDetector(content_similarity_threshold=0.85)
        session_id = f"test_event_{uuid.uuid4()}"
        
        # Set up log capture
        log_capture = LogCapture()
        logger = logging.getLogger('app.event_planning.duplicate_detector')
        logger.addFilter(log_capture)
        
        try:
            # Add some initial content
            initial_text = "I found five great Italian restaurants in South Philadelphia."
            detector.add_content(initial_text)
            
            # Act - try to add very similar content (should be detected as duplicate)
            duplicate_text = "I found five great Italian restaurants in South Philadelphia."
            is_dup, preview = detector.contains_duplicate_content(duplicate_text, session_id=session_id)
            
            # Assert - verify duplication was detected
            assert is_dup, "Expected duplicate to be detected"
            assert preview is not None, "Expected duplicate preview to be returned"
            
            # Verify ContentDuplicationEvent was logged
            warnings = log_capture.get_warnings()
            assert len(warnings) > 0, "Expected at least one warning log"
            
            # Find the content-level duplicate warning
            content_dup_warnings = [w for w in warnings if 'content-level duplicate' in w.getMessage().lower()]
            assert len(content_dup_warnings) > 0, "Expected content-level duplicate warning"
            
            # Verify log contains required fields
            warning = content_dup_warnings[0]
            assert hasattr(warning, 'session_id'), "Log should have session_id"
            assert hasattr(warning, 'duplicate_preview'), "Log should have duplicate_preview"
            assert hasattr(warning, 'similar_sentence_preview'), "Log should have similar_sentence_preview"
            assert hasattr(warning, 'similarity_score'), "Log should have similarity_score"
            assert hasattr(warning, 'position'), "Log should have position"
            
            # Verify values are reasonable
            assert warning.similarity_score >= 0.85, \
                f"Similarity score should be >= 0.85, got {warning.similarity_score}"
            assert warning.position >= 0, "Position should be non-negative"
        finally:
            logger.removeFilter(log_capture)
    
    def test_response_metadata_includes_content_duplicate_count(self):
        """
        Test that response metadata includes content duplicate count.
        
        This test verifies that when a response completes, the metadata
        includes information about content-level duplicates detected.
        
        **Validates: Requirement 2.4**
        """
        # Arrange
        metrics = DuplicationMetrics(enable_logging=False)
        session_id = f"test_metadata_{uuid.uuid4()}"
        
        # Simulate a response with content duplicates
        metrics.increment_content_duplicate_detected(session_id, count=2)
        metrics.record_response_quality(
            session_id=session_id,
            total_chunks=10,
            duplicate_chunks=2
        )
        
        # Act - get session metrics (this is what would be included in response metadata)
        session_metrics = metrics.get_session_metrics(session_id)
        
        # Assert - verify content duplicate count is included
        assert 'total_content_duplicates_detected' in session_metrics, \
            "Session metrics should include total_content_duplicates_detected"
        assert session_metrics['total_content_duplicates_detected'] == 2, \
            f"Expected 2 content duplicates, got {session_metrics['total_content_duplicates_detected']}"
        
        # Verify other expected fields
        assert 'total_responses' in session_metrics
        assert 'total_duplicates_detected' in session_metrics
        assert 'duplication_rate' in session_metrics
    
    def test_multiple_content_duplicates_tracked_separately(self):
        """
        Test that multiple content duplication events are tracked separately.
        
        When multiple duplications occur in a single response, each should be
        tracked and reported separately.
        
        **Validates: Requirement 2.4**
        """
        # Arrange
        detector = DuplicateDetector(content_similarity_threshold=0.85)
        session_id = f"test_multiple_{uuid.uuid4()}"
        
        # Set up log capture
        log_capture = LogCapture()
        logger = logging.getLogger('app.event_planning.duplicate_detector')
        logger.addFilter(log_capture)
        
        try:
            # Add initial content with multiple sentences
            initial_sentences = [
                "I found five great Italian restaurants.",
                "They are all located in South Philadelphia.",
                "Each restaurant has excellent reviews."
            ]
            
            for sentence in initial_sentences:
                detector.add_content(sentence)
            
            # Act - try to add duplicate versions of each sentence
            duplicate_count = 0
            for sentence in initial_sentences:
                is_dup, preview = detector.contains_duplicate_content(sentence, session_id=session_id)
                if is_dup:
                    duplicate_count += 1
            
            # Assert - all three should be detected as duplicates
            assert duplicate_count == 3, \
                f"Expected 3 duplicates to be detected, got {duplicate_count}"
            
            # Verify each duplication was logged separately
            warnings = log_capture.get_warnings()
            content_dup_warnings = [w for w in warnings if 'content-level duplicate' in w.getMessage().lower()]
            assert len(content_dup_warnings) >= 3, \
                f"Expected at least 3 content-level duplicate warnings, got {len(content_dup_warnings)}"
        finally:
            logger.removeFilter(log_capture)
    
    @pytest.mark.skip(reason="Requires real agent - run manually if needed")
    def test_content_duplicate_with_real_agent_streaming(self):
        """
        Test content duplication metrics with real agent streaming.
        
        This test uses the actual agent to generate a response and verifies
        that if content duplication occurs, it's properly tracked in metrics.
        
        Note: This test may not always trigger content duplication (depends on LLM),
        but it verifies the metrics infrastructure is in place.
        
        **Validates: Requirement 2.4**
        """
        # This test is skipped by default to avoid hanging during test collection
        # To run it manually: pytest tests/integration/test_content_duplication_metrics.py::TestContentDuplicationMetrics::test_content_duplicate_with_real_agent_streaming -v -s
        from app.event_planning.agent_loader import get_agent
        from app.event_planning.agent_invoker import invoke_agent_streaming
        
        # Arrange
        agent = get_agent()
        session_id = f"test_real_agent_{uuid.uuid4()}"
        
        # Get metrics instance
        metrics = get_metrics_instance()
        
        # Reset metrics for this session to start clean
        metrics.reset_session_metrics(session_id)
        
        # Set up log capture
        log_capture = LogCapture()
        logger = logging.getLogger('app.event_planning.duplicate_detector')
        logger.addFilter(log_capture)
        
        try:
            # Act - invoke agent with streaming
            message = "Tell me about Italian restaurants in Philadelphia"
            tokens = []
            for item in invoke_agent_streaming(agent, message, session_id):
                if item['type'] == 'text':
                    tokens.append(item['content'])
            
            full_response = ''.join(tokens)
            
            # Assert - verify response was generated
            assert len(full_response) > 0, "Expected non-empty response"
            
            # Get session metrics
            session_metrics = metrics.get_session_metrics(session_id)
            
            # Verify metrics structure is correct (even if no duplicates occurred)
            assert 'total_content_duplicates_detected' in session_metrics, \
                "Session metrics should include total_content_duplicates_detected"
            assert 'total_duplicates_detected' in session_metrics, \
                "Session metrics should include total_duplicates_detected"
            
            # If content duplicates were detected, verify they were logged
            if session_metrics['total_content_duplicates_detected'] > 0:
                warnings = log_capture.get_warnings()
                content_dup_warnings = [w for w in warnings if 'content-level duplicate' in w.getMessage().lower()]
                assert len(content_dup_warnings) > 0, \
                    "If content duplicates detected, they should be logged"
        finally:
            logger.removeFilter(log_capture)
    
    def test_global_metrics_aggregate_content_duplicates(self):
        """
        Test that global metrics properly aggregate content duplicates across sessions.
        
        **Validates: Requirement 2.4**
        """
        # Arrange
        metrics = DuplicationMetrics(enable_logging=False)
        session_ids = [f"test_global_{uuid.uuid4()}" for _ in range(3)]
        
        # Act - increment content duplicates in multiple sessions
        for i, session_id in enumerate(session_ids):
            metrics.increment_content_duplicate_detected(session_id, count=i+1)
        
        # Assert - verify global metrics aggregate correctly
        global_metrics = metrics.get_global_metrics()
        expected_total = sum(range(1, 4))  # 1 + 2 + 3 = 6
        assert global_metrics['total_content_duplicates_detected'] == expected_total, \
            f"Expected {expected_total} total content duplicates, got {global_metrics['total_content_duplicates_detected']}"
        
        # Verify each session has correct count
        for i, session_id in enumerate(session_ids):
            session_metrics = metrics.get_session_metrics(session_id)
            assert session_metrics['total_content_duplicates_detected'] == i+1, \
                f"Session {i} should have {i+1} content duplicates"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
