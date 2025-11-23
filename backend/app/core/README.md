# Backend Configuration

This module provides centralized configuration management for the FastAPI backend.

## Overview

The configuration system uses `pydantic-settings` to load and validate environment variables, providing type-safe access to application settings.

## Usage

```python
from backend.app.core.config import settings

# Access configuration values
print(settings.app_name)
print(settings.environment)
print(settings.get_cors_origins())

# Check environment
if settings.is_production:
    # Production-specific logic
    pass
```

## Environment Variables

The following environment variables can be set in a `.env` file or as system environment variables:

### Application Settings

- `APP_NAME` (default: "Vibehuntr Agent API") - Application name
- `APP_VERSION` (default: "1.0.0") - Application version
- `ENVIRONMENT` (default: "development") - Environment (development/production)
- `DEBUG` (default: true) - Debug mode flag

### CORS Configuration

- `CORS_ORIGINS` (default: localhost URLs) - Comma-separated list of allowed CORS origins
  - Development: Automatically includes localhost:5173, localhost:3000, etc.
  - Production: Must be explicitly set to production domains

### API Keys

- `GOOGLE_API_KEY` - Google API key for services
- `GOOGLE_PLACES_API_KEY` - Google Places API key

### Server Configuration

- `BACKEND_HOST` (default: "0.0.0.0") - Backend host address
- `BACKEND_PORT` (default: 8000) - Backend port number

## Development vs Production

### Development Mode

In development mode (`ENVIRONMENT=development`):
- CORS allows all localhost ports (5173, 3000, etc.)
- Debug mode is enabled
- Detailed error messages are shown

### Production Mode

In production mode (`ENVIRONMENT=production`):
- CORS origins must be explicitly configured via `CORS_ORIGINS`
- Debug mode should be disabled
- Error messages are sanitized

## Example .env File

```env
# Application
APP_NAME=Vibehuntr Agent API
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true

# CORS (production example)
# CORS_ORIGINS=https://vibehuntr.com,https://app.vibehuntr.com

# API Keys
GOOGLE_API_KEY=your-api-key-here
GOOGLE_PLACES_API_KEY=your-places-api-key-here

# Server
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
```

## Requirements Satisfied

- **5.4**: Environment-specific CORS configuration
- **10.3**: Environment variable loading from .env files
