"""
Comprehensive Synthetic Data Generator for Esophageal Cancer Research
Version: 2.0
Generates synthetic samples with realistic distributions
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
from typing import Dict, List, Optional
import json
import os
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.clinical_data import ClinicalData
from app.models.genomic_data import GenomicData
from app.models.imaging_data import ImagingData
from app.models.treatment_data import TreatmentData
from app.models.lab_results import LabResult
from app.models.quality_of_life import QualityOfLife


class EsophagealCancerSyntheticData:
    """
    Advanced synthetic data generator for esophageal cancer research
    Generates realistic multi-modal data including clinical, genomic, and imaging features
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        np.random.seed(seed)
        random.seed(seed)

        # Cancer type distributions based on real-world epidemiology
        self.cancer_types = {
            "adenocarcinoma": {
                "prevalence": 0.85,
                "median_age": 67,
                "male_ratio": 0.75,
                "smoking_associated": 0.65,
                "obesity_associated": 0.80,
                "subtypes": ["intestinal", "diffuse", "mucinous"],
            },
            "squamous_cell_carcinoma": {
                "prevalence": 0.12,
                "median_age": 70,
                "male_ratio": 0.80,
                "smoking_associated": 0.85,
                "alcohol_associated": 0.70,
                "subtypes": ["keratinizing", "non-keratinizing", "basaloid"],
            },
            "neuroendocrine_carcinoma": {
                "prevalence": 0.02,
                "median_age": 55,
                "male_ratio": 0.60,
                "subtypes": ["small_cell", "large_cell"],
            },
            "gastrointestinal_stromal_tumor": {
                "prevalence": 0.01,
                "median_age": 60,
                "male_ratio": 0.55,
                "subtypes": ["spindle_cell", "epithelioid", "mixed"],
            },
        }

        # Clinical parameters based on literature
        self.clinical_parameters = {
            "symptoms": {
                "dysphagia": {"cancer": 0.85, "normal": 0.02},
                "weight_loss": {"cancer": 0.75, "normal": 0.01},
                "chest_pain": {"cancer": 0.50, "normal": 0.05},
                "heartburn": {"cancer": 0.40, "normal": 0.15},
                "regurgitation": {"cancer": 0.30, "normal": 0.10},
            },
            "risk_factors": {
                "smoking": {"cancer": 0.70, "normal": 0.25},
                "alcohol": {"cancer": 0.60, "normal": 0.20},
                "obesity": {"cancer": 0.65, "normal": 0.30},
                "gerd": {"cancer": 0.80, "normal": 0.10},
                "barretts_esophagus": {"cancer": 0.40, "normal": 0.01},
            },
        }

        # Genomic mutation frequencies from COSMIC database
        self.genomic_mutations = {
            "adenocarcinoma": {
                "TP53": 0.75,
                "CDKN2A": 0.40,
                "SMAD4": 0.30,
                "ARID1A": 0.25,
                "ERBB2": 0.20,
                "PIK3CA": 0.15,
            },
            "squamous_cell_carcinoma": {
                "TP53": 0.90,
                "CDKN2A": 0.50,
                "NOTCH1": 0.30,
                "PIK3CA": 0.25,
                "FBXW7": 0.20,
            },
        }

        # Biomarker ranges
        self.biomarkers = {
            "cea": {"normal": (0, 3), "cancer": (5, 100)},
            "ca19_9": {"normal": (0, 37), "cancer": (40, 500)},
            "crp": {"normal": (0, 5), "cancer": (10, 100)},
            "albumin": {"normal": (3.5, 5.0), "cancer": (2.5, 4.0)},
        }

    def generate_patient_demographics(
        self, n_patients: int = 1000, cancer_ratio: float = 0.3
    ) -> pd.DataFrame:
        """Generate synthetic patient demographics"""
        patients = []

        n_cancer = int(n_patients * cancer_ratio)
        n_normal = n_patients - n_cancer

        # Generate cancer patients
        for i in range(n_cancer):
            # Determine cancer type based on prevalence
            cancer_type = np.random.choice(
                list(self.cancer_types.keys()),
                p=[t["prevalence"] for t in self.cancer_types.values()],
            )

            cancer_info = self.cancer_types[cancer_type]

            # Generate age based on cancer type
            age = int(np.random.normal(cancer_info["median_age"], 8))
            age = max(40, min(age, 90))

            # Generate gender based on cancer type male ratio
            gender = "Male" if random.random() < cancer_info["male_ratio"] else "Female"

            # Generate ethnicity distribution
            ethnicity = np.random.choice(
                ["White", "Asian", "Black", "Hispanic"], p=[0.70, 0.20, 0.05, 0.05]
            )

            patients.append(
                {
                    "patient_id": f"CAN{i+1:04d}",
                    "age": age,
                    "gender": gender,
                    "ethnicity": ethnicity,
                    "has_cancer": True,
                    "cancer_type": cancer_type,
                    "cancer_subtype": random.choice(cancer_info["subtypes"]),
                }
            )

        # Generate normal patients
        for i in range(n_normal):
            age = int(np.random.uniform(30, 80))
            gender = random.choice(["Male", "Female"])
            ethnicity = np.random.choice(
                ["White", "Asian", "Black", "Hispanic"], p=[0.70, 0.20, 0.05, 0.05]
            )

            patients.append(
                {
                    "patient_id": f"CTL{i+1:04d}",
                    "age": age,
                    "gender": gender,
                    "ethnicity": ethnicity,
                    "has_cancer": False,
                    "cancer_type": None,
                    "cancer_subtype": None,
                }
            )

        return pd.DataFrame(patients)

    def generate_clinical_data(self, patients_df: pd.DataFrame) -> pd.DataFrame:
        """Generate clinical symptoms and examination data"""
        clinical_data = []

        for _, patient in patients_df.iterrows():
            clinical_record = {
                "patient_id": patient["patient_id"],
                "height_cm": np.random.normal(170, 10)
                if patient["gender"] == "Male"
                else np.random.normal(160, 8),
                "weight_kg": np.random.normal(80, 15)
                if patient["gender"] == "Male"
                else np.random.normal(65, 12),
                "systolic_bp": np.random.normal(120, 15),
                "diastolic_bp": np.random.normal(80, 10),
                "heart_rate": np.random.normal(75, 10),
                "respiratory_rate": np.random.normal(16, 3),
            }

            # Calculate BMI
            clinical_record["bmi"] = round(
                clinical_record["weight_kg"] / ((clinical_record["height_cm"] / 100) ** 2),
                1,
            )

            # Generate symptoms based on cancer status
            symptoms = {}
            for symptom, probs in self.clinical_parameters["symptoms"].items():
                prob = probs["cancer"] if patient["has_cancer"] else probs["normal"]
                symptoms[symptom] = random.random() < prob

            clinical_record["symptoms"] = json.dumps(symptoms)

            # Generate risk factors
            risk_factors = {}
            for factor, probs in self.clinical_parameters["risk_factors"].items():
                prob = probs["cancer"] if patient["has_cancer"] else probs["normal"]
                risk_factors[factor] = random.random() < prob

            clinical_record["risk_factors"] = json.dumps(risk_factors)

            # Cancer-specific clinical features
            if patient["has_cancer"]:
                clinical_record["tumor_location"] = random.choice(
                    ["Upper esophagus", "Middle esophagus", "Lower esophagus", "GE junction"]
                )

                clinical_record["tumor_length_cm"] = round(np.random.uniform(1.5, 8.0), 1)

                # Generate TNM staging
                clinical_record["t_stage"] = np.random.choice(
                    ["T1", "T2", "T3", "T4"], p=[0.15, 0.25, 0.40, 0.20]
                )
                clinical_record["n_stage"] = np.random.choice(
                    ["N0", "N1", "N2", "N3"], p=[0.30, 0.35, 0.25, 0.10]
                )
                clinical_record["m_stage"] = np.random.choice(["M0", "M1"], p=[0.70, 0.30])

                clinical_record["histological_grade"] = np.random.choice(
                    ["Well differentiated", "Moderately differentiated", "Poorly differentiated"],
                    p=[0.20, 0.50, 0.30],
                )

                clinical_record["lymphovascular_invasion"] = random.random() < 0.40
                clinical_record["perineural_invasion"] = random.random() < 0.25
            else:
                clinical_record.update(
                    {
                        "tumor_location": None,
                        "tumor_length_cm": 0.0,
                        "t_stage": None,
                        "n_stage": None,
                        "m_stage": None,
                        "histological_grade": None,
                        "lymphovascular_invasion": False,
                        "perineural_invasion": False,
                    }
                )

            clinical_data.append(clinical_record)

        return pd.DataFrame(clinical_data)

    def generate_lab_results(self, patients_df: pd.DataFrame) -> pd.DataFrame:
        """Generate laboratory test results"""
        lab_results = []

        test_types = ["CBC", "Chemistry", "Liver_Function", "Coagulation", "Tumor_Markers"]

        for _, patient in patients_df.iterrows():
            for test_type in test_types:
                is_cancer = patient["has_cancer"]

                lab_record = {
                    "patient_id": patient["patient_id"],
                    "test_type": test_type,
                    "test_date": (
                        datetime.now() - timedelta(days=np.random.randint(1, 365))
                    ).strftime("%Y-%m-%d"),
                }

                # Generate test-specific values
                if test_type == "CBC":
                    if is_cancer:
                        lab_record["hemoglobin"] = round(np.random.uniform(8.0, 12.0), 1)
                        lab_record["wbc_count"] = round(np.random.uniform(4.0, 15.0), 1)
                        lab_record["platelet_count"] = round(np.random.uniform(150, 450))
                    else:
                        lab_record["hemoglobin"] = round(np.random.normal(14.0, 1.0), 1)
                        lab_record["wbc_count"] = round(np.random.normal(7.0, 2.0), 1)
                        lab_record["platelet_count"] = round(np.random.normal(250, 50))

                elif test_type == "Chemistry":
                    lab_record["creatinine"] = round(np.random.normal(0.9, 0.2), 2)
                    lab_record["sodium"] = round(np.random.normal(140, 3))
                    lab_record["potassium"] = round(np.random.normal(4.0, 0.3), 1)

                elif test_type == "Liver_Function":
                    if is_cancer:
                        lab_record["ast"] = round(np.random.uniform(30, 100))
                        lab_record["alt"] = round(np.random.uniform(25, 80))
                        lab_record["alkaline_phosphatase"] = round(np.random.uniform(100, 300))
                    else:
                        lab_record["ast"] = round(np.random.normal(25, 5))
                        lab_record["alt"] = round(np.random.normal(22, 4))
                        lab_record["alkaline_phosphatase"] = round(np.random.normal(70, 15))

                elif test_type == "Tumor_Markers":
                    if is_cancer:
                        for marker, ranges in self.biomarkers.items():
                            lab_record[marker] = round(
                                np.random.uniform(ranges["cancer"][0], ranges["cancer"][1]), 1
                            )
                    else:
                        for marker, ranges in self.biomarkers.items():
                            lab_record[marker] = round(
                                np.random.uniform(ranges["normal"][0], ranges["normal"][1]), 1
                            )

                lab_results.append(lab_record)

        return pd.DataFrame(lab_results)

    def generate_genomic_data(self, patients_df: pd.DataFrame) -> pd.DataFrame:
        """Generate synthetic genomic and molecular data"""
        genomic_data = []

        for _, patient in patients_df.iterrows():
            if not patient["has_cancer"]:
                continue

            genomic_record = {
                "patient_id": patient["patient_id"],
                "cancer_type": patient["cancer_type"],
                "sequencing_date": (
                    datetime.now() - timedelta(days=np.random.randint(1, 180))
                ).strftime("%Y-%m-%d"),
                "sequencing_platform": np.random.choice(
                    ["Illumina NovaSeq", "Ion Torrent", "Oxford Nanopore"]
                ),
                "coverage_depth": np.random.randint(50, 200),
            }

            # Generate mutations based on cancer type
            mutations = []
            mutation_info = self.genomic_mutations.get(patient["cancer_type"], {})

            for gene, mutation_freq in mutation_info.items():
                if random.random() < mutation_freq:
                    mutation_type = np.random.choice(
                        ["Missense", "Nonsense", "Frameshift", "Splice_site"],
                        p=[0.60, 0.15, 0.20, 0.05],
                    )

                    mutations.append(
                        {
                            "gene": gene,
                            "mutation_type": mutation_type,
                            "allele_frequency": round(np.random.uniform(0.1, 0.9), 3),
                        }
                    )

            genomic_record["mutations"] = json.dumps(mutations)

            # Generate copy number variations
            cnvs = []
            common_cnv_genes = ["EGFR", "MYC", "CCND1", "CDK4", "MDM2"]
            for gene in common_cnv_genes:
                if random.random() < 0.3:
                    cnv_type = "Amplification" if random.random() < 0.7 else "Deletion"
                    cnvs.append(
                        {
                            "gene": gene,
                            "type": cnv_type,
                            "copy_number": np.random.randint(3, 10)
                            if cnv_type == "Amplification"
                            else 1,
                        }
                    )

            genomic_record["copy_number_variations"] = json.dumps(cnvs)

            # Generate gene expression data
            expression_data = {}
            cancer_genes = ["TP53", "EGFR", "HER2", "VEGFA", "PDL1", "MSI_status"]
            for gene in cancer_genes:
                if gene == "MSI_status":
                    expression_data[gene] = "MSI-H" if random.random() < 0.15 else "MSS"
                else:
                    # Higher expression in cancer patients
                    base_exp = np.random.normal(10, 3)
                    if random.random() < 0.4:  # 40% chance of overexpression
                        base_exp *= np.random.uniform(2, 5)
                    expression_data[gene] = round(base_exp, 2)

            genomic_record["gene_expression"] = json.dumps(expression_data)

            # Generate PD-L1 status
            genomic_record["pdl1_status"] = np.random.choice(
                ["Positive", "Negative"], p=[0.40, 0.60]
            )
            genomic_record["pdl1_percentage"] = round(np.random.uniform(0, 80), 1)

            genomic_data.append(genomic_record)

        return pd.DataFrame(genomic_data)

    def generate_imaging_data(self, patients_df: pd.DataFrame) -> pd.DataFrame:
        """Generate synthetic imaging data reports"""
        imaging_data = []

        imaging_modalities = ["Endoscopy", "CT_Chest_Abdomen", "PET_CT", "EUS", "MRI"]

        for _, patient in patients_df.iterrows():
            for modality in imaging_modalities:
                imaging_record = {
                    "patient_id": patient["patient_id"],
                    "imaging_modality": modality,
                    "imaging_date": (
                        datetime.now() - timedelta(days=np.random.randint(1, 180))
                    ).strftime("%Y-%m-%d"),
                    "contrast_used": random.random() < 0.7,
                    "radiologist_id": f"RAD{np.random.randint(1000, 9999)}",
                }

                if patient["has_cancer"]:
                    # Cancer-specific findings
                    findings = []

                    if modality == "Endoscopy":
                        findings.append("Ulcerated mass with irregular borders")
                        findings.append("Friable mucosa with contact bleeding")
                        if random.random() < 0.3:
                            findings.append("Barrett's esophagus present")

                    elif modality == "CT_Chest_Abdomen":
                        findings.append(
                            f"Esophageal wall thickening ({np.random.uniform(1.5, 3.0):.1f} cm)"
                        )
                        if random.random() < 0.5:
                            findings.append("Regional lymphadenopathy")
                        if random.random() < 0.2:
                            findings.append("Distant metastases noted")

                    elif modality == "PET_CT":
                        findings.append(
                            f"Hypermetabolic lesion (SUVmax: {np.random.uniform(5.0, 15.0):.1f})"
                        )
                        if random.random() < 0.4:
                            findings.append("FDG-avid lymph nodes")
                    
                    elif modality == "MRI":
                        findings.append(
                            f"Esophageal wall thickening with enhancement ({np.random.uniform(1.2, 2.8):.1f} cm)"
                        )
                        if random.random() < 0.5:
                            findings.append("Peri-esophageal lymphadenopathy")
                        if random.random() < 0.3:
                            findings.append("Invasion of adjacent structures")

                    imaging_record["findings"] = "; ".join(findings)
                    imaging_record["impression"] = "Findings consistent with esophageal carcinoma"

                    # Quantitative measurements
                    imaging_record["tumor_length_cm"] = round(np.random.uniform(2.0, 7.0), 1)
                    imaging_record["wall_thickness_cm"] = round(np.random.uniform(1.0, 2.5), 1)
                    imaging_record["lymph_nodes_positive"] = np.random.randint(0, 10)

                else:
                    # Normal findings
                    imaging_record["findings"] = "No significant abnormalities"
                    imaging_record["impression"] = "Normal study"
                    imaging_record["tumor_length_cm"] = 0.0
                    imaging_record["wall_thickness_cm"] = round(np.random.uniform(0.3, 0.5), 1)
                    imaging_record["lymph_nodes_positive"] = 0

                imaging_data.append(imaging_record)

        return pd.DataFrame(imaging_data)

    def generate_treatment_data(self, patients_df: pd.DataFrame) -> pd.DataFrame:
        """Generate synthetic treatment history and outcomes"""
        treatment_data = []

        treatment_modalities = {
            "surgery": ["Esophagectomy", "Endoscopic resection", "Palliative stent"],
            "chemotherapy": ["Cisplatin + 5-FU", "Carboplatin + Paclitaxel", "FOLFOX", "DCF"],
            "radiation": ["External beam RT", "IMRT", "Brachytherapy"],
            "targeted": ["Trastuzumab", "Ramucirumab", "Pembrolizumab", "Nivolumab"],
        }

        for _, patient in patients_df.iterrows():
            if not patient["has_cancer"]:
                continue

            # Generate treatment plan
            treatments = []

            # Surgery (70% of cancer patients)
            if random.random() < 0.7:
                surgery = random.choice(treatment_modalities["surgery"])
                treatments.append(
                    {
                        "type": "Surgery",
                        "regimen": surgery,
                        "cycles": 1,
                        "start_date": (
                            datetime.now() - timedelta(days=np.random.randint(30, 180))
                        ).strftime("%Y-%m-%d"),
                        "end_date": (
                            datetime.now() - timedelta(days=np.random.randint(1, 30))
                        ).strftime("%Y-%m-%d"),
                    }
                )

            # Chemotherapy (80% of cancer patients)
            if random.random() < 0.8:
                chemo = random.choice(treatment_modalities["chemotherapy"])
                cycles = np.random.randint(4, 12)
                treatments.append(
                    {
                        "type": "Chemotherapy",
                        "regimen": chemo,
                        "cycles": cycles,
                        "start_date": (
                            datetime.now() - timedelta(days=np.random.randint(60, 240))
                        ).strftime("%Y-%m-%d"),
                        "end_date": (
                            datetime.now() - timedelta(days=np.random.randint(1, 60))
                        ).strftime("%Y-%m-%d"),
                    }
                )

            # Radiation (60% of cancer patients)
            if random.random() < 0.6:
                radiation = random.choice(treatment_modalities["radiation"])
                fractions = np.random.randint(25, 35)
                treatments.append(
                    {
                        "type": "Radiation",
                        "regimen": radiation,
                        "cycles": fractions,
                        "start_date": (
                            datetime.now() - timedelta(days=np.random.randint(45, 180))
                        ).strftime("%Y-%m-%d"),
                        "end_date": (
                            datetime.now() - timedelta(days=np.random.randint(1, 45))
                        ).strftime("%Y-%m-%d"),
                    }
                )

            # Targeted therapy (30% of cancer patients)
            if random.random() < 0.3:
                targeted = random.choice(treatment_modalities["targeted"])
                treatments.append(
                    {
                        "type": "Targeted Therapy",
                        "regimen": targeted,
                        "cycles": np.random.randint(6, 24),
                        "start_date": (
                            datetime.now() - timedelta(days=np.random.randint(90, 360))
                        ).strftime("%Y-%m-%d"),
                        "end_date": None,  # Ongoing treatment
                    }
                )

            # Generate treatment response
            response_options = [
                "Complete Response",
                "Partial Response",
                "Stable Disease",
                "Progressive Disease",
            ]
            response_weights = [0.2, 0.4, 0.3, 0.1]

            treatment_record = {
                "patient_id": patient["patient_id"],
                "treatments": json.dumps(treatments),
                "best_response": np.random.choice(response_options, p=response_weights),
                "response_date": (
                    datetime.now() - timedelta(days=np.random.randint(30, 180))
                ).strftime("%Y-%m-%d"),
                "treatment_complications": random.random() < 0.3,
                "complication_details": "Anemia, fatigue"
                if random.random() < 0.5
                else "Neutropenia, nausea",
            }

            # Generate survival data
            diagnosis_date = (
                datetime.now() - timedelta(days=np.random.randint(180, 720))
            ).strftime("%Y-%m-%d")

            treatment_record["diagnosis_date"] = diagnosis_date

            # Calculate survival based on stage and response
            base_survival_days = 365 * np.random.uniform(1.0, 5.0)

            # Adjust based on response
            response_factor = {
                "Complete Response": 2.0,
                "Partial Response": 1.5,
                "Stable Disease": 1.0,
                "Progressive Disease": 0.5,
            }[treatment_record["best_response"]]

            survival_days = base_survival_days * response_factor

            treatment_record["survival_days"] = int(survival_days)
            treatment_record["vital_status"] = "Alive" if random.random() < 0.7 else "Deceased"

            if treatment_record["vital_status"] == "Deceased":
                treatment_record["death_date"] = (
                    datetime.strptime(diagnosis_date, "%Y-%m-%d") + timedelta(days=int(survival_days))
                ).strftime("%Y-%m-%d")
                treatment_record["cause_of_death"] = (
                    "Esophageal cancer" if random.random() < 0.8 else "Other causes"
                )
            else:
                treatment_record["death_date"] = None
                treatment_record["cause_of_death"] = None

            treatment_data.append(treatment_record)

        return pd.DataFrame(treatment_data)

    def generate_quality_of_life_data(self, patients_df: pd.DataFrame) -> pd.DataFrame:
        """Generate synthetic quality of life assessment data"""
        qol_data = []

        qol_questionnaires = ["EORTC_QLQ_C30", "EORTC_QLQ_OG25", "EQ_5D", "MDASI"]

        for _, patient in patients_df.iterrows():
            for questionnaire in qol_questionnaires:
                # Generate multiple assessments over time
                n_assessments = np.random.randint(1, 4) if patient["has_cancer"] else 1

                for assessment_num in range(n_assessments):
                    assessment_date = (
                        datetime.now() - timedelta(days=np.random.randint(1, 365))
                    ).strftime("%Y-%m-%d")

                    qol_record = {
                        "patient_id": patient["patient_id"],
                        "questionnaire": questionnaire,
                        "assessment_date": assessment_date,
                        "assessment_number": assessment_num + 1,
                    }

                    # Generate scores based on cancer status
                    if patient["has_cancer"]:
                        # Lower QoL scores for cancer patients
                        qol_record["global_health_score"] = round(np.random.uniform(40, 70), 1)
                        qol_record["physical_functioning"] = round(np.random.uniform(50, 80), 1)
                        qol_record["emotional_functioning"] = round(np.random.uniform(45, 75), 1)
                        qol_record["social_functioning"] = round(np.random.uniform(40, 70), 1)

                        # Symptom scores (higher = worse)
                        qol_record["fatigue_score"] = round(np.random.uniform(30, 70), 1)
                        qol_record["pain_score"] = round(np.random.uniform(20, 60), 1)
                        qol_record["dysphagia_score"] = round(np.random.uniform(25, 80), 1)
                        qol_record["reflux_score"] = round(np.random.uniform(15, 50), 1)
                    else:
                        # Higher QoL scores for normal patients
                        qol_record["global_health_score"] = round(np.random.uniform(70, 95), 1)
                        qol_record["physical_functioning"] = round(np.random.uniform(80, 100), 1)
                        qol_record["emotional_functioning"] = round(np.random.uniform(75, 95), 1)
                        qol_record["social_functioning"] = round(np.random.uniform(70, 95), 1)

                        # Low symptom scores for normal patients
                        qol_record["fatigue_score"] = round(np.random.uniform(10, 30), 1)
                        qol_record["pain_score"] = round(np.random.uniform(5, 20), 1)
                        qol_record["dysphagia_score"] = round(np.random.uniform(0, 10), 1)
                        qol_record["reflux_score"] = round(np.random.uniform(5, 25), 1)

                    qol_data.append(qol_record)

        return pd.DataFrame(qol_data)

    def generate_all_data(
        self, n_patients: int = 1000, cancer_ratio: float = 0.3
    ) -> Dict[str, pd.DataFrame]:
        """Generate complete synthetic dataset"""
        print("Generating comprehensive synthetic dataset for esophageal cancer research...")
        print(
            f"Total patients: {n_patients} "
            f"(Cancer: {int(n_patients*cancer_ratio)}, "
            f"Normal: {n_patients - int(n_patients*cancer_ratio)})"
        )

        # Generate all data components
        print("\n1. Generating patient demographics...")
        patients_df = self.generate_patient_demographics(n_patients, cancer_ratio)

        print("2. Generating clinical data...")
        clinical_df = self.generate_clinical_data(patients_df)

        print("3. Generating laboratory results...")
        lab_df = self.generate_lab_results(patients_df)

        print("4. Generating genomic data...")
        genomic_df = self.generate_genomic_data(patients_df)

        print("5. Generating imaging data...")
        imaging_df = self.generate_imaging_data(patients_df)

        print("6. Generating treatment data...")
        treatment_df = self.generate_treatment_data(patients_df)

        print("7. Generating quality of life data...")
        qol_df = self.generate_quality_of_life_data(patients_df)

        print("\n✅ Synthetic data generation complete!")

        return {
            "patients": patients_df,
            "clinical": clinical_df,
            "lab": lab_df,
            "genomic": genomic_df,
            "imaging": imaging_df,
            "treatment": treatment_df,
            "qol": qol_df,
        }

    def save_to_database(self, dataset: Dict[str, pd.DataFrame], db: Session):
        """Save generated data to database"""
        from datetime import datetime
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info("Starting to save data to database...")

        # Save patients
        for _, row in dataset["patients"].iterrows():
            patient = Patient(
                patient_id=row["patient_id"],
                age=row["age"],
                gender=row["gender"],
                ethnicity=row.get("ethnicity"),
                has_cancer=row["has_cancer"],
                cancer_type=row.get("cancer_type"),
                cancer_subtype=row.get("cancer_subtype"),
            )
            db.add(patient)

        db.commit()

        # Save clinical data
        for _, row in dataset["clinical"].iterrows():
            clinical = ClinicalData(
                patient_id=row["patient_id"],
                height_cm=row.get("height_cm"),
                weight_kg=row.get("weight_kg"),
                bmi=row.get("bmi"),
                systolic_bp=row.get("systolic_bp"),
                diastolic_bp=row.get("diastolic_bp"),
                heart_rate=row.get("heart_rate"),
                respiratory_rate=row.get("respiratory_rate"),
                tumor_location=row.get("tumor_location"),
                tumor_length_cm=row.get("tumor_length_cm"),
                t_stage=row.get("t_stage"),
                n_stage=row.get("n_stage"),
                m_stage=row.get("m_stage"),
                histological_grade=row.get("histological_grade"),
                lymphovascular_invasion=row.get("lymphovascular_invasion", False),
                perineural_invasion=row.get("perineural_invasion", False),
                symptoms=row.get("symptoms"),
                risk_factors=row.get("risk_factors"),
                examination_date=datetime.now().date(),
            )
            db.add(clinical)

        db.commit()

        # Save lab results
        for _, row in dataset["lab"].iterrows():
            lab = LabResult(
                patient_id=row["patient_id"],
                test_type=row.get("test_type"),
                test_date=datetime.strptime(row.get("test_date"), "%Y-%m-%d").date()
                if row.get("test_date")
                else None,
                hemoglobin=row.get("hemoglobin"),
                wbc_count=row.get("wbc_count"),
                platelet_count=row.get("platelet_count"),
                creatinine=row.get("creatinine"),
                sodium=row.get("sodium"),
                potassium=row.get("potassium"),
                ast=row.get("ast"),
                alt=row.get("alt"),
                alkaline_phosphatase=row.get("alkaline_phosphatase"),
                cea=row.get("cea"),
                ca19_9=row.get("ca19_9"),
                crp=row.get("crp"),
                albumin=row.get("albumin"),
            )
            db.add(lab)

        db.commit()

        # Save genomic data
        for _, row in dataset["genomic"].iterrows():
            genomic = GenomicData(
                patient_id=row["patient_id"],
                cancer_type=row.get("cancer_type"),
                mutations=row.get("mutations"),
                copy_number_variations=row.get("copy_number_variations"),
                gene_expression=row.get("gene_expression"),
                pdl1_status=row.get("pdl1_status"),
                pdl1_percentage=row.get("pdl1_percentage"),
                msi_status=row.get("msi_status"),
                sequencing_platform=row.get("sequencing_platform"),
                coverage_depth=row.get("coverage_depth"),
                sequencing_date=datetime.strptime(row.get("sequencing_date"), "%Y-%m-%d").date()
                if row.get("sequencing_date")
                else None,
            )
            db.add(genomic)

        db.commit()

        # Save imaging data
        logger.info(f"Saving {len(dataset['imaging'])} imaging records...")
        mri_count = 0
        for _, row in dataset["imaging"].iterrows():
            try:
                imaging = ImagingData(
                    patient_id=row["patient_id"],
                    imaging_modality=row.get("imaging_modality"),
                    findings=row.get("findings"),
                    impression=row.get("impression"),
                    tumor_length_cm=row.get("tumor_length_cm"),
                    wall_thickness_cm=row.get("wall_thickness_cm"),
                    lymph_nodes_positive=row.get("lymph_nodes_positive", 0),
                    contrast_used=row.get("contrast_used", False),
                    radiologist_id=row.get("radiologist_id"),
                    imaging_date=datetime.strptime(row.get("imaging_date"), "%Y-%m-%d").date()
                    if row.get("imaging_date")
                    else None,
                )
                db.add(imaging)
                if row.get("imaging_modality") == "MRI":
                    mri_count += 1
            except Exception as e:
                logger.error(f"Error saving imaging record for patient {row.get('patient_id')}: {e}")
                continue

        db.commit()
        logger.info(f"✅ Saved {mri_count} MRI records out of {len(dataset['imaging'])} total imaging records")
        
        # Verify MRI records were actually saved (refresh session to see committed data)
        db.expire_all()
        saved_mri_count = db.query(ImagingData).filter(ImagingData.imaging_modality == "MRI").count()
        logger.info(f"✅ Verified: {saved_mri_count} MRI records now in database")

        # Save treatment data
        for _, row in dataset["treatment"].iterrows():
            treatment = TreatmentData(
                patient_id=row["patient_id"],
                treatments=row.get("treatments"),
                best_response=row.get("best_response"),
                response_date=datetime.strptime(row.get("response_date"), "%Y-%m-%d").date()
                if row.get("response_date")
                else None,
                diagnosis_date=datetime.strptime(row.get("diagnosis_date"), "%Y-%m-%d").date()
                if row.get("diagnosis_date")
                else None,
                survival_days=row.get("survival_days"),
                vital_status=row.get("vital_status"),
                death_date=datetime.strptime(row.get("death_date"), "%Y-%m-%d").date()
                if row.get("death_date")
                else None,
                cause_of_death=row.get("cause_of_death"),
                treatment_complications=row.get("treatment_complications", False),
                complication_details=row.get("complication_details"),
            )
            db.add(treatment)

        db.commit()

        # Save quality of life data
        for _, row in dataset["qol"].iterrows():
            qol = QualityOfLife(
                patient_id=row["patient_id"],
                questionnaire=row.get("questionnaire"),
                assessment_date=datetime.strptime(row.get("assessment_date"), "%Y-%m-%d").date()
                if row.get("assessment_date")
                else None,
                assessment_number=row.get("assessment_number"),
                global_health_score=row.get("global_health_score"),
                physical_functioning=row.get("physical_functioning"),
                emotional_functioning=row.get("emotional_functioning"),
                social_functioning=row.get("social_functioning"),
                fatigue_score=row.get("fatigue_score"),
                pain_score=row.get("pain_score"),
                dysphagia_score=row.get("dysphagia_score"),
                reflux_score=row.get("reflux_score"),
            )
            db.add(qol)

        # Final commit for all data
        db.commit()
        db.flush()  # Ensure all changes are flushed to database
        
        logger.info("✅ Data saved to database successfully!")
        print("✅ Data saved to database successfully!")
        
        # Final verification - check all imaging modalities
        db.expire_all()  # Refresh all objects from database
        total_imaging = db.query(ImagingData).count()
        total_mri_final = db.query(ImagingData).filter(ImagingData.imaging_modality == "MRI").count()
        logger.info(f"✅ Final verification: {total_imaging} total imaging records, {total_mri_final} MRI records in database")
        print(f"✅ Final verification: {total_imaging} total imaging records, {total_mri_final} MRI records in database")

