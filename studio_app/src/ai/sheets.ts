// Contact sheets: many labelled frames per image, so Opus sees the footage densely within the
// per-call image limit (each image is downsized to about 1.2 megapixels by the platform).
import { grabFrames } from '../media/library';
import { store } from '../state/store';
import { Project } from '../state/types';
import { renderStills } from '../engine/exporter';

export interface Sheet { blob: Blob; caption: string }

const TARGET_PX = 1_150_000;

function gridFor(n: number, aspect: number) {
  // choose columns so the cells are as large as possible within ~1.15 MP
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

async function compose(cells: { img: CanvasImageSource | null; w: number; h: number; label: string }[], aspect: number): Promise<Blob> {
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
    if (cell.img && cell.w && cell.h) {
      const s = Math.min(cw / cell.w, ch / cell.h);
      const dw = cell.w * s, dh = cell.h * s;
      g.drawImage(cell.img, x + (cw - dw) / 2, y + (ch - dh) / 2, dw, dh);
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

/**
 * Contact sheets for the library's video and image files. `maxImages` caps the image count;
 * `cellsPerSheet` sets the density.
 */
export async function mediaSheets(maxImages: number, cellsPerSheet: number, signal?: AbortSignal, onStep?: (msg: string) => void): Promise<Sheet[]> {
  const s = store.state;
  const vids = s.mediaOrder.map(id => s.media[id]).filter(m => m && m.status === 'ready' && m.kind === 'video' && m.hasVideo);
  const stills = s.mediaOrder.map(id => s.media[id]).filter(m => m && m.status === 'ready' && m.kind === 'image');
  const sheets: Sheet[] = [];
  let budget = maxImages - (stills.length ? Math.ceil(stills.length / cellsPerSheet) : 0);
  if (budget < vids.length) {
    // too many files for one sheet each: share sheets between short files
    budget = Math.max(1, budget);
  }
  const totalDur = vids.reduce((a, m) => a + Math.max(1, m.duration), 0) || 1;
  // sheets per video, proportional to length, at least one when the budget allows
  const alloc = vids.map(m => Math.max(budget >= vids.length ? 1 : 0, Math.round((Math.max(1, m.duration) / totalDur) * budget)));
  let over = alloc.reduce((a, b) => a + b, 0) - budget;
  while (over > 0) {
    const i = alloc.indexOf(Math.max(...alloc));
    if (alloc[i] <= 1) break;
    alloc[i]--; over--;
  }
  // files without their own sheet share pooled sheets
  const pooled: { img: CanvasImageSource | null; w: number; h: number; label: string; aspect: number }[] = [];
  for (let vi = 0; vi < vids.length; vi++) {
    if (signal?.aborted) break;
    const m = vids[vi];
    const nSheets = alloc[vi];
    onStep?.(`Contact sheets: ${m.name}`);
    const aspect = (m.width || 16) / (m.height || 9);
    if (nSheets <= 0) {
      const times = [0.2, 0.5, 0.8].map(f => f * m.duration);
      const frames = await grabFrames(m.id, times, 320, signal);
      frames.forEach(f => pooled.push({ img: f.img, w: f.w, h: f.h, label: `${m.id} ${fmt(f.t)}s`, aspect }));
      continue;
    }
    const n = Math.max(2, Math.min(nSheets * cellsPerSheet, Math.ceil(m.duration / 0.35)));
    const times = Array.from({ length: n }, (_, i) => ((i + 0.5) / n) * m.duration);
    const cellH = aspect < 1 ? 420 : 300;
    const frames = await grabFrames(m.id, times, cellH, signal);
    const per = Math.ceil(n / nSheets);
    for (let k = 0; k < nSheets; k++) {
      const part = frames.slice(k * per, (k + 1) * per);
      if (!part.length) continue;
      const blob = await compose(part.map(f => ({ img: f.img, w: f.w, h: f.h, label: `${m.id} ${fmt(f.t)}s` })), aspect);
      sheets.push({ blob, caption: `contact sheet of ${m.id} ("${m.name}"), ${part.length} frames from ${fmt(part[0].t)}s to ${fmt(part[part.length - 1].t)}s, labelled with source time` });
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
export async function timelineSheets(p: Project, times: number[], perSheet: number, maxImages: number, signal?: AbortSignal): Promise<Sheet[]> {
  const aspect = p.width / p.height;
  const cellH = aspect < 1 ? 420 : 300;
  const list = times.slice(0, perSheet * maxImages);
  const stills = await renderStills(p, list, cellH, signal);
  const sheets: Sheet[] = [];
  for (let i = 0; i < list.length; i += perSheet) {
    const part = list.slice(i, i + perSheet);
    const blob = await compose(part.map((t, k) => {
      const c = stills[i + k];
      return { img: c, w: c?.width || 0, h: c?.height || 0, label: `T ${t.toFixed(2)}s` };
    }), aspect);
    sheets.push({ blob, caption: `frames of the current edit rendered by the studio at timeline times ${part[0].toFixed(2)}s to ${part[part.length - 1].toFixed(2)}s` });
  }
  return sheets;
}
