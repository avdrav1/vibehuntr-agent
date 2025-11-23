"""Property-based tests for recommendation engine.

This module tests recommendation engine correctness properties.
"""

import sys
import os
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite
import pytest

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.event_planning.models.user import User, PreferenceProfile
from app.event_planning.models.group import FriendGroup
from app.event_planning.models.event import Location
from app.event_planning.models.suggestion import EventSuggestion
from app.event_planning.services.recommendation_engine import RecommendationEngine, SearchFilters


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
def event_suggestion_strategy(draw: st.DrawFn, activity_type: str = None) -> EventSuggestion:
    """Generate a valid EventSuggestion."""
    suggestion_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="_-"
    )))
    
    if activity_type is None:
        activity_type = draw(st.sampled_from(["dining", "sports", "arts", "entertainment", "outdoor"]))
    
    location = draw(location_strategy())
    estimated_duration = draw(st.timedeltas(min_value=timedelta(minutes=30), max_value=timedelta(hours=8)))
    estimated_cost_per_person = draw(st.floats(min_value=0.0, max_value=500.0))
    description = draw(st.text(min_size=1, max_size=200))
    
    return EventSuggestion(
        id=suggestion_id,
        activity_type=activity_type,
        location=location,
        estimated_duration=estimated_duration,
        estimated_cost_per_person=estimated_cost_per_person,
        description=description,
        consensus_score=0.0,
        member_compatibility={}
    )


@composite
def friend_group_strategy(draw: st.DrawFn, member_ids: list[str], priority_member_ids: list[str] = None) -> FriendGroup:
    """Generate a valid FriendGroup with specific member IDs."""
    group_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="_-"
    )))
    name = draw(st.text(min_size=1, max_size=50))
    
    created_at = draw(st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31)
    ))
    
    if priority_member_ids is None:
        # Priority members must be a subset of members
        num_priority = draw(st.integers(min_value=0, max_value=min(2, len(member_ids))))
        priority_member_ids = draw(st.lists(
            st.sampled_from(member_ids) if member_ids else st.nothing(),
            min_size=num_priority,
            max_size=num_priority,
            unique=True
        ))
    
    return FriendGroup(
        id=group_id,
        name=name,
        member_ids=member_ids.copy(),
        created_at=created_at,
        priority_member_ids=priority_member_ids,
    )


# Property Tests

# Feature: event-planning-agent, Property 10: Suggestion relevance to preferences
@given(
    num_users=st.integers(min_value=1, max_value=5),
    num_suggestions=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=100)
def test_property_10_suggestion_relevance_to_preferences(num_users: int, num_suggestions: int) -> None:
    """
    Feature: event-planning-agent, Property 10: Suggestion relevance to preferences
    
    For any friend group with defined member preferences, generated event suggestions
    should align with at least some of the stated preferences from the group members.
    
    Validates: Requirements 3.1
    """
    # Generate users with unique IDs
    user_ids = [f"user_{i}" for i in range(num_users)]
    users = []
    
    for i, user_id in enumerate(user_ids):
        # Create user with specific preferences
        preference_profile = PreferenceProfile(
            user_id=user_id,
            activity_preferences={
                "dining": 0.8 if i % 2 == 0 else 0.2,
                "sports": 0.5,
                "arts": 0.7 if i % 3 == 0 else 0.3
            },
            budget_max=100.0 + (i * 50),
            location_preferences=["downtown", "suburb"],
            dietary_restrictions=[],
            accessibility_needs=[],
            updated_at=datetime.now()
        )
        
        user = User(
            id=user_id,
            name=f"User {i}",
            email=f"user{i}@test.com",
            preference_profile=preference_profile,
            availability_windows=[]
        )
        users.append(user)
    
    # Create a friend group
    group = FriendGroup(
        id="test_group",
        name="Test Group",
        member_ids=user_ids,
        created_at=datetime.now(),
        priority_member_ids=[]
    )
    
    # Create suggestions with various activity types
    suggestions = []
    activity_types = ["dining", "sports", "arts", "entertainment", "outdoor"]
    for i in range(num_suggestions):
        activity_type = activity_types[i % len(activity_types)]
        suggestion = EventSuggestion(
            id=f"suggestion_{i}",
            activity_type=activity_type,
            location=Location(name=f"Location {i}", address=f"Address {i}"),
            estimated_duration=timedelta(hours=2),
            estimated_cost_per_person=50.0 + (i * 20),
            description=f"Description {i}",
            consensus_score=0.0,
            member_compatibility={}
        )
        suggestions.append(suggestion)
    
    # Generate suggestions using the recommendation engine
    engine = RecommendationEngine()
    ranked_suggestions = engine.generate_suggestions(group, users, suggestions)
    
    # Verify that suggestions have been scored
    assert len(ranked_suggestions) > 0, "Should return at least one suggestion"
    
    # Verify that each suggestion has compatibility scores for all users
    for suggestion in ranked_suggestions:
        assert len(suggestion.member_compatibility) == len(users), \
            f"Suggestion should have compatibility scores for all {len(users)} users"
        
        # Verify that at least one user has some compatibility with the suggestion
        # (unless all users have 0 preference for that activity type)
        max_compatibility = max(suggestion.member_compatibility.values())
        
        # Check if any user has a preference for this activity type
        any_user_prefers = any(
            user.preference_profile.activity_preferences.get(suggestion.activity_type, 0) > 0
            for user in users
        )
        
        if any_user_prefers:
            assert max_compatibility > 0, \
                f"If any user prefers {suggestion.activity_type}, max compatibility should be > 0"


