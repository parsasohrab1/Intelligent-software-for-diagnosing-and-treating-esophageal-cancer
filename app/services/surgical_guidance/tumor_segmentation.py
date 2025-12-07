"""
Real-Time Tumor Segmentation for Endoscopy
تشخیص مرزهای تومور به صورت Real-Time در تصاویر آندوسکوپی
"""
import logging
import numpy as np
import cv2
from typing import Dict, Optional, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class EndoscopyMode(str, Enum):
    """حالت‌های آندوسکوپی"""
    NBI = "nbi"  # Narrow Band Imaging
    WLI = "wli"  # White Light Imaging
    AUTO = "auto"  # Auto-detect


@dataclass
class TumorBoundary:
    """مرزهای تومور"""
    contour: np.ndarray  # Contour points
    area: float  # مساحت تومور
    perimeter: float  # محیط تومور
    centroid: Tuple[float, float]  # مرکز جرم
    bbox: Tuple[int, int, int, int]  # Bounding box (x, y, w, h)
    confidence: float  # اطمینان از تشخیص


@dataclass
class SegmentationResult:
    """نتیجه segmentation"""
    frame_id: int
    timestamp: float
    processing_time_ms: float
    tumor_boundaries: List[TumorBoundary]
    segmentation_mask: np.ndarray
    overlay_image: np.ndarray
    confidence: float
    error: Optional[str] = None


