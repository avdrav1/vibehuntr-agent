#!/usr/bin/env python3
"""Standalone CLI entry point for the Event Planning Agent.

This script can be run directly without triggering the main agent imports.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Main entry point for the CLI."""
    # Import the CLI module directly, avoiding app/__init__.py
    from app.event_planning.cli import cli
    cli(obj={})


if __name__ == '__main__':
    main()
