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
  { id: 'emblem_dive', does: 'THE FLASH v10 drop: lightning crackles on the chest emblem, the camera dives through it on the drop and the next shot bursts out on a gold shockwave with light rays; zap then impact', takes: 'at (the drop, a cut), anchor (the emblem on the outgoing shot, default the chest under the framed face)' },
  { id: 'lightning_strike', does: 'THE FLASH v10 lens shatter: a bolt is thrown at the lens, the frame shatters where it hits with gold sparks; zap then glass', takes: 'at (a cut), anchor (where it hits: off the face)' },
  { id: 'time_stop', does: 'THE FLASH v10 stutter: time stops on the hit (frozen frame, drained colour, gold rim light), embers hang in the air, then time restarts on a gold shockwave; reverse then impact', takes: 'at (the hit), hold 0.6-1.4 (0.9)' },
  { id: 'speed_rift', does: 'THE FLASH v11 focal: a jagged rift tears open below his face with white-gold electric edges and the Speed Force churning inside, sparks off its edges, then the camera flies through it into the next shot; rip then boom', takes: 'at (a cut), anchor (the rift centre, default under the face)' },
  { id: 'bolt_split', does: 'THE FLASH v11 drop: a lightning bolt splits the frame on the cut and every outline in the new shot pulses gold; zap', takes: 'at (the drop, a cut)' },
  { id: 'speedforce_loop', does: 'THE FLASH v10 loop: the last second dissolves into the Speed Force (the picture pulled toward the centre with streaks racing past), then the push lands exactly on frame 0; riser into it', takes: 'nothing (it builds on the end of the edit)' },
  { id: 'pupil_loop', does: 'v4/v7 loop: the last shot pushes into the eye as an aperture closes on it, frame 0 opens from the same black on the first shot\'s eye: the wrap is black to black, invisible; heartbeat under the close', takes: 'anchor (the eye on the last shot, default the focus point), open_anchor (the eye on frame 0)' },
];

