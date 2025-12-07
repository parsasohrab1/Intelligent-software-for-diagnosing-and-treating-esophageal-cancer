"""
Data masking and anonymization utilities for HIPAA/GDPR compliance
"""
from typing import Dict, Any, Optional, List
from enum import Enum
from app.core.security.rbac import Role
from app.core.security.encryption import DataEncryption


class MaskingLevel(str, Enum):
    """Data masking levels"""
    NONE = "none"  # No masking - full access
    PARTIAL = "partial"  # Partial masking (e.g., show last 4 digits)
    FULL = "full"  # Full masking (complete anonymization)
    AGGREGATE = "aggregate"  # Only aggregate statistics


class DataMasking:
    """Data masking and anonymization based on user role and consent"""

    # Define which fields should be masked for each role
    ROLE_MASKING_RULES: Dict[Role, Dict[str, MaskingLevel]] = {
        Role.DATA_SCIENTIST: {
            "patient_id": MaskingLevel.PARTIAL,
            "name": MaskingLevel.FULL,
            "email": MaskingLevel.FULL,
            "phone": MaskingLevel.FULL,
            "address": MaskingLevel.FULL,
            "ssn": MaskingLevel.FULL,
            "date_of_birth": MaskingLevel.PARTIAL,
        },
        Role.CLINICAL_RESEARCHER: {
            "patient_id": MaskingLevel.PARTIAL,
            "name": MaskingLevel.PARTIAL,
            "email": MaskingLevel.FULL,
            "phone": MaskingLevel.FULL,
            "address": MaskingLevel.FULL,
            "ssn": MaskingLevel.FULL,
            "date_of_birth": MaskingLevel.NONE,
        },
        Role.MEDICAL_ONCOLOGIST: {
            "patient_id": MaskingLevel.NONE,
            "name": MaskingLevel.NONE,
            "email": MaskingLevel.PARTIAL,
            "phone": MaskingLevel.PARTIAL,
            "address": MaskingLevel.PARTIAL,
            "ssn": MaskingLevel.FULL,
            "date_of_birth": MaskingLevel.NONE,
        },
        Role.DATA_ENGINEER: {
            "patient_id": MaskingLevel.NONE,
            "name": MaskingLevel.NONE,
            "email": MaskingLevel.NONE,
            "phone": MaskingLevel.NONE,
            "address": MaskingLevel.NONE,
            "ssn": MaskingLevel.PARTIAL,
            "date_of_birth": MaskingLevel.NONE,
        },
        Role.SYSTEM_ADMINISTRATOR: {
            "patient_id": MaskingLevel.NONE,
            "name": MaskingLevel.NONE,
            "email": MaskingLevel.NONE,
            "phone": MaskingLevel.NONE,
            "address": MaskingLevel.NONE,
            "ssn": MaskingLevel.NONE,
            "date_of_birth": MaskingLevel.NONE,
        },
        Role.ETHICS_COMMITTEE: {
            "patient_id": MaskingLevel.PARTIAL,
            "name": MaskingLevel.FULL,
            "email": MaskingLevel.FULL,
            "phone": MaskingLevel.FULL,
            "address": MaskingLevel.FULL,
            "ssn": MaskingLevel.FULL,
            "date_of_birth": MaskingLevel.PARTIAL,
        },
    }

    def __init__(self):
        self.encryption = DataEncryption(use_aes256=True)

    def mask_patient_data(
        self, 
        data: Dict[str, Any], 
        user_role: Role,
        has_consent: bool = False
    ) -> Dict[str, Any]:
        """
        Mask patient data based on user role and consent
        
        Args:
            data: Patient data dictionary
            user_role: User's role
            has_consent: Whether patient has given consent for data access
            
        Returns:
            Masked data dictionary
        """
        if not has_consent and user_role not in [Role.MEDICAL_ONCOLOGIST, Role.SYSTEM_ADMINISTRATOR]:
            # Without consent, apply full masking for most roles
            return self._apply_full_masking(data)
        
        # Get masking rules for role
        masking_rules = self.ROLE_MASKING_RULES.get(user_role, {})
        
        masked_data = {}
        for key, value in data.items():
            if value is None:
                masked_data[key] = None
                continue
                
            # Get masking level for this field
            masking_level = masking_rules.get(key.lower(), MaskingLevel.NONE)
            
            if masking_level == MaskingLevel.NONE:
                masked_data[key] = value
            elif masking_level == MaskingLevel.FULL:
                masked_data[key] = self._mask_value(key, value, show_last=0)
            elif masking_level == MaskingLevel.PARTIAL:
                masked_data[key] = self._mask_value(key, value, show_last=4)
            elif masking_level == MaskingLevel.AGGREGATE:
                # For aggregate, only include statistical data
                if key in ["age", "bmi", "tumor_length_cm"]:
                    masked_data[key] = value
                else:
                    masked_data[key] = None
            else:
                masked_data[key] = value
        
        return masked_data

    def _mask_value(self, field_name: str, value: Any, show_last: int = 0) -> str:
        """Mask a single value"""
        if value is None:
            return None
        
        value_str = str(value)
        
        # Special handling for different field types
        if field_name.lower() in ["email", "phone", "phone_number"]:
            # For email: mask@domain.com -> m***@d***.com
            if "@" in value_str:
                parts = value_str.split("@")
                if len(parts) == 2:
                    local = parts[0]
                    domain = parts[1]
                    masked_local = local[0] + "*" * (len(local) - 1) if len(local) > 1 else "*"
                    masked_domain = domain[0] + "*" * (len(domain) - 1) if len(domain) > 1 else "*"
                    return f"{masked_local}@{masked_domain}"
            
            # For phone: (123) 456-7890 -> (***) ***-7890
            if len(value_str) > show_last:
                return "*" * (len(value_str) - show_last) + value_str[-show_last:]
            return "*" * len(value_str)
        
        # For other fields
        if len(value_str) > show_last:
            return "*" * (len(value_str) - show_last) + value_str[-show_last:]
        return "*" * len(value_str)

    def _apply_full_masking(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply full masking to all sensitive fields"""
        masked = {}
        sensitive_fields = DataEncryption.PHI_FIELDS
        
        for key, value in data.items():
            if any(field.lower() == key.lower() for field in sensitive_fields):
                masked[key] = "***REDACTED***"
            else:
                masked[key] = value
        
        return masked

    def anonymize_patient_id(self, patient_id: str, salt: Optional[str] = None) -> str:
        """Create anonymized patient ID"""
        return self.encryption.hash_identifier(patient_id, salt)

    def deidentify_dataset(
        self, 
        dataset: List[Dict[str, Any]], 
        user_role: Role,
        has_consent: bool = False
    ) -> List[Dict[str, Any]]:
        """
        De-identify an entire dataset
        
        Args:
            dataset: List of patient records
            user_role: User's role
            has_consent: Whether consent has been obtained
            
        Returns:
            De-identified dataset
        """
        deidentified = []
        for record in dataset:
            masked_record = self.mask_patient_data(record, user_role, has_consent)
            
            # Replace patient_id with anonymized version
            if "patient_id" in masked_record:
                original_id = record.get("patient_id")
                if original_id:
                    masked_record["patient_id"] = self.anonymize_patient_id(str(original_id))
                    masked_record["original_patient_id_hash"] = self.encryption.hash_identifier(str(original_id))
            
            deidentified.append(masked_record)
        
        return deidentified

