"""
Consent management system for HIPAA/GDPR compliance
"""
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from app.core.database import Base


class ConsentType(str, Enum):
    """Types of consent"""
    DATA_PROCESSING = "data_processing"
    DATA_SHARING = "data_sharing"
    RESEARCH = "research"
    MARKETING = "marketing"
    THIRD_PARTY = "third_party"


class ConsentStatus(str, Enum):
    """Consent status"""
    GRANTED = "granted"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    PENDING = "pending"


class PatientConsent(Base):
    """Patient consent model"""
    __tablename__ = "patient_consents"

    consent_id = Column(String(50), primary_key=True)
    patient_id = Column(String(20), nullable=False, index=True)
    consent_type = Column(SQLEnum(ConsentType), nullable=False)
    status = Column(SQLEnum(ConsentStatus), nullable=False, default=ConsentStatus.PENDING)
    granted = Column(Boolean, default=False)
    granted_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    withdrawn_at = Column(DateTime(timezone=True), nullable=True)
    purpose = Column(Text, nullable=True)  # Purpose of consent
    scope = Column(Text, nullable=True)  # Scope of data access
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def is_valid(self) -> bool:
        """Check if consent is currently valid"""
        if self.status != ConsentStatus.GRANTED or not self.granted:
            return False
        
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        
        if self.withdrawn_at:
            return False
        
        return True


class ConsentManager:
    """Manage patient consent for data access"""

    def __init__(self, db: Session):
        self.db = db

    def grant_consent(
        self,
        patient_id: str,
        consent_type: ConsentType,
        purpose: Optional[str] = None,
        scope: Optional[str] = None,
        expires_in_days: Optional[int] = None
    ) -> PatientConsent:
        """
        Grant consent for a patient
        
        Args:
            patient_id: Patient identifier
            consent_type: Type of consent
            purpose: Purpose of data access
            scope: Scope of data access
            expires_in_days: Number of days until consent expires (None = no expiration)
            
        Returns:
            PatientConsent object
        """
        # Check for existing consent
        existing = self.db.query(PatientConsent).filter(
            PatientConsent.patient_id == patient_id,
            PatientConsent.consent_type == consent_type,
            PatientConsent.status == ConsentStatus.GRANTED
        ).first()
        
        if existing:
            # Update existing consent
            existing.granted = True
            existing.status = ConsentStatus.GRANTED
            existing.granted_at = datetime.now()
            existing.purpose = purpose
            existing.scope = scope
            
            if expires_in_days:
                existing.expires_at = datetime.now() + timedelta(days=expires_in_days)
            else:
                existing.expires_at = None
            
            existing.withdrawn_at = None
            self.db.commit()
            self.db.refresh(existing)
            return existing
        
        # Create new consent
        consent_id = f"{patient_id}_{consent_type.value}_{datetime.now().timestamp()}"
        consent = PatientConsent(
            consent_id=consent_id,
            patient_id=patient_id,
            consent_type=consent_type,
            status=ConsentStatus.GRANTED,
            granted=True,
            granted_at=datetime.now(),
            purpose=purpose,
            scope=scope
        )
        
        if expires_in_days:
            consent.expires_at = datetime.now() + timedelta(days=expires_in_days)
        
        self.db.add(consent)
        self.db.commit()
        self.db.refresh(consent)
        
        return consent

    def withdraw_consent(
        self,
        patient_id: str,
        consent_type: ConsentType
    ) -> bool:
        """
        Withdraw consent for a patient
        
        Args:
            patient_id: Patient identifier
            consent_type: Type of consent to withdraw
            
        Returns:
            True if consent was withdrawn, False otherwise
        """
        consent = self.db.query(PatientConsent).filter(
            PatientConsent.patient_id == patient_id,
            PatientConsent.consent_type == consent_type,
            PatientConsent.status == ConsentStatus.GRANTED
        ).first()
        
        if consent:
            consent.status = ConsentStatus.WITHDRAWN
            consent.granted = False
            consent.withdrawn_at = datetime.now()
            self.db.commit()
            return True
        
        return False

    def check_consent(
        self,
        patient_id: str,
        consent_type: ConsentType
    ) -> bool:
        """
        Check if patient has valid consent
        
        Args:
            patient_id: Patient identifier
            consent_type: Type of consent to check
            
        Returns:
            True if valid consent exists, False otherwise
        """
        consent = self.db.query(PatientConsent).filter(
            PatientConsent.patient_id == patient_id,
            PatientConsent.consent_type == consent_type
        ).order_by(PatientConsent.created_at.desc()).first()
        
        if not consent:
            return False
        
        return consent.is_valid()

    def get_patient_consents(self, patient_id: str) -> List[PatientConsent]:
        """Get all consents for a patient"""
        return self.db.query(PatientConsent).filter(
            PatientConsent.patient_id == patient_id
        ).order_by(PatientConsent.created_at.desc()).all()

    def expire_old_consents(self) -> int:
        """
        Expire consents that have passed their expiration date
        
        Returns:
            Number of consents expired
        """
        now = datetime.now()
        expired = self.db.query(PatientConsent).filter(
            PatientConsent.status == ConsentStatus.GRANTED,
            PatientConsent.expires_at < now
        ).all()
        
        count = 0
        for consent in expired:
            consent.status = ConsentStatus.EXPIRED
            consent.granted = False
            count += 1
        
        self.db.commit()
        return count

