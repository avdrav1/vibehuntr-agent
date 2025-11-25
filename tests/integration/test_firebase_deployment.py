"""Integration tests for Firebase Hosting deployment workflow.

This module tests the complete deployment workflow from build to Firebase,
including frontend accessibility, API communication, route testing, and
CORS integration between Firebase frontend and Cloud Run backend.

Requirements: 1.1, 1.2, 1.3 (Firebase Hosting Migration)
"""

import pytest
import os
import subprocess
import requests
import time
from typing import Dict, Any, Optional
from unittest.mock import patch, Mock


# Test configuration
TEST_PROJECT_ID = os.getenv('TEST_PROJECT_ID', 'vibehuntr-test')
TEST_BACKEND_URL = os.getenv('TEST_BACKEND_URL', 'https://vibehuntr-backend-test.run.app')
TEST_FRONTEND_URL = f"https://{TEST_PROJECT_ID}.web.app"
TIMEOUT = 30  # seconds


class DeploymentTestHelper:
    """Helper class for deployment testing operations."""
    
    @staticmethod
    def check_firebase_cli_installed() -> bool:
        """Check if Firebase CLI is installed."""
        try:
            result = subprocess.run(
                ['firebase', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    @staticmethod
    def check_npm_installed() -> bool:
        """Check if npm is installed."""
        try:
            result = subprocess.run(
                ['npm', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    @staticmethod
    def build_frontend(api_url: str) -> Dict[str, Any]:
        """
        Build the frontend application.
        
        Args:
            api_url: Backend API URL to configure
            
        Returns:
            Dictionary with build results
        """
        try:
            # Set environment variable for build
            env = os.environ.copy()
            env['VITE_API_URL'] = api_url
            
            # Run npm install
            install_result = subprocess.run(
                ['npm', 'ci'],
                cwd='frontend',
                capture_output=True,
                text=True,
                timeout=300,
                env=env
            )
            
            if install_result.returncode != 0:
                return {
                    'success': False,
                    'error': f"npm install failed: {install_result.stderr}",
                    'stdout': install_result.stdout,
                    'stderr': install_result.stderr
                }
            
            # Run build
            build_result = subprocess.run(
                ['npm', 'run', 'build'],
                cwd='frontend',
                capture_output=True,
                text=True,
                timeout=300,
                env=env
            )
            
            if build_result.returncode != 0:
                return {
                    'success': False,
                    'error': f"npm build failed: {build_result.stderr}",
                    'stdout': build_result.stdout,
                    'stderr': build_result.stderr
                }
            
            # Check if dist directory exists
            dist_path = os.path.join('frontend', 'dist')
            if not os.path.exists(dist_path):
                return {
                    'success': False,
                    'error': 'Build output directory (dist) not found',
                    'stdout': build_result.stdout,
                    'stderr': build_result.stderr
                }
            
            return {
                'success': True,
                'error': None,
                'stdout': build_result.stdout,
                'stderr': build_result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Build process timed out',
                'stdout': '',
                'stderr': ''
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Build failed: {str(e)}",
                'stdout': '',
                'stderr': ''
            }
    
    @staticmethod
    def check_frontend_accessible(url: str, timeout: int = TIMEOUT) -> Dict[str, Any]:
        """
        Check if frontend is accessible at the given URL.
        
        Args:
            url: Frontend URL to check
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary with accessibility check results
        """
        try:
            response = requests.get(url, timeout=timeout, allow_redirects=True)
            
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content_length': len(response.content),
                'error': None if response.status_code == 200 else f"HTTP {response.status_code}"
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'status_code': None,
                'headers': {},
                'content_length': 0,
                'error': 'Request timeout'
            }
        except requests.exceptions.ConnectionError as e:
            return {
                'success': False,
                'status_code': None,
                'headers': {},
                'content_length': 0,
                'error': f'Connection failed: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'headers': {},
                'content_length': 0,
                'error': str(e)
            }
    
    @staticmethod
    def test_api_communication(frontend_url: str, backend_url: str, timeout: int = TIMEOUT) -> Dict[str, Any]:
        """
        Test API communication from frontend to backend.
        
        Args:
            frontend_url: Frontend URL
            backend_url: Backend API URL
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary with API communication test results
        """
        try:
            # Test backend health endpoint
            health_response = requests.get(
                f"{backend_url}/health",
                timeout=timeout,
                headers={'Origin': frontend_url}
            )
            
            if health_response.status_code != 200:
                return {
                    'success': False,
                    'error': f"Backend health check failed: HTTP {health_response.status_code}",
                    'cors_headers': {}
                }
            
            # Check CORS headers
            cors_headers = {
                'access-control-allow-origin': health_response.headers.get('Access-Control-Allow-Origin', ''),
                'access-control-allow-methods': health_response.headers.get('Access-Control-Allow-Methods', ''),
                'access-control-allow-headers': health_response.headers.get('Access-Control-Allow-Headers', '')
            }
            
            # Verify CORS allows the frontend origin
            allowed_origin = cors_headers['access-control-allow-origin']
            cors_configured = allowed_origin == '*' or frontend_url in allowed_origin
            
            return {
                'success': True,
                'cors_configured': cors_configured,
                'cors_headers': cors_headers,
                'backend_healthy': True,
                'error': None
            }
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Backend request timeout',
                'cors_headers': {}
            }
        except requests.exceptions.ConnectionError as e:
            return {
                'success': False,
                'error': f'Backend connection failed: {str(e)}',
                'cors_headers': {}
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'cors_headers': {}
            }
    
    @staticmethod
    def test_application_routes(frontend_url: str, routes: list, timeout: int = TIMEOUT) -> Dict[str, Any]:
        """
        Test that application routes return 200 status.
        
        Args:
            frontend_url: Frontend URL
            routes: List of routes to test
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary with route test results
        """
        results = {}
        all_success = True
        
        for route in routes:
            url = f"{frontend_url}{route}"
            try:
                response = requests.get(url, timeout=timeout, allow_redirects=True)
                success = response.status_code == 200
                
                results[route] = {
                    'success': success,
                    'status_code': response.status_code,
                    'error': None if success else f"HTTP {response.status_code}"
                }
                
                if not success:
                    all_success = False
                    
            except Exception as e:
                results[route] = {
                    'success': False,
                    'status_code': None,
                    'error': str(e)
                }
                all_success = False
        
        return {
            'success': all_success,
            'routes': results,
            'total_routes': len(routes),
            'successful_routes': sum(1 for r in results.values() if r['success'])
        }


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv('RUN_DEPLOYMENT_TESTS'),
    reason="Deployment tests require RUN_DEPLOYMENT_TESTS=1 environment variable"
)
class TestFirebaseDeploymentWorkflow:
    """
    Integration tests for complete Firebase deployment workflow.
    
    These tests verify the end-to-end deployment process including:
    - Frontend build process
    - Firebase deployment
    - Frontend accessibility
    - API communication
    - Route functionality
    - CORS configuration
    
    Requirements: 1.1, 1.2, 1.3
    """
    
    def test_prerequisites_installed(self):
        """
        Test that required tools are installed.
        
        **Validates: Requirements 1.1**
        """
        helper = DeploymentTestHelper()
        
        # Check Firebase CLI
        assert helper.check_firebase_cli_installed(), \
            "Firebase CLI is not installed. Install with: npm install -g firebase-tools"
        
        # Check npm
        assert helper.check_npm_installed(), \
            "npm is not installed. Please install Node.js and npm"
    
    def test_frontend_build_process(self):
        """
        Test that frontend builds successfully with backend API URL.
        
        **Validates: Requirements 1.1**
        """
        helper = DeploymentTestHelper()
        
        # Build frontend with test backend URL
        result = helper.build_frontend(TEST_BACKEND_URL)
        
        # Assert build succeeded
        assert result['success'], \
            f"Frontend build failed: {result['error']}\nStdout: {result['stdout']}\nStderr: {result['stderr']}"
        
        # Verify dist directory exists
        dist_path = os.path.join('frontend', 'dist')
        assert os.path.exists(dist_path), "Build output directory (dist) not found"
        
        # Verify index.html exists
        index_path = os.path.join(dist_path, 'index.html')
        assert os.path.exists(index_path), "index.html not found in build output"
    
    @pytest.mark.skipif(
        not os.getenv('TEST_DEPLOYED_FRONTEND'),
        reason="Requires deployed frontend (TEST_DEPLOYED_FRONTEND=1)"
    )
    def test_frontend_accessible_at_firebase_url(self):
        """
        Test that frontend is accessible at Firebase Hosting URL.
        
        This test requires a deployed frontend and should be run after deployment.
        
        **Validates: Requirements 1.2**
        """
        helper = DeploymentTestHelper()
        
        # Check frontend accessibility
        result = helper.check_frontend_accessible(TEST_FRONTEND_URL)
        
        # Assert frontend is accessible
        assert result['success'], \
            f"Frontend not accessible at {TEST_FRONTEND_URL}: {result['error']}"
        
        assert result['status_code'] == 200, \
            f"Expected HTTP 200, got {result['status_code']}"
        
        # Verify we got HTML content
        assert result['content_length'] > 0, "Frontend returned empty content"
        
        # Verify content type
        content_type = result['headers'].get('content-type', '').lower()
        assert 'text/html' in content_type, \
            f"Expected HTML content, got {content_type}"
    
    @pytest.mark.skipif(
        not os.getenv('TEST_DEPLOYED_FRONTEND'),
        reason="Requires deployed frontend (TEST_DEPLOYED_FRONTEND=1)"
    )
    def test_api_communication_works_from_deployed_frontend(self):
        """
        Test that API communication works from deployed frontend to backend.
        
        This test verifies CORS configuration and backend connectivity.
        
        **Validates: Requirements 1.3**
        """
        helper = DeploymentTestHelper()
        
        # Test API communication
        result = helper.test_api_communication(TEST_FRONTEND_URL, TEST_BACKEND_URL)
        
        # Assert API communication works
        assert result['success'], \
            f"API communication failed: {result['error']}"
        
        assert result.get('backend_healthy'), \
            "Backend health check failed"
        
        # Verify CORS is configured
        assert result.get('cors_configured'), \
            f"CORS not properly configured. Headers: {result.get('cors_headers', {})}"
    
    @pytest.mark.skipif(
        not os.getenv('TEST_DEPLOYED_FRONTEND'),
        reason="Requires deployed frontend (TEST_DEPLOYED_FRONTEND=1)"
    )
    def test_all_application_routes_return_200(self):
        """
        Test that all application routes return 200 status.
        
        This verifies SPA routing is working correctly with Firebase Hosting.
        
        **Validates: Requirements 1.2**
        """
        helper = DeploymentTestHelper()
        
        # Define routes to test (SPA routes)
        routes = [
            '/',
            '/chat',
            '/about',
            '/settings',
            '/nonexistent-route'  # Should still return 200 due to SPA rewrites
        ]
        
        # Test all routes
        result = helper.test_application_routes(TEST_FRONTEND_URL, routes)
        
        # Assert all routes return 200
        assert result['success'], \
            f"Some routes failed: {result['routes']}"
        
        assert result['successful_routes'] == result['total_routes'], \
            f"Only {result['successful_routes']}/{result['total_routes']} routes succeeded"
        
        # Verify each route individually
        for route, route_result in result['routes'].items():
            assert route_result['success'], \
                f"Route {route} failed: {route_result['error']}"
    
    @pytest.mark.skipif(
        not os.getenv('TEST_DEPLOYED_FRONTEND'),
        reason="Requires deployed frontend (TEST_DEPLOYED_FRONTEND=1)"
    )
    def test_cors_integration_between_firebase_and_cloud_run(self):
        """
        Test CORS integration between Firebase Hosting frontend and Cloud Run backend.
        
        This test verifies that:
        1. Backend accepts requests from Firebase Hosting origin
        2. CORS headers are properly set
        3. Preflight requests work correctly
        
        **Validates: Requirements 1.3**
        """
        # Test preflight request (OPTIONS)
        try:
            response = requests.options(
                f"{TEST_BACKEND_URL}/api/sessions",
                headers={
                    'Origin': TEST_FRONTEND_URL,
                    'Access-Control-Request-Method': 'POST',
                    'Access-Control-Request-Headers': 'content-type'
                },
                timeout=TIMEOUT
            )
            
            # Preflight should succeed
            assert response.status_code in [200, 204], \
                f"Preflight request failed with status {response.status_code}"
            
            # Check CORS headers in preflight response
            assert 'access-control-allow-origin' in response.headers, \
                "CORS Allow-Origin header missing in preflight response"
            
            assert 'access-control-allow-methods' in response.headers, \
                "CORS Allow-Methods header missing in preflight response"
            
        except Exception as e:
            pytest.fail(f"CORS preflight request failed: {str(e)}")
        
        # Test actual request with Origin header
        try:
            response = requests.get(
                f"{TEST_BACKEND_URL}/health",
                headers={'Origin': TEST_FRONTEND_URL},
                timeout=TIMEOUT
            )
            
            assert response.status_code == 200, \
                f"Request with Origin header failed: HTTP {response.status_code}"
            
            # Verify CORS headers
            allowed_origin = response.headers.get('access-control-allow-origin', '')
            assert allowed_origin == '*' or TEST_FRONTEND_URL in allowed_origin, \
                f"Frontend origin not allowed. Allowed: {allowed_origin}"
            
        except Exception as e:
            pytest.fail(f"Request with Origin header failed: {str(e)}")
    
    @pytest.mark.skipif(
        not os.getenv('TEST_DEPLOYED_FRONTEND'),
        reason="Requires deployed frontend (TEST_DEPLOYED_FRONTEND=1)"
    )
    def test_cache_headers_configured_correctly(self):
        """
        Test that cache headers are configured correctly for different asset types.
        
        **Validates: Requirements 1.2**
        """
        helper = DeploymentTestHelper()
        
        # Test HTML file (index.html)
        html_result = helper.check_frontend_accessible(TEST_FRONTEND_URL)
        assert html_result['success'], "Frontend not accessible"
        
        # Check cache headers for HTML
        cache_control = html_result['headers'].get('cache-control', '').lower()
        assert 'public' in cache_control, \
            f"HTML cache headers should include 'public': {cache_control}"
        
        # HTML should have shorter cache time
        assert 'max-age' in cache_control, \
            f"HTML cache headers should include 'max-age': {cache_control}"
    
    @pytest.mark.skipif(
        not os.getenv('TEST_DEPLOYED_FRONTEND'),
        reason="Requires deployed frontend (TEST_DEPLOYED_FRONTEND=1)"
    )
    def test_https_enforced(self):
        """
        Test that HTTPS is enforced for all requests.
        
        **Validates: Requirements 1.2**
        """
        # Firebase Hosting automatically enforces HTTPS
        # Verify the URL uses HTTPS
        assert TEST_FRONTEND_URL.startswith('https://'), \
            f"Frontend URL should use HTTPS: {TEST_FRONTEND_URL}"
        
        # Try to access via HTTPS
        try:
            response = requests.get(TEST_FRONTEND_URL, timeout=TIMEOUT)
            assert response.status_code == 200, \
                f"HTTPS request failed: HTTP {response.status_code}"
        except Exception as e:
            pytest.fail(f"HTTPS request failed: {str(e)}")


@pytest.mark.integration
class TestDeploymentScriptMocked:
    """
    Mock-based tests for deployment script functionality.
    
    These tests don't require actual deployment and can run in CI/CD.
    """
    
    def test_build_process_sets_api_url(self):
        """
        Test that build process correctly sets API URL environment variable.
        
        **Validates: Requirements 1.1**
        """
        helper = DeploymentTestHelper()
        
        # Mock the subprocess calls
        with patch('subprocess.run') as mock_run:
            # Mock successful npm install
            mock_run.return_value = Mock(
                returncode=0,
                stdout='Dependencies installed',
                stderr=''
            )
            
            # Mock os.path.exists to return True for dist directory
            with patch('os.path.exists', return_value=True):
                result = helper.build_frontend('https://test-backend.run.app')
                
                # Verify build was called
                assert mock_run.called
                
                # Verify environment variable was set
                calls = mock_run.call_args_list
                for call in calls:
                    if 'env' in call.kwargs:
                        env = call.kwargs['env']
                        if 'VITE_API_URL' in env:
                            assert env['VITE_API_URL'] == 'https://test-backend.run.app'
                            break
    
    def test_deployment_handles_build_failure(self):
        """
        Test that deployment handles build failures gracefully.
        
        **Validates: Requirements 1.1**
        """
        helper = DeploymentTestHelper()
        
        # Mock failed build
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout='',
                stderr='Build failed: syntax error'
            )
            
            result = helper.build_frontend('https://test-backend.run.app')
            
            # Verify failure is reported
            assert not result['success']
            assert 'failed' in result['error'].lower()
            assert result['stderr'] != ''
    
    def test_health_check_detects_frontend_unavailable(self):
        """
        Test that health check detects when frontend is unavailable.
        
        **Validates: Requirements 1.2**
        """
        helper = DeploymentTestHelper()
        
        # Mock connection error
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError('Connection refused')
            
            result = helper.check_frontend_accessible('https://test.web.app')
            
            # Verify failure is detected
            assert not result['success']
            assert 'connection' in result['error'].lower()
    
    def test_api_communication_detects_cors_issues(self):
        """
        Test that API communication test detects CORS configuration issues.
        
        **Validates: Requirements 1.3**
        """
        helper = DeploymentTestHelper()
        
        # Mock response without CORS headers
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {}  # No CORS headers
            mock_get.return_value = mock_response
            
            result = helper.test_api_communication(
                'https://test.web.app',
                'https://backend.run.app'
            )
            
            # Verify CORS issue is detected
            assert not result.get('cors_configured', False)


