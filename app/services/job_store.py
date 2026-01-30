"""
Job store for async job status and result.
In-memory store with optional Redis persistence for job metadata.
"""
import json
import logging
import threading
import time
import uuid
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

# Job status values
STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_FAILED = "failed"

# In-memory store: job_id -> { status, result, error, created_at, type, params, updated_at }
_store: Dict[str, Dict[str, Any]] = {}
_lock = threading.RLock()
# Default TTL for job metadata in Redis (seconds)
JOB_TTL = 86400  # 24 hours


def _redis():
    """Return Redis client or None."""
    try:
        from app.core.redis_client import get_redis_client
        return get_redis_client()
    except Exception:
        return None


def create_job(job_type: str, params: Optional[Dict[str, Any]] = None) -> str:
    """Create a new job record and return job_id."""
    job_id = str(uuid.uuid4())
    now = time.time()
    record = {
        "job_id": job_id,
        "type": job_type,
        "params": params or {},
        "status": STATUS_PENDING,
        "result": None,
        "error": None,
        "created_at": now,
        "updated_at": now,
    }
    with _lock:
        _store[job_id] = record
    # Optional: persist to Redis
    r = _redis()
    if r:
        try:
            key = f"job:{job_id}"
            r.setex(key, JOB_TTL, json.dumps(record, default=str))
        except Exception as e:
            logger.debug("Job store Redis set skipped: %s", e)
    return job_id


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Return job record by id, or None."""
    with _lock:
        if job_id in _store:
            return dict(_store[job_id])
    r = _redis()
    if r:
        try:
            raw = r.get(f"job:{job_id}")
            if raw:
                return json.loads(raw)
        except Exception as e:
            logger.debug("Job store Redis get skipped: %s", e)
    return None


def set_job_running(job_id: str) -> None:
    """Mark job as running."""
    _update_job(job_id, status=STATUS_RUNNING)


def set_job_done(job_id: str, result: Any = None) -> None:
    """Mark job as done with optional result."""
    _update_job(job_id, status=STATUS_DONE, result=result)


def set_job_failed(job_id: str, error: str) -> None:
    """Mark job as failed with error message."""
    _update_job(job_id, status=STATUS_FAILED, error=error)


def _update_job(
    job_id: str,
    status: Optional[str] = None,
    result: Optional[Any] = None,
    error: Optional[str] = None,
) -> None:
    now = time.time()
    with _lock:
        if job_id not in _store:
            _store[job_id] = {
                "job_id": job_id,
                "type": "unknown",
                "params": {},
                "status": STATUS_PENDING,
                "result": None,
                "error": None,
                "created_at": now,
                "updated_at": now,
            }
        rec = _store[job_id]
        if status is not None:
            rec["status"] = status
        if result is not None:
            rec["result"] = result
        if error is not None:
            rec["error"] = error
        rec["updated_at"] = now

    r = _redis()
    if r:
        try:
            key = f"job:{job_id}"
            r.setex(key, JOB_TTL, json.dumps(_store[job_id], default=str))
        except Exception as e:
            logger.debug("Job store Redis update skipped: %s", e)


# Registry of job type -> callable(job_id, params) that runs the job
_job_handlers: Dict[str, Callable[[str, Dict], None]] = {}


def register_handler(job_type: str, handler: Callable[[str, Dict], None]) -> None:
    """Register a handler for a job type. Handler receives (job_id, params)."""
    _job_handlers[job_type] = handler


def run_job(job_id: str, job_type: str, params: Dict) -> None:
    """
    Run job by type and update store. Call this from a background task.
    Handler must call set_job_running/job_done/job_failed.
    """
    handler = _job_handlers.get(job_type)
    if not handler:
        set_job_failed(job_id, f"Unknown job type: {job_type}")
        return
    try:
        set_job_running(job_id)
        handler(job_id, params)
        # If handler did not set done/failed, assume done
        rec = get_job(job_id)
        if rec and rec.get("status") == STATUS_RUNNING:
            set_job_done(job_id, rec.get("result"))
    except Exception as e:
        logger.exception("Job %s failed: %s", job_id, e)
        set_job_failed(job_id, str(e))
