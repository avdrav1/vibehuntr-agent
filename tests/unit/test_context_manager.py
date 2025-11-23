"""Unit tests for context manager.

This module tests the context manager's ability to extract and track
conversation context including locations, search queries, and venues.
"""

import sys
import os
import pytest
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.event_planning.context_manager import (
    ConversationContext,
    VenueInfo,
    get_context,
    clear_context
)


class TestLocationExtraction:
    """Test location extraction from user messages."""
    
    def test_extract_city_name(self):
        """Test extracting city names from messages."""
        context = ConversationContext()
        
        # Test various city names
        test_cases = [
            ("I want pizza in philadelphia", "philadelphia"),
            ("Looking for food in philly", "philly"),
            ("Restaurants in nyc", "nyc"),
            ("Find me something in new york", "new york"),
            ("Boston area restaurants", "boston"),
            ("Chicago pizza places", "chicago"),
        ]
        
        for message, expected_location in test_cases:
            context = ConversationContext()
            context.update_from_user_message(message)
            assert context.location == expected_location, \
                f"Failed to extract '{expected_location}' from '{message}', got '{context.location}'"
    
    def test_extract_location_with_prepositions(self):
        """Test extracting locations with 'around' and 'near' prepositions."""
        context = ConversationContext()
        
        test_cases = [
            ("restaurants around seattle", "seattle"),
            ("food near portland", "portland"),
            ("places around austin", "austin"),
        ]
        
        for message, expected_location in test_cases:
            context = ConversationContext()
            context.update_from_user_message(message)
            assert context.location == expected_location, \
                f"Failed to extract '{expected_location}' from '{message}'"
    
    def test_location_persistence(self):
        """Test that location persists across messages."""
        context = ConversationContext()
        
        # First message sets location
        context.update_from_user_message("pizza in philly")
        assert context.location == "philly"
        
        # Second message without location should keep the same location
        context.update_from_user_message("what about italian food")
        assert context.location == "philly"
    
    def test_location_update(self):
        """Test that location updates when explicitly changed."""
        context = ConversationContext()
        
        # First message sets location
        context.update_from_user_message("pizza in philly")
        assert context.location == "philly"
        
        # Second message changes location
        context.update_from_user_message("actually, show me places in boston")
        assert context.location == "boston"


class TestSearchQueryExtraction:
    """Test search query extraction from user messages."""
    
    def test_extract_food_types(self):
        """Test extracting food types from messages."""
        context = ConversationContext()
        
        test_cases = [
            ("I want pizza", "pizza"),
            ("Looking for sushi", "sushi"),
            ("Find me italian food", "italian"),
            ("Chinese restaurants", "chinese"),
            ("Mexican tacos", "mexican"),
            ("Thai food", "thai"),
            ("Indian cuisine", "indian"),
            ("Burgers please", "burger"),
        ]
        
        for message, expected_query in test_cases:
            context = ConversationContext()
            context.update_from_user_message(message)
            assert context.search_query == expected_query, \
                f"Failed to extract '{expected_query}' from '{message}', got '{context.search_query}'"
    
    def test_extract_venue_types(self):
        """Test extracting venue types from messages."""
        context = ConversationContext()
        
        test_cases = [
            ("Find me a restaurant", "restaurant"),
            ("Looking for a bar", "bar"),
            ("Coffee shops nearby", "coffee"),
            ("Good cafes", "cafe"),
        ]
        
        for message, expected_query in test_cases:
            context = ConversationContext()
            context.update_from_user_message(message)
            assert context.search_query == expected_query, \
                f"Failed to extract '{expected_query}' from '{message}'"
    
    def test_extract_meal_times(self):
        """Test extracting meal times from messages."""
        context = ConversationContext()
        
        test_cases = [
            ("brunch spots", "brunch"),
            ("lunch places", "lunch"),
            ("dinner restaurants", "dinner"),
            ("breakfast options", "breakfast"),
        ]
        
        for message, expected_query in test_cases:
            context = ConversationContext()
            context.update_from_user_message(message)
            assert context.search_query == expected_query, \
                f"Failed to extract '{expected_query}' from '{message}'"
    
    def test_search_query_persistence(self):
        """Test that search query persists across messages."""
        context = ConversationContext()
        
        # First message sets search query
        context.update_from_user_message("I want pizza")
        assert context.search_query == "pizza"
        
        # Second message without search query should keep the same query
        context.update_from_user_message("in philadelphia")
        assert context.search_query == "pizza"


