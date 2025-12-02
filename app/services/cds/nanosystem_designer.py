"""
Personalized nanosystem design suggestions
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import json


class NanosystemDesigner:
    """Suggest personalized nanosystem designs"""

    def __init__(self):
        # Nanosystem types and their characteristics
        self.nanosystem_types = {
            "liposomal": {
                "description": "Lipid-based nanoparticles",
                "applications": ["Drug delivery", "Imaging"],
                "targeting": ["Passive (EPR effect)", "Active (ligand-based)"],
                "size_range": "50-200 nm",
            },
            "polymeric": {
                "description": "Polymer-based nanoparticles",
                "applications": ["Drug delivery", "Gene therapy"],
                "targeting": ["Active targeting"],
                "size_range": "20-500 nm",
            },
            "metallic": {
                "description": "Metal-based nanoparticles (gold, iron oxide)",
                "applications": ["Imaging", "Hyperthermia", "Drug delivery"],
                "targeting": ["Active targeting"],
                "size_range": "10-100 nm",
            },
            "quantum_dot": {
                "description": "Semiconductor quantum dots",
                "applications": ["Imaging", "Diagnostics"],
                "targeting": ["Active targeting"],
                "size_range": "2-10 nm",
            },
        }

        # Targeting ligands
        self.targeting_ligands = {
            "EGFR": {
                "ligand": "Cetuximab",
                "target": "Epidermal Growth Factor Receptor",
                "applicable_cancers": ["adenocarcinoma", "squamous_cell_carcinoma"],
            },
            "HER2": {
                "ligand": "Trastuzumab",
                "target": "Human Epidermal Growth Factor Receptor 2",
                "applicable_cancers": ["adenocarcinoma"],
            },
            "VEGFR": {
                "ligand": "Bevacizumab",
                "target": "Vascular Endothelial Growth Factor Receptor",
                "applicable_cancers": ["adenocarcinoma", "squamous_cell_carcinoma"],
            },
            "PD-L1": {
                "ligand": "Atezolizumab",
                "target": "Programmed Death-Ligand 1",
                "applicable_cancers": ["adenocarcinoma", "squamous_cell_carcinoma"],
            },
        }

    def suggest_nanosystem(
        self, patient_data: Dict, cancer_data: Optional[Dict] = None
    ) -> Dict:
        """Suggest personalized nanosystem design"""
        suggestions = {
            "patient_id": patient_data.get("patient_id"),
            "suggestions": [],
            "rationale": [],
            "generated_at": datetime.now().isoformat(),
        }

        if not cancer_data:
            return suggestions

        # Determine cancer type
        cancer_type = cancer_data.get("cancer_type", "adenocarcinoma")

        # Analyze biomarkers
        biomarkers = self._analyze_biomarkers(cancer_data)

        # Suggest nanosystem type
        nanosystem_type = self._suggest_nanosystem_type(cancer_type, biomarkers)
        suggestions["suggestions"].append(
            {
                "component": "Nanosystem Type",
                "recommendation": nanosystem_type,
                "rationale": f"Recommended for {cancer_type} based on characteristics",
            }
        )

        # Suggest targeting ligand
        targeting = self._suggest_targeting(cancer_data, biomarkers)
        if targeting:
            suggestions["suggestions"].append(
                {
                    "component": "Targeting Ligand",
                    "recommendation": targeting["ligand"],
                    "target": targeting["target"],
                    "rationale": targeting["rationale"],
                }
            )

        # Suggest payload
        payload = self._suggest_payload(cancer_type, biomarkers)
        if payload:
            suggestions["suggestions"].append(
                {
                    "component": "Therapeutic Payload",
                    "recommendation": payload,
                    "rationale": f"Based on {cancer_type} characteristics and biomarkers",
                }
            )

        # Suggest size
        size = self._suggest_size(cancer_type, nanosystem_type)
        suggestions["suggestions"].append(
            {
                "component": "Particle Size",
                "recommendation": size,
                "rationale": "Optimized for tumor penetration and retention",
            }
        )

        return suggestions

    def _analyze_biomarkers(self, cancer_data: Dict) -> Dict:
        """Analyze biomarkers from cancer data"""
        biomarkers = {
            "her2_positive": False,
            "egfr_positive": False,
            "pdl1_positive": False,
            "msi_high": False,
        }

        # Check HER2
        mutations = cancer_data.get("mutations", "[]")
        try:
            mut_list = json.loads(mutations) if isinstance(mutations, str) else mutations
            if isinstance(mut_list, list):
                for mut in mut_list:
                    if mut.get("gene") == "ERBB2":
                        biomarkers["her2_positive"] = True
        except:
            pass

        # Check PD-L1
        pdl1_status = cancer_data.get("pdl1_status", "")
        if pdl1_status == "Positive":
            biomarkers["pdl1_positive"] = True

        # Check MSI
        msi_status = cancer_data.get("msi_status", "")
        if msi_status == "MSI-H":
            biomarkers["msi_high"] = True

        return biomarkers

    def _suggest_nanosystem_type(
        self, cancer_type: str, biomarkers: Dict
    ) -> str:
        """Suggest nanosystem type"""
        # For most cases, liposomal is a good default
        if cancer_type == "adenocarcinoma":
            return "liposomal"
        elif cancer_type == "squamous_cell_carcinoma":
            return "polymeric"
        else:
            return "liposomal"

    def _suggest_targeting(
        self, cancer_data: Dict, biomarkers: Dict
    ) -> Optional[Dict]:
        """Suggest targeting ligand"""
        # HER2 targeting
        if biomarkers.get("her2_positive"):
            return {
                "ligand": "Trastuzumab",
                "target": "HER2",
                "rationale": "HER2 positive status indicates benefit from HER2-targeted therapy",
            }

        # PD-L1 targeting
        if biomarkers.get("pdl1_positive"):
            return {
                "ligand": "Atezolizumab",
                "target": "PD-L1",
                "rationale": "PD-L1 positive status suggests immunotherapy benefit",
            }

        # EGFR targeting (default for many cases)
        return {
            "ligand": "Cetuximab",
            "target": "EGFR",
            "rationale": "EGFR is commonly expressed in esophageal cancer",
        }

    def _suggest_payload(
        self, cancer_type: str, biomarkers: Dict
    ) -> Optional[str]:
        """Suggest therapeutic payload"""
        # Chemotherapy payload
        if cancer_type == "adenocarcinoma":
            return "Cisplatin + 5-FU"
        elif cancer_type == "squamous_cell_carcinoma":
            return "Carboplatin + Paclitaxel"

        # Immunotherapy payload
        if biomarkers.get("pdl1_positive") or biomarkers.get("msi_high"):
            return "Pembrolizumab"

        return "Cisplatin + 5-FU"  # Default

    def _suggest_size(self, cancer_type: str, nanosystem_type: str) -> str:
        """Suggest particle size"""
        size_ranges = {
            "liposomal": "100-150 nm",
            "polymeric": "50-100 nm",
            "metallic": "20-50 nm",
            "quantum_dot": "5-10 nm",
        }
        return size_ranges.get(nanosystem_type, "50-150 nm")

