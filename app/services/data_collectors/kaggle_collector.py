"""
Kaggle data collector
"""
import os
import pandas as pd
from typing import Dict, List, Optional
from app.services.data_collectors.base_collector import BaseDataCollector


class KaggleCollector(BaseDataCollector):
    """Collector for Kaggle datasets"""

    def __init__(self, api_key: Optional[str] = None, username: Optional[str] = None):
        super().__init__(api_key)
        self.username = username
        self._setup_kaggle()

    def _setup_kaggle(self):
        """Setup Kaggle API credentials"""
        try:
            import kaggle

            if self.api_key and self.username:
                os.environ["KAGGLE_USERNAME"] = self.username
                os.environ["KAGGLE_KEY"] = self.api_key

            self.kaggle_api = kaggle
        except ImportError:
            print("Warning: kaggle package not installed. Install with: pip install kaggle")
            self.kaggle_api = None

    def discover_datasets(self, query: str = "esophageal cancer") -> List[Dict]:
        """Discover Kaggle datasets"""
        if not self.kaggle_api:
            return []

        try:
            datasets = self.kaggle_api.api.dataset_list(search=query)
            return [
                {
                    "dataset_id": f"{ds.ref}",
                    "title": ds.title,
                    "size": ds.size,
                    "votes": ds.votes,
                    "usability_rating": ds.usabilityRating,
                }
                for ds in datasets
            ]

        except Exception as e:
            print(f"Error discovering Kaggle datasets: {str(e)}")
            return []

    def download_dataset(self, dataset_id: str, output_path: str) -> bool:
        """Download a Kaggle dataset"""
        if not self.kaggle_api:
            return False

        try:
            self.kaggle_api.api.dataset_download_files(
                dataset_id, path=output_path, unzip=True
            )
            return True

        except Exception as e:
            print(f"Error downloading Kaggle dataset {dataset_id}: {str(e)}")
            return False

    def validate_data(self, data: pd.DataFrame) -> Dict:
        """Validate Kaggle data"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "row_count": len(data),
            "column_count": len(data.columns) if not data.empty else 0,
        }

        if data.empty:
            validation_result["valid"] = False
            validation_result["errors"].append("Dataset is empty")
            return validation_result

        return validation_result

