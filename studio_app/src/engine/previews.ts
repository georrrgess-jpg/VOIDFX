// Live previews of transitions and text animations, rendered by the real compositor and text
// engine on two sample shots, so each picker tile shows exactly what the effect does.
import { Clip, STANDARD_CAPTION, TextAnimIn, TextAnimOut, TransitionType } from '../state/types';
import { Compositor } from './compositor';
import { loadLogo } from './logo';
import { renderText } from './text';
import { logoLayerFx, NO_FX, transitionFx } from './transitions';

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
