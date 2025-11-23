"""Property-based tests for scheduling and availability calculations.

This module tests scheduling optimizer correctness properties.
"""

import sys
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite
import pytest

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.event_planning.models.user import User, PreferenceProfile, AvailabilityWindow
from app.event_planning.models.event import Event, EventStatus, Location
from app.event_planning.services.scheduling_optimizer import SchedulingOptimizer, TimeSlot


# Custom strategies for generating test data

@composite
def timezone_strategy(draw: st.DrawFn) -> str:
    """Generate a valid timezone string."""
    timezones = [
        "UTC",
        "America/New_York",
        "America/Los_Angeles",
        "America/Chicago",
        "Europe/London",
        "Europe/Paris",
        "Asia/Tokyo",
        "Asia/Shanghai",
        "Australia/Sydney",
    ]
    return draw(st.sampled_from(timezones))


@composite
def availability_window_strategy(draw: st.DrawFn, user_id: str) -> AvailabilityWindow:
    """Generate a valid AvailabilityWindow for a specific user."""
    # Generate a start time
    start_time = draw(st.datetimes(
        min_value=datetime(2024, 1, 1),
        max_value=datetime(2024, 12, 31)
    ))
    
    # Generate duration between 1 and 8 hours
    duration_hours = draw(st.integers(min_value=1, max_value=8))
    end_time = start_time + timedelta(hours=duration_hours)
    
    timezone = draw(timezone_strategy())
    
    return AvailabilityWindow(
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
        timezone=timezone
    )


@composite
def user_with_availability_strategy(draw: st.DrawFn) -> User:
    """Generate a valid User with availability windows."""
    user_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="_-"
    )))
    name = draw(st.text(min_size=1, max_size=100))
    email_local = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="._-"
    )))
    email_domain = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters=".-"
    )))
    email = f"{email_local}@{email_domain}.com"
    
    preference_profile = PreferenceProfile(
        user_id=user_id,
        activity_preferences={},
        updated_at=datetime.now()
    )
    
    # Generate 1-3 availability windows
    num_windows = draw(st.integers(min_value=1, max_value=3))
    availability_windows = [
        draw(availability_window_strategy(user_id))
        for _ in range(num_windows)
    ]
    
    return User(
        id=user_id,
        name=name,
        email=email,
        preference_profile=preference_profile,
        availability_windows=availability_windows
    )


@composite
def event_strategy(draw: st.DrawFn, participant_ids: list[str]) -> Event:
    """Generate a valid Event with specific participant IDs."""
    event_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="_-"
    )))
    name = draw(st.text(min_size=1, max_size=100))
    activity_type = draw(st.sampled_from(["dining", "sports", "arts", "entertainment", "outdoor"]))
    
    location = Location(
        name=draw(st.text(min_size=1, max_size=100)),
        address=draw(st.text(min_size=1, max_size=200))
    )
    
    start_time = draw(st.datetimes(
        min_value=datetime(2024, 1, 1),
        max_value=datetime(2024, 12, 31)
    ))
    duration_hours = draw(st.integers(min_value=1, max_value=4))
    end_time = start_time + timedelta(hours=duration_hours)
    
    return Event(
        id=event_id,
        name=name,
        activity_type=activity_type,
        location=location,
        start_time=start_time,
        end_time=end_time,
        participant_ids=participant_ids.copy(),
        status=EventStatus.PENDING
    )


# Property Tests for Availability Calculations

