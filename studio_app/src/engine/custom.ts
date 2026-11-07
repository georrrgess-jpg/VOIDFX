// Custom layers that Opus (or the owner) writes for one edit: vector graphics (SVG) and GPU effects
// (a GLSL function). Both are checked before they run: SVG is reduced to an allowlist of drawing
// elements with no scripts or outside references, and effect code is limited to a safe subset with
// bounded loops. A layer that still fails is skipped and its error is reported, never fatal.
import { Clip, GraphicReveal, MediaInfo, Project } from '../state/types';
import { clamp, srcAt } from '../state/util';
import { timelineBeats } from './evaluate';
import type { LayerFx } from './transitions';

// ---------- SVG ----------

const SVG_TAGS = new Set([
  'svg', 'g', 'path', 'circle', 'ellipse', 'rect', 'line', 'polyline', 'polygon', 'defs', 'lineargradient', 'radialgradient', 'stop',
  'clippath', 'mask', 'filter', 'fegaussianblur', 'femerge', 'femergenode', 'feoffset', 'fecolormatrix', 'feblend', 'fecomposite', 'feflood', 'use', 'symbol',
]);
const SVG_ATTRS = new Set([
  'id', 'd', 'x', 'y', 'x1', 'y1', 'x2', 'y2', 'cx', 'cy', 'r', 'rx', 'ry', 'fx', 'fy', 'fr', 'width', 'height', 'points', 'viewbox', 'transform',
  'fill', 'stroke', 'stroke-width', 'stroke-linecap', 'stroke-linejoin', 'stroke-miterlimit', 'stroke-dasharray', 'stroke-dashoffset', 'stroke-opacity',
  'fill-opacity', 'fill-rule', 'clip-rule', 'opacity', 'offset', 'stop-color', 'stop-opacity', 'gradientunits', 'gradienttransform', 'spreadmethod',
  'clip-path', 'clippathunits', 'mask', 'maskunits', 'maskcontentunits', 'filter', 'filterunits', 'stddeviation', 'in', 'in2', 'result', 'mode', 'operator', 'values', 'type', 'dx', 'dy',
  'flood-color', 'flood-opacity', 'href', 'xlink:href', 'preserveaspectratio', 'xmlns', 'xmlns:xlink', 'version', 'color', 'style', 'k1', 'k2', 'k3', 'k4',
]);
export const SVG_MAX = 40000;

export interface CleanSvg { svg: string; vbW: number; vbH: number; removed?: string[] }