class TestVenueExtraction:
    """Test venue extraction from agent responses."""
    
    def test_extract_single_venue(self):
        """Test extracting a single venue from agent response."""
        context = ConversationContext()
        
        agent_message = "I found **Osteria**. Place ID: ChIJabc123def456"
        context.update_from_agent_message(agent_message)
        
        assert len(context.recent_venues) == 1
        assert context.recent_venues[0].name == "Osteria"
        assert context.recent_venues[0].place_id == "ChIJabc123def456"
    
    def test_extract_multiple_venues(self):
        """Test extracting multiple venues from agent response."""
        context = ConversationContext()
        
        agent_message = """Here are some options:
        **Osteria**. Place ID: ChIJabc123def456
        **Vedge**. Place ID: ChIJxyz789ghi012
        **Zahav**. Place ID: ChIJmno345pqr678
        """
        context.update_from_agent_message(agent_message)
        
        assert len(context.recent_venues) == 3
        assert context.recent_venues[0].name == "Osteria"
        assert context.recent_venues[1].name == "Vedge"
        assert context.recent_venues[2].name == "Zahav"
    
    def test_venue_list_size_limit(self):
        """Test that venue list is limited to 5 items."""
        context = ConversationContext()
        
        # Add 7 venues
        for i in range(7):
            agent_message = f"**Venue_{i}**. Place ID: ChIJ{i:010d}"
            context.update_from_agent_message(agent_message)
        
        # Should only keep the last 5
        assert len(context.recent_venues) == 5
        assert context.recent_venues[0].name == "Venue_2"
        assert context.recent_venues[4].name == "Venue_6"
    
    def test_venue_timestamp(self):
        """Test that venues have timestamps."""
        context = ConversationContext()
        
        agent_message = "**Osteria**. Place ID: ChIJabc123def456"
        context.update_from_agent_message(agent_message)
        
        assert len(context.recent_venues) == 1
        assert isinstance(context.recent_venues[0].mentioned_at, datetime)


class TestContextStringGeneration:
    """Test context string generation for injection."""
    
    def test_empty_context(self):
        """Test context string with no information."""
        context = ConversationContext()
        context_string = context.get_context_string()
        
        assert context_string == ""
    
    def test_location_only(self):
        """Test context string with only location."""
        context = ConversationContext()
        context.location = "philadelphia"
        context_string = context.get_context_string()
        
        assert "Location: philadelphia" in context_string
    
    def test_search_query_only(self):
        """Test context string with only search query."""
        context = ConversationContext()
        context.search_query = "pizza"
        context_string = context.get_context_string()
        
        assert "User is looking for: pizza" in context_string
    
    def test_combined_context(self):
        """Test context string with multiple pieces of information."""
        context = ConversationContext()
        context.location = "philadelphia"
        context.search_query = "pizza"
        
        # Add a venue
        agent_message = "**Osteria**. Place ID: ChIJabc123def456"
        context.update_from_agent_message(agent_message)
        
        context_string = context.get_context_string()
        
        assert "Location: philadelphia" in context_string
        assert "User is looking for: pizza" in context_string
        assert "Recently mentioned venues:" in context_string
        assert "Osteria" in context_string
    
    def test_context_string_format(self):
        """Test that context string uses pipe separator."""
        context = ConversationContext()
        context.location = "philadelphia"
        context.search_query = "pizza"
        
        context_string = context.get_context_string()
        
        # Should use " | " as separator
        assert " | " in context_string


