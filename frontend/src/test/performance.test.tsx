/**
 * Performance tests for the React frontend.
 * 
 * Tests long conversations, rapid message sending, and memory usage.
 * Requirements: 7.5
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useChat } from '../hooks/useChat';

describe('Frontend Performance Tests', () => {
  beforeEach(() => {
    // Mock fetch for all tests
    global.fetch = vi.fn();
    
    // Mock EventSource
    global.EventSource = vi.fn().mockImplementation(() => ({
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      close: vi.fn(),
      onerror: null,
      onmessage: null,
      onopen: null,
      readyState: 0,
      url: '',
      withCredentials: false,
      CONNECTING: 0,
      OPEN: 1,
      CLOSED: 2,
      dispatchEvent: vi.fn(),
    })) as any;
  });

  it('handles long conversation (100+ messages) efficiently', async () => {
    // Mock session creation
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ session_id: 'test-session' }),
    });

    const { result } = renderHook(() => useChat());

    // Wait for session initialization
    await waitFor(() => {
      expect(result.current.sessionId).toBe('test-session');
    });

    const startTime = performance.now();

    // Simulate adding 100 messages
    await act(async () => {
      for (let i = 0; i < 100; i++) {
        // Mock streaming response
        const mockEventSource = {
          addEventListener: vi.fn((event, handler) => {
            if (event === 'message') {
              // Simulate streaming tokens
              setTimeout(() => {
                handler({ data: JSON.stringify({ type: 'token', content: 'Response ' }) });
                handler({ data: JSON.stringify({ type: 'token', content: `${i}` }) });
                handler({ data: JSON.stringify({ type: 'done' }) });
              }, 0);
            }
          }),
          close: vi.fn(),
          onerror: null,
          onmessage: null,
        };

        (global.EventSource as any).mockImplementationOnce(() => mockEventSource);

        await result.current.sendMessage(`Message ${i}`);
        
        // Small delay to allow state updates
        await new Promise(resolve => setTimeout(resolve, 10));
      }
    });

    const endTime = performance.now();
    const totalTime = endTime - startTime;

    // Verify all messages are in state
    expect(result.current.messages.length).toBe(200); // 100 user + 100 assistant

    // Performance assertion - should complete in reasonable time
    // Allow 10 seconds for 100 message exchanges in test environment
    expect(totalTime).toBeLessThan(10000);

    console.log(`\nLong conversation performance:`);
    console.log(`  Total messages: ${result.current.messages.length}`);
    console.log(`  Total time: ${totalTime.toFixed(2)}ms`);
    console.log(`  Average per message: ${(totalTime / 100).toFixed(2)}ms`);
  });

  it('handles rapid message sending without blocking', async () => {
    // Mock session creation
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ session_id: 'test-session' }),
    });

    const { result } = renderHook(() => useChat());

    await waitFor(() => {
      expect(result.current.sessionId).toBe('test-session');
    });

    const startTime = performance.now();

    // Send 20 messages rapidly without waiting
    await act(async () => {
      const promises = [];
      
      for (let i = 0; i < 20; i++) {
        const mockEventSource = {
          addEventListener: vi.fn((event, handler) => {
            if (event === 'message') {
              setTimeout(() => {
                handler({ data: JSON.stringify({ type: 'token', content: `Rapid ${i}` }) });
                handler({ data: JSON.stringify({ type: 'done' }) });
              }, 0);
            }
          }),
          close: vi.fn(),
          onerror: null,
          onmessage: null,
        };

        (global.EventSource as any).mockImplementationOnce(() => mockEventSource);

        promises.push(result.current.sendMessage(`Rapid message ${i}`));
      }

      await Promise.all(promises);
    });

    const endTime = performance.now();
    const totalTime = endTime - startTime;

    // Verify all messages are present
    expect(result.current.messages.length).toBe(40); // 20 user + 20 assistant

    console.log(`\nRapid message sending performance:`);
    console.log(`  Messages sent: 20`);
    console.log(`  Total time: ${totalTime.toFixed(2)}ms`);
    console.log(`  Messages per second: ${(20000 / totalTime).toFixed(2)}`);
  });

  it('does not leak memory with repeated clear operations', async () => {
    // Mock session creation
    let sessionCount = 0;
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/sessions') && !url.includes('messages')) {
        sessionCount++;
        return Promise.resolve({
          ok: true,
          json: async () => ({ session_id: `session-${sessionCount}` }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({}),
      });
    });

    const { result } = renderHook(() => useChat());

    await waitFor(() => {
      expect(result.current.sessionId).toBeTruthy();
    });

    // Perform 10 cycles of: add messages -> clear -> add messages
    for (let cycle = 0; cycle < 10; cycle++) {
      await act(async () => {
        // Add 10 messages
        for (let i = 0; i < 10; i++) {
          const mockEventSource = {
            addEventListener: vi.fn((event, handler) => {
              if (event === 'message') {
                setTimeout(() => {
                  handler({ data: JSON.stringify({ type: 'token', content: `Msg ${i}` }) });
                  handler({ data: JSON.stringify({ type: 'done' }) });
                }, 0);
              }
            }),
            close: vi.fn(),
            onerror: null,
            onmessage: null,
          };

          (global.EventSource as any).mockImplementationOnce(() => mockEventSource);
          await result.current.sendMessage(`Cycle ${cycle} Message ${i}`);
        }

        // Clear session
        await result.current.clearSession();
      });

      // After clearing, messages should be empty
      expect(result.current.messages.length).toBe(0);
    }

    // After 10 cycles, verify we have a new session and no messages
    expect(result.current.messages.length).toBe(0);
    expect(result.current.sessionId).toBeTruthy();
    
    // Session count should be 11 (initial + 10 clears)
    expect(sessionCount).toBe(11);

    console.log(`\nMemory leak test:`);
    console.log(`  Cycles completed: 10`);
    console.log(`  Final message count: ${result.current.messages.length}`);
    console.log(`  Sessions created: ${sessionCount}`);
  });

  it('maintains performance with streaming updates', async () => {
    // Mock session creation
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ session_id: 'test-session' }),
    });

    const { result } = renderHook(() => useChat());

    await waitFor(() => {
      expect(result.current.sessionId).toBe('test-session');
    });

    const startTime = performance.now();

    // Simulate a message with many streaming tokens
    await act(async () => {
      const mockEventSource = {
        addEventListener: vi.fn((event, handler) => {
          if (event === 'message') {
            // Simulate 100 token updates
            setTimeout(() => {
              for (let i = 0; i < 100; i++) {
                handler({ data: JSON.stringify({ type: 'token', content: `Token ${i} ` }) });
              }
              handler({ data: JSON.stringify({ type: 'done' }) });
            }, 0);
          }
        }),
        close: vi.fn(),
        onerror: null,
        onmessage: null,
      };

      (global.EventSource as any).mockImplementationOnce(() => mockEventSource);

      await result.current.sendMessage('Test streaming');
    });

    const endTime = performance.now();
    const totalTime = endTime - startTime;

    // Verify message was assembled correctly
    expect(result.current.messages.length).toBe(2); // user + assistant
    expect(result.current.messages[1].content).toContain('Token');

    // Should handle 100 token updates quickly
    expect(totalTime).toBeLessThan(1000);

    console.log(`\nStreaming performance:`);
    console.log(`  Tokens streamed: 100`);
    console.log(`  Total time: ${totalTime.toFixed(2)}ms`);
    console.log(`  Time per token: ${(totalTime / 100).toFixed(2)}ms`);
  });

  it('handles concurrent operations without race conditions', async () => {
    // Mock session creation
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ session_id: 'test-session' }),
    });

    const { result } = renderHook(() => useChat());

    await waitFor(() => {
      expect(result.current.sessionId).toBe('test-session');
    });

    // Try to trigger race conditions by rapid operations
    await act(async () => {
      const operations = [];

      // Send 5 messages concurrently
      for (let i = 0; i < 5; i++) {
        const mockEventSource = {
          addEventListener: vi.fn((event, handler) => {
            if (event === 'message') {
              setTimeout(() => {
                handler({ data: JSON.stringify({ type: 'token', content: `Concurrent ${i}` }) });
                handler({ data: JSON.stringify({ type: 'done' }) });
              }, Math.random() * 50); // Random delay to simulate real conditions
            }
          }),
          close: vi.fn(),
          onerror: null,
          onmessage: null,
        };

        (global.EventSource as any).mockImplementationOnce(() => mockEventSource);
        operations.push(result.current.sendMessage(`Concurrent ${i}`));
      }

      await Promise.all(operations);
    });

    // All messages should be present without duplicates
    expect(result.current.messages.length).toBe(10); // 5 user + 5 assistant

    // Verify no duplicate messages
    const userMessages = result.current.messages.filter(m => m.role === 'user');
    const uniqueUserMessages = new Set(userMessages.map(m => m.content));
    expect(uniqueUserMessages.size).toBe(5);

    console.log(`\nConcurrent operations test:`);
    console.log(`  Concurrent messages: 5`);
    console.log(`  Total messages: ${result.current.messages.length}`);
    console.log(`  Unique user messages: ${uniqueUserMessages.size}`);
  });
});
