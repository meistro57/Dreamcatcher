#!/bin/bash

# Dreamcatcher Backup Script
# Backup database and important files

set -e

echo "💾 Starting Dreamcatcher backup..."

# Configuration
BACKUP_DIR="/opt/dreamcatcher/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="dreamcatcher_backup_${TIMESTAMP}"
RETENTION_DAYS=30

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Create backup directory
mkdir -p $BACKUP_DIR

log_info "Creating backup: $BACKUP_NAME"

# Create backup directory
mkdir -p $BACKUP_DIR/$BACKUP_NAME

# Backup database
log_info "Backing up database..."
docker exec dreamcatcher-db pg_dump -U dreamcatcher dreamcatcher > $BACKUP_DIR/$BACKUP_NAME/database.sql

# Backup storage files
log_info "Backing up storage files..."
tar -czf $BACKUP_DIR/$BACKUP_NAME/storage.tar.gz -C /opt/dreamcatcher storage/

# Backup configuration
log_info "Backing up configuration..."
cp /home/mark/Dreamcatcher/.env $BACKUP_DIR/$BACKUP_NAME/
cp -r /home/mark/Dreamcatcher/docker/ssl $BACKUP_DIR/$BACKUP_NAME/ 2>/dev/null || true

# Create backup info file
cat > $BACKUP_DIR/$BACKUP_NAME/backup_info.txt << EOF
Dreamcatcher Backup Information
===============================
Backup Date: $(date)
Backup Name: $BACKUP_NAME
Database: PostgreSQL dump included
Storage: Compressed archive included
Configuration: .env and SSL certificates included

Restore Instructions:
1. Stop services: systemctl stop dreamcatcher
2. Restore database: docker exec -i dreamcatcher-db psql -U dreamcatcher dreamcatcher < database.sql
3. Restore storage: tar -xzf storage.tar.gz -C /opt/dreamcatcher
4. Restore config: cp .env /home/mark/Dreamcatcher/
5. Start services: systemctl start dreamcatcher
EOF

# Compress entire backup
log_info "Compressing backup..."
tar -czf $BACKUP_DIR/$BACKUP_NAME.tar.gz -C $BACKUP_DIR $BACKUP_NAME
rm -rf $BACKUP_DIR/$BACKUP_NAME

# Calculate backup size
BACKUP_SIZE=$(du -h $BACKUP_DIR/$BACKUP_NAME.tar.gz | cut -f1)
log_success "Backup created: $BACKUP_NAME.tar.gz ($BACKUP_SIZE)"

# Clean up old backups
log_info "Cleaning up old backups (keeping last $RETENTION_DAYS days)..."
find $BACKUP_DIR -name "dreamcatcher_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# List current backups
log_info "Current backups:"
ls -lh $BACKUP_DIR/dreamcatcher_backup_*.tar.gz 2>/dev/null || echo "No backups found"

log_success "Backup completed successfully!"

echo ""
echo "📁 Backup location: $BACKUP_DIR/$BACKUP_NAME.tar.gz"
echo "📊 Backup size: $BACKUP_SIZE"
echo "🔄 Retention: $RETENTION_DAYS days"
echo ""
echo "To restore from backup:"
echo "1. Extract: tar -xzf $BACKUP_DIR/$BACKUP_NAME.tar.gz"
echo "2. Follow instructions in backup_info.txt"