#!/usr/bin/env bash
# Restore the PostgreSQL database from a pg_dump custom-format backup file.
#
# This is DESTRUCTIVE: existing objects in the target database are dropped
# (--clean --if-exists) before being recreated from the backup.
#
# Required env vars (same names used in app/core/config.py / docker-compose.prod.yml):
#   POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
#
# Usage:
#   ./scripts/restore_postgres.sh <backup_file> --yes
#
# Without --yes, the script only prints what it would do and exits without
# touching the database.

set -euo pipefail

BACKUP_FILE="${1:-}"
CONFIRM="${2:-}"

if [ -z "$BACKUP_FILE" ]; then
    echo "ERROR: missing backup file argument." >&2
    echo "Usage: $0 <backup_file> --yes" >&2
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: backup file not found: $BACKUP_FILE" >&2
    exit 1
fi

for var in POSTGRES_HOST POSTGRES_PORT POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD; do
    if [ -z "${!var:-}" ]; then
        echo "ERROR: required environment variable $var is not set." >&2
        exit 1
    fi
done

if ! command -v pg_restore >/dev/null 2>&1; then
    echo "ERROR: pg_restore not found on PATH. Install the postgresql-client package." >&2
    exit 1
fi

if [ "$CONFIRM" != "--yes" ]; then
    echo "This would restore database '$POSTGRES_DB' on $POSTGRES_HOST:$POSTGRES_PORT"
    echo "from backup file: $BACKUP_FILE"
    echo "using: pg_restore --clean --if-exists (this DROPS existing objects first)"
    echo
    echo "No changes made. Re-run with --yes as the second argument to actually restore:"
    echo "  $0 \"$BACKUP_FILE\" --yes"
    exit 0
fi

export PGPASSWORD="$POSTGRES_PASSWORD"

pg_restore \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --clean \
    --if-exists \
    "$BACKUP_FILE"

unset PGPASSWORD

echo "Restore complete from: $BACKUP_FILE"
