// Contact sheets: many labelled frames per image, so Opus sees the footage densely within the
// per-call image limit (each image is downsized to about 1.2 megapixels by the platform).
import { ALL_FORMATS, BlobSource, CanvasSink, Input } from 'mediabunny';
import { grabFrames } from '../media/library';
import { MediaInfo, Project } from '../state/types';
import { renderStills } from '../engine/exporter';
import { getBlob } from '../state/storage';
import type { LibraryItem, Standard } from '../state/catalog';

export interface Sheet {
  blob: Blob; caption: string;
  /** Mean brightness (0-1) of each rendered frame on it, with its time. */
  lumas?: [number, number][];
  /** Each rendered frame measured: its time, mean brightness, contrast (sd) and a 16x16 brightness grid. */
  stats?: FrameStat[];
}
export interface FrameStat { t: number; luma: number; sd: number; px: Float32Array }

const TARGET_PX = 1_150_000;

function gridFor(n: number, aspect: number) {
  let best = { cols: 1, rows: n, cw: 0, ch: 0 };
  for (let cols = 1; cols <= n; cols++) {
    const rows = Math.ceil(n / cols);
    const ch = Math.sqrt(TARGET_PX / (cols * rows * aspect));
    const cw = ch * aspect;
    if (cols * cw > 1600 || rows * ch > 1600) continue;
    if (cw > best.cw) best = { cols, rows, cw, ch };
  }
  if (!best.cw) {
    const cols = Math.ceil(Math.sqrt(n)), rows = Math.ceil(n / cols);
    const s = Math.min(1600 / (cols * aspect), 1600 / rows);
    best = { cols, rows, cw: s * aspect, ch: s };
  }
  return { cols: best.cols, rows: best.rows, cw: Math.floor(best.cw), ch: Math.floor(best.ch) };
}

interface Cell { img: CanvasImageSource | null; w: number; h: number; label: string; guide?: number; ruler?: boolean }

async function compose(cells: Cell[], aspect: number): Promise<Blob> {
  const { cols, rows, cw, ch } = gridFor(cells.length, aspect);
  const gap = 4;
  const c = document.createElement('canvas');
  c.width = cols * cw + (cols - 1) * gap;
  c.height = rows * ch + (rows - 1) * gap;
  const g = c.getContext('2d')!;
  g.fillStyle = '#202020';
  g.fillRect(0, 0, c.width, c.height);
  const fs = Math.max(13, Math.round(Math.min(cw, ch) * 0.085));
  cells.forEach((cell, i) => {
    const x = (i % cols) * (cw + gap), y = Math.floor(i / cols) * (ch + gap);
    g.fillStyle = '#000';
    g.fillRect(x, y, cw, ch);
    let dx = x, dy = y, dw = cw, dh = ch;
    if (cell.img && cell.w && cell.h) {
      const s = Math.min(cw / cell.w, ch / cell.h);
      dw = cell.w * s; dh = cell.h * s; dx = x + (cw - dw) / 2; dy = y + (ch - dh) / 2;
      g.drawImage(cell.img, dx, dy, dw, dh);
    }
    if (cell.ruler && cell.img) {
      // a 0..1 ruler on the source picture, so Opus can read the subject's position for "focus"
      g.save();
      const tf = Math.max(9, Math.round(fs * 0.62));
      g.font = `700 ${tf}px "Geist Mono", ui-monospace, Menlo, monospace`;
      g.textBaseline = 'top';
      for (let k = 1; k < 10; k++) {
        const x = dx + (dw * k) / 10, major = k % 5 === 0 || k === 2 || k === 8;
        g.strokeStyle = 'rgba(0,229,255,0.9)';
        g.lineWidth = major ? 2 : 1;
        g.beginPath(); g.moveTo(x, dy); g.lineTo(x, dy + (major ? 12 : 7)); g.stroke();
        if (k % 2 === 0) {
          const t = `.${k}`;
          g.fillStyle = 'rgba(0,0,0,0.7)';
          g.fillRect(x - tf * 0.9, dy + 13, tf * 1.8, tf + 2);
          g.fillStyle = '#00e5ff';
          g.fillText(t, x - g.measureText(t).width / 2, dy + 14);
        }
      }
      for (let k = 1; k < 4; k++) {
        const y = dy + (dh * k) / 4;
        g.strokeStyle = 'rgba(0,229,255,0.9)';
        g.lineWidth = 1.5;
        g.beginPath(); g.moveTo(dx, y); g.lineTo(dx + 8, y); g.stroke();
      }
      g.restore();
    }
    if (cell.guide && cell.img) {
      // the centred crop window of the project frame, for framing landscape footage
      const gw = Math.min(dw, dh * cell.guide);
      g.save();
      g.strokeStyle = 'rgba(255,214,0,0.95)';
      g.lineWidth = 2;
      g.setLineDash([6, 4]);
      g.strokeRect(dx + (dw - gw) / 2 + 1, dy + 1, gw - 2, dh - 2);
      g.restore();
    }
    g.font = `700 ${fs}px "Geist Mono", ui-monospace, Menlo, monospace`;
    const tw = g.measureText(cell.label).width;
    g.fillStyle = 'rgba(0,0,0,0.78)';
    g.fillRect(x, y + ch - fs - 8, Math.min(cw, tw + 12), fs + 8);
    g.fillStyle = '#fff';
    g.textBaseline = 'middle';
    g.fillText(cell.label, x + 6, y + ch - fs / 2 - 4);
  });
  return await new Promise<Blob>((res, rej) => c.toBlob(b => (b ? res(b) : rej(new Error('encode failed'))), 'image/jpeg', 0.84));
}

