#!/usr/bin/env python3
"""Interactive menu-based CLI for the Event Planning Agent.

This provides a user-friendly interface that uses names instead of IDs.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from typing import Optional, List
from app.event_planning.services.event_planning_service import EventPlanningService
from app.event_planning.repositories.user_repository import UserRepository
from app.event_planning.repositories.group_repository import GroupRepository
from app.event_planning.repositories.event_repository import EventRepository
from app.event_planning.repositories.feedback_repository import FeedbackRepository
from app.event_planning.models.user import User
from app.event_planning.models.group import FriendGroup
from app.event_planning.models.event import Event


class InteractiveCLI:
    """Interactive CLI with name-based lookups."""
    
    def __init__(self, storage_dir: str = "data"):
        """Initialize the CLI with repositories."""
        self.storage_dir = storage_dir
        user_repo = UserRepository(storage_dir)
        group_repo = GroupRepository(storage_dir)
        event_repo = EventRepository(storage_dir)
        feedback_repo = FeedbackRepository(storage_dir)
        
        self.service = EventPlanningService(
            user_repository=user_repo,
            group_repository=group_repo,
            event_repository=event_repo,
            feedback_repository=feedback_repo,
            storage_dir=storage_dir
        )
    
    def select_user(self, prompt: str = "Select a user") -> Optional[User]:
        """Show a list of users and let the user select one by number or name."""
        users = self.service.user_repo.list_all()
        
        if not users:
            print("No users found. Please create a user first.")
            return None
        
        print(f"\n{prompt}:")
        for i, user in enumerate(users, 1):
            print(f"  {i}. {user.name} ({user.email})")
        
        while True:
            choice = input("\nEnter number or name (or 'cancel'): ").strip()
            
            if choice.lower() == 'cancel':
                return None
            
            # Try as number first
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(users):
                    return users[idx]
            
            # Try as name
            matches = [u for u in users if u.name.lower() == choice.lower()]
            if len(matches) == 1:
                return matches[0]
            elif len(matches) > 1:
                print(f"Multiple users found with name '{choice}'. Please use the number.")
            else:
                print(f"Invalid choice. Please enter a number (1-{len(users)}) or exact name.")
    
    def select_group(self, prompt: str = "Select a group", user_id: Optional[str] = None) -> Optional[FriendGroup]:
        """Show a list of groups and let the user select one."""
        if user_id:
            groups = self.service.get_user_groups(user_id)
        else:
            groups = self.service.group_repo.list_all()
        
        if not groups:
            print("No groups found. Please create a group first.")
            return None
        
        print(f"\n{prompt}:")
        for i, group in enumerate(groups, 1):
            print(f"  {i}. {group.name} ({len(group.member_ids)} members)")
        
        while True:
            choice = input("\nEnter number or name (or 'cancel'): ").strip()
            
            if choice.lower() == 'cancel':
                return None
            
            # Try as number
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(groups):
                    return groups[idx]
            
            # Try as name
            matches = [g for g in groups if g.name.lower() == choice.lower()]
            if len(matches) == 1:
                return matches[0]
            elif len(matches) > 1:
                print(f"Multiple groups found with name '{choice}'. Please use the number.")
            else:
                print(f"Invalid choice. Please enter a number (1-{len(groups)}) or exact name.")
    
    def select_event(self, prompt: str = "Select an event", user_id: Optional[str] = None) -> Optional[Event]:
        """Show a list of events and let the user select one."""
        if user_id:
            events = self.service.get_user_events(user_id)
        else:
            events = self.service.event_repo.list_all()
        
        if not events:
            print("No events found.")
            return None
        
        print(f"\n{prompt}:")
        for i, event in enumerate(events, 1):
            print(f"  {i}. {event.name} ({event.status.value}) - {event.start_time.strftime('%Y-%m-%d %H:%M')}")
        
        while True:
            choice = input("\nEnter number or name (or 'cancel'): ").strip()
            
            if choice.lower() == 'cancel':
                return None
            
            # Try as number
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(events):
                    return events[idx]
            
            # Try as name
            matches = [e for e in events if e.name.lower() == choice.lower()]
            if len(matches) == 1:
                return matches[0]
            elif len(matches) > 1:
                print(f"Multiple events found with name '{choice}'. Please use the number.")
            else:
                print(f"Invalid choice. Please enter a number (1-{len(events)}) or exact name.")
    
    def select_multiple_users(self, prompt: str = "Select users", exclude_ids: Optional[List[str]] = None) -> List[User]:
        """Allow selecting multiple users."""
        users = self.service.user_repo.list_all()
        
        if exclude_ids:
            users = [u for u in users if u.id not in exclude_ids]
        
        if not users:
            print("No users available.")
            return []
        
        print(f"\n{prompt} (comma-separated numbers or names, or 'done'):")
        for i, user in enumerate(users, 1):
            print(f"  {i}. {user.name} ({user.email})")
        
        selected = []
        while True:
            choice = input("\nEnter selection (or 'done'): ").strip()
            
            if choice.lower() == 'done':
                break
            
            # Split by comma
            parts = [p.strip() for p in choice.split(',')]
            
            for part in parts:
                # Try as number
                if part.isdigit():
                    idx = int(part) - 1
                    if 0 <= idx < len(users):
                        user = users[idx]
                        if user not in selected:
                            selected.append(user)
                            print(f"  Added: {user.name}")
                    else:
                        print(f"  Invalid number: {part}")
                else:
                    # Try as name
                    matches = [u for u in users if u.name.lower() == part.lower()]
                    if len(matches) == 1:
                        if matches[0] not in selected:
                            selected.append(matches[0])
                            print(f"  Added: {matches[0].name}")
                    elif len(matches) > 1:
                        print(f"  Multiple users found with name '{part}'")
                    else:
                        print(f"  User not found: {part}")
            
            if selected:
                print(f"\nCurrently selected: {', '.join(u.name for u in selected)}")
        
        return selected
    
    def run(self):
        """Run the interactive menu."""
        while True:
            print("\n" + "="*50)
            print("Event Planning Agent - Interactive Menu")
            print("="*50)
            print("1. User Management")
            print("2. Group Management")
            print("3. Event Management")
            print("4. Feedback")
            print("5. View Information")
            print("6. Exit")
            
            choice = input("\nChoose an option: ").strip()
            
            if choice == '1':
                self.user_management_menu()
            elif choice == '2':
                self.group_management_menu()
            elif choice == '3':
                self.event_management_menu()
            elif choice == '4':
                self.feedback_menu()
            elif choice == '5':
                self.view_information_menu()
            elif choice == '6':
                print("\nGoodbye!")
                break
            else:
                print("Invalid choice. Please try again.")
    
    def user_management_menu(self):
        """User management submenu."""
        while True:
            print("\n--- User Management ---")
            print("1. Create User")
            print("2. List Users")
            print("3. View User Details")
            print("4. Update Preferences")
            print("5. Add Availability")
            print("6. Back")
            
            choice = input("\nChoose an option: ").strip()
            
            if choice == '1':
                self.create_user()
            elif choice == '2':
                self.list_users()
            elif choice == '3':
                self.view_user_details()
            elif choice == '4':
                self.update_preferences()
            elif choice == '5':
                self.add_availability()
            elif choice == '6':
                break
            else:
                print("Invalid choice.")
    
    def group_management_menu(self):
        """Group management submenu."""
        while True:
            print("\n--- Group Management ---")
            print("1. Create Group")
            print("2. List Groups")
            print("3. View Group Details")
            print("4. Add Members")
            print("5. Remove Member")
            print("6. Back")
            
            choice = input("\nChoose an option: ").strip()
            
            if choice == '1':
                self.create_group()
            elif choice == '2':
                self.list_groups()
            elif choice == '3':
                self.view_group_details()
            elif choice == '4':
                self.add_group_members()
            elif choice == '5':
                self.remove_group_member()
            elif choice == '6':
                break
            else:
                print("Invalid choice.")
    
    def event_management_menu(self):
        """Event management submenu."""
        while True:
            print("\n--- Event Management ---")
            print("1. Create Event (Simple)")
            print("2. Finalize Event")
            print("3. Cancel Event")
            print("4. Check Conflicts")
            print("5. Back")
            
            choice = input("\nChoose an option: ").strip()
            
            if choice == '1':
                self.create_event_simple()
            elif choice == '2':
                self.finalize_event()
            elif choice == '3':
                self.cancel_event()
            elif choice == '4':
                self.check_conflicts()
            elif choice == '5':
                break
            else:
                print("Invalid choice.")
    
    def feedback_menu(self):
        """Feedback submenu."""
        while True:
            print("\n--- Feedback ---")
            print("1. Submit Feedback")
            print("2. View Event Feedback")
            print("3. Back")
            
            choice = input("\nChoose an option: ").strip()
            
            if choice == '1':
                self.submit_feedback()
            elif choice == '2':
                self.view_event_feedback()
            elif choice == '3':
                break
            else:
                print("Invalid choice.")
    
    def view_information_menu(self):
        """View information submenu."""
        while True:
            print("\n--- View Information ---")
            print("1. List All Users")
            print("2. List All Groups")
            print("3. List All Events")
            print("4. Back")
            
            choice = input("\nChoose an option: ").strip()
            
            if choice == '1':
                self.list_users()
            elif choice == '2':
                self.list_groups()
            elif choice == '3':
                self.list_events()
            elif choice == '4':
                break
            else:
                print("Invalid choice.")
    
    # Implementation methods
    
    def create_user(self):
        """Create a new user."""
        print("\n--- Create User ---")
        name = input("Name: ").strip()
        email = input("Email: ").strip()
        
        if not name or not email:
            print("Name and email are required.")
            return
        
        try:
            user = self.service.create_user(name=name, email=email)
            print(f"\n✓ User created successfully!")
            print(f"  Name: {user.name}")
            print(f"  Email: {user.email}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def list_users(self):
        """List all users."""
        users = self.service.user_repo.list_all()
        
        if not users:
            print("\nNo users found.")
            return
        
        print(f"\n--- Users ({len(users)}) ---")
        for user in users:
            print(f"  • {user.name} ({user.email})")
    
    def view_user_details(self):
        """View detailed user information."""
        user = self.select_user("Select user to view")
        if not user:
            return
        
        print(f"\n--- User: {user.name} ---")
        print(f"Email: {user.email}")
        
        profile = user.preference_profile
        if profile.activity_preferences:
            print(f"\nActivity Preferences:")
            for activity, weight in profile.activity_preferences.items():
                print(f"  • {activity}: {weight:.1f}")
        
        if profile.budget_max:
            print(f"\nMax Budget: ${profile.budget_max}")
        
        if profile.location_preferences:
            print(f"\nPreferred Locations: {', '.join(profile.location_preferences)}")
        
        if profile.dietary_restrictions:
            print(f"\nDietary Restrictions: {', '.join(profile.dietary_restrictions)}")
        
        if profile.accessibility_needs:
            print(f"\nAccessibility Needs: {', '.join(profile.accessibility_needs)}")
        
        if user.availability_windows:
            print(f"\nAvailability ({len(user.availability_windows)} windows):")
            for window in user.availability_windows:
                print(f"  • {window.start_time} to {window.end_time} ({window.timezone})")
    
    def update_preferences(self):
        """Update user preferences."""
        user = self.select_user("Select user to update")
        if not user:
            return
        
        print(f"\n--- Update Preferences for {user.name} ---")
        print("Leave blank to skip a field")
        
        # Activity preferences
        activities_input = input("\nActivity preferences (format: hiking:0.8,dining:0.6): ").strip()
        activity_prefs = None
        if activities_input:
            activity_prefs = {}
            for item in activities_input.split(','):
                if ':' in item:
                    activity, weight = item.split(':', 1)
                    activity_prefs[activity.strip()] = float(weight.strip())
        
        # Budget
        budget_input = input("Max budget: ").strip()
        budget = float(budget_input) if budget_input else None
        
        # Locations
        locations_input = input("Preferred locations (comma-separated): ").strip()
        locations = [l.strip() for l in locations_input.split(',')] if locations_input else None
        
        # Dietary
        dietary_input = input("Dietary restrictions (comma-separated): ").strip()
        dietary = [d.strip() for d in dietary_input.split(',')] if dietary_input else None
        
        # Accessibility
        accessibility_input = input("Accessibility needs (comma-separated): ").strip()
        accessibility = [a.strip() for a in accessibility_input.split(',')] if accessibility_input else None
        
        try:
            user = self.service.update_user_preferences(
                user_id=user.id,
                activity_preferences=activity_prefs,
                budget_max=budget,
                location_preferences=locations,
                dietary_restrictions=dietary,
                accessibility_needs=accessibility
            )
            print(f"\n✓ Preferences updated for {user.name}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def add_availability(self):
        """Add availability window."""
        user = self.select_user("Select user")
        if not user:
            return
        
        print(f"\n--- Add Availability for {user.name} ---")
        print("Enter times in format: YYYY-MM-DD HH:MM")
        
        start_input = input("Start time: ").strip()
        end_input = input("End time: ").strip()
        timezone = input("Timezone (default: UTC): ").strip() or "UTC"
        
        try:
            start_time = datetime.strptime(start_input, "%Y-%m-%d %H:%M")
            end_time = datetime.strptime(end_input, "%Y-%m-%d %H:%M")
            
            user = self.service.add_user_availability(
                user_id=user.id,
                start_time=start_time,
                end_time=end_time,
                timezone=timezone
            )
            print(f"\n✓ Availability added for {user.name}")
        except ValueError as e:
            print(f"\n✗ Invalid date format: {e}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def create_group(self):
        """Create a new group."""
        print("\n--- Create Group ---")
        name = input("Group name: ").strip()
        
        if not name:
            print("Group name is required.")
            return
        
        creator = self.select_user("Select group creator")
        if not creator:
            return
        
        print("\nAdd additional members (optional)")
        members = self.select_multiple_users("Select members", exclude_ids=[creator.id])
        
        member_ids = [m.id for m in members] if members else None
        
        try:
            group = self.service.create_group(
                name=name,
                creator_id=creator.id,
                member_ids=member_ids
            )
            print(f"\n✓ Group '{group.name}' created successfully!")
            print(f"  Members: {len(group.member_ids)}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def list_groups(self):
        """List all groups."""
        groups = self.service.group_repo.list_all()
        
        if not groups:
            print("\nNo groups found.")
            return
        
        print(f"\n--- Groups ({len(groups)}) ---")
        for group in groups:
            print(f"  • {group.name} ({len(group.member_ids)} members)")
    
    def view_group_details(self):
        """View detailed group information."""
        group = self.select_group("Select group to view")
        if not group:
            return
        
        print(f"\n--- Group: {group.name} ---")
        print(f"Created: {group.created_at}")
        print(f"\nMembers ({len(group.member_ids)}):")
        
        for member_id in group.member_ids:
            user = self.service.user_repo.get(member_id)
            if user:
                priority = " [PRIORITY]" if member_id in group.priority_member_ids else ""
                print(f"  • {user.name} ({user.email}){priority}")
    
    def add_group_members(self):
        """Add members to a group."""
        group = self.select_group("Select group")
        if not group:
            return
        
        print(f"\n--- Add Members to {group.name} ---")
        members = self.select_multiple_users("Select members to add", exclude_ids=group.member_ids)
        
        if not members:
            print("No members selected.")
            return
        
        try:
            for member in members:
                group = self.service.add_group_member(group.id, member.id)
                print(f"  ✓ Added {member.name}")
            
            print(f"\n✓ Added {len(members)} member(s) to {group.name}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def remove_group_member(self):
        """Remove a member from a group."""
        group = self.select_group("Select group")
        if not group:
            return
        
        # Show current members
        print(f"\n--- Remove Member from {group.name} ---")
        members = []
        for member_id in group.member_ids:
            user = self.service.user_repo.get(member_id)
            if user:
                members.append(user)
        
        if not members:
            print("No members in group.")
            return
        
        print("Current members:")
        for i, user in enumerate(members, 1):
            print(f"  {i}. {user.name}")
        
        choice = input("\nEnter number or name to remove (or 'cancel'): ").strip()
        
        if choice.lower() == 'cancel':
            return
        
        user_to_remove = None
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(members):
                user_to_remove = members[idx]
        else:
            matches = [u for u in members if u.name.lower() == choice.lower()]
            if matches:
                user_to_remove = matches[0]
        
        if not user_to_remove:
            print("Invalid choice.")
            return
        
        try:
            group = self.service.remove_group_member(group.id, user_to_remove.id)
            print(f"\n✓ Removed {user_to_remove.name} from {group.name}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def create_event_simple(self):
        """Create a simple event."""
        print("\n--- Create Event ---")
        
        group = self.select_group("Select group for event")
        if not group:
            return
        
        name = input("\nEvent name: ").strip()
        if not name:
            print("Event name is required.")
            return
        
        activity_type = input("Activity type (e.g., hiking, dining): ").strip()
        location_name = input("Location name: ").strip()
        location_address = input("Location address: ").strip()
        
        print("\nEnter times in format: YYYY-MM-DD HH:MM")
        start_input = input("Start time: ").strip()
        end_input = input("End time: ").strip()
        
        budget_input = input("Budget per person (optional): ").strip()
        budget = float(budget_input) if budget_input else None
        
        description = input("Description (optional): ").strip()
        
        try:
            from app.event_planning.models.event import Location, EventStatus
            import uuid
            
            start_time = datetime.strptime(start_input, "%Y-%m-%d %H:%M")
            end_time = datetime.strptime(end_input, "%Y-%m-%d %H:%M")
            
            location = Location(
                name=location_name,
                address=location_address,
                latitude=0.0,
                longitude=0.0
            )
            
            event = Event(
                id=str(uuid.uuid4()),
                name=name,
                activity_type=activity_type,
                location=location,
                start_time=start_time,
                end_time=end_time,
                participant_ids=group.member_ids,
                status=EventStatus.PENDING,
                budget_per_person=budget,
                description=description or ""
            )
            
            # Validate and save
            event.validate()
            self.service.event_repo.create(event)
            
            print(f"\n✓ Event '{event.name}' created successfully!")
            print(f"  Status: {event.status.value}")
            print(f"  Time: {event.start_time} to {event.end_time}")
            print(f"  Participants: {len(event.participant_ids)}")
        except ValueError as e:
            print(f"\n✗ Invalid date format: {e}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def finalize_event(self):
        """Finalize a pending event."""
        event = self.select_event("Select event to finalize")
        if not event:
            return
        
        try:
            event = self.service.finalize_event(event.id)
            print(f"\n✓ Event '{event.name}' finalized!")
            print(f"  Status: {event.status.value}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def cancel_event(self):
        """Cancel an event."""
        event = self.select_event("Select event to cancel")
        if not event:
            return
        
        confirm = input(f"\nAre you sure you want to cancel '{event.name}'? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Cancelled.")
            return
        
        try:
            event = self.service.cancel_event(event.id)
            print(f"\n✓ Event '{event.name}' cancelled")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def check_conflicts(self):
        """Check scheduling conflicts for an event."""
        event = self.select_event("Select event to check")
        if not event:
            return
        
        try:
            result = self.service.check_event_conflicts(event.id)
            
            print(f"\n--- Conflict Check: {event.name} ---")
            print(f"Attendance: {result['attendance_percentage']:.0%}")
            print(f"Available: {len(result['available_members'])} members")
            print(f"Unavailable: {len(result['unavailable_members'])} members")
            
            if result['unavailable_members']:
                print("\nUnavailable members:")
                for member_id in result['unavailable_members']:
                    user = self.service.user_repo.get(member_id)
                    if user:
                        print(f"  • {user.name}")
            
            if result['alternative_times']:
                print("\nAlternative times:")
                for i, slot in enumerate(result['alternative_times'][:3], 1):
                    print(f"  {i}. {slot.start_time} to {slot.end_time}")
                    print(f"     {slot.availability_percentage:.0%} attendance")
            
            if result['is_unresolvable']:
                print("\n⚠ Conflicts cannot be fully resolved")
                print(f"Options: {', '.join(result['resolution_options'])}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def list_events(self):
        """List all events."""
        events = self.service.event_repo.list_all()
        
        if not events:
            print("\nNo events found.")
            return
        
        print(f"\n--- Events ({len(events)}) ---")
        for event in events:
            print(f"  • {event.name} ({event.status.value}) - {event.start_time.strftime('%Y-%m-%d %H:%M')}")
    
    def submit_feedback(self):
        """Submit feedback for an event."""
        event = self.select_event("Select event")
        if not event:
            return
        
        user = self.select_user("Select user submitting feedback")
        if not user:
            return
        
        print(f"\n--- Submit Feedback for {event.name} ---")
        
        while True:
            rating_input = input("Rating (1-5): ").strip()
            try:
                rating = int(rating_input)
                if 1 <= rating <= 5:
                    break
                print("Rating must be between 1 and 5.")
            except ValueError:
                print("Please enter a number.")
        
        comments = input("Comments (optional): ").strip()
        
        try:
            feedback = self.service.submit_event_feedback(
                event_id=event.id,
                user_id=user.id,
                rating=rating,
                comments=comments if comments else None
            )
            print(f"\n✓ Feedback submitted!")
            print(f"  Rating: {feedback.rating}/5")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def view_event_feedback(self):
        """View feedback for an event."""
        event = self.select_event("Select event")
        if not event:
            return
        
        try:
            feedbacks = self.service.get_event_feedback(event.id)
            
            if not feedbacks:
                print(f"\nNo feedback for '{event.name}'")
                return
            
            print(f"\n--- Feedback for {event.name} ---")
            for fb in feedbacks:
                user = self.service.user_repo.get(fb.user_id)
                user_name = user.name if user else "Unknown"
                print(f"\n{user_name}: {fb.rating}/5")
                if fb.comments:
                    print(f"  \"{fb.comments}\"")
                print(f"  Submitted: {fb.submitted_at}")
        except Exception as e:
            print(f"\n✗ Error: {e}")


def main():
    """Main entry point."""
    cli = InteractiveCLI()
    cli.run()


if __name__ == '__main__':
    main()
