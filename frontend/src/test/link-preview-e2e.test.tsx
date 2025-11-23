/**
 * End-to-end integration tests for link preview feature
 * 
 * Tests the complete flow from message with URL to preview card display:
 * 1. URL extraction from message
 * 2. API call to backend
 * 3. Metadata fetch and parse
 * 4. Preview card rendering
 * 
 * Requirements: 1.1, 1.2, 1.3, 3.1, 3.2, 3.3, 3.4
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { Message } from '../components/Message';
import * as api from '../services/api';
import type { LinkMetadata } from '../types/linkPreview';
import type { Message as MessageType } from '../types';

// Mock the API module
vi.mock('../services/api');

describe('Link Preview End-to-End Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // Helper function to create message object
  const createMessage = (role: 'user' | 'assistant', content: string, timestamp?: string): MessageType => ({
    role,
    content,
    timestamp: timestamp || '2024-01-01T10:00:00Z',
  });

  /**
   * Test complete flow: message with URL → extraction → API call → metadata → preview card
   * Requirements: 1.1, 1.2, 1.3, 3.1, 3.2, 3.3, 3.4
   */
  describe('Complete Link Preview Flow', () => {
    it('should extract URL, fetch metadata, and render preview card', async () => {
      // Step 1: Create message with URL
      const messageContent = 'Check out this website: https://example.com';
      const sessionId = 'test-session-123';

      // Step 2: Mock API response with metadata
      const mockMetadata: LinkMetadata = {
        url: 'https://example.com',
        title: 'Example Domain',
        description: 'This domain is for use in illustrative examples',
        image: 'https://example.com/image.jpg',
        favicon: 'https://example.com/favicon.ico',
        domain: 'example.com',
      };

      vi.mocked(api.fetchLinkPreviews).mockResolvedValue([mockMetadata]);

      // Step 3: Render message component
      const message = createMessage('assistant', messageContent);

      render(
        <Message
          message={message}
          sessionId={sessionId}
        />
      );

      // Step 4: Verify URL extraction - message content should be displayed
      expect(screen.getByText(/Check out this website:/)).toBeInTheDocument();

      // Step 5: Verify API was called with correct parameters
      await waitFor(() => {
        expect(api.fetchLinkPreviews).toHaveBeenCalledWith(
          ['https://example.com'],
          sessionId
        );
      });

      // Step 6: Verify preview card is rendered with metadata
      await waitFor(() => {
        expect(screen.getByText('Example Domain')).toBeInTheDocument();
      });

      expect(screen.getByText('This domain is for use in illustrative examples')).toBeInTheDocument();
      expect(screen.getByText('example.com')).toBeInTheDocument();

      // Step 7: Verify image is rendered
      const image = screen.getByAltText('Preview image for Example Domain');
      expect(image).toBeInTheDocument();
      expect(image).toHaveAttribute('src', 'https://example.com/image.jpg');

      // Step 8: Verify link has correct attributes
      const link = screen.getByRole('link', { name: /Example Domain/ });
      expect(link).toHaveAttribute('href', 'https://example.com');
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('should handle multiple URLs in a single message', async () => {
      // Message with multiple URLs
      const messageContent = 'Check these sites: https://example.com and https://test.org';
      const sessionId = 'test-session-456';

      // Mock API to return different metadata based on URL
      vi.mocked(api.fetchLinkPreviews).mockImplementation(async (urls: string[]) => {
        const url = urls[0]; // Each LinkPreview calls with a single URL
        if (url === 'https://example.com') {
          return [{
            url: 'https://example.com',
            title: 'Example Site',
            description: 'First site',
            domain: 'example.com',
          }];
        } else if (url === 'https://test.org') {
          return [{
            url: 'https://test.org',
            title: 'Test Site',
            description: 'Second site',
            domain: 'test.org',
          }];
        }
        return [];
      });

      const message = createMessage('assistant', messageContent);

      render(
        <Message
          message={message}
          sessionId={sessionId}
        />
      );

      // Verify both URLs were extracted and sent to API
      await waitFor(() => {
        expect(api.fetchLinkPreviews).toHaveBeenCalledTimes(2);
        const calls = vi.mocked(api.fetchLinkPreviews).mock.calls;
        const allUrls = calls.flatMap(call => call[0]);
        expect(allUrls).toContain('https://example.com');
        expect(allUrls).toContain('https://test.org');
      });

      // Verify both preview cards are rendered
      await waitFor(() => {
        expect(screen.getByText('Example Site')).toBeInTheDocument();
        expect(screen.getByText('Test Site')).toBeInTheDocument();
      });

      expect(screen.getByText('First site')).toBeInTheDocument();
      expect(screen.getByText('Second site')).toBeInTheDocument();
    });

    it('should handle metadata fetch with partial data', async () => {
      // Message with URL
      const messageContent = 'Visit https://minimal.com';
      const sessionId = 'test-session-789';

      // Mock metadata with only required fields (no image, no description)
      const mockMetadata: LinkMetadata = {
        url: 'https://minimal.com',
        title: 'Minimal Site',
        domain: 'minimal.com',
      };

      vi.mocked(api.fetchLinkPreviews).mockResolvedValue([mockMetadata]);

      const message = createMessage('assistant', messageContent);

      render(
        <Message
          message={message}
          sessionId={sessionId}
        />
      );

      // Verify preview card renders with available data
      await waitFor(() => {
        expect(screen.getByText('Minimal Site')).toBeInTheDocument();
      });

      expect(screen.getByText('minimal.com')).toBeInTheDocument();

      // Verify fallback icon is shown instead of image
      const fallbackIcon = screen.getByRole('img', { name: 'Link icon' });
      expect(fallbackIcon).toBeInTheDocument();
    });

    it('should handle metadata fetch errors gracefully', async () => {
      // Message with URL
      const messageContent = 'Check https://error.com';
      const sessionId = 'test-session-error';

      // Mock API to return error metadata
      const mockMetadata: LinkMetadata = {
        url: 'https://error.com',
        domain: 'error.com',
        error: 'Failed to fetch metadata',
      };

      vi.mocked(api.fetchLinkPreviews).mockResolvedValue([mockMetadata]);

      const message = createMessage('assistant', messageContent);

      render(
        <Message
          message={message}
          sessionId={sessionId}
        />
      );

      // Verify minimal preview card is rendered (domain appears in both title and footer)
      await waitFor(() => {
        const domainElements = screen.getAllByText('error.com');
        expect(domainElements.length).toBeGreaterThan(0);
      });

      // Verify error message is shown
      expect(screen.getByRole('alert')).toHaveTextContent('Unable to load full preview');
    });

    it('should show loading state before metadata arrives', async () => {
      // Message with URL
      const messageContent = 'Loading test: https://slow.com';
      const sessionId = 'test-session-loading';

      // Mock API with delayed response
      let resolveMetadata: (value: LinkMetadata[]) => void;
      const metadataPromise = new Promise<LinkMetadata[]>((resolve) => {
        resolveMetadata = resolve;
      });

      vi.mocked(api.fetchLinkPreviews).mockReturnValue(metadataPromise);

      const message = createMessage('assistant', messageContent);

      render(
        <Message
          message={message}
          sessionId={sessionId}
        />
      );

      // Verify loading skeleton is shown
      await waitFor(() => {
        const loadingElement = screen.getByRole('status', { name: 'Loading link preview' });
        expect(loadingElement).toBeInTheDocument();
      });

      // Resolve the metadata
      const mockMetadata: LinkMetadata = {
        url: 'https://slow.com',
        title: 'Slow Site',
        description: 'Finally loaded',
        domain: 'slow.com',
      };

      resolveMetadata!([mockMetadata]);

      // Verify preview card replaces loading state
      await waitFor(() => {
        expect(screen.getByText('Slow Site')).toBeInTheDocument();
      });

      expect(screen.getByText('Finally loaded')).toBeInTheDocument();

      // Loading skeleton should be gone
      expect(screen.queryByRole('status', { name: 'Loading link preview' })).not.toBeInTheDocument();
    });

    it('should not create preview for excluded URLs (venue links)', async () => {
      // Message with venue link pattern (actual format used by the agent)
      const messageContent = `**Venue Name**
📍 Address: 123 Main St
🌐 Website: https://example.com/venue
🆔 Place ID: ChIJabcdef123456`;
      const sessionId = 'test-session-venue';

      // Mock API should not be called for venue links
      vi.mocked(api.fetchLinkPreviews).mockResolvedValue([]);

      const message = createMessage('assistant', messageContent);

      render(
        <Message
          message={message}
          sessionId={sessionId}
        />
      );

      // Wait a bit to ensure no API call is made
      await new Promise(resolve => setTimeout(resolve, 100));

      // Verify API was not called (venue links are excluded)
      expect(api.fetchLinkPreviews).not.toHaveBeenCalled();
      
      // Verify venue link button is shown instead
      expect(screen.getByRole('link', { name: /Visit Venue Name/ })).toBeInTheDocument();
    });

    it('should not create preview for localhost URLs', async () => {
      // Message with localhost URL
      const messageContent = 'Local dev: http://localhost:3000';
      const sessionId = 'test-session-localhost';

      // Mock API should not be called for localhost
      vi.mocked(api.fetchLinkPreviews).mockResolvedValue([]);

      const message = createMessage('assistant', messageContent);

      render(
        <Message
          message={message}
          sessionId={sessionId}
        />
      );

      // Wait a bit to ensure no API call is made
      await new Promise(resolve => setTimeout(resolve, 100));

      // Verify API was not called (localhost is excluded)
      expect(api.fetchLinkPreviews).not.toHaveBeenCalled();
    });

    it('should handle network errors during metadata fetch', async () => {
      // Message with URL
      const messageContent = 'Network error test: https://network-error.com';
      const sessionId = 'test-session-network-error';

      // Mock API to throw network error
      vi.mocked(api.fetchLinkPreviews).mockRejectedValue(new Error('Network error'));

      const message = createMessage('assistant', messageContent);

      render(
        <Message
          message={message}
          sessionId={sessionId}
        />
      );

      // Wait for error handling
      await waitFor(() => {
        expect(api.fetchLinkPreviews).toHaveBeenCalled();
      });

      // Component should handle error gracefully - no preview card shown
      // Message content should still be visible
      expect(screen.getByText(/Network error test:/)).toBeInTheDocument();
    });

    it('should render preview cards in order of URL appearance', async () => {
      // Message with multiple URLs
      const messageContent = 'First: https://first.com, Second: https://second.com, Third: https://third.com';
      const sessionId = 'test-session-order';

      // Mock API to return different metadata based on URL
      vi.mocked(api.fetchLinkPreviews).mockImplementation(async (urls: string[]) => {
        const url = urls[0]; // Each LinkPreview calls with a single URL
        if (url === 'https://first.com') {
          return [{
            url: 'https://first.com',
            title: 'First Site',
            domain: 'first.com',
          }];
        } else if (url === 'https://second.com') {
          return [{
            url: 'https://second.com',
            title: 'Second Site',
            domain: 'second.com',
          }];
        } else if (url === 'https://third.com') {
          return [{
            url: 'https://third.com',
            title: 'Third Site',
            domain: 'third.com',
          }];
        }
        return [];
      });

      const message = createMessage('assistant', messageContent);

      render(
        <Message
          message={message}
          sessionId={sessionId}
        />
      );

      // Wait for all preview cards to render
      await waitFor(() => {
        expect(screen.getByText('First Site')).toBeInTheDocument();
        expect(screen.getByText('Second Site')).toBeInTheDocument();
        expect(screen.getByText('Third Site')).toBeInTheDocument();
      });

      // Verify order by checking preview card links (filter out venue links if any)
      const previewCards = screen.getAllByRole('link').filter(link => 
        link.getAttribute('aria-label')?.startsWith('Link preview:')
      );
      expect(previewCards.length).toBe(3);
      expect(previewCards[0]).toHaveTextContent('First Site');
      expect(previewCards[1]).toHaveTextContent('Second Site');
      expect(previewCards[2]).toHaveTextContent('Third Site');
    });

    it('should handle URLs with query parameters and fragments', async () => {
      // Message with complex URL
      const messageContent = 'Complex URL: https://example.com/path?query=value&foo=bar#section';
      const sessionId = 'test-session-complex';

      // Mock metadata
      const mockMetadata: LinkMetadata = {
        url: 'https://example.com/path?query=value&foo=bar#section',
        title: 'Complex URL Site',
        description: 'Site with query params',
        domain: 'example.com',
      };

      vi.mocked(api.fetchLinkPreviews).mockResolvedValue([mockMetadata]);

      const message = createMessage('assistant', messageContent);

      render(
        <Message
          message={message}
          sessionId={sessionId}
        />
      );

      // Verify URL was extracted correctly
      await waitFor(() => {
        expect(api.fetchLinkPreviews).toHaveBeenCalledWith(
          ['https://example.com/path?query=value&foo=bar#section'],
          sessionId
        );
      });

      // Verify preview card renders
      await waitFor(() => {
        expect(screen.getByText('Complex URL Site')).toBeInTheDocument();
      });
    });

    it('should handle message with no URLs', async () => {
      // Message without URLs
      const messageContent = 'This message has no URLs at all';
      const sessionId = 'test-session-no-urls';

      const message = createMessage('assistant', messageContent);

      render(
        <Message
          message={message}
          sessionId={sessionId}
        />
      );

      // Wait a bit to ensure no API call is made
      await new Promise(resolve => setTimeout(resolve, 100));

      // Verify API was not called
      expect(api.fetchLinkPreviews).not.toHaveBeenCalled();

      // Verify message content is displayed
      expect(screen.getByText('This message has no URLs at all')).toBeInTheDocument();
    });

    it('should handle user messages (no preview for user messages)', async () => {
      // User message with URL
      const messageContent = 'User sent: https://example.com';
      const sessionId = 'test-session-user';

      const message = createMessage('user', messageContent);

      render(
        <Message
          message={message}
          sessionId={sessionId}
        />
      );

      // Wait a bit to ensure no API call is made
      await new Promise(resolve => setTimeout(resolve, 100));

      // Verify API was not called (only assistant messages get previews)
      expect(api.fetchLinkPreviews).not.toHaveBeenCalled();

      // Verify message content is displayed
      expect(screen.getByText(/User sent:/)).toBeInTheDocument();
    });
  });

  /**
   * Test mock HTTP responses for backend simulation
   * Requirements: 3.2, 3.3, 3.4
   */
  describe('Mock HTTP Response Handling', () => {
    it('should handle successful HTTP 200 response with full metadata', async () => {
      const messageContent = 'Test: https://success.com';
      const sessionId = 'test-session-http-200';

      // Mock successful response with all fields
      const mockMetadata: LinkMetadata = {
        url: 'https://success.com',
        title: 'Success Page',
        description: 'Successfully fetched metadata',
        image: 'https://success.com/og-image.jpg',
        favicon: 'https://success.com/favicon.ico',
        domain: 'success.com',
      };

      vi.mocked(api.fetchLinkPreviews).mockResolvedValue([mockMetadata]);

      const message = createMessage('assistant', messageContent);

      render(
        <Message
          message={message}
          sessionId={sessionId}
        />
      );

      // Verify all metadata fields are rendered
      await waitFor(() => {
        expect(screen.getByText('Success Page')).toBeInTheDocument();
      });

      expect(screen.getByText('Successfully fetched metadata')).toBeInTheDocument();
      expect(screen.getByText('success.com')).toBeInTheDocument();

      const image = screen.getByAltText('Preview image for Success Page');
      expect(image).toHaveAttribute('src', 'https://success.com/og-image.jpg');
    });

    it('should handle HTTP 404 response', async () => {
      const messageContent = 'Not found: https://notfound.com';
      const sessionId = 'test-session-http-404';

      // Mock 404 error response
      const mockMetadata: LinkMetadata = {
        url: 'https://notfound.com',
        domain: 'notfound.com',
        error: '404 Not Found',
      };

      vi.mocked(api.fetchLinkPreviews).mockResolvedValue([mockMetadata]);

      const message = createMessage('assistant', messageContent);

      render(
        <Message
          message={message}
          sessionId={sessionId}
        />
      );

      // Verify minimal card is shown (domain appears in both title and footer)
      await waitFor(() => {
        const domainElements = screen.getAllByText('notfound.com');
        expect(domainElements.length).toBeGreaterThan(0);
      });

      // Verify error message is shown
      expect(screen.getByRole('alert')).toHaveTextContent('Unable to load full preview');
    });

    it('should handle HTTP 500 server error', async () => {
      const messageContent = 'Server error: https://servererror.com';
      const sessionId = 'test-session-http-500';

      // Mock 500 error response
      const mockMetadata: LinkMetadata = {
        url: 'https://servererror.com',
        domain: 'servererror.com',
        error: '500 Internal Server Error',
      };

      vi.mocked(api.fetchLinkPreviews).mockResolvedValue([mockMetadata]);

      const message = createMessage('assistant', messageContent);

      render(
        <Message
          message={message}
          sessionId={sessionId}
        />
      );

      // Verify minimal card is shown (domain appears in both title and footer)
      await waitFor(() => {
        const domainElements = screen.getAllByText('servererror.com');
        expect(domainElements.length).toBeGreaterThan(0);
      });
      
      // Verify error message is shown
      expect(screen.getByRole('alert')).toHaveTextContent('Unable to load full preview');
    });

    it('should handle timeout response', async () => {
      const messageContent = 'Timeout: https://timeout.com';
      const sessionId = 'test-session-timeout';

      // Mock timeout error
      const mockMetadata: LinkMetadata = {
        url: 'https://timeout.com',
        domain: 'timeout.com',
        error: 'Request timeout',
      };

      vi.mocked(api.fetchLinkPreviews).mockResolvedValue([mockMetadata]);

      const message = createMessage('assistant', messageContent);

      render(
        <Message
          message={message}
          sessionId={sessionId}
        />
      );

      // Verify minimal card is shown (domain appears in both title and footer)
      await waitFor(() => {
        const domainElements = screen.getAllByText('timeout.com');
        expect(domainElements.length).toBeGreaterThan(0);
      });
      
      // Verify error message is shown
      expect(screen.getByRole('alert')).toHaveTextContent('Unable to load full preview');
    });

    it('should handle malformed HTML response', async () => {
      const messageContent = 'Malformed: https://malformed.com';
      const sessionId = 'test-session-malformed';

      // Mock response with partial metadata (parsing succeeded partially)
      const mockMetadata: LinkMetadata = {
        url: 'https://malformed.com',
        title: 'Malformed Site',
        domain: 'malformed.com',
        // No description or image due to malformed HTML
      };

      vi.mocked(api.fetchLinkPreviews).mockResolvedValue([mockMetadata]);

      const message = createMessage('assistant', messageContent);

      render(
        <Message
          message={message}
          sessionId={sessionId}
        />
      );

      // Verify partial metadata is rendered
      await waitFor(() => {
        expect(screen.getByText('Malformed Site')).toBeInTheDocument();
      });

      expect(screen.getByText('malformed.com')).toBeInTheDocument();
    });
  });
});
