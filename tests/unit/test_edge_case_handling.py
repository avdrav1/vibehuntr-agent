"""Unit tests for edge case handling in duplicate detection."""

import pytest
from app.event_planning.duplicate_detector import DuplicateDetector


class TestEdgeCaseHandling:
    """Test edge case handling in duplicate detection."""
    
    def test_empty_content_skips_detection(self):
        """Test that empty content skips duplicate detection."""
        detector = DuplicateDetector()
        
        # Add some content first
        detector.add_content("This is a test sentence.")
        
        # Test empty string
        is_dup, preview = detector.contains_duplicate_content("")
        assert is_dup is False
        assert preview is None
        
    def test_whitespace_only_content_skips_detection(self):
        """Test that whitespace-only content skips duplicate detection."""
        detector = DuplicateDetector()
        
        # Add some content first
        detector.add_content("This is a test sentence.")
        
        # Test whitespace-only strings
        test_cases = [
            "   ",
            "\n",
            "\t",
            "  \n  \t  ",
        ]
        
        for whitespace_text in test_cases:
            is_dup, preview = detector.contains_duplicate_content(whitespace_text)
            assert is_dup is False, f"Failed for: {repr(whitespace_text)}"
            assert preview is None, f"Failed for: {repr(whitespace_text)}"
    
    def test_very_short_chunks_skip_detection(self):
        """Test that very short chunks (< 10 chars) skip duplicate detection."""
        detector = DuplicateDetector()
        
        # Add some content first
        detector.add_content("This is a test sentence.")
        
        # Test short strings (< 10 characters)
        test_cases = [
            "a",
            "ab",
            "abc",
            "test",
            "short",
            "123456789",  # Exactly 9 characters
        ]
        
        for short_text in test_cases:
            assert len(short_text) < 10, f"Test case too long: {short_text}"
            is_dup, preview = detector.contains_duplicate_content(short_text)
            assert is_dup is False, f"Failed for: {short_text}"
            assert preview is None, f"Failed for: {short_text}"
    
    def test_empty_accumulated_response_skips_detection(self):
        """Test that detection is skipped when accumulated_sentences is empty."""
        detector = DuplicateDetector()
        
        # Don't add any content - accumulated_sentences should be empty
        assert len(detector.accumulated_sentences) == 0
        
        # Try to detect duplicates with no accumulated content
        is_dup, preview = detector.contains_duplicate_content("This is a test sentence.")
        assert is_dup is False
        assert preview is None
    
    def test_first_chunk_is_not_duplicate(self):
        """Test that the first chunk is never considered a duplicate."""
        detector = DuplicateDetector()
        
        # First chunk should not be a duplicate
        first_chunk = "This is the first chunk of content."
        is_dup, preview = detector.contains_duplicate_content(first_chunk)
        assert is_dup is False
        assert preview is None
        
        # Add it to tracking
        detector.add_content(first_chunk)
        
        # Now the same content should be detected as duplicate
        is_dup, preview = detector.contains_duplicate_content(first_chunk)
        assert is_dup is True
        assert preview is not None
    
    def test_edge_case_combination(self):
        """Test combination of edge cases."""
        detector = DuplicateDetector()
        
        # Empty accumulated + empty content
        is_dup, preview = detector.contains_duplicate_content("")
        assert is_dup is False
        assert preview is None
        
        # Empty accumulated + short content
        is_dup, preview = detector.contains_duplicate_content("short")
        assert is_dup is False
        assert preview is None
        
        # Empty accumulated + whitespace
        is_dup, preview = detector.contains_duplicate_content("   ")
        assert is_dup is False
        assert preview is None
        
        # Add some content
        detector.add_content("This is a longer sentence with enough content.")
        
        # Now test edge cases with accumulated content
        is_dup, preview = detector.contains_duplicate_content("")
        assert is_dup is False
        assert preview is None
        
        is_dup, preview = detector.contains_duplicate_content("short")
        assert is_dup is False
        assert preview is None
        
        is_dup, preview = detector.contains_duplicate_content("   ")
        assert is_dup is False
        assert preview is None
    
    def test_ten_character_boundary(self):
        """Test the 10-character boundary for short chunk detection."""
        detector = DuplicateDetector()
        
        # Add some content first
        detector.add_content("This is a test sentence.")
        
        # 9 characters - should skip
        is_dup, preview = detector.contains_duplicate_content("123456789")
        assert is_dup is False
        assert preview is None
        
        # 10 characters - should NOT skip (should process)
        # Note: This won't be detected as duplicate since it's different content
        is_dup, preview = detector.contains_duplicate_content("1234567890")
        assert is_dup is False  # Not a duplicate, but was processed
        assert preview is None
        
        # Add the 10-char content
        detector.add_content("1234567890")
        
        # Now it should be detected as duplicate
        is_dup, preview = detector.contains_duplicate_content("1234567890")
        assert is_dup is True
        assert preview is not None
    
    def test_no_errors_on_edge_cases(self):
        """Test that edge cases don't raise exceptions."""
        detector = DuplicateDetector()
        
        # These should all complete without raising exceptions
        try:
            detector.contains_duplicate_content(None)  # type: ignore
        except (TypeError, AttributeError):
            # Expected - None is not a valid string
            pass
        
        # These should not raise exceptions
        detector.contains_duplicate_content("")
        detector.contains_duplicate_content("   ")
        detector.contains_duplicate_content("\n\n\n")
        detector.contains_duplicate_content("a")
        detector.contains_duplicate_content("ab")
        
        # Add content and try again
        detector.add_content("Some content here.")
        detector.contains_duplicate_content("")
        detector.contains_duplicate_content("   ")
        detector.contains_duplicate_content("a")
