# Screenshots Directory

This directory contains screenshots of the Vibehuntr application for documentation purposes.

## Required Screenshots

### 1. Chat Interface (`chat-interface.png`)
- Main chat interface showing a conversation
- Should include:
  - Header with Vibehuntr branding
  - Multiple messages (user and assistant)
  - Streaming indicator (if possible)
  - Input field at bottom

### 2. Welcome Screen (`welcome-screen.png`)
- Initial welcome screen when no messages exist
- Should show:
  - Vibehuntr logo and branding
  - Feature overview
  - Suggested prompts or capabilities

### 3. Mobile View (`mobile-view.png`)
- Mobile-responsive view of the chat interface
- Capture on a mobile device or using browser DevTools mobile emulation
- Should demonstrate responsive design

## Optional Screenshots

### 4. Error Handling (`error-handling.png`)
- Example of error message display
- Shows graceful error recovery

### 5. Streaming in Progress (`streaming.png`)
- Capture of streaming response in progress
- Shows the streaming indicator/cursor

### 6. Session Management (`session-management.png`)
- New conversation button
- Session clearing functionality

## How to Capture Screenshots

### Using Browser DevTools

1. Start the application:
   ```bash
   # Terminal 1 - Backend
   cd backend
   uv run uvicorn app.main:app --reload
   
   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

2. Open http://localhost:5173 in your browser

3. Open DevTools (F12)

4. For desktop screenshots:
   - Use full browser window
   - Ensure good lighting/contrast
   - Capture at 1920x1080 or similar

5. For mobile screenshots:
   - Open DevTools
   - Click device toolbar icon (Ctrl+Shift+M)
   - Select a mobile device (e.g., iPhone 12 Pro)
   - Capture screenshot

### Screenshot Tools

- **macOS**: Cmd+Shift+4 (select area) or Cmd+Shift+3 (full screen)
- **Windows**: Windows+Shift+S (Snipping Tool)
- **Linux**: Gnome Screenshot, Flameshot, or similar
- **Browser**: DevTools → More tools → Capture screenshot

### Image Guidelines

- **Format**: PNG (preferred) or JPG
- **Resolution**: At least 1920x1080 for desktop, actual device resolution for mobile
- **File size**: Optimize images (use tools like TinyPNG or ImageOptim)
- **Naming**: Use kebab-case (e.g., `chat-interface.png`)

## Updating README

After adding screenshots, update the main README.md to reference them:

```markdown
![Chat Interface](docs/screenshots/chat-interface.png)
*Main chat interface with streaming responses*
```

## Privacy Note

Ensure screenshots do not contain:
- Real API keys or credentials
- Personal information
- Sensitive data
- Real user information

Use test data and example conversations for all screenshots.
