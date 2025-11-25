/**
 * Property-based tests for SPA routing configuration
 * 
 * Feature: firebase-hosting-migration, Property 2: SPA routing serves index.html for all routes
 * Validates: Requirements 2.3
 * 
 * Tests that Firebase Hosting configuration correctly serves index.html for all application routes
 */

import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import { readFileSync } from 'fs';
import { join } from 'path';

describe('Property 2: SPA routing serves index.html for all routes', () => {
  /**
   * Helper function to check if a route matches Firebase rewrite rules
   */
  const matchesRewriteRule = (route: string, rewriteRules: Array<{ source: string; destination: string }>): boolean => {
    for (const rule of rewriteRules) {
      // Convert Firebase glob pattern to regex
      // ** matches any path segments (including slashes)
      // * matches within a single segment (no slashes)
      
      // Escape special regex characters except * and **
      let pattern = rule.source
        .replace(/[.+?^${}()|[\]\\]/g, '\\$&');
      
      // Replace ** with a placeholder first to avoid conflicts
      pattern = pattern.replace(/\*\*/g, '__DOUBLE_STAR__');
      
      // Replace single * with pattern that matches anything except /
      pattern = pattern.replace(/\*/g, '[^/]*');
      
      // Replace ** placeholder with pattern that matches everything
      pattern = pattern.replace(/__DOUBLE_STAR__/g, '.*');
      
      const regex = new RegExp(`^${pattern}$`);
      
      if (regex.test(route)) {
        return rule.destination === '/index.html';
      }
    }
    return false;
  };

  /**
   * Generator for valid application route paths
   * Routes should start with / and contain valid URL path characters
   */
  const validRoutePath = fc.oneof(
    // Root path
    fc.constant('/'),
    
    // Single segment paths
    fc.string({ minLength: 1, maxLength: 20 })
      .filter(s => /^[a-zA-Z0-9_-]+$/.test(s))
      .map(s => `/${s}`),
    
    // Multi-segment paths
    fc.array(
      fc.string({ minLength: 1, maxLength: 15 })
        .filter(s => /^[a-zA-Z0-9_-]+$/.test(s)),
      { minLength: 2, maxLength: 5 }
    ).map(segments => `/${segments.join('/')}`),
    
    // Paths with query parameters
    fc.tuple(
      fc.string({ minLength: 1, maxLength: 20 })
        .filter(s => /^[a-zA-Z0-9_-]+$/.test(s)),
      fc.string({ minLength: 1, maxLength: 30 })
        .filter(s => /^[a-zA-Z0-9_=-]+$/.test(s))
    ).map(([path, query]) => `/${path}?${query}`),
    
    // Paths with hash fragments
    fc.tuple(
      fc.string({ minLength: 1, maxLength: 20 })
        .filter(s => /^[a-zA-Z0-9_-]+$/.test(s)),
      fc.string({ minLength: 1, maxLength: 20 })
        .filter(s => /^[a-zA-Z0-9_-]+$/.test(s))
    ).map(([path, hash]) => `/${path}#${hash}`)
  );

  it('should configure rewrite rules to serve index.html for any valid route path', () => {
    // Read Firebase configuration
    const configPath = join(__dirname, '../../firebase.json');
    const configContent = readFileSync(configPath, 'utf-8');
    const config = JSON.parse(configContent);
    
    const rewriteRules = config.hosting.rewrites;
    
    fc.assert(
      fc.property(
        validRoutePath,
        (route) => {
          // For any valid application route, the Firebase rewrite rules should
          // match it and serve index.html
          const servesIndexHtml = matchesRewriteRule(route, rewriteRules);
          
          expect(servesIndexHtml).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should have catch-all rewrite rule that matches all paths', () => {
    // Read Firebase configuration
    const configPath = join(__dirname, '../../firebase.json');
    const configContent = readFileSync(configPath, 'utf-8');
    const config = JSON.parse(configContent);
    
    const rewriteRules = config.hosting.rewrites;
    
    // Check that there's a catch-all rule
    const catchAllRule = rewriteRules.find(
      (rule: { source: string; destination: string }) => rule.source === '**'
    );
    
    expect(catchAllRule).toBeDefined();
    expect(catchAllRule.destination).toBe('/index.html');
  });

  it('should serve index.html for deeply nested routes', () => {
    // Read Firebase configuration
    const configPath = join(__dirname, '../../firebase.json');
    const configContent = readFileSync(configPath, 'utf-8');
    const config = JSON.parse(configContent);
    
    const rewriteRules = config.hosting.rewrites;
    
    fc.assert(
      fc.property(
        // Generate deeply nested paths (3-10 segments)
        fc.array(
          fc.string({ minLength: 1, maxLength: 10 })
            .filter(s => /^[a-zA-Z0-9_-]+$/.test(s)),
          { minLength: 3, maxLength: 10 }
        ).map(segments => `/${segments.join('/')}`),
        (deepRoute) => {
          const servesIndexHtml = matchesRewriteRule(deepRoute, rewriteRules);
          expect(servesIndexHtml).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should serve index.html for routes with various special characters', () => {
    // Read Firebase configuration
    const configPath = join(__dirname, '../../firebase.json');
    const configContent = readFileSync(configPath, 'utf-8');
    const config = JSON.parse(configContent);
    
    const rewriteRules = config.hosting.rewrites;
    
    fc.assert(
      fc.property(
        // Generate routes with URL-safe special characters
        fc.tuple(
          fc.string({ minLength: 1, maxLength: 15 })
            .filter(s => /^[a-zA-Z0-9]+$/.test(s)),
          fc.oneof(
            fc.constant('-'),
            fc.constant('_'),
            fc.constant('.')
          )
        ).map(([base, char]) => `/${base}${char}${base}`),
        (routeWithSpecialChar) => {
          const servesIndexHtml = matchesRewriteRule(routeWithSpecialChar, rewriteRules);
          expect(servesIndexHtml).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should not interfere with static asset paths', () => {
    // Read Firebase configuration
    const configPath = join(__dirname, '../../firebase.json');
    const configContent = readFileSync(configPath, 'utf-8');
    const config = JSON.parse(configContent);
    
    const rewriteRules = config.hosting.rewrites;
    
    // Static assets should still be served as-is by Firebase
    // The rewrite rule should match them, but Firebase will serve the actual file if it exists
    // This test verifies the configuration allows for this behavior
    
    const staticAssetPaths = [
      '/assets/index.js',
      '/assets/index.css',
      '/vite.svg',
      '/assets/logo.png',
      '/favicon.ico'
    ];
    
    staticAssetPaths.forEach(assetPath => {
      // The rewrite rule will match, but Firebase serves the actual file if it exists
      // This is the expected behavior - the catch-all rule is a fallback
      const matchesRule = matchesRewriteRule(assetPath, rewriteRules);
      expect(matchesRule).toBe(true);
    });
  });

  it('should handle routes that look like file paths', () => {
    // Read Firebase configuration
    const configPath = join(__dirname, '../../firebase.json');
    const configContent = readFileSync(configPath, 'utf-8');
    const config = JSON.parse(configContent);
    
    const rewriteRules = config.hosting.rewrites;
    
    fc.assert(
      fc.property(
        // Generate paths that look like files but are actually routes
        fc.tuple(
          fc.string({ minLength: 1, maxLength: 15 })
            .filter(s => /^[a-zA-Z0-9_-]+$/.test(s)),
          fc.oneof(
            fc.constant('html'),
            fc.constant('json'),
            fc.constant('xml')
          )
        ).map(([name, ext]) => `/${name}.${ext}`),
        (fileLikePath) => {
          // Even paths that look like files should serve index.html if the file doesn't exist
          const servesIndexHtml = matchesRewriteRule(fileLikePath, rewriteRules);
          expect(servesIndexHtml).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });
});
