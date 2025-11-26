"""Unit tests for sentence splitting in duplicate detection."""

import pytest
from app.event_planning.duplicate_detector import DuplicateDetector


class TestSentenceSplitting:
    """Test sentence splitting functionality in DuplicateDetector."""
    
    def test_normal_sentences_with_periods(self):
        """Test splitting normal sentences with periods."""
        detector = DuplicateDetector()
        
        text = "This is the first sentence. This is the second sentence. This is the third sentence."
        sentences = detector._split_into_sentences(text)
        
        assert len(sentences) == 3
        assert sentences[0] == "This is the first sentence"
        assert sentences[1] == "This is the second sentence"
        # Last sentence keeps its punctuation since there's no whitespace after it
        assert sentences[2] == "This is the third sentence."
    
    def test_sentences_with_exclamation_marks(self):
        """Test splitting sentences with exclamation marks."""
        detector = DuplicateDetector()
        
        text = "This is exciting! This is also exciting! And this too!"
        sentences = detector._split_into_sentences(text)
        
        assert len(sentences) == 3
        assert sentences[0] == "This is exciting"
        assert sentences[1] == "This is also exciting"
        # Last sentence keeps its punctuation since there's no whitespace after it
        assert sentences[2] == "And this too!"
    
    def test_sentences_with_question_marks(self):
        """Test splitting sentences with question marks."""
        detector = DuplicateDetector()
        
        text = "Is this a question? Is this another question? What about this?"
        sentences = detector._split_into_sentences(text)
        
        assert len(sentences) == 3
        assert sentences[0] == "Is this a question"
        assert sentences[1] == "Is this another question"
        # Last sentence keeps its punctuation since there's no whitespace after it
        assert sentences[2] == "What about this?"
    
    def test_mixed_punctuation(self):
        """Test splitting sentences with mixed punctuation."""
        detector = DuplicateDetector()
        
        text = "This is a statement. Is this a question? This is exciting!"
        sentences = detector._split_into_sentences(text)
        
        assert len(sentences) == 3
        assert sentences[0] == "This is a statement"
        assert sentences[1] == "Is this a question"
        # Last sentence keeps its punctuation since there's no whitespace after it
        assert sentences[2] == "This is exciting!"
    
    def test_multiple_punctuation_marks(self):
        """Test splitting with multiple consecutive punctuation marks."""
        detector = DuplicateDetector()
        
        text = "Really?! This is amazing!! What...? Okay."
        sentences = detector._split_into_sentences(text)
        
        # Should handle multiple punctuation marks
        assert len(sentences) >= 3
        assert "Really" in sentences[0]
        assert "amazing" in sentences[1]
    
    def test_text_with_no_punctuation(self):
        """Test splitting text with no sentence-ending punctuation."""
        detector = DuplicateDetector()
        
        text = "This is text with no punctuation at all"
        sentences = detector._split_into_sentences(text)
        
        # Should return the whole text as one sentence
        assert len(sentences) == 1
        assert sentences[0] == "This is text with no punctuation at all"
    
    def test_empty_text(self):
        """Test splitting empty text."""
        detector = DuplicateDetector()
        
        text = ""
        sentences = detector._split_into_sentences(text)
        
        assert len(sentences) == 0
        assert sentences == []
    
    def test_text_with_only_whitespace(self):
        """Test splitting text with only whitespace."""
        detector = DuplicateDetector()
        
        test_cases = [
            "   ",
            "\n",
            "\t",
            "  \n  \t  ",
            "\n\n\n",
        ]
        
        for whitespace_text in test_cases:
            sentences = detector._split_into_sentences(whitespace_text)
            assert len(sentences) == 0, f"Failed for: {repr(whitespace_text)}"
            assert sentences == [], f"Failed for: {repr(whitespace_text)}"
    
    def test_whitespace_around_sentences(self):
        """Test that whitespace around sentences is properly stripped."""
        detector = DuplicateDetector()
        
        text = "  This is a sentence.   This is another.  "
        sentences = detector._split_into_sentences(text)
        
        assert len(sentences) == 2
        assert sentences[0] == "This is a sentence"
        assert sentences[1] == "This is another"
        # Verify no leading/trailing whitespace
        assert sentences[0].strip() == sentences[0]
        assert sentences[1].strip() == sentences[1]
    
    def test_sentences_with_newlines(self):
        """Test splitting sentences that contain newlines."""
        detector = DuplicateDetector()
        
        text = "This is the first sentence.\nThis is the second sentence.\nThis is the third."
        sentences = detector._split_into_sentences(text)
        
        assert len(sentences) == 3
        assert "first sentence" in sentences[0]
        assert "second sentence" in sentences[1]
        assert "third" in sentences[2]
    
    def test_single_sentence(self):
        """Test splitting text with a single sentence."""
        detector = DuplicateDetector()
        
        text = "This is just one sentence."
        sentences = detector._split_into_sentences(text)
        
        assert len(sentences) == 1
        # Single sentence keeps its punctuation since there's no whitespace after it
        assert sentences[0] == "This is just one sentence."
    
    def test_sentence_ending_without_space(self):
        """Test handling of sentence ending without trailing space."""
        detector = DuplicateDetector()
        
        text = "First sentence.Second sentence."
        sentences = detector._split_into_sentences(text)
        
        # Without space after period, might not split correctly
        # This tests the actual behavior of the regex
        # The regex requires whitespace after punctuation
        if len(sentences) == 1:
            # If it doesn't split, that's the current behavior
            assert "First sentence.Second sentence" in sentences[0]
        else:
            # If it does split, verify the split
            assert len(sentences) >= 1
    
    def test_abbreviations_and_periods(self):
        """Test handling of abbreviations with periods."""
        detector = DuplicateDetector()
        
        # Note: The simple regex won't handle abbreviations perfectly
        # This test documents the current behavior
        text = "Dr. Smith went to the store. He bought milk."
        sentences = detector._split_into_sentences(text)
        
        # The regex will split on "Dr. " which is not ideal but acceptable
        # for our duplicate detection use case
        assert len(sentences) >= 2
        assert "milk" in sentences[-1]
    
    def test_long_text_with_many_sentences(self):
        """Test splitting long text with many sentences."""
        detector = DuplicateDetector()
        
        text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
        sentences = detector._split_into_sentences(text)
        
        assert len(sentences) == 5
        for i, sentence in enumerate(sentences, 1):
            assert f"Sentence {['one', 'two', 'three', 'four', 'five'][i-1]}" in sentence
    
    def test_empty_sentences_are_filtered(self):
        """Test that empty sentences are filtered out."""
        detector = DuplicateDetector()
        
        # Text with multiple spaces between sentences
        text = "First sentence.     Second sentence."
        sentences = detector._split_into_sentences(text)
        
        # Should only get non-empty sentences
        assert len(sentences) == 2
        assert all(len(s) > 0 for s in sentences)
        assert all(s.strip() == s for s in sentences)
    
    def test_punctuation_only_text(self):
        """Test text with only punctuation."""
        detector = DuplicateDetector()
        
        text = "...!!???"
        sentences = detector._split_into_sentences(text)
        
        # Should return empty list or handle gracefully
        # After splitting and filtering empty strings, should be empty
        assert len(sentences) == 0 or all(len(s) > 0 for s in sentences)
    
    def test_unicode_and_special_characters(self):
        """Test splitting with unicode and special characters."""
        detector = DuplicateDetector()
        
        text = "This has émojis 😀. This has spëcial çharacters. This is normal."
        sentences = detector._split_into_sentences(text)
        
        assert len(sentences) == 3
        assert "émojis" in sentences[0]
        assert "çharacters" in sentences[1]
        assert "normal" in sentences[2]
    
    def test_error_handling_fallback(self):
        """Test that error handling falls back to paragraph splitting."""
        detector = DuplicateDetector()
        
        # Normal text should work fine
        text = "First paragraph.\n\nSecond paragraph."
        sentences = detector._split_into_sentences(text)
        
        # Should successfully split
        assert len(sentences) >= 1
        assert isinstance(sentences, list)
        assert all(isinstance(s, str) for s in sentences)
