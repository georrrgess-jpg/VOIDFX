// Offline, frame-accurate export (WebCodecs via Mediabunny) and still rendering for Opus reviews.
import {
  AudioBufferSource, BufferTarget, CanvasSource, Mp4OutputFormat, Output, StreamTarget, StreamTargetChunk,
  VideoSample, VideoSampleSink, WebMOutputFormat, canEncodeAudio, canEncodeVideo,
} from 'mediabunny';
import { registerAacEncoder } from '@mediabunny/aac-encoder';
import { runtime } from '../media/library';
import { store } from '../state/store';
import { Clip, MediaInfo, Project } from '../state/types';
import { clamp, deepClone, projectDuration, textStyleOf } from '../state/util';
import { mixAudio, MIX_RATE } from './audiomix';
import { Compositor, fitSize } from './compositor';
import { evaluate, VisualLayer } from './evaluate';
import { player } from './player';
import { dropTextRasters, ensureFont, renderText } from './text';

export interface ExportSettings { width: number; height: number; fps: number; bitrate: number; audioBitrate: number }
export interface ExportResult { blob: Blob; ext: 'mp4' | 'webm'; videoCodec: string; audioCodec: string | null; seconds: number; warnings: string[] }
export type ExportPhase = 'prepare' | 'audio' | 'video' | 'finish';

const abortErr = () => new DOMException('Export cancelled', 'AbortError');

/** Rotation-aware conversion of a decoded sample into a canvas no larger than `maxLong` pixels. */
class SampleCanvas {
  private canvases = new Map<string, OffscreenCanvas | HTMLCanvasElement>();
  get(key: string, sample: VideoSample, maxLong: number) {
    const dw = sample.displayWidth, dh = sample.displayHeight;
    const s = Math.min(1, maxLong / Math.max(dw, dh));
    const w = Math.max(2, Math.round(dw * s)), h = Math.max(2, Math.round(dh * s));
    let c = this.canvases.get(key);
    if (!c) {
      c = typeof OffscreenCanvas !== 'undefined' ? new OffscreenCanvas(w, h) : Object.assign(document.createElement('canvas'), { width: w, height: h });
      this.canvases.set(key, c);
    }
    if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
    const ctx = c.getContext('2d') as CanvasRenderingContext2D;
    sample.draw(ctx, 0, 0, w, h);
    return { canvas: c, w, h };
  }
  drop(key: string) { this.canvases.delete(key); }
}

/** Element-seek fallback for sources WebCodecs cannot decode. */
class ElementFrames {
  private els = new Map<string, HTMLVideoElement>();
  async get(mediaId: string, t: number): Promise<HTMLVideoElement | null> {
    const rt = runtime.get(mediaId);
    if (!rt) return null;
    let v = this.els.get(mediaId);
    if (!v) {
      v = document.createElement('video');
      v.muted = true;
      v.preload = 'auto';
      v.src = rt.url;
      this.els.set(mediaId, v);
      await new Promise<void>(r => { v!.onloadeddata = () => r(); v!.onerror = () => r(); setTimeout(r, 8000); });
    }
    if (Math.abs(v.currentTime - t) > 0.004) {
      await new Promise<void>(r => {
        const done = () => { v!.removeEventListener('seeked', done); r(); };
        v!.addEventListener('seeked', done);
        v!.currentTime = t;
        setTimeout(done, 4000);
      });
    }
    return v.readyState >= 2 ? v : null;
  }
  dispose() {
    for (const v of this.els.values()) { v.removeAttribute('src'); v.load(); }
    this.els.clear();
  }
}

