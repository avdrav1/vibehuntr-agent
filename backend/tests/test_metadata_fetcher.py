"""Unit tests for metadata fetcher service.

This module tests the MetadataFetcher service, including HTML fetching,
URL validation, exclusion logic, timeout handling, and error handling.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx

# Add parent directory to path for imports
import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from backend.app.services.metadata_fetcher import MetadataFetcher, FetchError


@pytest.fixture
def fetcher():
    """Create a MetadataFetcher instance for testing."""
    return MetadataFetcher(timeout=5, max_size=5_000_000)


class TestMetadataFetcherInitialization:
    """Tests for MetadataFetcher initialization."""
    
    def test_default_initialization(self):
        """Test fetcher initializes with default values."""
        fetcher = MetadataFetcher()
        
        assert fetcher.timeout == 5
        assert fetcher.max_size == 5_000_000
        assert fetcher.max_redirects == 3
        assert fetcher.user_agent == "VibehuntrBot/1.0"
    
    def test_custom_initialization(self):
        """Test fetcher initializes with custom values."""
        fetcher = MetadataFetcher(
            timeout=10,
            max_size=1_000_000,
            max_redirects=5,
            user_agent="CustomBot/2.0"
        )
        
        assert fetcher.timeout == 10
        assert fetcher.max_size == 1_000_000
        assert fetcher.max_redirects == 5
        assert fetcher.user_agent == "CustomBot/2.0"


class TestURLValidation:
    """Tests for URL validation logic."""
    
    def test_valid_http_url(self, fetcher):
        """Test that valid HTTP URLs pass validation."""
        assert fetcher.is_valid_url("http://example.com") == True
        assert fetcher.is_valid_url("http://example.com/path") == True
        assert fetcher.is_valid_url("http://example.com/path?query=value") == True
    
    def test_valid_https_url(self, fetcher):
        """Test that valid HTTPS URLs pass validation."""
        assert fetcher.is_valid_url("https://example.com") == True
        assert fetcher.is_valid_url("https://example.com/path") == True
        assert fetcher.is_valid_url("https://subdomain.example.com") == True
    
    def test_invalid_scheme(self, fetcher):
        """Test that URLs with invalid schemes fail validation."""
        assert fetcher.is_valid_url("ftp://example.com") == False
        assert fetcher.is_valid_url("file:///path/to/file") == False
        assert fetcher.is_valid_url("javascript:alert('xss')") == False
        assert fetcher.is_valid_url("mailto:test@example.com") == False
    
    def test_no_scheme(self, fetcher):
        """Test that URLs without scheme fail validation."""
        assert fetcher.is_valid_url("example.com") == False
        assert fetcher.is_valid_url("www.example.com") == False
    
    def test_no_domain(self, fetcher):
        """Test that URLs without domain fail validation."""
        assert fetcher.is_valid_url("http://") == False
        assert fetcher.is_valid_url("https://") == False
    
    def test_malformed_url(self, fetcher):
        """Test that malformed URLs fail validation."""
        assert fetcher.is_valid_url("not a url") == False
        assert fetcher.is_valid_url("") == False
        assert fetcher.is_valid_url("http:///path") == False


class TestURLExclusion:
    """Tests for URL exclusion logic."""
    
    def test_localhost_exclusion(self, fetcher):
        """Test that localhost URLs are excluded."""
        assert fetcher.should_exclude("http://localhost") == True
        assert fetcher.should_exclude("http://localhost:8080") == True
        assert fetcher.should_exclude("https://localhost") == True
        assert fetcher.should_exclude("http://test.localhost") == True
    
    def test_loopback_ip_exclusion(self, fetcher):
        """Test that loopback IPs are excluded."""
        assert fetcher.should_exclude("http://127.0.0.1") == True
        assert fetcher.should_exclude("http://127.0.0.1:8080") == True
        assert fetcher.should_exclude("http://[::1]") == True
    
    def test_private_ip_exclusion(self, fetcher):
        """Test that private IP ranges are excluded."""
        # 10.0.0.0/8
        assert fetcher.should_exclude("http://10.0.0.1") == True
        assert fetcher.should_exclude("http://10.255.255.255") == True
        
        # 172.16.0.0/12
        assert fetcher.should_exclude("http://172.16.0.1") == True
        assert fetcher.should_exclude("http://172.31.255.255") == True
        
        # 192.168.0.0/16
        assert fetcher.should_exclude("http://192.168.0.1") == True
        assert fetcher.should_exclude("http://192.168.255.255") == True
    
    def test_link_local_exclusion(self, fetcher):
        """Test that link-local addresses are excluded."""
        assert fetcher.should_exclude("http://169.254.1.1") == True
        assert fetcher.should_exclude("http://169.254.255.255") == True
    
    def test_data_uri_exclusion(self, fetcher):
        """Test that data URIs are excluded."""
        assert fetcher.should_exclude("data:text/html,<html></html>") == True
        assert fetcher.should_exclude("DATA:text/plain,hello") == True
    
    def test_blob_url_exclusion(self, fetcher):
        """Test that blob URLs are excluded."""
        assert fetcher.should_exclude("blob:http://example.com/550e8400") == True
        assert fetcher.should_exclude("BLOB:https://example.com/abc123") == True
    
    def test_public_url_not_excluded(self, fetcher):
        """Test that public URLs are not excluded."""
        assert fetcher.should_exclude("http://example.com") == False
        assert fetcher.should_exclude("https://google.com") == False
        assert fetcher.should_exclude("http://8.8.8.8") == False


class TestFetchHTML:
    """Tests for HTML fetching functionality."""
    
    @pytest.mark.asyncio
    async def test_successful_fetch(self, fetcher):
        """Test successful HTML fetch."""
        mock_response = Mock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.headers = {"content-length": "100"}
        mock_response.raise_for_status = Mock()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            html = await fetcher.fetch_html("http://example.com")
            
            assert html == "<html><body>Test</body></html>"
            mock_client.get.assert_called_once_with("http://example.com")
    
    @pytest.mark.asyncio
    async def test_fetch_invalid_url(self, fetcher):
        """Test that fetching invalid URL raises FetchError."""
        with pytest.raises(FetchError, match="Invalid URL format"):
            await fetcher.fetch_html("not a url")
    
    @pytest.mark.asyncio
    async def test_fetch_excluded_url(self, fetcher):
        """Test that fetching excluded URL raises FetchError."""
        with pytest.raises(FetchError, match="URL is excluded"):
            await fetcher.fetch_html("http://localhost")
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, fetcher):
        """Test that timeout raises FetchError."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client_class.return_value = mock_client
            
            with pytest.raises(FetchError, match="timed out"):
                await fetcher.fetch_html("http://example.com")
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self, fetcher):
        """Test that connection errors raise FetchError."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(
                side_effect=httpx.ConnectError("Connection failed")
            )
            mock_client_class.return_value = mock_client
            
            with pytest.raises(FetchError, match="Connection error"):
                await fetcher.fetch_html("http://example.com")
    
    @pytest.mark.asyncio
    async def test_http_error_handling(self, fetcher):
        """Test that HTTP errors raise FetchError."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.reason_phrase = "Not Found"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "404 Not Found",
                    request=Mock(),
                    response=mock_response
                )
            )
            mock_client_class.return_value = mock_client
            
            with pytest.raises(FetchError, match="HTTP error 404"):
                await fetcher.fetch_html("http://example.com")
    
    @pytest.mark.asyncio
    async def test_too_many_redirects_handling(self, fetcher):
        """Test that too many redirects raises FetchError."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(
                side_effect=httpx.TooManyRedirects("Too many redirects")
            )
            mock_client_class.return_value = mock_client
            
            with pytest.raises(FetchError, match="Too many redirects"):
                await fetcher.fetch_html("http://example.com")
    
    @pytest.mark.asyncio
    async def test_response_size_limit_header(self, fetcher):
        """Test that response size limit is enforced via header."""
        mock_response = Mock()
        mock_response.headers = {"content-length": "10000000"}  # 10MB
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            with pytest.raises(FetchError, match="Response too large"):
                await fetcher.fetch_html("http://example.com")
    
    @pytest.mark.asyncio
    async def test_response_size_limit_content(self, fetcher):
        """Test that response size limit is enforced on content."""
        # Create content larger than max_size
        large_content = "x" * (fetcher.max_size + 1000)
        mock_response = Mock()
        mock_response.text = large_content
        mock_response.headers = {}  # No content-length header
        mock_response.raise_for_status = Mock()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            with pytest.raises(FetchError, match="exceeds maximum size"):
                await fetcher.fetch_html("http://example.com")
    
    @pytest.mark.asyncio
    async def test_user_agent_header(self, fetcher):
        """Test that user agent is set in request headers."""
        mock_response = Mock()
        mock_response.text = "<html></html>"
        mock_response.headers = {}
        mock_response.raise_for_status = Mock()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            await fetcher.fetch_html("http://example.com")
            
            # Verify AsyncClient was created with correct headers
            call_kwargs = mock_client_class.call_args[1]
            assert call_kwargs['headers']['User-Agent'] == "VibehuntrBot/1.0"
    
    @pytest.mark.asyncio
    async def test_redirect_configuration(self, fetcher):
        """Test that redirect settings are configured correctly."""
        mock_response = Mock()
        mock_response.text = "<html></html>"
        mock_response.headers = {}
        mock_response.raise_for_status = Mock()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            await fetcher.fetch_html("http://example.com")
            
            # Verify AsyncClient was created with correct redirect settings
            call_kwargs = mock_client_class.call_args[1]
            assert call_kwargs['follow_redirects'] == True
            assert call_kwargs['max_redirects'] == 3
