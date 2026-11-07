// What the director and the critic measure on rendered frames: the storyboard of a cut, every
// transition as three frames, and which transitions are weak (an empty middle, invisible, a plain
// crossfade) or used too often.
import { TRANSITION_LABELS } from '../engine/transitions';
import { Project, TransitionType } from '../state/types';
import { projectDuration } from '../state/util';
import type { FrameStat, Sheet } from './sheets';

const f2 = (t: number) => t.toFixed(2);
const mainShots = (p: Project) => {
  const main = p.tracks.find(t => t.main)?.id;
  return p.clips.filter(c => c.track === main && (c.kind === 'video' || c.kind === 'image')).sort((a, b) => a.start - b.start);
};

/** A storyboard of the main track: each shot's first, middle and last frame (fewer when the budget is tight). */
export function storyboardTimes(p: Project, budget: number): { times: number[]; labels: string[] } {
  const shots = mainShots(p);
  const dur = projectDuration(p);
  const per = Math.max(1, Math.min(3, Math.floor(budget / Math.max(1, shots.length))));
  const times: number[] = [], labels: string[] = [];
  for (const c of shots) {
    const a = c.start, b = Math.min(dur, c.start + c.dur);
    const picks: [string, number][] = per >= 3 && c.dur >= 0.45 ? [['in', a + 0.03], ['mid', (a + b) / 2], ['out', b - 0.03]] : per >= 2 && c.dur >= 0.3 ? [['in', a + 0.03], ['out', b - 0.03]] : [['mid', (a + b) / 2]];
    for (const [k, t] of picks) { times.push(+Math.max(0, Math.min(dur - 0.01, t)).toFixed(3)); labels.push(`${c.id} ${k} ${f2(t)}`); }
  }
  return { times: times.slice(0, budget), labels: labels.slice(0, budget) };
}

export interface TransFrame { t: number; label: string; clip: string; k: 'a' | 'b' | 'c' }

/** Three frames around every transition: a just before, b the middle, c just after. */
export function transitionTimes(p: Project, max: number): TransFrame[] {
  const dur = projectDuration(p);
  const out: TransFrame[] = [];
  const trans = p.clips.filter(c => c.transition).sort((a, b) => a.start - b.start).slice(0, Math.floor(max / 3));
  for (const c of trans) {
    const d = c.transition!.dur || 0.4;
    const name = (TRANSITION_LABELS[c.transition!.type] || c.transition!.type).slice(0, 14);
    for (const [k, dt] of [['a', -d * 0.45], ['b', 0], ['c', d * 0.45]] as ['a' | 'b' | 'c', number][]) {
      const t = Math.min(dur - 0.01, Math.max(0, c.start + dt));
      out.push({ t, label: `${name} ${k} ${f2(t)}s`, clip: c.id, k });
    }
  }
  return out;
}

/** Moves whose middle is a designed blink of black (the eye dive, the M99 blink, the logo). */
const DESIGNED_BLINK = new Set(['dive', 'blink', 'logo', 'eyelid']);

const diff = (a: Float32Array, b: Float32Array) => { let s = 0; for (let i = 0; i < a.length; i++) s += Math.abs(a[i] - b[i]); return s / a.length; };

/**
 * The transitions measured on their three frames. Weak: the middle frame is an empty black, white or
 * flat card; it is just one of the two shots (the move is invisible and plays as a cut); or it is the
 * plain average of the two (a crossfade dressed as a transition). Repeated: a type used three or more
 * times, or twice in a row.
 */
