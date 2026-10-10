"""
Real Estate Management System - FastAPI Application

12-Factor App Compliance:
- Factor 6: Processes (stateless, no session affinity)
- Factor 7: Port binding (self-contained HTTP service)
- Factor 9: Disposability (graceful startup/shutdown)
- Factor 11: Logs (structured logging to stdout)
"""
import logging
import re
import signal
import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.exc import OperationalError

from app.config.settings import settings
from app.config.logging_config import setup_logging, get_logger
from app.database.database import engine
from app.models.base import Base
from app.middleware.security_headers import SecurityHeadersMiddleware
# FIX: added PlatformSettings so Base.metadata.create_all() (the dev-only
# INIT_DB path below) creates this table too, matching the new
# 0013_create_platform_settings migration used in production.
from app.models import (
    User, Property, PropertyMedia, VerificationEvidence, OwnerExpense, ProviderInvoice, ProviderRating, Favorite, Inquiry, Unit, Lease, Payment, Maintenance,
    Notification, PlatformSettings, RentalApplication, Viewing, Lead,
    Conversation, ServiceProviderProfile, VerificationRecord, AuditLog, InspectionRecord, EmailVerification,
    PasswordResetToken, PasswordHistory, RecoveryCode, SmsChallenge,
    ConsentRecord, DataDeletionRequest, EmailPreference
)
from app.routers import (
    auth, users, properties, favorites, inquiries, admin, manager, units,
    leases, payments, maintenance, notifications, viewings, applications,
    leads, communications, service_marketplace, verifications, audit_logs,
    owner, agent, tenant, buildings, property_media, property_tours, companies, companies,
    email_verification, password_reset, mfa, privacy, reports, analytics
)
from app.observability.metrics import snapshot, timed_call
from app.services.rate_limiter import allow_request

# Initialize logging (12-factor: logs to stdout)
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_format=settings.LOG_FORMAT,
    app_name=settings.APP_NAME,
    log_to_file=settings.LOG_TO_FILE,
    log_file_path=settings.LOG_FILE_PATH,
)

logger = get_logger(__name__)


