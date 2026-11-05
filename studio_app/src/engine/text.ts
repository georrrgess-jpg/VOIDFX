// Renders a text clip into a tight canvas at output resolution, with per-word / per-letter animation.
import { Clip, TextStyle } from '../state/types';
import { clamp, easeOutBack, textAnimOf, textStyleOf } from '../state/util';

export interface TextRaster {
  canvas: HTMLCanvasElement | OffscreenCanvas;
  /** Size in output pixels. */
  w: number;
  h: number;
  /** Extra layer offset (frame fractions) and opacity from whole-block animations. */
  dx: number;
  opacity: number;
  scale: number;
  /** Changes whenever the pixels change; used to skip texture uploads. */
  version: string;
}

const io3 = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2);
const out3 = (t: number) => 1 - (1 - t) ** 3;

function fontCss(s: TextStyle, px: number) {
  return `${s.italic ? 'italic ' : ''}${s.weight} ${px.toFixed(2)}px "${s.font}", "Montserrat", "Arial Black", sans-serif`;
}

const fontWaiters = new Map<string, Promise<unknown>>();
/** Ask the browser to load a font face; resolves when ready (or immediately if unsupported). */
export function ensureFont(s: Pick<TextStyle, 'font' | 'weight' | 'italic'>): Promise<unknown> {
  const key = `${s.italic ? 'i' : 'n'}${s.weight}${s.font}`;
  let p = fontWaiters.get(key);
  if (!p) {
    p = (document as any).fonts?.load?.(`${s.italic ? 'italic ' : ''}${s.weight} 40px "${s.font}"`).catch(() => null) ?? Promise.resolve();
    fontWaiters.set(key, p!);
  }
  return p!;
}

interface Word { text: string; x: number; w: number; line: number; index: number; chars: number; charStart: number }
interface Layout { lines: { words: Word[]; w: number }[]; words: Word[]; lineH: number; blockW: number; blockH: number; px: number; totalChars: number }

const layoutCache = new Map<string, Layout>();
let measureCtx: CanvasRenderingContext2D | OffscreenCanvasRenderingContext2D | null = null;

function getMeasure() {
  if (!measureCtx) {
    const c = typeof OffscreenCanvas !== 'undefined' ? new OffscreenCanvas(8, 8) : document.createElement('canvas');
    measureCtx = c.getContext('2d') as any;
  }
  return measureCtx!;
}

function layoutText(text: string, s: TextStyle, frameW: number, frameH: number): Layout {
  const key = JSON.stringify([text, s, frameW, frameH]);
  const hit = layoutCache.get(key);
  if (hit) return hit;
  const px = Math.max(4, s.size * frameH);
  const ctx = getMeasure();
  ctx.font = fontCss(s, px);
  (ctx as any).letterSpacing = `${(s.tracking * px).toFixed(2)}px`;
  const maxW = s.maxWidth * frameW;
  const space = ctx.measureText(' ').width;
  const src = s.uppercase ? text.toUpperCase() : text;
  const lines: { words: Word[]; w: number }[] = [];
  const words: Word[] = [];
  let charCount = 0;
  for (const para of src.split('\n')) {
    const tokens = para.split(/\s+/).filter(Boolean);
    let line: Word[] = [];
    let x = 0;
    const flush = () => { lines.push({ words: line, w: line.length ? line[line.length - 1].x + line[line.length - 1].w : 0 }); line = []; x = 0; };
    if (!tokens.length) { flush(); continue; }
    for (const tk of tokens) {
      const w = ctx.measureText(tk).width;
      if (line.length && x + space + w > maxW) flush();
      if (line.length) x += space;
      const word: Word = { text: tk, x, w, line: lines.length, index: words.length, chars: tk.length, charStart: charCount };
      charCount += tk.length;
      line.push(word);
      words.push(word);
      x += w;
    }
    flush();
  }
  const lineH = px * s.lineHeight;
  const blockW = Math.max(1, ...lines.map(l => l.w));
  const blockH = Math.max(lineH, lines.length * lineH);
  const out = { lines, words, lineH, blockW, blockH, px, totalChars: charCount };
  if (layoutCache.size > 400) layoutCache.clear();
  layoutCache.set(key, out);
  return out;
}

interface WordState { a: number; dy: number; blur: number; scale: number; chars?: number }

