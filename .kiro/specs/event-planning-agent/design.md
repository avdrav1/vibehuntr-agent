# Design Document

## Overview

The Event Planning Agent is an AI-powered system that helps users discover, plan, and coordinate social events with friend groups. The system uses a multi-layered architecture combining user preference modeling, constraint satisfaction, and collaborative filtering to generate personalized event suggestions. The agent learns from user feedback to continuously improve recommendations while respecting individual constraints like availability, budget, and accessibility needs.

The system is designed as a modular application with clear separation between data storage, business logic, and user interaction layers. It employs a recommendation engine that balances individual preferences with group consensus, and a scheduling optimizer that finds optimal time slots considering multiple participants' availability.

## Architecture

The system follows a layered architecture pattern:

```
┌─────────────────────────────────────────┐
│         User Interface Layer            │
│  (CLI/API endpoints for interaction)    │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         Application Layer               │
│  - Event Planning Service               │
│  - Recommendation Engine                │
│  - Scheduling Optimizer                 │
│  - Feedback Processor                   │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         Domain Layer                    │
│  - User Management                      │
│  - Group Management                     │
│  - Event Management                     │
│  - Preference Management                │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         Data Layer                      │
│  - Repository Interfaces                │
│  - Data Models                          │
│  - Storage Backend (JSON/SQLite)        │
└─────────────────────────────────────────┘
```

### Key Architectural Decisions

1. **Repository Pattern**: Abstracts data access to allow easy switching between storage backends
2. **Service Layer**: Encapsulates business logic and orchestrates domain operations
3. **Immutable Events**: Once finalized, events are immutable; changes create new versions
4. **Preference Learning**: Feedback updates preference weights using a simple weighted average algorithm
5. **Consensus Scoring**: Uses a normalized scoring function that balances individual preferences

## Components and Interfaces

### User Management Component

Handles user creation, authentication, and profile management.

```python
class User:
    id: str
    name: str
    email: str
    preference_profile: PreferenceProfile
    availability_windows: List[AvailabilityWindow]

class UserRepository:
    def create_user(user: User) -> User
    def get_user(user_id: str) -> Optional[User]
    def update_user(user: User) -> User
    def list_users() -> List[User]
```

### Group Management Component

Manages friend groups and membership.

```python
class FriendGroup:
    id: str
    name: str
    member_ids: List[str]
    created_at: datetime
    priority_member_ids: List[str]  # Optional priority members

class GroupRepository:
    def create_group(group: FriendGroup) -> FriendGroup
    def get_group(group_id: str) -> Optional[FriendGroup]
    def update_group(group: FriendGroup) -> FriendGroup
    def get_groups_for_user(user_id: str) -> List[FriendGroup]
    def add_member(group_id: str, user_id: str) -> FriendGroup
    def remove_member(group_id: str, user_id: str) -> FriendGroup
```

### Event Management Component

Handles event creation, updates, and lifecycle management.

```python
class Event:
    id: str
    name: str
    activity_type: str
    location: Location
    start_time: datetime
    end_time: datetime
    participant_ids: List[str]
    status: EventStatus  # PENDING, CONFIRMED, CANCELLED
    budget_per_person: Optional[float]
    description: str

class EventRepository:
    def create_event(event: Event) -> Event
    def get_event(event_id: str) -> Optional[Event]
    def update_event(event: Event) -> Event
    def list_events_for_user(user_id: str) -> List[Event]
    def list_events_for_group(group_id: str) -> List[Event]
```

### Preference Management Component

Stores and manages user preferences and constraints.

```python
class PreferenceProfile:
    user_id: str
    activity_preferences: Dict[str, float]  # activity_type -> weight (0-1)
    budget_max: Optional[float]
    location_preferences: List[str]  # preferred areas/neighborhoods
    dietary_restrictions: List[str]
    accessibility_needs: List[str]
    updated_at: datetime

class AvailabilityWindow:
    user_id: str
    start_time: datetime
    end_time: datetime
    timezone: str
```

### Recommendation Engine

