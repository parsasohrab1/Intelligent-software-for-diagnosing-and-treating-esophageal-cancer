"""
Patient endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.cache import CacheManager
from app.models.patient import Patient
from app.schemas.patient import PatientResponse, PatientCreate

router = APIRouter()
cache_manager = CacheManager()


@router.get("/")
async def get_patients(
    skip: int = 0, limit: int = 10000, db: Session = Depends(get_db)
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
        # Further reduce limit to prevent timeouts
        effective_limit = min(limit, 100) if limit > 100 else limit
        patients = db.query(Patient).offset(skip).limit(effective_limit).all()
        
        query_time = time.time() - start_time
        if query_time > 1.0:
            logger.warning(f"Patient query took {query_time:.2f}s, returned {len(patients)} patients")
        
        # Convert to dict for response (avoid Pydantic serialization issues)
        # Optimized: Use list comprehension and simplified datetime handling
        patient_list = []
        now_iso = datetime.now().isoformat()
        
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
                patient_list.append(patient_dict)
            except Exception as conv_err:
                # Reduced logging for performance - only log if critical
                logger.warning(f"Error converting patient {getattr(p, 'patient_id', 'unknown')}: {str(conv_err)}")
                continue
        
        total_time = time.time() - start_time
        if total_time > 1.0:
            logger.warning(f"get_patients took {total_time:.2f}s total (query: {query_time:.2f}s, conversion: {total_time - query_time:.2f}s)")
        
        return patient_list
    except (OperationalError, DisconnectionError, SQLAlchemyError) as e:
        # Database connection/operation errors - return empty list
        logger.warning(f"Database error querying patients: {str(e)}")
        try:
            db.rollback()
        except Exception:
            pass
        return []
    except Exception as e:
        # Any other error - log and return empty list
        logger.error(f"Error querying patients: {str(e)}")
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logger.error(traceback.format_exc())
        try:
            db.rollback()
        except Exception:
            pass
        return []


@router.get("/{patient_id}")
async def get_patient(patient_id: str, db: Session = Depends(get_db)):
    """Get patient by ID"""
    import logging
    import traceback
    from datetime import datetime
    
    try:
        # Query database
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Convert to dict for response
        created_at_str = None
        if patient.created_at:
            if hasattr(patient.created_at, 'isoformat'):
                created_at_str = patient.created_at.isoformat()
            else:
                created_at_str = str(patient.created_at)
        else:
            created_at_str = datetime.now().isoformat()
        
        updated_at_str = None
        if patient.updated_at:
            if hasattr(patient.updated_at, 'isoformat'):
                updated_at_str = patient.updated_at.isoformat()
            else:
                updated_at_str = str(patient.updated_at)
        else:
            updated_at_str = datetime.now().isoformat()
        
        patient_dict = {
            "patient_id": str(patient.patient_id) if patient.patient_id else "",
            "age": int(patient.age) if patient.age is not None else 0,
            "gender": str(patient.gender) if patient.gender else "",
            "ethnicity": str(patient.ethnicity) if patient.ethnicity else None,
            "has_cancer": bool(patient.has_cancer) if patient.has_cancer is not None else False,
            "cancer_type": str(patient.cancer_type) if patient.cancer_type else None,
            "cancer_subtype": str(patient.cancer_subtype) if patient.cancer_subtype else None,
            "created_at": created_at_str,
            "updated_at": updated_at_str,
        }
        
        return patient_dict
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching patient {patient_id}: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error fetching patient: {str(e)}")


@router.post("/", status_code=201)
async def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
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