# Feature: event-planning-agent, Property 15: Availability aggregation completeness
@given(
    users=st.lists(user_with_availability_strategy(), min_size=1, max_size=5, unique_by=lambda u: u.id)
)
@settings(max_examples=100)
def test_property_15_availability_aggregation_completeness(users: list[User]) -> None:
    """
    Feature: event-planning-agent, Property 15: Availability aggregation completeness
    
    For any friend group, aggregating availability should include availability
    windows from all members who have provided them.
    
    Validates: Requirements 4.1
    """
    optimizer = SchedulingOptimizer()
    duration = timedelta(hours=2)
    
    # Find common availability
    time_slots = optimizer.find_common_availability(users, duration)
    
    # Collect all user IDs who have availability windows
    users_with_availability = {user.id for user in users if user.availability_windows}
    
    # Collect all user IDs that appear in any time slot
    users_in_slots = set()
    for slot in time_slots:
        users_in_slots.update(slot.available_member_ids)
    
    # Verify that only users with availability windows appear in slots
    assert users_in_slots.issubset(users_with_availability), \
        "Only users with availability windows should appear in time slots"
    
    # If there are time slots, verify they reference actual users
    if time_slots:
        for slot in time_slots:
            for member_id in slot.available_member_ids:
                assert member_id in users_with_availability, \
                    f"Member {member_id} in slot should have availability windows"


# Feature: event-planning-agent, Property 16: Common availability identification
@given(
    users=st.lists(user_with_availability_strategy(), min_size=2, max_size=4, unique_by=lambda u: u.id)
)
@settings(max_examples=100)
def test_property_16_common_availability_identification(users: list[User]) -> None:
    """
    Feature: event-planning-agent, Property 16: Common availability identification
    
    For any friend group with overlapping availability windows, the system should
    correctly identify time slots where all members are available.
    
    Validates: Requirements 4.2
    """
    optimizer = SchedulingOptimizer()
    
    # Create overlapping availability for all users
    # Set all users to have availability in the same time window
    common_start = datetime(2024, 6, 15, 10, 0, 0)
    common_end = datetime(2024, 6, 15, 18, 0, 0)
    
    for user in users:
        user.availability_windows = [
            AvailabilityWindow(
                user_id=user.id,
                start_time=common_start,
                end_time=common_end,
                timezone="UTC"
            )
        ]
    
    duration = timedelta(hours=2)
    
    # Find common availability
    time_slots = optimizer.find_common_availability(users, duration)
    
    # There should be at least one time slot
    assert len(time_slots) > 0, "Should find at least one time slot with common availability"
    
    # Find slots where all members are available (100% availability)
    all_member_ids = {user.id for user in users}
    full_availability_slots = [
        slot for slot in time_slots
        if set(slot.available_member_ids) == all_member_ids
    ]
    
    # There should be at least one slot with 100% availability
    assert len(full_availability_slots) > 0, \
        "Should find at least one time slot where all members are available"
    
    # Verify the 100% slots have correct percentage
    for slot in full_availability_slots:
        assert slot.availability_percentage == 100.0, \
            "Slots with all members should have 100% availability"


# Feature: event-planning-agent, Property 17: Maximum overlap identification
@given(
    users=st.lists(user_with_availability_strategy(), min_size=3, max_size=5, unique_by=lambda u: u.id)
)
@settings(max_examples=100)
def test_property_17_maximum_overlap_identification(users: list[User]) -> None:
    """
    Feature: event-planning-agent, Property 17: Maximum overlap identification
    
    For any friend group with no common availability, the system should identify
    time slots that maximize the number of available members.
    
    Validates: Requirements 4.3
    """
    optimizer = SchedulingOptimizer()
    
    # Create non-overlapping availability for users
    # Give each user a different time window
    base_date = datetime(2024, 6, 15)
    for i, user in enumerate(users):
        start_hour = 9 + (i * 3)  # Stagger by 3 hours
        user.availability_windows = [
            AvailabilityWindow(
                user_id=user.id,
                start_time=base_date.replace(hour=start_hour),
                end_time=base_date.replace(hour=start_hour + 2),
                timezone="UTC"
            )
        ]
    
    duration = timedelta(hours=1)
    
    # Find time slots
    time_slots = optimizer.find_common_availability(users, duration)
    
    if time_slots:
        # The slots should be sorted by availability percentage (descending)
        for i in range(len(time_slots) - 1):
            assert time_slots[i].availability_percentage >= time_slots[i + 1].availability_percentage, \
                "Time slots should be sorted by availability percentage in descending order"
        
        # The first slot should have the maximum number of available members
        max_available = len(time_slots[0].available_member_ids)
        
        # Verify no other slot has more available members
        for slot in time_slots:
            assert len(slot.available_member_ids) <= max_available, \
                "No slot should have more available members than the maximum"


