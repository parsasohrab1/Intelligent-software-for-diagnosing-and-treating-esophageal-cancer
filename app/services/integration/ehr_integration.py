"""
EHR (Electronic Health Records) Integration
یکپارچه‌سازی با سیستم‌های EHR با استفاده از HL7 FHIR
"""
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)


class EHRSystemType(str, Enum):
    """انواع سیستم‌های EHR"""
    EPIC = "epic"
    CERNER = "cerner"
    ALLSCRIPTS = "allscripts"
    ATHENAHEALTH = "athenahealth"
    GENERIC_FHIR = "generic_fhir"
    HL7_V2 = "hl7_v2"


@dataclass
class EHRConnection:
    """اطلاعات اتصال EHR"""
    system_type: EHRSystemType
    fhir_base_url: Optional[str] = None
    api_key: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    hl7_endpoint: Optional[str] = None
    use_oauth: bool = True


class EHRIntegration:
    """یکپارچه‌سازی با سیستم EHR"""

    def __init__(self, connection: EHRConnection):
        self.connection = connection
        self.system_type = connection.system_type
        self.access_token: Optional[str] = None

    def authenticate(self) -> bool:
        """
        احراز هویت با سیستم EHR
        
        Returns:
            True if successful
        """
        try:
            if self.connection.use_oauth and self.connection.client_id:
                # OAuth 2.0 authentication
                self.access_token = self._get_oauth_token()
                return self.access_token is not None
            elif self.connection.api_key:
                # API key authentication
                self.access_token = self.connection.api_key
                return True
            else:
                logger.warning("No authentication method configured")
                return False
        except Exception as e:
            logger.error(f"Error authenticating with EHR: {str(e)}")
            return False

    def _get_oauth_token(self) -> Optional[str]:
        """دریافت OAuth token"""
        try:
            import requests
            
            token_url = f"{self.connection.fhir_base_url}/oauth/token"
            
            response = requests.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.connection.client_id,
                    "client_secret": self.connection.client_secret
                },
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                return token_data.get("access_token")
            else:
                logger.error(f"OAuth token request failed: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting OAuth token: {str(e)}")
            return None

    def get_patient(self, patient_id: str) -> Optional[Dict]:
        """
        دریافت اطلاعات بیمار از EHR (FHIR Patient)
        
        Args:
            patient_id: شناسه بیمار
            
        Returns:
            اطلاعات بیمار در فرمت FHIR
        """
        try:
            if not self.authenticate():
                return None
            
            if self.system_type in [EHRSystemType.EPIC, EHRSystemType.CERNER, EHRSystemType.GENERIC_FHIR]:
                return self._get_fhir_patient(patient_id)
            else:
                return self._get_hl7_patient(patient_id)
                
        except Exception as e:
            logger.error(f"Error getting patient: {str(e)}")
            return None

    def _get_fhir_patient(self, patient_id: str) -> Optional[Dict]:
        """دریافت بیمار از FHIR API"""
        try:
            import requests
            
            url = f"{self.connection.fhir_base_url}/Patient/{patient_id}"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/fhir+json"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"FHIR request failed: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting FHIR patient: {str(e)}")
            return None

    def _get_hl7_patient(self, patient_id: str) -> Optional[Dict]:
        """دریافت بیمار از HL7 v2"""
        # Implementation for HL7 v2
        return None

    def create_observation(
        self,
        patient_id: str,
        observation_data: Dict
    ) -> Optional[Dict]:
        """
        ایجاد Observation در EHR (FHIR Observation)
        
        Args:
            patient_id: شناسه بیمار
            observation_data: داده‌های observation
            
        Returns:
            Observation ایجاد شده
        """
        try:
            if not self.authenticate():
                return None
            
            # Create FHIR Observation resource
            observation = {
                "resourceType": "Observation",
                "status": "final",
                "subject": {
                    "reference": f"Patient/{patient_id}"
                },
                "code": {
                    "coding": [{
                        "system": observation_data.get("code_system", "http://loinc.org"),
                        "code": observation_data.get("code"),
                        "display": observation_data.get("display")
                    }]
                },
                "valueQuantity": {
                    "value": observation_data.get("value"),
                    "unit": observation_data.get("unit"),
                    "system": "http://unitsofmeasure.org",
                    "code": observation_data.get("unit_code")
                },
                "effectiveDateTime": datetime.now().isoformat()
            }
            
            # Send to EHR
            import requests
            
            url = f"{self.connection.fhir_base_url}/Observation"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/fhir+json"
            }
            
            response = requests.post(url, json=observation, headers=headers, timeout=10)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"Failed to create observation: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating observation: {str(e)}")
            return None

    def create_diagnostic_report(
        self,
        patient_id: str,
        report_data: Dict
    ) -> Optional[Dict]:
        """
        ایجاد Diagnostic Report در EHR (FHIR DiagnosticReport)
        
        Args:
            patient_id: شناسه بیمار
            report_data: داده‌های گزارش
            
        Returns:
            Diagnostic Report ایجاد شده
        """
        try:
            if not self.authenticate():
                return None
            
            # Create FHIR DiagnosticReport resource
            diagnostic_report = {
                "resourceType": "DiagnosticReport",
                "status": "final",
                "subject": {
                    "reference": f"Patient/{patient_id}"
                },
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": report_data.get("code", "11526-1"),
                        "display": report_data.get("display", "Pathology report")
                    }]
                },
                "effectiveDateTime": report_data.get("effective_date", datetime.now().isoformat()),
                "issued": datetime.now().isoformat(),
                "conclusion": report_data.get("conclusion"),
                "conclusionCode": report_data.get("conclusion_codes", [])
            }
            
            # Send to EHR
            import requests
            
            url = f"{self.connection.fhir_base_url}/DiagnosticReport"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/fhir+json"
            }
            
            response = requests.post(url, json=diagnostic_report, headers=headers, timeout=10)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"Failed to create diagnostic report: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating diagnostic report: {str(e)}")
            return None

    def search_patients(
        self,
        name: Optional[str] = None,
        birth_date: Optional[str] = None,
        identifier: Optional[str] = None
    ) -> List[Dict]:
        """
        جستجوی بیماران در EHR (FHIR Patient Search)
        
        Args:
            name: نام بیمار
            birth_date: تاریخ تولد
            identifier: شناسه
            
        Returns:
            لیست بیماران
        """
        try:
            if not self.authenticate():
                return []
            
            import requests
            
            url = f"{self.connection.fhir_base_url}/Patient"
            params = {}
            
            if name:
                params["name"] = name
            if birth_date:
                params["birthdate"] = birth_date
            if identifier:
                params["identifier"] = identifier
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/fhir+json"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                bundle = response.json()
                patients = []
                
                if bundle.get("resourceType") == "Bundle" and "entry" in bundle:
                    for entry in bundle["entry"]:
                        if entry.get("resource", {}).get("resourceType") == "Patient":
                            patients.append(entry["resource"])
                
                return patients
            else:
                logger.error(f"Patient search failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching patients: {str(e)}")
            return []

    def get_patient_observations(
        self,
        patient_id: str,
        observation_type: Optional[str] = None
    ) -> List[Dict]:
        """
        دریافت Observations یک بیمار
        
        Args:
            patient_id: شناسه بیمار
            observation_type: نوع observation (اختیاری)
            
        Returns:
            لیست observations
        """
        try:
            if not self.authenticate():
                return []
            
            import requests
            
            url = f"{self.connection.fhir_base_url}/Observation"
            params = {"subject": f"Patient/{patient_id}"}
            
            if observation_type:
                params["code"] = observation_type
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/fhir+json"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                bundle = response.json()
                observations = []
                
                if bundle.get("resourceType") == "Bundle" and "entry" in bundle:
                    for entry in bundle["entry"]:
                        if entry.get("resource", {}).get("resourceType") == "Observation":
                            observations.append(entry["resource"])
                
                return observations
            else:
                logger.error(f"Failed to get observations: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting observations: {str(e)}")
            return []

