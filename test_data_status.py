#!/usr/bin/env python3
"""Test data status and generate if needed"""
import sys
import os
sys.path.insert(0, '.')

import requests
from app.services.synthetic_data_generator import EsophagealCancerSyntheticData
from app.core.database import SessionLocal
from app.models.patient import Patient
from app.models.imaging_data import ImagingData

def check_api():
    """Check API status"""
    try:
        r = requests.get('http://127.0.0.1:8001/api/v1/patients', timeout=5)
        print(f"API Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            count = len(data) if isinstance(data, list) else 0
            print(f"Patients from API: {count}")
            return count
        else:
            print(f"API Error: {r.text}")
            return 0
    except Exception as e:
        print(f"API Connection Error: {e}")
        return -1

def check_database():
    """Check database directly"""
    try:
        db = SessionLocal()
        try:
            patient_count = db.query(Patient).count()
            mri_count = db.query(ImagingData).filter(ImagingData.imaging_modality == "MRI").count()
            print(f"Database - Patients: {patient_count}, MRI: {mri_count}")
            return patient_count, mri_count
        finally:
            db.close()
    except Exception as e:
        print(f"Database Error: {e}")
        return 0, 0

def generate_data():
    """Generate data"""
    print("\nGenerating data...")
    try:
        db = SessionLocal()
        try:
            generator = EsophagealCancerSyntheticData(seed=42)
            dataset = generator.generate_all_data(n_patients=50, cancer_ratio=0.4)
            generator.save_to_database(dataset, db)
            db.commit()
            print("✅ Data generated and saved!")
            
            # Verify
            patient_count = db.query(Patient).count()
            mri_count = db.query(ImagingData).filter(ImagingData.imaging_modality == "MRI").count()
            print(f"   Patients: {patient_count}, MRI: {mri_count}")
        finally:
            db.close()
    except Exception as e:
        print(f"❌ Generation Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("Data Status Check")
    print("=" * 60)
    
    # Check database
    print("\n1. Checking database...")
    db_patients, db_mri = check_database()
    
    # Check API
    print("\n2. Checking API...")
    api_count = check_api()
    
    # Generate if needed
    if db_patients < 10:
        print("\n3. Database has insufficient data, generating...")
        generate_data()
        
        # Check again
        print("\n4. Re-checking after generation...")
        db_patients, db_mri = check_database()
        api_count = check_api()
    
    print("\n" + "=" * 60)
    print("Final Status:")
    print(f"  Database: {db_patients} patients, {db_mri} MRI images")
    print(f"  API: {api_count} patients")
    print("=" * 60)
