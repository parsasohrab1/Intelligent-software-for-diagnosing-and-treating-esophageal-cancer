"""
Script to generate synthetic data from command line
"""
import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.synthetic_data_generator import EsophagealCancerSyntheticData
from app.services.data_validator import DataValidator


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic esophageal cancer data")
    parser.add_argument(
        "--patients",
        type=int,
        default=1000,
        help="Number of patients to generate (default: 1000)",
    )
    parser.add_argument(
        "--cancer-ratio",
        type=float,
        default=0.3,
        help="Ratio of cancer patients (default: 0.3)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="synthetic_data",
        help="Output directory for CSV files (default: synthetic_data)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate generated data",
    )
    parser.add_argument(
        "--save-db",
        action="store_true",
        help="Save data to database",
    )

    args = parser.parse_args()

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Initialize generator
    print(f"Initializing synthetic data generator (seed={args.seed})...")
    generator = EsophagealCancerSyntheticData(seed=args.seed)

    # Generate data
    print(f"\nGenerating {args.patients} patients (cancer ratio: {args.cancer_ratio})...")
    dataset = generator.generate_all_data(
        n_patients=args.patients, cancer_ratio=args.cancer_ratio
    )

    # Save to CSV files
    print(f"\nSaving data to {args.output_dir}/...")
    for name, df in dataset.items():
        filepath = os.path.join(args.output_dir, f"{name}.csv")
        df.to_csv(filepath, index=False)
        print(f"  ✅ {name}.csv ({len(df)} rows)")

    # Validate if requested
    if args.validate:
        print("\nValidating generated data...")
        validator = DataValidator()
        validation_report = validator.validate_dataset(dataset)
        quality_score = validator.calculate_quality_score(validation_report)

        print(f"\nValidation Results:")
        print(f"  Status: {validation_report['overall_status']}")
        print(f"  Quality Score: {quality_score:.2f}/100")

        if validation_report["errors"]:
            print(f"\n  Errors ({len(validation_report['errors'])}):")
            for error in validation_report["errors"]:
                print(f"    - {error}")

        if validation_report["warnings"]:
            print(f"\n  Warnings ({len(validation_report['warnings'])}):")
            for warning in validation_report["warnings"]:
                print(f"    - {warning}")

    # Save to database if requested
    if args.save_db:
        print("\nSaving to database...")
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            generator.save_to_database(dataset, db)
            print("  ✅ Data saved to database")
        except Exception as e:
            print(f"  ❌ Error saving to database: {str(e)}")
        finally:
            db.close()

    print("\n✅ Synthetic data generation complete!")
    print(f"📁 Data saved in: {args.output_dir}/")


if __name__ == "__main__":
    main()

