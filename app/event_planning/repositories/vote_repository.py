"""Firestore repository for votes."""


from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter

from app.event_planning.error_logging import log_storage_error, log_validation_error
from app.event_planning.exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
    ValidationError,
)
from app.event_planning.models.venue import VenueOption, Vote


class VoteRepository:
    """Firestore repository for Vote entities stored as subcollections."""

    def __init__(self, db: firestore.Client | None = None):
        """
        Initialize the vote repository.

        Args:
            db: Firestore client instance. If None, creates a new client.
        """
        self.db = db or firestore.Client()
        self.sessions_collection = self.db.collection("planning_sessions")
        self.venues_collection_name = "venues"
        self.votes_collection_name = "votes"

    def _get_votes_collection(self, session_id: str, venue_id: str):
        """Get the votes subcollection reference."""
        return (
            self.sessions_collection
            .document(session_id)
            .collection(self.venues_collection_name)
            .document(venue_id)
            .collection(self.votes_collection_name)
        )

    def create(self, vote: Vote) -> Vote:
        """
        Create a new vote.

        Args:
            vote: The vote to create

        Returns:
            The created vote

        Raises:
            DuplicateEntityError: If vote with this ID already exists
            ValidationError: If vote data is invalid
        """
        # Validate vote
        try:
            vote.validate()
        except ValueError as e:
            error = ValidationError(str(e), details={"vote_id": vote.id})
            log_validation_error(error, "Vote", {"id": vote.id})
            raise error

        try:
            votes_ref = self._get_votes_collection(vote.session_id, vote.venue_id)
            doc_ref = votes_ref.document(vote.id)

            if doc_ref.get().exists:
                error = DuplicateEntityError("Vote", vote.id)
                log_storage_error(
                    error,
                    "create",
                    f"planning_sessions/{vote.session_id}/venues/{vote.venue_id}/votes/{vote.id}"
                )
                raise error

            doc_ref.set(vote.to_dict())
            return vote
        except DuplicateEntityError:
            raise
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to create vote: {e!s}",
                f"planning_sessions/{vote.session_id}/venues/{vote.venue_id}/votes/{vote.id}"
            )
            log_storage_error(
                error,
                "create",
                f"planning_sessions/{vote.session_id}/venues/{vote.venue_id}/votes"
            )
            raise error

    def get(self, session_id: str, venue_id: str, vote_id: str) -> Vote | None:
        """
        Get a vote by ID.

        Args:
            session_id: The session ID
            venue_id: The venue ID
            vote_id: The vote ID

        Returns:
            The vote or None if not found
        """
        try:
            votes_ref = self._get_votes_collection(session_id, venue_id)
            doc_ref = votes_ref.document(vote_id)
            doc = doc_ref.get()

            if not doc.exists:
                return None

            return Vote.from_dict(doc.to_dict())
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to get vote: {e!s}",
                f"planning_sessions/{session_id}/venues/{venue_id}/votes/{vote_id}"
            )
            log_storage_error(
                error,
                "get",
                f"planning_sessions/{session_id}/venues/{venue_id}/votes/{vote_id}"
            )
            raise error

    def get_by_participant(
        self,
        session_id: str,
        venue_id: str,
        participant_id: str
    ) -> Vote | None:
        """
        Get a vote by participant ID.

        Args:
            session_id: The session ID
            venue_id: The venue ID
            participant_id: The participant ID

        Returns:
            The vote or None if not found
        """
        try:
            votes_ref = self._get_votes_collection(session_id, venue_id)
            query = votes_ref.where(
                filter=FieldFilter("participant_id", "==", participant_id)
            ).limit(1)

            docs = list(query.stream())

            if not docs:
                return None

            return Vote.from_dict(docs[0].to_dict())
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to get vote by participant: {e!s}",
                f"planning_sessions/{session_id}/venues/{venue_id}/votes"
            )
            log_storage_error(
                error,
                "get_by_participant",
                f"planning_sessions/{session_id}/venues/{venue_id}/votes"
            )
            raise error

    def update(self, vote: Vote) -> Vote:
        """
        Update an existing vote.

        Args:
            vote: The vote to update

        Returns:
            The updated vote

        Raises:
            EntityNotFoundError: If vote doesn't exist
            ValidationError: If vote data is invalid
        """
        # Validate vote
        try:
            vote.validate()
        except ValueError as e:
            error = ValidationError(str(e), details={"vote_id": vote.id})
            log_validation_error(error, "Vote", {"id": vote.id})
            raise error

        try:
            votes_ref = self._get_votes_collection(vote.session_id, vote.venue_id)
            doc_ref = votes_ref.document(vote.id)

            if not doc_ref.get().exists:
                error = EntityNotFoundError("Vote", vote.id)
                log_storage_error(
                    error,
                    "update",
                    f"planning_sessions/{vote.session_id}/venues/{vote.venue_id}/votes/{vote.id}"
                )
                raise error

            doc_ref.set(vote.to_dict())
            return vote
        except EntityNotFoundError:
            raise
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to update vote: {e!s}",
                f"planning_sessions/{vote.session_id}/venues/{vote.venue_id}/votes/{vote.id}"
            )
            log_storage_error(
                error,
                "update",
                f"planning_sessions/{vote.session_id}/venues/{vote.venue_id}/votes/{vote.id}"
            )
            raise error

    def delete(self, session_id: str, venue_id: str, vote_id: str) -> bool:
        """
        Delete a vote.

        Args:
            session_id: The session ID
            venue_id: The venue ID
            vote_id: The vote ID

        Returns:
            True if deleted, False if not found
        """
        try:
            votes_ref = self._get_votes_collection(session_id, venue_id)
            doc_ref = votes_ref.document(vote_id)

            if not doc_ref.get().exists:
                return False

            doc_ref.delete()
            return True
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to delete vote: {e!s}",
                f"planning_sessions/{session_id}/venues/{venue_id}/votes/{vote_id}"
            )
            log_storage_error(
                error,
                "delete",
                f"planning_sessions/{session_id}/venues/{venue_id}/votes/{vote_id}"
            )
            raise error

    def list_for_venue(self, session_id: str, venue_id: str) -> list[Vote]:
        """
        List all votes for a venue.

        Args:
            session_id: The session ID
            venue_id: The venue ID

        Returns:
            List of votes
        """
        try:
            votes_ref = self._get_votes_collection(session_id, venue_id)
            votes = []

            for doc in votes_ref.stream():
                try:
                    votes.append(Vote.from_dict(doc.to_dict()))
                except Exception as e:
                    # Log error but continue processing
                    from app.event_planning.exceptions import FileStorageError
                    error = FileStorageError(
                        f"Failed to parse vote {doc.id}: {e!s}",
                        f"planning_sessions/{session_id}/venues/{venue_id}/votes/{doc.id}"
                    )
                    log_storage_error(
                        error,
                        "list_for_venue",
                        f"planning_sessions/{session_id}/venues/{venue_id}/votes/{doc.id}"
                    )
                    continue

            return votes
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to list votes: {e!s}",
                f"planning_sessions/{session_id}/venues/{venue_id}/votes"
            )
            log_storage_error(
                error,
                "list_for_venue",
                f"planning_sessions/{session_id}/venues/{venue_id}/votes"
            )
            raise error

    def list_for_participant(self, session_id: str, participant_id: str) -> list[Vote]:
        """
        List all votes by a participant across all venues in a session.

        Args:
            session_id: The session ID
            participant_id: The participant ID

        Returns:
            List of votes
        """
        try:
            # This requires querying across all venues, which is more complex
            # We'll need to use collection group queries
            votes = []

            # Query all votes subcollections in the session
            query = self.db.collection_group(self.votes_collection_name).where(
                filter=FieldFilter("session_id", "==", session_id)
            ).where(
                filter=FieldFilter("participant_id", "==", participant_id)
            )

            for doc in query.stream():
                try:
                    votes.append(Vote.from_dict(doc.to_dict()))
                except Exception as e:
                    # Log error but continue processing
                    from app.event_planning.exceptions import FileStorageError
                    error = FileStorageError(
                        f"Failed to parse vote {doc.id}: {e!s}",
                        f"votes/{doc.id}"
                    )
                    log_storage_error(error, "list_for_participant", f"votes/{doc.id}")
                    continue

            return votes
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to list votes for participant: {e!s}",
                f"planning_sessions/{session_id}/votes"
            )
            log_storage_error(
                error,
                "list_for_participant",
                f"planning_sessions/{session_id}/votes"
            )
            raise error


