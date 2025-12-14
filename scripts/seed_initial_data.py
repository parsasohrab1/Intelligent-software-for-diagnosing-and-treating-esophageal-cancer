"""
Script to seed initial data into database
وارد کردن داده‌های اولیه به دیتابیس
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from datetime import datetime, date
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.patient import Patient
from app.core.security.auth import get_password_hash
from app.core.security.rbac import Role
from app.services.synthetic_data_generator import EsophagealCancerSyntheticData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_initial_users(db: Session):
    """ایجاد کاربران اولیه"""
    logger.info("Creating initial users...")
    
    users = [
        {
            "username": "admin",
            "email": "admin@hospital.com",
            "password": "admin123",  # باید در production تغییر کند
            "full_name": "System Administrator",
            "role": Role.ADMIN,
            "is_active": True
        },
        {
            "username": "doctor1",
            "email": "doctor1@hospital.com",
            "password": "doctor123",
            "full_name": "Dr. John Smith",
            "role": Role.PHYSICIAN,
            "is_active": True
        },
        {
            "username": "radiologist1",
            "email": "radiologist1@hospital.com",
            "password": "radio123",
            "full_name": "Dr. Jane Doe",
            "role": Role.RADIOLOGIST,
            "is_active": True
        },
        {
            "username": "nurse1",
            "email": "nurse1@hospital.com",
            "password": "nurse123",
            "full_name": "Nurse Mary Johnson",
            "role": Role.NURSE,
            "is_active": True
        },
        {
            "username": "researcher1",
            "email": "researcher1@hospital.com",
            "password": "research123",
            "full_name": "Researcher Bob Wilson",
            "role": Role.RESEARCHER,
            "is_active": True
        }
    ]
    
    created_count = 0
    for user_data in users:
        # Check if user exists
        existing = db.query(User).filter(User.username == user_data["username"]).first()
        if existing:
            logger.info(f"User {user_data['username']} already exists, skipping...")
            continue
        
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=get_password_hash(user_data["password"]),
            full_name=user_data["full_name"],
            role=user_data["role"],
            is_active=user_data["is_active"],
            created_at=datetime.now()
        )
        db.add(user)
        created_count += 1
        logger.info(f"Created user: {user_data['username']} ({user_data['role']})")
    
    db.commit()
    logger.info(f"✅ Created {created_count} users")
    return created_count


def seed_sample_patients(db: Session, n_patients: int = 50):
    """وارد کردن نمونه بیماران"""
    logger.info(f"Seeding {n_patients} sample patients...")
    
    # Check if patients already exist
    existing_count = db.query(Patient).count()
    if existing_count >= n_patients:
        logger.info(f"Database already has {existing_count} patients, skipping...")
        return 0
    
    # Generate synthetic data
    generator = EsophagealCancerSyntheticData(seed=42)
    dataset = generator.generate_all_data(
        n_patients=n_patients,
        cancer_ratio=0.4
    )
    
    # Save to database
    generator.save_to_database(dataset, db)
    db.commit()
    
    new_count = db.query(Patient).count()
    logger.info(f"✅ Seeded {new_count - existing_count} new patients")
    return new_count - existing_count


def seed_compliance_data(db: Session):
    """وارد کردن داده‌های اولیه compliance"""
    logger.info("Seeding compliance data...")
    
    from app.core.compliance.validation_documentation import (
        ValidationDocumentation,
        ValidationType,
        ValidationStatus
    )
    from app.core.compliance.risk_management import (
        RiskManagement,
        RiskCategory,
        SeverityLevel,
        ProbabilityLevel
    )
    
    validation_doc = ValidationDocumentation(db)
    risk_mgmt = RiskManagement(db)
    
    # Create sample validation protocol
    try:
        protocol = validation_doc.create_protocol(
            validation_type=ValidationType.SOFTWARE_VALIDATION,
            title="Initial Software Validation Protocol",
            objective="Validate core software functionality",
            scope="All core modules",
            acceptance_criteria="All test cases must pass"
        )
        logger.info(f"✅ Created validation protocol: {protocol.protocol_id}")
    except Exception as e:
        logger.warning(f"Could not create validation protocol: {str(e)}")
    
    # Create sample risk
    try:
        risk = risk_mgmt.identify_risk(
            title="Data Privacy Risk",
            description="Risk of unauthorized access to patient data",
            category=RiskCategory.SECURITY,
            severity=SeverityLevel.SERIOUS,
            probability=ProbabilityLevel.OCCASIONAL,
            identified_by="System"
        )
        logger.info(f"✅ Created risk: {risk.risk_number}")
    except Exception as e:
        logger.warning(f"Could not create risk: {str(e)}")
    
    db.commit()


def main():
    """Main function"""
    print("=" * 60)
    print("Database Initial Data Seeding")
    print("=" * 60)
    
    # Create tables if not exist
    logger.info("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Error creating tables: {str(e)}")
        return
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create initial users
        user_count = create_initial_users(db)
        
        # Seed sample patients
        patient_count = seed_sample_patients(db, n_patients=50)
        
        # Seed compliance data
        seed_compliance_data(db)
        
        print("\n" + "=" * 60)
        print("✅ Initial Data Seeding Completed!")
        print(f"   Users created: {user_count}")
        print(f"   Patients created: {patient_count}")
        print("=" * 60)
        print("\nDefault credentials:")
        print("  Admin: admin / admin123")
        print("  Doctor: doctor1 / doctor123")
        print("  Radiologist: radiologist1 / radio123")
        print("  Nurse: nurse1 / nurse123")
        print("  Researcher: researcher1 / research123")
        print("\n⚠️  IMPORTANT: Change default passwords in production!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Error seeding data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()

