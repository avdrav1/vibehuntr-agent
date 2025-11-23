# Design Document

## Overview

This design addresses the critical issues in the Vibehuntr Streamlit playground: duplicate message display and conversation context loss. The root cause is a fundamental mismatch between how Streamlit manages UI state and how Google ADK manages conversation sessions.

**Current Problems:**
1. **Duplicate Display**: Messages appear multiple times because we display from history AND display inline, then rerun
2. **Context Loss**: ADK's InMemorySessionService manages its own history, but we're not properly syncing with it
3. **Dual State Management**: We maintain history in both Streamlit session state AND ADK session service, causing inconsistency

**Solution Approach:**
Use a hybrid approach where ADK's session service handles agent context automatically, while Streamlit manages UI state and display. This provides clear separation of concerns and leverages the strengths of both systems.

## Architecture

### Hybrid Pattern (Revised)

```
User Input → Streamlit State (for display)
     ↓
ADK Runner → ADK Session Service (for agent context)
     ↓
Agent Response → Both Streamlit State AND ADK Session
     ↓
Display from Streamlit State
```

**Key Principles:**
1. **ADK session service**: Handles agent context automatically (no manual history passing)
2. **Streamlit session state**: Manages message history for UI display
3. **Sync on each turn**: After agent responds, add messages to both stores
4. **Clear separation**: ADK = agent memory, Streamlit = UI state
5. **UI state separate**: Processing flags, agent cache kept in Streamlit state

**Why Hybrid?**
- ADK Runner already handles agent context automatically via session service
- Streamlit naturally handles UI display, pagination, and state management
- Simpler than trying to query ADK's internal session state
- Clear ownership: each system manages what it's good at
- Solves both duplicate display and context loss issues

### Component Interaction

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

## Components and Interfaces

### 1. SessionManager (Refactored for Hybrid)

**Purpose**: Manage Streamlit message history and provide display helpers

**Key Methods:**
```python
class SessionManager:
    def __init__(self, session_state=None):
        """Initialize with Streamlit session state"""
        
    def add_message(self, role: str, content: str) -> None:
        """Add message to Streamlit history"""
        
    def get_messages(self, recent_only: bool = False, recent_count: int = 10) -> List[Dict[str, str]]:
        """Get messages from Streamlit state for display"""
        
    def clear_messages(self) -> None:
        """Clear message history (new conversation)"""
        
    def get_agent(self) -> Optional[Agent]:
        """Get cached agent instance"""
        
    def set_agent(self, agent: Agent) -> None:
        """Cache agent instance"""
```

**Changes from Current:**
- **Keep** `add_message()` - needed for Streamlit display
- **Keep** internal message storage in Streamlit state
- **Keep** agent caching functionality
- **Keep** pagination helpers (should_show_history_button, get_older_messages)
- **Simplify**: Remove ADK session service dependency
- **Focus**: UI state management only

### 2. Agent Invoker (Minimal Changes)

**Purpose**: Invoke agent and handle streaming

**Current Implementation:**
```python
def invoke_agent_streaming(
    agent: Any,
    message: str,
    chat_history: List[Dict[str, str]],  # Currently unused
    session_id: str,
    user_id: str = "playground_user",
    yield_tool_calls: bool = False
) -> Generator[Dict[str, Any], None, None]:
    """
    Invoke agent with streaming.
    ADK Runner automatically uses session service for context.
    """
```

