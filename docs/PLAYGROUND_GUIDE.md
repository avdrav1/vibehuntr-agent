# ADK Playground Guide

## Starting the Playground

The Vibehuntr playground provides a custom-branded Streamlit interface for interacting with the event planning agent.

```bash
make playground
# or
./start_playground.sh
# or directly
streamlit run vibehuntr_playground.py
```

Then open: **http://localhost:8501**

## ⚠️ Important Setup

### 1. Configure Environment Variables

The playground requires specific environment variables to function. Create or update your `.env` file in the project root:

```bash
# Required: Google API Key for Gemini
GOOGLE_API_KEY=your-api-key-here

# Optional: Agent Configuration
USE_DOCUMENT_RETRIEVAL=false

# Optional: GCP Configuration (for production deployments)
GOOGLE_CLOUD_PROJECT=your-project-id
DATA_STORE_ID=your-datastore-id

# Optional: Google Places API (for venue search)
GOOGLE_PLACES_API_KEY=your-places-api-key
```

#### Environment Variable Details

**GOOGLE_API_KEY** (Required)
- Your Gemini API key for LLM access
- Get one at: https://aistudio.google.com/app/apikey
- Used by both full and simple agents

**USE_DOCUMENT_RETRIEVAL** (Optional, default: false)
- Controls which agent is loaded
- `true`: Uses full agent with document retrieval (`app/agent.py`)
- `false`: Uses simple agent with event planning only (`app/event_planning/simple_agent.py`)
- Simple agent is recommended for local development

**GOOGLE_CLOUD_PROJECT** (Optional)
- Your GCP project ID
- Only needed when `USE_DOCUMENT_RETRIEVAL=true`
- Required for Vertex AI Search integration

**DATA_STORE_ID** (Optional)
- Vertex AI Search datastore ID
- Only needed when `USE_DOCUMENT_RETRIEVAL=true`
- Used for document retrieval features

**GOOGLE_PLACES_API_KEY** (Optional)
- Google Places API key for venue search
- Only needed if using venue discovery features
- See `GOOGLE_PLACES_SETUP.md` for setup instructions

### 2. Verify Your Setup

Check that your environment is configured correctly:

```bash
# Load environment variables
source .env

# Verify API key is set
echo $GOOGLE_API_KEY

# Verify agent configuration
echo $USE_DOCUMENT_RETRIEVAL
```

### 3. Start Chatting!

Once the playground loads:
1. You'll see the Vibehuntr branded interface
2. Type your message in the chat input at the bottom
3. Press Enter or click Send
4. Watch the agent respond in real-time

## 💬 What to Try

### User Management
```
Create a user for me named Alice with email alice@example.com
Show me all users
```

### Group Management
```
Create a hiking group called Weekend Warriors with Alice as creator
Show me all my groups
Who's in the Weekend Warriors group?
```

### Event Planning
```
When can my Weekend Warriors group meet?
Plan a hiking event for next Saturday at 10am
Show me all events
```

## 🐛 Troubleshooting

> **📖 For comprehensive troubleshooting, see [PLAYGROUND_TROUBLESHOOTING.md](PLAYGROUND_TROUBLESHOOTING.md)**

This section covers common issues. For detailed troubleshooting, architecture-specific issues, and advanced debugging, see the full troubleshooting guide.

### Agent Loading Issues

**Problem: "Error loading agent" or "Agent not properly configured"**

**Solution:**
1. Check your `GOOGLE_API_KEY` is set in `.env`
2. Verify the API key is valid at https://aistudio.google.com/app/apikey
3. Restart the playground:
   ```bash
   # Stop with Ctrl+C, then:
   make playground
   ```

**Problem: "ImportError: No module named 'app.agent'" or "No module named 'app.event_planning.simple_agent'"**

**Solution:**
1. Ensure you're running from the project root directory
2. Check that `USE_DOCUMENT_RETRIEVAL` is set correctly:
   - For local dev: `USE_DOCUMENT_RETRIEVAL=false` (uses simple agent)
   - For full features: `USE_DOCUMENT_RETRIEVAL=true` (requires GCP setup)
3. Verify the agent files exist:
   ```bash
   ls app/agent.py
   ls app/event_planning/simple_agent.py
   ```

