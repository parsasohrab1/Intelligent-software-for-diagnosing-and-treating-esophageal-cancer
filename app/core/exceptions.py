"""
Custom exceptions for INEsCape
"""
from fastapi import HTTPException, status
from typing import Any, Dict, Optional


class INEsCapeException(HTTPException):
    """Base exception for INEsCape"""
    
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


class ValidationError(INEsCapeException):
    """Validation error"""
    
    def __init__(self, detail: str, field: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VALIDATION_ERROR"
        )
        self.field = field


class NotFoundError(INEsCapeException):
    """Resource not found error"""
    
    def __init__(self, resource: str, identifier: Optional[str] = None):
        detail = f"{resource} not found"
        if identifier:
            detail += f": {identifier}"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND"
        )
        self.resource = resource
        self.identifier = identifier


class AuthenticationError(INEsCapeException):
    """Authentication error"""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationError(INEsCapeException):
    """Authorization error"""
    
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="AUTHORIZATION_ERROR"
        )


class RateLimitError(INEsCapeException):
    """Rate limit exceeded error"""
    
    def __init__(self, detail: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers=headers,
            error_code="RATE_LIMIT_ERROR"
        )
        self.retry_after = retry_after


class DatabaseError(INEsCapeException):
    """Database operation error"""
    
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="DATABASE_ERROR"
        )


class ExternalServiceError(INEsCapeException):
    """External service error"""
    
    def __init__(self, service: str, detail: str = "External service error"):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{service}: {detail}",
            error_code="EXTERNAL_SERVICE_ERROR"
        )
        self.service = service


class MLModelError(INEsCapeException):
    """ML model operation error"""
    
    def __init__(self, detail: str = "ML model operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="ML_MODEL_ERROR"
        )


class DataProcessingError(INEsCapeException):
    """Data processing error"""
    
    def __init__(self, detail: str = "Data processing failed"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="DATA_PROCESSING_ERROR"
        )

