"""Pytest configuration for tests."""

import sys
from unittest.mock import MagicMock

# Mock the app module to prevent agent initialization during imports
sys.modules['app.agent'] = MagicMock()
