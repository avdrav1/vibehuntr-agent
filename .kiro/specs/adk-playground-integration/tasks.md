# Implementation Plan

- [x] 1. Create agent loader module
  - Create `app/event_planning/agent_loader.py` with agent selection logic
  - Implement `get_agent()` function that checks `USE_DOCUMENT_RETRIEVAL` environment variable
  - Add agent instance caching to avoid reloading
  - Handle import errors gracefully with informative messages
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 2. Create session manager module
  - Create `app/event_planning/session_manager.py` for session state management
  - Implement `SessionManager` class with Streamlit session state integration
  - Add methods for message management: `get_messages()`, `get_all_messages()`, `add_message()`, `clear_messages()`
  - Implement history pagination logic with `recent_only` parameter
  - Add `should_show_history_button()` method to check if older messages exist
  - Add agent caching in session state
  - _Requirements: 3.1, 3.2, 3.4, 3.5_

- [x] 2.1 Write property test for session manager
  - **Property 1: Message persistence in session**
  - **Property 2: Agent response persistence**
  - **Property 4: Fresh session on refresh**
  - **Property 11: Recent messages display limit**
  - **Property 12: Complete history availability**
  - **Validates: Requirements 3.1, 3.2, 3.4, 3.5**

- [x] 3. Create agent invoker module
  - Create `app/event_planning/agent_invoker.py` for agent invocation logic
  - Implement `invoke_agent_streaming()` function with generator for token streaming
  - Implement `invoke_agent()` function for complete response
  - Add chat history formatting for ADK agent context
  - Implement error handling with custom `AgentInvocationError` exception
  - Add logging for invocations and errors
  - _Requirements: 1.1, 1.2, 2.1, 3.3, 5.1, 7.1, 7.2_

- [x] 3.1 Write property test for agent invoker
  - **Property 3: Session context provision**
  - **Property 6: Streaming token order**
  - **Validates: Requirements 3.3, 2.1**

- [x] 3.2 Write unit tests for agent invoker
  - Test message formatting for ADK context
  - Test error handling and exception raising
  - Test logging behavior
  - Mock agent responses for testing
  - _Requirements: 1.1, 1.2, 7.1, 7.2_

- [x] 4. Update playground interface with agent integration
  - Update `vibehuntr_playground.py` to import new modules
  - Initialize `SessionManager` in session state
  - Replace placeholder response with actual agent invocation
  - Implement streaming response display using `st.write_stream()` or progressive updates
  - Add loading indicator during agent processing
  - Implement input blocking while agent is processing
  - _Requirements: 1.1, 1.2, 1.4, 2.1, 2.2, 2.3, 5.1, 5.5_

- [x] 5. Implement history pagination UI
  - Modify message display to show only last 10 messages by default
  - Add "Show Older Messages" expander section for messages beyond the recent 10
  - Conditionally display expander only when there are more than 10 messages
  - Ensure chat input remains visible at bottom of page
  - Use `st.container()` for organized layout
  - _Requirements: 1.3, 3.5_

- [x] 5.1 Write property test for history pagination
  - **Property 11: Recent messages display limit**
  - **Property 12: Complete history availability**
  - **Validates: Requirements 1.3, 3.5**

- [x] 6. Add conversation management features
  - Add "New Conversation" button in sidebar or below chat input
  - Implement conversation reset functionality using `SessionManager.clear_messages()`
  - Display welcome message when starting new conversation
  - Add confirmation dialog for clearing conversation (optional)
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 7. Implement error handling and display
  - Add try-catch blocks around agent invocation
  - Display user-friendly error messages using `st.error()`
  - Apply Vibehuntr styling to error messages
  - Ensure errors don't crash the application
  - Add error logging with context (timestamp, error type, user message, session ID)
  - _Requirements: 2.4, 5.2, 5.3, 6.4, 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 7.1 Write property test for error handling
  - **Property 7: Error message display**
  - **Property 8: Input blocking during processing**
  - **Validates: Requirements 5.2, 5.5, 7.4**

- [x] 7.2 Write unit tests for error scenarios
  - Test agent loading errors
  - Test agent invocation errors
  - Test streaming errors
  - Test session state errors
  - Verify error messages are user-friendly
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 8. Enhance UI with status indicators
  - Add visual indicator when agent is thinking (spinner or animated icon)
  - Show "Agent is typing..." message during streaming
  - Display completion indicator when response is done
  - Optionally show tool invocations in UI for transparency
  - _Requirements: 5.1, 5.3, 5.4_

- [x] 9. Maintain Vibehuntr branding throughout
  - Ensure all new UI elements use Vibehuntr styling from `playground_style.py`
  - Apply custom CSS to chat messages, buttons, and error displays
  - Verify header and branding elements remain intact
  - Test responsive layout on different screen sizes
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 9.1 Write unit tests for styling
  - Test that Vibehuntr CSS is applied to messages
  - Test that error messages use styled containers
  - Verify branding elements are present
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 10. Add environment configuration documentation
  - Update `PLAYGROUND_GUIDE.md` with ADK integration instructions
  - Document required environment variables (`USE_DOCUMENT_RETRIEVAL`, `GOOGLE_API_KEY`, etc.)
  - Add troubleshooting section for common issues
  - Provide example `.env` configuration
  - _Requirements: 4.1, 4.2, 4.4_

- [x] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Integration testing
  - Test complete conversation flow from user input to agent response
  - Test with both full agent and simple agent configurations
  - Test history pagination with various message counts
  - Test error recovery scenarios
  - Test "New Conversation" functionality
  - Verify session isolation between page refreshes
  - _Requirements: 1.1, 1.2, 1.3, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 8.1, 8.2_

- [x] 13. Manual testing and validation
  - Test visual appearance and Vibehuntr branding
  - Test on different screen sizes and browsers
  - Verify streaming performance with long responses
  - Test various conversation scenarios (event planning, venue search, etc.)
  - Validate error messages are clear and helpful
  - Test with real Gemini API to ensure tool invocations work
  - _Requirements: 1.1, 1.2, 1.4, 2.1, 5.1, 5.4, 6.1, 6.2_
