#!/usr/bin/env bash
# Backup the PostgreSQL database using pg_dump (custom format).
#
# Required env vars (same names used in app/core/config.py / docker-compose.prod.yml):
#   POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
#
# Output: backups/postgres/<db>_<timestamp>.dump
#
# Usage:
#   ./scripts/backup_postgres.sh

set -euo pipefail

for var in POSTGRES_HOST POSTGRES_PORT POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD; do
    if [ -z "${!var:-}" ]; then
        echo "ERROR: required environment variable $var is not set." >&2
        exit 1
    fi
done

if ! command -v pg_dump >/dev/null 2>&1; then
    echo "ERROR: pg_dump not found on PATH. Install the postgresql-client package." >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="$REPO_ROOT/backups/postgres"
mkdir -p "$BACKUP_DIR"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_FILE="$BACKUP_DIR/${POSTGRES_DB}_${TIMESTAMP}.dump"

export PGPASSWORD="$POSTGRES_PASSWORD"

pg_dump \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    -Fc \
    -f "$BACKUP_FILE"

unset PGPASSWORD

echo "Backup written to: $BACKUP_FILE"
