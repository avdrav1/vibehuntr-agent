"""Feedback processor for learning from user feedback.

This service processes user feedback on events and updates user preferences
to improve future recommendations.
"""

from typing import List, Optional
from datetime import datetime

from backend.app.event_planning.models.feedback import EventFeedback
from backend.app.event_planning.models.event import Event
from backend.app.event_planning.models.user import User, PreferenceProfile
from backend.app.event_planning.repositories.feedback_repository import FeedbackRepository
from backend.app.event_planning.repositories.event_repository import EventRepository
from backend.app.event_planning.repositories.user_repository import UserRepository
from backend.app.event_planning.exceptions import (
    EventNotFoundError,
    UserNotFoundError,
    NotParticipantError,
)
from backend.app.event_planning.error_logging import log_business_logic_error


class FeedbackProcessor:
    """
    Processes user feedback to improve recommendations.
    
    Uses exponential moving average to update preference weights based on
    positive and negative feedback.
    """
    
    def __init__(
        self,
        feedback_repository: FeedbackRepository,
        event_repository: EventRepository,
        user_repository: UserRepository,
        learning_rate: float = 0.1
    ):
        """
        Initialize the feedback processor.
        
        Args:
            feedback_repository: Repository for feedback persistence
            event_repository: Repository for event data access
            user_repository: Repository for user data access
            learning_rate: Learning rate for exponential moving average (default 0.1)
        """
        self.feedback_repo = feedback_repository
        self.event_repo = event_repository
        self.user_repo = user_repository
        self.learning_rate = learning_rate
    
    def submit_feedback(
        self,
        feedback_id: str,
        event_id: str,
        user_id: str,
        rating: int,
        comments: Optional[str] = None
    ) -> EventFeedback:
        """
        Submit feedback for an event with validation.
        
        Args:
            feedback_id: Unique identifier for the feedback
            event_id: ID of the event being rated
            user_id: ID of the user providing feedback
            rating: Rating from 1-5
            comments: Optional text comments
        
        Returns:
            The created feedback
        
        Raises:
            ValueError: If validation fails
        
        Validates: Requirements 6.1
        """
        # Validate that the event exists
        event = self.event_repo.get(event_id)
        if event is None:
            error = EventNotFoundError(event_id)
            log_business_logic_error(error, "submit_feedback", {"event_id": event_id, "user_id": user_id})
            raise error
        
        # Validate that the user exists
        user = self.user_repo.get(user_id)
        if user is None:
            error = UserNotFoundError(user_id)
            log_business_logic_error(error, "submit_feedback", {"event_id": event_id, "user_id": user_id})
            raise error
        
        # Validate that the user was a participant in the event
        if user_id not in event.participant_ids:
            error = NotParticipantError(user_id, event_id)
            log_business_logic_error(error, "submit_feedback", {"event_id": event_id, "user_id": user_id})
            raise error
        
        # Create the feedback
        feedback = EventFeedback(
            id=feedback_id,
            event_id=event_id,
            user_id=user_id,
            rating=rating,
            comments=comments,
            submitted_at=datetime.now()
        )
        
        # Validate and store the feedback
        feedback.validate()
        stored_feedback = self.feedback_repo.create(feedback)
        
        # Update user preferences based on the feedback
        self.update_preference_weights(user_id, feedback, event)
        
        return stored_feedback
    
    def update_preference_weights(
        self,
        user_id: str,
        feedback: EventFeedback,
        event: Event
    ) -> None:
        """
        Update user preference weights based on feedback using exponential moving average.
        
        The algorithm:
        - For positive feedback (rating >= 4): new_weight = old_weight * 0.9 + 0.1 * 1.0
        - For negative feedback (rating <= 2): new_weight = old_weight * 0.9 + 0.1 * 0.0
        - For neutral feedback (rating == 3): no change
        
        Args:
            user_id: ID of the user
            feedback: The feedback provided
            event: The event that was rated
        
        Validates: Requirements 6.3, 6.4
        """
        user = self.user_repo.get(user_id)
        if user is None:
            error = UserNotFoundError(user_id)
            log_business_logic_error(error, "update_preference_weights", {"user_id": user_id})
            raise error
        
        # Extract event characteristics
        activity_type = event.activity_type
        
        # Determine feedback direction
        if feedback.rating >= 4:
            # Positive feedback - increase weight
            target_value = 1.0
        elif feedback.rating <= 2:
            # Negative feedback - decrease weight
            target_value = 0.0
        else:
            # Neutral feedback - no change
            return
        
        # Get current preference profile
        profile = user.preference_profile
        
        # Get current weight for this activity type (default to 0.5 if not present)
        old_weight = profile.activity_preferences.get(activity_type, 0.5)
        
        # Apply exponential moving average
        new_weight = old_weight * (1 - self.learning_rate) + self.learning_rate * target_value
        
        # Ensure weight is in valid range [0, 1]
        new_weight = max(0.0, min(1.0, new_weight))
        
        # Update the preference profile
        profile.activity_preferences[activity_type] = new_weight
        profile.updated_at = datetime.now()
        
        # Save the updated profile
        self.user_repo.update_preference_profile(user_id, profile)
    
    def get_feedback_for_event(self, event_id: str) -> List[EventFeedback]:
        """
        Get all feedback for a specific event.
        
        Args:
            event_id: ID of the event
        
        Returns:
            List of feedback for the event
        
        Validates: Requirements 6.2
        """
        return self.feedback_repo.get_feedback_for_event(event_id)
    
    def get_feedback_for_user(self, user_id: str) -> List[EventFeedback]:
        """
        Get all feedback submitted by a specific user.
        
        Args:
            user_id: ID of the user
        
        Returns:
            List of feedback submitted by the user
        
        Validates: Requirements 6.2
        """
        return self.feedback_repo.get_feedback_for_user(user_id)
    
    def get_historical_feedback_patterns(
        self,
        user_ids: List[str]
    ) -> dict:
        """
        Get historical feedback patterns for a group of users.
        
        This analyzes all feedback from the users to identify patterns
        that can inform future recommendations.
        
        Args:
            user_ids: List of user IDs to analyze
        
        Returns:
            Dictionary with feedback patterns including:
            - activity_ratings: Average ratings by activity type
            - total_feedback_count: Total number of feedback entries
        
        Validates: Requirements 6.5
        """
        # Collect all feedback from these users
        all_feedback = []
        for user_id in user_ids:
            user_feedback = self.feedback_repo.get_feedback_for_user(user_id)
            all_feedback.extend(user_feedback)
        
        if not all_feedback:
            return {
                "activity_ratings": {},
                "total_feedback_count": 0
            }
        
        # Analyze feedback by activity type
        activity_ratings = {}
        activity_counts = {}
        
        for feedback in all_feedback:
            # Get the event to extract activity type
            event = self.event_repo.get(feedback.event_id)
            if event is None:
                continue
            
            activity_type = event.activity_type
            
            if activity_type not in activity_ratings:
                activity_ratings[activity_type] = 0.0
                activity_counts[activity_type] = 0
            
            activity_ratings[activity_type] += feedback.rating
            activity_counts[activity_type] += 1
        
        # Calculate average ratings
        for activity_type in activity_ratings:
            if activity_counts[activity_type] > 0:
                activity_ratings[activity_type] /= activity_counts[activity_type]
        
        return {
            "activity_ratings": activity_ratings,
            "total_feedback_count": len(all_feedback)
        }
