// Offline audio mix for export: decodes only the source ranges each clip uses, applies speed (with
// pitch kept by a WSOLA time-stretch), volume keyframes, fades and transition crossfades.
import { AudioBufferSink } from 'mediabunny';
import { runtime } from '../media/library';
import { Clip, MediaInfo, Project } from '../state/types';
import { clamp, clipEnd, hasRamp, srcAt, volumeAt } from '../state/util';
import { SFX_RATE, sfxData } from './sfx';
import { trackWindows } from './evaluate';

export const MIX_RATE = 48000;

function hermite(d: Float32Array, x: number): number {
  const i = Math.floor(x);
  const f = x - i;
  const xm1 = d[i - 1] ?? d[i] ?? 0, x0 = d[i] ?? 0, x1 = d[i + 1] ?? x0, x2 = d[i + 2] ?? x1;
  const c = (x1 - xm1) * 0.5;
  const v = x0 - x1;
  const w = c + v;
  const a = w + v + (x2 - x0) * 0.5;
  const b = w + a;
  return ((a * f - b) * f + c) * f + x0;
}

/** WSOLA time-stretch: changes duration by 1/speed while keeping pitch. */
export function timeStretch(chans: Float32Array[], speed: number, sr: number): Float32Array[] {
  const inLen = chans[0].length;
  const outLen = Math.max(1, Math.floor(inLen / speed));
  const win = Math.max(256, Math.round(sr * 0.046) & ~1);
  const hop = win / 2;
  const tol = Math.round(sr * 0.012);
  const w = new Float32Array(win);
  for (let i = 0; i < win; i++) w[i] = 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / win);
  const out = chans.map(() => new Float32Array(outLen + win));
  const norm = new Float32Array(outLen + win);
  const mono = chans.length === 1 ? chans[0] : (() => {
    const m = new Float32Array(inLen);
    for (const c of chans) for (let i = 0; i < inLen; i++) m[i] += c[i] / chans.length;
    return m;
  })();
  let prev = -1;
  for (let op = 0; op < outLen; op += hop) {
    const nominal = Math.round(op * speed);
    let start = nominal;
    if (prev >= 0) {
      // best match to the natural continuation of the previous segment
      const nat = prev + hop;
      let best = -Infinity;
      const lo = Math.max(0, nominal - tol), hi = Math.min(inLen - win, nominal + tol);
      for (let s = lo; s <= hi; s += 2) {
        let acc = 0;
        for (let k = 0; k < win; k += 8) acc += mono[s + k] * (mono[nat + k] ?? 0);
        if (acc > best) { best = acc; start = s; }
      }
    }
    start = clamp(start, 0, Math.max(0, inLen - win));
    for (let ch = 0; ch < chans.length; ch++) {
      const src = chans[ch], dst = out[ch];
      for (let k = 0; k < win && op + k < dst.length; k++) dst[op + k] += (src[start + k] ?? 0) * w[k];
    }
    for (let k = 0; k < win && op + k < norm.length; k++) norm[op + k] += w[k];
    prev = start;
  }
  return out.map(d => {
    const r = new Float32Array(outLen);
    for (let i = 0; i < outLen; i++) r[i] = norm[i] > 1e-3 ? d[i] / norm[i] : d[i];
    return r;
  });
}

async function decodeRange(mediaId: string, a: number, b: number, signal?: AbortSignal): Promise<{ chans: Float32Array[]; sr: number; t0: number } | null> {
  const rt = runtime.get(mediaId);
  if (!rt) return null;
  if (rt.audio && rt.canDecodeAudio) {
    const sink = new AudioBufferSink(rt.audio);
    const parts: AudioBuffer[] = [];
    let t0 = -1;
    for await (const { buffer, timestamp } of sink.buffers(Math.max(0, a), b)) {
      if (signal?.aborted) throw new DOMException('Export cancelled', 'AbortError');
      if (t0 < 0) t0 = timestamp;
      parts.push(buffer);
    }
    if (!parts.length) return null;
    const sr = parts[0].sampleRate;
    const len = parts.reduce((n, p) => n + p.length, 0);
    const nCh = Math.min(2, Math.max(...parts.map(p => p.numberOfChannels)));
    const chans = Array.from({ length: nCh }, () => new Float32Array(len));
    let off = 0;
    for (const p of parts) {
      for (let ch = 0; ch < nCh; ch++) chans[ch].set(p.getChannelData(Math.min(ch, p.numberOfChannels - 1)), off);
      off += p.length;
    }
    return { chans, sr, t0 };
  }
  if (rt.file.size < 400 * 1024 * 1024) {
    const AC = window.OfflineAudioContext || (window as any).webkitOfflineAudioContext;
    const ctx = new AC(2, 1, MIX_RATE);
    const buf = await ctx.decodeAudioData(await rt.file.arrayBuffer());
    const s = Math.floor(Math.max(0, a) * buf.sampleRate), e = Math.min(buf.length, Math.ceil(b * buf.sampleRate));
    const chans = Array.from({ length: Math.min(2, buf.numberOfChannels) }, (_, ch) => buf.getChannelData(ch).slice(s, e));
    return { chans, sr: buf.sampleRate, t0: s / buf.sampleRate };
  }
  return null;
}

