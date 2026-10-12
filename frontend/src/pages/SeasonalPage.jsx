import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import SectionCard from '../components/SectionCard';

export default function SeasonalPage({ data }) {
  const seasonalData = data?.seasonal_sales || [];

  return (
    <>
      <SectionCard title="Seasonal Sales Distribution" subtitle="Demand by season">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={seasonalData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="season" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="units_sold" fill="#f59e0b" />
          </BarChart>
        </ResponsiveContainer>
      </SectionCard>

      <SectionCard title="Season vs Region" subtitle="Cross-regional seasonal view">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={data?.season_region_heatmap || []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="season" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="units_sold" fill="#dc2626" />
          </BarChart>
        </ResponsiveContainer>
      </SectionCard>
    </>
  );
}
