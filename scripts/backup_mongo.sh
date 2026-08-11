#!/usr/bin/env bash
# Backup the MongoDB database using mongodump.
#
# Required env vars (same names used in app/core/config.py):
#   MONGODB_HOST, MONGODB_PORT, MONGODB_DB, MONGODB_USER, MONGODB_PASSWORD
#
# Output: backups/mongo/<timestamp>/<db>/...
#
# Usage:
#   ./scripts/backup_mongo.sh

set -euo pipefail

for var in MONGODB_HOST MONGODB_PORT MONGODB_DB MONGODB_USER MONGODB_PASSWORD; do
    if [ -z "${!var:-}" ]; then
        echo "ERROR: required environment variable $var is not set." >&2
        exit 1
    fi
done

if ! command -v mongodump >/dev/null 2>&1; then
    echo "ERROR: mongodump not found on PATH. Install the mongodb-database-tools package." >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="$REPO_ROOT/backups/mongo/$TIMESTAMP"
mkdir -p "$OUT_DIR"

# NOTE: --authenticationDatabase defaults to MONGODB_DB to match this
# project's default single-database setup. If your MongoDB user was created
# against a different auth database (e.g. "admin"), override with
# MONGODB_AUTH_DB.
AUTH_DB="${MONGODB_AUTH_DB:-$MONGODB_DB}"

mongodump \
    --host "$MONGODB_HOST" \
    --port "$MONGODB_PORT" \
    --db "$MONGODB_DB" \
    --username "$MONGODB_USER" \
    --password "$MONGODB_PASSWORD" \
    --authenticationDatabase "$AUTH_DB" \
    --out "$OUT_DIR"

echo "Backup written to: $OUT_DIR"
