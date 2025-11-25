"""Unit tests for deployment script health check functions.

This module tests the health check functionality that verifies successful
deployment to Firebase Hosting.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
import subprocess


# Mock health check functions that mirror the deployment script behavior

def check_frontend_health(frontend_url: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Check if the frontend is accessible and properly configured.
    
    Args:
        frontend_url: The Firebase Hosting URL to check
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary with health check results:
        - success: bool
        - status_code: int or None
        - cache_headers: dict or None
        - error: str or None
    """
    import requests
    
    try:
        response = requests.get(frontend_url, timeout=timeout, allow_redirects=True)
        
        # Check if we got a successful response
        success = response.status_code == 200
        
        # Extract cache headers
        cache_headers = {
            'cache-control': response.headers.get('Cache-Control', ''),
            'content-type': response.headers.get('Content-Type', ''),
        }
        
        return {
            'success': success,
            'status_code': response.status_code,
            'cache_headers': cache_headers,
            'error': None if success else f"HTTP {response.status_code}"
        }
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'status_code': None,
            'cache_headers': None,
            'error': 'Request timeout'
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'status_code': None,
            'cache_headers': None,
            'error': 'Connection failed'
        }
    except Exception as e:
        return {
            'success': False,
            'status_code': None,
            'cache_headers': None,
            'error': str(e)
        }


def validate_cache_headers(cache_control: str, is_html: bool = True) -> bool:
    """
    Validate that cache headers are correctly configured.
    
    Args:
        cache_control: The Cache-Control header value
        is_html: Whether this is an HTML file (vs static asset)
        
    Returns:
        True if cache headers are correct
    """
    if not cache_control:
        return False
    
    cache_lower = cache_control.lower()
    
    if is_html:
        # HTML should have short-term caching
        # Expected: public, max-age=3600, must-revalidate
        return (
            'public' in cache_lower and
            'max-age' in cache_lower and
            ('3600' in cache_lower or 'must-revalidate' in cache_lower)
        )
    else:
        # Static assets should have long-term caching
        # Expected: public, max-age=31536000, immutable
        return (
            'public' in cache_lower and
            'max-age=31536000' in cache_lower and
            'immutable' in cache_lower
        )


def format_health_check_output(result: Dict[str, Any], frontend_url: str) -> str:
    """
    Format health check results for display.
    
    Args:
        result: Health check result dictionary
        frontend_url: The URL that was checked
        
    Returns:
        Formatted output string
    """
    if result['success']:
        output = f"✓ Frontend is accessible at {frontend_url}\n"
        output += f"  Status: {result['status_code']}\n"
        
        if result['cache_headers']:
            cache_control = result['cache_headers'].get('cache-control', 'Not set')
            output += f"  Cache-Control: {cache_control}\n"
        
        return output
    else:
        output = f"✗ Frontend health check failed\n"
        output += f"  URL: {frontend_url}\n"
        output += f"  Error: {result['error']}\n"
        
        if result['status_code']:
            output += f"  Status Code: {result['status_code']}\n"
        
        output += "\nDiagnostic Information:\n"
        output += "  - Verify Firebase deployment completed successfully\n"
        output += "  - Check Firebase Hosting configuration\n"
        output += "  - Ensure DNS records are properly configured\n"
        
        return output


# Unit Tests

