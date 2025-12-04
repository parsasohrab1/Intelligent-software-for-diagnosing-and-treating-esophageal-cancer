"""
Multi-Modality Data Processing Service
Handles medical images (CT/MRI/DICOM) and unstructured text reports
"""
import logging
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import numpy as np
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Process medical images (CT, MRI, DICOM, NIfTI)"""

    def __init__(self):
        self.backend = settings.IMAGE_PROCESSING_BACKEND
        self.max_size_mb = settings.MAX_IMAGE_SIZE_MB
        self.supported_formats = settings.SUPPORTED_IMAGE_FORMATS

    def process_image(
        self, image_path: str, modality: str = "CT"
    ) -> Dict[str, Any]:
        """
        Process a medical image file
        Returns metadata and processed image data
        """
        try:
            image_path_obj = Path(image_path)

            if not image_path_obj.exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")

            # Check file size
            file_size_mb = image_path_obj.stat().st_size / (1024 * 1024)
            if file_size_mb > self.max_size_mb:
                raise ValueError(
                    f"Image file too large: {file_size_mb:.2f}MB > {self.max_size_mb}MB"
                )

            # Determine format
            file_extension = image_path_obj.suffix.lower()
            format_type = self._detect_format(file_extension)

            metadata = {
                "file_path": str(image_path),
                "modality": modality,
                "format": format_type,
                "file_size_mb": float(file_size_mb),
                "processed_at": datetime.now().isoformat(),
            }

            # Process based on format
            if format_type == "dicom":
                image_data = self._process_dicom(image_path)
            elif format_type == "nifti":
                image_data = self._process_nifti(image_path)
            else:
                # Standard image formats (PNG, JPG, etc.)
                image_data = self._process_standard_image(image_path)

            metadata.update(image_data)
            return metadata

        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise

    def _detect_format(self, extension: str) -> str:
        """Detect image format from extension"""
        extension_map = {
            ".dcm": "dicom",
            ".dicom": "dicom",
            ".nii": "nifti",
            ".nii.gz": "nifti",
            ".png": "png",
            ".jpg": "jpg",
            ".jpeg": "jpeg",
            ".tiff": "tiff",
            ".tif": "tiff",
        }
        return extension_map.get(extension, "unknown")

    def _process_dicom(self, file_path: str) -> Dict[str, Any]:
        """Process DICOM file"""
        try:
            import pydicom

            ds = pydicom.dcmread(file_path)

            # Extract DICOM metadata
            metadata = {
                "patient_id": getattr(ds, "PatientID", None),
                "study_date": getattr(ds, "StudyDate", None),
                "modality": getattr(ds, "Modality", None),
                "series_description": getattr(ds, "SeriesDescription", None),
                "slice_thickness": getattr(ds, "SliceThickness", None),
                "pixel_spacing": getattr(ds, "PixelSpacing", None),
            }

            # Extract pixel array
            pixel_array = ds.pixel_array
            image_stats = {
                "shape": list(pixel_array.shape),
                "dtype": str(pixel_array.dtype),
                "min_value": float(np.min(pixel_array)),
                "max_value": float(np.max(pixel_array)),
                "mean_value": float(np.mean(pixel_array)),
                "std_value": float(np.std(pixel_array)),
            }

            return {
                "dicom_metadata": metadata,
                "image_statistics": image_stats,
                "has_pixel_data": True,
            }

        except ImportError:
            logger.warning("pydicom not installed. Install with: pip install pydicom")
            return {"error": "DICOM processing requires pydicom library"}
        except Exception as e:
            logger.error(f"Error processing DICOM: {str(e)}")
            return {"error": str(e)}

    def _process_nifti(self, file_path: str) -> Dict[str, Any]:
        """Process NIfTI file"""
        try:
            import nibabel as nib

            nii_img = nib.load(file_path)
            data = nii_img.get_fdata()

            # Extract header information
            header = nii_img.header
            affine = nii_img.affine

            image_stats = {
                "shape": list(data.shape),
                "dtype": str(data.dtype),
                "min_value": float(np.min(data)),
                "max_value": float(np.max(data)),
                "mean_value": float(np.mean(data)),
                "std_value": float(np.std(data)),
            }

            return {
                "nifti_metadata": {
                    "voxel_sizes": list(header.get_zooms()),
                    "affine_matrix": affine.tolist() if affine is not None else None,
                },
                "image_statistics": image_stats,
                "has_pixel_data": True,
            }

        except ImportError:
            logger.warning("nibabel not installed. Install with: pip install nibabel")
            return {"error": "NIfTI processing requires nibabel library"}
        except Exception as e:
            logger.error(f"Error processing NIfTI: {str(e)}")
            return {"error": str(e)}

    def _process_standard_image(self, file_path: str) -> Dict[str, Any]:
        """Process standard image formats (PNG, JPG, etc.)"""
        try:
            if self.backend == "opencv":
                import cv2

                img = cv2.imread(file_path)
                if img is None:
                    raise ValueError(f"Could not read image: {file_path}")

                # Convert to grayscale if needed
                if len(img.shape) == 3:
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                else:
                    gray = img

                image_stats = {
                    "shape": list(gray.shape),
                    "dtype": str(gray.dtype),
                    "min_value": float(np.min(gray)),
                    "max_value": float(np.max(gray)),
                    "mean_value": float(np.mean(gray)),
                    "std_value": float(np.std(gray)),
                }

                return {
                    "image_statistics": image_stats,
                    "has_pixel_data": True,
                }

            else:  # pillow
                from PIL import Image

                img = Image.open(file_path)
                img_array = np.array(img)

                image_stats = {
                    "shape": list(img_array.shape),
                    "dtype": str(img_array.dtype),
                    "min_value": float(np.min(img_array)),
                    "max_value": float(np.max(img_array)),
                    "mean_value": float(np.mean(img_array)),
                    "std_value": float(np.std(img_array)),
                }

                return {
                    "image_statistics": image_stats,
                    "has_pixel_data": True,
                    "mode": img.mode,
                }

        except ImportError:
            logger.warning(
                f"{self.backend} not installed. Install opencv-python or Pillow"
            )
            return {"error": f"Image processing requires {self.backend} library"}
        except Exception as e:
            logger.error(f"Error processing standard image: {str(e)}")
            return {"error": str(e)}


class TextReportProcessor:
    """Process unstructured text reports"""

    def __init__(self):
        self.backend = settings.TEXT_PROCESSING_BACKEND

    def process_text_report(self, text: str, report_type: str = "radiology") -> Dict[str, Any]:
        """
        Process unstructured text report
        Extracts key information, entities, and structured data
        """
        try:
            # Basic text processing
            text_metadata = {
                "text_length": len(text),
                "word_count": len(text.split()),
                "sentence_count": len(text.split(".")),
                "report_type": report_type,
                "processed_at": datetime.now().isoformat(),
            }

            # Extract structured information
            extracted_info = self._extract_medical_entities(text)
            text_metadata["extracted_entities"] = extracted_info

            # Extract key findings
            findings = self._extract_findings(text)
            text_metadata["findings"] = findings

            # Extract measurements
            measurements = self._extract_measurements(text)
            text_metadata["measurements"] = measurements

            return text_metadata

        except Exception as e:
            logger.error(f"Error processing text report: {str(e)}")
            raise

    def _extract_medical_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract medical entities from text"""
        entities = {
            "anatomical_structures": [],
            "pathologies": [],
            "measurements": [],
            "dates": [],
        }

        # Simple keyword-based extraction (can be enhanced with NLP)
        pathology_keywords = [
            "tumor",
            "cancer",
            "lesion",
            "mass",
            "nodule",
            "metastasis",
            "malignancy",
        ]
        anatomical_keywords = [
            "esophagus",
            "stomach",
            "lymph node",
            "chest",
            "abdomen",
        ]

        text_lower = text.lower()
        for keyword in pathology_keywords:
            if keyword in text_lower:
                entities["pathologies"].append(keyword)

        for keyword in anatomical_keywords:
            if keyword in text_lower:
                entities["anatomical_structures"].append(keyword)

        # Extract measurements (numbers with units)
        import re

        measurement_pattern = r"(\d+\.?\d*)\s*(cm|mm|ml|%)"
        measurements = re.findall(measurement_pattern, text)
        entities["measurements"] = [f"{val} {unit}" for val, unit in measurements]

        return entities

    def _extract_findings(self, text: str) -> List[str]:
        """Extract key findings from report"""
        findings = []

        # Look for "FINDINGS:" or "IMPRESSION:" sections
        import re

        findings_section = re.search(
            r"(?:FINDINGS?|IMPRESSION):\s*(.+?)(?:\n\n|\Z)", text, re.IGNORECASE | re.DOTALL
        )
        if findings_section:
            findings_text = findings_section.group(1)
            # Split into sentences
            sentences = findings_text.split(".")
            findings = [s.strip() for s in sentences if s.strip()]

        return findings[:10]  # Return top 10 findings

    def _extract_measurements(self, text: str) -> List[Dict[str, Any]]:
        """Extract measurements from text"""
        measurements = []

        import re

        # Pattern for measurements like "2.5 cm", "10 mm", etc.
        pattern = r"(\d+\.?\d*)\s*(cm|mm|ml|%)"
        matches = re.finditer(pattern, text)

        for match in matches:
            measurements.append({
                "value": float(match.group(1)),
                "unit": match.group(2),
                "text": match.group(0),
            })

        return measurements


class MultiModalityProcessor:
    """Main processor for multi-modality data"""

    def __init__(self):
        self.image_processor = ImageProcessor()
        self.text_processor = TextReportProcessor()

    def process_imaging_data(
        self, image_path: str, modality: str = "CT", text_report: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process imaging data with optional text report
        """
        result = {
            "modality": modality,
            "processed_at": datetime.now().isoformat(),
        }

        # Process image
        try:
            image_data = self.image_processor.process_image(image_path, modality)
            result["image"] = image_data
        except Exception as e:
            result["image"] = {"error": str(e)}

        # Process text report if provided
        if text_report:
            try:
                text_data = self.text_processor.process_text_report(
                    text_report, report_type=f"{modality}_report"
                )
                result["text_report"] = text_data
            except Exception as e:
                result["text_report"] = {"error": str(e)}

        return result

    def process_text_only(self, text: str, report_type: str = "clinical") -> Dict[str, Any]:
        """Process text report only"""
        return self.text_processor.process_text_report(text, report_type)

