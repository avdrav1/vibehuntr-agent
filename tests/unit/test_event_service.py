"""Unit tests for event service."""

import tempfile
import shutil
from datetime import datetime, timedelta
import pytest

from app.event_planning.models.event import Event, EventStatus, Location
from app.event_planning.models.suggestion import EventSuggestion
from app.event_planning.models.user import User, PreferenceProfile, AvailabilityWindow
from app.event_planning.repositories.event_repository import EventRepository
from app.event_planning.repositories.user_repository import UserRepository
from app.event_planning.services.event_service import EventService
from app.event_planning.exceptions import (
    EventNotFoundError,
    InvalidEventStatusError,
    InsufficientAvailabilityError,
)


@pytest.fixture
def temp_storage():
    """Create a temporary storage directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def event_service(temp_storage):
    """Create an event service with temporary storage."""
    event_repo = EventRepository(storage_dir=temp_storage)
    user_repo = UserRepository(storage_dir=temp_storage)
    return EventService(event_repo, user_repo)


@pytest.fixture
def sample_user(temp_storage):
    """Create a sample user with availability."""
    user_repo = UserRepository(storage_dir=temp_storage)
    
    user = User(
        id="user1",
        name="Test User",
        email="test@example.com",
        preference_profile=PreferenceProfile(
            user_id="user1",
            activity_preferences={"dining": 0.8},
            updated_at=datetime.now()
        ),
        availability_windows=[
            AvailabilityWindow(
                user_id="user1",
                start_time=datetime(2025, 1, 1, 10, 0),
                end_time=datetime(2025, 1, 1, 22, 0),
                timezone="UTC"
            )
        ]
    )
    
    return user_repo.create(user)


@pytest.fixture
def sample_suggestion():
    """Create a sample event suggestion."""
    return EventSuggestion(
        id="suggestion1",
        activity_type="dining",
        location=Location(
            name="Restaurant",
            address="123 Main St"
        ),
        estimated_duration=timedelta(hours=2),
        estimated_cost_per_person=50.0,
        description="Nice dinner",
        consensus_score=0.9
    )


def test_create_event_from_suggestion(event_service, sample_user, sample_suggestion):
    """Test creating an event from a suggestion."""
    # Create event during user's availability
    start_time = datetime(2025, 1, 1, 18, 0)
    
    event = event_service.create_event_from_suggestion(
        suggestion=sample_suggestion,
        event_id="event1",
        event_name="Dinner Event",
        start_time=start_time,
        participant_ids=[sample_user.id]
    )
    
    assert event.id == "event1"
    assert event.name == "Dinner Event"
    assert event.status == EventStatus.PENDING
    assert event.activity_type == sample_suggestion.activity_type
    assert event.budget_per_person == sample_suggestion.estimated_cost_per_person
    assert sample_user.id in event.participant_ids


def test_create_event_outside_availability_fails(event_service, sample_user, sample_suggestion):
    """Test that creating an event outside availability window fails."""
    # Try to create event outside user's availability
    start_time = datetime(2025, 1, 2, 18, 0)  # Different day
    
    with pytest.raises(InsufficientAvailabilityError, match="availability window"):
        event_service.create_event_from_suggestion(
            suggestion=sample_suggestion,
            event_id="event1",
            event_name="Dinner Event",
            start_time=start_time,
            participant_ids=[sample_user.id]
        )


def test_finalize_event(event_service, sample_user, sample_suggestion):
    """Test finalizing a pending event."""
    # Create a pending event
    start_time = datetime(2025, 1, 1, 18, 0)
    event = event_service.create_event_from_suggestion(
        suggestion=sample_suggestion,
        event_id="event1",
        event_name="Dinner Event",
        start_time=start_time,
        participant_ids=[sample_user.id]
    )
    
    assert event.status == EventStatus.PENDING
    
    # Finalize the event
    finalized_event = event_service.finalize_event("event1")
    
    assert finalized_event.status == EventStatus.CONFIRMED
    assert finalized_event.id == event.id


def test_finalize_nonexistent_event_fails(event_service):
    """Test that finalizing a non-existent event fails."""
    with pytest.raises(EventNotFoundError, match="does not exist"):
        event_service.finalize_event("nonexistent")


def test_finalize_already_confirmed_event_fails(event_service, sample_user, sample_suggestion):
    """Test that finalizing an already confirmed event fails."""
    # Create and finalize an event
    start_time = datetime(2025, 1, 1, 18, 0)
    event = event_service.create_event_from_suggestion(
        suggestion=sample_suggestion,
        event_id="event1",
        event_name="Dinner Event",
        start_time=start_time,
        participant_ids=[sample_user.id]
    )
    
    event_service.finalize_event("event1")
    
    # Try to finalize again
    with pytest.raises(InvalidEventStatusError, match="Only PENDING events"):
        event_service.finalize_event("event1")


def test_cancel_event(event_service, sample_user, sample_suggestion):
    """Test canceling an event."""
    # Create and finalize an event
    start_time = datetime(2025, 1, 1, 18, 0)
    event = event_service.create_event_from_suggestion(
        suggestion=sample_suggestion,
        event_id="event1",
        event_name="Dinner Event",
        start_time=start_time,
        participant_ids=[sample_user.id]
    )
    
    finalized_event = event_service.finalize_event("event1")
    assert finalized_event.status == EventStatus.CONFIRMED
    
    # Cancel the event
    cancelled_event = event_service.cancel_event("event1")
    
    assert cancelled_event.status == EventStatus.CANCELLED
    assert cancelled_event.id == event.id
    
    # Verify event is still retrievable
    retrieved_event = event_service.get_event("event1")
    assert retrieved_event is not None
    assert retrieved_event.status == EventStatus.CANCELLED


def test_cancel_nonexistent_event_fails(event_service):
    """Test that canceling a non-existent event fails."""
    with pytest.raises(EventNotFoundError, match="does not exist"):
        event_service.cancel_event("nonexistent")


def test_cancel_already_cancelled_event_fails(event_service, sample_user, sample_suggestion):
    """Test that canceling an already cancelled event fails."""
    # Create, finalize, and cancel an event
    start_time = datetime(2025, 1, 1, 18, 0)
    event = event_service.create_event_from_suggestion(
        suggestion=sample_suggestion,
        event_id="event1",
        event_name="Dinner Event",
        start_time=start_time,
        participant_ids=[sample_user.id]
    )
    
    event_service.finalize_event("event1")
    event_service.cancel_event("event1")
    
    # Try to cancel again
    with pytest.raises(InvalidEventStatusError, match="already cancelled"):
        event_service.cancel_event("event1")
