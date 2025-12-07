"""
Depth Estimation for Tumor Invasion
تخمین عمق نفوذ احتمالی تومور
"""
import logging
import numpy as np
import cv2
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class DepthEstimation:
    """تخمین عمق نفوذ"""
    mean_depth_mm: float  # عمق متوسط (میلی‌متر)
    max_depth_mm: float  # حداکثر عمق
    min_depth_mm: float  # حداقل عمق
    depth_map: np.ndarray  # نقشه عمق
    confidence: float  # اطمینان از تخمین
    invasion_level: str  # سطح نفوذ: "superficial", "moderate", "deep"


class DepthEstimator:
    """تخمین عمق نفوذ تومور"""

    def __init__(self):
        self.depth_model = None

    def estimate_invasion_depth(
        self,
        frame: np.ndarray,
        tumor_mask: np.ndarray,
        tumor_boundaries: List,
        model: Optional[Any] = None
    ) -> DepthEstimation:
        """
        تخمین عمق نفوذ احتمالی
        
        Args:
            frame: فریم آندوسکوپی
            tumor_mask: ماسک تومور
            tumor_boundaries: مرزهای تومور
            model: مدل تخمین عمق (اختیاری)
            
        Returns:
            تخمین عمق نفوذ
        """
        try:
            if model is not None:
                depth_map = self._estimate_with_model(frame, tumor_mask, model)
            else:
                depth_map = self._estimate_rule_based(frame, tumor_mask)
            
            # Calculate depth statistics
            roi_depths = depth_map[tumor_mask > 0]
            
            if len(roi_depths) == 0:
                return DepthEstimation(
                    mean_depth_mm=0.0,
                    max_depth_mm=0.0,
                    min_depth_mm=0.0,
                    depth_map=depth_map,
                    confidence=0.0,
                    invasion_level="unknown"
                )
            
            mean_depth = float(np.mean(roi_depths))
            max_depth = float(np.max(roi_depths))
            min_depth = float(np.min(roi_depths))
            
            # Determine invasion level
            invasion_level = self._classify_invasion_level(mean_depth, max_depth)
            
            # Calculate confidence
            confidence = self._calculate_depth_confidence(depth_map, tumor_mask)
            
            return DepthEstimation(
                mean_depth_mm=mean_depth,
                max_depth_mm=max_depth,
                min_depth_mm=min_depth,
                depth_map=depth_map,
                confidence=confidence,
                invasion_level=invasion_level
            )
            
        except Exception as e:
            logger.error(f"Error estimating depth: {str(e)}")
            return DepthEstimation(
                mean_depth_mm=0.0,
                max_depth_mm=0.0,
                min_depth_mm=0.0,
                depth_map=np.zeros_like(frame[:, :, 0] if len(frame.shape) == 3 else frame, dtype=np.float32),
                confidence=0.0,
                invasion_level="unknown"
            )

    def _estimate_with_model(
        self,
        frame: np.ndarray,
        tumor_mask: np.ndarray,
        model: Any
    ) -> np.ndarray:
        """تخمین عمق با مدل ML"""
        try:
            # Preprocess
            if len(frame.shape) == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                gray = frame
            
            # Resize for model
            input_shape = (224, 224)
            resized = cv2.resize(gray, input_shape)
            normalized = resized.astype(np.float32) / 255.0
            input_batch = np.expand_dims(normalized, axis=0)
            
            # Predict
            if hasattr(model, 'predict'):
                prediction = model.predict(input_batch, verbose=0)
                if len(prediction.shape) == 4:
                    depth = prediction[0, :, :, 0]
                else:
                    depth = prediction[0]
            else:
                import torch
                model.eval()
                with torch.no_grad():
                    input_tensor = torch.from_numpy(input_batch)
                    if torch.cuda.is_available():
                        input_tensor = input_tensor.cuda()
                        model = model.cuda()
                    output = model(input_tensor)
                    if isinstance(output, (list, tuple)):
                        output = output[0]
                    depth = output[0, 0].cpu().numpy()
            
            # Resize back
            original_shape = gray.shape
            depth = cv2.resize(depth, (original_shape[1], original_shape[0]))
            
            # Scale to millimeters (typical range: 0-10mm for esophageal wall)
            depth = depth * 10.0  # Scale to 0-10mm range
            
            return depth.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Error in model depth estimation: {str(e)}")
            return self._estimate_rule_based(frame, tumor_mask)

    def _estimate_rule_based(
        self,
        frame: np.ndarray,
        tumor_mask: np.ndarray
    ) -> np.ndarray:
        """تخمین عمق بر اساس قوانین (fallback)"""
        try:
            if len(frame.shape) == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                gray = frame
            
            # Estimate depth based on intensity and texture
            # Darker regions may indicate deeper invasion
            # More irregular texture may indicate deeper invasion
            
            # Normalize intensity
            normalized = gray.astype(np.float32) / 255.0
            
            # Calculate gradient magnitude (texture irregularity)
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)
            gradient_normalized = gradient_magnitude / (gradient_magnitude.max() + 1e-8)
            
            # Estimate depth: darker and more irregular = deeper
            # Invert intensity (darker = deeper)
            inverted_intensity = 1.0 - normalized
            
            # Combine intensity and gradient
            depth_estimate = (inverted_intensity * 0.6 + gradient_normalized * 0.4) * 8.0  # Scale to 0-8mm
            
            # Apply smoothing
            depth_estimate = cv2.GaussianBlur(depth_estimate, (5, 5), 0)
            
            # Mask to tumor region
            depth_map = np.zeros_like(depth_estimate, dtype=np.float32)
            depth_map[tumor_mask > 0] = depth_estimate[tumor_mask > 0]
            
            return depth_map
            
        except Exception as e:
            logger.error(f"Error in rule-based depth estimation: {str(e)}")
            return np.zeros_like(frame[:, :, 0] if len(frame.shape) == 3 else frame, dtype=np.float32)

    def _classify_invasion_level(self, mean_depth: float, max_depth: float) -> str:
        """دسته‌بندی سطح نفوذ"""
        # Esophageal wall thickness: ~3-5mm
        # Superficial: < 1mm (mucosa)
        # Moderate: 1-3mm (submucosa)
        # Deep: > 3mm (muscularis propria or beyond)
        
        if mean_depth < 1.0:
            return "superficial"
        elif mean_depth < 3.0:
            return "moderate"
        else:
            return "deep"

    def _calculate_depth_confidence(
        self,
        depth_map: np.ndarray,
        tumor_mask: np.ndarray
    ) -> float:
        """محاسبه اطمینان از تخمین عمق"""
        try:
            roi_depths = depth_map[tumor_mask > 0]
            
            if len(roi_depths) == 0:
                return 0.0
            
            # Confidence based on consistency
            std_depth = np.std(roi_depths)
            mean_depth = np.mean(roi_depths)
            
            # Lower std relative to mean = higher confidence
            if mean_depth > 0:
                cv_coefficient = std_depth / mean_depth
                confidence = max(0.0, 1.0 - cv_coefficient)
            else:
                confidence = 0.5
            
            return float(confidence)
            
        except:
            return 0.5

