"""Data models for the Event Planning Agent."""

from app.event_planning.models.user import User, PreferenceProfile, AvailabilityWindow
from app.event_planning.models.group import FriendGroup
from app.event_planning.models.event import Event, EventStatus, Location
from app.event_planning.models.feedback import EventFeedback
from app.event_planning.models.suggestion import EventSuggestion

# Group coordination models
from app.event_planning.models.planning_session import (
    PlanningSession,
    Participant,
    SessionStatus,
)
from app.event_planning.models.venue import VenueOption, Vote, VoteType
from app.event_planning.models.itinerary import ItineraryItem, Comment, COMMENT_MAX_LENGTH
from app.event_planning.models.session_summary import SessionSummary

__all__ = [
    # Existing models
    "User",
    "PreferenceProfile",
    "AvailabilityWindow",
    "FriendGroup",
    "Event",
    "EventStatus",
    "Location",
    "EventFeedback",
    "EventSuggestion",
    # Group coordination models
    "PlanningSession",
    "Participant",
    "SessionStatus",
    "VenueOption",
    "Vote",
    "VoteType",
    "ItineraryItem",
    "Comment",
    "COMMENT_MAX_LENGTH",
    "SessionSummary",
]
