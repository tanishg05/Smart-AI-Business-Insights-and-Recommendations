import { Area, Bar, BarChart, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import SectionCard from '../components/SectionCard';
import ChartTooltip from '../components/ChartTooltip';
import Heatmap from '../components/Heatmap';
import { useCopilot } from '../context/CopilotContext';
import { COLORS, axisProps, gridProps } from '../utils/chartTheme';
import { formatCompact, formatCurrency, formatDate, formatNumber, formatPercent } from '../utils/formatters';
import useMountAnimation from '../hooks/useMountAnimation';

const SEASON_ORDER = ['Winter', 'Summer', 'Monsoon', 'Autumn'];
const bySeason = (entries) =>
  entries.sort(([a], [b]) => (SEASON_ORDER.indexOf(a) + 1 || 99) - (SEASON_ORDER.indexOf(b) + 1 || 99)).map(([season, days]) => ({ season, days }));

export default function SeasonalPage({ data }) {
  const animate = useMountAnimation();
  const seasonLead = bySeason(Object.entries(data.lead_time.by_season));
  const { ask } = useCopilot();
  const fc = data.forecast_series;
  const g = data.granularity;
  const history = (fc.history || []).map((h) => ({ period: h.period, actual: h.units }));
  const last = history[history.length - 1];
  const forecast = (fc.forecast || []).map((f) => ({ period: f.period, forecast: f.forecast, band: [f.lower, f.upper], lower: f.lower, upper: f.upper }));
  // Bridge the forecast to the last actual so the line is continuous.
  const series = [...history.slice(0, -1), last ? { ...last, forecast: last.actual, band: [last.actual, last.actual] } : null, ...forecast].filter(Boolean);

  return (
    <div className="view">
      <div className="grid grid--main-r">
        <SectionCard
          title="Season × region demand"
          subtitle="Seasonality index: daily units relative to each region's average"
          inspect={{ data: data.heatmap.cells, query: 'Where are the seasonal demand spikes by region, and how far ahead should we pre-build inventory for each?' }}
        >
          <Heatmap heatmap={data.heatmap} onSelect={(cell) => ask(`Explain demand in ${cell.region} during ${cell.season} (index ${cell.index.toFixed(2)}). Should we change stock positioning?`, { title: `Heatmap ${cell.season} × ${cell.region}`, data: [cell] })} />
        </SectionCard>

        <SectionCard
          title={`7-${g} rolling demand forecast`}
          subtitle={`${fc.method || 'Forecast'} with 95% confidence band${fc.mape !== undefined ? ` · in-sample MAPE ${formatPercent(fc.mape)}` : ''}`}
          inspect={{ data: [...history.slice(-12), ...fc.forecast], query: 'Interpret this demand forecast and its confidence band. What inventory should we commit for the next periods?' }}
        >
          {forecast.length === 0 ? (
            <p className="muted">Not enough history to forecast.</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={series} margin={{ top: 8, right: 4, left: 0, bottom: 0 }}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="period" {...axisProps} tickFormatter={(v) => formatDate(v, g)} minTickGap={32} />
                <YAxis {...axisProps} tickFormatter={(v) => formatCompact(v, 0)} width={48} domain={['auto', 'auto']} />
                <Tooltip
                  content={
                    <ChartTooltip
                      granularity={g}
                      rows={[
                        { key: 'actual', label: 'Actual', color: COLORS.ice, format: (v) => formatNumber(v) },
                        { key: 'forecast', label: 'Forecast', color: COLORS.emerald, format: (v) => formatNumber(v) },
                        { key: 'lower', label: '95% low', format: (v) => formatNumber(v) },
                        { key: 'upper', label: '95% high', format: (v) => formatNumber(v) },
                      ]}
                    />
                  }
                />
                <Area type="monotone" dataKey="band" stroke="none" fill={COLORS.emerald} fillOpacity={0.12} isAnimationActive={false} />
                <Line isAnimationActive={animate} type="monotone" dataKey="actual" stroke={COLORS.ice} strokeWidth={1.75} dot={false} />
                <Line isAnimationActive={animate} type="monotone" dataKey="forecast" stroke={COLORS.emerald} strokeWidth={1.75} strokeDasharray="5 3" dot={{ r: 2, strokeWidth: 0, fill: COLORS.emerald }} />
              </ComposedChart>
            </ResponsiveContainer>
          )}
        </SectionCard>
      </div>

      <div className="grid grid--2">
        <SectionCard title="Seasonal volume" subtitle="Units and revenue by season" inspect={{ data: data.seasonal_sales }}>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={data.seasonal_sales} margin={{ top: 8, right: 4, left: 0, bottom: 0 }}>
              <CartesianGrid {...gridProps} />
              <XAxis dataKey="season" {...axisProps} />
              <YAxis {...axisProps} tickFormatter={(v) => formatCompact(v, 0)} width={48} />
              <Tooltip
                cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                content={
                  <ChartTooltip
                    rows={[
                      { key: 'units_sold', label: 'Units', color: COLORS.ice, format: (v) => formatNumber(v) },
                      { key: 'revenue', label: 'Revenue', format: (v) => formatCurrency(v) },
                    ]}
                  />
                }
              />
              <Bar isAnimationActive={animate} dataKey="units_sold" fill={COLORS.ice} radius={[3, 3, 0, 0]} maxBarSize={48} />
            </BarChart>
          </ResponsiveContainer>
        </SectionCard>

        <SectionCard title="Seasonal lead time" subtitle="Mean delivery days by season" inspect={{ data: seasonLead }}>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={seasonLead} margin={{ top: 8, right: 4, left: 0, bottom: 0 }}>
              <CartesianGrid {...gridProps} />
              <XAxis dataKey="season" {...axisProps} />
              <YAxis {...axisProps} domain={[0, 'auto']} tickFormatter={(v) => `${v.toFixed(1)}d`} width={44} />
              <Tooltip cursor={{ fill: 'rgba(255,255,255,0.03)' }} content={<ChartTooltip rows={[{ key: 'days', label: 'Mean lead', color: COLORS.amber, format: (v) => `${v.toFixed(2)}d` }]} />} />
              <Bar isAnimationActive={animate} dataKey="days" fill={COLORS.amber} fillOpacity={0.85} radius={[3, 3, 0, 0]} maxBarSize={48} />
            </BarChart>
          </ResponsiveContainer>
        </SectionCard>
      </div>
    </div>
  );
}