const fmt = (t: number) => (t < 100 ? t.toFixed(1) : t.toFixed(0));

/** Frame times for a file: shot midpoints for scene packs (spread over the budget), else an even sweep. */
function timesFor(m: MediaInfo, n: number): { t: number; label: string }[] {
  if (m.shots && m.shots.length > 2) {
    const shots = m.shots;
    if (shots.length <= n) {
      // room to spare: long takes get more frames (about one every 2.5 s), so a 30 s shot is not one still
      const extra = shots.map(([a, b]) => Math.max(0, Math.floor((b - a) / 2.5) - 1));
      const spare = n - shots.length, want = extra.reduce((x, y) => x + y, 0);
      const scale = want > spare ? spare / want : 1;
      const out: { t: number; label: string }[] = [];
      shots.forEach(([a, b], i) => {
        const k = 1 + Math.floor(extra[i] * scale);
        for (let j = 0; j < k; j++) {
          const t = a + ((j + 0.5) / k) * (b - a);
          out.push({ t, label: k > 1 ? `${m.id} #${i + 1} ${fmt(a)}-${fmt(b)}s @${fmt(t)}` : `${m.id} #${i + 1} ${fmt(a)}-${fmt(b)}s` });
        }
      });
      return out;
    }
    const pick = Array.from({ length: n }, (_, k) => Math.floor((k * shots.length) / n));
    return pick.map(i => ({ t: (shots[i][0] + shots[i][1]) / 2, label: `${m.id} #${i + 1} ${fmt(shots[i][0])}-${fmt(shots[i][1])}s` }));
  }
  const k = Math.max(2, Math.min(n, Math.ceil(m.duration / 0.35)));
  return Array.from({ length: k }, (_, i) => {
    const t = ((i + 0.5) / k) * m.duration;
    return { t, label: `${m.id} ${fmt(t)}s` };
  });
}

/** What the sheets and prompts read: a project with its media (the editor's or a background job's). */
export interface EditCtx { project: Project; media: Record<string, MediaInfo>; order: string[] }

const sheetCache = new Map<string, Sheet[]>();

/** Contact sheets for the project's video and image files (cached: the footage does not change between rounds). */
export async function mediaSheets(ctx: EditCtx, maxImages: number, cellsPerSheet: number, signal?: AbortSignal, onStep?: (msg: string) => void): Promise<Sheet[]> {
  const key = [ctx.project.width, ctx.project.height, maxImages, cellsPerSheet, ...ctx.order.map(id => { const m = ctx.media[id]; return m ? `${id}:${m.status}:${m.duration.toFixed(2)}:${m.shots?.length ?? 0}` : id; })].join('|');
  const hit = sheetCache.get(key);
  if (hit) return hit;
  const out = await buildMediaSheets(ctx, maxImages, cellsPerSheet, signal, onStep);
  if (!signal?.aborted && out.length) { sheetCache.set(key, out); if (sheetCache.size > 24) sheetCache.delete(sheetCache.keys().next().value!); }
  return out;
}

