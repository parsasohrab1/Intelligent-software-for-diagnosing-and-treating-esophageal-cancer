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
            # Log error (but don't fail if audit logger fails)
            try:
                audit_logger.log_security_event(
                    event_type="request_error",
                    severity="medium",
                    description=f"Error processing request: {str(e)}",
                    ip_address=client_ip,
                )
            except Exception:
                pass  # Don't fail if audit logging fails
            raise

        # Calculate processing time
        process_time = time.time() - start_time

        # Log slow requests (but don't fail if audit logger fails)
        if process_time > 5.0:
            try:
                audit_logger.log_security_event(
                    event_type="slow_request",
                    severity="low",
                    description=f"Slow request: {request.url.path} took {process_time:.2f}s",
                    ip_address=client_ip,
                )
            except Exception:
                pass  # Don't fail if audit logging fails

        # Add comprehensive security headers using utility (but don't fail if it errors)
        try:
            from app.core.security_headers import apply_security_headers
            apply_security_headers(response)
        except Exception:
            # Don't fail if security headers can't be applied
            pass

        return response

