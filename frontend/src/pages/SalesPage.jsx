import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import SectionCard from '../components/SectionCard';

export default function SalesPage({ data }) {
  const channelData = data?.sales_by_channel || [];
  const regionData = data?.sales_by_region || [];
  const categoryData = data?.category_sales || [];

  return (
    <>
      <div className="grid-2">
        <SectionCard title="Sales by Channel" subtitle="Channel contribution">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={channelData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="channel" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="units_sold" fill="#0f766e" />
            </BarChart>
          </ResponsiveContainer>
        </SectionCard>

        <SectionCard title="Regional Contribution" subtitle="Sales by region">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={regionData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="region" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="units_sold" fill="#7c3aed" />
            </BarChart>
          </ResponsiveContainer>
        </SectionCard>
      </div>

      <SectionCard title="Category Performance" subtitle="Best-performing categories">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={categoryData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="category" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="units_sold" fill="#2563eb" />
          </BarChart>
        </ResponsiveContainer>
      </SectionCard>
    </>
  );
}
