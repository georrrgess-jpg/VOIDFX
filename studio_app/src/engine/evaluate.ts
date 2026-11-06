// Evaluates the timeline at one instant: which layers are visible (bottom to top) and what each
// audio-bearing clip contributes. Preview, export and the Opus review renderer all use this.
import { Clip, ColorAdjust, MediaInfo, Project, Transform } from '../state/types';
import { clamp, clipEnd, colorOf, EPS, speedAt, srcAt, transformAt, volumeAt } from '../state/util';
import { LayerFx, NO_FX, logoLayerFx, transitionFx } from './transitions';
import { revealFx } from './custom';

export interface VisualLayer {
  clip: Clip;
  kind: 'video' | 'image' | 'text' | 'logo' | 'graphic' | 'shader';
  /** Seconds since the clip's start (negative or past the end during transitions). */
  lt: number;
  srcTime: number;
  transform: Transform;
  color: ColorAdjust;
  fx: LayerFx;
}

export interface AudioVoice {
  clip: Clip;
  srcTime: number;
  gain: number;
  speed: number;
}

export interface Evaluation { layers: VisualLayer[]; audio: AudioVoice[]; sfx: { clip: Clip; lt: number; gain: number }[] }

export interface Window { clip: Clip; from: number; to: number; tin?: { dur: number; type: any }; tout?: { dur: number; type: any } }

/** Visible span of each clip on a track, including the half-transition overlaps into neighbours. */
export function trackWindows(p: Project, trackId: string): Window[] {
  const list = p.clips.filter(c => c.track === trackId).sort((a, b) => a.start - b.start);
  const frame = 1 / (p.fps || 30);
  const out: Window[] = list.map(c => ({ clip: c, from: c.start, to: clipEnd(c) }));
  for (let i = 1; i < out.length; i++) {
    const a = out[i - 1], b = out[i];
    const tr = b.clip.transition;
    if (!tr || Math.abs(clipEnd(a.clip) - b.clip.start) > frame * 1.5) continue;
    const h = tr.dur / 2;
    a.to = clipEnd(a.clip) + h;
    a.tout = tr;
    b.from = b.clip.start - h;
    b.tin = tr;
  }
  return out;
}

export function sourceTime(c: Clip, t: number, m?: MediaInfo): number {
  const s = srcAt(c, t - c.start);
  const maxT = m?.duration ? Math.max(0, m.duration - 0.5 / Math.max(1, m.fps || 30)) : Infinity;
  return clamp(s, 0, maxT);
}

function fadeGain(c: Clip, lt: number): number {
  let g = 1;
  if (c.fadeIn && c.fadeIn > EPS && lt < c.fadeIn) g *= clamp(lt / c.fadeIn, 0, 1);
  if (c.fadeOut && c.fadeOut > EPS && lt > c.dur - c.fadeOut) g *= clamp((c.dur - lt) / c.fadeOut, 0, 1);
  return g;
}

// ---------- music beats on the timeline (for snapping, the beat camera and Opus) ----------

const beatCache = new WeakMap<object, { media: object; beats: { t: number; down: boolean; i: number }[] }>();
/** Beats of the music on audio tracks, mapped to timeline time. */
export function timelineBeats(p: Project, media: Record<string, MediaInfo>): { t: number; down: boolean; i: number }[] {
  const hit = beatCache.get(p.clips);
  if (hit && hit.media === media) return hit.beats;
  const out: { t: number; down: boolean; i: number }[] = [];
  for (const c of p.clips) {
    if (c.kind !== 'audio' || !c.media) continue;
    const a = media[c.media]?.analysis;
    if (!a?.bpm || !a.beats.length) continue;
    const s0 = srcAt(c, 0), s1 = srcAt(c, c.dur);
    const down = new Set(a.downbeats.map(x => x.toFixed(3)));
    a.beats.forEach((b, i) => {
      if (b < s0 || b > s1) return;
      // invert the (possibly ramped) mapping numerically: speed is ~constant for music beds
      const sp = Math.max(0.05, speedAt(c, 0));
      out.push({ t: c.start + (b - s0) / sp, down: down.has(b.toFixed(3)), i });
    });
  }
  out.sort((x, y) => x.t - y.t);
  beatCache.set(p.clips, { media, beats: out });
  return out;
}

