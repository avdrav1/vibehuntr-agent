/**
 * API Client Service
 * 
 * Provides functions to interact with the FastAPI backend.
 * Handles all HTTP requests and error handling for API endpoints.
 * 
 * Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 3.1, 8.1
 */

import type { 
  Message, 
  ChatRequest, 
  ChatResponse, 
  SessionResponse, 
  MessagesResponse,
  SessionSummary
} from '../types';
import type {
  LinkPreviewRequest,
  LinkPreviewResponse,
  LinkMetadata
} from '../types/linkPreview';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Custom error class for API errors
 */
export class APIError extends Error {
  status?: number;
  details?: unknown;

  constructor(
    message: string,
    status?: number,
    details?: unknown
  ) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.details = details;
  }
}

/**
 * Handle API response and throw errors if needed
 * Provides user-friendly error messages (Requirement 8.1)
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage: string;
    let errorDetails: unknown;

    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || getStatusMessage(response.status);
      errorDetails = errorData;
    } catch {
      // If response is not JSON, use user-friendly status message
      errorMessage = getStatusMessage(response.status);
    }

    throw new APIError(errorMessage, response.status, errorDetails);
  }

  // Handle empty responses (e.g., 204 No Content)
  if (response.status === 204) {
    return {} as T;
  }

  try {
    return await response.json();
  } catch {
    throw new APIError('Unable to process server response. Please try again.', response.status);
  }
}

/**
 * Get user-friendly error message based on HTTP status code
 * Requirement 8.1: Display user-friendly error messages
 */
function getStatusMessage(status: number): string {
  switch (status) {
    case 400:
      return 'Invalid request. Please check your input and try again.';
    case 401:
      return 'Authentication required. Please log in.';
    case 403:
      return 'Access denied. You do not have permission to perform this action.';
    case 404:
      return 'Resource not found. The requested item does not exist.';
    case 408:
      return 'Request timeout. The server took too long to respond.';
    case 429:
      return 'Too many requests. Please wait a moment and try again.';
    case 500:
      return 'Server error. Something went wrong on our end. Please try again later.';
    case 502:
      return 'Bad gateway. The server is temporarily unavailable.';
    case 503:
      return 'Service unavailable. The server is temporarily down for maintenance.';
    case 504:
      return 'Gateway timeout. The server took too long to respond.';
    default:
      return `An error occurred (${status}). Please try again.`;
  }
}

/**
 * Send a message and get complete response (non-streaming)
 * 
 * POST /api/chat
 * Requirement: 4.1, 8.1
 */
export async function sendMessage(request: ChatRequest): Promise<ChatResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    return await handleResponse<ChatResponse>(response);
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    // Handle network errors with user-friendly messages (Requirement 8.1)
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError('Network error: Unable to reach the server. Please check your connection.');
    }
    throw new APIError(
      error instanceof Error ? error.message : 'Unable to send message. Please try again.'
    );
  }
}

/**
 * Create an EventSource for streaming chat responses
 * 
 * GET /api/chat/stream
 * Requirement: 4.2
 * 
 * @returns EventSource instance for SSE streaming
 */
export function createStreamingConnection(
  sessionId: string,
  message: string
): EventSource {
  const params = new URLSearchParams({
    session_id: sessionId,
    message: message,
  });

  const url = `${API_BASE_URL}/api/chat/stream?${params.toString()}`;
  return new EventSource(url);
}

/**
 * Get all messages for a session
 * 
 * GET /api/sessions/{session_id}/messages
 * Requirement: 4.3, 8.1
 */
export async function getSessionMessages(sessionId: string): Promise<Message[]> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/sessions/${sessionId}/messages`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    const data = await handleResponse<MessagesResponse>(response);
    return data.messages;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    // Handle network errors with user-friendly messages (Requirement 8.1)
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError('Network error: Unable to reach the server. Please check your connection.');
    }
    throw new APIError(
      error instanceof Error ? error.message : 'Unable to load message history. Please try again.'
    );
  }
}

/**
 * Get all sessions for the user
 * 
 * GET /api/sessions
 * Requirement: 1.1, 1.4
 */
export async function getSessions(): Promise<SessionSummary[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/sessions`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const data = await handleResponse<{ sessions: SessionSummary[] }>(response);
    return data.sessions;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    // Handle network errors with user-friendly messages (Requirement 8.1)
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError('Network error: Unable to reach the server. Please check your connection.');
    }
    throw new APIError(
      error instanceof Error ? error.message : 'Unable to load sessions. Please try again.'
    );
  }
}

