"""
12-Factor App Compliant Configuration

All configuration is loaded from environment variables. 
The .env file is ONLY for local development and should never be committed to version control.

Factor 3: Configuration - All configuration should be stored in environment variables
Factor 10: Dev/prod parity - Use environment variables to maintain consistency across environments
"""
from pathlib import Path
from typing import List, Optional

from pydantic import field_validator, model_validator, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env located at the backend folder next to this package.
# Only used in development; production uses actual environment variables
ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / ".env"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Principles:
    - Factor 3 (Configuration): All configuration stored in environment
    - Factor 4 (Backing Services): Database, Redis, etc. are attached resources
    - Factor 10 (Dev/prod parity): Same code runs everywhere with different env vars
    """

    # Use environment variables; .env only in development
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH) if ENV_PATH.exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    # ==== ENVIRONMENT & DEPLOYMENT ====
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False
    LOG_LEVEL: str = "info"

    # ==== APPLICATION ====
    APP_NAME: str = "Real Estate Management System"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Enterprise-grade real estate property management platform"
    
    # ==== SERVER ====
    HOST: str = "0.0.0.0"  # Listen on all interfaces (12-factor: port binding)  # nosec B104 - intentional default; containers must accept external connections
    PORT: int = 8000
    WORKERS: int = 4  # Number of Uvicorn workers
    
    # ==== DATABASE (Factor 4: Backing Services) ====
    DATABASE_URL: str  # Required: postgresql://user:password@host:5432/dbname
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600  # Recycle connections after 1 hour
    DATABASE_STATEMENT_TIMEOUT_MS: int = 30000
    DATABASE_ECHO: bool = False  # SQL query logging
    SLOW_QUERY_THRESHOLD_MS: int = 500
    TEST_DATABASE_URL: Optional[str] = None
    # Optional read replica: when set, read-only endpoints (public property
    # listing/detail/insights) route through it; unset means reads hit the
    # primary, so local dev and single-node deployments need nothing.
    DATABASE_REPLICA_URL: Optional[str] = None

    # ==== API RESOURCE LIMITS ====
    # This is an infrastructure safeguard, not a business-data limit.
    # Increase it deliberately when clients need larger pages.
    MAX_PAGE_SIZE: int = 500
    MAX_REQUEST_BODY_BYTES: int = 10 * 1024 * 1024
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_PER_MINUTE: int = 120
    REDIS_URL: Optional[str] = None

    # ==== FILE UPLOADS ====
    # Relative to the backend directory; overrides are absolute-friendly via .env
    UPLOAD_DIR: str = "uploads/property_media"
    MAX_UPLOAD_FILE_BYTES: int = 10 * 1024 * 1024  # 10 MB per file
    # Relative paths resolve against the same root as UPLOAD_DIR
    DOCUMENTS_DIR: str = "uploads/documents"

    # ==== PASSWORD RESET & HISTORY ====
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    PASSWORD_HISTORY_LIMIT: int = 5  # block reuse of the last N passwords

    # ==== MFA (TOTP / SMS backup / recovery codes) ====
    MFA_ISSUER_NAME: str = "PropNoxa"
    MFA_TOKEN_EXPIRE_MINUTES: int = 5  # post-password, pre-OTP challenge window
    MFA_SMS_CODE_EXPIRE_MINUTES: int = 5
    MFA_RECOVERY_CODE_COUNT: int = 10
    # When true, admin-role accounts cannot complete login until MFA is enrolled.
    # OFF by default so existing sessions/tests are unaffected; turn ON in production.
    MFA_MANDATORY_FOR_ADMIN: bool = False

    # ==== PAYMENT GATEWAY ====
    # mock: fully working in-process gateway (development/tests only — rejected
    # in production). stripe/paypal/mpesa require provider credentials.
    PAYMENT_GATEWAY: str = "mock"
    # HMAC secret verifying gateway webhook signatures (X-Webhook-Signature).
    # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
    PAYMENT_WEBHOOK_SECRET: Optional[str] = None

    # ==== EMAIL (transactional notifications) ====
    # console: log the email instead of delivering it (safe default for dev/tests).
    # smtp: deliver via SMTP_HOST (works with SES/Mailgun SMTP relays, Mailhog, Gmail).
    EMAIL_BACKEND: str = "console"
    EMAIL_FROM: str = "PropNoxa <no-reply@propnoxa.com>"
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None  # secret: env/.env only, never commit
    SMTP_USE_TLS: bool = True
    SMTP_TIMEOUT_SECONDS: int = 10

    # ==== SMS (MFA backup codes, high-priority alerts) ====
    # console: log the message instead of delivering it (safe default for dev/tests).
    # twilio: fails closed until provider credentials are set (from a secrets manager).
    SMS_BACKEND: str = "console"

    # ==== BACKUPS ====
    BACKUP_DIR: str = "backups/database"
    # Legal/insurance data is long-lived; keep daily dumps a month and never drop below a floor.
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_KEEP_MINIMUM: int = 7
    BACKUP_INTERVAL_HOURS: int = 24
    BACKUP_VERIFY_AFTER_CREATE: bool = True
    # Physical base backups are what WAL replay (point-in-time recovery) starts from.
    BACKUP_PHYSICAL_ENABLED: bool = False
    BACKUP_PHYSICAL_KEEP_COUNT: int = 4
    # Second location for the same dumps (mounted bucket / replicated volume) - off in dev.
    BACKUP_SECONDARY_DIR: Optional[str] = None
    BACKUP_WAL_ARCHIVE_DIR: Optional[str] = None
    # Explicit binary paths when they are not on PATH (e.g. a pinned client version).
    BACKUP_PG_DUMP_PATH: Optional[str] = None
    BACKUP_PG_RESTORE_PATH: Optional[str] = None
    BACKUP_PG_BASEBACKUP_PATH: Optional[str] = None

    # ==== DATA RETENTION (storage limitation) ====
    # Legal/litigation hold: when TRUE, destructive purges of business records
    # (audit logs, notifications) are suspended. Ephemeral auth artifacts
    # (expired one-time tokens) are still purged - they have no evidentiary
    # value and keeping them is a liability.
    LEGAL_HOLD_ENABLED: bool = False
    # Expired/used one-time tokens are purged this many days after expiry.
    RETENTION_TOKEN_GRACE_DAYS: int = 30
    # Audit log entries older than this many days are pruned (0 = keep forever).
    RETENTION_AUDIT_LOG_DAYS: int = 365
    # Read notifications older than this are pruned; unread get double the window.
    RETENTION_NOTIFICATIONS_DAYS: int = 180

    # ==== SECRETS & SECURITY ====
    SECRET_KEY: str  # Required: Use secrets manager in production (e.g., AWS Secrets Manager)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    # Optional dedicated HMAC key for the tamper-evident audit chain. When
    # unset, SECRET_KEY is used. Treat it as write-once: changing it makes
    # every earlier audit entry fail verification (they were keyed with the
    # old value), so production should pin it in the secrets manager.
    AUDIT_CHAIN_SECRET: str = ""
    
    # CORS settings (Factor 10: Dev/prod parity)
    CORS_ORIGINS: List[str] = []
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # ==== HEALTH CHECKS & MONITORING ====
    ENABLE_HEALTH_CHECK: bool = True
    LIVENESS_PROBE_PATH: str = "/health/live"
    READINESS_PROBE_PATH: str = "/health/ready"
    STARTUP_TIMEOUT_SECONDS: int = 30

    # ==== LOGGING (Factor 11: Logs as event streams) ====
    # All logs go to stdout for container orchestration (Kubernetes, Docker, ECS)
    LOG_FORMAT: str = "json"  # json or text
    LOG_TO_FILE: bool = False
    LOG_FILE_PATH: Optional[str] = None

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Ensure environment is one of allowed values."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}, got '{v}'")
        return v

    @field_validator("EMAIL_BACKEND")
    @classmethod
    def validate_email_backend(cls, v: str) -> str:
        """Only console and smtp transports exist; smtp needs a host to be usable."""
        v = v.strip().lower()
        if v not in ("console", "smtp"):
            raise ValueError("EMAIL_BACKEND must be 'console' or 'smtp'")
        return v

    @field_validator("SMS_BACKEND")
    @classmethod
    def validate_sms_backend(cls, v: str) -> str:
        """Only console and twilio transports exist; unknown values fail fast."""
        v = v.strip().lower()
        if v not in ("console", "twilio"):
            raise ValueError("SMS_BACKEND must be 'console' or 'twilio'")
        return v

    @model_validator(mode="after")
    def validate_smtp_config(self) -> "Settings":
        """Fail fast when EMAIL_BACKEND=smtp is selected without a host."""
        if self.EMAIL_BACKEND == "smtp" and not self.SMTP_HOST:
            raise ValueError("SMTP_HOST is required when EMAIL_BACKEND=smtp")
        return self

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        """
        Accept CORS origins as comma-separated string or list.
        
        Examples:
            - ENV: CORS_ORIGINS="http://localhost:3000,http://localhost:5173"
            - Code: CORS_ORIGINS=["http://localhost:3000"]
        """
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        return []

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL is configured."""
        if not v:
            raise ValueError(
                "DATABASE_URL is required. "
                "Set via environment variable or .env file. "
                "Format: postgresql://user:password@host:5432/dbname or sqlite:///./database.db"
            )
        if not v.startswith(("postgresql://", "postgres://", "sqlite:///")):
            raise ValueError(
                f"DATABASE_URL must use PostgreSQL or SQLite. Got: {v[:30]}..."
            )
        # Keep local SQLite development consistent regardless of whether the
        # API is launched from the repository root or the backend directory.
        if v.startswith("sqlite:///./"):
            database_path = (ROOT_DIR / v.removeprefix("sqlite:///./")).resolve()
            return f"sqlite:///{database_path.as_posix()}"
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Ensure SECRET_KEY is properly set."""
        if not v or len(v) < 32:
            raise ValueError(
                "SECRET_KEY is required and must be at least 32 characters. "
                "Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is valid."""
        valid_levels = ["debug", "info", "warning", "error", "critical"]
        if v.lower() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.lower()

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == "development"

    @property
    def upload_root(self) -> Path:
        """Absolute directory where uploaded files are stored."""
        upload_path = Path(self.UPLOAD_DIR)
        if not upload_path.is_absolute():
            upload_path = ROOT_DIR / upload_path
        return upload_path.resolve()

    @property
    def backup_root(self) -> Path:
        """Absolute directory where database backups are written."""
        backup_path = Path(self.BACKUP_DIR)
        if not backup_path.is_absolute():
            backup_path = ROOT_DIR / backup_path
        return backup_path.resolve()

    def _optional_dir(self, value: Optional[str]) -> Optional[Path]:
        if not value:
            return None
        path = Path(value)
        if not path.is_absolute():
            path = ROOT_DIR / path
        return path.resolve()

    @property
    def backup_secondary_root(self) -> Optional[Path]:
        return self._optional_dir(self.BACKUP_SECONDARY_DIR)

    @property
    def backup_wal_archive_root(self) -> Optional[Path]:
        return self._optional_dir(self.BACKUP_WAL_ARCHIVE_DIR)


# Global settings instance
# Raises ValidationError if any required settings are missing
try:
    settings = Settings()
except Exception as e:
    print(f"Configuration Error: {e}")
    raise
