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
    # Metadata fields
    data_source: Optional[str] = None
    created_at: Optional[str] = None
    collected_at: Optional[str] = None
    generation_method: Optional[str] = None
    
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
    """Get MRI reports with patient information (optimized, no join required)"""
    import logging
    import traceback
    from sqlalchemy.exc import SQLAlchemyError, OperationalError, DisconnectionError
    
    logger = logging.getLogger(__name__)
    
    try:
        # Use simple query first - avoid join issues
        query = db.query(ImagingData).filter(ImagingData.imaging_modality == "MRI")
        
        if patient_id:
            query = query.filter(ImagingData.patient_id == patient_id)
        
        # Get total count for logging
        total_count = query.count()
        logger.info(f"Total MRI records found: {total_count}")
        
        # Get imaging records
        images = query.order_by(ImagingData.imaging_date.desc()).offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(images)} MRI images")
        
        if len(images) == 0:
            logger.warning(f"No MRI images found with filters: patient_id={patient_id}, skip={skip}, limit={limit}")
            return []
        
        # Build reports - fetch patient data separately if needed
        reports = []
        patient_cache = {}  # Cache patient lookups
        
        for image in images:
            try:
                patient_id_str = str(image.patient_id) if image.patient_id else "Unknown"
                
                # Get patient data if not cached
                patient = None
                if patient_id_str not in patient_cache:
                    try:
                        patient = db.query(Patient).filter(Patient.patient_id == patient_id_str).first()
                        patient_cache[patient_id_str] = patient
                    except Exception:
                        patient_cache[patient_id_str] = None
                else:
                    patient = patient_cache[patient_id_str]
                
                # Get all imaging data for this patient (for comprehensive report)
                all_imaging = db.query(ImagingData).filter(
                    ImagingData.patient_id == image.patient_id
                ).all()
                
                # Build comprehensive report
                report_parts = [f"MRI scan for patient {patient_id_str}"]
                
                # Add MRI findings
                if image.findings:
                    report_parts.append(f"MRI Findings: {image.findings[:200]}")
                if image.impression:
                    report_parts.append(f"MRI Impression: {image.impression[:200]}")
                
                # Add radiology data (CT, PET-CT, etc.)
                radiology_data = [img for img in all_imaging if img.imaging_modality in ["CT_Chest_Abdomen", "PET_CT", "EUS"]]
                if radiology_data:
                    for rad in radiology_data:
                        if rad.findings:
                            report_parts.append(f"{rad.imaging_modality} Findings: {rad.findings[:200]}")
                        if rad.impression:
                            report_parts.append(f"{rad.imaging_modality} Impression: {rad.impression[:200]}")
                
                # Add endoscopy data
                endoscopy_data = [img for img in all_imaging if img.imaging_modality == "Endoscopy"]
                if endoscopy_data:
                    for endo in endoscopy_data:
                        if endo.findings:
                            report_parts.append(f"Endoscopy Findings: {endo.findings[:200]}")
                        if endo.impression:
                            report_parts.append(f"Endoscopy Impression: {endo.impression[:200]}")
                
                report_summary = ". ".join(report_parts)
                
                # Handle datetime conversion safely
                imaging_date_str = None
                if image.imaging_date:
                    if hasattr(image.imaging_date, 'isoformat'):
                        imaging_date_str = image.imaging_date.isoformat()
                    else:
                        imaging_date_str = str(image.imaging_date)
                
                # Determine data source based on patient_id pattern
                is_synthetic = patient_id_str.startswith('CAN') or patient_id_str.startswith('NOR')
                data_source = "Synthetic" if is_synthetic else "Real"
                
                # Get creation/generation metadata
                from datetime import datetime
                created_at = None
                collected_at = None
                generation_method = None
                
                # Try to get creation timestamp from database record
                if hasattr(image, 'created_at') and image.created_at:
                    try:
                        if hasattr(image.created_at, 'isoformat'):
                            created_at = image.created_at.isoformat()
                        else:
                            created_at = str(image.created_at)
                    except:
                        pass
                
                # Determine collection/generation metadata
                if data_source == "Synthetic":
                    # For synthetic data, use imaging_date as creation date
                    collected_at = imaging_date_str
                    generation_method = "Synthetic Data Generator"
                    # Check if GAN-generated (image_id > 10000 suggests GAN expansion)
                    if image.image_id and image.image_id > 10000:
                        # Check if divisible pattern suggests GAN generation
                        base_id = image.image_id // 10000
                        remainder = image.image_id % 10000
                        if base_id > 0 and remainder < 100:
                            generation_method = "GAN-Generated"
                            # For GAN-generated, created_at is when it was generated
                            if not created_at:
                                created_at = datetime.now().isoformat()
                else:
                    # For real data, imaging_date is when it was collected
                    collected_at = imaging_date_str
                    generation_method = "Clinical Collection"
                    # Could be from online platforms (Kaggle, TCGA, etc.)
                    if patient_id_str and not (patient_id_str.startswith('CAN') or patient_id_str.startswith('NOR')):
                        # Real data collected from clinical sources or online platforms
                        generation_method = "Real Data (Collected from Clinical/Online Sources)"
                
                # If no created_at, use imaging_date or current time as fallback
                if not created_at:
                    created_at = imaging_date_str if imaging_date_str else datetime.now().isoformat()
                
                # Ensure collected_at is set
                if not collected_at:
                    collected_at = imaging_date_str if imaging_date_str else created_at
                
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
                    "report_summary": report_summary,
                    # Patient details
                    "patient_age": int(patient.age) if patient and patient.age is not None else None,
                    "patient_gender": str(patient.gender) if patient and patient.gender else None,
                    "patient_ethnicity": str(patient.ethnicity) if patient and patient.ethnicity else None,
                    "patient_has_cancer": bool(patient.has_cancer) if patient and patient.has_cancer is not None else None,
                    "patient_cancer_type": str(patient.cancer_type) if patient and patient.cancer_type else None,
                    "patient_cancer_subtype": str(patient.cancer_subtype) if patient and patient.cancer_subtype else None,
                    # Data metadata
                    "data_source": data_source,
                    "created_at": created_at,
                    "collected_at": collected_at,
                    "generation_method": generation_method,
                }
                reports.append(report_dict)
            except Exception as conv_err:
                logger.warning(f"Error converting MRI report for image_id {getattr(image, 'image_id', 'unknown')}: {str(conv_err)}")
                logger.warning(traceback.format_exc())
                continue
        
        logger.info(f"Successfully converted {len(reports)} MRI reports out of {len(images)} images")
        return reports
        
    except (SQLAlchemyError, OperationalError, DisconnectionError) as db_err:
        logger.error(f"Database error fetching MRI reports: {db_err}")
        logger.error(traceback.format_exc())
        return []
    except Exception as e:
        logger.error(f"Error fetching MRI reports: {str(e)}")
        logger.error(traceback.format_exc())
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


