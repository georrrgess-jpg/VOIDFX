// The revision stage. The owner writes the instructions Opus follows in the next round: their own
// words, the critic points they choose to pass on, and how the round runs. Rounds run in the
// background, so this screen closes as soon as the round starts.
import { useEffect, useMemo, useRef, useState } from 'preact/hooks';
import { issueLine } from '../../ai/critic';
import { EFFORTS } from '../../ai/director';
import { activeJobFor, enqueue } from '../../ai/jobs';
import { listPresets, Preset } from '../../state/catalog';
import { getRecord, openProject, ProjectRecord, updateRecord } from '../../state/projects';
import { store, useStore } from '../../state/store';
import { Effort } from '../../state/types';
import { Icon } from '../controls';
import { useCatalog } from '../home/common';
import { sendToCritic } from './actions';
import { CritiqueView } from './CritiqueView';

const QUICK = [
  'Keep everything that already works.',
  'Re-cut every shot on the beat grid.',
  'Make the first second hit harder.',
  'Build a bigger set piece on the drop.',
  'Add motion: speed ramps and camera hits on every montage shot.',
  'Swap the weakest shots for stronger moments.',
  'Make the text cleaner and better timed.',
  'Make the loop seamless.',
];

function AfterRound(props: { critic: boolean; setCritic: (v: boolean) => void; auto: number; setAuto: (v: number) => void }) {
  return (
    <div class="after">
      <label class={`toggle${props.critic ? ' on' : ''}`}>
        <input type="checkbox" checked={props.critic} onChange={() => { props.setCritic(!props.critic); if (props.critic) props.setAuto(0); }} />
        <span class="toggle-t" aria-hidden="true" />
        <span><b>Send to the critic when it's done</b><em>A harsh review with a write-up you can pass into the next round.</em></span>
      </label>
      <div class={`after-auto${props.critic ? '' : ' off'}`}>
        <span class="fld-l">Then</span>
        <div class="seg seg-auto" role="radiogroup" aria-label="Automatic rounds">
          {[[0, 'Wait for my instructions'], [1, 'Revise once on its own'], [2, 'Revise twice on its own']].map(([v, l]) => (
            <button type="button" role="radio" aria-checked={props.auto === v} class={props.auto === v ? 'is-on' : ''} disabled={!props.critic} onClick={() => props.setAuto(v as number)}>{l}</button>
          ))}
        </div>
      </div>
    </div>
  );
}

export function EffortSeg({ value, onChange }: { value: Effort; onChange: (e: Effort) => void }) {
  return (
    <div class="effort-pick">
      <div class="seg seg-effort" role="radiogroup" aria-label="Effort">
        {(Object.keys(EFFORTS) as Effort[]).map(k => <button type="button" role="radio" aria-checked={value === k} class={value === k ? 'is-on' : ''} onClick={() => onChange(k)} title={EFFORTS[k].hint}>{EFFORTS[k].label}</button>)}
      </div>
      <p class="muted">{EFFORTS[value].hint}</p>
    </div>
  );
}