async function buildMediaSheets(ctx: EditCtx, maxImages: number, cellsPerSheet: number, signal?: AbortSignal, onStep?: (msg: string) => void): Promise<Sheet[]> {
  const proj = ctx.project;
  const frameAspect = proj.width / proj.height;
  const vids = ctx.order.map(id => ctx.media[id]).filter(m => m && m.status === 'ready' && m.kind === 'video' && m.hasVideo);
  const stills = ctx.order.map(id => ctx.media[id]).filter(m => m && m.status === 'ready' && m.kind === 'image');
  const sheets: Sheet[] = [];
  if (maxImages <= 0) return sheets;
  const budget = Math.max(1, maxImages - (stills.length ? Math.ceil(stills.length / cellsPerSheet) : 0));
  const weight = (m: MediaInfo) => Math.max(1, m.shots?.length ? m.shots.length / 6 : m.duration / 8);
  const totalW = vids.reduce((a, m) => a + weight(m), 0) || 1;
  const alloc = vids.map(m => Math.max(budget >= vids.length ? 1 : 0, Math.round((weight(m) / totalW) * budget)));
  let over = alloc.reduce((a, b) => a + b, 0) - budget;
  while (over > 0) {
    const i = alloc.indexOf(Math.max(...alloc));
    if (alloc[i] <= 1) break;
    alloc[i]--; over--;
  }
  // never more sheets than a file has distinct frames to fill (a short clip on four near-empty sheets
  // costs four images and shows nothing more); the freed images go to the files with more shots
  const frames = (m: MediaInfo) => m.shots && m.shots.length > 2 ? m.shots.reduce((a, [s0, s1]) => a + Math.max(1, Math.floor((s1 - s0) / 2.5)), 0) : Math.max(2, Math.ceil(m.duration / 0.35));
  const cap = (m: MediaInfo) => Math.max(1, Math.ceil(frames(m) / cellsPerSheet));
  for (let i = 0; i < vids.length; i++) alloc[i] = Math.min(alloc[i], cap(vids[i]));
  let spare = budget - alloc.reduce((a, b) => a + b, 0);
  while (spare > 0) {
    let best = -1, bw = 0;
    for (let i = 0; i < vids.length; i++) if (alloc[i] < cap(vids[i])) { const w = weight(vids[i]) / (alloc[i] + 1); if (w > bw) { bw = w; best = i; } }
    if (best < 0) break;
    alloc[best]++; spare--;
  }
  const pooled: (Cell & { aspect: number })[] = [];
  for (let vi = 0; vi < vids.length; vi++) {
    if (signal?.aborted) break;
    const m = vids[vi];
    const nSheets = alloc[vi];
    onStep?.(`Contact sheets: ${m.name}`);
    const aspect = (m.width || 16) / (m.height || 9);
    const guide = aspect > frameAspect * 1.15 ? frameAspect : 0;
    if (nSheets <= 0) {
      const ts = timesFor(m, 3);
      const frames = await grabFrames(m.id, ts.map(x => x.t), 320, signal);
      frames.forEach((f, k) => pooled.push({ img: f.img, w: f.w, h: f.h, label: ts[k].label, guide, aspect, ruler: true }));
      continue;
    }
    const ts = timesFor(m, nSheets * cellsPerSheet);
    const cellH = aspect < 1 ? 420 : 300;
    const frames = await grabFrames(m.id, ts.map(x => x.t), cellH, signal);
    const per = Math.ceil(ts.length / nSheets);
    for (let k = 0; k < nSheets; k++) {
      const part = frames.slice(k * per, (k + 1) * per);
      const labels = ts.slice(k * per, (k + 1) * per);
      if (!part.length) continue;
      const blob = await compose(part.map((f, j) => ({ img: f.img, w: f.w, h: f.h, label: labels[j].label, guide, ruler: true })), aspect);
      const shotsNote = m.shots && m.shots.length > 2 ? 'one frame per shot (long takes get several, marked @ with the frame\'s source time), labelled with media id, shot number and its source range' : 'labelled with media id and source time';
      sheets.push({ blob, caption: `contact sheet of ${m.id} ("${m.name}"), ${part.length} frames, ${shotsNote}${guide ? '; the dashed yellow box is the centred 9:16 crop' : ''}; cyan ticks along the top mark x = .1 to .9 and on the left y = .25/.5/.75, for reading each subject's focus point` });
    }
  }
  for (const m of stills) {
    const f = (await grabFrames(m.id, [0], 320))[0];
    pooled.push({ img: f.img, w: f.w, h: f.h, label: `${m.id} still`, aspect: (m.width || 1) / (m.height || 1) });
  }
  for (let i = 0; i < pooled.length; i += cellsPerSheet) {
    const part = pooled.slice(i, i + cellsPerSheet);
    const aspect = part.reduce((a, c) => a + c.aspect, 0) / part.length;
    const blob = await compose(part, aspect);
    const ids = [...new Set(part.map(c => c.label.split(' ')[0]))];
    sheets.push({ blob, caption: `frames of ${ids.join(', ')}, labelled with media id and source time` });
  }
  return sheets.slice(0, maxImages);
}

