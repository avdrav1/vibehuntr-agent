# Implementation Plan

- [x] 1. Enhance DuplicateDetector with content-level detection
  - Add content similarity detection methods to `app/event_planning/duplicate_detector.py`
  - Implement sentence splitting using regex
  - Implement similarity calculation using SequenceMatcher
  - Add sentence window tracking (last 50 sentences)
  - _Requirements: 1.1, 3.1, 4.2, 4.3_

- [x] 1.1 Add sentence splitting method
  - Implement `_split_into_sentences()` using regex pattern `[.!?]+\s+`
  - Handle edge cases (empty text, no punctuation)
  - Add fallback to paragraph splitting on error
  - _Requirements: 4.2, 5.3_

- [x] 1.2 Add similarity detection method
  - Implement `_find_similar_sentence()` to compare against accumulated sentences
  - Use SequenceMatcher for similarity calculation
  - Only compare against last 50 sentences for performance
  - Return tuple of (similar_sentence, similarity_score) if found
  - _Requirements: 1.1, 3.2, 4.1_

- [x] 1.3 Add main content duplicate detection method
  - Implement `contains_duplicate_content()` as main entry point
  - Split new text into sentences
  - Check each sentence against accumulated sentences
  - Return (is_duplicate, duplicate_preview) tuple
  - _Requirements: 1.1, 1.2_

- [x] 1.4 Add content tracking method
  - Implement `add_content()` to track accumulated sentences
  - Maintain sliding window of last 50 sentences
  - _Requirements: 4.1_

- [x] 1.5 Add content similarity threshold parameter
  - Add `content_similarity_threshold` parameter to `__init__`
  - Default to 0.85
  - Use in similarity comparisons
  - _Requirements: 3.1, 3.2, 3.5_

- [x] 2. Add data models for content duplication events
  - Create `ContentDuplicationEvent` dataclass in `duplicate_detector.py`
  - Add fields: event_id, session_id, timestamp, duplicate_sentence, similar_sentence, similarity_score, position
  - Implement `to_dict()` method for logging
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 3. Integrate content-level detection into agent_invoker
  - Modify `invoke_agent_streaming()` in `app/event_planning/agent_invoker.py`
  - Add content-level duplicate check after hash-based check
  - Skip yielding if content duplicate detected
  - Add content to tracking if not duplicate
  - _Requirements: 1.2, 1.3_

- [x] 3.1 Add content duplicate detection call
  - Call `duplicate_detector.contains_duplicate_content()` on new chunks
  - Handle the returned (is_duplicate, preview) tuple
  - _Requirements: 1.1, 1.2_

- [x] 3.2 Add content duplicate filtering logic
  - Skip yielding chunk if content duplicate detected
  - Log warning with duplicate preview
  - Increment metrics counter
  - Continue to next chunk
  - _Requirements: 1.2, 1.3, 2.1_

- [x] 3.3 Add content tracking for non-duplicates
  - Call `duplicate_detector.add_content()` for non-duplicate chunks
  - Ensure content is tracked before yielding
  - _Requirements: 1.1_

- [x] 4. Add comprehensive error handling
  - Wrap content duplicate detection in try-except
  - Log errors and gracefully degrade
  - Ensure content is yielded even if detection fails
  - _Requirements: 4.5, 5.4_

- [x] 4.1 Add error handling for sentence splitting
  - Wrap `_split_into_sentences()` in try-except
  - Fall back to paragraph splitting on error
  - Log errors
  - _Requirements: 5.3, 5.4_

- [x] 4.2 Add error handling for similarity calculation
  - Wrap `_calculate_similarity()` in try-except
  - Return 0.0 (not similar) on error
  - Log errors
  - _Requirements: 5.4_

- [x] 4.3 Add error handling for main detection
  - Wrap `contains_duplicate_content()` call in try-except
  - Return (False, None) on error to allow content through
  - Log errors with full context
  - _Requirements: 4.5, 5.4_

- [x] 5. Add edge case handling
  - Handle empty/whitespace content
  - Handle very short chunks (< 10 chars)
  - Handle empty accumulated response
  - _Requirements: 5.1, 5.2, 5.5_

- [x] 5.1 Skip detection for empty/whitespace content
  - Check if new_text is empty or whitespace-only
  - Return (False, None) immediately
  - _Requirements: 5.1_

- [x] 5.2 Skip detection for very short chunks
  - Check if new_text length < 10 characters
  - Return (False, None) immediately
  - _Requirements: 5.2_

