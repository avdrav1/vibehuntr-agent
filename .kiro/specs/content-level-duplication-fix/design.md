# Design Document

## Overview

This design addresses content-level duplication in agent responses by adding sentence-level similarity detection to the existing duplicate detection system. The solution extends the `DuplicateDetector` class with methods to detect when new content is semantically similar to already-generated content, preventing the LLM from repeating the same information multiple times in a single response.

## Architecture

The content-level duplication detection integrates into the existing streaming pipeline in `agent_invoker.py`:

```
User Message → Agent → Events Stream → Duplicate Detection → Yield to User
                                            ↓
                                    [Chunk-Level Detection]
                                            ↓
                                    [Content-Level Detection] ← NEW
```

The new content-level detection layer sits after chunk-level detection and before yielding content to the user.

## Components and Interfaces

### 1. Enhanced DuplicateDetector

**Location**: `app/event_planning/duplicate_detector.py`

**New Methods**:

```python
class DuplicateDetector:
    def __init__(self, similarity_threshold: float = 0.95, content_similarity_threshold: float = 0.85):
        # Existing initialization
        self.content_similarity_threshold = content_similarity_threshold
        self.accumulated_sentences: List[str] = []
        self.sentence_window_size = 50  # Only compare against recent sentences
    
    def contains_duplicate_content(self, new_text: str) -> tuple[bool, Optional[str]]:
        """
        Check if new_text contains content similar to accumulated response.
        
        Returns:
            tuple: (is_duplicate, duplicate_sentence_preview)
        """
        pass
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex."""
        pass
    
    def _find_similar_sentence(self, sentence: str) -> Optional[tuple[str, float]]:
        """
        Find if sentence is similar to any accumulated sentence.
        
        Returns:
            Optional tuple of (similar_sentence, similarity_score)
        """
        pass
    
    def add_content(self, text: str) -> None:
        """Add text to accumulated content tracking."""
        pass
```

### 2. Integration in agent_invoker.py

**Location**: `app/event_planning/agent_invoker.py`

**Modified Section**: The event processing loop where chunks are yielded

```python
# After hash-based duplicate detection
if chunk_hash not in yielded_chunk_hashes:
    # NEW: Content-level duplicate detection
    is_content_dup, dup_preview = duplicate_detector.contains_duplicate_content(new_content)
    
    if is_content_dup:
        logger.warning(
            f"Content-level duplicate detected: {dup_preview}",
            extra={
                "session_id": session_id,
                "duplicate_preview": dup_preview
            }
        )
        # Skip this content
        if metrics:
            metrics.increment_content_duplicate_detected(session_id)
        continue
    
    # Not a duplicate - yield it
    yielded_chunk_hashes.add(chunk_hash)
    duplicate_detector.add_content(new_content)
    accumulated_response = part.text
    yield {'type': 'text', 'content': new_content}
```

## Data Models

### SentenceSimilarity

```python
@dataclass
class SentenceSimilarity:
    """Result of sentence similarity comparison."""
    sentence1: str
    sentence2: str
    similarity_score: float
    is_duplicate: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sentence1_preview": self.sentence1[:100],
            "sentence2_preview": self.sentence2[:100],
            "similarity_score": self.similarity_score,
            "is_duplicate": self.is_duplicate
        }
```

### ContentDuplicationEvent

```python
@dataclass
class ContentDuplicationEvent:
    """Event logged when content-level duplication is detected."""
    event_id: str
    session_id: str
    timestamp: datetime
    duplicate_sentence: str
    similar_sentence: str
    similarity_score: float
    position_in_response: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "duplicate_sentence_preview": self.duplicate_sentence[:100],
            "similar_sentence_preview": self.similar_sentence[:100],
            "similarity_score": self.similarity_score,
            "position_in_response": self.position_in_response
        }
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: No duplicate paragraphs in final response

*For any* agent response, no paragraph should appear more than once in the final accumulated text
**Validates: Requirements 1.4**

### Property 2: Similarity detection is symmetric

*For any* two sentences A and B, similarity(A, B) should equal similarity(B, A)
**Validates: Requirements 3.2**

### Property 3: Threshold enforcement

*For any* two sentences with similarity score S and threshold T, they should be marked as duplicates if and only if S >= T
**Validates: Requirements 3.2, 3.3, 3.4**

### Property 4: Performance bounds

*For any* chunk of text, content-level duplicate detection should complete in less than 50ms on average
**Validates: Requirements 4.4**

### Property 5: Graceful degradation

*For any* error during duplicate detection, the system should log the error and yield the content rather than crash
**Validates: Requirements 4.5, 5.4**

### Property 6: Empty content handling

*For any* chunk that is empty or whitespace-only, duplicate detection should be skipped
**Validates: Requirements 5.1, 5.5**

## Error Handling

### Detection Errors

```python
try:
    is_dup, preview = duplicate_detector.contains_duplicate_content(new_content)
