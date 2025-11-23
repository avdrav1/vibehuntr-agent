# Streamlit Version Archive

This directory contains the archived Streamlit-based playground interface for Vibehuntr. The Streamlit version has been replaced by a modern React + FastAPI architecture.

## Archived Files

- **vibehuntr_playground.py** - Main Streamlit playground interface
- **start_playground.sh** - Shell script to launch the Streamlit playground
- **playground_style.py** - Custom CSS and branding for Streamlit
- **vibehuntr_app.py** - Branded app wrapper for Streamlit

## Why Archived?

The Streamlit implementation suffered from fundamental incompatibilities between Streamlit's rerun model and chat UI requirements, resulting in:
- Duplicate messages in the chat interface
- Poor state management
- Difficulty with streaming responses
- Production deployment challenges

## Current Implementation

The application now uses:
- **Frontend**: React + TypeScript with Vite
- **Backend**: FastAPI with Server-Sent Events (SSE) for streaming
- **Benefits**: Proper state management, no duplicates, production-ready architecture

See the main README.md for setup instructions for the React version.

## Running the Archived Version (Not Recommended)

If you need to run the old Streamlit version for reference:

```bash
cd ../..  # Return to project root
uv run streamlit run archive/streamlit/vibehuntr_playground.py
```

**Note**: The Streamlit version is no longer maintained and may have issues.

## Migration Date

Archived: November 2025
Replaced by: React + FastAPI implementation (see `.kiro/specs/react-migration/`)
