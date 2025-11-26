"""Friend group repository implementation."""

from typing import Dict, List
from backend.app.event_planning.models.group import FriendGroup
from backend.app.event_planning.repositories.base import JsonFileRepository
from backend.app.event_planning.exceptions import (
    GroupNotFoundError,
    AlreadyMemberError,
    NotMemberError,
)
from backend.app.event_planning.error_logging import log_business_logic_error


class GroupRepository(JsonFileRepository[FriendGroup]):
    """Repository for FriendGroup entities."""
    
    def __init__(self, storage_dir: str = "data"):
        """Initialize the group repository."""
        super().__init__(storage_dir, "groups")
    
    def _dict_to_entity(self, data: Dict) -> FriendGroup:
        """Convert dictionary to FriendGroup entity."""
        return FriendGroup.from_dict(data)
    
    def get_groups_for_user(self, user_id: str) -> List[FriendGroup]:
        """Get all groups where the user is a member."""
        groups = []
        for group in self.list_all():
            if user_id in group.member_ids:
                groups.append(group)
        return groups
    
    def add_member(self, group_id: str, user_id: str) -> FriendGroup:
        """Add a member to a group."""
        group = self.get(group_id)
        if not group:
            error = GroupNotFoundError(group_id)
            log_business_logic_error(error, "add_member", {"group_id": group_id, "user_id": user_id})
            raise error
        
        if user_id in group.member_ids:
            error = AlreadyMemberError(user_id, group_id)
            log_business_logic_error(error, "add_member", {"group_id": group_id, "user_id": user_id})
            raise error
        
        group.member_ids.append(user_id)
        return self.update(group)
    
    def remove_member(self, group_id: str, user_id: str) -> FriendGroup:
        """Remove a member from a group."""
        group = self.get(group_id)
        if not group:
            error = GroupNotFoundError(group_id)
            log_business_logic_error(error, "remove_member", {"group_id": group_id, "user_id": user_id})
            raise error
        
        if user_id not in group.member_ids:
            error = NotMemberError(user_id, group_id)
            log_business_logic_error(error, "remove_member", {"group_id": group_id, "user_id": user_id})
            raise error
        
        group.member_ids.remove(user_id)
        
        # Also remove from priority members if present
        if user_id in group.priority_member_ids:
            group.priority_member_ids.remove(user_id)
        
        return self.update(group)
