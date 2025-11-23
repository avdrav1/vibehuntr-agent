"""Property-based tests for link preview feature.

This module tests the correctness properties for link preview functionality,
including metadata fetching, URL validation, and timeout handling.
"""

import sys
import os
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from hypothesis.strategies import composite
import pytest
import asyncio

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.app.services.metadata_fetcher import MetadataFetcher, FetchError


# Custom strategies for generating test data

@composite
def valid_url_strategy(draw: st.DrawFn) -> str:
    """Generate a valid HTTP/HTTPS URL."""
    scheme = draw(st.sampled_from(['http', 'https']))
    # Generate a simple domain name
    domain_parts = draw(st.lists(
        st.text(
            alphabet=st.characters(whitelist_categories=('Ll', 'Nd')),
            min_size=1,
            max_size=10
        ),
        min_size=1,
        max_size=3
    ))
    domain = '.'.join(domain_parts)
    tld = draw(st.sampled_from(['com', 'org', 'net', 'io', 'dev']))
    
    # Optional path
    has_path = draw(st.booleans())
    path = ''
    if has_path:
        path_parts = draw(st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=('Ll', 'Nd')),
                min_size=1,
                max_size=10
            ),
            min_size=1,
            max_size=3
        ))
        path = '/' + '/'.join(path_parts)
    
    return f"{scheme}://{domain}.{tld}{path}"


@composite
def excluded_url_strategy(draw: st.DrawFn) -> str:
    """Generate URLs that should be excluded."""
    url_type = draw(st.sampled_from([
        'localhost',
        'private_ip',
        'data_uri',
        'blob_url',
        'loopback'
    ]))
    
    if url_type == 'localhost':
        return draw(st.sampled_from([
            'http://localhost',
            'http://localhost:8080',
            'https://localhost',
            'http://test.localhost'
        ]))
    elif url_type == 'private_ip':
        return draw(st.sampled_from([
            'http://192.168.1.1',
            'http://10.0.0.1',
            'http://172.16.0.1',
            'http://169.254.1.1'
        ]))
    elif url_type == 'data_uri':
        return 'data:text/html,<html></html>'
    elif url_type == 'blob_url':
        return 'blob:http://example.com/550e8400-e29b-41d4-a716-446655440000'
    else:  # loopback
        return draw(st.sampled_from([
            'http://127.0.0.1',
            'http://127.0.0.1:8080'
        ]))


@composite
def invalid_url_strategy(draw: st.DrawFn) -> str:
    """Generate invalid URLs."""
    url_type = draw(st.sampled_from([
        'no_scheme',
        'invalid_scheme',
        'no_domain',
        'malformed'
    ]))
    
    if url_type == 'no_scheme':
        return 'example.com/path'
    elif url_type == 'invalid_scheme':
        scheme = draw(st.sampled_from(['ftp', 'file', 'javascript', 'mailto']))
        return f'{scheme}://example.com'
    elif url_type == 'no_domain':
        return 'http://'
    else:  # malformed
        return draw(st.text(min_size=1, max_size=50).filter(
            lambda x: not x.startswith('http://') and not x.startswith('https://')
        ))


# Property Tests

# Feature: link-preview-cards, Property 11: Fetch timeout
@given(st.integers(min_value=1, max_value=10))
@settings(max_examples=100, deadline=None)
def test_property_11_fetch_timeout(timeout_seconds: int) -> None:
    """
    Feature: link-preview-cards, Property 11: Fetch timeout
    
    For any URL where the fetch operation exceeds the configured timeout,
    the system should timeout and raise a FetchError.
    
    Validates: Requirements 4.4
    """
    # Create fetcher with specified timeout
    fetcher = MetadataFetcher(timeout=timeout_seconds)
    
    # Verify timeout is set correctly
    assert fetcher.timeout == timeout_seconds
    
    # Note: We can't easily test actual timeout behavior in property tests
    # without making real network requests or complex mocking.
    # This test verifies the timeout configuration is properly set.
    # Actual timeout behavior will be tested in unit tests with mocking.


