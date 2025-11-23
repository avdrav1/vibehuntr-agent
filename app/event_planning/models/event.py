"""Event-related data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
import json


class EventStatus(Enum):
    """Event status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


@dataclass
class Location:
    """Represents a location."""
    
    name: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    def validate(self) -> None:
        """Validate the location data."""
        if not self.name:
            raise ValueError("name cannot be empty")
        if not self.address:
            raise ValueError("address cannot be empty")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Location":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            address=data["address"],
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
        )


@dataclass
class Event:
    """Represents an event."""
    
    id: str
    name: str
    activity_type: str
    location: Location
    start_time: datetime
    end_time: datetime
    participant_ids: List[str]
    status: EventStatus = EventStatus.PENDING
    budget_per_person: Optional[float] = None
    description: str = ""
    
    def validate(self) -> None:
        """Validate the event data."""
        if not self.id:
            raise ValueError("id cannot be empty")
        if not self.name:
            raise ValueError("name cannot be empty")
        if not self.activity_type:
            raise ValueError("activity_type cannot be empty")
        if not self.participant_ids:
            raise ValueError("participant_ids cannot be empty")
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        if self.budget_per_person is not None and self.budget_per_person < 0:
            raise ValueError("budget_per_person cannot be negative")
        
        self.location.validate()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "activity_type": self.activity_type,
            "location": self.location.to_dict(),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "participant_ids": self.participant_ids,
            "status": self.status.value,
            "budget_per_person": self.budget_per_person,
            "description": self.description,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Event":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            activity_type=data["activity_type"],
            location=Location.from_dict(data["location"]),
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]),
            participant_ids=data["participant_ids"],
            status=EventStatus(data["status"]),
            budget_per_person=data.get("budget_per_person"),
            description=data.get("description", ""),
        )
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "Event":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))
