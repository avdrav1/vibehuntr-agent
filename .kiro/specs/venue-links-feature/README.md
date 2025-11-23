# Venue Website Links Feature

## Summary

Automatically detects venue information in chat messages and displays clickable website links as styled buttons.

## What Was Implemented

When the agent shows venue details with a website and Place ID, a clickable button automatically appears below the message:

```
[🌐 Visit Restaurant Name →]
```

## Changes Made

### 1. Enhanced Message Component (`frontend/src/components/Message.tsx`)

- Added `venueLinks` state using `useMemo` for efficient parsing
- Detects patterns: venue name (**Name**), website (🌐 Website: URL), Place ID (🆔 Place ID: ChIJa...)
- Renders styled link buttons below message content
- Only processes assistant messages

### 2. Added Styling (`frontend/src/index.css`)

- `.venue-link-button` - Gradient background with Vibehuntr theme
- Hover animations (slide right, border glow)
- Responsive layout with icon, text, and arrow

### 3. Added Tests (`frontend/src/components/MessageVenueLinks.test.tsx`)

- 7 comprehensive tests covering all scenarios
- All tests passing ✓

## How It Works

### Detection Pattern

The component looks for this structure in agent messages:

```
**Restaurant Name**
📍 Address (optional)
🌐 Website: https://example.com
🆔 Place ID: ChIJabc123... (optional)
```

When the two key elements are present (name and website), a link button is rendered. Place ID is optional and used for uniqueness if present.

### Visual Design

- **Icon**: 🌐 globe emoji
- **Text**: "Visit [Venue Name]"
- **Arrow**: → that slides on hover
- **Style**: Vibehuntr gradient (pink/red)
- **Behavior**: Opens in new tab with security attributes

## Benefits

### User Experience
- One-click access to restaurant websites
- No need to copy/paste URLs
- Visual clarity - buttons stand out
- Consistent with Vibehuntr theme

### Technical
- Automatic detection - no backend changes
- Efficient parsing with `useMemo`
- Secure links (`rel="noopener noreferrer"`)
- Flexible pattern matching

## Testing

### Run Tests
```bash
cd frontend
npm test -- MessageVenueLinks
```

### Manual Testing
1. Start the application
2. Ask: "Find Italian restaurants in Philadelphia"
3. Agent shows results with websites
4. Click the "Visit [Restaurant]" button
5. Restaurant website opens in new tab

## Example

**Before:**
```
Agent: I found Osteria Ama Philly.
       Website: https://www.osteriaamaphilly.com
       Place ID: ChIJaSuyUYrHxokR-4BpMKOWt1M
```
User must copy/paste the URL.

**After:**
```
Agent: I found Osteria Ama Philly.
       Website: https://www.osteriaamaphilly.com
       Place ID: ChIJaSuyUYrHxokR-4BpMKOWt1M

[🌐 Visit Osteria Ama Philly →]  ← Clickable!
```
User clicks the button.

## Files

- `frontend/src/components/Message.tsx` - Link detection and rendering
- `frontend/src/index.css` - Button styling
- `frontend/src/components/MessageVenueLinks.test.tsx` - Tests
- `frontend/VENUE_LINKS_FEATURE.md` - Detailed documentation

## Future Enhancements

Potential additions:
- Phone number click-to-call buttons
- "Get Directions" links to Google Maps
- "Make Reservation" integration
- Inline photo previews
- Quick actions dropdown menu

## Rollback

To remove this feature:
1. Remove `venueLinks` useMemo from Message.tsx
2. Remove venue links rendering section
3. Remove `.venue-link-button` styles from index.css
4. Delete MessageVenueLinks.test.tsx
