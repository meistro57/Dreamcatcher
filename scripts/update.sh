#!/bin/bash

# Dreamcatcher Update Script
# Update the system with minimal downtime

set -e

echo "🔄 Updating Dreamcatcher..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root"
    exit 1
fi

# Check if we're in the right directory
if [[ ! -f "/home/mark/Dreamcatcher/Project_vision.md" ]]; then
    log_error "Dreamcatcher directory not found"
    exit 1
fi

cd /home/mark/Dreamcatcher

# Backup before update
log_info "Creating backup before update..."
./scripts/backup.sh

# Pull latest changes
log_info "Pulling latest changes..."
git pull origin main

# Update backend dependencies
log_info "Updating backend dependencies..."
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade
cd ..

# Update frontend dependencies
log_info "Updating frontend dependencies..."
cd frontend
npm install
npm audit fix --force 2>/dev/null || true
cd ..

# Rebuild containers
log_info "Rebuilding Docker containers..."
cd docker
docker-compose -f docker-compose.prod.yml build --no-cache

# Rolling update with health checks
log_info "Performing rolling update..."

# Update backend first
log_info "Updating backend..."
docker-compose -f docker-compose.prod.yml up -d --no-deps backend scheduler

# Wait for backend to be healthy
log_info "Waiting for backend to be healthy..."
for i in {1..30}; do
    if curl -s -f http://localhost:8000/api/health > /dev/null; then
        log_success "Backend is healthy"
        break
    fi
    
    if [ $i -eq 30 ]; then
        log_error "Backend health check failed after 30 attempts"
        exit 1
    fi
    
    sleep 2
done

# Update frontend
log_info "Updating frontend..."
docker-compose -f docker-compose.prod.yml up -d --no-deps frontend

# Wait for frontend to be healthy
log_info "Waiting for frontend to be healthy..."
for i in {1..15}; do
    if curl -s -f http://localhost:3000 > /dev/null; then
        log_success "Frontend is healthy"
        break
    fi
    
    if [ $i -eq 15 ]; then
        log_error "Frontend health check failed after 15 attempts"
        exit 1
    fi
    
    sleep 2
done

# Reload nginx
log_info "Reloading nginx..."
docker exec dreamcatcher-nginx nginx -s reload

# Run any database migrations
log_info "Running database migrations..."
docker exec dreamcatcher-backend python -c "from database import create_tables; create_tables()"

# Clean up old images
log_info "Cleaning up old Docker images..."
docker image prune -f

# Final health check
log_info "Performing final health check..."
if curl -s -f http://localhost:8000/api/health > /dev/null; then
    log_success "Backend health check passed"
else
    log_error "Backend health check failed"
    exit 1
fi

if curl -s -f http://localhost:3000 > /dev/null; then
    log_success "Frontend health check passed"
else
    log_error "Frontend health check failed"
    exit 1
fi

# Update system service
log_info "Restarting systemd service..."
systemctl daemon-reload
systemctl restart dreamcatcher

log_success "Update completed successfully!"

echo ""
echo "🎉 Dreamcatcher has been updated!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend: http://localhost:8000"
echo "📊 API Docs: http://localhost:8000/docs"
echo ""
echo "📝 View logs: docker-compose -f docker/docker-compose.prod.yml logs -f"
echo "💾 Backup created at: /opt/dreamcatcher/backups/"
echo ""
echo "The basement is now running the latest version! 🚀"