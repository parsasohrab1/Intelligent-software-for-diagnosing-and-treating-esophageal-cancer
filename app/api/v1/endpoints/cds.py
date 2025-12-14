"""
Clinical Decision Support endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from functools import lru_cache

from app.core.database import get_db
from app.services.cds.risk_predictor import RiskPredictor
from app.services.cds.treatment_recommender import TreatmentRecommender
from app.services.cds.prognostic_scorer import PrognosticScorer
from app.services.cds.nanosystem_designer import NanosystemDesigner
from app.services.cds.clinical_trial_matcher import ClinicalTrialMatcher
from app.services.cds.monitoring_alerts import MonitoringAlerts
from app.services.model_registry import ModelRegistry
from app.services.explainable_ai import ExplainableAI
import pandas as pd

router = APIRouter()


class RiskPredictionRequest(BaseModel):
    """Request model for risk prediction"""

    patient_data: Dict[str, Any] = Field(..., description="Patient data")
    use_ml_model: bool = Field(
        default=False, description="Use ML model for prediction"
    )
    model_id: Optional[str] = Field(None, description="ML model ID to use")
    include_explanation: bool = Field(
        default=True, description="Include SHAP explanation"
    )


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
        model_obj = None
        if request.use_ml_model and request.model_id:
            registry = ModelRegistry()
            model_info = registry.get_model(request.model_id)
            if model_info:
                # Load model (similar to ml_models endpoint)
                from app.services.ml_models.sklearn_models import (
                    LogisticRegressionModel,
                    RandomForestModel,
                    XGBoostModel,
                    LightGBMModel,
                )
                from app.services.ml_models.neural_network import NeuralNetworkModel

                model_type = model_info["model_type"]
                if model_type == "LogisticRegression":
                    model_obj = LogisticRegressionModel()
                elif model_type == "RandomForest":
                    model_obj = RandomForestModel()
                elif model_type == "XGBoost":
                    model_obj = XGBoostModel()
                elif model_type == "LightGBM":
                    model_obj = LightGBMModel()
                elif model_type == "NeuralNetwork":
                    model_obj = NeuralNetworkModel()
                
                if model_obj:
                    model_obj.load_model(model_info["model_path"])
                    model = model_obj.model

        result = predictor.predict_with_model(request.patient_data, model)

        # Add SHAP explanation if requested
        if request.include_explanation:
            try:
                explainer = ExplainableAI()
                features = predictor._extract_features(request.patient_data)
                feature_df = pd.DataFrame([features])
                
                # If we have a model, use SHAP
                if model is not None and model_obj is not None:
                    # Prepare feature dataframe for model
                    if hasattr(model_obj, "feature_names"):
                        missing_cols = set(model_obj.feature_names) - set(feature_df.columns)
                        for col in missing_cols:
                            feature_df[col] = 0
                        feature_df = feature_df[model_obj.feature_names]
                    
                    shap_explanation = explainer.explain_prediction(model, feature_df, instance_idx=0)
                    result["shap_explanation"] = shap_explanation
                else:
                    # Use rule-based feature importance
                    feature_importance = {}
                    for factor in result.get("factors", []):
                        feature_importance[factor["factor"]] = factor["contribution"]
                    
                    result["shap_explanation"] = {
                        "feature_importance": feature_importance,
                        "method": "rule_based"
                    }
            except Exception as e:
                # If SHAP fails, still return prediction without explanation
                result["shap_explanation"] = {"error": f"Explanation unavailable: {str(e)}"}

        return result

    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Error predicting risk: {str(e)}")
        logger.error(traceback.format_exc())
        # Raise HTTPException to maintain API contract - clients should handle errors explicitly
        # Returning default values would mislead clients into treating errors as valid predictions
        raise HTTPException(
            status_code=500,
            detail=f"Error predicting risk: {str(e)}"
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


# Cache the services list since it's static data
@lru_cache(maxsize=1)
def _get_cds_services_list():
    """Get CDS services list (cached)"""
    return [
        {
            "name": "Risk Prediction",
            "id": "risk-prediction",
            "description": "Predict risk of esophageal cancer development",
            "endpoint": "/cds/risk-prediction"
        },
        {
            "name": "Treatment Recommendation",
            "id": "treatment-recommendation",
            "description": "Recommend treatment based on patient characteristics",
            "endpoint": "/cds/treatment-recommendation"
        },
        {
            "name": "Prognostic Scoring",
            "id": "prognostic-score",
            "description": "Calculate prognostic score for patient",
            "endpoint": "/cds/prognostic-score"
        },
        {
            "name": "Nanosystem Design",
            "id": "nanosystem-design",
            "description": "Suggest personalized nanosystem design",
            "endpoint": "/cds/nanosystem-design"
        },
        {
            "name": "Clinical Trial Matching",
            "id": "clinical-trial-match",
            "description": "Match patient to clinical trials",
            "endpoint": "/cds/clinical-trial-match"
        },
        {
            "name": "Monitoring Alerts",
            "id": "monitoring-alerts",
            "description": "Check for monitoring alerts",
            "endpoint": "/cds/monitoring-alerts"
        }
    ]

@router.get("/services")
async def get_cds_services():
    """Get list of available CDS services"""
    # This endpoint should always work as it doesn't depend on external services
    # Return immediately - optimized for speed with caching
    services = _get_cds_services_list()
    return {"services": services, "count": len(services)}


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
