# Error Handling Documentation

## Overview

The Event Planning Agent implements comprehensive error handling with custom exception classes, consistent error responses, and structured logging.

## Exception Hierarchy

All custom exceptions inherit from `EventPlanningError`, which provides:
- Machine-readable error codes
- Human-readable error messages
- Additional error details
- Timestamp tracking
- Structured error response format

### Exception Categories

#### 1. Validation Errors (`ValidationError`)

Raised when input data fails validation:

- `InvalidUserDataError` - Invalid user data (missing name, invalid email, etc.)
- `InvalidGroupDataError` - Invalid group data (empty member list, etc.)
- `InvalidEventDataError` - Invalid event data (invalid times, missing fields, etc.)
- `InvalidPreferenceDataError` - Invalid preference data (negative budget, invalid weights, etc.)
- `InvalidAvailabilityDataError` - Invalid availability data (invalid time ranges, etc.)
- `InvalidFeedbackDataError` - Invalid feedback data (rating out of range, etc.)

**Example:**
```python
from app.event_planning.exceptions import InvalidUserDataError

if not user.email or "@" not in user.email:
    raise InvalidUserDataError("email must be valid", field="email")
```

#### 2. Business Logic Errors (`BusinessLogicError`)

Raised when business rules are violated:

- `EntityNotFoundError` - Base class for not found errors
  - `UserNotFoundError` - User not found
  - `GroupNotFoundError` - Group not found
  - `EventNotFoundError` - Event not found
  - `FeedbackNotFoundError` - Feedback not found
- `MembershipError` - Base class for membership errors
  - `AlreadyMemberError` - User is already a group member
  - `NotMemberError` - User is not a group member
- `NotParticipantError` - User was not a participant in an event
- `InsufficientAvailabilityError` - No availability for proposed event time
- `SchedulingConflictError` - Scheduling conflicts exist
- `InvalidEventStatusError` - Operation invalid for current event status

**Example:**
```python
from app.event_planning.exceptions import EventNotFoundError

event = event_repo.get(event_id)
if event is None:
    raise EventNotFoundError(event_id)
```

#### 3. Data Integrity Errors (`DataIntegrityError`)

Raised when data integrity is compromised:

- `DuplicateEntityError` - Entity with duplicate ID already exists
- `OrphanedReferenceError` - Entity references non-existent entity
- `ConcurrentModificationError` - Concurrent modification conflict

**Example:**
```python
from app.event_planning.exceptions import DuplicateEntityError

if file_path.exists():
    raise DuplicateEntityError("User", user_id)
```

#### 4. Storage Errors (`StorageError`)

Raised when storage operations fail:

- `FileStorageError` - File storage operation failed

**Example:**
```python
from app.event_planning.exceptions import FileStorageError

try:
    with open(file_path, 'w') as f:
        json.dump(data, f)
except IOError as e:
    raise FileStorageError(f"Failed to write file: {str(e)}", str(file_path))
```

## Error Logging

The `error_logging` module provides structured logging utilities:

### Basic Error Logging

```python
from app.event_planning.error_logging import log_error

try:
    # Some operation
    pass
except Exception as e:
    log_error(e, context={"operation": "create_user", "user_id": user_id})
    raise
```

### Specialized Logging Functions

```python
from app.event_planning.error_logging import (
    log_validation_error,
    log_business_logic_error,
    log_data_integrity_error,
    log_storage_error
)

# Log validation error
log_validation_error(error, "User", {"id": user_id})

# Log business logic error
log_business_logic_error(error, "finalize_event", {"event_id": event_id})

# Log data integrity error
log_data_integrity_error(error, "create", {"entity_type": "User", "entity_id": user_id})

# Log storage error
log_storage_error(error, "write", "/path/to/file")
```

### Configure Logging

```python
from app.event_planning.error_logging import configure_logging

# Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
configure_logging(log_level="INFO")
```

## Error Response Format

All exceptions can be converted to a consistent dictionary format:

