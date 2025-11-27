# Firestore Repositories for Group Coordination

This document describes the Firestore-based persistence layer for the group coordination feature.

## Overview

The group coordination feature uses Google Cloud Firestore for persistent storage of planning sessions, participants, venues, votes, comments, and itinerary items. The data is organized in a hierarchical structure using collections and subcollections.

## Data Structure

```
planning_sessions (collection)
├── {session_id} (document)
│   ├── participants (subcollection)
│   │   └── {participant_id} (document)
│   ├── venues (subcollection)
│   │   └── {venue_id} (document)
│   │       ├── votes (subcollection)
│   │       │   └── {vote_id} (document)
│   │       └── comments (subcollection)
│   │           └── {comment_id} (document)
│   └── itinerary (subcollection)
│       └── {item_id} (document)
```

## Required Firestore Indexes

For optimal query performance, create the following composite indexes:

### 1. Planning Sessions by Invite Token
- Collection: `planning_sessions`
- Fields:
  - `invite_token` (Ascending)
- Query scope: Collection

### 2. Inactive Sessions for Archival
- Collection: `planning_sessions`
- Fields:
  - `updated_at` (Ascending)
  - `status` (Ascending)
- Query scope: Collection

### 3. Votes by Participant (Collection Group)
- Collection: `votes` (Collection group)
- Fields:
  - `session_id` (Ascending)
  - `participant_id` (Ascending)
- Query scope: Collection group

### 4. Comments by Participant (Collection Group)
- Collection: `comments` (Collection group)
- Fields:
  - `session_id` (Ascending)
  - `participant_id` (Ascending)
  - `created_at` (Ascending)
- Query scope: Collection group

### 5. Comments Ordered by Time
- Collection: `comments` (subcollection under venues)
- Fields:
  - `created_at` (Ascending)
- Query scope: Collection

### 6. Itinerary Items Ordered by Time
- Collection: `itinerary` (subcollection under sessions)
- Fields:
  - `scheduled_time` (Ascending)
- Query scope: Collection

## Creating Indexes

You can create these indexes using the Firebase Console or the `gcloud` CLI:

```bash
# Example: Create index for invite_token lookup
gcloud firestore indexes composite create \
  --collection-group=planning_sessions \
  --field-config field-path=invite_token,order=ascending \
  --project=YOUR_PROJECT_ID

# Example: Create collection group index for votes
gcloud firestore indexes composite create \
  --collection-group=votes \
  --field-config field-path=session_id,order=ascending \
  --field-config field-path=participant_id,order=ascending \
  --project=YOUR_PROJECT_ID
```

Alternatively, Firestore will suggest creating indexes when you run queries that require them.

## Repository Usage

### PlanningSessionRepository

```python
from app.event_planning.repositories import PlanningSessionRepository
from app.event_planning.models.planning_session import PlanningSession, Participant

# Initialize repository
repo = PlanningSessionRepository()

# Create a session
session = PlanningSession(...)
repo.create(session)

# Get by ID
session = repo.get(session_id)

# Get by invite token
session = repo.get_by_invite_token(invite_token)

# Update session
session.status = SessionStatus.FINALIZED
repo.update(session)

# Add participant
participant = Participant(...)
repo.add_participant(session_id, participant)

# Get participants
participants = repo.get_participants(session_id)

# Archive inactive sessions
archived_count = repo.archive_inactive_sessions(days_inactive=30)
```

### VenueRepository

```python
from app.event_planning.repositories import VenueRepository
from app.event_planning.models.venue import VenueOption

repo = VenueRepository()

# Create venue
venue = VenueOption(...)
repo.create(venue)

# Get venue
venue = repo.get(session_id, venue_id)

# List venues for session
venues = repo.list_for_session(session_id)
```

### VoteRepository

```python
from app.event_planning.repositories import VoteRepository
from app.event_planning.models.venue import Vote, VoteType

repo = VoteRepository()

# Create vote
vote = Vote(...)
repo.create(vote)

# Get vote by participant (check if already voted)
existing_vote = repo.get_by_participant(session_id, venue_id, participant_id)

# Update vote
if existing_vote:
    existing_vote.vote_type = VoteType.UPVOTE
    repo.update(existing_vote)

# List votes for venue
votes = repo.list_for_venue(session_id, venue_id)

# List all votes by participant
participant_votes = repo.list_for_participant(session_id, participant_id)
```

