"""Pytest configuration for backend tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# CRITICAL: Add both project root AND backend directory to path
# - Project root is needed for 'app' module (ADK agent)
# - Backend directory is needed for 'app.main' (FastAPI app) when tests import it
project_root = Path(__file__).resolve().parent.parent.parent
backend_dir = str(project_root / "backend")

# Ensure backend directory is at the very beginning so 'app' resolves to backend/app
# This allows tests to import from app.main, app.services, etc.
if backend_dir in sys.path:
    sys.path.remove(backend_dir)
sys.path.insert(0, backend_dir)

# Also add project root for any imports that need it
if str(project_root) in sys.path:
    sys.path.remove(str(project_root))
sys.path.insert(1, str(project_root))

# Debug: Print sys.path to see what's happening
print(f"DEBUG conftest.py: project_root = {project_root}")
print(f"DEBUG conftest.py: backend_dir = {backend_dir}")
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
