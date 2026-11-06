// Live previews of transitions and text animations, rendered by the real compositor and text
// engine on two sample shots, so each picker tile shows exactly what the effect does.
import { Clip, STANDARD_CAPTION, TextAnimIn, TextAnimOut, TransitionType } from '../state/types';
import { Compositor } from './compositor';
import { loadLogo } from './logo';
import { renderText } from './text';
import { logoLayerFx, NO_FX, transitionFx } from './transitions';
import { graphicCanvas, revealFx, svgSize } from './custom';
import type { FxPreset } from './fxlibrary';
import { FxDef, fxCode, fxParams } from './fxlib';

export const PW = 144, PH = 256;
let comp: Compositor | null = null;
let shotA: HTMLCanvasElement | null = null;
let shotB: HTMLCanvasElement | null = null;

function makeShot(kind: 'a' | 'b'): HTMLCanvasElement {
  const c = document.createElement('canvas');
  c.width = PW * 2; c.height = PH * 2;
  const g = c.getContext('2d')!;
  const W = c.width, H = c.height;
  if (kind === 'a') {
    // night interior: cold blue with a red practical light and a figure in silhouette
    const bg = g.createLinearGradient(0, 0, 0, H);
    bg.addColorStop(0, '#0b1726'); bg.addColorStop(1, '#03060c');
    g.fillStyle = bg; g.fillRect(0, 0, W, H);
    const lamp = g.createRadialGradient(W * 0.72, H * 0.3, 4, W * 0.72, H * 0.3, W * 0.6);
    lamp.addColorStop(0, 'rgba(255,60,60,0.85)'); lamp.addColorStop(1, 'rgba(255,0,0,0)');
    g.fillStyle = lamp; g.fillRect(0, 0, W, H);
    g.fillStyle = '#05070c';
    g.beginPath(); g.ellipse(W * 0.45, H * 0.42, W * 0.13, H * 0.085, 0, 0, Math.PI * 2); g.fill();
    g.beginPath(); g.moveTo(W * 0.18, H); g.quadraticCurveTo(W * 0.45, H * 0.45, W * 0.74, H); g.fill();
    g.strokeStyle = 'rgba(160,200,255,0.25)'; g.lineWidth = 3;
    for (let i = 0; i < 9; i++) { g.beginPath(); g.moveTo(0, H * (0.1 + i * 0.1)); g.lineTo(W * 0.2, H * (0.12 + i * 0.1)); g.stroke(); }
  } else {
    // warm day exterior: sky, sun behind the subject, water
    const bg = g.createLinearGradient(0, 0, 0, H);
    bg.addColorStop(0, '#f2a65a'); bg.addColorStop(0.55, '#f7d9a6'); bg.addColorStop(0.56, '#2a7f8f'); bg.addColorStop(1, '#0e3b46');
    g.fillStyle = bg; g.fillRect(0, 0, W, H);
    const sun = g.createRadialGradient(W * 0.5, H * 0.38, 2, W * 0.5, H * 0.38, W * 0.5);
    sun.addColorStop(0, 'rgba(255,255,240,1)'); sun.addColorStop(0.2, 'rgba(255,230,180,0.8)'); sun.addColorStop(1, 'rgba(255,200,120,0)');
    g.fillStyle = sun; g.fillRect(0, 0, W, H);
    g.fillStyle = '#3b1f17';
    g.beginPath(); g.ellipse(W * 0.5, H * 0.36, W * 0.11, H * 0.07, 0, 0, Math.PI * 2); g.fill();
    g.beginPath(); g.moveTo(W * 0.24, H * 0.62); g.quadraticCurveTo(W * 0.5, H * 0.36, W * 0.76, H * 0.62); g.fill();
    g.strokeStyle = 'rgba(255,255,255,0.35)'; g.lineWidth = 2;
    for (let i = 0; i < 7; i++) { g.beginPath(); g.moveTo(W * 0.1 * i, H * (0.7 + i * 0.035)); g.lineTo(W * (0.1 * i + 0.25), H * (0.7 + i * 0.035)); g.stroke(); }
  }
  return c;
}

function ensure(): Compositor | null {
  if (comp) return comp;
  try {
    const c = document.createElement('canvas');
    comp = new Compositor(c, { preserve: true });
    comp.resize(PW, PH);
    shotA = makeShot('a');
    shotB = makeShot('b');
    void loadLogo();
    return comp;
  } catch {
    return null;
  }
}

