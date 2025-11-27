"""Shared service instances for group coordination.

This module provides singleton instances of the group coordination services
to ensure data consistency across API endpoints.
"""

from app.event_planning.services.planning_session_service import PlanningSessionService
from app.event_planning.services.vote_manager import VoteManager
from app.event_planning.services.itinerary_manager import ItineraryManager
from app.event_planning.services.comment_service import CommentService
from app.event_planning.services.broadcast_service import BroadcastService

# Create singleton instances
broadcast_service = BroadcastService()
session_service = PlanningSessionService()
vote_manager = VoteManager(broadcast_service=broadcast_service)
itinerary_manager = ItineraryManager(broadcast_service=broadcast_service)
comment_service = CommentService(broadcast_service=broadcast_service)