/** Reduce SVG to drawing elements only. Returns the cleaned markup and its viewBox size, or an error. */
export function sanitizeSvg(raw: unknown): CleanSvg | { error: string } {
  const src = String(raw ?? '').trim();
  if (!src) return { error: 'empty svg' };
  if (src.length > SVG_MAX) return { error: `svg is ${src.length} characters; the limit is ${SVG_MAX}` };
  if (typeof DOMParser === 'undefined') return { error: 'svg cannot be read here' };
  const doc = new DOMParser().parseFromString(src, 'image/svg+xml');
  const root = doc.documentElement;
  if (!root || root.nodeName.toLowerCase() !== 'svg' || doc.getElementsByTagName('parsererror').length) return { error: 'not valid SVG markup (it must be one <svg> element)' };
  const bad = new Set<string>();
  const walk = (el: Element) => {
    for (const child of Array.from(el.children)) {
      const tag = child.nodeName.toLowerCase();
      if (!SVG_TAGS.has(tag)) { bad.add(tag); child.remove(); continue; }
      walk(child);
    }
    for (const a of Array.from(el.attributes)) {
      const n = a.name.toLowerCase();
      const v = a.value;
      const external = /url\(\s*['"]?(?!#)/i.test(v) || /javascript:|data:|expression\(|@import/i.test(v);
      if (!SVG_ATTRS.has(n) || n.startsWith('on') || external || ((n === 'href' || n === 'xlink:href') && !v.startsWith('#'))) el.removeAttribute(a.name);
    }
  };
  walk(root);
  // strip text nodes outside the allowed set (no <text> elements survive the walk)
  let vb = (root.getAttribute('viewBox') || '').trim().split(/[\s,]+/).map(Number);
  if (vb.length !== 4 || vb.some(x => !Number.isFinite(x)) || vb[2] <= 0 || vb[3] <= 0) {
    const w = parseFloat(root.getAttribute('width') || ''), h = parseFloat(root.getAttribute('height') || '');
    if (!(w > 0 && h > 0)) return { error: 'the svg needs a viewBox (e.g. viewBox="0 0 1000 1000")' };
    vb = [0, 0, w, h];
    root.setAttribute('viewBox', vb.join(' '));
  }
  root.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
  root.removeAttribute('width');
  root.removeAttribute('height');
  const svg = new XMLSerializer().serializeToString(root);
  return { svg, vbW: vb[2], vbH: vb[3], removed: bad.size ? [...bad] : undefined };
}

export function svgSize(svg: string): { vbW: number; vbH: number } {
  const m = svg.match(/viewBox="([^"]+)"/);
  const vb = m ? m[1].split(/[\s,]+/).map(Number) : [];
  return vb.length === 4 && vb[2] > 0 && vb[3] > 0 ? { vbW: vb[2], vbH: vb[3] } : { vbW: 1, vbH: 1 };
}

// rasterized graphics, keyed by clip id + content + pixel width
const rasters = new Map<string, { canvas: HTMLCanvasElement; used: number } | 'pending' | 'failed'>();
let readyListeners: (() => void)[] = [];
export function onGraphicReady(fn: () => void) { readyListeners.push(fn); return () => { readyListeners = readyListeners.filter(f => f !== fn); }; }

function hashStr(s: string): string {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
  return (h >>> 0).toString(36);
}

const bucket = (px: number) => Math.max(32, Math.min(4096, Math.ceil(px / 64) * 64));

async function rasterize(svg: string, pxW: number): Promise<HTMLCanvasElement> {
  const { vbW, vbH } = svgSize(svg);
  const w = pxW, h = Math.max(1, Math.round((pxW * vbH) / vbW));
  const sized = svg.replace('<svg', `<svg width="${w}" height="${h}"`);
  const url = URL.createObjectURL(new Blob([sized], { type: 'image/svg+xml' }));
  try {
    const img = new Image();
    img.decoding = 'async';
    img.src = url;
    await img.decode();
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    c.getContext('2d')!.drawImage(img, 0, 0, w, h);
    return c;
  } finally {
    URL.revokeObjectURL(url);
  }
}

function rasterKey(c: Clip, pxW: number) { return `${c.id}:${hashStr(c.svg || '')}:${bucket(pxW)}`; }

/**
 * One raster size per graphic and frame size: big enough for its largest scale (transform and
 * keyframes), so an animated graphic is drawn once and never re-drawn mid-render.
 */
export function rasterWidthFor(c: Clip, frameW: number): number {
  let maxScale = Math.max(1, c.transform?.scale ?? 1);
  for (const k of c.kf?.scale || []) maxScale = Math.max(maxScale, k.v);
  return Math.min(4096, (c.gw ?? 0.6) * frameW * Math.min(maxScale, 4) * (frameW < 900 ? 1.5 : 1.15));
}

/** The graphic as a canvas at about `pxW` pixels wide; null while it is being drawn (a redraw follows). */
export function graphicCanvas(c: Clip, pxW: number): HTMLCanvasElement | null {
  if (!c.svg) return null;
  const key = rasterKey(c, pxW);
  const hit = rasters.get(key);
  if (hit && hit !== 'pending' && hit !== 'failed') { hit.used = Date.now(); return hit.canvas; }
  // while this size is being drawn, any finished size of the same graphic stands in (never a blank frame)
  const prefix = `${c.id}:${hashStr(c.svg || '')}:`;
  let stand: HTMLCanvasElement | null = null;
  for (const [k, v] of rasters) if (k.startsWith(prefix) && typeof v === 'object') { stand = v.canvas; break; }
  if (!hit) {
    rasters.set(key, 'pending');
    rasterize(c.svg, bucket(pxW)).then(canvas => {
      rasters.set(key, { canvas, used: Date.now() });
      if (rasters.size > 80) {
        const old = [...rasters.entries()].filter(([, v]) => typeof v === 'object').sort((a: any, b: any) => a[1].used - b[1].used).slice(0, 20);
        for (const [k] of old) rasters.delete(k);
      }
      for (const f of readyListeners) f();
    }).catch(() => rasters.set(key, 'failed'));
  }
  return stand;
}

/** Draw every graphic of a project at the given frame width before an offline render. */
export async function preloadGraphics(p: Project, frameW: number) {
  const jobs = p.clips.filter(c => c.kind === 'graphic' && c.svg).map(async c => {
    const pxW = rasterWidthFor(c, frameW);
    const key = rasterKey(c, pxW);
    const hit = rasters.get(key);
    if (hit && typeof hit === 'object') return;
    try { rasters.set(key, { canvas: await rasterize(c.svg!, bucket(pxW)), used: Date.now() }); } catch { rasters.set(key, 'failed'); }
  });
  await Promise.all(jobs);
}

const io3 = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2);
const outBack = (t: number) => { const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2; };