const base = { x: 0, y: 0, scale: 1, rotation: 0, opacity: 1 };

/** Draw a transition at progress p into `target`. */
export function drawTransitionPreview(target: HTMLCanvasElement, type: TransitionType, p: number) {
  const C = ensure();
  if (!C || !shotA || !shotB) return;
  C.resize(PW, PH);
  C.begin('#000000');
  const fa = { ...NO_FX, ...transitionFx(type, p, 'out') };
  const fb = { ...NO_FX, ...transitionFx(type, p, 'in') };
  if (fa.visible) C.draw({ key: '__pa', version: 1, source: shotA, srcW: shotA.width, srcH: shotA.height, srcRot: 0, baseW: PW, baseH: PH, transform: base, fx: fa });
  if (fb.visible) C.draw({ key: '__pb', version: 1, source: shotB, srcW: shotB.width, srcH: shotB.height, srcRot: 0, baseW: PW, baseH: PH, transform: base, fx: fb });
  if (type === 'logo') C.drawLogo({ ...NO_FX, ...logoLayerFx(p) });
  blit(target);
}

function blit(target: HTMLCanvasElement) {
  if (!comp) return;
  if (target.width !== PW) { target.width = PW; target.height = PH; }
  const g = target.getContext('2d');
  if (!g) return;
  g.clearRect(0, 0, PW, PH);
  g.drawImage(comp.canvas as HTMLCanvasElement, 0, 0);
}

const sampleText: Clip = { id: '__pt', track: '', kind: 'text', start: 0, dur: 2.2, text: 'COULD IT BE\n*HIM*', style: { ...STANDARD_CAPTION, size: 0.07 } };

/** Draw a text animation at time t (seconds) of a 2.2 s sample caption into `target`. */
export function drawTextPreview(target: HTMLCanvasElement, anim: { in?: TextAnimIn; out?: TextAnimOut }, t: number) {
  const C = ensure();
  if (!C || !shotA) return;
  C.resize(PW, PH);
  C.begin('#000000');
  C.draw({ key: '__pa', version: 1, source: shotA, srcW: shotA.width, srcH: shotA.height, srcRot: 0, baseW: PW, baseH: PH, transform: base, fx: { ...NO_FX, flash: 0.35, flashColor: [0, 0, 0] } });
  const clip: Clip = { ...sampleText, id: `__pt_${anim.in || 'n'}_${anim.out || 'n'}`, anim: { in: anim.in || 'none', out: anim.out || 'none', inDur: anim.in === 'letters' ? 0.9 : anim.in === 'words' ? 0.6 : 0.45, outDur: 0.6 } };
  const r = renderText(clip, t, PW, PH, 'pv');
  if (r) C.draw({ key: clip.id, version: r.version, source: r.canvas as any, srcW: r.w, srcH: r.h, srcRot: 0, baseW: r.w, baseH: r.h, transform: { ...base, y: 0.05 }, fx: { ...NO_FX, dx: r.dx, opacity: r.opacity, scale: r.scale }, premultiplied: true });
  blit(target);
}

/** The progress at which a transition reads best as a still. */
export function stillProgress(type: TransitionType): number {
  if (type === 'logo') return 0.62;
  if (type.startsWith('dip') || type === 'flash' || type === 'punch' || type === 'glitch' || type === 'spin' || type === 'roll' || type === 'blink' || type === 'warp' || type.startsWith('zoom')) return 0.42;
  return 0.5;
}

