import { useState } from 'react';
import { Bar, BarChart, CartesianGrid, Cell, ComposedChart, Line, ReferenceArea, ReferenceLine, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from 'recharts';
import SectionCard from '../components/SectionCard';
import ChartTooltip from '../components/ChartTooltip';
import { DeficitTable } from './DashboardPage';
import { COLORS, QUADRANT_COLOR, axisProps, gridProps } from '../utils/chartTheme';
import { formatNumber, formatPercent } from '../utils/formatters';

const QUADRANTS = ['Critical Low', 'Fast Mover', 'Overstocked', 'Dead Stock'];
const QUADRANT_HINT = {
  'Critical Low': 'Fast velocity, thin stock',
  'Fast Mover': 'Fast velocity, healthy stock',
  Overstocked: 'Slow velocity, heavy stock',
  'Dead Stock': 'Slow velocity, thin stock',
};

export default function OperationsPage({ data }) {
  const lt = data.lead_time;
  const vm = data.velocity_matrix;
  const [hidden, setHidden] = useState({});
  const points = vm.points.filter((p) => !hidden[p.quadrant]);
  const xs = vm.points.map((p) => p.velocity);
  const ys = vm.points.map((p) => p.stock);
  const xMax = Math.max(...xs, vm.x_split) * 1.08;
  const yMax = Math.max(...ys, vm.y_split) * 1.08;

  return (
    <div className="view">
      <div className="grid grid--main">
        <SectionCard
          title="Lead-time distribution"
          subtitle="Orders by delivery days with fitted normal curve"
          inspect={{ data: lt.histogram, query: 'Where are the logistics bottlenecks in this lead-time distribution, and what SLA should we set?' }}
          footer={
            <>
              <span>Mean <strong>{lt.mean.toFixed(2)}d</strong></span>
              <span>σ <strong>{lt.std.toFixed(2)}</strong></span>
              <span>p95 <strong>{lt.p95.toFixed(1)}d</strong></span>
              <span>Beyond 2σ <strong>{formatNumber(lt.anomaly_count)}</strong></span>
              <span>Late vs {lt.sla_days}d SLA <strong>{formatPercent(lt.late_share)}</strong></span>
            </>
          }
        >
          <ResponsiveContainer width="100%" height={280}>
            <ComposedChart data={lt.histogram} margin={{ top: 16, right: 8, left: -6, bottom: 0 }}>
              <CartesianGrid {...gridProps} />
              <XAxis dataKey="days" type="number" domain={['dataMin - 0.5', 'dataMax + 0.5']} ticks={lt.histogram.map((h) => h.days)} {...axisProps} tickFormatter={(v) => `${v}d`} />
              <YAxis {...axisProps} tickFormatter={(v) => formatNumber(v)} width={52} />
              <Tooltip
                cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                content={
                  <ChartTooltip
                    labelFormatter={(l) => `${l} delivery days`}
                    rows={[
                      { key: 'count', label: 'Orders', color: COLORS.ice, format: (v) => formatNumber(v) },
                      { key: 'normal', label: 'Normal fit', color: COLORS.slate, format: (v) => formatNumber(v) },
                    ]}
                  />
                }
              />
              <Bar dataKey="count" barSize={36} radius={[3, 3, 0, 0]}>
                {lt.histogram.map((h) => (
                  <Cell key={h.days} fill={h.anomaly ? COLORS.coral : h.days > lt.sla_days ? COLORS.amber : COLORS.ice} fillOpacity={0.85} />
                ))}
              </Bar>
              <Line type="monotone" dataKey="normal" stroke={COLORS.slate} strokeWidth={1.25} strokeDasharray="4 3" dot={false} />
              <ReferenceLine x={lt.mean} stroke={COLORS.text} strokeOpacity={0.5} strokeDasharray="2 3" label={{ value: 'μ', fill: COLORS.text, fontSize: 11, position: 'top' }} />
              <ReferenceLine x={lt.sla_days + 0.5} stroke={COLORS.amber} strokeOpacity={0.6} label={{ value: 'SLA', fill: COLORS.amber, fontSize: 10, position: 'top' }} />
            </ComposedChart>
          </ResponsiveContainer>
        </SectionCard>

        <SectionCard title="Lead time by region" subtitle="Mean delivery days, σ shown in tooltip" inspect={{ data: lt.by_region }}>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={lt.by_region} layout="vertical" margin={{ top: 4, right: 16, left: 4, bottom: 0 }}>
              <CartesianGrid {...gridProps} horizontal={false} vertical />
              <XAxis type="number" {...axisProps} domain={[0, 'auto']} tickFormatter={(v) => `${v}d`} />
              <YAxis type="category" dataKey="region" {...axisProps} width={84} />
              <Tooltip
                cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                content={
                  <ChartTooltip
                    rows={[
                      { key: 'mean', label: 'Mean', color: COLORS.ice, format: (v) => `${v.toFixed(2)}d` },
                      { key: 'std', label: 'σ', format: (v) => v.toFixed(2) },
                      { key: 'count', label: 'Orders', format: (v) => formatNumber(v) },
                    ]}
                  />
                }
              />
              <ReferenceLine x={lt.sla_days} stroke={COLORS.amber} strokeDasharray="3 3" />
              <Bar dataKey="mean" radius={[0, 3, 3, 0]} maxBarSize={18}>
                {lt.by_region.map((r) => (
                  <Cell key={r.region} fill={r.mean > lt.sla_days ? COLORS.amber : COLORS.ice} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </SectionCard>
      </div>

      <SectionCard
        title="Stock vs velocity matrix"
        subtitle={`Each point is a ${vm.unit}. X = 7-day demand velocity, Y = stock available; split at medians.`}
        inspect={{ data: vm.points.map(({ segment, velocity, stock, cover_days, quadrant }) => ({ segment, velocity, stock, cover_days, quadrant })), query: 'Read this safety-stock quadrant: which Critical Low items need replenishment, and which Overstocked items can fund them?' }}
        className="span-2"
      >
        <ResponsiveContainer width="100%" height={360}>
          <ScatterChart margin={{ top: 8, right: 12, left: -4, bottom: 4 }}>
            <CartesianGrid {...gridProps} vertical />
            <ReferenceArea x1={vm.x_split} x2={xMax} y1={0} y2={vm.y_split} fill={COLORS.coral} fillOpacity={0.04} />
            <ReferenceArea x1={0} x2={vm.x_split} y1={vm.y_split} y2={yMax} fill={COLORS.amber} fillOpacity={0.03} />
            <XAxis type="number" dataKey="velocity" name="Velocity" domain={[0, xMax]} {...axisProps} tickFormatter={(v) => formatNumber(v, v < 10 ? 1 : 0)} label={{ value: 'units / day', position: 'insideBottomRight', offset: -2, fill: COLORS.axis, fontSize: 10 }} />
            <YAxis type="number" dataKey="stock" name="Stock" domain={[0, yMax]} {...axisProps} tickFormatter={(v) => formatNumber(v)} width={52} />
            <ReferenceLine x={vm.x_split} stroke="rgba(255,255,255,0.18)" strokeDasharray="3 3" />
            <ReferenceLine y={vm.y_split} stroke="rgba(255,255,255,0.18)" strokeDasharray="3 3" />
            <Tooltip
              cursor={{ strokeDasharray: '2 3', stroke: 'rgba(255,255,255,0.2)' }}
              content={
                <ChartTooltip
                  labelFormatter={(_, d) => d.segment}
                  rows={[
                    { key: 'quadrant', label: 'Quadrant', format: (v) => v },
                    { key: 'velocity', label: 'Units / day', format: (v) => formatNumber(v, 1) },
                    { key: 'stock', label: 'Stock', format: (v) => formatNumber(v) },
                    { key: 'cover_days', label: 'Cover', format: (v) => `${v.toFixed(1)}d` },
                    { key: 'reorder_point', label: 'Reorder point', format: (v) => formatNumber(v) },
                  ]}
                />
              }
            />
            <Scatter data={points} isAnimationActive animationDuration={500}>
              {points.map((p) => (
                <Cell key={p.segment} fill={QUADRANT_COLOR[p.quadrant]} fillOpacity={p.at_risk ? 0.95 : 0.6} stroke={p.at_risk ? COLORS.text : 'none'} strokeWidth={p.at_risk ? 1 : 0} />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
        <div className="quad-legend">
          {QUADRANTS.map((q) => (
            <button key={q} className={`quad-chip ${hidden[q] ? 'is-off' : ''}`} onClick={() => setHidden((h) => ({ ...h, [q]: !h[q] }))} aria-pressed={!hidden[q]}>
              <span className="quad-chip__name">
                <span className="legend__swatch" style={{ background: QUADRANT_COLOR[q] }} />
                {q}
              </span>
              <div className="quad-chip__count">{vm.counts[q] || 0}</div>
              <span className="muted" style={{ fontSize: 11 }}>{QUADRANT_HINT[q]}</span>
            </button>
          ))}
        </div>
      </SectionCard>

      <div style={{ height: 14 }} />
      <SectionCard title="Replenishment queue" subtitle="Lowest cover relative to lead time + review period" bodyClassName="card__body--flush" inspect={{ data: data.deficits }}>
        <DeficitTable deficits={data.deficits} />
      </SectionCard>
    </div>
  );
}