### Environment Variable Issues

**Problem: Environment variables not loading**

**Solution:**
1. Make sure `.env` file exists in project root
2. Export variables manually before starting:
   ```bash
   export GOOGLE_API_KEY="your-key-here"
   export USE_DOCUMENT_RETRIEVAL=false
   make playground
   ```
3. Or use the start script which loads `.env` automatically:
   ```bash
   ./start_playground.sh
   ```

**Problem: "Missing key inputs" or API authentication errors**

**Solution:**
1. Verify your API key format (should be a long alphanumeric string)
2. Check for extra spaces or quotes in `.env`:
   ```bash
   # Correct format:
   GOOGLE_API_KEY=AIzaSyAbc123...
   
   # Incorrect (no quotes needed):
   GOOGLE_API_KEY="AIzaSyAbc123..."
   ```
3. Regenerate your API key if it's expired

### Streaming and Response Issues

**Problem: Agent response appears slowly or freezes**

**Solution:**
1. This is normal for first response (3-5 seconds)
2. Check your internet connection
3. For very slow responses, try:
   - Using a shorter message
   - Clearing conversation history (click "New Conversation")
   - Restarting the playground

**Problem: "Connection Error: Unable to reach the agent"**

**Solution:**
1. Check internet connectivity
2. Verify Gemini API is accessible:
   ```bash
   curl -H "Content-Type: application/json" \
        -d '{"contents":[{"parts":[{"text":"test"}]}]}' \
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=$GOOGLE_API_KEY"
   ```
3. Check for firewall or proxy issues
4. Try again in a few minutes (temporary API issues)

### Session and History Issues

**Problem: Conversation history not maintained**

**Solution:**
1. This is expected behavior - history is session-based
2. History clears on page refresh (by design)
3. Use "New Conversation" button to intentionally clear history
4. For persistent history, see Future Enhancements in design doc

**Problem: "Show Older Messages" not appearing**

**Solution:**
1. This only appears when you have more than 10 messages
2. Send more messages to see the feature
3. Recent 10 messages always show by default

### UI and Display Issues

**Problem: Chat input not visible or stuck at top**

**Solution:**
1. Scroll to bottom of page
2. Refresh the browser (Ctrl+R or Cmd+R)
3. Try a different browser (Chrome recommended)
4. Clear browser cache

**Problem: Vibehuntr styling not applied**

**Solution:**
1. Check that `app/playground_style.py` exists
2. Restart the playground
3. Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)

**Problem: Error messages not displaying properly**

**Solution:**
1. Check browser console for JavaScript errors (F12)
2. Ensure Streamlit version is compatible:
   ```bash
   uv run streamlit --version
   ```
3. Update dependencies if needed:
   ```bash
   make install
   ```

### Agent Behavior Issues

**Problem: "Agent doesn't understand me" or gives irrelevant responses**

**Solution:**
1. Be specific and clear:
   - ❌ "Do something"
   - ✅ "Create a user named Alice with email alice@example.com"
2. Use natural language but be explicit about what you want
3. Reference previous context: "Add Bob to that group"
4. Check that you're using the right agent:
   - Simple agent: Event planning, user/group management
   - Full agent: Above + document retrieval

**Problem: Tool execution errors**

**Solution:**
1. Check that data directories exist:
   ```bash
   mkdir -p data/users data/groups data/events data/feedback
   ```
2. Verify file permissions:
   ```bash
   chmod -R 755 data/
   ```
3. Check logs for specific error details
4. Try a simpler request first to verify agent is working

### GCP and Document Retrieval Issues

**Problem: Document retrieval not working (USE_DOCUMENT_RETRIEVAL=true)**

**Solution:**
1. Verify GCP credentials are configured:
   ```bash
   gcloud auth application-default login
   ```
2. Check required environment variables:
   ```bash
   echo $GOOGLE_CLOUD_PROJECT
   echo $DATA_STORE_ID
   ```
3. Ensure Vertex AI Search is set up (see deployment docs)
4. For local dev, use `USE_DOCUMENT_RETRIEVAL=false` instead

### Performance Issues

**Problem: Playground is slow or unresponsive**

