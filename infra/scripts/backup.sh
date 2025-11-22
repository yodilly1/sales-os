#!/bin/bash
# =============================================================================
# Sales OS - Database Backup Script
# =============================================================================
# Creates compressed backups of the PostgreSQL database
# Usage: ./infra/scripts/backup.sh [backup-name]
# =============================================================================

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="${1:-sales_os_backup_$TIMESTAMP}"

# Database configuration (from environment or defaults)
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-sales_os}"
POSTGRES_DB="${POSTGRES_DB:-sales_os}"
PGPASSWORD="${POSTGRES_PASSWORD:-}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
    exit 1
}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

log_info "Starting backup: $BACKUP_NAME"

# Check if running in Docker or directly
if [ -f /.dockerenv ]; then
    # Running inside Docker container
    BACKUP_FILE="$BACKUP_DIR/${BACKUP_NAME}.sql.gz"

    log_info "Creating database dump..."
    export PGPASSWORD
    pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
        --format=plain --no-owner --no-acl | gzip > "$BACKUP_FILE"
else
    # Running on host, use docker exec
    BACKUP_FILE="$BACKUP_DIR/${BACKUP_NAME}.sql.gz"

    log_info "Creating database dump via Docker..."
    docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" sales-os-postgres \
        pg_dump -h localhost -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
        --format=plain --no-owner --no-acl | gzip > "$BACKUP_FILE"
fi

# Verify backup
if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log_info "Backup created successfully: $BACKUP_FILE ($BACKUP_SIZE)"
else
    log_error "Backup file not created!"
fi

# Cleanup old backups
log_info "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "sales_os_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete
REMAINING=$(find "$BACKUP_DIR" -name "sales_os_backup_*.sql.gz" -type f | wc -l)
log_info "Remaining backups: $REMAINING"

# Optional: Upload to S3 (uncomment and configure)
# if [ -n "$AWS_S3_BUCKET" ]; then
#     log_info "Uploading to S3..."
#     aws s3 cp "$BACKUP_FILE" "s3://$AWS_S3_BUCKET/backups/$(basename $BACKUP_FILE)"
#     log_info "Uploaded to S3 successfully"
# fi

log_info "Backup completed successfully!"
