// WebGL2 compositor. Draws media, image, text and logo layers with transform, colour, blur and
// transition effects. One instance drives the preview canvas; export, review and previews use their own.
import { BlendMode, ColorAdjust, Transform } from '../state/types';
import { logo } from './logo';
import { readsFrame, SHADER_VS, wrapShader } from './custom';
import { LayerFx } from './transitions';

const VS = `#version 300 es
in vec2 aPos;
uniform vec2 uCenter; uniform vec2 uSize; uniform float uRot; uniform vec2 uRes; uniform int uSrcRot;
out vec2 vUv;
void main() {
  vec2 p = (aPos - 0.5) * uSize;
  float c = cos(uRot), s = sin(uRot);
  p = vec2(c * p.x - s * p.y, s * p.x + c * p.y) + uCenter;
  vec2 cl = (p / uRes) * 2.0 - 1.0;
  gl_Position = vec4(cl.x, -cl.y, 0.0, 1.0);
  vec2 uv = aPos;
  if (uSrcRot == 1) uv = vec2(uv.y, 1.0 - uv.x);
  else if (uSrcRot == 2) uv = vec2(1.0 - uv.x, 1.0 - uv.y);
  else if (uSrcRot == 3) uv = vec2(1.0 - uv.y, uv.x);
  vUv = uv;
}`;

