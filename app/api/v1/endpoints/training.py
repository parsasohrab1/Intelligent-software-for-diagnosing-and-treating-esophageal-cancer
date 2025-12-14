"""
Training API Endpoints
API برای سیستم آموزش تیم
"""
import logging
from typing import Dict, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security.dependencies import get_current_user_with_role
from app.models.user import User
from app.services.training.training_system import (
    TrainingSystem,
    TrainingType,
    TrainingStatus
)

logger = logging.getLogger(__name__)

router = APIRouter()


class EnrollRequest(BaseModel):
    """Request for enrollment"""
    module_id: str = Field(..., description="Module ID")


class UpdateProgressRequest(BaseModel):
    """Request for updating progress"""
    enrollment_id: str = Field(..., description="Enrollment ID")
    progress_percentage: int = Field(..., ge=0, le=100, description="Progress percentage")
    status: Optional[str] = Field(None, description="Status")


class CompleteTrainingRequest(BaseModel):
    """Request for completing training"""
    enrollment_id: str = Field(..., description="Enrollment ID")
    score: Optional[int] = Field(None, ge=0, le=100, description="Quiz score")


@router.get("/modules")
async def get_available_modules(
    current_user: User = Depends(get_current_user_with_role),
    db: Session = Depends(get_db)
):
    """دریافت لیست ماژول‌های آموزش موجود"""
    try:
        training_system = TrainingSystem(db)
        modules = training_system.get_available_modules(user_id=current_user.user_id)
        return {
            "modules": modules,
            "total": len(modules)
        }
    except Exception as e:
        logger.error(f"Error getting modules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/enroll")
async def enroll_in_module(
    request: EnrollRequest,
    current_user: User = Depends(get_current_user_with_role),
    db: Session = Depends(get_db)
):
    """ثبت‌نام در ماژول آموزش"""
    try:
        training_system = TrainingSystem(db)
        enrollment = training_system.enroll_user(
            user_id=current_user.user_id,
            module_id=request.module_id
        )
        
        return {
            "enrollment_id": enrollment.enrollment_id,
            "module_id": enrollment.module_id,
            "status": enrollment.status,
            "message": "Successfully enrolled in training module"
        }
    except Exception as e:
        logger.error(f"Error enrolling: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/progress")
async def get_my_progress(
    current_user: User = Depends(get_current_user_with_role),
    db: Session = Depends(get_db)
):
    """دریافت پیشرفت آموزشی کاربر"""
    try:
        training_system = TrainingSystem(db)
        progress = training_system.get_user_progress(current_user.user_id)
        return progress
    except Exception as e:
        logger.error(f"Error getting progress: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/update-progress")
async def update_progress(
    request: UpdateProgressRequest,
    current_user: User = Depends(get_current_user_with_role),
    db: Session = Depends(get_db)
):
    """به‌روزرسانی پیشرفت آموزشی"""
    try:
        training_system = TrainingSystem(db)
        
        # Verify enrollment belongs to user
        from app.services.training.training_system import TrainingEnrollment
        enrollment = db.query(TrainingEnrollment).filter(
            TrainingEnrollment.enrollment_id == request.enrollment_id,
            TrainingEnrollment.user_id == current_user.user_id
        ).first()
        
        if not enrollment:
            raise HTTPException(status_code=404, detail="Enrollment not found")
        
        status = TrainingStatus(request.status) if request.status else None
        enrollment = training_system.update_progress(
            enrollment_id=request.enrollment_id,
            progress_percentage=request.progress_percentage,
            status=status
        )
        
        return {
            "enrollment_id": enrollment.enrollment_id,
            "progress": enrollment.progress_percentage,
            "status": enrollment.status
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating progress: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/complete")
async def complete_training(
    request: CompleteTrainingRequest,
    current_user: User = Depends(get_current_user_with_role),
    db: Session = Depends(get_db)
):
    """تکمیل آموزش"""
    try:
        training_system = TrainingSystem(db)
        
        # Verify enrollment belongs to user
        from app.services.training.training_system import TrainingEnrollment
        enrollment = db.query(TrainingEnrollment).filter(
            TrainingEnrollment.enrollment_id == request.enrollment_id,
            TrainingEnrollment.user_id == current_user.user_id
        ).first()
        
        if not enrollment:
            raise HTTPException(status_code=404, detail="Enrollment not found")
        
        enrollment = training_system.complete_training(
            enrollment_id=request.enrollment_id,
            score=request.score
        )
        
        return {
            "enrollment_id": enrollment.enrollment_id,
            "status": enrollment.status,
            "score": enrollment.score,
            "completed_at": enrollment.completed_at.isoformat() if enrollment.completed_at else None,
            "message": "Training completed successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing training: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

