"""
Security Headers Middleware

Implements OWASP-recommended security headers for production deployments.

Headers:
- X-Content-Type-Options: Prevents MIME sniffing
- X-Frame-Options: Prevents clickjacking
- X-XSS-Protection: Enables XSS filtering
- Strict-Transport-Security (HSTS): Enforces HTTPS
- Content-Security-Policy (CSP): Controls resource loading
- Referrer-Policy: Controls referrer information
- Permissions-Policy: Controls browser features
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint

from app.config.settings import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    
    In development, some headers are relaxed to allow easier debugging.
    In production, all security headers are enforced.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # X-Content-Type-Options: Prevents MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options: Prevents clickjacking
        # In development, allow framing for easier testing
        if settings.is_development:
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
        else:
            response.headers["X-Frame-Options"] = "DENY"

        # X-XSS-Protection: Enables XSS filtering (deprecated but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy: Controls referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy: Controls browser features
        # Disable geolocation, camera, microphone by default
        permissions_policy = [
            "geolocation=()",
            "camera=()",
            "microphone=()",
            "payment=()",
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions_policy)

        # Strict-Transport-Security (HSTS): Enforces HTTPS
        # Only in production when HTTPS is configured
        if settings.is_production:
            # 1 year max-age, include subdomains, preload
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Content-Security-Policy (CSP): Controls resource loading
        # In development, more permissive to allow hot-reload and debugging
        # In production, strict policy
        if settings.is_development:
            # Development CSP: Allow inline scripts and eval for debugging
            csp = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
                "style-src 'self' 'unsafe-inline'",
                "img-src 'self' data: blob: https:",
                "font-src 'self' data:",
                "connect-src 'self' ws://localhost:* ws://127.0.0.1:* http://localhost:* http://127.0.0.1:*",
                "frame-ancestors 'self'",
            ]
        else:
            # Production CSP: Strict policy
            csp = [
                "default-src 'self'",
                "script-src 'self'",
                "style-src 'self' 'unsafe-inline'",  # Allow inline styles for some UI libraries
                "img-src 'self' data: blob: https:",
                "font-src 'self' data:",
                f"connect-src 'self' {' '.join(settings.CORS_ORIGINS)}",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
            ]
        
        response.headers["Content-Security-Policy"] = "; ".join(csp)

        # Cache-Control for sensitive endpoints
        # Prevent caching of auth-related responses
        if request.url.path in ["/auth/login", "/auth/register", "/auth/me"]:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response
