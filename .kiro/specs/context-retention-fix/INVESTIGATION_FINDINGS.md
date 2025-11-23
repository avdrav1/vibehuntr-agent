# Context Retention Investigation Findings

## Issue Summary

The agent loses context between conversation turns, specifically:
- Agent finds a venue and displays details (including Place ID)
- User responds "more details"
- Agent asks user to specify which venue and provide the Place ID
- **Expected**: Agent should remember it just showed venue details
- **Actual**: Agent acts as if it has no memory of the previous response

## Root Cause Analysis

### 1. **ADK Session Service Handles Context Automatically**

The codebase uses ADK's `InMemorySessionService` which **automatically** maintains conversation history:

```python
# From agent_invoker.py
_session_service = InMemorySessionService()

# When invoking:
runner = Runner(
    agent=agent,
    session_service=_session_service,
    app_name="vibehuntr_playground"
)

events = runner.run(
    new_message=content,
    user_id=user_id,
    session_id=session_id,  # ADK uses this to retrieve history
    run_config=RunConfig(streaming_mode=StreamingMode.SSE)
)
```

**Key Finding**: The session_id is passed correctly, and ADK should automatically provide conversation history to the agent. The infrastructure is correct.

### 2. **Agent Instruction May Be Insufficient**

From `app/agent.py`, the agent instruction is:

```python
instruction = """You are a friendly AI assistant that helps people plan events with their friends.

You help users:
- Create profiles and set preferences
- Form groups with friends
- Find optimal meeting times
- Plan and organize events
- Provide feedback after events

Be conversational, helpful, and encouraging! Use emojis to celebrate successes (✓, 🎉).

When helping with event planning:
- Be proactive and suggest next steps
- Use natural language and be friendly
- Summarize complex information clearly
- If someone's request is ambiguous, ask clarifying questions

Example interactions:
- "I want to plan a hike" → Ask about group, timing, preferences
- "When can my group meet?" → Use find_optimal_time_tool
- "Create a user for me" → Ask for name and email
- "What are my groups?" → Use list_groups_tool with their name

Always be helpful, clear, and encouraging!"""
```

**Key Finding**: The instruction doesn't explicitly tell the agent to:
- Remember information from its own previous responses
- Use context from recent conversation turns
- Avoid asking for information it just provided

### 3. **Tool Design Doesn't Support State Retention**

From `places_tools.py`:

```python
def search_venues_tool(query: str, location: Optional[str] = None, ...) -> str:
    """Search for real venues and locations using Google Places."""
    # Returns formatted string with venue details including Place ID
    
def get_venue_details_tool(place_id: str) -> str:
    """Get detailed information about a specific venue including reviews."""
    # Requires place_id as input
```

**Key Finding**: The tools are stateless. When `search_venues_tool` returns results with Place IDs, there's no mechanism to:
- Store the last search results in agent state
- Allow the agent to reference "the venue I just showed you"
- Automatically pass Place IDs from search to details

### 4. **No Explicit Context Management in Agent State**

The agent doesn't maintain any working memory or state between turns beyond what ADK provides in the conversation history. When the agent says:

> "Would you like me to get more details on this venue, or would you like me to search for something else?"

And the user replies "more details", the agent needs to:
1. Parse its own previous message
2. Extract the Place ID from that message
3. Call `get_venue_details_tool` with that Place ID

**Key Finding**: The agent relies entirely on the LLM's ability to parse its own previous responses from the conversation history. If the LLM doesn't do this correctly, context is "lost".

## Why This Happens

This is a **prompt engineering and tool design issue**, not a technical infrastructure issue:

1. **LLM Behavior**: The underlying LLM (Gemini 2.5 Flash) may not consistently:
   - Parse structured data from its own previous responses
   - Maintain working memory of entities it just mentioned
   - Understand implicit references like "more details" = "details about the venue I just showed"

2. **Tool Interface Gap**: There's a mismatch between:
   - How the agent presents information (conversational, with embedded data)
   - How tools expect information (explicit parameters like place_id)
   - No intermediate state to bridge this gap

