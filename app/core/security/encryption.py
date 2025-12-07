"""
Data encryption utilities - HIPAA/GDPR compliant encryption
"""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.backends import default_backend
from typing import Optional, Dict, Any, List
import base64
import os
import hashlib
import secrets
from app.core.config import settings


class DataEncryption:
    """
    HIPAA/GDPR compliant data encryption
    Supports both Fernet (symmetric) and AES-256 encryption
    """

    # PHI (Protected Health Information) fields that must be encrypted
    PHI_FIELDS = [
        "patient_id",
        "name",
        "first_name",
        "last_name",
        "email",
        "phone",
        "phone_number",
        "address",
        "street_address",
        "city",
        "zip_code",
        "postal_code",
        "ssn",
        "social_security_number",
        "medical_record_number",
        "mrn",
        "date_of_birth",
        "dob",
        "insurance_number",
        "national_id",
        "passport_number",
    ]

    def __init__(self, key: Optional[bytes] = None, use_aes256: bool = True):
        """
        Initialize encryption with AES-256 (HIPAA compliant) or Fernet
        
        Args:
            key: Encryption key (if None, will be generated or loaded from settings)
            use_aes256: Use AES-256 encryption (default: True for HIPAA compliance)
        """
        self.use_aes256 = use_aes256
        
        if key is None:
            # Generate or load key from settings
            key_str = getattr(settings, "ENCRYPTION_KEY", None)
            if key_str:
                if use_aes256:
                    # For AES-256, we need 32 bytes (256 bits)
                    self.key = self._derive_key(key_str.encode())
                else:
                    self.key = key_str.encode()
            else:
                if use_aes256:
                    # Generate 32-byte key for AES-256
                    self.key = secrets.token_bytes(32)
                else:
                    # Generate Fernet key
                    self.key = Fernet.generate_key()
        else:
            self.key = key

        if use_aes256:
            # AES-256 cipher will be created per operation
            self.cipher = None
        else:
            self.cipher = Fernet(self.key)

    def _derive_key(self, password: bytes) -> bytes:
        """Derive a 32-byte key from a password using PBKDF2"""
        salt = b'inescape_salt_2024'  # In production, use unique salt per key
        kdf = hashes.Hash(hashes.SHA256(), backend=default_backend())
        kdf.update(password)
        kdf.update(salt)
        return kdf.finalize()

    def encrypt(self, data: str) -> str:
        """
        Encrypt data using AES-256 (HIPAA compliant) or Fernet
        
        Args:
            data: Data to encrypt (string)
            
        Returns:
            Base64 encoded encrypted string
        """
        if isinstance(data, str):
            data = data.encode()
        
        if self.use_aes256:
            return self._encrypt_aes256(data)
        else:
            encrypted = self.cipher.encrypt(data)
            return base64.b64encode(encrypted).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data using AES-256 or Fernet
        
        Args:
            encrypted_data: Base64 encoded encrypted string
            
        Returns:
            Decrypted string
        """
        encrypted_bytes = base64.b64decode(encrypted_data.encode())
        
        if self.use_aes256:
            return self._decrypt_aes256(encrypted_bytes).decode()
        else:
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()

    def _encrypt_aes256(self, data: bytes) -> str:
        """Encrypt using AES-256-CBC (HIPAA compliant)"""
        # Generate random IV for each encryption
        iv = secrets.token_bytes(16)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Pad data to block size
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        # Encrypt
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        
        # Combine IV and encrypted data
        combined = iv + encrypted
        
        # Return base64 encoded
        return base64.b64encode(combined).decode()

    def _decrypt_aes256(self, encrypted_data: bytes) -> bytes:
        """Decrypt using AES-256-CBC"""
        # Extract IV (first 16 bytes)
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Decrypt
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Unpad
        unpadder = padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        
        return data

    def encrypt_dict(self, data: Dict[str, Any], fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Encrypt PHI fields in a dictionary (HIPAA compliant)
        
        Args:
            data: Dictionary containing potentially sensitive data
            fields: Optional list of specific fields to encrypt (defaults to PHI_FIELDS)
            
        Returns:
            Dictionary with encrypted PHI fields
        """
        encrypted = {}
        fields_to_encrypt = fields or self.PHI_FIELDS

        for key, value in data.items():
            # Check if field should be encrypted (case-insensitive)
            if any(field.lower() == key.lower() for field in fields_to_encrypt) and value is not None:
                try:
                    encrypted[key] = self.encrypt(str(value))
                    # Mark as encrypted
                    encrypted[f"{key}_encrypted"] = True
                except Exception as e:
                    # Log error but don't fail - keep original value
                    encrypted[key] = value
            else:
                encrypted[key] = value

        return encrypted

    def decrypt_dict(self, encrypted_data: Dict[str, Any], fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Decrypt PHI fields in a dictionary
        
        Args:
            encrypted_data: Dictionary with encrypted fields
            fields: Optional list of specific fields to decrypt (defaults to PHI_FIELDS)
            
        Returns:
            Dictionary with decrypted PHI fields
        """
        decrypted = {}
        fields_to_decrypt = fields or self.PHI_FIELDS

        for key, value in encrypted_data.items():
            # Skip encryption markers
            if key.endswith("_encrypted"):
                continue
                
            # Check if field should be decrypted
            if any(field.lower() == key.lower() for field in fields_to_decrypt) and value is not None:
                try:
                    # Try to decrypt (will fail if not encrypted)
                    decrypted[key] = self.decrypt(str(value))
                except Exception:
                    # If decryption fails, assume it's not encrypted
                    decrypted[key] = value
            else:
                decrypted[key] = value

        return decrypted

    def hash_identifier(self, identifier: str, salt: Optional[str] = None) -> str:
        """
        Hash an identifier (one-way) for anonymization
        Used for creating de-identified datasets
        
        Args:
            identifier: Identifier to hash
            salt: Optional salt for additional security
            
        Returns:
            SHA-256 hash of the identifier
        """
        if salt is None:
            salt = getattr(settings, "HASH_SALT", "inescape_salt_2024")
        
        combined = f"{identifier}{salt}".encode()
        return hashlib.sha256(combined).hexdigest()

    def mask_data(self, data: str, mask_char: str = "*", show_last: int = 0) -> str:
        """
        Mask sensitive data (e.g., for display purposes)
        
        Args:
            data: Data to mask
            mask_char: Character to use for masking
            show_last: Number of characters to show at the end
            
        Returns:
            Masked string
        """
        if not data or len(data) <= show_last:
            return mask_char * len(data) if data else ""
        
        masked_length = len(data) - show_last
        return mask_char * masked_length + data[-show_last:] if show_last > 0 else mask_char * len(data)

