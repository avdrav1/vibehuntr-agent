"""Test script for Google Places API integration."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.event_planning.places_tools import search_venues_tool, get_venue_details_tool


def test_places_integration():
    """Test the Places API integration."""
    
    print("=" * 60)
    print("Testing Google Places API Integration")
    print("=" * 60)
    
    # Test 1: Search for restaurants
    print("\n1. Searching for Italian restaurants in San Francisco...")
    print("-" * 60)
    result = search_venues_tool(
        query="Italian restaurants",
        location="San Francisco, CA",
        min_rating=4.0
    )
    print(result)
    
    # Test 2: Search for activities
    print("\n2. Searching for hiking trails near Seattle...")
    print("-" * 60)
    result = search_venues_tool(
        query="hiking trails",
        location="Seattle, WA"
    )
    print(result)
    
    # Test 3: Search with budget filter
    print("\n3. Searching for budget-friendly cafes...")
    print("-" * 60)
    result = search_venues_tool(
        query="coffee shops",
        location="Austin, TX",
        max_price=2
    )
    print(result)
    
    print("\n" + "=" * 60)
    print("✓ Tests completed!")
    print("\nTo get details about a venue, use:")
    print("  get_venue_details_tool(place_id='...')")
    print("\nOr try the conversational interface:")
    print("  uv run python app/event_planning/chat_interface.py")


if __name__ == '__main__':
    test_places_integration()
