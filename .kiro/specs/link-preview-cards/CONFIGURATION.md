# Link Preview Configuration Guide

This document describes the configuration options for the link preview feature.

## Overview

The link preview feature can be configured through environment variables to control its behavior, performance, and security settings.

## Backend Configuration

Backend configuration is managed through environment variables in `.env` or through the hosting environment.

### Environment Variables

Add these to your `.env` file or set them in your deployment environment:

```bash
# Enable/disable link preview feature
LINK_PREVIEW_ENABLED=true

# Timeout for fetching link metadata (seconds)
LINK_PREVIEW_TIMEOUT=5

# Cache TTL for link metadata (seconds, default: 1 hour)
LINK_PREVIEW_CACHE_TTL=3600

# Maximum response size for link fetching (bytes, default: 5MB)
LINK_PREVIEW_MAX_SIZE=5000000

# Comma-separated list of domains to exclude from link preview
# Example: LINK_PREVIEW_EXCLUDED_DOMAINS=example.com,test.com
LINK_PREVIEW_EXCLUDED_DOMAINS=
```

### Configuration Details

#### LINK_PREVIEW_ENABLED
- **Type**: Boolean
- **Default**: `true`
- **Description**: Master switch to enable/disable the link preview feature. When disabled, the API endpoint returns empty responses.

#### LINK_PREVIEW_TIMEOUT
- **Type**: Integer (seconds)
- **Default**: `5`
- **Description**: Maximum time to wait when fetching HTML from a URL. Requests exceeding this timeout will fail gracefully.

#### LINK_PREVIEW_CACHE_TTL
- **Type**: Integer (seconds)
- **Default**: `3600` (1 hour)
- **Description**: How long to cache metadata for each URL. Cached entries are reused within this time period to improve performance.

#### LINK_PREVIEW_MAX_SIZE
- **Type**: Integer (bytes)
- **Default**: `5000000` (5MB)
- **Description**: Maximum size of HTML response to fetch. Larger responses are rejected to prevent memory issues.

#### LINK_PREVIEW_EXCLUDED_DOMAINS
- **Type**: String (comma-separated)
- **Default**: Empty string
- **Description**: List of domain names to exclude from link preview generation. Both exact matches and subdomains are excluded.
- **Example**: `example.com,test.org` will exclude:
  - `https://example.com`
  - `https://www.example.com`
  - `https://api.example.com`
  - `https://test.org`
  - `https://subdomain.test.org`

### Accessing Configuration in Code

Configuration is accessed through the `Settings` class:

```python
from backend.app.core.config import get_settings

settings = get_settings()

# Check if feature is enabled
if settings.link_preview_enabled:
    # Fetch metadata
    pass

# Get excluded domains as a list
excluded = settings.get_link_preview_excluded_domains()
```

## Frontend Configuration

Frontend configuration is managed through Vite environment variables in `frontend/.env`.

### Environment Variables

Add this to your `frontend/.env` file:

```bash
# Enable/disable link preview feature in the frontend
# When disabled, URLs will be displayed as plain text without preview cards
# Default: true
VITE_LINK_PREVIEW_ENABLED=true
```

### Configuration Details

#### VITE_LINK_PREVIEW_ENABLED
- **Type**: String (`'true'` or `'false'`)
- **Default**: `'true'`
- **Description**: Controls whether link preview cards are rendered in the frontend. When set to `'false'`, URLs in messages appear as plain text.

**Note**: All Vite environment variables must be prefixed with `VITE_` to be exposed to the client.

### Accessing Configuration in Code

The environment variable is accessed using `import.meta.env`:

```typescript
// Check if link preview is enabled
if (import.meta.env.VITE_LINK_PREVIEW_ENABLED !== 'false') {
  // Render link preview cards
}
```

## Default Exclusions

The following URL patterns are always excluded from link preview, regardless of configuration:

- **Localhost**: `localhost`, `127.0.0.1`, `::1`, `*.localhost`
- **Private IPs**: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
- **Link-local**: `169.254.0.0/16`
- **Data URIs**: `data:*`
- **Blob URLs**: `blob:*`
- **Venue links**: URLs already handled by the venue links feature

## Configuration Examples

### Development Environment

```bash
# .env (backend)
LINK_PREVIEW_ENABLED=true
LINK_PREVIEW_TIMEOUT=5
LINK_PREVIEW_CACHE_TTL=3600
LINK_PREVIEW_MAX_SIZE=5000000
LINK_PREVIEW_EXCLUDED_DOMAINS=

# frontend/.env
VITE_LINK_PREVIEW_ENABLED=true
```

### Production Environment

```bash
# .env (backend)
LINK_PREVIEW_ENABLED=true
LINK_PREVIEW_TIMEOUT=3
LINK_PREVIEW_CACHE_TTL=7200
LINK_PREVIEW_MAX_SIZE=3000000
LINK_PREVIEW_EXCLUDED_DOMAINS=internal.company.com,staging.company.com

# frontend/.env
VITE_LINK_PREVIEW_ENABLED=true
```

### Disabled Feature

```bash
# .env (backend)
LINK_PREVIEW_ENABLED=false

# frontend/.env
VITE_LINK_PREVIEW_ENABLED=false
```

## Performance Tuning

### Reducing Latency
- Decrease `LINK_PREVIEW_TIMEOUT` (e.g., `3` seconds)
- Increase `LINK_PREVIEW_CACHE_TTL` for frequently accessed URLs

### Reducing Memory Usage
- Decrease `LINK_PREVIEW_MAX_SIZE` (e.g., `2000000` for 2MB)
- Decrease cache TTL to expire entries sooner

### Blocking Problematic Sites
- Add slow or unreliable domains to `LINK_PREVIEW_EXCLUDED_DOMAINS`

## Security Considerations

1. **Excluded Domains**: Use `LINK_PREVIEW_EXCLUDED_DOMAINS` to prevent fetching from internal or sensitive domains
2. **Timeout**: Keep `LINK_PREVIEW_TIMEOUT` low to prevent slow sites from blocking the service
3. **Max Size**: Limit `LINK_PREVIEW_MAX_SIZE` to prevent memory exhaustion attacks
4. **Feature Toggle**: Use `LINK_PREVIEW_ENABLED` to quickly disable the feature if issues arise

## Troubleshooting

### Link previews not appearing
1. Check `LINK_PREVIEW_ENABLED=true` in backend `.env`
2. Check `VITE_LINK_PREVIEW_ENABLED=true` in frontend `.env`
3. Restart both backend and frontend servers after changing `.env` files

### Specific domains not showing previews
1. Check if domain is in `LINK_PREVIEW_EXCLUDED_DOMAINS`
2. Check if domain is in default exclusion list (localhost, private IPs, etc.)
3. Check backend logs for fetch errors

### Slow performance
1. Reduce `LINK_PREVIEW_TIMEOUT` to fail faster
2. Increase `LINK_PREVIEW_CACHE_TTL` to cache longer
3. Add slow domains to `LINK_PREVIEW_EXCLUDED_DOMAINS`

## Requirements Validation

This configuration implementation satisfies **Requirement 6.5**:
- ✅ Feature can be enabled/disabled via configuration
- ✅ Timeout, cache TTL, and max size are configurable
- ✅ Excluded domains can be specified via configuration
- ✅ Configuration is documented with examples
- ✅ Both backend and frontend support configuration
