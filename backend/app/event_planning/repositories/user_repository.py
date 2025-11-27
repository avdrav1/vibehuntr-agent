"""User repository implementation."""

from typing import Dict, List, Optional
from app.event_planning.models.user import User, PreferenceProfile, AvailabilityWindow
from app.event_planning.repositories.base import JsonFileRepository
from app.event_planning.exceptions import (
    UserNotFoundError,
    InvalidPreferenceDataError,
    InvalidAvailabilityDataError,
    ValidationError,
)
from app.event_planning.error_logging import log_business_logic_error, log_validation_error


class UserRepository(JsonFileRepository[User]):
    """Repository for User entities."""
    
    def __init__(self, storage_dir: str = "data"):
        """Initialize the user repository."""
        super().__init__(storage_dir, "users")
    
    def _dict_to_entity(self, data: Dict) -> User:
        """Convert dictionary to User entity."""
        return User.from_dict(data)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address."""
        for user in self.list_all():
            if user.email == email:
                return user
        return None
    
    def update_preference_profile(self, user_id: str, preference_profile: PreferenceProfile) -> User:
        """Update a user's preference profile."""
        user = self.get(user_id)
        if not user:
            error = UserNotFoundError(user_id)
            log_business_logic_error(error, "update_preference_profile", {"user_id": user_id})
            raise error
        
        # Validate that the preference profile belongs to this user
        if preference_profile.user_id != user_id:
            error = InvalidPreferenceDataError(
                "Preference profile user_id must match user id",
                field="user_id"
            )
            log_validation_error(error, "PreferenceProfile", {"user_id": user_id})
            raise error
        
        try:
            preference_profile.validate()
        except ValueError as e:
            error = InvalidPreferenceDataError(str(e))
            log_validation_error(error, "PreferenceProfile", {"user_id": user_id})
            raise error
        
        user.preference_profile = preference_profile
        return self.update(user)
    
    def add_availability_window(self, user_id: str, window: AvailabilityWindow) -> User:
        """Add an availability window to a user."""
        user = self.get(user_id)
        if not user:
            error = UserNotFoundError(user_id)
            log_business_logic_error(error, "add_availability_window", {"user_id": user_id})
            raise error
        
        # Validate that the window belongs to this user
        if window.user_id != user_id:
            error = InvalidAvailabilityDataError(
                "Availability window user_id must match user id",
                field="user_id"
            )
            log_validation_error(error, "AvailabilityWindow", {"user_id": user_id})
            raise error
        
        try:
            window.validate()
        except ValueError as e:
            error = InvalidAvailabilityDataError(str(e))
            log_validation_error(error, "AvailabilityWindow", {"user_id": user_id})
            raise error
        
        user.availability_windows.append(window)
        return self.update(user)
    
    def update_availability_window(self, user_id: str, window_index: int, window: AvailabilityWindow) -> User:
        """Update an availability window for a user."""
        user = self.get(user_id)
        if not user:
            error = UserNotFoundError(user_id)
            log_business_logic_error(error, "update_availability_window", {"user_id": user_id})
            raise error
        
        if window_index < 0 or window_index >= len(user.availability_windows):
            error = InvalidAvailabilityDataError(
                f"Invalid window index {window_index}",
                field="window_index"
            )
            log_validation_error(error, "AvailabilityWindow", {"user_id": user_id, "window_index": window_index})
            raise error
        
        # Validate that the window belongs to this user
        if window.user_id != user_id:
            error = InvalidAvailabilityDataError(
                "Availability window user_id must match user id",
                field="user_id"
            )
            log_validation_error(error, "AvailabilityWindow", {"user_id": user_id})
            raise error
        
        try:
            window.validate()
        except ValueError as e:
            error = InvalidAvailabilityDataError(str(e))
            log_validation_error(error, "AvailabilityWindow", {"user_id": user_id})
            raise error
        
        user.availability_windows[window_index] = window
        return self.update(user)
    
    def remove_availability_window(self, user_id: str, window_index: int) -> User:
        """Remove an availability window from a user."""
        user = self.get(user_id)
        if not user:
            error = UserNotFoundError(user_id)
            log_business_logic_error(error, "remove_availability_window", {"user_id": user_id})
            raise error
        
        if window_index < 0 or window_index >= len(user.availability_windows):
            error = InvalidAvailabilityDataError(
                f"Invalid window index {window_index}",
                field="window_index"
            )
            log_validation_error(error, "AvailabilityWindow", {"user_id": user_id, "window_index": window_index})
            raise error
        
        user.availability_windows.pop(window_index)
        return self.update(user)
