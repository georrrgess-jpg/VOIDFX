// Offline, frame-accurate export (WebCodecs via Mediabunny) and still rendering for Opus reviews.
import {
  AudioSample, AudioSampleSource, BufferTarget, CanvasSource, Mp4OutputFormat, Output, StreamTarget, StreamTargetChunk,
  VideoSample, VideoSampleSink, WebMOutputFormat, canEncodeAudio, canEncodeVideo,
} from 'mediabunny';
import { registerAacEncoder } from '@mediabunny/aac-encoder';
import { preloadGraphics } from './custom';
import { runtime } from '../media/library';
import { store } from '../state/store';
import { Clip, MediaInfo, Project } from '../state/types';
import { clamp, deepClone, projectDuration, textStyleOf } from '../state/util';
import { mixAudio, MIX_RATE } from './audiomix';
import { Compositor } from './compositor';
import { drawLayers, FrameRef } from './drawlayers';
import { loadLogo } from './logo';
import { masterMix, MasterStats } from './loudness';
import { evaluate, VisualLayer } from './evaluate';
import { player } from './player';
import { dropTextRasters, ensureFont } from './text';

export interface ExportSettings { width: number; height: number; fps: number; bitrate: number; audioBitrate: number; loudness?: { target: number; ceiling: number } | null }
export interface ExportResult { blob: Blob; ext: 'mp4' | 'webm'; videoCodec: string; audioCodec: string | null; seconds: number; warnings: string[]; master?: MasterStats; frames?: number }
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
  const frames = new Map<string, FrameRef | null>();
  const releases: (() => void)[] = [];
  for (const L of layers) {
    if (L.kind !== 'video') continue;
    const f = await frameFor(L);
    frames.set(L.clip.id, f ? { src: f.src, w: f.w, h: f.h, version: frameNo } : null);
    if (f?.release) releases.push(f.release);
  }
  drawLayers(comp, p, media, layers, L => frames.get(L.clip.id), slot);
  for (const r of releases) r();
}

async function loadFonts(p: Project, frameW = p.width) {
  const waits: Promise<unknown>[] = p.clips.filter(c => c.kind === 'text').map(c => ensureFont(textStyleOf(c)));
  if (p.clips.some(c => c.transition?.type === 'logo')) waits.push(loadLogo());
  if (p.clips.some(c => c.kind === 'graphic')) waits.push(preloadGraphics(p, frameW));
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
  // Encoder delay in samples. The bundled WASM AAC encoder (FFmpeg's) primes with 1024 samples and does
  // not report it, so the export feeds audio from -1024 samples and the MP4 edit list trims the priming:
  // audio and video then start together and end at the same frame (the loop needs both).
  let priming = 0;
  if (needAudio && video) {
    let nativeAac = false;
    try {
      nativeAac = typeof AudioEncoder !== 'undefined' && !!(await AudioEncoder.isConfigSupported({ codec: 'mp4a.40.2', sampleRate: MIX_RATE, numberOfChannels: 2, bitrate: 192000 })).supported;
    } catch { nativeAac = false; }
    if (video === 'avc' && nativeAac) audio = 'aac';
    else if (video === 'avc' && wasmAllowed() && (registerAacEncoder(), await canEncodeAudio('aac').catch(() => false))) { audio = 'aac'; priming = 1024; }
    else if (await canEncodeAudio('opus').catch(() => false)) audio = 'opus';
  }
  return { video, audio, priming };
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
  return { writable, parts, blob: (type: string) => new Blob(parts as BlobPart[], { type }) };
}

/**
 * The AAC encoder pads its last frame, so the audio track runs up to 21 ms past the picture. With fast-start
 * the moov box is at the head of the file: set the audio edit's duration (and the track and movie durations)
 * to the picture's length, so audio and video end on the same frame and the loop wraps cleanly.
 */
