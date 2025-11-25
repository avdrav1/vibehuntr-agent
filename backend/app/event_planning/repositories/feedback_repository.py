"""Feedback repository implementation."""

from typing import Dict, List
from app.event_planning.models.feedback import EventFeedback
from app.event_planning.repositories.base import JsonFileRepository


class FeedbackRepository(JsonFileRepository[EventFeedback]):
    """Repository for EventFeedback entities."""
    
    def __init__(self, storage_dir: str = "data"):
        """Initialize the feedback repository."""
        super().__init__(storage_dir, "feedback")
    
    def _dict_to_entity(self, data: Dict) -> EventFeedback:
        """Convert dictionary to EventFeedback entity."""
        return EventFeedback.from_dict(data)
    
    def get_feedback_for_event(self, event_id: str) -> List[EventFeedback]:
        """Get all feedback for a specific event."""
        feedback_list = []
        for feedback in self.list_all():
            if feedback.event_id == event_id:
                feedback_list.append(feedback)
        return feedback_list
    
    def get_feedback_for_user(self, user_id: str) -> List[EventFeedback]:
        """Get all feedback submitted by a specific user."""
        feedback_list = []
        for feedback in self.list_all():
            if feedback.user_id == user_id:
                feedback_list.append(feedback)
        return feedback_list
