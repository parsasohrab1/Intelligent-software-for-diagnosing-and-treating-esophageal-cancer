"""
Job status and result API.
Endpoints: POST /api/v1/jobs (submit job), GET /api/v1/jobs/{job_id} (status and result).
"""
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.services.job_store import (
    STATUS_DONE,
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_RUNNING,
    create_job,
    get_job,
    run_job,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ----- Default job handlers (can be extended) -----
def _handler_report(job_id: str, params: Dict[str, Any]) -> None:
    """Placeholder: heavy report job. Replace with real report generation."""
    from app.services.job_store import set_job_done, set_job_failed
    import time
    try:
        # Simulate work; replace with actual report generation
        time.sleep(2)
        set_job_done(job_id, {"message": "Report job completed (placeholder)", "params": params})
    except Exception as e:
        set_job_failed(job_id, str(e))


def _handler_inference(job_id: str, params: Dict[str, Any]) -> None:
    """Placeholder: ML inference job. Replace with actual model inference."""
    from app.services.job_store import set_job_done, set_job_failed
    import time
    try:
        time.sleep(1)
        set_job_done(job_id, {"message": "Inference job completed (placeholder)", "params": params})
    except Exception as e:
        set_job_failed(job_id, str(e))


def _handler_mri_processing(job_id: str, params: Dict[str, Any]) -> None:
    """Placeholder: MRI processing job. Replace with actual image processing + optional queue publish."""
    from app.services.job_store import set_job_done, set_job_failed
    import time
    try:
        time.sleep(1)
        # Optional: publish to message queue for downstream consumers
        try:
            from app.services.messaging import get_message_queue
            mq = get_message_queue()
            if mq:
                mq.publish("imaging_data", {"job_id": job_id, "type": "mri_processing", **params})
        except Exception:
            pass
        set_job_done(job_id, {"message": "MRI processing job completed (placeholder)", "params": params})
    except Exception as e:
        set_job_failed(job_id, str(e))


# Register default handlers
from app.services import job_store as _job_store_module  # noqa: E402
_job_store_module.register_handler("report", _handler_report)
_job_store_module.register_handler("inference", _handler_inference)
_job_store_module.register_handler("mri_processing", _handler_mri_processing)


@router.post("")
def submit_job(
    body: Dict[str, Any],
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Submit a job. Returns job_id. Poll GET /jobs/{job_id} for status and result.
    Body: { "type": "report" | "inference" | "mri_processing", "params": { ... } }
    """
    job_type = body.get("type") or "report"
    params = body.get("params")
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise HTTPException(status_code=400, detail="params must be an object")
    job_id = create_job(job_type, params)
    background_tasks.add_task(run_job, job_id, job_type, params)
    return {"job_id": job_id, "type": job_type, "status": STATUS_PENDING}


@router.get("/{job_id}")
def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get job status and result.
    status: pending | running | done | failed
    """
    record = get_job(job_id)
    if not record:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": record["job_id"],
        "type": record.get("type", "unknown"),
        "status": record.get("status", STATUS_PENDING),
        "result": record.get("result"),
        "error": record.get("error"),
        "created_at": record.get("created_at"),
        "updated_at": record.get("updated_at"),
    }
