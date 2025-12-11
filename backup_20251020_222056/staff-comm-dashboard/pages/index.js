export default function Home() {
  return (
    <div style={{ padding: '50px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Staff Communication Dashboard</h1>
      <p>Service is operational</p>
      <div style={{ marginTop: '20px' }}>
        <a href="/api/health">Health Check</a>
      </div>
    </div>
  );
}
