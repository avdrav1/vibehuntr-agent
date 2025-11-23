"""
Metadata fetcher service for link preview feature.

This service fetches HTML content from URLs with proper timeout,
error handling, and security validations.
"""

import asyncio
import ipaddress
import re
from typing import Optional
from urllib.parse import urlparse

import httpx


class FetchError(Exception):
    """Exception raised when fetching URL fails."""
    pass


class MetadataFetcher:
    """
    Service to fetch HTML content from URLs.
    
    Handles timeouts, redirects, connection errors, and implements
    security validations to exclude dangerous URLs.
    """
    
    def __init__(
        self,
        timeout: int = 5,
        max_size: int = 5_000_000,
        max_redirects: int = 3,
        user_agent: str = "VibehuntrBot/1.0",
        excluded_domains: Optional[list[str]] = None
    ):
        """
        Initialize metadata fetcher.
        
        Args:
            timeout: Request timeout in seconds (default: 5)
            max_size: Maximum response size in bytes (default: 5MB)
            max_redirects: Maximum number of redirects to follow (default: 3)
            user_agent: User agent string for requests
            excluded_domains: List of domain names to exclude (default: None)
        """
        self.timeout = timeout
        self.max_size = max_size
        self.max_redirects = max_redirects
        self.user_agent = user_agent
        self.excluded_domains = excluded_domains or []
        
        # Compile regex patterns for efficiency
        self._data_uri_pattern = re.compile(r'^data:', re.IGNORECASE)
        self._blob_pattern = re.compile(r'^blob:', re.IGNORECASE)
    
    async def fetch_html(self, url: str) -> str:
        """
        Fetch HTML content from URL.
        
        Args:
            url: The URL to fetch
            
        Returns:
            HTML content as string
            
        Raises:
            FetchError: If fetch fails, times out, or URL is invalid/excluded
        """
        # Validate URL
        if not self.is_valid_url(url):
            raise FetchError(f"Invalid URL format: {url}")
        
        # Check exclusions
        if self.should_exclude(url):
            raise FetchError(f"URL is excluded from fetching: {url}")
        
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                max_redirects=self.max_redirects,
                headers={"User-Agent": self.user_agent}
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # Check response size
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > self.max_size:
                    raise FetchError(f"Response too large: {content_length} bytes")
                
                # Get content and check size
                content = response.text
                if len(content.encode('utf-8')) > self.max_size:
                    raise FetchError(f"Response content exceeds maximum size")
                
                return content
                
        except httpx.TimeoutException as e:
            raise FetchError(f"Request timed out after {self.timeout} seconds") from e
        except httpx.HTTPStatusError as e:
            raise FetchError(f"HTTP error {e.response.status_code}: {e.response.reason_phrase}") from e
        except httpx.ConnectError as e:
            raise FetchError(f"Connection error: {str(e)}") from e
        except httpx.TooManyRedirects as e:
            raise FetchError(f"Too many redirects") from e
        except Exception as e:
            raise FetchError(f"Unexpected error fetching URL: {str(e)}") from e
    
    def is_valid_url(self, url: str) -> bool:
        """
        Validate URL format and scheme.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid HTTP/HTTPS, False otherwise
        """
        try:
            parsed = urlparse(url)
            # Must have HTTP or HTTPS scheme
            if parsed.scheme not in ('http', 'https'):
                return False
            # Must have a netloc (domain)
            if not parsed.netloc:
                return False
            return True
        except Exception:
            return False
    
    def should_exclude(self, url: str) -> bool:
        """
        Check if URL should be excluded from fetching.
        
        Excludes:
        - localhost and loopback addresses
        - Private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
        - Link-local addresses (169.254.0.0/16)
        - Data URIs and blob URLs
        - Domains in excluded_domains list (Requirement 6.5)
        
        Args:
            url: URL to check
            
        Returns:
            True if URL should be excluded, False otherwise
        """
        # Check for data URIs and blob URLs
        if self._data_uri_pattern.match(url) or self._blob_pattern.match(url):
            return True
        
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            
            if not hostname:
                return True
            
            # Check if domain is in excluded list (Requirement 6.5)
            if self.excluded_domains:
                hostname_lower = hostname.lower()
                for excluded_domain in self.excluded_domains:
                    excluded_lower = excluded_domain.lower()
                    # Check exact match or subdomain match
                    if hostname_lower == excluded_lower or hostname_lower.endswith(f'.{excluded_lower}'):
                        return True
            
            # Check for localhost
            if hostname.lower() in ('localhost', '127.0.0.1', '::1'):
                return True
            
            # Try to parse as IP address
            try:
                ip = ipaddress.ip_address(hostname)
                
                # Check if private, loopback, or link-local
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    return True
                    
            except ValueError:
                # Not an IP address, check if it resolves to localhost
                if hostname.lower().endswith('.localhost'):
                    return True
            
            return False
            
        except Exception:
            # If we can't parse it, exclude it to be safe
            return True
