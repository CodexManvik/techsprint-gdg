"""
Setup script to create tests directory and files
"""
import os
from pathlib import Path

# Create tests directory
tests_dir = Path("C:/Project/interview-mirror/Interview-Mirror/tests")
tests_dir.mkdir(exist_ok=True)

print(f"Created directory: {tests_dir}")

# File contents
files = {
    "conftest.py": '''"""
Pytest Configuration and Fixtures

Provides shared fixtures for testing the Interview Mirror backend.
"""
import pytest
import asyncio
from typing import AsyncGenerator

try:
    from httpx import AsyncClient, ASGITransport
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    AsyncClient = None
    ASGITransport = None

from backend.main import create_app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if HTTPX_AVAILABLE:
    @pytest.fixture
    async def client() -> AsyncGenerator:
        """
        Async HTTP client for testing FastAPI endpoints.
        
        Uses httpx.AsyncClient with ASGITransport to avoid blocking the event loop.
        """
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as c:
            yield c


@pytest.fixture
def sample_landmarks():
    """Sample MediaPipe face landmarks for vision testing."""
    # Simplified landmark structure (468 points normally)
    landmarks = {}
    for i in range(478):  # 468 face + 10 iris
        landmarks[i] = {"x": 0.5, "y": 0.5, "z": 0.0}
    
    # Key landmarks for testing
    landmarks[1] = {"x": 0.5, "y": 0.5, "z": 0.0}  # Nose tip
    landmarks[33] = {"x": 0.3, "y": 0.4, "z": 0.0}  # Left eye inner
    landmarks[133] = {"x": 0.25, "y": 0.4, "z": 0.0}  # Left eye outer
    landmarks[468] = {"x": 0.275, "y": 0.4, "z": 0.0}  # Left iris
    landmarks[55] = {"x": 0.3, "y": 0.35, "z": 0.0}  # Left brow
    landmarks[285] = {"x": 0.7, "y": 0.35, "z": 0.0}  # Right brow
    landmarks[61] = {"x": 0.35, "y": 0.6, "z": 0.0}  # Mouth left
    landmarks[291] = {"x": 0.65, "y": 0.6, "z": 0.0}  # Mouth right
    landmarks[13] = {"x": 0.5, "y": 0.58, "z": 0.0}  # Upper lip
    landmarks[14] = {"x": 0.5, "y": 0.62, "z": 0.0}  # Lower lip
    landmarks[10] = {"x": 0.5, "y": 0.2, "z": 0.0}  # Forehead
    landmarks[152] = {"x": 0.5, "y": 0.8, "z": 0.0}  # Chin
    landmarks[263] = {"x": 0.7, "y": 0.4, "z": 0.0}  # Right eye inner
    
    return landmarks


@pytest.fixture
def sample_session_data():
    """Sample session data for testing."""
    return {
        "session_id": "test-session-123",
        "user_id": "test-user-456",
        "difficulty": "medium",
        "topic": "System Design",
        "job_description": "Senior Backend Engineer",
        "resume_text": "Experienced Python developer with 5 years in distributed systems."
    }
''',
    "test_session_analytics.py": '''"""
Tests for session analytics and None handling

Critical test: Ensures analytics don't crash on None values in metrics.
"""
import pytest
from engine.session_manager import InterviewSession


def test_session_initialization():
    """Test InterviewSession initializes with empty history."""
    session = InterviewSession(
        session_id="test-123",
        difficulty="medium",
        topic="Python"
    )
    
    assert session.session_id == "test-123"
    assert session.difficulty == "medium"
    assert session.topic == "Python"
    assert len(session.history["wpm"]) == 0


def test_log_audio_metrics_handles_none():
    """Test logging audio metrics with None WPM doesn't crash."""
    session = InterviewSession("test-123", "medium", "Python")
    
    # Log metrics with None WPM
    session.log_audio_metrics(None, 30.0, 0.85)
    
    # Should store None without crashing
    assert len(session.history["wpm"]) == 1
    assert session.history["wpm"][0] is None


def test_get_stats_filters_none_values():
    """Test get_stats correctly filters None before averaging."""
    session = InterviewSession("test-123", "medium", "Python")
    
    # Log mix of valid and None WPM values
    session.log_audio_metrics(120, 10.0, 0.9)
    session.log_audio_metrics(None, 5.0, 0.5)  # No speech detected
    session.log_audio_metrics(95, 12.0, 0.85)
    session.log_audio_metrics(110, 11.0, 0.88)
    session.log_audio_metrics(None, 3.0, 0.3)  # No speech
    
    stats = session.get_stats()
    
    # Average should exclude None values: (120 + 95 + 110) / 3 = 108.33
    assert stats["avg_wpm"] is not None
    assert 100 < stats["avg_wpm"] < 115
    
    # Should not have NaN or None in result
    assert stats["avg_wpm"] != float('nan')
'''
}

# Write all files
for filename, content in files.items():
    filepath = tests_dir / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {filepath}")

print("\nTests directory setup complete!")
