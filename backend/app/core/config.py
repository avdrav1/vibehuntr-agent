"""
Configuration management for the FastAPI backend.

This module handles environment variables and application settings
for both development and production environments.

Requirements: 5.4, 10.3
"""

import os
from typing import List
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Attributes:
        app_name: Application name
        app_version: Application version
        environment: Current environment (development/production)
        debug: Debug mode flag
        cors_origins: List of allowed CORS origins
        google_api_key: Google API key for services
        google_places_api_key: Google Places API key
        backend_host: Backend host address
        backend_port: Backend port number
        link_preview_enabled: Enable/disable link preview feature
        link_preview_timeout: Timeout for fetching link metadata (seconds)
        link_preview_cache_ttl: Cache TTL for link metadata (seconds)
        link_preview_max_size: Maximum response size for link fetching (bytes)
        link_preview_excluded_domains: Comma-separated list of domains to exclude
    """
    
    # Application settings
    app_name: str = "Vibehuntr Agent API"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    
    # CORS configuration
    # Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 1.3 (Firebase Hosting)
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"
    
    # Firebase Hosting configuration
    # Requirements: 1.3 (Firebase Hosting Migration)
    firebase_project_id: str = ""
    
    # API Keys
    google_api_key: str = ""
    google_places_api_key: str = ""
    
    # Server configuration
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    
    # Link Preview configuration
    # Requirements: 6.5
    link_preview_enabled: bool = True
    link_preview_timeout: int = 5
    link_preview_cache_ttl: int = 3600
    link_preview_max_size: int = 5000000
    link_preview_excluded_domains: str = ""
    
    model_config = SettingsConfigDict(
        # Look for .env in project root - works when running from project root
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    def get_cors_origins(self) -> List[str]:
        """
        Get CORS origins as a list.
        
        Returns:
            List of allowed CORS origin URLs
            
        Requirements: 5.1, 5.2, 5.5, 1.3 (Firebase Hosting)
        """
        origins = []
        
        if self.environment == "production":
            # In production, parse from environment variable
            # Should be comma-separated list of production domains
            env_origins = [origin.strip() for origin in self.cors_origins.split(",")]
            origins.extend([origin for origin in env_origins if origin])
            
            # Add Firebase Hosting URLs if project ID is configured
            # Requirements: 1.3 (Firebase Hosting Migration)
            if self.firebase_project_id:
                firebase_origins = [
                    f"https://{self.firebase_project_id}.web.app",
                    f"https://{self.firebase_project_id}.firebaseapp.com",
                ]
                origins.extend(firebase_origins)
        else:
            # In development, allow localhost ports
            origins = [
                "http://localhost:5173",  # Vite default
                "http://localhost:3000",  # Alternative React port
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000",
            ]
        
        return origins
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"
    
    def get_link_preview_excluded_domains(self) -> List[str]:
        """
        Get link preview excluded domains as a list.
        
        Returns:
            List of domain names to exclude from link preview generation
            
        Requirements: 6.5
        """
        if not self.link_preview_excluded_domains:
            return []
        domains = [domain.strip() for domain in self.link_preview_excluded_domains.split(",")]
        return [domain for domain in domains if domain]


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    This function uses lru_cache to ensure settings are loaded only once
    and reused throughout the application lifecycle.
    
    Returns:
        Settings instance with loaded configuration
        
    Requirements: 10.3
    """
    return Settings()


# Convenience function to get settings
settings = get_settings()
