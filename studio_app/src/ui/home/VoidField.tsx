import { useEffect, useRef } from 'preact/hooks';

// The main menu's living background: domain-warped smoke drifting around a dark event horizon,
// tinted by the active section, leaning toward the pointer.
const VS = `#version 300 es
in vec2 aPos; out vec2 vUv;
void main() { vUv = aPos * 0.5 + 0.5; gl_Position = vec4(aPos, 0.0, 1.0); }`;
const FS = `#version 300 es
precision highp float;
in vec2 vUv; out vec4 o;
uniform vec2 uRes; uniform float uTime; uniform vec2 uMouse; uniform vec3 uTint; uniform vec3 uTint2;
float h(vec2 p){ return fract(sin(dot(p, vec2(41.3, 289.1))) * 43758.5453); }
float n(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f);
  return mix(mix(h(i), h(i+vec2(1,0)), u.x), mix(h(i+vec2(0,1)), h(i+vec2(1,1)), u.x), u.y); }
float fbm(vec2 p){ float v = 0.0, a = 0.5; mat2 r = mat2(0.8, -0.6, 0.6, 0.8); for (int i = 0; i < 6; i++){ v += a*n(p); p = r*p*2.03 + 7.1; a *= 0.5; } return v; }
void main(){
  vec2 uv = (gl_FragCoord.xy - 0.5*uRes) / uRes.y;
  vec2 m = (uMouse - 0.5) * vec2(uRes.x/uRes.y, 1.0);
  vec2 c = vec2(0.32 * uRes.x / uRes.y, 0.04) + m * 0.06;
  vec2 d = uv - c;
  float r = length(d);
  float ang = atan(d.y, d.x);
  float t = uTime * 0.045;
  // swirl around the horizon
  float sw = 0.9 / (r + 0.35);
  vec2 q = vec2(cos(ang + sw + t * 3.0), sin(ang + sw + t * 3.0)) * r;
  float f1 = fbm(q * 2.2 + vec2(t, -t));
  float f2 = fbm(q * 3.6 + f1 * 1.8 + vec2(-t * 1.7, t));
  float smoke = smoothstep(0.35, 1.0, f2) * (1.0 - smoothstep(0.08, 1.2, r));
  float ring = exp(-pow((r - 0.205) * 26.0, 2.0)) * (0.55 + 0.45 * f1);
  float core = smoothstep(0.2, 0.17, r);
  vec3 col = vec3(0.012, 0.012, 0.02);
  col += uTint * smoke * 0.42;
  col += mix(uTint2, uTint, f1) * ring * 0.9;
  col += uTint * 0.05 * exp(-r * 2.4);
  col *= 1.0 - core * 0.97;
  // fine stars
  vec2 sp = gl_FragCoord.xy / 2.0;
  float st = step(0.9975, h(floor(sp))) * (0.5 + 0.5 * sin(uTime * 2.0 + h(floor(sp) + 3.1) * 40.0));
  col += vec3(st) * 0.5 * (1.0 - smoke);
  // vignette and grain
  vec2 v = vUv - 0.5;
  col *= 1.0 - dot(v, v) * 1.1;
  col += (h(gl_FragCoord.xy + uTime) - 0.5) * 0.018;
  o = vec4(max(col, 0.0), 1.0);
}`;

const hex = (s: string) => { const n = parseInt(s.slice(1), 16); return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255]; };

export function VoidField({ tint, tint2 }: { tint: string; tint2: string }) {
  const ref = useRef<HTMLCanvasElement>(null);
  const tintRef = useRef({ a: hex(tint), b: hex(tint2) });
  tintRef.current.a = hex(tint);
  tintRef.current.b = hex(tint2);
  useEffect(() => {
    const canvas = ref.current!;
    const gl = canvas.getContext('webgl2', { antialias: false, alpha: false });
    if (!gl) return;
    const sh = (t: number, src: string) => { const s = gl.createShader(t)!; gl.shaderSource(s, src); gl.compileShader(s); return s; };
    const prog = gl.createProgram()!;
    gl.attachShader(prog, sh(gl.VERTEX_SHADER, VS));
    gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) return;
    gl.useProgram(prog);
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(prog, 'aPos');
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    const U = (n: string) => gl.getUniformLocation(prog, n);
    const uRes = U('uRes'), uTime = U('uTime'), uMouse = U('uMouse'), uTint = U('uTint'), uTint2 = U('uTint2');
    const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    let mouse = [0.5, 0.5], target = [0.5, 0.5];
    const cur = { a: [...tintRef.current.a], b: [...tintRef.current.b] };
    const onMove = (e: PointerEvent) => { target = [e.clientX / window.innerWidth, 1 - e.clientY / window.innerHeight]; };
    window.addEventListener('pointermove', onMove);
    let raf = 0;
    const t0 = performance.now();
    const frame = () => {
      const dpr = Math.min(1.5, window.devicePixelRatio || 1) * 0.6;
      const w = Math.round(canvas.clientWidth * dpr), h = Math.round(canvas.clientHeight * dpr);
      if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
      gl.viewport(0, 0, w, h);
      mouse = [mouse[0] + (target[0] - mouse[0]) * 0.04, mouse[1] + (target[1] - mouse[1]) * 0.04];
      for (let i = 0; i < 3; i++) { cur.a[i] += (tintRef.current.a[i] - cur.a[i]) * 0.05; cur.b[i] += (tintRef.current.b[i] - cur.b[i]) * 0.05; }
      gl.uniform2f(uRes, w, h);
      gl.uniform1f(uTime, reduce ? 20 : (performance.now() - t0) / 1000);
      gl.uniform2f(uMouse, mouse[0], mouse[1]);
      gl.uniform3f(uTint, cur.a[0], cur.a[1], cur.a[2]);
      gl.uniform3f(uTint2, cur.b[0], cur.b[1], cur.b[2]);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      raf = requestAnimationFrame(frame);
    };
    raf = requestAnimationFrame(frame);
    return () => { cancelAnimationFrame(raf); window.removeEventListener('pointermove', onMove); gl.getExtension('WEBGL_lose_context')?.loseContext(); };
  }, []);
  return <canvas ref={ref} class="void-field" aria-hidden="true" />;
}
