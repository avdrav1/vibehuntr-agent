"""Event planning tools for the conversational AI agent.

These tools provide natural language interfaces to the event planning system.
"""

from datetime import datetime, timedelta
from typing import Optional, List
import json

from backend.app.event_planning.services.event_planning_service import EventPlanningService
from backend.app.event_planning.repositories.user_repository import UserRepository
from backend.app.event_planning.repositories.group_repository import GroupRepository
from backend.app.event_planning.repositories.event_repository import EventRepository
from backend.app.event_planning.repositories.feedback_repository import FeedbackRepository
from backend.app.event_planning.models.event import Location, EventStatus
from backend.app.event_planning.models.suggestion import EventSuggestion
import uuid


# Global service instance
_service: Optional[EventPlanningService] = None


def get_event_planning_service(storage_dir: str = "data") -> EventPlanningService:
    """Get or create the event planning service instance."""
    global _service
    if _service is None:
        user_repo = UserRepository(storage_dir)
        group_repo = GroupRepository(storage_dir)
        event_repo = EventRepository(storage_dir)
        feedback_repo = FeedbackRepository(storage_dir)
        
        _service = EventPlanningService(
            user_repository=user_repo,
            group_repository=group_repo,
            event_repository=event_repo,
            feedback_repository=feedback_repo,
            storage_dir=storage_dir
        )
    return _service


def create_user_tool(name: str, email: str) -> str:
    """
    Create a new user in the event planning system.
    
    Use this when someone wants to join the event planning system or create a profile.
    
    Args:
        name: The user's full name (e.g., "Alice Johnson")
        email: The user's email address (e.g., "alice@example.com")
    
    Returns:
        A confirmation message with the user's details.
    """
    try:
        service = get_event_planning_service()
        user = service.create_user(name=name, email=email)
        return f"✓ Created user profile for {user.name} ({user.email}). They can now join groups and plan events!"
    except Exception as e:
        return f"Error creating user: {str(e)}"


def list_users_tool() -> str:
    """
    List all users in the system.
    
    Use this when someone asks "who's in the system" or "show me all users".
    
    Returns:
        A formatted list of all users with their names and emails.
    """
    try:
        service = get_event_planning_service()
        users = service.user_repo.list_all()
        
        if not users:
            return "No users found in the system yet. Create some users first!"
        
        result = f"Found {len(users)} user(s):\n\n"
        for user in users:
            result += f"• {user.name} ({user.email})\n"
        
        return result
    except Exception as e:
        return f"Error listing users: {str(e)}"


def update_user_preferences_tool(
    user_name: str,
    activities: Optional[str] = None,
    budget: Optional[float] = None,
    locations: Optional[str] = None,
    dietary: Optional[str] = None
) -> str:
    """
    Update a user's preferences for event planning.
    
    Use this when someone wants to set their preferences like favorite activities,
    budget constraints, preferred locations, or dietary restrictions.
    
    Args:
        user_name: The user's name (e.g., "Alice")
        activities: Comma-separated activities with weights (e.g., "hiking:0.8,dining:0.6")
        budget: Maximum budget per event in dollars (e.g., 50.0)
        locations: Comma-separated preferred locations (e.g., "Downtown,Mountains")
        dietary: Comma-separated dietary restrictions (e.g., "vegetarian,gluten-free")
    
    Returns:
        A confirmation message about the updated preferences.
    """
    try:
        service = get_event_planning_service()
        
        # Find user by name
        users = service.user_repo.list_all()
        user = next((u for u in users if u.name.lower() == user_name.lower()), None)
        
        if not user:
            return f"User '{user_name}' not found. Available users: {', '.join(u.name for u in users)}"
        
        # Parse activities
        activity_prefs = None
        if activities:
            activity_prefs = {}
            for item in activities.split(','):
                if ':' in item:
                    activity, weight = item.split(':', 1)
                    activity_prefs[activity.strip()] = float(weight.strip())
        
        # Parse locations and dietary
        location_list = [l.strip() for l in locations.split(',')] if locations else None
        dietary_list = [d.strip() for d in dietary.split(',')] if dietary else None
        
        user = service.update_user_preferences(
            user_id=user.id,
            activity_preferences=activity_prefs,
            budget_max=budget,
            location_preferences=location_list,
            dietary_restrictions=dietary_list
        )
        
        result = f"✓ Updated preferences for {user.name}:\n"
        if activity_prefs:
            result += f"  Activities: {', '.join(f'{k} ({v})' for k, v in activity_prefs.items())}\n"
        if budget:
            result += f"  Max Budget: ${budget}\n"
        if location_list:
            result += f"  Locations: {', '.join(location_list)}\n"
        if dietary_list:
            result += f"  Dietary: {', '.join(dietary_list)}\n"
        
        return result
    except Exception as e:
        return f"Error updating preferences: {str(e)}"


