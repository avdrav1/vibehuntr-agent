"""Link preview API endpoints for fetching URL metadata.

This module provides REST API endpoints for link preview functionality:
- POST /api/link-preview: Fetch metadata for one or more URLs

Requirements: 3.1, 3.4
"""

import logging
from fastapi import APIRouter, HTTPException
from urllib.parse import urlparse

from backend.app.models.link_preview import (
    LinkPreviewRequest,
    LinkPreviewResponse,
    LinkMetadata,
)


# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["link-preview"])


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
    
    Args:
        request: LinkPreviewRequest with urls list and session_id
        
    Returns:
        LinkPreviewResponse: Metadata for each URL
        
    Raises:
        HTTPException: 400 for invalid requests, 500 for server errors
        
    Requirements:
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
        logger.info(
            f"Fetching link previews for {len(request.urls)} URLs "
            f"(session: {request.session_id})"
        )
        
        previews: list[LinkMetadata] = []
        
        # Process each URL
        for url in request.urls:
            try:
                # Extract domain for minimal fallback
                domain = _extract_domain(url)
                
                # TODO: Implement actual metadata fetching in future tasks
                # For now, return minimal metadata with domain only
                # This will be replaced with actual fetching logic in task 2
                metadata = LinkMetadata(
                    url=url,
                    domain=domain,
                    error="Metadata fetching not yet implemented"
                )
                
                previews.append(metadata)
                logger.debug(f"Processed URL: {url} -> domain: {domain}")
                
            except Exception as url_error:
                # If processing a single URL fails, include error in response
                logger.warning(
                    f"Failed to process URL {url}: {type(url_error).__name__}: {url_error}"
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
