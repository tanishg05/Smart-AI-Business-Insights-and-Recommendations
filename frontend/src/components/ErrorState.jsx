export default function ErrorState({ message, onRetry }) {
  return (
    <div className="error-state">
      <h3>Something went wrong</h3>
      <p>{message}</p>
      <button className="btn btn-primary" onClick={onRetry}>
        Retry
      </button>
    </div>
  );
}
