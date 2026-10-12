import { useCallback, useEffect, useRef, useState } from 'react';
import {
  errorMessage,
  fetchDashboard,
  listDatasets,
  loadDataset as loadDatasetRequest,
  uploadDataset as uploadDatasetRequest,
} from '../services/api';

const NO_DATASET = 'No dataset loaded';

export default function useDashboardData(filters) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [noDataset, setNoDataset] = useState(false);
  const [datasets, setDatasets] = useState([]);
  const [busy, setBusy] = useState('');
  const requestId = useRef(0);
  const hasData = useRef(false);

  const refreshDatasets = useCallback(async () => {
    try {
      const response = await listDatasets();
      setDatasets(response.data.datasets || []);
    } catch {
      setDatasets([]);
    }
  }, []);

  const refreshDashboard = useCallback(async () => {
    const id = ++requestId.current;
    // Keep the current view on screen while filters change; skeletons only on first load.
    if (hasData.current) setRefreshing(true);
    else setLoading(true);
    setError('');
    try {
      const response = await fetchDashboard(filters);
      if (id !== requestId.current) return;
      setData(response.data);
      setNoDataset(false);
      hasData.current = true;
    } catch (err) {
      if (id !== requestId.current) return;
      const message = errorMessage(err, 'Failed to load dashboard data.');
      if (message.includes(NO_DATASET)) {
        setNoDataset(true);
        setData(null);
        hasData.current = false;
        refreshDatasets();
      } else {
        setError(message);
      }
    } finally {
      if (id === requestId.current) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  }, [filters, refreshDatasets]);

  const runLoad = useCallback(
    async (label, request) => {
      setBusy(label);
      setError('');
      try {
        await request();
        hasData.current = false;
        await refreshDashboard();
        refreshDatasets();
        return true;
      } catch (err) {
        setError(errorMessage(err, 'Upload failed.'));
        return false;
      } finally {
        setBusy('');
      }
    },
    [refreshDashboard, refreshDatasets]
  );

  const uploadDataset = useCallback((file) => runLoad(file.name, () => uploadDatasetRequest(file)), [runLoad]);
  const loadDataset = useCallback((name) => runLoad(name, () => loadDatasetRequest(name)), [runLoad]);

  useEffect(() => {
    refreshDashboard();
  }, [refreshDashboard]);

  return {
    data,
    loading,
    refreshing,
    error,
    noDataset,
    datasets,
    busy,
    datasetName: data?.last_file_name || '',
    refreshDashboard,
    uploadDataset,
    loadDataset,
    refreshDatasets,
  };
}
