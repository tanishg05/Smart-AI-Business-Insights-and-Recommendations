import { BarChart3, Sparkles, TrendingUp, CalendarRange, ClipboardList, Lightbulb } from 'lucide-react';

const items = [
  { key: 'dashboard', label: 'Dashboard', icon: BarChart3 },
  { key: 'sales', label: 'Sales Performance', icon: TrendingUp },
  { key: 'seasonality', label: 'Seasonal Analysis', icon: CalendarRange },
  { key: 'operations', label: 'Operational Insights', icon: ClipboardList },
  { key: 'ai', label: 'AI Insights', icon: Sparkles },
  { key: 'recommendations', label: 'Recommendations', icon: Lightbulb }
];

export default function Sidebar({ activeView, onSelect }) {
  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <div className="sidebar__logo">SC</div>
        <div>
          <h3>Supply Chain</h3>
          <p>Intelligence Suite</p>
        </div>
      </div>

      <nav className="sidebar__nav">
        {items.map(({ key, label, icon: Icon }) => (
          <button key={key} className={`nav-item ${activeView === key ? 'active' : ''}`} onClick={() => onSelect(key)}>
            <Icon size={18} />
            <span>{label}</span>
          </button>
        ))}
      </nav>
    </aside>
  );
}
