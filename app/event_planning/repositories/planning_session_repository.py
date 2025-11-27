"""Firestore repository for planning sessions."""

from datetime import datetime, timedelta

from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter

from app.event_planning.error_logging import log_storage_error, log_validation_error
from app.event_planning.exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
    ValidationError,
)
from app.event_planning.models.planning_session import Participant, PlanningSession


class PlanningSessionRepository:
    """Firestore repository for PlanningSession entities."""

    def __init__(self, db: firestore.Client | None = None):
        """
        Initialize the planning session repository.

        Args:
            db: Firestore client instance. If None, creates a new client.
        """
        self.db = db or firestore.Client()
        self.collection = self.db.collection("planning_sessions")
        self.participants_collection_name = "participants"

    def create(self, session: PlanningSession) -> PlanningSession:
        """
        Create a new planning session.

        Args:
            session: The planning session to create

        Returns:
            The created planning session

        Raises:
            DuplicateEntityError: If session with this ID already exists
            ValidationError: If session data is invalid
        """
        # Check if session already exists
        doc_ref = self.collection.document(session.id)
        if doc_ref.get().exists:
            error = DuplicateEntityError("PlanningSession", session.id)
            log_storage_error(error, "create", f"planning_sessions/{session.id}")
            raise error

        # Validate session
        try:
            session.validate()
        except ValueError as e:
            error = ValidationError(str(e), details={"session_id": session.id})
            log_validation_error(error, "PlanningSession", {"id": session.id})
            raise error

        # Store session
        try:
            doc_ref.set(session.to_dict())
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to create session: {e!s}",
                f"planning_sessions/{session.id}"
            )
            log_storage_error(error, "create", f"planning_sessions/{session.id}")
            raise error

        return session

    def get(self, session_id: str) -> PlanningSession | None:
        """
        Get a planning session by ID.

        Args:
            session_id: The session ID

        Returns:
            The planning session or None if not found
        """
        try:
            doc_ref = self.collection.document(session_id)
            doc = doc_ref.get()

            if not doc.exists:
                return None

            return PlanningSession.from_dict(doc.to_dict())
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to get session: {e!s}",
                f"planning_sessions/{session_id}"
            )
            log_storage_error(error, "get", f"planning_sessions/{session_id}")
            raise error

    def get_by_invite_token(self, invite_token: str) -> PlanningSession | None:
        """
        Get a planning session by invite token.

        Args:
            invite_token: The invite token

        Returns:
            The planning session or None if not found
        """
        try:
            # Query by invite_token (requires index)
            query = self.collection.where(
                filter=FieldFilter("invite_token", "==", invite_token)
            ).limit(1)

            docs = list(query.stream())

            if not docs:
                return None

            return PlanningSession.from_dict(docs[0].to_dict())
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to get session by token: {e!s}",
                f"planning_sessions?invite_token={invite_token}"
            )
            log_storage_error(error, "get_by_invite_token", "planning_sessions")
            raise error

    def update(self, session: PlanningSession) -> PlanningSession:
        """
        Update an existing planning session.

        Args:
            session: The planning session to update

        Returns:
            The updated planning session

        Raises:
            EntityNotFoundError: If session doesn't exist
            ValidationError: If session data is invalid
        """
        doc_ref = self.collection.document(session.id)

        if not doc_ref.get().exists:
            error = EntityNotFoundError("PlanningSession", session.id)
            log_storage_error(error, "update", f"planning_sessions/{session.id}")
            raise error

        # Validate session
        try:
            session.validate()
        except ValueError as e:
            error = ValidationError(str(e), details={"session_id": session.id})
            log_validation_error(error, "PlanningSession", {"id": session.id})
            raise error

        # Update session
        try:
            doc_ref.set(session.to_dict())
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to update session: {e!s}",
                f"planning_sessions/{session.id}"
            )
            log_storage_error(error, "update", f"planning_sessions/{session.id}")
            raise error

        return session

    def delete(self, session_id: str) -> bool:
        """
        Delete a planning session.

        Args:
            session_id: The session ID

        Returns:
            True if deleted, False if not found
        """
        try:
            doc_ref = self.collection.document(session_id)

            if not doc_ref.get().exists:
                return False

            doc_ref.delete()
            return True
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to delete session: {e!s}",
                f"planning_sessions/{session_id}"
            )
            log_storage_error(error, "delete", f"planning_sessions/{session_id}")
            raise error

    def list_all(self) -> list[PlanningSession]:
        """
        List all planning sessions.

        Returns:
            List of all planning sessions
        """
        try:
            sessions = []
            for doc in self.collection.stream():
                try:
                    sessions.append(PlanningSession.from_dict(doc.to_dict()))
                except Exception as e:
                    # Log error but continue processing
                    from app.event_planning.exceptions import FileStorageError
                    error = FileStorageError(
                        f"Failed to parse session {doc.id}: {e!s}",
                        f"planning_sessions/{doc.id}"
                    )
                    log_storage_error(error, "list_all", f"planning_sessions/{doc.id}")
                    continue

            return sessions
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to list sessions: {e!s}",
                "planning_sessions"
            )
            log_storage_error(error, "list_all", "planning_sessions")
            raise error

    def archive_inactive_sessions(self, days_inactive: int = 30) -> int:
        """
        Archive sessions that have been inactive for the specified number of days.

        Args:
            days_inactive: Number of days of inactivity before archiving

        Returns:
            Number of sessions archived
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_inactive)

            # Query for sessions that haven't been updated recently and are not already archived
            query = self.collection.where(
                filter=FieldFilter("updated_at", "<", cutoff_date.isoformat())
            ).where(
                filter=FieldFilter("status", "!=", "archived")
            )

            archived_count = 0
            for doc in query.stream():
                try:
                    session = PlanningSession.from_dict(doc.to_dict())
                    from app.event_planning.models.planning_session import SessionStatus
                    session.status = SessionStatus.ARCHIVED
                    session.updated_at = datetime.now()
                    self.update(session)
                    archived_count += 1
                except Exception as e:
                    # Log error but continue processing
                    from app.event_planning.exceptions import FileStorageError
                    error = FileStorageError(
                        f"Failed to archive session {doc.id}: {e!s}",
                        f"planning_sessions/{doc.id}"
                    )
                    log_storage_error(error, "archive_inactive_sessions", f"planning_sessions/{doc.id}")
                    continue

            return archived_count
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to archive inactive sessions: {e!s}",
                "planning_sessions"
            )
            log_storage_error(error, "archive_inactive_sessions", "planning_sessions")
            raise error

    # Participant management methods

    def add_participant(self, session_id: str, participant: Participant) -> Participant:
        """
        Add a participant to a session.

        Args:
            session_id: The session ID
            participant: The participant to add

        Returns:
            The added participant

        Raises:
            EntityNotFoundError: If session doesn't exist
            ValidationError: If participant data is invalid
        """
        # Validate participant
        try:
            participant.validate()
        except ValueError as e:
            error = ValidationError(str(e), details={"participant_id": participant.id})
            log_validation_error(error, "Participant", {"id": participant.id})
            raise error

        try:
            # Add participant to subcollection
            doc_ref = self.collection.document(session_id)

            if not doc_ref.get().exists:
                error = EntityNotFoundError("PlanningSession", session_id)
                log_storage_error(error, "add_participant", f"planning_sessions/{session_id}")
                raise error

            participant_ref = doc_ref.collection(self.participants_collection_name).document(participant.id)
            participant_ref.set(participant.to_dict())

            return participant
        except EntityNotFoundError:
            raise
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to add participant: {e!s}",
                f"planning_sessions/{session_id}/participants/{participant.id}"
            )
            log_storage_error(error, "add_participant", f"planning_sessions/{session_id}")
            raise error

    def get_participants(self, session_id: str) -> list[Participant]:
        """
        Get all participants for a session.

        Args:
            session_id: The session ID

        Returns:
            List of participants
        """
        try:
            doc_ref = self.collection.document(session_id)
            participants_ref = doc_ref.collection(self.participants_collection_name)

            participants = []
            for doc in participants_ref.stream():
                try:
                    participants.append(Participant.from_dict(doc.to_dict()))
                except Exception as e:
                    # Log error but continue processing
                    from app.event_planning.exceptions import FileStorageError
                    error = FileStorageError(
                        f"Failed to parse participant {doc.id}: {e!s}",
                        f"planning_sessions/{session_id}/participants/{doc.id}"
                    )
                    log_storage_error(error, "get_participants", f"planning_sessions/{session_id}")
                    continue

            return participants
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to get participants: {e!s}",
                f"planning_sessions/{session_id}/participants"
            )
            log_storage_error(error, "get_participants", f"planning_sessions/{session_id}")
            raise error

    def get_participant(self, session_id: str, participant_id: str) -> Participant | None:
        """
        Get a specific participant.

        Args:
            session_id: The session ID
            participant_id: The participant ID

        Returns:
            The participant or None if not found
        """
        try:
            doc_ref = self.collection.document(session_id)
            participant_ref = doc_ref.collection(self.participants_collection_name).document(participant_id)
            doc = participant_ref.get()

            if not doc.exists:
                return None

            return Participant.from_dict(doc.to_dict())
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to get participant: {e!s}",
                f"planning_sessions/{session_id}/participants/{participant_id}"
            )
            log_storage_error(error, "get_participant", f"planning_sessions/{session_id}")
            raise error
