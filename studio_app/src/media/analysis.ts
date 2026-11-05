// Streaming audio analysis: waveform peaks, tempo, beat grid, downbeats, strongest hits, loudness
// envelope, sharp rises and quiet stretches. Fed one decoded buffer at a time, so a long file never
// has to be held in memory.
import { AudioAnalysis } from '../state/types';

export const PEAK_RATE = 100; // waveform bins per second

export class AudioAnalyzer {
  private sr: number;
  private hop: number;
  private n: number; // FFT size
  private win: Float32Array;
  private ring: Float32Array; // last n samples
  private ringFill = 0;
  private pendingHop = 0;
  private prevMag: Float32Array;
  private re: Float32Array;
  private im: Float32Array;
  private rmsAcc = 0;
  private rmsCount = 0;
  private peakAcc = 0;
  private peakCount = 0;
  private peakSize: number;
  flux: number[] = [];
  rms: number[] = [];
  peaks: number[] = [];
  private totalSq = 0;
  private totalN = 0;

  constructor(sampleRate: number) {
    this.sr = sampleRate;
    this.hop = Math.max(128, Math.round(sampleRate / 86.13));
    let n = 512;
    while (n < this.hop * 2) n *= 2;
    this.n = n;
    this.win = new Float32Array(n);
    for (let i = 0; i < n; i++) this.win[i] = 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / (n - 1));
    this.ring = new Float32Array(n);
    this.prevMag = new Float32Array(n / 2);
    this.re = new Float32Array(n);
    this.im = new Float32Array(n);
    this.peakSize = Math.max(1, Math.round(sampleRate / PEAK_RATE));
  }

  get frameRate() { return this.sr / this.hop; }

  /** Feed mono samples (any block size). */
  pushBlock(mono: Float32Array) {
    const n = this.n;
    let i = 0;
    while (i < mono.length) {
      const take = Math.min(this.hop - this.pendingHop, mono.length - i);
      // peaks + rms over the chunk
      for (let k = 0; k < take; k++) {
        const s = mono[i + k];
        const a = s < 0 ? -s : s;
        if (a > this.peakAcc) this.peakAcc = a;
        if (++this.peakCount >= this.peakSize) { this.peaks.push(this.peakAcc); this.peakAcc = 0; this.peakCount = 0; }
        this.rmsAcc += s * s;
        this.totalSq += s * s;
      }
      this.rmsCount += take;
      this.totalN += take;
      // shift ring left by `take` and append
      this.ring.copyWithin(0, take);
      this.ring.set(mono.subarray(i, i + take), n - take);
      this.ringFill = Math.min(n, this.ringFill + take);
      this.pendingHop += take;
      i += take;
      if (this.pendingHop >= this.hop) {
        this.pendingHop = 0;
        this.frame();
      }
    }
  }

  private frame() {
    const n = this.n;
    const re = this.re, im = this.im;
    for (let i = 0; i < n; i++) { re[i] = this.ring[i] * this.win[i]; im[i] = 0; }
    fft(re, im);
    let flux = 0;
    const half = n / 2;
    for (let k = 1; k < half; k++) {
      const mag = Math.log1p(100 * Math.sqrt(re[k] * re[k] + im[k] * im[k]));
      const d = mag - this.prevMag[k];
      if (d > 0) flux += d;
      this.prevMag[k] = mag;
    }
    this.flux.push(flux);
    this.rms.push(Math.sqrt(this.rmsAcc / Math.max(1, this.rmsCount)));
    this.rmsAcc = 0;
    this.rmsCount = 0;
  }

  finish(): { analysis: AudioAnalysis; peaks: Float32Array } {
    if (this.peakCount) this.peaks.push(this.peakAcc);
    const peaks = Float32Array.from(this.peaks);
    return { analysis: analyze(this.flux, this.rms, this.frameRate, this.totalSq / Math.max(1, this.totalN)), peaks };
  }
}

function fft(re: Float32Array, im: Float32Array) {
  const n = re.length;
  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) { let t = re[i]; re[i] = re[j]; re[j] = t; t = im[i]; im[i] = im[j]; im[j] = t; }
  }
  for (let len = 2; len <= n; len <<= 1) {
    const ang = (-2 * Math.PI) / len;
    const wr = Math.cos(ang), wi = Math.sin(ang);
    for (let i = 0; i < n; i += len) {
      let cr = 1, ci = 0;
      for (let k = 0; k < len / 2; k++) {
        const a = i + k, b = a + len / 2;
        const xr = re[b] * cr - im[b] * ci;
        const xi = re[b] * ci + im[b] * cr;
        re[b] = re[a] - xr; im[b] = im[a] - xi;
        re[a] += xr; im[a] += xi;
        const ncr = cr * wr - ci * wi;
        ci = cr * wi + ci * wr;
        cr = ncr;
      }
    }
  }
}

