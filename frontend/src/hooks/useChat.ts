/**
 * useChat Hook
 * 
 * Custom React hook for managing chat state and interactions.
 * Handles message state, session management, and SSE streaming.
 * 
 * Requirements: 1.4, 3.1, 3.5
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import type { Message, StreamEvent, ConversationContext } from '../types';
import {
  createSession,
  createStreamingConnection,
  clearSession as clearSessionAPI,
  getSessionMessages,
  fetchContext,
} from '../services/api';

export interface UseChatReturn {
  messages: Message[];
  sessionId: string;
  isStreaming: boolean;
  isLoading: boolean;
  isConnected: boolean;
  error: string | null;
  context: ConversationContext | null;
  contextRefreshTrigger: number;
  sendMessage: (content: string) => Promise<void>;
  clearSession: () => Promise<void>;
  retryLastMessage: () => Promise<void>;
  dismissError: () => void;
}

/**
 * Custom hook for chat functionality
 * 
 * Manages:
 * - Message state (Requirement 1.4)
 * - Session ID state (Requirement 3.1)
 * - Streaming state
 * - SSE connection for real-time streaming
 * 
 * @returns Chat state and control functions
 */
export function useChat(): UseChatReturn {
  // State management (Requirement 1.4)
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false); // Requirement 7.5: Loading state
  const [isConnected, setIsConnected] = useState<boolean>(true); // Requirement 7.5: Connection status
  const [error, setError] = useState<string | null>(null);
  const [context, setContext] = useState<ConversationContext | null>(null); // Requirement 11.4: Context state
  const [contextRefreshTrigger, setContextRefreshTrigger] = useState<number>(0); // Requirement 11.4: Trigger context refresh

  // Ref to track the current EventSource connection
  const eventSourceRef = useRef<EventSource | null>(null);
  
  // Ref to track the last user message for retry functionality (Requirement 8.5)
  const lastUserMessageRef = useRef<string | null>(null);

  /**
   * Fetch and update context for the current session (Requirement 11.4)
   */
  const updateContext = useCallback(async (currentSessionId: string) => {
    if (!currentSessionId) return;
    
    try {
      const contextData = await fetchContext(currentSessionId);
      setContext(contextData);
    } catch (err) {
      // Don't show error to user for context fetch failures
      // Context is supplementary information
      console.error('Failed to fetch context:', err);
      setContext(null);
    }
  }, []);

  /**
   * Initialize session on mount (Requirement 3.1)
   */
  useEffect(() => {
    const initializeSession = async () => {
      try {
        const newSessionId = await createSession();
        setSessionId(newSessionId);
        
        // Load existing messages if any
        try {
          const existingMessages = await getSessionMessages(newSessionId);
          if (existingMessages.length > 0) {
            setMessages(existingMessages);
          }
        } catch {
          // If no messages exist, that's fine - start with empty array
          console.log('No existing messages for session');
        }
        
        // Fetch initial context for the session (Requirement 11.4)
        await updateContext(newSessionId);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to initialize session';
        setError(errorMessage);
        console.error('Failed to initialize session:', err);
      }
    };

    initializeSession();

    // Cleanup on unmount
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [updateContext]);

  /**
   * Update context when contextRefreshTrigger changes (Requirement 11.4)
   * This happens after each message is complete
   */
  useEffect(() => {
    if (sessionId && contextRefreshTrigger > 0) {
      updateContext(sessionId);
    }
  }, [contextRefreshTrigger, sessionId, updateContext]);

  /**
   * Send a message and stream the response (Requirement 1.4, 8.1, 8.2)
   * 
   * @param content - The message content to send
   */
  const sendMessage = useCallback(async (content: string) => {
    if (!sessionId) {
      setError('Unable to send message: No active session. Please refresh the page.');
      return;
    }

    if (!content.trim()) {
      return;
    }

    try {
      setError(null);
      
      // Store the message for retry functionality (Requirement 8.5)
      lastUserMessageRef.current = content.trim();

      // Add user message to state
      const userMessage: Message = {
        role: 'user',
        content: content.trim(),
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, userMessage]);

      // Start loading state (Requirement 7.5: Show loading indicator while waiting for first token)
      setIsLoading(true);
      setIsConnected(true);

      // Create assistant message placeholder
      const assistantMessage: Message = {
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, assistantMessage]);

      // Close any existing connection
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      // Create new SSE connection
      const eventSource = createStreamingConnection(sessionId, content.trim());
      eventSourceRef.current = eventSource;

      // Handle incoming messages
      eventSource.onmessage = (event) => {
        try {
          const data: StreamEvent = JSON.parse(event.data);

          if (data.type === 'token') {
            // First token received - switch from loading to streaming (Requirement 7.5)
            if (isLoading) {
              setIsLoading(false);
              setIsStreaming(true);
            }
            
            // Append token to the last message (assistant message)
            setMessages(prev => {
              const updated = [...prev];
              const lastMessage = updated[updated.length - 1];
              if (lastMessage && lastMessage.role === 'assistant') {
                // Create a new message object instead of mutating
                updated[updated.length - 1] = {
                  ...lastMessage,
                  content: lastMessage.content + data.content
                };
              }
              return updated;
            });
          } else if (data.type === 'done') {
            // Streaming complete
            setIsLoading(false);
            setIsStreaming(false);
            eventSource.close();
            eventSourceRef.current = null;
            
            // Trigger context refresh after message is complete (Requirement 11.4)
            setContextRefreshTrigger(prev => prev + 1);
          } else if (data.type === 'error') {
            // Handle error from stream (Requirement 8.2)
            const errorMsg = data.message || 'The agent encountered an error while processing your request.';
            setError(errorMsg);
            setIsLoading(false);
            setIsStreaming(false);
            
            // Remove the empty assistant message on error
            setMessages(prev => {
              const updated = [...prev];
              if (updated.length > 0 && updated[updated.length - 1].role === 'assistant' && !updated[updated.length - 1].content) {
                updated.pop();
              }
              return updated;
            });
            
            eventSource.close();
            eventSourceRef.current = null;
          }
        } catch (err) {
          console.error('Failed to parse SSE message:', err);
          setError('Unable to process the server response. Please try again.');
          setIsLoading(false);
          setIsStreaming(false);
          
          // Remove the empty assistant message on error
          setMessages(prev => {
            const updated = [...prev];
            if (updated.length > 0 && updated[updated.length - 1].role === 'assistant' && !updated[updated.length - 1].content) {
              updated.pop();
            }
            return updated;
          });
          
          eventSource.close();
          eventSourceRef.current = null;
        }
      };

      // Handle connection errors (Requirement 8.1, 7.5: Show connection status)
      eventSource.onerror = () => {
        console.error('SSE connection error');
        setError('Connection lost. Please check your internet connection and try again.');
        setIsLoading(false);
        setIsStreaming(false);
        setIsConnected(false); // Update connection status
        
        // Remove the empty assistant message on error
        setMessages(prev => {
          const updated = [...prev];
          if (updated.length > 0 && updated[updated.length - 1].role === 'assistant' && !updated[updated.length - 1].content) {
            updated.pop();
          }
          return updated;
        });
        
        eventSource.close();
        eventSourceRef.current = null;
      };

    } catch (err) {
      // Provide user-friendly error messages (Requirement 8.1)
      let errorMessage = 'Unable to send your message. Please try again.';
      
      if (err instanceof Error) {
        if (err.message.includes('fetch')) {
          errorMessage = 'Network error: Unable to reach the server. Please check your connection.';
        } else if (err.message.includes('timeout')) {
          errorMessage = 'Request timed out. The server is taking too long to respond.';
        } else {
          errorMessage = `Error: ${err.message}`;
        }
      }
      
      setError(errorMessage);
      setIsLoading(false);
      setIsStreaming(false);
      
      // Remove the empty assistant message on error
      setMessages(prev => {
        const updated = [...prev];
        if (updated.length > 0 && updated[updated.length - 1].role === 'assistant' && !updated[updated.length - 1].content) {
          updated.pop();
        }
        return updated;
      });
      
      console.error('Failed to send message:', err);
    }
  }, [sessionId, isLoading]);

  /**
   * Clear the current session and start a new one (Requirement 3.5)
   */
  const clearSession = useCallback(async () => {
    try {
      setError(null);

      // Close any active streaming connection
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }

      // Clear the current session on the backend
      if (sessionId) {
        await clearSessionAPI(sessionId);
      }

      // Create a new session
      const newSessionId = await createSession();
      setSessionId(newSessionId);

      // Clear messages, context, and last message ref
      setMessages([]);
      setContext(null);
      setIsLoading(false);
      setIsStreaming(false);
      setIsConnected(true);
      lastUserMessageRef.current = null;
      
      // Fetch context for new session (Requirement 11.4)
      await updateContext(newSessionId);

    } catch (err) {
      let errorMessage = 'Unable to start a new conversation. Please refresh the page.';
      
      if (err instanceof Error) {
        if (err.message.includes('fetch') || err.message.includes('Network')) {
          errorMessage = 'Network error: Unable to reach the server. Please check your connection.';
        }
      }
      
      setError(errorMessage);
      console.error('Failed to clear session:', err);
    }
  }, [sessionId]);

  /**
   * Retry the last message that failed (Requirement 8.5)
   */
  const retryLastMessage = useCallback(async () => {
    if (lastUserMessageRef.current) {
      // Remove the last user message from the display before retrying
      setMessages(prev => {
        const updated = [...prev];
        // Remove the last message if it's a user message
        if (updated.length > 0 && updated[updated.length - 1].role === 'user') {
          updated.pop();
        }
        return updated;
      });
      
      // Retry sending the message
      await sendMessage(lastUserMessageRef.current);
    }
  }, [sendMessage]);

  /**
   * Dismiss the current error message (Requirement 8.1)
   */
  const dismissError = useCallback(() => {
    setError(null);
  }, []);

  return {
    messages,
    sessionId,
    isStreaming,
    isLoading,
    isConnected,
    error,
    context,
    contextRefreshTrigger,
    sendMessage,
    clearSession,
    retryLastMessage,
    dismissError,
  };
}