/** Animation state of each word at clip-local time lt. */
function wordStates(c: Clip, L: Layout, lt: number): { words: WordState[]; block: { a: number; dy: number; dx: number; scale: number; blur: number } } {
  const an = textAnimOf(c);
  const n = Math.max(1, L.words.length);
  const block = { a: 1, dy: 0, dx: 0, scale: 1, blur: 0 };
  const words: WordState[] = L.words.map(() => ({ a: 1, dy: 0, blur: 0, scale: 1 }));
  const px = L.px;
  // ---- in ----
  if (an.in !== 'none' && an.inDur > 0 && lt < an.inDur) {
    const p = clamp(lt / an.inDur, 0, 1);
    const e = out3(p);
    switch (an.in) {
      case 'fade': block.a *= io3(p); break;
      case 'rise': block.a *= e; block.dy += (1 - e) * 0.45 * px; block.blur += (1 - e) * 0.12 * px; break;
      case 'drop': block.a *= e; block.dy -= (1 - e) * 0.45 * px; break;
      case 'pop': block.a *= clamp(p * 3, 0, 1); block.scale *= 0.6 + 0.4 * easeOutBack(p); break;
      case 'blur': block.a *= e; block.blur += (1 - e) * 0.35 * px; break;
      case 'slide_left': block.a *= e; block.dx += (1 - e) * 0.25; break;
      case 'slide_right': block.a *= e; block.dx -= (1 - e) * 0.25; break;
      case 'typewriter': {
        const shown = Math.floor(p * L.totalChars + 0.0001);
        L.words.forEach((w, i) => { words[i].chars = clamp(shown - w.charStart, 0, w.chars); });
        break;
      }
      case 'words': {
        const span = an.inDur;
        const each = Math.max(0.12, Math.min(0.45, span * 0.55));
        const stagger = n > 1 ? (span - each) / (n - 1) : 0;
        L.words.forEach((_, i) => {
          const q = clamp((lt - i * stagger) / each, 0, 1);
          const qe = out3(q);
          words[i].a *= qe;
          words[i].dy += (1 - qe) * 0.38 * px;
          words[i].blur += (1 - qe) * 0.16 * px;
        });
        break;
      }
    }
  }
  // ---- out ----
  const left = c.dur - lt;
  if (an.out !== 'none' && an.outDur > 0 && left < an.outDur) {
    const p = clamp(1 - left / an.outDur, 0, 1); // 0 → 1 as it leaves
    const e = io3(p);
    switch (an.out) {
      case 'fade': block.a *= 1 - e; break;
      case 'sink': block.a *= 1 - e; block.dy += e * 0.4 * px; break;
      case 'lift': block.a *= 1 - e; block.dy -= e * 0.4 * px; break;
      case 'shrink': block.a *= 1 - e; block.scale *= 1 - 0.4 * e; break;
      case 'blur': block.a *= 1 - e; block.blur += e * 0.35 * px; break;
      case 'slide_left': block.a *= 1 - e; block.dx -= e * 0.25; break;
      case 'slide_right': block.a *= 1 - e; block.dx += e * 0.25; break;
      case 'words': {
        const span = an.outDur;
        const each = Math.max(0.1, Math.min(0.35, span * 0.5));
        const stagger = n > 1 ? (span - each) / (n - 1) : 0;
        const tOut = an.outDur - left; // seconds into the out animation
        L.words.forEach((_, i) => {
          const q = clamp((tOut - i * stagger) / each, 0, 1);
          words[i].a *= 1 - io3(q);
          words[i].dy -= io3(q) * 0.3 * px;
        });
        break;
      }
    }
  }
  return { words, block };
}

const rasters = new Map<string, { canvas: HTMLCanvasElement | OffscreenCanvas; version: string }>();

/**
 * Render a text clip at clip-local time `lt` for an output frame of frameW x frameH.
 * `slot` separates canvases of different consumers (preview, export) that may render concurrently.
 */
