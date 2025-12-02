"""
Data encryption utilities
"""
from cryptography.fernet import Fernet
from typing import Optional
import base64
import os
from app.core.config import settings


class DataEncryption:
    """Encrypt and decrypt sensitive data"""

    def __init__(self, key: Optional[bytes] = None):
        if key is None:
            # Generate or load key from settings
            key_str = getattr(settings, "ENCRYPTION_KEY", None)
            if key_str:
                self.key = key_str.encode()
            else:
                # Generate new key (should be stored securely in production)
                self.key = Fernet.generate_key()
        else:
            self.key = key

        self.cipher = Fernet(self.key)

    def encrypt(self, data: str) -> str:
        """Encrypt data"""
        if isinstance(data, str):
            data = data.encode()
        encrypted = self.cipher.encrypt(data)
        return base64.b64encode(encrypted).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data"""
        encrypted_bytes = base64.b64decode(encrypted_data.encode())
        decrypted = self.cipher.decrypt(encrypted_bytes)
        return decrypted.decode()

    def encrypt_dict(self, data: Dict) -> Dict:
        """Encrypt sensitive fields in a dictionary"""
        import json

        encrypted = {}
        sensitive_fields = [
            "patient_id",
            "name",
            "email",
            "phone",
            "address",
            "ssn",
            "medical_record_number",
        ]

        for key, value in data.items():
            if key.lower() in sensitive_fields and value:
                encrypted[key] = self.encrypt(str(value))
            else:
                encrypted[key] = value

        return encrypted

    def decrypt_dict(self, encrypted_data: Dict) -> Dict:
        """Decrypt sensitive fields in a dictionary"""
        decrypted = {}
        sensitive_fields = [
            "patient_id",
            "name",
            "email",
            "phone",
            "address",
            "ssn",
            "medical_record_number",
        ]

        for key, value in encrypted_data.items():
            if key.lower() in sensitive_fields and value:
                try:
                    decrypted[key] = self.decrypt(str(value))
                except:
                    decrypted[key] = value  # If decryption fails, keep original
            else:
                decrypted[key] = value

        return decrypted

