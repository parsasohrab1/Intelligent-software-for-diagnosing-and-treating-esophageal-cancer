"""
Main FastAPI application for INEsCape
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager
from datetime import datetime

from app.core.config import settings
from app.core.database import init_db
from app.api.v1.router import api_router
from app.middleware.security_middleware import SecurityMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware
from app.middleware.performance_middleware import PerformanceMiddleware
from app.core.exceptions import INEsCapeException
from fastapi.exceptions import RequestValidationError
from fastapi import Request


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for the application"""
    # Startup
    try:
        await init_db()
    except Exception as e:
        # Log error but don't crash the app
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Database initialization failed: {e}")
        logger.warning("App will continue but database operations may fail")
    yield
    # Shutdown
    pass


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Integrated Nano-Theranostic Platform for Esophageal Cancer Management",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# Performance monitoring middleware (first to track all requests)
app.add_middleware(PerformanceMiddleware)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Security middleware
app.add_middleware(SecurityMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix=settings.API_PREFIX)


# Exception handlers
@app.exception_handler(INEsCapeException)
async def inescape_exception_handler(request: Request, exc: INEsCapeException):
    """Handle INEsCape custom exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code or "ERROR",
            "detail": exc.detail,
            "path": str(request.url.path),
        },
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "detail": "Validation failed",
            "errors": errors,
            "path": str(request.url.path),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions, with special handling for dashboard GET endpoints"""
    import traceback
    import logging
    from sqlalchemy.exc import OperationalError, DisconnectionError, SQLAlchemyError
    from pymongo.errors import PyMongoError
    
    logger = logging.getLogger(__name__)
    
    path = str(request.url.path)
    is_dashboard_endpoint = any([
        "/api/v1/patients" in path,
        "/api/v1/data-collection/metadata/statistics" in path,
        "/api/v1/ml-models/models" in path,
        "/api/v1/imaging/mri" in path,
        "/api/v1/cds/services" in path,
    ])
    
    # Check if it's a database/MongoDB error or any error on dashboard endpoints
    is_db_error = isinstance(exc, (OperationalError, DisconnectionError, SQLAlchemyError, PyMongoError))
    
    if is_db_error:
        logger.warning(f"Database/MongoDB error in {path}: {exc}")
    else:
        logger.error(f"Error in {path}: {exc}")
        logger.error(traceback.format_exc())
    
    # For GET endpoints on dashboard, return empty arrays/defaults instead of 500
    if request.method == "GET" and is_dashboard_endpoint:
        logger.warning(f"Returning empty/default response for dashboard endpoint {path} due to error")
        
        # Return appropriate empty responses for dashboard endpoints
        if "/api/v1/patients" in path or path.endswith("/patients/"):
            return JSONResponse(status_code=200, content=[])
        elif "/api/v1/data-collection/metadata/statistics" in path:
            return JSONResponse(status_code=200, content={
                "total_datasets": 0,
                "by_source": {},
                "by_data_type": {},
            })
        elif "/api/v1/ml-models/models" in path:
            return JSONResponse(status_code=200, content={"models": [], "count": 0})
        elif "/api/v1/imaging/mri" in path:
            return JSONResponse(status_code=200, content=[])
        elif "/api/v1/cds/services" in path:
            # CDS services should always work - return the services list
            return JSONResponse(status_code=200, content={
                "services": [
                    {
                        "name": "Risk Prediction",
                        "id": "risk-prediction",
                        "description": "Predict risk of esophageal cancer development",
                        "endpoint": "/cds/risk-prediction"
                    },
                    {
                        "name": "Treatment Recommendation",
                        "id": "treatment-recommendation",
                        "description": "Recommend treatment based on patient characteristics",
                        "endpoint": "/cds/treatment-recommendation"
                    },
                    {
                        "name": "Prognostic Scoring",
                        "id": "prognostic-score",
                        "description": "Calculate prognostic score for patient",
                        "endpoint": "/cds/prognostic-score"
                    },
                    {
                        "name": "Nanosystem Design",
                        "id": "nanosystem-design",
                        "description": "Suggest personalized nanosystem design",
                        "endpoint": "/cds/nanosystem-design"
                    },
                    {
                        "name": "Clinical Trial Matching",
                        "id": "clinical-trial-match",
                        "description": "Match patient to clinical trials",
                        "endpoint": "/cds/clinical-trial-match"
                    },
                    {
                        "name": "Monitoring Alerts",
                        "id": "monitoring-alerts",
                        "description": "Check for monitoring alerts",
                        "endpoint": "/cds/monitoring-alerts"
                    }
                ],
                "count": 6
            })
    
    # Log the error for non-dashboard endpoints
    if not is_dashboard_endpoint:
        logger.error(f"Unhandled exception: {exc}")
        logger.error(traceback.format_exc())
    
    # Print to console in debug mode
    if settings.DEBUG:
        print(f"\n{'='*60}")
        print(f"ERROR: Unhandled exception in {path}")
        print(f"{'='*60}")
        traceback.print_exc()
        print(f"{'='*60}\n")
    
    # Return safe error response for non-dashboard endpoints
    try:
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "detail": "An internal server error occurred",
                "path": path,
            } if not settings.DEBUG else {
                "error": "INTERNAL_SERVER_ERROR",
                "detail": str(exc),
                "path": path,
                "traceback": traceback.format_exc(),
            },
        )
    except Exception as e:
        # If even JSONResponse fails, return plain text
        logger.error(f"Failed to create error response: {e}")
        from fastapi.responses import Response
        return Response(
            content=f"Internal Server Error: {str(exc)}",
            status_code=500,
            media_type="text/plain"
        )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to INEsCape API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }
    )


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint for Kubernetes (legacy - use /api/v1/health/readiness)"""
    from app.core.health_check import HealthCheckService
    
    health_service = HealthCheckService()
    readiness = health_service.get_readiness()
    
    status_code = 200 if readiness["status"] == "ready" else 503
    
    return JSONResponse(
        content=readiness,
        status_code=status_code
    )


@app.get("/live")
async def liveness_check():
    """Liveness check endpoint for Kubernetes (legacy - use /api/v1/health/liveness)"""
    from app.core.health_check import HealthCheckService
    
    health_service = HealthCheckService()
    liveness = health_service.get_liveness()
    
    return JSONResponse(
        content=liveness,
        status_code=200
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )

