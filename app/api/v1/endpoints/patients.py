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


@router.get("/", response_model=List[PatientResponse])
async def get_patients(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """Get list of patients with caching"""
    cache_key = None
    try:
        # Generate cache key
        cache_key = cache_manager.generate_key("patients", "list", skip=skip, limit=limit)
        
        # Try to get from cache (if Redis is available)
        cached_patients = cache_manager.get(cache_key)
        if cached_patients is not None:
            # Convert cached dicts back to PatientResponse objects
            return [PatientResponse(**p) if isinstance(p, dict) else p for p in cached_patients]
    except Exception:
        # If cache fails, continue without cache
        pass
    
    # Query database
    try:
        patients = db.query(Patient).offset(skip).limit(limit).all()
    except Exception as e:
        # If database is not available, return empty list
        import psycopg2
        error_orig = getattr(e, 'orig', None)
        if error_orig and isinstance(error_orig, psycopg2.OperationalError):
            return []
        # Check if it's a connection error
        error_str = str(e).lower()
        if 'connection' in error_str or 'refused' in error_str or 'operationalerror' in error_str:
            return []
        # For other errors, log and return empty list
        import logging
        logging.error(f"Error querying patients: {str(e)}")
        return []
    
    # Convert to Pydantic models for response (Pydantic v2 uses model_validate)
    patient_responses = []
    for p in patients:
        try:
            # Try Pydantic v2 model_validate first
            if hasattr(PatientResponse, 'model_validate'):
                patient_responses.append(PatientResponse.model_validate(p))
            else:
                # Fallback to Pydantic v1
                patient_responses.append(PatientResponse(
                    patient_id=p.patient_id,
                    age=p.age,
                    gender=p.gender,
                    ethnicity=p.ethnicity,
                    has_cancer=p.has_cancer,
                    cancer_type=p.cancer_type,
                    cancer_subtype=p.cancer_subtype,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                ))
        except Exception as conv_err:
            import logging
            logging.warning(f"Error converting patient {p.patient_id}: {str(conv_err)}")
            # Try manual conversion as last resort
            try:
                patient_responses.append(PatientResponse(
                    patient_id=str(p.patient_id) if p.patient_id else "",
                    age=int(p.age) if p.age else 0,
                    gender=str(p.gender) if p.gender else "",
                    ethnicity=str(p.ethnicity) if p.ethnicity else "",
                    has_cancer=bool(p.has_cancer) if p.has_cancer is not None else False,
                    cancer_type=str(p.cancer_type) if p.cancer_type else None,
                    cancer_subtype=str(p.cancer_subtype) if p.cancer_subtype else None,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                ))
            except Exception as final_err:
                logging.error(f"Final conversion error for patient {p.patient_id}: {str(final_err)}")
                continue
    
    # Try to cache (if Redis is available) - cache as dicts
    if cache_key:
        try:
            # Convert to dict for caching (Pydantic v2 uses model_dump)
            try:
                cache_data = [p.model_dump() if hasattr(p, 'model_dump') else p.dict() for p in patient_responses]
            except AttributeError:
                # Fallback for Pydantic v1
                cache_data = [p.dict() for p in patient_responses]
            cache_manager.set(cache_key, cache_data, ttl=300)
        except Exception:
            # If cache fails, continue without cache
            pass
    
    return patient_responses


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: str, db: Session = Depends(get_db)):
    """Get patient by ID with caching"""
    try:
        # Generate cache key
        cache_key = cache_manager.generate_key("patients", "by_id", patient_id=patient_id)
        
        # Try to get from cache (if Redis is available)
        cached_patient = cache_manager.get(cache_key)
        if cached_patient is not None:
            return cached_patient
    except Exception:
        # If cache fails, continue without cache
        pass
    
    # Query database
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Try to cache (if Redis is available)
    try:
        cache_manager.set(cache_key, patient, ttl=600)
    except Exception:
        # If cache fails, continue without cache
        pass
    
    return patient


@router.post("/", response_model=PatientResponse, status_code=201)
async def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    """Create a new patient"""
    db_patient = Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

