"""
Neural network models using TensorFlow/Keras
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models, callbacks
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    tf = None
    keras = None
    layers = None
    models = None
    callbacks = None

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

        # Improved architectures for better accuracy
        if arch == "simple":
            self.model = models.Sequential(
                [
                    layers.Dense(128, activation="relu", input_shape=(input_shape,)),
                    layers.BatchNormalization(),
                    layers.Dropout(0.3),
                    layers.Dense(64, activation="relu"),
                    layers.BatchNormalization(),
                    layers.Dropout(0.3),
                    layers.Dense(32, activation="relu"),
                    layers.Dropout(0.2),
                    layers.Dense(num_classes, activation="softmax" if num_classes > 2 else "sigmoid"),
                ]
            )
        elif arch == "deep":
            self.model = models.Sequential(
                [
                    layers.Dense(256, activation="relu", input_shape=(input_shape,)),
                    layers.BatchNormalization(),
                    layers.Dropout(0.4),
                    layers.Dense(128, activation="relu"),
                    layers.BatchNormalization(),
                    layers.Dropout(0.3),
                    layers.Dense(64, activation="relu"),
                    layers.BatchNormalization(),
                    layers.Dropout(0.3),
                    layers.Dense(32, activation="relu"),
                    layers.Dropout(0.2),
                    layers.Dense(num_classes, activation="softmax" if num_classes > 2 else "sigmoid"),
                ]
            )
        else:
            raise ValueError(f"Unknown architecture: {arch}")

        # Compile model with improved optimizer settings
        optimizer_name = kwargs.get("optimizer", "adam")
        learning_rate = kwargs.get("learning_rate", 0.001)
        
        if optimizer_name == "adam":
            from tensorflow.keras.optimizers import Adam
            optimizer = Adam(learning_rate=learning_rate, beta_1=0.9, beta_2=0.999)
        else:
            optimizer = optimizer_name
        
        self.model.compile(
            optimizer=optimizer,
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

        # Enhanced training with callbacks for better accuracy
        callbacks_list = kwargs.get("callbacks", [])
        
        # Add early stopping and learning rate reduction if not already present
        if TENSORFLOW_AVAILABLE:
            if not any(isinstance(cb, keras.callbacks.EarlyStopping) for cb in callbacks_list):
                callbacks_list.append(
                    keras.callbacks.EarlyStopping(
                        monitor='val_accuracy' if validation_data else 'accuracy',
                        patience=10,
                        restore_best_weights=True,
                        verbose=0
                    )
                )
            
            if not any(isinstance(cb, keras.callbacks.ReduceLROnPlateau) for cb in callbacks_list):
                callbacks_list.append(
                    keras.callbacks.ReduceLROnPlateau(
                        monitor='val_accuracy' if validation_data else 'accuracy',
                        factor=0.5,
                        patience=5,
                        min_lr=1e-7,
                        verbose=0
                    )
                )
        
        # Train
        self.history = self.model.fit(
            X_train.values,
            y_train.values,
            epochs=kwargs.get("epochs", 100),
            batch_size=kwargs.get("batch_size", 32),
            validation_data=validation_data,
            verbose=kwargs.get("verbose", 1),
            callbacks=callbacks_list,
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