**Solution:**
1. Clear conversation history (click "New Conversation")
2. Restart the playground
3. Check system resources (CPU, memory)
4. Close other browser tabs
5. For very long conversations, start fresh

### Duplicate Messages Issue

**Problem: Messages appearing multiple times in chat**

**Solution:**
1. This should be fixed in the current version
2. If you still see duplicates:
   - Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
   - Clear browser cache
   - Restart playground: Stop (Ctrl+C) and run `make playground` again
3. Check that you're running the latest version:
   ```bash
   git pull origin main
   make install
   make playground
   ```
4. Verify `is_processing` flag is working:
   - Check terminal logs for "Processing flag" messages
   - Should see "Processing: True" then "Processing: False"

**Root Cause:**
- Streamlit reruns can cause inline messages to persist
- Fixed by clearing inline containers before rerun
- Processing flag prevents duplicate processing

### Context Loss Issue

**Problem: Agent forgets previous conversation**

**Solution:**
1. This should be fixed in the current version
2. If agent still forgets:
   - Verify session ID is consistent:
     ```python
     # Check in terminal logs
     # Should see same session_id throughout conversation
     ```
   - Check ADK version:
     ```bash
     uv run python -c "import google.adk; print(google.adk.__version__)"
     # Should be >= 1.15.0
     ```
   - Test with simple conversation:
     - Send: "My name is Alice"
     - Send: "What's my name?"
     - Agent should respond with "Alice"
3. If still not working:
   - Click "New Conversation" to reset
   - Restart playground
   - Check logs for session service errors

**Root Cause:**
- ADK's InMemorySessionService manages agent context
- Session ID must be consistent throughout conversation
- Fixed by proper session ID management and ADK integration

### State Corruption Issue

**Problem: "Session reset" or "Invalid state" errors**

**Solution:**
1. Click "New Conversation" button
2. If that doesn't work, restart playground:
   ```bash
   # Stop with Ctrl+C
   make playground
   ```
3. Clear browser storage:
   - Open browser DevTools (F12)
   - Application tab → Storage → Clear site data
   - Refresh page
4. Check for conflicting browser extensions:
   - Try in incognito/private mode
   - Disable extensions that modify page content

**Root Cause:**
- Streamlit session state can become corrupted
- Usually caused by browser refresh during processing
- Fixed by proper state initialization and error recovery

### Still Having Issues?

If none of the above solutions work:

1. **Check the logs:**
   ```bash
   # Playground logs appear in terminal where you ran it
   # Look for ERROR or WARNING messages
   ```

2. **Test with minimal config:**
   ```bash
   # Create a minimal .env
   echo "GOOGLE_API_KEY=your-key" > .env
   echo "USE_DOCUMENT_RETRIEVAL=false" >> .env
   make playground
   ```

3. **Try the alternative CLI interface:**
   ```bash
   uv run python app/event_planning/chat_interface.py
   ```

4. **Verify installation:**
   ```bash
   make install
   make test
   ```

5. **Run diagnostic tests:**
   ```bash
   # Test session manager
   uv run pytest tests/unit/test_clear_session.py -v
   
   # Test agent invoker
   uv run pytest tests/unit/test_agent_invoker.py -v
   
   # Test playground integration
   uv run pytest tests/integration/test_playground_integration.py -v
   ```

6. **Check GitHub issues or create a new one with:**
   - Error messages from terminal
   - Your `.env` configuration (without API keys!)
   - Steps to reproduce the issue
   - Browser and OS information
   - Output from diagnostic tests

## 🎯 Features

The Vibehuntr playground provides:

### Core Features
- **Real-time Streaming** - See agent responses as they're generated
- **Session Management** - Conversation context maintained during your session
- **History Pagination** - Recent 10 messages shown by default, older messages accessible via expander
- **New Conversation** - Clear history and start fresh anytime
- **Error Handling** - User-friendly error messages with recovery options
- **Vibehuntr Branding** - Custom styling and visual identity

### Agent Capabilities
- **User Management** - Create and manage users
- **Group Management** - Create groups, add members, manage permissions
- **Event Planning** - Schedule events, check availability, coordinate groups
- **Venue Discovery** - Search for venues using Google Places (if configured)
- **Document Retrieval** - Search knowledge base (if full agent enabled)

