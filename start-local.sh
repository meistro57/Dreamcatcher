#!/bin/bash

# Dreamcatcher Local Development Startup Script
# This script starts the entire Dreamcatcher stack locally without domain requirements

set -e

echo "🧠 Starting Dreamcatcher Local Development Environment..."

# Check if .env exists, if not copy from .env.local
if [ ! -f .env ]; then
    echo "📋 Creating .env file from .env.local template..."
    cp .env.local .env
    echo "⚠️  Please edit .env file and add your API keys before continuing!"
    echo "   Required: ANTHROPIC_API_KEY and OPENAI_API_KEY"
    echo ""
    echo "   You can get these from:"
    echo "   - Anthropic: https://console.anthropic.com/"
    echo "   - OpenAI: https://platform.openai.com/api-keys"
    echo ""
    read -p "Press Enter after you've updated the .env file..."
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version > /dev/null 2>&1; then
    echo "❌ docker compose is not available. Please install Docker Compose v2."
    exit 1
fi

# Create logs directory
mkdir -p logs

# Stop any existing containers
echo "🧹 Stopping any existing containers..."
docker compose -f docker-compose.local.yml down

# Pull latest images
echo "📦 Pulling latest images..."
docker compose -f docker-compose.local.yml pull postgres redis

# Start the services
echo "🚀 Starting services..."
docker compose -f docker-compose.local.yml up -d postgres redis

# Wait for databases to be ready
echo "⏳ Waiting for databases to be ready..."
sleep 10

# Start backend and frontend
echo "🖥️  Starting backend and frontend..."
docker compose -f docker-compose.local.yml up -d backend frontend

echo ""
echo "✅ Dreamcatcher is starting up!"
echo ""
echo "🌐 Access points:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Database: localhost:5432 (dreamcatcher/dreamcatcher_password)"
echo "   Redis: localhost:6379"
echo ""
echo "📊 Monitor logs with:"
echo "   docker compose -f docker-compose.local.yml logs -f"
echo ""
echo "🛑 Stop with:"
echo "   docker compose -f docker-compose.local.yml down"
echo ""
echo "🔧 If you encounter issues, try:"
echo "   ./reset-local.sh"
echo ""

# Wait a bit and check health
sleep 5
echo "🏥 Checking service health..."

# Check backend health
if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "⚠️  Backend is still starting up..."
fi

# Check frontend
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "⚠️  Frontend is still starting up..."
fi

echo ""
echo "🎉 Dreamcatcher is ready! Open http://localhost:3000 to start capturing ideas!"