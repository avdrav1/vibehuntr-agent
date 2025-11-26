"""Unit tests for similarity calculation in duplicate detection."""

import pytest
from app.event_planning.duplicate_detector import DuplicateDetector


class TestSimilarityCalculation:
    """Test similarity calculation functionality in DuplicateDetector."""
    
    def test_identical_sentences_return_1_0(self):
        """Test that identical sentences return similarity of 1.0."""
        detector = DuplicateDetector()
        
        sentence = "This is a test sentence."
        similarity = detector._calculate_similarity(sentence, sentence)
        
        assert similarity == 1.0
    
    def test_identical_sentences_different_instances(self):
        """Test that identical sentences (different string instances) return 1.0."""
        detector = DuplicateDetector()
        
        sentence1 = "This is a test sentence."
        sentence2 = "This is a test sentence."
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        assert similarity == 1.0
    
    def test_completely_different_sentences_near_zero(self):
        """Test that completely different sentences return similarity near 0.0."""
        detector = DuplicateDetector()
        
        sentence1 = "The quick brown fox jumps over the lazy dog."
        sentence2 = "Python programming is very interesting and fun."
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        # Should be low similarity (some common words like "is" may overlap)
        assert similarity < 0.4
        assert similarity >= 0.0
    
    def test_completely_different_short_sentences(self):
        """Test completely different short sentences."""
        detector = DuplicateDetector()
        
        sentence1 = "Hello world"
        sentence2 = "Goodbye moon"
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        # Should be very low similarity
        assert similarity < 0.3
        assert similarity >= 0.0
    
    def test_similar_sentences_high_score(self):
        """Test that similar sentences return similarity in 0.8-0.9 range."""
        detector = DuplicateDetector()
        
        sentence1 = "I found five Italian restaurants in South Philadelphia."
        sentence2 = "I found five Italian restaurants in South Philly."
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        # Should be high similarity (0.8-0.9 range)
        assert similarity >= 0.8
        assert similarity < 1.0
    
    def test_similar_sentences_minor_differences(self):
        """Test sentences with minor word differences."""
        detector = DuplicateDetector()
        
        sentence1 = "The cat sat on the mat."
        sentence2 = "The cat sits on the mat."
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        # Should be high similarity (one word different)
        assert similarity >= 0.85
        assert similarity < 1.0
    
    def test_similar_sentences_word_order(self):
        """Test sentences with same words but different order."""
        detector = DuplicateDetector()
        
        sentence1 = "The quick brown fox"
        sentence2 = "The brown quick fox"
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        # Should have moderate to high similarity (word order affects score)
        assert similarity >= 0.65
        assert similarity < 1.0
    
    def test_similar_sentences_extra_words(self):
        """Test sentences where one has extra words."""
        detector = DuplicateDetector()
        
        sentence1 = "I like pizza."
        sentence2 = "I really like pizza very much."
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        # Should have moderate similarity
        assert similarity >= 0.5
        assert similarity < 0.9
    
    def test_short_sentences_identical(self):
        """Test similarity with short identical sentences."""
        detector = DuplicateDetector()
        
        sentence1 = "Hello"
        sentence2 = "Hello"
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        assert similarity == 1.0
    
    def test_short_sentences_different(self):
        """Test similarity with short different sentences."""
        detector = DuplicateDetector()
        
        sentence1 = "Hello"
        sentence2 = "World"
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        # Should be very low or zero
        assert similarity < 0.3
        assert similarity >= 0.0
    
    def test_long_sentences_identical(self):
        """Test similarity with long identical sentences."""
        detector = DuplicateDetector()
        
        sentence = (
            "This is a very long sentence that contains many words and "
            "is designed to test the similarity calculation with longer "
            "text strings to ensure it works correctly."
        )
        similarity = detector._calculate_similarity(sentence, sentence)
        
        assert similarity == 1.0
    
    def test_long_sentences_similar(self):
        """Test similarity with long similar sentences."""
        detector = DuplicateDetector()
        
        sentence1 = (
            "This is a very long sentence that contains many words and "
            "is designed to test the similarity calculation with longer "
            "text strings to ensure it works correctly."
        )
        sentence2 = (
            "This is a very long sentence that contains many words and "
            "is designed to test the similarity calculation with longer "
            "text strings to ensure it functions correctly."
        )
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        # Should be very high similarity (only one word different)
        assert similarity >= 0.95
        assert similarity < 1.0
    
    def test_long_sentences_different(self):
        """Test similarity with long different sentences."""
        detector = DuplicateDetector()
        
        sentence1 = (
            "This is a very long sentence that contains many words and "
            "is designed to test the similarity calculation with longer "
            "text strings to ensure it works correctly."
        )
        sentence2 = (
            "Python is a high-level programming language that is widely "
            "used for web development, data science, and automation tasks "
            "because of its simplicity and readability."
        )
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        # Should be low similarity (some common words may overlap)
        assert similarity < 0.4
        assert similarity >= 0.0
    
    def test_empty_string_first(self):
        """Test similarity when first string is empty."""
        detector = DuplicateDetector()
        
        sentence1 = ""
        sentence2 = "This is a test."
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        # Should return 0.0 for empty string
        assert similarity == 0.0
    
    def test_empty_string_second(self):
        """Test similarity when second string is empty."""
        detector = DuplicateDetector()
        
        sentence1 = "This is a test."
        sentence2 = ""
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        # Should return 0.0 for empty string
        assert similarity == 0.0
    
    def test_both_empty_strings(self):
        """Test similarity when both strings are empty."""
        detector = DuplicateDetector()
        
        sentence1 = ""
        sentence2 = ""
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        # Should return 0.0 for both empty
        assert similarity == 0.0
    
    def test_whitespace_only_strings(self):
        """Test similarity with whitespace-only strings."""
        detector = DuplicateDetector()
        
        sentence1 = "   "
        sentence2 = "This is a test."
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        # Should be low similarity (whitespace may match some spaces in sentence2)
        assert similarity < 0.4
        assert similarity >= 0.0
    
    def test_case_sensitivity(self):
        """Test that similarity calculation is case-sensitive."""
        detector = DuplicateDetector()
        
        sentence1 = "This is a test."
        sentence2 = "this is a test."
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        # Should be very high but not 1.0 due to case difference
        assert similarity >= 0.9
        assert similarity < 1.0
    
    def test_punctuation_differences(self):
        """Test similarity with punctuation differences."""
        detector = DuplicateDetector()
        
        sentence1 = "Hello, world!"
        sentence2 = "Hello world"
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        # Should be high similarity (punctuation is minor difference)
        assert similarity >= 0.8
        assert similarity < 1.0
    
    def test_unicode_characters(self):
        """Test similarity with unicode characters."""
        detector = DuplicateDetector()
        
        sentence1 = "This has émojis 😀 and spëcial çharacters."
        sentence2 = "This has émojis 😀 and spëcial çharacters."
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        assert similarity == 1.0
    
    def test_unicode_differences(self):
        """Test similarity with unicode character differences."""
        detector = DuplicateDetector()
        
        sentence1 = "This has émojis 😀."
        sentence2 = "This has emojis 🎉."
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        # Should be high but not perfect similarity
        assert similarity >= 0.7
        assert similarity < 1.0
    
    def test_numbers_in_sentences(self):
        """Test similarity with numbers in sentences."""
        detector = DuplicateDetector()
        
        sentence1 = "I found 5 restaurants."
        sentence2 = "I found 5 restaurants."
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        assert similarity == 1.0
    
    def test_different_numbers(self):
        """Test similarity with different numbers."""
        detector = DuplicateDetector()
        
        sentence1 = "I found 5 restaurants."
        sentence2 = "I found 3 restaurants."
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        # Should be very high similarity (only number different)
        assert similarity >= 0.9
        assert similarity < 1.0
    
    def test_special_characters(self):
        """Test similarity with special characters."""
        detector = DuplicateDetector()
        
        sentence1 = "Price: $50-$100 per person."
        sentence2 = "Price: $50-$100 per person."
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        assert similarity == 1.0
    
    def test_similarity_is_symmetric(self):
        """Test that similarity(A, B) == similarity(B, A)."""
        detector = DuplicateDetector()
        
        sentence1 = "The quick brown fox jumps."
        sentence2 = "The lazy dog sleeps."
        
        similarity_ab = detector._calculate_similarity(sentence1, sentence2)
        similarity_ba = detector._calculate_similarity(sentence2, sentence1)
        
        # Similarity should be symmetric
        assert similarity_ab == similarity_ba
    
    def test_similarity_range(self):
        """Test that similarity is always between 0.0 and 1.0."""
        detector = DuplicateDetector()
        
        test_pairs = [
            ("Hello", "World"),
            ("Same", "Same"),
            ("", "Text"),
            ("Very long sentence here", "Short"),
            ("Test 123", "Test 456"),
        ]
        
        for sentence1, sentence2 in test_pairs:
            similarity = detector._calculate_similarity(sentence1, sentence2)
            assert 0.0 <= similarity <= 1.0, (
                f"Similarity {similarity} out of range for "
                f"'{sentence1}' vs '{sentence2}'"
            )
    
    def test_very_long_sentences(self):
        """Test similarity with very long sentences (performance check)."""
        detector = DuplicateDetector()
        
        # Create very long sentences
        sentence1 = " ".join(["word"] * 1000)
        sentence2 = " ".join(["word"] * 1000)
        
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        # Should be identical
        assert similarity == 1.0
    
    def test_very_long_different_sentences(self):
        """Test similarity with very long different sentences."""
        detector = DuplicateDetector()
        
        # Create very long different sentences
        sentence1 = " ".join([f"word{i}" for i in range(1000)])
        sentence2 = " ".join([f"text{i}" for i in range(1000)])
        
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        # Should be very low similarity
        assert similarity < 0.2
        assert similarity >= 0.0
    
    def test_substring_similarity(self):
        """Test similarity when one sentence is substring of another."""
        detector = DuplicateDetector()
        
        sentence1 = "This is a test"
        sentence2 = "This is a test sentence with more words"
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        # Should have moderate similarity (substring but different lengths)
        assert similarity >= 0.5
        assert similarity < 1.0
    
    def test_repeated_words(self):
        """Test similarity with repeated words."""
        detector = DuplicateDetector()
        
        sentence1 = "test test test test"
        sentence2 = "test test test test"
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        assert similarity == 1.0
    
    def test_repeated_words_different_count(self):
        """Test similarity with different counts of repeated words."""
        detector = DuplicateDetector()
        
        sentence1 = "test test test"
        sentence2 = "test test test test test"
        similarity = detector._calculate_similarity(sentence1, sentence2)
        
        # Should have moderate similarity
        assert similarity >= 0.5
        assert similarity < 1.0
