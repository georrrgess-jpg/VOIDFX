import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'preact/hooks';
import { runtime, PEAK_RATE } from '../media/library';
import { player } from '../engine/player';
import { compileError } from '../engine/custom';
import { TRANSITION_LABELS } from '../engine/transitions';
import { addTrack, mainTrack, mediaLimit, normalize, trackKindFor } from '../state/ops';
import { store, useStore } from '../state/store';
import { Clip, MediaInfo, Project, Track, TrackKind } from '../state/types';
import { clamp, clipEnd, clipIn, clipSpeed, EPS, fmtTime, hasRamp, projectDuration, round, srcAt as srcAtLocal, trackClips } from '../state/util';
import { sfxPeaks } from '../engine/sfx';
import { timelineBeats } from '../engine/evaluate';
import { addMediaClip, deleteSelected, duplicateSelected, splitAtPlayhead } from './actions';
import { Btn, Icon } from './controls';

const RULER_H = 28;
const GAP = 3;
const trackH = (t: Track) => (t.kind === 'text' ? 34 : t.kind === 'audio' ? 52 : t.main ? 74 : 58);
const MIN_ZOOM = 2, MAX_ZOOM = 800;

interface Row { track: Track; y: number; h: number }
type Gesture =
  | { kind: 'move' | 'trim-l' | 'trim-r'; id: string; x0: number; y0: number; started: boolean; base: Project; ids: string[] }
  | { kind: 'scrub'; started: boolean };

function beatMarks(p: Project, media: Record<string, MediaInfo>): { t: number; down: boolean }[] {
  return timelineBeats(p, media);
}

