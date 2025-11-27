"""Error logging utilities for the Event Planning Agent."""

import logging
import traceback
from typing import Any, Dict, Optional
from .exceptions import EventPlanningError


# Configure logger
logger = logging.getLogger("event_planning_agent")


def log_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    level: int = logging.ERROR
) -> None:
    """
    Log an error with context information.
    
    Args:
        error: The exception to log
        context: Additional context information
        level: Logging level (default: ERROR)
    """
    context = context or {}
    
    if isinstance(error, EventPlanningError):
        # Log structured error information
        error_info = error.to_dict()
        error_info.update(context)
        
        logger.log(
            level,
            f"[{error.error_code}] {error.message}",
            extra={
                "error_code": error.error_code,
                "error_details": error.details,
                "context": context,
                "timestamp": error.timestamp.isoformat(),
            }
        )
    else:
        # Log generic exception
        logger.log(
            level,
            f"Unexpected error: {str(error)}",
            extra={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context,
                "traceback": traceback.format_exc(),
            }
        )


def log_validation_error(
    error: Exception,
    entity_type: str,
    entity_data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a validation error with entity information.
    
    Args:
        error: The validation exception
        entity_type: Type of entity being validated
        entity_data: The entity data that failed validation
    """
    context = {
        "entity_type": entity_type,
    }
    
    # Don't log full entity data for privacy, just the ID if available
    if entity_data and "id" in entity_data:
        context["entity_id"] = entity_data["id"]
    
    log_error(error, context, logging.WARNING)


def log_business_logic_error(
    error: Exception,
    operation: str,
    entity_ids: Optional[Dict[str, str]] = None
) -> None:
    """
    Log a business logic error with operation context.
    
    Args:
        error: The business logic exception
        operation: The operation that failed
        entity_ids: Dictionary of entity types to IDs involved
    """
    context = {
        "operation": operation,
    }
    
    if entity_ids:
        context.update(entity_ids)
    
    log_error(error, context, logging.WARNING)


def log_data_integrity_error(
    error: Exception,
    operation: str,
    affected_entities: Optional[Dict[str, str]] = None
) -> None:
    """
    Log a data integrity error.
    
    Args:
        error: The data integrity exception
        operation: The operation that caused the integrity issue
        affected_entities: Dictionary of entity types to IDs affected
    """
    context = {
        "operation": operation,
        "severity": "HIGH",
    }
    
    if affected_entities:
        context["affected_entities"] = affected_entities
    
    log_error(error, context, logging.ERROR)


def log_storage_error(
    error: Exception,
    operation: str,
    storage_path: Optional[str] = None
) -> None:
    """
    Log a storage error.
    
    Args:
        error: The storage exception
        operation: The storage operation that failed
        storage_path: Path to the storage location
    """
    context = {
        "operation": operation,
    }
    
    if storage_path:
        context["storage_path"] = storage_path
    
    log_error(error, context, logging.ERROR)


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure logging for the Event Planning Agent.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Set logger for event planning agent
    logger.setLevel(getattr(logging, log_level.upper()))
