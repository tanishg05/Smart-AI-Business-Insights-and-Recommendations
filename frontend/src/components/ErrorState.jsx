import { AlertTriangle, RotateCw } from 'lucide-react';

export default function ErrorState({ message, onRetry }) {
  return (
    <div className="card state" role="alert">
      <div className="state__icon" style={{ color: 'var(--status-critical)' }}>
        <AlertTriangle size={18} />
      </div>
      <div>
        <h3 className="state__title">Something went wrong</h3>
        <p className="state__text">{message}</p>
      </div>
      <div>
        <button className="btn" onClick={onRetry}>
          <RotateCw size={14} />
          Retry
        </button>
      </div>
    </div>
  );
}