### CommentRepository

```python
from app.event_planning.repositories import CommentRepository
from app.event_planning.models.itinerary import Comment

repo = CommentRepository()

# Create comment
comment = Comment(...)
repo.create(comment)

# List comments for venue (chronologically ordered)
comments = repo.list_for_venue(session_id, venue_id)

# List comments by participant
participant_comments = repo.list_for_participant(session_id, participant_id)
```

### ItineraryRepository

```python
from app.event_planning.repositories import ItineraryRepository
from app.event_planning.models.itinerary import ItineraryItem

repo = ItineraryRepository()

# Create itinerary item
item = ItineraryItem(...)
repo.create(item)

# List itinerary (chronologically ordered)
itinerary = repo.list_for_session(session_id)

# Delete item
repo.delete(session_id, item_id)
```

## Session Archival

The system includes automatic archival of inactive sessions.

### Using the Archival Service

```python
from app.event_planning.services.session_archival_service import SessionArchivalService

service = SessionArchivalService()

# Archive sessions inactive for 30 days
archived_count = service.archive_inactive_sessions(days_inactive=30)

# Get statistics
stats = service.get_archival_stats()
print(f"Active: {stats['active_sessions']}")
print(f"Archived: {stats['archived_sessions']}")
```

### Using the CLI Script

```bash
# Archive sessions inactive for 30 days
python scripts/archive_sessions.py --days 30

# Show statistics only
python scripts/archive_sessions.py --stats-only
```

### Scheduling Archival

For production, schedule the archival to run periodically using:

1. **Cloud Scheduler + Cloud Functions**:
   ```python
   # cloud_function.py
   from app.event_planning.services.session_archival_service import run_archival
   
   def archive_sessions(request):
       run_archival(days_inactive=30)
       return "OK", 200
   ```

2. **Cloud Scheduler + Cloud Run**:
   Create a Cloud Run job that runs the archival script on a schedule.

3. **Cron Job**:
   ```cron
   # Run daily at 2 AM
   0 2 * * * cd /path/to/project && python scripts/archive_sessions.py --days 30
   ```

## Environment Setup

Ensure you have the required dependencies:

```bash
# Install dependencies
uv sync

# Set up Google Cloud credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Or use gcloud auth
gcloud auth application-default login
```

## Testing

The repositories can be tested using the Firestore emulator:

```bash
# Start Firestore emulator
gcloud emulators firestore start

# In another terminal, set environment variable
export FIRESTORE_EMULATOR_HOST=localhost:8080

# Run tests
pytest tests/property/test_properties_group_coordination.py
```

## Error Handling

All repositories include comprehensive error handling:

- `DuplicateEntityError`: Attempting to create an entity that already exists
- `EntityNotFoundError`: Attempting to update/delete a non-existent entity
- `ValidationError`: Entity data fails validation
- `FileStorageError`: Firestore operation fails

All errors are logged using the error logging system.

## Performance Considerations

1. **Batch Operations**: For bulk operations, consider using Firestore batch writes
2. **Caching**: Consider implementing caching for frequently accessed sessions
3. **Pagination**: For large result sets, implement pagination using Firestore cursors
4. **Indexes**: Ensure all required indexes are created before deploying to production

## Migration from JSON Storage

If migrating from the JSON file-based storage:

1. Read entities from JSON files using existing repositories
2. Create corresponding Firestore documents using new repositories
3. Verify data integrity
4. Switch application to use Firestore repositories
5. Archive or delete JSON files

Example migration script:

```python
from app.event_planning.repositories import (
    JsonFileRepository,
    PlanningSessionRepository
)

# Read from JSON
json_repo = JsonFileRepository("data", "planning_sessions")
sessions = json_repo.list_all()

# Write to Firestore
firestore_repo = PlanningSessionRepository()
for session in sessions:
    firestore_repo.create(session)
```