@router.get("/mri/{image_id}/image")
async def get_mri_image_visualization(
    image_id: int,
    db: Session = Depends(get_db),
    use_gan: bool = Query(True, description="Use GAN for image generation (falls back to geometric if GAN unavailable)")
):
    """Generate and return MRI image visualization using GAN or fallback method"""
    from fastapi.responses import Response
    import io
    import math
    import random
    
    # Try to use GAN first if requested
    if use_gan:
        try:
            from app.services.gan.mri_image_generator import get_gan_generator
            from app.core.config import settings
            from pathlib import Path
            
            # Try to load pre-trained model if available
            model_path = None
            if hasattr(settings, 'GAN_MODEL_PATH'):
                model_path = settings.GAN_MODEL_PATH
            else:
                # Default path
                default_path = Path('models/gan/final_model')
                if default_path.exists():
                    model_path = str(default_path)
            
            gan_gen = get_gan_generator(model_path=model_path)
            
            if gan_gen is not None:
                image = db.query(ImagingData).filter(
                    ImagingData.image_id == image_id,
                    ImagingData.imaging_modality == "MRI"
                ).first()
                
                if not image:
                    raise HTTPException(status_code=404, detail="MRI image not found")
                
                # Generate image using GAN
                imaging_date_str = str(image.imaging_date) if image.imaging_date else None
                gan_image = gan_gen.generate_with_annotations(
                    image_id=image_id,
                    patient_id=image.patient_id,
                    tumor_length_cm=image.tumor_length_cm,
                    wall_thickness_cm=image.wall_thickness_cm,
                    lymph_nodes_positive=image.lymph_nodes_positive,
                    contrast_used=image.contrast_used,
                    findings=image.findings,
                    impression=image.impression,
                    imaging_date=imaging_date_str
                )
                
                # Convert to bytes
                buffer = io.BytesIO()
                gan_image.save(buffer, format='PNG', optimize=True)
                img_bytes = buffer.getvalue()
                
                return Response(
                    content=img_bytes,
                    media_type="image/png",
                    headers={
                        "Content-Disposition": f"inline; filename=mri_{image_id}.png",
                        "Cache-Control": "public, max-age=3600",
                        "X-Image-Source": "GAN"
                    }
                )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"GAN generation failed, falling back to geometric method: {e}")
            # Fall through to geometric method
    
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise HTTPException(status_code=500, detail="PIL/Pillow not available for image generation")
    
    image = db.query(ImagingData).filter(
        ImagingData.image_id == image_id,
        ImagingData.imaging_modality == "MRI"
    ).first()
    
    if not image:
        raise HTTPException(status_code=404, detail="MRI image not found")
    
    # Generate medical-style image based on findings
    width, height = 1000, 700  # Larger for better clarity
    img = Image.new('RGB', (width, height), color='black')
    draw = ImageDraw.Draw(img)
    
    # Create gradient background (dark medical imaging style)
    for y in range(height):
        intensity = int(25 + (y / height) * 25)
        color = (intensity, intensity, intensity + 15)
        draw.line([(0, y), (width, y)], fill=color)
    
    # Draw anatomical structures (simplified esophagus cross-section)
    center_x, center_y = width // 2, height // 2 - 50
    
    # Outer wall (normal tissue)
    outer_radius = 180
    draw.ellipse(
        [center_x - outer_radius, center_y - outer_radius,
         center_x + outer_radius, center_y + outer_radius],
        outline='white', width=3, fill=None
    )
    
    # Inner lumen
    inner_radius = 100
    draw.ellipse(
        [center_x - inner_radius, center_y - inner_radius,
         center_x + inner_radius, center_y + inner_radius],
        outline='white', width=2, fill='black'
    )
    
    # Draw tumor if present
    if image.tumor_length_cm and image.tumor_length_cm > 0:
        tumor_size = min(int(image.tumor_length_cm * 20), 120)
        tumor_color = (255, 80, 80)  # Reddish for tumor
        # Draw irregular tumor shape
        tumor_points = []
        for angle in range(0, 360, 8):
            rad = math.radians(angle)
            radius_var = inner_radius + tumor_size + math.sin(angle * 4) * 15
            x = center_x + int(radius_var * math.cos(rad))
            y = center_y + int(radius_var * math.sin(rad))
            tumor_points.append((x, y))
        if len(tumor_points) > 2:
            draw.polygon(tumor_points, fill=tumor_color, outline='red', width=3)
            # Add tumor label
            draw.text((center_x + inner_radius + 20, center_y - 10), "TUMOR", fill='red', font=ImageFont.load_default())
    
    # Draw wall thickness if available
    if image.wall_thickness_cm and image.wall_thickness_cm > 0:
        thickness = int(image.wall_thickness_cm * 15)
        draw.ellipse(
            [center_x - inner_radius - thickness, center_y - inner_radius - thickness,
             center_x + inner_radius + thickness, center_y + inner_radius + thickness],
            outline='yellow', width=2, fill=None
        )
    
    # Add lymph nodes if positive
    if image.lymph_nodes_positive and image.lymph_nodes_positive > 0:
        node_count = min(image.lymph_nodes_positive, 10)
        for i in range(node_count):
            angle = (360 / node_count) * i + random.uniform(-10, 10)
            rad = math.radians(angle)
            node_x = center_x + int((outer_radius + 40) * math.cos(rad))
            node_y = center_y + int((outer_radius + 40) * math.sin(rad))
            draw.ellipse(
                [node_x - 10, node_y - 10, node_x + 10, node_y + 10],
                fill='orange', outline='red', width=2
            )
    
    # Add text annotations
    try:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Add header info
    header_y = 15
    draw.text((20, header_y), f"MRI SCAN #{image_id}", fill='white', font=font_large)
    header_y += 25
    
    if image.patient_id:
        draw.text((20, header_y), f"Patient ID: {image.patient_id}", fill='lightblue', font=font_small)
        header_y += 20
    
    if image.imaging_date:
        date_str = str(image.imaging_date)
        draw.text((20, header_y), f"Date: {date_str}", fill='lightblue', font=font_small)
        header_y += 20
    
    # Add measurements on right side
    measurements_x = width - 250
    measurements_y = 15
    draw.rectangle(
        [measurements_x - 10, measurements_y - 5, width - 10, measurements_y + 120],
        outline='white', width=1, fill=(20, 20, 30)
    )
    draw.text((measurements_x, measurements_y), "MEASUREMENTS", fill='yellow', font=font_small)
    measurements_y += 20
    
    if image.tumor_length_cm:
        draw.text((measurements_x, measurements_y), f"Tumor: {image.tumor_length_cm} cm", fill='red', font=font_small)
        measurements_y += 18
    if image.wall_thickness_cm:
        draw.text((measurements_x, measurements_y), f"Wall: {image.wall_thickness_cm} cm", fill='yellow', font=font_small)
        measurements_y += 18
    if image.lymph_nodes_positive:
        draw.text((measurements_x, measurements_y), f"Lymph Nodes: {image.lymph_nodes_positive}", fill='orange', font=font_small)
        measurements_y += 18
    if image.contrast_used:
        draw.text((measurements_x, measurements_y), "Contrast: Yes", fill='cyan', font=font_small)
    
    # Add findings and impression at bottom
    interpretation_y = height - 180
    if image.findings:
        draw.rectangle(
            [10, interpretation_y, width - 10, interpretation_y + 60],
            outline='white', width=1, fill=(10, 10, 20)
        )
        draw.text((15, interpretation_y + 5), "FINDINGS:", fill='yellow', font=font_small)
        # Wrap text
        findings_text = image.findings[:200] + "..." if len(image.findings) > 200 else image.findings
        words = findings_text.split()
        line = ""
        y_offset = interpretation_y + 22
        for word in words:
            test_line = line + word + " "
            if len(test_line) * 6 > width - 30:
                draw.text((15, y_offset), line, fill='white', font=font_small)
                line = word + " "
                y_offset += 16
            else:
                line = test_line
        if line:
            draw.text((15, y_offset), line, fill='white', font=font_small)
    
    if image.impression:
        impression_y = height - 100
        draw.rectangle(
            [10, impression_y, width - 10, height - 10],
            outline='cyan', width=1, fill=(5, 15, 25)
        )
        draw.text((15, impression_y + 5), "IMPRESSION:", fill='cyan', font=font_small)
        # Wrap text
        impression_text = image.impression[:200] + "..." if len(image.impression) > 200 else image.impression
        words = impression_text.split()
        line = ""
        y_offset = impression_y + 22
        for word in words:
            test_line = line + word + " "
            if len(test_line) * 6 > width - 30:
                draw.text((15, y_offset), line, fill='lightcyan', font=font_small)
                line = word + " "
                y_offset += 16
            else:
                line = test_line
        if line:
            draw.text((15, y_offset), line, fill='lightcyan', font=font_small)
    
    # Convert to PNG
    buffer = io.BytesIO()
    img.save(buffer, format='PNG', optimize=True)
    img_bytes = buffer.getvalue()
    
    return Response(
        content=img_bytes,
        media_type="image/png",
        headers={
            "Content-Disposition": f"inline; filename=mri_{image_id}.png",
            "Cache-Control": "public, max-age=3600",
            "X-Image-Source": "Geometric"
        }
    )


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
    
    # Generate comprehensive report summary including radiology and endoscopy
    report_parts = []
    
    # Add MRI findings
    if image.findings:
        report_parts.append(f"MRI Findings: {image.findings}")
    if image.impression:
        report_parts.append(f"MRI Impression: {image.impression}")
    if image.tumor_length_cm:
        report_parts.append(f"MRI Tumor length: {image.tumor_length_cm} cm")
    if image.wall_thickness_cm:
        report_parts.append(f"MRI Wall thickness: {image.wall_thickness_cm} cm")
    if image.lymph_nodes_positive is not None:
        report_parts.append(f"MRI Lymph nodes positive: {image.lymph_nodes_positive}")
    
    # Get all imaging data for this patient (radiology and endoscopy)
    all_imaging = db.query(ImagingData).filter(
        ImagingData.patient_id == image.patient_id
    ).all()
    
    # Add radiology data (CT, PET-CT, etc.)
    radiology_data = [img for img in all_imaging if img.imaging_modality in ["CT_Chest_Abdomen", "PET_CT", "EUS"]]
    if radiology_data:
        for rad in radiology_data:
            if rad.findings:
                report_parts.append(f"{rad.imaging_modality} Findings: {rad.findings}")
            if rad.impression:
                report_parts.append(f"{rad.imaging_modality} Impression: {rad.impression}")
            if rad.tumor_length_cm:
                report_parts.append(f"{rad.imaging_modality} Tumor length: {rad.tumor_length_cm} cm")
    
    # Add endoscopy data
    endoscopy_data = [img for img in all_imaging if img.imaging_modality == "Endoscopy"]
    if endoscopy_data:
        for endo in endoscopy_data:
            if endo.findings:
                report_parts.append(f"Endoscopy Findings: {endo.findings}")
            if endo.impression:
                report_parts.append(f"Endoscopy Impression: {endo.impression}")
            if endo.tumor_length_cm:
                report_parts.append(f"Endoscopy Tumor length: {endo.tumor_length_cm} cm")
    
    report_summary = ". ".join(report_parts) if report_parts else "No detailed findings available"
    
    # Add metadata for single report endpoint
    from datetime import datetime
    is_synthetic = str(image.patient_id).startswith('CAN') or str(image.patient_id).startswith('NOR')
    data_source = "Synthetic" if is_synthetic else "Real"
    
    created_at = None
    collected_at = None
    generation_method = None
    
    if hasattr(image, 'created_at') and image.created_at:
        try:
            if hasattr(image.created_at, 'isoformat'):
                created_at = image.created_at.isoformat()
            else:
                created_at = str(image.created_at)
        except:
            pass
    
    imaging_date_str = image.imaging_date.isoformat() if image.imaging_date and hasattr(image.imaging_date, 'isoformat') else (str(image.imaging_date) if image.imaging_date else None)
    
    if data_source == "Synthetic":
        collected_at = imaging_date_str
        generation_method = "Synthetic Data Generator"
        if image.image_id and image.image_id > 10000:
            base_id = image.image_id // 10000
            remainder = image.image_id % 10000
            if base_id > 0 and remainder < 100:
                generation_method = "GAN-Generated"
    else:
        collected_at = imaging_date_str
        generation_method = "Clinical Collection"
    
    if not created_at:
        created_at = imaging_date_str if imaging_date_str else datetime.now().isoformat()
    if not collected_at:
        collected_at = imaging_date_str if imaging_date_str else created_at
    
    # Return with metadata
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
        report_summary=report_summary,
        # Metadata
        data_source=data_source,
        created_at=created_at,
        collected_at=collected_at,
        generation_method=generation_method,
    )


