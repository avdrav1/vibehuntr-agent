"""Itinerary and comment models for group coordination."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict
import json


# Maximum character limit for comments
COMMENT_MAX_LENGTH = 500


@dataclass
class ItineraryItem:
    """Represents an item in the planning session itinerary."""
    
    id: str
    session_id: str
    venue_id: str
    scheduled_time: datetime
    added_at: datetime
    added_by: str
    order: int
    
    def validate(self) -> None:
        """Validate the itinerary item data."""
        if not self.id:
            raise ValueError("id cannot be empty")
        if not self.session_id:
            raise ValueError("session_id cannot be empty")
        if not self.venue_id:
            raise ValueError("venue_id cannot be empty")
        if not self.added_by:
            raise ValueError("added_by cannot be empty")
        if self.order < 0:
            raise ValueError("order cannot be negative")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "venue_id": self.venue_id,
            "scheduled_time": self.scheduled_time.isoformat(),
            "added_at": self.added_at.isoformat(),
            "added_by": self.added_by,
            "order": self.order,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ItineraryItem":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            session_id=data["session_id"],
            venue_id=data["venue_id"],
            scheduled_time=datetime.fromisoformat(data["scheduled_time"]),
            added_at=datetime.fromisoformat(data["added_at"]),
            added_by=data["added_by"],
            order=data["order"],
        )
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "ItineraryItem":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class Comment:
    """Represents a comment on a venue option."""
    
    id: str
    session_id: str
    venue_id: str
    participant_id: str
    text: str
    created_at: datetime
    
    def validate(self) -> None:
        """Validate the comment data."""
        if not self.id:
            raise ValueError("id cannot be empty")
        if not self.session_id:
            raise ValueError("session_id cannot be empty")
        if not self.venue_id:
            raise ValueError("venue_id cannot be empty")
        if not self.participant_id:
            raise ValueError("participant_id cannot be empty")
        if not self.text:
            raise ValueError("text cannot be empty")
        if len(self.text) > COMMENT_MAX_LENGTH:
            raise ValueError(f"text exceeds maximum length of {COMMENT_MAX_LENGTH} characters")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "venue_id": self.venue_id,
            "participant_id": self.participant_id,
            "text": self.text,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Comment":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            session_id=data["session_id"],
            venue_id=data["venue_id"],
            participant_id=data["participant_id"],
            text=data["text"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "Comment":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))
