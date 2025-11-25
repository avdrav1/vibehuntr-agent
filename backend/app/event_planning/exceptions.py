"""Custom exception classes for the Event Planning Agent."""

from datetime import datetime
from typing import Any, Dict, Optional


class EventPlanningError(Exception):
    """Base exception for all Event Planning Agent errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the error.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Optional additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


# Validation Errors

class ValidationError(EventPlanningError):
    """Base class for validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: Field that failed validation
            details: Additional details
        """
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(message, "VALIDATION_ERROR", error_details)


class InvalidUserDataError(ValidationError):
    """Raised when user data is invalid."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, field)
        self.error_code = "INVALID_USER_DATA"


class InvalidGroupDataError(ValidationError):
    """Raised when group data is invalid."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, field)
        self.error_code = "INVALID_GROUP_DATA"


class InvalidEventDataError(ValidationError):
    """Raised when event data is invalid."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, field)
        self.error_code = "INVALID_EVENT_DATA"


class InvalidPreferenceDataError(ValidationError):
    """Raised when preference data is invalid."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, field)
        self.error_code = "INVALID_PREFERENCE_DATA"


class InvalidAvailabilityDataError(ValidationError):
    """Raised when availability data is invalid."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, field)
        self.error_code = "INVALID_AVAILABILITY_DATA"


class InvalidFeedbackDataError(ValidationError):
    """Raised when feedback data is invalid."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, field)
        self.error_code = "INVALID_FEEDBACK_DATA"


# Business Logic Errors

class BusinessLogicError(EventPlanningError):
    """Base class for business logic errors."""
    
    def __init__(self, message: str, error_code: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, details)


class EntityNotFoundError(BusinessLogicError):
    """Raised when an entity is not found."""
    
    def __init__(self, entity_type: str, entity_id: str):
        message = f"{entity_type} with id {entity_id} does not exist"
        details = {"entity_type": entity_type, "entity_id": entity_id}
        super().__init__(message, "ENTITY_NOT_FOUND", details)


class UserNotFoundError(EntityNotFoundError):
    """Raised when a user is not found."""
    
    def __init__(self, user_id: str):
        super().__init__("User", user_id)
        self.error_code = "USER_NOT_FOUND"


class GroupNotFoundError(EntityNotFoundError):
    """Raised when a group is not found."""
    
    def __init__(self, group_id: str):
        super().__init__("Group", group_id)
        self.error_code = "GROUP_NOT_FOUND"


class EventNotFoundError(EntityNotFoundError):
    """Raised when an event is not found."""
    
    def __init__(self, event_id: str):
        super().__init__("Event", event_id)
        self.error_code = "EVENT_NOT_FOUND"


class FeedbackNotFoundError(EntityNotFoundError):
    """Raised when feedback is not found."""
    
    def __init__(self, feedback_id: str):
        super().__init__("Feedback", feedback_id)
        self.error_code = "FEEDBACK_NOT_FOUND"


class MembershipError(BusinessLogicError):
    """Raised when there's an issue with group membership."""
    
    def __init__(self, message: str, user_id: str, group_id: str):
        details = {"user_id": user_id, "group_id": group_id}
        super().__init__(message, "MEMBERSHIP_ERROR", details)


class AlreadyMemberError(MembershipError):
    """Raised when trying to add a user who is already a member."""
    
    def __init__(self, user_id: str, group_id: str):
        message = f"User {user_id} is already a member of group {group_id}"
        super().__init__(message, user_id, group_id)
        self.error_code = "ALREADY_MEMBER"


class NotMemberError(MembershipError):
    """Raised when trying to operate on a user who is not a member."""
    
    def __init__(self, user_id: str, group_id: str):
        message = f"User {user_id} is not a member of group {group_id}"
        super().__init__(message, user_id, group_id)
        self.error_code = "NOT_MEMBER"


class NotParticipantError(BusinessLogicError):
    """Raised when a user is not a participant in an event."""
    
    def __init__(self, user_id: str, event_id: str):
        message = f"User {user_id} was not a participant in event {event_id}"
        details = {"user_id": user_id, "event_id": event_id}
        super().__init__(message, "NOT_PARTICIPANT", details)


class InsufficientAvailabilityError(BusinessLogicError):
    """Raised when there's insufficient availability for an event."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "INSUFFICIENT_AVAILABILITY", details)


class SchedulingConflictError(BusinessLogicError):
    """Raised when there's a scheduling conflict."""
    
    def __init__(self, message: str, conflicting_member_ids: list, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        error_details["conflicting_member_ids"] = conflicting_member_ids
        super().__init__(message, "SCHEDULING_CONFLICT", error_details)


class InvalidEventStatusError(BusinessLogicError):
    """Raised when an operation is invalid for the current event status."""
    
    def __init__(self, message: str, event_id: str, current_status: str, expected_status: Optional[str] = None):
        details = {
            "event_id": event_id,
            "current_status": current_status,
        }
        if expected_status:
            details["expected_status"] = expected_status
        super().__init__(message, "INVALID_EVENT_STATUS", details)


# Data Integrity Errors

class DataIntegrityError(EventPlanningError):
    """Base class for data integrity errors."""
    
    def __init__(self, message: str, error_code: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, details)


class DuplicateEntityError(DataIntegrityError):
    """Raised when trying to create an entity with a duplicate ID."""
    
    def __init__(self, entity_type: str, entity_id: str):
        message = f"{entity_type} with id {entity_id} already exists"
        details = {"entity_type": entity_type, "entity_id": entity_id}
        super().__init__(message, "DUPLICATE_ENTITY", details)


class OrphanedReferenceError(DataIntegrityError):
    """Raised when an entity references a non-existent entity."""
    
    def __init__(self, source_entity: str, target_entity: str, target_id: str):
        message = f"{source_entity} references non-existent {target_entity} with id {target_id}"
        details = {
            "source_entity": source_entity,
            "target_entity": target_entity,
            "target_id": target_id,
        }
        super().__init__(message, "ORPHANED_REFERENCE", details)


class ConcurrentModificationError(DataIntegrityError):
    """Raised when there's a concurrent modification conflict."""
    
    def __init__(self, entity_type: str, entity_id: str):
        message = f"{entity_type} with id {entity_id} was modified by another process"
        details = {"entity_type": entity_type, "entity_id": entity_id}
        super().__init__(message, "CONCURRENT_MODIFICATION", details)


# Storage Errors

class StorageError(EventPlanningError):
    """Base class for storage-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "STORAGE_ERROR", details)


class FileStorageError(StorageError):
    """Raised when there's an error with file storage operations."""
    
    def __init__(self, message: str, file_path: Optional[str] = None):
        details = {}
        if file_path:
            details["file_path"] = file_path
        super().__init__(message, details)
        self.error_code = "FILE_STORAGE_ERROR"
