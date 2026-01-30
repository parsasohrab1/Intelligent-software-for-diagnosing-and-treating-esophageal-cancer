"""
Cache Warming Service

Handles pre-loading of frequently accessed data into cache on startup
and maintains warm cache for high-traffic endpoints.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

from app.core.advanced_cache import (
    CacheWarmer,
    MultiLevelCacheManager,
    get_cache_manager,
    get_cache_warmer,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheWarmingService:
    """
    Service for managing cache warming across the application.
    
    Registered endpoints for warming:
    - Dashboard statistics
    - Patients list
    - ML models list
    - Synthetic data statistics
    - Health metrics
    """
    
    def __init__(self):
        self._cache = get_cache_manager()
        self._warmer = get_cache_warmer()
        self._registered = False
    
    def register_warmers(self) -> None:
        """Register all cache warmers for high-traffic endpoints"""
        if self._registered:
            return
        
        # Dashboard statistics
        self._warmer.register(
            key="dashboard_stats",
            loader=self._load_dashboard_stats,
            ttl=getattr(settings, 'CACHE_TTL_DASHBOARD', 300),
            interval=150,  # Warm every 2.5 minutes
            priority=1  # Highest priority
        )
        
        # Patients list (first page)
        self._warmer.register(
            key="patients_list_page_1",
            loader=self._load_patients_list,
            ttl=getattr(settings, 'CACHE_TTL_PATIENTS_LIST', 120),
            interval=60,  # Warm every minute
            priority=1
        )
        
        # ML models list
        self._warmer.register(
            key="ml_models_list",
            loader=self._load_ml_models,
            ttl=getattr(settings, 'CACHE_TTL_ML_MODELS', 600),
            interval=300,  # Warm every 5 minutes
            priority=2
        )
        
        # Synthetic data statistics
        self._warmer.register(
            key="synthetic_data_stats",
            loader=self._load_synthetic_stats,
            ttl=getattr(settings, 'CACHE_TTL_STATISTICS', 900),
            interval=450,  # Warm every 7.5 minutes
            priority=3
        )
        
        # Health metrics summary
        self._warmer.register(
            key="health_metrics_summary",
            loader=self._load_health_metrics,
            ttl=60,  # 1 minute
            interval=30,  # Warm every 30 seconds
            priority=1
        )
        
        # CDS services list (static, warm once)
        self._warmer.register(
            key="cds_services_list",
            loader=self._load_cds_services,
            ttl=86400,  # 24 hours
            interval=3600,  # Warm every hour
            priority=5
        )
        
        self._registered = True
        logger.info(f"Registered {len(self._warmer._warm_registry)} cache warmers")
    
    async def _load_dashboard_stats(self) -> Dict[str, Any]:
        """Load dashboard statistics"""
        try:
            from app.core.database import get_db
            from sqlalchemy import func
            from app.models.patient import Patient
            from app.models.imaging_data import ImagingData

            db = next(get_db())
            try:
                total_patients = db.query(func.count(Patient.patient_id)).scalar() or 0
                total_studies = db.query(func.count(ImagingData.image_id)).scalar() or 0
                return {
                    "total_patients": total_patients,
                    "total_studies": total_studies,
                    "last_updated": "warm_cache"
                }
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Failed to load dashboard stats for warming: {e}")
            return {
                "total_patients": 0,
                "total_studies": 0,
                "status": "unavailable"
            }
    
    async def _load_patients_list(self) -> List[Dict[str, Any]]:
        """Load first page of patients list"""
        try:
            from app.core.database import get_db
            from app.models.patient import Patient

            db = next(get_db())
            try:
                patients = db.query(Patient).limit(20).all()
                return [
                    {
                        "id": str(p.patient_id),
                        "name": f"Patient {p.patient_id}",
                        "status": "cancer" if p.has_cancer else "non_cancer"
                    }
                    for p in patients
                ]
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Failed to load patients list for warming: {e}")
            return []
    
    async def _load_ml_models(self) -> List[Dict[str, Any]]:
        """Load ML models list"""
        try:
            from app.services.model_registry import ModelRegistry
            
            registry = ModelRegistry()
            models = registry.list_models()
            return models[:50]  # Limit to first 50 models
        except Exception as e:
            logger.warning(f"Failed to load ML models for warming: {e}")
            return []
    
    async def _load_synthetic_stats(self) -> Dict[str, Any]:
        """Load synthetic data statistics"""
        try:
            from app.core.database import get_db
            from app.models.patient import Patient
            from app.models.imaging_data import ImagingData
            from sqlalchemy import func

            db = next(get_db())
            try:
                n_patients = db.query(func.count(Patient.patient_id)).scalar() or 0
                n_imaging = db.query(func.count(ImagingData.image_id)).scalar() or 0
                return {
                    "total_patients": n_patients,
                    "total_imaging": n_imaging,
                    "status": "ok"
                }
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Failed to load synthetic stats for warming: {e}")
            return {"status": "unavailable", "error": str(e)}
    
    async def _load_health_metrics(self) -> Dict[str, Any]:
        """Load health metrics summary"""
        try:
            from app.core.health_check import HealthCheckService

            service = HealthCheckService()
            return service.get_readiness()
        except Exception as e:
            logger.warning(f"Failed to load health metrics for warming: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def _load_cds_services(self) -> List[Dict[str, Any]]:
        """Load CDS services list"""
        # Static data - define available CDS services
        return [
            {
                "id": "risk-predictor",
                "name": "Cancer Risk Predictor",
                "hook": "patient-view",
                "description": "Predicts cancer risk based on patient data"
            },
            {
                "id": "treatment-recommender",
                "name": "Treatment Recommender",
                "hook": "order-select",
                "description": "Recommends treatment options"
            },
            {
                "id": "prognostic-scorer",
                "name": "Prognostic Scorer",
                "hook": "patient-view",
                "description": "Calculates prognosis scores"
            },
            {
                "id": "clinical-trial-matcher",
                "name": "Clinical Trial Matcher",
                "hook": "patient-view",
                "description": "Matches patients to clinical trials"
            }
        ]
    
    async def warm_startup(self) -> Dict[str, bool]:
        """
        Warm all caches on application startup.
        Called from main.py lifespan.
        """
        if not getattr(settings, 'CACHE_WARMING_ENABLED', True):
            logger.info("Cache warming is disabled")
            return {}
        
        self.register_warmers()
        
        logger.info("Starting cache warming on startup...")
        results = await self._warmer.warm_all(force=True)
        
        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        
        logger.info(f"Cache warming complete: {success_count}/{total_count} successful")
        
        return results
    
    async def start_background_warming(self) -> None:
        """Start background cache warming"""
        if not getattr(settings, 'CACHE_WARMING_ENABLED', True):
            return
        
        self.register_warmers()
        await self._warmer.start_background_warming(
            check_interval=getattr(settings, 'CACHE_WARMING_INTERVAL', 60)
        )
    
    async def stop_background_warming(self) -> None:
        """Stop background cache warming"""
        await self._warmer.stop_background_warming()
    
    def get_warming_status(self) -> Dict[str, Any]:
        """Get current warming status"""
        return self._warmer.get_status()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self._cache.get_stats()


# Global instance
_warming_service: Optional[CacheWarmingService] = None


def get_warming_service() -> CacheWarmingService:
    """Get singleton warming service instance"""
    global _warming_service
    if _warming_service is None:
        _warming_service = CacheWarmingService()
    return _warming_service


async def initialize_cache_warming() -> None:
    """Initialize cache warming on application startup"""
    service = get_warming_service()
    
    if getattr(settings, 'CACHE_WARMING_ON_STARTUP', True):
        await service.warm_startup()
    
    if getattr(settings, 'CACHE_WARMING_ENABLED', True):
        await service.start_background_warming()


async def shutdown_cache_warming() -> None:
    """Shutdown cache warming"""
    service = get_warming_service()
    await service.stop_background_warming()
