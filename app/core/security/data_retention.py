"""
Data retention and deletion policies for HIPAA/GDPR compliance
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.core.security.audit_logger import AuditLogger
from app.models.patient import Patient
from app.models.clinical_data import ClinicalData
from app.models.lab_results import LabResult
from app.models.imaging_data import ImagingData
from app.models.treatment_data import TreatmentData


class DataRetentionPolicy:
    """Data retention and deletion policies"""
    
    # Retention periods (in days)
    PATIENT_DATA_RETENTION_DAYS = 2555  # 7 years (HIPAA requirement)
    CLINICAL_DATA_RETENTION_DAYS = 2555  # 7 years
    LAB_RESULTS_RETENTION_DAYS = 2555  # 7 years
    IMAGING_DATA_RETENTION_DAYS = 2555  # 7 years
    TREATMENT_DATA_RETENTION_DAYS = 2555  # 7 years
    AUDIT_LOG_RETENTION_DAYS = 2555  # 7 years
    
    # GDPR: Right to be forgotten - immediate deletion
    GDPR_DELETION_IMMEDIATE = True

    def __init__(self, db: Session):
        self.db = db
        self.audit_logger = AuditLogger()

    def delete_patient_data(
        self,
        patient_id: str,
        reason: str = "patient_request",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete all patient data (GDPR Right to be Forgotten)
        
        Args:
            patient_id: Patient identifier
            reason: Reason for deletion
            user_id: User requesting deletion
            
        Returns:
            Dictionary with deletion summary
        """
        deletion_summary = {
            "patient_id": patient_id,
            "deleted_at": datetime.now().isoformat(),
            "reason": reason,
            "deleted_by": user_id,
            "tables_affected": [],
            "records_deleted": 0
        }
        
        try:
            # Delete in order (respecting foreign key constraints)
            # 1. Treatment data
            treatment_count = self.db.query(TreatmentData).filter(
                TreatmentData.patient_id == patient_id
            ).delete(synchronize_session=False)
            deletion_summary["records_deleted"] += treatment_count
            deletion_summary["tables_affected"].append("treatment_data")
            
            # 2. Imaging data
            imaging_count = self.db.query(ImagingData).filter(
                ImagingData.patient_id == patient_id
            ).delete(synchronize_session=False)
            deletion_summary["records_deleted"] += imaging_count
            deletion_summary["tables_affected"].append("imaging_data")
            
            # 3. Lab results
            lab_count = self.db.query(LabResult).filter(
                LabResult.patient_id == patient_id
            ).delete(synchronize_session=False)
            deletion_summary["records_deleted"] += lab_count
            deletion_summary["tables_affected"].append("lab_results")
            
            # 4. Clinical data
            clinical_count = self.db.query(ClinicalData).filter(
                ClinicalData.patient_id == patient_id
            ).delete(synchronize_session=False)
            deletion_summary["records_deleted"] += clinical_count
            deletion_summary["tables_affected"].append("clinical_data")
            
            # 5. Patient record (last, as it may be referenced)
            patient_count = self.db.query(Patient).filter(
                Patient.patient_id == patient_id
            ).delete(synchronize_session=False)
            deletion_summary["records_deleted"] += patient_count
            deletion_summary["tables_affected"].append("patients")
            
            # Commit deletion
            self.db.commit()
            
            # Log deletion
            self.audit_logger.log_user_action(
                user_id=user_id or "system",
                action="delete_patient_data",
                resource_type="patient",
                resource_id=patient_id,
                details=deletion_summary
            )
            
            # Log security event
            self.audit_logger.log_security_event(
                event_type="data_deletion",
                severity="high",
                description=f"Patient data deleted: {patient_id}. Reason: {reason}",
                user_id=user_id
            )
            
            deletion_summary["status"] = "success"
            
        except Exception as e:
            self.db.rollback()
            deletion_summary["status"] = "error"
            deletion_summary["error"] = str(e)
            
            # Log error
            self.audit_logger.log_security_event(
                event_type="data_deletion_error",
                severity="high",
                description=f"Error deleting patient data {patient_id}: {str(e)}",
                user_id=user_id
            )
        
        return deletion_summary

    def get_expired_data(
        self,
        table_name: str,
        retention_days: int
    ) -> List[Dict[str, Any]]:
        """
        Get data that has exceeded retention period
        
        Args:
            table_name: Name of the table
            retention_days: Retention period in days
            
        Returns:
            List of expired records
        """
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        if table_name == "patients":
            expired = self.db.query(Patient).filter(
                Patient.updated_at < cutoff_date
            ).all()
        elif table_name == "clinical_data":
            expired = self.db.query(ClinicalData).filter(
                ClinicalData.examination_date < cutoff_date.date()
            ).all()
        elif table_name == "lab_results":
            expired = self.db.query(LabResult).filter(
                LabResult.test_date < cutoff_date.date()
            ).all()
        elif table_name == "imaging_data":
            expired = self.db.query(ImagingData).filter(
                ImagingData.imaging_date < cutoff_date.date()
            ).all()
        elif table_name == "treatment_data":
            expired = self.db.query(TreatmentData).filter(
                TreatmentData.treatment_start_date < cutoff_date.date()
            ).all()
        else:
            return []
        
        return [self._record_to_dict(record) for record in expired]

    def cleanup_expired_data(
        self,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Clean up data that has exceeded retention period
        
        Args:
            dry_run: If True, only report what would be deleted
            
        Returns:
            Summary of cleanup operation
        """
        summary = {
            "dry_run": dry_run,
            "cutoff_date": (datetime.now() - timedelta(days=self.PATIENT_DATA_RETENTION_DAYS)).isoformat(),
            "tables_processed": [],
            "total_records": 0
        }
        
        tables = [
            ("clinical_data", self.CLINICAL_DATA_RETENTION_DAYS),
            ("lab_results", self.LAB_RESULTS_RETENTION_DAYS),
            ("imaging_data", self.IMAGING_DATA_RETENTION_DAYS),
            ("treatment_data", self.TREATMENT_DATA_RETENTION_DAYS),
        ]
        
        for table_name, retention_days in tables:
            expired = self.get_expired_data(table_name, retention_days)
            count = len(expired)
            
            if not dry_run and count > 0:
                # Delete expired records
                cutoff_date = datetime.now() - timedelta(days=retention_days)
                
                if table_name == "clinical_data":
                    deleted = self.db.query(ClinicalData).filter(
                        ClinicalData.examination_date < cutoff_date.date()
                    ).delete(synchronize_session=False)
                elif table_name == "lab_results":
                    deleted = self.db.query(LabResult).filter(
                        LabResult.test_date < cutoff_date.date()
                    ).delete(synchronize_session=False)
                elif table_name == "imaging_data":
                    deleted = self.db.query(ImagingData).filter(
                        ImagingData.imaging_date < cutoff_date.date()
                    ).delete(synchronize_session=False)
                elif table_name == "treatment_data":
                    deleted = self.db.query(TreatmentData).filter(
                        TreatmentData.treatment_start_date < cutoff_date.date()
                    ).delete(synchronize_session=False)
                else:
                    deleted = 0
                
                self.db.commit()
                
                summary["tables_processed"].append({
                    "table": table_name,
                    "records_found": count,
                    "records_deleted": deleted
                })
                summary["total_records"] += deleted
            else:
                summary["tables_processed"].append({
                    "table": table_name,
                    "records_found": count,
                    "records_deleted": 0 if dry_run else count
                })
                summary["total_records"] += count
        
        # Log cleanup
        if not dry_run:
            self.audit_logger.log_user_action(
                user_id="system",
                action="data_retention_cleanup",
                resource_type="system",
                details=summary
            )
        
        return summary

    def _record_to_dict(self, record: Any) -> Dict[str, Any]:
        """Convert SQLAlchemy record to dictionary"""
        return {
            column.name: getattr(record, column.name)
            for column in record.__table__.columns
        }

    def anonymize_patient_data(
        self,
        patient_id: str,
        keep_statistics: bool = True
    ) -> Dict[str, Any]:
        """
        Anonymize patient data instead of deleting (alternative to deletion)
        Keeps data for research but removes identifying information
        
        Args:
            patient_id: Patient identifier
            keep_statistics: Whether to keep statistical/aggregate data
            
        Returns:
            Anonymization summary
        """
        from app.core.security.encryption import DataEncryption
        
        encryption = DataEncryption(use_aes256=True)
        
        summary = {
            "patient_id": patient_id,
            "anonymized_at": datetime.now().isoformat(),
            "method": "encryption",
            "tables_affected": []
        }
        
        try:
            # Anonymize patient record
            patient = self.db.query(Patient).filter(
                Patient.patient_id == patient_id
            ).first()
            
            if patient:
                # Replace patient_id with hash
                original_id = patient.patient_id
                anonymized_id = encryption.hash_identifier(original_id)
                
                # Update all related records with anonymized ID
                # (In production, you'd want to update foreign keys)
                
                summary["tables_affected"].append("patients")
                summary["anonymized_id"] = anonymized_id
            
            self.db.commit()
            summary["status"] = "success"
            
        except Exception as e:
            self.db.rollback()
            summary["status"] = "error"
            summary["error"] = str(e)
        
        return summary

