# Design Document: Enhanced Context Retention

## Overview

This design addresses the persistent context retention issues in the Vibehuntr agent by implementing a multi-layered approach:

1. **Enhanced Context Manager**: Improved entity extraction and storage
2. **Explicit Context Injection**: Structured context prepended to every message
3. **Agent Instruction Optimization**: Better prompts for context awareness
4. **Context Visibility UI**: User-facing display of active context
5. **Comprehensive Logging**: Debugging and observability

The solution combines ADK's built-in session management with explicit context injection to ensure reliable context retention across conversation turns.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Chat Input   │  │ Message List │  │ Context Display  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                         Backend API                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Chat Endpoint (SSE)                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent Invoker Layer                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  1. Get/Create Session                               │   │
│  │  2. Extract Context from User Message                │   │
│  │  3. Inject Context into Message                      │   │
│  │  4. Invoke Agent with Enhanced Message               │   │
│  │  5. Extract Entities from Agent Response             │   │
│  │  6. Update Context with Response Entities            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Context Manager                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  - Location Tracking                                 │   │
│  │  - Search Query Tracking                             │   │
│  │  - Entity List Management (Recent 5)                 │   │
│  │  - Reference Resolution                              │   │
│  │  - Context String Generation                         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      ADK Agent                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  - Model: gemini-2.0-flash-exp                       │   │
│  │  - Enhanced Instructions                             │   │
│  │  - Session Service (Auto History)                    │   │
│  │  - Tools: Places + Event Planning                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```



## Components and Interfaces

### 1. Enhanced Context Manager (`app/event_planning/context_manager.py`)

**Purpose**: Track and manage conversation context across message turns.

**Key Classes**:

```python
@dataclass
class VenueInfo:
    """Information about a venue mentioned in conversation."""
    name: str
    place_id: str
    location: Optional[str] = None
    mentioned_at: datetime = field(default_factory=datetime.now)

@dataclass
class ConversationContext:
    """Tracks key information across conversation turns."""
    
    # Current search context
    search_query: Optional[str] = None
    location: Optional[str] = None
    
    # Recently mentioned venues (last 5, ordered by recency)
    recent_venues: List[VenueInfo] = field(default_factory=list)
    
    # Last user intent (for debugging)
    last_user_intent: Optional[str] = None
    
    # Timestamp of last update
    last_updated: datetime = field(default_factory=datetime.now)
```

**Key Methods**:

- `update_from_user_message(message: str) -> None`: Extract location, search query, and intent from user message
- `update_from_agent_message(message: str) -> None`: Extract venues and Place IDs from agent response
- `get_context_string() -> str`: Generate formatted context string for injection
- `find_venue_by_reference(reference: str) -> Optional[VenueInfo]`: Resolve vague references to entities
- `clear() -> None`: Clear all context for session reset

**Enhanced Extraction Patterns**:

```python
# Location patterns (expanded)
LOCATION_PATTERNS = [
    r'\b(philadelphia|philly|nyc|new york|boston|chicago|sf|san francisco|la|los angeles|seattle|portland|austin|miami|denver)\b',
    r'\bin\s+([a-z\s]+)',
    r'\baround\s+([a-z\s]+)',
    r'\bnear\s+([a-z\s]+)',
]

# Search query patterns (expanded)
SEARCH_PATTERNS = [
    r'\b(cheesesteak|pizza|sushi|italian|chinese|mexican|thai|indian|burger|taco|ramen|pho|bbq)s?\b',
    r'\b(restaurant|bar|cafe|coffee|food|dining|eatery)\b',
    r'\b(brunch|lunch|dinner|breakfast)\b',
]

# Venue extraction from agent response
VENUE_PATTERN = r'\*\*([^*]+)\*\*.*?Place ID:\s*(ChI[a-zA-Z0-9_-]+)'
```

### 2. Agent Invoker with Context Injection (`app/event_planning/agent_invoker.py`)

**Purpose**: Invoke agent with explicit context injection.

**Enhanced Flow**:

```python
def invoke_agent_streaming(agent, message, session_id, user_id, yield_tool_calls=False):
    # 1. Get or create ADK session
    session = _session_service.get_session_sync(session_id=session_id)
    
    # 2. Get context manager for this session
    context = get_context(session_id)
    
    # 3. Extract context from user message
    context.update_from_user_message(message)
    
    # 4. Generate context string
    context_string = context.get_context_string()
    
    # 5. Inject context into message
    if context_string:
        enhanced_message = f"[CONTEXT: {context_string}]\n\n{message}"
        logger.info(f"Injected context: {context_string}")
    else:
        enhanced_message = message
    
    # 6. Create message content
    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=enhanced_message)]
    )
    
    # 7. Run agent (ADK handles history automatically)
    runner = Runner(agent=agent, session_service=_session_service)
    events = runner.run(
        new_message=content,
        user_id=user_id,
        session_id=session_id,
        run_config=RunConfig(streaming_mode=StreamingMode.SSE)
    )
    
    # 8. Stream response and accumulate
    accumulated_text = ""
    for event in events:
        # ... yield tokens ...
        accumulated_text += token
    
    # 9. Extract entities from agent response
    context.update_from_agent_message(accumulated_text)
    
    return accumulated_text
