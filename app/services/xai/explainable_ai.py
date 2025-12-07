"""
Explainable AI Service
سرویس توضیح‌پذیری برای مدل‌های ML
"""
import logging
from typing import Dict, Optional, List, Any, Union
import numpy as np
from datetime import datetime

from app.services.xai.saliency_maps import SaliencyMapGenerator, SaliencyMethod
from app.services.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


class ExplainableAIService:
    """سرویس Explainable AI برای توضیح تصمیم‌گیری مدل"""

    def __init__(self):
        self.registry = ModelRegistry()

    def explain_image_prediction(
        self,
        model_id: str,
        image: np.ndarray,
        method: SaliencyMethod = SaliencyMethod.GRAD_CAM,
        target_class: Optional[int] = None,
        layer_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        توضیح پیش‌بینی برای تصویر
        
        Args:
            model_id: شناسه مدل
            image: تصویر ورودی
            method: روش توضیح‌پذیری
            target_class: کلاس هدف (اگر None، از کلاس پیش‌بینی شده استفاده می‌شود)
            layer_name: نام لایه برای Grad-CAM
            
        Returns:
            توضیحات شامل saliency map و اطلاعات مرتبط
        """
        try:
            # Load model
            model_info = self.registry.get_model(model_id)
            if not model_info:
                return {
                    "success": False,
                    "error": f"Model {model_id} not found"
                }
            
            # Load model
            model = self._load_model(model_info)
            if model is None:
                return {
                    "success": False,
                    "error": "Failed to load model"
                }
            
            # Generate saliency map
            generator = SaliencyMapGenerator(method=method)
            saliency_result = generator.generate_saliency_map(
                model=model,
                image=image,
                target_class=target_class,
                layer_name=layer_name
            )
            
            if not saliency_result.get("success", False):
                return saliency_result
            
            # Get prediction
            prediction_info = self._get_prediction_info(model, image)
            
            # Combine results
            return {
                "success": True,
                "model_id": model_id,
                "prediction": prediction_info,
                "saliency_map": {
                    "method": method.value,
                    "map": saliency_result.get("saliency_map"),
                    "heatmap_colored": saliency_result.get("heatmap_colored"),
                    "overlay": saliency_result.get("overlay"),
                    "target_class": saliency_result.get("target_class"),
                    "layer_name": saliency_result.get("layer_name")
                },
                "explanation": {
                    "regions_of_interest": self._extract_regions_of_interest(
                        saliency_result.get("saliency_map")
                    ),
                    "confidence_regions": self._identify_confidence_regions(
                        saliency_result.get("saliency_map"),
                        threshold=0.5
                    )
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error explaining prediction: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def explain_batch_predictions(
        self,
        model_id: str,
        images: List[np.ndarray],
        method: SaliencyMethod = SaliencyMethod.GRAD_CAM
    ) -> List[Dict[str, Any]]:
        """
        توضیح پیش‌بینی‌ها برای چند تصویر
        
        Args:
            model_id: شناسه مدل
            images: لیست تصاویر
            method: روش توضیح‌پذیری
            
        Returns:
            لیست توضیحات
        """
        results = []
        for i, image in enumerate(images):
            result = self.explain_image_prediction(
                model_id=model_id,
                image=image,
                method=method
            )
            result["image_index"] = i
            results.append(result)
        
        return results

    def compare_explanations(
        self,
        model_id: str,
        image: np.ndarray,
        methods: List[SaliencyMethod]
    ) -> Dict[str, Any]:
        """
        مقایسه توضیحات با روش‌های مختلف
        
        Args:
            model_id: شناسه مدل
            image: تصویر ورودی
            methods: لیست روش‌های توضیح‌پذیری
            
        Returns:
            مقایسه توضیحات
        """
        explanations = {}
        
        for method in methods:
            result = self.explain_image_prediction(
                model_id=model_id,
                image=image,
                method=method
            )
            explanations[method.value] = result
        
        return {
            "model_id": model_id,
            "explanations": explanations,
            "comparison": self._compare_saliency_maps(explanations),
            "timestamp": datetime.now().isoformat()
        }

    def _load_model(self, model_info: Dict) -> Optional[Any]:
        """بارگذاری مدل"""
        try:
            model_path = model_info.get("model_path")
            model_type = model_info.get("model_type")
            
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
            
            # Try pickle (for scikit-learn models)
            try:
                import pickle
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                return model
            except:
                pass
            
            logger.warning(f"Could not load model from {model_path}")
            return None
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return None

    def _get_prediction_info(self, model: Any, image: np.ndarray) -> Dict:
        """دریافت اطلاعات پیش‌بینی"""
        try:
            # Preprocess image
            if hasattr(model, 'predict'):
                # TensorFlow/Keras
                preprocessed = self._preprocess_for_model(model, image)
                predictions = model.predict(preprocessed, verbose=0)
                
                predicted_class = int(np.argmax(predictions[0]))
                confidence = float(np.max(predictions[0]))
                probabilities = predictions[0].tolist()
                
                return {
                    "predicted_class": predicted_class,
                    "confidence": confidence,
                    "probabilities": probabilities
                }
            else:
                return {
                    "predicted_class": None,
                    "confidence": None,
                    "probabilities": []
                }
        except Exception as e:
            logger.error(f"Error getting prediction info: {str(e)}")
            return {
                "predicted_class": None,
                "confidence": None,
                "probabilities": []
            }

    def _preprocess_for_model(self, model: Any, image: np.ndarray) -> np.ndarray:
        """پیش‌پردازش تصویر برای مدل"""
        import cv2
        
        # Resize if needed
        if image.shape[:2] != (224, 224):
            image = cv2.resize(image, (224, 224))
        
        # Normalize
        image = image.astype(np.float32) / 255.0
        
        # Expand dimensions
        return np.expand_dims(image, axis=0)

    def _extract_regions_of_interest(self, saliency_map: Optional[List]) -> List[Dict]:
        """استخراج مناطق مورد علاقه از saliency map"""
        if saliency_map is None:
            return []
        
        try:
            import cv2
            
            # Convert to numpy array
            if isinstance(saliency_map, list):
                saliency_map = np.array(saliency_map)
            
            # Threshold
            _, binary = cv2.threshold(saliency_map, 127, 255, cv2.THRESH_BINARY)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            regions = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 100:  # Minimum area threshold
                    x, y, w, h = cv2.boundingRect(contour)
                    regions.append({
                        "bbox": [int(x), int(y), int(w), int(h)],
                        "area": float(area),
                        "center": [int(x + w/2), int(y + h/2)]
                    })
            
            return regions
        except Exception as e:
            logger.error(f"Error extracting regions: {str(e)}")
            return []

    def _identify_confidence_regions(
        self,
        saliency_map: Optional[List],
        threshold: float = 0.5
    ) -> List[Dict]:
        """شناسایی مناطق با اطمینان بالا"""
        if saliency_map is None:
            return []
        
        try:
            # Convert to numpy array
            if isinstance(saliency_map, list):
                saliency_map = np.array(saliency_map)
            
            # Normalize to 0-1
            saliency_map = saliency_map.astype(np.float32) / 255.0
            
            # Find high-confidence regions
            high_confidence = saliency_map > threshold
            
            # Get coordinates
            coords = np.where(high_confidence)
            
            regions = []
            if len(coords[0]) > 0:
                regions.append({
                    "threshold": threshold,
                    "pixel_count": int(len(coords[0])),
                    "percentage": float(len(coords[0]) / saliency_map.size * 100),
                    "coordinates": list(zip(coords[0].tolist(), coords[1].tolist()))[:100]  # Limit to 100
                })
            
            return regions
        except Exception as e:
            logger.error(f"Error identifying confidence regions: {str(e)}")
            return []

    def _compare_saliency_maps(self, explanations: Dict[str, Dict]) -> Dict:
        """مقایسه saliency maps مختلف"""
        try:
            # Extract saliency maps
            maps = {}
            for method, explanation in explanations.items():
                if explanation.get("success") and "saliency_map" in explanation:
                    saliency_data = explanation.get("saliency_map", {})
                    if "map" in saliency_data:
                        maps[method] = np.array(saliency_data["map"])
            
            if len(maps) < 2:
                return {
                    "similarity": None,
                    "note": "Need at least 2 methods for comparison"
                }
            
            # Calculate similarity (correlation)
            similarities = {}
            methods = list(maps.keys())
            
            for i, method1 in enumerate(methods):
                for method2 in methods[i+1:]:
                    map1 = maps[method1].flatten()
                    map2 = maps[method2].flatten()
                    
                    # Normalize
                    map1 = (map1 - map1.min()) / (map1.max() - map1.min() + 1e-8)
                    map2 = (map2 - map2.min()) / (map2.max() - map2.min() + 1e-8)
                    
                    # Correlation
                    correlation = np.corrcoef(map1, map2)[0, 1]
                    similarities[f"{method1}_vs_{method2}"] = float(correlation)
            
            return {
                "similarity": similarities,
                "methods_compared": methods,
                "average_similarity": float(np.mean(list(similarities.values())))
            }
        except Exception as e:
            logger.error(f"Error comparing saliency maps: {str(e)}")
            return {
                "similarity": None,
                "error": str(e)
            }

