import { Database, FileSpreadsheet, Loader2 } from 'lucide-react';
import UploadPanel from './UploadPanel';

export default function EmptyState({ datasets = [], onLoad, onUpload, busy }) {
  return (
    <div className="card state">
      <div className="state__icon">
        <Database size={18} />
      </div>
      <div>
        <h3 className="state__title">Connect a dataset</h3>
        <p className="state__text">
          Upload a CSV with <span className="mono">date, units_sold, price_unit, delivery_days, delivered_qty, stock_available</span>, plus
          optional <span className="mono">region, channel, category, sku</span>.
        </p>
      </div>
      {datasets.length > 0 && (
        <div className="dataset-list">
          <span className="eyebrow">Available on the server</span>
          {datasets.map((d) => (
            <button key={d.file_name} className="dataset-row" onClick={() => onLoad(d.file_name)} disabled={Boolean(busy)}>
              {busy === d.file_name ? <Loader2 size={14} style={{ animation: 'spin 0.8s linear infinite' }} /> : <FileSpreadsheet size={14} />}
              <span>{d.file_name}</span>
              <span className="dataset-row__size">{d.size_kb >= 1024 ? `${(d.size_kb / 1024).toFixed(1)} MB` : `${d.size_kb} KB`}</span>
            </button>
          ))}
        </div>
      )}
      <div>
        <UploadPanel onUpload={onUpload} busy={busy} variant="primary" />
      </div>
    </div>
  );
}
