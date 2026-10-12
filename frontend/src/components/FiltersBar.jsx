import { ChevronDown, X } from 'lucide-react';
import { formatNumber } from '../utils/formatters';

const DIMENSIONS = [
  { key: 'region', label: 'Region' },
  { key: 'channel', label: 'Channel' },
  { key: 'category', label: 'Category' },
  { key: 'season', label: 'Season' },
];

export default function FiltersBar({ options = {}, value, onChange, rows, totalRows, granularity }) {
  const active = Object.values(value).filter(Boolean).length;

  return (
    <div className="filters" role="toolbar" aria-label="Filters">
      {DIMENSIONS.map(({ key, label }) => {
        const choices = options[key] || [];
        if (choices.length < 2 && !value[key]) return null;
        return (
          <label key={key} className={`filter ${value[key] ? 'is-set' : ''}`}>
            <span className="filter__label">{label}</span>
            <select value={value[key] || ''} onChange={(e) => onChange({ ...value, [key]: e.target.value })} aria-label={label}>
              <option value="">All</option>
              {choices.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
            <ChevronDown size={12} className="filter__chev" />
          </label>
        );
      })}
      {active > 0 && (
        <button className="btn btn--ghost btn--sm" onClick={() => onChange({})}>
          <X size={12} />
          Clear {active}
        </button>
      )}
      <div className="filters__meta">
        {rows !== undefined && (
          <span className="mono">
            {formatNumber(rows)} / {formatNumber(totalRows)} rows
          </span>
        )}
        {granularity && <span className="badge badge--neutral">{granularity}ly</span>}
      </div>
    </div>
  );
}
