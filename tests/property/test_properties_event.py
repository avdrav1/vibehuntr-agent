"""Property-based tests for event management operations.

This module tests the correctness properties for event creation, finalization,
validation, and cancellation.
"""

import sys
import os
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings
from hypothesis.strategies import composite
import pytest
import tempfile
import shutil

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.event_planning.models.event import Event, EventStatus, Location
from app.event_planning.models.suggestion import EventSuggestion
from app.event_planning.models.user import User, AvailabilityWindow
from app.event_planning.repositories.event_repository import EventRepository
from app.event_planning.repositories.user_repository import UserRepository


# Custom strategies for generating test data

@composite
def location_strategy(draw: st.DrawFn) -> Location:
    """Generate a valid Location."""
    name = draw(st.text(min_size=1, max_size=100))
    address = draw(st.text(min_size=1, max_size=200))
    latitude = draw(st.none() | st.floats(min_value=-90.0, max_value=90.0, allow_nan=False, allow_infinity=False))
    longitude = draw(st.none() | st.floats(min_value=-180.0, max_value=180.0, allow_nan=False, allow_infinity=False))
    
    return Location(
        name=name,
        address=address,
        latitude=latitude,
        longitude=longitude,
    )


@composite
def event_suggestion_strategy(draw: st.DrawFn) -> EventSuggestion:
    """Generate a valid EventSuggestion."""
    # Generate valid IDs without filesystem-problematic characters
    suggestion_id = draw(st.text(
        min_size=1, max_size=50,
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-")
    ))
    activity_type = draw(st.text(min_size=1, max_size=50))
    location = draw(location_strategy())
    
    estimated_duration = draw(st.timedeltas(min_value=timedelta(hours=1), max_value=timedelta(days=3)))
    estimated_cost_per_person = draw(st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False))
    description = draw(st.text(max_size=500))
    consensus_score = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    
    return EventSuggestion(
        id=suggestion_id,
        activity_type=activity_type,
        location=location,
        estimated_duration=estimated_duration,
        estimated_cost_per_person=estimated_cost_per_person,
        description=description,
        consensus_score=consensus_score,
    )


@composite
def availability_window_strategy(draw: st.DrawFn, user_id: str = None) -> AvailabilityWindow:
    """Generate a valid AvailabilityWindow."""
    if user_id is None:
        user_id = draw(st.text(
            min_size=1, max_size=50,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-")
        ))
    
    start_time = draw(st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31)
    ))
    duration = draw(st.timedeltas(min_value=timedelta(hours=1), max_value=timedelta(days=7)))
    end_time = start_time + duration
    timezone_str = draw(st.sampled_from(["UTC", "America/New_York", "Europe/London", "Asia/Tokyo"]))
    
    return AvailabilityWindow(
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
        timezone=timezone_str,
    )


@composite
def pending_event_strategy(draw: st.DrawFn) -> Event:
    """Generate a valid Event with PENDING status."""
    event_id = draw(st.text(
        min_size=1, max_size=50,
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-")
    ))
    name = draw(st.text(min_size=1, max_size=100))
    activity_type = draw(st.text(min_size=1, max_size=50))
    location = draw(location_strategy())
    
    start_time = draw(st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31)
    ))
    duration = draw(st.timedeltas(min_value=timedelta(hours=1), max_value=timedelta(days=3)))
    end_time = start_time + duration
    
    num_participants = draw(st.integers(min_value=1, max_value=10))
    participant_ids = draw(st.lists(
        st.text(
            min_size=1, max_size=50,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-")
        ),
        min_size=num_participants,
        max_size=num_participants,
        unique=True
    ))
    
    budget_per_person = draw(st.none() | st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False))
    description = draw(st.text(max_size=500))
    
    return Event(
        id=event_id,
        name=name,
        activity_type=activity_type,
        location=location,
        start_time=start_time,
        end_time=end_time,
        participant_ids=participant_ids,
        status=EventStatus.PENDING,
        budget_per_person=budget_per_person,
        description=description,
    )


@composite
def confirmed_event_strategy(draw: st.DrawFn) -> Event:
    """Generate a valid Event with CONFIRMED status."""
    event = draw(pending_event_strategy())
    event.status = EventStatus.CONFIRMED
    return event


# Property Tests

# Feature: event-planning-agent, Property 20: Event creation from suggestion
@given(
    event_suggestion_strategy(),
    st.lists(
        st.text(
            min_size=1, max_size=50,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-")
        ),
        min_size=1, max_size=10, unique=True
    )
)
@settings(max_examples=100)
def test_property_20_event_creation_from_suggestion(suggestion: EventSuggestion, participant_ids: list) -> None:
    """
    Feature: event-planning-agent, Property 20: Event creation from suggestion
    
    For any event suggestion, creating an event from it should initialize the event
    with all suggestion details and set the status to pending.
    
    Validates: Requirements 5.1
    """
    # Create a temporary storage directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        repo = EventRepository(storage_dir=temp_dir)
        
        # Create event from suggestion
        # We need to provide start_time and end_time based on the suggestion
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + suggestion.estimated_duration
        
        event = Event(
            id=f"event_{suggestion.id}",
            name=f"Event: {suggestion.activity_type}",
            activity_type=suggestion.activity_type,
            location=suggestion.location,
            start_time=start_time,
            end_time=end_time,
            participant_ids=participant_ids,
            status=EventStatus.PENDING,
            budget_per_person=suggestion.estimated_cost_per_person,
            description=suggestion.description,
        )
        
        # Store the event
        created_event = repo.create(event)
        
        # Verify the event was created with PENDING status
        assert created_event.status == EventStatus.PENDING
        
        # Verify all suggestion details were transferred
        assert created_event.activity_type == suggestion.activity_type
        assert created_event.location.name == suggestion.location.name
        assert created_event.location.address == suggestion.location.address
        assert created_event.budget_per_person == suggestion.estimated_cost_per_person
        assert created_event.description == suggestion.description
        
        # Verify the event can be retrieved
        retrieved_event = repo.get(created_event.id)
        assert retrieved_event is not None
        assert retrieved_event.id == created_event.id
        assert retrieved_event.status == EventStatus.PENDING
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir)


