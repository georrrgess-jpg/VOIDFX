// Long form: a 5-30 minute video edited calmly. Drop the video, give Opus its transcript, pick the
// features (or write what to add and remove), and one planning call builds it from the studio templates.
import { useMemo, useRef, useState } from 'preact/hooks';
import { startLongform } from '../../ai/jobs';
import { DEFAULT_LONGFORM, LongformOptions } from '../../ai/longform';
import { parseTranscript } from '../../state/transcript';
import { Effort, store, useStore } from '../../state/store';
import { fmtBytes } from '../../state/util';
import { Icon } from '../controls';
import { SectionHead } from './common';

const FEATURES: { key: keyof LongformOptions; label: string; text: string }[] = [
  { key: 'trim', label: 'Trim pauses', text: 'Dead air, false starts and repeated takes come out; jump cuts get a subtle punch-in.' },
  { key: 'chapters', label: 'Chapter cards', text: 'A clean title card at each change of topic.' },
  { key: 'breakdowns', label: 'Breakdown panels', text: 'An animated panel beside the speaker for the complicated parts: a title and the key points, revealed as they are said.' },
  { key: 'zooms', label: 'Emphasis zooms', text: 'A slow push-in on key lines, every minute or two.' },
  { key: 'captions', label: 'Captions', text: 'Subtitles from the transcript.' },
];
const ACCENTS = ['#7fd3ff', '#ffb357', '#52d6a0', '#c084fc', '#ff5f6d', '#f5f7fa'];

