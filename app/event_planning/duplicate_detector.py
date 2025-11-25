"""Duplicate detection module for response streaming.

This module provides enhanced duplicate detection with multiple strategies
to identify and prevent duplicate content in agent responses.
"""

import logging
from typing import Set, List, Optional, Dict, Any
from difflib import SequenceMatcher
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class DuplicationSource(Enum):
    """Enumeration of possible duplication sources in the pipeline."""
    AGENT = "agent"  # Duplication at the agent/LLM level
    RUNNER = "runner"  # Duplication at the ADK Runner level
    STREAMING = "streaming"  # Duplication at the streaming/yielding level
    UNKNOWN = "unknown"  # Source could not be determined


class PipelineStage(Enum):
    """Enumeration of pipeline stages where duplication can be detected."""
    AGENT_GENERATION = "agent_generation"  # During agent response generation
    EVENT_PROCESSING = "event_processing"  # During ADK event processing
    TOKEN_YIELDING = "token_yielding"  # During token yielding to client
    SESSION_STORAGE = "session_storage"  # During session history storage


class PatternDetector:
    """Detects repeated patterns in sequences of chunks."""
    
    def __init__(self, window_size: int = 5):
        """
        Initialize pattern detector.
        
        Args:
            window_size: Number of recent chunks to analyze for patterns
        """
        self.window_size = window_size
        self.recent_chunks: List[str] = []
    
    def add_chunk(self, chunk: str) -> None:
        """Add a chunk to the pattern detection window."""
        self.recent_chunks.append(chunk)
        # Keep only the most recent chunks
        if len(self.recent_chunks) > self.window_size * 2:
            self.recent_chunks = self.recent_chunks[-self.window_size * 2:]
    
    def detect_pattern(self, chunk: str) -> bool:
        """
        Detect if the chunk is part of a repeated pattern.
        
        Returns:
            True if a repeated pattern is detected, False otherwise
        """
        if len(self.recent_chunks) < 2:
            return False
        
        # Check if this chunk matches any recent chunk exactly
        # (this catches simple repetitions like "A B C A B C")
        chunk_count = self.recent_chunks.count(chunk)
        if chunk_count > 0:
            # If we've seen this exact chunk recently, it might be a pattern
            # But we need to be careful not to flag legitimate repeated words
            # Only flag if we see it multiple times in a short window
            recent_window = self.recent_chunks[-self.window_size:]
            if recent_window.count(chunk) > 1:
                return True
        
        return False


