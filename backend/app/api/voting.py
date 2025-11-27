"""Voting API endpoints for group coordination.

This module provides REST API endpoints for venue voting:
- POST /api/planning-sessions/{session_id}/venues - Add venue option
- POST /api/planning-sessions/{session_id}/venues/{venue_id}/vote - Cast vote
- GET /api/planning-sessions/{session_id}/venues - Get venues with votes

Requirements: 2.1, 2.2
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Path, Body
from pydantic import BaseModel, Field

from app.event_planning.models.venue import VoteType
from app.event_planning.services.vote_manager import (
    VenueNotFoundError,
    SessionFinalizedError,
)
from app.event_planning.services.planning_session_service import (
    SessionNotFoundError,
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/planning-sessions", tags=["voting"])

# Import shared service instances
from ..services.group_coordination import (
    vote_manager as _vote_manager,
    session_service as _session_service,
)


# Request/Response Models

class AddVenueRequest(BaseModel):
    """Request model for adding a venue option."""
    place_id: str = Field(..., description="Google Places ID")
    name: str = Field(..., min_length=1, max_length=200, description="Venue name")
    address: str = Field(..., min_length=1, description="Venue address")
    suggested_by: str = Field(..., description="'agent' or participant ID")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Venue rating (0-5)")
    price_level: Optional[int] = Field(None, ge=0, le=4, description="Price level (0-4)")
    photo_url: Optional[str] = Field(None, description="Photo URL")


class VenueResponse(BaseModel):
    """Response model for venue details."""
    id: str
    session_id: str
    place_id: str
    name: str
    address: str
    rating: Optional[float]
    price_level: Optional[int]
    photo_url: Optional[str]
    suggested_at: str
    suggested_by: str


class CastVoteRequest(BaseModel):
    """Request model for casting a vote."""
    participant_id: str = Field(..., description="ID of the participant voting")
    vote_type: str = Field(..., description="Vote type: UPVOTE, DOWNVOTE, or NEUTRAL")


class VoteResponse(BaseModel):
    """Response model for vote details."""
    id: str
    session_id: str
    venue_id: str
    participant_id: str
    vote_type: str
    created_at: str
    updated_at: str


class VoteTallyResponse(BaseModel):
    """Response model for vote tally."""
    venue_id: str
    upvotes: int
    downvotes: int
    neutral: int
    voters: list[str]
    net_score: int
    total_votes: int


class VenueWithVotesResponse(BaseModel):
    """Response model for venue with vote information."""
    venue: VenueResponse
    tally: VoteTallyResponse


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str
    error_code: str
    details: Optional[dict] = None


# Endpoints

@router.post(
    "/{session_id}/venues",
    response_model=VenueResponse,
    status_code=201,
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
        400: {"model": ErrorResponse, "description": "Session finalized"},
        500: {"model": ErrorResponse, "description": "Failed to add venue"},
    },
)
async def add_venue_option(
    session_id: str = Path(..., description="Planning session ID"),
    request: AddVenueRequest = Body(...),
) -> VenueResponse:
    """
    Add a venue option for voting.
    
    Stores the venue with Google Places data. The venue can be suggested
    by the agent or by a participant.
    
    Args:
        session_id: ID of the planning session
        request: Venue details including Google Places data
    
    Returns:
        VenueResponse with venue details
    
    Raises:
        HTTPException: 404 if session not found, 400 if finalized,
                      500 on other errors
    
    Requirements:
    - 2.1: Display venue as votable card with venue details
    """
    try:
        logger.info(
            f"Adding venue option: session={session_id}, "
            f"name={request.name}, suggested_by={request.suggested_by}"
        )
        
        # Verify session exists
        try:
            session = _session_service.get_session(session_id)
            _vote_manager.set_session_status(session_id, session.status)
        except SessionNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        venue = _vote_manager.add_venue_option(
            session_id=session_id,
            place_id=request.place_id,
            name=request.name,
            address=request.address,
            suggested_by=request.suggested_by,
            rating=request.rating,
            price_level=request.price_level,
            photo_url=request.photo_url,
        )
        
        logger.info(f"Venue added: {venue.id}")
        
        return VenueResponse(
            id=venue.id,
            session_id=venue.session_id,
            place_id=venue.place_id,
            name=venue.name,
            address=venue.address,
            rating=venue.rating,
            price_level=venue.price_level,
            photo_url=venue.photo_url,
            suggested_at=venue.suggested_at.isoformat(),
            suggested_by=venue.suggested_by,
        )
        
    except SessionFinalizedError as e:
        logger.warning(f"Session finalized: {session_id}")
        raise HTTPException(
            status_code=400,
            detail="This session has been finalized and cannot be modified"
        )
    except Exception as e:
        logger.error(
            f"Failed to add venue to session {session_id}: "
            f"{type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add venue: {str(e)}"
        )


@router.post(
    "/{session_id}/venues/{venue_id}/vote",
    response_model=VoteResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Session or venue not found"},
        400: {"model": ErrorResponse, "description": "Session finalized or invalid vote type"},
        500: {"model": ErrorResponse, "description": "Failed to cast vote"},
    },
)
async def cast_vote(
    session_id: str = Path(..., description="Planning session ID"),
    venue_id: str = Path(..., description="Venue ID"),
    request: CastVoteRequest = Body(...),
) -> VoteResponse:
    """
    Cast or update a vote on a venue.
    
    If the participant has already voted on this venue, their vote is updated.
    Otherwise, a new vote is created. This prevents duplicate votes.
    
    Args:
        session_id: ID of the planning session
        venue_id: ID of the venue to vote on
        request: Vote details including participant ID and vote type
    
    Returns:
        VoteResponse with vote details
    
    Raises:
        HTTPException: 404 if session/venue not found, 400 if finalized or invalid,
                      500 on other errors
    
    Requirements:
    - 2.2: Record vote and update tally immediately
    """
    try:
        logger.info(
            f"Casting vote: session={session_id}, venue={venue_id}, "
            f"participant={request.participant_id}, type={request.vote_type}"
        )
        
        # Verify session exists and set status
        try:
            session = _session_service.get_session(session_id)
            _vote_manager.set_session_status(session_id, session.status)
        except SessionNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        # Parse vote type
        try:
            vote_type = VoteType[request.vote_type.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid vote type: {request.vote_type}. "
                       f"Must be UPVOTE, DOWNVOTE, or NEUTRAL"
            )
        
        vote = _vote_manager.cast_vote(
            session_id=session_id,
            venue_id=venue_id,
            participant_id=request.participant_id,
            vote_type=vote_type,
        )
        
        logger.info(f"Vote cast: {vote.id}")
        
        return VoteResponse(
            id=vote.id,
            session_id=vote.session_id,
            venue_id=vote.venue_id,
            participant_id=vote.participant_id,
            vote_type=vote.vote_type.value,
            created_at=vote.created_at.isoformat(),
            updated_at=vote.updated_at.isoformat(),
        )
        
    except VenueNotFoundError as e:
        logger.warning(f"Venue not found: {venue_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Venue {venue_id} not found in session {session_id}"
        )
    except SessionFinalizedError as e:
        logger.warning(f"Session finalized: {session_id}")
        raise HTTPException(
            status_code=400,
            detail="This session has been finalized and cannot be modified"
        )
    except Exception as e:
        logger.error(
            f"Failed to cast vote: session={session_id}, venue={venue_id}, "
            f"{type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cast vote: {str(e)}"
        )


@router.get(
    "/{session_id}/venues",
    response_model=list[VenueWithVotesResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
        500: {"model": ErrorResponse, "description": "Failed to retrieve venues"},
    },
)
async def get_venues_with_votes(
    session_id: str = Path(..., description="Planning session ID"),
) -> list[VenueWithVotesResponse]:
    """
    Get all venue options with their vote tallies.
    
    Returns all venues for the session along with current vote counts
    and the list of participants who voted.
    
    Args:
        session_id: ID of the planning session
    
    Returns:
        List of VenueWithVotesResponse containing venue details and vote tallies
    
    Raises:
        HTTPException: 404 if session not found, 500 on other errors
    
    Requirements:
    - 2.1: Display venues as votable cards
    - 2.4: Show vote count and which participants voted
    """
    try:
        logger.info(f"Retrieving venues with votes: session={session_id}")
        
        # Verify session exists
        try:
            _session_service.get_session(session_id)
        except SessionNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        # Get all venues
        venues = _vote_manager.get_venues(session_id)
        
        # Build response with vote tallies
        result = []
        for venue in venues:
            tally = _vote_manager.get_votes(session_id, venue.id)
            
            result.append(VenueWithVotesResponse(
                venue=VenueResponse(
                    id=venue.id,
                    session_id=venue.session_id,
                    place_id=venue.place_id,
                    name=venue.name,
                    address=venue.address,
                    rating=venue.rating,
                    price_level=venue.price_level,
                    photo_url=venue.photo_url,
                    suggested_at=venue.suggested_at.isoformat(),
                    suggested_by=venue.suggested_by,
                ),
                tally=VoteTallyResponse(
                    venue_id=tally.venue_id,
                    upvotes=tally.upvotes,
                    downvotes=tally.downvotes,
                    neutral=tally.neutral,
                    voters=tally.voters,
                    net_score=tally.net_score,
                    total_votes=tally.total_votes,
                ),
            ))
        
        logger.info(f"Retrieved {len(result)} venues with votes")
        
        return result
        
    except Exception as e:
        logger.error(
            f"Failed to retrieve venues for session {session_id}: "
            f"{type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve venues: {str(e)}"
        )
