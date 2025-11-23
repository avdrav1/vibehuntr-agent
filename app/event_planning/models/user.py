"""User-related data models."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional
import json


@dataclass
class AvailabilityWindow:
    """Represents a time period when a user is available."""
    
    user_id: str
    start_time: datetime
    end_time: datetime
    timezone: str
    
    def validate(self) -> None:
        """Validate the availability window."""
        if not self.user_id:
            raise ValueError("user_id cannot be empty")
        if not self.timezone:
            raise ValueError("timezone cannot be empty")
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "user_id": self.user_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "timezone": self.timezone,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "AvailabilityWindow":
        """Create from dictionary."""
        return cls(
            user_id=data["user_id"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]),
            timezone=data["timezone"],
        )


@dataclass
class PreferenceProfile:
    """User preferences for events."""
    
    user_id: str
    activity_preferences: Dict[str, float] = field(default_factory=dict)
    budget_max: Optional[float] = None
    location_preferences: List[str] = field(default_factory=list)
    dietary_restrictions: List[str] = field(default_factory=list)
    accessibility_needs: List[str] = field(default_factory=list)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def validate(self) -> None:
        """Validate the preference profile."""
        if not self.user_id:
            raise ValueError("user_id cannot be empty")
        if self.budget_max is not None and self.budget_max < 0:
            raise ValueError("budget_max cannot be negative")
        for activity, weight in self.activity_preferences.items():
            if not 0 <= weight <= 1:
                raise ValueError(f"activity preference weight must be between 0 and 1, got {weight}")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "user_id": self.user_id,
            "activity_preferences": self.activity_preferences,
            "budget_max": self.budget_max,
            "location_preferences": self.location_preferences,
            "dietary_restrictions": self.dietary_restrictions,
            "accessibility_needs": self.accessibility_needs,
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PreferenceProfile":
        """Create from dictionary."""
        return cls(
            user_id=data["user_id"],
            activity_preferences=data.get("activity_preferences", {}),
            budget_max=data.get("budget_max"),
            location_preferences=data.get("location_preferences", []),
            dietary_restrictions=data.get("dietary_restrictions", []),
            accessibility_needs=data.get("accessibility_needs", []),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


@dataclass
class User:
    """Represents a user in the system."""
    
    id: str
    name: str
    email: str
    preference_profile: PreferenceProfile
    availability_windows: List[AvailabilityWindow] = field(default_factory=list)
    
    def validate(self) -> None:
        """Validate the user data."""
        if not self.id:
            raise ValueError("id cannot be empty")
        if not self.name:
            raise ValueError("name cannot be empty")
        if not self.email:
            raise ValueError("email cannot be empty")
        if "@" not in self.email:
            raise ValueError("email must be valid")
        
        self.preference_profile.validate()
        for window in self.availability_windows:
            window.validate()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "preference_profile": self.preference_profile.to_dict(),
            "availability_windows": [w.to_dict() for w in self.availability_windows],
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "User":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            email=data["email"],
            preference_profile=PreferenceProfile.from_dict(data["preference_profile"]),
            availability_windows=[
                AvailabilityWindow.from_dict(w) for w in data.get("availability_windows", [])
            ],
        )
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "User":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))
