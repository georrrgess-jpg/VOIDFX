// WebGL2 compositor. Draws media, image and text layers with transform, colour, blur and
// transition effects. One instance drives the preview canvas; export and review use their own.
import { ColorAdjust, Transform } from '../state/types';
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
uniform vec2 uTexel; uniform vec2 uRes;
uniform float uOpacity;
uniform float uBright, uContrast, uSat, uTemp, uTint, uHue, uVignette;
uniform float uBlur; uniform vec2 uDir; uniform float uChroma;
uniform int uMask; uniform vec2 uMaskDir; uniform float uMaskP;
uniform vec3 uFlashColor; uniform float uFlash;
uniform int uPremul; uniform int uGrade;
out vec4 outColor;

vec4 tap(vec2 uv) { return texture(uTex, clamp(uv, vec2(0.0), vec2(1.0))); }
vec3 hueShift(vec3 col, float h) {
  const vec3 k = vec3(0.57735);
  float c = cos(h);
  return col * c + cross(k, col) * sin(h) + k * dot(k, col) * (1.0 - c);
}
void main() {
  vec4 col;
  if (uDir.x != 0.0 || uDir.y != 0.0) {
    col = vec4(0.0);
    for (int i = -8; i <= 8; i++) col += tap(vUv + uDir * (float(i) / 8.0));
    col /= 17.0;
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
  c = mix(c, uFlashColor, uFlash);
  float m = 1.0;
  if (uMask == 1) {
    vec2 sp = vec2(gl_FragCoord.x / uRes.x, 1.0 - gl_FragCoord.y / uRes.y);
    float proj = dot(sp - 0.5, uMaskDir) + 0.5;
    m = 1.0 - smoothstep(uMaskP - 0.02, uMaskP + 0.02, proj * 1.04 - 0.02);
  } else if (uMask == 2) {
    vec2 sp = gl_FragCoord.xy / uRes - 0.5;
    sp.x *= uRes.x / uRes.y;
    float d = length(sp) / length(vec2(0.5 * uRes.x / uRes.y, 0.5));
    m = 1.0 - smoothstep(uMaskP - 0.03, uMaskP + 0.001, d);
  }
  float alpha = a * uOpacity * m;
  outColor = vec4(c * alpha, alpha);
}`;

export interface DrawParams {
  /** Texture key; the texture is re-uploaded only when `version` changes. */
  key: string;
  version: unknown;
  source: TexImageSource | null;
  /** Natural size of the source before rotation. */
  srcW: number;
  srcH: number;
  /** Quarter turns (clockwise) to apply to the source. */
  srcRot: 0 | 1 | 2 | 3;
  /** Base size in output pixels before transform (fit already applied). */
  baseW: number;
  baseH: number;
  /** Centre offset in output pixels before transform (text anchor). */
  baseCx?: number;
  baseCy?: number;
  transform: Transform;
  fx: LayerFx;
  color?: ColorAdjust;
  premultiplied?: boolean;
}

export interface Quad { cx: number; cy: number; w: number; h: number; rot: number }

interface TexEntry { tex: WebGLTexture; version: unknown; w: number; h: number; used: number }

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
    const names = ['uCenter', 'uSize', 'uRot', 'uRes', 'uSrcRot', 'uTex', 'uTexel', 'uOpacity', 'uBright', 'uContrast', 'uSat', 'uTemp', 'uTint', 'uHue', 'uVignette', 'uBlur', 'uDir', 'uChroma', 'uMask', 'uMaskDir', 'uMaskP', 'uFlashColor', 'uFlash', 'uPremul', 'uGrade'];
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

  draw(d: DrawParams): boolean {
    const gl = this.gl;
    const premul = !!d.premultiplied;
    const e = this.texture(d.key, d.version, d.source, premul);
    if (!e) return false;
    const fx = d.fx;
    const t = d.transform;
    const W = this.width, H = this.height;
    const scale = t.scale * fx.scale;
    const w = d.baseW * scale, h = d.baseH * scale;
    const cx = (d.baseCx ?? W / 2) + (t.x + fx.dx) * W;
    const cy = (d.baseCy ?? H / 2) + (t.y + fx.dy) * H;
    const rot = t.rotation + fx.rot;
    const opacity = t.opacity * fx.opacity;
    if (opacity <= 0.001 || w < 0.5 || h < 0.5) return true;
    this.quads.set(d.key, { cx, cy, w, h, rot });
    gl.bindTexture(gl.TEXTURE_2D, e.tex);
    gl.uniform2f(this.u.uCenter, cx, cy);
    gl.uniform2f(this.u.uSize, w, h);
    gl.uniform1f(this.u.uRot, (rot * Math.PI) / 180);
    gl.uniform1i(this.u.uSrcRot, d.srcRot);
    gl.uniform2f(this.u.uTexel, 1 / e.w, 1 / e.h);
    gl.uniform1f(this.u.uOpacity, opacity);
    const c = d.color;
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
    // blur radius in texture pixels: fraction of frame height mapped into source space
    const blurAmt = Math.max(c?.blur || 0, fx.blur);
    const pxPerTex = h / (d.srcRot % 2 ? e.w : e.h);
    gl.uniform1f(this.u.uBlur, blurAmt > 0 ? (blurAmt * 0.035 * H) / Math.max(pxPerTex, 1e-3) : 0);
    // directional blur vector in uv space (rotate into source orientation)
    let dirU = 0, dirV = 0;
    if (fx.dirX || fx.dirY) {
      const ux = (fx.dirX * W) / w, uy = (fx.dirY * H) / h;
      [dirU, dirV] = rotUv(ux, uy, d.srcRot);
    }
    gl.uniform2f(this.u.uDir, dirU, dirV);
    gl.uniform1f(this.u.uChroma, fx.chroma ? (fx.chroma * W) / w : 0);
    gl.uniform1i(this.u.uMask, fx.mask);
    gl.uniform2f(this.u.uMaskDir, fx.maskX, fx.maskY);
    gl.uniform1f(this.u.uMaskP, fx.mask === 2 ? fx.maskP * 1.05 : fx.maskP);
    gl.uniform3f(this.u.uFlashColor, fx.flashColor[0], fx.flashColor[1], fx.flashColor[2]);
    gl.uniform1f(this.u.uFlash, fx.flash);
    gl.uniform1i(this.u.uPremul, premul ? 1 : 0);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    return true;
  }

  /** Free textures not used for a while (clips removed or scrolled away). */
  gc(maxIdleFrames = 240) {
    for (const [k, e] of this.textures) {
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
  // convert a display-space vector into raw texture space for a source rotated by rot quarter turns
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
