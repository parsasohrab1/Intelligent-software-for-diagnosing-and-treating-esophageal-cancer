"""
Data privacy endpoints for GDPR compliance (Right to be Forgotten)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.security.dependencies import get_current_user_with_role, require_role
from app.core.security.rbac import Role
from app.core.security.data_retention import DataRetentionPolicy
from app.models.user import User

router = APIRouter()


class DataDeletionRequest(BaseModel):
    """Request model for data deletion"""
    patient_id: str
    reason: str = "patient_request"
    anonymize_instead: bool = False  # If True, anonymize instead of deleting


class DataDeletionResponse(BaseModel):
    """Response model for data deletion"""
    patient_id: str
    status: str
    deleted_at: str
    reason: str
    tables_affected: list
    records_deleted: int
    error: Optional[str] = None


@router.post("/delete-patient-data", response_model=DataDeletionResponse, status_code=200)
async def delete_patient_data(
    request: DataDeletionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.SYSTEM_ADMINISTRATOR))
):
    """
    Delete all patient data (GDPR Right to be Forgotten)
    Requires SYSTEM_ADMINISTRATOR role
    
    This permanently deletes all patient data including:
    - Patient record
    - Clinical data
    - Lab results
    - Imaging data
    - Treatment data
    
    WARNING: This action is irreversible!
    """
    retention_policy = DataRetentionPolicy(db)
    
    if request.anonymize_instead:
        # Anonymize instead of deleting
        result = retention_policy.anonymize_patient_data(
            request.patient_id,
            keep_statistics=True
        )
        return DataDeletionResponse(
            patient_id=request.patient_id,
            status=result.get("status", "unknown"),
            deleted_at=result.get("anonymized_at", ""),
            reason=request.reason,
            tables_affected=result.get("tables_affected", []),
            records_deleted=0,
            error=result.get("error")
        )
    else:
        # Delete data
        result = retention_policy.delete_patient_data(
            request.patient_id,
            reason=request.reason,
            user_id=current_user.user_id
        )
        
        return DataDeletionResponse(
            patient_id=result["patient_id"],
            status=result["status"],
            deleted_at=result["deleted_at"],
            reason=result["reason"],
            tables_affected=result["tables_affected"],
            records_deleted=result["records_deleted"],
            error=result.get("error")
        )


@router.post("/cleanup-expired-data", response_model=dict)
async def cleanup_expired_data(
    dry_run: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.SYSTEM_ADMINISTRATOR))
):
    """
    Clean up data that has exceeded retention period (HIPAA 7-year requirement)
    Requires SYSTEM_ADMINISTRATOR role
    
    Args:
        dry_run: If True, only report what would be deleted without actually deleting
    """
    retention_policy = DataRetentionPolicy(db)
    summary = retention_policy.cleanup_expired_data(dry_run=dry_run)
    
    return summary


@router.get("/retention-policy", response_model=dict)
async def get_retention_policy(
    current_user: User = Depends(require_role(Role.SYSTEM_ADMINISTRATOR, Role.ETHICS_COMMITTEE))
):
    """
    Get current data retention policy settings
    """
    return {
        "patient_data_retention_days": DataRetentionPolicy.PATIENT_DATA_RETENTION_DAYS,
        "clinical_data_retention_days": DataRetentionPolicy.CLINICAL_DATA_RETENTION_DAYS,
        "lab_results_retention_days": DataRetentionPolicy.LAB_RESULTS_RETENTION_DAYS,
        "imaging_data_retention_days": DataRetentionPolicy.IMAGING_DATA_RETENTION_DAYS,
        "treatment_data_retention_days": DataRetentionPolicy.TREATMENT_DATA_RETENTION_DAYS,
        "audit_log_retention_days": DataRetentionPolicy.AUDIT_LOG_RETENTION_DAYS,
        "gdpr_deletion_immediate": DataRetentionPolicy.GDPR_DELETION_IMMEDIATE,
        "note": "Retention periods are set according to HIPAA requirements (7 years)"
    }

