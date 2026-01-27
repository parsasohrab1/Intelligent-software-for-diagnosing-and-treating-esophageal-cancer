"""
Advanced Multi-level Caching System with Compression and Cache Warming

Features:
- L1 Cache: In-memory (fast, limited size)
- L2 Cache: Redis (slower, larger capacity)
- Automatic compression for large data
- Cache warming for high-traffic endpoints
- Statistics and monitoring
"""
import asyncio
import gzip
import hashlib
import json
import logging
import time
import zlib
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from threading import RLock
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from app.core.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class CompressionAlgorithm(Enum):
    """Supported compression algorithms"""
    NONE = "none"
    GZIP = "gzip"
    ZLIB = "zlib"


@dataclass
class CacheEntry:
    """Represents a single cache entry"""
    value: Any
    created_at: float
    ttl: int
    hits: int = 0
    last_accessed: float = field(default_factory=time.time)
    compressed: bool = False
    compression_algo: CompressionAlgorithm = CompressionAlgorithm.NONE
    original_size: int = 0
    compressed_size: int = 0


@dataclass
class CacheStats:
    """Cache statistics"""
    l1_hits: int = 0
    l1_misses: int = 0
    l2_hits: int = 0
    l2_misses: int = 0
    compressions: int = 0
    decompressions: int = 0
    bytes_saved: int = 0
    warm_calls: int = 0
    evictions: int = 0
    
    @property
    def l1_hit_ratio(self) -> float:
        total = self.l1_hits + self.l1_misses
        return self.l1_hits / total if total > 0 else 0.0
    
    @property
    def l2_hit_ratio(self) -> float:
        total = self.l2_hits + self.l2_misses
        return self.l2_hits / total if total > 0 else 0.0
    
    @property
    def overall_hit_ratio(self) -> float:
        total_hits = self.l1_hits + self.l2_hits
        total_requests = self.l1_hits + self.l1_misses
        return total_hits / total_requests if total_requests > 0 else 0.0
    
    def to_dict(self) -> Dict:
        return {
            "l1_hits": self.l1_hits,
            "l1_misses": self.l1_misses,
            "l1_hit_ratio": round(self.l1_hit_ratio, 4),
            "l2_hits": self.l2_hits,
            "l2_misses": self.l2_misses,
            "l2_hit_ratio": round(self.l2_hit_ratio, 4),
            "overall_hit_ratio": round(self.overall_hit_ratio, 4),
            "compressions": self.compressions,
            "decompressions": self.decompressions,
            "bytes_saved": self.bytes_saved,
            "warm_calls": self.warm_calls,
            "evictions": self.evictions
        }


