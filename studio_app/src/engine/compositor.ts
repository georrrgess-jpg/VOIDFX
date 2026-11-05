// WebGL2 compositor. Draws media, image, text and logo layers with transform, colour, blur and
// transition effects. One instance drives the preview canvas; export, review and previews use their own.
import { ColorAdjust, Transform } from '../state/types';
import { logo } from './logo';
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
uniform float uBlur; uniform vec2 uDir; uniform float uRadial; uniform float uChroma;
uniform int uMask; uniform vec2 uMaskDir; uniform float uMaskP; uniform float uMaskSoft;
uniform vec2 uMaskCenter; uniform vec2 uMaskSize;
uniform vec3 uEdge; uniform float uEdgeW;
uniform vec3 uFlashColor; uniform float uFlash; uniform float uInvert;
uniform float uLeak; uniform float uLeakPos;
uniform int uPremul; uniform int uGrade;
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

void main() {
  vec4 col;
  if (uDir.x != 0.0 || uDir.y != 0.0) {
    col = vec4(0.0);
    for (int i = -8; i <= 8; i++) col += tap(vUv + uDir * (float(i) / 8.0));
    col /= 17.0;
  } else if (uRadial > 0.0) {
    col = vec4(0.0);
    vec2 d = (vec2(0.5) - vUv) * uRadial * 0.32;
    for (int i = 0; i < 14; i++) col += tap(vUv + d * (float(i) / 13.0));
    col /= 14.0;
  } else if (uBlur > 0.5) {
    col = vec4(0.0);
    for (int i = 0; i < 24; i++) {
      float r = sqrt((float(i) + 0.5) / 24.0);
      float a = float(i) * 2.39996323;
      col += tap(vUv + vec2(cos(a), sin(a)) * r * uBlur * uTexel);
    }
    col /= 24.0;
  } else {
    col = tap(vUv);
  }
  if (uChroma > 0.0) {
    col.r = tap(vUv + vec2(uChroma, 0.0)).r;
    col.b = tap(vUv - vec2(uChroma, 0.0)).b;
  }
  float a = col.a;
  vec3 c = col.rgb;
  if (uPremul == 1 && a > 0.0001) c /= a;
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
  vec2 sp = vec2(gl_FragCoord.x / uRes.x, 1.0 - gl_FragCoord.y / uRes.y);
  if (uLeak > 0.0) {
    float s = dot(sp, normalize(vec2(1.0, 0.45))) - uLeakPos * 1.25;
    vec3 lc = vec3(1.0, 0.58, 0.22) * uLeak * (exp(-s * s / 0.028) + 0.18);
    c = 1.0 - (1.0 - c) * (1.0 - clamp(lc, 0.0, 1.0));
  }
  c = mix(c, uFlashColor, uFlash);
  float m = 1.0;
  if (uMask == 1) {
    float proj = dot(sp - 0.5, uMaskDir) + 0.5;
    m = 1.0 - smoothstep(uMaskP - uMaskSoft, uMaskP + uMaskSoft, proj);
  } else if (uMask == 2) {
    vec2 q = gl_FragCoord.xy / uRes - 0.5;
    q.x *= uRes.x / uRes.y;
    float d = length(q) / length(vec2(0.5 * uRes.x / uRes.y, 0.5));
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
  } else if (uMask == 6) {
    float th = 1.0 - uMaskP * 1.2;
    m = smoothstep(th, th + 0.22, lum0);
  }
  float alpha = a * uOpacity * m;
  outColor = vec4(c * alpha, alpha);
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
}

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
  width = 1;
  height = 1;
  /** Where each clip was drawn in the last frame (output pixels). */
  quads = new Map<string, Quad>();

  constructor(readonly canvas: HTMLCanvasElement | OffscreenCanvas, opts: { preserve?: boolean } = {}) {
    const gl = canvas.getContext('webgl2', {
      alpha: false, antialias: false, depth: false, stencil: false, premultipliedAlpha: true,
      preserveDrawingBuffer: !!opts.preserve, powerPreference: 'high-performance',
    }) as WebGL2RenderingContext | null;
    if (!gl) throw new Error('WebGL2 is not available in this browser.');
    this.gl = gl;
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
    const names = ['uCenter', 'uSize', 'uRot', 'uRes', 'uSrcRot', 'uTex', 'uMaskTex', 'uTexel', 'uOpacity', 'uBright', 'uContrast', 'uSat', 'uTemp', 'uTint', 'uHue', 'uVignette',
      'uBlur', 'uDir', 'uRadial', 'uChroma', 'uMask', 'uMaskDir', 'uMaskP', 'uMaskSoft', 'uMaskCenter', 'uMaskSize', 'uEdge', 'uEdgeW', 'uFlashColor', 'uFlash', 'uInvert', 'uLeak', 'uLeakPos', 'uPremul', 'uGrade'];
    for (const n of names) this.u[n] = gl.getUniformLocation(prog, n);
    this.vao = gl.createVertexArray()!;
    gl.bindVertexArray(this.vao);
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([0, 0, 1, 0, 0, 1, 1, 1]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(prog, 'aPos');
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

  private texture(key: string, version: unknown, source: TexImageSource | null, premul: boolean): TexEntry | null {
    const gl = this.gl;
    let e = this.textures.get(key);
    if (source && (!e || e.version !== version)) {
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
    const e = this.texture(d.key, d.version, d.source, premul);
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
    this.raw(e, cx, cy, w, h, rot, d.srcRot, fx, d.color, premul, opacity, fx.mask === 1 ? 0.02 : 0);
    return true;
  }

  private raw(e: TexEntry, cx: number, cy: number, w: number, h: number, rot: number, srcRot: number, fx: LayerFx, c: ColorAdjust | undefined, premul: boolean, opacity: number, soft = 0) {
    const gl = this.gl;
    const H = this.height, W = this.width;
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, e.tex);
    gl.uniform2f(this.u.uCenter, cx, cy);
    gl.uniform2f(this.u.uSize, w, h);
    gl.uniform1f(this.u.uRot, (rot * Math.PI) / 180);
    gl.uniform1i(this.u.uSrcRot, srcRot);
    gl.uniform2f(this.u.uTexel, 1 / e.w, 1 / e.h);
    gl.uniform1f(this.u.uOpacity, opacity);
    gl.uniform1i(this.u.uGrade, c ? 1 : 0);
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

  hasTexture(key: string) { return this.textures.has(key); }

  dispose() {
    for (const e of this.textures.values()) this.gl.deleteTexture(e.tex);
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
