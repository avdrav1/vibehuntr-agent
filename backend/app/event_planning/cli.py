"""Command-line interface for the Event Planning Agent.

This module provides a CLI for interacting with the event planning system,
including user management, group management, event planning, and feedback.
"""

import click
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from app.event_planning.services.event_planning_service import EventPlanningService
from app.event_planning.repositories.user_repository import UserRepository
from app.event_planning.repositories.group_repository import GroupRepository
from app.event_planning.repositories.event_repository import EventRepository
from app.event_planning.repositories.feedback_repository import FeedbackRepository
from app.event_planning.models.suggestion import EventSuggestion
from app.event_planning.models.event import Location


# Global service instance
_service: Optional[EventPlanningService] = None


def get_service(storage_dir: str = "data") -> EventPlanningService:
    """Get or create the event planning service instance."""
    global _service
    if _service is None:
        # Initialize repositories
        user_repo = UserRepository(storage_dir)
        group_repo = GroupRepository(storage_dir)
        event_repo = EventRepository(storage_dir)
        feedback_repo = FeedbackRepository(storage_dir)
        
        # Create service
        _service = EventPlanningService(
            user_repository=user_repo,
            group_repository=group_repo,
            event_repository=event_repo,
            feedback_repository=feedback_repo,
            storage_dir=storage_dir
        )
    return _service


@click.group()
@click.option('--storage-dir', default='data', help='Directory for data storage')
@click.pass_context
def cli(ctx, storage_dir):
    """Event Planning Agent - Plan events with your friends!"""
    ctx.ensure_object(dict)
    ctx.obj['storage_dir'] = storage_dir
    # Initialize service
    get_service(storage_dir)


# ============================================================================
# User Management Commands
# ============================================================================

@cli.group()
def user():
    """Manage users."""
    pass


@user.command('create')
@click.option('--name', required=True, help='User name')
@click.option('--email', required=True, help='User email')
@click.pass_context
def create_user(ctx, name, email):
    """Create a new user."""
    try:
        service = get_service(ctx.obj['storage_dir'])
        user = service.create_user(name=name, email=email)
        click.echo(f"✓ User created successfully!")
        click.echo(f"  ID: {user.id}")
        click.echo(f"  Name: {user.name}")
        click.echo(f"  Email: {user.email}")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@user.command('list')
@click.pass_context
def list_users(ctx):
    """List all users."""
    try:
        service = get_service(ctx.obj['storage_dir'])
        users = service.user_repo.list()
        
        if not users:
            click.echo("No users found.")
            return
        
        click.echo(f"Found {len(users)} user(s):")
        for user in users:
            click.echo(f"  • {user.name} ({user.email}) - ID: {user.id}")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@user.command('show')
@click.argument('user_id')
@click.pass_context
def show_user(ctx, user_id):
    """Show user details."""
    try:
        service = get_service(ctx.obj['storage_dir'])
        user = service.user_repo.get(user_id)
        
        if not user:
            click.echo(f"✗ User {user_id} not found.", err=True)
            raise click.Abort()
        
        click.echo(f"User: {user.name}")
        click.echo(f"  ID: {user.id}")
        click.echo(f"  Email: {user.email}")
        click.echo(f"  Preferences:")
        
        profile = user.preference_profile
        if profile.activity_preferences:
            click.echo(f"    Activities: {profile.activity_preferences}")
        if profile.budget_max:
            click.echo(f"    Max Budget: ${profile.budget_max}")
        if profile.location_preferences:
            click.echo(f"    Locations: {', '.join(profile.location_preferences)}")
        if profile.dietary_restrictions:
            click.echo(f"    Dietary: {', '.join(profile.dietary_restrictions)}")
        if profile.accessibility_needs:
            click.echo(f"    Accessibility: {', '.join(profile.accessibility_needs)}")
        
        if user.availability_windows:
            click.echo(f"  Availability ({len(user.availability_windows)} window(s)):")
            for window in user.availability_windows:
                click.echo(f"    • {window.start_time} to {window.end_time} ({window.timezone})")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@user.command('update-preferences')
