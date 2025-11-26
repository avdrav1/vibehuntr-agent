# Final Duplicate Detection Fix

## Problem

Even with hash-based duplicate detection, duplicates were still appearing because:

1. Gemini 2.0 Flash Exp sends individual standalone chunks during streaming
2. At the END, it sends one final event with the COMPLETE accumulated response
3. This final complete message has a different hash than individual chunks
4. So it passed the hash check and was yielded as a "new" chunk

## Evidence from Logs

```
2025-11-25 08:27:15,683 - Yielding standalone chunk: 120 chars  # Chunk 11
2025-11-25 08:27:15,683 - Yielding standalone chunk: 643 chars  # Chunk 12 - DUPLICATE!
```

The 643-char chunk contains the entire response that was already sent in chunks 1-11.

## Solution

Added a check to detect when a "standalone" chunk actually contains the accumulated response:

```python
else:
    # part.text doesn't start with accumulated_response
    # This means it's a standalone chunk (Gemini 2.0 Flash Exp behavior)
    
    # Check if this is a final complete response re-send
    # If accumulated_response is substantial and part.text contains it, skip
    if accumulated_response and len(accumulated_response) > 100 and accumulated_response in part.text:
        logger.debug(f"Skipped final complete response re-send: {len(part.text)} chars")
        if metrics:
            try:
                metrics.increment_duplicate_detected(session_id)
            except:
                pass
        continue  # Skip this chunk entirely
    
    # Otherwise, treat as new standalone chunk
    chunk_hash = get_chunk_hash(part.text)
    if chunk_hash not in yielded_chunk_hashes:
        # ... yield it
```

## Logic Flow

For each `part.text` in the event stream:

1. **Check if accumulated format**: `part.text.startswith(accumulated_response)`
   - YES → Extract new content, hash it, yield if new
   - NO → Go to step 2

2. **Check if final complete re-send**: `accumulated_response in part.text` AND `len(accumulated_response) > 100`
   - YES → Skip entirely (this is a duplicate)
   - NO → Go to step 3

3. **Treat as standalone chunk**: Hash it, yield if new

## Why This Works

- **Accumulated format** (some models): Handled by step 1
- **Standalone chunks** (Gemini 2.0 Flash Exp): Handled by step 3
- **Final complete re-send** (Gemini 2.0 Flash Exp): Caught by step 2

The key insight is that if we've already accumulated 100+ characters and a new chunk CONTAINS that accumulated text, it must be a duplicate re-send of the complete response.

## Testing

To verify:
1. Search for "Italian restaurants in South Philly"
2. Check that the restaurant list appears ONCE (not twice)
3. Check logs for "Skipped final complete response re-send" message
4. Verify venues appear in Agent Memory sidebar

## Performance

- Minimal overhead: One string containment check per chunk
- Only checks when accumulated_response > 100 chars
- Prevents sending large duplicate responses to frontend

## Files Modified

- `app/event_planning/agent_invoker.py`: Added final complete response detection

## Related Issues

This fix addresses:
- ✅ Duplicate responses when searching for venues
- ✅ Duplicate text in multi-item lists
- ✅ Final accumulated response being sent twice
