#!/bin/bash

# Quick start script for local development

echo "🚀 Starting Sensor Ingestion Service (Local Development)"
echo "========================================================="

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your database and Redis URLs!"
    echo ""
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python -m venv venv
    echo ""
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "========================================================="
echo "✅ Setup complete!"
echo ""
echo "📡 Starting FastAPI server..."
echo "   API: http://localhost:8001"
echo "   Docs: http://localhost:8001/docs"
echo "   Health: http://localhost:8001/health"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================================="
echo ""

# Run the service
python -m uvicorn app.main:app --reload --port 8001 --log-level info
