import { useRef, useState } from 'preact/hooks';
import { attachLibraryItem, importFiles, removeMedia, runtime } from '../media/library';
import { defaultTransitionDur, TRANSITION_GROUPS, TRANSITION_LABELS } from '../engine/transitions';
import { SFX_INFO, sfxBuffer } from '../engine/sfx';
import { player } from '../engine/player';
import { listLibrary, LibraryItem } from '../state/catalog';
import { addSfx, addTransitionSounds, normalize } from '../state/ops';
import { LeftTab, store, useStore } from '../state/store';
import { MediaInfo, SFX, SfxType, STANDARD_CAPTION, TEXT_ANIMS_IN, TEXT_ANIMS_OUT, TextAnimIn, TextAnimOut } from '../state/types';
import { fmtBytes, fmtTime } from '../state/util';
import { addMediaClip, addText, applyTransition, selectedClips, TEXT_PRESETS, updateClip } from './actions';
import { Btn, Icon } from './controls';
import { EffectTile } from './EffectTile';
import { useCatalog } from './home/common';

export function Rail() {
  const tab = useStore(s => s.leftTab);
  const items: { id: LeftTab; label: string; icon: any }[] = [
    { id: 'media', label: 'Media', icon: Icon.media },
    { id: 'text', label: 'Text', icon: Icon.text },
    { id: 'transitions', label: 'Transitions', icon: Icon.transition },
    { id: 'sounds', label: 'Sounds', icon: Icon.vol },
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
      {tab === 'sounds' && <SoundsPanel />}
    </aside>
  );
}

function MediaPanel() {
  const order = useStore(s => s.mediaOrder);
  const media = useStore(s => s.media);
  useStore(s => s.mediaRev);
  const inputRef = useRef<HTMLInputElement>(null);
  const [showDb, setShowDb] = useState(false);
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
        <span class="drop-s">Any size. Files are kept with the project in this browser.</span>
      </button>
      <Btn kind="solid" class="w100" onClick={() => setShowDb(!showDb)} active={showDb}>{Icon.media}<span>From the database</span></Btn>
      {showDb && <DbPicker onDone={() => setShowDb(false)} />}
      {offline > 0 && <p class="note warn">{offline} file{offline > 1 ? 's are' : ' is'} offline. Import the same file{offline > 1 ? 's' : ''} again to re-link.</p>}
      <div class="mgrid">
        {list.map(m => <MediaCard m={m} />)}
      </div>
    </div>
  );
}

function DbPicker({ onDone }: { onDone: () => void }) {
  const [items] = useCatalog<LibraryItem[]>(listLibrary, []);
  const ready = items.filter(i => i.state === 'ready');
  if (!ready.length) return <p class="note">The database is empty. Add scene packs and music from the main menu.</p>;
  return (
    <div class="dbpick">
      {ready.map(it => (
        <button type="button" class="dbpick-i" onClick={() => { void attachLibraryItem(it).then(id => { if (id) store.toast(`Added ${it.name}`, 'ok'); }); onDone(); }}>
          {it.poster ? <img src={it.poster} alt="" /> : <span class="recent-ph">{it.kind === 'audio' ? Icon.vol : Icon.media}</span>}
          <span>{it.name}</span>
          <em>{it.role}</em>
        </button>
      ))}
    </div>
  );
}

function MediaCard({ m }: { m: MediaInfo }) {
  const rt = runtime.get(m.id);
  const poster = rt?.poster || m.poster;
  const status = m.status === 'loading' ? 'Reading…' : m.status === 'error' ? 'Cannot open' : m.status === 'offline' ? 'Offline' : '';
  const a = m.analysis;
  const chip = m.analysisState === 'running' ? 'Analysing…' : a?.bpm ? `${Math.round(a.bpm)} BPM` : m.shots && m.shots.length > 2 ? `${m.shots.length} shots` : m.analysisState === 'done' && m.hasAudio ? 'Sound ✓' : '';
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
        <button type="button" class="mcard-del" title="Remove from this project" onClick={() => removeMedia(m.id)}>{Icon.close}</button>
      </div>
    </div>
  );
}

const IN_LABEL: Record<string, string> = { none: 'None', fade: 'Fade', rise: 'Rise', drop: 'Drop', pop: 'Pop', blur: 'Blur', typewriter: 'Typewriter', words: 'Word by word', letters: 'Letter build', slide_left: 'Slide left', slide_right: 'Slide right' };
const OUT_LABEL: Record<string, string> = { none: 'None', fade: 'Fade', sink: 'Sink', lift: 'Lift', shrink: 'Shrink', blur: 'Blur', words: 'Word by word', scatter: 'Scatter', fall: 'Fall', slide_left: 'Slide left', slide_right: 'Slide right' };
export { IN_LABEL, OUT_LABEL };

