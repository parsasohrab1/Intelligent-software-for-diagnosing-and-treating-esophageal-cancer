#!/usr/bin/env python3
"""Check and fix dashboard data"""
import sys
import os
sys.path.insert(0, '.')

import requests
from app.services.synthetic_data_generator import EsophagealCancerSyntheticData
from app.core.database import SessionLocal
from app.models.patient import Patient
from app.models.imaging_data import ImagingData

def check_database():
    """Check database directly"""
    print("=" * 60)
    print("Checking Database...")
    print("=" * 60)
    try:
        db = SessionLocal()
        try:
            patient_count = db.query(Patient).count()
            mri_count = db.query(ImagingData).filter(ImagingData.imaging_modality == "MRI").count()
            print(f"✅ Database Status:")
            print(f"   Patients: {patient_count}")
            print(f"   MRI Images: {mri_count}")
            return patient_count, mri_count
        finally:
            db.close()
    except Exception as e:
        print(f"❌ Database Error: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0

def check_api():
    """Check API endpoints"""
    print("\n" + "=" * 60)
    print("Checking API Endpoints...")
    print("=" * 60)
    try:
        # Check dashboard endpoint
        print("\n1. Testing /api/v1/patients/dashboard...")
        r = requests.get('http://127.0.0.1:8001/api/v1/patients/dashboard', timeout=10)
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            count = len(data) if isinstance(data, list) else 0
            print(f"   Patients returned: {count}")
        else:
            print(f"   Error: {r.text[:200]}")
        
        # Check regular endpoint
        print("\n2. Testing /api/v1/patients/...")
        try:
            r2 = requests.get('http://127.0.0.1:8001/api/v1/patients/', timeout=10)
            print(f"   Status: {r2.status_code}")
            if r2.status_code == 200:
                data = r2.json()
                count = len(data) if isinstance(data, list) else 0
                print(f"   Patients returned: {count}")
            else:
                print(f"   Error: {r2.text[:200]}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Check seed endpoint
        print("\n3. Testing /api/v1/patients/seed-data...")
        r3 = requests.post('http://127.0.0.1:8001/api/v1/patients/seed-data', timeout=120)
        print(f"   Status: {r3.status_code}")
        if r3.status_code == 200:
            print(f"   Response: {r3.json()}")
        else:
            print(f"   Error: {r3.text[:200]}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Is backend running?")
    except Exception as e:
        print(f"❌ API Error: {e}")
        import traceback
        traceback.print_exc()

def generate_data():
    """Generate data directly"""
    print("\n" + "=" * 60)
    print("Generating Data...")
    print("=" * 60)
    try:
        db = SessionLocal()
        try:
            print("\nCreating generator...")
            generator = EsophagealCancerSyntheticData(seed=42)
            
            print("Generating dataset (50 patients, 40% cancer)...")
            dataset = generator.generate_all_data(n_patients=50, cancer_ratio=0.4)
            
            print("Saving to database...")
            generator.save_to_database(dataset, db)
            db.commit()
            
            # Verify
            patient_count = db.query(Patient).count()
            mri_count = db.query(ImagingData).filter(ImagingData.imaging_modality == "MRI").count()
            
            print("\n✅ Data Generated Successfully!")
            print(f"   Patients: {patient_count}")
            print(f"   MRI Images: {mri_count}")
            return True
        finally:
            db.close()
    except Exception as e:
        print(f"\n❌ Generation Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Check database
    db_patients, db_mri = check_database()
    
    # Check API
    check_api()
    
    # Generate if needed
    if db_patients < 10:
        print("\n" + "=" * 60)
        print("Insufficient data. Generating...")
        print("=" * 60)
        if generate_data():
            print("\n✅ Data generation completed!")
            print("   Please refresh your dashboard.")
        else:
            print("\n❌ Data generation failed!")
    else:
        print("\n✅ Database has sufficient data!")
        print("   If dashboard still shows no data, check API endpoints above.")