/** Draw one evaluated frame into `comp`. `frameFor` supplies decoded pictures for video layers. */
async function drawOffline(
  comp: Compositor, p: Project, media: Record<string, MediaInfo>, layers: VisualLayer[],
  frameFor: (L: VisualLayer) => Promise<{ src: TexImageSource; w: number; h: number; release?: () => void } | null>,
  slot: string, frameNo: number,
) {
  const W = comp.width, H = comp.height;
  comp.begin(p.background);
  const releases: (() => void)[] = [];
  for (const L of layers) {
    const c = L.clip;
    if (L.kind === 'text') {
      const r = renderText(c, L.lt, W, H, slot);
      if (!r) continue;
      comp.draw({
        key: c.id, version: r.version, source: r.canvas as any, srcW: r.w, srcH: r.h, srcRot: 0, baseW: r.w, baseH: r.h,
        transform: L.transform, fx: { ...L.fx, dx: L.fx.dx + r.dx, opacity: L.fx.opacity * r.opacity, scale: L.fx.scale * r.scale }, premultiplied: true,
      });
      continue;
    }
    const rt = c.media ? runtime.get(c.media) : undefined;
    if (!rt) continue;
    if (L.kind === 'image') {
      if (!rt.image) continue;
      const [bw, bh] = fitSize(rt.image.width, rt.image.height, W, H, c.fit || 'cover');
      comp.draw({ key: c.id, version: c.media, source: rt.image, srcW: rt.image.width, srcH: rt.image.height, srcRot: 0, baseW: bw, baseH: bh, transform: L.transform, fx: L.fx, color: L.color });
      continue;
    }
    const f = await frameFor(L);
    const m = media[c.media!];
    const sw = f?.w || m.width || 16, sh = f?.h || m.height || 9;
    const [bw, bh] = fitSize(sw, sh, W, H, c.fit || 'cover');
    comp.draw({ key: c.id, version: f ? frameNo : undefined, source: f?.src ?? null, srcW: sw, srcH: sh, srcRot: 0, baseW: bw, baseH: bh, transform: L.transform, fx: L.fx, color: L.color });
    if (f?.release) releases.push(f.release);
  }
  for (const r of releases) r();
}

async function loadFonts(p: Project) {
  const waits = p.clips.filter(c => c.kind === 'text').map(c => ensureFont(textStyleOf(c)));
  await Promise.all(waits);
}

/** Video + audio codec choice for this browser. */
export async function pickCodecs(w: number, h: number, bitrate: number, needAudio: boolean) {
  let video: 'avc' | 'vp9' | null = null;
  if (typeof VideoEncoder !== 'undefined') {
    if (await canEncodeVideo('avc', { width: w, height: h, bitrate }).catch(() => false)) video = 'avc';
    else if (await canEncodeVideo('vp9', { width: w, height: h, bitrate }).catch(() => false)) video = 'vp9';
  }
  let audio: 'aac' | 'opus' | null = null;
  if (needAudio && video) {
    let nativeAac = false;
    try {
      nativeAac = typeof AudioEncoder !== 'undefined' && !!(await AudioEncoder.isConfigSupported({ codec: 'mp4a.40.2', sampleRate: MIX_RATE, numberOfChannels: 2, bitrate: 192000 })).supported;
    } catch { nativeAac = false; }
    if (video === 'avc' && (nativeAac || (wasmAllowed() && (registerAacEncoder(), await canEncodeAudio('aac').catch(() => false))))) audio = 'aac';
    else if (await canEncodeAudio('opus').catch(() => false)) audio = 'opus';
  }
  return { video, audio };
}

function wasmAllowed(): boolean {
  try {
    new WebAssembly.Module(new Uint8Array([0, 97, 115, 109, 1, 0, 0, 0]));
    return true;
  } catch {
    return false;
  }
}

