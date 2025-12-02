"""
Hybrid data integration - combining synthetic and real data
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy import stats
from sklearn.preprocessing import StandardScaler
import json


class HybridDataIntegrator:
    """Integrate synthetic and real-world data"""

    def __init__(self):
        self.scaler = StandardScaler()

    def statistical_matching(
        self, synthetic_data: pd.DataFrame, real_data: pd.DataFrame, key_columns: List[str]
    ) -> Dict[str, float]:
        """Calculate statistical matching between synthetic and real data"""
        matching_scores = {}

        for col in key_columns:
            if col not in synthetic_data.columns or col not in real_data.columns:
                continue

            # Remove NaN values
            synth_vals = synthetic_data[col].dropna()
            real_vals = real_data[col].dropna()

            if len(synth_vals) == 0 or len(real_vals) == 0:
                continue

            # For numeric columns, calculate correlation
            if pd.api.types.is_numeric_dtype(synth_vals):
                # Kolmogorov-Smirnov test
                try:
                    ks_statistic, p_value = stats.ks_2samp(synth_vals, real_vals)
                    matching_scores[f"{col}_ks_pvalue"] = p_value

                    # Correlation
                    if len(synth_vals) == len(real_vals):
                        correlation = np.corrcoef(synth_vals, real_vals)[0, 1]
                        matching_scores[f"{col}_correlation"] = correlation
                    else:
                        # Resample to same length
                        min_len = min(len(synth_vals), len(real_vals))
                        synth_sample = synth_vals.sample(min_len, random_state=42)
                        real_sample = real_vals.sample(min_len, random_state=42)
                        correlation = np.corrcoef(synth_sample, real_sample)[0, 1]
                        matching_scores[f"{col}_correlation"] = correlation

                    # Mean difference
                    mean_diff = abs(synth_vals.mean() - real_vals.mean())
                    mean_ratio = mean_diff / (real_vals.mean() + 1e-10)
                    matching_scores[f"{col}_mean_ratio"] = mean_ratio

                except Exception as e:
                    print(f"Error calculating matching for {col}: {str(e)}")

            # For categorical columns, calculate distribution similarity
            else:
                synth_dist = synth_vals.value_counts(normalize=True)
                real_dist = real_vals.value_counts(normalize=True)

                # Get common categories
                common_cats = set(synth_dist.index) & set(real_dist.index)
                if len(common_cats) > 0:
                    similarity = sum(
                        min(synth_dist.get(cat, 0), real_dist.get(cat, 0))
                        for cat in common_cats
                    )
                    matching_scores[f"{col}_similarity"] = similarity

        return matching_scores

    def fuse_datasets(
        self,
        synthetic_data: pd.DataFrame,
        real_data: pd.DataFrame,
        fusion_method: str = "concatenate",
        matching_threshold: float = 0.8,
    ) -> pd.DataFrame:
        """Fuse synthetic and real datasets"""
        if fusion_method == "concatenate":
            # Simple concatenation
            fused = pd.concat([synthetic_data, real_data], ignore_index=True)
            fused["data_source"] = (
                ["synthetic"] * len(synthetic_data) + ["real"] * len(real_data)
            )
            return fused

        elif fusion_method == "weighted":
            # Weighted combination based on quality
            # This would require quality scores for each dataset
            synthetic_data["data_source"] = "synthetic"
            real_data["data_source"] = "real"
            fused = pd.concat([synthetic_data, real_data], ignore_index=True)
            return fused

        elif fusion_method == "matched":
            # Match synthetic to real data based on key features
            # This is more complex and would require matching algorithm
            return self._match_and_fuse(synthetic_data, real_data, matching_threshold)

        else:
            raise ValueError(f"Unknown fusion method: {fusion_method}")

    def _match_and_fuse(
        self,
        synthetic_data: pd.DataFrame,
        real_data: pd.DataFrame,
        threshold: float,
    ) -> pd.DataFrame:
        """Match and fuse datasets based on similarity"""
        # Simple implementation - can be enhanced
        synthetic_data["data_source"] = "synthetic"
        real_data["data_source"] = "real"
        fused = pd.concat([synthetic_data, real_data], ignore_index=True)
        return fused

    def calculate_quality_metrics(
        self, fused_data: pd.DataFrame
    ) -> Dict[str, float]:
        """Calculate quality metrics for fused dataset"""
        metrics = {
            "total_samples": len(fused_data),
            "synthetic_samples": len(fused_data[fused_data.get("data_source") == "synthetic"]),
            "real_samples": len(fused_data[fused_data.get("data_source") == "real"]),
            "missing_percentage": (fused_data.isnull().sum().sum() / fused_data.size) * 100,
            "duplicate_percentage": (fused_data.duplicated().sum() / len(fused_data)) * 100,
        }

        return metrics

    def detect_bias(self, fused_data: pd.DataFrame, sensitive_columns: List[str]) -> Dict:
        """Detect bias in fused dataset"""
        bias_report = {}

        for col in sensitive_columns:
            if col not in fused_data.columns:
                continue

            # Check distribution across data sources
            if "data_source" in fused_data.columns:
                source_dist = pd.crosstab(fused_data[col], fused_data["data_source"])
                if len(source_dist) > 0:
                    # Calculate chi-square test
                    try:
                        chi2, p_value, dof, expected = stats.chi2_contingency(source_dist)
                        bias_report[col] = {
                            "chi2": chi2,
                            "p_value": p_value,
                            "biased": p_value < 0.05,
                        }
                    except:
                        pass

        return bias_report

    def correct_bias(
        self, fused_data: pd.DataFrame, bias_report: Dict, method: str = "resample"
    ) -> pd.DataFrame:
        """Correct detected bias"""
        if method == "resample":
            # Resample to balance distributions
            corrected_data = fused_data.copy()
            # Implementation would depend on specific bias type
            return corrected_data
        else:
            return fused_data

    def cross_validate(
        self,
        synthetic_data: pd.DataFrame,
        real_data: pd.DataFrame,
        validation_columns: List[str],
    ) -> Dict:
        """Cross-validate between synthetic and real data"""
        validation_results = {}

        for col in validation_columns:
            if col not in synthetic_data.columns or col not in real_data.columns:
                continue

            synth_vals = synthetic_data[col].dropna()
            real_vals = real_data[col].dropna()

            if len(synth_vals) == 0 or len(real_vals) == 0:
                continue

            if pd.api.types.is_numeric_dtype(synth_vals):
                # Statistical tests
                try:
                    # T-test
                    t_stat, t_pvalue = stats.ttest_ind(synth_vals, real_vals)
                    validation_results[f"{col}_ttest_pvalue"] = t_pvalue

                    # Mann-Whitney U test
                    u_stat, u_pvalue = stats.mannwhitneyu(synth_vals, real_vals)
                    validation_results[f"{col}_mannwhitney_pvalue"] = u_pvalue

                except Exception as e:
                    print(f"Error in validation for {col}: {str(e)}")

        return validation_results