@click.argument('user_id')
@click.option('--activity', multiple=True, help='Activity preference (format: type:weight, e.g., hiking:0.8)')
@click.option('--budget', type=float, help='Maximum budget')
@click.option('--location', multiple=True, help='Preferred location')
@click.option('--dietary', multiple=True, help='Dietary restriction')
@click.option('--accessibility', multiple=True, help='Accessibility need')
@click.pass_context
def update_preferences(ctx, user_id, activity, budget, location, dietary, accessibility):
    """Update user preferences."""
    try:
        service = get_service(ctx.obj['storage_dir'])
        
        # Parse activity preferences
        activity_prefs = None
        if activity:
            activity_prefs = {}
            for pref in activity:
                if ':' not in pref:
                    click.echo(f"✗ Invalid activity format: {pref}. Use type:weight", err=True)
                    raise click.Abort()
                activity_type, weight = pref.split(':', 1)
                activity_prefs[activity_type] = float(weight)
        
        user = service.update_user_preferences(
            user_id=user_id,
            activity_preferences=activity_prefs,
            budget_max=budget,
            location_preferences=list(location) if location else None,
            dietary_restrictions=list(dietary) if dietary else None,
            accessibility_needs=list(accessibility) if accessibility else None
        )
        
        click.echo(f"✓ Preferences updated for {user.name}")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@user.command('add-availability')
@click.argument('user_id')
@click.option('--start', required=True, help='Start time (ISO format: YYYY-MM-DDTHH:MM:SS)')
@click.option('--end', required=True, help='End time (ISO format: YYYY-MM-DDTHH:MM:SS)')
@click.option('--timezone', default='UTC', help='Timezone (default: UTC)')
@click.pass_context
def add_availability(ctx, user_id, start, end, timezone):
    """Add availability window for a user."""
    try:
        service = get_service(ctx.obj['storage_dir'])
        
        start_time = datetime.fromisoformat(start)
        end_time = datetime.fromisoformat(end)
        
        user = service.add_user_availability(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            timezone=timezone
        )
        
        click.echo(f"✓ Availability added for {user.name}")
        click.echo(f"  {start_time} to {end_time} ({timezone})")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


# ============================================================================
# Group Management Commands
# ============================================================================

@cli.group()
def group():
    """Manage friend groups."""
    pass


@group.command('create')
@click.option('--name', required=True, help='Group name')
@click.option('--creator', required=True, help='Creator user ID')
@click.option('--member', multiple=True, help='Additional member user IDs')
@click.option('--priority', multiple=True, help='Priority member user IDs')
@click.pass_context
def create_group(ctx, name, creator, member, priority):
    """Create a new friend group."""
    try:
        service = get_service(ctx.obj['storage_dir'])
        
        group = service.create_group(
            name=name,
            creator_id=creator,
            member_ids=list(member) if member else None,
            priority_member_ids=list(priority) if priority else None
        )
        
        click.echo(f"✓ Group created successfully!")
        click.echo(f"  ID: {group.id}")
        click.echo(f"  Name: {group.name}")
        click.echo(f"  Members: {len(group.member_ids)}")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@group.command('list')
@click.option('--user', help='Filter by user ID')
@click.pass_context
def list_groups(ctx, user):
    """List all groups or groups for a specific user."""
    try:
        service = get_service(ctx.obj['storage_dir'])
        
        if user:
            groups = service.get_user_groups(user)
            click.echo(f"Groups for user {user}:")
        else:
            groups = service.group_repo.list()
            click.echo("All groups:")
        
        if not groups:
            click.echo("  No groups found.")
            return
        
        for grp in groups:
            click.echo(f"  • {grp.name} - ID: {grp.id} ({len(grp.member_ids)} members)")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@group.command('show')
@click.argument('group_id')
@click.pass_context
def show_group(ctx, group_id):
    """Show group details."""
    try:
        service = get_service(ctx.obj['storage_dir'])
        grp = service.group_repo.get(group_id)
        
        if not grp:
            click.echo(f"✗ Group {group_id} not found.", err=True)
            raise click.Abort()
        
        click.echo(f"Group: {grp.name}")
        click.echo(f"  ID: {grp.id}")
        click.echo(f"  Created: {grp.created_at}")
        click.echo(f"  Members ({len(grp.member_ids)}):")
        
        for member_id in grp.member_ids:
            user = service.user_repo.get(member_id)
            if user:
                priority = " [PRIORITY]" if member_id in grp.priority_member_ids else ""
                click.echo(f"    • {user.name} ({user.email}){priority}")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@group.command('add-member')
