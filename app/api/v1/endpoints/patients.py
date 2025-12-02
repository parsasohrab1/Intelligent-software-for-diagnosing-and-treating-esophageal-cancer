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
    # Generate cache key
    cache_key = cache_manager.generate_key("patients", "list", skip=skip, limit=limit)
    
    # Try to get from cache
    cached_patients = cache_manager.get(cache_key)
    if cached_patients is not None:
        return cached_patients
    
    # Query database
    patients = db.query(Patient).offset(skip).limit(limit).all()
    
    # Cache for 5 minutes
    cache_manager.set(cache_key, patients, ttl=300)
    
    return patients


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: str, db: Session = Depends(get_db)):
    """Get patient by ID with caching"""
    # Generate cache key
    cache_key = cache_manager.generate_key("patients", "by_id", patient_id=patient_id)
    
    # Try to get from cache
    cached_patient = cache_manager.get(cache_key)
    if cached_patient is not None:
        return cached_patient
    
    # Query database
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Cache for 10 minutes
    cache_manager.set(cache_key, patient, ttl=600)
    
    return patient


@router.post("/", response_model=PatientResponse, status_code=201)
async def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    """Create a new patient"""
    db_patient = Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

