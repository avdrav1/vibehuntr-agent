# Content-Level Duplication Issue

## Problem

The current duplicate detection in `agent_invoker.py` uses hash-based chunk detection, which prevents the same chunk from being yielded twice during streaming. However, it doesn't detect when the LLM generates the same content twice as part of its natural response.

## Example

In the "South Philly Italian" conversation, the agent generated:

```
Okay, I found five Italian restaurants in South Philly. Only La Sera Italiana BYOB, Villa di 
Roma and L'Angolo Ristorante have price ratings, and all are $$. The other two, Fiorella 
Pasta and La Nonna, do not have price ratings.

[venue list]

Would you like to explore any of these further? I can get more details.
Okay, I found five Italian restaurants in South Philly. Only La Sera Italiana BYOB, Villa di 
Roma and L'Angolo Ristorante have price ratings, and all are $$. The other two, Fiorella 
Pasta and La Nonna, do not have price ratings.

[venue list again]
```

The paragraph and venue list appear twice in the response.

## Root Cause

This type of duplication occurs at the LLM generation level, not the streaming level. Possible causes:

1. **Tool called twice**: The agent may be calling `search_venues_tool` twice with the same parameters
2. **LLM repetition**: The LLM may be generating the same summary twice in its response
3. **Context injection issue**: The context string may be causing the LLM to repeat information

## Current Detection

The hash-based detection in `agent_invoker.py` works like this:

```python
chunk_hash = get_chunk_hash(new_content)
if chunk_hash not in yielded_chunk_hashes:
    yielded_chunk_hashes.add(chunk_hash)
    yield {'type': 'text', 'content': new_content}
```

This catches:
- ✅ Same chunk yielded multiple times during streaming
- ✅ Accumulated message re-sends
- ❌ LLM generating same content twice in different chunks
- ❌ Tool being called twice with same results

## Solution

We need to add **content-level duplicate detection** that:

1. Tracks sentences or paragraphs in the accumulated response
2. Detects when a new chunk contains content that's already in the accumulated response
3. Filters out the duplicate portion before yielding

### Implementation Approach

```python
def contains_duplicate_content(accumulated: str, new_chunk: str, threshold: float = 0.8) -> bool:
    """
    Check if new_chunk contains content that's already in accumulated response.
    
    Uses sentence-level similarity matching to detect repeated content.
    """
    # Split into sentences
    accumulated_sentences = split_sentences(accumulated)
    new_sentences = split_sentences(new_chunk)
    
    # Check if any new sentence is very similar to an existing sentence
    for new_sent in new_sentences:
        for acc_sent in accumulated_sentences:
            similarity = calculate_similarity(new_sent, acc_sent)
            if similarity >= threshold:
                return True
    
    return False
```

### Alternative: Tool Call Tracking

Another approach is to track tool calls and prevent the same tool from being called twice with identical parameters:

```python
tool_call_cache: Dict[str, Any] = {}

def track_tool_call(tool_name: str, args: Dict) -> Optional[Any]:
    """
    Track tool calls and return cached result if tool was already called.
    """
    cache_key = f"{tool_name}:{json.dumps(args, sort_keys=True)}"
    
    if cache_key in tool_call_cache:
        logger.warning(f"Tool {tool_name} called twice with same args, using cached result")
        return tool_call_cache[cache_key]
    
    return None
```

## Recommended Fix

1. Add sentence-level duplicate detection to `duplicate_detector.py`
2. Integrate it into the streaming loop in `agent_invoker.py`
3. Log when content-level duplicates are detected
4. Add tests to verify the fix

## Testing

Create a test that:
1. Simulates the exact conversation flow that triggered the duplicate
2. Verifies that the response doesn't contain repeated paragraphs
3. Checks that tool calls aren't duplicated

```python
def test_no_content_duplication():
    """Test that LLM-generated content isn't duplicated."""
    agent = get_agent()
    session_id = "test_content_dup"
    
    # Simulate the conversation
    invoke_agent_streaming(agent, "Italian food", session_id)
    invoke_agent_streaming(agent, "$$$", session_id)
    
    response_chunks = []
    for item in invoke_agent_streaming(agent, "South Philly Italian", session_id):
        if item['type'] == 'text':
            response_chunks.append(item['content'])
    
    response = ''.join(response_chunks)
    
    # Check for duplicate paragraphs
    paragraphs = response.split('\n\n')
    unique_paragraphs = set(paragraphs)
    
    assert len(paragraphs) == len(unique_paragraphs), \
        f"Found duplicate paragraphs: {len(paragraphs)} total, {len(unique_paragraphs)} unique"
```

## Priority

**HIGH** - This affects user experience significantly and undermines trust in the agent's responses.
