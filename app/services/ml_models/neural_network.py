"""
Neural network models using TensorFlow/Keras
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    tf = None
    keras = None
    layers = None
    models = None

from app.services.ml_models.base_model import BaseMLModel


class NeuralNetworkModel(BaseMLModel):
    """Neural Network model using TensorFlow"""

    def __init__(self, architecture: str = "simple", **kwargs):
        super().__init__("NeuralNetwork", **kwargs)
        self.architecture = architecture
        self.history = None

    def build_model(
        self,
        input_shape: int,
        num_classes: int = 2,
        architecture: Optional[str] = None,
        **kwargs
    ):
        """Build neural network model"""
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is not installed. Install with: pip install tensorflow")
        
        arch = architecture or self.architecture

        if arch == "simple":
            self.model = models.Sequential(
                [
                    layers.Dense(64, activation="relu", input_shape=(input_shape,)),
                    layers.Dropout(0.3),
                    layers.Dense(32, activation="relu"),
                    layers.Dropout(0.3),
                    layers.Dense(num_classes, activation="softmax"),
                ]
            )
        elif arch == "deep":
            self.model = models.Sequential(
                [
                    layers.Dense(128, activation="relu", input_shape=(input_shape,)),
                    layers.Dropout(0.3),
                    layers.Dense(64, activation="relu"),
                    layers.Dropout(0.3),
                    layers.Dense(32, activation="relu"),
                    layers.Dropout(0.3),
                    layers.Dense(num_classes, activation="softmax"),
                ]
            )
        else:
            raise ValueError(f"Unknown architecture: {arch}")

        # Compile model
        self.model.compile(
            optimizer=kwargs.get("optimizer", "adam"),
            loss=kwargs.get("loss", "sparse_categorical_crossentropy"),
            metrics=["accuracy"],
        )

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Train model"""
        self.feature_names = X_train.columns.tolist()

        # Build model if not built
        if self.model is None:
            self.build_model(
                input_shape=X_train.shape[1],
                num_classes=len(y_train.unique()),
                **kwargs
            )

        # Prepare validation data
        validation_data = None
        if X_val is not None and y_val is not None:
            validation_data = (X_val.values, y_val.values)

        # Train
        self.history = self.model.fit(
            X_train.values,
            y_train.values,
            epochs=kwargs.get("epochs", 50),
            batch_size=kwargs.get("batch_size", 32),
            validation_data=validation_data,
            verbose=kwargs.get("verbose", 1),
            callbacks=kwargs.get("callbacks", []),
        )

        self.is_trained = True

        # Extract training history
        history_dict = {
            "train_accuracy": float(self.history.history["accuracy"][-1]),
            "train_loss": float(self.history.history["loss"][-1]),
        }

        if validation_data:
            history_dict["val_accuracy"] = float(
                self.history.history["val_accuracy"][-1]
            )
            history_dict["val_loss"] = float(self.history.history["val_loss"][-1])

        self.training_history = history_dict
        return history_dict

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        predictions = self.model.predict(X.values, verbose=0)
        return np.argmax(predictions, axis=1)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict probabilities"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        return self.model.predict(X.values, verbose=0)

    def save_model(self, filepath: str):
        """Save model"""
        if not self.is_trained:
            raise ValueError("Model must be trained before saving")
        self.model.save(filepath)

    def load_model(self, filepath: str):
        """Load model"""
        self.model = keras.models.load_model(filepath)
        self.is_trained = True

