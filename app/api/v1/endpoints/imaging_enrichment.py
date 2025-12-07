"""
Imaging Data Enrichment API Endpoints
API برای اضافه کردن داده‌های رادیولوژی و آندوسکوپی با تفسیر
"""
import logging
from typing import Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import date

from app.core.database import get_db
from app.core.security.dependencies import require_role, get_current_user_with_role
from app.core.security.rbac import Role
from app.models.user import User
from app.services.imaging_data_enrichment import ImagingDataEnrichment
from app.models.imaging_data import ImagingData

logger = logging.getLogger(__name__)

router = APIRouter()


class RadiologyDataRequest(BaseModel):
    """Request for adding radiology data"""
    patient_id: str = Field(..., description="Patient ID")
    modality: str = Field("CT_Chest_Abdomen", description="Imaging modality")
    findings: Optional[str] = Field(None, description="Radiology findings")
    impression: Optional[str] = Field(None, description="Radiologist impression")
    tumor_length_cm: Optional[float] = Field(None, description="Tumor length in cm")
    wall_thickness_cm: Optional[float] = Field(None, description="Wall thickness in cm")
    lymph_nodes_positive: Optional[int] = Field(None, description="Number of positive lymph nodes")
    contrast_used: bool = Field(True, description="Whether contrast was used")
    radiologist_id: Optional[str] = Field(None, description="Radiologist ID")
    imaging_date: Optional[date] = Field(None, description="Imaging date")


class EndoscopyDataRequest(BaseModel):
    """Request for adding endoscopy data"""
    patient_id: str = Field(..., description="Patient ID")
    findings: Optional[str] = Field(None, description="Endoscopy findings")
    impression: Optional[str] = Field(None, description="Endoscopist impression")
    tumor_length_cm: Optional[float] = Field(None, description="Tumor length in cm")
    wall_thickness_cm: Optional[float] = Field(None, description="Wall thickness in cm")
    lymph_nodes_positive: Optional[int] = Field(None, description="Number of positive lymph nodes")
    endoscopist_id: Optional[str] = Field(None, description="Endoscopist ID")
    imaging_date: Optional[date] = Field(None, description="Endoscopy date")


class EnrichAllPatientsRequest(BaseModel):
    """Request for enriching all patients"""
    include_radiology: bool = Field(True, description="Include radiology data")
    include_endoscopy: bool = Field(True, description="Include endoscopy data")
    generate_interpretations: bool = Field(True, description="Generate automatic interpretations")


