"""
TCGA (The Cancer Genome Atlas) data collector
"""
import requests
import pandas as pd
from typing import Dict, List, Optional
import time
from app.services.data_collectors.base_collector import BaseDataCollector


class TCGACollector(BaseDataCollector):
    """Collector for TCGA data via GDC API"""

    BASE_URL = "https://api.gdc.cancer.gov"
    PROJECT_ID = "TCGA-ESCA"  # Esophageal Cancer

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def discover_datasets(self, query: str = "esophageal") -> List[Dict]:
        """Discover TCGA datasets for esophageal cancer"""
        try:
            # Search for files
            files_endpoint = f"{self.BASE_URL}/files"
            params = {
                "filters": {
                    "op": "and",
                    "content": [
                        {
                            "op": "=",
                            "content": {
                                "field": "cases.project.project_id",
                                "value": [self.PROJECT_ID],
                            },
                        }
                    ],
                },
                "size": 100,
            }

            response = self.session.post(files_endpoint, json=params)
            response.raise_for_status()

            data = response.json()
            datasets = []

            for file_info in data.get("data", {}).get("hits", []):
                datasets.append(
                    {
                        "dataset_id": file_info.get("file_id"),
                        "file_name": file_info.get("file_name"),
                        "data_type": file_info.get("data_type"),
                        "data_format": file_info.get("data_format"),
                        "file_size": file_info.get("file_size"),
                        "cases": file_info.get("cases", []),
                    }
                )

            return datasets

        except Exception as e:
            print(f"Error discovering TCGA datasets: {str(e)}")
            return []

    def download_dataset(self, dataset_id: str, output_path: str) -> bool:
        """Download a TCGA dataset"""
        try:
            download_endpoint = f"{self.BASE_URL}/data/{dataset_id}"
            response = self.session.get(download_endpoint, stream=True)
            response.raise_for_status()

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return True

        except Exception as e:
            print(f"Error downloading TCGA dataset {dataset_id}: {str(e)}")
            return False

    def get_clinical_data(self) -> pd.DataFrame:
        """Get clinical data for TCGA-ESCA"""
        try:
            # Query for clinical data
            files_endpoint = f"{self.BASE_URL}/files"
            params = {
                "filters": {
                    "op": "and",
                    "content": [
                        {
                            "op": "=",
                            "content": {
                                "field": "cases.project.project_id",
                                "value": [self.PROJECT_ID],
                            },
                        },
                        {
                            "op": "=",
                            "content": {
                                "field": "data_type",
                                "value": ["Clinical Supplement"],
                            },
                        },
                    ],
                },
                "size": 1,
            }

            response = self.session.post(files_endpoint, json=params)
            response.raise_for_status()

            data = response.json()
            files = data.get("data", {}).get("hits", [])

            if not files:
                return pd.DataFrame()

            file_id = files[0].get("file_id")
            download_url = f"{self.BASE_URL}/data/{file_id}"

            # Download and parse
            response = self.session.get(download_url)
            response.raise_for_status()

            # Parse TSV data
            df = pd.read_csv(
                response.text.split("\n"), sep="\t", skiprows=1, low_memory=False
            )

            return df

        except Exception as e:
            print(f"Error getting TCGA clinical data: {str(e)}")
            return pd.DataFrame()

    def validate_data(self, data: pd.DataFrame) -> Dict:
        """Validate TCGA data"""
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

        # Check for required columns
        required_columns = ["case_id", "submitter_id"]
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            validation_result["warnings"].append(
                f"Missing columns: {', '.join(missing_columns)}"
            )

        # Check for missing values
        missing_percentage = (data.isnull().sum().sum() / data.size) * 100
        if missing_percentage > 50:
            validation_result["warnings"].append(
                f"High percentage of missing values: {missing_percentage:.2f}%"
            )

        return validation_result