```



### 3. Enhanced Agent Instructions (`app/agent.py`)

**Purpose**: Provide explicit context retention rules to the agent.

**Enhanced Instruction Template**:

```python
instruction = """You are a friendly AI assistant that helps people plan events with their friends.

CRITICAL CONTEXT RETENTION RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. ALWAYS READ THE [CONTEXT: ...] PREFIX
   - Every message may start with [CONTEXT: key: value | key: value]
   - This contains critical information from the conversation
   - Use this context to avoid asking for repeated information

2. REMEMBER YOUR OWN RESPONSES
   - When you mention venues with Place IDs, remember them
   - When user says "more details" or "that one", refer to your last response
   - Extract Place IDs from your previous message, don't ask for them again

3. LOCATION PERSISTENCE
   - If context shows "Location: philly", use Philadelphia for all searches
   - Don't ask "what location?" if location is in context
   - Only ask for location if context doesn't have it

4. ENTITY REFERENCES
   - "that one" = most recent entity you mentioned
   - "the first one" = first entity in your last list
   - "more details" = user wants details about the last entity

EXAMPLES OF CORRECT BEHAVIOR:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Example 1: Location Persistence
User: "Indian food"
[CONTEXT: Location: philly]
You: "Great! Let me search for Indian restaurants in Philadelphia..."
✓ CORRECT - Used location from context

Example 2: Entity Reference
You: "I found Osteria. Place ID: ChIJabc123"
User: "more details"
[CONTEXT: Recently mentioned venues: Osteria (Place ID: ChIJabc123)]
You: [Call get_venue_details_tool(place_id="ChIJabc123")]
✓ CORRECT - Extracted Place ID from context

Example 3: Search Query Persistence
User: "Indian food"
[CONTEXT: Location: philly]
You: "Here are some Indian restaurants..."
User: "any with outdoor seating?"
[CONTEXT: Location: philly | User is looking for: indian]
You: "Let me filter those Indian restaurants for outdoor seating..."
✓ CORRECT - Remembered the search query

EXAMPLES OF INCORRECT BEHAVIOR (DO NOT DO THIS):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ WRONG Example 1:
You: "I found Osteria. Place ID: ChIJabc123"
User: "more details"
You: "Could you please provide the Place ID?"
❌ WRONG - You just provided it!

❌ WRONG Example 2:
User: "Indian food"
[CONTEXT: Location: philly]
You: "What location would you like to search in?"
❌ WRONG - Location is in context!

❌ WRONG Example 3:
User: "philly"
You: "Great! What would you like to do in Philadelphia?"
User: "Indian food"
You: "What location should I search in?"
❌ WRONG - User already said philly!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Always be helpful, clear, and encouraging! Use emojis to celebrate successes (✓, 🎉).
"""
```



### 4. Context Display UI Component (`frontend/src/components/ContextDisplay.tsx`)

**Purpose**: Show users what context the agent is tracking.

**Component Structure**:

```typescript
interface ContextDisplayProps {
  sessionId: string;
  context: ConversationContext;
  onClearContext: () => void;
  onClearItem: (itemType: 'location' | 'query' | 'venue', index?: number) => void;
}

interface ConversationContext {
  location?: string;
  searchQuery?: string;
  recentVenues: Array<{
    name: string;
    placeId: string;
    location?: string;
  }>;
}
```

**Visual Design**:

```
┌─────────────────────────────────────────────────────────┐
│  💭 Agent Memory                              [Clear All]│
├─────────────────────────────────────────────────────────┤
│  📍 Location: Philadelphia                          [×] │
│  🔍 Looking for: Indian food                        [×] │
│  🏪 Recent venues:                                      │
│     • Osteria Ama Philly (ChIJabc...)              [×] │
│     • Vedge Restaurant (ChIJdef...)                [×] │
└─────────────────────────────────────────────────────────┘
```

**Styling** (Vibehuntr theme):
- Background: `rgba(139, 92, 246, 0.1)` (purple with transparency)
- Border: `1px solid rgba(139, 92, 246, 0.3)`
- Text: `#e5e7eb` (light gray)
- Chips: Dark background with purple accent
- Clear buttons: Subtle hover effect

