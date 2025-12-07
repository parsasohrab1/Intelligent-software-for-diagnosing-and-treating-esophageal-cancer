"""
Clinical System Integration Module
ماژول یکپارچه‌سازی با سیستم‌های کلینیک
"""
from app.services.integration.pacs_integration import (
    PACSIntegration,
    PACSConnection,
    DICOMService
)
from app.services.integration.endoscopy_integration import (
    EndoscopyIntegration,
    EndoscopyConnection,
    EndoscopySystemType
)
from app.services.integration.ehr_integration import (
    EHRIntegration,
    EHRConnection,
    EHRSystemType
)
from app.services.integration.integration_adapter import (
    IntegrationManager,
    IntegrationAdapter,
    PACSAdapter,
    EndoscopyAdapter,
    EHRAdapter,
    IntegrationType
)

__all__ = [
    # PACS
    "PACSIntegration",
    "PACSConnection",
    "DICOMService",
    # Endoscopy
    "EndoscopyIntegration",
    "EndoscopyConnection",
    "EndoscopySystemType",
    # EHR
    "EHRIntegration",
    "EHRConnection",
    "EHRSystemType",
    # Adapters
    "IntegrationManager",
    "IntegrationAdapter",
    "PACSAdapter",
    "EndoscopyAdapter",
    "EHRAdapter",
    "IntegrationType",
]

