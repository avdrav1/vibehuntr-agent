# Design Document

## Overview

This design document describes the integration of the Vibehuntr event planning agent with Google's Agent Development Kit (ADK) through a custom-branded Streamlit playground interface. The integration will enable real-time conversational AI interactions while maintaining the existing Vibehuntr branding and user experience.

The system will connect the existing `vibehuntr_playground.py` Streamlit interface to either the full agent (`app/agent.py`) or the simple agent (`app/event_planning/simple_agent.py`), depending on environment configuration. The integration will support streaming responses, session management, and proper error handling while preserving the visual styling and user experience.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit UI Layer                        │
│  (vibehuntr_playground.py + playground_style.py)            │
│  - Chat interface                                            │
│  - Message display                                           │
│  - Vibehuntr branding                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Session Management Layer                        │
│  - Streamlit session state                                   │
│  - Chat history management                                   │
│  - Agent instance caching                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 Agent Invocation Layer                       │
│  - Agent selection (full vs simple)                          │
│  - Message streaming                                         │
│  - Error handling                                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    ADK Agent Layer                           │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │   Full Agent     │   OR    │  Simple Agent    │         │
│  │  (app/agent.py)  │         │  (simple_agent)  │         │
│  │  - Doc retrieval │         │  - Event tools   │         │
│  │  - Event tools   │         │  - Places tools  │         │
│  │  - Places tools  │         │                  │         │
│  └──────────────────┘         └──────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
User Input → Streamlit Chat → Session State → Agent Invoke → Stream Response → Display
     ↑                                                                            │
     └────────────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Agent Loader Module (`app/event_planning/agent_loader.py`)

**Purpose**: Centralized agent loading logic that selects and initializes the appropriate agent based on environment configuration.

**Interface**:
```python
def get_agent() -> Agent:
    """
    Load and return the appropriate agent based on environment configuration.
    
    Returns:
        Agent: Either the full agent (with document retrieval) or simple agent
        
    Raises:
        ImportError: If agent modules cannot be loaded
        RuntimeError: If agent initialization fails
    """
```

**Responsibilities**:
- Check `USE_DOCUMENT_RETRIEVAL` environment variable
- Import and return the appropriate agent
- Cache agent instance for reuse
- Handle import errors gracefully

### 2. Session Manager (`app/event_planning/session_manager.py`)

**Purpose**: Manage conversation state and chat history using Streamlit's session state.

**Interface**:
```python
class SessionManager:
    """Manages conversation sessions and chat history."""
    
    def __init__(self):
        """Initialize session manager with Streamlit session state."""
        
    def get_messages(self, recent_only: bool = False, recent_count: int = 10) -> List[Dict[str, str]]:
        """
        Get chat history.
        
        Args:
            recent_only: If True, return only recent messages
            recent_count: Number of recent messages to return
            
        Returns:
            List of message dictionaries
        """
        
    def get_all_messages(self) -> List[Dict[str, str]]:
        """Get complete chat history."""
        
    def add_message(self, role: str, content: str) -> None:
        """Add a message to chat history."""
        
    def clear_messages(self) -> None:
        """Clear all messages and start fresh."""
        
    def get_agent(self) -> Agent:
        """Get or create cached agent instance."""
        
    def should_show_history_button(self, recent_count: int = 10) -> bool:
        """Check if there are older messages to show."""
```

**Responsibilities**:
- Initialize and manage Streamlit session state
- Store and retrieve chat messages
- Provide session reset functionality
- Cache agent instance per session

### 3. Agent Invoker (`app/event_planning/agent_invoker.py`)

**Purpose**: Handle agent invocation with streaming support and error handling.

**Interface**:
```python
def invoke_agent_streaming(
    agent: Agent,
    message: str,
    chat_history: List[Dict[str, str]]
) -> Generator[str, None, None]:
    """
    Invoke agent with streaming response.
    
    Args:
        agent: The ADK agent instance
        message: User's input message
        chat_history: Previous conversation messages
        
    Yields:
        str: Response tokens as they are generated
        
    Raises:
        AgentInvocationError: If agent invocation fails
    """

def invoke_agent(
    agent: Agent,
    message: str,
    chat_history: List[Dict[str, str]]
) -> str:
    """
    Invoke agent and return complete response.
    
    Args:
        agent: The ADK agent instance
        message: User's input message
        chat_history: Previous conversation messages
        
    Returns:
        str: Complete agent response
        
    Raises:
        AgentInvocationError: If agent invocation fails
    """
```

**Responsibilities**:
- Format chat history for agent context
- Invoke agent with proper parameters
- Stream response tokens
- Handle errors and exceptions
- Log invocations for debugging

### 4. Updated Playground Interface (`vibehuntr_playground.py`)

**Purpose**: Streamlit UI that integrates with ADK agent for conversational interaction with optimized single-page layout.

**Key Changes**:
- Replace placeholder response with actual agent invocation
- Add streaming response display
- Implement session management with history pagination
- Display only recent messages (last 10) by default
- Add "Show Older Messages" expandable section for full history
- Add "New Conversation" button
- Enhance error display
- Maintain Vibehuntr branding
- Keep chat input always visible at bottom

