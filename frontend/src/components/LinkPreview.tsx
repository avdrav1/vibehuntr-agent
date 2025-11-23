import { useState, useEffect } from 'react';
import { PreviewCard } from './PreviewCard';
import { fetchLinkPreviews } from '../services/api';
import type { LinkMetadata } from '../types/linkPreview';

interface LinkPreviewProps {
  url: string;
  sessionId: string;
}

/**
 * LinkPreview component fetches metadata and manages state for link preview cards
 * Implements Requirements:
 * - 1.2: Fetch metadata from backend
 * - 1.4: Handle errors gracefully
 * - 4.1: Render message immediately, fetch metadata async
 * - 4.2: Show loading skeleton while fetching
 * - 4.4: Handle timeout (5 seconds)
 */
export function LinkPreview({ url, sessionId }: LinkPreviewProps) {
  const [metadata, setMetadata] = useState<LinkMetadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let isMounted = true;
    let timeoutId: NodeJS.Timeout;

    const fetchMetadata = async () => {
      try {
        // Set timeout to show minimal card after 5 seconds (Requirement 4.4)
        timeoutId = setTimeout(() => {
          if (isMounted) {
            setLoading(false);
            setError(true);
            setMetadata({
              url,
              domain: new URL(url).hostname,
              error: 'Request timed out',
            });
          }
        }, 5000);

        // Fetch metadata from backend (Requirement 1.2)
        const previews = await fetchLinkPreviews([url], sessionId);

        if (isMounted) {
          clearTimeout(timeoutId);
          setLoading(false);

          if (previews.length > 0) {
            const preview = previews[0];
            setMetadata(preview);

            // Check if there was an error in the metadata
            if (preview.error) {
              setError(true);
            }
          } else {
            // No metadata returned, show minimal card
            setError(true);
            setMetadata({
              url,
              domain: new URL(url).hostname,
              error: 'Unable to load preview',
            });
          }
        }
      } catch (err) {
        // Handle fetch errors (Requirement 1.4)
        if (isMounted) {
          clearTimeout(timeoutId);
          setLoading(false);
          setError(true);

          // Create minimal metadata with error
          try {
            setMetadata({
              url,
              domain: new URL(url).hostname,
              error: err instanceof Error ? err.message : 'Unable to load preview',
            });
          } catch {
            // If URL parsing fails, use url as domain
            setMetadata({
              url,
              domain: url,
              error: 'Unable to load preview',
            });
          }
        }
      }
    };

    fetchMetadata();

    // Cleanup function
    return () => {
      isMounted = false;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [url, sessionId]);

  // Show loading skeleton (Requirement 4.2)
  if (loading) {
    return <PreviewCard metadata={{ url, domain: '' }} loading={true} />;
  }

  // Show minimal card on error or render full card with metadata (Requirement 1.4)
  if (metadata) {
    return <PreviewCard metadata={metadata} loading={false} />;
  }

  // Fallback: should not reach here, but handle gracefully
  return null;
}
