"""
Risk prediction for esophageal cancer development
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class RiskPredictor:
    """Predict risk of esophageal cancer development"""

    def __init__(self, model=None):
        self.model = model
        self.risk_factors_weights = {
            "age": 0.15,
            "gender": 0.10,
            "smoking": 0.20,
            "alcohol": 0.15,
            "obesity": 0.15,
            "gerd": 0.20,
            "barretts_esophagus": 0.25,
            "family_history": 0.10,
        }

    def calculate_risk_score(self, patient_data: Dict) -> Dict:
        """Calculate risk score for esophageal cancer"""
        risk_score = 0.0
        factors = []

        # Age factor
        age = patient_data.get("age", 50)
        if age >= 60:
            age_risk = min(1.0, (age - 60) / 30)  # Normalized to 0-1
            risk_score += age_risk * self.risk_factors_weights["age"]
            factors.append({"factor": "age", "risk": age_risk, "contribution": age_risk * self.risk_factors_weights["age"]})

        # Gender factor
        if patient_data.get("gender") == "Male":
            gender_risk = 0.8  # Males have higher risk
            risk_score += gender_risk * self.risk_factors_weights["gender"]
            factors.append({"factor": "gender", "risk": gender_risk, "contribution": gender_risk * self.risk_factors_weights["gender"]})

        # Smoking
        if patient_data.get("smoking", False):
            risk_score += 1.0 * self.risk_factors_weights["smoking"]
            factors.append({"factor": "smoking", "risk": 1.0, "contribution": self.risk_factors_weights["smoking"]})

        # Alcohol
        if patient_data.get("alcohol", False):
            risk_score += 0.8 * self.risk_factors_weights["alcohol"]
            factors.append({"factor": "alcohol", "risk": 0.8, "contribution": 0.8 * self.risk_factors_weights["alcohol"]})

        # Obesity (BMI > 30)
        bmi = patient_data.get("bmi", 25)
        if bmi > 30:
            obesity_risk = min(1.0, (bmi - 30) / 10)
            risk_score += obesity_risk * self.risk_factors_weights["obesity"]
            factors.append({"factor": "obesity", "risk": obesity_risk, "contribution": obesity_risk * self.risk_factors_weights["obesity"]})

        # GERD
        if patient_data.get("gerd", False):
            risk_score += 1.0 * self.risk_factors_weights["gerd"]
            factors.append({"factor": "gerd", "risk": 1.0, "contribution": self.risk_factors_weights["gerd"]})

        # Barrett's esophagus
        if patient_data.get("barretts_esophagus", False):
            risk_score += 1.0 * self.risk_factors_weights["barretts_esophagus"]
            factors.append({"factor": "barretts_esophagus", "risk": 1.0, "contribution": self.risk_factors_weights["barretts_esophagus"]})

        # Family history
        if patient_data.get("family_history", False):
            risk_score += 0.6 * self.risk_factors_weights["family_history"]
            factors.append({"factor": "family_history", "risk": 0.6, "contribution": 0.6 * self.risk_factors_weights["family_history"]})

        # Normalize to 0-1
        risk_score = min(1.0, risk_score)

        # Categorize risk
        if risk_score < 0.3:
            risk_category = "Low"
            recommendation = "Routine screening recommended"
        elif risk_score < 0.6:
            risk_category = "Moderate"
            recommendation = "Regular monitoring and lifestyle modifications recommended"
        elif risk_score < 0.8:
            risk_category = "High"
            recommendation = "Close monitoring and preventive measures recommended"
        else:
            risk_category = "Very High"
            recommendation = "Immediate evaluation and intervention recommended"

        return {
            "risk_score": round(risk_score, 3),
            "risk_category": risk_category,
            "recommendation": recommendation,
            "factors": factors,
            "calculated_at": datetime.now().isoformat(),
        }

    def predict_with_model(self, patient_data: Dict, model) -> Dict:
        """Predict risk using ML model"""
        if model is None:
            return self.calculate_risk_score(patient_data)

        try:
            # Prepare features
            features = self._extract_features(patient_data)
            feature_df = pd.DataFrame([features])

            # Ensure all model features are present
            if hasattr(model, "feature_names"):
                missing_cols = set(model.feature_names) - set(feature_df.columns)
                for col in missing_cols:
                    feature_df[col] = 0
                feature_df = feature_df[model.feature_names]

            # Predict
            probability = model.predict_proba(feature_df)[0]
            risk_score = probability[1] if len(probability) > 1 else probability[0]

            # Get base risk score for factors
            base_risk = self.calculate_risk_score(patient_data)

            return {
                "risk_score": round(float(risk_score), 3),
                "ml_risk_score": round(float(risk_score), 3),
                "base_risk_score": base_risk["risk_score"],
                "risk_category": self._categorize_risk(risk_score),
                "recommendation": self._get_recommendation(risk_score),
                "factors": base_risk["factors"],
                "model_used": True,
                "calculated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            # Fallback to rule-based
            return self.calculate_risk_score(patient_data)

    def _extract_features(self, patient_data: Dict) -> Dict:
        """Extract features from patient data"""
        return {
            "age": patient_data.get("age", 50),
            "is_male": 1 if patient_data.get("gender") == "Male" else 0,
            "smoking": 1 if patient_data.get("smoking", False) else 0,
            "alcohol": 1 if patient_data.get("alcohol", False) else 0,
            "bmi": patient_data.get("bmi", 25),
            "gerd": 1 if patient_data.get("gerd", False) else 0,
            "barretts_esophagus": 1 if patient_data.get("barretts_esophagus", False) else 0,
            "family_history": 1 if patient_data.get("family_history", False) else 0,
        }

    def _categorize_risk(self, risk_score: float) -> str:
        """Categorize risk score"""
        if risk_score < 0.3:
            return "Low"
        elif risk_score < 0.6:
            return "Moderate"
        elif risk_score < 0.8:
            return "High"
        else:
            return "Very High"

    def _get_recommendation(self, risk_score: float) -> str:
        """Get recommendation based on risk score"""
        if risk_score < 0.3:
            return "Routine screening recommended"
        elif risk_score < 0.6:
            return "Regular monitoring and lifestyle modifications recommended"
        elif risk_score < 0.8:
            return "Close monitoring and preventive measures recommended"
        else:
            return "Immediate evaluation and intervention recommended"

