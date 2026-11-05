import { TransitionType } from '../state/types';
import { clamp } from '../state/util';

/** Per-layer effect parameters a transition sets on the outgoing ('out') and incoming ('in') clip. */
export interface LayerFx {
  visible: boolean;
  dx: number; dy: number; // frame fractions
  scale: number;
  rot: number; // degrees
  opacity: number;
  blur: number; // 0..1 (fraction of frame height * 0.035)
  dirX: number; dirY: number; // directional blur, frame fractions
  radial: number; // radial zoom blur toward the centre, 0..1
  /** 0 none, 1 linear wipe, 2 iris, 3 logo counter, 4 eyelid slit, 5 noise dissolve, 6 brightest-first, 7 lightning */
  mask: 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7;
  maskX: number; maskY: number; // direction for linear masks, centre for noise masks (frame fractions)
  maskP: number;
  edge: [number, number, number]; // glow colour on dissolve edges
  edgeW: number;
  chroma: number; // RGB split, frame fraction
  flash: number;
  flashColor: [number, number, number];
  invert: number;
  leak: number; // warm light leak strength
  leakPos: number; // position of the leak band across the frame (0..1)
  /** Draw the layer in two halves split along a line through the centre (normal nx, ny) pushed apart by gap. */
  split: null | { nx: number; ny: number; gap: number };
  /** Draw this (outgoing) layer above the incoming one. */
  top: boolean;
  /** Logo geometry (logo layer and the counter mask): scale, anchor in logo uv kept at frame centre. */
  logoS: number; logoAx: number; logoAy: number;
}

export const NO_FX: LayerFx = {
  visible: true, dx: 0, dy: 0, scale: 1, rot: 0, opacity: 1, blur: 0, dirX: 0, dirY: 0, radial: 0,
  mask: 0, maskX: 1, maskY: 0, maskP: 1, edge: [0, 0, 0], edgeW: 0, chroma: 0, flash: 0, flashColor: [0, 0, 0],
  invert: 0, leak: 0, leakPos: 0.5, split: null, top: false, logoS: 1, logoAx: 0.5, logoAy: 0.5,
};

const io3 = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2);
const io5 = (t: number) => (t < 0.5 ? 16 * t ** 5 : 1 - (-2 * t + 2) ** 5 / 2);
const out3 = (t: number) => 1 - (1 - t) ** 3;
const in3 = (t: number) => t * t * t;
const outBack = (t: number) => { const c1 = 2.2, c3 = c1 + 1; return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2; };
const bump = (p: number) => Math.sin(Math.PI * clamp(p, 0, 1)); // 0 → 1 → 0
const seg = (p: number, a: number, b: number) => clamp((p - a) / (b - a), 0, 1);
const DIRS: Record<string, [number, number]> = { left: [-1, 0], right: [1, 0], up: [0, -1], down: [0, 1] };

/** The voidfx 'o' counter centroid in logo uv (measured on the supplied logo file). */
export const LOGO_O: [number, number] = [0.3313, 0.5659];

/** Geometry of the logo fly-through at progress p: slam in, push to the 'o', fly through it. */
export function logoGeom(p: number): { s: number; ax: number; ay: number; opacity: number; radial: number } {
  if (p < 0.3) {
    const q = seg(p, 0, 0.3);
    return { s: 1.75 - 0.75 * outBack(q), ax: 0.5, ay: 0.5, opacity: clamp(q * 3, 0, 1), radial: 0.25 * (1 - q) };
  }
  if (p < 0.52) {
    const q = io3(seg(p, 0.3, 0.52));
    return { s: 1 + 0.14 * q, ax: 0.5 + (LOGO_O[0] - 0.5) * q, ay: 0.5 + (LOGO_O[1] - 0.5) * q, opacity: 1, radial: 0 };
  }
  const q = in3(seg(p, 0.52, 1));
  return { s: 1.14 * Math.exp(Math.log(70 / 1.14) * q), ax: LOGO_O[0], ay: LOGO_O[1], opacity: 1, radial: 0.55 * bump(q) };
}

