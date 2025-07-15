#!/bin/bash

# Dreamcatcher Native Development Startup Script
# This script starts Dreamcatcher without Docker (requires local Python and Node.js)

set -e

echo "🧠 Starting Dreamcatcher Native Development Environment..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📋 Creating .env file from .env.local template..."
    cp .env.local .env
    echo "⚠️  Please edit .env file and add your API keys before continuing!"
    echo "   Required: ANTHROPIC_API_KEY and OPENAI_API_KEY"
    echo ""
    read -p "Press Enter after you've updated the .env file..."
fi

# Check dependencies
echo "🔍 Checking dependencies..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm"
    exit 1
fi

# Check for PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed. Please install PostgreSQL 15+"
    echo "   Or use Docker: docker run -d --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=dreamcatcher_password postgres:15"
    exit 1
fi

# Check for Redis
if ! command -v redis-cli &> /dev/null; then
    echo "❌ Redis is not installed. Please install Redis 7+"
    echo "   Or use Docker: docker run -d --name redis -p 6379:6379 redis:7-alpine"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Set up Python environment
echo "🐍 Setting up Python environment..."
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        echo "💡 Try: python3 -m pip install --user virtualenv"
        exit 1
    fi
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    echo "💡 Try removing venv directory and running again: rm -rf venv"
    exit 1
fi

# Upgrade pip and install requirements
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python dependencies"
    echo "💡 Try: pip install --upgrade pip && pip install -r requirements.txt"
    exit 1
fi

# Start backend in background
echo "🚀 Starting backend..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd ..

# Set up frontend
echo "⚛️  Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Start frontend in background
echo "🚀 Starting frontend..."
npm run dev -- --host 0.0.0.0 --port 3000 &
FRONTEND_PID=$!

cd ..

# Function to cleanup processes
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

# Set up cleanup trap
trap cleanup SIGINT SIGTERM

echo ""
echo "✅ Dreamcatcher is starting up!"
echo ""
echo "🌐 Access points:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🔧 Manual database setup required:"
echo "   1. Create PostgreSQL database: createdb dreamcatcher"
echo "   2. Create user: createuser dreamcatcher"
echo "   3. Grant permissions: psql -c 'GRANT ALL PRIVILEGES ON DATABASE dreamcatcher TO dreamcatcher;'"
echo ""
echo "📊 To see logs, check the terminals or logs/ directory"
echo "🛑 Press Ctrl+C to stop all services"
echo ""

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID