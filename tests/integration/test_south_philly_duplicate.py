"""
Integration test for South Philly duplicate bug.

This test reproduces the exact conversation that triggered content-level duplication:
"Italian food" → "$$" → "South Philly Italian"

The bug manifested as duplicate paragraphs in the final response, particularly:
- Venue list appearing multiple times
- "Okay, I found five Italian restaurants" appearing multiple times

**Validates: Requirement 1.4 - No duplicate paragraphs in final response**
"""

import pytest
import uuid
import re
from typing import List, Set
from app.event_planning.agent_loader import get_agent
from app.event_planning.agent_invoker import invoke_agent


class TestSouthPhillyDuplicate:
    """Test the South Philly duplicate bug scenario.
    
    **Validates: Requirement 1.4**
    """
    
    def test_south_philly_conversation_no_duplicates(self):
        """
        Test the exact conversation that triggered the South Philly duplicate bug.
        
        This test reproduces the conversation:
        1. User: "Italian food"
        2. User: "$$"
        3. User: "South Philly Italian"
        
        And verifies that the final response has no duplicate paragraphs.
        
        **Validates: Requirement 1.4**
        """
        # Arrange
        agent = get_agent()
        session_id = f"test_south_philly_{uuid.uuid4()}"
        
        # The exact conversation that triggered the bug
        messages = [
            "Italian food",
            "$$",
            "South Philly Italian"
        ]
        
        # Act - execute the conversation
        responses = []
        for message in messages:
            response = invoke_agent(agent, message, session_id)
            responses.append(response)
        
        # Get the final response (the one that had duplicates)
        final_response = responses[-1]
        
        # Assert - verify no duplicate paragraphs
        paragraphs = self._extract_paragraphs(final_response)
        
        # Check for exact duplicate paragraphs
        paragraph_set = set(paragraphs)
        assert len(paragraphs) == len(paragraph_set), \
            f"Found duplicate paragraphs in response. Total: {len(paragraphs)}, Unique: {len(paragraph_set)}"
        
        # Additional check: verify no paragraph appears more than once
        paragraph_counts = {}
        for para in paragraphs:
            paragraph_counts[para] = paragraph_counts.get(para, 0) + 1
        
        duplicates = {p: count for p, count in paragraph_counts.items() if count > 1}
        assert len(duplicates) == 0, \
            f"Found paragraphs that appear multiple times: {duplicates}"
    
    def test_venue_list_appears_once(self):
        """
        Test that the venue list appears only once in the South Philly response.
        
        The bug caused the venue list to be repeated multiple times.
        
        **Validates: Requirement 1.4**
        """
        # Arrange
        agent = get_agent()
        session_id = f"test_venue_list_{uuid.uuid4()}"
        
        # Execute the conversation
        messages = ["Italian food", "$$", "South Philly Italian"]
        responses = []
        for message in messages:
            response = invoke_agent(agent, message, session_id)
            responses.append(response)
        
        final_response = responses[-1]
        
        # Act - extract venue mentions
        # Look for patterns like "1. Restaurant Name" or "- Restaurant Name"
        venue_list_patterns = [
            r'\d+\.\s+[A-Z][a-zA-Z\s]+',  # Numbered lists: "1. Restaurant Name"
            r'-\s+[A-Z][a-zA-Z\s]+',       # Bullet lists: "- Restaurant Name"
        ]
        
        venue_mentions = []
        for pattern in venue_list_patterns:
            matches = re.findall(pattern, final_response)
            venue_mentions.extend(matches)
        
        # Assert - each venue should appear at most once
        if venue_mentions:
            venue_set = set(venue_mentions)
            # Allow some flexibility - venues might be mentioned in different contexts
            # But the same formatted list item shouldn't appear twice
            venue_counts = {}
            for venue in venue_mentions:
                venue_counts[venue] = venue_counts.get(venue, 0) + 1
            
            duplicate_venues = {v: count for v, count in venue_counts.items() if count > 1}
            assert len(duplicate_venues) == 0, \
                f"Found duplicate venue list items: {duplicate_venues}"
    
    def test_intro_phrase_appears_once(self):
        """
        Test that intro phrases like "Okay, I found five Italian restaurants" appear only once.
        
        The bug caused intro phrases to be repeated.
        
        **Validates: Requirement 1.4**
        """
        # Arrange
        agent = get_agent()
        session_id = f"test_intro_phrase_{uuid.uuid4()}"
        
        # Execute the conversation
        messages = ["Italian food", "$$", "South Philly Italian"]
        responses = []
        for message in messages:
            response = invoke_agent(agent, message, session_id)
            responses.append(response)
        
        final_response = responses[-1]
        
        # Act - look for common intro phrases
        intro_patterns = [
            r"(?i)okay,?\s+i\s+found\s+\w+\s+italian\s+restaurants?",
            r"(?i)here\s+are\s+\w+\s+italian\s+restaurants?",
            r"(?i)i\s+found\s+\w+\s+italian\s+restaurants?",
        ]
        
        # Assert - each intro phrase should appear at most once
        for pattern in intro_patterns:
            matches = re.findall(pattern, final_response)
            if matches:
                # Check if the same phrase appears multiple times
                phrase_counts = {}
                for match in matches:
                    # Normalize whitespace for comparison
                    normalized = ' '.join(match.split())
                    phrase_counts[normalized] = phrase_counts.get(normalized, 0) + 1
                
                duplicate_phrases = {p: count for p, count in phrase_counts.items() if count > 1}
                assert len(duplicate_phrases) == 0, \
                    f"Found duplicate intro phrases: {duplicate_phrases}"
    
    def test_no_repeated_sentences(self):
        """
        Test that no sentences are repeated in the South Philly response.
        
        This is a more granular check than paragraphs - ensures sentence-level uniqueness.
        
        **Validates: Requirement 1.4**
        """
        # Arrange
        agent = get_agent()
        session_id = f"test_sentences_{uuid.uuid4()}"
        
        # Execute the conversation
        messages = ["Italian food", "$$", "South Philly Italian"]
        responses = []
        for message in messages:
            response = invoke_agent(agent, message, session_id)
            responses.append(response)
        
        final_response = responses[-1]
        
        # Act - extract sentences
        sentences = self._extract_sentences(final_response)
        
        # Filter out very short sentences (< 10 chars) as they might legitimately repeat
        substantial_sentences = [s for s in sentences if len(s) >= 10]
        
        # Assert - no sentence should appear more than once
        sentence_counts = {}
        for sentence in substantial_sentences:
            # Normalize whitespace for comparison
            normalized = ' '.join(sentence.split())
            sentence_counts[normalized] = sentence_counts.get(normalized, 0) + 1
        
        duplicate_sentences = {s: count for s, count in sentence_counts.items() if count > 1}
        assert len(duplicate_sentences) == 0, \
            f"Found duplicate sentences: {duplicate_sentences}"
    
    def test_multi_turn_context_retention(self):
        """
        Test that context is properly retained across turns without causing duplication.
        
        This verifies that the context injection mechanism doesn't cause content duplication.
        
        **Validates: Requirement 1.4**
        """
        # Arrange
        agent = get_agent()
        session_id = f"test_context_{uuid.uuid4()}"
        
        # Execute the conversation
        messages = ["Italian food", "$$", "South Philly Italian"]
        responses = []
        
        for message in messages:
            response = invoke_agent(agent, message, session_id)
            responses.append(response)
            
            # Each response should have no internal duplicates (if non-empty)
            if response and response.strip():
                paragraphs = self._extract_paragraphs(response)
                paragraph_set = set(paragraphs)
                assert len(paragraphs) == len(paragraph_set), \
                    f"Found duplicate paragraphs in response to '{message}'"
        
        # Verify that non-empty responses are different
        # Filter out empty responses first
        non_empty_responses = [(i, resp) for i, resp in enumerate(responses) if resp and resp.strip()]
        
        # Check that non-empty responses are unique
        for idx1, (i, resp1) in enumerate(non_empty_responses):
            for idx2, (j, resp2) in enumerate(non_empty_responses):
                if idx1 != idx2:
                    # Responses should be different
                    assert resp1 != resp2, \
                        f"Response {i} and {j} are identical (possible duplication bug)"
    
    def test_streaming_no_duplicates(self):
        """
        Test that streaming the South Philly conversation produces no duplicates.
        
        This tests the streaming path specifically, which is where the bug occurred.
        
        **Validates: Requirement 1.4**
        """
        # Arrange
        from app.event_planning.agent_invoker import invoke_agent_streaming
        
        agent = get_agent()
        session_id = f"test_streaming_{uuid.uuid4()}"
        
        # Execute the conversation with streaming
        messages = ["Italian food", "$$", "South Philly Italian"]
        
        for message in messages:
            # Collect all tokens
            tokens = []
            for item in invoke_agent_streaming(agent, message, session_id):
                if item['type'] == 'text':
                    tokens.append(item['content'])
            
            # Reconstruct response
            full_response = ''.join(tokens)
            
            # Assert - no duplicate paragraphs in this response
            paragraphs = self._extract_paragraphs(full_response)
            paragraph_set = set(paragraphs)
            assert len(paragraphs) == len(paragraph_set), \
                f"Found duplicate paragraphs in streaming response to '{message}'"
            
            # Assert - no duplicate sentences
            sentences = self._extract_sentences(full_response)
            substantial_sentences = [s for s in sentences if len(s) >= 10]
            sentence_set = set(substantial_sentences)
            assert len(substantial_sentences) == len(sentence_set), \
                f"Found duplicate sentences in streaming response to '{message}'"
    
    # Helper methods
    
    def _extract_paragraphs(self, text: str) -> List[str]:
        """
        Extract paragraphs from text.
        
        Args:
            text: The text to extract paragraphs from
            
        Returns:
            List of paragraphs (non-empty, stripped)
        """
        # Split on double newlines or single newlines followed by significant whitespace
        paragraphs = re.split(r'\n\s*\n|\n(?=\s{2,})', text)
        
        # Filter out empty paragraphs and strip whitespace
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def _extract_sentences(self, text: str) -> List[str]:
        """
        Extract sentences from text.
        
        Args:
            text: The text to extract sentences from
            
        Returns:
            List of sentences (non-empty, stripped)
        """
        # Split on sentence-ending punctuation followed by whitespace
        sentences = re.split(r'[.!?]+\s+', text)
        
        # Filter out empty sentences and strip whitespace
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
