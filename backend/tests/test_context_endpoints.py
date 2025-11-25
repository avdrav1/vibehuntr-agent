"""Tests for context API endpoints."""

import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.main import app

# Import context_manager after conftest has set it up
import app.event_planning.context_manager as context_manager_module
get_context = context_manager_module.get_context
clear_context = context_manager_module.clear_context


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_all_contexts():
    """Clear all contexts before and after each test."""
    # Clear before test
    from app.event_planning.context_manager import _context_store
    _context_store.clear()
    yield
    # Clear after test
    _context_store.clear()


def test_get_context_empty(client):
    """Test getting context for a session with no context.
    
    Requirements: 11.2
    """
    session_id = "test_session_123"
    
    response = client.get(f"/api/context/{session_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["location"] is None
    assert data["search_query"] is None
    assert data["recent_venues"] == []


def test_get_context_with_location(client):
    """Test getting context with location set."""
    session_id = "test_session_456"
    
    # Set up context
    context = get_context(session_id)
    context.location = "Philadelphia"
    
    response = client.get(f"/api/context/{session_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["location"] == "Philadelphia"
    assert data["search_query"] is None
    assert data["recent_venues"] == []


def test_get_context_with_search_query(client):
    """Test getting context with search query set."""
    session_id = "test_session_789"
    
    # Set up context
    context = get_context(session_id)
    context.search_query = "italian"
    
    response = client.get(f"/api/context/{session_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["location"] is None
    assert data["search_query"] == "italian"
    assert data["recent_venues"] == []


def test_get_context_with_venues(client):
    """Test getting context with venues."""
    session_id = "test_session_abc"
    
    # Set up context with venues
    context = get_context(session_id)
    agent_message = "I found **Test Venue**. Place ID: ChIJtest123"
    context.update_from_agent_message(agent_message)
    
    response = client.get(f"/api/context/{session_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["location"] is None
    assert data["search_query"] is None
    assert len(data["recent_venues"]) == 1
    assert data["recent_venues"][0]["name"] == "Test Venue"
    assert data["recent_venues"][0]["place_id"] == "ChIJtest123"


def test_get_context_with_all_fields(client):
    """Test getting context with all fields populated."""
    session_id = "test_session_full"
    
    # Set up complete context
    context = get_context(session_id)
    context.location = "New York"
    context.search_query = "sushi"
    
    # Add multiple venues
    for i in range(3):
        agent_message = f"I found **Venue {i}**. Place ID: ChIJtest{i}"
        context.update_from_agent_message(agent_message)
    
    response = client.get(f"/api/context/{session_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["location"] == "New York"
    assert data["search_query"] == "sushi"
    assert len(data["recent_venues"]) == 3
    
    # Verify venues are in correct order
    for i in range(3):
        assert data["recent_venues"][i]["name"] == f"Venue {i}"
        assert data["recent_venues"][i]["place_id"] == f"ChIJtest{i}"


def test_clear_context_success(client):
    """Test clearing all context for a session.
    
    Requirements: 10.2, 10.3
    """
    session_id = "test_session_clear"
    
    # Set up context
    context = get_context(session_id)
    context.location = "Boston"
    context.search_query = "pizza"
    agent_message = "I found **Test Venue**. Place ID: ChIJtest123"
    context.update_from_agent_message(agent_message)
    
    # Verify context exists
    assert context.location is not None
    assert context.search_query is not None
    assert len(context.recent_venues) > 0
    
    # Clear context
    response = client.delete(f"/api/context/{session_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "message" in data
    
    # Verify context is cleared
    new_context = get_context(session_id)
    assert new_context.location is None
    assert new_context.search_query is None
    assert len(new_context.recent_venues) == 0


def test_clear_context_nonexistent_session(client):
    """Test clearing context for a session that doesn't exist."""
    session_id = "nonexistent_session"
    
    # Should succeed even if session doesn't exist
    response = client.delete(f"/api/context/{session_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_clear_context_item_location(client):
    """Test clearing only the location from context.
    
    Requirements: 11.6
    """
    session_id = "test_session_clear_location"
    
    # Set up context
    context = get_context(session_id)
    context.location = "Chicago"
    context.search_query = "tacos"
    
    # Clear only location
    response = client.delete(
        f"/api/context/{session_id}/item",
        params={"item_type": "location"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Verify only location is cleared
    context = get_context(session_id)
    assert context.location is None
    assert context.search_query == "tacos"


def test_clear_context_item_query(client):
    """Test clearing only the search query from context."""
    session_id = "test_session_clear_query"
    
    # Set up context
    context = get_context(session_id)
    context.location = "Seattle"
    context.search_query = "coffee"
    
    # Clear only search query
    response = client.delete(
        f"/api/context/{session_id}/item",
        params={"item_type": "query"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Verify only query is cleared
    context = get_context(session_id)
    assert context.location == "Seattle"
    assert context.search_query is None


def test_clear_context_item_venue(client):
    """Test clearing a specific venue from context."""
    session_id = "test_session_clear_venue"
    
    # Set up context with multiple venues
    context = get_context(session_id)
    for i in range(3):
        agent_message = f"I found **Venue {i}**. Place ID: ChIJtest{i}"
        context.update_from_agent_message(agent_message)
    
    # Verify we have 3 venues
    assert len(context.recent_venues) == 3
    
    # Clear the second venue (index 1)
    response = client.delete(
        f"/api/context/{session_id}/item",
        params={"item_type": "venue", "index": 1}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Verify venue was removed
    context = get_context(session_id)
    assert len(context.recent_venues) == 2
    assert context.recent_venues[0].name == "Venue 0"
    assert context.recent_venues[1].name == "Venue 2"


def test_clear_context_item_venue_invalid_index(client):
    """Test clearing venue with invalid index."""
    session_id = "test_session_invalid_index"
    
    # Set up context with one venue
    context = get_context(session_id)
    agent_message = "I found **Test Venue**. Place ID: ChIJtest123"
    context.update_from_agent_message(agent_message)
    
    # Try to clear venue at invalid index
    response = client.delete(
        f"/api/context/{session_id}/item",
        params={"item_type": "venue", "index": 5}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "Invalid venue index" in data["error"]


def test_clear_context_item_venue_missing_index(client):
    """Test clearing venue without providing index."""
    session_id = "test_session_missing_index"
    
    # Try to clear venue without index
    response = client.delete(
        f"/api/context/{session_id}/item",
        params={"item_type": "venue"}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "index parameter is required" in data["error"]


def test_clear_context_item_invalid_type(client):
    """Test clearing context item with invalid type."""
    session_id = "test_session_invalid_type"
    
    # Try to clear with invalid item type
    response = client.delete(
        f"/api/context/{session_id}/item",
        params={"item_type": "invalid"}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "Invalid item_type" in data["error"]


def test_clear_context_item_missing_type(client):
    """Test clearing context item without providing type."""
    session_id = "test_session_missing_type"
    
    # Try to clear without item_type
    response = client.delete(f"/api/context/{session_id}/item")
    
    # Should return 422 for missing required parameter
    assert response.status_code == 422


def test_context_isolation_between_sessions(client):
    """Test that context is isolated between different sessions."""
    session_id_1 = "test_session_1"
    session_id_2 = "test_session_2"
    
    # Set up different context for each session
    context1 = get_context(session_id_1)
    context1.location = "Philadelphia"
    context1.search_query = "italian"
    
    context2 = get_context(session_id_2)
    context2.location = "New York"
    context2.search_query = "sushi"
    
    # Get context for session 1
    response1 = client.get(f"/api/context/{session_id_1}")
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["location"] == "Philadelphia"
    assert data1["search_query"] == "italian"
    
    # Get context for session 2
    response2 = client.get(f"/api/context/{session_id_2}")
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["location"] == "New York"
    assert data2["search_query"] == "sushi"
    
    # Clear session 1
    clear_response = client.delete(f"/api/context/{session_id_1}")
    assert clear_response.status_code == 200
    
    # Verify session 1 is cleared
    response1_after = client.get(f"/api/context/{session_id_1}")
    data1_after = response1_after.json()
    assert data1_after["location"] is None
    assert data1_after["search_query"] is None
    
    # Verify session 2 is unchanged
    response2_after = client.get(f"/api/context/{session_id_2}")
    data2_after = response2_after.json()
    assert data2_after["location"] == "New York"
    assert data2_after["search_query"] == "sushi"
