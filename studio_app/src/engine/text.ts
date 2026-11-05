// Renders a text clip into a tight canvas at output resolution: per-line sizes, *emphasis* words with
// a glow, a soft scrim, and word-, letter- and block-level animation (the v9 caption construction).
import { Clip, TextStyle } from '../state/types';
import { clamp, easeOutBack, textAnimOf, textStyleOf } from '../state/util';

export interface TextRaster {
  canvas: HTMLCanvasElement | OffscreenCanvas;
  /** Size in output pixels. */
  w: number;
  h: number;
  /** Extra layer offset (frame fractions), opacity and scale from whole-block animations. */
  dx: number;
  opacity: number;
  scale: number;
  /** Changes whenever the pixels change; used to skip texture uploads. */
  version: string;
}

const io3 = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2);
const out3 = (t: number) => 1 - (1 - t) ** 3;
/** The house ease-in per word: fade + rise + blur-to-sharp over about 0.17 s. */
export const WORD_EASE = 0.17;

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

interface Char { ch: string; x: number; w: number; index: number }
interface Word { text: string; x: number; w: number; line: number; index: number; chars: Char[]; emph: boolean; px: number }
interface Line { words: Word[]; w: number; px: number; y: number; h: number }
interface Layout { lines: Line[]; words: Word[]; blockW: number; blockH: number; pxMax: number; totalChars: number }

const layoutCache = new Map<string, Layout>();
let measureCtx: CanvasRenderingContext2D | OffscreenCanvasRenderingContext2D | null = null;
function getMeasure() {
  if (!measureCtx) {
    const c = typeof OffscreenCanvas !== 'undefined' ? new OffscreenCanvas(8, 8) : document.createElement('canvas');
    measureCtx = c.getContext('2d') as any;
  }
  return measureCtx!;
}

/** Split text into tokens, marking *emphasised* spans. */
function tokens(para: string): { t: string; emph: boolean }[] {
  const out: { t: string; emph: boolean }[] = [];
  let on = false;
  for (const raw of para.split(/\s+/).filter(Boolean)) {
    let t = raw;
    let start = false, end = false;
    if (t.startsWith('*')) { start = true; t = t.slice(1); }
    if (t.endsWith('*') && t.length > 0) { end = true; t = t.slice(0, -1); }
    if (start) on = true;
    if (t) out.push({ t, emph: on || (start && end) });
    if (end) on = false;
  }
  return out;
}

function layoutText(text: string, s: TextStyle, frameW: number, frameH: number): Layout {
  const key = JSON.stringify([text, s, frameW, frameH]);
  const hit = layoutCache.get(key);
  if (hit) return hit;
  const ctx = getMeasure();
  const maxW = s.maxWidth * frameW;
  const src = s.uppercase ? text.toUpperCase() : text;
  const lines: Line[] = [];
  const words: Word[] = [];
  let charIndex = 0;
  src.split('\n').forEach((para, pi) => {
    const px = Math.max(4, s.size * frameH * (s.lineScales?.[pi] ?? 1));
    ctx.font = fontCss(s, px);
    (ctx as any).letterSpacing = `${(s.tracking * px).toFixed(2)}px`;
    const space = ctx.measureText(' ').width;
    let line: Word[] = [];
    let x = 0;
    const flush = () => {
      const w = line.length ? line[line.length - 1].x + line[line.length - 1].w : 0;
      lines.push({ words: line, w, px, y: 0, h: px * s.lineHeight });
      line = []; x = 0;
    };
    const toks = tokens(para);
    if (!toks.length) { flush(); return; }
    for (const tk of toks) {
      const w = ctx.measureText(tk.t).width;
      if (line.length && x + space + w > maxW) flush();
      if (line.length) x += space;
      const chars: Char[] = [];
      let cx = 0;
      for (const ch of Array.from(tk.t)) {
        const cw = ctx.measureText(ch).width;
        chars.push({ ch, x: cx, w: cw, index: charIndex++ });
        cx += cw;
      }
      const word: Word = { text: tk.t, x, w, line: lines.length, index: words.length, chars, emph: tk.emph, px };
      line.push(word);
      words.push(word);
      x += w;
    }
    flush();
  });
  let y = 0;
  for (const l of lines) { l.y = y + l.h / 2; y += l.h; }
  const out: Layout = {
    lines, words,
    blockW: Math.max(1, ...lines.map(l => l.w)),
    blockH: Math.max(1, y),
    pxMax: Math.max(4, ...lines.map(l => l.px)),
    totalChars: charIndex,
  };
  if (layoutCache.size > 400) layoutCache.clear();
  layoutCache.set(key, out);
  return out;
}

