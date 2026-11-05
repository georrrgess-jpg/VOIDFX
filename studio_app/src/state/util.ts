import {
  AnimProp, Clip, ColorAdjust, DEFAULT_COLOR, DEFAULT_TEXT_ANIM, DEFAULT_TEXT_STYLE, DEFAULT_TRANSFORM,
  Ease, Keyframe, Project, TextAnim, TextStyle, Transform,
} from './types';

export const clamp = (v: number, a: number, b: number) => (v < a ? a : v > b ? b : v);
export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
export const EPS = 1e-4;

let idCounter = 0;
export function uid(prefix = 'c'): string {
  idCounter = (idCounter + 1) % 1e6;
  return prefix + Date.now().toString(36).slice(-4) + Math.random().toString(36).slice(2, 5) + idCounter.toString(36);
}

/** A short id unique within `taken` (used for ids Opus reads: m1, c12, t3). */
export function shortId(prefix: string, taken: Set<string>): string {
  let i = 1;
  while (taken.has(prefix + i)) i++;
  return prefix + i;
}

export function num(v: unknown, lo: number, hi: number, dflt: number): number {
  const n = typeof v === 'string' ? parseFloat(v) : (v as number);
  return typeof n === 'number' && Number.isFinite(n) ? clamp(n, lo, hi) : dflt;
}

export const round = (v: number, d = 3) => {
  const m = 10 ** d;
  return Math.round(v * m) / m;
};

export function fmtTime(t: number, fps = 30, withFrames = false): string {
  if (!Number.isFinite(t)) t = 0;
  const neg = t < 0;
  t = Math.abs(t);
  const m = Math.floor(t / 60);
  const s = Math.floor(t % 60);
  const base = `${neg ? '-' : ''}${m}:${String(s).padStart(2, '0')}`;
  if (!withFrames) return base;
  const f = Math.floor((t - Math.floor(t)) * fps + 1e-6);
  return `${base}:${String(f).padStart(2, '0')}`;
}

/** Broadcast-style timecode HH:MM:SS:FF. */
export function fmtTC(t: number, fps = 30): string {
  if (!Number.isFinite(t) || t < 0) t = 0;
  const total = Math.floor(t * fps + 1e-6);
  const f = total % fps;
  const secs = Math.floor(total / fps);
  const p2 = (n: number) => String(n).padStart(2, '0');
  return `${p2(Math.floor(secs / 3600))}:${p2(Math.floor(secs / 60) % 60)}:${p2(secs % 60)}:${p2(f)}`;
}

export function fmtSec(t: number): string {
  return `${t.toFixed(t < 10 ? 2 : 1)}s`;
}

export function fmtBytes(b: number): string {
  if (b < 1024) return `${b} B`;
  if (b < 1048576) return `${(b / 1024).toFixed(0)} KB`;
  if (b < 1073741824) return `${(b / 1048576).toFixed(1)} MB`;
  return `${(b / 1073741824).toFixed(2)} GB`;
}

export function ease(e: Ease | undefined, t: number): number {
  switch (e) {
    case 'linear': return t;
    case 'in': return t * t * t;
    case 'out': return 1 - (1 - t) ** 3;
    case 'hold': return 0;
    case 'inOut':
    default: return t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2;
  }
}
export const easeOutBack = (t: number) => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2; };

export function sampleKeys(keys: Keyframe[] | undefined, t: number, fallback: number): number {
  if (!keys || !keys.length) return fallback;
  if (t <= keys[0].t) return keys[0].v;
  const last = keys[keys.length - 1];
  if (t >= last.t) return last.v;
  for (let i = 0; i < keys.length - 1; i++) {
    const a = keys[i], b = keys[i + 1];
    if (t >= a.t && t <= b.t) {
      const span = b.t - a.t;
      if (span <= EPS) return b.v;
      return lerp(a.v, b.v, ease(a.e, (t - a.t) / span));
    }
  }
  return last.v;
}

// ---- resolved clip properties (defaults filled in) ----

export const clipSpeed = (c: Clip) => c.speed ?? 1;
export const clipIn = (c: Clip) => c.in ?? 0;
export const clipEnd = (c: Clip) => c.start + c.dur;
export const srcOut = (c: Clip) => clipIn(c) + c.dur * clipSpeed(c);

export function baseTransform(c: Clip): Transform {
  return { ...DEFAULT_TRANSFORM, ...(c.transform || {}) };
}

/** Transform at clip-local time `lt` (seconds from clip start), keyframes applied. */
export function transformAt(c: Clip, lt: number): Transform {
  const b = baseTransform(c);
  const kf = c.kf;
  if (!kf) return b;
  return {
    x: sampleKeys(kf.x, lt, b.x),
    y: sampleKeys(kf.y, lt, b.y),
    scale: sampleKeys(kf.scale, lt, b.scale),
    rotation: sampleKeys(kf.rotation, lt, b.rotation),
    opacity: sampleKeys(kf.opacity, lt, b.opacity),
  };
}

export function volumeAt(c: Clip, lt: number): number {
  return sampleKeys(c.kf?.volume, lt, c.volume ?? 1);
}

export function propValue(c: Clip, prop: AnimProp, lt: number): number {
  if (prop === 'volume') return volumeAt(c, lt);
  return transformAt(c, lt)[prop];
}

export const colorOf = (c: Clip): ColorAdjust => ({ ...DEFAULT_COLOR, ...(c.color || {}) });
export const textStyleOf = (c: Clip): TextStyle => ({ ...DEFAULT_TEXT_STYLE, ...(c.style || {}) });
export const textAnimOf = (c: Clip): TextAnim => ({ ...DEFAULT_TEXT_ANIM, ...(c.anim || {}) });

export function projectDuration(p: Project): number {
  let d = 0;
  for (const c of p.clips) d = Math.max(d, c.start + c.dur);
  return d;
}

export function trackClips(p: Project, trackId: string): Clip[] {
  return p.clips.filter(c => c.track === trackId).sort((a, b) => a.start - b.start);
}

export const frameDur = (p: Project) => 1 / p.fps;
export const snapToFrame = (t: number, fps: number) => Math.round(t * fps) / fps;

export function deepClone<T>(v: T): T {
  return typeof structuredClone === 'function' ? structuredClone(v) : JSON.parse(JSON.stringify(v));
}

export function isTextInput(el: EventTarget | null): boolean {
  if (!(el instanceof HTMLElement)) return false;
  const tag = el.tagName;
  if (tag === 'TEXTAREA' || el.isContentEditable) return true;
  if (tag === 'INPUT') {
    const type = (el as HTMLInputElement).type;
    return !['range', 'checkbox', 'radio', 'button', 'color'].includes(type);
  }
  return tag === 'SELECT';
}
