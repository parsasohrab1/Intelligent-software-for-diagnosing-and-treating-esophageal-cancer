"""
Production Model Monitoring
نظارت پیشرفته بر مدل‌ها در محیط تولید
"""
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import numpy as np
import pandas as pd

from app.core.config import settings
from app.services.model_registry import ModelRegistry
from app.services.mlops.model_monitoring import ModelMonitoring

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """سطح هشدار"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MonitoringAlert:
    """هشدار نظارت"""
    alert_id: str
    model_id: str
    alert_type: str
    level: AlertLevel
    message: str
    timestamp: datetime
    details: Dict
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class ProductionModelMonitoring:
    """نظارت پیشرفته بر مدل‌ها در تولید"""

    def __init__(self):
        self.registry = ModelRegistry()
        self.monitoring = ModelMonitoring()
        self.alerts: List[MonitoringAlert] = []

    def monitor_production_models(self) -> Dict:
        """
        نظارت بر تمام مدل‌های تولید
        
        Returns:
            Dict with monitoring results for all production models
        """
        results = {}
        
        # Get all production models
        production_models = self.registry.get_production_models()
        
        for model in production_models:
            model_id = model["model_id"]
            results[model_id] = self.monitor_single_model(model_id)
        
        return results

    def monitor_single_model(self, model_id: str) -> Dict:
        """
        نظارت بر یک مدل
        
        Returns:
            Dict with comprehensive monitoring results
        """
        try:
            # Get basic monitoring status
            monitoring_status = self.monitoring.get_monitoring_status(model_id)
            
            # Enhanced monitoring checks
            checks = {
                "data_drift": self._check_data_drift_advanced(model_id),
                "model_performance": self._check_model_performance(model_id),
                "prediction_distribution": self._check_prediction_distribution(model_id),
                "feature_importance_drift": self._check_feature_importance_drift(model_id),
                "equipment_changes": self._check_equipment_changes(model_id),
                "population_changes": self._check_population_changes(model_id),
            }
            
            # Generate alerts if needed
            alerts = self._generate_alerts(model_id, checks, monitoring_status)
            
            return {
                "model_id": model_id,
                "monitoring_status": monitoring_status,
                "checks": checks,
                "alerts": [a.__dict__ for a in alerts],
                "overall_health": self._calculate_health_score(checks),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error monitoring model {model_id}: {str(e)}")
            return {
                "model_id": model_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _check_data_drift_advanced(self, model_id: str) -> Dict:
        """بررسی پیشرفته Data Drift"""
        try:
            # Get baseline statistics
            model_info = self.registry.get_model(model_id)
            baseline_stats = model_info.get("baseline_statistics", {})
            
            if not baseline_stats:
                return {"status": "unknown", "reason": "No baseline statistics"}
            
            # Get recent predictions
            recent_data = self.monitoring.get_recent_predictions(model_id, limit=1000)
            
            if len(recent_data) < 100:
                return {"status": "insufficient_data", "count": len(recent_data)}
            
            # Advanced drift detection
            drift_features = []
            for feature_name in baseline_stats.keys():
                baseline_mean = baseline_stats[feature_name].get("mean")
                baseline_std = baseline_stats[feature_name].get("std")
                
                if baseline_mean is None or baseline_std is None:
                    continue
                
                # Get recent values
                recent_values = [p["features"].get(feature_name) for p in recent_data if p["features"].get(feature_name) is not None]
                
                if len(recent_values) < 30:
                    continue
                
                recent_mean = np.mean(recent_values)
                recent_std = np.std(recent_values)
                
                # Calculate drift score
                mean_drift = abs(recent_mean - baseline_mean) / baseline_std if baseline_std > 0 else 0
                std_drift = abs(recent_std - baseline_std) / baseline_std if baseline_std > 0 else 0
                
                drift_score = max(mean_drift, std_drift)
                
                if drift_score > settings.DATA_DRIFT_THRESHOLD:
                    drift_features.append({
                        "feature": feature_name,
                        "drift_score": float(drift_score),
                        "baseline_mean": float(baseline_mean),
                        "recent_mean": float(recent_mean),
                        "baseline_std": float(baseline_std),
                        "recent_std": float(recent_std)
                    })
            
            return {
                "status": "drift_detected" if drift_features else "no_drift",
                "drift_features": drift_features,
                "drift_count": len(drift_features)
            }
            
        except Exception as e:
            logger.error(f"Error checking data drift: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _check_model_performance(self, model_id: str) -> Dict:
        """بررسی عملکرد مدل"""
        try:
            # Get model metrics
            model_info = self.registry.get_model(model_id)
            baseline_metrics = model_info.get("metrics", {})
            baseline_accuracy = baseline_metrics.get("accuracy", 0)
            
            # Get recent performance (if ground truth available)
            recent_performance = self.monitoring.get_recent_performance(model_id, limit=1000)
            
            if len(recent_performance) < 50:
                return {"status": "insufficient_data", "count": len(recent_performance)}
            
            # Calculate current accuracy
            correct = sum(1 for p in recent_performance if abs(p["prediction"] - p["ground_truth"]) < 0.5)
            current_accuracy = correct / len(recent_performance) if recent_performance else 0
            
            # Check for decay
            accuracy_decay = baseline_accuracy - current_accuracy
            
            return {
                "status": "decay_detected" if accuracy_decay > settings.MODEL_DECAY_THRESHOLD else "stable",
                "baseline_accuracy": float(baseline_accuracy),
                "current_accuracy": float(current_accuracy),
                "accuracy_decay": float(accuracy_decay),
                "samples": len(recent_performance)
            }
            
        except Exception as e:
            logger.error(f"Error checking model performance: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _check_prediction_distribution(self, model_id: str) -> Dict:
        """بررسی توزیع پیش‌بینی‌ها"""
        try:
            recent_predictions = self.monitoring.get_recent_predictions(model_id, limit=1000)
            
            if len(recent_predictions) < 100:
                return {"status": "insufficient_data"}
            
            predictions = [p["prediction"] for p in recent_predictions]
            
            return {
                "status": "ok",
                "mean": float(np.mean(predictions)),
                "std": float(np.std(predictions)),
                "min": float(np.min(predictions)),
                "max": float(np.max(predictions)),
                "samples": len(predictions)
            }
            
        except Exception as e:
            logger.error(f"Error checking prediction distribution: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _check_feature_importance_drift(self, model_id: str) -> Dict:
        """بررسی تغییر در اهمیت ویژگی‌ها"""
        try:
            # This would compare feature importance from training vs current
            # For now, return placeholder
            return {
                "status": "not_implemented",
                "note": "Feature importance drift detection not yet implemented"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _check_equipment_changes(self, model_id: str) -> Dict:
        """بررسی تغییرات در تجهیزات تصویربرداری"""
        try:
            # Get metadata from recent predictions
            recent_data = self.monitoring.get_recent_predictions(model_id, limit=1000)
            
            if len(recent_data) < 100:
                return {"status": "insufficient_data"}
            
            # Check for equipment metadata in predictions
            equipment_ids = set()
            for pred in recent_data:
                equipment_id = pred.get("metadata", {}).get("equipment_id")
                if equipment_id:
                    equipment_ids.add(equipment_id)
            
            return {
                "status": "ok",
                "unique_equipment_count": len(equipment_ids),
                "equipment_ids": list(equipment_ids),
                "note": "Multiple equipment detected" if len(equipment_ids) > 1 else "Single equipment"
            }
            
        except Exception as e:
            logger.error(f"Error checking equipment changes: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _check_population_changes(self, model_id: str) -> Dict:
        """بررسی تغییرات در جمعیت بیماران"""
        try:
            recent_data = self.monitoring.get_recent_predictions(model_id, limit=1000)
            
            if len(recent_data) < 100:
                return {"status": "insufficient_data"}
            
            # Analyze patient demographics
            ages = []
            genders = []
            
            for pred in recent_data:
                features = pred.get("features", {})
                if "age" in features:
                    ages.append(features["age"])
                if "gender" in features:
                    genders.append(features["gender"])
            
            return {
                "status": "ok",
                "age_distribution": {
                    "mean": float(np.mean(ages)) if ages else None,
                    "std": float(np.std(ages)) if ages else None,
                    "min": float(np.min(ages)) if ages else None,
                    "max": float(np.max(ages)) if ages else None
                },
                "gender_distribution": {
                    "counts": {g: genders.count(g) for g in set(genders)} if genders else {}
                },
                "samples": len(recent_data)
            }
            
        except Exception as e:
            logger.error(f"Error checking population changes: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _generate_alerts(self, model_id: str, checks: Dict, monitoring_status: Dict) -> List[MonitoringAlert]:
        """تولید هشدارها بر اساس بررسی‌ها"""
        alerts = []
        
        # Data drift alert
        if checks["data_drift"]["status"] == "drift_detected":
            alerts.append(MonitoringAlert(
                alert_id=f"alert_{model_id}_{datetime.now().timestamp()}",
                model_id=model_id,
                alert_type="data_drift",
                level=AlertLevel.WARNING,
                message=f"Data drift detected in {checks['data_drift']['drift_count']} features",
                timestamp=datetime.now(),
                details=checks["data_drift"]
            ))
        
        # Model decay alert
        if checks["model_performance"]["status"] == "decay_detected":
            decay = checks["model_performance"]["accuracy_decay"]
            level = AlertLevel.CRITICAL if decay > 0.1 else AlertLevel.WARNING
            alerts.append(MonitoringAlert(
                alert_id=f"alert_{model_id}_{datetime.now().timestamp()}",
                model_id=model_id,
                alert_type="model_decay",
                level=level,
                message=f"Model performance decay detected: {decay:.2%}",
                timestamp=datetime.now(),
                details=checks["model_performance"]
            ))
        
        # Equipment change alert
        if checks["equipment_changes"]["unique_equipment_count"] > 1:
            alerts.append(MonitoringAlert(
                alert_id=f"alert_{model_id}_{datetime.now().timestamp()}",
                model_id=model_id,
                alert_type="equipment_change",
                level=AlertLevel.INFO,
                message=f"Multiple equipment detected: {checks['equipment_changes']['unique_equipment_count']}",
                timestamp=datetime.now(),
                details=checks["equipment_changes"]
            ))
        
        return alerts

    def _calculate_health_score(self, checks: Dict) -> float:
        """محاسبه امتیاز سلامت مدل"""
        score = 1.0
        
        # Deduct for data drift
        if checks["data_drift"]["status"] == "drift_detected":
            score -= 0.2
        
        # Deduct for model decay
        if checks["model_performance"]["status"] == "decay_detected":
            decay = checks["model_performance"].get("accuracy_decay", 0)
            score -= min(0.3, decay)
        
        return max(0.0, score)

    def get_alerts(self, model_id: Optional[str] = None, level: Optional[AlertLevel] = None) -> List[Dict]:
        """دریافت هشدارها"""
        alerts = self.alerts
        
        if model_id:
            alerts = [a for a in alerts if a.model_id == model_id]
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        return [
            {
                "alert_id": a.alert_id,
                "model_id": a.model_id,
                "alert_type": a.alert_type,
                "level": a.level.value,
                "message": a.message,
                "timestamp": a.timestamp.isoformat(),
                "details": a.details,
                "resolved": a.resolved
            }
            for a in alerts
        ]

