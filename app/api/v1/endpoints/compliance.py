"""
Regulatory Compliance API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import date

from app.core.database import get_db
from app.core.security.dependencies import get_current_user_with_role, require_role
from app.core.security.rbac import Role
from app.core.compliance.regulatory_tracking import (
    RegulatoryTracker,
    RegulatoryStandard,
    ComplianceStatus
)
from app.core.compliance.validation_documentation import (
    ValidationDocumentation,
    ValidationType,
    ValidationStatus
)
from app.core.compliance.quality_assurance import (
    QualityAssurance,
    QADocumentType,
    AuditType
)
from app.core.compliance.risk_management import (
    RiskManagement,
    RiskCategory,
    SeverityLevel,
    ProbabilityLevel
)
from app.core.compliance.change_control import (
    ChangeControl,
    ChangeType,
    ChangePriority
)
from app.core.compliance.software_lifecycle import (
    SoftwareLifecycle,
    SoftwareSafetyClass,
    LifecyclePhase
)
from app.models.user import User

router = APIRouter()


# ========== Regulatory Tracking ==========

class RegulatorySubmissionRequest(BaseModel):
    standard: RegulatoryStandard
    submission_number: Optional[str] = None
    regulatory_body: Optional[str] = None


@router.post("/regulatory/submissions", status_code=201)
async def create_regulatory_submission(
    request: RegulatorySubmissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.SYSTEM_ADMINISTRATOR))
):
    """ایجاد ارسال نظارتی جدید"""
    tracker = RegulatoryTracker(db)
    submission = tracker.create_submission(
        standard=request.standard,
        submission_number=request.submission_number,
        regulatory_body=request.regulatory_body
    )
    return {"submission_id": submission.submission_id, "status": submission.status.value}


@router.get("/regulatory/submissions/{submission_id}")
async def get_submission_status(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_role)
):
    """دریافت وضعیت ارسال نظارتی"""
    tracker = RegulatoryTracker(db)
    status = tracker.get_submission_status(submission_id)
    return status


@router.get("/regulatory/compliance-summary")
async def get_compliance_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_role)
):
    """خلاصه وضعیت انطباق"""
    tracker = RegulatoryTracker(db)
    summary = tracker.get_compliance_summary()
    return summary


# ========== Validation Documentation ==========

class ValidationProtocolRequest(BaseModel):
    validation_type: ValidationType
    title: str
    objective: Optional[str] = None
    scope: Optional[str] = None
    acceptance_criteria: Optional[str] = None


@router.post("/validation/protocols", status_code=201)
async def create_validation_protocol(
    request: ValidationProtocolRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.SYSTEM_ADMINISTRATOR))
):
    """ایجاد پروتکل اعتبارسنجی"""
    validation = ValidationDocumentation(db)
    protocol = validation.create_protocol(
        validation_type=request.validation_type,
        title=request.title,
        objective=request.objective,
        scope=request.scope,
        acceptance_criteria=request.acceptance_criteria
    )
    return {"protocol_id": protocol.protocol_id, "status": protocol.status.value}


@router.get("/validation/protocols/{protocol_id}")
async def get_protocol_summary(
    protocol_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_role)
):
    """خلاصه پروتکل اعتبارسنجی"""
    validation = ValidationDocumentation(db)
    summary = validation.get_protocol_summary(protocol_id)
    return summary


# ========== Quality Assurance ==========

@router.get("/quality/metrics")
async def get_quality_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_role)
):
    """دریافت معیارهای کیفیت"""
    qa = QualityAssurance(db)
    metrics = qa.get_quality_metrics()
    return metrics


# ========== Risk Management ==========

class RiskRequest(BaseModel):
    risk_number: str
    title: str
    category: RiskCategory
    severity: SeverityLevel
    probability: ProbabilityLevel
    description: Optional[str] = None


@router.post("/risk/risks", status_code=201)
async def create_risk(
    request: RiskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.SYSTEM_ADMINISTRATOR))
):
    """ایجاد ریسک"""
    risk_mgmt = RiskManagement(db)
    risk = risk_mgmt.create_risk(
        risk_number=request.risk_number,
        title=request.title,
        category=request.category,
        severity=request.severity,
        probability=request.probability,
        description=request.description
    )
    return {
        "risk_id": risk.risk_id,
        "risk_score": risk.risk_score,
        "risk_level": risk.initial_risk_level
    }


@router.get("/risk/summary")
async def get_risk_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_role)
):
    """خلاصه ریسک‌ها"""
    risk_mgmt = RiskManagement(db)
    summary = risk_mgmt.get_risk_summary()
    return summary


# ========== Change Control ==========

class ChangeRequestModel(BaseModel):
    change_number: str
    change_type: ChangeType
    priority: ChangePriority
    title: str
    description: Optional[str] = None


@router.post("/change-control/requests", status_code=201)
async def create_change_request(
    request: ChangeRequestModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_role)
):
    """ایجاد درخواست تغییر"""
    change_control = ChangeControl(db)
    change = change_control.create_change_request(
        change_number=request.change_number,
        change_type=request.change_type,
        priority=request.priority,
        title=request.title,
        description=request.description,
        requested_by=current_user.username
    )
    return {"change_id": change.change_id, "status": change.status.value}


@router.get("/change-control/summary")
async def get_change_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_role)
):
    """خلاصه تغییرات"""
    change_control = ChangeControl(db)
    summary = change_control.get_change_summary()
    return summary


# ========== Software Lifecycle ==========

class SoftwareItemRequest(BaseModel):
    item_name: str
    item_version: str
    safety_class: SoftwareSafetyClass
    description: Optional[str] = None


@router.post("/software-lifecycle/items", status_code=201)
async def create_software_item(
    request: SoftwareItemRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.SYSTEM_ADMINISTRATOR))
):
    """ایجاد آیتم نرم‌افزاری"""
    lifecycle = SoftwareLifecycle(db)
    item = lifecycle.create_software_item(
        item_name=request.item_name,
        item_version=request.item_version,
        safety_class=request.safety_class,
        description=request.description
    )
    return {"item_id": item.item_id, "current_phase": item.current_phase.value}


@router.get("/software-lifecycle/items/{item_id}")
async def get_lifecycle_summary(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_role)
):
    """خلاصه چرخه حیات"""
    lifecycle = SoftwareLifecycle(db)
    summary = lifecycle.get_lifecycle_summary(item_id)
    return summary

