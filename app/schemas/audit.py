"""
Audit logging schemas
"""
from typing import Literal

from pydantic import BaseModel, Field


class SecurityEventRequest(BaseModel):
    """Schema for POST /audit/logs/security-event"""

    event_type: str = Field(..., min_length=1, max_length=100)
    severity: Literal["low", "medium", "high", "critical"]
    description: str = Field(..., min_length=1, max_length=2000)
