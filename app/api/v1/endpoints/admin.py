"""
Admin API for monitoring and troubleshooting.

Endpoints:
- GET /api/v1/admin/cache/stats — multi-level cache statistics (L1, L2, compression)
- GET /api/v1/admin/database/index-health — index health report (coverage, usage on PostgreSQL)
"""
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get(
    "/cache/stats",
    summary="Cache statistics",
    response_description="L1/L2 cache stats, compression and hit ratios",
)
async def get_cache_stats():
    """
    Return multi-level cache statistics for monitoring and troubleshooting.

    Includes L1 (in-memory) size and hits, L2 (Redis) availability and hits,
    compression stats and bytes saved, and overall warm calls.
    """
    try:
        from app.core.advanced_cache import get_cache_manager
        manager = get_cache_manager()
        return manager.get_stats()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Cache stats unavailable: {e}")


@router.get(
    "/database/index-health",
    summary="Database index health",
    response_description="Strategic indexes status, coverage, and usage (PostgreSQL)",
)
async def get_database_index_health():
    """
    Return database index health report from `get_index_health_report()`.

    Includes which strategic indexes exist per table, coverage percentage,
    all existing indexes, and on PostgreSQL also index usage analysis
    (scans, tuples read/fetched, recommendations).
    """
    try:
        from app.core.database_indexes import get_index_health_report
        return get_index_health_report()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Index health unavailable: {e}")
