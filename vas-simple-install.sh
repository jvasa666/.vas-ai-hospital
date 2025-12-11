#!/bin/bash
set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     VAS-AI-HOSPITAL - ULTRA-SIMPLE INSTALLATION           ║"
echo "║     One Command. Zero Hassle. Full Stack.                ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "✗ Docker not found. Install from: https://docker.com/get-started"
    exit 1
fi

echo "✓ Docker installed"

# Check Docker is running
if ! docker ps &> /dev/null; then
    echo "✗ Docker is not running. Start Docker."
    exit 1
fi

echo "✓ Docker is running"
echo ""

# Check for .env.vas
if [ ! -f ".env.vas" ]; then
    if [ -f ".env.vas.example" ]; then
        echo "→ Creating .env.vas from example..."
        cp .env.vas.example .env.vas
        echo "⚠ IMPORTANT: Edit .env.vas and add your ANTHROPIC_API_KEY"
    else
        echo "✗ No .env.vas.example found!"
        exit 1
    fi
fi

# Check for docker-compose file
COMPOSE_FILE="docker-compose.vas.yml"
if [ ! -f "$COMPOSE_FILE" ]; then
    if [ -f "docker-compose.yml" ]; then
        COMPOSE_FILE="docker-compose.yml"
    else
        echo "✗ No docker-compose file found!"
        exit 1
    fi
fi

echo "→ Building and deploying services..."
echo "  This may take 3-5 minutes on first run..."
echo ""

# Build and deploy
docker compose -f "$COMPOSE_FILE" build --no-cache
docker compose -f "$COMPOSE_FILE" up -d

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                 INSTALLATION COMPLETE!                    ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Access Points:"
echo "  • AI-Gateway:       http://localhost:8888/capabilities"
echo "  • Patient Service:  http://localhost:8081/api/health"
echo "  • Staff Dashboard:  http://localhost:3001"
echo ""
echo "🔧 Quick Commands:"
echo "  • View logs:   docker compose -f $COMPOSE_FILE logs -f"
echo "  • Stop all:    docker compose -f $COMPOSE_FILE down"
echo ""
