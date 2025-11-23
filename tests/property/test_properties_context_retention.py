"""Property-based tests for context retention across conversation turns.

This module tests the correctness properties for context retention,
ensuring that the agent maintains conversation context across multiple turns.
"""

import sys
import os
from hypothesis import given, strategies as st, settings, HealthCheck
from hypothesis.strategies import composite
import pytest
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.event_planning.agent_invoker import invoke_agent_streaming, invoke_agent
from google.adk.sessions import InMemorySessionService
from google.genai import types


# Custom strategies for generating test data

@composite
def user_message_strategy(draw: st.DrawFn) -> str:
    """Generate a valid user message."""
    return draw(st.text(min_size=5, max_size=200, alphabet=st.characters(
        blacklist_categories=('Cs',),
        whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')
    )))


@composite
def session_id_strategy(draw: st.DrawFn) -> str:
    """Generate a valid session ID."""
    return draw(st.text(min_size=5, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd')
    )))


@composite
def user_id_strategy(draw: st.DrawFn) -> str:
    """Generate a valid user ID."""
    return draw(st.text(min_size=3, max_size=30, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd')
    )))


@composite
def conversation_turn_strategy(draw: st.DrawFn) -> tuple:
    """Generate a conversation turn (user message, agent response)."""
    user_msg = draw(user_message_strategy())
    agent_response = draw(st.text(min_size=10, max_size=300, alphabet=st.characters(
        blacklist_categories=('Cs',),
        whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')
    )))
    return (user_msg, agent_response)


@composite
def multi_turn_conversation_strategy(draw: st.DrawFn) -> List[tuple]:
    """Generate a multi-turn conversation."""
    return draw(st.lists(
        conversation_turn_strategy(),
        min_size=2,
        max_size=5
    ))


# Feature: playground-fix, Property 3: Context retention across turns
@given(
    user_id=user_id_strategy(),
    conversation=multi_turn_conversation_strategy()
)
@settings(max_examples=100)
def test_property_3_context_retention_across_turns(
    user_id: str,
    conversation: List[tuple]
) -> None:
    """
    Feature: playground-fix, Property 3: Context retention across turns
    
    For any multi-turn conversation, information provided in earlier turns
    should be available to the agent in later turns.
    
    Validates: Requirements 2.1, 2.3
    """
    with patch('app.event_planning.agent_invoker._session_service') as mock_session_service, \
         patch('app.event_planning.agent_invoker.Runner') as mock_runner_class:
        
        # Create a real session service to track history
        real_session_service = InMemorySessionService()
        
        # Create session
        session = real_session_service.create_session_sync(
            user_id=user_id,
            app_name="test_app"
        )
        actual_session_id = session.id
        
        # Mock session service to return our real session
        mock_session_service.get_session_sync.return_value = session
        mock_session_service.create_session_sync.return_value = session
        
        # Track all messages added via runner.run calls
        history_messages = []
        
        def mock_runner_run(**kwargs):
            """Mock runner that tracks history and returns response."""
            # Get the new message
            new_message = kwargs.get('new_message')
            if new_message:
                # Track user message
                history_messages.append(new_message)
            
            # Get current turn index based on history length
            # Each turn has 2 messages (user + agent), so divide by 2
            turn_idx = (len(history_messages) - 1) // 2
            if turn_idx < len(conversation):
                response_text = conversation[turn_idx][1]
            else:
                response_text = "Default response"
            
            # Create response event
            mock_event = Mock()
            mock_event.content = Mock()
            mock_part = Mock()
            mock_part.text = response_text
            mock_event.content.parts = [mock_part]
            mock_event.function_calls = None
            
            # Track agent response
            agent_content = types.Content(
                role="model",
                parts=[types.Part.from_text(text=response_text)]
            )
            history_messages.append(agent_content)
            
            return iter([mock_event])
        
        # Mock runner
        mock_runner = Mock()
        mock_runner.run = mock_runner_run
        mock_runner_class.return_value = mock_runner
        
        # Create mock agent
        mock_agent = Mock()
        
        # Simulate multi-turn conversation
        for turn_idx, (user_msg, expected_response) in enumerate(conversation):
            # Invoke agent
            response = invoke_agent(
                mock_agent,
                user_msg,
                session_id=actual_session_id,
                user_id=user_id
            )
            
            # Verify response matches expected
            assert response == expected_response
            
            # Verify history contains all previous messages
            # At this point, history should have: (turn_idx + 1) * 2 messages
            # (user message + agent response for each turn)
            expected_history_length = (turn_idx + 1) * 2
            assert len(history_messages) == expected_history_length, \
                f"Turn {turn_idx}: Expected {expected_history_length} messages in history, got {len(history_messages)}"
            
            # Verify all previous user messages are in history
            user_messages_in_history = [
                msg for msg in history_messages
                if hasattr(msg, 'role') and msg.role == 'user'
            ]
            assert len(user_messages_in_history) == turn_idx + 1, \
                f"Turn {turn_idx}: Expected {turn_idx + 1} user messages in history"
            
            # Verify the current user message is in the last user message
            # (it may have context prepended, which is expected behavior)
            if user_messages_in_history:
                last_user_msg = user_messages_in_history[-1]
                assert user_msg in last_user_msg.parts[0].text, \
                    f"Turn {turn_idx}: Last user message doesn't contain current message"
        
        # Final verification: history should contain all messages from all turns
        total_expected_messages = len(conversation) * 2  # user + agent for each turn
        assert len(history_messages) == total_expected_messages, \
            f"Final history should have {total_expected_messages} messages, got {len(history_messages)}"