export function Composer() {
  const c = useStore(s => s.composer);
  const rev = useStore(s => s.catalogRev);
  const jobs = useStore(s => s.jobs);
  const [rec, setRec] = useState<ProjectRecord | null>(null);
  const [presets] = useCatalog<Preset[]>(listPresets, []);
  const [text, setText] = useState('');
  const [picked, setPicked] = useState<Set<number>>(new Set());
  const [briefOn, setBriefOn] = useState(true);
  const [effort, setEffort] = useState<Effort>(store.state.director.effort);
  const [critic, setCritic] = useState(true);
  const [auto, setAuto] = useState(0);
  const [presetId, setPresetId] = useState(store.state.director.presetId);
  const [lyrics, setLyrics] = useState('');
  const [useDb, setUseDb] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [busy, setBusy] = useState(false);
  const loadedFor = useRef<string | null>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!c) { loadedFor.current = null; return; }
    void getRecord(c.projectId).then(r => {
      if (!r) return;
      setRec(r);
      if (loadedFor.current === c.projectId) return;
      loadedFor.current = c.projectId;
      const rs = r.rounds || [];
      const last = rs[rs.length - 1];
      const crit = last?.critique;
      setText(r.draft || '');
      setPicked(new Set(crit ? crit.issues.map((x, i) => (x.severity !== 'minor' ? i : -1)).filter(i => i >= 0) : []));
      setBriefOn(true);
      setEffort(last?.effort || (r.director?.effort as Effort) || store.state.director.effort);
      setPresetId(last?.presetId || r.director?.presetId || r.presetId || store.state.director.presetId);
      setTimeout(() => taRef.current?.focus(), 80);
    });
  }, [c?.projectId, rev, jobs.length]);

  // keep the unsent instructions with the project
  useEffect(() => {
    if (!c || loadedFor.current !== c.projectId) return;
    const t = setTimeout(() => void updateRecord(c.projectId, r => { if (r.draft === text) return false; r.draft = text; }), 600);
    return () => clearTimeout(t);
  }, [text]);

  useEffect(() => {
    if (!c) return;
    const esc = (e: KeyboardEvent) => { if (e.key === 'Escape') store.set({ composer: null }); };
    window.addEventListener('keydown', esc);
    return () => window.removeEventListener('keydown', esc);
  }, [!!c]);

  const rounds = rec?.rounds || [];
  const last = rounds[rounds.length - 1];
  const crit = last?.critique;
  const mode = c?.mode === 'create' && !rounds.length && !rec?.clips ? 'create' : 'revise';
  const nextRound = mode === 'create' ? 1 : (last?.n || 0) + 1;
  const running = c ? activeJobFor(c.projectId) : undefined;
  const criticRunning = running?.kind === 'critique';

  const fromCritic = useMemo(() => {
    if (!crit) return [] as string[];
    const lines = crit.issues.filter((_, i) => picked.has(i)).map(issueLine);
    return briefOn && crit.brief ? [`The critic's write-up: ${crit.brief}`, ...lines] : lines;
  }, [crit, picked, briefOn]);

  if (!c || !rec) return null;
  const close = () => store.set({ composer: null });
  const preset = presets.find(p => p.id === presetId);
  const hasMedia = (rec.media || []).some(m => m.status !== 'error');
  const canGo = !busy && !running && (mode === 'create' ? hasMedia || useDb : !!(text.trim() || fromCritic.length));

  const start = async () => {
    if (!canGo) return;
    setBusy(true);
    try {
      const follow = { critic, autoRounds: critic ? auto : 0 };
      const job = mode === 'create'
        ? await enqueue({ kind: 'create', projectId: rec.id, effort, presetId, request: { notes: text, lyrics, library: { mode: useDb ? 'auto' : 'none', ids: [] } }, follow })
        : await enqueue({ kind: 'revise', projectId: rec.id, effort, presetId, brief: text.trim(), fromCritic, follow });
      if (job) {
        await updateRecord(rec.id, r => { r.draft = ''; });
        store.set({ composer: null });
        store.toast(`Round ${job.round} of “${rec.name}” is running in the background. You can keep working.`, 'ok', 6000);
      }
    } finally {
      setBusy(false);
    }
  };

  const preview = mode === 'revise' ? [
    `ROUND ${nextRound} INSTRUCTIONS FROM THE OWNER`,
    text.trim() || '(no extra words: work through the critic\'s points)',
    fromCritic.length ? `THE CRITIC'S POINTS THE OWNER PASSED ON (fix every one)\n${fromCritic.map((x, i) => `${i + 1}. ${x}`).join('\n')}` : '',
    'Plus: the house rules, the standards, the current timeline, frames rendered from the edit, contact sheets of the media and the checkpoint.',
  ].filter(Boolean).join('\n\n') : '';

  return (
    <div class="modal-bg comp-bg" onClick={e => { if (e.target === e.currentTarget) close(); }}>
      <div class="comp" role="dialog" aria-modal="true" aria-labelledby="comp-title">
        <header class="comp-h">
          <div class="comp-round" aria-hidden="true"><span>Round</span><b>{nextRound}</b></div>
          <div class="comp-ht">
            <p class="hs-eyebrow">{mode === 'create' ? 'The build' : 'The revision stage'} · {rec.name}</p>
            <h2 id="comp-title">{mode === 'create' ? 'Brief Opus for the first round' : `You're writing the instructions for round ${nextRound}`}</h2>
            <p class="muted">{mode === 'create' ? 'Opus builds the edit from this project\'s media.' : 'Opus reads exactly what you set here, on top of the house rules and the current edit.'} The round runs in the background: close this and keep working.</p>
          </div>
          <button type="button" class="btn btn-ghost comp-x" onClick={close} aria-label="Close">{Icon.close}</button>
        </header>

        <div class={`comp-body${mode === 'revise' ? ' two' : ' one'}`}>
          {mode === 'revise' && (
            <section class="comp-left" aria-label="The critic">
              {crit ? (
                <CritiqueView crit={crit} projectId={rec.id} picked={picked} briefOn={briefOn} onBrief={setBriefOn}
                  onPick={i => { const n = new Set(picked); if (n.has(i)) n.delete(i); else n.add(i); setPicked(n); }} />
              ) : (
                <div class="nocrit">
                  <span class="nocrit-ic" aria-hidden="true">{Icon.critic}</span>
                  <h3>{criticRunning ? 'The critic is watching this round…' : `No critique of round ${last?.n || 1} yet`}</h3>
                  <p class="muted">The critic judges the edit against your standards and the best TikTok edits of its kind, then writes up what to fix. Its points land here as checkboxes for this round.</p>
                  {!criticRunning && <button type="button" class="cta cta-ghost" disabled={!!running || !rec.clips} onClick={() => void sendToCritic(rec.id)}>{Icon.critic}<span>Send round {last?.n || 1} to the critic</span></button>}
                  <p class="muted small">Or skip it and write your own instructions.</p>
                </div>
              )}
            </section>
          )}

          <section class="comp-right" aria-label="Your instructions">
            {mode === 'create' && (
              <div class="cblock">
                <h3><span class="cnum">1</span>Preset</h3>
                <select value={presetId} onChange={e => { const id = (e.target as HTMLSelectElement).value; setPresetId(id); const p = presets.find(x => x.id === id); if (p) setEffort(p.effort); }}>
                  {presets.map(p => <option value={p.id}>{p.name}</option>)}
                </select>
                {preset && <p class="muted">{preset.description}</p>}
              </div>
            )}
            <div class="cblock">
              <h3><span class="cnum">{mode === 'create' ? 2 : 1}</span>{mode === 'create' ? 'What makes this edit unique' : 'Your instructions'}</h3>
              <textarea ref={taRef} class="ta big" rows={7} value={text} onInput={e => setText((e.target as HTMLTextAreaElement).value)}
                placeholder={mode === 'create' ? 'The concept, the song section, the moments you want, shots to use or avoid.' : 'What should change in this round? Be as specific as you like: "open on the bathtub shot", "the drop needs a bigger set piece", "cut the second caption".'} />
              <div class="quick">
                {QUICK.filter(q => mode === 'revise' || !q.startsWith('Keep')).map(q => (
                  <button type="button" class="chipbtn" disabled={text.includes(q)} onClick={() => setText(t => (t.trim() ? `${t.trim()}\n${q}` : q))}>+ {q.replace(/\.$/, '')}</button>
                ))}
              </div>
              {mode === 'create' && (
                <>
                  <textarea class="ta" rows={3} value={lyrics} onInput={e => setLyrics((e.target as HTMLTextAreaElement).value)} placeholder="Lyrics for captions (optional)" aria-label="Lyrics" />
                  <label class={`toggle${useDb ? ' on' : ''}`}><input type="checkbox" checked={useDb} onChange={() => setUseDb(!useDb)} /><span class="toggle-t" aria-hidden="true" /><span><b>Let Opus add material from the database</b><em>{hasMedia ? 'Opus picks extra packs, clips or the song from the database.' : 'This project has no media yet: import files in the editor, or turn this on.'}</em></span></label>
                </>
              )}
            </div>
            {mode === 'revise' && (
              <div class="cblock">
                <h3><span class="cnum">2</span>From the critic</h3>
                <p class="comp-count">{crit ? <><b>{picked.size}</b> of {crit.issues.length} points{briefOn && crit.brief ? ' + the write-up' : ''} go into this round.</> : 'No critique to pass on.'}</p>
                {crit && <div class="quick"><button type="button" class="chipbtn" onClick={() => setPicked(new Set(crit.issues.map((_, i) => i)))}>All</button><button type="button" class="chipbtn" onClick={() => setPicked(new Set(crit.issues.map((x, i) => (x.severity !== 'minor' ? i : -1)).filter(i => i >= 0)))}>Critical and major</button><button type="button" class="chipbtn" onClick={() => setPicked(new Set())}>None</button></div>}
              </div>
            )}
            <div class="cblock">
              <h3><span class="cnum">{mode === 'create' ? 3 : 3}</span>How it runs</h3>
              <EffortSeg value={effort} onChange={setEffort} />
              <AfterRound critic={critic} setCritic={setCritic} auto={auto} setAuto={setAuto} />
            </div>
            {mode === 'revise' && (
              <div class="cblock">
                <button type="button" class="linkbtn" aria-expanded={showPreview} onClick={() => setShowPreview(!showPreview)}>{showPreview ? '▾' : '▸'} What Opus will receive</button>
                {showPreview && <pre class="comp-preview">{preview}</pre>}
              </div>
            )}
            <div class="comp-go">
              {running && <p class="note warn">{running.kind === 'critique' ? 'The critic is still reviewing this project.' : 'Opus is already working on this project.'} Start the next round when it finishes.</p>}
              <button type="button" class="cta cta-opus cta-xl" disabled={!canGo} onClick={() => void start()}>{Icon.spark}<span>{busy ? 'Starting…' : `Start round ${nextRound} in the background`}</span></button>
              {!canGo && !running && mode === 'revise' && <p class="muted small">Write an instruction or pick at least one critic point.</p>}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

/** The critique on its own (from a notification or a menu). */
export function CritiqueModal() {
  const c = useStore(s => s.critique);
  const rev = useStore(s => s.catalogRev);
  const [rec, setRec] = useState<ProjectRecord | null>(null);
  useEffect(() => { if (c) void getRecord(c.projectId).then(r => setRec(r || null)); }, [c?.projectId, c?.round, rev]);
  useEffect(() => {
    if (!c) return;
    const esc = (e: KeyboardEvent) => { if (e.key === 'Escape') store.set({ critique: null }); };
    window.addEventListener('keydown', esc);
    return () => window.removeEventListener('keydown', esc);
  }, [!!c]);
  if (!c || !rec) return null;
  const round = (rec.rounds || []).find(r => r.n === c.round);
  const crit = round?.critique;
  const close = () => store.set({ critique: null });
  return (
    <div class="modal-bg comp-bg" onClick={e => { if (e.target === e.currentTarget) close(); }}>
      <div class="comp crit-modal" role="dialog" aria-modal="true" aria-label="Critique">
        <header class="comp-h">
          <div class="comp-round crit-badge" aria-hidden="true"><span>Critic</span><b>{Icon.critic}</b></div>
          <div class="comp-ht">
            <p class="hs-eyebrow">The critic · {rec.name}</p>
            <h2>Round {c.round} assessment</h2>
          </div>
          <button type="button" class="btn btn-ghost comp-x" onClick={close} aria-label="Close">{Icon.close}</button>
        </header>
        <div class="comp-body one">
          {crit ? <CritiqueView crit={crit} projectId={rec.id} /> : <p class="muted">This round has no critique yet.</p>}
        </div>
        <footer class="comp-foot">
          <button type="button" class="cta cta-ghost" onClick={() => { close(); void openProject(rec.id); }}>{Icon.play}<span>Open the edit</span></button>
          <button type="button" class="cta cta-opus" onClick={() => store.set({ critique: null, composer: { projectId: rec.id, mode: 'revise' } })}>{Icon.pen}<span>Write round {c.round + 1} with this</span></button>
        </footer>
      </div>
    </div>
  );
}
