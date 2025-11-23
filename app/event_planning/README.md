# Event Planning System

A comprehensive event planning system with both traditional CLI and conversational AI interfaces.

## 🚀 Quick Start

### 1. Choose Your Interface

**Conversational AI (Natural Language)**
```bash
# Requires: Google Cloud auth OR Gemini API key
export GOOGLE_API_KEY="your-key"  # Get from https://aistudio.google.com/app/apikey
uv run python app/event_planning/chat_interface.py
```

**Interactive Menu (No Auth Required)**
```bash
# Works immediately, no setup needed!
uv run python cli/interactive_menu.py
```

### 2. Start Planning!

Both interfaces let you:
- Create users and set preferences
- Form friend groups
- Find optimal meeting times
- Plan and finalize events
- Submit feedback

## 📚 Documentation

- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Fix common issues
- **[CONVERSATIONAL_AI.md](./CONVERSATIONAL_AI.md)** - Full AI guide
- **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - Command reference
- **[demo_conversation.md](./demo_conversation.md)** - Example chat

## 🎯 Which Interface Should I Use?

| Feature | Interactive Menu | Conversational AI |
|---------|-----------------|-------------------|
| Setup Required | ❌ None | ✅ API Key or GCP |
| Natural Language | ❌ No | ✅ Yes |
| Menu Navigation | ✅ Yes | ❌ No |
| Select by Name | ✅ Yes | ✅ Yes |
| Best For | Quick tasks | Exploration |

## 🛠️ Architecture

```
┌─────────────────────────────────────┐
│   User Interfaces                   │
│   - Conversational AI (chat)        │
│   - Interactive Menu (TUI)          │
│   - Command Line (scripts)          │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│   Event Planning Service            │
│   - User Management                 │
│   - Group Management                │
│   - Event Planning                  │
│   - Feedback Processing             │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│   Data Layer                        │
│   - JSON File Storage               │
│   - Repository Pattern              │
└─────────────────────────────────────┘
```

## 🧪 Testing

```bash
# Test the tools
uv run python app/event_planning/test_agent_tools.py

# Run all tests
uv run pytest tests/unit tests/integration tests/property
```

## 📖 Example Usage

### Interactive Menu
```
1. User Management → Create User → Enter details
2. Group Management → Create Group → Select members
3. Event Management → Create Event → Enter details
4. Event Management → Finalize Event → Confirm
```

### Conversational AI
```
You: Create a user named Alice with email alice@example.com
Agent: ✓ Created user profile for Alice!

You: Create a hiking group called Weekend Warriors
Agent: ✓ Created group 'Weekend Warriors'!

You: When can my group meet?
Agent: Found 3 optimal time slots...
```

## 🎉 Features

- ✅ **78 passing tests** (unit + integration + property-based)
- ✅ **Natural language** understanding
- ✅ **Smart scheduling** with conflict resolution
- ✅ **Preference learning** from feedback
- ✅ **Consensus scoring** for group decisions
- ✅ **Production ready** with proper error handling

## 🐛 Troubleshooting

**"Missing key inputs argument"**
→ See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md#issue-missing-key-inputs-argument)

**Agent doesn't respond**
→ Check internet connection and API key

**Tools fail**
→ Ensure `data/` directory exists and is writable

## 📞 Need Help?

1. Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
2. Try the interactive menu (no auth required)
3. Run the test script to verify setup

Happy event planning! 🎊
