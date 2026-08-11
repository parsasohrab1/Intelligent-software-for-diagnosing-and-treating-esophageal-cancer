"""
Maintenance / issue-tracker schemas
"""
from pydantic import BaseModel, Field

from app.services.maintenance.issue_tracker import IssuePriority, IssueType


class IssueCreateRequest(BaseModel):
    """Schema for POST /maintenance/issues"""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=5000)
    issue_type: IssueType
    priority: IssuePriority = IssuePriority.MEDIUM


class IssueCommentRequest(BaseModel):
    """Schema for POST /maintenance/issues/{issue_id}/comments"""

    comment: str = Field(..., min_length=1, max_length=2000)
