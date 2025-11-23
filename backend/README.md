# Vibehuntr Backend - Development Setup

FastAPI backend for the Vibehuntr event planning agent with streaming support.

## Prerequisites

- Python 3.10-3.12 (3.13 not supported)
- `uv` package manager (required)
- Google Cloud credentials configured
- Access to Gemini API

## Installation

### 1. Install uv (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip
pip install uv
```

### 2. Install Dependencies

From the project root:

```bash
# Install all project dependencies
make install

# Or manually with uv
uv sync
```

## Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Gemini API Configuration
GEMINI_MODEL=gemini-2.0-flash-exp
GOOGLE_API_KEY=your-api-key-here  # Optional if using ADC

# Google Places API (for event planning features)
GOOGLE_PLACES_API_KEY=your-places-api-key

# Backend Configuration
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Session Configuration
SESSION_TIMEOUT_MINUTES=60

# Logging
LOG_LEVEL=INFO
```

### Required Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | Yes | - |
| `GOOGLE_CLOUD_LOCATION` | GCP region | Yes | us-central1 |
| `GEMINI_MODEL` | Gemini model to use | No | gemini-2.0-flash-exp |
| `GOOGLE_API_KEY` | Gemini API key | No* | - |
| `GOOGLE_PLACES_API_KEY` | Google Places API key | Yes | - |
| `BACKEND_PORT` | Port for backend server | No | 8000 |
| `CORS_ORIGINS` | Allowed CORS origins | No | http://localhost:5173 |

*Not required if using Application Default Credentials (ADC)

## Running the Backend

### Development Mode (with auto-reload)

From the project root:

```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

Or use the shorthand:

```bash
# From project root
uv run uvicorn backend.app.main:app --reload --port 8000
```

The backend will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Production Mode

```bash
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Health Check
```
GET /health
```

### Chat Endpoints
```
POST /api/chat
GET /api/chat/stream
```

### Session Endpoints
```
POST /api/sessions
GET /api/sessions/{session_id}/messages
DELETE /api/sessions/{session_id}
```

See full API documentation at http://localhost:8000/docs when running.

## Testing

### Run All Tests

```bash
# From project root
uv run pytest backend/tests/

# With coverage
uv run pytest backend/tests/ --cov=backend/app --cov-report=html
```

### Run Specific Test Suites

```bash
# Unit tests only
uv run pytest backend/tests/test_session_manager.py

# Integration tests
uv run pytest backend/tests/test_integration.py

# Error handling tests
uv run pytest backend/tests/test_error_handling.py
```

### Run Tests with Verbose Output

```bash
uv run pytest backend/tests/ -v
```

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── chat.py           # Chat endpoints
│   │   └── sessions.py       # Session management endpoints
│   ├── services/
│   │   ├── agent_service.py  # Agent invocation wrapper
│   │   └── session_manager.py # Session state management
│   ├── models/
│   │   └── schemas.py        # Pydantic models
│   ├── core/
│   │   └── config.py         # Configuration
│   └── main.py               # FastAPI application
├── tests/
│   ├── conftest.py           # Test fixtures
│   ├── test_*.py             # Test files
│   └── ...
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:

```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9

# Or use a different port
uv run uvicorn app.main:app --reload --port 8001
```

### Import Errors

Make sure you're running from the correct directory:

```bash
# From backend/ directory
uv run uvicorn app.main:app --reload

# From project root
uv run uvicorn backend.app.main:app --reload
```

### Google Cloud Authentication

If you see authentication errors:

```bash
# Login with gcloud
gcloud auth application-default login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Verify credentials
gcloud auth application-default print-access-token
```

### Missing Dependencies

```bash
# Reinstall all dependencies
uv sync --reinstall

# Or from project root
make install
```

## Development Tips

### Auto-reload on File Changes

The `--reload` flag automatically restarts the server when code changes:

```bash
uv run uvicorn app.main:app --reload
```

### Debug Mode

Enable debug logging:

```bash
LOG_LEVEL=DEBUG uv run uvicorn app.main:app --reload
```

### CORS Configuration

For local development with different frontend ports:

```bash
CORS_ORIGINS="http://localhost:5173,http://localhost:3000" uv run uvicorn app.main:app --reload
```

## Next Steps

1. Start the backend server
2. Verify health check: http://localhost:8000/health
3. Check API docs: http://localhost:8000/docs
4. Set up and run the frontend (see `frontend/README.md`)
5. Test the full stack integration

## Production Deployment

For production deployment to Google Cloud Platform:

- **[Production Deployment Guide](../PRODUCTION_DEPLOYMENT.md)** - Complete deployment instructions
- **[Production Quick Start](../PRODUCTION_QUICKSTART.md)** - 5-minute deployment guide
- **[Environment Variables Reference](../ENVIRONMENT_VARIABLES.md)** - All configuration options
- **[Deployment Checklist](../PRODUCTION_CHECKLIST.md)** - Pre-deployment checklist

Quick deploy:
```bash
export GCP_PROJECT_ID="your-project-id"
./scripts/deploy-production.sh
```

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google ADK Documentation](https://cloud.google.com/agent-development-kit/docs)
- [Project Main README](../README.md)
