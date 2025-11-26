/**
 * URL extraction utility for link preview cards
 * Extracts valid HTTP/HTTPS URLs from message text and applies exclusion rules
 * 
 * Requirements:
 * - 1.1: Extract all valid HTTP/HTTPS URLs from message content
 * - 6.1: Exclude localhost and internal IP addresses
 * - 6.2: Exclude data URIs and blob URLs
 * - 6.3: Exclude malformed URLs
 * - 6.4: Exclude URLs already handled by venue links feature
 */

import type { ExtractedURL } from '../types/linkPreview';

export type { ExtractedURL };

/**
 * Regular expression to match HTTP/HTTPS URLs
 * Matches URLs with:
 * - http:// or https:// protocol
 * - Domain name or IP address
 * - Optional port, path, query parameters, and fragments
 * 
 * Note: We use a negative lookbehind to avoid matching URLs inside blob: or data: URIs
 */
const URL_REGEX = /(?<!blob:|data:)https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_+.~#?&/=]*)/gi;

/**
 * Private IP address ranges (RFC 1918)
 */
const PRIVATE_IP_PATTERNS = [
  /^https?:\/\/10\.\d{1,3}\.\d{1,3}\.\d{1,3}/,           // 10.0.0.0/8
  /^https?:\/\/172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}/, // 172.16.0.0/12
  /^https?:\/\/192\.168\.\d{1,3}\.\d{1,3}/,              // 192.168.0.0/16
  /^https?:\/\/127\.\d{1,3}\.\d{1,3}\.\d{1,3}/,          // 127.0.0.0/8 (loopback)
  /^https?:\/\/169\.254\.\d{1,3}\.\d{1,3}/,              // 169.254.0.0/16 (link-local)
];

/**
 * Localhost patterns
 */
const LOCALHOST_PATTERNS = [
  /^https?:\/\/localhost(?::\d+)?(?:\/|$)/i,
  /^https?:\/\/\[::1\](?::\d+)?(?:\/|$)/i,  // IPv6 loopback
  /^https?:\/\/\[::ffff:127\.0\.0\.1\](?::\d+)?(?:\/|$)/i,  // IPv6-mapped IPv4 loopback
];

/**
 * Venue link pattern - matches URLs that appear in venue link blocks
 * Looks for the pattern used in Message.tsx:
 * - Venue name in bold: **Name**
 * - Website line: 🌐 Website: https://...
 * - Optional Place ID: Place ID: ChI...
 */
const VENUE_LINK_PATTERN = /\*\*[^*]+\*\*[\s\S]*?🌐\s*Website:\s*(https?:\/\/[^\s\n]+)/gi;

/**
 * Validates if a string is a properly formatted URL
 * 
 * @param url - The URL string to validate
 * @returns true if the URL is valid, false otherwise
 */
export function isValidURL(url: string): boolean {
  try {
    const urlObj = new URL(url);
    
    // Only allow HTTP and HTTPS protocols
    if (urlObj.protocol !== 'http:' && urlObj.protocol !== 'https:') {
      return false;
    }
    
    // Must have a hostname
    if (!urlObj.hostname) {
      return false;
    }
    
    return true;
  } catch {
    // URL constructor throws for invalid URLs
    return false;
  }
}

/**
 * Checks if a URL should be excluded from preview generation
 * 
 * Exclusion rules:
 * - localhost addresses
 * - Private IP addresses (10.x.x.x, 172.16-31.x.x, 192.168.x.x, 127.x.x.x)
 * - Link-local addresses (169.254.x.x)
 * - Data URIs (data:)
 * - Blob URLs (blob:)
 * - URLs matching custom exclusion patterns
 * 
 * @param url - The URL to check
 * @param excludePatterns - Optional array of regex patterns to exclude
 * @returns true if the URL should be excluded, false otherwise
 */
export function shouldExcludeURL(url: string, excludePatterns: string[] = []): boolean {
  // Exclude data URIs
  if (url.startsWith('data:')) {
    return true;
  }
  
  // Exclude blob URLs
  if (url.startsWith('blob:')) {
    return true;
  }
  
  // Check localhost patterns
  for (const pattern of LOCALHOST_PATTERNS) {
    if (pattern.test(url)) {
      return true;
    }
  }
  
  // Check private IP patterns
  for (const pattern of PRIVATE_IP_PATTERNS) {
    if (pattern.test(url)) {
      return true;
    }
  }
  
  // Check custom exclusion patterns
  for (const patternStr of excludePatterns) {
    try {
      const pattern = new RegExp(patternStr, 'i');
      if (pattern.test(url)) {
        return true;
      }
    } catch {
      // Invalid regex pattern, skip it
      continue;
    }
  }
  
  return false;
}

/**
 * Extracts venue link URLs from message content
 * These URLs should be excluded from link preview generation
 * to avoid duplication with the venue link buttons
 * 
 * @param text - The message content to search
 * @returns Array of venue link URLs
 */
function extractVenueLinkURLs(text: string): string[] {
  const venueURLs: string[] = [];
  const matches = text.matchAll(VENUE_LINK_PATTERN);
  
  for (const match of matches) {
    if (match[1]) {
      venueURLs.push(match[1].trim());
    }
  }
  
  return venueURLs;
}

/**
 * Extracts all valid HTTP/HTTPS URLs from message text
 * Applies validation and exclusion rules
 * Deduplicates URLs to ensure each unique URL appears only once
 * 
 * @param text - The message content to extract URLs from
 * @param excludePatterns - Optional array of regex patterns to exclude
 * @returns Array of ExtractedURL objects with positions (deduplicated)
 */
export function extractURLs(text: string, excludePatterns: string[] = []): ExtractedURL[] {
  if (!text) {
    return [];
  }
  
  const extractedURLs: ExtractedURL[] = [];
  const seenURLs = new Set<string>();
  
  // First, extract venue link URLs to exclude them
  const venueLinkURLs = extractVenueLinkURLs(text);
  const venueLinkSet = new Set(venueLinkURLs);
  
  // Find all URL matches
  const matches = text.matchAll(URL_REGEX);
  
  for (const match of matches) {
    let url = match[0];
    let startIndex = match.index!;
    
    // Trim trailing punctuation that's not part of the URL
    // Common punctuation that might follow a URL: ), ], !, ., ,
    const trailingPunctuation = /[)\]!.,]+$/;
    const trimmed = url.replace(trailingPunctuation, '');
    if (trimmed !== url) {
      url = trimmed;
    }
    
    const endIndex = startIndex + url.length;
    
    // Validate URL format
    if (!isValidURL(url)) {
      continue;
    }
    
    // Check if URL should be excluded
    if (shouldExcludeURL(url, excludePatterns)) {
      continue;
    }
    
    // Check if URL is a venue link (avoid duplication)
    if (venueLinkSet.has(url)) {
      continue;
    }
    
    // Deduplicate: skip if we've already seen this URL
    if (seenURLs.has(url)) {
      continue;
    }
    
    seenURLs.add(url);
    extractedURLs.push({
      url,
      startIndex,
      endIndex,
    });
  }
  
  return extractedURLs;
}