@router.post("/radiology")
async def add_radiology_data(
    request: RadiologyDataRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.MEDICAL_ONCOLOGIST, Role.DATA_ENGINEER, Role.SYSTEM_ADMINISTRATOR))
):
    """
    اضافه کردن داده رادیولوژی برای یک بیمار
    """
    try:
        enrichment = ImagingDataEnrichment(db)
        imaging_data = enrichment.add_radiology_data(
            patient_id=request.patient_id,
            modality=request.modality,
            findings=request.findings,
            impression=request.impression,
            tumor_length_cm=request.tumor_length_cm,
            wall_thickness_cm=request.wall_thickness_cm,
            lymph_nodes_positive=request.lymph_nodes_positive,
            contrast_used=request.contrast_used,
            radiologist_id=request.radiologist_id,
            imaging_date=request.imaging_date
        )

        return {
            "success": True,
            "message": f"Radiology data added for patient {request.patient_id}",
            "image_id": imaging_data.image_id,
            "imaging_data": {
                "image_id": imaging_data.image_id,
                "patient_id": imaging_data.patient_id,
                "imaging_modality": imaging_data.imaging_modality,
                "findings": imaging_data.findings,
                "impression": imaging_data.impression,
                "tumor_length_cm": imaging_data.tumor_length_cm,
                "wall_thickness_cm": imaging_data.wall_thickness_cm,
                "lymph_nodes_positive": imaging_data.lymph_nodes_positive,
                "contrast_used": imaging_data.contrast_used,
                "radiologist_id": imaging_data.radiologist_id,
                "imaging_date": imaging_data.imaging_date.isoformat() if imaging_data.imaging_date else None
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding radiology data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding radiology data: {str(e)}")


@router.post("/endoscopy")
async def add_endoscopy_data(
    request: EndoscopyDataRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.MEDICAL_ONCOLOGIST, Role.DATA_ENGINEER, Role.SYSTEM_ADMINISTRATOR))
):
    """
    اضافه کردن داده آندوسکوپی برای یک بیمار
    """
    try:
        enrichment = ImagingDataEnrichment(db)
        imaging_data = enrichment.add_endoscopy_data(
            patient_id=request.patient_id,
            findings=request.findings,
            impression=request.impression,
            tumor_length_cm=request.tumor_length_cm,
            wall_thickness_cm=request.wall_thickness_cm,
            lymph_nodes_positive=request.lymph_nodes_positive,
            endoscopist_id=request.endoscopist_id,
            imaging_date=request.imaging_date
        )

        return {
            "success": True,
            "message": f"Endoscopy data added for patient {request.patient_id}",
            "image_id": imaging_data.image_id,
            "imaging_data": {
                "image_id": imaging_data.image_id,
                "patient_id": imaging_data.patient_id,
                "imaging_modality": imaging_data.imaging_modality,
                "findings": imaging_data.findings,
                "impression": imaging_data.impression,
                "tumor_length_cm": imaging_data.tumor_length_cm,
                "wall_thickness_cm": imaging_data.wall_thickness_cm,
                "lymph_nodes_positive": imaging_data.lymph_nodes_positive,
                "contrast_used": imaging_data.contrast_used,
                "radiologist_id": imaging_data.radiologist_id,
                "imaging_date": imaging_data.imaging_date.isoformat() if imaging_data.imaging_date else None
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding endoscopy data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding endoscopy data: {str(e)}")


@router.post("/enrich-all")
async def enrich_all_patients(
    request: EnrichAllPatientsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.SYSTEM_ADMINISTRATOR, Role.DATA_ENGINEER))
):
    """
    غنی‌سازی داده‌های تصویربرداری برای تمام بیماران موجود در دیتابیس
    
    این endpoint داده‌های رادیولوژی و آندوسکوپی با تفسیر را برای تمام بیماران اضافه می‌کند.
    """
    try:
        enrichment = ImagingDataEnrichment(db)
        stats = enrichment.enrich_all_patients(
            include_radiology=request.include_radiology,
            include_endoscopy=request.include_endoscopy,
            generate_interpretations=request.generate_interpretations
        )

        return {
            "success": True,
            "message": "Imaging data enrichment completed",
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error enriching all patients: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error enriching all patients: {str(e)}")


@router.get("/patient/{patient_id}/imaging")
async def get_patient_imaging_data(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_role)
):
    """
    دریافت تمام داده‌های تصویربرداری یک بیمار (شامل رادیولوژی و آندوسکوپی)
    """
    try:
        imaging_data_list = db.query(ImagingData).filter(
            ImagingData.patient_id == patient_id
        ).order_by(ImagingData.imaging_date.desc()).all()

        result = []
        for img in imaging_data_list:
            result.append({
                "image_id": img.image_id,
                "patient_id": img.patient_id,
                "imaging_modality": img.imaging_modality,
                "findings": img.findings,
                "impression": img.impression,
                "tumor_length_cm": img.tumor_length_cm,
                "wall_thickness_cm": img.wall_thickness_cm,
                "lymph_nodes_positive": img.lymph_nodes_positive,
                "contrast_used": img.contrast_used,
                "radiologist_id": img.radiologist_id,
                "imaging_date": img.imaging_date.isoformat() if img.imaging_date else None
            })

        return {
            "patient_id": patient_id,
            "imaging_data": result,
            "count": len(result)
        }
    except Exception as e:
        logger.error(f"Error getting patient imaging data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting patient imaging data: {str(e)}")