export function transitionReport(p: Project, frames: TransFrame[], sheets: Sheet[]): { text: string; weak: number[] } {
  const stats: FrameStat[] = sheets.flatMap(s => s.stats || []);
  const at = (t: number) => stats.find(s => Math.abs(s.t - t) < 0.002);
  const lines: string[] = [];
  const weak: number[] = [];
  const byClip = new Map<string, Partial<Record<'a' | 'b' | 'c', FrameStat>>>();
  for (const f of frames) { const s = at(f.t); if (!s) continue; const m = byClip.get(f.clip) || {}; m[f.k] = s; byClip.set(f.clip, m); }
  for (const [id, m] of byClip) {
    const c = p.clips.find(x => x.id === id);
    if (!c?.transition || !m.a || !m.b || !m.c) continue;
    const type = c.transition.type;
    const name = TRANSITION_LABELS[type] || type;
    const span = diff(m.a.px, m.c.px);
    const mix = new Float32Array(256);
    for (let i = 0; i < 256; i++) mix[i] = (m.a.px[i] + m.c.px[i]) / 2;
    const nearOne = Math.min(diff(m.b.px, m.a.px), diff(m.b.px, m.c.px));
    const nearMix = diff(m.b.px, mix);
    const sdAround = (m.a.sd + m.c.sd) / 2;
    let why = '';
    if (type === 'logo') why = '';
    else if (!DESIGNED_BLINK.has(type) && m.b.sd < 0.045 && m.b.sd < sdAround * 0.4) why = `its middle is an empty ${m.b.luma < 0.08 ? 'black' : m.b.luma > 0.85 ? 'white' : 'flat'} frame: nothing is seen going through anything`;
    else if (span > 0.06 && nearOne < 0.018) why = 'its middle frame is just one of the two shots: the move is invisible and plays as a plain cut (longer, or a move with more travel)';
    else if (span > 0.08 && nearMix < 0.02 && !/dissolve|cross|fade/.test(type)) why = 'its middle is the plain average of the two shots: it reads as a crossfade, not a designed move';
    if (why) { weak.push(c.start); lines.push(`- ${name} at ${f2(c.start)} s (${id}): ${why}.`); }
  }
  const all = p.clips.filter(c => c.transition).sort((a, b) => a.start - b.start);
  const count = new Map<TransitionType, number[]>();
  for (const c of all) { const k = c.transition!.type; count.set(k, [...(count.get(k) || []), c.start]); }
  const over = [...count].filter(([k, ts]) => k !== 'logo' && ts.length >= 3);
  for (const [k, ts] of over) lines.push(`- ${TRANSITION_LABELS[k] || k} is used ${ts.length} times (${ts.map(f2).join(', ')} s): the repeats read as a template. Keep the best one and replace the others with different designed moves.`);
  const main = mainShots(p);
  for (let i = 1; i < main.length; i++) {
    const a = main[i - 1].transition?.type, b = main[i].transition?.type;
    if (a && b && a === b && a !== 'logo' && !over.some(([k]) => k === a)) lines.push(`- ${TRANSITION_LABELS[a] || a} twice in a row at ${f2(main[i - 1].start)} and ${f2(main[i].start)} s: change one.`);
  }
  if (!byClip.size && !lines.length) return { text: '', weak };
  const head = `MEASURED TRANSITIONS (each one's three frames: a before, b middle, c after; ${byClip.size} measured)`;
  return { text: lines.length ? `${head}\n${lines.join('\n')}\nRebuild each weak or repeated one as a different designed move that goes through something in the shot (its anchor on that thing), with its sound.` : `${head}: none is empty, invisible or a plain crossfade, and no type repeats too often.`, weak };
}

// ---------- does each layer show? ----------

const DESIGNED_DARK = new Set(['aperture', 'tv_off', 'static', 'exposure_wash', 'impact_frame', 'flash', 'letterbox']);

function rgbGrid(c: HTMLCanvasElement | null): Float32Array | null {
  if (!c) return null;
  const s = document.createElement('canvas');
  s.width = 16; s.height = 16;
  const g = s.getContext('2d', { willReadFrequently: true })!;
  g.drawImage(c, 0, 0, 16, 16);
  const d = g.getImageData(0, 0, 16, 16).data;
  const out = new Float32Array(768);
  for (let i = 0; i < 256; i++) for (let k = 0; k < 3; k++) out[i * 3 + k] = d[i * 4 + k] / 255;
  return out;
}
const lumaSd = (g: Float32Array) => {
  const l: number[] = [];
  for (let i = 0; i < 256; i++) l.push(g[i * 3] * 0.2126 + g[i * 3 + 1] * 0.7152 + g[i * 3 + 2] * 0.0722);
  const m = l.reduce((a, b) => a + b, 0) / 256;
  return { m, sd: Math.sqrt(l.reduce((a, b) => a + (b - m) ** 2, 0) / 256) };
};

