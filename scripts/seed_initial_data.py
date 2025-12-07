"""
Seed Initial Data Script
وارد کردن داده‌های اولیه به دیتابیس
"""
import sys
import os
from pathlib import Path
from datetime import datetime, date, timedelta
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
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
from app.core.security.auth import get_password_hash
from app.core.security.rbac import Role

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_admin_user(db: Session):
    """ایجاد کاربر ادمین"""
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            logger.info("Admin user already exists")
            return admin
        
        # Create admin user
        admin = User(
            username="admin",
            email="admin@hospital.com",
            hashed_password=get_password_hash("admin123"),
            full_name="System Administrator",
            role=Role.ADMIN,
            is_active=True,
            is_verified=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        logger.info("✅ Admin user created successfully!")
        logger.info("   Username: admin")
        logger.info("   Password: admin123")
        logger.info("   ⚠️  Please change the password after first login!")
        
        return admin
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        db.rollback()
        raise


def create_doctor_user(db: Session):
    """ایجاد کاربر پزشک"""
    try:
        doctor = db.query(User).filter(User.username == "doctor").first()
        if doctor:
            logger.info("Doctor user already exists")
            return doctor
        
        doctor = User(
            username="doctor",
            email="doctor@hospital.com",
            hashed_password=get_password_hash("doctor123"),
            full_name="Dr. John Smith",
            role=Role.DOCTOR,
            is_active=True,
            is_verified=True
        )
        db.add(doctor)
        db.commit()
        db.refresh(doctor)
        
        logger.info("✅ Doctor user created successfully!")
        logger.info("   Username: doctor")
        logger.info("   Password: doctor123")
        
        return doctor
    except Exception as e:
        logger.error(f"Error creating doctor user: {str(e)}")
        db.rollback()
        raise


def create_sample_patients(db: Session, count: int = 5):
    """ایجاد نمونه بیماران"""
    try:
        existing = db.query(Patient).count()
        if existing >= count:
            logger.info(f"Already have {existing} patients, skipping...")
            return
        
        patients = []
        for i in range(count):
            patient_id = f"CAN{str(i+1).zfill(3)}"
            
            # Check if exists
            if db.query(Patient).filter(Patient.patient_id == patient_id).first():
                continue
            
            patient = Patient(
                patient_id=patient_id,
                first_name=f"Patient{i+1}",
                last_name="Sample",
                date_of_birth=date(1950 + random.randint(0, 30), 
                                  random.randint(1, 12), 
                                  random.randint(1, 28)),
                gender=random.choice(["Male", "Female"]),
                phone_number=f"+123456789{i}",
                email=f"patient{i+1}@example.com",
                address=f"{random.randint(100, 999)} Main St, City",
                emergency_contact=f"Emergency Contact {i+1}",
                emergency_phone=f"+123456789{i+10}",
                insurance_provider=random.choice(["Insurance A", "Insurance B", "Insurance C"]),
                insurance_number=f"INS{random.randint(100000, 999999)}",
                created_at=datetime.now() - timedelta(days=random.randint(1, 365))
            )
            db.add(patient)
            patients.append(patient)
        
        db.commit()
        
        for patient in patients:
            db.refresh(patient)
        
        logger.info(f"✅ Created {len(patients)} sample patients")
        return patients
        
    except Exception as e:
        logger.error(f"Error creating sample patients: {str(e)}")
        db.rollback()
        raise


def create_sample_clinical_data(db: Session):
    """ایجاد داده‌های بالینی نمونه"""
    try:
        patients = db.query(Patient).limit(3).all()
        if not patients:
            logger.warning("No patients found, skipping clinical data")
            return
        
        for patient in patients:
            # Check if exists
            existing = db.query(ClinicalData).filter(
                ClinicalData.patient_id == patient.patient_id
            ).first()
            if existing:
                continue
            
            clinical = ClinicalData(
                patient_id=patient.patient_id,
                examination_date=date.today() - timedelta(days=random.randint(1, 30)),
                height_cm=random.randint(150, 190),
                weight_kg=random.randint(50, 100),
                bmi=random.uniform(18.5, 35.0),
                blood_pressure_systolic=random.randint(100, 140),
                blood_pressure_diastolic=random.randint(60, 90),
                heart_rate=random.randint(60, 100),
                temperature=random.uniform(36.0, 37.5),
                t_stage=random.choice(["T1", "T2", "T3", "T4"]),
                n_stage=random.choice(["N0", "N1", "N2", "N3"]),
                m_stage=random.choice(["M0", "M1"]),
                tumor_location=random.choice(["Upper", "Middle", "Lower"]),
                tumor_size_cm=random.uniform(1.0, 8.0),
                performance_status=random.choice(["0", "1", "2"]),
                comorbidities=random.choice(["None", "Hypertension", "Diabetes", "Heart Disease"])
            )
            db.add(clinical)
        
        db.commit()
        logger.info("✅ Created sample clinical data")
        
    except Exception as e:
        logger.error(f"Error creating clinical data: {str(e)}")
        db.rollback()


def seed_initial_data():
    """وارد کردن تمام داده‌های اولیه"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("Seeding Initial Data")
        print("=" * 60)
        
        # Create users
        print("\n1. Creating users...")
        create_admin_user(db)
        create_doctor_user(db)
        
        # Create sample patients
        print("\n2. Creating sample patients...")
        create_sample_patients(db, count=5)
        
        # Create sample clinical data
        print("\n3. Creating sample clinical data...")
        create_sample_clinical_data(db)
        
        print("\n" + "=" * 60)
        print("✅ Initial data seeding completed!")
        print("=" * 60)
        
        # Summary
        print("\n📊 Database Summary:")
        print(f"   Users: {db.query(User).count()}")
        print(f"   Patients: {db.query(Patient).count()}")
        print(f"   Clinical Data: {db.query(ClinicalData).count()}")
        
    except Exception as e:
        logger.error(f"Error seeding data: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_initial_data()