const FS = `#version 300 es
precision highp float;
in vec2 vUv;
uniform sampler2D uTex;
uniform sampler2D uMaskTex;
uniform vec2 uTexel; uniform vec2 uRes;
uniform float uOpacity;
uniform float uBright, uContrast, uSat, uTemp, uTint, uHue, uVignette;
uniform float uAutoExp;
uniform float uBlur; uniform vec2 uDir; uniform float uRadial; uniform float uChroma;
uniform int uMask; uniform vec2 uMaskDir; uniform float uMaskP; uniform float uMaskSoft;
uniform vec2 uMaskCenter; uniform vec2 uMaskSize;
uniform vec3 uEdge; uniform float uEdgeW;
uniform vec3 uFlashColor; uniform float uFlash; uniform float uInvert;
uniform float uLeak; uniform float uLeakPos; uniform vec3 uLeakColor;
uniform int uPremul; uniform int uGrade;
uniform int uWarp; uniform float uWarpP; uniform float uWarpA; uniform vec2 uWarpC; uniform vec4 uRect; uniform int uSrcRotF;
uniform vec2 uRadC; uniform vec2 uIris; uniform float uExpo;
out vec4 outColor;

vec4 tap(vec2 uv) { return texture(uTex, clamp(uv, vec2(0.0), vec2(1.0))); }
vec3 hueShift(vec3 col, float h) {
  const vec3 k = vec3(0.57735);
  float c = cos(h);
  return col * c + cross(k, col) * sin(h) + k * dot(k, col) * (1.0 - c);
}
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p) {
  vec2 i = floor(p), f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}
float fbm(vec2 p) { float v = 0.0, a = 0.5; for (int i = 0; i < 5; i++) { v += a * vnoise(p); p *= 2.03; a *= 0.5; } return v; }
mat2 rot(float a) { float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }
// nearest cell of a jittered grid: offset to its site (xy), its random id (z), distance to its edge (w)
vec4 cells(vec2 x) {
  vec2 n = floor(x), f = fract(x); vec2 mg = vec2(0.0), mr = vec2(0.0); float md = 8.0;
  for (int k = 0; k < 9; k++) { vec2 g = vec2(float(k - (k / 3) * 3) - 1.0, float(k / 3) - 1.0); vec2 o = vec2(hash(n + g), hash(n + g + 19.7)) * 0.9 + 0.05; vec2 r = g + o - f; float d = dot(r, r); if (d < md) { md = d; mr = r; mg = g; } }
  float me = 8.0;
  for (int k = 0; k < 9; k++) { vec2 g = mg + vec2(float(k - (k / 3) * 3) - 1.0, float(k / 3) - 1.0); vec2 o = vec2(hash(n + g), hash(n + g + 19.7)) * 0.9 + 0.05; vec2 r = g + o - f;
    if (dot(mr - r, mr - r) > 1e-5) me = min(me, dot(0.5 * (mr + r), normalize(r - mr))); }
  return vec4(mr, hash(n + mg + 3.3), me);
}

void main() {
  vec4 col;
  vec2 uv0 = vUv;
  float inside = 1.0, shade = 1.0, glint = 0.0;
  if (uWarp > 0) {
    // screen-space warps: the quad covers the frame; map each pixel back onto the layer's own rectangle
    vec2 px = vec2(gl_FragCoord.x, uRes.y - gl_FragCoord.y);
    vec2 C = uWarpC * uRes;
    if (uWarp == 1 || uWarp == 2) {
      // the layer as a plane turning about a vertical (1) or horizontal (2) axis at depth uWarpA x its size
      bool vert = uWarp == 2;
      vec2 rel = px - uRect.xy;
      float xs = vert ? rel.y : rel.x, ys = vert ? rel.x : rel.y, size = vert ? uRect.w : uRect.z;
      float D = 2.2 * uRes.y, zp = uWarpA * size, th = uWarpP;
      float den = D * cos(th) - xs * sin(th);
      if (den <= 1.0) inside = 0.0;
      float u = (xs * (D + zp * (1.0 - cos(th))) - zp * D * sin(th)) / max(den, 1.0);
      float Z = zp + u * sin(th) - zp * cos(th);
      float v = ys * (D + Z) / D;
      px = uRect.xy + (vert ? vec2(v, u) : vec2(u, v));
      shade = 0.5 + 0.5 * cos(th);
    } else if (uWarp == 3) {
      // shatter: radial fracture round the impact C (fine near it, long wedges further out); cracks spread
      // from C first (uWarpA), then the shards fly outward and toward the lens over the next shot
      vec2 q = (px - C) / uRes.y;
      float pe = uWarpP, s = 1.0 + pe * pe * 5.0;
      vec2 qs = q / s;
      float r = max(length(qs), 1e-3);
      vec2 cs = vec2(log(r) * 2.4, atan(qs.y, qs.x) * 2.4);
      vec4 v = cells(cs);
      vec2 sc = cs + v.xy;
      vec2 site = vec2(cos(sc.y / 2.4), sin(sc.y / 2.4)) * exp(sc.x / 2.4);
      vec2 loc = rot((v.z - 0.5) * 3.0 * pe * pe) * (qs - site) / (1.0 + pe * (0.4 + v.z));
      px = C + (site + loc) * uRes.y;
      float em = v.w * r / 2.4;
      float broken = step(0.001, pe);
      inside = mix(1.0, smoothstep(0.0, 0.002, em - pe * 0.012) * (1.0 - smoothstep(0.55, 1.0, pe + v.z * 0.35)), broken);
      shade = mix(1.0, 0.8 + 0.4 * v.z, smoothstep(0.0, 0.15, pe));
      glint = (1.0 - smoothstep(0.0, 0.0022, em)) * step(r, uWarpA * 1.4) * min(1.0, uWarpA * 3.0);
    } else if (uWarp == 4) {
      // slices: vertical strips slide away in alternating directions, staggered (uWarpA strips; negative reverses)
      float N = abs(uWarpA), i = floor(px.x / uRes.x * N);
      float delay = mod(i, 2.0) == 0.0 ? i / N * 0.35 : (N - 1.0 - i) / N * 0.35;
      float pe = clamp((uWarpP - delay) / 0.65, 0.0, 1.0);
      pe = pe * pe * (3.0 - 2.0 * pe);
      px.y -= (mod(i, 2.0) == 0.0 ? 1.0 : -1.0) * sign(uWarpA) * pe * uRes.y * 1.05;
    } else if (uWarp == 5) {
      vec2 d = px - C; float r = length(d) / uRes.y;
      px += normalize(d + 1e-4) * sin(r * 60.0 - uWarpP * 18.0) * uWarpA * 0.03 * exp(-r * 2.0) * uRes.y;
    } else if (uWarp == 6) {
      vec2 d = px - C; float r = length(d) / uRes.y;
      px = C + rot(uWarpA * (1.0 - smoothstep(0.0, 0.7, r))) * d;
    } else if (uWarp == 7) {
      float b = max(1.0, uWarpA);
      px = (floor(px / b) + 0.5) * b;
    } else if (uWarp == 8) {
      vec2 d = px - C; float r = length(d), seg = 6.2832 / 6.0;
      float af = abs(mod(atan(d.y, d.x) + uWarpP, seg) - seg * 0.5);
      px = mix(px, C + vec2(cos(af), sin(af)) * r, uWarpA);
    } else if (uWarp == 9) {
      float k = uWarpA * px.y / uRes.y;
      px.x += sin(px.y * 0.025 + uWarpP * 20.0) * 18.0 * k + (vnoise(px * 0.02 + vec2(0.0, uWarpP * 8.0)) - 0.5) * 30.0 * k;
    } else if (uWarp == 10) {
      vec2 blk = floor(px / vec2(uRes.x / 8.0, uRes.y / 14.0));
      float f = floor(uWarpP * 18.0), on = step(0.7, hash(blk + f)) * uWarpA;
      px += (vec2(hash(blk + f + 1.0), hash(blk + f + 2.0)) - 0.5) * vec2(uRes.x * 0.15, uRes.y * 0.05) * on;
    }
    vec2 l = (px - uRect.xy) / uRect.zw + 0.5;
    // geometric moves cut off at the picture's edge; distortions keep their edge pixels
    if (uWarp <= 4) { if (l.x < 0.0 || l.y < 0.0 || l.x > 1.0 || l.y > 1.0) inside = 0.0; } else l = clamp(l, 0.0, 1.0);
    uv0 = l;
    if (uSrcRotF == 1) uv0 = vec2(l.y, 1.0 - l.x);
    else if (uSrcRotF == 2) uv0 = vec2(1.0 - l.x, 1.0 - l.y);
    else if (uSrcRotF == 3) uv0 = vec2(1.0 - l.y, l.x);
  }
  if (uDir.x != 0.0 || uDir.y != 0.0) {
    col = vec4(0.0);
    for (int i = -8; i <= 8; i++) col += tap(uv0 + uDir * (float(i) / 8.0));
    col /= 17.0;
  } else if (uRadial > 0.0) {
    col = vec4(0.0);
    vec2 d = (uRadC - uv0) * uRadial * 0.32;
    for (int i = 0; i < 14; i++) col += tap(uv0 + d * (float(i) / 13.0));
    col /= 14.0;
  } else if (uBlur > 0.5) {
    col = vec4(0.0);
    for (int i = 0; i < 24; i++) {
      float r = sqrt((float(i) + 0.5) / 24.0);
      float a = float(i) * 2.39996323;
      col += tap(uv0 + vec2(cos(a), sin(a)) * r * uBlur * uTexel);
    }
    col /= 24.0;
  } else {
    col = tap(uv0);
  }
  if (uChroma > 0.0) {
    col.r = tap(uv0 + vec2(uChroma, 0.0)).r;
    col.b = tap(uv0 - vec2(uChroma, 0.0)).b;
  }
  float a = col.a;
  vec3 c = col.rgb;
  if (uPremul == 1 && a > 0.0001) c /= a;
  if (uAutoExp > 0.0) {
    // the source's mean brightness from the top of its mip chain; a dim shot is lifted toward the target
    // with a curve that raises shadows and mids and keeps the highlights
    vec3 avg = textureLod(uTex, vec2(0.5), 16.0).rgb;
    float m = max(0.02, dot(avg, vec3(0.2126, 0.7152, 0.0722)));
    float g = clamp(uAutoExp / m, 1.0, 2.2);
    c = c * g / (1.0 + (g - 1.0) * c);
  }
  float lum0 = dot(c, vec3(0.2126, 0.7152, 0.0722));
  if (uGrade == 1) {
    c += uBright * 0.3;
    c = (c - 0.5) * (1.0 + uContrast) + 0.5;
    float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
    c = mix(vec3(l), c, 1.0 + uSat);
    c += vec3(uTemp * 0.09, -uTint * 0.07, -uTemp * 0.09);
    if (uHue != 0.0) c = hueShift(c, uHue);
    if (uVignette > 0.0) {
      vec2 sp = gl_FragCoord.xy / uRes - 0.5;
      sp.x *= uRes.x / uRes.y;
      float d = length(sp) / length(vec2(0.5 * uRes.x / uRes.y, 0.5));
      c *= 1.0 - uVignette * smoothstep(0.35, 1.0, d);
    }
    c = clamp(c, 0.0, 1.0);
  }
  if (uInvert > 0.0) c = mix(c, 1.0 - c, uInvert);
  c *= shade;
  if (uExpo > 0.0) c = clamp(c * (1.0 + 4.0 * uExpo), 0.0, 1.0);
  c += glint * vec3(0.9, 0.95, 1.0);
  vec2 sp = vec2(gl_FragCoord.x / uRes.x, 1.0 - gl_FragCoord.y / uRes.y);
  if (uLeak > 0.0) {
    float s = dot(sp, normalize(vec2(1.0, 0.45))) - uLeakPos * 1.25;
    vec3 lc = uLeakColor * uLeak * (exp(-s * s / 0.028) + 0.18);
    c = 1.0 - (1.0 - c) * (1.0 - clamp(lc, 0.0, 1.0));
  }
  c = mix(c, uFlashColor, uFlash);
  float m = 1.0;
  vec3 bolt = vec3(0.0);
  if (uMask == 1) {
    float proj = dot(sp - 0.5, uMaskDir) + 0.5;
    m = 1.0 - smoothstep(uMaskP - uMaskSoft, uMaskP + uMaskSoft, proj);
  } else if (uMask == 2) {
    vec2 ar = vec2(uRes.x / uRes.y, 1.0);
    float d = length((sp - uIris) * ar) / length(max(uIris, 1.0 - uIris) * ar);
    m = 1.0 - smoothstep(uMaskP - 0.03, uMaskP + 0.001, d);
  } else if (uMask == 3) {
    vec2 px = vec2(gl_FragCoord.x, uRes.y - gl_FragCoord.y);
    vec2 muv = (px - (uMaskCenter - uMaskSize * 0.5)) / uMaskSize;
    m = (muv.x < 0.0 || muv.y < 0.0 || muv.x > 1.0 || muv.y > 1.0) ? 0.0 : texture(uMaskTex, muv).a;
  } else if (uMask == 4) {
    float d = abs(sp.y - 0.5) + 0.14 * (sp.x - 0.5) * (sp.x - 0.5) * (1.0 - uMaskP);
    m = 1.0 - smoothstep(uMaskP * 0.56 - 0.03, uMaskP * 0.56 + 0.005, d);
  } else if (uMask == 5) {
    vec2 q = sp * vec2(uRes.x / uRes.y, 1.0);
    vec2 cc = uMaskDir * vec2(uRes.x / uRes.y, 1.0);
    float field = length(q - cc) * 0.95 + (fbm(q * 4.5) - 0.5) * 0.5;
    m = 1.0 - smoothstep(uMaskP - 0.012, uMaskP, field);
    float e = smoothstep(uMaskP - uEdgeW, uMaskP - 0.004, field) * m;
    c = mix(c, uEdge, clamp(e * 1.4, 0.0, 1.0));
  } else if (uMask == 7) {
    // lightning: a jagged channel from the top edge down with one fork; shape seed in uMaskDir.x, strike
    // progress in uMaskDir.y; the next shot opens out from the channel, the bolt's light is added on top
    vec2 q = vec2((sp.x - 0.5) * uRes.x / uRes.y, sp.y);
    float seed = uMaskDir.x * 17.0;
    float x0 = (hash(vec2(seed, 1.0)) - 0.5) * 0.2 * uRes.x / uRes.y;
    float path = x0 + (fbm(vec2(q.y * 2.6, seed)) - 0.5) * 0.5 + (vnoise(vec2(q.y * 28.0, seed + 5.0)) - 0.5) * 0.05;
    float d = abs(q.x - path);
    float fy = 0.34 + hash(vec2(seed, 3.0)) * 0.18;
    float side = hash(vec2(seed, 4.0)) > 0.5 ? 1.0 : -1.0;
    float fpath = path + (q.y - fy) * 0.75 * side + (fbm(vec2(q.y * 5.0, seed + 9.0)) - 0.5) * 0.18 + (vnoise(vec2(q.y * 34.0, seed + 2.0)) - 0.5) * 0.03;
    float fd = q.y > fy ? abs(q.x - fpath) : 9.0;
    float reach = uMaskDir.y * 1.08;
    float alive = smoothstep(reach + 0.001, reach - 0.05, q.y);
    float forkAlive = smoothstep(reach * 0.92 + 0.001, reach * 0.92 - 0.05, q.y) * smoothstep(fy + 0.62, fy, q.y);
    m = 1.0 - smoothstep(uMaskP - 0.012, uMaskP + 0.012, d + (1.0 - alive) * 2.0);
    float core = exp(-d * d / 0.000016) * alive + exp(-fd * fd / 0.000007) * forkAlive * 0.7;
    float halo = exp(-d / 0.03) * alive * 0.5 + exp(-fd / 0.016) * forkAlive * 0.28 + exp(-d / 0.16) * alive * 0.12;
    bolt = (vec3(1.0) * core * 1.5 + uEdge * (core * 0.7 + halo)) * uEdgeW;
  } else if (uMask == 6) {
    float th = 1.0 - uMaskP * 1.2;
    m = smoothstep(th, th + 0.22, lum0);
  } else if (uMask == 8) {
    // a jagged tear across the frame along uMaskDir; the torn edge catches the light (uEdge)
    float x = dot(sp - 0.5, uMaskDir) + 0.5 + (vnoise(sp * 42.0) - 0.5) * 0.045 + (fbm(sp * 5.0) - 0.5) * 0.07;
    m = 1.0 - smoothstep(uMaskP - 0.003, uMaskP + 0.003, x);
    c = mix(c, uEdge, (1.0 - smoothstep(0.0, uEdgeW, abs(x - uMaskP))) * 0.85 * m);
  } else if (uMask == 9) {
    // a six-blade camera aperture at uIris that turns as it opens
    vec2 q = (sp - uIris) * vec2(uRes.x / uRes.y, 1.0);
    float seg = 6.2832 / 6.0;
    float hd = length(q) * cos(mod(atan(q.y, q.x) + uMaskP * 2.2, seg) - seg * 0.5);
    m = 1.0 - smoothstep(uMaskP - 0.004, uMaskP + 0.002, hd);
    c *= 1.0 - 0.6 * (1.0 - smoothstep(0.0, 0.025, uMaskP - hd)) * m;
  } else if (uMask == 10) {
    // a windscreen wiper arm sweeping round a pivot below the frame
    vec2 q = (sp - vec2(0.5, 1.15)) * vec2(uRes.x / uRes.y, 1.0);
    float ang = atan(q.x, -q.y), th = mix(-1.35, 1.35, uMaskP);
    m = 1.0 - smoothstep(th - 0.015, th + 0.015, ang);
    c = mix(c, uEdge, (1.0 - smoothstep(0.0, uEdgeW, abs(ang - th))) * m);
  } else if (uMask == 11) {
    // venetian blinds: backlit slats open from the top down
    float N = 12.0, row = floor(sp.y * N), f = fract(sp.y * N);
    float o = clamp(uMaskP * 1.45 - row / N * 0.45, 0.0, 1.0);
    m = step(abs(f - 0.5), o * 0.5);
    c += uEdge * uEdgeW * (1.0 - smoothstep(0.0, 0.08, abs(abs(f - 0.5) - o * 0.5))) * step(0.001, o) * (1.0 - smoothstep(0.8, 1.0, o));
  }
  float alpha = a * uOpacity * m * inside;
  outColor = vec4(c * alpha + bolt * uOpacity, alpha);
}`;

