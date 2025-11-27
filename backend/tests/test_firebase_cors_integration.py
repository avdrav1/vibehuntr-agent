"""Integration tests for Firebase Hosting CORS configuration.

This module tests that the backend properly allows requests from
Firebase Hosting URLs when configured.

Requirements: 1.3 (Firebase Hosting Migration)
"""

import pytest
from app.core.config import Settings


def test_firebase_cors_configuration_in_production():
    """
    Test that Firebase Hosting URLs are properly configured in CORS origins.
    
    This test verifies that when the backend is deployed to production with
    a Firebase project ID, the CORS configuration automatically includes
    both Firebase Hosting domains.
    
    Requirements: 1.3 (Firebase Hosting Migration)
    """
    # Simulate production environment with Firebase project
    settings = Settings(
        environment="production",
        firebase_project_id="vibehuntr-prod",
        cors_origins=""
    )
    
    origins = settings.get_cors_origins()
    
    # Verify Firebase Hosting URLs are included
    assert "https://vibehuntr-prod.web.app" in origins
    assert "https://vibehuntr-prod.firebaseapp.com" in origins
    assert len(origins) == 2


def test_firebase_cors_with_custom_domains():
    """
    Test that custom domains work alongside Firebase Hosting URLs.
    
    Requirements: 1.3 (Firebase Hosting Migration)
    """
    settings = Settings(
        environment="production",
        firebase_project_id="vibehuntr-prod",
        cors_origins="https://vibehuntr.com,https://www.vibehuntr.com"
    )
    
    origins = settings.get_cors_origins()
    
    # Should include custom domains
    assert "https://vibehuntr.com" in origins
    assert "https://www.vibehuntr.com" in origins
    
    # Should also include Firebase Hosting URLs
    assert "https://vibehuntr-prod.web.app" in origins
    assert "https://vibehuntr-prod.firebaseapp.com" in origins
    
    # Total of 4 origins
    assert len(origins) == 4


def test_firebase_cors_not_in_development():
    """
    Test that Firebase URLs are not added in development mode.
    
    In development, we only want localhost origins regardless of
    Firebase project ID configuration.
    
    Requirements: 1.3 (Firebase Hosting Migration)
    """
    settings = Settings(
        environment="development",
        firebase_project_id="vibehuntr-prod"
    )
    
    origins = settings.get_cors_origins()
    
    # Should only include localhost origins
    assert "http://localhost:5173" in origins
    assert "http://localhost:3000" in origins
    
    # Should NOT include Firebase URLs in development
    assert "https://vibehuntr-prod.web.app" not in origins
    assert "https://vibehuntr-prod.firebaseapp.com" not in origins


def test_firebase_cors_without_project_id():
    """
    Test that Firebase URLs are not added when project ID is empty.
    
    Requirements: 1.3 (Firebase Hosting Migration)
    """
    settings = Settings(
        environment="production",
        firebase_project_id="",
        cors_origins="https://custom-domain.com"
    )
    
    origins = settings.get_cors_origins()
    
    # Should only include custom domain
    assert "https://custom-domain.com" in origins
    assert len(origins) == 1
    
    # No Firebase URLs should be present
    for origin in origins:
        assert ".web.app" not in origin
        assert ".firebaseapp.com" not in origin