/** Collects StreamTarget writes into Blob parts (monotonic with fastStart 'in-memory', patched otherwise). */
function blobCollector() {
  const parts: Uint8Array[] = [];
  let size = 0;
  const writable = new WritableStream<StreamTargetChunk>({
    write(chunk) {
      const data = chunk.data;
      if (chunk.position === size) { parts.push(data.slice()); size += data.byteLength; return; }
      // rare out-of-order write: patch in place
      const end = chunk.position + data.byteLength;
      if (end > size) { parts.push(new Uint8Array(end - size)); size = end; }
      let off = 0;
      for (const part of parts) {
        const pStart = off, pEnd = off + part.byteLength;
        const s = Math.max(pStart, chunk.position), e = Math.min(pEnd, end);
        if (s < e) part.set(data.subarray(s - chunk.position, e - chunk.position), s - pStart);
        off = pEnd;
      }
    },
  });
  return { writable, blob: (type: string) => new Blob(parts as BlobPart[], { type }) };
}

export async function exportVideo(
  settings: ExportSettings,
  onProgress: (phase: ExportPhase, frac: number, note?: string) => void,
  signal: AbortSignal,
): Promise<ExportResult> {
  const p: Project = deepClone(store.state.project);
  const media = store.state.media;
  const warnings: string[] = [];
  const total = projectDuration(p);
  if (total <= 0) throw new Error('The timeline is empty.');
  const { width: W, height: H, fps } = settings;
  const missing = p.clips.filter(c => c.media && !runtime.has(c.media));
  if (missing.length) throw new Error(`Re-link ${new Set(missing.map(c => media[c.media!]?.name)).size} offline media file(s) in the Media panel first.`);

  onProgress('prepare', 0);
  await loadFonts(p);
  const needAudio = p.clips.some(c => (c.kind === 'video' || c.kind === 'audio') && c.media && media[c.media]?.hasAudio && !c.muted);
  const codecs = await pickCodecs(W, H, settings.bitrate, needAudio);
  if (!codecs.video) throw new Error('NO_WEBCODECS');
  if (needAudio && !codecs.audio) warnings.push('This browser cannot encode audio, so the export is silent.');
  if (codecs.audio === 'opus' && codecs.video === 'avc') warnings.push('AAC audio is not available in this browser, so the MP4 uses Opus audio. Some apps may not play it; Chrome on Mac or Windows exports AAC.');

  // ---- audio first (gives an exact, sample-accurate mix) ----
  let mix: [Float32Array, Float32Array] | null = null;
  if (codecs.audio) {
    onProgress('audio', 0);
    mix = await mixAudio(p, media, total, f => onProgress('audio', f), signal, w => warnings.push(w));
  }
  if (signal.aborted) throw abortErr();

  // ---- output ----
  const ext: 'mp4' | 'webm' = codecs.video === 'avc' ? 'mp4' : 'webm';
  const sink = blobCollector();
  const output = new Output({
    format: ext === 'mp4' ? new Mp4OutputFormat({ fastStart: 'in-memory' }) : new WebMOutputFormat(),
    target: new StreamTarget(sink.writable),
  });
  const canvas = typeof OffscreenCanvas !== 'undefined' ? new OffscreenCanvas(W, H) : Object.assign(document.createElement('canvas'), { width: W, height: H });
  const comp = new Compositor(canvas, { preserve: true });
  comp.resize(W, H);
  const videoSource = new CanvasSource(canvas, { codec: codecs.video, bitrate: settings.bitrate, keyFrameInterval: 1 });
  output.addVideoTrack(videoSource, { frameRate: fps });
  let audioSource: AudioBufferSource | null = null;
  if (codecs.audio && mix) {
    audioSource = new AudioBufferSource({ codec: codecs.audio, bitrate: settings.audioBitrate });
    output.addAudioTrack(audioSource);
  }
  await output.start();

  // ---- plan decoding: the source times each clip needs, in frame order ----
  const nFrames = Math.max(1, Math.round(total * fps));
  const plans = new Map<string, { times: number[]; first: number; last: number }>();
  for (let n = 0; n < nFrames; n++) {
    const ev = evaluate(p, media, n / fps, { audio: false });
    for (const L of ev.layers) {
      if (L.kind !== 'video') continue;
      const rt = runtime.get(L.clip.media!);
      if (!rt?.video || !rt.canDecodeVideo) continue;
      let pl = plans.get(L.clip.id);
      if (!pl) { pl = { times: [], first: n, last: n }; plans.set(L.clip.id, pl); }
      pl.times.push(L.srcTime);
      pl.last = n;
    }
  }
  type Cursor = { it: AsyncGenerator<VideoSample | null>; };
  const cursors = new Map<string, Cursor>();
  const sc = new SampleCanvas();
  const elFrames = new ElementFrames();
  const maxLong = Math.round(Math.max(W, H) * 1.5);

  let audioPushed = 0; // frames of the mix already handed to the encoder
  const pushAudioUntil = async (tSec: number) => {
    if (!audioSource || !mix) return;
    const until = Math.min(mix[0].length, Math.ceil(tSec * MIX_RATE));
    while (audioPushed < until) {
      const len = Math.min(MIX_RATE, mix[0].length - audioPushed);
      const buf = new AudioBuffer({ numberOfChannels: 2, length: len, sampleRate: MIX_RATE });
      buf.copyToChannel(mix[0].subarray(audioPushed, audioPushed + len) as Float32Array<ArrayBuffer>, 0);
      buf.copyToChannel(mix[1].subarray(audioPushed, audioPushed + len) as Float32Array<ArrayBuffer>, 1);
      await audioSource.add(buf);
      audioPushed += len;
    }
  };

  const t0 = performance.now();
  try {
    for (let n = 0; n < nFrames; n++) {
      if (signal.aborted) throw abortErr();
      const t = n / fps;
      await pushAudioUntil(t + 1);
      const ev = evaluate(p, media, t, { audio: false });
      await drawOffline(comp, p, media, ev.layers, async L => {
        const c = L.clip;
        const pl = plans.get(c.id);
        if (pl) {
          let cur = cursors.get(c.id);
          if (!cur) {
            const sinkV = new VideoSampleSink(runtime.get(c.media!)!.video!);
            cur = { it: sinkV.samplesAtTimestamps(pl.times) };
            cursors.set(c.id, cur);
          }
          const r = await cur.it.next();
          const sample = r.done ? null : r.value;
          if (n >= pl.last) { void cur.it.return(undefined); cursors.delete(c.id); }
          if (!sample) return null;
          const out = sc.get(c.id, sample, maxLong);
          sample.close();
          return { src: out.canvas as any, w: out.w, h: out.h };
        }
        const el = await elFrames.get(c.media!, L.srcTime);
        return el ? { src: el, w: el.videoWidth, h: el.videoHeight } : null;
      }, 'x', n);
      await videoSource.add(t, 1 / fps);
      if (n % 3 === 0) {
        const el = (performance.now() - t0) / 1000;
        const eta = n > 5 ? (el / (n + 1)) * (nFrames - n - 1) : NaN;
        onProgress('video', (n + 1) / nFrames, Number.isFinite(eta) ? `${Math.ceil(eta)} s left` : undefined);
      }
    }
    await pushAudioUntil(total + 1);
    onProgress('finish', 1);
    await output.finalize();
  } catch (e) {
    await output.cancel().catch(() => {});
    throw e;
  } finally {
    for (const c of cursors.values()) void c.it.return(undefined);
    elFrames.dispose();
    comp.dispose();
    dropTextRasters('x');
  }
  const mime = ext === 'mp4' ? 'video/mp4' : 'video/webm';
  return { blob: sink.blob(mime), ext, videoCodec: codecs.video === 'avc' ? 'H.264' : 'VP9', audioCodec: codecs.audio ? (codecs.audio === 'aac' ? 'AAC' : 'Opus') : null, seconds: (performance.now() - t0) / 1000, warnings };
}

