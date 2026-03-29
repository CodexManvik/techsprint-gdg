"""
Shared in-memory session state used by HTTP and WebSocket routes.

This avoids drift from multiple independent module-level dictionaries.
"""
import asyncio
from engine.session_manager import InterviewSession


# Legacy InterviewSession objects keyed by session_id.
legacy_sessions: dict[str, InterviewSession] = {}

# Number of active websocket connections per session.
active_connections: dict[str, int] = {}

# Guards concurrent mutations to shared in-memory dictionaries.
sessions_lock = asyncio.Lock()
