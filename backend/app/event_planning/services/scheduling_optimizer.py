"""Scheduling optimizer for finding optimal event times."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Set, Tuple
from zoneinfo import ZoneInfo

from app.event_planning.models.user import User, AvailabilityWindow
from app.event_planning.models.event import Event


@dataclass
class TimeSlot:
    """Represents a potential time slot for an event."""
    
    start_time: datetime
    end_time: datetime
    available_member_ids: List[str]
    availability_percentage: float
    
    def validate(self) -> None:
        """Validate the time slot."""
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        if not 0 <= self.availability_percentage <= 100:
            raise ValueError("availability_percentage must be between 0 and 100")


class SchedulingOptimizer:
    """Optimizes event scheduling based on participant availability."""
    
    def find_common_availability(
        self,
        users: List[User],
        duration: timedelta,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> List[TimeSlot]:
        """
        Find time slots where participants are available.
        
        Args:
            users: List of users to check availability for
            duration: Required duration for the event
            date_range: Optional date range to search within (start, end)
        
        Returns:
            List of TimeSlot objects sorted by availability percentage (descending)
        """
        if not users:
            return []
        
        # Collect all availability windows and convert to UTC
        utc_windows = []
        for user in users:
            for window in user.availability_windows:
                # Convert to UTC for comparison
                utc_start = self._convert_to_utc(window.start_time, window.timezone)
                utc_end = self._convert_to_utc(window.end_time, window.timezone)
                
                # Filter by date range if provided
                if date_range:
                    range_start, range_end = date_range
                    if utc_end <= range_start or utc_start >= range_end:
                        continue
                    # Clip to date range
                    utc_start = max(utc_start, range_start)
                    utc_end = min(utc_end, range_end)
                
                utc_windows.append((utc_start, utc_end, user.id))
        
        if not utc_windows:
            return []
        
        # Find all potential time slots
        time_slots = self._find_time_slots(utc_windows, duration, len(users))
        
        # Sort by availability percentage (descending), then by start time
        time_slots.sort(key=lambda ts: (-ts.availability_percentage, ts.start_time))
        
        return time_slots
    
    def resolve_conflicts(
        self,
        event: Event,
        users: List[User],
        priority_member_ids: Optional[List[str]] = None
    ) -> List[TimeSlot]:
        """
        Find alternative time slots for an event with conflicts.
        
        Args:
            event: The event with potential conflicts
            users: List of users to check availability for
            priority_member_ids: Optional list of priority member IDs
        
        Returns:
            List of alternative TimeSlot objects that improve participation
        """
        duration = event.end_time - event.start_time
        
        # Find all available time slots
        time_slots = self.find_common_availability(users, duration)
        
        # If priority members are specified, weight their availability
        if priority_member_ids:
            time_slots = self._apply_priority_weighting(time_slots, priority_member_ids, len(users))
        
        # Filter to only slots that have better or equal attendance than current
        current_available = self._get_available_members(event.start_time, event.end_time, users)
        current_percentage = (len(current_available) / len(users)) * 100 if users else 0
        
        better_slots = [
            slot for slot in time_slots
            if slot.availability_percentage >= current_percentage
        ]
        
        return better_slots
    
    def identify_conflicts(
        self,
        event_start: datetime,
        event_end: datetime,
        users: List[User]
    ) -> Tuple[List[str], List[str]]:
        """
        Identify which members can and cannot attend an event.
        
        Args:
            event_start: Event start time
            event_end: Event end time
            users: List of users to check
        
        Returns:
            Tuple of (available_member_ids, unavailable_member_ids)
        """
        available = self._get_available_members(event_start, event_end, users)
        all_member_ids = {user.id for user in users}
        unavailable = all_member_ids - available
        
        return sorted(list(available)), sorted(list(unavailable))
    
    def get_members_without_availability(self, users: List[User]) -> List[str]:
        """
        Get list of member IDs who have not provided availability information.
        
        Args:
            users: List of users to check
        
        Returns:
            List of user IDs without availability windows
        """
        return [user.id for user in users if not user.availability_windows]
    
    def _convert_to_utc(self, dt: datetime, timezone: str) -> datetime:
        """Convert a datetime to UTC."""
        if dt.tzinfo is None:
            # Assume the datetime is in the specified timezone
            local_tz = ZoneInfo(timezone)
            dt = dt.replace(tzinfo=local_tz)
        return dt.astimezone(ZoneInfo("UTC"))
    
    def _get_available_members(
        self,
        event_start: datetime,
        event_end: datetime,
        users: List[User]
    ) -> Set[str]:
        """Get set of member IDs available during the event time."""
        # Convert event times to UTC if needed
        if event_start.tzinfo is None:
            event_start = event_start.replace(tzinfo=ZoneInfo("UTC"))
        if event_end.tzinfo is None:
            event_end = event_end.replace(tzinfo=ZoneInfo("UTC"))
        
        event_start_utc = event_start.astimezone(ZoneInfo("UTC"))
        event_end_utc = event_end.astimezone(ZoneInfo("UTC"))
        
        available = set()
        for user in users:
            for window in user.availability_windows:
                window_start = self._convert_to_utc(window.start_time, window.timezone)
                window_end = self._convert_to_utc(window.end_time, window.timezone)
                
                # Check if event falls within this availability window
                if window_start <= event_start_utc and event_end_utc <= window_end:
                    available.add(user.id)
                    break
        
        return available
    
    def _find_time_slots(
        self,
        utc_windows: List[Tuple[datetime, datetime, str]],
        duration: timedelta,
        total_members: int
    ) -> List[TimeSlot]:
        """Find all potential time slots from availability windows."""
        if not utc_windows:
            return []
        
        # Create events for interval processing
        events = []
        for start, end, user_id in utc_windows:
            events.append((start, 'start', user_id))
            events.append((end, 'end', user_id))
        
        # Sort events by time
        events.sort(key=lambda e: (e[0], e[1] == 'end'))
        
        # Track active users and generate time slots
        active_users = set()
        time_slots = []
        prev_time = None
        
        for time, event_type, user_id in events:
            # If we have a previous time and active users, check if we can create a slot
            if prev_time and active_users and time > prev_time:
                # Check if the interval is long enough
                if time - prev_time >= duration:
                    # Generate time slots for this interval
                    current_time = prev_time
                    while current_time + duration <= time:
                        time_slots.append(TimeSlot(
                            start_time=current_time,
                            end_time=current_time + duration,
                            available_member_ids=sorted(list(active_users)),
                            availability_percentage=(len(active_users) / total_members) * 100
                        ))
                        # Move forward by 1 hour for next potential slot
                        current_time += timedelta(hours=1)
            
            # Update active users
            if event_type == 'start':
                active_users.add(user_id)
            else:
                active_users.discard(user_id)
            
            prev_time = time
        
        # Remove duplicate time slots (same start time)
        seen_starts = set()
        unique_slots = []
        for slot in time_slots:
            if slot.start_time not in seen_starts:
                seen_starts.add(slot.start_time)
                unique_slots.append(slot)
        
        return unique_slots
    
    def calculate_attendance_percentage(
        self,
        event_start: datetime,
        event_end: datetime,
        users: List[User]
    ) -> float:
        """
        Calculate the percentage of members who can attend an event.
        
        Args:
            event_start: Event start time
            event_end: Event end time
            users: List of users to check
        
        Returns:
            Attendance percentage (0-100)
        """
        if not users:
            return 0.0
        
        available_members = self._get_available_members(event_start, event_end, users)
        return (len(available_members) / len(users)) * 100
    
    def suggest_alternative_times(
        self,
        event: Event,
        users: List[User],
        priority_member_ids: Optional[List[str]] = None,
        min_improvement: float = 0.0
    ) -> List[TimeSlot]:
        """
        Suggest alternative times that improve member participation.
        
        Args:
            event: The event with potential conflicts
            users: List of users to check availability for
            priority_member_ids: Optional list of priority member IDs
            min_improvement: Minimum improvement in attendance percentage required
        
        Returns:
            List of alternative TimeSlot objects with better or equal participation
        """
        # Calculate current attendance
        current_percentage = self.calculate_attendance_percentage(
            event.start_time,
            event.end_time,
            users
        )
        
        # Get alternative time slots
        alternatives = self.resolve_conflicts(event, users, priority_member_ids)
        
        # Filter to only slots that meet minimum improvement threshold
        improved_slots = [
            slot for slot in alternatives
            if slot.availability_percentage >= current_percentage + min_improvement
        ]
        
        return improved_slots
    
    def detect_unresolvable_conflicts(
        self,
        event: Event,
        users: List[User],
        threshold_percentage: float = 100.0
    ) -> Tuple[bool, List[str]]:
        """
        Detect if conflicts cannot be fully resolved.
        
        Args:
            event: The event to check
            users: List of users
            threshold_percentage: Minimum acceptable attendance percentage
        
        Returns:
            Tuple of (is_unresolvable, options)
            - is_unresolvable: True if no time slot achieves threshold
            - options: List of suggested actions
        """
        duration = event.end_time - event.start_time
        
        # Find all possible time slots
        time_slots = self.find_common_availability(users, duration)
        
        # Check if any slot meets the threshold
        can_resolve = any(slot.availability_percentage >= threshold_percentage for slot in time_slots)
        
        options = []
        if not can_resolve:
            # Calculate current attendance
            current_percentage = self.calculate_attendance_percentage(
                event.start_time,
                event.end_time,
                users
            )
            
            # Find best possible attendance
            best_percentage = max(
                (slot.availability_percentage for slot in time_slots),
                default=current_percentage
            )
            
            # Provide options
            if best_percentage > current_percentage:
                options.append(
                    f"Reschedule to improve attendance from {current_percentage:.1f}% to {best_percentage:.1f}%"
                )
            
            if current_percentage > 0:
                options.append(
                    f"Proceed with partial attendance ({current_percentage:.1f}% of members)"
                )
            
            options.append("Cancel or postpone the event")
            
            # Identify who cannot attend
            available, unavailable = self.identify_conflicts(
                event.start_time,
                event.end_time,
                users
            )
            
            if unavailable:
                options.append(
                    f"Members unable to attend: {', '.join(unavailable)}"
                )
        
        return (not can_resolve, options)
    
    def _apply_priority_weighting(
        self,
        time_slots: List[TimeSlot],
        priority_member_ids: List[str],
        total_members: int
    ) -> List[TimeSlot]:
        """
        Apply priority weighting to time slots.
        
        Priority members count as 1.5x when calculating availability percentage.
        """
        weighted_slots = []
        
        for slot in time_slots:
            # Count priority and non-priority members
            priority_count = sum(1 for uid in slot.available_member_ids if uid in priority_member_ids)
            non_priority_count = len(slot.available_member_ids) - priority_count
            
            # Calculate weighted availability
            weighted_count = priority_count * 1.5 + non_priority_count
            weighted_percentage = (weighted_count / total_members) * 100
            
            # Create new slot with weighted percentage
            weighted_slot = TimeSlot(
                start_time=slot.start_time,
                end_time=slot.end_time,
                available_member_ids=slot.available_member_ids,
                availability_percentage=min(weighted_percentage, 100.0)  # Cap at 100%
            )
            weighted_slots.append(weighted_slot)
        
        # Re-sort by weighted percentage
        weighted_slots.sort(key=lambda ts: (-ts.availability_percentage, ts.start_time))
        
        return weighted_slots
