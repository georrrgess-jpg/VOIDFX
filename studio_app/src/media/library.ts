// Media: import, probing, filmstrips, waveforms, analysis and shot detection. Files are read through
// Mediabunny's BlobSource, which pulls byte ranges on demand, so multi-gigabyte files stay cheap.
// Every imported file is also kept in this browser's storage so projects reopen with their media.
import { ALL_FORMATS, AudioBufferSink, BlobSource, CanvasSink, Input, InputAudioTrack, InputVideoTrack } from 'mediabunny';
import { store } from '../state/store';
import { AudioAnalysis, MediaInfo, MediaKind } from '../state/types';
import { blobKeyFor, getBlob, idbGet, idbPut, pinnedBlobs, saveBlob } from '../state/storage';
import { AudioAnalyzer, PEAK_RATE } from './analysis';

export interface Thumb { t: number; img: CanvasImageSource; w: number; h: number }

export interface MediaRuntime {
  file: Blob;
  /** Storage key of the file (shared between projects and jobs that use the same file). */
  blobId?: string;
  /** Media bays (the open editor 'ui', background jobs) using this file. */
  users: Set<string>;
  /** Everything known about the file (seed info plus what probing found). */
  meta: MediaInfo;
  ready: boolean;
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

export interface Derived { peaks?: Float32Array; analysis?: AudioAnalysis | null; poster?: string; shots?: [number, number][] }

export const runtime = new Map<string, MediaRuntime>();

/**
 * A media bay is one place media lives: the open editor (the store) or a background job's own copy of
 * a project. Loaded files are shared between bays by media id (ids are unique across projects), so a
 * job and the editor working on the same project read the same file handles.
 */
export interface MediaBay {
  key: string;
  media(): Record<string, MediaInfo>;
  order(): string[];
  add(info: MediaInfo): void;
  patch(id: string, patch: Partial<MediaInfo>): void;
  /** Build timeline filmstrips (only the editor needs them). */
  thumbs: boolean;
}

export const uiBay: MediaBay = {
  key: 'ui',
  media: () => store.state.media,
  order: () => store.state.mediaOrder,
  add: info => store.set(s => ({ media: { ...s.media, [info.id]: info }, mediaOrder: s.mediaOrder.includes(info.id) ? s.mediaOrder : [...s.mediaOrder, info.id] })),
  patch: (id, patch) => store.set(s => (s.media[id] ? { media: { ...s.media, [id]: { ...s.media[id], ...patch } } } : {})),
  thumbs: true,
};

const bays = new Map<string, MediaBay>([['ui', uiBay]]);
export function registerBay(b: MediaBay) { bays.set(b.key, b); }

/** Media ids are unique across every project, so loaded files can be shared safely. */
export function newMediaId(taken: Iterable<string> = []): string {
  const used = new Set(taken);
  for (;;) {
    const id = 'm' + Math.random().toString(36).slice(2, 7);
    if (id.length === 6 && !used.has(id) && !runtime.has(id)) return id;
  }
}

const VIDEO_EXT = /\.(mp4|m4v|mov|webm|mkv|avi|3gp|ts|mts|m2ts|ogv)$/i;
const AUDIO_EXT = /\.(mp3|wav|m4a|aac|ogg|oga|opus|flac|aif|aiff|weba)$/i;
const IMAGE_EXT = /\.(png|jpe?g|webp|gif|avif|bmp)$/i;

export function detectKind(f: { name: string; type?: string }): MediaKind | null {
  const t = f.type || '';
  if (t.startsWith('video/') || VIDEO_EXT.test(f.name)) return 'video';
  if (t.startsWith('audio/') || AUDIO_EXT.test(f.name)) return 'audio';
  if (t.startsWith('image/') || IMAGE_EXT.test(f.name)) return 'image';
  return null;
}

/** Update a file's info in every bay that uses it. */
function patchMedia(id: string, patch: Partial<MediaInfo>) {
  const rt = runtime.get(id);
  if (rt) rt.meta = { ...rt.meta, ...patch };
  const users = rt ? [...rt.users] : ['ui'];
  for (const k of users) bays.get(k)?.patch(id, patch);
}

function bumpRuntime() {
  store.set(s => ({ mediaRev: s.mediaRev + 1 }));
}

let quotaWarned = false;

/** Import files into the current project's library. */
export async function importFiles(files: File[] | FileList, opts: { origin?: 'file' | 'library'; tags?: string[] } = {}): Promise<string[]> {
  const ids: string[] = [];
  if (store.blocked()) return ids;
  for (const file of Array.from(files)) {
    const kind = detectKind(file);
    if (!kind) { store.toast(`${file.name} is not a video, audio or image file.`, 'error'); continue; }
    const st = store.state;
    const key = blobKeyFor(file);
    const dup = st.mediaOrder.map(id => st.media[id]).find(m => m && m.blobId === key && m.status !== 'offline');
    if (dup) { ids.push(dup.id); continue; }
    const offline = st.mediaOrder.map(id => st.media[id]).find(m => m && m.status === 'offline' && m.name === file.name && m.size === file.size);
    const id = offline ? offline.id : newMediaId(st.mediaOrder);
    const info: MediaInfo = offline
      ? { ...offline, status: 'loading', blobId: key }
      : {
        id, name: file.name, kind, size: file.size, lastModified: file.lastModified, mime: file.type, duration: 0, width: 0, height: 0,
        fps: 0, hasVideo: kind !== 'audio', hasAudio: kind !== 'image', rotation: 0, status: 'loading', blobId: key,
        analysisState: kind === 'image' ? 'none' : 'pending', origin: opts.origin || 'file', tags: opts.tags,
      };
    uiBay.add(info);
    ids.push(id);
    attach(uiBay, info, file, false);
    // keep the bytes so the project reopens with its media (large files are written to disk by the browser)
    void saveBlob(file, key).then(k => {
      if (!k && !quotaWarned) {
        quotaWarned = true;
        store.toast('This browser has no room to keep a copy of that file. It works now, but re-import it after a reload.', 'error', 7000);
      }
    });
  }
  return ids;
}

/** Bring stored media of a project back online in a bay (the editor by default). */
export async function attachStored(list: MediaInfo[], bay: MediaBay = uiBay, files?: Map<string, Blob>) {
  for (const m of list) {
    if (!m.blobId) continue;
    if (adopt(bay, m)) continue;
    const blob = files?.get(m.blobId) || (await getBlob(m.blobId).catch(() => undefined));
    if (!blob) { bay.patch(m.id, { status: 'offline' }); continue; }
    bay.patch(m.id, { status: 'loading' });
    attach(bay, { ...m, status: 'loading' }, blob, true);
  }
}

/** Use a file another bay already loaded (same id and file). */
function adopt(bay: MediaBay, m: MediaInfo): boolean {
  const rt = runtime.get(m.id);
  if (!rt || (rt.blobId && m.blobId && rt.blobId !== m.blobId)) return false;
  rt.users.add(bay.key);
  if (rt.ready) bay.patch(m.id, { ...rt.meta, id: m.id, status: 'ready' });
  else bay.patch(m.id, { status: 'loading' });
  if (bay.thumbs && rt.ready && !rt.thumbs.length && rt.meta.kind === 'video') queue(() => buildThumbs(m.id));
  return true;
}

/** Add a stored database item to the current project's library (no copy of the file is made). */
export async function attachLibraryItem(item: { id: string; blobId: string; name: string; kind: MediaKind; size: number; tags?: string[] }, bay: MediaBay = uiBay): Promise<string | null> {
  if (bay === uiBay && store.blocked()) return null;
  const existing = bay.order().map(id => bay.media()[id]).find(m => m && m.blobId === item.blobId);
  if (existing) return existing.id;
  const blob = await getBlob(item.blobId).catch(() => undefined);
  if (!blob) return null;
  const id = newMediaId(bay.order());
  const der = await idbGet<Derived>('derived', item.blobId).catch(() => undefined);
  const info: MediaInfo = {
    id, name: item.name, kind: item.kind, size: item.size, lastModified: 0, mime: blob.type, duration: 0, width: 0, height: 0, fps: 0,
    hasVideo: item.kind !== 'audio', hasAudio: item.kind !== 'image', rotation: 0, status: 'loading', blobId: item.blobId,
    analysis: der?.analysis ?? undefined, analysisState: der?.analysis ? 'done' : 'pending', shots: der?.shots, poster: der?.poster,
    origin: 'library', libraryId: item.id, tags: item.tags,
  };
  bay.add(info);
  attach(bay, info, blob, !!der?.analysis);
  return id;
}

/** Add a file to a bay that is not the editor (a background job's project). The file is kept in storage. */
export async function addFileToBay(file: File, bay: MediaBay, opts: { tags?: string[] } = {}): Promise<string | null> {
  const kind = detectKind(file);
  if (!kind) return null;
  const key = blobKeyFor(file);
  const dup = bay.order().map(id => bay.media()[id]).find(m => m && m.blobId === key);
  if (dup) return dup.id;
  const id = newMediaId(bay.order());
  const info: MediaInfo = {
    id, name: file.name, kind, size: file.size, lastModified: file.lastModified, mime: file.type, duration: 0, width: 0, height: 0,
    fps: 0, hasVideo: kind !== 'audio', hasAudio: kind !== 'image', rotation: 0, status: 'loading', blobId: key,
    analysisState: kind === 'image' ? 'none' : 'pending', origin: 'file', tags: opts.tags,
  };
  bay.add(info);
  attach(bay, info, file, false);
  pinnedBlobs.add(key);
  const saved = await saveBlob(file, key);
  if (!saved) store.toast(`This browser has no room to keep ${file.name}. The edit can use it now, but it must be re-imported after a reload.`, 'error', 8000);
  return id;
}

function attach(bay: MediaBay, seed: MediaInfo, blob: Blob, haveAnalysis: boolean) {
  const id = seed.id;
  const old = runtime.get(id);
  if (old) {
    if (old.blobId && old.blobId === seed.blobId) { adopt(bay, seed); return; }
    disposeRuntime(old);
  }
  runtime.set(id, {
    file: blob, blobId: seed.blobId, users: new Set([bay.key]), meta: { ...seed }, ready: false,
    url: URL.createObjectURL(blob), input: null, video: null, audio: null, canDecodeVideo: false, canDecodeAudio: false, elementOk: true, thumbs: [], peaks: null, image: null, poster: null,
  });
  probe(id, blob, seed.kind, haveAnalysis).catch(err => {
    console.error(err);
    patchMedia(id, { status: 'error', error: String(err?.message || err) });
    store.toast(`Could not open ${seed.name || 'a file'}: ${err?.message || 'unsupported file'}`, 'error', 6000);
  });
}

function disposeRuntime(rt: MediaRuntime) {
  URL.revokeObjectURL(rt.url);
  try { rt.input?.dispose(); } catch { /* already disposed */ }
  rt.image?.close();
}

/** Probe a stored or picked file without a project (database items, standards). */
export async function probeBlob(blob: Blob, name: string): Promise<Partial<MediaInfo> & { kind: MediaKind }> {
  const kind = detectKind({ name, type: blob.type }) || 'video';
  if (kind === 'image') {
    const bmp = await createImageBitmap(blob);
    const r = { kind, width: bmp.width, height: bmp.height, duration: 0, hasAudio: false, hasVideo: true, fps: 0, poster: posterFrom(bmp, bmp.width, bmp.height) };
    bmp.close();
    return r;
  }
  const input = new Input({ formats: ALL_FORMATS, source: new BlobSource(blob) });
  try {
    const v = kind === 'video' ? await input.getPrimaryVideoTrack() : null;
    const a = await input.getPrimaryAudioTrack();
    const duration = (await input.getDurationFromMetadata().catch(() => null)) ?? (await input.computeDuration());
    const out: Partial<MediaInfo> & { kind: MediaKind } = { kind: v ? 'video' : 'audio', duration, hasVideo: !!v, hasAudio: !!a, width: 0, height: 0, fps: 0 };
    if (v) {
      out.width = await v.getDisplayWidth();
      out.height = await v.getDisplayHeight();
      try { out.fps = Math.round((await v.computeFrameRateMetrics({ targetPacketCount: 120 })).bestGuessFrameRate * 100) / 100; } catch { out.fps = 30; }
      if (await v.canDecode().catch(() => false)) {
        const H = 240, W = Math.max(16, Math.round((H * out.width) / (out.height || 1)));
        const sink = new CanvasSink(v, { width: W, height: H, fit: 'fill' });
        const wc = await sink.getCanvas(Math.min(duration * 0.15, Math.max(0, duration - 0.1)));
        if (wc) out.poster = posterFrom(wc.canvas as CanvasImageSource, W, H);
      }
    }
    return out;
  } finally {
    input.dispose();
  }
}

async function probe(id: string, file: Blob, kind: MediaKind, haveAnalysis: boolean) {
  const rt = runtime.get(id)!;
  const blobId = rt.blobId;
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
    rt.ready = true;
    patchMedia(id, { status: 'ready', width, height, duration: 0, hasAudio: false, hasVideo: true, analysisState: 'none', poster: rt.poster });
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
  // cached waveform and analysis from an earlier session
  const der = blobId ? await idbGet<Derived>('derived', blobId).catch(() => undefined) : undefined;
  if (der?.peaks) rt.peaks = der.peaks;
  const cur = rt.meta;
  const analysisKnown = (haveAnalysis || !!der?.analysis) && !!(cur?.analysis || der?.analysis);
  rt.ready = true;
  patchMedia(id, {
    ...patch, kind: finalKind, status: 'ready',
    analysis: cur?.analysis ?? der?.analysis ?? undefined,
    shots: cur?.shots ?? der?.shots,
    analysisState: patch.hasAudio ? (analysisKnown && rt.peaks ? 'done' : 'pending') : 'none',
  });
  if ([...rt.users].some(k => bays.get(k)?.thumbs)) queue(() => buildThumbs(id));
  else if (!cur?.poster && finalKind === 'video') queue(() => buildPoster(id));
  if (patch.hasAudio && !(analysisKnown && rt.peaks)) queue(() => buildAudio(id));
  // a long video dropped straight into a project is usually a scene pack: find its shots too, so its
  // contact sheets show one frame per shot and Opus gets the shot list (database items have it already)
  if (finalKind === 'video' && (patch.duration || 0) >= 30 && !(cur?.shots ?? der?.shots)) queue(() => buildShots(id));
}

async function buildShots(id: string) {
  const rt = runtime.get(id);
  if (!rt?.file || rt.meta?.shots) return;
  const shots = await detectShots(rt.file).catch(() => [] as [number, number][]);
  if (shots.length < 3) return;
  patchMedia(id, { shots });
  void saveDerived(rt.blobId, { shots });
}

// ---------- background queue (one heavy job at a time keeps the UI responsive) ----------

const jobs: (() => Promise<void>)[] = [];
let busy = false;
export function queue(job: () => Promise<void>) {
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
export async function whenMediaIdle(timeoutMs = 600000, bay: MediaBay = uiBay, signal?: AbortSignal) {
  const t0 = Date.now();
  const live = () => Date.now() - t0 < timeoutMs && !signal?.aborted;
  while ((busy || jobs.length) && live()) await new Promise(r => setTimeout(r, 200));
  while (bay.order().some(id => bay.media()[id]?.status === 'loading') && live()) await new Promise(r => setTimeout(r, 200));
  while ((busy || jobs.length) && live()) await new Promise(r => setTimeout(r, 200));
}

export function posterFrom(img: CanvasImageSource, w: number, h: number): string {
  const c = document.createElement('canvas');
  const s = 240 / Math.max(w, h);
  c.width = Math.max(1, Math.round(w * s));
  c.height = Math.max(1, Math.round(h * s));
  c.getContext('2d')!.drawImage(img, 0, 0, c.width, c.height);
  return c.toDataURL('image/jpeg', 0.75);
}

async function saveDerived(blobId: string | undefined, patch: Derived) {
  if (!blobId) return;
  try {
    const cur = (await idbGet<Derived>('derived', blobId)) || {};
    await idbPut('derived', blobId, { ...cur, ...patch });
  } catch { /* storage unavailable */ }
}

async function buildThumbs(id: string) {
  const rt = runtime.get(id);
  const m = rt?.meta;
  if (!rt || !m || !m.hasVideo || m.kind !== 'video' || rt.thumbs.length) return;
  const count = Math.max(6, Math.min(160, Math.round(m.duration / 1.5)));
  const times = Array.from({ length: count }, (_, i) => ((i + 0.5) / count) * m.duration);
  const frames = await grabFrames(id, times, 120);
  rt.thumbs = frames.filter(f => f.img).map(f => ({ t: f.t, img: f.img!, w: f.w, h: f.h }));
  const posterSrc = rt.thumbs[Math.min(rt.thumbs.length - 1, Math.floor(rt.thumbs.length * 0.15))];
  if (posterSrc) {
    rt.poster = posterFrom(posterSrc.img, posterSrc.w, posterSrc.h);
    patchMedia(id, { poster: rt.poster });
    void saveDerived(m.blobId, { poster: rt.poster });
  }
  bumpRuntime();
}

/** A poster frame only (background jobs do not need filmstrips). */
async function buildPoster(id: string) {
  const rt = runtime.get(id);
  const m = rt?.meta;
  if (!rt || !m || !m.hasVideo || m.kind !== 'video' || m.poster) return;
  const [f] = await grabFrames(id, [Math.min(m.duration * 0.15, Math.max(0, m.duration - 0.1))], 240);
  if (!f?.img) return;
  const poster = posterFrom(f.img, f.w, f.h);
  rt.poster = poster;
  patchMedia(id, { poster });
  void saveDerived(m.blobId, { poster });
}

/**
 * Frames of a media file at the given source times, `height` pixels tall, rotation applied.
 * Decodes with WebCodecs where possible and falls back to seeking a media element.
 */
export async function grabFrames(id: string, times: number[], height: number, signal?: AbortSignal): Promise<{ t: number; img: CanvasImageSource | null; w: number; h: number }[]> {
  const rt = runtime.get(id);
  const m = rt?.meta;
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

/** Decode a file's sound once: waveform peaks plus the analysis Opus reads instead of listening. */
export async function analyseAudioBlob(blob: Blob, onProgress?: (f: number) => void): Promise<{ analysis: AudioAnalysis; peaks: Float32Array } | null> {
  let input: Input | null = null;
  try {
    input = new Input({ formats: ALL_FORMATS, source: new BlobSource(blob) });
    const track = await input.getPrimaryAudioTrack();
    if (track && (await track.canDecode().catch(() => false))) {
      const sr = await track.getSampleRate();
      const dur = (await input.getDurationFromMetadata().catch(() => null)) || 0;
      const an = new AudioAnalyzer(sr);
      const sink = new AudioBufferSink(track);
      let mono = new Float32Array(0);
      for await (const { buffer, timestamp } of sink.buffers()) {
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
        if (dur && onProgress) onProgress(Math.min(1, timestamp / dur));
      }
      return an.finish();
    }
  } catch (e) {
    console.warn('streamed audio decode failed', e);
  } finally {
    input?.dispose();
  }
  if (blob.size < 400 * 1024 * 1024) {
    const AC = window.OfflineAudioContext || (window as any).webkitOfflineAudioContext;
    const ctx = new AC(1, 1, 44100);
    const buf = await ctx.decodeAudioData(await blob.arrayBuffer());
    const an = new AudioAnalyzer(buf.sampleRate);
    const n = buf.length;
    const mono = new Float32Array(n);
    for (let ch = 0; ch < buf.numberOfChannels; ch++) {
      const d = buf.getChannelData(ch);
      for (let i = 0; i < n; i++) mono[i] += d[i] / buf.numberOfChannels;
    }
    for (let i = 0; i < n; i += 65536) an.pushBlock(mono.subarray(i, Math.min(n, i + 65536)));
    return an.finish();
  }
  return null;
}

async function buildAudio(id: string) {
  const rt = runtime.get(id);
  const m = rt?.meta;
  if (!rt || !m || !m.hasAudio) return;
  patchMedia(id, { analysisState: 'running' });
  try {
    const result = await analyseAudioBlob(rt.file);
    if (!result) { patchMedia(id, { analysisState: 'none' }); return; }
    rt.peaks = result.peaks;
    patchMedia(id, { analysis: result.analysis, analysisState: 'done' });
    void saveDerived(m.blobId, { peaks: result.peaks, analysis: result.analysis });
    bumpRuntime();
  } catch (e) {
    console.warn('audio analysis failed', e);
    patchMedia(id, { analysisState: 'error' });
  }
}

/**
 * Find the shots in a video (scene packs): small luma frames 5 times a second, cut where the
 * picture changes sharply against its neighbourhood.
 */
export async function detectShots(blob: Blob, onProgress?: (f: number) => void, signal?: AbortSignal): Promise<[number, number][]> {
  const input = new Input({ formats: ALL_FORMATS, source: new BlobSource(blob) });
  try {
    const v = await input.getPrimaryVideoTrack();
    if (!v || !(await v.canDecode().catch(() => false))) return [];
    const dur = (await input.getDurationFromMetadata().catch(() => null)) ?? (await input.computeDuration());
    const step = 0.2;
    const times = Array.from({ length: Math.max(1, Math.floor(dur / step)) }, (_, i) => i * step);
    const W = 32, H = 18;
    const sink = new CanvasSink(v, { width: W, height: H, fit: 'fill', poolSize: 2 });
    const scratch = document.createElement('canvas');
    scratch.width = W; scratch.height = H;
    const g = scratch.getContext('2d', { willReadFrequently: true })!;
    let prev: Float32Array | null = null, prevZ: Float32Array | null = null;
    const diffs: number[] = [], zdiffs: number[] = [];
    let k = 0;
    for await (const wc of sink.canvasesAtTimestamps(times)) {
      if (signal?.aborted) break;
      k++;
      if (!wc) { diffs.push(0); zdiffs.push(0); continue; }
      g.drawImage(wc.canvas as CanvasImageSource, 0, 0);
      const d = g.getImageData(0, 0, W, H).data;
      const cur = new Float32Array(W * H);
      let mu = 0;
      for (let i = 0; i < W * H; i++) { cur[i] = (d[i * 4] * 0.299 + d[i * 4 + 1] * 0.587 + d[i * 4 + 2] * 0.114) / 255; mu += cur[i]; }
      mu /= cur.length;
      let sd = 0;
      for (let i = 0; i < cur.length; i++) sd += (cur[i] - mu) ** 2;
      sd = Math.sqrt(sd / cur.length) + 0.03;
      // the same picture with its exposure taken out: a cut between two shots of similar tone (black-and-
      // white film, night scenes) still changes the composition
      const z = new Float32Array(cur.length);
      for (let i = 0; i < cur.length; i++) z[i] = (cur[i] - mu) / sd;
      if (prev && prevZ) {
        let s = 0, sz = 0;
        for (let i = 0; i < cur.length; i++) { s += Math.abs(cur[i] - prev[i]); sz += Math.abs(z[i] - prevZ[i]); }
        diffs.push(s / cur.length);
        zdiffs.push(sz / cur.length);
      } else { diffs.push(0); zdiffs.push(0); }
      prev = cur;
      prevZ = z;
      if (onProgress && k % 25 === 0) onProgress(k / times.length);
    }
    const cuts: number[] = [];
    const localMean = (arr: number[], i: number) => {
      const lo = Math.max(1, i - 8), hi = Math.min(arr.length - 1, i + 8);
      let mean = 0, cnt = 0;
      for (let j = lo; j <= hi; j++) if (j !== i) { mean += arr[j]; cnt++; }
      return mean / Math.max(1, cnt);
    };
    for (let i = 1; i < diffs.length; i++) {
      const byLuma = diffs[i] > 0.09 && diffs[i] > localMean(diffs, i) * 3 + 0.02;
      const byShape = zdiffs[i] > 0.5 && zdiffs[i] > localMean(zdiffs, i) * 2.5 + 0.05;
      if ((byLuma || byShape) && (!cuts.length || times[i] - step / 2 - cuts[cuts.length - 1] > 0.4)) cuts.push(times[i] - step / 2);
    }
    const shots: [number, number][] = [];
    let s0 = 0;
    for (const c of cuts) { if (c - s0 > 0.25) shots.push([+s0.toFixed(2), +c.toFixed(2)]); s0 = c; }
    if (dur - s0 > 0.25) shots.push([+s0.toFixed(2), +dur.toFixed(2)]);
    return shots;
  } finally {
    input.dispose();
  }
}

export function removeMedia(id: string) {
  if (store.blocked()) return;
  const rt = runtime.get(id);
  if (rt) {
    rt.users.delete('ui');
    if (!rt.users.size) { disposeRuntime(rt); runtime.delete(id); }
  }
  store.commit(p => { p.clips = p.clips.filter(c => c.media !== id); });
  store.set(s => {
    const media = { ...s.media };
    delete media[id];
    return { media, mediaOrder: s.mediaOrder.filter(x => x !== id) };
  });
}

/** Let go of every file a bay uses; files no other bay uses are closed. */
export function releaseBay(key: string) {
  for (const [id, rt] of runtime) {
    if (!rt.users.delete(key)) continue;
    if (!rt.users.size) { disposeRuntime(rt); runtime.delete(id); }
  }
  if (key !== 'ui') bays.delete(key);
}

/** Drop the editor's files (switching projects); files a background job still uses stay open. */
export function clearRuntime() { releaseBay('ui'); }

export { PEAK_RATE };
