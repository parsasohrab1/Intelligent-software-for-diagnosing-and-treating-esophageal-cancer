#!/usr/bin/env python3
"""
بازیابی داده‌های ذخیره شده
Restore saved data from snapshot file
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine, Base
from app.models.patient import Patient
from app.models.imaging_data import ImagingData
from app.models.clinical_data import ClinicalData
from app.models.genomic_data import GenomicData
from app.models.treatment_data import TreatmentData
from app.models.user import User
from app.core.security.auth import get_password_hash
from app.core.security.rbac import Role

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_date(date_str):
    """Parse date string to date object"""
    if not date_str:
        return None
    try:
        from datetime import datetime as dt
        # Try ISO format first
        if 'T' in date_str:
            return dt.fromisoformat(date_str.replace('Z', '+00:00')).date()
        else:
            return dt.fromisoformat(date_str).date()
    except:
        try:
            from datetime import datetime as dt
            return dt.strptime(date_str, '%Y-%m-%d').date()
        except:
            logger.warning(f"Could not parse date: {date_str}")
            return None


def restore_patients(db, patients_data):
    """Restore patients"""
    logger.info(f"Restoring {len(patients_data)} patients...")
    
    for p_data in patients_data:
        try:
            # Check if exists
            existing = db.query(Patient).filter(Patient.patient_id == p_data['patient_id']).first()
            if existing:
                # Update existing
                for key, value in p_data.items():
                    if key == 'diagnosis_date':
                        setattr(existing, key, parse_date(value))
                    elif key != 'patient_id':
                        setattr(existing, key, value)
            else:
                # Create new
                patient = Patient(
                    patient_id=p_data['patient_id'],
                    name=p_data.get('name'),
                    age=p_data.get('age'),
                    gender=p_data.get('gender'),
                    ethnicity=p_data.get('ethnicity'),
                    has_cancer=p_data.get('has_cancer'),
                    cancer_type=p_data.get('cancer_type'),
                    cancer_subtype=p_data.get('cancer_subtype'),
                    diagnosis_date=parse_date(p_data.get('diagnosis_date')),
                    stage=p_data.get('stage'),
                )
                db.add(patient)
        except Exception as e:
            logger.warning(f"Error restoring patient {p_data.get('patient_id')}: {e}")
    
    db.commit()
    logger.info(f"✓ Restored {len(patients_data)} patients")


def restore_imaging_data(db, imaging_data):
    """Restore imaging data"""
    logger.info(f"Restoring {len(imaging_data)} imaging records...")
    
    for img_data in imaging_data:
        try:
            # Check if exists
            existing = db.query(ImagingData).filter(
                ImagingData.image_id == img_data.get('image_id')
            ).first()
            
            if existing:
                # Update existing
                for key, value in img_data.items():
                    if key == 'imaging_date':
                        setattr(existing, key, parse_date(value))
                    elif key != 'image_id':
                        setattr(existing, key, value)
            else:
                # Create new (without image_id to let DB auto-generate)
                img_dict = {k: v for k, v in img_data.items() if k != 'image_id'}
                if 'imaging_date' in img_dict:
                    img_dict['imaging_date'] = parse_date(img_dict['imaging_date'])
                
                imaging = ImagingData(**img_dict)
                db.add(imaging)
        except Exception as e:
            logger.warning(f"Error restoring imaging data {img_data.get('image_id')}: {e}")
    
    db.commit()
    logger.info(f"✓ Restored {len(imaging_data)} imaging records")


def restore_related_data(db, data_list, model_class, id_field='id'):
    """Restore related data (clinical, genomic, treatment)"""
    if not data_list:
        return
    
    logger.info(f"Restoring {len(data_list)} {model_class.__name__} records...")
    
    for data_item in data_list:
        try:
            # Check if exists
            if id_field in data_item and data_item[id_field]:
                existing = db.query(model_class).filter(
                    getattr(model_class, id_field) == data_item[id_field]
                ).first()
            else:
                existing = None
            
            if existing:
                # Update existing
                for key, value in data_item.items():
                    if key in ['start_date', 'end_date', 'created_at']:
                        setattr(existing, key, parse_date(value))
                    elif key != id_field:
                        setattr(existing, key, value)
            else:
                # Create new
                item_dict = {k: v for k, v in data_item.items() if k != id_field}
                for date_key in ['start_date', 'end_date', 'created_at']:
                    if date_key in item_dict:
                        item_dict[date_key] = parse_date(item_dict[date_key])
                
                item = model_class(**item_dict)
                db.add(item)
        except Exception as e:
            logger.warning(f"Error restoring {model_class.__name__} record: {e}")
    
    db.commit()
    logger.info(f"✓ Restored {len(data_list)} {model_class.__name__} records")


def restore_users(db, users_data):
    """Restore users (with default passwords)"""
    logger.info(f"Restoring {len(users_data)} users...")
    
    for u_data in users_data:
        try:
            # Check if exists
            existing = db.query(User).filter(User.username == u_data['username']).first()
            
            if existing:
                # Update existing (don't change password)
                for key, value in u_data.items():
                    if key not in ['username', 'password']:
                        setattr(existing, key, value)
            else:
                # Create new with default password
                user = User(
                    username=u_data['username'],
                    email=u_data['email'],
                    hashed_password=get_password_hash('default123'),  # Default password
                    full_name=u_data.get('full_name'),
                    role=Role[u_data.get('role', 'USER')] if isinstance(u_data.get('role'), str) else u_data.get('role'),
                    is_active=u_data.get('is_active', True),
                )
                db.add(user)
        except Exception as e:
            logger.warning(f"Error restoring user {u_data.get('username')}: {e}")
    
    db.commit()
    logger.info(f"✓ Restored {len(users_data)} users")


def restore_saved_data(snapshot_file: str = "data_snapshot.json", clear_existing: bool = False):
    """Restore data from snapshot file"""
    logger.info("=" * 60)
    logger.info("Restoring Saved Data")
    logger.info("=" * 60)
    
    snapshot_path = Path(snapshot_file)
    if not snapshot_path.exists():
        logger.error(f"❌ Snapshot file not found: {snapshot_path.absolute()}")
        return False
    
    # Load snapshot
    logger.info(f"Loading snapshot from: {snapshot_path}")
    with open(snapshot_path, 'r', encoding='utf-8') as f:
        snapshot = json.load(f)
    
    metadata = snapshot.get('metadata', {})
    logger.info(f"Snapshot created at: {metadata.get('created_at', 'unknown')}")
    
    data = snapshot.get('data', {})
    
    db = SessionLocal()
    
    try:
        # Clear existing data if requested
        if clear_existing:
            logger.info("\n⚠️  Clearing existing data...")
            db.query(ImagingData).delete()
            try:
                db.query(ClinicalData).delete()
            except:
                pass
            try:
                db.query(GenomicData).delete()
            except:
                pass
            try:
                db.query(TreatmentData).delete()
            except:
                pass
            db.query(Patient).delete()
            db.commit()
            logger.info("✓ Cleared existing data")
        
        # Restore data
        logger.info("\nRestoring data...")
        
        if 'patients' in data:
            restore_patients(db, data['patients'])
        
        if 'imaging_data' in data:
            restore_imaging_data(db, data['imaging_data'])
        
        if 'clinical_data' in data:
            restore_related_data(db, data['clinical_data'], ClinicalData, 'clinical_id')
        
        if 'genomic_data' in data:
            restore_related_data(db, data['genomic_data'], GenomicData, 'genomic_id')
        
        if 'treatment_data' in data:
            restore_related_data(db, data['treatment_data'], TreatmentData, 'treatment_id')
        
        if 'users' in data:
            restore_users(db, data['users'])
        
        # Verify
        final_patients = db.query(Patient).count()
        final_imaging = db.query(ImagingData).count()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Data restoration completed!")
        logger.info("=" * 60)
        logger.info(f"\nFinal state:")
        logger.info(f"  Patients: {final_patients}")
        logger.info(f"  Imaging Data: {final_imaging}")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error restoring data: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Restore saved data from snapshot")
    parser.add_argument('--file', '-f', default='data_snapshot.json', help='Snapshot file path')
    parser.add_argument('--clear', action='store_true', help='Clear existing data before restore')
    args = parser.parse_args()
    
    restore_saved_data(args.file, args.clear)