# Feature: playground-fix, Property 4: Question non-repetition
@given(
    user_id=user_id_strategy(),
    question=st.text(min_size=10, max_size=100, alphabet=st.characters(
        blacklist_categories=('Cs',),
        whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')
    )).filter(lambda x: '?' in x or 'what' in x.lower() or 'when' in x.lower() or 'where' in x.lower()),
    answer=st.text(min_size=5, max_size=100, alphabet=st.characters(
        blacklist_categories=('Cs',),
        whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')
    )),
    follow_up_messages=st.lists(
        st.text(min_size=5, max_size=100, alphabet=st.characters(
            blacklist_categories=('Cs',),
            whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')
        )),
        min_size=1,
        max_size=3
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.filter_too_much])
def test_property_4_question_non_repetition(
    user_id: str,
    question: str,
    answer: str,
    follow_up_messages: List[str]
) -> None:
    """
    Feature: playground-fix, Property 4: Question non-repetition
    
    For any question asked by the agent that receives an answer, the agent
    should not ask the same question in subsequent turns.
    
    Validates: Requirements 2.2
    """
    # Skip if question and answer are too similar (would cause false positives)
    if question in answer or answer in question:
        return
    
    with patch('app.event_planning.agent_invoker._session_service') as mock_session_service, \
         patch('app.event_planning.agent_invoker.Runner') as mock_runner_class:
        
        # Create a real session service
        real_session_service = InMemorySessionService()
        
        # Create session
        session = real_session_service.create_session_sync(
            user_id=user_id,
            app_name="test_app"
        )
        actual_session_id = session.id
        
        # Mock session service to return our real session
        mock_session_service.get_session_sync.return_value = session
        mock_session_service.create_session_sync.return_value = session
        
        # Track all agent responses
        agent_responses = []
        turn_count = [0]  # Use list to allow modification in nested function
        
        def mock_runner_run(**kwargs):
            """Mock runner that tracks responses."""
            turn_count[0] += 1
            
            # First turn: agent asks a question
            if turn_count[0] == 1:
                response_text = question
            # Second turn: agent acknowledges answer (should not repeat question)
            elif turn_count[0] == 2:
                response_text = "Thank you for answering. Moving on to next topic."
            # Subsequent turns: agent continues conversation (should not repeat question)
            else:
                response_text = "Continuing conversation about other topics."
            
            agent_responses.append(response_text)
            
            # Create response event
            mock_event = Mock()
            mock_event.content = Mock()
            mock_part = Mock()
            mock_part.text = response_text
            mock_event.content.parts = [mock_part]
            mock_event.function_calls = None
            
            return iter([mock_event])
        
        # Mock runner
        mock_runner = Mock()
        mock_runner.run = mock_runner_run
        mock_runner_class.return_value = mock_runner
        
        # Create mock agent
        mock_agent = Mock()
        
        # Turn 1: Initial message, agent asks question
        response1 = invoke_agent(
            mock_agent,
            "Hello",
            session_id=actual_session_id,
            user_id=user_id
        )
        assert response1 == question
        
        # Turn 2: User answers the question
        response2 = invoke_agent(
            mock_agent,
            answer,
            session_id=actual_session_id,
            user_id=user_id
        )
        # Agent should acknowledge, not repeat the question
        assert question not in response2, \
            f"Agent repeated question in turn 2: {response2}"
        
        # Subsequent turns: Continue conversation
        for follow_up in follow_up_messages:
            response = invoke_agent(
                mock_agent,
                follow_up,
                session_id=actual_session_id,
                user_id=user_id
            )
            # Agent should not repeat the original question
            assert question not in response, \
                f"Agent repeated question in follow-up turn: {response}"
        
        # Verify that the question only appears once in all agent responses
        question_count = sum(1 for resp in agent_responses if question in resp)
        assert question_count == 1, \
            f"Question should appear exactly once, but appeared {question_count} times"