Generates event suggestions based on group preferences.

```python
class EventSuggestion:
    id: str
    activity_type: str
    location: Location
    estimated_duration: timedelta
    estimated_cost_per_person: float
    description: str
    consensus_score: float
    member_compatibility: Dict[str, float]  # user_id -> compatibility score

class RecommendationEngine:
    def generate_suggestions(
        group: FriendGroup,
        users: List[User],
        filters: Optional[SearchFilters] = None
    ) -> List[EventSuggestion]
    
    def calculate_consensus_score(
        suggestion: EventSuggestion,
        users: List[User]
    ) -> float
    
    def rank_suggestions(
        suggestions: List[EventSuggestion]
    ) -> List[EventSuggestion]
```

### Scheduling Optimizer

Finds optimal time slots for events considering participant availability.

```python
class TimeSlot:
    start_time: datetime
    end_time: datetime
    available_member_ids: List[str]
    availability_percentage: float

class SchedulingOptimizer:
    def find_common_availability(
        users: List[User],
        duration: timedelta,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> List[TimeSlot]
    
    def resolve_conflicts(
        event: Event,
        users: List[User],
        priority_member_ids: Optional[List[str]] = None
    ) -> List[TimeSlot]
```

### Feedback Processor

Processes user feedback to improve future recommendations.

```python
class EventFeedback:
    id: str
    event_id: str
    user_id: str
    rating: int  # 1-5 scale
    comments: Optional[str]
    submitted_at: datetime

class FeedbackProcessor:
    def process_feedback(feedback: EventFeedback) -> None
    def update_preference_weights(user_id: str, feedback: EventFeedback) -> None
    def get_feedback_for_event(event_id: str) -> List[EventFeedback]
```

## Data Models

### Core Entities

**User**
- Unique identifier
- Profile information (name, email)
- Embedded preference profile
- List of availability windows

**FriendGroup**
- Unique identifier
- Group name
- List of member user IDs
- Optional priority member IDs
- Creation timestamp

**Event**
- Unique identifier
- Event details (name, type, location, time)
- Participant list
- Status (pending/confirmed/cancelled)
- Budget information
- Description

**PreferenceProfile**
- Associated user ID
- Activity type preferences (weighted)
- Budget constraints
- Location preferences
- Dietary and accessibility requirements
- Last updated timestamp

**EventFeedback**
- Unique identifier
- Associated event and user IDs
- Numerical rating
- Optional text comments
- Submission timestamp

### Relationships

- User → PreferenceProfile (1:1, embedded)
- User → AvailabilityWindow (1:many)
- FriendGroup → User (many:many via member_ids)
- Event → User (many:many via participant_ids)
- Event → EventFeedback (1:many)
- User → EventFeedback (1:many)

### Storage Format

Data will be persisted using JSON files with the following structure:

```
data/
  users/
    {user_id}.json
  groups/
    {group_id}.json
  events/
    {event_id}.json
  feedback/
    {feedback_id}.json
```

Each JSON file contains the serialized object with all its properties. This approach provides simplicity for the initial implementation while maintaining clear data boundaries.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Group Management Properties

**Property 1: Group creation persistence**
*For any* friend group with valid data, creating the group should result in the group being retrievable with the same identifier and member list.
**Validates: Requirements 1.1**

**Property 2: Member addition updates membership**
*For any* friend group and existing user, adding the user to the group should result in the user appearing in the group's member list, and attempting to add a non-existent user should fail validation.
**Validates: Requirements 1.2**

**Property 3: Member removal preserves history**
*For any* friend group with existing events, removing a member should update the group's current membership while historical events still reference the removed member correctly.
**Validates: Requirements 1.3**

**Property 4: User group query completeness**
*For any* user, querying their friend groups should return exactly the set of groups where they are a member—no more, no less.
**Validates: Requirements 1.4**

**Property 5: Member access to group details**
*For any* friend group with multiple members, each member should be able to retrieve the complete group details.
**Validates: Requirements 1.5**

### Preference Management Properties

