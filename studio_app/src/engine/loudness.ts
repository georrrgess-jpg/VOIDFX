// Loudness to the house standard: ITU-R BS.1770 integrated loudness (K-weighted, gated), a 4x
// true-peak estimate, and a look-ahead limiter. Runs on the final 48 kHz stereo mix before encoding.

function kWeight(x: Float32Array): Float32Array {
  // BS.1770 K-weighting at 48 kHz: high shelf, then high-pass
  const y = new Float32Array(x.length);
  const b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], a1 = [-1.69065929318241, 0.73248077421585];
  const b2 = [1.0, -2.0, 1.0], a2 = [-1.99004745483398, 0.99007225036621];
  let x1 = 0, x2 = 0, y1 = 0, y2 = 0, z1 = 0, z2 = 0, w1 = 0, w2 = 0;
  for (let i = 0; i < x.length; i++) {
    const xi = x[i];
    const s = b1[0] * xi + b1[1] * x1 + b1[2] * x2 - a1[0] * y1 - a1[1] * y2;
    x2 = x1; x1 = xi; y2 = y1; y1 = s;
    const o = b2[0] * s + b2[1] * z1 + b2[2] * z2 - a2[0] * w1 - a2[1] * w2;
    z2 = z1; z1 = s; w2 = w1; w1 = o;
    y[i] = o;
  }
  return y;
}

/** Integrated loudness in LUFS (gated). */
export function integratedLufs(L: Float32Array, R: Float32Array, sr = 48000): number {
  const kl = kWeight(L), kr = kWeight(R);
  const block = Math.round(0.4 * sr), hop = Math.round(0.1 * sr);
  const powers: number[] = [];
  for (let s = 0; s + block <= kl.length; s += hop) {
    let a = 0, b = 0;
    for (let i = s; i < s + block; i++) { a += kl[i] * kl[i]; b += kr[i] * kr[i]; }
    powers.push((a + b) / block);
  }
  if (!powers.length) return -70;
  const lufs = (p: number) => -0.691 + 10 * Math.log10(p + 1e-12);
  const abs = powers.filter(p => lufs(p) > -70);
  if (!abs.length) return -70;
  const rel = lufs(abs.reduce((x, y) => x + y, 0) / abs.length) - 10;
  const gated = abs.filter(p => lufs(p) > rel);
  return lufs(gated.reduce((x, y) => x + y, 0) / Math.max(1, gated.length));
}

/** Peak magnitude per sample including 4x inter-sample estimates (Catmull-Rom). */
function truePeakTrack(x: Float32Array): Float32Array {
  const n = x.length;
  const out = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    const p0 = x[i - 1] ?? x[i], p1 = x[i], p2 = x[i + 1] ?? x[i], p3 = x[i + 2] ?? p2;
    let m = Math.abs(p1);
    for (const t of [0.25, 0.5, 0.75]) {
      const t2 = t * t, t3 = t2 * t;
      const v = 0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3);
      const a = Math.abs(v);
      if (a > m) m = a;
    }
    out[i] = m;
  }
  return out;
}

export function truePeakDb(L: Float32Array, R: Float32Array): number {
  let m = 0;
  for (const x of [L, R]) { const t = truePeakTrack(x); for (let i = 0; i < t.length; i++) if (t[i] > m) m = t[i]; }
  return 20 * Math.log10(m + 1e-12);
}

/** Look-ahead limiter: gain never lets the true peak pass `ceiling` (linear). */
function limit(L: Float32Array, R: Float32Array, ceiling: number, sr = 48000) {
  const n = L.length;
  const tl = truePeakTrack(L), tr = truePeakTrack(R);
  const need = new Float32Array(n);
  for (let i = 0; i < n; i++) { const pk = Math.max(tl[i], tr[i]); need[i] = pk > ceiling ? ceiling / pk : 1; }
  const look = Math.max(1, Math.round(0.002 * sr));
  // minimum over the look-ahead window (monotonic deque), so gain is down before the peak arrives
  const minf = new Float32Array(n);
  const dq: number[] = [];
  let head = 0;
  for (let i = n - 1; i >= 0; i--) {
    while (dq.length > head && need[dq[dq.length - 1]] >= need[i]) dq.pop();
    dq.push(i);
    while (dq[head] > i + 2 * look) head++;
    minf[i] = need[dq[head]];
  }
  // attack: moving average of the window minimum over the last `look` samples. Every value averaged
  // looks ahead past the current sample, so the result never exceeds what this sample needs.
  const rel = 1 - Math.exp(-1 / (0.08 * sr));
  let acc = 0;
  let g = 1;
  for (let i = 0; i < n; i++) {
    acc += minf[i] - (i >= look ? minf[i - look] : 0);
    const t = i >= look ? Math.min(acc / look, 1) : minf[i];
    g = t < g ? t : g + (t - g) * rel;
    L[i] *= g;
    R[i] *= g;
  }
}

export interface MasterStats { inputLufs: number; gainDb: number; lufs: number; truePeakDb: number }

/** Normalise to `targetLufs` and limit the true peak to `ceilingDb`. Works in place. */
export function masterMix(L: Float32Array, R: Float32Array, targetLufs: number, ceilingDb: number): MasterStats {
  const inputLufs = integratedLufs(L, R);
  if (inputLufs <= -69) return { inputLufs, gainDb: 0, lufs: inputLufs, truePeakDb: truePeakDb(L, R) };
  const ceiling = 10 ** (ceilingDb / 20);
  let total = 0;
  let lufs = inputLufs;
  // the limiter takes some loudness back, so gain and limit until the target is reached
  for (let pass = 0; pass < 4; pass++) {
    const g = Math.max(-30, Math.min(24 - total, targetLufs - lufs));
    if (Math.abs(g) < 0.1 && pass > 0) break;
    const k = 10 ** (g / 20);
    for (let i = 0; i < L.length; i++) { L[i] *= k; R[i] *= k; }
    total += g;
    limit(L, R, ceiling);
    lufs = integratedLufs(L, R);
  }
  return { inputLufs, gainDb: total, lufs, truePeakDb: truePeakDb(L, R) };
}
