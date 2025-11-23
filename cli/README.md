# Event Planning Agent CLI

A command-line interface for the Event Planning Agent that helps you plan events with your friends.

## Installation

The CLI is installed automatically when you install the project:

```bash
uv sync
```

## Usage

### Interactive Menu (Recommended)

The easiest way to use the CLI is with the interactive menu that uses names instead of IDs:

```bash
uv run python cli/interactive_menu.py
```

This provides a user-friendly menu where you can:
- Select users, groups, and events by name or number
- Create and manage everything without remembering IDs
- Navigate through intuitive menus

### Command-Line Interface

For scripting and automation, use the command-based CLI:

```bash
uv run event-planner --help
```

### User Management

Create and manage users:

```bash
# Create a new user
uv run event-planner user create --name "Alice" --email "alice@example.com"

# List all users
uv run event-planner user list

# Show user details
uv run event-planner user show <user-id>

# Update user preferences
uv run event-planner user update-preferences <user-id> \
  --activity "hiking:0.8" \
  --activity "dining:0.6" \
  --budget 50.0 \
  --location "Downtown" \
  --dietary "vegetarian"

# Add availability window
uv run event-planner user add-availability <user-id> \
  --start "2025-01-20T18:00:00" \
  --end "2025-01-20T22:00:00" \
  --timezone "America/New_York"
```

### Group Management

Create and manage friend groups:

```bash
# Create a new group
uv run event-planner group create \
  --name "Weekend Warriors" \
  --creator <creator-user-id> \
  --member <user-id-1> \
  --member <user-id-2>

# List all groups
uv run event-planner group list

# List groups for a specific user
uv run event-planner group list --user <user-id>

# Show group details
uv run event-planner group show <group-id>

# Add a member to a group
uv run event-planner group add-member <group-id> <user-id>

# Remove a member from a group
uv run event-planner group remove-member <group-id> <user-id>
```

### Event Planning

Plan and manage events:

```bash
# Plan an event (requires a suggestions JSON file)
uv run event-planner event plan <group-id> \
  --suggestions-file suggestions.json

# Create an event from a suggestion
uv run event-planner event create \
  --suggestion-id <suggestion-id> \
  --suggestions-file suggestions.json \
  --name "Hiking Trip" \
  --start "2025-01-25T10:00:00" \
  --participant <user-id-1> \
  --participant <user-id-2>

# Finalize a pending event
uv run event-planner event finalize <event-id>

# Cancel an event
uv run event-planner event cancel <event-id>

# List all events
uv run event-planner event list

# List events for a specific user
uv run event-planner event list --user <user-id>

# Show event details
uv run event-planner event show <event-id>

# Check for scheduling conflicts
uv run event-planner event check-conflicts <event-id>
```

### Feedback

Submit and view feedback:

```bash
# Submit feedback for an event
uv run event-planner feedback submit <event-id> <user-id> \
  --rating 5 \
  --comments "Great event!"

# List all feedback
uv run event-planner feedback list

# List feedback for a specific event
uv run event-planner feedback list --event <event-id>

# List feedback from a specific user
uv run event-planner feedback list --user <user-id>
```

### Search and Filtering

Search for event suggestions:

```bash
# Search suggestions with filters
uv run event-planner search suggestions <group-id> \
  --suggestions-file suggestions.json \
  --activity "hiking" \
  --location "Mountains" \
  --budget 30.0
```

### Scheduling

Find optimal time slots:

```bash
# Find available time slots for a group
uv run event-planner schedule find-time <group-id> --duration 2
```

## Suggestions File Format

The suggestions file should be a JSON array of event suggestions:

```json
[
  {
    "id": "suggestion-1",
    "activity_type": "hiking",
    "location": {
      "name": "Mountain Trail",
      "address": "123 Trail Rd",
      "latitude": 40.7128,
      "longitude": -74.0060
    },
    "estimated_duration": 7200,
    "estimated_cost_per_person": 25.0,
    "description": "Beautiful mountain hiking trail",
    "consensus_score": 0.0,
    "member_compatibility": {},
    "available_start_date": "2025-01-20T00:00:00",
    "available_end_date": "2025-01-31T23:59:59"
  }
]
```

## Data Storage

By default, data is stored in the `data/` directory. You can specify a different directory:

```bash
uv run event-planner --storage-dir /path/to/data user list
```

## Examples

### Complete Workflow

```bash
# 1. Create users
uv run event-planner user create --name "Alice" --email "alice@example.com"
uv run event-planner user create --name "Bob" --email "bob@example.com"

# 2. Add availability
uv run event-planner user add-availability <alice-id> \
  --start "2025-01-25T18:00:00" \
  --end "2025-01-25T22:00:00"

# 3. Create a group
uv run event-planner group create \
  --name "Dinner Club" \
  --creator <alice-id> \
  --member <bob-id>

# 4. Plan an event
uv run event-planner event plan <group-id> \
  --suggestions-file suggestions.json

# 5. Create and finalize the event
uv run event-planner event create \
  --suggestion-id <suggestion-id> \
  --suggestions-file suggestions.json \
  --name "Dinner at Italian Restaurant" \
  --start "2025-01-25T19:00:00" \
  --participant <alice-id> \
  --participant <bob-id>

uv run event-planner event finalize <event-id>

# 6. Submit feedback
uv run event-planner feedback submit <event-id> <alice-id> \
  --rating 5 \
  --comments "Amazing dinner!"
```