**Property 6: Availability window round-trip**
*For any* user and valid availability windows, storing the windows and then retrieving them should return equivalent time periods with correct dates, times, and timezones.
**Validates: Requirements 2.1**

**Property 7: Preference profile completeness**
*For any* user and preference profile containing activity types, budget constraints, location preferences, dietary restrictions, and accessibility needs, updating the profile should result in all fields being stored and retrievable.
**Validates: Requirements 2.2, 2.3**

**Property 8: Preference-user association**
*For any* set of users with different preference profiles, each user should retrieve only their own preferences, not those of other users.
**Validates: Requirements 2.4**

**Property 9: Most recent preference retrieval**
*For any* user who updates their preferences multiple times, retrieving their preferences should return the most recently stored version.
**Validates: Requirements 2.5**

### Recommendation Properties

**Property 10: Suggestion relevance to preferences**
*For any* friend group with defined member preferences, generated event suggestions should align with at least some of the stated preferences from the group members.
**Validates: Requirements 3.1**

**Property 11: Consensus score calculation**
*For any* event suggestion and friend group, the suggestion should have a consensus score that mathematically reflects the compatibility with member preferences.
**Validates: Requirements 3.2**

**Property 12: Suggestion ranking by consensus**
*For any* list of event suggestions with different consensus scores, the suggestions should be ordered in descending order by consensus score.
**Validates: Requirements 3.3**

**Property 13: Compatible preference satisfaction**
*For any* friend group where all members have compatible preferences (no conflicts), generated suggestions should satisfy all stated preferences.
**Validates: Requirements 3.4**

**Property 14: Conflict optimization**
*For any* friend group with conflicting member preferences, generated suggestions should maximize the overall consensus score across all members.
**Validates: Requirements 3.5**

### Availability Properties

**Property 15: Availability aggregation completeness**
*For any* friend group, aggregating availability should include availability windows from all members who have provided them.
**Validates: Requirements 4.1**

**Property 16: Common availability identification**
*For any* friend group with overlapping availability windows, the system should correctly identify time slots where all members are available.
**Validates: Requirements 4.2**

**Property 17: Maximum overlap identification**
*For any* friend group with no common availability, the system should identify time slots that maximize the number of available members.
**Validates: Requirements 4.3**

**Property 18: Timezone-aware availability**
*For any* friend group with members in different timezones, availability calculations should correctly account for timezone differences when identifying common time slots.
**Validates: Requirements 4.4**

**Property 19: Incomplete availability reporting**
*For any* friend group where some members have not provided availability, the system should identify and report which members are missing availability data.
**Validates: Requirements 4.5**

### Event Management Properties

**Property 20: Event creation from suggestion**
*For any* event suggestion, creating an event from it should initialize the event with all suggestion details and set the status to pending.
**Validates: Requirements 5.1**

**Property 21: Event finalization status**
*For any* pending event, finalizing it should change the status to confirmed.
**Validates: Requirements 5.2**

**Property 22: Event time validation**
*For any* event with a proposed time, the event should only be created if the time falls within at least one participant's availability window.
**Validates: Requirements 5.3**

**Property 23: Event data persistence**
*For any* finalized event, all event details including time, location, activity type, and participant list should be stored and retrievable.
**Validates: Requirements 5.4**

**Property 24: Event cancellation preservation**
*For any* confirmed event, canceling it should update the status to cancelled while keeping the event record retrievable for historical reference.
**Validates: Requirements 5.5**

### Feedback Properties

**Property 25: Feedback storage completeness**
*For any* completed event and user feedback with rating and optional comments, storing the feedback should result in all fields being retrievable.
**Validates: Requirements 6.1**

**Property 26: Feedback association**
*For any* submitted feedback, it should be correctly associated with both the event and the user who provided it.
**Validates: Requirements 6.2**

**Property 27: Feedback-driven preference learning**
*For any* user who provides feedback on an event, the preference weights for characteristics similar to that event should be adjusted in the direction of the feedback (increased for positive ratings, decreased for negative ratings).
**Validates: Requirements 6.3, 6.4**

