"""
Base class for ML models
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin


class BaseMLModel(ABC):
    """Base class for all ML models"""

    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.model = None
        self.is_trained = False
        self.feature_names = []
        self.training_history = {}

    @abstractmethod
    def build_model(self, input_shape: Optional[int] = None, **kwargs):
        """Build the model architecture"""
        pass

    @abstractmethod
    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Train the model"""
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions"""
        pass

    @abstractmethod
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict probabilities"""
        pass

    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """Evaluate model performance"""
        from sklearn.metrics import (
            accuracy_score,
            precision_score,
            recall_score,
            f1_score,
            roc_auc_score,
        )

        y_pred = self.predict(X)
        y_proba = self.predict_proba(X)[:, 1] if len(y_proba.shape) > 1 else y_proba

        metrics = {
            "accuracy": accuracy_score(y, y_pred),
            "precision": precision_score(y, y_pred, average="weighted", zero_division=0),
            "recall": recall_score(y, y_pred, average="weighted", zero_division=0),
            "f1_score": f1_score(y, y_pred, average="weighted", zero_division=0),
        }

        try:
            metrics["roc_auc"] = roc_auc_score(y, y_proba)
        except:
            metrics["roc_auc"] = 0.0

        return metrics

    def save_model(self, filepath: str):
        """Save model to file"""
        import pickle

        with open(filepath, "wb") as f:
            pickle.dump(
                {
                    "model": self.model,
                    "model_name": self.model_name,
                    "feature_names": self.feature_names,
                    "is_trained": self.is_trained,
                },
                f,
            )

    def load_model(self, filepath: str):
        """Load model from file"""
        import pickle

        with open(filepath, "rb") as f:
            data = pickle.load(f)
            self.model = data["model"]
            self.model_name = data["model_name"]
            self.feature_names = data["feature_names"]
            self.is_trained = data["is_trained"]

