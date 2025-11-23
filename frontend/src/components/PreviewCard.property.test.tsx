import { describe, it, expect, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import fc from 'fast-check';
import { PreviewCard } from './PreviewCard';
import type { LinkMetadata } from '../types/linkPreview';

/**
 * Property-based tests for PreviewCard component
 * Uses fast-check for property-based testing
 */

// Arbitraries (generators) for test data

const urlArbitrary = fc.webUrl();

const domainArbitrary = fc.domain();

const optionalStringArbitrary = fc.option(
  fc.string({ minLength: 1, maxLength: 200 }),
  { nil: undefined }
);

const linkMetadataArbitrary = fc.record({
  url: urlArbitrary,
  domain: domainArbitrary,
  title: optionalStringArbitrary,
  description: optionalStringArbitrary,
  image: fc.option(urlArbitrary, { nil: undefined }),
  favicon: fc.option(urlArbitrary, { nil: undefined }),
  error: fc.option(fc.string(), { nil: undefined }),
});

describe('PreviewCard Property Tests', () => {
  // Cleanup after each test to avoid DOM accumulation
  afterEach(() => {
    cleanup();
  });

  /**
   * Feature: link-preview-cards, Property 4: Preview card rendering with metadata
   * 
   * For any metadata object with at least a URL and domain, the preview card
   * component should render successfully and include all available fields in the output.
   * 
   * Validates: Requirements 1.3
   */
  it('Property 4: renders successfully with any valid metadata', () => {
    fc.assert(
      fc.property(linkMetadataArbitrary, (metadata) => {
        // Render the component
        const { container } = render(<PreviewCard metadata={metadata} />);
        
        // Component should render without crashing
        expect(container).toBeTruthy();
        
        // Should have a link element
        const link = container.querySelector('a[role="link"]');
        expect(link).toBeInTheDocument();
        expect(link).toHaveAttribute('href', metadata.url);
        
        // Should display domain
        const domainElement = container.querySelector('.link-preview-domain');
        expect(domainElement).toBeInTheDocument();
        expect(domainElement?.textContent).toBe(metadata.domain);
        
        // Should display title if present
        const titleElement = container.querySelector('.link-preview-title');
        if (metadata.title) {
          expect(titleElement?.textContent).toBe(metadata.title);
        } else {
          // If no title, domain should be shown as title
          expect(titleElement?.textContent).toBe(metadata.domain);
        }
        
        // Should display description if present
        if (metadata.description) {
          const descElement = container.querySelector('.link-preview-description');
          expect(descElement?.textContent).toBe(metadata.description);
        }
        
        // Should have security attributes
        expect(link).toHaveAttribute('target', '_blank');
        expect(link).toHaveAttribute('rel', 'noopener noreferrer');
        
        // Should have ARIA label
        expect(link).toHaveAttribute('aria-label');
        
        cleanup();
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Feature: link-preview-cards, Property 7: Image fallback handling
   * 
   * For any metadata object without an image field, the preview card should
   * render with a fallback element (icon or gradient) instead of an image.
   * 
   * Validates: Requirements 2.4, 5.5
   */
  it('Property 7: shows fallback when image is missing', () => {
    fc.assert(
      fc.property(
        fc.record({
          url: urlArbitrary,
          domain: domainArbitrary,
          title: optionalStringArbitrary,
          description: optionalStringArbitrary,
          image: fc.constant(undefined), // No image
          favicon: fc.option(urlArbitrary, { nil: undefined }),
          error: fc.option(fc.string(), { nil: undefined }),
        }),
        (metadata) => {
          // Only test when there's some content (title or description)
          if (!metadata.title && !metadata.description) {
            return true; // Skip this case
          }
          
          render(<PreviewCard metadata={metadata} />);
          
          // Should not have an img element with link-preview-image class
          const images = document.querySelectorAll('.link-preview-image');
          expect(images.length).toBe(0);
          
          // Should have fallback element
          const fallback = document.querySelector('.link-preview-fallback');
          expect(fallback).toBeInTheDocument();
          expect(fallback).toHaveAttribute('role', 'img');
          expect(fallback).toHaveAttribute('aria-label', 'Link icon');
        }
      ),
      { numRuns: 100 }
    );
  });

  it('Property: renders loading state correctly', () => {
    fc.assert(
      fc.property(linkMetadataArbitrary, (metadata) => {
        const { container } = render(<PreviewCard metadata={metadata} loading={true} />);
        
        // Should show loading skeleton
        const loadingElement = container.querySelector('[role="status"]');
        expect(loadingElement).toBeInTheDocument();
        expect(loadingElement).toHaveAttribute('aria-label', 'Loading link preview');
        
        // Should have skeleton class
        expect(loadingElement).toHaveClass('link-preview-loading');
        
        cleanup();
      }),
      { numRuns: 50 }
    );
  });

  it('Property: includes alt text for images when present', () => {
    fc.assert(
      fc.property(
        fc.record({
          url: urlArbitrary,
          domain: domainArbitrary,
          title: fc.string({ minLength: 1, maxLength: 100 }),
          description: optionalStringArbitrary,
          image: urlArbitrary, // Always has image
          favicon: fc.option(urlArbitrary, { nil: undefined }),
          error: fc.constant(undefined),
        }),
        (metadata) => {
          const { container } = render(<PreviewCard metadata={metadata} />);
          
          // Should have an image with alt text
          const image = container.querySelector('.link-preview-image');
          expect(image).toBeInTheDocument();
          expect(image).toHaveAttribute('alt');
          
          const altText = image?.getAttribute('alt');
          expect(altText).toBeTruthy();
          
          // Alt text should start with "Preview image for"
          expect(altText).toMatch(/^Preview image for/);
        }
      ),
      { numRuns: 50 }
    );
  });

  it('Property: displays error indicator when error is present', () => {
    fc.assert(
      fc.property(
        fc.record({
          url: urlArbitrary,
          domain: domainArbitrary,
          title: optionalStringArbitrary,
          description: optionalStringArbitrary,
          image: fc.option(urlArbitrary, { nil: undefined }),
          favicon: fc.option(urlArbitrary, { nil: undefined }),
          error: fc.string({ minLength: 1, maxLength: 100 }).filter(s => s.trim().length > 0), // Always has non-empty error
        }),
        (metadata) => {
          const { container } = render(<PreviewCard metadata={metadata} />);
          
          // Should display error message
          const errorElement = container.querySelector('.link-preview-error');
          expect(errorElement).toBeInTheDocument();
          expect(errorElement).toHaveTextContent('Unable to load full preview');
          expect(errorElement).toHaveAttribute('role', 'alert');
        }
      ),
      { numRuns: 50 }
    );
  });

  it('Property: handles metadata with only required fields', () => {
    fc.assert(
      fc.property(
        fc.record({
          url: urlArbitrary,
          domain: domainArbitrary,
          title: fc.constant(undefined),
          description: fc.constant(undefined),
          image: fc.constant(undefined),
          favicon: fc.constant(undefined),
          error: fc.constant(undefined),
        }),
        (metadata) => {
          const { container } = render(<PreviewCard metadata={metadata} />);
          
          // Should render without crashing
          expect(container).toBeTruthy();
          
          // Should display domain (appears in both title and footer)
          const domainElements = container.querySelectorAll(`*:not(script):not(style)`);
          const domainTexts = Array.from(domainElements)
            .map(el => el.textContent)
            .filter(text => text?.includes(metadata.domain));
          expect(domainTexts.length).toBeGreaterThan(0);
          
          // Should have link with correct attributes
          const link = container.querySelector('a[role="link"]');
          expect(link).toBeInTheDocument();
          expect(link).toHaveAttribute('href', metadata.url);
          expect(link).toHaveAttribute('target', '_blank');
          expect(link).toHaveAttribute('rel', 'noopener noreferrer');
        }
      ),
      { numRuns: 50 }
    );
  });
});
