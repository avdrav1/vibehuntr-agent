# Design Document

## Overview

The response duplication issue manifests as the agent generating the same response content twice consecutively in the chat interface. Based on investigation of the codebase and the screenshot provided, the duplication appears to be happening at the agent/LLM level rather than in the streaming or session management layers.

The current implementation already has duplicate detection logic in `agent_invoker.py` that tracks accumulated text and seen chunks to prevent duplicate tokens from being yielded. However, this is a downstream filter that doesn't address the root cause - the agent itself is generating duplicate content.

This design proposes a multi-layered approach:
1. **Root Cause Investigation**: Add comprehensive logging to identify exactly where duplication originates
2. **Agent Configuration Fix**: Adjust agent settings to prevent duplicate generation
3. **Enhanced Duplicate Detection**: Improve the existing duplicate filtering logic
4. **Monitoring and Alerting**: Add metrics to detect duplication in production

## Architecture

### Current Flow

```
User Message
    ↓
Backend API (/api/chat/stream)
    ↓
Agent Service (agent_service.py)
    ↓
Agent Invoker (agent_invoker.py)
    ├─ Context Injection
    ├─ Session Management
    └─ ADK Runner
        ↓
    Agent (agent.py)
        ↓
    Gemini 2.0 Flash Exp
        ↓
    Response Stream
        ↓
    Duplicate Detection (agent_invoker.py)
        ↓
    Frontend Display
```

### Problem Points

Based on the screenshot and code analysis, duplication can occur at multiple points:

1. **Agent Level** (Most Likely): The LLM generates the same response twice
   - Possible causes: Model behavior, prompt issues, context confusion
   - Evidence: Duplicate detection logic exists but duplication still occurs

2. **Runner Level**: ADK Runner yields duplicate events
   - Possible causes: Event stream processing issues
   - Evidence: Less likely given ADK's maturity

3. **Session Level**: Session history contains duplicates
   - Possible causes: Multiple message additions
   - Evidence: Tests show session management is working correctly

4. **Streaming Level**: Tokens are yielded multiple times
   - Possible causes: Generator iteration issues
   - Evidence: Duplicate detection exists but may have gaps

## Components and Interfaces

### 1. Enhanced Logging Module

**Purpose**: Add comprehensive logging to track response generation and identify duplication points

**Interface**:
```python
class ResponseTracker:
    """Track response generation to detect duplication."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.response_id = generate_unique_id()
        self.chunks_seen: Set[str] = set()
        self.total_chunks = 0
        self.duplicate_chunks = 0
    
    def track_chunk(self, chunk: str) -> bool:
        """
        Track a response chunk and detect if it's a duplicate.
        
        Returns:
            bool: True if chunk is unique, False if duplicate
        """
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get duplication metrics for this response."""
        pass
```

### 2. Agent Configuration Module

**Purpose**: Centralize agent configuration with settings to prevent duplication

**Interface**:
```python
def get_agent_config() -> Dict[str, Any]:
    """
    Get agent configuration with duplication prevention settings.
    
    Returns:
        Dict with model, temperature, and other settings
    """
    return {
        "model": "gemini-2.0-flash-exp",
        "temperature": 0.7,  # Lower temperature for more deterministic responses
        "top_p": 0.95,
        "top_k": 40,
        # Add any other settings that might affect duplication
    }
```

### 3. Enhanced Duplicate Detection

**Purpose**: Improve the existing duplicate detection logic in agent_invoker.py

**Current Implementation**:
```python
# Tracks accumulated text and seen chunks
accumulated_text = ""
seen_chunks = set()

# Detects duplicates by checking if new content starts with accumulated text
if part.text.startswith(accumulated_text):
    new_content = part.text[len(accumulated_text):]
    if new_content:
        chunk_hash = hash(new_content)
        if chunk_hash not in seen_chunks:
            # Yield new content
            pass
```

