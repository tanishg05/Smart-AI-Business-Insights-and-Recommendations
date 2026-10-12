import { useMemo, useState } from 'react';
import { Bar, BarChart, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Scatter, Tooltip, XAxis, YAxis, ZAxis } from 'recharts';
import SectionCard from '../components/SectionCard';
import ChartTooltip from '../components/ChartTooltip';
import { COLORS, SERIES, axisProps, gridProps } from '../utils/chartTheme';
import { formatCompact, formatCurrency, formatNumber, formatPercent } from '../utils/formatters';

function Legend({ items }) {
  return (
    <div className="legend">
      {items.map((i) => (
        <span key={i.label} className="legend__item">
          <span className="legend__swatch" style={{ background: i.color }} />
          {i.label}
        </span>
      ))}
    </div>
  );
}

function EfficiencyMatrix({ cells, metric }) {
  const regions = [...new Set(cells.map((c) => c.region))];
  const channels = [...new Set(cells.map((c) => c.channel))];
  const lookup = Object.fromEntries(cells.map((c) => [`${c.region}|${c.channel}`, c]));
  const values = cells.map((c) => c[metric.key]);
  const min = Math.min(...values);
  const max = Math.max(...values);
  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Region</th>
            {channels.map((c) => (
              <th key={c} className="r">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {regions.map((r) => (
            <tr key={r}>
              <td>{r}</td>
              {channels.map((ch) => {
                const cell = lookup[`${r}|${ch}`];
                if (!cell) return <td key={ch} className="r muted">—</td>;
                const t = max > min ? (cell[metric.key] - min) / (max - min) : 0.5;
                return (
                  <td key={ch} className="r num" style={{ background: `rgba(56,189,248,${0.03 + t * 0.2})` }}>
                    {metric.fmt(cell[metric.key])}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const METRICS = [
  { key: 'rev_per_unit', label: 'Revenue / unit', fmt: (v) => formatCurrency(v) },
  { key: 'sell_through', label: 'Sell-through', fmt: (v) => formatPercent(v) },
  { key: 'on_time', label: 'On-time', fmt: (v) => formatPercent(v) },
  { key: 'lead', label: 'Lead time', fmt: (v) => `${v.toFixed(2)}d` },
];

export default function SalesPage({ data }) {
  const cr = data.channel_region;
  const el = data.elasticity;
  const [metric, setMetric] = useState(METRICS[0]);
  const channelColors = Object.fromEntries(cr.channels.map((c, i) => [c, SERIES[i % SERIES.length]]));

  const byCategory = useMemo(() => {
    const groups = {};
    (el.points || []).forEach((p) => {
      (groups[p.category] ||= []).push(p);
    });
    return groups;
  }, [el.points]);
  const categories = Object.keys(byCategory);

  return (
    <div className="view">
      <div className="grid grid--main">
        <SectionCard
          title="Revenue by region and channel"
          subtitle="Stacked composition, sorted by total revenue"
          tools={<Legend items={cr.channels.map((c) => ({ label: c, color: channelColors[c] }))} />}
          inspect={{ data: cr.stacked, query: 'Compare channel mix across regions. Which channel under-performs where, and how should we reallocate inventory or promotion spend?' }}
        >
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={cr.stacked} margin={{ top: 8, right: 4, left: 0, bottom: 0 }} barCategoryGap="28%">
              <CartesianGrid {...gridProps} />
              <XAxis dataKey="region" {...axisProps} />
              <YAxis {...axisProps} tickFormatter={(v) => formatCurrency(v, { compact: true, digits: 0 })} width={56} />
              <Tooltip
                cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                content={
                  <ChartTooltip
                    rows={[
                      ...cr.channels.map((c) => ({ key: c, label: c, color: channelColors[c], format: (v) => formatCurrency(v) })),
                      { key: 'total', label: 'Total', format: (v) => formatCurrency(v) },
                    ]}
                  />
                }
              />
              {cr.channels.map((c, i) => (
                <Bar key={c} dataKey={c} stackId="rev" fill={channelColors[c]} radius={i === cr.channels.length - 1 ? [3, 3, 0, 0] : 0} maxBarSize={64} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </SectionCard>

        <SectionCard
          title="Channel efficiency matrix"
          subtitle="Region × channel, shaded by the selected measure"
          bodyClassName="card__body--flush"
          tools={
            <div className="filter" style={{ height: 24 }}>
              <select value={metric.key} onChange={(e) => setMetric(METRICS.find((m) => m.key === e.target.value))} aria-label="Measure">
                {METRICS.map((m) => (
                  <option key={m.key} value={m.key}>
                    {m.label}
                  </option>
                ))}
              </select>
            </div>
          }
          inspect={{ data: cr.cells, query: `Where is ${metric.label.toLowerCase()} weakest across regions and channels, and what is driving the gap?` }}
        >
          <EfficiencyMatrix cells={cr.cells} metric={metric} />
        </SectionCard>
      </div>

      <div className="grid grid--main">
        <SectionCard
          title="Price elasticity"
          subtitle={
            el.coefficient !== null && el.coefficient !== undefined
              ? `Price per unit vs units sold · log-log slope ${el.coefficient.toFixed(3)}, r² ${el.r2.toFixed(3)}`
              : 'Price per unit vs units sold'
          }
          tools={<Legend items={categories.map((c, i) => ({ label: c, color: SERIES[i % SERIES.length] }))} />}
          inspect={{ data: el.points, query: 'What does this price-vs-volume relationship say about pricing headroom by category?' }}
        >
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid {...gridProps} vertical />
              <XAxis type="number" dataKey="price" {...axisProps} domain={[(min) => Math.floor(min * 0.95 * 10) / 10, (max) => Math.ceil(max * 1.03 * 10) / 10]} tickFormatter={(v) => `$${v.toFixed(2)}`} allowDuplicatedCategory={false} />
              <YAxis type="number" dataKey="units" {...axisProps} domain={[(min) => Math.max(0, Math.floor(min * 0.9)), (max) => Math.ceil(max * 1.05)]} tickFormatter={(v) => formatCompact(v, 0)} width={44} />
              <ZAxis type="number" dataKey="n" range={[24, 140]} />
              <Tooltip
                cursor={{ strokeDasharray: '2 3', stroke: 'rgba(255,255,255,0.2)' }}
                content={
                  <ChartTooltip
                    labelFormatter={(_, d) => d.category || 'Fitted curve'}
                    rows={[
                      { key: 'price', label: 'Price', format: (v) => formatCurrency(v) },
                      { key: 'units', label: 'Avg units', format: (v) => formatNumber(v, 1) },
                      { key: 'n', label: 'Orders', format: (v) => formatNumber(v) },
                    ]}
                  />
                }
              />
              {categories.map((c, i) => (
                <Scatter key={c} name={c} data={byCategory[c]} fill={SERIES[i % SERIES.length]} fillOpacity={0.75} />
              ))}
              {el.trendline?.length > 0 && (
                <Line data={el.trendline} dataKey="units" stroke={COLORS.text} strokeOpacity={0.55} strokeWidth={1.25} strokeDasharray="5 4" dot={false} activeDot={false} legendType="none" isAnimationActive={false} />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        </SectionCard>

        <SectionCard title="Category performance" subtitle="Revenue and average price" inspect={{ data: data.category_sales }}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.category_sales} layout="vertical" margin={{ top: 4, right: 12, left: 4, bottom: 0 }}>
              <CartesianGrid {...gridProps} horizontal={false} vertical />
              <XAxis type="number" {...axisProps} tickFormatter={(v) => formatCurrency(v, { compact: true, digits: 0 })} />
              <YAxis type="category" dataKey="category" {...axisProps} width={84} />
              <Tooltip
                cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                content={
                  <ChartTooltip
                    rows={[
                      { key: 'revenue', label: 'Revenue', color: COLORS.ice, format: (v) => formatCurrency(v) },
                      { key: 'units_sold', label: 'Units', format: (v) => formatNumber(v) },
                      { key: 'avg_price', label: 'Avg price', format: (v) => formatCurrency(v) },
                      { key: 'share', label: 'Unit share', format: (v) => formatPercent(v) },
                    ]}
                  />
                }
              />
              <Bar dataKey="revenue" fill={COLORS.ice} radius={[0, 3, 3, 0]} maxBarSize={18} />
            </BarChart>
          </ResponsiveContainer>
        </SectionCard>
      </div>
    </div>
  );
}