- [x] 5.3 Handle empty accumulated response
  - Check if accumulated_sentences is empty
  - Return (False, None) immediately for first chunk
  - _Requirements: 5.5_

- [x] 6. Add metrics tracking for content duplication
  - Add `increment_content_duplicate_detected()` to duplication_metrics.py
  - Track content-level duplicates separately from chunk-level
  - Include in response metadata
  - _Requirements: 2.4_

- [x] 7. Add logging for content duplication events
  - Log at WARNING level when content duplicate detected
  - Include duplicate preview, similarity score, position
  - Log at DEBUG level for similarity checks
  - Log at ERROR level for detection failures
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 8. Write unit tests for sentence splitting
  - Test normal sentences with periods
  - Test sentences with exclamation marks and question marks
  - Test text with no punctuation
  - Test empty text
  - Test text with only whitespace
  - _Requirements: 4.2, 5.1_

- [x] 9. Write unit tests for similarity calculation
  - Test identical sentences (should return 1.0)
  - Test completely different sentences (should return ~0.0)
  - Test similar sentences (should return 0.8-0.9)
  - Test with various sentence lengths
  - _Requirements: 3.2_

- [x] 10. Write unit tests for duplicate detection
  - Test with duplicate sentences (should detect)
  - Test with similar sentences above threshold (should detect)
  - Test with similar sentences below threshold (should not detect)
  - Test with completely different sentences (should not detect)
  - Test with empty accumulated response (should not detect)
  - _Requirements: 1.1, 3.2, 3.3, 3.4, 5.5_

- [x] 11. Write unit tests for edge cases
  - Test with empty new_text (should skip detection)
  - Test with whitespace-only new_text (should skip detection)
  - Test with very short new_text < 10 chars (should skip detection)
  - Test with empty accumulated_sentences (should skip detection)
  - _Requirements: 5.1, 5.2, 5.5_

- [x] 12. Write unit tests for error handling
  - Test sentence splitting with invalid regex
  - Test similarity calculation with None values
  - Test detection with exceptions in sub-methods
  - Verify graceful degradation in all cases
  - _Requirements: 4.5, 5.3, 5.4_

- [ ]* 13. Write property test for no duplicate paragraphs
  - **Property 1: No duplicate paragraphs in final response**
  - **Validates: Requirements 1.4**
  - Generate random multi-paragraph responses
  - Run through duplicate detection
  - Verify each paragraph appears at most once

- [ ]* 14. Write property test for similarity symmetry
  - **Property 2: Similarity detection is symmetric**
  - **Validates: Requirements 3.2**
  - Generate random sentence pairs
  - Calculate similarity(A, B) and similarity(B, A)
  - Verify they are equal

- [ ]* 15. Write property test for threshold enforcement
  - **Property 3: Threshold enforcement**
  - **Validates: Requirements 3.2, 3.3, 3.4**
  - Generate sentence pairs with known similarity
  - Test with various thresholds
  - Verify correct duplicate classification

- [ ]* 16. Write property test for performance bounds
  - **Property 4: Performance bounds**
  - **Validates: Requirements 4.4**
  - Generate chunks of various sizes
  - Measure detection time for each
  - Verify average time < 50ms

- [ ]* 17. Write property test for graceful degradation
  - **Property 5: Graceful degradation**
  - **Validates: Requirements 4.5, 5.4**
  - Inject errors into detection components
  - Verify content is still yielded
  - Verify errors are logged

- [ ]* 18. Write property test for empty content handling
  - **Property 6: Empty content handling**
  - **Validates: Requirements 5.1, 5.5**
  - Generate empty and whitespace-only chunks
  - Verify detection is skipped
  - Verify no errors occur

- [x] 19. Write integration test for South Philly duplicate
  - Reproduce exact conversation: "Italian food" → "$$$" → "South Philly Italian"
  - Verify no duplicate paragraphs in final response
  - Verify venue list appears only once
  - Verify "Okay, I found five Italian restaurants" appears only once
  - _Requirements: 1.4_

- [x] 20. Write integration test for content duplication metrics
  - Trigger content-level duplication
  - Verify metrics show the duplication
  - Verify logs contain ContentDuplicationEvent
  - Verify response metadata includes content duplicate count
  - _Requirements: 2.4_

- [x] 21. Update documentation
  - Document new content_similarity_threshold parameter
  - Document ContentDuplicationEvent structure
  - Add examples of content-level vs chunk-level duplication
  - Document performance characteristics
  - _Requirements: All_

- [x] 22. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
