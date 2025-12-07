"""
Multi-Modal Fusion API Endpoints
API برای ادغام چندوجهی با Attention Mechanism
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
from app.models.patient import Patient
from app.models.genomic_data import GenomicData
from app.models.lab_results import LabResult
from app.models.imaging_data import ImagingData
from app.services.multimodal_fusion.fusion_service import MultiModalFusionService

logger = logging.getLogger(__name__)

router = APIRouter()


class MultiModalPredictionRequest(BaseModel):
    """Request for multi-modal prediction"""
    patient_id: str = Field(..., description="Patient ID")
    use_endoscopy: bool = Field(True, description="Use endoscopy image")
    use_radiomics: bool = Field(True, description="Use radiomics features")
    use_lab: bool = Field(True, description="Use lab results")
    use_genomic: bool = Field(True, description="Use genomic data")
    return_attention_weights: bool = Field(True, description="Return attention weights for explainability")


@router.post("/predict")
async def predict_multimodal(
    request: MultiModalPredictionRequest,
    endoscopy_image: Optional[UploadFile] = File(None),
    ct_image: Optional[UploadFile] = File(None),
    pet_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_role)
):
    """
    پیش‌بینی با ادغام چندوجهی
    
    ترکیب تصاویر آندوسکوپی، داده‌های رادیومیکس، و اطلاعات آزمایشگاهی/ژنتیکی
    با استفاده از Attention Mechanism برای وزن‌دهی هوشمند
    """
    try:
        # Get patient
        patient = db.query(Patient).filter(Patient.patient_id == request.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {request.patient_id} not found")
        
        # Initialize fusion service
        fusion_service = MultiModalFusionService()
        
        # Load or build model (in production, load from registry)
        # For now, build a default model
        try:
            fusion_service.build_and_compile_model(
                endoscopy_shape=(224, 224, 3) if request.use_endoscopy else None,
                radiomics_dim=13 if request.use_radiomics else None,
                lab_dim=8 if request.use_lab else None,
                genomic_dim=9 if request.use_genomic else None,
                num_classes=2
            )
        except Exception as e:
            logger.warning(f"Could not build model, using rule-based: {str(e)}")
            # Fallback to rule-based prediction
            return await _rule_based_prediction(request, patient, db)
        
        # Prepare inputs
        inputs = {}
        
        # Endoscopy image
        if request.use_endoscopy and endoscopy_image:
            contents = await endoscopy_image.read()
            nparr = np.frombuffer(contents, np.uint8)
            endoscopy_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if endoscopy_img is not None:
                inputs['endoscopy'] = endoscopy_img
        
        # Extract radiomics from CT/PET
        if request.use_radiomics:
            radiomics_features = []
            
            if ct_image:
                contents = await ct_image.read()
                nparr = np.frombuffer(contents, np.uint8)
                ct_img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
                if ct_img is not None:
                    radiomics_dict = fusion_service.radiomics_extractor.extract_features(
                        image=ct_img,
                        modality='CT'
                    )
                    radiomics_features.append(
                        fusion_service._dict_to_radiomics_array(radiomics_dict)
                    )
            
            if pet_image:
                contents = await pet_image.read()
                nparr = np.frombuffer(contents, np.uint8)
                pet_img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
                if pet_img is not None:
                    radiomics_dict = fusion_service.radiomics_extractor.extract_features(
                        image=pet_img,
                        modality='PET'
                    )
                    radiomics_features.append(
                        fusion_service._dict_to_radiomics_array(radiomics_dict)
                    )
            
            # Get from database if no images provided
            if not radiomics_features:
                imaging_data = db.query(ImagingData).filter(
                    ImagingData.patient_id == request.patient_id
                ).first()
                if imaging_data:
                    # Use placeholder radiomics
                    radiomics_features.append(np.zeros(13, dtype=np.float32))
            
            if radiomics_features:
                inputs['radiomics'] = np.mean(radiomics_features, axis=0)
        
        # Lab features
        if request.use_lab:
            lab_result = db.query(LabResult).filter(
                LabResult.patient_id == request.patient_id
            ).order_by(LabResult.test_date.desc()).first()
            
            if lab_result:
                lab_dict = {
                    'hemoglobin': lab_result.hemoglobin or 0.0,
                    'wbc_count': lab_result.wbc_count or 0.0,
                    'platelet_count': lab_result.platelet_count or 0.0,
                    'creatinine': lab_result.creatinine or 0.0,
                    'cea': lab_result.cea or 0.0,
                    'ca19_9': lab_result.ca19_9 or 0.0,
                    'crp': lab_result.crp or 0.0,
                    'albumin': lab_result.albumin or 0.0
                }
                inputs['lab'] = fusion_service._extract_lab_features(lab_dict)
        
        # Genomic features
        if request.use_genomic:
            genomic_data = db.query(GenomicData).filter(
                GenomicData.patient_id == request.patient_id
            ).first()
            
            if genomic_data:
                genomic_dict = {
                    'pdl1_status': genomic_data.pdl1_status,
                    'pdl1_percentage': genomic_data.pdl1_percentage,
                    'msi_status': genomic_data.msi_status,
                    'mutations': genomic_data.mutations or {},
                    'copy_number_variations': genomic_data.copy_number_variations or {}
                }
                inputs['genomic'] = fusion_service._extract_genomic_features(genomic_dict)
        
        # Prepare inputs for model
        prepared_inputs = fusion_service.prepare_inputs(**inputs)
        
        # Predict
        result = fusion_service.predict(
            inputs=prepared_inputs,
            return_attention_weights=request.return_attention_weights
        )
        
        return {
            "patient_id": request.patient_id,
            "prediction": result['prediction'],
            "confidence": result['confidence'],
            "probabilities": result['probabilities'],
            "modalities_used": list(prepared_inputs.keys()),
            "attention_weights": result.get('attention_weights'),
            "modality_contributions": result.get('modality_contributions'),
            "timestamp": result['timestamp']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in multi-modal prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in prediction: {str(e)}")


async def _rule_based_prediction(
    request: MultiModalPredictionRequest,
    patient: Patient,
    db: Session
) -> Dict:
    """Fallback rule-based prediction"""
    score = 0.5
    
    # Simple rule-based scoring
    if request.use_genomic:
        genomic_data = db.query(GenomicData).filter(
            GenomicData.patient_id == request.patient_id
        ).first()
        if genomic_data and genomic_data.pdl1_status == 'positive':
            score += 0.2
    
    return {
        "patient_id": request.patient_id,
        "prediction": min(1.0, max(0.0, score)),
        "confidence": 0.6,
        "probabilities": [1 - score, score],
        "modalities_used": [],
        "method": "rule_based",
        "note": "Model not available, using rule-based prediction"
    }


@router.post("/build-model")
async def build_fusion_model(
    endoscopy_shape: Optional[List[int]] = Query(None),
    radiomics_dim: Optional[int] = Query(None),
    lab_dim: Optional[int] = Query(None),
    genomic_dim: Optional[int] = Query(None),
    embed_dim: int = Query(256),
    num_attention_heads: int = Query(8),
    num_attention_layers: int = Query(2),
    current_user: User = Depends(require_role(Role.SYSTEM_ADMINISTRATOR, Role.DATA_ENGINEER))
):
    """
    ساخت مدل ادغام چندوجهی با پارامترهای سفارشی
    
    این endpoint برای توسعه‌دهندگان و محققان است
    """
    try:
        fusion_service = MultiModalFusionService()
        
        endoscopy_shape_tuple = None
        if endoscopy_shape and len(endoscopy_shape) == 3:
            endoscopy_shape_tuple = tuple(endoscopy_shape)
        
        model = fusion_service.build_and_compile_model(
            endoscopy_shape=endoscopy_shape_tuple,
            radiomics_dim=radiomics_dim,
            lab_dim=lab_dim,
            genomic_dim=genomic_dim,
            embed_dim=embed_dim,
            num_attention_heads=num_attention_heads,
            num_attention_layers=num_attention_layers
        )
        
        # Get model summary
        summary_lines = []
        if hasattr(model, 'summary'):
            import io
            import sys
            old_stdout = sys.stdout
            sys.stdout = buffer = io.StringIO()
            model.summary()
            sys.stdout = old_stdout
            summary_lines = buffer.getvalue().split('\n')
        
        return {
            "status": "success",
            "model_name": model.name,
            "total_params": model.count_params(),
            "input_shapes": {inp.name: inp.shape for inp in model.inputs},
            "output_shape": model.output_shape,
            "summary": summary_lines[:50]  # First 50 lines
        }
        
    except Exception as e:
        logger.error(f"Error building model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error building model: {str(e)}")


@router.get("/model-info")
async def get_model_info(
    current_user: User = Depends(get_current_user_with_role)
):
    """دریافت اطلاعات مدل ادغام چندوجهی"""
    return {
        "architecture": "Multi-Modal Attention Fusion",
        "description": "Innovative architecture for fusing multi-modal medical data using attention mechanism",
        "modalities_supported": [
            "Endoscopy Images",
            "Radiomics (CT/PET)",
            "Lab Results",
            "Genomic Data"
        ],
        "key_features": [
            "Modality-specific encoders",
            "Cross-modal attention layers",
            "Intelligent weighting",
            "Explainable attention weights"
        ],
        "innovation": "Patent-pending attention mechanism for medical data fusion"
    }

