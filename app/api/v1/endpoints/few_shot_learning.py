"""
Few-Shot Learning API Endpoints
API برای تشخیص زیرگونه‌های نادر با Few-Shot Learning
"""
import logging
from typing import Dict, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from pydantic import BaseModel, Field
import numpy as np
import cv2

from app.core.database import get_db
from sqlalchemy.orm import Session
from app.core.security.dependencies import get_current_user_with_role, require_role
from app.core.security.rbac import Role
from app.models.user import User
from app.services.few_shot_learning.few_shot_service import FewShotLearningService

logger = logging.getLogger(__name__)

router = APIRouter()


class FewShotTrainingRequest(BaseModel):
    """Request for few-shot training"""
    subtype: str = Field(..., description="Rare subtype name")
    n_way: int = Field(..., description="Number of classes")
    k_shot: int = Field(..., description="Number of samples per class")
    method: str = Field("prototypical", description="Few-shot method: prototypical, transfer_learning")
    use_transfer_learning: bool = Field(True, description="Use transfer learning")


class FewShotPredictionRequest(BaseModel):
    """Request for few-shot prediction"""
    subtype: str = Field(..., description="Rare subtype name")
    method: str = Field("prototypical", description="Few-shot method")


@router.post("/train")
async def train_few_shot_model(
    request: FewShotTrainingRequest,
    support_files: List[UploadFile] = File(...),
    query_files: List[UploadFile] = File(...),
    support_labels: List[int] = Query(...),
    query_labels: List[int] = Query(...),
    current_user: User = Depends(require_role([Role.ADMIN, Role.DEVELOPER]))
):
    """
    آموزش مدل Few-Shot Learning برای زیرگونه نادر
    
    این endpoint برای آموزش با داده‌های کم طراحی شده است.
    """
    try:
        # Load images
        support_images = []
        for file in support_files:
            contents = await file.read()
            nparr = np.frombuffer(contents, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is not None:
                # Resize and normalize
                img = cv2.resize(img, (224, 224))
                img = img.astype(np.float32) / 255.0
                support_images.append(img)
        
        query_images = []
        for file in query_files:
            contents = await file.read()
            nparr = np.frombuffer(contents, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is not None:
                img = cv2.resize(img, (224, 224))
                img = img.astype(np.float32) / 255.0
                query_images.append(img)
        
        if len(support_images) == 0 or len(query_images) == 0:
            raise HTTPException(status_code=400, detail="No valid images provided")
        
        support_set = np.array(support_images)
        query_set = np.array(query_images)
        support_labels = np.array(support_labels)
        query_labels = np.array(query_labels)
        
        # Initialize service
        service = FewShotLearningService(
            method=request.method,
            use_transfer_learning=request.use_transfer_learning
        )
        
        service.initialize_for_subtype(
            subtype=request.subtype,
            input_shape=(224, 224, 3),
            num_classes=request.n_way
        )
        
        # Train
        result = service.train_few_shot(
            support_set=support_set,
            support_labels=support_labels,
            query_set=query_set,
            query_labels=query_labels,
            n_way=request.n_way,
            k_shot=request.k_shot,
            epochs=50
        )
        
        return {
            "subtype": request.subtype,
            "method": result["method"],
            "accuracy": result["accuracy"],
            "final_accuracy": result.get("final_accuracy", result["accuracy"]),
            "n_way": request.n_way,
            "k_shot": request.k_shot,
            "support_samples": len(support_set),
            "query_samples": len(query_set)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in few-shot training: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in training: {str(e)}")


@router.post("/predict")
async def predict_rare_subtype(
    request: FewShotPredictionRequest,
    query_files: List[UploadFile] = File(...),
    support_files: Optional[List[UploadFile]] = File(None),
    support_labels: Optional[List[int]] = Query(None),
    current_user: User = Depends(get_current_user_with_role)
):
    """
    پیش‌بینی زیرگونه نادر با Few-Shot Learning
    """
    try:
        # Load query images
        query_images = []
        for file in query_files:
            contents = await file.read()
            nparr = np.frombuffer(contents, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is not None:
                img = cv2.resize(img, (224, 224))
                img = img.astype(np.float32) / 255.0
                query_images.append(img)
        
        if len(query_images) == 0:
            raise HTTPException(status_code=400, detail="No valid query images")
        
        query_set = np.array(query_images)
        
        # Initialize service
        service = FewShotLearningService(
            method=request.method,
            use_transfer_learning=True
        )
        
        service.initialize_for_subtype(
            subtype=request.subtype,
            input_shape=(224, 224, 3),
            num_classes=2
        )
        
        # Load support set if provided
        support_set = None
        support_labels_array = None
        
        if support_files and support_labels:
            support_images = []
            for file in support_files:
                contents = await file.read()
                nparr = np.frombuffer(contents, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is not None:
                    img = cv2.resize(img, (224, 224))
                    img = img.astype(np.float32) / 255.0
                    support_images.append(img)
            
            if support_images:
                support_set = np.array(support_images)
                support_labels_array = np.array(support_labels)
        
        # Predict
        result = service.predict_rare_subtype(
            query_samples=query_set,
            support_set=support_set,
            support_labels=support_labels_array
        )
        
        return {
            "subtype": request.subtype,
            "predictions": result["predictions"],
            "probabilities": result["probabilities"],
            "confidence": result["confidence"],
            "method": request.method
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in few-shot prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in prediction: {str(e)}")


@router.get("/rare-subtypes")
async def get_rare_subtypes(
    current_user: User = Depends(get_current_user_with_role)
):
    """دریافت لیست زیرگونه‌های نادر پشتیبانی شده"""
    service = FewShotLearningService()
    subtypes = service.get_rare_subtypes_info()
    
    return {
        "rare_subtypes": subtypes,
        "description": "Rare esophageal cancer subtypes supported for few-shot learning",
        "methods_available": ["prototypical", "transfer_learning"]
    }


@router.get("/method-info")
async def get_method_info(
    method: str = Query("prototypical"),
    current_user: User = Depends(get_current_user_with_role)
):
    """دریافت اطلاعات روش Few-Shot Learning"""
    methods_info = {
        "prototypical": {
            "name": "Prototypical Networks",
            "description": "Learns a metric space where samples cluster around class prototypes",
            "advantages": [
                "Simple and effective",
                "Works well with very few samples (5-shot)",
                "Fast inference"
            ],
            "use_cases": [
                "Rare subtype classification",
                "Few-shot diagnosis",
                "Rapid adaptation to new classes"
            ]
        },
        "transfer_learning": {
            "name": "Transfer Learning with Adaptive Unfreezing",
            "description": "Innovative transfer learning method optimized for few-shot scenarios",
            "advantages": [
                "Leverages pre-trained models",
                "Adaptive unfreezing strategy",
                "Differential learning rates",
                "Patent-pending optimization"
            ],
            "use_cases": [
                "Rare subtype detection",
                "Precancerous condition classification",
                "Image-based few-shot learning"
            ],
            "innovation": "Adaptive unfreezing and differential learning rates for few-shot optimization"
        }
    }
    
    if method not in methods_info:
        raise HTTPException(status_code=404, detail=f"Method {method} not found")
    
    return methods_info[method]

