"""
API-level checks of the validated prognosis endpoint and the real-data endpoints.

Uses the real routers through a TestClient. The replay test needs the cached
public cohorts (data/real_world/cache, created by scripts/run_real_data_validation.py)
and is skipped when they are absent.

    pytest --noconftest --no-cov tests/test_real_data_api.py
"""
import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints import cds, real_data

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    app.include_router(cds.router, prefix="/api/v1/cds")
    app.include_router(real_data.router, prefix="/api/v1/real-data")
    return TestClient(app)


BODY = {
    "patient_data": {"age": 63, "gender": "Male"},
    "cancer_data": {"t_stage": "T3", "n_stage": "N1", "m_stage": "M0", "histology": "Squamous cell carcinoma"},
}


def test_v2_endpoint_contract_and_validation_evidence(client):
    r = client.post("/api/v1/cds/prognostic-score-v2", json=BODY)
    assert r.status_code == 200
    out = r.json()
    assert set(out["survival"]) == {"1_year", "3_year"}  # 5y deliberately absent
    assert 0 < out["survival"]["3_year"] <= out["survival"]["1_year"] < 1
    assert out["risk_group"] in {"Low", "Intermediate", "High"}
    assert out["validation"]["status"].endswith("PASS")
    assert "5_year survival (calibration inconsistent across cohorts)" in out["validation"]["not_validated"]


def test_v2_endpoint_degrades_gracefully_with_missing_inputs(client):
    r = client.post("/api/v1/cds/prognostic-score-v2", json={"patient_data": {}, "cancer_data": None})
    assert r.status_code == 200
    assert {"age", "T stage", "N stage", "M stage"} <= set(r.json()["inputs_missing_or_imputed"])


def test_higher_stage_means_lower_predicted_survival(client):
    early = client.post("/api/v1/cds/prognostic-score-v2", json={
        "patient_data": {"age": 60, "gender": "Male"}, "cancer_data": {"t_stage": "T1", "n_stage": "N0", "m_stage": "M0"}}).json()
    late = client.post("/api/v1/cds/prognostic-score-v2", json={
        "patient_data": {"age": 60, "gender": "Male"}, "cancer_data": {"t_stage": "T3", "n_stage": "N2", "m_stage": "M1"}}).json()
    assert late["survival"]["3_year"] < early["survival"]["3_year"]
    assert late["linear_predictor"] > early["linear_predictor"]


def test_legacy_endpoint_carries_failed_validation_notice(client):
    out = client.post("/api/v1/cds/prognostic-score", json=BODY).json()
    assert "FAILED" in out["validation_notice"]


def test_catalog_is_honest_about_verification(client):
    out = client.get("/api/v1/real-data/catalog").json()
    ids = {d["id"]: d for d in out["datasets"]}
    assert ids["tcga-esca-gdc"]["verification"] == "live" and ids["tcga-esca-gdc"]["integration"] == "validated"
    assert ids["rare25"]["license_or_terms"].upper().find("NON-COMMERCIAL") >= 0
    assert all(d["verification"] in {"live", "literature"} for d in out["datasets"])
    only_validated = client.get("/api/v1/real-data/catalog?integration=validated").json()["datasets"]
    assert {d["id"] for d in only_validated} == {"tcga-esca-gdc", "gse53624", "icgc-escc-cbioportal"}


def test_validation_endpoint_reports_both_versions(client):
    v1 = client.get("/api/v1/real-data/validation?version=v1").json()
    v2 = client.get("/api/v1/real-data/validation?version=v2").json()
    assert v1["all_criteria_passed"] is False and v2["all_criteria_passed"] is True
    assert v2["pooled_c_index"] > v1["pooled_c_index"]
    assert client.get("/api/v1/real-data/validation?version=v9").status_code == 400


@pytest.mark.skipif(not (ROOT / "data/real_world/cache/tcga_esca_gdc_cases.json").exists(), reason="public cohort cache not downloaded")
def test_replaying_real_patients_through_api_has_no_failures():
    spec = importlib.util.spec_from_file_location("replay", ROOT / "scripts/replay_real_patients_through_api.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["replay"] = mod
    spec.loader.exec_module(mod)
    result = mod.replay(limit=15)
    assert result["n_requests"] == 45
    assert result["http_failures"] == 0 and result["model_vs_http_mismatches"] == 0 and result["contract_errors"] == 0