/** Camera transform from the beat camera at time t: zoom, rotation (deg) and hit-frame strength. */
export function cameraAt(p: Project, media: Record<string, MediaInfo>, t: number): { zoom: number; rot: number; hit: number } | null {
  const cam = p.camera;
  if (!cam?.on) return null;
  if ((cam.from !== undefined && t < cam.from) || (cam.to !== undefined && t > cam.to)) return null;
  const beats = timelineBeats(p, media).filter(b => cam.every === 'downbeat' ? b.down : cam.every === 'half' ? b.i % 2 === 0 : true);
  if (!beats.length) return null;
  let lo = 0, hi = beats.length - 1, k = -1;
  while (lo <= hi) { const mid = (lo + hi) >> 1; if (beats[mid].t <= t + 1e-6) { k = mid; lo = mid + 1; } else hi = mid - 1; }
  if (k < 0) return null;
  const age = t - beats[k].t;
  const decay = Math.max(0.03, cam.decay);
  if (age > decay * 5) return null;
  const amt = Math.exp(-age / decay);
  const sign = k % 2 === 0 ? 1 : -1;
  return { zoom: 1 + cam.punch * amt, rot: cam.kick * amt * sign, hit: age < 1.5 / p.fps ? 1 : 0 };
}

function applyCamera(tr: Transform, fx: LayerFx, cam: { zoom: number; rot: number; hit: number }, aspect: number): [Transform, LayerFx] {
  // scale and rotate about the frame centre: move the layer's offset with the camera
  const r = (cam.rot * Math.PI) / 180;
  const ox = tr.x * aspect, oy = tr.y; // offset in frame-height units
  const rx = (ox * Math.cos(r) - oy * Math.sin(r)) * cam.zoom, ry = (ox * Math.sin(r) + oy * Math.cos(r)) * cam.zoom;
  const t2 = { ...tr, x: rx / aspect, y: ry, scale: tr.scale * cam.zoom, rotation: tr.rotation + cam.rot };
  const f2 = cam.hit ? { ...fx, chroma: Math.max(fx.chroma, 0.006), blur: Math.max(fx.blur, 0.12) } : fx;
  return [t2, f2];
}

/**
 * Offset (in frame fractions) that centres a clip's focus point in the frame for a filled ("cover")
 * picture at the given scale, without ever showing past the picture's edges.
 */
export function focusOffset(c: Clip, m: MediaInfo | undefined, p: Project, scale: number): { x: number; y: number } {
  if (!c.focus || !m || !m.width || !m.height || (c.fit || 'cover') !== 'cover') return { x: 0, y: 0 };
  const W = p.width, H = p.height;
  const k = Math.max(W / m.width, H / m.height) * Math.max(0.05, scale);
  const dw = m.width * k, dh = m.height * k;
  const sx = (clamp(c.focus.x, 0, 1) - 0.5) * dw, sy = (clamp(c.focus.y, 0, 1) - 0.5) * dh;
  const mx = Math.max(0, (dw - W) / 2), my = Math.max(0, (dh - H) / 2);
  // faces sit a little above centre in 9:16, leaving room for captions below
  const targetY = H > W ? -0.06 * H : 0;
  return { x: clamp(-sx, -mx, mx) / W, y: clamp(targetY - sy, -my, my) / H };
}

