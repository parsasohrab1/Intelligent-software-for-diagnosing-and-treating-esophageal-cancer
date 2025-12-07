"""
Safe Margin Calculator for Surgical Resection
محاسبه حاشیه امن برداشت
"""
import logging
import numpy as np
import cv2
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime

from app.services.surgical_guidance.tumor_segmentation import TumorBoundary
from app.services.surgical_guidance.depth_estimation import DepthEstimation

logger = logging.getLogger(__name__)


@dataclass
class SafeMargin:
    """حاشیه امن برداشت"""
    margin_mask: np.ndarray  # ماسک حاشیه امن
    margin_distance_mm: float  # فاصله حاشیه (میلی‌متر)
    resection_contour: np.ndarray  # کانتور برداشت پیشنهادی
    resection_area_mm2: float  # مساحت برداشت (میلی‌متر مربع)
    safety_score: float  # امتیاز ایمنی (0-1)
    recommendations: List[str]  # توصیه‌ها


class SafeMarginCalculator:
    """محاسبه حاشیه امن برداشت"""

    def __init__(self):
        # استانداردهای حاشیه امن بر اساس نوع سرطان
        self.margin_standards = {
            "superficial": 2.0,  # 2mm برای نفوذ سطحی
            "moderate": 5.0,  # 5mm برای نفوذ متوسط
            "deep": 10.0  # 10mm برای نفوذ عمیق
        }

    def calculate_safe_margin(
        self,
        tumor_boundaries: List[TumorBoundary],
        depth_estimation: DepthEstimation,
        frame_shape: Tuple[int, int],
        custom_margin_mm: Optional[float] = None
    ) -> SafeMargin:
        """
        محاسبه حاشیه امن برداشت
        
        Args:
            tumor_boundaries: مرزهای تومور
            depth_estimation: تخمین عمق نفوذ
            frame_shape: ابعاد فریم
            custom_margin_mm: حاشیه سفارشی (میلی‌متر)
            
        Returns:
            حاشیه امن
        """
        try:
            if len(tumor_boundaries) == 0:
                return SafeMargin(
                    margin_mask=np.zeros(frame_shape[:2], dtype=np.uint8),
                    margin_distance_mm=0.0,
                    resection_contour=np.array([]),
                    resection_area_mm2=0.0,
                    safety_score=0.0,
                    recommendations=["No tumor detected"]
                )
            
            # Determine margin distance based on invasion depth
            if custom_margin_mm is not None:
                margin_distance_mm = custom_margin_mm
            else:
                margin_distance_mm = self._determine_margin_distance(depth_estimation)
            
            # Convert mm to pixels (assuming typical endoscopy: ~1mm = 10 pixels at close range)
            # This is approximate and should be calibrated based on endoscope specifications
            pixels_per_mm = 10.0  # Calibration factor
            margin_pixels = int(margin_distance_mm * pixels_per_mm)
            
            # Create margin mask
            margin_mask = np.zeros(frame_shape[:2], dtype=np.uint8)
            resection_contours = []
            
            for boundary in tumor_boundaries:
                # Dilate tumor contour to create margin
                temp_mask = np.zeros(frame_shape[:2], dtype=np.uint8)
                cv2.drawContours(temp_mask, [boundary.contour], -1, 255, -1)
                
                # Dilate by margin distance
                kernel_size = margin_pixels * 2 + 1
                kernel = np.ones((kernel_size, kernel_size), np.uint8)
                dilated = cv2.dilate(temp_mask, kernel, iterations=1)
                
                # Find dilated contour
                contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    resection_contours.append(contours[0])
                    cv2.drawContours(margin_mask, contours, -1, 255, -1)
            
            # Combine all resection contours
            if resection_contours:
                combined_contour = np.vstack(resection_contours)
            else:
                combined_contour = np.array([])
            
            # Calculate resection area
            resection_area_pixels = np.sum(margin_mask > 0)
            resection_area_mm2 = (resection_area_pixels / (pixels_per_mm ** 2))
            
            # Calculate safety score
            safety_score = self._calculate_safety_score(
                tumor_boundaries,
                depth_estimation,
                margin_distance_mm
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                tumor_boundaries,
                depth_estimation,
                margin_distance_mm,
                safety_score
            )
            
            return SafeMargin(
                margin_mask=margin_mask,
                margin_distance_mm=margin_distance_mm,
                resection_contour=combined_contour,
                resection_area_mm2=resection_area_mm2,
                safety_score=safety_score,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error calculating safe margin: {str(e)}")
            return SafeMargin(
                margin_mask=np.zeros(frame_shape[:2], dtype=np.uint8),
                margin_distance_mm=0.0,
                resection_contour=np.array([]),
                resection_area_mm2=0.0,
                safety_score=0.0,
                recommendations=[f"Error: {str(e)}"]
            )

    def _determine_margin_distance(self, depth_estimation: DepthEstimation) -> float:
        """تعیین فاصله حاشیه بر اساس عمق نفوذ"""
        invasion_level = depth_estimation.invasion_level
        
        if invasion_level == "superficial":
            return self.margin_standards["superficial"]
        elif invasion_level == "moderate":
            return self.margin_standards["moderate"]
        else:  # deep
            return self.margin_standards["deep"]

    def _calculate_safety_score(
        self,
        tumor_boundaries: List[TumorBoundary],
        depth_estimation: DepthEstimation,
        margin_distance_mm: float
    ) -> float:
        """محاسبه امتیاز ایمنی"""
        try:
            score = 1.0
            
            # Penalize for deep invasion
            if depth_estimation.invasion_level == "deep":
                score *= 0.7
            elif depth_estimation.invasion_level == "moderate":
                score *= 0.85
            
            # Penalize for multiple tumors (more complex resection)
            if len(tumor_boundaries) > 1:
                score *= 0.9
            
            # Reward adequate margin
            required_margin = self.margin_standards.get(depth_estimation.invasion_level, 5.0)
            if margin_distance_mm >= required_margin:
                score *= 1.0
            elif margin_distance_mm >= required_margin * 0.8:
                score *= 0.9
            else:
                score *= 0.7
            
            # Adjust based on depth confidence
            score *= (0.5 + 0.5 * depth_estimation.confidence)
            
            return float(max(0.0, min(1.0, score)))
            
        except:
            return 0.5

    def _generate_recommendations(
        self,
        tumor_boundaries: List[TumorBoundary],
        depth_estimation: DepthEstimation,
        margin_distance_mm: float,
        safety_score: float
    ) -> List[str]:
        """تولید توصیه‌ها"""
        recommendations = []
        
        # Margin recommendation
        recommendations.append(
            f"Recommended safe margin: {margin_distance_mm:.1f}mm "
            f"({depth_estimation.invasion_level} invasion)"
        )
        
        # Depth information
        recommendations.append(
            f"Estimated invasion depth: {depth_estimation.mean_depth_mm:.1f}mm "
            f"(range: {depth_estimation.min_depth_mm:.1f}-{depth_estimation.max_depth_mm:.1f}mm)"
        )
        
        # Safety score
        if safety_score >= 0.8:
            recommendations.append("High safety score: Resection margin appears adequate")
        elif safety_score >= 0.6:
            recommendations.append("Moderate safety score: Consider additional margin or frozen section")
        else:
            recommendations.append("Low safety score: Strongly recommend wider margin or alternative approach")
        
        # Multiple tumors
        if len(tumor_boundaries) > 1:
            recommendations.append(f"Multiple tumor regions detected ({len(tumor_boundaries)}): Plan resection accordingly")
        
        # Deep invasion warning
        if depth_estimation.invasion_level == "deep":
            recommendations.append(
                "WARNING: Deep invasion detected. Consider preoperative staging "
                "and multidisciplinary team discussion."
            )
        
        return recommendations