export function Timeline() {
  const project = useStore(s => s.project);
  const selection = useStore(s => s.selection);
  const zoom = useStore(s => s.zoom);
  const snap = useStore(s => s.snap);
  const media = useStore(s => s.media);
  const mediaRev = useStore(s => s.mediaRev);
  const bodyRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const headsRef = useRef<HTMLDivElement>(null);
  const rulerRef = useRef<HTMLCanvasElement>(null);
  const [view, setView] = useState({ left: 0, top: 0, width: 900, height: 240 });
  const [snapX, setSnapX] = useState<number | null>(null);
  const [dropHint, setDropHint] = useState<{ x: number; y: number; h: number } | null>(null);
  const gesture = useRef<Gesture | null>(null);

  const dur = projectDuration(project);
  const rows: Row[] = useMemo(() => {
    let y = 0;
    return project.tracks.map(t => { const h = trackH(t); const r = { track: t, y, h }; y += h + GAP; return r; });
  }, [project.tracks]);
  const tracksH = rows.length ? rows[rows.length - 1].y + rows[rows.length - 1].h : 0;
  const contentW = Math.max(view.width, (dur + Math.max(10, view.width / zoom * 0.5)) * zoom);
  const beats = useMemo(() => beatMarks(project, media), [project, media]);

  // keep view metrics in sync with the scroll box
  useLayoutEffect(() => {
    const el = bodyRef.current!;
    const sync = () => {
      setView({ left: el.scrollLeft, top: el.scrollTop, width: el.clientWidth, height: el.clientHeight });
      if (headsRef.current) headsRef.current.style.transform = `translateY(${-el.scrollTop}px)`;
    };
    sync();
    let raf = 0;
    const onScroll = () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(sync); };
    el.addEventListener('scroll', onScroll, { passive: true });
    const ro = new ResizeObserver(sync);
    ro.observe(el);
    return () => { el.removeEventListener('scroll', onScroll); ro.disconnect(); cancelAnimationFrame(raf); };
  }, []);

  // ruler
  useEffect(() => {
    const cv = rulerRef.current;
    if (!cv) return;
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const W = view.width, H = RULER_H;
    cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
    cv.style.width = `${W}px`; cv.style.height = `${H}px`;
    const g = cv.getContext('2d')!;
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, W, H);
    const steps = [1 / project.fps, 0.1, 0.2, 0.5, 1, 2, 5, 10, 15, 30, 60, 120, 300, 600];
    const major = steps.find(s => s * zoom >= 84) || 600;
    const minor = major / (major >= 1 && major % 5 === 0 ? 5 : major >= 1 ? 4 : 5);
    const t0 = view.left / zoom, t1 = (view.left + W) / zoom;
    const css = getComputedStyle(cv);
    g.strokeStyle = css.getPropertyValue('--tick').trim() || '#555';
    g.fillStyle = css.getPropertyValue('--tick-label').trim() || '#999';
    g.font = '500 10px "Geist Mono", ui-monospace, monospace';
    g.lineWidth = 1;
    g.beginPath();
    for (let t = Math.floor(t0 / minor) * minor; t <= t1; t += minor) {
      const x = Math.round(t * zoom - view.left) + 0.5;
      const isMajor = Math.abs(t / major - Math.round(t / major)) < 1e-6;
      g.moveTo(x, H - (isMajor ? 10 : 5));
      g.lineTo(x, H);
      if (isMajor) g.fillText(major < 1 ? `${fmtTime(t)}.${String(Math.round((t % 1) * 100)).padStart(2, '0')}` : fmtTime(t), x + 3, 11);
    }
    g.stroke();
    // beat markers
    if (beats.length && zoom * (60 / 200) > 2) {
      for (const b of beats) {
        if (b.t < t0 - 1 || b.t > t1 + 1) continue;
        const x = Math.round(b.t * zoom - view.left) + 0.5;
        g.fillStyle = b.down ? css.getPropertyValue('--beat-down').trim() || '#ffb454' : css.getPropertyValue('--beat').trim() || '#776';
        g.fillRect(x - (b.down ? 1.5 : 1), H - (b.down ? 7 : 4), b.down ? 3 : 2, b.down ? 7 : 4);
      }
    }
  }, [view.left, view.width, zoom, project.fps, beats]);

  // ---------- helpers ----------
  const rowAt = (y: number): Row | null => rows.find(r => y >= r.y - GAP / 2 && y < r.y + r.h + GAP / 2) || null;
  const timeAt = (clientX: number) => {
    const r = contentRef.current!.getBoundingClientRect();
    return Math.max(0, (clientX - r.left) / zoom);
  };
  const snapTargets = (exclude: Set<string>) => {
    const s = store.state;
    const out = [0, s.time];
    for (const c of s.project.clips) if (!exclude.has(c.id)) out.push(c.start, clipEnd(c));
    if (s.snap) for (const b of beats) out.push(b.t);
    return out;
  };
  const snapValue = (t: number, targets: number[]): number | null => {
    let best: number | null = null, bd = 8 / zoom;
    for (const x of targets) { const d = Math.abs(x - t); if (d < bd) { bd = d; best = x; } }
    return best;
  };

  // ---------- pointer gestures ----------
  const onPointerDown = (e: PointerEvent) => {
    if (e.button !== 0) return;
    const target = e.target as HTMLElement;
    const clipEl = target.closest('[data-clip]') as HTMLElement | null;
    contentRef.current!.setPointerCapture(e.pointerId);
    if (!clipEl) {
      gesture.current = { kind: 'scrub', started: true };
      if (!e.shiftKey) store.set({ selection: [] });
      player.seek(timeAt(e.clientX));
      return;
    }
    const id = clipEl.dataset.clip!;
    const h = target.dataset.h as 'l' | 'r' | undefined;
    let sel = store.state.selection;
    if (e.shiftKey || e.metaKey || e.ctrlKey) sel = sel.includes(id) ? sel.filter(x => x !== id) : [...sel, id];
    else if (!sel.includes(id)) sel = [id];
    store.set({ selection: sel, rightTab: 'inspector' });
    const tr = store.state.project.tracks.find(t => t.id === store.state.project.clips.find(c => c.id === id)?.track);
    if (tr?.locked) { gesture.current = null; return; }
    gesture.current = { kind: h ? (h === 'l' ? 'trim-l' : 'trim-r') : 'move', id, x0: e.clientX, y0: e.clientY, started: false, base: store.state.project, ids: h ? [id] : sel };
  };

  const onPointerMove = (e: PointerEvent) => {
    const g = gesture.current;
    if (!g) return;
    if (g.kind === 'scrub') { player.seek(timeAt(e.clientX)); return; }
    if (!g.started) {
      if (Math.abs(e.clientX - g.x0) < 4 && Math.abs(e.clientY - g.y0) < 4) return;
      g.started = true;
      store.beginGesture();
    }
    const mediaNow = store.state.media;
    const fps = g.base.fps;
    const minDur = 1 / fps;
    const orig = g.base.clips.find(c => c.id === g.id);
    if (!orig) return;
    const dx = (e.clientX - g.x0) / zoom;
    const exclude = new Set(g.ids);
    const targets = snapTargets(exclude);
    const origTrack = g.base.tracks.find(t => t.id === orig.track)!;
    if (g.kind === 'move') {
      let dt = dx;
      let line: number | null = null;
      if (store.state.snap && !origTrack.main) {
        const s1 = snapValue(orig.start + dt, targets);
        const s2 = snapValue(clipEnd(orig) + dt, targets);
        if (s1 !== null && (s2 === null || Math.abs(s1 - orig.start - dt) <= Math.abs(s2 - clipEnd(orig) - dt))) { dt = s1 - orig.start; line = s1; }
        else if (s2 !== null) { dt = s2 - clipEnd(orig); line = s2; }
      }
      const minStart = Math.min(...g.ids.map(id => g.base.clips.find(c => c.id === id)?.start ?? 0));
      dt = Math.max(dt, -minStart);
      const r = contentRef.current!.getBoundingClientRect();
      const row = g.ids.length === 1 ? rowAt(e.clientY - r.top) : null;
      const kindOf = (c: Clip): TrackKind => trackKindFor(c.kind);
      let dest: Track | null = null;
      if (row && row.track.id !== orig.track) {
        const ok = row.track.kind === kindOf(orig);
        if (ok && !row.track.locked) dest = row.track;
      }
      setSnapX(line === null ? null : line * zoom);
      store.liveFromBase(p => {
        for (const c of p.clips) {
          if (!exclude.has(c.id)) continue;
          const o = g.base.clips.find(x => x.id === c.id)!;
          c.start = Math.max(0, o.start + dt);
        }
        const c = p.clips.find(x => x.id === g.id)!;
        if (dest) c.track = dest.id;
        const tr = p.tracks.find(t => t.id === c.track)!;
        if (tr.main) {
          // magnetic: order by pointer position among the other main clips
          const others = trackClips(p, tr.id).filter(x => x.id !== c.id);
          const tp = timeAt(e.clientX);
          let acc = 0, idx = others.length;
          for (let i = 0; i < others.length; i++) {
            if (tp < acc + others[i].dur / 2) { idx = i; break; }
            acc += others[i].dur;
          }
          c.start = idx < others.length ? others[idx].start - EPS * 10 : 1e6;
        }
        normalize(p, mediaNow, { resolveOverlaps: false });
      });
    } else {
      const sp = clipSpeed(orig);
      const isMedia = orig.kind === 'video' || orig.kind === 'audio';
      const list = trackClips(g.base, orig.track);
      const i = list.findIndex(c => c.id === orig.id);
      const prevEnd = !origTrack.main && i > 0 ? clipEnd(list[i - 1]) : 0;
      const nextStart = !origTrack.main && i < list.length - 1 ? list[i + 1].start : Infinity;
      let line: number | null = null;
      if (g.kind === 'trim-l') {
        let d = dx;
        if (store.state.snap && !origTrack.main) { const s = snapValue(orig.start + d, targets); if (s !== null) { d = s - orig.start; line = s; } }
        if (isMedia) d = Math.max(d, -clipIn(orig) / sp);
        d = Math.max(d, prevEnd - orig.start);
        d = Math.min(d, orig.dur - minDur);
        setSnapX(line === null ? null : line * zoom);
        store.liveFromBase(p => {
          const c = p.clips.find(x => x.id === g.id)!;
          if (!origTrack.main) c.start = round(orig.start + d, 4);
          c.dur = round(orig.dur - d, 4);
          if (isMedia) c.in = round(clipIn(orig) + d * sp, 4);
          if (c.kf) for (const k of Object.values(c.kf)) if (k) for (const key of k) key.t = round(key.t - d, 4);
          normalize(p, mediaNow, { resolveOverlaps: false });
        });
      } else {
        let d = dx;
        if (store.state.snap && !origTrack.main) { const s = snapValue(clipEnd(orig) + d, targets); if (s !== null) { d = s - clipEnd(orig); line = s; } }
        const maxDur = Math.min(mediaLimit(orig, mediaNow), nextStart - orig.start);
        d = Math.min(d, maxDur - orig.dur);
        d = Math.max(d, minDur - orig.dur);
        setSnapX(line === null ? null : line * zoom);
        store.liveFromBase(p => {
          const c = p.clips.find(x => x.id === g.id)!;
          c.dur = round(orig.dur + d, 4);
          normalize(p, mediaNow, { resolveOverlaps: false });
        });
      }
    }
  };

  const onPointerUp = () => {
    const g = gesture.current;
    gesture.current = null;
    setSnapX(null);
    if (g && g.kind !== 'scrub' && g.started) {
      store.live(p => normalize(p, store.state.media));
      store.endGesture();
    }
  };

  // ---------- media drag and drop from the library ----------
  const onDragOver = (e: DragEvent) => {
    if (!e.dataTransfer?.types.includes('application/x-voidfx-media')) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    const r = contentRef.current!.getBoundingClientRect();
    const row = rowAt(e.clientY - r.top);
    setDropHint({ x: e.clientX - r.left, y: row ? row.y : 0, h: row ? row.h : 40 });
  };
  const onDrop = (e: DragEvent) => {
    const id = e.dataTransfer?.getData('application/x-voidfx-media');
    setDropHint(null);
    if (!id) return;
    e.preventDefault();
    const r = contentRef.current!.getBoundingClientRect();
    const row = rowAt(e.clientY - r.top);
    const t = Math.max(0, (e.clientX - r.left) / zoom);
    const m = store.state.media[id];
    if (!m) return;
    if (row?.track.main || (!row && m.kind !== 'audio')) {
      const p = store.state.project;
      const main = mainTrack(p)!;
      const list = trackClips(p, main.id);
      let idx = list.length;
      for (let i = 0; i < list.length; i++) if (t < list[i].start + list[i].dur / 2) { idx = i; break; }
      addMediaClip(id, { trackId: main.id, insertIndex: idx });
    } else {
      addMediaClip(id, { at: t, trackId: row?.track.id });
    }
  };

  // wheel: ctrl/cmd zooms around the pointer, shift scrolls sideways
  const onWheel = (e: WheelEvent) => {
    const el = bodyRef.current!;
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault();
      const r = el.getBoundingClientRect();
      const px = e.clientX - r.left;
      const tAt = (el.scrollLeft + px) / zoom;
      const nz = clamp(zoom * Math.exp(-e.deltaY * 0.0022), MIN_ZOOM, MAX_ZOOM);
      store.set({ zoom: nz });
      requestAnimationFrame(() => { el.scrollLeft = tAt * nz - px; });
    } else if (e.shiftKey && Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
      e.preventDefault();
      el.scrollLeft += e.deltaY;
    }
  };

  const fitZoom = () => {
    const w = bodyRef.current?.clientWidth || 800;
    store.set({ zoom: clamp((w - 40) / Math.max(1, dur), MIN_ZOOM, MAX_ZOOM) });
    requestAnimationFrame(() => { if (bodyRef.current) bodyRef.current.scrollLeft = 0; });
  };

  const addTrackOf = (kind: TrackKind) => store.commit(p => { addTrack(p, kind); });

  const removeTrack = (id: string) => store.commit(p => { p.tracks = p.tracks.filter(t => t.id !== id); normalize(p, store.state.media); });

  const zoomPos = Math.log(zoom / MIN_ZOOM) / Math.log(MAX_ZOOM / MIN_ZOOM);
  const selSet = new Set(selection);

  return (
    <div class="tl" onWheel={onWheel as any}>
      <div class="tl-bar" role="toolbar" aria-label="Timeline tools">
        <Btn title="Split at playhead (S)" onClick={splitAtPlayhead}>{Icon.split}<span>Split</span></Btn>
        <Btn title="Duplicate (Ctrl+D)" onClick={duplicateSelected} disabled={!selection.length}>{Icon.copy}</Btn>
        <Btn title="Delete (Del)" onClick={deleteSelected} disabled={!selection.length}>{Icon.trash}</Btn>
        <span class="tl-sep" />
        <Btn title="Snap to clips, playhead and beats" active={snap} onClick={() => store.set({ snap: !snap })}>{Icon.snap}<span>Snap</span></Btn>
        <span class="tl-info">{project.clips.length ? `${project.clips.length} clip${project.clips.length === 1 ? '' : 's'} · ${dur.toFixed(2)}s` : 'Drag media here, or press + on a file'}</span>
        <span class="tl-grow" />
        <Btn title="Zoom out" onClick={() => store.set({ zoom: clamp(zoom / 1.4, MIN_ZOOM, MAX_ZOOM) })}>{Icon.minus}</Btn>
        <input class="tl-zoom" type="range" min={0} max={1000} value={Math.round(zoomPos * 1000)} aria-label="Timeline zoom"
          onInput={e => store.set({ zoom: MIN_ZOOM * Math.pow(MAX_ZOOM / MIN_ZOOM, +(e.target as HTMLInputElement).value / 1000) })} />
        <Btn title="Zoom in" onClick={() => store.set({ zoom: clamp(zoom * 1.4, MIN_ZOOM, MAX_ZOOM) })}>{Icon.plus}</Btn>
        <Btn title="Fit the whole edit" onClick={fitZoom}>{Icon.fit}</Btn>
      </div>
      <div class="tl-main">
        <div class="tl-corner">
          <TrackMenu onAdd={addTrackOf} />
        </div>
        <div class="tl-ruler" onPointerDown={e => { (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId); player.seek(timeAt(e.clientX)); gesture.current = { kind: 'scrub', started: true }; }} onPointerMove={onPointerMove as any} onPointerUp={onPointerUp}>
          <canvas ref={rulerRef} />
          <CriticMarks zoom={zoom} left={view.left} />
          <PlayheadHead zoom={zoom} left={view.left} />
        </div>
        <div class="tl-heads">
          <div ref={headsRef} class="tl-heads-in">
            {rows.map(r => (
              <TrackHead row={r} empty={!project.clips.some(c => c.track === r.track.id)} onRemove={() => removeTrack(r.track.id)} />
            ))}
          </div>
        </div>
        <div class="tl-body" ref={bodyRef}>
          <div class="tl-content" ref={contentRef} style={{ width: `${contentW}px`, height: `${Math.max(tracksH + 24, view.height)}px` }}
            onPointerDown={onPointerDown as any} onPointerMove={onPointerMove as any} onPointerUp={onPointerUp} onPointerCancel={onPointerUp}
            onDragOver={onDragOver as any} onDragLeave={() => setDropHint(null)} onDrop={onDrop as any}>
            {rows.map(r => <div class={`tl-row k-${r.track.kind}${r.track.main ? ' is-main' : ''}`} style={{ top: `${r.y}px`, height: `${r.h}px` }} />)}
            {project.clips.map(c => {
              const r = rows.find(x => x.track.id === c.track);
              if (!r) return null;
              return <ClipView key={c.id} clip={c} row={r} zoom={zoom} sel={selSet.has(c.id)} view={view} media={media} rev={mediaRev} fps={project.fps} />;
            })}
            {snapX !== null && <div class="tl-snap" style={{ left: `${snapX}px` }} />}
            {dropHint && <div class="tl-drop" style={{ left: `${dropHint.x}px`, top: `${dropHint.y}px`, height: `${dropHint.h}px` }} />}
            <PlayheadLine zoom={zoom} viewLeft={view.left} viewWidth={view.width} bodyRef={bodyRef} />
          </div>
        </div>
      </div>
    </div>
  );
}

