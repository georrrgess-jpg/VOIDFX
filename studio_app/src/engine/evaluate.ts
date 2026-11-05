// Evaluates the timeline at one instant: which layers are visible (bottom to top) and what each
// audio-bearing clip contributes. Preview, export and the Opus review renderer all use this.
import { Clip, ColorAdjust, MediaInfo, Project, Transform } from '../state/types';
import { clamp, clipEnd, clipIn, clipSpeed, colorOf, EPS, transformAt, volumeAt } from '../state/util';
import { LayerFx, NO_FX, transitionFx } from './transitions';

export interface VisualLayer {
  clip: Clip;
  kind: 'video' | 'image' | 'text';
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

export interface Evaluation { layers: VisualLayer[]; audio: AudioVoice[] }

interface Window { clip: Clip; from: number; to: number; tin?: { dur: number; type: any }; tout?: { dur: number; type: any } }

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
  const s = clipIn(c) + (t - c.start) * clipSpeed(c);
  const maxT = m?.duration ? Math.max(0, m.duration - 0.5 / Math.max(1, m.fps || 30)) : Infinity;
  return clamp(s, 0, maxT);
}

function fadeGain(c: Clip, lt: number): number {
  let g = 1;
  if (c.fadeIn && c.fadeIn > EPS && lt < c.fadeIn) g *= clamp(lt / c.fadeIn, 0, 1);
  if (c.fadeOut && c.fadeOut > EPS && lt > c.dur - c.fadeOut) g *= clamp((c.dur - lt) / c.fadeOut, 0, 1);
  return g;
}

export function evaluate(p: Project, media: Record<string, MediaInfo>, t: number, opts: { audio?: boolean } = {}): Evaluation {
  const layers: VisualLayer[] = [];
  const audio: AudioVoice[] = [];
  // bottom track first: tracks are listed top to bottom
  for (let ti = p.tracks.length - 1; ti >= 0; ti--) {
    const tr = p.tracks[ti];
    const wins = trackWindows(p, tr.id);
    for (const w of wins) {
      if (t < w.from - EPS || t >= w.to - EPS) continue;
      const c = w.clip;
      const lt = t - c.start;
      let fx: LayerFx = NO_FX;
      let tGain = 1;
      if (w.tin && t < c.start + w.tin.dur / 2) {
        const pr = (t - (c.start - w.tin.dur / 2)) / w.tin.dur;
        fx = { ...NO_FX, ...transitionFx(w.tin.type, pr, 'in') };
        tGain = Math.sin(clamp(pr, 0, 1) * Math.PI / 2);
      } else if (w.tout && t >= clipEnd(c) - w.tout.dur / 2) {
        const pr = (t - (clipEnd(c) - w.tout.dur / 2)) / w.tout.dur;
        fx = { ...NO_FX, ...transitionFx(w.tout.type, pr, 'out') };
        tGain = Math.cos(clamp(pr, 0, 1) * Math.PI / 2);
      }
      const m = c.media ? media[c.media] : undefined;
      const ltc = clamp(lt, 0, c.dur);
      if (tr.kind !== 'audio' && !tr.hidden && fx.visible) {
        if (c.kind === 'video' || c.kind === 'image' || c.kind === 'text') {
          layers.push({
            clip: c,
            kind: c.kind,
            lt,
            srcTime: c.kind === 'video' ? sourceTime(c, t, m) : 0,
            transform: transformAt(c, ltc),
            color: colorOf(c),
            fx,
          });
        }
      }
      if (opts.audio !== false && (c.kind === 'video' || c.kind === 'audio') && m?.hasAudio) {
        const muted = c.muted || tr.muted;
        const g = muted ? 0 : volumeAt(c, ltc) * fadeGain(c, lt) * tGain;
        audio.push({ clip: c, srcTime: sourceTime(c, t, m), gain: g, speed: clipSpeed(c) });
      }
    }
  }
  return { layers, audio };
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
    set.add(+c.start.toFixed(3));
    set.add(+clipEnd(c).toFixed(3));
  }
  return [...set].sort((a, b) => a - b);
}
