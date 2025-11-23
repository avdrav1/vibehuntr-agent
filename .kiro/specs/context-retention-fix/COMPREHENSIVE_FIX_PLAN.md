# Comprehensive Context Retention Fix Plan

## Problem Analysis

The context retention issue persists despite:
1. ✓ ADK InMemorySessionService correctly storing conversation history
2. ✓ Enhanced agent instructions about context retention
3. ✓ Generation config adjustments
4. ✓ Session ID properly passed to Runner

**Root Cause**: The LLM (Gemini 2.0/2.5 Flash) is not effectively using the conversation history that ADK provides. This is a known limitation with some LLMs - they have access to history but don't always reference it properly.

## Observed Behavior

```
Turn 1:
User: "cheesesteak"
Agent: "Where are you located?"

Turn 2:
User: "philly"
Agent: "Okay, I'm ready to help you plan something in Philly!"
       ❌ FORGOT user wants cheesesteak

Turn 3:
User: "cheesesteak" (repeating)
Agent: "Where are you located?"
       ❌ FORGOT they just said philly
```

## Why This Happens

1. **Model Attention**: Flash models prioritize recent tokens over older context
2. **Tool Calls**: When tools are involved, the model may lose track of user intent
3. **Multi-turn Complexity**: Each turn adds more tokens, diluting earlier context
4. **No Explicit State**: The model has no working memory beyond conversation history

## Comprehensive Solutions

### Solution 1: Explicit Context Injection (Recommended)

Modify the agent invoker to inject a context summary at the start of each user message:

```python
# Before sending to agent:
recent_turns = get_last_n_turns(session, n=2)
context_prefix = f"[CONTEXT: {summarize_turns(recent_turns)}]\n\n"
enhanced_message = context_prefix + user_message
```

**Pros**: Forces the model to see recent context
**Cons**: Adds tokens to each request

### Solution 2: Stateful Context Manager

Create a context manager that tracks key entities:

```python
class ConversationContext:
    def __init__(self):
        self.current_search_query = None
        self.current_location = None
        self.last_venues = []
        self.current_event = None
    
    def update_from_message(self, role, content):
        # Extract and store key information
        if "cheesesteak" in content.lower():
            self.current_search_query = "cheesesteak"
        if "philly" in content.lower():
            self.current_location = "Philadelphia"
    
    def get_context_string(self) -> str:
        parts = []
        if self.current_search_query:
            parts.append(f"Looking for: {self.current_search_query}")
        if self.current_location:
            parts.append(f"Location: {self.current_location}")
        return " | ".join(parts) if parts else "No active context"
```

**Pros**: Explicit state management
**Cons**: Requires maintaining state logic

### Solution 3: Use Gemini Pro Instead of Flash

Switch to `gemini-2.0-pro` or `gemini-1.5-pro` which have better context retention:

```python
event_planning_agent = Agent(
    name="event_planning_agent",
    model="gemini-2.0-pro",  # Better context retention
    instruction=instruction,
    tools=EVENT_PLANNING_TOOLS + PLACES_TOOLS,
)
```

**Pros**: Better model capabilities
**Cons**: Slower and more expensive

### Solution 4: Conversation Summarization

After every N turns, summarize the conversation and inject it:

```python
if turn_count % 3 == 0:
    summary = summarize_conversation(history)
    inject_system_message(f"Conversation summary: {summary}")
```

**Pros**: Keeps context manageable
**Cons**: Adds complexity

### Solution 5: Structured State in System Prompt

Update the system prompt dynamically with current state:

```python
base_instruction = "You are a helpful assistant..."

# Add dynamic context
current_state = f"""

CURRENT CONVERSATION STATE:
- User is looking for: {context.search_query or 'Not specified'}
- Location: {context.location or 'Not specified'}
- Last action: {context.last_action or 'None'}

IMPORTANT: Use this state information to maintain context across turns.
"""

full_instruction = base_instruction + current_state
```

**Pros**: Explicit state visible to model
**Cons**: Requires updating agent instruction per turn (not supported by ADK)

## Recommended Implementation

**Phase 1: Quick Win**
- Switch to `gemini-2.0-pro` for better context retention
- Add explicit context tracking in agent_invoker

**Phase 2: Robust Solution**
- Implement ConversationContext manager
- Inject context summary at start of each message
- Track key entities (search queries, locations, venues, events)

**Phase 3: Advanced**
- Add conversation summarization every N turns
- Implement smart context pruning
- Add explicit state management UI

## Implementation Priority

1. **HIGH**: Switch to Gemini Pro model
2. **HIGH**: Add context injection to messages
3. **MEDIUM**: Implement ConversationContext manager
4. **LOW**: Add conversation summarization

## Testing Strategy

Test with this exact scenario:
```
1. User: "cheesesteak"
2. Agent should ask: "Where?"
3. User: "philly"
4. Agent should: Search for cheesesteak in philly
5. User: "more details"
6. Agent should: Show details for first result
```

Success criteria:
- Agent remembers "cheesesteak" from turn 1 to turn 3
- Agent remembers "philly" from turn 3 to turn 5
- Agent remembers venue from turn 4 to turn 6

## Next Steps

Would you like me to implement:
A) Switch to Gemini Pro (quick, may help immediately)
B) Add context injection (more robust, requires code changes)
C) Both A and B