### 5. Backend Context API (`backend/app/api/context.py`)

**Purpose**: Provide API endpoints for context management.

**New Endpoints**:

```python
@router.get("/api/context/{session_id}")
async def get_context(session_id: str) -> ContextResponse:
    """Get current context for a session."""
    context = get_context(session_id)
    return ContextResponse(
        location=context.location,
        search_query=context.search_query,
        recent_venues=[
            VenueResponse(
                name=v.name,
                place_id=v.place_id,
                location=v.location
            )
            for v in context.recent_venues
        ]
    )

@router.delete("/api/context/{session_id}")
async def clear_context(session_id: str) -> StatusResponse:
    """Clear all context for a session."""
    clear_context(session_id)
    return StatusResponse(success=True)

@router.delete("/api/context/{session_id}/item")
async def clear_context_item(
    session_id: str,
    item_type: str = Query(...),
    index: Optional[int] = Query(None)
) -> StatusResponse:
    """Clear a specific context item."""
    context = get_context(session_id)
    
    if item_type == "location":
        context.location = None
    elif item_type == "query":
        context.search_query = None
    elif item_type == "venue" and index is not None:
        if 0 <= index < len(context.recent_venues):
            context.recent_venues.pop(index)
    
    return StatusResponse(success=True)
```



## Data Models

### ConversationContext

```python
@dataclass
class ConversationContext:
    """Tracks key information across conversation turns."""
    
    # Current search context
    search_query: Optional[str] = None
    location: Optional[str] = None
    
    # Recently mentioned venues (last 5, ordered by recency)
    recent_venues: List[VenueInfo] = field(default_factory=list)
    
    # Last user intent (for debugging)
    last_user_intent: Optional[str] = None
    
    # Timestamp of last update
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "search_query": self.search_query,
            "location": self.location,
            "recent_venues": [
                {
                    "name": v.name,
                    "place_id": v.place_id,
                    "location": v.location,
                    "mentioned_at": v.mentioned_at.isoformat()
                }
                for v in self.recent_venues
            ],
            "last_user_intent": self.last_user_intent,
            "last_updated": self.last_updated.isoformat()
        }
```

### VenueInfo

```python
@dataclass
class VenueInfo:
    """Information about a venue mentioned in conversation."""
    name: str
    place_id: str
    location: Optional[str] = None
    mentioned_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "name": self.name,
            "place_id": self.place_id,
            "location": self.location,
            "mentioned_at": self.mentioned_at.isoformat()
        }
```

### API Response Models