class DuplicateDetector:
    """Enhanced duplicate detection with multiple strategies."""
    
    def __init__(self, similarity_threshold: float = 0.95):
        """
        Initialize duplicate detector.
        
        Args:
            similarity_threshold: Threshold for content similarity (0.0 to 1.0)
                                Higher values mean stricter matching
        """
        self.accumulated_text = ""
        self.seen_chunks: Set[int] = set()
        self.chunk_sequence: List[str] = []
        self.pattern_detector = PatternDetector()
        self.similarity_threshold = similarity_threshold
        
        # Duplication source tracking
        self.duplication_events: List[Dict[str, Any]] = []
        self.current_stage: Optional[PipelineStage] = None
        
        logger.debug(
            f"Initialized DuplicateDetector with similarity_threshold={similarity_threshold}"
        )
    
    def is_duplicate(self, chunk: str, stage: Optional[PipelineStage] = None) -> bool:
        """
        Check if chunk is a duplicate using multiple strategies.
        
        Strategies:
        1. Exact hash matching (current approach)
        2. Sequence pattern detection (detect repeated sequences)
        3. Content similarity (detect near-duplicates)
        
        Args:
            chunk: The text chunk to check
            stage: The pipeline stage where this check is happening
            
        Returns:
            True if the chunk is a duplicate, False if it's unique
        """
        try:
            if not chunk:
                # Empty chunks are not duplicates
                return False
            
            # Update current stage if provided
            if stage:
                self.current_stage = stage
            
            detection_method = None
            is_dup = False
            
            # Strategy 1: Exact hash matching
            try:
                chunk_hash = hash(chunk)
                if chunk_hash in self.seen_chunks:
                    logger.debug(f"Duplicate detected via exact hash matching: {chunk[:50]}...")
                    detection_method = "hash"
                    is_dup = True
            except Exception as hash_error:
                # Log error but continue with other strategies
                logger.error(
                    f"Hash matching failed: {type(hash_error).__name__}: {hash_error}",
                    exc_info=True
                )
            
            # Strategy 2: Sequence pattern detection
            if not is_dup:
                try:
                    if self.pattern_detector.detect_pattern(chunk):
                        logger.debug(f"Duplicate detected via pattern detection: {chunk[:50]}...")
                        detection_method = "pattern"
                        is_dup = True
                except Exception as pattern_error:
                    # Log error but continue with other strategies
                    logger.error(
                        f"Pattern detection failed: {type(pattern_error).__name__}: {pattern_error}",
                        exc_info=True
                    )
            
            # Strategy 3: Content similarity for near-duplicates
            # Check if this chunk is very similar to any recent chunk
            if not is_dup:
                try:
                    if self._is_similar_to_recent(chunk):
                        logger.debug(f"Duplicate detected via similarity matching: {chunk[:50]}...")
                        detection_method = "similarity"
                        is_dup = True
                except Exception as similarity_error:
                    # Log error but continue
                    logger.error(
                        f"Similarity detection failed: {type(similarity_error).__name__}: {similarity_error}",
                        exc_info=True
                    )
            
            # If duplicate detected, log the duplication event with source tracking
            if is_dup:
                try:
                    self._log_duplication_event(chunk, detection_method, stage)
                except Exception as log_error:
                    # Don't let logging failures affect duplicate detection
                    logger.error(
                        f"Failed to log duplication event: {type(log_error).__name__}: {log_error}",
                        exc_info=True
                    )
            
            return is_dup
            
        except Exception as e:
            # If duplicate detection fails completely, log error and return False
            # (graceful degradation - better to show potential duplicate than crash)
            logger.error(
                f"Duplicate detection failed: {type(e).__name__}: {e}",
                exc_info=True
            )
            return False
    
    def _is_similar_to_recent(self, chunk: str, window_size: int = 10) -> bool:
        """
        Check if chunk is similar to any recent chunk.
        
        Args:
            chunk: The chunk to check
            window_size: Number of recent chunks to compare against
            
        Returns:
            True if chunk is similar to a recent chunk, False otherwise
        """
        if len(self.chunk_sequence) == 0:
            return False
        
        # Only check the most recent chunks for efficiency
        recent_chunks = self.chunk_sequence[-window_size:]
        
        for recent_chunk in recent_chunks:
            similarity = self._calculate_similarity(chunk, recent_chunk)
            if similarity >= self.similarity_threshold:
                logger.debug(
                    f"High similarity ({similarity:.2f}) detected between chunks"
                )
                return True
        
        return False
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity ratio between two text strings.
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            Similarity ratio between 0.0 and 1.0
        """
        if not text1 or not text2:
            return 0.0
        
        # Use SequenceMatcher for similarity calculation
        matcher = SequenceMatcher(None, text1, text2)
        return matcher.ratio()
    
    def add_chunk(self, chunk: str) -> None:
        """
        Add chunk to tracking after confirming it's not a duplicate.
        
        Args:
            chunk: The chunk to add
        """
        try:
            if not chunk:
                return
            
            chunk_hash = hash(chunk)
            self.seen_chunks.add(chunk_hash)
            self.chunk_sequence.append(chunk)
            self.pattern_detector.add_chunk(chunk)
            
            logger.debug(f"Added chunk to tracking: {len(chunk)} chars")
        except Exception as e:
            # Log error but don't crash - graceful degradation
            logger.error(
                f"Failed to add chunk to tracking: {type(e).__name__}: {e}",
                exc_info=True
            )
    
    def update_accumulated_text(self, text: str) -> None:
        """
        Update the accumulated text.
        
        Args:
            text: The new accumulated text
        """
        self.accumulated_text = text
    
    def get_accumulated_text(self) -> str:
        """Get the current accumulated text."""
        return self.accumulated_text
    
    def get_stats(self) -> dict:
        """
        Get statistics about duplicate detection.
        
        Returns:
            Dictionary with detection statistics
        """
        return {
            "total_chunks_tracked": len(self.chunk_sequence),
            "unique_hashes": len(self.seen_chunks),
            "accumulated_text_length": len(self.accumulated_text),
            "similarity_threshold": self.similarity_threshold,
            "duplication_events": len(self.duplication_events)
        }
    
    def _log_duplication_event(
        self,
        chunk: str,
        detection_method: str,
        stage: Optional[PipelineStage]
    ) -> None:
        """
        Log a duplication event with source tracking information.
        
        Args:
            chunk: The duplicate chunk
            detection_method: Method used to detect duplication (hash/pattern/similarity)
            stage: Pipeline stage where duplication was detected
        """
        try:
            # Determine duplication source based on the stage
            source = self._determine_duplication_source(stage)
            
            event = {
                "timestamp": datetime.now().isoformat(),
                "chunk_preview": chunk[:100] if chunk else "",
                "chunk_length": len(chunk),
                "detection_method": detection_method,
                "pipeline_stage": stage.value if stage else "unknown",
                "duplication_source": source.value,
                "chunk_index": len(self.chunk_sequence)
            }
            
            self.duplication_events.append(event)
            
            # Log the exact stage where duplication occurred
            try:
                logger.warning(
                    f"Duplication detected at {stage.value if stage else 'unknown'} stage",
                    extra={
                        "duplication_source": source.value,
                        "pipeline_stage": stage.value if stage else "unknown",
                        "detection_method": detection_method,
                        "chunk_preview": chunk[:100] if chunk else "",
                        "chunk_length": len(chunk),
                        "timestamp": event["timestamp"]
                    }
                )
            except Exception as log_error:
                # Fallback to basic logging if structured logging fails
                print(
                    f"Warning: Duplication detected at {stage.value if stage else 'unknown'} stage",
                    file=__import__('sys').stderr
                )
        except Exception as e:
            # Don't let logging failures affect functionality
            logger.error(
                f"Failed to log duplication event: {type(e).__name__}: {e}",
                exc_info=True
            )
    
    def _determine_duplication_source(
        self,
        stage: Optional[PipelineStage]
    ) -> DuplicationSource:
        """
        Determine the source of duplication based on the pipeline stage.
        
        Args:
            stage: The pipeline stage where duplication was detected
            
        Returns:
            DuplicationSource enum indicating where duplication originated
        """
        if not stage:
            return DuplicationSource.UNKNOWN
        
        # Map pipeline stages to duplication sources
        stage_to_source = {
            PipelineStage.AGENT_GENERATION: DuplicationSource.AGENT,
            PipelineStage.EVENT_PROCESSING: DuplicationSource.RUNNER,
            PipelineStage.TOKEN_YIELDING: DuplicationSource.STREAMING,
            PipelineStage.SESSION_STORAGE: DuplicationSource.STREAMING
        }
        
        return stage_to_source.get(stage, DuplicationSource.UNKNOWN)
    
    def set_pipeline_stage(self, stage: PipelineStage) -> None:
        """
        Set the current pipeline stage for tracking.
        
        Args:
            stage: The current pipeline stage
        """
        self.current_stage = stage
        logger.debug(f"Pipeline stage set to: {stage.value}")
    
    def get_duplication_events(self) -> List[Dict[str, Any]]:
        """
        Get all duplication events that have been logged.
        
        Returns:
            List of duplication event dictionaries
        """
        return self.duplication_events
    
    def get_duplication_summary(self) -> Dict[str, Any]:
        """
        Get a summary of duplication events by source and stage.
        
        Returns:
            Dictionary with duplication summary statistics
        """
        if not self.duplication_events:
            return {
                "total_duplications": 0,
                "by_source": {},
                "by_stage": {},
                "by_method": {}
            }
        
        # Count by source
        by_source: Dict[str, int] = {}
        for event in self.duplication_events:
            source = event["duplication_source"]
            by_source[source] = by_source.get(source, 0) + 1
        
        # Count by stage
        by_stage: Dict[str, int] = {}
        for event in self.duplication_events:
            stage = event["pipeline_stage"]
            by_stage[stage] = by_stage.get(stage, 0) + 1
        
        # Count by detection method
        by_method: Dict[str, int] = {}
        for event in self.duplication_events:
            method = event["detection_method"]
            by_method[method] = by_method.get(method, 0) + 1
        
        return {
            "total_duplications": len(self.duplication_events),
            "by_source": by_source,
            "by_stage": by_stage,
            "by_method": by_method
        }
