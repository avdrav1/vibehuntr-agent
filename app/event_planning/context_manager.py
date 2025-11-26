"""Context manager for tracking conversation state and entities.

This module provides explicit context tracking to improve agent memory
across conversation turns. It extracts and stores key information like
search queries, locations, and venue details.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class VenueInfo:
    """Information about a venue mentioned in conversation."""
    name: str
    place_id: str
    location: Optional[str] = None
    mentioned_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "name": self.name,
            "place_id": self.place_id,
            "location": self.location,
            "mentioned_at": self.mentioned_at.isoformat()
        }
    

@dataclass
class ConversationContext:
    """Tracks key information across conversation turns."""
    
    # Current search context
    search_query: Optional[str] = None
    location: Optional[str] = None
    
    # Recently mentioned venues (last 5)
    recent_venues: List[VenueInfo] = field(default_factory=list)
    
    # User profile information
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    
    # Event planning details
    event_venue_name: Optional[str] = None
    event_date_time: Optional[str] = None
    event_party_size: Optional[int] = None
    
    # Last user intent
    last_user_intent: Optional[str] = None
    
    def update_from_user_message(self, message: str) -> None:
        """Extract and store information from user message."""
        message_lower = message.lower()
        
        # Store the message as last intent
        self.last_user_intent = message
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, message)
        if email_match:
            self.user_email = email_match.group(0)
        
        # Extract names (simple heuristic: capitalized words that might be names)
        # Look for patterns like "my name is X" or "I'm X" or just "Name and email"
        name_patterns = [
            r'(?:my name is|i\'m|i am|call me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+and\s+[a-z0-9._%+-]+@',  # "John Doe and john@example.com"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, message)
            if match:
                self.user_name = match.group(1).strip()
                break
        
        # If no name pattern matched but we have words before an email, try that
        if not self.user_name and self.user_email:
            # Look for capitalized words before the email
            before_email = message.split(self.user_email)[0].strip()
            # Extract last 1-3 capitalized words before email
            words = before_email.split()
            capitalized = [w for w in words if w and w[0].isupper() and w.isalpha()]
            if capitalized:
                # Take last 1-2 capitalized words as potential name
                self.user_name = ' '.join(capitalized[-2:]) if len(capitalized) >= 2 else capitalized[-1]
        
        # Extract event planning details
        # Extract party size
        party_size_patterns = [
            r'(?:group|party|table)\s+of\s+(\d+)',
            r'for\s+(\d+)\s+(?:people|person|ppl|guests?)',
            r'(\d+)\s+(?:people|person|ppl|guests?)',
        ]
        
        for pattern in party_size_patterns:
            match = re.search(pattern, message_lower)
            if match:
                self.event_party_size = int(match.group(1))
                break
        
        # Extract venue name (capitalized words that might be venue names)
        # Look for patterns like "at VENUE" or "for VENUE"
        venue_patterns = [
            r'at\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',  # "at Dabbawala"
            r'for\s+(?:indian|chinese|thai|italian|mexican|japanese|korean|vietnamese|greek|mediterranean|french|american)\s+food\s+(?:at\s+)?([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',  # "for Indian food at Dabbawala"
        ]
        
        for pattern in venue_patterns:
            match = re.search(pattern, message)
            if match:
                potential_venue = match.group(1).strip()
                # Filter out common non-venue words
                if potential_venue.lower() not in ['south', 'north', 'east', 'west', 'philly', 'philadelphia']:
                    self.event_venue_name = potential_venue
                    break
        
        # Extract date and time
        # Try to find date and time together first
        date_time_pattern = r'(tomorrow|tonight|today|(?:on\s+)?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|(?:\d{1,2}/\d{1,2}))\s+(?:night|morning|afternoon|evening)?\s*(?:at\s+)?(\d+(?::\d+)?\s*(?:am|pm)?)?'
        date_match = re.search(date_time_pattern, message_lower)
        
        # Also try to find time and date separately (e.g., "at 8pm tomorrow")
        time_date_pattern = r'at\s+(\d+(?::\d+)?\s*(?:am|pm))\s+(tomorrow|tonight|today|(?:on\s+)?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))'
        time_date_match = re.search(time_date_pattern, message_lower)
        
        if time_date_match:
            # Time comes before date (e.g., "at 8pm tomorrow")
            time_part = time_date_match.group(1)
            date_part = time_date_match.group(2)
            self.event_date_time = f"{date_part} at {time_part}"
        elif date_match:
            # Date comes before time (e.g., "tomorrow at 8pm")
            date_part = date_match.group(1)
            time_part = date_match.group(2) if len(date_match.groups()) >= 2 and date_match.group(2) else None
            if time_part:
                self.event_date_time = f"{date_part} at {time_part}"
            else:
                # Try to find time separately
                time_only_pattern = r'at\s+(\d+(?::\d+)?\s*(?:am|pm))'
                time_match = re.search(time_only_pattern, message_lower)
                if time_match:
                    self.event_date_time = f"{date_part} at {time_match.group(1)}"
                else:
                    self.event_date_time = date_part
        
        # Extract location mentions (including neighborhood prefixes like "south philly")
        location_patterns = [
            r'\b(south|north|east|west|center city|downtown)?\s*(philadelphia|philly)\b',
            r'\b(south|north|east|west)?\s*(nyc|new york|boston|chicago|sf|san francisco|la|los angeles|seattle|portland|austin|miami|denver|dc|washington|baltimore|atlanta|dallas|houston|san diego|san jose)\b',
            r'\bin\s+([a-z\s]+)',
            r'\baround\s+([a-z\s]+)',
            r'\bnear\s+([a-z\s]+)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, message_lower)
            if match:
                # For patterns with optional neighborhood prefix, combine both groups
                if len(match.groups()) >= 2 and match.group(1) and match.group(2):
                    self.location = f"{match.group(1)} {match.group(2)}".strip()
                else:
                    # Find the first non-None group
                    for group in match.groups():
                        if group:
                            self.location = group.strip()
                            break
                break
        
        # Extract search queries (food types, activities, etc.)
        # Note: Order matters - more specific patterns should come first
        food_patterns = [
            r'\b(brunch|lunch|dinner|breakfast|happy hour)\b',
            r'\b(cheesesteak|pizza|sushi|italian|chinese|mexican|thai|indian|burger|taco|ramen|pho|bbq|barbecue|korean|japanese|vietnamese|greek|mediterranean|french|american|seafood|steak|vegan|vegetarian)s?\b',
            r'\b(restaurant|bar|cafe|coffee|food|dining|eatery|pub|bistro|brewery|winery|lounge)s?\b',
        ]
        
        for pattern in food_patterns:
            match = re.search(pattern, message_lower)
            if match:
                self.search_query = match.group(1)
                break
    
    def update_from_agent_message(self, message: str) -> None:
        """Extract venue information from agent's response."""
        # Extract Place IDs and venue names
        # Pattern: **Venue Name** ... Place ID: ChIJabc123
        # Also handles emoji prefixes like 🆔 Place ID:
        venue_pattern = r'\*\*([^*]+)\*\*.*?(?:🆔\s*)?Place ID:\s*(ChI[a-zA-Z0-9_-]+)'
        
        matches = re.findall(venue_pattern, message, re.DOTALL)
        
        for name, place_id in matches:
            venue = VenueInfo(
                name=name.strip(),
                place_id=place_id.strip(),
                location=self.location
            )
            
            # Add to recent venues (keep last 5)
            self.recent_venues.append(venue)
            if len(self.recent_venues) > 5:
                self.recent_venues.pop(0)
    
    def get_context_string(self) -> str:
        """Generate a context string to inject into messages."""
        parts = []
        
        # User profile information (highest priority)
        if self.user_name:
            parts.append(f"User's name: {self.user_name}")
        
        if self.user_email:
            parts.append(f"User's email: {self.user_email}")
        
        # Event planning details
        if self.event_venue_name:
            parts.append(f"Planning event at: {self.event_venue_name}")
        
        if self.event_party_size:
            parts.append(f"Party size: {self.event_party_size} people")
        
        if self.event_date_time:
            parts.append(f"Event time: {self.event_date_time}")
        
        if self.search_query:
            parts.append(f"User is looking for: {self.search_query}")
        
        if self.location:
            parts.append(f"Location: {self.location}")
        
        if self.recent_venues:
            venue_list = []
            for v in self.recent_venues[-3:]:  # Last 3 venues
                venue_list.append(f"{v.name} (Place ID: {v.place_id})")
            parts.append(f"Recently mentioned venues: {', '.join(venue_list)}")
        
        if self.last_user_intent and len(self.last_user_intent) < 100:
            parts.append(f"Last user message: '{self.last_user_intent}'")
        
        return " | ".join(parts) if parts else ""
    
    def find_venue_by_reference(self, reference: str) -> Optional[VenueInfo]:
        """Find a venue based on a vague reference like 'the one in Philadelphia' or 'the first one'."""
        reference_lower = reference.lower()
        
        # Check for ordinal references (first, second, third, etc.)
        ordinal_patterns = [
            (r'\bfirst\b|^1\b', 0),
            (r'\bsecond\b|^2\b', 1),
            (r'\bthird\b|^3\b', 2),
            (r'\bfourth\b|^4\b', 3),
            (r'\bfifth\b|^5\b', 4),
        ]
        
        for pattern, index in ordinal_patterns:
            if re.search(pattern, reference_lower):
                if index < len(self.recent_venues):
                    return self.recent_venues[index]
                return None
        
        # Check for vague references ("that one", "this one", "the one")
        vague_patterns = [
            r'\bthat one\b',
            r'\bthis one\b',
            r'\bthe one\b',
            r'\bit\b',
            r'\bthat\b',
            r'\bthis\b',
        ]
        
        for pattern in vague_patterns:
            if re.search(pattern, reference_lower):
                # Return most recent venue for vague references
                return self.recent_venues[-1] if self.recent_venues else None
        
        # Check for location-based references
        if self.location and self.location.lower() in reference_lower:
            # Find venue matching the location
            for venue in reversed(self.recent_venues):
                if venue.location and self.location.lower() in venue.location.lower():
                    return venue
        
        # Check for name-based references
        for venue in reversed(self.recent_venues):
            if venue.name.lower() in reference_lower:
                return venue
        
        # Default to most recent venue
        return self.recent_venues[-1] if self.recent_venues else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "user_name": self.user_name,
            "user_email": self.user_email,
            "search_query": self.search_query,
            "location": self.location,
            "event_venue_name": self.event_venue_name,
            "event_date_time": self.event_date_time,
            "event_party_size": self.event_party_size,
            "recent_venues": [venue.to_dict() for venue in self.recent_venues],
            "last_user_intent": self.last_user_intent
        }
    
    def clear(self) -> None:
        """Clear all context."""
        self.user_name = None
        self.user_email = None
        self.search_query = None
        self.location = None
        self.event_venue_name = None
        self.event_date_time = None
        self.event_party_size = None
        self.recent_venues = []
        self.last_user_intent = None


# Global context manager (one per session in production)
_context_store: Dict[str, ConversationContext] = {}


def get_context(session_id: str) -> ConversationContext:
    """Get or create context for a session."""
    if session_id not in _context_store:
        _context_store[session_id] = ConversationContext()
    return _context_store[session_id]


def clear_context(session_id: str) -> None:
    """Clear context for a session."""
    if session_id in _context_store:
        del _context_store[session_id]
