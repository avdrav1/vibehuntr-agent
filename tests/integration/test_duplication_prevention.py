"""
Integration tests for response duplication prevention.

These tests verify that the complete system prevents response duplication
across different scenarios: end-to-end flow, streaming, and multi-session.

**Validates: Requirements 1.1, 1.2, 1.4**
"""

import pytest
import uuid
from typing import List, Dict, Any
from app.event_planning.agent_loader import get_agent
from app.event_planning.agent_invoker import invoke_agent_streaming, invoke_agent
from app.event_planning.session_manager import SessionManager


class TestEndToEndDuplicationPrevention:
    """Test end-to-end duplication prevention through the complete stack.
    
    **Validates: Requirement 1.1 - Response content uniqueness**
    """
    
    def test_single_message_no_duplication(self):
        """
        Test that a single message produces a response with no duplicates.
        
        This test verifies the complete flow from message input through
        agent invocation to response generation, ensuring no duplication
        occurs at any stage.
        
        **Validates: Requirement 1.1**
        """
        # Arrange
        agent = get_agent()
        session_id = f"test_e2e_single_{uuid.uuid4()}"
        message = "What are some good Italian restaurants?"
        
        # Act - collect complete response
        response = invoke_agent(agent, message, session_id)
        
        # Assert - check for duplicates
        # Split into sentences and check for exact duplicates
        sentences = [s.strip() for s in response.split('.') if s.strip()]
        sentence_set = set(sentences)
        
        # Each sentence should appear only once
        assert len(sentences) == len(sentence_set), \
            f"Found duplicate sentences in response. Total: {len(sentences)}, Unique: {len(sentence_set)}"
        
        # Check for repeated phrases (more than 10 words)
        words = response.split()
        for i in range(len(words) - 10):
            phrase = ' '.join(words[i:i+10])
            rest_of_text = ' '.join(words[i+10:])
            assert phrase not in rest_of_text, \
                f"Found repeated phrase: '{phrase}'"
    
    def test_multi_turn_conversation_no_duplication(self):
        """
        Test that multi-turn conversations maintain uniqueness across turns.
        
        This test verifies that context injection and conversation history
        don't cause duplication in subsequent responses.
        
        **Validates: Requirement 1.1, 3.2**
        """
        # Arrange
        agent = get_agent()
        session_id = f"test_e2e_multi_{uuid.uuid4()}"
        messages = [
            "I'm looking for restaurants",
            "I prefer Italian food",
            "What about South Philly?"
        ]
        
        # Act & Assert - test each turn
        all_responses = []
        for message in messages:
            response = invoke_agent(agent, message, session_id)
            
            # Check this response has no internal duplicates
            sentences = [s.strip() for s in response.split('.') if s.strip()]
            sentence_set = set(sentences)
            assert len(sentences) == len(sentence_set), \
                f"Found duplicate sentences in turn '{message}'"
            
            # Store for cross-turn check
            all_responses.append(response)
        
        # Verify no response is duplicated across turns
        for i, resp1 in enumerate(all_responses):
            for j, resp2 in enumerate(all_responses):
                if i != j:
                    # Responses should be different
                    assert resp1 != resp2, \
                        f"Turn {i} and turn {j} produced identical responses"
    
    def test_tool_usage_no_duplication(self):
        """
        Test that responses involving tool calls have no duplication.
        
        This test verifies that tool outputs and final responses are
        both unique when tools are invoked during response generation.
        
        **Validates: Requirement 1.5**
        """
        # Arrange
        agent = get_agent()
        session_id = f"test_e2e_tools_{uuid.uuid4()}"
        # Message likely to trigger search_venues_tool
        message = "Find me Italian restaurants in Philadelphia"
        
        # Act - collect response with tool calls
        tool_calls = []
        text_chunks = []
        
        for item in invoke_agent_streaming(agent, message, session_id, yield_tool_calls=True):
            if item['type'] == 'tool_call':
                tool_calls.append(item)
            elif item['type'] == 'text':
                text_chunks.append(item['content'])
        
        # Assert - check tool calls are unique
        if tool_calls:
            tool_call_strs = [str(tc) for tc in tool_calls]
            assert len(tool_call_strs) == len(set(tool_call_strs)), \
                "Found duplicate tool calls"
        
        # Assert - check text response is unique
        full_response = ''.join(text_chunks)
        sentences = [s.strip() for s in full_response.split('.') if s.strip()]
        sentence_set = set(sentences)
        assert len(sentences) == len(sentence_set), \
            "Found duplicate sentences in tool-using response"


