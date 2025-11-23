# Implementation Plan

- [x] 1. Set up backend infrastructure for link preview API
  - Create API endpoint structure and models
  - Set up error handling and logging
  - _Requirements: 3.1, 3.4_

- [x] 1.1 Create backend data models for link preview
  - Create `backend/app/models/link_preview.py` with Pydantic models
  - Define `LinkPreviewRequest`, `LinkMetadata`, `LinkPreviewResponse`
  - Add validation for URL format and required fields
  - _Requirements: 3.4_

- [x] 1.2 Create link preview API endpoint
  - Create `backend/app/api/link_preview.py` with FastAPI router
  - Implement POST `/api/link-preview` endpoint
  - Add request validation and error handling
  - Return structured metadata response
  - _Requirements: 3.1, 3.4_

- [x] 1.3 Register link preview router in main app
  - Import and include link preview router in `backend/app/main.py`
  - Verify endpoint is accessible at `/api/link-preview`
  - _Requirements: 3.1_

- [x] 2. Implement metadata fetching service
  - Create service to fetch HTML from URLs
  - Handle timeouts, redirects, and errors
  - _Requirements: 3.2, 5.1, 5.2_

- [x] 2.1 Create metadata fetcher service
  - Create `backend/app/services/metadata_fetcher.py`
  - Implement `MetadataFetcher` class with async HTTP client (httpx)
  - Add `fetch_html()` method with 5-second timeout
  - Implement URL validation and exclusion logic
  - Handle connection errors, timeouts, and HTTP errors
  - _Requirements: 3.2, 5.1, 5.2, 6.1, 6.2, 6.3_

- [x] 2.2 Write property test for metadata fetcher
  - **Property 11: Fetch timeout**
  - **Validates: Requirements 4.4**

- [x] 2.3 Write unit tests for metadata fetcher
  - Test successful HTML fetch
  - Test timeout handling
  - Test connection error handling
  - Test URL validation
  - Test exclusion patterns (localhost, private IPs, data URIs)
  - _Requirements: 3.2, 5.1, 5.2, 6.2, 6.3_

- [x] 3. Implement HTML parsing service
  - Create service to extract metadata from HTML
  - Parse Open Graph, Twitter Card, and standard meta tags
  - _Requirements: 3.3, 5.4_

- [x] 3.1 Create HTML parser service
  - Create `backend/app/services/html_parser.py`
  - Implement `HTMLParser` class using BeautifulSoup4
  - Add `parse_metadata()` method
  - Extract Open Graph tags (og:title, og:description, og:image)
  - Extract Twitter Card tags (twitter:title, twitter:description, twitter:image)
  - Extract standard meta tags (title, description)
  - Resolve relative URLs to absolute
  - Extract favicon from link tags or /favicon.ico
  - _Requirements: 3.3_

- [x] 3.2 Write property test for HTML parser robustness
  - **Property 12: HTML parsing robustness**
  - **Validates: Requirements 3.3, 5.4**

- [x] 3.3 Write unit tests for HTML parser
  - Test Open Graph tag extraction
  - Test Twitter Card tag extraction
  - Test standard meta tag extraction
  - Test malformed HTML handling
  - Test relative URL resolution
  - Test missing tags fallback
  - _Requirements: 3.3, 5.4_

- [x] 4. Implement metadata caching service
  - Create in-memory cache for metadata
  - Implement TTL and LRU eviction
  - _Requirements: 3.5_

- [x] 4.1 Create metadata cache service
  - Create `backend/app/services/metadata_cache.py`
  - Implement `MetadataCache` class with in-memory dict
  - Add `get()` and `set()` methods
  - Implement TTL (1 hour default)
  - Implement LRU eviction (max 1000 entries)
  - Make thread-safe with asyncio locks
  - _Requirements: 3.5_

- [x] 4.2 Write property test for metadata caching
  - **Property 9: Metadata caching**
  - **Validates: Requirements 3.5**

- [x] 4.3 Write unit tests for metadata cache
  - Test cache hit returns cached data
  - Test cache miss returns None
  - Test cache expiration after TTL
  - Test LRU eviction when cache is full
  - Test thread safety with concurrent access
  - _Requirements: 3.5_

- [x] 5. Integrate services in link preview endpoint
  - Wire up fetcher, parser, and cache in API endpoint
  - Implement error handling and response formatting
  - _Requirements: 1.2, 1.4, 3.1, 3.4_

- [x] 5.1 Implement link preview endpoint logic
  - Update `backend/app/api/link_preview.py` endpoint
  - For each URL: check cache, fetch HTML, parse metadata
  - Handle errors gracefully (return error in metadata object)
  - Return response with all metadata objects
  - _Requirements: 1.2, 1.4, 3.1, 3.4_

- [x] 5.2 Write property test for metadata fetch attempt
  - **Property 3: Metadata fetch attempt**
  - **Validates: Requirements 1.2, 3.2, 3.3, 3.4**

