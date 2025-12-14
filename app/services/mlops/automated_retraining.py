"""
Automated Model Retraining
سیستم آموزش مجدد خودکار مدل‌ها
"""
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import time
import threading

try:
    import schedule
except ImportError:
    schedule = None

from app.core.config import settings
from app.services.mlops.cicd_pipeline import MLModelCICDPipeline
from app.services.mlops.production_monitoring import ProductionModelMonitoring
from app.services.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


class RetrainTrigger(str, Enum):
    """محرک‌های retraining"""
    SCHEDULED = "scheduled"  # زمان‌بندی شده
    DRIFT_DETECTED = "drift_detected"  # تشخیص drift
    DECAY_DETECTED = "decay_detected"  # تشخیص decay
    MANUAL = "manual"  # دستی
    DATA_ACCUMULATION = "data_accumulation"  # تجمع داده


class AutomatedRetraining:
    """سیستم آموزش مجدد خودکار"""

    def __init__(self):
        self.cicd_pipeline = MLModelCICDPipeline()
        self.production_monitoring = ProductionModelMonitoring()
        self.registry = ModelRegistry()
        self.retraining_thread = None
        self.is_running = False
        self.retraining_history: List[Dict] = []

    def start_automated_retraining(self):
        """شروع سیستم retraining خودکار"""
        if schedule is None:
            logger.warning("schedule module not available, automated retraining disabled")
            return
            
        if self.is_running:
            logger.warning("Automated retraining is already running")
            return
        
        self.is_running = True
        
        # Schedule periodic checks
        schedule.every(settings.MONITORING_CHECK_INTERVAL).seconds.do(
            self._check_and_retrain_all_models
        )
        
        # Schedule daily retraining check
        schedule.every().day.at("02:00").do(self._daily_retraining_check)
        
        # Start scheduler thread
        self.retraining_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True
        )
        self.retraining_thread.start()
        
        logger.info("Automated retraining system started")

    def stop_automated_retraining(self):
        """توقف سیستم retraining خودکار"""
        self.is_running = False
        if schedule is not None:
            schedule.clear()
        logger.info("Automated retraining system stopped")

    def _scheduler_loop(self):
        """حلقه scheduler"""
        if schedule is None:
            return
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    def _check_and_retrain_all_models(self):
        """بررسی و retraining تمام مدل‌ها"""
        try:
            production_models = self.registry.get_production_models()
            
            for model in production_models:
                model_id = model["model_id"]
                model_type = model.get("model_type", "Unknown")
                
                # Check retrain conditions
                retrain_check = self.cicd_pipeline.check_retrain_conditions(model_id)
                
                if retrain_check["retrain_required"]:
                    logger.info(
                        f"Retraining required for {model_id}. Reasons: {retrain_check['reasons']}"
                    )
                    
                    # Determine trigger
                    if "data_drift" in retrain_check["reasons"]:
                        trigger = RetrainTrigger.DRIFT_DETECTED
                    elif "model_decay" in retrain_check["reasons"]:
                        trigger = RetrainTrigger.DECAY_DETECTED
                    else:
                        trigger = RetrainTrigger.SCHEDULED
                    
                    # Trigger retraining
                    self.trigger_retraining(model_type, trigger)
                    
        except Exception as e:
            logger.error(f"Error in automated retraining check: {str(e)}")

    def _daily_retraining_check(self):
        """بررسی روزانه برای retraining"""
        logger.info("Running daily retraining check")
        self._check_and_retrain_all_models()

    def trigger_retraining(
        self,
        model_type: str,
        trigger: RetrainTrigger,
        force: bool = False
    ) -> Dict:
        """
        راه‌اندازی retraining
        
        Args:
            model_type: نوع مدل
            trigger: محرک retraining
            force: اگر True، حتی اگر شرایط برقرار نباشد retrain می‌کند
            
        Returns:
            نتیجه retraining
        """
        try:
            logger.info(f"Triggering retraining for {model_type}, trigger: {trigger.value}")
            
            # Run CI/CD pipeline
            pipeline_result = self.cicd_pipeline.run_pipeline(
                model_type=model_type,
                trigger_reason=trigger.value
            )
            
            # Record in history
            retrain_record = {
                "model_type": model_type,
                "trigger": trigger.value,
                "pipeline_id": pipeline_result.pipeline_id,
                "status": pipeline_result.status.value,
                "model_id": pipeline_result.model_id,
                "start_time": pipeline_result.start_time.isoformat(),
                "end_time": pipeline_result.end_time.isoformat() if pipeline_result.end_time else None,
                "error": pipeline_result.error,
                "metrics": pipeline_result.metrics
            }
            
            self.retraining_history.append(retrain_record)
            
            # Keep only last 100 records
            if len(self.retraining_history) > 100:
                self.retraining_history = self.retraining_history[-100:]
            
            return retrain_record
            
        except Exception as e:
            logger.error(f"Error triggering retraining: {str(e)}")
            return {
                "model_type": model_type,
                "trigger": trigger.value,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def get_retraining_history(self, model_type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """دریافت تاریخچه retraining"""
        history = self.retraining_history
        
        if model_type:
            history = [h for h in history if h.get("model_type") == model_type]
        
        return history[-limit:]

    def get_retraining_stats(self) -> Dict:
        """دریافت آمار retraining"""
        total = len(self.retraining_history)
        
        if total == 0:
            return {
                "total_retrainings": 0,
                "successful": 0,
                "failed": 0,
                "by_trigger": {},
                "avg_time_hours": 0
            }
        
        successful = len([h for h in self.retraining_history if h.get("status") == "success"])
        failed = len([h for h in self.retraining_history if h.get("status") == "failed"])
        
        # Count by trigger
        by_trigger = {}
        for h in self.retraining_history:
            trigger = h.get("trigger", "unknown")
            by_trigger[trigger] = by_trigger.get(trigger, 0) + 1
        
        # Calculate average time
        times = []
        for h in self.retraining_history:
            if h.get("start_time") and h.get("end_time"):
                start = datetime.fromisoformat(h["start_time"])
                end = datetime.fromisoformat(h["end_time"])
                times.append((end - start).total_seconds() / 3600)
        
        avg_time = sum(times) / len(times) if times else 0
        
        return {
            "total_retrainings": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0,
            "by_trigger": by_trigger,
            "avg_time_hours": avg_time
        }

