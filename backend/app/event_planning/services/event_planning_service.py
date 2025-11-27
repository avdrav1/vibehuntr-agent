"""Event planning service layer.

This service orchestrates all components to provide high-level workflows
for event planning operations.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from uuid import uuid4

from ..models.user import User, PreferenceProfile, AvailabilityWindow
from ..models.group import FriendGroup
from ..models.event import Event
from ..models.suggestion import EventSuggestion
from ..models.feedback import EventFeedback
from ..repositories.user_repository import UserRepository
from ..repositories.group_repository import GroupRepository
from ..repositories.event_repository import EventRepository
from ..repositories.feedback_repository import FeedbackRepository
from ..services.event_service import EventService
from ..services.recommendation_engine import RecommendationEngine, SearchFilters
from ..services.scheduling_optimizer import SchedulingOptimizer, TimeSlot
from ..services.feedback_processor import FeedbackProcessor


class EventPlanningService:
    """
    High-level service that orchestrates all event planning components.
    
    This service provides complete workflows for common operations like
    creating groups, planning events, and managing feedback.
    """
    
    def __init__(
        self,
        user_repository: UserRepository,
        group_repository: GroupRepository,
        event_repository: EventRepository,
        feedback_repository: FeedbackRepository,
        storage_dir: str = "data"
    ):
        """
        Initialize the event planning service.
        
        Args:
            user_repository: Repository for user data
            group_repository: Repository for group data
            event_repository: Repository for event data
            feedback_repository: Repository for feedback data
            storage_dir: Directory for data storage
        """
        self.user_repo = user_repository
        self.group_repo = group_repository
        self.event_repo = event_repository
        self.feedback_repo = feedback_repository
        
        # Initialize component services
        self.event_service = EventService(event_repository, user_repository)
        self.recommendation_engine = RecommendationEngine()
        self.scheduling_optimizer = SchedulingOptimizer()
        self.feedback_processor = FeedbackProcessor(
            feedback_repository,
            event_repository,
            user_repository
        )
    
    # User Management Workflows
    
    def create_user(
        self,
        name: str,
        email: str,
        user_id: Optional[str] = None
    ) -> User:
        """
        Create a new user with default preferences.
        
        Args:
            name: User's name
            email: User's email address
            user_id: Optional user ID (generated if not provided)
        
        Returns:
            The created user
        
        Raises:
            ValueError: If validation fails or email already exists
        """
        # Check if email already exists
        existing_user = self.user_repo.get_by_email(email)
        if existing_user:
            raise ValueError(f"User with email {email} already exists")
        
        # Generate ID if not provided
        if user_id is None:
            user_id = str(uuid4())
        
        # Create user with default preference profile
        user = User(
            id=user_id,
            name=name,
            email=email,
            preference_profile=PreferenceProfile(user_id=user_id),
            availability_windows=[]
        )
        
        user.validate()
        return self.user_repo.create(user)
    
    def update_user_preferences(
        self,
        user_id: str,
        activity_preferences: Optional[dict] = None,
        budget_max: Optional[float] = None,
        location_preferences: Optional[List[str]] = None,
        dietary_restrictions: Optional[List[str]] = None,
        accessibility_needs: Optional[List[str]] = None
    ) -> User:
        """
        Update a user's preference profile.
        
        Args:
            user_id: ID of the user
            activity_preferences: Optional activity type preferences
            budget_max: Optional maximum budget
            location_preferences: Optional location preferences
            dietary_restrictions: Optional dietary restrictions
            accessibility_needs: Optional accessibility needs
        
        Returns:
            The updated user
        
        Raises:
            ValueError: If user doesn't exist or validation fails
        """
        user = self.user_repo.get(user_id)
        if not user:
            raise ValueError(f"User with id {user_id} does not exist")
        
        # Update preference profile fields
        profile = user.preference_profile
        
        if activity_preferences is not None:
            profile.activity_preferences = activity_preferences
        if budget_max is not None:
            profile.budget_max = budget_max
        if location_preferences is not None:
            profile.location_preferences = location_preferences
        if dietary_restrictions is not None:
            profile.dietary_restrictions = dietary_restrictions
        if accessibility_needs is not None:
            profile.accessibility_needs = accessibility_needs
        
        profile.updated_at = datetime.now()
        
        return self.user_repo.update_preference_profile(user_id, profile)
    
    def add_user_availability(
        self,
        user_id: str,
        start_time: datetime,
        end_time: datetime,
        timezone: str = "UTC"
    ) -> User:
        """
        Add an availability window for a user.
        
        Args:
            user_id: ID of the user
            start_time: Start of availability window
            end_time: End of availability window
            timezone: Timezone for the window
        
        Returns:
            The updated user
        
        Raises:
            ValueError: If user doesn't exist or validation fails
        """
        window = AvailabilityWindow(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            timezone=timezone
        )
        
        return self.user_repo.add_availability_window(user_id, window)
    
    # Group Management Workflows
    
    def create_group(
        self,
        name: str,
        creator_id: str,
        member_ids: Optional[List[str]] = None,
        priority_member_ids: Optional[List[str]] = None,
        group_id: Optional[str] = None
    ) -> FriendGroup:
        """
        Create a new friend group.
        
        Args:
            name: Name of the group
            creator_id: ID of the user creating the group
            member_ids: Optional list of initial member IDs (creator is added automatically)
            priority_member_ids: Optional list of priority member IDs
            group_id: Optional group ID (generated if not provided)
        
        Returns:
            The created group
        
        Raises:
            ValueError: If validation fails or users don't exist
        """
        # Validate creator exists
        creator = self.user_repo.get(creator_id)
        if not creator:
            raise ValueError(f"Creator with id {creator_id} does not exist")
        
        # Initialize member list with creator
        members = [creator_id]
        if member_ids:
            # Validate all members exist
            for member_id in member_ids:
                if member_id != creator_id:  # Don't duplicate creator
                    user = self.user_repo.get(member_id)
                    if not user:
                        raise ValueError(f"User with id {member_id} does not exist")
                    members.append(member_id)
        
        # Generate ID if not provided
        if group_id is None:
            group_id = str(uuid4())
        
        # Create the group
        group = FriendGroup(
            id=group_id,
            name=name,
            member_ids=members,
            priority_member_ids=priority_member_ids or []
        )
        
        group.validate()
        return self.group_repo.create(group)
    
    def add_group_member(
        self,
        group_id: str,
        user_id: str
    ) -> FriendGroup:
        """
        Add a member to a group.
        
        Args:
            group_id: ID of the group
            user_id: ID of the user to add
        
        Returns:
            The updated group
        
        Raises:
            ValueError: If group or user doesn't exist
        """
        # Validate user exists
        user = self.user_repo.get(user_id)
        if not user:
            raise ValueError(f"User with id {user_id} does not exist")
        
        return self.group_repo.add_member(group_id, user_id)
    
    def remove_group_member(
        self,
        group_id: str,
        user_id: str
    ) -> FriendGroup:
        """
        Remove a member from a group.
        
        Args:
            group_id: ID of the group
            user_id: ID of the user to remove
        
        Returns:
            The updated group
        
        Raises:
            ValueError: If group doesn't exist or user is not a member
        """
        return self.group_repo.remove_member(group_id, user_id)
    
    def get_user_groups(self, user_id: str) -> List[FriendGroup]:
        """
        Get all groups where the user is a member.
        
        Args:
            user_id: ID of the user
        
        Returns:
            List of groups
        """
        return self.group_repo.get_groups_for_user(user_id)
    
    # Event Planning Workflows
    
    def plan_event(
        self,
        group_id: str,
        suggestions: List[EventSuggestion],
        filters: Optional[SearchFilters] = None,
        duration: Optional[timedelta] = None
    ) -> dict:
        """
        Complete event planning workflow: get suggestions, check availability, and provide options.
        
        This is a high-level workflow that:
        1. Gets all group members
        2. Generates ranked suggestions based on preferences
        3. Finds available time slots
        4. Returns comprehensive planning information
        
        Args:
            group_id: ID of the friend group
            suggestions: List of candidate suggestions to evaluate
            filters: Optional search filters
            duration: Optional event duration (uses suggestion duration if not provided)
        
        Returns:
            Dictionary containing:
            - group: The friend group
            - members: List of member users
            - suggestions: Ranked event suggestions
            - time_slots: Available time slots
            - members_without_availability: List of member IDs without availability
        
        Raises:
            ValueError: If group doesn't exist
        """
        # Get the group
        group = self.group_repo.get(group_id)
        if not group:
            raise ValueError(f"Group with id {group_id} does not exist")
        
        # Get all group members
        members = []
        for member_id in group.member_ids:
            user = self.user_repo.get(member_id)
            if user:
                members.append(user)
        
        if not members:
            raise ValueError(f"No valid members found for group {group_id}")
        
        # Generate and rank suggestions
        ranked_suggestions = self.recommendation_engine.generate_suggestions(
            group=group,
            users=members,
            suggestions=suggestions,
            filters=filters
        )
        
        # Find available time slots (use first suggestion's duration if not provided)
        event_duration = duration
        if event_duration is None and ranked_suggestions:
            event_duration = ranked_suggestions[0].estimated_duration
        
        time_slots = []
        if event_duration:
            time_slots = self.scheduling_optimizer.find_common_availability(
                users=members,
                duration=event_duration
            )
        
        # Identify members without availability
        members_without_availability = self.scheduling_optimizer.get_members_without_availability(members)
        
        return {
            "group": group,
            "members": members,
            "suggestions": ranked_suggestions,
            "time_slots": time_slots,
            "members_without_availability": members_without_availability
        }
    
    def create_event(
        self,
        suggestion_id: str,
        suggestions: List[EventSuggestion],
        event_name: str,
        start_time: datetime,
        participant_ids: List[str],
        event_id: Optional[str] = None
    ) -> Event:
        """
        Create an event from a suggestion.
        
        Args:
            suggestion_id: ID of the suggestion to use
            suggestions: List of available suggestions
            event_name: Name for the event
            start_time: Proposed start time
            participant_ids: List of participant user IDs
            event_id: Optional event ID (generated if not provided)
        
        Returns:
            The created event
        
        Raises:
            ValueError: If suggestion not found or validation fails
        """
        # Find the suggestion
        suggestion = None
        for s in suggestions:
            if s.id == suggestion_id:
                suggestion = s
                break
        
        if not suggestion:
            raise ValueError(f"Suggestion with id {suggestion_id} not found")
        
        # Generate ID if not provided
        if event_id is None:
            event_id = str(uuid4())
        
        # Create the event
        return self.event_service.create_event_from_suggestion(
            suggestion=suggestion,
            event_id=event_id,
            event_name=event_name,
            start_time=start_time,
            participant_ids=participant_ids
        )
    
    def finalize_event(self, event_id: str) -> Event:
        """
        Finalize a pending event.
        
        Args:
            event_id: ID of the event to finalize
        
        Returns:
            The finalized event
        
        Raises:
            ValueError: If event doesn't exist or is not pending
        """
        return self.event_service.finalize_event(event_id)
    
    def cancel_event(self, event_id: str) -> Event:
        """
        Cancel an event.
        
        Args:
            event_id: ID of the event to cancel
        
        Returns:
            The cancelled event
        
        Raises:
            ValueError: If event doesn't exist
        """
        return self.event_service.cancel_event(event_id)
    
    def get_event_details(self, event_id: str) -> Optional[Event]:
        """
        Get event details.
        
        Args:
            event_id: ID of the event
        
        Returns:
            The event if found, None otherwise
        """
        return self.event_service.get_event(event_id)
    
    def get_user_events(self, user_id: str) -> List[Event]:
        """
        Get all events for a user.
        
        Args:
            user_id: ID of the user
        
        Returns:
            List of events where the user is a participant
        """
        return self.event_service.list_events_for_user(user_id)
    
    # Scheduling and Conflict Resolution Workflows
    
    def check_event_conflicts(
        self,
        event_id: str
    ) -> dict:
        """
        Check for scheduling conflicts for an event.
        
        Args:
            event_id: ID of the event
        
        Returns:
            Dictionary containing:
            - event: The event
            - available_members: List of available member IDs
            - unavailable_members: List of unavailable member IDs
            - attendance_percentage: Percentage of members who can attend
            - alternative_times: List of alternative time slots
            - is_unresolvable: Whether conflicts cannot be fully resolved
            - resolution_options: List of suggested actions
        
        Raises:
            ValueError: If event doesn't exist
        """
        event = self.event_repo.get(event_id)
        if not event:
            raise ValueError(f"Event with id {event_id} does not exist")
        
        # Get all participants
        participants = []
        for participant_id in event.participant_ids:
            user = self.user_repo.get(participant_id)
            if user:
                participants.append(user)
        
        # Identify conflicts
        available, unavailable = self.scheduling_optimizer.identify_conflicts(
            event_start=event.start_time,
            event_end=event.end_time,
            users=participants
        )
        
        # Calculate attendance percentage
        attendance_percentage = self.scheduling_optimizer.calculate_attendance_percentage(
            event_start=event.start_time,
            event_end=event.end_time,
            users=participants
        )
        
        # Get alternative times
        alternative_times = self.scheduling_optimizer.suggest_alternative_times(
            event=event,
            users=participants
        )
        
        # Check if conflicts are unresolvable
        is_unresolvable, resolution_options = self.scheduling_optimizer.detect_unresolvable_conflicts(
            event=event,
            users=participants
        )
        
        return {
            "event": event,
            "available_members": available,
            "unavailable_members": unavailable,
            "attendance_percentage": attendance_percentage,
            "alternative_times": alternative_times,
            "is_unresolvable": is_unresolvable,
            "resolution_options": resolution_options
        }
    
    def find_optimal_time(
        self,
        group_id: str,
        duration: timedelta,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> List[TimeSlot]:
        """
        Find optimal time slots for a group event.
        
        Args:
            group_id: ID of the friend group
            duration: Required event duration
            date_range: Optional date range to search within
        
        Returns:
            List of time slots sorted by availability
        
        Raises:
            ValueError: If group doesn't exist
        """
        group = self.group_repo.get(group_id)
        if not group:
            raise ValueError(f"Group with id {group_id} does not exist")
        
        # Get all group members
        members = []
        for member_id in group.member_ids:
            user = self.user_repo.get(member_id)
            if user:
                members.append(user)
        
        # Find available time slots
        return self.scheduling_optimizer.find_common_availability(
            users=members,
            duration=duration,
            date_range=date_range
        )
    
    # Feedback Workflows
    
    def submit_event_feedback(
        self,
        event_id: str,
        user_id: str,
        rating: int,
        comments: Optional[str] = None,
        feedback_id: Optional[str] = None
    ) -> EventFeedback:
        """
        Submit feedback for an event.
        
        This automatically updates the user's preferences based on the feedback.
        
        Args:
            event_id: ID of the event
            user_id: ID of the user providing feedback
            rating: Rating from 1-5
            comments: Optional text comments
            feedback_id: Optional feedback ID (generated if not provided)
        
        Returns:
            The created feedback
        
        Raises:
            ValueError: If validation fails
        """
        # Generate ID if not provided
        if feedback_id is None:
            feedback_id = str(uuid4())
        
        return self.feedback_processor.submit_feedback(
            feedback_id=feedback_id,
            event_id=event_id,
            user_id=user_id,
            rating=rating,
            comments=comments
        )
    
    def get_event_feedback(self, event_id: str) -> List[EventFeedback]:
        """
        Get all feedback for an event.
        
        Args:
            event_id: ID of the event
        
        Returns:
            List of feedback for the event
        """
        return self.feedback_processor.get_feedback_for_event(event_id)
    
    def get_user_feedback_history(self, user_id: str) -> List[EventFeedback]:
        """
        Get all feedback submitted by a user.
        
        Args:
            user_id: ID of the user
        
        Returns:
            List of feedback submitted by the user
        """
        return self.feedback_processor.get_feedback_for_user(user_id)
    
    def get_group_feedback_patterns(self, group_id: str) -> dict:
        """
        Get historical feedback patterns for a group.
        
        Args:
            group_id: ID of the group
        
        Returns:
            Dictionary with feedback patterns
        
        Raises:
            ValueError: If group doesn't exist
        """
        group = self.group_repo.get(group_id)
        if not group:
            raise ValueError(f"Group with id {group_id} does not exist")
        
        return self.feedback_processor.get_historical_feedback_patterns(group.member_ids)
    
    # Search and Discovery Workflows
    
    def search_suggestions(
        self,
        group_id: str,
        suggestions: List[EventSuggestion],
        activity_keywords: Optional[List[str]] = None,
        location_area: Optional[str] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        budget_max: Optional[float] = None
    ) -> List[EventSuggestion]:
        """
        Search and filter event suggestions for a group.
        
        Args:
            group_id: ID of the friend group
            suggestions: List of candidate suggestions
            activity_keywords: Optional activity keywords to filter by
            location_area: Optional location to filter by
            date_range: Optional date range to filter by
            budget_max: Optional maximum budget to filter by
        
        Returns:
            Filtered and ranked list of suggestions
        
        Raises:
            ValueError: If group doesn't exist or filters are invalid
        """
        group = self.group_repo.get(group_id)
        if not group:
            raise ValueError(f"Group with id {group_id} does not exist")
        
        # Get all group members
        members = []
        for member_id in group.member_ids:
            user = self.user_repo.get(member_id)
            if user:
                members.append(user)
        
        # Create search filters
        filters = SearchFilters(
            activity_keywords=activity_keywords or [],
            location_area=location_area,
            date_range=date_range,
            budget_max=budget_max
        )
        
        filters.validate()
        
        # Generate and rank suggestions with filters
        return self.recommendation_engine.generate_suggestions(
            group=group,
            users=members,
            suggestions=suggestions,
            filters=filters
        )
