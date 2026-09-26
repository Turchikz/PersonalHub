#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="/home/adminka/projects/PersonalHub"
BACKUP_DIR="/home/adminka/projects/backups/personalhub"
RETENTION_DAYS=180

TIMESTAMP=$(TZ=Europe/Moscow date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/personalhub_${TIMESTAMP}.dump"
TEMP_FILE="${BACKUP_FILE}.tmp"

cleanup() {
    rm -f "$TEMP_FILE"
}

trap cleanup EXIT

mkdir -p "$BACKUP_DIR"
cd "$PROJECT_DIR"

echo "Creating PostgreSQL backup: $BACKUP_FILE"

docker compose exec -T db sh -c \
    'pg_dump --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" --format=custom' \
    > "$TEMP_FILE"

if [[ ! -s "$TEMP_FILE" ]]; then
    echo "Backup file is empty"
    exit 1
fi

docker compose exec -T db pg_restore --list \
    < "$TEMP_FILE" \
    > /dev/null

mv "$TEMP_FILE" "$BACKUP_FILE"

find "$BACKUP_DIR" \
    -maxdepth 1 \
    -type f \
    -name "personalhub_*.dump" \
    -mtime +"$RETENTION_DAYS" \
    -delete

echo "Backup completed successfully: $BACKUP_FILE"