/**
 * TypeScript type definitions for link preview functionality
 */

/**
 * Metadata extracted from a URL
 */
export interface LinkMetadata {
  url: string;
  title?: string;
  description?: string;
  image?: string;
  favicon?: string;
  domain: string;
  error?: string;
}

/**
 * Request payload for link preview endpoint
 */
export interface LinkPreviewRequest {
  urls: string[];
  session_id: string;
}

/**
 * Response from link preview endpoint
 */
export interface LinkPreviewResponse {
  previews: LinkMetadata[];
}

/**
 * Represents a URL extracted from message text with position information
 */
export interface ExtractedURL {
  url: string;
  startIndex: number;
  endIndex: number;
}
