"""Response tracking module for detecting and logging response duplication.

This module provides the ResponseTracker class for tracking response generation,
detecting duplicates, and collecting metrics about response quality.
"""

import logging
import uuid
from typing import Set, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ResponseMetadata:
    """Metadata about a response generation.
    
    This class captures comprehensive information about a response generation
    event for logging and monitoring purposes.
    """
    
    response_id: str
    session_id: str
    user_id: str
    timestamp: datetime
    total_chunks: int = 0
    duplicate_chunks: int = 0
    duplication_rate: float = 0.0
    model_used: str = "gemini-2.0-flash-exp"
    temperature: float = 0.7
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging.
        
        Returns:
            Dict with all metadata fields
        """
        return {
            "response_id": self.response_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "total_chunks": self.total_chunks,
            "duplicate_chunks": self.duplicate_chunks,
            "duplication_rate": self.duplication_rate,
            "model_used": self.model_used,
            "temperature": self.temperature
        }


@dataclass
class DuplicationEvent:
    """Event logged when duplication is detected.
    
    This class captures information about a specific duplication event
    for debugging and analysis.
    """
    
    event_id: str
    session_id: str
    response_id: str
    timestamp: datetime
    duplicate_chunk: str
    chunk_index: int
    detection_method: str  # "hash", "pattern", "similarity"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging.
        
        Returns:
            Dict with all event fields
        """
        return {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "response_id": self.response_id,
            "timestamp": self.timestamp.isoformat(),
            "duplicate_chunk_preview": self.duplicate_chunk[:100] if self.duplicate_chunk else "",
            "chunk_index": self.chunk_index,
            "detection_method": self.detection_method
        }


