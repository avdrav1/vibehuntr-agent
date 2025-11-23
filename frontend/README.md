# Vibehuntr Frontend - Development Setup

React + TypeScript frontend for the Vibehuntr event planning agent with real-time streaming.

## Prerequisites

- Node.js 18+ (LTS recommended)
- npm or yarn
- Backend server running (see `backend/README.md`)

## Installation

### 1. Install Node.js (if not already installed)

```bash
# macOS with Homebrew
brew install node

# Or download from https://nodejs.org/
```

### 2. Install Dependencies

From the frontend directory:

```bash
cd frontend
npm install
```

## Environment Variables

Create a `.env` file in the `frontend/` directory:

```bash
# Backend API URL
VITE_API_URL=http://localhost:8000

# Optional: Enable debug mode
VITE_DEBUG=false
```

### Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `VITE_API_URL` | Backend API base URL | No | http://localhost:8000 |
| `VITE_DEBUG` | Enable debug logging | No | false |

**Note:** Vite requires environment variables to be prefixed with `VITE_` to be exposed to the client.

## Running the Frontend

### Development Mode (with hot reload)

```bash
cd frontend
npm run dev
```

The frontend will be available at:
- App: http://localhost:5173
- Vite will automatically open your browser

### Build for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

Serves the production build locally for testing.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Chat.tsx          # Main chat container
│   │   ├── Header.tsx        # App header with branding
│   │   ├── MessageList.tsx   # Message display container
│   │   ├── Message.tsx       # Individual message component
│   │   ├── ChatInput.tsx     # Message input field
│   │   ├── Welcome.tsx       # Welcome screen
│   │   ├── ErrorMessage.tsx  # Error display component
│   │   └── index.ts          # Component exports
│   ├── hooks/
│   │   ├── useChat.ts        # Chat state management
│   │   └── index.ts          # Hook exports
│   ├── services/
│   │   └── api.ts            # API client
│   ├── types/
│   │   └── index.ts          # TypeScript types
│   ├── test/
│   │   ├── setup.ts          # Test configuration
│   │   └── *.test.tsx        # Test files
│   ├── App.tsx               # Root component
│   ├── main.tsx              # Entry point
│   └── index.css             # Global styles (Tailwind)
├── public/                   # Static assets
├── dist/                     # Production build output
├── package.json              # Dependencies
├── vite.config.ts            # Vite configuration
├── tailwind.config.js        # Tailwind CSS config
├── tsconfig.json             # TypeScript config
└── README.md                 # This file
```

## Testing

### Run All Tests

```bash
npm run test
```

### Run Tests in Watch Mode

```bash
npm run test:watch
```

### Run Tests with Coverage

```bash
npm run test:coverage
```

### Run Specific Test File

```bash
npm run test -- src/components/Message.test.tsx
```

## Development Workflow

### 1. Start Backend

```bash
# In terminal 1 (from project root)
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

### 2. Start Frontend

```bash
# In terminal 2 (from project root)
cd frontend
npm run dev
```

### 3. Open Browser

Navigate to http://localhost:5173

## Styling

The app uses Tailwind CSS with custom Vibehuntr branding:

### Color Palette

```css
/* Primary Colors */
--vibehuntr-purple: #8B5CF6
--vibehuntr-pink: #EC4899
--vibehuntr-dark: #1F2937

/* Gradients */
background: linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%)
```

### Customizing Styles

Edit `tailwind.config.js` to modify the theme:

```javascript
export default {
  theme: {
    extend: {
      colors: {
        vibehuntr: {
          purple: '#8B5CF6',
          pink: '#EC4899',
          // Add more colors
        }
      }
    }
  }
}
```

## Troubleshooting

### Port Already in Use

If port 5173 is already in use:

```bash
# Kill the process
lsof -ti:5173 | xargs kill -9

# Or specify a different port
npm run dev -- --port 3000
```

### Backend Connection Issues

Verify the backend is running:

```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy"}`

If not, check:
1. Backend server is running
2. `.env` file has correct `VITE_API_URL`
3. CORS is configured correctly in backend

### Module Not Found Errors

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### TypeScript Errors

```bash
# Check TypeScript compilation
npm run type-check

# Or use the TypeScript compiler directly
npx tsc --noEmit
```

### Build Errors

```bash
# Clear Vite cache
rm -rf node_modules/.vite

# Rebuild
npm run build
```

### Hot Reload Not Working

1. Check file watcher limits (Linux):
```bash
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

2. Restart the dev server:
```bash
npm run dev
```

## Development Tips

### Enable Debug Mode

Set `VITE_DEBUG=true` in `.env` to see detailed logs in the browser console.

### API Proxy Configuration

Vite is configured to proxy API requests. See `vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

### Component Development

Use React DevTools browser extension for debugging:
- [Chrome](https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi)
- [Firefox](https://addons.mozilla.org/en-US/firefox/addon/react-devtools/)

### Code Formatting

```bash
# Format code with Prettier (if configured)
npm run format

# Lint code
npm run lint
```

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions

## Performance Tips

1. **Lazy Loading**: Components are loaded on demand
2. **Code Splitting**: Vite automatically splits code
3. **Tree Shaking**: Unused code is removed in production
4. **Asset Optimization**: Images and assets are optimized

## Next Steps

1. Start the backend server (see `backend/README.md`)
2. Start the frontend dev server
3. Open http://localhost:5173
4. Start chatting with the Vibehuntr agent!

## Production Deployment

For production deployment to Google Cloud Platform:

- **[Production Deployment Guide](../PRODUCTION_DEPLOYMENT.md)** - Complete deployment instructions
- **[Production Quick Start](../PRODUCTION_QUICKSTART.md)** - 5-minute deployment guide
- **[Environment Variables Reference](../ENVIRONMENT_VARIABLES.md)** - All configuration options
- **[Deployment Checklist](../PRODUCTION_CHECKLIST.md)** - Pre-deployment checklist

The frontend is deployed to Cloud Storage with Cloud CDN for global distribution.

## Additional Resources

- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [TypeScript Documentation](https://www.typescriptlang.org/)
- [Project Main README](../README.md)
