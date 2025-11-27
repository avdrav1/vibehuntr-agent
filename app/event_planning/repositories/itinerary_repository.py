"""Firestore repository for itinerary items."""


from google.cloud import firestore

from app.event_planning.error_logging import log_storage_error, log_validation_error
from app.event_planning.exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
    ValidationError,
)
from app.event_planning.models.itinerary import ItineraryItem


class ItineraryRepository:
    """Firestore repository for ItineraryItem entities stored as subcollections."""

    def __init__(self, db: firestore.Client | None = None):
        """
        Initialize the itinerary repository.

        Args:
            db: Firestore client instance. If None, creates a new client.
        """
        self.db = db or firestore.Client()
        self.sessions_collection = self.db.collection("planning_sessions")
        self.itinerary_collection_name = "itinerary"

    def _get_itinerary_collection(self, session_id: str):
        """Get the itinerary subcollection reference."""
        return self.sessions_collection.document(session_id).collection(self.itinerary_collection_name)

    def create(self, item: ItineraryItem) -> ItineraryItem:
        """
        Create a new itinerary item.

        Args:
            item: The itinerary item to create

        Returns:
            The created itinerary item

        Raises:
            DuplicateEntityError: If item with this ID already exists
            ValidationError: If item data is invalid
        """
        # Validate item
        try:
            item.validate()
        except ValueError as e:
            error = ValidationError(str(e), details={"item_id": item.id})
            log_validation_error(error, "ItineraryItem", {"id": item.id})
            raise error

        try:
            itinerary_ref = self._get_itinerary_collection(item.session_id)
            doc_ref = itinerary_ref.document(item.id)

            if doc_ref.get().exists:
                error = DuplicateEntityError("ItineraryItem", item.id)
                log_storage_error(
                    error,
                    "create",
                    f"planning_sessions/{item.session_id}/itinerary/{item.id}"
                )
                raise error

            doc_ref.set(item.to_dict())
            return item
        except DuplicateEntityError:
            raise
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to create itinerary item: {e!s}",
                f"planning_sessions/{item.session_id}/itinerary/{item.id}"
            )
            log_storage_error(
                error,
                "create",
                f"planning_sessions/{item.session_id}/itinerary/{item.id}"
            )
            raise error

    def get(self, session_id: str, item_id: str) -> ItineraryItem | None:
        """
        Get an itinerary item by ID.

        Args:
            session_id: The session ID
            item_id: The item ID

        Returns:
            The itinerary item or None if not found
        """
        try:
            itinerary_ref = self._get_itinerary_collection(session_id)
            doc_ref = itinerary_ref.document(item_id)
            doc = doc_ref.get()

            if not doc.exists:
                return None

            return ItineraryItem.from_dict(doc.to_dict())
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to get itinerary item: {e!s}",
                f"planning_sessions/{session_id}/itinerary/{item_id}"
            )
            log_storage_error(
                error,
                "get",
                f"planning_sessions/{session_id}/itinerary/{item_id}"
            )
            raise error

    def update(self, item: ItineraryItem) -> ItineraryItem:
        """
        Update an existing itinerary item.

        Args:
            item: The itinerary item to update

        Returns:
            The updated itinerary item

        Raises:
            EntityNotFoundError: If item doesn't exist
            ValidationError: If item data is invalid
        """
        # Validate item
        try:
            item.validate()
        except ValueError as e:
            error = ValidationError(str(e), details={"item_id": item.id})
            log_validation_error(error, "ItineraryItem", {"id": item.id})
            raise error

        try:
            itinerary_ref = self._get_itinerary_collection(item.session_id)
            doc_ref = itinerary_ref.document(item.id)

            if not doc_ref.get().exists:
                error = EntityNotFoundError("ItineraryItem", item.id)
                log_storage_error(
                    error,
                    "update",
                    f"planning_sessions/{item.session_id}/itinerary/{item.id}"
                )
                raise error

            doc_ref.set(item.to_dict())
            return item
        except EntityNotFoundError:
            raise
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to update itinerary item: {e!s}",
                f"planning_sessions/{item.session_id}/itinerary/{item.id}"
            )
            log_storage_error(
                error,
                "update",
                f"planning_sessions/{item.session_id}/itinerary/{item.id}"
            )
            raise error

    def delete(self, session_id: str, item_id: str) -> bool:
        """
        Delete an itinerary item.

        Args:
            session_id: The session ID
            item_id: The item ID

        Returns:
            True if deleted, False if not found
        """
        try:
            itinerary_ref = self._get_itinerary_collection(session_id)
            doc_ref = itinerary_ref.document(item_id)

            if not doc_ref.get().exists:
                return False

            doc_ref.delete()
            return True
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to delete itinerary item: {e!s}",
                f"planning_sessions/{session_id}/itinerary/{item_id}"
            )
            log_storage_error(
                error,
                "delete",
                f"planning_sessions/{session_id}/itinerary/{item_id}"
            )
            raise error

    def list_for_session(self, session_id: str) -> list[ItineraryItem]:
        """
        List all itinerary items for a session, ordered by scheduled_time.

        Args:
            session_id: The session ID

        Returns:
            List of itinerary items ordered chronologically
        """
        try:
            itinerary_ref = self._get_itinerary_collection(session_id)

            # Order by scheduled_time ascending
            query = itinerary_ref.order_by("scheduled_time")

            items = []
            for doc in query.stream():
                try:
                    items.append(ItineraryItem.from_dict(doc.to_dict()))
                except Exception as e:
                    # Log error but continue processing
                    from app.event_planning.exceptions import FileStorageError
                    error = FileStorageError(
                        f"Failed to parse itinerary item {doc.id}: {e!s}",
                        f"planning_sessions/{session_id}/itinerary/{doc.id}"
                    )
                    log_storage_error(
                        error,
                        "list_for_session",
                        f"planning_sessions/{session_id}/itinerary/{doc.id}"
                    )
                    continue

            return items
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to list itinerary items: {e!s}",
                f"planning_sessions/{session_id}/itinerary"
            )
            log_storage_error(
                error,
                "list_for_session",
                f"planning_sessions/{session_id}/itinerary"
            )
            raise error
