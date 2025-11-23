"""Event feedback data model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional
import json


@dataclass
class EventFeedback:
    """Represents feedback for an event."""
    
    id: str
    event_id: str
    user_id: str
    rating: int
    comments: Optional[str] = None
    submitted_at: datetime = field(default_factory=datetime.now)
    
    def validate(self) -> None:
        """Validate the feedback data."""
        if not self.id:
            raise ValueError("id cannot be empty")
        if not self.event_id:
            raise ValueError("event_id cannot be empty")
        if not self.user_id:
            raise ValueError("user_id cannot be empty")
        if not 1 <= self.rating <= 5:
            raise ValueError("rating must be between 1 and 5")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "user_id": self.user_id,
            "rating": self.rating,
            "comments": self.comments,
            "submitted_at": self.submitted_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "EventFeedback":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            event_id=data["event_id"],
            user_id=data["user_id"],
            rating=data["rating"],
            comments=data.get("comments"),
            submitted_at=datetime.fromisoformat(data["submitted_at"]),
        )
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "EventFeedback":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))
