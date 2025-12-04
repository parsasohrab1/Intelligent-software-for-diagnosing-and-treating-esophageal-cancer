"""
Model Monitoring Service for Data Drift and Model Decay Detection
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
import logging
from scipy import stats
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from app.core.mongodb import get_mongodb_database
from app.services.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


class ModelMonitoring:
    """
    Monitor ML models for data drift and performance decay
    """

    def __init__(self):
        self.db = get_mongodb_database()
        self.monitoring_collection = (
            self.db["model_monitoring"] if self.db is not None else None
        )
        self.registry = ModelRegistry()
        # In-memory cache for recent predictions
        self.prediction_cache: Dict[str, deque] = {}
        self.performance_cache: Dict[str, deque] = {}

    def record_prediction(
        self,
        model_id: str,
        features: Dict,
        prediction: float,
        probability: Optional[List[float]] = None,
        ground_truth: Optional[float] = None,
    ):
        """
        Record a prediction for monitoring
        """
        if self.monitoring_collection is None:
            return

        try:
            # Store prediction data
            prediction_record = {
                "model_id": model_id,
                "features": features,
                "prediction": float(prediction),
                "probability": probability,
                "ground_truth": ground_truth,
                "timestamp": datetime.now().isoformat(),
            }

            self.monitoring_collection.insert_one(prediction_record)

            # Update in-memory cache
            if model_id not in self.prediction_cache:
                self.prediction_cache[model_id] = deque(maxlen=1000)
            self.prediction_cache[model_id].append({
                "features": features,
                "prediction": prediction,
                "ground_truth": ground_truth,
            })

            # Check for drift periodically
            if len(self.prediction_cache[model_id]) % 100 == 0:
                self._check_data_drift(model_id)

            # If ground truth is available, check for model decay
            if ground_truth is not None:
                if model_id not in self.performance_cache:
                    self.performance_cache[model_id] = deque(maxlen=1000)
                self.performance_cache[model_id].append({
                    "prediction": prediction,
                    "ground_truth": ground_truth,
                })

                if len(self.performance_cache[model_id]) % 100 == 0:
                    self._check_model_decay(model_id)

        except Exception as e:
            logger.error(f"Error recording prediction: {str(e)}")

    def _check_data_drift(self, model_id: str) -> Dict:
        """
        Check for data drift using statistical tests
        """
        try:
            model_info = self.registry.get_model(model_id)
            if not model_info:
                return {"drift_detected": False}

            # Get baseline data (training data statistics)
            baseline_stats = model_info.get("baseline_statistics", {})
            if not baseline_stats:
                return {"drift_detected": False, "reason": "No baseline statistics"}

            # Get recent predictions
            recent_predictions = list(self.prediction_cache.get(model_id, []))
            if len(recent_predictions) < 100:
                return {"drift_detected": False, "reason": "Insufficient data"}

            # Extract features from recent predictions
            recent_features = pd.DataFrame([p["features"] for p in recent_predictions])

            drift_results = {}
            drift_detected = False

            # Check each feature for drift
            for feature_name in model_info.get("feature_names", []):
                if feature_name not in recent_features.columns:
                    continue

                baseline_mean = baseline_stats.get(feature_name, {}).get("mean")
                baseline_std = baseline_stats.get(feature_name, {}).get("std")

                if baseline_mean is None or baseline_std is None:
                    continue

                # Kolmogorov-Smirnov test for distribution shift
                recent_values = recent_features[feature_name].dropna()
                if len(recent_values) < 30:
                    continue

                # Generate baseline distribution sample
                baseline_sample = np.random.normal(
                    baseline_mean, baseline_std, size=min(1000, len(recent_values))
                )

                # Perform KS test
                ks_statistic, p_value = stats.ks_2samp(baseline_sample, recent_values)

                from app.core.config import settings

                if ks_statistic > settings.DATA_DRIFT_THRESHOLD:
                    drift_detected = True
                    drift_results[feature_name] = {
                        "ks_statistic": float(ks_statistic),
                        "p_value": float(p_value),
                        "drift_detected": True,
                    }

            result = {
                "drift_detected": drift_detected,
                "timestamp": datetime.now().isoformat(),
                "feature_drifts": drift_results,
            }

            # Store drift detection result
            if drift_detected:
                self.monitoring_collection.insert_one({
                    "model_id": model_id,
                    "type": "data_drift",
                    "result": result,
                    "timestamp": datetime.now().isoformat(),
                })
                logger.warning(
                    f"Data drift detected for model {model_id}: {drift_results}"
                )

            return result

        except Exception as e:
            logger.error(f"Error checking data drift: {str(e)}")
            return {"drift_detected": False, "error": str(e)}

    def _check_model_decay(self, model_id: str) -> Dict:
        """
        Check for model performance decay
        """
        try:
            model_info = self.registry.get_model(model_id)
            if not model_info:
                return {"decay_detected": False}

            # Get baseline performance metrics
            baseline_metrics = model_info.get("metrics", {})
            baseline_accuracy = baseline_metrics.get("accuracy", 0.0)
            baseline_f1 = baseline_metrics.get("f1_score", 0.0)

            # Get recent performance
            recent_performance = list(self.performance_cache.get(model_id, []))
            if len(recent_performance) < 100:
                return {"decay_detected": False, "reason": "Insufficient data"}

            y_true = [p["ground_truth"] for p in recent_performance]
            y_pred = [p["prediction"] for p in recent_performance]

            current_accuracy = accuracy_score(y_true, y_pred)
            current_f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)

            from app.core.config import settings

            accuracy_decay = baseline_accuracy - current_accuracy
            f1_decay = baseline_f1 - current_f1

            decay_detected = (
                accuracy_decay > settings.MODEL_DECAY_THRESHOLD
                or f1_decay > settings.MODEL_DECAY_THRESHOLD
            )

            result = {
                "decay_detected": decay_detected,
                "timestamp": datetime.now().isoformat(),
                "baseline_accuracy": float(baseline_accuracy),
                "current_accuracy": float(current_accuracy),
                "accuracy_decay": float(accuracy_decay),
                "baseline_f1": float(baseline_f1),
                "current_f1": float(current_f1),
                "f1_decay": float(f1_decay),
            }

            # Store decay detection result
            if decay_detected:
                self.monitoring_collection.insert_one({
                    "model_id": model_id,
                    "type": "model_decay",
                    "result": result,
                    "timestamp": datetime.now().isoformat(),
                })
                logger.warning(
                    f"Model decay detected for model {model_id}: "
                    f"Accuracy decay: {accuracy_decay:.4f}, F1 decay: {f1_decay:.4f}"
                )

            return result

        except Exception as e:
            logger.error(f"Error checking model decay: {str(e)}")
            return {"decay_detected": False, "error": str(e)}

    def get_monitoring_status(self, model_id: str) -> Dict:
        """
        Get current monitoring status for a model
        """
        try:
            if self.monitoring_collection is None:
                return {"status": "monitoring_disabled"}

            # Get recent drift and decay alerts
            recent_alerts = list(
                self.monitoring_collection.find(
                    {"model_id": model_id}
                ).sort("timestamp", -1).limit(10)
            )

            # Get latest drift check
            drift_result = self._check_data_drift(model_id)

            # Get latest decay check
            decay_result = self._check_model_decay(model_id)

            return {
                "model_id": model_id,
                "drift_status": drift_result,
                "decay_status": decay_result,
                "recent_alerts": [
                    {
                        "type": alert.get("type"),
                        "timestamp": alert.get("timestamp"),
                        "result": alert.get("result"),
                    }
                    for alert in recent_alerts
                ],
                "cache_size": len(self.prediction_cache.get(model_id, [])),
            }

        except Exception as e:
            logger.error(f"Error getting monitoring status: {str(e)}")
            return {"error": str(e)}

    def get_all_monitoring_status(self) -> List[Dict]:
        """
        Get monitoring status for all active models
        """
        try:
            registry = ModelRegistry()
            active_models = registry.list_models(status="active")

            return [
                self.get_monitoring_status(model["model_id"])
                for model in active_models
            ]

        except Exception as e:
            logger.error(f"Error getting all monitoring status: {str(e)}")
            return []

