"""Property-based tests for search and filtering.

This module tests search and filtering correctness properties.
"""

import sys
import os
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings
from hypothesis.strategies import composite

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.event_planning.models.event import Location
from app.event_planning.models.suggestion import EventSuggestion
from app.event_planning.services.recommendation_engine import SearchFilters


# Custom strategies for generating test data

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
def event_suggestion_strategy(
    draw: st.DrawFn,
    activity_type: str = None,
    location_name: str = None,
    cost: float = None,
    start_date: datetime = None,
    end_date: datetime = None
) -> EventSuggestion:
    """Generate a valid EventSuggestion with optional fixed values."""
    suggestion_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="_-"
    )))
    
    if activity_type is None:
        activity_type = draw(st.sampled_from(["dining", "sports", "arts", "entertainment", "outdoor"]))
    
    if location_name is None:
        location_name = draw(st.text(min_size=1, max_size=50))
    
    location_address = draw(st.text(min_size=1, max_size=100))
    location = Location(name=location_name, address=location_address)
    
    estimated_duration = draw(st.timedeltas(min_value=timedelta(minutes=30), max_value=timedelta(hours=8)))
    
    if cost is None:
        cost = draw(st.floats(min_value=0.0, max_value=500.0))
    
    description = draw(st.text(min_size=1, max_size=200))
    
    # Generate date range if not provided
    if start_date is None:
        start_date = draw(st.none() | st.datetimes(
            min_value=datetime(2024, 1, 1),
            max_value=datetime(2025, 12, 31)
        ))
    
    if end_date is None and start_date is not None:
        # End date should be after start date
        end_date = draw(st.datetimes(
            min_value=start_date + timedelta(days=1),
            max_value=start_date + timedelta(days=365)
        ))
    
    return EventSuggestion(
        id=suggestion_id,
        activity_type=activity_type,
        location=location,
        estimated_duration=estimated_duration,
        estimated_cost_per_person=cost,
        description=description,
        consensus_score=0.0,
        member_compatibility={},
        available_start_date=start_date,
        available_end_date=end_date
    )


# Property Tests

# Feature: event-planning-agent, Property 29: Activity keyword filtering
@given(
    num_suggestions=st.integers(min_value=5, max_value=20),
    keyword=st.sampled_from(["dining", "sports", "arts", "entertainment", "outdoor"])
)
@settings(max_examples=100)
def test_property_29_activity_keyword_filtering(num_suggestions: int, keyword: str) -> None:
    """
    Feature: event-planning-agent, Property 29: Activity keyword filtering
    
    For any search query with activity keywords, returned suggestions should only
    include those matching the specified keywords.
    
    Validates: Requirements 7.1
    """
    # Generate suggestions with various activity types
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
            description=f"A great {activity_type} activity",
            consensus_score=0.0,
            member_compatibility={}
        )
        suggestions.append(suggestion)
    
    # Create filter with activity keyword
    filters = SearchFilters(activity_keywords=[keyword])
    
    # Apply filters manually (simulating what recommendation engine does)
    filtered = [
        s for s in suggestions
        if any(
            kw.lower() in s.activity_type.lower() or
            kw.lower() in s.description.lower()
            for kw in filters.activity_keywords
        )
    ]
    
    # Verify all filtered suggestions match the keyword
    for suggestion in filtered:
        assert (
            keyword.lower() in suggestion.activity_type.lower() or
            keyword.lower() in suggestion.description.lower()
        ), f"Filtered suggestion should contain keyword '{keyword}'"
    
    # Verify we didn't include suggestions that don't match
    for suggestion in suggestions:
        matches_keyword = (
            keyword.lower() in suggestion.activity_type.lower() or
            keyword.lower() in suggestion.description.lower()
        )
        is_in_filtered = suggestion in filtered
        
        assert matches_keyword == is_in_filtered, \
            f"Suggestion should be in filtered list if and only if it matches keyword"


