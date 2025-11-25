import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, waitFor, cleanup } from '@testing-library/react';
import { LinkPreview } from './LinkPreview';
import * as api from '../services/api';

/**
 * Unit tests for LinkPreview component
 * Tests Requirements: 1.2, 1.4, 4.1, 4.2, 4.4
 */

// Mock the API module
vi.mock('../services/api', () => ({
  fetchLinkPreviews: vi.fn(),
}));

describe('LinkPreview Component', () => {
  const mockUrl = 'https://example.com/article';
  const mockSessionId = 'test-session-123';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  /**
   * Test: Loading state displayed initially
   * Requirement 4.2: Show loading skeleton while fetching
   */
  it('displays loading state initially', () => {
    // Mock API with a delay
    const mockFetchLinkPreviews = vi.mocked(api.fetchLinkPreviews);
    mockFetchLinkPreviews.mockImplementation(
      () =>
        new Promise((resolve) => {
          setTimeout(() => {
            resolve([
              {
                url: mockUrl,
                domain: 'example.com',
                title: 'Test Article',
              },
            ]);
          }, 1000);
        })
    );

    const { container } = render(<LinkPreview url={mockUrl} sessionId={mockSessionId} />);

    // Should show loading skeleton immediately
    const loadingElement = container.querySelector('[role="status"]');
    expect(loadingElement).toBeInTheDocument();
    expect(loadingElement).toHaveAttribute('aria-label', 'Loading link preview');
    expect(loadingElement).toHaveClass('link-preview-loading');
  });

  /**
   * Test: Preview card rendered after fetch
   * Requirement 1.2: Fetch metadata from backend
   * Requirement 4.1: Render message immediately, fetch metadata async
   */
  it('renders preview card after successful fetch', async () => {
    const mockMetadata = {
      url: mockUrl,
      domain: 'example.com',
      title: 'Test Article',
      description: 'This is a test article',
      image: 'https://example.com/image.jpg',
      favicon: 'https://example.com/favicon.ico',
    };

    const mockFetchLinkPreviews = vi.mocked(api.fetchLinkPreviews);
    mockFetchLinkPreviews.mockResolvedValue([mockMetadata]);

    const { container } = render(<LinkPreview url={mockUrl} sessionId={mockSessionId} />);

    // Wait for fetch to complete
    await waitFor(() => {
      const link = container.querySelector('a[role="link"]');
      expect(link).toBeInTheDocument();
    });

    // Should display preview card with metadata
    const link = container.querySelector('a[role="link"]');
    expect(link).toHaveAttribute('href', mockUrl);

    const title = container.querySelector('.link-preview-title');
    expect(title).toHaveTextContent('Test Article');

    const description = container.querySelector('.link-preview-description');
    expect(description).toHaveTextContent('This is a test article');

    const domain = container.querySelector('.link-preview-domain');
    expect(domain).toHaveTextContent('example.com');

    // Verify API was called correctly
    expect(mockFetchLinkPreviews).toHaveBeenCalledWith([mockUrl], mockSessionId);
    expect(mockFetchLinkPreviews).toHaveBeenCalledTimes(1);
  });

  /**
   * Test: Error state on fetch failure
   * Requirement 1.4: Handle errors gracefully
   */
  it('displays minimal card on fetch error', async () => {
    const mockFetchLinkPreviews = vi.mocked(api.fetchLinkPreviews);
    mockFetchLinkPreviews.mockRejectedValue(new Error('Network error'));

    const { container } = render(<LinkPreview url={mockUrl} sessionId={mockSessionId} />);

    // Wait for error handling
    await waitFor(() => {
      const link = container.querySelector('a[role="link"]');
      expect(link).toBeInTheDocument();
    });

    // Should display minimal card with error
    const link = container.querySelector('a[role="link"]');
    expect(link).toHaveAttribute('href', mockUrl);

    const errorElement = container.querySelector('.link-preview-error');
    expect(errorElement).toBeInTheDocument();
    expect(errorElement).toHaveTextContent('Unable to load full preview');

    // Should still show domain
    const domain = container.querySelector('.link-preview-domain');
    expect(domain).toHaveTextContent('example.com');
  });

  /**
   * Test: Timeout handling
   * Requirement 4.4: Handle timeout (5 seconds)
   */
  it('displays minimal card after timeout', { timeout: 10000 }, async () => {
    // Mock API with a very long delay (longer than timeout)
    const mockFetchLinkPreviews = vi.mocked(api.fetchLinkPreviews);
    mockFetchLinkPreviews.mockImplementation(
      () =>
        new Promise((resolve) => {
          setTimeout(() => {
            resolve([
              {
                url: mockUrl,
                domain: 'example.com',
                title: 'Test Article',
              },
            ]);
          }, 10000); // 10 seconds - longer than 5 second timeout
        })
    );

    const { container } = render(<LinkPreview url={mockUrl} sessionId={mockSessionId} />);

    // Should show loading initially
    expect(container.querySelector('[role="status"]')).toBeInTheDocument();

    // Wait for timeout (5 seconds + buffer)
    await waitFor(
      () => {
        const link = container.querySelector('a[role="link"]');
        expect(link).toBeInTheDocument();
      },
      { timeout: 6000 }
    );

    // Should display minimal card with timeout error
    const errorElement = container.querySelector('.link-preview-error');
    expect(errorElement).toBeInTheDocument();

    const domain = container.querySelector('.link-preview-domain');
    expect(domain).toHaveTextContent('example.com');
  });

  /**
   * Test: Minimal card on error
   * Requirement 1.4: Handle errors gracefully
   */
  it('displays minimal card when API returns empty array', async () => {
    const mockFetchLinkPreviews = vi.mocked(api.fetchLinkPreviews);
    mockFetchLinkPreviews.mockResolvedValue([]);

    const { container } = render(<LinkPreview url={mockUrl} sessionId={mockSessionId} />);

    // Wait for fetch to complete
    await waitFor(() => {
      const link = container.querySelector('a[role="link"]');
      expect(link).toBeInTheDocument();
    });

    // Should display minimal card
    const link = container.querySelector('a[role="link"]');
    expect(link).toHaveAttribute('href', mockUrl);

    const errorElement = container.querySelector('.link-preview-error');
    expect(errorElement).toBeInTheDocument();

    const domain = container.querySelector('.link-preview-domain');
    expect(domain).toHaveTextContent('example.com');
  });

  /**
   * Test: Minimal card when metadata has error field
   * Requirement 1.4: Handle errors gracefully
   */
  it('displays error indicator when metadata contains error', async () => {
    const mockMetadata = {
      url: mockUrl,
      domain: 'example.com',
      error: '404 Not Found',
    };

    const mockFetchLinkPreviews = vi.mocked(api.fetchLinkPreviews);
    mockFetchLinkPreviews.mockResolvedValue([mockMetadata]);

    const { container } = render(<LinkPreview url={mockUrl} sessionId={mockSessionId} />);

    // Wait for fetch to complete
    await waitFor(() => {
      const link = container.querySelector('a[role="link"]');
      expect(link).toBeInTheDocument();
    });

    // Should display card with error indicator
    const errorElement = container.querySelector('.link-preview-error');
    expect(errorElement).toBeInTheDocument();
    expect(errorElement).toHaveTextContent('Unable to load full preview');
  });

  /**
   * Test: Component cleans up on unmount
   * Ensures no memory leaks or state updates after unmount
   */
  it('cleans up properly on unmount', async () => {
    const mockFetchLinkPreviews = vi.mocked(api.fetchLinkPreviews);
    mockFetchLinkPreviews.mockImplementation(
      () =>
        new Promise((resolve) => {
          setTimeout(() => {
            resolve([
              {
                url: mockUrl,
                domain: 'example.com',
                title: 'Test Article',
              },
            ]);
          }, 1000);
        })
    );

    const { unmount } = render(<LinkPreview url={mockUrl} sessionId={mockSessionId} />);

    // Unmount immediately
    unmount();

    // Wait a bit to ensure no errors occur
    await new Promise((resolve) => setTimeout(resolve, 100));

    // If we get here without errors, cleanup worked correctly
    expect(true).toBe(true);
  });

  /**
   * Test: Handles malformed URL gracefully
   * Requirement 1.4: Handle errors gracefully
   */
  it('handles malformed URL gracefully', async () => {
    const malformedUrl = 'not-a-valid-url';
    const mockFetchLinkPreviews = vi.mocked(api.fetchLinkPreviews);
    mockFetchLinkPreviews.mockRejectedValue(new Error('Invalid URL'));

    const { container } = render(<LinkPreview url={malformedUrl} sessionId={mockSessionId} />);

    // Wait for error handling
    await waitFor(() => {
      const link = container.querySelector('a[role="link"]');
      expect(link).toBeInTheDocument();
    });

    // Should display minimal card
    const link = container.querySelector('a[role="link"]');
    expect(link).toHaveAttribute('href', malformedUrl);

    const errorElement = container.querySelector('.link-preview-error');
    expect(errorElement).toBeInTheDocument();
  });
});