**Enhanced Implementation**:
```python
class DuplicateDetector:
    """Enhanced duplicate detection with multiple strategies."""
    
    def __init__(self):
        self.accumulated_text = ""
        self.seen_chunks: Set[int] = set()
        self.chunk_sequence: List[str] = []
        self.pattern_detector = PatternDetector()
    
    def is_duplicate(self, chunk: str) -> bool:
        """
        Check if chunk is a duplicate using multiple strategies.
        
        Strategies:
        1. Exact hash matching (current approach)
        2. Sequence pattern detection (detect repeated sequences)
        3. Content similarity (detect near-duplicates)
        """
        pass
    
    def add_chunk(self, chunk: str) -> None:
        """Add chunk to tracking."""
        pass
```

### 4. Monitoring and Metrics

**Purpose**: Track duplication metrics for production monitoring

**Interface**:
```python
class DuplicationMetrics:
    """Track duplication metrics for monitoring."""
    
    @staticmethod
    def increment_duplicate_detected(session_id: str) -> None:
        """Increment counter when duplicate is detected."""
        pass
    
    @staticmethod
    def record_response_quality(
        session_id: str,
        total_chunks: int,
        duplicate_chunks: int
    ) -> None:
        """Record response quality metrics."""
        pass
    
    @staticmethod
    def get_duplication_rate() -> float:
        """Get overall duplication rate."""
        pass
```

## Data Models

### ResponseMetadata

```python
@dataclass
class ResponseMetadata:
    """Metadata about a response generation."""
    
    response_id: str
    session_id: str
    user_id: str
    timestamp: datetime
    total_chunks: int
    duplicate_chunks: int
    duplication_rate: float
    model_used: str
    temperature: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "response_id": self.response_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "total_chunks": self.total_chunks,
            "duplicate_chunks": self.duplicate_chunks,
            "duplication_rate": self.duplication_rate,
            "model_used": self.model_used,
            "temperature": self.temperature
        }
```

### DuplicationEvent

```python
@dataclass
class DuplicationEvent:
    """Event logged when duplication is detected."""
    
    event_id: str
    session_id: str
    response_id: str
    timestamp: datetime
    duplicate_chunk: str
    chunk_index: int
    detection_method: str  # "hash", "pattern", "similarity"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "response_id": self.response_id,
            "timestamp": self.timestamp.isoformat(),
            "duplicate_chunk_preview": self.duplicate_chunk[:100],
            "chunk_index": self.chunk_index,
            "detection_method": self.detection_method
        }
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing all acceptance criteria, I've identified several redundant properties:
- Properties 3.3, 3.4, and 3.5 are redundant with 1.2, 1.3, and 1.4 respectively
- These will be consolidated into the core properties to avoid redundant testing

### Core Properties

Property 1: Response content uniqueness
*For any* agent response, the displayed content should contain no repeated sections or duplicate text blocks
**Validates: Requirements 1.1**

Property 2: Token streaming uniqueness
*For any* streaming response, each token should be yielded exactly once in the sequence without any duplicates
**Validates: Requirements 1.2, 3.3**

Property 3: Session history uniqueness
*For any* completed response, the session history should contain exactly one copy of that response
**Validates: Requirements 1.3, 3.4**

Property 4: Concurrent session isolation
*For any* set of concurrent sessions, each session should maintain response uniqueness independently without interference from other sessions
**Validates: Requirements 1.4, 3.5**

Property 5: Tool usage uniqueness
*For any* response that involves tool calls, neither the tool outputs nor the final response should contain duplicate content
**Validates: Requirements 1.5**

Property 6: Response ID uniqueness
*For any* response generation event, the system should assign a unique identifier that is logged with all related events
**Validates: Requirements 2.1**

Property 7: Duplication source tracking
*For any* detected duplication, the tracking mechanism should correctly identify whether it originated at the agent level or streaming level
**Validates: Requirements 2.2**

Property 8: Duplication point logging
*For any* detected duplication, the system should log the exact pipeline stage where the duplication occurred
**Validates: Requirements 2.3**

Property 9: Multi-turn conversation uniqueness
*For any* multi-turn conversation, each turn should produce a unique response with no duplication across turns
**Validates: Requirements 3.2**

Property 10: Duplication detection logging
*For any* detected duplication, the system should log a warning that includes the session ID and duplication context
**Validates: Requirements 4.1**

Property 11: Duplication counter accuracy
*For any* sequence of duplication events, the duplication counter metric should increment exactly once per event
**Validates: Requirements 4.2**

Property 12: Resolution confirmation logging
*For any* duplication resolution, the system should log confirmation that responses are now unique
**Validates: Requirements 4.5**

## Error Handling

### Duplication Detection Errors

**Scenario**: Duplicate detection logic fails or throws an exception

**Handling**:
- Log the error with full context (session ID, response ID, chunk content)
- Fall back to yielding the content (graceful degradation - better to show duplicate than crash)
- Increment error counter for monitoring
- Continue processing remaining chunks

**Example**:
```python
try:
    if duplicate_detector.is_duplicate(chunk):
        logger.warning(f"Duplicate chunk detected: {chunk[:50]}...")
        metrics.increment_duplicate_detected(session_id)
        continue  # Skip duplicate