# Feature: event-planning-agent, Property 11: Consensus score calculation
@given(
    num_users=st.integers(min_value=1, max_value=5),
    suggestion=event_suggestion_strategy()
)
@settings(max_examples=100)
def test_property_11_consensus_score_calculation(num_users: int, suggestion: EventSuggestion) -> None:
    """
    Feature: event-planning-agent, Property 11: Consensus score calculation
    
    For any event suggestion and friend group, the suggestion should have a consensus
    score that mathematically reflects the compatibility with member preferences.
    
    Validates: Requirements 3.2
    """
    # Generate users with unique IDs
    user_ids = [f"user_{i}" for i in range(num_users)]
    users = []
    
    for i, user_id in enumerate(user_ids):
        # Create user with specific preferences
        preference_profile = PreferenceProfile(
            user_id=user_id,
            activity_preferences={
                suggestion.activity_type: 0.8 if i % 2 == 0 else 0.2
            },
            budget_max=suggestion.estimated_cost_per_person + 100.0,
            location_preferences=[],
            dietary_restrictions=[],
            accessibility_needs=[],
            updated_at=datetime.now()
        )
        
        user = User(
            id=user_id,
            name=f"User {i}",
            email=f"user{i}@test.com",
            preference_profile=preference_profile,
            availability_windows=[]
        )
        users.append(user)
    
    # Calculate consensus score
    engine = RecommendationEngine()
    consensus_score = engine.calculate_consensus_score(suggestion, users, priority_member_ids=[])
    
    # Verify consensus score is in valid range
    assert 0.0 <= consensus_score <= 1.0, \
        f"Consensus score must be between 0 and 1, got {consensus_score}"
    
    # Manually calculate expected consensus score
    individual_scores = []
    for user in users:
        compatibility = engine._calculate_individual_compatibility(suggestion, user)
        individual_scores.append(compatibility)
    
    expected_consensus = sum(individual_scores) / len(individual_scores) if individual_scores else 0.0
    
    # Verify the consensus score matches the expected calculation
    assert abs(consensus_score - expected_consensus) < 0.01, \
        f"Consensus score {consensus_score} should match expected {expected_consensus}"


