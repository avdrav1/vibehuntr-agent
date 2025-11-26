"""Recommendation engine for generating event suggestions."""

from typing import List, Optional, Dict
from dataclasses import dataclass, field

from backend.app.event_planning.models.user import User
from backend.app.event_planning.models.group import FriendGroup
from backend.app.event_planning.models.suggestion import EventSuggestion


@dataclass
class SearchFilters:
    """Filters for searching event suggestions."""
    
    activity_keywords: List[str] = field(default_factory=list)
    location_area: Optional[str] = None
    date_range: Optional[tuple] = None  # (start_datetime, end_datetime)
    budget_max: Optional[float] = None
    
    def validate(self) -> None:
        """Validate the search filters."""
        if self.budget_max is not None and self.budget_max < 0:
            raise ValueError("budget_max cannot be negative")
        if self.date_range is not None:
            if len(self.date_range) != 2:
                raise ValueError("date_range must be a tuple of (start_datetime, end_datetime)")
            start_date, end_date = self.date_range
            if start_date >= end_date:
                raise ValueError("date_range start must be before end")


class RecommendationEngine:
    """
    Generates event suggestions based on group preferences.
    
    The engine calculates consensus scores by analyzing individual user preferences
    and finding suggestions that maximize overall group satisfaction.
    """
    
    def __init__(self, priority_weight_multiplier: float = 1.5):
        """
        Initialize the recommendation engine.
        
        Args:
            priority_weight_multiplier: Multiplier for priority member scores (default 1.5)
        """
        self.priority_weight_multiplier = priority_weight_multiplier
    
    def generate_suggestions(
        self,
        group: FriendGroup,
        users: List[User],
        suggestions: List[EventSuggestion],
        filters: Optional[SearchFilters] = None
    ) -> List[EventSuggestion]:
        """
        Generate and rank event suggestions for a friend group.
        
        Args:
            group: The friend group
            users: List of users in the group
            suggestions: List of candidate suggestions to score and rank
            filters: Optional search filters to apply
        
        Returns:
            List of suggestions ranked by consensus score
        """
        # Validate that all users are in the group
        user_ids = {user.id for user in users}
        for member_id in group.member_ids:
            if member_id not in user_ids:
                raise ValueError(f"User {member_id} from group not found in users list")
        
        # Apply filters if provided
        if filters:
            suggestions = self._apply_filters(suggestions, filters)
        
        # Calculate consensus scores for each suggestion
        scored_suggestions = []
        for suggestion in suggestions:
            # Calculate individual compatibility scores
            member_compatibility = {}
            for user in users:
                if user.id in group.member_ids:
                    compatibility = self._calculate_individual_compatibility(suggestion, user)
                    member_compatibility[user.id] = compatibility
            
            # Calculate consensus score
            consensus_score = self.calculate_consensus_score(
                suggestion, users, group.priority_member_ids
            )
            
            # Create a new suggestion with updated scores
            scored_suggestion = EventSuggestion(
                id=suggestion.id,
                activity_type=suggestion.activity_type,
                location=suggestion.location,
                estimated_duration=suggestion.estimated_duration,
                estimated_cost_per_person=suggestion.estimated_cost_per_person,
                description=suggestion.description,
                consensus_score=consensus_score,
                member_compatibility=member_compatibility,
                available_start_date=suggestion.available_start_date,
                available_end_date=suggestion.available_end_date,
            )
            scored_suggestions.append(scored_suggestion)
        
        # Rank suggestions by consensus score
        return self.rank_suggestions(scored_suggestions)
    
    def calculate_consensus_score(
        self,
        suggestion: EventSuggestion,
        users: List[User],
        priority_member_ids: Optional[List[str]] = None
    ) -> float:
        """
        Calculate consensus score for a suggestion based on user preferences.
        
        The consensus score is a weighted average of individual compatibility scores,
        with priority members receiving higher weight.
        
        Args:
            suggestion: The event suggestion to score
            users: List of users to consider
            priority_member_ids: Optional list of priority member IDs
        
        Returns:
            Consensus score between 0 and 1
        """
        if not users:
            return 0.0
        
        priority_ids = set(priority_member_ids or [])
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for user in users:
            compatibility = self._calculate_individual_compatibility(suggestion, user)
            
            # Apply priority weighting
            weight = self.priority_weight_multiplier if user.id in priority_ids else 1.0
            
            total_weighted_score += compatibility * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        consensus_score = total_weighted_score / total_weight
        
        # Ensure score is in valid range
        return max(0.0, min(1.0, consensus_score))
    
    def _calculate_individual_compatibility(
        self,
        suggestion: EventSuggestion,
        user: User
    ) -> float:
        """
        Calculate how compatible a suggestion is with a user's preferences.
        
        Args:
            suggestion: The event suggestion
            user: The user
        
        Returns:
            Compatibility score between 0 and 1
        """
        profile = user.preference_profile
        
        # Start with activity preference weight
        activity_score = profile.activity_preferences.get(suggestion.activity_type, 0.5)
        
        # Check budget constraint
        budget_score = 1.0
        if profile.budget_max is not None:
            if suggestion.estimated_cost_per_person > profile.budget_max:
                budget_score = 0.0
            else:
                # Partial score based on how much of budget is used
                budget_score = 1.0 - (suggestion.estimated_cost_per_person / profile.budget_max) * 0.5
        
        # Check location preference
        location_score = 0.5  # Default neutral score
        if profile.location_preferences:
            # Check if suggestion location matches any preferred locations
            suggestion_location = suggestion.location.name.lower()
            for pref_location in profile.location_preferences:
                if pref_location.lower() in suggestion_location:
                    location_score = 1.0
                    break
        
        # Weighted average of all factors
        # Activity preference is most important (50%), budget (30%), location (20%)
        compatibility = (
            activity_score * 0.5 +
            budget_score * 0.3 +
            location_score * 0.2
        )
        
        return max(0.0, min(1.0, compatibility))
    
    def rank_suggestions(self, suggestions: List[EventSuggestion]) -> List[EventSuggestion]:
        """
        Rank suggestions by consensus score in descending order.
        
        Args:
            suggestions: List of suggestions to rank
        
        Returns:
            Sorted list of suggestions (highest consensus score first)
        """
        return sorted(suggestions, key=lambda s: s.consensus_score, reverse=True)
    
    def _apply_filters(
        self,
        suggestions: List[EventSuggestion],
        filters: SearchFilters
    ) -> List[EventSuggestion]:
        """
        Apply search filters to suggestions.
        
        Args:
            suggestions: List of suggestions to filter
            filters: Search filters to apply
        
        Returns:
            Filtered list of suggestions
        """
        filtered = suggestions
        
        # Activity keyword filter
        if filters.activity_keywords:
            filtered = [
                s for s in filtered
                if any(
                    keyword.lower() in s.activity_type.lower() or
                    keyword.lower() in s.description.lower()
                    for keyword in filters.activity_keywords
                )
            ]
        
        # Location filter
        if filters.location_area:
            filtered = [
                s for s in filtered
                if filters.location_area.lower() in s.location.name.lower() or
                   filters.location_area.lower() in s.location.address.lower()
            ]
        
        # Date range filter
        if filters.date_range is not None:
            start_date, end_date = filters.date_range
            filtered = [
                s for s in filtered
                if s.available_start_date is not None and s.available_end_date is not None and
                   # Check if suggestion's availability overlaps with the filter date range
                   s.available_start_date <= end_date and s.available_end_date >= start_date
            ]
        
        # Budget filter
        if filters.budget_max is not None:
            filtered = [
                s for s in filtered
                if s.estimated_cost_per_person <= filters.budget_max
            ]
        
        return filtered