- [x] 5.3 Write integration tests for link preview API
  - Test successful metadata fetch for valid URL
  - Test error handling for 404 response
  - Test error handling for timeout
  - Test multiple URLs in single request
  - Test cache hit scenario
  - _Requirements: 1.2, 1.4, 3.1, 3.5_

- [x] 6. Checkpoint - Ensure backend tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Create frontend URL extraction utility
  - Implement URL detection and validation
  - Add exclusion logic for venue links and special URLs
  - _Requirements: 1.1, 6.1, 6.2, 6.3, 6.4_

- [x] 7.1 Create URL extractor utility
  - Create `frontend/src/utils/urlExtractor.ts`
  - Implement `extractURLs()` function with regex
  - Implement `isValidURL()` validation
  - Implement `shouldExcludeURL()` with exclusion patterns
  - Exclude localhost, private IPs, data URIs, blob URLs
  - Exclude URLs matching venue link pattern
  - Return array of `ExtractedURL` objects with positions
  - _Requirements: 1.1, 6.1, 6.2, 6.3, 6.4_

- [x] 7.2 Write property test for URL extraction completeness
  - **Property 1: URL extraction completeness**
  - **Validates: Requirements 1.1, 6.1, 6.2, 6.3, 6.5**

- [x] 7.3 Write property test for venue link deduplication
  - **Property 2: Venue link deduplication**
  - **Validates: Requirements 6.4**

- [x] 7.4 Write unit tests for URL extractor
  - Test single URL extraction
  - Test multiple URL extraction
  - Test no URLs in message
  - Test URLs with query parameters and fragments
  - Test malformed URL rejection
  - Test localhost exclusion
  - Test private IP exclusion
  - Test data URI exclusion
  - Test venue link pattern exclusion
  - _Requirements: 1.1, 6.1, 6.2, 6.3, 6.4_

- [x] 8. Create frontend API service for link preview
  - Add API client method to fetch metadata
  - Handle errors and timeouts
  - _Requirements: 3.1, 8.1_

- [x] 8.1 Add link preview API method to frontend service
  - Update `frontend/src/services/api.ts`
  - Add `fetchLinkPreviews()` function
  - Call POST `/api/link-preview` with URLs and session_id
  - Handle network errors with user-friendly messages
  - Return array of `LinkMetadata` objects
  - _Requirements: 3.1, 8.1_

- [x] 8.2 Write unit tests for link preview API client
  - Test successful API call
  - Test network error handling
  - Test timeout handling
  - Test error response handling
  - _Requirements: 3.1, 8.1_

- [x] 9. Create frontend type definitions
  - Define TypeScript interfaces for link preview data
  - _Requirements: 3.4_

- [x] 9.1 Create link preview type definitions
  - Create `frontend/src/types/linkPreview.ts`
  - Define `LinkMetadata` interface
  - Define `LinkPreviewRequest` interface
  - Define `LinkPreviewResponse` interface
  - Define `ExtractedURL` interface
  - Export all types
  - _Requirements: 3.4_

- [x] 10. Create PreviewCard UI component
  - Implement visual preview card with metadata
  - Handle loading and error states
  - _Requirements: 1.3, 1.4, 2.4, 2.5_

- [x] 10.1 Create PreviewCard component
  - Create `frontend/src/components/PreviewCard.tsx`
  - Accept `metadata` and `loading` props
  - Render card with title, description, image, favicon, domain
  - Show fallback icon when image is missing
  - Add Vibehuntr gradient border on hover
  - Include security attributes (target="_blank", rel="noopener noreferrer")
  - Add ARIA labels and roles for accessibility
  - Style with Tailwind CSS matching Vibehuntr theme
  - _Requirements: 1.3, 1.4, 2.4, 2.5, 7.1, 7.4_

- [x] 10.2 Write property test for preview card rendering
  - **Property 4: Preview card rendering with metadata**
  - **Validates: Requirements 1.3**

- [x] 10.3 Write property test for image fallback handling
  - **Property 7: Image fallback handling**
  - **Validates: Requirements 2.4, 5.5**

- [x] 10.4 Write unit tests for PreviewCard component
  - Test render with full metadata
  - Test render with partial metadata (no image)
  - Test render with loading state
  - Test render with error state
  - Test fallback icon when image missing
  - Test security attributes on link
  - Test ARIA labels present
  - Test image alt text present
  - _Requirements: 1.3, 1.4, 2.4, 2.5, 7.1, 7.4_

- [ ] 11. Create LinkPreview container component
  - Fetch metadata and manage state
  - Handle async loading and errors
  - _Requirements: 1.2, 1.4, 4.1, 4.2, 4.4_

- [ ] 11.1 Create LinkPreview component
  - Create `frontend/src/components/LinkPreview.tsx`
  - Accept `url` and `sessionId` props
  - Use `useState` for metadata and loading state
  - Use `useEffect` to fetch metadata on mount
  - Call `fetchLinkPreviews()` API method
  - Show loading skeleton while fetching
  - Render PreviewCard with fetched metadata
  - Handle fetch errors (show minimal card)
  - Handle timeout (show minimal card after 5 seconds)
  - _Requirements: 1.2, 1.4, 4.1, 4.2, 4.4_

- [ ] 11.2 Write property test for async rendering
  - **Property 10: Async rendering**
  - **Validates: Requirements 4.1**

- [ ] 11.3 Write unit tests for LinkPreview component
  - Test loading state displayed initially
  - Test preview card rendered after fetch
  - Test error state on fetch failure
  - Test timeout handling
  - Test minimal card on error
  - _Requirements: 1.2, 1.4, 4.1, 4.2, 4.4_

- [ ] 12. Enhance Message component with link previews
  - Integrate URL extraction and preview rendering
  - Maintain existing venue link functionality
  - _Requirements: 1.1, 1.5, 6.4_

- [ ] 12.1 Update Message component to include link previews
  - Update `frontend/src/components/Message.tsx`
  - Import `extractURLs` and `LinkPreview` components
  - Extract URLs from message content using `useMemo`
  - Filter out URLs already handled by venue links
  - Render LinkPreview component for each URL
  - Maintain existing venue link button functionality
  - Ensure previews render below message content
  - _Requirements: 1.1, 1.5, 6.4_

- [ ] 12.2 Write property test for multiple URL ordering
  - **Property 6: Multiple URL ordering**
  - **Validates: Requirements 1.5**

- [ ] 12.3 Write property test for frontend-backend integration
  - **Property 8: Frontend-backend integration**
  - **Validates: Requirements 3.1**

- [ ] 12.4 Write integration tests for Message component with link previews
  - Test message with single URL shows one preview
  - Test message with multiple URLs shows multiple previews in order
  - Test message with venue link URL doesn't duplicate preview
  - Test message with no URLs shows no previews
  - Test preview cards render after message content
  - _Requirements: 1.1, 1.5, 6.4_

- [ ] 13. Add CSS styling for link preview cards
  - Create Vibehuntr-themed styles for preview cards
  - Add loading skeleton styles
  - _Requirements: 2.1, 4.2_

- [ ] 13.1 Add link preview styles to index.css
  - Update `frontend/src/index.css`
  - Add `.link-preview-card` styles with gradient border
  - Add `.link-preview-loading` skeleton animation
  - Add `.link-preview-image` styles with aspect ratio
  - Add `.link-preview-fallback` styles for missing images
  - Add hover effects with Vibehuntr gradient
  - Ensure responsive design (mobile and desktop)
  - _Requirements: 2.1, 4.2_

- [ ] 14. Add configuration for link preview feature
  - Add environment variables for feature toggle and settings
  - _Requirements: 6.5_

- [ ] 14.1 Add backend configuration
  - Update `backend/app/core/config.py`
  - Add `LINK_PREVIEW_ENABLED` setting (default: True)
  - Add `LINK_PREVIEW_TIMEOUT` setting (default: 5)
  - Add `LINK_PREVIEW_CACHE_TTL` setting (default: 3600)
  - Add `LINK_PREVIEW_MAX_SIZE` setting (default: 5000000)
  - Add `LINK_PREVIEW_EXCLUDED_DOMAINS` setting (default: empty list)
  - _Requirements: 6.5_

- [ ] 14.2 Add frontend configuration
  - Update `frontend/.env.example`
  - Add `VITE_LINK_PREVIEW_ENABLED` variable
  - Document configuration options
  - _Requirements: 6.5_

- [ ] 15. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 16. Add error handling property test
  - Test error fallback behavior across various error scenarios
  - _Requirements: 1.4, 5.1, 5.2, 5.3, 5.4_

- [ ] 16.1 Write property test for error handling fallback
  - **Property 5: Error handling fallback**
  - **Validates: Requirements 1.4, 5.1, 5.2, 5.3, 5.4**

- [ ] 17. Add end-to-end integration test
  - Test complete flow from message to preview card display
  - _Requirements: 1.1, 1.2, 1.3, 3.1, 3.2, 3.3, 3.4_

- [ ] 17.1 Write end-to-end integration test
  - Create test that sends message with URL
  - Verify URL extraction
  - Verify API call to backend
  - Verify metadata fetch and parse
  - Verify preview card rendering
  - Test with mock HTTP responses
  - _Requirements: 1.1, 1.2, 1.3, 3.1, 3.2, 3.3, 3.4_

- [ ] 18. Update documentation
  - Document the link preview feature
  - Add usage examples and configuration guide
  - _Requirements: All_

- [ ] 18.1 Create link preview feature documentation
  - Create `.kiro/specs/link-preview-cards/README.md`
  - Document feature overview and benefits
  - Document configuration options
  - Add usage examples with screenshots
  - Document exclusion patterns
  - Add troubleshooting section
  - Document performance considerations
  - _Requirements: All_

- [ ] 18.2 Update main README
  - Update `README.md` or `frontend/README.md`
  - Add link preview feature to feature list
  - Link to detailed documentation
  - _Requirements: All_

- [ ] 19. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