@router.get("/stats")
async def get_imaging_stats(db: Session = Depends(get_db)):
    """Get statistics about imaging data in database"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get all imaging records first to see what we have
        all_imaging = db.query(ImagingData).all()
        total_count = len(all_imaging)
        
        # Count by modality
        mri_count = db.query(ImagingData).filter(ImagingData.imaging_modality == "MRI").count()
        endoscopy_count = db.query(ImagingData).filter(ImagingData.imaging_modality == "Endoscopy").count()
        ct_count = db.query(ImagingData).filter(ImagingData.imaging_modality == "CT_Chest_Abdomen").count()
        pet_count = db.query(ImagingData).filter(ImagingData.imaging_modality == "PET_CT").count()
        eus_count = db.query(ImagingData).filter(ImagingData.imaging_modality == "EUS").count()
        
        # Get unique modalities to see what's actually in the database
        unique_modalities = db.query(ImagingData.imaging_modality).distinct().all()
        modality_list = [mod[0] for mod in unique_modalities] if unique_modalities else []
        
        # Get sample MRI records
        sample_mri = db.query(ImagingData).filter(ImagingData.imaging_modality == "MRI").limit(5).all()
        sample_ids = [img.image_id for img in sample_mri]
        
        # Get sample of all imaging to see what modalities exist
        sample_all = db.query(ImagingData).limit(10).all()
        sample_modalities = [img.imaging_modality for img in sample_all]
        
        logger.info(f"Imaging stats: Total={total_count}, MRI={mri_count}, Endoscopy={endoscopy_count}, CT={ct_count}, PET={pet_count}, EUS={eus_count}")
        logger.info(f"Unique modalities in DB: {modality_list}")
        
        return {
            "total_imaging_records": total_count,
            "mri_count": mri_count,
            "endoscopy_count": endoscopy_count,
            "ct_count": ct_count,
            "pet_count": pet_count,
            "eus_count": eus_count,
            "unique_modalities": modality_list,
            "sample_mri_ids": sample_ids,
            "sample_modalities": sample_modalities[:10],  # First 10 modalities
        }
    except Exception as e:
        logger.error(f"Error getting imaging stats: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "error": str(e),
            "total_imaging_records": 0,
            "mri_count": 0,
            "unique_modalities": [],
        }


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

