// Set pieces as one operation: {"op":"piece","kind":"freeze_hit","at":9.6,...}. Each expands into the
// tested multi-stage build of an approved set piece (the ramp or freeze, the transition, the effects with
// their anchors and amounts, the title, the sounds), timed on the shots that are on the timeline, so the
// hardest moments of an edit render right the first time instead of being assembled from scratch.
import { Clip, Project } from './types';
import { projectDuration } from './util';

export interface PieceDef { id: string; does: string; takes: string }

export const PIECES: PieceDef[] = [
  { id: 'freeze_hit', does: 'the hit freezes the shot (drained colour, coloured rim light), a short shake and an ink impact frame land on it, the word stamps in, impact sound; the shot runs on after the hold', takes: 'at (the hit), hold 0.4-1.0 (0.7), color (rim), word (optional)' },
  { id: 'blood_drop', does: 'v8 "Darling," freeze: the word freezes the shot and writes on in blood red, a drop falls from under the word and splats on the drop, the cut blooms open as ink with a red shockwave; heartbeat then subdrop', takes: 'at (the drop, a cut), word_at (the freeze, default at-1.2), word, anchor (where the drop falls, off the face)' },
  { id: 'plastic_burst', does: 'v7 hero: the shot sits behind kill-room plastic that bulges toward the camera, then on the drop the plastic tears open (tear transition) with a shockwave, blood-red sparks and a two-frame ink impact; riser, rip and impact', takes: 'at (the drop, a cut), anchor (the burst point, off the face)' },
  { id: 'crt_dive', does: 'v6 hero: the outgoing shot shrinks into a curved CRT picture, then the camera dives through the screen on the drop with speed streaks; riser then impact', takes: 'at (the drop, a cut)' },
  { id: 'polaroid_toss', does: 'v4/v6: the outgoing moment freezes as a white-bordered print with a camera flash and is tossed off frame as the next shot plays; shutter and whoosh', takes: 'at (a cut)' },
  { id: 'glass_shatter', does: 'v4 drop: the cut shatters from the impact point (muzzle flash, a hit) with a shake; impact and glass', takes: 'at (a cut), anchor (the impact point, never the face)' },
  { id: 'lens_blood', does: 'v7: blood splats on the lens in a corner and runs clear while the next shot plays through it; hit and rip', takes: 'at (the splat, usually on a cut), anchor (a top corner or the lower third)' },
  { id: 'light_title', does: 'a hero word revealed by a light sweep across it, the light passing over the shot; whoosh', takes: 'at, word, dur (1.2), color (the light tint)' },
  { id: 'pupil_loop', does: 'v4/v7 loop: the last shot pushes into the eye as an aperture closes on it, frame 0 opens from the same black on the first shot\'s eye: the wrap is black to black, invisible; heartbeat under the close', takes: 'anchor (the eye on the last shot, default the focus point), open_anchor (the eye on frame 0)' },
];

const r4 = (v: number) => Math.round(v * 10000) / 10000;
const pt = (v: any, d: { x: number; y: number }) => (v && typeof v === 'object' && Number.isFinite(+v.x) && Number.isFinite(+v.y) ? { x: Math.min(1, Math.max(0, +v.x)), y: Math.min(1, Math.max(0, +v.y)) } : d);

/** The main-track shot playing at t, and the cut nearest t (within 0.2 s). */
function shotsAt(p: Project, t: number) {
  const main = p.tracks.find(x => x.main)?.id;
  const shots = p.clips.filter(c => c.track === main && (c.kind === 'video' || c.kind === 'image')).sort((a, b) => a.start - b.start);
  const at = shots.find(c => c.start <= t + 1e-3 && t < c.start + c.dur - 1e-3) || shots[shots.length - 1];
  const cut = shots.filter(c => c !== shots[0] && Math.abs(c.start - t) <= 0.2).sort((a, b) => Math.abs(a.start - t) - Math.abs(b.start - t))[0];
  const before = cut ? shots[shots.indexOf(cut) - 1] : undefined;
  return { shots, at, cut, before };
}

/** Speed keys that hold the shot (0.04x) from lt for `hold` seconds, keeping its keys outside the hold. */
function freezeKeys(c: Clip, lt: number, hold: number) {
  const keys = (c.kf?.speed || []).filter(k => k.t < lt - 0.01 || k.t > lt + hold + 0.01);
  const after = [...(c.kf?.speed || [])].filter(k => k.t <= lt).pop()?.v ?? c.speed ?? 1;
  keys.push({ t: r4(lt), v: 0.04, e: 'hold' as const }, { t: r4(Math.min(c.dur, lt + hold)), v: Math.max(0.3, after), e: 'hold' as const });
  return keys.sort((a, b) => a.t - b.t);
}

function scaleKeys(c: Clip, a: number, b: number, from: number, to: number) {
  const keys = (c.kf?.scale || []).filter(k => k.t < a - 0.01 || k.t > b + 0.01);
  keys.push({ t: r4(Math.max(0, a)), v: from, e: 'in' as const } as any, { t: r4(Math.min(c.dur, b)), v: to } as any);
  return keys.sort((x, y) => x.t - y.t);
}

