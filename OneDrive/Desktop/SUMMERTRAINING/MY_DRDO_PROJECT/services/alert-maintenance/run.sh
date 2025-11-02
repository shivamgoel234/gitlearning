#!/bin/bash

# Alert & Maintenance Service Startup Script

echo "=================================================="
echo "  DRDO Alert & Maintenance Service"
echo "=================================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    python -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.installed" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    touch venv/.installed
    echo "✓ Dependencies installed"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "✓ .env file created - please update with your credentials"
    echo ""
    echo "❗ IMPORTANT: Update .env with your database and Redis credentials"
    echo ""
    read -p "Press Enter to continue or Ctrl+C to exit and edit .env..."
fi

# Start the service
echo ""
echo "🚀 Starting Alert & Maintenance Service..."
echo "   Port: 8003"
echo "   Docs: http://localhost:8003/docs"
echo ""
echo "Press Ctrl+C to stop"
echo "=================================================="
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