**Changes from Current:**
- **Keep** `chat_history` parameter for backward compatibility (but don't use it)
- **Document** that ADK Runner handles history automatically
- **No functional changes needed** - already works correctly
- ADK Runner already provides history from session service automatically
- Just improve logging and error handling

### 3. Streamlit Playground (Refactored for Hybrid)

**Purpose**: Display UI and handle user interaction

**Key Flow:**
```python
# 1. Initialize (once per session)
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "session_manager" not in st.session_state:
    st.session_state.session_manager = SessionManager()

session_manager = st.session_state.session_manager

# 2. Display messages from Streamlit state
messages = session_manager.get_messages()
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 3. Handle new input (with processing flag to prevent duplicate processing)
if prompt := st.chat_input("What would you like to plan today?"):
    if not st.session_state.get("is_processing", False):
        st.session_state.is_processing = True
        
        # Add user message to Streamlit state
        session_manager.add_message("user", prompt)
        
        # Invoke agent (ADK handles context automatically via session service)
        full_response = ""
        for item in invoke_agent_streaming(
            agent, 
            prompt, 
            [],  # chat_history unused by ADK
            st.session_state.session_id
        ):
            if item['type'] == 'text':
                full_response += item['content']
        
        # Add agent response to Streamlit state
        session_manager.add_message("assistant", full_response)
        
        # Reset processing flag and rerun to display from history
        st.session_state.is_processing = False
        st.rerun()
```

**Key Changes:**
- **Display from Streamlit state** (not ADK)
- **Add messages to Streamlit state** after each turn
- **ADK Runner handles agent context automatically** (no manual history passing)
- **Processing flag** prevents duplicate processing on rerun
- **Single rerun** after response completes to show clean history
- **No inline display** during streaming (simpler, prevents duplicates)

## Data Models

### Message Format

```python
{
    "role": str,      # "user" or "assistant"
    "content": str    # Message text
}
```

This matches both Streamlit's chat message format and ADK's expected format.

### Session State Structure

```python
# Streamlit session state (UI state + message history)
st.session_state = {
    "session_id": str,                    # ADK session ID
    "messages": List[Dict[str, str]],     # Message history for display
    "agent": Agent,                       # Cached agent instance
    "is_processing": bool,                # Prevent duplicate processing
    "session_manager": SessionManager     # Session manager instance
}
```

**Note**: Messages stored in Streamlit state for display. ADK session service maintains separate history for agent context automatically.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Message display uniqueness
*For any* conversation history, when displaying messages in the UI, each message should appear exactly once
**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

### Property 2: Streaming completion consistency
*For any* agent response, after streaming completes and the UI reruns, the message should appear exactly once in the history
**Validates: Requirements 1.5**

### Property 3: Context retention across turns
*For any* multi-turn conversation, information provided in earlier turns should be available to the agent in later turns
**Validates: Requirements 2.1, 2.3**

### Property 4: Question non-repetition
*For any* question asked by the agent that receives an answer, the agent should not ask the same question in subsequent turns
**Validates: Requirements 2.2**

### Property 5: Reference resolution
*For any* entity mentioned in conversation, when referenced later (by pronoun or description), the agent should correctly identify it
**Validates: Requirements 2.4**

### Property 6: History availability to agent
*For any* message stored in the ADK session service, that message should be available in the context provided to the agent
**Validates: Requirements 2.5**

### Property 7: State preservation across reruns
*For any* Streamlit rerun, the conversation history should remain intact and complete
**Validates: Requirements 4.1**

### Property 8: State integrity during UI updates
*For any* UI update operation, the conversation history should not be corrupted or modified
**Validates: Requirements 4.5**

### Property 9: Streaming display progression
*For any* agent response being streamed, partial content should be visible in the UI before completion
**Validates: Requirements 5.1**

### Property 10: Error handling during streaming
*For any* error that occurs during streaming, the system should handle it gracefully and display an appropriate error message
**Validates: Requirements 5.5**

### Property 11: User-friendly error messages
*For any* error that occurs, the displayed error message should not contain internal implementation details (stack traces, variable names, etc.)
**Validates: Requirements 6.1, 6.4**

### Property 12: Error recovery without corruption
*For any* error that prevents response generation, the conversation history should remain intact and uncorrupted
**Validates: Requirements 6.5**

### Property 13: Error logging completeness
*For any* error that occurs, the logged error should include sufficient context (timestamp, session ID, user message, error type)
**Validates: Requirements 6.3**

### Property 14: Session error recovery
*For any* session-related error, the system should either recover automatically or provide clear guidance to the user
**Validates: Requirements 6.2**

### Property 15: Session ID consistency
*For any* conversation session, all messages should use the same session ID throughout
**Validates: Requirements 7.2**

### Property 16: History storage round-trip
*For any* message added to the session service, querying the session history should return that message with identical content
**Validates: Requirements 7.3**

### Property 17: History retrieval order
*For any* sequence of messages added to session history, querying the history should return them in the same chronological order
**Validates: Requirements 7.4**

## Error Handling

### Error Categories

1. **Agent Invocation Errors**
   - API failures, timeouts, rate limits
   - Display: "Unable to get response. Please try again."
   - Log: Full error with context

2. **Session Errors**
   - Session not found, session creation failure
   - Recovery: Create new session automatically
   - Display: "Starting new conversation..."

3. **Streaming Errors**
   - Connection drops during streaming
   - Display: Partial response + error message
   - Preserve: Partial response in history

4. **State Corruption**
   - Invalid session state
   - Recovery: Reset to clean state
   - Display: "Session reset. Please start over."

### Error Handling Pattern

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

## Testing Strategy

### Unit Tests

Unit tests will verify specific behaviors and edge cases:

1. **Session Manager Tests**
   - Session creation and retrieval
   - History querying
   - Session clearing
   - Error handling for missing sessions

2. **Agent Invoker Tests**
   - Successful invocation
   - Streaming token collection
   - Error propagation
   - Session ID usage

3. **UI Component Tests**
   - Message display formatting
   - Error message display
   - Processing flag management

### Property-Based Tests

Property-based tests will verify universal properties using **Hypothesis** (Python's PBT library). Each test will run a minimum of 100 iterations with randomly generated inputs.

**Configuration:**
```python
from hypothesis import given, settings
import hypothesis.strategies as st

@settings(max_examples=100)
@given(...)
def test_property_name(...):
    # Test implementation
```

**Test Tagging:**
Each property-based test will be tagged with a comment referencing the design document:
```python
# Feature: playground-fix, Property 1: Message display uniqueness
```

**Property Test Examples:**

1. **Property 1: Message display uniqueness**
   - Generate: Random conversation histories
   - Test: Count occurrences of each message in rendered output
   - Assert: Each message appears exactly once

2. **Property 3: Context retention**
   - Generate: Multi-turn conversations with information in early turns
   - Test: Verify agent responses reference earlier information
   - Assert: Context is maintained

3. **Property 16: History storage round-trip**
   - Generate: Random messages
   - Test: Add to session, query history
   - Assert: Retrieved message matches original

### Integration Tests

Integration tests will verify end-to-end flows:

1. **Complete Conversation Flow**
   - Start playground
   - Send multiple messages
   - Verify history and context

2. **Error Recovery Flow**
   - Trigger various errors
   - Verify recovery mechanisms
   - Verify history integrity

3. **Session Lifecycle**
   - Create session
   - Use session across multiple turns
   - Clear session
   - Verify new session starts fresh

### Manual Testing

Manual testing checklist for visual and UX verification:

1. Send message and verify it appears once
2. Verify agent response appears once
3. Send multiple messages and verify no duplicates
4. Verify streaming shows cursor during generation
5. Verify cursor disappears after completion
6. Reference earlier conversation and verify agent remembers
7. Trigger error and verify user-friendly message
8. Start new conversation and verify history clears

## Implementation Notes

### Migration Strategy (Revised for Hybrid Approach)

1. **Phase 1**: Revert SessionManager changes - keep current implementation
2. **Phase 2**: Fix playground UI display logic to prevent duplicates
3. **Phase 3**: Add processing flag to prevent duplicate processing on rerun
4. **Phase 4**: Verify ADK session service maintains context automatically
5. **Phase 5**: Add comprehensive error handling
6. **Phase 6**: Write and run all tests

### Backward Compatibility

**Minimal breaking changes:**
- SessionManager keeps current API (no changes needed)
- Agent invoker keeps current API (already works correctly)
- Only playground UI logic changes (internal implementation)
- External user experience remains the same

### Performance Considerations

- Streamlit state access is instant (in-memory)
- ADK session service is also in-memory
- No performance concerns with hybrid approach
- Simpler than querying ADK for display

### Why Hybrid is Better

1. **Simpler**: Leverages existing Streamlit patterns
2. **Clearer**: Each system has clear ownership
3. **Maintainable**: Standard Streamlit state management
4. **Testable**: Easy to test display logic separately from agent logic
5. **Flexible**: Can add features like export, search, etc. easily

### Future Enhancements

- Persist Streamlit messages to disk for recovery after restart
- Add conversation export functionality (easy with Streamlit state)
- Support multiple concurrent sessions
- Add conversation branching/forking
- Add message search and filtering
