"""
Data validation module for synthetic data quality assurance
"""
from typing import Dict, List
import pandas as pd
from datetime import datetime
from scipy import stats


class DataValidator:
    """Validate synthetic data against real-world statistics"""

    def __init__(self):
        self.validation_criteria = {
            "demographic": {
                "age_range": (30, 90),
                "gender_ratio_range": (0.6, 0.8),  # Male ratio in cancer
                "cancer_type_distribution": {
                    "adenocarcinoma": (0.80, 0.90),
                    "squamous_cell_carcinoma": (0.10, 0.15),
                    "neuroendocrine_carcinoma": (0.01, 0.03),
                    "gastrointestinal_stromal_tumor": (0.00, 0.02),
                },
            },
            "clinical": {
                "tumor_size_range": (1.0, 10.0),  # cm
                "stage_distribution": {
                    "I": (0.10, 0.20),
                    "II": (0.25, 0.35),
                    "III": (0.35, 0.45),
                    "IV": (0.15, 0.25),
                },
            },
            "genomic": {
                "tp53_mutation_rate": (0.70, 0.90),
                "her2_amplification_rate": (0.15, 0.25),
                "msi_high_rate": (0.10, 0.20),
            },
        }

    def validate_dataset(self, dataset: Dict[str, pd.DataFrame]) -> Dict:
        """Comprehensive dataset validation"""
        validation_report = {
            "overall_status": "PASS",
            "validation_date": datetime.now().isoformat(),
            "detailed_results": {},
            "warnings": [],
            "errors": [],
        }

        # Validate demographics
        demo_validation = self.validate_demographics(dataset["patients"])
        validation_report["detailed_results"]["demographics"] = demo_validation

        if not demo_validation["pass"]:
            validation_report["overall_status"] = "FAIL"
            validation_report["errors"].extend(demo_validation["errors"])

        # Validate clinical data
        if "clinical" in dataset:
            clinical_validation = self.validate_clinical_data(dataset["clinical"])
            validation_report["detailed_results"]["clinical"] = clinical_validation

            if not clinical_validation["pass"]:
                validation_report["overall_status"] = "FAIL"
                validation_report["errors"].extend(clinical_validation["errors"])

        # Validate genomic data
        if "genomic" in dataset:
            genomic_validation = self.validate_genomic_data(dataset["genomic"])
            validation_report["detailed_results"]["genomic"] = genomic_validation

            if not genomic_validation["pass"]:
                validation_report["overall_status"] = "FAIL"
                validation_report["errors"].extend(genomic_validation["errors"])

        return validation_report

    def validate_demographics(self, patients_df: pd.DataFrame) -> Dict:
        """Validate demographic data"""
        results = {"pass": True, "errors": [], "warnings": []}

        cancer_patients = patients_df[patients_df["has_cancer"]]
        normal_patients = patients_df[~patients_df["has_cancer"]]

        if len(cancer_patients) == 0:
            results["errors"].append("No cancer patients found in dataset")
            results["pass"] = False
            return results

        # Validate cancer patient age
        if cancer_patients["age"].min() < 40 or cancer_patients["age"].max() > 90:
            results["errors"].append("Cancer patient age outside valid range (40-90)")
            results["pass"] = False

        # Validate gender ratio
        male_ratio = len(cancer_patients[cancer_patients["gender"] == "Male"]) / len(
            cancer_patients
        )
        expected_range = self.validation_criteria["demographic"]["gender_ratio_range"]
        if not (expected_range[0] <= male_ratio <= expected_range[1]):
            results["warnings"].append(
                f"Male ratio {male_ratio:.2f} outside expected range "
                f"({expected_range[0]}-{expected_range[1]})"
            )

        # Validate cancer type distribution
        cancer_dist = cancer_patients["cancer_type"].value_counts(normalize=True)
        for (
            cancer_type,
            expected_range,
        ) in self.validation_criteria["demographic"]["cancer_type_distribution"].items():
            if cancer_type in cancer_dist:
                actual = cancer_dist[cancer_type]
                if not (expected_range[0] <= actual <= expected_range[1]):
                    results["errors"].append(
                        f"{cancer_type} prevalence {actual:.3f} outside range {expected_range}"
                    )
                    results["pass"] = False

        return results

    def validate_clinical_data(self, clinical_df: pd.DataFrame) -> Dict:
        """Validate clinical data"""
        results = {"pass": True, "errors": [], "warnings": []}

        # Check tumor size range for cancer patients
        cancer_clinical = clinical_df[clinical_df["tumor_length_cm"] > 0]
        if len(cancer_clinical) > 0:
            tumor_sizes = cancer_clinical["tumor_length_cm"]
            expected_range = self.validation_criteria["clinical"]["tumor_size_range"]
            if tumor_sizes.min() < expected_range[0] or tumor_sizes.max() > expected_range[1]:
                results["warnings"].append(
                    f"Tumor size outside expected range {expected_range}"
                )

        return results

    def validate_genomic_data(self, genomic_df: pd.DataFrame) -> Dict:
        """Validate genomic data"""
        results = {"pass": True, "errors": [], "warnings": []}

        if len(genomic_df) == 0:
            results["warnings"].append("No genomic data found")
            return results

        # Check TP53 mutation rate
        import json

        tp53_mutations = 0
        total_patients = len(genomic_df)

        for _, row in genomic_df.iterrows():
            mutations = json.loads(row.get("mutations", "[]"))
            if any(m.get("gene") == "TP53" for m in mutations):
                tp53_mutations += 1

        if total_patients > 0:
            tp53_rate = tp53_mutations / total_patients
            expected_range = self.validation_criteria["genomic"]["tp53_mutation_rate"]
            if not (expected_range[0] <= tp53_rate <= expected_range[1]):
                results["warnings"].append(
                    f"TP53 mutation rate {tp53_rate:.2f} outside expected range {expected_range}"
                )

        return results

    def calculate_quality_score(self, validation_report: Dict) -> float:
        """Calculate overall quality score (0-100)"""
        total_checks = 0
        passed_checks = 0

        for category, results in validation_report["detailed_results"].items():
            if isinstance(results, dict):
                if "pass" in results:
                    total_checks += 1
                    if results["pass"]:
                        passed_checks += 1

        if total_checks == 0:
            return 0.0

        return (passed_checks / total_checks) * 100

