"""Base repository interface and JSON storage implementation."""

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Generic, List, Optional, TypeVar

from app.event_planning.exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
    FileStorageError,
    ValidationError,
)
from app.event_planning.error_logging import log_storage_error, log_validation_error

T = TypeVar('T')


class Repository(ABC, Generic[T]):
    """Abstract base repository interface."""
    
    @abstractmethod
    def create(self, entity: T) -> T:
        """Create a new entity."""
        pass
    
    @abstractmethod
    def get(self, entity_id: str) -> Optional[T]:
        """Get an entity by ID."""
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """Update an existing entity."""
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID."""
        pass
    
    @abstractmethod
    def list_all(self) -> List[T]:
        """List all entities."""
        pass


class JsonFileRepository(Repository[T], Generic[T]):
    """JSON file-based storage implementation."""
    
    def __init__(self, storage_dir: str, entity_type: str):
        """
        Initialize the repository.
        
        Args:
            storage_dir: Base directory for storage
            entity_type: Type of entity (e.g., 'users', 'groups')
        """
        self.storage_dir = Path(storage_dir) / entity_type
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, entity_id: str) -> Path:
        """Get the file path for an entity."""
        return self.storage_dir / f"{entity_id}.json"
    
    def _entity_to_dict(self, entity: T) -> Dict:
        """Convert entity to dictionary. Override if needed."""
        if hasattr(entity, 'to_dict'):
            return entity.to_dict()
        raise NotImplementedError("Entity must have to_dict method")
    
    def _dict_to_entity(self, data: Dict) -> T:
        """Convert dictionary to entity. Must be implemented by subclass."""
        raise NotImplementedError("Subclass must implement _dict_to_entity")
    
    def create(self, entity: T) -> T:
        """Create a new entity."""
        entity_id = getattr(entity, 'id')
        file_path = self._get_file_path(entity_id)
        
        if file_path.exists():
            error = DuplicateEntityError(type(entity).__name__, entity_id)
            log_storage_error(error, "create", str(file_path))
            raise error
        
        # Validate entity if it has a validate method
        if hasattr(entity, 'validate'):
            try:
                entity.validate()
            except ValueError as e:
                error = ValidationError(str(e), details={"entity_id": entity_id})
                log_validation_error(error, type(entity).__name__, {"id": entity_id})
                raise error
        
        try:
            data = self._entity_to_dict(entity)
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except (IOError, OSError) as e:
            error = FileStorageError(f"Failed to create entity: {str(e)}", str(file_path))
            log_storage_error(error, "create", str(file_path))
            raise error
        
        return entity
    
    def get(self, entity_id: str) -> Optional[T]:
        """Get an entity by ID."""
        file_path = self._get_file_path(entity_id)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return self._dict_to_entity(data)
        except (IOError, OSError, json.JSONDecodeError) as e:
            error = FileStorageError(f"Failed to read entity: {str(e)}", str(file_path))
            log_storage_error(error, "get", str(file_path))
            raise error
    
    def update(self, entity: T) -> T:
        """Update an existing entity."""
        entity_id = getattr(entity, 'id')
        file_path = self._get_file_path(entity_id)
        
        if not file_path.exists():
            error = EntityNotFoundError(type(entity).__name__, entity_id)
            log_storage_error(error, "update", str(file_path))
            raise error
        
        # Validate entity if it has a validate method
        if hasattr(entity, 'validate'):
            try:
                entity.validate()
            except ValueError as e:
                error = ValidationError(str(e), details={"entity_id": entity_id})
                log_validation_error(error, type(entity).__name__, {"id": entity_id})
                raise error
        
        try:
            data = self._entity_to_dict(entity)
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except (IOError, OSError) as e:
            error = FileStorageError(f"Failed to update entity: {str(e)}", str(file_path))
            log_storage_error(error, "update", str(file_path))
            raise error
        
        return entity
    
    def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID."""
        file_path = self._get_file_path(entity_id)
        
        if not file_path.exists():
            return False
        
        os.remove(file_path)
        return True
    
    def list_all(self) -> List[T]:
        """List all entities."""
        entities = []
        
        try:
            for file_path in self.storage_dir.glob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    entities.append(self._dict_to_entity(data))
                except (IOError, OSError, json.JSONDecodeError) as e:
                    # Log error but continue processing other files
                    error = FileStorageError(f"Failed to read entity from {file_path}: {str(e)}", str(file_path))
                    log_storage_error(error, "list_all", str(file_path))
                    # Continue to next file instead of failing completely
                    continue
        except Exception as e:
            error = FileStorageError(f"Failed to list entities: {str(e)}", str(self.storage_dir))
            log_storage_error(error, "list_all", str(self.storage_dir))
            raise error
        
        return entities
