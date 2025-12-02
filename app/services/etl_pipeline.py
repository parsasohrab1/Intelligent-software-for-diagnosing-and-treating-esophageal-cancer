"""
ETL Pipeline for data collection and processing
"""
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import os
import json
from pathlib import Path

from app.services.data_collectors.tcga_collector import TCGACollector
from app.services.data_collectors.geo_collector import GEOCollector
from app.services.data_collectors.kaggle_collector import KaggleCollector
from app.services.data_deidentifier import DataDeidentifier
from app.core.config import settings


class ETLPipeline:
    """ETL Pipeline for real-world data collection"""

    def __init__(
        self,
        tcga_api_key: Optional[str] = None,
        geo_api_key: Optional[str] = None,
        kaggle_username: Optional[str] = None,
        kaggle_key: Optional[str] = None,
    ):
        self.tcga_collector = TCGACollector(api_key=tcga_api_key)
        self.geo_collector = GEOCollector(api_key=geo_api_key)
        self.kaggle_collector = KaggleCollector(
            api_key=kaggle_key, username=kaggle_username
        )
        self.deidentifier = DataDeidentifier()

        # Setup output directory
        self.output_dir = Path("collected_data")
        self.output_dir.mkdir(exist_ok=True)

    def extract(self, source: str, query: str = "esophageal cancer") -> List[Dict]:
        """Extract data from source"""
        print(f"Extracting data from {source}...")

        if source.lower() == "tcga":
            datasets = self.tcga_collector.discover_datasets(query)
        elif source.lower() == "geo":
            datasets = self.geo_collector.discover_datasets(query)
        elif source.lower() == "kaggle":
            datasets = self.kaggle_collector.discover_datasets(query)
        else:
            raise ValueError(f"Unknown source: {source}")

        print(f"Found {len(datasets)} datasets from {source}")
        return datasets

    def transform(
        self, data: pd.DataFrame, source: str, dataset_id: str
    ) -> pd.DataFrame:
        """Transform data to unified format"""
        print(f"Transforming data from {source} (dataset: {dataset_id})...")

        # De-identify data
        deidentified_data = self.deidentifier.deidentify_dataframe(data)

        # Standardize column names
        deidentified_data.columns = deidentified_data.columns.str.lower().str.replace(
            " ", "_"
        )

        # Add metadata columns
        deidentified_data["source"] = source
        deidentified_data["dataset_id"] = dataset_id
        deidentified_data["collection_date"] = datetime.now().isoformat()

        return deidentified_data

    def load(
        self, data: pd.DataFrame, source: str, dataset_id: str, format: str = "csv"
    ) -> str:
        """Load data to storage"""
        print(f"Loading data from {source} (dataset: {dataset_id})...")

        # Create source directory
        source_dir = self.output_dir / source.lower()
        source_dir.mkdir(exist_ok=True)

        # Save data
        if format == "csv":
            output_path = source_dir / f"{dataset_id}.csv"
            data.to_csv(output_path, index=False)
        elif format == "parquet":
            output_path = source_dir / f"{dataset_id}.parquet"
            data.to_parquet(output_path, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

        print(f"Data saved to {output_path}")
        return str(output_path)

    def run_pipeline(
        self,
        source: str,
        query: str = "esophageal cancer",
        dataset_ids: Optional[List[str]] = None,
        auto_download: bool = False,
    ) -> Dict:
        """Run complete ETL pipeline"""
        print(f"\n{'='*50}")
        print(f"Running ETL Pipeline for {source}")
        print(f"{'='*50}\n")

        pipeline_result = {
            "source": source,
            "query": query,
            "start_time": datetime.now().isoformat(),
            "datasets_discovered": 0,
            "datasets_processed": 0,
            "datasets_failed": 0,
            "errors": [],
            "output_files": [],
        }

        try:
            # Extract
            datasets = self.extract(source, query)
            pipeline_result["datasets_discovered"] = len(datasets)

            if not datasets:
                print(f"No datasets found for {source}")
                return pipeline_result

            # Process datasets
            if dataset_ids:
                datasets = [d for d in datasets if d.get("dataset_id") in dataset_ids]

            for dataset in datasets:
                dataset_id = dataset.get("dataset_id")
                print(f"\nProcessing dataset: {dataset_id}")

                try:
                    # Download if auto_download is enabled
                    if auto_download:
                        temp_path = self.output_dir / f"temp_{dataset_id}"
                        temp_path.mkdir(exist_ok=True)

                        if source.lower() == "tcga":
                            success = self.tcga_collector.download_dataset(
                                dataset_id, str(temp_path / f"{dataset_id}.tsv")
                            )
                        elif source.lower() == "geo":
                            success = self.geo_collector.download_dataset(
                                dataset_id, str(temp_path / f"{dataset_id}.txt")
                            )
                        elif source.lower() == "kaggle":
                            success = self.kaggle_collector.download_dataset(
                                dataset_id, str(temp_path)
                            )

                        if success:
                            # Load and transform
                            # This would need to be adapted based on actual file format
                            print(f"Dataset {dataset_id} downloaded successfully")
                            pipeline_result["datasets_processed"] += 1
                        else:
                            pipeline_result["datasets_failed"] += 1
                            pipeline_result["errors"].append(
                                f"Failed to download {dataset_id}"
                            )
                    else:
                        # Just save metadata
                        metadata_path = self.output_dir / source.lower() / f"{dataset_id}_metadata.json"
                        metadata_path.parent.mkdir(exist_ok=True)
                        with open(metadata_path, "w") as f:
                            json.dump(dataset, f, indent=2, default=str)
                        pipeline_result["output_files"].append(str(metadata_path))

                except Exception as e:
                    print(f"Error processing dataset {dataset_id}: {str(e)}")
                    pipeline_result["datasets_failed"] += 1
                    pipeline_result["errors"].append(f"{dataset_id}: {str(e)}")

        except Exception as e:
            print(f"Error in ETL pipeline: {str(e)}")
            pipeline_result["errors"].append(str(e))

        pipeline_result["end_time"] = datetime.now().isoformat()
        print(f"\n{'='*50}")
        print(f"ETL Pipeline completed for {source}")
        print(f"Discovered: {pipeline_result['datasets_discovered']}")
        print(f"Processed: {pipeline_result['datasets_processed']}")
        print(f"Failed: {pipeline_result['datasets_failed']}")
        print(f"{'='*50}\n")

        return pipeline_result