```python
class VenueResponse(BaseModel):
    """Venue information in API responses."""
    name: str
    place_id: str
    location: Optional[str] = None

class ContextResponse(BaseModel):
    """Context information in API responses."""
    location: Optional[str] = None
    search_query: Optional[str] = None
    recent_venues: List[VenueResponse] = []

class StatusResponse(BaseModel):
    """Generic status response."""
    success: bool
    message: Optional[str] = None
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Location extraction and storage
*For any* user message containing a location mention, extracting and storing the location should result in the context having that location value.
**Validates: Requirements 1.1**

### Property 2: Location persistence across messages
*For any* session with stored location context, sending a message without a location should result in the stored location being available for use.
**Validates: Requirements 1.2**

### Property 3: Location injection into messages
*For any* message processed with stored location context, the enhanced message should contain the location in the context prefix.
**Validates: Requirements 1.3**

### Property 4: Location update on explicit change
*For any* session with stored location, setting a new location should result in the new location being used for subsequent operations.
**Validates: Requirements 1.4**

### Property 5: Venue extraction from agent responses
*For any* agent response containing venue names and Place IDs, parsing the response should extract all venues correctly.
**Validates: Requirements 2.1**

### Property 6: Vague reference resolution
*For any* session with recent venues, resolving a vague reference like "that one" or "the first one" should return the correct venue from the list.
**Validates: Requirements 2.2**

### Property 7: Entity injection after resolution
*For any* resolved entity reference, the injected context should contain the entity's Place ID and name.
**Validates: Requirements 2.3**

### Property 8: Venue list size limit
*For any* session, adding more than 5 venues should result in only the 5 most recent venues being stored.
**Validates: Requirements 2.4**

### Property 9: Ordinal reference resolution
*For any* session with multiple venues, resolving ordinal references ("first", "second") should return the venue at the correct position.
**Validates: Requirements 2.5**

### Property 10: Search query extraction
*For any* user message containing a search query (food type, activity), extracting the query should store it in the context.
**Validates: Requirements 3.1**

### Property 11: Search query injection
*For any* session with stored search query, the injected context should include the query.
**Validates: Requirements 3.2**

### Property 12: Search query update
*For any* session with stored search query, specifying a new query should update the stored value.
**Validates: Requirements 3.3**

### Property 13: Combined context injection
*For any* session with both location and search query, the injected context should include both values.
**Validates: Requirements 3.4**

### Property 14: Entity extraction from agent responses
*For any* agent response, parsing should extract all entities (venues, Place IDs) mentioned in the response.
**Validates: Requirements 4.1, 4.2**

### Property 15: Bidirectional entity tracking
*For any* session, the injected context should include entities from both user messages and agent responses.
**Validates: Requirements 4.3**

### Property 16: Entity list size limit
*For any* session, the context should keep only the 3 most recent entities to avoid token limits.
**Validates: Requirements 4.5**

### Property 17: Context string generation
*For any* non-empty context, generating a context string should produce a non-empty formatted string.
**Validates: Requirements 5.1**

### Property 18: Context string format
*For any* generated context string, it should match the pattern "[CONTEXT: key: value | key: value]".
**Validates: Requirements 5.2**

### Property 19: Context prepending
*For any* message with available context, the enhanced message should start with the context string.
**Validates: Requirements 5.3**

### Property 20: Context logging
*For any* context injection operation, a log entry should be created with the session_id and context string.
**Validates: Requirements 5.5, 7.2**

### Property 21: Multi-turn context accumulation
*For any* sequence of messages in a session, the context should accumulate information from all messages.
**Validates: Requirements 8.1**

### Property 22: Context preservation on update
*For any* context update, existing values should be preserved unless explicitly overridden.
**Validates: Requirements 8.2**

### Property 23: Context conflict resolution
*For any* context with conflicting values (e.g., two different locations), the most recent value should be used.
**Validates: Requirements 8.5**

### Property 24: Session context isolation
*For any* two different sessions, context from one session should not be accessible from the other.
**Validates: Requirements 10.4**

### Property 25: Context clearing
*For any* session, clearing the context should remove all stored values.
**Validates: Requirements 10.2**

### Property 26: Context clear logging
*For any* context clear operation, a log entry should be created with the session_id and timestamp.
**Validates: Requirements 10.3**

### Property 27: UI context display
*For any* session with context, the UI should display the location, search query, and recent venues.
**Validates: Requirements 11.2**

### Property 28: UI real-time updates
*For any* context update during conversation, the UI should reflect the changes immediately.
**Validates: Requirements 11.4**

### Property 29: UI context clearing
*For any* context item in the UI, clicking the clear button should remove that item from the context.
**Validates: Requirements 11.6**



## Error Handling

### Context Extraction Errors

**Scenario**: Regex patterns fail to match or extraction throws exception

**Handling**:
- Log the error with message content (truncated for privacy)
- Continue with empty context rather than failing the request
- Return gracefully degraded service

```python
try:
    context.update_from_user_message(message)
except Exception as e:
    logger.error(f"Context extraction failed: {e}", exc_info=True)
    # Continue without context - don't break the flow
```

### Context Injection Errors

**Scenario**: Context string generation fails or injection causes issues

**Handling**:
- Log the error with session_id
- Send original message without context injection
- Alert monitoring system for investigation

```python
try:
    context_string = context.get_context_string()
    enhanced_message = f"[CONTEXT: {context_string}]\n\n{message}"
except Exception as e:
    logger.error(f"Context injection failed: {e}", exc_info=True)
    enhanced_message = message  # Fallback to original
```

### Entity Resolution Errors

**Scenario**: Vague reference cannot be resolved to an entity

**Handling**:
- Log the failed resolution attempt
- Return None to indicate no match
- Let agent handle the ambiguity naturally

```python
def find_venue_by_reference(self, reference: str) -> Optional[VenueInfo]:
    try:
        # ... resolution logic ...
        return matched_venue
    except Exception as e:
        logger.warning(f"Entity resolution failed for '{reference}': {e}")
        return None
