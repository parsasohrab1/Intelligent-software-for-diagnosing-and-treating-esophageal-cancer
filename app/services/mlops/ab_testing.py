"""
A/B Testing Framework for ML Models
"""
import random
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict

from app.core.mongodb import get_mongodb_database
from app.services.model_registry import ModelRegistry
from app.services.mlops.model_monitoring import ModelMonitoring

logger = logging.getLogger(__name__)


class ABTestManager:
    """
    Manage A/B testing for ML models
    """

    def __init__(self):
        self.db = get_mongodb_database()
        self.ab_test_collection = (
            self.db["ab_tests"] if self.db is not None else None
        )
        self.registry = ModelRegistry()
        self.monitoring = ModelMonitoring()
        self.active_tests: Dict[str, Dict] = {}

    def create_ab_test(
        self,
        test_name: str,
        control_model_id: str,
        treatment_model_id: str,
        traffic_split: float = 0.5,
        metric: str = "accuracy",
    ) -> str:
        """
        Create a new A/B test
        """
        try:
            # Validate models exist
            control_model = self.registry.get_model(control_model_id)
            treatment_model = self.registry.get_model(treatment_model_id)

            if not control_model or not treatment_model:
                raise ValueError("One or both models not found")

            test_id = f"ab_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            test_config = {
                "test_id": test_id,
                "test_name": test_name,
                "control_model_id": control_model_id,
                "treatment_model_id": treatment_model_id,
                "traffic_split": traffic_split,  # Percentage of traffic to treatment
                "metric": metric,
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "results": {
                    "control": {
                        "predictions": 0,
                        "correct": 0,
                        "metrics": {},
                    },
                    "treatment": {
                        "predictions": 0,
                        "correct": 0,
                        "metrics": {},
                    },
                },
            }

            if self.ab_test_collection:
                self.ab_test_collection.insert_one(test_config)

            self.active_tests[test_id] = test_config

            logger.info(f"Created A/B test: {test_id}")
            return test_id

        except Exception as e:
            logger.error(f"Error creating A/B test: {str(e)}")
            raise

    def select_model(self, test_id: str, user_id: Optional[str] = None) -> Tuple[str, str]:
        """
        Select which model to use for a prediction (control or treatment)
        Returns: (model_id, variant)
        """
        try:
            test_config = self.active_tests.get(test_id)
            if not test_config:
                # Try to load from database
                if self.ab_test_collection:
                    test_config = self.ab_test_collection.find_one({"test_id": test_id})
                    if test_config:
                        self.active_tests[test_id] = test_config

            if not test_config or test_config.get("status") != "active":
                raise ValueError(f"A/B test {test_id} not found or not active")

            # Use consistent hashing based on user_id for sticky assignment
            if user_id:
                # Hash user_id to get consistent assignment
                hash_value = hash(user_id) % 100
                traffic_split_percent = test_config["traffic_split"] * 100
                variant = "treatment" if hash_value < traffic_split_percent else "control"
            else:
                # Random assignment
                variant = (
                    "treatment"
                    if random.random() < test_config["traffic_split"]
                    else "control"
                )

            model_id = (
                test_config["treatment_model_id"]
                if variant == "treatment"
                else test_config["control_model_id"]
            )

            return model_id, variant

        except Exception as e:
            logger.error(f"Error selecting model: {str(e)}")
            # Fallback to control model
            if test_config:
                return test_config["control_model_id"], "control"
            raise

    def record_prediction_result(
        self,
        test_id: str,
        variant: str,
        prediction: float,
        ground_truth: Optional[float] = None,
        metrics: Optional[Dict] = None,
    ):
        """
        Record prediction result for A/B test analysis
        """
        try:
            test_config = self.active_tests.get(test_id)
            if not test_config:
                if self.ab_test_collection:
                    test_config = self.ab_test_collection.find_one({"test_id": test_id})
                    if test_config:
                        self.active_tests[test_id] = test_config

            if not test_config:
                return

            # Update results
            results = test_config.get("results", {})
            variant_results = results.get(variant, {"predictions": 0, "correct": 0, "metrics": {}})

            variant_results["predictions"] += 1

            if ground_truth is not None:
                if prediction == ground_truth:
                    variant_results["correct"] += 1

                # Update metrics
                if metrics:
                    for metric_name, metric_value in metrics.items():
                        if metric_name not in variant_results["metrics"]:
                            variant_results["metrics"][metric_name] = []
                        variant_results["metrics"][metric_name].append(metric_value)

            results[variant] = variant_results
            test_config["results"] = results

            # Update in database
            if self.ab_test_collection:
                self.ab_test_collection.update_one(
                    {"test_id": test_id},
                    {"$set": {"results": results, "updated_at": datetime.now().isoformat()}},
                )

            self.active_tests[test_id] = test_config

        except Exception as e:
            logger.error(f"Error recording prediction result: {str(e)}")

    def get_test_results(self, test_id: str) -> Dict:
        """
        Get A/B test results and statistical analysis
        """
        try:
            test_config = self.active_tests.get(test_id)
            if not test_config:
                if self.ab_test_collection:
                    test_config = self.ab_test_collection.find_one({"test_id": test_id})

            if not test_config:
                raise ValueError(f"A/B test {test_id} not found")

            results = test_config.get("results", {})
            control_results = results.get("control", {})
            treatment_results = results.get("treatment", {})

            # Calculate metrics
            control_accuracy = (
                control_results["correct"] / control_results["predictions"]
                if control_results["predictions"] > 0
                else 0.0
            )
            treatment_accuracy = (
                treatment_results["correct"] / treatment_results["predictions"]
                if treatment_results["predictions"] > 0
                else 0.0
            )

            # Statistical significance test (simplified)
            import numpy as np
            from scipy import stats

            significance = None
            if (
                control_results["predictions"] > 30
                and treatment_results["predictions"] > 30
            ):
                # Perform chi-square test for proportions
                control_correct = control_results["correct"]
                control_total = control_results["predictions"]
                treatment_correct = treatment_results["correct"]
                treatment_total = treatment_results["predictions"]

                contingency_table = [
                    [control_correct, control_total - control_correct],
                    [treatment_correct, treatment_total - treatment_correct],
                ]
                chi2, p_value = stats.chi2_contingency(contingency_table)[:2]

                significance = {
                    "chi2": float(chi2),
                    "p_value": float(p_value),
                    "significant": p_value < 0.05,
                }

            return {
                "test_id": test_id,
                "test_name": test_config.get("test_name"),
                "status": test_config.get("status"),
                "control": {
                    "model_id": test_config["control_model_id"],
                    "predictions": control_results["predictions"],
                    "accuracy": float(control_accuracy),
                    "metrics": control_results.get("metrics", {}),
                },
                "treatment": {
                    "model_id": test_config["treatment_model_id"],
                    "predictions": treatment_results["predictions"],
                    "accuracy": float(treatment_accuracy),
                    "metrics": treatment_results.get("metrics", {}),
                },
                "improvement": float(treatment_accuracy - control_accuracy),
                "statistical_significance": significance,
                "created_at": test_config.get("created_at"),
            }

        except Exception as e:
            logger.error(f"Error getting test results: {str(e)}")
            raise

    def stop_test(self, test_id: str, winner: Optional[str] = None):
        """
        Stop an A/B test and optionally promote winner
        """
        try:
            test_config = self.active_tests.get(test_id)
            if not test_config:
                if self.ab_test_collection:
                    test_config = self.ab_test_collection.find_one({"test_id": test_id})

            if not test_config:
                raise ValueError(f"A/B test {test_id} not found")

            test_config["status"] = "completed"
            test_config["completed_at"] = datetime.now().isoformat()

            if winner:
                test_config["winner"] = winner
                # Optionally update model status
                if winner == "treatment":
                    self.registry.update_model_status(
                        test_config["treatment_model_id"], "active"
                    )
                    self.registry.update_model_status(
                        test_config["control_model_id"], "archived"
                    )

            if self.ab_test_collection:
                self.ab_test_collection.update_one(
                    {"test_id": test_id},
                    {"$set": test_config},
                )

            if test_id in self.active_tests:
                del self.active_tests[test_id]

            logger.info(f"Stopped A/B test: {test_id}, winner: {winner}")
            return test_config

        except Exception as e:
            logger.error(f"Error stopping test: {str(e)}")
            raise

    def list_active_tests(self) -> List[Dict]:
        """
        List all active A/B tests
        """
        try:
            if self.ab_test_collection:
                tests = list(
                    self.ab_test_collection.find({"status": "active"}).sort(
                        "created_at", -1
                    )
                )
                return [
                    {
                        "test_id": t["test_id"],
                        "test_name": t.get("test_name"),
                        "control_model_id": t["control_model_id"],
                        "treatment_model_id": t["treatment_model_id"],
                        "traffic_split": t.get("traffic_split", 0.5),
                        "created_at": t.get("created_at"),
                    }
                    for t in tests
                ]
            return []

        except Exception as e:
            logger.error(f"Error listing active tests: {str(e)}")
            return []

