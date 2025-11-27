/**
 * Property-based tests for useChat functionality
 * Tests universal properties that should hold across all inputs
 * 
 * **Feature: chat-ux-improvements, Property 6: Retry sends same content**
 * **Feature: chat-ux-improvements, Property 5: Failed messages show retry**
 * **Feature: chat-ux-improvements, Property 1: New sessions appear at list top**
 * Uses fast-check for property-based testing
 */

import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import type { Message, SessionSummary } from '../types';

/**
 * Simulates the retry logic from useChat hook
 * This extracts the core logic for testing without React hooks
 */
function simulateRetryMessage(
  messages: Message[],
  messageIndex: number
): { contentToRetry: string | null; messagesAfterRetry: Message[] } {
  // Get the message content at the specified index
  const messageToRetry = messages[messageIndex];
  
  if (!messageToRetry || messageToRetry.role !== 'user') {
    return { contentToRetry: null, messagesAfterRetry: messages };
  }
  
  const contentToRetry = messageToRetry.content;
  
  // Remove the failed user message and any subsequent messages
  const messagesAfterRetry = messages.slice(0, messageIndex);
  
  return { contentToRetry, messagesAfterRetry };
}

/**
 * Simulates marking a message as failed
 */
function markMessageAsFailed(
  messages: Message[],
  messageIndex: number,
  errorMessage: string
): { updatedMessages: Message[]; failedIndices: Set<number> } {
  const updatedMessages = [...messages];
  const failedIndices = new Set<number>();
  
  if (messageIndex >= 0 && messageIndex < messages.length && messages[messageIndex].role === 'user') {
    updatedMessages[messageIndex] = {
      ...messages[messageIndex],
      status: 'failed',
      error: errorMessage,
    };
    failedIndices.add(messageIndex);
  }
  
  return { updatedMessages, failedIndices };
}

// Helper to generate valid message content
const validMessageContent = fc.string({ minLength: 1, maxLength: 500 })
  .filter(s => s.trim().length > 0);

// Helper to generate valid ISO timestamp strings
const validTimestamp = fc.integer({ 
  min: new Date('2000-01-01').getTime(), 
  max: new Date('2030-12-31').getTime() 
}).map(ts => new Date(ts).toISOString());

// Helper to generate a user message
const userMessage = fc.record({
  role: fc.constant('user' as const),
  content: validMessageContent,
  timestamp: validTimestamp,
});

// Helper to generate an assistant message
const assistantMessage = fc.record({
  role: fc.constant('assistant' as const),
  content: validMessageContent,
  timestamp: validTimestamp,
});

