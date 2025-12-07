"""
Radiomics Feature Extraction
استخراج ویژگی‌های رادیومیکس از تصاویر پزشکی
"""
import logging
import numpy as np
from typing import Dict, List, Optional, Any
from pathlib import Path
import cv2
from datetime import datetime

logger = logging.getLogger(__name__)


class RadiomicsExtractor:
    """استخراج ویژگی‌های رادیومیکس از تصاویر"""

    def __init__(self):
        self.feature_categories = [
            "first_order",
            "shape",
            "texture",
            "wavelet",
            "gradient"
        ]

    def extract_features(
        self,
        image: np.ndarray,
        mask: Optional[np.ndarray] = None,
        modality: str = "CT"
    ) -> Dict[str, Any]:
        """
        استخراج ویژگی‌های رادیومیکس از تصویر
        
        Args:
            image: تصویر ورودی
            mask: ماسک ROI (اختیاری)
            modality: نوع تصویربرداری
            
        Returns:
            ویژگی‌های رادیومیکس
        """
        try:
            features = {
                "modality": modality,
                "extraction_date": datetime.now().isoformat(),
                "first_order": {},
                "shape": {},
                "texture": {},
                "wavelet": {},
                "gradient": {}
            }

            # Preprocess image
            processed_image = self._preprocess_image(image, modality)
            
            # Create mask if not provided
            if mask is None:
                mask = self._create_default_mask(processed_image)

            # Extract first-order features
            features["first_order"] = self._extract_first_order_features(processed_image, mask)
            
            # Extract shape features
            features["shape"] = self._extract_shape_features(processed_image, mask)
            
            # Extract texture features
            features["texture"] = self._extract_texture_features(processed_image, mask)
            
            # Extract wavelet features
            features["wavelet"] = self._extract_wavelet_features(processed_image, mask)
            
            # Extract gradient features
            features["gradient"] = self._extract_gradient_features(processed_image, mask)

            return features

        except Exception as e:
            logger.error(f"Error extracting radiomics features: {str(e)}")
            return {
                "error": str(e),
                "modality": modality
            }

    def _preprocess_image(self, image: np.ndarray, modality: str) -> np.ndarray:
        """پیش‌پردازش تصویر"""
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Normalize
        image = image.astype(np.float32)
        if image.max() > 0:
            image = (image - image.min()) / (image.max() - image.min()) * 255
        
        return image.astype(np.uint8)

    def _create_default_mask(self, image: np.ndarray) -> np.ndarray:
        """ایجاد ماسک پیش‌فرض (کل تصویر)"""
        return np.ones_like(image, dtype=np.uint8)

    def _extract_first_order_features(
        self,
        image: np.ndarray,
        mask: np.ndarray
    ) -> Dict[str, float]:
        """استخراج ویژگی‌های مرتبه اول"""
        try:
            roi = image[mask > 0]
            
            if len(roi) == 0:
                return {}
            
            features = {
                "mean": float(np.mean(roi)),
                "std": float(np.std(roi)),
                "variance": float(np.var(roi)),
                "skewness": float(self._skewness(roi)),
                "kurtosis": float(self._kurtosis(roi)),
                "min": float(np.min(roi)),
                "max": float(np.max(roi)),
                "range": float(np.max(roi) - np.min(roi)),
                "median": float(np.median(roi)),
                "percentile_10": float(np.percentile(roi, 10)),
                "percentile_25": float(np.percentile(roi, 25)),
                "percentile_75": float(np.percentile(roi, 75)),
                "percentile_90": float(np.percentile(roi, 90)),
                "energy": float(np.sum(roi ** 2)),
                "entropy": float(self._entropy(roi))
            }
            
            return features
        except Exception as e:
            logger.error(f"Error extracting first-order features: {str(e)}")
            return {}

    def _extract_shape_features(
        self,
        image: np.ndarray,
        mask: np.ndarray
    ) -> Dict[str, float]:
        """استخراج ویژگی‌های شکل"""
        try:
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if len(contours) == 0:
                return {}
            
            # Use largest contour
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            perimeter = cv2.arcLength(largest_contour, True)
            
            # Bounding box
            x, y, w, h = cv2.boundingRect(largest_contour)
            
            features = {
                "area": float(area),
                "perimeter": float(perimeter),
                "compactness": float(4 * np.pi * area / (perimeter ** 2)) if perimeter > 0 else 0.0,
                "sphericity": float(np.sqrt(4 * np.pi * area / (perimeter ** 2))) if perimeter > 0 else 0.0,
                "aspect_ratio": float(w / h) if h > 0 else 0.0,
                "extent": float(area / (w * h)) if (w * h) > 0 else 0.0,
                "solidity": float(area / cv2.contourArea(cv2.convexHull(largest_contour))) if len(largest_contour) > 0 else 0.0,
                "eccentricity": float(np.sqrt(1 - (min(w, h) / max(w, h)) ** 2)) if max(w, h) > 0 else 0.0
            }
            
            return features
        except Exception as e:
            logger.error(f"Error extracting shape features: {str(e)}")
            return {}

    def _extract_texture_features(
        self,
        image: np.ndarray,
        mask: np.ndarray
    ) -> Dict[str, float]:
        """استخراج ویژگی‌های بافت"""
        try:
            roi = image[mask > 0]
            
            if len(roi) == 0:
                return {}
            
            # GLCM-like features (simplified)
            # Calculate co-occurrence matrix
            glcm = self._calculate_glcm(image, mask)
            
            features = {
                "contrast": float(self._glcm_contrast(glcm)),
                "dissimilarity": float(self._glcm_dissimilarity(glcm)),
                "homogeneity": float(self._glcm_homogeneity(glcm)),
                "energy": float(self._glcm_energy(glcm)),
                "correlation": float(self._glcm_correlation(glcm)),
                "variance": float(np.var(roi)),
                "sum_average": float(np.mean(roi)),
                "sum_variance": float(np.var(roi)),
                "sum_entropy": float(self._entropy(roi)),
                "difference_variance": float(np.var(np.diff(roi))),
                "difference_entropy": float(self._entropy(np.diff(roi))) if len(roi) > 1 else 0.0
            }
            
            return features
        except Exception as e:
            logger.error(f"Error extracting texture features: {str(e)}")
            return {}

    def _extract_wavelet_features(
        self,
        image: np.ndarray,
        mask: np.ndarray
    ) -> Dict[str, float]:
        """استخراج ویژگی‌های موجک"""
        try:
            # Simplified wavelet features
            # In production, use pywavelets or similar library
            roi = image[mask > 0]
            
            if len(roi) == 0:
                return {}
            
            # Calculate gradients as approximation
            grad_x = np.gradient(roi.reshape(image.shape)[mask > 0])
            grad_y = np.gradient(roi.reshape(image.shape)[mask > 0])
            
            features = {
                "wavelet_LL_mean": float(np.mean(roi)),
                "wavelet_LL_std": float(np.std(roi)),
                "wavelet_LH_mean": float(np.mean(grad_x)) if len(grad_x) > 0 else 0.0,
                "wavelet_LH_std": float(np.std(grad_x)) if len(grad_x) > 0 else 0.0,
                "wavelet_HL_mean": float(np.mean(grad_y)) if len(grad_y) > 0 else 0.0,
                "wavelet_HL_std": float(np.std(grad_y)) if len(grad_y) > 0 else 0.0,
                "wavelet_HH_mean": float(np.mean(np.sqrt(grad_x ** 2 + grad_y ** 2))) if len(grad_x) > 0 and len(grad_y) > 0 else 0.0,
                "wavelet_HH_std": float(np.std(np.sqrt(grad_x ** 2 + grad_y ** 2))) if len(grad_x) > 0 and len(grad_y) > 0 else 0.0
            }
            
            return features
        except Exception as e:
            logger.error(f"Error extracting wavelet features: {str(e)}")
            return {}

    def _extract_gradient_features(
        self,
        image: np.ndarray,
        mask: np.ndarray
    ) -> Dict[str, float]:
        """استخراج ویژگی‌های گرادیان"""
        try:
            roi = image[mask > 0]
            
            if len(roi) == 0:
                return {}
            
            # Calculate gradients
            grad_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)[mask > 0]
            grad_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)[mask > 0]
            magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)
            
            features = {
                "gradient_mean": float(np.mean(magnitude)),
                "gradient_std": float(np.std(magnitude)),
                "gradient_max": float(np.max(magnitude)),
                "gradient_min": float(np.min(magnitude)),
                "gradient_range": float(np.max(magnitude) - np.min(magnitude)),
                "gradient_entropy": float(self._entropy(magnitude))
            }
            
            return features
        except Exception as e:
            logger.error(f"Error extracting gradient features: {str(e)}")
            return {}

    def _calculate_glcm(self, image: np.ndarray, mask: np.ndarray, distance: int = 1) -> np.ndarray:
        """محاسبه GLCM (simplified)"""
        try:
            # Simplified GLCM calculation
            levels = 256
            glcm = np.zeros((levels, levels), dtype=np.float64)
            
            roi = image[mask > 0]
            if len(roi) < 2:
                return glcm
            
            # Calculate co-occurrence for horizontal direction
            for i in range(len(roi) - distance):
                if i + distance < len(roi):
                    glcm[roi[i], roi[i + distance]] += 1
            
            # Normalize
            if glcm.sum() > 0:
                glcm = glcm / glcm.sum()
            
            return glcm
        except Exception as e:
            logger.error(f"Error calculating GLCM: {str(e)}")
            return np.zeros((256, 256))

    def _glcm_contrast(self, glcm: np.ndarray) -> float:
        """محاسبه contrast از GLCM"""
        try:
            contrast = 0.0
            for i in range(glcm.shape[0]):
                for j in range(glcm.shape[1]):
                    contrast += glcm[i, j] * ((i - j) ** 2)
            return contrast
        except:
            return 0.0

    def _glcm_dissimilarity(self, glcm: np.ndarray) -> float:
        """محاسبه dissimilarity از GLCM"""
        try:
            dissimilarity = 0.0
            for i in range(glcm.shape[0]):
                for j in range(glcm.shape[1]):
                    dissimilarity += glcm[i, j] * abs(i - j)
            return dissimilarity
        except:
            return 0.0

    def _glcm_homogeneity(self, glcm: np.ndarray) -> float:
        """محاسبه homogeneity از GLCM"""
        try:
            homogeneity = 0.0
            for i in range(glcm.shape[0]):
                for j in range(glcm.shape[1]):
                    homogeneity += glcm[i, j] / (1 + abs(i - j))
            return homogeneity
        except:
            return 0.0

    def _glcm_energy(self, glcm: np.ndarray) -> float:
        """محاسبه energy از GLCM"""
        try:
            return float(np.sqrt(np.sum(glcm ** 2)))
        except:
            return 0.0

    def _glcm_correlation(self, glcm: np.ndarray) -> float:
        """محاسبه correlation از GLCM"""
        try:
            mean_i = np.sum([i * np.sum(glcm[i, :]) for i in range(glcm.shape[0])])
            mean_j = np.sum([j * np.sum(glcm[:, j]) for j in range(glcm.shape[1])])
            
            std_i = np.sqrt(np.sum([((i - mean_i) ** 2) * np.sum(glcm[i, :]) for i in range(glcm.shape[0])]))
            std_j = np.sqrt(np.sum([((j - mean_j) ** 2) * np.sum(glcm[:, j]) for j in range(glcm.shape[1])]))
            
            if std_i * std_j == 0:
                return 0.0
            
            correlation = 0.0
            for i in range(glcm.shape[0]):
                for j in range(glcm.shape[1]):
                    correlation += glcm[i, j] * ((i - mean_i) * (j - mean_j)) / (std_i * std_j)
            
            return correlation
        except:
            return 0.0

    def _skewness(self, data: np.ndarray) -> float:
        """محاسبه skewness"""
        try:
            mean = np.mean(data)
            std = np.std(data)
            if std == 0:
                return 0.0
            return float(np.mean(((data - mean) / std) ** 3))
        except:
            return 0.0

    def _kurtosis(self, data: np.ndarray) -> float:
        """محاسبه kurtosis"""
        try:
            mean = np.mean(data)
            std = np.std(data)
            if std == 0:
                return 0.0
            return float(np.mean(((data - mean) / std) ** 4))
        except:
            return 0.0

    def _entropy(self, data: np.ndarray) -> float:
        """محاسبه entropy"""
        try:
            hist, _ = np.histogram(data, bins=256)
            hist = hist[hist > 0]
            prob = hist / hist.sum()
            return float(-np.sum(prob * np.log2(prob)))
        except:
            return 0.0

