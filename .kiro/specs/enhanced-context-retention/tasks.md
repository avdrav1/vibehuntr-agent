# Implementation Plan: Enhanced Context Retention

## Overview

This implementation plan breaks down the enhanced context retention feature into discrete, manageable coding tasks. Each task builds incrementally on previous work, with property-based tests integrated throughout to validate correctness.

## Tasks

- [x] 1. Enhance Context Manager with improved extraction
- [x] 1.1 Expand location extraction patterns
  - Add patterns for more cities and location phrases ("around", "near")
  - Update LOCATION_PATTERNS list in context_manager.py
  - _Requirements: 1.1_

- [x] 1.2 Expand search query extraction patterns
  - Add patterns for more food types and venue types
  - Add patterns for meal times (brunch, lunch, dinner)
  - Update SEARCH_PATTERNS list in context_manager.py
  - _Requirements: 3.1_

- [x] 1.3 Add timestamp tracking to VenueInfo
  - Add mentioned_at field with datetime
  - Update VenueInfo dataclass
  - _Requirements: 2.1_

- [x] 1.4 Implement venue list size limiting
  - Ensure recent_venues list never exceeds 5 items
  - Remove oldest when adding 6th item
  - _Requirements: 2.4_

- [x] 1.5 Write property test for venue list size limit
  - **Property 8: Venue list size limit**
  - **Validates: Requirements 2.4**

- [x] 1.6 Enhance entity reference resolution
  - Improve find_venue_by_reference to handle more patterns
  - Add support for "that one", "this one", "the one"
  - _Requirements: 2.2, 2.5_

- [x] 1.7 Write property test for reference resolution
  - **Property 6: Vague reference resolution**
  - **Validates: Requirements 2.2**

- [x] 1.8 Write property test for ordinal resolution
  - **Property 9: Ordinal reference resolution**
  - **Validates: Requirements 2.5_

- [x] 1.9 Add to_dict methods for serialization
  - Implement to_dict on ConversationContext
  - Implement to_dict on VenueInfo
  - _Requirements: 11.2_

- [x] 1.10 Write unit tests for context manager
  - Test location extraction
  - Test search query extraction
  - Test venue extraction from agent responses
  - Test context string generation
  - _Requirements: 1.1, 2.1, 3.1, 5.1_

- [x] 2. Enhance Agent Invoker with context injection
- [x] 2.1 Update invoke_agent_streaming to inject context
  - Get context for session
  - Extract context from user message
  - Generate context string
  - Prepend context to message
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 2.2 Write property test for context injection
  - **Property 19: Context prepending**
  - **Validates: Requirements 5.3**

- [x] 2.3 Add context extraction from agent responses
  - Parse agent response for venues and Place IDs
  - Update context with extracted entities
  - _Requirements: 4.1, 4.2_

- [x] 2.4 Write property test for entity extraction
  - **Property 14: Entity extraction from agent responses**
  - **Validates: Requirements 4.1, 4.2**

- [x] 2.5 Add comprehensive logging for context operations
  - Log context extraction with session_id
  - Log context injection with full context string
  - Log entity storage operations
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 2.6 Write property test for context logging
  - **Property 20: Context logging**
  - **Validates: Requirements 5.5, 7.2**

- [x] 2.7 Add error handling for context operations
  - Wrap context extraction in try-catch
  - Wrap context injection in try-catch
  - Ensure graceful degradation on errors
  - _Requirements: 7.5_

- [x] 2.8 Write unit tests for agent invoker context
  - Test context injection flow
  - Test error handling
  - Test entity extraction from responses
  - _Requirements: 5.3, 4.1, 7.5_

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Update agent instructions for context awareness
- [x] 4.1 Add CRITICAL CONTEXT RETENTION RULES section
  - Add rules for reading [CONTEXT: ...] prefix
  - Add rules for remembering own responses
  - Add rules for location persistence
  - Add rules for entity references
  - _Requirements: 6.1_

- [x] 4.2 Add EXAMPLES OF CORRECT BEHAVIOR section
  - Add example for location persistence
  - Add example for entity reference
  - Add example for search query persistence
  - _Requirements: 6.2_

- [x] 4.3 Add EXAMPLES OF INCORRECT BEHAVIOR section
  - Add examples of what NOT to do
  - Use ❌ markers for clarity
  - _Requirements: 6.3_

