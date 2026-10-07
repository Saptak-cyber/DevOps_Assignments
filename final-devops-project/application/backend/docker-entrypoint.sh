#!/bin/sh
# Apply database migrations (retrying while PostgreSQL starts), then exec the server.
# Concurrent replicas are serialised by an advisory lock inside alembic/env.py.
set -eu

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  attempts=0
  until alembic upgrade head; do
    attempts=$((attempts + 1))
    if [ "$attempts" -ge "${MIGRATION_RETRIES:-20}" ]; then
      echo "entrypoint: database still unavailable after $attempts attempts, giving up" >&2
      exit 1
    fi
    echo "entrypoint: migration attempt $attempts failed, retrying in 3s" >&2
    sleep 3
  done
fi

exec "$@"
