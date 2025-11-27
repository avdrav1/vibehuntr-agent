"""Event repository implementation."""

from typing import Dict, List
from ..models.event import Event
from .base import JsonFileRepository


class EventRepository(JsonFileRepository[Event]):
    """Repository for Event entities."""
    
    def __init__(self, storage_dir: str = "data"):
        """Initialize the event repository."""
        super().__init__(storage_dir, "events")
    
    def _dict_to_entity(self, data: Dict) -> Event:
        """Convert dictionary to Event entity."""
        return Event.from_dict(data)
    
    def list_events_for_user(self, user_id: str) -> List[Event]:
        """Get all events where the user is a participant."""
        events = []
        for event in self.list_all():
            if user_id in event.participant_ids:
                events.append(event)
        return events
    
    def list_events_for_group(self, group_id: str, participant_ids: List[str]) -> List[Event]:
        """
        Get all events for a group.
        
        Args:
            group_id: The group identifier (for reference)
            participant_ids: List of user IDs in the group
        
        Returns:
            List of events where all participants are from the group
        """
        events = []
        for event in self.list_all():
            # Check if all event participants are in the group
            if all(pid in participant_ids for pid in event.participant_ids):
                events.append(event)
        return events
