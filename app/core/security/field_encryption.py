"""
Field-level encryption-at-rest for SQLAlchemy models.

Wraps a String column so that values are transparently encrypted with
Fernet (AES-128-CBC + HMAC) before being written to the database and
decrypted when read back. The Fernet key is derived deterministically
from settings.ENCRYPTION_KEY so any non-empty string can be used as the
configured secret.
"""
import base64
import hashlib

from cryptography.fernet import Fernet
from sqlalchemy import String
from sqlalchemy.types import TypeDecorator

from app.core.config import settings


def _get_fernet() -> Fernet:
    if not settings.ENCRYPTION_KEY:
        raise RuntimeError(
            "ENCRYPTION_KEY must be set to use EncryptedString fields. "
            "Set the ENCRYPTION_KEY environment variable before storing "
            "or reading encrypted data."
        )
    derived_key = base64.urlsafe_b64encode(
        hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
    )
    return Fernet(derived_key)


class EncryptedString(TypeDecorator):
    """A String column that is encrypted at rest using Fernet."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return _get_fernet().encrypt(value.encode()).decode()

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return _get_fernet().decrypt(value.encode()).decode()
