// Edit operations shared by the UI and the Opus Director. Every change is validated here so the
// timeline can never hold out-of-range values, overlapping clips or dangling references.
import { expandPiece } from './pieces';
import {
  ANIM_PROPS, AnimProp, BLEND_MODES, Clip, ClipKind, DEFAULT_CAMERA, Ease, FONTS, Keyframe, MediaInfo, Project, REVEALS_IN, REVEALS_OUT, SFX, SfxType, STANDARD_CAPTION, TEXT_ANIMS_IN, TEXT_ANIMS_OUT,
  Track, TrackKind, TRANSITIONS, TransitionType, BeatCamera,
} from './types';
import { twoLines } from './lyrics';
import { clamp, clipEnd, clipIn, clipSpeed, deepClone, EPS, hasRamp, num, projectDuration, round, shortId, srcAt, trackClips } from './util';

import { SFX_INFO, SFX_PEAK, sfxPeakAt, soundsForTransition } from '../engine/sfx';
import { timelineBeats } from '../engine/evaluate';
import { defaultTransitionDur } from '../engine/transitions';
import { checkShaderCode, sanitizeSvg } from '../engine/custom';
import { FX_LIBRARY, fxCode, fxParams, getFx } from '../engine/fxlib';
import { newProject } from './store';

const HEX = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i;
const EASES: Ease[] = ['linear', 'in', 'out', 'inOut', 'hold'];

export const trackKindFor = (k: ClipKind): TrackKind => (k === 'image' || k === 'graphic' || k === 'shader' ? 'video' : k === 'sfx' ? 'audio' : k);
/** Custom layers (vector graphics and effects) live on overlay video tracks, never the main track. */
export const isCustom = (c: Clip) => c.kind === 'graphic' || c.kind === 'shader';

/**
 * An overlay video track with room for [start, start+dur), named FX when it has to be added. Effects
 * go under the edit's look (so they are graded with the picture) unless `over` puts them above it.
 */
export function fxTrack(p: Project, start: number, dur: number, prefer?: string, ignore?: string, over = false): Track {
  const ok = (t: Track) => t.kind === 'video' && !t.main && t.role !== 'look' && (over ? t.role === 'over' : t.role !== 'over');
  const pref = prefer ? p.tracks.find(t => t.id === prefer && ok(t)) : undefined;
  if (pref && isFree(p, pref.id, start, dur, ignore)) return pref;
  for (const t of p.tracks) if (ok(t) && isFree(p, t.id, start, dur, ignore)) return t;
  return over ? addTrack(p, 'video', undefined, 'FX over look', 'over') : addTrack(p, 'video', undefined, 'FX');
}

/** The edit's look track (the grade over every video track, under the text), added when needed. */
export function lookTrack(p: Project): Track {
  return p.tracks.find(t => t.role === 'look') || addTrack(p, 'video', undefined, 'Look', 'look');
}

export function mainTrack(p: Project): Track | undefined {
  return p.tracks.find(t => t.main) || p.tracks.find(t => t.kind === 'video');
}

export function allIds(p: Project): Set<string> {
  return new Set([...p.clips.map(c => c.id), ...p.tracks.map(t => t.id)]);
}

/** Ids the studio makes up itself: a form Opus does not use for its own ids (c1, t1, e1, fx2), so they never collide. */
export function newClipId(p: Project, kind: ClipKind): string {
  return shortId(kind === 'text' ? 'T_' : kind === 'audio' ? 'A_' : kind === 'sfx' ? 'S_' : kind === 'graphic' ? 'G_' : kind === 'shader' ? 'X_' : 'C_', allIds(p));
}

export function newTrackId(p: Project, kind: TrackKind): string {
  return shortId(kind === 'video' ? 'V' : kind === 'audio' ? 'A' : 'T', allIds(p));
}

/**
 * Add a track of `kind`. Video and text tracks go above existing ones of their kind, audio below.
 * Video order, top to bottom: effects over the look, the look, then every other video track.
 */
export function addTrack(p: Project, kind: TrackKind, id?: string, name?: string, role?: Track['role']): Track {
  const t: Track = { id: id || newTrackId(p, kind), kind, name: name || (kind === 'video' ? 'Overlay' : kind === 'audio' ? 'Audio' : 'Text'), ...(role ? { role } : {}) };
  const lookAt = p.tracks.findIndex(x => x.role === 'look');
  const lastOver = p.tracks.map(x => x.role === 'over').lastIndexOf(true);
  const firstVideo = p.tracks.findIndex(x => x.kind === 'video');
  if (kind === 'audio') {
    p.tracks.push(t);
  } else if (kind === 'video' && role === 'over') {
    p.tracks.splice(firstVideo >= 0 ? firstVideo : p.tracks.findIndex(x => x.kind === 'audio') < 0 ? p.tracks.length : p.tracks.findIndex(x => x.kind === 'audio'), 0, t);
  } else if (kind === 'video' && role === 'look') {
    p.tracks.splice(lastOver >= 0 ? lastOver + 1 : firstVideo >= 0 ? firstVideo : p.tracks.length, 0, t);
  } else if (kind === 'video' && (lookAt >= 0 || lastOver >= 0)) {
    p.tracks.splice(Math.max(lookAt, lastOver) + 1, 0, t);
  } else {
    const firstOfKind = p.tracks.findIndex(x => x.kind === kind);
    if (firstOfKind >= 0) p.tracks.splice(firstOfKind, 0, t);
    else if (kind === 'text') p.tracks.unshift(t);
    else {
      const firstAudio = p.tracks.findIndex(x => x.kind === 'audio');
      p.tracks.splice(firstAudio < 0 ? p.tracks.length : firstAudio, 0, t);
    }
  }
  return t;
}

export function isFree(p: Project, trackId: string, start: number, dur: number, ignore?: string): boolean {
  const end = start + dur;
  return !p.clips.some(c => c.track === trackId && c.id !== ignore && c.start < end - EPS && c.start + c.dur > start + EPS);
}

/** A track of `kind` with room for [start, start+dur): the preferred one, else any, else a new one. */
export function freeTrack(p: Project, kind: TrackKind, start: number, dur: number, prefer?: string, ignore?: string): Track {
  const pref = prefer ? p.tracks.find(t => t.id === prefer && t.kind === kind) : undefined;
  if (pref && (pref.main || isFree(p, pref.id, start, dur, ignore))) return pref;
  for (const t of p.tracks) if (t.kind === kind && !t.main && !t.role && isFree(p, t.id, start, dur, ignore)) return t;
  return addTrack(p, kind);
}

export function mediaLimit(c: Clip, media: Record<string, MediaInfo>): number {
  // Longest timeline duration this clip may have given its in-point and speed (ramps included).
  if (c.kind === 'text' || c.kind === 'image' || c.kind === 'graphic' || c.kind === 'shader') return Infinity;
  if (c.kind === 'sfx') return c.sfx ? Math.max(0.02, SFX_INFO[c.sfx].dur - (c.in ?? 0)) : Infinity;
  const m = c.media ? media[c.media] : undefined;
  if (!m || !m.duration) return Infinity;
  if (!hasRamp(c)) return Math.max(0, (m.duration - clipIn(c)) / clipSpeed(c));
  if (srcAt(c, c.dur) <= m.duration) return Infinity;
  let lo = 0, hi = c.dur;
  for (let i = 0; i < 30; i++) { const mid = (lo + hi) / 2; if (srcAt(c, mid) <= m.duration) lo = mid; else hi = mid; }
  return lo;
}

/**
 * Clean up after any change: pack the magnetic main track, move overlapping clips to free tracks,
 * keep media ranges valid, drop transitions without a neighbour, and remove empty extra tracks.
 */