@pytest.mark.integration
class TestDeploymentWorkflowEnd2End:
    """
    End-to-end tests for complete deployment workflow.
    
    These tests simulate the full deployment process.
    """
    
    @pytest.mark.skipif(
        not os.getenv('RUN_FULL_DEPLOYMENT_TEST'),
        reason="Full deployment test requires RUN_FULL_DEPLOYMENT_TEST=1"
    )
    def test_complete_deployment_workflow(self):
        """
        Test complete deployment workflow from build to verification.
        
        This is a comprehensive test that:
        1. Builds the frontend
        2. Verifies build artifacts
        3. Checks frontend accessibility (if deployed)
        4. Tests API communication (if deployed)
        5. Verifies all routes work (if deployed)
        
        **Validates: Requirements 1.1, 1.2, 1.3**
        """
        helper = DeploymentTestHelper()
        
        # Step 1: Build frontend
        print("\n[1/5] Building frontend...")
        build_result = helper.build_frontend(TEST_BACKEND_URL)
        assert build_result['success'], \
            f"Build failed: {build_result['error']}"
        print("✓ Frontend built successfully")
        
        # Step 2: Verify build artifacts
        print("\n[2/5] Verifying build artifacts...")
        dist_path = os.path.join('frontend', 'dist')
        assert os.path.exists(dist_path), "dist directory not found"
        assert os.path.exists(os.path.join(dist_path, 'index.html')), \
            "index.html not found"
        print("✓ Build artifacts verified")
        
        # If deployed, run additional checks
        if os.getenv('TEST_DEPLOYED_FRONTEND'):
            # Step 3: Check frontend accessibility
            print(f"\n[3/5] Checking frontend accessibility at {TEST_FRONTEND_URL}...")
            access_result = helper.check_frontend_accessible(TEST_FRONTEND_URL)
            assert access_result['success'], \
                f"Frontend not accessible: {access_result['error']}"
            print("✓ Frontend is accessible")
            
            # Step 4: Test API communication
            print("\n[4/5] Testing API communication...")
            api_result = helper.test_api_communication(TEST_FRONTEND_URL, TEST_BACKEND_URL)
            assert api_result['success'], \
                f"API communication failed: {api_result['error']}"
            print("✓ API communication works")
            
            # Step 5: Test routes
            print("\n[5/5] Testing application routes...")
            routes = ['/', '/chat', '/about']
            route_result = helper.test_application_routes(TEST_FRONTEND_URL, routes)
            assert route_result['success'], \
                f"Route tests failed: {route_result['routes']}"
            print(f"✓ All {route_result['total_routes']} routes work correctly")
            
            print("\n✓ Complete deployment workflow verified successfully!")
        else:
            print("\n[3-5/5] Skipping deployed frontend tests (TEST_DEPLOYED_FRONTEND not set)")
            print("✓ Build workflow verified successfully!")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
