#!/bin/bash

# Dreamcatcher Setup Script
# Initial setup for development environment

set -e

echo "🧠 Setting up Dreamcatcher development environment..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Check if running in development directory
if [[ ! -f "Project_vision.md" ]]; then
    echo "Error: Run this script from the Dreamcatcher project root directory"
    exit 1
fi

# Install backend dependencies
log_info "Setting up backend environment..."
cd backend

# Create virtual environment if it doesn't exist
if [[ ! -d "venv" ]]; then
    log_info "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
log_info "Installing Python dependencies..."
pip install -r requirements.txt

# Create development .env if it doesn't exist
if [[ ! -f ".env" ]]; then
    log_info "Creating development .env file..."
    cp ../.env.example .env
    log_warning "Don't forget to add your API keys to backend/.env"
fi

cd ..

# Install frontend dependencies
log_info "Setting up frontend environment..."
cd frontend

# Install npm dependencies
if [[ ! -d "node_modules" ]]; then
    log_info "Installing Node.js dependencies..."
    npm install
fi

cd ..

# Create storage directories
log_info "Creating storage directories..."
mkdir -p storage/{audio,images,logs}

# Set up development database
log_info "Setting up development database..."
docker-compose -f docker/docker-compose.yml up -d postgres redis

# Wait for database to be ready
log_info "Waiting for database to be ready..."
sleep 10

# Run database migrations
log_info "Running database migrations..."
cd backend
source venv/bin/activate
python -c "from database import create_tables; create_tables()"
cd ..

log_success "Development environment setup complete!"

echo ""
echo "🚀 Quick Start:"
echo "1. Add your API keys to backend/.env"
echo "2. Start backend: cd backend && source venv/bin/activate && python main.py"
echo "3. Start frontend: cd frontend && npm run dev"
echo "4. Visit: http://localhost:3000"
echo ""
echo "🐳 Or use Docker:"
echo "docker-compose -f docker/docker-compose.yml up"
echo ""
echo "Happy idea catching! 💡"