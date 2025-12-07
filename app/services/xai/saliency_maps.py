"""
Saliency Maps and Heatmaps for Explainable AI
نقشه‌های برجستگی برای توضیح تصمیم‌گیری مدل
"""
import logging
import numpy as np
from typing import Dict, Optional, List, Tuple, Any, Union
from enum import Enum
import cv2
from datetime import datetime

logger = logging.getLogger(__name__)


class SaliencyMethod(str, Enum):
    """روش‌های تولید Saliency Map"""
    GRAD_CAM = "grad_cam"  # Gradient-weighted Class Activation Mapping
    GRAD_CAM_PLUS_PLUS = "grad_cam_plus_plus"
    LIME = "lime"  # Local Interpretable Model-agnostic Explanations
    SHAP = "shap"  # SHapley Additive exPlanations
    INTEGRATED_GRADIENTS = "integrated_gradients"
    OCCLUSION = "occlusion"
    GUIDED_BACKPROP = "guided_backprop"


class SaliencyMapGenerator:
    """تولید نقشه‌های برجستگی برای تصاویر"""

    def __init__(self, method: SaliencyMethod = SaliencyMethod.GRAD_CAM):
        self.method = method

    def generate_saliency_map(
        self,
        model: Any,
        image: np.ndarray,
        target_class: Optional[int] = None,
        layer_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        تولید نقشه برجستگی
        
        Args:
            model: مدل ML (TensorFlow/Keras یا PyTorch)
            image: تصویر ورودی
            target_class: کلاس هدف (اگر None، از کلاس پیش‌بینی شده استفاده می‌شود)
            layer_name: نام لایه برای Grad-CAM (اگر None، آخرین لایه convolutional استفاده می‌شود)
            
        Returns:
            نقشه برجستگی و اطلاعات مرتبط
        """
        try:
            if self.method == SaliencyMethod.GRAD_CAM:
                return self._generate_grad_cam(model, image, target_class, layer_name)
            elif self.method == SaliencyMethod.GRAD_CAM_PLUS_PLUS:
                return self._generate_grad_cam_plus_plus(model, image, target_class, layer_name)
            elif self.method == SaliencyMethod.LIME:
                return self._generate_lime(model, image, target_class)
            elif self.method == SaliencyMethod.SHAP:
                return self._generate_shap(model, image, target_class)
            elif self.method == SaliencyMethod.INTEGRATED_GRADIENTS:
                return self._generate_integrated_gradients(model, image, target_class)
            elif self.method == SaliencyMethod.OCCLUSION:
                return self._generate_occlusion(model, image, target_class)
            else:
                raise ValueError(f"Unknown saliency method: {self.method}")
        except Exception as e:
            logger.error(f"Error generating saliency map: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "saliency_map": None
            }

    def _generate_grad_cam(
        self,
        model: Any,
        image: np.ndarray,
        target_class: Optional[int] = None,
        layer_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """تولید Grad-CAM"""
        try:
            # Detect framework
            is_tensorflow = self._is_tensorflow_model(model)
            is_pytorch = self._is_pytorch_model(model)
            
            if is_tensorflow:
                return self._grad_cam_tensorflow(model, image, target_class, layer_name)
            elif is_pytorch:
                return self._grad_cam_pytorch(model, image, target_class, layer_name)
            else:
                raise ValueError("Unsupported model framework")
        except Exception as e:
            logger.error(f"Error in Grad-CAM: {str(e)}")
            raise

    def _grad_cam_tensorflow(
        self,
        model: Any,
        image: np.ndarray,
        target_class: Optional[int],
        layer_name: Optional[str]
    ) -> Dict[str, Any]:
        """Grad-CAM برای TensorFlow/Keras"""
        try:
            import tensorflow as tf
            from tensorflow import keras
            
            # Preprocess image
            img_array = self._preprocess_image_tf(image)
            
            # Get prediction
            predictions = model.predict(img_array, verbose=0)
            predicted_class = int(np.argmax(predictions[0]))
            confidence = float(np.max(predictions[0]))
            
            if target_class is None:
                target_class = predicted_class
            
            # Find last convolutional layer
            if layer_name is None:
                for layer in reversed(model.layers):
                    if len(layer.output_shape) == 4:  # Convolutional layer
                        layer_name = layer.name
                        break
            
            if layer_name is None:
                raise ValueError("No convolutional layer found")
            
            # Create Grad-CAM model
            grad_model = tf.keras.models.Model(
                [model.inputs],
                [model.get_layer(layer_name).output, model.output]
            )
            
            # Compute gradients
            with tf.GradientTape() as tape:
                conv_outputs, predictions = grad_model(img_array)
                loss = predictions[:, target_class]
            
            grads = tape.gradient(loss, conv_outputs)
            
            # Global average pooling of gradients
            pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
            
            # Weight feature maps
            conv_outputs = conv_outputs[0]
            heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
            heatmap = tf.squeeze(heatmap)
            
            # Normalize heatmap
            heatmap = tf.maximum(heatmap, 0) / tf.math.reduce_max(heatmap)
            heatmap = heatmap.numpy()
            
            # Resize to original image size
            heatmap = cv2.resize(heatmap, (image.shape[1], image.shape[0]))
            heatmap = np.uint8(255 * heatmap)
            
            # Apply colormap
            heatmap_colored = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
            
            # Overlay on original image
            overlay = cv2.addWeighted(image, 0.6, heatmap_colored, 0.4, 0)
            
            return {
                "success": True,
                "method": "grad_cam",
                "saliency_map": heatmap.tolist(),
                "heatmap_colored": heatmap_colored.tolist(),
                "overlay": overlay.tolist(),
                "predicted_class": predicted_class,
                "target_class": target_class,
                "confidence": confidence,
                "layer_name": layer_name,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in TensorFlow Grad-CAM: {str(e)}")
            raise

    def _grad_cam_pytorch(
        self,
        model: Any,
        image: np.ndarray,
        target_class: Optional[int],
        layer_name: Optional[str]
    ) -> Dict[str, Any]:
        """Grad-CAM برای PyTorch"""
        try:
            import torch
            import torch.nn.functional as F
            
            # Preprocess image
            img_tensor = self._preprocess_image_torch(image)
            
            # Set model to eval mode
            model.eval()
            
            # Get prediction
            with torch.no_grad():
                output = model(img_tensor)
                predictions = F.softmax(output, dim=1)
                predicted_class = int(torch.argmax(predictions[0]))
                confidence = float(predictions[0][predicted_class])
            
            if target_class is None:
                target_class = predicted_class
            
            # Find target layer
            target_layer = None
            if layer_name:
                for name, module in model.named_modules():
                    if name == layer_name:
                        target_layer = module
                        break
            else:
                # Find last convolutional layer
                for module in reversed(list(model.modules())):
                    if isinstance(module, torch.nn.Conv2d):
                        target_layer = module
                        break
            
            if target_layer is None:
                raise ValueError("No convolutional layer found")
            
            # Register hook for gradients
            gradients = []
            activations = []
            
            def backward_hook(module, grad_input, grad_output):
                gradients.append(grad_output[0])
            
            def forward_hook(module, input, output):
                activations.append(output)
            
            handle_backward = target_layer.register_full_backward_hook(backward_hook)
            handle_forward = target_layer.register_forward_hook(forward_hook)
            
            # Forward pass
            output = model(img_tensor)
            
            # Backward pass
            model.zero_grad()
            loss = output[0, target_class]
            loss.backward()
            
            # Get gradients and activations
            grads = gradients[0]
            acts = activations[0]
            
            # Global average pooling of gradients
            pooled_grads = torch.mean(grads, dim=[2, 3], keepdim=True)
            
            # Weight feature maps
            heatmap = torch.sum(acts * pooled_grads, dim=1, keepdim=True)
            heatmap = F.relu(heatmap)
            heatmap = heatmap.squeeze().cpu().numpy()
            
            # Normalize
            heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min() + 1e-8)
            
            # Resize to original image size
            heatmap = cv2.resize(heatmap, (image.shape[1], image.shape[0]))
            heatmap = np.uint8(255 * heatmap)
            
            # Apply colormap
            heatmap_colored = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
            
            # Overlay on original image
            overlay = cv2.addWeighted(image, 0.6, heatmap_colored, 0.4, 0)
            
            # Remove hooks
            handle_backward.remove()
            handle_forward.remove()
            
            return {
                "success": True,
                "method": "grad_cam",
                "saliency_map": heatmap.tolist(),
                "heatmap_colored": heatmap_colored.tolist(),
                "overlay": overlay.tolist(),
                "predicted_class": predicted_class,
                "target_class": target_class,
                "confidence": confidence,
                "layer_name": layer_name or "last_conv",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in PyTorch Grad-CAM: {str(e)}")
            raise

    def _generate_lime(
        self,
        model: Any,
        image: np.ndarray,
        target_class: Optional[int]
    ) -> Dict[str, Any]:
        """تولید LIME explanation"""
        try:
            from lime import lime_image
            from skimage.segmentation import mark_boundaries
            
            # Create LIME explainer
            explainer = lime_image.LimeImageExplainer()
            
            # Get prediction
            def predict_fn(images):
                preprocessed = np.array([self._preprocess_image_for_model(img, model) for img in images])
                predictions = model.predict(preprocessed, verbose=0)
                return predictions
            
            # Explain
            explanation = explainer.explain_instance(
                image.astype('double'),
                predict_fn,
                top_labels=1,
                hide_color=0,
                num_samples=1000
            )
            
            # Get explanation for target class
            if target_class is None:
                temp, mask = explanation.get_image_and_mask(
                    explanation.top_labels[0],
                    positive_only=True,
                    num_features=10,
                    hide_rest=False
                )
            else:
                temp, mask = explanation.get_image_and_mask(
                    target_class,
                    positive_only=True,
                    num_features=10,
                    hide_rest=False
                )
            
            # Create overlay
            overlay = mark_boundaries(temp, mask)
            
            return {
                "success": True,
                "method": "lime",
                "saliency_map": mask.tolist(),
                "overlay": overlay.tolist(),
                "target_class": target_class or explanation.top_labels[0],
                "timestamp": datetime.now().isoformat()
            }
        except ImportError:
            logger.warning("LIME not installed. Install with: pip install lime")
            return {
                "success": False,
                "error": "LIME not installed",
                "method": "lime"
            }
        except Exception as e:
            logger.error(f"Error in LIME: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "method": "lime"
            }

    def _generate_shap(
        self,
        model: Any,
        image: np.ndarray,
        target_class: Optional[int]
    ) -> Dict[str, Any]:
        """تولید SHAP explanation"""
        try:
            import shap
            
            # Preprocess image
            img_array = self._preprocess_image_for_model(image, model)
            
            # Create SHAP explainer
            explainer = shap.Explainer(model, img_array[np.newaxis, ...])
            
            # Explain
            shap_values = explainer(img_array[np.newaxis, ...])
            
            # Get saliency map
            if target_class is None:
                saliency_map = np.abs(shap_values.values[0, :, :, :]).sum(axis=2)
            else:
                saliency_map = np.abs(shap_values.values[0, :, :, target_class])
            
            # Normalize
            saliency_map = (saliency_map - saliency_map.min()) / (saliency_map.max() - saliency_map.min() + 1e-8)
            saliency_map = np.uint8(255 * saliency_map)
            
            # Apply colormap
            heatmap_colored = cv2.applyColorMap(saliency_map, cv2.COLORMAP_JET)
            
            # Overlay
            overlay = cv2.addWeighted(image, 0.6, heatmap_colored, 0.4, 0)
            
            return {
                "success": True,
                "method": "shap",
                "saliency_map": saliency_map.tolist(),
                "heatmap_colored": heatmap_colored.tolist(),
                "overlay": overlay.tolist(),
                "target_class": target_class,
                "timestamp": datetime.now().isoformat()
            }
        except ImportError:
            logger.warning("SHAP not installed. Install with: pip install shap")
            return {
                "success": False,
                "error": "SHAP not installed",
                "method": "shap"
            }
        except Exception as e:
            logger.error(f"Error in SHAP: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "method": "shap"
            }

    def _generate_grad_cam_plus_plus(
        self,
        model: Any,
        image: np.ndarray,
        target_class: Optional[int],
        layer_name: Optional[str]
    ) -> Dict[str, Any]:
        """تولید Grad-CAM++"""
        # Similar to Grad-CAM but with improved weighting
        # Implementation would be similar to Grad-CAM with modified gradient computation
        return self._generate_grad_cam(model, image, target_class, layer_name)

    def _generate_integrated_gradients(
        self,
        model: Any,
        image: np.ndarray,
        target_class: Optional[int]
    ) -> Dict[str, Any]:
        """تولید Integrated Gradients"""
        # Implementation for integrated gradients
        # This would compute gradients along a path from baseline to input
        return {
            "success": False,
            "error": "Not yet implemented",
            "method": "integrated_gradients"
        }

    def _generate_occlusion(
        self,
        model: Any,
        image: np.ndarray,
        target_class: Optional[int]
    ) -> Dict[str, Any]:
        """تولید Occlusion-based saliency"""
        # Implementation for occlusion sensitivity
        return {
            "success": False,
            "error": "Not yet implemented",
            "method": "occlusion"
        }

    def _is_tensorflow_model(self, model: Any) -> bool:
        """بررسی اینکه آیا مدل TensorFlow/Keras است"""
        try:
            import tensorflow as tf
            from tensorflow import keras
            return isinstance(model, (tf.keras.Model, keras.Model))
        except:
            return False

    def _is_pytorch_model(self, model: Any) -> bool:
        """بررسی اینکه آیا مدل PyTorch است"""
        try:
            import torch
            return isinstance(model, torch.nn.Module)
        except:
            return False

    def _preprocess_image_tf(self, image: np.ndarray) -> np.ndarray:
        """پیش‌پردازش تصویر برای TensorFlow"""
        # Resize if needed
        if image.shape[:2] != (224, 224):
            image = cv2.resize(image, (224, 224))
        
        # Normalize
        image = image.astype(np.float32) / 255.0
        
        # Expand dimensions
        return np.expand_dims(image, axis=0)

    def _preprocess_image_torch(self, image: np.ndarray) -> np.ndarray:
        """پیش‌پردازش تصویر برای PyTorch"""
        import torch
        
        # Resize if needed
        if image.shape[:2] != (224, 224):
            image = cv2.resize(image, (224, 224))
        
        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Normalize
        image = image.astype(np.float32) / 255.0
        
        # Convert to tensor and normalize (ImageNet normalization)
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        image = (image - mean) / std
        
        # Convert to tensor
        image = torch.from_numpy(image).permute(2, 0, 1).unsqueeze(0)
        
        return image

    def _preprocess_image_for_model(self, image: np.ndarray, model: Any) -> np.ndarray:
        """پیش‌پردازش تصویر بر اساس نوع مدل"""
        if self._is_tensorflow_model(model):
            return self._preprocess_image_tf(image)
        elif self._is_pytorch_model(model):
            img_tensor = self._preprocess_image_torch(image)
            return img_tensor.numpy()
        else:
            # Default preprocessing
            if image.shape[:2] != (224, 224):
                image = cv2.resize(image, (224, 224))
            return image.astype(np.float32) / 255.0