/** The Speed Force rift (v11 focal): a tear with electric edges and the Speed Force churning inside. */
const RIFT = `vec4 effect(vec2 uv, float t, float p) { vec2 q = toLocal(uv); float open = easeOutCubic(stage(p, 0.1, 0.85)); float wob = (fbm(vec2(q.x * 9.0, floor(t * 18.0))) - 0.5) * 0.05 + (noise(vec2(q.x * 40.0, t * 6.0)) - 0.5) * 0.012; float len = mix(0.02, 0.3, easeOutExpo(stage(p, 0.0, 0.4))); float along = 1.0 - smoothstep(len * 0.8, len, abs(q.x)); float hw = (0.004 + 0.07 * open) * along * (1.0 - 0.6 * smoothstep(0.0, len, abs(q.x))); float d = abs(q.y - wob) - hw; vec3 pic = frame(uv); vec2 sw = rot2(t * 2.0) * q; float churn = fbm(sw * 7.0 + vec2(t * 3.0, 0.0)); float streak = smoothstep(0.6, 0.95, fbm(vec2(atan(q.y, q.x) * 3.0, length(q) * 14.0 - t * 12.0))); vec3 inner = mix(vec3(0.9, 0.42, 0.05), vec3(1.0, 0.93, 0.62), churn) * (0.55 + 0.8 * streak) + frame(uv + q * 0.25 * open) * 0.25; float inside = fillAA(d); float edge = glow(abs(d), 0.0035) * along; float halo = glow(max(d, 0.0), 0.05) * along * open; vec3 col = pic + vec3(1.0, 0.8, 0.4) * halo * 0.55 + lightSpill(uv, uPos, vec3(1.0, 0.7, 0.3), 0.25) * open * 0.5; col = mix(col, inner, inside); col += vec3(1.0, 0.97, 0.85) * edge * (1.1 + 0.5 * sin(t * 60.0)); vec4 sp = sparks(q, vec2(0.0, 0.0), stage(p, 0.15, 1.0) * 0.8, 3.0, 0.6, vec3(1.0, 0.75, 0.3)); col = mix(col, sp.rgb, sp.a * 0.8); return vec4(col, envelope(p, 0.0, 0.05, 0.94, 1.0)); }`;

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
    case 'emblem_dive': {
      const a = pt(op.anchor, { x: 0.5, y: 0.62 });
      fx('lightning_arc', T - 0.45, 0.45, { amount: 1, color: color || '#ffc23d' }, a);
      if (needCut()) out.push({ op: 'set', id: cut!.id, transition: { type: 'dive', dur: 0.45, at: a, to: { x: 0.5, y: 0.45 } }, ...note });
      fx('shockwave', T + 0.02, 0.55, { amount: 0.85, color: '#ffd27a' }, { x: 0.5, y: 0.55 });
      fx('light_rays', T, 1.2, { strength: 0.6, tint: '#ffe0a0', length: 0.5 }, { x: 0.5, y: 0.08 });
      sfx('zap', T - 0.45, 0.4);
      sfx('impact', T, 0.55);
      break;
    }
    case 'lightning_strike': {
      const a = pt(op.anchor, { x: 0.66, y: 0.3 });
      fx('lightning_arc', T - 0.35, 0.38, { amount: 1, color: color || '#ffd04a' }, a);
      if (needCut()) out.push({ op: 'set', id: cut!.id, transition: { type: 'shatter', dur: 0.5, at: a }, ...note });
      fx('sparks_burst', T, 0.6, { amount: 1, spread: 0.8, color: '#ffc04a' }, a);
      sfx('zap', T - 0.35, 0.4);
      sfx('glass', T, 0.45);
      break;
    }
    case 'time_stop': {
      const hold = Math.min(1.4, Math.max(0.6, +op.hold || 0.9));
      const lt = t - at.start;
      const h = Math.min(hold, at.dur - lt);
      out.push({ op: 'set', id: at.id, kf: { ...(at.kf || {}), speed: freezeKeys(at, lt, h) }, ...note });
      fx('freeze', t, h, { drain: 0.8, rim: color || '#ffc74d', glow: 0.5 });
      fx('embers', t, h, { amount: 0.8, density: 0.6, speed: 0.3, color: '#ffb84a' });
      fx('shockwave', t + h, 0.5, { amount: 0.75, color: '#ffd27a' }, { x: 0.5, y: 0.5 });
      sfx('reverse', t, 0.35);
      sfx('impact', t + h, 0.5);
      break;
    }
    case 'speed_rift': {
      const a = pt(op.anchor, { x: 0.5, y: 0.66 });
      const s0 = Math.max(0, T - 0.7);
      out.push({ op: 'shader', start: r4(s0), dur: r4(T + 0.05 - s0), blend: 'normal', at: a, name: 'speed rift', code: RIFT, ...note });
      if (needCut()) out.push({ op: 'set', id: cut!.id, transition: { type: 'dive', dur: 0.45, at: a, to: { x: 0.5, y: 0.45 } }, ...note });
      fx('speed_force', T, 0.5, { amount: 0.55, color: '#ffc74d' }, { x: 0.5, y: 0.5 });
      sfx('rip', s0 + 0.05, 0.4);
      sfx('boom', T, 0.55);
      break;
    }
    case 'bolt_split': {
      if (needCut()) out.push({ op: 'set', id: cut!.id, transition: { type: 'bolt', dur: 0.4 }, ...note });
      fx('edge_pulse', T, 0.9, { amount: 0.7, color: color || '#ffc23d' });
      sfx('zap', T, 0.5);
      break;
    }
    case 'speedforce_loop': {
      const s0 = Math.max(0, dur - 1.0);
      fx('speed_force', s0, dur - s0 - 0.05, { amount: 0.5, color: '#ffc74d' }, { x: 0.5, y: 0.5 });
      fx('speed_streaks', s0, dur - s0, { amount: 0.6, color: '#ffd980' });
      sfx('riser', s0, 0.3);
      out.push({ op: 'loop', style: 'push', dur: 0.5, ...note });
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