- [x] 4.4 Update both USE_DOCUMENT_RETRIEVAL modes
  - Update instructions for document retrieval mode
  - Update instructions for event planning only mode
  - Ensure consistency between both
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 5. Create backend API for context management
- [x] 5.1 Create context API router
  - Create backend/app/api/context.py
  - Set up FastAPI router with /api/context prefix
  - _Requirements: 11.2_

- [x] 5.2 Implement GET /api/context/{session_id}
  - Return current context for session
  - Include location, search_query, recent_venues
  - _Requirements: 11.2_

- [x] 5.3 Implement DELETE /api/context/{session_id}
  - Clear all context for session
  - Log the clear operation
  - _Requirements: 10.2, 10.3_

- [x] 5.4 Write property test for context clearing
  - **Property 25: Context clearing**
  - **Validates: Requirements 10.2**

- [x] 5.5 Implement DELETE /api/context/{session_id}/item
  - Clear specific context items (location, query, venue)
  - Support index parameter for venue removal
  - _Requirements: 11.6_

- [x] 5.6 Create Pydantic models for API responses
  - Create VenueResponse model
  - Create ContextResponse model
  - Create StatusResponse model
  - _Requirements: 11.2_

- [x] 5.7 Register context router in main.py
  - Import context router
  - Add to app.include_router
  - _Requirements: 11.2_

- [x] 5.8 Write unit tests for context API
  - Test GET endpoint
  - Test DELETE endpoints
  - Test error handling
  - _Requirements: 11.2, 10.2, 11.6_

- [x] 6. Create Context Display UI component
- [x] 6.1 Create ContextDisplay component
  - Create frontend/src/components/ContextDisplay.tsx
  - Define ContextDisplayProps interface
  - Implement basic component structure
  - _Requirements: 11.1, 11.2_

- [x] 6.2 Implement context data fetching
  - Add fetchContext function to api.ts
  - Use useEffect to fetch on mount and updates
  - Handle loading and error states
  - _Requirements: 11.2_

- [x] 6.3 Implement context display UI
  - Show location with 📍 icon
  - Show search query with 🔍 icon
  - Show recent venues with 🏪 icon
  - Add [×] buttons for each item
  - Add [Clear All] button
  - _Requirements: 11.2, 11.6_

- [x] 6.4 Style with Vibehuntr theme
  - Use purple accent colors (rgba(139, 92, 246, ...))
  - Use dark background
  - Add hover effects for buttons
  - Ensure responsive design
  - _Requirements: 11.7_

- [x] 6.5 Implement clear functionality
  - Add onClearItem handler
  - Add onClearAll handler
  - Call DELETE API endpoints
  - Update local state after clearing
  - _Requirements: 11.6_

- [x] 6.6 Add real-time context updates
  - Update context display when new messages arrive
  - Use React state to trigger re-renders
  - _Requirements: 11.4_

- [x] 6.7 Integrate ContextDisplay into ChatInterface
  - Import ContextDisplay component
  - Add to ChatInterface layout
  - Pass sessionId and context props
  - _Requirements: 11.1_

- [x] 6.8 Write unit tests for ContextDisplay
  - Test rendering with context
  - Test empty state
  - Test clear button functionality
  - Test real-time updates
  - _Requirements: 11.2, 11.4, 11.6_

- [x] 7. Add context types to frontend
- [x] 7.1 Create context types in types.ts
  - Add ConversationContext interface
  - Add VenueInfo interface
  - Export types
  - _Requirements: 11.2_

