Real Estate Management System — Backend

Phase 1: Backend foundation

## PostgreSQL with Docker Compose

The project uses PostgreSQL for multi-user deployments. From the repository
root, start PostgreSQL, apply Alembic migrations, and start the API with:

```bash
docker compose up --build
```

The API is available at `http://localhost:8000` and PostgreSQL is available on
port `5432`. The database data is stored in the named `postgres_data` volume,
so it survives container restarts.

Production capacity is controlled through the database pool settings rather
than by hard-coding an application data limit. Pool sizes are per API worker,
so calculate the total across all workers and replicas against PostgreSQL's
connection limit. `DATABASE_STATEMENT_TIMEOUT_MS` prevents an unexpectedly
expensive query from holding a connection indefinitely, and `MAX_PAGE_SIZE`
protects API memory while still allowing the value to be increased for
legitimate clients.

### Capacity and background processing

Run database migrations before starting API and worker processes:

```bash
docker compose run --rm migrate
docker compose up api worker
```

The worker process is intentionally separate from API workers. Long-running
reports, imports, and notification work should enqueue a `BackgroundJob` and
be handled by a worker rather than blocking an HTTP request. Job handlers must
be registered explicitly; unknown job types fail and retry instead of being
silently discarded.

Rate limiting is process-independent when `RATE_LIMIT_ENABLED=true` and
`REDIS_URL` points to a shared Redis instance. Keep it disabled only for
local development. `/health/metrics` exposes per-process request, slow-query,
pool, error, and RSS counters for internal monitoring.

Opt-in PostgreSQL capacity testing is available in
`tests/load/test_postgres_capacity.py`. It requires a separate test database
through `LOAD_TEST_DATABASE_URL`.

For a non-local environment, set these variables in a root `.env` file or in
the deployment platform's secret configuration before starting Compose:

```text
POSTGRES_DB=real_estate
POSTGRES_USER=real_estate
POSTGRES_PASSWORD=<strong-password>
SECRET_KEY=<random-secret-at-least-32-characters>
CORS_ORIGINS=https://your-frontend.example.com
```

Never use the Compose fallback password or secret outside local development.

Run locally:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