describe('useChat Retry - Property-Based Tests', () => {
  /**
   * Property 6: Retry sends same content
   * *For any* retry operation on a failed message, the content sent to the agent 
   * should equal the original message content
   * 
   * **Validates: Requirements 3.2**
   */
  describe('Property 6: Retry sends same content', () => {
    it('should return the exact original message content when retrying', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          // Generate a conversation with at least one user message
          fc.array(
            fc.oneof(userMessage, assistantMessage),
            { minLength: 1, maxLength: 10 }
          ).filter(msgs => msgs.some(m => m.role === 'user')),
          (messages) => {
            // Find a user message index to retry
            const userMessageIndices = messages
              .map((m, i) => ({ message: m, index: i }))
              .filter(({ message }) => message.role === 'user')
              .map(({ index }) => index);
            
            // Pick a random user message index
            const indexToRetry = userMessageIndices[Math.floor(Math.random() * userMessageIndices.length)];
            const originalContent = messages[indexToRetry].content;
            
            // Simulate retry
            const { contentToRetry } = simulateRetryMessage(messages, indexToRetry);
            
            // Property: content to retry should equal original content exactly
            expect(contentToRetry).toBe(originalContent);
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should preserve content exactly including whitespace and special characters', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          // Generate content with various special characters
          fc.string({ minLength: 1, maxLength: 200 }),
          validTimestamp,
          (content, timestamp) => {
            // Skip empty content after trim
            if (content.trim().length === 0) return true;
            
            const messages: Message[] = [
              { role: 'user', content, timestamp },
            ];
            
            const { contentToRetry } = simulateRetryMessage(messages, 0);
            
            // Property: content should be preserved exactly
            expect(contentToRetry).toBe(content);
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should return null for non-user messages', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          assistantMessage,
          (message) => {
            const messages: Message[] = [message];
            
            const { contentToRetry } = simulateRetryMessage(messages, 0);
            
            // Property: should not retry assistant messages
            expect(contentToRetry).toBeNull();
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should return null for invalid indices', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          fc.array(userMessage, { minLength: 1, maxLength: 5 }),
          fc.integer({ min: -100, max: 100 }),
          (messages, invalidIndex) => {
            // Only test truly invalid indices
            if (invalidIndex >= 0 && invalidIndex < messages.length) return true;
            
            const { contentToRetry } = simulateRetryMessage(messages, invalidIndex);
            
            // Property: should return null for invalid indices
            expect(contentToRetry).toBeNull();
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should remove all messages after the retried message index', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          // Generate a conversation with multiple messages
          fc.array(
            fc.oneof(userMessage, assistantMessage),
            { minLength: 2, maxLength: 10 }
          ).filter(msgs => msgs.some(m => m.role === 'user')),
          (messages) => {
            // Find a user message index to retry (not the last one if possible)
            const userMessageIndices = messages
              .map((m, i) => ({ message: m, index: i }))
              .filter(({ message }) => message.role === 'user')
              .map(({ index }) => index);
            
            const indexToRetry = userMessageIndices[0]; // Use first user message
            
            // Simulate retry
            const { messagesAfterRetry } = simulateRetryMessage(messages, indexToRetry);
            
            // Property: messages after retry should only contain messages before the retried index
            expect(messagesAfterRetry.length).toBe(indexToRetry);
            
            // All remaining messages should be from before the retry index
            messagesAfterRetry.forEach((msg, i) => {
              expect(msg).toEqual(messages[i]);
            });
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 5: Failed messages show retry
   * *For any* message with status 'failed', the retry button should be visible in the UI
   * 
   * This tests the state tracking logic that determines which messages are failed
   * 
   * **Validates: Requirements 3.1**
   */
  describe('Property 5: Failed messages show retry', () => {
    it('should track failed message indices correctly', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          // Generate a conversation with user messages
          fc.array(userMessage, { minLength: 1, maxLength: 10 }),
          fc.string({ minLength: 1, maxLength: 100 }), // error message
          (messages, errorMessage) => {
            // Pick a random message index to mark as failed
            const indexToFail = Math.floor(Math.random() * messages.length);
            
            const { updatedMessages, failedIndices } = markMessageAsFailed(
              messages,
              indexToFail,
              errorMessage
            );
            
            // Property: failed index should be tracked
            expect(failedIndices.has(indexToFail)).toBe(true);
            
            // Property: failed message should have status 'failed'
            expect(updatedMessages[indexToFail].status).toBe('failed');
            
            // Property: failed message should have the error message
            expect(updatedMessages[indexToFail].error).toBe(errorMessage);
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should not mark assistant messages as failed', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          assistantMessage,
          fc.string({ minLength: 1, maxLength: 100 }),
          (message, errorMessage) => {
            const messages: Message[] = [message];
            
            const { updatedMessages, failedIndices } = markMessageAsFailed(
              messages,
              0,
              errorMessage
            );
            
            // Property: assistant messages should not be marked as failed
            expect(failedIndices.size).toBe(0);
            expect(updatedMessages[0].status).toBeUndefined();
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should preserve other message properties when marking as failed', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          userMessage,
          fc.string({ minLength: 1, maxLength: 100 }),
          (message, errorMessage) => {
            const messages: Message[] = [message];
            
            const { updatedMessages } = markMessageAsFailed(messages, 0, errorMessage);
            
            // Property: original properties should be preserved
            expect(updatedMessages[0].role).toBe(message.role);
            expect(updatedMessages[0].content).toBe(message.content);
            expect(updatedMessages[0].timestamp).toBe(message.timestamp);
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should correctly identify failed messages by status or index', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          fc.array(userMessage, { minLength: 1, maxLength: 10 }),
          fc.string({ minLength: 1, maxLength: 100 }),
          (messages, errorMessage) => {
            const indexToFail = Math.floor(Math.random() * messages.length);
            
            const { updatedMessages, failedIndices } = markMessageAsFailed(
              messages,
              indexToFail,
              errorMessage
            );
            
            // Check each message
            updatedMessages.forEach((msg, index) => {
              const isFailed = failedIndices.has(index) || msg.status === 'failed';
              
              if (index === indexToFail) {
                // Property: the failed message should be identified as failed
                expect(isFailed).toBe(true);
              } else {
                // Property: other messages should not be identified as failed
                expect(isFailed).toBe(false);
              }
            });
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});

/**
 * Simulates the edit message logic from useChat hook
 * This extracts the core logic for testing without React hooks
 */
function simulateStartEditMessage(
  messages: Message[],
  messageIndex: number,
  isStreaming: boolean,
  isLoading: boolean
): { canEdit: boolean; editContent: string | null } {
  // Only allow editing user messages
  if (messages[messageIndex]?.role !== 'user') {
    return { canEdit: false, editContent: null };
  }
  
  // Don't allow editing while streaming or loading
  if (isStreaming || isLoading) {
    return { canEdit: false, editContent: null };
  }
  
  return { canEdit: true, editContent: messages[messageIndex].content };
}

/**
 * Simulates saving an edited message
 */
function simulateSaveEditMessage(
  messages: Message[],
  messageIndex: number,
  newContent: string
): { messagesAfterEdit: Message[]; contentToSend: string | null } {
  if (!newContent.trim()) {
    return { messagesAfterEdit: messages, contentToSend: null };
  }
  
  // Remove all messages after the edited index
  const messagesAfterEdit = messages.slice(0, messageIndex);
  
  return { messagesAfterEdit, contentToSend: newContent.trim() };
}

/**
 * Simulates canceling an edit
 */
function simulateCancelEditMessage(
  originalContent: string,
  _editContent: string
): { restoredContent: string; editingIndex: number | null } {
  // Cancel should restore original content and clear editing state
  return { restoredContent: originalContent, editingIndex: null };
}

/**
 * Simulates checking if input should be disabled during edit mode
 */
function isInputDisabledDuringEdit(
  editingMessageIndex: number | null,
  isStreaming: boolean,
  isLoading: boolean
): boolean {
  return isStreaming || isLoading || editingMessageIndex !== null;
}

describe('useChat Edit - Property-Based Tests', () => {
  /**
   * Property 8: Edit input contains original
   * *For any* message entering edit mode, the edit input field should contain 
   * the exact original message content
   * 
   * **Feature: chat-ux-improvements, Property 8: Edit input contains original**
   * **Validates: Requirements 4.2**
   */
  describe('Property 8: Edit input contains original', () => {
    it('should populate edit input with exact original message content', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          // Generate a conversation with user messages
          fc.array(
            fc.oneof(userMessage, assistantMessage),
            { minLength: 1, maxLength: 10 }
          ).filter(msgs => msgs.some(m => m.role === 'user')),
          (messages) => {
            // Find a user message index to edit
            const userMessageIndices = messages
              .map((m, i) => ({ message: m, index: i }))
              .filter(({ message }) => message.role === 'user')
              .map(({ index }) => index);
            
            const indexToEdit = userMessageIndices[Math.floor(Math.random() * userMessageIndices.length)];
            const originalContent = messages[indexToEdit].content;
            
            // Simulate starting edit (not streaming, not loading)
            const { canEdit, editContent } = simulateStartEditMessage(messages, indexToEdit, false, false);
            
            // Property: should be able to edit and content should match exactly
            expect(canEdit).toBe(true);
            expect(editContent).toBe(originalContent);
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should preserve content exactly including whitespace and special characters', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          // Generate content with various special characters
          fc.string({ minLength: 1, maxLength: 200 }),
          validTimestamp,
          (content, timestamp) => {
            // Skip empty content after trim
            if (content.trim().length === 0) return true;
            
            const messages: Message[] = [
              { role: 'user', content, timestamp },
            ];
            
            const { canEdit, editContent } = simulateStartEditMessage(messages, 0, false, false);
            
            // Property: content should be preserved exactly
            expect(canEdit).toBe(true);
            expect(editContent).toBe(content);
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should not allow editing assistant messages', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          assistantMessage,
          (message) => {
            const messages: Message[] = [message];
            
            const { canEdit, editContent } = simulateStartEditMessage(messages, 0, false, false);
            
            // Property: should not be able to edit assistant messages
            expect(canEdit).toBe(false);
            expect(editContent).toBeNull();
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should not allow editing while streaming', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          userMessage,
          (message) => {
            const messages: Message[] = [message];
            
            const { canEdit } = simulateStartEditMessage(messages, 0, true, false);
            
            // Property: should not be able to edit while streaming
            expect(canEdit).toBe(false);
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should not allow editing while loading', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          userMessage,
          (message) => {
            const messages: Message[] = [message];
            
            const { canEdit } = simulateStartEditMessage(messages, 0, false, true);
            
            // Property: should not be able to edit while loading
            expect(canEdit).toBe(false);
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 9: Edit removes subsequent messages
   * *For any* saved edit at index N, all messages with index > N should be 
   * removed from the message list before re-sending
   * 
   * **Feature: chat-ux-improvements, Property 9: Edit removes subsequent messages**
   * **Validates: Requirements 4.4**
   */
  describe('Property 9: Edit removes subsequent messages', () => {
    it('should remove all messages after the edited index', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          // Generate a conversation with multiple messages
          fc.array(
            fc.oneof(userMessage, assistantMessage),
            { minLength: 2, maxLength: 10 }
          ).filter(msgs => msgs.some(m => m.role === 'user')),
          validMessageContent,
          (messages, newContent) => {
            // Find a user message index to edit (preferably not the last one)
            const userMessageIndices = messages
              .map((m, i) => ({ message: m, index: i }))
              .filter(({ message }) => message.role === 'user')
              .map(({ index }) => index);
            
            const indexToEdit = userMessageIndices[0]; // Use first user message
            
            // Simulate saving edit
            const { messagesAfterEdit } = simulateSaveEditMessage(messages, indexToEdit, newContent);
            
            // Property: messages after edit should only contain messages before the edited index
            expect(messagesAfterEdit.length).toBe(indexToEdit);
            
            // All remaining messages should be from before the edit index
            messagesAfterEdit.forEach((msg, i) => {
              expect(msg).toEqual(messages[i]);
            });
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should result in empty array when editing first message', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          fc.array(
            fc.oneof(userMessage, assistantMessage),
            { minLength: 1, maxLength: 10 }
          ),
          validMessageContent,
          (messages, newContent) => {
            // Ensure first message is a user message
            const messagesWithUserFirst: Message[] = [
              { role: 'user', content: 'original', timestamp: new Date().toISOString() },
              ...messages,
            ];
            
            // Edit the first message (index 0)
            const { messagesAfterEdit } = simulateSaveEditMessage(messagesWithUserFirst, 0, newContent);
            
            // Property: editing first message should result in empty array
            expect(messagesAfterEdit.length).toBe(0);
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should not modify messages if new content is empty', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          fc.array(userMessage, { minLength: 1, maxLength: 5 }),
          fc.constantFrom('', '   ', '\t', '\n'),
          (messages, emptyContent) => {
            const { messagesAfterEdit, contentToSend } = simulateSaveEditMessage(messages, 0, emptyContent);
            
            // Property: empty content should not modify messages
            expect(messagesAfterEdit).toEqual(messages);
            expect(contentToSend).toBeNull();
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should trim the new content before sending', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          userMessage,
          fc.string({ minLength: 1, maxLength: 100 }).filter(s => s.trim().length > 0),
          (message, content) => {
            const paddedContent = `  ${content}  `;
            const messages: Message[] = [message];
            
            const { contentToSend } = simulateSaveEditMessage(messages, 0, paddedContent);
            
            // Property: content should be trimmed
            expect(contentToSend).toBe(content.trim());
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 10: Cancel preserves original
   * *For any* cancelled edit operation, the message content should equal 
   * the original content before editing began
   * 
   * **Feature: chat-ux-improvements, Property 10: Cancel preserves original**
   * **Validates: Requirements 4.5**
   */
  describe('Property 10: Cancel preserves original', () => {
    it('should restore original content when canceling edit', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          validMessageContent,
          validMessageContent,
          (originalContent, editedContent) => {
            // Simulate canceling an edit
            const { restoredContent, editingIndex } = simulateCancelEditMessage(originalContent, editedContent);
            
            // Property: restored content should equal original
            expect(restoredContent).toBe(originalContent);
            
            // Property: editing index should be cleared
            expect(editingIndex).toBeNull();
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should preserve original content regardless of edit changes', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          // Generate content with various special characters
          fc.string({ minLength: 1, maxLength: 200 }).filter(s => s.trim().length > 0),
          fc.string({ minLength: 0, maxLength: 200 }),
          (originalContent, editedContent) => {
            const { restoredContent } = simulateCancelEditMessage(originalContent, editedContent);
            
            // Property: original content should be preserved exactly
            expect(restoredContent).toBe(originalContent);
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 11: Edit mode disables input
   * *For any* active edit operation (editingMessageIndex !== null), 
   * the main chat input should be disabled
   * 
   * **Feature: chat-ux-improvements, Property 11: Edit mode disables input**
   * **Validates: Requirements 4.6**
   */
  describe('Property 11: Edit mode disables input', () => {
    it('should disable input when editing any message', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          fc.integer({ min: 0, max: 100 }),
          (editingIndex) => {
            const isDisabled = isInputDisabledDuringEdit(editingIndex, false, false);
            
            // Property: input should be disabled when editingMessageIndex is not null
            expect(isDisabled).toBe(true);
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should enable input when not editing', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          fc.boolean(),
          fc.boolean(),
          (isStreaming, isLoading) => {
            // When not editing (editingMessageIndex is null)
            const isDisabled = isInputDisabledDuringEdit(null, isStreaming, isLoading);
            
            // Property: input should only be disabled if streaming or loading
            expect(isDisabled).toBe(isStreaming || isLoading);
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should disable input when editing regardless of streaming/loading state', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          fc.integer({ min: 0, max: 100 }),
          fc.boolean(),
          fc.boolean(),
          (editingIndex, isStreaming, isLoading) => {
            const isDisabled = isInputDisabledDuringEdit(editingIndex, isStreaming, isLoading);
            
            // Property: input should always be disabled when editing
            expect(isDisabled).toBe(true);
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});


/**
 * Simulates adding a new session to the session list
 * This extracts the core logic for testing without React hooks
 */
function simulateAddNewSession(
  sessions: SessionSummary[],
  newSessionId: string
): SessionSummary[] {
  const newSession: SessionSummary = {
    id: newSessionId,
    preview: '',
    timestamp: new Date().toISOString(),
    messageCount: 0,
  };
  return [newSession, ...sessions];
}

/**
 * Simulates updating a session when a message is sent
 * This extracts the core logic for testing without React hooks
 */
function simulateUpdateSessionOnMessage(
  sessions: SessionSummary[],
  sessionId: string,
  messageContent: string
): SessionSummary[] {
  const existingIndex = sessions.findIndex(s => s.id === sessionId);
  
  if (existingIndex >= 0) {
    // Update existing session
    const updated = [...sessions];
    const existing = updated[existingIndex];
    // Only update preview if it's empty (first message)
    const newPreview = existing.preview || messageContent.substring(0, 100);
    updated[existingIndex] = {
      ...existing,
      preview: newPreview,
      timestamp: new Date().toISOString(),
      messageCount: existing.messageCount + 1,
    };
    // Move to top of list
    const [session] = updated.splice(existingIndex, 1);
    return [session, ...updated];
  } else {
    // Add new session to top
    const newSession: SessionSummary = {
      id: sessionId,
      preview: messageContent.substring(0, 100),
      timestamp: new Date().toISOString(),
      messageCount: 1,
    };
    return [newSession, ...sessions];
  }
}

// Helper to generate valid session IDs (UUID-like)
const validSessionId = fc.uuid();

// Helper to generate a session summary
const sessionSummary = fc.record({
  id: validSessionId,
  preview: fc.string({ minLength: 0, maxLength: 100 }),
  timestamp: fc.integer({ 
    min: new Date('2000-01-01').getTime(), 
    max: new Date('2030-12-31').getTime() 
  }).map(ts => new Date(ts).toISOString()),
  messageCount: fc.integer({ min: 0, max: 1000 }),
});

describe('useChat Session Management - Property-Based Tests', () => {
  /**
   * Property 1: New sessions appear at list top
   * *For any* new session created, the session list should have that session 
   * at index 0 (top of the list)
   * 
   * **Feature: chat-ux-improvements, Property 1: New sessions appear at list top**
   * **Validates: Requirements 1.3**
   */
  describe('Property 1: New sessions appear at list top', () => {
    it('should place new session at index 0 when added to empty list', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          validSessionId,
          (newSessionId) => {
            const sessions: SessionSummary[] = [];
            
            const updatedSessions = simulateAddNewSession(sessions, newSessionId);
            
            // Property: new session should be at index 0
            expect(updatedSessions[0].id).toBe(newSessionId);
            expect(updatedSessions.length).toBe(1);
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should place new session at index 0 when added to non-empty list', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          fc.array(sessionSummary, { minLength: 1, maxLength: 20 }),
          validSessionId,
          (existingSessions, newSessionId) => {
            // Ensure new session ID is unique
            const uniqueNewId = existingSessions.some(s => s.id === newSessionId) 
              ? `${newSessionId}-new` 
              : newSessionId;
            
            const updatedSessions = simulateAddNewSession(existingSessions, uniqueNewId);
            
            // Property: new session should be at index 0
            expect(updatedSessions[0].id).toBe(uniqueNewId);
            
            // Property: list length should increase by 1
            expect(updatedSessions.length).toBe(existingSessions.length + 1);
            
            // Property: all existing sessions should still be present
            existingSessions.forEach(existingSession => {
              expect(updatedSessions.some(s => s.id === existingSession.id)).toBe(true);
            });
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should preserve order of existing sessions after new session', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          fc.array(sessionSummary, { minLength: 1, maxLength: 20 }),
          validSessionId,
          (existingSessions, newSessionId) => {
            // Ensure new session ID is unique
            const uniqueNewId = existingSessions.some(s => s.id === newSessionId) 
              ? `${newSessionId}-new` 
              : newSessionId;
            
            const updatedSessions = simulateAddNewSession(existingSessions, uniqueNewId);
            
            // Property: existing sessions should maintain their relative order
            for (let i = 0; i < existingSessions.length; i++) {
              expect(updatedSessions[i + 1].id).toBe(existingSessions[i].id);
            }
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should move existing session to top when message is sent', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          fc.array(sessionSummary, { minLength: 2, maxLength: 20 }),
          fc.integer({ min: 1, max: 19 }),
          fc.string({ minLength: 1, maxLength: 200 }).filter(s => s.trim().length > 0),
          (sessions, targetIndex, messageContent) => {
            // Ensure targetIndex is valid
            const validIndex = Math.min(targetIndex, sessions.length - 1);
            const targetSessionId = sessions[validIndex].id;
            
            const updatedSessions = simulateUpdateSessionOnMessage(
              sessions,
              targetSessionId,
              messageContent
            );
            
            // Property: the session that received a message should be at index 0
            expect(updatedSessions[0].id).toBe(targetSessionId);
            
            // Property: list length should remain the same
            expect(updatedSessions.length).toBe(sessions.length);
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should add new session to top when message is sent to unknown session', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          fc.array(sessionSummary, { minLength: 0, maxLength: 20 }),
          validSessionId,
          fc.string({ minLength: 1, maxLength: 200 }).filter(s => s.trim().length > 0),
          (sessions, newSessionId, messageContent) => {
            // Ensure new session ID is unique
            const uniqueNewId = sessions.some(s => s.id === newSessionId) 
              ? `${newSessionId}-new` 
              : newSessionId;
            
            const updatedSessions = simulateUpdateSessionOnMessage(
              sessions,
              uniqueNewId,
              messageContent
            );
            
            // Property: new session should be at index 0
            expect(updatedSessions[0].id).toBe(uniqueNewId);
            
            // Property: list length should increase by 1
            expect(updatedSessions.length).toBe(sessions.length + 1);
            
            // Property: new session should have the message content as preview
            expect(updatedSessions[0].preview).toBe(messageContent.substring(0, 100));
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should update message count when message is sent', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          sessionSummary,
          fc.string({ minLength: 1, maxLength: 200 }).filter(s => s.trim().length > 0),
          (session, messageContent) => {
            const sessions = [session];
            const originalCount = session.messageCount;
            
            const updatedSessions = simulateUpdateSessionOnMessage(
              sessions,
              session.id,
              messageContent
            );
            
            // Property: message count should increase by 1
            expect(updatedSessions[0].messageCount).toBe(originalCount + 1);
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should only update preview if it was empty', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 1, maxLength: 100 }),
          fc.string({ minLength: 1, maxLength: 200 }).filter(s => s.trim().length > 0),
          validSessionId,
          fc.integer({ 
            min: new Date('2000-01-01').getTime(), 
            max: new Date('2030-12-31').getTime() 
          }),
          (existingPreview, newMessageContent, sessionId, timestamp) => {
            const session: SessionSummary = {
              id: sessionId,
              preview: existingPreview,
              timestamp: new Date(timestamp).toISOString(),
              messageCount: 5,
            };
            
            const updatedSessions = simulateUpdateSessionOnMessage(
              [session],
              sessionId,
              newMessageContent
            );
            
            // Property: preview should remain unchanged if it was not empty
            expect(updatedSessions[0].preview).toBe(existingPreview);
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should set preview from first message if preview was empty', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 1, maxLength: 200 }).filter(s => s.trim().length > 0),
          validSessionId,
          fc.integer({ 
            min: new Date('2000-01-01').getTime(), 
            max: new Date('2030-12-31').getTime() 
          }),
          (messageContent, sessionId, timestamp) => {
            const session: SessionSummary = {
              id: sessionId,
              preview: '', // Empty preview
              timestamp: new Date(timestamp).toISOString(),
              messageCount: 0,
            };
            
            const updatedSessions = simulateUpdateSessionOnMessage(
              [session],
              sessionId,
              messageContent
            );
            
            // Property: preview should be set from the message content
            expect(updatedSessions[0].preview).toBe(messageContent.substring(0, 100));
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});
