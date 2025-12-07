"""
Change Control System
سیستم کنترل تغییرات برای مدیریت تغییرات نرم‌افزار
"""
from typing import Dict, Optional, List
from datetime import datetime, date
from enum import Enum
from sqlalchemy import Column, String, Text, DateTime, Date, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ChangeType(str, Enum):
    """انواع تغییر"""
    BUG_FIX = "bug_fix"  # رفع باگ
    FEATURE_ADDITION = "feature_addition"  # افزودن ویژگی
    ENHANCEMENT = "enhancement"  # بهبود
    SECURITY_PATCH = "security_patch"  # وصله امنیتی
    PERFORMANCE_IMPROVEMENT = "performance_improvement"  # بهبود عملکرد
    REGULATORY_UPDATE = "regulatory_update"  # به‌روزرسانی نظارتی
    DOCUMENTATION_UPDATE = "documentation_update"  # به‌روزرسانی مستندات


class ChangePriority(str, Enum):
    """اولویت تغییر"""
    CRITICAL = "critical"  # بحرانی
    HIGH = "high"  # بالا
    MEDIUM = "medium"  # متوسط
    LOW = "low"  # پایین


class ChangeStatus(str, Enum):
    """وضعیت تغییر"""
    REQUESTED = "requested"  # درخواست شده
    APPROVED = "approved"  # تایید شده
    IN_PROGRESS = "in_progress"  # در حال انجام
    TESTING = "testing"  # در حال تست
    COMPLETED = "completed"  # تکمیل شده
    REJECTED = "rejected"  # رد شده
    CANCELLED = "cancelled"  # لغو شده


class ChangeRequest(Base):
    """درخواست تغییر"""
    __tablename__ = "change_requests"

    change_id = Column(String(50), primary_key=True)
    change_number = Column(String(50), nullable=False, unique=True)
    change_type = Column(SQLEnum(ChangeType), nullable=False)
    priority = Column(SQLEnum(ChangePriority), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)  # دلیل تغییر
    impact_assessment = Column(Text, nullable=True)  # ارزیابی تاثیر
    affected_components = Column(Text, nullable=True)  # اجزای تحت تاثیر
    risk_assessment = Column(Text, nullable=True)  # ارزیابی ریسک
    status = Column(SQLEnum(ChangeStatus), nullable=False, default=ChangeStatus.REQUESTED)
    requested_by = Column(String(100), nullable=True)
    requested_date = Column(Date, nullable=False, default=date.today)
    approved_by = Column(String(100), nullable=True)
    approval_date = Column(Date, nullable=True)
    implementation_date = Column(Date, nullable=True)
    testing_date = Column(Date, nullable=True)
    completed_date = Column(Date, nullable=True)
    version_from = Column(String(20), nullable=True)  # نسخه قبل
    version_to = Column(String(20), nullable=True)  # نسخه بعد
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    approvals = relationship("ChangeApproval", back_populates="change_request")
    test_results = relationship("ChangeTestResult", back_populates="change_request")


class ChangeApproval(Base):
    """تایید تغییر"""
    __tablename__ = "change_approvals"

    approval_id = Column(String(50), primary_key=True)
    change_id = Column(String(50), ForeignKey("change_requests.change_id"), nullable=False)
    approver_role = Column(String(50), nullable=False)  # نقش تاییدکننده (QA, Regulatory, etc.)
    approver_name = Column(String(100), nullable=False)
    approval_status = Column(String(20), nullable=False)  # approved, rejected, conditional
    approval_date = Column(Date, nullable=False, default=date.today)
    comments = Column(Text, nullable=True)
    conditions = Column(Text, nullable=True)  # شرایط تایید
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    change_request = relationship("ChangeRequest", back_populates="approvals")


class ChangeTestResult(Base):
    """نتیجه تست تغییر"""
    __tablename__ = "change_test_results"

    test_result_id = Column(String(50), primary_key=True)
    change_id = Column(String(50), ForeignKey("change_requests.change_id"), nullable=False)
    test_type = Column(String(50), nullable=False)  # unit, integration, regression, etc.
    test_status = Column(String(20), nullable=False)  # pass, fail, partial
    test_date = Column(Date, nullable=False, default=date.today)
    tested_by = Column(String(100), nullable=True)
    test_results = Column(Text, nullable=True)
    issues_found = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    change_request = relationship("ChangeRequest", back_populates="test_results")