function clampAudioEdit(parts: Uint8Array[], seconds: number): boolean {
  const offs: number[] = []; let acc = 0;
  for (const pt of parts) { offs.push(acc); acc += pt.byteLength; }
  const total = acc;
  const loc = (pos: number) => { let i = offs.length - 1; while (i > 0 && offs[i] > pos) i--; return [i, pos - offs[i]] as const; };
  const u8 = (pos: number) => { const [i, o] = loc(pos); return parts[i][o]; };
  const set8 = (pos: number, v: number) => { const [i, o] = loc(pos); parts[i][o] = v & 255; };
  const u32 = (pos: number) => ((u8(pos) << 24) >>> 0) + (u8(pos + 1) << 16) + (u8(pos + 2) << 8) + u8(pos + 3);
  const put32 = (pos: number, v: number) => { for (let k = 0; k < 4; k++) set8(pos + k, Math.floor(v / 2 ** (8 * (3 - k)))); };
  const put64 = (pos: number, v: number) => { put32(pos, Math.floor(v / 2 ** 32)); put32(pos + 4, v % 2 ** 32); };
  const type = (pos: number) => String.fromCharCode(u8(pos + 4), u8(pos + 5), u8(pos + 6), u8(pos + 7));
  const boxes = (start: number, end: number) => {
    const out: { t: string; s: number; e: number; h: number }[] = [];
    for (let pos = start; pos + 8 <= end;) {
      let size = u32(pos), h = 8;
      if (size === 1) { size = u32(pos + 8) * 2 ** 32 + u32(pos + 12); h = 16; }
      if (size < h || pos + size > end) break;
      out.push({ t: type(pos), s: pos, e: pos + size, h });
      pos += size;
    }
    return out;
  };
  const moov = boxes(0, Math.min(total, 64 * 1024 * 1024)).find(b => b.t === 'moov');
  if (!moov) return false;
  const kids = boxes(moov.s + moov.h, moov.e);
  const mvhd = kids.find(b => b.t === 'mvhd');
  if (!mvhd) return false;
  const mv1 = u8(mvhd.s + 8) === 1;
  const scale = u32(mvhd.s + (mv1 ? 28 : 20));
  const dur = Math.round(seconds * scale);
  let done = false;
  for (const trak of kids.filter(b => b.t === 'trak')) {
    const tk = boxes(trak.s + trak.h, trak.e);
    const mdia = tk.find(b => b.t === 'mdia');
    const hdlr = mdia && boxes(mdia.s + mdia.h, mdia.e).find(b => b.t === 'hdlr');
    if (!hdlr || type(hdlr.s + 12) !== 'soun') continue;
    const edts = tk.find(b => b.t === 'edts');
    const elst = edts && boxes(edts.s + edts.h, edts.e).find(b => b.t === 'elst');
    if (!elst || u32(elst.s + 12) !== 1) return false; // only the single trimming edit Mediabunny writes for priming
    const ev1 = u8(elst.s + 8) === 1;
    if (ev1) put64(elst.s + 16, dur); else put32(elst.s + 16, dur);
    const tkhd = tk.find(b => b.t === 'tkhd');
    if (tkhd) { if (u8(tkhd.s + 8) === 1) put64(tkhd.s + 36, dur); else put32(tkhd.s + 28, dur); }
    done = true;
  }
  if (done) { if (mv1) put64(mvhd.s + 32, dur); else put32(mvhd.s + 24, dur); }
  return done;
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
  if (total > 3600) throw new Error(`The edit is ${Math.round(total)} s long; something sits far down the timeline. Check the last clips.`);
  const { width: W, height: H, fps } = settings;
  const missing = p.clips.filter(c => c.media && !runtime.has(c.media));
  if (missing.length) {
    const names = [...new Set(missing.map(c => media[c.media!]?.name || c.media!))];
    throw new Error(`${names.length} media file${names.length > 1 ? 's are' : ' is'} offline: ${names.slice(0, 4).join(', ')}${names.length > 4 ? '…' : ''}. This browser no longer has ${names.length > 1 ? 'these files' : 'this file'} (storage was full or cleared). Re-import ${names.length > 1 ? 'them' : 'it'} in the Media panel (the clips re-link by name), or remove the clips that use ${names.length > 1 ? 'them' : 'it'}, then export again.`);
  }

  onProgress('prepare', 0);
  await loadFonts(p, W);
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
  let master: MasterStats | undefined;
  if (mix) {
    if (settings.loudness) {
      master = masterMix(mix[0], mix[1], settings.loudness.target, settings.loudness.ceiling);
    } else {
      let peak = 0;
      for (const ch of mix) for (let i = 0; i < ch.length; i++) { const a = Math.abs(ch[i]); if (a > peak) peak = a; }
      if (peak > 0.98) {
        const k = 0.98 / peak;
        for (const ch of mix) for (let i = 0; i < ch.length; i++) ch[i] *= k;
        warnings.push(`The mix peaked at ${(20 * Math.log10(peak)).toFixed(1)} dBFS and was turned down to avoid clipping.`);
      }
    }
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
  let audioSource: AudioSampleSource | null = null;
  if (codecs.audio && mix) {
    audioSource = new AudioSampleSource({ codec: codecs.audio, bitrate: settings.audioBitrate });
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
  const failedDecode = new Set<string>();
  const sc = new SampleCanvas();
  const elFrames = new ElementFrames();
  const maxLong = Math.round(Math.max(W, H) * 1.5);

  let audioPushed = 0; // frames of the mix already handed to the encoder
  const pushAudioUntil = async (tSec: number) => {
    if (!audioSource || !mix) return;
    const until = Math.min(mix[0].length, Math.ceil(tSec * MIX_RATE));
    while (audioPushed < until) {
      const len = Math.min(MIX_RATE, mix[0].length - audioPushed);
      const data = new Float32Array(len * 2);
      data.set(mix[0].subarray(audioPushed, audioPushed + len), 0);
      data.set(mix[1].subarray(audioPushed, audioPushed + len), len);
      const sample = new AudioSample({ data, format: 'f32-planar', numberOfChannels: 2, sampleRate: MIX_RATE, timestamp: (audioPushed - codecs.priming) / MIX_RATE });
      await audioSource.add(sample);
      sample.close();
      audioPushed += len;
    }
  };

  const t0 = performance.now();
  let phaseNow = 'rendering frames', frameNow = 0;
  try {
    for (let n = 0; n < nFrames; n++) {
      if (signal.aborted) throw abortErr();
      const t = n / fps;
      frameNow = n + 1;
      await pushAudioUntil(t + 1);
      const ev = evaluate(p, media, t, { audio: false });
      if (comp.lost) throw new Error(`the graphics card stopped responding at ${t.toFixed(2)} s${comp.lastShader ? ` while drawing effect ${comp.lastShader}` : ''}. That effect is too heavy for this computer: turn it off or simplify it (Edit tab), then export again`);
      await drawOffline(comp, p, media, ev.layers, async L => {
        const c = L.clip;
        const pl = failedDecode.has(c.id) ? undefined : plans.get(c.id);
        if (pl) {
          try {
            let cur = cursors.get(c.id);
            if (!cur) {
              const sinkV = new VideoSampleSink(runtime.get(c.media!)!.video!);
              cur = { it: sinkV.samplesAtTimestamps(pl.times) };
              cursors.set(c.id, cur);
            }
            const r = await cur.it.next();
            const sample = r.done ? null : r.value;
            if (n >= pl.last) { void cur.it.return(undefined); cursors.delete(c.id); }
            if (sample) {
              const out = sc.get(c.id, sample, maxLong);
              sample.close();
              return { src: out.canvas as any, w: out.w, h: out.h };
            }
          } catch (e) {
            // a file the decoder chokes on: finish the clip by seeking a media element instead
            console.warn('decode failed, falling back', c.id, e);
            failedDecode.add(c.id);
            const cur = cursors.get(c.id);
            if (cur) { void cur.it.return(undefined).catch(() => undefined); cursors.delete(c.id); }
            warnings.push(`${media[c.media!]?.name || c.media} could not be decoded directly from ${t.toFixed(2)} s; those frames were taken from the browser's player instead.`);
          }
        }
        const el = await elFrames.get(c.media!, L.srcTime).catch(() => null);
        return el ? { src: el, w: el.videoWidth, h: el.videoHeight } : null;
      }, 'x', n);
      await videoSource.add(t, 1 / fps);
      if (n % 3 === 0) {
        const el = (performance.now() - t0) / 1000;
        const eta = n > 5 ? (el / (n + 1)) * (nFrames - n - 1) : NaN;
        onProgress('video', (n + 1) / nFrames, Number.isFinite(eta) ? `${Math.ceil(eta)} s left` : undefined);
      }
    }
    phaseNow = 'writing the audio';
    await pushAudioUntil(total + 1);
    onProgress('finish', 1);
    phaseNow = 'finishing the file';
    await output.finalize();
  } catch (e: any) {
    await output.cancel().catch(() => {});
    if (e?.name === 'AbortError') throw e;
    const msg = String(e?.message || e);
    throw new Error(/^the graphics card|offline/.test(msg) ? msg : `${msg} (while ${phaseNow}; frame ${frameNow} of ${nFrames})`);
  } finally {
    for (const c of cursors.values()) void c.it.return(undefined);
    elFrames.dispose();
    comp.dispose();
    dropTextRasters('x');
  }
  const mime = ext === 'mp4' ? 'video/mp4' : 'video/webm';
  if (ext === 'mp4' && codecs.priming && audioSource) { try { clampAudioEdit(sink.parts, nFrames / fps); } catch { /* leave the file as written */ } }
  return { blob: sink.blob(mime), ext, videoCodec: codecs.video === 'avc' ? 'H.264' : 'VP9', audioCodec: codecs.audio ? (codecs.audio === 'aac' ? 'AAC' : 'Opus') : null, seconds: (performance.now() - t0) / 1000, warnings, master, frames: nFrames };
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
export async function renderStills(p: Project, times: number[], height: number, signal?: AbortSignal, media: Record<string, MediaInfo> = store.state.media): Promise<(HTMLCanvasElement | null)[]> {
  const H = Math.round(height), W = Math.max(2, Math.round((H * p.width) / p.height));
  await loadFonts(p, W);
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

/**
 * Loop seam: blurred mean difference (0-255) between frame 0 and the last frame, and the size of a normal
 * frame-to-frame step on either side of the wrap (grain and moving layers change every frame anyway), so
 * the jump can be judged against what the eye already accepts.
 */
export async function measureLoopSeam(p: Project, media: Record<string, MediaInfo> = store.state.media): Promise<{ seam: number; step: number } | null> {
  const dur = projectDuration(p);
  if (dur <= 0.2) return null;
  const f = 1 / p.fps;
  const [a, a1, b0, b] = await renderStills(p, [0, f, Math.max(0, dur - 2 * f), Math.max(0, dur - f)], 96, undefined, media);
  if (!a || !b) return null;
  const w = 18, h = Math.max(8, Math.round((18 * p.height) / p.width));
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const g = c.getContext('2d', { willReadFrequently: true })!;
  const px = (im: HTMLCanvasElement) => { g.drawImage(im, 0, 0, w, h); return g.getImageData(0, 0, w, h).data; };
  const diff = (x: Uint8ClampedArray, y: Uint8ClampedArray) => { let s = 0; for (let i = 0; i < x.length; i += 4) s += (Math.abs(x[i] - y[i]) + Math.abs(x[i + 1] - y[i + 1]) + Math.abs(x[i + 2] - y[i + 2])) / 3; return s / (w * h); };
  const da = px(a), db = px(b);
  const seam = diff(da, db);
  const step = Math.max(a1 ? diff(da, px(a1)) : 0, b0 ? diff(px(b0), db) : 0);
  return { seam, step };
}
