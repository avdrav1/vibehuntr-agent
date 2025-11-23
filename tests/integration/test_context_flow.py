"""
End-to-end integration tests for context retention flow.

This module tests the complete context retention flow across multiple
conversation turns, including location persistence, entity reference
resolution, and search query persistence.

Requirements tested:
- 1.2: Location persistence across turns
- 2.2: Entity reference resolution
- 3.2: Search query persistence
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.event_planning.agent_invoker import invoke_agent
from app.event_planning.context_manager import get_context, clear_context


class TestEndToEndContextFlow:
    """End-to-end tests for context retention across conversation turns."""
    
    def test_location_persistence_across_turns(self):
        """
        Test that location persists across multiple conversation turns.
        
        Validates: Requirements 1.2
        
        Flow:
        1. User mentions location in first message
        2. User sends follow-up without location
        3. Verify location is retained and injected into second message
        """
        with patch('app.event_planning.agent_invoker._session_service') as mock_session_service, \
             patch('app.event_planning.agent_invoker.Runner') as mock_runner_class:
            
            # Create a real session service
            real_session_service = InMemorySessionService()
            
            # Create session
            session = real_session_service.create_session_sync(
                user_id="test_user",
                app_name="test_app"
            )
            session_id = session.id
            
            # Clear any existing context
            clear_context(session_id)
            
            # Mock session service to return our real session
            mock_session_service.get_session_sync.return_value = session
            mock_session_service.create_session_sync.return_value = session
            
            # Track messages sent to agent
            messages_to_agent = []
            
            def mock_runner_run(**kwargs):
                """Mock runner that captures messages."""
                new_message = kwargs.get('new_message')
                if new_message:
                    messages_to_agent.append(new_message.parts[0].text)
                
                # Return appropriate response based on turn
                turn_num = len(messages_to_agent)
                if turn_num == 1:
                    response_text = "Great! I'll search for Indian restaurants in Philadelphia."
                else:
                    response_text = "Here are some Indian restaurants with outdoor seating in Philadelphia."
                
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
            
            # Turn 1: User mentions location
            response1 = invoke_agent(
                mock_agent,
                "Indian food in philly",
                session_id=session_id,
                user_id="test_user"
            )
            
            assert "Philadelphia" in response1 or "philly" in response1.lower()
            
            # Verify context was extracted
            context = get_context(session_id)
            assert context.location is not None, "Location should be extracted from first message"
            assert "phil" in context.location.lower(), f"Location should contain 'phil', got: {context.location}"
            
            # Turn 2: User sends follow-up without location
            response2 = invoke_agent(
                mock_agent,
                "any with outdoor seating?",
                session_id=session_id,
                user_id="test_user"
            )
            
            # Verify location was injected into second message
            assert len(messages_to_agent) == 2, "Should have sent 2 messages to agent"
            
            second_message = messages_to_agent[1]
            assert "[CONTEXT:" in second_message, \
                f"Second message should have context injected, got: {second_message[:100]}"
            assert "Location:" in second_message or "location:" in second_message, \
                f"Second message should include location in context, got: {second_message[:200]}"
            
            # Verify the original message is included
            assert "outdoor seating" in second_message, \
                f"Second message should contain original text, got: {second_message}"
            
            # Clean up
            clear_context(session_id)
    
    def test_entity_reference_resolution(self):
        """
        Test that entity references are resolved correctly.
        
        Validates: Requirements 2.2
        
        Flow:
        1. Agent mentions venues with Place IDs
        2. User refers to venue with vague reference ("that one", "the first one")
        3. Verify reference is resolved and Place ID is available in context
        """
        with patch('app.event_planning.agent_invoker._session_service') as mock_session_service, \
             patch('app.event_planning.agent_invoker.Runner') as mock_runner_class:
            
            # Create a real session service
            real_session_service = InMemorySessionService()
            
            # Create session
            session = real_session_service.create_session_sync(
                user_id="test_user",
                app_name="test_app"
            )
            session_id = session.id
            
            # Clear any existing context
            clear_context(session_id)
            
            # Mock session service to return our real session
            mock_session_service.get_session_sync.return_value = session
            mock_session_service.create_session_sync.return_value = session
            
            # Track messages sent to agent
            messages_to_agent = []
            
            def mock_runner_run(**kwargs):
                """Mock runner that captures messages."""
                new_message = kwargs.get('new_message')
                if new_message:
                    messages_to_agent.append(new_message.parts[0].text)
                
                # Return appropriate response based on turn
                turn_num = len(messages_to_agent)
                if turn_num == 1:
                    # Agent lists venues with Place IDs
                    response_text = (
                        "I found these restaurants:\n"
                        "1. **Osteria**. Place ID: ChIJabc123\n"
                        "2. **Vedge**. Place ID: ChIJdef456\n"
                        "3. **Zahav**. Place ID: ChIJghi789"
                    )
                else:
                    # Agent provides details about the referenced venue
                    response_text = "Here are more details about Osteria..."
                
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
            
            # Turn 1: User asks for restaurants
            response1 = invoke_agent(
                mock_agent,
                "restaurants in philly",
                session_id=session_id,
                user_id="test_user"
            )
            
            assert "Osteria" in response1
            assert "ChIJabc123" in response1
            
            # Verify venues were extracted
            context = get_context(session_id)
            assert len(context.recent_venues) == 3, \
                f"Should have extracted 3 venues, got {len(context.recent_venues)}"
            
            # Verify first venue
            first_venue = context.recent_venues[0]
            assert first_venue.name == "Osteria", \
                f"First venue should be Osteria, got {first_venue.name}"
            assert first_venue.place_id == "ChIJabc123", \
                f"First venue should have Place ID ChIJabc123, got {first_venue.place_id}"
            
            # Turn 2: User refers to venue with vague reference
            response2 = invoke_agent(
                mock_agent,
                "more details on the first one",
                session_id=session_id,
                user_id="test_user"
            )
            
            # Verify reference was resolved
            assert len(messages_to_agent) == 2, "Should have sent 2 messages to agent"
            
            second_message = messages_to_agent[1]
            assert "[CONTEXT:" in second_message, \
                f"Second message should have context injected, got: {second_message[:100]}"
            
            # Verify venues are in context
            assert "Osteria" in second_message or "ChIJabc123" in second_message, \
                f"Second message should include venue information in context, got: {second_message[:300]}"
            
            # Test resolution with different reference types
            resolved_venue = context.find_venue_by_reference("the first one")
            assert resolved_venue is not None, "Should resolve 'the first one'"
            assert resolved_venue.name == "Osteria", \
                f"Should resolve to Osteria, got {resolved_venue.name}"
            
            resolved_venue = context.find_venue_by_reference("that one")
            assert resolved_venue is not None, "Should resolve 'that one'"
            # "that one" should resolve to most recent (last in list)
            assert resolved_venue.name == "Zahav", \
                f"'that one' should resolve to most recent venue (Zahav), got {resolved_venue.name}"
            
            # Clean up
            clear_context(session_id)
    
    def test_search_query_persistence(self):
        """
        Test that search query persists across conversation turns.
        
        Validates: Requirements 3.2
        
        Flow:
        1. User specifies search query (food type)
        2. User sends follow-up related to the search
        3. Verify search query is retained and injected into second message
        """
        with patch('app.event_planning.agent_invoker._session_service') as mock_session_service, \
             patch('app.event_planning.agent_invoker.Runner') as mock_runner_class:
            
            # Create a real session service
            real_session_service = InMemorySessionService()
            
            # Create session
            session = real_session_service.create_session_sync(
                user_id="test_user",
                app_name="test_app"
            )
            session_id = session.id
            
            # Clear any existing context
            clear_context(session_id)
            
            # Mock session service to return our real session
            mock_session_service.get_session_sync.return_value = session
            mock_session_service.create_session_sync.return_value = session
            
            # Track messages sent to agent
            messages_to_agent = []
            
            def mock_runner_run(**kwargs):
                """Mock runner that captures messages."""
                new_message = kwargs.get('new_message')
                if new_message:
                    messages_to_agent.append(new_message.parts[0].text)
                
                # Return appropriate response based on turn
                turn_num = len(messages_to_agent)
                if turn_num == 1:
                    response_text = "Here are some Italian restaurants in Philadelphia."
                elif turn_num == 2:
                    response_text = "Here are Italian restaurants with parking in Philadelphia."
                else:
                    response_text = "Here are Italian restaurants with outdoor seating and parking in Philadelphia."
                
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
            
            # Turn 1: User specifies search query
            response1 = invoke_agent(
                mock_agent,
                "Italian food in philly",
                session_id=session_id,
                user_id="test_user"
            )
            
            assert "Italian" in response1
            
            # Verify search query was extracted
            context = get_context(session_id)
            assert context.search_query is not None, \
                "Search query should be extracted from first message"
            assert "italian" in context.search_query.lower(), \
                f"Search query should contain 'italian', got: {context.search_query}"
            
            # Turn 2: User sends follow-up related to search
            response2 = invoke_agent(
                mock_agent,
                "any with parking?",
                session_id=session_id,
                user_id="test_user"
            )
            
            # Verify search query was injected into second message
            assert len(messages_to_agent) == 2, "Should have sent 2 messages to agent"
            
            second_message = messages_to_agent[1]
            assert "[CONTEXT:" in second_message, \
                f"Second message should have context injected, got: {second_message[:100]}"
            
            # Verify search query is in context
            assert "italian" in second_message.lower() or "User is looking for:" in second_message, \
                f"Second message should include search query in context, got: {second_message[:300]}"
            
            # Turn 3: Another follow-up
            response3 = invoke_agent(
                mock_agent,
                "and outdoor seating?",
                session_id=session_id,
                user_id="test_user"
            )
            
            # Verify search query still persists
            assert len(messages_to_agent) == 3, "Should have sent 3 messages to agent"
            
            third_message = messages_to_agent[2]
            assert "[CONTEXT:" in third_message, \
                f"Third message should have context injected, got: {third_message[:100]}"
            
            # Clean up
            clear_context(session_id)
    
    def test_combined_context_persistence(self):
        """
        Test that all context types persist together across turns.
        
        Validates: Requirements 1.2, 2.2, 3.2
        
        Flow:
        1. User mentions location and search query
        2. Agent responds with venues
        3. User sends follow-up without any context
        4. Verify all context (location, query, venues) is retained
        """
        with patch('app.event_planning.agent_invoker._session_service') as mock_session_service, \
             patch('app.event_planning.agent_invoker.Runner') as mock_runner_class:
            
            # Create a real session service
            real_session_service = InMemorySessionService()
            
            # Create session
            session = real_session_service.create_session_sync(
                user_id="test_user",
                app_name="test_app"
            )
            session_id = session.id
            
            # Clear any existing context
            clear_context(session_id)
            
            # Mock session service to return our real session
            mock_session_service.get_session_sync.return_value = session
            mock_session_service.create_session_sync.return_value = session
            
            # Track messages sent to agent
            messages_to_agent = []
            
            def mock_runner_run(**kwargs):
                """Mock runner that captures messages."""
                new_message = kwargs.get('new_message')
                if new_message:
                    messages_to_agent.append(new_message.parts[0].text)
                
                # Return appropriate response based on turn
                turn_num = len(messages_to_agent)
                if turn_num == 1:
                    response_text = (
                        "Here are some sushi restaurants in San Francisco:\n"
                        "1. **Akiko's**. Place ID: ChIJsushi1\n"
                        "2. **Omakase**. Place ID: ChIJsushi2"
                    )
                else:
                    response_text = "Akiko's has great reviews and is highly rated."
                
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
            
            # Turn 1: User mentions location and search query
            response1 = invoke_agent(
                mock_agent,
                "sushi in SF",
                session_id=session_id,
                user_id="test_user"
            )
            
            assert "Akiko" in response1
            
            # Verify all context was extracted
            context = get_context(session_id)
            assert context.location is not None, "Location should be extracted"
            assert context.search_query is not None, "Search query should be extracted"
            assert len(context.recent_venues) == 2, "Venues should be extracted"
            
            # Turn 2: User sends follow-up without any context
            response2 = invoke_agent(
                mock_agent,
                "tell me more about the first one",
                session_id=session_id,
                user_id="test_user"
            )
            
            # Verify all context was injected
            assert len(messages_to_agent) == 2, "Should have sent 2 messages to agent"
            
            second_message = messages_to_agent[1]
            assert "[CONTEXT:" in second_message, \
                f"Second message should have context injected, got: {second_message[:100]}"
            
            # Verify location is in context
            assert "Location:" in second_message or "location:" in second_message, \
                f"Second message should include location, got: {second_message[:300]}"
            
            # Verify search query is in context
            assert "sushi" in second_message.lower() or "User is looking for:" in second_message, \
                f"Second message should include search query, got: {second_message[:300]}"
            
            # Verify venues are in context
            assert "Akiko" in second_message or "ChIJsushi1" in second_message, \
                f"Second message should include venue information, got: {second_message[:300]}"
            
            # Clean up
            clear_context(session_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
