/**
 * useChat Hook
 * 
 * Custom React hook for managing chat state and interactions.
 * Handles message state, session management, and SSE streaming.
 * 
 * Requirements: 1.4, 3.1, 3.5
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import type { Message, StreamEvent, ConversationContext, SessionSummary } from '../types';
import {
  createSession,
  createStreamingConnection,
  clearSession as clearSessionAPI,
  getSessionMessages,
  fetchContext,
  getSessions,
  deleteSession as deleteSessionAPI,
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
  failedMessageIndices: Set<number>;
  editingMessageIndex: number | null;
  sessions: SessionSummary[];
  sendMessage: (content: string) => Promise<void>;
  clearSession: () => Promise<void>;
  retryLastMessage: () => Promise<void>;
  retryMessage: (messageIndex: number) => Promise<void>;
  dismissError: () => void;
  startEditMessage: (messageIndex: number) => void;
  saveEditMessage: (messageIndex: number, newContent: string) => Promise<void>;
  cancelEditMessage: () => void;
  loadSession: (sessionId: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
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
  
  // Retry state tracking (Requirement 3.1)
  const [failedMessageIndices, setFailedMessageIndices] = useState<Set<number>>(new Set());
  
  // Edit state tracking (Requirement 4.2)
  const [editingMessageIndex, setEditingMessageIndex] = useState<number | null>(null);
  
  // Session list state (Requirement 1.1)
  const [sessions, setSessions] = useState<SessionSummary[]>([]);

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
   * Fetch all sessions from the backend (Requirement 1.1)
   */
  const fetchSessions = useCallback(async () => {
    try {
      const sessionList = await getSessions();
      setSessions(sessionList);
    } catch (err) {
      console.error('Failed to fetch sessions:', err);
      // Don't show error to user for session list failures
    }
  }, []);

  /**
   * Initialize session on mount (Requirement 3.1)
   */
  useEffect(() => {
    const initializeSession = async () => {
      try {
        // Fetch existing sessions first (Requirement 1.1)
        await fetchSessions();
        
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
  }, [updateContext, fetchSessions]);

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

      // Update session in the list (Requirement 1.3, 1.4)
      // If this is the first message, update the preview
      setSessions(prev => {
        const existingIndex = prev.findIndex(s => s.id === sessionId);
        if (existingIndex >= 0) {
          // Update existing session
          const updated = [...prev];
          const existing = updated[existingIndex];
          // Only update preview if it's empty (first message)
          const newPreview = existing.preview || content.trim().substring(0, 100);
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
            preview: content.trim().substring(0, 100),
            timestamp: new Date().toISOString(),
            messageCount: 1,
          };
          return [newSession, ...prev];
        }
      });

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
            // Handle error from stream (Requirement 8.2, 3.1)
            const errorMsg = data.message || 'The agent encountered an error while processing your request.';
            setError(errorMsg);
            setIsLoading(false);
            setIsStreaming(false);
            
            // Mark the user message as failed and track its index (Requirement 3.1)
            setMessages(prev => {
              const updated = [...prev];
              // Remove the empty assistant message on error
              if (updated.length > 0 && updated[updated.length - 1].role === 'assistant' && !updated[updated.length - 1].content) {
                updated.pop();
              }
              // Mark the last user message as failed
              const userMsgIndex = updated.length - 1;
              if (userMsgIndex >= 0 && updated[userMsgIndex].role === 'user') {
                updated[userMsgIndex] = {
                  ...updated[userMsgIndex],
                  status: 'failed',
                  error: errorMsg,
                };
                // Track failed message index
                setFailedMessageIndices(prev => new Set(prev).add(userMsgIndex));
              }
              return updated;
            });
            
            eventSource.close();
            eventSourceRef.current = null;
          }
        } catch (err) {
          console.error('Failed to parse SSE message:', err);
          const errorMsg = 'Unable to process the server response. Please try again.';
          setError(errorMsg);
          setIsLoading(false);
          setIsStreaming(false);
          
          // Mark the user message as failed and track its index (Requirement 3.1)
          setMessages(prev => {
            const updated = [...prev];
            // Remove the empty assistant message on error
            if (updated.length > 0 && updated[updated.length - 1].role === 'assistant' && !updated[updated.length - 1].content) {
              updated.pop();
            }
            // Mark the last user message as failed
            const userMsgIndex = updated.length - 1;
            if (userMsgIndex >= 0 && updated[userMsgIndex].role === 'user') {
              updated[userMsgIndex] = {
                ...updated[userMsgIndex],
                status: 'failed',
                error: errorMsg,
              };
              setFailedMessageIndices(prev => new Set(prev).add(userMsgIndex));
            }
            return updated;
          });
          
          eventSource.close();
          eventSourceRef.current = null;
        }
      };

      // Handle connection errors (Requirement 8.1, 7.5, 3.1: Show connection status)
      eventSource.onerror = () => {
        console.error('SSE connection error');
        const errorMsg = 'Connection lost. Please check your internet connection and try again.';
        setError(errorMsg);
        setIsLoading(false);
        setIsStreaming(false);
        setIsConnected(false); // Update connection status
        
        // Mark the user message as failed and track its index (Requirement 3.1)
        setMessages(prev => {
          const updated = [...prev];
          // Remove the empty assistant message on error
          if (updated.length > 0 && updated[updated.length - 1].role === 'assistant' && !updated[updated.length - 1].content) {
            updated.pop();
          }
          // Mark the last user message as failed
          const userMsgIndex = updated.length - 1;
          if (userMsgIndex >= 0 && updated[userMsgIndex].role === 'user') {
            updated[userMsgIndex] = {
              ...updated[userMsgIndex],
              status: 'failed',
              error: errorMsg,
            };
            setFailedMessageIndices(prev => new Set(prev).add(userMsgIndex));
          }
          return updated;
        });
        
        eventSource.close();
        eventSourceRef.current = null;
      };

    } catch (err) {
      // Provide user-friendly error messages (Requirement 8.1, 3.1)
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
      
      // Mark the user message as failed and track its index (Requirement 3.1)
      setMessages(prev => {
        const updated = [...prev];
        // Remove the empty assistant message on error
        if (updated.length > 0 && updated[updated.length - 1].role === 'assistant' && !updated[updated.length - 1].content) {
          updated.pop();
        }
        // Mark the last user message as failed
        const userMsgIndex = updated.length - 1;
        if (userMsgIndex >= 0 && updated[userMsgIndex].role === 'user') {
          updated[userMsgIndex] = {
            ...updated[userMsgIndex],
            status: 'failed',
            error: errorMessage,
          };
          setFailedMessageIndices(prev => new Set(prev).add(userMsgIndex));
        }
        return updated;
      });
      
      console.error('Failed to send message:', err);
    }
  }, [sessionId, isLoading]);

  /**
   * Clear the current session and start a new one (Requirement 3.5, 1.3)
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

      // Add new session to top of list (Requirement 1.3)
      const newSessionSummary: SessionSummary = {
        id: newSessionId,
        preview: '',
        timestamp: new Date().toISOString(),
        messageCount: 0,
      };
      setSessions(prev => [newSessionSummary, ...prev]);

      // Clear messages, context, failed indices, and last message ref
      setMessages([]);
      setContext(null);
      setIsLoading(false);
      setIsStreaming(false);
      setIsConnected(true);
      setFailedMessageIndices(new Set());
      setEditingMessageIndex(null);
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
  }, [sessionId, updateContext]);

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
   * Retry a specific failed message by index (Requirement 3.2, 3.3)
   * 
   * @param messageIndex - The index of the failed user message to retry
   */
  const retryMessage = useCallback(async (messageIndex: number) => {
    // Get the message content at the specified index
    const messageToRetry = messages[messageIndex];
    
    if (!messageToRetry || messageToRetry.role !== 'user') {
      console.error('Cannot retry: Invalid message index or not a user message');
      return;
    }
    
    const contentToRetry = messageToRetry.content;
    
    // Remove the failed message from tracking (Requirement 3.3)
    setFailedMessageIndices(prev => {
      const updated = new Set(prev);
      updated.delete(messageIndex);
      return updated;
    });
    
    // Remove the failed user message and any subsequent messages
    setMessages(prev => prev.slice(0, messageIndex));
    
    // Clear any existing error
    setError(null);
    
    // Re-send the original message content (Requirement 3.2)
    await sendMessage(contentToRetry);
  }, [messages, sendMessage]);

  /**
   * Dismiss the current error message (Requirement 8.1)
   */
  const dismissError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Start editing a message at the specified index (Requirement 4.2)
   * 
   * @param messageIndex - The index of the user message to edit
   */
  const startEditMessage = useCallback((messageIndex: number) => {
    // Only allow editing user messages
    if (messages[messageIndex]?.role !== 'user') {
      console.error('Cannot edit: Not a user message');
      return;
    }
    
    // Don't allow editing while streaming or loading
    if (isStreaming || isLoading) {
      console.error('Cannot edit: Currently streaming or loading');
      return;
    }
    
    setEditingMessageIndex(messageIndex);
  }, [messages, isStreaming, isLoading]);

  /**
   * Save an edited message and re-send to the agent (Requirement 4.4)
   * Removes all messages after the edited index and re-sends the edited content
   * 
   * @param messageIndex - The index of the message being edited
   * @param newContent - The new content for the message
   */
  const saveEditMessage = useCallback(async (messageIndex: number, newContent: string) => {
    if (!newContent.trim()) {
      console.error('Cannot save: Empty message content');
      return;
    }
    
    // Clear editing state
    setEditingMessageIndex(null);
    
    // Remove all messages after the edited index (Requirement 4.4)
    setMessages(prev => prev.slice(0, messageIndex));
    
    // Clear any failed message indices that are at or after the edited index
    setFailedMessageIndices(prev => {
      const updated = new Set<number>();
      prev.forEach(idx => {
        if (idx < messageIndex) {
          updated.add(idx);
        }
      });
      return updated;
    });
    
    // Clear any existing error
    setError(null);
    
    // Re-send the edited content to the agent
    await sendMessage(newContent.trim());
  }, [sendMessage]);

  /**
   * Cancel editing and restore the original message (Requirement 4.5)
   */
  const cancelEditMessage = useCallback(() => {
    setEditingMessageIndex(null);
  }, []);

  /**
   * Load a session by ID (Requirement 1.2)
   * Loads messages for the selected session and updates current sessionId
   * 
   * @param targetSessionId - The session ID to load
   */
  const loadSession = useCallback(async (targetSessionId: string) => {
    try {
      setError(null);
      
      // Close any active streaming connection
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      
      // Reset states
      setIsLoading(false);
      setIsStreaming(false);
      setFailedMessageIndices(new Set());
      setEditingMessageIndex(null);
      
      // Update session ID
      setSessionId(targetSessionId);
      
      // Load messages for the session
      try {
        const sessionMessages = await getSessionMessages(targetSessionId);
        setMessages(sessionMessages);
      } catch {
        // If no messages exist, start with empty array
        setMessages([]);
        console.log('No existing messages for session');
      }
      
      // Fetch context for the session (Requirement 11.4)
      await updateContext(targetSessionId);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load session';
      setError(errorMessage);
      console.error('Failed to load session:', err);
    }
  }, [updateContext]);

  /**
   * Delete a session (Requirement 1.6)
   * Calls DELETE endpoint and removes from local sessions list
   * 
   * @param targetSessionId - The session ID to delete
   */
  const deleteSessionHandler = useCallback(async (targetSessionId: string) => {
    try {
      // Call DELETE endpoint
      await deleteSessionAPI(targetSessionId);
      
      // Remove from local sessions list
      setSessions(prev => prev.filter(s => s.id !== targetSessionId));
      
      // If we deleted the current session, create a new one
      if (targetSessionId === sessionId) {
        const newSessionId = await createSession();
        setSessionId(newSessionId);
        setMessages([]);
        setContext(null);
        setFailedMessageIndices(new Set());
        setEditingMessageIndex(null);
        lastUserMessageRef.current = null;
        
        // Fetch context for new session
        await updateContext(newSessionId);
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete session';
      setError(errorMessage);
      console.error('Failed to delete session:', err);
    }
  }, [sessionId, updateContext]);

  return {
    messages,
    sessionId,
    isStreaming,
    isLoading,
    isConnected,
    error,
    context,
    contextRefreshTrigger,
    failedMessageIndices,
    editingMessageIndex,
    sessions,
    sendMessage,
    clearSession,
    retryLastMessage,
    retryMessage,
    dismissError,
    startEditMessage,
    saveEditMessage,
    cancelEditMessage,
    loadSession,
    deleteSession: deleteSessionHandler,
  };
}
