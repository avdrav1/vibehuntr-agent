# Venue Website Links Feature

## Overview

Automatically detects venue information in agent responses and displays clickable website links as styled buttons below the message content.

## How It Works

### Detection

The Message component automatically scans assistant messages for venue information patterns:

```
**Venue Name**
📍 Address
🌐 Website: https://example.com
🆔 Place ID: ChIJabc123...
```

When all three elements are present (name, website, Place ID), a clickable link button is rendered.

### Visual Design

The link buttons feature:
- Vibehuntr gradient background (subtle pink/red)
- Globe icon (🌐) on the left
- Venue name in the center
- Arrow (→) on the right that slides on hover
- Smooth hover animations
- Opens in new tab with security attributes

### Example

**Agent Message:**
```
Found 1 venue for 'Italian restaurants':

1. **Osteria Ama Philly**
   📍 1905 Chestnut St, Philadelphia, PA 19103, USA
   ⭐⭐⭐⭐ 4.8/5 (1745 reviews)
   💰 Price: $$
   🌐 Website: https://www.osteriaamaphilly.com
   🆔 Place ID: ChIJaSuyUYrHxokR-4BpMKOWt1M
```

**Rendered Output:**
- Message text displays as normal
- Below the text, a styled button appears:
  ```
  [🌐 Visit Osteria Ama Philly →]
  ```
- Clicking opens the restaurant's website in a new tab

## Implementation Details

### Frontend Components

**Message.tsx**
- Added `venueLinks` state using `useMemo` for efficient parsing
- Extracts venue name, website URL, and Place ID from message content
- Renders link buttons below message content
- Only processes assistant messages (not user messages)

**index.css**
- Added `.venue-link-button` styles
- Gradient background matching Vibehuntr theme
- Hover animations (slide right, border glow)
- Responsive icon and text layout

### Pattern Matching

The component looks for these patterns:

1. **Venue Name**: `**Name**` or `1. **Name**`
2. **Website**: `🌐 Website: https://...` or `🌐 https://...`
3. **Place ID**: `🆔 Place ID: ChIJa...` or `Place ID: ChIJa...`

All three must be present in the same block (separated by double newlines) to create a link.

### Security

Links include security attributes:
- `target="_blank"` - Opens in new tab
- `rel="noopener noreferrer"` - Prevents security vulnerabilities

## Testing

### Unit Tests

`MessageVenueLinks.test.tsx` includes tests for:
- ✓ Single venue link extraction
- ✓ Multiple venue links
- ✓ No links for user messages
- ✓ No links when website missing
- ✓ No links when Place ID missing
- ✓ No links for non-venue messages
- ✓ Alternative Place ID format support

All tests pass.

### Manual Testing

1. Start the application
2. Search for venues: "Find Italian restaurants in Philadelphia"
3. Agent should show results with Place IDs and websites
4. Link buttons should appear below the message
5. Click a button to open the restaurant website

## Benefits

### User Experience
- **One-click access** to restaurant websites
- **Visual clarity** - buttons stand out from text
- **No copy/paste** needed for URLs
- **Consistent styling** with Vibehuntr theme

### Technical
- **Automatic detection** - no backend changes needed
- **Efficient parsing** - uses `useMemo` to avoid re-parsing
- **Flexible patterns** - handles multiple venue formats
- **Secure** - proper link security attributes

## Future Enhancements

Potential improvements:
1. **Phone number links** - Add click-to-call buttons
2. **Directions links** - Add "Get Directions" using Google Maps
3. **Booking integration** - Add "Make Reservation" buttons
4. **Photo previews** - Show venue photos inline
5. **Quick actions menu** - Dropdown with multiple actions per venue

## Files Modified

- `frontend/src/components/Message.tsx` - Added venue link detection and rendering
- `frontend/src/index.css` - Added venue link button styles
- `frontend/src/components/MessageVenueLinks.test.tsx` - Added comprehensive tests

## Rollback

To remove this feature:
1. Remove the `venueLinks` useMemo hook from Message.tsx
2. Remove the venue links rendering section
3. Remove `.venue-link-button` styles from index.css
4. Delete MessageVenueLinks.test.tsx

## Screenshots

### Before
```
Agent: I found Osteria Ama Philly at 1905 Chestnut St.
       Website: https://www.osteriaamaphilly.com
       Place ID: ChIJaSuyUYrHxokR-4BpMKOWt1M
```
User has to copy/paste the URL.

### After
```
Agent: I found Osteria Ama Philly at 1905 Chestnut St.
       Website: https://www.osteriaamaphilly.com
       Place ID: ChIJaSuyUYrHxokR-4BpMKOWt1M

[🌐 Visit Osteria Ama Philly →]  ← Clickable button
```
User can click the button to visit the website.