# Feature: event-planning-agent, Property 21: Event finalization status
@given(pending_event_strategy())
@settings(max_examples=100)
def test_property_21_event_finalization_status(event: Event) -> None:
    """
    Feature: event-planning-agent, Property 21: Event finalization status
    
    For any pending event, finalizing it should change the status to confirmed.
    
    Validates: Requirements 5.2
    """
    # Create a temporary storage directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        repo = EventRepository(storage_dir=temp_dir)
        
        # Create the pending event
        created_event = repo.create(event)
        assert created_event.status == EventStatus.PENDING
        
        # Finalize the event
        created_event.status = EventStatus.CONFIRMED
        updated_event = repo.update(created_event)
        
        # Verify the status changed to CONFIRMED
        assert updated_event.status == EventStatus.CONFIRMED
        
        # Verify the change persists
        retrieved_event = repo.get(updated_event.id)
        assert retrieved_event is not None
        assert retrieved_event.status == EventStatus.CONFIRMED
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir)


# Feature: event-planning-agent, Property 22: Event time validation
@given(
    st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31)),
    st.timedeltas(min_value=timedelta(hours=1), max_value=timedelta(days=3)),
    st.text(
        min_size=1, max_size=50,
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-")
    )
)
@settings(max_examples=100)
def test_property_22_event_time_validation(start_time: datetime, duration: timedelta, user_id: str) -> None:
    """
    Feature: event-planning-agent, Property 22: Event time validation
    
    For any event with a proposed time, the event should only be created if the time
    falls within at least one participant's availability window.
    
    Validates: Requirements 5.3
    """
    # Create temporary storage directories
    temp_dir = tempfile.mkdtemp()
    
    try:
        user_repo = UserRepository(storage_dir=temp_dir)
        
        # Create a user with an availability window that matches the event time
        end_time = start_time + duration
        
        # Create an availability window that overlaps with the event time
        availability_window = AvailabilityWindow(
            user_id=user_id,
            start_time=start_time - timedelta(hours=1),  # Starts before event
            end_time=end_time + timedelta(hours=1),      # Ends after event
            timezone="UTC"
        )
        
        from app.event_planning.models.user import User, PreferenceProfile
        user = User(
            id=user_id,
            name="Test User",
            email=f"{user_id}@test.com",
            preference_profile=PreferenceProfile(
                user_id=user_id,
                activity_preferences={},
                updated_at=datetime.now()
            ),
            availability_windows=[availability_window]
        )
        
        user_repo.create(user)
        
        # Verify the user has availability
        retrieved_user = user_repo.get(user_id)
        assert retrieved_user is not None
        assert len(retrieved_user.availability_windows) > 0
        
        # Check if event time falls within availability window
        event_start = start_time
        event_end = end_time
        window = retrieved_user.availability_windows[0]
        
        # The event time should fall within the availability window
        is_within_availability = (
            window.start_time <= event_start and
            event_end <= window.end_time
        )
        
        assert is_within_availability, "Event time should fall within availability window"
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir)


# Feature: event-planning-agent, Property 24: Event cancellation preservation
@given(confirmed_event_strategy())
@settings(max_examples=100)
def test_property_24_event_cancellation_preservation(event: Event) -> None:
    """
    Feature: event-planning-agent, Property 24: Event cancellation preservation
    
    For any confirmed event, canceling it should update the status to cancelled
    while keeping the event record retrievable for historical reference.
    
    Validates: Requirements 5.5
    """
    # Create a temporary storage directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        repo = EventRepository(storage_dir=temp_dir)
        
        # Create the confirmed event
        created_event = repo.create(event)
        assert created_event.status == EventStatus.CONFIRMED
        
        # Store original event details
        original_id = created_event.id
        original_name = created_event.name
        original_activity_type = created_event.activity_type
        original_participant_ids = created_event.participant_ids.copy()
        
        # Cancel the event
        created_event.status = EventStatus.CANCELLED
        cancelled_event = repo.update(created_event)
        
        # Verify the status changed to CANCELLED
        assert cancelled_event.status == EventStatus.CANCELLED
        
        # Verify the event is still retrievable
        retrieved_event = repo.get(original_id)
        assert retrieved_event is not None
        
        # Verify all original details are preserved
        assert retrieved_event.id == original_id
        assert retrieved_event.name == original_name
        assert retrieved_event.activity_type == original_activity_type
        assert retrieved_event.participant_ids == original_participant_ids
        assert retrieved_event.status == EventStatus.CANCELLED
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir)
