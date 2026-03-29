"""
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
