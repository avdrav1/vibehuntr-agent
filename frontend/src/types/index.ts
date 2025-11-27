/**
 * TypeScript type definitions for the Vibehuntr React frontend
 */

/**
 * Represents a single message in the chat conversation
 */
export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

/**
 * Represents the overall chat state
 */
export interface ChatState {
  messages: Message[];
  sessionId: string;
  isStreaming: boolean;
}

/**
 * Request payload for sending a chat message
 */
export interface ChatRequest {
  session_id: string;
  message: string;
}

/**
 * Response from the non-streaming chat endpoint
 */
export interface ChatResponse {
  response: string;
}

/**
 * Response from session creation endpoint
 */
export interface SessionResponse {
  session_id: string;
}

/**
 * Response from get messages endpoint
 */
export interface MessagesResponse {
  messages: Message[];
}

/**
 * SSE event types for streaming
 */
export interface StreamTokenEvent {
  type: 'token';
  content: string;
}

export interface StreamDoneEvent {
  type: 'done';
}

export interface StreamErrorEvent {
  type: 'error';
  message: string;
}

export type StreamEvent = StreamTokenEvent | StreamDoneEvent | StreamErrorEvent;

/**
 * Error response from API
 */
export interface ErrorResponse {
  detail: string;
}

/**
 * Venue information in context
 */
export interface VenueInfo {
  name: string;
  place_id: string;
  location?: string;
}

/**
 * Conversation context tracked by the agent
 */
export interface ConversationContext {
  user_name?: string;
  user_email?: string;
  location?: string;
  search_query?: string;
  event_venue_name?: string;
  event_date_time?: string;
  event_party_size?: number;
  recent_venues: VenueInfo[];
}

/**
 * Response from context API endpoint
 */
export interface ContextResponse {
  user_name?: string;
  user_email?: string;
  location?: string;
  search_query?: string;
  event_venue_name?: string;
  event_date_time?: string;
  event_party_size?: number;
  recent_venues: VenueInfo[];
}

/**
 * Link preview types - re-exported from linkPreview.ts for convenience
 */
export type {
  LinkMetadata,
  LinkPreviewRequest,
  LinkPreviewResponse,
  ExtractedURL
} from './linkPreview';

/**
 * Planning session types - re-exported from planningSession.ts for convenience
 */
export type {
  SessionStatus,
  VoteType,
  Participant,
  PlanningSession,
  VenueOption,
  Vote,
  VoteTally,
  RankedVenue,
  ItineraryItem,
  Comment,
  SessionSummary,
  SessionEventType,
  SessionEvent,
  CreateSessionRequest,
  CreateSessionResponse,
  JoinSessionRequest,
  JoinSessionResponse,
  CastVoteRequest,
  AddToItineraryRequest,
  AddCommentRequest,
} from './planningSession';
