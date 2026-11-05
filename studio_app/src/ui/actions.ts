// User commands shared by keyboard shortcuts, toolbars and the inspector.
import { player } from '../engine/player';
import { addMediaToTimeline, deleteClips, duplicateClip, freeTrack, fxTrack, mainTrack, newClipId, normalize, patchClip, splitClipAt, velocityRamp } from '../state/ops';
import type { FxPreset } from '../engine/fxlibrary';
import { timelineBeats } from '../engine/evaluate';
import { store } from '../state/store';
import { AnimProp, Clip, DEFAULT_TEXT_STYLE, Project, TextStyle, TransitionType } from '../state/types';
import { clipEnd, EPS, projectDuration, propValue, round, trackClips } from '../state/util';

const media = () => store.state.media;

export function selectedClips(): Clip[] {
  const s = store.state;
  return s.selection.map(id => s.project.clips.find(c => c.id === id)).filter(Boolean) as Clip[];
}

export function commitNorm(fn: (p: Project) => void) {
  store.commit(p => { fn(p); normalize(p, media()); });
}

export function splitAtPlayhead() {
  const t = store.state.time;
  const p = store.state.project;
  let targets = selectedClips().filter(c => t > c.start + EPS && t < clipEnd(c) - EPS);
  if (!targets.length) {
    const main = mainTrack(p);
    targets = p.clips.filter(c => c.track === main?.id && t > c.start + EPS && t < clipEnd(c) - EPS);
  }
  if (!targets.length) { store.toast('Put the playhead over a clip to split it.'); return; }
  const created: string[] = [];
  commitNorm(pp => { for (const c of targets) { const b = splitClipAt(pp, c.id, t); if (b) created.push(b.id); } });
  if (created.length) store.set({ selection: created });
}

export function deleteSelected() {
  const ids = store.state.selection;
  if (!ids.length) return;
  commitNorm(p => deleteClips(p, ids));
  store.set({ selection: [] });
}

export function duplicateSelected() {
  const ids = store.state.selection;
  if (!ids.length) return;
  const made: string[] = [];
  commitNorm(p => { for (const id of ids) { const d = duplicateClip(p, id); if (d) made.push(d.id); } });
  store.set({ selection: made });
}

export function addMediaClip(mediaId: string, opts: { at?: number; trackId?: string; insertIndex?: number } = {}) {
  const m = media()[mediaId];
  if (!m || m.status !== 'ready') { store.toast('That file is still loading.'); return; }
  let id = '';
  commitNorm(p => { id = addMediaToTimeline(p, m, opts.at ?? store.state.time, opts).id; });
  store.set({ selection: [id], rightTab: 'inspector' });
}

export function addText(preset: Partial<TextStyle> = {}, text = 'Your text', anim?: Clip['anim'], transform?: Clip['transform']) {
  let id = '';
  const t = store.state.time;
  commitNorm(p => {
    const dur = 3;
    const tr = freeTrack(p, 'text', t, dur);
    const c: Clip = { id: newClipId(p, 'text'), track: tr.id, kind: 'text', start: round(t, 4), dur, text, style: { ...preset }, anim: anim || { in: 'fade', out: 'fade', inDur: 0.3, outDur: 0.25 } };
    if (transform) c.transform = transform;
    else if (preset.font === 'Inter' && preset.weight === 900) c.transform = { y: 0.25 };
    p.clips.push(c);
    id = c.id;
  });
  store.set({ selection: [id], rightTab: 'inspector' });
}

/** Patch the selected clip(s) through the validated path. */
export function updateClip(id: string, props: Record<string, any>, live = false) {
  const issues: string[] = [];
  const apply = (p: Project) => {
    const c = p.clips.find(x => x.id === id);
    if (!c) return;
    patchClip(c, props, issues, p);
    normalize(p, media());
  };
  if (live) store.live(apply); else store.commit(apply);
  if (issues.length && !live) store.toast(issues[0].replace(/^clip \S+: /, ''), 'error');
}

/** Velocity ramp on the selected clip from the music's beats (burst on the beat, slow motion between). */
export function rampSelected(clear = false) {
  const c = selectedClips().find(x => x.kind === 'video');
  if (!c) { store.toast('Select a video clip.'); return; }
  let ok = true;
  store.commit(p => {
    const cc = p.clips.find(x => x.id === c.id)!;
    if (clear) { if (cc.kf) delete cc.kf.speed; }
    else ok = velocityRamp(p, media(), cc);
    normalize(p, media());
  });
  if (!ok) store.toast('No music beats fall inside this clip. Put a song on an audio track first.', 'error');
}

/** Put each word of the selected text clip on the next beats (or every 0.2 s without music). */
export function wordsOnBeats() {
  const c = selectedClips().find(x => x.kind === 'text');
  if (!c) return;
  const n = (c.text || '').replace(/\*/g, '').split(/\s+/).filter(Boolean).length;
  const beats = timelineBeats(store.state.project, media()).map(b => b.t - c.start).filter(t => t >= 0 && t < c.dur);
  const half: number[] = [];
  for (let i = 0; i < beats.length; i++) { half.push(beats[i]); if (i + 1 < beats.length) half.push((beats[i] + beats[i + 1]) / 2); }
  const times = Array.from({ length: n }, (_, i) => round(half[i] ?? (half.length ? half[half.length - 1] + (i - half.length + 1) * 0.2 : i * 0.2), 3));
  updateClip(c.id, { words: times, anim: { in: 'words' } });
}

