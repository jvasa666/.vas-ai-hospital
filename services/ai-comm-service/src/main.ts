import express, { Request, Response } from 'express';
import { WebSocketServer, WebSocket } from 'ws';
import { createClient } from 'redis';

const app = express();
const PORT = process.env.PORT || 3001; // New Service Port

// Redis Client for Pub/Sub (Pillar 3: Synchronize)
const redisClient = createClient({
    url: `redis://${process.env.REDIS_HOST || 'redis'}:6379` // Assuming Docker Compose name 'redis'
});
redisClient.on('error', err => console.error('Redis Client Error', err));
redisClient.connect();

// WebSocket Server (Pillar 3: Synchronize - Real-time push)
const wss = new WebSocketServer({ port: 3002 });
const staffConnections = new Set<WebSocket>();

wss.on('connection', function connection(ws) {
    staffConnections.add(ws);
    console.log(`[P3] Staff member connected. Total: ${staffConnections.size}`);
    
    ws.on('close', () => {
        staffConnections.delete(ws);
        console.log(`[P3] Staff member disconnected. Total: ${staffConnections.size}`);
    });
});

// AI Call Prioritization Logic (Pillar 8: Orchestrate & Pillar 13: Empathy)
function prioritizeCall(callData: any): string {
    const { urgency, patientVitals } = callData;

    // Direct Routing based on urgency
    if (urgency === 'CODE_BLUE' || patientVitals.heartRate < 40 || patientVitals.spo2 < 85) {
        return 'CRITICAL_HIGH';
    }
    if (urgency === 'PAIN_SEVERE' || patientVitals.temp > 102) {
        return 'HIGH';
    }
    if (urgency === 'ASSISTANCE') {
        return 'NORMAL';
    }
    return 'LOW';
}

// --- REST ENDPOINTS ---

// Health Check
app.get('/api/health', (req: Request, res: Response) => {
    res.json({
        status: 'UP',
        service: 'ai-comm-service',
        redis: redisClient.isReady ? 'CONNECTED' : 'DISCONNECTED',
        ws_clients: staffConnections.size
    });
});

// Patient Bedside Call Endpoint (The Smart Call Button)
app.post('/api/call/patient', async (req: Request, res: Response) => {
    const callData = req.body;
    const priority = prioritizeCall(callData);
    
    const task = {
        taskId: `T${Date.now()}`,
        patientId: callData.patientId,
        message: callData.message,
        priority: priority, // CRITICAL_HIGH, HIGH, NORMAL, LOW
        timestamp: new Date().toISOString()
    };
    
    // 1. Log to Audit (Pillar 9 is external, assumed to be called via ZFP AI-API here)
    console.log(`[P9] Logging Task Creation: ${task.taskId} with Priority ${priority}`);
    
    // 2. Publish to Redis Queue (Pillar 3: Synchronize)
    await redisClient.publish('hospital:critical_tasks', JSON.stringify(task));
    
    // 3. Push via WebSocket (Pillar 3: Real-time Staff Alert)
    const notification = JSON.stringify({ type: 'NEW_TASK', task });
    staffConnections.forEach(ws => ws.send(notification));

    res.status(202).json({ taskId: task.taskId, priority: priority, status: 'Task Routed' });
});


// --- START SERVER ---
app.listen(PORT, () => {
    console.log(`+AI Comm Service running on port ${PORT}`);
});