function TrackMenu({ onAdd }: { onAdd: (k: TrackKind) => void }) {
  const [open, setOpen] = useState(false);
  return (
    <div class="tm">
      <Btn title="Add a track" onClick={() => setOpen(!open)}>{Icon.plus}<span>Track</span></Btn>
      {open && (
        <div class="tm-pop" onMouseLeave={() => setOpen(false)}>
          <button type="button" onClick={() => { onAdd('video'); setOpen(false); }}>Video overlay</button>
          <button type="button" onClick={() => { onAdd('text'); setOpen(false); }}>Text</button>
          <button type="button" onClick={() => { onAdd('audio'); setOpen(false); }}>Audio</button>
        </div>
      )}
    </div>
  );
}

function TrackHead({ row, empty, onRemove }: { row: Row; empty: boolean; onRemove: () => void }) {
  const t = row.track;
  const toggle = (k: 'muted' | 'hidden') => store.commit(p => { const x = p.tracks.find(y => y.id === t.id); if (x) x[k] = !x[k]; });
  return (
    <div class={`th k-${t.kind}${t.main ? ' is-main' : ''}`} style={{ height: `${row.h}px`, marginBottom: `${GAP}px` }}>
      <span class="th-icon" aria-hidden="true">{t.kind === 'text' ? Icon.text : t.kind === 'audio' ? Icon.vol : Icon.media}</span>
      <span class="th-name" title={t.main ? 'Main track: clips stay back to back' : t.name}>{t.main ? 'Main' : t.name}<em>{t.id}</em></span>
      <span class="th-btns">
        {t.kind !== 'text' && <button type="button" class={`th-b${t.muted ? ' is-on' : ''}`} title={t.muted ? 'Unmute track' : 'Mute track'} onClick={() => toggle('muted')}>{t.muted ? Icon.mute : Icon.vol}</button>}
        {t.kind !== 'audio' && <button type="button" class={`th-b${t.hidden ? ' is-on' : ''}`} title={t.hidden ? 'Show track' : 'Hide track'} onClick={() => toggle('hidden')}>{t.hidden ? Icon.eyeOff : Icon.eye}</button>}
        {empty && !t.main && <button type="button" class="th-b th-x" title="Remove empty track" onClick={onRemove}>{Icon.close}</button>}
      </span>
    </div>
  );
}

