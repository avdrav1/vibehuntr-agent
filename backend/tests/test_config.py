"""Tests for configuration module."""

import os
from unittest.mock import patch

import pytest


def test_settings_defaults():
    """Test that settings load with default values."""
    from app.core.config import Settings
    
    settings = Settings()
    
    assert settings.app_name == "Vibehuntr Agent API"
    assert settings.app_version == "1.0.0"
    assert settings.environment == "development"
    assert settings.debug is True
    assert settings.backend_host == "0.0.0.0"
    assert settings.backend_port == 8000


def test_get_cors_origins_development():
    """Test CORS origins in development mode."""
    from app.core.config import Settings
    
    settings = Settings(environment="development")
    origins = settings.get_cors_origins()
    
    assert "http://localhost:5173" in origins
    assert "http://localhost:3000" in origins
    assert "http://127.0.0.1:5173" in origins
    assert "http://127.0.0.1:3000" in origins


def test_get_cors_origins_production():
    """Test CORS origins in production mode."""
    from app.core.config import Settings
    
    settings = Settings(
        environment="production",
        cors_origins="https://example.com,https://app.example.com"
    )
    origins = settings.get_cors_origins()
    
    assert "https://example.com" in origins
    assert "https://app.example.com" in origins
    assert len(origins) == 2


def test_is_production():
    """Test production environment detection."""
    from app.core.config import Settings
    
    prod_settings = Settings(environment="production")
    dev_settings = Settings(environment="development")
    
    assert prod_settings.is_production is True
    assert dev_settings.is_production is False


def test_is_development():
    """Test development environment detection."""
    from app.core.config import Settings
    
    prod_settings = Settings(environment="production")
    dev_settings = Settings(environment="development")
    
    assert prod_settings.is_development is False
    assert dev_settings.is_development is True


def test_settings_from_env():
    """Test loading settings from environment variables."""
    from app.core.config import Settings
    
    with patch.dict(os.environ, {
        "APP_NAME": "Test API",
        "APP_VERSION": "2.0.0",
        "ENVIRONMENT": "production",
        "DEBUG": "false",
        "GOOGLE_API_KEY": "test-key-123"
    }):
        settings = Settings()
        
        assert settings.app_name == "Test API"
        assert settings.app_version == "2.0.0"
        assert settings.environment == "production"
        assert settings.debug is False
        assert settings.google_api_key == "test-key-123"


def test_get_settings_cached():
    """Test that get_settings returns cached instance."""
    from app.core.config import get_settings
    
    settings1 = get_settings()
    settings2 = get_settings()
    
    # Should be the same instance due to lru_cache
    assert settings1 is settings2


def test_firebase_cors_origins_production():
    """
    Test that Firebase Hosting URLs are added to CORS origins in production.
    
    Requirements: 1.3 (Firebase Hosting Migration)
    """
    from app.core.config import Settings
    
    settings = Settings(
        environment="production",
        firebase_project_id="test-project-123",
        cors_origins="https://custom-domain.com"
    )
    origins = settings.get_cors_origins()
    
    # Should include custom domain
    assert "https://custom-domain.com" in origins
    
    # Should include Firebase Hosting URLs
    assert "https://test-project-123.web.app" in origins
    assert "https://test-project-123.firebaseapp.com" in origins
    
    # Should have 3 origins total
    assert len(origins) == 3


def test_firebase_cors_origins_no_project_id():
    """
    Test that Firebase URLs are not added when project ID is not set.
    
    Requirements: 1.3 (Firebase Hosting Migration)
    """
    from app.core.config import Settings
    
    settings = Settings(
        environment="production",
        firebase_project_id="",
        cors_origins="https://custom-domain.com"
    )
    origins = settings.get_cors_origins()
    
    # Should only include custom domain
    assert "https://custom-domain.com" in origins
    assert len(origins) == 1


def test_firebase_cors_origins_development():
    """
    Test that Firebase URLs are not added in development mode.
    
    Requirements: 1.3 (Firebase Hosting Migration)
    """
    from app.core.config import Settings
    
    settings = Settings(
        environment="development",
        firebase_project_id="test-project-123"
    )
    origins = settings.get_cors_origins()
    
    # Should only include localhost origins
    assert "http://localhost:5173" in origins
    assert "http://localhost:3000" in origins
    
    # Should NOT include Firebase URLs in development
    assert "https://test-project-123.web.app" not in origins
    assert "https://test-project-123.firebaseapp.com" not in origins


def test_firebase_cors_both_domains():
    """
    Test that both .web.app and .firebaseapp.com domains are included.
    
    Requirements: 1.3 (Firebase Hosting Migration)
    """
    from app.core.config import Settings
    
    settings = Settings(
        environment="production",
        firebase_project_id="my-app",
        cors_origins=""
    )
    origins = settings.get_cors_origins()
    
    # Both Firebase domains should be present
    assert "https://my-app.web.app" in origins
    assert "https://my-app.firebaseapp.com" in origins
    assert len(origins) == 2
