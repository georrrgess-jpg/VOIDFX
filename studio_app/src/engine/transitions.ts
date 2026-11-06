import { TransitionSpec, TransitionType } from '../state/types';
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
  /** 0 none, 1 linear wipe, 2 iris, 3 logo counter, 4 eyelid slit, 5 noise dissolve, 6 brightest-first, 7 lightning,
   * 8 jagged tear, 9 six-blade aperture, 10 wiper arm, 11 venetian blinds */
  mask: 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11;
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
  /** Screen-space warp: 0 none, 1/2 plane turning about a vertical/horizontal axis (cube, flip), 3 shatter,
   * 4 sliding strips, 5 ripple, 6 swirl, 7 pixelate, 8 kaleidoscope, 9 heat haze, 10 datamosh blocks. */
  warp: number; warpP: number; warpA: number; warpC: [number, number];
  /** Centre of the radial blur in layer uv; centre of the iris and aperture masks in frame fractions. */
  radC: [number, number]; iris: [number, number];
  /** Exposure push (0 = none, 1 = +400 %); colour of the light leak. */
  expo: number; leakColor: [number, number, number];
}

export const NO_FX: LayerFx = {
  visible: true, dx: 0, dy: 0, scale: 1, rot: 0, opacity: 1, blur: 0, dirX: 0, dirY: 0, radial: 0,
  mask: 0, maskX: 1, maskY: 0, maskP: 1, edge: [0, 0, 0], edgeW: 0, chroma: 0, flash: 0, flashColor: [0, 0, 0],
  invert: 0, leak: 0, leakPos: 0.5, split: null, top: false, logoS: 1, logoAx: 0.5, logoAy: 0.5,
  warp: 0, warpP: 0, warpA: 0, warpC: [0.5, 0.5], radC: [0.5, 0.5], iris: [0.5, 0.5], expo: 0, leakColor: [1, 0.58, 0.22],
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

/** Default anchor: where a face sits once a shot is framed on its focus point. */
const FACE: [number, number] = [0.5, 0.42];

/** Effects for one side of a transition at progress p (0..1). `spec` carries the anchors (at, to). */
export function transitionFx(type: TransitionType, p: number, role: 'out' | 'in', spec?: Partial<TransitionSpec>): Partial<LayerFx> {
  p = clamp(p, 0, 1);
  const e = io3(p);
  const isIn = role === 'in';
  const parts = type.split('_');
  const kind = type === 'light_leak' ? 'leak' : type === 'light_sweep' ? 'sweep' : parts[0];
  // a dive goes into the face by default; a burst or a shatter lands off it (never over his face)
  const at: [number, number] = spec?.at ? [spec.at.x, spec.at.y] : kind === 'shatter' ? [0.62, 0.66] : FACE;
  const to: [number, number] = spec?.to ? [spec.to.x, spec.to.y] : spec?.at ? at : FACE;
  const anchor = isIn ? to : at;
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
      return isIn ? { mask: 2, maskP: e, iris: spec?.to || spec?.at ? to : [0.5, 0.5] } : {};
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
    // ---------- added: physical and designed moves ----------
    case 'cube': {
      // the shots are faces of a cube turning away; the cube recedes a little mid-turn
      const vert = dirName === 'up' || dirName === 'down';
      const sgn = dirName === 'left' || dirName === 'up' ? 1 : -1;
      const q = io3(p), recede = 1 - 0.1 * bump(p);
      const th = isIn ? sgn * (Math.PI / 2) * (1 - q) : -sgn * (Math.PI / 2) * q;
      return { warp: vert ? 2 : 1, warpP: th, warpA: 0.5, scale: recede, visible: isIn ? p > 0.02 : p < 0.98 };
    }
    case 'flip': {
      // a card flip about the centre: the first shot turns edge-on, the next turns in from behind
      const vert = dirName === 'v';
      if (isIn) return { visible: p >= 0.5, warp: vert ? 2 : 1, warpP: -(Math.PI / 2) * (1 - out3(seg(p, 0.5, 1))), warpA: 0, scale: 1 - 0.08 * bump(p) };
      return { visible: p < 0.5, warp: vert ? 2 : 1, warpP: (Math.PI / 2) * in3(seg(p, 0, 0.5)), warpA: 0, scale: 1 - 0.08 * bump(p) };
    }
    case 'shatter': {
      // the frame cracks at the anchor, then bursts into shards that fly at the lens over the next shot
      if (isIn) return { scale: 1.08 - 0.08 * out3(seg(p, 0.3, 1)), flash: 0.35 * (1 - seg(p, 0.28, 0.6)), flashColor: [1, 1, 1] };
      const crack = seg(p, 0.05, 0.3);
      return { visible: p < 0.97, top: true, warp: 3, warpP: in3(seg(p, 0.28, 1)) * 1.1, warpA: crack * (1 - seg(p, 0.3, 0.55)), warpC: at, flash: 0.15 * crack * (1 - seg(p, 0.3, 0.5)), flashColor: [1, 1, 1] };
    }
    case 'slices': {
      // vertical strips of the frame slide away in alternating directions onto the next shot
      if (isIn) return { scale: 1.05 - 0.05 * out3(p) };
      return { visible: p < 0.99, top: true, warp: 4, warpP: p, warpA: 7 };
    }
    case 'blinds': {
      // backlit venetian slats open from the top down onto the next shot
      if (isIn) return { mask: 11, maskP: e, edge: [1.0, 0.86, 0.6], edgeW: 0.5 };
      return { flash: 0.35 * bump(p), flashColor: [0, 0, 0] };
    }
    case 'ripple': {
      const b = bump(p);
      if (isIn) return { warp: 5, warpP: p, warpA: b, warpC: to, opacity: io3(seg(p, 0.35, 0.65)) };
      return { warp: 5, warpP: p, warpA: b, warpC: at };
    }
    case 'swirl': {
      const b = bump(p);
      if (isIn) return { warp: 6, warpA: -4.5 * b * b, warpC: to, opacity: io3(seg(p, 0.4, 0.6)) };
      return { warp: 6, warpA: 4.5 * b * b, warpC: at };
    }
    case 'pixelate': {
      const b = bump(p);
      const blk = 1 + 70 * b * b;
      if (isIn) return { warp: 7, warpA: blk, opacity: clamp((p - 0.45) * 10, 0, 1) };
      return { warp: 7, warpA: blk };
    }
    case 'kaleido': {
      const b = bump(p);
      if (isIn) return { warp: 8, warpA: b, warpP: p * 2, warpC: to, opacity: io3(seg(p, 0.4, 0.6)) };
      return { warp: 8, warpA: b, warpP: p * 2, warpC: at };
    }
    case 'heat': {
      // rising heat haze carries the next shot in behind a glowing wall
      const b = bump(p);
      const lk = { leak: 0.55 * b, leakPos: 1.2 - 1.4 * p, leakColor: [1, 0.45, 0.12] as [number, number, number] };
      if (isIn) return { warp: 9, warpP: p, warpA: b, opacity: io3(seg(p, 0.3, 0.7)), ...lk };
      return { warp: 9, warpP: p, warpA: b, ...lk };
    }
    case 'datamosh': {
      const b = bump(p);
      if (isIn) return { visible: p >= 0.5, warp: 10, warpP: p, warpA: b, chroma: 0.012 * b };
      return { visible: p < 0.5, warp: 10, warpP: p, warpA: b, chroma: 0.012 * b };
    }
    case 'tear': {
      // the frame tears open along a jagged diagonal; the torn edge catches the light. With "at" and "to"
      // the tear starts at "at" (a cord, a blade, a crack) and runs toward "to"
      if (spec?.at && spec?.to) {
        let dx = spec.to.x - spec.at.x, dy = spec.to.y - spec.at.y;
        const len = Math.hypot(dx, dy) || 1;
        dx /= len; dy /= len;
        // the jagged front sweeps the whole frame in that direction, from the corner behind "at"
        const xs = [[0, 0], [1, 0], [0, 1], [1, 1]].map(([cx, cy]) => (cx - 0.5) * dx + (cy - 0.5) * dy + 0.5);
        const p0 = Math.min(...xs) - 0.08, p1 = Math.max(...xs) + 0.08;
        return isIn ? { mask: 8, maskX: dx, maskY: dy, maskP: p0 + (p1 - p0) * io3(p), edge: [0.94, 0.92, 0.88], edgeW: 0.014 } : { dy: 0.015 * bump(p) };
      }
      return isIn ? { mask: 8, maskX: 0.38, maskY: 0.92, maskP: -0.08 + 1.16 * io3(p), edge: [0.94, 0.92, 0.88], edgeW: 0.014 } : { dy: 0.015 * bump(p) };
    }
    case 'shutter': {
      // a six-blade aperture closes on the anchor of the first shot and opens from the anchor of the next
      if (isIn) { const q = io3(seg(p, 0.5, 1)); return { visible: p >= 0.5, mask: 9, maskP: 0.02 + 1.1 * q, iris: to, scale: 1.12 - 0.12 * q }; }
      const q = io3(seg(p, 0, 0.5));
      return { visible: p < 0.5, mask: 9, maskP: 1.12 - 1.1 * q, iris: at, scale: 1 + 0.1 * q };
    }
    case 'wiper': {
      // a windscreen wiper sweeps across and leaves the next shot behind it
      return isIn ? { mask: 10, maskP: io3(p), edge: [0.02, 0.02, 0.025], edgeW: 0.035 } : {};
    }
    case 'dive': {
      // the camera dives into the anchor (an eye, a pupil, a light) until it swallows the frame,
      // then the next shot opens out of its own anchor through an aperture
      const A = anchor;
      if (isIn) {
        const q = seg(p, 0.5, 1), s = 1 + 3.2 * (1 - out3(q));
        return { visible: p >= 0.5, scale: s, dx: (A[0] - 0.5) * (1 - s), dy: (A[1] - 0.5) * (1 - s), radial: 0.8 * (1 - q), radC: A, mask: 9, maskP: 0.02 + 1.3 * out3(q), iris: A, flash: 0.8 * (1 - seg(q, 0, 0.35)), flashColor: [0, 0, 0] };
      }
      const q = seg(p, 0, 0.5), s = 1 + 7 * in3(q);
      return { visible: p < 0.5, scale: s, dx: (A[0] - 0.5) * (1 - s), dy: (A[1] - 0.5) * (1 - s), radial: 0.9 * q, radC: A, flash: 0.9 * seg(q, 0.55, 1), flashColor: [0, 0, 0] };
    }
    case 'sweep': {
      // a streetlight band sweeps across; the shots cross under the light
      const pos = -0.3 + 1.6 * io3(p);
      const lk = { leak: 0.95 * bump(p), leakPos: pos, leakColor: [1.0, 0.86, 0.62] as [number, number, number] };
      return isIn ? { opacity: io3(seg(p, 0.35, 0.65)), ...lk } : lk;
    }
    case 'wash': {
      // the drop hit: exposure pushes toward white and recovers fast so the face reads again
      if (isIn) { const k = Math.exp(-seg(p, 0.5, 1) * 5); return { visible: p >= 0.5, expo: 0.8 * k, flash: 0.5 * k, flashColor: [1, 0.98, 0.95] }; }
      const k = seg(p, 0, 0.5) ** 2;
      return { visible: p < 0.5, expo: 0.8 * k, flash: 0.5 * k, flashColor: [1, 0.98, 0.95] };
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
  cube_left: 'Cube turn left', cube_right: 'Cube turn right', cube_up: 'Cube turn up', cube_down: 'Cube turn down', flip_h: 'Card flip', flip_v: 'Card flip vertical',
  shatter: 'Glass shatter', slices: 'Slices', blinds: 'Venetian blinds', ripple: 'Ripple', swirl: 'Swirl', pixelate: 'Pixelate', kaleido: 'Kaleidoscope',
  heat: 'Heat haze', datamosh: 'Datamosh', tear: 'Tear', shutter: 'Camera aperture', wiper: 'Wiper', dive: 'Dive into the eye', light_sweep: 'Streetlight sweep', wash: 'Exposure wash',
};

/** Groups for the transitions panel. */
export const TRANSITION_GROUPS: { name: string; items: TransitionType[] }[] = [
  { name: 'Signature', items: ['logo', 'dive', 'shatter', 'bolt', 'blink', 'ink', 'burn', 'slash', 'tear', 'punch', 'shadow', 'warp', 'roll', 'shutter', 'wash', 'light_leak', 'light_sweep', 'heat'] },
  { name: '3D and physical', items: ['cube_left', 'cube_right', 'cube_up', 'cube_down', 'flip_h', 'flip_v', 'slices', 'blinds', 'wiper'] },
  { name: 'Distort', items: ['ripple', 'swirl', 'kaleido', 'pixelate', 'datamosh'] },
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
  if (t === 'dive') return 0.8;
  if (t === 'shatter' || t === 'ripple' || t === 'heat') return 0.7;
  if (t.startsWith('cube') || t === 'slices' || t === 'blinds' || t === 'swirl' || t === 'kaleido' || t === 'light_sweep') return 0.6;
  if (t === 'pixelate' || t === 'wash') return 0.4;
  if (t === 'datamosh') return 0.35;
  return 0.5;
}

/** Transitions that count as a flash for the flash-rate rule. */
export const FLASHY = new Set<TransitionType>(['flash', 'dip_white', 'punch', 'glitch', 'warp', 'bolt', 'wash']);

/** Library moves that read as template filler when they carry an edit (the house rule: at most a quarter of the joins). */
export const GENERIC = new Set<TransitionType>(['crossfade', 'dip_black', 'dip_white', 'flash', 'slide_left', 'slide_right', 'slide_up', 'slide_down', 'push_left', 'push_right', 'push_up', 'push_down', 'wipe_left', 'wipe_right', 'wipe_up', 'wipe_down', 'iris', 'zoom_in', 'zoom_out', 'spin', 'blur', 'glitch', 'ripple', 'swirl', 'pixelate', 'kaleido', 'datamosh']);
