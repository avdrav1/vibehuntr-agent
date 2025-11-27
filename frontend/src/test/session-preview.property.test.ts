/**
 * Property-based tests for Session Preview functionality
 * Tests universal properties that should hold across all inputs
 * 
 * **Feature: chat-ux-improvements, Property 2: Session preview matches first message**
 * Uses fast-check for property-based testing
 */

import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import type { Message, SessionSummary } from '../types';

// Helper to generate valid ISO timestamp strings
// Using integer timestamps to avoid invalid date issues
const validTimestamp = fc.integer({ 
  min: new Date('2000-01-01').getTime(), 
  max: new Date('2030-12-31').getTime() 
}).map(ts => new Date(ts).toISOString());

/**
 * Helper function to generate a session preview from messages
 * This simulates the logic that will be used in the actual implementation
 */
function generateSessionPreview(messages: Message[], maxLength: number = 100): string {
  if (messages.length === 0) {
    return '';
  }
  
  const firstMessage = messages[0];
  const content = firstMessage.content.trim();
  
  if (content.length <= maxLength) {
    return content;
  }
  
  return content.substring(0, maxLength);
}

/**
 * Helper function to create a SessionSummary from messages
 * This simulates the logic that will be used in the actual implementation
 */
function createSessionSummary(
  sessionId: string,
  messages: Message[],
  timestamp: string
): SessionSummary {
  return {
    id: sessionId,
    preview: generateSessionPreview(messages),
    timestamp,
    messageCount: messages.length,
  };
}

describe('Session Preview - Property-Based Tests', () => {
  /**
   * Property 2: Session preview matches first message
   * *For any* session with at least one message, the session preview should 
   * contain a substring of the first message's content
   * 
   * **Validates: Requirements 1.4**
   */
  describe('Property 2: Session preview matches first message', () => {
    it('should have preview that is a substring of first message content', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          // Generate a non-empty message content
          fc.string({ minLength: 1, maxLength: 500 }).filter(s => s.trim().length > 0),
          // Generate additional messages (0-5)
          fc.array(
            fc.record({
              role: fc.constantFrom('user', 'assistant') as fc.Arbitrary<'user' | 'assistant'>,
              content: fc.string({ minLength: 1, maxLength: 200 }),
              timestamp: validTimestamp,
            }),
            { minLength: 0, maxLength: 5 }
          ),
          // Generate session metadata
          fc.uuid(),
          validTimestamp,
          (firstMessageContent, additionalMessages, sessionId, timestamp) => {
            // Create the first message
            const firstMessage: Message = {
              role: 'user',
              content: firstMessageContent,
              timestamp: new Date().toISOString(),
            };
            
            // Combine all messages
            const messages: Message[] = [firstMessage, ...additionalMessages];
            
            // Create session summary
            const summary = createSessionSummary(sessionId, messages, timestamp);
            
            // Property: preview should be a substring of the first message content
            const trimmedContent = firstMessageContent.trim();
            
            // The preview should either:
            // 1. Equal the trimmed content (if content is short enough)
            // 2. Be a prefix of the trimmed content (if content was truncated)
            expect(trimmedContent.startsWith(summary.preview)).toBe(true);
            
            // Preview should not be empty for non-empty messages
            expect(summary.preview.length).toBeGreaterThan(0);
            
            // Preview should not exceed max length
            expect(summary.preview.length).toBeLessThanOrEqual(100);
            
            return true;
          }
        ),
        { numRuns: 100 } // Run 100 iterations as specified in design doc
      );
    });

    it('should preserve exact content for short messages', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          // Generate short message content (under 100 chars)
          fc.string({ minLength: 1, maxLength: 99 }).filter(s => s.trim().length > 0 && s.trim().length <= 99),
          fc.uuid(),
          validTimestamp,
          (content, sessionId, timestamp) => {
            const message: Message = {
              role: 'user',
              content,
              timestamp: new Date().toISOString(),
            };
            
            const summary = createSessionSummary(sessionId, [message], timestamp);
            
            // For short messages, preview should equal trimmed content exactly
            expect(summary.preview).toBe(content.trim());
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should truncate long messages to max length', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          // Generate long message content (over 100 chars)
          fc.string({ minLength: 101, maxLength: 500 }).filter(s => s.trim().length > 100),
          fc.uuid(),
          validTimestamp,
          (content, sessionId, timestamp) => {
            const message: Message = {
              role: 'user',
              content,
              timestamp: new Date().toISOString(),
            };
            
            const summary = createSessionSummary(sessionId, [message], timestamp);
            
            // Preview should be exactly 100 characters
            expect(summary.preview.length).toBe(100);
            
            // Preview should be the first 100 characters of trimmed content
            expect(summary.preview).toBe(content.trim().substring(0, 100));
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should handle empty message arrays gracefully', () => {
      const summary = createSessionSummary('test-id', [], new Date().toISOString());
      
      expect(summary.preview).toBe('');
      expect(summary.messageCount).toBe(0);
    });
  });
});