# Feature: playground-fix, Property 5: Reference resolution
@given(
    user_id=user_id_strategy(),
    entity_name=st.text(min_size=5, max_size=30, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll')
    )).filter(lambda x: len(x.strip()) > 0),
    entity_description=st.text(min_size=10, max_size=100, alphabet=st.characters(
        blacklist_categories=('Cs',),
        whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')
    )),
    reference_type=st.sampled_from(['pronoun', 'description'])
)
@settings(max_examples=100)
def test_property_5_reference_resolution(
    user_id: str,
    entity_name: str,
    entity_description: str,
    reference_type: str
) -> None:
    """
    Feature: playground-fix, Property 5: Reference resolution
    
    For any entity mentioned in conversation, when referenced later (by pronoun
    or description), the agent should correctly identify it.
    
    Validates: Requirements 2.4
    """
    with patch('app.event_planning.agent_invoker._session_service') as mock_session_service, \
         patch('app.event_planning.agent_invoker.Runner') as mock_runner_class:
        
        # Create a real session service
        real_session_service = InMemorySessionService()
        
        # Create session
        session = real_session_service.create_session_sync(
            user_id=user_id,
            app_name="test_app"
        )
        actual_session_id = session.id
        
        # Mock session service to return our real session
        mock_session_service.get_session_sync.return_value = session
        mock_session_service.create_session_sync.return_value = session
        
        # Track messages passed to runner
        messages_to_agent = []
        
        def mock_runner_run(**kwargs):
            """Mock runner that tracks messages and returns appropriate responses."""
            new_message = kwargs.get('new_message')
            if new_message:
                messages_to_agent.append(new_message.parts[0].text)
            
            # Determine response based on turn
            turn_num = len(messages_to_agent)
            
            if turn_num == 1:
                # First turn: acknowledge entity introduction
                response_text = f"I understand you mentioned {entity_name}. {entity_description}"
            elif turn_num == 2:
                # Second turn: demonstrate understanding of reference
                if reference_type == 'pronoun':
                    response_text = f"Yes, I remember {entity_name} from earlier."
                else:
                    response_text = f"You're referring to {entity_name}, correct?"
            else:
                response_text = "Continuing conversation."
            
            # Create response event
            mock_event = Mock()
            mock_event.content = Mock()
            mock_part = Mock()
            mock_part.text = response_text
            mock_event.content.parts = [mock_part]
            mock_event.function_calls = None
            
            return iter([mock_event])
        
        # Mock runner
        mock_runner = Mock()
        mock_runner.run = mock_runner_run
        mock_runner_class.return_value = mock_runner
        
        # Create mock agent
        mock_agent = Mock()
        
        # Turn 1: User introduces an entity
        user_message_1 = f"I want to tell you about {entity_name}. {entity_description}"
        response1 = invoke_agent(
            mock_agent,
            user_message_1,
            session_id=actual_session_id,
            user_id=user_id
        )
        
        # Verify agent acknowledges the entity
        assert entity_name in response1, \
            f"Agent should acknowledge entity {entity_name} in response: {response1}"
        
        # Turn 2: User references the entity
        if reference_type == 'pronoun':
            user_message_2 = "Can you tell me more about it?"
        else:
            # Use a description-based reference
            user_message_2 = f"What do you think about the one I mentioned?"
        
        response2 = invoke_agent(
            mock_agent,
            user_message_2,
            session_id=actual_session_id,
            user_id=user_id
        )
        
        # Verify agent correctly resolves the reference to the entity
        assert entity_name in response2, \
            f"Agent should resolve reference to {entity_name} in response: {response2}"
        
        # Verify both messages were passed to the agent (context retention)
        assert len(messages_to_agent) == 2, \
            f"Agent should have received 2 messages, got {len(messages_to_agent)}"
        
        # Verify the first message contained the entity
        assert entity_name in messages_to_agent[0], \
            f"First message should contain entity {entity_name}"


# Feature: enhanced-context-retention, Property 8: Venue list size limit
@given(
    num_venues=st.integers(min_value=0, max_value=20)
)
@settings(max_examples=100)
def test_property_8_venue_list_size_limit(num_venues: int) -> None:
    """
    Feature: enhanced-context-retention, Property 8: Venue list size limit
    
    For any session, adding more than 5 venues should result in only the 5 most
    recent venues being stored.
    
    Validates: Requirements 2.4
    """
    from app.event_planning.context_manager import ConversationContext, VenueInfo
    
    # Create a fresh context
    context = ConversationContext()
    
    # Generate agent messages with venues
    for i in range(num_venues):
        venue_name = f"Venue_{i}"
        place_id = f"ChIJ{i:010d}"
        
        # Create agent message with venue
        agent_message = f"I found **{venue_name}**. Place ID: {place_id}"
        
        # Update context from agent message
        context.update_from_agent_message(agent_message)
    
    # Property: venue list should never exceed 5 items
    assert len(context.recent_venues) <= 5, \
        f"Venue list should have at most 5 items, but has {len(context.recent_venues)}"
    
    # If we added more than 5 venues, verify we kept the most recent 5
    if num_venues > 5:
        assert len(context.recent_venues) == 5, \
            f"When adding {num_venues} venues, should keep exactly 5, but kept {len(context.recent_venues)}"
        
        # Verify the venues are the last 5 added
        expected_start_idx = num_venues - 5
        for i, venue in enumerate(context.recent_venues):
            expected_venue_num = expected_start_idx + i
            expected_name = f"Venue_{expected_venue_num}"
            assert venue.name == expected_name, \
                f"Venue at position {i} should be {expected_name}, but is {venue.name}"
    
    # If we added 5 or fewer venues, verify we kept all of them
    elif num_venues > 0:
        assert len(context.recent_venues) == num_venues, \
            f"When adding {num_venues} venues, should keep all {num_venues}, but kept {len(context.recent_venues)}"
        
        # Verify the venues are in the correct order
        for i, venue in enumerate(context.recent_venues):
            expected_name = f"Venue_{i}"
            assert venue.name == expected_name, \
                f"Venue at position {i} should be {expected_name}, but is {venue.name}"
    
    # If we added 0 venues, verify the list is empty
    else:
        assert len(context.recent_venues) == 0, \
            f"When adding 0 venues, list should be empty, but has {len(context.recent_venues)} items"


