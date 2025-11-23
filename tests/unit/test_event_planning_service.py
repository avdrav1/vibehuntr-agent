"""Unit tests for EventPlanningService."""

import pytest
from datetime import datetime, timedelta
from app.event_planning.services.event_planning_service import EventPlanningService
from app.event_planning.repositories.user_repository import UserRepository
from app.event_planning.repositories.group_repository import GroupRepository
from app.event_planning.repositories.event_repository import EventRepository
from app.event_planning.repositories.feedback_repository import FeedbackRepository
from app.event_planning.models.suggestion import EventSuggestion
from app.event_planning.models.event import Location


@pytest.fixture
def service(tmp_path):
    """Create an EventPlanningService with temporary storage."""
    storage_dir = str(tmp_path)
    user_repo = UserRepository(storage_dir)
    group_repo = GroupRepository(storage_dir)
    event_repo = EventRepository(storage_dir)
    feedback_repo = FeedbackRepository(storage_dir)
    
    return EventPlanningService(
        user_repository=user_repo,
        group_repository=group_repo,
        event_repository=event_repo,
        feedback_repository=feedback_repo,
        storage_dir=storage_dir
    )


def test_create_user(service):
    """Test creating a user through the service."""
    user = service.create_user(
        name="Alice",
        email="alice@example.com"
    )
    
    assert user.name == "Alice"
    assert user.email == "alice@example.com"
    assert user.id is not None
    assert user.preference_profile is not None


def test_create_user_duplicate_email(service):
    """Test that creating a user with duplicate email fails."""
    service.create_user(name="Alice", email="alice@example.com")
    
    with pytest.raises(ValueError, match="already exists"):
        service.create_user(name="Alice2", email="alice@example.com")


def test_create_group_workflow(service):
    """Test the complete group creation workflow."""
    # Create users
    alice = service.create_user(name="Alice", email="alice@example.com")
    bob = service.create_user(name="Bob", email="bob@example.com")
    
    # Create group
    group = service.create_group(
        name="Weekend Warriors",
        creator_id=alice.id,
        member_ids=[bob.id]
    )
    
    assert group.name == "Weekend Warriors"
    assert alice.id in group.member_ids
    assert bob.id in group.member_ids
    assert len(group.member_ids) == 2


def test_add_group_member(service):
    """Test adding a member to a group."""
    alice = service.create_user(name="Alice", email="alice@example.com")
    bob = service.create_user(name="Bob", email="bob@example.com")
    
    group = service.create_group(
        name="Test Group",
        creator_id=alice.id
    )
    
    updated_group = service.add_group_member(group.id, bob.id)
    
    assert bob.id in updated_group.member_ids
    assert len(updated_group.member_ids) == 2


def test_update_user_preferences(service):
    """Test updating user preferences."""
    user = service.create_user(name="Alice", email="alice@example.com")
    
    updated_user = service.update_user_preferences(
        user_id=user.id,
        activity_preferences={"hiking": 0.9, "movies": 0.7},
        budget_max=50.0,
        location_preferences=["downtown", "park"]
    )
    
    assert updated_user.preference_profile.activity_preferences["hiking"] == 0.9
    assert updated_user.preference_profile.budget_max == 50.0
    assert "downtown" in updated_user.preference_profile.location_preferences


def test_add_user_availability(service):
    """Test adding availability windows."""
    user = service.create_user(name="Alice", email="alice@example.com")
    
    start = datetime(2024, 1, 15, 10, 0)
    end = datetime(2024, 1, 15, 18, 0)
    
    updated_user = service.add_user_availability(
        user_id=user.id,
        start_time=start,
        end_time=end,
        timezone="America/New_York"
    )
    
    assert len(updated_user.availability_windows) == 1
    assert updated_user.availability_windows[0].start_time == start
    assert updated_user.availability_windows[0].timezone == "America/New_York"


def test_plan_event_workflow(service):
    """Test the complete event planning workflow."""
    # Create users with preferences
    alice = service.create_user(name="Alice", email="alice@example.com")
    bob = service.create_user(name="Bob", email="bob@example.com")
    
    service.update_user_preferences(
        user_id=alice.id,
        activity_preferences={"hiking": 0.9}
    )
    service.update_user_preferences(
        user_id=bob.id,
        activity_preferences={"hiking": 0.8}
    )
    
    # Add availability
    start = datetime(2024, 1, 15, 10, 0)
    end = datetime(2024, 1, 15, 18, 0)
    service.add_user_availability(alice.id, start, end)
    service.add_user_availability(bob.id, start, end)
    
    # Create group
    group = service.create_group(
        name="Hiking Buddies",
        creator_id=alice.id,
        member_ids=[bob.id]
    )
    
    # Create suggestions
    suggestions = [
        EventSuggestion(
            id="s1",
            activity_type="hiking",
            location=Location(name="Mountain Trail", address="123 Trail Rd", latitude=0.0, longitude=0.0),
            estimated_duration=timedelta(hours=3),
            estimated_cost_per_person=10.0,
            description="Beautiful mountain hike"
        )
    ]
    
    # Plan event
    plan = service.plan_event(
        group_id=group.id,
        suggestions=suggestions,
        duration=timedelta(hours=3)
    )
    
    assert plan["group"].id == group.id
    assert len(plan["members"]) == 2
    assert len(plan["suggestions"]) == 1
    assert plan["suggestions"][0].consensus_score > 0


