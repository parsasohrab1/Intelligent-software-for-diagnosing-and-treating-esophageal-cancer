"""
Script to integrate synthetic and real data
"""
import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from app.services.data_integration.hybrid_integrator import HybridDataIntegrator
from app.services.feature_engineering import FeatureEngineer
from app.services.data_augmentation import DataAugmenter


def main():
    parser = argparse.ArgumentParser(description="Integrate synthetic and real data")
    parser.add_argument(
        "--synthetic",
        type=str,
        required=True,
        help="Path to synthetic data CSV",
    )
    parser.add_argument(
        "--real",
        type=str,
        required=True,
        help="Path to real data CSV",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="integrated_data.csv",
        help="Output file path",
    )
    parser.add_argument(
        "--fusion-method",
        type=str,
        default="concatenate",
        choices=["concatenate", "weighted", "matched"],
        help="Fusion method",
    )
    parser.add_argument(
        "--engineer-features",
        action="store_true",
        help="Engineer features from integrated data",
    )
    parser.add_argument(
        "--augment",
        action="store_true",
        help="Augment data with synthetic samples",
    )

    args = parser.parse_args()

    # Load data
    print("Loading data...")
    synthetic_data = pd.read_csv(args.synthetic)
    real_data = pd.read_csv(args.real)

    print(f"Synthetic data: {len(synthetic_data)} samples")
    print(f"Real data: {len(real_data)} samples")

    # Integrate
    print("\nIntegrating data...")
    integrator = HybridDataIntegrator()

    # Statistical matching
    key_columns = ["age", "gender"]
    if "has_cancer" in synthetic_data.columns:
        key_columns.append("has_cancer")

    matching_scores = integrator.statistical_matching(
        synthetic_data, real_data, key_columns
    )
    print(f"Matching scores: {matching_scores}")

    # Fuse datasets
    fused_data = integrator.fuse_datasets(
        synthetic_data, real_data, fusion_method=args.fusion_method
    )
    print(f"Fused data: {len(fused_data)} samples")

    # Feature engineering
    if args.engineer_features:
        print("\nEngineering features...")
        engineer = FeatureEngineer()

        patient_features = engineer.extract_features_from_patients(fused_data)
        clinical_features = engineer.extract_features_from_clinical(fused_data)

        combined_features = engineer.combine_features(
            patient_features, clinical_features
        )
        combined_features = engineer.normalize_features(combined_features)

        print(f"Engineered {len(combined_features.columns)} features")
        fused_data = combined_features

    # Augmentation
    if args.augment and "has_cancer" in fused_data.columns:
        print("\nAugmenting data...")
        augmenter = DataAugmenter()
        augmented_data = augmenter.augment_with_synthetic(
            real_data, synthetic_data, "has_cancer", augmentation_ratio=0.5
        )
        print(f"Augmented data: {len(augmented_data)} samples")
        fused_data = augmented_data

    # Save
    print(f"\nSaving to {args.output}...")
    fused_data.to_csv(args.output, index=False)
    print("✅ Integration complete!")


if __name__ == "__main__":
    main()

