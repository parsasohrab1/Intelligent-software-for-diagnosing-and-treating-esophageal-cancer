"""
Post-deployment system monitoring
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.mongodb import get_mongodb_database
from app.core.redis_client import get_redis_client


class SystemMonitor:
    """Monitor system health and performance"""

    def __init__(self):
        self.db = get_mongodb_database()
        self.monitoring_collection = self.db["system_monitoring"] if self.db is not None else None

    def collect_metrics(self) -> Dict:
        """Collect current system metrics"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "database": self._check_database(),
            "mongodb": self._check_mongodb(),
            "redis": self._check_redis(),
            "api": self._check_api_health(),
        }

        # Store metrics (if MongoDB is available)
        if self.monitoring_collection is not None:
            try:
                self.monitoring_collection.insert_one(metrics)
            except Exception:
                pass  # Don't fail if MongoDB is unavailable

        return metrics

    def _check_database(self) -> Dict:
        """Check PostgreSQL database"""
        try:
            from app.core.database import engine
            with engine.connect() as conn:
                result = conn.execute("SELECT 1")
                result.fetchone()

            return {
                "status": "healthy",
                "response_time_ms": 10,  # Placeholder
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def _check_mongodb(self) -> Dict:
        """Check MongoDB"""
        try:
            db = get_mongodb_database()
            db.admin.command("ping")
            return {
                "status": "healthy",
                "response_time_ms": 5,  # Placeholder
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def _check_redis(self) -> Dict:
        """Check Redis"""
        try:
            redis = get_redis_client()
            start = datetime.now()
            redis.ping()
            elapsed = (datetime.now() - start).total_seconds() * 1000

            return {
                "status": "healthy",
                "response_time_ms": elapsed,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def _check_api_health(self) -> Dict:
        """Check API health"""
        try:
            import requests
            response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def get_system_health(self, hours: int = 24) -> Dict:
        """Get system health summary"""
        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()

        metrics = list(
            self.monitoring_collection.find({"timestamp": {"$gte": cutoff_time}}).sort(
                "timestamp", -1
            )
        )

        if not metrics:
            return {"status": "no_data", "message": "No metrics available"}

        # Calculate health statistics
        total_checks = len(metrics)
        healthy_checks = sum(
            1
            for m in metrics
            if all(
                service.get("status") == "healthy"
                for service in [m.get("database"), m.get("mongodb"), m.get("redis")]
            )
        )

        health_percentage = (healthy_checks / total_checks) * 100 if total_checks > 0 else 0

        return {
            "status": "healthy" if health_percentage > 95 else "degraded",
            "health_percentage": health_percentage,
            "total_checks": total_checks,
            "healthy_checks": healthy_checks,
            "latest_metrics": metrics[0] if metrics else None,
        }

    def get_performance_trends(self, days: int = 7) -> Dict:
        """Get performance trends"""
        cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()

        metrics = list(
            self.monitoring_collection.find({"timestamp": {"$gte": cutoff_time}}).sort(
                "timestamp", 1
            )
        )

        trends = {
            "database": [],
            "mongodb": [],
            "redis": [],
        }

        for metric in metrics:
            if metric.get("database"):
                trends["database"].append(
                    {
                        "timestamp": metric["timestamp"],
                        "response_time": metric["database"].get("response_time_ms", 0),
                    }
                )
            if metric.get("mongodb"):
                trends["mongodb"].append(
                    {
                        "timestamp": metric["timestamp"],
                        "response_time": metric["mongodb"].get("response_time_ms", 0),
                    }
                )
            if metric.get("redis"):
                trends["redis"].append(
                    {
                        "timestamp": metric["timestamp"],
                        "response_time": metric["redis"].get("response_time_ms", 0),
                    }
                )

        return trends