@click.argument('group_id')
@click.argument('user_id')
@click.pass_context
def add_member(ctx, group_id, user_id):
    """Add a member to a group."""
    try:
        service = get_service(ctx.obj['storage_dir'])
        grp = service.add_group_member(group_id, user_id)
        
        user = service.user_repo.get(user_id)
        click.echo(f"✓ Added {user.name} to {grp.name}")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@group.command('remove-member')
@click.argument('group_id')
@click.argument('user_id')
@click.pass_context
def remove_member(ctx, group_id, user_id):
    """Remove a member from a group."""
    try:
        service = get_service(ctx.obj['storage_dir'])
        grp = service.remove_group_member(group_id, user_id)
        
        click.echo(f"✓ Removed member from {grp.name}")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


# ============================================================================
# Event Planning Commands
# ============================================================================

@cli.group()
def event():
    """Manage events."""
    pass


@event.command('plan')
@click.argument('group_id')
@click.option('--suggestions-file', required=True, help='JSON file with event suggestions')
@click.option('--activity', multiple=True, help='Filter by activity keyword')
@click.option('--location', help='Filter by location')
@click.option('--budget', type=float, help='Filter by maximum budget')
@click.pass_context
def plan_event(ctx, group_id, suggestions_file, activity, location, budget):
    """Plan an event for a group with suggestions."""
    try:
        service = get_service(ctx.obj['storage_dir'])
        
        # Load suggestions from file
        with open(suggestions_file, 'r') as f:
            suggestions_data = json.load(f)
        
        suggestions = [EventSuggestion.from_dict(s) for s in suggestions_data]
        
        # Plan the event
        result = service.plan_event(
            group_id=group_id,
            suggestions=suggestions,
            filters=None  # Filters will be applied via search command
        )
        
        click.echo(f"✓ Event planning for group: {result['group'].name}")
        click.echo(f"  Members: {len(result['members'])}")
        
        if result['members_without_availability']:
            click.echo(f"  ⚠ Members without availability: {len(result['members_without_availability'])}")
        
        click.echo(f"\n  Top Suggestions:")
        for i, suggestion in enumerate(result['suggestions'][:5], 1):
            click.echo(f"    {i}. {suggestion.activity_type} at {suggestion.location.name}")
            click.echo(f"       Score: {suggestion.consensus_score:.2f} | Cost: ${suggestion.estimated_cost_per_person}")
        
        if result['time_slots']:
            click.echo(f"\n  Available Time Slots:")
            for i, slot in enumerate(result['time_slots'][:5], 1):
                click.echo(f"    {i}. {slot.start_time} to {slot.end_time}")
                click.echo(f"       {slot.availability_percentage:.0%} attendance ({len(slot.available_member_ids)} members)")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@event.command('create')
@click.option('--suggestion-id', required=True, help='ID of the suggestion to use')
@click.option('--suggestions-file', required=True, help='JSON file with event suggestions')
@click.option('--name', required=True, help='Event name')
@click.option('--start', required=True, help='Start time (ISO format)')
@click.option('--participant', multiple=True, required=True, help='Participant user IDs')
@click.pass_context
def create_event(ctx, suggestion_id, suggestions_file, name, start, participant):
    """Create an event from a suggestion."""
    try:
        service = get_service(ctx.obj['storage_dir'])
        
        # Load suggestions
        with open(suggestions_file, 'r') as f:
            suggestions_data = json.load(f)
        suggestions = [EventSuggestion.from_dict(s) for s in suggestions_data]
        
        start_time = datetime.fromisoformat(start)
        
        event = service.create_event(
            suggestion_id=suggestion_id,
            suggestions=suggestions,
            event_name=name,
            start_time=start_time,
            participant_ids=list(participant)
        )
        
        click.echo(f"✓ Event created successfully!")
        click.echo(f"  ID: {event.id}")
        click.echo(f"  Name: {event.name}")
        click.echo(f"  Status: {event.status.value}")
        click.echo(f"  Time: {event.start_time} to {event.end_time}")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@event.command('finalize')
