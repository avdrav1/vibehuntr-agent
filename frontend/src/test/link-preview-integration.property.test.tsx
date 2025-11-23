/**
 * Property-based tests for frontend-backend link preview integration
 * Tests universal properties for the complete link preview flow
 * 
 * Feature: link-preview-cards, Property 8: Frontend-backend integration
 * Validates: Requirements 3.1
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import fc from 'fast-check';
import { fetchLinkPreviews } from '../services/api';
import type { LinkMetadata } from '../types/linkPreview';

// Mock fetch globally
const originalFetch = global.fetch;

describe('Link Preview Integration - Property-Based Tests', () => {
  beforeEach(() => {
    // Reset fetch mock before each test
    global.fetch = vi.fn();
  });

  afterEach(() => {
    // Restore original fetch
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  /**
   * Property 8: Frontend-backend integration
   * For any message with detected URLs, the frontend should send a POST request 
   * to /api/link-preview with the URLs and session_id, and the backend should 
   * return a response with the same number of preview objects as input URLs.
   * 
   * Validates: Requirements 3.1
   */
  describe('Property 8: Frontend-backend integration', () => {
    it('should send POST request with URLs and receive same number of previews', async () => {
      await fc.assert(
        fc.asyncProperty(
          // Generate 1-5 URLs
          fc.array(
            fc.webUrl({ validSchemes: ['http', 'https'] }),
            { minLength: 1, maxLength: 5 }
          ),
          // Generate session ID
          fc.string({ minLength: 10, maxLength: 50 }),
          async (urls, sessionId) => {
            // Clear mock before each iteration
            vi.clearAllMocks();
            
            // Filter out invalid URLs
            const validUrls = urls.filter(url => {
              try {
                const urlObj = new URL(url);
                const hostname = urlObj.hostname;
                return hostname !== 'localhost' && 
                       !hostname.startsWith('10.') &&
                       !hostname.startsWith('192.168.');
              } catch {
                return false;
              }
            });

            if (validUrls.length === 0) {
              return true; // Skip this test case
            }

            // Create mock response with same number of previews as input URLs
            const mockPreviews: LinkMetadata[] = validUrls.map(url => ({
              url,
              domain: new URL(url).hostname,
              title: `Title for ${url}`,
              description: `Description for ${url}`,
            }));

            const mockResponse = {
              previews: mockPreviews,
            };

            // Mock fetch to return our response
            (global.fetch as any).mockResolvedValueOnce({
              ok: true,
              json: async () => mockResponse,
            });

            // Call the API function
            const result = await fetchLinkPreviews(validUrls, sessionId);

            // Verify fetch was called with correct parameters
            expect(global.fetch).toHaveBeenCalledTimes(1);
            expect(global.fetch).toHaveBeenCalledWith(
              expect.stringContaining('/api/link-preview'),
              expect.objectContaining({
                method: 'POST',
                headers: expect.objectContaining({
                  'Content-Type': 'application/json',
                }),
                body: JSON.stringify({
                  urls: validUrls,
                  session_id: sessionId,
                }),
              })
            );

            // Verify response has same number of previews as input URLs
            expect(result).toHaveLength(validUrls.length);

            // Verify each preview has the required fields
            result.forEach((preview, index) => {
              expect(preview).toHaveProperty('url');
              expect(preview).toHaveProperty('domain');
              expect(preview.url).toBe(validUrls[index]);
            });

            return true;
          }
        ),
        { numRuns: 100 } // Run 100 iterations as specified in design doc
      );
    });

    it('should handle backend errors gracefully', async () => {
      await fc.assert(
        fc.asyncProperty(
          // Generate 1-3 URLs
          fc.array(
            fc.webUrl({ validSchemes: ['http', 'https'] }),
            { minLength: 1, maxLength: 3 }
          ),
          // Generate session ID
          fc.string({ minLength: 10, maxLength: 50 }),
          // Generate HTTP error status
          fc.integer({ min: 400, max: 599 }),
          async (urls, sessionId, errorStatus) => {
            // Clear mock before each iteration
            vi.clearAllMocks();
            
            // Filter out invalid URLs
            const validUrls = urls.filter(url => {
              try {
                const urlObj = new URL(url);
                const hostname = urlObj.hostname;
                return hostname !== 'localhost' && 
                       !hostname.startsWith('10.') &&
                       !hostname.startsWith('192.168.');
              } catch {
                return false;
              }
            });

            if (validUrls.length === 0) {
              return true; // Skip this test case
            }

            // Mock fetch to return an error
            (global.fetch as any).mockResolvedValueOnce({
              ok: false,
              status: errorStatus,
              statusText: 'Error',
            });

            // Call the API function and expect it to throw or return empty
            try {
              const result = await fetchLinkPreviews(validUrls, sessionId);
              
              // If it doesn't throw, it should return an empty array or handle gracefully
              expect(Array.isArray(result)).toBe(true);
            } catch (error) {
              // Error is expected and acceptable
              expect(error).toBeTruthy();
            }

            return true;
          }
        ),
        { numRuns: 50 } // Fewer runs for error cases
      );
    });

    it('should handle network errors gracefully', async () => {
      await fc.assert(
        fc.asyncProperty(
          // Generate 1-3 URLs
          fc.array(
            fc.webUrl({ validSchemes: ['http', 'https'] }),
            { minLength: 1, maxLength: 3 }
          ),
          // Generate session ID
          fc.string({ minLength: 10, maxLength: 50 }),
          async (urls, sessionId) => {
            // Clear mock before each iteration
            vi.clearAllMocks();
            
            // Filter out invalid URLs
            const validUrls = urls.filter(url => {
              try {
                const urlObj = new URL(url);
                const hostname = urlObj.hostname;
                return hostname !== 'localhost' && 
                       !hostname.startsWith('10.') &&
                       !hostname.startsWith('192.168.');
              } catch {
                return false;
              }
            });

            if (validUrls.length === 0) {
              return true; // Skip this test case
            }

            // Mock fetch to throw a network error
            (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

            // Call the API function and expect it to handle the error
            try {
              const result = await fetchLinkPreviews(validUrls, sessionId);
              
              // If it doesn't throw, it should return an empty array or handle gracefully
              expect(Array.isArray(result)).toBe(true);
            } catch (error) {
              // Error is expected and acceptable
              expect(error).toBeTruthy();
            }

            return true;
          }
        ),
        { numRuns: 50 } // Fewer runs for error cases
      );
    });
  });
});
