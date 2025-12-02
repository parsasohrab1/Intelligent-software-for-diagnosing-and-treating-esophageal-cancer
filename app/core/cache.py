"""
Caching utilities
"""
from typing import Optional, Any
import json
import hashlib
from functools import wraps
from app.core.redis_client import get_redis_client


class CacheManager:
    """Cache manager using Redis"""

    def __init__(self):
        self.redis = get_redis_client()
        self.default_ttl = 3600  # 1 hour

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value)
            return self.redis.setex(key, ttl, serialized)
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            return bool(self.redis.delete(key))
        except Exception:
            return False

    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception:
            return 0

    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()


def cached(ttl: int = 3600, key_prefix: str = "cache"):
    """Decorator to cache function results"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_manager = CacheManager()
            cache_key = cache_manager.generate_key(key_prefix, func.__name__, *args, **kwargs)

            # Try to get from cache
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = await func(*args, **kwargs) if hasattr(func, '__call__') else func(*args, **kwargs)

            # Store in cache
            cache_manager.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator

