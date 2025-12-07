"""
Few-Shot Learning Service for Rare Subtypes
سرویس Few-Shot Learning برای تشخیص زیرگونه‌های نادر
"""
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from app.services.few_shot_learning.prototypical_networks import (
    PrototypicalNetwork,
    FewShotTask
)
from app.services.few_shot_learning.transfer_learning import (
    TransferLearningOptimizer
)

logger = logging.getLogger(__name__)


class FewShotLearningService:
    """سرویس Few-Shot Learning برای زیرگونه‌های نادر"""
    
    # زیرگونه‌های نادر سرطان مری
    RARE_SUBTYPES = {
        "barretts_adenocarcinoma": {
            "prevalence": 0.01,
            "description": "Adenocarcinoma arising from Barrett's esophagus",
            "min_samples": 5
        },
        "neuroendocrine_carcinoma": {
            "prevalence": 0.02,
            "description": "Neuroendocrine carcinoma of esophagus",
            "min_samples": 5
        },
        "gastrointestinal_stromal_tumor": {
            "prevalence": 0.01,
            "description": "GIST of esophagus",
            "min_samples": 5
        },
        "precancerous_complex": {
            "prevalence": 0.05,
            "description": "Complex precancerous conditions",
            "min_samples": 10
        }
    }
    
    def __init__(
        self,
        method: str = "prototypical",
        use_transfer_learning: bool = True
    ):
        """
        Args:
            method: روش Few-Shot Learning (prototypical, matching, maml)
            use_transfer_learning: استفاده از transfer learning
        """
        self.method = method
        self.use_transfer_learning = use_transfer_learning
        self.prototypical_net = None
        self.transfer_optimizer = None
    
    def initialize_for_subtype(
        self,
        subtype: str,
        input_shape: Tuple[int, ...],
        num_classes: int = 2
    ):
        """
        Initialize برای یک زیرگونه خاص
        
        Args:
            subtype: نام زیرگونه
            input_shape: شکل ورودی
            num_classes: تعداد کلاس‌ها
        """
        if subtype not in self.RARE_SUBTYPES:
            logger.warning(f"Unknown subtype: {subtype}, using default settings")
        
        # Initialize prototypical network
        if self.method == "prototypical":
            self.prototypical_net = PrototypicalNetwork(
                embedding_dim=64,
                use_transfer_learning=self.use_transfer_learning
            )
            
            # Build embedding network
            if len(input_shape) == 3:  # Image
                self.prototypical_net.build_embedding_network(
                    input_shape=input_shape,
                    architecture="resnet" if self.use_transfer_learning else "cnn"
                )
            else:  # Tabular data
                # For tabular data, use dense layers
                self._build_tabular_embedding(input_shape)
        
        # Initialize transfer learning optimizer
        if self.use_transfer_learning and len(input_shape) == 3:
            self.transfer_optimizer = TransferLearningOptimizer(
                base_model_name="resnet50",
                input_shape=input_shape,
                num_classes=num_classes
            )
            self.transfer_optimizer.build_transfer_model(
                freeze_base=True,
                fine_tune_layers=10,
                use_adaptive_unfreezing=True
            )
            self.transfer_optimizer.compile_for_few_shot(
                learning_rate=0.001,
                use_differential_lr=True
            )
    
    def _build_tabular_embedding(self, input_shape: Tuple[int, ...]):
        """ساخت embedding برای داده‌های tabular"""
        try:
            import tensorflow as tf
            from tensorflow import keras
            from tensorflow.keras import layers, Model
            
            inputs = layers.Input(shape=input_shape)
            x = layers.Dense(256, activation='relu')(inputs)
            x = layers.BatchNormalization()(x)
            x = layers.Dropout(0.3)(x)
            x = layers.Dense(128, activation='relu')(x)
            x = layers.BatchNormalization()(x)
            x = layers.Dropout(0.2)(x)
            outputs = layers.Dense(64, name='embedding')(x)
            
            self.prototypical_net.embedding_model = Model(inputs, outputs)
        except ImportError:
            logger.error("TensorFlow not available for tabular embedding")
    
    def train_few_shot(
        self,
        support_set: np.ndarray,
        support_labels: np.ndarray,
        query_set: np.ndarray,
        query_labels: np.ndarray,
        n_way: int,
        k_shot: int,
        epochs: int = 50
    ) -> Dict[str, Any]:
        """
        آموزش Few-Shot Learning
        
        Args:
            support_set: نمونه‌های support
            support_labels: برچسب‌های support
            query_set: نمونه‌های query
            query_labels: برچسب‌های query
            n_way: تعداد کلاس‌ها
            k_shot: تعداد نمونه در هر کلاس
            epochs: تعداد epochs
        """
        try:
            if self.method == "prototypical" and self.prototypical_net:
                # Create task
                task = FewShotTask(
                    support_set=support_set,
                    support_labels=support_labels,
                    query_set=query_set,
                    query_labels=query_labels,
                    n_way=n_way,
                    k_shot=k_shot
                )
                
                # Train
                history = self.prototypical_net.train_episode(
                    task=task,
                    epochs=epochs
                )
                
                # Evaluate
                prototypes = self.prototypical_net.compute_prototypes(
                    support_set, support_labels
                )
                predictions, distances = self.prototypical_net.predict(
                    query_set, prototypes
                )
                
                accuracy = np.mean(predictions == query_labels)
                
                return {
                    "method": "prototypical",
                    "accuracy": float(accuracy),
                    "history": history,
                    "prototypes": {k: v.tolist() for k, v in prototypes.items()}
                }
            
            elif self.use_transfer_learning and self.transfer_optimizer:
                # Use transfer learning
                # Combine support and query for training
                X_train = np.vstack([support_set, query_set])
                y_train = np.hstack([support_labels, query_labels])
                
                # Split for validation
                split_idx = len(support_set)
                X_val = query_set
                y_val = query_labels
                
                history = self.transfer_optimizer.train_with_few_samples(
                    X_train=X_train,
                    y_train=y_train,
                    X_val=X_val,
                    y_val=y_val,
                    epochs=epochs,
                    batch_size=min(8, len(X_train) // 2),
                    use_data_augmentation=True,
                    use_early_stopping=True
                )
                
                # Evaluate
                predictions = self.transfer_optimizer.model.predict(X_val, verbose=0)
                if self.transfer_optimizer.num_classes == 2:
                    predictions = (predictions > 0.5).astype(int).flatten()
                else:
                    predictions = np.argmax(predictions, axis=1)
                
                accuracy = np.mean(predictions == y_val)
                
                return {
                    "method": "transfer_learning",
                    "accuracy": float(accuracy),
                    "history": history,
                    "final_accuracy": history.get('final_accuracy', 0.0)
                }
            
            else:
                raise ValueError("No valid method initialized")
                
        except Exception as e:
            logger.error(f"Error in few-shot training: {str(e)}")
            raise
    
    def predict_rare_subtype(
        self,
        query_samples: np.ndarray,
        support_set: Optional[np.ndarray] = None,
        support_labels: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        پیش‌بینی زیرگونه نادر
        
        Args:
            query_samples: نمونه‌های query
            support_set: نمونه‌های support (اختیاری)
            support_labels: برچسب‌های support (اختیاری)
        """
        try:
            if self.method == "prototypical" and self.prototypical_net:
                if support_set is None or support_labels is None:
                    raise ValueError("Support set required for prototypical networks")
                
                # Compute prototypes
                prototypes = self.prototypical_net.compute_prototypes(
                    support_set, support_labels
                )
                
                # Predict
                predictions, distances = self.prototypical_net.predict(
                    query_samples, prototypes
                )
                
                # Convert distances to probabilities
                probabilities = self._distances_to_probabilities(distances)
                
                return {
                    "predictions": predictions.tolist(),
                    "probabilities": probabilities.tolist(),
                    "distances": distances.tolist(),
                    "confidence": float(np.mean(np.max(probabilities, axis=1)))
                }
            
            elif self.use_transfer_learning and self.transfer_optimizer:
                # Use transfer learning model
                predictions = self.transfer_optimizer.model.predict(
                    query_samples, verbose=0
                )
                
                if self.transfer_optimizer.num_classes == 2:
                    probabilities = predictions.flatten()
                    predicted_classes = (probabilities > 0.5).astype(int)
                else:
                    probabilities = predictions
                    predicted_classes = np.argmax(probabilities, axis=1)
                
                return {
                    "predictions": predicted_classes.tolist(),
                    "probabilities": probabilities.tolist(),
                    "confidence": float(np.mean(np.max(probabilities, axis=1) if len(probabilities.shape) > 1 else probabilities))
                }
            
            else:
                raise ValueError("No valid method initialized")
                
        except Exception as e:
            logger.error(f"Error in prediction: {str(e)}")
            raise
    
    def _distances_to_probabilities(self, distances: np.ndarray) -> np.ndarray:
        """تبدیل فاصله‌ها به احتمال"""
        # Use softmax over negative distances
        logits = -distances
        exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
        probabilities = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
        return probabilities
    
    def get_rare_subtypes_info(self) -> Dict[str, Dict]:
        """دریافت اطلاعات زیرگونه‌های نادر"""
        return self.RARE_SUBTYPES