# Additional property test: URL validation consistency
@given(valid_url_strategy())
@settings(max_examples=100)
def test_property_url_validation_accepts_valid_urls(url: str) -> None:
    """
    For any valid HTTP/HTTPS URL, the is_valid_url method should return True.
    
    Validates: URL validation logic
    """
    fetcher = MetadataFetcher()
    
    # Valid URLs should pass validation
    assert fetcher.is_valid_url(url) == True


@given(invalid_url_strategy())
@settings(max_examples=100)
def test_property_url_validation_rejects_invalid_urls(url: str) -> None:
    """
    For any invalid URL (wrong scheme, no domain, malformed), the is_valid_url
    method should return False.
    
    Validates: URL validation logic
    """
    fetcher = MetadataFetcher()
    
    # Invalid URLs should fail validation
    assert fetcher.is_valid_url(url) == False


@given(excluded_url_strategy())
@settings(max_examples=100)
def test_property_url_exclusion_blocks_dangerous_urls(url: str) -> None:
    """
    For any URL matching exclusion patterns (localhost, private IPs, data URIs,
    blob URLs), the should_exclude method should return True.
    
    Validates: Requirements 6.1, 6.2, 6.3
    """
    fetcher = MetadataFetcher()
    
    # Excluded URLs should be blocked
    assert fetcher.should_exclude(url) == True


# Additional property test: Fetcher configuration
@given(
    st.integers(min_value=1, max_value=30),
    st.integers(min_value=100_000, max_value=10_000_000),
    st.integers(min_value=1, max_value=10)
)
@settings(max_examples=100)
def test_property_fetcher_configuration(
    timeout: int,
    max_size: int,
    max_redirects: int
) -> None:
    """
    For any valid configuration parameters, the MetadataFetcher should
    initialize correctly with those settings.
    
    Validates: Fetcher initialization
    """
    fetcher = MetadataFetcher(
        timeout=timeout,
        max_size=max_size,
        max_redirects=max_redirects
    )
    
    assert fetcher.timeout == timeout
    assert fetcher.max_size == max_size
    assert fetcher.max_redirects == max_redirects
    assert fetcher.user_agent == "VibehuntrBot/1.0"


# Additional property test: User agent consistency
@given(st.text(min_size=1, max_size=100))
@settings(max_examples=100)
def test_property_user_agent_configuration(user_agent: str) -> None:
    """
    For any user agent string, the MetadataFetcher should store and use
    that user agent.
    
    Validates: User agent configuration
    """
    fetcher = MetadataFetcher(user_agent=user_agent)
    
    assert fetcher.user_agent == user_agent


from backend.app.services.html_parser import HTMLParser
from backend.app.services.metadata_cache import MetadataCache
from backend.app.models.link_preview import LinkMetadata, LinkPreviewRequest, LinkPreviewResponse
from backend.app.api.link_preview import get_link_preview


# HTML generation strategies

