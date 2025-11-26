"""Agent tools for Google Places integration."""

from typing import Optional
from backend.app.event_planning.google_places_service import GooglePlacesService


# Global service instance
_places_service: Optional[GooglePlacesService] = None


def get_places_service() -> GooglePlacesService:
    """Get or create the Google Places service instance."""
    global _places_service
    if _places_service is None:
        _places_service = GooglePlacesService()
    return _places_service


def search_venues_tool(
    query: str,
    location: Optional[str] = None,
    min_rating: Optional[float] = None,
    max_price: Optional[int] = None
) -> str:
    """
    Search for real venues and locations using Google Places.
    
    Use this when someone wants to find restaurants, activities, or venues for their event.
    
    Args:
        query: What to search for (e.g., "Italian restaurants", "hiking trails", "museums")
        location: Where to search (e.g., "San Francisco", "Downtown Seattle")
        min_rating: Minimum rating (1-5 stars)
        max_price: Maximum price level (1-4, where 4 is most expensive)
    
    Returns:
        Formatted list of venues with ratings, prices, and addresses.
    """
    try:
        service = get_places_service()
        
        results = service.search_places(
            query=query,
            location=location,
            min_rating=min_rating,
            max_results=5
        )
        
        if not results:
            return f"No venues found for '{query}'" + (f" in {location}" if location else "")
        
        output = f"Found {len(results)} venue(s) for '{query}':\n\n"
        
        for i, place in enumerate(results, 1):
            output += f"{i}. **{place.name}**\n"
            output += f"   📍 {place.address}\n"
            
            if place.rating:
                stars = "⭐" * int(place.rating)
                output += f"   {stars} {place.rating}/5 ({place.user_ratings_total or 0} reviews)\n"
            
            if place.price_level:
                price = "$" * place.price_level
                output += f"   💰 Price: {price}\n"
            
            # Filter by max_price if specified
            if max_price and place.price_level and place.price_level > max_price:
                output += f"   ⚠️ Above budget (price level {place.price_level})\n"
            
            output += f"   🆔 Place ID: {place.place_id}\n\n"
        
        return output
    
    except ValueError as e:
        return f"❌ Google Places API not configured: {str(e)}\n\nTo enable venue search, add GOOGLE_PLACES_API_KEY to your .env file.\nGet a key at: https://console.cloud.google.com/apis/credentials"
    except Exception as e:
        return f"Error searching venues: {str(e)}"


def get_venue_details_tool(place_id: str) -> str:
    """
    Get detailed information about a specific venue including reviews.
    
    Use this when someone wants more details about a venue from search results.
    
    Args:
        place_id: The Google Place ID from search results
    
    Returns:
        Detailed venue information including reviews, hours, and contact info.
    """
    try:
        service = get_places_service()
        
        details = service.get_place_details(place_id, include_reviews=True)
        
        if not details:
            return f"Venue with ID '{place_id}' not found."
        
        output = f"**{details.name}**\n\n"
        output += f"📍 Address: {details.address}\n"
        
        if details.phone:
            output += f"📞 Phone: {details.phone}\n"
        
        if details.website:
            output += f"🌐 Website: {details.website}\n"
        
        # Include Place ID for consistency and link detection
        output += f"🆔 Place ID: {details.place_id}\n"
        
        if details.rating:
            stars = "⭐" * int(details.rating)
            output += f"\n{stars} {details.rating}/5 ({details.user_ratings_total or 0} reviews)\n"
        
        if details.price_level:
            price = "$" * details.price_level
            output += f"💰 Price Level: {price}\n"
        
        if details.opening_hours:
            output += f"\n⏰ Hours: "
            if details.opening_hours.get("open_now"):
                output += "Open now ✅\n"
            else:
                output += "Closed ❌\n"
        
        # Include top reviews
        if details.reviews:
            output += f"\n📝 Recent Reviews:\n\n"
            for i, review in enumerate(details.reviews[:3], 1):
                rating = "⭐" * review.get("rating", 0)
                author = review.get("author_name", "Anonymous")
                text = review.get("text", "")[:200]  # Truncate long reviews
                output += f"{i}. {rating} - {author}\n"
                output += f"   \"{text}...\"\n\n"
        
        return output
    
    except ValueError as e:
        return f"❌ Google Places API not configured: {str(e)}"
    except Exception as e:
        return f"Error getting venue details: {str(e)}"


# Export tools
PLACES_TOOLS = [
    search_venues_tool,
    get_venue_details_tool,
]