### Developer Features
- **Auto-reload** - Code changes trigger automatic agent reload
- **Status Indicators** - Visual feedback for agent processing state
- **Error Logging** - Detailed logs for debugging
- **Dual Agent Support** - Switch between simple and full agent modes

## 🔄 Agent Configuration

### Simple Agent (Default)

Best for local development and event planning features.

```bash
# In .env
USE_DOCUMENT_RETRIEVAL=false
```

**Includes:**
- Event planning tools
- User and group management
- Google Places integration (if API key provided)
- No GCP dependencies

### Full Agent (Advanced)

Includes document retrieval via Vertex AI Search.

```bash
# In .env
USE_DOCUMENT_RETRIEVAL=true
GOOGLE_CLOUD_PROJECT=your-project-id
DATA_STORE_ID=your-datastore-id
```

**Includes:**
- All simple agent features
- Document retrieval from Vertex AI Search
- RAG (Retrieval Augmented Generation)
- Requires GCP setup

### Switching Agents

1. Update `USE_DOCUMENT_RETRIEVAL` in `.env`
2. Restart the playground
3. Agent will reload with new configuration

## 📊 Understanding the Interface

### Message Display
- **Recent Messages**: Last 10 messages shown by default
- **Older Messages**: Click "Show Older Messages" expander to see full history
- **User Messages**: Your inputs displayed on the right
- **Agent Messages**: Agent responses on the left with streaming animation

### Status Indicators
- **Thinking Spinner**: Agent is processing your request
- **Streaming Animation**: Response is being generated
- **Completion**: Response finished, ready for next input
- **Error Badge**: Something went wrong, see error message

### Controls
- **Chat Input**: Type your message at the bottom
- **Send Button**: Submit your message (or press Enter)
- **New Conversation**: Clear history and start fresh
- **Show Older Messages**: Expand to see messages beyond recent 10

## 📝 Example Configuration

### Minimal Setup (Recommended for Local Dev)

Create a `.env` file in the project root:

```bash
# .env - Minimal configuration for local development

# Required: Gemini API Key
GOOGLE_API_KEY=AIzaSyAbc123YourActualKeyHere456

# Use simple agent (no GCP required)
USE_DOCUMENT_RETRIEVAL=false
```

### Full Setup (With Document Retrieval)

```bash
# .env - Full configuration with document retrieval

# Required: Gemini API Key
GOOGLE_API_KEY=AIzaSyAbc123YourActualKeyHere456

# Enable document retrieval
USE_DOCUMENT_RETRIEVAL=true

# GCP Configuration
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
DATA_STORE_ID=your-vertex-ai-datastore-id

# Optional: Google Places API
GOOGLE_PLACES_API_KEY=AIzaSyDef789YourPlacesKeyHere012
```

### Complete Setup (All Features)

```bash
# .env - Complete configuration with all features

# ===== Required =====
GOOGLE_API_KEY=AIzaSyAbc123YourActualKeyHere456

# ===== Agent Configuration =====
USE_DOCUMENT_RETRIEVAL=true

# ===== GCP Configuration =====
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
DATA_STORE_ID=your-vertex-ai-datastore-id

# ===== Optional APIs =====
GOOGLE_PLACES_API_KEY=AIzaSyDef789YourPlacesKeyHere012

# ===== Optional: Observability =====
# ENABLE_TRACING=true
# GOOGLE_CLOUD_TRACE_PROJECT=your-project-id

# ===== Optional: Development =====
# LOG_LEVEL=DEBUG
# STREAMLIT_SERVER_PORT=8501
```

### Getting API Keys

**Gemini API Key (GOOGLE_API_KEY)**
1. Go to https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key to your `.env` file

**Google Places API Key (GOOGLE_PLACES_API_KEY)**
1. Go to https://console.cloud.google.com/apis/credentials
2. Create credentials → API Key
3. Enable Google Places API (New)
4. Copy the key to your `.env` file
5. See `GOOGLE_PLACES_SETUP.md` for detailed instructions

**GCP Setup (for Document Retrieval)**
1. Create a GCP project
2. Enable Vertex AI Search API
3. Create a datastore and note the ID
4. Set up authentication:
   ```bash
   gcloud auth application-default login
   ```

