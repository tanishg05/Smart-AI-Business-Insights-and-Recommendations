import { Sparkles } from 'lucide-react';
import { useCopilot } from '../context/CopilotContext';

/**
 * Card shell for every chart and panel.
 * Pass `inspect={{ query, data }}` to show the "Inspect with Groq" action, which sends the chart's data slice to the copilot.
 */
export default function SectionCard({ title, subtitle, tools, inspect, footer, children, className = '', bodyClassName = '', lift = false }) {
  const { ask } = useCopilot();

  return (
    <section className={`card ${lift ? 'card--lift' : ''} ${className}`}>
      {(title || tools || inspect) && (
        <header className="card__head">
          <div className="card__titles">
            {title && <h3 className="card__title">{title}</h3>}
            {subtitle && <p className="card__subtitle">{subtitle}</p>}
          </div>
          <div className="card__tools">
            {tools}
            {inspect && (
              <button
                type="button"
                className="inspect-btn"
                title="Inspect with Groq"
                aria-label={`Inspect ${title} with Groq`}
                onClick={() => ask(inspect.query || `Explain the key movements in "${title}" and what to do about them.`, { title, data: inspect.data })}
              >
                <Sparkles size={13} />
                <span>Inspect</span>
              </button>
            )}
          </div>
        </header>
      )}
      <div className={`card__body ${bodyClassName}`}>{children}</div>
      {footer && <footer className="card__foot">{footer}</footer>}
    </section>
  );
}
