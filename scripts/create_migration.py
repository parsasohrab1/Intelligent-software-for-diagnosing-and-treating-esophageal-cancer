"""
Create Database Migration Script
ایجاد migration برای جداول دیتابیس
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import Base, engine
from app.models import (
    Patient,
    ClinicalData,
    GenomicData,
    ImagingData,
    TreatmentData,
    LabResult,
    QualityOfLife,
    User,
)
from app.core.security.consent_manager import PatientConsent

# Import compliance models if they exist
try:
    from app.core.compliance.validation_documentation import (
        ValidationProtocol,
        ValidationTestCase,
        ValidationExecution,
        ValidationResult
    )
    from app.core.compliance.quality_assurance import (
        QADocument,
        Audit,
        CAPA,
        NonConformance
    )
    from app.core.compliance.risk_management import (
        Risk,
        RiskControl
    )
    from app.core.compliance.change_control import (
        ChangeRequest,
        DeviceHistoryRecord
    )
    from app.core.compliance.software_lifecycle import (
        SoftwareVersion,
        SoftwareRelease
    )
except ImportError:
    pass

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_all_tables():
    """ایجاد تمام جداول دیتابیس"""
    try:
        logger.info("Creating all database tables...")
        
        # Import all models to ensure they are registered
        from app.models import (
            patient,
            clinical_data,
            genomic_data,
            imaging_data,
            treatment_data,
            lab_results,
            quality_of_life,
            user,
        )
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ All database tables created successfully!")
        
        # List created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        logger.info(f"\n📊 Created {len(tables)} tables:")
        for table in sorted(tables):
            logger.info(f"  - {table}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating tables: {str(e)}")
        raise


def verify_tables():
    """بررسی وجود جداول"""
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = [
            'patients',
            'clinical_data',
            'genomic_data',
            'imaging_data',
            'treatment_data',
            'lab_results',
            'quality_of_life',
            'users',
        ]
        
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            logger.warning(f"⚠️  Missing tables: {', '.join(missing_tables)}")
            return False
        else:
            logger.info("✅ All required tables exist!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error verifying tables: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Creating Tables")
    print("=" * 60)
    
    try:
        create_all_tables()
        verify_tables()
        print("\n✅ Migration completed successfully!")
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        sys.exit(1)