@click.argument('event_id')
@click.pass_context
def finalize_event(ctx, event_id):
    """Finalize a pending event."""
    try:
        service = get_service(ctx.obj['storage_dir'])
        event = service.finalize_event(event_id)
        
        click.echo(f"✓ Event finalized!")
        click.echo(f"  {event.name} is now {event.status.value}")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@event.command('cancel')
@click.argument('event_id')
@click.pass_context
def cancel_event(ctx, event_id):
    """Cancel an event."""
    try:
        service = get_service(ctx.obj['storage_dir'])
        event = service.cancel_event(event_id)
        
        click.echo(f"✓ Event cancelled: {event.name}")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@event.command('list')
@click.option('--user', help='Filter by user ID')
@click.pass_context
def list_events(ctx, user):
    """List events."""
    try:
        service = get_service(ctx.obj['storage_dir'])
        
        if user:
            events = service.get_user_events(user)
            click.echo(f"Events for user {user}:")
        else:
            events = service.event_repo.list()
            click.echo("All events:")
        
        if not events:
            click.echo("  No events found.")
            return
        
        for evt in events:
            click.echo(f"  • {evt.name} ({evt.status.value}) - {evt.start_time}")
            click.echo(f"    {evt.activity_type} at {evt.location.name}")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@event.command('show')
@click.argument('event_id')
@click.pass_context
def show_event(ctx, event_id):
    """Show event details."""
    try:
        service = get_service(ctx.obj['storage_dir'])
        evt = service.get_event_details(event_id)
        
        if not evt:
            click.echo(f"✗ Event {event_id} not found.", err=True)
            raise click.Abort()
        
        click.echo(f"Event: {evt.name}")
        click.echo(f"  ID: {evt.id}")
        click.echo(f"  Status: {evt.status.value}")
        click.echo(f"  Activity: {evt.activity_type}")
        click.echo(f"  Location: {evt.location.name} ({evt.location.address})")
        click.echo(f"  Time: {evt.start_time} to {evt.end_time}")
        if evt.budget_per_person:
            click.echo(f"  Budget: ${evt.budget_per_person} per person")
        if evt.description:
            click.echo(f"  Description: {evt.description}")
        click.echo(f"  Participants ({len(evt.participant_ids)}):")
        for participant_id in evt.participant_ids:
            user = service.user_repo.get(participant_id)
            if user:
                click.echo(f"    • {user.name}")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@event.command('check-conflicts')
@click.argument('event_id')
@click.pass_context
def check_conflicts(ctx, event_id):
    """Check for scheduling conflicts."""
    try:
        service = get_service(ctx.obj['storage_dir'])
        result = service.check_event_conflicts(event_id)
        
        evt = result['event']
        click.echo(f"Conflict check for: {evt.name}")
        click.echo(f"  Attendance: {result['attendance_percentage']:.0%}")
        click.echo(f"  Available: {len(result['available_members'])} members")
        click.echo(f"  Unavailable: {len(result['unavailable_members'])} members")
        
        if result['unavailable_members']:
            click.echo(f"\n  Unavailable members:")
            for member_id in result['unavailable_members']:
                user = service.user_repo.get(member_id)
                if user:
                    click.echo(f"    • {user.name}")
        
        if result['alternative_times']:
            click.echo(f"\n  Alternative times:")
            for i, slot in enumerate(result['alternative_times'][:3], 1):
                click.echo(f"    {i}. {slot.start_time} to {slot.end_time}")
                click.echo(f"       {slot.availability_percentage:.0%} attendance")
        
        if result['is_unresolvable']:
            click.echo(f"\n  ⚠ Conflicts cannot be fully resolved")
            click.echo(f"  Options: {', '.join(result['resolution_options'])}")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


# ============================================================================
# Feedback Commands
# ============================================================================

@cli.group()
def feedback():
    """Manage event feedback."""
    pass