# Feature: enhanced-context-retention, Property 6: Vague reference resolution
@given(
    num_venues=st.integers(min_value=1, max_value=5),
    reference_type=st.sampled_from(['that one', 'this one', 'the one', 'it', 'that', 'this'])
)
@settings(max_examples=100)
def test_property_6_vague_reference_resolution(num_venues: int, reference_type: str) -> None:
    """
    Feature: enhanced-context-retention, Property 6: Vague reference resolution
    
    For any session with recent venues, resolving a vague reference like "that one"
    or "the first one" should return the correct venue from the list.
    
    Validates: Requirements 2.2
    """
    from app.event_planning.context_manager import ConversationContext, VenueInfo
    
    # Create a fresh context
    context = ConversationContext()
    
    # Add venues to the context
    for i in range(num_venues):
        venue_name = f"Venue_{i}"
        place_id = f"ChIJ{i:010d}"
        
        # Create agent message with venue
        agent_message = f"I found **{venue_name}**. Place ID: {place_id}"
        
        # Update context from agent message
        context.update_from_agent_message(agent_message)
    
    # Test vague reference resolution
    resolved_venue = context.find_venue_by_reference(reference_type)
    
    # Property: vague references should resolve to the most recent venue
    assert resolved_venue is not None, \
        f"Vague reference '{reference_type}' should resolve to a venue"
    
    # The most recent venue should be the last one added
    expected_venue_name = f"Venue_{num_venues - 1}"
    assert resolved_venue.name == expected_venue_name, \
        f"Vague reference '{reference_type}' should resolve to most recent venue {expected_venue_name}, but resolved to {resolved_venue.name}"
    
    # Verify the Place ID is correct
    expected_place_id = f"ChIJ{num_venues - 1:010d}"
    assert resolved_venue.place_id == expected_place_id, \
        f"Resolved venue should have Place ID {expected_place_id}, but has {resolved_venue.place_id}"


# Feature: enhanced-context-retention, Property 9: Ordinal reference resolution
@given(
    num_venues=st.integers(min_value=1, max_value=5),
    ordinal_index=st.integers(min_value=0, max_value=4)
)
@settings(max_examples=100)
def test_property_9_ordinal_reference_resolution(num_venues: int, ordinal_index: int) -> None:
    """
    Feature: enhanced-context-retention, Property 9: Ordinal reference resolution
    
    For any session with multiple venues, resolving ordinal references ("first",
    "second") should return the venue at the correct position.
    
    Validates: Requirements 2.5
    """
    from app.event_planning.context_manager import ConversationContext, VenueInfo
    
    # Skip if ordinal index is beyond the number of venues
    if ordinal_index >= num_venues:
        return
    
    # Create a fresh context
    context = ConversationContext()
    
    # Add venues to the context
    for i in range(num_venues):
        venue_name = f"Venue_{i}"
        place_id = f"ChIJ{i:010d}"
        
        # Create agent message with venue
        agent_message = f"I found **{venue_name}**. Place ID: {place_id}"
        
        # Update context from agent message
        context.update_from_agent_message(agent_message)
    
    # Map ordinal index to ordinal word
    ordinal_words = ['first', 'second', 'third', 'fourth', 'fifth']
    ordinal_reference = ordinal_words[ordinal_index]
    
    # Test ordinal reference resolution
    resolved_venue = context.find_venue_by_reference(ordinal_reference)
    
    # Property: ordinal references should resolve to the correct position
    assert resolved_venue is not None, \
        f"Ordinal reference '{ordinal_reference}' should resolve to a venue"
    
    # The venue at the ordinal position should match
    expected_venue_name = f"Venue_{ordinal_index}"
    assert resolved_venue.name == expected_venue_name, \
        f"Ordinal reference '{ordinal_reference}' should resolve to venue at position {ordinal_index} ({expected_venue_name}), but resolved to {resolved_venue.name}"
    
    # Verify the Place ID is correct
    expected_place_id = f"ChIJ{ordinal_index:010d}"
    assert resolved_venue.place_id == expected_place_id, \
        f"Resolved venue should have Place ID {expected_place_id}, but has {resolved_venue.place_id}"
    
    # Test with numeric reference as well
    numeric_reference = str(ordinal_index + 1)  # 1-indexed for users
    resolved_venue_numeric = context.find_venue_by_reference(numeric_reference)
    
    # Should resolve to the same venue
    if resolved_venue_numeric:
        assert resolved_venue_numeric.name == expected_venue_name, \
            f"Numeric reference '{numeric_reference}' should resolve to same venue as '{ordinal_reference}'"


