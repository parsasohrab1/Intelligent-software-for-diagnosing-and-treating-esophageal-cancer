"""
Real-time monitoring and alert system
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MonitoringAlerts:
    """Real-time monitoring and alert generation"""

    def __init__(self):
        self.alert_thresholds = {
            "risk_score": {"high": 0.7, "critical": 0.9},
            "prognostic_score": {"high": 0.8, "critical": 0.95},
            "biomarker_change": {"high": 0.3, "critical": 0.5},
            "treatment_response": {"high": "Stable Disease", "critical": "Progressive Disease"},
        }

    def check_alerts(
        self, patient_data: Dict, previous_data: Optional[Dict] = None
    ) -> List[Dict]:
        """Check for alerts based on patient data"""
        alerts = []

        # Risk score alert
        risk_score = patient_data.get("risk_score", 0)
        if risk_score >= self.alert_thresholds["risk_score"]["critical"]:
            alerts.append(
                {
                    "type": "risk_score",
                    "severity": AlertSeverity.CRITICAL.value,
                    "message": f"Critical risk score detected: {risk_score:.2f}",
                    "recommendation": "Immediate evaluation required",
                    "timestamp": datetime.now().isoformat(),
                }
            )
        elif risk_score >= self.alert_thresholds["risk_score"]["high"]:
            alerts.append(
                {
                    "type": "risk_score",
                    "severity": AlertSeverity.HIGH.value,
                    "message": f"High risk score detected: {risk_score:.2f}",
                    "recommendation": "Close monitoring recommended",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Prognostic score alert
        prognostic_score = patient_data.get("prognostic_score", 0)
        if prognostic_score >= self.alert_thresholds["prognostic_score"]["critical"]:
            alerts.append(
                {
                    "type": "prognostic_score",
                    "severity": AlertSeverity.CRITICAL.value,
                    "message": f"Critical prognostic score: {prognostic_score:.2f}",
                    "recommendation": "Urgent intervention may be needed",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Biomarker change alert
        if previous_data:
            alerts.extend(self._check_biomarker_changes(patient_data, previous_data))

        # Treatment response alert
        treatment_response = patient_data.get("treatment_response", "")
        if treatment_response == "Progressive Disease":
            alerts.append(
                {
                    "type": "treatment_response",
                    "severity": AlertSeverity.CRITICAL.value,
                    "message": "Progressive disease detected",
                    "recommendation": "Treatment modification required",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Vital signs alerts
        alerts.extend(self._check_vital_signs(patient_data))

        return alerts

    def _check_biomarker_changes(
        self, current_data: Dict, previous_data: Dict
    ) -> List[Dict]:
        """Check for significant biomarker changes"""
        alerts = []

        biomarkers = ["cea", "ca19_9", "crp"]
        for biomarker in biomarkers:
            current_value = current_data.get(biomarker, 0)
            previous_value = previous_data.get(biomarker, 0)

            if previous_value > 0:
                change_ratio = abs(current_value - previous_value) / previous_value

                if change_ratio >= self.alert_thresholds["biomarker_change"]["critical"]:
                    alerts.append(
                        {
                            "type": "biomarker_change",
                            "severity": AlertSeverity.CRITICAL.value,
                            "message": f"Critical change in {biomarker}: {change_ratio:.1%}",
                            "recommendation": "Immediate review required",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                elif change_ratio >= self.alert_thresholds["biomarker_change"]["high"]:
                    alerts.append(
                        {
                            "type": "biomarker_change",
                            "severity": AlertSeverity.HIGH.value,
                            "message": f"Significant change in {biomarker}: {change_ratio:.1%}",
                            "recommendation": "Close monitoring recommended",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

        return alerts

    def _check_vital_signs(self, patient_data: Dict) -> List[Dict]:
        """Check vital signs for alerts"""
        alerts = []

        # Blood pressure
        systolic_bp = patient_data.get("systolic_bp", 120)
        if systolic_bp > 180:
            alerts.append(
                {
                    "type": "vital_signs",
                    "severity": AlertSeverity.HIGH.value,
                    "message": f"Elevated blood pressure: {systolic_bp} mmHg",
                    "recommendation": "Medical evaluation recommended",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Heart rate
        heart_rate = patient_data.get("heart_rate", 75)
        if heart_rate > 120:
            alerts.append(
                {
                    "type": "vital_signs",
                    "severity": AlertSeverity.MEDIUM.value,
                    "message": f"Elevated heart rate: {heart_rate} bpm",
                    "recommendation": "Monitor closely",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        return alerts

    def generate_alert_summary(self, alerts: List[Dict]) -> Dict:
        """Generate summary of alerts"""
        if not alerts:
            return {
                "total_alerts": 0,
                "by_severity": {},
                "status": "no_alerts",
            }

        severity_counts = {}
        for alert in alerts:
            severity = alert["severity"]
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # Determine overall status
        if severity_counts.get("critical", 0) > 0:
            status = "critical"
        elif severity_counts.get("high", 0) > 0:
            status = "high_priority"
        elif severity_counts.get("medium", 0) > 0:
            status = "monitor"
        else:
            status = "low_priority"

        return {
            "total_alerts": len(alerts),
            "by_severity": severity_counts,
            "status": status,
            "alerts": alerts,
        }