3. **Instruction Ambiguity**: The agent instruction doesn't explicitly guide the agent on:
   - How to handle follow-up requests
   - When to extract information from its own previous responses
   - How to maintain working memory of entities

## Proposed Solutions

### Solution 1: Enhanced Agent Instructions (Quick Fix)

Add explicit guidance to the agent instruction:

```python
instruction = """...

IMPORTANT CONTEXT RULES:
- Always remember information from your previous responses in this conversation
- When you mention specific entities (venues, Place IDs, etc.), remember them
- If a user says "more details" or "tell me more", refer to the most recent entity you mentioned
- Extract Place IDs from your own previous messages when needed
- Never ask users to repeat information you just provided

Example:
- You: "I found Osteria Ama Philly (Place ID: ChIJa...)"
- User: "more details"
- You: [Extract Place ID from your previous message and call get_venue_details_tool]
"""
```

### Solution 2: Stateful Tool Wrapper (Medium Fix)

Create a wrapper that maintains recent search results:

```python
class StatefulPlacesTools:
    def __init__(self):
        self.last_search_results = []
    
    def search_venues(self, query, location=None, ...):
        results = google_places_service.search(...)
        self.last_search_results = results  # Store for later
        return formatted_results
    
    def get_details_for_last_result(self, index: int = 0):
        """Get details for the Nth result from the last search."""
        if not self.last_search_results:
            return "No recent search results"
        place_id = self.last_search_results[index].place_id
        return self.get_venue_details(place_id)
```

### Solution 3: Structured State Management (Comprehensive Fix)

Implement proper agent state management:

```python
class AgentState:
    """Maintains working memory for the agent."""
    def __init__(self):
        self.current_venues = []
        self.current_event = None
        self.current_group = None
    
    def update_from_tool_call(self, tool_name, result):
        """Update state based on tool results."""
        if tool_name == "search_venues_tool":
            self.current_venues = parse_venues(result)
    
    def get_context_for_agent(self) -> str:
        """Provide current state as context to agent."""
        return f"Current venues in memory: {self.current_venues}"
```

### Solution 4: Improved Tool Design (Best Practice)

Redesign tools to support implicit references:

```python
def get_venue_details_tool(
    place_id: Optional[str] = None,
    venue_index: Optional[int] = None
) -> str:
    """
    Get detailed information about a venue.
    
    Args:
        place_id: Specific Place ID (if known)
        venue_index: Index from last search results (0 = first result)
    
    If neither is provided, returns details for the most recent venue.
    """
```

## Recommended Approach

**Phase 1 (Immediate)**:
1. Enhance agent instructions with explicit context retention rules
2. Add examples of handling follow-up questions

**Phase 2 (Short-term)**:
3. Implement stateful tool wrapper for Places API
4. Add "get details for last result" convenience method

**Phase 3 (Long-term)**:
5. Design comprehensive agent state management system
6. Refactor all tools to support implicit references
7. Add state persistence across sessions

## Testing Strategy

Property-based tests should verify:
1. **Context Retention**: Information from turn N is available in turn N+1
2. **Reference Resolution**: "more details" correctly resolves to recent entities
3. **Question Non-Repetition**: Agent doesn't ask for information it just provided
4. **State Consistency**: Agent state matches conversation history

Existing tests in `test_properties_context_retention.py` already cover these properties but use mocks. Real integration tests are needed.

## Related Files

- `app/agent.py` - Agent definition and instructions
- `app/event_planning/agent_invoker.py` - ADK invocation with session management
- `app/event_planning/places_tools.py` - Places API tool definitions
- `tests/property/test_properties_context_retention.py` - Property tests for context
- `.kiro/specs/playground-fix/requirements.md` - Requirements for context retention
- `.kiro/specs/playground-fix/design.md` - Design for context retention

## Conclusion

The issue is **not** a context window size problem. The ADK session service correctly maintains conversation history. The issue is that:

1. The agent instruction doesn't explicitly guide context retention behavior
2. The tools are stateless and don't support implicit references
3. The LLM doesn't consistently parse its own previous responses

The fix requires improving the agent's prompt engineering and potentially adding stateful tool wrappers, not increasing context window size.
