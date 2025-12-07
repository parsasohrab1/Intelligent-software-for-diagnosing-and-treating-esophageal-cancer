"""
Real-Time Surgical Guidance System
سیستم راهنمای جراحی Real-Time برای آندوسکوپی
"""
import logging
import numpy as np
import cv2
from typing import Dict, Optional, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

from app.services.surgical_guidance.tumor_segmentation import (
    TumorSegmentation,
    SegmentationResult,
    EndoscopyMode
)
from app.services.surgical_guidance.depth_estimation import (
    DepthEstimator,
    DepthEstimation
)
from app.services.surgical_guidance.safe_margin_calculator import (
    SafeMarginCalculator,
    SafeMargin
)

logger = logging.getLogger(__name__)


@dataclass
class SurgicalGuidanceResult:
    """نتیجه راهنمای جراحی"""
    frame_id: int
    timestamp: float
    processing_time_ms: float
    segmentation: SegmentationResult
    depth_estimation: DepthEstimation
    safe_margin: SafeMargin
    overlay_image: np.ndarray
    error: Optional[str] = None


class SurgicalGuidanceSystem:
    """سیستم راهنمای جراحی Real-Time"""

    def __init__(self, endoscopy_mode: EndoscopyMode = EndoscopyMode.AUTO):
        self.segmentation = TumorSegmentation(mode=endoscopy_mode)
        self.depth_estimator = DepthEstimator()
        self.margin_calculator = SafeMarginCalculator()

    def process_frame(
        self,
        frame: np.ndarray,
        frame_id: int = 0,
        endoscopy_mode: Optional[EndoscopyMode] = None,
        segmentation_model: Optional[Any] = None,
        depth_model: Optional[Any] = None,
        custom_margin_mm: Optional[float] = None
    ) -> SurgicalGuidanceResult:
        """
        پردازش یک فریم برای راهنمای جراحی
        
        Args:
            frame: فریم آندوسکوپی
            frame_id: شناسه فریم
            endoscopy_mode: حالت آندوسکوپی
            segmentation_model: مدل segmentation
            depth_model: مدل تخمین عمق
            custom_margin_mm: حاشیه سفارشی
            
        Returns:
            نتیجه راهنمای جراحی
        """
        start_time = datetime.now().timestamp()
        
        try:
            # Step 1: Tumor segmentation
            segmentation_result = self.segmentation.segment_tumor(
                frame=frame,
                mode=endoscopy_mode,
                model=segmentation_model
            )
            
            if segmentation_result.error:
                return SurgicalGuidanceResult(
                    frame_id=frame_id,
                    timestamp=start_time,
                    processing_time_ms=(datetime.now().timestamp() - start_time) * 1000,
                    segmentation=segmentation_result,
                    depth_estimation=DepthEstimation(
                        mean_depth_mm=0.0,
                        max_depth_mm=0.0,
                        min_depth_mm=0.0,
                        depth_map=np.zeros_like(frame[:, :, 0] if len(frame.shape) == 3 else frame),
                        confidence=0.0,
                        invasion_level="unknown"
                    ),
                    safe_margin=SafeMargin(
                        margin_mask=np.zeros_like(frame[:, :, 0] if len(frame.shape) == 3 else frame, dtype=np.uint8),
                        margin_distance_mm=0.0,
                        resection_contour=np.array([]),
                        resection_area_mm2=0.0,
                        safety_score=0.0,
                        recommendations=[]
                    ),
                    overlay_image=frame.copy(),
                    error=segmentation_result.error
                )
            
            # Step 2: Depth estimation
            depth_estimation = self.depth_estimator.estimate_invasion_depth(
                frame=frame,
                tumor_mask=segmentation_result.segmentation_mask,
                tumor_boundaries=segmentation_result.tumor_boundaries,
                model=depth_model
            )
            
            # Step 3: Safe margin calculation
            safe_margin = self.margin_calculator.calculate_safe_margin(
                tumor_boundaries=segmentation_result.tumor_boundaries,
                depth_estimation=depth_estimation,
                frame_shape=frame.shape,
                custom_margin_mm=custom_margin_mm
            )
            
            # Step 4: Create comprehensive overlay
            overlay = self._create_comprehensive_overlay(
                frame=frame,
                segmentation_result=segmentation_result,
                depth_estimation=depth_estimation,
                safe_margin=safe_margin
            )
            
            processing_time = (datetime.now().timestamp() - start_time) * 1000
            
            return SurgicalGuidanceResult(
                frame_id=frame_id,
                timestamp=start_time,
                processing_time_ms=processing_time,
                segmentation=segmentation_result,
                depth_estimation=depth_estimation,
                safe_margin=safe_margin,
                overlay_image=overlay
            )
            
        except Exception as e:
            logger.error(f"Error in surgical guidance: {str(e)}")
            return SurgicalGuidanceResult(
                frame_id=frame_id,
                timestamp=start_time,
                processing_time_ms=(datetime.now().timestamp() - start_time) * 1000,
                segmentation=SegmentationResult(
                    frame_id=frame_id,
                    timestamp=start_time,
                    processing_time_ms=0.0,
                    tumor_boundaries=[],
                    segmentation_mask=np.zeros_like(frame[:, :, 0] if len(frame.shape) == 3 else frame),
                    overlay_image=frame.copy(),
                    confidence=0.0
                ),
                depth_estimation=DepthEstimation(
                    mean_depth_mm=0.0,
                    max_depth_mm=0.0,
                    min_depth_mm=0.0,
                    depth_map=np.zeros_like(frame[:, :, 0] if len(frame.shape) == 3 else frame),
                    confidence=0.0,
                    invasion_level="unknown"
                ),
                safe_margin=SafeMargin(
                    margin_mask=np.zeros_like(frame[:, :, 0] if len(frame.shape) == 3 else frame, dtype=np.uint8),
                    margin_distance_mm=0.0,
                    resection_contour=np.array([]),
                    resection_area_mm2=0.0,
                    safety_score=0.0,
                    recommendations=[]
                ),
                overlay_image=frame.copy(),
                error=str(e)
            )

    def _create_comprehensive_overlay(
        self,
        frame: np.ndarray,
        segmentation_result: SegmentationResult,
        depth_estimation: DepthEstimation,
        safe_margin: SafeMargin
    ) -> np.ndarray:
        """ایجاد overlay جامع"""
        try:
            overlay = frame.copy()
            
            if len(overlay.shape) == 2:
                overlay = cv2.cvtColor(overlay, cv2.COLOR_GRAY2BGR)
            
            # Draw safe margin (yellow)
            margin_colored = np.zeros_like(overlay)
            margin_colored[safe_margin.margin_mask > 0] = [0, 255, 255]  # Yellow
            overlay = cv2.addWeighted(overlay, 0.6, margin_colored, 0.4, 0)
            
            # Draw tumor segmentation (red)
            tumor_colored = np.zeros_like(overlay)
            tumor_colored[segmentation_result.segmentation_mask > 0] = [0, 0, 255]  # Red
            overlay = cv2.addWeighted(overlay, 0.7, tumor_colored, 0.3, 0)
            
            # Draw tumor boundaries (thick red line)
            for boundary in segmentation_result.tumor_boundaries:
                cv2.drawContours(overlay, [boundary.contour], -1, (0, 0, 255), 3)
            
            # Draw resection contour (green)
            if len(safe_margin.resection_contour) > 0:
                cv2.drawContours(overlay, [safe_margin.resection_contour], -1, (0, 255, 0), 2)
            
            # Draw depth visualization
            depth_colored = self._colorize_depth(depth_estimation.depth_map)
            depth_overlay = cv2.addWeighted(overlay, 0.8, depth_colored, 0.2, 0)
            overlay = depth_overlay
            
            # Add text annotations
            self._add_text_annotations(
                overlay=overlay,
                segmentation_result=segmentation_result,
                depth_estimation=depth_estimation,
                safe_margin=safe_margin
            )
            
            return overlay
            
        except Exception as e:
            logger.error(f"Error creating overlay: {str(e)}")
            return frame

    def _colorize_depth(self, depth_map: np.ndarray) -> np.ndarray:
        """رنگ‌آمیزی نقشه عمق"""
        try:
            # Normalize depth map
            if depth_map.max() > 0:
                normalized = (depth_map / depth_map.max() * 255).astype(np.uint8)
            else:
                normalized = np.zeros_like(depth_map, dtype=np.uint8)
            
            # Apply colormap (blue = shallow, red = deep)
            colored = cv2.applyColorMap(normalized, cv2.COLORMAP_JET)
            
            return colored
        except:
            return np.zeros((*depth_map.shape, 3), dtype=np.uint8)

    def _add_text_annotations(
        self,
        overlay: np.ndarray,
        segmentation_result: SegmentationResult,
        depth_estimation: DepthEstimation,
        safe_margin: SafeMargin
    ):
        """افزودن حاشیه‌نویسی متنی"""
        try:
            y_offset = 30
            line_height = 25
            
            # Tumor info
            if len(segmentation_result.tumor_boundaries) > 0:
                text = f"Tumors: {len(segmentation_result.tumor_boundaries)} (Conf: {segmentation_result.confidence:.1%})"
                cv2.putText(
                    overlay, text,
                    (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (255, 255, 255), 2
                )
                y_offset += line_height
            
            # Depth info
            text = f"Depth: {depth_estimation.mean_depth_mm:.1f}mm ({depth_estimation.invasion_level})"
            cv2.putText(
                overlay, text,
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (255, 255, 255), 2
            )
            y_offset += line_height
            
            # Margin info
            text = f"Safe Margin: {safe_margin.margin_distance_mm:.1f}mm (Safety: {safe_margin.safety_score:.1%})"
            cv2.putText(
                overlay, text,
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (255, 255, 255), 2
            )
            y_offset += line_height
            
            # Resection area
            text = f"Resection Area: {safe_margin.resection_area_mm2:.1f}mm²"
            cv2.putText(
                overlay, text,
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (255, 255, 255), 2
            )
            
        except Exception as e:
            logger.error(f"Error adding text annotations: {str(e)}")

