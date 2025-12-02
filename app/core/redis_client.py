"""
Redis client configuration
"""
import redis
from typing import Optional

from app.core.config import settings

_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Get Redis client instance"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True,
        )
    return _redis_client


def close_redis_connection():
    """Close Redis connection"""
    global _redis_client
    if _redis_client:
        _redis_client.close()
        _redis_client = None

