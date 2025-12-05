"""
Audit logging system
"""
from typing import Dict, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.mongodb import get_mongodb_database


class AuditLogger:
    """Comprehensive audit logging system"""

    def __init__(self):
        # Use try-except to prevent hanging if MongoDB is not available
        try:
            self.db = get_mongodb_database()
            self.collection = self.db["audit_logs"] if self.db is not None else None
        except Exception:
            # If MongoDB connection fails, disable audit logging
            self.db = None
            self.collection = None

    def log_data_access(
        self,
        user_id: str,
        dataset_id: str,
        access_type: str,
        query_params: Optional[Dict] = None,
        result_size: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log all data access events"""
        audit_record = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "data_access",
            "user_id": user_id,
            "dataset_id": dataset_id,
            "access_type": access_type,
            "query_params": query_params,
            "result_size": result_size,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

        if self.collection is not None:
            try:
                # Use timeout to prevent hanging
                self.collection.insert_one(audit_record)
                # Check for suspicious patterns (only if insert succeeded)
                self._detect_suspicious_activity(user_id)
            except Exception:
                # Don't fail if MongoDB write fails
                pass

    def log_user_action(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None,
    ):
        """Log user actions"""
        audit_record = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "user_action",
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details,
            "ip_address": ip_address,
        }

        if self.collection is not None:
            try:
                # Use timeout to prevent hanging
                self.collection.insert_one(audit_record)
            except Exception:
                # Don't fail if MongoDB write fails
                pass

    def log_model_usage(
        self,
        user_id: str,
        model_id: str,
        prediction_count: int = 1,
        input_data_hash: Optional[str] = None,
    ):
        """Log model usage"""
        audit_record = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "model_usage",
            "user_id": user_id,
            "model_id": model_id,
            "prediction_count": prediction_count,
            "input_data_hash": input_data_hash,
        }

        if self.collection is not None:
            try:
                # Use timeout to prevent hanging
                self.collection.insert_one(audit_record)
            except Exception:
                # Don't fail if MongoDB write fails
                pass

    def log_security_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
    ):
        """Log security events"""
        audit_record = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "security_event",
            "security_event_type": event_type,
            "severity": severity,
            "description": description,
            "user_id": user_id,
            "ip_address": ip_address,
        }

        if self.collection is not None:
            try:
                # Use timeout to prevent hanging
                self.collection.insert_one(audit_record)
            except Exception:
                # Don't fail if MongoDB write fails
                pass

        # Alert on high severity events
        if severity in ["high", "critical"]:
            self._alert_security_team(audit_record)

    def _detect_suspicious_activity(self, user_id: str):
        """Detect potential data misuse"""
        if self.collection is None:
            return
        
        # Get recent accesses (last 24 hours)
        from datetime import timedelta

        cutoff_time = (datetime.now() - timedelta(hours=24)).isoformat()

        try:
            recent_accesses = list(
                self.collection.find(
                    {
                        "user_id": user_id,
                        "timestamp": {"$gte": cutoff_time},
                        "event_type": "data_access",
                    }
                ).max_time_ms(1000)  # Add timeout to prevent hanging
            )
        except Exception:
            # If query fails, return empty list
            recent_accesses = []

        # Check for excessive access
        if len(recent_accesses) > 1000:
            self.log_security_event(
                event_type="excessive_data_access",
                severity="high",
                description=f"User {user_id} accessed data {len(recent_accesses)} times in 24 hours",
                user_id=user_id,
            )

        # Check for wide data access pattern
        unique_datasets = len(set(access.get("dataset_id") for access in recent_accesses))
        if unique_datasets > 50:
            self.log_security_event(
                event_type="wide_data_access",
                severity="medium",
                description=f"User {user_id} accessed {unique_datasets} different datasets in 24 hours",
                user_id=user_id,
            )

    def _alert_security_team(self, audit_record: Dict):
        """Alert security team (placeholder)"""
        # In production, this would send email/SMS/notification
        print(f"SECURITY ALERT: {audit_record}")

    def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000,
    ) -> List[Dict]:
        """Get audit logs with filters"""
        if self.collection is None:
            return []
        
        query = {}

        if user_id:
            query["user_id"] = user_id

        if event_type:
            query["event_type"] = event_type

        if start_date or end_date:
            query["timestamp"] = {}
            if start_date:
                query["timestamp"]["$gte"] = start_date
            if end_date:
                query["timestamp"]["$lte"] = end_date

        try:
            logs = self.collection.find(query).sort("timestamp", -1).limit(limit).max_time_ms(1000)  # Add timeout
        except Exception:
            # If query fails, return empty list
            logs = []

        return [self._format_log(log) for log in logs]

    def _format_log(self, log: Dict) -> Dict:
        """Format log for output"""
        if "_id" in log:
            log["_id"] = str(log["_id"])
        return log

    def get_user_activity_summary(self, user_id: str, days: int = 30) -> Dict:
        """Get summary of user activity"""
        if self.collection is None:
            return {
                "user_id": user_id,
                "period_days": days,
                "total_events": 0,
                "data_accesses": 0,
                "user_actions": 0,
                "model_usage": 0,
                "unique_datasets": 0,
            }
        
        from datetime import timedelta

        cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()

        try:
            logs = list(
                self.collection.find(
                    {"user_id": user_id, "timestamp": {"$gte": cutoff_time}}
                ).max_time_ms(1000)  # Add timeout to prevent hanging
            )
        except Exception:
            # If query fails, return empty list
            logs = []

        return {
            "user_id": user_id,
            "period_days": days,
            "total_events": len(logs),
            "data_accesses": len([l for l in logs if l.get("event_type") == "data_access"]),
            "user_actions": len([l for l in logs if l.get("event_type") == "user_action"]),
            "model_usage": len([l for l in logs if l.get("event_type") == "model_usage"]),
            "unique_datasets": len(set(l.get("dataset_id") for l in logs if l.get("dataset_id"))),
        }

