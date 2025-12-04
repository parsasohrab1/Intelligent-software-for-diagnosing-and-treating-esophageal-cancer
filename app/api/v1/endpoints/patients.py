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
    from datetime import datetime
    from sqlalchemy.exc import SQLAlchemyError, OperationalError, DisconnectionError
    
    try:
        # Query database
        patients = db.query(Patient).offset(skip).limit(limit).all()
        
        # Convert to dict for response (avoid Pydantic serialization issues)
        patient_list = []
        for p in patients:
            try:
                # Handle datetime conversion safely
                created_at_str = None
                if p.created_at:
                    if hasattr(p.created_at, 'isoformat'):
                        created_at_str = p.created_at.isoformat()
                    else:
                        created_at_str = str(p.created_at)
                else:
                    created_at_str = datetime.now().isoformat()
                
                updated_at_str = None
                if p.updated_at:
                    if hasattr(p.updated_at, 'isoformat'):
                        updated_at_str = p.updated_at.isoformat()
                    else:
                        updated_at_str = str(p.updated_at)
                else:
                    updated_at_str = datetime.now().isoformat()
                
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
                logging.warning(f"Error converting patient {p.patient_id}: {str(conv_err)}")
                logging.warning(traceback.format_exc())
                continue
        
        return patient_list
    except (OperationalError, DisconnectionError, SQLAlchemyError) as e:
        # Database connection/operation errors - return empty list
        logging.warning(f"Database error querying patients: {str(e)}")
        try:
            db.rollback()
        except Exception:
            pass
        return []
    except Exception as e:
        # Any other error - log and return empty list
        logging.error(f"Error querying patients: {str(e)}")
        logging.error(traceback.format_exc())
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

