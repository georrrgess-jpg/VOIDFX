// Media library: import, probing, filmstrips, waveforms and analysis. Files are read through
// Mediabunny's BlobSource, which pulls byte ranges on demand, so multi-gigabyte files stay cheap.
import { ALL_FORMATS, AudioBufferSink, BlobSource, CanvasSink, Input, InputAudioTrack, InputVideoTrack } from 'mediabunny';
import { store } from '../state/store';
import { MediaInfo, MediaKind } from '../state/types';
import { shortId } from '../state/util';
import { AudioAnalyzer, PEAK_RATE } from './analysis';

export interface Thumb { t: number; img: CanvasImageSource; w: number; h: number }

export interface MediaRuntime {
  file: File;
  url: string;
  input: Input | null;
  video: InputVideoTrack | null;
  audio: InputAudioTrack | null;
  canDecodeVideo: boolean;
  canDecodeAudio: boolean;
  /** False when the browser's media element cannot play this file; the preview then decodes it with WebCodecs. */
  elementOk: boolean;
  thumbs: Thumb[];
  peaks: Float32Array | null;
  image: ImageBitmap | null;
  poster: string | null;
}

export const runtime = new Map<string, MediaRuntime>();

const VIDEO_EXT = /\.(mp4|m4v|mov|webm|mkv|avi|3gp|ts|mts|m2ts|ogv)$/i;
const AUDIO_EXT = /\.(mp3|wav|m4a|aac|ogg|oga|opus|flac|aif|aiff|weba)$/i;
const IMAGE_EXT = /\.(png|jpe?g|webp|gif|avif|bmp)$/i;

export function detectKind(f: File): MediaKind | null {
  const t = f.type || '';
  if (t.startsWith('video/') || VIDEO_EXT.test(f.name)) return 'video';
  if (t.startsWith('audio/') || AUDIO_EXT.test(f.name)) return 'audio';
  if (t.startsWith('image/') || IMAGE_EXT.test(f.name)) return 'image';
  return null;
}

function patchMedia(id: string, patch: Partial<MediaInfo>) {
  store.set(s => (s.media[id] ? { media: { ...s.media, [id]: { ...s.media[id], ...patch } } } : {}));
}

function bumpRuntime() {
  store.set(s => ({ mediaRev: s.mediaRev + 1 }));
}

/** Import files into the library. Files matching an offline entry (same name and size) re-link it. */
export async function importFiles(files: File[] | FileList): Promise<string[]> {
  const ids: string[] = [];
  const list = Array.from(files);
  for (const file of list) {
    const kind = detectKind(file);
    if (!kind) { store.toast(`${file.name} is not a video, audio or image file.`, 'error'); continue; }
    const st = store.state;
    const offline = st.mediaOrder.map(id => st.media[id]).find(m => m && m.status === 'offline' && m.name === file.name && m.size === file.size);
    const dup = st.mediaOrder.map(id => st.media[id]).find(m => m && m.status !== 'offline' && m.name === file.name && m.size === file.size && m.lastModified === file.lastModified);
    if (dup) { store.toast(`${file.name} is already in the library.`); ids.push(dup.id); continue; }
    const id = offline ? offline.id : shortId('m', new Set(st.mediaOrder));
    const info: MediaInfo = offline
      ? { ...offline, status: 'loading' }
      : {
        id, name: file.name, kind, size: file.size, lastModified: file.lastModified, mime: file.type, duration: 0, width: 0, height: 0,
        fps: 0, hasVideo: kind !== 'audio', hasAudio: kind !== 'image', rotation: 0, status: 'loading', analysisState: kind === 'image' ? 'none' : 'pending',
      };
    store.set(s => ({ media: { ...s.media, [id]: info }, mediaOrder: s.mediaOrder.includes(id) ? s.mediaOrder : [...s.mediaOrder, id] }));
    ids.push(id);
    runtime.set(id, { file, url: URL.createObjectURL(file), input: null, video: null, audio: null, canDecodeVideo: false, canDecodeAudio: false, elementOk: true, thumbs: [], peaks: null, image: null, poster: null });
    probe(id, file, kind, !!offline).catch(err => {
      console.error(err);
      patchMedia(id, { status: 'error', error: String(err?.message || err) });
      store.toast(`Could not open ${file.name}: ${err?.message || 'unsupported file'}`, 'error', 6000);
    });
  }
  return ids;
}

