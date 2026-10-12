// Shared chart styling so every Recharts surface reads as one system.
export const COLORS = {
  ice: '#38BDF8',
  iceSoft: 'rgba(56, 189, 248, 0.16)',
  emerald: '#10B981',
  amber: '#F59E0B',
  coral: '#EF4444',
  slate: '#94A3B8',
  grid: 'rgba(255, 255, 255, 0.05)',
  axis: '#6B768A',
  text: '#E6EAF2',
};

// Restrained categorical ramp: ice → steel → sand → teal → slate.
export const SERIES = ['#38BDF8', '#8EA4C8', '#D9C8A6', '#5EC2B7', '#64748B', '#BAE6FD', '#A8A29E'];

export const STATUS_COLOR = {
  healthy: COLORS.emerald,
  warning: COLORS.amber,
  critical: COLORS.coral,
  info: COLORS.ice,
};

export const QUADRANT_COLOR = {
  'Critical Low': COLORS.coral,
  'Fast Mover': COLORS.emerald,
  Overstocked: COLORS.amber,
  'Dead Stock': COLORS.slate,
};

export const axisProps = {
  tickLine: false,
  axisLine: false,
  tickMargin: 8,
  fontSize: 10.5,
};

export const gridProps = {
  strokeDasharray: '2 4',
  vertical: false,
  stroke: COLORS.grid,
};

export const ANIMATION = { isAnimationActive: true, animationDuration: 650, animationEasing: 'ease-out' };
