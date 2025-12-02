"""
Prognostic scoring system
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime, timedelta


class PrognosticScorer:
    """Calculate prognostic scores for esophageal cancer patients"""

    def __init__(self):
        # AJCC 8th edition staging
        self.stage_survival = {
            "I": {"median_survival_months": 60, "5_year_survival": 0.70},
            "II": {"median_survival_months": 36, "5_year_survival": 0.50},
            "III": {"median_survival_months": 18, "5_year_survival": 0.25},
            "IV": {"median_survival_months": 12, "5_year_survival": 0.10},
        }

    def calculate_prognostic_score(
        self, patient_data: Dict, cancer_data: Optional[Dict] = None
    ) -> Dict:
        """Calculate comprehensive prognostic score"""
        score = 0.0
        factors = []

        # Stage factor (most important)
        stage = self._determine_stage(patient_data, cancer_data)
        stage_info = self.stage_survival.get(stage, self.stage_survival["III"])
        stage_score = 1.0 - (stage_info["5_year_survival"])
        score += stage_score * 0.40
        factors.append(
            {
                "factor": "stage",
                "value": stage,
                "contribution": stage_score * 0.40,
                "impact": "high",
            }
        )

        # Age factor
        age = patient_data.get("age", 65)
        if age > 75:
            age_score = 0.3
        elif age > 65:
            age_score = 0.15
        else:
            age_score = 0.0
        score += age_score * 0.15
        factors.append(
            {
                "factor": "age",
                "value": age,
                "contribution": age_score * 0.15,
                "impact": "moderate",
            }
        )

        # Performance status (if available)
        performance_status = patient_data.get("performance_status", 1)
        ps_score = (performance_status - 1) / 3.0  # Normalize 1-4 to 0-1
        score += ps_score * 0.15
        factors.append(
            {
                "factor": "performance_status",
                "value": performance_status,
                "contribution": ps_score * 0.15,
                "impact": "moderate",
            }
        )

        # Treatment response (if available)
        if cancer_data:
            response = cancer_data.get("best_response", "")
            if response == "Complete Response":
                response_score = -0.3  # Negative = better prognosis
            elif response == "Partial Response":
                response_score = -0.15
            elif response == "Stable Disease":
                response_score = 0.0
            else:  # Progressive Disease
                response_score = 0.3
            score += response_score * 0.20
            factors.append(
                {
                    "factor": "treatment_response",
                    "value": response,
                    "contribution": response_score * 0.20,
                    "impact": "high",
                }
            )

        # Biomarkers
        if cancer_data:
            # PD-L1 positive
            pdl1_status = cancer_data.get("pdl1_status", "")
            if pdl1_status == "Positive":
                biomarker_score = -0.1  # Better prognosis
                score += biomarker_score * 0.10
                factors.append(
                    {
                        "factor": "pdl1_positive",
                        "value": True,
                        "contribution": biomarker_score * 0.10,
                        "impact": "low",
                    }
                )

        # Normalize score to 0-1 (higher = worse prognosis)
        score = max(0.0, min(1.0, score))

        # Calculate survival estimates
        survival_estimates = self._calculate_survival_estimates(
            stage, score, patient_data, cancer_data
        )

        # Prognostic category
        if score < 0.3:
            category = "Favorable"
            interpretation = "Good prognosis with appropriate treatment"
        elif score < 0.6:
            category = "Moderate"
            interpretation = "Moderate prognosis, close monitoring recommended"
        else:
            category = "Poor"
            interpretation = "Poor prognosis, aggressive treatment may be needed"

        return {
            "prognostic_score": round(score, 3),
            "category": category,
            "interpretation": interpretation,
            "stage": stage,
            "survival_estimates": survival_estimates,
            "factors": factors,
            "calculated_at": datetime.now().isoformat(),
        }

    def _determine_stage(
        self, patient_data: Dict, cancer_data: Optional[Dict]
    ) -> str:
        """Determine cancer stage"""
        if cancer_data:
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

        return "II"  # Default

    def _calculate_survival_estimates(
        self,
        stage: str,
        score: float,
        patient_data: Dict,
        cancer_data: Optional[Dict],
    ) -> Dict:
        """Calculate survival estimates"""
        base_survival = self.stage_survival.get(stage, self.stage_survival["III"])

        # Adjust based on prognostic score
        adjustment_factor = 1.0 - (score * 0.5)  # Reduce survival by up to 50%

        median_survival = base_survival["median_survival_months"] * adjustment_factor
        five_year_survival = base_survival["5_year_survival"] * adjustment_factor

        return {
            "median_survival_months": round(median_survival, 1),
            "5_year_survival_rate": round(five_year_survival, 3),
            "1_year_survival_rate": round(min(0.95, five_year_survival * 1.5), 3),
        }

    def correlate_with_outcomes(
        self, prognostic_scores: pd.Series, actual_outcomes: pd.Series
    ) -> Dict:
        """Correlate prognostic scores with actual outcomes"""
        from scipy.stats import pearsonr, spearmanr

        try:
            # Remove NaN
            valid_indices = ~(prognostic_scores.isna() | actual_outcomes.isna())
            scores_clean = prognostic_scores[valid_indices]
            outcomes_clean = actual_outcomes[valid_indices]

            if len(scores_clean) < 2:
                return {"correlation": 0.0, "p_value": 1.0}

            # Pearson correlation
            pearson_r, pearson_p = pearsonr(scores_clean, outcomes_clean)

            # Spearman correlation
            spearman_r, spearman_p = spearmanr(scores_clean, outcomes_clean)

            return {
                "pearson_correlation": round(float(pearson_r), 3),
                "pearson_p_value": round(float(pearson_p), 4),
                "spearman_correlation": round(float(spearman_r), 3),
                "spearman_p_value": round(float(spearman_p), 4),
                "n_samples": len(scores_clean),
            }

        except Exception as e:
            return {"error": str(e)}

