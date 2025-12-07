#!/usr/bin/env python3
"""Force generate data for dashboard"""
import sys
import os
sys.path.insert(0, '.')

print("=" * 60)
print("Force Generating Dashboard Data")
print("=" * 60)

try:
    from app.services.synthetic_data_generator import EsophagealCancerSyntheticData
    from app.core.database import SessionLocal
    from app.models.patient import Patient
    from app.models.imaging_data import ImagingData
    
    db = SessionLocal()
    try:
        # Check existing
        patient_count = db.query(Patient).count()
        mri_count = db.query(ImagingData).filter(ImagingData.imaging_modality == "MRI").count()
        print(f"\nCurrent: {patient_count} patients, {mri_count} MRI images")
        
        # Always generate (clear old data if needed)
        if patient_count > 0:
            print("\n⚠️  Existing data found. Generating additional data...")
        else:
            print("\n📊 Database is empty. Generating initial data...")
        
        # Generate
        print("\nGenerating 50 patients with 40% cancer ratio...")
        generator = EsophagealCancerSyntheticData(seed=42)
        dataset = generator.generate_all_data(n_patients=50, cancer_ratio=0.4)
        
        print("Saving to database...")
        generator.save_to_database(dataset, db)
        db.commit()
        
        # Verify
        new_patient_count = db.query(Patient).count()
        new_mri_count = db.query(ImagingData).filter(ImagingData.imaging_modality == "MRI").count()
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS!")
        print(f"   Total Patients: {new_patient_count}")
        print(f"   Total MRI Images: {new_mri_count}")
        print("=" * 60)
        print("\n📝 Next Steps:")
        print("   1. Refresh your dashboard")
        print("   2. Data should now be visible")
        print("   3. If not, check browser console for errors")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()
        
except Exception as e:
    print(f"\n❌ CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
