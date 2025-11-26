# Hash-Based Duplicate Detection Fix

## Problem

The previous duplicate detection logic was complex and didn't work correctly with Gemini 2.0 Flash Exp's streaming format:
- Expected accumulated messages (each event contains all previous text + new text)
- Gemini 2.0 Flash Exp sends standalone chunks (each event contains only new text)
- This caused "Unexpected: part.text doesn't start with accumulated_text" warnings
- Duplicate detection failed, causing duplicate text in responses

## Solution

Implemented a simpler hash-based duplicate detection system that works regardless of how the model sends tokens.

### Key Changes

**1. Added Hash-Based Tracking**
```python
# Track yielded chunks by hash
yielded_chunk_hashes: Set[str] = set()
accumulated_response = ""

def get_chunk_hash(text: str) -> str:
    """Generate a hash for a text chunk."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()
```

**2. Simplified Duplicate Detection**

Instead of complex string comparison and accumulated text tracking, we now:
1. Hash each chunk before yielding
2. Check if hash exists in the set
3. Only yield if hash is new
4. Add hash to set after yielding

**3. Handles Both Streaming Formats**

The fix works for both:
- **Accumulated format**: `part.text.startswith(accumulated_response)` - extract new part
- **Standalone format**: Each chunk is independent - hash and check

### Code Flow

```python
for event in events:
    if event.content and event.content.parts:
        for part in event.content.parts:
            if part.text:
                if part.text.startswith(accumulated_response):
                    # Accumulated format - extract new content
                    new_content = part.text[len(accumulated_response):]
                    if new_content:
                        chunk_hash = get_chunk_hash(new_content)
                        if chunk_hash not in yielded_chunk_hashes:
                            yielded_chunk_hashes.add(chunk_hash)
                            accumulated_response = part.text
                            yield {'type': 'text', 'content': new_content}
                else:
                    # Standalone format - check entire chunk
                    chunk_hash = get_chunk_hash(part.text)
                    if chunk_hash not in yielded_chunk_hashes:
                        yielded_chunk_hashes.add(chunk_hash)
                        accumulated_response += part.text
                        yield {'type': 'text', 'content': part.text}
```

### Benefits

1. **Simpler Logic**: No complex string comparison or state tracking
2. **Model Agnostic**: Works with any streaming format
3. **Reliable**: Hash collisions are extremely rare with MD5
4. **Efficient**: O(1) hash lookup vs O(n) string comparison
5. **Maintainable**: Easy to understand and debug

### Removed Complexity

- Removed dependency on `DuplicateDetector.get_accumulated_text()`
- Removed complex "Unexpected" path handling
- Removed multiple try-except blocks for duplicate detection
- Simplified error handling
- Reduced logging noise

### Testing

To verify the fix works:

1. **Test Accumulated Format**:
   - Send a message that triggers a long response
   - Verify no duplicate text appears
   - Check logs for "Yielding new content" messages

2. **Test Standalone Format**:
   - Send a message that triggers Places API calls
   - Verify venue information appears once
   - Check logs for "Yielding standalone chunk" messages

3. **Test Context Extraction**:
   - Search for venues
   - Verify venues appear in Agent Memory sidebar
   - Check logs for "Stored X new venue(s) in context"

### Metrics

The fix still tracks duplicates for metrics:
- Increments `metrics.increment_duplicate_detected()` when duplicates are skipped
- Logs duplicate detection at DEBUG level (not WARNING)
- Maintains compatibility with existing metrics system

### Files Modified

- `app/event_planning/agent_invoker.py`:
  - Added `hashlib` import
  - Added `Set` type import
  - Added hash-based tracking variables
  - Simplified event processing loop
  - Updated context extraction to use `accumulated_response`

### Performance Impact

- **Memory**: Minimal - stores hashes (32 bytes each) instead of full text
- **CPU**: Faster - O(1) hash lookup vs O(n) string comparison
- **Network**: No change - same number of tokens yielded

### Backward Compatibility

- Still works with existing `ResponseTracker` and metrics
- Still updates context from agent responses
- Still handles tool calls correctly
- No changes to API or external interfaces

## Next Steps

1. Test with various message types
2. Monitor logs for any remaining duplicate warnings
3. Verify venue extraction works correctly
4. Check that link previews still work