export function evaluate(p: Project, media: Record<string, MediaInfo>, t: number, opts: { audio?: boolean; camera?: boolean } = {}): Evaluation {
  const layers: VisualLayer[] = [];
  const audio: AudioVoice[] = [];
  const sfx: { clip: Clip; lt: number; gain: number }[] = [];
  const cam = opts.camera === false ? null : cameraAt(p, media, t);
  const aspect = p.width / p.height;
  // bottom track first: tracks are listed top to bottom
  for (let ti = p.tracks.length - 1; ti >= 0; ti--) {
    const tr = p.tracks[ti];
    const wins = trackWindows(p, tr.id);
    const trackStart = layers.length;
    for (const w of wins) {
      if (t < w.from - EPS || t >= w.to - EPS) continue;
      const c = w.clip;
      const lt = t - c.start;
      let fx: LayerFx = NO_FX;
      let tGain = 1;
      let logoP = -1;
      if (w.tin && t < c.start + w.tin.dur / 2) {
        const pr = (t - (c.start - w.tin.dur / 2)) / w.tin.dur;
        fx = { ...NO_FX, ...transitionFx(w.tin.type, pr, 'in') };
        tGain = Math.sin(clamp(pr, 0, 1) * Math.PI / 2);
        if (w.tin.type === 'logo') logoP = pr;
      } else if (w.tout && t >= clipEnd(c) - w.tout.dur / 2) {
        const pr = (t - (clipEnd(c) - w.tout.dur / 2)) / w.tout.dur;
        fx = { ...NO_FX, ...transitionFx(w.tout.type, pr, 'out') };
        tGain = Math.cos(clamp(pr, 0, 1) * Math.PI / 2);
      }
      const m = c.media ? media[c.media] : undefined;
      const ltc = clamp(lt, 0, c.dur);
      if (tr.kind !== 'audio' && !tr.hidden && fx.visible) {
        if (c.kind === 'video' || c.kind === 'image' || c.kind === 'text') {
          let transform = transformAt(c, ltc);
          if (c.focus && c.kind !== 'text') { const f = focusOffset(c, m, p, transform.scale); transform = { ...transform, x: transform.x + f.x, y: transform.y + f.y }; }
          let lfx = fx;
          if (cam && c.kind !== 'text') [transform, lfx] = applyCamera(transform, fx, cam, aspect);
          layers.push({ clip: c, kind: c.kind, lt, srcTime: c.kind === 'video' ? sourceTime(c, t, m) : 0, transform, color: colorOf(c), fx: lfx });
        } else if (c.kind === 'graphic') {
          // graphics sit on the footage, so they ride with the beat camera
          let transform = transformAt(c, ltc);
          const rf = revealFx(c, lt);
          let lfx: LayerFx = { ...fx, ...rf, opacity: fx.opacity * (rf.opacity ?? 1), scale: fx.scale * (rf.scale ?? 1) };
          if (cam) [transform, lfx] = applyCamera(transform, lfx, cam, aspect);
          layers.push({ clip: c, kind: 'graphic', lt, srcTime: 0, transform, color: colorOf(c), fx: lfx });
        } else if (c.kind === 'shader') {
          layers.push({ clip: c, kind: 'shader', lt, srcTime: 0, transform: transformAt(c, ltc), color: colorOf(c), fx });
        }
      }
      if (logoP >= 0 && tr.kind !== 'audio' && !tr.hidden) {
        layers.push({ clip: c, kind: 'logo', lt, srcTime: 0, transform: { x: 0, y: 0, scale: 1, rotation: 0, opacity: 1 }, color: colorOf(c), fx: { ...NO_FX, ...logoLayerFx(logoP) } });
      }
      if (opts.audio !== false) {
        const muted = c.muted || tr.muted;
        if ((c.kind === 'video' || c.kind === 'audio') && m?.hasAudio) {
          const g = muted ? 0 : volumeAt(c, ltc) * fadeGain(c, lt) * tGain;
          audio.push({ clip: c, srcTime: sourceTime(c, t, m), gain: g, speed: speedAt(c, ltc) });
        } else if (c.kind === 'sfx') {
          sfx.push({ clip: c, lt, gain: muted ? 0 : volumeAt(c, ltc) * fadeGain(c, lt) });
        }
      }
    }
    // an outgoing layer that splits apart (slash) is drawn above the incoming one
    const mine = layers.splice(trackStart);
    layers.push(...mine.filter(L => !L.fx.top), ...mine.filter(L => L.fx.top));
  }
  return { layers, audio, sfx };
}

/** Clips that become active within (t, t + ahead], with the source time they start at. */
export function upcoming(p: Project, media: Record<string, MediaInfo>, t: number, ahead: number): { clip: Clip; srcTime: number }[] {
  const out: { clip: Clip; srcTime: number }[] = [];
  for (const tr of p.tracks) {
    for (const w of trackWindows(p, tr.id)) {
      if (w.from > t + EPS && w.from <= t + ahead && (w.clip.kind === 'video' || w.clip.kind === 'audio')) {
        out.push({ clip: w.clip, srcTime: sourceTime(w.clip, w.from, w.clip.media ? media[w.clip.media] : undefined) });
      }
    }
  }
  return out;
}

/** Times where something changes (cuts, transition midpoints, text in/out), for reviews. */
export function cutTimes(p: Project): number[] {
  const set = new Set<number>();
  for (const c of p.clips) {
    if (c.kind === 'sfx') continue;
    set.add(+c.start.toFixed(3));
    set.add(+clipEnd(c).toFixed(3));
  }
  return [...set].sort((a, b) => a - b);
}
