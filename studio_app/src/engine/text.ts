// Renders a text clip into a canvas at output resolution: the v9 NIGHT BLOOM caption construction
// (heavy caps on two lines, a thin dark keyline, a dense soft shadow, a dark-red halo on emphasis words
// and a full-width scrim band), each line shrunk to fit rather than wrapped, and the designed title
// moves of the approved edits: per-word ease-in on sung onsets, the per-letter hero bloom with its
// flare and blood flood, slams, fly-ins, stamps, light-bar sweeps, mask rises, tracking resolves, neon
// flicker, and exits that blow the letters away in the edit's own motif, streak them off or fly them
// past the camera. Constants follow the v9/v10 renderers (px at 1080x1920 scaled to the frame).
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
const ease = (t: number, k: number) => 1 - (1 - clamp(t, 0, 1)) ** k;
const smooth = (t: number) => { const x = clamp(t, 0, 1); return x * x * (3 - 2 * x); };
/** The house ease-in per word: fade + rise + blur-to-sharp over 0.17 s (v9). */
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
  // v9: the ink gap between words is wider than a typed space (0.26 em + 8 px at 1080)
  const gapOf = (px: number) => (s.fit ? 0.26 * px + (8 * frameW) / 1080 : ctx.measureText(' ').width);
  src.split('\n').forEach((para, pi) => {
    let px = Math.max(4, s.size * frameH * (s.lineScales?.[pi] ?? 1));
    const toks = tokens(para);
    const setFont = () => { ctx.font = fontCss(s, px); (ctx as any).letterSpacing = `${(s.tracking * px).toFixed(2)}px`; };
    setFont();
    if (s.fit && toks.length) {
      // a caption line never wraps: it shrinks until it fits (v9: at most six tries)
      for (let k = 0; k < 6; k++) {
        const w = toks.reduce((a, tk, i) => a + ctx.measureText(tk.t).width + (i ? gapOf(px) : 0), 0);
        if (w <= maxW || px <= 6) break;
        px = Math.max(6, (px * maxW) / w - 1);
        setFont();
      }
    }
    const space = gapOf(px);
    let line: Word[] = [];
    let x = 0;
    const flush = () => {
      const w = line.length ? line[line.length - 1].x + line[line.length - 1].w : 0;
      lines.push({ words: line, w, px, y: 0, h: px * s.lineHeight });
      line = []; x = 0;
    };
    if (!toks.length) { flush(); return; }
    for (const tk of toks) {
      const w = ctx.measureText(tk.t).width;
      if (!s.fit && line.length && x + space + w > maxW) flush();
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

/** Per-word or per-letter state. sx/sy stretch about the letter; hot = white-hot amount; flood = 0..1 fill
 * from the bottom with the emphasis colour; flare = light behind the letter; ex = exit progress (particles). */
interface Piece { a: number; dx: number; dy: number; blur: number; scale: number; rot: number; sx: number; sy: number; hot: number; flood: number; flare: number; ex: number; clip: number; chars?: number }
const piece = (): Piece => ({ a: 1, dx: 0, dy: 0, blur: 0, scale: 1, rot: 0, sx: 1, sy: 1, hot: 0, flood: 0, flare: 0, ex: 0, clip: 0 });

function hash(i: number) { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); }

const PER_CHAR_IN = new Set(['letters', 'bloom', 'typewriter', 'track', 'sweep']);
const PER_CHAR_OUT = new Set(['scatter', 'fall', 'blowaway', 'streak']);
const NEON = [0.55, 0.15, 0.7, 0.3, 1, 0.55, 1, 1, 0.85, 1];

/** Animation state for each word (and for each letter when an animation works per letter). */
function animState(c: Clip, L: Layout, lt: number, frameW: number, frameH: number) {
  const an = textAnimOf(c);
  const n = Math.max(1, L.words.length);
  const U = frameH / 1920, UX = frameW / 1080;
  const block = { a: 1, dy: 0, dx: 0, scale: 1, blur: 0, sweep: -1 };
  const words: Piece[] = L.words.map(piece);
  const perChar = PER_CHAR_IN.has(an.in) || PER_CHAR_OUT.has(an.out);
  const chars: Piece[] | null = perChar ? Array.from({ length: L.totalChars }, piece) : null;
  const px = L.pxMax;
  const times = c.words;
  // when each word starts: its sung or spoken onset, else spread over the in-time
  const each = an.in === 'words' ? WORD_EASE : Math.max(0.12, Math.min(0.45, an.inDur * 0.55));
  const spread = n > 1 ? Math.max(0, an.inDur - each) / (n - 1) : 0;
  const onset = (i: number) => (times && times.length ? times[i] ?? times[times.length - 1] + (i - times.length + 1) * 0.12 : i * spread);
  const lastLine = L.lines.length - 1;
  // ---- in ----
  switch (an.in) {
    case 'words': {
      // v9: each word fades in, rises 30 px and blurs to sharp over 0.17 s from its onset (ease 2.4)
      L.words.forEach((_, i) => {
        const v = ease((lt - onset(i)) / WORD_EASE, 2.4);
        words[i].a *= v;
        words[i].dy += (1 - v) * 30 * U;
        words[i].blur += (1 - v) * 6 * U;
      });
      break;
    }
    case 'slam': {
      // v10 HAPPENS: 1.5 -> 1 in 0.16 s, blur to sharp, white-hot cooling over 0.28 s
      L.words.forEach((_, i) => {
        const t = lt - onset(i), v = clamp(t / 0.16, 0, 1), e = out3(v);
        words[i].a *= clamp(v * 1.5, 0, 1);
        words[i].scale *= 1.5 - 0.5 * e;
        words[i].blur += (1 - e) * 6 * U;
        words[i].hot = t < 0 ? 0 : 1 - clamp(t / 0.28, 0, 1);
      });
      break;
    }
    case 'fly': {
      // v4 BULLETS: flies in from the camera, 3.2 -> 1 in 0.15 s, blur 12 -> 0
      L.words.forEach((_, i) => {
        const v = clamp((lt - onset(i)) / 0.15, 0, 1), e = out3(v);
        words[i].a *= e;
        words[i].scale *= 3.2 - 2.2 * e;
        words[i].blur += (1 - e) * 12 * U;
      });
      break;
    }
    case 'stamp': {
      // v7 CASE CLOSED: slams 1.9 -> 1 in 6 frames, then a small bounce
      L.words.forEach((_, i) => {
        const k = (lt - onset(i)) * 60;
        words[i].a *= clamp(k / 2, 0, 1);
        words[i].scale *= k < 6 ? 1.9 - 0.9 * out3(clamp(k / 6, 0, 1)) : 1 + 0.04 * Math.exp(-(k - 6) / 2) * Math.sin(1.8 * (k - 6));
        words[i].blur += (1 - clamp(k / 6, 0, 1)) * 4 * U;
      });
      break;
    }
    case 'mask': {
      // v4 I NEED IT: each word rises out of its own box from below (10 frames, ease 4)
      L.words.forEach((wd, i) => {
        const e = ease((lt - onset(i)) / (10 / 60), 4);
        words[i].dy += (1 - e) * 0.7 * L.lines[wd.line].h;
        words[i].clip = 1;
        words[i].a *= lt >= onset(i) ? 1 : 0;
      });
      break;
    }
    case 'flicker': {
      // v6 neon: each word flickers on with the tube table, then hums
      L.words.forEach((_, i) => {
        const k = Math.floor(((lt - onset(i)) * 60) / 2);
        words[i].a *= k < 0 ? 0 : k >= NEON.length ? 0.92 + 0.08 * hash(Math.floor(lt * 30) + i) : NEON[k];
      });
      break;
    }
    case 'none': break;
    default: {
      if (perChar && chars) {
        let k = 0;
        for (const wd of L.words) {
          for (let ci = 0; ci < wd.chars.length; ci++, k++) {
            const C = chars[wd.chars[ci].index];
            if (an.in === 'bloom') {
              // v9 hero: each letter blooms open from a point on its word's onset + 35 ms per letter
              const t0 = onset(wd.index) + ci * (wd.line === lastLine && lastLine > 0 ? 0.03 : 0.035);
              const v = clamp((lt - t0) / 0.24, 0, 1), ve = out3(v);
              C.a *= ve;
              C.scale *= 0.3 + 0.7 * ve + 0.06 * Math.sin(Math.PI * v);
              C.rot += (C.rot === 0 ? 1 : 1) * (wd.chars[ci].index % 2 ? 1 : -1) * ((24 * Math.PI) / 180) * (1 - ve);
              C.blur += (0.1 + 5 * (1 - ve)) * U;
              C.flare = 0.19 * Math.sin(Math.PI * Math.min(1, v / 0.7)) * (v < 1 ? 1 : 0);
              if (wd.line === lastLine && (lastLine > 0 || wd.emph)) C.flood = ease((lt - t0 - 0.12) / 0.32, 2);
            } else if (an.in === 'typewriter') {
              // characters ease in one after another (fade, 15 px rise, a touch of blur): nothing pops on
              const t0 = (k * Math.max(0.2, an.inDur)) / Math.max(1, L.totalChars);
              const e = out3(clamp((lt - t0) / 0.1, 0, 1));
              C.a *= e;
              C.dy += (1 - e) * 15 * U;
              C.blur += (1 - e) * 3 * U;
            } else if (an.in === 'letters') {
              const nc = Math.max(1, L.totalChars);
              const eachL = Math.max(0.14, Math.min(0.4, an.inDur * 0.5));
              const stagger = nc > 1 ? (an.inDur - eachL) / (nc - 1) : 0;
              const q = clamp((lt - wd.chars[ci].index * stagger) / eachL, 0, 1);
              const qe = out3(q);
              C.a *= clamp(q * 1.6, 0, 1);
              C.dy += (1 - qe) * 0.55 * px;
              C.blur += (1 - qe) * 0.22 * px;
              C.scale *= 1 + 0.5 * (1 - easeOutBack(q));
            } else if (an.in === 'track') {
              // v4 UNDEFEATED: wide tracking resolves to tight with blur to sharp
              const e = out3(clamp(lt / Math.max(0.15, an.inDur), 0, 1));
              const ln = L.lines[wd.line];
              const cxl = (L.blockW - ln.w) / 2 + wd.x + wd.chars[ci].x + wd.chars[ci].w / 2 - L.blockW / 2;
              C.dx += cxl * 0.9 * (1 - e);
              C.blur += (1 - e) * 8 * U;
              C.a *= 0.25 + 0.75 * e;
            } else if (an.in === 'sweep') {
              // v4 light-bar reveal: a soft bar of light crosses and the letters appear behind it
              const bar = -0.15 + 1.3 * io3(clamp(lt / Math.max(0.2, an.inDur), 0, 1));
              block.sweep = bar < 1.15 ? bar : -1;
              const ln = L.lines[wd.line];
              const cx = ((L.blockW - ln.w) / 2 + wd.x + wd.chars[ci].x + wd.chars[ci].w / 2) / L.blockW;
              C.a *= clamp((bar - cx) / (60 * UX / L.blockW) + 0.15, 0, 1);
            }
          }
        }
      } else if (an.inDur > 0 && lt < an.inDur + 1e-6) {
        const p = clamp(lt / an.inDur, 0, 1);
        const e = out3(p);
        switch (an.in) {
          case 'fade': block.a *= io3(p); break;
          case 'rise': block.a *= e; block.dy += (1 - e) * 30 * U * 1.4; block.blur += (1 - e) * 6 * U; break;
          case 'drop': block.a *= e; block.dy -= (1 - e) * 0.45 * px; break;
          case 'pop': block.a *= clamp(p * 3, 0, 1); block.scale *= 0.6 + 0.4 * easeOutBack(p); break;
          case 'blur': block.a *= e; block.blur += (1 - e) * 0.35 * px; break;
          case 'slide_left': block.a *= e; block.dx += (1 - e) * 0.25; break;
          case 'slide_right': block.a *= e; block.dx -= (1 - e) * 0.25; break;
        }
      }
    }
  }
  // ---- out ----
  const left = c.dur - lt;
  if (an.out !== 'none' && an.outDur > 0 && left < an.outDur) {
    const p = clamp(1 - left / an.outDur, 0, 1);
    const e = io3(p);
    const tOut = an.outDur - left;
    switch (an.out) {
      case 'fade': block.a *= 1 - e; break;
      case 'cap': { const k = smooth(p); block.a *= 1 - k; block.blur += 5 * U * k; block.dy -= 14 * U * k; break; }
      case 'sink': block.a *= 1 - e; block.dy += e * 0.4 * px; break;
      case 'lift': block.a *= 1 - e; block.dy -= e * 0.4 * px; break;
      case 'shrink': block.a *= 1 - e; block.scale *= 1 - 0.4 * e; break;
      case 'blur': block.a *= 1 - e; block.blur += e * 0.35 * px; break;
      case 'slide_left': block.a *= 1 - e; block.dx -= e * 0.25; break;
      case 'slide_right': block.a *= 1 - e; block.dx += e * 0.25; break;
      case 'zoom': {
        // v4 knockout exit: the letters fly past the camera
        const k = p ** 2.2;
        block.scale *= 1 + 7 * k;
        block.a *= 1 - smooth((p - 0.55) / 0.45);
        block.blur += 6 * U * k;
        break;
      }
      case 'words': {
        const eachW = Math.max(0.1, Math.min(0.35, an.outDur * 0.5));
        const stagger = n > 1 ? (an.outDur - eachW) / (n - 1) : 0;
        L.words.forEach((_, i) => {
          const q = clamp((tOut - i * stagger) / eachW, 0, 1);
          words[i].a *= 1 - io3(q);
          words[i].dy -= io3(q) * 0.3 * px;
        });
        break;
      }
      case 'blowaway': {
        // v9 hero exit: letters loosen one by one (18 ms apart), lift, twist and blur away throwing particles
        const nc = Math.max(1, L.totalChars);
        const step = Math.min(0.018, Math.max(0, an.outDur - 0.2) / nc);
        const dur = Math.max(0.15, an.outDur - step * nc);
        for (let k = 0; k < nc; k++) {
          const ex = clamp((tOut - k * step) / dur, 0, 1);
          const C = chars![k];
          C.dy -= 40 * U * ex + 30 * U * ex * ex;
          C.scale *= 1 + 0.15 * ex;
          C.rot += (k % 2 ? 1 : -1) * ((30 * Math.PI) / 180) * ex;
          C.blur += 7 * U * ex;
          C.a *= 1 - ex;
          C.ex = ex;
        }
        break;
      }
      case 'streak': {
        // v10/v11 speed exit: letters snatched off to the right, stretched and blurred, 12 ms apart
        const nc = Math.max(1, L.totalChars);
        const step = Math.min(0.012, Math.max(0, an.outDur - 0.12) / nc);
        const dur = Math.max(0.1, an.outDur - step * nc);
        for (let k = 0; k < nc; k++) {
          const ex = clamp((tOut - (nc - 1 - k) * step) / dur, 0, 1);
          const C = chars![k];
          C.dx += 520 * UX * ex ** 1.6;
          C.sx *= 1 + 3 * ex;
          C.blur += 14 * U * ex;
          C.a *= 1 - ex * ex;
        }
        break;
      }
      case 'scatter': {
        // letters burst up and out, staggered, and blur away
        const cx = L.blockW / 2, cy = L.blockH / 2;
        for (const w of L.words) for (const ch of w.chars) {
          const st = chars![ch.index];
          const q = clamp((p * 1.3) - (ch.index / Math.max(1, L.totalChars)) * 0.3, 0, 1);
          const line = L.lines[w.line];
          const lx = (L.blockW - line.w) / 2 + w.x + ch.x + ch.w / 2 - cx, ly = line.y - cy;
          const ang = Math.atan2(ly - 0.8 * px + (hash(ch.index) - 0.5) * px, lx + (hash(ch.index + 9) - 0.5) * px);
          const dist = (0.6 + hash(ch.index + 3)) * 2.4 * px * out3(q);
          st.dx += Math.cos(ang) * dist;
          st.dy += Math.sin(ang) * dist - 0.4 * px * out3(q);
          st.rot += (hash(ch.index + 5) - 0.5) * 2.2 * out3(q);
          st.blur += 0.25 * px * io3(q);
          st.scale *= 1 - 0.35 * io3(q);
          st.a *= 1 - clamp((q - 0.15) / 0.85, 0, 1);
          st.ex = q;
        }
        break;
      }
      case 'fall': {
        // v5 FALLING done right: letters break loose one by one, tumble and drop
        const nc = Math.max(1, L.totalChars);
        for (let k = 0; k < nc; k++) {
          const q = clamp(p * 1.6 - (k / nc) * 0.6, 0, 1);
          const st = chars![k];
          st.dy += q * q * 6 * px;
          st.rot += (hash(k) - 0.5) * 2.4 * q;
          st.sy *= 1 + 0.4 * q;
          st.a *= 1 - clamp((q - 0.55) / 0.45, 0, 1);
          st.blur += 0.1 * px * q;
        }
        break;
      }
    }
  }
  return { words, chars, block, perChar, scatterPad: an.out === 'scatter' || an.out === 'fall' || an.out === 'blowaway' || an.out === 'streak' };
}

const rasters = new Map<string, { canvas: HTMLCanvasElement | OffscreenCanvas; version: string }>();

const hexA = (hex: string, a: number, k = 1) => {
  let h = (hex || '#000').replace('#', '');
  if (h.length === 3) h = h.split('').map(x => x + x).join('');
  const n = parseInt(h, 16) || 0;
  return `rgba(${Math.round(((n >> 16) & 255) * k)},${Math.round(((n >> 8) & 255) * k)},${Math.round((n & 255) * k)},${a.toFixed(3)})`;
};

const MOTIF: Record<string, { col: string; col2: string; shape: 'drop' | 'flake' | 'shard' | 'spark' | 'petal' }> = {
  blood: { col: '#8a0008', col2: '#d4111c', shape: 'drop' },
  ash: { col: '#6f6a64', col2: '#a39d95', shape: 'flake' },
  glass: { col: '#cfe6ff', col2: '#ffffff', shape: 'shard' },
  sparks: { col: '#ff8a2a', col2: '#fff0c0', shape: 'spark' },
  petals: { col: '#f4e9ef', col2: '#ffffff', shape: 'petal' },
};

/**
 * Render a text clip at clip-local time `lt` for an output frame of frameW x frameH.
 * `slot` separates canvases of different consumers (preview, export) that may render concurrently.
 * `mask`: only the letters, solid white (the stencil for footage-in-letters knockout type).
 */
export function renderText(c: Clip, lt: number, frameW: number, frameH: number, slot = 'p', mask = false): TextRaster | null {
  const text = (c.text || '').trim();
  if (!text) return null;
  const s = textStyleOf(c);
  const L = layoutText(text, s, frameW, frameH);
  const st = animState(c, L, lt, frameW, frameH);
  const { words, chars, block } = st;
  if (block.a <= 0.001) return null;
  const px = L.pxMax;
  const U = frameH / 1920;
  const scrim = !mask && s.scrim > 0.01;
  let padX = Math.ceil(px * (st.scatterPad ? 4 : 0.9) + (s.bg ? px * 0.4 : 0));
  let padY = Math.ceil(px * (st.scatterPad ? 4 : 0.9) + (s.bg ? px * 0.4 : 0));
  // the scrim is a full-width band reaching about 230 px past the lines (v9)
  if (scrim) { padX = Math.max(padX, Math.ceil((frameW - L.blockW) / 2)); padY = Math.max(padY, Math.ceil(240 * U)); }
  if (st.scatterPad) padY = Math.max(padY, Math.ceil(420 * U));
  const w = Math.ceil(L.blockW + padX * 2);
  const h = Math.ceil(L.blockH + padY * 2);
  const q = (v: number) => v.toFixed(1);
  const pk = (p: Piece) => `${p.a.toFixed(3)},${q(p.dx)},${q(p.dy)},${q(p.blur)},${p.scale.toFixed(3)},${p.rot.toFixed(3)},${p.sx.toFixed(2)},${p.sy.toFixed(2)},${p.hot.toFixed(2)},${p.flood.toFixed(2)},${p.flare.toFixed(2)},${p.ex.toFixed(2)},${p.chars ?? -1},${p.clip}`;
  // both levels: a word can slam while its letters run an exit
  const stateKey = words.map(pk).join(';') + (chars ? '|' + chars.map(pk).join(';') : '');
  const version = `${text}|${JSON.stringify(s)}|${frameW}x${frameH}|${stateKey}|${q(block.dy)}|${q(block.blur)}|${block.sweep.toFixed(3)}|${mask ? 'm' : ''}`;
  const id = `${slot}:${c.id}${mask ? '#m' : ''}`;
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
  const lineX = (lw: number) => (s.align === 'left' ? padX : s.align === 'right' ? padX + L.blockW - lw : padX + (L.blockW - lw) / 2);
  const lineY = (i: number) => padY + L.lines[i].y + block.dy;
  const maxA = Math.max(0, Math.min(1, Math.max(...(chars || words).map(x => x.a))));

  // v9 scrim: a full-width band, darkest across the lines and fading out ~230 px beyond them
  if (scrim && maxA > 0.003) {
    const y1 = lineY(0), y2 = lineY(L.lines.length - 1);
    const yc = (y1 + y2) / 2, half = (y2 - y1) / 2 + 70 * U, R = half + 160 * U;
    const g = ctx.createLinearGradient(0, yc - R, 0, yc + R);
    for (let k = 0; k <= 8; k++) {
      const u = k / 8, d = Math.abs(u * 2 - 1);
      g.addColorStop(u, `rgba(8,5,6,${(s.scrim * (1 - d) ** 1.5 * maxA).toFixed(4)})`);
    }
    ctx.fillStyle = g;
    ctx.fillRect(0, yc - R, w, R * 2);
  }

  // background box per line
  if (s.bg && !mask) {
    ctx.fillStyle = s.bgColor;
    L.lines.forEach((ln, i) => {
      if (!ln.words.length) return;
      const a = Math.max(...ln.words.map(wd => words[wd.index].a));
      if (a <= 0.01) return;
      const bx = ln.px * 0.32, by = (ln.h - ln.px) / 2 + ln.px * 0.12;
      ctx.globalAlpha = a;
      roundRect(ctx, lineX(ln.w) - bx, lineY(i) - ln.px / 2 - by, ln.w + bx * 2, ln.px + by * 2, ln.px * 0.22);
      ctx.fill();
    });
    ctx.globalAlpha = 1;
  }

  type Pass = 'flare' | 'shadow' | 'glow' | 'stroke' | 'fill' | 'particles';
  const faceOf = (wd: Word, P: Piece) => {
    const base = wd.emph ? s.emphColor : s.color;
    return P.hot > 0.01 ? mixHex(base, '#ffe69e', P.hot) : base;
  };
  const paint = (str: string, x: number, y: number, P: Piece, wd: Word, pass: Pass) => {
    if (pass === 'particles') { if (P.ex > 0.01 && P.ex < 1) particles(ctx, x, y, P.ex, wd.px, hash(str.charCodeAt(0) + x), s.motif || 'ash', U); return; }
    if (P.a <= 0.003) return;
    ctx.font = fontCss(s, wd.px);
    (ctx as any).letterSpacing = `${(s.tracking * wd.px).toFixed(2)}px`;
    ctx.globalAlpha = P.a;
    const blur = P.blur + block.blur;
    ctx.filter = blur > 0.3 ? `blur(${blur.toFixed(1)}px)` : 'none';
    const needT = P.scale !== 1 || P.rot !== 0 || P.sx !== 1 || P.sy !== 1;
    if (needT) { ctx.save(); ctx.translate(x, y); ctx.rotate(P.rot); ctx.scale(P.scale * P.sx, P.scale * P.sy); x = 0; y = 0; }
    const face = faceOf(wd, P);
    if (pass === 'flare') {
      // a soft white flare behind a blooming letter
      if (P.flare > 0.005) {
        const r = wd.px * 0.55;
        const g = ctx.createRadialGradient(x + (ctx.textAlign === 'center' ? 0 : wd.px * 0.3), y, 0, x + (ctx.textAlign === 'center' ? 0 : wd.px * 0.3), y, r);
        g.addColorStop(0, `rgba(255,250,230,${P.flare.toFixed(3)})`);
        g.addColorStop(1, 'rgba(255,250,230,0)');
        ctx.filter = 'none';
        ctx.fillStyle = g;
        ctx.fillRect(x - r * 1.2, y - r * 1.2, r * 2.4 + wd.px * 0.6, r * 2.4);
      }
    } else if (pass === 'shadow') {
      // v9: dense soft drop shadow (sigma 0.13 em, 0.05 em down, 85 %)
      ctx.shadowColor = `rgba(8,5,6,${(0.85 * s.shadow).toFixed(3)})`;
      ctx.shadowBlur = wd.px * 0.26 * Math.max(0.3, s.shadow);
      ctx.shadowOffsetY = wd.px * 0.05;
      ctx.fillStyle = face;
      ctx.fillText(str, x, y);
      ctx.shadowColor = 'transparent'; ctx.shadowBlur = 0; ctx.shadowOffsetY = 0;
    } else if (pass === 'glow') {
      // v9 emphasis: a dark-red halo outside the keyline, not a neon bloom; white-hot words glow warm
      const hotGlow = P.hot > 0.01;
      ctx.shadowColor = hotGlow ? hexA('#ffe69e', 0.45 * P.hot) : hexA(s.emphColor, 0.55 * s.emphGlow, 0.6);
      ctx.shadowBlur = wd.px * (hotGlow ? 0.6 : 0.36);
      ctx.fillStyle = face;
      ctx.fillText(str, x, y);
      ctx.shadowColor = 'transparent'; ctx.shadowBlur = 0;
    } else if (pass === 'stroke') {
      ctx.lineWidth = s.stroke * wd.px * 2;
      ctx.strokeStyle = hexA(s.strokeColor, 0.92);
      ctx.strokeText(str, x, y);
    } else {
      if (mask) ctx.fillStyle = '#ffffff';
      else if (P.flood > 0.001) {
        // the letter fills with the emphasis colour from the bottom, a soft 3 px front
        const top = y - wd.px * 0.42, bot = y + wd.px * 0.42;
        const front = bot - P.flood * 1.08 * (bot - top);
        const g = ctx.createLinearGradient(0, top, 0, bot);
        const f = clamp((front - top) / (bot - top), 0, 1), e = (3 * U) / (bot - top);
        g.addColorStop(0, face);
        g.addColorStop(clamp(f - e, 0, 1), face);
        g.addColorStop(clamp(f + e, 0, 1), s.emphColor === face ? '#dc131c' : s.emphColor);
        g.addColorStop(1, s.emphColor === face ? '#dc131c' : s.emphColor);
        ctx.fillStyle = g;
      } else ctx.fillStyle = face;
      ctx.fillText(str, x, y);
    }
    if (needT) ctx.restore();
  };
  const drawAll = (pass: Pass) => {
    for (const wd of L.words) {
      if (pass === 'glow' && !wd.emph && !(chars ? false : words[wd.index].hot > 0.01)) continue;
      const ln = L.lines[wd.line];
      const wx = lineX(ln.w) + wd.x, wy = lineY(wd.line);
      const WP = words[wd.index];
      if (WP.clip) {
        // mask rise: the word is only visible inside its own line box
        ctx.save();
        ctx.beginPath();
        ctx.rect(wx - wd.px * 0.2, wy - ln.h / 2, wd.w + wd.px * 0.4, ln.h);
        ctx.clip();
      }
      if (chars) {
        for (const ch of wd.chars) {
          const C = chars[ch.index];
          const P: Piece = { ...C, a: C.a * WP.a, dx: C.dx + WP.dx, dy: C.dy + WP.dy, blur: C.blur + WP.blur, scale: C.scale * WP.scale, hot: Math.max(C.hot, WP.hot) };
          const needT = P.scale !== 1 || P.rot !== 0 || P.sx !== 1 || P.sy !== 1 || pass === 'particles' || pass === 'flare';
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
        if (WP.chars !== undefined) { if (WP.chars <= 0) { if (WP.clip) ctx.restore(); continue; } str = Array.from(str).slice(0, WP.chars).join(''); }
        if (WP.scale !== 1 || WP.rot !== 0 || WP.sx !== 1 || WP.sy !== 1) {
          ctx.textAlign = 'center';
          paint(str, wx + wd.w / 2 + WP.dx, wy + WP.dy, WP, wd, pass);
          ctx.textAlign = 'left';
        } else paint(str, wx + WP.dx, wy + WP.dy, WP, wd, pass);
      }
      if (WP.clip) ctx.restore();
    }
  };
  if (!mask) {
    if ((chars || []).some(p => p.flare > 0.005)) drawAll('flare');
    if (s.shadow > 0.01) drawAll('shadow');
    if ((s.emphGlow > 0.01 && L.words.some(x => x.emph)) || words.some(p => p.hot > 0.01)) drawAll('glow');
    if (s.stroke > 0.001) drawAll('stroke');
  }
  drawAll('fill');
  if (!mask && (chars || []).some(p => p.ex > 0.01 && p.ex < 1)) drawAll('particles');
  // the light bar of a sweep reveal
  if (!mask && block.sweep >= -0.1) {
    const bx = padX + block.sweep * L.blockW, bw = 26 * U;
    const g = ctx.createLinearGradient(bx - bw * 2, 0, bx + bw * 2, 0);
    g.addColorStop(0, 'rgba(255,255,255,0)');
    g.addColorStop(0.5, 'rgba(255,255,255,0.75)');
    g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.globalAlpha = 1;
    ctx.filter = 'none';
    ctx.fillStyle = g;
    ctx.fillRect(bx - bw * 2, padY - px * 0.3, bw * 4, L.blockH + px * 0.6);
  }
  ctx.filter = 'none';
  ctx.globalAlpha = 1;
  rasters.set(id, { canvas, version });
  if (rasters.size > 300) {
    const first = rasters.keys().next().value;
    if (first) rasters.delete(first);
  }
  return { canvas, w, h, dx: block.dx, opacity: block.a, scale: block.scale, version };
}

/** Three particles in the edit's motif thrown up and out of a letter as it blows away. */
function particles(ctx: CanvasRenderingContext2D, x: number, y: number, ex: number, size: number, seed: number, motif: string, U: number) {
  const M = MOTIF[motif] || MOTIF.ash;
  ctx.filter = 'none';
  for (let i = 0; i < 3; i++) {
    const r1 = hash(seed * 31 + i * 7), r2 = hash(seed * 17 + i * 13), r3 = hash(seed * 7 + i * 3);
    const ang = ((-149 + 120 * r1) * Math.PI) / 180;
    const dist = 260 * U * ex * (0.6 + 0.8 * r2);
    const px = x + Math.cos(ang) * dist, py = y + Math.sin(ang) * dist - 60 * U * ex;
    const sc = (0.35 + 0.3 * r3) * size * 0.32;
    const flip = Math.cos(8 * ex + r1 * 6);
    ctx.save();
    ctx.globalAlpha = Math.sin(Math.PI * ex);
    ctx.translate(px, py);
    ctx.rotate(((400 * ex + r2 * 180) * Math.PI) / 180);
    ctx.scale(flip, 1);
    ctx.fillStyle = flip < 0 ? M.col : M.col2;
    ctx.beginPath();
    if (M.shape === 'drop') { ctx.arc(0, 0, sc * 0.35, 0, Math.PI * 2); ctx.moveTo(-sc * 0.25, 0); ctx.quadraticCurveTo(0, -sc * 1.1, sc * 0.25, 0); }
    else if (M.shape === 'flake') ctx.rect(-sc * 0.5, -sc * 0.18, sc, sc * 0.36);
    else if (M.shape === 'shard') { ctx.moveTo(-sc * 0.5, sc * 0.3); ctx.lineTo(sc * 0.1, -sc * 0.6); ctx.lineTo(sc * 0.5, sc * 0.25); }
    else if (M.shape === 'spark') { ctx.arc(0, 0, sc * 0.16, 0, Math.PI * 2); }
    else ctx.ellipse(0, 0, sc * 0.5, sc * 0.28, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
}

function mixHex(a: string, b: string, t: number): string {
  const pa = parseInt((a || '#000').replace('#', '').padEnd(6, '0'), 16), pb = parseInt(b.replace('#', ''), 16);
  const ch = (sh: number) => Math.round(((pa >> sh) & 255) * (1 - t) + ((pb >> sh) & 255) * t);
  return `rgb(${ch(16)},${ch(8)},${ch(0)})`;
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
