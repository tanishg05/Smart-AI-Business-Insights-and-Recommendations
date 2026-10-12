import { CornerDownRight, Sparkles } from 'lucide-react';
import { useCopilot } from '../context/CopilotContext';
import { formatCurrency } from '../utils/formatters';
import { SkeletonBlock } from './Loader';

export default function InsightPills({ insights, loading, limit }) {
  const { ask } = useCopilot();

  if (loading && !insights) {
    return (
      <div className="insight-list">
        {Array.from({ length: 3 }).map((_, i) => (
          <div className="insight" key={i} style={{ paddingLeft: 14 }}>
            <span />
            <div style={{ display: 'grid', gap: 8 }}>
              <SkeletonBlock height={12} width="40%" />
              <SkeletonBlock height={10} width="85%" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  const list = (insights || []).slice(0, limit || undefined);
  if (!list.length) return <p className="muted">No threshold breaches in the current slice.</p>;

  return (
    <div className="insight-list">
      {list.map((item, i) => (
        <article key={item.id} className={`insight insight--${item.severity}`} style={{ animationDelay: `${i * 50}ms` }}>
          <span className="insight__rail" />
          <div>
            <div className="insight__head">
              <span className={`badge badge--${item.severity.toLowerCase()}`}>{item.severity}</span>
              <h4 className="insight__title">{item.title}</h4>
            </div>
            <p className="insight__detail">{item.detail}</p>
            <p className="insight__action">
              <CornerDownRight size={13} />
              {item.action}
            </p>
          </div>
          <div className="insight__side">
            <div>
              <div className="insight__metric-label">{item.metric?.label}</div>
              <div className="insight__metric-value">{item.metric?.value}</div>
              {item.impact_usd > 0 && !String(item.metric?.value).startsWith('$') && <div className="muted mono" style={{ fontSize: 11 }}>≈ {formatCurrency(item.impact_usd, { compact: true })}</div>}
            </div>
            <button className="inspect-btn" onClick={() => ask(item.query)} title="Ask the copilot">
              <Sparkles size={13} />
              Investigate
            </button>
          </div>
        </article>
      ))}
    </div>
  );
}