- [x] 7.2 Update useChat hook tINFO:     Waiting for application lette.sse - DEBUG - chunk: b'event: message\r\ndata: {"type":"token"INFO:     127.0.0.1:46364 - "OPTIONS /api/sessions HTTP/1.1" 200 OK
2025-11-22 10:02:18,459 - backend.app.api.sessions - INFO - Creating new session: c7129b5b-41a3-417a-9a4b-053454866507
2025-11-22 10:02:18,459 - backend.app.api.sessions - INFO - Session created successfully: c7129b5b-41a3-417a-9a4b-053454866507
INFO:     127.0.0.1:46376 - "POST /api/sessions HTTP/1.1" 201 Created
INFO:     127.0.0.1:46376 - "OPTIONS /api/sessions/c7129b5b-41a3-417a-9a4b-053454866507/messages HTTP/1.1" 200 OK
2025-11-22 10:02:18,487 - backend.app.api.sessions - INFO - Retrieving messages for session: c7129b5b-41a3-417a-9a4b-053454866507
2025-11-22 10:02:18,488 - backend.app.api.sessions - INFO - Retrieved 0 messages for session c7129b5b-41a3-417a-9a4b-053454866507
INFO:     127.0.0.1:46364 - "GET /api/sessions/c7129b5b-41a3-417a-9a4b-053454866507/messages HTTP/1.1" 200 OK
INFO:     127.0.0.1:46388 - "GET /api/chat/stream?session_id=c7129b5b-41a3-417a-9a4b-053454866507&message=Cheesesteak HTTP/1.1" 200 OK
2025-11-22 10:02:24,249 - backend.app.api.chat - INFO - Starting stream for session c7129b5b-41a3-417a-9a4b-053454866507: Cheesesteak...
2025-11-22 10:02:24,249 - backend.app.api.chat - DEBUG - Added user message to session c7129b5b-41a3-417a-9a4b-053454866507
2025-11-22 10:02:24,249 - backend.app.services.agent_service - INFO - AgentService initialized
/home/av/Development/vibehuntr/vibehuntr-agent/.venv/lib/python3.12/site-packages/google/cloud/aiplatform/models.py:52: FutureWarning: Support for google-cloud-storage < 3.0.0 will be removed in a future version of google-cloud-aiplatform. Please upgrade to google-cloud-storage >= 3.0.0.
  from google.cloud.aiplatform.utils import gcs_utils
2025-11-22 10:02:27,414 - app.event_planning.agent_loader - INFO - Loading simple agent (event planning only) from app.event_planning.simple_agent
2025-11-22 10:02:27,426 - app.event_planning.agent_loader - INFO - Successfully loaded simple agent
2025-11-22 10:02:27,427 - backend.app.services.agent_service - INFO - Agent loaded successfully
2025-11-22 10:02:27,427 - app.event_planning.agent_invoker - INFO - Invoking agent with streaming for message: Cheesesteak...
2025-11-22 10:02:27,427 - app.event_planning.agent_invoker - DEBUG - Session ID: c7129b5b-41a3-417a-9a4b-053454866507, User ID: web_user
2025-11-22 10:02:27,428 - app.event_planning.agent_invoker - WARNING - Session retrieval failed, creating new session: InMemorySessionService.get_session_sync() missing 2 required keyword-only arguments: 'app_name' and 'user_id'
2025-11-22 10:02:27,428 - google_adk.google.adk.sessions.in_memory_session_service - WARNING - Deprecated. Please migrate to the async method.
2025-11-22 10:02:27,428 - app.event_planning.agent_invoker - INFO - Successfully created new session: 1e815e10-4995-49ca-8b5f-f0930ac88f4c
2025-11-22 10:02:27,428 - google_adk.google.adk.runners - WARNING - App name mismatch detected. The runner is configured with app name "vibehuntr_playground", but the root agent was loaded from "/home/av/Development/vibehuntr/vibehuntr-agent/.venv/lib/python3.12/site-packages/google/adk/agents", which implies app name "agents".
2025-11-22 10:02:27,429 - app.event_planning.agent_invoker - DEBUG - Created ADK Runner successfully
2025-11-22 10:02:27,429 - app.event_planning.agent_invoker - ERROR - Failed to create message content: UnboundLocalError: cannot access local variable 'enhanced_message' where it is not associated with a value
Traceback (most recent call last):
  File "/home/av/Development/vibehuntr/vibehuntr-agent/app/event_planning/agent_invoker.py", line 151, in invoke_agent_streaming
    parts=[types.Part.from_text(text=enhanced_message)]
                                     ^^^^^^^^^^^^^^^^
UnboundLocalError: cannot access local variable 'enhanced_message' where it is not associated with a value
2025-11-22 10:02:27,429 - backend.app.services.agent_service - ERROR - Agent streaming failed: AgentInvocationError: Failed to create message content: UnboundLocalError: cannot access local variable 'enhanced_message' where it is not associated with a value
Traceback (most recent call last):
  File "/home/av/Development/vibehuntr/vibehuntr-agent/app/event_planning/agent_invoker.py", line 151, in invoke_agent_streaming
    parts=[types.Part.from_text(text=enhanced_message)]
                                     ^^^^^^^^^^^^^^^^