**UI Layout**:
```
┌─────────────────────────────────────┐
│  Vibehuntr Header & Welcome         │
├─────────────────────────────────────┤
│  [Show Older Messages] (if > 10)    │
├─────────────────────────────────────┤
│  Recent Messages (last 10)          │
│  - Message 1                        │
│  - Message 2                        │
│  - ...                              │
│  - Message 10                       │
├─────────────────────────────────────┤
│  Chat Input (always visible)        │
│  [New Conversation]                 │
└─────────────────────────────────────┘
```

## Data Models

### Message Format

```python
{
    "role": str,      # "user" or "assistant"
    "content": str    # Message text
}
```

### Session State Schema

```python
{
    "messages": List[Dict[str, str]],  # Complete chat history
    "agent": Agent,                     # Cached agent instance
    "session_id": str,                  # Unique session identifier
    "show_all_history": bool            # Whether to show all messages or just recent
}
```

### Agent Response Format

The agent returns responses as either:
1. **Streaming**: Generator yielding tokens
2. **Complete**: Full response string

Both formats are handled by the invoker layer.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Message persistence in session

*For any* user message sent during a session, that message should appear in the session's chat history after submission.
**Validates: Requirements 3.1**

### Property 2: Agent response persistence

*For any* agent response generated, that response should be appended to the session's chat history after completion.
**Validates: Requirements 3.2**

### Property 3: Session context provision

*For any* agent invocation, the complete chat history up to that point should be provided as context to the agent.
**Validates: Requirements 3.3**

### Property 4: Fresh session on refresh

*For any* page refresh, the system should initialize a new session with empty chat history.
**Validates: Requirements 3.4**

### Property 5: Agent selection consistency

*For any* environment configuration, when USE_DOCUMENT_RETRIEVAL is true, the system should use the full agent; when false, the system should use the simple agent.
**Validates: Requirements 4.1, 4.2**

### Property 6: Streaming token order

*For any* streaming response, tokens should be yielded in the order they are generated by the agent.
**Validates: Requirements 2.1**

### Property 7: Error message display

*For any* error that occurs during agent invocation, the system should display a user-friendly error message and not crash.
**Validates: Requirements 5.2, 7.4**

### Property 8: Input blocking during processing

*For any* active agent invocation, the system should prevent submission of new messages until the current response is complete.
**Validates: Requirements 5.5**

### Property 9: History clearing completeness

*For any* "New Conversation" action, all messages should be removed from the session state.
**Validates: Requirements 8.2**

### Property 10: Branding preservation

*For any* message displayed, the Vibehuntr styling should be applied to maintain visual consistency.
**Validates: Requirements 6.1, 6.2**

### Property 11: Recent messages display limit

*For any* conversation with more than 10 messages, the default view should display only the 10 most recent messages.
**Validates: Requirements 1.1** (implied from user feedback)

### Property 12: Complete history availability

*For any* conversation with more than 10 messages, all older messages should be accessible through the "Show Older Messages" section.
**Validates: Requirements 3.5** (chronological order)

## Error Handling

### Error Categories

1. **Agent Loading Errors**
   - Missing dependencies
   - Configuration errors
   - Import failures
   
   **Handling**: Display error message with setup instructions, allow retry

2. **Agent Invocation Errors**
   - API failures
   - Timeout errors
   - Tool execution failures
   
   **Handling**: Display user-friendly error, log details, allow retry

3. **Streaming Errors**
   - Connection interruptions
   - Partial response failures
   
   **Handling**: Display partial response, indicate error, allow retry

4. **Session State Errors**
   - State corruption
   - Serialization failures
   
   **Handling**: Reset session, log error, notify user

### Error Logging Strategy

All errors will be logged with:
- Timestamp
- Error type and message
- Stack trace
- User message that triggered error
- Session ID for correlation

Logging will use Python's `logging` module with appropriate levels:
- `ERROR`: For failures that prevent functionality
- `WARNING`: For recoverable issues
- `INFO`: For normal operations
- `DEBUG`: For detailed troubleshooting

### User-Facing Error Messages

Errors will be displayed in styled containers matching Vibehuntr branding:

```python
st.error(f"🚫 {error_type}: {user_friendly_message}")
```

Examples:
- "🚫 Connection Error: Unable to reach the agent. Please try again."
- "🚫 Configuration Error: Agent not properly configured. Check environment variables."
- "🚫 Processing Error: Something went wrong. Please try a different request."

## Testing Strategy

### Unit Testing

Unit tests will verify individual components in isolation:

1. **Agent Loader Tests**
   - Test agent selection based on environment variable
   - Test error handling for missing modules
   - Test agent caching behavior

2. **Session Manager Tests**
   - Test message addition and retrieval
   - Test session clearing
   - Test agent caching

3. **Agent Invoker Tests**
   - Test message formatting
   - Test streaming response handling
   - Test error handling and logging

