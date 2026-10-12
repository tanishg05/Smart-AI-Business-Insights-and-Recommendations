import { useCallback, useEffect, useMemo, useState } from 'react';
import { Sparkles } from 'lucide-react';
import Sidebar, { NAV_ITEMS } from './components/Sidebar';
import Navbar from './components/Navbar';
import FiltersBar from './components/FiltersBar';
import Loader from './components/Loader';
import ErrorState from './components/ErrorState';
import EmptyState from './components/EmptyState';
import GroqCopilotDrawer from './components/GroqCopilotDrawer';
import KeyConfigModal from './components/KeyConfigModal';
import DashboardPage from './pages/DashboardPage';
import SalesPage from './pages/SalesPage';
import SeasonalPage from './pages/SeasonalPage';
import OperationsPage from './pages/OperationsPage';
import SimulatorPage from './pages/SimulatorPage';
import AIPage from './pages/AIPage';
import useDashboardData from './hooks/useDashboardData';
import useProactiveInsights from './hooks/useProactiveInsights';
import useHotkey from './hooks/useHotkey';
import { CopilotProvider, useCopilot } from './context/CopilotContext';

const VIEW_KEY = 'scid.view';

function readView() {
  const fromHash = window.location.hash.replace('#', '');
  if (NAV_ITEMS.some((i) => i.key === fromHash)) return fromHash;
  try {
    const v = window.localStorage.getItem(VIEW_KEY);
    return NAV_ITEMS.some((i) => i.key === v) ? v : 'dashboard';
  } catch {
    return 'dashboard';
  }
}

export default function App() {
  const [filters, setFilters] = useState({});
  const stableFilters = useMemo(() => filters, [JSON.stringify(filters)]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <CopilotProvider filters={stableFilters}>
      <Shell filters={stableFilters} setFilters={setFilters} />
    </CopilotProvider>
  );
}

function Shell({ filters, setFilters }) {
  const [activeView, setActiveView] = useState(readView);
  const [toast, setToast] = useState('');
  const dashboard = useDashboardData(filters);
  const { data, loading, error, noDataset } = dashboard;
  const hasData = Boolean(data && !data.empty);
  const insights = useProactiveInsights(filters, hasData, data?.loaded_at);
  const copilot = useCopilot();

  const selectView = useCallback((key) => {
    setActiveView(key);
    window.history.replaceState(null, '', `#${key}`);
    try {
      window.localStorage.setItem(VIEW_KEY, key);
    } catch {
      /* storage unavailable */
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  useHotkey('k', copilot.toggle);

  useEffect(() => {
    const onHash = () => {
      const key = window.location.hash.replace('#', '');
      if (NAV_ITEMS.some((i) => i.key === key)) setActiveView(key);
    };
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  useEffect(() => {
    const onKey = (e) => {
      const tag = e.target?.tagName;
      if (e.metaKey || e.ctrlKey || e.altKey || tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || copilot.open) return;
      const item = NAV_ITEMS.find((i) => i.kbd === e.key);
      if (item) selectView(item.key);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [copilot.open, selectView]);

  useEffect(() => {
    // Copilot status depends on the dataset being loaded; refresh it when the dataset changes.
    copilot.refreshStatus();
  }, [data?.loaded_at]); // eslint-disable-line react-hooks/exhaustive-deps

  const withToast = (fn) => async (arg) => {
    const ok = await fn(arg);
    if (ok) {
      setFilters({});
      setToast(`Loaded ${arg?.name || arg}`);
      setTimeout(() => setToast(''), 2600);
    }
  };
  const onUpload = withToast(dashboard.uploadDataset);
  const onLoad = withToast(dashboard.loadDataset);

  let body;
  if (loading) body = <Loader />;
  else if (noDataset) body = <EmptyState datasets={dashboard.datasets} onLoad={onLoad} onUpload={onUpload} busy={dashboard.busy} />;
  else if (error && !data) body = <ErrorState message={error} onRetry={dashboard.refreshDashboard} />;
  else if (data?.empty)
    body = (
      <div className="card state">
        <h3 className="state__title">No rows match these filters</h3>
        <p className="state__text">Loosen a filter to bring data back.</p>
        <div>
          <button className="btn" onClick={() => setFilters({})}>
            Clear filters
          </button>
        </div>
      </div>
    );
  else if (data) body = <View key={activeView} view={activeView} data={data} insights={insights} filters={filters} />;

  return (
    <div className="app-shell">
      <Sidebar activeView={activeView} onSelect={selectView} data={data} />

      <main className="main-shell">
        <Navbar
          activeView={activeView}
          data={data}
          refreshing={dashboard.refreshing}
          busy={dashboard.busy}
          onUpload={onUpload}
          onRefresh={() => {
            dashboard.refreshDashboard();
            insights.reload();
          }}
        />

        <div className="content">
          {data && (
            <FiltersBar
              options={data.filter_options}
              value={filters}
              onChange={setFilters}
              rows={data.rows}
              totalRows={data.total_rows}
              granularity={data.granularity}
            />
          )}
          {error && data && <div className="engine-note" style={{ marginBottom: 14 }}>{error}</div>}
          {body}
        </div>
      </main>

      <button className={`fab ${copilot.open ? 'is-hidden' : ''}`} onClick={() => copilot.setOpen(true)} aria-label="Open AI copilot">
        <Sparkles size={15} />
        Ask Copilot
        <span className="kbd">⌘K</span>
      </button>
      <GroqCopilotDrawer hasData={hasData} />
      <KeyConfigModal />
      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}

function View({ view, data, insights, filters }) {
  switch (view) {
    case 'sales':
      return <SalesPage data={data} />;
    case 'seasonality':
      return <SeasonalPage data={data} />;
    case 'operations':
      return <OperationsPage data={data} />;
    case 'simulator':
      return <SimulatorPage filters={filters} />;
    case 'ai':
    case 'recommendations':
      return <AIPage data={data} insights={insights} />;
    default:
      return <DashboardPage data={data} insights={insights} />;
  }
}
