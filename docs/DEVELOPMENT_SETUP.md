# Vibehuntr Development Setup Guide

Complete guide for setting up and running the Vibehuntr React + FastAPI application.

> **📌 Note:** This guide covers the modern React + FastAPI implementation. The legacy Streamlit version has been archived to `archive/streamlit/` and is no longer maintained.

## Quick Start

### Prerequisites Checklist

- [ ] Python 3.10-3.12 installed
- [ ] `uv` package manager installed
- [ ] Node.js 18+ installed
- [ ] Google Cloud credentials configured
- [ ] Google API keys obtained

### 5-Minute Setup

```bash
# 1. Clone and navigate to project
cd vibehuntr-agent

# 2. Install Python dependencies
make install

# 3. Install frontend dependencies
cd frontend && npm install && cd ..

# 4. Create .env file (see Environment Variables section below)
cp .env.example .env  # Edit with your values

# 5. Start backend (terminal 1)
cd backend
uv run uvicorn app.main:app --reload --port 8000

# 6. Start frontend (terminal 2)
cd frontend
npm run dev

# 7. Open browser
# Navigate to http://localhost:5173
```

## Detailed Setup Instructions

### 1. Install Prerequisites

#### Install uv (Python Package Manager)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

#### Install Node.js

```bash
# macOS with Homebrew
brew install node

# Verify installation
node --version  # Should be 18+
npm --version
```

#### Configure Google Cloud

```bash
# Install gcloud CLI (if not installed)
# https://cloud.google.com/sdk/docs/install

# Login and set project
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### 2. Environment Variables

Create a `.env` file in the project root:

```bash
# ============================================
# Google Cloud Configuration
# ============================================
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# ============================================
# Gemini API Configuration
# ============================================
GEMINI_MODEL=gemini-2.0-flash-exp
GOOGLE_API_KEY=your-gemini-api-key

# ============================================
# Google Places API
# ============================================
GOOGLE_PLACES_API_KEY=your-places-api-key

# ============================================
# Backend Configuration
# ============================================
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# ============================================
# Session Configuration
# ============================================
SESSION_TIMEOUT_MINUTES=60

# ============================================
# Logging
# ============================================
LOG_LEVEL=INFO
```

#### Required API Keys

1. **Gemini API Key**
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Add to `.env` as `GOOGLE_API_KEY`

2. **Google Places API Key**
   - Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Create credentials → API key
   - Enable Places API
   - Add to `.env` as `GOOGLE_PLACES_API_KEY`

### 3. Install Dependencies

#### Backend Dependencies

```bash
# From project root
make install

# Or manually
uv sync
```

#### Frontend Dependencies

```bash
cd frontend
npm install
```

### 4. Verify Installation

```bash
# Check Python environment
uv run python --version

# Check backend can import modules
uv run python -c "from backend.app.main import app; print('Backend OK')"

# Check frontend build
cd frontend
npm run build
```

## Running the Application

### Development Mode

#### Option 1: Two Terminals

**Terminal 1 - Backend:**
```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

#### Option 2: Using Make (if configured)

```bash
# Terminal 1
make backend-dev

# Terminal 2
make frontend-dev
```

### Verify Everything is Running

1. **Backend Health Check:**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"healthy"}
   ```

2. **Backend API Docs:**
   - Open http://localhost:8000/docs
   - You should see the FastAPI Swagger UI

3. **Frontend:**
   - Open http://localhost:5173
   - You should see the Vibehuntr chat interface

## Testing

### Backend Tests

```bash
# Run all backend tests
uv run pytest backend/tests/

# Run with coverage
uv run pytest backend/tests/ --cov=backend/app --cov-report=html

# Run specific test file
uv run pytest backend/tests/test_session_manager.py -v
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm run test

# Run with coverage
npm run test:coverage

# Run specific test
npm run test -- src/components/Message.test.tsx
```

### Integration Tests

```bash
# Backend integration tests
uv run pytest backend/tests/test_integration.py

# Frontend integration tests
cd frontend
npm run test -- src/test/integration.test.tsx
```

## Common Issues and Solutions

### Issue: Port Already in Use

**Backend (8000):**
```bash
lsof -ti:8000 | xargs kill -9
```

**Frontend (5173):**
```bash
lsof -ti:5173 | xargs kill -9
```

### Issue: Import Errors

```bash
# Reinstall dependencies
uv sync --reinstall
cd frontend && npm install
```

### Issue: CORS Errors

Check that:
1. Backend is running on port 8000
2. Frontend `.env` has correct `VITE_API_URL`
3. Backend CORS_ORIGINS includes `http://localhost:5173`

