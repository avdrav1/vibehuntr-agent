"""Itinerary manager service for group coordination.

This service handles the shared itinerary including adding venues,
removing items, and maintaining chronological order.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from app.event_planning.models.itinerary import ItineraryItem
from app.event_planning.models.planning_session import SessionStatus
from app.event_planning.exceptions import (
    BusinessLogicError,
    EntityNotFoundError,
)


class ItineraryItemNotFoundError(EntityNotFoundError):
    """Raised when an itinerary item is not found."""
    
    def __init__(self, item_id: str):
        super().__init__("ItineraryItem", item_id)
        self.error_code = "ITINERARY_ITEM_NOT_FOUND"


class SessionFinalizedError(BusinessLogicError):
    """Raised when attempting to modify a finalized session."""
    
    def __init__(self, session_id: str):
        message = f"Planning session {session_id} has been finalized and cannot be modified"
        details = {"session_id": session_id}
        super().__init__(message, "SESSION_FINALIZED", details)


class ItineraryManager:
    """Service for managing the shared itinerary with business logic."""
    
    def __init__(self, broadcast_service=None):
        """
        Initialize the itinerary manager with in-memory storage.
        
        Args:
            broadcast_service: Optional BroadcastService for real-time updates
        """
        # session_id -> {item_id -> ItineraryItem}
        self._items: Dict[str, Dict[str, ItineraryItem]] = {}
        # session_id -> SessionStatus (for finalization checks)
        self._session_status: Dict[str, SessionStatus] = {}
        # Optional broadcast service for real-time updates
        self._broadcast_service = broadcast_service
    
    def set_session_status(self, session_id: str, status: SessionStatus) -> None:
        """Set the session status for finalization checks."""
        self._session_status[session_id] = status
    
    def _check_session_not_finalized(self, session_id: str) -> None:
        """Check if session is finalized and raise error if so."""
        status = self._session_status.get(session_id, SessionStatus.ACTIVE)
        if status == SessionStatus.FINALIZED:
            raise SessionFinalizedError(session_id)

    def add_to_itinerary(
        self,
        session_id: str,
        venue_id: str,
        scheduled_time: datetime,
        added_by: str,
        item_id: Optional[str] = None,
    ) -> ItineraryItem:
        """
        Add a venue to the itinerary.
        
        Adds the venue with the scheduled time and maintains chronological order
        by assigning an order value based on the scheduled_time.
        
        Args:
            session_id: ID of the planning session
            venue_id: ID of the venue to add
            scheduled_time: When the venue is scheduled
            added_by: ID of the participant adding the item
            item_id: Optional item ID (generated if not provided)
        
        Returns:
            The created ItineraryItem
        
        Raises:
            SessionFinalizedError: If session is finalized
        
        Validates: Requirements 3.1, 4.2
        """
        self._check_session_not_finalized(session_id)
        
        # Generate item ID if not provided
        if item_id is None:
            item_id = str(uuid.uuid4())
        
        now = datetime.now()
        
        # Initialize session storage if needed
        if session_id not in self._items:
            self._items[session_id] = {}
        
        # Calculate order based on chronological position
        existing_items = list(self._items[session_id].values())
        order = self._calculate_order(existing_items, scheduled_time)
        
        # Create the itinerary item
        item = ItineraryItem(
            id=item_id,
            session_id=session_id,
            venue_id=venue_id,
            scheduled_time=scheduled_time,
            added_at=now,
            added_by=added_by,
            order=order,
        )
        
        item.validate()
        
        # Store the item
        self._items[session_id][item_id] = item
        
        # Re-order all items to maintain chronological consistency
        self._reorder_items(session_id)
        
        # Broadcast itinerary item added event if broadcast service is available
        if self._broadcast_service is not None:
            import asyncio
            from app.event_planning.services.broadcast_service import SessionEvent, EventType
            event = SessionEvent(
                event_type=EventType.ITINERARY_ITEM_ADDED,
                session_id=session_id,
                timestamp=now,
                data={
                    "item": item.to_dict(),
                    "itinerary": [i.to_dict() for i in self.get_itinerary(session_id)],
                },
                participant_id=added_by,
            )
            # Run broadcast in background if in async context
            try:
                asyncio.create_task(self._broadcast_service.broadcast(session_id, event))
            except RuntimeError:
                # Not in async context, skip broadcast
                pass
        
        return item
    
    def _calculate_order(
        self,
        existing_items: List[ItineraryItem],
        scheduled_time: datetime
    ) -> int:
        """Calculate the order value for a new item based on scheduled time."""
        if not existing_items:
            return 0
        
        # Sort existing items by scheduled_time
        sorted_items = sorted(existing_items, key=lambda x: x.scheduled_time)
        
        # Find the position where this item should be inserted
        for i, item in enumerate(sorted_items):
            if scheduled_time <= item.scheduled_time:
                return i
        
        return len(sorted_items)
    
    def _reorder_items(self, session_id: str) -> None:
        """Re-order all items in a session to maintain chronological order."""
        items = self._items.get(session_id, {})
        if not items:
            return
        
        # Sort by scheduled_time
        sorted_items = sorted(items.values(), key=lambda x: x.scheduled_time)
        
        # Update order values
        for i, item in enumerate(sorted_items):
            item.order = i

    def remove_from_itinerary(
        self,
        session_id: str,
        item_id: str,
    ) -> bool:
        """
        Remove an item from the itinerary.
        
        Removes the item and updates the order of remaining items.
        
        Args:
            session_id: ID of the planning session
            item_id: ID of the item to remove
        
        Returns:
            True if removal was successful
        
        Raises:
            SessionFinalizedError: If session is finalized
            ItineraryItemNotFoundError: If item doesn't exist
        
        Validates: Requirements 3.3
        """
        self._check_session_not_finalized(session_id)
        
        items = self._items.get(session_id, {})
        if item_id not in items:
            raise ItineraryItemNotFoundError(item_id)
        
        # Remove the item
        del self._items[session_id][item_id]
        
        # Re-order remaining items
        self._reorder_items(session_id)
        
        # Broadcast itinerary item removed event if broadcast service is available
        if self._broadcast_service is not None:
            import asyncio
            from app.event_planning.services.broadcast_service import SessionEvent, EventType
            event = SessionEvent(
                event_type=EventType.ITINERARY_ITEM_REMOVED,
                session_id=session_id,
                timestamp=datetime.now(),
                data={
                    "item_id": item_id,
                    "itinerary": [i.to_dict() for i in self.get_itinerary(session_id)],
                },
            )
            # Run broadcast in background if in async context
            try:
                asyncio.create_task(self._broadcast_service.broadcast(session_id, event))
            except RuntimeError:
                # Not in async context, skip broadcast
                pass
        
        return True
    
    def get_itinerary(self, session_id: str) -> List[ItineraryItem]:
        """
        Get the full itinerary sorted chronologically.
        
        Returns items sorted by scheduled_time in ascending order.
        
        Args:
            session_id: ID of the planning session
        
        Returns:
            List of ItineraryItems sorted by scheduled_time ascending
        
        Validates: Requirements 3.2
        """
        items = self._items.get(session_id, {})
        
        # Sort by scheduled_time ascending
        sorted_items = sorted(items.values(), key=lambda x: x.scheduled_time)
        
        return sorted_items
    
    def get_item(self, session_id: str, item_id: str) -> ItineraryItem:
        """
        Get an itinerary item by ID.
        
        Args:
            session_id: ID of the planning session
            item_id: ID of the item
        
        Returns:
            The ItineraryItem
        
        Raises:
            ItineraryItemNotFoundError: If item doesn't exist
        """
        items = self._items.get(session_id, {})
        item = items.get(item_id)
        if item is None:
            raise ItineraryItemNotFoundError(item_id)
        return item
    
    def reorder_itinerary(
        self,
        session_id: str,
        item_ids: List[str]
    ) -> List[ItineraryItem]:
        """
        Reorder itinerary items manually.
        
        Args:
            session_id: ID of the planning session
            item_ids: List of item IDs in desired order
        
        Returns:
            List of ItineraryItems in new order
        
        Raises:
            SessionFinalizedError: If session is finalized
            ItineraryItemNotFoundError: If any item doesn't exist
        """
        self._check_session_not_finalized(session_id)
        
        items = self._items.get(session_id, {})
        
        # Verify all item IDs exist
        for item_id in item_ids:
            if item_id not in items:
                raise ItineraryItemNotFoundError(item_id)
        
        # Update order values based on position in list
        for i, item_id in enumerate(item_ids):
            items[item_id].order = i
        
        return [items[item_id] for item_id in item_ids]
