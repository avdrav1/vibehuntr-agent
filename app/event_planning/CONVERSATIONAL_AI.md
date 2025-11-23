# Conversational AI Interface for Event Planning

The event planning system now includes a natural language conversational interface powered by Google's ADK and Gemini!

## Quick Start

Run the chat interface:

```bash
uv run python app/event_planning/chat_interface.py
```

Or use the ADK playground:

```bash
make playground
```

Then navigate to `http://localhost:8501` in your browser.

## What You Can Do

The AI agent understands natural language and can help you with:

### User Management
- "Create a user for me named Alice with email alice@example.com"
- "Show me all users"
- "Update my preferences - I like hiking and have a budget of $50"
- "I'm available next Saturday from 2pm to 6pm"

### Group Management
- "Create a hiking group called Weekend Warriors with me as creator"
- "Add Bob and Charlie to my Weekend Warriors group"
- "Show me all my groups"
- "Who's in the Weekend Warriors group?"

### Event Planning
- "When can my Weekend Warriors group meet?"
- "Find a time for a 3-hour event with my group"
- "Plan a hiking event for next Saturday at 10am"
- "Create a dinner event at Italian Bistro for my group"
- "Finalize the Saturday Hike event"

### Feedback
- "I want to rate the Saturday Hike event"
- "Submit feedback: 5 stars, it was amazing!"
- "Show me all events"

## Example Conversation

```
🗣️  You: Create a user for me named Alice with email alice@example.com

🤖 Agent: ✓ Created user profile for Alice (alice@example.com). 
         They can now join groups and plan events!

🗣️  You: Create another user named Bob with email bob@example.com

🤖 Agent: ✓ Created user profile for Bob (bob@example.com). 
         They can now join groups and plan events!

🗣️  You: Create a hiking group called Weekend Warriors with Alice as creator

🤖 Agent: ✓ Created group 'Weekend Warriors' with 1 member(s)!

🗣️  You: Add Bob to the Weekend Warriors group

🤖 Agent: I'll help you add Bob to the group. Let me do that now...
         ✓ Added Bob to Weekend Warriors! The group now has 2 members.

🗣️  You: I'm Alice and I'm available next Saturday from 10am to 4pm

🤖 Agent: ✓ Added availability for Alice: 2025-01-25 10:00 to 2025-01-25 16:00 (UTC)

🗣️  You: When can my Weekend Warriors group meet?

🤖 Agent: Found 1 optimal time slot(s) for Weekend Warriors:

         1. 2025-01-25 10:00 to 12:00
            50% attendance (1 members)

         Note: Only Alice has provided availability. Bob should add their 
         availability for better scheduling!

🗣️  You: Plan a hiking event called Mountain Adventure for Saturday at 10am

🤖 Agent: ✓ Created event 'Mountain Adventure'!
           Activity: hiking
           When: 2025-01-25 10:00 to 12:00
           Where: Mountain Trail
           Participants: 2 members
           Status: PENDING

         Use finalize_event to confirm this event!

🗣️  You: Finalize the Mountain Adventure event

🤖 Agent: ✓ Event 'Mountain Adventure' is now CONFIRMED! 🎉
```

## How It Works

### Architecture

```
┌─────────────────────────────────────┐
│   User Input (Natural Language)    │
│   "Plan a hike next Saturday"      │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Gemini 2.0 Flash (LLM)           │
│   - Understands intent              │
│   - Decides which tools to use      │
│   - Generates friendly responses    │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Event Planning Tools              │
│   - create_user_tool                │
│   - create_group_tool               │
│   - find_optimal_time_tool          │
│   - create_event_tool               │
│   - etc. (12 tools total)           │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Event Planning Service            │
│   - Business logic                  │
│   - Validation                      │
│   - Data persistence                │
└─────────────────────────────────────┘
```

### Tools Available

The agent has access to 12 specialized tools:

1. **create_user_tool** - Create new users
2. **list_users_tool** - List all users
3. **update_user_preferences_tool** - Set preferences
4. **add_availability_tool** - Add availability windows
5. **create_group_tool** - Create friend groups
6. **list_groups_tool** - List groups
7. **get_group_details_tool** - Get group info
8. **find_optimal_time_tool** - Find meeting times
9. **create_event_tool** - Create events
10. **finalize_event_tool** - Confirm events
11. **list_events_tool** - List events
12. **submit_feedback_tool** - Submit feedback

