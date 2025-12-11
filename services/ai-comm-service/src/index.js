const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');
const jwt = require('jsonwebtoken');
const cors = require('cors');
const helmet = require('helmet');

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: {
    origin: ['http://localhost:3000', 'http://localhost:3001', 'http://localhost:3003'],
    credentials: true
  }
});

app.use(helmet());
app.use(cors());
app.use(express.json());

const JWT_SECRET = process.env.JWT_SECRET || 'hospital-secret-change-in-production';
const users = new Map();
const messages = new Map();
const alerts = new Map();
const userSockets = new Map();

console.log('🏥 Initializing Hospital Communications System...');

// Health endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'ai-comm-service',
    timestamp: new Date().toISOString(),
    connections: io.engine.clientsCount,
    uptime: Math.floor(process.uptime())
  });
});

app.get('/ready', (req, res) => {
  res.json({ ready: true, service: 'ai-comm-service' });
});

// Auth endpoint
app.post('/api/auth/login', (req, res) => {
  const { username, password, role, department } = req.body;
  
  const userId = `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  const token = jwt.sign(
    { id: userId, username, role: role || 'nurse', department: department || 'general' },
    JWT_SECRET,
    { expiresIn: '24h' }
  );

  const user = {
    id: userId,
    name: username,
    role: role || 'nurse',
    department: department || 'general',
    status: 'available'
  };

  users.set(userId, user);
  
  console.log(`✓ User logged in: ${username} (${role})`);
  
  res.json({ token, user });
});

// Get online users
app.get('/api/users/online', (req, res) => {
  const onlineUsers = Array.from(users.values()).filter(u => u.socketId);
  res.json({ users: onlineUsers, count: onlineUsers.length });
});

// Send message
app.post('/api/messages/send', (req, res) => {
  const { to, from, content, priority } = req.body;

  const message = {
    id: `msg-${Date.now()}`,
    from,
    to,
    type: 'direct',
    priority: priority || 'normal',
    content,
    timestamp: new Date(),
    readBy: [],
    deliveredTo: []
  };

  messages.set(message.id, message);

  const targetSocket = userSockets.get(to);
  if (targetSocket) {
    io.to(targetSocket).emit('message:receive', message);
    message.deliveredTo.push(to);
  }

  res.json({ success: true, message });
});

// Broadcast alert
app.post('/api/alerts/broadcast', (req, res) => {
  const { type, location, message, priority } = req.body;
  
  const alert = {
    id: `alert-${Date.now()}`,
    type: type || 'info',
    location,
    message,
    priority: priority || 'info',
    timestamp: new Date(),
    acknowledgedBy: []
  };

  alerts.set(alert.id, alert);
  io.emit('alert:emergency', alert);

  console.log(`🚨 ALERT BROADCAST: ${type} at ${location}`);

  res.json({ success: true, alert });
});

// Get active alerts
app.get('/api/alerts/active', (req, res) => {
  const activeAlerts = Array.from(alerts.values()).filter(a => !a.resolvedAt);
  res.json({ alerts: activeAlerts, count: activeAlerts.length });
});

// Socket.IO connection handler
io.on('connection', (socket) => {
  console.log(`✓ Client connected: ${socket.id}`);

  socket.on('auth', (token) => {
    try {
      const decoded = jwt.verify(token, JWT_SECRET);
      socket.data.user = decoded;
      
      const user = users.get(decoded.id) || {
        id: decoded.id,
        name: decoded.username,
        role: decoded.role,
        department: decoded.department,
        status: 'available'
      };
      
      user.socketId = socket.id;
      users.set(decoded.id, user);
      userSockets.set(decoded.id, socket.id);

      socket.join(`department:${decoded.department}`);
      socket.join(`role:${decoded.role}`);

      const onlineUsers = Array.from(users.values())
        .filter(u => u.socketId)
        .map(u => ({ 
          id: u.id, 
          name: u.name, 
          role: u.role, 
          department: u.department, 
          status: u.status 
        }));
      
      socket.emit('auth:success', { user });
      socket.emit('users:list', onlineUsers);
      socket.broadcast.emit('user:online', { 
        id: user.id, 
        name: user.name, 
        role: user.role 
      });

      console.log(`✓ User authenticated: ${decoded.username} (${decoded.role})`);
    } catch (err) {
      socket.emit('auth:error', { message: 'Invalid token' });
      console.error('Auth error:', err.message);
    }
  });

  socket.on('message:send', (data) => {
    const user = socket.data.user;
    if (!user) return;

    const message = {
      id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      from: user.id,
      to: data.to,
      type: 'direct',
      priority: data.priority || 'normal',
      content: data.content,
      timestamp: new Date(),
      readBy: [],
      deliveredTo: []
    };

    messages.set(message.id, message);

    const targetSocket = userSockets.get(data.to);
    if (targetSocket) {
      io.to(targetSocket).emit('message:receive', message);
      socket.emit('message:delivered', { messageId: message.id, to: data.to });
    }

    console.log(`📨 Message: ${user.username} → user ${data.to}`);
  });

  socket.on('status:update', (status) => {
    const user = socket.data.user;
    if (!user) return;

    const currentUser = users.get(user.id);
    if (currentUser) {
      currentUser.status = status;
      io.emit('user:status_changed', { userId: user.id, status });
    }
  });

  socket.on('typing:start', (data) => {
    const targetSocket = userSockets.get(data.to);
    if (targetSocket) {
      io.to(targetSocket).emit('typing:indicator', { 
        from: socket.data.user?.id, 
        isTyping: true 
      });
    }
  });

  socket.on('typing:stop', (data) => {
    const targetSocket = userSockets.get(data.to);
    if (targetSocket) {
      io.to(targetSocket).emit('typing:indicator', { 
        from: socket.data.user?.id, 
        isTyping: false 
      });
    }
  });

  socket.on('emergency:code', (data) => {
    const user = socket.data.user;
    if (!user) return;

    const alert = {
      id: `alert-${Date.now()}`,
      type: data.type,
      location: data.location,
      message: data.message,
      priority: 'emergency',
      timestamp: new Date(),
      acknowledgedBy: [],
      initiatedBy: user.username
    };

    alerts.set(alert.id, alert);
    io.emit('alert:emergency', alert);

    console.log(`🚨 EMERGENCY CODE: ${data.type} at ${data.location} by ${user.username}`);
  });

  socket.on('disconnect', () => {
    const user = socket.data.user;
    if (user) {
      const disconnectedUser = users.get(user.id);
      if (disconnectedUser) {
        disconnectedUser.socketId = undefined;
        disconnectedUser.status = 'offline';
      }
      userSockets.delete(user.id);
      socket.broadcast.emit('user:offline', { id: user.id });
      console.log(`✗ User disconnected: ${user.username || 'unknown'}`);
    }
  });
});

const PORT = process.env.PORT || 3001;

httpServer.listen(PORT, '0.0.0.0', () => {
  console.log('');
  console.log('='.repeat(70));
  console.log('  🏥 HOSPITAL COMMUNICATIONS SYSTEM - OPERATIONAL');
  console.log('='.repeat(70));
  console.log(`  📡 HTTP API:        http://localhost:${PORT}`);
  console.log(`  🔌 WebSocket:       ws://localhost:${PORT}`);
  console.log(`  ✅ Health Check:    http://localhost:${PORT}/health`);
  console.log(`  👥 Online Users:    http://localhost:${PORT}/api/users/online`);
  console.log('='.repeat(70));
  console.log('');
});

process.on('SIGTERM', () => {
  console.log('Shutting down gracefully...');
  httpServer.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});