def add_availability_tool(
    user_name: str,
    start_time: str,
    end_time: str,
    timezone: str = "UTC"
) -> str:
    """
    Add an availability window for a user.
    
    Use this when someone says they're available at certain times.
    
    Args:
        user_name: The user's name (e.g., "Alice")
        start_time: Start time in ISO format (e.g., "2025-01-25 18:00")
        end_time: End time in ISO format (e.g., "2025-01-25 22:00")
        timezone: Timezone (default: "UTC", can be "America/New_York", etc.)
    
    Returns:
        A confirmation message about the added availability.
    """
    try:
        service = get_event_planning_service()
        
        # Find user
        users = service.user_repo.list_all()
        user = next((u for u in users if u.name.lower() == user_name.lower()), None)
        
        if not user:
            return f"User '{user_name}' not found."
        
        # Parse times - try multiple formats
        for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
            try:
                start_dt = datetime.strptime(start_time, fmt)
                end_dt = datetime.strptime(end_time, fmt)
                break
            except ValueError:
                continue
        else:
            return f"Invalid time format. Use YYYY-MM-DD HH:MM (e.g., '2025-01-25 18:00')"
        
        user = service.add_user_availability(
            user_id=user.id,
            start_time=start_dt,
            end_time=end_dt,
            timezone=timezone
        )
        
        return f"✓ Added availability for {user.name}: {start_dt} to {end_dt} ({timezone})"
    except Exception as e:
        return f"Error adding availability: {str(e)}"


def create_group_tool(
    group_name: str,
    creator_name: str,
    member_names: Optional[str] = None
) -> str:
    """
    Create a new friend group for event planning.
    
    Use this when someone wants to create a group to plan events together.
    
    Args:
        group_name: Name for the group (e.g., "Weekend Warriors")
        creator_name: Name of the person creating the group (e.g., "Alice")
        member_names: Optional comma-separated list of member names to add (e.g., "Bob,Charlie")
    
    Returns:
        A confirmation message with group details.
    """
    try:
        service = get_event_planning_service()
        users = service.user_repo.list_all()
        
        # Find creator
        creator = next((u for u in users if u.name.lower() == creator_name.lower()), None)
        if not creator:
            return f"Creator '{creator_name}' not found. Available users: {', '.join(u.name for u in users)}"
        
        # Find members
        member_ids = None
        if member_names:
            member_ids = []
            for name in member_names.split(','):
                name = name.strip()
                member = next((u for u in users if u.name.lower() == name.lower()), None)
                if member:
                    member_ids.append(member.id)
                else:
                    return f"Member '{name}' not found."
        
        group = service.create_group(
            name=group_name,
            creator_id=creator.id,
            member_ids=member_ids
        )
        
        return f"✓ Created group '{group.name}' with {len(group.member_ids)} member(s)!"
    except Exception as e:
        return f"Error creating group: {str(e)}"


def list_groups_tool(user_name: Optional[str] = None) -> str:
    """
    List all groups or groups for a specific user.
    
    Use this when someone asks "what groups do I have" or "show me all groups".
    
    Args:
        user_name: Optional user name to filter groups (e.g., "Alice")
    
    Returns:
        A formatted list of groups.
    """
    try:
        service = get_event_planning_service()
        
        if user_name:
            users = service.user_repo.list_all()
            user = next((u for u in users if u.name.lower() == user_name.lower()), None)
            if not user:
                return f"User '{user_name}' not found."
            groups = service.get_user_groups(user.id)
            result = f"Groups for {user.name}:\n\n"
        else:
            groups = service.group_repo.list_all()
            result = "All groups:\n\n"
        
        if not groups:
            return result + "No groups found."
        
        for group in groups:
            result += f"• {group.name} ({len(group.member_ids)} members)\n"
        
        return result
    except Exception as e:
        return f"Error listing groups: {str(e)}"


