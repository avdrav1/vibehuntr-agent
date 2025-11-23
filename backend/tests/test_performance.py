"""
Performance tests for the FastAPI backend.

Tests long conversations, rapid message sending, and memory usage.
Requirements: 7.5
"""

import asyncio
import time
import tracemalloc
from typing import List
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture
def mock_agent_service():
    """Mock the agent service for performance testing."""
    with patch('backend.app.api.chat.get_agent_service') as mock:
        service = MagicMock()
        
        # Mock invoke_agent_async to return a simple response quickly
        async def mock_invoke(*args, **kwargs):
            return "Performance test response"
        service.invoke_agent_async = mock_invoke
        
        mock.return_value = service
        yield service


class TestPerformance:
    """Performance tests for backend API."""

    @pytest.fixture
    def client(self, mock_agent_service):
        """Create test client with mocked agent."""
        return TestClient(app)

    def test_long_conversation_performance(self, client):
        """
        Test performance with a long conversation (100+ messages).
        
        Validates: Requirements 7.5 - System handles long conversations efficiently
        """
        # Create session
        response = client.post("/api/sessions")
        assert response.status_code == 201
        session_id = response.json()["session_id"]

        # Track timing for 100 messages
        start_time = time.time()
        message_times = []

        for i in range(100):
            msg_start = time.time()
            
            # Send message
            response = client.post(
                "/api/chat",
                json={
                    "session_id": session_id,
                    "message": f"Test message {i}"
                }
            )
            
            msg_end = time.time()
            message_times.append(msg_end - msg_start)
            
            assert response.status_code == 200

        end_time = time.time()
        total_time = end_time - start_time
        avg_time = sum(message_times) / len(message_times)

        # Verify messages are stored
        response = client.get(f"/api/sessions/{session_id}/messages")
        assert response.status_code == 200
        messages = response.json()["messages"]
        
        # Should have 100 user messages + 100 assistant responses
        assert len(messages) == 200

        # Performance assertions
        # Average response time should be reasonable (< 5 seconds per message)
        assert avg_time < 5.0, f"Average response time too high: {avg_time}s"
        
        # Total time should be reasonable (< 10 minutes for 100 messages)
        assert total_time < 600, f"Total time too high: {total_time}s"

        print(f"\nLong conversation performance:")
        print(f"  Total messages: 200 (100 exchanges)")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Average time per message: {avg_time:.2f}s")

    def test_rapid_message_sending(self, client):
        """
        Test rapid message sending without delays.
        
        Validates: Requirements 7.5 - System handles rapid requests
        """
        # Create session
        response = client.post("/api/sessions")
        assert response.status_code == 201
        session_id = response.json()["session_id"]

        # Send 20 messages as fast as possible
        start_time = time.time()
        
        for i in range(20):
            response = client.post(
                "/api/chat",
                json={
                    "session_id": session_id,
                    "message": f"Rapid message {i}"
                }
            )
            assert response.status_code == 200

        end_time = time.time()
        total_time = end_time - start_time

        # Verify all messages are stored
        response = client.get(f"/api/sessions/{session_id}/messages")
        assert response.status_code == 200
        messages = response.json()["messages"]
        
        # Should have 20 user messages + 20 assistant responses
        assert len(messages) == 40

        print(f"\nRapid message sending performance:")
        print(f"  Messages sent: 20")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Messages per second: {20/total_time:.2f}")

    def test_memory_usage_long_conversation(self, client):
        """
        Test memory usage during long conversation.
        
        Validates: Requirements 7.5 - No memory leaks
        """
        # Start memory tracking
        tracemalloc.start()
        
        # Create session
        response = client.post("/api/sessions")
        assert response.status_code == 201
        session_id = response.json()["session_id"]

        # Get baseline memory
        baseline_snapshot = tracemalloc.take_snapshot()
        baseline_memory = sum(stat.size for stat in baseline_snapshot.statistics('lineno'))

        # Send 50 messages
        for i in range(50):
            response = client.post(
                "/api/chat",
                json={
                    "session_id": session_id,
                    "message": f"Memory test message {i}"
                }
            )
            assert response.status_code == 200

        # Get memory after messages
        after_snapshot = tracemalloc.take_snapshot()
        after_memory = sum(stat.size for stat in after_snapshot.statistics('lineno'))

        # Clear session
        response = client.delete(f"/api/sessions/{session_id}")
        assert response.status_code == 204

        # Get memory after clearing
        cleared_snapshot = tracemalloc.take_snapshot()
        cleared_memory = sum(stat.size for stat in cleared_snapshot.statistics('lineno'))

        tracemalloc.stop()

        # Calculate memory growth
        memory_growth = after_memory - baseline_memory
        memory_after_clear = cleared_memory - baseline_memory

        print(f"\nMemory usage analysis:")
        print(f"  Baseline: {baseline_memory / 1024 / 1024:.2f} MB")
        print(f"  After 50 messages: {after_memory / 1024 / 1024:.2f} MB")
        print(f"  After clearing: {cleared_memory / 1024 / 1024:.2f} MB")
        print(f"  Growth: {memory_growth / 1024 / 1024:.2f} MB")
        print(f"  Remaining after clear: {memory_after_clear / 1024 / 1024:.2f} MB")

        # Memory should be released after clearing session
        # Allow some overhead - Python's GC doesn't immediately free all memory
        # We just want to ensure memory doesn't grow unbounded
        assert memory_after_clear < memory_growth * 0.9, "Memory not properly released after clearing session"

    def test_concurrent_sessions_performance(self, client):
        """
        Test performance with multiple concurrent sessions.
        
        Validates: Requirements 7.5 - System handles multiple sessions
        """
        # Create 10 sessions
        session_ids = []
        for _ in range(10):
            response = client.post("/api/sessions")
            assert response.status_code == 201
            session_ids.append(response.json()["session_id"])

        # Send messages to all sessions
        start_time = time.time()
        
        for session_id in session_ids:
            for i in range(10):
                response = client.post(
                    "/api/chat",
                    json={
                        "session_id": session_id,
                        "message": f"Concurrent test {i}"
                    }
                )
                assert response.status_code == 200

        end_time = time.time()
        total_time = end_time - start_time

        # Verify all sessions have correct message counts
        for session_id in session_ids:
            response = client.get(f"/api/sessions/{session_id}/messages")
            assert response.status_code == 200
            messages = response.json()["messages"]
            assert len(messages) == 20  # 10 user + 10 assistant

        print(f"\nConcurrent sessions performance:")
        print(f"  Sessions: 10")
        print(f"  Messages per session: 10")
        print(f"  Total messages: 100")
        print(f"  Total time: {total_time:.2f}s")

    def test_session_cleanup_performance(self, client):
        """
        Test performance of session cleanup operations.
        
        Validates: Requirements 7.5 - Efficient cleanup
        """
        # Create 20 sessions with messages
        session_ids = []
        
        for _ in range(20):
            response = client.post("/api/sessions")
            assert response.status_code == 201
            session_id = response.json()["session_id"]
            session_ids.append(session_id)
            
            # Add 10 messages to each
            for i in range(10):
                client.post(
                    "/api/chat",
                    json={
                        "session_id": session_id,
                        "message": f"Cleanup test {i}"
                    }
                )

        # Time cleanup operations
        start_time = time.time()
        
        for session_id in session_ids:
            response = client.delete(f"/api/sessions/{session_id}")
            assert response.status_code == 204

        end_time = time.time()
        cleanup_time = end_time - start_time

        # Verify sessions are cleared
        for session_id in session_ids:
            response = client.get(f"/api/sessions/{session_id}/messages")
            assert response.status_code == 200
            messages = response.json()["messages"]
            assert len(messages) == 0

        print(f"\nSession cleanup performance:")
        print(f"  Sessions cleaned: 20")
        print(f"  Total cleanup time: {cleanup_time:.2f}s")
        print(f"  Average per session: {cleanup_time/20:.3f}s")

        # Cleanup should be fast (< 1 second total for 20 sessions)
        assert cleanup_time < 1.0, f"Cleanup too slow: {cleanup_time}s"