/** Draw a starter effect or graphic at progress u (0..1) over a sample shot. */
export function drawFxPreview(target: HTMLCanvasElement, fx: FxPreset, u: number) {
  const C = ensure();
  if (!C || !shotA || !shotB) return;
  C.resize(PW, PH);
  C.begin('#000000');
  const shot = fx.kind === 'graphic' ? shotA : shotB;
  C.draw({ key: fx.kind === 'graphic' ? '__pa' : '__pb', version: 1, source: shot, srcW: shot.width, srcH: shot.height, srcRot: 0, baseW: PW, baseH: PH, transform: base, fx: NO_FX });
  const t = u * fx.dur;
  if (fx.kind === 'shader' && fx.code) {
    const beatAge = (t % 0.5);
    C.drawShader(fx.code, fx.blend, { t, p: u, dur: fx.dur, time: t, beat: Math.exp(-beatAge / 0.14), beatAge, energy: 0.6, opacity: 1, scale: 1, rot: 0, pos: [0.5, 0.42], seed: 3.1 });
  } else if (fx.kind === 'graphic' && fx.svg) {
    const clip: Clip = { id: `__fx_${fx.id}`, track: '', kind: 'graphic', start: 0, dur: fx.dur, svg: fx.svg, gw: fx.gw, glow: fx.glow, reveal: fx.reveal, blend: fx.blend };
    const gw = (fx.gw ?? 0.6) * PW;
    const cv = graphicCanvas(clip, gw * 2);
    if (cv) {
      const { vbW, vbH } = svgSize(fx.svg);
      const rf = revealFx(clip, t);
      const lfx = { ...NO_FX, ...rf };
      const bh = (gw * vbH) / vbW;
      if ((fx.glow ?? 0) > 0.01) C.draw({ key: `${clip.id}#g`, version: 1, source: cv, srcW: cv.width, srcH: cv.height, srcRot: 0, baseW: gw, baseH: bh, transform: { ...base, y: -0.05 }, fx: { ...lfx, blur: 0.25 + fx.glow! * 0.6, opacity: (lfx.opacity ?? 1) * fx.glow! }, premultiplied: true, blend: 'add' });
      C.draw({ key: clip.id, version: 1, source: cv, srcW: cv.width, srcH: cv.height, srcRot: 0, baseW: gw, baseH: bh, transform: { ...base, y: -0.05 }, fx: lfx, premultiplied: true, blend: fx.blend });
    }
  }
  blit(target);
}

// ---------- library looks and effects, previewed on the owner's own footage when there is some ----------

let photo: HTMLCanvasElement | null = null;
let photoUrl = '';
const photoWatchers = new Set<() => void>();

/** Use a frame of the owner's footage (a poster data URL) as the backdrop of the look and effect previews. */
export function setPreviewPhoto(url?: string | null) {
  const u = url || '';
  if (u === photoUrl) return;
  photoUrl = u;
  if (!u) { photo = null; photoWatchers.forEach(f => f()); return; }
  const img = new Image();
  img.onload = () => {
    if (photoUrl !== u) return;
    // cover-crop to the tile's 9:16, centred a little above the middle where faces usually sit
    const c = document.createElement('canvas');
    c.width = PW * 2; c.height = PH * 2;
    const g = c.getContext('2d')!;
    const s = Math.max(c.width / img.width, c.height / img.height);
    const w = img.width * s, h = img.height * s;
    g.drawImage(img, (c.width - w) / 2, Math.min(0, Math.max(c.height - h, (c.height - h) * 0.42)), w, h);
    photo = c;
    photoWatchers.forEach(f => f());
  };
  img.src = u;
}

export function onPreviewPhoto(cb: () => void) { photoWatchers.add(cb); return () => { photoWatchers.delete(cb); }; }

/** Draw a library look or effect at progress u (0..1) over the backdrop. */
export function drawLibPreview(target: HTMLCanvasElement, def: FxDef, u: number, params?: Record<string, number | string>) {
  const C = ensure();
  if (!C || !shotA || !shotB) return;
  C.resize(PW, PH);
  C.begin('#000000');
  const shot = photo || (def.group === 'look' || def.group === 'finish' ? shotB : shotA);
  C.draw({ key: photo ? `__ph${photoUrl.length}` : shot === shotA ? '__pa' : '__pb', version: photoUrl, source: shot, srcW: shot.width, srcH: shot.height, srcRot: 0, baseW: PW, baseH: PH, transform: base, fx: NO_FX });
  const dur = def.group === 'look' ? 2 : def.dur;
  const t = u * dur;
  const beatAge = t % 0.5;
  const anchor: [number, number] = def.anchor ? [0.5, 0.36] : [0.5, 0.5];
  C.drawShader(fxCode(def, fxParams(def, params)), def.blend, { t, p: def.group === 'look' ? 0.5 : u, dur, time: t, beat: Math.exp(-beatAge / 0.14), beatAge, energy: 0.6, opacity: 1, scale: 1, rot: 0, pos: anchor, seed: 3.1 }, `preview ${def.id}`);
  blit(target);
}
