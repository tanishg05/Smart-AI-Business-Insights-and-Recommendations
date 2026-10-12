import { useRef } from 'react';
import { UploadCloud } from 'lucide-react';

export default function UploadPanel({ onUpload }) {
  const inputRef = useRef(null);

  const handleChange = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    await onUpload(file);
    event.target.value = '';
  };

  return (
    <div className="upload-panel">
      <div>
        <h3>Upload CSV Dataset</h3>
        <p>Use your supply chain or sales CSV to generate analytics.</p>
      </div>

      <button className="btn btn-primary" onClick={() => inputRef.current?.click()}>
        <UploadCloud size={18} />
        Upload CSV
      </button>

      <input ref={inputRef} type="file" accept=".csv" hidden onChange={handleChange} />
    </div>
  );
}
