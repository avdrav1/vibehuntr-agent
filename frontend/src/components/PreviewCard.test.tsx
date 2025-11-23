import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { PreviewCard } from './PreviewCard';
import type { LinkMetadata } from '../types/linkPreview';

/**
 * Unit tests for PreviewCard component
 * Requirements: 1.3, 1.4, 2.4, 2.5, 7.1, 7.4
 */
describe('PreviewCard Component', () => {
  const fullMetadata: LinkMetadata = {
    url: 'https://example.com/article',
    domain: 'example.com',
    title: 'Example Article Title',
    description: 'This is a description of the example article with some interesting content.',
    image: 'https://example.com/image.jpg',
    favicon: 'https://example.com/favicon.ico',
  };

  const partialMetadata: LinkMetadata = {
    url: 'https://example.com',
    domain: 'example.com',
    title: 'Example Site',
  };

  const minimalMetadata: LinkMetadata = {
    url: 'https://example.com',
    domain: 'example.com',
  };

  describe('Rendering with full metadata (Requirement 1.3)', () => {
    it('renders with all metadata fields', () => {
      render(<PreviewCard metadata={fullMetadata} />);

      // Title should be displayed
      expect(screen.getByText('Example Article Title')).toBeInTheDocument();

      // Description should be displayed
      expect(screen.getByText(/This is a description/)).toBeInTheDocument();

      // Domain should be displayed
      expect(screen.getByText('example.com')).toBeInTheDocument();

      // Link should have correct href
      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('href', 'https://example.com/article');
    });

    it('renders image when provided', () => {
      const { container } = render(<PreviewCard metadata={fullMetadata} />);

      const image = container.querySelector('.link-preview-image');
      expect(image).toBeInTheDocument();
      expect(image).toHaveAttribute('src', 'https://example.com/image.jpg');
      expect(image).toHaveAttribute('alt', 'Preview image for Example Article Title');
    });

    it('renders favicon when provided', () => {
      const { container } = render(<PreviewCard metadata={fullMetadata} />);

      const favicon = container.querySelector('.link-preview-favicon');
      expect(favicon).toBeInTheDocument();
      expect(favicon).toHaveAttribute('src', 'https://example.com/favicon.ico');
    });
  });

  describe('Rendering with partial metadata (Requirement 2.4)', () => {
    it('renders without image', () => {
      const { container } = render(<PreviewCard metadata={partialMetadata} />);

      // Should not have image
      const image = container.querySelector('.link-preview-image');
      expect(image).not.toBeInTheDocument();

      // Should have fallback
      const fallback = container.querySelector('.link-preview-fallback');
      expect(fallback).toBeInTheDocument();
    });

    it('renders without description', () => {
      render(<PreviewCard metadata={partialMetadata} />);

      // Title and domain should still be present
      expect(screen.getByText('Example Site')).toBeInTheDocument();
      expect(screen.getByText('example.com')).toBeInTheDocument();

      // Description should not be present
      const description = document.querySelector('.link-preview-description');
      expect(description).not.toBeInTheDocument();
    });

    it('renders without favicon', () => {
      const { container } = render(<PreviewCard metadata={partialMetadata} />);

      const favicon = container.querySelector('.link-preview-favicon');
      expect(favicon).not.toBeInTheDocument();
    });
  });

  describe('Rendering with minimal metadata', () => {
    it('renders with only URL and domain', () => {
      render(<PreviewCard metadata={minimalMetadata} />);

      // Domain should be used as title when title is missing
      const titleElements = screen.getAllByText('example.com');
      expect(titleElements.length).toBeGreaterThan(0);

      // Link should still work
      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('href', 'https://example.com');
    });
  });

  describe('Loading state (Requirement 4.2)', () => {
    it('renders loading skeleton', () => {
      const { container } = render(<PreviewCard metadata={fullMetadata} loading={true} />);

      const loadingElement = screen.getByRole('status');
      expect(loadingElement).toBeInTheDocument();
      expect(loadingElement).toHaveAttribute('aria-label', 'Loading link preview');

      // Should have skeleton elements
      expect(container.querySelector('.skeleton-title')).toBeInTheDocument();
      expect(container.querySelector('.skeleton-description')).toBeInTheDocument();
      expect(container.querySelector('.skeleton-image')).toBeInTheDocument();
      expect(container.querySelector('.skeleton-domain')).toBeInTheDocument();
    });

    it('does not render actual content when loading', () => {
      render(<PreviewCard metadata={fullMetadata} loading={true} />);

      // Should not show actual title
      expect(screen.queryByText('Example Article Title')).not.toBeInTheDocument();
    });
  });

  describe('Error state (Requirement 1.4)', () => {
    it('displays error indicator when error is present', () => {
      const errorMetadata: LinkMetadata = {
        ...fullMetadata,
        error: 'Failed to fetch metadata',
      };

      render(<PreviewCard metadata={errorMetadata} />);

      const errorElement = screen.getByRole('alert');
      expect(errorElement).toBeInTheDocument();
      expect(errorElement).toHaveTextContent('Unable to load full preview');
    });

    it('still renders available metadata when error is present', () => {
      const errorMetadata: LinkMetadata = {
        ...fullMetadata,
        error: 'Failed to fetch metadata',
      };

      render(<PreviewCard metadata={errorMetadata} />);

      // Should still show title and domain
      expect(screen.getByText('Example Article Title')).toBeInTheDocument();
      expect(screen.getByText('example.com')).toBeInTheDocument();
    });
  });

  describe('Fallback icon (Requirement 2.4)', () => {
    it('shows fallback icon when image is missing', () => {
      const { container } = render(<PreviewCard metadata={partialMetadata} />);

      const fallback = container.querySelector('.link-preview-fallback');
      expect(fallback).toBeInTheDocument();
      expect(fallback).toHaveAttribute('role', 'img');
      expect(fallback).toHaveAttribute('aria-label', 'Link icon');
    });

    it('shows fallback icon when image fails to load', async () => {
      const { container } = render(<PreviewCard metadata={fullMetadata} />);

      // Simulate image load error
      const image = container.querySelector('.link-preview-image') as HTMLImageElement;
      if (image) {
        image.dispatchEvent(new Event('error'));
      }

      // Wait for state update
      await waitFor(() => {
        const fallback = container.querySelector('.link-preview-fallback');
        expect(fallback).toBeInTheDocument();
      });
    });
  });

  describe('Security attributes (Requirement 2.5)', () => {
    it('includes target="_blank" on link', () => {
      render(<PreviewCard metadata={fullMetadata} />);

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('target', '_blank');
    });

    it('includes rel="noopener noreferrer" on link', () => {
      render(<PreviewCard metadata={fullMetadata} />);

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    });
  });

  describe('Accessibility (Requirements 7.1, 7.4)', () => {
    it('includes ARIA label on link', () => {
      render(<PreviewCard metadata={fullMetadata} />);

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('aria-label');
      expect(link.getAttribute('aria-label')).toContain('Example Article Title');
    });

    it('includes ARIA label with domain when no title', () => {
      render(<PreviewCard metadata={minimalMetadata} />);

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('aria-label');
      expect(link.getAttribute('aria-label')).toContain('example.com');
    });

    it('includes alt text on image', () => {
      const { container } = render(<PreviewCard metadata={fullMetadata} />);

      const image = container.querySelector('.link-preview-image');
      expect(image).toHaveAttribute('alt');
      expect(image?.getAttribute('alt')).toContain('Example Article Title');
    });

    it('includes alt text with domain when no title', () => {
      const metadataWithImageNoTitle: LinkMetadata = {
        ...minimalMetadata,
        image: 'https://example.com/image.jpg',
      };

      const { container } = render(<PreviewCard metadata={metadataWithImageNoTitle} />);

      const image = container.querySelector('.link-preview-image');
      expect(image).toHaveAttribute('alt');
      expect(image?.getAttribute('alt')).toContain('example.com');
    });

    it('includes role="img" on fallback', () => {
      const { container } = render(<PreviewCard metadata={partialMetadata} />);

      const fallback = container.querySelector('.link-preview-fallback');
      expect(fallback).toHaveAttribute('role', 'img');
    });

    it('includes aria-label on fallback', () => {
      const { container } = render(<PreviewCard metadata={partialMetadata} />);

      const fallback = container.querySelector('.link-preview-fallback');
      expect(fallback).toHaveAttribute('aria-label', 'Link icon');
    });
  });

  describe('Image loading behavior', () => {
    it('shows loading indicator while image loads', () => {
      const { container } = render(<PreviewCard metadata={fullMetadata} />);

      const loadingIndicator = container.querySelector('.link-preview-image-loading');
      expect(loadingIndicator).toBeInTheDocument();
    });

    it('hides loading indicator when image loads', async () => {
      const { container } = render(<PreviewCard metadata={fullMetadata} />);

      // Simulate image load
      const image = container.querySelector('.link-preview-image') as HTMLImageElement;
      if (image) {
        image.dispatchEvent(new Event('load'));
      }

      // Image should have loaded class
      await waitFor(() => {
        expect(image).toHaveClass('loaded');
      });
    });

    it('includes lazy loading attribute on image', () => {
      const { container } = render(<PreviewCard metadata={fullMetadata} />);

      const image = container.querySelector('.link-preview-image');
      expect(image).toHaveAttribute('loading', 'lazy');
    });
  });
});