# ============================================================================
# STARTUP & SHUTDOWN EVENTS (Factor 9: Disposability)
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle application startup and shutdown gracefully.
    
    Startup: Initialize database, migrations, logging
    Shutdown: Close connections, cleanup resources
    
    Factor 9: Disposability - Fast startup, graceful shutdown
    Factor 11: Logs - Log lifecycle events
    """
    # ---- STARTUP ----
    logger.info(
        "Application Starting",
        extra={
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "version": settings.APP_VERSION,
        }
    )

    try:
        # Create database tables only in development when explicitly enabled.
        # Production MUST use Alembic migrations instead of create_all().
        # To initialize a local dev DB set: ENVIRONMENT=development and INIT_DB=true
        init_db = os.getenv("INIT_DB", "false").lower() == "true"
        if settings.is_development and init_db:
            logger.info("INIT_DB detected: Initializing database (development only)...")
            Base.metadata.create_all(bind=engine)
            logger.info("Database initialized (development)")
        else:
            logger.info("Skipping automatic DB creation; use Alembic migrations for schema changes.")

    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        raise

    yield

    # ---- SHUTDOWN ----
    logger.info("Application Shutting Down - Cleaning up resources...")
    try:
        from app.database.database import replica_engine
        engine.dispose()
        if replica_engine is not engine:
            replica_engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}", exc_info=True)


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan  # 12-factor: graceful startup/shutdown
)


# ============================================================================
# MIDDLEWARE (Factor 4: Backing Services - Structured for cloud)
# ============================================================================

# CORS Middleware
# For development, allow specific origins. In production, use environment variables.
cors_origins = settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://127.0.0.1:5173", "http://127.0.0.1:5174", "http://127.0.0.1:5175", "http://[::1]:5173", "http://[::1]:5174", "http://[::1]:5175"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Security Headers Middleware
# Adds OWASP-recommended security headers to all responses
app.add_middleware(SecurityHeadersMiddleware)


# Request Logging Middleware (Factor 11: Logs as event streams)
# Every request gets a correlation ID (echoed back via X-Request-ID) so a log
# line, a security event, and an error report can be tied to one request.
_INCOMING_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests and responses for debugging and monitoring."""
    incoming_id = request.headers.get("x-request-id")
    request_id = (
        incoming_id
        if incoming_id and _INCOMING_REQUEST_ID_RE.fullmatch(incoming_id)
        else uuid.uuid4().hex[:16]
    )
    request.state.request_id = request_id

    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)

    level = logging.DEBUG
    if response.status_code >= 500:
        level = logging.ERROR
    elif response.status_code >= 400:
        level = logging.WARNING
    logger.log(
        level,
        f"{request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else "unknown",
            "status": response.status_code,
            "duration_ms": duration_ms,
            "request_id": request_id,
        }
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.middleware("http")
async def request_resource_middleware(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.MAX_REQUEST_BODY_BYTES:
        return JSONResponse(status_code=413, content={"detail": "Request body is too large"})
    if request.url.path not in {"/health/live", "/health/ready"}:
        try:
            allowed = await allow_request(request)
        except Exception:
            logger.error("Rate-limit backend unavailable", exc_info=True)
            return JSONResponse(status_code=503, content={"detail": "Request protection is unavailable"})
        if not allowed:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
    return await timed_call(request, call_next)


# ============================================================================
# API VERSIONING
# Canonical prefix is /api/v1. Legacy /api/* requests are transparently
# rewritten to /api/v1 and flagged with Deprecation/Sunset headers so clients
# can detect and migrate. See SECURITY_IMPROVEMENTS.md for the policy.
# ============================================================================

API_V1_PREFIX = "/api/v1"
LEGACY_API_SUNSET = "Wed, 01 Sep 2027 00:00:00 GMT"
NON_API_PATHS = ("/docs", "/redoc", "/openapi.json", "/health", "/favicon.ico", "/media")


@app.middleware("http")
async def api_versioning_middleware(request: Request, call_next):
    path = request.scope.get("path", "")

    if path.startswith(API_V1_PREFIX) or path == "/" or path.startswith(NON_API_PATHS):
        return await call_next(request)

    if path.startswith("/api/"):
        # Legacy versioned-style call: /api/auth/login -> /api/v1/auth/login
        request.scope["path"] = API_V1_PREFIX + path[len("/api"):]
    elif path != "/" and not path.startswith(NON_API_PATHS):
        # Un-prefixed call: /auth/login -> /api/v1/auth/login
        request.scope["path"] = API_V1_PREFIX + path

    response = await call_next(request)
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = LEGACY_API_SUNSET
    response.headers["X-API-Version"] = "legacy; migrate to /api/v1"
    return response


# ============================================================================
# HEALTH CHECK ENDPOINTS (Factor 9: Disposability)
# Used by container orchestrators (Docker, Kubernetes) for:
# - Liveness probe: Is the container alive?
# - Readiness probe: Is the container ready to accept traffic?
# ============================================================================

@app.get("/health/live", tags=["health"])
async def liveness_probe():
    """
    Liveness probe for container orchestrators.
    
    Returns 200 if the application is alive (even if not ready).
    Used by Kubernetes/Docker for restart decisions.
    
    12-Factor: Factor 9 (Disposability)
    """
    return {"status": "alive"}


@app.get("/health/ready", tags=["health"])
async def readiness_probe():
    """
    Readiness probe for container orchestrators.
    
    Returns 200 only if the application is ready to handle traffic.
    Checks: Database connectivity, dependencies available
    
    Used by Kubernetes/Docker for load balancer decisions.
    
    12-Factor: Factor 4 (Backing Services), Factor 9 (Disposability)
    """
    try:
        # Check database connectivity
        with engine.connect() as connection:
            pass
        
        return {
            "status": "ready",
            "environment": settings.ENVIRONMENT,
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "reason": "Database unavailable"
            }
        )


