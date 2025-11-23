"""Test to verify the duplication bug is fixed."""

import re


def test_no_duplicate_context_injection():
    """Verify that context injection code appears only once in agent_invoker.py"""
    
    with open('app/event_planning/agent_invoker.py', 'r') as f:
        content = f.read()
    
    # Look for the context injection pattern
    pattern = r'context\.update_from_user_message\(message\)'
    matches = re.findall(pattern, content)
    
    print(f"Found {len(matches)} occurrences of context.update_from_user_message(message)")
    
    # Should appear exactly once in invoke_agent_streaming
    assert len(matches) == 1, f"Expected 1 occurrence, found {len(matches)}"
    
    # Also check for the enhanced_message assignment
    enhanced_pattern = r'enhanced_message = f"\[CONTEXT: {context_string}\]\\n\\n{message}"'
    enhanced_matches = re.findall(enhanced_pattern, content)
    
    print(f"Found {len(enhanced_matches)} occurrences of enhanced_message assignment")
    
    # Should appear exactly once
    assert len(enhanced_matches) == 1, f"Expected 1 occurrence of enhanced_message, found {len(enhanced_matches)}"
    
    print("✓ Duplication bug is fixed!")


if __name__ == "__main__":
    test_no_duplicate_context_injection()
