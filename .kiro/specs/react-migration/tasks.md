# Implementation Plan: React + FastAPI Migration

## Phase 1: Backend Setup

- [x] 1. Create FastAPI application structure
  - Create `backend/` directory
  - Create `backend/app/main.py` with FastAPI app
  - Set up CORS middleware for localhost:5173
  - Add health check endpoint
  - _Requirements: 1.1, 5.1, 5.2, 5.3_
am3
- [x] 2. Create session management service
  - Create `backend/app/services/session_manager.py`
  - Implement in-memory session storage
  - Add create_session, add_message, get_messages, clear_session methods
  - _Requirements: 3.1, 3.2, 3.4_

- [x] 3. Create agent service wrapper
  - Create `backend/app/services/agent_service.py`
  - Import existing agent_invoker and agent_loader
  - Create async wrapper for streaming
  - _Requirements: 11.1, 11.2, 11.4_

- [x] 4. Implement chat endpoints
  - Create `backend/app/api/chat.py`
  - Implement POST /api/chat for non-streaming
  - Implement GET /api/chat/stream for SSE streaming
  - Add error handling
  - _Requirements: 2.1, 2.2, 2.3, 4.1, 4.2_

- [x] 5. Implement session endpoints
  - Create `backend/app/api/sessions.py`
  - Implement POST /api/sessions (create)
  - Implement GET /api/sessions/{id}/messages (get history)
  - Implement DELETE /api/sessions/{id} (clear)
  - _Requirements: 3.1, 3.5, 4.3, 4.4, 4.5_

- [x] 6. Create Pydantic models
  - Create `backend/app/models/schemas.py`
  - Define Message, ChatRequest, ChatResponse, SessionResponse models
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 7. Add backend configuration
  - Create `backend/app/core/config.py`
  - Load environment variables
  - Configure CORS origins
  - _Requirements: 5.4, 10.3_

- [x] 8. Create backend requirements.txt
  - Add fastapi, uvicorn, sse-starlette
  - Add existing dependencies from main pyproject.toml
  - _Requirements: 1.1_

## Phase 2: Frontend Setup

- [x] 9. Initialize React project with Vite
  - Run `npm create vite@latest frontend -- --template react-ts`
  - Install dependencies
  - Configure Vite for proxy to backend
  - _Requirements: 1.1, 1.2_

- [x] 10. Set up Tailwind CSS
  - Install tailwindcss, postcss, autoprefixer
  - Configure tailwind.config.js with Vibehuntr colors
  - Create base styles in index.css
  - _Requirements: 1.5, 9.1, 9.2_

- [x] 11. Create TypeScript types
  - Create `frontend/src/types/index.ts`
  - Define Message, ChatState, API request/response types
  - _Requirements: 1.4_

- [x] 12. Create API client service
  - Create `frontend/src/services/api.ts`
  - Implement functions for all API endpoints
  - Add error handling
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

## Phase 3: React Components

- [x] 13. Create Header component
  - Create `frontend/src/components/Header.tsx`
  - Add Vibehuntr logo and title
  - Add "New Conversation" button
  - Apply Vibehuntr styling
  - _Requirements: 9.1, 9.3_

- [x] 14. Create Message component
  - Create `frontend/src/components/Message.tsx`
  - Display role (user/assistant) and content
  - Apply Vibehuntr message styling
  - Add timestamp display
  - _Requirements: 6.1, 9.2_

- [x] 15. Create MessageList component
  - Create `frontend/src/components/MessageList.tsx`
  - Map over messages array
  - Render Message components
  - Add auto-scroll to bottom
  - _Requirements: 6.1, 6.2, 6.5_

- [x] 16. Create ChatInput component
  - Create `frontend/src/components/ChatInput.tsx`
  - Add textarea with submit button
  - Handle Enter key to send
  - Disable during streaming
  - Apply Vibehuntr styling
  - _Requirements: 1.4, 7.5, 9.3_

