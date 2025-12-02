"""
Security headers configuration and utilities
"""
from typing import Dict, Optional
from app.core.config import settings


class SecurityHeadersConfig:
    """Configuration for security headers"""

    @staticmethod
    def get_security_headers(environment: Optional[str] = None) -> Dict[str, str]:
        """
        Get security headers based on environment
        
        Args:
            environment: Environment name (development, staging, production)
            
        Returns:
            Dictionary of security headers
        """
        env = environment or settings.ENVIRONMENT
        
        headers = {
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Prevent clickjacking
            "X-Frame-Options": "DENY",
            
            # XSS Protection (legacy but still useful)
            "X-XSS-Protection": "1; mode=block",
            
            # Content Security Policy
            "Content-Security-Policy": SecurityHeadersConfig._get_csp(env),
            
            # Referrer Policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Permissions Policy
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "accelerometer=()"
            ),
            
            # Cross-Origin Policies
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
            
            # Permitted Cross-Domain Policies
            "X-Permitted-Cross-Domain-Policies": "none",
        }
        
        # HSTS - only in production with HTTPS
        if env == "production":
            headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        return headers

    @staticmethod
    def _get_csp(environment: str) -> str:
        """
        Get Content Security Policy based on environment
        
        Args:
            environment: Environment name
            
        Returns:
            CSP header value
        """
        if environment == "production":
            # Strict CSP for production
            return (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "object-src 'none'; "
                "upgrade-insecure-requests"
            )
        else:
            # More permissive for development (allows Swagger UI)
            return (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' http://localhost:* http://127.0.0.1:* ws://localhost:* ws://127.0.0.1:*; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )

    @staticmethod
    def get_cors_headers() -> Dict[str, str]:
        """Get CORS-related security headers"""
        return {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": (
                "Content-Type, Authorization, X-Requested-With, "
                "Accept, Origin, X-CSRF-Token"
            ),
            "Access-Control-Max-Age": "3600",
        }


def apply_security_headers(response, environment: Optional[str] = None):
    """
    Apply security headers to a response
    
    Args:
        response: FastAPI/Starlette response object
        environment: Optional environment override
    """
    headers = SecurityHeadersConfig.get_security_headers(environment)
    
    for header_name, header_value in headers.items():
        if header_value:
            response.headers[header_name] = header_value
    
    # Remove potentially sensitive headers
    if "X-Powered-By" in response.headers:
        del response.headers["X-Powered-By"]
    if "Server" in response.headers:
        del response.headers["Server"]

