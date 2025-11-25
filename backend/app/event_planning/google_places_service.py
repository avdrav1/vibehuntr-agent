"""Google Places API integration for venue recommendations.

This service provides real-world venue data including restaurants,
activities, reviews, and ratings.
"""

import os
from typing import List, Dict, Optional, Any
import requests
from dataclasses import dataclass


@dataclass
class PlaceResult:
    """A place result from Google Places API."""
    
    place_id: str
    name: str
    address: str
    rating: Optional[float]
    user_ratings_total: Optional[int]
    price_level: Optional[int]  # 0-4 scale
    types: List[str]
    latitude: float
    longitude: float
    photo_reference: Optional[str] = None
    opening_hours: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "place_id": self.place_id,
            "name": self.name,
            "address": self.address,
            "rating": self.rating,
            "user_ratings_total": self.user_ratings_total,
            "price_level": self.price_level,
            "types": self.types,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "photo_reference": self.photo_reference,
            "opening_hours": self.opening_hours,
        }


@dataclass
class PlaceDetails:
    """Detailed information about a place."""
    
    place_id: str
    name: str
    address: str
    phone: Optional[str]
    website: Optional[str]
    rating: Optional[float]
    user_ratings_total: Optional[int]
    price_level: Optional[int]
    reviews: List[Dict[str, Any]]
    photos: List[str]
    opening_hours: Optional[Dict[str, Any]]
    types: List[str]


class GooglePlacesService:
    """Service for interacting with Google Places API (New)."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the service.
        
        Args:
            api_key: Google Places API key. If not provided, reads from GOOGLE_PLACES_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GOOGLE_PLACES_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google Places API key required. Set GOOGLE_PLACES_API_KEY environment variable "
                "or pass api_key parameter. Get a key at: https://console.cloud.google.com/apis/credentials"
            )
        
        # Use the NEW Places API
        self.base_url = "https://places.googleapis.com/v1"
    
    def search_places(
        self,
        query: str,
        location: Optional[str] = None,
        radius: int = 5000,
        type_filter: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_results: int = 10
    ) -> List[PlaceResult]:
        """Search for places using text query (NEW Places API).
        
        Args:
            query: Search query (e.g., "Italian restaurants")
            location: Location to search near (e.g., "San Francisco, CA")
            radius: Search radius in meters (default: 5000)
            type_filter: Place type filter (e.g., "restaurant", "park")
            min_rating: Minimum rating filter (0-5)
            max_results: Maximum number of results to return
        
        Returns:
            List of place results
        """
        # Use NEW Places API - Text Search
        url = f"{self.base_url}/places:searchText"
        
        # Build the request body
        text_query = query
        if location:
            text_query = f"{query} in {location}"
        
        body = {
            "textQuery": text_query,
            "maxResultCount": min(max_results, 20),  # API limit is 20
        }
        
        # Add location bias if specified
        if location:
            body["locationBias"] = {
                "circle": {
                    "center": {
                        "latitude": 0,  # Will be geocoded
                        "longitude": 0
                    },
                    "radius": radius
                }
            }
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.priceLevel,places.types,places.location"
        }
        
        response = requests.post(url, json=body, headers=headers)
        data = response.json()
        
        if "places" not in data:
            return []
        
        results = []
        for place in data.get("places", []):
            # Filter by rating if specified
            rating = place.get("rating")
            if min_rating and (not rating or rating < min_rating):
                continue
            
            # Extract location
            location_data = place.get("location", {})
            
            result = PlaceResult(
                place_id=place.get("id", ""),
                name=place.get("displayName", {}).get("text", "Unknown"),
                address=place.get("formattedAddress", ""),
                rating=rating,
                user_ratings_total=place.get("userRatingCount"),
                price_level=self._convert_price_level(place.get("priceLevel")),
                types=place.get("types", []),
                latitude=location_data.get("latitude", 0.0),
                longitude=location_data.get("longitude", 0.0),
                photo_reference=None,  # Photos require separate API call in new API
                opening_hours=None,
            )
            results.append(result)
        
        return results
    
    def _convert_price_level(self, price_level_str: Optional[str]) -> Optional[int]:
        """Convert new API price level string to numeric value.
        
        Args:
            price_level_str: Price level from new API (e.g., "PRICE_LEVEL_MODERATE")
        
        Returns:
            Numeric price level (1-4) or None
        """
        if not price_level_str:
            return None
        
        mapping = {
            "PRICE_LEVEL_FREE": 0,
            "PRICE_LEVEL_INEXPENSIVE": 1,
            "PRICE_LEVEL_MODERATE": 2,
            "PRICE_LEVEL_EXPENSIVE": 3,
            "PRICE_LEVEL_VERY_EXPENSIVE": 4,
        }
        
        return mapping.get(price_level_str)
    
    def get_place_details(self, place_id: str, include_reviews: bool = True) -> Optional[PlaceDetails]:
        """Get detailed information about a place (NEW Places API).
        
        Args:
            place_id: Google Place ID
            include_reviews: Whether to include reviews
        
        Returns:
            Place details or None if not found
        """
        # NEW Places API - Get Place
        # The place_id needs to be prefixed with "places/" if not already
        if not place_id.startswith("places/"):
            place_id = f"places/{place_id}"
        url = f"{self.base_url}/{place_id}"
        
        field_mask = [
            "id", "displayName", "formattedAddress", "nationalPhoneNumber",
            "websiteUri", "rating", "userRatingCount", "priceLevel",
            "regularOpeningHours", "types"
        ]
        
        if include_reviews:
            field_mask.append("reviews")
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": ",".join(field_mask)
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            place = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching place details: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return None
        
        # Extract reviews
        reviews = []
        if include_reviews and "reviews" in place:
            for review in place.get("reviews", []):
                reviews.append({
                    "author_name": review.get("authorAttribution", {}).get("displayName", "Anonymous"),
                    "rating": review.get("rating", 0),
                    "text": review.get("text", {}).get("text", ""),
                    "time": review.get("publishTime", ""),
                })
        
        return PlaceDetails(
            place_id=place.get("id", ""),
            name=place.get("displayName", {}).get("text", "Unknown"),
            address=place.get("formattedAddress", ""),
            phone=place.get("nationalPhoneNumber"),
            website=place.get("websiteUri"),
            rating=place.get("rating"),
            user_ratings_total=place.get("userRatingCount"),
            price_level=self._convert_price_level(place.get("priceLevel")),
            reviews=reviews,
            photos=[],  # Photos require separate handling in new API
            opening_hours=place.get("regularOpeningHours"),
            types=place.get("types", []),
        )

