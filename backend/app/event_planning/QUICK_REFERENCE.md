# Event Planning Agent - Quick Reference

## 🚀 Start the Agent

```bash
# Terminal chat interface
uv run python app/event_planning/chat_interface.py

# Web UI (ADK Playground)
make playground

# Test tools
uv run python app/event_planning/test_agent_tools.py
```

## 💬 Common Commands

### Users
```
Create a user named Alice with email alice@example.com
Show me all users
Update my preferences - I like hiking and dining
I'm available Saturday 2pm to 6pm
```

### Groups
```
Create a hiking group called Weekend Warriors
Add Bob to the Weekend Warriors group
Show me all my groups
Who's in the Weekend Warriors group?
```

### Events
```
When can my Weekend Warriors group meet?
Plan a hiking event for Saturday at 10am
Create a dinner event at Italian Bistro
Finalize the Saturday Hike event
Show me all events
```

### Feedback
```
Rate the Saturday Hike event 5 stars
Submit feedback: it was amazing!
```

## 🎯 Tips

- **Use names** instead of IDs: "Add Alice" not "Add user-123"
- **Be specific**: "Plan a hike Saturday at 10am" not "plan something"
- **Ask questions**: The agent is conversational!
- **Natural language**: Talk like you're texting a friend

## 🛠️ Tools Available

1. `create_user_tool` - Create users
2. `list_users_tool` - List users
3. `update_user_preferences_tool` - Set preferences
4. `add_availability_tool` - Add availability
5. `create_group_tool` - Create groups
6. `list_groups_tool` - List groups
7. `get_group_details_tool` - Group info
8. `find_optimal_time_tool` - Find times
9. `create_event_tool` - Create events
10. `finalize_event_tool` - Confirm events
11. `list_events_tool` - List events
12. `submit_feedback_tool` - Submit feedback

## 📚 More Info

- Full docs: `app/event_planning/CONVERSATIONAL_AI.md`
- Setup guide: `CONVERSATIONAL_AI_SETUP.md`
- Tool code: `app/event_planning/agent_tools.py`
