import { useCallback, useEffect, useRef, useState } from 'react';
import { errorMessage, fetchProactiveInsights } from '../services/api';

export default function useProactiveInsights(filters, enabled, version) {
  const [state, setState] = useState({ insights: null, source: null, model: null, loading: false, error: '' });
  const req = useRef(0);

  const load = useCallback(async () => {
    if (!enabled) return;
    const id = ++req.current;
    setState((s) => ({ ...s, loading: true, error: '' }));
    try {
      const response = await fetchProactiveInsights(filters);
      if (id !== req.current) return;
      setState({ ...response.data, loading: false, error: '' });
    } catch (err) {
      if (id !== req.current) return;
      setState((s) => ({ ...s, loading: false, error: errorMessage(err) }));
    }
  }, [filters, enabled]);

  useEffect(() => {
    load();
  }, [load, version]);

  return { ...state, reload: load };
}
