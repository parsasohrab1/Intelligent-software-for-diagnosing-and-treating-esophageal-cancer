#!/usr/bin/env python3
"""
Script to generate synthetic data with MRI images and display in dashboard
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.synthetic_data_generator import EsophagealCancerSyntheticData
from app.core.database import SessionLocal, engine, Base
from app.models.imaging_data import ImagingData
from app.models.patient import Patient
from sqlalchemy import func

def generate_data():
    """Generate synthetic data with MRI images"""
    print("=" * 60)
    print("Generating Synthetic Data with MRI Images")
    print("=" * 60)
    print()
    
    # Initialize database session
    db = SessionLocal()
    
    try:
        # Check existing data
        existing_patients = db.query(Patient).count()
        existing_mri = db.query(ImagingData).filter(ImagingData.imaging_modality == "MRI").count()
        
        print(f"Current database status:")
        print(f"  - Patients: {existing_patients}")
        print(f"  - MRI Images: {existing_mri}")
        print()
        
        # Generate data if needed
        if existing_mri < 10:
            print("Generating new synthetic data...")
            print("  - Patients: 50")
            print("  - Cancer Ratio: 0.4 (40%)")
            print("  - Including MRI imaging data")
            print()
            
            # Initialize generator
            generator = EsophagealCancerSyntheticData(seed=42)
            
            # Generate all data
            dataset = generator.generate_all_data(
                n_patients=50,
                cancer_ratio=0.4
            )
            
            print("\nSaving to database...")
            generator.save_to_database(dataset, db)
            
            print("✅ Data generated and saved successfully!")
        else:
            print("✅ Sufficient data already exists in database")
        
        # Display MRI data summary
        print()
        print("=" * 60)
        print("MRI Data Summary")
        print("=" * 60)
        
        mri_images = db.query(ImagingData).filter(
            ImagingData.imaging_modality == "MRI"
        ).limit(10).all()
        
        print(f"\nTotal MRI Images: {db.query(ImagingData).filter(ImagingData.imaging_modality == 'MRI').count()}")
        print(f"\nSample MRI Images (showing first 10):")
        print("-" * 60)
        
        for i, img in enumerate(mri_images, 1):
            patient = db.query(Patient).filter(Patient.patient_id == img.patient_id).first()
            print(f"\n{i}. Image ID: {img.image_id}")
            print(f"   Patient ID: {img.patient_id}")
            if patient:
                print(f"   Patient Name: {getattr(patient, 'name', 'N/A')}")
            print(f"   Imaging Date: {img.imaging_date}")
            print(f"   Findings: {img.findings[:80] if img.findings else 'N/A'}...")
            print(f"   Impression: {img.impression[:80] if img.impression else 'N/A'}...")
            if img.tumor_length_cm:
                print(f"   Tumor Length: {img.tumor_length_cm} cm")
            if img.wall_thickness_cm:
                print(f"   Wall Thickness: {img.wall_thickness_cm} cm")
            print(f"   Lymph Nodes: {img.lymph_nodes_positive}")
            print(f"   Contrast Used: {img.contrast_used}")
        
        print()
        print("=" * 60)
        print("✅ Data Ready for Dashboard!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Start the FastAPI server:")
        print("     uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print()
        print("  2. Access MRI Report:")
        print("     - Frontend: http://localhost:3000/mri (if frontend is running)")
        print("     - API: http://localhost:8000/api/v1/imaging/mri")
        print("     - API Docs: http://localhost:8000/docs")
        print()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    generate_data()

