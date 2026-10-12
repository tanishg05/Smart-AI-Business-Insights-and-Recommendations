import { Area, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { RotateCw } from 'lucide-react';
import KPIGrid from '../components/KPIGrid';
import SectionCard from '../components/SectionCard';
import InsightPills from '../components/InsightPills';
import RecommendationCard from '../components/RecommendationCard';
import ChartTooltip from '../components/ChartTooltip';
import { COLORS, axisProps, gridProps } from '../utils/chartTheme';
import { formatCompact, formatCurrency, formatDate, formatNumber } from '../utils/formatters';
import useMountAnimation from '../hooks/useMountAnimation';

export function DeficitTable({ deficits = [] }) {
  if (!deficits.length) return <p className="muted" style={{ padding: 16 }}>No segments to rank.</p>;
  const maxNeed = Math.max(...deficits.map((d) => d.need_days), 1);
  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Segment</th>
            <th className="r">Stock</th>
            <th className="r">Units / day</th>
            <th className="r">Cover vs need</th>
            <th className="r">Reorder pt</th>
            <th className="r">At risk</th>
          </tr>
        </thead>
        <tbody>
          {deficits.map((d) => {
            const ratio = d.cover_days / d.need_days;
            const color = ratio < 0.5 ? COLORS.coral : ratio < 1 ? COLORS.amber : COLORS.emerald;
            return (
              <tr key={d.segment}>
                <td>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                    <span className="dot" style={{ background: color }} />
                    {d.segment}
                  </span>
                </td>
                <td className="r num">{formatNumber(d.stock)}</td>
                <td className="r num">{formatNumber(d.velocity, 1)}</td>
                <td className="r num">
                  <div className="bar-cell">
                    {d.cover_days.toFixed(1)} / {d.need_days.toFixed(1)}d
                    <div className="bar-cell__track">
                      <div className="bar-cell__fill" style={{ width: `${Math.min(100, (d.cover_days / maxNeed) * 100)}%`, background: color }} />
                    </div>
                  </div>
                </td>
                <td className="r num">{formatNumber(d.reorder_point)}</td>
                <td className="r num">{formatCurrency(d.revenue_at_risk, { compact: true })}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default function DashboardPage({ data, insights }) {
  const animate = useMountAnimation();
  const trend = data.trend || [];
  const g = data.granularity;

  return (
    <div className="view">
      <KPIGrid kpis={data.kpis} />

      <div className="grid grid--main">
        <SectionCard
          title="Revenue trajectory"
          subtitle={`Units sold per ${g} against a 7-${g} moving-average baseline`}
          inspect={{ data: trend.map(({ period, units, ma, revenue }) => ({ period, units, ma, revenue })), query: 'Explain the trajectory of units sold versus the moving-average baseline. Where did it break out or under-perform, and why?' }}
          footer={
            <>
              <span>Total units <strong>{formatCompact(data.summary.total_sales)}</strong></span>
              <span>Revenue <strong>{formatCurrency(data.summary.total_revenue, { compact: true })}</strong></span>
              <span>Avg price <strong>{formatCurrency(data.summary.avg_price)}</strong></span>
            </>
          }
        >
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={trend} margin={{ top: 8, right: 4, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="unitsFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={COLORS.ice} stopOpacity={0.24} />
                  <stop offset="100%" stopColor={COLORS.ice} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid {...gridProps} />
              <XAxis dataKey="period" {...axisProps} tickFormatter={(v) => formatDate(v, g)} minTickGap={36} />
              <YAxis yAxisId="u" {...axisProps} tickFormatter={(v) => formatCompact(v, 0)} width={48} />
              <YAxis yAxisId="r" orientation="right" {...axisProps} tickFormatter={(v) => formatCurrency(v, { compact: true, digits: 0 })} width={52} />
              <Tooltip
                content={
                  <ChartTooltip
                    granularity={g}
                    rows={[
                      { key: 'units', label: 'Units sold', color: COLORS.ice },
                      { key: 'ma', label: 'MA baseline', color: COLORS.slate, format: (v) => formatNumber(v, 0) },
                      { key: 'revenue', label: 'Revenue', color: '#D9C8A6', format: (v) => formatCurrency(v) },
                    ]}
                  />
                }
              />
              <Legend verticalAlign="top" align="right" height={24} iconType="plainline" iconSize={12} wrapperStyle={{ fontSize: 11, color: 'var(--text-secondary)' }} />
              <Area isAnimationActive={animate} yAxisId="u" type="monotone" dataKey="units" name="Units sold" stroke={COLORS.ice} strokeWidth={1.75} fill="url(#unitsFill)" activeDot={{ r: 3, strokeWidth: 0 }} />
              <Line isAnimationActive={animate} yAxisId="u" type="monotone" dataKey="ma" name="MA baseline" stroke={COLORS.slate} strokeWidth={1.25} strokeDasharray="4 3" dot={false} />
              <Line isAnimationActive={animate} yAxisId="r" type="monotone" dataKey="revenue" name="Revenue" stroke="#D9C8A6" strokeWidth={1} strokeOpacity={0.7} dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </SectionCard>

        <SectionCard
          title="Proactive signals"
          subtitle={insights.source === 'groq' ? `Scanned and summarised by Groq · ${insights.model}` : insights.fallback_reason ? `Local engine (Groq failed: ${insights.fallback_reason})` : 'Scanned by the local analytics engine'}
          tools={
            <button className="btn btn--ghost btn--icon btn--sm" onClick={insights.reload} title="Rescan" aria-label="Rescan insights">
              <RotateCw size={12} style={insights.loading ? { animation: 'spin .8s linear infinite' } : undefined} />
            </button>
          }
        >
          {insights.error ? <p className="muted">{insights.error}</p> : <InsightPills insights={insights.insights} loading={insights.loading} limit={4} />}
        </SectionCard>
      </div>

      <div className="grid grid--main">
        <SectionCard
          title="Top stock deficits"
          subtitle={`Tightest ${data.velocity_matrix?.unit || 'segments'} by days of cover vs lead time + 7-day review`}
          bodyClassName="card__body--flush"
          inspect={{ data: data.deficits, query: 'Which of these deficit segments should we replenish first, how many units, and what is the financial exposure?' }}
        >
          <DeficitTable deficits={data.deficits} />
        </SectionCard>

        <SectionCard title="Recommended actions" subtitle="Rule-based priorities from current thresholds">
          <div style={{ display: 'grid', gap: 10 }}>
            {data.recommendations.slice(0, 3).map((r) => (
              <RecommendationCard key={r.title} {...r} />
            ))}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