class TestFrontendHealthCheck:
    """Tests for frontend health check functionality."""
    
    @patch('requests.get')
    def test_health_check_validates_index_html_accessibility(self, mock_get):
        """
        Test that health check validates index.html is accessible.
        
        **Validates: Requirements 7.1, 7.2**
        """
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            'Content-Type': 'text/html',
            'Cache-Control': 'public, max-age=3600, must-revalidate'
        }
        mock_get.return_value = mock_response
        
        # Act
        result = check_frontend_health('https://test-project.web.app')
        
        # Assert
        assert result['success'] is True
        assert result['status_code'] == 200
        assert result['error'] is None
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_health_check_detects_404_error(self, mock_get):
        """
        Test that health check detects when index.html is not found.
        
        **Validates: Requirements 7.2**
        """
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.headers = {}
        mock_get.return_value = mock_response
        
        # Act
        result = check_frontend_health('https://test-project.web.app')
        
        # Assert
        assert result['success'] is False
        assert result['status_code'] == 404
        assert 'HTTP 404' in result['error']
    
    @patch('requests.get')
    def test_health_check_detects_connection_failure(self, mock_get):
        """
        Test that health check detects connection failures.
        
        **Validates: Requirements 7.2, 7.4**
        """
        # Arrange
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError('Connection refused')
        
        # Act
        result = check_frontend_health('https://test-project.web.app')
        
        # Assert
        assert result['success'] is False
        assert result['status_code'] is None
        assert 'Connection failed' in result['error']
    
    @patch('requests.get')
    def test_health_check_detects_timeout(self, mock_get):
        """
        Test that health check detects request timeouts.
        
        **Validates: Requirements 7.2, 7.4**
        """
        # Arrange
        import requests
        mock_get.side_effect = requests.exceptions.Timeout('Request timed out')
        
        # Act
        result = check_frontend_health('https://test-project.web.app', timeout=5)
        
        # Assert
        assert result['success'] is False
        assert result['status_code'] is None
        assert 'timeout' in result['error'].lower()
    
    @patch('requests.get')
    def test_health_check_extracts_cache_headers(self, mock_get):
        """
        Test that health check extracts cache control headers.
        
        **Validates: Requirements 7.2**
        """
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            'Content-Type': 'text/html',
            'Cache-Control': 'public, max-age=3600, must-revalidate'
        }
        mock_get.return_value = mock_response
        
        # Act
        result = check_frontend_health('https://test-project.web.app')
        
        # Assert
        assert result['cache_headers'] is not None
        assert 'cache-control' in result['cache_headers']
        assert 'public' in result['cache_headers']['cache-control']
    
    @patch('requests.get')
    def test_health_check_handles_missing_cache_headers(self, mock_get):
        """
        Test that health check handles missing cache headers gracefully.
        
        **Validates: Requirements 7.2**
        """
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_get.return_value = mock_response
        
        # Act
        result = check_frontend_health('https://test-project.web.app')
        
        # Assert
        assert result['success'] is True
        assert result['cache_headers'] is not None
        assert result['cache_headers']['cache-control'] == ''


class TestCacheHeaderValidation:
    """Tests for cache header validation."""
    
    def test_validates_html_cache_headers(self):
        """
        Test validation of HTML cache headers.
        
        **Validates: Requirements 7.2**
        """
        # Valid HTML cache headers
        assert validate_cache_headers('public, max-age=3600, must-revalidate', is_html=True)
        assert validate_cache_headers('public, max-age=3600', is_html=True)
        assert validate_cache_headers('PUBLIC, MAX-AGE=3600', is_html=True)  # Case insensitive
        
        # Invalid HTML cache headers
        assert not validate_cache_headers('', is_html=True)
        assert not validate_cache_headers('private', is_html=True)
        assert not validate_cache_headers('no-cache', is_html=True)
    
    def test_validates_static_asset_cache_headers(self):
        """
        Test validation of static asset cache headers.
        
        **Validates: Requirements 7.2**
        """
        # Valid static asset cache headers
        assert validate_cache_headers('public, max-age=31536000, immutable', is_html=False)
        assert validate_cache_headers('PUBLIC, MAX-AGE=31536000, IMMUTABLE', is_html=False)
        
        # Invalid static asset cache headers
        assert not validate_cache_headers('', is_html=False)
        assert not validate_cache_headers('public, max-age=3600', is_html=False)
        assert not validate_cache_headers('public, immutable', is_html=False)
    
    def test_rejects_empty_cache_headers(self):
        """
        Test that empty cache headers are rejected.
        
        **Validates: Requirements 7.2**
        """
        assert not validate_cache_headers('', is_html=True)
        assert not validate_cache_headers('', is_html=False)
        assert not validate_cache_headers(None, is_html=True)


