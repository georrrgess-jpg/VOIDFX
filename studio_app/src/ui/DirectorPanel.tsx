import { useEffect, useRef, useState } from 'preact/hooks';
import { createEdit, EFFORTS, MODEL, refineEdit, resetConversation, stopDirector } from '../ai/director';
import { Effort, store, useStore } from '../state/store';
import { Btn, Icon } from './controls';
import { listPresets, Preset } from '../state/catalog';
import { useCatalog } from './home/common';

export function DirectorPanel() {
  const d = useStore(s => s.director);
  const clips = useStore(s => s.project.clips.length);
  const ready = useStore(s => s.mediaOrder.filter(id => s.media[id]?.status === 'ready').length);
  const [chat, setChat] = useState('');
  const [showKnow, setShowKnow] = useState(false);
  const logRef = useRef<HTMLDivElement>(null);
  const [, tick] = useState(0);
  useEffect(() => { logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' }); }, [d.messages.length, d.steps]);
  useEffect(() => {
    if (!d.running) return;
    const t = setInterval(() => tick(x => x + 1), 1000);
    return () => clearInterval(t);
  }, [d.running]);

  const [presets] = useCatalog<Preset[]>(listPresets, []);
  const preset = presets.find(p => p.id === d.presetId);
  const effortKeys = Object.keys(EFFORTS) as Effort[];
  const hasConversation = d.messages.some(m => m.role === 'opus');
  const disabled = d.available !== 'yes';
  return (
    <div class={`dir${d.running ? ' is-running' : ''}`}>
      <header class="dir-h">
        <div class="dir-title">
          <span class="dir-mark" aria-hidden="true">{Icon.spark}</span>
          <div>
            <h2>Opus Director</h2>
            <p class="dir-model" title="The model Opus calls are sent to">{d.lastModel ? `answered by ${d.lastModel}` : MODEL}</p>
          </div>
        </div>
        {d.messages.length > 0 && !d.running && <Btn title="Clear the conversation" onClick={resetConversation}>Clear</Btn>}
      </header>

      {d.available === 'no' && <p class="note warn">{d.unavailableReason || 'Opus is not available in this view.'} You can still edit by hand.</p>}
      {d.available === 'checking' && <p class="note">Connecting to Opus…</p>}

      <div class="dir-log" ref={logRef} aria-live="polite">
        {!d.messages.length && !d.running && (
          <div class="dir-empty">
            <p class="dir-empty-t">Opus builds the whole edit.</p>
            <ol>
              <li>Import your clips and music.</li>
              <li>Say what you want, or leave it to Opus.</li>
              <li>Press <b>Create edit</b>. Every change lands on the timeline as one undo step you can tweak by hand.</li>
            </ol>
          </div>
        )}
        {d.messages.map(m => (
          <div class={`msg m-${m.role}`}>
            {m.role === 'opus' && <span class="msg-who">Opus</span>}
            <p>{m.text}</p>
            {(m.applied !== undefined || m.undoTo !== undefined) && (
              <div class="msg-foot">
                {m.applied !== undefined && <span>{m.applied} change{m.applied === 1 ? '' : 's'} applied</span>}
                {m.model && <span class="mono">{m.model}</span>}
                {m.undoTo !== undefined && !d.running && <button type="button" class="linkbtn" onClick={() => { store.undoTo(m.undoTo!); store.toast('Reverted to before this Opus edit.'); }}>Undo this edit</button>}
              </div>
            )}
            {m.issues && m.issues.length > 0 && (
              <details class="msg-issues"><summary>{m.issues.length} operation{m.issues.length > 1 ? 's were' : ' was'} adjusted</summary><ul>{m.issues.map(x => <li>{x}</li>)}</ul></details>
            )}
          </div>
        ))}
        {d.steps.length > 0 && (d.running || d.steps.some(s => s.state === 'error')) && (
          <ol class="steps">
            {d.steps.map(s => {
              const secs = s.t0 ? Math.round(((s.t1 || Date.now()) - s.t0) / 1000) : 0;
              return (
                <li class={`step st-${s.state}`}>
                  <span class="step-dot" aria-hidden="true" />
                  <span class="step-l">{s.label}</span>
                  <span class="step-d">{s.detail}{s.state === 'run' && secs > 1 ? ` · ${secs}s` : ''}</span>
                </li>
              );
            })}
          </ol>
        )}
      </div>

      <div class="dir-form">
        <div class="fld fld-wide">
          <label class="fld-l" for="dir-preset">Preset</label>
          <select id="dir-preset" value={d.presetId} disabled={d.running} onChange={e => { const id = (e.target as HTMLSelectElement).value; const pr = presets.find(x => x.id === id); store.setDirector({ presetId: id, ...(pr ? { effort: pr.effort } : {}) }); }}>
            {presets.map(p => <option value={p.id}>{p.name}</option>)}
          </select>
          {preset && <p class="hint">{preset.description}</p>}
        </div>
        {!hasConversation || d.running ? (
          <>
            <label class="fld-l" for="brief">What makes this edit unique</label>
            <textarea id="brief" class="ta" rows={4} value={d.brief} disabled={d.running}
              placeholder="Describe the edit: length, mood, story, the moments that matter. Leave empty and Opus decides."
              onInput={e => store.setDirector({ brief: (e.target as HTMLTextAreaElement).value })} />
          </>
        ) : (
          <>
            <label class="fld-l" for="chat">Ask Opus for a change</label>
            <textarea id="chat" class="ta" rows={3} value={chat} disabled={d.running}
              placeholder="e.g. tighten the opening, end on the strongest shot, move the title up"
              onInput={e => setChat((e.target as HTMLTextAreaElement).value)}
              onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey) && chat.trim()) { void refineEdit(chat); setChat(''); } }} />
          </>
        )}
        <div class="fld fld-wide">
          <span class="fld-l" id="effort-l">Effort</span>
          <div class="seg seg-effort" role="radiogroup" aria-labelledby="effort-l">
            {effortKeys.map(k => (
              <button type="button" role="radio" aria-checked={d.effort === k} class={d.effort === k ? 'is-on' : ''} title={EFFORTS[k].hint} disabled={d.running} onClick={() => store.setDirector({ effort: k })}>
                {EFFORTS[k].label}
              </button>
            ))}
          </div>
          <p class="hint">{EFFORTS[d.effort].hint}</p>
        </div>
        <div class="dir-actions">
          {d.running ? (
            <Btn kind="danger" class="grow" onClick={stopDirector}>{Icon.stop}<span>Stop</span></Btn>
          ) : hasConversation ? (
            <>
              <Btn kind="opus" class="grow" disabled={disabled || !chat.trim()} onClick={() => { void refineEdit(chat); setChat(''); }}>{Icon.spark}<span>Send</span></Btn>
              <Btn kind="solid" disabled={disabled || !ready} title="Build the edit again from scratch with the brief" onClick={() => { resetConversation(); }}>New brief</Btn>
            </>
          ) : (
            <Btn kind="opus" class="grow" disabled={disabled || !ready} onClick={() => void createEdit()}>{Icon.spark}<span>{clips ? 'Rebuild edit' : 'Create edit'}</span></Btn>
          )}
        </div>
        <button type="button" class="linkbtn know-t" onClick={() => setShowKnow(!showKnow)} aria-expanded={showKnow}>
          {showKnow ? '▾' : '▸'} {preset?.houseRules ? 'House rules on' : 'House rules off'} · your additions {d.knowledge.trim() ? `(${d.knowledge.trim().length} chars)` : '(none)'}
        </button>
        {showKnow && <p class="hint">Edit the house rules view, your additions, presets and standards from the main menu.</p>}
        <p class="dir-foot">Uses your Claude usage. Opus sees contact sheets and sound analysis of your media; it cannot hear audio.</p>
      </div>
    </div>
  );
}
