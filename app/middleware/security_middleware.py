"""
Security middleware
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
from app.core.security.audit_logger import AuditLogger

audit_logger = AuditLogger()


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for request logging and validation"""

    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # Start time
        start_time = time.time()

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error
            audit_logger.log_security_event(
                event_type="request_error",
                severity="medium",
                description=f"Error processing request: {str(e)}",
                ip_address=client_ip,
            )
            raise

        # Calculate processing time
        process_time = time.time() - start_time

        # Log slow requests
        if process_time > 5.0:
            audit_logger.log_security_event(
                event_type="slow_request",
                severity="low",
                description=f"Slow request: {request.url.path} took {process_time:.2f}s",
                ip_address=client_ip,
            )

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response