@feedback.command('submit')
@click.argument('event_id')
@click.argument('user_id')
@click.option('--rating', type=int, required=True, help='Rating (1-5)')
@click.option('--comments', help='Optional comments')
@click.pass_context
def submit_feedback(ctx, event_id, user_id, rating, comments):
    """Submit feedback for an event."""
    try:
        service = get_service(ctx.obj['storage_dir'])
        
        feedback = service.submit_event_feedback(
            event_id=event_id,
            user_id=user_id,
            rating=rating,
            comments=comments
        )
        
        click.echo(f"✓ Feedback submitted!")
        click.echo(f"  Rating: {feedback.rating}/5")
        if feedback.comments:
            click.echo(f"  Comments: {feedback.comments}")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@feedback.command('list')
@click.option('--event', help='Filter by event ID')
@click.option('--user', help='Filter by user ID')
@click.pass_context
def list_feedback(ctx, event, user):
    """List feedback."""
    try:
        service = get_service(ctx.obj['storage_dir'])
        
        if event:
            feedbacks = service.get_event_feedback(event)
            click.echo(f"Feedback for event {event}:")
        elif user:
            feedbacks = service.get_user_feedback_history(user)
            click.echo(f"Feedback from user {user}:")
        else:
            feedbacks = service.feedback_repo.list()
            click.echo("All feedback:")
        
        if not feedbacks:
            click.echo("  No feedback found.")
            return
        
        for fb in feedbacks:
            user_obj = service.user_repo.get(fb.user_id)
            user_name = user_obj.name if user_obj else fb.user_id
            click.echo(f"  • {user_name}: {fb.rating}/5 - {fb.submitted_at}")
            if fb.comments:
                click.echo(f"    \"{fb.comments}\"")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


# ============================================================================
# Search Commands
# ============================================================================

@cli.group()
def search():
    """Search and filter event suggestions."""
    pass


@search.command('suggestions')
@click.argument('group_id')
@click.option('--suggestions-file', required=True, help='JSON file with event suggestions')
@click.option('--activity', multiple=True, help='Filter by activity keyword')
@click.option('--location', help='Filter by location')
@click.option('--budget', type=float, help='Filter by maximum budget')
@click.pass_context
def search_suggestions(ctx, group_id, suggestions_file, activity, location, budget):
    """Search and filter event suggestions for a group."""
    try:
        service = get_service(ctx.obj['storage_dir'])
        
        # Load suggestions
        with open(suggestions_file, 'r') as f:
            suggestions_data = json.load(f)
        suggestions = [EventSuggestion.from_dict(s) for s in suggestions_data]
        
        # Search with filters
        results = service.search_suggestions(
            group_id=group_id,
            suggestions=suggestions,
            activity_keywords=list(activity) if activity else None,
            location_area=location,
            budget_max=budget
        )
        
        click.echo(f"Found {len(results)} suggestion(s):")
        for i, suggestion in enumerate(results, 1):
            click.echo(f"\n  {i}. {suggestion.activity_type} at {suggestion.location.name}")
            click.echo(f"     Score: {suggestion.consensus_score:.2f}")
            click.echo(f"     Cost: ${suggestion.estimated_cost_per_person}")
            click.echo(f"     Duration: {suggestion.estimated_duration}")
            click.echo(f"     {suggestion.description}")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


# ============================================================================
# Scheduling Commands
# ============================================================================

@cli.group()
def schedule():
    """Find optimal scheduling times."""
    pass


@schedule.command('find-time')
@click.argument('group_id')
@click.option('--duration', type=int, required=True, help='Duration in hours')
@click.pass_context
def find_time(ctx, group_id, duration):
    """Find optimal time slots for a group."""
    try:
        service = get_service(ctx.obj['storage_dir'])
        
        duration_td = timedelta(hours=duration)
        time_slots = service.find_optimal_time(group_id, duration_td)
        
        if not time_slots:
            click.echo("No available time slots found.")
            return
        
        click.echo(f"Found {len(time_slots)} time slot(s):")
        for i, slot in enumerate(time_slots[:10], 1):
            click.echo(f"  {i}. {slot.start_time} to {slot.end_time}")
            click.echo(f"     {slot.availability_percentage:.0%} attendance ({len(slot.available_member_ids)} members)")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli(obj={})
