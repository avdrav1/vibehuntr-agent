/**
 * Property-based tests for HTTPS enforcement
 * 
 * Feature: firebase-hosting-migration, Property 5: HTTPS is enforced for all requests
 * Validates: Requirements 6.5
 * 
 * Tests that Firebase Hosting configuration enforces HTTPS for all requests.
 * Firebase Hosting automatically provides SSL certificates and enforces HTTPS by default.
 * This test verifies that the configuration doesn't disable this behavior.
 */

import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import { readFileSync } from 'fs';
import { join } from 'path';

describe('Property 5: HTTPS is enforced for all requests', () => {
  // Read Firebase configuration once for all tests
  const configPath = join(__dirname, '../../firebase.json');
  const configContent = readFileSync(configPath, 'utf-8');
  const config = JSON.parse(configContent);

  /**
   * Helper function to check if HTTPS redirect is explicitly disabled
   * Firebase Hosting enforces HTTPS by default, but it can be disabled
   */
  const isHttpsRedirectDisabled = (): boolean => {
    // Check if there's an explicit redirect configuration that disables HTTPS
    if (config.hosting.redirects) {
      const httpsDisablingRedirect = config.hosting.redirects.find((redirect: any) => 
        redirect.type === 301 && redirect.destination && redirect.destination.startsWith('http://')
      );
      return !!httpsDisablingRedirect;
    }
    return false;
  };

  /**
   * Helper function to check if there are any insecure headers that might weaken HTTPS
   */
  const hasInsecureHeaders = (): boolean => {
    if (!config.hosting.headers) {
      return false;
    }

    for (const headerRule of config.hosting.headers) {
      for (const header of headerRule.headers) {
        // Check for headers that might weaken HTTPS security
        if (header.key === 'Content-Security-Policy' && header.value.includes('upgrade-insecure-requests; block-all-mixed-content')) {
          // This is actually good - it enforces HTTPS
          continue;
        }
        
        // Check for headers that explicitly allow insecure content
        if (header.key === 'Content-Security-Policy' && 
            (header.value.includes('http:') && !header.value.includes('https:'))) {
          return true;
        }
      }
    }
    return false;
  };

  /**
   * Generator for various URL paths to test HTTPS enforcement
   */
  const urlPath = fc.oneof(
    fc.constant('/'),
    fc.string({ minLength: 1, maxLength: 20 })
      .filter(s => /^[a-zA-Z0-9_-]+$/.test(s))
      .map(s => `/${s}`),
    fc.array(
      fc.string({ minLength: 1, maxLength: 15 })
        .filter(s => /^[a-zA-Z0-9_-]+$/.test(s)),
      { minLength: 2, maxLength: 5 }
    ).map(segments => `/${segments.join('/')}`)
  );

  it('should not explicitly disable HTTPS redirect', () => {
    // Firebase Hosting enforces HTTPS by default
    // Verify that the configuration doesn't explicitly disable this
    expect(isHttpsRedirectDisabled()).toBe(false);
  });

  it('should not have insecure headers that weaken HTTPS', () => {
    // Verify that no headers explicitly allow insecure content
    expect(hasInsecureHeaders()).toBe(false);
  });

  it('should not have any HTTP-only redirect rules', () => {
    // Check that there are no redirects forcing HTTP
    if (config.hosting.redirects) {
      config.hosting.redirects.forEach((redirect: any) => {
        if (redirect.destination) {
          expect(redirect.destination).not.toMatch(/^http:\/\//);
        }
      });
    }
  });

  it('should maintain HTTPS enforcement for all generated paths', () => {
    fc.assert(
      fc.property(
        urlPath,
        (path) => {
          // For any path, verify that the configuration doesn't have rules
          // that would prevent HTTPS enforcement
          
          // Check if there's a redirect rule for this path that forces HTTP
          if (config.hosting.redirects) {
            const matchingRedirect = config.hosting.redirects.find((redirect: any) => {
              if (redirect.source === path || redirect.source === '**') {
                return redirect.destination && redirect.destination.startsWith('http://');
              }
              return false;
            });
            expect(matchingRedirect).toBeUndefined();
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should not have configuration that bypasses HTTPS', () => {
    // Firebase Hosting automatically provides SSL and enforces HTTPS
    // Verify that the configuration doesn't have any settings that would bypass this
    
    // Check for any explicit HTTP-only settings
    expect(config.hosting).not.toHaveProperty('httpOnly');
    expect(config.hosting).not.toHaveProperty('disableHttps');
    expect(config.hosting).not.toHaveProperty('allowHttp');
  });

  it('should allow HTTPS URLs in all configuration sections', () => {
    // Verify that if there are any URL references in the config, they use HTTPS
    const configString = JSON.stringify(config);
    
    // Find all URL patterns in the configuration
    const httpUrlPattern = /http:\/\/[^\s"']+/g;
    const httpUrls = configString.match(httpUrlPattern) || [];
    
    // Filter out localhost URLs (which are acceptable for development)
    const nonLocalhostHttpUrls = httpUrls.filter(url => 
      !url.includes('localhost') && !url.includes('127.0.0.1')
    );
    
    // There should be no non-localhost HTTP URLs in the configuration
    expect(nonLocalhostHttpUrls).toHaveLength(0);
  });

  it('should not have mixed content policy that allows insecure requests', () => {
    // Check Content-Security-Policy headers
    if (config.hosting.headers) {
      config.hosting.headers.forEach((headerRule: any) => {
        const cspHeader = headerRule.headers.find((h: any) => 
          h.key === 'Content-Security-Policy'
        );
        
        if (cspHeader) {
          // If CSP is defined, it should not explicitly allow insecure content
          expect(cspHeader.value).not.toContain('upgrade-insecure-requests: false');
          
          // It should not have directives that allow HTTP resources
          const directives = cspHeader.value.split(';').map((d: string) => d.trim());
          directives.forEach((directive: string) => {
            if (directive.startsWith('default-src') || 
                directive.startsWith('script-src') || 
                directive.startsWith('style-src') ||
                directive.startsWith('img-src')) {
              // These directives should not explicitly allow HTTP
              const httpPattern = /\bhttp:\/\/(?!localhost|127\.0\.0\.1)/;
              expect(directive).not.toMatch(httpPattern);
            }
          });
        }
      });
    }
  });

  it('should maintain HTTPS enforcement across different file types', () => {
    const fileExtensions = ['html', 'js', 'css', 'json', 'xml', 'svg', 'png', 'jpg'];
    
    fc.assert(
      fc.property(
        fc.constantFrom(...fileExtensions),
        fc.string({ minLength: 1, maxLength: 20 })
          .filter(s => /^[a-zA-Z0-9_-]+$/.test(s)),
        (ext, filename) => {
          const filePath = `/${filename}.${ext}`;
          
          // Verify no redirect rules force HTTP for this file type
          if (config.hosting.redirects) {
            const matchingRedirect = config.hosting.redirects.find((redirect: any) => {
              const sourceMatches = redirect.source === filePath || 
                                   redirect.source === '**' ||
                                   redirect.source === `**/*.${ext}`;
              return sourceMatches && redirect.destination && redirect.destination.startsWith('http://');
            });
            expect(matchingRedirect).toBeUndefined();
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should not have any configuration that would prevent automatic SSL', () => {
    // Firebase Hosting automatically provisions SSL certificates
    // Verify that the configuration doesn't interfere with this
    
    // Check that there are no SSL-related settings that would disable it
    expect(config.hosting).not.toHaveProperty('ssl');
    expect(config.hosting).not.toHaveProperty('disableSsl');
    expect(config.hosting).not.toHaveProperty('certificate');
    
    // The absence of these properties means Firebase uses its default SSL behavior
  });

  it('should enforce HTTPS for all rewrite destinations', () => {
    // Check that rewrite rules don't redirect to HTTP URLs
    if (config.hosting.rewrites) {
      config.hosting.rewrites.forEach((rewrite: any) => {
        if (rewrite.destination) {
          // Destinations should be relative paths or HTTPS URLs
          if (rewrite.destination.startsWith('http')) {
            expect(rewrite.destination).toMatch(/^https:\/\//);
          }
        }
      });
    }
  });
});
