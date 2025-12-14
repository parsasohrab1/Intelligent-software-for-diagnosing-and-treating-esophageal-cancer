"""
Redis client configuration
"""
from typing import Optional

_redis_client = None


def get_redis_client():
    """Get Redis client instance"""
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            from app.core.config import settings
            
            _redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            # Test connection
            _redis_client.ping()
        except Exception:
            # Redis not available, return None
            _redis_client = None
    return _redis_client


def close_redis_connection():
    """Close Redis connection"""
    global _redis_client
    if _redis_client:
        _redis_client.close()
        _redis_client = None

