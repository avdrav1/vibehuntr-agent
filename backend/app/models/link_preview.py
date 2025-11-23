"""Pydantic models for link preview API.

This module defines the data schemas used for link preview functionality,
including request/response models and metadata structures.

Requirements: 3.4
"""

from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional


class LinkPreviewRequest(BaseModel):
    """Request model for link preview endpoint.
    
    Attributes:
        urls: List of URLs to fetch metadata for
        session_id: Session identifier for potential caching per session
    """
    urls: list[str] = Field(..., min_length=1, description="List of URLs to preview")
    session_id: str = Field(..., description="Session identifier")
    
    @field_validator('urls')
    @classmethod
    def validate_urls(cls, v: list[str]) -> list[str]:
        """Validate that URLs are non-empty strings.
        
        Args:
            v: List of URL strings
            
        Returns:
            Validated list of URLs
            
        Raises:
            ValueError: If any URL is empty
        """
        if not v:
            raise ValueError("URLs list cannot be empty")
        for url in v:
            if not url or not url.strip():
                raise ValueError("URLs cannot be empty strings")
        return v


class LinkMetadata(BaseModel):
    """Metadata extracted from a URL.
    
    Attributes:
        url: The original URL
        title: Page title (from Open Graph, Twitter Card, or HTML title)
        description: Page description
        image: Preview image URL
        favicon: Favicon URL
        domain: Domain name extracted from URL
        error: Error message if metadata fetch failed
    """
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    favicon: Optional[str] = None
    domain: str
    error: Optional[str] = None


class LinkPreviewResponse(BaseModel):
    """Response model for link preview endpoint.
    
    Attributes:
        previews: List of metadata objects for each requested URL
    """
    previews: list[LinkMetadata]
