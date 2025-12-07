#!/usr/bin/env python3
"""
Quick script to seed data for dashboard
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.synthetic_data_generator import EsophagealCancerSyntheticData
from app.core.database import SessionLocal
from app.models.patient import Patient
from app.models.imaging_data import ImagingData

def main():
    print("=" * 60)
    print("Quick Data Seeding for Dashboard")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Check existing data
        patient_count = db.query(Patient).count()
        mri_count = db.query(ImagingData).filter(ImagingData.imaging_modality == "MRI").count()
        
        print(f"\nCurrent database status:")
        print(f"  - Patients: {patient_count}")
        print(f"  - MRI Images: {mri_count}")
        
        if patient_count >= 10 and mri_count >= 10:
            print("\n✅ Database already has sufficient data!")
            return
        
        print("\nGenerating data...")
        print("  - Patients: 50")
        print("  - Cancer Ratio: 40%")
        print("  - Seed: 42")
        
        # Generate data
        generator = EsophagealCancerSyntheticData(seed=42)
        dataset = generator.generate_all_data(n_patients=50, cancer_ratio=0.4)
        
        # Save to database
        print("\nSaving to database...")
        generator.save_to_database(dataset, db)
        db.commit()
        
        # Verify
        new_patient_count = db.query(Patient).count()
        new_mri_count = db.query(ImagingData).filter(ImagingData.imaging_modality == "MRI").count()
        
        print("\n" + "=" * 60)
        print("✅ Data generation completed!")
        print(f"   Patients: {new_patient_count}")
        print(f"   MRI Images: {new_mri_count}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