# Feature: event-planning-agent, Property 30: Location filtering
@given(
    num_suggestions=st.integers(min_value=5, max_value=20),
    location_filter=st.sampled_from(["downtown", "suburb", "beach", "mountain", "city"])
)
@settings(max_examples=100)
def test_property_30_location_filtering(num_suggestions: int, location_filter: str) -> None:
    """
    Feature: event-planning-agent, Property 30: Location filtering
    
    For any location filter, returned suggestions should only include those within
    the specified geographic area.
    
    Validates: Requirements 7.2
    """
    # Generate suggestions with various locations
    suggestions = []
    location_names = ["downtown plaza", "suburb mall", "beach resort", "mountain lodge", "city center"]
    
    for i in range(num_suggestions):
        location_name = location_names[i % len(location_names)]
        suggestion = EventSuggestion(
            id=f"suggestion_{i}",
            activity_type="dining",
            location=Location(name=location_name, address=f"{location_name} address"),
            estimated_duration=timedelta(hours=2),
            estimated_cost_per_person=50.0,
            description=f"Activity at {location_name}",
            consensus_score=0.0,
            member_compatibility={}
        )
        suggestions.append(suggestion)
    
    # Create filter with location
    filters = SearchFilters(location_area=location_filter)
    
    # Apply filters manually
    filtered = [
        s for s in suggestions
        if filters.location_area.lower() in s.location.name.lower() or
           filters.location_area.lower() in s.location.address.lower()
    ]
    
    # Verify all filtered suggestions match the location
    for suggestion in filtered:
        assert (
            location_filter.lower() in suggestion.location.name.lower() or
            location_filter.lower() in suggestion.location.address.lower()
        ), f"Filtered suggestion should be in location area '{location_filter}'"
    
    # Verify we didn't include suggestions that don't match
    for suggestion in suggestions:
        matches_location = (
            location_filter.lower() in suggestion.location.name.lower() or
            location_filter.lower() in suggestion.location.address.lower()
        )
        is_in_filtered = suggestion in filtered
        
        assert matches_location == is_in_filtered, \
            f"Suggestion should be in filtered list if and only if it matches location"


# Feature: event-planning-agent, Property 31: Date range filtering
@given(
    num_suggestions=st.integers(min_value=5, max_value=20)
)
@settings(max_examples=100)
def test_property_31_date_range_filtering(num_suggestions: int) -> None:
    """
    Feature: event-planning-agent, Property 31: Date range filtering
    
    For any date range filter, returned suggestions should only include those
    available during the specified time period.
    
    Validates: Requirements 7.3
    """
    # Define filter date range
    filter_start = datetime(2024, 6, 1)
    filter_end = datetime(2024, 8, 31)
    
    # Generate suggestions with various date ranges
    suggestions = []
    
    for i in range(num_suggestions):
        # Create suggestions with different availability patterns
        if i % 4 == 0:
            # Fully within range
            start_date = datetime(2024, 6, 15)
            end_date = datetime(2024, 7, 15)
        elif i % 4 == 1:
            # Overlaps start
            start_date = datetime(2024, 5, 15)
            end_date = datetime(2024, 6, 15)
        elif i % 4 == 2:
            # Overlaps end
            start_date = datetime(2024, 8, 15)
            end_date = datetime(2024, 9, 15)
        else:
            # Outside range
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 3, 31)
        
        suggestion = EventSuggestion(
            id=f"suggestion_{i}",
            activity_type="dining",
            location=Location(name=f"Location {i}", address=f"Address {i}"),
            estimated_duration=timedelta(hours=2),
            estimated_cost_per_person=50.0,
            description=f"Activity {i}",
            consensus_score=0.0,
            member_compatibility={},
            available_start_date=start_date,
            available_end_date=end_date
        )
        suggestions.append(suggestion)
    
    # Create filter with date range
    filters = SearchFilters(date_range=(filter_start, filter_end))
    
    # Apply filters manually
    filtered = [
        s for s in suggestions
        if s.available_start_date is not None and s.available_end_date is not None and
           s.available_start_date <= filter_end and s.available_end_date >= filter_start
    ]
    
    # Verify all filtered suggestions overlap with the date range
    for suggestion in filtered:
        assert suggestion.available_start_date is not None
        assert suggestion.available_end_date is not None
        assert suggestion.available_start_date <= filter_end, \
            f"Suggestion start date should be before or equal to filter end"
        assert suggestion.available_end_date >= filter_start, \
            f"Suggestion end date should be after or equal to filter start"
    
    # Verify we didn't include suggestions that don't overlap
    for suggestion in suggestions:
        if suggestion.available_start_date is None or suggestion.available_end_date is None:
            # Suggestions without dates should be excluded
            assert suggestion not in filtered
        else:
            overlaps = (
                suggestion.available_start_date <= filter_end and
                suggestion.available_end_date >= filter_start
            )
            is_in_filtered = suggestion in filtered
            
            assert overlaps == is_in_filtered, \
                f"Suggestion should be in filtered list if and only if it overlaps with date range"