export function normalize(p: Project, media: Record<string, MediaInfo>, opts: { pruneTracks?: boolean; resolveOverlaps?: boolean } = {}): Project {
  const fps = p.fps || 30;
  const minDur = 1 / fps;
  // valid references
  const trackIds = new Set(p.tracks.map(t => t.id));
  p.clips = p.clips.filter(c => {
    if (!trackIds.has(c.track)) return false;
    if (c.kind === 'sfx') return !!c.sfx;
    if (c.kind === 'graphic') return !!c.svg;
    if (c.kind === 'shader') return !!c.code;
    if (c.kind !== 'text' && (!c.media || !media[c.media])) return false;
    return true;
  });
  // custom layers never sit on the magnetic main track or a non-video track
  for (const c of p.clips) {
    if (!isCustom(c)) continue;
    const t = p.tracks.find(x => x.id === c.track);
    if (!t || t.main || t.kind !== 'video') c.track = fxTrack(p, c.start, c.dur, undefined, c.id).id;
  }
  for (const c of p.clips) {
    c.start = Math.max(0, round(c.start, 4));
    const lim = mediaLimit(c, media);
    if (c.dur > lim) c.dur = lim;
    c.dur = round(Math.max(minDur, c.dur), 4);
    if (c.in !== undefined) c.in = round(Math.max(0, c.in), 4);
    if (c.fadeIn) c.fadeIn = clamp(c.fadeIn, 0, c.dur);
    if (c.fadeOut) c.fadeOut = clamp(c.fadeOut, 0, c.dur);
  }
  // main track: packed end to end in start order
  const main = mainTrack(p);
  if (main && main.main) {
    let t = 0;
    for (const c of trackClips(p, main.id)) { c.start = round(t, 4); t += c.dur; }
  }
  // overlaps on other tracks: later clips move to a free track of the same kind
  if (opts.resolveOverlaps !== false) for (const tr of [...p.tracks]) {
    if (tr.main) continue;
    const list = trackClips(p, tr.id);
    let end = -Infinity;
    for (const c of list) {
      if (c.start < end - EPS) {
        const dest = freeTrack(p, tr.kind, c.start, c.dur, undefined, c.id);
        c.track = dest.id;
      } else end = c.start + c.dur;
    }
  }
  // transitions need a clip ending where this one starts
  for (const tr of p.tracks) {
    const list = trackClips(p, tr.id);
    for (let i = 0; i < list.length; i++) {
      const c = list[i];
      if (!c.transition) continue;
      const prev = list[i - 1];
      if (!prev || Math.abs(clipEnd(prev) - c.start) > minDur * 1.5 || tr.kind === 'text') { delete c.transition; continue; }
      const maxD = Math.min(prev.dur, c.dur, 3);
      const { at, to } = c.transition;
      c.transition = { type: c.transition.type, dur: round(clamp(c.transition.dur, minDur * 2, maxD), 3), ...(at ? { at } : {}), ...(to ? { to } : {}) };
    }
  }
  if (opts.pruneTracks) {
    const used = new Set(p.clips.map(c => c.track));
    const defaults = new Set(newProject().tracks.map(t => t.id));
    p.tracks = p.tracks.filter(t => used.has(t.id) || t.main || defaults.has(t.id));
  }
  // at least one track of each kind
  for (const k of ['text', 'video', 'audio'] as TrackKind[]) if (!p.tracks.some(t => t.kind === k)) addTrack(p, k);
  if (!p.tracks.some(t => t.main)) {
    const v = p.tracks.find(t => t.kind === 'video');
    if (v) v.main = true;
  }
  // looks that cover the whole edit follow its length
  const len = projectDuration(p);
  if (len > 0) for (const c of p.clips) if (c.span === 'all') c.dur = round(Math.max(minDur, len - c.start), 4);
  p.clips.sort((a, b) => a.start - b.start);
  return p;
}

// ---------- UI helpers ----------

export function makeMediaClip(p: Project, m: MediaInfo, start: number, trackId: string, asAudio = false): Clip {
  const kind: ClipKind = asAudio ? 'audio' : m.kind;
  const c: Clip = { id: newClipId(p, kind), track: trackId, kind, start, dur: m.kind === 'image' ? 3 : Math.max(0.1, m.duration), media: m.id, in: 0 };
  if (kind !== 'audio') c.fit = 'cover';
  return c;
}

/** Add media at the playhead (overlays/audio) or at the end of the main track (video/images). */
export function addMediaToTimeline(p: Project, m: MediaInfo, at: number, opts: { trackId?: string; insertIndex?: number } = {}): Clip {
  const forceTrack = opts.trackId ? p.tracks.find(t => t.id === opts.trackId) : undefined;
  if (m.kind === 'audio' || (forceTrack && forceTrack.kind === 'audio')) {
    const probe = makeMediaClip(p, m, at, '', true);
    const tr = freeTrack(p, 'audio', at, probe.dur, forceTrack?.id);
    probe.track = tr.id;
    p.clips.push(probe);
    return probe;
  }
  const main = mainTrack(p)!;
  const target = forceTrack && forceTrack.kind === 'video' ? forceTrack : main;
  if (target.main) {
    const list = trackClips(p, target.id);
    const idx = opts.insertIndex ?? list.length;
    const c = makeMediaClip(p, m, 0, target.id);
    // insert by giving it a start just before the clip at idx; normalize packs the track
    c.start = idx >= list.length ? (list.length ? clipEnd(list[list.length - 1]) : 0) : list[idx].start - EPS * 10;
    p.clips.push(c);
    return c;
  }
  const c = makeMediaClip(p, m, at, target.id);
  const tr = freeTrack(p, 'video', at, c.dur, target.id);
  c.track = tr.id;
  p.clips.push(c);
  return c;
}

export function splitClipAt(p: Project, id: string, at: number): Clip | null {
  const c = p.clips.find(x => x.id === id);
  if (!c) return null;
  const lt = at - c.start;
  const minDur = 1 / (p.fps || 30);
  if (lt < minDur || c.dur - lt < minDur) return null;
  const b: Clip = deepClone(c);
  b.id = newClipId(p, c.kind);
  b.start = at;
  b.dur = c.dur - lt;
  if (c.kind === 'video' || c.kind === 'audio') b.in = round(srcAt(c, lt), 4);
  else if (c.kind === 'sfx') b.in = round((c.in ?? 0) + lt, 4);
  else if (c.kind === 'image') b.in = 0;
  c.dur = lt;
  delete b.transition;
  delete c.fadeOut;
  delete b.fadeIn;
  if (c.kind === 'text') { b.anim = { ...(b.anim || {}), in: 'none' }; c.anim = { ...(c.anim || {}), out: 'none' }; }
  if (c.kf) {
    const ka: Clip['kf'] = {}, kb: Clip['kf'] = {};
    for (const prop of ANIM_PROPS) {
      const keys = c.kf[prop];
      if (!keys?.length) continue;
      const va = keys.filter(k => k.t <= lt + EPS);
      const vb = keys.filter(k => k.t >= lt - EPS).map(k => ({ ...k, t: round(k.t - lt, 4) }));
      if (va.length) ka[prop] = va;
      if (vb.length) kb[prop] = vb;
    }
    c.kf = ka;
    b.kf = kb;
  }
  p.clips.push(b);
  return b;
}

export function deleteClips(p: Project, ids: string[]) {
  const set = new Set(ids);
  p.clips = p.clips.filter(c => !set.has(c.id));
}

export function duplicateClip(p: Project, id: string): Clip | null {
  const c = p.clips.find(x => x.id === id);
  if (!c) return null;
  const d: Clip = deepClone(c);
  d.id = newClipId(p, c.kind);
  delete d.transition;
  const tr = p.tracks.find(t => t.id === c.track)!;
  if (tr.main) {
    d.start = c.start + c.dur - EPS * 10; // lands right after the original once packed
  } else {
    d.start = clipEnd(c);
    d.track = freeTrack(p, tr.kind, d.start, d.dur, tr.id).id;
  }
  p.clips.push(d);
  return d;
}

// ---------- validated property patches (shared by the inspector and Opus) ----------

function sanitizeKeys(raw: unknown, prop: AnimProp, maxT: number): Keyframe[] | null {
  if (!Array.isArray(raw)) return null;
  const range: Record<AnimProp, [number, number]> = {
    x: [-3, 3], y: [-3, 3], scale: [0.02, 20], rotation: [-1440, 1440], opacity: [0, 1], volume: [0, 4], speed: [0.05, 10],
  };
  const [lo, hi] = range[prop];
  const out: Keyframe[] = [];
  for (const k of raw) {
    let t: number, v: number, e: unknown;
    if (Array.isArray(k)) [t, v, e] = k as [number, number, unknown];
    else if (k && typeof k === 'object') ({ t, v, e } = k as any);
    else continue;
    if (!Number.isFinite(+t) || !Number.isFinite(+v)) continue;
    const key: Keyframe = { t: round(clamp(+t, 0, maxT), 4), v: round(clamp(+v, lo, hi), 4) };
    if (typeof e === 'string' && EASES.includes(e as Ease) && e !== 'inOut') key.e = e as Ease;
    out.push(key);
  }
  out.sort((a, b) => a.t - b.t);
  return out;
}

