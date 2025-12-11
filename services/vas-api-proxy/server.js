const express = require('express');
const cors = require('cors');
const Anthropic = require('@anthropic-ai/sdk');

const app = express();
const PORT = process.env.PORT || 3002;

// Middleware
app.use(cors({
  origin: ['http://localhost:3001', 'http://localhost:3000'],
  credentials: true
}));
app.use(express.json({ limit: '10mb' }));

// Initialize Anthropic client
const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY || 'your-api-key-here'
});

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'UP', 
    service: 'vas-api-proxy',
    timestamp: new Date().toISOString()
  });
});

// Proxy endpoint
app.post('/api/messages', async (req, res) => {
  try {
    const { messages, max_tokens = 1024, model = 'claude-sonnet-4-20250514' } = req.body;

    console.log('[API-PROXY] Forwarding request to Anthropic');

    const response = await anthropic.messages.create({
      model,
      max_tokens,
      messages
    });

    res.json(response);
  } catch (error) {
    console.error('[API-PROXY] Error:', error.message);
    res.status(500).json({
      error: error.message,
      type: error.type || 'unknown_error'
    });
  }
});

app.listen(PORT, () => {
  console.log(`[VAS-API-PROXY] Running on http://localhost:${PORT}`);

  console.log('[VAS-API-PROXY] Health: http://localhost:\/health');
});
