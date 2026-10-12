export default function Navbar({ activeView, datasetName }) {
  return (
    <header className="navbar">
      <div>
        <p className="eyebrow">Business Analytics Dashboard</p>
        <h1>{activeViewLabel(activeView)}</h1>
      </div>

      <div className="navbar__meta">
        <span className="badge">Dataset: {datasetName || 'Not loaded'}</span>
      </div>
    </header>
  );
}

function activeViewLabel(view) {
  const map = {
    dashboard: 'Executive Overview',
    sales: 'Sales Performance',
    seasonality: 'Seasonal Analysis',
    operations: 'Operational Insights',
    ai: 'AI Insights',
    recommendations: 'Recommendations'
  };

  return map[view] || 'Dashboard';
}
