import { RotateCw, Sparkles } from 'lucide-react';
import { useCopilot } from '../context/CopilotContext';
import UploadPanel from './UploadPanel';
import { NAV_ITEMS } from './Sidebar';

const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform);

export default function Navbar({ activeView, data, refreshing, busy, onUpload, onRefresh }) {
  const { toggle, status } = useCopilot();
  const item = NAV_ITEMS.find((i) => i.key === activeView);
  const range = data?.date_range;

  return (
    <header className="topbar">
      <div className="topbar__crumbs">
        <span className="topbar__section">{item?.group}</span>
        <span className="sep">/</span>
        <h1 className="topbar__title">{item?.title || 'Overview'}</h1>
      </div>

      <div className="topbar__actions">
        {data && (
          <span className="pill" title={`${data.last_file_name} · loaded ${data.loaded_at ? new Date(data.loaded_at).toLocaleString() : ''}`}>
            <span className={`dot ${refreshing || busy ? 'dot--live' : 'dot--healthy'}`} />
            <span className="pill__text mono">{data.last_file_name}</span>
            {range && (
              <span className="muted mono">
                {range.start} → {range.end}
              </span>
            )}
          </span>
        )}
        {data && (
          <button className="btn btn--ghost btn--icon" onClick={onRefresh} title="Refresh" aria-label="Refresh data">
            <RotateCw size={14} style={refreshing ? { animation: 'spin 0.8s linear infinite' } : undefined} />
          </button>
        )}
        <UploadPanel onUpload={onUpload} busy={busy} />
        <button className="btn" onClick={toggle} title="AI Copilot">
          <Sparkles size={14} style={{ color: 'var(--accent-primary)' }} />
          Copilot
          <span className={`dot ${status.enabled ? 'dot--healthy' : 'dot--warning'}`} />
          <span className="kbd">{isMac ? '⌘' : 'Ctrl'} K</span>
        </button>
      </div>
    </header>
  );
}
