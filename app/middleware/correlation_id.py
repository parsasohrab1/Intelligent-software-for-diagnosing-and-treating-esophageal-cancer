"""
Correlation ID middleware
"""
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging_config import correlation_id_var


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to attach a correlation ID to each request.

    Reads the incoming X-Request-ID header if present, otherwise
    generates a new one. The ID is made available to log statements via
    correlation_id_var for the duration of the request, stashed on
    request.state, and echoed back as a response header.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """Attach a correlation ID to the request context"""
        correlation_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        token = correlation_id_var.set(correlation_id)
        try:
            response = await call_next(request)
        finally:
            correlation_id_var.reset(token)

        response.headers["X-Request-ID"] = correlation_id

        return response
