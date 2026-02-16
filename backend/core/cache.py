"""
Redis Session Cache Manager

Provides fast session state persistence with automatic expiration.
"""
import json
from typing import Optional
from redis.asyncio import Redis
from backend.config.settings import settings


class RedisCache:
    """Async Redis client for session caching"""
    
    def __init__(self):
        self.redis: Optional[Redis] = None
        self.enabled = settings.REDIS_ENABLED
        self.ttl = settings.REDIS_TTL
        
    async def connect(self):
        """Initialize Redis connection"""
        if not self.enabled:
            print("ℹ️ Redis caching disabled")
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
                # Replace password with asterisks
                masked_netloc = f"{parsed.username}:***@{parsed.hostname}:{parsed.port}"
                masked = parsed._replace(netloc=masked_netloc)
                masked_url = urlunparse(masked)
            else:
                masked_url = settings.REDIS_URL
            
            print(f"✅ Redis connected: {masked_url}")
        except Exception as e:
            print(f"⚠️ Redis connection failed: {e}")
            print("   Falling back to database-only session storage")
            self.enabled = False
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """Retrieve session from cache"""
        if not self.enabled or not self.redis:
            return None
            
        try:
            data = await self.redis.get(f"session:{session_id}")
            if data:
                return json.loads(data)
        except Exception as e:
            print(f"Redis GET error: {e}")
        return None
    
    async def set_session(self, session_id: str, session_data: dict):
        """Store session in cache with TTL"""
        if not self.enabled or not self.redis:
            return
            
        try:
            await self.redis.setex(
                f"session:{session_id}",
                self.ttl,
                json.dumps(session_data)
            )
        except Exception as e:
            print(f"Redis SET error: {e}")
    
    async def delete_session(self, session_id: str):
        """Remove session from cache"""
        if not self.enabled or not self.redis:
            return
            
        try:
            await self.redis.delete(f"session:{session_id}")
        except Exception as e:
            print(f"Redis DELETE error: {e}")
    
    async def close(self):
        """Cleanup Redis connection"""
        if self.redis:
            await self.redis.close()


# Global cache instance
redis_cache = RedisCache()
