"""Test to reproduce the South Philly Italian duplicate response issue."""

import logging
from app.event_planning.agent_loader import get_agent
from app.event_planning.agent_invoker import invoke_agent_streaming

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_south_philly_italian():
    """Test the conversation that triggered duplicate response."""
    agent = get_agent()
    session_id = "test_south_philly_duplicate"
    
    # First message: "Italian food"
    print("\n=== Message 1: Italian food ===")
    response1_chunks = []
    for item in invoke_agent_streaming(agent, "Italian food", session_id=session_id):
        if item['type'] == 'text':
            response1_chunks.append(item['content'])
            print(item['content'], end='', flush=True)
    response1 = ''.join(response1_chunks)
    print(f"\n\nResponse 1 length: {len(response1)} chars")
    
    # Second message: "$$$"
    print("\n\n=== Message 2: $$$ ===")
    response2_chunks = []
    for item in invoke_agent_streaming(agent, "$$$", session_id=session_id):
        if item['type'] == 'text':
            response2_chunks.append(item['content'])
            print(item['content'], end='', flush=True)
    response2 = ''.join(response2_chunks)
    print(f"\n\nResponse 2 length: {len(response2)} chars")
    
    # Third message: "South Philly Italian"
    print("\n\n=== Message 3: South Philly Italian ===")
    response3_chunks = []
    for item in invoke_agent_streaming(agent, "South Philly Italian", session_id=session_id):
        if item['type'] == 'text':
            response3_chunks.append(item['content'])
            print(item['content'], end='', flush=True)
    response3 = ''.join(response3_chunks)
    print(f"\n\nResponse 3 length: {len(response3)} chars")
    
    # Check for duplicates in response 3
    print("\n\n=== Checking for duplicates ===")
    
    # Look for the repeated paragraph
    search_text = "Okay, I found five Italian restaurants in South Philly"
    count = response3.count(search_text)
    print(f"Found '{search_text}' {count} time(s)")
    
    if count > 1:
        print("\n❌ DUPLICATE DETECTED!")
        print(f"The paragraph appears {count} times in the response")
        
        # Find the positions
        import re
        matches = list(re.finditer(re.escape(search_text), response3))
        for i, match in enumerate(matches, 1):
            print(f"\nOccurrence {i} at position {match.start()}")
            # Show context
            start = max(0, match.start() - 50)
            end = min(len(response3), match.end() + 200)
            print(f"Context: ...{response3[start:end]}...")
    else:
        print("\n✅ No duplicates found")
    
    return response3

if __name__ == "__main__":
    test_south_philly_italian()