async function probe(id: string, file: File, kind: MediaKind, relink: boolean) {
  const rt = runtime.get(id)!;
  if (kind === 'image') {
    const probeBmp = await createImageBitmap(file);
    const { width, height } = probeBmp;
    let bmp = probeBmp;
    const maxSide = 4096;
    if (Math.max(width, height) > maxSide) {
      const s = maxSide / Math.max(width, height);
      bmp = await createImageBitmap(file, { resizeWidth: Math.round(width * s), resizeHeight: Math.round(height * s), resizeQuality: 'high' });
      probeBmp.close();
    }
    rt.image = bmp;
    rt.poster = posterFrom(bmp, bmp.width, bmp.height);
    rt.thumbs = [{ t: 0, img: bmp, w: bmp.width, h: bmp.height }];
    patchMedia(id, { status: 'ready', width, height, duration: 0, hasAudio: false, hasVideo: true, analysisState: 'none' });
    bumpRuntime();
    return;
  }

  let input: Input | null = null;
  try {
    input = new Input({ formats: ALL_FORMATS, source: new BlobSource(file) });
    if (!(await input.canRead())) { input.dispose(); input = null; }
  } catch {
    input = null;
  }

  const patch: Partial<MediaInfo> = {};
  if (input) {
    const v = kind === 'video' ? await input.getPrimaryVideoTrack() : null;
    const a = await input.getPrimaryAudioTrack();
    rt.input = input;
    rt.video = v;
    rt.audio = a;
    const dur = (await input.getDurationFromMetadata().catch(() => null)) ?? (await input.computeDuration());
    patch.duration = dur;
    patch.hasVideo = !!v;
    patch.hasAudio = !!a;
    if (v) {
      patch.width = await v.getDisplayWidth();
      patch.height = await v.getDisplayHeight();
      patch.rotation = await v.getRotation();
      patch.codec = (await v.getCodec()) || undefined;
      rt.canDecodeVideo = await v.canDecode().catch(() => false);
      try {
        const fr = await v.computeFrameRateMetrics({ targetPacketCount: 120 });
        patch.fps = Math.round(fr.bestGuessFrameRate * 100) / 100;
      } catch { patch.fps = 30; }
    }
    if (a) {
      patch.audioCodec = (await a.getCodec()) || undefined;
      rt.canDecodeAudio = await a.canDecode().catch(() => false);
    }
    if (kind === 'video' && !v) {
      // a "video" file with only sound (e.g. .webm voice memo)
      patch.hasVideo = false;
    }
  }

  // The preview plays through a media element when the browser can decode the file; otherwise it
  // falls back to WebCodecs. Check by actually decoding a frame, not just reading the header.
  const el = document.createElement(kind === 'audio' ? 'audio' : 'video');
  el.preload = 'auto';
  el.muted = true;
  el.src = rt.url;
  const meta = await new Promise<{ ok: boolean; d: number; w: number; h: number }>(resolve => {
    let settled = false;
    const done = (ok: boolean) => {
      if (settled) return;
      settled = true;
      resolve({ ok, d: el.duration, w: (el as HTMLVideoElement).videoWidth || 0, h: (el as HTMLVideoElement).videoHeight || 0 });
    };
    el.onerror = () => done(false);
    el.onloadedmetadata = () => {
      if (kind === 'audio' || !(el as HTMLVideoElement).videoWidth) { el.oncanplay = () => done(true); return; }
      el.onseeked = () => setTimeout(() => done(!el.error && el.readyState >= 2), 60);
      el.currentTime = Math.min(0.5, (Number.isFinite(el.duration) ? el.duration : 1) / 2);
    };
    setTimeout(() => done(!el.error && el.readyState >= 2), 12000);
  });
  el.removeAttribute('src');
  el.load();
  rt.elementOk = meta.ok;
  if (!input && !meta.ok) throw new Error('this browser cannot read the file');
  if (!meta.ok && kind !== 'audio' && !rt.canDecodeVideo) throw new Error('this browser cannot decode this video codec');
  if (!patch.duration || !Number.isFinite(patch.duration)) patch.duration = Number.isFinite(meta.d) ? meta.d : 0;
  if (!patch.width && meta.w) { patch.width = meta.w; patch.height = meta.h; }
  if (!patch.fps) patch.fps = 30;
  if (patch.hasVideo === undefined) patch.hasVideo = kind === 'video';
  if (patch.hasAudio === undefined) patch.hasAudio = true;
  const finalKind: MediaKind = kind === 'video' && patch.hasVideo === false ? 'audio' : kind;
  patchMedia(id, { ...patch, kind: finalKind, status: 'ready', analysisState: patch.hasAudio ? (relink && store.state.media[id]?.analysis ? 'done' : 'pending') : 'none' });

  // background work: thumbnails first (visible), then audio
  queue(() => buildThumbs(id));
  if (patch.hasAudio) queue(() => buildAudio(id, relink && !!store.state.media[id]?.analysis));
}