/**
 * Delete a session
 * 
 * DELETE /api/sessions/{session_id}
 * Requirement: 1.6
 */
export async function deleteSession(sessionId: string): Promise<boolean> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/sessions/${sessionId}`,
      {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    const data = await handleResponse<{ success: boolean }>(response);
    return data.success;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    // Handle network errors with user-friendly messages (Requirement 8.1)
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError('Network error: Unable to reach the server. Please check your connection.');
    }
    throw new APIError(
      error instanceof Error ? error.message : 'Unable to delete session. Please try again.'
    );
  }
}

/**
 * Create a new session
 * 
 * POST /api/sessions
 * Requirement: 4.4, 8.1
 */
export async function createSession(): Promise<string> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/sessions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const data = await handleResponse<SessionResponse>(response);
    return data.session_id;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    // Handle network errors with user-friendly messages (Requirement 8.1)
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError('Network error: Unable to reach the server. Please check your connection.');
    }
    throw new APIError(
      error instanceof Error ? error.message : 'Unable to create a new session. Please refresh the page.'
    );
  }
}

/**
 * Clear a session's history
 * 
 * DELETE /api/sessions/{session_id}
 * Requirement: 4.5, 8.1
 */
export async function clearSession(sessionId: string): Promise<void> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/sessions/${sessionId}`,
      {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    await handleResponse<{ status: string }>(response);
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    // Handle network errors with user-friendly messages (Requirement 8.1)
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError('Network error: Unable to reach the server. Please check your connection.');
    }
    throw new APIError(
      error instanceof Error ? error.message : 'Unable to clear the session. Please try again.'
    );
  }
}

/**
 * Health check endpoint
 * 
 * GET /health
 */
export async function healthCheck(): Promise<{ status: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
    });

    return await handleResponse<{ status: string }>(response);
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    throw new APIError(
      `Health check failed: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

/**
 * Fetch context for a session
 * 
 * GET /api/context/{session_id}
 * Requirement: 11.2
 */
export async function fetchContext(sessionId: string): Promise<import('../types').ContextResponse> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/context/${sessionId}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    return await handleResponse<import('../types').ContextResponse>(response);
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError('Network error: Unable to reach the server. Please check your connection.');
    }
    throw new APIError(
      error instanceof Error ? error.message : 'Unable to load context. Please try again.'
    );
  }
}

/**
 * Clear all context for a session
 * 
 * DELETE /api/context/{session_id}
 * Requirement: 11.6
 */
export async function clearContext(sessionId: string): Promise<void> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/context/${sessionId}`,
      {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    await handleResponse<{ success: boolean }>(response);
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError('Network error: Unable to reach the server. Please check your connection.');
    }
    throw new APIError(
      error instanceof Error ? error.message : 'Unable to clear context. Please try again.'
    );
  }
}

/**
 * Clear a specific context item
 * 
 * DELETE /api/context/{session_id}/item
 * Requirement: 11.6
 */
export async function clearContextItem(
  sessionId: string,
  itemType: 'location' | 'query' | 'venue' | 'user_name' | 'user_email',
  index?: number
): Promise<void> {
  try {
    const params = new URLSearchParams({ item_type: itemType });
    if (index !== undefined) {
      params.append('index', index.toString());
    }

    const response = await fetch(
      `${API_BASE_URL}/api/context/${sessionId}/item?${params.toString()}`,
      {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    await handleResponse<{ success: boolean }>(response);
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError('Network error: Unable to reach the server. Please check your connection.');
    }
    throw new APIError(
      error instanceof Error ? error.message : 'Unable to clear context item. Please try again.'
    );
  }
}

/**
 * Fetch link preview metadata for one or more URLs
 * 
 * POST /api/link-preview
 * Requirements: 3.1, 8.1
 * 
 * @param urls - Array of URLs to fetch metadata for
 * @param sessionId - Session ID for potential caching
 * @returns Array of LinkMetadata objects
 */
export async function fetchLinkPreviews(
  urls: string[],
  sessionId: string
): Promise<LinkMetadata[]> {
  try {
    const request: LinkPreviewRequest = {
      urls,
      session_id: sessionId,
    };

    const response = await fetch(`${API_BASE_URL}/api/link-preview`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    const data = await handleResponse<LinkPreviewResponse>(response);
    return data.previews;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    // Handle network errors with user-friendly messages (Requirement 8.1)
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError('Network error: Unable to load link previews. Please check your connection.');
    }
    throw new APIError(
      error instanceof Error ? error.message : 'Unable to load link previews. Please try again.'
    );
  }
}
