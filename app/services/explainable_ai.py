"""
Explainable AI using SHAP and feature importance
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import json


class ExplainableAI:
    """Explainable AI for model predictions"""

    def __init__(self):
        self.shap_explainer = None
        self.shap_values = None

    def calculate_feature_importance(
        self, model, X: pd.DataFrame, method: str = "builtin"
    ) -> Dict[str, float]:
        """Calculate feature importance"""
        if method == "builtin":
            # Use model's built-in feature importance
            if hasattr(model, "feature_importances_"):
                importances = model.feature_importances_
            elif hasattr(model, "coef_"):
                # For linear models, use absolute coefficients
                importances = np.abs(model.coef_[0])
            else:
                raise ValueError("Model does not have feature importance")
        else:
            raise ValueError(f"Unknown method: {method}")

        return dict(zip(X.columns, importances))

    def explain_with_shap(
        self,
        model,
        X: pd.DataFrame,
        X_background: Optional[pd.DataFrame] = None,
        max_samples: int = 100,
    ) -> Dict:
        """Explain predictions using SHAP"""
        try:
            import shap

            # Use subset for background
            if X_background is None:
                X_background = X.sample(min(max_samples, len(X)), random_state=42)

            # Create explainer
            if hasattr(model, "predict_proba"):
                explainer = shap.TreeExplainer(model) if hasattr(model, "tree_") else shap.Explainer(model, X_background)
            else:
                explainer = shap.Explainer(model, X_background)

            # Calculate SHAP values
            shap_values = explainer(X.head(max_samples))

            # Summary statistics
            if hasattr(shap_values, "values"):
                mean_abs_shap = np.abs(shap_values.values).mean(axis=0)
            else:
                mean_abs_shap = np.abs(shap_values).mean(axis=0)

            feature_importance = dict(zip(X.columns, mean_abs_shap))

            return {
                "shap_values": shap_values.values.tolist() if hasattr(shap_values, "values") else shap_values.tolist(),
                "feature_importance": feature_importance,
                "base_value": float(shap_values.base_values[0]) if hasattr(shap_values, "base_values") else 0.0,
            }

        except ImportError:
            return {"error": "SHAP not installed. Install with: pip install shap"}
        except Exception as e:
            return {"error": f"Error calculating SHAP values: {str(e)}"}

    def explain_prediction(
        self,
        model,
        X: pd.DataFrame,
        instance_idx: int = 0,
    ) -> Dict:
        """Explain a single prediction"""
        instance = X.iloc[[instance_idx]]

        # Get prediction
        if hasattr(model, "predict_proba"):
            prediction = model.predict_proba(instance)[0]
        else:
            prediction = model.predict(instance)[0]

        # Feature importance
        feature_importance = self.calculate_feature_importance(model, X)

        # SHAP explanation if available
        shap_explanation = self.explain_with_shap(model, instance, X, max_samples=10)

        return {
            "instance": instance.to_dict(orient="records")[0],
            "prediction": float(prediction) if isinstance(prediction, (int, float, np.number)) else prediction.tolist(),
            "feature_importance": feature_importance,
            "shap_explanation": shap_explanation,
        }

    def generate_explanation_report(
        self,
        model,
        X: pd.DataFrame,
        y: Optional[pd.Series] = None,
    ) -> Dict:
        """Generate comprehensive explanation report"""
        report = {
            "feature_importance": self.calculate_feature_importance(model, X),
            "top_features": [],
        }

        # Get top features
        sorted_features = sorted(
            report["feature_importance"].items(), key=lambda x: x[1], reverse=True
        )
        report["top_features"] = [
            {"feature": f, "importance": float(imp)} for f, imp in sorted_features[:10]
        ]

        # SHAP summary if available
        try:
            shap_summary = self.explain_with_shap(model, X, max_samples=100)
            report["shap_summary"] = shap_summary
        except:
            report["shap_summary"] = {"error": "SHAP calculation failed"}

        return report