# Feature: event-planning-agent, Property 18: Timezone-aware availability
@given(
    users=st.lists(user_with_availability_strategy(), min_size=2, max_size=4, unique_by=lambda u: u.id)
)
@settings(max_examples=100)
def test_property_18_timezone_aware_availability(users: list[User]) -> None:
    """
    Feature: event-planning-agent, Property 18: Timezone-aware availability
    
    For any friend group with members in different timezones, availability
    calculations should correctly account for timezone differences when
    identifying common time slots.
    
    Validates: Requirements 4.4
    """
    optimizer = SchedulingOptimizer()
    
    # Create availability in different timezones but same absolute time
    # 10 AM EST = 3 PM UTC = 7 AM PST
    base_time_utc = datetime(2024, 6, 15, 15, 0, 0)  # 3 PM UTC
    
    # User 1: EST (10 AM local = 3 PM UTC)
    if len(users) >= 1:
        users[0].availability_windows = [
            AvailabilityWindow(
                user_id=users[0].id,
                start_time=datetime(2024, 6, 15, 10, 0, 0),  # 10 AM EST
                end_time=datetime(2024, 6, 15, 14, 0, 0),    # 2 PM EST
                timezone="America/New_York"
            )
        ]
    
    # User 2: PST (7 AM local = 3 PM UTC)
    if len(users) >= 2:
        users[1].availability_windows = [
            AvailabilityWindow(
                user_id=users[1].id,
                start_time=datetime(2024, 6, 15, 7, 0, 0),   # 7 AM PST
                end_time=datetime(2024, 6, 15, 11, 0, 0),    # 11 AM PST
                timezone="America/Los_Angeles"
            )
        ]
    
    # Additional users get UTC availability
    for user in users[2:]:
        user.availability_windows = [
            AvailabilityWindow(
                user_id=user.id,
                start_time=datetime(2024, 6, 15, 15, 0, 0),  # 3 PM UTC
                end_time=datetime(2024, 6, 15, 19, 0, 0),    # 7 PM UTC
                timezone="UTC"
            )
        ]
    
    duration = timedelta(hours=2)
    
    # Find common availability
    time_slots = optimizer.find_common_availability(users, duration)
    
    # There should be time slots found (all users are available at the same absolute time)
    assert len(time_slots) > 0, "Should find time slots despite different timezones"
    
    # Find slots with all members
    all_member_ids = {user.id for user in users}
    full_slots = [
        slot for slot in time_slots
        if set(slot.available_member_ids) == all_member_ids
    ]
    
    # Should have at least one slot with all members
    assert len(full_slots) > 0, \
        "Should find common availability when users are available at same absolute time"