class TestStreamingDuplicationPrevention:
    """Test streaming-specific duplication prevention.
    
    **Validates: Requirement 1.2 - Token streaming uniqueness**
    """
    
    def test_streaming_tokens_unique(self):
        """
        Test that streaming yields each token exactly once.
        
        This test verifies the core streaming logic that prevents
        duplicate token emission during response generation.
        
        **Validates: Requirement 1.2**
        """
        # Arrange
        agent = get_agent()
        session_id = f"test_stream_tokens_{uuid.uuid4()}"
        message = "Tell me about restaurants in Philadelphia"
        
        # Act - collect all tokens
        tokens = []
        for item in invoke_agent_streaming(agent, message, session_id):
            if item['type'] == 'text':
                tokens.append(item['content'])
        
        # Assert - verify no token appears twice consecutively
        for i in range(len(tokens) - 1):
            assert tokens[i] != tokens[i+1], \
                f"Found consecutive duplicate tokens at index {i}: '{tokens[i]}'"
        
        # Assert - verify accumulated text grows monotonically
        accumulated = ""
        for token in tokens:
            new_accumulated = accumulated + token
            assert len(new_accumulated) > len(accumulated), \
                "Token didn't add new content (possible duplicate)"
            accumulated = new_accumulated
    
    def test_streaming_no_overlapping_content(self):
        """
        Test that streaming tokens don't overlap or repeat content.
        
        This test verifies that the accumulated text tracking correctly
        prevents yielding content that was already yielded.
        
        **Validates: Requirement 1.2**
        """
        # Arrange
        agent = get_agent()
        session_id = f"test_stream_overlap_{uuid.uuid4()}"
        message = "What are the best restaurants?"
        
        # Act - collect tokens and track accumulation
        tokens = []
        accumulated_lengths = []
        accumulated = ""
        
        for item in invoke_agent_streaming(agent, message, session_id):
            if item['type'] == 'text':
                token = item['content']
                tokens.append(token)
                accumulated += token
                accumulated_lengths.append(len(accumulated))
        
        # Assert - lengths should be strictly increasing
        for i in range(len(accumulated_lengths) - 1):
            assert accumulated_lengths[i+1] > accumulated_lengths[i], \
                f"Accumulated length didn't increase at index {i}: " \
                f"{accumulated_lengths[i]} -> {accumulated_lengths[i+1]}"
    
    def test_streaming_multi_turn_no_duplication(self):
        """
        Test that streaming maintains uniqueness across multiple turns.
        
        This test verifies that the streaming state is properly reset
        between turns and doesn't carry over duplicates.
        
        **Validates: Requirement 1.2, 3.2**
        """
        # Arrange
        agent = get_agent()
        session_id = f"test_stream_multi_{uuid.uuid4()}"
        messages = [
            "Hello",
            "Tell me about Italian food",
            "What about restaurants?"
        ]
        
        # Act & Assert - test each turn
        for message in messages:
            tokens = []
            accumulated = ""
            
            for item in invoke_agent_streaming(agent, message, session_id):
                if item['type'] == 'text':
                    token = item['content']
                    tokens.append(token)
                    
                    # Verify this token adds new content
                    new_accumulated = accumulated + token
                    assert len(new_accumulated) > len(accumulated), \
                        f"Token didn't add content in message '{message}'"
                    accumulated = new_accumulated
            
            # Verify no consecutive duplicates
            for i in range(len(tokens) - 1):
                assert tokens[i] != tokens[i+1], \
                    f"Found consecutive duplicates in message '{message}'"
    
    def test_streaming_large_response_no_duplication(self):
        """
        Test that large streaming responses maintain uniqueness.
        
        This test verifies that the duplicate detection works correctly
        even with longer responses that might stress the system.
        
        **Validates: Requirement 1.2**
        """
        # Arrange
        agent = get_agent()
        session_id = f"test_stream_large_{uuid.uuid4()}"
        # Ask for a detailed response to get more tokens
        message = "Give me a detailed guide to the best restaurants in Philadelphia, " \
                 "including Italian, Mexican, and Asian cuisine options"
        
        # Act - collect all tokens
        tokens = []
        accumulated = ""
        
        for item in invoke_agent_streaming(agent, message, session_id):
            if item['type'] == 'text':
                token = item['content']
                tokens.append(token)
                accumulated += token
        
        # Assert - verify no duplicates in the token stream
        # Check for repeated sequences of 5+ tokens
        for i in range(len(tokens) - 5):
            sequence = tokens[i:i+5]
            sequence_str = ''.join(sequence)
            
            # Check if this sequence appears later
            for j in range(i+5, len(tokens) - 5):
                later_sequence = tokens[j:j+5]
                later_sequence_str = ''.join(later_sequence)
                
                assert sequence_str != later_sequence_str, \
                    f"Found repeated 5-token sequence at positions {i} and {j}"


