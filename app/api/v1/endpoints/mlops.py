"""
MLOps endpoints for model monitoring, A/B testing, and messaging
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from app.services.mlops.model_monitoring import ModelMonitoring
from app.services.mlops.ab_testing import ABTestManager
from app.services.messaging.message_queue import get_message_queue
from app.services.model_registry import ModelRegistry

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

