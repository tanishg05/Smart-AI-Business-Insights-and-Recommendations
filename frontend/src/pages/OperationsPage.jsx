import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import SectionCard from '../components/SectionCard';

export default function OperationsPage({ data }) {
  const deliveryData = data?.delivery_distribution || [];
  const stockData = data?.stock_sales || [];

  return (
    <>
      <div className="grid-2">
        <SectionCard title="Delivery Time Distribution" subtitle="Fulfillment speed">
          <ResponsiveContainer width="100%" height={260}>
            <ScatterChart>
              <CartesianGrid />
              <XAxis type="number" dataKey="delivery_days" name="Delivery Days" />
              <YAxis type="number" dataKey="count" name="Count" />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter data={deliveryData} fill="#2563eb" />
            </ScatterChart>
          </ResponsiveContainer>
        </SectionCard>

        <SectionCard title="Stock vs Sales" subtitle="Inventory utilization signal">
          <ResponsiveContainer width="100%" height={260}>
            <ScatterChart>
              <CartesianGrid />
              <XAxis type="number" dataKey="stock_available" name="Stock Available" />
              <YAxis type="number" dataKey="units_sold" name="Units Sold" />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter data={stockData} fill="#10b981" />
            </ScatterChart>
          </ResponsiveContainer>
        </SectionCard>
      </div>
    </>
  );
}