```python
error = EventNotFoundError("event123")
error_dict = error.to_dict()

# Returns:
# {
#     "error_code": "EVENT_NOT_FOUND",
#     "message": "Event with id event123 does not exist",
#     "details": {
#         "entity_type": "Event",
#         "entity_id": "event123"
#     },
#     "timestamp": "2025-01-15T10:30:00.000000"
# }
```

## Best Practices

### 1. Use Specific Exception Classes

Always use the most specific exception class available:

```python
# Good
raise UserNotFoundError(user_id)

# Avoid
raise ValueError(f"User with id {user_id} does not exist")
```

### 2. Include Context in Error Details

Provide relevant context in error details:

```python
raise InsufficientAvailabilityError(
    "Event time must fall within at least one participant's availability window",
    details={
        "event_id": event_id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "participant_ids": participant_ids,
    }
)
```

### 3. Log Errors Before Raising

Always log errors before raising them:

```python
error = EventNotFoundError(event_id)
log_business_logic_error(error, "finalize_event", {"event_id": event_id})
raise error
```

### 4. Handle Errors at Appropriate Layers

- **Repository Layer**: Raise storage and data integrity errors
- **Service Layer**: Raise business logic and validation errors
- **API/CLI Layer**: Catch and format errors for user display

### 5. Preserve Error Context

When catching and re-raising errors, preserve the original context:

```python
try:
    entity.validate()
except ValueError as e:
    error = ValidationError(str(e), details={"entity_id": entity.id})
    log_validation_error(error, type(entity).__name__, {"id": entity.id})
    raise error
```

## Testing Error Handling

When writing tests, use the specific exception classes:

```python
import pytest
from app.event_planning.exceptions import EventNotFoundError

def test_finalize_nonexistent_event_fails(event_service):
    """Test that finalizing a non-existent event fails."""
    with pytest.raises(EventNotFoundError, match="does not exist"):
        event_service.finalize_event("nonexistent")
```

## Error Codes Reference

| Error Code | Exception Class | Description |
|------------|----------------|-------------|
| `VALIDATION_ERROR` | `ValidationError` | Generic validation error |
| `INVALID_USER_DATA` | `InvalidUserDataError` | Invalid user data |
| `INVALID_GROUP_DATA` | `InvalidGroupDataError` | Invalid group data |
| `INVALID_EVENT_DATA` | `InvalidEventDataError` | Invalid event data |
| `INVALID_PREFERENCE_DATA` | `InvalidPreferenceDataError` | Invalid preference data |
| `INVALID_AVAILABILITY_DATA` | `InvalidAvailabilityDataError` | Invalid availability data |
| `INVALID_FEEDBACK_DATA` | `InvalidFeedbackDataError` | Invalid feedback data |
| `ENTITY_NOT_FOUND` | `EntityNotFoundError` | Generic entity not found |
| `USER_NOT_FOUND` | `UserNotFoundError` | User not found |
| `GROUP_NOT_FOUND` | `GroupNotFoundError` | Group not found |
| `EVENT_NOT_FOUND` | `EventNotFoundError` | Event not found |
| `FEEDBACK_NOT_FOUND` | `FeedbackNotFoundError` | Feedback not found |
| `MEMBERSHIP_ERROR` | `MembershipError` | Generic membership error |
| `ALREADY_MEMBER` | `AlreadyMemberError` | User already a member |
| `NOT_MEMBER` | `NotMemberError` | User not a member |
| `NOT_PARTICIPANT` | `NotParticipantError` | User not a participant |
| `INSUFFICIENT_AVAILABILITY` | `InsufficientAvailabilityError` | Insufficient availability |
| `SCHEDULING_CONFLICT` | `SchedulingConflictError` | Scheduling conflict |
| `INVALID_EVENT_STATUS` | `InvalidEventStatusError` | Invalid event status |
| `DUPLICATE_ENTITY` | `DuplicateEntityError` | Duplicate entity |
| `ORPHANED_REFERENCE` | `OrphanedReferenceError` | Orphaned reference |
| `CONCURRENT_MODIFICATION` | `ConcurrentModificationError` | Concurrent modification |
| `STORAGE_ERROR` | `StorageError` | Generic storage error |
| `FILE_STORAGE_ERROR` | `FileStorageError` | File storage error |
