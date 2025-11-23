"""Property-based tests for data model serialization.

This module tests the round-trip serialization properties for core data models.
"""

import sys
import os
from datetime import datetime, timedelta, timezone
from hypothesis import given, strategies as st
from hypothesis.strategies import composite
import pytest

# Add the project root to the path to import models directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import models directly without going through app package
from app.event_planning.models.user import User, PreferenceProfile, AvailabilityWindow
from app.event_planning.models.group import FriendGroup
from app.event_planning.models.event import Event, EventStatus, Location
from app.event_planning.models.feedback import EventFeedback


# Custom strategies for generating test data

@composite
def preference_profile_strategy(draw: st.DrawFn) -> PreferenceProfile:
    """Generate a valid PreferenceProfile."""
    user_id = draw(st.text(min_size=1, max_size=50))
    
    # Generate activity preferences with weights between 0 and 1
    num_activities = draw(st.integers(min_value=0, max_value=5))
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
    
    budget_max = draw(st.none() | st.floats(min_value=0.0, max_value=10000.0))
    location_preferences = draw(st.lists(st.text(min_size=1, max_size=50), max_size=5))
    dietary_restrictions = draw(st.lists(st.text(min_size=1, max_size=50), max_size=5))
    accessibility_needs = draw(st.lists(st.text(min_size=1, max_size=50), max_size=5))
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
def availability_window_strategy(draw: st.DrawFn) -> AvailabilityWindow:
    """Generate a valid AvailabilityWindow."""
    user_id = draw(st.text(min_size=1, max_size=50))
    start_time = draw(st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31)
    ))
    # Ensure end_time is after start_time
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
def user_strategy(draw: st.DrawFn) -> User:
    """Generate a valid User."""
    user_id = draw(st.text(min_size=1, max_size=50))
    name = draw(st.text(min_size=1, max_size=100))
    # Generate valid email
    email_local = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="._-"
    )))
    email_domain = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters=".-"
    )))
    email = f"{email_local}@{email_domain}.com"
    
    preference_profile = draw(preference_profile_strategy())
    # Override user_id to match
    preference_profile.user_id = user_id
    
    availability_windows = draw(st.lists(availability_window_strategy(), max_size=5))
    # Override user_ids to match
    for window in availability_windows:
        window.user_id = user_id
    
    return User(
        id=user_id,
        name=name,
        email=email,
        preference_profile=preference_profile,
        availability_windows=availability_windows,
    )


@composite
def friend_group_strategy(draw: st.DrawFn) -> FriendGroup:
    """Generate a valid FriendGroup."""
    group_id = draw(st.text(min_size=1, max_size=50))
    name = draw(st.text(min_size=1, max_size=100))
    
    # Generate unique member IDs
    num_members = draw(st.integers(min_value=1, max_value=10))
    member_ids = draw(st.lists(
        st.text(min_size=1, max_size=50),
        min_size=num_members,
        max_size=num_members,
        unique=True
    ))
    
    created_at = draw(st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31)
    ))
    
    # Priority members must be a subset of members
    num_priority = draw(st.integers(min_value=0, max_value=min(3, len(member_ids))))
    priority_member_ids = draw(st.lists(
        st.sampled_from(member_ids),
        min_size=num_priority,
        max_size=num_priority,
        unique=True
    ))
    
    return FriendGroup(
        id=group_id,
        name=name,
        member_ids=member_ids,
        created_at=created_at,
        priority_member_ids=priority_member_ids,
    )


@composite
def location_strategy(draw: st.DrawFn) -> Location:
    """Generate a valid Location."""
    name = draw(st.text(min_size=1, max_size=100))
    address = draw(st.text(min_size=1, max_size=200))
    latitude = draw(st.none() | st.floats(min_value=-90.0, max_value=90.0))
    longitude = draw(st.none() | st.floats(min_value=-180.0, max_value=180.0))
    
    return Location(
        name=name,
        address=address,
        latitude=latitude,
        longitude=longitude,
    )


@composite
def event_strategy(draw: st.DrawFn) -> Event:
    """Generate a valid Event."""
    event_id = draw(st.text(min_size=1, max_size=50))
    name = draw(st.text(min_size=1, max_size=100))
    activity_type = draw(st.text(min_size=1, max_size=50))
    location = draw(location_strategy())
    
    start_time = draw(st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31)
    ))
    duration = draw(st.timedeltas(min_value=timedelta(hours=1), max_value=timedelta(days=3)))
    end_time = start_time + duration
    
    # Generate unique participant IDs
    num_participants = draw(st.integers(min_value=1, max_value=10))
    participant_ids = draw(st.lists(
        st.text(min_size=1, max_size=50),
        min_size=num_participants,
        max_size=num_participants,
        unique=True
    ))
    
    status = draw(st.sampled_from(list(EventStatus)))
    budget_per_person = draw(st.none() | st.floats(min_value=0.0, max_value=10000.0))
    description = draw(st.text(max_size=500))
    
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


