"""Firestore repository for comments."""


from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter

from app.event_planning.error_logging import log_storage_error, log_validation_error
from app.event_planning.exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
    ValidationError,
)
from app.event_planning.models.itinerary import Comment


class CommentRepository:
    """Firestore repository for Comment entities stored as subcollections."""

    def __init__(self, db: firestore.Client | None = None):
        """
        Initialize the comment repository.

        Args:
            db: Firestore client instance. If None, creates a new client.
        """
        self.db = db or firestore.Client()
        self.sessions_collection = self.db.collection("planning_sessions")
        self.venues_collection_name = "venues"
        self.comments_collection_name = "comments"

    def _get_comments_collection(self, session_id: str, venue_id: str):
        """Get the comments subcollection reference."""
        return (
            self.sessions_collection
            .document(session_id)
            .collection(self.venues_collection_name)
            .document(venue_id)
            .collection(self.comments_collection_name)
        )

    def create(self, comment: Comment) -> Comment:
        """
        Create a new comment.

        Args:
            comment: The comment to create

        Returns:
            The created comment

        Raises:
            DuplicateEntityError: If comment with this ID already exists
            ValidationError: If comment data is invalid
        """
        # Validate comment
        try:
            comment.validate()
        except ValueError as e:
            error = ValidationError(str(e), details={"comment_id": comment.id})
            log_validation_error(error, "Comment", {"id": comment.id})
            raise error

        try:
            comments_ref = self._get_comments_collection(comment.session_id, comment.venue_id)
            doc_ref = comments_ref.document(comment.id)

            if doc_ref.get().exists:
                error = DuplicateEntityError("Comment", comment.id)
                log_storage_error(
                    error,
                    "create",
                    f"planning_sessions/{comment.session_id}/venues/{comment.venue_id}/comments/{comment.id}"
                )
                raise error

            doc_ref.set(comment.to_dict())
            return comment
        except DuplicateEntityError:
            raise
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to create comment: {e!s}",
                f"planning_sessions/{comment.session_id}/venues/{comment.venue_id}/comments/{comment.id}"
            )
            log_storage_error(
                error,
                "create",
                f"planning_sessions/{comment.session_id}/venues/{comment.venue_id}/comments"
            )
            raise error

    def get(self, session_id: str, venue_id: str, comment_id: str) -> Comment | None:
        """
        Get a comment by ID.

        Args:
            session_id: The session ID
            venue_id: The venue ID
            comment_id: The comment ID

        Returns:
            The comment or None if not found
        """
        try:
            comments_ref = self._get_comments_collection(session_id, venue_id)
            doc_ref = comments_ref.document(comment_id)
            doc = doc_ref.get()

            if not doc.exists:
                return None

            return Comment.from_dict(doc.to_dict())
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to get comment: {e!s}",
                f"planning_sessions/{session_id}/venues/{venue_id}/comments/{comment_id}"
            )
            log_storage_error(
                error,
                "get",
                f"planning_sessions/{session_id}/venues/{venue_id}/comments/{comment_id}"
            )
            raise error

    def update(self, comment: Comment) -> Comment:
        """
        Update an existing comment.

        Args:
            comment: The comment to update

        Returns:
            The updated comment

        Raises:
            EntityNotFoundError: If comment doesn't exist
            ValidationError: If comment data is invalid
        """
        # Validate comment
        try:
            comment.validate()
        except ValueError as e:
            error = ValidationError(str(e), details={"comment_id": comment.id})
            log_validation_error(error, "Comment", {"id": comment.id})
            raise error

        try:
            comments_ref = self._get_comments_collection(comment.session_id, comment.venue_id)
            doc_ref = comments_ref.document(comment.id)

            if not doc_ref.get().exists:
                error = EntityNotFoundError("Comment", comment.id)
                log_storage_error(
                    error,
                    "update",
                    f"planning_sessions/{comment.session_id}/venues/{comment.venue_id}/comments/{comment.id}"
                )
                raise error

            doc_ref.set(comment.to_dict())
            return comment
        except EntityNotFoundError:
            raise
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to update comment: {e!s}",
                f"planning_sessions/{comment.session_id}/venues/{comment.venue_id}/comments/{comment.id}"
            )
            log_storage_error(
                error,
                "update",
                f"planning_sessions/{comment.session_id}/venues/{comment.venue_id}/comments/{comment.id}"
            )
            raise error

    def delete(self, session_id: str, venue_id: str, comment_id: str) -> bool:
        """
        Delete a comment.

        Args:
            session_id: The session ID
            venue_id: The venue ID
            comment_id: The comment ID

        Returns:
            True if deleted, False if not found
        """
        try:
            comments_ref = self._get_comments_collection(session_id, venue_id)
            doc_ref = comments_ref.document(comment_id)

            if not doc_ref.get().exists:
                return False

            doc_ref.delete()
            return True
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to delete comment: {e!s}",
                f"planning_sessions/{session_id}/venues/{venue_id}/comments/{comment_id}"
            )
            log_storage_error(
                error,
                "delete",
                f"planning_sessions/{session_id}/venues/{venue_id}/comments/{comment_id}"
            )
            raise error

    def list_for_venue(self, session_id: str, venue_id: str) -> list[Comment]:
        """
        List all comments for a venue, ordered by created_at.

        Args:
            session_id: The session ID
            venue_id: The venue ID

        Returns:
            List of comments ordered chronologically
        """
        try:
            comments_ref = self._get_comments_collection(session_id, venue_id)

            # Order by created_at ascending
            query = comments_ref.order_by("created_at")

            comments = []
            for doc in query.stream():
                try:
                    comments.append(Comment.from_dict(doc.to_dict()))
                except Exception as e:
                    # Log error but continue processing
                    from app.event_planning.exceptions import FileStorageError
                    error = FileStorageError(
                        f"Failed to parse comment {doc.id}: {e!s}",
                        f"planning_sessions/{session_id}/venues/{venue_id}/comments/{doc.id}"
                    )
                    log_storage_error(
                        error,
                        "list_for_venue",
                        f"planning_sessions/{session_id}/venues/{venue_id}/comments/{doc.id}"
                    )
                    continue

            return comments
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to list comments: {e!s}",
                f"planning_sessions/{session_id}/venues/{venue_id}/comments"
            )
            log_storage_error(
                error,
                "list_for_venue",
                f"planning_sessions/{session_id}/venues/{venue_id}/comments"
            )
            raise error

    def list_for_participant(self, session_id: str, participant_id: str) -> list[Comment]:
        """
        List all comments by a participant across all venues in a session.

        Args:
            session_id: The session ID
            participant_id: The participant ID

        Returns:
            List of comments
        """
        try:
            # Use collection group query to search across all venues
            query = self.db.collection_group(self.comments_collection_name).where(
                filter=FieldFilter("session_id", "==", session_id)
            ).where(
                filter=FieldFilter("participant_id", "==", participant_id)
            ).order_by("created_at")

            comments = []
            for doc in query.stream():
                try:
                    comments.append(Comment.from_dict(doc.to_dict()))
                except Exception as e:
                    # Log error but continue processing
                    from app.event_planning.exceptions import FileStorageError
                    error = FileStorageError(
                        f"Failed to parse comment {doc.id}: {e!s}",
                        f"comments/{doc.id}"
                    )
                    log_storage_error(error, "list_for_participant", f"comments/{doc.id}")
                    continue

            return comments
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to list comments for participant: {e!s}",
                f"planning_sessions/{session_id}/comments"
            )
            log_storage_error(
                error,
                "list_for_participant",
                f"planning_sessions/{session_id}/comments"
            )
            raise error