**Property 28: Historical feedback incorporation**
*For any* friend group with historical feedback from members, newly generated suggestions should reflect the feedback patterns in their consensus scores and rankings.
**Validates: Requirements 6.5**

### Search and Filtering Properties

**Property 29: Activity keyword filtering**
*For any* search query with activity keywords, returned suggestions should only include those matching the specified keywords.
**Validates: Requirements 7.1**

**Property 30: Location filtering**
*For any* location filter, returned suggestions should only include those within the specified geographic area.
**Validates: Requirements 7.2**

**Property 31: Date range filtering**
*For any* date range filter, returned suggestions should only include those available during the specified time period.
**Validates: Requirements 7.3**

**Property 32: Budget filtering**
*For any* budget filter, returned suggestions should only include those within the specified price range.
**Validates: Requirements 7.4**

**Property 33: Multiple filter composition**
*For any* combination of filters (activity, location, date, budget), returned suggestions should satisfy all specified filter criteria simultaneously.
**Validates: Requirements 7.5**

### Conflict Resolution Properties

**Property 34: Conflict member identification**
*For any* event with a proposed time, if the time conflicts with some members' availability, the system should correctly identify which specific members cannot attend.
**Validates: Requirements 8.1**

**Property 35: Attendance percentage calculation**
*For any* event suggestion and friend group, the displayed attendance percentage should accurately reflect the proportion of members who can attend based on their availability.
**Validates: Requirements 8.2**

**Property 36: Alternative time optimization**
*For any* event with scheduling conflicts, suggested alternative times should have equal or higher member participation percentages than the original time.
**Validates: Requirements 8.3**

**Property 37: Unresolvable conflict options**
*For any* event where conflicts cannot be fully resolved, the system should provide options for both proceeding with partial attendance and rescheduling.
**Validates: Requirements 8.4**

**Property 38: Priority member weighting**
*For any* friend group with designated priority members, conflict resolution should favor time slots where priority members are available over time slots where only non-priority members are available.
**Validates: Requirements 8.5**

## Error Handling

The system will implement comprehensive error handling across all layers:

### Validation Errors

- **Invalid User Data**: Reject user creation with missing required fields (name, email)
- **Invalid Group Data**: Reject group creation with empty member lists or non-existent member IDs
- **Invalid Event Data**: Reject events with invalid times (end before start), missing required fields
- **Invalid Preferences**: Reject preference profiles with invalid budget values (negative numbers)
- **Invalid Availability**: Reject availability windows with invalid time ranges or malformed timezone data

### Business Logic Errors

- **Member Not Found**: Return clear error when attempting to add non-existent user to group
- **Group Not Found**: Return clear error when attempting operations on non-existent groups
- **Event Not Found**: Return clear error when attempting to access non-existent events
- **Insufficient Availability**: Warn when no common availability exists for a group
- **Scheduling Conflicts**: Clearly communicate which members have conflicts and why

### Data Integrity Errors

- **Duplicate IDs**: Prevent creation of entities with duplicate identifiers
- **Orphaned References**: Validate that all referenced entities (users, groups, events) exist
- **Concurrent Modifications**: Handle concurrent updates gracefully (last-write-wins for MVP)

### Error Response Format

All errors will follow a consistent structure:

```python
class ErrorResponse:
    error_code: str
    message: str
    details: Optional[Dict[str, Any]]
    timestamp: datetime
```

## Testing Strategy

The Event Planning Agent will employ a dual testing approach combining unit tests and property-based tests to ensure comprehensive correctness validation.

### Property-Based Testing

