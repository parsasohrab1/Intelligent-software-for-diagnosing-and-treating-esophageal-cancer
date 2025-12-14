#!/usr/bin/env python3
"""
پاک کردن داده‌های غیرضروری از دیتابیس
Clear unnecessary data from database, keeping only essential data
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.patient import Patient
from app.models.imaging_data import ImagingData
from app.models.clinical_data import ClinicalData
from app.models.genomic_data import GenomicData
from app.models.treatment_data import TreatmentData
from sqlalchemy import and_, or_, func

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clear_duplicate_patients(db):
    """Remove duplicate patients (keep first occurrence)"""
    logger.info("Checking for duplicate patients...")
    
    # Find duplicates by patient_id
    duplicates = db.query(Patient.patient_id).group_by(Patient.patient_id).having(
        func.count(Patient.patient_id) > 1
    ).all()
    
    if duplicates:
        logger.warning(f"Found {len(duplicates)} duplicate patient IDs")
        for (patient_id,) in duplicates:
            # Keep first, delete others
            patients = db.query(Patient).filter(Patient.patient_id == patient_id).order_by(Patient.patient_id).all()
            for p in patients[1:]:  # Skip first
                db.delete(p)
        db.commit()
        logger.info("✓ Removed duplicate patients")
    else:
        logger.info("✓ No duplicate patients found")


def clear_orphaned_imaging_data(db):
    """Remove imaging data without valid patient"""
    logger.info("Checking for orphaned imaging data...")
    
    # Get all patient IDs
    patient_ids = {p[0] for p in db.query(Patient.patient_id).all()}
    
    # Find imaging data without valid patient
    orphaned = db.query(ImagingData).filter(
        ~ImagingData.patient_id.in_(patient_ids)
    ).all()
    
    if orphaned:
        count = len(orphaned)
        for img in orphaned:
            db.delete(img)
        db.commit()
        logger.info(f"✓ Removed {count} orphaned imaging records")
    else:
        logger.info("✓ No orphaned imaging data found")


def clear_orphaned_related_data(db):
    """Remove clinical/genomic/treatment data without valid patient"""
    logger.info("Checking for orphaned related data...")
    
    # Get all patient IDs
    patient_ids = {p[0] for p in db.query(Patient.patient_id).all()}
    
    # Clinical data
    try:
        orphaned_clinical = db.query(ClinicalData).filter(
            ~ClinicalData.patient_id.in_(patient_ids)
        ).all()
        if orphaned_clinical:
            for c in orphaned_clinical:
                db.delete(c)
            logger.info(f"✓ Removed {len(orphaned_clinical)} orphaned clinical records")
    except Exception as e:
        logger.warning(f"Error checking clinical data: {e}")
    
    # Genomic data
    try:
        orphaned_genomic = db.query(GenomicData).filter(
            ~GenomicData.patient_id.in_(patient_ids)
        ).all()
        if orphaned_genomic:
            for g in orphaned_genomic:
                db.delete(g)
            logger.info(f"✓ Removed {len(orphaned_genomic)} orphaned genomic records")
    except Exception as e:
        logger.warning(f"Error checking genomic data: {e}")
    
    # Treatment data
    try:
        orphaned_treatment = db.query(TreatmentData).filter(
            ~TreatmentData.patient_id.in_(patient_ids)
        ).all()
        if orphaned_treatment:
            for t in orphaned_treatment:
                db.delete(t)
            logger.info(f"✓ Removed {len(orphaned_treatment)} orphaned treatment records")
    except Exception as e:
        logger.warning(f"Error checking treatment data: {e}")
    
    db.commit()


def clear_test_data(db, keep_patterns=None):
    """Remove test data (optional: keep certain patterns)"""
    logger.info("Checking for test data...")
    
    if keep_patterns is None:
        keep_patterns = ['CAN', 'NOR']  # Keep synthetic data patterns
    
    # Find test patients (those with test/test_ prefix or similar)
    test_patients = db.query(Patient).filter(
        or_(
            Patient.patient_id.like('TEST%'),
            Patient.patient_id.like('test%'),
            Patient.patient_id.like('TEMP%'),
            Patient.patient_id.like('temp%'),
        )
    ).all()
    
    # But keep patterns we want to preserve
    if keep_patterns:
        test_patients = [p for p in test_patients if not any(
            p.patient_id.startswith(pattern) for pattern in keep_patterns
        )]
    
    if test_patients:
        count = len(test_patients)
        patient_ids = [p.patient_id for p in test_patients]
        
        # Delete related data first
        db.query(ImagingData).filter(ImagingData.patient_id.in_(patient_ids)).delete()
        try:
            db.query(ClinicalData).filter(ClinicalData.patient_id.in_(patient_ids)).delete()
        except:
            pass
        try:
            db.query(GenomicData).filter(GenomicData.patient_id.in_(patient_ids)).delete()
        except:
            pass
        try:
            db.query(TreatmentData).filter(TreatmentData.patient_id.in_(patient_ids)).delete()
        except:
            pass
        
        # Delete patients
        for p in test_patients:
            db.delete(p)
        
        db.commit()
        logger.info(f"✓ Removed {count} test patients and related data")
    else:
        logger.info("✓ No test data found")


def clear_unnecessary_data(keep_synthetic=True):
    """Clear all unnecessary data from database"""
    logger.info("=" * 60)
    logger.info("Clearing Unnecessary Data")
    logger.info("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Get initial counts
        initial_patients = db.query(Patient).count()
        initial_imaging = db.query(ImagingData).count()
        
        logger.info(f"\nInitial state:")
        logger.info(f"  Patients: {initial_patients}")
        logger.info(f"  Imaging Data: {initial_imaging}")
        
        # Clear operations
        clear_duplicate_patients(db)
        clear_orphaned_imaging_data(db)
        clear_orphaned_related_data(db)
        
        if not keep_synthetic:
            clear_test_data(db, keep_patterns=[])
        else:
            clear_test_data(db, keep_patterns=['CAN', 'NOR'])
        
        # Get final counts
        final_patients = db.query(Patient).count()
        final_imaging = db.query(ImagingData).count()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Cleanup completed!")
        logger.info("=" * 60)
        logger.info(f"\nFinal state:")
        logger.info(f"  Patients: {final_patients} (removed {initial_patients - final_patients})")
        logger.info(f"  Imaging Data: {final_imaging} (removed {initial_imaging - final_imaging})")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Error clearing data: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Clear unnecessary data from database")
    parser.add_argument('--no-synthetic', action='store_true', help='Also remove synthetic data (CAN/NOR patterns)')
    args = parser.parse_args()
    
    clear_unnecessary_data(keep_synthetic=not args.no_synthetic)
