import { Boxes, BrainCircuit, CalendarRange, Gauge, SlidersHorizontal, TrendingUp } from 'lucide-react';
import { useCopilot } from '../context/CopilotContext';

export const NAV_ITEMS = [
  { key: 'dashboard', label: 'Overview', title: 'Executive Overview', icon: Gauge, group: 'Analytics', kbd: '1' },
  { key: 'sales', label: 'Demand & Sales', title: 'Demand & Sales', icon: TrendingUp, group: 'Analytics', kbd: '2' },
  { key: 'operations', label: 'Operations', title: 'Lead Time & Operations', icon: Boxes, group: 'Analytics', kbd: '3' },
  { key: 'seasonality', label: 'Seasonality', title: 'Seasonality & Forecast', icon: CalendarRange, group: 'Analytics', kbd: '4' },
  { key: 'simulator', label: 'Scenario Lab', title: 'What-if Scenario Lab', icon: SlidersHorizontal, group: 'Intelligence', kbd: '5' },
  { key: 'ai', label: 'Intelligence Hub', title: 'Supply Chain Intelligence Hub', icon: BrainCircuit, group: 'Intelligence', kbd: '6' },
];

function Mark() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
      <path d="M2 10.5 5 7l2.5 2L12 3.5" stroke="#38BDF8" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="12" cy="3.5" r="1.3" fill="#E6EAF2" />
    </svg>
  );
}

export default function Sidebar({ activeView, onSelect, data }) {
  const { status } = useCopilot();
  const groups = [...new Set(NAV_ITEMS.map((i) => i.group))];

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand__mark">
          <Mark />
        </div>
        <div className="brand__text">
          <div className="brand__name">Supply Chain</div>
          <div className="brand__sub">Intelligence</div>
        </div>
      </div>

      {groups.map((group) => (
        <nav className="nav-group" key={group} aria-label={group}>
          <div className="nav-group__label">{group}</div>
          {NAV_ITEMS.filter((i) => i.group === group).map(({ key, label, icon: Icon, kbd }) => (
            <button
              key={key}
              type="button"
              className={`nav-item ${activeView === key ? 'active' : ''}`}
              onClick={() => onSelect(key)}
              aria-current={activeView === key ? 'page' : undefined}
            >
              <Icon size={15} strokeWidth={1.75} />
              <span>{label}</span>
              <span className="kbd nav-item__kbd">{kbd}</span>
            </button>
          ))}
        </nav>
      ))}

      <div className="sidebar__footer">
        <div className="status-card">
          <div className="status-card__row">
            <span className="muted">Dataset</span>
            <span className="mono" title={data?.last_file_name}>{data?.last_file_name || '—'}</span>
          </div>
          <div className="status-card__row">
            <span className="muted">Rows</span>
            <span className="mono">{data?.total_rows ? data.total_rows.toLocaleString() : '—'}</span>
          </div>
          <div className="status-card__row">
            <span className="muted">Engine</span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <span className={`dot ${status.enabled ? 'dot--healthy' : 'dot--warning'}`} />
              {status.enabled ? 'Groq live' : 'Local'}
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}
