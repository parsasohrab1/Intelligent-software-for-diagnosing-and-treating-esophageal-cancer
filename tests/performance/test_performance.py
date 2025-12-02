"""
Performance tests
"""
import pytest
import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestResponseTimes:
    """Test API response times"""

    def test_health_endpoint_performance(self):
        """Test health endpoint response time"""
        start = time.time()
        response = client.get("/api/v1/health")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.1  # Should be very fast

    def test_synthetic_data_generation_performance(self):
        """Test synthetic data generation performance"""
        data = {
            "n_patients": 100,
            "cancer_ratio": 0.3,
            "seed": 42,
            "save_to_db": False,
        }

        start = time.time()
        response = client.post("/api/v1/synthetic-data/generate", json=data)
        elapsed = time.time() - start

        # Should complete in reasonable time
        assert elapsed < 30.0  # 30 seconds for 100 patients

    def test_risk_prediction_performance(self):
        """Test risk prediction performance"""
        patient_data = {
            "patient_data": {
                "age": 65,
                "gender": "Male",
                "smoking": True,
            }
        }

        start = time.time()
        response = client.post("/api/v1/cds/risk-prediction", json=patient_data)
        elapsed = time.time() - start

        # Should be very fast
        assert elapsed < 1.0  # 1 second


class TestConcurrentRequests:
    """Test concurrent request handling"""

    def test_concurrent_health_checks(self):
        """Test multiple concurrent health checks"""
        import concurrent.futures

        def make_request():
            return client.get("/api/v1/health")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # All should succeed
        assert all(r.status_code == 200 for r in results)


@pytest.mark.performance
class TestLoadHandling:
    """Test system load handling"""

    def test_sequential_requests(self):
        """Test handling of sequential requests"""
        start = time.time()

        for _ in range(50):
            response = client.get("/api/v1/health")
            assert response.status_code == 200

        elapsed = time.time() - start
        avg_time = elapsed / 50

        # Average should be reasonable
        assert avg_time < 0.1

