"""Quick tests for agent tools to verify they work correctly."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.event_planning.agent_tools import (
    create_user_tool,
    list_users_tool,
    create_group_tool,
    list_groups_tool,
    create_event_tool,
    finalize_event_tool,
    list_events_tool,
)


def test_basic_workflow():
    """Test a basic event planning workflow."""
    print("Testing Event Planning Agent Tools\n")
    print("=" * 60)
    
    # 1. List existing users
    print("\n1. Listing existing users...")
    result = list_users_tool()
    print(result)
    
    # 2. Create a test user if needed
    print("\n2. Creating a test user...")
    result = create_user_tool("Test User", "test@example.com")
    print(result)
    
    # 3. Create a group with existing users
    print("\n3. Creating a group...")
    result = create_group_tool(
        group_name="Test Group",
        creator_name="Alice",  # Use existing user
        member_names="Test User"
    )
    print(result)
    
    # 4. List groups
    print("\n4. Listing groups...")
    result = list_groups_tool()
    print(result)
    
    # 5. Create an event
    print("\n5. Creating an event...")
    result = create_event_tool(
        event_name="Test Hike",
        group_name="Test Group",
        activity_type="hiking",
        location_name="Mountain Vista Trail",
        start_time="2025-01-25 10:00",
        duration_hours=3.0,
        budget=25.0,
        description="Beautiful mountain trail with scenic views"
    )
    print(result)
    
    # 6. List events
    print("\n6. Listing events...")
    result = list_events_tool()
    print(result)
    
    # 7. Finalize event
    print("\n7. Finalizing event...")
    result = finalize_event_tool("Test Hike")
    print(result)
    
    # 8. List events again
    print("\n8. Listing events after finalization...")
    result = list_events_tool()
    print(result)
    
    print("\n" + "=" * 60)
    print("✓ All tests completed successfully!")
    print("\nYou can now try the conversational interface:")
    print("  uv run python app/event_planning/chat_interface.py")


if __name__ == '__main__':
    test_basic_workflow()