class VenueRepository:
    """Firestore repository for VenueOption entities stored as subcollections."""

    def __init__(self, db: firestore.Client | None = None):
        """
        Initialize the venue repository.

        Args:
            db: Firestore client instance. If None, creates a new client.
        """
        self.db = db or firestore.Client()
        self.sessions_collection = self.db.collection("planning_sessions")
        self.venues_collection_name = "venues"

    def _get_venues_collection(self, session_id: str):
        """Get the venues subcollection reference."""
        return self.sessions_collection.document(session_id).collection(self.venues_collection_name)

    def create(self, venue: VenueOption) -> VenueOption:
        """
        Create a new venue option.

        Args:
            venue: The venue to create

        Returns:
            The created venue

        Raises:
            DuplicateEntityError: If venue with this ID already exists
            ValidationError: If venue data is invalid
        """
        # Validate venue
        try:
            venue.validate()
        except ValueError as e:
            error = ValidationError(str(e), details={"venue_id": venue.id})
            log_validation_error(error, "VenueOption", {"id": venue.id})
            raise error

        try:
            venues_ref = self._get_venues_collection(venue.session_id)
            doc_ref = venues_ref.document(venue.id)

            if doc_ref.get().exists:
                error = DuplicateEntityError("VenueOption", venue.id)
                log_storage_error(
                    error,
                    "create",
                    f"planning_sessions/{venue.session_id}/venues/{venue.id}"
                )
                raise error

            doc_ref.set(venue.to_dict())
            return venue
        except DuplicateEntityError:
            raise
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to create venue: {e!s}",
                f"planning_sessions/{venue.session_id}/venues/{venue.id}"
            )
            log_storage_error(
                error,
                "create",
                f"planning_sessions/{venue.session_id}/venues/{venue.id}"
            )
            raise error

    def get(self, session_id: str, venue_id: str) -> VenueOption | None:
        """
        Get a venue by ID.

        Args:
            session_id: The session ID
            venue_id: The venue ID

        Returns:
            The venue or None if not found
        """
        try:
            venues_ref = self._get_venues_collection(session_id)
            doc_ref = venues_ref.document(venue_id)
            doc = doc_ref.get()

            if not doc.exists:
                return None

            return VenueOption.from_dict(doc.to_dict())
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to get venue: {e!s}",
                f"planning_sessions/{session_id}/venues/{venue_id}"
            )
            log_storage_error(
                error,
                "get",
                f"planning_sessions/{session_id}/venues/{venue_id}"
            )
            raise error

    def update(self, venue: VenueOption) -> VenueOption:
        """
        Update an existing venue.

        Args:
            venue: The venue to update

        Returns:
            The updated venue

        Raises:
            EntityNotFoundError: If venue doesn't exist
            ValidationError: If venue data is invalid
        """
        # Validate venue
        try:
            venue.validate()
        except ValueError as e:
            error = ValidationError(str(e), details={"venue_id": venue.id})
            log_validation_error(error, "VenueOption", {"id": venue.id})
            raise error

        try:
            venues_ref = self._get_venues_collection(venue.session_id)
            doc_ref = venues_ref.document(venue.id)

            if not doc_ref.get().exists:
                error = EntityNotFoundError("VenueOption", venue.id)
                log_storage_error(
                    error,
                    "update",
                    f"planning_sessions/{venue.session_id}/venues/{venue.id}"
                )
                raise error

            doc_ref.set(venue.to_dict())
            return venue
        except EntityNotFoundError:
            raise
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to update venue: {e!s}",
                f"planning_sessions/{venue.session_id}/venues/{venue.id}"
            )
            log_storage_error(
                error,
                "update",
                f"planning_sessions/{venue.session_id}/venues/{venue.id}"
            )
            raise error

    def delete(self, session_id: str, venue_id: str) -> bool:
        """
        Delete a venue.

        Args:
            session_id: The session ID
            venue_id: The venue ID

        Returns:
            True if deleted, False if not found
        """
        try:
            venues_ref = self._get_venues_collection(session_id)
            doc_ref = venues_ref.document(venue_id)

            if not doc_ref.get().exists:
                return False

            doc_ref.delete()
            return True
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to delete venue: {e!s}",
                f"planning_sessions/{session_id}/venues/{venue_id}"
            )
            log_storage_error(
                error,
                "delete",
                f"planning_sessions/{session_id}/venues/{venue_id}"
            )
            raise error

    def list_for_session(self, session_id: str) -> list[VenueOption]:
        """
        List all venues for a session.

        Args:
            session_id: The session ID

        Returns:
            List of venues
        """
        try:
            venues_ref = self._get_venues_collection(session_id)
            venues = []

            for doc in venues_ref.stream():
                try:
                    venues.append(VenueOption.from_dict(doc.to_dict()))
                except Exception as e:
                    # Log error but continue processing
                    from app.event_planning.exceptions import FileStorageError
                    error = FileStorageError(
                        f"Failed to parse venue {doc.id}: {e!s}",
                        f"planning_sessions/{session_id}/venues/{doc.id}"
                    )
                    log_storage_error(
                        error,
                        "list_for_session",
                        f"planning_sessions/{session_id}/venues/{doc.id}"
                    )
                    continue

            return venues
        except Exception as e:
            from app.event_planning.exceptions import FileStorageError
            error = FileStorageError(
                f"Failed to list venues: {e!s}",
                f"planning_sessions/{session_id}/venues"
            )
            log_storage_error(
                error,
                "list_for_session",
                f"planning_sessions/{session_id}/venues"
            )
            raise error