UnboundLocalError: cannot access local variable 'enhanced_message' where it is not associated with a value

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/av/Development/vibehuntr/vibehuntr-agent/backend/app/services/agent_service.py", line 154, in stream_agent
    items = await loop.run_in_executor(None, sync_generator_wrapper)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/av/.local/share/uv/python/cpython-3.12.11-linux-x86_64-gnu/lib/python3.12/concurrent/futures/thread.py", line 59, in run
    result = self.fn(*self.args, **self.kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/av/Development/vibehuntr/vibehuntr-agent/backend/app/services/agent_service.py", line 151, in sync_generator_wrapper
    return list(stream_func())
           ^^^^^^^^^^^^^^^^^^^
  File "/home/av/Development/vibehuntr/vibehuntr-agent/app/event_planning/agent_invoker.py", line 164, in invoke_agent_streaming
    raise AgentInvocationError(error_msg) from content_error
app.event_planning.agent_invoker.AgentInvocationError: Failed to create message content: UnboundLocalError: cannot access local variable 'enhanced_message' where it is not associated with a value
2025-11-22 10:02:27,430 - backend.app.api.chat - ERROR - Agent streaming failed for session c7129b5b-41a3-417a-9a4b-053454866507: Agent streaming failed: AgentInvocationError: Failed to create message content: UnboundLocalError: cannot access local variable 'enhanced_message' where it is not associated with a value
Traceback (most recent call last):
  File "/home/av/Development/vibehuntr/vibehuntr-agent/app/event_planning/agent_invoker.py", line 151, in invoke_agent_streaming
    parts=[types.Part.from_text(text=enhanced_message)]
                                     ^^^^^^^^^^^^^^^^
UnboundLocalError: cannot access local variable 'enhanced_message' where it is not associated with a value

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/av/Development/vibehuntr/vibehuntr-agent/backend/app/services/agent_service.py", line 154, in stream_agent
    items = await loop.run_in_executor(None, sync_generator_wrapper)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/av/.local/share/uv/python/cpython-3.12.11-linux-x86_64-gnu/lib/python3.12/concurrent/futures/thread.py", line 59, in run
    result = self.fn(*self.args, **self.kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/av/Development/vibehuntr/vibehuntr-agent/backend/app/services/agent_service.py", line 151, in sync_generator_wrapper
    return list(stream_func())
           ^^^^^^^^^^^^^^^^^^^
  File "/home/av/Development/vibehuntr/vibehuntr-agent/app/event_planning/agent_invoker.py", line 164, in invoke_agent_streaming
    raise AgentInvocationError(error_msg) from content_error
app.event_planning.agent_invoker.AgentInvocationError: Failed to create message content: UnboundLocalError: cannot access local variable 'enhanced_message' where it is not associated with a value

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/av/Development/vibehuntr/vibehuntr-agent/backend/app/api/chat.py", line 205, in event_generator
    async for item in agent_service.stream_agent(
  File "/home/av/Development/vibehuntr/vibehuntr-agent/backend/app/services/agent_service.py", line 167, in stream_agent
    raise AgentInvocationError(error_msg) from e
backend.app.services.agent_service.AgentInvocationError: Agent streaming failed: AgentInvocationError: Failed to create message content: UnboundLocalError: cannot access local variable 'enhanced_message' where it is not associated with a value
2025-11-22 10:02:27,431 - sse_starlette.sse - DEBUG - chunk: b'event: error\r\ndata: {"type":"error","content":"Agent invocation failed: Agent streaming failed: AgentInvocationError: Failed to create message content: UnboundLocalError: cannot access local variable \'enhanced_message\' where it is not associated with a value"}\r\n\r\n'
2025-11-22 10:02:27,432 - sse_starlette.sse - DEBUG - Got event: http.disconnect. Stop streaming.o manage context
  - Add context state
  - Fetch context on session init
  - Update context after each message
  - _Requirements: 11.4_

- [x] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Write integration tests
- [x] 9.1 Write end-to-end context flow test
  - Test location persistence across turns
  - Test entity reference resolution
  - Test search query persistence
  - _Requirements: 1.2, 2.2, 3.2_

- [x] 9.2 Write property test for multi-turn accumulation
  - **Property 21: Multi-turn context accumulation**
  - **Validates: Requirements 8.1**

- [x] 9.3 Write property test for session isolation
  - **Property 24: Session context isolation**
  - **Validates: Requirements 10.4**

- [x] 9.4 Write property test for context format
  - **Property 18: Context string format**
  - **Validates: Requirements 5.2**

- [x] 9.5 Write UI integration test for context display
  - Test context display updates in real-time
  - Test clear functionality
  - _Requirements: 11.4, 11.6_

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
