"""
Treatment recommendation engine
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import json


class TreatmentRecommender:
    """Recommend treatments based on patient characteristics"""

    def __init__(self):
        # NCCN guidelines-based recommendations
        self.treatment_guidelines = {
            "stage_I": {
                "primary": ["Surgery", "Endoscopic resection"],
                "adjuvant": [],
                "targeted": [],
            },
            "stage_II": {
                "primary": ["Surgery", "Chemoradiation"],
                "adjuvant": ["Chemotherapy"],
                "targeted": [],
            },
            "stage_III": {
                "primary": ["Chemoradiation", "Surgery"],
                "adjuvant": ["Chemotherapy"],
                "targeted": ["Pembrolizumab", "Nivolumab"],
            },
            "stage_IV": {
                "primary": ["Chemotherapy", "Targeted therapy"],
                "adjuvant": [],
                "targeted": ["Pembrolizumab", "Nivolumab", "Ramucirumab", "Trastuzumab"],
            },
        }

        # Treatment regimens
        self.regimens = {
            "Chemotherapy": [
                "Cisplatin + 5-FU",
                "Carboplatin + Paclitaxel",
                "FOLFOX",
                "DCF (Docetaxel + Cisplatin + 5-FU)",
            ],
            "Radiation": [
                "External beam RT (50-54 Gy)",
                "IMRT (Intensity-Modulated RT)",
                "Brachytherapy",
            ],
            "Surgery": [
                "Esophagectomy",
                "Endoscopic resection",
                "Minimally invasive esophagectomy",
            ],
            "Targeted Therapy": [
                "Trastuzumab (HER2+)",
                "Ramucirumab",
                "Pembrolizumab (PD-L1+)",
                "Nivolumab (PD-L1+)",
            ],
        }

    def recommend_treatment(
        self, patient_data: Dict, cancer_data: Optional[Dict] = None
    ) -> Dict:
        """Recommend treatment based on patient and cancer characteristics"""
        recommendations = {
            "patient_id": patient_data.get("patient_id"),
            "recommendations": [],
            "rationale": [],
            "guidelines": "NCCN",
            "generated_at": datetime.now().isoformat(),
        }

        # Determine stage
        stage = self._determine_stage(patient_data, cancer_data)

        # Get guideline-based recommendations
        if stage in self.treatment_guidelines:
            guidelines = self.treatment_guidelines[stage]

            # Primary treatments
            for treatment_type in guidelines["primary"]:
                regimens = self.regimens.get(treatment_type, [])
                for regimen in regimens:
                    if self._is_applicable(regimen, patient_data, cancer_data):
                        recommendations["recommendations"].append(
                            {
                                "type": treatment_type,
                                "regimen": regimen,
                                "priority": "primary",
                                "rationale": f"Recommended for {stage} based on NCCN guidelines",
                            }
                        )

            # Adjuvant treatments
            for treatment_type in guidelines["adjuvant"]:
                regimens = self.regimens.get(treatment_type, [])
                for regimen in regimens:
                    if self._is_applicable(regimen, patient_data, cancer_data):
                        recommendations["recommendations"].append(
                            {
                                "type": treatment_type,
                                "regimen": regimen,
                                "priority": "adjuvant",
                                "rationale": f"Adjuvant therapy for {stage}",
                            }
                        )

            # Targeted therapies
            for treatment_type in guidelines["targeted"]:
                if self._is_applicable(treatment_type, patient_data, cancer_data):
                    recommendations["recommendations"].append(
                        {
                            "type": "Targeted Therapy",
                            "regimen": treatment_type,
                            "priority": "targeted",
                            "rationale": f"Targeted therapy for {stage}",
                        }
                    )

        # Add personalized recommendations based on biomarkers
        personalized = self._get_personalized_recommendations(patient_data, cancer_data)
        recommendations["recommendations"].extend(personalized)

        # Sort by priority
        priority_order = {"primary": 1, "adjuvant": 2, "targeted": 3}
        recommendations["recommendations"].sort(
            key=lambda x: priority_order.get(x["priority"], 4)
        )

        return recommendations

    def _determine_stage(
        self, patient_data: Dict, cancer_data: Optional[Dict]
    ) -> str:
        """Determine cancer stage"""
        if cancer_data:
            t_stage = cancer_data.get("t_stage", "")
            n_stage = cancer_data.get("n_stage", "")
            m_stage = cancer_data.get("m_stage", "")

            # Simple staging logic
            if m_stage == "M1":
                return "stage_IV"
            elif t_stage in ["T3", "T4"] or n_stage in ["N2", "N3"]:
                return "stage_III"
            elif t_stage in ["T2"] or n_stage == "N1":
                return "stage_II"
            elif t_stage == "T1" and n_stage == "N0":
                return "stage_I"

        # Default based on patient data
        if patient_data.get("has_cancer"):
            return "stage_II"  # Default assumption
        return "stage_I"

    def _is_applicable(
        self, regimen: str, patient_data: Dict, cancer_data: Optional[Dict]
    ) -> bool:
        """Check if treatment is applicable"""
        # Check for HER2+ for Trastuzumab
        if "Trastuzumab" in regimen or "HER2" in regimen:
            if cancer_data:
                # Check genomic data for HER2
                mutations = cancer_data.get("mutations", "[]")
                try:
                    mut_list = json.loads(mutations) if isinstance(mutations, str) else mutations
                    if isinstance(mut_list, list):
                        her2_genes = [m.get("gene") for m in mut_list if m.get("gene") == "ERBB2"]
                        if not her2_genes:
                            # Check expression
                            expression = cancer_data.get("gene_expression", "{}")
                            expr_dict = json.loads(expression) if isinstance(expression, str) else expression
                            if isinstance(expr_dict, dict) and expr_dict.get("HER2", 0) > 10:
                                return True
                    return False
                except:
                    return True  # Default to applicable if can't check

        # Check for PD-L1+ for immunotherapy
        if "Pembrolizumab" in regimen or "Nivolumab" in regimen or "PD-L1" in regimen:
            if cancer_data:
                pdl1_status = cancer_data.get("pdl1_status", "")
                pdl1_percentage = cancer_data.get("pdl1_percentage", 0)
                if pdl1_status == "Positive" or pdl1_percentage >= 1:
                    return True
                return False

        # Default: applicable
        return True

    def _get_personalized_recommendations(
        self, patient_data: Dict, cancer_data: Optional[Dict]
    ) -> List[Dict]:
        """Get personalized recommendations based on biomarkers"""
        personalized = []

        if not cancer_data:
            return personalized

        # MSI-H status
        msi_status = cancer_data.get("msi_status", "")
        if msi_status == "MSI-H":
            personalized.append(
                {
                    "type": "Targeted Therapy",
                    "regimen": "Pembrolizumab",
                    "priority": "targeted",
                    "rationale": "MSI-H status indicates potential benefit from immunotherapy",
                }
            )

        # High mutation burden
        mutations = cancer_data.get("mutations", "[]")
        try:
            mut_list = json.loads(mutations) if isinstance(mutations, str) else mutations
            if isinstance(mut_list, list) and len(mut_list) > 5:
                personalized.append(
                    {
                        "type": "Targeted Therapy",
                        "regimen": "Pembrolizumab",
                        "priority": "targeted",
                        "rationale": "High tumor mutational burden may benefit from immunotherapy",
                    }
                )
        except:
            pass

        return personalized

