"""Link preview API endpoints for fetching URL metadata.

This module provides REST API endpoints for link preview functionality:
- POST /api/link-preview: Fetch metadata for one or more URLs

Requirements: 3.1, 3.4
"""

import logging
from fastapi import APIRouter, HTTPException
from urllib.parse import urlparse

from app.models.link_preview import (
    LinkPreviewRequest,
    LinkPreviewResponse,
    LinkMetadata,
)
from app.services.metadata_fetcher import MetadataFetcher, FetchError
from app.services.html_parser import HTMLParser
from app.services.metadata_cache import MetadataCache
from app.core.config import get_settings


# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["link-preview"])

# Get settings
settings = get_settings()

# Initialize services (singleton instances) using configuration
# Requirements: 6.5
_metadata_fetcher = MetadataFetcher(
    timeout=settings.link_preview_timeout,
    max_size=settings.link_preview_max_size,
    excluded_domains=settings.get_link_preview_excluded_domains()
)
_html_parser = HTMLParser()
_metadata_cache = MetadataCache(
    ttl=settings.link_preview_cache_ttl,
    max_size=1000
)


def _extract_domain(url: str) -> str:
    """Extract domain name from URL.
    
    Args:
        url: The URL to extract domain from
        
    Returns:
        Domain name (e.g., "example.com")
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split('/')[0]
        return domain if domain else url
    except Exception:
        return url


@router.post(
    "/link-preview",
    response_model=LinkPreviewResponse,
    status_code=200,
    responses={
        400: {"description": "Invalid request"},
        500: {"description": "Internal server error"},
    },
)
async def get_link_preview(request: LinkPreviewRequest) -> LinkPreviewResponse:
    """
    Fetch metadata for one or more URLs.
    
    This endpoint accepts a list of URLs and returns metadata for each,
    including title, description, image, favicon, and domain. If metadata
    fetch fails for a URL, an error field is included in the response.
    
    The endpoint is designed to handle multiple URLs in a single request
    to optimize performance when messages contain multiple links.
    
    The flow for each URL is:
    1. Check cache for existing metadata
    2. If not cached, fetch HTML from URL
    3. Parse HTML to extract metadata
    4. Cache the result
    5. Return metadata (or error if any step fails)
    
    Args:
        request: LinkPreviewRequest with urls list and session_id
        
    Returns:
        LinkPreviewResponse: Metadata for each URL
        
    Raises:
        HTTPException: 400 for invalid requests, 500 for server errors
        
    Requirements:
    - 1.2: Fetch metadata for detected URLs
    - 1.4: Handle errors gracefully with minimal preview
    - 3.1: Frontend sends request to backend API with list of URLs
    - 3.4: Backend returns structured response with metadata
    
    Example:
        Request:
        {
            "urls": ["https://example.com", "https://github.com"],
            "session_id": "abc-123"
        }
        
        Response:
        {
            "previews": [
                {
                    "url": "https://example.com",
                    "title": "Example Domain",
                    "description": "Example description",
                    "image": null,
                    "favicon": "https://example.com/favicon.ico",
                    "domain": "example.com",
                    "error": null
                },
                ...
            ]
        }
    """
    try:
        # Check if link preview feature is enabled (Requirement 6.5)
        if not settings.link_preview_enabled:
            logger.info("Link preview feature is disabled")
            # Return empty previews when feature is disabled
            return LinkPreviewResponse(previews=[])
        
        logger.info(
            f"Fetching link previews for {len(request.urls)} URLs "
            f"(session: {request.session_id})"
        )
        
        previews: list[LinkMetadata] = []
        
        # Process each URL
        for url in request.urls:
            try:
                # Step 1: Check cache first
                cached_metadata = await _metadata_cache.get(url)
                if cached_metadata:
                    logger.debug(f"Cache hit for URL: {url}")
                    previews.append(cached_metadata)
                    continue
                
                logger.debug(f"Cache miss for URL: {url}, fetching...")
                
                # Step 2: Fetch HTML from URL
                try:
                    html = await _metadata_fetcher.fetch_html(url)
                except FetchError as fetch_error:
                    # Fetch failed - return minimal metadata with error
                    logger.warning(f"Fetch failed for {url}: {fetch_error}")
                    domain = _extract_domain(url)
                    metadata = LinkMetadata(
                        url=url,
                        domain=domain,
                        error=str(fetch_error)
                    )
                    # Cache the error result (with shorter TTL handled by cache)
                    await _metadata_cache.set(url, metadata)
                    previews.append(metadata)
                    continue
                
                # Step 3: Parse HTML to extract metadata
                try:
                    metadata = _html_parser.parse_metadata(html, url)
                    logger.debug(
                        f"Successfully parsed metadata for {url}: "
                        f"title={metadata.title}, domain={metadata.domain}"
                    )
                except Exception as parse_error:
                    # Parse failed - return minimal metadata with error
                    logger.warning(f"Parse failed for {url}: {parse_error}")
                    domain = _extract_domain(url)
                    metadata = LinkMetadata(
                        url=url,
                        domain=domain,
                        error=f"Failed to parse metadata: {str(parse_error)}"
                    )
                
                # Step 4: Cache the result
                await _metadata_cache.set(url, metadata)
                
                # Step 5: Add to response
                previews.append(metadata)
                
            except Exception as url_error:
                # Unexpected error processing this URL - include error in response
                logger.warning(
                    f"Unexpected error processing URL {url}: "
                    f"{type(url_error).__name__}: {url_error}"
                )
                previews.append(
                    LinkMetadata(
                        url=url,
                        domain=_extract_domain(url),
                        error=f"Failed to process URL: {str(url_error)}"
                    )
                )
        
        logger.info(
            f"Successfully processed {len(previews)} URLs "
            f"for session {request.session_id}"
        )
        
        return LinkPreviewResponse(previews=previews)
        
    except Exception as e:
        logger.error(
            f"Failed to fetch link previews: {type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch link previews: {str(e)}"
        )
