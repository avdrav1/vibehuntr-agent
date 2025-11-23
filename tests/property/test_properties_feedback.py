"""Property-based tests for feedback processing.

This module tests feedback processing correctness properties.
"""

import sys
import os
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite
import pytest
import tempfile
import shutil

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.event_planning.models.user import User, PreferenceProfile
from app.event_planning.models.event import Event, EventStatus, Location
from app.event_planning.models.feedback import EventFeedback
from app.event_planning.repositories.feedback_repository import FeedbackRepository
from app.event_planning.repositories.event_repository import EventRepository
from app.event_planning.repositories.user_repository import UserRepository
from app.event_planning.services.feedback_processor import FeedbackProcessor


# Custom strategies for generating test data

@composite
def preference_profile_strategy(draw: st.DrawFn, user_id: str) -> PreferenceProfile:
    """Generate a valid PreferenceProfile for a specific user."""
    # Generate activity preferences with weights between 0 and 1
    num_activities = draw(st.integers(min_value=1, max_value=5))
    activity_types = ["dining", "sports", "arts", "entertainment", "outdoor"]
    activities = draw(st.lists(
        st.sampled_from(activity_types),
        min_size=num_activities,
        max_size=num_activities,
        unique=True
    ))
    activity_preferences = {
        activity: draw(st.floats(min_value=0.0, max_value=1.0))
        for activity in activities
    }
    
    budget_max = draw(st.none() | st.floats(min_value=10.0, max_value=1000.0))
    location_preferences = draw(st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=3))
    dietary_restrictions = draw(st.lists(st.text(min_size=1, max_size=20), max_size=3))
    accessibility_needs = draw(st.lists(st.text(min_size=1, max_size=20), max_size=3))
    updated_at = draw(st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31)
    ))
    
    return PreferenceProfile(
        user_id=user_id,
        activity_preferences=activity_preferences,
        budget_max=budget_max,
        location_preferences=location_preferences,
        dietary_restrictions=dietary_restrictions,
        accessibility_needs=accessibility_needs,
        updated_at=updated_at,
    )


@composite
def user_strategy(draw: st.DrawFn, user_id: str = None) -> User:
    """Generate a valid User."""
    if user_id is None:
        user_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),
            whitelist_characters="_-"
        )))
    name = draw(st.text(min_size=1, max_size=50))
    # Generate valid email
    email_local = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="._-"
    )))
    email_domain = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters=".-"
    )))
    email = f"{email_local}@{email_domain}.com"
    
    preference_profile = draw(preference_profile_strategy(user_id))
    
    return User(
        id=user_id,
        name=name,
        email=email,
        preference_profile=preference_profile,
        availability_windows=[],
    )


@composite
def location_strategy(draw: st.DrawFn) -> Location:
    """Generate a valid Location."""
    name = draw(st.text(min_size=1, max_size=50))
    address = draw(st.text(min_size=1, max_size=100))
    latitude = draw(st.none() | st.floats(min_value=-90, max_value=90))
    longitude = draw(st.none() | st.floats(min_value=-180, max_value=180))
    
    return Location(
        name=name,
        address=address,
        latitude=latitude,
        longitude=longitude
    )


@composite
def event_strategy(draw: st.DrawFn, event_id: str = None, participant_ids: list = None) -> Event:
    """Generate a valid Event."""
    if event_id is None:
        event_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),
            whitelist_characters="_-"
        )))
    
    if participant_ids is None:
        num_participants = draw(st.integers(min_value=1, max_value=5))
        participant_ids = [f"user_{i}" for i in range(num_participants)]
    
    name = draw(st.text(min_size=1, max_size=50))
    activity_type = draw(st.sampled_from(["dining", "sports", "arts", "entertainment", "outdoor"]))
    location = draw(location_strategy())
    
    start_time = draw(st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31)
    ))
    duration = draw(st.timedeltas(min_value=timedelta(minutes=30), max_value=timedelta(hours=8)))
    end_time = start_time + duration
    
    status = draw(st.sampled_from([EventStatus.PENDING, EventStatus.CONFIRMED, EventStatus.CANCELLED]))
    budget_per_person = draw(st.none() | st.floats(min_value=0.0, max_value=500.0))
    description = draw(st.text(min_size=0, max_size=200))
    
    return Event(
        id=event_id,
        name=name,
        activity_type=activity_type,
        location=location,
        start_time=start_time,
        end_time=end_time,
        participant_ids=participant_ids,
        status=status,
        budget_per_person=budget_per_person,
        description=description,
    )


# Property Tests

