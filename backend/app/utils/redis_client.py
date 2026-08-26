"""
Redis client utilities for caching, rate limiting, and pub/sub.
"""

from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings
from app.utils.logging import get_logger

logger = get_logger("redis")

# Global async Redis client
_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Get or create the async Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    """Close the Redis connection."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


async def cache_get(key: str) -> str | None:
    """Get a value from cache."""
    client = await get_redis()
    try:
        return await client.get(key)
    except Exception as e:
        logger.warning(f"Redis cache get failed for key '{key}': {e}")
        return None


async def cache_set(key: str, value: Any, expire_seconds: int = 300) -> bool:
    """Set a value in cache with expiration."""
    client = await get_redis()
    try:
        await client.set(key, str(value), ex=expire_seconds)
        return True
    except Exception as e:
        logger.warning(f"Redis cache set failed for key '{key}': {e}")
        return False


async def cache_delete(key: str) -> bool:
    """Delete a key from cache."""
    client = await get_redis()
    try:
        await client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Redis cache delete failed for key '{key}': {e}")
        return False


async def check_rate_limit(
    key: str, max_requests: int = 60, window_seconds: int = 60
) -> bool:
    """
    Simple sliding window rate limiter.

    Returns True if the request is allowed, False if rate limited.
    """
    client = await get_redis()
    try:
        current = await client.incr(key)
        if current == 1:
            await client.expire(key, window_seconds)
        return current <= max_requests
    except Exception as e:
        logger.warning(f"Rate limit check failed for key '{key}': {e}")
        return True  # Fail open