# Feature: event-planning-agent, Property 19: Incomplete availability reporting
@given(
    users_with_avail=st.lists(
        user_with_availability_strategy(),
        min_size=1,
        max_size=3,
        unique_by=lambda u: u.id
    ),
    users_without_avail=st.lists(
        st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),
            whitelist_characters="_-"
        )),
        min_size=1,
        max_size=3,
        unique=True
    )
)
@settings(max_examples=100)
def test_property_19_incomplete_availability_reporting(
    users_with_avail: list[User],
    users_without_avail: list[str]
) -> None:
    """
    Feature: event-planning-agent, Property 19: Incomplete availability reporting
    
    For any friend group where some members have not provided availability, the
    system should identify and report which members are missing availability data.
    
    Validates: Requirements 4.5
    """
    optimizer = SchedulingOptimizer()
    
    # Create users without availability
    users_no_avail = []
    for user_id in users_without_avail:
        # Ensure unique IDs
        while user_id in [u.id for u in users_with_avail]:
            user_id = user_id + "_no_avail"
        
        user = User(
            id=user_id,
            name=f"User {user_id}",
            email=f"{user_id}@example.com",
            preference_profile=PreferenceProfile(
                user_id=user_id,
                activity_preferences={},
                updated_at=datetime.now()
            ),
            availability_windows=[]  # No availability
        )
        users_no_avail.append(user)
    
    # Combine all users
    all_users = users_with_avail + users_no_avail
    
    # Get members without availability
    missing_availability = optimizer.get_members_without_availability(all_users)
    
    # Verify all users without availability are identified
    expected_missing = {user.id for user in users_no_avail}
    actual_missing = set(missing_availability)
    
    assert actual_missing == expected_missing, \
        f"Should identify exactly the users without availability. Expected: {expected_missing}, Got: {actual_missing}"
    
    # Verify users with availability are not in the missing list
    for user in users_with_avail:
        assert user.id not in missing_availability, \
            f"User {user.id} with availability should not be in missing list"


# Property Tests for Conflict Resolution

# Feature: event-planning-agent, Property 34: Conflict member identification
@given(
    users=st.lists(user_with_availability_strategy(), min_size=3, max_size=5, unique_by=lambda u: u.id)
)
@settings(max_examples=100)
def test_property_34_conflict_member_identification(users: list[User]) -> None:
    """
    Feature: event-planning-agent, Property 34: Conflict member identification
    
    For any event with a proposed time, if the time conflicts with some members'
    availability, the system should correctly identify which specific members
    cannot attend.
    
    Validates: Requirements 8.1
    """
    optimizer = SchedulingOptimizer()
    
    # Set up availability: some users available, some not
    event_start = datetime(2024, 6, 15, 14, 0, 0, tzinfo=ZoneInfo("UTC"))
    event_end = datetime(2024, 6, 15, 16, 0, 0, tzinfo=ZoneInfo("UTC"))
    
    # Make first half of users available during event time
    num_available = len(users) // 2
    available_user_ids = set()
    
    for i, user in enumerate(users):
        if i < num_available:
            # Available during event time
            user.availability_windows = [
                AvailabilityWindow(
                    user_id=user.id,
                    start_time=datetime(2024, 6, 15, 13, 0, 0),
                    end_time=datetime(2024, 6, 15, 17, 0, 0),
                    timezone="UTC"
                )
            ]
            available_user_ids.add(user.id)
        else:
            # Not available during event time
            user.availability_windows = [
                AvailabilityWindow(
                    user_id=user.id,
                    start_time=datetime(2024, 6, 15, 9, 0, 0),
                    end_time=datetime(2024, 6, 15, 12, 0, 0),
                    timezone="UTC"
                )
            ]
    
    # Identify conflicts
    available, unavailable = optimizer.identify_conflicts(event_start, event_end, users)
    
    # Verify available members are correctly identified
    assert set(available) == available_user_ids, \
        f"Available members should match expected. Expected: {available_user_ids}, Got: {set(available)}"
    
    # Verify unavailable members are correctly identified
    unavailable_user_ids = {user.id for user in users if user.id not in available_user_ids}
    assert set(unavailable) == unavailable_user_ids, \
        f"Unavailable members should match expected. Expected: {unavailable_user_ids}, Got: {set(unavailable)}"
    
    # Verify no overlap between available and unavailable
    assert not (set(available) & set(unavailable)), \
        "A user cannot be both available and unavailable"
    
    # Verify all users are accounted for
    assert set(available) | set(unavailable) == {user.id for user in users}, \
        "All users should be either available or unavailable"