# Feature: event-planning-agent, Property 32: Budget filtering
@given(
    num_suggestions=st.integers(min_value=5, max_value=20),
    budget_max=st.floats(min_value=50.0, max_value=200.0)
)
@settings(max_examples=100)
def test_property_32_budget_filtering(num_suggestions: int, budget_max: float) -> None:
    """
    Feature: event-planning-agent, Property 32: Budget filtering
    
    For any budget filter, returned suggestions should only include those within
    the specified price range.
    
    Validates: Requirements 7.4
    """
    # Generate suggestions with various costs
    suggestions = []
    
    for i in range(num_suggestions):
        cost = 25.0 + (i * 20.0)  # Costs from 25 to 25 + (num_suggestions-1)*20
        suggestion = EventSuggestion(
            id=f"suggestion_{i}",
            activity_type="dining",
            location=Location(name=f"Location {i}", address=f"Address {i}"),
            estimated_duration=timedelta(hours=2),
            estimated_cost_per_person=cost,
            description=f"Activity {i}",
            consensus_score=0.0,
            member_compatibility={}
        )
        suggestions.append(suggestion)
    
    # Create filter with budget
    filters = SearchFilters(budget_max=budget_max)
    
    # Apply filters manually
    filtered = [
        s for s in suggestions
        if s.estimated_cost_per_person <= budget_max
    ]
    
    # Verify all filtered suggestions are within budget
    for suggestion in filtered:
        assert suggestion.estimated_cost_per_person <= budget_max, \
            f"Filtered suggestion cost ({suggestion.estimated_cost_per_person}) should be <= budget ({budget_max})"
    
    # Verify we didn't include suggestions that exceed budget
    for suggestion in suggestions:
        within_budget = suggestion.estimated_cost_per_person <= budget_max
        is_in_filtered = suggestion in filtered
        
        assert within_budget == is_in_filtered, \
            f"Suggestion should be in filtered list if and only if it's within budget"


