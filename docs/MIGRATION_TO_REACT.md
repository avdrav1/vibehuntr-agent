# Migration from Streamlit to React + FastAPI

## Overview

Vibehuntr has migrated from a Streamlit-based playground to a modern React + FastAPI architecture. This document explains the migration and helps you transition.

## Why We Migrated

The Streamlit implementation had several fundamental issues:

1. **Duplicate Messages**: Streamlit's rerun model caused messages to appear multiple times
2. **Poor State Management**: Difficult to control when and how components re-render
3. **Streaming Challenges**: Streamlit's architecture made real-time streaming problematic
4. **Production Limitations**: Streamlit is designed for prototyping, not production deployments
5. **Limited Control**: Difficult to customize UI behavior and styling

## What Changed

### Before (Streamlit)

```
vibehuntr-agent/
├── vibehuntr_playground.py    # Main Streamlit app
├── start_playground.sh         # Launch script
├── app/
│   ├── playground_style.py    # Custom CSS
│   └── vibehuntr_app.py       # App wrapper
```

**Running:**
```bash
streamlit run vibehuntr_playground.py
```

### After (React + FastAPI)

```
vibehuntr-agent/
├── frontend/                   # React application
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── hooks/             # Custom hooks
│   │   └── services/          # API client
│   └── package.json
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── api/               # REST endpoints
│   │   ├── services/          # Business logic
│   │   └── main.py            # FastAPI app
│   └── requirements.txt
└── archive/streamlit/         # Archived Streamlit files
```

**Running:**
```bash
# Terminal 1: Backend
cd backend && uv run uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

## Benefits of React + FastAPI

### ✅ No Duplicate Messages
React's explicit state management prevents UI duplication issues.

### ✅ Real-Time Streaming
Server-Sent Events (SSE) provide smooth token-by-token streaming.

### ✅ Production Ready
Standard web architecture suitable for Cloud Run + Cloud Storage deployment.

### ✅ Better UX
- Responsive design
- Fine-grained control over rendering
- Smooth animations and transitions
- Mobile-friendly interface

### ✅ Maintainable
Clear separation between:
- Frontend (React)
- Backend (FastAPI)
- Agent Logic (ADK)

## Migration Guide

### For Developers

If you were working with the Streamlit version:

1. **Setup New Environment**
   ```bash
   # Install frontend dependencies
   cd frontend && npm install
   
   # Backend uses existing Python environment
   cd backend && uv sync
   ```

2. **Update Your Workflow**
   - Old: `make playground` or `streamlit run vibehuntr_playground.py`
   - New: Start backend and frontend separately (see DEVELOPMENT_SETUP.md)

3. **Learn the New Architecture**
   - Read [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md) for setup
   - Review [backend/README.md](backend/README.md) for API documentation
   - Check [frontend/README.md](frontend/README.md) for component structure

4. **Agent Code Unchanged**
   - The core agent logic in `app/` remains the same
   - Agent tools and services are reused
   - Only the UI layer changed

### For Users

If you were using the Streamlit playground:

1. **Access the New Interface**
   - Old: http://localhost:8501
   - New: http://localhost:5173

2. **Same Features, Better Experience**
   - All agent capabilities remain
   - Improved streaming responses
   - Better error handling
   - Faster, more responsive UI

## Accessing Archived Streamlit Version

The Streamlit version is archived in `archive/streamlit/` for reference.

### Running the Archived Version (Not Recommended)

```bash
# From project root
uv run streamlit run archive/streamlit/vibehuntr_playground.py
```

**⚠️ Warning:** The archived version is no longer maintained and may have issues.

## Getting Help

### Documentation

- **[DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md)** - Complete setup guide
- **[backend/README.md](backend/README.md)** - Backend API documentation
- **[frontend/README.md](frontend/README.md)** - Frontend development guide
- **[PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)** - Deployment guide

### Architecture

- **[Design Document](.kiro/specs/react-migration/design.md)** - Architecture overview
- **[Requirements](.kiro/specs/react-migration/requirements.md)** - Feature requirements
- **[Tasks](.kiro/specs/react-migration/tasks.md)** - Implementation details

## Timeline

- **Before November 2025**: Streamlit-based playground
- **November 2025**: Migration to React + FastAPI
- **Current**: React + FastAPI is the recommended implementation

## Questions?

If you have questions about the migration:

1. Check the documentation links above
2. Review the design documents in `.kiro/specs/react-migration/`
3. Compare the archived Streamlit code with the new React implementation
4. Refer to the commit history for migration details

---

**Remember:** The React + FastAPI version provides a better experience with no duplicate messages, real-time streaming, and production-ready architecture. We recommend using it for all new development.