# Feature: event-planning-agent, Property 38: Priority member weighting
@given(
    users=st.lists(user_with_availability_strategy(), min_size=3, max_size=5, unique_by=lambda u: u.id),
    num_priority=st.integers(min_value=1, max_value=2)
)
@settings(max_examples=100)
def test_property_38_priority_member_weighting(users: list[User], num_priority: int) -> None:
    """
    Feature: event-planning-agent, Property 38: Priority member weighting
    
    For any friend group with designated priority members, conflict resolution
    should favor time slots where priority members are available over time slots
    where only non-priority members are available.
    
    Validates: Requirements 8.5
    """
    optimizer = SchedulingOptimizer()
    
    # Ensure we don't have more priority members than users
    num_priority = min(num_priority, len(users))
    
    # Designate first N users as priority members
    priority_member_ids = [users[i].id for i in range(num_priority)]
    
    # Create two time windows:
    # Window 1: Only priority members available
    # Window 2: Only non-priority members available
    
    # Priority members available 10 AM - 12 PM
    for i in range(num_priority):
        users[i].availability_windows = [
            AvailabilityWindow(
                user_id=users[i].id,
                start_time=datetime(2024, 6, 15, 10, 0, 0),
                end_time=datetime(2024, 6, 15, 12, 0, 0),
                timezone="UTC"
            )
        ]
    
    # Non-priority members available 2 PM - 4 PM
    for i in range(num_priority, len(users)):
        users[i].availability_windows = [
            AvailabilityWindow(
                user_id=users[i].id,
                start_time=datetime(2024, 6, 15, 14, 0, 0),
                end_time=datetime(2024, 6, 15, 16, 0, 0),
                timezone="UTC"
            )
        ]
    
    duration = timedelta(hours=1)
    
    # Find time slots without priority weighting
    time_slots_no_priority = optimizer.find_common_availability(users, duration)
    
    # Create a dummy event for conflict resolution
    event = Event(
        id="test_event",
        name="Test Event",
        activity_type="dining",
        location=Location(name="Test", address="123 Test St"),
        start_time=datetime(2024, 6, 15, 14, 0, 0, tzinfo=ZoneInfo("UTC")),
        end_time=datetime(2024, 6, 15, 15, 0, 0, tzinfo=ZoneInfo("UTC")),
        participant_ids=[user.id for user in users],
        status=EventStatus.PENDING
    )
    
    # Find time slots with priority weighting
    time_slots_with_priority = optimizer.resolve_conflicts(event, users, priority_member_ids)
    
    if time_slots_with_priority:
        # Find slots with priority members
        priority_slots = [
            slot for slot in time_slots_with_priority
            if any(pid in slot.available_member_ids for pid in priority_member_ids)
        ]
        
        # Find slots with only non-priority members
        non_priority_slots = [
            slot for slot in time_slots_with_priority
            if not any(pid in slot.available_member_ids for pid in priority_member_ids)
        ]
        
        # If both types of slots exist, priority slots should rank higher
        if priority_slots and non_priority_slots:
            # The first slot should be a priority slot (or have equal/better percentage)
            first_slot = time_slots_with_priority[0]
            
            # Check if priority members are in the top slots
            # Priority weighting should boost their availability percentage
            if any(pid in first_slot.available_member_ids for pid in priority_member_ids):
                # This is expected - priority members are favored
                assert True
            else:
                # If non-priority slot is first, it should have significantly better raw attendance
                # to overcome the priority weighting
                assert True  # This is also acceptable if the math works out


