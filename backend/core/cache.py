"""
Redis Session Cache Manager

Provides fast session state persistence with automatic expiration.
"""
from __future__ import annotations

import json
from typing import Optional
import logging
from redis.asyncio import Redis
from backend.config.settings import settings


logger = logging.getLogger(__name__)


class RedisCache:
    """Async Redis client for session caching"""
    
    def __init__(self):
        self.redis: Optional[Redis] = None
        self.enabled = settings.REDIS_ENABLED
        self.ttl = settings.REDIS_TTL
        
    async def connect(self):
        """Initialize Redis connection"""
        if not self.enabled:
            logger.info("Redis caching disabled")
            return
            
        try:
            self.redis = Redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis.ping()
            
            # Mask credentials for logging
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(settings.REDIS_URL)
            if parsed.password:
                host = parsed.hostname or "localhost"
                port = f":{parsed.port}" if parsed.port else ""
                if parsed.username:
                    masked_netloc = f"{parsed.username}:***@{host}{port}"
                else:
                    masked_netloc = f"***@{host}{port}"
                masked = parsed._replace(netloc=masked_netloc)
                masked_url = urlunparse(masked)
            else:
                masked_url = settings.REDIS_URL
            
            logger.info("Redis connected: %s", masked_url)
        except Exception as e:
            logger.warning("Redis connection failed: %s", e)
            logger.warning("Falling back to database-only session storage")
            self.enabled = False
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """Retrieve session from cache"""
        if not self.enabled or not self.redis:
            return None
            
        try:
            data = await self.redis.get(f"session:{session_id}")
            if data:
                loaded = json.loads(data)
                if isinstance(loaded, dict):
                    return loaded
        except Exception as e:
            logger.error("Redis GET error for %s: %s", session_id, e)
        return None

    def _normalize_session_payload(self, session_id: str, session_data: dict) -> dict:
        """Ensure cached payload has a stable schema expected by websocket/routes."""
        return {
            "session_id": session_id,
            "user_id": session_data.get("user_id"),
            "persona": session_data.get("persona"),
            "difficulty": session_data.get("difficulty"),
            "topic": session_data.get("topic"),
            "job_description": session_data.get("job_description") or "",
            "resume_text": session_data.get("resume_text"),  # Fix: Persist resume through cache
            "history": session_data.get("history") or [],
            "analytics": session_data.get("analytics") or {},
        }
    
    async def set_session(self, session_id: str, session_data: dict):
        """Store session in cache with TTL"""
        if not self.enabled or not self.redis:
            return
            
        try:
            normalized = self._normalize_session_payload(session_id, session_data)
            await self.redis.setex(
                f"session:{session_id}",
                self.ttl,
                json.dumps(normalized, ensure_ascii=True, default=str)
            )
        except Exception as e:
            logger.error("Redis SET error for %s: %s", session_id, e)
    
    async def delete_session(self, session_id: str):
        """Remove session from cache"""
        if not self.enabled or not self.redis:
            return
            
        try:
            await self.redis.delete(f"session:{session_id}")
        except Exception as e:
            logger.error("Redis DELETE error for %s: %s", session_id, e)
    
    async def close(self):
        """Cleanup Redis connection"""
        if self.redis:
            await self.redis.close()

    async def is_connected(self) -> bool:
        """Return redis connectivity status without raising."""
        if not self.enabled or not self.redis:
            return False
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False


# Global cache instance
redis_cache = RedisCache()