/** Effects for the logo layer itself. */
export function logoLayerFx(p: number): Partial<LayerFx> {
  const g = logoGeom(p);
  return { logoS: g.s, logoAx: g.ax, logoAy: g.ay, opacity: g.opacity, radial: g.radial, visible: p < 0.995 };
}

/** Effects for one side of a transition at progress p (0..1). */
export function transitionFx(type: TransitionType, p: number, role: 'out' | 'in'): Partial<LayerFx> {
  p = clamp(p, 0, 1);
  const e = io3(p);
  const isIn = role === 'in';
  const parts = type.split('_');
  const kind = type === 'light_leak' ? 'leak' : parts[0];
  const dirName = parts[1];
  const dir = DIRS[dirName || 'left'] || DIRS.left;

  switch (kind) {
    case 'crossfade':
      return isIn ? { opacity: e } : {};
    case 'dip': {
      const c: [number, number, number] = dirName === 'white' ? [1, 1, 1] : [0, 0, 0];
      return isIn
        ? { visible: p >= 0.5, flash: clamp((1 - p) * 2, 0, 1), flashColor: c }
        : { visible: p < 0.5, flash: clamp(p * 2, 0, 1), flashColor: c };
    }
    case 'flash': {
      // a flare that keeps the picture: peaks at 0.75, never a full white-out
      const w: [number, number, number] = [1, 0.97, 0.92];
      return isIn
        ? { visible: p >= 0.5, flash: 0.75 * clamp((1 - p) * 2, 0, 1) ** 2, flashColor: w, scale: 1 + 0.06 * (1 - io3(seg(p, 0.5, 1))) }
        : { visible: p < 0.5, flash: 0.75 * clamp(p * 2, 0, 1) ** 2, flashColor: w };
    }
    case 'slide':
      return isIn ? { dx: -dir[0] * (1 - e), dy: -dir[1] * (1 - e) } : { flash: 0.25 * e, flashColor: [0, 0, 0] };
    case 'push':
      return isIn ? { dx: -dir[0] * (1 - e), dy: -dir[1] * (1 - e) } : { dx: dir[0] * e, dy: dir[1] * e };
    case 'wipe':
      return isIn ? { mask: 1, maskX: dir[0], maskY: dir[1], maskP: -0.03 + 1.06 * e } : {};
    case 'iris':
      return isIn ? { mask: 2, maskP: e } : {};
    case 'zoom': {
      const inward = dirName !== 'out';
      const q = io5(p);
      const b = bump(p);
      if (isIn) return { visible: p >= 0.5, scale: inward ? 1 + 0.6 * (1 - q) : 1 - 0.35 * (1 - q), radial: 0.7 * b, opacity: clamp((p - 0.45) * 10, 0, 1) };
      return { visible: p < 0.55, scale: inward ? 1 + 0.9 * q : 1 - 0.45 * q, radial: 0.7 * b };
    }
    case 'whip': {
      const q = io5(p);
      const b = bump(p) ** 0.6;
      const amt = 0.12 * b;
      if (isIn) return { dx: -dir[0] * (1 - q), dy: -dir[1] * (1 - q), dirX: dir[0] * amt, dirY: dir[1] * amt };
      return { dx: dir[0] * q, dy: dir[1] * q, dirX: dir[0] * amt, dirY: dir[1] * amt };
    }
    case 'spin': {
      const q = io3(p);
      const b = bump(p);
      if (isIn) return { visible: p >= 0.5, rot: -180 * (1 - q), scale: 0.7 + 0.3 * q, blur: 0.6 * b };
      return { visible: p < 0.5, rot: 180 * q, scale: 1 - 0.3 * q, blur: 0.6 * b };
    }
    case 'blur': {
      const b = bump(p);
      return isIn ? { opacity: e, blur: b } : { blur: b };
    }
    case 'glitch': {
      const b = bump(p);
      const k = Math.floor(p * 24);
      const jitter = ((Math.sin(k * 12.9898) * 43758.5453) % 1) * 0.06 * b;
      return isIn
        ? { visible: p >= 0.5, dx: jitter, chroma: 0.02 * b, flash: 0.15 * b, flashColor: [1, 1, 1] }
        : { visible: p < 0.5, dx: -jitter, chroma: 0.02 * b };
    }
    // ---------- themed set (from the voidfx catalogue) ----------
    case 'logo': {
      // the incoming shot is seen through the logo's 'o', which grows until it fills the frame
      const g = logoGeom(p);
      if (isIn) return { visible: p >= 0.5, mask: 3, logoS: g.s, logoAx: g.ax, logoAy: g.ay, radial: g.radial * 0.6 };
      return { visible: p < 0.97, flash: 0.45 * seg(p, 0, 0.3), flashColor: [0, 0, 0], scale: 1 + 0.05 * e };
    }
    case 'blink': {
      // eyelids close (blur, double vision, darkening) and blink open on the next shot
      if (isIn) {
        const q = out3(seg(p, 0.5, 1));
        return { visible: p >= 0.5, mask: 4, maskP: q, blur: 0.5 * (1 - q), flash: 0.5 * (1 - q), flashColor: [0, 0, 0] };
      }
      const q = in3(seg(p, 0, 0.5));
      return { visible: p < 0.5, mask: 4, maskP: 1 - q, blur: 0.6 * q, chroma: 0.008 * q, flash: 0.45 * q, flashColor: [0.05, 0, 0] };
    }
    case 'bolt': {
      // a forked lightning bolt strikes down the frame (maskY = how far it has struck, maskX = its shape);
      // the next shot opens out from the channel; its light falls on both shots and flickers out
      const strike = clamp(p / 0.16, 0, 1);
      const glow = p < 0.16 ? 0.35 + 0.65 * strike : Math.max(0, 1 - (p - 0.16) / 0.6) * (0.78 + 0.22 * Math.sin(p * 95));
      if (isIn) return { mask: 7, maskX: 0.37, maskY: strike, maskP: -0.02 + 0.92 * io3(clamp((p - 0.1) / 0.8, 0, 1)), edge: [1.0, 0.8, 0.28], edgeW: glow, flash: 0.12 * glow, flashColor: [1, 0.92, 0.7] };
      return { flash: 0.2 * glow, flashColor: [1, 0.9, 0.62], chroma: 0.003 * glow, dx: 0.004 * glow * Math.sin(p * 120) };
    }
    case 'ink': {
      // a blood-red stain blooms from the centre and opens into the next shot
      return isIn ? { mask: 5, maskP: -0.12 + 0.98 * io3(p), maskX: 0.5, maskY: 0.5, edge: [0.42, 0.0, 0.02], edgeW: 0.09 } : {};
    }
    case 'burn': {
      // film-burn holes with an ember rim eat through the outgoing frame
      return isIn ? { mask: 5, maskP: -0.12 + 1.1 * io3(p), maskX: 0.62, maskY: 0.3, edge: [1.0, 0.45, 0.08], edgeW: 0.07 } : { flash: 0.15 * bump(p), flashColor: [1, 0.5, 0.15] };
    }
    case 'slash': {
      // a blade cuts the frame diagonally; the halves fly apart onto the next shot
      if (isIn) return { scale: 1.06 - 0.06 * out3(p), flash: 0.25 * (1 - seg(p, 0, 0.4)), flashColor: [1, 1, 1] };
      const q = in3(seg(p, 0.15, 1));
      return { visible: p < 0.98, split: { nx: 0.34, ny: 0.94, gap: 1.2 * q }, chroma: 0.004 * bump(p), top: true };
    }
    case 'punch': {
      // impact frame: a one-frame negative and a zoom punch on the cut
      if (isIn) {
        const q = seg(p, 0.5, 1);
        return { visible: p >= 0.5, scale: 1.14 - 0.14 * out3(q), invert: q < 0.08 ? 1 : 0, chroma: 0.01 * (1 - q), radial: 0.4 * (1 - q) };
      }
      return { visible: p < 0.5, scale: 1 + 0.1 * in3(seg(p, 0, 0.5)), radial: 0.3 * seg(p, 0, 0.5) };
    }
    case 'leak': {
      // a warm light leak sweeps across while the shots cross under it
      const pos = -0.3 + 1.6 * io3(p);
      const amt = 0.9 * bump(p);
      return isIn ? { opacity: io3(seg(p, 0.3, 0.7)), leak: amt, leakPos: pos } : { leak: amt, leakPos: pos };
    }
    case 'roll': {
      // the world rolls 90 degrees with rotational blur
      const q = io5(p);
      const b = bump(p);
      if (isIn) return { visible: p >= 0.5, rot: -90 * (1 - q), scale: 1 + 0.8 * (1 - q), blur: 0.7 * b };
      return { visible: p < 0.5, rot: 90 * q, scale: 1 + 0.8 * q, blur: 0.7 * b };
    }
    case 'shadow': {
      // darkness swallows the frame; the next shot emerges brightest-first
      if (isIn) return { visible: p >= 0.35, mask: 6, maskP: io3(seg(p, 0.35, 1)) };
      return { flash: 0.95 * io3(seg(p, 0, 0.6)), flashColor: [0, 0, 0] };
    }
    case 'warp': {
      // a radial pull through the centre, as if into the Speed Force
      const b = bump(p);
      if (isIn) return { visible: p >= 0.5, scale: 1 + 0.35 * (1 - io3(seg(p, 0.5, 1))), radial: 0.9 * b, flash: 0.2 * b, flashColor: [1, 0.95, 0.8] };
      return { visible: p < 0.5, scale: 1 + 0.45 * in3(seg(p, 0, 0.5)), radial: 0.9 * b };
    }
    default:
      return isIn ? { opacity: e } : {};
  }
}

