"""Venue and voting models for group coordination."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Optional
import json


class VoteType(Enum):
    """Vote type enumeration."""
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"
    NEUTRAL = "neutral"


@dataclass
class VenueOption:
    """Represents a venue option for voting."""
    
    id: str
    session_id: str
    place_id: str  # Google Places ID
    name: str
    address: str
    suggested_at: datetime
    suggested_by: str  # "agent" or participant_id
    rating: Optional[float] = None
    price_level: Optional[int] = None
    photo_url: Optional[str] = None
    
    def validate(self) -> None:
        """Validate the venue option data."""
        if not self.id:
            raise ValueError("id cannot be empty")
        if not self.session_id:
            raise ValueError("session_id cannot be empty")
        if not self.place_id:
            raise ValueError("place_id cannot be empty")
        if not self.name:
            raise ValueError("name cannot be empty")
        if not self.address:
            raise ValueError("address cannot be empty")
        if not self.suggested_by:
            raise ValueError("suggested_by cannot be empty")
        if self.rating is not None and not (0 <= self.rating <= 5):
            raise ValueError("rating must be between 0 and 5")
        if self.price_level is not None and not (0 <= self.price_level <= 4):
            raise ValueError("price_level must be between 0 and 4")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "place_id": self.place_id,
            "name": self.name,
            "address": self.address,
            "rating": self.rating,
            "price_level": self.price_level,
            "photo_url": self.photo_url,
            "suggested_at": self.suggested_at.isoformat(),
            "suggested_by": self.suggested_by,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "VenueOption":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            session_id=data["session_id"],
            place_id=data["place_id"],
            name=data["name"],
            address=data["address"],
            rating=data.get("rating"),
            price_level=data.get("price_level"),
            photo_url=data.get("photo_url"),
            suggested_at=datetime.fromisoformat(data["suggested_at"]),
            suggested_by=data["suggested_by"],
        )
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "VenueOption":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class Vote:
    """Represents a vote on a venue option."""
    
    id: str
    session_id: str
    venue_id: str
    participant_id: str
    vote_type: VoteType
    created_at: datetime
    updated_at: datetime
    
    def validate(self) -> None:
        """Validate the vote data."""
        if not self.id:
            raise ValueError("id cannot be empty")
        if not self.session_id:
            raise ValueError("session_id cannot be empty")
        if not self.venue_id:
            raise ValueError("venue_id cannot be empty")
        if not self.participant_id:
            raise ValueError("participant_id cannot be empty")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "venue_id": self.venue_id,
            "participant_id": self.participant_id,
            "vote_type": self.vote_type.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Vote":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            session_id=data["session_id"],
            venue_id=data["venue_id"],
            participant_id=data["participant_id"],
            vote_type=VoteType(data["vote_type"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "Vote":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))
