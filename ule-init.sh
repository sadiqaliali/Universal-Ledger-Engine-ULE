#!/bin/bash
# ULE Production Bootstrapper Script
set -e # Exit on error

echo "🌌 Initializing ULE Production Environment..."

# Check dependencies
if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker and Docker Compose are required."
    echo "👉 Please install from: https://www.docker.com/"
    exit 1
fi

echo "🚀 Spinning up ULE Infrastructure..."
docker-compose up -d --build

echo "✅ ULE is running at http://localhost:8000"
echo "------------------------------------------------"
echo "👉 To check logs: docker-compose logs -f"
echo "👉 To stop the engine: docker-compose down"
echo "------------------------------------------------"
