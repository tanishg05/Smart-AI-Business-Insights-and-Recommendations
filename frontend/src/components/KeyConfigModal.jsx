import { KeyRound, X } from 'lucide-react';
import { useCopilot } from '../context/CopilotContext';

export default function KeyConfigModal() {
  const { keyModal, setKeyModal, status, refreshStatus } = useCopilot();
  if (!keyModal) return null;

  return (
    <div className="modal-scrim" onClick={() => setKeyModal(false)}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="key-title" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div className="state__icon">
            <KeyRound size={16} />
          </div>
          <h2 className="modal__title" id="key-title">
            Connect Groq
          </h2>
          <button className="btn btn--ghost btn--icon" style={{ marginLeft: 'auto' }} onClick={() => setKeyModal(false)} aria-label="Close">
            <X size={14} />
          </button>
        </div>
        <p className="secondary">
          {status.enabled
            ? `Groq is live on ${status.model}.`
            : 'The copilot is running on the local analytics engine. Answers are computed from your data but without live LLM reasoning.'}
        </p>
        <ol>
          <li>
            Create a key at <a href="https://console.groq.com/keys" target="_blank" rel="noreferrer">console.groq.com/keys</a>.
          </li>
          <li>
            Add it to <span className="mono">backend/.env</span> (the key stays on the server and is never sent to the browser):
          </li>
        </ol>
        <div className="codeblock">{'GROQ_API_KEY=gsk_…\nGROQ_MODEL=llama-3.3-70b-versatile'}</div>
        <ol start={3}>
          <li>Restart the backend, then check again.</li>
        </ol>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <button className="btn btn--ghost" onClick={() => setKeyModal(false)}>
            Keep local engine
          </button>
          <button className="btn btn--primary" onClick={refreshStatus}>
            Check connection
          </button>
        </div>
      </div>
    </div>
  );
}
