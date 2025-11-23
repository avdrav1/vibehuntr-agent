# Link Preview Cards Feature

## Overview

The Link Preview Cards feature automatically generates rich, visual preview cards for URLs included in chat messages. When the AI agent shares links in its responses, users see beautiful preview cards with metadata including titles, descriptions, images, and favicons - similar to how links appear in Slack, Discord, or Twitter.

This feature enhances the user experience by:
- **Providing context** - Users can see what a link contains before clicking
- **Improving trust** - Rich previews make links feel more legitimate and safe
- **Enhancing aesthetics** - Preview cards match the Vibehuntr design language
- **Saving time** - Users can quickly scan link content without leaving the chat

## Architecture

The feature uses a client-server architecture to avoid CORS issues and enable efficient caching:

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ URL Extractor  │→ │ LinkPreview  │→ │ PreviewCard UI │  │
│  └────────────────┘  └──────────────┘  └────────────────┘  │
└─────────────────────────────┬───────────────────────────────┘
                              │ POST /api/link-preview
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │ API Endpoint │→ │ HTML Fetcher│→ │ Metadata Parser  │   │
│  └──────────────┘  └─────────────┘  └──────────────────┘   │
│                           ↓                                  │
│                    ┌─────────────┐                           │
│                    │    Cache    │                           │
│                    └─────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

**Frontend:**
- **URL Extractor** (`frontend/src/utils/urlExtractor.ts`) - Detects and validates URLs in messages
- **LinkPreview Component** (`frontend/src/components/LinkPreview.tsx`) - Manages state and fetches metadata
- **PreviewCard Component** (`frontend/src/components/PreviewCard.tsx`) - Renders the visual card

**Backend:**
- **API Endpoint** (`backend/app/api/link_preview.py`) - Handles metadata requests
- **Metadata Fetcher** (`backend/app/services/metadata_fetcher.py`) - Fetches HTML from URLs
- **HTML Parser** (`backend/app/services/html_parser.py`) - Extracts metadata from HTML
- **Metadata Cache** (`backend/app/services/metadata_cache.py`) - Caches results for performance

## Features

### Automatic URL Detection

The system automatically detects HTTP and HTTPS URLs in assistant messages and generates previews without any user action required.

### Rich Metadata Extraction

Preview cards display:
- **Title** - From Open Graph, Twitter Card, or HTML title tag
- **Description** - From meta tags or Open Graph description
- **Image** - Preview image from Open Graph or Twitter Card
- **Favicon** - Site icon for branding
- **Domain** - Clean domain name display

### Smart Exclusions

The system intelligently excludes certain URLs from preview generation:
- Localhost and private IP addresses (10.x.x.x, 192.168.x.x, 127.x.x.x)
- Data URIs and blob URLs
- URLs already handled by the venue links feature
- Configurable domain exclusions

### Graceful Error Handling

When metadata cannot be fetched:
- **404/5xx errors** - Shows minimal card with domain name
- **Timeouts** - Shows minimal card after 5 seconds
- **Parse failures** - Falls back to available metadata
- **Image load failures** - Hides image, shows text-only card

### Performance Optimization

- **Caching** - Metadata cached for 1 hour (configurable)
- **Async loading** - Message content renders immediately, previews load in background
- **Timeout protection** - 5-second timeout prevents slow sites from blocking UI
- **Connection pooling** - Efficient HTTP request handling

### Accessibility

Preview cards are fully accessible:
- ARIA labels and roles for screen readers
- Keyboard navigation support (Tab, Enter)
- Focus indicators
- Alt text for images
- Semantic HTML structure

## Configuration

### Backend Configuration

Configure the backend via environment variables in `backend/app/core/config.py`:

```python
# Enable/disable the feature
LINK_PREVIEW_ENABLED = True

# Fetch timeout in seconds
LINK_PREVIEW_TIMEOUT = 5

# Cache TTL in seconds (1 hour)
LINK_PREVIEW_CACHE_TTL = 3600

# Max response size in bytes (5MB)
LINK_PREVIEW_MAX_SIZE = 5000000

# Excluded domains (comma-separated)
LINK_PREVIEW_EXCLUDED_DOMAINS = ""
```

### Frontend Configuration

Configure the frontend via environment variables in `frontend/.env`:

```bash
# Enable/disable the feature
VITE_LINK_PREVIEW_ENABLED=true
```

### Excluding Specific Domains

To exclude specific domains from preview generation, set the `LINK_PREVIEW_EXCLUDED_DOMAINS` environment variable:

```bash
# Backend .env
LINK_PREVIEW_EXCLUDED_DOMAINS=example.com,test.org,internal.company.com
```

### Adjusting Cache TTL

To change how long metadata is cached:

```bash
# Backend .env
LINK_PREVIEW_CACHE_TTL=7200  # 2 hours in seconds
```

### Adjusting Timeout

To change the fetch timeout:

```bash
# Backend .env
LINK_PREVIEW_TIMEOUT=10  # 10 seconds
```

