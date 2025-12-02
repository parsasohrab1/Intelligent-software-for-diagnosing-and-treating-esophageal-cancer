"""
Clinical Decision Support endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.cds.risk_predictor import RiskPredictor
from app.services.cds.treatment_recommender import TreatmentRecommender
from app.services.cds.prognostic_scorer import PrognosticScorer
from app.services.cds.nanosystem_designer import NanosystemDesigner
from app.services.cds.clinical_trial_matcher import ClinicalTrialMatcher
from app.services.cds.monitoring_alerts import MonitoringAlerts
from app.services.model_registry import ModelRegistry

router = APIRouter()


class RiskPredictionRequest(BaseModel):
    """Request model for risk prediction"""

    patient_data: Dict[str, Any] = Field(..., description="Patient data")
    use_ml_model: bool = Field(
        default=False, description="Use ML model for prediction"
    )
    model_id: Optional[str] = Field(None, description="ML model ID to use")


class TreatmentRecommendationRequest(BaseModel):
    """Request model for treatment recommendation"""

    patient_data: Dict[str, Any] = Field(..., description="Patient data")
    cancer_data: Optional[Dict[str, Any]] = Field(None, description="Cancer data")


class PrognosticScoreRequest(BaseModel):
    """Request model for prognostic scoring"""

    patient_data: Dict[str, Any] = Field(..., description="Patient data")
    cancer_data: Optional[Dict[str, Any]] = Field(None, description="Cancer data")


class NanosystemDesignRequest(BaseModel):
    """Request model for nanosystem design"""

    patient_data: Dict[str, Any] = Field(..., description="Patient data")
    cancer_data: Optional[Dict[str, Any]] = Field(None, description="Cancer data")


class ClinicalTrialMatchRequest(BaseModel):
    """Request model for clinical trial matching"""

    patient_data: Dict[str, Any] = Field(..., description="Patient data")
    cancer_data: Optional[Dict[str, Any]] = Field(None, description="Cancer data")


class MonitoringAlertRequest(BaseModel):
    """Request model for monitoring alerts"""

    patient_data: Dict[str, Any] = Field(..., description="Current patient data")
    previous_data: Optional[Dict[str, Any]] = Field(
        None, description="Previous patient data for comparison"
    )


@router.post("/risk-prediction")
async def predict_risk(request: RiskPredictionRequest):
    """Predict risk of esophageal cancer development"""
    try:
        predictor = RiskPredictor()

        # Use ML model if requested
        model = None
        if request.use_ml_model and request.model_id:
            registry = ModelRegistry()
            model_info = registry.get_model(request.model_id)
            if model_info:
                # Load model (similar to ml_models endpoint)
                # ... (model loading logic)
                pass

        result = predictor.predict_with_model(request.patient_data, model)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error predicting risk: {str(e)}"
        )


@router.post("/treatment-recommendation")
async def recommend_treatment(request: TreatmentRecommendationRequest):
    """Recommend treatment based on patient characteristics"""
    try:
        recommender = TreatmentRecommender()
        recommendations = recommender.recommend_treatment(
            request.patient_data, request.cancer_data
        )
        return recommendations

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating recommendations: {str(e)}"
        )


@router.post("/prognostic-score")
async def calculate_prognostic_score(request: PrognosticScoreRequest):
    """Calculate prognostic score for patient"""
    try:
        scorer = PrognosticScorer()
        score = scorer.calculate_prognostic_score(
            request.patient_data, request.cancer_data
        )
        return score

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error calculating prognostic score: {str(e)}"
        )


@router.post("/nanosystem-design")
async def suggest_nanosystem(request: NanosystemDesignRequest):
    """Suggest personalized nanosystem design"""
    try:
        designer = NanosystemDesigner()
        suggestions = designer.suggest_nanosystem(
            request.patient_data, request.cancer_data
        )
        return suggestions

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating nanosystem suggestions: {str(e)}"
        )


@router.post("/clinical-trial-match")
async def match_clinical_trials(request: ClinicalTrialMatchRequest):
    """Match patient to clinical trials"""
    try:
        matcher = ClinicalTrialMatcher()
        matches = matcher.match_patient_to_trials(
            request.patient_data, request.cancer_data
        )
        return matches

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error matching clinical trials: {str(e)}"
        )


@router.post("/monitoring-alerts")
async def check_monitoring_alerts(request: MonitoringAlertRequest):
    """Check for monitoring alerts"""
    try:
        monitor = MonitoringAlerts()
        alerts = monitor.check_alerts(
            request.patient_data, request.previous_data
        )
        summary = monitor.generate_alert_summary(alerts)
        return summary

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking alerts: {str(e)}"
        )


@router.get("/clinical-trials/search")
async def search_clinical_trials(
    condition: str = "Esophageal Cancer",
    status: str = "RECRUITING",
    max_results: int = 50,
):
    """Search for clinical trials"""
    try:
        matcher = ClinicalTrialMatcher()
        trials = matcher.search_trials(
            condition=condition, status=status, max_results=max_results
        )
        return {"trials": trials, "count": len(trials)}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error searching trials: {str(e)}"
        )