class L1MemoryCache:
    """
    L1 In-memory cache using LRU eviction policy.
    Thread-safe implementation with size limits.
    """
    
    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = RLock()
        self._max_size = max_size
        self._max_memory_bytes = max_memory_mb * 1024 * 1024
        self._current_memory = 0
        self._stats = CacheStats()
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """Get entry from L1 cache"""
        with self._lock:
            if key not in self._cache:
                self._stats.l1_misses += 1
                return None
            
            entry = self._cache[key]
            
            # Check TTL
            if time.time() - entry.created_at > entry.ttl:
                self._remove_entry(key)
                self._stats.l1_misses += 1
                return None
            
            # Update access info and move to end (LRU)
            entry.hits += 1
            entry.last_accessed = time.time()
            self._cache.move_to_end(key)
            self._stats.l1_hits += 1
            
            return entry
    
    def set(self, key: str, entry: CacheEntry) -> bool:
        """Set entry in L1 cache"""
        with self._lock:
            # Calculate entry size
            entry_size = self._estimate_size(entry)
            
            # Evict entries if necessary
            while (len(self._cache) >= self._max_size or 
                   self._current_memory + entry_size > self._max_memory_bytes):
                if not self._evict_oldest():
                    break
            
            # Remove existing entry if present
            if key in self._cache:
                self._remove_entry(key)
            
            # Add new entry
            self._cache[key] = entry
            self._current_memory += entry_size
            return True
    
    def delete(self, key: str) -> bool:
        """Delete entry from L1 cache"""
        with self._lock:
            if key in self._cache:
                self._remove_entry(key)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all entries"""
        with self._lock:
            self._cache.clear()
            self._current_memory = 0
    
    def _remove_entry(self, key: str) -> None:
        """Remove entry and update memory tracking"""
        if key in self._cache:
            entry = self._cache.pop(key)
            self._current_memory -= self._estimate_size(entry)
    
    def _evict_oldest(self) -> bool:
        """Evict the oldest (least recently used) entry"""
        if not self._cache:
            return False
        
        oldest_key = next(iter(self._cache))
        self._remove_entry(oldest_key)
        self._stats.evictions += 1
        return True
    
    def _estimate_size(self, entry: CacheEntry) -> int:
        """Estimate memory size of entry in bytes"""
        try:
            if entry.compressed:
                return entry.compressed_size + 200  # metadata overhead
            return len(json.dumps(entry.value, default=str).encode()) + 200
        except Exception:
            return 1024  # default estimate
    
    @property
    def stats(self) -> CacheStats:
        return self._stats
    
    @property
    def size(self) -> int:
        return len(self._cache)
    
    @property
    def memory_usage_mb(self) -> float:
        return self._current_memory / (1024 * 1024)


class CacheCompressor:
    """Handles compression and decompression of cache data"""
    
    def __init__(
        self,
        compression_threshold: int = 1024,  # 1KB
        algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP,
        compression_level: int = 6
    ):
        self.compression_threshold = compression_threshold
        self.algorithm = algorithm
        self.compression_level = compression_level
        self._stats = CacheStats()
    
    def should_compress(self, data: bytes) -> bool:
        """Determine if data should be compressed"""
        return len(data) >= self.compression_threshold
    
    def compress(self, data: Any) -> Tuple[bytes, CompressionAlgorithm, int, int]:
        """
        Compress data if it exceeds threshold.
        Returns: (compressed_data, algorithm_used, original_size, compressed_size)
        """
        # Serialize to JSON
        serialized = json.dumps(data, default=str).encode('utf-8')
        original_size = len(serialized)
        
        if not self.should_compress(serialized):
            return serialized, CompressionAlgorithm.NONE, original_size, original_size
        
        # Compress based on algorithm
        if self.algorithm == CompressionAlgorithm.GZIP:
            compressed = gzip.compress(serialized, compresslevel=self.compression_level)
        elif self.algorithm == CompressionAlgorithm.ZLIB:
            compressed = zlib.compress(serialized, level=self.compression_level)
        else:
            return serialized, CompressionAlgorithm.NONE, original_size, original_size
        
        compressed_size = len(compressed)
        
        # Only use compression if it actually saves space
        if compressed_size >= original_size:
            return serialized, CompressionAlgorithm.NONE, original_size, original_size
        
        self._stats.compressions += 1
        self._stats.bytes_saved += (original_size - compressed_size)
        
        return compressed, self.algorithm, original_size, compressed_size
    
    def decompress(self, data: bytes, algorithm: CompressionAlgorithm) -> Any:
        """Decompress data and deserialize"""
        if algorithm == CompressionAlgorithm.NONE:
            return json.loads(data.decode('utf-8'))
        
        if algorithm == CompressionAlgorithm.GZIP:
            decompressed = gzip.decompress(data)
        elif algorithm == CompressionAlgorithm.ZLIB:
            decompressed = zlib.decompress(data)
        else:
            raise ValueError(f"Unknown compression algorithm: {algorithm}")
        
        self._stats.decompressions += 1
        return json.loads(decompressed.decode('utf-8'))
    
    @property
    def stats(self) -> CacheStats:
        return self._stats


class MultiLevelCacheManager:
    """
    Multi-level cache manager with L1 (Memory) and L2 (Redis) caching.
    
    Features:
    - Write-through caching strategy
    - Automatic compression for large values
    - LRU eviction for L1
    - TTL support for both levels
    - Statistics and monitoring
    """
    
    _instance = None
    _lock = RLock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern for cache manager"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(
        self,
        l1_max_size: int = 1000,
        l1_max_memory_mb: int = 100,
        default_ttl: int = 3600,
        compression_threshold: int = 1024,
        compression_algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP
    ):
        if self._initialized:
            return
        
        self._l1_cache = L1MemoryCache(
            max_size=l1_max_size,
            max_memory_mb=l1_max_memory_mb
        )
        self._compressor = CacheCompressor(
            compression_threshold=compression_threshold,
            algorithm=compression_algorithm
        )
        self._default_ttl = default_ttl
        self._redis = None
        self._stats = CacheStats()
        self._initialized = True
        
        # Try to initialize Redis
        try:
            self._redis = get_redis_client()
        except Exception as e:
            logger.warning(f"Redis not available for L2 cache: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        First checks L1 (memory), then L2 (Redis).
        """
        # Try L1 first
        l1_entry = self._l1_cache.get(key)
        if l1_entry is not None:
            if l1_entry.compressed:
                return self._compressor.decompress(
                    l1_entry.value,
                    l1_entry.compression_algo
                )
            return l1_entry.value
        
        # Try L2 (Redis)
        if self._redis is not None:
            try:
                redis_data = self._redis.get(f"ml_cache:{key}")
                if redis_data:
                    self._stats.l2_hits += 1
                    
                    # Parse Redis data
                    cache_data = json.loads(redis_data)
                    value = cache_data['value']
                    
                    # Handle compressed data
                    if cache_data.get('compressed'):
                        import base64
                        compressed_bytes = base64.b64decode(cache_data['value'])
                        algo = CompressionAlgorithm(cache_data['compression_algo'])
                        value = self._compressor.decompress(compressed_bytes, algo)
                    
                    # Promote to L1
                    self._promote_to_l1(key, value, cache_data.get('ttl', self._default_ttl))
                    
                    return value
                else:
                    self._stats.l2_misses += 1
            except Exception as e:
                logger.warning(f"L2 cache read error: {e}")
                self._stats.l2_misses += 1
        
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        l1_only: bool = False
    ) -> bool:
        """
        Set value in cache.
        Writes to both L1 and L2 (write-through).
        """
        ttl = ttl or self._default_ttl
        
        # Compress if needed
        compressed_data, algo, original_size, compressed_size = \
            self._compressor.compress(value)
        
        is_compressed = algo != CompressionAlgorithm.NONE
        
        # Create cache entry
        entry = CacheEntry(
            value=compressed_data if is_compressed else value,
            created_at=time.time(),
            ttl=ttl,
            compressed=is_compressed,
            compression_algo=algo,
            original_size=original_size,
            compressed_size=compressed_size
        )
        
        # Write to L1
        self._l1_cache.set(key, entry)
        
        # Write to L2 (Redis)
        if not l1_only and self._redis is not None:
            try:
                import base64
                
                redis_data = {
                    'value': base64.b64encode(compressed_data).decode() if is_compressed else value,
                    'compressed': is_compressed,
                    'compression_algo': algo.value,
                    'ttl': ttl,
                    'created_at': time.time()
                }
                
                self._redis.setex(
                    f"ml_cache:{key}",
                    ttl,
                    json.dumps(redis_data, default=str)
                )
            except Exception as e:
                logger.warning(f"L2 cache write error: {e}")
        
        return True
    
    def delete(self, key: str) -> bool:
        """Delete from both cache levels"""
        l1_deleted = self._l1_cache.delete(key)
        l2_deleted = False
        
        if self._redis is not None:
            try:
                l2_deleted = bool(self._redis.delete(f"ml_cache:{key}"))
            except Exception as e:
                logger.warning(f"L2 cache delete error: {e}")
        
        return l1_deleted or l2_deleted
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        count = 0
        
        # Clear from L1
        with self._l1_cache._lock:
            keys_to_delete = [
                k for k in self._l1_cache._cache.keys()
                if pattern.replace('*', '') in k
            ]
            for key in keys_to_delete:
                self._l1_cache._remove_entry(key)
                count += 1
        
        # Clear from L2
        if self._redis is not None:
            try:
                keys = self._redis.keys(f"ml_cache:{pattern}")
                if keys:
                    count += self._redis.delete(*keys)
            except Exception as e:
                logger.warning(f"L2 cache clear error: {e}")
        
        return count
    
    def _promote_to_l1(self, key: str, value: Any, ttl: int) -> None:
        """Promote a value from L2 to L1"""
        compressed_data, algo, original_size, compressed_size = \
            self._compressor.compress(value)
        
        is_compressed = algo != CompressionAlgorithm.NONE
        
        entry = CacheEntry(
            value=compressed_data if is_compressed else value,
            created_at=time.time(),
            ttl=ttl,
            compressed=is_compressed,
            compression_algo=algo,
            original_size=original_size,
            compressed_size=compressed_size
        )
        
        self._l1_cache.set(key, entry)
    
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        key_string = ":".join(key_parts)
        return f"{prefix}:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    def get_stats(self) -> Dict:
        """Get combined statistics from all cache levels"""
        l1_stats = self._l1_cache.stats.to_dict()
        compressor_stats = self._compressor.stats.to_dict()
        
        return {
            "l1": {
                **l1_stats,
                "size": self._l1_cache.size,
                "memory_usage_mb": round(self._l1_cache.memory_usage_mb, 2)
            },
            "l2": {
                "available": self._redis is not None,
                "hits": self._stats.l2_hits,
                "misses": self._stats.l2_misses
            },
            "compression": {
                "compressions": compressor_stats["compressions"],
                "decompressions": compressor_stats["decompressions"],
                "bytes_saved": compressor_stats["bytes_saved"]
            },
            "overall": {
                "total_hits": l1_stats["l1_hits"] + self._stats.l2_hits,
                "total_misses": l1_stats["l1_misses"],
                "warm_calls": self._stats.warm_calls
            }
        }
    
    def health_check(self) -> Dict:
        """Check health of all cache levels"""
        health = {
            "l1": {"status": "healthy", "size": self._l1_cache.size},
            "l2": {"status": "unavailable"}
        }
        
        if self._redis is not None:
            try:
                self._redis.ping()
                info = self._redis.info()
                health["l2"] = {
                    "status": "healthy",
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0)
                }
            except Exception as e:
                health["l2"] = {"status": "unhealthy", "error": str(e)}
        
        return health


