"""
Health check endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.redis_client import get_redis_client
from app.core.mongodb import get_mongodb_database

router = APIRouter()


@router.get("/")
async def health():
    """Basic health check"""
    return {"status": "ok"}


@router.get("/detailed")
async def detailed_health(db: Session = Depends(get_db)):
    """Detailed health check with database connectivity"""
    health_status = {
        "status": "healthy",
        "services": {
            "api": "ok",
            "postgresql": "unknown",
            "mongodb": "unknown",
            "redis": "unknown",
        },
    }

    # Check PostgreSQL
    try:
        db.execute("SELECT 1")
        health_status["services"]["postgresql"] = "ok"
    except Exception as e:
        health_status["services"]["postgresql"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    # Check MongoDB
    try:
        mongodb = get_mongodb_database()
        mongodb.command("ping")
        health_status["services"]["mongodb"] = "ok"
    except Exception as e:
        health_status["services"]["mongodb"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    # Check Redis
    try:
        redis_client = get_redis_client()
        redis_client.ping()
        health_status["services"]["redis"] = "ok"
    except Exception as e:
        health_status["services"]["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    return health_status