except Exception as e:
    logger.error(
        f"Content duplicate detection failed: {e}",
        exc_info=True
    )
    # Graceful degradation - allow content through
    is_dup = False
    preview = None
```

### Sentence Splitting Errors

```python
def _split_into_sentences(self, text: str) -> List[str]:
    try:
        # Try regex-based splitting
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    except Exception as e:
        logger.error(f"Sentence splitting failed: {e}")
        # Fall back to paragraph splitting
        return text.split('\n\n')
```

### Similarity Calculation Errors

```python
def _calculate_similarity(self, text1: str, text2: str) -> float:
    try:
        matcher = SequenceMatcher(None, text1, text2)
        return matcher.ratio()
    except Exception as e:
        logger.error(f"Similarity calculation failed: {e}")
        return 0.0  # Assume not similar on error
```

## Testing Strategy

### Unit Tests

1. **test_sentence_splitting**: Verify sentences are correctly split from text
2. **test_similarity_calculation**: Verify similarity scores are calculated correctly
3. **test_duplicate_detection_threshold**: Verify threshold enforcement
4. **test_empty_content_handling**: Verify empty/whitespace content is handled
5. **test_error_handling**: Verify graceful degradation on errors

### Property-Based Tests

1. **Property 1 Test**: Generate random responses and verify no duplicate paragraphs
   - Generate random multi-paragraph text
   - Run through duplicate detection
   - Verify each paragraph appears at most once

2. **Property 2 Test**: Verify similarity is symmetric
   - Generate pairs of random sentences
   - Calculate similarity(A, B) and similarity(B, A)
   - Verify they are equal

3. **Property 3 Test**: Verify threshold enforcement
   - Generate sentence pairs with known similarity scores
   - Test with various thresholds
   - Verify correct duplicate classification

4. **Property 4 Test**: Verify performance bounds
   - Generate chunks of various sizes
   - Measure detection time for each
   - Verify average time < 50ms

5. **Property 5 Test**: Verify graceful degradation
   - Inject errors into detection components
   - Verify content is still yielded
   - Verify errors are logged

6. **Property 6 Test**: Verify empty content handling
   - Generate empty and whitespace-only chunks
   - Verify detection is skipped
   - Verify no errors occur

### Integration Tests

1. **test_south_philly_duplicate**: Reproduce the exact conversation that triggered the bug
   - Send "Italian food" → "$$$" → "South Philly Italian"
   - Verify no duplicate paragraphs in final response
   - Verify venue list appears only once

2. **test_content_duplication_metrics**: Verify metrics are tracked correctly
   - Trigger content-level duplication
   - Verify metrics show the duplication
   - Verify logs contain duplication events

## Implementation Notes

### Sentence Splitting Strategy

Use regex-based splitting for performance:

```python
# Split on sentence-ending punctuation followed by whitespace
sentences = re.split(r'[.!?]+\s+', text)
```

This is faster than NLP-based parsing and sufficient for duplicate detection.

### Similarity Window

Only compare against the last 50 sentences to maintain performance:

```python
recent_sentences = self.accumulated_sentences[-50:]
```

This prevents O(n²) growth as responses get longer.

### Threshold Tuning

Default threshold of 0.85 balances false positives and false negatives:
- 1.0: Only exact matches (too strict, misses paraphrases)
- 0.9: Very similar sentences (good for catching near-duplicates)
- 0.85: Similar sentences (recommended default)
- 0.8: Somewhat similar (may catch legitimate variations)

### Logging Strategy

Log at different levels:
- **DEBUG**: Every similarity check
- **INFO**: Content added to tracking
- **WARNING**: Duplicate content detected and filtered
- **ERROR**: Detection failures

## Deployment Considerations

### Backward Compatibility

The new content-level detection is additive and doesn't change existing APIs. It integrates seamlessly into the current streaming pipeline.

### Performance Impact

Expected performance impact:
- Per-chunk overhead: ~10-30ms (well under 50ms requirement)
- Memory overhead: ~50KB per response (storing recent sentences)
- No impact on non-duplicate responses

### Monitoring

Add metrics to track:
- `content_duplicates_detected`: Count of content-level duplicates filtered
- `content_detection_latency`: Time spent in content duplicate detection
- `content_detection_errors`: Count of detection errors

### Rollback Plan

If issues arise:
1. Set `content_similarity_threshold` to 1.0 (only exact matches)
2. Or disable by catching all exceptions and allowing content through
3. Or revert the changes to `agent_invoker.py`
