import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { fetchAIStatus, streamAIQuery } from '../services/api';

const CopilotContext = createContext(null);

let nextId = 1;
const MAX_CHART_ROWS = 40;

/** Trim a chart's data slice to what the model needs. */
function compactChart(chart) {
  if (!chart) return null;
  const rows = Array.isArray(chart.data) ? chart.data : [];
  const step = rows.length > MAX_CHART_ROWS ? Math.ceil(rows.length / MAX_CHART_ROWS) : 1;
  return {
    title: chart.title,
    data: rows.filter((_, i) => i % step === 0).slice(0, MAX_CHART_ROWS),
  };
}

export function CopilotProvider({ filters, children }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [streaming, setStreaming] = useState(false);
  const [status, setStatus] = useState({ enabled: false, mode: 'engine', model: null, loaded: false });
  const [keyModal, setKeyModal] = useState(false);
  const abortRef = useRef(null);
  const messagesRef = useRef(messages);
  messagesRef.current = messages;

  const refreshStatus = useCallback(async () => {
    try {
      const response = await fetchAIStatus();
      setStatus({ ...response.data, loaded: true });
    } catch {
      setStatus((s) => ({ ...s, loaded: true, offline: true }));
    }
  }, []);

  useEffect(() => {
    refreshStatus();
  }, [refreshStatus]);

  const patch = (id, fn) => setMessages((list) => list.map((m) => (m.id === id ? { ...m, ...fn(m) } : m)));

  const ask = useCallback(
    async (query, chart) => {
      const text = String(query || '').trim();
      if (!text) return;
      setOpen(true);
      abortRef.current?.abort();

      const history = messagesRef.current
        .filter((m) => m.content && !m.error)
        .slice(-12)
        .map((m) => ({ role: m.role, content: m.content }));

      const userMsg = { id: nextId++, role: 'user', content: text, chart: chart?.title || null };
      const botId = nextId++;
      setMessages((list) => [...list, userMsg, { id: botId, role: 'assistant', content: '', pending: true, source: null }]);
      setStreaming(true);

      const controller = new AbortController();
      abortRef.current = controller;
      try {
        await streamAIQuery({
          query: text,
          filters,
          history,
          chartContext: compactChart(chart),
          signal: controller.signal,
          onEvent: (event) => {
            if (event.type === 'meta') patch(botId, () => ({ source: event.source, model: event.model, fallback: event.fallback_reason }));
            else if (event.type === 'delta') patch(botId, (m) => ({ content: m.content + event.text, pending: false }));
            else if (event.type === 'error') patch(botId, () => ({ error: event.message, pending: false }));
          },
        });
      } catch (err) {
        if (err.name !== 'AbortError') {
          patch(botId, () => ({ error: err.message || 'The copilot could not answer.', pending: false }));
        }
      } finally {
        patch(botId, () => ({ pending: false, done: true }));
        if (abortRef.current === controller) {
          abortRef.current = null;
          setStreaming(false);
        }
      }
    },
    [filters]
  );

  const stop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setStreaming(false);
  }, []);

  const clear = useCallback(() => {
    stop();
    setMessages([]);
  }, [stop]);

  const value = useMemo(
    () => ({
      open,
      setOpen,
      toggle: () => setOpen((o) => !o),
      messages,
      streaming,
      ask,
      stop,
      clear,
      status,
      refreshStatus,
      keyModal,
      setKeyModal,
    }),
    [open, messages, streaming, ask, stop, clear, status, refreshStatus, keyModal]
  );

  return <CopilotContext.Provider value={value}>{children}</CopilotContext.Provider>;
}

export function useCopilot() {
  const ctx = useContext(CopilotContext);
  if (!ctx) throw new Error('useCopilot must be used inside CopilotProvider');
  return ctx;
}