# Feature: event-planning-agent, Property 12: Suggestion ranking by consensus
@given(
    num_users=st.integers(min_value=1, max_value=5),
    num_suggestions=st.integers(min_value=2, max_value=10)
)
@settings(max_examples=100)
def test_property_12_suggestion_ranking_by_consensus(num_users: int, num_suggestions: int) -> None:
    """
    Feature: event-planning-agent, Property 12: Suggestion ranking by consensus
    
    For any list of event suggestions with different consensus scores, the suggestions
    should be ordered in descending order by consensus score.
    
    Validates: Requirements 3.3
    """
    # Generate users with unique IDs
    user_ids = [f"user_{i}" for i in range(num_users)]
    users = []
    
    for i, user_id in enumerate(user_ids):
        # Create user with specific preferences
        preference_profile = PreferenceProfile(
            user_id=user_id,
            activity_preferences={
                "dining": 0.9,
                "sports": 0.5,
                "arts": 0.3,
                "entertainment": 0.7,
                "outdoor": 0.4
            },
            budget_max=200.0,
            location_preferences=["downtown"],
            dietary_restrictions=[],
            accessibility_needs=[],
            updated_at=datetime.now()
        )
        
        user = User(
            id=user_id,
            name=f"User {i}",
            email=f"user{i}@test.com",
            preference_profile=preference_profile,
            availability_windows=[]
        )
        users.append(user)
    
    # Create a friend group
    group = FriendGroup(
        id="test_group",
        name="Test Group",
        member_ids=user_ids,
        created_at=datetime.now(),
        priority_member_ids=[]
    )
    
    # Create suggestions with different activity types (which will lead to different scores)
    suggestions = []
    activity_types = ["dining", "sports", "arts", "entertainment", "outdoor"]
    for i in range(num_suggestions):
        activity_type = activity_types[i % len(activity_types)]
        suggestion = EventSuggestion(
            id=f"suggestion_{i}",
            activity_type=activity_type,
            location=Location(name=f"Location {i}", address=f"Address {i}"),
            estimated_duration=timedelta(hours=2),
            estimated_cost_per_person=50.0,
            description=f"Description {i}",
            consensus_score=0.0,
            member_compatibility={}
        )
        suggestions.append(suggestion)
    
    # Generate and rank suggestions
    engine = RecommendationEngine()
    ranked_suggestions = engine.generate_suggestions(group, users, suggestions)
    
    # Verify suggestions are ranked in descending order by consensus score
    for i in range(len(ranked_suggestions) - 1):
        assert ranked_suggestions[i].consensus_score >= ranked_suggestions[i + 1].consensus_score, \
            f"Suggestion {i} (score {ranked_suggestions[i].consensus_score}) should have >= score than " \
            f"suggestion {i+1} (score {ranked_suggestions[i + 1].consensus_score})"


# Feature: event-planning-agent, Property 13: Compatible preference satisfaction
@given(
    num_users=st.integers(min_value=1, max_value=5),
    num_suggestions=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=100)
def test_property_13_compatible_preference_satisfaction(num_users: int, num_suggestions: int) -> None:
    """
    Feature: event-planning-agent, Property 13: Compatible preference satisfaction
    
    For any friend group where all members have compatible preferences (no conflicts),
    generated suggestions should satisfy all stated preferences.
    
    Validates: Requirements 3.4
    """
    # Generate users with compatible preferences (all like the same activity)
    user_ids = [f"user_{i}" for i in range(num_users)]
    users = []
    common_activity = "dining"
    common_budget = 100.0
    common_location = "downtown"
    
    for i, user_id in enumerate(user_ids):
        # Create user with compatible preferences
        preference_profile = PreferenceProfile(
            user_id=user_id,
            activity_preferences={
                common_activity: 0.9  # All users strongly prefer dining
            },
            budget_max=common_budget,  # All users have same budget
            location_preferences=[common_location],  # All users prefer same location
            dietary_restrictions=[],
            accessibility_needs=[],
            updated_at=datetime.now()
        )
        
        user = User(
            id=user_id,
            name=f"User {i}",
            email=f"user{i}@test.com",
            preference_profile=preference_profile,
            availability_windows=[]
        )
        users.append(user)
    
    # Create a friend group
    group = FriendGroup(
        id="test_group",
        name="Test Group",
        member_ids=user_ids,
        created_at=datetime.now(),
        priority_member_ids=[]
    )
    
    # Create suggestions, including one that satisfies all preferences
    suggestions = []
    for i in range(num_suggestions):
        # Make at least one suggestion that satisfies all preferences
        if i == 0:
            activity_type = common_activity
            cost = common_budget - 10.0  # Within budget
            location_name = common_location
        else:
            activity_type = ["sports", "arts", "entertainment"][i % 3]
            cost = 50.0 + (i * 20)
            location_name = f"Location {i}"
        
        suggestion = EventSuggestion(
            id=f"suggestion_{i}",
            activity_type=activity_type,
            location=Location(name=location_name, address=f"Address {i}"),
            estimated_duration=timedelta(hours=2),
            estimated_cost_per_person=cost,
            description=f"Description {i}",
            consensus_score=0.0,
            member_compatibility={}
        )
        suggestions.append(suggestion)
    
    # Generate and rank suggestions
    engine = RecommendationEngine()
    ranked_suggestions = engine.generate_suggestions(group, users, suggestions)
    
    # Find the suggestion that satisfies all preferences
    perfect_suggestion = None
    for suggestion in ranked_suggestions:
        if (suggestion.activity_type == common_activity and
            suggestion.estimated_cost_per_person <= common_budget and
            common_location.lower() in suggestion.location.name.lower()):
            perfect_suggestion = suggestion
            break
    
    # If we have a perfect suggestion, it should have high consensus score
    if perfect_suggestion:
        # All users should have high compatibility with this suggestion
        for user_id in user_ids:
            compatibility = perfect_suggestion.member_compatibility.get(user_id, 0.0)
            assert compatibility > 0.5, \
                f"User {user_id} should have high compatibility (>0.5) with perfect suggestion, got {compatibility}"
        
        # Consensus score should be high
        assert perfect_suggestion.consensus_score > 0.5, \
            f"Perfect suggestion should have high consensus score (>0.5), got {perfect_suggestion.consensus_score}"


