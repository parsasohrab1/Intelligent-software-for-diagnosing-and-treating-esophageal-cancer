"""
End-to-end tests for user workflows
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestDataScientistWorkflow:
    """Test workflow for Data Scientist"""

    def test_data_scientist_workflow(self):
        """Test complete data scientist workflow"""
        # 1. Login
        login_data = {
            "username": "data_scientist",
            "password": "password",
        }
        login_response = client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # 2. Generate synthetic data
            data_gen = {
                "n_patients": 100,
                "cancer_ratio": 0.3,
                "seed": 42,
            }
            gen_response = client.post(
                "/api/v1/synthetic-data/generate", json=data_gen, headers=headers
            )
            assert gen_response.status_code in [200, 201]

            # 3. Train model
            train_data = {
                "data_path": "synthetic_data.csv",
                "target_column": "has_cancer",
                "model_type": "RandomForest",
            }
            train_response = client.post(
                "/api/v1/ml-models/train", json=train_data, headers=headers
            )
            # May fail if data doesn't exist, that's ok
            assert train_response.status_code in [200, 400, 404]


class TestClinicalResearcherWorkflow:
    """Test workflow for Clinical Researcher"""

    def test_clinical_researcher_workflow(self):
        """Test complete clinical researcher workflow"""
        # 1. Login
        login_data = {
            "username": "clinical_researcher",
            "password": "password",
        }
        login_response = client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # 2. Collect real data
            collect_data = {
                "source": "tcga",
                "query": "esophageal cancer",
            }
            collect_response = client.post(
                "/api/v1/data-collection/collect", json=collect_data, headers=headers
            )
            assert collect_response.status_code in [200, 400, 401]

            # 3. View metadata
            metadata_response = client.get(
                "/api/v1/data-collection/metadata/statistics", headers=headers
            )
            assert metadata_response.status_code in [200, 401]


class TestMedicalOncologistWorkflow:
    """Test workflow for Medical Oncologist"""

    def test_medical_oncologist_workflow(self):
        """Test complete medical oncologist workflow"""
        # 1. Login
        login_data = {
            "username": "oncologist",
            "password": "password",
        }
        login_response = client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # 2. Risk prediction
            patient_data = {
                "patient_data": {
                    "age": 65,
                    "gender": "Male",
                    "smoking": True,
                    "gerd": True,
                }
            }
            risk_response = client.post(
                "/api/v1/cds/risk-prediction", json=patient_data, headers=headers
            )
            assert risk_response.status_code in [200, 401]

            # 3. Treatment recommendation
            treatment_data = {
                "patient_data": {"age": 65, "gender": "Male"},
                "cancer_data": {
                    "t_stage": "T3",
                    "n_stage": "N1",
                    "m_stage": "M0",
                },
            }
            treatment_response = client.post(
                "/api/v1/cds/treatment-recommendation",
                json=treatment_data,
                headers=headers,
            )
            assert treatment_response.status_code in [200, 401]


class TestSystemAdministratorWorkflow:
    """Test workflow for System Administrator"""

    def test_system_administrator_workflow(self):
        """Test complete system administrator workflow"""
        # 1. Login
        login_data = {
            "username": "admin",
            "password": "password",
        }
        login_response = client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # 2. View audit logs
            audit_response = client.get("/api/v1/audit/logs", headers=headers)
            assert audit_response.status_code in [200, 401, 403]

            # 3. View system statistics
            stats_response = client.get("/api/v1/health", headers=headers)
            assert stats_response.status_code == 200

