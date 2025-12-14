"""
Training System for Team Education
سیستم آموزش تیم
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import Column, String, Text, DateTime, Date, Boolean, Integer, ForeignKey, JSON
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func
from app.core.database import Base

logger = logging.getLogger(__name__)


class TrainingStatus(str, Enum):
    """وضعیت آموزش"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class TrainingType(str, Enum):
    """نوع آموزش"""
    SYSTEM_OVERVIEW = "system_overview"
    PATIENT_MANAGEMENT = "patient_management"
    IMAGING_ANALYSIS = "imaging_analysis"
    CDS_USAGE = "cds_usage"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    API_USAGE = "api_usage"
    ADVANCED_FEATURES = "advanced_features"


class TrainingModule(Base):
    """ماژول آموزش"""
    __tablename__ = "training_modules"
    
    module_id = Column(String(50), primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    training_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=True)  # محتوای آموزش
    video_url = Column(String(500), nullable=True)
    documentation_url = Column(String(500), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    difficulty_level = Column(String(20), nullable=True)  # beginner, intermediate, advanced
    prerequisites = Column(JSON, nullable=True)  # لیست module_id های پیش‌نیاز
    order = Column(Integer, nullable=True)  # ترتیب نمایش
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    enrollments = relationship("TrainingEnrollment", back_populates="module")


class TrainingEnrollment(Base):
    """ثبت‌نام در آموزش"""
    __tablename__ = "training_enrollments"
    
    enrollment_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    module_id = Column(String(50), ForeignKey("training_modules.module_id"), nullable=False)
    status = Column(String(20), nullable=False, default=TrainingStatus.NOT_STARTED.value)
    progress_percentage = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    score = Column(Integer, nullable=True)  # نمره آزمون (0-100)
    certificate_issued = Column(Boolean, default=False)
    certificate_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="training_enrollments")
    module = relationship("TrainingModule", back_populates="enrollments")


