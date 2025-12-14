"""
Explainable AI API Endpoints
API برای توضیح‌پذیری و Saliency Maps
"""
import logging
from typing import Dict, Optional, List
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query
from pydantic import BaseModel, Field
import numpy as np
import cv2

from app.core.security.dependencies import get_current_user_with_role
from app.models.user import User
from app.services.xai.explainable_ai import ExplainableAIService
from app.services.xai.saliency_maps import SaliencyMethod

logger = logging.getLogger(__name__)

router = APIRouter()

# Lazy initialization to avoid MongoDB connection on import
_xai_service = None

def get_xai_service():
    """Get XAI service instance (lazy initialization)"""
    global _xai_service
    if _xai_service is None:
        try:
            _xai_service = ExplainableAIService()
        except Exception as e:
            import logging
            logging.warning(f"Failed to initialize XAI service: {e}")
            _xai_service = None
    return _xai_service


class ExplainImageRequest(BaseModel):
    """Request for image explanation"""
    model_id: str = Field(..., description="Model ID")
    method: str = Field("grad_cam", description="Saliency method: grad_cam, lime, shap, etc.")
    target_class: Optional[int] = Field(None, description="Target class (if None, uses predicted class)")
    layer_name: Optional[str] = Field(None, description="Layer name for Grad-CAM")


@router.post("/explain-image")
async def explain_image_prediction(
    file: UploadFile = File(...),
    model_id: str = Query(...),
    method: str = Query("grad_cam"),
    target_class: Optional[int] = Query(None),
    layer_name: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user_with_role)
):
    """
    توضیح پیش‌بینی برای یک تصویر
    
    تولید Saliency Map/Heatmap برای نشان دادن مناطقی که مدل بر اساس آن‌ها تصمیم گرفته است
    """
    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Convert method string to enum
        try:
            saliency_method = SaliencyMethod(method.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown method: {method}. Available: {[m.value for m in SaliencyMethod]}"
            )
        
        # Generate explanation
        xai_service = get_xai_service()
        if xai_service is None:
            raise HTTPException(status_code=503, detail="XAI service is not available (MongoDB may not be running)")
        result = xai_service.explain_image_prediction(
            model_id=model_id,
            image=image,
            method=saliency_method,
            target_class=target_class,
            layer_name=layer_name
        )
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to generate explanation")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error explaining image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error explaining image: {str(e)}")


@router.post("/explain-batch")
async def explain_batch_predictions(
    files: List[UploadFile] = File(...),
    model_id: str = Query(...),
    method: str = Query("grad_cam"),
    current_user: User = Depends(get_current_user_with_role)
):
    """
    توضیح پیش‌بینی‌ها برای چند تصویر
    """
    try:
        # Read images
        images = []
        for file in files:
            contents = await file.read()
            nparr = np.frombuffer(contents, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if image is not None:
                images.append(image)
        
        if len(images) == 0:
            raise HTTPException(status_code=400, detail="No valid images provided")
        
        # Convert method string to enum
        try:
            saliency_method = SaliencyMethod(method.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown method: {method}"
            )
        
        # Generate explanations
        xai_service = get_xai_service()
        if xai_service is None:
            raise HTTPException(status_code=503, detail="XAI service is not available (MongoDB may not be running)")
        results = xai_service.explain_batch_predictions(
            model_id=model_id,
            images=images,
            method=saliency_method
        )
        
        return {
            "results": results,
            "count": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error explaining batch: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error explaining batch: {str(e)}")


@router.post("/compare-methods")
async def compare_explanation_methods(
    file: UploadFile = File(...),
    model_id: str = Query(...),
    methods: str = Query("grad_cam,lime,shap", description="Comma-separated list of methods"),
    current_user: User = Depends(get_current_user_with_role)
):
    """
    مقایسه توضیحات با روش‌های مختلف
    """
    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Parse methods
        method_list = [m.strip().lower() for m in methods.split(",")]
        saliency_methods = []
        
        for method_str in method_list:
            try:
                saliency_methods.append(SaliencyMethod(method_str))
            except ValueError:
                logger.warning(f"Unknown method: {method_str}, skipping")
        
        if len(saliency_methods) == 0:
            raise HTTPException(status_code=400, detail="No valid methods provided")
        
        # Compare explanations
        xai_service = get_xai_service()
        if xai_service is None:
            raise HTTPException(status_code=503, detail="XAI service is not available (MongoDB may not be running)")
        result = xai_service.compare_explanations(
            model_id=model_id,
            image=image,
            methods=saliency_methods
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing methods: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error comparing methods: {str(e)}")


@router.get("/methods")
async def get_available_methods(
    current_user: User = Depends(get_current_user_with_role)
):
    """دریافت لیست روش‌های توضیح‌پذیری موجود"""
    return {
        "methods": [
            {
                "name": method.value,
                "description": _get_method_description(method)
            }
            for method in SaliencyMethod
        ]
    }


def _get_method_description(method: SaliencyMethod) -> str:
    """دریافت توضیحات روش"""
    descriptions = {
        SaliencyMethod.GRAD_CAM: "Gradient-weighted Class Activation Mapping - Visualizes important regions using gradients",
        SaliencyMethod.GRAD_CAM_PLUS_PLUS: "Improved version of Grad-CAM with better localization",
        SaliencyMethod.LIME: "Local Interpretable Model-agnostic Explanations - Explains individual predictions",
        SaliencyMethod.SHAP: "SHapley Additive exPlanations - Game theory-based feature importance",
        SaliencyMethod.INTEGRATED_GRADIENTS: "Integrated Gradients - Attributes predictions to input features",
        SaliencyMethod.OCCLUSION: "Occlusion Sensitivity - Tests importance by occluding regions",
        SaliencyMethod.GUIDED_BACKPROP: "Guided Backpropagation - Visualizes important pixels"
    }
    return descriptions.get(method, "No description available")

