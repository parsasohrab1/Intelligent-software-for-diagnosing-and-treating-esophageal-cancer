"""
Multi-Modal Attention Fusion Architecture
معماری ادغام چندوجهی با Attention Mechanism

این معماری نوآورانه برای ادغام مؤثر داده‌های چندگانه:
- تصاویر آندوسکوپی
- داده‌های رادیومیکس (CT/PET)
- اطلاعات آزمایشگاهی/ژنتیکی

با استفاده از Attention Layer برای وزن‌دهی هوشمند
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


@dataclass
class MultiModalInput:
    """ورودی چندوجهی"""
    endoscopy_image: Optional[np.ndarray] = None
    radiomics_features: Optional[np.ndarray] = None
    lab_features: Optional[np.ndarray] = None
    genomic_features: Optional[np.ndarray] = None


class CrossModalAttentionLayer:
    """
    Cross-Modal Attention Layer
    لایه توجه متقابل برای وزن‌دهی هوشمند بین modalities
    
    این لایه نوآورانه می‌تواند موضوع ثبت اختراع باشد.
    """
    
    def __init__(self, embed_dim: int, num_heads: int = 8, dropout: float = 0.1):
        """
        Args:
            embed_dim: بعد embedding
            num_heads: تعداد heads در multi-head attention
            dropout: نرخ dropout
        """
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.dropout = dropout
        
    def build_tensorflow(self):
        """ساخت لایه با TensorFlow"""
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is not available")
        
        # Multi-head self-attention
        self.attention = layers.MultiHeadAttention(
            num_heads=self.num_heads,
            key_dim=self.embed_dim // self.num_heads,
            dropout=self.dropout
        )
        
        # Layer normalization
        self.norm1 = layers.LayerNormalization()
        self.norm2 = layers.LayerNormalization()
        
        # Feed-forward network
        self.ffn = keras.Sequential([
            layers.Dense(self.embed_dim * 4, activation='relu'),
            layers.Dropout(self.dropout),
            layers.Dense(self.embed_dim)
        ])
        
        return self
    
    def __call__(self, inputs: tf.Tensor, training: bool = True) -> tf.Tensor:
        """Forward pass"""
        # Self-attention
        attn_output = self.attention(inputs, inputs, training=training)
        out1 = self.norm1(inputs + attn_output)
        
        # Feed-forward
        ffn_output = self.ffn(out1, training=training)
        out2 = self.norm2(out1 + ffn_output)
        
        return out2


class ModalitySpecificEncoder:
    """Encoder اختصاصی برای هر modality"""
    
    @staticmethod
    def build_endoscopy_encoder(input_shape: Tuple[int, int, int], embed_dim: int = 256):
        """
        Encoder برای تصاویر آندوسکوپی
        استفاده از CNN برای استخراج ویژگی
        """
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is not available")
        
        inputs = layers.Input(shape=input_shape)
        
        # Base CNN (ResNet-like)
        x = layers.Conv2D(64, (7, 7), strides=2, padding='same')(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.Activation('relu')(x)
        x = layers.MaxPooling2D((3, 3), strides=2, padding='same')(x)
        
        # Residual blocks
        for filters in [128, 256, 512]:
            x = ModalitySpecificEncoder._residual_block(x, filters)
        
        # Global average pooling
        x = layers.GlobalAveragePooling2D()(x)
        
        # Projection to embed_dim
        x = layers.Dense(embed_dim, activation='relu')(x)
        x = layers.Dropout(0.3)(x)
        outputs = layers.Dense(embed_dim, name='endoscopy_embedding')(x)
        
        return Model(inputs, outputs, name='endoscopy_encoder')
    
    @staticmethod
    def _residual_block(x, filters, kernel_size=3):
        """Residual block"""
        shortcut = x
        
        x = layers.Conv2D(filters, kernel_size, padding='same')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Activation('relu')(x)
        
        x = layers.Conv2D(filters, kernel_size, padding='same')(x)
        x = layers.BatchNormalization()(x)
        
        # Match dimensions if needed
        if shortcut.shape[-1] != filters:
            shortcut = layers.Conv2D(filters, 1, padding='same')(shortcut)
            shortcut = layers.BatchNormalization()(shortcut)
        
        x = layers.Add()([x, shortcut])
        x = layers.Activation('relu')(x)
        
        return x
    
    @staticmethod
    def build_radiomics_encoder(input_dim: int, embed_dim: int = 256):
        """
        Encoder برای داده‌های رادیومیکس
        استفاده از Dense layers
        """
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is not available")
        
        inputs = layers.Input(shape=(input_dim,))
        
        x = layers.Dense(512, activation='relu')(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        
        x = layers.Dense(256, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        
        outputs = layers.Dense(embed_dim, name='radiomics_embedding')(x)
        
        return Model(inputs, outputs, name='radiomics_encoder')
    
    @staticmethod
    def build_lab_encoder(input_dim: int, embed_dim: int = 128):
        """
        Encoder برای داده‌های آزمایشگاهی
        """
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is not available")
        
        inputs = layers.Input(shape=(input_dim,))
        
        x = layers.Dense(256, activation='relu')(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.2)(x)
        
        x = layers.Dense(128, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        
        outputs = layers.Dense(embed_dim, name='lab_embedding')(x)
        
        return Model(inputs, outputs, name='lab_encoder')
    
    @staticmethod
    def build_genomic_encoder(input_dim: int, embed_dim: int = 128):
        """
        Encoder برای داده‌های ژنتیکی
        """
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is not available")
        
        inputs = layers.Input(shape=(input_dim,))
        
        x = layers.Dense(256, activation='relu')(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.2)(x)
        
        x = layers.Dense(128, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        
        outputs = layers.Dense(embed_dim, name='genomic_embedding')(x)
        
        return Model(inputs, outputs, name='genomic_encoder')


class MultiModalAttentionFusion:
    """
    معماری اصلی ادغام چندوجهی با Attention
    
    این معماری نوآورانه شامل:
    1. Encoders اختصاصی برای هر modality
    2. Cross-Modal Attention Layer برای وزن‌دهی
    3. Fusion Layer برای ادغام نهایی
    4. Prediction Head
    """
    
    def __init__(
        self,
        embed_dim: int = 256,
        num_attention_heads: int = 8,
        num_attention_layers: int = 2,
        dropout: float = 0.1,
        use_positional_encoding: bool = True
    ):
        """
        Args:
            embed_dim: بعد embedding مشترک
            num_attention_heads: تعداد heads در attention
            num_attention_layers: تعداد لایه‌های attention
            dropout: نرخ dropout
            use_positional_encoding: استفاده از positional encoding
        """
        self.embed_dim = embed_dim
        self.num_attention_heads = num_attention_heads
        self.num_attention_layers = num_attention_layers
        self.dropout = dropout
        self.use_positional_encoding = use_positional_encoding
        
        self.model = None
        self.encoders = {}
        self.attention_layers = []
        
    def build_model(
        self,
        endoscopy_shape: Optional[Tuple[int, int, int]] = None,
        radiomics_dim: Optional[int] = None,
        lab_dim: Optional[int] = None,
        genomic_dim: Optional[int] = None,
        num_classes: int = 2
    ) -> Model:
        """
        ساخت مدل کامل
        
        Args:
            endoscopy_shape: شکل تصویر آندوسکوپی (height, width, channels)
            radiomics_dim: بعد ویژگی‌های رادیومیکس
            lab_dim: بعد داده‌های آزمایشگاهی
            genomic_dim: بعد داده‌های ژنتیکی
            num_classes: تعداد کلاس‌های خروجی
        """
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is not available")
        
        # Build encoders
        modality_inputs = {}
        modality_embeddings = []
        
        # Endoscopy encoder
        if endoscopy_shape:
            endoscopy_input = layers.Input(shape=endoscopy_shape, name='endoscopy_input')
            endoscopy_encoder = ModalitySpecificEncoder.build_endoscopy_encoder(
                endoscopy_shape, self.embed_dim
            )
            endoscopy_embed = endoscopy_encoder(endoscopy_input)
            modality_inputs['endoscopy'] = endoscopy_input
            modality_embeddings.append(endoscopy_embed)
            self.encoders['endoscopy'] = endoscopy_encoder
        
        # Radiomics encoder
        if radiomics_dim:
            radiomics_input = layers.Input(shape=(radiomics_dim,), name='radiomics_input')
            radiomics_encoder = ModalitySpecificEncoder.build_radiomics_encoder(
                radiomics_dim, self.embed_dim
            )
            radiomics_embed = radiomics_encoder(radiomics_input)
            modality_inputs['radiomics'] = radiomics_input
            modality_embeddings.append(radiomics_embed)
            self.encoders['radiomics'] = radiomics_encoder
        
        # Lab encoder
        if lab_dim:
            lab_input = layers.Input(shape=(lab_dim,), name='lab_input')
            lab_encoder = ModalitySpecificEncoder.build_lab_encoder(
                lab_dim, self.embed_dim // 2
            )
            lab_embed = lab_encoder(lab_input)
            # Project to embed_dim
            lab_embed = layers.Dense(self.embed_dim, name='lab_projection')(lab_embed)
            modality_inputs['lab'] = lab_input
            modality_embeddings.append(lab_embed)
            self.encoders['lab'] = lab_encoder
        
        # Genomic encoder
        if genomic_dim:
            genomic_input = layers.Input(shape=(genomic_dim,), name='genomic_input')
            genomic_encoder = ModalitySpecificEncoder.build_genomic_encoder(
                genomic_dim, self.embed_dim // 2
            )
            genomic_embed = genomic_encoder(genomic_input)
            # Project to embed_dim
            genomic_embed = layers.Dense(self.embed_dim, name='genomic_projection')(genomic_embed)
            modality_inputs['genomic'] = genomic_input
            modality_embeddings.append(genomic_embed)
            self.encoders['genomic'] = genomic_encoder
        
        if not modality_embeddings:
            raise ValueError("At least one modality must be provided")
        
        # Stack embeddings
        # Shape: (batch_size, num_modalities, embed_dim)
        stacked_embeddings = layers.Lambda(
            lambda x: tf.stack(x, axis=1),
            name='stack_modalities'
        )(modality_embeddings)
        
        # Add positional encoding if requested
        if self.use_positional_encoding:
            stacked_embeddings = self._add_positional_encoding(stacked_embeddings)
        
        # Apply attention layers
        x = stacked_embeddings
        for i in range(self.num_attention_layers):
            attention_layer = CrossModalAttentionLayer(
                embed_dim=self.embed_dim,
                num_heads=self.num_attention_heads,
                dropout=self.dropout
            )
            attention_layer.build_tensorflow()
            x = attention_layer(x, training=True)
            self.attention_layers.append(attention_layer)
        
        # Global pooling across modalities
        # Weighted average based on attention
        attention_weights = layers.Lambda(
            lambda x: tf.nn.softmax(tf.reduce_mean(x, axis=-1), axis=1),
            name='modality_weights'
        )(x)
        
        # Weighted sum
        fused = layers.Lambda(
            lambda inputs: tf.reduce_sum(
                inputs[0] * tf.expand_dims(inputs[1], axis=-1),
                axis=1
            ),
            name='weighted_fusion'
        )([x, attention_weights])
        
        # Final prediction head
        x = layers.Dense(512, activation='relu')(fused)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        
        x = layers.Dense(256, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.2)(x)
        
        # Output layer
        if num_classes == 2:
            outputs = layers.Dense(1, activation='sigmoid', name='prediction')(x)
        else:
            outputs = layers.Dense(num_classes, activation='softmax', name='prediction')(x)
        
        # Create model
        self.model = Model(
            inputs=list(modality_inputs.values()),
            outputs=outputs,
            name='multi_modal_attention_fusion'
        )
        
        return self.model
    
    def _add_positional_encoding(self, embeddings: tf.Tensor) -> tf.Tensor:
        """افزودن positional encoding"""
        batch_size = tf.shape(embeddings)[0]
        num_modalities = embeddings.shape[1]
        embed_dim = embeddings.shape[2]
        
        # Create positional encoding
        position = tf.range(num_modalities, dtype=tf.float32)[:, None]
        div_term = tf.exp(tf.range(0, embed_dim, 2, dtype=tf.float32) * 
                         -(np.log(10000.0) / embed_dim))
        
        pos_encoding = tf.zeros((num_modalities, embed_dim))
        pos_encoding = tf.tensor_scatter_nd_update(
            pos_encoding,
            tf.stack([tf.range(num_modalities), tf.range(0, embed_dim, 2)], axis=1),
            tf.sin(position * div_term)
        )
        if embed_dim % 2 == 1:
            pos_encoding = pos_encoding[:, :-1]
        
        pos_encoding = tf.expand_dims(pos_encoding, 0)
        pos_encoding = tf.tile(pos_encoding, [batch_size, 1, 1])
        
        return embeddings + pos_encoding
    
    def compile_model(
        self,
        optimizer: str = 'adam',
        learning_rate: float = 0.001,
        loss: Optional[str] = None,
        metrics: Optional[List[str]] = None
    ):
        """Compile مدل"""
        if self.model is None:
            raise ValueError("Model must be built before compilation")
        
        if loss is None:
            if self.model.output_shape[-1] == 1:
                loss = 'binary_crossentropy'
            else:
                loss = 'sparse_categorical_crossentropy'
        
        if metrics is None:
            metrics = ['accuracy']
        
        opt = keras.optimizers.Adam(learning_rate=learning_rate) if optimizer == 'adam' else optimizer
        
        self.model.compile(
            optimizer=opt,
            loss=loss,
            metrics=metrics
        )
        
        return self.model
    
    def get_attention_weights(self, inputs: Dict[str, np.ndarray]) -> np.ndarray:
        """
        دریافت وزن‌های attention برای تفسیر
        
        این می‌تواند برای explainability استفاده شود
        """
        if self.model is None:
            raise ValueError("Model must be built first")
        
        # Create intermediate model to extract attention weights
        # This is a simplified version - in production, use proper extraction
        modality_names = list(inputs.keys())
        num_modalities = len(modality_names)
        
        # Get attention weights from the last attention layer
        # This would need to be implemented based on the actual model structure
        # For now, return uniform weights as placeholder
        return np.ones((num_modalities,)) / num_modalities