/** Real-time fallback for browsers without WebCodecs encoders: records the preview while it plays. */
export async function recordRealtime(onProgress: (f: number) => void, signal: AbortSignal): Promise<ExportResult> {
  const comp = player.comp;
  if (!comp || typeof MediaRecorder === 'undefined') throw new Error('This browser cannot export video.');
  const p = store.state.project;
  const total = projectDuration(p);
  player.ensureAudio();
  const stream = (comp.canvas as HTMLCanvasElement).captureStream(p.fps);
  player.streamDest?.stream.getAudioTracks().forEach(t => stream.addTrack(t));
  const types = ['video/mp4;codecs=avc1,mp4a.40.2', 'video/mp4', 'video/webm;codecs=vp9,opus', 'video/webm'];
  const mime = types.find(t => MediaRecorder.isTypeSupported(t)) || '';
  const rec = new MediaRecorder(stream, { mimeType: mime || undefined, videoBitsPerSecond: 12_000_000 });
  const chunks: Blob[] = [];
  rec.ondataavailable = e => { if (e.data.size) chunks.push(e.data); };
  const stopped = new Promise(r => { rec.onstop = r; });
  player.pause();
  player.seek(0);
  await new Promise(r => setTimeout(r, 300));
  rec.start(250);
  await player.play();
  const t0 = performance.now();
  await new Promise<void>(resolve => {
    const tick = () => {
      onProgress(clamp(player.time / total, 0, 1));
      if (!player.playing || signal.aborted || (performance.now() - t0) / 1000 > total + 5) resolve();
      else requestAnimationFrame(tick);
    };
    tick();
  });
  player.pause();
  rec.stop();
  await stopped;
  if (signal.aborted) throw abortErr();
  const type = (rec.mimeType || mime || 'video/webm').split(';')[0];
  return { blob: new Blob(chunks, { type }), ext: type.includes('mp4') ? 'mp4' : 'webm', videoCodec: 'browser default', audioCodec: 'browser default', seconds: total, warnings: ['Recorded in real time because this browser has no WebCodecs encoder.'] };
}