def test_create_and_finalize_event(service):
    """Test creating and finalizing an event."""
    # Setup
    alice = service.create_user(name="Alice", email="alice@example.com")
    start = datetime(2024, 1, 15, 10, 0)
    end = datetime(2024, 1, 15, 18, 0)
    service.add_user_availability(alice.id, start, end)
    
    # Create suggestion
    suggestion = EventSuggestion(
        id="s1",
        activity_type="hiking",
        location=Location(name="Trail", address="123 St", latitude=0.0, longitude=0.0),
        estimated_duration=timedelta(hours=3),
        estimated_cost_per_person=10.0,
        description="Hike"
    )
    
    # Create event
    event = service.create_event(
        suggestion_id="s1",
        suggestions=[suggestion],
        event_name="Weekend Hike",
        start_time=datetime(2024, 1, 15, 11, 0),
        participant_ids=[alice.id]
    )
    
    assert event.name == "Weekend Hike"
    assert event.status.value == "pending"
    
    # Finalize event
    finalized = service.finalize_event(event.id)
    assert finalized.status.value == "confirmed"


def test_submit_feedback_workflow(service):
    """Test submitting feedback for an event."""
    # Setup
    alice = service.create_user(name="Alice", email="alice@example.com")
    service.update_user_preferences(
        user_id=alice.id,
        activity_preferences={"hiking": 0.5}
    )
    
    start = datetime(2024, 1, 15, 10, 0)
    end = datetime(2024, 1, 15, 18, 0)
    service.add_user_availability(alice.id, start, end)
    
    suggestion = EventSuggestion(
        id="s1",
        activity_type="hiking",
        location=Location(name="Trail", address="123 St", latitude=0.0, longitude=0.0),
        estimated_duration=timedelta(hours=3),
        estimated_cost_per_person=10.0,
        description="Hike"
    )
    
    event = service.create_event(
        suggestion_id="s1",
        suggestions=[suggestion],
        event_name="Hike",
        start_time=datetime(2024, 1, 15, 11, 0),
        participant_ids=[alice.id]
    )
    
    # Submit positive feedback
    feedback = service.submit_event_feedback(
        event_id=event.id,
        user_id=alice.id,
        rating=5,
        comments="Great hike!"
    )
    
    assert feedback.rating == 5
    assert feedback.comments == "Great hike!"
    
    # Check that preferences were updated
    updated_user = service.user_repo.get(alice.id)
    # Preference should increase from 0.5 toward 1.0
    assert updated_user.preference_profile.activity_preferences["hiking"] > 0.5


def test_check_event_conflicts(service):
    """Test checking for event conflicts."""
    # Create users with different availability
    alice = service.create_user(name="Alice", email="alice@example.com")
    bob = service.create_user(name="Bob", email="bob@example.com")
    
    # Alice is available, Bob is not
    service.add_user_availability(
        alice.id,
        datetime(2024, 1, 15, 10, 0),
        datetime(2024, 1, 15, 18, 0)
    )
    service.add_user_availability(
        bob.id,
        datetime(2024, 1, 16, 10, 0),  # Different day
        datetime(2024, 1, 16, 18, 0)
    )
    
    # Create event
    suggestion = EventSuggestion(
        id="s1",
        activity_type="meeting",
        location=Location(name="Office", address="123 St", latitude=0.0, longitude=0.0),
        estimated_duration=timedelta(hours=2),
        estimated_cost_per_person=0.0,
        description="Team meeting"
    )
    
    event = service.create_event(
        suggestion_id="s1",
        suggestions=[suggestion],
        event_name="Team Meeting",
        start_time=datetime(2024, 1, 15, 14, 0),
        participant_ids=[alice.id, bob.id]
    )
    
    # Check conflicts
    conflicts = service.check_event_conflicts(event.id)
    
    assert alice.id in conflicts["available_members"]
    assert bob.id in conflicts["unavailable_members"]
    assert conflicts["attendance_percentage"] == 50.0


def test_search_suggestions_with_filters(service):
    """Test searching suggestions with filters."""
    alice = service.create_user(name="Alice", email="alice@example.com")
    group = service.create_group(name="Test", creator_id=alice.id)
    
    suggestions = [
        EventSuggestion(
            id="s1",
            activity_type="hiking",
            location=Location(name="Mountain", address="Downtown", latitude=0.0, longitude=0.0),
            estimated_duration=timedelta(hours=3),
            estimated_cost_per_person=20.0,
            description="Mountain hike"
        ),
        EventSuggestion(
            id="s2",
            activity_type="movies",
            location=Location(name="Cinema", address="Uptown", latitude=0.0, longitude=0.0),
            estimated_duration=timedelta(hours=2),
            estimated_cost_per_person=15.0,
            description="Movie night"
        ),
        EventSuggestion(
            id="s3",
            activity_type="hiking",
            location=Location(name="Trail", address="Uptown", latitude=0.0, longitude=0.0),
            estimated_duration=timedelta(hours=2),
            estimated_cost_per_person=50.0,
            description="Premium trail"
        )
    ]
    
    # Filter by activity and budget
    filtered = service.search_suggestions(
        group_id=group.id,
        suggestions=suggestions,
        activity_keywords=["hiking"],
        budget_max=30.0
    )
    
    # Should only return the first hiking suggestion (within budget)
    assert len(filtered) == 1
    assert filtered[0].id == "s1"


def test_error_handling_nonexistent_user(service):
    """Test error handling for nonexistent user."""
    with pytest.raises(ValueError, match="does not exist"):
        service.update_user_preferences(
            user_id="nonexistent",
            budget_max=100.0
        )


def test_error_handling_nonexistent_group(service):
    """Test error handling for nonexistent group."""
    with pytest.raises(ValueError, match="does not exist"):
        service.add_group_member(
            group_id="nonexistent",
            user_id="user123"
        )
