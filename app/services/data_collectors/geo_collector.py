"""
GEO (Gene Expression Omnibus) data collector
"""
import requests
import pandas as pd
from typing import Dict, List, Optional
import time
from app.services.data_collectors.base_collector import BaseDataCollector


class GEOCollector(BaseDataCollector):
    """Collector for GEO data via NCBI API"""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    DATABASE = "gds"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.session = requests.Session()

    def discover_datasets(self, query: str = "esophageal cancer") -> List[Dict]:
        """Discover GEO datasets"""
        try:
            # Search GEO
            search_url = f"{self.BASE_URL}/esearch.fcgi"
            params = {
                "db": self.DATABASE,
                "term": query,
                "retmax": 100,
                "retmode": "json",
            }

            if self.api_key:
                params["api_key"] = self.api_key

            response = self.session.get(search_url, params=params)
            response.raise_for_status()

            data = response.json()
            id_list = data.get("esearchresult", {}).get("idlist", [])

            # Get summary for each dataset
            summary_url = f"{self.BASE_URL}/esummary.fcgi"
            datasets = []

            # Process in batches
            for i in range(0, len(id_list), 20):
                batch_ids = id_list[i : i + 20]
                params = {
                    "db": self.DATABASE,
                    "id": ",".join(batch_ids),
                    "retmode": "json",
                }

                if self.api_key:
                    params["api_key"] = self.api_key

                response = self.session.get(summary_url, params=params)
                response.raise_for_status()

                summary_data = response.json()
                result = summary_data.get("result", {})

                for dataset_id, dataset_info in result.items():
                    if dataset_id == "uids":
                        continue

                    datasets.append(
                        {
                            "dataset_id": dataset_id,
                            "title": dataset_info.get("title", ""),
                            "summary": dataset_info.get("summary", ""),
                            "organism": dataset_info.get("taxon", ""),
                            "platform": dataset_info.get("platform", ""),
                            "samples": dataset_info.get("samples", []),
                        }
                    )

                # Rate limiting
                time.sleep(0.34)  # NCBI allows 3 requests per second

            return datasets

        except Exception as e:
            print(f"Error discovering GEO datasets: {str(e)}")
            return []

    def download_dataset(self, dataset_id: str, output_path: str) -> bool:
        """Download a GEO dataset"""
        try:
            # Get dataset details
            fetch_url = f"{self.BASE_URL}/efetch.fcgi"
            params = {
                "db": self.DATABASE,
                "id": dataset_id,
                "retmode": "text",
            }

            if self.api_key:
                params["api_key"] = self.api_key

            response = self.session.get(fetch_url, params=params)
            response.raise_for_status()

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(response.text)

            return True

        except Exception as e:
            print(f"Error downloading GEO dataset {dataset_id}: {str(e)}")
            return False

    def validate_data(self, data: pd.DataFrame) -> Dict:
        """Validate GEO data"""
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

