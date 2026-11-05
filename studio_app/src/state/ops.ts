// Edit operations shared by the UI and the Opus Director. Every change is validated here so the
// timeline can never hold out-of-range values, overlapping clips or dangling references.
import {
  ANIM_PROPS, AnimProp, Clip, ClipKind, Ease, FONTS, Keyframe, MediaInfo, Project, TEXT_ANIMS_IN, TEXT_ANIMS_OUT,
  Track, TrackKind, TRANSITIONS, TransitionType,
} from './types';
import { clamp, clipEnd, clipIn, clipSpeed, deepClone, EPS, num, round, shortId, trackClips } from './util';
import { newProject } from './store';

const HEX = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i;
const EASES: Ease[] = ['linear', 'in', 'out', 'inOut', 'hold'];

export const trackKindFor = (k: ClipKind): TrackKind => (k === 'image' ? 'video' : k);

export function mainTrack(p: Project): Track | undefined {
  return p.tracks.find(t => t.main) || p.tracks.find(t => t.kind === 'video');
}

export function allIds(p: Project): Set<string> {
  return new Set([...p.clips.map(c => c.id), ...p.tracks.map(t => t.id)]);
}

export function newClipId(p: Project, kind: ClipKind): string {
  return shortId(kind === 'text' ? 't' : kind === 'audio' ? 'a' : 'c', allIds(p));
}

export function newTrackId(p: Project, kind: TrackKind): string {
  return shortId(kind === 'video' ? 'V' : kind === 'audio' ? 'A' : 'T', allIds(p));
}

/** Add a track of `kind`. Video and text tracks go above existing ones of their kind, audio below. */
export function addTrack(p: Project, kind: TrackKind, id?: string, name?: string): Track {
  const t: Track = { id: id || newTrackId(p, kind), kind, name: name || (kind === 'video' ? 'Overlay' : kind === 'audio' ? 'Audio' : 'Text') };
  if (kind === 'audio') {
    p.tracks.push(t);
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
  for (const t of p.tracks) if (t.kind === kind && !t.main && isFree(p, t.id, start, dur, ignore)) return t;
  return addTrack(p, kind);
}

export function mediaLimit(c: Clip, media: Record<string, MediaInfo>): number {
  // Longest timeline duration this clip may have given its in-point and speed.
  if (c.kind === 'text' || c.kind === 'image') return Infinity;
  const m = c.media ? media[c.media] : undefined;
  if (!m || !m.duration) return Infinity;
  return Math.max(0, (m.duration - clipIn(c)) / clipSpeed(c));
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
    if (c.kind !== 'text' && (!c.media || !media[c.media])) return false;
    return true;
  });
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
      c.transition = { type: c.transition.type, dur: round(clamp(c.transition.dur, minDur * 2, maxD), 3) };
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
  if (c.kind !== 'text' && c.kind !== 'image') b.in = clipIn(c) + lt * clipSpeed(c);
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
    x: [-3, 3], y: [-3, 3], scale: [0.02, 20], rotation: [-1440, 1440], opacity: [0, 1], volume: [0, 4],
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
      case 'fit': if (v === 'cover' || v === 'contain') c.fit = v; else issues.push(`${where}: fit must be "cover" or "contain"`); break;
      case 'name': c.name = String(v).slice(0, 60); break;
      case 'track': {
        const t = p.tracks.find(x => x.id === v);
        if (!t) { issues.push(`${where}: no track "${v}"`); break; }
        if (t.kind !== (c.kind === 'image' ? 'video' : c.kind) && !(c.kind === 'video' && t.kind === 'audio')) { issues.push(`${where}: cannot go on ${t.kind} track ${t.id}`); break; }
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
        const dur = typeof v === 'object' ? num(v.dur, 0.05, 3, 0.4) : 0.4;
        c.transition = { type: type as TransitionType, dur: round(dur, 3) };
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
      default: issues.push(`${where}: unknown field "${k}"`);
    }
  }
}

// ---------- Opus operations ----------

export interface OpsResult { project: Project; applied: number; issues: string[]; touched: string[] }

/** Apply a list of edit operations (the format Opus writes). Invalid operations are skipped and reported. */
export function applyOps(base: Project, rawOps: unknown, media: Record<string, MediaInfo>): OpsResult {
  const p = deepClone(base);
  const issues: string[] = [];
  const touched: string[] = [];
  let applied = 0;
  const ops = Array.isArray(rawOps) ? rawOps : [];
  if (!Array.isArray(rawOps)) issues.push('ops must be an array');
  ops.slice(0, 2000).forEach((op: any, i: number) => {
    const tag = `op ${i + 1}`;
    if (!op || typeof op !== 'object' || typeof op.op !== 'string') { issues.push(`${tag}: not an operation`); return; }
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
          let track = op.track ? p.tracks.find(t => t.id === op.track) : undefined;
          if (op.track && !track) { issues.push(`${tag}: no track "${op.track}" (add it with a track op first)`); return; }
          const asAudio = m.kind === 'audio' || track?.kind === 'audio';
          if (!track) track = asAudio ? p.tracks.find(t => t.kind === 'audio') : mainTrack(p);
          if (!track) { issues.push(`${tag}: no track for this clip`); return; }
          if (track.kind === 'text') { issues.push(`${tag}: media cannot go on text track ${track.id}`); return; }
          if (m.kind === 'audio' && track.kind !== 'audio') { issues.push(`${tag}: audio media must go on an audio track`); return; }
          const c = makeMediaClip(p, m, 0, track.id, asAudio);
          if (typeof op.id === 'string' && /^[A-Za-z][\w-]{0,23}$/.test(op.id) && !allIds(p).has(op.id)) c.id = op.id;
          else if (op.id) issues.push(`${tag}: id "${op.id}" is taken or invalid, used ${c.id}`);
          c.start = 'start' in op ? num(op.start, 0, 36000, 0) : (track.main ? 1e6 : 0);
          c.in = num(op.in, 0, Math.max(0, m.duration - 0.01), 0);
          const sp = 'speed' in op ? num(op.speed, 0.1, 10, 1) : 1;
          const rest = m.kind === 'image' ? 3 : Math.max(1 / p.fps, (m.duration - c.in) / sp);
          c.dur = 'dur' in op ? num(op.dur, 1 / p.fps, 36000, rest) : rest;
          const { op: _o, media: _m, track: _t, start: _s, in: _i, dur: _d, id: _id, ...rest2 } = op;
          patchClip(c, rest2, issues, p);
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
          if (typeof op.id === 'string' && /^[A-Za-z][\w-]{0,23}$/.test(op.id) && !allIds(p).has(op.id)) c.id = op.id;
          const { op: _o, track: _t, start: _s, dur: _d, id: _id, ...rest } = op;
          patchClip(c, rest, issues, p);
          if (!c.text) { issues.push(`${tag}: text clip without text was skipped`); return; }
          p.clips.push(c);
          touched.push(c.id);
          applied++;
          break;
        }
        case 'set': {
          const c = p.clips.find(x => x.id === op.id);
          if (!c) { issues.push(`${tag}: no clip "${op.id}"`); return; }
          const { op: _o, id: _id, ...rest } = op;
          patchClip(c, rest, issues, p);
          touched.push(c.id);
          applied++;
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
  });
  if (ops.length > 2000) issues.push('only the first 2000 operations were applied');
  normalize(p, media, { pruneTracks: true });
  return { project: p, applied, issues, touched };
}
