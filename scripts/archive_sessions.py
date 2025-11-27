#!/usr/bin/env python3
"""CLI script for archiving inactive planning sessions."""

import argparse
import logging
import sys

from app.event_planning.services.session_archival_service import SessionArchivalService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main() -> int:
    """Main entry point for the archival script."""
    parser = argparse.ArgumentParser(
        description="Archive inactive planning sessions"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days of inactivity before archiving (default: 30)"
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only show statistics without archiving"
    )

    args = parser.parse_args()

    try:
        service = SessionArchivalService()

        if args.stats_only:
            logger.info("Fetching archival statistics...")
            stats = service.get_archival_stats()
            print("\n=== Session Statistics ===")
            print(f"Total sessions: {stats['total_sessions']}")
            print(f"Active sessions: {stats['active_sessions']}")
            print(f"Finalized sessions: {stats['finalized_sessions']}")
            print(f"Archived sessions: {stats['archived_sessions']}")
            print(f"Timestamp: {stats['timestamp']}")
        else:
            logger.info(f"Archiving sessions inactive for {args.days} days...")
            archived_count = service.archive_inactive_sessions(args.days)
            print(f"\n✓ Successfully archived {archived_count} sessions")

            # Show updated stats
            stats = service.get_archival_stats()
            print("\n=== Updated Statistics ===")
            print(f"Total sessions: {stats['total_sessions']}")
            print(f"Active sessions: {stats['active_sessions']}")
            print(f"Finalized sessions: {stats['finalized_sessions']}")
            print(f"Archived sessions: {stats['archived_sessions']}")

        return 0
    except Exception as e:
        logger.error(f"Archival failed: {e!s}")
        print(f"\n✗ Error: {e!s}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
