"""
Issue tracking and bug management
"""
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
from app.core.mongodb import get_mongodb_database


class IssueStatus(str, Enum):
    """Issue status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"


class IssuePriority(str, Enum):
    """Issue priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueType(str, Enum):
    """Issue type"""
    BUG = "bug"
    FEATURE = "feature"
    ENHANCEMENT = "enhancement"
    TASK = "task"
    SUPPORT = "support"


class IssueTracker:
    """Issue tracking system"""

    def __init__(self):
        self.db = get_mongodb_database()
        self.issues_collection = self.db["issues"]

    def create_issue(
        self,
        title: str,
        description: str,
        issue_type: IssueType,
        priority: IssuePriority = IssuePriority.MEDIUM,
        reporter: Optional[str] = None,
        assignee: Optional[str] = None,
    ) -> str:
        """Create a new issue"""
        issue = {
            "issue_id": f"ISSUE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "title": title,
            "description": description,
            "type": issue_type.value,
            "priority": priority.value,
            "status": IssueStatus.OPEN.value,
            "reporter": reporter,
            "assignee": assignee,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "comments": [],
            "attachments": [],
        }

        self.issues_collection.insert_one(issue)
        return issue["issue_id"]

    def get_issue(self, issue_id: str) -> Optional[Dict]:
        """Get issue by ID"""
        issue = self.issues_collection.find_one({"issue_id": issue_id})
        if issue:
            issue["_id"] = str(issue["_id"])
        return issue

    def update_issue_status(
        self, issue_id: str, status: IssueStatus, updated_by: Optional[str] = None
    ) -> bool:
        """Update issue status"""
        result = self.issues_collection.update_one(
            {"issue_id": issue_id},
            {
                "$set": {
                    "status": status.value,
                    "updated_at": datetime.now().isoformat(),
                    "updated_by": updated_by,
                }
            },
        )
        return result.modified_count > 0

    def assign_issue(self, issue_id: str, assignee: str) -> bool:
        """Assign issue to user"""
        result = self.issues_collection.update_one(
            {"issue_id": issue_id},
            {
                "$set": {
                    "assignee": assignee,
                    "updated_at": datetime.now().isoformat(),
                }
            },
        )
        return result.modified_count > 0

    def add_comment(
        self, issue_id: str, comment: str, author: Optional[str] = None
    ) -> bool:
        """Add comment to issue"""
        comment_obj = {
            "comment": comment,
            "author": author,
            "created_at": datetime.now().isoformat(),
        }

        result = self.issues_collection.update_one(
            {"issue_id": issue_id},
            {
                "$push": {"comments": comment_obj},
                "$set": {"updated_at": datetime.now().isoformat()},
            },
        )
        return result.modified_count > 0

    def list_issues(
        self,
        status: Optional[IssueStatus] = None,
        priority: Optional[IssuePriority] = None,
        issue_type: Optional[IssueType] = None,
        assignee: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """List issues with filters"""
        query = {}

        if status:
            query["status"] = status.value
        if priority:
            query["priority"] = priority.value
        if issue_type:
            query["type"] = issue_type.value
        if assignee:
            query["assignee"] = assignee

        issues = (
            self.issues_collection.find(query).sort("created_at", -1).limit(limit)
        )

        return [self._format_issue(issue) for issue in issues]

    def get_issue_statistics(self) -> Dict:
        """Get issue statistics"""
        total = self.issues_collection.count_documents({})
        open_count = self.issues_collection.count_documents(
            {"status": IssueStatus.OPEN.value}
        )
        in_progress_count = self.issues_collection.count_documents(
            {"status": IssueStatus.IN_PROGRESS.value}
        )
        resolved_count = self.issues_collection.count_documents(
            {"status": IssueStatus.RESOLVED.value}
        )

        return {
            "total": total,
            "open": open_count,
            "in_progress": in_progress_count,
            "resolved": resolved_count,
            "closed": self.issues_collection.count_documents(
                {"status": IssueStatus.CLOSED.value}
            ),
        }

    def _format_issue(self, issue: Dict) -> Dict:
        """Format issue for output"""
        if "_id" in issue:
            issue["_id"] = str(issue["_id"])
        return issue

