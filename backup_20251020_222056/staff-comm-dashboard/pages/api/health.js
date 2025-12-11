export default function handler(req, res) {
  res.status(200).json({
    status: 'healthy',
    service: 'staff-comm-dashboard',
    timestamp: new Date().toISOString()
  });
}
