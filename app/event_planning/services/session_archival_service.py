"""Service for archiving inactive planning sessions."""

import logging
from datetime import datetime

from google.cloud import firestore

from app.event_planning.repositories.planning_session_repository import (
    PlanningSessionRepository,
)

logger = logging.getLogger(__name__)


class SessionArchivalService:
    """Service for managing session archival."""

    def __init__(self, db: firestore.Client | None = None):
        """
        Initialize the session archival service.

        Args:
            db: Firestore client instance. If None, creates a new client.
        """
        self.repository = PlanningSessionRepository(db)

    def archive_inactive_sessions(self, days_inactive: int = 30) -> int:
        """
        Archive sessions that have been inactive for the specified number of days.

        This method should be called periodically (e.g., via a cron job or Cloud Scheduler)
        to automatically archive old sessions.

        Args:
            days_inactive: Number of days of inactivity before archiving (default: 30)

        Returns:
            Number of sessions archived

        Example:
            >>> service = SessionArchivalService()
            >>> archived_count = service.archive_inactive_sessions(days_inactive=30)
            >>> print(f"Archived {archived_count} sessions")
        """
        logger.info(f"Starting session archival for sessions inactive for {days_inactive} days")

        try:
            archived_count = self.repository.archive_inactive_sessions(days_inactive)
            logger.info(f"Successfully archived {archived_count} sessions")
            return archived_count
        except Exception as e:
            logger.error(f"Failed to archive sessions: {e!s}")
            raise

    def get_archival_stats(self) -> dict:
        """
        Get statistics about archived sessions.

        Returns:
            Dictionary with archival statistics
        """
        try:
            all_sessions = self.repository.list_all()

            from app.event_planning.models.planning_session import SessionStatus

            active_count = sum(1 for s in all_sessions if s.status == SessionStatus.ACTIVE)
            finalized_count = sum(1 for s in all_sessions if s.status == SessionStatus.FINALIZED)
            archived_count = sum(1 for s in all_sessions if s.status == SessionStatus.ARCHIVED)

            return {
                "total_sessions": len(all_sessions),
                "active_sessions": active_count,
                "finalized_sessions": finalized_count,
                "archived_sessions": archived_count,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to get archival stats: {e!s}")
            raise


def run_archival(days_inactive: int = 30) -> None:
    """
    Standalone function to run session archival.

    This can be called from a Cloud Function, Cloud Run job, or cron script.

    Args:
        days_inactive: Number of days of inactivity before archiving

    Example:
        # In a Cloud Function or Cloud Run job:
        from app.event_planning.services.session_archival_service import run_archival

        def archive_sessions(request):
            run_archival(days_inactive=30)
            return "Archival complete", 200
    """
    service = SessionArchivalService()
    archived_count = service.archive_inactive_sessions(days_inactive)

    stats = service.get_archival_stats()

    logger.info(f"Archival complete. Stats: {stats}")
    print(f"Archived {archived_count} sessions")
    print(f"Current stats: {stats}")