- [x] 17. Create Chat container component
  - Create `frontend/src/components/Chat.tsx`
  - Compose Header, MessageList, ChatInput
  - Apply layout styling
  - _Requirements: 1.2, 1.3_

## Phase 4: State Management and Streaming

- [x] 18. Create useChat hook
  - Create `frontend/src/hooks/useChat.ts`
  - Manage messages state with useState
  - Manage sessionId state
  - Implement sendMessage function
  - Implement clearSession function
  - _Requirements: 1.4, 3.1, 3.5_

- [x] 19. Implement SSE streaming in useChat
  - Add EventSource connection in sendMessage
  - Handle 'message' events to append tokens
  - Handle 'done' event to close stream
  - Handle 'error' events
  - Update messages state as tokens arrive
  - _Requirements: 2.2, 2.3, 2.4, 7.1, 7.2, 7.3_

- [x] 20. Add streaming visual indicator
  - Show cursor or animation during streaming
  - Remove indicator when streaming completes
  - Update isStreaming state
  - _Requirements: 7.3, 7.4_

- [x] 21. Implement session initialization
  - Call POST /api/sessions on app load
  - Store session_id in state
  - Load existing messages if session exists
  - _Requirements: 3.1, 3.4_

## Phase 5: Error Handling and Polish

- [x] 22. Add frontend error handling
  - Wrap API calls in try-catch
  - Display error messages in chat
  - Add retry functionality
  - _Requirements: 8.1, 8.2, 8.5_

- [x] 23. Add backend error handling
  - Add global exception handler
  - Log errors with context
  - Return user-friendly error messages
  - _Requirements: 8.2, 8.3, 8.4_

- [x] 24. Add loading states
  - Show loading indicator while waiting for first token
  - Disable input during streaming
  - Show connection status
  - _Requirements: 7.5_

- [x] 25. Implement welcome message
  - Show welcome screen when no messages
  - Display Vibehuntr branding and capabilities
  - _Requirements: 9.1, 9.4_

- [x] 26. Add message timestamps
  - Display timestamp for each message
  - Format timestamps nicely
  - _Requirements: 6.4_

## Phase 6: Testing

- [x] 27. Write backend unit tests
  - Test session_manager methods
  - Test API endpoints
  - Test error handlinghttp://127.0.0.1:5173/
  - _Requirements: 12.1, 12.4_

- [x] 28. Write frontend component tests
  - Test Message component rendering
  - Test MessageList without duplicates
  - Test ChatInput functionality
  - Test useChat hook
  - _Requirements: 12.2, 12.3_

- [x] 29. Write integration tests
  - Test full message flow
  - Test streaming end-to-end
  - Test session management
  - _Requirements: 12.3, 12.5_

## Phase 7: Documentation and Deployment

- [x] 30. Create development setup documentation
  - Document how to run backend
  - Document how to run frontend
  - Document environment variables needed
  - _Requirements: 10.1, 10.3_

- [x] 31. Create production deployment guide
  - Document backend deployment (Cloud Run)
  - Document frontend deployment (Cloud Storage)
  - Document environment configuration
  - _Requirements: 10.2, 10.4, 10.5_

- [x] 32. Update main README
  - Add React + FastAPI architecture overview
  - Link to setup documentation
  - Add screenshots
  - _Requirements: 10.5_

## Phase 8: Migration and Cleanup

- [x] 33. Verify feature parity
  - Test all features from Streamlit version
  - Verify no duplicate messages
  - Verify streaming works correctly
  - Verify context retention
  - _Requirements: 6.1, 6.2, 6.3, 7.1, 7.2_

- [x] 34. Performance testing
  - Test with long conversations
  - Test with rapid message sending
  - Verify no memory leaks
  - _Requirements: 7.5_

- [x] 35. Archive Streamlit version
  - Move vibehuntr_playground.py to archive/
  - Update documentation to point to React version
  - Keep for reference
  - _Requirements: 11.5_
