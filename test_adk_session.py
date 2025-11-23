"""Test script to understand ADK session service behavior."""

from google.adk.sessions import InMemorySessionService
from google.genai import types

# Create session service
session_service = InMemorySessionService()

# Create a session
session = session_service.create_session_sync(
    user_id="test_user",
    app_name="test_app"
)

print(f"Created session: {session.id}")
print(f"Initial events: {len(session.events)}")
print(f"Events: {session.events}")

# Try to retrieve the session
retrieved_session = session_service.get_session_sync(
    session_id=session.id,
    app_name="test_app",
    user_id="test_user"
)
print(f"\nRetrieved session: {retrieved_session.id}")
print(f"Retrieved events: {len(retrieved_session.events)}")
print(f"Events: {retrieved_session.events}")

# Check if events are stored after runner invocation
print("\n" + "="*50)
print("Session events are stored by ADK Runner automatically")
print("We need to query the session to get the conversation history")
print("="*50)
