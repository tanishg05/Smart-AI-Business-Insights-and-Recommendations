import "./App.css";

function Sidebar() {
  return (
    <div className="sidebar">
      <h2 className="logo">SupplyChain AI</h2>

      <ul>
        <li>📊 Dashboard</li>
        <li>📈 Sales Performance</li>
        <li>📅 Seasonal Analysis</li>
        <li>⚙ Operational Insights</li>
        <li>🤖 AI Insights</li>
        <li>📌 Recommendations</li>
      </ul>
    </div>
  );
}

function Navbar() {
  return (
    <div className="navbar">
      <h1>Supply Chain Analytics Dashboard</h1>

      <div className="profile">
        <span>👤 Analyst</span>
      </div>
    </div>
  );
}

function App() {
  return (
    <div className="app-container">
      <Sidebar />
      <Navbar />

      <div className="page">
        <h2>Dashboard Overview</h2>

        <div className="kpi-grid">
          <div className="kpi-card">
            <h3>Total Sales</h3>
            <p>₹ 12,45,000</p>
          </div>

          <div className="kpi-card">
            <h3>Total Orders</h3>
            <p>3,245</p>
          </div>

          <div className="kpi-card">
            <h3>Active SKUs</h3>
            <p>148</p>
          </div>

          <div className="kpi-card">
            <h3>Demand Accuracy</h3>
            <p>92%</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;