function PlayheadHead({ zoom, left }: { zoom: number; left: number }) {
  const time = useStore(s => s.time);
  const x = time * zoom - left;
  return <div class="ph-head" style={{ transform: `translateX(${x}px)` }} />;
}

function PlayheadLine({ zoom, viewLeft, viewWidth, bodyRef }: { zoom: number; viewLeft: number; viewWidth: number; bodyRef: { current: HTMLDivElement | null } }) {
  const time = useStore(s => s.time);
  const playing = useStore(s => s.playing);
  const x = time * zoom;
  useEffect(() => {
    if (!playing || !bodyRef.current) return;
    if (x > viewLeft + viewWidth - 60 || x < viewLeft) bodyRef.current.scrollLeft = Math.max(0, x - viewWidth * 0.2);
  }, [x, playing]);
  return <div class="ph-line" style={{ transform: `translateX(${x}px)` }} />;
}

// ---------- clip ----------

function ClipView({ clip: c, row, zoom, sel, view, media, rev, fps }: { clip: Clip; row: Row; zoom: number; sel: boolean; view: { left: number; width: number }; media: Record<string, MediaInfo>; rev: number; fps: number }) {
  const left = c.start * zoom;
  const width = Math.max(3, c.dur * zoom);
  const m = c.media ? media[c.media] : undefined;
  const label = c.kind === 'text' ? (c.text || '').replace(/\n/g, ' ').replace(/\*/g, '') : c.kind === 'sfx' ? `${c.sfx}` : c.kind === 'graphic' ? `◆ ${c.name || `graphic ${c.id}`}` : c.kind === 'shader' ? `✦ ${c.name || `effect ${c.id}`}` : c.name?.startsWith('auto:') ? (m?.name || c.kind) : c.name || m?.name || c.kind;
  const sp = clipSpeed(c);
  const offline = m && m.status === 'offline';
  const kfTimes = useMemo(() => {
    const set = new Set<number>();
    if (c.kf) for (const keys of Object.values(c.kf)) if (keys) for (const k of keys) set.add(+k.t.toFixed(3));
    return [...set];
  }, [c.kf]);
  return (
    <div data-clip={c.id} class={`clip k-${c.kind}${sel ? ' is-sel' : ''}${offline ? ' is-off' : ''}`} style={{ left: `${left}px`, width: `${width}px`, top: `${row.y}px`, height: `${row.h}px` }}
      title={`${label} · ${c.dur.toFixed(2)}s${sp !== 1 ? ` · ${sp}x` : ''}`}>
      {c.kind !== 'text' && (m || c.kind === 'sfx') && <ClipArt clip={c} zoom={zoom} h={row.h} view={view} m={m} rev={rev} />}
      <div class="clip-label">
        {offline && <b class="clip-badge bad">offline</b>}
        {hasRamp(c) ? <b class="clip-badge">ramp</b> : sp !== 1 && <b class="clip-badge">{sp}x</b>}
        {c.muted && <b class="clip-badge">muted</b>}
        {c.kind === 'shader' && c.code && compileError(c.code) && <b class="clip-badge bad" title={compileError(c.code) || ''}>error</b>}
        {(c.kind === 'shader' || c.kind === 'graphic') && c.blend && c.blend !== 'normal' && <b class="clip-badge">{c.blend}</b>}
        <span>{label}</span>
      </div>
      {c.transition && (
        <div class="clip-tr" style={{ width: `${Math.max(14, c.transition.dur * zoom)}px` }} title={`${TRANSITION_LABELS[c.transition.type]} · ${c.transition.dur}s`}>
          <span>⧓</span>
        </div>
      )}
      {kfTimes.map(t => <i class="clip-kf" style={{ left: `${t * zoom}px` }} />)}
      {(c.fadeIn ?? 0) > 0 && <i class="clip-fade l" style={{ width: `${(c.fadeIn || 0) * zoom}px` }} />}
      {(c.fadeOut ?? 0) > 0 && <i class="clip-fade r" style={{ width: `${(c.fadeOut || 0) * zoom}px` }} />}
      <div class="clip-h l" data-h="l" title="Drag to trim the start" />
      <div class="clip-h r" data-h="r" title="Drag to trim the end" />
    </div>
  );
}

