"""
Clinical trial matching system
"""
import requests
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import json


class ClinicalTrialMatcher:
    """Match patients to clinical trials"""

    def __init__(self):
        self.base_url = "https://clinicaltrials.gov/api/v2/studies"
        self.cache = {}

    def search_trials(
        self,
        condition: str = "Esophageal Cancer",
        status: str = "RECRUITING",
        max_results: int = 50,
    ) -> List[Dict]:
        """Search for clinical trials"""
        try:
            params = {
                "query.cond": condition,
                "filter.overallStatus": status,
                "pageSize": min(max_results, 100),
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            trials = []

            for study in data.get("studies", []):
                protocol_section = study.get("protocolSection", {})
                identification = protocol_section.get("identificationModule", {})
                eligibility = protocol_section.get("eligibilityModule", {})

                trial = {
                    "nct_id": identification.get("nctId", ""),
                    "title": identification.get("briefTitle", ""),
                    "status": study.get("status", {}).get("overallStatus", ""),
                    "phase": protocol_section.get("designModule", {}).get("phases", []),
                    "eligibility_criteria": eligibility.get("eligibilityCriteria", ""),
                    "conditions": [
                        c.get("name", "") for c in eligibility.get("conditions", [])
                    ],
                }

                trials.append(trial)

            return trials

        except Exception as e:
            print(f"Error searching trials: {str(e)}")
            return []

    def match_patient_to_trials(
        self, patient_data: Dict, cancer_data: Optional[Dict] = None
    ) -> Dict:
        """Match patient to relevant clinical trials"""
        matches = {
            "patient_id": patient_data.get("patient_id"),
            "matches": [],
            "match_criteria": {},
            "generated_at": datetime.now().isoformat(),
        }

        # Search for trials
        trials = self.search_trials(
            condition="Esophageal Cancer", status="RECRUITING", max_results=50
        )

        # Match based on patient characteristics
        for trial in trials:
            match_score = self._calculate_match_score(
                patient_data, cancer_data, trial
            )

            if match_score["score"] > 0.5:  # Threshold for matching
                matches["matches"].append(
                    {
                        "nct_id": trial["nct_id"],
                        "title": trial["title"],
                        "status": trial["status"],
                        "phase": trial["phase"],
                        "match_score": match_score["score"],
                        "match_reasons": match_score["reasons"],
                    }
                )

        # Sort by match score
        matches["matches"].sort(key=lambda x: x["match_score"], reverse=True)

        # Calculate overall match statistics
        matches["total_trials_found"] = len(trials)
        matches["matching_trials"] = len(matches["matches"])
        matches["match_rate"] = (
            len(matches["matches"]) / len(trials) if trials else 0
        )

        return matches

    def _calculate_match_score(
        self, patient_data: Dict, cancer_data: Optional[Dict], trial: Dict
    ) -> Dict:
        """Calculate match score for a trial"""
        score = 0.0
        reasons = []

        # Check cancer type match
        if cancer_data:
            cancer_type = cancer_data.get("cancer_type", "")
            trial_conditions = " ".join(trial.get("conditions", [])).lower()

            if cancer_type.lower() in trial_conditions or "esophageal" in trial_conditions:
                score += 0.3
                reasons.append("Cancer type matches trial condition")

        # Check stage match
        if cancer_data:
            stage = self._get_stage(cancer_data)
            eligibility = trial.get("eligibility_criteria", "").lower()

            if stage.lower() in eligibility:
                score += 0.2
                reasons.append(f"Stage {stage} matches eligibility")

        # Check age eligibility (basic)
        age = patient_data.get("age", 65)
        if "18 years" in trial.get("eligibility_criteria", ""):
            if 18 <= age <= 80:
                score += 0.1
                reasons.append("Age within eligible range")

        # Check biomarker match
        if cancer_data:
            biomarkers = self._extract_biomarkers(cancer_data)
            eligibility = trial.get("eligibility_criteria", "").lower()

            if biomarkers.get("pdl1_positive") and "pdl1" in eligibility:
                score += 0.2
                reasons.append("PD-L1 positive status matches trial")

            if biomarkers.get("her2_positive") and "her2" in eligibility:
                score += 0.2
                reasons.append("HER2 positive status matches trial")

        return {"score": min(1.0, score), "reasons": reasons}

    def _get_stage(self, cancer_data: Dict) -> str:
        """Get cancer stage"""
        t_stage = cancer_data.get("t_stage", "")
        n_stage = cancer_data.get("n_stage", "")
        m_stage = cancer_data.get("m_stage", "")

        if m_stage == "M1":
            return "IV"
        elif t_stage in ["T3", "T4"] or n_stage in ["N2", "N3"]:
            return "III"
        elif t_stage in ["T2"] or n_stage == "N1":
            return "II"
        elif t_stage == "T1" and n_stage == "N0":
            return "I"
        return "II"

    def _extract_biomarkers(self, cancer_data: Dict) -> Dict:
        """Extract biomarkers"""
        biomarkers = {
            "pdl1_positive": False,
            "her2_positive": False,
        }

        pdl1_status = cancer_data.get("pdl1_status", "")
        if pdl1_status == "Positive":
            biomarkers["pdl1_positive"] = True

        mutations = cancer_data.get("mutations", "[]")
        try:
            mut_list = json.loads(mutations) if isinstance(mutations, str) else mutations
            if isinstance(mut_list, list):
                for mut in mut_list:
                    if mut.get("gene") == "ERBB2":
                        biomarkers["her2_positive"] = True
        except:
            pass

        return biomarkers