class TestHealthCheckOutput:
    """Tests for health check output formatting."""
    
    def test_successful_deployment_displays_correct_url(self):
        """
        Test that successful deployment displays the Firebase Hosting URL.
        
        **Validates: Requirements 7.5**
        """
        # Arrange
        result = {
            'success': True,
            'status_code': 200,
            'cache_headers': {
                'cache-control': 'public, max-age=3600',
                'content-type': 'text/html'
            },
            'error': None
        }
        frontend_url = 'https://test-project.web.app'
        
        # Act
        output = format_health_check_output(result, frontend_url)
        
        # Assert
        assert frontend_url in output
        assert '✓' in output or 'accessible' in output.lower()
        assert '200' in output
    
    def test_failed_deployment_reports_diagnostic_info(self):
        """
        Test that failed health check reports diagnostic information.
        
        **Validates: Requirements 7.4**
        """
        # Arrange
        result = {
            'success': False,
            'status_code': 404,
            'cache_headers': None,
            'error': 'HTTP 404'
        }
        frontend_url = 'https://test-project.web.app'
        
        # Act
        output = format_health_check_output(result, frontend_url)
        
        # Assert
        assert 'failed' in output.lower()
        assert '404' in output
        assert 'Diagnostic' in output or 'diagnostic' in output.lower()
        assert 'Verify' in output or 'verify' in output.lower()
    
    def test_connection_failure_provides_troubleshooting_steps(self):
        """
        Test that connection failures provide troubleshooting guidance.
        
        **Validates: Requirements 7.4**
        """
        # Arrange
        result = {
            'success': False,
            'status_code': None,
            'cache_headers': None,
            'error': 'Connection failed'
        }
        frontend_url = 'https://test-project.web.app'
        
        # Act
        output = format_health_check_output(result, frontend_url)
        
        # Assert
        assert 'failed' in output.lower()
        assert 'Connection failed' in output
        assert 'Diagnostic' in output or 'diagnostic' in output.lower()
        # Should provide actionable guidance
        assert any(word in output.lower() for word in ['verify', 'check', 'ensure'])
    
    def test_output_includes_cache_header_info(self):
        """
        Test that output includes cache header information.
        
        **Validates: Requirements 7.2, 7.5**
        """
        # Arrange
        result = {
            'success': True,
            'status_code': 200,
            'cache_headers': {
                'cache-control': 'public, max-age=3600, must-revalidate',
                'content-type': 'text/html'
            },
            'error': None
        }
        frontend_url = 'https://test-project.web.app'
        
        # Act
        output = format_health_check_output(result, frontend_url)
        
        # Assert
        assert 'Cache-Control' in output or 'cache' in output.lower()
        assert 'public' in output.lower()
    
    def test_output_format_is_readable(self):
        """
        Test that output is formatted in a readable way.
        
        **Validates: Requirements 7.5**
        """
        # Arrange
        result = {
            'success': True,
            'status_code': 200,
            'cache_headers': {
                'cache-control': 'public, max-age=3600',
                'content-type': 'text/html'
            },
            'error': None
        }
        frontend_url = 'https://test-project.web.app'
        
        # Act
        output = format_health_check_output(result, frontend_url)
        
        # Assert
        # Should have multiple lines for readability
        assert '\n' in output
        # Should have clear structure
        lines = output.split('\n')
        assert len(lines) >= 2
        # Should not be overly verbose
        assert len(output) < 1000


class TestHealthCheckIntegration:
    """Integration tests for health check workflow."""
    
    @patch('requests.get')
    def test_complete_health_check_workflow_success(self, mock_get):
        """
        Test complete health check workflow for successful deployment.
        
        **Validates: Requirements 7.1, 7.2, 7.5**
        """
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            'Content-Type': 'text/html',
            'Cache-Control': 'public, max-age=3600, must-revalidate'
        }
        mock_get.return_value = mock_response
        frontend_url = 'https://test-project.web.app'
        
        # Act
        result = check_frontend_health(frontend_url)
        output = format_health_check_output(result, frontend_url)
        
        # Assert
        assert result['success'] is True
        assert frontend_url in output
        assert result['cache_headers'] is not None
        
        # Validate cache headers
        cache_control = result['cache_headers']['cache-control']
        assert validate_cache_headers(cache_control, is_html=True)
    
    @patch('requests.get')
    def test_complete_health_check_workflow_failure(self, mock_get):
        """
        Test complete health check workflow for failed deployment.
        
        **Validates: Requirements 7.2, 7.4**
        """
        # Arrange
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError('Connection refused')
        frontend_url = 'https://test-project.web.app'
        
        # Act
        result = check_frontend_health(frontend_url)
        output = format_health_check_output(result, frontend_url)
        
        # Assert
        assert result['success'] is False
        assert 'failed' in output.lower()
        assert 'Diagnostic' in output or 'diagnostic' in output.lower()
        assert frontend_url in output
