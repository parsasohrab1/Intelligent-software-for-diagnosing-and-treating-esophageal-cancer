"""
Quality Assurance System
سیستم تضمین کیفیت برای انطباق با ISO 13485
"""
from typing import Dict, Optional, List
from datetime import datetime, date
from enum import Enum
from sqlalchemy import Column, String, Text, DateTime, Date, Boolean, Enum as SQLEnum, ForeignKey, Integer
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func
from app.core.database import Base


class QADocumentType(str, Enum):
    """انواع مستندات QA"""
    SOP = "sop"  # Standard Operating Procedure
    WORK_INSTRUCTION = "work_instruction"
    QUALITY_PLAN = "quality_plan"
    QUALITY_MANUAL = "quality_manual"
    AUDIT_REPORT = "audit_report"
    CORRECTIVE_ACTION = "corrective_action"
    PREVENTIVE_ACTION = "preventive_action"
    NON_CONFORMANCE = "non_conformance"


class AuditType(str, Enum):
    """انواع ممیزی"""
    INTERNAL_AUDIT = "internal_audit"
    EXTERNAL_AUDIT = "external_audit"
    SUPPLIER_AUDIT = "supplier_audit"
    REGULATORY_AUDIT = "regulatory_audit"


class AuditStatus(str, Enum):
    """وضعیت ممیزی"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class QADocument(Base):
    """مستندات QA"""
    __tablename__ = "qa_documents"

    document_id = Column(String(50), primary_key=True)
    document_type = Column(SQLEnum(QADocumentType), nullable=False)
    document_number = Column(String(50), nullable=False, unique=True)  # شماره مستند
    title = Column(String(200), nullable=False)
    version = Column(String(20), nullable=False, default="1.0")
    file_path = Column(String(500), nullable=True)
    file_hash = Column(String(64), nullable=True)
    author = Column(String(100), nullable=True)
    reviewer = Column(String(100), nullable=True)
    approver = Column(String(100), nullable=True)
    approval_date = Column(Date, nullable=True)
    effective_date = Column(Date, nullable=True)
    review_date = Column(Date, nullable=True)  # تاریخ بررسی بعدی
    is_current = Column(Boolean, default=True)
    is_obsolete = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class QualityAudit(Base):
    """ممیزی کیفیت"""
    __tablename__ = "quality_audits"

    audit_id = Column(String(50), primary_key=True)
    audit_type = Column(SQLEnum(AuditType), nullable=False)
    audit_number = Column(String(50), nullable=False, unique=True)
    title = Column(String(200), nullable=False)
    scope = Column(Text, nullable=True)  # محدوده ممیزی
    audit_standard = Column(String(100), nullable=True)  # استاندارد ممیزی (ISO 13485, etc.)
    planned_date = Column(Date, nullable=True)
    actual_date = Column(Date, nullable=True)
    auditor = Column(String(100), nullable=True)  # ممیز
    auditee = Column(String(100), nullable=True)  # ممیزی‌شونده
    status = Column(SQLEnum(AuditStatus), nullable=False, default=AuditStatus.PLANNED)
    findings = Column(Text, nullable=True)  # یافته‌ها
    non_conformances = Column(Text, nullable=True)  # عدم انطباق‌ها
    observations = Column(Text, nullable=True)  # مشاهدات
    recommendations = Column(Text, nullable=True)  # توصیه‌ها
    report_path = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    corrective_actions = relationship("CorrectiveAction", back_populates="audit")


class CorrectiveAction(Base):
    """اقدام اصلاحی (CAPA)"""
    __tablename__ = "corrective_actions"

    action_id = Column(String(50), primary_key=True)
    audit_id = Column(String(50), ForeignKey("quality_audits.audit_id"), nullable=True)
    action_number = Column(String(50), nullable=False, unique=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    root_cause = Column(Text, nullable=True)  # علت ریشه‌ای
    action_plan = Column(Text, nullable=True)  # برنامه اقدام
    responsible_person = Column(String(100), nullable=True)
    target_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)
    verification_date = Column(Date, nullable=True)
    verified_by = Column(String(100), nullable=True)
    is_completed = Column(Boolean, default=False)
    is_effective = Column(Boolean, default=False)  # آیا اقدام موثر بوده؟
    effectiveness_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    audit = relationship("QualityAudit", back_populates="corrective_actions")


class NonConformance(Base):
    """عدم انطباق"""
    __tablename__ = "non_conformances"

    nc_id = Column(String(50), primary_key=True)
    nc_number = Column(String(50), nullable=False, unique=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # Major, Minor, Critical
    detected_date = Column(Date, nullable=False)
    detected_by = Column(String(100), nullable=True)
    location = Column(String(100), nullable=True)  # محل شناسایی
    impact_assessment = Column(Text, nullable=True)  # ارزیابی تاثیر
    containment_action = Column(Text, nullable=True)  # اقدام مهار
    root_cause_analysis = Column(Text, nullable=True)  # تحلیل علت ریشه‌ای
    corrective_action_id = Column(String(50), ForeignKey("corrective_actions.action_id"), nullable=True)
    status = Column(String(20), nullable=False, default="open")  # open, in_progress, closed
    closed_date = Column(Date, nullable=True)
    closed_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class QualityAssurance:
    """سیستم تضمین کیفیت"""

    def __init__(self, db: Session):
        self.db = db

    def create_document(
        self,
        document_type: QADocumentType,
        document_number: str,
        title: str,
        version: str = "1.0",
        author: Optional[str] = None
    ) -> QADocument:
        """ایجاد مستند QA"""
        document_id = f"QA_{document_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        document = QADocument(
            document_id=document_id,
            document_type=document_type,
            document_number=document_number,
            title=title,
            version=version,
            author=author
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        return document

    def create_audit(
        self,
        audit_type: AuditType,
        audit_number: str,
        title: str,
        scope: Optional[str] = None,
        planned_date: Optional[date] = None
    ) -> QualityAudit:
        """ایجاد ممیزی"""
        audit_id = f"AUD_{audit_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        audit = QualityAudit(
            audit_id=audit_id,
            audit_type=audit_type,
            audit_number=audit_number,
            title=title,
            scope=scope,
            planned_date=planned_date,
            status=AuditStatus.PLANNED
        )
        
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)
        
        return audit

    def create_corrective_action(
        self,
        action_number: str,
        title: str,
        description: Optional[str] = None,
        audit_id: Optional[str] = None
    ) -> CorrectiveAction:
        """ایجاد اقدام اصلاحی"""
        action_id = f"CAPA_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        action = CorrectiveAction(
            action_id=action_id,
            audit_id=audit_id,
            action_number=action_number,
            title=title,
            description=description
        )
        
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        
        return action

    def create_non_conformance(
        self,
        nc_number: str,
        title: str,
        description: Optional[str] = None,
        category: Optional[str] = None
    ) -> NonConformance:
        """ایجاد عدم انطباق"""
        nc_id = f"NC_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        nc = NonConformance(
            nc_id=nc_id,
            nc_number=nc_number,
            title=title,
            description=description,
            category=category,
            detected_date=date.today(),
            status="open"
        )
        
        self.db.add(nc)
        self.db.commit()
        self.db.refresh(nc)
        
        return nc

    def get_quality_metrics(self) -> Dict:
        """دریافت معیارهای کیفیت"""
        total_audits = self.db.query(QualityAudit).count()
        completed_audits = self.db.query(QualityAudit).filter(
            QualityAudit.status == AuditStatus.COMPLETED
        ).count()
        
        open_ncs = self.db.query(NonConformance).filter(
            NonConformance.status == "open"
        ).count()
        closed_ncs = self.db.query(NonConformance).filter(
            NonConformance.status == "closed"
        ).count()
        
        open_capas = self.db.query(CorrectiveAction).filter(
            CorrectiveAction.is_completed == False
        ).count()
        completed_capas = self.db.query(CorrectiveAction).filter(
            CorrectiveAction.is_completed == True
        ).count()
        
        return {
            "audits": {
                "total": total_audits,
                "completed": completed_audits,
                "completion_rate": (completed_audits / total_audits * 100) if total_audits > 0 else 0
            },
            "non_conformances": {
                "open": open_ncs,
                "closed": closed_ncs,
                "total": open_ncs + closed_ncs,
                "closure_rate": (closed_ncs / (open_ncs + closed_ncs) * 100) if (open_ncs + closed_ncs) > 0 else 0
            },
            "corrective_actions": {
                "open": open_capas,
                "completed": completed_capas,
                "total": open_capas + completed_capas,
                "completion_rate": (completed_capas / (open_capas + completed_capas) * 100) if (open_capas + completed_capas) > 0 else 0
            }
        }