function TextPanel() {
  const sel = useStore(s => s.selection);
  const project = useStore(s => s.project);
  const textClip = sel.length === 1 ? project.clips.find(c => c.id === sel[0] && c.kind === 'text') : undefined;
  return (
    <div class="panel">
      <header class="panel-h"><h2>Text</h2></header>
      <p class="note">Adds text at the playhead. Wrap a word in *asterisks* to emphasise it.</p>
      <div class="tgrid">
        <button type="button" class="tcard tcard-house" onClick={() => addText(STANDARD_CAPTION, 'COULD IT BE\n*HIM*', { in: 'words', out: 'fade', inDur: 0.6, outDur: 0.25 })}>
          <span class="tcard-s" style={{ fontFamily: '"Inter", sans-serif', fontWeight: 900, fontSize: '13px', lineHeight: 1.05, textAlign: 'center', textShadow: '0 0 2px #000, 0 1px 3px #000' }}>COULD IT BE<br /><b style={{ color: '#ff2b3a', fontSize: '17px', textShadow: '0 0 8px rgba(255,43,58,.6)' }}>HIM</b></span><em>house caption</em>
        </button>
        <button type="button" class="tcard tcard-house" onClick={() => addText({ ...STANDARD_CAPTION, size: 0.085, lineScales: [1], scrim: 0.2 }, 'BOP', { in: 'letters', out: 'scatter', inDur: 0.8, outDur: 0.5 })}>
          <span class="tcard-s" style={{ fontFamily: '"Inter", sans-serif', fontWeight: 900, fontSize: '20px' }}>HERO</span><em>letter build</em>
        </button>
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
      <h3 class="panel-sub">Animation in {textClip ? '' : <em>(select a text clip to apply)</em>}</h3>
      <div class="etgrid">
        {TEXT_ANIMS_IN.filter(a => a !== 'none').map(a => (
          <EffectTile kind="text" anim={{ in: a as TextAnimIn }} label={IN_LABEL[a]} active={textClip?.anim?.in === a}
            onPick={() => textClip ? updateClip(textClip.id, { anim: { in: a, inDur: a === 'letters' ? 0.8 : a === 'words' ? 0.6 : 0.35 } }) : addText(STANDARD_CAPTION, 'COULD IT BE\n*HIM*', { in: a as TextAnimIn, out: 'fade', inDur: 0.6, outDur: 0.25 })} />
        ))}
      </div>
      <h3 class="panel-sub">Animation out</h3>
      <div class="etgrid">
        {TEXT_ANIMS_OUT.filter(a => a !== 'none').map(a => (
          <EffectTile kind="text" anim={{ out: a as TextAnimOut }} label={OUT_LABEL[a]} active={textClip?.anim?.out === a}
            onPick={() => textClip ? updateClip(textClip.id, { anim: { out: a, outDur: a === 'scatter' || a === 'fall' ? 0.6 : 0.3 } }) : store.toast('Select a text clip first.')} />
        ))}
      </div>
    </div>
  );
}

function TransitionsPanel() {
  const sel = useStore(s => s.selection);
  const project = useStore(s => s.project);
  const cur = sel.length === 1 ? project.clips.find(c => c.id === sel[0])?.transition?.type : undefined;
  const logoUsed = project.clips.some(c => c.transition?.type === 'logo');
  return (
    <div class="panel">
      <header class="panel-h"><h2>Transitions</h2></header>
      <p class="note">{sel.length ? 'Applies into the selected clip from the clip before it.' : 'Applies at the main-track cut nearest the playhead, or select a clip first.'} Hover a tile to play it.</p>
      {TRANSITION_GROUPS.map(g => (
        <section>
          <h3 class="panel-sub">{g.name}</h3>
          <div class="etgrid">
            {g.items.map(t => (
              <EffectTile kind="transition" type={t} label={TRANSITION_LABELS[t]} active={cur === t}
                hint={t === 'logo' ? (logoUsed ? 'The logo is already used once in this edit (house rule: exactly once).' : 'The voidfx logo, as supplied, slams in and the camera flies through its "o". Once per edit.') : TRANSITION_LABELS[t]}
                onPick={() => applyTransition(t, defaultTransitionDur(t))} />
            ))}
          </div>
        </section>
      ))}
      <Btn kind="solid" class="w100" onClick={() => applyTransition(null)}>Remove transition</Btn>
    </div>
  );
}

let previewNode: AudioBufferSourceNode | null = null;
function previewSfx(t: SfxType) {
  player.ensureAudio();
  const ctx = player.actx;
  if (!ctx || !player.master) return;
  try { previewNode?.stop(); } catch { /* ended */ }
  const n = ctx.createBufferSource();
  n.buffer = sfxBuffer(ctx, t);
  const g = ctx.createGain();
  g.gain.value = 0.7;
  n.connect(g).connect(player.master);
  n.start();
  previewNode = n;
}

function SoundsPanel() {
  const trans = useStore(s => s.project.clips.filter(c => c.transition).length);
  return (
    <div class="panel">
      <header class="panel-h"><h2>Sounds</h2></header>
      <p class="note">Generated sound effects: every transition gets its own sound. Click the name to hear it; + adds it at the playhead on an SFX track.</p>
      <Btn kind="solid" class="w100" disabled={!trans} onClick={() => { store.commit(p => { addTransitionSounds(p); normalize(p, store.state.media); }); store.toast(`Matched sounds added to ${trans} transition${trans === 1 ? '' : 's'}.`, 'ok'); }}>
        {Icon.vol}<span>Sound every transition</span>
      </Btn>
      <ul class="sfxlist">
        {SFX.map(t => (
          <li>
            <button type="button" class="sfx-play" onClick={() => previewSfx(t)} title="Listen">{Icon.play}<span>{SFX_INFO[t].label}</span></button>
            <span class="sfx-h">{SFX_INFO[t].hint}</span>
            <button type="button" class="sfx-add" title="Add at the playhead" onClick={() => {
              let id = '';
              store.commit(p => { id = addSfx(p, t, store.state.time).id; normalize(p, store.state.media); });
              store.set({ selection: [id], rightTab: 'inspector' });
            }}>{Icon.plus}</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export { selectedClips };
