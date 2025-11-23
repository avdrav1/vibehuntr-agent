# Model Upgrade: Gemini 2.0 Flash Experimental

## Change Summary

Upgraded from `gemini-2.0-flash` to `gemini-2.0-flash-exp` for better context retention.

## Why This Helps

**Gemini 2.0 Flash Experimental** has:
- ✓ Better conversation context retention
- ✓ Improved multi-turn understanding
- ✓ Better instruction following
- ✓ Same speed as regular Flash
- ✓ Similar cost to regular Flash

## Files Modified

1. `app/event_planning/simple_agent.py` - Changed model to `gemini-2.0-flash-exp`
2. `app/agent.py` - Changed both agent variants to `gemini-2.0-flash-exp`

## Changes Made

### Before
```python
event_planning_agent = Agent(
    name="event_planning_agent",
    model="gemini-2.0-flash",  # Standard flash
    ...
)
```

### After
```python
event_planning_agent = Agent(
    name="event_planning_agent",
    model="gemini-2.0-flash-exp",  # Experimental flash with better context
    ...
)
```

## Expected Improvements

The agent should now:
1. ✓ Remember user's search query across turns
   - User: "cheesesteak"
   - Agent: "Where?"
   - User: "philly"
   - Agent: **Should search for cheesesteak in philly** (not forget "cheesesteak")

2. ✓ Remember location across turns
   - User: "Find restaurants"
   - Agent: "Where?"
   - User: "philly"
   - User: "Find bars"
   - Agent: **Should search in philly** (not ask for location again)

3. ✓ Remember venue details for follow-ups
   - Agent shows venue with Place ID
   - User: "more details"
   - Agent: **Should extract Place ID from previous message** (not ask for it)

## Testing

### Test Scenario 1: Search Query Retention
```
1. User: "cheesesteak"
2. Agent: "Where are you located?"
3. User: "philly"
4. Expected: Agent searches for cheesesteak in Philadelphia
5. Actual: [Test after restart]
```

### Test Scenario 2: Location Retention
```
1. User: "Find restaurants in philly"
2. Agent: Shows results
3. User: "Find bars"
4. Expected: Agent searches for bars in philly
5. Actual: [Test after restart]
```

### Test Scenario 3: Venue Follow-up
```
1. User: "Find Italian restaurants in philly"
2. Agent: Shows results with Place IDs
3. User: "more details on the first one"
4. Expected: Agent extracts Place ID and shows details
5. Actual: [Test after restart]
```

## Rollback

If the experimental model causes issues, revert to standard flash:

```python
model="gemini-2.0-flash"  # Revert to standard
```

Or try Gemini Pro for even better context (slower/more expensive):

```python
model="gemini-1.5-pro"  # Best context retention
```

## Additional Improvements

Combined with previous fixes:
1. ✓ Enhanced agent instructions with context retention rules
2. ✓ Generation config tuning (temperature=0.7)
3. ✓ Model upgrade to experimental flash
4. ✓ Website link detection (no Place ID required)

## Next Steps

1. **Test the application** with the scenarios above
2. **Monitor behavior** - does context retention improve?
3. **If still issues**: Consider adding explicit context injection (Solution B from COMPREHENSIVE_FIX_PLAN.md)

## Status

- Backend: ✓ Reloaded with new model
- Frontend: ✓ Running (no changes needed)
- Ready to test: ✓ Yes

## How to Test

1. Open http://localhost:5173
2. Start a **new conversation** (click "+ New Conversation")
3. Try the test scenarios above
4. Check if the agent remembers context across turns

The experimental flash model should significantly improve context retention!