## Usage Examples

### Basic Usage

When the agent includes a URL in its response:

```
Agent: Check out this article about AI: https://example.com/ai-article
```

The system automatically displays a preview card below the message:

```
┌─────────────────────────────────────────────┐
│ [🌐] The Future of AI                       │
│ An in-depth look at artificial intelligence │
│ and its impact on society...                │
│ ┌─────────────────────────────────────────┐ │
│ │                                         │ │
│ │      [Preview Image]                    │ │
│ │                                         │ │
│ └─────────────────────────────────────────┘ │
│ 🔗 example.com                              │
└─────────────────────────────────────────────┘
```

### Multiple URLs

When multiple URLs are present, each gets its own preview card:

```
Agent: Here are some resources:
- https://example.com/resource1
- https://example.com/resource2
```

Both URLs will have preview cards displayed in order.

### Integration with Venue Links

The feature works seamlessly with the existing venue links feature. URLs that are already handled as venue links (with Place ID) won't show duplicate preview cards.

## Exclusion Patterns

### Automatic Exclusions

The following URL patterns are automatically excluded:

**Localhost and Private IPs:**
- `http://localhost:*`
- `http://127.0.0.1:*`
- `http://10.*.*.*`
- `http://192.168.*.*`
- `http://172.16.*.*` through `http://172.31.*.*`

**Special URLs:**
- `data:*` (data URIs)
- `blob:*` (blob URLs)
- `javascript:*` (JavaScript URIs)

**Venue Links:**
URLs matching the venue link pattern with Place ID are excluded to prevent duplication.

### Custom Exclusions

Add custom domain exclusions via configuration:

```bash
LINK_PREVIEW_EXCLUDED_DOMAINS=internal.company.com,staging.example.com
```

## Troubleshooting

### Preview Cards Not Appearing

**Problem:** URLs in messages don't show preview cards

**Solutions:**
1. Check that `VITE_LINK_PREVIEW_ENABLED=true` in frontend `.env`
2. Check that `LINK_PREVIEW_ENABLED=True` in backend config
3. Verify the URL is not in an exclusion pattern
4. Check browser console for JavaScript errors
5. Check backend logs for API errors

### Preview Shows "Unable to Load"

**Problem:** Preview card shows error message instead of metadata

**Solutions:**
1. Check if the URL is accessible from the backend server
2. Verify the URL returns valid HTML (not JSON or binary)
3. Check if the site blocks bots (User-Agent: VibehuntrBot/1.0)
4. Increase timeout if site is slow: `LINK_PREVIEW_TIMEOUT=10`
5. Check backend logs for specific error messages

### Preview Takes Too Long to Load

**Problem:** Preview cards appear slowly or timeout

**Solutions:**
1. Reduce timeout: `LINK_PREVIEW_TIMEOUT=3`
2. Check network connectivity from backend to target sites
3. Verify cache is working (check cache hit rate in logs)
4. Consider excluding slow domains: `LINK_PREVIEW_EXCLUDED_DOMAINS=slow-site.com`

### Images Not Displaying

**Problem:** Preview cards show text but no images

**Solutions:**
1. Check if image URLs are absolute (not relative)
2. Verify image URLs are accessible (not behind authentication)
3. Check browser console for CORS or CSP errors
4. Verify image URLs use HTTPS (mixed content issues)
5. Check if images are too large (>5MB limit)

### Cache Not Working

**Problem:** Same URLs fetch metadata repeatedly

**Solutions:**
1. Verify cache TTL is set: `LINK_PREVIEW_CACHE_TTL=3600`
2. Check backend logs for cache hit/miss rates
3. Ensure backend server has sufficient memory
4. Consider using Redis for distributed caching (future enhancement)

### Specific Domain Always Fails

**Problem:** One domain never shows previews

**Solutions:**
1. Check if domain blocks bots (check robots.txt)
2. Verify domain has Open Graph or meta tags
3. Test URL manually with curl: `curl -A "VibehuntrBot/1.0" https://example.com`
4. Check if domain requires authentication
5. Add domain to exclusions if it's not meant to be previewed

## Performance Considerations

### Backend Performance

**Caching Strategy:**
- Successful fetches cached for 1 hour
- Failed fetches cached for 5 minutes (shorter TTL)
- LRU eviction when cache exceeds 1000 entries
- Cache key is normalized URL

**Request Optimization:**
- Connection pooling via httpx
- Async/await for parallel fetching
- Request deduplication (same URL fetched once)
- Response size limit (5MB)
- HTML parsing limited to first 100KB

**Expected Performance:**
- Cache hit: <10ms
- Cache miss: 500ms - 5s (depends on target site)
- Timeout: 5s maximum

### Frontend Performance

**Rendering Optimization:**
- React.memo for PreviewCard component
- Lazy loading (future enhancement)
- Debouncing for streaming messages
- CSS containment for preview cards