export interface DrawParams {
  /** Texture key; the texture is re-uploaded only when `version` changes. */
  key: string;
  version: unknown;
  source: TexImageSource | null;
  /** Natural size of the source (display orientation). */
  srcW: number;
  srcH: number;
  /** Quarter turns (clockwise) to apply to the source. */
  srcRot: 0 | 1 | 2 | 3;
  /** Base size in output pixels before transform (fit already applied). */
  baseW: number;
  baseH: number;
  transform: Transform;
  fx: LayerFx;
  color?: ColorAdjust;
  premultiplied?: boolean;
  /** How the layer combines with what is under it (graphics). */
  blend?: BlendMode;
  /** Auto exposure: lift a dim picture toward this mean brightness (0-1; 0 = off). */
  autoExpose?: number;
}

/** Values an effect reads (see the prelude in custom.ts). */
export interface ShaderUniforms {
  t: number; p: number; dur: number; time: number; beat: number; beatAge: number; energy: number;
  opacity: number; scale: number; rot: number; pos: [number, number]; seed: number;
}

type FxProgram = { prog: WebGLProgram; u: Record<string, WebGLUniformLocation | null> } | { error: string };
const FX_UNIFORMS = ['uRes', 'uT', 'uP', 'uDur', 'uTime', 'uBeat', 'uBeatAge', 'uEnergy', 'uOpacity', 'uScale', 'uRot', 'uAspect', 'uSeed', 'uPos', 'uFrame', 'uTextMask', 'uTextRect'];