Property-based testing will be the primary mechanism for validating the correctness properties defined in this document. We will use **Hypothesis** (Python's property-based testing library) to implement these tests.

**Configuration:**
- Each property-based test will run a minimum of 100 iterations to ensure thorough coverage
- Tests will use Hypothesis's built-in strategies and custom generators for domain objects
- Each test will be tagged with a comment explicitly referencing the correctness property it implements

**Tagging Format:**
```python
# Feature: event-planning-agent, Property 1: Group creation persistence
@given(friend_group=friend_group_strategy())
def test_group_creation_persistence(friend_group):
    # Test implementation
```

**Property Test Coverage:**
- All 38 correctness properties will be implemented as property-based tests
- Each property will have exactly one corresponding property-based test
- Tests will generate random valid inputs to verify properties hold universally
- Custom Hypothesis strategies will be created for: User, FriendGroup, Event, PreferenceProfile, AvailabilityWindow, EventSuggestion, EventFeedback

**Key Property Tests:**
- Round-trip properties for data persistence (Properties 1, 6, 23, 25)
- Invariant properties for data integrity (Properties 3, 8, 26)
- Ordering properties for rankings and sorts (Property 12)
- Filter composition properties (Properties 29-33)
- Optimization properties for scheduling and recommendations (Properties 14, 17, 36)

### Unit Testing

Unit tests will complement property-based tests by covering:

**Specific Examples:**
- Edge cases like empty groups, single-member groups
- Boundary conditions for budget filters (zero, negative values)
- Timezone edge cases (DST transitions, UTC boundaries)
- Date edge cases (leap years, month boundaries)

**Integration Points:**
- Repository layer interactions with storage backend
- Service layer orchestration of multiple domain operations
- Recommendation engine integration with preference data

**Error Conditions:**
- Invalid input validation
- Missing required fields
- Constraint violations
- Not-found scenarios

**Test Organization:**
```
tests/
  unit/
    test_user_management.py
    test_group_management.py
    test_event_management.py
    test_preference_management.py
    test_recommendation_engine.py
    test_scheduling_optimizer.py
    test_feedback_processor.py
  property/
    test_properties_group.py
    test_properties_preference.py
    test_properties_recommendation.py
    test_properties_availability.py
    test_properties_event.py
    test_properties_feedback.py
    test_properties_search.py
    test_properties_conflict.py
```

### Testing Principles

1. **Implementation-First Development**: Implement features before writing corresponding tests
2. **Property Tests for Universal Behavior**: Use property-based tests to verify behavior across all valid inputs
3. **Unit Tests for Specific Cases**: Use unit tests for concrete examples and edge cases
4. **Complementary Coverage**: Both test types work together—unit tests catch specific bugs, property tests verify general correctness
5. **Minimal Mocking**: Prefer testing real functionality over mocked dependencies where practical
6. **Clear Test Names**: Test names should clearly describe what is being tested and why

## Implementation Notes

### Recommendation Algorithm

The consensus scoring algorithm will use a weighted average approach:

1. For each suggestion, calculate individual compatibility scores for each member
2. Compatibility score = weighted sum of (preference_weight × feature_match)
3. Consensus score = average of all member compatibility scores
4. Apply priority member weighting if applicable (multiply priority member scores by 1.5)

### Scheduling Algorithm

The availability optimization will use an interval intersection approach:

1. Convert all availability windows to a common timezone (UTC)
2. For each potential time slot, count how many members are available
3. Rank time slots by availability count
4. Return top N time slots with availability percentage

### Feedback Learning

Preference weight updates will use exponential moving average:

1. Extract event characteristics (activity_type, location_area, price_range)
2. For positive feedback: new_weight = old_weight × 0.9 + 0.1 × 1.0
3. For negative feedback: new_weight = old_weight × 0.9 + 0.1 × 0.0
4. Normalize weights to sum to 1.0 across all activity types

### Storage Implementation

Initial implementation will use JSON file storage:
- Simple, human-readable format
- Easy to debug and inspect
- Sufficient for MVP with small datasets
- Can be migrated to SQLite or PostgreSQL later if needed

### Future Enhancements

Potential improvements for future iterations:
- External API integration for real event data (Eventbrite, Meetup, etc.)
- Machine learning models for better preference prediction
- Real-time notifications for event updates
- Calendar integration (Google Calendar, iCal)
- Cost splitting and payment tracking
- Weather-aware suggestions
- Transportation and travel time considerations