function ClipArt({ clip: c, zoom, h, view, m, rev }: { clip: Clip; zoom: number; h: number; view: { left: number; width: number }; m?: MediaInfo; rev: number }) {
  const ref = useRef<HTMLCanvasElement>(null);
  const clipL = c.start * zoom, clipW = c.dur * zoom;
  const visL = Math.max(0, Math.floor(view.left - clipL - 100));
  const visR = Math.min(clipW, Math.ceil(view.left + view.width - clipL + 100));
  const w = Math.max(0, visR - visL);
  useEffect(() => {
    const cv = ref.current;
    if (!cv || w <= 0 || (!m && c.kind !== 'sfx')) return;
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    cv.width = Math.max(1, Math.round(w * dpr));
    cv.height = Math.max(1, Math.round(h * dpr));
    const g = cv.getContext('2d')!;
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, w, h);
    if (c.kind === 'sfx' && c.sfx) {
      const peaks = sfxPeaks(c.sfx);
      g.fillStyle = getComputedStyle(cv).getPropertyValue('--wave').trim() || 'rgba(255,200,140,0.85)';
      const base = h / 2 + 6, waveH = h - 18, off = c.in ?? 0;
      for (let x = 0; x < w; x++) {
        const t = off + (visL + x) / zoom;
        const pk = peaks[Math.floor(t * 100)] ?? 0;
        const amp = Math.min(1, pk * Math.min(2, (c.volume ?? 0.35) * 2.2)) * (waveH / 2);
        g.fillRect(x, base - amp, 1, amp * 2 || 1);
      }
      return;
    }
    const rt = runtime.get(m!.id);
    if (!rt || !m) return;
    const srcAt = (x: number) => srcAtLocal(c, (visL + x) / zoom);
    const showThumbs = (c.kind === 'video' || c.kind === 'image') && rt.thumbs.length;
    const waveH = c.kind === 'audio' ? h - 18 : m.hasAudio && c.kind === 'video' ? Math.round(h * 0.32) : 0;
    if (showThumbs) {
      const th = h - waveH;
      const t0 = rt.thumbs[0];
      const tileW = Math.max(16, (th * t0.w) / t0.h);
      const start = Math.floor(visL / tileW) * tileW - visL;
      for (let x = start; x < w; x += tileW) {
        let img = t0;
        if (c.kind === 'video' && rt.thumbs.length > 1) {
          const target = srcAt(x + tileW / 2);
          let lo = 0, hi = rt.thumbs.length - 1;
          while (lo < hi) { const mid = (lo + hi) >> 1; if (rt.thumbs[mid].t < target) lo = mid + 1; else hi = mid; }
          img = rt.thumbs[lo > 0 && Math.abs(rt.thumbs[lo - 1].t - target) < Math.abs(rt.thumbs[lo].t - target) ? lo - 1 : lo];
        }
        const s = Math.max(tileW / img.w, th / img.h);
        const dw = img.w * s, dh = img.h * s;
        g.save();
        g.beginPath();
        g.rect(x, 0, tileW, th);
        g.clip();
        g.drawImage(img.img, x + (tileW - dw) / 2, (th - dh) / 2, dw, dh);
        g.restore();
      }
    }
    if (waveH > 0 && rt.peaks) {
      const peaks = rt.peaks;
      const vol = Math.min(2, c.volume ?? 1) * (c.muted ? 0.15 : 1);
      const base = c.kind === 'audio' ? h / 2 + 7 : h - 1;
      g.fillStyle = getComputedStyle(cv).getPropertyValue('--wave').trim() || 'rgba(160,240,210,0.8)';
      for (let x = 0; x < w; x++) {
        const a = Math.floor(srcAt(x) * PEAK_RATE), b = Math.max(a + 1, Math.floor(srcAt(x + 1) * PEAK_RATE));
        let pk = 0;
        for (let i = Math.max(0, a); i < Math.min(peaks.length, b); i++) if (peaks[i] > pk) pk = peaks[i];
        const amp = Math.min(1, pk * vol) * (c.kind === 'audio' ? waveH / 2 : waveH);
        if (c.kind === 'audio') g.fillRect(x, base - amp, 1, amp * 2 || 1);
        else g.fillRect(x, base - amp, 1, amp || 1);
      }
    }
  }, [c.in, c.speed, c.dur, c.kind, c.volume, c.muted, c.kf?.speed, c.sfx, zoom, h, visL, w, rev, m?.id]);
  if (w <= 0) return null;
  return <canvas ref={ref} class="clip-art" style={{ left: `${visL}px`, width: `${w}px`, height: `${h}px` }} />;
}

/** The latest critique's points as markers on the ruler: hover for the point, click to jump there. */
function CriticMarks({ zoom, left }: { zoom: number; left: number }) {
  const rounds = useStore(s => s.rounds);
  const crit = [...rounds].reverse().find(r => r.critique)?.critique;
  if (!crit) return null;
  const marks = crit.issues.filter(i => i.at !== undefined).slice(0, 24);
  return (
    <>
      {marks.map(i => (
        <button type="button" class={`cmark s-${i.severity}`} style={{ left: `${i.at! * zoom - left}px` }} title={`Critic (${i.severity}, ${i.area}) at ${i.at!.toFixed(2)} s: ${i.problem}${i.fix ? `\nFix: ${i.fix}` : ''}`}
          aria-label={`Critic point at ${i.at!.toFixed(2)} seconds: ${i.problem}`}
          onPointerDown={e => { e.stopPropagation(); player.seek(i.at!); }} />
      ))}
    </>
  );
}
