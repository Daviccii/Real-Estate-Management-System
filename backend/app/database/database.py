"""
Database connection and session management.

12-Factor App Compliance:
- Factor 4: Backing Services - Database as external resource
- Factor 3: Configuration - Connection string from environment
- Factor 9: Disposability - Proper connection cleanup
"""
from sqlalchemy import create_engine, event, Engine
from sqlalchemy.exc import TimeoutError as PoolTimeoutError
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool
import logging
import time

from app.config.settings import settings
from app.observability.metrics import increment

logger = logging.getLogger(__name__)


def create_db_engine(url: str = None):
    """
    Create SQLAlchemy engine with 12-factor compliant configuration.

    Production settings:
    - Connection pooling for performance
    - Pool recycling to handle database server restarts
    - SSL support for cloud databases

    Development settings:
    - NullPool (no connection pooling) for simplicity
    """
    target_url = url or settings.DATABASE_URL

    # Use NullPool in development for simplicity (no pooling)
    # Use QueuePool in production for better performance (pooling enabled)
    use_queue_pool = not settings.is_development

    engine_kwargs = {
        "pool_recycle": settings.DATABASE_POOL_RECYCLE,
        "pool_pre_ping": True,
        "echo": settings.DATABASE_ECHO and settings.is_development,
    }

    # Only add PostgreSQL-specific connect_args for PostgreSQL connections
    if target_url.startswith(("postgresql://", "postgres://")):
        engine_kwargs["connect_args"] = {
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
            "options": f"-c statement_timeout={settings.DATABASE_STATEMENT_TIMEOUT_MS}",
        }

    if use_queue_pool:
        # Only include pool sizing arguments when using QueuePool
        engine_kwargs.update({
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_timeout": settings.DATABASE_POOL_TIMEOUT,
            "poolclass": QueuePool,
        })
    else:
        engine_kwargs.update({"poolclass": NullPool})

    engine = create_engine(target_url, **engine_kwargs)

    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        context._query_started_at = time.perf_counter()

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        duration_ms = (time.perf_counter() - context._query_started_at) * 1000
        if duration_ms >= settings.SLOW_QUERY_THRESHOLD_MS:
            logger.warning(
                "Slow database query",
                extra={"duration_ms": round(duration_ms, 2), "statement": statement[:500]},
            )
            increment("slow_queries_total")

    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        increment("database_pool_checkouts_total")

    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_conn, connection_record):
        increment("database_pool_checkins_total")

    # Log connection events (Factor 11: Logs as event streams)
    @event.listens_for(Engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Log successful database connections."""
        logger.debug("Database connection established")
    
    @event.listens_for(Engine, "close")
    def receive_close(dbapi_conn, connection_record):
        """Log connection closure."""
        logger.debug("Database connection closed")
    
    @event.listens_for(Engine, "detach")
    def receive_detach(dbapi_conn, connection_record):
        """Log connection detachment."""
        logger.debug("Database connection detached")
    
    return engine


# Create engine instance
engine = create_db_engine()

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=True  # Ensure objects are reloaded on next access
)

# Optional read replica. Only read-only endpoints depend on get_read_db; when
# DATABASE_REPLICA_URL is unset everything falls back to the primary so dev
# and single-node deployments are unchanged.
replica_engine = create_db_engine(settings.DATABASE_REPLICA_URL) if settings.DATABASE_REPLICA_URL else engine
ReplicaSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=replica_engine,
    expire_on_commit=True,
)


def get_db() -> Session:
    """
    Dependency injection for database sessions.
    
    Usage in FastAPI routes:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    
    12-Factor Compliance:
    - Factor 4: Database as backing service
    - Factor 6: Stateless processes (no shared DB state)
    """
    db = SessionLocal()
    try:
        logger.debug("Session created")
        yield db
    except PoolTimeoutError:
        increment("database_pool_exhaustion_total")
        logger.error("Database connection pool exhausted", exc_info=True)
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Database session error: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        logger.debug("Session closed")
        db.close()


def get_read_db() -> Session:
    """Session from the read replica (falls back to the primary when unset).

    Only for endpoints that never write — replica lag means a read-after-write
    through this dependency is not guaranteed.
    """
    db = ReplicaSessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database (create tables if they don't exist).
    
    This is called on application startup.
    In production, use Alembic migrations instead.
    """
    from app.models.base import Base
    
    try:
        logger.info("Initializing database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}", exc_info=True)
        raise


def close_db():
    """
    Close all database connections gracefully.
    
    Called on application shutdown (Factor 9: Disposability).
    """
    try:
        logger.info("Closing database connections...")
        engine.dispose()
        if replica_engine is not engine:
            replica_engine.dispose()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing database: {e}", exc_info=True)
