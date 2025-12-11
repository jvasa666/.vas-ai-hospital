#!/bin/bash
set -e

echo "🚀 VAS-AI-Hospital Installation Starting..."
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Install from: https://docker.com"
    exit 1
fi
echo "✓ Docker found"

# Check Docker is running
if ! docker ps &> /dev/null; then
    echo "❌ Docker daemon not running. Start Docker Desktop."
    exit 1
fi
echo "✓ Docker is running"

# Find compose file
if [ -f "docker-compose.vas.yml" ]; then
    COMPOSE_FILE="docker-compose.vas.yml"
elif [ -f "docker-compose.yml" ]; then
    COMPOSE_FILE="docker-compose.yml"
else
    echo "❌ No docker-compose file found!"
    exit 1
fi

echo "✓ Using $COMPOSE_FILE"
echo ""
echo "🔨 Building and starting services (this may take 3-5 minutes)..."
echo ""

# Build and start
docker compose -f "$COMPOSE_FILE" up -d --build

if [ $? -eq 0 ]; then
    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║              INSTALLATION SUCCESSFUL! ✅                   ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""
    echo "🌐 Access Points:"
    echo "  • Staff Dashboard:  http://localhost:3001"
    echo "  • AI Gateway:       http://localhost:8888/capabilities"
    echo "  • Patient Service:  http://localhost:8081/api/health"
    echo ""
    echo "📊 Check status:  docker compose -f $COMPOSE_FILE ps"
    echo "📝 View logs:     docker compose -f $COMPOSE_FILE logs -f"
    echo "🛑 Stop all:      docker compose -f $COMPOSE_FILE down"
    echo ""
else
    echo ""
    echo "❌ Installation failed. Check logs with:"
    echo "   docker compose -f $COMPOSE_FILE logs"
    exit 1
fi