## 🚀 Alternative Interfaces

If the playground doesn't work, try these alternatives:

### Terminal Chat Interface

Interactive chat in your terminal:

```bash
uv run python app/event_planning/chat_interface.py
```

**Features:**
- Same agent capabilities
- No browser required
- Faster for quick testing
- Better for debugging

### Interactive Menu (No API Key Needed)

Test data models without API calls:

```bash
uv run python cli/interactive_menu.py
```

**Features:**
- No API key required
- Direct data manipulation
- Test repositories and models
- Good for offline development

### ADK Web Playground (Standard)

Use the standard ADK playground:

```bash
adk web
```

**Features:**
- Standard ADK interface
- Multi-agent support
- Built-in debugging tools
- Requires selecting "app" folder in UI

## 💡 Tips and Best Practices

### Conversation Tips
1. **Be patient** - First response can take 3-5 seconds while agent initializes
2. **Be specific** - "Create a user named Alice with email alice@example.com" works better than "add someone"
3. **Ask questions** - "What groups do I have?" or "Show my events"
4. **Use context** - "Add Bob to that group" after creating a group
5. **Natural language** - The agent understands conversational requests

### Performance Tips
1. **Start fresh** - Click "New Conversation" if responses slow down
2. **Shorter messages** - Break complex requests into steps
3. **Check history** - Use "Show Older Messages" to review past context
4. **Simple agent** - Use `USE_DOCUMENT_RETRIEVAL=false` for faster local dev

### Development Tips
1. **Auto-reload** - Code changes reload automatically, no restart needed
2. **Check logs** - Terminal shows detailed error messages
3. **Test incrementally** - Test one feature at a time
4. **Use alternatives** - Try CLI interface if playground has issues

### Debugging Tips
1. **Check environment** - Verify `.env` variables are set correctly
2. **Read errors** - Error messages include helpful troubleshooting info
3. **Test API key** - Use simple request first: "Hello"
4. **Isolate issues** - Try minimal config to rule out configuration problems

## 🏗️ Architecture Overview

Understanding how the playground works:

```
User Input
    ↓
Streamlit UI (vibehuntr_playground.py)
    ↓
Session Manager (session_manager.py)
    ↓
Agent Loader (agent_loader.py) → Selects agent based on USE_DOCUMENT_RETRIEVAL
    ↓
Agent Invoker (agent_invoker.py) → Streams response
    ↓
ADK Agent (agent.py or simple_agent.py)
    ↓
Tools (event planning, places, etc.)
    ↓
Response streamed back to UI
```

### Hybrid State Management Pattern

The playground uses a **hybrid approach** that leverages the strengths of both Streamlit and ADK:

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Playground                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  UI Layer (vibehuntr_playground.py)                    │ │
│  │  - Display messages from Streamlit state              │ │
│  │  - Handle user input                                   │ │
│  │  - Manage UI state (processing flags, messages)        │ │
│  │  - Sync messages to both stores after response         │ │
│  └────────────────┬───────────────────────────────────────┘ │
│                   │                                          │
│  ┌────────────────▼───────────────────────────────────────┐ │
│  │  Session Manager (session_manager.py)                  │ │
│  │  - Manage Streamlit message history                    │ │
│  │  - Provide pagination and display helpers              │ │
│  │  - Cache agent instance                                │ │
│  └────────────────┬───────────────────────────────────────┘ │
│                   │                                          │
│  ┌────────────────▼───────────────────────────────────────┐ │
│  │  Agent Invoker (agent_invoker.py)                      │ │
│  │  - Invoke agent with ADK Runner                        │ │
│  │  - Stream responses                                    │ │
│  │  - Handle errors                                       │ │
│  │  - ADK Runner uses session service automatically       │ │
│  └────────────────┬───────────────────────────────────────┘ │
└───────────────────┼──────────────────────────────────────────┘
                    │
         ┌──────────▼──────────┐
         │  ADK Session Service │
         │  (InMemorySessionService) │
         │  - Automatically maintains agent context │
         │  - Used by ADK Runner internally │
         └─────────────────────┘