/** Apply a property patch to a clip, clamping every value. Unknown or invalid fields are reported. */
export function patchClip(c: Clip, props: Record<string, any>, issues: string[], p: Project) {
  const where = `clip ${c.id}`;
  for (const [k, v] of Object.entries(props)) {
    switch (k) {
      case 'op': case 'id': case 'newId': break;
      case 'start': c.start = num(v, 0, 36000, c.start); break;
      case 'dur': c.dur = num(v, 1 / p.fps, 36000, c.dur); break;
      case 'in': if (c.kind !== 'text') c.in = num(v, 0, 360000, clipIn(c)); break;
      case 'speed': if (c.kind === 'video' || c.kind === 'audio') c.speed = round(num(v, 0.1, 10, 1), 4); break;
      case 'keepPitch': c.keepPitch = !!v; break;
      case 'volume': c.volume = round(num(v, 0, 4, 1), 3); break;
      case 'fadeIn': c.fadeIn = round(num(v, 0, 60, 0), 3); break;
      case 'fadeOut': c.fadeOut = round(num(v, 0, 60, 0), 3); break;
      case 'muted': c.muted = !!v; break;
      case 'autoExposure': if (v === false) c.autoExposure = false; else delete c.autoExposure; break;
      case 'fit': if (v === 'cover' || v === 'contain') c.fit = v; else issues.push(`${where}: fit must be "cover" or "contain"`); break;
      case 'name': c.name = String(v).slice(0, 60); break;
      case 'track': {
        const t = p.tracks.find(x => x.id === v);
        if (!t) { issues.push(`${where}: no track "${v}"`); break; }
        if (t.kind !== trackKindFor(c.kind) && !(c.kind === 'video' && t.kind === 'audio')) { issues.push(`${where}: cannot go on ${t.kind} track ${t.id}`); break; }
        if (isCustom(c) && t.main) { issues.push(`${where}: graphics and effects go on an overlay track, not the main track`); break; }
        if (c.kind === 'video' && t.kind === 'audio') c.kind = 'audio';
        c.track = t.id;
        break;
      }
      case 'transform': {
        if (!v || typeof v !== 'object') break;
        const tr = { ...(c.transform || {}) };
        if ('x' in v) tr.x = round(num(v.x, -3, 3, 0), 4);
        if ('y' in v) tr.y = round(num(v.y, -3, 3, 0), 4);
        if ('scale' in v) tr.scale = round(num(v.scale, 0.02, 20, 1), 4);
        if ('rotation' in v) tr.rotation = round(num(v.rotation, -1440, 1440, 0), 3);
        if ('opacity' in v) tr.opacity = round(num(v.opacity, 0, 1, 1), 4);
        c.transform = tr;
        break;
      }
      case 'color': {
        if (!v || typeof v !== 'object') break;
        const co = { ...(c.color || {}) };
        for (const key of ['brightness', 'contrast', 'saturation', 'temperature', 'tint'] as const) if (key in v) co[key] = round(num(v[key], -1, 1, 0), 3);
        if ('hue' in v) co.hue = round(num(v.hue, -180, 180, 0), 2);
        if ('vignette' in v) co.vignette = round(num(v.vignette, 0, 1, 0), 3);
        if ('blur' in v) co.blur = round(num(v.blur, 0, 1, 0), 3);
        c.color = co;
        break;
      }
      case 'transition': {
        if (v === null || v === 'none' || v === false) { delete c.transition; break; }
        const type = typeof v === 'string' ? v : v?.type;
        if (!TRANSITIONS.includes(type)) { issues.push(`${where}: unknown transition "${type}"`); break; }
        if (type === 'logo' && p.clips.some(x => x.id !== c.id && x.transition?.type === 'logo')) { issues.push(`${where}: the voidfx logo transition is already used once in this edit`); break; }
        const dur = typeof v === 'object' && v.dur !== undefined ? num(v.dur, 0.05, 3, 0.4) : defaultTransitionDur(type);
        const pt = (q: any) => (q && typeof q === 'object' ? { x: round(clamp(num(q.x, -0.5, 1.5, 0.5), -0.5, 1.5), 4), y: round(clamp(num(q.y, -0.5, 1.5, 0.5), -0.5, 1.5), 4) } : undefined);
        const at = typeof v === 'object' ? pt(v.at) : undefined, to = typeof v === 'object' ? pt(v.to) : undefined;
        c.transition = { type: type as TransitionType, dur: round(dur, 3), ...(at ? { at } : {}), ...(to ? { to } : {}) };
        break;
      }
      case 'kf': {
        if (!v || typeof v !== 'object') break;
        const kf = { ...(c.kf || {}) };
        for (const [prop, keys] of Object.entries(v)) {
          if (!ANIM_PROPS.includes(prop as AnimProp)) { issues.push(`${where}: cannot keyframe "${prop}"`); continue; }
          if (keys === null || (Array.isArray(keys) && !keys.length)) { delete kf[prop as AnimProp]; continue; }
          const clean = sanitizeKeys(keys, prop as AnimProp, 36000);
          if (clean && clean.length) kf[prop as AnimProp] = clean;
          else issues.push(`${where}: keyframes for ${prop} must be [[t, value, ease?], ...]`);
        }
        c.kf = kf;
        break;
      }
      case 'text': if (c.kind === 'text') c.text = String(v ?? '').slice(0, 600); break;
      case 'words': {
        if (c.kind !== 'text') break;
        if (v === null) { delete c.words; break; }
        if (!Array.isArray(v)) { issues.push(`${where}: words must be an array of start times (seconds from the clip start)`); break; }
        c.words = v.map((x: unknown) => round(num(x, 0, 3600, 0), 3)).slice(0, 200);
        break;
      }
      case 'sfx': {
        if (c.kind !== 'sfx') break;
        if ((SFX as readonly string[]).includes(v)) c.sfx = v as SfxType; else issues.push(`${where}: unknown sound "${v}"`);
        break;
      }
      case 'style': {
        if (c.kind !== 'text' || !v || typeof v !== 'object') break;
        const s = { ...(c.style || {}) };
        if ('font' in v) { if (FONTS.includes(v.font)) s.font = v.font; else issues.push(`${where}: font "${v.font}" is not available`); }
        if ('weight' in v) s.weight = Math.round(num(v.weight, 100, 900, 700) / 100) * 100;
        if ('italic' in v) s.italic = !!v.italic;
        if ('size' in v) s.size = round(num(v.size, 0.01, 0.4, 0.045), 4);
        for (const key of ['color', 'strokeColor', 'bgColor'] as const) {
          if (key in v) { if (HEX.test(String(v[key]))) s[key] = String(v[key]); else issues.push(`${where}: ${key} must be a hex colour`); }
        }
        if ('stroke' in v) s.stroke = round(num(v.stroke, 0, 0.5, 0), 3);
        if ('shadow' in v) s.shadow = round(num(v.shadow, 0, 1, 0), 3);
        if ('bg' in v) s.bg = !!v.bg;
        if ('align' in v && ['left', 'center', 'right'].includes(v.align)) s.align = v.align;
        if ('uppercase' in v) s.uppercase = !!v.uppercase;
        if ('tracking' in v) s.tracking = round(num(v.tracking, -0.2, 1.5, 0), 3);
        if ('lineHeight' in v) s.lineHeight = round(num(v.lineHeight, 0.6, 2.5, 1.12), 3);
        if ('maxWidth' in v) s.maxWidth = round(num(v.maxWidth, 0.1, 1, 0.86), 3);
        if ('emphColor' in v) { if (HEX.test(String(v.emphColor))) s.emphColor = String(v.emphColor); else issues.push(`${where}: emphColor must be a hex colour`); }
        if ('emphGlow' in v) s.emphGlow = round(num(v.emphGlow, 0, 1, 0.6), 3);
        if ('scrim' in v) s.scrim = round(num(v.scrim, 0, 1, 0), 3);
        if ('fit' in v) s.fit = !!v.fit;
        if ('knockout' in v) s.knockout = !!v.knockout;
        if ('knockDark' in v) s.knockDark = round(num(v.knockDark, 0, 1, 0.82), 3);
        if ('motif' in v) { if (['blood', 'ash', 'glass', 'sparks', 'petals'].includes(v.motif)) s.motif = v.motif; else issues.push(`${where}: motif must be blood, ash, glass, sparks or petals`); }
        if ('lineScales' in v) {
          if (Array.isArray(v.lineScales)) s.lineScales = v.lineScales.slice(0, 6).map((x: unknown) => round(num(x, 0.3, 3, 1), 3));
          else if (v.lineScales === null) delete s.lineScales;
        }
        c.style = s;
        break;
      }
      case 'anim': {
        if (c.kind !== 'text' || !v || typeof v !== 'object') break;
        const a = { ...(c.anim || {}) };
        if ('in' in v) { if ((TEXT_ANIMS_IN as readonly string[]).includes(v.in)) a.in = v.in; else issues.push(`${where}: unknown text animation in "${v.in}"`); }
        if ('out' in v) { if ((TEXT_ANIMS_OUT as readonly string[]).includes(v.out)) a.out = v.out; else issues.push(`${where}: unknown text animation out "${v.out}"`); }
        if ('inDur' in v) a.inDur = round(num(v.inDur, 0, 5, 0.3), 3);
        if ('outDur' in v) a.outDur = round(num(v.outDur, 0, 5, 0.25), 3);
        c.anim = a;
        break;
      }
      case 'media': break; // fixed after creation
      case 'focus': {
        if (v === null) { delete c.focus; break; }
        if (!v || typeof v !== 'object' || c.kind === 'text' || c.kind === 'audio' || c.kind === 'sfx') break;
        c.focus = { x: round(num(v.x, 0, 1, 0.5), 3), y: round(num(v.y, 0, 1, 0.4), 3) };
        break;
      }
      case 'svg': {
        if (c.kind !== 'graphic') break;
        const r = sanitizeSvg(v);
        if ('error' in r) { issues.push(`${where}: svg rejected: ${r.error}`); break; }
        c.svg = r.svg;
        if (r.removed?.length) issues.push(`${where}: removed unsupported svg elements: ${r.removed.join(', ')}`);
        break;
      }
      case 'gw': if (c.kind === 'graphic') c.gw = round(num(v, 0.02, 3, 0.6), 4); break;
      case 'glow': if (c.kind === 'graphic') c.glow = round(num(v, 0, 1, 0), 3); break;
      case 'blend': if (BLEND_MODES.includes(v)) c.blend = v; else issues.push(`${where}: blend must be ${BLEND_MODES.join(', ')}`); break;
      case 'reveal': {
        if (!v || typeof v !== 'object' || c.kind !== 'graphic') break;
        const r = { ...(c.reveal || {}) };
        if (v.in !== undefined) { if ((REVEALS_IN as readonly string[]).includes(v.in)) r.in = v.in; else issues.push(`${where}: reveal.in must be ${REVEALS_IN.join(', ')}`); }
        if (v.out !== undefined) { if ((REVEALS_OUT as readonly string[]).includes(v.out)) r.out = v.out; else issues.push(`${where}: reveal.out must be ${REVEALS_OUT.join(', ')}`); }
        if (v.inDur !== undefined) r.inDur = round(num(v.inDur, 0, 10, 0.25), 3);
        if (v.outDur !== undefined) r.outDur = round(num(v.outDur, 0, 10, 0.2), 3);
        c.reveal = r;
        break;
      }
      case 'code': {
        if (c.kind !== 'shader') break;
        const r = checkShaderCode(v);
        if (r.issues.length) { issues.push(`${where}: effect code rejected: ${r.issues.join('; ')}`); break; }
        c.code = r.code;
        if (c.preset && r.code !== fxCode(getFx(c.preset)!, c.params || {})) { delete c.preset; delete c.params; }
        break;
      }
      case 'preset': {
        if (c.kind !== 'shader') break;
        const def = getFx(String(v));
        if (!def) { issues.push(`${where}: unknown effect preset "${v}" (see the effect library)`); break; }
        c.preset = def.id;
        c.params = fxParams(def, c.params);
        c.code = fxCode(def, c.params);
        if (!('blend' in props)) c.blend = def.blend;
        break;
      }
      case 'params': {
        if (c.kind !== 'shader' || !v || typeof v !== 'object') break;
        const def = c.preset ? getFx(c.preset) : undefined;
        if (!def) { c.params = { ...(c.params || {}), ...v }; break; }
        const unknown = Object.keys(v).filter(k2 => !def.params.some(p2 => p2.id === k2));
        if (unknown.length) issues.push(`${where}: ${def.id} has no parameter ${unknown.join(', ')} (it takes ${def.params.map(p2 => p2.id).join(', ')})`);
        c.params = fxParams(def, { ...(c.params || {}), ...v });
        c.code = fxCode(def, c.params);
        break;
      }
      case 'at': {
        // an anchor point in frame coordinates (0..1 from the top-left) for effects, graphics and text
        if (!v || typeof v !== 'object' || c.kind === 'audio' || c.kind === 'sfx') break;
        c.transform = { ...(c.transform || {}), x: round(num(v.x, -1, 2, 0.5) - 0.5, 4), y: round(num(v.y, -1, 2, 0.5) - 0.5, 4) };
        break;
      }
      case 'span': if (v === 'all') c.span = 'all'; else delete c.span; break;
      case 'over': break; // handled by the fx operation
      default: issues.push(`${where}: unknown field "${k}"`);
    }
  }
}

