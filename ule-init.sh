#!/bin/bash
# ULE Bootstrapper Script
echo "🌌 Initializing ULE Engine..."

if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed. Please install Docker from https://www.docker.com/"
    exit 1
fi

echo "🚀 Starting ULE Database..."
docker-compose up -d --build

echo "✅ ULE is running at http://localhost:8000"
echo "👉 To stop it, run: docker-compose down"
