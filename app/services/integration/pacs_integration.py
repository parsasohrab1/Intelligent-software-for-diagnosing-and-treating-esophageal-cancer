"""
PACS (Picture Archiving and Communication System) Integration
یکپارچه‌سازی با سیستم‌های PACS برای دریافت و ارسال تصاویر DICOM
"""
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import pydicom
try:
    from pynetdicom import AE, evt
except ImportError:
    AE = None
    evt = None
try:
    from pynetdicom.sop_class import (
        PatientRootQueryRetrieveInformationModelFind,
        PatientRootQueryRetrieveInformationModelMove,
        CTImageStorage,
        MRImageStorage,
        UltrasoundImageStorage,
        SecondaryCaptureImageStorage,
    )
except ImportError:
    PatientRootQueryRetrieveInformationModelFind = None
    PatientRootQueryRetrieveInformationModelMove = None
    CTImageStorage = None
    MRImageStorage = None
    UltrasoundImageStorage = None
    SecondaryCaptureImageStorage = None

logger = logging.getLogger(__name__)


class DICOMService(str, Enum):
    """سرویس‌های DICOM"""
    C_STORE = "c_store"  # Store images
    C_FIND = "c_find"  # Query/Find
    C_MOVE = "c_move"  # Move images
    C_GET = "c_get"  # Get images


@dataclass
class PACSConnection:
    """اطلاعات اتصال PACS"""
    host: str
    port: int
    ae_title: str  # Application Entity Title
    use_tls: bool = False
    timeout: int = 30


