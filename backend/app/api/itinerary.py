"""Itinerary API endpoints for group coordination.

This module provides REST API endpoints for itinerary management:
- POST /api/planning-sessions/{session_id}/itinerary - Add to itinerary
- DELETE /api/planning-sessions/{session_id}/itinerary/{item_id} - Remove from itinerary
- GET /api/planning-sessions/{session_id}/itinerary - Get itinerary

Requirements: 3.2, 4.2
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Path, Body
from pydantic import BaseModel, Field

from app.event_planning.services.itinerary_manager import (
    ItineraryItemNotFoundError,
    SessionFinalizedError,
)
from app.event_planning.services.planning_session_service import (
    SessionNotFoundError,
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/planning-sessions", tags=["itinerary"])

# Import shared service instances
from ..services.group_coordination import (
    itinerary_manager as _itinerary_manager,
    session_service as _session_service,
)


# Request/Response Models

class AddToItineraryRequest(BaseModel):
    """Request model for adding an item to the itinerary."""
    venue_id: str = Field(..., description="ID of the venue to add")
    scheduled_time: str = Field(..., description="ISO format datetime for when venue is scheduled")
    added_by: str = Field(..., description="ID of the participant adding the item")


class ItineraryItemResponse(BaseModel):
    """Response model for itinerary item details."""
    id: str
    session_id: str
    venue_id: str
    scheduled_time: str
    added_at: str
    added_by: str
    order: int


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str
    error_code: str
    details: Optional[dict] = None


# Endpoints

@router.post(
    "/{session_id}/itinerary",
    response_model=ItineraryItemResponse,
    status_code=201,
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
        400: {"model": ErrorResponse, "description": "Session finalized or invalid datetime"},
        500: {"model": ErrorResponse, "description": "Failed to add to itinerary"},
    },
)
async def add_to_itinerary(
    session_id: str = Path(..., description="Planning session ID"),
    request: AddToItineraryRequest = Body(...),
) -> ItineraryItemResponse:
    """
    Add a venue to the itinerary.
    
    Adds the venue with the scheduled time and maintains chronological order.
    The itinerary is automatically sorted by scheduled_time.
    
    Args:
        session_id: ID of the planning session
        request: Itinerary item details including venue ID and scheduled time
    
    Returns:
        ItineraryItemResponse with item details
    
    Raises:
        HTTPException: 404 if session not found, 400 if finalized or invalid,
                      500 on other errors
    
    Requirements:
    - 4.2: Add venue and notify all participants
    """
    try:
        logger.info(
            f"Adding to itinerary: session={session_id}, "
            f"venue={request.venue_id}, time={request.scheduled_time}"
        )
        
        # Verify session exists and set status
        try:
            session = _session_service.get_session(session_id)
            _itinerary_manager.set_session_status(session_id, session.status)
        except SessionNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        # Parse scheduled time
        try:
            scheduled_time = datetime.fromisoformat(request.scheduled_time)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid datetime format: {request.scheduled_time}. "
                       f"Use ISO format (e.g., 2024-01-15T14:30:00)"
            )
        
        item = _itinerary_manager.add_to_itinerary(
            session_id=session_id,
            venue_id=request.venue_id,
            scheduled_time=scheduled_time,
            added_by=request.added_by,
        )
        
        logger.info(f"Added to itinerary: {item.id}")
        
        return ItineraryItemResponse(
            id=item.id,
            session_id=item.session_id,
            venue_id=item.venue_id,
            scheduled_time=item.scheduled_time.isoformat(),
            added_at=item.added_at.isoformat(),
            added_by=item.added_by,
            order=item.order,
        )
        
    except SessionFinalizedError as e:
        logger.warning(f"Session finalized: {session_id}")
        raise HTTPException(
            status_code=400,
            detail="This session has been finalized and cannot be modified"
        )
    except Exception as e:
        logger.error(
            f"Failed to add to itinerary: session={session_id}, "
            f"{type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add to itinerary: {str(e)}"
        )


@router.delete(
    "/{session_id}/itinerary/{item_id}",
    status_code=204,
    responses={
        404: {"model": ErrorResponse, "description": "Session or item not found"},
        400: {"model": ErrorResponse, "description": "Session finalized"},
        500: {"model": ErrorResponse, "description": "Failed to remove from itinerary"},
    },
)
async def remove_from_itinerary(
    session_id: str = Path(..., description="Planning session ID"),
    item_id: str = Path(..., description="Itinerary item ID"),
) -> None:
    """
    Remove an item from the itinerary.
    
    Removes the item and updates the order of remaining items to maintain
    chronological consistency.
    
    Args:
        session_id: ID of the planning session
        item_id: ID of the itinerary item to remove
    
    Returns:
        None: 204 No Content on success
    
    Raises:
        HTTPException: 404 if session/item not found, 400 if finalized,
                      500 on other errors
    
    Requirements:
    - 3.3: Update all participant views and maintain consistency
    """
    try:
        logger.info(
            f"Removing from itinerary: session={session_id}, item={item_id}"
        )
        
        # Verify session exists and set status
        try:
            session = _session_service.get_session(session_id)
            _itinerary_manager.set_session_status(session_id, session.status)
        except SessionNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        _itinerary_manager.remove_from_itinerary(
            session_id=session_id,
            item_id=item_id,
        )
        
        logger.info(f"Removed from itinerary: {item_id}")
        # Return 204 No Content
        
    except ItineraryItemNotFoundError as e:
        logger.warning(f"Itinerary item not found: {item_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Itinerary item {item_id} not found in session {session_id}"
        )
    except SessionFinalizedError as e:
        logger.warning(f"Session finalized: {session_id}")
        raise HTTPException(
            status_code=400,
            detail="This session has been finalized and cannot be modified"
        )
    except Exception as e:
        logger.error(
            f"Failed to remove from itinerary: session={session_id}, "
            f"item={item_id}, {type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove from itinerary: {str(e)}"
        )


@router.get(
    "/{session_id}/itinerary",
    response_model=list[ItineraryItemResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
        500: {"model": ErrorResponse, "description": "Failed to retrieve itinerary"},
    },
)
async def get_itinerary(
    session_id: str = Path(..., description="Planning session ID"),
) -> list[ItineraryItemResponse]:
    """
    Get the full itinerary sorted chronologically.
    
    Returns all itinerary items sorted by scheduled_time in ascending order.
    
    Args:
        session_id: ID of the planning session
    
    Returns:
        List of ItineraryItemResponse sorted by scheduled_time
    
    Raises:
        HTTPException: 404 if session not found, 500 on other errors
    
    Requirements:
    - 3.2: Display venues in chronological order with time, location, and vote results
    """
    try:
        logger.info(f"Retrieving itinerary: session={session_id}")
        
        # Verify session exists
        try:
            _session_service.get_session(session_id)
        except SessionNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        # Get itinerary (already sorted chronologically)
        items = _itinerary_manager.get_itinerary(session_id)
        
        result = [
            ItineraryItemResponse(
                id=item.id,
                session_id=item.session_id,
                venue_id=item.venue_id,
                scheduled_time=item.scheduled_time.isoformat(),
                added_at=item.added_at.isoformat(),
                added_by=item.added_by,
                order=item.order,
            )
            for item in items
        ]
        
        logger.info(f"Retrieved {len(result)} itinerary items")
        
        return result
        
    except Exception as e:
        logger.error(
            f"Failed to retrieve itinerary for session {session_id}: "
            f"{type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve itinerary: {str(e)}"
        )
