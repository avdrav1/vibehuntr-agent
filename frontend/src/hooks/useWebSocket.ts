/**
 * useWebSocket Hook
 * 
 * Custom React hook for managing WebSocket connections for real-time updates.
 * Handles connection lifecycle, reconnection, and event broadcasting.
 * 
 * Requirements: 3.1, 3.4
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import type { SessionEvent } from '../types/planningSession';

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';

export interface UseWebSocketReturn {
  isConnected: boolean;
  lastEvent: SessionEvent | null;
  error: string | null;
  connect: (sessionId: string, participantId: string) => void;
  disconnect: () => void;
  clearError: () => void;
}

/**
 * Custom hook for WebSocket connection management
 * 
 * Requirements: 3.1, 3.4
 */
export function useWebSocket(
  onEvent?: (event: SessionEvent) => void
): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [lastEvent, setLastEvent] = useState<SessionEvent | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef<number>(0);
  const sessionIdRef = useRef<string | null>(null);
  const participantIdRef = useRef<string | null>(null);

  const MAX_RECONNECT_ATTEMPTS = 5;
  const RECONNECT_DELAY = 2000;

  /**
   * Connect to WebSocket
   * Requirement: 3.1
   */
  const connect = useCallback((sessionId: string, participantId: string) => {
    // Store connection params for reconnection
    sessionIdRef.current = sessionId;
    participantIdRef.current = participantId;

    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close();
    }

    try {
      const ws = new WebSocket(
        `${WS_BASE_URL}/api/sessions/${sessionId}/ws?participant_id=${participantId}`
      );

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const sessionEvent: SessionEvent = JSON.parse(event.data);
          setLastEvent(sessionEvent);
          
          // Call the callback if provided
          if (onEvent) {
            onEvent(sessionEvent);
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
          setError('Failed to process real-time update');
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('Connection error occurred');
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        wsRef.current = null;

        // Attempt reconnection if not a normal closure and we have connection params
        if (
          event.code !== 1000 &&
          sessionIdRef.current &&
          participantIdRef.current &&
          reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS
        ) {
          reconnectAttemptsRef.current += 1;
          console.log(
            `Attempting to reconnect (${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})...`
          );
          
          reconnectTimeoutRef.current = setTimeout(() => {
            if (sessionIdRef.current && participantIdRef.current) {
              connect(sessionIdRef.current, participantIdRef.current);
            }
          }, RECONNECT_DELAY);
        } else if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
          setError('Unable to maintain connection. Please refresh the page.');
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('Failed to create WebSocket connection:', err);
      setError('Failed to establish real-time connection');
    }
  }, [onEvent]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    // Clear reconnection timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Clear connection params to prevent reconnection
    sessionIdRef.current = null;
    participantIdRef.current = null;
    reconnectAttemptsRef.current = 0;

    // Close WebSocket connection
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }

    setIsConnected(false);
  }, []);

  /**
   * Clear error message
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    lastEvent,
    error,
    connect,
    disconnect,
    clearError,
  };
}
