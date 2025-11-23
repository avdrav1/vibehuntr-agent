import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { fetchLinkPreviews, APIError } from './api';
import type { LinkMetadata } from '../types/linkPreview';

/**
 * Tests for link preview API client
 * Requirements: 3.1, 8.1
 */

// Mock fetch globally
const mockFetch = vi.fn();
globalThis.fetch = mockFetch;

describe('fetchLinkPreviews', () => {
  const API_BASE_URL = 'http://localhost:8000';
  const TEST_SESSION_ID = 'test-session-123';
  const TEST_URLS = ['https://example.com', 'https://test.com'];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Successful API call (Requirement 3.1)', () => {
    it('fetches link previews successfully', async () => {
      const mockMetadata: LinkMetadata[] = [
        {
          url: 'https://example.com',
          title: 'Example Domain',
          description: 'Example description',
          image: 'https://example.com/image.jpg',
          favicon: 'https://example.com/favicon.ico',
          domain: 'example.com',
        },
        {
          url: 'https://test.com',
          title: 'Test Site',
          description: 'Test description',
          domain: 'test.com',
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ previews: mockMetadata }),
      });

      const result = await fetchLinkPreviews(TEST_URLS, TEST_SESSION_ID);

      expect(mockFetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/link-preview`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            urls: TEST_URLS,
            session_id: TEST_SESSION_ID,
          }),
        }
      );

      expect(result).toEqual(mockMetadata);
    });

    it('returns empty array when no URLs provided', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ previews: [] }),
      });

      const result = await fetchLinkPreviews([], TEST_SESSION_ID);

      expect(result).toEqual([]);
    });

    it('handles partial metadata correctly', async () => {
      const mockMetadata: LinkMetadata[] = [
        {
          url: 'https://example.com',
          domain: 'example.com',
          // No title, description, image, or favicon
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ previews: mockMetadata }),
      });

      const result = await fetchLinkPreviews(['https://example.com'], TEST_SESSION_ID);

      expect(result).toEqual(mockMetadata);
      expect(result[0].title).toBeUndefined();
      expect(result[0].description).toBeUndefined();
    });
  });

  describe('Network error handling (Requirement 8.1)', () => {
    it('throws user-friendly error on network failure', async () => {
      mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));

      await expect(
        fetchLinkPreviews(TEST_URLS, TEST_SESSION_ID)
      ).rejects.toThrow('Network error: Unable to load link previews');
    });

    it('throws user-friendly error on connection refused', async () => {
      mockFetch.mockRejectedValueOnce(
        new TypeError('NetworkError when attempting to fetch resource')
      );

      await expect(
        fetchLinkPreviews(TEST_URLS, TEST_SESSION_ID)
      ).rejects.toThrow('Network error: Unable to load link previews');
    });
  });

  describe('Timeout handling (Requirement 8.1)', () => {
    it('throws user-friendly error on timeout', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 408,
        json: async () => ({ detail: 'Request timeout' }),
      });

      await expect(
        fetchLinkPreviews(TEST_URLS, TEST_SESSION_ID)
      ).rejects.toThrow('Request timeout');
    });

    it('throws user-friendly error on gateway timeout', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 504,
        json: async () => ({ detail: 'Gateway timeout' }),
      });

      await expect(
        fetchLinkPreviews(TEST_URLS, TEST_SESSION_ID)
      ).rejects.toThrow('Gateway timeout');
    });
  });

  describe('Error response handling (Requirement 8.1)', () => {
    it('throws APIError with status code on 4xx error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Invalid URLs provided' }),
      });

      try {
        await fetchLinkPreviews(TEST_URLS, TEST_SESSION_ID);
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(APIError);
        expect((error as APIError).status).toBe(400);
        expect((error as APIError).message).toBe('Invalid URLs provided');
      }
    });

    it('throws APIError with status code on 5xx error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Internal server error' }),
      });

      try {
        await fetchLinkPreviews(TEST_URLS, TEST_SESSION_ID);
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(APIError);
        expect((error as APIError).status).toBe(500);
        expect((error as APIError).message).toBe('Internal server error');
      }
    });

    it('handles error response without JSON body', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 503,
        json: async () => {
          throw new Error('Not JSON');
        },
      });

      await expect(
        fetchLinkPreviews(TEST_URLS, TEST_SESSION_ID)
      ).rejects.toThrow('Service unavailable');
    });

    it('handles 404 not found error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Endpoint not found' }),
      });

      try {
        await fetchLinkPreviews(TEST_URLS, TEST_SESSION_ID);
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(APIError);
        expect((error as APIError).status).toBe(404);
      }
    });

    it('handles rate limiting error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        json: async () => ({ detail: 'Too many requests' }),
      });

      await expect(
        fetchLinkPreviews(TEST_URLS, TEST_SESSION_ID)
      ).rejects.toThrow('Too many requests');
    });
  });

  describe('Response parsing', () => {
    it('handles malformed JSON response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => {
          throw new Error('Invalid JSON');
        },
      });

      await expect(
        fetchLinkPreviews(TEST_URLS, TEST_SESSION_ID)
      ).rejects.toThrow('Unable to process server response');
    });

    it('handles response with error field in metadata', async () => {
      const mockMetadata: LinkMetadata[] = [
        {
          url: 'https://example.com',
          domain: 'example.com',
          error: 'Failed to fetch metadata',
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ previews: mockMetadata }),
      });

      const result = await fetchLinkPreviews(['https://example.com'], TEST_SESSION_ID);

      expect(result[0].error).toBe('Failed to fetch metadata');
    });
  });
});
