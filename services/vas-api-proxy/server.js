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
