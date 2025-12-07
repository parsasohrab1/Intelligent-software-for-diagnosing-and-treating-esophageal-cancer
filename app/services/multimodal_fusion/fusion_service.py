"""
Multi-Modal Fusion Service
سرویس ادغام چندوجهی برای استفاده در production
"""
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from app.services.multimodal_fusion.attention_fusion import (
    MultiModalAttentionFusion,
    MultiModalInput
)
from app.services.radiomics.radiomics_extractor import RadiomicsExtractor

logger = logging.getLogger(__name__)


class MultiModalFusionService:
    """سرویس ادغام چندوجهی"""
    
    def __init__(self):
        self.fusion_model = None
        self.radiomics_extractor = RadiomicsExtractor()
        self.is_loaded = False
    
    def load_model(self, model_path: str):
        """بارگذاری مدل از فایل"""
        try:
            import tensorflow as tf
            self.fusion_model = tf.keras.models.load_model(model_path)
            self.is_loaded = True
            logger.info(f"Model loaded from {model_path}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def build_and_compile_model(
        self,
        endoscopy_shape: Optional[Tuple[int, int, int]] = None,
        radiomics_dim: Optional[int] = None,
        lab_dim: Optional[int] = None,
        genomic_dim: Optional[int] = None,
        num_classes: int = 2,
        embed_dim: int = 256,
        num_attention_heads: int = 8,
        num_attention_layers: int = 2
    ):
        """ساخت و compile مدل"""
        try:
            fusion = MultiModalAttentionFusion(
                embed_dim=embed_dim,
                num_attention_heads=num_attention_heads,
                num_attention_layers=num_attention_layers
            )
            
            model = fusion.build_model(
                endoscopy_shape=endoscopy_shape,
                radiomics_dim=radiomics_dim,
                lab_dim=lab_dim,
                genomic_dim=genomic_dim,
                num_classes=num_classes
            )
            
            fusion.compile_model()
            self.fusion_model = fusion.model
            self.fusion_architecture = fusion
            self.is_loaded = True
            
            logger.info("Multi-modal fusion model built and compiled")
            return model
            
        except Exception as e:
            logger.error(f"Error building model: {str(e)}")
            raise
    
    def prepare_inputs(
        self,
        endoscopy_image: Optional[np.ndarray] = None,
        radiomics_features: Optional[np.ndarray] = None,
        radiomics_dict: Optional[Dict] = None,
        lab_features: Optional[np.ndarray] = None,
        genomic_features: Optional[np.ndarray] = None
    ) -> Dict[str, np.ndarray]:
        """
        آماده‌سازی ورودی‌ها برای مدل
        
        Args:
            endoscopy_image: تصویر آندوسکوپی
            radiomics_features: ویژگی‌های رادیومیکس (array)
            radiomics_dict: ویژگی‌های رادیومیکس (dict) - تبدیل به array می‌شود
            lab_features: ویژگی‌های آزمایشگاهی
            genomic_features: ویژگی‌های ژنتیکی
            
        Returns:
            Dictionary of prepared inputs
        """
        inputs = {}
        
        # Prepare endoscopy image
        if endoscopy_image is not None:
            # Resize and normalize
            if len(endoscopy_image.shape) == 2:
                endoscopy_image = np.expand_dims(endoscopy_image, axis=-1)
            if endoscopy_image.max() > 1.0:
                endoscopy_image = endoscopy_image.astype(np.float32) / 255.0
            # Resize to standard size if needed
            if endoscopy_image.shape[:2] != (224, 224):
                import cv2
                endoscopy_image = cv2.resize(
                    endoscopy_image,
                    (224, 224),
                    interpolation=cv2.INTER_LINEAR
                )
            inputs['endoscopy'] = np.expand_dims(endoscopy_image, axis=0)
        
        # Prepare radiomics features
        if radiomics_dict is not None:
            radiomics_features = self._dict_to_radiomics_array(radiomics_dict)
        
        if radiomics_features is not None:
            if len(radiomics_features.shape) == 1:
                radiomics_features = np.expand_dims(radiomics_features, axis=0)
            inputs['radiomics'] = radiomics_features.astype(np.float32)
        
        # Prepare lab features
        if lab_features is not None:
            if len(lab_features.shape) == 1:
                lab_features = np.expand_dims(lab_features, axis=0)
            inputs['lab'] = lab_features.astype(np.float32)
        
        # Prepare genomic features
        if genomic_features is not None:
            if len(genomic_features.shape) == 1:
                genomic_features = np.expand_dims(genomic_features, axis=0)
            inputs['genomic'] = genomic_features.astype(np.float32)
        
        return inputs
    
    def _dict_to_radiomics_array(self, radiomics_dict: Dict) -> np.ndarray:
        """تبدیل dict رادیومیکس به array"""
        features = []
        
        # First-order features
        first_order = radiomics_dict.get('first_order', {})
        features.extend([
            first_order.get('mean', 0.0),
            first_order.get('std', 0.0),
            first_order.get('variance', 0.0),
            first_order.get('skewness', 0.0),
            first_order.get('kurtosis', 0.0),
            first_order.get('entropy', 0.0)
        ])
        
        # Texture features
        texture = radiomics_dict.get('texture', {})
        features.extend([
            texture.get('contrast', 0.0),
            texture.get('homogeneity', 0.0),
            texture.get('energy', 0.0),
            texture.get('correlation', 0.0)
        ])
        
        # Shape features
        shape = radiomics_dict.get('shape', {})
        features.extend([
            shape.get('area', 0.0),
            shape.get('compactness', 0.0),
            shape.get('sphericity', 0.0)
        ])
        
        return np.array(features, dtype=np.float32)
    
    def predict(
        self,
        inputs: Dict[str, np.ndarray],
        return_attention_weights: bool = False
    ) -> Dict[str, Any]:
        """
        پیش‌بینی با مدل ادغام چندوجهی
        
        Args:
            inputs: ورودی‌های آماده شده
            return_attention_weights: برگرداندن وزن‌های attention
            
        Returns:
            نتایج پیش‌بینی
        """
        if not self.is_loaded or self.fusion_model is None:
            raise ValueError("Model must be loaded or built before prediction")
        
        try:
            # Prepare input list in correct order
            input_list = []
            if 'endoscopy' in inputs:
                input_list.append(inputs['endoscopy'])
            if 'radiomics' in inputs:
                input_list.append(inputs['radiomics'])
            if 'lab' in inputs:
                input_list.append(inputs['lab'])
            if 'genomic' in inputs:
                input_list.append(inputs['genomic'])
            
            # Predict
            prediction = self.fusion_model.predict(input_list, verbose=0)
            
            result = {
                'prediction': float(prediction[0][0]) if len(prediction[0]) == 1 else float(prediction[0]),
                'confidence': float(np.max(prediction)),
                'probabilities': prediction[0].tolist() if len(prediction[0]) > 1 else [1 - prediction[0][0], prediction[0][0]],
                'timestamp': datetime.now().isoformat()
            }
            
            # Get attention weights if requested
            if return_attention_weights and hasattr(self, 'fusion_architecture'):
                try:
                    attention_weights = self.fusion_architecture.get_attention_weights(inputs)
                    result['attention_weights'] = attention_weights.tolist()
                    result['modality_contributions'] = self._interpret_attention_weights(
                        attention_weights,
                        list(inputs.keys())
                    )
                except Exception as e:
                    logger.warning(f"Could not extract attention weights: {str(e)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in prediction: {str(e)}")
            raise
    
    def _interpret_attention_weights(
        self,
        weights: np.ndarray,
        modality_names: List[str]
    ) -> Dict[str, float]:
        """تفسیر وزن‌های attention"""
        contributions = {}
        total = np.sum(weights)
        
        for i, name in enumerate(modality_names):
            if i < len(weights):
                contributions[name] = float(weights[i] / total) if total > 0 else 0.0
        
        return contributions
    
    def extract_features_from_patient_data(
        self,
        endoscopy_image: Optional[np.ndarray] = None,
        ct_image: Optional[np.ndarray] = None,
        pet_image: Optional[np.ndarray] = None,
        lab_results: Optional[Dict] = None,
        genomic_data: Optional[Dict] = None
    ) -> Dict[str, np.ndarray]:
        """
        استخراج ویژگی‌ها از داده‌های بیمار
        
        این متد داده‌های خام را به ویژگی‌های آماده برای مدل تبدیل می‌کند
        """
        features = {}
        
        # Endoscopy image (already in correct format)
        if endoscopy_image is not None:
            features['endoscopy'] = endoscopy_image
        
        # Extract radiomics from CT/PET
        radiomics_list = []
        if ct_image is not None:
            ct_radiomics = self.radiomics_extractor.extract_features(
                image=ct_image,
                modality='CT'
            )
            radiomics_list.append(self._dict_to_radiomics_array(ct_radiomics))
        
        if pet_image is not None:
            pet_radiomics = self.radiomics_extractor.extract_features(
                image=pet_image,
                modality='PET'
            )
            radiomics_list.append(self._dict_to_radiomics_array(pet_radiomics))
        
        if radiomics_list:
            # Average radiomics from multiple sources
            features['radiomics'] = np.mean(radiomics_list, axis=0)
        
        # Extract lab features
        if lab_results:
            lab_features = self._extract_lab_features(lab_results)
            features['lab'] = lab_features
        
        # Extract genomic features
        if genomic_data:
            genomic_features = self._extract_genomic_features(genomic_data)
            features['genomic'] = genomic_features
        
        return features
    
    def _extract_lab_features(self, lab_results: Dict) -> np.ndarray:
        """استخراج ویژگی‌های آزمایشگاهی"""
        features = []
        
        # Common lab values
        features.extend([
            lab_results.get('hemoglobin', 0.0),
            lab_results.get('wbc_count', 0.0),
            lab_results.get('platelet_count', 0.0),
            lab_results.get('creatinine', 0.0),
            lab_results.get('cea', 0.0),
            lab_results.get('ca19_9', 0.0),
            lab_results.get('crp', 0.0),
            lab_results.get('albumin', 0.0)
        ])
        
        return np.array(features, dtype=np.float32)
    
    def _extract_genomic_features(self, genomic_data: Dict) -> np.ndarray:
        """استخراج ویژگی‌های ژنتیکی"""
        features = []
        
        # PD-L1
        features.append(1.0 if genomic_data.get('pdl1_status') == 'positive' else 0.0)
        features.append(genomic_data.get('pdl1_percentage', 0.0) or 0.0)
        
        # MSI
        features.append(1.0 if genomic_data.get('msi_status') == 'MSI-H' else 0.0)
        
        # Mutations
        mutations = genomic_data.get('mutations', {})
        if isinstance(mutations, dict):
            features.append(1.0 if mutations.get('TP53') else 0.0)
            features.append(1.0 if mutations.get('PIK3CA') else 0.0)
            features.append(1.0 if mutations.get('KRAS') else 0.0)
            features.append(float(len([m for m in mutations.values() if m])))
        else:
            features.extend([0.0, 0.0, 0.0, 0.0])
        
        # CNV
        cnv = genomic_data.get('copy_number_variations', {})
        if isinstance(cnv, dict):
            features.append(float(len([c for c in cnv.values() if c > 1.5])))
            features.append(float(len([c for c in cnv.values() if c < 0.5])))
        else:
            features.extend([0.0, 0.0])
        
        return np.array(features, dtype=np.float32)