// ---------- sound effects, beat camera, speed ramps ----------

export function sanitizeCamera(v: any, issues: string[]): Project['camera'] {
  if (v === null || v === false) return undefined;
  if (v === true) return { ...DEFAULT_CAMERA };
  if (!v || typeof v !== 'object') { issues.push('camera must be an object'); return undefined; }
  const cam = { ...DEFAULT_CAMERA, on: v.on !== false };
  if ('every' in v) { if (['beat', 'half', 'downbeat'].includes(v.every)) cam.every = v.every; else issues.push('camera.every must be beat, half or downbeat'); }
  if ('punch' in v) cam.punch = round(num(v.punch, 0, 0.3, DEFAULT_CAMERA.punch), 4);
  if ('kick' in v) cam.kick = round(num(v.kick, 0, 10, DEFAULT_CAMERA.kick), 3);
  if ('decay' in v) cam.decay = round(num(v.decay, 0.03, 1, DEFAULT_CAMERA.decay), 3);
  if ('from' in v && v.from !== null) cam.from = round(num(v.from, 0, 36000, 0), 3);
  if ('to' in v && v.to !== null) cam.to = round(num(v.to, 0, 36000, 0), 3);
  if (Array.isArray(v.sections)) {
    const secs: NonNullable<BeatCamera['sections']> = [];
    for (const x of v.sections.slice(0, 12)) {
      if (!x || typeof x !== 'object') continue;
      const from = round(num(x.from, 0, 36000, 0), 3), to = round(num(x.to, 0, 36000, 0), 3);
      if (to <= from) { issues.push(`camera section ${from}-${to}: "to" must be after "from"`); continue; }
      const sec: NonNullable<BeatCamera['sections']>[number] = { from, to };
      if ('punch' in x) sec.punch = round(num(x.punch, 0, 0.3, cam.punch), 4);
      if ('kick' in x) sec.kick = round(num(x.kick, 0, 10, cam.kick), 3);
      if (['beat', 'half', 'downbeat'].includes(x.every)) sec.every = x.every;
      secs.push(sec);
    }
    if (secs.length) cam.sections = secs.sort((a, b) => a.from - b.from);
  } else if (v.sections === null) delete cam.sections;
  return cam;
}