Each tool has detailed docstrings that help the LLM understand when and how to use them.

## Advanced Features

### Multi-Turn Conversations

The agent maintains context across the conversation:

```
You: Create a user named Alice
Agent: ✓ Created user Alice

You: Add her to the hiking group
Agent: ✓ Added Alice to hiking group
```

### Intelligent Suggestions

The agent can make smart suggestions:

```
You: When can we meet?
Agent: I found 3 time slots, but only 2 out of 5 members have provided 
       availability. Would you like me to remind the others to add theirs?
```

### Error Handling

The agent handles errors gracefully:

```
You: Add Bob to the group
Agent: I don't see a user named Bob. Would you like to create one first?
```

## Integration with Existing Systems

### ADK Playground

The agent is automatically available in the ADK playground:

```bash
make playground
```

This gives you a web UI with:
- Chat interface
- Session management
- Feedback collection
- Tracing and debugging

### Agent Engine Deployment

Deploy to Vertex AI Agent Engine:

```bash
make deploy
```

Then access via:
- REST API
- gRPC
- Web interface

### Custom Integrations

You can integrate the agent into:
- **Slack**: Create a Slack bot
- **Discord**: Create a Discord bot
- **SMS**: Use Twilio
- **WhatsApp**: Use WhatsApp Business API
- **Web App**: Embed in your React/Vue app
- **Mobile App**: Use the REST API

## Tips for Best Results

### Be Specific

❌ "Plan something"
✅ "Plan a hiking event for my Weekend Warriors group next Saturday at 10am"

### Use Names

❌ "Add user abc-123-def to group xyz-456"
✅ "Add Alice to the Weekend Warriors group"

### Provide Context

❌ "When can we meet?"
✅ "When can my Weekend Warriors group meet for a 2-hour event?"

### Ask Follow-up Questions

The agent is conversational! If you're not sure, just ask:
- "What groups do I have?"
- "Who's in my hiking group?"
- "What events are coming up?"

## Troubleshooting

### Agent doesn't understand

Try rephrasing more explicitly:
- Instead of: "Set it up"
- Try: "Create a hiking event called Mountain Adventure"

### Missing information

The agent will ask for clarification:
```
You: Create a user
Agent: I'd be happy to help! What's the user's name and email?
```

### Tool errors

If a tool fails, the agent will explain:
```
Agent: I tried to create the group, but the creator 'Alice' wasn't found. 
       Would you like to create Alice first?
```

## Performance

- **Response time**: 1-3 seconds typical
- **Streaming**: Responses stream in real-time
- **Context**: Maintains conversation history
- **Accuracy**: High with clear instructions

## Future Enhancements

Potential improvements:
- **Proactive suggestions**: "Your group hasn't planned anything in a while..."
- **Smart scheduling**: "Based on past events, your group prefers Saturday mornings"
- **Conflict resolution**: "Bob can't make it. Should we reschedule or proceed?"
- **Multi-modal**: Show maps, calendars, photos
- **Voice interface**: Talk to the agent
- **Notifications**: "Alice just updated her availability!"

## Development

### Adding New Tools

1. Create a new tool function in `agent_tools.py`:

```python
def my_new_tool(param: str) -> str:
    """
    Description of what this tool does.
    
    Args:
        param: Description of parameter
    
    Returns:
        Description of return value
    """
    # Implementation
    return "Result"
```

2. Add to `EVENT_PLANNING_TOOLS` list

3. The agent automatically gets access!

### Testing Tools

Test individual tools:

```python
from app.event_planning.agent_tools import create_user_tool

result = create_user_tool("Alice", "alice@example.com")
print(result)
```

### Debugging

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Resources

- [Google ADK Documentation](https://cloud.google.com/vertex-ai/docs/agent-builder)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Event Planning Service Code](./services/event_planning_service.py)
- [Agent Tools Code](./agent_tools.py)

## Support

Questions? Issues?
- Check the logs in the chat interface
- Review tool docstrings in `agent_tools.py`
- Test tools individually before using in conversation
- Use the ADK playground for debugging

Happy event planning! 🎉