const title = (word: string, start: number, dur: number, anim: string, color?: string) => ({
  op: 'text', start: r4(start), dur: r4(dur), text: `*${word.toUpperCase()}*`,
  style: { size: 0.085, uppercase: true, weight: 900, ...(color ? { emphColor: color } : {}) },
  anim: { in: anim, out: 'fade', inDur: 0.35, outDur: 0.3 }, transform: { y: 0.25 },
});

/** The operations a piece stands for (applied right after it, in order). Problems are reported in `issues`. */
export function expandPiece(p: Project, op: any, issues: string[], tag: string): any[] {
  const kind = String(op.kind || op.piece || '');
  const def = PIECES.find(d => d.id === kind);
  if (!def) { issues.push(`${tag}: unknown piece "${kind}" (pieces: ${PIECES.map(d => d.id).join(', ')})`); return []; }
  const dur = projectDuration(p);
  const t = Math.min(Math.max(0, Number.isFinite(+op.at) ? +op.at : Number.isFinite(+op.start) ? +op.start : 0), Math.max(0, dur - 0.05));
  const { at, cut, before } = shotsAt(p, t);
  if (!at) { issues.push(`${tag}: piece ${kind} needs shots on the main track first`); return []; }
  const note = op.note !== undefined ? { note: op.note } : {};
  const color = typeof op.color === 'string' ? op.color : undefined;
  const word = typeof op.word === 'string' && op.word.trim() ? op.word.trim().slice(0, 24) : '';
  const needCut = () => { if (!cut) issues.push(`${tag}: piece ${kind} at ${t.toFixed(2)} s needs a cut there (none within 0.2 s); its transition was left out`); return !!cut; };
  const T = cut ? cut.start : t;
  const out: any[] = [];
  const fx = (preset: string, start: number, d: number, params: Record<string, any> = {}, anchor?: { x: number; y: number }, extra: Record<string, any> = {}) =>
    out.push({ op: 'fx', preset, start: r4(Math.max(0, start)), dur: r4(d), params, ...(anchor ? { at: anchor } : {}), ...extra, ...note });
  const sfx = (sound: string, start: number, volume = 0.4) => out.push({ op: 'sfx', sound, start: r4(Math.max(0, start)), volume, ...note });

  switch (kind) {
    case 'freeze_hit': {
      const hold = Math.min(1.0, Math.max(0.4, +op.hold || 0.7));
      const lt = t - at.start;
      out.push({ op: 'set', id: at.id, kf: { ...(at.kf || {}), speed: freezeKeys(at, lt, Math.min(hold, at.dur - lt)) }, ...note });
      fx('freeze', t, Math.min(hold, at.start + at.dur - t), { drain: 0.85, rim: color || '#ff2b33', glow: 0.5 });
      fx('shake', t, 0.22, { amount: 0.55 });
      fx('impact_frame', t, 0.07, { style: 1, amount: 0.5 });
      if (word) out.push({ ...title(word, t, Math.min(1.4, hold + 0.5), 'stamp', color), ...note });
      sfx('impact', t, 0.5);
      break;
    }
    case 'blood_drop': {
      const w = Math.max(0, Number.isFinite(+op.word_at) ? +op.word_at : T - 1.2);
      const ws = shotsAt(p, w).at!;
      const hold = Math.max(0.3, Math.min(T - w, ws.start + ws.dur - w));
      out.push({ op: 'set', id: ws.id, kf: { ...(ws.kf || {}), speed: freezeKeys(ws, w - ws.start, hold) }, ...note });
      fx('freeze', w, hold, { drain: 0.9, rim: '#ffb060', glow: 0.4 });
      if (word) out.push({ ...title(word, w, Math.max(0.6, T - w), 'sweep', '#b3000c'), ...note });
      const a = pt(op.anchor, { x: 0.5, y: 0.7 });
      const bd = 1.4;
      fx('blood_lens', T - 0.14 * bd, bd, { size: 1.1, clear: 0.5 }, a);
      if (needCut()) out.push({ op: 'set', id: cut!.id, transition: { type: 'ink', dur: 0.6, at: a }, ...note });
      fx('shockwave', T, 0.5, { amount: 0.6, color: '#ff2b33' }, a);
      sfx('hit', w + 0.05, 0.35);
      sfx('subdrop', T, 0.55);
      break;
    }
    case 'plastic_burst': {
      const a = pt(op.anchor, { x: 0.5, y: 0.72 });
      const shot = before || at;
      const s0 = Math.max(shot.start, T - 0.8);
      fx('plastic_wrap', s0, T - s0, { amount: 0.6, crease: 0.6 });
      out.push({ op: 'set', id: shot.id, kf: { ...(shot.kf || {}), scale: scaleKeys(shot, s0 - shot.start, T - shot.start, 1, 1.08) }, ...note });
      if (needCut()) out.push({ op: 'set', id: cut!.id, transition: { type: 'tear', dur: 0.45, at: a }, ...note });
      fx('shockwave', T, 0.5, { amount: 0.7, color: '#ffffff' }, a);
      fx('sparks_burst', T, 0.6, { amount: 1, spread: 0.7, color: '#9a0010' }, a);
      fx('impact_frame', T, 0.07, { style: 1, amount: 0.5 });
      sfx('riser', s0, 0.3);
      sfx('rip', T - 0.02, 0.45);
      sfx('impact', T + 0.3, 0.5);
      break;
    }
    case 'crt_dive': {
      const shot = before || at;
      const s0 = Math.max(shot.start, T - 0.9);
      fx('crt', s0, T - s0, { curve: 0.7, mask: 0.5 });
      out.push({ op: 'set', id: shot.id, kf: { ...(shot.kf || {}), scale: scaleKeys(shot, s0 - shot.start, T - shot.start, 1, 0.62) }, ...note });
      if (needCut()) out.push({ op: 'set', id: cut!.id, transition: { type: 'dive', dur: 0.4, at: { x: 0.5, y: 0.5 }, to: { x: 0.5, y: 0.45 } }, ...note });
      fx('speed_streaks', T, 0.5, { amount: 0.7 });
      fx('exposure_wash', T - 0.04, 0.3, { amount: 0.55, peak: 0.25 });
      sfx('riser', s0, 0.3);
      sfx('impact', T + 0.3, 0.5);
      break;
    }
    case 'polaroid_toss': {
      if (!needCut() || !before?.media) break;
      const d = 0.75;
      const srcEnd = (before.in ?? 0) + before.dur * (before.speed ?? 1);
      const k = { scale: [{ t: 0, v: 1, e: 'in' }, { t: d, v: 0.62 }], rotation: [{ t: 0, v: 0, e: 'in' }, { t: d, v: -31 }], x: [{ t: 0.12, v: 0, e: 'in' }, { t: d, v: -1.3 }] };
      out.push({ op: 'add', media: before.media, track: op.track || '@overlay', start: r4(T), dur: d, in: r4(Math.max(0, srcEnd - 0.04)), speed: 0.05, ...(before.focus ? { focus: before.focus } : {}), kf: k, name: 'polaroid', ...note });
      out.push({ op: 'graphic', start: r4(T), dur: d, gw: 1.0, svg: '<svg viewBox="0 0 900 1600"><rect x="14" y="14" width="872" height="1572" rx="6" fill="none" stroke="#f4f1ea" stroke-width="28"/><rect x="0" y="1380" width="900" height="220" fill="#f4f1ea"/></svg>', kf: k, ...note });
      fx('exposure_wash', T, 0.15, { amount: 0.5, peak: 0.2 });
      sfx('shutter', T, 0.45);
      sfx('whoosh', T + 0.3, 0.3);
      break;
    }
    case 'glass_shatter': {
      const a = pt(op.anchor, { x: 0.62, y: 0.7 });
      if (needCut()) out.push({ op: 'set', id: cut!.id, transition: { type: 'shatter', dur: 0.55, at: a }, ...note });
      fx('shake', T, 0.25, { amount: 0.5 });
      sfx('impact', T, 0.5);
      sfx('glass', T + 0.3, 0.4);
      break;
    }
    case 'lens_blood': {
      const a = pt(op.anchor, { x: 0.22, y: 0.2 });
      fx('blood_lens', t, 1.4, { size: 1.2, clear: 0.5 }, a);
      sfx('hit', t, 0.4);
      sfx('rip', t + 0.3, 0.3);
      break;
    }
    case 'light_title': {
      const d = Math.min(2.5, Math.max(0.6, +op.dur || 1.2));
      if (!word) { issues.push(`${tag}: piece light_title needs "word"`); break; }
      out.push({ ...title(word, t, d, 'sweep', color), ...note });
      fx('light_sweep', t - 0.05, 0.6, { strength: 0.8, width: 0.14, tint: color || '#ffd9a8' });
      sfx('whoosh', t, 0.3);
      break;
    }
    case 'pupil_loop': {
      const { shots } = shotsAt(p, 0);
      const last = shots[shots.length - 1], first = shots[0];
      const eye = (c?: Clip) => (c?.focus ? { x: 0.5, y: 0.4 } : { x: 0.5, y: 0.42 });
      const a = pt(op.anchor, eye(last)), a0 = pt(op.open_anchor, eye(first));
      const s0 = Math.max(last.start, dur - 0.8);
      out.push({ op: 'set', id: last.id, kf: { ...(last.kf || {}), scale: scaleKeys(last, s0 - last.start, last.dur, 1, 2.2) }, ...note });
      fx('aperture', s0, dur - s0, { mode: 1, shape: 0 }, a);
      fx('aperture', 0, 0.5, { mode: 0, shape: 0 }, a0);
      sfx('hit', dur - 0.45, 0.3);
      break;
    }
  }
  return out;
}
