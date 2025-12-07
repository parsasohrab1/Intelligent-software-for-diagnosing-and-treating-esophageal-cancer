"""
Software Lifecycle Management
مدیریت چرخه حیات نرم‌افزار برای انطباق با IEC 62304
"""
from typing import Dict, Optional, List
from datetime import datetime, date
from enum import Enum
from sqlalchemy import Column, String, Text, DateTime, Date, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func
from app.core.database import Base


class SoftwareSafetyClass(str, Enum):
    """کلاس ایمنی نرم‌افزار (IEC 62304)"""
    CLASS_A = "class_a"  # بدون خطر برای سلامت
    CLASS_B = "class_b"  # خطر غیرجدی
    CLASS_C = "class_c"  # خطر جدی یا مرگ‌بار


class LifecyclePhase(str, Enum):
    """فازهای چرخه حیات"""
    PLANNING = "planning"  # برنامه‌ریزی
    REQUIREMENTS = "requirements"  # الزامات
    DESIGN = "design"  # طراحی
    IMPLEMENTATION = "implementation"  # پیاده‌سازی
    TESTING = "testing"  # تست
    INTEGRATION = "integration"  # یکپارچه‌سازی
    SYSTEM_TESTING = "system_testing"  # تست سیستم
    RELEASE = "release"  # انتشار
    MAINTENANCE = "maintenance"  # نگهداری
    RETIREMENT = "retirement"  # بازنشستگی


class SoftwareItem(Base):
    """آیتم نرم‌افزاری"""
    __tablename__ = "software_items"

    item_id = Column(String(50), primary_key=True)
    item_name = Column(String(200), nullable=False)
    item_version = Column(String(20), nullable=False)
    safety_class = Column(SQLEnum(SoftwareSafetyClass), nullable=False)
    description = Column(Text, nullable=True)
    purpose = Column(Text, nullable=True)  # هدف
    current_phase = Column(SQLEnum(LifecyclePhase), nullable=False, default=LifecyclePhase.PLANNING)
    development_start_date = Column(Date, nullable=True)
    release_date = Column(Date, nullable=True)
    retirement_date = Column(Date, nullable=True)
    responsible_person = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    requirements = relationship("SoftwareRequirement", back_populates="software_item")
    design_docs = relationship("SoftwareDesignDoc", back_populates="software_item")
    test_docs = relationship("SoftwareTestDoc", back_populates="software_item")


class SoftwareRequirement(Base):
    """الزامات نرم‌افزاری"""
    __tablename__ = "software_requirements"

    requirement_id = Column(String(50), primary_key=True)
    item_id = Column(String(50), ForeignKey("software_items.item_id"), nullable=False)
    requirement_number = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    requirement_type = Column(String(50), nullable=True)  # functional, non-functional, safety
    priority = Column(String(20), nullable=True)  # High, Medium, Low
    source = Column(String(100), nullable=True)  # منبع الزام
    is_verified = Column(Boolean, default=False)
    verification_method = Column(String(100), nullable=True)  # روش تایید
    verification_date = Column(Date, nullable=True)
    verified_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    software_item = relationship("SoftwareItem", back_populates="requirements")


class SoftwareDesignDoc(Base):
    """مستندات طراحی"""
    __tablename__ = "software_design_docs"

    design_doc_id = Column(String(50), primary_key=True)
    item_id = Column(String(50), ForeignKey("software_items.item_id"), nullable=False)
    doc_type = Column(String(50), nullable=False)  # architecture, detailed_design, interface_spec
    title = Column(String(200), nullable=False)
    version = Column(String(20), nullable=False, default="1.0")
    file_path = Column(String(500), nullable=True)
    author = Column(String(100), nullable=True)
    reviewer = Column(String(100), nullable=True)
    approval_date = Column(Date, nullable=True)
    is_current = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    software_item = relationship("SoftwareItem", back_populates="design_docs")