/** A texture an effect reads as a stencil (knockout text), placed at a rectangle of the frame (px, centre and size). */
export interface ShaderMask { key: string; version: unknown; source: TexImageSource; cx: number; cy: number; w: number; h: number }

export interface Quad { cx: number; cy: number; w: number; h: number; rot: number }

interface TexEntry { tex: WebGLTexture; version: unknown; w: number; h: number; used: number }

/** Width of the logo at scale 1, as a fraction of the frame width. */
const LOGO_W = 0.86;

export class Compositor {
  readonly gl: WebGL2RenderingContext;
  private prog: WebGLProgram;
  private vao: WebGLVertexArrayObject;
  private u: Record<string, WebGLUniformLocation | null> = {};
  private textures = new Map<string, TexEntry>();
  private frame = 0;
  private autoExp = 0;
  width = 1;
  height = 1;
  /** Where each clip was drawn in the last frame (output pixels). */
  quads = new Map<string, Quad>();
  private aPosLoc = 0;
  /** The GPU dropped this context (a driver reset, often from an effect that is too heavy). */
  lost = false;
  /** The last effect drawn, to name it when the GPU gives up. */
  lastShader = '';
  private fxProgs = new Map<string, FxProgram>();
  private frameTex: WebGLTexture | null = null;

  constructor(readonly canvas: HTMLCanvasElement | OffscreenCanvas, opts: { preserve?: boolean } = {}) {
    const gl = canvas.getContext('webgl2', {
      alpha: false, antialias: false, depth: false, stencil: false, premultipliedAlpha: true,
      preserveDrawingBuffer: !!opts.preserve, powerPreference: 'high-performance',
    }) as WebGL2RenderingContext | null;
    if (!gl) throw new Error('WebGL2 is not available in this browser.');
    this.gl = gl;
    (canvas as any).addEventListener?.('webglcontextlost', (e: Event) => { e.preventDefault(); this.lost = true; });
    const sh = (type: number, src: string) => {
      const s = gl.createShader(type)!;
      gl.shaderSource(s, src);
      gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error('Shader: ' + gl.getShaderInfoLog(s));
      return s;
    };
    const prog = gl.createProgram()!;
    gl.attachShader(prog, sh(gl.VERTEX_SHADER, VS));
    gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error('Program: ' + gl.getProgramInfoLog(prog));
    this.prog = prog;
    gl.useProgram(prog);
    const names = ['uCenter', 'uSize', 'uRot', 'uRes', 'uSrcRot', 'uTex', 'uMaskTex', 'uTexel', 'uOpacity', 'uBright', 'uContrast', 'uSat', 'uTemp', 'uTint', 'uHue', 'uVignette', 'uAutoExp',
      'uBlur', 'uDir', 'uRadial', 'uChroma', 'uMask', 'uMaskDir', 'uMaskP', 'uMaskSoft', 'uMaskCenter', 'uMaskSize', 'uEdge', 'uEdgeW', 'uFlashColor', 'uFlash', 'uInvert', 'uLeak', 'uLeakPos', 'uPremul', 'uGrade',
      'uLeakColor', 'uWarp', 'uWarpP', 'uWarpA', 'uWarpC', 'uRect', 'uSrcRotF', 'uRadC', 'uIris', 'uExpo'];
    for (const n of names) this.u[n] = gl.getUniformLocation(prog, n);
    this.vao = gl.createVertexArray()!;
    gl.bindVertexArray(this.vao);
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([0, 0, 1, 0, 0, 1, 1, 1]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(prog, 'aPos');
    this.aPosLoc = loc;
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    gl.uniform1i(this.u.uTex, 0);
    gl.uniform1i(this.u.uMaskTex, 1);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
  }

  resize(w: number, h: number) {
    w = Math.max(2, Math.round(w));
    h = Math.max(2, Math.round(h));
    if (this.canvas.width !== w) this.canvas.width = w;
    if (this.canvas.height !== h) this.canvas.height = h;
    this.width = w;
    this.height = h;
  }

  begin(bg: string) {
    const gl = this.gl;
    this.frame++;
    this.quads.clear();
    gl.viewport(0, 0, this.width, this.height);
    const [r, g, b] = hexToRgb(bg);
    gl.clearColor(r, g, b, 1);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.useProgram(this.prog);
    gl.bindVertexArray(this.vao);
    gl.uniform2f(this.u.uRes, this.width, this.height);
  }

  private texture(key: string, version: unknown, source: TexImageSource | null, premul: boolean, mip = false): TexEntry | null {
    const gl = this.gl;
    let e = this.textures.get(key);
    if (source && (!e || e.version !== version)) {
      // uploads always go through unit 0, so a new texture never replaces what another unit holds
      gl.activeTexture(gl.TEXTURE0);
      if (!e) {
        const tex = gl.createTexture()!;
        gl.bindTexture(gl.TEXTURE_2D, tex);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        e = { tex, version: undefined, w: 1, h: 1, used: this.frame };
        this.textures.set(key, e);
      }
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, e.tex);
      gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, premul);
      try {
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, source);
        // auto exposure reads the picture's mean from the smallest mip level
        if (mip) { gl.generateMipmap(gl.TEXTURE_2D); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR); }
        else gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
        const s = source as any;
        e.w = s.displayWidth || s.videoWidth || s.naturalWidth || s.width || 1;
        e.h = s.displayHeight || s.videoHeight || s.naturalHeight || s.height || 1;
        e.version = version;
      } catch {
        // source not ready (e.g. video without a decoded frame): keep the previous texture
      }
    }
    if (e) e.used = this.frame;
    return e && e.version !== undefined ? e : null;
  }

  /** Geometry of the logo (and its counter mask) for logo fx parameters. */
  logoQuad(fx: LayerFx): Quad | null {
    const L = logo();
    if (!L) return null;
    const w = LOGO_W * this.width * fx.logoS, h = (w * L.h) / L.w;
    return { cx: this.width / 2 + (0.5 - fx.logoAx) * w, cy: this.height / 2 + (0.5 - fx.logoAy) * h, w, h, rot: 0 };
  }

  /** Draw the voidfx logo exactly as supplied (no colour changes). */
  drawLogo(fx: LayerFx) {
    const L = logo();
    const q = this.logoQuad(fx);
    if (!L || !q || fx.opacity <= 0.001) return;
    const e = this.texture('__logo', 1, L.img, true);
    if (!e) return;
    this.raw(e, q.cx, q.cy, q.w, q.h, 0, 0, { ...fx, mask: 0, flash: 0, invert: 0, leak: 0, chroma: 0 }, undefined, true, fx.opacity);
  }

  draw(d: DrawParams): boolean {
    const premul = !!d.premultiplied;
    this.autoExp = d.autoExpose && d.autoExpose > 0 ? d.autoExpose : 0;
    const e = this.texture(d.key, d.version, d.source, premul, this.autoExp > 0);
    if (!e) return false;
    const fx = d.fx;
    const t = d.transform;
    const W = this.width, H = this.height;
    const scale = t.scale * fx.scale;
    const w = d.baseW * scale, h = d.baseH * scale;
    const cx = W / 2 + (t.x + fx.dx) * W;
    const cy = H / 2 + (t.y + fx.dy) * H;
    const rot = t.rotation + fx.rot;
    const opacity = t.opacity * fx.opacity;
    if (opacity <= 0.001 || w < 0.5 || h < 0.5) return true;
    this.quads.set(d.key, { cx, cy, w, h, rot });
    if (fx.split) {
      const len = Math.hypot(fx.split.nx, fx.split.ny) || 1;
      const nx = fx.split.nx / len, ny = fx.split.ny / len, g = fx.split.gap / 2;
      for (const sgn of [-1, 1]) {
        const sub: LayerFx = { ...fx, split: null, mask: 1, maskX: -sgn * nx, maskY: -sgn * ny, maskP: 0.5 - g };
        this.raw(e, cx + sgn * nx * g * W, cy + sgn * ny * g * H, w, h, rot, d.srcRot, sub, d.color, premul, opacity, 0.002);
      }
      return true;
    }
    if (d.blend && d.blend !== 'normal') this.setBlend(d.blend);
    this.raw(e, cx, cy, w, h, rot, d.srcRot, fx, d.color, premul, opacity, fx.mask === 1 ? 0.02 : 0);
    if (d.blend && d.blend !== 'normal') this.setBlend('normal');
    return true;
  }

  setBlend(mode: BlendMode) {
    const gl = this.gl;
    if (mode === 'add') gl.blendFunc(gl.ONE, gl.ONE);
    else if (mode === 'screen') gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_COLOR);
    else gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
  }

  private buildFx(code: string): FxProgram {
    const gl = this.gl;
    const sh = (type: number, src: string): WebGLShader | string => {
      const s = gl.createShader(type)!;
      gl.shaderSource(s, src);
      gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) { const log = gl.getShaderInfoLog(s) || 'did not compile'; gl.deleteShader(s); return log; }
      return s;
    };
    const vs = sh(gl.VERTEX_SHADER, SHADER_VS), fs = sh(gl.FRAGMENT_SHADER, wrapShader(code));
    if (typeof vs === 'string') return { error: vs };
    if (typeof fs === 'string') return { error: fs.trim() };
    const prog = gl.createProgram()!;
    gl.attachShader(prog, vs);
    gl.attachShader(prog, fs);
    gl.bindAttribLocation(prog, this.aPosLoc, 'aPos');
    gl.linkProgram(prog);
    gl.deleteShader(vs);
    gl.deleteShader(fs);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) return { error: gl.getProgramInfoLog(prog) || 'did not link' };
    const u: Record<string, WebGLUniformLocation | null> = {};
    for (const n of FX_UNIFORMS) u[n] = gl.getUniformLocation(prog, n);
    return { prog, u };
  }

  /** Run an effect over the whole frame. Returns the compiler's message when it cannot run (it is then skipped). */
  drawShader(code: string, blend: BlendMode, v: ShaderUniforms, name = '', mask?: ShaderMask): string | null {
    const gl = this.gl;
    if (this.lost) return 'the graphics context was lost';
    this.lastShader = name;
    let entry = this.fxProgs.get(code);
    if (!entry) {
      entry = this.buildFx(code);
      this.fxProgs.set(code, entry);
      if (this.fxProgs.size > 64) {
        const [k, old] = this.fxProgs.entries().next().value as [string, FxProgram];
        if ('prog' in old) gl.deleteProgram(old.prog);
        this.fxProgs.delete(k);
      }
    }
    if ('error' in entry) return entry.error;
    if (v.opacity <= 0.001) return null;
    const u = entry.u;
    let maskOn = false;
    if (mask) {
      const me = this.texture(mask.key, mask.version, mask.source, true);
      if (me) {
        gl.activeTexture(gl.TEXTURE3);
        gl.bindTexture(gl.TEXTURE_2D, me.tex);
        maskOn = true;
      }
    }
    if (readsFrame(code)) {
      gl.activeTexture(gl.TEXTURE2);
      if (!this.frameTex) {
        this.frameTex = gl.createTexture();
        gl.bindTexture(gl.TEXTURE_2D, this.frameTex);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      }
      gl.activeTexture(gl.TEXTURE2);
      gl.bindTexture(gl.TEXTURE_2D, this.frameTex);
      gl.copyTexImage2D(gl.TEXTURE_2D, 0, gl.RGB, 0, 0, this.width, this.height, 0);
    }
    gl.useProgram(entry.prog);
    gl.uniform1i(u.uTextMask, 3);
    gl.uniform4f(u.uTextRect, mask && maskOn ? mask.cx - mask.w / 2 : -10, mask && maskOn ? mask.cy - mask.h / 2 : -10, mask && maskOn ? mask.w : 1, mask && maskOn ? mask.h : 1);
    gl.uniform2f(u.uRes, this.width, this.height);
    gl.uniform1f(u.uT, v.t); gl.uniform1f(u.uP, v.p); gl.uniform1f(u.uDur, v.dur); gl.uniform1f(u.uTime, v.time);
    gl.uniform1f(u.uBeat, v.beat); gl.uniform1f(u.uBeatAge, v.beatAge); gl.uniform1f(u.uEnergy, v.energy);
    gl.uniform1f(u.uOpacity, v.opacity); gl.uniform1f(u.uScale, v.scale); gl.uniform1f(u.uRot, v.rot);
    gl.uniform1f(u.uAspect, this.width / this.height); gl.uniform1f(u.uSeed, v.seed);
    gl.uniform2f(u.uPos, v.pos[0], v.pos[1]);
    gl.uniform1i(u.uFrame, 2);
    this.setBlend(blend);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    this.setBlend('normal');
    gl.useProgram(this.prog);
    gl.activeTexture(gl.TEXTURE0);
    return null;
  }

  private raw(e: TexEntry, cx: number, cy: number, w: number, h: number, rot: number, srcRot: number, fx: LayerFx, c: ColorAdjust | undefined, premul: boolean, opacity: number, soft = 0) {
    const gl = this.gl;
    const H = this.height, W = this.width;
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, e.tex);
    const warp = fx.warp || 0;
    // a warped layer is drawn as a full-frame quad and mapped back onto its own rectangle per pixel
    gl.uniform2f(this.u.uCenter, warp ? W / 2 : cx, warp ? H / 2 : cy);
    gl.uniform2f(this.u.uSize, warp ? W : w, warp ? H : h);
    gl.uniform1f(this.u.uRot, warp ? 0 : (rot * Math.PI) / 180);
    gl.uniform1i(this.u.uSrcRot, warp ? 0 : srcRot);
    gl.uniform1i(this.u.uWarp, warp);
    gl.uniform1f(this.u.uWarpP, fx.warpP || 0);
    gl.uniform1f(this.u.uWarpA, fx.warpA || 0);
    gl.uniform2f(this.u.uWarpC, fx.warpC?.[0] ?? 0.5, fx.warpC?.[1] ?? 0.5);
    gl.uniform4f(this.u.uRect, cx, cy, w, h);
    gl.uniform1i(this.u.uSrcRotF, srcRot);
    gl.uniform2f(this.u.uRadC, fx.radC?.[0] ?? 0.5, fx.radC?.[1] ?? 0.5);
    gl.uniform2f(this.u.uIris, fx.iris?.[0] ?? 0.5, fx.iris?.[1] ?? 0.5);
    gl.uniform1f(this.u.uExpo, fx.expo || 0);
    const lc = fx.leakColor || [1, 0.58, 0.22];
    gl.uniform3f(this.u.uLeakColor, lc[0], lc[1], lc[2]);
    gl.uniform2f(this.u.uTexel, 1 / e.w, 1 / e.h);
    gl.uniform1f(this.u.uOpacity, opacity);
    gl.uniform1i(this.u.uGrade, c ? 1 : 0);
    gl.uniform1f(this.u.uAutoExp, this.autoExp);
    if (c) {
      gl.uniform1f(this.u.uBright, c.brightness);
      gl.uniform1f(this.u.uContrast, c.contrast);
      gl.uniform1f(this.u.uSat, c.saturation);
      gl.uniform1f(this.u.uTemp, c.temperature);
      gl.uniform1f(this.u.uTint, c.tint);
      gl.uniform1f(this.u.uHue, (c.hue * Math.PI) / 180);
      gl.uniform1f(this.u.uVignette, c.vignette);
    }
    const blurAmt = Math.max(c?.blur || 0, fx.blur);
    const pxPerTex = h / (srcRot % 2 ? e.w : e.h);
    gl.uniform1f(this.u.uBlur, blurAmt > 0 ? (blurAmt * 0.035 * H) / Math.max(pxPerTex, 1e-3) : 0);
    let dirU = 0, dirV = 0;
    if (fx.dirX || fx.dirY) [dirU, dirV] = rotUv((fx.dirX * W) / w, (fx.dirY * H) / h, srcRot);
    gl.uniform2f(this.u.uDir, dirU, dirV);
    gl.uniform1f(this.u.uRadial, fx.radial || 0);
    gl.uniform1f(this.u.uChroma, fx.chroma ? (fx.chroma * W) / w : 0);
    let mask = fx.mask;
    if (mask === 3) {
      const L = logo();
      const q = this.logoQuad(fx);
      if (L && q) {
        const me = this.texture('__logomask', 1, L.mask as any, true);
        if (me) {
          gl.activeTexture(gl.TEXTURE1);
          gl.bindTexture(gl.TEXTURE_2D, me.tex);
          gl.activeTexture(gl.TEXTURE0);
          gl.bindTexture(gl.TEXTURE_2D, e.tex);
          gl.uniform2f(this.u.uMaskCenter, q.cx, q.cy);
          gl.uniform2f(this.u.uMaskSize, q.w, q.h);
        } else mask = 0;
      } else mask = 0;
    }
    gl.uniform1i(this.u.uMask, mask);
    gl.uniform2f(this.u.uMaskDir, fx.maskX, fx.maskY);
    gl.uniform1f(this.u.uMaskP, mask === 2 ? fx.maskP * 1.05 : mask === 1 && !soft ? fx.maskP : fx.maskP);
    gl.uniform1f(this.u.uMaskSoft, soft || 0.02);
    gl.uniform3f(this.u.uEdge, fx.edge[0], fx.edge[1], fx.edge[2]);
    gl.uniform1f(this.u.uEdgeW, fx.edgeW || 0.05);
    gl.uniform3f(this.u.uFlashColor, fx.flashColor[0], fx.flashColor[1], fx.flashColor[2]);
    gl.uniform1f(this.u.uFlash, fx.flash);
    gl.uniform1f(this.u.uInvert, fx.invert || 0);
    gl.uniform1f(this.u.uLeak, fx.leak || 0);
    gl.uniform1f(this.u.uLeakPos, fx.leakPos);
    gl.uniform1i(this.u.uPremul, premul ? 1 : 0);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  }

  /** Free textures not used for a while (clips removed or scrolled away). */
  gc(maxIdleFrames = 240) {
    for (const [k, e] of this.textures) {
      if (k.startsWith('__')) continue;
      if (this.frame - e.used > maxIdleFrames) {
        this.gl.deleteTexture(e.tex);
        this.textures.delete(k);
      }
    }
  }

  /** Has this key a drawn texture (a frame to hold while a source catches up)? */
  hasTexture(key: string) { const e = this.textures.get(key); return !!e && e.version !== undefined; }

  dispose() {
    for (const e of this.textures.values()) this.gl.deleteTexture(e.tex);
    for (const f of this.fxProgs.values()) if ('prog' in f) this.gl.deleteProgram(f.prog);
    if (this.frameTex) this.gl.deleteTexture(this.frameTex);
    this.textures.clear();
    this.gl.getExtension('WEBGL_lose_context')?.loseContext();
  }
}

function rotUv(x: number, y: number, rot: number): [number, number] {
  switch (rot) {
    case 1: return [y, -x];
    case 2: return [-x, -y];
    case 3: return [-y, x];
    default: return [x, y];
  }
}

export function hexToRgb(hex: string): [number, number, number] {
  let h = (hex || '#000').replace('#', '');
  if (h.length === 3) h = h.split('').map(c => c + c).join('');
  const n = parseInt(h, 16) || 0;
  return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
}

/** Base (fitted) size of a source inside the frame. */
export function fitSize(srcW: number, srcH: number, W: number, H: number, fit: 'cover' | 'contain' = 'cover'): [number, number] {
  const s = fit === 'contain' ? Math.min(W / srcW, H / srcH) : Math.max(W / srcW, H / srcH);
  return [srcW * s, srcH * s];
}