```

**Key Principles:**

1. **ADK session service**: Handles agent context automatically (no manual history passing)
2. **Streamlit session state**: Manages message history for UI display
3. **Sync on each turn**: After agent responds, messages exist in both stores
4. **Clear separation**: ADK = agent memory, Streamlit = UI state
5. **UI state separate**: Processing flags, agent cache kept in Streamlit state

**Why Hybrid Works:**

- **ADK Runner** already handles agent context automatically via session service
- **Streamlit** naturally handles UI display, pagination, and state management
- **Simpler** than trying to query ADK's internal session state
- **Clear ownership**: Each system manages what it's good at
- **Solves critical issues**: Eliminates duplicate messages AND preserves conversation context

### Single Source of Truth Pattern

The architecture follows a **single source of truth** pattern for different concerns:

**For Agent Context (ADK Session Service):**
- ADK's InMemorySessionService is the single source of truth for agent memory
- ADK Runner automatically provides conversation history to the agent
- No manual history passing required
- Session ID ensures continuity across turns

**For UI Display (Streamlit Session State):**
- Streamlit session state is the single source of truth for UI display
- Messages stored in `st.session_state.messages`
- Pagination, filtering, and display logic use this state
- Independent of ADK's internal state

**Sync Strategy:**
- After each agent response, messages are added to BOTH stores
- Each store maintains its own copy for its specific purpose
- No cross-querying between stores (clean separation)
- Processing flag prevents duplicate processing on reruns

**Benefits:**
- ✅ No duplicate messages in UI
- ✅ Agent remembers full conversation history
- ✅ Clear separation of concerns
- ✅ Easy to test each component independently
- ✅ Maintainable and extensible

### Key Components

**Session Manager**
- Manages conversation history for UI display
- Caches agent instance for performance
- Handles pagination (10 recent messages by default)
- Provides helper methods for message management
- **Does NOT** interact with ADK session service (separation of concerns)

**Agent Loader**
- Selects appropriate agent based on `USE_DOCUMENT_RETRIEVAL`
- Handles import errors gracefully
- Provides fallback behavior
- Caches loaded agent in session state

**Agent Invoker**
- Invokes agent with ADK Runner
- Streams responses token-by-token for real-time display
- Handles errors gracefully with user-friendly messages
- **Does NOT** manually pass chat history (ADK handles this automatically)
- Uses session ID for conversation continuity

**Vibehuntr Styling**
- Custom CSS from `playground_style.py`
- Branded colors and fonts
- Responsive layout
- Professional appearance

### Message Flow

**User Sends Message:**
1. User types message in chat input
2. Processing flag set to prevent duplicate processing
3. Message added to Streamlit state
4. Message displayed inline immediately
5. Agent invoked with session ID (ADK provides history automatically)

**Agent Responds:**
1. Response streamed token-by-token
2. Displayed inline with cursor animation
3. Full response added to Streamlit state
4. Inline containers cleared
5. Processing flag reset
6. Page reruns to display clean history

**On Rerun:**
1. All messages displayed from Streamlit state
2. No duplicates (inline containers were cleared)
3. Agent has full context from ADK session service
4. Ready for next user input

### Error Handling Architecture

**Error Categories:**

1. **Agent Invocation Errors**
   - API failures, timeouts, rate limits
   - Display: User-friendly error message
   - Log: Full error with context (session ID, timestamp, message)
   - Recovery: Allow retry

2. **Session Errors**
   - Session not found, session creation failure
   - Display: "Starting new conversation..."
   - Recovery: Create new session automatically
   - Log: Session error details

3. **Streaming Errors**
   - Connection drops during streaming
   - Display: Partial response + error message
   - Preserve: Partial response in history
   - Recovery: Allow continuation

4. **State Corruption**
   - Invalid session state
   - Display: "Session reset. Please start over."
   - Recovery: Reset to clean state
   - Log: State corruption details

**Error Handling Pattern:**
```python
try:
    # Operation
    pass
except SpecificError as e:
    # Log with context
    logger.error(f"Error: {e}", extra={
        "session_id": session_id,
        "timestamp": datetime.now(),
        "user_message": message[:100]
    })
    
    # Display user-friendly message
    st.error("🚫 User-friendly message")
    
    # Attempt recovery if possible
    recover_from_error()
