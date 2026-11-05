import { useRef } from 'preact/hooks';
import { importFiles, removeMedia, runtime } from '../media/library';
import { TRANSITION_LABELS } from '../engine/transitions';
import { LeftTab, store, useStore } from '../state/store';
import { MediaInfo, TRANSITIONS, TransitionType } from '../state/types';
import { fmtBytes, fmtTime } from '../state/util';
import { addMediaClip, addText, applyTransition, TEXT_PRESETS } from './actions';
import { Btn, Icon } from './controls';

export function Rail() {
  const tab = useStore(s => s.leftTab);
  const items: { id: LeftTab; label: string; icon: any }[] = [
    { id: 'media', label: 'Media', icon: Icon.media },
    { id: 'text', label: 'Text', icon: Icon.text },
    { id: 'transitions', label: 'Transitions', icon: Icon.transition },
  ];
  return (
    <nav class="rail" aria-label="Library">
      {items.map(i => (
        <button type="button" class={`rail-b${tab === i.id ? ' is-on' : ''}`} onClick={() => store.set({ leftTab: i.id })} aria-pressed={tab === i.id}>
          {i.icon}<span>{i.label}</span>
        </button>
      ))}
    </nav>
  );
}

export function LeftPanel() {
  const tab = useStore(s => s.leftTab);
  return (
    <aside class="lp">
      {tab === 'media' && <MediaPanel />}
      {tab === 'text' && <TextPanel />}
      {tab === 'transitions' && <TransitionsPanel />}
    </aside>
  );
}

function MediaPanel() {
  const order = useStore(s => s.mediaOrder);
  const media = useStore(s => s.media);
  useStore(s => s.mediaRev);
  const inputRef = useRef<HTMLInputElement>(null);
  const list = order.map(id => media[id]).filter(Boolean);
  const offline = list.filter(m => m.status === 'offline').length;
  const total = list.reduce((a, m) => a + (m.size || 0), 0);
  return (
    <div class="panel">
      <header class="panel-h">
        <h2>Media</h2>
        <span class="panel-meta">{list.length ? `${list.length} · ${fmtBytes(total)}` : ''}</span>
      </header>
      <input ref={inputRef} type="file" multiple accept="video/*,audio/*,image/*,.mov,.mkv,.m4a,.flac" hidden onChange={e => { const f = (e.target as HTMLInputElement).files; if (f?.length) void importFiles(f); (e.target as HTMLInputElement).value = ''; }} />
      <button type="button" class="drop" onClick={() => inputRef.current?.click()}>
        {Icon.upload}
        <span class="drop-t">Import media</span>
        <span class="drop-s">Video, audio and images. Large files stream from disk.</span>
      </button>
      {offline > 0 && <p class="note warn">{offline} file{offline > 1 ? 's are' : ' is'} offline after a reload. Import the same file{offline > 1 ? 's' : ''} again to re-link.</p>}
      <div class="mgrid">
        {list.map(m => <MediaCard m={m} />)}
      </div>
    </div>
  );
}

function MediaCard({ m }: { m: MediaInfo }) {
  const rt = runtime.get(m.id);
  const poster = rt?.poster;
  const status = m.status === 'loading' ? 'Reading…' : m.status === 'error' ? 'Cannot open' : m.status === 'offline' ? 'Offline' : '';
  const a = m.analysis;
  const chip = m.analysisState === 'running' ? 'Analysing sound…' : a?.bpm ? `${Math.round(a.bpm)} BPM` : m.analysisState === 'done' && m.hasAudio ? 'Sound ✓' : '';
  return (
    <div class={`mcard k-${m.kind} s-${m.status}`} draggable={m.status === 'ready'}
      onDragStart={e => { e.dataTransfer?.setData('application/x-voidfx-media', m.id); if (e.dataTransfer) e.dataTransfer.effectAllowed = 'copy'; }}
      title={`${m.name}\n${m.kind}${m.width ? ` · ${m.width}×${m.height}` : ''}${m.duration ? ` · ${m.duration.toFixed(2)}s` : ''} · ${fmtBytes(m.size)}${m.error ? `\n${m.error}` : ''}`}>
      <div class="mcard-img">
        {poster ? <img src={poster} alt="" /> : <span class="mcard-ph">{m.kind === 'audio' ? Icon.vol : Icon.media}</span>}
        {m.kind !== 'image' && m.duration > 0 && <span class="mcard-dur">{fmtTime(m.duration)}</span>}
        <span class="mcard-id">{m.id}</span>
        {m.status === 'ready' && <button type="button" class="mcard-add" title="Add to timeline" onClick={() => addMediaClip(m.id)}>{Icon.plus}</button>}
      </div>
      <div class="mcard-name">{m.name}</div>
      <div class="mcard-meta">
        {status ? <span class={m.status === 'error' ? 'bad' : ''}>{status}</span> : <span>{fmtBytes(m.size)}</span>}
        {chip && <span class="chip">{chip}</span>}
        <button type="button" class="mcard-del" title="Remove from library" onClick={() => removeMedia(m.id)}>{Icon.close}</button>
      </div>
    </div>
  );
}

function TextPanel() {
  return (
    <div class="panel">
      <header class="panel-h"><h2>Text</h2></header>
      <p class="note">Adds a text clip at the playhead. Style it in the Edit panel.</p>
      <div class="tgrid">
        {TEXT_PRESETS.map(p => (
          <button type="button" class="tcard" onClick={() => addText(p.style, p.text, p.anim)}>
            <span class="tcard-s" style={{
              fontFamily: `"${p.style.font || 'Montserrat'}", sans-serif`, fontWeight: p.style.weight || 800, fontStyle: p.style.italic ? 'italic' : 'normal',
              textTransform: p.style.uppercase ? 'uppercase' : 'none', letterSpacing: `${p.style.tracking || 0}em`,
              background: p.style.bg ? p.style.bgColor : 'transparent', padding: p.style.bg ? '2px 6px' : 0,
              WebkitTextStroke: p.style.stroke ? '1px #000' : undefined,
            }}>{p.name}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function TransitionsPanel() {
  const sel = useStore(s => s.selection);
  return (
    <div class="panel">
      <header class="panel-h"><h2>Transitions</h2></header>
      <p class="note">{sel.length ? 'Applies into the selected clip from the clip before it.' : 'Applies at the main-track cut nearest the playhead, or select a clip first.'}</p>
      <div class="trgrid">
        {TRANSITIONS.map(t => <TransitionCard t={t} />)}
      </div>
      <Btn kind="solid" class="w100" onClick={() => applyTransition(null)}>Remove transition</Btn>
    </div>
  );
}

function TransitionCard({ t }: { t: TransitionType }) {
  return (
    <button type="button" class="trcard" onClick={() => applyTransition(t, t.startsWith('whip') || t === 'flash' || t === 'glitch' ? 0.35 : 0.5)} title={TRANSITION_LABELS[t]}>
      <span class={`trprev tp-${t.split('_')[0]} d-${t.split('_')[1] || 'x'}`} aria-hidden="true"><i class="a" /><i class="b" /></span>
      <span class="trcard-n">{TRANSITION_LABELS[t]}</span>
    </button>
  );
}