# Feature: event-planning-agent, Property 26: Feedback association
@given(
    rating=st.integers(min_value=1, max_value=5),
    comments=st.none() | st.text(min_size=0, max_size=200)
)
@settings(max_examples=100)
def test_property_26_feedback_association(rating: int, comments: str) -> None:
    """
    Feature: event-planning-agent, Property 26: Feedback association
    
    For any submitted feedback, it should be correctly associated with both
    the event and the user who provided it.
    
    Validates: Requirements 6.2
    """
    # Create temporary storage directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize repositories
        feedback_repo = FeedbackRepository(storage_dir=temp_dir)
        event_repo = EventRepository(storage_dir=temp_dir)
        user_repo = UserRepository(storage_dir=temp_dir)
        
        # Create a user
        user_id = "test_user_1"
        user = User(
            id=user_id,
            name="Test User",
            email="test@example.com",
            preference_profile=PreferenceProfile(
                user_id=user_id,
                activity_preferences={"dining": 0.5},
                updated_at=datetime.now()
            ),
            availability_windows=[]
        )
        user_repo.create(user)
        
        # Create an event with the user as a participant
        event_id = "test_event_1"
        event = Event(
            id=event_id,
            name="Test Event",
            activity_type="dining",
            location=Location(name="Test Location", address="123 Test St"),
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=2),
            participant_ids=[user_id],
            status=EventStatus.CONFIRMED,
            description="Test event"
        )
        event_repo.create(event)
        
        # Create feedback processor
        processor = FeedbackProcessor(feedback_repo, event_repo, user_repo)
        
        # Submit feedback
        feedback_id = "test_feedback_1"
        feedback = processor.submit_feedback(
            feedback_id=feedback_id,
            event_id=event_id,
            user_id=user_id,
            rating=rating,
            comments=comments
        )
        
        # Verify feedback is associated with the event
        event_feedback = processor.get_feedback_for_event(event_id)
        assert len(event_feedback) == 1, "Should have exactly one feedback for the event"
        assert event_feedback[0].id == feedback_id, "Feedback ID should match"
        assert event_feedback[0].event_id == event_id, "Feedback should be associated with the event"
        
        # Verify feedback is associated with the user
        user_feedback = processor.get_feedback_for_user(user_id)
        assert len(user_feedback) == 1, "Should have exactly one feedback for the user"
        assert user_feedback[0].id == feedback_id, "Feedback ID should match"
        assert user_feedback[0].user_id == user_id, "Feedback should be associated with the user"
        
        # Verify both associations point to the same feedback
        assert event_feedback[0].id == user_feedback[0].id, \
            "Event and user feedback should be the same feedback object"
        assert event_feedback[0].rating == rating, "Rating should match"
        assert event_feedback[0].comments == comments, "Comments should match"
    
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)


# Feature: event-planning-agent, Property 27: Feedback-driven preference learning
@given(
    initial_weight=st.floats(min_value=0.0, max_value=1.0),
    rating=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=100)
def test_property_27_feedback_driven_preference_learning(initial_weight: float, rating: int) -> None:
    """
    Feature: event-planning-agent, Property 27: Feedback-driven preference learning
    
    For any user who provides feedback on an event, the preference weights for
    characteristics similar to that event should be adjusted in the direction
    of the feedback (increased for positive ratings, decreased for negative ratings).
    
    Validates: Requirements 6.3, 6.4
    """
    # Create temporary storage directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize repositories
        feedback_repo = FeedbackRepository(storage_dir=temp_dir)
        event_repo = EventRepository(storage_dir=temp_dir)
        user_repo = UserRepository(storage_dir=temp_dir)
        
        # Create a user with initial preference
        user_id = "test_user_1"
        activity_type = "dining"
        user = User(
            id=user_id,
            name="Test User",
            email="test@example.com",
            preference_profile=PreferenceProfile(
                user_id=user_id,
                activity_preferences={activity_type: initial_weight},
                updated_at=datetime.now()
            ),
            availability_windows=[]
        )
        user_repo.create(user)
        
        # Create an event with the activity type
        event_id = "test_event_1"
        event = Event(
            id=event_id,
            name="Test Event",
            activity_type=activity_type,
            location=Location(name="Test Location", address="123 Test St"),
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=2),
            participant_ids=[user_id],
            status=EventStatus.CONFIRMED,
            description="Test event"
        )
        event_repo.create(event)
        
        # Create feedback processor
        processor = FeedbackProcessor(feedback_repo, event_repo, user_repo, learning_rate=0.1)
        
        # Submit feedback
        feedback_id = "test_feedback_1"
        processor.submit_feedback(
            feedback_id=feedback_id,
            event_id=event_id,
            user_id=user_id,
            rating=rating,
            comments=None
        )
        
        # Get updated user preferences
        updated_user = user_repo.get(user_id)
        new_weight = updated_user.preference_profile.activity_preferences[activity_type]
        
        # Verify preference weight adjustment based on rating
        if rating >= 4:
            # Positive feedback - weight should increase (or stay same if already 1.0)
            expected_weight = initial_weight * 0.9 + 0.1 * 1.0
            expected_weight = min(1.0, expected_weight)
            assert abs(new_weight - expected_weight) < 0.01, \
                f"For positive rating {rating}, weight should increase from {initial_weight} to ~{expected_weight}, got {new_weight}"
            if initial_weight < 1.0:
                assert new_weight >= initial_weight, \
                    f"Positive feedback should increase or maintain weight"
        elif rating <= 2:
            # Negative feedback - weight should decrease (or stay same if already 0.0)
            expected_weight = initial_weight * 0.9 + 0.1 * 0.0
            expected_weight = max(0.0, expected_weight)
            assert abs(new_weight - expected_weight) < 0.01, \
                f"For negative rating {rating}, weight should decrease from {initial_weight} to ~{expected_weight}, got {new_weight}"
            if initial_weight > 0.0:
                assert new_weight <= initial_weight, \
                    f"Negative feedback should decrease or maintain weight"
        else:
            # Neutral feedback (rating == 3) - weight should not change
            assert abs(new_weight - initial_weight) < 0.01, \
                f"Neutral rating {rating} should not change weight from {initial_weight}, got {new_weight}"
        
        # Verify weight is in valid range
        assert 0.0 <= new_weight <= 1.0, \
            f"Preference weight must be in [0, 1], got {new_weight}"
    
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)