```

### State Management Details

**Streamlit Session State Structure:**
```python
st.session_state = {
    "session_id": str,                    # ADK session ID (UUID)
    "messages": List[Dict[str, str]],     # Message history for display
    "agent": Agent,                       # Cached agent instance
    "is_processing": bool,                # Prevent duplicate processing
    "session_manager": SessionManager     # Session manager instance
}
```

**Message Format:**
```python
{
    "role": str,      # "user" or "assistant"
    "content": str    # Message text
}
```

**ADK Session Service:**
- Managed internally by ADK Runner
- Automatically maintains conversation history
- Accessed via session ID
- No direct manipulation required

### Performance Considerations

**Caching:**
- Agent instance cached in session state (avoid reload on every message)
- Session manager cached in session state
- Messages stored in memory (fast access)

**Streaming:**
- Token-by-token streaming for responsive UI
- Cursor animation during generation
- No blocking operations

**Pagination:**
- Recent 10 messages shown by default
- Older messages in collapsible expander
- Reduces initial render time for long conversations

**Auto-reload:**
- Code changes trigger automatic agent reload
- No need to restart playground during development
- Preserves session state across reloads

## 🎉 Use Cases

The playground is perfect for:

### Development
- **Testing new features** - Try agent capabilities interactively
- **Debugging tools** - See tool execution in real-time
- **Iterating quickly** - Auto-reload on code changes
- **Validating behavior** - Test edge cases and error handling

### Demonstration
- **Showcasing capabilities** - Natural conversation interface
- **Client demos** - Branded, professional appearance
- **Feature walkthroughs** - Show event planning workflow
- **Proof of concept** - Validate ideas quickly

### Learning
- **Understanding ADK** - See how agents work
- **Exploring tools** - Discover available functions
- **Testing prompts** - Experiment with different requests
- **Studying responses** - Learn agent behavior patterns

## 📚 Additional Documentation

### Architecture & Design
- **[Design Document](.kiro/specs/playground-fix/design.md)** - Detailed architecture and design decisions
- **[Requirements](.kiro/specs/playground-fix/requirements.md)** - Feature requirements and acceptance criteria
- **[Bug Fix Details](BUGFIX_DUPLICATE_RESPONSES.md)** - Technical details of duplicate message fix

### Troubleshooting & Support
- **[Troubleshooting Guide](PLAYGROUND_TROUBLESHOOTING.md)** - Comprehensive troubleshooting for all issues
- **[Manual Testing Guide](MANUAL_TESTING_GUIDE.md)** - Manual testing procedures
- **[Testing Summary](TESTING_SUMMARY.md)** - Overview of test coverage

### Development
- **[Implementation Tasks](.kiro/specs/playground-fix/tasks.md)** - Implementation plan and task list
- **[Implementation Status](.kiro/specs/playground-fix/IMPLEMENTATION_STATUS.md)** - Current implementation status

### Related Features
- **[Google Places Setup](GOOGLE_PLACES_SETUP.md)** - Setting up venue search
- **[Conversational AI Setup](CONVERSATIONAL_AI_SETUP.md)** - Conversational AI configuration

## 🎯 Key Takeaways

### Single Source of Truth Pattern

The playground follows a **single source of truth** pattern:

- **For Agent Context**: ADK session service is the single source
  - Automatically maintains conversation history
  - Provides context to agent on each turn
  - Managed by ADK Runner internally

- **For UI Display**: Streamlit session state is the single source
  - Stores messages for display
  - Handles pagination and filtering
  - Independent of ADK's internal state

- **Sync Strategy**: Messages added to both stores after each response
  - Each store maintains its own copy
  - No cross-querying between stores
  - Processing flag prevents duplicate processing

### Why This Matters

Understanding this pattern helps you:
- **Debug issues**: Know where to look for problems
- **Extend features**: Add new functionality correctly
- **Maintain code**: Understand the architecture
- **Avoid bugs**: Follow established patterns

### Best Practices

1. **Never manually modify ADK session service** - Let ADK Runner handle it
2. **Always use SessionManager** for UI state changes
3. **Use processing flag** to prevent concurrent operations
4. **Clear inline containers** before rerun to prevent duplicates
5. **Maintain consistent session ID** throughout conversation

Enjoy planning events with Vibehuntr! 🎊
