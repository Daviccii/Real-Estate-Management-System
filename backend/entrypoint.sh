#!/bin/sh
set -e

# entrypoint.sh - supports: release | run | admin <cmd>
# - release: validate config and run alembic migrations (alembic upgrade head)
# - run: start the web server (uvicorn)
# - admin: run one-off admin commands

validate_env() {
  missing=0
  if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL is not set" >&2
    missing=1
  fi
  if [ -z "$SECRET_KEY" ]; then
    echo "ERROR: SECRET_KEY is not set" >&2
    missing=1
  fi
  if [ "$missing" -ne 0 ]; then
    exit 1
  fi
}

case "$1" in
  release)
    echo "[entrypoint] Running release: validating config and applying migrations"
    validate_env
    # Run alembic migrations; fail fast on error so release can be halted
    alembic -c /app/alembic.ini upgrade head
    exit $?
    ;;

  run)
    echo "[entrypoint] Starting web server"
    exec uvicorn app.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000} --workers ${WORKERS:-4} --proxy-headers
    ;;

  admin)
    shift
    exec "$@"
    ;;

  *)
    # Default: start the app
    exec uvicorn app.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000} --workers ${WORKERS:-4} --proxy-headers
    ;;
esac
