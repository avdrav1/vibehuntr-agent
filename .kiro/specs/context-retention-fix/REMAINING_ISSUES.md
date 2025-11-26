# Remaining Issues After Agent Memory Fix

## Status Summary

✅ **FIXED**: Agent Memory now shows context in UI  
⚠️ **PARTIAL**: Venues not being added to Agent Memory  
⚠️ **ONGOING**: Duplicate responses still appearing  
⚠️ **REGRESSION**: "More details" not showing embed links  

## Issue 1: Venues Not Being Added to Agent Memory

### Problem
When the agent searches for venues, they appear in the chat but are not added to the "Recent Venues" section of Agent Memory.

### Root Cause
The context manager's regex pattern for extracting venues from agent responses doesn't match the actual format returned by the `search_venues_tool`.

**Expected Pattern:**
```
**Venue Name** ... Place ID: ChI...
```

**Actual Format:**
```
1. **Venue Name**
   📍 Address
   ⭐⭐⭐⭐ 4.5/5
   💰 Price: $$
   🆔 Place ID: ChI...
```

### Fix Applied
Updated the regex pattern in `context_manager.py` to handle the emoji prefix:

```python
# Before
venue_pattern = r'\*\*([^*]+)\*\*.*?Place ID:\s*(ChI[a-zA-Z0-9_-]+)'

# After  
venue_pattern = r'\*\*([^*]+)\*\*.*?(?:🆔\s*)?Place ID:\s*(ChI[a-zA-Z0-9_-]+)'
```

### Testing Needed
1. Search for venues: "Italian restaurants in South Philly"
2. Check Agent Memory sidebar
3. Verify venues appear in "Recent Venues" section

---

## Issue 2: Duplicate Responses Still Appearing

### Problem
Despite the duplication fix, responses are still showing duplicates in the UI.

### Root Cause
Gemini 2.0 Flash Exp sends tokens in a different format than expected:
- Each event contains a complete new chunk (not accumulated)
- This triggers the "Unexpected: part.text doesn't start with accumulated_text" path
- The duplicate detection logic in that path isn't working correctly

### Evidence from Logs
```
2025-11-25 08:09:36,271 - app.event_planning.agent_invoker - WARNING - Unexpected: part.text doesn't start with accumulated_text (len=47)
2025-11-25 08:09:36,439 - app.event_planning.agent_invoker - WARNING - Unexpected: part.text doesn't start with accumulated_text (len=100)
```

### Potential Solutions

**Option 1: Fix the "Unexpected" Path**
The current logic treats each new chunk as unique when it doesn't start with accumulated text. We need to:
1. Track all yielded chunks separately
2. Check if the new chunk was already yielded
3. Only yield truly new content

**Option 2: Adjust Accumulated Text Tracking**
Instead of expecting `part.text.startswith(accumulated_text)`, we should:
1. Track each individual chunk as it's yielded
2. Build accumulated text from yielded chunks
3. Compare new chunks against the set of yielded chunks

**Option 3: Model-Specific Handling**
Add special handling for Gemini 2.0 Flash Exp's streaming format:
1. Detect the model being used
2. Use different duplicate detection logic for this model
3. Treat each event as a new chunk (not accumulated)

### Recommended Approach
Option 2 is most robust. We should:
1. Maintain a set of yielded chunk hashes
2. Hash each new chunk before yielding
3. Only yield if hash is not in the set
4. This works regardless of how the model sends tokens

---

## Issue 3: "More Details" Not Showing Embed Links

### Problem
When user asks for "more details" about a venue, the response no longer shows clickable embed links to the restaurant.

### Possible Causes

**Cause 1: Link Preview Feature Disabled**
The link preview feature might have been disabled or broken during recent changes.

**Cause 2: URL Format Changed**
The `get_venue_details_tool` might not be returning URLs in the expected format.

**Cause 3: Frontend Link Detection Broken**
The frontend's URL extraction or link preview rendering might be broken.

### Investigation Needed

1. **Check Tool Output**
   - Look at what `get_venue_details_tool` returns
   - Verify it includes website URLs
   - Check the format of the URLs

2. **Check Frontend**
   - Verify `urlExtractor.ts` is working
   - Check `LinkPreview.tsx` component
   - Look for console errors in browser

3. **Check Backend**
   - Verify link preview API is working
   - Test `/api/link-preview` endpoint
   - Check for CORS issues

### Files to Check
- `app/event_planning/places_tools.py` - Tool output format
- `frontend/src/utils/urlExtractor.ts` - URL detection
- `frontend/src/components/LinkPreview.tsx` - Link rendering
- `backend/app/api/link_preview.py` - Link preview API

---

## Next Steps

### Priority 1: Verify Venue Extraction Fix
Test that venues are now being added to Agent Memory after the regex fix.

### Priority 2: Fix Duplicate Responses
Implement Option 2 (chunk hash tracking) to properly detect and prevent duplicates.

### Priority 3: Restore Link Previews
Investigate and fix the "more details" link preview functionality.

### Testing Checklist
- [ ] Venues appear in Agent Memory after search
- [ ] No duplicate text in agent responses
- [ ] "More details" shows clickable venue links
- [ ] Links show preview cards with venue info
- [ ] Context persists across conversation
- [ ] No regression in other features
