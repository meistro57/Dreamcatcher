#!/bin/bash

# Dreamcatcher Start Script
# Quick start for development

set -e

echo "🧠 Starting Dreamcatcher development environment..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if we're in the right directory
if [[ ! -f "Project_vision.md" ]]; then
    echo "Error: Run this script from the Dreamcatcher project root directory"
    exit 1
fi

# Start with Docker Compose
log_info "Starting services with Docker Compose..."
docker compose -f docker/docker-compose.yml up -d

# Wait for services to be ready
log_info "Waiting for services to start..."
sleep 10

# Check service health
log_info "Checking service health..."
if curl -s -f http://localhost:8000/api/health > /dev/null; then
    log_success "Backend is running at http://localhost:8000"
else
    echo "Backend health check failed"
fi

if curl -s -f http://localhost:3000 > /dev/null; then
    log_success "Frontend is running at http://localhost:3000"
else
    echo "Frontend health check failed"
fi

log_success "Dreamcatcher is running!"

echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📊 API Docs: http://localhost:8000/docs"
echo "🗄️ Database: localhost:5432 (dreamcatcher/secure_password)"
echo ""
echo "📝 View logs: docker compose -f docker/docker-compose.yml logs -f"
echo "🛑 Stop services: docker compose -f docker/docker-compose.yml down"
echo ""
echo "Start capturing ideas! 💡"