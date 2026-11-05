import { TransitionType } from '../state/types';
import { clamp } from '../state/util';

/** Per-layer effect parameters a transition sets on the outgoing ('out') and incoming ('in') clip. */
export interface LayerFx {
  visible: boolean;
  dx: number; dy: number; // frame fractions
  scale: number;
  rot: number; // degrees
  opacity: number;
  blur: number; // 0..1 (fraction of frame height * 0.04)
  dirX: number; dirY: number; // directional blur, frame fractions
  mask: 0 | 1 | 2; // none, linear, radial
  maskX: number; maskY: number; // direction for linear mask
  maskP: number;
  chroma: number; // RGB split, frame fraction
  flash: number;
  flashColor: [number, number, number];
}

export const NO_FX: LayerFx = {
  visible: true, dx: 0, dy: 0, scale: 1, rot: 0, opacity: 1, blur: 0, dirX: 0, dirY: 0,
  mask: 0, maskX: 1, maskY: 0, maskP: 1, chroma: 0, flash: 0, flashColor: [0, 0, 0],
};

const io3 = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2);
const io5 = (t: number) => (t < 0.5 ? 16 * t ** 5 : 1 - (-2 * t + 2) ** 5 / 2);
const bump = (p: number) => Math.sin(Math.PI * clamp(p, 0, 1)); // 0 → 1 → 0
const DIRS: Record<string, [number, number]> = { left: [-1, 0], right: [1, 0], up: [0, -1], down: [0, 1] };

/** Effects for one side of a transition at progress p (0..1). */
export function transitionFx(type: TransitionType, p: number, role: 'out' | 'in'): Partial<LayerFx> {
  p = clamp(p, 0, 1);
  const e = io3(p);
  const isIn = role === 'in';
  const [kind, dirName] = type.split('_') as [string, string | undefined];
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
      const w: [number, number, number] = [1, 1, 1];
      return isIn
        ? { visible: p >= 0.5, flash: clamp((1 - p) * 2, 0, 1) ** 2, flashColor: w, scale: 1 + 0.06 * (1 - io3(clamp((p - 0.5) * 2, 0, 1))) }
        : { visible: p < 0.5, flash: clamp(p * 2, 0, 1) ** 2, flashColor: w };
    }
    case 'slide':
      // incoming clip slides over the outgoing one, entering from the side opposite to `dir`
      return isIn ? { dx: -dir[0] * (1 - e), dy: -dir[1] * (1 - e) } : { flash: 0.25 * e, flashColor: [0, 0, 0] };
    case 'push':
      return isIn ? { dx: -dir[0] * (1 - e), dy: -dir[1] * (1 - e) } : { dx: dir[0] * e, dy: dir[1] * e };
    case 'wipe':
      return isIn ? { mask: 1, maskX: dir[0], maskY: dir[1], maskP: e } : {};
    case 'iris':
      return isIn ? { mask: 2, maskP: e } : {};
    case 'zoom': {
      const inward = dirName !== 'out';
      const q = io5(p);
      const b = bump(p);
      if (isIn) {
        return { visible: p >= 0.5, scale: inward ? 1 + 0.6 * (1 - q) : 1 - 0.35 * (1 - q), blur: 0.9 * b * (p < 0.75 ? 1 : (1 - p) * 4), opacity: clamp((p - 0.45) * 10, 0, 1) };
      }
      return { visible: p < 0.55, scale: inward ? 1 + 0.9 * q : 1 - 0.45 * q, blur: 0.9 * b };
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
    default:
      return isIn ? { opacity: e } : {};
  }
}

export const TRANSITION_LABELS: Record<TransitionType, string> = {
  crossfade: 'Crossfade', dip_black: 'Dip to black', dip_white: 'Dip to white', flash: 'Flash',
  slide_left: 'Slide left', slide_right: 'Slide right', slide_up: 'Slide up', slide_down: 'Slide down',
  push_left: 'Push left', push_right: 'Push right', push_up: 'Push up', push_down: 'Push down',
  wipe_left: 'Wipe left', wipe_right: 'Wipe right', wipe_up: 'Wipe up', wipe_down: 'Wipe down',
  iris: 'Iris', zoom_in: 'Zoom in', zoom_out: 'Zoom out',
  whip_left: 'Whip left', whip_right: 'Whip right', whip_up: 'Whip up', whip_down: 'Whip down',
  spin: 'Spin', blur: 'Blur', glitch: 'Glitch',
};
