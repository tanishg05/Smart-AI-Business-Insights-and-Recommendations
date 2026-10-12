import { formatMetric, formatNumber, formatPercent } from '../utils/formatters';

export default function KPIGrid({ metrics }) {
  return (
    <div className="kpi-grid">
      {metrics.map((metric) => (
        <div className="kpi-card" key={metric.label}>
          <p className="kpi-label">{metric.label}</p>
          <h3 className="kpi-value">{renderValue(metric)}</h3>
          {metric.subtitle ? <p className="kpi-subtitle">{metric.subtitle}</p> : null}
        </div>
      ))}
    </div>
  );
}

function renderValue(metric) {
  if (metric.type === 'percent') return formatPercent(metric.value);
  if (metric.type === 'number') return formatNumber(metric.value);
  return formatMetric(metric.value);
}