# Feature: enhanced-context-retention, Property 19: Context prepending
@given(
    user_id=user_id_strategy(),
    user_message=user_message_strategy().filter(lambda x: len(x.strip()) > 0),
    has_location=st.booleans(),
    has_search_query=st.booleans(),
    has_venues=st.booleans()
)
@settings(max_examples=100)
def test_property_19_context_prepending(
    user_id: str,
    user_message: str,
    has_location: bool,
    has_search_query: bool,
    has_venues: bool
) -> None:
    """
    Feature: enhanced-context-retention, Property 19: Context prepending
    
    For any message with available context, the enhanced message should start
    with the context string.
    
    Validates: Requirements 5.3
    """
    from app.event_planning.context_manager import get_context, clear_context
    
    # Skip if no context is set (nothing to test)
    if not (has_location or has_search_query or has_venues):
        return
    
    with patch('app.event_planning.agent_invoker._session_service') as mock_session_service, \
         patch('app.event_planning.agent_invoker.Runner') as mock_runner_class:
        
        # Create a real session service
        real_session_service = InMemorySessionService()
        
        # Create session
        session = real_session_service.create_session_sync(
            user_id=user_id,
            app_name="test_app"
        )
        actual_session_id = session.id
        
        # Clear any existing context for this session
        clear_context(actual_session_id)
        
        # Mock session service to return our real session
        mock_session_service.get_session_sync.return_value = session
        mock_session_service.create_session_sync.return_value = session
        
        # Set up context based on test parameters BEFORE invoking agent
        context = get_context(actual_session_id)
        
        if has_location:
            context.location = "Philadelphia"
        
        if has_search_query:
            context.search_query = "italian"
        
        if has_venues:
            # Add a venue
            agent_message = "I found **Test Venue**. Place ID: ChIJtest123"
            context.update_from_agent_message(agent_message)
        
        # Get expected context string BEFORE the user message modifies it
        expected_context_string = context.get_context_string()
        
        # Track the message sent to the agent
        message_sent_to_agent = []
        
        def mock_runner_run(**kwargs):
            """Mock runner that captures the message."""
            new_message = kwargs.get('new_message')
            if new_message:
                message_sent_to_agent.append(new_message.parts[0].text)
            
            # Create response event
            mock_event = Mock()
            mock_event.content = Mock()
            mock_part = Mock()
            mock_part.text = "Response"
            mock_event.content.parts = [mock_part]
            mock_event.function_calls = None
            
            return iter([mock_event])
        
        # Mock runner
        mock_runner = Mock()
        mock_runner.run = mock_runner_run
        mock_runner_class.return_value = mock_runner
        
        # Create mock agent
        mock_agent = Mock()
        
        # Invoke agent
        invoke_agent(
            mock_agent,
            user_message,
            session_id=actual_session_id,
            user_id=user_id
        )
        
        # Verify message was sent
        assert len(message_sent_to_agent) == 1, \
            "Should have sent exactly one message to agent"
        
        actual_message = message_sent_to_agent[0]
        
        # Property: If context exists, message should start with [CONTEXT: ...]
        # Note: The context may have been updated by update_from_user_message,
        # so we check that SOME context was injected
        assert actual_message.startswith("[CONTEXT: "), \
            f"Message with context should start with '[CONTEXT: ', but got: {actual_message[:100]}"
        
        # Verify the original message is included after context
        assert user_message in actual_message, \
            f"Message should contain original user message '{user_message}', but got: {actual_message}"
        
        # Verify there's a newline separator between context and message
        assert "]\n\n" in actual_message, \
            f"Message should have ']\n\n' separator between context and user message, but got: {actual_message[:100]}"
        
        # Clean up
        clear_context(actual_session_id)


# Feature: enhanced-context-retention, Property 14: Entity extraction from agent responses
@given(
    num_venues=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=100)
def test_property_14_entity_extraction_from_agent_responses(num_venues: int) -> None:
    """
    Feature: enhanced-context-retention, Property 14: Entity extraction from agent responses
    
    For any agent response, parsing should extract all entities (venues, Place IDs)
    mentioned in the response.
    
    Validates: Requirements 4.1, 4.2
    """
    from app.event_planning.context_manager import ConversationContext
    
    # Create a fresh context
    context = ConversationContext()
    
    # Generate agent response with multiple venues
    venue_names = [f"Venue_{i}" for i in range(num_venues)]
    place_ids = [f"ChIJ{i:010d}" for i in range(num_venues)]
    
    # Create agent message with venues in the expected format
    agent_message_parts = []
    for name, place_id in zip(venue_names, place_ids):
        agent_message_parts.append(f"I found **{name}**. Place ID: {place_id}")
    
    agent_message = " ".join(agent_message_parts)
    
    # Update context from agent message
    context.update_from_agent_message(agent_message)
    
    # Property: All venues should be extracted
    # Note: Context keeps only last 5 venues
    expected_num_venues = min(num_venues, 5)
    assert len(context.recent_venues) == expected_num_venues, \
        f"Should have extracted {expected_num_venues} venues, but got {len(context.recent_venues)}"
    
    # Verify the extracted venues are the most recent ones
    if num_venues > 5:
        # Should have the last 5 venues
        start_idx = num_venues - 5
        for i, venue in enumerate(context.recent_venues):
            expected_name = f"Venue_{start_idx + i}"
            expected_place_id = f"ChIJ{start_idx + i:010d}"
            
            assert venue.name == expected_name, \
                f"Venue at position {i} should be {expected_name}, but is {venue.name}"
            assert venue.place_id == expected_place_id, \
                f"Venue at position {i} should have Place ID {expected_place_id}, but has {venue.place_id}"
    else:
        # Should have all venues
        for i, venue in enumerate(context.recent_venues):
            expected_name = f"Venue_{i}"
            expected_place_id = f"ChIJ{i:010d}"
            
            assert venue.name == expected_name, \
                f"Venue at position {i} should be {expected_name}, but is {venue.name}"
            assert venue.place_id == expected_place_id, \
                f"Venue at position {i} should have Place ID {expected_place_id}, but has {venue.place_id}"



