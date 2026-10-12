import { Area, AreaChart, ResponsiveContainer, YAxis } from 'recharts';
import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react';
import useCountUp from '../hooks/useCountUp';
import { STATUS_COLOR } from '../utils/chartTheme';
import { formatDelta, formatKpi } from '../utils/formatters';

const STATUS_LABEL = { healthy: 'Healthy', warning: 'Watch', critical: 'Critical' };

function Sparkline({ values, color, id }) {
  if (!values || values.length < 2) return <div className="kpi__spark" />;
  const data = values.map((v, i) => ({ i, v }));
  return (
    <div className="kpi__spark">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 2, right: 0, bottom: 2, left: 0 }}>
          <defs>
            <linearGradient id={`spark-${id}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.28} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <YAxis hide domain={['dataMin', 'dataMax']} />
          <Area type="monotone" dataKey="v" stroke={color} strokeWidth={1.5} fill={`url(#spark-${id})`} isAnimationActive animationDuration={700} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function KpiCard({ kpi, index }) {
  const animated = useCountUp(kpi.value);
  const { value, unit } = formatKpi(kpi.format, animated);
  const delta = kpi.delta;
  const good = delta === null || delta === undefined ? null : kpi.higher_is_better ? delta >= 0 : delta <= 0;
  const direction = delta === null || delta === undefined || Math.abs(delta) < 0.0005 ? 'flat' : delta > 0 ? 'up' : 'down';
  const tone = direction === 'flat' ? 'flat' : good ? 'up' : 'down';
  const Icon = direction === 'up' ? ArrowUpRight : direction === 'down' ? ArrowDownRight : Minus;
  const sparkColor = STATUS_COLOR[kpi.status] || STATUS_COLOR.info;

  return (
    <article className={`card card--lift kpi kpi--${kpi.status}`} style={{ animation: `slideIn 420ms ${index * 45}ms var(--ease-spring) both` }}>
      <div className="kpi__top">
        <span className="kpi__label" title={kpi.hint}>
          {kpi.label}
        </span>
        <span className={`badge badge--${kpi.status}`}>{STATUS_LABEL[kpi.status] || kpi.status}</span>
      </div>
      <div className="kpi__row">
        <div>
          <div className="kpi__value">
            {value}
            {unit && <span className="kpi__unit">{unit}</span>}
          </div>
          <div className="kpi__meta">
            <span className={`delta delta--${tone}`} style={{ display: 'inline-flex', alignItems: 'center', gap: 2 }}>
              <Icon size={12} />
              {formatDelta(delta)}
            </span>
            <span>{kpi.delta_label}</span>
          </div>
        </div>
        <Sparkline values={kpi.sparkline} color={sparkColor} id={kpi.key} />
      </div>
      <p className="kpi__hint">{kpi.detail || kpi.hint}</p>
    </article>
  );
}

export default function KPIGrid({ kpis = [] }) {
  return (
    <div className="grid grid--kpi">
      {kpis.map((kpi, i) => (
        <KpiCard key={kpi.key} kpi={kpi} index={i} />
      ))}
    </div>
  );
}
