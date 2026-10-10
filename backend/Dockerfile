# ============================================================================
# DOCKERFILE - 12-Factor App Compliant
# ============================================================================
# 
# 12-Factor Principles Implemented:
# - Factor 2 (Dependencies): All Python packages in requirements.txt
# - Factor 3 (Config): All config from environment variables
# - Factor 7 (Port Binding): Self-contained, PORT env var configurable
# - Factor 9 (Disposability): Fast startup, graceful shutdown via signals
# - Factor 11 (Logs): Logs to stdout for container orchestrators
# 
# Build:
#   docker build -t real-estate-api:latest .
#
# Run:
#   docker run -e DATABASE_URL=... -e SECRET_KEY=... -p 8000:8000 real-estate-api
#
# ============================================================================

# Stage 1: Builder
# ============================================================================
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies only (will be removed in final image)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt


# Stage 2: Runtime
# ============================================================================
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install only runtime dependencies (much smaller image)
# postgresql-client-16 comes from the PGDG repo: pg_dump refuses to dump a server
# of a newer major version, so the client must match the PostgreSQL server major.
# Change "16" here together with docker-compose.yml if you upgrade the server.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    ca-certificates \
    gnupg \
    && curl -fsS https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.gpg \
    && echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.gpg] https://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update && apt-get install -y --no-install-recommends postgresql-client-16 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security (12-factor: principle of least privilege)
RUN useradd -m -u 1000 appuser

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Set environment variables for Python
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Switch to non-root user (security best practice)
USER appuser

# Expose port (configurable via PORT env var at runtime)
EXPOSE 8000

# Health check (Docker/Kubernetes can monitor container health)
# Factor 9: Disposability - Quick startup/shutdown detection
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Copy and install an entrypoint script to handle release/run/admin
COPY --chown=appuser:appuser entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Entrypoint: use the script to separate release (migrations) from run
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["run"]