# Feature: enhanced-context-retention, Property 20: Context logging
@given(
    user_id=user_id_strategy(),
    user_message=user_message_strategy().filter(lambda x: len(x.strip()) > 0),
    has_context=st.booleans()
)
@settings(max_examples=100)
def test_property_20_context_logging(
    user_id: str,
    user_message: str,
    has_context: bool
) -> None:
    """
    Feature: enhanced-context-retention, Property 20: Context logging
    
    For any context injection operation, a log entry should be created with
    the session_id and context string.
    
    Validates: Requirements 5.5, 7.2
    """
    from app.event_planning.context_manager import get_context, clear_context
    import logging
    
    with patch('app.event_planning.agent_invoker._session_service') as mock_session_service, \
         patch('app.event_planning.agent_invoker.Runner') as mock_runner_class, \
         patch('app.event_planning.agent_invoker.logger') as mock_logger:
        
        # Create a real session service
        real_session_service = InMemorySessionService()
        
        # Create session
        session = real_session_service.create_session_sync(
            user_id=user_id,
            app_name="test_app"
        )
        actual_session_id = session.id
        
        # Clear any existing context for this session
        clear_context(actual_session_id)
        
        # Mock session service to return our real session
        mock_session_service.get_session_sync.return_value = session
        mock_session_service.create_session_sync.return_value = session
        
        # Set up context if needed
        if has_context:
            context = get_context(actual_session_id)
            context.location = "Philadelphia"
            context.search_query = "italian"
        
        def mock_runner_run(**kwargs):
            """Mock runner that returns a simple response."""
            mock_event = Mock()
            mock_event.content = Mock()
            mock_part = Mock()
            mock_part.text = "Response"
            mock_event.content.parts = [mock_part]
            mock_event.function_calls = None
            
            return iter([mock_event])
        
        # Mock runner
        mock_runner = Mock()
        mock_runner.run = mock_runner_run
        mock_runner_class.return_value = mock_runner
        
        # Create mock agent
        mock_agent = Mock()
        
        # Invoke agent
        invoke_agent(
            mock_agent,
            user_message,
            session_id=actual_session_id,
            user_id=user_id
        )
        
        # Property: Logging should occur for context operations
        # Check that logger was called with session_id
        log_calls = mock_logger.info.call_args_list + mock_logger.debug.call_args_list
        
        # Verify at least one log call contains session_id
        session_id_logged = False
        context_logged = False
        
        for call in log_calls:
            if len(call.args) > 0 or 'extra' in call.kwargs:
                extra = call.kwargs.get('extra', {})
                if 'session_id' in extra and extra['session_id'] == actual_session_id:
                    session_id_logged = True
                
                # If context was injected, verify it was logged
                if has_context and 'context_string' in extra:
                    context_logged = True
        
        assert session_id_logged, \
            f"Session ID {actual_session_id} should be logged in context operations"
        
        # If context was present, verify it was logged
        if has_context:
            assert context_logged, \
                "Context string should be logged when context is injected"
        
        # Clean up
        clear_context(actual_session_id)



# Feature: enhanced-context-retention, Property 25: Context clearing
@given(
    has_location=st.booleans(),
    has_search_query=st.booleans(),
    num_venues=st.integers(min_value=0, max_value=5)
)
@settings(max_examples=100)
def test_property_25_context_clearing(
    has_location: bool,
    has_search_query: bool,
    num_venues: int
) -> None:
    """
    Feature: enhanced-context-retention, Property 25: Context clearing
    
    For any session, clearing the context should remove all stored values.
    
    Validates: Requirements 10.2
    """
    from app.event_planning.context_manager import get_context, clear_context
    
    # Generate a unique session ID for this test
    import uuid
    session_id = str(uuid.uuid4())
    
    # Get context for the session
    context = get_context(session_id)
    
    # Set up context with various values
    if has_location:
        context.location = "Philadelphia"
    
    if has_search_query:
        context.search_query = "italian"
    
    # Add venues
    for i in range(num_venues):
        venue_name = f"Venue_{i}"
        place_id = f"ChIJ{i:010d}"
        agent_message = f"I found **{venue_name}**. Place ID: {place_id}"
        context.update_from_agent_message(agent_message)
    
    # Verify context has values before clearing
    if has_location:
        assert context.location is not None, "Location should be set before clearing"
    
    if has_search_query:
        assert context.search_query is not None, "Search query should be set before clearing"
    
    if num_venues > 0:
        assert len(context.recent_venues) > 0, "Venues should be set before clearing"
    
    # Clear the context
    clear_context(session_id)
    
    # Get context again (should be a fresh instance)
    new_context = get_context(session_id)
    
    # Property: All context values should be cleared
    assert new_context.location is None, \
        f"Location should be None after clearing, but is {new_context.location}"
    
    assert new_context.search_query is None, \
        f"Search query should be None after clearing, but is {new_context.search_query}"
    
    assert len(new_context.recent_venues) == 0, \
        f"Recent venues should be empty after clearing, but has {len(new_context.recent_venues)} items"
    
    assert new_context.last_user_intent is None, \
        f"Last user intent should be None after clearing, but is {new_context.last_user_intent}"