/** Add a generated sound effect clip on a free audio track (an 'SFX' track is created if needed). */
export function addSfx(p: Project, type: SfxType, start: number, opts: { volume?: number; id?: string; name?: string; track?: string } = {}): Clip {
  const dur = SFX_INFO[type].dur;
  let at = Math.max(0, start), inPt = 0;
  if (start < 0) { inPt = -start; at = 0; }
  const c: Clip = { id: opts.id || newClipId(p, 'audio'), track: '', kind: 'sfx', sfx: type, start: round(at, 4), dur: round(Math.max(0.02, dur - inPt), 4), in: round(inPt, 4), volume: opts.volume ?? 0.35 };
  if (opts.name) c.name = opts.name;
  let tr = opts.track ? p.tracks.find(t => t.id === opts.track && t.kind === 'audio') : undefined;
  if (!tr || !isFree(p, tr.id, c.start, c.dur)) {
    tr = p.tracks.find(t => t.kind === 'audio' && t.name.startsWith('SFX') && isFree(p, t.id, c.start, c.dur));
    if (!tr) tr = addTrack(p, 'audio', undefined, `SFX ${p.tracks.filter(t => t.name.startsWith('SFX')).length + 1}`);
  }
  c.track = tr.id;
  p.clips.push(c);
  return c;
}

/** Joins that do not get a sound of their own: soft or plain moves that should stay invisible. */
export const QUIET_TRANSITIONS = new Set<string>(['crossfade', 'dip_black', 'dip_white', 'blur', 'slide_left', 'slide_right', 'slide_up', 'slide_down', 'push_left', 'push_right', 'push_up', 'push_down', 'wipe_left', 'wipe_right', 'wipe_up', 'wipe_down']);

/** The sound budget for an edit of `dur` seconds: about three effects every four seconds at most. */
export const sfxBudget = (dur: number) => Math.max(6, Math.ceil(dur * 0.75));

/**
 * Sounds for the designed transitions only (signature moves, whips, impacts), placed so they peak on
 * the cut, at most one every ~0.9 s and never stacked: sound design that supports the music rather
 * than clicking on every cut. Earlier automatic sounds are replaced.
 */
export function addTransitionSounds(p: Project, volume = 0.3): number {
  p.clips = p.clips.filter(c => !(c.kind === 'sfx' && c.name?.startsWith('auto:')));
  const taken = p.clips.filter(c => c.kind === 'sfx').map(sfxPeakAt);
  const free = (t: number, gap: number) => !taken.some(x => Math.abs(x - t) < gap);
  let n = 0;
  const trans = p.clips.filter(c => c.transition && !QUIET_TRANSITIONS.has(c.transition.type)).sort((a, b) => a.start - b.start);
  for (const c of trans) {
    const set = soundsForTransition(c.transition!.type, c.transition!.dur);
    // the main hit of the transition decides whether there is room for its sound
    const main = set[set.length - 1];
    if (!main || !free(c.start + main[1] + SFX_PEAK[main[0]], 0.9)) continue;
    for (const [type, off] of set) {
      const peak = c.start + off + SFX_PEAK[type];
      if (!free(peak, 0.35)) continue;
      addSfx(p, type, c.start + off, { volume: type === 'boom' || type === 'impact' || type === 'subdrop' ? volume * 1.15 : volume, name: `auto:${c.id}` });
      taken.push(peak);
      n++;
    }
  }
  return n;
}

/** Sound effects grouped by when they peak: sounds peaking within 60 ms of each other are one layered event. */
export function sfxEvents(p: Project): { t: number; clips: Clip[] }[] {
  const list = p.clips.filter(c => c.kind === 'sfx' && c.sfx).map(c => ({ c, t: sfxPeakAt(c) })).sort((a, b) => a.t - b.t);
  const ev: { t: number; clips: Clip[] }[] = [];
  for (const x of list) {
    const last = ev[ev.length - 1];
    if (last && x.t - last.t < 0.06) last.clips.push(x.c); else ev.push({ t: x.t, clips: [x.c] });
  }
  return ev;
}

/**
 * Thin out sound effects: at most two layers per moment, no two moments within 0.3 s of each other,
 * and no more than the budget for the edit's length (automatic sounds go first, then the quietest).
 */
export function pruneSfx(p: Project): number {
  const drop = new Set<string>();
  const auto = (c: Clip) => !!c.name?.startsWith('auto:');
  const rank = (a: Clip, b: Clip) => Number(auto(a)) - Number(auto(b)) || (b.volume ?? 1) - (a.volume ?? 1);
  const kept: { t: number; clips: Clip[] }[] = [];
  for (const e of sfxEvents(p)) {
    const layers = [...e.clips].sort(rank);
    for (const c of layers.slice(2)) drop.add(c.id);
    const ev = { t: e.t, clips: layers.slice(0, 2) };
    const prev = kept[kept.length - 1];
    if (prev && ev.t - prev.t < 0.3) {
      // keep the owner's or Opus's own sound over an automatic one, else the earlier
      const prevAuto = prev.clips.every(auto), evAuto = ev.clips.every(auto);
      if (prevAuto && !evAuto) { for (const c of prev.clips) drop.add(c.id); kept[kept.length - 1] = ev; }
      else for (const c of ev.clips) drop.add(c.id);
      continue;
    }
    // at most two moments in any second
    const prev2 = kept[kept.length - 2];
    if (prev2 && ev.t - prev2.t < 1) {
      const evAuto = ev.clips.every(auto), midAuto = prev!.clips.every(auto);
      if (midAuto && !evAuto) { for (const c of prev!.clips) drop.add(c.id); kept[kept.length - 1] = ev; }
      else for (const c of ev.clips) drop.add(c.id);
      continue;
    }
    kept.push(ev);
  }
  const cap = sfxBudget(projectDuration(p));
  if (kept.length > cap) {
    const order = [...kept].sort((a, b) => Number(b.clips.every(auto)) - Number(a.clips.every(auto)) || Math.max(...a.clips.map(c => c.volume ?? 1)) - Math.max(...b.clips.map(c => c.volume ?? 1)));
    for (const e of order.slice(0, kept.length - cap)) for (const c of e.clips) drop.add(c.id);
  }
  // layers count too: about one sound per second of edit in total
  const left = kept.flatMap(e => e.clips).filter(c => !drop.has(c.id));
  const maxClips = Math.max(8, Math.ceil(projectDuration(p) * 0.9));
  if (left.length > maxClips) {
    const second = kept.filter(e => e.clips.length > 1).map(e => [...e.clips].sort(rank)[1]).filter(c => !drop.has(c.id));
    const order = [...second.filter(auto), ...left.filter(c => auto(c) && !second.includes(c)), ...second.filter(c => !auto(c)).sort((a, b) => (a.volume ?? 1) - (b.volume ?? 1))];
    for (const c of order.slice(0, left.length - maxClips)) drop.add(c.id);
  }
  if (drop.size) {
    pruned = p.clips.filter(c => drop.has(c.id)).map(c => `${c.sfx || 'sound'} at ${c.start.toFixed(2)} s (${c.id})`);
    p.clips = p.clips.filter(c => !drop.has(c.id));
  } else pruned = [];
  return drop.size;
}
/** The sounds the last pruneSfx removed, for the report. */
let pruned: string[] = [];
export const lastPruned = () => pruned;

/**
 * Put main-track cuts exactly on the music's beats when they are within `tol` seconds of one, and
 * carry text, effects, graphics, overlays and sounds along with the cuts they belong to.
 */
export function snapToBeats(p: Project, media: Record<string, MediaInfo>, tol = 0.09): number {
  const beats = timelineBeats(p, media).map(b => b.t);
  const main = mainTrack(p);
  if (beats.length < 4 || !main) return 0;
  const list = trackClips(p, main.id);
  if (list.length < 2) return 0;
  const minDur = 2 / (p.fps || 30);
  const oldB: number[] = [list[0].start], newB: number[] = [list[0].start];
  let t = list[0].start, moved = 0;
  for (let i = 0; i < list.length; i++) {
    const c = list[i];
    const oldEnd = c.start + c.dur;
    let end = t + c.dur;
    if (i < list.length - 1) {
      let best = Infinity, bt = end;
      for (const b of beats) { const d = Math.abs(b - end); if (d < best) { best = d; bt = b; } }
      if (best > 0.004 && best <= tol && bt - t >= minDur && bt - t <= mediaLimit(c, media) + 1e-6) { end = bt; moved++; }
    }
    c.start = round(t, 4);
    c.dur = round(end - t, 4);
    t = end;
    oldB.push(oldEnd); newB.push(end);
  }
  if (!moved) return 0;
  const map = (x: number) => {
    if (x <= oldB[0]) return x + (newB[0] - oldB[0]);
    for (let k = 1; k < oldB.length; k++) {
      if (x <= oldB[k]) { const a = oldB[k - 1], b = oldB[k]; const f = b > a ? (x - a) / (b - a) : 0; return newB[k - 1] + f * (newB[k] - newB[k - 1]); }
    }
    return x + (newB[newB.length - 1] - oldB[oldB.length - 1]);
  };
  for (const c of p.clips) {
    // lyric captions belong to the song, which does not move
    if (c.track === main.id || c.kind === 'audio' || c.name?.startsWith('lyric L')) continue;
    if (c.kind === 'video' && p.tracks.find(t => t.id === c.track)?.kind === 'audio') continue;
    const s0 = map(c.start);
    if (c.kind !== 'sfx') c.dur = round(Math.max(minDur, map(c.start + c.dur) - s0), 4);
    c.start = round(Math.max(0, s0), 4);
  }
  return moved;
}

