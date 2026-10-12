const isNil = (value) => value === null || value === undefined || Number.isNaN(Number(value));

// Intl throws RangeError for fraction digits outside 0–20 or for non-numbers; clamp defensively.
const safeDigits = (digits, fallback = 0) => {
  const n = Number(digits);
  return Number.isFinite(n) ? Math.min(20, Math.max(0, Math.round(n))) : fallback;
};

export function formatNumber(value, digits = 0) {
  if (isNil(value)) return '—';
  const d = safeDigits(digits);
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: d, minimumFractionDigits: d }).format(Number(value));
}

export function formatCompact(value, digits = 1) {
  if (isNil(value)) return '—';
  digits = safeDigits(digits, 1);
  const n = Number(value);
  const abs = Math.abs(n);
  if (abs >= 1e9) return `${(n / 1e9).toFixed(digits)}B`;
  if (abs >= 1e6) return `${(n / 1e6).toFixed(digits)}M`;
  // Keep one decimal below 10K so adjacent axis ticks ($1.2K, $1.4K) stay distinct.
  if (abs >= 1e3) return `${(n / 1e3).toFixed(abs < 1e4 ? Math.max(digits, 1) : digits)}K`;
  return formatNumber(n, abs < 10 && n % 1 !== 0 ? 2 : 0);
}

export function formatCurrency(value, { compact = false, digits } = {}) {
  if (isNil(value)) return '—';
  const n = Number(value);
  if (compact) return `${n < 0 ? '−' : ''}$${formatCompact(Math.abs(n), safeDigits(digits, 2))}`;
  const d = safeDigits(digits, Math.abs(n) >= 100 ? 0 : 2);
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: d,
    minimumFractionDigits: d,
  }).format(n);
}

export function formatMetric(value) {
  if (isNil(value)) return '—';
  return Number(value).toFixed(2);
}

export function formatPercent(value, digits = 1) {
  if (isNil(value)) return '—';
  return `${(Number(value) * 100).toFixed(digits)}%`;
}

export function formatDelta(value, digits = 1) {
  if (isNil(value)) return '—';
  const n = Number(value) * 100;
  const sign = n > 0 ? '+' : n < 0 ? '−' : '±';
  return `${sign}${Math.abs(n).toFixed(digits)}%`;
}

export function formatDays(value, digits = 1) {
  if (isNil(value)) return '—';
  return `${Number(value).toFixed(digits)}d`;
}

export function formatDate(value, granularity = 'day') {
  if (!value) return '';
  const d = new Date(`${value}T00:00:00`);
  if (Number.isNaN(d.getTime())) return value;
  if (granularity === 'month') return d.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', ...(granularity === 'week' ? { year: '2-digit' } : {}) });
}

/** Format a KPI value by its declared format. Returns { value, unit }. */
export function formatKpi(format, value) {
  switch (format) {
    case 'currency':
      return { value: formatCurrency(value, { compact: Math.abs(value) >= 10000 }), unit: '' };
    case 'percent':
      return { value: (Number(value) * 100).toFixed(1), unit: '%' };
    case 'turns':
      return { value: Number(value).toFixed(1), unit: '×/yr' };
    case 'index':
      return { value: Number(value).toFixed(1), unit: '/100' };
    case 'days':
      return { value: Number(value).toFixed(2), unit: 'days' };
    default:
      return { value: formatNumber(value), unit: '' };
  }
}
