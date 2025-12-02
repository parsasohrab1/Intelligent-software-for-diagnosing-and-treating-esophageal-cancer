"""
Feature engineering for multi-modal data
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
from sklearn.preprocessing import StandardScaler, LabelEncoder, MinMaxScaler
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif


class FeatureEngineer:
    """Feature engineering from multi-modal data"""

    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = []

    def extract_features_from_patients(
        self, patients_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Extract features from patient demographics"""
        features = pd.DataFrame()

        # Basic demographics
        features["age"] = patients_df["age"]
        features["age_squared"] = patients_df["age"] ** 2
        features["is_male"] = (patients_df["gender"] == "Male").astype(int)

        # Encode ethnicity
        if "ethnicity" in patients_df.columns:
            le = LabelEncoder()
            features["ethnicity_encoded"] = le.fit_transform(
                patients_df["ethnicity"].fillna("Unknown")
            )
            self.label_encoders["ethnicity"] = le

        # Cancer status
        features["has_cancer"] = patients_df["has_cancer"].astype(int)

        # Cancer type encoding
        if "cancer_type" in patients_df.columns:
            le = LabelEncoder()
            features["cancer_type_encoded"] = le.fit_transform(
                patients_df["cancer_type"].fillna("None")
            )
            self.label_encoders["cancer_type"] = le

        return features

    def extract_features_from_clinical(
        self, clinical_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Extract features from clinical data"""
        features = pd.DataFrame()

        # Vital signs
        if "systolic_bp" in clinical_df.columns:
            features["systolic_bp"] = clinical_df["systolic_bp"]
        if "diastolic_bp" in clinical_df.columns:
            features["diastolic_bp"] = clinical_df["diastolic_bp"]
        if "bmi" in clinical_df.columns:
            features["bmi"] = clinical_df["bmi"]
            features["bmi_category"] = pd.cut(
                clinical_df["bmi"],
                bins=[0, 18.5, 25, 30, 100],
                labels=[0, 1, 2, 3],
            ).astype(float)

        # Tumor characteristics
        if "tumor_length_cm" in clinical_df.columns:
            features["tumor_length"] = clinical_df["tumor_length_cm"]
        if "t_stage" in clinical_df.columns:
            features["t_stage_numeric"] = clinical_df["t_stage"].str.extract(
                r"(\d+)"
            )[0].astype(float)
        if "n_stage" in clinical_df.columns:
            features["n_stage_numeric"] = clinical_df["n_stage"].str.extract(
                r"(\d+)"
            )[0].astype(float)
        if "m_stage" in clinical_df.columns:
            features["m_stage_numeric"] = (clinical_df["m_stage"] == "M1").astype(int)

        # Symptoms and risk factors (from JSON)
        if "symptoms" in clinical_df.columns:
            symptoms_features = self._extract_json_features(
                clinical_df["symptoms"], prefix="symptom"
            )
            features = pd.concat([features, symptoms_features], axis=1)

        if "risk_factors" in clinical_df.columns:
            risk_features = self._extract_json_features(
                clinical_df["risk_factors"], prefix="risk"
            )
            features = pd.concat([features, risk_features], axis=1)

        return features

    def extract_features_from_genomic(
        self, genomic_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Extract features from genomic data"""
        features = pd.DataFrame()

        # Mutation features
        if "mutations" in genomic_df.columns:
            mutations_features = self._extract_mutation_features(genomic_df["mutations"])
            features = pd.concat([features, mutations_features], axis=1)

        # Copy number variations
        if "copy_number_variations" in genomic_df.columns:
            cnv_features = self._extract_cnv_features(
                genomic_df["copy_number_variations"]
            )
            features = pd.concat([features, cnv_features], axis=1)

        # Gene expression
        if "gene_expression" in genomic_df.columns:
            expression_features = self._extract_expression_features(
                genomic_df["gene_expression"]
            )
            features = pd.concat([features, expression_features], axis=1)

        # PD-L1 status
        if "pdl1_status" in genomic_df.columns:
            features["pdl1_positive"] = (genomic_df["pdl1_status"] == "Positive").astype(
                int
            )
        if "pdl1_percentage" in genomic_df.columns:
            features["pdl1_percentage"] = genomic_df["pdl1_percentage"]

        # MSI status
        if "msi_status" in genomic_df.columns:
            features["msi_high"] = (genomic_df["msi_status"] == "MSI-H").astype(int)

        return features

    def extract_features_from_lab(self, lab_df: pd.DataFrame) -> pd.DataFrame:
        """Extract features from lab results"""
        features = pd.DataFrame()

        # Aggregate lab results by patient
        numeric_cols = [
            "hemoglobin",
            "wbc_count",
            "platelet_count",
            "creatinine",
            "cea",
            "ca19_9",
            "crp",
            "albumin",
        ]

        for col in numeric_cols:
            if col in lab_df.columns:
                patient_labs = lab_df.groupby("patient_id")[col].agg(
                    ["mean", "std", "min", "max", "last"]
                )
                for stat in ["mean", "std", "min", "max", "last"]:
                    features[f"{col}_{stat}"] = patient_labs[stat]

        return features

    def _extract_json_features(
        self, json_series: pd.Series, prefix: str
    ) -> pd.DataFrame:
        """Extract features from JSON columns"""
        features = pd.DataFrame()

        for idx, json_str in json_series.items():
            try:
                data = json.loads(json_str) if isinstance(json_str, str) else json_str
                if isinstance(data, dict):
                    for key, value in data.items():
                        feature_name = f"{prefix}_{key}"
                        if feature_name not in features.columns:
                            features[feature_name] = 0
                        features.loc[idx, feature_name] = int(value) if isinstance(value, bool) else value
            except:
                pass

        return features.fillna(0)

    def _extract_mutation_features(
        self, mutations_series: pd.Series
    ) -> pd.DataFrame:
        """Extract features from mutations JSON"""
        features = pd.DataFrame()

        # Common cancer genes
        important_genes = ["TP53", "CDKN2A", "SMAD4", "ARID1A", "ERBB2", "PIK3CA"]

        for gene in important_genes:
            features[f"mutated_{gene}"] = 0

        features["total_mutations"] = 0
        features["missense_mutations"] = 0
        features["nonsense_mutations"] = 0

        for idx, mut_json in mutations_series.items():
            try:
                mutations = json.loads(mut_json) if isinstance(mut_json, str) else mut_json
                if isinstance(mutations, list):
                    features.loc[idx, "total_mutations"] = len(mutations)
                    for mut in mutations:
                        gene = mut.get("gene", "")
                        if gene in important_genes:
                            features.loc[idx, f"mutated_{gene}"] = 1
                        mut_type = mut.get("mutation_type", "")
                        if mut_type == "Missense":
                            features.loc[idx, "missense_mutations"] += 1
                        elif mut_type == "Nonsense":
                            features.loc[idx, "nonsense_mutations"] += 1
            except:
                pass

        return features.fillna(0)

    def _extract_cnv_features(self, cnv_series: pd.Series) -> pd.DataFrame:
        """Extract features from CNV JSON"""
        features = pd.DataFrame()

        important_genes = ["EGFR", "MYC", "CCND1", "CDK4", "MDM2"]

        for gene in important_genes:
            features[f"cnv_{gene}_amplified"] = 0
            features[f"cnv_{gene}_deleted"] = 0

        for idx, cnv_json in cnv_series.items():
            try:
                cnvs = json.loads(cnv_json) if isinstance(cnv_json, str) else cnv_json
                if isinstance(cnvs, list):
                    for cnv in cnvs:
                        gene = cnv.get("gene", "")
                        cnv_type = cnv.get("type", "")
                        if gene in important_genes:
                            if cnv_type == "Amplification":
                                features.loc[idx, f"cnv_{gene}_amplified"] = 1
                            elif cnv_type == "Deletion":
                                features.loc[idx, f"cnv_{gene}_deleted"] = 1
            except:
                pass

        return features.fillna(0)

    def _extract_expression_features(
        self, expression_series: pd.Series
    ) -> pd.DataFrame:
        """Extract features from gene expression JSON"""
        features = pd.DataFrame()

        important_genes = ["TP53", "EGFR", "HER2", "VEGFA", "PDL1"]

        for gene in important_genes:
            features[f"expression_{gene}"] = 0.0

        features["msi_status_encoded"] = 0

        for idx, expr_json in expression_series.items():
            try:
                expression = (
                    json.loads(expr_json) if isinstance(expr_json, str) else expr_json
                )
                if isinstance(expression, dict):
                    for gene in important_genes:
                        if gene in expression:
                            features.loc[idx, f"expression_{gene}"] = expression[gene]
                    if "MSI_status" in expression:
                        msi = expression["MSI_status"]
                        features.loc[idx, "msi_status_encoded"] = (
                            1 if msi == "MSI-H" else 0
                        )
            except:
                pass

        return features.fillna(0)

    def combine_features(
        self,
        patient_features: pd.DataFrame,
        clinical_features: pd.DataFrame,
        genomic_features: Optional[pd.DataFrame] = None,
        lab_features: Optional[pd.DataFrame] = None,
        join_key: str = "patient_id",
    ) -> pd.DataFrame:
        """Combine features from multiple sources"""
        # Start with patient features
        combined = patient_features.copy()

        # Merge clinical features
        if not clinical_features.empty:
            combined = combined.merge(
                clinical_features, left_index=True, right_index=True, how="left"
            )

        # Merge genomic features
        if genomic_features is not None and not genomic_features.empty:
            combined = combined.merge(
                genomic_features, left_index=True, right_index=True, how="left"
            )

        # Merge lab features
        if lab_features is not None and not lab_features.empty:
            combined = combined.merge(
                lab_features, left_index=True, right_index=True, how="left"
            )

        # Fill missing values
        combined = combined.fillna(0)

        return combined

    def normalize_features(
        self, features: pd.DataFrame, method: str = "standard"
    ) -> pd.DataFrame:
        """Normalize features"""
        if method == "standard":
            scaler = StandardScaler()
        elif method == "minmax":
            scaler = MinMaxScaler()
        else:
            raise ValueError(f"Unknown normalization method: {method}")

        numeric_cols = features.select_dtypes(include=[np.number]).columns
        features_normalized = features.copy()
        features_normalized[numeric_cols] = scaler.fit_transform(
            features[numeric_cols]
        )

        self.scaler = scaler
        return features_normalized

    def select_features(
        self,
        features: pd.DataFrame,
        target: pd.Series,
        k: int = 50,
        method: str = "f_classif",
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Select top k features"""
        if method == "f_classif":
            selector = SelectKBest(score_func=f_classif, k=k)
        elif method == "mutual_info":
            selector = SelectKBest(score_func=mutual_info_classif, k=k)
        else:
            raise ValueError(f"Unknown selection method: {method}")

        numeric_cols = features.select_dtypes(include=[np.number]).columns
        X = features[numeric_cols].fillna(0)

        selector.fit(X, target)
        selected_cols = numeric_cols[selector.get_support()].tolist()

        return features[selected_cols], selected_cols