/** Speed ramp synced to the music: a burst on every beat, slow motion between (the v10 motion pass). */
export function velocityRamp(p: Project, media: Record<string, MediaInfo>, c: Clip, opts: { fast?: number; slow?: number; burst?: number } = {}): boolean {
  if (c.kind !== 'video') return false;
  const fast = opts.fast ?? 2.2, slow = opts.slow ?? 0.45, burst = opts.burst ?? 0.18;
  // the beat the clip is cut on counts too: a short shot between two beats bursts on its own cut
  const beats = timelineBeats(p, media).map(b => b.t - c.start).filter(lt => lt > -0.03 && lt < c.dur - 0.05);
  if (!beats.length) return false;
  const onCut = beats[0] <= 0.02;
  const keys: { t: number; v: number; e?: 'out' | 'hold' }[] = onCut ? [] : [{ t: 0, v: slow, e: 'hold' }];
  for (const lb0 of beats) {
    const lb = Math.max(0, lb0);
    keys.push({ t: round(lb, 4), v: fast, e: 'out' });
    keys.push({ t: round(Math.min(c.dur, lb + burst), 4), v: slow, e: 'hold' });
  }
  const kf = { ...(c.kf || {}), speed: keys };
  const probe: Clip = { ...c, kf };
  const m = c.media ? media[c.media] : undefined;
  if (m?.duration) {
    const avail = m.duration - clipIn(c) - 0.05;
    const used = srcAt(probe, c.dur) - clipIn(c);
    if (used > avail && used > 0) {
      const k = Math.max(0.05, avail / used);
      for (const key of keys) key.v = round(Math.max(0.05, key.v * k), 3);
    }
  }
  c.kf = kf;
  return true;
}

/** The song bed: the longest clip on an audio track whose file has a sound analysis. */
export function musicClip(p: Project, media: Record<string, MediaInfo>): Clip | undefined {
  const audioTracks = new Set(p.tracks.filter(t => t.kind === 'audio').map(t => t.id));
  return p.clips.filter(c => (c.kind === 'audio' || (c.kind === 'video' && audioTracks.has(c.track))) && c.media && media[c.media]?.analysis)
    .sort((a, b) => b.dur - a.dur)[0];
}

/**
 * Captions for timed lyric lines, each on its sung time through the music clip (song time → timeline
 * time), in the house caption style. Re-running a line replaces its caption.
 */
function placeLyrics(p: Project, media: Record<string, MediaInfo>, op: any, tag: string, issues: string[], touched: string[]): boolean {
  const L = p.lyrics;
  if (!L?.lines.length) { issues.push(`${tag}: this project has no lyrics (the owner pastes them when creating the edit)`); return false; }
  if (!L.timed) { issues.push(`${tag}: the lyrics have no times, so lines cannot be placed on their sung time; caption nothing, or use a designed title on an obvious hit`); return false; }
  const mus = (typeof op.music === 'string' ? p.clips.find(c => c.id === op.music) : undefined) || musicClip(p, media);
  if (!mus) { issues.push(`${tag}: add the music clip before placing lyrics`); return false; }
  const n = L.lines.length;
  let idx: number[] = Array.isArray(op.lines) ? op.lines.map((x: any) => Math.round(+x)) : [];
  if (!idx.length) {
    const a = Math.round(num(op.from, 1, n, 1)), b = Math.round(num(op.to, a, n, n));
    for (let i = a; i <= b; i++) idx.push(i);
  }
  const missing = idx.filter(i => !(i >= 1 && i <= n));
  if (missing.length) issues.push(`${tag}: there is no lyric line ${missing.join(', ')} (lines run L1-L${n})`);
  idx = [...new Set(idx)].filter(i => i >= 1 && i <= n).sort((a, b) => a - b).slice(0, 60);
  const rate = num(op.rate, 0.25, 4, 1), shift = num(op.shift, -30, 30, 0);
  const sp = clipSpeed(mus), mIn = clipIn(mus), mEnd = clipEnd(mus);
  const toTl = (s: number) => mus.start + (s / rate + shift - mIn) / sp;
  const lead = num(op.lead, 0, 0.5, 0.06), hold = num(op.hold, 0.6, 8, 3.6);
  const texts = op.text && typeof op.text === 'object' ? op.text : {};
  let track = op.track ? p.tracks.find(t => t.id === op.track && t.kind === 'text') : p.tracks.find(t => t.kind === 'text');
  if (!track) track = addTrack(p, 'text');
  const outside: number[] = [];
  let placed = 0;
  for (const i of idx) {
    const line = L.lines[i - 1];
    const t0 = toTl(line.t);
    if (t0 < mus.start - 0.01 || t0 > mEnd - 0.3) { outside.push(i); continue; }
    const nextT = L.lines[i] ? toTl(L.lines[i].t) : Infinity;
    const lineEnd = line.end !== undefined ? toTl(line.end) : nextT;
    const start = Math.max(0, t0 - lead);
    let end = Math.min(lineEnd + 0.15, nextT - 0.04, t0 + hold, mEnd);
    if (end - start < 0.45) end = Math.min(start + 0.45, mEnd);
    const id = `ly${i}`;
    p.clips = p.clips.filter(c => c.id !== id);
    const text = typeof texts[i] === 'string' && texts[i].trim() ? String(texts[i]).slice(0, 300) : twoLines(line.text);
    const nWords = text.split(/\s+/).filter(Boolean).length;
    const words = line.words && line.words.length === nWords
      ? line.words.map(w => round(Math.max(0, toTl(w) - start), 3))
      : Array.from({ length: nWords }, (_, k) => round(lead + k * Math.min(0.11, ((end - start) * 0.45) / Math.max(1, nWords)), 3));
    const c: Clip = {
      id, track: track.id, kind: 'text', start: round(start, 4), dur: round(end - start, 4), text, words, name: `lyric L${i}`,
      style: { ...STANDARD_CAPTION }, anim: { in: 'words', out: 'cap', inDur: 0.3, outDur: 0.24 }, transform: { x: 0, y: 0.25, scale: 1, rotation: 0, opacity: 1 },
    };
    patchClip(c, { ...(op.style ? { style: op.style } : {}), ...(op.anim ? { anim: op.anim } : {}), ...(op.transform ? { transform: op.transform } : {}) }, issues, p);
    if (!isFree(p, c.track, c.start, c.dur, c.id)) c.track = freeTrack(p, 'text', c.start, c.dur, track.id, c.id).id;
    p.clips.push(c);
    touched.push(c.id);
    placed++;
  }
  if (outside.length) issues.push(`${tag}: lines ${outside.join(', ')} are sung outside the part of the song on the timeline (music clip ${mus.id} plays song ${mIn.toFixed(2)}-${(mIn + mus.dur * sp).toFixed(2)} s), so they were not placed`);
  return placed > 0;
}

// ---------- Opus operations ----------

export interface OpsResult { project: Project; applied: number; issues: string[]; touched: string[]; /** applied operations per note id they were tagged with */ notes?: Record<string, number> }

