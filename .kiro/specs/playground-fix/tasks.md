# Implementation Plan

- [x] 1. Refactor SessionManager to use ADK as single source of truth
  - Modify `app/event_planning/session_manager.py` to wrap ADK session service
  - Remove internal message storage (`messages` list)
  - Remove `add_message()` method (ADK handles this automatically)
  - Add `get_or_create_session()` method
  - Update `get_messages()` to query ADK session service
  - Add `clear_session()` method for new conversations
  - Keep agent caching functionality separate
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 7.1_

- [x] 1.1 Write property test for session manager
  - **Property 16: History storage round-trip**
  - **Validates: Requirements 7.3**

- [x] 1.2 Write property test for history retrieval order
  - **Property 17: History retrieval order**
  - **Validates: Requirements 7.4**

- [x] 2. Update AgentInvoker to remove chat_history parameter
  - Modify `app/event_planning/agent_invoker.py`
  - Remove `chat_history` parameter from `invoke_agent_streaming()`
  - Remove `chat_history` parameter from `invoke_agent()`
  - Remove `_format_chat_history()` helper function (no longer needed)
  - Update docstrings to reflect that ADK session service handles history
  - Ensure session_id is properly passed to ADK Runner
  - _Requirements: 2.5, 7.2_

- [x] 2.1 Write property test for session ID consistency
  - **Property 15: Session ID consistency**
  - **Validates: Requirements 7.2**

- [x] 2.2 Write property test for history availability to agent
  - **Property 6: History availability to agent**
  - **Validates: Requirements 2.5**

- [x] 3. Refactor playground UI to query ADK for history
  - Modify `vibehuntr_playground.py`
  - Update message display loop to query SessionManager (which queries ADK)
  - Remove inline message display after adding to history
  - Implement clean display flow: display from history → handle input → stream response → rerun
  - Add processing flag to prevent duplicate processing on rerun
  - Ensure user message is displayed inline immediately
  - Ensure agent response is streamed inline with cursor
  - After streaming completes, rerun to show all messages from ADK history
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 5.1_

- [x] 3.1 Write property test for message display uniqueness
  - **Property 1: Message display uniqueness**
  - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

- [x] 3.2 Write property test for streaming completion consistency
  - **Property 2: Streaming completion consistency**
  - **Validates: Requirements 1.5**

- [x] 3.3 Write property test for state preservation across reruns
  - **Property 7: State preservation across reruns**
  - **Validates: Requirements 4.1**

- [x] 4. Implement comprehensive error handling
  - Add error handling for agent invocation failures in `agent_invoker.py`
  - Add error handling for session errors in `session_manager.py`
  - Add error handling for streaming errors in `vibehuntr_playground.py`
  - Implement user-friendly error messages (no internal details)
  - Add detailed error logging with context (timestamp, session_id, etc.)
  - Implement automatic recovery for session errors
  - Ensure errors don't corrupt conversation history
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 4.1 Write property test for error handling during streaming
  - **Property 10: Error handling during streaming**
  - **Validates: Requirements 5.5**

- [x] 4.2 Write property test for user-friendly error messages
  - **Property 11: User-friendly error messages**
  - **Validates: Requirements 6.1, 6.4**

- [x] 4.3 Write property test for error recovery without corruption
  - **Property 12: Error recovery without corruption**
  - **Validates: Requirements 6.5**

- [x] 4.4 Write property test for error logging completeness
  - **Property 13: Error logging completeness**
  - **Validates: Requirements 6.3**

- [x] 4.5 Write property test for session error recovery
  - **Property 14: Session error recovery**
  - **Validates: Requirements 6.2**

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement context retention verification
  - Add logging to verify agent receives full history
  - Test multi-turn conversations manually
  - Verify agent remembers information from earlier turns
  - Verify agent doesn't repeat questions
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 6.1 Write property test for context retention across turns
  - **Property 3: Context retention across turns**
  - **Validates: Requirements 2.1, 2.3**

- [x] 6.2 Write property test for question non-repetition
  - **Property 4: Question non-repetition**
  - **Validates: Requirements 2.2**

- [x] 6.3 Write property test for reference resolution
  - **Property 5: Reference resolution**
  - **Validates: Requirements 2.4**

- [x] 7. Implement streaming UI improvements
  - Ensure streaming shows cursor (▌) during generation
  - Remove cursor when streaming completes
  - Ensure streaming doesn't block UI
  - Add visual feedback for processing state
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 7.1 Write property test for streaming display progression
  - **Property 9: Streaming display progression**
  - **Validates: Requirements 5.1**

- [x] 8. Add "New Conversation" functionality
  - Implement clear_session() in SessionManager
  - Add UI button to start new conversation
  - Verify new session starts with empty history
  - Verify new session gets new session ID
  - _Requirements: 7.5_

- [x] 9. Update documentation
  - Update BUGFIX_DUPLICATE_RESPONSES.md with final solution
  - Update PLAYGROUND_GUIDE.md with architecture explanation
  - Document the single source of truth pattern
  - Add troubleshooting guide for common issues
  - _Requirements: All_

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Manual testing and validation
  - Run through manual testing checklist
  - Verify no duplicate messages
  - Verify context retention works
  - Verify streaming works smoothly
  - Verify error handling is user-friendly
  - Verify new conversation functionality
  - _Requirements: All_
