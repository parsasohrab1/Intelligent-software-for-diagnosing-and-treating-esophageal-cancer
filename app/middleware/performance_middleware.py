"""
Performance monitoring middleware
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
from typing import Dict
from app.core.mongodb import get_mongodb_database


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware to track request performance"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        try:
            self.mongodb = get_mongodb_database()
            if self.mongodb is not None:
                self.performance_collection = self.mongodb["performance_metrics"]
            else:
                self.performance_collection = None
        except Exception:
            # If MongoDB is not available, disable performance tracking
            self.mongodb = None
            self.performance_collection = None
    
    async def dispatch(self, request: Request, call_next):
        """Track request performance"""
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate metrics
        process_time = time.time() - start_time
        
        # Track performance metrics (only if MongoDB is available)
        if self.performance_collection is not None:
            try:
                metrics = {
                    "endpoint": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                    "response_time": round(process_time, 4),
                    "timestamp": time.time(),
                }
                
                # Only log slow requests (> 1 second) or errors
                if process_time > 1.0 or response.status_code >= 400:
                    self.performance_collection.insert_one(metrics)
            except Exception:
                # Don't fail request if metrics logging fails
                pass
        
        # Add performance headers
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        
        return response