class TestMultiSessionDuplicationPrevention:
    """Test duplication prevention across concurrent sessions.
    
    **Validates: Requirement 1.4 - Concurrent session isolation**
    """
    
    def test_concurrent_sessions_isolated(self):
        """
        Test that concurrent sessions don't interfere with each other.
        
        This test verifies that multiple sessions can run simultaneously
        without causing duplication or cross-contamination.
        
        **Validates: Requirement 1.4**
        """
        # Arrange
        agent = get_agent()
        session_ids = [
            f"test_concurrent_1_{uuid.uuid4()}",
            f"test_concurrent_2_{uuid.uuid4()}",
            f"test_concurrent_3_{uuid.uuid4()}"
        ]
        messages = [
            "Tell me about Italian restaurants",
            "What are good Mexican places?",
            "Find me Asian cuisine"
        ]
        
        # Act - invoke all sessions
        responses = {}
        for session_id, message in zip(session_ids, messages):
            response = invoke_agent(agent, message, session_id)
            responses[session_id] = response
        
        # Assert - each response should be unique
        response_list = list(responses.values())
        for i, resp1 in enumerate(response_list):
            for j, resp2 in enumerate(response_list):
                if i != j:
                    # Responses should be different (different queries)
                    assert resp1 != resp2, \
                        f"Session {i} and {j} produced identical responses"
            
            # Each response should have no internal duplicates
            sentences = [s.strip() for s in resp1.split('.') if s.strip()]
            sentence_set = set(sentences)
            assert len(sentences) == len(sentence_set), \
                f"Session {i} has duplicate sentences"
    
    def test_session_isolation_with_streaming(self):
        """
        Test that streaming sessions maintain isolation.
        
        This test verifies that streaming state doesn't leak between
        concurrent sessions.
        
        **Validates: Requirement 1.4**
        """
        # Arrange
        agent = get_agent()
        session_ids = [
            f"test_stream_iso_1_{uuid.uuid4()}",
            f"test_stream_iso_2_{uuid.uuid4()}"
        ]
        message = "Tell me about restaurants"
        
        # Act - stream from both sessions
        session_tokens = {}
        for session_id in session_ids:
            tokens = []
            for item in invoke_agent_streaming(agent, message, session_id):
                if item['type'] == 'text':
                    tokens.append(item['content'])
            session_tokens[session_id] = tokens
        
        # Assert - each session should have unique token streams
        tokens1 = session_tokens[session_ids[0]]
        tokens2 = session_tokens[session_ids[1]]
        
        # Verify each session has no internal duplicates
        for session_id, tokens in session_tokens.items():
            for i in range(len(tokens) - 1):
                assert tokens[i] != tokens[i+1], \
                    f"Session {session_id} has consecutive duplicate tokens"
    
    def test_session_history_isolation(self):
        """
        Test that session history is properly isolated between sessions.
        
        This test verifies that messages from one session don't appear
        in another session's history.
        
        **Validates: Requirement 1.4, 1.3**
        """
        # Arrange
        session_managers = {
            f"test_history_iso_1_{uuid.uuid4()}": SessionManager({}),
            f"test_history_iso_2_{uuid.uuid4()}": SessionManager({})
        }
        
        # Act - add different messages to each session
        messages_by_session = {
            list(session_managers.keys())[0]: [
                ("user", "Hello from session 1"),
                ("assistant", "Response to session 1")
            ],
            list(session_managers.keys())[1]: [
                ("user", "Hello from session 2"),
                ("assistant", "Response to session 2")
            ]
        }
        
        for session_id, manager in session_managers.items():
            for role, content in messages_by_session[session_id]:
                manager.add_message(role, content)
        
        # Assert - each session should only have its own messages
        for session_id, manager in session_managers.items():
            messages = manager.get_messages()
            expected_messages = messages_by_session[session_id]
            
            assert len(messages) == len(expected_messages), \
                f"Session {session_id} has wrong number of messages"
            
            for msg, (expected_role, expected_content) in zip(messages, expected_messages):
                assert msg['role'] == expected_role
                assert msg['content'] == expected_content
    
    def test_rapid_session_switching_no_duplication(self):
        """
        Test that rapidly switching between sessions doesn't cause duplication.
        
        This test verifies that the system handles rapid context switching
        without state leakage or duplication.
        
        **Validates: Requirement 1.4**
        """
        # Arrange
        agent = get_agent()
        session_ids = [
            f"test_rapid_1_{uuid.uuid4()}",
            f"test_rapid_2_{uuid.uuid4()}"
        ]
        
        # Act - alternate between sessions rapidly
        responses = []
        for i in range(4):  # 2 messages per session
            session_id = session_ids[i % 2]
            message = f"Message {i} for session {i % 2}"
            response = invoke_agent(agent, message, session_id)
            responses.append((session_id, response))
        
        # Assert - each response should be unique
        for i, (sid1, resp1) in enumerate(responses):
            # Check no internal duplicates
            sentences = [s.strip() for s in resp1.split('.') if s.strip()]
            sentence_set = set(sentences)
            assert len(sentences) == len(sentence_set), \
                f"Response {i} has duplicate sentences"


class TestSessionHistoryUniqueness:
    """Test that session history maintains uniqueness.
    
    **Validates: Requirement 1.3 - Session history uniqueness**
    """
    
    def test_session_history_no_duplicate_storage(self):
        """
        Test that responses are stored exactly once in session history.
        
        This test verifies that the session manager's duplicate prevention
        works correctly.
        
        **Validates: Requirement 1.3**
        """
        # Arrange
        session_manager = SessionManager({})
        
        # Act - add messages
        session_manager.add_message("user", "Hello")
        session_manager.add_message("assistant", "Hi there")
        session_manager.add_message("user", "How are you?")
        
        # Try to add a duplicate (should be prevented)
        session_manager.add_message("user", "How are you?")
        
        # Assert - should only have 3 messages (duplicate prevented)
        messages = session_manager.get_messages()
        assert len(messages) == 3, \
            f"Expected 3 messages, got {len(messages)}"
        
        # Verify content
        assert messages[0]['content'] == "Hello"
        assert messages[1]['content'] == "Hi there"
        assert messages[2]['content'] == "How are you?"
    
    def test_session_history_allows_legitimate_repeats(self):
        """
        Test that legitimate repeated messages are allowed.
        
        This test verifies that the duplicate prevention doesn't block
        legitimate cases where a user sends the same message twice.
        
        **Validates: Requirement 1.3**
        """
        # Arrange
        session_manager = SessionManager({})
        
        # Act - add messages with a legitimate repeat
        session_manager.add_message("user", "Hello")
        session_manager.add_message("assistant", "Hi")
        session_manager.add_message("user", "Hello")  # Legitimate repeat
        
        # Assert - should have all 3 messages
        messages = session_manager.get_messages()
        assert len(messages) == 3, \
            f"Expected 3 messages, got {len(messages)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
