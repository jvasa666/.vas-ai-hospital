import express, { Request, Response } from 'express';
import cors from 'cors';

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// In-memory storage
interface User {
  id: string;
  username: string;
  role: string;
  email: string;
  createdAt: string;
}

const users: User[] = [
  {
    id: 'U001',
    username: 'admin',
    role: 'administrator',
    email: 'admin@hospital.com',
    createdAt: new Date().toISOString()
  },
  {
    id: 'U002',
    username: 'doctor1',
    role: 'physician',
    email: 'doctor1@hospital.com',
    createdAt: new Date().toISOString()
  }
];

// Health check
app.get('/api/health', (req: Request, res: Response) => {
  res.json({
    status: 'UP',
    service: 'admin-service',
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});

// Get all users
app.get('/api/users', (req: Request, res: Response) => {
  res.json({
    users: users,
    total: users.length
  });
});

// Get user by id
app.get('/api/users/:id', (req: Request, res: Response) => {
  const user = users.find(u => u.id === req.params.id);
  if (!user) {
    return res.status(404).json({ error: 'User not found' });
  }
  res.json(user);
});

// Create user
app.post('/api/users', (req: Request, res: Response) => {
  const newUser: User = {
    id: +'U' + String(users.length + 1).padStart(3, '0'),
    username: req.body.username,
    role: req.body.role || 'staff',
    email: req.body.email,
    createdAt: new Date().toISOString()
  };
  users.push(newUser);
  res.status(201).json(newUser);
});

// Update user
app.put('/api/users/:id', (req: Request, res: Response) => {
  const index = users.findIndex(u => u.id === req.params.id);
  if (index === -1) {
    return res.status(404).json({ error: 'User not found' });
  }
  users[index] = { ...users[index], ...req.body };
  res.json(users[index]);
});

// Delete user
app.delete('/api/users/:id', (req: Request, res: Response) => {
  const index = users.findIndex(u => u.id === req.params.id);
  if (index === -1) {
    return res.status(404).json({ error: 'User not found' });
  }
  users.splice(index, 1);
  res.json({ message: 'User deleted successfully' });
});

// System stats
app.get('/api/stats', (req: Request, res: Response) => {
  res.json({
    totalUsers: users.length,
    usersByRole: {
      administrator: users.filter(u => u.role === 'administrator').length,
      physician: users.filter(u => u.role === 'physician').length,
      nurse: users.filter(u => u.role === 'nurse').length,
      staff: users.filter(u => u.role === 'staff').length
    },
    uptime: process.uptime(),
    timestamp: new Date().toISOString()
  });
});

// Start server
app.listen(PORT, () => {
  console.log('+Admin Service running on port '+PORT);
  console.log('+Health check: http://localhost:'+PORT+'/api/health');
});