// ---------- stills for the Opus review ----------

const sinkCache = new Map<string, VideoSampleSink>();

/** Render timeline frames at the given times, `height` pixels tall. Random access, for reviews. */
export async function renderStills(p: Project, times: number[], height: number, signal?: AbortSignal): Promise<(HTMLCanvasElement | null)[]> {
  const media = store.state.media;
  const H = Math.round(height), W = Math.max(2, Math.round((H * p.width) / p.height));
  await loadFonts(p);
  const out: (HTMLCanvasElement | null)[] = [];
  const canvas = document.createElement('canvas');
  const comp = new Compositor(canvas, { preserve: true });
  comp.resize(W, H);
  const sc = new SampleCanvas();
  const elFrames = new ElementFrames();
  try {
    for (let i = 0; i < times.length; i++) {
      if (signal?.aborted) break;
      const ev = evaluate(p, media, times[i], { audio: false });
      await drawOffline(comp, p, media, ev.layers, async L => {
        const rt = runtime.get(L.clip.media!);
        if (!rt) return null;
        if (rt.video && rt.canDecodeVideo) {
          let sink = sinkCache.get(rt.url);
          if (!sink) { sink = new VideoSampleSink(rt.video); sinkCache.set(rt.url, sink); }
          const sample = await sink.getSample(L.srcTime);
          if (!sample) return null;
          const o = sc.get(L.clip.id, sample, Math.max(W, H) * 1.5);
          sample.close();
          return { src: o.canvas as any, w: o.w, h: o.h };
        }
        const el = await elFrames.get(L.clip.media!, L.srcTime);
        return el ? { src: el, w: el.videoWidth, h: el.videoHeight } : null;
      }, 'r', i + 1);
      const copy = document.createElement('canvas');
      copy.width = W; copy.height = H;
      copy.getContext('2d')!.drawImage(canvas, 0, 0);
      out.push(copy);
    }
  } finally {
    elFrames.dispose();
    comp.dispose();
    dropTextRasters('r');
  }
  return out;
}

export function clipsUsingMedia(p: Project, id: string): Clip[] { return p.clips.filter(c => c.media === id); }

export { BufferTarget };
