"""Context API endpoints for managing conversation context.

This module provides REST API endpoints for context management:
- GET /api/context/{session_id}: Get current context for a session
- DELETE /api/context/{session_id}: Clear all context for a session
- DELETE /api/context/{session_id}/item: Clear specific context items

Requirements: 11.2, 10.2, 10.3, 11.6
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Path as PathParam, Query

# Add parent directory to path to import main app modules
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent
print(f"DEBUG context.py: current_file = {current_file}")
print(f"DEBUG context.py: project_root = {project_root}")
print(f"DEBUG context.py: sys.path[:3] = {sys.path[:3]}")
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    print(f"DEBUG context.py: Added project_root to sys.path")

from ..models.schemas import (
    ContextResponse,
    StatusResponse,
    ErrorResponse,
)
from app.event_planning.context_manager import get_context, clear_context as clear_context_store


# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/context", tags=["context"])


@router.get(
    "/{session_id}",
    response_model=ContextResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
        500: {"model": ErrorResponse, "description": "Failed to retrieve context"},
    },
)
async def get_session_context(
    session_id: str = PathParam(..., description="Session identifier")
) -> ContextResponse:
    """
    Get current context for a session.
    
    This endpoint retrieves the complete conversation context for a given
    session, including location, search query, and recently mentioned venues.
    
    Args:
        session_id: Unique identifier for the session
        
    Returns:
        ContextResponse: Current context information
        
    Raises:
        HTTPException: 500 on errors
        
    Requirements:
    - 11.2: Backend provides API endpoint to retrieve current context
    """
    try:
        logger.info(f"Retrieving context for session: {session_id}")
        
        # Get context from context manager
        context = get_context(session_id)
        
        # Convert to response model
        response = ContextResponse(
            user_name=context.user_name,
            user_email=context.user_email,
            location=context.location,
            search_query=context.search_query,
            event_venue_name=context.event_venue_name,
            event_date_time=context.event_date_time,
            event_party_size=context.event_party_size,
            recent_venues=[
                {
                    "name": v.name,
                    "place_id": v.place_id,
                    "location": v.location
                }
                for v in context.recent_venues
            ]
        )
        
        logger.info(
            f"Retrieved context for session {session_id}: "
            f"name={context.user_name}, email={context.user_email}, "
            f"location={context.location}, query={context.search_query}, "
            f"venues={len(context.recent_venues)}"
        )
        return response
        
    except Exception as e:
        logger.error(
            f"Failed to retrieve context for session {session_id}: "
            f"{type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve context: {str(e)}"
        )


@router.delete(
    "/{session_id}",
    response_model=StatusResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Failed to clear context"},
    },
)
async def clear_session_context(
    session_id: str = PathParam(..., description="Session identifier")
) -> StatusResponse:
    """
    Clear all context for a session.
    
    This endpoint removes all stored context (location, search query, venues)
    for a given session. This is useful when starting a fresh conversation
    or when the user wants to reset the agent's memory.
    
    Args:
        session_id: Unique identifier for the session
        
    Returns:
        StatusResponse: Success status
        
    Raises:
        HTTPException: 500 on errors
        
    Requirements:
    - 10.2: Backend clears all context when user starts new conversation
    - 10.3: Backend logs session_id and timestamp when context is cleared
    """
    try:
        logger.info(f"Clearing context for session: {session_id}")
        
        # Clear context from context manager
        clear_context_store(session_id)
        
        logger.info(f"Context cleared successfully for session {session_id}")
        return StatusResponse(
            success=True,
            message=f"Context cleared for session {session_id}"
        )
        
    except Exception as e:
        logger.error(
            f"Failed to clear context for session {session_id}: "
            f"{type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear context: {str(e)}"
        )


@router.delete(
    "/{session_id}/item",
    response_model=StatusResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Failed to clear context item"},
    },
)
async def clear_context_item(
    session_id: str = PathParam(..., description="Session identifier"),
    item_type: str = Query(..., description="Type of item to clear: location, query, or venue"),
    index: Optional[int] = Query(None, description="Index of venue to remove (for venue type)")
) -> StatusResponse:
    """
    Clear a specific context item.
    
    This endpoint allows clearing individual context items without removing
    all context. Supported item types:
    - location: Clear stored location
    - query: Clear stored search query
    - venue: Clear a specific venue (requires index parameter)
    
    Args:
        session_id: Unique identifier for the session
        item_type: Type of item to clear (location, query, venue)
        index: Index of venue to remove (required for venue type)
        
    Returns:
        StatusResponse: Success status
        
    Raises:
        HTTPException: 400 for invalid requests, 500 on errors
        
    Requirements:
    - 11.6: Backend provides ability to clear individual context items
    """
    try:
        logger.info(
            f"Clearing context item for session {session_id}: "
            f"type={item_type}, index={index}"
        )
        
        # Validate item_type
        if item_type not in ["location", "query", "venue", "user_name", "user_email"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid item_type: {item_type}. "
                       "Must be 'location', 'query', 'venue', 'user_name', or 'user_email'"
            )
        
        # Get context
        context = get_context(session_id)
        
        # Clear specific item
        if item_type == "location":
            context.location = None
            logger.info(f"Cleared location for session {session_id}")
            
        elif item_type == "query":
            context.search_query = None
            logger.info(f"Cleared search query for session {session_id}")
            
        elif item_type == "user_name":
            context.user_name = None
            logger.info(f"Cleared user name for session {session_id}")
            
        elif item_type == "user_email":
            context.user_email = None
            logger.info(f"Cleared user email for session {session_id}")
            
        elif item_type == "venue":
            if index is None:
                raise HTTPException(
                    status_code=400,
                    detail="index parameter is required for venue type"
                )
            
            if index < 0 or index >= len(context.recent_venues):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid venue index: {index}. "
                           f"Must be between 0 and {len(context.recent_venues) - 1}"
                )
            
            removed_venue = context.recent_venues.pop(index)
            logger.info(
                f"Removed venue {removed_venue.name} at index {index} "
                f"for session {session_id}"
            )
        
        return StatusResponse(
            success=True,
            message=f"Cleared {item_type} for session {session_id}"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            f"Failed to clear context item for session {session_id}: "
            f"{type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear context item: {str(e)}"
        )