export function renderText(c: Clip, lt: number, frameW: number, frameH: number, slot = 'p'): TextRaster | null {
  const text = (c.text || '').trim();
  if (!text) return null;
  const s = textStyleOf(c);
  const L = layoutText(text, s, frameW, frameH);
  const { words, block } = wordStates(c, L, lt);
  if (block.a <= 0.001) return null;
  const px = L.px;
  const pad = Math.ceil(px * 0.9 + (s.bg ? px * 0.4 : 0));
  const w = Math.ceil(L.blockW + pad * 2);
  const h = Math.ceil(L.blockH + pad * 2);
  // version: everything that changes the pixels
  const state = words.map(ws => `${ws.a.toFixed(3)},${ws.dy.toFixed(1)},${ws.blur.toFixed(1)},${ws.chars ?? -1}`).join(';');
  const version = `${text}|${JSON.stringify(s)}|${frameW}x${frameH}|${state}|${block.dy.toFixed(1)}|${block.blur.toFixed(1)}`;
  const id = `${slot}:${c.id}`;
  const prev = rasters.get(id);
  if (prev && prev.version === version) {
    return { canvas: prev.canvas, w, h, dx: block.dx, opacity: block.a, scale: block.scale, version };
  }
  const canvas = prev?.canvas ?? (typeof OffscreenCanvas !== 'undefined' ? new OffscreenCanvas(w, h) : document.createElement('canvas'));
  if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
  const ctx = canvas.getContext('2d') as CanvasRenderingContext2D;
  ctx.clearRect(0, 0, w, h);
  ctx.font = fontCss(s, px);
  (ctx as any).letterSpacing = `${(s.tracking * px).toFixed(2)}px`;
  ctx.textBaseline = 'middle';
  ctx.textAlign = 'left';
  ctx.lineJoin = 'round';
  ctx.miterLimit = 2;
  const lineX = (lw: number) => (s.align === 'left' ? pad : s.align === 'right' ? pad + L.blockW - lw : pad + (L.blockW - lw) / 2);
  const lineY = (i: number) => pad + L.lineH * (i + 0.5) + block.dy;

  // background box per line
  if (s.bg) {
    ctx.fillStyle = s.bgColor;
    const padX = px * 0.32, padY = (L.lineH - px) / 2 + px * 0.12;
    L.lines.forEach((ln, i) => {
      if (!ln.words.length) return;
      const visible = ln.words.some(wd => words[wd.index].a > 0.01 && (words[wd.index].chars ?? 1) > 0);
      if (!visible) return;
      const a = Math.max(...ln.words.map(wd => words[wd.index].a));
      ctx.globalAlpha = a;
      const x = lineX(ln.w) - padX, y = lineY(i) - px / 2 - padY;
      roundRect(ctx, x, y, ln.w + padX * 2, px + padY * 2, px * 0.22);
      ctx.fill();
    });
    ctx.globalAlpha = 1;
  }

  const drawWord = (wd: Word, pass: 'shadow' | 'stroke' | 'fill') => {
    const st = words[wd.index];
    if (st.a <= 0.003) return;
    let str = wd.text;
    if (st.chars !== undefined) { if (st.chars <= 0) return; str = str.slice(0, st.chars); }
    const ln = L.lines[wd.line];
    const x = lineX(ln.w) + wd.x;
    const y = lineY(wd.line) + st.dy;
    ctx.globalAlpha = st.a;
    const blur = st.blur + block.blur;
    ctx.filter = blur > 0.3 ? `blur(${blur.toFixed(1)}px)` : 'none';
    if (pass === 'shadow') {
      ctx.shadowColor = `rgba(0,0,0,${(0.55 * s.shadow).toFixed(3)})`;
      ctx.shadowBlur = px * 0.35 * s.shadow;
      ctx.shadowOffsetY = px * 0.06 * s.shadow;
      ctx.fillStyle = s.color;
      ctx.fillText(str, x, y);
      ctx.shadowColor = 'transparent';
      ctx.shadowBlur = 0;
      ctx.shadowOffsetY = 0;
    } else if (pass === 'stroke') {
      ctx.lineWidth = s.stroke * px * 2;
      ctx.strokeStyle = s.strokeColor;
      ctx.strokeText(str, x, y);
    } else {
      ctx.fillStyle = s.color;
      ctx.fillText(str, x, y);
    }
  };
  if (s.shadow > 0.01) for (const wd of L.words) drawWord(wd, 'shadow');
  if (s.stroke > 0.001) for (const wd of L.words) drawWord(wd, 'stroke');
  for (const wd of L.words) drawWord(wd, 'fill');
  ctx.filter = 'none';
  ctx.globalAlpha = 1;
  rasters.set(id, { canvas, version });
  if (rasters.size > 300) {
    const first = rasters.keys().next().value;
    if (first) rasters.delete(first);
  }
  return { canvas, w, h, dx: block.dx, opacity: block.a, scale: block.scale, version };
}

function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

/** Forget cached rasters for a consumer (e.g. after an export finishes). */
export function dropTextRasters(slot: string) {
  for (const k of [...rasters.keys()]) if (k.startsWith(slot + ':')) rasters.delete(k);
}

