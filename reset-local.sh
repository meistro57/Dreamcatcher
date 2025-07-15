#!/bin/bash

# Dreamcatcher Local Development Reset Script
# This script resets the entire local development environment

set -e

echo "🔄 Resetting Dreamcatcher Local Development Environment..."

# Stop all containers
echo "🛑 Stopping all containers..."
docker-compose -f docker-compose.local.yml down

# Remove containers and volumes
echo "🧹 Removing containers and volumes..."
docker-compose -f docker-compose.local.yml down -v

# Remove any dangling images
echo "🗑️  Cleaning up Docker images..."
docker system prune -f

# Remove logs
echo "📝 Clearing logs..."
rm -rf logs/*

# Create fresh logs directory
mkdir -p logs

echo ""
echo "✅ Local environment reset complete!"
echo ""
echo "🚀 To start fresh, run:"
echo "   ./start-local.sh"
echo ""