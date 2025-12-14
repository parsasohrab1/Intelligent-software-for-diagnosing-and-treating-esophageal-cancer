"""
MLOps endpoints for model monitoring, A/B testing, messaging, CI/CD, and automated retraining
"""
from fastapi import APIRouter, HTTPException, Query, Depends, Body
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from app.services.mlops.model_monitoring import ModelMonitoring
from app.services.mlops.ab_testing import ABTestManager
from app.services.mlops.cicd_pipeline import MLModelCICDPipeline
from app.services.mlops.automated_retraining import AutomatedRetraining, RetrainTrigger
from app.services.mlops.production_monitoring import ProductionModelMonitoring
from app.services.mlops.model_versioning import ModelVersioning
from app.services.messaging.message_queue import get_message_queue
from app.services.model_registry import ModelRegistry
from app.core.security.dependencies import get_current_user_with_role, require_role
from app.core.security.rbac import Role
from app.models.user import User

router = APIRouter()


# Model Monitoring Endpoints
@router.get("/monitoring/{model_id}")
async def get_model_monitoring_status(model_id: str):
    """Get monitoring status for a specific model"""
    try:
        monitoring = ModelMonitoring()
        status = monitoring.get_monitoring_status(model_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting monitoring status: {str(e)}")


@router.get("/monitoring")
async def get_all_monitoring_status():
    """Get monitoring status for all active models"""
    try:
        monitoring = ModelMonitoring()
        status_list = monitoring.get_all_monitoring_status()
        return {"models": status_list, "count": len(status_list)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting monitoring status: {str(e)}")


@router.post("/monitoring/{model_id}/record")
async def record_prediction(
    model_id: str,
    features: Dict[str, Any],
    prediction: float,
    probability: Optional[List[float]] = None,
    ground_truth: Optional[float] = None,
):
    """Record a prediction for monitoring"""
    try:
        monitoring = ModelMonitoring()
        monitoring.record_prediction(
            model_id=model_id,
            features=features,
            prediction=prediction,
            probability=probability,
            ground_truth=ground_truth,
        )
        return {"message": "Prediction recorded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording prediction: {str(e)}")


# A/B Testing Endpoints
class CreateABTestRequest(BaseModel):
    """Request model for creating A/B test"""
    test_name: str = Field(..., description="Name of the A/B test")
    control_model_id: str = Field(..., description="Control model ID")
    treatment_model_id: str = Field(..., description="Treatment model ID")
    traffic_split: float = Field(0.5, ge=0.0, le=1.0, description="Traffic split to treatment (0.0-1.0)")
    metric: str = Field("accuracy", description="Metric to evaluate")


@router.post("/ab-testing/create")
async def create_ab_test(request: CreateABTestRequest):
    """Create a new A/B test"""
    try:
        ab_manager = ABTestManager()
        test_id = ab_manager.create_ab_test(
            test_name=request.test_name,
            control_model_id=request.control_model_id,
            treatment_model_id=request.treatment_model_id,
            traffic_split=request.traffic_split,
            metric=request.metric,
        )
        return {"test_id": test_id, "message": "A/B test created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating A/B test: {str(e)}")


@router.get("/ab-testing")
async def list_ab_tests():
    """List all active A/B tests"""
    try:
        ab_manager = ABTestManager()
        tests = ab_manager.list_active_tests()
        return {"tests": tests, "count": len(tests)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing A/B tests: {str(e)}")


@router.get("/ab-testing/{test_id}")
async def get_ab_test_results(test_id: str):
    """Get A/B test results"""
    try:
        ab_manager = ABTestManager()
        results = ab_manager.get_test_results(test_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting A/B test results: {str(e)}")


@router.post("/ab-testing/{test_id}/select-model")
async def select_model_for_ab_test(
    test_id: str,
    user_id: Optional[str] = Query(None, description="User ID for consistent assignment"),
):
    """Select which model to use for A/B testing"""
    try:
        ab_manager = ABTestManager()
        model_id, variant = ab_manager.select_model(test_id, user_id)
        return {"model_id": model_id, "variant": variant, "test_id": test_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error selecting model: {str(e)}")


@router.post("/ab-testing/{test_id}/record")
async def record_ab_test_result(
    test_id: str,
    variant: str,
    prediction: float,
    ground_truth: Optional[float] = None,
    metrics: Optional[Dict[str, float]] = None,
):
    """Record result for A/B test"""
    try:
        ab_manager = ABTestManager()
        ab_manager.record_prediction_result(
            test_id=test_id,
            variant=variant,
            prediction=prediction,
            ground_truth=ground_truth,
            metrics=metrics,
        )
        return {"message": "Result recorded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording result: {str(e)}")


@router.post("/ab-testing/{test_id}/stop")
async def stop_ab_test(test_id: str, winner: Optional[str] = Query(None, description="Winner: 'control' or 'treatment'")):
    """Stop an A/B test"""
    try:
        ab_manager = ABTestManager()
        result = ab_manager.stop_test(test_id, winner)
        return {"message": "A/B test stopped", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping A/B test: {str(e)}")


# Messaging Endpoints
class PublishMessageRequest(BaseModel):
    """Request model for publishing message"""
    topic: str = Field(..., description="Topic/queue name")
    message: Dict[str, Any] = Field(..., description="Message content")


@router.post("/messaging/publish")
async def publish_message(request: PublishMessageRequest):
    """Publish a message to the message queue"""
    try:
        queue = get_message_queue()
        success = queue.publish(request.topic, request.message)
        if success:
            return {"message": "Message published successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to publish message")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error publishing message: {str(e)}")


@router.get("/messaging/status")
async def get_messaging_status():
    """Get messaging queue status"""
    try:
        from app.core.config import settings
        queue = get_message_queue()
        return {
            "queue_type": settings.MESSAGE_QUEUE_TYPE,
            "connected": queue is not None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting messaging status: {str(e)}")


# CI/CD Pipeline Endpoints
class RunPipelineRequest(BaseModel):
    """Request model for running CI/CD pipeline"""
    model_type: str = Field(..., description="Type of model to train")
    trigger_reason: str = Field("manual", description="Reason for running pipeline")


@router.post("/cicd/run-pipeline")
async def run_cicd_pipeline(
    request: RunPipelineRequest,
    current_user: User = Depends(require_role(Role.SYSTEM_ADMINISTRATOR, Role.DATA_ENGINEER))
):
    """Run CI/CD pipeline for model training and deployment"""
    try:
        pipeline = MLModelCICDPipeline()
        result = pipeline.run_pipeline(
            model_type=request.model_type,
            trigger_reason=request.trigger_reason
        )
        
        return {
            "pipeline_id": result.pipeline_id,
            "status": result.status.value,
            "model_id": result.model_id,
            "stages": {
                stage: {
                    "success": stage_result.get("success", False),
                    "timestamp": stage_result.get("timestamp")
                }
                for stage, stage_result in result.stages.items()
            },
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "error": result.error,
            "metrics": result.metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running pipeline: {str(e)}")


@router.get("/cicd/pipeline-history")
async def get_pipeline_history(
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user_with_role)
):
    """Get CI/CD pipeline history"""
    try:
        pipeline = MLModelCICDPipeline()
        history = pipeline.get_pipeline_history(limit=limit)
        return {"history": history, "count": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting pipeline history: {str(e)}")


@router.get("/cicd/check-retrain/{model_id}")
async def check_retrain_conditions(
    model_id: str,
    current_user: User = Depends(get_current_user_with_role)
):
    """Check if model needs retraining"""
    try:
        pipeline = MLModelCICDPipeline()
        result = pipeline.check_retrain_conditions(model_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking retrain conditions: {str(e)}")


# Automated Retraining Endpoints
@router.post("/retraining/start")
async def start_automated_retraining(
    current_user: User = Depends(require_role(Role.SYSTEM_ADMINISTRATOR))
):
    """Start automated retraining system"""
    try:
        retraining = AutomatedRetraining()
        retraining.start_automated_retraining()
        return {"message": "Automated retraining started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting automated retraining: {str(e)}")


@router.post("/retraining/stop")
async def stop_automated_retraining(
    current_user: User = Depends(require_role(Role.SYSTEM_ADMINISTRATOR))
):
    """Stop automated retraining system"""
    try:
        retraining = AutomatedRetraining()
        retraining.stop_automated_retraining()
        return {"message": "Automated retraining stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping automated retraining: {str(e)}")


@router.post("/retraining/trigger")
async def trigger_retraining(
    model_type: str = Query(..., description="Type of model to retrain"),
    trigger: str = Query("manual", description="Trigger type"),
    current_user: User = Depends(require_role(Role.SYSTEM_ADMINISTRATOR, Role.DATA_ENGINEER))
):
    """Manually trigger model retraining"""
    try:
        retraining = AutomatedRetraining()
        result = retraining.trigger_retraining(
            model_type=model_type,
            trigger=RetrainTrigger(trigger)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering retraining: {str(e)}")


@router.get("/retraining/history")
async def get_retraining_history(
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user_with_role)
):
    """Get retraining history"""
    try:
        retraining = AutomatedRetraining()
        history = retraining.get_retraining_history(model_type=model_type, limit=limit)
        return {"history": history, "count": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting retraining history: {str(e)}")


@router.get("/retraining/stats")
async def get_retraining_stats(
    current_user: User = Depends(get_current_user_with_role)
):
    """Get retraining statistics"""
    try:
        retraining = AutomatedRetraining()
        stats = retraining.get_retraining_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting retraining stats: {str(e)}")


# Production Monitoring Endpoints
@router.get("/production-monitoring")
async def get_production_monitoring(
    current_user: User = Depends(get_current_user_with_role)
):
    """Get production monitoring for all models"""
    try:
        monitoring = ProductionModelMonitoring()
        results = monitoring.monitor_production_models()
        return {"models": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting production monitoring: {str(e)}")


@router.get("/production-monitoring/{model_id}")
async def get_model_production_monitoring(
    model_id: str,
    current_user: User = Depends(get_current_user_with_role)
):
    """Get production monitoring for a specific model"""
    try:
        monitoring = ProductionModelMonitoring()
        result = monitoring.monitor_single_model(model_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting model monitoring: {str(e)}")


@router.get("/production-monitoring/alerts")
async def get_monitoring_alerts(
    model_id: Optional[str] = Query(None, description="Filter by model ID"),
    level: Optional[str] = Query(None, description="Filter by alert level"),
    current_user: User = Depends(get_current_user_with_role)
):
    """Get monitoring alerts"""
    try:
        from app.services.mlops.production_monitoring import AlertLevel
        monitoring = ProductionModelMonitoring()
        
        alert_level = AlertLevel(level) if level else None
        alerts = monitoring.get_alerts(model_id=model_id, level=alert_level)
        
        return {"alerts": alerts, "count": len(alerts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting alerts: {str(e)}")


# Model Versioning Endpoints
class CreateModelVersionRequest(BaseModel):
    """Request model for creating model version"""
    model_id: str = Field(..., description="Model ID")
    model_path: str = Field(..., description="Path to model file")
    metrics: Dict[str, Any] = Field(..., description="Model metrics")
    version_number: Optional[str] = Field(None, description="Version number (auto-generated if not provided)")
    changelog: Optional[str] = Field(None, description="Changelog")

@router.post("/versioning/create-version")
async def create_model_version(
    request: CreateModelVersionRequest,
    current_user: User = Depends(require_role(Role.SYSTEM_ADMINISTRATOR, Role.DATA_ENGINEER))
):
    """Create a new model version"""
    try:
        versioning = ModelVersioning()
        version = versioning.create_version(
            model_id=request.model_id,
            model_path=request.model_path,
            metrics=request.metrics,
            version_number=request.version_number,
            changelog=request.changelog
        )
        
        return {
            "version_id": version.version_id,
            "version_number": version.version_number,
            "status": version.status.value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating version: {str(e)}")


@router.get("/versioning/{model_id}/versions")
async def get_model_versions(
    model_id: str,
    current_user: User = Depends(get_current_user_with_role)
):
    """Get all versions of a model"""
    try:
        versioning = ModelVersioning()
        history = versioning.get_version_history(model_id)
        return {"versions": history, "count": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting versions: {str(e)}")


@router.post("/versioning/{version_id}/promote-to-production")
async def promote_to_production(
    version_id: str,
    current_user: User = Depends(require_role(Role.SYSTEM_ADMINISTRATOR))
):
    """Promote a model version to production"""
    try:
        versioning = ModelVersioning()
        success = versioning.promote_to_production(version_id)
        
        if success:
            return {"message": "Version promoted to production", "version_id": version_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to promote version")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error promoting version: {str(e)}")


@router.post("/versioning/{model_id}/rollback")
async def rollback_model(
    model_id: str,
    version_id: Optional[str] = Query(None, description="Version ID to rollback to (if not provided, rolls back to previous)"),
    current_user: User = Depends(require_role(Role.SYSTEM_ADMINISTRATOR))
):
    """Rollback model to a previous version"""
    try:
        versioning = ModelVersioning()
        
        if version_id:
            success = versioning.rollback_to_version(version_id)
            if success:
                return {"message": f"Rolled back to version {version_id}", "version_id": version_id}
            else:
                raise HTTPException(status_code=400, detail="Failed to rollback")
        else:
            version = versioning.rollback_to_previous(model_id)
            if version:
                return {
                    "message": "Rolled back to previous version",
                    "version_id": version.version_id,
                    "version_number": version.version_number
                }
            else:
                raise HTTPException(status_code=400, detail="No previous version found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rolling back: {str(e)}")