class SoftwareTestDoc(Base):
    """مستندات تست"""
    __tablename__ = "software_test_docs"

    test_doc_id = Column(String(50), primary_key=True)
    item_id = Column(String(50), ForeignKey("software_items.item_id"), nullable=False)
    test_type = Column(String(50), nullable=False)  # unit, integration, system, acceptance
    title = Column(String(200), nullable=False)
    version = Column(String(20), nullable=False, default="1.0")
    test_plan_path = Column(String(500), nullable=True)
    test_results_path = Column(String(500), nullable=True)
    test_coverage = Column(String(20), nullable=True)  # درصد پوشش
    test_status = Column(String(20), nullable=True)  # pass, fail, in_progress
    executed_by = Column(String(100), nullable=True)
    execution_date = Column(Date, nullable=True)
    approved_by = Column(String(100), nullable=True)
    approval_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    software_item = relationship("SoftwareItem", back_populates="test_docs")


class SoftwareLifecycle:
    """مدیریت چرخه حیات نرم‌افزار"""

    def __init__(self, db: Session):
        self.db = db

    def create_software_item(
        self,
        item_name: str,
        item_version: str,
        safety_class: SoftwareSafetyClass,
        description: Optional[str] = None
    ) -> SoftwareItem:
        """ایجاد آیتم نرم‌افزاری"""
        item_id = f"SW_{item_name.replace(' ', '_')}_{item_version}"
        
        item = SoftwareItem(
            item_id=item_id,
            item_name=item_name,
            item_version=item_version,
            safety_class=safety_class,
            description=description,
            current_phase=LifecyclePhase.PLANNING
        )
        
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        
        return item

    def add_requirement(
        self,
        item_id: str,
        requirement_number: str,
        title: str,
        description: Optional[str] = None,
        requirement_type: Optional[str] = None
    ) -> SoftwareRequirement:
        """افزودن الزام نرم‌افزاری"""
        requirement_id = f"{item_id}_REQ_{requirement_number}"
        
        requirement = SoftwareRequirement(
            requirement_id=requirement_id,
            item_id=item_id,
            requirement_number=requirement_number,
            title=title,
            description=description,
            requirement_type=requirement_type
        )
        
        self.db.add(requirement)
        self.db.commit()
        self.db.refresh(requirement)
        
        return requirement

    def add_design_doc(
        self,
        item_id: str,
        doc_type: str,
        title: str,
        version: str = "1.0",
        author: Optional[str] = None
    ) -> SoftwareDesignDoc:
        """افزودن مستند طراحی"""
        design_doc_id = f"{item_id}_DES_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        doc = SoftwareDesignDoc(
            design_doc_id=design_doc_id,
            item_id=item_id,
            doc_type=doc_type,
            title=title,
            version=version,
            author=author
        )
        
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        
        return doc

    def add_test_doc(
        self,
        item_id: str,
        test_type: str,
        title: str,
        version: str = "1.0"
    ) -> SoftwareTestDoc:
        """افزودن مستند تست"""
        test_doc_id = f"{item_id}_TST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        doc = SoftwareTestDoc(
            test_doc_id=test_doc_id,
            item_id=item_id,
            test_type=test_type,
            title=title,
            version=version
        )
        
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        
        return doc

    def advance_phase(
        self,
        item_id: str,
        new_phase: LifecyclePhase
    ) -> SoftwareItem:
        """پیشرفت به فاز بعدی"""
        item = self.db.query(SoftwareItem).filter(
            SoftwareItem.item_id == item_id
        ).first()
        
        if not item:
            raise ValueError(f"Software item {item_id} not found")
        
        item.current_phase = new_phase
        
        if new_phase == LifecyclePhase.RELEASE:
            item.release_date = date.today()
        
        self.db.commit()
        self.db.refresh(item)
        
        return item

    def get_lifecycle_summary(self, item_id: str) -> Dict:
        """خلاصه چرخه حیات"""
        item = self.db.query(SoftwareItem).filter(
            SoftwareItem.item_id == item_id
        ).first()
        
        if not item:
            return {}
        
        requirements = self.db.query(SoftwareRequirement).filter(
            SoftwareRequirement.item_id == item_id
        ).all()
        
        verified_requirements = len([r for r in requirements if r.is_verified])
        
        return {
            "item_id": item.item_id,
            "item_name": item.item_name,
            "version": item.item_version,
            "safety_class": item.safety_class.value,
            "current_phase": item.current_phase.value,
            "total_requirements": len(requirements),
            "verified_requirements": verified_requirements,
            "verification_rate": (verified_requirements / len(requirements) * 100) if requirements else 0,
            "development_start_date": item.development_start_date.isoformat() if item.development_start_date else None,
            "release_date": item.release_date.isoformat() if item.release_date else None
        }

