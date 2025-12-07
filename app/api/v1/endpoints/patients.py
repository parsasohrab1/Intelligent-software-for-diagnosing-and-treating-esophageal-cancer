"""
Patient endpoints with HIPAA/GDPR compliant security
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.cache import CacheManager
from app.models.patient import Patient
from app.models.user import User
from app.schemas.patient import PatientResponse, PatientCreate
from app.core.security.dependencies import (
    get_current_user_with_role,
    check_patient_access,
    get_masked_patient_data,
    require_permission
)
from app.core.security.rbac import Permission
from app.core.security.data_masking import DataMasking
from app.core.security.consent_manager import ConsentManager, ConsentType

router = APIRouter()
cache_manager = CacheManager()
data_masking = DataMasking()


@router.get("/")
async def get_patients(
    skip: int = 0,
    limit: int = 10000,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.READ_DEIDENTIFIED))
):
    """Get list of patients"""
    import logging
    import traceback
    import time
    from datetime import datetime
    from sqlalchemy.exc import SQLAlchemyError, OperationalError, DisconnectionError
    
    start_time = time.time()
    logger = logging.getLogger(__name__)
    
    try:
        # Query database - optimized with limit
        # Reduce default limit if not specified to improve performance
        # Further reduce limit to prevent timeouts, but inform caller if truncated
        max_allowed_limit = 100
        effective_limit = min(limit, max_allowed_limit) if limit > max_allowed_limit else limit
        was_truncated = limit > max_allowed_limit
        patients = db.query(Patient).offset(skip).limit(effective_limit).all()
        
        query_time = time.time() - start_time
        if query_time > 1.0:
            logger.warning(f"Patient query took {query_time:.2f}s, returned {len(patients)} patients")
        
        if was_truncated:
            logger.warning(f"Patient query limit truncated from {limit} to {effective_limit} to prevent timeouts")
        
        # Convert to dict for response with data masking
        # Optimized: Use list comprehension and simplified datetime handling
        patient_list = []
        now_iso = datetime.now().isoformat()
        consent_manager = ConsentManager(db)
        
        for p in patients:
            try:
                # Optimized datetime conversion with better error handling
                try:
                    created_at_str = p.created_at.isoformat() if p.created_at and hasattr(p.created_at, 'isoformat') else now_iso
                except (AttributeError, ValueError, TypeError):
                    created_at_str = now_iso
                
                try:
                    updated_at_str = p.updated_at.isoformat() if p.updated_at and hasattr(p.updated_at, 'isoformat') else now_iso
                except (AttributeError, ValueError, TypeError):
                    updated_at_str = now_iso
                
                patient_dict = {
                    "patient_id": str(p.patient_id) if p.patient_id else "",
                    "age": int(p.age) if p.age is not None else 0,
                    "gender": str(p.gender) if p.gender else "",
                    "ethnicity": str(p.ethnicity) if p.ethnicity else None,
                    "has_cancer": bool(p.has_cancer) if p.has_cancer is not None else False,
                    "cancer_type": str(p.cancer_type) if p.cancer_type else None,
                    "cancer_subtype": str(p.cancer_subtype) if p.cancer_subtype else None,
                    "created_at": created_at_str,
                    "updated_at": updated_at_str,
                }
                
                # Apply data masking based on user role and consent
                has_consent = consent_manager.check_consent(
                    str(p.patient_id),
                    ConsentType.DATA_PROCESSING
                )
                masked_dict = data_masking.mask_patient_data(
                    patient_dict,
                    current_user.role,
                    has_consent
                )
                patient_list.append(masked_dict)
            except Exception as conv_err:
                # Reduced logging for performance - only log if critical
                logger.warning(f"Error converting patient {getattr(p, 'patient_id', 'unknown')}: {str(conv_err)}")
                continue
        
        total_time = time.time() - start_time
        if total_time > 1.0:
            logger.warning(f"get_patients took {total_time:.2f}s total (query: {query_time:.2f}s, conversion: {total_time - query_time:.2f}s)")
        
        # Always return consistent dict structure for API contract
        return {
            "patients": patient_list,
            "total_returned": len(patient_list),
            "requested_limit": limit,
            "effective_limit": effective_limit,
            "truncated": was_truncated,
            "message": f"Results limited to {effective_limit} records to prevent timeouts. Requested {limit} records." if was_truncated else None
        }
    except (OperationalError, DisconnectionError, SQLAlchemyError) as e:
        # Database connection/operation errors - return consistent structure
        logger.warning(f"Database error querying patients: {str(e)}")
        try:
            db.rollback()
        except Exception:
            pass
        return {
            "patients": [],
            "total_returned": 0,
            "requested_limit": limit,
            "effective_limit": effective_limit,
            "truncated": False,
            "message": "Database error occurred"
        }
    except Exception as e:
        # Any other error - log and return consistent structure
        logger.error(f"Error querying patients: {str(e)}")
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logger.error(traceback.format_exc())
        try:
            db.rollback()
        except Exception:
            pass
        return {
            "patients": [],
            "total_returned": 0,
            "requested_limit": limit,
            "effective_limit": effective_limit,
            "truncated": False,
            "message": "An error occurred while querying patients"
        }


@router.get("/{patient_id}")
async def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_role)
):
    """
    Get patient by ID with access control and data masking (HIPAA/GDPR compliant)
    """
    # Check access and get patient (includes access control and audit logging)
    patient = check_patient_access(patient_id, current_user, db)
    
    # Get masked patient data based on role and consent
    masked_data = get_masked_patient_data(patient, current_user, db)
    
    return masked_data


@router.post("/", status_code=201)
async def create_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WRITE_ALL))
):
    """Create a new patient"""
    import logging
    import traceback
    from datetime import datetime
    
    try:
        db_patient = Patient(**patient.dict())
        db.add(db_patient)
        db.commit()
        db.refresh(db_patient)
        
        # Convert to dict for response
        created_at_str = None
        if db_patient.created_at:
            if hasattr(db_patient.created_at, 'isoformat'):
                created_at_str = db_patient.created_at.isoformat()
            else:
                created_at_str = str(db_patient.created_at)
        else:
            created_at_str = datetime.now().isoformat()
        
        updated_at_str = None
        if db_patient.updated_at:
            if hasattr(db_patient.updated_at, 'isoformat'):
                updated_at_str = db_patient.updated_at.isoformat()
            else:
                updated_at_str = str(db_patient.updated_at)
        else:
            updated_at_str = datetime.now().isoformat()
        
        patient_dict = {
            "patient_id": str(db_patient.patient_id) if db_patient.patient_id else "",
            "age": int(db_patient.age) if db_patient.age is not None else 0,
            "gender": str(db_patient.gender) if db_patient.gender else "",
            "ethnicity": str(db_patient.ethnicity) if db_patient.ethnicity else None,
            "has_cancer": bool(db_patient.has_cancer) if db_patient.has_cancer is not None else False,
            "cancer_type": str(db_patient.cancer_type) if db_patient.cancer_type else None,
            "cancer_subtype": str(db_patient.cancer_subtype) if db_patient.cancer_subtype else None,
            "created_at": created_at_str,
            "updated_at": updated_at_str,
        }
        
        return patient_dict
    except Exception as e:
        logging.error(f"Error creating patient: {str(e)}")
        logging.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating patient: {str(e)}")


@router.post("/seed-data", status_code=200)
async def seed_dashboard_data(
    db: Session = Depends(get_db),
):
    """Quick endpoint to seed dashboard data (for development)"""
    import logging
    from app.services.synthetic_data_generator import EsophagealCancerSyntheticData
    from app.models.imaging_data import ImagingData
    
    logger = logging.getLogger(__name__)
    
    try:
        # Check existing data
        patient_count = db.query(Patient).count()
        mri_count = db.query(ImagingData).filter(ImagingData.imaging_modality == "MRI").count()
        
        if patient_count >= 10 and mri_count >= 10:
            return {
                "message": "Database already has sufficient data",
                "patients": patient_count,
                "mri_images": mri_count
            }
        
        logger.info("Generating data for dashboard...")
        
        # Generate data
        generator = EsophagealCancerSyntheticData(seed=42)
        dataset = generator.generate_all_data(n_patients=50, cancer_ratio=0.4)
        
        # Save to database
        generator.save_to_database(dataset, db)
        db.commit()
        
        # Verify
        new_patient_count = db.query(Patient).count()
        new_mri_count = db.query(ImagingData).filter(ImagingData.imaging_modality == "MRI").count()
        
        logger.info(f"Data generation completed: {new_patient_count} patients, {new_mri_count} MRI images")
        
        return {
            "message": "Data generated successfully",
            "patients": new_patient_count,
            "mri_images": new_mri_count
        }
    except Exception as e:
        logger.error(f"Error seeding data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error seeding data: {str(e)}")
