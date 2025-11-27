/**
 * TypeScript type definitions for Planning Session feature
 * Requirements: 1.1, 1.2, 1.4, 2.1, 2.2, 3.1, 3.2, 4.5, 6.1
 */

/**
 * Session status enum
 */
export type SessionStatus = 'ACTIVE' | 'FINALIZED' | 'ARCHIVED';

/**
 * Vote type enum
 */
export type VoteType = 'UPVOTE' | 'DOWNVOTE' | 'NEUTRAL';

/**
 * Participant in a planning session
 * Requirement: 1.4
 */
export interface Participant {
  id: string;
  session_id: string;
  display_name: string;
  joined_at: string;
  is_organizer: boolean;
}

/**
 * Planning session
 * Requirements: 1.1, 1.2
 */
export interface PlanningSession {
  id: string;
  name: string;
  organizer_id: string;
  invite_token: string;
  invite_expires_at: string;
  invite_revoked: boolean;
  status: SessionStatus;
  created_at: string;
  updated_at: string;
  participant_ids: string[];
}

/**
 * Venue option for voting
 * Requirement: 2.1
 */
export interface VenueOption {
  id: string;
  session_id: string;
  place_id: string;
  name: string;
  address: string;
  rating?: number;
  price_level?: number;
  photo_url?: string;
  suggested_at: string;
  suggested_by: string;
}

/**
 * Vote on a venue
 * Requirement: 2.2
 */
export interface Vote {
  id: string;
  session_id: string;
  venue_id: string;
  participant_id: string;
  vote_type: VoteType;
  created_at: string;
  updated_at: string;
}

/**
 * Vote tally for a venue
 * Requirement: 2.4
 */
export interface VoteTally {
  venue_id: string;
  upvotes: number;
  downvotes: number;
  neutral: number;
  total: number;
  voters: Array<{
    participant_id: string;
    display_name: string;
    vote_type: VoteType;
  }>;
}

/**
 * Ranked venue with vote information
 * Requirement: 4.1
 */
export interface RankedVenue extends VenueOption {
  vote_tally: VoteTally;
  rank: number;
}

/**
 * Itinerary item
 * Requirement: 3.2
 */
export interface ItineraryItem {
  id: string;
  session_id: string;
  venue_id: string;
  venue: VenueOption;
  scheduled_time: string;
  added_at: string;
  added_by: string;
  order: number;
}

/**
 * Comment on a venue
 * Requirement: 6.1
 */
export interface Comment {
  id: string;
  session_id: string;
  venue_id: string;
  participant_id: string;
  participant_name: string;
  text: string;
  created_at: string;
}

/**
 * Session summary
 * Requirement: 4.5
 */
export interface SessionSummary {
  session_id: string;
  session_name: string;
  finalized_at: string;
  participants: Participant[];
  itinerary: ItineraryItem[];
  share_url: string;
}

/**
 * WebSocket event types for real-time updates
 * Requirement: 3.1
 */
export type SessionEventType =
  | 'participant_joined'
  | 'participant_left'
  | 'venue_added'
  | 'vote_cast'
  | 'itinerary_updated'
  | 'comment_added'
  | 'session_finalized';

export interface SessionEvent {
  type: SessionEventType;
  session_id: string;
  timestamp: string;
  data: unknown;
}

/**
 * API Request/Response types
 */

export interface CreateSessionRequest {
  name: string;
  organizer_id: string;
  expiry_hours?: number;
}

export interface CreateSessionResponse {
  session: PlanningSession;
  invite_url: string;
}

export interface JoinSessionRequest {
  display_name: string;
}

export interface JoinSessionResponse {
  participant: Participant;
  session: PlanningSession;
}

export interface CastVoteRequest {
  participant_id: string;
  vote_type: VoteType;
}

export interface AddToItineraryRequest {
  venue_id: string;
  scheduled_time: string;
  added_by: string;
}

export interface AddCommentRequest {
  participant_id: string;
  text: string;
}
