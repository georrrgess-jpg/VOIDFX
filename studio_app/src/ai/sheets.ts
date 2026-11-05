// Contact sheets: many labelled frames per image, so Opus sees the footage densely within the
// per-call image limit (each image is downsized to about 1.2 megapixels by the platform).
import { ALL_FORMATS, BlobSource, CanvasSink, Input } from 'mediabunny';
import { grabFrames } from '../media/library';
import { MediaInfo, Project } from '../state/types';
import { renderStills } from '../engine/exporter';
import { getBlob } from '../state/storage';
import type { LibraryItem, Standard } from '../state/catalog';

export interface Sheet { blob: Blob; caption: string }

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

interface Cell { img: CanvasImageSource | null; w: number; h: number; label: string; guide?: number }

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
    const pick = shots.length <= n ? shots.map((s, i) => i) : Array.from({ length: n }, (_, k) => Math.floor((k * shots.length) / n));
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

/** Contact sheets for the project's video and image files. */
export async function mediaSheets(ctx: EditCtx, maxImages: number, cellsPerSheet: number, signal?: AbortSignal, onStep?: (msg: string) => void): Promise<Sheet[]> {
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
      frames.forEach((f, k) => pooled.push({ img: f.img, w: f.w, h: f.h, label: ts[k].label, guide, aspect }));
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
      const blob = await compose(part.map((f, j) => ({ img: f.img, w: f.w, h: f.h, label: labels[j].label, guide })), aspect);
      const shotsNote = m.shots && m.shots.length > 2 ? 'one frame per shot, labelled with media id, shot number and its source range' : 'labelled with media id and source time';
      sheets.push({ blob, caption: `contact sheet of ${m.id} ("${m.name}"), ${part.length} frames, ${shotsNote}${guide ? '; the dashed yellow box is the centred 9:16 crop' : ''}` });
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

/** Frames of the edit itself (rendered by the studio), labelled with timeline time. */
export async function timelineSheets(p: Project, media: Record<string, MediaInfo>, times: number[], perSheet: number, maxImages: number, signal?: AbortSignal, cellH = p.width / p.height < 1 ? 420 : 300, labels?: string[]): Promise<Sheet[]> {
  const aspect = p.width / p.height;
  const list = times.slice(0, perSheet * maxImages);
  const stills = await renderStills(p, list, cellH, signal, media);
  const sheets: Sheet[] = [];
  for (let i = 0; i < list.length; i += perSheet) {
    const part = list.slice(i, i + perSheet);
    const blob = await compose(part.map((t, k) => {
      const c = stills[i + k];
      return { img: c, w: c?.width || 0, h: c?.height || 0, label: labels?.[i + k] || `T ${t.toFixed(2)}s` };
    }), aspect);
    sheets.push({ blob, caption: `frames of the current edit rendered by the studio at timeline times ${part[0].toFixed(2)}s to ${part[part.length - 1].toFixed(2)}s` });
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
