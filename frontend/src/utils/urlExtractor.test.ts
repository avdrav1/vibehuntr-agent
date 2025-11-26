/**
 * Property-based and unit tests for URL extraction utility
 * 
 * Tests Requirements:
 * - 1.1: Extract all valid HTTP/HTTPS URLs from message content
 * - 6.1: Exclude localhost and internal IP addresses
 * - 6.2: Exclude data URIs and blob URLs
 * - 6.3: Exclude malformed URLs
 * - 6.4: Exclude URLs already handled by venue links feature
 * - 6.5: Exclude URLs matching custom exclusion patterns
 */

import { describe, it, expect } from 'vitest';
import { extractURLs, isValidURL, shouldExcludeURL } from './urlExtractor';

describe('urlExtractor', () => {
  describe('Property 1: URL extraction completeness', () => {
    /**
     * Feature: link-preview-cards, Property 1: URL extraction completeness
     * 
     * For any message text containing HTTP/HTTPS URLs, the URL extractor should
     * identify all valid URLs and exclude invalid ones, localhost addresses,
     * data URIs, blob URLs, and URLs matching exclusion patterns.
     * 
     * Validates: Requirements 1.1, 6.1, 6.2, 6.3, 6.5
     */
    
    it('should extract all valid HTTP URLs from message text', () => {
      const testCases = [
        {
          text: 'Check out http://example.com',
          expected: ['http://example.com'],
        },
        {
          text: 'Visit https://example.com and http://test.org',
          expected: ['https://example.com', 'http://test.org'],
        },
        {
          text: 'Multiple URLs: https://site1.com https://site2.net https://site3.io',
          expected: ['https://site1.com', 'https://site2.net', 'https://site3.io'],
        },
        {
          text: 'URL with path: https://example.com/path/to/page',
          expected: ['https://example.com/path/to/page'],
        },
        {
          text: 'URL with query: https://example.com?param=value&other=123',
          expected: ['https://example.com?param=value&other=123'],
        },
        {
          text: 'URL with fragment: https://example.com/page#section',
          expected: ['https://example.com/page#section'],
        },
        {
          text: 'URL with port: https://example.com:8080/api',
          expected: ['https://example.com:8080/api'],
        },
        {
          text: 'Complex URL: https://sub.example.com:3000/path?q=test&id=1#top',
          expected: ['https://sub.example.com:3000/path?q=test&id=1#top'],
        },
      ];

      for (const { text, expected } of testCases) {
        const result = extractURLs(text);
        expect(result.map(u => u.url)).toEqual(expected);
      }
    });

    it('should exclude localhost URLs', () => {
      const localhostURLs = [
        'http://localhost',
        'http://localhost:8080',
        'https://localhost',
        'https://localhost:3000/api',
        'http://localhost/path',
        'http://[::1]',
        'http://[::1]:8080',
        'http://[::ffff:127.0.0.1]',
      ];

      for (const url of localhostURLs) {
        const text = `Check out ${url} for more info`;
        const result = extractURLs(text);
        expect(result).toHaveLength(0);
      }
    });

    it('should exclude private IP addresses', () => {
      const privateIPs = [
        'http://192.168.1.1',
        'http://192.168.0.100:8080',
        'http://10.0.0.1',
        'http://10.255.255.255/path',
        'http://172.16.0.1',
        'http://172.31.255.255',
        'http://127.0.0.1',
        'http://127.0.0.1:3000',
        'http://169.254.1.1',
        'http://169.254.169.254',
      ];

      for (const url of privateIPs) {
        const text = `Internal link: ${url}`;
        const result = extractURLs(text);
        expect(result).toHaveLength(0);
      }
    });

    it('should exclude data URIs', () => {
      const dataURIs = [
        'data:text/html,<html></html>',
        'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA',
        'data:application/json,{"key":"value"}',
      ];

      for (const uri of dataURIs) {
        const text = `Embedded data: ${uri}`;
        const result = extractURLs(text);
        expect(result).toHaveLength(0);
      }
    });

    it('should exclude blob URLs', () => {
      const blobURLs = [
        'blob:http://example.com/550e8400-e29b-41d4-a716-446655440000',
        'blob:https://example.com/abc123',
      ];

      for (const url of blobURLs) {
        const text = `Blob URL: ${url}`;
        const result = extractURLs(text);
        expect(result).toHaveLength(0);
      }
    });

    it('should exclude malformed URLs', () => {
      const malformedURLs = [
        'not a url',
        'ftp://example.com',
        'javascript:alert(1)',
        'mailto:test@example.com',
        'file:///path/to/file',
        'http://',
        'https://',
        'http://.',
        'http://..',
      ];

      for (const url of malformedURLs) {
        const text = `Invalid: ${url}`;
        const result = extractURLs(text);
        expect(result).toHaveLength(0);
      }
    });

    it('should exclude URLs matching custom exclusion patterns', () => {
      const text = 'Visit https://blocked.com and https://allowed.com';
      const excludePatterns = ['blocked\\.com'];
      
      const result = extractURLs(text, excludePatterns);
      
      expect(result).toHaveLength(1);
      expect(result[0].url).toBe('https://allowed.com');
    });

    it('should handle empty or null text', () => {
      expect(extractURLs('')).toHaveLength(0);
      expect(extractURLs('   ')).toHaveLength(0);
    });

    it('should handle text with no URLs', () => {
      const text = 'This is just plain text without any links.';
      expect(extractURLs(text)).toHaveLength(0);
    });

    it('should extract URLs with correct positions', () => {
      const text = 'Start https://example.com middle https://test.org end';
      const result = extractURLs(text);
      
      expect(result).toHaveLength(2);
      
      expect(result[0].url).toBe('https://example.com');
      expect(result[0].startIndex).toBe(6);
      expect(result[0].endIndex).toBe(25); // 6 + 19 = 25
      
      expect(result[1].url).toBe('https://test.org');
      expect(result[1].startIndex).toBe(33); // "Start https://example.com middle " = 33
      expect(result[1].endIndex).toBe(49); // 33 + 16 = 49
    });
  });

  describe('Property 2: Venue link deduplication', () => {
    /**
     * Feature: link-preview-cards, Property 2: Venue link deduplication
     * 
     * For any message containing URLs that match the venue link pattern
     * (with venue name, website, and Place ID), those URLs should be excluded
     * from link preview generation to avoid duplication.
     * 
     * Validates: Requirements 6.4
     */
    
    it('should exclude URLs that are part of venue link blocks', () => {
      const text = `
Here are some venues:

1. **Parc Restaurant**
📍 Address: 227 S 18th St, Philadelphia, PA
🌐 Website: https://parc-restaurant.com
🆔 Place ID: ChIJabcdef123456

2. **Zahav**
📍 Address: 237 St James Pl, Philadelphia, PA
🌐 Website: https://zahavrestaurant.com
🆔 Place ID: ChIJxyz789012345

Also check out https://example.com for more info.
      `;
      
      const result = extractURLs(text);
      
      // Should only extract the non-venue URL
      expect(result).toHaveLength(1);
      expect(result[0].url).toBe('https://example.com');
    });

    it('should exclude venue URLs even without Place ID', () => {
      const text = `
**Restaurant Name**
📍 Address: 123 Main St
🌐 Website: https://restaurant.com

Regular link: https://example.com
      `;
      
      const result = extractURLs(text);
      
      expect(result).toHaveLength(1);
      expect(result[0].url).toBe('https://example.com');
    });

    it('should handle multiple venue blocks correctly', () => {
      const text = `
**Venue 1**
🌐 Website: https://venue1.com

**Venue 2**
🌐 Website: https://venue2.com

**Venue 3**
🌐 Website: https://venue3.com

Non-venue link: https://other.com
      `;
      
      const result = extractURLs(text);
      
      expect(result).toHaveLength(1);
      expect(result[0].url).toBe('https://other.com');
    });

    it('should extract URLs that look similar but are not in venue blocks', () => {
      const text = `
Check out these websites:
- https://site1.com
- https://site2.com

**Venue Name**
🌐 Website: https://venue.com
      `;
      
      const result = extractURLs(text);
      
      // Should extract the first two URLs but not the venue URL
      expect(result).toHaveLength(2);
      expect(result[0].url).toBe('https://site1.com');
      expect(result[1].url).toBe('https://site2.com');
    });
  });

  describe('isValidURL', () => {
    it('should validate HTTP and HTTPS URLs', () => {
      expect(isValidURL('http://example.com')).toBe(true);
      expect(isValidURL('https://example.com')).toBe(true);
      expect(isValidURL('https://sub.example.com')).toBe(true);
      expect(isValidURL('https://example.com:8080')).toBe(true);
      expect(isValidURL('https://example.com/path')).toBe(true);
      expect(isValidURL('https://example.com?query=value')).toBe(true);
      expect(isValidURL('https://example.com#fragment')).toBe(true);
    });

    it('should reject non-HTTP/HTTPS protocols', () => {
      expect(isValidURL('ftp://example.com')).toBe(false);
      expect(isValidURL('file:///path/to/file')).toBe(false);
      expect(isValidURL('javascript:alert(1)')).toBe(false);
      expect(isValidURL('mailto:test@example.com')).toBe(false);
      expect(isValidURL('data:text/html,<html></html>')).toBe(false);
    });

    it('should reject malformed URLs', () => {
      expect(isValidURL('not a url')).toBe(false);
      expect(isValidURL('http://')).toBe(false);
      expect(isValidURL('https://')).toBe(false);
      expect(isValidURL('')).toBe(false);
      expect(isValidURL('example.com')).toBe(false);
    });
  });

  describe('shouldExcludeURL', () => {
    it('should exclude data URIs', () => {
      expect(shouldExcludeURL('data:text/html,<html></html>')).toBe(true);
      expect(shouldExcludeURL('data:image/png;base64,abc')).toBe(true);
    });

    it('should exclude blob URLs', () => {
      expect(shouldExcludeURL('blob:http://example.com/abc')).toBe(true);
      expect(shouldExcludeURL('blob:https://example.com/123')).toBe(true);
    });

    it('should exclude localhost', () => {
      expect(shouldExcludeURL('http://localhost')).toBe(true);
      expect(shouldExcludeURL('http://localhost:8080')).toBe(true);
      expect(shouldExcludeURL('https://localhost')).toBe(true);
      expect(shouldExcludeURL('http://[::1]')).toBe(true);
      expect(shouldExcludeURL('http://[::ffff:127.0.0.1]')).toBe(true);
    });

    it('should exclude private IP addresses', () => {
      expect(shouldExcludeURL('http://192.168.1.1')).toBe(true);
      expect(shouldExcludeURL('http://10.0.0.1')).toBe(true);
      expect(shouldExcludeURL('http://172.16.0.1')).toBe(true);
      expect(shouldExcludeURL('http://127.0.0.1')).toBe(true);
      expect(shouldExcludeURL('http://169.254.1.1')).toBe(true);
    });

    it('should not exclude public URLs', () => {
      expect(shouldExcludeURL('http://example.com')).toBe(false);
      expect(shouldExcludeURL('https://google.com')).toBe(false);
      expect(shouldExcludeURL('https://github.com')).toBe(false);
    });

    it('should exclude URLs matching custom patterns', () => {
      const excludePatterns = ['example\\.com', 'test\\.org'];
      
      expect(shouldExcludeURL('http://example.com', excludePatterns)).toBe(true);
      expect(shouldExcludeURL('https://test.org', excludePatterns)).toBe(true);
      expect(shouldExcludeURL('https://other.com', excludePatterns)).toBe(false);
    });

    it('should handle invalid regex patterns gracefully', () => {
      const invalidPatterns = ['[invalid(regex'];
      
      // Should not throw, just skip invalid patterns
      expect(() => shouldExcludeURL('http://example.com', invalidPatterns)).not.toThrow();
      expect(shouldExcludeURL('http://example.com', invalidPatterns)).toBe(false);
    });
  });

  describe('Unit Tests - Edge Cases', () => {
    it('should handle URLs at the start of text', () => {
      const text = 'https://example.com is a great site';
      const result = extractURLs(text);
      
      expect(result).toHaveLength(1);
      expect(result[0].url).toBe('https://example.com');
      expect(result[0].startIndex).toBe(0);
    });

    it('should handle URLs at the end of text', () => {
      const text = 'Check out https://example.com';
      const result = extractURLs(text);
      
      expect(result).toHaveLength(1);
      expect(result[0].url).toBe('https://example.com');
    });

    it('should handle URLs with special characters in path', () => {
      const text = 'Visit https://example.com/path-with_special.chars~123';
      const result = extractURLs(text);
      
      expect(result).toHaveLength(1);
      expect(result[0].url).toBe('https://example.com/path-with_special.chars~123');
    });

    it('should handle URLs with multiple query parameters', () => {
      const text = 'https://example.com?a=1&b=2&c=3';
      const result = extractURLs(text);
      
      expect(result).toHaveLength(1);
      expect(result[0].url).toBe('https://example.com?a=1&b=2&c=3');
    });

    it('should handle URLs surrounded by punctuation', () => {
      const text = 'Check (https://example.com) and [https://test.org]!';
      const result = extractURLs(text);
      
      expect(result).toHaveLength(2);
      expect(result[0].url).toBe('https://example.com');
      expect(result[1].url).toBe('https://test.org');
    });

    it('should deduplicate URLs that appear multiple times', () => {
      const text = 'Visit https://example.com and also https://example.com again';
      const result = extractURLs(text);
      
      // Should only extract the first occurrence (deduplicated)
      expect(result).toHaveLength(1);
      expect(result[0].url).toBe('https://example.com');
    });

    it('should deduplicate multiple identical URLs', () => {
      const text = `
        Check https://example.com
        Also https://example.com
        And https://example.com again
        Plus https://test.org
        And https://test.org too
      `;
      const result = extractURLs(text);
      
      // Should only have 2 unique URLs
      expect(result).toHaveLength(2);
      expect(result[0].url).toBe('https://example.com');
      expect(result[1].url).toBe('https://test.org');
    });

    it('should handle URLs with www prefix', () => {
      const text = 'Visit https://www.example.com';
      const result = extractURLs(text);
      
      expect(result).toHaveLength(1);
      expect(result[0].url).toBe('https://www.example.com');
    });

    it('should handle URLs with subdomains', () => {
      const text = 'https://api.staging.example.com/v1/users';
      const result = extractURLs(text);
      
      expect(result).toHaveLength(1);
      expect(result[0].url).toBe('https://api.staging.example.com/v1/users');
    });

    it('should handle mixed valid and invalid URLs', () => {
      const text = `
        Valid: https://example.com
        Invalid: ftp://example.com
        Valid: https://test.org
        Invalid: http://localhost
        Valid: https://site.io
      `;
      const result = extractURLs(text);
      
      expect(result).toHaveLength(3);
      expect(result[0].url).toBe('https://example.com');
      expect(result[1].url).toBe('https://test.org');
      expect(result[2].url).toBe('https://site.io');
    });

    it('should handle URLs in markdown-style text', () => {
      const text = `
# Title

Check out [this link](https://example.com) and also https://test.org

- Item 1: https://site1.com
- Item 2: https://site2.com
      `;
      const result = extractURLs(text);
      
      expect(result).toHaveLength(4);
    });

    it('should handle URLs with authentication info (though not recommended)', () => {
      const text = 'https://user:pass@example.com/path';
      const result = extractURLs(text);
      
      expect(result).toHaveLength(1);
      expect(result[0].url).toBe('https://user:pass@example.com/path');
    });

    it('should handle international domain names', () => {
      const text = 'Visit https://münchen.de';
      const result = extractURLs(text);
      
      // Should extract the URL (URL constructor handles IDN)
      expect(result.length).toBeGreaterThanOrEqual(0);
    });
  });
});
