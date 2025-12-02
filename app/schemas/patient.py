"""
Patient schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PatientBase(BaseModel):
    """Base patient schema"""
    age: int
    gender: str
    ethnicity: Optional[str] = None
    has_cancer: bool = False
    cancer_type: Optional[str] = None
    cancer_subtype: Optional[str] = None


class PatientCreate(PatientBase):
    """Schema for creating a patient"""
    patient_id: str


class PatientResponse(PatientBase):
    """Schema for patient response"""
    patient_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

