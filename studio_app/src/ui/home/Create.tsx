import { useMemo, useRef, useState } from 'preact/hooks';
import { parseLyrics } from '../../state/lyrics';
import { startAiEdit } from '../../ai/jobs';
import { detectKind, importFiles } from '../../media/library';
import { LibraryItem, listLibrary, listPresets, listStandards, Preset, Standard } from '../../state/catalog';
import { createProject } from '../../state/projects';
import { Effort, store, useStore } from '../../state/store';
import { fmtBytes } from '../../state/util';
import { Icon } from '../controls';
import { EffortSeg } from '../ai/Composer';
import { ActivityList } from '../ai/Activity';
import { fmtDur, SectionHead, useCatalog } from './common';

type Source = 'files' | 'library' | 'both';

export function CreateSection() {
  const [presets] = useCatalog<Preset[]>(listPresets, []);
  const [library] = useCatalog<LibraryItem[]>(listLibrary, []);
  const [standards] = useCatalog<Standard[]>(listStandards, []);
  const director = useStore(s => s.director);
  const [presetId, setPresetId] = useState(director.presetId);
  const [notes, setNotes] = useState('');
  const [lyrics, setLyrics] = useState('');
  const [showLyrics, setShowLyrics] = useState(false);
  const [title, setTitle] = useState('');
  const [source, setSource] = useState<Source>('files');
  const [files, setFiles] = useState<File[]>([]);
  const [libMode, setLibMode] = useState<'auto' | 'picked'>('auto');
  const [picked, setPicked] = useState<string[]>([]);
  const [tagFilter, setTagFilter] = useState('');
  const [effort, setEffort] = useState<Effort>(director.effort);
  const [stdOverride, setStdOverride] = useState<string[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [drag, setDrag] = useState(false);
  const [critic, setCritic] = useState(true);
  const [auto, setAuto] = useState(0);
  const [started, setStarted] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const preset = presets.find(p => p.id === presetId) || presets[0];
  const readyLib = library.filter(i => i.state === 'ready');
  const tags = [...new Set(readyLib.flatMap(i => i.tags))].sort();
  const libShown = readyLib.filter(i => !tagFilter || i.tags.includes(tagFilter));
  const defaultStd = preset ? standards.filter(s => preset.standards.includes(s.id) || (s.kind === 'video' && (s.scope === 'general' || (Array.isArray(s.scope) && s.scope.includes(preset.id))))).map(s => s.id) : [];
  const stdIds = stdOverride ?? defaultStd;
  const useFiles = source !== 'library', useLib = source !== 'files';
  const totalBytes = files.reduce((a, f) => a + f.size, 0);
  const canGo = !!preset && !busy && ((useFiles && files.length > 0) || (useLib && (libMode === 'auto' ? readyLib.length > 0 : picked.length > 0)));
  const opusOk = director.available === 'yes';

  const addFiles = (list: FileList | File[]) => {
    const ok = Array.from(list).filter(f => detectKind(f));
    if (ok.length < Array.from(list).length) store.toast('Some files were skipped: only video, audio and images can be used.');
    setFiles(prev => [...prev, ...ok.filter(f => !prev.some(p => p.name === f.name && p.size === f.size))]);
  };

  const go = async () => {
    if (!canGo || !preset) return;
    setBusy(true);
    try {
      const name = title.trim() || `${preset.name.replace(/^VOIDFX · /, '')} edit`;
      store.setDirector({ presetId: preset.id, effort });
      if (!opusOk) {
        // no Opus here: make the project with the files and open it for editing by hand
        await createProject({ name, aspect: preset.aspect, fps: preset.fps, presetId: preset.id });
        if (useFiles && files.length) await importFiles(files);
        store.toast('The project is ready with your files. Opus is not available in this view, so build the edit by hand.', 'info', 7000);
        return;
      }
      const job = await startAiEdit({
        name, presetId: preset.id, effort, files: useFiles ? files : [],
        request: { notes, lyrics, library: useLib ? { mode: libMode, ids: picked } : { mode: 'none', ids: [] }, standards: stdIds },
        follow: { critic, autoRounds: critic ? auto : 0 },
      });
      if (job) {
        setStarted(name);
        setFiles([]); setNotes(''); setLyrics(''); setTitle('');
        window.scrollTo?.({ top: 0, behavior: 'smooth' });
        document.querySelector('.home-main')?.scrollTo({ top: 0, behavior: 'smooth' });
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div class="hs create">
      <SectionHead eyebrow="AI Edit" title="Opus builds the edit" text="Pick a preset for the standing brief, add what makes this edit unique, and give Opus material: your own files, the database, or both." />
      {!opusOk && <p class="note warn glass-note">{director.unavailableReason || 'Opus is not connected in this view.'} You can still create the project with your files and edit by hand.</p>}
      {started && (
        <div class="started glass">
          <div class="started-h">
            <span class="started-ic" aria-hidden="true">{Icon.check}</span>
            <div><b>“{started}” is building in the background.</b><p class="muted">Leave this page, open other projects or start another edit. You'll get a notice when it's ready{critic ? ' and when the critic has reviewed it' : ''}.</p></div>
            <button type="button" class="btn btn-ghost" onClick={() => setStarted(null)} aria-label="Dismiss">{Icon.close}</button>
          </div>
          <ActivityList compact limit={3} />
        </div>
      )}

      <section class="cstep">
        <h2><span class="cstep-n">1</span>Preset</h2>
        <div class="preset-row">
          {presets.map(p => (
            <button type="button" class={`preset-card${p.id === presetId ? ' is-on' : ''}`} style={{ '--c': p.accent } as any} onClick={() => { setPresetId(p.id); setEffort(p.effort); setStdOverride(null); }} aria-pressed={p.id === presetId}>
              <span class="preset-dot" aria-hidden="true" />
              <span class="preset-name">{p.name}</span>
              <span class="preset-desc">{p.description || 'Custom preset'}</span>
              <span class="preset-meta">{p.houseRules ? 'House rules' : 'Open brief'} · {p.duration[0]}–{p.duration[1]} s · {p.fps} fps</span>
            </button>
          ))}
        </div>
      </section>

      <section class="cstep">
        <h2><span class="cstep-n">2</span>What makes this one unique</h2>
        <textarea id="c-notes" class="ta big" rows={4} value={notes} onInput={e => setNotes((e.target as HTMLTextAreaElement).value)}
          placeholder="The concept, the song section, moments you want, shots to use or avoid, the mood. e.g. 'Trinity season: the bathtub, the hammer; open on “Could it be him?”, drop on the second chorus.'" />
        <div class="row">
          <input id="c-title" class="search" type="text" value={title} onInput={e => setTitle((e.target as HTMLInputElement).value)} placeholder="Project name (optional)" aria-label="Project name" />
          <button type="button" class="linkbtn" onClick={() => setShowLyrics(!showLyrics)} aria-expanded={showLyrics}>{showLyrics ? '▾' : '▸'} Lyrics for captions</button>
        </div>
        {showLyrics && <>
          <textarea id="c-lyrics" class="ta" rows={4} value={lyrics} onInput={e => setLyrics((e.target as HTMLTextAreaElement).value)} placeholder={'Synced lyrics (LRC) put each caption on its sung time:\n[00:51.20] I could never be the one\n[00:54.80] you wanted me to be\nThe times must match your song file (a sped-up or slowed version needs its own).'} />
          {lyrics.trim() && <LyricsStatus text={lyrics} />}
        </>}
      </section>

      <section class="cstep">
        <h2><span class="cstep-n">3</span>Material</h2>
        <div class="seg seg-big" role="radiogroup" aria-label="Material">
          {([['files', 'My files'], ['library', 'Database'], ['both', 'Both']] as [Source, string][]).map(([v, l]) => (
            <button type="button" role="radio" aria-checked={source === v} class={source === v ? 'is-on' : ''} onClick={() => setSource(v)}>{l}</button>
          ))}
        </div>
        {useFiles && (
          <div class={`cdrop${drag ? ' is-drag' : ''}`}
            onDragOver={e => { e.preventDefault(); e.stopPropagation(); setDrag(true); }} onDragLeave={() => setDrag(false)}
            onDrop={e => { e.preventDefault(); e.stopPropagation(); setDrag(false); if (e.dataTransfer?.files.length) addFiles(e.dataTransfer.files); }}>
            <input ref={fileRef} type="file" multiple hidden accept="video/*,audio/*,image/*,.mov,.mkv,.m4a,.flac" onChange={e => { const f = (e.target as HTMLInputElement).files; if (f) addFiles(f); (e.target as HTMLInputElement).value = ''; }} />
            <button type="button" class="cdrop-btn" onClick={() => fileRef.current?.click()}>{Icon.upload}<span>Attach clips, scene packs and the song</span></button>
            <p class="muted">Any size: files of hundreds of megabytes or several gigabytes are read from disk as needed and kept in this browser for the project.</p>
            {files.length > 0 && (
              <ul class="flist">
                {files.map(f => (
                  <li><span class={`fkind k-${detectKind(f)}`}>{detectKind(f)}</span><span class="fname">{f.name}</span><span class="muted">{fmtBytes(f.size)}</span>
                    <button type="button" class="th-b" title="Remove" onClick={() => setFiles(files.filter(x => x !== f))}>{Icon.close}</button></li>
                ))}
                <li class="flist-total"><span>{files.length} file{files.length > 1 ? 's' : ''}</span><span class="muted">{fmtBytes(totalBytes)}</span></li>
              </ul>
            )}
          </div>
        )}
        {useLib && (
          <div class="clib">
            {!readyLib.length ? (
              <p class="muted">The database is empty. <button type="button" class="linkbtn" onClick={() => store.set({ homeTab: 'library' })}>Add scene packs, clips and music</button></p>
            ) : (
              <>
                <div class="seg" role="radiogroup" aria-label="Database use">
                  <button type="button" role="radio" aria-checked={libMode === 'auto'} class={libMode === 'auto' ? 'is-on' : ''} onClick={() => setLibMode('auto')}>Let Opus choose</button>
                  <button type="button" role="radio" aria-checked={libMode === 'picked'} class={libMode === 'picked' ? 'is-on' : ''} onClick={() => setLibMode('picked')}>I'll pick</button>
                </div>
                <p class="muted">{libMode === 'auto' ? `Opus picks the song and the strongest packs or clips from ${readyLib.length} items${preset?.libraryTags.length ? `, favouring ${preset.libraryTags.join(', ')}` : ''}.` : `${picked.length} picked`}</p>
                {libMode === 'picked' && (
                  <>
                    {tags.length > 0 && <div class="chips-row">{['', ...tags].map(t => <button type="button" class={`chipbtn${tagFilter === t ? ' is-on' : ''}`} onClick={() => setTagFilter(t)}>{t || 'All'}</button>)}</div>}
                    <div class="lpick">
                      {libShown.map(i => {
                        const on = picked.includes(i.id);
                        return (
                          <button type="button" class={`lpick-i${on ? ' is-on' : ''}`} aria-pressed={on} onClick={() => setPicked(on ? picked.filter(x => x !== i.id) : [...picked, i.id])}>
                            <span class="lpick-img">{i.poster ? <img src={i.poster} alt="" /> : <span class="recent-ph">{i.kind === 'audio' ? Icon.vol : Icon.media}</span>}</span>
                            <span class="lpick-n">{i.name}</span>
                            <span class="muted">{i.role} · {fmtDur(i.duration)}{i.bpm ? ` · ${Math.round(i.bpm)} BPM` : ''}</span>
                          </button>
                        );
                      })}
                    </div>
                  </>
                )}
              </>
            )}
          </div>
        )}
      </section>

      <section class="cstep">
        <h2><span class="cstep-n">4</span>Standards to beat</h2>
        <div class="chips-row">
          {standards.map(s => {
            const on = stdIds.includes(s.id);
            return <button type="button" class={`chipbtn${on ? ' is-on' : ''}`} aria-pressed={on} onClick={() => setStdOverride(on ? stdIds.filter(x => x !== s.id) : [...stdIds, s.id])} title={s.notes}>{s.kind === 'video' ? '▶ ' : ''}{s.name}</button>;
          })}
        </div>
      </section>

      <section class="cstep">
        <h2><span class="cstep-n">5</span>After it's built</h2>
        <div class="after">
          <label class={`toggle${critic ? ' on' : ''}`}>
            <input type="checkbox" checked={critic} onChange={() => { setCritic(!critic); if (critic) setAuto(0); }} />
            <span class="toggle-t" aria-hidden="true" />
            <span><b>Send it to the critic automatically</b><em>A harsh review against your standards and the best TikTok edits, with a write-up for the next round.</em></span>
          </label>
          <div class={`after-auto${critic ? '' : ' off'}`}>
            <span class="fld-l">Then</span>
            <div class="seg seg-auto" role="radiogroup" aria-label="Automatic rounds">
              {[[0, 'Wait for my instructions'], [1, 'Revise once on its own'], [2, 'Revise twice on its own']].map(([v, l]) => (
                <button type="button" role="radio" aria-checked={auto === v} class={auto === v ? 'is-on' : ''} disabled={!critic} onClick={() => setAuto(v as number)}>{l}</button>
              ))}
            </div>
          </div>
          <p class="muted">{!critic ? 'Opus builds round 1 and stops; you decide what happens next.' : auto ? `Fully autonomous: build, critique, then ${auto === 1 ? 'one revision' : 'two revisions'} from the critic's write-up, each critiqued again.` : 'Opus builds round 1 and the critic reviews it. You then write the round 2 instructions, with the critic\'s points if you want them.'}</p>
        </div>
      </section>

      <section class="cstep cgo">
        <h2><span class="cstep-n">6</span>Effort</h2>
        <EffortSeg value={effort} onChange={setEffort} />
        <p class="muted">Runs in the background on your Claude usage. Opus sees contact sheets and the sound analysis; closing the studio stops the job (you can resume it).</p>
        <button type="button" class="cta cta-opus cta-xl" disabled={!canGo} onClick={() => void go()}>{Icon.spark}<span>{busy ? 'Starting…' : opusOk ? 'Create edit in the background' : 'Create the project'}</span></button>
      </section>
    </div>
  );
}

function LyricsStatus({ text }: { text: string }) {
  const l = useMemo(() => parseLyrics(text), [text]);
  return <p class={`muted small lyr-st${l.timed ? '' : ' warn'}`}>{l.timed ? `${l.lines.length} timed lines: captions land on the sung words.` : `${l.lines.length} lines without times: Opus uses them for the concept and at most two titles, not line-by-line captions. Paste synced lyrics for timed captions.`}</p>;
}
