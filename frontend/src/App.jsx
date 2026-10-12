import { useState } from 'react';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import UploadPanel from './components/UploadPanel';
import FiltersBar from './components/FiltersBar';
import Loader from './components/Loader';
import ErrorState from './components/ErrorState';
import DashboardPage from './pages/DashboardPage';
import SalesPage from './pages/SalesPage';
import SeasonalPage from './pages/SeasonalPage';
import OperationsPage from './pages/OperationsPage';
import AIPage from './pages/AIPage';
import RecommendationsPage from './pages/RecommendationsPage';
import useDashboardData from './hooks/useDashboardData';

export default function App() {
  const [activeView, setActiveView] = useState('dashboard');
  const [filterValue, setFilterValue] = useState('overall');

  const { data, loading, error, datasetName, uploadDataset, refreshDashboard } = useDashboardData();

  return (
    <div className="app-shell">
      <Sidebar activeView={activeView} onSelect={setActiveView} />

      <main className="main-shell">
        <Navbar activeView={activeView} datasetName={datasetName} />

        <div className="content">
          <UploadPanel onUpload={uploadDataset} />
          <FiltersBar value={filterValue} onChange={setFilterValue} />

          {loading ? (
            <Loader />
          ) : error ? (
            <ErrorState message={error} onRetry={refreshDashboard} />
          ) : data ? (
            renderPage(activeView, data)
          ) : (
            <div className="empty-state">
              <h3>No dataset loaded</h3>
              <p>Upload a CSV to generate insights and recommendations.</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

function renderPage(activeView, data) {
  switch (activeView) {
    case 'sales':
      return <SalesPage data={data} />;
    case 'seasonality':
      return <SeasonalPage data={data} />;
    case 'operations':
      return <OperationsPage data={data} />;
    case 'ai':
      return <AIPage data={data} />;
    case 'recommendations':
      return <RecommendationsPage data={data} />;
    default:
      return <DashboardPage data={data} />;
  }
}
