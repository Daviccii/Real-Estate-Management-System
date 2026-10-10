"""
Shared pytest fixtures — test/dev database isolation.

ROOT CAUSE THIS FIXES: there was previously no conftest.py at all, so every
`TestClient(app)` in the test suite used the app's real `get_db` dependency
unmodified — which is wired to `database.py`'s engine, pointed at the real
DATABASE_URL (your actual dev database.db). Every test run was writing
"Test Property for X" rows directly into the same database the running app
reads from, which is why that junk kept reappearing on every page no matter
what frontend/backend fixes were made elsewhere.

This file gives each test function a brand-new, empty, in-memory SQLite
database and overrides `get_db` so requests made through the test client hit
that throwaway database instead. Nothing a test does can ever touch
database.db again, regardless of what future tests get written.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.database.database import get_db, get_read_db
from app.models.base import Base

# In-memory SQLite, but with StaticPool + check_same_thread=False so the
# handful of separate connections a single test's requests open (each
# get_db() call creates a new session) all see the SAME in-memory database
# instead of each getting its own empty one — which is the default, and
# would make every route look like it has no data.
TEST_DATABASE_URL = "sqlite://"


@pytest.fixture()
def test_engine():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # SQLite ignores foreign key constraints unless explicitly turned on per
    # connection — enable it so cascade deletes/relationship behavior in
    # tests matches production (Postgres) semantics.
    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(test_engine):
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(test_engine):
    """
    A TestClient wired to the isolated in-memory database above instead of
    the real one. Use this in tests instead of constructing
    `TestClient(app)` directly.
    """
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # Read-replica dependency must point at the same isolated database.
    app.dependency_overrides[get_read_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()