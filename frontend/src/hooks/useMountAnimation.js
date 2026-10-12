import { useEffect, useState } from 'react';

/**
 * Recharts replays its draw-in animation whenever a series receives a new data array,
 * which makes charts blank out and redraw on every filter change or re-render.
 * Animate only on first mount; afterwards updates swap in place.
 */
export default function useMountAnimation(duration = 1100) {
  const [animate, setAnimate] = useState(true);
  useEffect(() => {
    const timer = setTimeout(() => setAnimate(false), duration);
    return () => clearTimeout(timer);
  }, [duration]);
  return animate;
}
