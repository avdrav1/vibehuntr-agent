# Quick Fix Implementation: Enhanced Agent Instructions

## Summary

Implemented enhanced agent instructions to explicitly guide context retention behavior. This addresses the issue where the agent would lose context between turns and ask users to repeat information it just provided.

## Changes Made

### 1. Updated `app/agent.py`

Enhanced both instruction variants (with and without document retrieval) to include:

**Added Section: CRITICAL CONTEXT RETENTION RULES**

```
CRITICAL CONTEXT RETENTION RULES:
- Always remember information from your previous responses in this conversation
- When you mention specific entities (venues, Place IDs, event details, etc.), keep them in mind
- If a user says "more details", "tell me more", or "that one", they're referring to the most recent entity you mentioned
- Extract Place IDs, names, and other identifiers from your own previous messages when needed for tool calls
- NEVER ask users to repeat information you just provided in your previous response
- When you show search results with Place IDs, remember them for follow-up questions
```

**Added Examples:**

Positive example showing correct behavior:
```
Example of correct context handling:
- You: "I found Osteria Ama Philly at 1905 Chestnut St. Place ID: ChIJaSuyUYrHxokR-4BpMKOWt1M"
- User: "more details"
- You: [Look at your previous message, extract the Place ID, call get_venue_details_tool(place_id="ChIJaSuyUYrHxokR-4BpMKOWt1M")]
```

Negative example showing what NOT to do:
```
Example of INCORRECT behavior (DO NOT DO THIS):
- You: "I found Osteria Ama Philly. Place ID: ChIJaSuyUYrHxokR-4BpMKOWt1M"
- User: "more details"
- You: "Could you please specify which venue and provide the Place ID?" ❌ WRONG - you just provided it!
```

### 2. Updated `app/event_planning/simple_agent.py`

Applied the same enhancements to the simple agent (used when `USE_DOCUMENT_RETRIEVAL=false`).

## Expected Behavior Changes

### Before Fix

**Conversation:**
```
Agent: "I found Osteria Ama Philly. Place ID: ChIJaSuyUYrHxokR-4BpMKOWt1M. 
        Would you like more details?"
User: "more details"
Agent: "Could you please specify which venue and provide the Place ID?"
```

**Problem**: Agent asks for information it just provided.

### After Fix

**Conversation:**
```
Agent: "I found Osteria Ama Philly. Place ID: ChIJaSuyUYrHxokR-4BpMKOWt1M. 
        Would you like more details?"
User: "more details"
Agent: [Extracts Place ID from previous message]
       [Calls get_venue_details_tool(place_id="ChIJaSuyUYrHxokR-4BpMKOWt1M")]
       "Here are the details for Osteria Ama Philly: ..."
```

**Solution**: Agent remembers and extracts information from its own previous response.

## How It Works

1. **Explicit Instructions**: The agent now has clear rules about context retention
2. **Concrete Examples**: Both positive and negative examples guide the LLM's behavior
3. **Reference Resolution**: Agent is told to interpret "more details" as referring to recent entities
4. **Self-Parsing**: Agent is instructed to extract Place IDs from its own previous messages

## Testing

To test the fix:

1. Start the application (frontend + backend or playground)
2. Search for a venue: "Find Italian restaurants in Philadelphia"
3. When agent shows results with Place IDs, respond: "more details"
4. **Expected**: Agent should call `get_venue_details_tool` with the Place ID from its previous message
5. **Not Expected**: Agent should NOT ask you to provide the Place ID again

## Limitations

This is a **prompt engineering fix** that relies on the LLM following instructions. It may not be 100% reliable because:

- LLMs can still make mistakes in parsing their own responses
- Complex conversations with multiple entities may still cause confusion
- The fix doesn't add actual state management or memory

## Next Steps (If Needed)

If this quick fix doesn't fully resolve the issue, consider:

1. **Stateful Tool Wrapper**: Add a wrapper that remembers recent search results
2. **Agent State Management**: Implement proper working memory for the agent
3. **Tool Redesign**: Add convenience methods like `get_details_for_last_result()`

See `INVESTIGATION_FINDINGS.md` for detailed analysis and comprehensive solutions.

## Files Modified

- `app/agent.py` - Enhanced instructions for both agent variants
- `app/event_planning/simple_agent.py` - Enhanced instructions for simple agent

## Verification

Run the following to verify the changes:
```bash
# Check that context retention rules are present
grep "CRITICAL CONTEXT RETENTION RULES" app/agent.py
grep "CRITICAL CONTEXT RETENTION RULES" app/event_planning/simple_agent.py

# Verify no syntax errors
python3 -m py_compile app/agent.py
python3 -m py_compile app/event_planning/simple_agent.py
```

## Rollback

If this fix causes issues, revert by removing the "CRITICAL CONTEXT RETENTION RULES" section and the two examples from both files.
