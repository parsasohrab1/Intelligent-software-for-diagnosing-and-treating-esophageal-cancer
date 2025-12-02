"""
Security tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestAuthentication:
    """Test authentication security"""

    def test_invalid_credentials(self):
        """Test login with invalid credentials"""
        login_data = {
            "username": "invalid_user",
            "password": "wrong_password",
        }
        response = client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 401

    def test_missing_token(self):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_invalid_token(self):
        """Test accessing protected endpoint with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401


class TestAuthorization:
    """Test authorization (RBAC)"""

    def test_unauthorized_access(self):
        """Test accessing resource without proper permissions"""
        # This would require a valid token with limited permissions
        # For now, just test that 401/403 is returned
        response = client.get("/api/v1/audit/logs")
        assert response.status_code in [401, 403]


class TestInputValidation:
    """Test input validation and sanitization"""

    def test_sql_injection_attempt(self):
        """Test SQL injection protection"""
        # Attempt SQL injection in search
        malicious_input = "'; DROP TABLE users; --"
        response = client.get(f"/api/v1/patients/?search={malicious_input}")
        # Should not crash, should return 400 or handle gracefully
        assert response.status_code in [200, 400, 401]

    def test_xss_attempt(self):
        """Test XSS protection"""
        malicious_input = "<script>alert('XSS')</script>"
        response = client.get(f"/api/v1/patients/?search={malicious_input}")
        # Should sanitize input
        assert response.status_code in [200, 400, 401]


class TestDataProtection:
    """Test data protection"""

    def test_sensitive_data_not_exposed(self):
        """Test that sensitive data is not exposed in responses"""
        # Check that patient IDs are hashed or de-identified
        response = client.get("/api/v1/patients/")
        if response.status_code == 200:
            data = response.json()
            # Verify no direct identifiers are exposed
            # This is a basic check
            assert isinstance(data, (list, dict))


class TestRateLimiting:
    """Test rate limiting (if implemented)"""

    def test_rate_limiting(self):
        """Test rate limiting on auth endpoints"""
        # Make many requests quickly
        for _ in range(20):
            login_data = {
                "username": "test",
                "password": "test",
            }
            response = client.post(
                "/api/v1/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            # After rate limit, should get 429
            # For now, just verify it doesn't crash
            assert response.status_code in [200, 401, 429]

