/**
 * Planning Session Context
 * 
 * React Context for managing planning session state across components.
 * Combines session state management with real-time WebSocket updates.
 * 
 * Requirements: 3.1, 3.4
 */

import React, { createContext, useContext, useEffect, useCallback } from 'react';
import { useSession, UseSessionReturn } from '../hooks/useSession';
import { useWebSocket } from '../hooks/useWebSocket';
import type { SessionEvent } from '../types/planningSession';

interface PlanningSessionContextValue extends UseSessionReturn {
  isWebSocketConnected: boolean;
  webSocketError: string | null;
  connectWebSocket: (participantId: string) => void;
  disconnectWebSocket: () => void;
}

const PlanningSessionContext = createContext<PlanningSessionContextValue | undefined>(undefined);

interface PlanningSessionProviderProps {
  children: React.ReactNode;
}

/**
 * Planning Session Provider
 * 
 * Provides planning session state and real-time updates to child components.
 * Requirements: 3.1, 3.4
 */
export function PlanningSessionProvider({ children }: PlanningSessionProviderProps) {
  const sessionHook = useSession();
  
  /**
   * Handle WebSocket events
   * Requirement: 3.1, 3.4
   */
  const handleWebSocketEvent = useCallback((event: SessionEvent) => {
    console.log('Received WebSocket event:', event.type);
    
    // Reload relevant data based on event type
    switch (event.type) {
      case 'participant_joined':
      case 'participant_left':
        sessionHook.loadParticipants();
        break;
      
      case 'venue_added':
      case 'vote_cast':
        sessionHook.loadVenues();
        break;
      
      case 'itinerary_updated':
        sessionHook.loadItinerary();
        break;
      
      case 'comment_added':
        // Reload comments for the specific venue
        if (event.data && typeof event.data === 'object' && 'venue_id' in event.data) {
          const venueId = (event.data as { venue_id: string }).venue_id;
          sessionHook.loadComments(venueId);
        }
        break;
      
      case 'session_finalized':
        sessionHook.loadSession(event.session_id);
        break;
    }
  }, [sessionHook]);

  const webSocketHook = useWebSocket(handleWebSocketEvent);

  /**
   * Connect to WebSocket for a participant
   */
  const connectWebSocket = useCallback((participantId: string) => {
    if (sessionHook.session) {
      webSocketHook.connect(sessionHook.session.id, participantId);
    }
  }, [sessionHook.session, webSocketHook]);

  /**
   * Disconnect from WebSocket
   */
  const disconnectWebSocket = useCallback(() => {
    webSocketHook.disconnect();
  }, [webSocketHook]);

  /**
   * Auto-disconnect WebSocket on unmount
   */
  useEffect(() => {
    return () => {
      webSocketHook.disconnect();
    };
  }, [webSocketHook]);

  const contextValue: PlanningSessionContextValue = {
    ...sessionHook,
    isWebSocketConnected: webSocketHook.isConnected,
    webSocketError: webSocketHook.error,
    connectWebSocket,
    disconnectWebSocket,
  };

  return (
    <PlanningSessionContext.Provider value={contextValue}>
      {children}
    </PlanningSessionContext.Provider>
  );
}

/**
 * Hook to use Planning Session Context
 * 
 * Must be used within a PlanningSessionProvider
 */
export function usePlanningSession(): PlanningSessionContextValue {
  const context = useContext(PlanningSessionContext);
  
  if (context === undefined) {
    throw new Error('usePlanningSession must be used within a PlanningSessionProvider');
  }
  
  return context;
}
