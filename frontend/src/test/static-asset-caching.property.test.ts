/**
 * Property-based tests for static asset caching configuration
 * 
 * Feature: firebase-hosting-migration, Property 4: Static assets have long-term cache headers
 * Validates: Requirements 6.1
 * 
 * Tests that Firebase Hosting configuration correctly applies long-term caching headers
 * to immutable static assets (JS, CSS, images, fonts)
 */

import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import { readFileSync } from 'fs';
import { join } from 'path';

describe('Property 4: Static assets have long-term cache headers', () => {
  // Read Firebase configuration once for all tests
  const configPath = join(__dirname, '../../firebase.json');
  const configContent = readFileSync(configPath, 'utf-8');
  const config = JSON.parse(configContent);
  const headerRules = config.hosting.headers;

  /**
   * Helper function to get cache header for a specific file extension
   */
  const getCacheHeaderForExtension = (ext: string): string | null => {
    // Find the static asset rule
    const staticAssetRule = headerRules.find((rule: any) => 
      rule.source.includes('@(') && rule.source.includes(ext)
    );
    
    if (staticAssetRule) {
      const cacheControl = staticAssetRule.headers.find((h: any) => h.key === 'Cache-Control');
      return cacheControl ? cacheControl.value : null;
    }
    
    return null;
  };

  /**
   * Helper function to check if a cache header value indicates long-term caching
   */
  const hasLongTermCaching = (cacheHeaderValue: string): boolean => {
    // Long-term caching should have max-age=31536000 (1 year in seconds)
    return cacheHeaderValue.includes('max-age=31536000');
  };

  it('should have a cache header rule for static assets', () => {
    // Verify that there's at least one rule for static assets
    const staticAssetRule = headerRules.find((rule: any) => 
      rule.source.includes('**/*') && rule.source.includes('@(')
    );
    
    expect(staticAssetRule).toBeDefined();
    expect(staticAssetRule.headers).toBeDefined();
    expect(staticAssetRule.headers.length).toBeGreaterThan(0);
  });

  it('should apply long-term cache headers to JavaScript files', () => {
    fc.assert(
      fc.property(
        fc.constantFrom('js'),
        (ext) => {
          const cacheHeader = getCacheHeaderForExtension(ext);
          expect(cacheHeader).not.toBeNull();
          expect(hasLongTermCaching(cacheHeader!)).toBe(true);
          expect(cacheHeader).toContain('max-age=31536000');
        }
      ),
      { numRuns: 10 }
    );
  });

  it('should apply long-term cache headers to CSS files', () => {
    fc.assert(
      fc.property(
        fc.constantFrom('css'),
        (ext) => {
          const cacheHeader = getCacheHeaderForExtension(ext);
          expect(cacheHeader).not.toBeNull();
          expect(hasLongTermCaching(cacheHeader!)).toBe(true);
          expect(cacheHeader).toContain('max-age=31536000');
        }
      ),
      { numRuns: 10 }
    );
  });

  it('should apply long-term cache headers to image files', () => {
    fc.assert(
      fc.property(
        fc.constantFrom('jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'),
        (ext) => {
          const cacheHeader = getCacheHeaderForExtension(ext);
          expect(cacheHeader).not.toBeNull();
          expect(hasLongTermCaching(cacheHeader!)).toBe(true);
          expect(cacheHeader).toContain('max-age=31536000');
        }
      ),
      { numRuns: 10 }
    );
  });

  it('should apply long-term cache headers to font files', () => {
    fc.assert(
      fc.property(
        fc.constantFrom('woff', 'woff2', 'ttf', 'eot'),
        (ext) => {
          const cacheHeader = getCacheHeaderForExtension(ext);
          expect(cacheHeader).not.toBeNull();
          expect(hasLongTermCaching(cacheHeader!)).toBe(true);
          expect(cacheHeader).toContain('max-age=31536000');
        }
      ),
      { numRuns: 10 }
    );
  });

  it('should include "immutable" directive in cache headers for static assets', () => {
    const staticExtensions = ['js', 'css', 'jpg', 'png', 'woff2'];
    
    staticExtensions.forEach(ext => {
      const cacheHeader = getCacheHeaderForExtension(ext);
      expect(cacheHeader).not.toBeNull();
      expect(cacheHeader).toContain('immutable');
    });
  });

  it('should include "public" directive in cache headers for static assets', () => {
    const staticExtensions = ['js', 'css', 'jpg', 'png', 'woff2'];
    
    staticExtensions.forEach(ext => {
      const cacheHeader = getCacheHeaderForExtension(ext);
      expect(cacheHeader).not.toBeNull();
      expect(cacheHeader).toContain('public');
    });
  });

  it('should NOT apply long-term cache headers to index.html', () => {
    // Find the index.html rule
    const indexRule = headerRules.find((rule: any) => rule.source === 'index.html');
    
    expect(indexRule).toBeDefined();
    const cacheControl = indexRule.headers.find((h: any) => h.key === 'Cache-Control');
    expect(cacheControl).toBeDefined();
    expect(hasLongTermCaching(cacheControl.value)).toBe(false);
    expect(cacheControl.value).toContain('max-age=3600'); // 1 hour, not 1 year
  });

  it('should have exactly one year (31536000 seconds) for static asset max-age', () => {
    const staticAssetRule = headerRules.find((rule: any) => 
      rule.source.includes('**/*') && rule.source.includes('@(')
    );
    
    const cacheControl = staticAssetRule.headers.find((h: any) => h.key === 'Cache-Control');
    expect(cacheControl.value).toContain('max-age=31536000');
    
    // Verify it's exactly 31536000 (1 year in seconds)
    const maxAgeMatch = cacheControl.value.match(/max-age=(\d+)/);
    expect(maxAgeMatch).not.toBeNull();
    expect(parseInt(maxAgeMatch[1])).toBe(31536000);
  });

  it('should cover all required static asset file types', () => {
    const requiredExtensions = ['js', 'css', 'jpg', 'jpeg', 'png', 'gif', 'svg', 'webp', 'woff', 'woff2', 'ttf', 'eot'];
    
    const staticAssetRule = headerRules.find((rule: any) => 
      rule.source.includes('**/*') && rule.source.includes('@(')
    );
    
    expect(staticAssetRule).toBeDefined();
    
    // Check that all required extensions are in the rule
    requiredExtensions.forEach(ext => {
      expect(staticAssetRule.source).toContain(ext);
    });
  });
});
