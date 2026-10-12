/** Skeletons shaped like the real layout so nothing jumps when data arrives. */
export function SkeletonBlock({ height = 16, width = '100%', style }) {
  return <div className="skeleton" style={{ height, width, ...style }} />;
}

export function ChartSkeleton({ height = 280 }) {
  return (
    <div className="card skeleton-card">
      <SkeletonBlock height={14} width="38%" />
      <SkeletonBlock height={10} width="22%" />
      <SkeletonBlock height={height} />
    </div>
  );
}

export default function Loader() {
  return (
    <div className="view" aria-busy="true" aria-label="Loading dashboard">
      <div className="grid grid--kpi">
        {Array.from({ length: 5 }).map((_, i) => (
          <div className="card skeleton-card" key={i}>
            <SkeletonBlock height={12} width="55%" />
            <SkeletonBlock height={30} width="70%" />
            <SkeletonBlock height={34} />
          </div>
        ))}
      </div>
      <div className="grid grid--main">
        <ChartSkeleton height={300} />
        <ChartSkeleton height={300} />
      </div>
      <div className="grid grid--2">
        <ChartSkeleton height={220} />
        <ChartSkeleton height={220} />
      </div>
    </div>
  );
}
