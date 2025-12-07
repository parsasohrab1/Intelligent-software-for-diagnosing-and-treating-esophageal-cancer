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
    imaging,
    patient_monitoring,
    mlops,
    multi_modality,
    consent,
    data_privacy,
    compliance,
    realtime,
    integration,
    xai,
    imaging_enrichment,
    treatment_response,
    surgical_guidance,
    multimodal_fusion,
    few_shot_learning,
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
api_router.include_router(imaging.router, prefix="/imaging", tags=["imaging"])
api_router.include_router(patient_monitoring.router, prefix="/monitoring", tags=["patient-monitoring"])
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["maintenance"])
api_router.include_router(mlops.router, prefix="/mlops", tags=["mlops"])
api_router.include_router(multi_modality.router, prefix="/multi-modality", tags=["multi-modality"])
api_router.include_router(consent.router, prefix="/consent", tags=["consent-management"])
api_router.include_router(data_privacy.router, prefix="/data-privacy", tags=["data-privacy"])
api_router.include_router(compliance.router, prefix="/compliance", tags=["regulatory-compliance"])
api_router.include_router(realtime.router, prefix="/realtime", tags=["real-time-processing"])
api_router.include_router(integration.router, prefix="/integration", tags=["clinical-integration"])
api_router.include_router(xai.router, prefix="/xai", tags=["explainable-ai"])
api_router.include_router(imaging_enrichment.router, prefix="/imaging-enrichment", tags=["imaging-enrichment"])
api_router.include_router(treatment_response.router, prefix="/treatment-response", tags=["treatment-response-prediction"])
api_router.include_router(surgical_guidance.router, prefix="/surgical-guidance", tags=["surgical-guidance"])
api_router.include_router(multimodal_fusion.router, prefix="/multimodal-fusion", tags=["multi-modal-fusion"])
api_router.include_router(few_shot_learning.router, prefix="/few-shot-learning", tags=["few-shot-learning"])

