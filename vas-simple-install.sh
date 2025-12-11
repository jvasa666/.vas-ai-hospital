#!/bin/bash
set -e

echo "🚀 Starting VAS-AI-Hospital Installation..."
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found!"
    exit 1
fi

# Check compose file
if [ -f "docker-compose.vas.yml" ]; then
    COMPOSE_FILE="docker-compose.vas.yml"
elif [ -f "docker-compose.yml" ]; then
    COMPOSE_FILE="docker-compose.yml"
else
    echo "❌ No docker-compose file found!"
    exit 1
fi

echo "✅ Found $COMPOSE_FILE"
echo "🔨 Building and starting services..."
echo ""

docker compose -f "$COMPOSE_FILE" up -d --build

echo ""
echo "✅ Installation complete!"
echo "🌐 Access at: http://localhost:3001"
echo ""
