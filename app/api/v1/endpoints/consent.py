"""
Consent management endpoints for HIPAA/GDPR compliance
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security.dependencies import get_current_user_with_role, require_permission, require_role
from app.core.security.rbac import Permission, Role
from app.core.security.consent_manager import ConsentManager, ConsentType, ConsentStatus
from app.models.user import User

router = APIRouter()


class ConsentRequest(BaseModel):
    """Request model for granting consent"""
    patient_id: str
    consent_type: ConsentType
    purpose: Optional[str] = None
    scope: Optional[str] = None
    expires_in_days: Optional[int] = None


class ConsentResponse(BaseModel):
    """Response model for consent"""
    consent_id: str
    patient_id: str
    consent_type: ConsentType
    status: ConsentStatus
    granted: bool
    granted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    purpose: Optional[str] = None
    scope: Optional[str] = None


@router.post("/grant", response_model=ConsentResponse, status_code=201)
async def grant_consent(
    request: ConsentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WRITE_ALL))
):
    """
    Grant consent for patient data access (HIPAA/GDPR compliant)
    Requires WRITE_ALL permission
    """
    consent_manager = ConsentManager(db)
    
    consent = consent_manager.grant_consent(
        patient_id=request.patient_id,
        consent_type=request.consent_type,
        purpose=request.purpose,
        scope=request.scope,
        expires_in_days=request.expires_in_days
    )
    
    return ConsentResponse(
        consent_id=consent.consent_id,
        patient_id=consent.patient_id,
        consent_type=consent.consent_type,
        status=consent.status,
        granted=consent.granted,
        granted_at=consent.granted_at,
        expires_at=consent.expires_at,
        purpose=consent.purpose,
        scope=consent.scope
    )


@router.post("/withdraw", status_code=200)
async def withdraw_consent(
    patient_id: str,
    consent_type: ConsentType,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WRITE_ALL))
):
    """
    Withdraw consent for patient data access
    Requires WRITE_ALL permission
    """
    consent_manager = ConsentManager(db)
    
    success = consent_manager.withdraw_consent(patient_id, consent_type)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"No active consent found for patient {patient_id} and type {consent_type.value}"
        )
    
    return {"message": "Consent withdrawn successfully", "patient_id": patient_id, "consent_type": consent_type.value}


@router.get("/check/{patient_id}", response_model=dict)
async def check_consent(
    patient_id: str,
    consent_type: ConsentType,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.READ_DEIDENTIFIED))
):
    """
    Check if patient has valid consent
    """
    consent_manager = ConsentManager(db)
    has_consent = consent_manager.check_consent(patient_id, consent_type)
    
    return {
        "patient_id": patient_id,
        "consent_type": consent_type.value,
        "has_consent": has_consent
    }


@router.get("/patient/{patient_id}", response_model=List[ConsentResponse])
async def get_patient_consents(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.READ_DEIDENTIFIED))
):
    """
    Get all consents for a patient
    """
    consent_manager = ConsentManager(db)
    consents = consent_manager.get_patient_consents(patient_id)
    
    return [
        ConsentResponse(
            consent_id=c.consent_id,
            patient_id=c.patient_id,
            consent_type=c.consent_type,
            status=c.status,
            granted=c.granted,
            granted_at=c.granted_at,
            expires_at=c.expires_at,
            purpose=c.purpose,
            scope=c.scope
        )
        for c in consents
    ]


@router.post("/expire-old", response_model=dict)
async def expire_old_consents(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.SYSTEM_ADMINISTRATOR))
):
    """
    Expire consents that have passed their expiration date
    Requires SYSTEM_ADMINISTRATOR role
    """
    consent_manager = ConsentManager(db)
    count = consent_manager.expire_old_consents()
    
    return {
        "message": f"Expired {count} consent(s)",
        "expired_count": count
    }

