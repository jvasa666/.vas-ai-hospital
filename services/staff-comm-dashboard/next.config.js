module.exports = {
  reactStrictMode: true,
  env: {
    AI_COMM_SERVICE_URL: process.env.AI_COMM_SERVICE_URL || 'http://localhost:8085'
  }
}
