"""
Security dependencies for FastAPI endpoints
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security.auth import get_current_user, decode_token
from app.core.security.rbac import Role, Permission, AccessControlManager
from app.core.security.consent_manager import ConsentManager, ConsentType
from app.core.security.data_masking import DataMasking
from app.core.security.audit_logger import AuditLogger
from app.models.user import User
from app.models.patient import Patient


# Initialize managers
access_control = AccessControlManager()
data_masking = DataMasking()
audit_logger = AuditLogger()


def get_current_user_with_role(
    token: str = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user with full user object
    
    Returns:
        User object
    """
    user_data = get_current_user(token, db)
    username = user_data.get("username")
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # Fetch user from database
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user


def require_permission(permission: Permission):
    """
    Dependency factory to require specific permission
    
    Usage:
        @router.get("/patients")
        async def get_patients(
            current_user: User = Depends(require_permission(Permission.READ_DEIDENTIFIED))
        ):
            ...
    """
    def permission_checker(current_user: User = Depends(get_current_user_with_role)):
        user_permissions = access_control.get_user_permissions(current_user.role)
        
        if permission not in user_permissions:
            # Log unauthorized access attempt
            audit_logger.log_security_event(
                event_type="unauthorized_access_attempt",
                severity="high",
                description=f"User {current_user.username} attempted to access resource requiring {permission.value}",
                user_id=current_user.user_id
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission.value}"
            )
        
        return current_user
    
    return permission_checker


def require_role(*allowed_roles: Role):
    """
    Dependency factory to require specific role(s)
    
    Usage:
        @router.get("/admin")
        async def admin_endpoint(
            current_user: User = Depends(require_role(Role.SYSTEM_ADMINISTRATOR))
        ):
            ...
    """
    def role_checker(current_user: User = Depends(get_current_user_with_role)):
        if current_user.role not in allowed_roles:
            audit_logger.log_security_event(
                event_type="unauthorized_role_access",
                severity="high",
                description=f"User {current_user.username} with role {current_user.role.value} attempted to access role-restricted resource",
                user_id=current_user.user_id
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to roles: {[r.value for r in allowed_roles]}"
            )
        
        return current_user
    
    return role_checker


def check_patient_access(
    patient_id: str,
    current_user: User = Depends(get_current_user_with_role),
    db: Session = Depends(get_db)
) -> Patient:
    """
    Check if user has access to patient data and return patient
    
    Args:
        patient_id: Patient identifier
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Patient object
        
    Raises:
        HTTPException: If patient not found or access denied
    """
    # Get patient
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Check access permissions
    can_access = access_control.can_access_resource(
        current_user.role,
        "patient_data",
        patient_id
    )
    
    if not can_access:
        # Log unauthorized access attempt
        audit_logger.log_security_event(
            event_type="unauthorized_patient_access",
            severity="high",
            description=f"User {current_user.username} attempted to access patient {patient_id} without permission",
            user_id=current_user.user_id
        )
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to patient data"
        )
    
    # Check consent (for non-admin roles)
    if current_user.role not in [Role.SYSTEM_ADMINISTRATOR, Role.MEDICAL_ONCOLOGIST]:
        consent_manager = ConsentManager(db)
        has_consent = consent_manager.check_consent(
            patient_id,
            ConsentType.DATA_PROCESSING
        )
        
        if not has_consent:
            # Log access without consent
            audit_logger.log_security_event(
                event_type="access_without_consent",
                severity="medium",
                description=f"User {current_user.username} accessed patient {patient_id} data without consent",
                user_id=current_user.user_id
            )
    
    # Log data access
    audit_logger.log_data_access(
        user_id=current_user.user_id,
        dataset_id=patient_id,
        access_type="patient_data_read",
        query_params={"patient_id": patient_id}
    )
    
    return patient


def get_masked_patient_data(
    patient: Patient,
    current_user: User,
    db: Session
) -> dict:
    """
    Get patient data with appropriate masking based on user role
    
    Args:
        patient: Patient object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Masked patient data dictionary
    """
    # Convert patient to dict
    patient_dict = {
        "patient_id": patient.patient_id,
        "age": patient.age,
        "gender": patient.gender,
        "ethnicity": patient.ethnicity,
        "has_cancer": patient.has_cancer,
        "cancer_type": patient.cancer_type,
        "cancer_subtype": patient.cancer_subtype,
        "created_at": patient.created_at.isoformat() if patient.created_at else None,
        "updated_at": patient.updated_at.isoformat() if patient.updated_at else None,
    }
    
    # Check consent
    consent_manager = ConsentManager(db)
    has_consent = consent_manager.check_consent(
        patient.patient_id,
        ConsentType.DATA_PROCESSING
    )
    
    # Apply masking based on role and consent
    masked_data = data_masking.mask_patient_data(
        patient_dict,
        current_user.role,
        has_consent
    )
    
    return masked_data

