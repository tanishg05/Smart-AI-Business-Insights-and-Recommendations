import { useState } from 'react';
import { formatCompact, formatNumber } from '../utils/formatters';

// Diverging ramp around 1.0: coral below the region's average, ice blue above.
function cellColor(index) {
  const d = Math.max(-1, Math.min(1, (index - 1) / 0.25));
  if (d >= 0) return `rgba(56, 189, 248, ${0.06 + d * 0.5})`;
  return `rgba(239, 68, 68, ${0.06 + -d * 0.42})`;
}

export default function Heatmap({ heatmap, onSelect }) {
  const [active, setActive] = useState(null);
  if (!heatmap?.cells?.length) return <p className="muted">No seasonal data.</p>;
  const { seasons, regions, cells } = heatmap;
  const lookup = Object.fromEntries(cells.map((c) => [`${c.season}|${c.region}`, c]));
  const current = active ? lookup[active] : null;

  return (
    <div>
      <div className="heatmap" style={{ gridTemplateColumns: `minmax(80px, auto) repeat(${regions.length}, minmax(0, 1fr))` }}>
        <div className="heatmap__corner">Season</div>
        {regions.map((r) => (
          <div key={r} className="heatmap__col">
            {r}
          </div>
        ))}
        {seasons.map((s) => (
          <div key={s} style={{ display: 'contents' }}>
            <div className="heatmap__row">{s}</div>
            {regions.map((r) => {
              const cell = lookup[`${s}|${r}`];
              const key = `${s}|${r}`;
              if (!cell) return <div key={key} className="heatmap__cell" style={{ opacity: 0.3 }} />;
              return (
                <button
                  type="button"
                  key={key}
                  className={`heatmap__cell ${active === key ? 'is-active' : ''}`}
                  style={{ background: cellColor(cell.index) }}
                  onMouseEnter={() => setActive(key)}
                  onMouseLeave={() => setActive(null)}
                  onFocus={() => setActive(key)}
                  onClick={() => onSelect?.(cell)}
                  title={`${s} · ${r}: index ${cell.index.toFixed(2)}`}
                >
                  <span className="heatmap__idx">{cell.index.toFixed(2)}</span>
                  <span className="heatmap__sub">{formatCompact(cell.daily)}/day</span>
                </button>
              );
            })}
          </div>
        ))}
      </div>
      <div className="heatmap__scale">
        <span>0.75</span>
        <div className="heatmap__ramp" style={{ background: 'linear-gradient(90deg, rgba(239,68,68,.48), rgba(255,255,255,.04), rgba(56,189,248,.56))' }} />
        <span>1.25</span>
        <span style={{ marginLeft: 'auto' }} className="secondary">
          {current
            ? `${current.season} · ${current.region} — ${formatNumber(current.units)} units, lead ${current.lead.toFixed(2)}d`
            : 'Index = daily units ÷ region average'}
        </span>
      </div>
    </div>
  );
}
