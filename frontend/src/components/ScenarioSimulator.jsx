import { useEffect, useMemo, useRef, useState } from 'react';
import { Area, Bar, BarChart, CartesianGrid, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Loader2, RotateCcw, Sparkles } from 'lucide-react';
import { errorMessage, simulateScenario } from '../services/api';
import { COLORS, axisProps, gridProps } from '../utils/chartTheme';
import { formatCurrency, formatPercent } from '../utils/formatters';
import useCountUp from '../hooks/useCountUp';
import ChartTooltip from './ChartTooltip';
import Markdown from './Markdown';
import SectionCard from './SectionCard';
import useMountAnimation from '../hooks/useMountAnimation';

const DEFAULTS = { delay_days: 0, demand_shift_pct: 0, safety_stock_multiplier: 1, price_change_pct: 0 };

const SLIDERS = [
  { key: 'delay_days', label: 'Supplier delivery delay', min: 0, max: 15, step: 1, fmt: (v) => `+${v}d` },
  { key: 'demand_shift_pct', label: 'Seasonal demand surge', min: -30, max: 50, step: 1, fmt: (v) => `${v > 0 ? '+' : ''}${v}%` },
  { key: 'safety_stock_multiplier', label: 'Safety stock buffer', min: 0.8, max: 2, step: 0.05, fmt: (v) => `${Number(v).toFixed(2)}×` },
  { key: 'price_change_pct', label: 'List price change', min: -20, max: 20, step: 1, fmt: (v) => `${v > 0 ? '+' : ''}${v}%` },
];

const PRESETS = [
  { label: 'Monsoon disruption', params: { delay_days: 6, demand_shift_pct: 15, safety_stock_multiplier: 1, price_change_pct: 0 } },
  { label: 'Festive surge', params: { delay_days: 2, demand_shift_pct: 40, safety_stock_multiplier: 1.2, price_change_pct: 0 } },
  { label: 'Lean inventory', params: { delay_days: 0, demand_shift_pct: 0, safety_stock_multiplier: 0.8, price_change_pct: 0 } },
  { label: 'Price hike', params: { delay_days: 0, demand_shift_pct: 0, safety_stock_multiplier: 1, price_change_pct: 10 } },
];

function Stat({ label, value, base, format, invert }) {
  const animated = useCountUp(value, 500);
  const diff = value - base;
  const worse = invert ? diff < 0 : diff > 0;
  const tone = Math.abs(diff) < 1e-6 ? 'var(--text-primary)' : worse ? 'var(--status-critical)' : 'var(--status-healthy)';
  return (
    <div className="sim-stat">
      <span className="sim-stat__label">{label}</span>
      <span className="sim-stat__value" style={{ color: tone }}>
        {format(animated)}
      </span>
      <span className="sim-stat__base">baseline {format(base)}</span>
    </div>
  );
}

export default function ScenarioSimulator({ filters }) {
  const animate = useMountAnimation();
  const [params, setParams] = useState(DEFAULTS);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [briefing, setBriefing] = useState(null);
  const [briefingLoading, setBriefingLoading] = useState(false);
  const controller = useRef(null);

  useEffect(() => {
    const timer = setTimeout(async () => {
      controller.current?.abort();
      const c = new AbortController();
      controller.current = c;
      setLoading(true);
      try {
        const response = await simulateScenario(params, filters, false, c.signal);
        setResult(response.data);
        setError('');
      } catch (err) {
        if (err.name !== 'CanceledError') setError(errorMessage(err, 'Simulation failed.'));
      } finally {
        if (controller.current === c) setLoading(false);
      }
    }, 180);
    return () => clearTimeout(timer);
  }, [params, filters]);

  useEffect(() => setBriefing(null), [params, filters]);

  const generateBriefing = async () => {
    setBriefingLoading(true);
    try {
      const response = await simulateScenario(params, filters, true);
      setBriefing({ text: response.data.narrative, source: response.data.source, model: response.data.model });
    } catch (err) {
      setBriefing({ text: `**Briefing failed.** ${errorMessage(err)}`, source: 'error' });
    } finally {
      setBriefingLoading(false);
    }
  };

  const regions = useMemo(
    () => (result?.regions || []).map((r) => ({ ...r, baseline: r.baseline_lost_revenue, scenario: r.lost_revenue })),
    [result]
  );

  const b = result?.baseline;
  const s = result?.scenario;

  return (
    <div className="sim">
      <section className="card sim__controls">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h3 className="card__title">Levers</h3>
            <p className="card__subtitle">{result?.horizon_days || 30}-day horizon · recalculates live</p>
          </div>
          {loading && <Loader2 size={14} style={{ animation: 'spin 0.8s linear infinite', color: 'var(--text-muted)' }} />}
        </div>

        {SLIDERS.map((sl) => {
          const v = params[sl.key];
          const fill = ((v - sl.min) / (sl.max - sl.min)) * 100;
          return (
            <div className="slider" key={sl.key}>
              <div className="slider__head">
                <label className="slider__label" htmlFor={sl.key}>
                  {sl.label}
                </label>
                <span className="slider__value">{sl.fmt(v)}</span>
              </div>
              <input
                id={sl.key}
                type="range"
                min={sl.min}
                max={sl.max}
                step={sl.step}
                value={v}
                style={{ '--fill': `${fill}%` }}
                onChange={(e) => setParams((p) => ({ ...p, [sl.key]: Number(e.target.value) }))}
              />
              <div className="slider__scale">
                <span>{sl.fmt(sl.min)}</span>
                <span>{sl.fmt(sl.max)}</span>
              </div>
            </div>
          );
        })}

        <div style={{ display: 'grid', gap: 8 }}>
          <span className="eyebrow">Presets</span>
          <div className="presets">
            {PRESETS.map((p) => (
              <button key={p.label} className="chip" onClick={() => setParams(p.params)}>
                {p.label}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', gap: 8, marginTop: 'auto' }}>
          <button className="btn" onClick={() => setParams(DEFAULTS)}>
            <RotateCcw size={13} />
            Reset
          </button>
          <button className="btn btn--primary" style={{ flex: 1 }} onClick={generateBriefing} disabled={!result || briefingLoading}>
            {briefingLoading ? <Loader2 size={14} style={{ animation: 'spin 0.8s linear infinite' }} /> : <Sparkles size={14} />}
            Generate briefing
          </button>
        </div>
        {result?.params?.price_elasticity_factor !== undefined && (
          <p className="muted" style={{ fontSize: 11 }}>
            Price elasticity {Number(result.params.price_elasticity_factor).toFixed(2)} (fitted, clamped to −3…−0.1).
          </p>
        )}
      </section>

      <div style={{ display: 'grid', gap: 14, minWidth: 0, alignContent: 'start' }}>
        {error && <div className="engine-note">{error}</div>}
        {b && s && (
          <div className="sim-stats">
            <Stat label="Projected lost sales" value={s.lost_revenue} base={b.lost_revenue} format={(v) => formatCurrency(v, { compact: true })} />
            <Stat label="Stockout probability" value={s.stockout_probability} base={b.stockout_probability} format={(v) => formatPercent(v)} />
            <Stat label="Fill rate" value={s.fill_rate} base={b.fill_rate} format={(v) => formatPercent(v)} invert />
            <Stat label="Holding cost" value={s.holding_cost} base={b.holding_cost} format={(v) => formatCurrency(v, { compact: true })} />
          </div>
        )}

        <div className="grid grid--2" style={{ marginBottom: 0 }}>
          <SectionCard
            title="Delay sensitivity"
            subtitle="Lost sales as supplier delay grows, other levers held"
            inspect={result && { data: result.delay_curve, query: 'Interpret this delay sensitivity curve: where does lost revenue accelerate and what buffer would flatten it?' }}
          >
            <ResponsiveContainer width="100%" height={240}>
              <ComposedChart data={result?.delay_curve || []} margin={{ top: 18, right: 8, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="lossFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={COLORS.coral} stopOpacity={0.28} />
                    <stop offset="100%" stopColor={COLORS.coral} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="delay_days" {...axisProps} tickFormatter={(v) => `+${v}d`} />
                <YAxis yAxisId="l" {...axisProps} tickFormatter={(v) => formatCurrency(v, { compact: true, digits: 0 })} width={56} />
                <YAxis yAxisId="r" orientation="right" {...axisProps} tickFormatter={(v) => `${Math.round(v * 100)}%`} width={36} domain={[0, 1]} />
                <Tooltip
                  content={
                    <ChartTooltip
                      labelFormatter={(l) => `+${l} days delay`}
                      rows={[
                        { key: 'lost_revenue', label: 'Lost sales', color: COLORS.coral, format: (v) => formatCurrency(v) },
                        { key: 'stockout_probability', label: 'Stockout prob.', color: COLORS.amber, format: (v) => formatPercent(v) },
                      ]}
                    />
                  }
                />
                <Area isAnimationActive={animate} yAxisId="l" type="monotone" dataKey="lost_revenue" stroke={COLORS.coral} strokeWidth={1.75} fill="url(#lossFill)" />
                <Line isAnimationActive={animate} yAxisId="r" type="monotone" dataKey="stockout_probability" stroke={COLORS.amber} strokeWidth={1.25} strokeDasharray="3 3" dot={false} />
                <ReferenceLine yAxisId="l" x={params.delay_days} stroke={COLORS.ice} strokeDasharray="2 3" label={{ value: 'now', fill: COLORS.ice, fontSize: 10, position: 'top' }} />
              </ComposedChart>
            </ResponsiveContainer>
          </SectionCard>

          <SectionCard title="Lost sales by region" subtitle="Baseline vs scenario" inspect={result && { data: regions }}>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={regions} margin={{ top: 8, right: 8, left: 0, bottom: 0 }} barGap={3}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="region" {...axisProps} />
                <YAxis {...axisProps} tickFormatter={(v) => formatCurrency(v, { compact: true, digits: 0 })} width={56} />
                <Tooltip
                  cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                  content={
                    <ChartTooltip
                      rows={[
                        { key: 'baseline', label: 'Baseline', color: COLORS.slate, format: (v) => formatCurrency(v) },
                        { key: 'scenario', label: 'Scenario', color: COLORS.coral, format: (v) => formatCurrency(v) },
                        { key: 'fill_rate', label: 'Fill rate', format: (v) => formatPercent(v) },
                      ]}
                    />
                  }
                />
                <Bar isAnimationActive={animate} dataKey="baseline" name="Baseline" fill="rgba(148,163,184,0.35)" radius={[3, 3, 0, 0]} maxBarSize={28} />
                <Bar isAnimationActive={animate} dataKey="scenario" name="Scenario" fill={COLORS.coral} radius={[3, 3, 0, 0]} maxBarSize={28} />
              </BarChart>
            </ResponsiveContainer>
          </SectionCard>
        </div>

        {result?.at_risk?.length > 0 && (
          <SectionCard title="Most exposed segments" subtitle="Ranked by scenario lost sales" bodyClassName="card__body--flush">
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Segment</th>
                    <th>Category</th>
                    <th className="r">Stockout prob.</th>
                    <th className="r">Lost units</th>
                    <th className="r">Lost sales</th>
                  </tr>
                </thead>
                <tbody>
                  {result.at_risk.map((r) => (
                    <tr key={r.segment}>
                      <td>{r.segment}</td>
                      <td className="secondary">{r.category}</td>
                      <td className="r num">
                        <div className="bar-cell">
                          {formatPercent(r.p_stockout)}
                          <div className="bar-cell__track">
                            <div className="bar-cell__fill" style={{ width: `${r.p_stockout * 100}%`, background: r.p_stockout > 0.5 ? COLORS.coral : r.p_stockout > 0.2 ? COLORS.amber : COLORS.emerald }} />
                          </div>
                        </div>
                      </td>
                      <td className="r num">{Math.round(r.lost_units).toLocaleString()}</td>
                      <td className="r num">{formatCurrency(r.lost_revenue)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </SectionCard>
        )}

        {briefing && (
          <SectionCard
            title="Scenario briefing"
            subtitle={briefing.source === 'groq' ? `Groq · ${briefing.model}` : 'Local analytics engine'}
            className="view"
          >
            <Markdown source={briefing.text} />
          </SectionCard>
        )}

        {result?.assumptions && (
          <p className="muted" style={{ fontSize: 11 }}>
            {result.assumptions.join(' ')}
          </p>
        )}
      </div>
    </div>
  );
}
