"""Planning session models for group coordination."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
import json


class SessionStatus(Enum):
    """Planning session status enumeration."""
    ACTIVE = "active"
    FINALIZED = "finalized"
    ARCHIVED = "archived"


@dataclass
class Participant:
    """Represents a participant in a planning session."""
    
    id: str
    session_id: str
    display_name: str
    joined_at: datetime
    is_organizer: bool = False
    
    def validate(self) -> None:
        """Validate the participant data."""
        if not self.id:
            raise ValueError("id cannot be empty")
        if not self.session_id:
            raise ValueError("session_id cannot be empty")
        if not self.display_name:
            raise ValueError("display_name cannot be empty")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "display_name": self.display_name,
            "joined_at": self.joined_at.isoformat(),
            "is_organizer": self.is_organizer,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Participant":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            session_id=data["session_id"],
            display_name=data["display_name"],
            joined_at=datetime.fromisoformat(data["joined_at"]),
            is_organizer=data.get("is_organizer", False),
        )


    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "Participant":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class PlanningSession:
    """Represents a collaborative planning session."""
    
    id: str
    name: str
    organizer_id: str
    invite_token: str
    invite_expires_at: datetime
    created_at: datetime
    updated_at: datetime
    invite_revoked: bool = False
    status: SessionStatus = SessionStatus.ACTIVE
    participant_ids: List[str] = field(default_factory=list)
    
    def validate(self) -> None:
        """Validate the planning session data."""
        if not self.id:
            raise ValueError("id cannot be empty")
        if not self.name:
            raise ValueError("name cannot be empty")
        if not self.organizer_id:
            raise ValueError("organizer_id cannot be empty")
        if not self.invite_token:
            raise ValueError("invite_token cannot be empty")
        if self.invite_expires_at <= self.created_at:
            raise ValueError("invite_expires_at must be after created_at")
    
    def is_invite_valid(self) -> bool:
        """Check if the invite link is still valid."""
        if self.invite_revoked:
            return False
        if datetime.now() > self.invite_expires_at:
            return False
        return True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "organizer_id": self.organizer_id,
            "invite_token": self.invite_token,
            "invite_expires_at": self.invite_expires_at.isoformat(),
            "invite_revoked": self.invite_revoked,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "participant_ids": self.participant_ids,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PlanningSession":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            organizer_id=data["organizer_id"],
            invite_token=data["invite_token"],
            invite_expires_at=datetime.fromisoformat(data["invite_expires_at"]),
            invite_revoked=data.get("invite_revoked", False),
            status=SessionStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            participant_ids=data.get("participant_ids", []),
        )
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "PlanningSession":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))
