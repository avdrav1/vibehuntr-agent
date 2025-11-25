"""Duplication metrics module for monitoring and alerting.

This module provides the DuplicationMetrics class for tracking duplication
metrics, calculating rates, and logging warnings and confirmations.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from threading import Lock
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SessionMetrics:
    """Metrics for a specific session."""
    
    session_id: str
    total_responses: int = 0
    responses_with_duplicates: int = 0
    total_duplicates_detected: int = 0
    last_duplication_time: Optional[datetime] = None
    last_clean_response_time: Optional[datetime] = None
    
    def get_duplication_rate(self) -> float:
        """Calculate duplication rate for this session.
        
        Returns:
            Float between 0.0 and 1.0 representing the rate
        """
        if self.total_responses == 0:
            return 0.0
        return self.responses_with_duplicates / self.total_responses
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "session_id": self.session_id,
            "total_responses": self.total_responses,
            "responses_with_duplicates": self.responses_with_duplicates,
            "total_duplicates_detected": self.total_duplicates_detected,
            "duplication_rate": self.get_duplication_rate(),
            "last_duplication_time": self.last_duplication_time.isoformat() if self.last_duplication_time else None,
            "last_clean_response_time": self.last_clean_response_time.isoformat() if self.last_clean_response_time else None
        }


class DuplicationMetrics:
    """Track duplication metrics for monitoring and alerting.
    
    This class provides a centralized way to track duplication events,
    calculate rates, and log warnings and confirmations. It is thread-safe
    and can be used across multiple sessions.
    
    Attributes:
        _session_metrics: Dictionary mapping session IDs to SessionMetrics
        _global_duplicates: Total number of duplicates detected across all sessions
        _global_responses: Total number of responses across all sessions
        _lock: Thread lock for thread-safe operations
        _enable_logging: Whether to enable logging (can be disabled for tests)
        
    Example:
        >>> metrics = DuplicationMetrics()
        >>> metrics.increment_duplicate_detected("session_123")
        >>> rate = metrics.get_duplication_rate("session_123")
    """
    
    def __init__(self, enable_logging: bool = True):
        """Initialize duplication metrics tracker.
        
        Args:
            enable_logging: Whether to enable logging (default: True)
        """
        self._session_metrics: Dict[str, SessionMetrics] = {}
        self._global_duplicates = 0
        self._global_responses = 0
        self._lock = Lock()
        self._enable_logging = enable_logging
        
        if self._enable_logging:
            logger.info(
                "DuplicationMetrics initialized",
                extra={
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    def _get_or_create_session_metrics(self, session_id: str) -> SessionMetrics:
        """Get or create metrics for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            SessionMetrics for the session
        """
        if session_id not in self._session_metrics:
            self._session_metrics[session_id] = SessionMetrics(session_id=session_id)
            logger.debug(
                f"Created new session metrics for {session_id}",
                extra={
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id
                }
            )
        return self._session_metrics[session_id]
    
    def increment_duplicate_detected(self, session_id: str, count: int = 1) -> None:
        """Increment counter when duplicate is detected.
        
        This method increments the duplication counter for a specific session
        and logs a warning with session context.
        
        Args:
            session_id: Session identifier
            count: Number of duplicates to add (default: 1)
        """
        try:
            with self._lock:
                # Update session metrics
                try:
                    session_metrics = self._get_or_create_session_metrics(session_id)
                    session_metrics.total_duplicates_detected += count
                    session_metrics.last_duplication_time = datetime.now()
                    
                    # Update global counter
                    self._global_duplicates += count
                except Exception as metrics_error:
                    # Log error but don't crash
                    logger.error(
                        f"Failed to update duplicate metrics: {type(metrics_error).__name__}: {metrics_error}",
                        exc_info=True
                    )
                    return
                
                # Log warning with session context (only log every 10th duplicate to avoid performance issues)
                if self._enable_logging and session_metrics.total_duplicates_detected % 10 == 1:
                    try:
                        logger.warning(
                            f"Duplicate detected in session {session_id}",
                            extra={
                                "timestamp": datetime.now().isoformat(),
                                "session_id": session_id,
                                "duplicates_in_session": session_metrics.total_duplicates_detected,
                                "total_global_duplicates": self._global_duplicates
                            }
                        )
                    except Exception as log_error:
                        # Fallback to basic logging
                        print(
                            f"Warning: Duplicate detected in session {session_id}",
                            file=__import__('sys').stderr
                        )
        except Exception as e:
            # Don't let metrics failures affect functionality
            logger.error(
                f"Failed to increment duplicate counter: {type(e).__name__}: {e}",
                exc_info=True
            )
    
    def record_response_quality(
        self,
        session_id: str,
        total_chunks: int,
        duplicate_chunks: int
    ) -> None:
        """Record response quality metrics.
        
        This method records metrics about a completed response, including
        whether it contained duplicates.
        
        Args:
            session_id: Session identifier
            total_chunks: Total number of chunks in the response
            duplicate_chunks: Number of duplicate chunks detected
        """
        try:
            with self._lock:
                # Update session metrics
                try:
                    session_metrics = self._get_or_create_session_metrics(session_id)
                    session_metrics.total_responses += 1
                    
                    # Update global response counter
                    self._global_responses += 1
                except Exception as metrics_error:
                    # Log error but don't crash
                    logger.error(
                        f"Failed to update response quality metrics: {type(metrics_error).__name__}: {metrics_error}",
                        exc_info=True
                    )
                    return
                
                if duplicate_chunks > 0:
                    # Response had duplicates
                    session_metrics.responses_with_duplicates += 1
                    session_metrics.last_duplication_time = datetime.now()
                    
                    try:
                        logger.warning(
                            f"Response with duplicates recorded for session {session_id}",
                            extra={
                                "timestamp": datetime.now().isoformat(),
                                "session_id": session_id,
                                "total_chunks": total_chunks,
                                "duplicate_chunks": duplicate_chunks,
                                "duplication_rate_in_response": duplicate_chunks / total_chunks if total_chunks > 0 else 0.0,
                                "session_duplication_rate": session_metrics.get_duplication_rate()
                            }
                        )
                    except Exception as log_error:
                        # Fallback to basic logging
                        print(
                            f"Warning: Response with duplicates recorded for session {session_id}",
                            file=__import__('sys').stderr
                        )
                else:
                    # Clean response
                    session_metrics.last_clean_response_time = datetime.now()
                    
                    try:
                        logger.info(
                            f"Clean response recorded for session {session_id}",
                            extra={
                                "timestamp": datetime.now().isoformat(),
                                "session_id": session_id,
                                "total_chunks": total_chunks,
                                "session_duplication_rate": session_metrics.get_duplication_rate()
                            }
                        )
                    except Exception as log_error:
                        # Fallback to basic logging
                        pass  # Info logging failures are not critical
        except Exception as e:
            # Don't let metrics failures affect functionality
            logger.error(
                f"Failed to record response quality: {type(e).__name__}: {e}",
                exc_info=True
            )
    
    def log_resolution_confirmation(self, session_id: str) -> None:
        """Log confirmation that duplication is resolved.
        
        This method logs a confirmation message when a session that previously
        had duplicates produces a clean response.
        
        Args:
            session_id: Session identifier
        """
        try:
            with self._lock:
                try:
                    session_metrics = self._get_or_create_session_metrics(session_id)
                    
                    # Check if this session previously had duplicates
                    if session_metrics.total_duplicates_detected > 0:
                        try:
                            logger.info(
                                f"Duplication resolved for session {session_id}",
                                extra={
                                    "timestamp": datetime.now().isoformat(),
                                    "session_id": session_id,
                                    "previous_duplicates": session_metrics.total_duplicates_detected,
                                    "total_responses": session_metrics.total_responses,
                                    "session_duplication_rate": session_metrics.get_duplication_rate(),
                                    "last_clean_response": session_metrics.last_clean_response_time.isoformat() if session_metrics.last_clean_response_time else None
                                }
                            )
                        except Exception as log_error:
                            # Fallback to basic logging
                            print(
                                f"Info: Duplication resolved for session {session_id}",
                                file=__import__('sys').stderr
                            )
                except Exception as metrics_error:
                    # Log error but don't crash
                    logger.error(
                        f"Failed to check resolution status: {type(metrics_error).__name__}: {metrics_error}",
                        exc_info=True
                    )
        except Exception as e:
            # Don't let logging failures affect functionality
            logger.error(
                f"Failed to log resolution confirmation: {type(e).__name__}: {e}",
                exc_info=True
            )
    
    def get_duplication_rate(self, session_id: Optional[str] = None) -> float:
        """Get duplication rate for a session or globally.
        
        Args:
            session_id: Session identifier (None for global rate)
            
        Returns:
            Float between 0.0 and 1.0 representing the duplication rate
        """
        with self._lock:
            if session_id is None:
                # Return global rate
                if self._global_responses == 0:
                    return 0.0
                
                # Calculate based on responses with duplicates
                responses_with_dups = sum(
                    m.responses_with_duplicates
                    for m in self._session_metrics.values()
                )
                return responses_with_dups / self._global_responses
            else:
                # Return session-specific rate
                if session_id not in self._session_metrics:
                    return 0.0
                return self._session_metrics[session_id].get_duplication_rate()
    
    def get_session_metrics(self, session_id: str) -> Dict[str, Any]:
        """Get metrics for a specific session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with session metrics
        """
        with self._lock:
            if session_id not in self._session_metrics:
                return {
                    "session_id": session_id,
                    "total_responses": 0,
                    "responses_with_duplicates": 0,
                    "total_duplicates_detected": 0,
                    "duplication_rate": 0.0
                }
            return self._session_metrics[session_id].to_dict()
    
    def get_global_metrics(self) -> Dict[str, Any]:
        """Get global metrics across all sessions.
        
        Returns:
            Dictionary with global metrics
        """
        with self._lock:
            total_responses_with_dups = sum(
                m.responses_with_duplicates
                for m in self._session_metrics.values()
            )
            
            return {
                "total_sessions": len(self._session_metrics),
                "total_responses": self._global_responses,
                "responses_with_duplicates": total_responses_with_dups,
                "total_duplicates_detected": self._global_duplicates,
                "global_duplication_rate": self.get_duplication_rate(),
                "timestamp": datetime.now().isoformat()
            }
    
    def check_threshold_exceeded(
        self,
        session_id: str,
        threshold: float = 0.1
    ) -> bool:
        """Check if duplication rate exceeds threshold.
        
        This method checks if the duplication rate for a session exceeds
        a specified threshold and logs an alert if it does.
        
        Args:
            session_id: Session identifier
            threshold: Threshold rate (default: 0.1 = 10%)
            
        Returns:
            True if threshold is exceeded, False otherwise
        """
        try:
            rate = self.get_duplication_rate(session_id)
            
            if rate > threshold:
                try:
                    with self._lock:
                        session_metrics = self._get_or_create_session_metrics(session_id)
                        
                        try:
                            logger.error(
                                f"Duplication threshold exceeded for session {session_id}",
                                extra={
                                    "timestamp": datetime.now().isoformat(),
                                    "session_id": session_id,
                                    "duplication_rate": rate,
                                    "threshold": threshold,
                                    "total_duplicates": session_metrics.total_duplicates_detected,
                                    "total_responses": session_metrics.total_responses
                                }
                            )
                        except Exception as log_error:
                            # Fallback to basic logging
                            print(
                                f"Error: Duplication threshold exceeded for session {session_id}",
                                file=__import__('sys').stderr
                            )
                except Exception as metrics_error:
                    # Log error but still return True
                    logger.error(
                        f"Failed to log threshold exceeded: {type(metrics_error).__name__}: {metrics_error}",
                        exc_info=True
                    )
                return True
            
            return False
            
        except Exception as e:
            # If threshold check fails, log error and return False
            # (graceful degradation - don't trigger false alerts)
            logger.error(
                f"Failed to check threshold: {type(e).__name__}: {e}",
                exc_info=True
            )
            return False
    
    def reset_session_metrics(self, session_id: str) -> None:
        """Reset metrics for a specific session.
        
        Args:
            session_id: Session identifier
        """
        with self._lock:
            if session_id in self._session_metrics:
                old_metrics = self._session_metrics[session_id]
                
                # Update global counters
                self._global_duplicates -= old_metrics.total_duplicates_detected
                self._global_responses -= old_metrics.total_responses
                
                # Remove session metrics
                del self._session_metrics[session_id]
                
                logger.info(
                    f"Reset metrics for session {session_id}",
                    extra={
                        "timestamp": datetime.now().isoformat(),
                        "session_id": session_id
                    }
                )
    
    def reset_all_metrics(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._session_metrics.clear()
            self._global_duplicates = 0
            self._global_responses = 0
            
            logger.info(
                "All metrics reset",
                extra={
                    "timestamp": datetime.now().isoformat()
                }
            )


# Global singleton instance
_metrics_instance: Optional[DuplicationMetrics] = None
_metrics_lock = Lock()


def get_metrics_instance() -> DuplicationMetrics:
    """Get the global DuplicationMetrics singleton instance.
    
    Returns:
        DuplicationMetrics singleton instance
    """
    global _metrics_instance
    
    if _metrics_instance is None:
        with _metrics_lock:
            if _metrics_instance is None:
                _metrics_instance = DuplicationMetrics()
    
    return _metrics_instance
