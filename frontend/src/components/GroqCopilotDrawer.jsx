import { useEffect, useRef, useState } from 'react';
import { ArrowUp, BarChart3, Check, Copy, Info, RotateCcw, Sparkles, Square, Trash2, X } from 'lucide-react';
import { useCopilot } from '../context/CopilotContext';
import Markdown from './Markdown';

export const QUICK_PROMPTS = [
  'Identify SKUs at immediate risk of stockout within 14 days',
  'Why is delivery lag spiking during the Monsoon season?',
  'Simulate financial impact if raw material lead-time increases by 25%',
  'Suggest optimal regional inventory distribution across North and South',
];

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      className="btn btn--ghost btn--icon btn--sm"
      title="Copy"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
          setCopied(true);
          setTimeout(() => setCopied(false), 1400);
        } catch {
          /* clipboard unavailable */
        }
      }}
    >
      {copied ? <Check size={12} /> : <Copy size={12} />}
    </button>
  );
}

function Message({ msg, onRetry }) {
  if (msg.role === 'user') {
    return (
      <div className="msg msg--user">
        {msg.chart && (
          <span className="msg__context">
            <BarChart3 size={11} />
            {msg.chart}
          </span>
        )}
        <div className="msg__bubble">{msg.content}</div>
      </div>
    );
  }

  return (
    <div className="msg">
      <div className="msg__meta">
        <span className={`dot ${msg.pending ? 'dot--live' : msg.source === 'groq' ? 'dot--healthy' : 'dot--warning'}`} />
        <span>{msg.source === 'groq' ? `Groq · ${msg.model}` : msg.source === 'engine' ? 'Local analytics engine' : 'Connecting'}</span>
        {!msg.pending && msg.content && (
          <div className="msg__actions">
            <CopyButton text={msg.content} />
            {onRetry && (
              <button className="btn btn--ghost btn--icon btn--sm" title="Ask again" onClick={onRetry}>
                <RotateCcw size={12} />
              </button>
            )}
          </div>
        )}
      </div>
      {msg.pending && !msg.content ? (
        <div className="thinking">
          <span className="dot dot--live" />
          Reasoning over your data…
        </div>
      ) : (
        <div className={!msg.done && !msg.error ? 'caret' : ''}>
          <Markdown source={msg.content} />
        </div>
      )}
      {msg.error && (
        <p className="engine-note" style={{ borderColor: 'rgba(239,68,68,.3)', background: 'rgba(239,68,68,.06)' }}>
          {msg.error}
        </p>
      )}
    </div>
  );
}

export default function GroqCopilotDrawer({ hasData }) {
  const { open, setOpen, messages, streaming, ask, stop, clear, status, setKeyModal } = useCopilot();
  const [input, setInput] = useState('');
  const bodyRef = useRef(null);
  const inputRef = useRef(null);
  const stick = useRef(true);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 60);
  }, [open]);

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && open && setOpen(false);
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, setOpen]);

  useEffect(() => {
    const el = bodyRef.current;
    if (el && stick.current) el.scrollTop = el.scrollHeight;
  }, [messages]);

  useEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 140)}px`;
  }, [input]);

  if (!open) return null;

  const submit = (text = input) => {
    if (!text.trim() || !hasData) return;
    stick.current = true;
    ask(text);
    setInput('');
  };

  const lastUserFor = (index) => {
    for (let i = index - 1; i >= 0; i -= 1) if (messages[i].role === 'user') return messages[i];
    return null;
  };

  return (
    <>
      <div className="drawer-scrim" onClick={() => setOpen(false)} />
      <aside className="drawer" role="dialog" aria-label="AI Copilot">
        <header className="drawer__head">
          <div className="drawer__title">
            <Sparkles size={15} />
            Copilot
          </div>
          <button className="pill" style={{ cursor: 'pointer' }} onClick={() => setKeyModal(true)} title="Engine settings">
            <span className={`dot ${status.enabled ? 'dot--healthy' : 'dot--warning'}`} />
            <span className="mono">{status.enabled ? status.model : 'local engine'}</span>
          </button>
          <div className="drawer__head-actions">
            {messages.length > 0 && (
              <button className="btn btn--ghost btn--icon" onClick={clear} title="Clear conversation" aria-label="Clear conversation">
                <Trash2 size={14} />
              </button>
            )}
            <button className="btn btn--ghost btn--icon" onClick={() => setOpen(false)} title="Close (Esc)" aria-label="Close copilot">
              <X size={15} />
            </button>
          </div>
        </header>

        <div
          className="drawer__body"
          ref={bodyRef}
          onScroll={(e) => {
            const el = e.currentTarget;
            stick.current = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
          }}
        >
          {!status.enabled && status.loaded && (
            <div className="engine-note">
              <Info size={14} />
              <span>
                No Groq key configured, so answers come from the local analytics engine.{' '}
                <button onClick={() => setKeyModal(true)}>Connect Groq</button>
              </span>
            </div>
          )}

          {messages.length === 0 ? (
            <div style={{ display: 'grid', gap: 12 }}>
              <div>
                <p className="eyebrow">Ask about your supply chain</p>
                <p className="secondary" style={{ marginTop: 4, fontSize: 13 }}>
                  Answers use the current filters and cite exact figures from the loaded dataset.
                </p>
              </div>
              <div className="chips">
                {QUICK_PROMPTS.map((p) => (
                  <button key={p} className="chip" onClick={() => submit(p)} disabled={!hasData}>
                    {p}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((m, i) => (
              <Message
                key={m.id}
                msg={m}
                onRetry={m.role === 'assistant' && !streaming ? () => { const u = lastUserFor(i); if (u) ask(u.content); } : null}
              />
            ))
          )}
        </div>

        <footer className="drawer__foot">
          {messages.length > 0 && !streaming && (
            <div className="chips" style={{ flexWrap: 'nowrap', overflowX: 'auto' }}>
              {QUICK_PROMPTS.map((p) => (
                <button key={p} className="chip" style={{ whiteSpace: 'nowrap' }} onClick={() => submit(p)}>
                  {p}
                </button>
              ))}
            </div>
          )}
          <div className="composer">
            <textarea
              ref={inputRef}
              rows={1}
              value={input}
              placeholder={hasData ? 'Ask about stockouts, lead times, scenarios…' : 'Load a dataset first'}
              disabled={!hasData}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  submit();
                }
              }}
            />
            {streaming ? (
              <button className="btn btn--icon" onClick={stop} title="Stop" aria-label="Stop generating">
                <Square size={12} fill="currentColor" />
              </button>
            ) : (
              <button className="btn btn--primary btn--icon" onClick={() => submit()} disabled={!input.trim() || !hasData} aria-label="Send">
                <ArrowUp size={15} />
              </button>
            )}
          </div>
          <div className="composer__hint">
            <span>Enter to send · Shift+Enter for newline</span>
            <span>Esc to close</span>
          </div>
        </footer>
      </aside>
    </>
  );
}
