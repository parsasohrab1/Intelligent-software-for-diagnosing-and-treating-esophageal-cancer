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


@router.get("/mri")
async def get_mri_images(
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10000, ge=1, le=50000),
    db: Session = Depends(get_db)
):
    """Get all MRI images"""
    import logging
    import traceback
    from sqlalchemy.exc import SQLAlchemyError, OperationalError, DisconnectionError
    
    try:
        query = db.query(ImagingData).filter(ImagingData.imaging_modality == "MRI")
        
        if patient_id:
            query = query.filter(ImagingData.patient_id == patient_id)
        
        images = query.order_by(ImagingData.imaging_date.desc()).offset(skip).limit(limit).all()
        
        # Convert to dict for response
        image_list = []
        for img in images:
            try:
                image_dict = {
                    "image_id": int(img.image_id) if img.image_id is not None else 0,
                    "patient_id": str(img.patient_id) if img.patient_id else "",
                    "imaging_modality": str(img.imaging_modality) if img.imaging_modality else "",
                    "findings": str(img.findings) if img.findings else None,
                    "impression": str(img.impression) if img.impression else None,
                    "tumor_length_cm": float(img.tumor_length_cm) if img.tumor_length_cm is not None else None,
                    "wall_thickness_cm": float(img.wall_thickness_cm) if img.wall_thickness_cm is not None else None,
                    "lymph_nodes_positive": int(img.lymph_nodes_positive) if img.lymph_nodes_positive is not None else 0,
                    "contrast_used": bool(img.contrast_used) if img.contrast_used is not None else False,
                    "radiologist_id": str(img.radiologist_id) if img.radiologist_id else None,
                    "imaging_date": img.imaging_date.isoformat() if img.imaging_date and hasattr(img.imaging_date, 'isoformat') else (str(img.imaging_date) if img.imaging_date else None),
                }
                image_list.append(image_dict)
            except Exception as conv_err:
                logging.warning(f"Error converting image {img.image_id}: {str(conv_err)}")
                logging.warning(traceback.format_exc())
                continue
        
        return image_list
    except (OperationalError, DisconnectionError, SQLAlchemyError) as e:
        # Database connection/operation errors - return empty list
        logging.warning(f"Database error fetching MRI images: {str(e)}")
        try:
            db.rollback()
        except Exception:
            pass
        return []
    except Exception as e:
        # Any other error - log and return empty list
        logging.error(f"Error fetching MRI images: {str(e)}")
        logging.error(traceback.format_exc())
        try:
            db.rollback()
        except Exception:
            pass
        return []


@router.get("/mri/reports")
async def get_mri_reports(
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10000, ge=1, le=50000),
    db: Session = Depends(get_db)
):
    """Get MRI reports with patient information"""
    import logging
    import traceback
    from sqlalchemy.exc import SQLAlchemyError, OperationalError, DisconnectionError
    
    logger = logging.getLogger(__name__)
    
    try:
        # Build query with proper error handling - use left outer join to handle missing patients
        try:
            # Use outerjoin to handle cases where patient might not exist
            query = db.query(ImagingData, Patient).outerjoin(
                Patient, ImagingData.patient_id == Patient.patient_id
            ).filter(ImagingData.imaging_modality == "MRI")
            
            if patient_id:
                query = query.filter(ImagingData.patient_id == patient_id)
            
            results = query.order_by(ImagingData.imaging_date.desc()).offset(skip).limit(limit).all()
        except (SQLAlchemyError, OperationalError, DisconnectionError) as db_err:
            logger.error(f"Database error in MRI reports query: {db_err}")
            logger.error(traceback.format_exc())
            return []
        except Exception as query_err:
            logger.error(f"Query error in MRI reports: {query_err}")
            logger.error(traceback.format_exc())
            return []
        
        reports = []
        for result in results:
            try:
                # Handle both tuple and single object results
                if isinstance(result, tuple):
                    image, patient = result
                else:
                    image = result
                    patient = None
                
                # Generate report summary
                patient_id_str = str(image.patient_id) if image.patient_id else "Unknown"
                report_summary = f"MRI scan for patient {patient_id_str}"
                if image.findings:
                    report_summary += f". Findings: {image.findings[:100]}"
                if image.impression:
                    report_summary += f". Impression: {image.impression}"
                
                # Handle datetime conversion safely
                imaging_date_str = None
                if image.imaging_date:
                    if hasattr(image.imaging_date, 'isoformat'):
                        imaging_date_str = image.imaging_date.isoformat()
                    else:
                        imaging_date_str = str(image.imaging_date)
                
                report_dict = {
                    "image_id": int(image.image_id) if image.image_id is not None else 0,
                    "patient_id": patient_id_str,
                    "patient_name": getattr(patient, 'name', None) if patient else None,
                    "imaging_date": imaging_date_str,
                    "findings": str(image.findings) if image.findings else None,
                    "impression": str(image.impression) if image.impression else None,
                    "tumor_length_cm": float(image.tumor_length_cm) if image.tumor_length_cm is not None else None,
                    "wall_thickness_cm": float(image.wall_thickness_cm) if image.wall_thickness_cm is not None else None,
                    "lymph_nodes_positive": int(image.lymph_nodes_positive) if image.lymph_nodes_positive is not None else 0,
                    "contrast_used": bool(image.contrast_used) if image.contrast_used is not None else False,
                    "radiologist_id": str(image.radiologist_id) if image.radiologist_id else None,
                    "report_summary": report_summary
                }
                reports.append(report_dict)
            except Exception as conv_err:
                logger.warning(f"Error converting MRI report: {str(conv_err)}")
                logger.warning(traceback.format_exc())
                continue
        
        return reports
    except Exception as e:
        logger.error(f"Error fetching MRI reports: {str(e)}")
        logger.error(traceback.format_exc())
        # Return empty list instead of raising exception to avoid 422
        return []


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

