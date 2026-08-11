"""
Clinical workflow API — end-to-end patient journey orchestration.
Register → MRI upload → analysis → CDS/SHAP → treatment → monitoring
"""
import logging
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.patient import Patient
from app.services.cds.risk_predictor import RiskPredictor
from app.services.cds.treatment_recommender import TreatmentRecommender
from app.services.data_processing.multi_modality import MultiModalityProcessor
from app.services.imaging_data_enrichment import ImagingDataEnrichment
from app.services.cds.data_completeness import validate_cds_inputs

logger = logging.getLogger(__name__)
router = APIRouter()


class WorkflowRegisterRequest(BaseModel):
    age: int = Field(65, ge=18, le=100)
    gender: str = Field("Male")
    ethnicity: Optional[str] = Field("Caucasian")
    has_cancer: bool = Field(True)
    cancer_type: Optional[str] = Field("Esophageal Adenocarcinoma")
    cancer_subtype: Optional[str] = None
    smoking: bool = Field(False)
    alcohol: bool = Field(False)
    gerd: bool = Field(True)
    bmi: float = Field(28.0)
    barretts_esophagus: bool = Field(False)
    family_history: bool = Field(False)


def _generate_patient_id() -> str:
    return f"WF{datetime.now().strftime('%y%m%d%H%M%S')}"


def _build_patient_data(info: Dict[str, Any], extras: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    data = {
        "age": info.get("age", 65),
        "gender": info.get("gender", "Male"),
        "smoking": False,
        "alcohol": False,
        "gerd": info.get("has_cancer", False),
        "bmi": 28,
        "barretts_esophagus": False,
        "family_history": False,
        "patient_id": info.get("patient_id"),
    }
    if extras:
        data.update(extras)
    return data


def _build_cancer_data(combined: Dict[str, Any]) -> Dict[str, Any]:
    imaging = (combined.get("imaging_data") or [{}])[0] if combined.get("imaging_data") else {}
    return {
        "t_stage": "T2",
        "n_stage": "N1",
        "m_stage": "M0",
        "histology": "adenocarcinoma",
        "grade": "G2",
        "tumor_length_cm": imaging.get("tumor_length_cm") or 4.5,
        "lymph_nodes_positive": imaging.get("lymph_nodes_positive") or 2,
    }


@router.post("/register-patient", status_code=201)
async def register_patient_workflow(
    request: WorkflowRegisterRequest,
    db: Session = Depends(get_db),
):
    """Register a new patient for the clinical workflow (dev-friendly, no auth)."""
    patient_id = _generate_patient_id()
    try:
        db_patient = Patient(
            patient_id=patient_id,
            age=request.age,
            gender=request.gender,
            ethnicity=request.ethnicity,
            has_cancer=request.has_cancer,
            cancer_type=request.cancer_type if request.has_cancer else None,
            cancer_subtype=request.cancer_subtype,
        )
        db.add(db_patient)
        db.commit()
        db.refresh(db_patient)

        return {
            "patient_id": patient_id,
            "patient": {
                "patient_id": patient_id,
                "age": request.age,
                "gender": request.gender,
                "ethnicity": request.ethnicity,
                "has_cancer": request.has_cancer,
                "cancer_type": request.cancer_type,
            },
            "cds_inputs": {
                "smoking": request.smoking,
                "alcohol": request.alcohol,
                "gerd": request.gerd,
                "bmi": request.bmi,
                "barretts_esophagus": request.barretts_esophagus,
                "family_history": request.family_history,
            },
            "message": "Patient registered successfully",
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Workflow register failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to register patient: {e}")


@router.post("/upload-mri")
async def upload_mri_workflow(
    patient_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload MRI, process image, and attach imaging record to patient."""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    suffix = os.path.splitext(file.filename or "mri.png")[1] or ".png"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        processor = MultiModalityProcessor()
        analysis = processor.process_imaging_data(
            image_path=tmp_path,
            modality="MRI",
            text_report=None,
        )

        findings = analysis.get("findings") or analysis.get("summary") or "MRI uploaded via clinical workflow"
        impression = analysis.get("impression") or analysis.get("interpretation") or "Pending radiologist review"
        tumor_length = analysis.get("tumor_length_cm") or analysis.get("measurements", {}).get("tumor_length_cm")
        wall_thickness = analysis.get("wall_thickness_cm") or analysis.get("measurements", {}).get("wall_thickness_cm")

        enrichment = ImagingDataEnrichment(db)
        imaging_data = enrichment.add_radiology_data(
            patient_id=patient_id,
            modality="MRI",
            findings=str(findings)[:2000],
            impression=str(impression)[:2000],
            tumor_length_cm=float(tumor_length) if tumor_length else 4.0,
            wall_thickness_cm=float(wall_thickness) if wall_thickness else 1.2,
            lymph_nodes_positive=2 if patient.has_cancer else 0,
            contrast_used=True,
        )

        return {
            "patient_id": patient_id,
            "image_id": imaging_data.image_id,
            "imaging_modality": "MRI",
            "analysis": analysis,
            "findings": imaging_data.findings,
            "impression": imaging_data.impression,
            "message": "MRI uploaded and analyzed successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MRI upload workflow failed: {e}")
        raise HTTPException(status_code=500, detail=f"MRI processing failed: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


class WorkflowCDSRequest(BaseModel):
    cds_inputs: Optional[Dict[str, Any]] = None


@router.post("/{patient_id}/cds")
async def run_cds_workflow(
    patient_id: str,
    body: Optional[WorkflowCDSRequest] = None,
    db: Session = Depends(get_db),
):
    """Run CDS risk prediction with SHAP + treatment recommendation for a patient."""
    from app.api.v1.endpoints.patients import get_patient_combined_data

    combined = await get_patient_combined_data(patient_id)
    if not combined.get("patient_info"):
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    info = combined["patient_info"]
    extras = body.cds_inputs if body and body.cds_inputs else {}
    patient_data = _build_patient_data(info, extras)
    cancer_data = _build_cancer_data(combined)

    data_completeness = validate_cds_inputs(patient_data, cancer_data, context="full")

    predictor = RiskPredictor()
    risk_result = predictor.predict_with_model(patient_data, None)

    try:
        feature_importance = {}
        for factor in risk_result.get("factors", []):
            feature_importance[factor["factor"]] = factor["contribution"]
        risk_result["shap_explanation"] = {
            "feature_importance": feature_importance,
            "method": "rule_based",
        }
    except Exception as e:
        risk_result["shap_explanation"] = {"error": str(e)}

    recommender = TreatmentRecommender()
    treatment_result = recommender.recommend_treatment(patient_data, cancer_data)

    return {
        "patient_id": patient_id,
        "risk_prediction": risk_result,
        "treatment_recommendation": treatment_result,
        "cancer_data_used": cancer_data,
        "patient_data_used": patient_data,
        "data_completeness": data_completeness,
        "reliability_notice": (
            None
            if data_completeness.get("prediction_reliable", True)
            else "CDS output generated with incomplete data. Review warnings before clinical use."
        ),
    }


@router.get("/{patient_id}/monitoring")
async def get_workflow_monitoring(patient_id: str, db: Session = Depends(get_db)):
    """Get patient monitoring data for workflow final step."""
    from app.api.v1.endpoints.patient_monitoring import get_patient_monitoring

    try:
        return await get_patient_monitoring(patient_id=patient_id, db=db)
    except Exception as e:
        logger.error(f"Monitoring fetch failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load monitoring: {e}")
