import { useState } from 'react';
import type { LinkMetadata } from '../types/linkPreview';

interface PreviewCardProps {
  metadata: LinkMetadata;
  loading?: boolean;
}

/**
 * PreviewCard component displays a rich preview card for a URL
 * Implements Requirements:
 * - 1.3: Display preview card with metadata
 * - 1.4: Handle error states gracefully
 * - 2.4: Show fallback when image is missing
 * - 2.5: Open links securely in new tab
 * - 7.1: Include ARIA labels for accessibility
 * - 7.4: Include alt text for images
 */
export function PreviewCard({ metadata, loading = false }: PreviewCardProps) {
  const [imageError, setImageError] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);

  // Show loading skeleton
  if (loading) {
    return (
      <div
        className="link-preview-card link-preview-loading"
        role="status"
        aria-label="Loading link preview"
      >
        <div className="link-preview-skeleton">
          <div className="skeleton-line skeleton-title"></div>
          <div className="skeleton-line skeleton-description"></div>
          <div className="skeleton-line skeleton-description short"></div>
          <div className="skeleton-image"></div>
          <div className="skeleton-line skeleton-domain"></div>
        </div>
      </div>
    );
  }

  // Determine if we should show the image
  const showImage = metadata.image && !imageError;
  const hasContent = metadata.title || metadata.description;

  // Generate alt text for image
  const imageAlt = metadata.title
    ? `Preview image for ${metadata.title}`
    : `Preview image for ${metadata.domain}`;

  return (
    <a
      href={metadata.url}
      target="_blank"
      rel="noopener noreferrer"
      className="link-preview-card"
      role="link"
      aria-label={`Link preview: ${metadata.title || metadata.domain}`}
    >
      {/* Favicon and Title */}
      <div className="link-preview-header">
        {metadata.favicon && (
          <img
            src={metadata.favicon}
            alt=""
            className="link-preview-favicon"
            onError={(e) => {
              // Hide favicon on error
              e.currentTarget.style.display = 'none';
            }}
          />
        )}
        <div className="link-preview-title">
          {metadata.title || metadata.domain}
        </div>
      </div>

      {/* Description */}
      {metadata.description && (
        <div className="link-preview-description">
          {metadata.description}
        </div>
      )}

      {/* Preview Image or Fallback */}
      {showImage ? (
        <div className="link-preview-image-container">
          <img
            src={metadata.image}
            alt={imageAlt}
            className={`link-preview-image ${imageLoaded ? 'loaded' : ''}`}
            onLoad={() => setImageLoaded(true)}
            onError={() => setImageError(true)}
            loading="lazy"
          />
          {!imageLoaded && (
            <div className="link-preview-image-loading">
              <div className="loading-dots">
                <div className="loading-dot"></div>
                <div className="loading-dot"></div>
                <div className="loading-dot"></div>
              </div>
            </div>
          )}
        </div>
      ) : hasContent ? (
        <div className="link-preview-fallback" role="img" aria-label="Link icon">
          <svg
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      ) : null}

      {/* Domain */}
      <div className="link-preview-footer">
        <span className="link-preview-domain-icon">🔗</span>
        <span className="link-preview-domain">{metadata.domain}</span>
      </div>

      {/* Error indicator (if present) */}
      {metadata.error && (
        <div className="link-preview-error" role="alert">
          Unable to load full preview
        </div>
      )}
    </a>
  );
}
