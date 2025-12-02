"""
Tests for security headers
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestSecurityHeaders:
    """Test security headers implementation"""

    def test_x_content_type_options(self):
        """Test X-Content-Type-Options header"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_x_frame_options(self):
        """Test X-Frame-Options header"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

    def test_x_xss_protection(self):
        """Test X-XSS-Protection header"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-XSS-Protection"] == "1; mode=block"

    def test_content_security_policy(self):
        """Test Content-Security-Policy header"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert "Content-Security-Policy" in response.headers
        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp

    def test_referrer_policy(self):
        """Test Referrer-Policy header"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert "Referrer-Policy" in response.headers
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_permissions_policy(self):
        """Test Permissions-Policy header"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert "Permissions-Policy" in response.headers
        permissions = response.headers["Permissions-Policy"]
        assert "geolocation=()" in permissions
        assert "camera=()" in permissions

    def test_cross_origin_policies(self):
        """Test Cross-Origin policy headers"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        # Cross-Origin-Embedder-Policy
        assert "Cross-Origin-Embedder-Policy" in response.headers
        assert response.headers["Cross-Origin-Embedder-Policy"] == "require-corp"
        
        # Cross-Origin-Opener-Policy
        assert "Cross-Origin-Opener-Policy" in response.headers
        assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"
        
        # Cross-Origin-Resource-Policy
        assert "Cross-Origin-Resource-Policy" in response.headers
        assert response.headers["Cross-Origin-Resource-Policy"] == "same-origin"

    def test_x_permitted_cross_domain_policies(self):
        """Test X-Permitted-Cross-Domain-Policies header"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert "X-Permitted-Cross-Domain-Policies" in response.headers
        assert response.headers["X-Permitted-Cross-Domain-Policies"] == "none"

    def test_server_header_removed(self):
        """Test that Server header is removed"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        # Server header should not be present or should be empty
        assert "Server" not in response.headers or response.headers.get("Server") == ""

    def test_x_powered_by_removed(self):
        """Test that X-Powered-By header is removed"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert "X-Powered-By" not in response.headers

    def test_security_headers_on_all_endpoints(self):
        """Test that security headers are present on all endpoints"""
        endpoints = [
            "/",
            "/health",
            "/api/v1/health",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Accept 200, 503 (service unavailable), or 404
            assert response.status_code in [200, 503, 404], f"Endpoint {endpoint} returned {response.status_code}"
            
            # Check key security headers (should be present regardless of status)
            assert "X-Content-Type-Options" in response.headers, f"Missing X-Content-Type-Options on {endpoint}"
            assert "X-Frame-Options" in response.headers, f"Missing X-Frame-Options on {endpoint}"
            assert "Content-Security-Policy" in response.headers, f"Missing Content-Security-Policy on {endpoint}"

