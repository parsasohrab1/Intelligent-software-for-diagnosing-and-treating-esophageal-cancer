"""
Performance analysis and optimization
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.core.mongodb import get_mongodb_database
from app.core.security.audit_logger import AuditLogger


class PerformanceAnalyzer:
    """Analyze system performance"""

    def __init__(self):
        self.db = get_mongodb_database()
        self.audit_logger = AuditLogger()
        self.performance_collection = self.db["performance_metrics"] if self.db is not None else None

    def analyze_api_performance(self, hours: int = 24) -> Dict:
        """Analyze API performance"""
        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()

        logs = self.audit_logger.get_audit_logs(
            event_type="user_action", start_date=cutoff_time, limit=10000
        )

        if not logs:
            return {"message": "No data available"}

        # Analyze response times (if available in logs)
        response_times = []
        endpoint_counts = {}

        for log in logs:
            if "response_time" in log:
                response_times.append(log["response_time"])

            endpoint = log.get("resource_type", "unknown")
            endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1

        analysis = {
            "period_hours": hours,
            "total_requests": len(logs),
            "endpoint_distribution": endpoint_counts,
        }

        if response_times:
            import statistics

            analysis["response_times"] = {
                "avg": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "min": min(response_times),
                "max": max(response_times),
                "p95": statistics.quantiles(response_times, n=20)[18]
                if len(response_times) > 20
                else max(response_times),
            }

        return analysis

    def identify_bottlenecks(self, days: int = 7) -> List[Dict]:
        """Identify performance bottlenecks"""
        cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()

        logs = self.audit_logger.get_audit_logs(start_date=cutoff_time, limit=10000)

        # Group by endpoint and calculate average response time
        endpoint_performance = {}

        for log in logs:
            endpoint = log.get("resource_type", "unknown")
            response_time = log.get("response_time", 0)

            if endpoint not in endpoint_performance:
                endpoint_performance[endpoint] = {
                    "count": 0,
                    "total_time": 0,
                    "max_time": 0,
                }

            endpoint_performance[endpoint]["count"] += 1
            endpoint_performance[endpoint]["total_time"] += response_time
            endpoint_performance[endpoint]["max_time"] = max(
                endpoint_performance[endpoint]["max_time"], response_time
            )

        bottlenecks = []

        for endpoint, perf in endpoint_performance.items():
            avg_time = (
                perf["total_time"] / perf["count"] if perf["count"] > 0 else 0
            )

            if avg_time > 1.0 or perf["max_time"] > 5.0:  # Thresholds
                bottlenecks.append(
                    {
                        "endpoint": endpoint,
                        "avg_response_time": avg_time,
                        "max_response_time": perf["max_time"],
                        "request_count": perf["count"],
                        "severity": "high" if avg_time > 2.0 else "medium",
                    }
                )

        return sorted(bottlenecks, key=lambda x: x["avg_response_time"], reverse=True)

    def get_performance_recommendations(self) -> List[Dict]:
        """Get performance optimization recommendations"""
        bottlenecks = self.identify_bottlenecks()

        recommendations = []

        for bottleneck in bottlenecks:
            if bottleneck["severity"] == "high":
                recommendations.append(
                    {
                        "type": "optimization",
                        "priority": "high",
                        "endpoint": bottleneck["endpoint"],
                        "recommendation": f"Optimize {bottleneck['endpoint']} endpoint - avg response time: {bottleneck['avg_response_time']:.2f}s",
                        "suggestions": [
                            "Add caching",
                            "Optimize database queries",
                            "Consider async processing",
                        ],
                    }
                )

        # General recommendations
        recommendations.append(
            {
                "type": "general",
                "priority": "medium",
                "recommendation": "Enable Redis caching for frequently accessed data",
            }
        )

        recommendations.append(
            {
                "type": "general",
                "priority": "medium",
                "recommendation": "Review and optimize database indexes",
            }
        )

        return recommendations

    def track_performance_metrics(self, metrics: Dict):
        """Track performance metrics"""
        metrics["timestamp"] = datetime.now().isoformat()
        self.performance_collection.insert_one(metrics)