/**
 * Every effect, graphic and shader layer rendered with and without itself at its own moment: a layer
 * that changes nothing on screen is not there (the critic's "depth on paper only"), and one that turns
 * a lit frame into a white or black card has failed.
 */
export async function layerReport(p: Project, media: Record<string, import('../state/types').MediaInfo>, signal?: AbortSignal, max = 24): Promise<{ text: string; invisible: string[]; blown: string[] }> {
  const { renderStills } = await import('../engine/exporter');
  const dur = projectDuration(p);
  const lookIds = new Set(p.tracks.filter(t => t.role === 'look').map(t => t.id));
  const layers = p.clips.filter(c => (c.kind === 'shader' || c.kind === 'graphic') && !lookIds.has(c.track) && c.span !== 'all' && c.dur >= 0.08 && c.start < dur).sort((a, b) => a.start - b.start).slice(0, max);
  if (!layers.length) return { text: '', invisible: [], blown: [] };
  const tOf = (c: typeof layers[number]) => +Math.min(dur - 0.02, c.start + Math.min(c.dur * 0.4, Math.max(0.04, c.dur - 0.04))).toFixed(3);
  const covers = (c: typeof layers[number], t: number) => c.start <= t && t < c.start + c.dur;
  const groups: (typeof layers)[] = [];
  for (const c of layers) {
    const g = groups.find(gr => gr.every(d => !covers(d, tOf(c)) && !covers(c, tOf(d))));
    if (g) g.push(c); else groups.push([c]);
  }
  const H = 128;
  const withF = await renderStills(p, layers.map(tOf), H, signal, media);
  const without = new Map<string, HTMLCanvasElement | null>();
  for (const g of groups) {
    if (signal?.aborted) break;
    const ids = new Set(g.map(c => c.id));
    const q: Project = { ...p, clips: p.clips.filter(c => !ids.has(c.id)) };
    const frames = await renderStills(q, g.map(tOf), H, signal, media);
    g.forEach((c, i) => without.set(c.id, frames[i]));
  }
  const invisible: string[] = [], blown: string[] = [], lines: string[] = [];
  layers.forEach((c, i) => {
    const a = rgbGrid(withF[i]), b = rgbGrid(without.get(c.id) ?? null);
    if (!a || !b) return;
    let sum = 0, peak = 0;
    for (let k = 0; k < a.length; k++) { const d = Math.abs(a[k] - b[k]); sum += d; if (d > peak) peak = d; }
    const mean = sum / a.length;
    const name = `${c.preset || c.kind} ${c.id} ${f2(c.start)}-${f2(c.start + c.dur)} s`;
    if (mean < 0.008 && peak < 0.06) { invisible.push(c.id); lines.push(`- ${name}: does not show (the frame looks the same without it). Raise its amount or opacity, put it "over" the look, move it where it reads, or remove it.`); return; }
    const A = lumaSd(a), B = lumaSd(b);
    if (!(c.preset && DESIGNED_DARK.has(c.preset)) && A.sd < 0.05 && (A.m > 0.85 || A.m < 0.05) && B.m > 0.1 && B.m < 0.8) {
      blown.push(c.id);
      lines.push(`- ${name}: turns a lit frame into a ${A.m > 0.5 ? 'white' : 'black'} card. Lower its amount, shorten it, or rebuild the moment.`);
    }
  });
  const head = `MEASURED LAYERS (each effect, graphic and shader rendered with and without itself; ${layers.length} measured)`;
  return { text: lines.length ? `${head}\n${lines.join('\n')}` : `${head}: every layer shows, and none blows the frame out.`, invisible, blown };
}
