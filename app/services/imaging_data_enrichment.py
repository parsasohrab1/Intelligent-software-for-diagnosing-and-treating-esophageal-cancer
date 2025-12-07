"""
Imaging Data Enrichment Service
سرویس برای اضافه کردن داده‌های رادیولوژی و آندوسکوپی با تفسیر به بیماران موجود
"""
import logging
from typing import Dict, List, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
import random

from app.models.patient import Patient
from app.models.imaging_data import ImagingData

logger = logging.getLogger(__name__)


class ImagingDataEnrichment:
    """سرویس برای غنی‌سازی داده‌های تصویربرداری"""

    def __init__(self, db: Session):
        self.db = db

    def add_radiology_data(
        self,
        patient_id: str,
        modality: str = "CT_Chest_Abdomen",
        findings: Optional[str] = None,
        impression: Optional[str] = None,
        tumor_length_cm: Optional[float] = None,
        wall_thickness_cm: Optional[float] = None,
        lymph_nodes_positive: Optional[int] = None,
        contrast_used: bool = True,
        radiologist_id: Optional[str] = None,
        imaging_date: Optional[date] = None
    ) -> ImagingData:
        """
        اضافه کردن داده رادیولوژی برای یک بیمار
        
        Args:
            patient_id: شناسه بیمار
            modality: نوع تصویربرداری (CT_Chest_Abdomen, MRI, PET_CT, etc.)
            findings: یافته‌ها
            impression: تفسیر
            tumor_length_cm: طول تومور
            wall_thickness_cm: ضخامت دیواره
            lymph_nodes_positive: تعداد غدد لنفاوی مثبت
            contrast_used: استفاده از کنتراست
            radiologist_id: شناسه رادیولوژیست
            imaging_date: تاریخ تصویربرداری
            
        Returns:
            ImagingData object
        """
        try:
            # Check if patient exists
            patient = self.db.query(Patient).filter(Patient.patient_id == patient_id).first()
            if not patient:
                raise ValueError(f"Patient {patient_id} not found")

            # Create imaging data
            imaging_data = ImagingData(
                patient_id=patient_id,
                imaging_modality=modality,
                findings=findings,
                impression=impression,
                tumor_length_cm=tumor_length_cm,
                wall_thickness_cm=wall_thickness_cm,
                lymph_nodes_positive=lymph_nodes_positive,
                contrast_used=contrast_used,
                radiologist_id=radiologist_id or "RAD001",
                imaging_date=imaging_date or date.today()
            )

            self.db.add(imaging_data)
            self.db.commit()
            self.db.refresh(imaging_data)

            logger.info(f"Added radiology data for patient {patient_id}, modality: {modality}")
            return imaging_data

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding radiology data: {str(e)}")
            raise

    def add_endoscopy_data(
        self,
        patient_id: str,
        findings: Optional[str] = None,
        impression: Optional[str] = None,
        tumor_length_cm: Optional[float] = None,
        wall_thickness_cm: Optional[float] = None,
        lymph_nodes_positive: Optional[int] = None,
        endoscopist_id: Optional[str] = None,
        imaging_date: Optional[date] = None
    ) -> ImagingData:
        """
        اضافه کردن داده آندوسکوپی برای یک بیمار
        
        Args:
            patient_id: شناسه بیمار
            findings: یافته‌ها
            impression: تفسیر
            tumor_length_cm: طول تومور
            wall_thickness_cm: ضخامت دیواره
            lymph_nodes_positive: تعداد غدد لنفاوی مثبت
            endoscopist_id: شناسه آندوسکوپیست
            imaging_date: تاریخ آندوسکوپی
            
        Returns:
            ImagingData object
        """
        try:
            # Check if patient exists
            patient = self.db.query(Patient).filter(Patient.patient_id == patient_id).first()
            if not patient:
                raise ValueError(f"Patient {patient_id} not found")

            # Create endoscopy data
            imaging_data = ImagingData(
                patient_id=patient_id,
                imaging_modality="Endoscopy",
                findings=findings,
                impression=impression,
                tumor_length_cm=tumor_length_cm,
                wall_thickness_cm=wall_thickness_cm,
                lymph_nodes_positive=lymph_nodes_positive,
                contrast_used=False,  # Endoscopy doesn't use contrast
                radiologist_id=endoscopist_id or "END001",
                imaging_date=imaging_date or date.today()
            )

            self.db.add(imaging_data)
            self.db.commit()
            self.db.refresh(imaging_data)

            logger.info(f"Added endoscopy data for patient {patient_id}")
            return imaging_data

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding endoscopy data: {str(e)}")
            raise

    def enrich_all_patients(
        self,
        include_radiology: bool = True,
        include_endoscopy: bool = True,
        generate_interpretations: bool = True
    ) -> Dict[str, int]:
        """
        غنی‌سازی داده‌های تصویربرداری برای تمام بیماران
        
        Args:
            include_radiology: اضافه کردن داده رادیولوژی
            include_endoscopy: اضافه کردن داده آندوسکوپی
            generate_interpretations: تولید خودکار تفسیرها
            
        Returns:
            آمار عملیات
        """
        try:
            # Get all patients
            patients = self.db.query(Patient).all()
            total_patients = len(patients)
            
            radiology_count = 0
            endoscopy_count = 0
            errors = []

            for patient in patients:
                try:
                    # Check if patient already has imaging data
                    existing_imaging = self.db.query(ImagingData).filter(
                        ImagingData.patient_id == patient.patient_id
                    ).first()

                    # Add radiology data if requested and not exists
                    if include_radiology:
                        if not existing_imaging or existing_imaging.imaging_modality != "CT_Chest_Abdomen":
                            if generate_interpretations:
                                findings, impression = self._generate_radiology_interpretation(patient)
                            else:
                                findings = None
                                impression = None
                            
                            self.add_radiology_data(
                                patient_id=patient.patient_id,
                                modality="CT_Chest_Abdomen",
                                findings=findings,
                                impression=impression,
                                tumor_length_cm=self._generate_tumor_length(patient),
                                wall_thickness_cm=self._generate_wall_thickness(patient),
                                lymph_nodes_positive=self._generate_lymph_nodes(patient)
                            )
                            radiology_count += 1

                    # Add endoscopy data if requested and not exists
                    if include_endoscopy:
                        if not existing_imaging or existing_imaging.imaging_modality != "Endoscopy":
                            if generate_interpretations:
                                findings, impression = self._generate_endoscopy_interpretation(patient)
                            else:
                                findings = None
                                impression = None
                            
                            self.add_endoscopy_data(
                                patient_id=patient.patient_id,
                                findings=findings,
                                impression=impression,
                                tumor_length_cm=self._generate_tumor_length(patient),
                                wall_thickness_cm=self._generate_wall_thickness(patient),
                                lymph_nodes_positive=self._generate_lymph_nodes(patient)
                            )
                            endoscopy_count += 1

                except Exception as e:
                    error_msg = f"Error enriching patient {patient.patient_id}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            return {
                "total_patients": total_patients,
                "radiology_added": radiology_count,
                "endoscopy_added": endoscopy_count,
                "errors": len(errors),
                "error_details": errors[:10]  # First 10 errors
            }

        except Exception as e:
            logger.error(f"Error enriching all patients: {str(e)}")
            raise

    def _generate_radiology_interpretation(self, patient: Patient) -> tuple[str, str]:
        """تولید خودکار تفسیر رادیولوژی"""
        if patient.has_cancer:
            findings = (
                f"Mass lesion identified in the esophagus. "
                f"Tumor length approximately {random.uniform(2.0, 8.0):.1f} cm. "
                f"Wall thickening noted. Regional lymphadenopathy present. "
                f"Contrast enhancement observed in the lesion."
            )
            impression = (
                f"Findings consistent with esophageal {patient.cancer_type or 'carcinoma'}. "
                f"Recommend further evaluation with endoscopy and biopsy for confirmation. "
                f"Staging assessment recommended."
            )
        else:
            findings = (
                f"Normal esophageal wall thickness. No mass lesions identified. "
                f"No significant lymphadenopathy. Normal contrast enhancement pattern."
            )
            impression = (
                f"No evidence of esophageal malignancy. Normal radiological appearance. "
                f"Clinical correlation recommended."
            )
        
        return findings, impression

    def _generate_endoscopy_interpretation(self, patient: Patient) -> tuple[str, str]:
        """تولید خودکار تفسیر آندوسکوپی"""
        if patient.has_cancer:
            findings = (
                f"Endoscopic examination reveals an irregular, ulcerated mass in the esophagus. "
                f"Tumor extends approximately {random.uniform(2.0, 8.0):.1f} cm. "
                f"Luminal narrowing observed. Biopsy performed from suspicious areas. "
                f"Vascular pattern abnormal in the lesion area."
            )
            impression = (
                f"Endoscopic findings highly suspicious for esophageal {patient.cancer_type or 'carcinoma'}. "
                f"Awaiting histopathological confirmation. "
                f"Recommend staging with additional imaging if not already performed."
            )
        else:
            findings = (
                f"Normal esophageal mucosa. No visible lesions or masses. "
                f"Normal vascular pattern. No luminal narrowing. "
                f"Biopsy performed from normal appearing mucosa for screening purposes."
            )
            impression = (
                f"Normal endoscopic appearance. No evidence of malignancy. "
                f"Histopathology pending for confirmation."
            )
        
        return findings, impression

    def _generate_tumor_length(self, patient: Patient) -> Optional[float]:
        """تولید طول تومور"""
        if patient.has_cancer:
            return round(random.uniform(2.0, 8.0), 1)
        return None

    def _generate_wall_thickness(self, patient: Patient) -> Optional[float]:
        """تولید ضخامت دیواره"""
        if patient.has_cancer:
            return round(random.uniform(0.8, 2.5), 1)
        return round(random.uniform(0.3, 0.6), 1)

    def _generate_lymph_nodes(self, patient: Patient) -> Optional[int]:
        """تولید تعداد غدد لنفاوی"""
        if patient.has_cancer:
            return random.randint(0, 5)
        return 0

