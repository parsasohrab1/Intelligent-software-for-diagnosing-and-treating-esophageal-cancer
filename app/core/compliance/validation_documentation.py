"""
Validation Documentation System
برای مستندسازی فرآیندهای اعتبارسنجی و تست
"""
from typing import Dict, Optional, List
from datetime import datetime, date
from enum import Enum
from sqlalchemy import Column, String, Text, DateTime, Date, Boolean, Enum as SQLEnum, ForeignKey, Float, Integer
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ValidationType(str, Enum):
    """انواع اعتبارسنجی"""
    SOFTWARE_VALIDATION = "software_validation"
    CLINICAL_VALIDATION = "clinical_validation"
    PERFORMANCE_VALIDATION = "performance_validation"
    SAFETY_VALIDATION = "safety_validation"
    USABILITY_VALIDATION = "usability_validation"
    DATA_VALIDATION = "data_validation"
    ALGORITHM_VALIDATION = "algorithm_validation"


class ValidationStatus(str, Enum):
    """وضعیت اعتبارسنجی"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ValidationProtocol(Base):
    """پروتکل اعتبارسنجی"""
    __tablename__ = "validation_protocols"

    protocol_id = Column(String(50), primary_key=True)
    validation_type = Column(SQLEnum(ValidationType), nullable=False)
    title = Column(String(200), nullable=False)
    version = Column(String(20), nullable=False, default="1.0")
    objective = Column(Text, nullable=True)  # هدف اعتبارسنجی
    scope = Column(Text, nullable=True)  # محدوده
    acceptance_criteria = Column(Text, nullable=True)  # معیارهای پذیرش
    test_environment = Column(Text, nullable=True)  # محیط تست
    test_data_description = Column(Text, nullable=True)  # توضیحات داده تست
    status = Column(SQLEnum(ValidationStatus), nullable=False, default=ValidationStatus.PLANNED)
    planned_start_date = Column(Date, nullable=True)
    planned_end_date = Column(Date, nullable=True)
    actual_start_date = Column(Date, nullable=True)
    actual_end_date = Column(Date, nullable=True)
    approved_by = Column(String(100), nullable=True)
    approval_date = Column(Date, nullable=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    test_cases = relationship("ValidationTestCase", back_populates="protocol")
    results = relationship("ValidationResult", back_populates="protocol")


class ValidationTestCase(Base):
    """مورد تست اعتبارسنجی"""
    __tablename__ = "validation_test_cases"

    test_case_id = Column(String(50), primary_key=True)
    protocol_id = Column(String(50), ForeignKey("validation_protocols.protocol_id"), nullable=False)
    test_case_number = Column(String(20), nullable=False)  # شماره تست
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    preconditions = Column(Text, nullable=True)  # پیش‌شرط‌ها
    test_steps = Column(Text, nullable=True)  # مراحل تست
    expected_result = Column(Text, nullable=True)  # نتیجه مورد انتظار
    priority = Column(String(20), nullable=True)  # High, Medium, Low
    is_required = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    protocol = relationship("ValidationProtocol", back_populates="test_cases")
    executions = relationship("ValidationExecution", back_populates="test_case")


class ValidationExecution(Base):
    """اجرای تست اعتبارسنجی"""
    __tablename__ = "validation_executions"

    execution_id = Column(String(50), primary_key=True)
    test_case_id = Column(String(50), ForeignKey("validation_test_cases.test_case_id"), nullable=False)
    protocol_id = Column(String(50), ForeignKey("validation_protocols.protocol_id"), nullable=False)
    execution_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    executed_by = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False)  # Pass, Fail, Blocked, Skipped
    actual_result = Column(Text, nullable=True)  # نتیجه واقعی
    deviation = Column(Text, nullable=True)  # انحراف از انتظار
    screenshots = Column(Text, nullable=True)  # مسیر تصاویر
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    test_case = relationship("ValidationTestCase", back_populates="executions")


class ValidationResult(Base):
    """نتیجه اعتبارسنجی"""
    __tablename__ = "validation_results"

    result_id = Column(String(50), primary_key=True)
    protocol_id = Column(String(50), ForeignKey("validation_protocols.protocol_id"), nullable=False)
    overall_status = Column(String(20), nullable=False)  # Pass, Fail, Conditional Pass
    summary = Column(Text, nullable=True)  # خلاصه نتایج
    total_test_cases = Column(Integer, default=0)
    passed_test_cases = Column(Integer, default=0)
    failed_test_cases = Column(Integer, default=0)
    blocked_test_cases = Column(Integer, default=0)
    pass_rate = Column(Float, nullable=True)  # درصد موفقیت
    deviations = Column(Text, nullable=True)  # انحرافات
    recommendations = Column(Text, nullable=True)  # توصیه‌ها
    approved_by = Column(String(100), nullable=True)
    approval_date = Column(Date, nullable=True)
    report_path = Column(String(500), nullable=True)  # مسیر گزارش
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    protocol = relationship("ValidationProtocol", back_populates="results")


class ValidationDocumentation:
    """سیستم مستندسازی اعتبارسنجی"""

    def __init__(self, db: Session):
        self.db = db

    def create_protocol(
        self,
        validation_type: ValidationType,
        title: str,
        objective: Optional[str] = None,
        scope: Optional[str] = None,
        acceptance_criteria: Optional[str] = None
    ) -> ValidationProtocol:
        """ایجاد پروتکل اعتبارسنجی"""
        protocol_id = f"VAL_{validation_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        protocol = ValidationProtocol(
            protocol_id=protocol_id,
            validation_type=validation_type,
            title=title,
            objective=objective,
            scope=scope,
            acceptance_criteria=acceptance_criteria,
            status=ValidationStatus.PLANNED
        )
        
        self.db.add(protocol)
        self.db.commit()
        self.db.refresh(protocol)
        
        return protocol

    def add_test_case(
        self,
        protocol_id: str,
        test_case_number: str,
        title: str,
        description: Optional[str] = None,
        expected_result: Optional[str] = None
    ) -> ValidationTestCase:
        """افزودن مورد تست"""
        test_case_id = f"{protocol_id}_TC_{test_case_number}"
        
        test_case = ValidationTestCase(
            test_case_id=test_case_id,
            protocol_id=protocol_id,
            test_case_number=test_case_number,
            title=title,
            description=description,
            expected_result=expected_result
        )
        
        self.db.add(test_case)
        self.db.commit()
        self.db.refresh(test_case)
        
        return test_case

    def execute_test_case(
        self,
        test_case_id: str,
        status: str,
        actual_result: Optional[str] = None,
        executed_by: Optional[str] = None
    ) -> ValidationExecution:
        """اجرای مورد تست"""
        test_case = self.db.query(ValidationTestCase).filter(
            ValidationTestCase.test_case_id == test_case_id
        ).first()
        
        if not test_case:
            raise ValueError(f"Test case {test_case_id} not found")
        
        execution_id = f"EXE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        execution = ValidationExecution(
            execution_id=execution_id,
            test_case_id=test_case_id,
            protocol_id=test_case.protocol_id,
            status=status,
            actual_result=actual_result,
            executed_by=executed_by
        )
        
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        
        return execution

    def generate_validation_result(
        self,
        protocol_id: str,
        approved_by: Optional[str] = None
    ) -> ValidationResult:
        """تولید نتیجه اعتبارسنجی"""
        # Get all test cases for protocol
        test_cases = self.db.query(ValidationTestCase).filter(
            ValidationTestCase.protocol_id == protocol_id
        ).all()
        
        # Get latest execution for each test case
        total = len(test_cases)
        passed = 0
        failed = 0
        blocked = 0
        
        for tc in test_cases:
            latest_execution = self.db.query(ValidationExecution).filter(
                ValidationExecution.test_case_id == tc.test_case_id
            ).order_by(ValidationExecution.execution_date.desc()).first()
            
            if latest_execution:
                if latest_execution.status.lower() == "pass":
                    passed += 1
                elif latest_execution.status.lower() == "fail":
                    failed += 1
                elif latest_execution.status.lower() == "blocked":
                    blocked += 1
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        # Determine overall status
        if failed > 0:
            overall_status = "Fail"
        elif blocked > 0:
            overall_status = "Conditional Pass"
        else:
            overall_status = "Pass"
        
        result_id = f"RES_{protocol_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        result = ValidationResult(
            result_id=result_id,
            protocol_id=protocol_id,
            overall_status=overall_status,
            total_test_cases=total,
            passed_test_cases=passed,
            failed_test_cases=failed,
            blocked_test_cases=blocked,
            pass_rate=pass_rate,
            approved_by=approved_by,
            approval_date=date.today() if approved_by else None
        )
        
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        
        return result

    def get_protocol_summary(self, protocol_id: str) -> Dict:
        """خلاصه پروتکل اعتبارسنجی"""
        protocol = self.db.query(ValidationProtocol).filter(
            ValidationProtocol.protocol_id == protocol_id
        ).first()
        
        if not protocol:
            return {}
        
        test_cases = self.db.query(ValidationTestCase).filter(
            ValidationTestCase.protocol_id == protocol_id
        ).all()
        
        executions = []
        for tc in test_cases:
            latest = self.db.query(ValidationExecution).filter(
                ValidationExecution.test_case_id == tc.test_case_id
            ).order_by(ValidationExecution.execution_date.desc()).first()
            
            executions.append({
                "test_case_id": tc.test_case_id,
                "test_case_number": tc.test_case_number,
                "title": tc.title,
                "status": latest.status if latest else "Not Executed",
                "execution_date": latest.execution_date.isoformat() if latest else None
            })
        
        return {
            "protocol_id": protocol.protocol_id,
            "validation_type": protocol.validation_type.value,
            "title": protocol.title,
            "version": protocol.version,
            "status": protocol.status.value,
            "total_test_cases": len(test_cases),
            "test_cases": executions
        }

