"""Unit tests for duplicate detection in DuplicateDetector."""

import pytest
from app.event_planning.duplicate_detector import DuplicateDetector


class TestDuplicateDetection:
    """Test duplicate detection functionality in DuplicateDetector."""
    
    def test_duplicate_sentences_detected(self):
        """Test that duplicate sentences are detected."""
        detector = DuplicateDetector(content_similarity_threshold=0.85)
        
        # Add some content to accumulated sentences
        detector.add_content("I found five Italian restaurants in South Philadelphia.")
        
        # Try to add the exact same sentence again
        is_duplicate, preview = detector.contains_duplicate_content(
            "I found five Italian restaurants in South Philadelphia."
        )
        
        assert is_duplicate is True
        assert preview is not None
        assert "I found five Italian restaurants" in preview
    
    def test_duplicate_sentences_with_minor_variation(self):
        """Test that duplicate sentences with minor variations are detected."""
        detector = DuplicateDetector(content_similarity_threshold=0.85)
        
        # Add original content
        detector.add_content("I found five Italian restaurants in South Philadelphia.")
        
        # Try to add very similar sentence (South Philly vs South Philadelphia)
        is_duplicate, preview = detector.contains_duplicate_content(
            "I found five Italian restaurants in South Philly."
        )
        
        assert is_duplicate is True
        assert preview is not None
    
    def test_similar_sentences_above_threshold_detected(self):
        """Test that similar sentences above threshold are detected as duplicates."""
        # Use a lower threshold to ensure detection
        detector = DuplicateDetector(content_similarity_threshold=0.80)
        
        # Add original content
        detector.add_content("The restaurant serves delicious Italian food.")
        
        # Add similar sentence that should be above 0.80 threshold
        is_duplicate, preview = detector.contains_duplicate_content(
            "The restaurant serves delicious Italian cuisine."
        )
        
        assert is_duplicate is True
        assert preview is not None
    
    def test_similar_sentences_below_threshold_not_detected(self):
        """Test that similar sentences below threshold are not detected as duplicates."""
        # Use a high threshold
        detector = DuplicateDetector(content_similarity_threshold=0.95)
        
        # Add original content
        detector.add_content("I found five Italian restaurants.")
        
        # Add somewhat similar but different sentence (should be below 0.95)
        is_duplicate, preview = detector.contains_duplicate_content(
            "I discovered three Mexican restaurants."
        )
        
        assert is_duplicate is False
        assert preview is None
    
    def test_similar_sentences_just_below_threshold(self):
        """Test sentences that are similar but just below the threshold."""
        detector = DuplicateDetector(content_similarity_threshold=0.90)
        
        # Add original content
        detector.add_content("The quick brown fox jumps over the lazy dog.")
        
        # Add sentence with some similarity but below threshold
        is_duplicate, preview = detector.contains_duplicate_content(
            "The quick brown cat walks around the lazy dog."
        )
        
        # Should not be detected as duplicate (similarity likely < 0.90)
        assert is_duplicate is False
        assert preview is None
    
    def test_completely_different_sentences_not_detected(self):
        """Test that completely different sentences are not detected as duplicates."""
        detector = DuplicateDetector(content_similarity_threshold=0.85)
        
        # Add original content
        detector.add_content("I found five Italian restaurants in South Philadelphia.")
        
        # Add completely different sentence
        is_duplicate, preview = detector.contains_duplicate_content(
            "Python programming is very interesting and fun to learn."
        )
        
        assert is_duplicate is False
        assert preview is None
    
    def test_different_topics_not_detected(self):
        """Test that sentences about different topics are not detected."""
        detector = DuplicateDetector(content_similarity_threshold=0.85)
        
        # Add content about restaurants
        detector.add_content("The restaurant has excellent reviews and great ambiance.")
        
        # Add content about weather
        is_duplicate, preview = detector.contains_duplicate_content(
            "The weather today is sunny with clear blue skies."
        )
        
        assert is_duplicate is False
        assert preview is None
    
    def test_empty_accumulated_response_not_detected(self):
        """Test that detection is skipped when accumulated response is empty."""
        detector = DuplicateDetector(content_similarity_threshold=0.85)
        
        # Don't add any content - accumulated_sentences should be empty
        
        # Try to check for duplicates with empty accumulated response
        is_duplicate, preview = detector.contains_duplicate_content(
            "This is the first sentence ever added."
        )
        
        assert is_duplicate is False
        assert preview is None
    
    def test_first_chunk_not_detected_as_duplicate(self):
        """Test that the very first chunk is never detected as duplicate."""
        detector = DuplicateDetector(content_similarity_threshold=0.85)
        
        # Verify accumulated sentences is empty
        assert len(detector.accumulated_sentences) == 0
        
        # First chunk should not be duplicate
        is_duplicate, preview = detector.contains_duplicate_content(
            "This is the first chunk of content."
        )
        
        assert is_duplicate is False
        assert preview is None
    
    def test_multiple_sentences_one_duplicate(self):
        """Test detection when new text has multiple sentences, one is duplicate."""
        detector = DuplicateDetector(content_similarity_threshold=0.85)
        
        # Add original content
        detector.add_content("I found five Italian restaurants.")
        
        # Add text with multiple sentences, one is duplicate
        new_text = "Here are some options. I found five Italian restaurants. They look great."
        is_duplicate, preview = detector.contains_duplicate_content(new_text)
        
        # Should detect the duplicate sentence
        assert is_duplicate is True
        assert preview is not None
        assert "I found five Italian restaurants" in preview
    
    def test_threshold_at_boundary(self):
        """Test detection at exact threshold boundary."""
        detector = DuplicateDetector(content_similarity_threshold=0.85)
        
        # Add original content
        detector.add_content("This is a test sentence for boundary testing.")
        
        # We can't easily create a sentence with exactly 0.85 similarity,
        # but we can test that the threshold is enforced correctly
        # by using identical sentences (1.0 similarity > 0.85)
        is_duplicate, preview = detector.contains_duplicate_content(
            "This is a test sentence for boundary testing."
        )
        
        assert is_duplicate is True
        assert preview is not None
    
    def test_default_threshold_value(self):
        """Test that default threshold is 0.85."""
        detector = DuplicateDetector()
        
        assert detector.content_similarity_threshold == 0.85
    
    def test_custom_threshold_value(self):
        """Test that custom threshold is respected."""
        detector = DuplicateDetector(content_similarity_threshold=0.90)
        
        assert detector.content_similarity_threshold == 0.90
    
    def test_threshold_1_0_only_exact_matches(self):
        """Test that threshold of 1.0 only detects exact matches."""
        detector = DuplicateDetector(content_similarity_threshold=1.0)
        
        # Add original content
        detector.add_content("This is a test sentence.")
        
        # Try very similar but not identical sentence
        is_duplicate, preview = detector.contains_duplicate_content(
            "This is a test sentence!"  # Added exclamation mark
        )
        
        # Should not be detected (similarity < 1.0)
        assert is_duplicate is False
        assert preview is None
        
        # Try exact match
        is_duplicate, preview = detector.contains_duplicate_content(
            "This is a test sentence."
        )
        
        # Should be detected (similarity == 1.0)
        assert is_duplicate is True
        assert preview is not None
    
    def test_threshold_0_8_detects_more_variations(self):
        """Test that lower threshold (0.8) detects more variations."""
        detector = DuplicateDetector(content_similarity_threshold=0.80)
        
        # Add original content
        detector.add_content("I found five Italian restaurants in the city.")
        
        # Try sentence with moderate similarity
        is_duplicate, preview = detector.contains_duplicate_content(
            "I found three Italian restaurants in the area."
        )
        
        # With 0.80 threshold, this should likely be detected
        # (many words in common: "I found", "Italian restaurants", "in the")
        assert is_duplicate is True
        assert preview is not None
    
    def test_accumulated_sentences_tracking(self):
        """Test that accumulated sentences are properly tracked."""
        detector = DuplicateDetector(content_similarity_threshold=0.85)
        
        # Initially empty
        assert len(detector.accumulated_sentences) == 0
        
        # Add content
        detector.add_content("First sentence. Second sentence. Third sentence.")
        
        # Should have accumulated sentences
        assert len(detector.accumulated_sentences) > 0
        assert len(detector.accumulated_sentences) <= 3  # May filter short sentences
    
    def test_sentence_window_size_limit(self):
        """Test that sentence window size is limited to 50."""
        detector = DuplicateDetector(content_similarity_threshold=0.85)
        
        # Add many sentences (more than window size)
        for i in range(60):
            detector.add_content(f"This is sentence number {i} with unique content.")
        
        # Should only keep last 50 sentences
        assert len(detector.accumulated_sentences) == 50
    
    def test_duplicate_detection_with_session_id(self):
        """Test that session_id parameter is accepted."""
        detector = DuplicateDetector(content_similarity_threshold=0.85)
        
        # Add content
        detector.add_content("Test sentence.")
        
        # Check with session_id
        is_duplicate, preview = detector.contains_duplicate_content(
            "Test sentence.",
            session_id="test-session-123"
        )
        
        assert is_duplicate is True
        assert preview is not None
    
    def test_preview_truncation(self):
        """Test that duplicate preview is truncated to 100 characters."""
        detector = DuplicateDetector(content_similarity_threshold=0.85)
        
        # Add very long sentence
        long_sentence = "This is a very long sentence " * 20  # > 100 chars
        detector.add_content(long_sentence)
        
        # Try to add it again
        is_duplicate, preview = detector.contains_duplicate_content(long_sentence)
        
        assert is_duplicate is True
        assert preview is not None
        assert len(preview) <= 100
    
    def test_multiple_accumulated_sentences_detection(self):
        """Test detection against multiple accumulated sentences."""
        detector = DuplicateDetector(content_similarity_threshold=0.85)
        
        # Add multiple different sentences
        detector.add_content("First sentence about restaurants.")
        detector.add_content("Second sentence about food.")
        detector.add_content("Third sentence about dining.")
        
        # Try to add sentence similar to the second one
        is_duplicate, preview = detector.contains_duplicate_content(
            "Second sentence about food."
        )
        
        assert is_duplicate is True
        assert preview is not None
    
    def test_detection_order_independence(self):
        """Test that detection works regardless of which sentence was added first."""
        detector1 = DuplicateDetector(content_similarity_threshold=0.85)
        detector2 = DuplicateDetector(content_similarity_threshold=0.85)
        
        sentence_a = "I found Italian restaurants."
        sentence_b = "I discovered Mexican restaurants."
        
        # Add in different orders
        detector1.add_content(sentence_a)
        is_dup1, _ = detector1.contains_duplicate_content(sentence_b)
        
        detector2.add_content(sentence_b)
        is_dup2, _ = detector2.contains_duplicate_content(sentence_a)
        
        # Both should give same result (both not duplicate)
        assert is_dup1 == is_dup2
        assert is_dup1 is False
    
    def test_case_sensitive_detection(self):
        """Test that detection is case-sensitive."""
        detector = DuplicateDetector(content_similarity_threshold=0.95)
        
        # Add lowercase sentence
        detector.add_content("this is a test sentence.")
        
        # Try uppercase version
        is_duplicate, preview = detector.contains_duplicate_content(
            "THIS IS A TEST SENTENCE."
        )
        
        # With high threshold (0.95), case difference should prevent detection
        # (similarity will be high but < 0.95 due to case differences)
        assert is_duplicate is False
        assert preview is None
    
    def test_punctuation_variations(self):
        """Test detection with punctuation variations."""
        detector = DuplicateDetector(content_similarity_threshold=0.90)
        
        # Add sentence with punctuation
        detector.add_content("Hello, world!")
        
        # Try without punctuation
        is_duplicate, preview = detector.contains_duplicate_content(
            "Hello world"
        )
        
        # Should be detected as similar (high similarity despite punctuation)
        assert is_duplicate is True
        assert preview is not None
    
    def test_number_variations(self):
        """Test detection with number variations."""
        detector = DuplicateDetector(content_similarity_threshold=0.85)
        
        # Add sentence with number
        detector.add_content("I found 5 restaurants.")
        
        # Try with different number
        is_duplicate, preview = detector.contains_duplicate_content(
            "I found 3 restaurants."
        )
        
        # Should be detected as similar (only number different)
        assert is_duplicate is True
        assert preview is not None