# Feature: event-planning-agent, Property 14: Conflict optimization
@given(
    num_suggestions=st.integers(min_value=2, max_value=10)
)
@settings(max_examples=100)
def test_property_14_conflict_optimization(num_suggestions: int) -> None:
    """
    Feature: event-planning-agent, Property 14: Conflict optimization
    
    For any friend group with conflicting member preferences, generated suggestions
    should maximize the overall consensus score across all members.
    
    Validates: Requirements 3.5
    """
    # Create users with conflicting preferences
    user1 = User(
        id="user_1",
        name="User 1",
        email="user1@test.com",
        preference_profile=PreferenceProfile(
            user_id="user_1",
            activity_preferences={
                "dining": 0.9,  # Strongly prefers dining
                "sports": 0.1   # Dislikes sports
            },
            budget_max=100.0,
            location_preferences=["downtown"],
            dietary_restrictions=[],
            accessibility_needs=[],
            updated_at=datetime.now()
        ),
        availability_windows=[]
    )
    
    user2 = User(
        id="user_2",
        name="User 2",
        email="user2@test.com",
        preference_profile=PreferenceProfile(
            user_id="user_2",
            activity_preferences={
                "dining": 0.1,  # Dislikes dining
                "sports": 0.9   # Strongly prefers sports
            },
            budget_max=100.0,
            location_preferences=["suburb"],
            dietary_restrictions=[],
            accessibility_needs=[],
            updated_at=datetime.now()
        ),
        availability_windows=[]
    )
    
    user3 = User(
        id="user_3",
        name="User 3",
        email="user3@test.com",
        preference_profile=PreferenceProfile(
            user_id="user_3",
            activity_preferences={
                "dining": 0.5,  # Neutral on dining
                "sports": 0.5,  # Neutral on sports
                "arts": 0.8     # Prefers arts
            },
            budget_max=100.0,
            location_preferences=["city_center"],
            dietary_restrictions=[],
            accessibility_needs=[],
            updated_at=datetime.now()
        ),
        availability_windows=[]
    )
    
    users = [user1, user2, user3]
    user_ids = [u.id for u in users]
    
    # Create a friend group
    group = FriendGroup(
        id="test_group",
        name="Test Group",
        member_ids=user_ids,
        created_at=datetime.now(),
        priority_member_ids=[]
    )
    
    # Create suggestions with different activity types
    suggestions = []
    activity_types = ["dining", "sports", "arts"]
    for i in range(num_suggestions):
        activity_type = activity_types[i % len(activity_types)]
        suggestion = EventSuggestion(
            id=f"suggestion_{i}",
            activity_type=activity_type,
            location=Location(name=f"Location {i}", address=f"Address {i}"),
            estimated_duration=timedelta(hours=2),
            estimated_cost_per_person=50.0,
            description=f"Description {i}",
            consensus_score=0.0,
            member_compatibility={}
        )
        suggestions.append(suggestion)
    
    # Generate and rank suggestions
    engine = RecommendationEngine()
    ranked_suggestions = engine.generate_suggestions(group, users, suggestions)
    
    # Verify that the top suggestion maximizes consensus
    # (should be "arts" since user3 prefers it and user1/user2 are neutral)
    top_suggestion = ranked_suggestions[0]
    
    # The consensus score should be the average of individual compatibilities
    # Verify that the ranking actually optimizes for consensus
    for i in range(len(ranked_suggestions) - 1):
        current_score = ranked_suggestions[i].consensus_score
        next_score = ranked_suggestions[i + 1].consensus_score
        
        assert current_score >= next_score, \
            f"Suggestion {i} should have consensus score >= suggestion {i+1}"
    
    # Verify that each suggestion has a valid consensus score
    for suggestion in ranked_suggestions:
        assert 0.0 <= suggestion.consensus_score <= 1.0, \
            f"Consensus score must be in [0, 1], got {suggestion.consensus_score}"
        
        # Verify consensus score is the average of member compatibilities
        if suggestion.member_compatibility:
            expected_consensus = sum(suggestion.member_compatibility.values()) / len(suggestion.member_compatibility)
            assert abs(suggestion.consensus_score - expected_consensus) < 0.01, \
                f"Consensus score should be average of member compatibilities"
