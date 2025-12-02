"""
Data de-identification module
"""
import hashlib
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
import pandas as pd


class DataDeidentifier:
    """De-identify sensitive patient data"""

    # Direct identifiers to remove
    DIRECT_IDENTIFIERS = [
        "name",
        "first_name",
        "last_name",
        "address",
        "phone",
        "email",
        "social_security_number",
        "ssn",
        "medical_record_number",
        "mrn",
        "patient_name",
        "full_name",
    ]

    # Quasi-identifiers to generalize
    QUASI_IDENTIFIERS = ["age", "zip_code", "date_of_birth", "birth_date"]

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)

    def deidentify_patient_data(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove or mask all personally identifiable information"""
        deidentified = patient_data.copy()

        # Remove direct identifiers
        for identifier in self.DIRECT_IDENTIFIERS:
            if identifier in deidentified:
                del deidentified[identifier]

        # Generalize quasi-identifiers
        if "age" in deidentified:
            # Age generalization: round to nearest 5 years
            age = deidentified["age"]
            deidentified["age_group"] = (age // 5) * 5
            del deidentified["age"]

        if "zip_code" in deidentified:
            # ZIP code generalization: first 3 digits only
            zip_code = str(deidentified["zip_code"])
            deidentified["zip_code"] = zip_code[:3] if len(zip_code) >= 3 else "000"

        if "date_of_birth" in deidentified or "birth_date" in deidentified:
            # Shift birth date by random offset (preserving age distribution)
            birth_date_key = "date_of_birth" if "date_of_birth" in deidentified else "birth_date"
            birth_date = deidentified[birth_date_key]

            if isinstance(birth_date, str):
                try:
                    birth_date = datetime.strptime(birth_date, "%Y-%m-%d")
                except:
                    pass

            if isinstance(birth_date, datetime):
                offset = random.randint(-30, 30)
                shifted_date = birth_date + timedelta(days=offset)
                deidentified[birth_date_key] = shifted_date.strftime("%Y-%m-%d")

        # Generate synthetic identifier
        patient_hash = hashlib.sha256(
            f"{str(patient_data)}{random.getrandbits(128)}".encode()
        ).hexdigest()[:16]
        deidentified["patient_hash"] = patient_hash

        return deidentified

    def deidentify_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """De-identify a pandas DataFrame"""
        deidentified_df = df.copy()

        # Remove direct identifier columns
        columns_to_remove = [
            col for col in deidentified_df.columns if col.lower() in self.DIRECT_IDENTIFIERS
        ]
        deidentified_df = deidentified_df.drop(columns=columns_to_remove, errors="ignore")

        # Generalize quasi-identifiers
        if "age" in deidentified_df.columns:
            deidentified_df["age_group"] = (deidentified_df["age"] // 5) * 5
            deidentified_df = deidentified_df.drop(columns=["age"])

        if "zip_code" in deidentified_df.columns:
            deidentified_df["zip_code"] = deidentified_df["zip_code"].astype(str).str[:3]

        # Generate hash identifiers
        if "patient_id" in deidentified_df.columns:
            deidentified_df["patient_hash"] = deidentified_df["patient_id"].apply(
                lambda x: hashlib.sha256(f"{x}{self.seed}".encode()).hexdigest()[:16]
            )

        return deidentified_df

    def verify_deidentification(self, data: Dict[str, Any]) -> Dict[str, bool]:
        """Verify that data is properly de-identified"""
        verification = {
            "no_direct_identifiers": True,
            "quasi_identifiers_generalized": True,
            "has_hash_identifier": False,
        }

        # Check for direct identifiers
        for identifier in self.DIRECT_IDENTIFIERS:
            if identifier in data:
                verification["no_direct_identifiers"] = False
                break

        # Check for quasi-identifier generalization
        if "age" in data and "age_group" not in data:
            verification["quasi_identifiers_generalized"] = False

        # Check for hash identifier
        if "patient_hash" in data or "patient_id" in data:
            verification["has_hash_identifier"] = True

        return verification

