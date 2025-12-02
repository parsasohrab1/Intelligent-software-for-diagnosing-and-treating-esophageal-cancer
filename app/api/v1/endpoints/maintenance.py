"""
Maintenance and monitoring endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.core.security.auth import get_current_user
from app.core.security.rbac import Role, Permission, AccessControlManager
from app.services.maintenance.system_monitor import SystemMonitor
from app.services.maintenance.issue_tracker import (
    IssueTracker,
    IssueType,
    IssuePriority,
    IssueStatus,
)
from app.services.maintenance.performance_analyzer import PerformanceAnalyzer

router = APIRouter()
system_monitor = SystemMonitor()
issue_tracker = IssueTracker()
performance_analyzer = PerformanceAnalyzer()
access_control = AccessControlManager()


@router.get("/health")
async def get_system_health(
    hours: int = Query(24, ge=1, le=168),
    current_user: dict = Depends(get_current_user),
):
    """Get system health status"""
    # Check permission
    user_role = Role(current_user["payload"].get("role", "data_scientist"))
    if Permission.READ_AUDIT_LOGS not in access_control.get_user_permissions(user_role):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    health = system_monitor.get_system_health(hours=hours)
    return health


@router.post("/metrics/collect")
async def collect_metrics(current_user: dict = Depends(get_current_user)):
    """Collect current system metrics"""
    user_role = Role(current_user["payload"].get("role", "data_scientist"))
    if user_role != Role.SYSTEM_ADMINISTRATOR:
        raise HTTPException(status_code=403, detail="Admin access required")

    metrics = system_monitor.collect_metrics()
    return metrics


@router.get("/performance/analysis")
async def get_performance_analysis(
    hours: int = Query(24, ge=1, le=168),
    current_user: dict = Depends(get_current_user),
):
    """Get performance analysis"""
    user_role = Role(current_user["payload"].get("role", "data_scientist"))
    if Permission.READ_AUDIT_LOGS not in access_control.get_user_permissions(user_role):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    analysis = performance_analyzer.analyze_api_performance(hours=hours)
    return analysis


@router.get("/performance/bottlenecks")
async def get_bottlenecks(
    days: int = Query(7, ge=1, le=30),
    current_user: dict = Depends(get_current_user),
):
    """Identify performance bottlenecks"""
    user_role = Role(current_user["payload"].get("role", "data_scientist"))
    if user_role != Role.SYSTEM_ADMINISTRATOR:
        raise HTTPException(status_code=403, detail="Admin access required")

    bottlenecks = performance_analyzer.identify_bottlenecks(days=days)
    return {"bottlenecks": bottlenecks, "count": len(bottlenecks)}


@router.get("/performance/recommendations")
async def get_recommendations(current_user: dict = Depends(get_current_user)):
    """Get performance optimization recommendations"""
    user_role = Role(current_user["payload"].get("role", "data_scientist"))
    if user_role != Role.SYSTEM_ADMINISTRATOR:
        raise HTTPException(status_code=403, detail="Admin access required")

    recommendations = performance_analyzer.get_performance_recommendations()
    return {"recommendations": recommendations, "count": len(recommendations)}


@router.post("/issues")
async def create_issue(
    title: str,
    description: str,
    issue_type: IssueType,
    priority: IssuePriority = IssuePriority.MEDIUM,
    current_user: dict = Depends(get_current_user),
):
    """Create a new issue"""
    issue_id = issue_tracker.create_issue(
        title=title,
        description=description,
        issue_type=issue_type,
        priority=priority,
        reporter=current_user["payload"].get("sub"),
    )
    return {"issue_id": issue_id, "message": "Issue created successfully"}


@router.get("/issues")
async def list_issues(
    status: Optional[IssueStatus] = None,
    priority: Optional[IssuePriority] = None,
    issue_type: Optional[IssueType] = None,
    limit: int = Query(100, le=1000),
    current_user: dict = Depends(get_current_user),
):
    """List issues"""
    issues = issue_tracker.list_issues(
        status=status, priority=priority, issue_type=issue_type, limit=limit
    )
    return {"issues": issues, "count": len(issues)}


@router.get("/issues/{issue_id}")
async def get_issue(issue_id: str, current_user: dict = Depends(get_current_user)):
    """Get issue details"""
    issue = issue_tracker.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.patch("/issues/{issue_id}/status")
async def update_issue_status(
    issue_id: str,
    status: IssueStatus,
    current_user: dict = Depends(get_current_user),
):
    """Update issue status"""
    success = issue_tracker.update_issue_status(
        issue_id, status, updated_by=current_user["payload"].get("sub")
    )
    if not success:
        raise HTTPException(status_code=404, detail="Issue not found")
    return {"message": "Issue status updated"}


@router.post("/issues/{issue_id}/comments")
async def add_comment(
    issue_id: str,
    comment: str,
    current_user: dict = Depends(get_current_user),
):
    """Add comment to issue"""
    success = issue_tracker.add_comment(
        issue_id, comment, author=current_user["payload"].get("sub")
    )
    if not success:
        raise HTTPException(status_code=404, detail="Issue not found")
    return {"message": "Comment added"}


@router.get("/issues/statistics")
async def get_issue_statistics(current_user: dict = Depends(get_current_user)):
    """Get issue statistics"""
    stats = issue_tracker.get_issue_statistics()
    return stats