```

### API Errors

**Scenario**: Context API endpoints fail

**Handling**:
- Return appropriate HTTP status codes (400, 404, 500)
- Include error message in response
- Log full error details server-side

```python
@router.get("/api/context/{session_id}")
async def get_context(session_id: str) -> ContextResponse:
    try:
        context = get_context(session_id)
        return ContextResponse(...)
    except Exception as e:
        logger.error(f"Failed to get context for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### UI Error Handling

**Scenario**: Context display fails to load or update

**Handling**:
- Show error state in UI component
- Provide retry button
- Don't block chat functionality

```typescript
try {
  const context = await fetchContext(sessionId);
  setContext(context);
} catch (error) {
  console.error('Failed to load context:', error);
  setError('Unable to load agent memory. Chat will continue to work.');
}
```



## Testing Strategy

### Unit Testing

**Context Manager Tests** (`tests/unit/test_context_manager.py`):
- Test location extraction from various message formats
- Test search query extraction patterns
- Test venue extraction from agent responses
- Test entity reference resolution (ordinal, vague references)
- Test context string generation
- Test context clearing
- Test venue list size limiting (max 5)

**Agent Invoker Tests** (`tests/unit/test_agent_invoker_context.py`):
- Test context injection into messages
- Test message enhancement with context
- Test context extraction from user messages
- Test context update from agent responses
- Test error handling when context operations fail

**API Tests** (`tests/unit/test_context_api.py`):
- Test GET /api/context/{session_id}
- Test DELETE /api/context/{session_id}
- Test DELETE /api/context/{session_id}/item
- Test error responses for invalid session_ids
- Test concurrent context access

### Property-Based Testing

**Property Testing Framework**: hypothesis (Python), fast-check (TypeScript)

**Test Configuration**: Minimum 100 iterations per property test

**Property Tests** (`tests/property/test_properties_context_retention.py`):

Each property test must be tagged with:
```python
# Feature: enhanced-context-retention, Property 1: Location extraction and storage
```

**Key Property Tests**:

1. **Property 1**: Location extraction and storage
   - Generate random messages with location mentions
   - Verify location is extracted and stored correctly

2. **Property 8**: Venue list size limit
   - Generate random number of venues (0-20)
   - Verify only last 5 are kept

3. **Property 18**: Context string format
   - Generate random context states
   - Verify format matches "[CONTEXT: key: value | key: value]"

4. **Property 21**: Multi-turn context accumulation
   - Generate sequence of messages
   - Verify context accumulates correctly

5. **Property 24**: Session context isolation
   - Generate multiple sessions with different context
   - Verify no cross-contamination

### Integration Testing

**End-to-End Context Flow** (`tests/integration/test_context_flow.py`):

```python
async def test_full_context_retention_flow():
    """Test complete context retention across multiple turns."""
    
    # Turn 1: User mentions location
    response1 = await send_message("Indian food in philly")
    assert "philadelphia" in response1.lower()
    
    # Turn 2: Follow-up without location
    response2 = await send_message("any with outdoor seating?")
    # Should use philly from context, not ask for location
    assert "location" not in response2.lower()
    assert "outdoor" in response2.lower()
    
    # Turn 3: Vague reference
    response3 = await send_message("more details on the first one")
    # Should resolve to first venue from response2
    assert "place_id" in response3.lower()
```

**UI Integration Tests** (`frontend/src/test/ContextDisplay.test.tsx`):

```typescript
test('context display updates in real-time', async () => {
  render(<ChatInterface />);
  
  // Send message with location
  await userEvent.type(screen.getByRole('textbox'), 'Indian food in philly');
  await userEvent.click(screen.getByRole('button', { name: /send/i }));
  
  // Verify context display shows location
  await waitFor(() => {
    expect(screen.getByText(/Location: Philadelphia/i)).toBeInTheDocument();
  });
  
  // Send follow-up with search query
  await userEvent.type(screen.getByRole('textbox'), 'with outdoor seating');
  await userEvent.click(screen.getByRole('button', { name: /send/i }));
  
  // Verify context display shows both location and query
  await waitFor(() => {
    expect(screen.getByText(/Location: Philadelphia/i)).toBeInTheDocument();
    expect(screen.getByText(/Looking for: indian/i)).toBeInTheDocument();
  });
});
```

### Manual Testing Scenarios

**Scenario 1: Location Persistence**
1. User: "Indian food"
2. Agent: "What location?"
3. User: "philly"
4. Agent: Shows results
5. User: "any with parking?"
6. Expected: Agent uses philly, doesn't ask for location again

**Scenario 2: Entity Reference**
1. User: "restaurants in philly"
2. Agent: Lists 3 restaurants with Place IDs
3. User: "more details on the first one"
4. Expected: Agent calls get_venue_details with correct Place ID

**Scenario 3: Context Display**
1. User: "Indian food in philly"
2. Expected: Context display shows "Location: Philadelphia" and "Looking for: indian"
3. User clicks [×] next to location
4. Expected: Location removed from context display
5. User: "any in NYC?"
6. Expected: Context display updates to "Location: NYC"

