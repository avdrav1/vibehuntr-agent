"""Integration tests for link preview API endpoints.

This module tests the link preview API endpoint with various scenarios
including successful fetches, error handling, caching, and multiple URLs.

Requirements: 1.2, 1.4, 3.1, 3.5
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio

from backend.app.main import app
from backend.app.models.link_preview import LinkMetadata


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_metadata_fetcher():
    """Mock the metadata fetcher service."""
    with patch('backend.app.api.link_preview._metadata_fetcher') as mock:
        yield mock


@pytest.fixture
def mock_html_parser():
    """Mock the HTML parser service."""
    with patch('backend.app.api.link_preview._html_parser') as mock:
        yield mock


@pytest.fixture
def mock_metadata_cache():
    """Mock the metadata cache service."""
    with patch('backend.app.api.link_preview._metadata_cache') as mock:
        # Make cache methods async
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock()
        yield mock


def test_link_preview_successful_fetch(
    client: TestClient,
    mock_metadata_fetcher,
    mock_html_parser,
    mock_metadata_cache
):
    """
    Test successful metadata fetch for a valid URL.
    
    Requirements: 1.2, 3.1, 3.4
    """
    # Setup mocks
    mock_metadata_cache.get = AsyncMock(return_value=None)  # Cache miss
    
    # Mock successful HTML fetch
    mock_html = "<html><head><title>Test Page</title></head></html>"
    mock_metadata_fetcher.fetch_html = AsyncMock(return_value=mock_html)
    
    # Mock successful parsing
    mock_metadata = LinkMetadata(
        url="https://example.com",
        title="Test Page",
        description="A test page",
        image="https://example.com/image.jpg",
        favicon="https://example.com/favicon.ico",
        domain="example.com"
    )
    mock_html_parser.parse_metadata = MagicMock(return_value=mock_metadata)
    
    # Make request
    response = client.post(
        "/api/link-preview",
        json={
            "urls": ["https://example.com"],
            "session_id": "test-session-123"
        }
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    assert "previews" in data
    assert len(data["previews"]) == 1
    
    preview = data["previews"][0]
    assert preview["url"] == "https://example.com"
    assert preview["title"] == "Test Page"
    assert preview["description"] == "A test page"
    assert preview["image"] == "https://example.com/image.jpg"
    assert preview["favicon"] == "https://example.com/favicon.ico"
    assert preview["domain"] == "example.com"
    assert preview["error"] is None


def test_link_preview_404_error(
    client: TestClient,
    mock_metadata_fetcher,
    mock_html_parser,
    mock_metadata_cache
):
    """
    Test error handling for 404 response.
    
    Requirements: 1.4, 5.1
    """
    from backend.app.services.metadata_fetcher import FetchError
    
    # Setup mocks
    mock_metadata_cache.get = AsyncMock(return_value=None)  # Cache miss
    
    # Mock 404 error
    mock_metadata_fetcher.fetch_html = AsyncMock(
        side_effect=FetchError("HTTP error 404: Not Found")
    )
    
    # Make request
    response = client.post(
        "/api/link-preview",
        json={
            "urls": ["https://example.com/notfound"],
            "session_id": "test-session-123"
        }
    )
    
    # Verify response
    assert response.status_code == 200  # Endpoint should not fail
    data = response.json()
    
    assert "previews" in data
    assert len(data["previews"]) == 1
    
    preview = data["previews"][0]
    assert preview["url"] == "https://example.com/notfound"
    assert preview["domain"] == "example.com"
    assert preview["error"] is not None
    assert "404" in preview["error"]


def test_link_preview_timeout_error(
    client: TestClient,
    mock_metadata_fetcher,
    mock_html_parser,
    mock_metadata_cache
):
    """
    Test error handling for timeout.
    
    Requirements: 1.4, 4.4, 5.2
    """
    from backend.app.services.metadata_fetcher import FetchError
    
    # Setup mocks
    mock_metadata_cache.get = AsyncMock(return_value=None)  # Cache miss
    
    # Mock timeout error
    mock_metadata_fetcher.fetch_html = AsyncMock(
        side_effect=FetchError("Request timed out after 5 seconds")
    )
    
    # Make request
    response = client.post(
        "/api/link-preview",
        json={
            "urls": ["https://slow-site.com"],
            "session_id": "test-session-123"
        }
    )
    
    # Verify response
    assert response.status_code == 200  # Endpoint should not fail
    data = response.json()
    
    assert "previews" in data
    assert len(data["previews"]) == 1
    
    preview = data["previews"][0]
    assert preview["url"] == "https://slow-site.com"
    assert preview["domain"] == "slow-site.com"
    assert preview["error"] is not None
    assert "timed out" in preview["error"].lower()


def test_link_preview_multiple_urls(
    client: TestClient,
    mock_metadata_fetcher,
    mock_html_parser,
    mock_metadata_cache
):
    """
    Test multiple URLs in single request.
    
    Requirements: 1.2, 1.4, 3.1
    """
    # Setup mocks
    mock_metadata_cache.get = AsyncMock(return_value=None)  # Cache miss
    
    # Mock successful HTML fetch for both URLs
    async def mock_fetch(url):
        if "example.com" in url:
            return "<html><head><title>Example</title></head></html>"
        elif "github.com" in url:
            return "<html><head><title>GitHub</title></head></html>"
        return "<html></html>"
    
    mock_metadata_fetcher.fetch_html = AsyncMock(side_effect=mock_fetch)
    
    # Mock parsing for both URLs
    def mock_parse(html, url):
        if "example.com" in url:
            return LinkMetadata(
                url=url,
                title="Example",
                description="Example site",
                domain="example.com"
            )
        elif "github.com" in url:
            return LinkMetadata(
                url=url,
                title="GitHub",
                description="GitHub site",
                domain="github.com"
            )
        return LinkMetadata(url=url, domain="unknown.com")
    
    mock_html_parser.parse_metadata = MagicMock(side_effect=mock_parse)
    
    # Make request with multiple URLs
    response = client.post(
        "/api/link-preview",
        json={
            "urls": [
                "https://example.com",
                "https://github.com"
            ],
            "session_id": "test-session-123"
        }
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    assert "previews" in data
    assert len(data["previews"]) == 2
    
    # Check first preview
    preview1 = data["previews"][0]
    assert preview1["url"] == "https://example.com"
    assert preview1["title"] == "Example"
    assert preview1["domain"] == "example.com"
    
    # Check second preview
    preview2 = data["previews"][1]
    assert preview2["url"] == "https://github.com"
    assert preview2["title"] == "GitHub"
    assert preview2["domain"] == "github.com"


def test_link_preview_cache_hit(
    client: TestClient,
    mock_metadata_fetcher,
    mock_html_parser,
    mock_metadata_cache
):
    """
    Test cache hit scenario.
    
    Requirements: 3.5
    """
    # Setup cached metadata
    cached_metadata = LinkMetadata(
        url="https://example.com",
        title="Cached Title",
        description="Cached description",
        domain="example.com"
    )
    
    # Mock cache hit
    mock_metadata_cache.get = AsyncMock(return_value=cached_metadata)
    
    # Make request
    response = client.post(
        "/api/link-preview",
        json={
            "urls": ["https://example.com"],
            "session_id": "test-session-123"
        }
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    assert "previews" in data
    assert len(data["previews"]) == 1
    
    preview = data["previews"][0]
    assert preview["url"] == "https://example.com"
    assert preview["title"] == "Cached Title"
    assert preview["description"] == "Cached description"
    assert preview["domain"] == "example.com"
    
    # Verify fetcher was NOT called (cache hit)
    mock_metadata_fetcher.fetch_html.assert_not_called()
    mock_html_parser.parse_metadata.assert_not_called()


def test_link_preview_invalid_request():
    """
    Test invalid request handling (empty URLs list).
    
    Requirements: 3.1
    """
    client = TestClient(app)
    
    # Make request with empty URLs list
    response = client.post(
        "/api/link-preview",
        json={
            "urls": [],
            "session_id": "test-session-123"
        }
    )
    
    # Should return 422 validation error
    assert response.status_code == 422


def test_link_preview_mixed_success_and_failure(
    client: TestClient,
    mock_metadata_fetcher,
    mock_html_parser,
    mock_metadata_cache
):
    """
    Test handling of mixed successful and failed fetches.
    
    Requirements: 1.2, 1.4
    """
    from backend.app.services.metadata_fetcher import FetchError
    
    # Setup mocks
    mock_metadata_cache.get = AsyncMock(return_value=None)  # Cache miss
    
    # Mock fetch: first succeeds, second fails
    async def mock_fetch(url):
        if "example.com" in url:
            return "<html><head><title>Example</title></head></html>"
        elif "error.com" in url:
            raise FetchError("Connection error")
        return "<html></html>"
    
    mock_metadata_fetcher.fetch_html = AsyncMock(side_effect=mock_fetch)
    
    # Mock parsing for successful URL
    def mock_parse(html, url):
        return LinkMetadata(
            url=url,
            title="Example",
            description="Example site",
            domain="example.com"
        )
    
    mock_html_parser.parse_metadata = MagicMock(side_effect=mock_parse)
    
    # Make request with mixed URLs
    response = client.post(
        "/api/link-preview",
        json={
            "urls": [
                "https://example.com",
                "https://error.com"
            ],
            "session_id": "test-session-123"
        }
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    assert "previews" in data
    assert len(data["previews"]) == 2
    
    # First should succeed
    preview1 = data["previews"][0]
    assert preview1["url"] == "https://example.com"
    assert preview1["title"] == "Example"
    assert preview1["error"] is None
    
    # Second should have error
    preview2 = data["previews"][1]
    assert preview2["url"] == "https://error.com"
    assert preview2["domain"] == "error.com"
    assert preview2["error"] is not None
    assert "Connection error" in preview2["error"]
