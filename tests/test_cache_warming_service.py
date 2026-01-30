"""
Unit tests for cache warming service.

Uses mocks for DB and Redis so cache warming behavior can be verified
without real database or Redis.
"""
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_db_session():
    """Mock database session: count queries return 0, limit().all() returns []."""
    session = MagicMock()
    session.query.return_value.scalar.return_value = 0
    session.query.return_value.limit.return_value.all.return_value = []
    session.close = MagicMock()
    return session


@pytest.fixture
def mock_get_db(mock_db_session):
    """Mock get_db to yield a single session."""

    def _get_db():
        yield mock_db_session

    return _get_db


@pytest.fixture
def mock_cache():
    """Mock multi-level cache manager (no Redis)."""
    cache = MagicMock()
    cache.get_stats.return_value = {
        "l1": {"size": 0, "memory_usage_mb": 0},
        "l2": {"available": False, "hits": 0, "misses": 0},
        "compression": {"compressions": 0, "bytes_saved": 0},
        "overall": {"total_hits": 0, "total_misses": 0, "warm_calls": 0},
    }
    cache.get.return_value = None
    cache.set.return_value = True
    return cache


@pytest.fixture
def mock_warmer(mock_cache):
    """Real CacheWarmer with mock cache so register/warm_all work."""
    from app.core.advanced_cache import CacheWarmer
    return CacheWarmer(mock_cache)


@pytest.fixture
def warming_service(mock_cache, mock_warmer):
    """CacheWarmingService with mocked get_cache_manager and get_cache_warmer."""
    with patch("app.services.cache_warming_service.get_cache_manager", return_value=mock_cache), \
         patch("app.services.cache_warming_service.get_cache_warmer", return_value=mock_warmer):
        from app.services.cache_warming_service import CacheWarmingService
        return CacheWarmingService()


class TestCacheWarmingService:
    """Tests for CacheWarmingService with mocked DB and cache."""

    def test_register_warmers_registers_keys(self, warming_service, mock_warmer):
        """Registering warmers should populate the warmer registry."""
        warming_service.register_warmers()
        assert len(mock_warmer._warm_registry) >= 5
        assert "dashboard_stats" in mock_warmer._warm_registry
        assert "patients_list_page_1" in mock_warmer._warm_registry
        assert "ml_models_list" in mock_warmer._warm_registry
        assert "synthetic_data_stats" in mock_warmer._warm_registry
        assert "health_metrics_summary" in mock_warmer._warm_registry
        assert "cds_services_list" in mock_warmer._warm_registry

    def test_register_warmers_idempotent(self, warming_service, mock_warmer):
        """Calling register_warmers twice should not duplicate entries."""
        warming_service.register_warmers()
        count_first = len(mock_warmer._warm_registry)
        warming_service.register_warmers()
        assert len(mock_warmer._warm_registry) == count_first

    @pytest.mark.asyncio
    async def test_warm_startup_returns_dict(self, warming_service, mock_get_db):
        """warm_startup should return a dict of key -> bool."""
        with patch("app.core.database.get_db", mock_get_db), \
             patch("app.services.model_registry.ModelRegistry") as MockRegistry, \
             patch("app.core.health_check.HealthCheckService") as MockHealth, \
             patch("app.services.cache_warming_service.settings") as mock_settings:
            MockRegistry.return_value.list_models.return_value = []
            MockHealth.return_value.get_readiness.return_value = {"status": "ok"}
            mock_settings.CACHE_WARMING_ENABLED = True
            mock_settings.CACHE_WARMING_ON_STARTUP = True
            mock_settings.CACHE_WARMING_INTERVAL = 60
            mock_settings.CACHE_TTL_DASHBOARD = 300
            mock_settings.CACHE_TTL_PATIENTS_LIST = 120
            mock_settings.CACHE_TTL_ML_MODELS = 600
            mock_settings.CACHE_TTL_STATISTICS = 900
            result = await warming_service.warm_startup()
        assert isinstance(result, dict)
        for k, v in result.items():
            assert isinstance(k, str)
            assert isinstance(v, bool)

    def test_get_warming_status_returns_dict(self, warming_service, mock_warmer):
        """get_warming_status should return running, registered_keys, configs."""
        warming_service.register_warmers()
        status = warming_service.get_warming_status()
        assert isinstance(status, dict)
        assert "running" in status
        assert "registered_keys" in status
        assert status["registered_keys"] >= 5
        assert "configs" in status

    def test_get_cache_stats_returns_dict(self, warming_service, mock_cache):
        """get_cache_stats should return cache statistics."""
        stats = warming_service.get_cache_stats()
        assert isinstance(stats, dict)
        mock_cache.get_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_cds_services_static(self, warming_service):
        """_load_cds_services returns static list (no DB)."""
        result = await warming_service._load_cds_services()
        assert isinstance(result, list)
        assert len(result) >= 4
        assert any(s.get("id") == "risk-predictor" for s in result)
        assert any(s.get("id") == "treatment-recommender" for s in result)

    @pytest.mark.asyncio
    async def test_warm_startup_respects_disabled(self, warming_service, mock_warmer):
        """When CACHE_WARMING_ENABLED is False, warm_startup returns empty."""
        with patch("app.services.cache_warming_service.settings") as mock_settings:
            mock_settings.CACHE_WARMING_ENABLED = False
            result = await warming_service.warm_startup()
        assert result == {}