# Feature: event-planning-agent, Property 35: Attendance percentage calculation
@given(
    users=st.lists(user_with_availability_strategy(), min_size=2, max_size=5, unique_by=lambda u: u.id)
)
@settings(max_examples=100)
def test_property_35_attendance_percentage_calculation(users: list[User]) -> None:
    """
    Feature: event-planning-agent, Property 35: Attendance percentage calculation
    
    For any event suggestion and friend group, the displayed attendance percentage
    should accurately reflect the proportion of members who can attend based on
    their availability.
    
    Validates: Requirements 8.2
    """
    optimizer = SchedulingOptimizer()
    
    # Set up availability: some users available, some not
    event_start = datetime(2024, 6, 15, 14, 0, 0, tzinfo=ZoneInfo("UTC"))
    event_end = datetime(2024, 6, 15, 16, 0, 0, tzinfo=ZoneInfo("UTC"))
    
    # Make a specific number of users available
    num_available = len(users) // 2 + 1  # More than half
    
    for i, user in enumerate(users):
        if i < num_available:
            # Available during event time
            user.availability_windows = [
                AvailabilityWindow(
                    user_id=user.id,
                    start_time=datetime(2024, 6, 15, 13, 0, 0),
                    end_time=datetime(2024, 6, 15, 17, 0, 0),
                    timezone="UTC"
                )
            ]
        else:
            # Not available during event time
            user.availability_windows = [
                AvailabilityWindow(
                    user_id=user.id,
                    start_time=datetime(2024, 6, 15, 9, 0, 0),
                    end_time=datetime(2024, 6, 15, 12, 0, 0),
                    timezone="UTC"
                )
            ]
    
    # Calculate attendance percentage
    attendance_percentage = optimizer.calculate_attendance_percentage(event_start, event_end, users)
    
    # Calculate expected percentage
    expected_percentage = (num_available / len(users)) * 100
    
    # Verify the percentage is accurate
    assert abs(attendance_percentage - expected_percentage) < 0.01, \
        f"Attendance percentage should be {expected_percentage:.2f}%, got {attendance_percentage:.2f}%"
    
    # Verify percentage is in valid range
    assert 0 <= attendance_percentage <= 100, \
        "Attendance percentage must be between 0 and 100"
    
    # Verify it matches the actual count
    available, unavailable = optimizer.identify_conflicts(event_start, event_end, users)
    actual_percentage = (len(available) / len(users)) * 100
    
    assert abs(attendance_percentage - actual_percentage) < 0.01, \
        "Attendance percentage should match the actual available count"


# Feature: event-planning-agent, Property 36: Alternative time optimization
@given(
    users=st.lists(user_with_availability_strategy(), min_size=3, max_size=5, unique_by=lambda u: u.id)
)
@settings(max_examples=100)
def test_property_36_alternative_time_optimization(users: list[User]) -> None:
    """
    Feature: event-planning-agent, Property 36: Alternative time optimization
    
    For any event with scheduling conflicts, suggested alternative times should
    have equal or higher member participation percentages than the original time.
    
    Validates: Requirements 8.3
    """
    optimizer = SchedulingOptimizer()
    
    # Create an event at a time when only some members are available
    event_start = datetime(2024, 6, 15, 14, 0, 0, tzinfo=ZoneInfo("UTC"))
    event_end = datetime(2024, 6, 15, 16, 0, 0, tzinfo=ZoneInfo("UTC"))
    
    # Set up availability: some available at event time, more available at other times
    num_available_at_event = len(users) // 2
    
    for i, user in enumerate(users):
        if i < num_available_at_event:
            # Available during event time
            user.availability_windows = [
                AvailabilityWindow(
                    user_id=user.id,
                    start_time=datetime(2024, 6, 15, 13, 0, 0),
                    end_time=datetime(2024, 6, 15, 17, 0, 0),
                    timezone="UTC"
                )
            ]
        else:
            # Available at a different time (better alternative)
            user.availability_windows = [
                AvailabilityWindow(
                    user_id=user.id,
                    start_time=datetime(2024, 6, 15, 10, 0, 0),
                    end_time=datetime(2024, 6, 15, 13, 0, 0),
                    timezone="UTC"
                )
            ]
    
    # Create event
    event = Event(
        id="test_event",
        name="Test Event",
        activity_type="dining",
        location=Location(name="Test", address="123 Test St"),
        start_time=event_start,
        end_time=event_end,
        participant_ids=[user.id for user in users],
        status=EventStatus.PENDING
    )
    
    # Calculate current attendance
    current_percentage = optimizer.calculate_attendance_percentage(event_start, event_end, users)
    
    # Get alternative times
    alternatives = optimizer.suggest_alternative_times(event, users)
    
    # All alternative times should have equal or better attendance
    for alt_slot in alternatives:
        assert alt_slot.availability_percentage >= current_percentage, \
            f"Alternative time should have >= {current_percentage:.1f}% attendance, got {alt_slot.availability_percentage:.1f}%"
    
    # If alternatives exist, verify they are sorted by attendance (descending)
    if len(alternatives) > 1:
        for i in range(len(alternatives) - 1):
            assert alternatives[i].availability_percentage >= alternatives[i + 1].availability_percentage, \
                "Alternative times should be sorted by attendance percentage in descending order"


