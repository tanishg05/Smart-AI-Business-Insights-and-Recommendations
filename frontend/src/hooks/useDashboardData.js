import { useEffect, useState } from 'react';
import { fetchDashboard, uploadDataset as uploadDatasetRequest } from '../services/api';

export default function useDashboardData() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [datasetName, setDatasetName] = useState('');

  const refreshDashboard = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetchDashboard();
      setData(response.data);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  const uploadDataset = async (file) => {
    setLoading(true);
    setError('');
    try {
      const response = await uploadDatasetRequest(file);
      setDatasetName(file.name);
      setData(response.data);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Upload failed.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshDashboard();
  }, []);

  return { data, loading, error, datasetName, refreshDashboard, uploadDataset };
}
