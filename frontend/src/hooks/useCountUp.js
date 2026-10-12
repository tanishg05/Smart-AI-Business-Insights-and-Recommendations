import { useEffect, useRef, useState } from 'react';

const easeOutExpo = (t) => (t === 1 ? 1 : 1 - 2 ** (-10 * t));

/** Animate a number from its previous value to `target`. */
export default function useCountUp(target, duration = 900) {
  const [value, setValue] = useState(Number(target) || 0);
  const from = useRef(Number(target) || 0);
  const frame = useRef(0);

  useEffect(() => {
    const to = Number(target) || 0;
    const start = performance.now();
    const origin = from.current;
    if (origin === to || window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
      from.current = to;
      setValue(to);
      return undefined;
    }
    const tick = (now) => {
      const t = Math.min(1, (now - start) / duration);
      const next = origin + (to - origin) * easeOutExpo(t);
      setValue(next);
      if (t < 1) frame.current = requestAnimationFrame(tick);
      else from.current = to;
    };
    frame.current = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(frame.current);
      from.current = to;
    };
  }, [target, duration]);

  return value;
}
