"""
Regulatory Compliance Tracking System
برای ردیابی انطباق با استانداردهای FDA, CE Mark, و وزارت بهداشت
"""
from typing import Dict, Optional, List
from datetime import datetime, date
from enum import Enum
from sqlalchemy import Column, String, Text, DateTime, Date, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func
from app.core.database import Base


class RegulatoryStandard(str, Enum):
    """استانداردهای نظارتی"""
    FDA_510K = "fda_510k"  # FDA 510(k) clearance
    FDA_PMA = "fda_pma"  # FDA Premarket Approval
    FDA_DE_NOVO = "fda_de_novo"  # FDA De Novo
    CE_MARK_CLASS_I = "ce_mark_class_i"
    CE_MARK_CLASS_IIA = "ce_mark_class_iia"
    CE_MARK_CLASS_IIB = "ce_mark_class_iib"
    CE_MARK_CLASS_III = "ce_mark_class_iii"
    MOH_IRAN = "moh_iran"  # وزارت بهداشت ایران
    ISO_13485 = "iso_13485"  # Quality Management System
    IEC_62304 = "iec_62304"  # Software Lifecycle
    ISO_14971 = "iso_14971"  # Risk Management


class ComplianceStatus(str, Enum):
    """وضعیت انطباق"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONDITIONAL_APPROVAL = "conditional_approval"
    EXPIRED = "expired"


class RegulatorySubmission(Base):
    """ثبت ارسال‌های نظارتی"""
    __tablename__ = "regulatory_submissions"

    submission_id = Column(String(50), primary_key=True)
    standard = Column(SQLEnum(RegulatoryStandard), nullable=False)
    status = Column(SQLEnum(ComplianceStatus), nullable=False, default=ComplianceStatus.NOT_STARTED)
    submission_date = Column(Date, nullable=True)
    review_date = Column(Date, nullable=True)
    approval_date = Column(Date, nullable=True)
    expiration_date = Column(Date, nullable=True)
    submission_number = Column(String(100), nullable=True)  # شماره ثبت/تایید
    regulatory_body = Column(String(100), nullable=True)  # سازمان نظارتی
    contact_person = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    requirements = relationship("RegulatoryRequirement", back_populates="submission")
    documents = relationship("RegulatoryDocument", back_populates="submission")


class RegulatoryRequirement(Base):
    """الزامات نظارتی"""
    __tablename__ = "regulatory_requirements"

    requirement_id = Column(String(50), primary_key=True)
    submission_id = Column(String(50), ForeignKey("regulatory_submissions.submission_id"), nullable=False)
    requirement_code = Column(String(50), nullable=False)  # کد الزام
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # documentation, testing, validation, etc.
    is_required = Column(Boolean, default=True)
    is_completed = Column(Boolean, default=False)
    completion_date = Column(Date, nullable=True)
    verified_by = Column(String(100), nullable=True)
    verification_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    submission = relationship("RegulatorySubmission", back_populates="requirements")
    documents = relationship("RegulatoryDocument", back_populates="requirement")


class RegulatoryDocument(Base):
    """مستندات نظارتی"""
    __tablename__ = "regulatory_documents"

    document_id = Column(String(50), primary_key=True)
    submission_id = Column(String(50), ForeignKey("regulatory_submissions.submission_id"), nullable=True)
    requirement_id = Column(String(50), ForeignKey("regulatory_requirements.requirement_id"), nullable=True)
    document_type = Column(String(50), nullable=False)  # SOP, Test Report, Validation Report, etc.
    title = Column(String(200), nullable=False)
    version = Column(String(20), nullable=False, default="1.0")
    file_path = Column(String(500), nullable=True)  # مسیر فایل
    file_hash = Column(String(64), nullable=True)  # SHA-256 hash
    author = Column(String(100), nullable=True)
    reviewer = Column(String(100), nullable=True)
    approval_date = Column(Date, nullable=True)
    effective_date = Column(Date, nullable=True)
    is_current = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    submission = relationship("RegulatorySubmission", back_populates="documents")
    requirement = relationship("RegulatoryRequirement", back_populates="documents")


class RegulatoryTracker:
    """سیستم ردیابی انطباق نظارتی"""

    def __init__(self, db: Session):
        self.db = db

    def create_submission(
        self,
        standard: RegulatoryStandard,
        submission_number: Optional[str] = None,
        regulatory_body: Optional[str] = None
    ) -> RegulatorySubmission:
        """ایجاد ارسال نظارتی جدید"""
        submission_id = f"{standard.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        submission = RegulatorySubmission(
            submission_id=submission_id,
            standard=standard,
            status=ComplianceStatus.NOT_STARTED,
            submission_number=submission_number,
            regulatory_body=regulatory_body
        )
        
        self.db.add(submission)
        self.db.commit()
        self.db.refresh(submission)
        
        return submission

    def add_requirement(
        self,
        submission_id: str,
        requirement_code: str,
        title: str,
        description: Optional[str] = None,
        category: Optional[str] = None
    ) -> RegulatoryRequirement:
        """افزودن الزام نظارتی"""
        requirement_id = f"{submission_id}_{requirement_code}"
        
        requirement = RegulatoryRequirement(
            requirement_id=requirement_id,
            submission_id=submission_id,
            requirement_code=requirement_code,
            title=title,
            description=description,
            category=category
        )
        
        self.db.add(requirement)
        self.db.commit()
        self.db.refresh(requirement)
        
        return requirement

    def mark_requirement_complete(
        self,
        requirement_id: str,
        verified_by: Optional[str] = None
    ) -> bool:
        """علامت‌گذاری الزام به عنوان تکمیل شده"""
        requirement = self.db.query(RegulatoryRequirement).filter(
            RegulatoryRequirement.requirement_id == requirement_id
        ).first()
        
        if not requirement:
            return False
        
        requirement.is_completed = True
        requirement.completion_date = date.today()
        requirement.verified_by = verified_by
        requirement.verification_date = date.today()
        
        self.db.commit()
        return True

    def add_document(
        self,
        submission_id: Optional[str],
        requirement_id: Optional[str],
        document_type: str,
        title: str,
        version: str = "1.0",
        file_path: Optional[str] = None,
        author: Optional[str] = None
    ) -> RegulatoryDocument:
        """افزودن مستند نظارتی"""
        document_id = f"DOC_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        document = RegulatoryDocument(
            document_id=document_id,
            submission_id=submission_id,
            requirement_id=requirement_id,
            document_type=document_type,
            title=title,
            version=version,
            file_path=file_path,
            author=author
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        return document

    def get_submission_status(self, submission_id: str) -> Dict:
        """دریافت وضعیت ارسال نظارتی"""
        submission = self.db.query(RegulatorySubmission).filter(
            RegulatorySubmission.submission_id == submission_id
        ).first()
        
        if not submission:
            return {}
        
        requirements = self.db.query(RegulatoryRequirement).filter(
            RegulatoryRequirement.submission_id == submission_id
        ).all()
        
        total_requirements = len(requirements)
        completed_requirements = len([r for r in requirements if r.is_completed])
        required_requirements = len([r for r in requirements if r.is_required])
        completed_required = len([r for r in requirements if r.is_required and r.is_completed])
        
        return {
            "submission_id": submission.submission_id,
            "standard": submission.standard.value,
            "status": submission.status.value,
            "submission_date": submission.submission_date.isoformat() if submission.submission_date else None,
            "approval_date": submission.approval_date.isoformat() if submission.approval_date else None,
            "total_requirements": total_requirements,
            "completed_requirements": completed_requirements,
            "required_requirements": required_requirements,
            "completed_required": completed_required,
            "completion_percentage": (completed_required / required_requirements * 100) if required_requirements > 0 else 0,
            "requirements": [
                {
                    "requirement_id": r.requirement_id,
                    "code": r.requirement_code,
                    "title": r.title,
                    "is_completed": r.is_completed,
                    "is_required": r.is_required
                }
                for r in requirements
            ]
        }

    def get_compliance_summary(self) -> Dict:
        """خلاصه وضعیت انطباق"""
        submissions = self.db.query(RegulatorySubmission).all()
        
        summary = {
            "total_submissions": len(submissions),
            "by_standard": {},
            "by_status": {},
            "overall_compliance": {}
        }
        
        for submission in submissions:
            # By standard
            standard_key = submission.standard.value
            if standard_key not in summary["by_standard"]:
                summary["by_standard"][standard_key] = {
                    "total": 0,
                    "approved": 0,
                    "in_progress": 0
                }
            summary["by_standard"][standard_key]["total"] += 1
            if submission.status == ComplianceStatus.APPROVED:
                summary["by_standard"][standard_key]["approved"] += 1
            elif submission.status in [ComplianceStatus.IN_PROGRESS, ComplianceStatus.UNDER_REVIEW]:
                summary["by_standard"][standard_key]["in_progress"] += 1
            
            # By status
            status_key = submission.status.value
            summary["by_status"][status_key] = summary["by_status"].get(status_key, 0) + 1
        
        return summary