@composite
def event_feedback_strategy(draw: st.DrawFn) -> EventFeedback:
    """Generate a valid EventFeedback."""
    feedback_id = draw(st.text(min_size=1, max_size=50))
    event_id = draw(st.text(min_size=1, max_size=50))
    user_id = draw(st.text(min_size=1, max_size=50))
    rating = draw(st.integers(min_value=1, max_value=5))
    comments = draw(st.none() | st.text(max_size=500))
    submitted_at = draw(st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31)
    ))
    
    return EventFeedback(
        id=feedback_id,
        event_id=event_id,
        user_id=user_id,
        rating=rating,
        comments=comments,
        submitted_at=submitted_at,
    )


# Property Tests

# Feature: event-planning-agent, Property 1: Group creation persistence
# Feature: event-planning-agent, Property 6: Availability window round-trip
# Feature: event-planning-agent, Property 23: Event data persistence
# Feature: event-planning-agent, Property 25: Feedback storage completeness
@given(friend_group_strategy())
def test_property_1_group_creation_persistence(group: FriendGroup) -> None:
    """
    Feature: event-planning-agent, Property 1: Group creation persistence
    
    For any friend group with valid data, creating the group should result in
    the group being retrievable with the same identifier and member list.
    
    Validates: Requirements 1.1
    """
    # Serialize to JSON
    json_str = group.to_json()
    
    # Deserialize from JSON
    restored_group = FriendGroup.from_json(json_str)
    
    # Verify all fields match
    assert restored_group.id == group.id
    assert restored_group.name == group.name
    assert restored_group.member_ids == group.member_ids
    assert restored_group.priority_member_ids == group.priority_member_ids
    # Compare timestamps (allow for microsecond precision differences)
    assert abs((restored_group.created_at - group.created_at).total_seconds()) < 0.001


@given(availability_window_strategy())
def test_property_6_availability_window_round_trip(window: AvailabilityWindow) -> None:
    """
    Feature: event-planning-agent, Property 6: Availability window round-trip
    
    For any user and valid availability windows, storing the windows and then
    retrieving them should return equivalent time periods with correct dates,
    times, and timezones.
    
    Validates: Requirements 2.1
    """
    # Serialize to dict
    window_dict = window.to_dict()
    
    # Deserialize from dict
    restored_window = AvailabilityWindow.from_dict(window_dict)
    
    # Verify all fields match
    assert restored_window.user_id == window.user_id
    assert restored_window.timezone == window.timezone
    # Compare timestamps (allow for microsecond precision differences)
    assert abs((restored_window.start_time - window.start_time).total_seconds()) < 0.001
    assert abs((restored_window.end_time - window.end_time).total_seconds()) < 0.001


@given(event_strategy())
def test_property_23_event_data_persistence(event: Event) -> None:
    """
    Feature: event-planning-agent, Property 23: Event data persistence
    
    For any finalized event, all event details including time, location,
    activity type, and participant list should be stored and retrievable.
    
    Validates: Requirements 5.4
    """
    # Serialize to JSON
    json_str = event.to_json()
    
    # Deserialize from JSON
    restored_event = Event.from_json(json_str)
    
    # Verify all fields match
    assert restored_event.id == event.id
    assert restored_event.name == event.name
    assert restored_event.activity_type == event.activity_type
    assert restored_event.participant_ids == event.participant_ids
    assert restored_event.status == event.status
    assert restored_event.budget_per_person == event.budget_per_person
    assert restored_event.description == event.description
    
    # Verify location
    assert restored_event.location.name == event.location.name
    assert restored_event.location.address == event.location.address
    assert restored_event.location.latitude == event.location.latitude
    assert restored_event.location.longitude == event.location.longitude
    
    # Compare timestamps
    assert abs((restored_event.start_time - event.start_time).total_seconds()) < 0.001
    assert abs((restored_event.end_time - event.end_time).total_seconds()) < 0.001


@given(event_feedback_strategy())
def test_property_25_feedback_storage_completeness(feedback: EventFeedback) -> None:
    """
    Feature: event-planning-agent, Property 25: Feedback storage completeness
    
    For any completed event and user feedback with rating and optional comments,
    storing the feedback should result in all fields being retrievable.
    
    Validates: Requirements 6.1
    """
    # Serialize to JSON
    json_str = feedback.to_json()
    
    # Deserialize from JSON
    restored_feedback = EventFeedback.from_json(json_str)
    
    # Verify all fields match
    assert restored_feedback.id == feedback.id
    assert restored_feedback.event_id == feedback.event_id
    assert restored_feedback.user_id == feedback.user_id
    assert restored_feedback.rating == feedback.rating
    assert restored_feedback.comments == feedback.comments
    
    # Compare timestamps
    assert abs((restored_feedback.submitted_at - feedback.submitted_at).total_seconds()) < 0.001