/** How a graphic appears and leaves at local time lt. */
export function revealFx(c: Clip, lt: number): Partial<LayerFx> {
  const r: GraphicReveal = { in: 'fade', out: 'fade', inDur: 0.25, outDur: 0.2, ...(c.reveal || {}) } as GraphicReveal;
  const fx: Partial<LayerFx> = {};
  const ein = r.in !== 'none' && r.inDur > 0 && lt < r.inDur ? clamp(lt / r.inDur, 0, 1) : 1;
  const eout = r.out !== 'none' && r.outDur > 0 && lt > c.dur - r.outDur ? clamp((c.dur - lt) / r.outDur, 0, 1) : 1;
  let opacity = 1, scale = 1;
  if (ein < 1) {
    if (r.in === 'fade') opacity *= io3(ein);
    if (r.in === 'pop') { scale *= 0.4 + 0.6 * outBack(ein); opacity *= Math.min(1, ein * 3); }
    if (r.in === 'iris') { fx.mask = 2; fx.maskP = io3(ein) * 1.1; }
    if (r.in === 'wipe') { fx.mask = 1; fx.maskX = 1; fx.maskY = 0; fx.maskP = -0.03 + 1.06 * io3(ein); }
    if (r.in === 'flicker') opacity *= ein > 0.85 || (Math.floor(ein * 14) % 2 === 0 && ein > 0.2) ? 1 : 0.15;
  }
  if (eout < 1) {
    if (r.out === 'fade') opacity *= io3(eout);
    if (r.out === 'shrink') { scale *= 0.3 + 0.7 * io3(eout); opacity *= Math.min(1, eout * 2); }
    if (r.out === 'wipe') { fx.mask = 1; fx.maskX = -1; fx.maskY = 0; fx.maskP = -0.03 + 1.06 * io3(eout); }
    if (r.out === 'flicker') opacity *= eout > 0.8 || Math.floor(eout * 14) % 2 === 1 ? 1 : 0.1;
  }
  fx.opacity = opacity;
  fx.scale = scale;
  return fx;
}

// ---------- effects (GLSL) ----------

export const CODE_MAX = 8000;