class TumorSegmentation:
    """Segmentation مرزهای تومور در تصاویر آندوسکوپی"""

    def __init__(self, mode: EndoscopyMode = EndoscopyMode.AUTO):
        self.mode = mode
        self.segmentation_model = None

    def segment_tumor(
        self,
        frame: np.ndarray,
        mode: Optional[EndoscopyMode] = None,
        model: Optional[Any] = None
    ) -> SegmentationResult:
        """
        Segmentation مرزهای تومور
        
        Args:
            frame: فریم آندوسکوپی (NBI یا WLI)
            mode: حالت آندوسکوپی
            model: مدل segmentation (اختیاری)
            
        Returns:
            نتیجه segmentation
        """
        start_time = datetime.now().timestamp()
        frame_id = 0  # Will be set by caller
        
        try:
            # Detect mode if auto
            detected_mode = mode or self.mode
            if detected_mode == EndoscopyMode.AUTO:
                detected_mode = self._detect_endoscopy_mode(frame)
            
            # Preprocess for mode
            preprocessed = self._preprocess_for_mode(frame, detected_mode)
            
            # Segment using model or rule-based
            if model is not None:
                mask = self._segment_with_model(preprocessed, model)
            else:
                mask = self._segment_rule_based(preprocessed, detected_mode)
            
            # Extract tumor boundaries
            boundaries = self._extract_boundaries(mask)
            
            # Create overlay
            overlay = self._create_overlay(frame, mask, boundaries)
            
            # Calculate overall confidence
            confidence = self._calculate_confidence(mask, boundaries)
            
            processing_time = (datetime.now().timestamp() - start_time) * 1000
            
            return SegmentationResult(
                frame_id=frame_id,
                timestamp=start_time,
                processing_time_ms=processing_time,
                tumor_boundaries=boundaries,
                segmentation_mask=mask,
                overlay_image=overlay,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error segmenting tumor: {str(e)}")
            return SegmentationResult(
                frame_id=frame_id,
                timestamp=start_time,
                processing_time_ms=(datetime.now().timestamp() - start_time) * 1000,
                tumor_boundaries=[],
                segmentation_mask=np.zeros_like(frame[:, :, 0] if len(frame.shape) == 3 else frame),
                overlay_image=frame.copy(),
                confidence=0.0,
                error=str(e)
            )

    def _detect_endoscopy_mode(self, frame: np.ndarray) -> EndoscopyMode:
        """تشخیص خودکار حالت آندوسکوپی"""
        try:
            # NBI typically has more blue/green tones
            # WLI has more natural colors
            if len(frame.shape) == 3:
                # Check color distribution
                blue_channel = frame[:, :, 0] if frame.shape[2] == 3 else frame
                green_channel = frame[:, :, 1] if frame.shape[2] == 3 else frame
                
                blue_mean = np.mean(blue_channel)
                green_mean = np.mean(green_channel)
                
                # NBI tends to have higher blue/green ratio
                if blue_mean > green_mean * 1.2 or green_mean > np.mean(frame) * 1.1:
                    return EndoscopyMode.NBI
                else:
                    return EndoscopyMode.WLI
            else:
                return EndoscopyMode.WLI
        except:
            return EndoscopyMode.WLI

    def _preprocess_for_mode(self, frame: np.ndarray, mode: EndoscopyMode) -> np.ndarray:
        """پیش‌پردازش بر اساس حالت"""
        try:
            if mode == EndoscopyMode.NBI:
                # NBI preprocessing: enhance contrast
                if len(frame.shape) == 3:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                else:
                    gray = frame
                
                # Apply CLAHE for contrast enhancement
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(gray)
                return enhanced
            else:
                # WLI preprocessing: standard enhancement
                if len(frame.shape) == 3:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                else:
                    gray = frame
                
                # Enhance contrast
                clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
                enhanced = clahe.apply(gray)
                return enhanced
        except Exception as e:
            logger.error(f"Error preprocessing: {str(e)}")
            return frame

    def _segment_with_model(self, preprocessed: np.ndarray, model: Any) -> np.ndarray:
        """Segmentation با مدل ML"""
        try:
            # Prepare input
            input_shape = (224, 224)  # Standard input size
            resized = cv2.resize(preprocessed, input_shape)
            
            # Normalize
            normalized = resized.astype(np.float32) / 255.0
            input_batch = np.expand_dims(normalized, axis=0)
            
            # Predict
            if hasattr(model, 'predict'):
                # TensorFlow/Keras
                prediction = model.predict(input_batch, verbose=0)
                if len(prediction.shape) == 4:
                    mask = prediction[0, :, :, 0]  # Get first channel
                else:
                    mask = prediction[0]
            else:
                # PyTorch
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
                    mask = output[0, 0].cpu().numpy()
            
            # Resize back to original
            original_shape = preprocessed.shape[:2]
            mask = cv2.resize(mask, (original_shape[1], original_shape[0]))
            
            # Threshold
            mask = (mask > 0.5).astype(np.uint8) * 255
            
            return mask
            
        except Exception as e:
            logger.error(f"Error in model segmentation: {str(e)}")
            return self._segment_rule_based(preprocessed, EndoscopyMode.WLI)

    def _segment_rule_based(self, preprocessed: np.ndarray, mode: EndoscopyMode) -> np.ndarray:
        """Segmentation بر اساس قوانین (fallback)"""
        try:
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(preprocessed, (5, 5), 0)
            
            # Adaptive thresholding
            if mode == EndoscopyMode.NBI:
                # NBI: use adaptive threshold
                thresh = cv2.adaptiveThreshold(
                    blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY_INV, 11, 2
                )
            else:
                # WLI: use Otsu's method
                _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Morphological operations to clean up
            kernel = np.ones((5, 5), np.uint8)
            opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
            closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel, iterations=2)
            
            # Remove small noise
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(closing, connectivity=8)
            
            # Filter by area (keep only large regions)
            min_area = preprocessed.shape[0] * preprocessed.shape[1] * 0.01  # 1% of image
            mask = np.zeros_like(closing)
            
            for i in range(1, num_labels):  # Skip background (label 0)
                area = stats[i, cv2.CC_STAT_AREA]
                if area > min_area:
                    mask[labels == i] = 255
            
            return mask
            
        except Exception as e:
            logger.error(f"Error in rule-based segmentation: {str(e)}")
            return np.zeros_like(preprocessed, dtype=np.uint8)

    def _extract_boundaries(self, mask: np.ndarray) -> List[TumorBoundary]:
        """استخراج مرزهای تومور"""
        boundaries = []
        
        try:
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                if len(contour) < 5:  # Need at least 5 points for ellipse fitting
                    continue
                
                # Calculate properties
                area = cv2.contourArea(contour)
                if area < 100:  # Filter small regions
                    continue
                
                perimeter = cv2.arcLength(contour, True)
                
                # Centroid
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                else:
                    cx, cy = 0, 0
                
                # Bounding box
                x, y, w, h = cv2.boundingRect(contour)
                
                # Confidence based on contour regularity
                # More regular contours (closer to ellipse) have higher confidence
                ellipse = cv2.fitEllipse(contour)
                ellipse_area = np.pi * (ellipse[1][0] / 2) * (ellipse[1][1] / 2)
                confidence = min(1.0, area / ellipse_area) if ellipse_area > 0 else 0.5
                
                boundary = TumorBoundary(
                    contour=contour,
                    area=float(area),
                    perimeter=float(perimeter),
                    centroid=(float(cx), float(cy)),
                    bbox=(int(x), int(y), int(w), int(h)),
                    confidence=float(confidence)
                )
                
                boundaries.append(boundary)
            
            # Sort by area (largest first)
            boundaries.sort(key=lambda b: b.area, reverse=True)
            
        except Exception as e:
            logger.error(f"Error extracting boundaries: {str(e)}")
        
        return boundaries

    def _create_overlay(
        self,
        frame: np.ndarray,
        mask: np.ndarray,
        boundaries: List[TumorBoundary]
    ) -> np.ndarray:
        """ایجاد overlay با مرزهای تومور"""
        try:
            overlay = frame.copy()
            
            # Draw mask with transparency
            if len(overlay.shape) == 3:
                # Create colored mask
                colored_mask = np.zeros_like(overlay)
                colored_mask[mask > 0] = [0, 255, 0]  # Green for tumor
                
                # Blend
                overlay = cv2.addWeighted(overlay, 0.7, colored_mask, 0.3, 0)
            else:
                overlay = cv2.cvtColor(overlay, cv2.COLOR_GRAY2BGR)
                colored_mask = np.zeros_like(overlay)
                colored_mask[mask > 0] = [0, 255, 0]
                overlay = cv2.addWeighted(overlay, 0.7, colored_mask, 0.3, 0)
            
            # Draw boundaries
            for i, boundary in enumerate(boundaries):
                # Draw contour
                cv2.drawContours(overlay, [boundary.contour], -1, (0, 0, 255), 2)
                
                # Draw bounding box
                x, y, w, h = boundary.bbox
                cv2.rectangle(overlay, (x, y), (x + w, y + h), (255, 0, 0), 2)
                
                # Draw centroid
                cx, cy = boundary.centroid
                cv2.circle(overlay, (int(cx), int(cy)), 5, (255, 255, 0), -1)
                
                # Label
                label = f"Tumor {i+1} ({boundary.confidence:.1%})"
                cv2.putText(
                    overlay, label,
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (255, 255, 255), 2
                )
            
            return overlay
            
        except Exception as e:
            logger.error(f"Error creating overlay: {str(e)}")
            return frame

    def _calculate_confidence(self, mask: np.ndarray, boundaries: List[TumorBoundary]) -> float:
        """محاسبه اطمینان کلی"""
        try:
            if len(boundaries) == 0:
                return 0.0
            
            # Average confidence of boundaries
            avg_confidence = np.mean([b.confidence for b in boundaries])
            
            # Adjust based on mask quality
            mask_coverage = np.sum(mask > 0) / mask.size
            if mask_coverage < 0.01 or mask_coverage > 0.5:  # Too small or too large
                avg_confidence *= 0.7
            
            return float(min(1.0, avg_confidence))
            
        except:
            return 0.5

