"""Unit tests for error handling in response duplication components.

This module tests that error handling in DuplicateDetector, ResponseTracker,
and DuplicationMetrics works correctly and provides graceful degradation.
"""

import pytest
import logging
from unittest.mock import Mock, patch
from app.event_planning.duplicate_detector import DuplicateDetector, PipelineStage
from app.event_planning.response_tracker import ResponseTracker
from app.event_planning.duplication_metrics import DuplicationMetrics


class TestDuplicateDetectorErrorHandling:
    """Test error handling in DuplicateDetector."""
    
    def test_is_duplicate_handles_hash_error(self):
        """Test that is_duplicate handles hash calculation errors gracefully."""
        detector = DuplicateDetector()
        
        # Mock hash to raise an error
        with patch('builtins.hash', side_effect=Exception("Hash error")):
            # Should not crash, should return False (graceful degradation)
            result = detector.is_duplicate("test chunk", PipelineStage.TOKEN_YIELDING)
            assert result is False
    
    def test_is_duplicate_handles_pattern_detection_error(self):
        """Test that is_duplicate handles pattern detection errors gracefully."""
        detector = DuplicateDetector()
        
        # Mock pattern detector to raise an error
        detector.pattern_detector.detect_pattern = Mock(side_effect=Exception("Pattern error"))
        
        # Should not crash, should return False (graceful degradation)
        result = detector.is_duplicate("test chunk", PipelineStage.TOKEN_YIELDING)
        assert result is False
    
    def test_is_duplicate_handles_similarity_error(self):
        """Test that is_duplicate handles similarity detection errors gracefully."""
        detector = DuplicateDetector()
        
        # Add some chunks first
        detector.add_chunk("chunk1")
        detector.add_chunk("chunk2")
        
        # Mock similarity calculation to raise an error
        detector._calculate_similarity = Mock(side_effect=Exception("Similarity error"))
        
        # Should not crash, should return False (graceful degradation)
        result = detector.is_duplicate("test chunk", PipelineStage.TOKEN_YIELDING)
        assert result is False
    
    def test_add_chunk_handles_error(self):
        """Test that add_chunk handles errors gracefully."""
        detector = DuplicateDetector()
        
        # Mock hash to raise an error
        with patch('builtins.hash', side_effect=Exception("Hash error")):
            # Should not crash
            detector.add_chunk("test chunk")
            # Chunk should not be added due to error
            assert len(detector.chunk_sequence) == 0
    
    def test_log_duplication_event_handles_error(self):
        """Test that logging errors don't crash the detector."""
        detector = DuplicateDetector()
        
        # Mock logger to raise an error
        with patch('app.event_planning.duplicate_detector.logger.warning', side_effect=Exception("Log error")):
            # Should not crash
            detector._log_duplication_event("test chunk", "hash", PipelineStage.TOKEN_YIELDING)


class TestResponseTrackerErrorHandling:
    """Test error handling in ResponseTracker."""
    
    def test_track_chunk_handles_hash_error(self):
        """Test that track_chunk handles hash calculation errors gracefully."""
        tracker = ResponseTracker("session_123")
        
        # Mock hash to raise an error
        with patch('builtins.hash', side_effect=Exception("Hash error")):
            # Should not crash, should return True (graceful degradation)
            result = tracker.track_chunk("test chunk")
            assert result is True
    
    def test_track_chunk_handles_logging_error(self):
        """Test that track_chunk handles logging errors gracefully."""
        tracker = ResponseTracker("session_123")
        
        # Mock logger to raise an error
        with patch('app.event_planning.response_tracker.logger.debug', side_effect=Exception("Log error")):
            # Should not crash
            result = tracker.track_chunk("test chunk")
            assert result is True
    
    def test_get_metrics_handles_error(self):
        """Test that get_metrics handles errors gracefully."""
        tracker = ResponseTracker("session_123")
        
        # Mock datetime to raise an error
        with patch('app.event_planning.response_tracker.datetime') as mock_datetime:
            mock_datetime.now.side_effect = Exception("Datetime error")
            
            # Should not crash, should return default metadata
            metadata = tracker.get_metrics()
            assert metadata is not None
            assert metadata.response_id == tracker.response_id
    
    def test_log_token_yield_handles_error(self):
        """Test that log_token_yield handles errors gracefully."""
        tracker = ResponseTracker("session_123")
        
        # Mock logger to raise an error
        with patch('app.event_planning.response_tracker.logger.debug', side_effect=Exception("Log error")):
            # Should not crash
            tracker.log_token_yield("token", 0)
    
    def test_log_session_history_update_handles_error(self):
        """Test that log_session_history_update handles errors gracefully."""
        tracker = ResponseTracker("session_123")
        
        # Mock logger to raise an error
        with patch('app.event_planning.response_tracker.logger.info', side_effect=Exception("Log error")):
            # Should not crash
            tracker.log_session_history_update("user", "message")


