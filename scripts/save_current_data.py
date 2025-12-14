#!/usr/bin/env python3
"""
ذخیره تمام داده‌های فعلی دیتابیس
Save all current database data to a snapshot file
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.patient import Patient
from app.models.imaging_data import ImagingData
from app.models.clinical_data import ClinicalData
from app.models.genomic_data import GenomicData
from app.models.treatment_data import TreatmentData
from app.models.user import User

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def serialize_date(obj):
    """Convert date/datetime to string"""
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    return str(obj)


def save_patients(db) -> List[Dict]:
    """Save all patients"""
    patients = db.query(Patient).all()
    data = []
    for p in patients:
        patient_dict = {
            'patient_id': p.patient_id,
            'name': p.name,
            'age': p.age,
            'gender': p.gender,
            'ethnicity': p.ethnicity,
            'has_cancer': p.has_cancer,
            'cancer_type': p.cancer_type,
            'cancer_subtype': p.cancer_subtype,
            'diagnosis_date': serialize_date(p.diagnosis_date) if p.diagnosis_date else None,
            'stage': p.stage,
            'created_at': serialize_date(p.created_at) if hasattr(p, 'created_at') and p.created_at else None,
        }
        data.append(patient_dict)
    return data


def save_imaging_data(db) -> List[Dict]:
    """Save all imaging data"""
    images = db.query(ImagingData).all()
    data = []
    for img in images:
        img_dict = {
            'image_id': img.image_id,
            'patient_id': img.patient_id,
            'imaging_modality': img.imaging_modality,
            'findings': img.findings,
            'impression': img.impression,
            'tumor_length_cm': img.tumor_length_cm,
            'wall_thickness_cm': img.wall_thickness_cm,
            'lymph_nodes_positive': img.lymph_nodes_positive,
            'contrast_used': img.contrast_used,
            'radiologist_id': img.radiologist_id,
            'imaging_date': serialize_date(img.imaging_date) if img.imaging_date else None,
        }
        data.append(img_dict)
    return data


def save_clinical_data(db) -> List[Dict]:
    """Save all clinical data"""
    try:
        clinical = db.query(ClinicalData).all()
        data = []
        for c in clinical:
            c_dict = {
                'clinical_id': c.clinical_id if hasattr(c, 'clinical_id') else None,
                'patient_id': c.patient_id,
                'symptoms': c.symptoms if hasattr(c, 'symptoms') else None,
                'comorbidities': c.comorbidities if hasattr(c, 'comorbidities') else None,
                'lab_results': c.lab_results if hasattr(c, 'lab_results') else None,
                'created_at': serialize_date(c.created_at) if hasattr(c, 'created_at') and c.created_at else None,
            }
            data.append(c_dict)
        return data
    except Exception as e:
        logger.warning(f"Error saving clinical data: {e}")
        return []


def save_genomic_data(db) -> List[Dict]:
    """Save all genomic data"""
    try:
        genomic = db.query(GenomicData).all()
        data = []
        for g in genomic:
            g_dict = {
                'genomic_id': g.genomic_id if hasattr(g, 'genomic_id') else None,
                'patient_id': g.patient_id,
                'mutations': g.mutations if hasattr(g, 'mutations') else None,
                'gene_expression': g.gene_expression if hasattr(g, 'gene_expression') else None,
                'created_at': serialize_date(g.created_at) if hasattr(g, 'created_at') and g.created_at else None,
            }
            data.append(g_dict)
        return data
    except Exception as e:
        logger.warning(f"Error saving genomic data: {e}")
        return []


def save_treatment_data(db) -> List[Dict]:
    """Save all treatment data"""
    try:
        treatments = db.query(TreatmentData).all()
        data = []
        for t in treatments:
            t_dict = {
                'treatment_id': t.treatment_id if hasattr(t, 'treatment_id') else None,
                'patient_id': t.patient_id,
                'treatment_type': t.treatment_type if hasattr(t, 'treatment_type') else None,
                'start_date': serialize_date(t.start_date) if hasattr(t, 'start_date') and t.start_date else None,
                'end_date': serialize_date(t.end_date) if hasattr(t, 'end_date') and t.end_date else None,
                'response': t.response if hasattr(t, 'response') else None,
                'created_at': serialize_date(t.created_at) if hasattr(t, 'created_at') and t.created_at else None,
            }
            data.append(t_dict)
        return data
    except Exception as e:
        logger.warning(f"Error saving treatment data: {e}")
        return []


def save_users(db) -> List[Dict]:
    """Save all users (without passwords)"""
    try:
        users = db.query(User).all()
        data = []
        for u in users:
            u_dict = {
                'user_id': u.user_id if hasattr(u, 'user_id') else None,
                'username': u.username,
                'email': u.email,
                'full_name': u.full_name if hasattr(u, 'full_name') else None,
                'role': u.role.value if hasattr(u.role, 'value') else str(u.role),
                'is_active': u.is_active if hasattr(u, 'is_active') else True,
                # Don't save password for security
            }
            data.append(u_dict)
        return data
    except Exception as e:
        logger.warning(f"Error saving users: {e}")
        return []


def save_current_data(output_file: str = "data_snapshot.json"):
    """Save all current database data to a JSON file"""
    logger.info("=" * 60)
    logger.info("Saving Current Database Data")
    logger.info("=" * 60)
    
    db = SessionLocal()
    snapshot = {
        'metadata': {
            'created_at': datetime.now().isoformat(),
            'version': '1.0',
            'description': 'Complete database snapshot'
        },
        'data': {}
    }
    
    try:
        # Save all data
        logger.info("Saving patients...")
        snapshot['data']['patients'] = save_patients(db)
        logger.info(f"  ✓ Saved {len(snapshot['data']['patients'])} patients")
        
        logger.info("Saving imaging data...")
        snapshot['data']['imaging_data'] = save_imaging_data(db)
        logger.info(f"  ✓ Saved {len(snapshot['data']['imaging_data'])} imaging records")
        
        logger.info("Saving clinical data...")
        snapshot['data']['clinical_data'] = save_clinical_data(db)
        logger.info(f"  ✓ Saved {len(snapshot['data']['clinical_data'])} clinical records")
        
        logger.info("Saving genomic data...")
        snapshot['data']['genomic_data'] = save_genomic_data(db)
        logger.info(f"  ✓ Saved {len(snapshot['data']['genomic_data'])} genomic records")
        
        logger.info("Saving treatment data...")
        snapshot['data']['treatment_data'] = save_treatment_data(db)
        logger.info(f"  ✓ Saved {len(snapshot['data']['treatment_data'])} treatment records")
        
        logger.info("Saving users...")
        snapshot['data']['users'] = save_users(db)
        logger.info(f"  ✓ Saved {len(snapshot['data']['users'])} users")
        
        # Save to file
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info("=" * 60)
        logger.info(f"✅ Data saved successfully to: {output_path.absolute()}")
        logger.info("=" * 60)
        logger.info("\nSummary:")
        logger.info(f"  Patients: {len(snapshot['data']['patients'])}")
        logger.info(f"  Imaging Data: {len(snapshot['data']['imaging_data'])}")
        logger.info(f"  Clinical Data: {len(snapshot['data']['clinical_data'])}")
        logger.info(f"  Genomic Data: {len(snapshot['data']['genomic_data'])}")
        logger.info(f"  Treatment Data: {len(snapshot['data']['treatment_data'])}")
        logger.info(f"  Users: {len(snapshot['data']['users'])}")
        logger.info("=" * 60)
        
        return output_path
        
    except Exception as e:
        logger.error(f"❌ Error saving data: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Save current database data")
    parser.add_argument('--output', '-o', default='data_snapshot.json', help='Output file path')
    args = parser.parse_args()
    
    save_current_data(args.output)