class ResponseTracker:
    """Track response generation to detect duplication.
    
    This class provides comprehensive tracking of response generation events,
    including chunk tracking, duplicate detection, and metrics collection.
    
    Attributes:
        session_id: Session identifier
        response_id: Unique identifier for this response
        chunks_seen: Set of chunk hashes we've already seen
        total_chunks: Total number of chunks processed
        duplicate_chunks: Number of duplicate chunks detected
        
    Example:
        >>> tracker = ResponseTracker("session_123")
        >>> is_unique = tracker.track_chunk("Hello world")
        >>> metrics = tracker.get_metrics()
    """
    
    def __init__(self, session_id: str, user_id: str = "default_user"):
        """Initialize response tracker.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
        """
        self.session_id = session_id
        self.user_id = user_id
        self.response_id = self._generate_unique_id()
        self.chunks_seen: Set[int] = set()
        self.total_chunks = 0
        self.duplicate_chunks = 0
        self.start_time = datetime.now()
        
        # Log response generation start
        logger.info(
            f"Response generation started",
            extra={
                "timestamp": self.start_time.isoformat(),
                "response_id": self.response_id,
                "session_id": self.session_id,
                "user_id": self.user_id
            }
        )
    
    def _generate_unique_id(self) -> str:
        """Generate a unique response ID.
        
        Returns:
            UUID string
        """
        return str(uuid.uuid4())
    
    def track_chunk(self, chunk: str) -> bool:
        """Track a response chunk and detect if it's a duplicate.
        
        This method tracks each chunk of the response and detects duplicates
        using hash-based comparison. It logs all tracking events for debugging.
        
        Args:
            chunk: Response chunk text
            
        Returns:
            bool: True if chunk is unique, False if duplicate
        """
        try:
            self.total_chunks += 1
            chunk_hash = hash(chunk)
            
            # Log chunk tracking
            try:
                logger.debug(
                    f"Tracking chunk {self.total_chunks}",
                    extra={
                        "timestamp": datetime.now().isoformat(),
                        "response_id": self.response_id,
                        "session_id": self.session_id,
                        "chunk_index": self.total_chunks,
                        "chunk_length": len(chunk),
                        "chunk_hash": chunk_hash
                    }
                )
            except Exception as log_error:
                # Fallback to basic logging if structured logging fails
                print(
                    f"Debug: Tracking chunk {self.total_chunks}",
                    file=__import__('sys').stderr
                )
            
            if chunk_hash in self.chunks_seen:
                # Duplicate detected
                self.duplicate_chunks += 1
                
                # Create duplication event
                try:
                    event = DuplicationEvent(
                        event_id=str(uuid.uuid4()),
                        session_id=self.session_id,
                        response_id=self.response_id,
                        timestamp=datetime.now(),
                        duplicate_chunk=chunk,
                        chunk_index=self.total_chunks,
                        detection_method="hash"
                    )
                    
                    # Log duplication event
                    try:
                        logger.warning(
                            f"Duplicate chunk detected",
                            extra=event.to_dict()
                        )
                    except Exception as log_error:
                        # Fallback to basic logging
                        print(
                            f"Warning: Duplicate chunk detected",
                            file=__import__('sys').stderr
                        )
                except Exception as event_error:
                    # Log error but continue
                    logger.error(
                        f"Failed to create duplication event: {type(event_error).__name__}: {event_error}",
                        exc_info=True
                    )
                
                return False
            
            # Unique chunk
            self.chunks_seen.add(chunk_hash)
            
            # Log unique chunk
            try:
                logger.debug(
                    f"Unique chunk tracked",
                    extra={
                        "timestamp": datetime.now().isoformat(),
                        "response_id": self.response_id,
                        "session_id": self.session_id,
                        "chunk_index": self.total_chunks,
                        "unique_chunks": len(self.chunks_seen)
                    }
                )
            except Exception as log_error:
                # Fallback to basic logging
                pass  # Don't log debug messages to stderr
            
            return True
            
        except Exception as e:
            # If tracking fails completely, log error and return True
            # (graceful degradation - better to show potential duplicate than crash)
            logger.error(
                f"Chunk tracking failed: {type(e).__name__}: {e}",
                exc_info=True
            )
            return True
    
    def get_metrics(self) -> ResponseMetadata:
        """Get duplication metrics for this response.
        
        Returns:
            ResponseMetadata with all tracking information
        """
        try:
            duplication_rate = (
                self.duplicate_chunks / self.total_chunks
                if self.total_chunks > 0
                else 0.0
            )
            
            metadata = ResponseMetadata(
                response_id=self.response_id,
                session_id=self.session_id,
                user_id=self.user_id,
                timestamp=self.start_time,
                total_chunks=self.total_chunks,
                duplicate_chunks=self.duplicate_chunks,
                duplication_rate=duplication_rate
            )
            
            # Log metrics
            try:
                logger.info(
                    f"Response generation completed",
                    extra=metadata.to_dict()
                )
            except Exception as log_error:
                # Fallback to basic logging
                print(
                    f"Info: Response generation completed",
                    file=__import__('sys').stderr
                )
            
            return metadata
            
        except Exception as e:
            # If metrics collection fails, return default metadata
            logger.error(
                f"Failed to get metrics: {type(e).__name__}: {e}",
                exc_info=True
            )
            # Return minimal metadata
            return ResponseMetadata(
                response_id=self.response_id,
                session_id=self.session_id,
                user_id=self.user_id,
                timestamp=self.start_time,
                total_chunks=0,
                duplicate_chunks=0,
                duplication_rate=0.0
            )
    
    def log_token_yield(self, token: str, token_index: int) -> None:
        """Log token yielding event.
        
        Args:
            token: Token text
            token_index: Index of token in sequence
        """
        try:
            logger.debug(
                f"Token yielded",
                extra={
                    "timestamp": datetime.now().isoformat(),
                    "response_id": self.response_id,
                    "session_id": self.session_id,
                    "token_index": token_index,
                    "token_length": len(token)
                }
            )
        except Exception as e:
            # Don't let logging failures affect functionality
            pass  # Debug logging failures are not critical
    
    def log_session_history_update(self, message_role: str, message_content: str) -> None:
        """Log session history update event.
        
        Args:
            message_role: Role of the message (user/assistant)
            message_content: Content of the message
        """
        try:
            logger.info(
                f"Session history updated",
                extra={
                    "timestamp": datetime.now().isoformat(),
                    "response_id": self.response_id,
                    "session_id": self.session_id,
                    "message_role": message_role,
                    "message_length": len(message_content)
                }
            )
        except Exception as e:
            # Don't let logging failures affect functionality
            logger.error(
                f"Failed to log session history update: {type(e).__name__}: {e}",
                exc_info=True
            )