### Issue: Authentication Errors

```bash
# Re-authenticate with Google Cloud
gcloud auth application-default login

# Verify credentials
gcloud auth application-default print-access-token
```

### Issue: Module Not Found

```bash
# Backend
uv sync

# Frontend
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Project Structure Overview

```
vibehuntr-agent/
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── api/             # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── models/          # Data models
│   │   └── main.py          # FastAPI app
│   ├── tests/               # Backend tests
│   └── README.md            # Backend docs
│
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks
│   │   ├── services/        # API client
│   │   └── types/           # TypeScript types
│   ├── tests/               # Frontend tests
│   └── README.md            # Frontend docs
│
├── app/                     # Original agent code
│   └── event_planning/      # Event planning domain
│
├── .env                     # Environment variables
├── pyproject.toml           # Python dependencies
├── package.json             # Root package.json
└── Makefile                 # Build automation
```

## Development Workflow

### Making Changes

1. **Backend Changes:**
   - Edit files in `backend/app/`
   - Server auto-reloads with `--reload` flag
   - Test changes: `uv run pytest backend/tests/`

2. **Frontend Changes:**
   - Edit files in `frontend/src/`
   - Vite hot-reloads automatically
   - Test changes: `npm run test`

### Adding New Features

1. Update requirements in `.kiro/specs/react-migration/requirements.md`
2. Update design in `.kiro/specs/react-migration/design.md`
3. Add tasks to `.kiro/specs/react-migration/tasks.md`
4. Implement backend changes
5. Implement frontend changes
6. Write tests
7. Update documentation

### Code Quality

```bash
# Backend linting
uv run ruff check backend/
uv run ruff format backend/

# Backend type checking
uv run mypy backend/

# Frontend linting
cd frontend
npm run lint
```

## Deployment

### Backend Deployment (Cloud Run)

```bash
# Build and deploy
gcloud run deploy vibehuntr-backend \
  --source backend/ \
  --region us-central1 \
  --allow-unauthenticated
```

### Frontend Deployment (Cloud Storage + CDN)

```bash
cd frontend
npm run build

# Upload to Cloud Storage
gsutil -m rsync -r dist/ gs://your-bucket-name/

# Configure CDN
# See deployment/README.md for details
```

## Additional Resources

### Documentation

- [Backend README](backend/README.md) - Backend-specific setup
- [Frontend README](frontend/README.md) - Frontend-specific setup
- [Main README](README.md) - Project overview
- [Design Document](.kiro/specs/react-migration/design.md) - Architecture details

### External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [Google ADK Documentation](https://cloud.google.com/agent-development-kit/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/)

## Getting Help

### Check Logs

**Backend:**
```bash
# View server logs in terminal where backend is running
# Or check Cloud Logging in production
```

**Frontend:**
```bash
# Open browser DevTools (F12)
# Check Console tab for errors
```

### Debug Mode

**Backend:**
```bash
LOG_LEVEL=DEBUG uv run uvicorn app.main:app --reload
```

**Frontend:**
```bash
# Set in frontend/.env
VITE_DEBUG=true
```

### Common Commands Reference

```bash
# Backend
cd backend
uv run uvicorn app.main:app --reload --port 8000  # Start dev server
uv run pytest tests/                               # Run tests
uv run pytest tests/ --cov=app                     # Run with coverage

# Frontend
cd frontend
npm run dev                                        # Start dev server
npm run build                                      # Build for production
npm run preview                                    # Preview production build
npm run test                                       # Run tests
npm run lint                                       # Lint code

# Both
make install                                       # Install all dependencies
make test                                          # Run all tests
```

## Next Steps

1. ✅ Complete setup following this guide
2. ✅ Verify both backend and frontend are running
3. ✅ Test the chat interface
4. 📖 Read the [Design Document](.kiro/specs/react-migration/design.md)
5. 🚀 Start building features!

---

**Need help?** Check the troubleshooting sections in:
- [Backend README](backend/README.md#troubleshooting)
- [Frontend README](frontend/README.md#troubleshooting)