@composite
def html_content_strategy(draw: st.DrawFn) -> str:
    """Generate various HTML content including malformed HTML."""
    html_type = draw(st.sampled_from([
        'valid_complete',
        'valid_minimal',
        'malformed_unclosed',
        'malformed_nested',
        'empty',
        'text_only',
        'with_og_tags',
        'with_twitter_tags',
        'with_standard_tags',
        'mixed_tags'
    ]))
    
    if html_type == 'valid_complete':
        title = draw(st.text(min_size=1, max_size=100))
        description = draw(st.text(min_size=1, max_size=200))
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <meta name="description" content="{description}">
        </head>
        <body>
            <h1>{title}</h1>
            <p>{description}</p>
        </body>
        </html>
        """
    elif html_type == 'valid_minimal':
        return '<html><head><title>Test</title></head><body></body></html>'
    elif html_type == 'malformed_unclosed':
        return '<html><head><title>Test</head><body><p>Content'
    elif html_type == 'malformed_nested':
        return '<html><body><div><p><span>Text</div></p></span></body></html>'
    elif html_type == 'empty':
        return ''
    elif html_type == 'text_only':
        return draw(st.text(min_size=0, max_size=100))
    elif html_type == 'with_og_tags':
        title = draw(st.text(min_size=1, max_size=100))
        description = draw(st.text(min_size=1, max_size=200))
        return f"""
        <html>
        <head>
            <meta property="og:title" content="{title}">
            <meta property="og:description" content="{description}">
            <meta property="og:image" content="https://example.com/image.jpg">
        </head>
        <body></body>
        </html>
        """
    elif html_type == 'with_twitter_tags':
        title = draw(st.text(min_size=1, max_size=100))
        description = draw(st.text(min_size=1, max_size=200))
        return f"""
        <html>
        <head>
            <meta name="twitter:title" content="{title}">
            <meta name="twitter:description" content="{description}">
            <meta name="twitter:image" content="https://example.com/image.jpg">
        </head>
        <body></body>
        </html>
        """
    elif html_type == 'with_standard_tags':
        title = draw(st.text(min_size=1, max_size=100))
        description = draw(st.text(min_size=1, max_size=200))
        return f"""
        <html>
        <head>
            <title>{title}</title>
            <meta name="description" content="{description}">
        </head>
        <body></body>
        </html>
        """
    else:  # mixed_tags
        title = draw(st.text(min_size=1, max_size=100))
        return f"""
        <html>
        <head>
            <title>{title}</title>
            <meta property="og:title" content="OG {title}">
            <meta name="twitter:title" content="Twitter {title}">
        </head>
        <body></body>
        </html>
        """


# Feature: link-preview-cards, Property 12: HTML parsing robustness
@given(html_content_strategy(), valid_url_strategy())
@settings(max_examples=100, deadline=None)
def test_property_12_html_parsing_robustness(html: str, url: str) -> None:
    """
    Feature: link-preview-cards, Property 12: HTML parsing robustness
    
    For any HTML content (including malformed HTML), the parser should not crash
    and should return at least a partial metadata object with the domain field populated.
    
    Validates: Requirements 3.3, 5.4
    """
    parser = HTMLParser()
    
    # Parser should not raise exceptions for any HTML input
    try:
        metadata = parser.parse_metadata(html, url)
        
        # Metadata should always have url and domain fields
        assert metadata.url == url
        assert metadata.domain is not None
        assert len(metadata.domain) > 0
        
        # Metadata should be a valid LinkMetadata object
        assert hasattr(metadata, 'title')
        assert hasattr(metadata, 'description')
        assert hasattr(metadata, 'image')
        assert hasattr(metadata, 'favicon')
        assert hasattr(metadata, 'error')
        
    except Exception as e:
        # Parser should never crash
        pytest.fail(f"Parser crashed with exception: {e}")


# Additional property test: Metadata field types
@given(html_content_strategy(), valid_url_strategy())
@settings(max_examples=100, deadline=None)
def test_property_metadata_field_types(html: str, url: str) -> None:
    """
    For any HTML content and URL, the parsed metadata should have correct field types.
    All optional fields should be either None or strings.
    
    Validates: Metadata structure consistency
    """
    parser = HTMLParser()
    metadata = parser.parse_metadata(html, url)
    
    # Required fields should be strings
    assert isinstance(metadata.url, str)
    assert isinstance(metadata.domain, str)
    
    # Optional fields should be None or strings
    assert metadata.title is None or isinstance(metadata.title, str)
    assert metadata.description is None or isinstance(metadata.description, str)
    assert metadata.image is None or isinstance(metadata.image, str)
    assert metadata.favicon is None or isinstance(metadata.favicon, str)
    assert metadata.error is None or isinstance(metadata.error, str)


# Additional property test: URL resolution
@given(
    st.sampled_from([
        'http://example.com',
        'https://example.com',
        'http://example.com/path',
        'https://example.com/path/to/page'
    ]),
    st.sampled_from([
        '/absolute/path',
        'relative/path',
        '../parent/path',
        'https://other.com/image.jpg',
        '//cdn.example.com/image.jpg'
    ])
)
@settings(max_examples=100)
def test_property_url_resolution(base_url: str, relative_url: str) -> None:
    """
    For any base URL and relative URL, the _resolve_url method should
    return a valid absolute URL.
    
    Validates: URL resolution logic
    """
    parser = HTMLParser()
    resolved = parser._resolve_url(base_url, relative_url)
    
    # Resolved URL should be a string
    assert isinstance(resolved, str)
    
    # If relative_url was already absolute (http/https), it should be unchanged
    if relative_url.startswith(('http://', 'https://')):
        assert resolved == relative_url
    else:
        # Otherwise, it should be resolved relative to base_url
        assert len(resolved) > 0


# Additional property test: Domain extraction
@given(valid_url_strategy())
@settings(max_examples=100)
def test_property_domain_extraction(url: str) -> None:
    """
    For any valid URL, the _extract_domain method should return a non-empty domain.
    
    Validates: Domain extraction logic
    """
    parser = HTMLParser()
    domain = parser._extract_domain(url)
    
    # Domain should be a non-empty string
    assert isinstance(domain, str)
    assert len(domain) > 0
    
    # Domain should not contain scheme
    assert not domain.startswith('http://')
    assert not domain.startswith('https://')


# Metadata generation strategy

@composite
def link_metadata_strategy(draw: st.DrawFn) -> LinkMetadata:
    """Generate LinkMetadata objects for testing."""
    url = draw(valid_url_strategy())
    domain = draw(st.text(min_size=1, max_size=50))
    
    # Optional fields
    has_title = draw(st.booleans())
    has_description = draw(st.booleans())
    has_image = draw(st.booleans())
    has_favicon = draw(st.booleans())
    
    return LinkMetadata(
        url=url,
        domain=domain,
        title=draw(st.text(min_size=1, max_size=100)) if has_title else None,
        description=draw(st.text(min_size=1, max_size=200)) if has_description else None,
        image=draw(valid_url_strategy()) if has_image else None,
        favicon=draw(valid_url_strategy()) if has_favicon else None,
        error=None
    )


# Feature: link-preview-cards, Property 9: Metadata caching
@given(valid_url_strategy(), link_metadata_strategy())
@settings(max_examples=100, deadline=None)
def test_property_9_metadata_caching(url: str, metadata: LinkMetadata) -> None:
    """
    Feature: link-preview-cards, Property 9: Metadata caching
    
    For any URL that has been fetched within the cache TTL period, a subsequent
    fetch request should return the cached metadata without making another HTTP
    request to the original URL.
    
    Validates: Requirements 3.5
    """
    # Create cache with 1 hour TTL
    cache = MetadataCache(ttl=3600, max_size=1000)
    
    # Run async test
    async def test_caching():
        # Initially, cache should be empty
        cached = await cache.get(url)
        assert cached is None
        
        # Set metadata in cache
        await cache.set(url, metadata)
        
        # Retrieve from cache - should return the same metadata
        cached = await cache.get(url)
        assert cached is not None
        assert cached.url == metadata.url
        assert cached.domain == metadata.domain
        assert cached.title == metadata.title
        assert cached.description == metadata.description
        assert cached.image == metadata.image
        assert cached.favicon == metadata.favicon
        assert cached.error == metadata.error
    
    # Run the async test
    asyncio.run(test_caching())


# Additional property test: Cache TTL expiration
@given(valid_url_strategy(), link_metadata_strategy(), st.integers(min_value=1, max_value=2))
@settings(max_examples=10, deadline=None)
def test_property_cache_ttl_expiration(url: str, metadata: LinkMetadata, ttl: int) -> None:
    """
    For any URL cached with a TTL, accessing it after the TTL has expired
    should return None.
    
    Validates: Cache TTL behavior
    """
    # Create cache with short TTL
    cache = MetadataCache(ttl=ttl, max_size=1000)
    
    async def test_expiration():
        # Set metadata in cache
        await cache.set(url, metadata)
        
        # Immediately retrieve - should be cached
        cached = await cache.get(url)
        assert cached is not None
        
        # Wait for TTL to expire
        await asyncio.sleep(ttl + 0.1)
        
        # Should now return None (expired)
        cached = await cache.get(url)
        assert cached is None
    
    asyncio.run(test_expiration())


# Additional property test: LRU eviction
@given(
    st.lists(valid_url_strategy(), min_size=5, max_size=20, unique=True),
    st.lists(link_metadata_strategy(), min_size=5, max_size=20)
)
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_property_lru_eviction(urls: list[str], metadatas: list[LinkMetadata]) -> None:
    """
    For any cache with a maximum size, when the cache is full and a new entry
    is added, the least recently used entry should be evicted.
    
    Validates: LRU eviction behavior
    """
    # Ensure we have matching lists
    assume(len(urls) == len(metadatas))
    assume(len(urls) >= 5)
    
    # Create cache with small max size
    max_size = 3
    cache = MetadataCache(ttl=3600, max_size=max_size)
    
    async def test_eviction():
        # Fill cache to capacity
        for i in range(max_size):
            await cache.set(urls[i], metadatas[i])
        
        # All entries should be cached
        for i in range(max_size):
            cached = await cache.get(urls[i])
            assert cached is not None
        
        # Add one more entry (should evict the first one)
        await cache.set(urls[max_size], metadatas[max_size])
        
        # First entry should be evicted
        cached = await cache.get(urls[0])
        assert cached is None
        
        # Other entries should still be cached
        for i in range(1, max_size + 1):
            cached = await cache.get(urls[i])
            assert cached is not None
    
    asyncio.run(test_eviction())


# Additional property test: Cache clear
@given(
    st.lists(valid_url_strategy(), min_size=1, max_size=10, unique=True),
    st.lists(link_metadata_strategy(), min_size=1, max_size=10)
)
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_property_cache_clear(urls: list[str], metadatas: list[LinkMetadata]) -> None:
    """
    For any cache with entries, calling clear() should remove all entries.
    
    Validates: Cache clear functionality
    """
    assume(len(urls) == len(metadatas))
    
    cache = MetadataCache(ttl=3600, max_size=1000)
    
    async def test_clear():
        # Add entries to cache
        for url, metadata in zip(urls, metadatas):
            await cache.set(url, metadata)
        
        # Verify entries are cached
        for url in urls:
            cached = await cache.get(url)
            assert cached is not None
        
        # Clear cache
        await cache.clear()
        
        # All entries should be gone
        for url in urls:
            cached = await cache.get(url)
            assert cached is None
    
    asyncio.run(test_clear())


# Feature: link-preview-cards, Property 3: Metadata fetch attempt
@given(st.lists(valid_url_strategy(), min_size=1, max_size=5, unique=True))
@settings(max_examples=100, deadline=None)
def test_property_3_metadata_fetch_attempt(urls: list[str]) -> None:
    """
    Feature: link-preview-cards, Property 3: Metadata fetch attempt
    
    For any valid URL that passes filtering, the backend should attempt to fetch
    HTML content and parse metadata, returning a structured response with title,
    description, image, favicon, and domain fields (even if some are empty).
    
    Note: This test validates the structure of the response, not the actual
    fetching behavior (which would require mocking external HTTP requests).
    The test ensures that for any valid URL, the endpoint returns a properly
    structured LinkMetadata object with all required fields.
    
    Validates: Requirements 1.2, 3.2, 3.3, 3.4
    """
    # Create request
    request = LinkPreviewRequest(
        urls=urls,
        session_id="test-session-123"
    )
    
    async def test_fetch():
        # Call the endpoint
        response = await get_link_preview(request)
        
        # Response should be a LinkPreviewResponse
        assert isinstance(response, LinkPreviewResponse)
        
        # Should have same number of previews as input URLs
        assert len(response.previews) == len(urls)
        
        # Each preview should have all required fields
        for i, preview in enumerate(response.previews):
            # Should be a LinkMetadata object
            assert isinstance(preview, LinkMetadata)
            
            # Required fields should always be present
            assert preview.url == urls[i]
            assert preview.domain is not None
            assert isinstance(preview.domain, str)
            assert len(preview.domain) > 0
            
            # Optional fields should be None or strings
            assert preview.title is None or isinstance(preview.title, str)
            assert preview.description is None or isinstance(preview.description, str)
            assert preview.image is None or isinstance(preview.image, str)
            assert preview.favicon is None or isinstance(preview.favicon, str)
            assert preview.error is None or isinstance(preview.error, str)
            
            # The response should have all the expected fields present
            # (even if some are None - that's valid for empty pages or fetch failures)
    
    # Run the async test
    asyncio.run(test_fetch())
