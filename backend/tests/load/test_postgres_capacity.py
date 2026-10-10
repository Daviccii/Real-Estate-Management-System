"""Opt-in PostgreSQL capacity tests.

Run against an isolated PostgreSQL database, never a production database:

    $env:LOAD_TEST_DATABASE_URL = "postgresql+psycopg://..."
    .\\backend\\.venv\\Scripts\\python.exe -m pytest -m load backend\\tests\\load -q
"""

import os
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, text


DATABASE_URL = os.getenv("LOAD_TEST_DATABASE_URL")
pytestmark = pytest.mark.load


@pytest.fixture(scope="module")
def load_engine():
    if not DATABASE_URL:
        pytest.skip("Set LOAD_TEST_DATABASE_URL to run PostgreSQL load tests")
    if not DATABASE_URL.startswith(("postgresql://", "postgresql+psycopg://")):
        pytest.fail("LOAD_TEST_DATABASE_URL must point to PostgreSQL")
    engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=10, pool_timeout=5)
    table_name = f"capacity_probe_{uuid.uuid4().hex}"
    with engine.begin() as connection:
        connection.execute(text(f"CREATE TABLE {table_name} (id integer primary key, payload text not null)"))
        connection.execute(
            text(f"INSERT INTO {table_name} SELECT id, repeat('x', 256) FROM generate_series(1, 10000) AS id")
        )
    yield engine, table_name
    with engine.begin() as connection:
        connection.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
    engine.dispose()


def test_concurrent_paginated_reads_remain_bounded(load_engine):
    engine, table_name = load_engine
    def read_page(page: int) -> int:
        with engine.connect() as connection:
            return connection.execute(
                text(
                    f"SELECT count(*) FROM (SELECT id FROM {table_name} "
                    "ORDER BY id OFFSET :offset LIMIT 100) page"
                ),
                {"offset": page * 100},
            ).scalar_one()

    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(read_page, range(100)))

    assert results == [100] * 100
