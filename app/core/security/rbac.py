"""
Role-Based Access Control (RBAC)
"""
from typing import List, Dict, Optional
from enum import Enum


class Role(str, Enum):
    """User roles"""
    DATA_SCIENTIST = "data_scientist"
    CLINICAL_RESEARCHER = "clinical_researcher"
    MEDICAL_ONCOLOGIST = "medical_oncologist"
    DATA_ENGINEER = "data_engineer"
    SYSTEM_ADMINISTRATOR = "system_administrator"
    ETHICS_COMMITTEE = "ethics_committee"


class Permission(str, Enum):
    """Permissions"""
    # Data permissions
    READ_SYNTHETIC = "read_synthetic"
    READ_DEIDENTIFIED = "read_deidentified"
    READ_ALL = "read_all"
    WRITE_ANNOTATIONS = "write_annotations"
    WRITE_MODELS = "write_models"
    WRITE_ALL = "write_all"
    # Management permissions
    MANAGE_USERS = "manage_users"
    READ_AUDIT_LOGS = "read_audit_logs"
    READ_METADATA = "read_metadata"


class AccessControlManager:
    """Role-based access control manager"""

    # Role to permissions mapping
    ROLE_PERMISSIONS: Dict[Role, List[Permission]] = {
        Role.DATA_SCIENTIST: [
            Permission.READ_SYNTHETIC,
            Permission.READ_DEIDENTIFIED,
            Permission.WRITE_MODELS,
        ],
        Role.CLINICAL_RESEARCHER: [
            Permission.READ_DEIDENTIFIED,
            Permission.READ_SYNTHETIC,
            Permission.WRITE_ANNOTATIONS,
        ],
        Role.MEDICAL_ONCOLOGIST: [
            Permission.READ_DEIDENTIFIED,
            Permission.READ_METADATA,
        ],
        Role.DATA_ENGINEER: [
            Permission.READ_ALL,
            Permission.WRITE_ALL,
        ],
        Role.SYSTEM_ADMINISTRATOR: [
            Permission.READ_ALL,
            Permission.WRITE_ALL,
            Permission.MANAGE_USERS,
            Permission.READ_AUDIT_LOGS,
        ],
        Role.ETHICS_COMMITTEE: [
            Permission.READ_AUDIT_LOGS,
            Permission.READ_METADATA,
        ],
    }

    # Action to permission mapping
    ACTION_PERMISSIONS: Dict[str, Permission] = {
        "view_patient_data": Permission.READ_DEIDENTIFIED,
        "view_full_data": Permission.READ_ALL,
        "view_synthetic_data": Permission.READ_SYNTHETIC,
        "modify_data": Permission.WRITE_ALL,
        "export_data": Permission.READ_DEIDENTIFIED,
        "train_model": Permission.WRITE_MODELS,
        "manage_users": Permission.MANAGE_USERS,
        "view_audit_logs": Permission.READ_AUDIT_LOGS,
    }

    def __init__(self):
        pass

    def check_access(
        self, user_role: Role, resource_type: str, action: str
    ) -> bool:
        """Check if user has permission to perform action"""
        # Get user permissions
        permissions = self.ROLE_PERMISSIONS.get(user_role, [])

        # Get required permission for action
        required_permission = self.ACTION_PERMISSIONS.get(action)

        if required_permission is None:
            return False

        return required_permission in permissions

    def get_user_permissions(self, user_role: Role) -> List[Permission]:
        """Get all permissions for a role"""
        return self.ROLE_PERMISSIONS.get(user_role, [])

    def can_access_resource(
        self, user_role: Role, resource_type: str, resource_id: Optional[str] = None
    ) -> bool:
        """Check if user can access a resource"""
        permissions = self.get_user_permissions(user_role)

        # Define resource access rules
        if resource_type == "synthetic_data":
            return Permission.READ_SYNTHETIC in permissions

        elif resource_type == "real_data":
            return Permission.READ_DEIDENTIFIED in permissions or Permission.READ_ALL in permissions

        elif resource_type == "patient_data":
            return Permission.READ_DEIDENTIFIED in permissions or Permission.READ_ALL in permissions

        elif resource_type == "audit_logs":
            return Permission.READ_AUDIT_LOGS in permissions

        elif resource_type == "metadata":
            return Permission.READ_METADATA in permissions or Permission.READ_ALL in permissions

        return False

    def require_permission(self, permission: Permission):
        """Decorator to require specific permission"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # This would be used with dependency injection
                # user_role = get_current_user_role()
                # if permission not in self.get_user_permissions(user_role):
                #     raise HTTPException(status_code=403, detail="Insufficient permissions")
                return func(*args, **kwargs)
            return wrapper
        return decorator

