/**
 * useSession Hook
 * 
 * Custom React hook for managing planning session state.
 * Handles session data, participants, venues, itinerary, and comments.
 * 
 * Requirements: 1.1, 1.2, 1.4, 2.1, 2.2, 3.2, 4.3, 6.1
 */

import { useState, useCallback } from 'react';
import type {
  PlanningSession,
  Participant,
  RankedVenue,
  ItineraryItem,
  Comment,
  SessionSummary,
  VoteType,
} from '../types/planningSession';
import {
  getPlanningSession,
  getParticipants,
  getVenues,
  castVote,
  getItinerary,
  addToItinerary,
  removeFromItinerary,
  finalizeSession,
  getComments,
  addComment,
  revokeInvite,
} from '../services/planningSessionApi';

export interface UseSessionReturn {
  session: PlanningSession | null;
  participants: Participant[];
  venues: RankedVenue[];
  itinerary: ItineraryItem[];
  comments: Record<string, Comment[]>;
  summary: SessionSummary | null;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  loadSession: (sessionId: string) => Promise<void>;
  loadParticipants: () => Promise<void>;
  loadVenues: () => Promise<void>;
  loadItinerary: () => Promise<void>;
  loadComments: (venueId: string) => Promise<void>;
  vote: (venueId: string, participantId: string, voteType: VoteType) => Promise<void>;
  addItemToItinerary: (venueId: string, scheduledTime: string, addedBy: string) => Promise<void>;
  removeItemFromItinerary: (itemId: string) => Promise<void>;
  addVenueComment: (venueId: string, participantId: string, text: string) => Promise<void>;
  finalize: (organizerId: string) => Promise<void>;
  revokeSessionInvite: (organizerId: string) => Promise<void>;
  clearError: () => void;
}

/**
 * Custom hook for planning session management
 * 
 * Requirements: 1.1, 1.2, 1.4, 2.1, 2.2, 3.2, 4.3, 6.1
 */
export function useSession(): UseSessionReturn {
  const [session, setSession] = useState<PlanningSession | null>(null);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [venues, setVenues] = useState<RankedVenue[]>([]);
  const [itinerary, setItinerary] = useState<ItineraryItem[]>([]);
  const [comments, setComments] = useState<Record<string, Comment[]>>({});
  const [summary, setSummary] = useState<SessionSummary | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Load session data
   * Requirement: 1.1, 1.2
   */
  const loadSession = useCallback(async (sessionId: string) => {
    try {
      setIsLoading(true);
      setError(null);
      const sessionData = await getPlanningSession(sessionId);
      setSession(sessionData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load session';
      setError(errorMessage);
      console.error('Failed to load session:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Load participants
   * Requirement: 1.4
   */
  const loadParticipants = useCallback(async () => {
    if (!session) return;
    
    try {
      setError(null);
      const participantData = await getParticipants(session.id);
      setParticipants(participantData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load participants';
      setError(errorMessage);
      console.error('Failed to load participants:', err);
    }
  }, [session]);

  /**
   * Load venues with votes
   * Requirement: 2.1, 2.4
   */
  const loadVenues = useCallback(async () => {
    if (!session) return;
    
    try {
      setError(null);
      const venueData = await getVenues(session.id);
      setVenues(venueData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load venues';
      setError(errorMessage);
      console.error('Failed to load venues:', err);
    }
  }, [session]);

  /**
   * Load itinerary
   * Requirement: 3.2
   */
  const loadItinerary = useCallback(async () => {
    if (!session) return;
    
    try {
      setError(null);
      const itineraryData = await getItinerary(session.id);
      setItinerary(itineraryData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load itinerary';
      setError(errorMessage);
      console.error('Failed to load itinerary:', err);
    }
  }, [session]);

  /**
   * Load comments for a venue
   * Requirement: 6.2
   */
  const loadComments = useCallback(async (venueId: string) => {
    if (!session) return;
    
    try {
      setError(null);
      const commentData = await getComments(session.id, venueId);
      setComments(prev => ({ ...prev, [venueId]: commentData }));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load comments';
      setError(errorMessage);
      console.error('Failed to load comments:', err);
    }
  }, [session]);

  /**
   * Cast a vote on a venue
   * Requirement: 2.2
   */
  const vote = useCallback(async (
    venueId: string,
    participantId: string,
    voteType: VoteType
  ) => {
    if (!session) return;
    
    try {
      setError(null);
      await castVote(session.id, venueId, { participant_id: participantId, vote_type: voteType });
      // Reload venues to get updated vote tallies
      await loadVenues();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to cast vote';
      setError(errorMessage);
      console.error('Failed to cast vote:', err);
    }
  }, [session, loadVenues]);

  /**
   * Add item to itinerary
   * Requirement: 3.2
   */
  const addItemToItinerary = useCallback(async (
    venueId: string,
    scheduledTime: string,
    addedBy: string
  ) => {
    if (!session) return;
    
    try {
      setError(null);
      await addToItinerary(session.id, {
        venue_id: venueId,
        scheduled_time: scheduledTime,
        added_by: addedBy,
      });
      // Reload itinerary
      await loadItinerary();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to add to itinerary';
      setError(errorMessage);
      console.error('Failed to add to itinerary:', err);
    }
  }, [session, loadItinerary]);

  /**
   * Remove item from itinerary
   * Requirement: 3.3
   */
  const removeItemFromItinerary = useCallback(async (itemId: string) => {
    if (!session) return;
    
    try {
      setError(null);
      await removeFromItinerary(session.id, itemId);
      // Reload itinerary
      await loadItinerary();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to remove from itinerary';
      setError(errorMessage);
      console.error('Failed to remove from itinerary:', err);
    }
  }, [session, loadItinerary]);

  /**
   * Add comment to venue
   * Requirement: 6.1
   */
  const addVenueComment = useCallback(async (
    venueId: string,
    participantId: string,
    text: string
  ) => {
    if (!session) return;
    
    try {
      setError(null);
      await addComment(session.id, venueId, { participant_id: participantId, text });
      // Reload comments for this venue
      await loadComments(venueId);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to add comment';
      setError(errorMessage);
      console.error('Failed to add comment:', err);
    }
  }, [session, loadComments]);

  /**
   * Finalize session
   * Requirement: 4.3
   */
  const finalize = useCallback(async (organizerId: string) => {
    if (!session) return;
    
    try {
      setIsLoading(true);
      setError(null);
      const summaryData = await finalizeSession(session.id, organizerId);
      setSummary(summaryData);
      // Reload session to get updated status
      await loadSession(session.id);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to finalize session';
      setError(errorMessage);
      console.error('Failed to finalize session:', err);
    } finally {
      setIsLoading(false);
    }
  }, [session, loadSession]);

  /**
   * Revoke invite link
   * Requirement: 1.5
   */
  const revokeSessionInvite = useCallback(async (organizerId: string) => {
    if (!session) return;
    
    try {
      setError(null);
      await revokeInvite(session.id, organizerId);
      // Reload session to get updated invite status
      await loadSession(session.id);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to revoke invite';
      setError(errorMessage);
      console.error('Failed to revoke invite:', err);
    }
  }, [session, loadSession]);

  /**
   * Clear error message
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    session,
    participants,
    venues,
    itinerary,
    comments,
    summary,
    isLoading,
    error,
    loadSession,
    loadParticipants,
    loadVenues,
    loadItinerary,
    loadComments,
    vote,
    addItemToItinerary,
    removeItemFromItinerary,
    addVenueComment,
    finalize,
    revokeSessionInvite,
    clearError,
  };
}
