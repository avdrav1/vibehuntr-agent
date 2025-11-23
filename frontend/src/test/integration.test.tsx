/**
 * Integration tests for React + FastAPI migration
 * 
 * These tests verify the full message flow, streaming, and session management
 * from the frontend perspective.
 * 
 * Requirements: 12.3, 12.5
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '../App';
import * as api from '../services/api';

// Mock the API module
vi.mock('../services/api');

describe('Frontend Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Default mock implementations
    vi.mocked(api.createSession).mockResolvedValue('test-session-id');
    vi.mocked(api.getSessionMessages).mockResolvedValue([]);
    vi.mocked(api.clearSession).mockResolvedValue(undefined);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Full Message Flow (Requirement 12.3)', () => {
    it('completes full message flow: send message, receive response, display in UI', async () => {
      const user = userEvent.setup();
      
      // Mock streaming connection
      let messageHandler: ((event: MessageEvent) => void) | null = null;
      const mockEventSource = {
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        close: vi.fn(),
        onmessage: null,
        onerror: null,
        onopen: null,
        readyState: 1,
        url: '',
        withCredentials: false,
        CONNECTING: 0,
        OPEN: 1,
        CLOSED: 2,
        dispatchEvent: vi.fn(),
      } as unknown as EventSource;

      Object.defineProperty(mockEventSource, 'onmessage', {
        set: (handler) => {
          messageHandler = handler;
        },
        get: () => messageHandler,
      });

      vi.mocked(api.createStreamingConnection).mockReturnValue(mockEventSource);

      // Render the App component
      render(<App />);

      // Wait for session to be created
      await waitFor(() => {
        expect(api.createSession).toHaveBeenCalled();
      });

      // Type a message
      const input = screen.getByLabelText('Message input');
      await user.type(input, 'Hello, agent!');

      // Send the message
      const sendButton = screen.getByLabelText('Send message');
      await user.click(sendButton);

      // Verify user message appears
      await waitFor(() => {
        expect(screen.getByText('Hello, agent!')).toBeInTheDocument();
      });

      // Simulate streaming response
      await waitFor(() => {
        messageHandler?.({ 
          data: JSON.stringify({ type: 'token', content: 'Hello' }) 
        } as MessageEvent);
      });

      await waitFor(() => {
        messageHandler?.({ 
          data: JSON.stringify({ type: 'token', content: ' there!' }) 
        } as MessageEvent);
      });

      await waitFor(() => {
        messageHandler?.({ 
          data: JSON.stringify({ type: 'done' }) 
        } as MessageEvent);
      });

      // Verify assistant response appears
      await waitFor(() => {
        expect(screen.getByText(/Hello there!/)).toBeInTheDocument();
      });

      // Verify no duplicate messages
      const userMessages = screen.getAllByText('Hello, agent!');
      expect(userMessages).toHaveLength(1);
    });

    it('handles multiple messages in sequence', async () => {
      const user = userEvent.setup();
      
      let messageHandler: ((event: MessageEvent) => void) | null = null;
      const mockEventSource = {
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        close: vi.fn(),
        onmessage: null,
        onerror: null,
        onopen: null,
        readyState: 1,
        url: '',
        withCredentials: false,
        CONNECTING: 0,
        OPEN: 1,
        CLOSED: 2,
        dispatchEvent: vi.fn(),
      } as unknown as EventSource;

      Object.defineProperty(mockEventSource, 'onmessage', {
        set: (handler) => {
          messageHandler = handler;
        },
        get: () => messageHandler,
      });

      vi.mocked(api.createStreamingConnection).mockReturnValue(mockEventSource);

      render(<App />);

      await waitFor(() => {
        expect(api.createSession).toHaveBeenCalled();
      });

      // Send first message
      const input = screen.getByLabelText('Message input');
      await user.type(input, 'First message');
      await user.click(screen.getByLabelText('Send message'));

      await waitFor(() => {
        messageHandler?.({ 
          data: JSON.stringify({ type: 'token', content: 'First response' }) 
        } as MessageEvent);
      });

      await waitFor(() => {
        messageHandler?.({ 
          data: JSON.stringify({ type: 'done' }) 
        } as MessageEvent);
      });

      // Send second message
      await user.type(input, 'Second message');
      await user.click(screen.getByLabelText('Send message'));

      await waitFor(() => {
        messageHandler?.({ 
          data: JSON.stringify({ type: 'token', content: 'Second response' }) 
        } as MessageEvent);
      });

      await waitFor(() => {
        messageHandler?.({ 
          data: JSON.stringify({ type: 'done' }) 
        } as MessageEvent);
      });

      // Verify both exchanges are visible
      expect(screen.getByText('First message')).toBeInTheDocument();
      expect(screen.getByText(/First response/)).toBeInTheDocument();
      expect(screen.getByText('Second message')).toBeInTheDocument();
      expect(screen.getByText(/Second response/)).toBeInTheDocument();
    });
  });


  describe('Streaming End-to-End (Requirement 12.3, 12.5)', () => {
    it('displays tokens as they arrive during streaming', async () => {
      const user = userEvent.setup();
      
      let messageHandler: ((event: MessageEvent) => void) | null = null;
      const mockEventSource = {
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        close: vi.fn(),
        onmessage: null,
        onerror: null,
        onopen: null,
        readyState: 1,
        url: '',
        withCredentials: false,
        CONNECTING: 0,
        OPEN: 1,
        CLOSED: 2,
        dispatchEvent: vi.fn(),
      } as unknown as EventSource;

      Object.defineProperty(mockEventSource, 'onmessage', {
        set: (handler) => {
          messageHandler = handler;
        },
        get: () => messageHandler,
      });

      vi.mocked(api.createStreamingConnection).mockReturnValue(mockEventSource);

      render(<App />);

      await waitFor(() => {
        expect(api.createSession).toHaveBeenCalled();
      });

      // Send message
      const input = screen.getByLabelText('Message input');
      await user.type(input, 'Test streaming');
      await user.click(screen.getByLabelText('Send message'));

      // Send tokens one by one
      await waitFor(() => {
        messageHandler?.({ 
          data: JSON.stringify({ type: 'token', content: 'This ' }) 
        } as MessageEvent);
      });

      // Verify first token appears
      await waitFor(() => {
        expect(screen.getByText(/This/)).toBeInTheDocument();
      });

      await waitFor(() => {
        messageHandler?.({ 
          data: JSON.stringify({ type: 'token', content: 'is ' }) 
        } as MessageEvent);
      });

      // Verify accumulated tokens
      await waitFor(() => {
        expect(screen.getByText(/This is/)).toBeInTheDocument();
      });

      await waitFor(() => {
        messageHandler?.({ 
          data: JSON.stringify({ type: 'token', content: 'streaming!' }) 
        } as MessageEvent);
      });

      await waitFor(() => {
        messageHandler?.({ 
          data: JSON.stringify({ type: 'done' }) 
        } as MessageEvent);
      });

      // Verify complete message
      await waitFor(() => {
        expect(screen.getByText(/This is streaming!/)).toBeInTheDocument();
      });
    });

    it('shows loading indicator during streaming', async () => {
      const user = userEvent.setup();
      
      let messageHandler: ((event: MessageEvent) => void) | null = null;
      const mockEventSource = {
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        close: vi.fn(),
        onmessage: null,
        onerror: null,
        onopen: null,
        readyState: 1,
        url: '',
        withCredentials: false,
        CONNECTING: 0,
        OPEN: 1,
        CLOSED: 2,
        dispatchEvent: vi.fn(),
      } as unknown as EventSource;

      Object.defineProperty(mockEventSource, 'onmessage', {
        set: (handler) => {
          messageHandler = handler;
        },
        get: () => messageHandler,
      });

      vi.mocked(api.createStreamingConnection).mockReturnValue(mockEventSource);

      render(<App />);

      await waitFor(() => {
        expect(api.createSession).toHaveBeenCalled();
      });

      // Send message
      const input = screen.getByLabelText('Message input');
      await user.type(input, 'Test');
      await user.click(screen.getByLabelText('Send message'));

      // Input should be disabled during loading
      await waitFor(() => {
        expect(input).toBeDisabled();
      });

      // Send first token to end loading state
      await waitFor(() => {
        messageHandler?.({ 
          data: JSON.stringify({ type: 'token', content: 'Response' }) 
        } as MessageEvent);
      });

      // Complete streaming
      await waitFor(() => {
        messageHandler?.({ 
          data: JSON.stringify({ type: 'done' }) 
        } as MessageEvent);
      });

      // Input should be enabled again
      await waitFor(() => {
        expect(input).not.toBeDisabled();
      });
    });

    it('handles streaming errors gracefully', async () => {
      const user = userEvent.setup();
      
      let messageHandler: ((event: MessageEvent) => void) | null = null;
      const mockEventSource = {
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        close: vi.fn(),
        onmessage: null,
        onerror: null,
        onopen: null,
        readyState: 1,
        url: '',
        withCredentials: false,
        CONNECTING: 0,
        OPEN: 1,
        CLOSED: 2,
        dispatchEvent: vi.fn(),
      } as unknown as EventSource;

      Object.defineProperty(mockEventSource, 'onmessage', {
        set: (handler) => {
          messageHandler = handler;
        },
        get: () => messageHandler,
      });

      vi.mocked(api.createStreamingConnection).mockReturnValue(mockEventSource);

      render(<App />);

      await waitFor(() => {
        expect(api.createSession).toHaveBeenCalled();
      });

      // Send message
      const input = screen.getByLabelText('Message input');
      await user.type(input, 'Test');
      await user.click(screen.getByLabelText('Send message'));

      // Simulate error
      await waitFor(() => {
        messageHandler?.({ 
          data: JSON.stringify({ type: 'error', message: 'Streaming failed' }) 
        } as MessageEvent);
      });

      // Error should be displayed
      await waitFor(() => {
        expect(screen.getByText(/Streaming failed/)).toBeInTheDocument();
      });
    });
  });


  describe('Session Management (Requirement 12.3, 12.5)', () => {
    it('creates session on mount', async () => {
      render(<App />);

      await waitFor(() => {
        expect(api.createSession).toHaveBeenCalledTimes(1);
      });
    });

    it('clears session and creates new one when "New Conversation" is clicked', async () => {
      const user = userEvent.setup();
      
      vi.mocked(api.createSession)
        .mockResolvedValueOnce('session-1')
        .mockResolvedValueOnce('session-2');

      let messageHandler: ((event: MessageEvent) => void) | null = null;
      const mockEventSource = {
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        close: vi.fn(),
        onmessage: null,
        onerror: null,
        onopen: null,
        readyState: 1,
        url: '',
        withCredentials: false,
        CONNECTING: 0,
        OPEN: 1,
        CLOSED: 2,
        dispatchEvent: vi.fn(),
      } as unknown as EventSource;

      Object.defineProperty(mockEventSource, 'onmessage', {
        set: (handler) => {
          messageHandler = handler;
        },
        get: () => messageHandler,
      });

      vi.mocked(api.createStreamingConnection).mockReturnValue(mockEventSource);

      render(<App />);

      await waitFor(() => {
        expect(api.createSession).toHaveBeenCalledTimes(1);
      });

      // Send a message
      const input = screen.getByLabelText('Message input');
      await user.type(input, 'Test message');
      await user.click(screen.getByLabelText('Send message'));

      await waitFor(() => {
        messageHandler?.({ 
          data: JSON.stringify({ type: 'token', content: 'Response' }) 
        } as MessageEvent);
      });

      await waitFor(() => {
        messageHandler?.({ 
          data: JSON.stringify({ type: 'done' }) 
        } as MessageEvent);
      });

      // Verify message is displayed
      expect(screen.getByText('Test message')).toBeInTheDocument();

      // Click "New Conversation"
      const newConversationButton = screen.getByText('New Conversation');
      await user.click(newConversationButton);

      // Verify clearSession was called
      await waitFor(() => {
        expect(api.clearSession).toHaveBeenCalledWith('session-1');
      });

      // Verify new session was created
      await waitFor(() => {
        expect(api.createSession).toHaveBeenCalledTimes(2);
      });

      // Verify messages were cleared
      await waitFor(() => {
        expect(screen.queryByText('Test message')).not.toBeInTheDocument();
      });
    });

    it('loads existing messages when session has history', async () => {
      const existingMessages = [
        { role: 'user' as const, content: 'Previous message', timestamp: '2024-01-01T10:00:00Z' },
        { role: 'assistant' as const, content: 'Previous response', timestamp: '2024-01-01T10:00:01Z' },
      ];

      vi.mocked(api.getSessionMessages).mockResolvedValue(existingMessages);

      render(<App />);

      // Wait for messages to load
      await waitFor(() => {
        expect(screen.getByText('Previous message')).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText('Previous response')).toBeInTheDocument();
      });
    });

    it('maintains conversation context across multiple messages', async () => {
      const user = userEvent.setup();
      
      let messageHandler: ((event: MessageEvent) => void) | null = null;
      const mockEventSource = {
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        close: vi.fn(),
        onmessage: null,
        onerror: null,
        onopen: null,
        readyState: 1,
        url: '',
        withCredentials: false,
        CONNECTING: 0,
        OPEN: 1,
        CLOSED: 2,
        dispatchEvent: vi.fn(),
      } as unknown as EventSource;

      Object.defineProperty(mockEventSource, 'onmessage', {
        set: (handler) => {
          messageHandler = handler;
        },
        get: () => messageHandler,
      });

      vi.mocked(api.createStreamingConnection).mockReturnValue(mockEventSource);

      render(<App />);

      await waitFor(() => {
        expect(api.createSession).toHaveBeenCalled();
      });

      const input = screen.getByLabelText('Message input');

      // Send multiple messages
      const messages = ['Message 1', 'Message 2', 'Message 3'];

      for (const msg of messages) {
        await user.type(input, msg);
        await user.click(screen.getByLabelText('Send message'));

        await waitFor(() => {
          messageHandler?.({ 
            data: JSON.stringify({ type: 'token', content: `Response to ${msg}` }) 
          } as MessageEvent);
        });

        await waitFor(() => {
          messageHandler?.({ 
            data: JSON.stringify({ type: 'done' }) 
          } as MessageEvent);
        });
      }

      // Verify all messages are displayed
      for (const msg of messages) {
        expect(screen.getByText(msg)).toBeInTheDocument();
        expect(screen.getByText(`Response to ${msg}`)).toBeInTheDocument();
      }

      // Verify messages are in order
      const allMessages = screen.getAllByText(/Message \d|Response to Message \d/);
      expect(allMessages.length).toBe(6); // 3 user + 3 assistant
    });
  });

  describe('Error Handling Integration (Requirement 12.3)', () => {
    it('displays error when session creation fails', async () => {
      vi.mocked(api.createSession).mockRejectedValue(new Error('Network error'));

      render(<App />);

      await waitFor(() => {
        expect(screen.getByText(/Network error/)).toBeInTheDocument();
      });
    });

    it('allows retry after error', async () => {
      const user = userEvent.setup();
      
      let messageHandler: ((event: MessageEvent) => void) | null = null;
      const mockEventSource = {
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        close: vi.fn(),
        onmessage: null,
        onerror: null,
        onopen: null,
        readyState: 1,
        url: '',
        withCredentials: false,
        CONNECTING: 0,
        OPEN: 1,
        CLOSED: 2,
        dispatchEvent: vi.fn(),
      } as unknown as EventSource;

      Object.defineProperty(mockEventSource, 'onmessage', {
        set: (handler) => {
          messageHandler = handler;
        },
        get: () => messageHandler,
      });

      vi.mocked(api.createStreamingConnection).mockReturnValue(mockEventSource);

      render(<App />);

      await waitFor(() => {
        expect(api.createSession).toHaveBeenCalled();
      });

      // Send message
      const input = screen.getByLabelText('Message input');
      await user.type(input, 'Test');
      await user.click(screen.getByLabelText('Send message'));

      // Simulate error
      await waitFor(() => {
        messageHandler?.({ 
          data: JSON.stringify({ type: 'error', message: 'Agent failed' }) 
        } as MessageEvent);
      });

      // Error should be displayed
      await waitFor(() => {
        expect(screen.getByText(/Agent failed/)).toBeInTheDocument();
      });

      // Dismiss error
      const dismissButton = screen.getByText('Dismiss');
      await user.click(dismissButton);

      // Error should be gone
      await waitFor(() => {
        expect(screen.queryByText(/Agent failed/)).not.toBeInTheDocument();
      });

      // Should be able to send another message
      await user.type(input, 'Retry');
      await user.click(screen.getByLabelText('Send message'));

      await waitFor(() => {
        messageHandler?.({ 
          data: JSON.stringify({ type: 'token', content: 'Success' }) 
        } as MessageEvent);
      });

      await waitFor(() => {
        messageHandler?.({ 
          data: JSON.stringify({ type: 'done' }) 
        } as MessageEvent);
      });

      expect(screen.getByText(/Success/)).toBeInTheDocument();
    });
  });
});
