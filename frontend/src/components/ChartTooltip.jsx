import { formatDate, formatNumber } from '../utils/formatters';

// Wrapped so a row object passed as the second argument is never read as a digits count.
const defaultFormat = (v) => formatNumber(v);

/**
 * Glass tooltip for Recharts.
 * `rows` overrides the default series list: [{ key, label, color, format }].
 */
export default function ChartTooltip({ active, payload, label, rows, labelFormatter, granularity, valueFormatter }) {
  if (!active || !payload?.length) return null;
  const datum = payload[0]?.payload || {};
  const title = labelFormatter ? labelFormatter(label, datum) : granularity ? formatDate(label, granularity) : label;

  const items = rows
    ? rows
        .filter((r) => datum[r.key] !== undefined && datum[r.key] !== null)
        .map((r) => ({ name: r.label, color: r.color, value: (r.format || defaultFormat)(datum[r.key], datum) }))
    : payload
        .filter((p) => p.value !== undefined && p.value !== null && !p.payload?.hidden)
        .map((p) => ({
          name: p.name,
          color: p.color || p.stroke || p.fill,
          value: (valueFormatter || defaultFormat)(Array.isArray(p.value) ? p.value.join(' – ') : p.value, p),
        }));

  return (
    <div className="tt">
      {title !== undefined && title !== '' && <div className="tt__title">{title}</div>}
      {items.map((item) => (
        <div className="tt__row" key={item.name}>
          {item.color && <span className="legend__swatch" style={{ background: item.color }} />}
          <span className="tt__name">{item.name}</span>
          <span className="tt__value">{item.value}</span>
        </div>
      ))}
    </div>
  );
}
