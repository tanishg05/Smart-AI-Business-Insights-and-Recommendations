import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
  timeout: 20000
});

export async function fetchDashboard() {
  return api.get('/dashboard');
}

export async function fetchSales() {
  return api.get('/sales');
}

export async function fetchSeasonality() {
  return api.get('/seasonality');
}

export async function fetchOperations() {
  return api.get('/operations');
}

export async function fetchInsights() {
  return api.get('/insights');
}

export async function fetchRecommendations() {
  return api.get('/recommendations');
}

export async function uploadDataset(file) {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
}
