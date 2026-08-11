#!/usr/bin/env bash
# Restore the MongoDB database from a mongodump backup directory.
#
# This is DESTRUCTIVE: mongorestore is run with --drop, which drops each
# collection in the target database before restoring it from the backup.
#
# Required env vars (same names used in app/core/config.py):
#   MONGODB_HOST, MONGODB_PORT, MONGODB_DB, MONGODB_USER, MONGODB_PASSWORD
#
# Optional: MONGODB_AUTH_DB (defaults to MONGODB_DB).
#
# Usage:
#   ./scripts/restore_mongo.sh <backup_dir> --yes
#
# <backup_dir> is the directory produced by backup_mongo.sh, e.g.
#   backups/mongo/20260101T120000Z
# (the directory that directly contains the "<db>" subdirectory of BSON files).
#
# Without --yes, the script only prints what it would do and exits without
# touching the database.

set -euo pipefail

BACKUP_DIR="${1:-}"
CONFIRM="${2:-}"

if [ -z "$BACKUP_DIR" ]; then
    echo "ERROR: missing backup directory argument." >&2
    echo "Usage: $0 <backup_dir> --yes" >&2
    exit 1
fi

if [ ! -d "$BACKUP_DIR" ]; then
    echo "ERROR: backup directory not found: $BACKUP_DIR" >&2
    exit 1
fi

for var in MONGODB_HOST MONGODB_PORT MONGODB_DB MONGODB_USER MONGODB_PASSWORD; do
    if [ -z "${!var:-}" ]; then
        echo "ERROR: required environment variable $var is not set." >&2
        exit 1
    fi
done

if ! command -v mongorestore >/dev/null 2>&1; then
    echo "ERROR: mongorestore not found on PATH. Install the mongodb-database-tools package." >&2
    exit 1
fi

AUTH_DB="${MONGODB_AUTH_DB:-$MONGODB_DB}"
SOURCE_DB_DIR="$BACKUP_DIR/$MONGODB_DB"

if [ "$CONFIRM" != "--yes" ]; then
    echo "This would restore database '$MONGODB_DB' on $MONGODB_HOST:$MONGODB_PORT"
    echo "from backup directory: $SOURCE_DB_DIR"
    echo "using: mongorestore --drop (this DROPS existing collections first)"
    echo
    echo "No changes made. Re-run with --yes as the second argument to actually restore:"
    echo "  $0 \"$BACKUP_DIR\" --yes"
    exit 0
fi

if [ ! -d "$SOURCE_DB_DIR" ]; then
    echo "ERROR: expected database subdirectory not found: $SOURCE_DB_DIR" >&2
    echo "Point <backup_dir> at the timestamped folder produced by backup_mongo.sh." >&2
    exit 1
fi

mongorestore \
    --host "$MONGODB_HOST" \
    --port "$MONGODB_PORT" \
    --db "$MONGODB_DB" \
    --username "$MONGODB_USER" \
    --password "$MONGODB_PASSWORD" \
    --authenticationDatabase "$AUTH_DB" \
    --drop \
    "$SOURCE_DB_DIR"

echo "Restore complete from: $SOURCE_DB_DIR"
