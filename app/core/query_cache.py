"""
Query result caching for database queries
"""
from typing import Optional, Any, Callable
from functools import wraps
from sqlalchemy.orm import Query
from app.core.cache import CacheManager
import hashlib
import json


class QueryCache:
    """Cache SQLAlchemy query results"""
    
    def __init__(self, default_ttl: int = 300):
        self.cache_manager = CacheManager()
        self.default_ttl = default_ttl
    
    def cache_query(
        self,
        query: Query,
        ttl: Optional[int] = None,
        key_prefix: str = "query"
    ) -> Any:
        """Cache a SQLAlchemy query result"""
        # Generate cache key from query
        cache_key = self._generate_query_key(query, key_prefix)
        
        # Try to get from cache
        cached_result = self.cache_manager.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Execute query
        result = query.all()
        
        # Serialize result (convert ORM objects to dicts)
        serialized = self._serialize_result(result)
        
        # Cache result
        self.cache_manager.set(cache_key, serialized, ttl=ttl or self.default_ttl)
        
        return result
    
    def _generate_query_key(self, query: Query, prefix: str) -> str:
        """Generate cache key from query"""
        # Get query string
        query_str = str(query.statement.compile(compile_kwargs={"literal_binds": True}))
        
        # Generate hash
        key_string = f"{prefix}:{query_str}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _serialize_result(self, result: list) -> list:
        """Serialize ORM objects to dictionaries"""
        serialized = []
        for item in result:
            if hasattr(item, "__dict__"):
                # Remove SQLAlchemy internal attributes
                item_dict = {
                    k: v for k, v in item.__dict__.items()
                    if not k.startswith("_")
                }
                serialized.append(item_dict)
            else:
                serialized.append(item)
        return serialized
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        return self.cache_manager.clear_pattern(pattern)


def cached_query(ttl: int = 300, key_prefix: str = "query"):
    """Decorator to cache query results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_manager = CacheManager()
            cache_key = cache_manager.generate_key(
                key_prefix,
                func.__name__,
                *args,
                **kwargs
            )
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs) if hasattr(func, '__call__') else func(*args, **kwargs)
            
            # Store in cache
            cache_manager.set(cache_key, result, ttl=ttl)
            
            return result
        return wrapper
    return decorator