**Network Optimization:**
- Batch requests for multiple URLs
- Abort ongoing requests when scrolling away
- Progressive rendering (message first, previews after)

### Monitoring Metrics

Track these metrics for performance monitoring:

- **Fetch success rate** - Should be >80%
- **Average fetch time** - Should be <3s
- **Cache hit rate** - Should be >50%
- **Error rate** - Should be <20%
- **Previews per message** - Typical: 1-3

## Security Considerations

### URL Validation

- Only HTTP and HTTPS schemes allowed
- Private IP ranges blocked
- Localhost blocked
- URL format validated before fetching

### Fetch Security

- User-Agent identifies bot: "VibehuntrBot/1.0"
- Redirect limit: 3 maximum
- Timeout enforced: 5 seconds
- Response size limited: 5MB
- No redirect to private IPs

### Content Security

- Extracted text sanitized (no scripts)
- Image URLs validated before display
- External links use `rel="noopener noreferrer"`
- No JavaScript execution from fetched pages
- No HTML rendering from fetched pages (text only)

### Rate Limiting

- Preview requests limited per session (50/hour)
- Concurrent fetches limited per session (5)
- Cache reduces external requests
- Cached errors prevent retry storms

## Testing

The feature includes comprehensive test coverage:

### Unit Tests

**Frontend:**
- `frontend/src/utils/urlExtractor.test.ts` - URL extraction logic
- `frontend/src/components/LinkPreview.test.tsx` - Component state management
- `frontend/src/components/PreviewCard.test.tsx` - Card rendering
- `frontend/src/services/api.test.ts` - API client

**Backend:**
- `backend/tests/test_metadata_fetcher.py` - HTML fetching
- `backend/tests/test_html_parser.py` - Metadata extraction
- `backend/tests/test_metadata_cache.py` - Caching logic
- `backend/tests/test_link_preview_api.py` - API endpoint

### Property-Based Tests

- `tests/property/test_properties_link_preview.py` - Backend properties
- `frontend/src/components/*.property.test.tsx` - Frontend properties

### Integration Tests

- `frontend/src/test/link-preview-e2e.test.tsx` - End-to-end flow
- `backend/tests/test_link_preview_api.py` - API integration

### Running Tests

```bash
# Backend tests
cd backend
uv run pytest tests/test_metadata_fetcher.py
uv run pytest tests/test_html_parser.py
uv run pytest tests/test_metadata_cache.py
uv run pytest tests/test_link_preview_api.py

# Frontend tests
cd frontend
npm test -- urlExtractor.test.ts
npm test -- LinkPreview.test.tsx
npm test -- PreviewCard.test.tsx

# Property-based tests
cd backend
uv run pytest tests/property/test_properties_link_preview.py

# Integration tests
cd frontend
npm test -- link-preview-e2e.test.tsx
```

## Future Enhancements

### Phase 2 Features

- **Video embeds** - Detect and embed YouTube, Vimeo videos
- **Rich embeds** - Support for Twitter, GitHub, Spotify embeds
- **PDF previews** - Show first page thumbnail for PDF links
- **Link unfurling** - Expand shortened URLs (bit.ly, tinyurl)

### Phase 3 Features

- **User preferences** - Allow users to disable previews
- **Preview editing** - Let users customize preview appearance
- **Analytics** - Track which previews are clicked
- **A/B testing** - Test different preview layouts

### Infrastructure Improvements

- **Redis caching** - Replace in-memory cache with Redis
- **CDN integration** - Cache preview images on CDN
- **Microservice** - Extract preview service to separate deployment
- **Enhanced rate limiting** - Implement per-user rate limits

## API Reference

### POST /api/link-preview

Fetch metadata for one or more URLs.

**Request:**
```json
{
  "urls": ["https://example.com", "https://example.org"],
  "session_id": "session-123"
}
```

**Response:**
```json
{
  "previews": [
    {
      "url": "https://example.com",
      "title": "Example Domain",
      "description": "This domain is for use in illustrative examples",
      "image": "https://example.com/image.jpg",
      "favicon": "https://example.com/favicon.ico",
      "domain": "example.com",
      "error": null
    },
    {
      "url": "https://example.org",
      "title": null,
      "description": null,
      "image": null,
      "favicon": null,
      "domain": "example.org",
      "error": "Failed to fetch: Connection timeout"
    }
  ]
}
```

**Error Response:**
```json
{
  "detail": "Invalid request: urls must be a non-empty list"
}
```

## Support

For issues or questions:

1. Check this documentation first
2. Review the troubleshooting section
3. Check backend logs: `logs/backend.log`
4. Check browser console for frontend errors
5. Review test files for usage examples
6. Contact the development team

## Related Documentation

- [Requirements Document](./requirements.md) - Feature requirements and acceptance criteria
- [Design Document](./design.md) - Technical design and architecture
- [Configuration Guide](./CONFIGURATION.md) - Detailed configuration options
- [Tasks Document](./tasks.md) - Implementation task list
