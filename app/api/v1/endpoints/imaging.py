"""
Imaging data endpoints including MRI
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.models.imaging_data import ImagingData
from app.models.patient import Patient
from pydantic import BaseModel

router = APIRouter()


class ImagingDataResponse(BaseModel):
    """Response model for imaging data"""
    image_id: int
    patient_id: str
    imaging_modality: str
    findings: Optional[str]
    impression: Optional[str]
    tumor_length_cm: Optional[float]
    wall_thickness_cm: Optional[float]
    lymph_nodes_positive: Optional[int]
    contrast_used: bool
    radiologist_id: Optional[str]
    imaging_date: Optional[date]
    
    class Config:
        from_attributes = True


class MRIReportResponse(BaseModel):
    """Response model for MRI report with image info"""
    image_id: int
    patient_id: str
    patient_name: Optional[str]
    imaging_date: Optional[date]
    findings: Optional[str]
    impression: Optional[str]
    tumor_length_cm: Optional[float]
    wall_thickness_cm: Optional[float]
    lymph_nodes_positive: Optional[int]
    contrast_used: bool
    radiologist_id: Optional[str]
    report_summary: str
    
    class Config:
        from_attributes = True


@router.get("/mri", response_model=List[ImagingDataResponse])
async def get_mri_images(
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all MRI images"""
    query = db.query(ImagingData).filter(ImagingData.imaging_modality == "MRI")
    
    if patient_id:
        query = query.filter(ImagingData.patient_id == patient_id)
    
    images = query.order_by(ImagingData.imaging_date.desc()).offset(skip).limit(limit).all()
    return images


@router.get("/mri/{image_id}", response_model=ImagingDataResponse)
async def get_mri_image(
    image_id: int,
    db: Session = Depends(get_db)
):
    """Get specific MRI image by ID"""
    image = db.query(ImagingData).filter(
        ImagingData.image_id == image_id,
        ImagingData.imaging_modality == "MRI"
    ).first()
    
    if not image:
        raise HTTPException(status_code=404, detail="MRI image not found")
    
    return image


@router.get("/mri/reports", response_model=List[MRIReportResponse])
async def get_mri_reports(
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get MRI reports with patient information"""
    query = db.query(ImagingData, Patient).join(
        Patient, ImagingData.patient_id == Patient.patient_id
    ).filter(ImagingData.imaging_modality == "MRI")
    
    if patient_id:
        query = query.filter(ImagingData.patient_id == patient_id)
    
    results = query.order_by(ImagingData.imaging_date.desc()).offset(skip).limit(limit).all()
    
    reports = []
    for image, patient in results:
        # Generate report summary
        report_summary = f"MRI scan for patient {patient.patient_id}"
        if image.findings:
            report_summary += f". Findings: {image.findings[:100]}"
        if image.impression:
            report_summary += f". Impression: {image.impression}"
        
        reports.append(MRIReportResponse(
            image_id=image.image_id,
            patient_id=image.patient_id,
            patient_name=getattr(patient, 'name', None),
            imaging_date=image.imaging_date,
            findings=image.findings,
            impression=image.impression,
            tumor_length_cm=image.tumor_length_cm,
            wall_thickness_cm=image.wall_thickness_cm,
            lymph_nodes_positive=image.lymph_nodes_positive,
            contrast_used=image.contrast_used,
            radiologist_id=image.radiologist_id,
            report_summary=report_summary
        ))
    
    return reports


@router.get("/mri/{image_id}/report", response_model=MRIReportResponse)
async def get_mri_report(
    image_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed MRI report for specific image"""
    result = db.query(ImagingData, Patient).join(
        Patient, ImagingData.patient_id == Patient.patient_id
    ).filter(
        ImagingData.image_id == image_id,
        ImagingData.imaging_modality == "MRI"
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="MRI image not found")
    
    image, patient = result
    
    # Generate detailed report summary
    report_parts = []
    if image.findings:
        report_parts.append(f"Findings: {image.findings}")
    if image.impression:
        report_parts.append(f"Impression: {image.impression}")
    if image.tumor_length_cm:
        report_parts.append(f"Tumor length: {image.tumor_length_cm} cm")
    if image.wall_thickness_cm:
        report_parts.append(f"Wall thickness: {image.wall_thickness_cm} cm")
    if image.lymph_nodes_positive is not None:
        report_parts.append(f"Lymph nodes positive: {image.lymph_nodes_positive}")
    
    report_summary = ". ".join(report_parts) if report_parts else "No detailed findings available"
    
    return MRIReportResponse(
        image_id=image.image_id,
        patient_id=image.patient_id,
        patient_name=getattr(patient, 'name', None),
        imaging_date=image.imaging_date,
        findings=image.findings,
        impression=image.impression,
        tumor_length_cm=image.tumor_length_cm,
        wall_thickness_cm=image.wall_thickness_cm,
        lymph_nodes_positive=image.lymph_nodes_positive,
        contrast_used=image.contrast_used,
        radiologist_id=image.radiologist_id,
        report_summary=report_summary
    )


@router.get("/imaging", response_model=List[ImagingDataResponse])
async def get_all_imaging(
    modality: Optional[str] = Query(None, description="Filter by imaging modality"),
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all imaging data with optional filters"""
    query = db.query(ImagingData)
    
    if modality:
        query = query.filter(ImagingData.imaging_modality == modality)
    
    if patient_id:
        query = query.filter(ImagingData.patient_id == patient_id)
    
    images = query.order_by(ImagingData.imaging_date.desc()).offset(skip).limit(limit).all()
    return images