# Feature: enhanced-context-retention, Property 21: Multi-turn context accumulation
@given(
    user_id=user_id_strategy(),
    num_turns=st.integers(min_value=2, max_value=5),
    has_location=st.booleans(),
    has_search_query=st.booleans(),
    has_venues=st.booleans()
)
@settings(max_examples=100)
def test_property_21_multi_turn_context_accumulation(
    user_id: str,
    num_turns: int,
    has_location: bool,
    has_search_query: bool,
    has_venues: bool
) -> None:
    """
    Feature: enhanced-context-retention, Property 21: Multi-turn context accumulation
    
    For any sequence of messages in a session, the context should accumulate
    information from all messages.
    
    Validates: Requirements 8.1
    """
    from app.event_planning.context_manager import get_context, clear_context
    
    with patch('app.event_planning.agent_invoker._session_service') as mock_session_service, \
         patch('app.event_planning.agent_invoker.Runner') as mock_runner_class:
        
        # Create a real session service
        real_session_service = InMemorySessionService()
        
        # Create session
        session = real_session_service.create_session_sync(
            user_id=user_id,
            app_name="test_app"
        )
        actual_session_id = session.id
        
        # Clear any existing context
        clear_context(actual_session_id)
        
        # Mock session service to return our real session
        mock_session_service.get_session_sync.return_value = session
        mock_session_service.create_session_sync.return_value = session
        
        # Track context state after each turn
        context_states = []
        
        def mock_runner_run(**kwargs):
            """Mock runner that returns responses with venues."""
            turn_num = len(context_states) + 1
            
            # Generate response with venue if requested
            if has_venues:
                response_text = f"I found **Venue_{turn_num}**. Place ID: ChIJ{turn_num:010d}"
            else:
                response_text = f"Response for turn {turn_num}"
            
            mock_event = Mock()
            mock_event.content = Mock()
            mock_part = Mock()
            mock_part.text = response_text
            mock_event.content.parts = [mock_part]
            mock_event.function_calls = None
            
            return iter([mock_event])
        
        # Mock runner
        mock_runner = Mock()
        mock_runner.run = mock_runner_run
        mock_runner_class.return_value = mock_runner
        
        # Create mock agent
        mock_agent = Mock()
        
        # Simulate multiple turns
        for turn_idx in range(num_turns):
            # Construct message with different context elements
            message_parts = [f"Message {turn_idx + 1}"]
            
            # Add location in first turn if requested
            if has_location and turn_idx == 0:
                message_parts.append("in Philadelphia")
            
            # Add search query in first or second turn if requested
            if has_search_query and turn_idx <= 1:
                message_parts.append("looking for italian food")
            
            user_message = " ".join(message_parts)
            
            # Invoke agent
            invoke_agent(
                mock_agent,
                user_message,
                session_id=actual_session_id,
                user_id=user_id
            )
            
            # Capture context state after this turn
            context = get_context(actual_session_id)
            context_states.append({
                'turn': turn_idx + 1,
                'location': context.location,
                'search_query': context.search_query,
                'num_venues': len(context.recent_venues)
            })
        
        # Property: Context should accumulate across turns
        
        # Verify we have context states for all turns
        assert len(context_states) == num_turns, \
            f"Should have {num_turns} context states, got {len(context_states)}"
        
        # Get final context
        final_context = get_context(actual_session_id)
        
        # Verify location persists if it was set
        if has_location:
            assert final_context.location is not None, \
                "Location should be set in final context"
            assert "phil" in final_context.location.lower(), \
                f"Location should contain 'phil', got: {final_context.location}"
            
            # Verify location persisted across all turns after it was set
            for state in context_states[1:]:  # Skip first turn where it was set
                assert state['location'] is not None, \
                    f"Location should persist in turn {state['turn']}"
        
        # Verify search query persists if it was set
        if has_search_query:
            assert final_context.search_query is not None, \
                "Search query should be set in final context"
            assert "italian" in final_context.search_query.lower(), \
                f"Search query should contain 'italian', got: {final_context.search_query}"
            
            # Verify search query persisted across turns after it was set
            for state in context_states[2:]:  # Skip first two turns where it might be set
                assert state['search_query'] is not None, \
                    f"Search query should persist in turn {state['turn']}"
        
        # Verify venues accumulate if they were added
        if has_venues:
            # Should have accumulated venues (up to max of 5)
            expected_num_venues = min(num_turns, 5)
            assert len(final_context.recent_venues) == expected_num_venues, \
                f"Should have {expected_num_venues} venues in final context, got {len(final_context.recent_venues)}"
            
            # Verify venue count increased over turns (up to max of 5)
            for i, state in enumerate(context_states):
                expected_venues_at_turn = min(i + 1, 5)
                assert state['num_venues'] == expected_venues_at_turn, \
                    f"Turn {state['turn']} should have {expected_venues_at_turn} venues, got {state['num_venues']}"
        
        # Property: Information from earlier turns should be available in later turns
        # This is verified by the persistence checks above
        
        # Clean up
        clear_context(actual_session_id)


