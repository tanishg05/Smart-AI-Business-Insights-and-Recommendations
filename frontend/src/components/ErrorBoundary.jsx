import { Component } from 'react';
import { AlertTriangle, RotateCw } from 'lucide-react';

/** Keeps a crash in one view from blanking the whole app. */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error('View crashed', error, info?.componentStack);
  }

  componentDidUpdate(prevProps) {
    if (this.state.error && prevProps.resetKey !== this.props.resetKey) this.setState({ error: null });
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="card state" role="alert">
        <div className="state__icon" style={{ color: 'var(--status-critical)' }}>
          <AlertTriangle size={18} />
        </div>
        <div>
          <h3 className="state__title">This view hit an error</h3>
          <p className="state__text mono" style={{ fontSize: 12 }}>{String(this.state.error?.message || this.state.error)}</p>
        </div>
        <div>
          <button className="btn" onClick={() => this.setState({ error: null })}>
            <RotateCw size={14} />
            Try again
          </button>
        </div>
      </div>
    );
  }
}
