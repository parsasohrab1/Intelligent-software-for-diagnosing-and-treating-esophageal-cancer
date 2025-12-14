"""
Prototypical Networks for Few-Shot Learning
شبکه‌های Prototypical برای یادگیری با داده‌های کم

این معماری برای تشخیص زیرگونه‌های نادر سرطان مری طراحی شده است.
"""
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models, Model
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    tf = None
    keras = None
    layers = None
    models = None
    Model = None

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    torch = None
    nn = None
    F = None

# Type checking imports - use Any to avoid runtime errors when tf is None
# At runtime, we'll use Any; type checkers can use tf.Tensor if available
TensorType = Any


@dataclass
class FewShotTask:
    """Task برای Few-Shot Learning"""
    support_set: np.ndarray  # نمونه‌های support (N-way, K-shot)
    support_labels: np.ndarray
    query_set: np.ndarray  # نمونه‌های query
    query_labels: np.ndarray
    n_way: int  # تعداد کلاس‌ها
    k_shot: int  # تعداد نمونه در هر کلاس


class PrototypicalNetwork:
    """
    Prototypical Network برای Few-Shot Learning
    
    این شبکه با یادگیری یک embedding space که در آن نمونه‌های هر کلاس
    به یک prototype نزدیک می‌شوند، کار می‌کند.
    """
    
    def __init__(
        self,
        embedding_dim: int = 64,
        use_transfer_learning: bool = True,
        base_model: Optional[Any] = None
    ):
        """
        Args:
            embedding_dim: بعد embedding
            use_transfer_learning: استفاده از transfer learning
            base_model: مدل پایه برای transfer learning
        """
        self.embedding_dim = embedding_dim
        self.use_transfer_learning = use_transfer_learning
        self.base_model = base_model
        self.embedding_model = None
        
    def build_embedding_network(
        self,
        input_shape: Tuple[int, ...],
        architecture: str = "cnn"
    ) -> Model:
        """
        ساخت شبکه embedding
        
        Args:
            input_shape: شکل ورودی
            architecture: نوع معماری (cnn, resnet, efficientnet)
        """
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is not available")
        
        inputs = layers.Input(shape=input_shape)
        
        if self.use_transfer_learning and self.base_model is not None:
            # Use pre-trained base model
            if hasattr(self.base_model, 'layers'):
                # Freeze early layers
                for layer in self.base_model.layers[:-2]:
                    layer.trainable = False
                x = self.base_model(inputs)
            else:
                x = self._build_cnn_embedding(inputs)
        else:
            if architecture == "cnn":
                x = self._build_cnn_embedding(inputs)
            elif architecture == "resnet":
                x = self._build_resnet_embedding(inputs)
            else:
                x = self._build_cnn_embedding(inputs)
        
        # Project to embedding dimension
        x = layers.GlobalAveragePooling2D()(x) if len(x.shape) == 4 else x
        x = layers.Dense(256, activation='relu')(x)
        x = layers.Dropout(0.3)(x)
        x = layers.Dense(128, activation='relu')(x)
        x = layers.Dropout(0.2)(x)
        outputs = layers.Dense(self.embedding_dim, name='embedding')(x)
        
        self.embedding_model = Model(inputs, outputs, name='prototypical_embedding')
        return self.embedding_model
    
    def _build_cnn_embedding(self, inputs: TensorType) -> TensorType:
        """ساخت CNN embedding"""
        x = layers.Conv2D(64, (3, 3), padding='same', activation='relu')(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling2D((2, 2))(x)
        
        x = layers.Conv2D(128, (3, 3), padding='same', activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling2D((2, 2))(x)
        
        x = layers.Conv2D(256, (3, 3), padding='same', activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling2D((2, 2))(x)
        
        return x
    
    def _build_resnet_embedding(self, inputs: TensorType) -> TensorType:
        """ساخت ResNet-like embedding"""
        # Simplified ResNet blocks
        x = layers.Conv2D(64, (7, 7), strides=2, padding='same')(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.Activation('relu')(x)
        x = layers.MaxPooling2D((3, 3), strides=2, padding='same')(x)
        
        # Residual blocks
        for filters in [128, 256]:
            x = self._residual_block(x, filters)
        
        return x
    
    def _residual_block(self, x: TensorType, filters: int) -> TensorType:
        """Residual block"""
        shortcut = x
        
        x = layers.Conv2D(filters, (3, 3), padding='same')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Activation('relu')(x)
        
        x = layers.Conv2D(filters, (3, 3), padding='same')(x)
        x = layers.BatchNormalization()(x)
        
        if shortcut.shape[-1] != filters:
            shortcut = layers.Conv2D(filters, 1, padding='same')(shortcut)
            shortcut = layers.BatchNormalization()(shortcut)
        
        x = layers.Add()([x, shortcut])
        x = layers.Activation('relu')(x)
        
        return x
    
    def compute_prototypes(
        self,
        support_set: np.ndarray,
        support_labels: np.ndarray
    ) -> Dict[int, np.ndarray]:
        """
        محاسبه prototypes برای هر کلاس
        
        Args:
            support_set: نمونه‌های support
            support_labels: برچسب‌های support
            
        Returns:
            Dictionary mapping class_id to prototype
        """
        if self.embedding_model is None:
            raise ValueError("Embedding model must be built first")
        
        # Get embeddings
        embeddings = self.embedding_model.predict(support_set, verbose=0)
        
        # Compute prototypes (mean of embeddings for each class)
        prototypes = {}
        unique_labels = np.unique(support_labels)
        
        for label in unique_labels:
            class_embeddings = embeddings[support_labels == label]
            prototype = np.mean(class_embeddings, axis=0)
            prototypes[int(label)] = prototype
        
        return prototypes
    
    def predict(
        self,
        query_set: np.ndarray,
        prototypes: Dict[int, np.ndarray]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        پیش‌بینی برای query set
        
        Args:
            query_set: نمونه‌های query
            prototypes: prototypes هر کلاس
            
        Returns:
            (predictions, distances)
        """
        if self.embedding_model is None:
            raise ValueError("Embedding model must be built first")
        
        # Get query embeddings
        query_embeddings = self.embedding_model.predict(query_set, verbose=0)
        
        # Compute distances to prototypes
        predictions = []
        distances = []
        
        for query_emb in query_embeddings:
            class_distances = {}
            for class_id, prototype in prototypes.items():
                # Euclidean distance
                distance = np.linalg.norm(query_emb - prototype)
                class_distances[class_id] = distance
            
            # Predict class with minimum distance
            predicted_class = min(class_distances, key=class_distances.get)
            predictions.append(predicted_class)
            distances.append(class_distances)
        
        return np.array(predictions), np.array(distances)
    
    def train_episode(
        self,
        task: FewShotTask,
        epochs: int = 10,
        learning_rate: float = 0.001
    ) -> Dict[str, Any]:
        """
        آموزش روی یک episode
        
        Args:
            task: Few-shot task
            epochs: تعداد epochs
            learning_rate: نرخ یادگیری
            
        Returns:
            Training history
        """
        if self.embedding_model is None:
            raise ValueError("Embedding model must be built first")
        
        # Compile model
        self.embedding_model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
            loss=self._prototypical_loss,
            metrics=['accuracy']
        )
        
        # Prepare data
        # For prototypical networks, we use episodic training
        # Each episode: compute prototypes, then classify queries
        
        history = {
            'loss': [],
            'accuracy': []
        }
        
        for epoch in range(epochs):
            # Compute prototypes
            prototypes = self.compute_prototypes(
                task.support_set,
                task.support_labels
            )
            
            # Predict queries
            predictions, distances = self.predict(
                task.query_set,
                prototypes
            )
            
            # Compute loss and accuracy
            loss = self._compute_episode_loss(
                task.query_set,
                task.query_labels,
                prototypes
            )
            
            accuracy = np.mean(predictions == task.query_labels)
            
            history['loss'].append(float(loss))
            history['accuracy'].append(float(accuracy))
            
            # Update model (simplified - in production use proper training loop)
            # This is a placeholder for the actual training procedure
        
        return history
    
    def _prototypical_loss(self, y_true, y_pred):
        """Loss function برای prototypical networks"""
        # This is a placeholder - actual implementation would compute
        # distances to prototypes and use cross-entropy
        return keras.losses.sparse_categorical_crossentropy(y_true, y_pred)
    
    def _compute_episode_loss(
        self,
        query_set: np.ndarray,
        query_labels: np.ndarray,
        prototypes: Dict[int, np.ndarray]
    ) -> float:
        """محاسبه loss برای یک episode"""
        query_embeddings = self.embedding_model.predict(query_set, verbose=0)
        
        # Compute distances to all prototypes
        distances = []
        for query_emb in query_embeddings:
            class_distances = []
            for class_id in sorted(prototypes.keys()):
                distance = np.linalg.norm(query_emb - prototypes[class_id])
                class_distances.append(distance)
            distances.append(class_distances)
        
        distances = np.array(distances)
        
        # Convert distances to probabilities (softmax over negative distances)
        logits = -distances
        probabilities = tf.nn.softmax(logits, axis=1)
        
        # Compute cross-entropy loss
        labels_one_hot = tf.one_hot(query_labels, depth=len(prototypes))
        loss = tf.reduce_mean(
            tf.keras.losses.categorical_crossentropy(labels_one_hot, probabilities)
        )
        
        return float(loss.numpy())