@app.get("/health/metrics", tags=["health"])
async def metrics():
    return snapshot()


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint - API information.
    """
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "online",
        "api_prefix": "/api/v1",
        "docs": "/docs",
        "health": "/health/live"
    }


# ============================================================================
# UPLOADED FILE SERVING
# Files were magic-byte validated at upload and stored under random names,
# so only generated names of the form <32-hex>.<ext> are ever resolvable.
# ============================================================================

@app.get("/media/uploads/{stored_name}", tags=["media"])
async def serve_upload(stored_name: str):
    from app.utils.file_validation import is_safe_stored_filename, media_type_for_stored_filename

    if not is_safe_stored_filename(stored_name):
        return JSONResponse(status_code=404, content={"detail": "File not found"})

    file_path = settings.upload_root / stored_name
    if not file_path.is_file():
        return JSONResponse(status_code=404, content={"detail": "File not found"})

    return FileResponse(
        file_path,
        media_type=media_type_for_stored_filename(stored_name),
        headers={
            "Content-Disposition": "inline",
            "X-Content-Type-Options": "nosniff",
            # Stored names are random 32-hex values that are never reused, so
            # browsers/CDNs can cache them essentially forever.
            "Cache-Control": "public, max-age=31536000, immutable",
        },
    )


# ============================================================================
# ROUTERS (API Routes)
# ============================================================================

app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(users.router, prefix="/api/v1", tags=["users"])
app.include_router(properties.router, prefix="/api/v1", tags=["properties"])
app.include_router(favorites.router, prefix="/api/v1", tags=["favorites"])
app.include_router(inquiries.router, prefix="/api/v1", tags=["inquiries"])
app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
app.include_router(manager.router, prefix="/api/v1", tags=["manager"])
app.include_router(units.router, prefix="/api/v1", tags=["units"])
app.include_router(leases.router, prefix="/api/v1", tags=["leases"])
app.include_router(payments.router, prefix="/api/v1", tags=["payments"])
app.include_router(maintenance.router, prefix="/api/v1", tags=["maintenance"])
app.include_router(notifications.router, prefix="/api/v1", tags=["notifications"])
app.include_router(viewings.router, prefix="/api/v1", tags=["viewings"])
app.include_router(applications.router, prefix="/api/v1", tags=["applications"])
app.include_router(leads.router, prefix="/api/v1", tags=["leads"])
app.include_router(communications.router, prefix="/api/v1", tags=["communications"])
app.include_router(service_marketplace.router, prefix="/api/v1", tags=["service-marketplace"])
app.include_router(verifications.router, prefix="/api/v1", tags=["verifications"])
app.include_router(audit_logs.router, prefix="/api/v1", tags=["audit-logs"])
app.include_router(owner.router, prefix="/api/v1", tags=["owner"])
app.include_router(agent.router, prefix="/api/v1", tags=["agent"])
app.include_router(tenant.router, prefix="/api/v1", tags=["tenant"])
app.include_router(buildings.router, prefix="/api/v1", tags=["buildings"])
app.include_router(property_media.router, prefix="/api/v1", tags=["property-media"])
app.include_router(property_tours.router, prefix="/api/v1", tags=["property-tours"])
app.include_router(companies.router, prefix="/api/v1", tags=["companies"])
app.include_router(email_verification.router, prefix="/api/v1", tags=["email-verification"])
app.include_router(password_reset.router, prefix="/api/v1", tags=["auth"])
app.include_router(mfa.router, prefix="/api/v1", tags=["auth"])
app.include_router(privacy.router, prefix="/api/v1", tags=["privacy"])
app.include_router(reports.router, prefix="/api/v1", tags=["reports"])
app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions with structured logging."""
    logger.error(
        f"Unhandled exception: {type(exc).__name__}",
        exc_info=exc,
        extra={
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    # Database connection details must not be sent to browsers, even in
    # development; they can contain usernames, hosts, and authentication data.
    if settings.is_production or isinstance(exc, OperationalError):
        return JSONResponse(
            status_code=500,
            content={"detail": "The backend database is unavailable." if isinstance(exc, OperationalError) else "Internal server error"}
        )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "type": type(exc).__name__
        }
    )


if __name__ == "__main__":
    # This is only for development with `python app/main.py`
    # In production, use: uvicorn app.main:app --workers 4
    import uvicorn
    
    logger.info(f"Starting development server on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL,
    )