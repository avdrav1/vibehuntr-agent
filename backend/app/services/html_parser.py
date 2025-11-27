"""
HTML parser service for link preview feature.

This service extracts metadata from HTML content by parsing
Open Graph tags, Twitter Card tags, and standard HTML meta tags.

Requirements: 3.3
"""

from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.models.link_preview import LinkMetadata


class HTMLParser:
    """
    Service to parse HTML and extract metadata.
    
    Extracts metadata from Open Graph tags, Twitter Card tags,
    and standard HTML meta tags with proper fallback handling.
    """
    
    def parse_metadata(self, html: str, url: str) -> LinkMetadata:
        """
        Parse HTML and extract metadata.
        
        Args:
            html: HTML content as string
            url: Original URL (for resolving relative URLs and extracting domain)
            
        Returns:
            LinkMetadata with extracted information
        """
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract domain from URL
        domain = self._extract_domain(url)
        
        # Extract metadata from various sources
        og_data = self._extract_open_graph(soup)
        twitter_data = self._extract_twitter_card(soup)
        standard_data = self._extract_standard_meta(soup)
        
        # Merge metadata with priority: Open Graph > Twitter Card > Standard
        title = og_data.get('title') or twitter_data.get('title') or standard_data.get('title')
        description = og_data.get('description') or twitter_data.get('description') or standard_data.get('description')
        image = og_data.get('image') or twitter_data.get('image')
        
        # Resolve relative URLs to absolute
        if image:
            image = self._resolve_url(url, image)
        
        # Extract favicon
        favicon = self._extract_favicon(soup, url)
        
        return LinkMetadata(
            url=url,
            title=title,
            description=description,
            image=image,
            favicon=favicon,
            domain=domain
        )
    
    def _extract_open_graph(self, soup: BeautifulSoup) -> dict[str, Optional[str]]:
        """
        Extract Open Graph meta tags.
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            Dictionary with og:title, og:description, og:image
        """
        og_data: dict[str, Optional[str]] = {}
        
        # Find all meta tags with property attribute
        og_tags = soup.find_all('meta', property=True)
        
        for tag in og_tags:
            prop = tag.get('property', '').lower()
            content = tag.get('content', '').strip()
            
            if prop == 'og:title' and content:
                og_data['title'] = content
            elif prop == 'og:description' and content:
                og_data['description'] = content
            elif prop == 'og:image' and content:
                og_data['image'] = content
        
        return og_data
    
    def _extract_twitter_card(self, soup: BeautifulSoup) -> dict[str, Optional[str]]:
        """
        Extract Twitter Card meta tags.
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            Dictionary with twitter:title, twitter:description, twitter:image
        """
        twitter_data: dict[str, Optional[str]] = {}
        
        # Find all meta tags with name attribute
        twitter_tags = soup.find_all('meta', attrs={'name': True})
        
        for tag in twitter_tags:
            name = tag.get('name', '').lower()
            content = tag.get('content', '').strip()
            
            if name == 'twitter:title' and content:
                twitter_data['title'] = content
            elif name == 'twitter:description' and content:
                twitter_data['description'] = content
            elif name == 'twitter:image' and content:
                twitter_data['image'] = content
        
        return twitter_data
    
    def _extract_standard_meta(self, soup: BeautifulSoup) -> dict[str, Optional[str]]:
        """
        Extract standard HTML meta tags and title.
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            Dictionary with title and description
        """
        standard_data: dict[str, Optional[str]] = {}
        
        # Extract title from <title> tag
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            standard_data['title'] = title_tag.string.strip()
        
        # Extract description from meta description tag
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag:
            content = desc_tag.get('content', '').strip()
            if content:
                standard_data['description'] = content
        
        return standard_data
    
    def _extract_favicon(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """
        Extract favicon URL from link tags or default location.
        
        Args:
            soup: BeautifulSoup parsed HTML
            base_url: Base URL for resolving relative paths
            
        Returns:
            Absolute favicon URL or None
        """
        # Look for favicon in link tags
        favicon_rels = ['icon', 'shortcut icon', 'apple-touch-icon']
        
        for rel in favicon_rels:
            link_tag = soup.find('link', rel=rel)
            if link_tag:
                href = link_tag.get('href', '').strip()
                if href:
                    return self._resolve_url(base_url, href)
        
        # Fallback to /favicon.ico
        parsed = urlparse(base_url)
        return f"{parsed.scheme}://{parsed.netloc}/favicon.ico"
    
    def _resolve_url(self, base_url: str, relative_url: str) -> str:
        """
        Resolve relative URLs to absolute.
        
        Args:
            base_url: Base URL for resolution
            relative_url: Potentially relative URL
            
        Returns:
            Absolute URL
        """
        # If already absolute, return as-is
        if relative_url.startswith(('http://', 'https://')):
            return relative_url
        
        # Use urljoin to resolve relative URLs
        return urljoin(base_url, relative_url)
    
    def _extract_domain(self, url: str) -> str:
        """
        Extract domain name from URL.
        
        Args:
            url: Full URL
            
        Returns:
            Domain name (netloc)
        """
        parsed = urlparse(url)
        return parsed.netloc or url
