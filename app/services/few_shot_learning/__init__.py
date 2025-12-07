"""
Few-Shot Learning Module
ماژول Few-Shot Learning برای تشخیص زیرگونه‌های نادر
"""
from app.services.few_shot_learning.prototypical_networks import (
    PrototypicalNetwork,
    FewShotTask
)
from app.services.few_shot_learning.transfer_learning import (
    TransferLearningOptimizer
)
from app.services.few_shot_learning.few_shot_service import (
    FewShotLearningService
)

__all__ = [
    "PrototypicalNetwork",
    "FewShotTask",
    "TransferLearningOptimizer",
    "FewShotLearningService",
]

