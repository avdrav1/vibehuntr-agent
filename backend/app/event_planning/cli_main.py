"""Standalone CLI entry point for the Event Planning Agent.

This module provides a CLI entry point that doesn't import the main agent,
avoiding Google Cloud initialization issues.
"""


def main():
    """Main entry point for the CLI."""
    # Import here to avoid triggering app/__init__.py at module load time
    from app.event_planning.cli import cli
    cli(obj={})


if __name__ == '__main__':
    main()
