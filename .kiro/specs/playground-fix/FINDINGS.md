# Playground Fix Implementation Findings

## Date
2024-11-20

## Summary
During the implementation of Task 1 (Refactor SessionManager), we discovered significant complexity in Google ADK's session management API that requires us to reconsider our approach.

## Problems Identified

### 1. Duplicate Message Display
**Status**: Confirmed issue
**Root Cause**: Messages are displayed from history loop AND displayed inline, then the page reruns showing them again from history.
**Evidence**: Screenshot showing identical response appearing twice in chat interface.

### 2. Context Loss (Memory)
**Status**: Confirmed issue  
**Root Cause**: ADK's `InMemorySessionService` manages its own history, but we're not properly syncing with it. The `chat_history` parameter in `invoke_agent_streaming()` is documented as "currently not used as session handles history" but the session history isn't being properly maintained.
**Evidence**: User reported agent asking "where are you from" multiple times in same conversation.

### 3. Dual State Management
**Status**: Confirmed architectural issue
**Root Cause**: We maintain history in both Streamlit session state (`st.session_state["messages"]`) AND ADK session service, causing inconsistency.

## ADK Session Service API Complexity

### Discovery
While implementing the refactored SessionManager, we discovered that ADK's session service API is more complex than initially understood:

```python
# get_session_sync() requires multiple parameters
session = session_service.get_session_sync(
    session_id=session_id,
    app_name="app_name",  # Required!
    user_id="user_id"      # Required!
)
```

### Implications

1. **Session Retrieval Complexity**: Getting a session requires knowing the app_name and user_id, not just the session_id
2. **History Access**: The session object's history attribute may not be directly accessible or may require special handling
3. **Session Creation**: Creating sessions through `create_session_sync()` returns a session with a generated ID, not the ID we provide
4. **Deprecation Warnings**: The sync methods are deprecated in favor of async methods

### Current Agent Invoker Approach

Looking at `app/event_planning/agent_invoker.py`, the current implementation:
- Uses a global `_session_service = InMemorySessionService()`
- Creates/retrieves sessions but doesn't pass chat history explicitly
- Relies on ADK Runner to automatically use session history
- **The chat_history parameter is explicitly documented as unused**

```python
def invoke_agent_streaming(
    agent: Any,
    message: str,
    chat_history: List[Dict[str, str]],  # <-- Not actually used!
    session_id: str = "default_session",
    user_id: str = "default_user",
    yield_tool_calls: bool = False
) -> Generator[Dict[str, Any], None, None]:
```

## Alternative Approaches to Consider

### Option A: Use ADK Runner's Built-in History (Current Attempt)
**Pros:**
- Single source of truth
- Leverages ADK's intended design
- No manual history management

**Cons:**
- Complex API with app_name/user_id requirements
- Unclear how to query history for display
- Session object structure not well documented
- May not support our pagination needs

**Status**: Partially implemented, blocked by API complexity

### Option B: Keep Streamlit State, Rebuild ADK Session Each Time
**Pros:**
- Simple to implement
- Full control over history
- Easy to query for display
- Supports pagination naturally

**Cons:**
- Dual state management (but explicit)
- Need to rebuild session context on each invocation
- May be inefficient

**Implementation:**
```python
# Store history in Streamlit state
st.session_state["messages"] = [...]

# On each agent invocation, create fresh session with history
session = session_service.create_session_sync(...)
# Manually add all messages from st.session_state to session
for msg in st.session_state["messages"]:
    # Add to session.history
    
# Invoke agent
runner.run(session_id=session.id, ...)
```

### Option C: Hybrid Approach - ADK for Agent, Streamlit for Display
**Pros:**
- Leverages strengths of both systems
- ADK handles agent context automatically
- Streamlit handles UI display naturally
- Clear separation of concerns

**Cons:**
- Need to keep both in sync
- Potential for drift between sources

**Implementation:**
```python
# ADK session service handles agent context (automatic)
runner.run(new_message=content, session_id=session_id, ...)

# After agent responds, add both user message and response to Streamlit state
st.session_state["messages"].append({"role": "user", "content": prompt})
st.session_state["messages"].append({"role": "assistant", "content": response})

# Display from Streamlit state
for msg in st.session_state["messages"]:
    st.chat_message(msg["role"]).markdown(msg["content"])
```

### Option D: Investigate ADK's Intended Pattern
**Action Required**: Research ADK documentation and examples to understand the intended pattern for:
- Querying session history for display
- Managing session lifecycle
- Handling pagination
- Accessing session state

## Recommended Next Steps

1. **Research Phase** (1-2 hours)
   - Review ADK documentation for session management
   - Look at ADK example code for playground implementations
   - Check if there's a way to query session history for display
   - Understand the async vs sync API migration path

2. **Decision Point**
   - If ADK provides clear history query API → Continue with Option A
   - If ADK doesn't support history queries → Choose Option B or C
   - Document the decision and rationale

3. **Prototype** (2-3 hours)
   - Implement chosen approach in a minimal test
   - Verify it solves both duplicate display and context loss
   - Ensure it's maintainable and testable

4. **Update Design Document**
   - Revise architecture based on chosen approach
   - Update component interfaces
   - Adjust correctness properties if needed

5. **Resume Implementation**
   - Complete refactored SessionManager
   - Update agent_invoker
   - Refactor playground UI
   - Write comprehensive tests

## Questions for Further Investigation

1. How does ADK's `InMemorySessionService` store and provide history to the agent?
2. Is there an API to query session history for display purposes?
3. What's the relationship between session.history and what the agent actually sees?
4. Are there ADK examples of Streamlit playgrounds we can reference?
5. What's the migration path from sync to async session methods?

## Code Changes Made So Far

### Modified Files
1. `app/event_planning/session_manager.py` - Partially refactored to accept session_service parameter
2. `tests/property/test_properties_session_manager_refactored.py` - New test file (failing due to API complexity)

### Changes to Revert or Complete
- SessionManager refactoring is incomplete and non-functional
- Tests are failing and need to be updated based on final approach
- No changes made to agent_invoker or playground UI yet

## Impact Assessment

**Current State**: Playground is broken with duplicate messages and context loss

**Risk of Continuing Current Approach**: Medium-High
- May hit more API complexity issues
- Unclear if ADK supports our display requirements
- Could waste significant time on wrong approach

**Risk of Switching Approach**: Low-Medium
- Need to revise design document
- Some code already written may need to be discarded
- But we'll have a clearer path forward

## Recommendation

**Pause implementation and conduct research phase** to understand ADK's intended session management pattern. Based on findings, choose the most appropriate approach (likely Option B or C for simplicity and control), update the design document, and then resume implementation with confidence.

The spec we created is still valuable - the requirements and correctness properties remain valid regardless of implementation approach. Only the architecture and component interfaces need adjustment.
