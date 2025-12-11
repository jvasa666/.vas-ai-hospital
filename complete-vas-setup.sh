#!/bin/bash
# Complete VAS-AI-Hospital Setup Script
# Fixes all common issues and sets up everything correctly

set -e

REPO_DIR="/mnt/c/Users/alexk/Desktop/ComboKickAzz/zfp-codex/.vas-ai-hospital"

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     VAS-AI-HOSPITAL COMPLETE SETUP & FIX SCRIPT           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# 1. Navigate to repo
echo "[1/7] Navigating to repository..."
cd "$REPO_DIR"
echo "✓ In $REPO_DIR"
echo ""

# 2. Clean up nested directory if it exists
echo "[2/7] Cleaning up nested directories..."
if [ -d ".vas-ai-hospital" ]; then
    echo "  → Removing nested .vas-ai-hospital directory"
    rm -rf .vas-ai-hospital
fi
echo "✓ Cleanup complete"
echo ""

# 3. Create install script if missing
echo "[3/7] Creating/updating install script..."
cat > vas-simple-install.sh << 'EOF'
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
EOF

chmod +x vas-simple-install.sh
echo "✓ Install script created"
echo ""

# 4. Create API proxy service
echo "[4/7] Creating API proxy service..."
mkdir -p services/vas-api-proxy
cd services/vas-api-proxy

# Create package.json
cat > package.json << 'EOF'
{
  "name": "vas-api-proxy",
  "version": "1.0.0",
  "description": "CORS proxy for Anthropic API",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "@anthropic-ai/sdk": "^0.20.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.2"
  }
}
EOF

# Create server.js
cat > server.js << 'EOF'
const express = require('express');
const cors = require('cors');
const Anthropic = require('@anthropic-ai/sdk');

const app = express();
const PORT = process.env.PORT || 3002;

app.use(cors({
  origin: ['http://localhost:3001', 'http://localhost:3000', 'http://localhost:5173'],
  credentials: true
}));
app.use(express.json({ limit: '10mb' }));

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY || ''
});

app.get('/health', (req, res) => {
  res.json({ 
    status: 'UP', 
    service: 'vas-api-proxy',
    hasApiKey: !!process.env.ANTHROPIC_API_KEY,
    timestamp: new Date().toISOString()
  });
});

app.post('/api/messages', async (req, res) => {
  try {
    if (!process.env.ANTHROPIC_API_KEY) {
      return res.status(500).json({
        error: 'ANTHROPIC_API_KEY not configured',
        message: 'Set ANTHROPIC_API_KEY environment variable'
      });
    }

    const { messages, max_tokens = 1024, model = 'claude-sonnet-4-20250514' } = req.body;

    console.log(`[${new Date().toISOString()}] API request: ${messages?.length || 0} messages`);

    const response = await anthropic.messages.create({
      model,
      max_tokens,
      messages
    });

    res.json(response);
  } catch (error) {
    console.error(`[${new Date().toISOString()}] Error:`, error.message);
    res.status(500).json({
      error: error.message,
      type: error.type || 'unknown_error'
    });
  }
});

app.listen(PORT, () => {
  console.log(`╔═══════════════════════════════════════════════════════════╗`);
  console.log(`║     VAS-API-PROXY RUNNING                                 ║`);
  console.log(`╚═══════════════════════════════════════════════════════════╝`);
  console.log(``);
  console.log(`🌐 Server:  http://localhost:${PORT}`);
  console.log(`💚 Health:  http://localhost:${PORT}/health`);
  console.log(`🔑 API Key: ${process.env.ANTHROPIC_API_KEY ? '✓ Set' : '✗ Missing'}`);
  console.log(``);
  if (!process.env.ANTHROPIC_API_KEY) {
    console.log(`⚠️  WARNING: ANTHROPIC_API_KEY not set!`);
    console.log(`   Set it with: export ANTHROPIC_API_KEY=your-key-here`);
    console.log(``);
  }
});
EOF

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install --production

COPY server.js .

EXPOSE 3002

CMD ["node", "server.js"]
EOF

# Create README
cat > README.md << 'EOF'
# VAS API Proxy

CORS proxy for Anthropic API calls from the frontend.

## Usage

```bash
# Install
npm install

# Set API key
export ANTHROPIC_API_KEY=your-key-here

# Run
npm start
```

Service runs on http://localhost:3002
EOF

cd ../..
echo "✓ API proxy service created"
echo ""

# 5. Create .env.vas.example if missing
echo "[5/7] Creating environment example..."
if [ ! -f ".env.vas.example" ]; then
    cat > .env.vas.example << 'EOF'
# VAS-AI-Hospital Configuration

# Database Passwords
PATIENT_DB_PASSWORD=CHANGE_ME_STRONG_PASSWORD
CLINICAL_DB_PASSWORD=CHANGE_ME_STRONG_PASSWORD
ADMIN_DB_PASSWORD=CHANGE_ME_STRONG_PASSWORD
REDIS_PASSWORD=CHANGE_ME_STRONG_PASSWORD

# Security
ENCRYPTION_KEY=GENERATE_NEW_KEY_HERE
JWT_SECRET=GENERATE_NEW_SECRET_HERE

# MinIO
MINIO_ROOT_USER=vasadmin
MINIO_ROOT_PASSWORD=CHANGE_ME_STRONG_PASSWORD

# Anthropic API (optional)
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Demo Mode
DEMO_MODE=true
EOF
fi
echo "✓ Environment example created"
echo ""

# 6. Commit and push changes
echo "[6/7] Committing changes to Git..."
git add .
git commit -m "Add complete setup with API proxy and install script" 2>/dev/null || echo "  (no changes to commit)"
git push 2>/dev/null || echo "  (push failed or not configured)"
echo "✓ Git operations complete"
echo ""

# 7. Show next steps
echo "[7/7] Setup complete!"
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                SETUP COMPLETED SUCCESSFULLY! ✅            ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1️⃣  Install API proxy dependencies:"
echo "   cd services/vas-api-proxy"
echo "   npm install"
echo ""
echo "2️⃣  Set your Anthropic API key:"
echo "   export ANTHROPIC_API_KEY=your-key-here"
echo ""
echo "3️⃣  Start API proxy (in separate terminal):"
echo "   cd services/vas-api-proxy"
echo "   npm start"
echo ""
echo "4️⃣  Deploy VAS services:"
echo "   cd $REPO_DIR"
echo "   ./vas-simple-install.sh"
echo ""
echo "🌐 After deployment, access at:"
echo "   • Staff Dashboard:  http://localhost:3001"
echo "   • API Proxy:        http://localhost:3002/health"
echo "   • AI Gateway:       http://localhost:8888"
echo ""