except Exception as e:
    logger.error(f"Duplicate detection failed: {e}", exc_info=True)
    metrics.increment_detection_error()
    # Fall back to yielding the chunk
    yield {'type': 'text', 'content': chunk}
```

### Logging Errors

**Scenario**: Logging fails during response generation

**Handling**:
- Don't let logging failures break response generation
- Use try-except around all logging calls
- Log to stderr as fallback
- Continue with response generation

**Example**:
```python
try:
    logger.info(f"Response generated: {response_id}")
except Exception as e:
    print(f"Logging failed: {e}", file=sys.stderr)
    # Continue anyway
```

### Metrics Collection Errors

**Scenario**: Metrics collection fails

**Handling**:
- Don't let metrics failures break functionality
- Use try-except around all metrics calls
- Log the metrics error
- Continue with normal operation

**Example**:
```python
try:
    metrics.record_response_quality(session_id, total_chunks, duplicate_chunks)
except Exception as e:
    logger.error(f"Metrics recording failed: {e}")
    # Continue anyway
```

## Testing Strategy

### Unit Testing

Unit tests will verify individual components in isolation:

1. **DuplicateDetector Tests**
   - Test exact hash matching with identical chunks
   - Test sequence pattern detection with repeated patterns
   - Test content similarity detection with near-duplicates
   - Test edge cases (empty chunks, very long chunks, special characters)

2. **ResponseTracker Tests**
   - Test chunk tracking with unique chunks
   - Test chunk tracking with duplicate chunks
   - Test metrics calculation
   - Test response ID generation uniqueness

3. **DuplicationMetrics Tests**
   - Test counter increments
   - Test rate calculations
   - Test metric retrieval
   - Test concurrent metric updates

### Property-Based Testing

Property-based tests will use the `hypothesis` library to verify properties across many random inputs:

**Library**: `hypothesis` (Python property-based testing library)
**Configuration**: Each property test will run a minimum of 100 iterations

**Test Tagging**: Each property-based test will include a comment with this format:
```python
# Feature: response-duplication-fix, Property 1: Response content uniqueness
```

1. **Property 1: Response content uniqueness**
   - Generate random agent responses
   - Verify no repeated sections exist in the response
   - Check that splitting the response into chunks and looking for duplicates finds none

2. **Property 2: Token streaming uniqueness**
   - Generate random streaming responses
   - Collect all yielded tokens
   - Verify no token appears twice in the sequence

3. **Property 3: Session history uniqueness**
   - Generate random responses and store them
   - Retrieve session history
   - Verify each response appears exactly once

4. **Property 4: Concurrent session isolation**
   - Generate multiple concurrent sessions with random messages
   - Verify each session maintains unique responses
   - Verify no cross-session interference

5. **Property 5: Tool usage uniqueness**
   - Generate responses that trigger tool calls
   - Verify tool outputs contain no duplicates
   - Verify final responses contain no duplicates

6. **Property 6: Response ID uniqueness**
   - Generate multiple responses
   - Collect all response IDs
   - Verify all IDs are unique

7. **Property 7: Duplication source tracking**
   - Create duplication scenarios at different pipeline stages
   - Verify tracking correctly identifies the source

8. **Property 8: Duplication point logging**
   - Create duplication scenarios
   - Verify logs contain the correct pipeline stage

9. **Property 9: Multi-turn conversation uniqueness**
   - Generate random multi-turn conversations
   - Verify each turn has a unique response

10. **Property 10: Duplication detection logging**
    - Create duplication scenarios
    - Verify warnings are logged with correct context

11. **Property 11: Duplication counter accuracy**
    - Create multiple duplication events
    - Verify counter increments correctly

12. **Property 12: Resolution confirmation logging**
    - Resolve duplication scenarios
    - Verify confirmation is logged

### Integration Testing

Integration tests will verify the complete flow:

1. **End-to-End Duplication Prevention**
   - Send a message through the full stack
   - Verify response contains no duplicates
   - Verify session history is correct
   - Verify metrics are recorded

2. **Streaming Duplication Prevention**
   - Stream a response through the full stack
   - Collect all tokens
   - Verify no duplicate tokens
   - Verify final response is correct

3. **Multi-Session Duplication Prevention**
   - Create multiple sessions
   - Send messages to each
   - Verify no session has duplicates
   - Verify sessions don't interfere

### Manual Testing

Manual testing scenarios to verify the fix:

1. **Scenario from Screenshot**
   - Send: "Italian restaurants in South Philly"
   - Verify: Response appears exactly once
   - Verify: No duplicate restaurant lists

2. **Multi-Turn Conversation**
   - Turn 1: "cheesesteak"
   - Turn 2: "philly"
   - Turn 3: "more details"
   - Verify: No duplicates in any turn

3. **Tool Usage**
   - Send message that triggers search_venues_tool
   - Verify: Tool output appears once
   - Verify: Final response appears once

## Implementation Notes

### Priority 1: Root Cause Investigation

Before implementing fixes, we need to identify the exact source of duplication:

1. Add comprehensive logging to track:
   - ADK Runner event generation
   - Token yielding in agent_invoker
   - Session history updates
   - Frontend message display

2. Run test scenarios and analyze logs to determine:
   - Is the agent generating duplicate content?
   - Is the Runner yielding duplicate events?
   - Is the streaming logic yielding duplicates?
   - Is the frontend displaying duplicates?

### Priority 2: Fix at the Source

Once the source is identified, implement the fix at that level:

**If Agent Level**:
- Adjust agent configuration (temperature, top_p, top_k)
- Review prompt for issues that might cause repetition
- Consider switching models if needed

**If Runner Level**:
- Review ADK Runner usage
- Check for event stream processing issues
- Verify session service integration

**If Streaming Level**:
- Enhance duplicate detection logic
- Add pattern detection for repeated sequences
- Improve chunk tracking

### Priority 3: Defense in Depth

Even after fixing the source, maintain defensive measures:

- Keep enhanced duplicate detection
- Maintain comprehensive logging
- Continue monitoring metrics
- Alert on duplication patterns

### Configuration Changes

Consider these agent configuration changes to reduce duplication:

```python
root_agent = Agent(
    name="root_agent",
    model="gemini-2.0-flash-exp",
    instruction=instruction,
    tools=tools,
    generation_config={
        "temperature": 0.7,  # Lower temperature for more deterministic output
        "top_p": 0.95,       # Slightly lower top_p
        "top_k": 40,         # Add top_k for additional control
        "max_output_tokens": 2048,  # Limit response length
    }
)
```

### Monitoring Dashboard

Create a monitoring dashboard to track:
- Duplication rate over time
- Duplication by session
- Duplication by model
- Duplication by message type
- Response quality metrics

This will help identify patterns and prevent regressions.
