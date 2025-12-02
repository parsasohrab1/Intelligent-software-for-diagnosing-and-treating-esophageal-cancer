"""
Health check endpoints
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.health_check import HealthCheckService

router = APIRouter()
health_service = HealthCheckService()


@router.get("/")
async def health():
    """Basic health check - quick response for load balancers"""
    return {
        "status": "ok",
        "service": "inescape-api"
    }


@router.get("/liveness")
async def liveness():
    """Kubernetes liveness probe - is the application running?"""
    return health_service.get_liveness()


@router.get("/readiness")
async def readiness():
    """Kubernetes readiness probe - is the application ready to serve traffic?"""
    return health_service.get_readiness()


@router.get("/detailed")
async def detailed_health(
    include_disk: bool = Query(False, description="Include disk space check")
):
    """Comprehensive health check with all services"""
    return health_service.get_comprehensive_health(include_disk=include_disk)


@router.get("/service/{service_name}")
async def check_service(service_name: str):
    """Check specific service health"""
    service_checks = {
        "postgresql": health_service.check_postgresql,
        "mongodb": health_service.check_mongodb,
        "redis": health_service.check_redis,
        "cache": health_service.check_cache,
        "disk": health_service.check_disk_space,
    }
    
    if service_name not in service_checks:
        return {
            "status": "error",
            "message": f"Unknown service: {service_name}",
            "available_services": list(service_checks.keys())
        }
    
    return service_checks[service_name]()