class CacheWarmer:
    """
    Cache warming service for pre-loading frequently accessed data.
    
    Features:
    - Configurable warm-up endpoints
    - Scheduled warming
    - Priority-based warming
    - Statistics tracking
    """
    
    def __init__(self, cache_manager: MultiLevelCacheManager):
        self._cache = cache_manager
        self._warm_registry: Dict[str, WarmConfig] = {}
        self._stats = CacheStats()
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    def register(
        self,
        key: str,
        loader: Callable,
        ttl: int = 3600,
        interval: int = 1800,  # 30 minutes
        priority: int = 1
    ) -> None:
        """
        Register a cache key for warming.
        
        Args:
            key: Cache key or key prefix
            loader: Async function that loads the data
            ttl: Cache TTL in seconds
            interval: Warm interval in seconds
            priority: Priority (lower = higher priority)
        """
        self._warm_registry[key] = WarmConfig(
            key=key,
            loader=loader,
            ttl=ttl,
            interval=interval,
            priority=priority,
            last_warmed=0
        )
    
    def unregister(self, key: str) -> bool:
        """Unregister a cache key from warming"""
        if key in self._warm_registry:
            del self._warm_registry[key]
            return True
        return False
    
    async def warm(self, key: str) -> bool:
        """Warm a specific cache key"""
        if key not in self._warm_registry:
            return False
        
        config = self._warm_registry[key]
        try:
            # Load data
            if asyncio.iscoroutinefunction(config.loader):
                data = await config.loader()
            else:
                data = config.loader()
            
            # Store in cache
            self._cache.set(key, data, ttl=config.ttl)
            
            # Update stats
            config.last_warmed = time.time()
            self._stats.warm_calls += 1
            
            logger.info(f"Cache warmed: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Cache warm failed for {key}: {e}")
            return False
    
    async def warm_all(self, force: bool = False) -> Dict[str, bool]:
        """Warm all registered cache keys"""
        results = {}
        
        # Sort by priority
        sorted_configs = sorted(
            self._warm_registry.items(),
            key=lambda x: x[1].priority
        )
        
        for key, config in sorted_configs:
            # Check if warming is needed
            if not force and time.time() - config.last_warmed < config.interval:
                continue
            
            results[key] = await self.warm(key)
        
        return results
    
    async def start_background_warming(self, check_interval: int = 60) -> None:
        """Start background warming task"""
        if self._running:
            return
        
        self._running = True
        
        async def warming_loop():
            while self._running:
                try:
                    await self.warm_all()
                except Exception as e:
                    logger.error(f"Background warming error: {e}")
                
                await asyncio.sleep(check_interval)
        
        self._task = asyncio.create_task(warming_loop())
        logger.info("Cache warming background task started")
    
    async def stop_background_warming(self) -> None:
        """Stop background warming task"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Cache warming background task stopped")
    
    def get_status(self) -> Dict:
        """Get warming status"""
        return {
            "running": self._running,
            "registered_keys": len(self._warm_registry),
            "total_warm_calls": self._stats.warm_calls,
            "configs": {
                key: {
                    "ttl": config.ttl,
                    "interval": config.interval,
                    "priority": config.priority,
                    "last_warmed": datetime.fromtimestamp(config.last_warmed).isoformat()
                    if config.last_warmed > 0 else None
                }
                for key, config in self._warm_registry.items()
            }
        }


@dataclass
class WarmConfig:
    """Configuration for cache warming"""
    key: str
    loader: Callable
    ttl: int
    interval: int
    priority: int
    last_warmed: float


# Decorator for multi-level caching
def ml_cached(
    ttl: int = 3600,
    key_prefix: str = "cache",
    compression_threshold: int = 1024
):
    """
    Decorator to cache function results using multi-level cache.
    
    Args:
        ttl: Time-to-live in seconds
        key_prefix: Prefix for cache keys
        compression_threshold: Size threshold for compression
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = MultiLevelCacheManager()
            cache_key = cache.generate_key(key_prefix, func.__name__, *args, **kwargs)
            
            # Try cache first
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache = MultiLevelCacheManager()
            cache_key = cache.generate_key(key_prefix, func.__name__, *args, **kwargs)
            
            # Try cache first
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# Global instances
_cache_manager: Optional[MultiLevelCacheManager] = None
_cache_warmer: Optional[CacheWarmer] = None


def get_cache_manager() -> MultiLevelCacheManager:
    """Get singleton cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        from app.core.config import settings
        _cache_manager = MultiLevelCacheManager(
            l1_max_size=getattr(settings, 'CACHE_L1_MAX_SIZE', 1000),
            l1_max_memory_mb=getattr(settings, 'CACHE_L1_MAX_MEMORY_MB', 100),
            default_ttl=getattr(settings, 'CACHE_DEFAULT_TTL', 3600),
            compression_threshold=getattr(settings, 'CACHE_COMPRESSION_THRESHOLD', 1024)
        )
    return _cache_manager


def get_cache_warmer() -> CacheWarmer:
    """Get singleton cache warmer instance"""
    global _cache_warmer
    if _cache_warmer is None:
        _cache_warmer = CacheWarmer(get_cache_manager())
    return _cache_warmer
