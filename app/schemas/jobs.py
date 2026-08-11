"""
Background job submission schemas
"""
from typing import Any, Dict, Literal

from pydantic import BaseModel, Field

# Keep in sync with the handlers registered in app/api/v1/endpoints/jobs.py
JobType = Literal["report", "inference", "mri_processing"]


class JobSubmitRequest(BaseModel):
    """Schema for POST /jobs"""

    type: JobType = Field(..., description="Which registered job handler to run")
    params: Dict[str, Any] = Field(default_factory=dict)
