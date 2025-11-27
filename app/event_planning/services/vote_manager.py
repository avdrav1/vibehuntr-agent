"""Vote manager service for group coordination.

This service handles voting on venue options including adding venues,
casting votes, and ranking venues by vote count.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from app.event_planning.models.venue import VenueOption, Vote, VoteType
from app.event_planning.models.planning_session import SessionStatus
from app.event_planning.exceptions import (
    BusinessLogicError,
    EntityNotFoundError,
)


class VenueNotFoundError(EntityNotFoundError):
    """Raised when a venue option is not found."""
    
    def __init__(self, venue_id: str):
        super().__init__("VenueOption", venue_id)
        self.error_code = "VENUE_NOT_FOUND"


class SessionFinalizedError(BusinessLogicError):
    """Raised when attempting to modify a finalized session."""
    
    def __init__(self, session_id: str):
        message = f"Planning session {session_id} has been finalized and cannot be modified"
        details = {"session_id": session_id}
        super().__init__(message, "SESSION_FINALIZED", details)


@dataclass
class VoteTally:
    """Represents the vote tally for a venue."""
    venue_id: str
    upvotes: int
    downvotes: int
    neutral: int
    voters: List[str]  # List of participant IDs who voted
    
    @property
    def net_score(self) -> int:
        """Calculate net score (upvotes - downvotes)."""
        return self.upvotes - self.downvotes
    
    @property
    def total_votes(self) -> int:
        """Total number of votes cast."""
        return self.upvotes + self.downvotes + self.neutral
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "venue_id": self.venue_id,
            "upvotes": self.upvotes,
            "downvotes": self.downvotes,
            "neutral": self.neutral,
            "voters": self.voters,
            "net_score": self.net_score,
            "total_votes": self.total_votes,
        }


@dataclass
class RankedVenue:
    """Represents a venue with its ranking information."""
    venue: VenueOption
    tally: VoteTally
    rank: int
    is_tied: bool = False


class VoteManager:
    """Service for managing venue voting with business logic."""
    
    def __init__(self, broadcast_service=None):
        """
        Initialize the vote manager with in-memory storage.
        
        Args:
            broadcast_service: Optional BroadcastService for real-time updates
        """
        # session_id -> {venue_id -> VenueOption}
        self._venues: Dict[str, Dict[str, VenueOption]] = {}
        # session_id -> {venue_id -> {participant_id -> Vote}}
        self._votes: Dict[str, Dict[str, Dict[str, Vote]]] = {}
        # session_id -> SessionStatus (for finalization checks)
        self._session_status: Dict[str, SessionStatus] = {}
        # Optional broadcast service for real-time updates
        self._broadcast_service = broadcast_service

    
    def set_session_status(self, session_id: str, status: SessionStatus) -> None:
        """Set the session status for finalization checks."""
        self._session_status[session_id] = status
    
    def _check_session_not_finalized(self, session_id: str) -> None:
        """Check if session is finalized and raise error if so."""
        status = self._session_status.get(session_id, SessionStatus.ACTIVE)
        if status == SessionStatus.FINALIZED:
            raise SessionFinalizedError(session_id)
    
    def add_venue_option(
        self,
        session_id: str,
        place_id: str,
        name: str,
        address: str,
        suggested_by: str,
        rating: Optional[float] = None,
        price_level: Optional[int] = None,
        photo_url: Optional[str] = None,
        venue_id: Optional[str] = None,
    ) -> VenueOption:
        """
        Add a venue option for voting.
        
        Stores venue with Google Places data.
        
        Args:
            session_id: ID of the planning session
            place_id: Google Places ID
            name: Venue name
            address: Venue address
            suggested_by: "agent" or participant_id
            rating: Optional venue rating (0-5)
            price_level: Optional price level (0-4)
            photo_url: Optional photo URL
            venue_id: Optional venue ID (generated if not provided)
        
        Returns:
            The created VenueOption
        
        Raises:
            SessionFinalizedError: If session is finalized
        
        Validates: Requirements 2.1
        """
        self._check_session_not_finalized(session_id)
        
        # Generate venue ID if not provided
        if venue_id is None:
            venue_id = str(uuid.uuid4())
        
        now = datetime.now()
        
        venue = VenueOption(
            id=venue_id,
            session_id=session_id,
            place_id=place_id,
            name=name,
            address=address,
            rating=rating,
            price_level=price_level,
            photo_url=photo_url,
            suggested_at=now,
            suggested_by=suggested_by,
        )
        
        venue.validate()
        
        # Initialize session storage if needed
        if session_id not in self._venues:
            self._venues[session_id] = {}
            self._votes[session_id] = {}
        
        # Store venue
        self._venues[session_id][venue_id] = venue
        self._votes[session_id][venue_id] = {}
        
        # Broadcast venue added event if broadcast service is available
        if self._broadcast_service is not None:
            import asyncio
            from app.event_planning.services.broadcast_service import SessionEvent, EventType
            event = SessionEvent(
                event_type=EventType.VENUE_ADDED,
                session_id=session_id,
                timestamp=now,
                data=venue.to_dict(),
                participant_id=suggested_by if suggested_by != "agent" else None,
            )
            # Run broadcast in background if in async context
            try:
                asyncio.create_task(self._broadcast_service.broadcast(session_id, event))
            except RuntimeError:
                # Not in async context, skip broadcast
                pass
        
        return venue
    
    def get_venue(self, session_id: str, venue_id: str) -> VenueOption:
        """
        Get a venue option by ID.
        
        Args:
            session_id: ID of the planning session
            venue_id: ID of the venue
        
        Returns:
            The VenueOption
        
        Raises:
            VenueNotFoundError: If venue doesn't exist
        """
        venues = self._venues.get(session_id, {})
        venue = venues.get(venue_id)
        if venue is None:
            raise VenueNotFoundError(venue_id)
        return venue
    
    def get_venues(self, session_id: str) -> List[VenueOption]:
        """
        Get all venue options for a session.
        
        Args:
            session_id: ID of the planning session
        
        Returns:
            List of VenueOptions
        """
        venues = self._venues.get(session_id, {})
        return list(venues.values())

    
    def cast_vote(
        self,
        session_id: str,
        venue_id: str,
        participant_id: str,
        vote_type: VoteType,
    ) -> Vote:
        """
        Cast or update a vote on a venue.
        
        Checks for existing vote by participant on venue and updates it
        if one exists, otherwise creates a new vote.
        
        Args:
            session_id: ID of the planning session
            venue_id: ID of the venue to vote on
            participant_id: ID of the participant casting the vote
            vote_type: Type of vote (UPVOTE, DOWNVOTE, NEUTRAL)
        
        Returns:
            The created or updated Vote
        
        Raises:
            SessionFinalizedError: If session is finalized
            VenueNotFoundError: If venue doesn't exist
        
        Validates: Requirements 2.2, 2.3, 2.5
        """
        self._check_session_not_finalized(session_id)
        
        # Verify venue exists
        self.get_venue(session_id, venue_id)
        
        now = datetime.now()
        
        # Check for existing vote by this participant on this venue
        venue_votes = self._votes.get(session_id, {}).get(venue_id, {})
        existing_vote = venue_votes.get(participant_id)
        
        if existing_vote is not None:
            # Update existing vote
            existing_vote.vote_type = vote_type
            existing_vote.updated_at = now
            return existing_vote
        else:
            # Create new vote
            vote_id = str(uuid.uuid4())
            vote = Vote(
                id=vote_id,
                session_id=session_id,
                venue_id=venue_id,
                participant_id=participant_id,
                vote_type=vote_type,
                created_at=now,
                updated_at=now,
            )
            
            vote.validate()
            
            # Store vote
            if session_id not in self._votes:
                self._votes[session_id] = {}
            if venue_id not in self._votes[session_id]:
                self._votes[session_id][venue_id] = {}
            
            self._votes[session_id][venue_id][participant_id] = vote
            
            # Broadcast vote cast event if broadcast service is available
            if self._broadcast_service is not None:
                import asyncio
                from app.event_planning.services.broadcast_service import SessionEvent, EventType
                tally = self.get_votes(session_id, venue_id)
                event = SessionEvent(
                    event_type=EventType.VOTE_CAST,
                    session_id=session_id,
                    timestamp=now,
                    data={
                        "vote": vote.to_dict(),
                        "tally": tally.to_dict(),
                    },
                    participant_id=participant_id,
                )
                # Run broadcast in background if in async context
                try:
                    asyncio.create_task(self._broadcast_service.broadcast(session_id, event))
                except RuntimeError:
                    # Not in async context, skip broadcast
                    pass
            
            return vote
    
    def get_votes(self, session_id: str, venue_id: str) -> VoteTally:
        """
        Get vote tally for a venue.
        
        Args:
            session_id: ID of the planning session
            venue_id: ID of the venue
        
        Returns:
            VoteTally with counts and voter list
        
        Raises:
            VenueNotFoundError: If venue doesn't exist
        
        Validates: Requirements 2.2, 2.4
        """
        # Verify venue exists
        self.get_venue(session_id, venue_id)
        
        venue_votes = self._votes.get(session_id, {}).get(venue_id, {})
        
        upvotes = 0
        downvotes = 0
        neutral = 0
        voters = []
        
        for participant_id, vote in venue_votes.items():
            voters.append(participant_id)
            if vote.vote_type == VoteType.UPVOTE:
                upvotes += 1
            elif vote.vote_type == VoteType.DOWNVOTE:
                downvotes += 1
            else:
                neutral += 1
        
        return VoteTally(
            venue_id=venue_id,
            upvotes=upvotes,
            downvotes=downvotes,
            neutral=neutral,
            voters=voters,
        )
    
    def get_participant_votes(
        self,
        session_id: str,
        participant_id: str
    ) -> List[Vote]:
        """
        Get all votes by a participant in a session.
        
        Args:
            session_id: ID of the planning session
            participant_id: ID of the participant
        
        Returns:
            List of Votes by the participant
        """
        votes = []
        session_votes = self._votes.get(session_id, {})
        
        for venue_id, venue_votes in session_votes.items():
            if participant_id in venue_votes:
                votes.append(venue_votes[participant_id])
        
        return votes

    
    def get_ranked_venues(self, session_id: str) -> List[RankedVenue]:
        """
        Get venues ranked by vote count.
        
        Sorts venues by net score (upvotes - downvotes) in descending order.
        Handles ties by marking tied venues.
        
        Args:
            session_id: ID of the planning session
        
        Returns:
            List of RankedVenue sorted by vote count descending
        
        Validates: Requirements 4.1, 4.4
        """
        venues = self.get_venues(session_id)
        
        if not venues:
            return []
        
        # Calculate tallies for all venues
        venue_tallies: List[tuple[VenueOption, VoteTally]] = []
        for venue in venues:
            tally = self.get_votes(session_id, venue.id)
            venue_tallies.append((venue, tally))
        
        # Sort by net score descending
        venue_tallies.sort(key=lambda x: x[1].net_score, reverse=True)
        
        # Assign ranks and detect ties
        ranked_venues: List[RankedVenue] = []
        current_rank = 1
        prev_score = None
        
        # First pass: assign ranks
        for i, (venue, tally) in enumerate(venue_tallies):
            if prev_score is not None and tally.net_score < prev_score:
                current_rank = i + 1
            
            ranked_venues.append(RankedVenue(
                venue=venue,
                tally=tally,
                rank=current_rank,
                is_tied=False,
            ))
            prev_score = tally.net_score
        
        # Second pass: mark ties
        # Group by rank and mark venues with same rank as tied
        rank_counts: Dict[int, int] = {}
        for rv in ranked_venues:
            rank_counts[rv.rank] = rank_counts.get(rv.rank, 0) + 1
        
        for rv in ranked_venues:
            if rank_counts[rv.rank] > 1:
                rv.is_tied = True
        
        return ranked_venues
