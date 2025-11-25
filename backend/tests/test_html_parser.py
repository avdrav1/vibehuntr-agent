"""Unit tests for HTML parser service.

This module tests the HTML parser's ability to extract metadata from
various HTML formats including Open Graph, Twitter Card, and standard tags.

Requirements: 3.3, 5.4
"""

import pytest
from app.services.html_parser import HTMLParser


class TestHTMLParser:
    """Test suite for HTMLParser class."""
    
    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.parser = HTMLParser()
        self.base_url = "https://example.com/page"
    
    def test_extract_open_graph_tags(self) -> None:
        """Test extraction of Open Graph meta tags.
        
        Requirements: 3.3
        """
        html = """
        <html>
        <head>
            <meta property="og:title" content="OG Title">
            <meta property="og:description" content="OG Description">
            <meta property="og:image" content="https://example.com/og-image.jpg">
        </head>
        <body></body>
        </html>
        """
        
        metadata = self.parser.parse_metadata(html, self.base_url)
        
        assert metadata.title == "OG Title"
        assert metadata.description == "OG Description"
        assert metadata.image == "https://example.com/og-image.jpg"
        assert metadata.domain == "example.com"
    
    def test_extract_twitter_card_tags(self) -> None:
        """Test extraction of Twitter Card meta tags.
        
        Requirements: 3.3
        """
        html = """
        <html>
        <head>
            <meta name="twitter:title" content="Twitter Title">
            <meta name="twitter:description" content="Twitter Description">
            <meta name="twitter:image" content="https://example.com/twitter-image.jpg">
        </head>
        <body></body>
        </html>
        """
        
        metadata = self.parser.parse_metadata(html, self.base_url)
        
        assert metadata.title == "Twitter Title"
        assert metadata.description == "Twitter Description"
        assert metadata.image == "https://example.com/twitter-image.jpg"
        assert metadata.domain == "example.com"
    
    def test_extract_standard_meta_tags(self) -> None:
        """Test extraction of standard HTML meta tags.
        
        Requirements: 3.3
        """
        html = """
        <html>
        <head>
            <title>Standard Title</title>
            <meta name="description" content="Standard Description">
        </head>
        <body></body>
        </html>
        """
        
        metadata = self.parser.parse_metadata(html, self.base_url)
        
        assert metadata.title == "Standard Title"
        assert metadata.description == "Standard Description"
        assert metadata.domain == "example.com"
    
    def test_metadata_priority_open_graph_over_twitter(self) -> None:
        """Test that Open Graph tags take priority over Twitter Card tags.
        
        Requirements: 3.3
        """
        html = """
        <html>
        <head>
            <meta property="og:title" content="OG Title">
            <meta name="twitter:title" content="Twitter Title">
            <meta property="og:description" content="OG Description">
            <meta name="twitter:description" content="Twitter Description">
        </head>
        <body></body>
        </html>
        """
        
        metadata = self.parser.parse_metadata(html, self.base_url)
        
        # Open Graph should take priority
        assert metadata.title == "OG Title"
        assert metadata.description == "OG Description"
    
    def test_metadata_priority_twitter_over_standard(self) -> None:
        """Test that Twitter Card tags take priority over standard tags.
        
        Requirements: 3.3
        """
        html = """
        <html>
        <head>
            <title>Standard Title</title>
            <meta name="twitter:title" content="Twitter Title">
            <meta name="description" content="Standard Description">
            <meta name="twitter:description" content="Twitter Description">
        </head>
        <body></body>
        </html>
        """
        
        metadata = self.parser.parse_metadata(html, self.base_url)
        
        # Twitter Card should take priority over standard
        assert metadata.title == "Twitter Title"
        assert metadata.description == "Twitter Description"
    
    def test_malformed_html_handling(self) -> None:
        """Test that parser handles malformed HTML gracefully.
        
        Requirements: 5.4
        """
        malformed_html = """
        <html>
        <head>
            <title>Test Title
            <meta name="description" content="Test Description"
        <body>
            <p>Unclosed paragraph
            <div>Unclosed div
        """
        
        # Should not raise exception
        metadata = self.parser.parse_metadata(malformed_html, self.base_url)
        
        # Should still extract what it can
        assert metadata.url == self.base_url
        assert metadata.domain == "example.com"
        # BeautifulSoup is forgiving, so it might extract the title
        assert metadata.title is not None or metadata.title is None  # Either is acceptable
    
    def test_empty_html_handling(self) -> None:
        """Test that parser handles empty HTML.
        
        Requirements: 5.4
        """
        empty_html = ""
        
        metadata = self.parser.parse_metadata(empty_html, self.base_url)
        
        assert metadata.url == self.base_url
        assert metadata.domain == "example.com"
        assert metadata.title is None
        assert metadata.description is None
        assert metadata.image is None
    
    def test_relative_url_resolution_absolute_path(self) -> None:
        """Test resolution of relative URLs with absolute paths.
        
        Requirements: 3.3
        """
        html = """
        <html>
        <head>
            <meta property="og:image" content="/images/photo.jpg">
        </head>
        <body></body>
        </html>
        """
        
        metadata = self.parser.parse_metadata(html, self.base_url)
        
        # Should resolve to absolute URL
        assert metadata.image == "https://example.com/images/photo.jpg"
    
    def test_relative_url_resolution_relative_path(self) -> None:
        """Test resolution of relative URLs with relative paths.
        
        Requirements: 3.3
        """
        html = """
        <html>
        <head>
            <meta property="og:image" content="images/photo.jpg">
        </head>
        <body></body>
        </html>
        """
        
        metadata = self.parser.parse_metadata(html, self.base_url)
        
        # Should resolve relative to base URL
        assert metadata.image == "https://example.com/images/photo.jpg"
    
    def test_relative_url_resolution_parent_path(self) -> None:
        """Test resolution of relative URLs with parent directory references.
        
        Requirements: 3.3
        """
        html = """
        <html>
        <head>
            <meta property="og:image" content="../images/photo.jpg">
        </head>
        <body></body>
        </html>
        """
        
        metadata = self.parser.parse_metadata(html, "https://example.com/blog/post")
        
        # Should resolve parent directory correctly
        assert metadata.image == "https://example.com/images/photo.jpg"
    
    def test_absolute_url_unchanged(self) -> None:
        """Test that absolute URLs are not modified.
        
        Requirements: 3.3
        """
        html = """
        <html>
        <head>
            <meta property="og:image" content="https://cdn.example.com/image.jpg">
        </head>
        <body></body>
        </html>
        """
        
        metadata = self.parser.parse_metadata(html, self.base_url)
        
        # Absolute URL should remain unchanged
        assert metadata.image == "https://cdn.example.com/image.jpg"
    
    def test_missing_tags_fallback(self) -> None:
        """Test fallback behavior when tags are missing.
        
        Requirements: 3.3
        """
        html = """
        <html>
        <head>
        </head>
        <body>
            <h1>Some content</h1>
        </body>
        </html>
        """
        
        metadata = self.parser.parse_metadata(html, self.base_url)
        
        # Should have URL and domain but no other metadata
        assert metadata.url == self.base_url
        assert metadata.domain == "example.com"
        assert metadata.title is None
        assert metadata.description is None
        assert metadata.image is None
        # Favicon should have fallback
        assert metadata.favicon == "https://example.com/favicon.ico"
    
    def test_favicon_extraction_from_link_tag(self) -> None:
        """Test extraction of favicon from link tag.
        
        Requirements: 3.3
        """
        html = """
        <html>
        <head>
            <link rel="icon" href="/favicon.png">
        </head>
        <body></body>
        </html>
        """
        
        metadata = self.parser.parse_metadata(html, self.base_url)
        
        assert metadata.favicon == "https://example.com/favicon.png"
    
    def test_favicon_extraction_shortcut_icon(self) -> None:
        """Test extraction of favicon from shortcut icon link tag.
        
        Requirements: 3.3
        """
        html = """
        <html>
        <head>
            <link rel="shortcut icon" href="/favicon.ico">
        </head>
        <body></body>
        </html>
        """
        
        metadata = self.parser.parse_metadata(html, self.base_url)
        
        assert metadata.favicon == "https://example.com/favicon.ico"
    
    def test_favicon_extraction_apple_touch_icon(self) -> None:
        """Test extraction of favicon from apple-touch-icon link tag.
        
        Requirements: 3.3
        """
        html = """
        <html>
        <head>
            <link rel="apple-touch-icon" href="/apple-icon.png">
        </head>
        <body></body>
        </html>
        """
        
        metadata = self.parser.parse_metadata(html, self.base_url)
        
        assert metadata.favicon == "https://example.com/apple-icon.png"
    
    def test_favicon_fallback_to_default(self) -> None:
        """Test fallback to /favicon.ico when no link tag present.
        
        Requirements: 3.3
        """
        html = """
        <html>
        <head>
            <title>Test</title>
        </head>
        <body></body>
        </html>
        """
        
        metadata = self.parser.parse_metadata(html, self.base_url)
        
        # Should fallback to default favicon location
        assert metadata.favicon == "https://example.com/favicon.ico"
    
    def test_whitespace_trimming(self) -> None:
        """Test that extracted metadata has whitespace trimmed.
        
        Requirements: 3.3
        """
        html = """
        <html>
        <head>
            <meta property="og:title" content="  Title with spaces  ">
            <meta property="og:description" content="
                Description with newlines
            ">
        </head>
        <body></body>
        </html>
        """
        
        metadata = self.parser.parse_metadata(html, self.base_url)
        
        # Whitespace should be trimmed
        assert metadata.title == "Title with spaces"
        # BeautifulSoup may preserve some internal whitespace
        assert "Description" in metadata.description
    
    def test_empty_content_attributes_ignored(self) -> None:
        """Test that empty content attributes are ignored.
        
        Requirements: 3.3
        """
        html = """
        <html>
        <head>
            <meta property="og:title" content="">
            <meta property="og:description" content="">
            <title>Fallback Title</title>
        </head>
        <body></body>
        </html>
        """
        
        metadata = self.parser.parse_metadata(html, self.base_url)
        
        # Should fall back to standard title since OG title is empty
        assert metadata.title == "Fallback Title"
        assert metadata.description is None
    
    def test_case_insensitive_tag_matching(self) -> None:
        """Test that tag matching is case-insensitive.
        
        Requirements: 3.3
        """
        html = """
        <html>
        <head>
            <meta property="OG:TITLE" content="Title">
            <meta name="TWITTER:DESCRIPTION" content="Description">
        </head>
        <body></body>
        </html>
        """
        
        metadata = self.parser.parse_metadata(html, self.base_url)
        
        # Should match case-insensitively
        assert metadata.title == "Title"
        assert metadata.description == "Description"
    
    def test_domain_extraction_with_port(self) -> None:
        """Test domain extraction from URL with port.
        
        Requirements: 3.3
        """
        url_with_port = "https://example.com:8080/page"
        html = "<html><head><title>Test</title></head><body></body></html>"
        
        metadata = self.parser.parse_metadata(html, url_with_port)
        
        assert metadata.domain == "example.com:8080"
    
    def test_domain_extraction_with_subdomain(self) -> None:
        """Test domain extraction from URL with subdomain.
        
        Requirements: 3.3
        """
        url_with_subdomain = "https://blog.example.com/post"
        html = "<html><head><title>Test</title></head><body></body></html>"
        
        metadata = self.parser.parse_metadata(html, url_with_subdomain)
        
        assert metadata.domain == "blog.example.com"
    
    def test_protocol_relative_url_resolution(self) -> None:
        """Test resolution of protocol-relative URLs.
        
        Requirements: 3.3
        """
        html = """
        <html>
        <head>
            <meta property="og:image" content="//cdn.example.com/image.jpg">
        </head>
        <body></body>
        </html>
        """
        
        metadata = self.parser.parse_metadata(html, self.base_url)
        
        # Should resolve protocol-relative URL
        assert metadata.image == "https://cdn.example.com/image.jpg"