class TestReferenceResolution:
    """Test entity reference resolution."""
    
    def test_ordinal_references(self):
        """Test resolving ordinal references (first, second, etc.)."""
        context = ConversationContext()
        
        # Add multiple venues
        for i in range(3):
            agent_message = f"**Venue_{i}**. Place ID: ChIJ{i:010d}"
            context.update_from_agent_message(agent_message)
        
        # Test ordinal references
        first = context.find_venue_by_reference("the first one")
        assert first.name == "Venue_0"
        
        second = context.find_venue_by_reference("second")
        assert second.name == "Venue_1"
        
        third = context.find_venue_by_reference("third")
        assert third.name == "Venue_2"
    
    def test_vague_references(self):
        """Test resolving vague references (that one, this one, etc.)."""
        context = ConversationContext()
        
        # Add multiple venues
        for i in range(3):
            agent_message = f"**Venue_{i}**. Place ID: ChIJ{i:010d}"
            context.update_from_agent_message(agent_message)
        
        # Vague references should resolve to most recent
        test_cases = ["that one", "this one", "the one", "it", "that", "this"]
        
        for reference in test_cases:
            resolved = context.find_venue_by_reference(reference)
            assert resolved.name == "Venue_2", \
                f"Vague reference '{reference}' should resolve to most recent venue"
    
    def test_name_based_reference(self):
        """Test resolving references by venue name."""
        context = ConversationContext()
        
        # Add venues
        agent_message = """
        **Osteria**. Place ID: ChIJabc123
        **Vedge**. Place ID: ChIJxyz789
        """
        context.update_from_agent_message(agent_message)
        
        # Reference by name
        resolved = context.find_venue_by_reference("tell me about Osteria")
        assert resolved.name == "Osteria"
    
    def test_no_venues_reference(self):
        """Test reference resolution with no venues."""
        context = ConversationContext()
        
        resolved = context.find_venue_by_reference("the first one")
        assert resolved is None


class TestSerialization:
    """Test serialization methods."""
    
    def test_venue_to_dict(self):
        """Test VenueInfo to_dict method."""
        venue = VenueInfo(
            name="Osteria",
            place_id="ChIJabc123",
            location="philadelphia"
        )
        
        venue_dict = venue.to_dict()
        
        assert venue_dict["name"] == "Osteria"
        assert venue_dict["place_id"] == "ChIJabc123"
        assert venue_dict["location"] == "philadelphia"
        assert "mentioned_at" in venue_dict
    
    def test_context_to_dict(self):
        """Test ConversationContext to_dict method."""
        context = ConversationContext()
        context.location = "philadelphia"
        context.search_query = "pizza"
        
        # Add a venue
        agent_message = "**Osteria**. Place ID: ChIJabc123"
        context.update_from_agent_message(agent_message)
        
        context_dict = context.to_dict()
        
        assert context_dict["location"] == "philadelphia"
        assert context_dict["search_query"] == "pizza"
        assert len(context_dict["recent_venues"]) == 1
        assert context_dict["recent_venues"][0]["name"] == "Osteria"


class TestContextClear:
    """Test context clearing."""
    
    def test_clear_all_context(self):
        """Test clearing all context."""
        context = ConversationContext()
        context.location = "philadelphia"
        context.search_query = "pizza"
        context.last_user_intent = "find me pizza"
        
        # Add a venue
        agent_message = "**Osteria**. Place ID: ChIJabc123"
        context.update_from_agent_message(agent_message)
        
        # Clear context
        context.clear()
        
        assert context.location is None
        assert context.search_query is None
        assert context.last_user_intent is None
        assert len(context.recent_venues) == 0


class TestSessionManagement:
    """Test session-based context management."""
    
    def test_get_context_creates_new(self):
        """Test that get_context creates new context for new session."""
        session_id = "test_session_123"
        
        context = get_context(session_id)
        
        assert context is not None
        assert isinstance(context, ConversationContext)
    
    def test_get_context_returns_existing(self):
        """Test that get_context returns existing context for same session."""
        session_id = "test_session_456"
        
        # Get context and modify it
        context1 = get_context(session_id)
        context1.location = "philadelphia"
        
        # Get context again
        context2 = get_context(session_id)
        
        # Should be the same context
        assert context2.location == "philadelphia"
        assert context1 is context2
    
    def test_clear_context_removes_session(self):
        """Test that clear_context removes session context."""
        session_id = "test_session_789"
        
        # Create context
        context = get_context(session_id)
        context.location = "philadelphia"
        
        # Clear context
        clear_context(session_id)
        
        # Get context again should create new empty context
        new_context = get_context(session_id)
        assert new_context.location is None