def get_group_details_tool(group_name: str) -> str:
    """
    Get detailed information about a group.
    
    Use this when someone asks about a specific group's members or details.
    
    Args:
        group_name: Name of the group (e.g., "Weekend Warriors")
    
    Returns:
        Detailed information about the group including members.
    """
    try:
        service = get_event_planning_service()
        groups = service.group_repo.list_all()
        
        group = next((g for g in groups if g.name.lower() == group_name.lower()), None)
        if not group:
            return f"Group '{group_name}' not found. Available groups: {', '.join(g.name for g in groups)}"
        
        result = f"Group: {group.name}\n"
        result += f"Created: {group.created_at}\n"
        result += f"\nMembers ({len(group.member_ids)}):\n"
        
        for member_id in group.member_ids:
            user = service.user_repo.get(member_id)
            if user:
                priority = " [PRIORITY]" if member_id in group.priority_member_ids else ""
                result += f"  • {user.name} ({user.email}){priority}\n"
        
        return result
    except Exception as e:
        return f"Error getting group details: {str(e)}"


def find_optimal_time_tool(group_name: str, duration_hours: float = 2.0) -> str:
    """
    Find optimal time slots when a group can meet.
    
    Use this when someone asks "when can we meet" or "find a time for our group".
    
    Args:
        group_name: Name of the group (e.g., "Weekend Warriors")
        duration_hours: How long the event will be in hours (default: 2.0)
    
    Returns:
        A list of optimal time slots with attendance percentages.
    """
    try:
        service = get_event_planning_service()
        groups = service.group_repo.list_all()
        
        group = next((g for g in groups if g.name.lower() == group_name.lower()), None)
        if not group:
            return f"Group '{group_name}' not found."
        
        duration = timedelta(hours=duration_hours)
        time_slots = service.find_optimal_time(group.id, duration)
        
        if not time_slots:
            return f"No available time slots found for {group.name}. Members may need to add their availability."
        
        result = f"Found {len(time_slots)} optimal time slot(s) for {group.name}:\n\n"
        for i, slot in enumerate(time_slots[:5], 1):
            result += f"{i}. {slot.start_time.strftime('%Y-%m-%d %H:%M')} to {slot.end_time.strftime('%H:%M')}\n"
            result += f"   {slot.availability_percentage:.0%} attendance ({len(slot.available_member_ids)} members)\n\n"
        
        return result
    except Exception as e:
        return f"Error finding optimal time: {str(e)}"


def create_event_tool(
    event_name: str,
    group_name: str,
    activity_type: str,
    location_name: str,
    start_time: str,
    duration_hours: float = 2.0,
    budget: Optional[float] = None,
    description: Optional[str] = None
) -> str:
    """
    Create a new event for a group.
    
    Use this when someone wants to plan an event like "let's go hiking next Saturday".
    
    Args:
        event_name: Name of the event (e.g., "Saturday Hike")
        group_name: Name of the group (e.g., "Weekend Warriors")
        activity_type: Type of activity (e.g., "hiking", "dining", "movie")
        location_name: Where the event will be (e.g., "Mountain Vista Trail")
        start_time: When the event starts (e.g., "2025-01-25 10:00")
        duration_hours: How long the event will be in hours (default: 2.0)
        budget: Optional budget per person in dollars
        description: Optional description of the event
    
    Returns:
        A confirmation message with event details.
    """
    try:
        service = get_event_planning_service()
        groups = service.group_repo.list_all()
        
        group = next((g for g in groups if g.name.lower() == group_name.lower()), None)
        if not group:
            return f"Group '{group_name}' not found."
        
        # Parse time
        for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
            try:
                start_dt = datetime.strptime(start_time, fmt)
                break
            except ValueError:
                continue
        else:
            return f"Invalid time format. Use YYYY-MM-DD HH:MM"
        
        end_dt = start_dt + timedelta(hours=duration_hours)
        
        # Create event
        from app.event_planning.models.event import Event
        
        location = Location(
            name=location_name,
            address=location_name,  # Use location name as address if not provided
            latitude=0.0,
            longitude=0.0
        )
        
        event = Event(
            id=str(uuid.uuid4()),
            name=event_name,
            activity_type=activity_type,
            location=location,
            start_time=start_dt,
            end_time=end_dt,
            participant_ids=group.member_ids,
            status=EventStatus.PENDING,
            budget_per_person=budget,
            description=description or ""
        )
        
        event.validate()
        service.event_repo.create(event)
        
        result = f"✓ Created event '{event.name}'!\n"
        result += f"  Activity: {event.activity_type}\n"
        result += f"  When: {event.start_time.strftime('%Y-%m-%d %H:%M')} to {event.end_time.strftime('%H:%M')}\n"
        result += f"  Where: {event.location.name}\n"
        result += f"  Participants: {len(event.participant_ids)} members\n"
        result += f"  Status: {event.status.value}\n"
        if budget:
            result += f"  Budget: ${budget} per person\n"
        result += f"\nUse finalize_event to confirm this event!"
        
        return result
    except Exception as e:
        return f"Error creating event: {str(e)}"