### Integration Testing

Integration tests will verify component interactions:

1. **End-to-End Conversation Flow**
   - Send message → receive response → verify history
   - Test multiple message exchanges
   - Verify context is maintained

2. **Agent Switching**
   - Test with USE_DOCUMENT_RETRIEVAL=true
   - Test with USE_DOCUMENT_RETRIEVAL=false
   - Verify correct agent is used

3. **Error Recovery**
   - Trigger various error conditions
   - Verify graceful handling
   - Verify system remains functional

### Property-Based Testing

Property-based tests will use the `hypothesis` library to verify correctness properties across many random inputs:

1. **Message History Properties**
   - Generate random sequences of messages
   - Verify all messages are stored in order
   - Verify history is provided to agent

2. **Session Isolation Properties**
   - Generate multiple concurrent sessions
   - Verify sessions don't interfere with each other
   - Verify session resets work correctly

3. **Streaming Properties**
   - Generate random response lengths
   - Verify all tokens are delivered
   - Verify order is preserved

### Manual Testing Checklist

1. **Visual Testing**
   - Verify Vibehuntr branding is applied
   - Check responsive layout
   - Test on different screen sizes

2. **Interaction Testing**
   - Test various conversation flows
   - Verify tool invocations work
   - Test error scenarios

3. **Performance Testing**
   - Test with long conversations
   - Verify streaming performance
   - Check memory usage

### Test Configuration

- Minimum 100 iterations for property-based tests
- Mock external dependencies (Gemini API) in unit tests
- Use real agent in integration tests with test API key
- Each property-based test will reference its design property using format: `**Feature: adk-playground-integration, Property {number}: {property_text}**`

## Implementation Notes

### Streamlit-Specific Considerations

1. **Session State Initialization**
   - Must check if keys exist before accessing
   - Initialize on first run
   - Handle page refreshes

2. **Streaming Display**
   - Use `st.write_stream()` for token-by-token display
   - Or use `st.empty()` with progressive updates
   - Show spinner during initial processing

3. **Chat Message Display**
   - Use `st.chat_message()` for proper formatting
   - Apply custom CSS for Vibehuntr styling
   - Support markdown rendering

4. **History Pagination**
   - Display only last 10 messages by default
   - Use `st.expander()` for "Show Older Messages" section
   - Expander should show messages 0 to N-10
   - Keep chat input always visible using `st.container()`
   - Auto-scroll to recent messages on new input

5. **Single Page Layout**
   - Use `st.container()` to organize sections
   - Keep header compact
   - Minimize vertical space usage
   - Ensure chat input is always accessible

### ADK Agent Integration

1. **Agent Invocation Pattern**
   ```python
   # For streaming
   for chunk in agent.run(message, stream=True):
       yield chunk.content
   
   # For complete response
   response = agent.run(message)
   return response.content
   ```

2. **Chat History Format**
   - ADK expects list of message dictionaries
   - Format: `[{"role": "user", "content": "..."}, ...]`
   - Include full history for context

3. **Tool Execution**
   - Tools are automatically invoked by agent
   - No special handling needed in UI
   - Optionally display tool calls for transparency

### Environment Configuration

Required environment variables:
- `USE_DOCUMENT_RETRIEVAL`: "true" or "false"
- `GOOGLE_API_KEY`: For Gemini API (if not using GCP credentials)
- `GOOGLE_CLOUD_PROJECT`: For GCP-based deployments
- `DATA_STORE_ID`: For document retrieval (if enabled)

### Performance Optimization

1. **Agent Caching**
   - Cache agent instance in session state
   - Avoid reloading on every message
   - Clear cache on configuration change

2. **Message History Management**
   - Consider truncating very long histories
   - Keep last N messages for context
   - Archive old messages if needed

3. **Streaming Optimization**
   - Use generators to avoid buffering
   - Display tokens as soon as available
   - Minimize UI updates

## Deployment Considerations

### Local Development

Run with:
```bash
streamlit run vibehuntr_playground.py
```

Or use the existing script:
```bash
./start_playground.sh
```

### Production Deployment

The playground is intended for development and testing. For production:
- Use Agent Engine deployment (`app/agent_engine_app.py`)
- Or deploy Streamlit app to Cloud Run
- Configure proper authentication
- Set up monitoring and logging

### Configuration Management

- Use `.env` files for local development
- Use environment variables for deployment
- Document required variables in README
- Provide example `.env.example` file

## Future Enhancements

Potential improvements for future iterations:

1. **Conversation Persistence**
   - Save conversations to database
   - Allow loading previous conversations
   - Export conversation history

2. **Multi-User Support**
   - User authentication
   - Per-user conversation history
   - User preferences

3. **Enhanced Feedback**
   - Show tool invocations in UI
   - Display thinking process
   - Provide response ratings

4. **Advanced Features**
   - Voice input/output
   - Image support
   - File uploads

5. **Analytics**
   - Track conversation metrics
   - Monitor agent performance
   - Collect user feedback
