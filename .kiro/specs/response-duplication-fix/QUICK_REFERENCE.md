# Response Duplication Prevention - Quick Reference

## Overview

Multi-layered defense system that prevents duplicate responses in the vibehuntr-agent chat interface.

**Status:** ✅ Production-ready, all tests passing

## Key Components

### 1. DuplicateDetector
**Location:** `app/event_planning/duplicate_detector.py`

**Purpose:** Detects duplicates using multiple strategies

**Usage:**
```python
from app.event_planning.duplicate_detector import DuplicateDetector, PipelineStage

detector = DuplicateDetector(similarity_threshold=0.95)
detector.set_pipeline_stage(PipelineStage.TOKEN_YIELDING)

if not detector.is_duplicate(chunk):
    detector.add_chunk(chunk)
    yield chunk
```

### 2. ResponseTracker
**Location:** `app/event_planning/response_tracker.py`

**Purpose:** Tracks response generation and metrics

**Usage:**
```python
from app.event_planning.response_tracker import ResponseTracker

tracker = ResponseTracker(session_id=session_id, user_id=user_id)

if tracker.track_chunk(chunk):  # Returns True if unique
    yield chunk

metrics = tracker.get_metrics()  # Get final metrics
```

### 3. DuplicationMetrics
**Location:** `app/event_planning/duplication_metrics.py`

**Purpose:** Production monitoring and alerting

**Usage:**
```python
from app.event_planning.duplication_metrics import DuplicationMetrics

metrics = DuplicationMetrics.get_instance()

# Record duplicate detection
metrics.increment_duplicate_detected(session_id)

# Record response quality
metrics.record_response_quality(session_id, total_chunks, duplicate_chunks)

# Check threshold
if metrics.check_threshold_exceeded(session_id, threshold=0.1):
    # Alert!
    pass
```

## Quick Checks

### Check if Duplication is Occurring

```bash
# Check logs for duplication warnings
gcloud logging read "resource.type=cloud_run_revision AND jsonPayload.message=~'duplicate'" --limit 50

# Should return no results in production
```

### Verify Clean Responses

```bash
# Check for clean response confirmations
gcloud logging read "resource.type=cloud_run_revision AND jsonPayload.message=~'Clean response'" --limit 10

# Should show regular confirmations
```

### Monitor Duplication Rate

```bash
# Get duplication summary
gcloud logging read "resource.type=cloud_run_revision AND jsonPayload.message='Duplication detected during response generation'" --limit 10

# Should return no results in production
```

## Configuration

### Adjust Similarity Threshold

```python
# More strict (catches more duplicates)
detector = DuplicateDetector(similarity_threshold=0.90)

# More lenient (catches fewer duplicates)
detector = DuplicateDetector(similarity_threshold=0.98)
```

### Adjust Alert Threshold

```python
# More sensitive (alert on any duplication)
metrics.check_threshold_exceeded(session_id, threshold=0.05)  # 5%

# Less sensitive (only alert on severe duplication)
metrics.check_threshold_exceeded(session_id, threshold=0.20)  # 20%
```

### Adjust Agent Configuration

```python
# More deterministic (less duplication)
root_agent = Agent(
    model="gemini-2.0-flash-exp",
    generation_config={
        "temperature": 0.7,      # Lower = more deterministic
        "top_p": 0.95,
        "top_k": 40,
    }
)
```

## Troubleshooting

### Issue: Duplication Still Occurring

**Quick Fix:**
```python
# Try stricter detection
detector = DuplicateDetector(similarity_threshold=0.90)

# Try lower temperature
generation_config={"temperature": 0.5}
```

### Issue: False Positives (Missing Content)

**Quick Fix:**
```python
# Try more lenient detection
detector = DuplicateDetector(similarity_threshold=0.98)

# Disable similarity detection
detector = DuplicateDetector(similarity_threshold=1.0)
```

### Issue: Performance Impact

**Quick Fix:**
```python
# Disable expensive strategies
detector = DuplicateDetector(
    enable_pattern_detection=False,
    enable_similarity_detection=False
)
```

## Testing

### Run All Tests

```bash
# Property-based tests
uv run pytest tests/property/test_properties_response_duplication.py -v

# Integration tests
uv run pytest tests/integration/test_no_message_duplication.py -v
uv run pytest tests/integration/test_duplication_prevention.py -v

# Unit tests
uv run pytest tests/unit/test_error_handling_components.py -v
```

### Manual Test

```bash
# Run manual test script
uv run python test_manual_duplication.py
```

## Monitoring Queries

### Cloud Logging

```bash
# All duplication-related logs
gcloud logging read "resource.type=cloud_run_revision AND jsonPayload.message=~'duplicate|duplication'" --limit 100

# Error logs
gcloud logging read "resource.type=cloud_run_revision AND severity=ERROR AND jsonPayload.message=~'duplicate'" --limit 50
```

### BigQuery

```sql
-- Duplication rate by session
SELECT 
  session_id,
  COUNT(*) as total_responses,
  SUM(CASE WHEN duplicate_chunks > 0 THEN 1 ELSE 0 END) as responses_with_duplicates,
  SAFE_DIVIDE(
    SUM(CASE WHEN duplicate_chunks > 0 THEN 1 ELSE 0 END),
    COUNT(*)
  ) * 100 as duplication_rate_percent
FROM `project.dataset.response_metrics`
GROUP BY session_id
ORDER BY duplication_rate_percent DESC
LIMIT 10
```

## Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Duplication Rate | 0% | > 10% |
| Response ID Uniqueness | 100% | < 100% |
| Clean Response Rate | 100% | < 90% |
| Detection Errors | 0 | > 5 per hour |

## Documentation Links

- **[Complete Documentation](README.md)** - Full documentation with all details
- **[Requirements](requirements.md)** - Detailed requirements and acceptance criteria
- **[Design](design.md)** - Architecture and design decisions
- **[Diagnostic Findings](DIAGNOSTIC_FINDINGS.md)** - Investigation results
- **[Fix Implementation](FIX_IMPLEMENTATION.md)** - Implementation details
- **[Error Handling](ERROR_HANDLING_SUMMARY.md)** - Error handling documentation

## Support

For issues or questions:
1. Check [README.md](README.md) troubleshooting section
2. Review logs using queries above
3. Run diagnostic tests
4. Check configuration settings

---

**Last Updated:** November 25, 2025  
**Version:** 1.0  
**Status:** ✅ Production-ready
