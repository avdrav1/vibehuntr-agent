"""Event management service.

This service provides business logic for event creation, finalization,
cancellation, and validation.
"""

from datetime import datetime
from typing import List, Optional
from ..models.event import Event, EventStatus, Location
from ..models.suggestion import EventSuggestion
from ..models.user import User
from ..repositories.event_repository import EventRepository
from ..repositories.user_repository import UserRepository
from ..exceptions import (
    EventNotFoundError,
    InvalidEventDataError,
    InvalidEventStatusError,
    InsufficientAvailabilityError,
)
from ..error_logging import log_business_logic_error, log_validation_error


class EventService:
    """Service for managing events with business logic."""
    
    def __init__(
        self,
        event_repository: EventRepository,
        user_repository: UserRepository
    ):
        """
        Initialize the event service.
        
        Args:
            event_repository: Repository for event persistence
            user_repository: Repository for user data access
        """
        self.event_repo = event_repository
        self.user_repo = user_repository
    
    def create_event_from_suggestion(
        self,
        suggestion: EventSuggestion,
        event_id: str,
        event_name: str,
        start_time: datetime,
        participant_ids: List[str]
    ) -> Event:
        """
        Create an event from a suggestion with validation.
        
        Args:
            suggestion: The event suggestion to base the event on
            event_id: Unique identifier for the new event
            event_name: Name for the event
            start_time: Proposed start time for the event
            participant_ids: List of user IDs who will participate
        
        Returns:
            The created event with PENDING status
        
        Raises:
            ValueError: If validation fails
        
        Validates: Requirements 5.1
        """
        # Calculate end time based on suggestion's estimated duration
        end_time = start_time + suggestion.estimated_duration
        
        # Validate that at least one participant exists
        if not participant_ids:
            error = InvalidEventDataError(
                "Event must have at least one participant",
                field="participant_ids"
            )
            log_validation_error(error, "Event", {"event_id": event_id})
            raise error
        
        # Validate that the proposed time falls within at least one participant's availability
        if not self._validate_event_time(start_time, end_time, participant_ids):
            error = InsufficientAvailabilityError(
                "Event time must fall within at least one participant's availability window",
                details={
                    "event_id": event_id,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "participant_ids": participant_ids,
                }
            )
            log_business_logic_error(error, "create_event_from_suggestion", {"event_id": event_id})
            raise error
        
        # Create the event with PENDING status
        event = Event(
            id=event_id,
            name=event_name,
            activity_type=suggestion.activity_type,
            location=suggestion.location,
            start_time=start_time,
            end_time=end_time,
            participant_ids=participant_ids,
            status=EventStatus.PENDING,
            budget_per_person=suggestion.estimated_cost_per_person,
            description=suggestion.description,
        )
        
        # Validate and create the event
        event.validate()
        return self.event_repo.create(event)
    
    def finalize_event(self, event_id: str) -> Event:
        """
        Finalize a pending event by changing its status to CONFIRMED.
        
        Args:
            event_id: ID of the event to finalize
        
        Returns:
            The finalized event with CONFIRMED status
        
        Raises:
            ValueError: If event doesn't exist or is not in PENDING status
        
        Validates: Requirements 5.2
        """
        event = self.event_repo.get(event_id)
        
        if event is None:
            error = EventNotFoundError(event_id)
            log_business_logic_error(error, "finalize_event", {"event_id": event_id})
            raise error
        
        if event.status != EventStatus.PENDING:
            error = InvalidEventStatusError(
                f"Only PENDING events can be finalized. Current status: {event.status.value}",
                event_id,
                event.status.value,
                expected_status="PENDING"
            )
            log_business_logic_error(error, "finalize_event", {"event_id": event_id})
            raise error
        
        # Update status to CONFIRMED
        event.status = EventStatus.CONFIRMED
        return self.event_repo.update(event)
    
    def cancel_event(self, event_id: str) -> Event:
        """
        Cancel an event while preserving its record for historical reference.
        
        Args:
            event_id: ID of the event to cancel
        
        Returns:
            The cancelled event with CANCELLED status
        
        Raises:
            ValueError: If event doesn't exist or is already cancelled
        
        Validates: Requirements 5.5
        """
        event = self.event_repo.get(event_id)
        
        if event is None:
            error = EventNotFoundError(event_id)
            log_business_logic_error(error, "cancel_event", {"event_id": event_id})
            raise error
        
        if event.status == EventStatus.CANCELLED:
            error = InvalidEventStatusError(
                "Event is already cancelled",
                event_id,
                event.status.value
            )
            log_business_logic_error(error, "cancel_event", {"event_id": event_id})
            raise error
        
        # Update status to CANCELLED (preserves all other data)
        event.status = EventStatus.CANCELLED
        return self.event_repo.update(event)
    
    def _validate_event_time(
        self,
        start_time: datetime,
        end_time: datetime,
        participant_ids: List[str]
    ) -> bool:
        """
        Validate that the event time falls within at least one participant's availability.
        
        Args:
            start_time: Event start time
            end_time: Event end time
            participant_ids: List of participant user IDs
        
        Returns:
            True if at least one participant is available, False otherwise
        
        Validates: Requirements 5.3
        """
        for user_id in participant_ids:
            user = self.user_repo.get(user_id)
            if user is None:
                continue
            
            # Check if event time falls within any of the user's availability windows
            for window in user.availability_windows:
                # Simple overlap check (ignoring timezone for now)
                if window.start_time <= start_time and end_time <= window.end_time:
                    return True
        
        return False
    
    def get_event(self, event_id: str) -> Optional[Event]:
        """
        Get an event by ID.
        
        Args:
            event_id: ID of the event to retrieve
        
        Returns:
            The event if found, None otherwise
        """
        return self.event_repo.get(event_id)
    
    def list_events_for_user(self, user_id: str) -> List[Event]:
        """
        Get all events where the user is a participant.
        
        Args:
            user_id: ID of the user
        
        Returns:
            List of events where the user is a participant
        """
        return self.event_repo.list_events_for_user(user_id)
    
    def list_events_for_group(
        self,
        group_id: str,
        participant_ids: List[str]
    ) -> List[Event]:
        """
        Get all events for a group.
        
        Args:
            group_id: The group identifier
            participant_ids: List of user IDs in the group
        
        Returns:
            List of events for the group
        """
        return self.event_repo.list_events_for_group(group_id, participant_ids)
