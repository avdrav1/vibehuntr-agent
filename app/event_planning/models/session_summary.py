"""Session summary model for group coordination."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import json

from app.event_planning.models.planning_session import Participant
from app.event_planning.models.itinerary import ItineraryItem


@dataclass
class SessionSummary:
    """Represents a finalized session summary.
    
    Contains all information needed for the final summary including:
    - All venues with their times and addresses
    - All participants with their names
    - Shareable URL for the summary
    
    Validates: Requirements 4.5
    """
    
    session_id: str
    session_name: str
    finalized_at: datetime
    participants: List[Participant]
    itinerary: List[ItineraryItem]
    share_url: str
    
    def validate(self) -> None:
        """Validate the session summary data."""
        if not self.session_id:
            raise ValueError("session_id cannot be empty")
        if not self.session_name:
            raise ValueError("session_name cannot be empty")
        if not self.share_url:
            raise ValueError("share_url cannot be empty")
    
    def get_participant_names(self) -> List[str]:
        """Get list of all participant display names.
        
        Returns:
            List of participant display names
        
        Validates: Requirements 4.5
        """
        return [p.display_name for p in self.participants]
    
    def get_venue_ids(self) -> List[str]:
        """Get list of all venue IDs in the itinerary.
        
        Returns:
            List of venue IDs from itinerary items
        
        Validates: Requirements 4.5
        """
        return [item.venue_id for item in self.itinerary]
    
    def get_scheduled_times(self) -> List[datetime]:
        """Get list of all scheduled times in the itinerary.
        
        Returns:
            List of scheduled times from itinerary items
        
        Validates: Requirements 4.5
        """
        return [item.scheduled_time for item in self.itinerary]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "session_name": self.session_name,
            "finalized_at": self.finalized_at.isoformat(),
            "participants": [p.to_dict() for p in self.participants],
            "itinerary": [i.to_dict() for i in self.itinerary],
            "share_url": self.share_url,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SessionSummary":
        """Create from dictionary."""
        return cls(
            session_id=data["session_id"],
            session_name=data["session_name"],
            finalized_at=datetime.fromisoformat(data["finalized_at"]),
            participants=[Participant.from_dict(p) for p in data["participants"]],
            itinerary=[ItineraryItem.from_dict(i) for i in data["itinerary"]],
            share_url=data["share_url"],
        )
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "SessionSummary":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))
