"""
Risk Management System
سیستم مدیریت ریسک برای انطباق با ISO 14971
"""
from typing import Dict, Optional, List
from datetime import datetime, date
from enum import Enum
from sqlalchemy import Column, String, Text, DateTime, Date, Boolean, Enum as SQLEnum, ForeignKey, Integer, Float
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func
from app.core.database import Base


class RiskCategory(str, Enum):
    """دسته‌بندی ریسک"""
    CLINICAL = "clinical"  # ریسک بالینی
    TECHNICAL = "technical"  # ریسک فنی
    SOFTWARE = "software"  # ریسک نرم‌افزاری
    DATA = "data"  # ریسک داده
    SECURITY = "security"  # ریسک امنیتی
    REGULATORY = "regulatory"  # ریسک نظارتی
    BUSINESS = "business"  # ریسک کسب‌وکار


class SeverityLevel(str, Enum):
    """سطح شدت"""
    CATASTROPHIC = "catastrophic"  # فاجعه‌بار
    CRITICAL = "critical"  # بحرانی
    SERIOUS = "serious"  # جدی
    MODERATE = "moderate"  # متوسط
    MINOR = "minor"  # جزئی
    NEGLIGIBLE = "negligible"  # ناچیز


class ProbabilityLevel(str, Enum):
    """سطح احتمال"""
    FREQUENT = "frequent"  # مکرر (>1%)
    PROBABLE = "probable"  # محتمل (0.1-1%)
    OCCASIONAL = "occasional"  # گاه‌به‌گاه (0.01-0.1%)
    REMOTE = "remote"  # دور از انتظار (0.001-0.01%)
    IMPROBABLE = "improbable"  # غیرمحتمل (<0.001%)


class RiskStatus(str, Enum):
    """وضعیت ریسک"""
    IDENTIFIED = "identified"  # شناسایی شده
    ANALYZED = "analyzed"  # تحلیل شده
    EVALUATED = "evaluated"  # ارزیابی شده
    MITIGATED = "mitigated"  # کاهش یافته
    ACCEPTED = "accepted"  # پذیرفته شده
    CLOSED = "closed"  # بسته شده