interface Piece { a: number; dx: number; dy: number; blur: number; scale: number; rot: number; chars?: number }

function hash(i: number) { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); }

/** Animation state for each word (and for each character when an animation works per letter). */
function animState(c: Clip, L: Layout, lt: number) {
  const an = textAnimOf(c);
  const n = Math.max(1, L.words.length);
  const block = { a: 1, dy: 0, dx: 0, scale: 1, blur: 0 };
  const words: Piece[] = L.words.map(() => ({ a: 1, dx: 0, dy: 0, blur: 0, scale: 1, rot: 0 }));
  const perChar = an.in === 'letters' || an.out === 'scatter' || an.out === 'fall';
  const chars: Piece[] | null = perChar ? Array.from({ length: L.totalChars }, () => ({ a: 1, dx: 0, dy: 0, blur: 0, scale: 1, rot: 0 })) : null;
  const px = L.pxMax;
  // ---- in ----
  const times = c.words;
  if (an.in === 'words' && times && times.length) {
    // word-timed: each word eases in on its own onset
    L.words.forEach((_, i) => {
      const t0 = times[i] ?? (times[times.length - 1] + (i - times.length + 1) * 0.12);
      const q = clamp((lt - t0) / WORD_EASE, 0, 1);
      const qe = out3(q);
      words[i].a *= qe;
      words[i].dy += (1 - qe) * 0.38 * px;
      words[i].blur += (1 - qe) * 0.16 * px;
    });
  } else if (an.in !== 'none' && an.inDur > 0 && lt < an.inDur + 1e-6) {
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
        L.words.forEach((w, i) => { words[i].chars = clamp(shown - w.chars[0].index, 0, w.chars.length); });
        break;
      }
      case 'words': {
        const each = Math.max(0.12, Math.min(0.45, an.inDur * 0.55));
        const stagger = n > 1 ? (an.inDur - each) / (n - 1) : 0;
        L.words.forEach((_, i) => {
          const q = clamp((lt - i * stagger) / each, 0, 1);
          const qe = out3(q);
          words[i].a *= qe;
          words[i].dy += (1 - qe) * 0.38 * px;
          words[i].blur += (1 - qe) * 0.16 * px;
        });
        break;
      }
      case 'letters': {
        // hero title: letters build one by one on a shared baseline
        const nc = Math.max(1, L.totalChars);
        const each = Math.max(0.14, Math.min(0.4, an.inDur * 0.5));
        const stagger = nc > 1 ? (an.inDur - each) / (nc - 1) : 0;
        for (let k = 0; k < nc; k++) {
          const q = clamp((lt - k * stagger) / each, 0, 1);
          const qe = out3(q);
          const ch = chars![k];
          ch.a *= clamp(q * 1.6, 0, 1);
          ch.dy += (1 - qe) * 0.55 * px;
          ch.blur += (1 - qe) * 0.22 * px;
          ch.scale *= 1 + 0.5 * (1 - easeOutBack(q));
        }
        break;
      }
    }
  }
  // ---- out ----
  const left = c.dur - lt;
  if (an.out !== 'none' && an.outDur > 0 && left < an.outDur) {
    const p = clamp(1 - left / an.outDur, 0, 1);
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
        const each = Math.max(0.1, Math.min(0.35, an.outDur * 0.5));
        const stagger = n > 1 ? (an.outDur - each) / (n - 1) : 0;
        const tOut = an.outDur - left;
        L.words.forEach((_, i) => {
          const q = clamp((tOut - i * stagger) / each, 0, 1);
          words[i].a *= 1 - io3(q);
          words[i].dy -= io3(q) * 0.3 * px;
        });
        break;
      }
      case 'scatter': {
        // letters burst outward like particles and blur away
        const cx = L.blockW / 2, cy = L.blockH / 2;
        for (const w of L.words) for (const ch of w.chars) {
          const st = chars![ch.index];
          const line = L.lines[w.line];
          const lx = (L.blockW - line.w) / 2 + w.x + ch.x + ch.w / 2 - cx, ly = line.y - cy;
          const ang = Math.atan2(ly + (hash(ch.index) - 0.5) * px, lx + (hash(ch.index + 9) - 0.5) * px);
          const dist = (0.6 + hash(ch.index + 3)) * 2.4 * px * out3(p);
          st.dx += Math.cos(ang) * dist;
          st.dy += Math.sin(ang) * dist - 0.4 * px * out3(p);
          st.rot += (hash(ch.index + 5) - 0.5) * 2.2 * out3(p);
          st.blur += 0.25 * px * e;
          st.scale *= 1 - 0.35 * e;
          st.a *= 1 - clamp((p - 0.15) / 0.85, 0, 1);
        }
        break;
      }
      case 'fall': {
        // letters drop away one after another, as if the floor gave out
        const nc = Math.max(1, L.totalChars);
        for (let k = 0; k < nc; k++) {
          const q = clamp(p * 1.6 - (k / nc) * 0.6, 0, 1);
          const st = chars![k];
          st.dy += q * q * 6 * px;
          st.rot += (hash(k) - 0.5) * 1.2 * q;
          st.a *= 1 - clamp((q - 0.55) / 0.45, 0, 1);
          st.blur += 0.1 * px * q;
        }
        break;
      }
    }
  }
  return { words, chars, block, perChar, scatterPad: an.out === 'scatter' || an.out === 'fall' };
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
  const st = animState(c, L, lt);
  const { words, chars, block } = st;
  if (block.a <= 0.001) return null;
  const px = L.pxMax;
  const pad = Math.ceil(px * (st.scatterPad ? 4 : 0.9) + (s.bg ? px * 0.4 : 0) + (s.scrim > 0 ? px * 1.2 : 0));
  const w = Math.ceil(L.blockW + pad * 2);
  const h = Math.ceil(L.blockH + pad * 2);
  const q = (v: number) => v.toFixed(1);
  const stateKey = (chars || words).map(p => `${p.a.toFixed(3)},${q(p.dx)},${q(p.dy)},${q(p.blur)},${p.scale.toFixed(3)},${p.rot.toFixed(3)}`).join(';')
    + (chars ? '' : words.map(p => p.chars ?? -1).join(','));
  const version = `${text}|${JSON.stringify(s)}|${frameW}x${frameH}|${stateKey}|${q(block.dy)}|${q(block.blur)}`;
  const id = `${slot}:${c.id}`;
  const prev = rasters.get(id);
  if (prev && prev.version === version) return { canvas: prev.canvas, w, h, dx: block.dx, opacity: block.a, scale: block.scale, version };
  const canvas = prev?.canvas ?? (typeof OffscreenCanvas !== 'undefined' ? new OffscreenCanvas(w, h) : document.createElement('canvas'));
  if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
  const ctx = canvas.getContext('2d') as CanvasRenderingContext2D;
  ctx.clearRect(0, 0, w, h);
  ctx.textBaseline = 'middle';
  ctx.textAlign = 'left';
  ctx.lineJoin = 'round';
  ctx.miterLimit = 2;
  const lineX = (lw: number) => (s.align === 'left' ? pad : s.align === 'right' ? pad + L.blockW - lw : pad + (L.blockW - lw) / 2);
  const lineY = (i: number) => pad + L.lines[i].y + block.dy;

  // soft scrim behind the whole block
  if (s.scrim > 0.01) {
    const cx = w / 2, cy = pad + L.blockH / 2 + block.dy;
    const rx = L.blockW / 2 + px * 1.1, ry = L.blockH / 2 + px * 0.9;
    ctx.save();
    ctx.translate(cx, cy);
    ctx.scale(1, ry / rx);
    const g = ctx.createRadialGradient(0, 0, 0, 0, 0, rx);
    g.addColorStop(0, `rgba(0,0,0,${(0.6 * s.scrim).toFixed(3)})`);
    g.addColorStop(0.6, `rgba(0,0,0,${(0.42 * s.scrim).toFixed(3)})`);
    g.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = g;
    ctx.globalAlpha = Math.max(0, Math.min(1, Math.max(...words.map(x => x.a))));
    ctx.fillRect(-rx, -rx, rx * 2, rx * 2);
    ctx.restore();
    ctx.globalAlpha = 1;
  }

  // background box per line
  if (s.bg) {
    ctx.fillStyle = s.bgColor;
    L.lines.forEach((ln, i) => {
      if (!ln.words.length) return;
      const a = Math.max(...ln.words.map(wd => words[wd.index].a));
      if (a <= 0.01) return;
      const padX = ln.px * 0.32, padY = (ln.h - ln.px) / 2 + ln.px * 0.12;
      ctx.globalAlpha = a;
      roundRect(ctx, lineX(ln.w) - padX, lineY(i) - ln.px / 2 - padY, ln.w + padX * 2, ln.px + padY * 2, ln.px * 0.22);
      ctx.fill();
    });
    ctx.globalAlpha = 1;
  }

  type Pass = 'shadow' | 'glow' | 'stroke' | 'fill';
  const paint = (str: string, x: number, y: number, P: Piece, wd: Word, pass: Pass) => {
    if (P.a <= 0.003) return;
    ctx.font = fontCss(s, wd.px);
    (ctx as any).letterSpacing = `${(s.tracking * wd.px).toFixed(2)}px`;
    ctx.globalAlpha = P.a;
    const blur = P.blur + block.blur;
    ctx.filter = blur > 0.3 ? `blur(${blur.toFixed(1)}px)` : 'none';
    const needT = P.scale !== 1 || P.rot !== 0;
    if (needT) { ctx.save(); ctx.translate(x, y); ctx.rotate(P.rot); ctx.scale(P.scale, P.scale); x = 0; y = 0; }
    const color = wd.emph ? s.emphColor : s.color;
    if (pass === 'shadow') {
      ctx.shadowColor = `rgba(0,0,0,${(0.55 * s.shadow).toFixed(3)})`;
      ctx.shadowBlur = wd.px * 0.35 * s.shadow;
      ctx.shadowOffsetY = wd.px * 0.06 * s.shadow;
      ctx.fillStyle = color;
      ctx.fillText(str, x, y);
      ctx.shadowColor = 'transparent'; ctx.shadowBlur = 0; ctx.shadowOffsetY = 0;
    } else if (pass === 'glow') {
      ctx.shadowColor = s.emphColor;
      ctx.shadowBlur = wd.px * 0.55 * s.emphGlow;
      ctx.fillStyle = color;
      ctx.fillText(str, x, y);
      ctx.shadowColor = 'transparent'; ctx.shadowBlur = 0;
    } else if (pass === 'stroke') {
      ctx.lineWidth = s.stroke * wd.px * 2;
      ctx.strokeStyle = s.strokeColor;
      ctx.strokeText(str, x, y);
    } else {
      ctx.fillStyle = color;
      ctx.fillText(str, x, y);
    }
    if (needT) ctx.restore();
  };
  const drawAll = (pass: Pass) => {
    for (const wd of L.words) {
      if (pass === 'glow' && !wd.emph) continue;
      const ln = L.lines[wd.line];
      const wx = lineX(ln.w) + wd.x, wy = lineY(wd.line);
      const WP = words[wd.index];
      if (chars) {
        for (const ch of wd.chars) {
          const C = chars[ch.index];
          const P: Piece = { a: C.a * WP.a, dx: C.dx + WP.dx, dy: C.dy + WP.dy, blur: C.blur + WP.blur, scale: C.scale, rot: C.rot };
          const needT = P.scale !== 1 || P.rot !== 0;
          const x = wx + ch.x + P.dx + (needT ? ch.w / 2 : 0);
          const y = wy + P.dy;
          if (needT) {
            // draw centred on the letter so it scales and spins in place
            ctx.textAlign = 'center';
            paint(ch.ch, x, y, P, wd, pass);
            ctx.textAlign = 'left';
          } else paint(ch.ch, x, y, P, wd, pass);
        }
      } else {
        let str = wd.text;
        if (WP.chars !== undefined) { if (WP.chars <= 0) continue; str = Array.from(str).slice(0, WP.chars).join(''); }
        paint(str, wx + WP.dx, wy + WP.dy, WP, wd, pass);
      }
    }
  };
  if (s.shadow > 0.01) drawAll('shadow');
  if (s.emphGlow > 0.01 && L.words.some(x => x.emph)) drawAll('glow');
  if (s.stroke > 0.001) drawAll('stroke');
  drawAll('fill');
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

/** Text block height as a fraction of frame height (for the text-band check). */
export function textBlockHeight(c: Clip, frameW: number, frameH: number): number {
  const L = layoutText((c.text || '').trim() || ' ', textStyleOf(c), frameW, frameH);
  return L.blockH / frameH;
}
