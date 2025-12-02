"""
Main API router
"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    patients,
    synthetic_data,
    data_collection,
    data_integration,
    ml_models,
    cds,
    auth,
    audit,
    maintenance,
)

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(patients.router, prefix="/patients", tags=["patients"])
api_router.include_router(
    synthetic_data.router, prefix="/synthetic-data", tags=["synthetic-data"]
)
api_router.include_router(
    data_collection.router, prefix="/data-collection", tags=["data-collection"]
)
api_router.include_router(
    data_integration.router, prefix="/data-integration", tags=["data-integration"]
)
api_router.include_router(ml_models.router, prefix="/ml-models", tags=["ml-models"])
api_router.include_router(cds.router, prefix="/cds", tags=["clinical-decision-support"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["maintenance"])

