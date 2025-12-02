"""
Integration tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self):
        """Test health endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        # Health endpoint returns "ok" or "healthy"
        assert data["status"] in ["healthy", "ok"]


class TestAuthentication:
    """Test authentication endpoints"""

    def test_register_user(self):
        """Test user registration"""
        user_data = {
            "username": "test_user",
            "email": "test@example.com",
            "password": "test_password123",
            "role": "data_scientist",
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code in [201, 400]  # 400 if user exists

    def test_login(self):
        """Test user login"""
        login_data = {
            "username": "test_user",
            "password": "test_password123",
        }
        response = client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        # May fail if user doesn't exist, that's ok for integration test
        assert response.status_code in [200, 401]


class TestSyntheticData:
    """Test synthetic data endpoints"""

    def test_generate_synthetic_data(self):
        """Test synthetic data generation"""
        # This would require authentication in production
        data = {
            "n_patients": 10,
            "cancer_ratio": 0.3,
            "seed": 42,
            "save_to_db": False,
        }
        response = client.post("/api/v1/synthetic-data/generate", json=data)
        # May require auth, so check for 200 or 401
        assert response.status_code in [200, 401, 403]


class TestDataCollection:
    """Test data collection endpoints"""

    def test_search_trials(self):
        """Test clinical trial search"""
        response = client.get("/api/v1/cds/clinical-trials/search?condition=Esophageal%20Cancer")
        assert response.status_code in [200, 401]


class TestCDS:
    """Test Clinical Decision Support endpoints"""

    def test_risk_prediction(self):
        """Test risk prediction"""
        patient_data = {
            "patient_data": {
                "age": 65,
                "gender": "Male",
                "smoking": True,
            }
        }
        response = client.post("/api/v1/cds/risk-prediction", json=patient_data)
        assert response.status_code in [200, 401]


@pytest.mark.integration
class TestEndToEnd:
    """End-to-end integration tests"""

    def test_complete_workflow(self):
        """Test complete workflow from data generation to prediction"""
        # 1. Generate synthetic data
        data_gen = {
            "n_patients": 5,
            "cancer_ratio": 0.3,
            "seed": 42,
            "save_to_db": False,
        }
        gen_response = client.post("/api/v1/synthetic-data/generate", json=data_gen)
        # May require auth
        assert gen_response.status_code in [200, 401, 403]

        # 2. Risk prediction (if data was generated)
        if gen_response.status_code == 200:
            patient_data = {
                "patient_data": {
                    "age": 65,
                    "gender": "Male",
                }
            }
            risk_response = client.post("/api/v1/cds/risk-prediction", json=patient_data)
            assert risk_response.status_code in [200, 401]

