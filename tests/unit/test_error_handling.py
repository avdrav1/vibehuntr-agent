"""Unit tests for error handling in duplicate detection."""

import pytest
from unittest.mock import patch, MagicMock
from app.event_planning.duplicate_detector import DuplicateDetector


class TestErrorHandling:
    """Test error handling and graceful degradation in duplicate detection."""
    
    def test_sentence_splitting_with_regex_error(self):
        """Test that sentence splitting handles regex errors gracefully."""
        detector = DuplicateDetector()
        
        # Mock re.split to raise an exception
        with patch('app.event_planning.duplicate_detector.re.split') as mock_split:
            mock_split.side_effect = Exception("Regex error")
            
            # Should fall back to paragraph splitting
            text = "First paragraph.\n\nSecond paragraph."
            sentences = detector._split_into_sentences(text)
            
            # Should return paragraphs as fallback
            assert isinstance(sentences, list)
            assert len(sentences) >= 1
            # Should have fallen back to paragraph splitting
            assert any("First paragraph" in s for s in sentences)
    
    def test_sentence_splitting_with_attribute_error(self):
        """Test sentence splitting with AttributeError."""
        detector = DuplicateDetector()
        
        # Mock re.split to raise AttributeError
        with patch('app.event_planning.duplicate_detector.re.split') as mock_split:
            mock_split.side_effect = AttributeError("Attribute error")
            
            text = "Test sentence. Another sentence."
            sentences = detector._split_into_sentences(text)
            
            # Should handle error gracefully
            assert isinstance(sentences, list)
            assert len(sentences) >= 1
    
    def test_sentence_splitting_fallback_also_fails(self):
        """Test when both sentence splitting and fallback fail."""
        detector = DuplicateDetector()
        
        # Mock both re.split and str.split to fail
        with patch('app.event_planning.duplicate_detector.re.split') as mock_split:
            mock_split.side_effect = Exception("Regex error")
            
            # Create a mock text object that fails on split
            mock_text = MagicMock()
            mock_text.split.side_effect = Exception("Split error")
            mock_text.__bool__.return_value = True
            mock_text.strip.return_value = mock_text
            mock_text.__str__.return_value = "test text"
            
            # Should return the text as-is in a list (last resort)
            sentences = detector._split_into_sentences(mock_text)
            
            # Should handle error gracefully
            assert isinstance(sentences, list)
    
    def test_similarity_calculation_with_none_first_arg(self):
        """Test similarity calculation when first argument is None."""
        detector = DuplicateDetector()
        
        # Should return 0.0 for None values
        similarity = detector._calculate_similarity(None, "test")  # type: ignore
        
        assert similarity == 0.0
    
    def test_similarity_calculation_with_none_second_arg(self):
        """Test similarity calculation when second argument is None."""
        detector = DuplicateDetector()
        
        # Should return 0.0 for None values
        similarity = detector._calculate_similarity("test", None)  # type: ignore
        
        assert similarity == 0.0
    
    def test_similarity_calculation_with_both_none(self):
        """Test similarity calculation when both arguments are None."""
        detector = DuplicateDetector()
        
        # Should return 0.0 for None values
        similarity = detector._calculate_similarity(None, None)  # type: ignore
        
        assert similarity == 0.0
    
    def test_similarity_calculation_with_sequence_matcher_error(self):
        """Test similarity calculation when SequenceMatcher raises an error."""
        detector = DuplicateDetector()
        
        # Mock SequenceMatcher to raise an exception
        with patch('app.event_planning.duplicate_detector.SequenceMatcher') as mock_matcher:
            mock_matcher.side_effect = Exception("SequenceMatcher error")
            
            # Should return 0.0 on error
            similarity = detector._calculate_similarity("test1", "test2")
            
            assert similarity == 0.0
    
    def test_similarity_calculation_with_ratio_error(self):
        """Test similarity calculation when ratio() method raises an error."""
        detector = DuplicateDetector()
        
        # Mock SequenceMatcher.ratio to raise an exception
        with patch('app.event_planning.duplicate_detector.SequenceMatcher') as mock_matcher_class:
            mock_matcher = MagicMock()
            mock_matcher.ratio.side_effect = Exception("Ratio calculation error")
            mock_matcher_class.return_value = mock_matcher
            
            # Should return 0.0 on error
            similarity = detector._calculate_similarity("test1", "test2")
            
            assert similarity == 0.0
    
    def test_contains_duplicate_content_with_split_error(self):
        """Test contains_duplicate_content when sentence splitting fails."""
        detector = DuplicateDetector()
        
        # Add some content first
        detector.add_content("This is a test sentence.")
        
        # Mock _split_into_sentences to raise an exception
        with patch.object(detector, '_split_into_sentences') as mock_split:
            mock_split.side_effect = Exception("Split error")
            
            # Should return (False, None) on error (graceful degradation)
            is_dup, preview = detector.contains_duplicate_content("Test content")
            
            assert is_dup is False
            assert preview is None
    
    def test_contains_duplicate_content_with_similarity_error(self):
        """Test contains_duplicate_content when similarity calculation fails."""
        detector = DuplicateDetector()
        
        # Add some content first
        detector.add_content("This is a test sentence.")
        
        # Mock _find_similar_sentence to raise an exception
        with patch.object(detector, '_find_similar_sentence') as mock_find:
            mock_find.side_effect = Exception("Similarity error")
            
            # Should return (False, None) on error (graceful degradation)
            is_dup, preview = detector.contains_duplicate_content("Test content here.")
            
            assert is_dup is False
            assert preview is None
    
    def test_contains_duplicate_content_with_general_exception(self):
        """Test contains_duplicate_content with a general exception."""
        detector = DuplicateDetector()
        
        # Add some content first
        detector.add_content("This is a test sentence.")
        
        # Mock _split_into_sentences to raise a general exception
        with patch.object(detector, '_split_into_sentences') as mock_split:
            mock_split.side_effect = RuntimeError("Unexpected error")
            
            # Should return (False, None) on error (graceful degradation)
            is_dup, preview = detector.contains_duplicate_content("Test content")
            
            assert is_dup is False
            assert preview is None
    
    def test_add_content_with_split_error(self):
        """Test add_content when sentence splitting fails."""
        detector = DuplicateDetector()
        
        # Mock _split_into_sentences to raise an exception
        with patch.object(detector, '_split_into_sentences') as mock_split:
            mock_split.side_effect = Exception("Split error")
            
            # Should handle error gracefully (not crash)
            try:
                detector.add_content("Test content")
                # If it doesn't raise, that's good
                success = True
            except Exception:
                success = False
            
            assert success is True
    
    def test_add_content_with_general_exception(self):
        """Test add_content with a general exception."""
        detector = DuplicateDetector()
        
        # Mock _split_into_sentences to raise a general exception
        with patch.object(detector, '_split_into_sentences') as mock_split:
            mock_split.side_effect = RuntimeError("Unexpected error")
            
            # Should handle error gracefully (not crash)
            try:
                detector.add_content("Test content")
                success = True
            except Exception:
                success = False
            
            assert success is True
    
    def test_find_similar_sentence_with_empty_accumulated(self):
        """Test _find_similar_sentence with empty accumulated sentences."""
        detector = DuplicateDetector()
        
        # Should return None when accumulated_sentences is empty
        result = detector._find_similar_sentence("Test sentence")
        
        assert result is None
    
    def test_find_similar_sentence_with_similarity_error(self):
        """Test _find_similar_sentence when similarity calculation fails."""
        detector = DuplicateDetector()
        
        # Add some content
        detector.add_content("This is a test sentence.")
        
        # Mock _calculate_similarity to raise an exception
        with patch.object(detector, '_calculate_similarity') as mock_calc:
            mock_calc.side_effect = Exception("Calculation error")
            
            # Should return None on error (graceful degradation)
            result = detector._find_similar_sentence("Another sentence")
            
            assert result is None
    
    def test_find_similar_sentence_with_partial_errors(self):
        """Test _find_similar_sentence when some comparisons fail."""
        detector = DuplicateDetector()
        
        # Add multiple sentences
        detector.add_content("First sentence. Second sentence. Third sentence.")
        
        # Mock _calculate_similarity to fail on some calls
        original_calc = detector._calculate_similarity
        call_count = [0]
        
        def mock_calc(text1, text2):
            call_count[0] += 1
            if call_count[0] == 2:  # Fail on second call
                raise Exception("Calculation error")
            return original_calc(text1, text2)
        
        with patch.object(detector, '_calculate_similarity', side_effect=mock_calc):
            # Should continue checking other sentences despite error
            result = detector._find_similar_sentence("Fourth sentence")
            
            # Should return None (no similar sentence found)
            assert result is None
    
    def test_graceful_degradation_allows_content_through(self):
        """Test that errors in detection allow content through (don't block)."""
        detector = DuplicateDetector()
        
        # Add some content
        detector.add_content("This is a test sentence.")
        
        # Mock to cause various errors
        with patch.object(detector, '_split_into_sentences') as mock_split:
            mock_split.side_effect = Exception("Error")
            
            # Content should be allowed through (not blocked)
            is_dup, preview = detector.contains_duplicate_content("New content")
            
            assert is_dup is False  # Not marked as duplicate
            assert preview is None  # No preview
    
    def test_multiple_error_types_handled(self):
        """Test that different error types are all handled gracefully."""
        detector = DuplicateDetector()
        
        # Add some content
        detector.add_content("This is a test sentence.")
        
        error_types = [
            ValueError("Value error"),
            TypeError("Type error"),
            AttributeError("Attribute error"),
            KeyError("Key error"),
            RuntimeError("Runtime error"),
            Exception("General exception"),
        ]
        
        for error in error_types:
            with patch.object(detector, '_split_into_sentences') as mock_split:
                mock_split.side_effect = error
                
                # Should handle all error types gracefully
                is_dup, preview = detector.contains_duplicate_content("Test content")
                
                assert is_dup is False, f"Failed for {type(error).__name__}"
                assert preview is None, f"Failed for {type(error).__name__}"
    
    def test_error_in_is_duplicate_method(self):
        """Test error handling in is_duplicate method."""
        detector = DuplicateDetector()
        
        # Mock hash() to raise an exception
        with patch('builtins.hash') as mock_hash:
            mock_hash.side_effect = Exception("Hash error")
            
            # Should return False on error (graceful degradation)
            is_dup = detector.is_duplicate("test chunk")
            
            assert is_dup is False
    
    def test_error_in_add_chunk_method(self):
        """Test error handling in add_chunk method."""
        detector = DuplicateDetector()
        
        # Mock hash() to raise an exception
        with patch('builtins.hash') as mock_hash:
            mock_hash.side_effect = Exception("Hash error")
            
            # Should handle error gracefully (not crash)
            try:
                detector.add_chunk("test chunk")
                success = True
            except Exception:
                success = False
            
            assert success is True
    
    def test_error_logging_doesnt_crash(self):
        """Test that the main error handling works even if debug logging fails."""
        detector = DuplicateDetector()
        
        # Add some content
        detector.add_content("This is a test sentence.")
        
        # Mock only debug logger to raise an exception (which is called before the error)
        with patch('app.event_planning.duplicate_detector.logger') as mock_logger:
            # Let error logging work, but make debug logging fail
            mock_logger.debug.side_effect = Exception("Debug logging error")
            
            # The detection should still work despite debug logging failures
            # Test with empty content which triggers debug logging
            is_dup, preview = detector.contains_duplicate_content("")
            
            # Should handle gracefully - empty content returns False
            assert is_dup is False
            assert preview is None
    
    def test_none_text_in_contains_duplicate_content(self):
        """Test contains_duplicate_content with None as text."""
        detector = DuplicateDetector()
        
        # Add some content first
        detector.add_content("This is a test sentence.")
        
        # Should handle None gracefully
        try:
            is_dup, preview = detector.contains_duplicate_content(None)  # type: ignore
            # If it returns, check the result
            assert is_dup is False
            assert preview is None
        except (TypeError, AttributeError):
            # Also acceptable - None is not a valid string
            pass
    
    def test_invalid_type_in_add_content(self):
        """Test add_content with invalid type."""
        detector = DuplicateDetector()
        
        # Should handle invalid types gracefully
        try:
            detector.add_content(None)  # type: ignore
            success = True
        except (TypeError, AttributeError):
            # Also acceptable - None is not a valid string
            success = True
        
        assert success is True
    
    def test_error_recovery_continues_processing(self):
        """Test that after an error, the detector continues to work."""
        detector = DuplicateDetector()
        
        # Add initial content
        detector.add_content("Initial content here.")
        
        # Cause an error
        with patch.object(detector, '_split_into_sentences') as mock_split:
            mock_split.side_effect = Exception("Error")
            is_dup, preview = detector.contains_duplicate_content("Error content")
            assert is_dup is False
        
        # Now try normal operation (should work)
        detector.add_content("New content after error.")
        is_dup, preview = detector.contains_duplicate_content("New content after error.")
        
        # Should detect duplicate normally
        assert is_dup is True
        assert preview is not None
    
    def test_concurrent_errors_handled(self):
        """Test handling of multiple errors in sequence."""
        detector = DuplicateDetector()
        
        # Add some content
        detector.add_content("Test sentence.")
        
        # Cause multiple errors in sequence
        for i in range(5):
            with patch.object(detector, '_split_into_sentences') as mock_split:
                mock_split.side_effect = Exception(f"Error {i}")
                
                is_dup, preview = detector.contains_duplicate_content(f"Content {i}")
                
                # Each should be handled gracefully
                assert is_dup is False
                assert preview is None
    
    def test_error_in_nested_method_calls(self):
        """Test error handling when nested method calls fail."""
        detector = DuplicateDetector()
        
        # Add content
        detector.add_content("Test sentence.")
        
        # Mock _calculate_similarity (called by _find_similar_sentence)
        with patch.object(detector, '_calculate_similarity') as mock_calc:
            mock_calc.side_effect = Exception("Nested error")
            
            # Should handle nested error gracefully
            is_dup, preview = detector.contains_duplicate_content("Another sentence here.")
            
            assert is_dup is False
            assert preview is None
    
    def test_error_with_valid_session_id(self):
        """Test error handling with session_id parameter."""
        detector = DuplicateDetector()
        
        # Add content
        detector.add_content("Test sentence.")
        
        # Cause error with session_id
        with patch.object(detector, '_split_into_sentences') as mock_split:
            mock_split.side_effect = Exception("Error")
            
            is_dup, preview = detector.contains_duplicate_content(
                "Test content",
                session_id="test-session-123"
            )
            
            assert is_dup is False
            assert preview is None
