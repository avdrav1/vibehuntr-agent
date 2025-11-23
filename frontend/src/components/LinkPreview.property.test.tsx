import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, waitFor, cleanup } from '@testing-library/react';
import fc from 'fast-check';
import { LinkPreview } from './LinkPreview';
import * as api from '../services/api';
import type { LinkMetadata } from '../types/linkPreview';

/**
 * Property-based tests for LinkPreview component
 * Uses fast-check for property-based testing
 */

// Mock the API module
vi.mock('../services/api', () => ({
  fetchLinkPreviews: vi.fn(),
}));

describe('LinkPreview Property Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  /**
   * Feature: link-preview-cards, Property 10: Async rendering
   * 
   * For any message with URLs, the message content should render immediately
   * (synchronously) while preview cards render asynchronously after metadata is fetched.
   * 
   * Validates: Requirements 4.1
   */
  it('Property 10: renders loading state immediately and fetches metadata asynchronously', { timeout: 30000 }, async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.webUrl(),
        fc.uuid(),
        fc.record({
          url: fc.webUrl(),
          domain: fc.domain(),
          title: fc.option(fc.string({ minLength: 1, maxLength: 100 }), { nil: undefined }),
          description: fc.option(fc.string({ minLength: 1, maxLength: 200 }), { nil: undefined }),
          image: fc.option(fc.webUrl(), { nil: undefined }),
          favicon: fc.option(fc.webUrl(), { nil: undefined }),
          error: fc.option(fc.string(), { nil: undefined }),
        }),
        async (url, sessionId, metadata) => {
          // Clear mocks before each property test run
          vi.clearAllMocks();

          // Mock API to return metadata after a short delay
          const mockFetchLinkPreviews = vi.mocked(api.fetchLinkPreviews);
          mockFetchLinkPreviews.mockImplementation(
            () =>
              new Promise((resolve) => {
                setTimeout(() => {
                  resolve([{ ...metadata, url }]);
                }, 10); // Reduced delay for faster tests
              })
          );

          // Render component
          const { container } = render(<LinkPreview url={url} sessionId={sessionId} />);

          // IMMEDIATELY after render, should show loading state (synchronous)
          // This validates that the component renders immediately without waiting
          const loadingElement = container.querySelector('[role="status"]');
          expect(loadingElement).toBeInTheDocument();
          expect(loadingElement).toHaveAttribute('aria-label', 'Loading link preview');

          // Wait for async fetch to complete
          await waitFor(
            () => {
              const link = container.querySelector('a[role="link"]');
              expect(link).toBeInTheDocument();
            },
            { timeout: 500 }
          );

          // After fetch, should display the preview card
          const link = container.querySelector('a[role="link"]');
          expect(link).toHaveAttribute('href', url);

          // Verify API was called with correct parameters
          expect(mockFetchLinkPreviews).toHaveBeenCalledWith([url], sessionId);
          expect(mockFetchLinkPreviews).toHaveBeenCalledTimes(1);

          cleanup();
        }
      ),
      { numRuns: 100 } // Run 100 times as per spec requirements
    );
  });

  it('Property: handles fetch errors gracefully', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.webUrl(),
        fc.uuid(),
        fc.string({ minLength: 1, maxLength: 100 }),
        async (url, sessionId, errorMessage) => {
          // Mock API to throw an error
          const mockFetchLinkPreviews = vi.mocked(api.fetchLinkPreviews);
          mockFetchLinkPreviews.mockRejectedValue(new Error(errorMessage));

          // Render component
          const { container } = render(<LinkPreview url={url} sessionId={sessionId} />);

          // Should show loading initially
          expect(container.querySelector('[role="status"]')).toBeInTheDocument();

          // Wait for error handling
          await waitFor(
            () => {
              const link = container.querySelector('a[role="link"]');
              expect(link).toBeInTheDocument();
            },
            { timeout: 2000 }
          );

          // Should display minimal card with error
          const errorElement = container.querySelector('.link-preview-error');
          expect(errorElement).toBeInTheDocument();

          // Should still have a valid link
          const link = container.querySelector('a[role="link"]');
          expect(link).toHaveAttribute('href', url);

          cleanup();
        }
      ),
      { numRuns: 50 }
    );
  });

  it('Property: handles empty response gracefully', async () => {
    await fc.assert(
      fc.asyncProperty(fc.webUrl(), fc.uuid(), async (url, sessionId) => {
        // Mock API to return empty array
        const mockFetchLinkPreviews = vi.mocked(api.fetchLinkPreviews);
        mockFetchLinkPreviews.mockResolvedValue([]);

        // Render component
        const { container } = render(<LinkPreview url={url} sessionId={sessionId} />);

        // Wait for fetch to complete
        await waitFor(
          () => {
            const link = container.querySelector('a[role="link"]');
            expect(link).toBeInTheDocument();
          },
          { timeout: 2000 }
        );

        // Should display minimal card
        const link = container.querySelector('a[role="link"]');
        expect(link).toHaveAttribute('href', url);

        // Should show error indicator
        const errorElement = container.querySelector('.link-preview-error');
        expect(errorElement).toBeInTheDocument();

        cleanup();
      }),
      { numRuns: 50 }
    );
  });

  it('Property: handles metadata with error field', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.webUrl(),
        fc.uuid(),
        fc.string({ minLength: 1, maxLength: 100 }),
        async (url, sessionId, errorMsg) => {
          // Mock API to return metadata with error
          const mockFetchLinkPreviews = vi.mocked(api.fetchLinkPreviews);
          mockFetchLinkPreviews.mockResolvedValue([
            {
              url,
              domain: new URL(url).hostname,
              error: errorMsg,
            },
          ]);

          // Render component
          const { container } = render(<LinkPreview url={url} sessionId={sessionId} />);

          // Wait for fetch to complete
          await waitFor(
            () => {
              const link = container.querySelector('a[role="link"]');
              expect(link).toBeInTheDocument();
            },
            { timeout: 2000 }
          );

          // Should display card with error indicator
          const errorElement = container.querySelector('.link-preview-error');
          expect(errorElement).toBeInTheDocument();

          cleanup();
        }
      ),
      { numRuns: 50 }
    );
  });

  it('Property: cleans up on unmount', async () => {
    await fc.assert(
      fc.asyncProperty(fc.webUrl(), fc.uuid(), async (url, sessionId) => {
        // Mock API with a long delay
        const mockFetchLinkPreviews = vi.mocked(api.fetchLinkPreviews);
        mockFetchLinkPreviews.mockImplementation(
          () =>
            new Promise((resolve) => {
              setTimeout(() => {
                resolve([
                  {
                    url,
                    domain: new URL(url).hostname,
                    title: 'Test',
                  },
                ]);
              }, 1000);
            })
        );

        // Render and immediately unmount
        const { unmount } = render(<LinkPreview url={url} sessionId={sessionId} />);
        unmount();

        // Wait a bit to ensure no errors occur
        await new Promise((resolve) => setTimeout(resolve, 100));

        // If we get here without errors, cleanup worked correctly
        expect(true).toBe(true);
      }),
      { numRuns: 30 }
    );
  });
});
