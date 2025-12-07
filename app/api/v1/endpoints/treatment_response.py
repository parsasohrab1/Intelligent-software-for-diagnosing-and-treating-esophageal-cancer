"""
Treatment Response Prediction API Endpoints
API برای پیش‌بینی پاسخ به درمان نئوادجوانت
"""
import logging
from typing import Dict, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import numpy as np
import cv2

from app.core.database import get_db
from app.core.security.dependencies import get_current_user_with_role, require_role
from app.core.security.rbac import Role
from app.models.user import User
from app.models.patient import Patient
from app.models.genomic_data import GenomicData
from app.models.imaging_data import ImagingData
from app.services.treatment_response.treatment_response_predictor import TreatmentResponsePredictor
from app.services.radiomics.radiomics_extractor import RadiomicsExtractor

logger = logging.getLogger(__name__)

router = APIRouter()


class TreatmentResponseRequest(BaseModel):
    """Request for treatment response prediction"""
    patient_id: str = Field(..., description="Patient ID")
    treatment_type: str = Field("Chemotherapy", description="Treatment type: Chemotherapy or Radiotherapy")
    model_id: Optional[str] = Field(None, description="Model ID (optional)")
    use_imaging: bool = Field(True, description="Use imaging data for radiomics")


@router.post("/predict")
async def predict_treatment_response(
    request: TreatmentResponseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_role)
):
    """
    پیش‌بینی پاسخ بیمار به شیمی‌درمانی یا رادیوتراپی نئوادجوانت
    
    این endpoint بر اساس ویژگی‌های بیومارکر و رادیومیکس، احتمال پاسخ موفقیت‌آمیز را پیش‌بینی می‌کند.
    """
    try:
        # Get patient
        patient = db.query(Patient).filter(Patient.patient_id == request.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {request.patient_id} not found")
        
        # Get genomic data (biomarkers)
        genomic_data = db.query(GenomicData).filter(
            GenomicData.patient_id == request.patient_id
        ).first()
        
        if not genomic_data:
            raise HTTPException(
                status_code=404,
                detail=f"Genomic data not found for patient {request.patient_id}"
            )
        
        # Prepare biomarkers
        biomarkers = {
            "pdl1_status": genomic_data.pdl1_status,
            "pdl1_percentage": genomic_data.pdl1_percentage,
            "msi_status": genomic_data.msi_status,
            "her2_status": "positive" if genomic_data.gene_expression and isinstance(genomic_data.gene_expression, dict) and genomic_data.gene_expression.get("ERBB2", 0) > 2.0 else "negative",
            "mutations": genomic_data.mutations or {},
            "copy_number_variations": genomic_data.copy_number_variations or {},
            "gene_expression": genomic_data.gene_expression or {}
        }
        
        # Get imaging data for radiomics
        imaging_data_array = None
        radiomics_features = None
        
        if request.use_imaging:
            imaging_data = db.query(ImagingData).filter(
                ImagingData.patient_id == request.patient_id
            ).order_by(ImagingData.imaging_date.desc()).first()
            
            if imaging_data:
                # In production, load actual image from storage
                # For now, we'll extract radiomics from available data
                radiomics_extractor = RadiomicsExtractor()
                # Note: In production, you would load the actual image file
                # For demonstration, we'll use placeholder
                radiomics_features = {
                    "modality": imaging_data.imaging_modality,
                    "first_order": {
                        "mean": 100.0,
                        "std": 20.0,
                        "entropy": 4.5
                    },
                    "texture": {
                        "homogeneity": 0.7,
                        "contrast": 2.5
                    }
                }
        
        # Predict
        predictor = TreatmentResponsePredictor()
        prediction = predictor.predict_response(
            patient_id=request.patient_id,
            biomarkers=biomarkers,
            radiomics_features=radiomics_features,
            imaging_data=imaging_data_array,
            treatment_type=request.treatment_type,
            model_id=request.model_id
        )
        
        return {
            "patient_id": prediction.patient_id,
            "treatment_type": prediction.treatment_type,
            "response_probability": prediction.response_probability,
            "response_category": prediction.response_category,
            "confidence": prediction.confidence,
            "biomarkers_contribution": prediction.biomarkers_contribution,
            "radiomics_contribution": prediction.radiomics_contribution,
            "key_factors": prediction.key_factors,
            "recommendation": prediction.recommendation,
            "timestamp": prediction.timestamp
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting treatment response: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error predicting treatment response: {str(e)}")


@router.post("/predict-with-image")
async def predict_treatment_response_with_image(
    patient_id: str = Query(...),
    treatment_type: str = Query("Chemotherapy"),
    file: UploadFile = File(...),
    model_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_role)
):
    """
    پیش‌بینی پاسخ درمانی با استفاده از تصویر برای استخراج رادیومیکس
    """
    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Get patient and genomic data
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
        
        genomic_data = db.query(GenomicData).filter(
            GenomicData.patient_id == patient_id
        ).first()
        
        if not genomic_data:
            raise HTTPException(
                status_code=404,
                detail=f"Genomic data not found for patient {patient_id}"
            )
        
        # Prepare biomarkers
        biomarkers = {
            "pdl1_status": genomic_data.pdl1_status,
            "pdl1_percentage": genomic_data.pdl1_percentage,
            "msi_status": genomic_data.msi_status,
            "her2_status": "positive" if genomic_data.gene_expression and isinstance(genomic_data.gene_expression, dict) and genomic_data.gene_expression.get("ERBB2", 0) > 2.0 else "negative",
            "mutations": genomic_data.mutations or {},
            "copy_number_variations": genomic_data.copy_number_variations or {},
            "gene_expression": genomic_data.gene_expression or {}
        }
        
        # Predict with image
        predictor = TreatmentResponsePredictor()
        prediction = predictor.predict_response(
            patient_id=patient_id,
            biomarkers=biomarkers,
            imaging_data=image,
            treatment_type=treatment_type,
            model_id=model_id
        )
        
        return {
            "patient_id": prediction.patient_id,
            "treatment_type": prediction.treatment_type,
            "response_probability": prediction.response_probability,
            "response_category": prediction.response_category,
            "confidence": prediction.confidence,
            "biomarkers_contribution": prediction.biomarkers_contribution,
            "radiomics_contribution": prediction.radiomics_contribution,
            "key_factors": prediction.key_factors,
            "recommendation": prediction.recommendation,
            "timestamp": prediction.timestamp
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting treatment response with image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error predicting treatment response: {str(e)}")


@router.get("/patient/{patient_id}/history")
async def get_treatment_response_history(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_role)
):
    """
    دریافت تاریخچه پیش‌بینی‌های پاسخ درمانی برای یک بیمار
    """
    try:
        # In production, this would query a treatment_response_predictions table
        # For now, return current prediction
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
        
        return {
            "patient_id": patient_id,
            "predictions": [],
            "message": "Treatment response prediction history will be stored in future updates"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting treatment response history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting history: {str(e)}")

