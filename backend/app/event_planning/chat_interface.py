#!/usr/bin/env python3
"""Simple chat interface for the event planning agent.

This provides a conversational interface to the event planning system.
"""

import sys
import os

# Ensure we can import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load .env file if it exists
from pathlib import Path
env_file = Path(__file__).parent.parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


def main():
    """Run the chat interface."""
    print("=" * 60)
    print("Event Planning Agent - Conversational Interface")
    print("=" * 60)
    print("\nI can help you plan events with your friends!")
    print("Try saying things like:")
    print("  • 'Create a user for me'")
    print("  • 'Show me all users'")
    print("  • 'Create a hiking group'")
    print("  • 'When can my group meet?'")
    print("  • 'Plan a dinner event'")
    print("\nType 'exit' or 'quit' to leave.\n")
    
    # Import simple agent (no document retrieval, no GCP credentials needed)
    from app.event_planning.simple_agent import event_planning_agent
    
    # Create session
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(
        user_id="chat_user",
        app_name="event_planning_chat"
    )
    
    # Create runner
    runner = Runner(
        agent=event_planning_agent,
        session_service=session_service,
        app_name="event_planning_chat"
    )
    
    # Chat loop
    while True:
        try:
            # Get user input
            user_input = input("\n🗣️  You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Goodbye! Happy event planning!")
                break
            
            # Create message
            message = types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_input)]
            )
            
            # Get response
            print("\n🤖 Agent: ", end="", flush=True)
            
            response_text = ""
            for event in runner.run(
                new_message=message,
                user_id="chat_user",
                session_id=session.id
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            # Print incrementally for streaming effect
                            new_text = part.text[len(response_text):]
                            print(new_text, end="", flush=True)
                            response_text = part.text
            
            print()  # New line after response
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Happy event planning!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Let's try again...")


if __name__ == '__main__':
    main()
