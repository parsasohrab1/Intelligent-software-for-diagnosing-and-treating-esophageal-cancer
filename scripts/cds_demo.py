"""
Demo script for Clinical Decision Support system
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.cds.risk_predictor import RiskPredictor
from app.services.cds.treatment_recommender import TreatmentRecommender
from app.services.cds.prognostic_scorer import PrognosticScorer
from app.services.cds.nanosystem_designer import NanosystemDesigner
from app.services.cds.clinical_trial_matcher import ClinicalTrialMatcher
from app.services.cds.monitoring_alerts import MonitoringAlerts


def main():
    # Sample patient data
    patient_data = {
        "patient_id": "DEMO001",
        "age": 65,
        "gender": "Male",
        "bmi": 32,
        "smoking": True,
        "alcohol": True,
        "gerd": True,
        "barretts_esophagus": True,
        "family_history": False,
    }

    cancer_data = {
        "cancer_type": "adenocarcinoma",
        "t_stage": "T3",
        "n_stage": "N1",
        "m_stage": "M0",
        "pdl1_status": "Positive",
        "pdl1_percentage": 45.0,
        "msi_status": "MSS",
        "mutations": '[{"gene": "TP53", "mutation_type": "Missense"}]',
    }

    print("=" * 60)
    print("Clinical Decision Support System Demo")
    print("=" * 60)

    # Risk Prediction
    print("\n1. Risk Prediction")
    print("-" * 60)
    predictor = RiskPredictor()
    risk_result = predictor.calculate_risk_score(patient_data)
    print(f"Risk Score: {risk_result['risk_score']:.3f}")
    print(f"Risk Category: {risk_result['risk_category']}")
    print(f"Recommendation: {risk_result['recommendation']}")

    # Treatment Recommendation
    print("\n2. Treatment Recommendation")
    print("-" * 60)
    recommender = TreatmentRecommender()
    treatment_result = recommender.recommend_treatment(patient_data, cancer_data)
    print(f"Found {len(treatment_result['recommendations'])} recommendations:")
    for i, rec in enumerate(treatment_result["recommendations"][:5], 1):
        print(f"  {i}. {rec['type']}: {rec['regimen']} ({rec['priority']})")

    # Prognostic Score
    print("\n3. Prognostic Score")
    print("-" * 60)
    scorer = PrognosticScorer()
    prognostic_result = scorer.calculate_prognostic_score(patient_data, cancer_data)
    print(f"Prognostic Score: {prognostic_result['prognostic_score']:.3f}")
    print(f"Category: {prognostic_result['category']}")
    print(f"Interpretation: {prognostic_result['interpretation']}")
    print(
        f"Median Survival: {prognostic_result['survival_estimates']['median_survival_months']:.1f} months"
    )

    # Nanosystem Design
    print("\n4. Nanosystem Design Suggestions")
    print("-" * 60)
    designer = NanosystemDesigner()
    nanosystem_result = designer.suggest_nanosystem(patient_data, cancer_data)
    print(f"Found {len(nanosystem_result['suggestions'])} suggestions:")
    for suggestion in nanosystem_result["suggestions"]:
        print(f"  - {suggestion['component']}: {suggestion['recommendation']}")

    # Clinical Trial Matching
    print("\n5. Clinical Trial Matching")
    print("-" * 60)
    matcher = ClinicalTrialMatcher()
    trial_result = matcher.match_patient_to_trials(patient_data, cancer_data)
    print(f"Found {trial_result['matching_trials']} matching trials:")
    for i, match in enumerate(trial_result["matches"][:3], 1):
        print(f"  {i}. {match['title'][:50]}...")
        print(f"     Match Score: {match['match_score']:.2f}")

    # Monitoring Alerts
    print("\n6. Monitoring Alerts")
    print("-" * 60)
    monitor = MonitoringAlerts()
    alerts = monitor.check_alerts(patient_data)
    summary = monitor.generate_alert_summary(alerts)
    print(f"Total Alerts: {summary['total_alerts']}")
    print(f"Status: {summary['status']}")
    if alerts:
        for alert in alerts[:3]:
            print(f"  - [{alert['severity'].upper()}] {alert['message']}")

    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

