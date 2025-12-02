#!/usr/bin/env python3
"""
Script to generate synthetic data including MRI images
"""
import requests
import json
import time

API_BASE_URL = "http://localhost:8000/api/v1"

def generate_synthetic_data():
    """Generate synthetic data with imaging data"""
    print("=" * 50)
    print("Generating Synthetic Data with MRI Images")
    print("=" * 50)
    print()
    
    # Generate synthetic data
    print("Step 1: Generating synthetic data...")
    data = {
        "n_patients": 50,  # Generate 50 patients
        "cancer_ratio": 0.4,  # 40% with cancer
        "seed": 42,
        "save_to_db": True,  # Important: Save to database
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/synthetic-data/generate",
            json=data,
            timeout=300  # 5 minutes timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Data generated successfully!")
            print(f"   Patients: {result.get('n_patients', 'N/A')}")
            print(f"   Files saved: {result.get('files_saved', [])}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server.")
        print("   Please make sure the server is running:")
        print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def check_mri_data():
    """Check if MRI data exists"""
    print()
    print("Step 2: Checking MRI data...")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/imaging/mri",
            timeout=10
        )
        
        if response.status_code == 200:
            mri_images = response.json()
            print(f"✅ Found {len(mri_images)} MRI images")
            
            if len(mri_images) > 0:
                print("\nSample MRI data:")
                for img in mri_images[:3]:
                    print(f"   - Image ID: {img.get('image_id')}")
                    print(f"     Patient: {img.get('patient_id')}")
                    print(f"     Date: {img.get('imaging_date')}")
                    print(f"     Impression: {img.get('impression', 'N/A')[:50]}...")
                    print()
            return True
        else:
            print(f"⚠️  No MRI data found (Status: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"⚠️  Error checking MRI data: {str(e)}")
        return False

def main():
    """Main function"""
    # Generate data
    success = generate_synthetic_data()
    
    if success:
        # Wait a bit for database to update
        print("\nWaiting for database to update...")
        time.sleep(3)
        
        # Check MRI data
        check_mri_data()
        
        print()
        print("=" * 50)
        print("✅ Data generation complete!")
        print("=" * 50)
        print()
        print("You can now:")
        print("  1. View MRI Report: http://localhost:3000/mri (if frontend is running)")
        print("  2. Check API: http://localhost:8000/api/v1/imaging/mri")
        print("  3. View API Docs: http://localhost:8000/docs")
        print()
    else:
        print()
        print("❌ Data generation failed. Please check the errors above.")
        print()

if __name__ == "__main__":
    main()

