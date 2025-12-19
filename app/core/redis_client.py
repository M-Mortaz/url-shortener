"""Redis client wrapper for caching operations."""

from __future__ import annotations

import logging
from typing import Optional

from redis.asyncio import Redis, from_url

from app.core.settings import settings

__all__ = ["get_redis_client", "redis_client", "RedisCache"]

logger = logging.getLogger(__name__)

# Global Redis client instance
redis_client: Optional[Redis] = None


async def get_redis_client() -> Redis:
    """
    Get or create the global Redis client.
    
    Returns:
        Async Redis client instance
    """
    global redis_client
    
    if redis_client is None:
        redis_client = from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info("Redis client initialized")
    
    return redis_client


async def close_redis_client() -> None:
    """Close the Redis client connection."""
    global redis_client
    
    if redis_client:
        await redis_client.aclose()
        redis_client = None
        logger.info("Redis client closed")


class RedisCache:
    """Redis cache operations for URL shortener."""
    
    KEY_PREFIX = "short_url:"
    DEFAULT_TTL = 86400  # 24 hours in seconds
    
    def __init__(self, redis_client: Redis):
        """
        Initialize the cache.
        
        Args:
            redis_client: Async Redis client
        """
        self.redis = redis_client
    
    def _make_key(self, short_code: str) -> str:
        """Create Redis key for a short code."""
        return f"{self.KEY_PREFIX}{short_code}"
    
    async def get(self, short_code: str) -> Optional[str]:
        """
        Get original URL from cache.
        
        Args:
            short_code: Short code to look up
            
        Returns:
            Original URL if found, None otherwise
        """
        key = self._make_key(short_code)
        url = await self.redis.get(key)
        return url
    
    async def set(
        self,
        short_code: str,
        original_url: str,
        ttl: Optional[int] = None
    ) -> None:
        """
        Cache a short code to URL mapping.
        
        Args:
            short_code: Short code
            original_url: Original URL to cache
            ttl: Time to live in seconds (default: DEFAULT_TTL)
        """
        key = self._make_key(short_code)
        ttl = ttl or self.DEFAULT_TTL
        await self.redis.setex(key, ttl, original_url)
    
    async def delete(self, short_code: str) -> None:
        """
        Delete a cached short code.
        
        Args:
            short_code: Short code to delete
        """
        key = self._make_key(short_code)
        await self.redis.delete(key)
    
    async def exists(self, short_code: str) -> bool:
        """
        Check if a short code exists in cache.
        
        Args:
            short_code: Short code to check
            
        Returns:
            True if exists, False otherwise
        """
        key = self._make_key(short_code)
        return bool(await self.redis.exists(key))

