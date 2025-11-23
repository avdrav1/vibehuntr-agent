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
    """
    
    # Application settings
    app_name: str = "Vibehuntr Agent API"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    
    # CORS configuration
    # Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"
    
    # API Keys
    google_api_key: str = ""
    google_places_api_key: str = ""
    
    # Server configuration
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    
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
            
        Requirements: 5.1, 5.2, 5.5
        """
        if self.environment == "production":
            # In production, parse from environment variable
            # Should be comma-separated list of production domains
            origins = [origin.strip() for origin in self.cors_origins.split(",")]
            return [origin for origin in origins if origin]
        else:
            # In development, allow localhost ports
            return [
                "http://localhost:5173",  # Vite default
                "http://localhost:3000",  # Alternative React port
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000",
            ]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


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