class TestDuplicationMetricsErrorHandling:
    """Test error handling in DuplicationMetrics."""
    
    def test_increment_duplicate_detected_handles_error(self):
        """Test that increment_duplicate_detected handles errors gracefully."""
        metrics = DuplicationMetrics(enable_logging=False)
        
        # Mock session metrics to raise an error
        with patch.object(metrics, '_get_or_create_session_metrics', side_effect=Exception("Metrics error")):
            # Should not crash
            metrics.increment_duplicate_detected("session_123")
    
    def test_record_response_quality_handles_error(self):
        """Test that record_response_quality handles errors gracefully."""
        metrics = DuplicationMetrics(enable_logging=False)
        
        # Mock session metrics to raise an error
        with patch.object(metrics, '_get_or_create_session_metrics', side_effect=Exception("Metrics error")):
            # Should not crash
            metrics.record_response_quality("session_123", 10, 2)
    
    def test_log_resolution_confirmation_handles_error(self):
        """Test that log_resolution_confirmation handles errors gracefully."""
        metrics = DuplicationMetrics(enable_logging=False)
        
        # Mock session metrics to raise an error
        with patch.object(metrics, '_get_or_create_session_metrics', side_effect=Exception("Metrics error")):
            # Should not crash
            metrics.log_resolution_confirmation("session_123")
    
    def test_check_threshold_exceeded_handles_error(self):
        """Test that check_threshold_exceeded handles errors gracefully."""
        metrics = DuplicationMetrics(enable_logging=False)
        
        # Mock get_duplication_rate to raise an error
        with patch.object(metrics, 'get_duplication_rate', side_effect=Exception("Rate error")):
            # Should not crash, should return False (graceful degradation)
            result = metrics.check_threshold_exceeded("session_123")
            assert result is False
    
    def test_get_duplication_rate_handles_empty_session(self):
        """Test that get_duplication_rate handles empty sessions gracefully."""
        metrics = DuplicationMetrics(enable_logging=False)
        
        # Should not crash, should return 0.0
        rate = metrics.get_duplication_rate("nonexistent_session")
        assert rate == 0.0
    
    def test_get_session_metrics_handles_empty_session(self):
        """Test that get_session_metrics handles empty sessions gracefully."""
        metrics = DuplicationMetrics(enable_logging=False)
        
        # Should not crash, should return default metrics
        session_metrics = metrics.get_session_metrics("nonexistent_session")
        assert session_metrics is not None
        assert session_metrics["total_responses"] == 0


class TestIntegratedErrorHandling:
    """Test error handling in integrated scenarios."""
    
    def test_detector_continues_after_logging_failure(self):
        """Test that detector continues to work after logging failures."""
        detector = DuplicateDetector()
        
        # Add a chunk successfully
        detector.add_chunk("chunk1")
        assert len(detector.chunk_sequence) == 1
        
        # Mock logger to fail
        with patch('app.event_planning.duplicate_detector.logger.warning', side_effect=Exception("Log error")):
            # Try to detect duplicate (should log but not crash)
            result = detector.is_duplicate("chunk1", PipelineStage.TOKEN_YIELDING)
            # Should still detect the duplicate
            assert result is True
    
    def test_tracker_continues_after_metrics_failure(self):
        """Test that tracker continues to work after metrics failures."""
        tracker = ResponseTracker("session_123")
        
        # Track a chunk successfully
        result = tracker.track_chunk("chunk1")
        assert result is True
        
        # Mock logger to fail
        with patch('app.event_planning.response_tracker.logger.debug', side_effect=Exception("Log error")):
            # Track another chunk (should work despite logging failure)
            result = tracker.track_chunk("chunk2")
            assert result is True
    
    def test_metrics_continues_after_logging_failure(self):
        """Test that metrics continues to work after logging failures."""
        metrics = DuplicationMetrics(enable_logging=True)
        
        # Record a response successfully
        metrics.record_response_quality("session_123", 10, 0)
        
        # Mock logger to fail
        with patch('app.event_planning.duplication_metrics.logger.info', side_effect=Exception("Log error")):
            # Record another response (should work despite logging failure)
            metrics.record_response_quality("session_123", 10, 0)
            
            # Verify metrics were still updated
            session_metrics = metrics.get_session_metrics("session_123")
            assert session_metrics["total_responses"] == 2