def finalize_event_tool(event_name: str) -> str:
    """
    Finalize a pending event to confirm it.
    
    Use this when someone says "confirm the event" or "finalize the hiking trip".
    
    Args:
        event_name: Name of the event to finalize (e.g., "Saturday Hike")
    
    Returns:
        A confirmation message.
    """
    try:
        service = get_event_planning_service()
        events = service.event_repo.list_all()
        
        event = next((e for e in events if e.name.lower() == event_name.lower()), None)
        if not event:
            return f"Event '{event_name}' not found. Available events: {', '.join(e.name for e in events)}"
        
        event = service.finalize_event(event.id)
        return f"✓ Event '{event.name}' is now {event.status.value}! 🎉"
    except Exception as e:
        return f"Error finalizing event: {str(e)}"


def list_events_tool(user_name: Optional[str] = None) -> str:
    """
    List all events or events for a specific user.
    
    Use this when someone asks "what events do we have" or "show my events".
    
    Args:
        user_name: Optional user name to filter events (e.g., "Alice")
    
    Returns:
        A formatted list of events.
    """
    try:
        service = get_event_planning_service()
        
        if user_name:
            users = service.user_repo.list_all()
            user = next((u for u in users if u.name.lower() == user_name.lower()), None)
            if not user:
                return f"User '{user_name}' not found."
            events = service.get_user_events(user.id)
            result = f"Events for {user.name}:\n\n"
        else:
            events = service.event_repo.list_all()
            result = "All events:\n\n"
        
        if not events:
            return result + "No events found."
        
        for event in events:
            result += f"• {event.name} ({event.status.value})\n"
            result += f"  {event.activity_type} at {event.location.name}\n"
            result += f"  {event.start_time.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        return result
    except Exception as e:
        return f"Error listing events: {str(e)}"


def submit_feedback_tool(
    event_name: str,
    user_name: str,
    rating: int,
    comments: Optional[str] = None
) -> str:
    """
    Submit feedback for a completed event.
    
    Use this when someone wants to rate an event or provide feedback.
    
    Args:
        event_name: Name of the event (e.g., "Saturday Hike")
        user_name: Name of the user submitting feedback (e.g., "Alice")
        rating: Rating from 1-5 (5 being best)
        comments: Optional comments about the event
    
    Returns:
        A confirmation message.
    """
    try:
        service = get_event_planning_service()
        
        # Find event
        events = service.event_repo.list_all()
        event = next((e for e in events if e.name.lower() == event_name.lower()), None)
        if not event:
            return f"Event '{event_name}' not found."
        
        # Find user
        users = service.user_repo.list_all()
        user = next((u for u in users if u.name.lower() == user_name.lower()), None)
        if not user:
            return f"User '{user_name}' not found."
        
        if not (1 <= rating <= 5):
            return "Rating must be between 1 and 5."
        
        feedback = service.submit_event_feedback(
            event_id=event.id,
            user_id=user.id,
            rating=rating,
            comments=comments
        )
        
        stars = "⭐" * rating
        result = f"✓ Feedback submitted for '{event.name}'!\n"
        result += f"  Rating: {stars} ({rating}/5)\n"
        if comments:
            result += f"  Comments: \"{comments}\"\n"
        
        return result
    except Exception as e:
        return f"Error submitting feedback: {str(e)}"


# Export all tools as a list
EVENT_PLANNING_TOOLS = [
    create_user_tool,
    list_users_tool,
    update_user_preferences_tool,
    add_availability_tool,
    create_group_tool,
    list_groups_tool,
    get_group_details_tool,
    find_optimal_time_tool,
    create_event_tool,
    finalize_event_tool,
    list_events_tool,
    submit_feedback_tool,
]