class DeviceHistoryRecord(Base):
    """سابقه دستگاه (DHR)"""
    __tablename__ = "device_history_records"

    dhr_id = Column(String(50), primary_key=True)
    device_serial_number = Column(String(100), nullable=False)
    software_version = Column(String(20), nullable=False)
    release_date = Column(Date, nullable=False)
    manufacturing_date = Column(Date, nullable=True)
    configuration = Column(Text, nullable=True)  # پیکربندی
    test_results = Column(Text, nullable=True)  # نتایج تست
    quality_checks = Column(Text, nullable=True)  # بررسی‌های کیفیت
    release_approval = Column(String(100), nullable=True)  # تایید انتشار
    release_approval_date = Column(Date, nullable=True)
    distribution_info = Column(Text, nullable=True)  # اطلاعات توزیع
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ChangeControl:
    """سیستم کنترل تغییرات"""

    def __init__(self, db: Session):
        self.db = db

    def create_change_request(
        self,
        change_number: str,
        change_type: ChangeType,
        priority: ChangePriority,
        title: str,
        description: Optional[str] = None,
        requested_by: Optional[str] = None
    ) -> ChangeRequest:
        """ایجاد درخواست تغییر"""
        change_id = f"CHG_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        change = ChangeRequest(
            change_id=change_id,
            change_number=change_number,
            change_type=change_type,
            priority=priority,
            title=title,
            description=description,
            requested_by=requested_by,
            status=ChangeStatus.REQUESTED
        )
        
        self.db.add(change)
        self.db.commit()
        self.db.refresh(change)
        
        return change

    def approve_change(
        self,
        change_id: str,
        approver_role: str,
        approver_name: str,
        approval_status: str = "approved",
        comments: Optional[str] = None
    ) -> ChangeApproval:
        """تایید تغییر"""
        approval_id = f"APR_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        approval = ChangeApproval(
            approval_id=approval_id,
            change_id=change_id,
            approver_role=approver_role,
            approver_name=approver_name,
            approval_status=approval_status,
            comments=comments
        )
        
        self.db.add(approval)
        
        # Update change request status
        change = self.db.query(ChangeRequest).filter(
            ChangeRequest.change_id == change_id
        ).first()
        
        if change and approval_status == "approved":
            change.status = ChangeStatus.APPROVED
            change.approved_by = approver_name
            change.approval_date = date.today()
        
        self.db.commit()
        self.db.refresh(approval)
        
        return approval

    def record_test_result(
        self,
        change_id: str,
        test_type: str,
        test_status: str,
        tested_by: Optional[str] = None,
        test_results: Optional[str] = None
    ) -> ChangeTestResult:
        """ثبت نتیجه تست"""
        test_result_id = f"TST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        test_result = ChangeTestResult(
            test_result_id=test_result_id,
            change_id=change_id,
            test_type=test_type,
            test_status=test_status,
            tested_by=tested_by,
            test_results=test_results
        )
        
        self.db.add(test_result)
        
        # Update change request
        change = self.db.query(ChangeRequest).filter(
            ChangeRequest.change_id == change_id
        ).first()
        
        if change:
            change.testing_date = date.today()
            if test_status.lower() == "pass":
                change.status = ChangeStatus.COMPLETED
                change.completed_date = date.today()
            else:
                change.status = ChangeStatus.TESTING
        
        self.db.commit()
        self.db.refresh(test_result)
        
        return test_result

    def create_device_history_record(
        self,
        device_serial_number: str,
        software_version: str,
        release_date: date,
        configuration: Optional[str] = None
    ) -> DeviceHistoryRecord:
        """ایجاد سابقه دستگاه"""
        dhr_id = f"DHR_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        dhr = DeviceHistoryRecord(
            dhr_id=dhr_id,
            device_serial_number=device_serial_number,
            software_version=software_version,
            release_date=release_date,
            configuration=configuration
        )
        
        self.db.add(dhr)
        self.db.commit()
        self.db.refresh(dhr)
        
        return dhr

    def get_change_summary(self) -> Dict:
        """خلاصه تغییرات"""
        all_changes = self.db.query(ChangeRequest).all()
        
        summary = {
            "total_changes": len(all_changes),
            "by_type": {},
            "by_status": {},
            "by_priority": {},
            "pending_approvals": 0,
            "in_testing": 0
        }
        
        for change in all_changes:
            # By type
            change_type = change.change_type.value
            summary["by_type"][change_type] = summary["by_type"].get(change_type, 0) + 1
            
            # By status
            status = change.status.value
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            
            # By priority
            priority = change.priority.value
            summary["by_priority"][priority] = summary["by_priority"].get(priority, 0) + 1
            
            # Counts
            if change.status == ChangeStatus.REQUESTED:
                summary["pending_approvals"] += 1
            elif change.status == ChangeStatus.TESTING:
                summary["in_testing"] += 1
        
        return summary

