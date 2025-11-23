#!/usr/bin/env python3
"""
Manual test script for context retention fix.

This script demonstrates the expected behavior after the context retention fix.
Run this manually to test the agent's ability to remember information from
its own previous responses.

Usage:
    python test_context_retention_manual.py

Requirements:
    - GOOGLE_API_KEY environment variable set, OR
    - Google Cloud credentials configured via `gcloud auth application-default login`
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.event_planning.agent_loader import get_agent
from app.event_planning.agent_invoker import invoke_agent
import uuid


def test_venue_search_context():
    """Test that agent remembers venue details from search results."""
    print("=" * 80)
    print("CONTEXT RETENTION TEST: Venue Search Follow-up")
    print("=" * 80)
    print()
    
    # Get agent
    print("Loading agent...")
    agent = get_agent()
    print(f"✓ Agent loaded: {agent.name}")
    print()
    
    # Create unique session
    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}")
    print()
    
    # Turn 1: Search for venues
    print("-" * 80)
    print("TURN 1: User searches for venues")
    print("-" * 80)
    user_message_1 = "Find Italian restaurants in Philadelphia"
    print(f"User: {user_message_1}")
    print()
    
    print("Agent: ", end="", flush=True)
    response_1 = invoke_agent(
        agent=agent,
        message=user_message_1,
        session_id=session_id,
        user_id="test_user"
    )
    print(response_1)
    print()
    
    # Check if response contains Place ID
    if "Place ID:" in response_1 or "place_id" in response_1.lower():
        print("✓ Agent provided Place ID in response")
    else:
        print("⚠ Agent did not provide Place ID (may not have found venues)")
    print()
    
    # Turn 2: Ask for more details (implicit reference)
    print("-" * 80)
    print("TURN 2: User asks for more details (implicit reference)")
    print("-" * 80)
    user_message_2 = "more details"
    print(f"User: {user_message_2}")
    print()
    
    print("Agent: ", end="", flush=True)
    response_2 = invoke_agent(
        agent=agent,
        message=user_message_2,
        session_id=session_id,
        user_id="test_user"
    )
    print(response_2)
    print()
    
    # Analyze response
    print("-" * 80)
    print("ANALYSIS")
    print("-" * 80)
    
    # Check for bad patterns (asking for Place ID again)
    bad_patterns = [
        "which venue",
        "provide the place id",
        "specify which",
        "which one",
        "could you please specify"
    ]
    
    found_bad_pattern = False
    for pattern in bad_patterns:
        if pattern.lower() in response_2.lower():
            print(f"❌ FAIL: Agent asked for clarification: '{pattern}'")
            found_bad_pattern = True
            break
    
    if not found_bad_pattern:
        print("✓ PASS: Agent did not ask user to repeat information")
    
    # Check for good patterns (providing details)
    good_patterns = [
        "hours",
        "reviews",
        "phone",
        "website",
        "address"
    ]
    
    found_good_pattern = False
    for pattern in good_patterns:
        if pattern.lower() in response_2.lower():
            print(f"✓ PASS: Agent provided venue details: '{pattern}'")
            found_good_pattern = True
            break
    
    if not found_good_pattern:
        print("⚠ WARNING: Agent response doesn't contain typical venue details")
    
    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print()
    print("Expected behavior:")
    print("  - Agent should extract Place ID from its previous message")
    print("  - Agent should call get_venue_details_tool with that Place ID")
    print("  - Agent should provide detailed venue information")
    print()
    print("Incorrect behavior:")
    print("  - Agent asks 'which venue?' or 'provide the Place ID'")
    print("  - Agent doesn't remember what it just showed")
    print()


def test_event_planning_context():
    """Test that agent remembers event details across turns."""
    print("=" * 80)
    print("CONTEXT RETENTION TEST: Event Planning Follow-up")
    print("=" * 80)
    print()
    
    # Get agent
    print("Loading agent...")
    agent = get_agent()
    print(f"✓ Agent loaded: {agent.name}")
    print()
    
    # Create unique session
    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}")
    print()
    
    # Turn 1: Create a user
    print("-" * 80)
    print("TURN 1: User creates profile")
    print("-" * 80)
    user_message_1 = "Create a user profile for me. My name is Alice and email is alice@example.com"
    print(f"User: {user_message_1}")
    print()
    
    print("Agent: ", end="", flush=True)
    response_1 = invoke_agent(
        agent=agent,
        message=user_message_1,
        session_id=session_id,
        user_id="test_user"
    )
    print(response_1)
    print()
    
    # Turn 2: Ask about the profile (implicit reference)
    print("-" * 80)
    print("TURN 2: User asks about their profile (implicit reference)")
    print("-" * 80)
    user_message_2 = "What's my email?"
    print(f"User: {user_message_2}")
    print()
    
    print("Agent: ", end="", flush=True)
    response_2 = invoke_agent(
        agent=agent,
        message=user_message_2,
        session_id=session_id,
        user_id="test_user"
    )
    print(response_2)
    print()
    
    # Analyze response
    print("-" * 80)
    print("ANALYSIS")
    print("-" * 80)
    
    if "alice@example.com" in response_2.lower():
        print("✓ PASS: Agent remembered the email from previous turn")
    else:
        print("❌ FAIL: Agent did not remember the email")
    
    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print()


if __name__ == "__main__":
    print()
    print("CONTEXT RETENTION MANUAL TEST SUITE")
    print("=" * 80)
    print()
    print("This script tests the agent's ability to maintain context across turns.")
    print("The agent should remember information from its own previous responses.")
    print()
    
    try:
        # Test 1: Venue search context
        test_venue_search_context()
        
        print()
        input("Press Enter to continue to next test...")
        print()
        
        # Test 2: Event planning context
        test_event_planning_context()
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