class PACSIntegration:
    """یکپارچه‌سازی با PACS"""

    def __init__(self, connection: PACSConnection):
        self.connection = connection
        self.ae = None
        self._initialize_ae()

    def _initialize_ae(self):
        """Initialize Application Entity"""
        if AE is None:
            logger.warning("pynetdicom not available, PACS integration disabled")
            return
        try:
            self.ae = AE(ae_title=self.connection.ae_title)
            
            # Add supported storage SOP classes
            if CTImageStorage:
                self.ae.add_supported_context(CTImageStorage)
            if MRImageStorage:
                self.ae.add_supported_context(MRImageStorage)
            if UltrasoundImageStorage:
                self.ae.add_supported_context(UltrasoundImageStorage)
            if SecondaryCaptureImageStorage:
                self.ae.add_supported_context(SecondaryCaptureImageStorage)
            
            # Add query/retrieve SOP classes
            if PatientRootQueryRetrieveInformationModelFind:
                self.ae.add_requested_context(PatientRootQueryRetrieveInformationModelFind)
            if PatientRootQueryRetrieveInformationModelMove:
                self.ae.add_requested_context(PatientRootQueryRetrieveInformationModelMove)
            
            logger.info(f"PACS AE initialized: {self.connection.ae_title}")
        except Exception as e:
            logger.error(f"Error initializing PACS AE: {str(e)}")
            raise

    def store_image(self, dicom_file_path: str) -> Dict:
        """
        Store DICOM image to PACS (C-STORE)
        
        Args:
            dicom_file_path: مسیر فایل DICOM
            
        Returns:
            نتیجه ذخیره‌سازی
        """
        try:
            # Read DICOM file
            ds = pydicom.dcmread(dicom_file_path)
            
            # Associate with PACS
            assoc = self.ae.associate(
                self.connection.host,
                self.connection.port,
                ae_title=self.connection.ae_title
            )
            
            if not assoc.is_established:
                raise Exception(f"Failed to associate with PACS: {assoc.release_reason}")
            
            # Send C-STORE request
            status = assoc.send_c_store(ds)
            
            # Release association
            assoc.release()
            
            if status:
                logger.info(f"Successfully stored DICOM image: {dicom_file_path}")
                return {
                    "success": True,
                    "patient_id": getattr(ds, "PatientID", None),
                    "study_instance_uid": getattr(ds, "StudyInstanceUID", None),
                    "series_instance_uid": getattr(ds, "SeriesInstanceUID", None),
                    "sop_instance_uid": getattr(ds, "SOPInstanceUID", None),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise Exception("C-STORE failed")
                
        except Exception as e:
            logger.error(f"Error storing DICOM image: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def find_studies(
        self,
        patient_id: Optional[str] = None,
        study_date: Optional[str] = None,
        modality: Optional[str] = None
    ) -> List[Dict]:
        """
        Query PACS for studies (C-FIND)
        
        Args:
            patient_id: شناسه بیمار
            study_date: تاریخ مطالعه
            modality: نوع تصویربرداری
            
        Returns:
            لیست مطالعات
        """
        try:
            # Create query dataset
            query_ds = pydicom.Dataset()
            query_ds.QueryRetrieveLevel = "STUDY"
            
            if patient_id:
                query_ds.PatientID = patient_id
            if study_date:
                query_ds.StudyDate = study_date
            if modality:
                query_ds.Modality = modality
            
            # Associate with PACS
            assoc = self.ae.associate(
                self.connection.host,
                self.connection.port,
                ae_title=self.connection.ae_title
            )
            
            if not assoc.is_established:
                raise Exception(f"Failed to associate with PACS: {assoc.release_reason}")
            
            # Send C-FIND request
            responses = assoc.send_c_find(query_ds, PatientRootQueryRetrieveInformationModelFind)
            
            studies = []
            for (status, identifier) in responses:
                if status and identifier:
                    study = {
                        "patient_id": getattr(identifier, "PatientID", None),
                        "patient_name": getattr(identifier, "PatientName", None),
                        "study_instance_uid": getattr(identifier, "StudyInstanceUID", None),
                        "study_date": getattr(identifier, "StudyDate", None),
                        "study_time": getattr(identifier, "StudyTime", None),
                        "modality": getattr(identifier, "ModalitiesInStudy", None),
                        "study_description": getattr(identifier, "StudyDescription", None),
                        "number_of_series": getattr(identifier, "NumberOfStudyRelatedSeries", None),
                    }
                    studies.append(study)
            
            # Release association
            assoc.release()
            
            logger.info(f"Found {len(studies)} studies")
            return studies
            
        except Exception as e:
            logger.error(f"Error finding studies: {str(e)}")
            return []

    def move_study(
        self,
        study_instance_uid: str,
        destination_ae_title: Optional[str] = None
    ) -> Dict:
        """
        Move study from PACS (C-MOVE)
        
        Args:
            study_instance_uid: Study Instance UID
            destination_ae_title: عنوان AE مقصد (اگر None، به خود سیستم)
            
        Returns:
            نتیجه انتقال
        """
        try:
            # Create move request
            move_ds = pydicom.Dataset()
            move_ds.QueryRetrieveLevel = "STUDY"
            move_ds.StudyInstanceUID = study_instance_uid
            
            destination = destination_ae_title or self.connection.ae_title
            
            # Associate with PACS
            assoc = self.ae.associate(
                self.connection.host,
                self.connection.port,
                ae_title=self.connection.ae_title
            )
            
            if not assoc.is_established:
                raise Exception(f"Failed to associate with PACS: {assoc.release_reason}")
            
            # Send C-MOVE request
            responses = assoc.send_c_move(
                move_ds,
                destination,
                PatientRootQueryRetrieveInformationModelMove
            )
            
            # Process responses
            statuses = []
            for (status, identifier) in responses:
                if status:
                    statuses.append({
                        "status": str(status),
                        "identifier": str(identifier) if identifier else None
                    })
            
            # Release association
            assoc.release()
            
            return {
                "success": True,
                "study_instance_uid": study_instance_uid,
                "destination": destination,
                "responses": statuses,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error moving study: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def receive_image(self, dicom_file_path: str) -> Dict:
        """
        Receive DICOM image from PACS (as Storage SCP)
        
        Args:
            dicom_file_path: مسیر ذخیره فایل
            
        Returns:
            اطلاعات فایل دریافت شده
        """
        try:
            # This would be implemented as a Storage SCP
            # For now, return placeholder
            return {
                "success": True,
                "file_path": dicom_file_path,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error receiving image: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

