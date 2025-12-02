"""
Script to collect real-world data from external sources
"""
import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.etl_pipeline import ETLPipeline
from app.services.metadata_manager import MetadataManager
from app.core.config import settings


def main():
    parser = argparse.ArgumentParser(description="Collect real-world data from external sources")
    parser.add_argument(
        "--source",
        type=str,
        required=True,
        choices=["tcga", "geo", "kaggle"],
        help="Data source (tcga, geo, or kaggle)",
    )
    parser.add_argument(
        "--query",
        type=str,
        default="esophageal cancer",
        help="Search query (default: esophageal cancer)",
    )
    parser.add_argument(
        "--dataset-ids",
        type=str,
        nargs="+",
        help="Specific dataset IDs to collect",
    )
    parser.add_argument(
        "--auto-download",
        action="store_true",
        help="Automatically download datasets",
    )
    parser.add_argument(
        "--save-metadata",
        action="store_true",
        help="Save metadata to MongoDB",
    )

    args = parser.parse_args()

    # Initialize ETL pipeline
    print(f"Initializing ETL pipeline for {args.source}...")
    pipeline = ETLPipeline(
        tcga_api_key=settings.TCGA_API_KEY if hasattr(settings, "TCGA_API_KEY") else None,
        geo_api_key=settings.GEO_API_KEY if hasattr(settings, "GEO_API_KEY") else None,
        kaggle_username=settings.KAGGLE_USERNAME if hasattr(settings, "KAGGLE_USERNAME") else None,
        kaggle_key=settings.KAGGLE_KEY if hasattr(settings, "KAGGLE_KEY") else None,
    )

    # Run pipeline
    result = pipeline.run_pipeline(
        source=args.source,
        query=args.query,
        dataset_ids=args.dataset_ids,
        auto_download=args.auto_download,
    )

    # Save metadata if requested
    if args.save_metadata:
        print("\nSaving metadata to MongoDB...")
        manager = MetadataManager()

        # This would need to be adapted based on actual dataset structure
        for dataset_id in args.dataset_ids or []:
            metadata = {
                "dataset_id": dataset_id,
                "source": args.source,
                "query": args.query,
                "collection_date": result["start_time"],
            }
            manager.store_metadata(metadata)
            print(f"  ✅ Metadata saved for {dataset_id}")

    print("\n✅ Data collection complete!")
    print(f"📊 Summary:")
    print(f"  Discovered: {result['datasets_discovered']}")
    print(f"  Processed: {result['datasets_processed']}")
    print(f"  Failed: {result['datasets_failed']}")


if __name__ == "__main__":
    main()