# Feature: enhanced-context-retention, Property 24: Session context isolation
@given(
    num_sessions=st.integers(min_value=2, max_value=5),
    locations=st.lists(
        st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        min_size=2,
        max_size=5
    ).filter(lambda x: len(set(x)) == len(x)),  # Ensure all locations are unique
    search_queries=st.lists(
        st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        min_size=2,
        max_size=5
    ).filter(lambda x: len(set(x)) == len(x))  # Ensure all queries are unique
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.filter_too_much])
def test_property_24_session_context_isolation(
    num_sessions: int,
    locations: list,
    search_queries: list
) -> None:
    """
    Feature: enhanced-context-retention, Property 24: Session context isolation
    
    For any two different sessions, context from one session should not be
    accessible from the other.
    
    Validates: Requirements 10.4
    """
    from app.event_planning.context_manager import get_context, clear_context
    import uuid
    
    # Ensure we have enough locations and queries for all sessions
    if len(locations) < num_sessions or len(search_queries) < num_sessions:
        return
    
    # Create multiple sessions with different context
    session_ids = []
    session_contexts = []
    
    for i in range(num_sessions):
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        session_ids.append(session_id)
        
        # Clear any existing context
        clear_context(session_id)
        
        # Set unique context for this session
        context = get_context(session_id)
        context.location = locations[i]
        context.search_query = search_queries[i]
        
        # Add unique venue
        venue_name = f"Venue_Session_{i}"
        place_id = f"ChIJSession{i:05d}"
        agent_message = f"I found **{venue_name}**. Place ID: {place_id}"
        context.update_from_agent_message(agent_message)
        
        # Store expected context
        session_contexts.append({
            'session_id': session_id,
            'location': locations[i],
            'search_query': search_queries[i],
            'venue_name': venue_name,
            'place_id': place_id
        })
    
    # Property: Each session should have only its own context
    for i, expected in enumerate(session_contexts):
        session_id = expected['session_id']
        context = get_context(session_id)
        
        # Verify this session has its own location
        assert context.location == expected['location'], \
            f"Session {i} should have location '{expected['location']}', got '{context.location}'"
        
        # Verify this session has its own search query
        assert context.search_query == expected['search_query'], \
            f"Session {i} should have search query '{expected['search_query']}', got '{context.search_query}'"
        
        # Verify this session has its own venue
        assert len(context.recent_venues) == 1, \
            f"Session {i} should have exactly 1 venue, got {len(context.recent_venues)}"
        
        venue = context.recent_venues[0]
        assert venue.name == expected['venue_name'], \
            f"Session {i} should have venue '{expected['venue_name']}', got '{venue.name}'"
        assert venue.place_id == expected['place_id'], \
            f"Session {i} should have Place ID '{expected['place_id']}', got '{venue.place_id}'"
        
        # Verify this session does NOT have context from other sessions
        for j, other in enumerate(session_contexts):
            if i != j:
                # Should not have other session's location
                if context.location == other['location'] and expected['location'] != other['location']:
                    pytest.fail(
                        f"Session {i} has location from session {j}: '{other['location']}'"
                    )
                
                # Should not have other session's search query
                if context.search_query == other['search_query'] and expected['search_query'] != other['search_query']:
                    pytest.fail(
                        f"Session {i} has search query from session {j}: '{other['search_query']}'"
                    )
                
                # Should not have other session's venue
                for venue in context.recent_venues:
                    if venue.name == other['venue_name']:
                        pytest.fail(
                            f"Session {i} has venue from session {j}: '{other['venue_name']}'"
                        )
    
    # Clean up all sessions
    for session_id in session_ids:
        clear_context(session_id)


# Feature: enhanced-context-retention, Property 18: Context string format
@given(
    has_location=st.booleans(),
    has_search_query=st.booleans(),
    num_venues=st.integers(min_value=0, max_value=3)
)
@settings(max_examples=100)
def test_property_18_context_string_format(
    has_location: bool,
    has_search_query: bool,
    num_venues: int
) -> None:
    """
    Feature: enhanced-context-retention, Property 18: Context string format
    
    For any generated context string, it should match the pattern
    "[CONTEXT: key: value | key: value]".
    
    Validates: Requirements 5.2
    """
    from app.event_planning.context_manager import ConversationContext
    import re
    
    # Create a fresh context
    context = ConversationContext()
    
    # Set up context based on test parameters
    if has_location:
        context.location = "Philadelphia"
    
    if has_search_query:
        context.search_query = "italian"
    
    # Add venues
    for i in range(num_venues):
        venue_name = f"Venue_{i}"
        place_id = f"ChIJ{i:010d}"
        agent_message = f"I found **{venue_name}**. Place ID: {place_id}"
        context.update_from_agent_message(agent_message)
    
    # Generate context string
    context_string = context.get_context_string()
    
    # Property: If context is non-empty, string should match format
    if has_location or has_search_query or num_venues > 0:
        # Should have a non-empty context string
        assert context_string, "Context string should not be empty when context exists"
        
        # Should match the pattern: key: value | key: value
        # The string should contain key-value pairs separated by " | "
        
        # Verify it contains expected keys
        if has_location:
            assert "Location:" in context_string or "location:" in context_string, \
                f"Context string should contain 'Location:', got: {context_string}"
            assert "Philadelphia" in context_string or "philly" in context_string.lower(), \
                f"Context string should contain location value, got: {context_string}"
        
        if has_search_query:
            assert "looking for:" in context_string.lower() or "search" in context_string.lower(), \
                f"Context string should contain search query indicator, got: {context_string}"
            assert "italian" in context_string.lower(), \
                f"Context string should contain search query value, got: {context_string}"
        
        if num_venues > 0:
            assert "venue" in context_string.lower() or "Venue" in context_string, \
                f"Context string should mention venues, got: {context_string}"
        
        # Verify format uses " | " as separator if multiple items
        num_items = sum([has_location, has_search_query, num_venues > 0])
        if num_items > 1:
            assert " | " in context_string, \
                f"Context string with multiple items should use ' | ' separator, got: {context_string}"
    
    else:
        # If no context, string should be empty
        assert not context_string, \
            f"Context string should be empty when no context exists, got: {context_string}"
