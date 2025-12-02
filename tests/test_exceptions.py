"""
Tests for custom exceptions
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.exceptions import (
    ValidationError,
    NotFoundError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    DatabaseError,
    ExternalServiceError,
    MLModelError,
    DataProcessingError,
)


client = TestClient(app)


class TestCustomExceptions:
    """Test custom exception classes"""
    
    def test_validation_error(self):
        """Test ValidationError exception"""
        error = ValidationError("Invalid input", field="email")
        assert error.status_code == 422
        assert error.error_code == "VALIDATION_ERROR"
        assert error.field == "email"
    
    def test_not_found_error(self):
        """Test NotFoundError exception"""
        error = NotFoundError("Patient", identifier="123")
        assert error.status_code == 404
        assert error.error_code == "NOT_FOUND"
        assert error.resource == "Patient"
        assert error.identifier == "123"
    
    def test_authentication_error(self):
        """Test AuthenticationError exception"""
        error = AuthenticationError("Invalid credentials")
        assert error.status_code == 401
        assert error.error_code == "AUTHENTICATION_ERROR"
    
    def test_authorization_error(self):
        """Test AuthorizationError exception"""
        error = AuthorizationError("Access denied")
        assert error.status_code == 403
        assert error.error_code == "AUTHORIZATION_ERROR"
    
    def test_rate_limit_error(self):
        """Test RateLimitError exception"""
        error = RateLimitError("Too many requests", retry_after=60)
        assert error.status_code == 429
        assert error.error_code == "RATE_LIMIT_ERROR"
        assert error.retry_after == 60
        assert "Retry-After" in error.headers
    
    def test_database_error(self):
        """Test DatabaseError exception"""
        error = DatabaseError("Connection failed")
        assert error.status_code == 500
        assert error.error_code == "DATABASE_ERROR"
    
    def test_external_service_error(self):
        """Test ExternalServiceError exception"""
        error = ExternalServiceError("TCGA", "Service unavailable")
        assert error.status_code == 502
        assert error.error_code == "EXTERNAL_SERVICE_ERROR"
        assert error.service == "TCGA"
    
    def test_ml_model_error(self):
        """Test MLModelError exception"""
        error = MLModelError("Model loading failed")
        assert error.status_code == 500
        assert error.error_code == "ML_MODEL_ERROR"
    
    def test_data_processing_error(self):
        """Test DataProcessingError exception"""
        error = DataProcessingError("Data transformation failed")
        assert error.status_code == 422
        assert error.error_code == "DATA_PROCESSING_ERROR"


class TestExceptionHandlers:
    """Test exception handlers in FastAPI app"""
    
    def test_validation_error_handler(self):
        """Test validation error handler"""
        # Send invalid data
        response = client.post(
            "/api/v1/auth/login",
            json={"invalid": "data"},  # Should be form data
        )
        # Should return 422 with proper format
        assert response.status_code in [422, 400]
        if response.status_code == 422:
            data = response.json()
            assert "error" in data or "detail" in data
    
    def test_404_error_format(self):
        """Test 404 error format"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

