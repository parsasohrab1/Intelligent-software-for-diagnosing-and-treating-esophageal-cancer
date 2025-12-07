"""
Integration Adapter Pattern
الگوی Adapter برای یکپارچه‌سازی با سیستم‌های مختلف
"""
import logging
from typing import Dict, Optional, List, Any, Protocol
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum

from app.services.integration.pacs_integration import PACSIntegration, PACSConnection
from app.services.integration.endoscopy_integration import EndoscopyIntegration, EndoscopyConnection
from app.services.integration.ehr_integration import EHRIntegration, EHRConnection

logger = logging.getLogger(__name__)


class IntegrationType(str, Enum):
    """انواع یکپارچه‌سازی"""
    PACS = "pacs"
    ENDOSCOPY = "endoscopy"
    EHR = "ehr"


class IntegrationAdapter(ABC):
    """Interface برای Adapterهای یکپارچه‌سازی"""

    @abstractmethod
    def connect(self) -> bool:
        """اتصال به سیستم"""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """قطع اتصال"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """بررسی وضعیت اتصال"""
        pass

    @abstractmethod
    def get_patient_data(self, patient_id: str) -> Optional[Dict]:
        """دریافت داده‌های بیمار"""
        pass

    @abstractmethod
    def send_results(self, patient_id: str, results: Dict) -> bool:
        """ارسال نتایج"""
        pass


class PACSAdapter(IntegrationAdapter):
    """Adapter برای PACS"""

    def __init__(self, connection: PACSConnection):
        self.connection = connection
        self.integration = PACSIntegration(connection)
        self.connected = False

    def connect(self) -> bool:
        """اتصال به PACS"""
        try:
            # PACS connection is established on-demand
            self.connected = True
            logger.info("PACS adapter connected")
            return True
        except Exception as e:
            logger.error(f"Error connecting to PACS: {str(e)}")
            return False

    def disconnect(self) -> bool:
        """قطع اتصال از PACS"""
        self.connected = False
        return True

    def is_connected(self) -> bool:
        """بررسی وضعیت اتصال"""
        return self.connected

    def get_patient_data(self, patient_id: str) -> Optional[Dict]:
        """دریافت داده‌های بیمار از PACS"""
        try:
            studies = self.integration.find_studies(patient_id=patient_id)
            return {
                "patient_id": patient_id,
                "studies": studies,
                "source": "pacs"
            }
        except Exception as e:
            logger.error(f"Error getting patient data from PACS: {str(e)}")
            return None

    def send_results(self, patient_id: str, results: Dict) -> bool:
        """ارسال نتایج به PACS"""
        try:
            # Store DICOM images with annotations
            if "dicom_path" in results:
                store_result = self.integration.store_image(results["dicom_path"])
                return store_result.get("success", False)
            return False
        except Exception as e:
            logger.error(f"Error sending results to PACS: {str(e)}")
            return False


class EndoscopyAdapter(IntegrationAdapter):
    """Adapter برای Endoscopy Software"""

    def __init__(self, connection: EndoscopyConnection):
        self.connection = connection
        self.integration = EndoscopyIntegration(connection)
        self.connected = False

    def connect(self) -> bool:
        """اتصال به سیستم آندوسکوپی"""
        try:
            self.connected = True
            logger.info("Endoscopy adapter connected")
            return True
        except Exception as e:
            logger.error(f"Error connecting to Endoscopy: {str(e)}")
            return False

    def disconnect(self) -> bool:
        """قطع اتصال"""
        self.connected = False
        return True

    def is_connected(self) -> bool:
        """بررسی وضعیت اتصال"""
        return self.connected

    def get_patient_data(self, patient_id: str) -> Optional[Dict]:
        """دریافت داده‌های بیمار از سیستم آندوسکوپی"""
        try:
            procedures = self.integration.get_patient_procedures(patient_id)
            return {
                "patient_id": patient_id,
                "procedures": procedures,
                "source": "endoscopy"
            }
        except Exception as e:
            logger.error(f"Error getting patient data from Endoscopy: {str(e)}")
            return None

    def send_results(self, patient_id: str, results: Dict) -> bool:
        """ارسال نتایج به سیستم آندوسکوپی"""
        try:
            procedure_id = results.get("procedure_id")
            if procedure_id:
                return self.integration.send_analysis_result(
                    procedure_id=procedure_id,
                    analysis_result=results.get("analysis", {}),
                    annotations=results.get("annotations", [])
                )
            return False
        except Exception as e:
            logger.error(f"Error sending results to Endoscopy: {str(e)}")
            return False


class EHRAdapter(IntegrationAdapter):
    """Adapter برای EHR"""

    def __init__(self, connection: EHRConnection):
        self.connection = connection
        self.integration = EHRIntegration(connection)
        self.connected = False

    def connect(self) -> bool:
        """اتصال به EHR"""
        try:
            self.connected = self.integration.authenticate()
            if self.connected:
                logger.info("EHR adapter connected")
            return self.connected
        except Exception as e:
            logger.error(f"Error connecting to EHR: {str(e)}")
            return False

    def disconnect(self) -> bool:
        """قطع اتصال"""
        self.connected = False
        return True

    def is_connected(self) -> bool:
        """بررسی وضعیت اتصال"""
        return self.connected

    def get_patient_data(self, patient_id: str) -> Optional[Dict]:
        """دریافت داده‌های بیمار از EHR"""
        try:
            patient = self.integration.get_patient(patient_id)
            observations = self.integration.get_patient_observations(patient_id)
            
            return {
                "patient_id": patient_id,
                "patient": patient,
                "observations": observations,
                "source": "ehr"
            }
        except Exception as e:
            logger.error(f"Error getting patient data from EHR: {str(e)}")
            return None

    def send_results(self, patient_id: str, results: Dict) -> bool:
        """ارسال نتایج به EHR"""
        try:
            # Create observation
            if "observation" in results:
                observation = self.integration.create_observation(
                    patient_id=patient_id,
                    observation_data=results["observation"]
                )
                if observation:
                    return True
            
            # Create diagnostic report
            if "diagnostic_report" in results:
                report = self.integration.create_diagnostic_report(
                    patient_id=patient_id,
                    report_data=results["diagnostic_report"]
                )
                if report:
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error sending results to EHR: {str(e)}")
            return False


class IntegrationManager:
    """مدیریت یکپارچه‌سازی با سیستم‌های مختلف"""

    def __init__(self):
        self.adapters: Dict[IntegrationType, IntegrationAdapter] = {}

    def register_adapter(
        self,
        integration_type: IntegrationType,
        adapter: IntegrationAdapter
    ):
        """ثبت adapter"""
        self.adapters[integration_type] = adapter
        logger.info(f"Registered adapter for {integration_type.value}")

    def connect_all(self) -> Dict[str, bool]:
        """اتصال به تمام سیستم‌ها"""
        results = {}
        for integration_type, adapter in self.adapters.items():
            try:
                results[integration_type.value] = adapter.connect()
            except Exception as e:
                logger.error(f"Error connecting {integration_type.value}: {str(e)}")
                results[integration_type.value] = False
        return results

    def disconnect_all(self) -> Dict[str, bool]:
        """قطع اتصال از تمام سیستم‌ها"""
        results = {}
        for integration_type, adapter in self.adapters.items():
            try:
                results[integration_type.value] = adapter.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting {integration_type.value}: {str(e)}")
                results[integration_type.value] = False
        return results

    def get_patient_data_from_all(self, patient_id: str) -> Dict[str, Optional[Dict]]:
        """دریافت داده‌های بیمار از تمام سیستم‌ها"""
        results = {}
        for integration_type, adapter in self.adapters.items():
            if adapter.is_connected():
                try:
                    data = adapter.get_patient_data(patient_id)
                    results[integration_type.value] = data
                except Exception as e:
                    logger.error(f"Error getting data from {integration_type.value}: {str(e)}")
                    results[integration_type.value] = None
            else:
                results[integration_type.value] = None
        return results

    def send_results_to_all(self, patient_id: str, results: Dict) -> Dict[str, bool]:
        """ارسال نتایج به تمام سیستم‌ها"""
        send_results = {}
        for integration_type, adapter in self.adapters.items():
            if adapter.is_connected():
                try:
                    success = adapter.send_results(patient_id, results)
                    send_results[integration_type.value] = success
                except Exception as e:
                    logger.error(f"Error sending to {integration_type.value}: {str(e)}")
                    send_results[integration_type.value] = False
            else:
                send_results[integration_type.value] = False
        return send_results

    def get_connection_status(self) -> Dict[str, bool]:
        """دریافت وضعیت اتصال تمام سیستم‌ها"""
        return {
            integration_type.value: adapter.is_connected()
            for integration_type, adapter in self.adapters.items()
        }