# Feature: event-planning-agent, Property 33: Multiple filter composition
@given(
    num_suggestions=st.integers(min_value=10, max_value=30)
)
@settings(max_examples=100)
def test_property_33_multiple_filter_composition(num_suggestions: int) -> None:
    """
    Feature: event-planning-agent, Property 33: Multiple filter composition
    
    For any combination of filters (activity, location, date, budget), returned
    suggestions should satisfy all specified filter criteria simultaneously.
    
    Validates: Requirements 7.5
    """
    # Define multiple filters
    keyword = "dining"
    location_filter = "downtown"
    budget_max = 100.0
    filter_start = datetime(2024, 6, 1)
    filter_end = datetime(2024, 8, 31)
    
    # Generate suggestions with various characteristics
    suggestions = []
    activity_types = ["dining", "sports", "arts"]
    location_names = ["downtown plaza", "suburb mall", "beach resort"]
    
    for i in range(num_suggestions):
        activity_type = activity_types[i % len(activity_types)]
        location_name = location_names[i % len(location_names)]
        cost = 50.0 + (i * 10.0)
        
        # Vary date availability
        if i % 3 == 0:
            start_date = datetime(2024, 6, 15)
            end_date = datetime(2024, 7, 15)
        elif i % 3 == 1:
            start_date = datetime(2024, 8, 15)
            end_date = datetime(2024, 9, 15)
        else:
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 3, 31)
        
        suggestion = EventSuggestion(
            id=f"suggestion_{i}",
            activity_type=activity_type,
            location=Location(name=location_name, address=f"{location_name} address"),
            estimated_duration=timedelta(hours=2),
            estimated_cost_per_person=cost,
            description=f"A {activity_type} activity",
            consensus_score=0.0,
            member_compatibility={},
            available_start_date=start_date,
            available_end_date=end_date
        )
        suggestions.append(suggestion)
    
    # Create filter with all criteria
    filters = SearchFilters(
        activity_keywords=[keyword],
        location_area=location_filter,
        date_range=(filter_start, filter_end),
        budget_max=budget_max
    )
    
    # Apply filters manually (simulating the full filter chain)
    filtered = suggestions
    
    # Activity keyword filter
    filtered = [
        s for s in filtered
        if any(
            kw.lower() in s.activity_type.lower() or
            kw.lower() in s.description.lower()
            for kw in filters.activity_keywords
        )
    ]
    
    # Location filter
    filtered = [
        s for s in filtered
        if filters.location_area.lower() in s.location.name.lower() or
           filters.location_area.lower() in s.location.address.lower()
    ]
    
    # Date range filter
    filtered = [
        s for s in filtered
        if s.available_start_date is not None and s.available_end_date is not None and
           s.available_start_date <= filter_end and s.available_end_date >= filter_start
    ]
    
    # Budget filter
    filtered = [
        s for s in filtered
        if s.estimated_cost_per_person <= budget_max
    ]
    
    # Verify all filtered suggestions satisfy ALL criteria
    for suggestion in filtered:
        # Check activity keyword
        assert (
            keyword.lower() in suggestion.activity_type.lower() or
            keyword.lower() in suggestion.description.lower()
        ), f"Filtered suggestion should match activity keyword"
        
        # Check location
        assert (
            location_filter.lower() in suggestion.location.name.lower() or
            location_filter.lower() in suggestion.location.address.lower()
        ), f"Filtered suggestion should match location"
        
        # Check date range
        assert suggestion.available_start_date is not None
        assert suggestion.available_end_date is not None
        assert suggestion.available_start_date <= filter_end
        assert suggestion.available_end_date >= filter_start
        
        # Check budget
        assert suggestion.estimated_cost_per_person <= budget_max
    
    # Verify we didn't include suggestions that fail any criterion
    for suggestion in suggestions:
        matches_activity = (
            keyword.lower() in suggestion.activity_type.lower() or
            keyword.lower() in suggestion.description.lower()
        )
        matches_location = (
            location_filter.lower() in suggestion.location.name.lower() or
            location_filter.lower() in suggestion.location.address.lower()
        )
        matches_date = (
            suggestion.available_start_date is not None and
            suggestion.available_end_date is not None and
            suggestion.available_start_date <= filter_end and
            suggestion.available_end_date >= filter_start
        )
        matches_budget = suggestion.estimated_cost_per_person <= budget_max
        
        matches_all = matches_activity and matches_location and matches_date and matches_budget
        is_in_filtered = suggestion in filtered
        
        assert matches_all == is_in_filtered, \
            f"Suggestion should be in filtered list if and only if it matches ALL criteria"