const r3 = (v: number) => Math.round(v * 1000) / 1000;

function movingAvg(x: Float32Array, radius: number): Float32Array {
  const out = new Float32Array(x.length);
  let acc = 0;
  const pre = new Float64Array(x.length + 1);
  for (let i = 0; i < x.length; i++) { acc += x[i]; pre[i + 1] = acc; }
  for (let i = 0; i < x.length; i++) {
    const a = Math.max(0, i - radius), b = Math.min(x.length, i + radius + 1);
    out[i] = (pre[b] - pre[a]) / (b - a);
  }
  return out;
}

export function analyze(fluxArr: number[], rmsArr: number[], fr: number, meanSq: number): AudioAnalysis {
  const N = fluxArr.length;
  const empty: AudioAnalysis = { bpm: null, pulse: 0, beats: [], downbeats: [], hits: [], energy: [], energyRate: 4, rises: [], quiet: [], rmsDb: -120 };
  if (N < fr * 1.5) return empty;
  const flux = Float32Array.from(fluxArr);
  const rms = Float32Array.from(rmsArr);
  // onset envelope: flux minus local mean, rectified, normalised
  const local = movingAvg(flux, Math.round(fr * 0.25));
  const env = new Float32Array(N);
  let mean = 0;
  for (let i = 0; i < N; i++) { env[i] = Math.max(0, flux[i] - local[i]); mean += env[i]; }
  mean /= N;
  let sd = 0;
  for (let i = 0; i < N; i++) sd += (env[i] - mean) ** 2;
  sd = Math.sqrt(sd / N) || 1;
  for (let i = 0; i < N; i++) env[i] = env[i] / sd;

  // ---- tempo by autocorrelation with a soft prior around 120 BPM ----
  const minLag = Math.floor((60 * fr) / 200), maxLag = Math.ceil((60 * fr) / 60);
  const span = Math.min(N, Math.round(fr * 240)); // up to 4 minutes from the loudest region
  let startAt = 0;
  if (N > span) {
    let best = -1;
    const step = Math.round(fr * 5);
    for (let s = 0; s + span <= N; s += step) {
      let e = 0;
      for (let i = s; i < s + span; i += 8) e += rms[i];
      if (e > best) { best = e; startAt = s; }
    }
  }
  const seg = env.subarray(startAt, startAt + span);
  const segMean = seg.reduce((a, b) => a + b, 0) / seg.length;
  const ac = new Float32Array(maxLag + 2);
  let ac0 = 0;
  for (let i = 0; i < seg.length; i++) ac0 += (seg[i] - segMean) ** 2;
  for (let lag = minLag; lag <= maxLag + 1 && lag < seg.length; lag++) {
    let s = 0;
    for (let i = 0; i + lag < seg.length; i++) s += (seg[i] - segMean) * (seg[i + lag] - segMean);
    ac[lag] = s / (seg.length - lag);
  }
  let bestLag = 0, bestScore = -Infinity;
  for (let lag = minLag; lag <= maxLag; lag++) {
    const bpm = (60 * fr) / lag;
    const prior = Math.exp(-0.5 * (Math.log2(bpm / 120) / 0.9) ** 2);
    // reward lags whose double also correlates (metrical consistency)
    const dbl = lag * 2 <= maxLag + 1 ? ac[lag * 2] : 0;
    const score = (ac[lag] + 0.5 * dbl) * prior;
    if (score > bestScore) { bestScore = score; bestLag = lag; }
  }
  let lagF = bestLag;
  if (bestLag > minLag && bestLag < maxLag) {
    const a = ac[bestLag - 1], b = ac[bestLag], c = ac[bestLag + 1];
    const den = a - 2 * b + c;
    if (den < 0) lagF = bestLag + (0.5 * (a - c)) / den;
  }
  const pulse = ac0 > 0 ? Math.max(0, Math.min(1, (ac[bestLag] / (ac0 / seg.length)) * 1.5)) : 0;
  let bpm: number | null = (60 * fr) / lagF;
  const steady = pulse > 0.08;

  // ---- beat tracking (dynamic programming) ----
  let beats: number[] = [];
  let downbeats: number[] = [];
  if (steady && bpm) {
    const P = lagF;
    const score = new Float32Array(N);
    const back = new Int32Array(N).fill(-1);
    const tight = 100;
    for (let i = 0; i < N; i++) {
      let best = 0, bi = -1;
      const lo = Math.max(0, Math.round(i - 2 * P)), hi = Math.round(i - P / 2);
      for (let j = lo; j <= hi && j < i; j++) {
        const pen = -tight * Math.log((i - j) / P) ** 2;
        const v = score[j] + pen;
        if (v > best || bi < 0) { best = v; bi = j; }
      }
      score[i] = env[i] + (bi >= 0 ? Math.max(0, best) : 0);
      back[i] = bi;
    }
    let end = N - 1, bestEnd = -Infinity;
    for (let i = Math.max(0, Math.round(N - P)); i < N; i++) if (score[i] > bestEnd) { bestEnd = score[i]; end = i; }
    const idx: number[] = [];
    for (let i = end; i >= 0; i = back[i]) { idx.push(i); if (back[i] < 0) break; }
    idx.reverse();
    const lat = 0.5 / fr;
    beats = idx.map(i => r3(i / fr + lat)).filter(t => t >= 0);
    // downbeats: the phase (of 4) whose beats carry the most onset energy
    let bestPh = 0, bestE = -1;
    for (let ph = 0; ph < 4; ph++) {
      let e = 0;
      for (let k = ph; k < idx.length; k += 4) e += env[idx[k]] + 0.5 * rms[idx[k]] / (Math.sqrt(meanSq) || 1);
      if (e > bestE) { bestE = e; bestPh = ph; }
    }
    downbeats = beats.filter((_, k) => k % 4 === bestPh);
    bpm = Math.round(bpm * 10) / 10;
  } else {
    bpm = null;
  }

  // ---- strongest hits ----
  const rad = Math.round(fr * 0.1);
  const cand: [number, number][] = [];
  for (let i = 1; i < N - 1; i++) {
    const v = env[i];
    if (v < 2) continue;
    let isMax = true;
    for (let j = Math.max(0, i - rad); j <= Math.min(N - 1, i + rad); j++) if (env[j] > v) { isMax = false; break; }
    if (isMax) cand.push([i, v]);
  }
  cand.sort((a, b) => b[1] - a[1]);
  const hits = cand.slice(0, 48).map(([i]) => r3(i / fr));

  // ---- loudness envelope (4 Hz), rises, quiet parts ----
  const eRate = 4;
  const per = Math.max(1, Math.round(fr / eRate));
  const db: number[] = [];
  for (let i = 0; i < N; i += per) {
    let s = 0, c = 0;
    for (let j = i; j < Math.min(N, i + per); j++) { s += rms[j] * rms[j]; c++; }
    db.push(10 * Math.log10(s / Math.max(1, c) + 1e-12));
  }
  const sorted = [...db].sort((a, b) => a - b);
  const lo = sorted[Math.floor(sorted.length * 0.05)] ?? -60;
  const hi = sorted[sorted.length - 1] ?? 0;
  const energy = db.map(v => r3(Math.max(0, Math.min(1, (v - lo) / Math.max(6, hi - lo)))));
  const sm = movingAvg(Float32Array.from(energy), 2);
  const rises: [number, number][] = [];
  const w = eRate; // compare 1 s before vs 1 s after
  for (let i = w; i < sm.length - w; i++) {
    const d = sm[i + w - 1] - sm[i - w];
    if (d > 0.22) rises.push([i, d]);
  }
  rises.sort((a, b) => b[1] - a[1]);
  const riseTimes: number[] = [];
  for (const [i] of rises) {
    const t = i / eRate;
    if (riseTimes.every(x => Math.abs(x - t) > 2)) riseTimes.push(r3(t));
    if (riseTimes.length >= 8) break;
  }
  riseTimes.sort((a, b) => a - b);
  // quiet: below -45 dBFS or 28 dB under the loud level
  const thr = Math.max(-45, hi - 28);
  const quiet: [number, number][] = [];
  let qs = -1;
  for (let i = 0; i <= N; i++) {
    const v = i < N ? 20 * Math.log10(rms[i] + 1e-9) : 0;
    if (i < N && v < thr) { if (qs < 0) qs = i; }
    else if (qs >= 0) {
      if ((i - qs) / fr >= 0.25) quiet.push([r3(qs / fr), r3(i / fr)]);
      qs = -1;
    }
  }
  return {
    bpm, pulse: r3(pulse), beats, downbeats, hits, energy, energyRate: eRate, rises: riseTimes,
    quiet: quiet.slice(0, 400), rmsDb: Math.round(10 * Math.log10(meanSq + 1e-12) * 10) / 10,
  };
}
