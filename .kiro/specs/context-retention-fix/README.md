# Context Retention Fix

This directory contains documentation and implementation details for fixing the context retention issue where the agent loses track of information from its own previous responses.

## Problem

The agent would show venue details (including Place IDs) and then ask the user to provide that same information when they said "more details":

```
Agent: "I found Osteria Ama Philly. Place ID: ChIJaSuyUYrHxokR-4BpMKOWt1M"
User: "more details"
Agent: "Could you please specify which venue and provide the Place ID?" ❌
```

## Root Cause

This was **not** a context window issue. The ADK session service correctly maintains conversation history. The issue was:

1. Agent instructions didn't explicitly guide context retention behavior
2. Tools are stateless and don't support implicit references
3. The LLM wasn't consistently parsing its own previous responses

See `INVESTIGATION_FINDINGS.md` for detailed analysis.

## Solution Implemented

**Quick Fix: Enhanced Agent Instructions**

Added explicit context retention rules and examples to the agent instructions in:
- `app/agent.py` (both variants)
- `app/event_planning/simple_agent.py`

The enhanced instructions tell the agent to:
- Remember information from its previous responses
- Extract Place IDs and other identifiers from its own messages
- Never ask users to repeat information it just provided
- Interpret "more details" as referring to recent entities

See `QUICK_FIX_IMPLEMENTATION.md` for implementation details.

## Testing

### Manual Testing

Run the manual test script:
```bash
python test_context_retention_manual.py
```

This will test:
1. Venue search follow-up (the original issue)
2. Event planning context retention

### Integration Testing

Test in the actual application:
1. Start the frontend + backend or playground
2. Search for venues: "Find Italian restaurants in Philadelphia"
3. When results appear, say: "more details"
4. **Expected**: Agent provides details without asking for Place ID
5. **Not Expected**: Agent asks you to specify which venue

## Files

- `README.md` - This file
- `INVESTIGATION_FINDINGS.md` - Detailed root cause analysis
- `QUICK_FIX_IMPLEMENTATION.md` - Implementation details
- `../../test_context_retention_manual.py` - Manual test script

## Next Steps

If the quick fix doesn't fully resolve the issue:

1. **Stateful Tool Wrapper**: Add memory for recent search results
2. **Agent State Management**: Implement proper working memory
3. **Tool Redesign**: Add convenience methods for implicit references

See `INVESTIGATION_FINDINGS.md` for comprehensive solution approaches.

## Rollback

If this fix causes issues, revert by removing the "CRITICAL CONTEXT RETENTION RULES" section from:
- `app/agent.py`
- `app/event_planning/simple_agent.py`
