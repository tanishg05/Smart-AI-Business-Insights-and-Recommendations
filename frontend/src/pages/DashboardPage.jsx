import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import KPIGrid from '../components/KPIGrid';
import SectionCard from '../components/SectionCard';
import RecommendationCard from '../components/RecommendationCard';
import { formatMetric, formatNumber } from '../utils/formatters';

export default function DashboardPage({ data }) {
  const summary = data?.summary || {};
  const trend = data?.sales_trend || [];
  const recommendations = data?.recommendations || [];

  const metrics = [
    { label: 'Total Units Sold', value: summary.total_sales || 0, type: 'number' },
    { label: 'Average Price', value: summary.avg_price || 0, type: 'metric' },
    { label: 'Average Delivery Days', value: summary.avg_delivery || 0, type: 'metric' },
    { label: 'Stock Utilization', value: summary.utilization || 0, type: 'percent' }
  ];

  return (
    <>
      <KPIGrid metrics={metrics} />

      <div className="grid-2">
        <SectionCard title="Sales Trend" subtitle="Demand movement over time">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tickFormatter={(value) => value.slice(0, 10)} />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="units_sold" stroke="#2563eb" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </SectionCard>

        <SectionCard title="AI Snapshot" subtitle="Quick business focus">
          <div className="stack">
            <div className="snapshot-box">
              <p>High Demand Share</p>
              <h3>{formatMetric(data?.insights?.high_demand_ratio || 0)}</h3>
            </div>
            <div className="snapshot-box">
              <p>Forecast Next Period</p>
              <h3>{formatNumber(data?.forecast?.forecast || 0)}</h3>
            </div>
          </div>
        </SectionCard>
      </div>

      <SectionCard title="Recommended Actions" subtitle="Operational priorities">
        <div className="cards-grid">
          {recommendations.slice(0, 3).map((item) => (
            <RecommendationCard key={item.title} title={item.title} description={item.description} />
          ))}
        </div>
      </SectionCard>
    </>
  );
}
