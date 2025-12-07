"""
Model Versioning and Rollback
مدیریت نسخه‌های مدل و قابلیت Rollback
"""
import logging
from typing import Dict, Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from app.services.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


class ModelStatus(str, Enum):
    """وضعیت مدل"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"
    ROLLED_BACK = "rolled_back"


@dataclass
class ModelVersion:
    """نسخه مدل"""
    version_id: str
    model_id: str
    version_number: str  # Semantic versioning: major.minor.patch
    model_path: str
    metrics: Dict
    trained_at: datetime
    deployed_at: Optional[datetime]
    status: ModelStatus
    parent_version: Optional[str] = None  # Version this was based on
    changelog: Optional[str] = None


class ModelVersioning:
    """مدیریت نسخه‌های مدل"""

    def __init__(self):
        self.registry = ModelRegistry()
        self.versions: Dict[str, List[ModelVersion]] = {}  # model_id -> versions

    def create_version(
        self,
        model_id: str,
        model_path: str,
        metrics: Dict,
        version_number: Optional[str] = None,
        parent_version: Optional[str] = None,
        changelog: Optional[str] = None
    ) -> ModelVersion:
        """
        ایجاد نسخه جدید از مدل
        
        Args:
            model_id: شناسه مدل
            model_path: مسیر فایل مدل
            metrics: معیارهای مدل
            version_number: شماره نسخه (اگر None، به صورت خودکار تولید می‌شود)
            parent_version: نسخه والد
            changelog: تغییرات
            
        Returns:
            ModelVersion object
        """
        # Generate version number if not provided
        if version_number is None:
            existing_versions = self.get_versions(model_id)
            if existing_versions:
                # Increment patch version
                last_version = existing_versions[-1].version_number
                parts = last_version.split(".")
                if len(parts) == 3:
                    major, minor, patch = parts
                    patch = str(int(patch) + 1)
                    version_number = f"{major}.{minor}.{patch}"
                else:
                    version_number = "1.0.0"
            else:
                version_number = "1.0.0"
        
        version_id = f"{model_id}_v{version_number}"
        
        version = ModelVersion(
            version_id=version_id,
            model_id=model_id,
            version_number=version_number,
            model_path=model_path,
            metrics=metrics,
            trained_at=datetime.now(),
            deployed_at=None,
            status=ModelStatus.DEVELOPMENT,
            parent_version=parent_version,
            changelog=changelog
        )
        
        # Store version
        if model_id not in self.versions:
            self.versions[model_id] = []
        self.versions[model_id].append(version)
        
        logger.info(f"Created version {version_number} for model {model_id}")
        
        return version

    def get_versions(self, model_id: str) -> List[ModelVersion]:
        """دریافت تمام نسخه‌های یک مدل"""
        return self.versions.get(model_id, [])

    def get_current_production_version(self, model_id: str) -> Optional[ModelVersion]:
        """دریافت نسخه تولید فعلی"""
        versions = self.get_versions(model_id)
        for version in reversed(versions):  # Check from newest
            if version.status == ModelStatus.PRODUCTION:
                return version
        return None

    def promote_to_staging(self, version_id: str) -> bool:
        """ارتقا به staging"""
        version = self._find_version(version_id)
        if not version:
            return False
        
        version.status = ModelStatus.STAGING
        logger.info(f"Promoted version {version_id} to staging")
        return True

    def promote_to_production(self, version_id: str) -> bool:
        """ارتقا به production"""
        version = self._find_version(version_id)
        if not version:
            return False
        
        # Archive current production version
        current_prod = self.get_current_production_version(version.model_id)
        if current_prod:
            current_prod.status = ModelStatus.ARCHIVED
        
        # Promote new version
        version.status = ModelStatus.PRODUCTION
        version.deployed_at = datetime.now()
        
        # Update registry
        self.registry.set_production_model(version.model_id)
        
        logger.info(f"Promoted version {version_id} to production")
        return True

    def rollback_to_version(self, version_id: str) -> bool:
        """
        Rollback به نسخه قبلی
        
        Args:
            version_id: شناسه نسخه برای rollback
            
        Returns:
            True if successful
        """
        version = self._find_version(version_id)
        if not version:
            logger.error(f"Version {version_id} not found")
            return False
        
        # Get current production
        current_prod = self.get_current_production_version(version.model_id)
        if current_prod:
            current_prod.status = ModelStatus.ROLLED_BACK
        
        # Rollback to specified version
        version.status = ModelStatus.PRODUCTION
        version.deployed_at = datetime.now()
        
        # Update registry
        self.registry.set_production_model(version.model_id)
        
        logger.info(f"Rolled back to version {version_id}")
        return True

    def rollback_to_previous(self, model_id: str) -> Optional[ModelVersion]:
        """
        Rollback به نسخه قبلی (last production version)
        
        Returns:
            Version that was rolled back to, or None
        """
        versions = self.get_versions(model_id)
        
        # Find current production
        current_prod = None
        previous_prod = None
        
        for i, version in enumerate(reversed(versions)):
            if version.status == ModelStatus.PRODUCTION:
                current_prod = version
                # Find previous production version
                for j in range(i + 1, len(versions)):
                    if versions[-(j+1)].status == ModelStatus.ARCHIVED:
                        previous_prod = versions[-(j+1)]
                        break
                break
        
        if not current_prod or not previous_prod:
            logger.error("No previous production version found for rollback")
            return None
        
        # Rollback
        current_prod.status = ModelStatus.ROLLED_BACK
        previous_prod.status = ModelStatus.PRODUCTION
        previous_prod.deployed_at = datetime.now()
        
        # Update registry
        self.registry.set_production_model(model_id)
        
        logger.info(f"Rolled back from {current_prod.version_number} to {previous_prod.version_number}")
        return previous_prod

    def _find_version(self, version_id: str) -> Optional[ModelVersion]:
        """یافتن نسخه بر اساس version_id"""
        for versions_list in self.versions.values():
            for version in versions_list:
                if version.version_id == version_id:
                    return version
        return None

    def get_version_history(self, model_id: str) -> List[Dict]:
        """دریافت تاریخچه نسخه‌ها"""
        versions = self.get_versions(model_id)
        
        return [
            {
                "version_id": v.version_id,
                "version_number": v.version_number,
                "status": v.status.value,
                "trained_at": v.trained_at.isoformat(),
                "deployed_at": v.deployed_at.isoformat() if v.deployed_at else None,
                "metrics": v.metrics,
                "changelog": v.changelog,
                "parent_version": v.parent_version
            }
            for v in versions
        ]