export const TRANSITION_LABELS: Record<TransitionType, string> = {
  crossfade: 'Crossfade', dip_black: 'Dip to black', dip_white: 'Dip to white', flash: 'Flare',
  slide_left: 'Slide left', slide_right: 'Slide right', slide_up: 'Slide up', slide_down: 'Slide down',
  push_left: 'Push left', push_right: 'Push right', push_up: 'Push up', push_down: 'Push down',
  wipe_left: 'Wipe left', wipe_right: 'Wipe right', wipe_up: 'Wipe up', wipe_down: 'Wipe down',
  iris: 'Iris', zoom_in: 'Zoom in', zoom_out: 'Zoom out',
  whip_left: 'Whip left', whip_right: 'Whip right', whip_up: 'Whip up', whip_down: 'Whip down',
  spin: 'Spin', blur: 'Blur', glitch: 'Glitch', bolt: 'Lightning strike',
  logo: 'voidfx logo fly-through', blink: 'Blink (eyelids)', ink: 'Blood bloom', burn: 'Film burn', slash: 'Blade slash',
  punch: 'Impact frame', light_leak: 'Light leak', roll: 'Roll 90°', shadow: 'Shadow (brightest first)', warp: 'Warp pull',
};

/** Groups for the transitions panel. */
export const TRANSITION_GROUPS: { name: string; items: TransitionType[] }[] = [
  { name: 'Signature', items: ['logo', 'bolt', 'blink', 'ink', 'burn', 'slash', 'punch', 'shadow', 'warp', 'roll', 'light_leak'] },
  { name: 'Motion', items: ['whip_left', 'whip_right', 'whip_up', 'whip_down', 'push_left', 'push_right', 'push_up', 'push_down', 'slide_left', 'slide_right', 'slide_up', 'slide_down', 'zoom_in', 'zoom_out', 'spin'] },
  { name: 'Reveal', items: ['iris', 'wipe_left', 'wipe_right', 'wipe_up', 'wipe_down', 'glitch'] },
  { name: 'Soft', items: ['crossfade', 'blur', 'dip_black', 'dip_white', 'flash'] },
];

/** Default length per transition (seconds). The logo needs room for its slam and fly-through. */
export function defaultTransitionDur(t: TransitionType): number {
  if (t === 'logo') return 1.2;
  if (t === 'punch' || t === 'glitch' || t.startsWith('whip') || t === 'slash') return 0.35;
  if (t === 'blink' || t === 'shadow' || t === 'ink' || t === 'burn') return 0.7;
  if (t === 'bolt') return 0.55;
  return 0.5;
}

/** Transitions that count as a flash for the flash-rate rule. */
export const FLASHY = new Set<TransitionType>(['flash', 'dip_white', 'punch', 'glitch', 'warp', 'bolt']);
