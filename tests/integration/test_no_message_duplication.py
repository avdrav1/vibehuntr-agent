"""
Regression test for message duplication bug.

This test ensures that streaming responses don't contain duplicate content.
The bug occurs when the agent_invoker yields accumulated text instead of
only new tokens.

Bug History:
- Original fix: Check if text starts with accumulated_text and only yield new content
- Regression: Bug reappeared after code changes
"""

import pytest
from app.event_planning.agent_loader import get_agent
from app.event_planning.agent_invoker import invoke_agent_streaming


def test_no_duplicate_tokens_in_stream():
    """
    Test that streaming doesn't produce duplicate tokens.
    
    This is a regression test for the duplication bug where the same
    content would appear multiple times in the streamed response.
    
    **Validates: No duplicate content in streaming responses**
    """
    agent = get_agent()
    session_id = "test_no_duplication"
    message = "Hello, can you help me find a restaurant?"
    
    # Collect all tokens
    tokens = []
    for item in invoke_agent_streaming(agent, message, session_id):
        if item['type'] == 'text':
            tokens.append(item['content'])
    
    # Reconstruct the full response
    full_response = ''.join(tokens)
    
    # Check for obvious duplications
    # Split into sentences and check if any sentence appears twice
    sentences = [s.strip() for s in full_response.split('.') if s.strip()]
    
    # Count occurrences of each sentence
    sentence_counts = {}
    for sentence in sentences:
        sentence_counts[sentence] = sentence_counts.get(sentence, 0) + 1
    
    # Find duplicates
    duplicates = {s: count for s, count in sentence_counts.items() if count > 1}
    
    # Assert no duplicates
    assert len(duplicates) == 0, f"Found duplicate sentences: {duplicates}"
    
    # Additional check: ensure tokens don't overlap
    # Each token should be unique or at least not repeat consecutively
    for i in range(len(tokens) - 1):
        if len(tokens[i]) > 10:  # Only check substantial tokens
            # Check if next token starts with current token (overlap)
            assert not tokens[i+1].startswith(tokens[i]), \
                f"Token overlap detected: '{tokens[i]}' followed by '{tokens[i+1]}'"


def test_accumulated_text_tracking():
    """
    Test that accumulated text is properly tracked to avoid duplicates.
    
    This test verifies the core fix: only yield new content, not accumulated content.
    
    **Validates: Proper accumulated text tracking in streaming**
    """
    agent = get_agent()
    session_id = "test_accumulation"
    message = "Tell me about Indian restaurants"
    
    accumulated = ""
    previous_length = 0
    
    for item in invoke_agent_streaming(agent, message, session_id):
        if item['type'] == 'text':
            token = item['content']
            accumulated += token
            
            # Each token should add to the length
            new_length = len(accumulated)
            assert new_length > previous_length, \
                "Token didn't add new content (possible duplicate)"
            
            previous_length = new_length


def test_multiple_messages_no_duplication():
    """
    Test that multiple messages in a session don't cause duplication.
    
    **Validates: No duplication across multiple messages in same session**
    """
    agent = get_agent()
    session_id = "test_multi_message"
    
    messages = [
        "Hello",
        "Can you help me find a restaurant?",
        "I'm looking for Indian food",
    ]
    
    for message in messages:
        tokens = []
        for item in invoke_agent_streaming(agent, message, session_id):
            if item['type'] == 'text':
                tokens.append(item['content'])
        
        full_response = ''.join(tokens)
        
        # Check for duplicates in this response
        sentences = [s.strip() for s in full_response.split('.') if s.strip()]
        sentence_counts = {}
        for sentence in sentences:
            sentence_counts[sentence] = sentence_counts.get(sentence, 0) + 1
        
        duplicates = {s: count for s, count in sentence_counts.items() if count > 1}
        assert len(duplicates) == 0, \
            f"Found duplicates in message '{message}': {duplicates}"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