class TrainingQuiz(Base):
    """آزمون آموزش"""
    __tablename__ = "training_quizzes"
    
    quiz_id = Column(String(50), primary_key=True)
    module_id = Column(String(50), ForeignKey("training_modules.module_id"), nullable=False)
    question = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)  # گزینه‌های پاسخ
    correct_answer = Column(Integer, nullable=False)  # شاخص پاسخ صحیح
    explanation = Column(Text, nullable=True)
    order = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TrainingSystem:
    """سیستم آموزش تیم"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_module(
        self,
        title: str,
        training_type: TrainingType,
        description: Optional[str] = None,
        content: Optional[str] = None,
        video_url: Optional[str] = None,
        documentation_url: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        difficulty_level: str = "beginner",
        prerequisites: Optional[List[str]] = None
    ) -> TrainingModule:
        """ایجاد ماژول آموزش"""
        module_id = f"TRAIN_{training_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        module = TrainingModule(
            module_id=module_id,
            title=title,
            description=description,
            training_type=training_type.value,
            content=content,
            video_url=video_url,
            documentation_url=documentation_url,
            duration_minutes=duration_minutes,
            difficulty_level=difficulty_level,
            prerequisites=prerequisites or [],
            is_active=True
        )
        
        self.db.add(module)
        self.db.commit()
        self.db.refresh(module)
        
        logger.info(f"Created training module: {module_id}")
        return module
    
    def enroll_user(
        self,
        user_id: str,
        module_id: str
    ) -> TrainingEnrollment:
        """ثبت‌نام کاربر در ماژول"""
        # Check if already enrolled
        existing = self.db.query(TrainingEnrollment).filter(
            TrainingEnrollment.user_id == user_id,
            TrainingEnrollment.module_id == module_id
        ).first()
        
        if existing:
            return existing
        
        enrollment_id = f"ENR_{user_id}_{module_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        enrollment = TrainingEnrollment(
            enrollment_id=enrollment_id,
            user_id=user_id,
            module_id=module_id,
            status=TrainingStatus.NOT_STARTED.value
        )
        
        self.db.add(enrollment)
        self.db.commit()
        self.db.refresh(enrollment)
        
        logger.info(f"Enrolled user {user_id} in module {module_id}")
        return enrollment
    
    def update_progress(
        self,
        enrollment_id: str,
        progress_percentage: int,
        status: Optional[TrainingStatus] = None
    ):
        """به‌روزرسانی پیشرفت"""
        enrollment = self.db.query(TrainingEnrollment).filter(
            TrainingEnrollment.enrollment_id == enrollment_id
        ).first()
        
        if not enrollment:
            raise ValueError(f"Enrollment {enrollment_id} not found")
        
        enrollment.progress_percentage = min(100, max(0, progress_percentage))
        
        if status:
            enrollment.status = status.value
        
        if progress_percentage == 100 and enrollment.status != TrainingStatus.COMPLETED.value:
            enrollment.status = TrainingStatus.COMPLETED.value
            enrollment.completed_at = datetime.now()
        
        if enrollment.status == TrainingStatus.IN_PROGRESS.value and not enrollment.started_at:
            enrollment.started_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(enrollment)
        
        return enrollment
    
    def complete_training(
        self,
        enrollment_id: str,
        score: Optional[int] = None
    ) -> TrainingEnrollment:
        """تکمیل آموزش"""
        enrollment = self.db.query(TrainingEnrollment).filter(
            TrainingEnrollment.enrollment_id == enrollment_id
        ).first()
        
        if not enrollment:
            raise ValueError(f"Enrollment {enrollment_id} not found")
        
        enrollment.status = TrainingStatus.COMPLETED.value
        enrollment.progress_percentage = 100
        enrollment.completed_at = datetime.now()
        
        if score is not None:
            enrollment.score = score
        
        self.db.commit()
        self.db.refresh(enrollment)
        
        return enrollment
    
    def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """دریافت پیشرفت کاربر"""
        enrollments = self.db.query(TrainingEnrollment).filter(
            TrainingEnrollment.user_id == user_id
        ).all()
        
        total_modules = len(enrollments)
        completed = len([e for e in enrollments if e.status == TrainingStatus.COMPLETED.value])
        in_progress = len([e for e in enrollments if e.status == TrainingStatus.IN_PROGRESS.value])
        
        return {
            "user_id": user_id,
            "total_enrollments": total_modules,
            "completed": completed,
            "in_progress": in_progress,
            "not_started": total_modules - completed - in_progress,
            "completion_rate": (completed / total_modules * 100) if total_modules > 0 else 0,
            "enrollments": [
                {
                    "module_id": e.module_id,
                    "status": e.status,
                    "progress": e.progress_percentage,
                    "score": e.score
                }
                for e in enrollments
            ]
        }
    
    def get_available_modules(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """دریافت ماژول‌های موجود"""
        modules = self.db.query(TrainingModule).filter(
            TrainingModule.is_active == True
        ).order_by(TrainingModule.order).all()
        
        result = []
        for module in modules:
            module_data = {
                "module_id": module.module_id,
                "title": module.title,
                "description": module.description,
                "training_type": module.training_type,
                "duration_minutes": module.duration_minutes,
                "difficulty_level": module.difficulty_level,
                "video_url": module.video_url,
                "documentation_url": module.documentation_url
            }
            
            # Check enrollment status if user_id provided
            if user_id:
                enrollment = self.db.query(TrainingEnrollment).filter(
                    TrainingEnrollment.user_id == user_id,
                    TrainingEnrollment.module_id == module.module_id
                ).first()
                
                if enrollment:
                    module_data["enrollment_status"] = enrollment.status
                    module_data["progress"] = enrollment.progress_percentage
                else:
                    module_data["enrollment_status"] = "not_enrolled"
            
            result.append(module_data)
        
        return result