# Feature: event-planning-agent, Property 28: Historical feedback incorporation
@given(
    num_users=st.integers(min_value=1, max_value=5),
    num_events_per_user=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=100)
def test_property_28_historical_feedback_incorporation(num_users: int, num_events_per_user: int) -> None:
    """
    Feature: event-planning-agent, Property 28: Historical feedback incorporation
    
    For any friend group with historical feedback from members, newly generated
    suggestions should reflect the feedback patterns in their consensus scores
    and rankings.
    
    Validates: Requirements 6.5
    """
    # Create temporary storage directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize repositories
        feedback_repo = FeedbackRepository(storage_dir=temp_dir)
        event_repo = EventRepository(storage_dir=temp_dir)
        user_repo = UserRepository(storage_dir=temp_dir)
        
        # Create users
        user_ids = []
        for i in range(num_users):
            user_id = f"user_{i}"
            user_ids.append(user_id)
            
            user = User(
                id=user_id,
                name=f"User {i}",
                email=f"user{i}@example.com",
                preference_profile=PreferenceProfile(
                    user_id=user_id,
                    activity_preferences={
                        "dining": 0.5,
                        "sports": 0.5,
                        "arts": 0.5
                    },
                    updated_at=datetime.now()
                ),
                availability_windows=[]
            )
            user_repo.create(user)
        
        # Create events and feedback for each user
        activity_types = ["dining", "sports", "arts"]
        for user_id in user_ids:
            for j in range(num_events_per_user):
                # Create event
                event_id = f"event_{user_id}_{j}"
                activity_type = activity_types[j % len(activity_types)]
                
                event = Event(
                    id=event_id,
                    name=f"Event {j}",
                    activity_type=activity_type,
                    location=Location(name=f"Location {j}", address=f"Address {j}"),
                    start_time=datetime.now() - timedelta(days=30 - j),
                    end_time=datetime.now() - timedelta(days=30 - j) + timedelta(hours=2),
                    participant_ids=[user_id],
                    status=EventStatus.CONFIRMED,
                    description=f"Event {j}"
                )
                event_repo.create(event)
                
                # Create feedback (vary ratings to create patterns)
                feedback_id = f"feedback_{user_id}_{j}"
                # Give higher ratings to "dining" events
                if activity_type == "dining":
                    rating = 5
                elif activity_type == "sports":
                    rating = 2
                else:
                    rating = 3
                
                feedback = EventFeedback(
                    id=feedback_id,
                    event_id=event_id,
                    user_id=user_id,
                    rating=rating,
                    comments=None,
                    submitted_at=datetime.now()
                )
                feedback_repo.create(feedback)
        
        # Create feedback processor
        processor = FeedbackProcessor(feedback_repo, event_repo, user_repo)
        
        # Get historical feedback patterns
        patterns = processor.get_historical_feedback_patterns(user_ids)
        
        # Verify patterns are captured
        assert patterns["total_feedback_count"] == num_users * num_events_per_user, \
            f"Should have {num_users * num_events_per_user} total feedback entries"
        
        # Verify activity ratings are calculated
        assert "activity_ratings" in patterns, "Should have activity_ratings in patterns"
        
        # If we have enough events, verify the pattern reflects our setup
        if num_events_per_user >= 3:
            # We gave high ratings to dining, low to sports, neutral to arts
            activity_ratings = patterns["activity_ratings"]
            
            if "dining" in activity_ratings:
                assert activity_ratings["dining"] >= 4.0, \
                    f"Dining should have high average rating, got {activity_ratings['dining']}"
            
            if "sports" in activity_ratings:
                assert activity_ratings["sports"] <= 3.0, \
                    f"Sports should have low average rating, got {activity_ratings['sports']}"
            
            if "arts" in activity_ratings:
                assert 2.5 <= activity_ratings["arts"] <= 3.5, \
                    f"Arts should have neutral average rating, got {activity_ratings['arts']}"
        
        # Verify that historical feedback can be retrieved for each user
        for user_id in user_ids:
            user_feedback = processor.get_feedback_for_user(user_id)
            assert len(user_feedback) == num_events_per_user, \
                f"User {user_id} should have {num_events_per_user} feedback entries"
    
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
