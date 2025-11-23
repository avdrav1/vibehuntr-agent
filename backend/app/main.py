"""FastAPI application entry point."""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Load .env file from project root
# This ensures environment variables are available before any imports
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)
    # Also set GOOGLE_API_KEY explicitly for Google ADK
    if "GOOGLE_API_KEY" in os.environ:
        os.environ["GOOGLE_API_KEY"] = os.environ["GOOGLE_API_KEY"]

from backend.app.api import chat, sessions, context, link_preview
from backend.app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="Backend API for Vibehuntr event planning agent",
    version=settings.app_version,
    debug=settings.debug
)

# CORS configuration for development and production
# Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
# Requirements: 8.2, 8.3, 8.4

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle HTTP exceptions with proper logging and user-friendly messages.
    
    Args:
        request: The incoming request
        exc: The HTTP exception
        
    Returns:
        JSONResponse with error details
        
    Requirements:
    - 8.2: Show error in chat interface when agent fails
    - 8.3: Include sufficient context for debugging when error is logged
    - 8.4: Do not expose internal implementation details when displaying errors
    """
    # Log the error with context
    logger.error(
        f"HTTP {exc.status_code} error on {request.method} {request.url.path}: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "method": request.method,
            "path": request.url.path,
            "client_host": request.client.host if request.client else None,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors with detailed information.
    
    Args:
        request: The incoming request
        exc: The validation error
        
    Returns:
        JSONResponse with validation error details
        
    Requirements:
    - 8.2: Show error in chat interface
    - 8.3: Include sufficient context for debugging
    - 8.4: Provide user-friendly error messages
    """
    # Log validation errors with details
    logger.warning(
        f"Validation error on {request.method} {request.url.path}: {exc.errors()}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "errors": exc.errors(),
            "client_host": request.client.host if request.client else None,
        }
    )
    
    # Create user-friendly error message
    error_messages = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        error_messages.append(f"{field}: {message}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Invalid request data",
            "details": error_messages,
            "status_code": 422,
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for all unhandled exceptions.
    
    This handler catches any exception that wasn't handled by more specific
    handlers, logs it with full context, and returns a user-friendly error
    message without exposing internal implementation details.
    
    Args:
        request: The incoming request
        exc: The unhandled exception
        
    Returns:
        JSONResponse with generic error message
        
    Requirements:
    - 8.2: Show error in chat interface when agent fails
    - 8.3: Include sufficient context for debugging when error is logged
    - 8.4: Do not expose internal implementation details when displaying errors
    """
    # Log the full exception with stack trace
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: "
        f"{type(exc).__name__}: {str(exc)}",
        exc_info=True,
        extra={
            "exception_type": type(exc).__name__,
            "method": request.method,
            "path": request.url.path,
            "client_host": request.client.host if request.client else None,
        }
    )
    
    # Return user-friendly error message without internal details
    # Requirements: 8.4
    if settings.debug:
        # In debug mode, include more details for development
        error_detail = f"Internal server error: {type(exc).__name__}: {str(exc)}"
    else:
        # In production, hide implementation details
        error_detail = "An internal server error occurred. Please try again later."
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": error_detail,
            "status_code": 500,
        }
    )


# Include routers
app.include_router(chat.router)
app.include_router(sessions.router)
app.include_router(context.router)
app.include_router(link_preview.router)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Status information
    
    Requirements: 1.1
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Vibehuntr Agent API",
        "docs": "/docs",
        "health": "/health"
    }