function fade(c: Clip, lt: number) {
  let g = 1;
  if (c.fadeIn && lt < c.fadeIn) g *= clamp(lt / c.fadeIn, 0, 1);
  if (c.fadeOut && lt > c.dur - c.fadeOut) g *= clamp((c.dur - lt) / c.fadeOut, 0, 1);
  return g;
}

/** Mix every audible clip into a stereo buffer `total` seconds long. Returns null when there is no sound. */
export async function mixAudio(
  p: Project, media: Record<string, MediaInfo>, total: number,
  onProgress: (f: number) => void, signal?: AbortSignal, warn?: (msg: string) => void,
): Promise<[Float32Array, Float32Array] | null> {
  const N = Math.ceil(total * MIX_RATE);
  const L = new Float32Array(N), R = new Float32Array(N);
  type Job = { clip: Clip; from: number; to: number; tin?: { dur: number }; tout?: { dur: number } };
  const jobs: Job[] = [];
  for (const tr of p.tracks) {
    if (tr.muted || tr.kind === 'text') continue;
    for (const w of trackWindows(p, tr.id)) {
      const c = w.clip;
      if (c.muted || !(c.kind === 'video' || c.kind === 'audio')) continue;
      const m = c.media ? media[c.media] : undefined;
      if (!m?.hasAudio) continue;
      if ((c.volume ?? 1) <= 0 && !c.kf?.volume?.length) continue;
      jobs.push({ clip: c, from: w.from, to: w.to, tin: w.tin, tout: w.tout });
    }
  }
  // generated sound effects
  let sfxCount = 0;
  for (const tr of p.tracks) {
    if (tr.muted || tr.kind !== 'audio') continue;
    for (const c of p.clips) {
      if (c.track !== tr.id || c.kind !== 'sfx' || !c.sfx || c.muted) continue;
      const d = sfxData(c.sfx);
      const off = c.in ?? 0;
      const i0 = Math.max(0, Math.floor(c.start * MIX_RATE)), i1 = Math.min(N, Math.ceil((c.start + c.dur) * MIX_RATE));
      for (let k = i0; k < i1; k++) {
        const lt = k / MIX_RATE - c.start;
        const x = (off + lt) * SFX_RATE;
        const j = Math.floor(x);
        if (j < 0 || j >= d.L.length - 1) continue;
        const g = volumeAt(c, clamp(lt, 0, c.dur)) * fade(c, lt);
        const f = x - j;
        L[k] += (d.L[j] + (d.L[j + 1] - d.L[j]) * f) * g;
        R[k] += (d.R[j] + (d.R[j + 1] - d.R[j]) * f) * g;
      }
      sfxCount++;
    }
  }
  if (!jobs.length && !sfxCount) return null;
  let done = 0;
  for (const j of jobs) {
    if (signal?.aborted) throw new DOMException('Export cancelled', 'AbortError');
    const c = j.clip;
    const m = media[c.media!];
    const ramp = hasRamp(c);
    const speed = c.speed ?? 1;
    const srcAtT = (t: number) => srcAt(c, t - c.start);
    const a = clamp(srcAtT(j.from), 0, m.duration), b = clamp(srcAtT(j.to), 0, m.duration);
    if (b - a <= 0.001) { done++; continue; }
    const dec = await decodeRange(m.id, a - 0.05, b + 0.05, signal);
    if (!dec) { warn?.(`Sound of ${m.name} could not be decoded and was left out.`); done++; continue; }
    let chans = dec.chans;
    // constant speed keeps pitch (WSOLA); speed ramps resample like a tape (pitch follows speed)
    const stretch = !ramp && speed !== 1 && c.keepPitch !== false;
    if (stretch) chans = timeStretch(chans, speed, dec.sr);
    const cL = chans[0], cR = chans[1] || chans[0];
    const i0 = Math.max(0, Math.floor(j.from * MIX_RATE)), i1 = Math.min(N, Math.ceil(j.to * MIX_RATE));
    const BLOCK = 64;
    for (let i = i0; i < i1; i += BLOCK) {
      const t = i / MIX_RATE;
      const lt = t - c.start;
      let g = volumeAt(c, clamp(lt, 0, c.dur)) * fade(c, lt);
      if (j.tin && t < c.start + j.tin.dur / 2) g *= Math.sin(clamp((t - (c.start - j.tin.dur / 2)) / j.tin.dur, 0, 1) * Math.PI / 2);
      else if (j.tout && t >= clipEnd(c) - j.tout.dur / 2) g *= Math.cos(clamp((t - (clipEnd(c) - j.tout.dur / 2)) / j.tout.dur, 0, 1) * Math.PI / 2);
      if (g <= 1e-5) continue;
      const end = Math.min(i1, i + BLOCK);
      const sA = srcAtT(i / MIX_RATE), sB = srcAtT(end / MIX_RATE);
      for (let k = i; k < end; k++) {
        const st = sA + (sB - sA) * ((k - i) / Math.max(1, end - i));
        if (st < 0 || st > m.duration) continue;
        const x = stretch ? ((st - dec.t0) / speed) * dec.sr : (st - dec.t0) * dec.sr;
        if (x < 0 || x >= cL.length - 1) continue;
        L[k] += hermite(cL, x) * g;
        R[k] += hermite(cR, x) * g;
      }
    }
    done++;
    onProgress(done / jobs.length);
    await new Promise(r => setTimeout(r, 0));
  }
  return [L, R];
}
