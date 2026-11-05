import { useRef, useState } from 'preact/hooks';
import { addStandardVideo, deleteStandard, listPresets, listStandards, Preset, saveStandard, Standard } from '../../state/catalog';
import { Icon } from '../controls';
import { SectionHead, TiltCard, useCatalog, useConfirm } from './common';

export function StandardsSection() {
  const [standards] = useCatalog<Standard[]>(listStandards, []);
  const [presets] = useCatalog<Preset[]>(listPresets, []);
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState('');
  const [notes, setNotes] = useState('');
  const [url, setUrl] = useState('');
  const [scope, setScope] = useState<string[]>([]);
  const [confirm, setConfirm] = useConfirm();
  const ref = useRef<HTMLInputElement>(null);
  const user = standards.filter(s => s.kind === 'video');
  const builtIn = standards.filter(s => s.kind === 'benchmark');
  const add = async () => {
    if (!file) return;
    await addStandardVideo(file, { name: name.trim() || undefined, notes, url: url.trim() || undefined, scope: scope.length ? scope : 'general' });
    setFile(null); setName(''); setNotes(''); setUrl(''); setScope([]);
  };
  const scopeLabel = (s: Standard) => s.scope === 'general' ? 'All edits' : presets.filter(p => (s.scope as string[]).includes(p.id)).map(p => p.name).join(', ') || 'No preset';
  return (
    <div class="hs">
      <SectionHead eyebrow="Standards" title="The bar every edit must clear" text="Add TikTok edits you think are excellent. The studio measures their pacing (cuts per second, shot length, cuts on the beat) and shows Opus their frames and your notes, for all edits or for chosen presets." />
      <div class="glass stdadd">
        <input ref={ref} type="file" hidden accept="video/*,.mov" onChange={e => { const f = (e.target as HTMLInputElement).files?.[0]; if (f) { setFile(f); if (!name) setName(f.name.replace(/\.[^.]+$/, '')); } (e.target as HTMLInputElement).value = ''; }} />
        <button type="button" class="cdrop-btn" onClick={() => ref.current?.click()}>{Icon.upload}<span>{file ? file.name : 'Choose a reference edit (video file)'}</span></button>
        <div class="fld fld-wide"><label class="fld-l" for="sd-name">Name</label><input id="sd-name" type="text" value={name} onInput={e => setName((e.target as HTMLInputElement).value)} placeholder="e.g. Trinity edit by @someone" /></div>
        <div class="fld fld-wide"><label class="fld-l" for="sd-url">Link</label><input id="sd-url" type="text" value={url} onInput={e => setUrl((e.target as HTMLInputElement).value)} placeholder="TikTok link (for your reference)" /></div>
        <label class="fld-l" for="sd-notes">What makes it a standard</label>
        <textarea id="sd-notes" class="ta" rows={3} value={notes} onInput={e => setNotes((e.target as HTMLTextAreaElement).value)} placeholder="e.g. the transitions hit every snare, the text acts out the lyric, the loop is invisible." />
        <span class="fld-l">Applies to</span>
        <div class="chips-row">
          <button type="button" class={`chipbtn${!scope.length ? ' is-on' : ''}`} onClick={() => setScope([])}>All edits</button>
          {presets.map(p => { const on = scope.includes(p.id); return <button type="button" class={`chipbtn${on ? ' is-on' : ''}`} onClick={() => setScope(on ? scope.filter(x => x !== p.id) : [...scope, p.id])}>{p.name}</button>; })}
        </div>
        <div class="row-end"><button type="button" class="cta cta-red" disabled={!file} onClick={() => void add()}>{Icon.plus}<span>Add standard</span></button></div>
      </div>
      {user.length > 0 && <h2 class="hs-sub">Your reference edits</h2>}
      <div class="sgrid">
        {user.map((s, i) => (
          <TiltCard class="scard" i={i}>
            <div class="scard-img">{s.poster ? <img src={s.poster} alt="" /> : <span class="recent-ph">{Icon.media}</span>}{s.state === 'processing' && <span class="litem-prog"><i style={{ width: `${Math.round((s.progress || 0) * 100)}%` }} /><em>Measuring…</em></span>}</div>
            <div class="scard-b">
              <div class="scard-n">{s.name}</div>
              <div class="muted">{scopeLabel(s)}</div>
              {s.profile && <dl class="sprof"><dt>Length</dt><dd>{s.profile.duration.toFixed(1)} s</dd><dt>Cuts</dt><dd>{s.profile.cuts} ({s.profile.cutsPerSec.toFixed(2)}/s)</dd><dt>Avg shot</dt><dd>{s.profile.avgShot.toFixed(2)} s</dd>{s.profile.bpm ? <><dt>Tempo</dt><dd>{s.profile.bpm} BPM</dd></> : null}{s.profile.onBeat !== null ? <><dt>On the beat</dt><dd>{Math.round(s.profile.onBeat * 100)}% of cuts</dd></> : null}</dl>}
              <textarea class="ta" rows={2} value={s.notes} aria-label="Notes" onChange={e => void saveStandard({ ...s, notes: (e.target as HTMLTextAreaElement).value })} />
              <div class="row-end">{confirm === s.id ? <button type="button" class="chipbtn danger" onClick={() => { setConfirm(null); void deleteStandard(s.id); }}>Confirm delete</button> : <button type="button" class="chipbtn" onClick={() => setConfirm(s.id)}>Delete</button>}</div>
            </div>
          </TiltCard>
        ))}
      </div>
      <h2 class="hs-sub">Your approved benchmarks</h2>
      <div class="bgrid">
        {builtIn.map((s, i) => (
          <TiltCard class="bcard" i={i}>
            <div class="bcard-n">{s.name}</div>
            <p class="bcard-t">{s.notes}</p>
            {s.quote && <blockquote>“{s.quote}”</blockquote>}
          </TiltCard>
        ))}
      </div>
    </div>
  );
}
