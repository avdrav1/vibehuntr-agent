# Playground Troubleshooting Guide

This guide provides detailed troubleshooting steps for common issues with the Vibehuntr Streamlit playground.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Common Issues](#common-issues)
  - [Duplicate Messages](#duplicate-messages)
  - [Context Loss](#context-loss)
  - [State Corruption](#state-corruption)
  - [Agent Loading Errors](#agent-loading-errors)
  - [Streaming Issues](#streaming-issues)
  - [Session Errors](#session-errors)
- [Architecture-Specific Issues](#architecture-specific-issues)
- [Advanced Debugging](#advanced-debugging)
- [Getting Help](#getting-help)

## Quick Diagnostics

Run these commands to quickly diagnose common issues:

```bash
# 1. Check environment variables
source .env
echo "API Key set: $([ -n "$GOOGLE_API_KEY" ] && echo "Yes" || echo "No")"
echo "Agent mode: $USE_DOCUMENT_RETRIEVAL"

# 2. Verify installation
make install
uv run python -c "import google.adk; print(f'ADK version: {google.adk.__version__}')"

# 3. Run diagnostic tests
uv run pytest tests/unit/test_clear_session.py -v
uv run pytest tests/unit/test_agent_invoker.py -v
uv run pytest tests/integration/test_playground_integration.py -v

# 4. Check for syntax errors
uv run python -m py_compile vibehuntr_playground.py
uv run python -m py_compile app/event_planning/session_manager.py
uv run python -m py_compile app/event_planning/agent_invoker.py
```

## Common Issues

### Duplicate Messages

**Symptoms:**
- Messages appear 2-3 times in the chat interface
- Previous messages reappear when sending new messages
- Chat history shows duplicates

**Root Cause:**
Streamlit's rerun mechanism can cause inline-displayed messages to persist and then be displayed again from history.

**Solutions:**

1. **Verify you're on the latest version:**
   ```bash
   git pull origin main
   make install
   make playground
   ```

2. **Clear browser cache:**
   - Hard refresh: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
   - Or clear cache manually:
     - Chrome: Settings → Privacy → Clear browsing data
     - Firefox: Settings → Privacy → Clear Data
     - Safari: Develop → Empty Caches

3. **Check processing flag:**
   Look for these log messages in terminal:
   ```
   Processing flag: True
   Processing flag: False
   ```
   If you don't see these, the processing flag may not be working.

4. **Restart playground:**
   ```bash
   # Stop with Ctrl+C
   make playground
   ```

5. **Test with clean session:**
   - Click "New Conversation" button
   - Send a test message
   - Verify it appears only once

**Prevention:**
- Don't refresh browser during message processing
- Wait for responses to complete before sending next message
- Use "New Conversation" if you notice duplicates starting

**Technical Details:**
The fix uses a clear-and-rerun pattern:
1. Display messages from history
2. When user sends message: display inline
3. When agent responds: display inline
4. Clear inline containers
5. Rerun to display everything from history cleanly

See `BUGFIX_DUPLICATE_RESPONSES.md` for full technical details.

### Context Loss

**Symptoms:**
- Agent forgets previous conversation turns
- Agent asks same questions repeatedly
- Agent doesn't remember information you provided
- References to earlier messages don't work

**Root Cause:**
Mismatch between Streamlit's UI state and ADK's session management, or inconsistent session ID usage.

**Solutions:**

1. **Verify session ID consistency:**
   Check terminal logs for session ID:
   ```
   Session ID: abc-123-def-456
   ```
   Should be the same throughout the conversation.

2. **Check ADK version:**
   ```bash
   uv run python -c "import google.adk; print(google.adk.__version__)"
   ```
   Should be >= 1.15.0. If not:
   ```bash
   make install
   ```

3. **Test context retention:**
   - Send: "My name is Alice"
   - Send: "What's my name?"
   - Agent should respond with "Alice"
   
   If agent doesn't remember:
   - Check terminal logs for errors
   - Look for "Session service" errors
   - Verify session ID is consistent

4. **Restart with clean session:**
   ```bash
   # Stop playground
   # Clear any cached session data
   rm -rf .streamlit/cache
   # Restart
   make playground
   ```

5. **Verify ADK session service:**
   ```bash
   # Run session manager tests
   uv run pytest tests/property/test_properties_session_manager.py -v
   
   # Run context retention tests
   uv run pytest tests/property/test_properties_context_retention.py -v
   ```

**Prevention:**
- Don't refresh browser during conversation
- Use "New Conversation" to intentionally clear context
- Ensure stable internet connection (API calls need to complete)

**Technical Details:**
The fix uses a hybrid state management pattern:
- ADK's InMemorySessionService maintains agent context automatically
- Streamlit session state manages UI display
- Session ID ensures continuity across turns
- No manual history passing required

See `.kiro/specs/playground-fix/design.md` for architecture details.

### State Corruption

**Symptoms:**
- "Session reset" error messages
- "Invalid state" errors
- Playground becomes unresponsive
- Unexpected behavior after errors

**Root Cause:**
Streamlit session state can become corrupted due to browser refresh during processing, errors during state updates, or conflicting browser extensions.

**Solutions:**

1. **Click "New Conversation":**
   This resets the session state cleanly.

2. **Restart playground:**
   ```bash
   # Stop with Ctrl+C
   make playground
   ```

3. **Clear browser storage:**
   - Open DevTools (F12)
   - Application tab → Storage → Clear site data
   - Refresh page

4. **Try incognito/private mode:**
   This rules out browser extensions or cached data:
   - Chrome: Ctrl+Shift+N
   - Firefox: Ctrl+Shift+P
   - Safari: Cmd+Shift+N

5. **Check for conflicting extensions:**
   Disable extensions that:
   - Modify page content
   - Block scripts
   - Intercept network requests

6. **Verify state initialization:**
   Check terminal logs for:
   ```
   Initializing session state
   Session ID: ...
   Session manager created
   ```

**Prevention:**
- Don't refresh browser during message processing
- Wait for errors to resolve before continuing
- Use "New Conversation" if you encounter errors
- Keep browser and extensions updated

**Technical Details:**
State corruption is prevented by:
- Proper state initialization checks
- Error recovery mechanisms
- Processing flag to prevent concurrent operations
- Clean state reset on "New Conversation"

### Agent Loading Errors

**Symptoms:**
- "Error loading agent" message
- "Agent not properly configured" error
- "ImportError: No module named..." errors
- Playground starts but agent doesn't respond

**Root Cause:**
Missing environment variables, incorrect agent configuration, or missing dependencies.

**Solutions:**

1. **Check environment variables:**
   ```bash
   source .env
   echo "GOOGLE_API_KEY: $([ -n "$GOOGLE_API_KEY" ] && echo "Set" || echo "NOT SET")"
   echo "USE_DOCUMENT_RETRIEVAL: $USE_DOCUMENT_RETRIEVAL"
   ```

2. **Verify API key:**
   - Go to https://aistudio.google.com/app/apikey
   - Verify your key is active
   - Copy to `.env` file:
     ```bash
     GOOGLE_API_KEY=your-actual-key-here
     ```

3. **Check agent mode:**
   For local development, use simple agent:
   ```bash
   echo "USE_DOCUMENT_RETRIEVAL=false" >> .env
   ```

4. **Verify agent files exist:**
   ```bash
   ls -la app/agent.py
   ls -la app/event_planning/simple_agent.py
   ```

5. **Test agent loading:**
   ```bash
   # Test simple agent
   uv run python -c "from app.event_planning.simple_agent import root_agent; print('Simple agent loaded')"
   
   # Test full agent (if USE_DOCUMENT_RETRIEVAL=true)
   uv run python -c "from app.agent import root_agent; print('Full agent loaded')"
   ```

6. **Reinstall dependencies:**
   ```bash
   make install
   ```

7. **Check for import errors:**
   ```bash
   uv run python vibehuntr_playground.py --help
   # Should show Streamlit help, not import errors
   ```

**Prevention:**
- Always set `GOOGLE_API_KEY` in `.env`
- Use `USE_DOCUMENT_RETRIEVAL=false` for local dev
- Run `make install` after pulling updates
- Verify `.env` file is in project root

**Technical Details:**
Agent loading process:
1. Load environment variables from `.env`
2. Check `USE_DOCUMENT_RETRIEVAL` setting
3. Import appropriate agent module
4. Initialize agent with configuration
5. Cache agent in session state

See `app/event_planning/agent_loader.py` for implementation.

### Streaming Issues

**Symptoms:**
- Responses appear slowly or freeze
- No streaming animation (cursor)
- Responses appear all at once
- "Connection Error" messages

**Root Cause:**
Network issues, API rate limits, or streaming implementation problems.

**Solutions:**

1. **Check internet connection:**
   ```bash
   ping -c 3 generativelanguage.googleapis.com
   ```

2. **Verify API access:**
   ```bash
   curl -H "Content-Type: application/json" \
        -d '{"contents":[{"parts":[{"text":"test"}]}]}' \
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=$GOOGLE_API_KEY"
   ```

3. **Check for rate limits:**
   Look for these errors in terminal:
   - "Rate limit exceeded"
   - "Quota exceeded"
   - "Too many requests"
   
   If rate limited:
   - Wait a few minutes
   - Use shorter messages
   - Consider upgrading API quota

4. **Test streaming:**
   ```bash
   # Run streaming tests
   uv run pytest tests/property/test_properties_playground_ui.py::test_streaming_display_progression -v
   ```

5. **Check firewall/proxy:**
   - Verify no firewall blocking API access
   - Check proxy settings if behind corporate network
   - Try from different network if possible

6. **Restart playground:**
   ```bash
   make playground
   ```

**Prevention:**
- Ensure stable internet connection
- Avoid very long messages (>1000 words)
- Don't send messages too rapidly
- Monitor API quota usage

**Technical Details:**
Streaming implementation:
1. Agent invoked with streaming enabled
2. Tokens yielded as they arrive
3. UI updated with each token
4. Cursor animation shows progress
5. Final response added to history

See `app/event_planning/agent_invoker.py` for implementation.

### Session Errors

**Symptoms:**
- "Session not found" errors
- "Session creation failed" errors
- "Starting new conversation..." messages
- Session ID changes unexpectedly

**Root Cause:**
ADK session service errors, memory issues, or session lifecycle problems.

**Solutions:**

1. **Let automatic recovery work:**
   The system should automatically create a new session.
   Wait for "Starting new conversation..." message.

2. **Manually start new conversation:**
   Click "New Conversation" button.

3. **Check memory usage:**
   ```bash
   # Check if system is low on memory
   free -h  # Linux
   vm_stat  # Mac
   ```
   
   If low on memory:
   - Close other applications
   - Restart playground
   - Consider increasing system memory

4. **Verify session service:**
   ```bash
   # Run session tests
   uv run pytest tests/property/test_properties_session_manager.py -v
   ```

5. **Check for session service errors:**
   Look in terminal logs for:
   - "Session service error"
   - "Failed to create session"
   - "Session not found"

6. **Restart playground:**
   ```bash
   make playground
   ```

**Prevention:**
- Don't refresh browser during conversation
- Use "New Conversation" to intentionally reset
- Monitor system memory usage
- Keep conversations to reasonable length (<100 messages)

**Technical Details:**
Session lifecycle:
1. Session created on first message
2. Session ID stored in Streamlit state
3. ADK session service maintains history
4. Session persists until "New Conversation" or browser refresh
5. Automatic recovery creates new session on errors

## Architecture-Specific Issues

### Hybrid State Management

**Understanding the Architecture:**

The playground uses a hybrid approach:
- **Streamlit session state**: Manages UI display
- **ADK session service**: Manages agent context

**Common Misunderstandings:**

1. **"Why are messages stored in two places?"**
   - Streamlit state: For UI display, pagination, filtering
   - ADK session service: For agent memory, context retention
   - Each serves a different purpose

2. **"Why not use just one?"**
   - ADK session service is internal to ADK Runner
   - Streamlit naturally handles UI state
   - Hybrid approach leverages strengths of both

3. **"How are they kept in sync?"**
   - After each agent response, messages added to both
   - No cross-querying between stores
   - Processing flag prevents duplicate processing

**Troubleshooting Sync Issues:**

If messages appear in UI but agent doesn't remember:
1. Check session ID is consistent
2. Verify ADK session service is working
3. Run context retention tests

If agent remembers but UI doesn't show:
1. Check Streamlit session state
2. Verify messages being added to state
3. Check for display logic errors

### Single Source of Truth Pattern

**Understanding the Pattern:**

- **For agent context**: ADK session service is the single source
- **For UI display**: Streamlit session state is the single source
- **No conflicts**: Each system owns its domain

**Common Issues:**

1. **"Messages not syncing"**
   - Verify both stores are updated after response
   - Check for errors during message addition
   - Run sync tests

2. **"Duplicate processing"**
   - Processing flag should prevent this
   - Check flag is set/reset correctly
   - Look for "Processing flag" logs

3. **"State divergence"**
   - Should not happen with current implementation
   - If it does, click "New Conversation"
   - Report as bug with reproduction steps

## Advanced Debugging

### Enable Debug Logging

Add to `.env`:
```bash
LOG_LEVEL=DEBUG
STREAMLIT_LOGGER_LEVEL=debug
```

Restart playground to see detailed logs.

### Inspect Session State

Add this to `vibehuntr_playground.py` temporarily:
```python
# Add after session state initialization
st.sidebar.write("Debug Info:")
st.sidebar.write(f"Session ID: {st.session_state.get('session_id', 'Not set')}")
st.sidebar.write(f"Message count: {len(st.session_state.get('messages', []))}")
st.sidebar.write(f"Processing: {st.session_state.get('is_processing', False)}")
st.sidebar.write(f"Agent loaded: {st.session_state.get('agent') is not None}")
```

### Monitor Network Requests

1. Open browser DevTools (F12)
2. Go to Network tab
3. Filter for "generativelanguage.googleapis.com"
4. Send a message
5. Check for:
   - Request sent successfully
   - Response received
   - No 4xx or 5xx errors

### Check ADK Session Service

Add this to test ADK session service directly:
```python
from google.adk.sessions import InMemorySessionService

# Create session service
session_service = InMemorySessionService()

# Create session
session_id = "test-session"
session_service.create_session(session_id)

# Add message
session_service.add_message(session_id, {"role": "user", "content": "test"})

# Get messages
messages = session_service.get_messages(session_id)
print(f"Messages: {messages}")
```

### Profile Performance

If playground is slow:
```bash
# Install profiling tools
uv add py-spy

# Profile playground
uv run py-spy top -- python -m streamlit run vibehuntr_playground.py
```

Look for:
- High CPU usage functions
- Memory leaks
- Slow operations

## Getting Help

### Before Asking for Help

1. **Run diagnostics:**
   ```bash
   # Run all diagnostic commands from Quick Diagnostics section
   ```

2. **Collect information:**
   - Error messages from terminal (full stack trace)
   - Browser console errors (F12 → Console)
   - Steps to reproduce the issue
   - Your `.env` configuration (WITHOUT API keys!)
   - OS and browser information
   - ADK version: `uv run python -c "import google.adk; print(google.adk.__version__)"`

3. **Try alternative interface:**
   ```bash
   uv run python app/event_planning/chat_interface.py
   ```
   Does the issue occur there too?

### Where to Get Help

1. **Check existing documentation:**
   - `PLAYGROUND_GUIDE.md` - User guide
   - `BUGFIX_DUPLICATE_RESPONSES.md` - Duplicate messages fix
   - `.kiro/specs/playground-fix/design.md` - Architecture details
   - This file - Troubleshooting guide

2. **Search GitHub issues:**
   - Check if issue already reported
   - Look for similar problems
   - Check closed issues for solutions

3. **Create GitHub issue:**
   Include:
   - Clear description of problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Diagnostic information collected above
   - Relevant log excerpts
   - Screenshots if applicable

4. **Ask in discussions:**
   - For questions, not bugs
   - Share your use case
   - Help others with similar issues

### Providing Good Bug Reports

**Good bug report template:**

```markdown
## Description
Brief description of the issue

## Steps to Reproduce
1. Start playground with `make playground`
2. Send message "Hello"
3. Observe duplicate messages

## Expected Behavior
Message should appear once

## Actual Behavior
Message appears twice

## Environment
- OS: Ubuntu 22.04
- Browser: Chrome 120
- ADK Version: 1.15.0
- Python: 3.11

## Logs
```
[Relevant log excerpts]
```

## Additional Context
- Happens consistently
- Started after updating to latest version
- Doesn't happen in CLI interface
```

## Summary

Most issues can be resolved by:
1. Verifying environment variables are set
2. Ensuring you're on the latest version
3. Restarting the playground
4. Clearing browser cache
5. Using "New Conversation" to reset state

For persistent issues:
1. Run diagnostic tests
2. Check logs for specific errors
3. Try alternative interface
4. Report issue with full details

The playground is designed to be robust and self-recovering. Most errors should resolve automatically or with a simple restart.
