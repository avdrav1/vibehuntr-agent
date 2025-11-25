"""Friend group data model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List
import json


@dataclass
class FriendGroup:
    """Represents a friend group."""
    
    id: str
    name: str
    member_ids: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    priority_member_ids: List[str] = field(default_factory=list)
    
    def validate(self) -> None:
        """Validate the friend group data."""
        if not self.id:
            raise ValueError("id cannot be empty")
        if not self.name:
            raise ValueError("name cannot be empty")
        if not self.member_ids:
            raise ValueError("member_ids cannot be empty")
        if len(self.member_ids) != len(set(self.member_ids)):
            raise ValueError("member_ids must be unique")
        for priority_id in self.priority_member_ids:
            if priority_id not in self.member_ids:
                raise ValueError(f"priority member {priority_id} must be in member_ids")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "member_ids": self.member_ids,
            "created_at": self.created_at.isoformat(),
            "priority_member_ids": self.priority_member_ids,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "FriendGroup":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            member_ids=data["member_ids"],
            created_at=datetime.fromisoformat(data["created_at"]),
            priority_member_ids=data.get("priority_member_ids", []),
        )
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "FriendGroup":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))
