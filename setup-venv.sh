#!/bin/bash

# Dreamcatcher Virtual Environment Setup Script
# This script sets up a clean Python virtual environment for Dreamcatcher

set -e

echo "🐍 Setting up Python Virtual Environment for Dreamcatcher..."

# Check if we're in the right directory
if [ ! -f "backend/requirements.txt" ]; then
    echo "❌ Please run this script from the Dreamcatcher root directory"
    exit 1
fi

cd backend

# Remove existing venv if it exists
if [ -d "venv" ]; then
    echo "🗑️  Removing existing virtual environment..."
    rm -rf venv
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "📋 Using Python version: $PYTHON_VERSION"

if [ "$(printf '%s\n' "3.8" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.8" ]; then
    echo "❌ Python 3.8+ is required. Current version: $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    echo "💡 Possible solutions:"
    echo "   - Install python3-venv: sudo apt-get install python3-venv"
    echo "   - Or install virtualenv: python3 -m pip install --user virtualenv"
    echo "   - Or use system package manager: sudo apt-get install python3-virtualenv"
    exit 1
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install wheel for better package building
echo "🛠️  Installing wheel..."
pip install wheel

# Install requirements
echo "📦 Installing Dreamcatcher dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    echo "💡 Try manually:"
    echo "   cd backend"
    echo "   source venv/bin/activate"
    echo "   pip install --upgrade pip"
    echo "   pip install -r requirements.txt"
    exit 1
fi

echo ""
echo "✅ Virtual environment setup complete!"
echo ""
echo "🚀 To activate the environment:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo ""
echo "🏃‍♂️ To start the backend:"
echo "   uvicorn main:app --reload"
echo ""
echo "🧹 To deactivate when done:"
echo "   deactivate"
echo ""