import { ArrowUpRight, KeyRound, MessageSquareText, RotateCw, Sparkles } from 'lucide-react';
import SectionCard from '../components/SectionCard';
import InsightPills from '../components/InsightPills';
import { QUICK_PROMPTS } from '../components/GroqCopilotDrawer';
import { useCopilot, useCopilotChat } from '../context/CopilotContext';
import RecommendationsPage from './RecommendationsPage';
import { COLORS } from '../utils/chartTheme';
import { formatNumber, formatPercent } from '../utils/formatters';

const EXTRA_PROMPTS = [
  'Which promotions are leaking margin and where should we cut discount depth?',
  'What safety stock should each region hold to reach a 95% service level?',
];

// Subscribes to the chat transcript on its own so streaming doesn't re-render the hub.
function RecentQuestions() {
  const { setOpen } = useCopilot();
  const { messages } = useCopilotChat();
  const recent = messages.filter((m) => m.role === 'user').slice(-3).reverse();
  if (!recent.length) return null;
  return (
    <SectionCard title="Recent questions">
      <div style={{ display: 'grid', gap: 6 }}>
        {recent.map((m) => (
          <button key={m.id} className="chip" onClick={() => setOpen(true)}>
            {m.content}
          </button>
        ))}
      </div>
    </SectionCard>
  );
}

export default function AIPage({ data, insights }) {
  const { ask, status, setKeyModal, setOpen } = useCopilot();
  const classification = data.demand_classification || [];
  const total = classification.reduce((s, c) => s + c.count, 0) || 1;
  const counts = { CRITICAL: 0, WARNING: 0, OPPORTUNITY: 0 };
  (insights.insights || []).forEach((i) => (counts[i.severity] += 1));

  return (
    <div className="view">
      <section className="card hub-hero" style={{ marginBottom: 14 }}>
        <div>
          <p className="eyebrow" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span className={`dot ${status.enabled ? 'dot--healthy' : 'dot--warning'}`} />
            {status.enabled ? `Groq live · ${status.model}` : 'Local analytics engine'}
          </p>
          <h2 className="hub-hero__title" style={{ marginTop: 6 }}>
            {counts.CRITICAL > 0
              ? `${counts.CRITICAL} critical signal${counts.CRITICAL > 1 ? 's' : ''} need attention`
              : counts.WARNING > 0
                ? `${counts.WARNING} warning${counts.WARNING > 1 ? 's' : ''} to review`
                : 'No critical signals in this slice'}
          </h2>
          <p className="hub-hero__text">
            Every answer is grounded in the loaded dataset: aggregates, deficit SKUs, regional seasonality, lead-time variance and turnover are
            serialised into the model's context before it reasons.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {!status.enabled && (
            <button className="btn" onClick={() => setKeyModal(true)}>
              <KeyRound size={14} />
              Connect Groq
            </button>
          )}
          <button className="btn btn--primary" onClick={() => setOpen(true)}>
            <Sparkles size={14} />
            Open copilot
          </button>
        </div>
      </section>

      <div className="grid grid--main">
        <SectionCard
          title="Proactive insights"
          subtitle="Lead-time anomalies, stockout hazards, margin leaks and seasonal mismatch"
          tools={
            <>
              <span className="badge badge--critical">{counts.CRITICAL}</span>
              <span className="badge badge--warning">{counts.WARNING}</span>
              <span className="badge badge--opportunity">{counts.OPPORTUNITY}</span>
              <button className="btn btn--ghost btn--icon btn--sm" onClick={insights.reload} title="Rescan" aria-label="Rescan insights">
                <RotateCw size={12} style={insights.loading ? { animation: 'spin .8s linear infinite' } : undefined} />
              </button>
            </>
          }
        >
          {insights.error ? <p className="muted">{insights.error}</p> : <InsightPills insights={insights.insights} loading={insights.loading} />}
        </SectionCard>

        <div style={{ display: 'grid', gap: 14, alignContent: 'start' }}>
          <SectionCard title="Ask the copilot" subtitle="One click sends the prompt with your current filters">
            <div className="prompt-grid" style={{ gridTemplateColumns: '1fr' }}>
              {[...QUICK_PROMPTS, ...EXTRA_PROMPTS].map((p) => (
                <button key={p} className="prompt-card" onClick={() => ask(p)}>
                  <MessageSquareText size={14} />
                  <span>{p}</span>
                  <ArrowUpRight size={13} style={{ marginLeft: 'auto', color: 'var(--text-faint)' }} />
                </button>
              ))}
            </div>
          </SectionCard>

          <SectionCard title="Demand classification" subtitle="Orders above vs below mean units sold" inspect={{ data: classification }}>
            <div className="split-bar">
              {classification.map((c, i) => (
                <div key={c.demand_class} style={{ width: `${(c.count / total) * 100}%`, background: i === 0 ? COLORS.ice : 'rgba(148,163,184,0.4)' }} />
              ))}
            </div>
            <div className="legend" style={{ marginTop: 10 }}>
              {classification.map((c, i) => (
                <span key={c.demand_class} className="legend__item">
                  <span className="legend__swatch" style={{ background: i === 0 ? COLORS.ice : 'rgba(148,163,184,0.4)' }} />
                  {c.demand_class}
                  <span className="mono muted">
                    {formatNumber(c.count)} · {formatPercent(c.count / total)}
                  </span>
                </span>
              ))}
            </div>
            <p className="muted" style={{ marginTop: 10, fontSize: 12 }}>
              Peak season <span className="secondary">{data.insights.high_demand_season}</span> · slowest region{' '}
              <span className="secondary">{data.insights.slow_region}</span>
            </p>
          </SectionCard>

          <RecentQuestions />
        </div>
      </div>

      <SectionCard title="Recommended actions" subtitle="Threshold-based priorities computed from the current slice">
        <RecommendationsPage data={data} />
      </SectionCard>
    </div>
  );
}
