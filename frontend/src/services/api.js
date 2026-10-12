import axios from 'axios';

export const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
});

/** Drop empty filter values so the backend sees only active filters. */
export function cleanFilters(filters = {}) {
  return Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== undefined && v !== null && v !== '' && v !== 'all'));
}

export function errorMessage(err, fallback = 'Request failed.') {
  if (err?.response?.data?.detail) return String(err.response.data.detail);
  if (err?.code === 'ERR_NETWORK' || err?.message === 'Network Error') {
    return `Can't reach the API at ${API_BASE}. Is the backend running?`;
  }
  return err?.message || fallback;
}

export async function fetchDashboard(filters) {
  return api.get('/dashboard', { params: cleanFilters(filters) });
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
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 180000,
  });
}

export async function listDatasets() {
  return api.get('/api/datasets');
}

export async function loadDataset(fileName) {
  return api.post('/api/datasets/load', { file_name: fileName }, { timeout: 180000 });
}

// ───────────── Groq intelligence ─────────────

export async function fetchAIStatus() {
  return api.get('/api/ai/status');
}

export async function fetchProactiveInsights(filters) {
  return api.get('/api/ai/proactive-insights', { params: cleanFilters(filters) });
}

export async function simulateScenario(params, filters, includeNarrative = false, signal) {
  return api.post(
    '/api/ai/scenario-simulate',
    { ...params, context_filters: cleanFilters(filters), include_narrative: includeNarrative },
    { signal }
  );
}

/**
 * Stream a copilot answer over server-sent events.
 * onEvent receives {type: 'meta'|'delta'|'done'|'error', ...}.
 */
export async function streamAIQuery({ query, filters, history, chartContext, signal, onEvent }) {
  const response = await fetch(`${API_BASE}/api/ai/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({
      query,
      context_filters: cleanFilters(filters),
      conversation_history: history,
      chart_context: chartContext || null,
      stream: true,
    }),
    signal,
  });

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body?.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let boundary;
    while ((boundary = buffer.indexOf('\n\n')) !== -1) {
      const frame = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const line = frame.split('\n').find((l) => l.startsWith('data: '));
      if (!line) continue;
      try {
        onEvent(JSON.parse(line.slice(6)));
      } catch {
        /* ignore malformed frames */
      }
    }
  }
}
