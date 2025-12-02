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
    await init_db()
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
    """Handle general exceptions"""
    import traceback
    
    # Log the error (in production, use proper logging)
    if settings.DEBUG:
        traceback.print_exc()
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "detail": "An internal server error occurred",
            "path": str(request.url.path),
        } if not settings.DEBUG else {
            "error": "INTERNAL_SERVER_ERROR",
            "detail": str(exc),
            "path": str(request.url.path),
            "traceback": traceback.format_exc(),
        },
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

