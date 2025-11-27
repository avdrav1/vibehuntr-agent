/**
 * Planning Session API Client
 * 
 * Provides functions to interact with planning session endpoints.
 * Requirements: 1.1, 1.2, 1.4, 1.5, 2.1, 2.2, 3.2, 4.3, 6.1, 6.2
 */

import type {
  PlanningSession,
  Participant,
  VenueOption,
  Vote,
  VoteTally,
  RankedVenue,
  ItineraryItem,
  Comment,
  SessionSummary,
  CreateSessionRequest,
  CreateSessionResponse,
  JoinSessionRequest,
  JoinSessionResponse,
  CastVoteRequest,
  AddToItineraryRequest,
  AddCommentRequest,
} from '../types/planningSession';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Custom error class for API errors
 */
export class PlanningSessionAPIError extends Error {
  status?: number;
  details?: unknown;

  constructor(message: string, status?: number, details?: unknown) {
    super(message);
    this.name = 'PlanningSessionAPIError';
    this.status = status;
    this.details = details;
  }
}

/**
 * Handle API response and throw errors if needed
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage: string;
    let errorDetails: unknown;

    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || `Request failed with status ${response.status}`;
      errorDetails = errorData;
    } catch {
      errorMessage = `Request failed with status ${response.status}`;
    }

    throw new PlanningSessionAPIError(errorMessage, response.status, errorDetails);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return await response.json();
}

/**
 * Create a new planning session
 * POST /api/sessions
 * Requirement: 1.1
 */
export async function createPlanningSession(
  request: CreateSessionRequest
): Promise<CreateSessionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return handleResponse<CreateSessionResponse>(response);
}

/**
 * Get a planning session by ID
 * GET /api/sessions/{id}
 * Requirement: 1.4
 */
export async function getPlanningSession(sessionId: string): Promise<PlanningSession> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });
  return handleResponse<PlanningSession>(response);
}

/**
 * Join a session via invite token
 * POST /api/sessions/join/{token}
 * Requirement: 1.2
 */
export async function joinSession(
  inviteToken: string,
  request: JoinSessionRequest
): Promise<JoinSessionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/join/${inviteToken}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return handleResponse<JoinSessionResponse>(response);
}

/**
 * Get all participants in a session
 * GET /api/sessions/{id}/participants
 * Requirement: 1.4
 */
export async function getParticipants(sessionId: string): Promise<Participant[]> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/participants`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });
  const data = await handleResponse<{ participants: Participant[] }>(response);
  return data.participants;
}

/**
 * Revoke invite link
 * POST /api/sessions/{id}/revoke
 * Requirement: 1.5
 */
export async function revokeInvite(sessionId: string, organizerId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/revoke`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ organizer_id: organizerId }),
  });
  await handleResponse<{ success: boolean }>(response);
}

/**
 * Add a venue option
 * POST /api/sessions/{id}/venues
 * Requirement: 2.1
 */
export async function addVenueOption(
  sessionId: string,
  venue: Omit<VenueOption, 'id' | 'session_id' | 'suggested_at'>
): Promise<VenueOption> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/venues`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(venue),
  });
  return handleResponse<VenueOption>(response);
}

/**
 * Get all venues with votes
 * GET /api/sessions/{id}/venues
 * Requirement: 2.1, 2.4
 */
export async function getVenues(sessionId: string): Promise<RankedVenue[]> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/venues`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });
  const data = await handleResponse<{ venues: RankedVenue[] }>(response);
  return data.venues;
}

/**
 * Cast a vote on a venue
 * POST /api/sessions/{id}/venues/{venue_id}/vote
 * Requirement: 2.2
 */
export async function castVote(
  sessionId: string,
  venueId: string,
  request: CastVoteRequest
): Promise<Vote> {
  const response = await fetch(
    `${API_BASE_URL}/api/sessions/${sessionId}/venues/${venueId}/vote`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    }
  );
  return handleResponse<Vote>(response);
}

/**
 * Get vote tally for a venue
 * GET /api/sessions/{id}/venues/{venue_id}/votes
 * Requirement: 2.4
 */
export async function getVoteTally(sessionId: string, venueId: string): Promise<VoteTally> {
  const response = await fetch(
    `${API_BASE_URL}/api/sessions/${sessionId}/venues/${venueId}/votes`,
    {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    }
  );
  return handleResponse<VoteTally>(response);
}

/**
 * Add item to itinerary
 * POST /api/sessions/{id}/itinerary
 * Requirement: 3.2
 */
export async function addToItinerary(
  sessionId: string,
  request: AddToItineraryRequest
): Promise<ItineraryItem> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/itinerary`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return handleResponse<ItineraryItem>(response);
}

/**
 * Remove item from itinerary
 * DELETE /api/sessions/{id}/itinerary/{item_id}
 * Requirement: 3.3
 */
export async function removeFromItinerary(sessionId: string, itemId: string): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/sessions/${sessionId}/itinerary/${itemId}`,
    {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
    }
  );
  await handleResponse<{ success: boolean }>(response);
}

/**
 * Get itinerary
 * GET /api/sessions/{id}/itinerary
 * Requirement: 3.2
 */
export async function getItinerary(sessionId: string): Promise<ItineraryItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/itinerary`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });
  const data = await handleResponse<{ itinerary: ItineraryItem[] }>(response);
  return data.itinerary;
}

/**
 * Finalize session
 * POST /api/sessions/{id}/finalize
 * Requirement: 4.3
 */
export async function finalizeSession(
  sessionId: string,
  organizerId: string
): Promise<SessionSummary> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/finalize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ organizer_id: organizerId }),
  });
  return handleResponse<SessionSummary>(response);
}

/**
 * Add comment to venue
 * POST /api/sessions/{id}/venues/{venue_id}/comments
 * Requirement: 6.1
 */
export async function addComment(
  sessionId: string,
  venueId: string,
  request: AddCommentRequest
): Promise<Comment> {
  const response = await fetch(
    `${API_BASE_URL}/api/sessions/${sessionId}/venues/${venueId}/comments`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    }
  );
  return handleResponse<Comment>(response);
}

/**
 * Get comments for a venue
 * GET /api/sessions/{id}/venues/{venue_id}/comments
 * Requirement: 6.2
 */
export async function getComments(sessionId: string, venueId: string): Promise<Comment[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/sessions/${sessionId}/venues/${venueId}/comments`,
    {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    }
  );
  const data = await handleResponse<{ comments: Comment[] }>(response);
  return data.comments;
}