export function LongformSection() {
  const director = useStore(s => s.director);
  const [file, setFile] = useState<File | null>(null);
  const [transcript, setTranscript] = useState('');
  const [notes, setNotes] = useState('');
  const [title, setTitle] = useState('');
  const [opts, setOpts] = useState<LongformOptions>({ ...DEFAULT_LONGFORM });
  const [effort, setEffort] = useState<Effort>('medium');
  const [busy, setBusy] = useState(false);
  const [drag, setDrag] = useState(false);
  const [started, setStarted] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const trRef = useRef<HTMLInputElement>(null);
  const tr = useMemo(() => (transcript.trim() ? parseTranscript(transcript) : null), [transcript]);
  const opusOk = director.available === 'yes';
  const canGo = !!file && !busy && opusOk;

  const pick = (list: FileList | null) => {
    const f = list && Array.from(list).find(x => x.type.startsWith('video/') || /\.(mp4|mov|mkv|webm|m4v)$/i.test(x.name));
    if (f) setFile(f); else if (list?.length) store.toast('Pick a video file.', 'error');
  };
  const loadTranscript = async (list: FileList | null) => { const f = list?.[0]; if (f) setTranscript(await f.text()); };
  const go = async () => {
    if (!file || !canGo) return;
    setBusy(true);
    try {
      const name = title.trim() || file.name.replace(/\.[^.]+$/, '');
      const job = await startLongform({ name, effort, file, longform: { notes, transcript, options: opts } });
      if (job) { setStarted(name); setFile(null); setTranscript(''); setNotes(''); setTitle(''); }
    } finally { setBusy(false); }
  };
  const flag = (k: keyof LongformOptions) => setOpts({ ...opts, [k]: !opts[k] });

  return (
    <div class="hs create longform">
      <SectionHead eyebrow="Long form" title="Long videos, edited calmly" text="Talks, commentary, video essays and tutorials of 5 to 30 minutes. Opus reads the transcript and plans the edit in one pass: tighter pacing, chapters, animated breakdowns of the complicated parts and a few well-placed zooms. Built from polished templates, so it is quick and the timeline stays clean." />
      {!opusOk && <p class="note warn glass-note">{director.unavailableReason || 'Opus is not connected in this view.'}</p>}
      {started && <div class="started glass"><div class="started-h"><span class="started-ic" aria-hidden="true">{Icon.check}</span><div><b>“{started}” is being edited in the background.</b><p class="muted">You'll get a notice when it's ready; it opens in the editor like any project.</p></div><button type="button" class="btn btn-ghost" onClick={() => setStarted(null)} aria-label="Dismiss">{Icon.close}</button></div></div>}
      <div class="create-grid">
        <div class="create-steps">
          <section class="cstep">
            <h2><span class="cstep-n">1</span>The video</h2>
            <div class={`cdrop${drag ? ' is-drag' : ''}`} onDragOver={e => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)} onDrop={e => { e.preventDefault(); setDrag(false); pick(e.dataTransfer?.files || null); }}>
              <input ref={fileRef} type="file" hidden accept="video/*,.mov,.mkv,.m4v" onChange={e => { pick((e.target as HTMLInputElement).files); (e.target as HTMLInputElement).value = ''; }} />
              <button type="button" class="cdrop-btn" onClick={() => fileRef.current?.click()}>{Icon.upload}<span>{file ? 'Choose another video' : 'Choose the video'}</span></button>
              {file ? <p class="lf-file"><span class="fkind k-video">video</span><b>{file.name}</b><span class="muted">{fmtBytes(file.size)}</span></p> : <p class="muted">Any size; it is read from disk as needed and kept in this browser.</p>}
            </div>
            <input class="search" type="text" value={title} onInput={e => setTitle((e.target as HTMLInputElement).value)} placeholder="Project name (optional)" aria-label="Project name" />
          </section>
          <section class="cstep">
            <h2><span class="cstep-n">2</span>The transcript</h2>
            <p class="muted">Opus cannot hear the video: the transcript is how it knows what is said and when. Export captions as SRT or VTT from YouTube Studio, CapCut, Premiere or any transcription tool, then paste them or load the file.</p>
            <textarea class="ta big" rows={6} value={transcript} onInput={e => setTranscript((e.target as HTMLTextAreaElement).value)} placeholder={'1\n00:00:01,200 --> 00:00:04,800\nToday we are breaking down how...\n\nor lines like  [01:23] the next point'} />
            <div class="row">
              <input ref={trRef} type="file" hidden accept=".srt,.vtt,.txt" onChange={e => void loadTranscript((e.target as HTMLInputElement).files)} />
              <button type="button" class="btn btn-solid" onClick={() => trRef.current?.click()}>{Icon.upload}<span>Load .srt / .vtt</span></button>
              <span class={`muted small lyr-st${tr?.timed ? '' : ' warn'}`}>{tr ? (tr.timed ? `${tr.segments.length} timed cues · ${tr.words} words` : `${tr.words} words without times: Opus spreads things by the order they are said`) : 'No transcript: Opus can only trim pauses and add light structure.'}</span>
            </div>
          </section>
          <section class="cstep">
            <h2><span class="cstep-n">3</span>Features</h2>
            <div class="lf-feats">
              {FEATURES.map(f => (
                <button type="button" class={`lf-feat${opts[f.key] ? ' is-on' : ''}`} aria-pressed={!!opts[f.key]} onClick={() => flag(f.key)}>
                  <span class="lf-tick" aria-hidden="true">{opts[f.key] ? Icon.check : ''}</span>
                  <span><b>{f.label}</b><em>{f.text}</em></span>
                </button>
              ))}
            </div>
            <div class="row lf-row">
              <span class="fld-l">Pace</span>
              <div class="seg" role="radiogroup" aria-label="Pace">
                {(['calm', 'lively'] as const).map(p => <button type="button" role="radio" aria-checked={opts.pace === p} class={opts.pace === p ? 'is-on' : ''} onClick={() => setOpts({ ...opts, pace: p })}>{p === 'calm' ? 'Calm' : 'Lively'}</button>)}
              </div>
              <span class="fld-l">Accent</span>
              <div class="lf-swatches">{ACCENTS.map(c => <button type="button" class={`lf-sw${opts.accent === c ? ' is-on' : ''}`} style={{ background: c }} aria-label={`Accent ${c}`} onClick={() => setOpts({ ...opts, accent: c })} />)}</div>
            </div>
          </section>
          <section class="cstep">
            <h2><span class="cstep-n">4</span>Anything to add or remove</h2>
            <textarea class="ta big" rows={4} value={notes} onInput={e => setNotes((e.target as HTMLTextAreaElement).value)} placeholder="e.g. 'No zooms in the interview part. Add a breakdown when I explain compound interest. Keep the intro pauses, they are dramatic. Chapter titles in lower case.'" />
          </section>
          <section class="cstep cgo">
            <h2><span class="cstep-n">5</span>Depth</h2>
            <div class="seg seg-big" role="radiogroup" aria-label="Depth">
              {([['medium', 'Quick'], ['high', 'Detailed']] as [Effort, string][]).map(([v, l]) => <button type="button" role="radio" aria-checked={effort === v} class={effort === v ? 'is-on' : ''} onClick={() => setEffort(v)}>{l}</button>)}
            </div>
            <button type="button" class="cta cta-ice cta-xl" disabled={!canGo} onClick={() => void go()}>{Icon.spark}<span>{busy ? 'Starting…' : 'Edit the long-form video'}</span></button>
          </section>
        </div>
        <aside class="create-sum glass spot" aria-label="Your long-form edit">
          <p class="desk-eyebrow">Your long-form edit</p>
          <ul class="csum-list">
            <li class={file ? 'ok' : 'bad'}><span class="csum-ic" aria-hidden="true">{file ? Icon.check : '×'}</span><span><b>{file ? 'Video' : 'No video yet'}</b><em>{file ? `${file.name} · ${fmtBytes(file.size)}` : 'Choose the video to edit'}</em></span></li>
            <li class={tr?.timed ? 'ok' : 'warn'}><span class="csum-ic" aria-hidden="true">{tr?.timed ? Icon.check : '!'}</span><span><b>{tr ? (tr.timed ? 'Timed transcript' : 'Transcript without times') : 'No transcript'}</b><em>{tr?.timed ? 'Chapters, breakdowns and callouts land on what is said' : 'Add SRT or VTT for the full edit'}</em></span></li>
            <li class="ok"><span class="csum-ic" aria-hidden="true">{Icon.check}</span><span><b>{FEATURES.filter(f => opts[f.key]).length} features on</b><em>{FEATURES.filter(f => opts[f.key]).map(f => f.label).join(', ') || 'none'} · {opts.pace}</em></span></li>
            <li class={notes.trim() ? 'ok' : 'warn'}><span class="csum-ic" aria-hidden="true">{notes.trim() ? Icon.check : '!'}</span><span><b>{notes.trim() ? 'Your comments' : 'No comments'}</b><em>{notes.trim() ? `${notes.trim().split(/\s+/).length} words` : 'Optional: what to add or remove'}</em></span></li>
          </ul>
          <div class="csum-eta"><span class="stat-k">Estimated time</span><span class="csum-eta-v">{effort === 'high' ? '4–8' : '2–5'}<small> min</small></span><span class="muted small">Reading the video, then one planning call</span></div>
          <button type="button" class="cta cta-ice csum-go" disabled={!canGo} onClick={() => void go()}>{Icon.spark}<span>{busy ? 'Starting…' : 'Edit it'}</span></button>
        </aside>
      </div>
    </div>
  );
}
