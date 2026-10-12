import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import SectionCard from '../components/SectionCard';
import RecommendationCard from '../components/RecommendationCard';

const COLORS = ['#2563eb', '#f59e0b'];

export default function AIPage({ data }) {
  const classification = data?.demand_classification || [];
  const insights = data?.insights || {};

  return (
    <>
      <SectionCard title="Demand Classification" subtitle="High vs low demand segmentation">
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie data={classification} dataKey="count" nameKey="demand_class" outerRadius={90}>
              {classification.map((entry, index) => (
                <Cell key={entry.demand_class} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </SectionCard>

      <SectionCard title="AI Business Insights" subtitle="Model-driven interpretation">
        <div className="cards-grid">
          <RecommendationCard title="High Demand Share" description={`${(insights.high_demand_ratio || 0) * 100}% of records fall in the high demand bucket.`} />
          <RecommendationCard title="Peak Season" description={`Peak demand season is ${insights.high_demand_season || 'not available'}.`} />
          <RecommendationCard title="Slow Region" description={`Lowest activity region: ${insights.slow_region || 'not available'}.`} />
        </div>
      </SectionCard>
    </>
  );
}