/** Apply a list of edit operations (the format Opus writes). Invalid operations are skipped and reported. */
export function applyOps(base: Project, rawOps: unknown, media: Record<string, MediaInfo>): OpsResult {
  const p = deepClone(base);
  const issues: string[] = [];
  const touched: string[] = [];
  let applied = 0;
  const ops = Array.isArray(rawOps) ? rawOps : [];
  const pendingRamps: [string, any][] = [];
  if (!Array.isArray(rawOps)) issues.push('ops must be an array');
  const noteOps: Record<string, number> = {};
  const alias = new Map<string, string>();
  // a queue: a set piece expands into its operations right after itself
  const queue: any[] = ops.slice(0, 2000);
  const step = (op: any, i: number) => {
    const tag = `op ${i + 1}`;
    if (!op || typeof op !== 'object' || typeof op.op !== 'string') { issues.push(`${tag}: not an operation`); return; }
    // "note": which of the round's numbered notes this operation serves (counted, not applied)
    // an id the reply asks for that is already taken: the new clip gets another one, and later operations in
    // this reply that name it go to the new clip (they mean the one they just made)
    const claim = (c: Clip) => {
      if (typeof op.id !== 'string' || !/^[A-Za-z][\w-]{0,23}$/.test(op.id)) return;
      if (!allIds(p).has(op.id)) { c.id = op.id; return; }
      const other = p.clips.find(x => x.id === op.id);
      alias.set(op.id, c.id);
      issues.push(`${tag}: id "${op.id}" already belongs to ${other ? `the ${other.kind} clip at ${other.start.toFixed(2)} s` : 'a track'}, so this new ${c.kind} clip is "${c.id}"; later operations in this reply that name "${op.id}" were applied to it`);
    };
    if ((op.op === 'set' || op.op === 'remove' || op.op === 'split') && typeof op.id === 'string' && alias.has(op.id)) op = { ...op, id: alias.get(op.id) };
    if (op.op === 'remove' && Array.isArray(op.ids)) op = { ...op, ids: op.ids.map((x: unknown) => alias.get(String(x)) ?? x) };
    let noteIds: string[] = [];
    if ('note' in op) {
      const raw = Array.isArray(op.note) ? op.note : [op.note];
      noteIds = raw.map((x: unknown) => String(x ?? '').trim().toUpperCase()).filter((x: string) => /^[A-Z]{1,2}\d{1,3}[A-Z]?$/.test(x)).slice(0, 6);
      const { note: _n, ...rest } = op;
      op = rest;
    }
    const before = applied;
    try {
      switch (op.op) {
        case 'clear': {
          const fresh = newProject();
          p.clips = [];
          p.tracks = fresh.tracks;
          applied++;
          break;
        }
        case 'project': {
          if ('name' in op) p.name = String(op.name).slice(0, 80) || p.name;
          if ('width' in op || 'height' in op) {
            const w = Math.round(num(op.width, 240, 4096, p.width) / 2) * 2;
            const h = Math.round(num(op.height, 240, 4096, p.height) / 2) * 2;
            p.width = w; p.height = h;
          }
          if ('fps' in op) p.fps = [24, 25, 30, 48, 50, 60].includes(+op.fps) ? +op.fps : p.fps;
          if ('background' in op && HEX.test(String(op.background))) p.background = String(op.background);
          if ('camera' in op) p.camera = sanitizeCamera(op.camera, issues);
          if ('exposure' in op) {
            const v = op.exposure;
            if (v === null || v === false) delete p.exposure;
            else if (v === true) p.exposure = { auto: true, target: 0.34 };
            else if (v && typeof v === 'object') p.exposure = { auto: v.auto !== false, target: round(num(v.target, 0.15, 0.6, p.exposure?.target ?? 0.34), 3) };
          }
          applied++;
          break;
        }
        case 'track': {
          const kind = op.kind as TrackKind;
          const existing = p.tracks.find(t => t.id === op.id);
          if (existing) {
            if ('name' in op) existing.name = String(op.name).slice(0, 40);
            if ('muted' in op) existing.muted = !!op.muted;
            if ('hidden' in op) existing.hidden = !!op.hidden;
          } else {
            if (!['video', 'audio', 'text'].includes(kind)) { issues.push(`${tag}: track kind must be video, audio or text`); return; }
            const id = typeof op.id === 'string' && /^[A-Za-z][\w-]{0,15}$/.test(op.id) ? op.id : undefined;
            const t = addTrack(p, kind, id, op.name ? String(op.name).slice(0, 40) : undefined);
            if (op.muted) t.muted = true;
          }
          applied++;
          break;
        }
        case 'add': {
          const m = media[op.media];
          if (!m) { issues.push(`${tag}: unknown media "${op.media}"`); return; }
          if (m.status === 'error') { issues.push(`${tag}: media ${m.id} could not be read`); return; }
          if (op.track === '@overlay') op = { ...op, track: freeTrack(p, 'video', num(op.start, 0, 36000, 0), num(op.dur, 0.05, 36000, 1)).id };
          let track = op.track ? p.tracks.find(t => t.id === op.track) : undefined;
          if (op.track && !track) { issues.push(`${tag}: no track "${op.track}" (add it with a track op first)`); return; }
          const asAudio = m.kind === 'audio' || track?.kind === 'audio';
          if (!track) track = asAudio ? p.tracks.find(t => t.kind === 'audio') : mainTrack(p);
          if (!track) { issues.push(`${tag}: no track for this clip`); return; }
          if (track.kind === 'text') { issues.push(`${tag}: media cannot go on text track ${track.id}`); return; }
          if (m.kind === 'audio' && track.kind !== 'audio') { issues.push(`${tag}: audio media must go on an audio track`); return; }
          const c = makeMediaClip(p, m, 0, track.id, asAudio);
          claim(c);
          c.start = 'start' in op ? num(op.start, 0, 36000, 0) : (track.main ? 1e6 : 0);
          c.in = num(op.in, 0, Math.max(0, m.duration - 0.01), 0);
          const sp = 'speed' in op ? num(op.speed, 0.1, 10, 1) : 1;
          const rest = m.kind === 'image' ? 3 : Math.max(1 / p.fps, (m.duration - c.in) / sp);
          c.dur = 'dur' in op ? num(op.dur, 1 / p.fps, 36000, rest) : rest;
          const { op: _o, media: _m, track: _t, start: _s, in: _i, dur: _d, id: _id, ramp: _r, ...rest2 } = op;
          patchClip(c, rest2, issues, p);
          if (op.ramp) pendingRamps.push([c.id, op.ramp]);
          if (m.kind !== 'image' && c.dur > (m.duration - (c.in ?? 0)) / clipSpeed(c) + 0.05) {
            issues.push(`${tag}: ${m.id} is ${m.duration.toFixed(2)}s long, so clip ${c.id} was shortened to fit`);
          }
          p.clips.push(c);
          touched.push(c.id);
          applied++;
          break;
        }
        case 'text': {
          let track = op.track ? p.tracks.find(t => t.id === op.track) : p.tracks.find(t => t.kind === 'text');
          if (!track || track.kind !== 'text') { issues.push(`${tag}: "${op.track}" is not a text track`); return; }
          const c: Clip = { id: newClipId(p, 'text'), track: track.id, kind: 'text', start: num(op.start, 0, 36000, 0), dur: num(op.dur, 1 / p.fps, 36000, 2), text: '' };
          claim(c);
          const { op: _o, track: _t, start: _s, dur: _d, id: _id, ...rest } = op;
          patchClip(c, rest, issues, p);
          if (!c.text) { issues.push(`${tag}: text clip without text was skipped`); return; }
          p.clips.push(c);
          touched.push(c.id);
          applied++;
          break;
        }
        case 'look': case 'fx': {
          const def = getFx(String(op.preset ?? op.look ?? op.fx ?? ''));
          if (!def) { issues.push(`${tag}: unknown ${op.op} "${op.preset ?? op.look ?? op.fx}" (looks: ${FX_LIBRARY.filter(d => d.group === 'look').map(d => d.id).join(', ')}; effects: see the library)`); return; }
          const isLook = op.op === 'look';
          const start = num(op.start, 0, 36000, 0);
          const whole = isLook && op.dur === undefined;
          const dur = whole ? Math.max(1, projectDuration(p) - start) : num(op.dur, 1 / p.fps, 36000, def.dur);
          let track: Track;
          if (isLook) {
            track = lookTrack(p);
            // one look at a time: a new look replaces the ones it overlaps
            const end = start + dur;
            p.clips = p.clips.filter(c => !(c.track === track.id && (whole || (c.start < end - EPS && c.start + c.dur > start + EPS))));
          } else track = fxTrack(p, start, dur, typeof op.track === 'string' ? op.track : undefined, undefined, op.over === true);
          const c: Clip = { id: newClipId(p, 'shader'), track: track.id, kind: 'shader', start, dur, blend: def.blend, preset: def.id, name: def.name };
          if (whole) c.span = 'all';
          claim(c);
          c.params = fxParams(def, op.params && typeof op.params === 'object' ? op.params : undefined);
          if (op.params && typeof op.params === 'object') {
            const unknown = Object.keys(op.params).filter(k => !def.params.some(q => q.id === k));
            if (unknown.length) issues.push(`${tag}: ${def.id} has no parameter ${unknown.join(', ')} (it takes ${def.params.map(q => q.id).join(', ') || 'none'})`);
          }
          c.code = fxCode(def, c.params);
          const { op: _o, track: _t, start: _s, dur: _d, id: _id, preset: _p, params: _pa, look: _l, fx: _f, over: _ov, ...rest } = op;
          patchClip(c, rest, issues, p);
          p.clips.push(c);
          touched.push(c.id);
          applied++;
          break;
        }
        case 'graphic': case 'shader': {
          const kind = op.op as 'graphic' | 'shader';
          const start = num(op.start, 0, 36000, 0), dur = num(op.dur, 1 / p.fps, 36000, 1);
          const pref = typeof op.track === 'string' ? op.track : undefined;
          const prefT = pref ? p.tracks.find(t => t.id === pref) : undefined;
          if (pref && (!prefT || prefT.kind !== 'video' || prefT.main)) issues.push(`${tag}: ${kind}s go on an overlay video track; used a free one instead of "${pref}"`);
          const track = fxTrack(p, start, dur, prefT && prefT.kind === 'video' && !prefT.main ? prefT.id : undefined);
          const c: Clip = { id: newClipId(p, kind), track: track.id, kind, start, dur };
          claim(c);
          if (kind === 'graphic') { c.gw = 0.6; c.blend = 'normal'; } else c.blend = 'normal';
          const { op: _o, track: _t, start: _s, dur: _d, id: _id, ...rest } = op;
          patchClip(c, rest, issues, p);
          if (kind === 'graphic' && !c.svg) { issues.push(`${tag}: graphic without a usable svg was skipped`); return; }
          if (kind === 'shader' && !c.code) { issues.push(`${tag}: effect without usable code was skipped`); return; }
          p.clips.push(c);
          touched.push(c.id);
          applied++;
          break;
        }
        case 'set': {
          const c = p.clips.find(x => x.id === op.id);
          if (!c) { issues.push(`${tag}: no clip "${op.id}"`); return; }
          const { op: _o, id: _id, ramp: _r, ...rest } = op;
          patchClip(c, rest, issues, p);
          if (op.ramp) pendingRamps.push([c.id, op.ramp]);
          touched.push(c.id);
          applied++;
          break;
        }
        case 'sfx': {
          const type = op.sound ?? op.sfx;
          if (!(SFX as readonly string[]).includes(type)) { issues.push(`${tag}: unknown sound "${type}" (use ${SFX.join(', ')})`); return; }
          const c = addSfx(p, type, num(op.start, -10, 36000, 0), { volume: op.volume !== undefined ? num(op.volume, 0, 4, 0.35) : undefined, track: op.track });
          claim(c);
          if (op.dur !== undefined) c.dur = num(op.dur, 0.02, c.dur, c.dur);
          touched.push(c.id);
          applied++;
          break;
        }
        case 'piece': {
          const sub = expandPiece(p, op, issues, tag);
          if (sub.length) { queue.splice(i + 1, 0, ...sub); applied++; }
          break;
        }
        case 'loop': {
          // land the loop: a twin of the first shot (same file, framing, colour) dissolves in over the last
          // seconds and ends on exactly the source frame frame 0 opens on
          normalize(p, media, { resolveOverlaps: false });
          const mainT = p.tracks.find(t => t.main);
          const shots = p.clips.filter(c => c.track === mainT?.id).sort((a, b) => a.start - b.start);
          const first = shots[0];
          const m = first?.media ? media[first.media] : undefined;
          if (!first || !m || first.kind !== 'video' && first.kind !== 'image') { issues.push(`${tag}: the loop needs a video or image shot first on the main track`); return; }
          const end = projectDuration(p);
          const d = num(op.dur, 0.1, 2, 0.4);
          p.clips = p.clips.filter(c => c.name !== 'loop twin');
          const tr = freeTrack(p, 'video', end - d, d);
          const tw = makeMediaClip(p, m, round(end - d, 4), tr.id);
          tw.dur = round(d, 4);
          tw.name = 'loop twin';
          const s1 = first.speed ?? 1, in0 = first.in ?? 0;
          if (first.kind === 'video') {
            const sp = in0 >= d * s1 ? s1 : Math.max(0.1, in0 / d);
            tw.speed = round(sp, 4);
            tw.in = round(Math.max(0, in0 - d * sp), 4);
            tw.muted = true;
          }
          for (const k of ['focus', 'fit', 'transform', 'color', 'autoExposure'] as const) if (first[k] !== undefined) (tw as any)[k] = deepClone(first[k]);
          tw.kf = { opacity: [{ t: 0, v: 0, e: 'inOut' }, { t: round(d, 4), v: 1 }] };
          p.clips.push(tw);
          touched.push(tw.id);
          applied++;
          break;
        }
        case 'sounds': {
          // pack the main track first so sounds land on the real cut times
          normalize(p, media, { resolveOverlaps: false });
          const n = addTransitionSounds(p, op.volume !== undefined ? num(op.volume, 0, 2, 0.35) : 0.35);
          if (!n) issues.push(`${tag}: there are no transitions to give sounds to yet`);
          applied++;
          break;
        }
        case 'lyrics': {
          // pack the main track first so captions sit on the final song position
          normalize(p, media, { resolveOverlaps: false });
          if (placeLyrics(p, media, op, tag, issues, touched)) applied++;
          break;
        }
        case 'remove': {
          const ids: string[] = Array.isArray(op.ids) ? op.ids.map(String) : [String(op.id)];
          const before = p.clips.length;
          deleteClips(p, ids);
          if (p.clips.length === before) { issues.push(`${tag}: nothing to remove for ${ids.join(', ')}`); return; }
          applied++;
          break;
        }
        case 'split': {
          const c = p.clips.find(x => x.id === op.id);
          if (!c) { issues.push(`${tag}: no clip "${op.id}"`); return; }
          const at = num(op.at, 0, 36000, -1);
          const b = splitClipAt(p, c.id, at);
          if (!b) { issues.push(`${tag}: split time ${op.at} is not inside clip ${c.id} (${c.start.toFixed(2)}-${clipEnd(c).toFixed(2)})`); return; }
          if (typeof op.newId === 'string' && /^[A-Za-z][\w-]{0,23}$/.test(op.newId) && !allIds(p).has(op.newId)) b.id = op.newId;
          touched.push(c.id, b.id);
          applied++;
          break;
        }
        default:
          issues.push(`${tag}: unknown op "${op.op}"`);
      }
    } catch (e: any) {
      issues.push(`${tag}: ${e?.message || 'failed'}`);
    }
    if (applied > before && noteIds.length) for (const n of noteIds) noteOps[n] = (noteOps[n] || 0) + 1;
  };
  for (let i = 0; i < queue.length && i < 4000; i++) step(queue[i], i);
  if (ops.length > 2000) issues.push('only the first 2000 operations were applied');
  normalize(p, media, { pruneTracks: true, resolveOverlaps: false });
  // velocity ramps need final positions and the music's beats
  for (const [id, r] of pendingRamps) {
    const c = p.clips.find(x => x.id === id);
    if (!c) continue;
    if (r === null || r === false) { if (c.kf) delete c.kf.speed; continue; }
    const o = typeof r === 'object' ? r : {};
    const ok = velocityRamp(p, media, c, { fast: o.fast !== undefined ? num(o.fast, 0.2, 8, 2.2) : undefined, slow: o.slow !== undefined ? num(o.slow, 0.05, 2, 0.45) : undefined, burst: o.burst !== undefined ? num(o.burst, 0.04, 1, 0.18) : undefined });
    if (!ok) issues.push(`clip ${id}: no music beats fall inside it, so the velocity ramp was skipped (add a music clip on an audio track first)`);
  }
  normalize(p, media, { pruneTracks: true });
  return { project: p, applied, issues, touched, notes: noteOps };
}