class Risk(Base):
    """ریسک"""
    __tablename__ = "risks"

    risk_id = Column(String(50), primary_key=True)
    risk_number = Column(String(50), nullable=False, unique=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(SQLEnum(RiskCategory), nullable=False)
    hazard = Column(Text, nullable=True)  # خطر
    hazardous_situation = Column(Text, nullable=True)  # وضعیت خطرناک
    harm = Column(Text, nullable=True)  # آسیب
    severity = Column(SQLEnum(SeverityLevel), nullable=False)
    probability = Column(SQLEnum(ProbabilityLevel), nullable=False)
    risk_score = Column(Float, nullable=True)  # امتیاز ریسک (Severity × Probability)
    initial_risk_level = Column(String(20), nullable=True)  # سطح اولیه ریسک
    residual_risk_level = Column(String(20), nullable=True)  # سطح باقیمانده ریسک
    status = Column(SQLEnum(RiskStatus), nullable=False, default=RiskStatus.IDENTIFIED)
    identified_date = Column(Date, nullable=False, default=date.today)
    identified_by = Column(String(100), nullable=True)
    mitigation_measures = Column(Text, nullable=True)  # اقدامات کاهش
    mitigation_effectiveness = Column(Text, nullable=True)  # اثربخشی کاهش
    residual_risk_acceptable = Column(Boolean, nullable=True)  # آیا ریسک باقیمانده قابل قبول است؟
    accepted_by = Column(String(100), nullable=True)
    acceptance_date = Column(Date, nullable=True)
    closed_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    controls = relationship("RiskControl", back_populates="risk")


class RiskControl(Base):
    """کنترل ریسک"""
    __tablename__ = "risk_controls"

    control_id = Column(String(50), primary_key=True)
    risk_id = Column(String(50), ForeignKey("risks.risk_id"), nullable=False)
    control_type = Column(String(50), nullable=False)  # elimination, substitution, engineering, administrative, PPE
    control_description = Column(Text, nullable=True)
    implementation_date = Column(Date, nullable=True)
    responsible_person = Column(String(100), nullable=True)
    verification_date = Column(Date, nullable=True)
    verified_by = Column(String(100), nullable=True)
    is_effective = Column(Boolean, nullable=True)
    effectiveness_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    risk = relationship("Risk", back_populates="controls")


class RiskManagement:
    """سیستم مدیریت ریسک"""

    # Risk Matrix: Severity × Probability = Risk Score
    SEVERITY_WEIGHTS = {
        SeverityLevel.CATASTROPHIC: 5,
        SeverityLevel.CRITICAL: 4,
        SeverityLevel.SERIOUS: 3,
        SeverityLevel.MODERATE: 2,
        SeverityLevel.MINOR: 1,
        SeverityLevel.NEGLIGIBLE: 0.5
    }

    PROBABILITY_WEIGHTS = {
        ProbabilityLevel.FREQUENT: 5,
        ProbabilityLevel.PROBABLE: 4,
        ProbabilityLevel.OCCASIONAL: 3,
        ProbabilityLevel.REMOTE: 2,
        ProbabilityLevel.IMPROBABLE: 1
    }

    def __init__(self, db: Session):
        self.db = db

    def calculate_risk_score(self, severity: SeverityLevel, probability: ProbabilityLevel) -> float:
        """محاسبه امتیاز ریسک"""
        severity_weight = self.SEVERITY_WEIGHTS.get(severity, 1)
        probability_weight = self.PROBABILITY_WEIGHTS.get(probability, 1)
        return severity_weight * probability_weight

    def get_risk_level(self, risk_score: float) -> str:
        """تعیین سطح ریسک"""
        if risk_score >= 20:
            return "Intolerable"  # غیرقابل تحمل
        elif risk_score >= 12:
            return "High"  # بالا
        elif risk_score >= 6:
            return "Medium"  # متوسط
        else:
            return "Low"  # پایین

    def create_risk(
        self,
        risk_number: str,
        title: str,
        category: RiskCategory,
        severity: SeverityLevel,
        probability: ProbabilityLevel,
        description: Optional[str] = None
    ) -> Risk:
        """ایجاد ریسک"""
        risk_id = f"RISK_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        risk_score = self.calculate_risk_score(severity, probability)
        risk_level = self.get_risk_level(risk_score)
        
        risk = Risk(
            risk_id=risk_id,
            risk_number=risk_number,
            title=title,
            description=description,
            category=category,
            severity=severity,
            probability=probability,
            risk_score=risk_score,
            initial_risk_level=risk_level,
            status=RiskStatus.IDENTIFIED
        )
        
        self.db.add(risk)
        self.db.commit()
        self.db.refresh(risk)
        
        return risk

    def add_control(
        self,
        risk_id: str,
        control_type: str,
        control_description: Optional[str] = None
    ) -> RiskControl:
        """افزودن کنترل ریسک"""
        control_id = f"CTRL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        control = RiskControl(
            control_id=control_id,
            risk_id=risk_id,
            control_type=control_type,
            control_description=control_description
        )
        
        self.db.add(control)
        self.db.commit()
        self.db.refresh(control)
        
        return control

    def mitigate_risk(
        self,
        risk_id: str,
        mitigation_measures: str,
        new_severity: Optional[SeverityLevel] = None,
        new_probability: Optional[ProbabilityLevel] = None
    ) -> Risk:
        """کاهش ریسک"""
        risk = self.db.query(Risk).filter(Risk.risk_id == risk_id).first()
        
        if not risk:
            raise ValueError(f"Risk {risk_id} not found")
        
        # Update severity and probability if provided
        if new_severity:
            risk.severity = new_severity
        if new_probability:
            risk.probability = new_probability
        
        # Recalculate risk score
        risk.risk_score = self.calculate_risk_score(risk.severity, risk.probability)
        risk.residual_risk_level = self.get_risk_level(risk.risk_score)
        
        risk.mitigation_measures = mitigation_measures
        risk.status = RiskStatus.MITIGATED
        
        self.db.commit()
        self.db.refresh(risk)
        
        return risk

    def get_risk_summary(self) -> Dict:
        """خلاصه ریسک‌ها"""
        all_risks = self.db.query(Risk).all()
        
        summary = {
            "total_risks": len(all_risks),
            "by_category": {},
            "by_status": {},
            "by_level": {
                "Intolerable": 0,
                "High": 0,
                "Medium": 0,
                "Low": 0
            },
            "mitigation_status": {
                "mitigated": 0,
                "accepted": 0,
                "open": 0
            }
        }
        
        for risk in all_risks:
            # By category
            cat = risk.category.value
            summary["by_category"][cat] = summary["by_category"].get(cat, 0) + 1
            
            # By status
            status = risk.status.value
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            
            # By level
            level = risk.residual_risk_level or risk.initial_risk_level
            if level:
                summary["by_level"][level] = summary["by_level"].get(level, 0) + 1
            
            # Mitigation status
            if risk.status == RiskStatus.MITIGATED:
                summary["mitigation_status"]["mitigated"] += 1
            elif risk.status == RiskStatus.ACCEPTED:
                summary["mitigation_status"]["accepted"] += 1
            else:
                summary["mitigation_status"]["open"] += 1
        
        return summary

