"""Pytest configuration for backend tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# CRITICAL: Add project root to path FIRST, before any other imports
# This ensures that 'app' module can be found when backend modules try to import it
project_root = Path(__file__).resolve().parent.parent.parent

# Remove backend directory from sys.path if it's there (pytest adds it)
backend_dir = str(project_root / "backend")
if backend_dir in sys.path:
    sys.path.remove(backend_dir)

# Ensure project root is at the very beginning
if str(project_root) in sys.path:
    sys.path.remove(str(project_root))
sys.path.insert(0, str(project_root))

# Debug: Print sys.path to see what's happening
print(f"DEBUG conftest.py: project_root = {project_root}")
print(f"DEBUG conftest.py: sys.path[:3] = {sys.path[:3]}")

# Mock heavy Google dependencies BEFORE any imports
# These must be mocked before any module tries to import them
sys.modules['google.adk'] = MagicMock()
sys.modules['google.adk.agents'] = MagicMock()
sys.modules['google.adk.runners'] = MagicMock()
sys.modules['google.adk.sessions'] = MagicMock()
sys.modules['google.adk.agents.run_config'] = MagicMock()
sys.modules['google.genai'] = MagicMock()
sys.modules['google.genai.types'] = MagicMock()

# DON'T mock app.event_planning modules here - let them import naturally
# The context_manager doesn't depend on Google modules, so it will import fine
# We'll mock agent_loader and agent_invoker at the function level if needed

# Import app to ensure it's loaded before any submodules are imported
# This is needed because app/__init__.py has a custom __getattr__ function
import app
print(f"DEBUG conftest.py: app module imported successfully")

# Try importing app.event_planning to see if it works
try:
    import app.event_planning
    print(f"DEBUG conftest.py: app.event_planning imported successfully")
except Exception as e:
    print(f"DEBUG conftest.py: Failed to import app.event_planning: {e}")