// ---------- background queue (one heavy job at a time keeps the UI responsive) ----------

const jobs: (() => Promise<void>)[] = [];
let busy = false;
function queue(job: () => Promise<void>) {
  jobs.push(job);
  if (!busy) void pump();
}
async function pump() {
  busy = true;
  while (jobs.length) {
    const j = jobs.shift()!;
    try { await j(); } catch (e) { console.warn('media job failed', e); }
  }
  busy = false;
}
export const mediaBusy = () => busy || jobs.length > 0;
/** Resolves when queued imports, thumbnails and analysis are finished. */
export async function whenMediaIdle(timeoutMs = 600000) {
  const t0 = Date.now();
  while ((busy || jobs.length) && Date.now() - t0 < timeoutMs) await new Promise(r => setTimeout(r, 200));
  while (store.state.mediaOrder.some(id => store.state.media[id]?.status === 'loading') && Date.now() - t0 < timeoutMs) await new Promise(r => setTimeout(r, 200));
}

function posterFrom(img: CanvasImageSource, w: number, h: number): string {
  const c = document.createElement('canvas');
  const s = 240 / Math.max(w, h);
  c.width = Math.max(1, Math.round(w * s));
  c.height = Math.max(1, Math.round(h * s));
  c.getContext('2d')!.drawImage(img, 0, 0, c.width, c.height);
  return c.toDataURL('image/jpeg', 0.75);
}

async function buildThumbs(id: string) {
  const rt = runtime.get(id);
  const m = store.state.media[id];
  if (!rt || !m || !m.hasVideo || m.kind !== 'video') return;
  const count = Math.max(6, Math.min(160, Math.round(m.duration / 1.5)));
  const times = Array.from({ length: count }, (_, i) => ((i + 0.5) / count) * m.duration);
  const frames = await grabFrames(id, times, 120);
  rt.thumbs = frames.filter(f => f.img).map(f => ({ t: f.t, img: f.img!, w: f.w, h: f.h }));
  const posterSrc = rt.thumbs[Math.min(rt.thumbs.length - 1, Math.floor(rt.thumbs.length * 0.15))];
  if (posterSrc) rt.poster = posterFrom(posterSrc.img, posterSrc.w, posterSrc.h);
  bumpRuntime();
}

/**
 * Frames of a media file at the given source times, `height` pixels tall, rotation applied.
 * Decodes with WebCodecs where possible and falls back to seeking a media element.
 */