/** Frames of the edit itself (rendered by the studio), labelled with timeline time. With `ruler`, each
 * frame carries the cyan 0..1 ruler of the output frame, for reading anchor and layer positions. */
export async function timelineSheets(p: Project, media: Record<string, MediaInfo>, times: number[], perSheet: number, maxImages: number, signal?: AbortSignal, cellH = p.width / p.height < 1 ? 420 : 300, labels?: string[], opts: { ruler?: boolean } = {}): Promise<Sheet[]> {
  const aspect = p.width / p.height;
  const list = times.slice(0, perSheet * maxImages);
  const stills = await renderStills(p, list, cellH, signal, media);
  const statOf = (c: HTMLCanvasElement | null, t: number): FrameStat | null => {
    if (!c) return null;
    const s = document.createElement('canvas');
    s.width = 16; s.height = 16;
    const g = s.getContext('2d', { willReadFrequently: true })!;
    g.drawImage(c, 0, 0, 16, 16);
    const d = g.getImageData(0, 0, 16, 16).data;
    const px = new Float32Array(256);
    let sum = 0;
    for (let i = 0; i < 256; i++) { px[i] = (d[i * 4] * 0.2126 + d[i * 4 + 1] * 0.7152 + d[i * 4 + 2] * 0.0722) / 255; sum += px[i]; }
    const luma = sum / 256;
    let v = 0;
    for (let i = 0; i < 256; i++) v += (px[i] - luma) ** 2;
    return { t, luma, sd: Math.sqrt(v / 256), px };
  };
  const stats = stills.map((c, i) => statOf(c, list[i]));
  const sheets: Sheet[] = [];
  for (let i = 0; i < list.length; i += perSheet) {
    const part = list.slice(i, i + perSheet);
    const blob = await compose(part.map((t, k) => {
      const c = stills[i + k];
      return { img: c, w: c?.width || 0, h: c?.height || 0, label: labels?.[i + k] || `T ${t.toFixed(2)}s`, ruler: opts.ruler };
    }), aspect);
    const st = part.map((_, k) => stats[i + k]).filter((x): x is FrameStat => !!x);
    sheets.push({
      blob,
      caption: `frames of the current edit rendered by the studio at timeline times ${part[0].toFixed(2)}s to ${part[part.length - 1].toFixed(2)}s${opts.ruler ? '; cyan ticks along the top mark x = .1 to .9 of the frame and on the left y = .25/.5/.75, for placing anchors and layers' : ''}`,
      lumas: st.map(x => [x.t, x.luma] as [number, number]),
      stats: st,
    });
  }
  return sheets;
}

