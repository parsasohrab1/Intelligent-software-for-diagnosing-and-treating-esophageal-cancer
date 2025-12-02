"""
Script to check MRI data in database
"""
import sys
import os
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db, engine, Base
from app.models.imaging_data import ImagingData
from app.models.patient import Patient


def check_mri_data():
    """Check if MRI data exists in database"""
    print("=== Checking MRI Data ===")
    print("")
    
    # Ensure database tables are created
    Base.metadata.create_all(bind=engine)
    
    db: Session = next(get_db())
    try:
        # Check total MRI images
        mri_count = db.query(ImagingData).filter(ImagingData.imaging_modality == "MRI").count()
        print(f"Total MRI images in database: {mri_count}")
        
        if mri_count == 0:
            print("")
            print("⚠️  No MRI data found in database!")
            print("")
            print("To generate MRI data, run:")
            print("  python scripts/generate_and_display_mri_data.py")
            print("")
            print("Or use the API:")
            print("  POST http://127.0.0.1:8001/api/v1/synthetic-data/generate")
            print("  Body: { 'n_patients': 50, 'cancer_ratio': 0.4, 'save_to_db': true }")
            return False
        
        # Show sample data
        print("")
        print("Sample MRI data:")
        sample_mri = db.query(ImagingData).filter(ImagingData.imaging_modality == "MRI").first()
        if sample_mri:
            print(f"  Image ID: {sample_mri.image_id}")
            print(f"  Patient ID: {sample_mri.patient_id}")
            print(f"  Date: {sample_mri.imaging_date}")
            print(f"  Impression: {sample_mri.impression[:50] if sample_mri.impression else 'N/A'}...")
            print(f"  Tumor Length: {sample_mri.tumor_length_cm} cm" if sample_mri.tumor_length_cm else "  Tumor Length: N/A")
        
        # Check patients
        patient_count = db.query(Patient).count()
        print("")
        print(f"Total patients in database: {patient_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking MRI data: {e}")
        print("")
        print("Make sure:")
        print("  1. Docker services are running (PostgreSQL)")
        print("  2. Database is initialized")
        print("  3. Backend can connect to database")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = check_mri_data()
    if not success:
        sys.exit(1)

