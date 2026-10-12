import { useRef } from 'react';
import { Loader2, UploadCloud } from 'lucide-react';

export default function UploadPanel({ onUpload, busy, variant = 'default' }) {
  const inputRef = useRef(null);

  const handleChange = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    await onUpload(file);
    event.target.value = '';
  };

  return (
    <>
      <button
        type="button"
        className={`btn ${variant === 'primary' ? 'btn--primary' : ''}`}
        onClick={() => inputRef.current?.click()}
        disabled={Boolean(busy)}
      >
        {busy ? <Loader2 size={14} style={{ animation: 'spin 0.8s linear infinite' }} /> : <UploadCloud size={14} />}
        {busy ? 'Processing…' : 'Upload CSV'}
      </button>
      <input ref={inputRef} type="file" accept=".csv,text/csv" hidden onChange={handleChange} />
    </>
  );
}
