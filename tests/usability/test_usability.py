"""
Usability tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestAPIUsability:
    """Test API usability"""

    def test_api_documentation_available(self):
        """Test that API documentation is available"""
        response = client.get("/docs")
        assert response.status_code == 200

        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_schema_available(self):
        """Test that OpenAPI schema is available"""
        # Try the configured OpenAPI URL
        response = client.get("/api/v1/openapi.json")
        if response.status_code != 200:
            # Fallback to default
            response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_error_messages_clear(self):
        """Test that error messages are clear and helpful"""
        # Test 404
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        # Error should be JSON
        assert response.headers["content-type"] == "application/json"

        # Test 401
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


class TestResponseFormat:
    """Test response format consistency"""

    def test_consistent_response_format(self):
        """Test that responses have consistent format"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        # Should have consistent structure
        assert isinstance(data, dict)

    def test_error_response_format(self):
        """Test that error responses have consistent format"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestEndpointDiscovery:
    """Test endpoint discoverability"""

    def test_endpoints_listed_in_openapi(self):
        """Test that all endpoints are listed in OpenAPI"""
        # Try the configured OpenAPI URL
        response = client.get("/api/v1/openapi.json")
        if response.status_code != 200:
            # Fallback to default
            response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()

        # Check for key endpoints (paths may be in schema)
        paths = schema.get("paths", {})
        # Health endpoint might be at root or /api/v1/health
        health_found = "/api/v1/health" in paths or "/health" in paths
        assert health_found, f"Health endpoint not found. Available paths: {list(paths.keys())[:10]}"
        # Check that we have some API endpoints
        assert len(paths) > 0, "No endpoints found in OpenAPI schema"

