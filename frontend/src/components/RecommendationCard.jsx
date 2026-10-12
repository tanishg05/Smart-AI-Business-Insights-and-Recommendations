const SEVERITY = {
  critical: { badge: 'critical', label: 'Critical' },
  warning: { badge: 'warning', label: 'Warning' },
  opportunity: { badge: 'opportunity', label: 'Opportunity' },
  healthy: { badge: 'healthy', label: 'Stable' },
};

export default function RecommendationCard({ title, description, severity = 'opportunity' }) {
  const s = SEVERITY[severity] || SEVERITY.opportunity;
  return (
    <div className="rec">
      <span className={`badge badge--${s.badge}`} style={{ justifySelf: 'start' }}>
        {s.label}
      </span>
      <h4 className="rec__title">{title}</h4>
      <p className="rec__desc">{description}</p>
    </div>
  );
}
