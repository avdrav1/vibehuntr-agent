# Vibehuntr Quick Start Guide

## Current Status

✅ **Backend**: Running at http://localhost:8000  
✅ **Frontend**: Running at http://localhost:5173  
⚠️ **Agent**: Needs Google Cloud credentials

## Fix the "Connection Lost" Error

The agent needs Google Cloud credentials to work. Choose one option:

### Option 1: Use Gemini API Key (Easiest)

1. **Get an API key**: Visit https://makersuite.google.com/app/apikey
2. **Add to `.env` file**:
   ```bash
   GOOGLE_API_KEY=your-actual-api-key-here
   ```
3. **Restart the backend**:
   ```bash
   # Stop the current backend (Ctrl+C or kill the process)
   # Then restart:
   uv run uvicorn backend.app.main:app --reload --port 8000
   ```

### Option 2: Use Google Cloud (Full Features)

1. **Authenticate with gcloud**:
   ```bash
   gcloud auth application-default login
   ```
   Follow the browser prompts to complete authentication.

2. **Set your project in `.env`**:
   ```bash
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_CLOUD_LOCATION=us-central1
   ```

3. **Restart the backend**:
   ```bash
   uv run uvicorn backend.app.main:app --reload --port 8000
   ```

## Running the Application

### Start Backend (Terminal 1)
```bash
cd /path/to/vibehuntr-agent
uv run uvicorn backend.app.main:app --reload --port 8000
```

### Start Frontend (Terminal 2)
```bash
cd /path/to/vibehuntr-agent/frontend
npm run dev
```

### Access the App
Open your browser to: **http://localhost:5173**

## Troubleshooting

### "Connection Lost" Error
- **Cause**: Missing Google Cloud credentials
- **Fix**: Follow Option 1 or Option 2 above

### "Module not found" Error
- **Cause**: Backend running from wrong directory
- **Fix**: Run backend from project root: `uv run uvicorn backend.app.main:app --reload --port 8000`

### Port Already in Use
- **Cause**: Previous process still running
- **Fix**: Kill the process:
  ```bash
  pkill -f "uvicorn"
  pkill -f "vite"
  ```

## Environment Variables

Your `.env` file should have at minimum:

```bash
# Required for agent to work
GOOGLE_API_KEY=your-api-key-here
# OR
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Optional but recommended
GEMINI_MODEL=gemini-2.0-flash-exp
GOOGLE_PLACES_API_KEY=your-places-api-key
LOG_LEVEL=INFO
```

## Next Steps

1. ✅ Set up Google Cloud credentials (see above)
2. ✅ Restart the backend
3. ✅ Refresh your browser at http://localhost:5173
4. ✅ Send a test message like "Hello" or "Find Indian restaurants"
5. ✅ Enjoy your working Vibehuntr agent!

## Need Help?

- **Backend logs**: Check the terminal where uvicorn is running
- **Frontend logs**: Open browser DevTools (F12) → Console tab
- **Documentation**: See `DEVELOPMENT_SETUP.md` for detailed setup

---

**Remember**: The Streamlit version has been archived. Use the React + FastAPI version for the best experience!