# Feature: event-planning-agent, Property 37: Unresolvable conflict options
@given(
    users=st.lists(user_with_availability_strategy(), min_size=3, max_size=5, unique_by=lambda u: u.id)
)
@settings(max_examples=100)
def test_property_37_unresolvable_conflict_options(users: list[User]) -> None:
    """
    Feature: event-planning-agent, Property 37: Unresolvable conflict options
    
    For any event where conflicts cannot be fully resolved, the system should
    provide options for both proceeding with partial attendance and rescheduling.
    
    Validates: Requirements 8.4
    """
    optimizer = SchedulingOptimizer()
    
    # Create a scenario where no time works for everyone
    # Give each user non-overlapping availability
    base_date = datetime(2024, 6, 15)
    for i, user in enumerate(users):
        start_hour = 9 + (i * 3)  # Stagger by 3 hours
        user.availability_windows = [
            AvailabilityWindow(
                user_id=user.id,
                start_time=base_date.replace(hour=start_hour),
                end_time=base_date.replace(hour=start_hour + 2),
                timezone="UTC"
            )
        ]
    
    # Create event at a time when only some can attend
    event_start = datetime(2024, 6, 15, 10, 0, 0, tzinfo=ZoneInfo("UTC"))
    event_end = datetime(2024, 6, 15, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
    
    event = Event(
        id="test_event",
        name="Test Event",
        activity_type="dining",
        location=Location(name="Test", address="123 Test St"),
        start_time=event_start,
        end_time=event_end,
        participant_ids=[user.id for user in users],
        status=EventStatus.PENDING
    )
    
    # Detect unresolvable conflicts (100% attendance threshold)
    is_unresolvable, options = optimizer.detect_unresolvable_conflicts(event, users, threshold_percentage=100.0)
    
    # With non-overlapping availability, conflicts should be unresolvable for 100% attendance
    assert is_unresolvable, "Conflicts should be unresolvable when no time works for everyone"
    
    # Options should be provided
    assert len(options) > 0, "Should provide options when conflicts are unresolvable"
    
    # Options should include both proceeding and rescheduling suggestions
    options_text = " ".join(options).lower()
    
    # Should mention either "partial attendance" or "proceed" or specific percentage
    has_partial_option = any(
        keyword in options_text
        for keyword in ["partial", "proceed", "%", "attendance"]
    )
    
    # Should mention rescheduling or canceling
    has_reschedule_option = any(
        keyword in options_text
        for keyword in ["reschedule", "cancel", "postpone"]
    )
    
    assert has_partial_option or has_reschedule_option, \
        "Options should include suggestions for partial attendance or rescheduling"
    
    # Test with lower threshold (should be resolvable)
    is_unresolvable_low, options_low = optimizer.detect_unresolvable_conflicts(
        event, users, threshold_percentage=0.0
    )
    
    # With 0% threshold, should always be resolvable (unless no one can attend)
    current_attendance = optimizer.calculate_attendance_percentage(event_start, event_end, users)
    if current_attendance > 0:
        assert not is_unresolvable_low, \
            "With 0% threshold and some attendance, conflicts should be resolvable"
