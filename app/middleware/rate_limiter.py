"""
Rate limiting middleware for FastAPI
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Dict, Tuple
import time
from collections import defaultdict
from app.core.redis_client import get_redis_client


class RateLimiter:
    """Rate limiter using sliding window algorithm"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.memory_store: Dict[str, list] = defaultdict(list)
        self.use_redis = redis_client is not None
    
    def _get_key(self, identifier: str, endpoint: str) -> str:
        """Generate rate limit key"""
        return f"rate_limit:{identifier}:{endpoint}"
    
    def _check_memory(self, key: str, max_requests: int, window: int) -> Tuple[bool, int]:
        """Check rate limit using in-memory storage"""
        now = time.time()
        requests = self.memory_store[key]
        
        # Remove expired requests
        requests[:] = [req_time for req_time in requests if now - req_time < window]
        
        if len(requests) >= max_requests:
            return False, len(requests)
        
        requests.append(now)
        return True, len(requests)
    
    def _check_redis(self, key: str, max_requests: int, window: int) -> Tuple[bool, int]:
        """Check rate limit using Redis"""
        try:
            redis = self.redis_client or get_redis_client()
            now = time.time()
            
            # Use sorted set for sliding window
            pipe = redis.pipeline()
            pipe.zremrangebyscore(key, 0, now - window)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, window)
            results = pipe.execute()
            
            current_count = results[1]
            
            if current_count >= max_requests:
                return False, current_count
            
            return True, current_count + 1
        except Exception:
            # Fallback to memory if Redis fails
            return self._check_memory(key, max_requests, window)
    
    def check_rate_limit(
        self, 
        identifier: str, 
        endpoint: str, 
        max_requests: int = 100, 
        window: int = 60
    ) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limit
        
        Returns:
            (allowed, current_count, remaining)
        """
        key = self._get_key(identifier, endpoint)
        
        if self.use_redis:
            allowed, count = self._check_redis(key, max_requests, window)
        else:
            allowed, count = self._check_memory(key, max_requests, window)
        
        remaining = max(0, max_requests - count)
        return allowed, count, remaining


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for FastAPI"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.rate_limiter = RateLimiter()
        
        # Rate limit configurations per endpoint
        self.limits = {
            "/api/v1/auth/login": (5, 60),  # 5 requests per minute
            "/api/v1/auth/register": (3, 60),  # 3 requests per minute
            "/api/v1/synthetic-data/generate": (10, 60),  # 10 requests per minute
            "/api/v1/ml-models/train": (5, 300),  # 5 requests per 5 minutes
            "/api/v1/cds/risk-prediction": (100, 60),  # 100 requests per minute
            "default": (100, 60),  # Default: 100 requests per minute
        }
    
    def _get_identifier(self, request: Request) -> str:
        """Get identifier for rate limiting (IP or user ID)"""
        # Try to get user ID from request state (if authenticated)
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"
        
        # Fallback to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def _get_endpoint_key(self, request: Request) -> str:
        """Get endpoint key for rate limiting"""
        path = request.url.path
        
        # Check for exact match
        if path in self.limits:
            return path
        
        # Check for prefix match (API endpoints)
        for endpoint, _ in self.limits.items():
            if endpoint != "default" and path.startswith(endpoint):
                return endpoint
        
        return "default"
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        # Skip rate limiting for health checks (but still add headers)
        is_health_check = request.url.path in ["/health", "/ready", "/api/v1/health"]
        
        if is_health_check:
            response = await call_next(request)
            # Add rate limit headers even for health checks (for testing)
            identifier = self._get_identifier(request)
            endpoint_key = self._get_endpoint_key(request)
            max_requests, window = self.limits.get(endpoint_key, self.limits["default"])
            _, count, remaining = self.rate_limiter.check_rate_limit(
                identifier=identifier,
                endpoint=endpoint_key,
                max_requests=max_requests,
                window=window
            )
            response.headers["X-RateLimit-Limit"] = str(max_requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window)
            return response
        
        identifier = self._get_identifier(request)
        endpoint_key = self._get_endpoint_key(request)
        max_requests, window = self.limits.get(endpoint_key, self.limits["default"])
        
        allowed, current_count, remaining = self.rate_limiter.check_rate_limit(
            identifier=identifier,
            endpoint=endpoint_key,
            max_requests=max_requests,
            window=window
        )
        
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded. Maximum {max_requests} requests per {window} seconds.",
                    "limit": max_requests,
                    "window": window,
                    "retry_after": window,
                },
                headers={
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(int(time.time()) + window),
                    "Retry-After": str(window),
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window)
        
        return response

