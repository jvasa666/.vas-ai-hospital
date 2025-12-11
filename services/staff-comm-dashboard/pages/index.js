import { useEffect, useState, useRef } from 'react';
import io from 'socket.io-client';

export default function Dashboard() {
  const [socket, setSocket] = useState(null);
  const [user, setUser] = useState(null);
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [messages, setMessages] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [messageInput, setMessageInput] = useState('');
  const [username, setUsername] = useState('');
  const [role, setRole] = useState('nurse');
  const [department, setDepartment] = useState('emergency');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Login handler
  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:8085/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, role, department })
      });
      
      if (!response.ok) throw new Error('Login failed');
      
      const data = await response.json();
      
      if (data.token) {
        localStorage.setItem('token', data.token);
        localStorage.setItem('user', JSON.stringify(data.user));
        setUser(data.user);
        setIsAuthenticated(true);
        initSocket(data.token);
      }
    } catch (error) {
      console.error('Login failed:', error);
      alert('Login failed. Please make sure the backend is running.');
    }
  };

  // Initialize Socket.IO
  const initSocket = (token) => {
    const newSocket = io('http://localhost:8085', {
      transports: ['websocket', 'polling']
    });

    newSocket.on('connect', () => {
      console.log('✓ Connected to server');
      newSocket.emit('auth', token);
    });

    newSocket.on('auth:success', (data) => {
      console.log('✓ Authenticated:', data.user.name);
    });

    newSocket.on('auth:error', (data) => {
      console.error('✗ Auth error:', data.message);
      alert('Authentication failed');
    });

    newSocket.on('users:list', (users) => {
      console.log('Users list received:', users.length);
      setOnlineUsers(users);
    });

    newSocket.on('user:online', (user) => {
      console.log('User came online:', user.name);
      setOnlineUsers(prev => {
        if (!prev.find(u => u.id === user.id)) {
          return [...prev, user];
        }
        return prev;
      });
    });

    newSocket.on('user:offline', (data) => {
      console.log('User went offline:', data.id);
      setOnlineUsers(prev => prev.filter(u => u.id !== data.id));
    });

    newSocket.on('message:receive', (message) => {
      console.log('Message received:', message);
      setMessages(prev => [...prev, message]);
      
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('New Message', { 
          body: message.content,
          icon: '/hospital-icon.png'
        });
      }
    });

    newSocket.on('message:delivered', (data) => {
      console.log('Message delivered:', data);
    });

    newSocket.on('alert:emergency', (alert) => {
      console.log('🚨 Emergency alert:', alert);
      setAlerts(prev => [...prev, alert]);
      
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(`🚨 ${alert.type.toUpperCase()}`, { 
          body: `${alert.message} at ${alert.location}`,
          requireInteraction: true,
          tag: alert.id
        });
      }
      
      // Play alert sound
      try {
        const audio = new Audio('/alert-sound.mp3');
        audio.play().catch(e => console.log('Could not play sound:', e));
      } catch (e) {}
    });

    newSocket.on('typing:indicator', (data) => {
      if (data.from === selectedUser?.id) {
        setIsTyping(data.isTyping);
      }
    });

    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  };

  // Send message
  const sendMessage = () => {
    if (!messageInput.trim() || !selectedUser || !socket) return;
    
    socket.emit('message:send', {
      to: selectedUser.id,
      content: messageInput,
      priority: 'normal'
    });

    setMessages(prev => [...prev, {
      id: `temp-${Date.now()}`,
      from: user.id,
      to: selectedUser.id,
      content: messageInput,
      timestamp: new Date(),
      type: 'direct'
    }]);

    setMessageInput('');
  };

  // Trigger emergency code
  const triggerEmergency = (type) => {
    const location = prompt(`Enter location for ${type}:`);
    if (location && socket) {
      socket.emit('emergency:code', {
        type,
        location,
        message: `${type} activated`
      });
    }
  };

  // Request notification permission
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  // Load from localStorage
  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    
    if (savedToken && savedUser) {
      try {
        const parsedUser = JSON.parse(savedUser);
        setUser(parsedUser);
        setIsAuthenticated(true);
        initSocket(savedToken);
      } catch (e) {
        localStorage.clear();
      }
    }
  }, []);

  // Typing indicator
  let typingTimeout;
  const handleTyping = (e) => {
    setMessageInput(e.target.value);
    
    if (socket && selectedUser) {
      socket.emit('typing:start', { to: selectedUser.id });
      
      clearTimeout(typingTimeout);
      typingTimeout = setTimeout(() => {
        socket.emit('typing:stop', { to: selectedUser.id });
      }, 1000);
    }
  };

  // Logout
  const handleLogout = () => {
    if (socket) socket.close();
    localStorage.clear();
    setIsAuthenticated(false);
    setUser(null);
    setOnlineUsers([]);
    setMessages([]);
    setAlerts([]);
  };

  // LOGIN SCREEN
  if (!isAuthenticated) {
    return (
      <div style={{ 
        minHeight: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}>
        <div style={{ 
          background: 'white', 
          padding: '40px', 
          borderRadius: '10px', 
          boxShadow: '0 10px 40px rgba(0,0,0,0.2)',
          maxWidth: '400px',
          width: '100%'
        }}>
          <div style={{ textAlign: 'center', marginBottom: '30px' }}>
            <div style={{ fontSize: '48px', marginBottom: '10px' }}>🏥</div>
            <h1 style={{ fontSize: '24px', margin: '0', color: '#333' }}>Hospital Communications</h1>
            <p style={{ color: '#666', marginTop: '5px' }}>Real-time staff coordination</p>
          </div>
          
          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <input
              type="text"
              placeholder="Your Name"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={{ 
                padding: '12px', 
                fontSize: '16px', 
                border: '2px solid #e0e0e0', 
                borderRadius: '6px',
                outline: 'none',
                transition: 'border 0.3s'
              }}
              onFocus={(e) => e.target.style.borderColor = '#667eea'}
              onBlur={(e) => e.target.style.borderColor = '#e0e0e0'}
              required
            />
            
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              style={{ 
                padding: '12px', 
                fontSize: '16px', 
                border: '2px solid #e0e0e0', 
                borderRadius: '6px',
                outline: 'none'
              }}
            >
              <option value="doctor">👨‍⚕️ Doctor</option>
              <option value="nurse">👩‍⚕️ Nurse</option>
              <option value="admin">👔 Administrator</option>
              <option value="dispatcher">📞 Dispatcher</option>
              <option value="technician">🔧 Technician</option>
            </select>
            
            <select
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              style={{ 
                padding: '12px', 
                fontSize: '16px', 
                border: '2px solid #e0e0e0', 
                borderRadius: '6px',
                outline: 'none'
              }}
            >
              <option value="emergency">🚨 Emergency</option>
              <option value="icu">💊 ICU</option>
              <option value="surgery">🔬 Surgery</option>
              <option value="pediatrics">👶 Pediatrics</option>
              <option value="cardiology">❤️ Cardiology</option>
              <option value="radiology">📡 Radiology</option>
              <option value="pharmacy">💉 Pharmacy</option>
            </select>
            
            <button 
              type="submit" 
              style={{ 
                padding: '12px', 
                fontSize: '16px', 
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
                color: 'white', 
                border: 'none', 
                borderRadius: '6px', 
                cursor: 'pointer',
                fontWeight: 'bold',
                transition: 'transform 0.2s'
              }}
              onMouseOver={(e) => e.target.style.transform = 'scale(1.02)'}
              onMouseOut={(e) => e.target.style.transform = 'scale(1)'}
            >
              Login to System
            </button>
          </form>
          
          <div style={{ marginTop: '20px', textAlign: 'center', fontSize: '12px', color: '#999' }}>
            <p>Backend: http://localhost:8085</p>
          </div>
        </div>
      </div>
    );
  }

  // MAIN DASHBOARD
  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'system-ui, -apple-system, sans-serif', background: '#f5f7fa' }}>
      
      {/* SIDEBAR */}
      <div style={{ 
        width: '280px', 
        background: 'white', 
        borderRight: '1px solid #e0e0e0',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* User Info */}
        <div style={{ padding: '20px', borderBottom: '1px solid #e0e0e0', background: '#667eea', color: 'white' }}>
          <div style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '5px' }}>{user.name}</div>
          <div style={{ fontSize: '14px', opacity: 0.9 }}>{user.role} • {user.department}</div>
          <button 
            onClick={handleLogout}
            style={{ 
              marginTop: '10px', 
              padding: '6px 12px', 
              background: 'rgba(255,255,255,0.2)', 
              color: 'white', 
              border: 'none', 
              borderRadius: '4px', 
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            Logout
          </button>
        </div>

        {/* Online Users */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '15px' }}>
          <h3 style={{ fontSize: '14px', color: '#666', marginBottom: '15px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Online Staff ({onlineUsers.filter(u => u.id !== user.id).length})
          </h3>
          
          {onlineUsers.filter(u => u.id !== user.id).length === 0 ? (
            <div style={{ textAlign: 'center', color: '#999', padding: '20px', fontSize: '14px' }}>
              No other staff online
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {onlineUsers.filter(u => u.id !== user.id).map(u => (
                <div
                  key={u.id}
                  onClick={() => setSelectedUser(u)}
                  style={{
                    padding: '12px',
                    background: selectedUser?.id === u.id ? '#667eea' : '#f8f9fa',
                    color: selectedUser?.id === u.id ? 'white' : '#333',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    border: selectedUser?.id === u.id ? '2px solid #667eea' : '2px solid transparent',
                    transition: 'all 0.2s'
                  }}
                  onMouseOver={(e) => {
                    if (selectedUser?.id !== u.id) {
                      e.currentTarget.style.background = '#e9ecef';
                    }
                  }}
                  onMouseOut={(e) => {
                    if (selectedUser?.id !== u.id) {
                      e.currentTarget.style.background = '#f8f9fa';
                    }
                  }}
                >
                  <div style={{ fontWeight: 'bold', marginBottom: '3px' }}>{u.name}</div>
                  <div style={{ fontSize: '12px', opacity: 0.8 }}>
                    {u.role} • {u.department}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        
        {/* HEADER */}
        <div style={{ 
          padding: '20px', 
          background: 'white', 
          borderBottom: '1px solid #e0e0e0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <h1 style={{ fontSize: '24px', margin: 0, color: '#333' }}>
              🏥 Hospital Communications System
            </h1>
            <div style={{ fontSize: '14px', color: '#666', marginTop: '5px' }}>
              Real-time coordination platform
            </div>
          </div>
          
          <div style={{ fontSize: '14px', color: '#666' }}>
            {socket ? '🟢 Connected' : '🔴 Disconnected'}
          </div>
        </div>

        {/* EMERGENCY BUTTONS */}
        <div style={{ 
          padding: '15px 20px', 
          background: '#fff3cd', 
          borderBottom: '1px solid #ffc107',
          display: 'flex', 
          gap: '10px',
          flexWrap: 'wrap'
        }}>
          <button 
            onClick={() => triggerEmergency('CODE_BLUE')} 
            style={{ 
              padding: '10px 20px', 
              background: '#dc3545', 
              color: 'white', 
              border: 'none', 
              borderRadius: '6px', 
              cursor: 'pointer', 
              fontWeight: 'bold',
              fontSize: '14px',
              transition: 'transform 0.2s'
            }}
            onMouseOver={(e) => e.target.style.transform = 'scale(1.05)'}
            onMouseOut={(e) => e.target.style.transform = 'scale(1)'}
          >
            🚨 CODE BLUE
          </button>
          <button 
            onClick={() => triggerEmergency('CODE_RED')} 
            style={{ 
              padding: '10px 20px', 
              background: '#fd7e14', 
              color: 'white', 
              border: 'none', 
              borderRadius: '6px', 
              cursor: 'pointer', 
              fontWeight: 'bold',
              fontSize: '14px',
              transition: 'transform 0.2s'
            }}
            onMouseOver={(e) => e.target.style.transform = 'scale(1.05)'}
            onMouseOut={(e) => e.target.style.transform = 'scale(1)'}
          >
            🔥 CODE RED
          </button>
          <button 
            onClick={() => triggerEmergency('RAPID_RESPONSE')} 
            style={{ 
              padding: '10px 20px', 
              background: '#ffc107', 
              color: '#000', 
              border: 'none', 
              borderRadius: '6px', 
              cursor: 'pointer', 
              fontWeight: 'bold',
              fontSize: '14px',
              transition: 'transform 0.2s'
            }}
            onMouseOver={(e) => e.target.style.transform = 'scale(1.05)'}
            onMouseOut={(e) => e.target.style.transform = 'scale(1)'}
          >
            ⚡ RAPID RESPONSE
          </button>
        </div>

        {/* ACTIVE ALERTS */}
        {alerts.length > 0 && (
          <div style={{ 
            maxHeight: '150px', 
            overflowY: 'auto', 
            background: '#f8d7da', 
            borderBottom: '1px solid #f5c6cb',
            padding: '15px 20px'
          }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#721c24', fontSize: '16px' }}>
              🚨 Active Alerts ({alerts.length})
            </h3>
            {alerts.slice(-5).reverse().map(alert => (
              <div 
                key={alert.id} 
                style={{ 
                  padding: '10px', 
                  background: 'white', 
                  marginBottom: '8px', 
                  borderRadius: '6px', 
                  borderLeft: '4px solid #dc3545' 
                }}
              >
                <div style={{ fontWeight: 'bold', color: '#dc3545' }}>
                  {alert.type} at {alert.location}
                </div>
                <div style={{ fontSize: '13px', color: '#666', marginTop: '4px' }}>
                  {alert.message} • {new Date(alert.timestamp).toLocaleTimeString()}
                  {alert.initiatedBy && ` • By: ${alert.initiatedBy}`}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* MESSAGES AREA */}
        <div style={{ 
          flex: 1, 
          padding: '20px', 
          overflowY: 'auto', 
          background: '#f5f7fa' 
        }}>
          {selectedUser ? (
            <>
              <div style={{ 
                marginBottom: '20px', 
                paddingBottom: '15px', 
                borderBottom: '2px solid #e0e0e0' 
              }}>
                <h2 style={{ margin: 0, fontSize: '20px', color: '#333' }}>
                  Chat with {selectedUser.name}
                </h2>
                <div style={{ fontSize: '14px', color: '#666', marginTop: '5px' }}>
                  {selectedUser.role} • {selectedUser.department}
                </div>
              </div>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {messages
                  .filter(m => 
                    (m.from === user.id && m.to === selectedUser.id) || 
                    (m.from === selectedUser.id && m.to === user.id)
                  )
                  .map((msg, idx) => (
                    <div
                      key={msg.id || idx}
                      style={{
                        display: 'flex',
                        justifyContent: msg.from === user.id ? 'flex-end' : 'flex-start'
                      }}
                    >
                      <div
                        style={{
                          padding: '12px 16px',
                          background: msg.from === user.id ? '#667eea' : 'white',
                          color: msg.from === user.id ? 'white' : '#333',
                          borderRadius: '12px',
                          maxWidth: '70%',
                          boxShadow: '0 2px 5px rgba(0,0,0,0.1)',
                          border: msg.from === user.id ? 'none' : '1px solid #e0e0e0'
                        }}
                      >
                        <div style={{ wordBreak: 'break-word' }}>{msg.content}</div>
                        <div style={{ 
                          fontSize: '11px', 
                          marginTop: '6px', 
                          opacity: 0.7,
                          textAlign: 'right'
                        }}>
                          {new Date(msg.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  ))}
                <div ref={messagesEndRef} />
              </div>
              
              {isTyping && (
                <div style={{ 
                  fontSize: '13px', 
                  color: '#666', 
                  fontStyle: 'italic',
                  marginTop: '10px'
                }}>
                  {selectedUser.name} is typing...
                </div>
              )}
            </>
          ) : (
            <div style={{ 
              textAlign: 'center', 
              color: '#999', 
              marginTop: '100px',
              fontSize: '16px'
            }}>
              <div style={{ fontSize: '48px', marginBottom: '20px' }}>💬</div>
              <div>Select a staff member to start messaging</div>
            </div>
          )}
        </div>

        {/* MESSAGE INPUT */}
        {selectedUser && (
          <div style={{ 
            padding: '20px', 
            background: 'white', 
            borderTop: '1px solid #e0e0e0',
            display: 'flex', 
            gap: '12px',
            alignItems: 'center'
          }}>
            <input
              type="text"
              value={messageInput}
              onChange={handleTyping}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Type your message..."
              style={{ 
                flex: 1, 
                padding: '12px 16px', 
                fontSize: '16px', 
                border: '2px solid #e0e0e0', 
                borderRadius: '8px',
                outline: 'none',
                transition: 'border 0.3s'
              }}
              onFocus={(e) => e.target.style.borderColor = '#667eea'}
              onBlur={(e) => e.target.style.borderColor = '#e0e0e0'}
            />
            <button 
              onClick={sendMessage} 
              disabled={!messageInput.trim()}
              style={{ 
                padding: '12px 30px', 
                background: messageInput.trim() ? '#667eea' : '#ccc', 
                color: 'white', 
                border: 'none', 
                borderRadius: '8px', 
                cursor: messageInput.trim() ? 'pointer' : 'not-allowed', 
                fontWeight: 'bold',
                fontSize: '16px',
                transition: 'all 0.2s'
              }}
              onMouseOver={(e) => {
                if (messageInput.trim()) {
                  e.target.style.background = '#5568d3';
                  e.target.style.transform = 'scale(1.05)';
                }
              }}
              onMouseOut={(e) => {
                if (messageInput.trim()) {
                  e.target.style.background = '#667eea';
                  e.target.style.transform = 'scale(1)';
                }
              }}
            >
              Send →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
