"""Tests for planning session API endpoints.

This module tests the REST API endpoints for group coordination:
- Session creation and management
- Voting on venues
- Itinerary management
- Comments
- WebSocket connections
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from backend.app.main import app
    return TestClient(app)


@pytest.fixture
def sample_session(client):
    """Create a sample planning session for testing."""
    response = client.post(
        "/api/planning-sessions",
        json={
            "organizer_id": "test-organizer-123",
            "name": "Test Planning Session",
            "expiry_hours": 72,
        }
    )
    assert response.status_code == 201
    return response.json()


class TestSessionEndpoints:
    """Tests for planning session endpoints."""
    
    def test_create_session(self, client):
        """Test creating a new planning session."""
        response = client.post(
            "/api/planning-sessions",
            json={
                "organizer_id": "test-organizer-123",
                "name": "Weekend Brunch Planning",
                "expiry_hours": 48,
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert "id" in data
        assert data["name"] == "Weekend Brunch Planning"
        assert data["organizer_id"] == "test-organizer-123"
        assert "invite_token" in data
        assert len(data["invite_token"]) > 20  # Secure token
        assert data["invite_revoked"] is False
        assert data["status"] == "active"
        assert "test-organizer-123" in data["participant_ids"]
    
    def test_get_session(self, client, sample_session):
        """Test retrieving a session by ID."""
        session_id = sample_session["id"]
        
        response = client.get(f"/api/planning-sessions/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == session_id
        assert data["name"] == sample_session["name"]
    
    def test_get_nonexistent_session(self, client):
        """Test retrieving a session that doesn't exist."""
        response = client.get("/api/planning-sessions/nonexistent-id")
        
        assert response.status_code == 404
    
    def test_join_session(self, client, sample_session):
        """Test joining a session via invite token."""
        invite_token = sample_session["invite_token"]
        
        response = client.post(
            f"/api/planning-sessions/join/{invite_token}",
            json={
                "display_name": "Alice",
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["display_name"] == "Alice"
        assert data["session_id"] == sample_session["id"]
        assert data["is_organizer"] is False
    
    def test_revoke_invite(self, client, sample_session):
        """Test revoking an invite link."""
        session_id = sample_session["id"]
        organizer_id = sample_session["organizer_id"]
        
        response = client.post(
            f"/api/planning-sessions/{session_id}/revoke",
            json={"organizer_id": organizer_id}
        )
        
        assert response.status_code == 204
        
        # Verify invite is revoked by trying to join
        invite_token = sample_session["invite_token"]
        join_response = client.post(
            f"/api/planning-sessions/join/{invite_token}",
            json={"display_name": "Bob"}
        )
        
        assert join_response.status_code == 400
        response_data = join_response.json()
        error_message = response_data.get("detail", response_data.get("error", ""))
        assert "revoked" in error_message.lower()
    
    def test_finalize_session(self, client, sample_session):
        """Test finalizing a session."""
        session_id = sample_session["id"]
        organizer_id = sample_session["organizer_id"]
        
        response = client.post(
            f"/api/planning-sessions/{session_id}/finalize",
            json={"organizer_id": organizer_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["session_id"] == session_id
        assert data["session_name"] == sample_session["name"]
        assert "finalized_at" in data
        assert "share_url" in data
        assert len(data["participants"]) > 0


class TestVotingEndpoints:
    """Tests for voting endpoints."""
    
    def test_add_venue(self, client, sample_session):
        """Test adding a venue option."""
        session_id = sample_session["id"]
        
        response = client.post(
            f"/api/planning-sessions/{session_id}/venues",
            json={
                "place_id": "ChIJtest123",
                "name": "Test Restaurant",
                "address": "123 Test St",
                "suggested_by": "agent",
                "rating": 4.5,
                "price_level": 2,
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == "Test Restaurant"
        assert data["place_id"] == "ChIJtest123"
        assert data["session_id"] == session_id
    
    def test_cast_vote(self, client, sample_session):
        """Test casting a vote on a venue."""
        session_id = sample_session["id"]
        
        # First add a venue
        venue_response = client.post(
            f"/api/planning-sessions/{session_id}/venues",
            json={
                "place_id": "ChIJtest456",
                "name": "Cafe Test",
                "address": "456 Test Ave",
                "suggested_by": "agent",
            }
        )
        venue_id = venue_response.json()["id"]
        
        # Cast a vote
        response = client.post(
            f"/api/planning-sessions/{session_id}/venues/{venue_id}/vote",
            json={
                "participant_id": sample_session["organizer_id"],
                "vote_type": "UPVOTE",
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["venue_id"] == venue_id
        assert data["vote_type"] == "upvote"
    
    def test_get_venues_with_votes(self, client, sample_session):
        """Test retrieving venues with vote tallies."""
        session_id = sample_session["id"]
        
        # Add a venue
        venue_response = client.post(
            f"/api/planning-sessions/{session_id}/venues",
            json={
                "place_id": "ChIJtest789",
                "name": "Bistro Test",
                "address": "789 Test Blvd",
                "suggested_by": "agent",
            }
        )
        venue_id = venue_response.json()["id"]
        
        # Cast a vote
        client.post(
            f"/api/planning-sessions/{session_id}/venues/{venue_id}/vote",
            json={
                "participant_id": sample_session["organizer_id"],
                "vote_type": "UPVOTE",
            }
        )
        
        # Get venues with votes
        response = client.get(f"/api/planning-sessions/{session_id}/venues")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["venue"]["id"] == venue_id
        assert data[0]["tally"]["upvotes"] == 1
        assert data[0]["tally"]["total_votes"] == 1


class TestItineraryEndpoints:
    """Tests for itinerary endpoints."""
    
    def test_add_to_itinerary(self, client, sample_session):
        """Test adding an item to the itinerary."""
        session_id = sample_session["id"]
        
        # Add a venue first
        venue_response = client.post(
            f"/api/planning-sessions/{session_id}/venues",
            json={
                "place_id": "ChIJitinerary1",
                "name": "Morning Cafe",
                "address": "100 Morning St",
                "suggested_by": "agent",
            }
        )
        venue_id = venue_response.json()["id"]
        
        # Add to itinerary
        scheduled_time = (datetime.now() + timedelta(days=1)).isoformat()
        response = client.post(
            f"/api/planning-sessions/{session_id}/itinerary",
            json={
                "venue_id": venue_id,
                "scheduled_time": scheduled_time,
                "added_by": sample_session["organizer_id"],
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["venue_id"] == venue_id
        assert data["session_id"] == session_id
    
    def test_get_itinerary(self, client, sample_session):
        """Test retrieving the itinerary."""
        session_id = sample_session["id"]
        
        # Add a venue and add to itinerary
        venue_response = client.post(
            f"/api/planning-sessions/{session_id}/venues",
            json={
                "place_id": "ChIJitinerary2",
                "name": "Lunch Spot",
                "address": "200 Lunch Ln",
                "suggested_by": "agent",
            }
        )
        venue_id = venue_response.json()["id"]
        
        scheduled_time = (datetime.now() + timedelta(days=1, hours=2)).isoformat()
        client.post(
            f"/api/planning-sessions/{session_id}/itinerary",
            json={
                "venue_id": venue_id,
                "scheduled_time": scheduled_time,
                "added_by": sample_session["organizer_id"],
            }
        )
        
        # Get itinerary
        response = client.get(f"/api/planning-sessions/{session_id}/itinerary")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 1
        assert data[0]["venue_id"] == venue_id
    
    def test_remove_from_itinerary(self, client, sample_session):
        """Test removing an item from the itinerary."""
        session_id = sample_session["id"]
        
        # Add venue and add to itinerary
        venue_response = client.post(
            f"/api/planning-sessions/{session_id}/venues",
            json={
                "place_id": "ChIJitinerary3",
                "name": "Dinner Place",
                "address": "300 Dinner Dr",
                "suggested_by": "agent",
            }
        )
        venue_id = venue_response.json()["id"]
        
        scheduled_time = (datetime.now() + timedelta(days=1, hours=6)).isoformat()
        itinerary_response = client.post(
            f"/api/planning-sessions/{session_id}/itinerary",
            json={
                "venue_id": venue_id,
                "scheduled_time": scheduled_time,
                "added_by": sample_session["organizer_id"],
            }
        )
        item_id = itinerary_response.json()["id"]
        
        # Remove from itinerary
        response = client.delete(
            f"/api/planning-sessions/{session_id}/itinerary/{item_id}"
        )
        
        assert response.status_code == 204


class TestCommentEndpoints:
    """Tests for comment endpoints."""
    
    def test_add_comment(self, client, sample_session):
        """Test adding a comment to a venue."""
        session_id = sample_session["id"]
        
        # Add a venue first
        venue_response = client.post(
            f"/api/planning-sessions/{session_id}/venues",
            json={
                "place_id": "ChIJcomment1",
                "name": "Comment Test Venue",
                "address": "400 Comment Ct",
                "suggested_by": "agent",
            }
        )
        venue_id = venue_response.json()["id"]
        
        # Add a comment
        response = client.post(
            f"/api/planning-sessions/{session_id}/venues/{venue_id}/comments",
            json={
                "participant_id": sample_session["organizer_id"],
                "text": "This place looks great!",
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["text"] == "This place looks great!"
        assert data["venue_id"] == venue_id
    
    def test_get_comments(self, client, sample_session):
        """Test retrieving comments for a venue."""
        session_id = sample_session["id"]
        
        # Add venue
        venue_response = client.post(
            f"/api/planning-sessions/{session_id}/venues",
            json={
                "place_id": "ChIJcomment2",
                "name": "Another Venue",
                "address": "500 Another Ave",
                "suggested_by": "agent",
            }
        )
        venue_id = venue_response.json()["id"]
        
        # Add a comment
        client.post(
            f"/api/planning-sessions/{session_id}/venues/{venue_id}/comments",
            json={
                "participant_id": sample_session["organizer_id"],
                "text": "Great atmosphere!",
            }
        )
        
        # Get comments
        response = client.get(
            f"/api/planning-sessions/{session_id}/venues/{venue_id}/comments"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["text"] == "Great atmosphere!"
    
    def test_comment_too_long(self, client, sample_session):
        """Test that comments exceeding 500 characters are rejected."""
        session_id = sample_session["id"]
        
        # Add venue
        venue_response = client.post(
            f"/api/planning-sessions/{session_id}/venues",
            json={
                "place_id": "ChIJcomment3",
                "name": "Long Comment Venue",
                "address": "600 Long St",
                "suggested_by": "agent",
            }
        )
        venue_id = venue_response.json()["id"]
        
        # Try to add a comment that's too long
        long_text = "x" * 501
        response = client.post(
            f"/api/planning-sessions/{session_id}/venues/{venue_id}/comments",
            json={
                "participant_id": sample_session["organizer_id"],
                "text": long_text,
            }
        )
        
        assert response.status_code == 422  # Validation error from Pydantic
