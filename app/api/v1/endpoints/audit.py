"""
Audit logging endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.core.security.audit_logger import AuditLogger
from app.core.security.rbac import Role, Permission
from app.core.security.auth import get_current_user

router = APIRouter()
audit_logger = AuditLogger()


@router.get("/logs")
async def get_audit_logs(
    user_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    current_user: dict = Depends(get_current_user),
):
    """Get audit logs (requires READ_AUDIT_LOGS permission)"""
    # Check permission
    user_role = Role(current_user["payload"].get("role", "data_scientist"))
    from app.core.security.rbac import AccessControlManager

    access_control = AccessControlManager()
    if Permission.READ_AUDIT_LOGS not in access_control.get_user_permissions(user_role):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    logs = audit_logger.get_audit_logs(
        user_id=user_id,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

    return {"logs": logs, "count": len(logs)}


@router.get("/logs/user/{user_id}/summary")
async def get_user_activity_summary(
    user_id: str,
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
):
    """Get user activity summary"""
    # Check permission
    user_role = Role(current_user["payload"].get("role", "data_scientist"))
    from app.core.security.rbac import AccessControlManager

    access_control = AccessControlManager()
    if Permission.READ_AUDIT_LOGS not in access_control.get_user_permissions(user_role):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    summary = audit_logger.get_user_activity_summary(user_id, days=days)
    return summary


@router.post("/logs/security-event")
async def log_security_event(
    event_type: str,
    severity: str,
    description: str,
    current_user: dict = Depends(get_current_user),
):
    """Log a security event"""
    audit_logger.log_security_event(
        event_type=event_type,
        severity=severity,
        description=description,
        user_id=current_user["payload"].get("sub"),
    )

    return {"message": "Security event logged"}

