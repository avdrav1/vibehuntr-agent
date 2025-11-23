# React + FastAPI Migration Spec

## Overview

This spec outlines the migration from Streamlit to React + FastAPI for the Vibehuntr playground. The migration solves the fundamental issues with Streamlit's rerun model that cause duplicate messages and poor chat UX.

## Why Migrate?

**Problems with Streamlit:**
- Rerun model causes duplicate messages
- No fine-grained control over rendering
- Difficult to implement proper streaming
- Not suitable for production chat applications

**Benefits of React + FastAPI:**
- Explicit state management (no duplicates)
- Proper SSE streaming support
- Production-ready architecture
- Full control over UI rendering
- Standard web stack

## Architecture

```
React Frontend (Port 5173)
    ↓ HTTP/SSE
FastAPI Backend (Port 8000)
    ↓
Existing Agent Code (Reused)
    ↓
Google ADK
```

## Key Features

1. **No Duplicate Messages**: React's explicit state prevents duplicates
2. **Real-Time Streaming**: SSE provides token-by-token streaming
3. **Session Management**: Backend maintains conversation history
4. **Vibehuntr Branding**: Tailwind CSS with custom theme
5. **Error Handling**: Comprehensive error handling throughout
6. **Backward Compatible**: Reuses existing agent code

## Documents

- **requirements.md**: Detailed requirements with acceptance criteria
- **design.md**: Architecture, components, and implementation details
- **tasks.md**: Step-by-step implementation plan (35 tasks)

## Quick Start (After Implementation)

### Development

```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

Visit: http://localhost:5173

### Production

- Backend: Deploy to Cloud Run
- Frontend: Build and deploy to Cloud Storage + CDN

## Implementation Phases

1. **Backend Setup** (Tasks 1-8): FastAPI app, endpoints, session management
2. **Frontend Setup** (Tasks 9-12): React + Vite, Tailwind, TypeScript
3. **React Components** (Tasks 13-17): UI components
4. **State & Streaming** (Tasks 18-21): Chat logic, SSE streaming
5. **Polish** (Tasks 22-26): Error handling, loading states
6. **Testing** (Tasks 27-29): Unit, component, integration tests
7. **Documentation** (Tasks 30-32): Setup guides, deployment docs
8. **Migration** (Tasks 33-35): Verification, cleanup

## Estimated Effort

- **Backend**: 4-6 hours
- **Frontend**: 6-8 hours
- **Testing**: 2-3 hours
- **Documentation**: 1-2 hours
- **Total**: 13-19 hours

## Next Steps

1. Review the spec documents
2. Approve the approach
3. Begin implementation with Phase 1 (Backend Setup)
4. Test incrementally as you build
5. Deploy when complete

## Success Criteria

- ✅ No duplicate messages
- ✅ Smooth real-time streaming
- ✅ Context maintained across conversation
- ✅ Vibehuntr branding applied
- ✅ Error handling works correctly
- ✅ Production-ready deployment

## Questions?

Review the detailed documents:
- `requirements.md` for what we're building
- `design.md` for how we're building it
- `tasks.md` for step-by-step implementation

Ready to start? Begin with Task 1: Create FastAPI application structure.
