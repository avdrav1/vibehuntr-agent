# Vibehuntr Startup Scripts

This document explains the startup scripts for the Vibehuntr application.

## Available Scripts

### `start_app.sh` - Start the Application

Starts both the backend (FastAPI) and frontend (React) services.

**Usage:**
```bash
./start_app.sh
```

**What it does:**
1. ✅ Checks prerequisites (uv, Node.js, npm)
2. ✅ Verifies `.env` file exists and has credentials
3. ✅ Kills any existing processes on ports 8000 and 5173
4. ✅ Installs dependencies if needed
5. ✅ Starts backend server (port 8000)
6. ✅ Starts frontend server (port 5173)
7. ✅ Opens browser automatically
8. ✅ Creates log files in `logs/` directory

**Logs:**
- Backend: `logs/backend.log`
- Frontend: `logs/frontend.log`

**Process IDs:**
- Backend PID: `logs/backend.pid`
- Frontend PID: `logs/frontend.pid`

---

### `stop_app.sh` - Stop the Application

Stops both backend and frontend services gracefully.

**Usage:**
```bash
./stop_app.sh
```

**What it does:**
1. ✅ Stops backend process
2. ✅ Stops frontend process
3. ✅ Cleans up PID files
4. ✅ Kills any remaining processes on ports 8000 and 5173

---

### `restart_app.sh` - Restart the Application

Stops and then starts the application.

**Usage:**
```bash
./restart_app.sh
```

**What it does:**
1. ✅ Runs `stop_app.sh`
2. ✅ Waits 2 seconds
3. ✅ Runs `start_app.sh`

---

## Prerequisites

Before running the scripts, ensure you have:

1. **uv** - Python package manager
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Node.js 18+** - JavaScript runtime
   ```bash
   # Check version
   node --version
   ```

3. **npm** - Node package manager (comes with Node.js)
   ```bash
   # Check version
   npm --version
   ```

4. **Google Cloud Credentials** - Required for the agent to work
   - Option 1: Get a Gemini API key from https://makersuite.google.com/app/apikey
   - Option 2: Set up Google Cloud project credentials

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Copy from example
cp .env.example .env

# Edit and add your credentials
nano .env  # or use your preferred editor
```

**Minimum required:**
```bash
# Option 1: Use Gemini API (easiest)
GOOGLE_API_KEY=your-api-key-here

# OR Option 2: Use Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
```

**Optional but recommended:**
```bash
GEMINI_MODEL=gemini-2.0-flash-exp
GOOGLE_PLACES_API_KEY=your-places-api-key
LOG_LEVEL=INFO
```

---

## Troubleshooting

### Script won't run

**Problem:** Permission denied

**Solution:**
```bash
chmod +x start_app.sh stop_app.sh restart_app.sh
```

---

### Port already in use

**Problem:** Error: "Port 8000 is already in use"

**Solution:** The script automatically kills existing processes, but if it fails:
```bash
# Manual cleanup
pkill -f "uvicorn"
pkill -f "vite"

# Or use the stop script
./stop_app.sh
```

---

### Dependencies not installed

**Problem:** "Module not found" or "Command not found"

**Solution:**
```bash
# Install Python dependencies
uv sync

# Install frontend dependencies
cd frontend && npm install && cd ..
```

---

### Agent not responding

**Problem:** "Connection lost" error in browser

**Solution:** Check your `.env` file has valid Google Cloud credentials:
```bash
# Verify .env has one of these:
grep GOOGLE_API_KEY .env
# OR
grep GOOGLE_CLOUD_PROJECT .env
```

If missing, add your credentials and restart:
```bash
./restart_app.sh
```

---

### Logs show errors

**Problem:** Application starts but doesn't work correctly

**Solution:** Check the log files:
```bash
# View backend logs
tail -f logs/backend.log

# View frontend logs
tail -f logs/frontend.log
```

Common issues:
- Missing environment variables
- Invalid API keys
- Network connectivity problems
- Port conflicts

---

## Manual Control

If you prefer manual control over the services:

### Start Backend Only
```bash
uv run uvicorn backend.app.main:app --reload --port 8000
```

### Start Frontend Only
```bash
cd frontend && npm run dev
```

### View Logs in Real-Time
```bash
# Backend
tail -f logs/backend.log

# Frontend
tail -f logs/frontend.log
```

### Check Running Processes
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check if frontend is running
curl http://localhost:5173
```

---

## Development Workflow

### Typical workflow:

1. **Start the app:**
   ```bash
   ./start_app.sh
   ```

2. **Make code changes** - The servers will auto-reload:
   - Backend: Uvicorn watches for Python file changes
   - Frontend: Vite HMR (Hot Module Replacement) updates instantly

3. **View logs if needed:**
   ```bash
   tail -f logs/backend.log
   tail -f logs/frontend.log
   ```

4. **Restart if needed:**
   ```bash
   ./restart_app.sh
   ```

5. **Stop when done:**
   ```bash
   ./stop_app.sh
   ```

---

## Production Deployment

These scripts are for **development only**. For production deployment, see:
- [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)
- [PRODUCTION_QUICKSTART.md](PRODUCTION_QUICKSTART.md)

---

## Additional Resources

- **Quick Start Guide**: [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)
- **Development Setup**: [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md)
- **Backend Documentation**: [backend/README.md](backend/README.md)
- **Frontend Documentation**: [frontend/README.md](frontend/README.md)
- **Environment Variables**: [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md)

---

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the log files in `logs/`
3. Ensure all prerequisites are installed
4. Verify your `.env` configuration
5. Try restarting: `./restart_app.sh`

---

**Happy coding! 🚀**
