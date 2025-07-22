#!/bin/bash

# Replenishment Service Startup Script

echo "🚀 Starting Replenishment Service..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp env.example .env
    echo "📝 Please edit .env file with your configuration before starting the service."
    exit 1
fi

# Create necessary directories
mkdir -p models logs

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the service
echo "🌟 Starting FastAPI server..."
python main.py 