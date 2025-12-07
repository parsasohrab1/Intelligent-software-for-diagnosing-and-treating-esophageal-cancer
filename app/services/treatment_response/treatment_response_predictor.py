"""
Treatment Response Prediction
پیش‌بینی پاسخ بیمار به شیمی‌درمانی یا رادیوتراپی نئوادجوانت
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

from app.services.radiomics.radiomics_extractor import RadiomicsExtractor
from app.services.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


@dataclass
class TreatmentResponsePrediction:
    """نتیجه پیش‌بینی پاسخ درمانی"""
    patient_id: str
    treatment_type: str  # "Chemotherapy" or "Radiotherapy"
    response_probability: float  # احتمال پاسخ موفق (0-1)
    response_category: str  # "High", "Moderate", "Low"
    confidence: float
    biomarkers_contribution: Dict[str, float]
    radiomics_contribution: Dict[str, float]
    key_factors: List[str]
    recommendation: str
    timestamp: str


class TreatmentResponsePredictor:
    """پیش‌بینی پاسخ به درمان نئوادجوانت"""

    def __init__(self):
        self.radiomics_extractor = RadiomicsExtractor()
        self.registry = ModelRegistry()
        self.response_model = None

    def predict_response(
        self,
        patient_id: str,
        biomarkers: Dict[str, Any],
        radiomics_features: Optional[Dict[str, Any]] = None,
        imaging_data: Optional[np.ndarray] = None,
        treatment_type: str = "Chemotherapy",
        model_id: Optional[str] = None
    ) -> TreatmentResponsePrediction:
        """
        پیش‌بینی پاسخ به درمان نئوادجوانت
        
        Args:
            patient_id: شناسه بیمار
            biomarkers: داده‌های بیومارکر (PD-L1, MSI, mutations, etc.)
            radiomics_features: ویژگی‌های رادیومیکس (اگر از قبل استخراج شده)
            imaging_data: تصویر برای استخراج رادیومیکس
            treatment_type: نوع درمان ("Chemotherapy" or "Radiotherapy")
            model_id: شناسه مدل (اگر None، از بهترین مدل استفاده می‌شود)
            
        Returns:
            پیش‌بینی پاسخ درمانی
        """
        try:
            # Extract radiomics if imaging data provided
            if radiomics_features is None and imaging_data is not None:
                radiomics_features = self.radiomics_extractor.extract_features(
                    image=imaging_data,
                    modality="CT"
                )
            
            # Prepare features
            features = self._prepare_features(biomarkers, radiomics_features)
            
            # Load or use default model
            if model_id:
                model_info = self.registry.get_model(model_id)
                if model_info:
                    self.response_model = self._load_model(model_info)
            
            # If no model, use rule-based prediction
            if self.response_model is None:
                response_prob, confidence = self._rule_based_prediction(
                    biomarkers, radiomics_features
                )
            else:
                response_prob, confidence = self._ml_prediction(features)
            
            # Calculate contributions
            biomarkers_contrib = self._calculate_biomarker_contribution(biomarkers)
            radiomics_contrib = self._calculate_radiomics_contribution(radiomics_features) if radiomics_features else {}
            
            # Determine response category
            response_category = self._categorize_response(response_prob)
            
            # Get key factors
            key_factors = self._identify_key_factors(
                biomarkers, radiomics_features, biomarkers_contrib, radiomics_contrib
            )
            
            # Generate recommendation
            recommendation = self._generate_recommendation(
                response_prob, response_category, treatment_type, key_factors
            )
            
            return TreatmentResponsePrediction(
                patient_id=patient_id,
                treatment_type=treatment_type,
                response_probability=response_prob,
                response_category=response_category,
                confidence=confidence,
                biomarkers_contribution=biomarkers_contrib,
                radiomics_contribution=radiomics_contrib,
                key_factors=key_factors,
                recommendation=recommendation,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error predicting treatment response: {str(e)}")
            raise

    def _prepare_features(
        self,
        biomarkers: Dict[str, Any],
        radiomics_features: Optional[Dict[str, Any]]
    ) -> pd.DataFrame:
        """آماده‌سازی ویژگی‌ها برای مدل"""
        features = {}
        
        # Biomarker features
        features["pdl1_status"] = 1.0 if biomarkers.get("pdl1_status") == "positive" else 0.0
        features["pdl1_percentage"] = biomarkers.get("pdl1_percentage", 0.0) or 0.0
        features["msi_status"] = 1.0 if biomarkers.get("msi_status") == "MSI-H" else 0.0
        features["her2_status"] = 1.0 if biomarkers.get("her2_status") == "positive" else 0.0
        
        # Mutation features
        mutations = biomarkers.get("mutations", {})
        if isinstance(mutations, dict):
            features["tp53_mutation"] = 1.0 if mutations.get("TP53") else 0.0
            features["pik3ca_mutation"] = 1.0 if mutations.get("PIK3CA") else 0.0
            features["kras_mutation"] = 1.0 if mutations.get("KRAS") else 0.0
            features["mutation_count"] = float(len([m for m in mutations.values() if m]))
        else:
            features["tp53_mutation"] = 0.0
            features["pik3ca_mutation"] = 0.0
            features["kras_mutation"] = 0.0
            features["mutation_count"] = 0.0
        
        # CNV features
        cnv = biomarkers.get("copy_number_variations", {})
        if isinstance(cnv, dict):
            features["cnv_amplifications"] = float(len([c for c in cnv.values() if c > 1.5]))
            features["cnv_deletions"] = float(len([c for c in cnv.values() if c < 0.5]))
        else:
            features["cnv_amplifications"] = 0.0
            features["cnv_deletions"] = 0.0
        
        # Gene expression features
        expression = biomarkers.get("gene_expression", {})
        if isinstance(expression, dict):
            features["expression_mean"] = float(np.mean(list(expression.values()))) if expression else 0.0
            features["expression_std"] = float(np.std(list(expression.values()))) if expression else 0.0
        else:
            features["expression_mean"] = 0.0
            features["expression_std"] = 0.0
        
        # Radiomics features
        if radiomics_features:
            # First-order
            first_order = radiomics_features.get("first_order", {})
            features["radiomics_mean"] = first_order.get("mean", 0.0)
            features["radiomics_std"] = first_order.get("std", 0.0)
            features["radiomics_skewness"] = first_order.get("skewness", 0.0)
            features["radiomics_kurtosis"] = first_order.get("kurtosis", 0.0)
            features["radiomics_entropy"] = first_order.get("entropy", 0.0)
            
            # Texture
            texture = radiomics_features.get("texture", {})
            features["radiomics_contrast"] = texture.get("contrast", 0.0)
            features["radiomics_homogeneity"] = texture.get("homogeneity", 0.0)
            features["radiomics_energy"] = texture.get("energy", 0.0)
            features["radiomics_correlation"] = texture.get("correlation", 0.0)
            
            # Shape
            shape = radiomics_features.get("shape", {})
            features["radiomics_area"] = shape.get("area", 0.0)
            features["radiomics_compactness"] = shape.get("compactness", 0.0)
            features["radiomics_sphericity"] = shape.get("sphericity", 0.0)
        else:
            # Default values if no radiomics
            for key in ["radiomics_mean", "radiomics_std", "radiomics_skewness", 
                       "radiomics_kurtosis", "radiomics_entropy", "radiomics_contrast",
                       "radiomics_homogeneity", "radiomics_energy", "radiomics_correlation",
                       "radiomics_area", "radiomics_compactness", "radiomics_sphericity"]:
                features[key] = 0.0
        
        return pd.DataFrame([features])

    def _rule_based_prediction(
        self,
        biomarkers: Dict[str, Any],
        radiomics_features: Optional[Dict[str, Any]]
    ) -> Tuple[float, float]:
        """پیش‌بینی بر اساس قوانین (fallback)"""
        score = 0.5  # Base probability
        confidence = 0.7
        
        # PD-L1 positive increases response
        if biomarkers.get("pdl1_status") == "positive":
            pdl1_pct = biomarkers.get("pdl1_percentage", 0) or 0
            score += 0.15 * (pdl1_pct / 100.0)
        
        # MSI-H increases response
        if biomarkers.get("msi_status") == "MSI-H":
            score += 0.2
        
        # HER2 positive (for targeted therapy)
        if biomarkers.get("her2_status") == "positive":
            score += 0.1
        
        # Mutation burden
        mutations = biomarkers.get("mutations", {})
        if isinstance(mutations, dict):
            mutation_count = len([m for m in mutations.values() if m])
            if mutation_count > 5:  # High mutation burden
                score += 0.1
        
        # Radiomics features
        if radiomics_features:
            texture = radiomics_features.get("texture", {})
            homogeneity = texture.get("homogeneity", 0.5)
            # Higher homogeneity may indicate better response
            score += 0.05 * (homogeneity - 0.5)
            
            first_order = radiomics_features.get("first_order", {})
            entropy = first_order.get("entropy", 0.0)
            # Moderate entropy may indicate better response
            if 2.0 < entropy < 6.0:
                score += 0.05
        
        # Normalize to 0-1
        score = max(0.0, min(1.0, score))
        
        # Adjust confidence based on data completeness
        data_completeness = self._assess_data_completeness(biomarkers, radiomics_features)
        confidence = 0.5 + 0.3 * data_completeness
        
        return score, confidence

    def _ml_prediction(self, features: pd.DataFrame) -> Tuple[float, float]:
        """پیش‌بینی با مدل ML"""
        try:
            if self.response_model is None:
                return self._rule_based_prediction({}, None)
            
            # Predict
            if hasattr(self.response_model, 'predict_proba'):
                probabilities = self.response_model.predict_proba(features)
                response_prob = float(probabilities[0][1]) if len(probabilities[0]) > 1 else float(probabilities[0][0])
            else:
                prediction = self.response_model.predict(features)
                response_prob = float(prediction[0])
            
            confidence = 0.85  # ML models have higher confidence
            
            return response_prob, confidence
            
        except Exception as e:
            logger.error(f"Error in ML prediction: {str(e)}")
            return self._rule_based_prediction({}, None)

    def _calculate_biomarker_contribution(self, biomarkers: Dict[str, Any]) -> Dict[str, float]:
        """محاسبه سهم بیومارکرها"""
        contributions = {}
        
        # PD-L1
        if biomarkers.get("pdl1_status") == "positive":
            pdl1_pct = biomarkers.get("pdl1_percentage", 0) or 0
            contributions["PD-L1"] = min(1.0, pdl1_pct / 50.0)  # Normalize to 0-1
        else:
            contributions["PD-L1"] = 0.0
        
        # MSI
        if biomarkers.get("msi_status") == "MSI-H":
            contributions["MSI-H"] = 1.0
        else:
            contributions["MSI-H"] = 0.0
        
        # HER2
        if biomarkers.get("her2_status") == "positive":
            contributions["HER2"] = 1.0
        else:
            contributions["HER2"] = 0.0
        
        # Mutation burden
        mutations = biomarkers.get("mutations", {})
        if isinstance(mutations, dict):
            mutation_count = len([m for m in mutations.values() if m])
            contributions["Mutation_Burden"] = min(1.0, mutation_count / 10.0)
        else:
            contributions["Mutation_Burden"] = 0.0
        
        return contributions

    def _calculate_radiomics_contribution(self, radiomics_features: Dict[str, Any]) -> Dict[str, float]:
        """محاسبه سهم رادیومیکس"""
        contributions = {}
        
        if not radiomics_features:
            return contributions
        
        # Texture features
        texture = radiomics_features.get("texture", {})
        contributions["Texture_Homogeneity"] = texture.get("homogeneity", 0.0)
        contributions["Texture_Contrast"] = min(1.0, texture.get("contrast", 0.0) / 10.0)
        
        # First-order features
        first_order = radiomics_features.get("first_order", {})
        contributions["First_Order_Entropy"] = min(1.0, first_order.get("entropy", 0.0) / 8.0)
        contributions["First_Order_Skewness"] = abs(first_order.get("skewness", 0.0)) / 2.0
        
        # Shape features
        shape = radiomics_features.get("shape", {})
        contributions["Shape_Compactness"] = shape.get("compactness", 0.0)
        
        return contributions

    def _categorize_response(self, probability: float) -> str:
        """دسته‌بندی احتمال پاسخ"""
        if probability >= 0.7:
            return "High"
        elif probability >= 0.4:
            return "Moderate"
        else:
            return "Low"

    def _identify_key_factors(
        self,
        biomarkers: Dict[str, Any],
        radiomics_features: Optional[Dict[str, Any]],
        biomarkers_contrib: Dict[str, float],
        radiomics_contrib: Dict[str, float]
    ) -> List[str]:
        """شناسایی عوامل کلیدی"""
        factors = []
        
        # Top biomarker contributors
        sorted_biomarkers = sorted(biomarkers_contrib.items(), key=lambda x: x[1], reverse=True)
        for factor, value in sorted_biomarkers[:3]:
            if value > 0.3:
                factors.append(f"{factor} (contribution: {value:.2f})")
        
        # Top radiomics contributors
        if radiomics_contrib:
            sorted_radiomics = sorted(radiomics_contrib.items(), key=lambda x: x[1], reverse=True)
            for factor, value in sorted_radiomics[:2]:
                if value > 0.3:
                    factors.append(f"{factor} (contribution: {value:.2f})")
        
        return factors

    def _generate_recommendation(
        self,
        probability: float,
        category: str,
        treatment_type: str,
        key_factors: List[str]
    ) -> str:
        """تولید توصیه"""
        if category == "High":
            recommendation = (
                f"High probability ({probability:.1%}) of successful response to {treatment_type}. "
                f"Neoadjuvant {treatment_type} is strongly recommended. "
            )
        elif category == "Moderate":
            recommendation = (
                f"Moderate probability ({probability:.1%}) of response to {treatment_type}. "
                f"Neoadjuvant {treatment_type} may be considered with close monitoring. "
            )
        else:
            recommendation = (
                f"Low probability ({probability:.1%}) of response to {treatment_type}. "
                f"Consider alternative treatment strategies or upfront surgery. "
            )
        
        if key_factors:
            recommendation += f"Key predictive factors: {', '.join(key_factors)}."
        
        return recommendation

    def _assess_data_completeness(
        self,
        biomarkers: Dict[str, Any],
        radiomics_features: Optional[Dict[str, Any]]
    ) -> float:
        """ارزیابی کامل بودن داده"""
        completeness = 0.0
        
        # Biomarker completeness
        biomarker_count = 0
        if biomarkers.get("pdl1_status"):
            biomarker_count += 1
        if biomarkers.get("msi_status"):
            biomarker_count += 1
        if biomarkers.get("her2_status"):
            biomarker_count += 1
        if biomarkers.get("mutations"):
            biomarker_count += 1
        
        completeness += (biomarker_count / 4.0) * 0.6
        
        # Radiomics completeness
        if radiomics_features:
            completeness += 0.4
        
        return completeness

    def _load_model(self, model_info: Dict) -> Optional[Any]:
        """بارگذاری مدل"""
        try:
            model_path = model_info.get("model_path")
            
            # Try TensorFlow/Keras
            try:
                import tensorflow as tf
                from tensorflow import keras
                model = keras.models.load_model(model_path)
                return model
            except:
                pass
            
            # Try PyTorch
            try:
                import torch
                model = torch.load(model_path, map_location='cpu')
                if isinstance(model, torch.nn.Module):
                    model.eval()
                    return model
            except:
                pass
            
            # Try pickle
            try:
                import pickle
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                return model
            except:
                pass
            
            return None
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return None

