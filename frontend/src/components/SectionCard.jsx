export default function SectionCard({ title, subtitle, children }) {
  return (
    <section className="panel">
      <div className="panel__header">
        <div>
          <h3>{title}</h3>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
      </div>
      <div className="panel__body">{children}</div>
    </section>
  );
}
