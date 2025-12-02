"""
Data augmentation using synthetic samples
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from imblearn.over_sampling import SMOTE, ADASYN
from imblearn.combine import SMOTETomek, SMOTEENN


class DataAugmenter:
    """Augment real data with synthetic samples"""

    def __init__(self, method: str = "smote"):
        self.method = method
        self.augmenter = None

    def augment_with_synthetic(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        target_column: str,
        augmentation_ratio: float = 0.5,
    ) -> pd.DataFrame:
        """Augment real data with synthetic samples"""
        # Select subset of synthetic data
        n_augment = int(len(real_data) * augmentation_ratio)
        synthetic_subset = synthetic_data.sample(
            n=min(n_augment, len(synthetic_data)), random_state=42
        )

        # Combine
        augmented = pd.concat([real_data, synthetic_subset], ignore_index=True)
        augmented["data_source"] = (
            ["real"] * len(real_data) + ["synthetic"] * len(synthetic_subset)
        )

        return augmented

    def augment_with_smote(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        k_neighbors: int = 5,
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Augment using SMOTE"""
        smote = SMOTE(k_neighbors=k_neighbors, random_state=42)
        X_resampled, y_resampled = smote.fit_resample(X, y)

        X_df = pd.DataFrame(X_resampled, columns=X.columns)
        y_series = pd.Series(y_resampled, name=y.name)

        return X_df, y_series

    def augment_with_adasyn(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        n_neighbors: int = 5,
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Augment using ADASYN"""
        adasyn = ADASYN(n_neighbors=n_neighbors, random_state=42)
        X_resampled, y_resampled = adasyn.fit_resample(X, y)

        X_df = pd.DataFrame(X_resampled, columns=X.columns)
        y_series = pd.Series(y_resampled, name=y.name)

        return X_df, y_series

    def augment_with_combined(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        method: str = "smote_tomek",
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Augment using combined methods"""
        if method == "smote_tomek":
            augmenter = SMOTETomek(random_state=42)
        elif method == "smote_enn":
            augmenter = SMOTEENN(random_state=42)
        else:
            raise ValueError(f"Unknown combined method: {method}")

        X_resampled, y_resampled = augmenter.fit_resample(X, y)

        X_df = pd.DataFrame(X_resampled, columns=X.columns)
        y_series = pd.Series(y_resampled, name=y.name)

        return X_df, y_series

    def validate_augmentation(
        self,
        original_data: pd.DataFrame,
        augmented_data: pd.DataFrame,
        target_column: str,
    ) -> Dict:
        """Validate augmentation effectiveness"""
        validation = {
            "original_size": len(original_data),
            "augmented_size": len(augmented_data),
            "augmentation_ratio": len(augmented_data) / len(original_data),
        }

        # Check class distribution
        if target_column in original_data.columns:
            original_dist = original_data[target_column].value_counts(normalize=True)
            augmented_dist = augmented_data[target_column].value_counts(normalize=True)

            validation["original_distribution"] = original_dist.to_dict()
            validation["augmented_distribution"] = augmented_dist.to_dict()

            # Calculate distribution similarity
            common_classes = set(original_dist.index) & set(augmented_dist.index)
            if len(common_classes) > 0:
                similarity = sum(
                    min(original_dist.get(c, 0), augmented_dist.get(c, 0))
                    for c in common_classes
                )
                validation["distribution_similarity"] = similarity

        return validation