export async function grabFrames(id: string, times: number[], height: number, signal?: AbortSignal): Promise<{ t: number; img: CanvasImageSource | null; w: number; h: number }[]> {
  const rt = runtime.get(id);
  const m = store.state.media[id];
  if (!rt || !m) return times.map(t => ({ t, img: null, w: 0, h: 0 }));
  if (m.kind === 'image' && rt.image) return times.map(t => ({ t, img: rt.image, w: rt.image!.width, h: rt.image!.height }));
  const order = times.map((t, i) => ({ t, i })).sort((a, b) => a.t - b.t);
  const out: { t: number; img: CanvasImageSource | null; w: number; h: number }[] = times.map(t => ({ t, img: null, w: 0, h: 0 }));
  const H = Math.max(16, Math.round(height));
  if (rt.video && rt.canDecodeVideo) {
    try {
      const W = Math.max(16, Math.round((H * (m.width || 16)) / (m.height || 9)));
      const sink = new CanvasSink(rt.video, { width: W, height: H, fit: 'fill' });
      let k = 0;
      for await (const wc of sink.canvasesAtTimestamps(order.map(o => Math.max(0, o.t)))) {
        if (signal?.aborted) break;
        const slot = order[k++];
        if (wc) {
          // copy: the sink may recycle canvases
          const c = document.createElement('canvas');
          c.width = W; c.height = H;
          c.getContext('2d')!.drawImage(wc.canvas as CanvasImageSource, 0, 0);
          out[slot.i] = { t: slot.t, img: c, w: W, h: H };
        }
      }
      if (out.some(o => o.img)) return out;
    } catch (e) {
      console.warn('WebCodecs frame grab failed, falling back to element seeking', e);
    }
  }
  // fallback: seek a hidden video element
  const v = document.createElement('video');
  v.muted = true;
  v.preload = 'auto';
  v.src = rt.url;
  await new Promise<void>(r => { v.onloadeddata = () => r(); v.onerror = () => r(); setTimeout(r, 10000); });
  const W = Math.max(16, Math.round((H * (v.videoWidth || 16)) / (v.videoHeight || 9)));
  for (const o of order) {
    if (signal?.aborted) break;
    await new Promise<void>(r => {
      const done = () => { v.removeEventListener('seeked', done); r(); };
      v.addEventListener('seeked', done);
      v.currentTime = Math.min(Math.max(0, o.t), Math.max(0, (v.duration || o.t) - 0.05));
      setTimeout(done, 3000);
    });
    const c = document.createElement('canvas');
    c.width = W; c.height = H;
    try { c.getContext('2d')!.drawImage(v, 0, 0, W, H); out[o.i] = { t: o.t, img: c, w: W, h: H }; } catch { /* not decodable */ }
  }
  v.removeAttribute('src');
  v.load();
  return out;
}

/** Decode the audio once: waveform peaks plus the analysis Opus reads instead of listening. */
async function buildAudio(id: string, haveAnalysis: boolean) {
  const rt = runtime.get(id);
  const m = store.state.media[id];
  if (!rt || !m || !m.hasAudio) return;
  patchMedia(id, { analysisState: 'running' });
  try {
    let result: { analysis: any; peaks: Float32Array } | null = null;
    if (rt.audio && rt.canDecodeAudio) {
      const sr = await rt.audio.getSampleRate();
      const an = new AudioAnalyzer(sr);
      const sink = new AudioBufferSink(rt.audio);
      let mono = new Float32Array(0);
      for await (const { buffer } of sink.buffers()) {
        const n = buffer.length;
        if (mono.length < n) mono = new Float32Array(n);
        const view = mono.subarray(0, n);
        view.fill(0);
        const chs = buffer.numberOfChannels;
        for (let ch = 0; ch < chs; ch++) {
          const d = buffer.getChannelData(ch);
          for (let i = 0; i < n; i++) view[i] += d[i] / chs;
        }
        an.pushBlock(view);
      }
      result = an.finish();
    } else if (rt.file.size < 400 * 1024 * 1024) {
      // small files the WebCodecs path cannot decode: let Web Audio decode the whole file
      const AC = window.OfflineAudioContext || (window as any).webkitOfflineAudioContext;
      const ctx = new AC(1, 1, 44100);
      const buf = await ctx.decodeAudioData(await rt.file.arrayBuffer());
      const an = new AudioAnalyzer(buf.sampleRate);
      const n = buf.length;
      const mono = new Float32Array(n);
      for (let ch = 0; ch < buf.numberOfChannels; ch++) {
        const d = buf.getChannelData(ch);
        for (let i = 0; i < n; i++) mono[i] += d[i] / buf.numberOfChannels;
      }
      for (let i = 0; i < n; i += 65536) an.pushBlock(mono.subarray(i, Math.min(n, i + 65536)));
      result = an.finish();
    }
    if (!result) { patchMedia(id, { analysisState: 'none' }); return; }
    rt.peaks = result.peaks;
    patchMedia(id, { analysis: haveAnalysis ? store.state.media[id]?.analysis : result.analysis, analysisState: 'done' });
    bumpRuntime();
  } catch (e) {
    console.warn('audio analysis failed', e);
    patchMedia(id, { analysisState: 'error' });
  }
}

export function removeMedia(id: string) {
  const rt = runtime.get(id);
  if (rt) {
    URL.revokeObjectURL(rt.url);
    rt.input?.dispose();
    rt.image?.close();
    runtime.delete(id);
  }
  store.commit(p => { p.clips = p.clips.filter(c => c.media !== id); });
  store.set(s => {
    const media = { ...s.media };
    delete media[id];
    return { media, mediaOrder: s.mediaOrder.filter(x => x !== id) };
  });
}

export { PEAK_RATE };