/** One sheet per reference edit: a frame from the middle of each of its shots. */
export async function standardSheets(standards: Standard[], maxImages: number): Promise<Sheet[]> {
  const out: Sheet[] = [];
  for (const st of standards) {
    if (out.length >= maxImages || !st.blobId) continue;
    const blob = await getBlob(st.blobId).catch(() => undefined);
    if (!blob) continue;
    const input = new Input({ formats: ALL_FORMATS, source: new BlobSource(blob) });
    try {
      const v = await input.getPrimaryVideoTrack();
      if (!v || !(await v.canDecode().catch(() => false))) continue;
      const dur = (await input.getDurationFromMetadata().catch(() => null)) ?? (await input.computeDuration());
      const shots = st.shots?.length ? st.shots : [[0, dur]] as [number, number][];
      const n = Math.min(20, Math.max(shots.length, 12));
      const pick = shots.length >= n ? Array.from({ length: n }, (_, k) => shots[Math.floor((k * shots.length) / n)]) : null;
      const times = pick ? pick.map(([a, b]) => (a + b) / 2) : Array.from({ length: n }, (_, k) => ((k + 0.5) / n) * dur);
      const W = await v.getDisplayWidth(), H = await v.getDisplayHeight();
      const ch = W < H ? 420 : 300;
      const cw = Math.round((ch * W) / H);
      const sink = new CanvasSink(v, { width: cw, height: ch, fit: 'fill' });
      const cells: Cell[] = [];
      let k = 0;
      for await (const wc of sink.canvasesAtTimestamps(times)) {
        const t = times[k++];
        if (!wc) continue;
        const c = document.createElement('canvas');
        c.width = cw; c.height = ch;
        c.getContext('2d')!.drawImage(wc.canvas as CanvasImageSource, 0, 0);
        cells.push({ img: c, w: cw, h: ch, label: `REF ${t.toFixed(1)}s` });
      }
      if (cells.length) out.push({ blob: await compose(cells, W / H), caption: `frames of the owner's reference edit "${st.name}", one per shot, labelled with its time` });
    } catch (e) {
      console.warn('standard sheet failed', e);
    } finally {
      input.dispose();
    }
  }
  return out;
}

/** A mosaic of database items (their posters) for the casting step. */
export async function libraryMosaic(items: LibraryItem[]): Promise<Sheet | null> {
  const withPoster = items.filter(i => i.poster).slice(0, 48);
  if (!withPoster.length) return null;
  const cells: Cell[] = [];
  for (const it of withPoster) {
    const img = new Image();
    img.src = it.poster!;
    await img.decode().catch(() => null);
    cells.push({ img, w: img.naturalWidth || 16, h: img.naturalHeight || 9, label: it.id });
  }
  return { blob: await compose(cells, 16 / 10), caption: 'posters of the database items, labelled with their ids' };
}

/**
 * One custom element, large: six frames through its life (labelled with its progress) and the same
 * moment without it, so Opus judges it the way it would in a chat: rendered, full size, against the shot.
 */
export async function elementSheet(p: Project, media: Record<string, MediaInfo>, clipId: string, signal?: AbortSignal): Promise<Sheet | null> {
  const c = p.clips.find(x => x.id === clipId);
  if (!c) return null;
  const aspect = p.width / p.height;
  const H = aspect < 1 ? 640 : 380;
  const fr = [0.06, 0.22, 0.38, 0.54, 0.7, 0.88];
  const times = fr.map(f => +(c.start + f * c.dur).toFixed(3));
  const withIt = await renderStills(p, times, H, signal, media);
  const q: Project = { ...p, clips: p.clips.filter(x => x.id !== clipId) };
  const without = await renderStills(q, [times[3]], H, signal, media);
  const cells: Cell[] = [
    ...withIt.map((img, k) => ({ img, w: img?.width || 0, h: img?.height || 0, label: `${c.id} ${Math.round(fr[k] * 100)}% ${times[k].toFixed(2)}s`, ruler: k === 0 })),
    { img: without[0], w: without[0]?.width || 0, h: without[0]?.height || 0, label: `without it ${times[3].toFixed(2)}s` },
  ];
  const blob = await compose(cells, aspect);
  return { blob, caption: `${c.kind === 'graphic' ? 'graphic' : 'effect'} ${c.id} (${c.start.toFixed(2)}-${(c.start + c.dur).toFixed(2)} s) rendered large through its life (6 frames, labelled with its progress; the first carries the frame ruler), and the same moment without it` };
}
