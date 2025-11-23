"""Pydantic models for API requests and responses.

This module defines the data schemas used for API communication between
the frontend and backend. All models use Pydantic for validation and
serialization.

Requirements: 4.1, 4.2, 4.3
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional


class Message(BaseModel):
    """Represents a single message in a conversation.
    
    Attributes:
        role: The role of the message sender ('user' or 'assistant')
        content: The content of the message
        timestamp: ISO format timestamp (optional)
    """
    role: Literal["user", "assistant"]
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    """Request model for sending a chat message.
    
    Attributes:
        session_id: Unique identifier for the conversation session
        message: The user's message content
    """
    session_id: str = Field(..., description="Session identifier")
    message: str = Field(..., min_length=1, description="User message content")


class ChatResponse(BaseModel):
    """Response model for chat endpoint.
    
    Attributes:
        response: The complete agent response
    """
    response: str


class SessionResponse(BaseModel):
    """Response model for session creation.
    
    Attributes:
        session_id: The newly created session identifier
    """
    session_id: str


class MessagesResponse(BaseModel):
    """Response model for retrieving message history.
    
    Attributes:
        messages: List of messages in the session
    """
    messages: list[Message]


class ErrorResponse(BaseModel):
    """Response model for error cases.
    
    Attributes:
        detail: Error message description
        error_type: Type of error (optional)
    """
    detail: str
    error_type: Optional[str] = None


class StreamEvent(BaseModel):
    """Model for Server-Sent Events during streaming.
    
    Attributes:
        type: Event type ('token', 'done', 'error')
        content: Event content (for token and error types)
    """
    type: Literal["token", "done", "error"]
    content: Optional[str] = None


class VenueResponse(BaseModel):
    """Venue information in API responses.
    
    Attributes:
        name: Venue name
        place_id: Google Places ID
        location: Optional location information
    """
    name: str
    place_id: str
    location: Optional[str] = None


class ContextResponse(BaseModel):
    """Context information in API responses.
    
    Attributes:
        user_name: User's name
        user_email: User's email address
        location: Current location context
        search_query: Current search query context
        event_venue_name: Venue name for event planning
        event_date_time: Date/time for event planning
        event_party_size: Number of people for event
        recent_venues: List of recently mentioned venues
    """
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    location: Optional[str] = None
    search_query: Optional[str] = None
    event_venue_name: Optional[str] = None
    event_date_time: Optional[str] = None
    event_party_size: Optional[int] = None
    recent_venues: list[dict] = Field(default_factory=list)


class StatusResponse(BaseModel):
    """Generic status response.
    
    Attributes:
        success: Whether the operation was successful
        message: Optional status message
    """
    success: bool
    message: Optional[str] = None
