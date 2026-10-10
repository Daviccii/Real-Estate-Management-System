#!/bin/sh
set -e

# release.sh - helper to run alembic migrations in CI or locally
# Usage:
#   ./backend/scripts/release.sh

if [ -z "$DATABASE_URL" ]; then
  echo "ERROR: DATABASE_URL must be set" >&2
  exit 1
fi

if [ -z "$SECRET_KEY" ]; then
  echo "ERROR: SECRET_KEY must be set" >&2
  exit 1
fi

# Determine alembic config path. If running from repository root, use backend/alembic.ini
if [ -f "backend/alembic.ini" ]; then
  ALEMBIC_INI="backend/alembic.ini"
else
  ALEMBIC_INI="alembic.ini"
fi

echo "Running migrations using $ALEMBIC_INI"
alembic -c "$ALEMBIC_INI" upgrade head
