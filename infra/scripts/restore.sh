#!/bin/bash
# =============================================================================
# Sales OS - Database Restore Script
# =============================================================================
# Restores the PostgreSQL database from a backup file
# Usage: ./infra/scripts/restore.sh <backup-file>
# =============================================================================

set -e

# Configuration
BACKUP_FILE="${1:-}"
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

# Validate input
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup-file>"
    echo "Example: $0 /backups/sales_os_backup_20241122_120000.sql.gz"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    log_error "Backup file not found: $BACKUP_FILE"
fi

# Confirmation prompt
echo -e "${RED}WARNING: This will overwrite all data in the '$POSTGRES_DB' database!${NC}"
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    log_info "Restore cancelled."
    exit 0
fi

log_info "Starting restore from: $BACKUP_FILE"

# Determine if file is compressed
if [[ "$BACKUP_FILE" == *.gz ]]; then
    log_info "Detected gzipped backup, decompressing..."
    DECOMPRESS_CMD="gunzip -c"
else
    DECOMPRESS_CMD="cat"
fi

# Check if running in Docker or directly
if [ -f /.dockerenv ]; then
    # Running inside Docker container
    log_info "Dropping existing connections..."
    export PGPASSWORD
    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres << EOF
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '$POSTGRES_DB'
  AND pid <> pg_backend_pid();
EOF

    log_info "Dropping and recreating database..."
    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres << EOF
DROP DATABASE IF EXISTS $POSTGRES_DB;
CREATE DATABASE $POSTGRES_DB OWNER $POSTGRES_USER;
EOF

    log_info "Restoring database..."
    $DECOMPRESS_CMD "$BACKUP_FILE" | psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB"
else
    # Running on host, use docker exec
    log_info "Dropping existing connections..."
    docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" sales-os-postgres psql -U "$POSTGRES_USER" -d postgres -c \
        "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '$POSTGRES_DB' AND pid <> pg_backend_pid();"

    log_info "Dropping and recreating database..."
    docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" sales-os-postgres psql -U "$POSTGRES_USER" -d postgres -c \
        "DROP DATABASE IF EXISTS $POSTGRES_DB; CREATE DATABASE $POSTGRES_DB OWNER $POSTGRES_USER;"

    log_info "Restoring database..."
    $DECOMPRESS_CMD "$BACKUP_FILE" | docker exec -i -e PGPASSWORD="$POSTGRES_PASSWORD" sales-os-postgres \
        psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
fi

log_info "Restore completed successfully!"
log_info "Verifying restore..."

# Quick verification
if [ -f /.dockerenv ]; then
    TABLE_COUNT=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c \
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
else
    TABLE_COUNT=$(docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" sales-os-postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c \
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
fi

log_info "Restored database has $TABLE_COUNT tables"