/** Set an animatable property: writes a keyframe at the playhead when the property is keyframed. */
export function setAnimProp(c: Clip, prop: AnimProp, v: number, live: boolean) {
  const lt = round(store.state.time - c.start, 4);
  const keys = c.kf?.[prop];
  if (keys && keys.length) {
    const frame = 0.5 / store.state.project.fps;
    const next = keys.filter(k => Math.abs(k.t - lt) > frame);
    if (lt >= -frame && lt <= c.dur + frame) next.push({ t: Math.max(0, Math.min(c.dur, lt)), v, ...(keys[0].e ? { e: keys[0].e } : {}) });
    next.sort((a, b) => a.t - b.t);
    updateClip(c.id, { kf: { [prop]: next } }, live);
  } else if (prop === 'volume') {
    updateClip(c.id, { volume: v }, live);
  } else {
    updateClip(c.id, { transform: { [prop]: v } }, live);
  }
}

export function toggleKeyframe(c: Clip, prop: AnimProp) {
  const lt = store.state.time - c.start;
  if (lt < 0 || lt > c.dur) { store.toast('Move the playhead inside the clip to add a keyframe.'); return; }
  const frame = 0.5 / store.state.project.fps;
  const keys = c.kf?.[prop] || [];
  const hit = keys.find(k => Math.abs(k.t - lt) <= frame);
  const next = hit ? keys.filter(k => k !== hit) : [...keys, { t: round(lt, 4), v: propValue(c, prop, lt) }].sort((a, b) => a.t - b.t);
  updateClip(c.id, { kf: { [prop]: next.length ? next : null } });
}

export function jumpKeyframe(c: Clip, prop: AnimProp, dir: 1 | -1) {
  const lt = store.state.time - c.start;
  const keys = c.kf?.[prop] || [];
  const eps = 0.5 / store.state.project.fps;
  const k = dir > 0 ? keys.find(x => x.t > lt + eps) : [...keys].reverse().find(x => x.t < lt - eps);
  if (k) player.seek(c.start + k.t);
}

/** Apply a transition into the selected clip, or into the main-track clip after the cut nearest the playhead. */
export function applyTransition(type: TransitionType | null, dur = 0.5) {
  const p = store.state.project;
  let target = selectedClips().find(c => c.kind !== 'text');
  if (target) {
    const prev = trackClips(p, target.track).filter(c => Math.abs(clipEnd(c) - target!.start) < 1.5 / p.fps);
    if (!prev.length) {
      store.toast('Transitions go between two clips that touch on the same track. Select the second clip.');
      return;
    }
  } else {
    const main = mainTrack(p);
    const list = main ? trackClips(p, main.id) : [];
    let best: Clip | null = null, bestD = Infinity;
    for (let i = 1; i < list.length; i++) {
      const d = Math.abs(list[i].start - store.state.time);
      if (d < bestD) { bestD = d; best = list[i]; }
    }
    if (!best) { store.toast('Add at least two clips to the main track first.'); return; }
    target = best;
  }
  const id = target.id;
  updateClip(id, { transition: type ? { type, dur } : null });
  store.set({ selection: [id] });
  if (type) player.seek(Math.max(0, target.start - Math.min(1, dur)));
}

export function nudgeSelection(dt: number) {
  const ids = store.state.selection;
  if (!ids.length) return;
  commitNorm(p => { for (const c of p.clips) if (ids.includes(c.id)) c.start = Math.max(0, c.start + dt); });
}

export const TEXT_PRESETS: { name: string; style: Partial<TextStyle>; text: string; anim?: Clip['anim'] }[] = [
  { name: 'Plain', style: {}, text: 'Your text' },
  { name: 'Bold caption', style: { font: 'Montserrat', weight: 900, size: 0.05, stroke: 0.08, strokeColor: '#000000', shadow: 0.6 }, text: 'Bold caption' },
  { name: 'Boxed', style: { font: 'Poppins', weight: 800, size: 0.04, bg: true, bgColor: '#000000', color: '#ffffff', shadow: 0 }, text: 'Boxed caption' },
  { name: 'Headline', style: { font: 'Anton', weight: 400, size: 0.085, uppercase: true, tracking: 0.02, shadow: 0.4 }, text: 'Headline' },
  { name: 'Condensed', style: { font: 'Bebas Neue', weight: 400, size: 0.09, tracking: 0.04, shadow: 0.3 }, text: 'Condensed title' },
  { name: 'Serif', style: { font: 'Playfair Display', weight: 700, italic: true, size: 0.055, shadow: 0.5 }, text: 'Serif title' },
  { name: 'Marker', style: { font: 'Permanent Marker', weight: 400, size: 0.055, shadow: 0.5 }, text: 'Marker' },
  { name: 'Mono', style: { font: 'Space Mono', weight: 700, size: 0.035, uppercase: true, tracking: 0.08, shadow: 0.4 }, text: 'Mono label' },
];

export { DEFAULT_TEXT_STYLE };

/** Add a starter effect or graphic at the playhead on an overlay track, selected for editing. */
export function addCustom(fx: FxPreset) {
  let id = '';
  const t = store.state.time;
  commitNorm(p => {
    const end = projectDuration(p);
    const dur = end > 0 && t + fx.dur > end ? Math.max(0.2, end - t) : fx.dur;
    const tr = fxTrack(p, t, dur);
    const c: Clip = { id: newClipId(p, fx.kind), track: tr.id, kind: fx.kind, start: round(t, 4), dur: round(dur, 4), name: fx.name, blend: fx.blend };
    const issues: string[] = [];
    if (fx.kind === 'graphic') patchClip(c, { svg: fx.svg, gw: fx.gw ?? 0.6, glow: fx.glow ?? 0, reveal: fx.reveal || {} }, issues, p);
    else patchClip(c, { code: fx.code }, issues, p);
    p.clips.push(c);
    id = c.id;
  });
  store.set({ selection: [id], rightTab: 'inspector' });
  player.seek(store.state.time + 0.0001);
}