/** Static checks before an effect is compiled: the safe subset of GLSL an effect may use. */
export function checkShaderCode(raw: unknown): { code: string; issues: string[] } {
  const code = String(raw ?? '').replace(/\r/g, '').trim();
  const issues: string[] = [];
  if (!code) return { code, issues: ['empty code'] };
  if (code.length > CODE_MAX) issues.push(`code is ${code.length} characters; the limit is ${CODE_MAX}`);
  if (!/vec4\s+effect\s*\(\s*vec2\s+\w+\s*,\s*float\s+\w+\s*,\s*float\s+\w+\s*\)/.test(code)) issues.push('it must define vec4 effect(vec2 uv, float t, float p)');
  const banned: [RegExp, string][] = [
    [/#/, 'no preprocessor lines (#)'], [/\bwhile\b|\bdo\s*\{/, 'no while or do loops (use for loops with a literal bound up to 64)'],
    [/\buniform\b|\blayout\b|\bsampler\w*\b|\bout\s+vec|\bin\s+vec/, 'no uniform, in/out or sampler declarations (the studio provides them)'],
    [/\btexture\w*\s*\(/, 'read the picture with frame(uv), not texture()'], [/\bvoid\s+main\s*\(/, 'do not define main()'], [/\bfxOut\b|gl_Frag/, 'return the colour from effect() instead of writing outputs'],
  ];
  for (const [re, msg] of banned) if (re.test(code)) issues.push(msg);
  const loops = [...code.matchAll(/\bfor\s*\(([^;]*);([^;]*);/g)];
  if (loops.length > 4) issues.push('at most 4 for loops');
  // each loop: its bound and the span of its body, to limit nested work (a GPU that takes too long
  // on one frame is reset by the browser, which would stop the preview or an export)
  const spans: { a: number; b: number; n: number }[] = [];
  for (const m of loops) {
    const init = m[1].trim(), cond = m[2].trim();
    const im = init.match(/^int\s+(\w+)\s*=\s*-?\d+$/);
    const cm = cond.match(/^(\w+)\s*<=?\s*(\d+)$/);
    if (!im || !cm || cm[1] !== im[1] || +cm[2] > 64) { issues.push(`loop "for (${init}; ${cond}; …)" must be "for (int i = 0; i < N; i++)" with a literal N up to 64`); continue; }
    const head = code.indexOf(')', (m.index ?? 0) + m[0].length);
    let i = head + 1;
    while (i < code.length && /\s/.test(code[i])) i++;
    let end = i;
    if (code[i] === '{') { let d = 0; for (; end < code.length; end++) { if (code[end] === '{') d++; else if (code[end] === '}' && --d === 0) break; } }
    else end = code.indexOf(';', i);
    spans.push({ a: m.index ?? 0, b: end, n: +cm[2] });
  }
  for (const s1 of spans) {
    const inner = spans.filter(s2 => s2 !== s1 && s2.a > s1.a && s2.b <= s1.b);
    if (inner.some(s2 => spans.some(s3 => s3 !== s2 && s3 !== s1 && s3.a > s2.a && s3.b <= s2.b))) issues.push('loops may nest at most two deep');
    for (const s2 of inner) if (s1.n * s2.n > 256) issues.push(`nested loops run ${s1.n * s2.n} times per pixel; keep them at 256 or fewer`);
  }
  return { code, issues };
}

/** The helpers, uniforms and coordinate conventions every effect gets (documented for Opus in prompt.ts). */
export const SHADER_PRELUDE = `#version 300 es
precision highp float;
uniform vec2 uRes;
uniform float uT, uP, uDur, uTime, uBeat, uBeatAge, uEnergy, uOpacity, uScale, uRot, uAspect, uSeed;
uniform vec2 uPos;
uniform sampler2D uFrame;
uniform sampler2D uTextMask;
uniform vec4 uTextRect;
out vec4 fxOut;
const float PI = 3.14159265;
float hash11(float x) { return fract(sin(x * 127.1 + uSeed) * 43758.5453); }
float hash21(vec2 p) { p = fract(p * vec2(123.34, 456.21) + uSeed * 0.013); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float noise(vec2 p) { vec2 i = floor(p), f = fract(p); vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash21(i), hash21(i + vec2(1, 0)), u.x), mix(hash21(i + vec2(0, 1)), hash21(i + vec2(1, 1)), u.x), u.y); }
float fbm(vec2 p) { float v = 0.0, a = 0.5; for (int i = 0; i < 5; i++) { v += a * noise(p); p = p * 2.03 + 7.1; a *= 0.5; } return v; }
mat2 rot2(float a) { float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }
vec2 aspectUv(vec2 uv) { return vec2((uv.x - 0.5) * uAspect, uv.y - 0.5); }
vec2 toLocal(vec2 uv) { vec2 q = vec2((uv.x - uPos.x) * uAspect, uv.y - uPos.y); return rot2(-uRot) * q / max(uScale, 1e-3); }
float sdCircle(vec2 p, float r) { return length(p) - r; }
float sdBox(vec2 p, vec2 b) { vec2 d = abs(p) - b; return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0); }
float sdSegment(vec2 p, vec2 a, vec2 b) { vec2 pa = p - a, ba = b - a; float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0); return length(pa - ba * h); }
float glow(float d, float w) { return exp(-max(d, 0.0) / max(w, 1e-4)); }
float boltDist(vec2 p, vec2 a, vec2 b, float seed, float jag) {
  vec2 ab = b - a; float L = max(length(ab), 1e-4); vec2 dir = ab / L; vec2 nrm = vec2(-dir.y, dir.x);
  float s = clamp(dot(p - a, dir) / L, 0.0, 1.0);
  float off = ((fbm(vec2(s * 3.5, seed)) - 0.5) + (noise(vec2(s * 26.0, seed + 7.0)) - 0.5) * 0.2) * jag * L;
  off *= smoothstep(0.0, 0.06, s) * smoothstep(1.0, 0.94, s);
  return length(p - (a + dir * s * L + nrm * off));
}
vec3 frame(vec2 uv) { return texture(uFrame, vec2(clamp(uv.x, 0.0, 1.0), 1.0 - clamp(uv.y, 0.0, 1.0))).rgb; }
float luma(vec3 c) { return dot(c, vec3(0.2126, 0.7152, 0.0722)); }
vec3 rgb2hsv(vec3 c) { vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0); vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
  vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r)); float d = q.x - min(q.w, q.y); return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + 1e-10)), d / (q.x + 1e-10), q.x); }
vec3 hsv2rgb(vec3 c) { vec3 p = abs(fract(c.xxx + vec3(1.0, 2.0 / 3.0, 1.0 / 3.0)) * 6.0 - 3.0); return c.z * mix(vec3(1.0), clamp(p - 1.0, 0.0, 1.0), c.y); }
vec3 saturate3(vec3 c, float s) { return mix(vec3(luma(c)), c, s); }
vec3 sCurve(vec3 c, float k) { vec3 x = clamp(c, 0.0, 1.0); return mix(x, x * x * (3.0 - 2.0 * x), k); }
vec3 splitTone(vec3 c, vec3 shadows, vec3 highs) { float l = luma(c); return c + shadows * (1.0 - l) * (1.0 - l) + highs * l * l; }
vec3 screen3(vec3 a, vec3 b) { return 1.0 - (1.0 - a) * (1.0 - b); }
vec3 overlay3(vec3 a, vec3 b) { return mix(2.0 * a * b, 1.0 - 2.0 * (1.0 - a) * (1.0 - b), step(0.5, a)); }
float filmGrain(vec2 uv, float t) { vec2 px = floor(uv * uRes / 1.6); float f = floor(t * 24.0); return hash21(px + vec2(f * 37.0, f * 11.0)) + hash21(px * 1.37 + vec2(f * 3.1, 7.7)) - 1.0; }
float vignette(vec2 uv, float k) { vec2 q = aspectUv(uv); return 1.0 - k * smoothstep(0.22, 0.78, length(q * vec2(1.3, 1.0))); }
vec3 blurFrame(vec2 uv, float r) { vec3 s = frame(uv); for (int i = 0; i < 16; i++) { float f = (float(i) + 0.5) / 16.0; float a = float(i) * 2.39996;
  s += frame(uv + vec2(cos(a) / uAspect, sin(a)) * sqrt(f) * r); } return s / 17.0; }
vec3 glowFrame(vec2 uv, float r, float th) { vec3 s = vec3(0.0); for (int i = 0; i < 16; i++) { float f = (float(i) + 0.5) / 16.0; float a = float(i) * 2.39996;
  vec3 c = frame(uv + vec2(cos(a) / uAspect, sin(a)) * sqrt(f) * r); s += c * smoothstep(th, th + 0.25, luma(c)) * (1.0 - 0.6 * f); } return s / 11.2; }
vec3 sharpenFrame(vec2 uv, float k) { vec2 px = 1.5 / uRes; vec3 c = frame(uv); if (k <= 0.0) return c;
  vec3 b = (frame(uv + vec2(px.x, 0.0)) + frame(uv - vec2(px.x, 0.0)) + frame(uv + vec2(0.0, px.y)) + frame(uv - vec2(0.0, px.y))) * 0.25; return c + (c - b) * k * 1.6; }
vec3 liftExposure(vec3 c, float e) { return clamp(c * exp2(e * 2.2), 0.0, 1.0); }
vec3 lookFinish(vec3 c, vec2 uv, float t, float grain, float vig, float halo, vec3 haloTint) {
  if (halo > 0.0) c = screen3(c, vec3(luma(glowFrame(uv, 0.02, 0.6))) * haloTint * halo * 1.5);
  c *= vignette(uv, vig);
  c += filmGrain(uv, t) * grain * 0.085 * (0.55 + 0.45 * (1.0 - luma(c)));
  return clamp(c, 0.0, 1.0); }
vec4 voronoi(vec2 x, float seed) { vec2 n = floor(x), f = fract(x); vec2 mg = vec2(0.0), mr = vec2(0.0); float md = 8.0;
  for (int k = 0; k < 9; k++) { vec2 g = vec2(float(k - (k / 3) * 3) - 1.0, float(k / 3) - 1.0); vec2 o = vec2(hash21(n + g + seed), hash21(n + g + seed + 19.7)); vec2 r = g + o - f; float d = dot(r, r); if (d < md) { md = d; mr = r; mg = g; } }
  float me = 8.0; for (int k = 0; k < 9; k++) { vec2 g = mg + vec2(float(k - (k / 3) * 3) - 1.0, float(k / 3) - 1.0); vec2 o = vec2(hash21(n + g + seed), hash21(n + g + seed + 19.7)); vec2 r = g + o - f;
    if (dot(mr - r, mr - r) > 1e-5) me = min(me, dot(0.5 * (mr + r), normalize(r - mr))); }
  return vec4(mr, hash21(n + mg + seed + 3.3), me); }
float textMask(vec2 uv) { vec2 t = (uv * uRes - uTextRect.xy) / max(uTextRect.zw, vec2(1.0));
  if (t.x < 0.0 || t.y < 0.0 || t.x > 1.0 || t.y > 1.0) return 0.0; return texture(uTextMask, t).a; }
float clamp01(float x) { return clamp(x, 0.0, 1.0); }
float stage(float p, float a, float b) { return clamp((p - a) / max(b - a, 1e-4), 0.0, 1.0); }
float envelope(float p, float a, float b, float c, float d) { return stage(p, a, b) * (1.0 - stage(p, c, d)); }
float easeOutCubic(float x) { float y = 1.0 - clamp01(x); return 1.0 - y * y * y; }
float easeInCubic(float x) { x = clamp01(x); return x * x * x; }
float easeInOutCubic(float x) { x = clamp01(x); float y = -2.0 * x + 2.0; return x < 0.5 ? 4.0 * x * x * x : 1.0 - y * y * y * 0.5; }
float easeOutExpo(float x) { x = clamp01(x); return x >= 1.0 ? 1.0 : 1.0 - exp2(-10.0 * x); }
float easeOutBack(float x) { x = clamp01(x); float y = x - 1.0; return 1.0 + 2.70158 * y * y * y + 1.70158 * y * y; }
float easeOutElastic(float x) { x = clamp01(x); if (x <= 0.0 || x >= 1.0) return x; return exp2(-10.0 * x) * sin((x * 10.0 - 0.75) * 2.0943951) + 1.0; }
float fillAA(float d) { return 1.0 - smoothstep(-0.0016, 0.0016, d); }
float strokeAA(float d, float w) { return 1.0 - smoothstep(w - 0.0016, w + 0.0016, abs(d)); }
float sdRoundBox(vec2 p, vec2 b, float r) { return sdBox(p, b - vec2(r)) - r; }
float sdRing(vec2 p, float r, float w) { return abs(length(p) - r) - w; }
float sdTri(vec2 p, float r) { const float k = 1.7320508; p.x = abs(p.x) - r; p.y = p.y + r / k; if (p.x + k * p.y > 0.0) p = vec2(p.x - k * p.y, -k * p.x - p.y) / 2.0; p.x -= clamp(p.x, -2.0 * r, 0.0); return -length(p) * sign(p.y); }
float sdStar(vec2 p, float r, float inner) { float a = atan(p.x, -p.y) + PI; float seg = 2.0 * PI / 5.0; float f = mod(a, seg) - seg * 0.5; float rr = mix(r * inner, r, smoothstep(seg * 0.5, 0.0, abs(f))); return length(p) - rr; }
float smoke(vec2 q, float t) { return fbm(q * 3.0 + vec2(0.0, -t * 0.6) + vec2(fbm(q * 2.0 - t * 0.3), 0.0)); }
vec3 lightSpill(vec2 uv, vec2 pos, vec3 col, float r) { vec2 d = (uv - pos) * vec2(uAspect, 1.0); float f = exp(-dot(d, d) / max(r * r, 1e-5)); vec3 pic = frame(uv); return pic * col * f * 1.6 + col * f * 0.12; }
vec3 refractFrame(vec2 uv, vec2 n, float k) { return frame(uv + n * k); }
vec4 sparks(vec2 q, vec2 o, float t, float seed, float spread, vec3 col) { float a = 0.0;
  for (int i = 0; i < 28; i++) { float fi = float(i); float ang = hash11(fi + seed) * 6.2831853; float sp = (0.25 + hash11(fi * 1.7 + seed) * 0.75) * spread;
    vec2 v = vec2(cos(ang), sin(ang)) * sp; vec2 pos = o + v * t + vec2(0.0, 0.35 * t * t); float life = 1.0 - smoothstep(0.15, 0.55 + 0.35 * hash11(fi + 9.0 + seed), t);
    vec2 dir = normalize(v + vec2(0.0, 0.7 * t) + 1e-4); a += glow(sdSegment(q, pos, pos - dir * (0.012 + 0.03 * sp)), 0.0022) * life; }
  return vec4(mix(col, vec3(1.0), clamp(a - 0.6, 0.0, 1.0)), clamp(a, 0.0, 1.0)); }
float sobel(vec2 uv, float w) { vec2 px = w / uRes; float gx = luma(frame(uv + vec2(px.x, 0.0))) - luma(frame(uv - vec2(px.x, 0.0)));
  float gy = luma(frame(uv + vec2(0.0, px.y))) - luma(frame(uv - vec2(0.0, px.y))); return length(vec2(gx, gy)); }
`;

export function wrapShader(code: string): string {
  return `${SHADER_PRELUDE}
#line 1
${code}
void main() {
  vec2 uv = vec2(gl_FragCoord.x / uRes.x, 1.0 - gl_FragCoord.y / uRes.y);
  vec4 c = clamp(effect(uv, uT, uP), 0.0, 1.0);
  float a = c.a * uOpacity;
  fxOut = vec4(c.rgb * a, a);
}`;
}

export const SHADER_VS = `#version 300 es
in vec2 aPos;
void main() { gl_Position = vec4(aPos * 2.0 - 1.0, 0.0, 1.0); }`;

/** Does the effect read the picture under it (so the frame must be copied first)? */
export const readsFrame = (code: string) => /\b(frame|blurFrame|glowFrame|sharpenFrame|sobel|lookFinish)\s*\(/.test(code);

let checkGl: WebGL2RenderingContext | null | undefined;
const compileMemo = new Map<string, string | null>();
/** Compile an effect in a small offscreen context; null when it compiles, else the compiler's message. */
export function compileError(code: string): string | null {
  const key = hashStr(code);
  if (compileMemo.has(key)) return compileMemo.get(key)!;
  const pre = checkShaderCode(code);
  if (pre.issues.length) { compileMemo.set(key, pre.issues.join('; ')); return pre.issues.join('; '); }
  if (checkGl === undefined) {
    try { checkGl = document.createElement('canvas').getContext('webgl2'); } catch { checkGl = null; }
  }
  const gl = checkGl;
  if (!gl) return null;
  const s = gl.createShader(gl.FRAGMENT_SHADER)!;
  gl.shaderSource(s, wrapShader(code));
  gl.compileShader(s);
  const ok = gl.getShaderParameter(s, gl.COMPILE_STATUS);
  const log = ok ? null : (gl.getShaderInfoLog(s) || 'did not compile').trim().split('\n').slice(0, 6).join(' | ');
  gl.deleteShader(s);
  compileMemo.set(key, log);
  if (compileMemo.size > 200) compileMemo.delete(compileMemo.keys().next().value!);
  return log;
}

/** Effects and graphics in a project that will not render, as review issues. */
export function customIssues(p: Project): string[] {
  const out: string[] = [];
  for (const c of p.clips) {
    if (c.kind === 'shader' && c.code) {
      const e = compileError(c.code);
      if (e) out.push(`effect ${c.id} does not compile and is skipped: ${e}`);
    }
  }
  return out;
}

// ---------- music the effects can react to ----------

/** Beat pulse (1 on a beat, decaying), seconds since the last beat, and music loudness 0..1 at t. */
export function musicAt(p: Project, media: Record<string, MediaInfo>, t: number): { beat: number; beatAge: number; energy: number } {
  const beats = timelineBeats(p, media);
  let k = -1, lo = 0, hi = beats.length - 1;
  while (lo <= hi) { const mid = (lo + hi) >> 1; if (beats[mid].t <= t + 1e-6) { k = mid; lo = mid + 1; } else hi = mid - 1; }
  const beatAge = k >= 0 ? t - beats[k].t : 9;
  let energy = 0;
  for (const c of p.clips) {
    if (c.kind !== 'audio' || !c.media || t < c.start || t > c.start + c.dur) continue;
    const a = media[c.media]?.analysis;
    if (!a?.energy?.length) continue;
    const i = Math.floor(srcAt(c, t - c.start) * a.energyRate);
    energy = Math.max(energy, a.energy[clamp(i, 0, a.energy.length - 1)] || 0);
  }
  return { beat: Math.exp(-beatAge / 0.14), beatAge, energy };
}

/** Footage-in-letters (v4 BAY HARBOR BUTCHER): the letters show the picture brightened, the rest darkens and
 * softens, and a thin light edge outlines each letter. */
export function knockoutCode(dark: number): string {
  const d = (Math.round(Math.min(1, Math.max(0, dark)) * 100) / 100).toFixed(2);
  return `vec4 effect(vec2 uv, float t, float p) {
  float m = textMask(uv);
  vec2 px = 2.0 / uRes;
  float e = clamp(max(max(textMask(uv + vec2(px.x, 0.0)), textMask(uv - vec2(px.x, 0.0))), max(textMask(uv + vec2(0.0, px.y)), textMask(uv - vec2(0.0, px.y)))) - m, 0.0, 1.0);
  vec3 bg = blurFrame(uv, 0.006) * (1.0 - ${d});
  vec3 inside = pow(clamp(frame((uv - 0.5) / 1.04 + 0.5) * 1.6, 0.0, 1.0), vec3(0.85));
  return vec4(mix(bg, inside, m) + vec3(0.92) * e * 0.9, 1.0);
}`;
}
