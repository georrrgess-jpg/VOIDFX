import { useEffect, useRef } from 'preact/hooks';

// The main menu's living background: a black hole. Gravitational lensing bends a drifting starfield
// into an Einstein ring; a tilted accretion disk spins with Keplerian shear (faster near the hole),
// brighter on the side turning toward the viewer; the far side of the disk is lensed up over the
// shadow; matter spirals in; a thin photon ring outlines the event horizon. It is tinted by the active
// section, leans toward the pointer and spins up when the menu opens.
const VS = `#version 300 es
in vec2 aPos;
void main() { gl_Position = vec4(aPos, 0.0, 1.0); }`;

const FS = `#version 300 es
precision highp float;
out vec4 o;
uniform vec2 uRes; uniform float uTime; uniform vec2 uMouse; uniform vec3 uTint; uniform vec3 uTint2;
uniform float uIntro; uniform vec2 uCenter; uniform float uScale;

float h21(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float n2(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(h21(i), h21(i + vec2(1, 0)), u.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), u.x), u.y); }
float fbm(vec2 p){ float v = 0.0, a = 0.5; mat2 r = mat2(0.8, -0.6, 0.6, 0.8); for (int i = 0; i < 5; i++){ v += a * n2(p); p = r * p * 2.02 + 3.7; a *= 0.5; } return v; }
mat2 rot(float a){ float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }

vec3 stars(vec2 p){
  vec3 col = vec3(0.0);
  for (int L = 0; L < 3; L++){
    float fl = float(L);
    vec2 g = p * (38.0 + fl * 46.0);
    vec2 id = floor(g); vec2 f = fract(g) - 0.5;
    float r = h21(id + fl * 17.0);
    if (r > 0.93) {
      vec2 off = (vec2(h21(id + 3.1), h21(id + 7.7)) - 0.5) * 0.7;
      float d = length(f - off);
      float size = mix(0.035, 0.11, h21(id + 11.0)) * (1.0 - fl * 0.18);
      float tw = 0.6 + 0.4 * sin(uTime * (0.7 + 2.5 * h21(id + 5.0)) + r * 40.0);
      vec3 c = mix(vec3(0.72, 0.84, 1.0), vec3(1.0, 0.86, 0.72), h21(id + 9.0));
      col += c * smoothstep(size, 0.0, d) * tw * (1.25 - fl * 0.3);
    }
  }
  return col;
}

// matter spiralling in: an endless zoom of sparse points in the disk plane
float infall(vec2 q, float t){
  float acc = 0.0;
  for (int i = 0; i < 2; i++){
    float ph = fract(t * 0.05 + float(i) * 0.5);
    float sc = exp2(ph);
    vec2 g = q * sc * 2.6;
    vec2 id = floor(g); vec2 f = fract(g) - 0.5;
    float rnd = h21(id + float(i) * 31.0);
    vec2 off = (vec2(h21(id + 1.3), h21(id + 4.1)) - 0.5) * 0.6;
    float d = length((f - off) * vec2(1.0, 2.2));
    acc += step(0.8, rnd) * sin(ph * 3.14159) * smoothstep(0.07, 0.0, d) * (0.5 + 0.5 * h21(id + 2.2));
  }
  return acc;
}

// accretion disk emission at a point of the disk plane (q in horizon radii)
vec3 diskAt(vec2 q, float t, float rin, float rout, out float mask){
  float dr = length(q);
  float w = 1.9 / pow(max(dr, 0.5), 1.5);
  vec2 qr = rot(-t * w * 0.42) * q;
  float band = smoothstep(rin * 0.92, rin * 1.12, dr) * (1.0 - smoothstep(rout * 0.45, rout, dr));
  float clumps = fbm(qr * 1.35 + 2.0);
  float streak = 0.55 + 0.45 * sin(dr * 9.0 + clumps * 6.0 - t * 0.2);
  float tex = mix(clumps, streak, 0.45);
  float heat = 1.0 - smoothstep(rin, rout * 0.8, dr);
  vec3 hot = mix(vec3(1.0, 0.93, 0.82), uTint, 0.12);
  vec3 warm = mix(vec3(1.0, 0.52, 0.18), uTint2, 0.55);
  vec3 cool = mix(uTint, uTint2, 0.35) * 1.15;
  vec3 c = mix(cool, mix(warm, hot, smoothstep(0.35, 1.0, heat)), smoothstep(0.0, 0.55, heat));
  mask = band;
  float inner = smoothstep(rin * 0.95, rin * 1.25, dr) * (1.0 - smoothstep(rin * 1.25, rin * 2.4, dr));
  return c * band * (0.35 + 1.25 * tex) * (0.55 + heat * 1.2) + hot * inner * 0.35;
}

void main(){
  vec2 uv = (gl_FragCoord.xy - 0.5 * uRes) / uRes.y;
  vec2 m = uMouse - 0.5;
  float intro = smoothstep(0.0, 1.0, uIntro);
  float t = uTime * (0.35 + 0.65 * intro) + (1.0 - intro) * 2.0;
  vec2 c = uCenter + m * vec2(0.035, 0.025);
  vec2 p = (uv - c) / uScale;
  float rs = 0.1 * mix(0.55, 1.0, intro);
  float r = length(p);
  vec2 pr = p / rs;
  float rr = r / rs;

  // ---- the sky, bent by the hole ----
  vec2 bg = p - normalize(p + 1e-5) * (1.75 * rs * rs / max(r, rs * 0.6));
  bg = rot(uTime * 0.006) * bg + vec2(uTime * 0.004, 0.0);
  vec3 sky = stars(bg * uScale * 1.4);
  float neb = fbm(bg * 2.2 + vec2(0.0, uTime * 0.01));
  float neb2 = fbm(bg * 4.0 - neb * 1.4 + 9.0);
  float near = exp(-max(r - rs, 0.0) * 1.8);
  sky += (uTint * 0.10 * smoothstep(0.45, 1.0, neb) + uTint2 * 0.07 * smoothstep(0.55, 1.0, neb2)) * (0.35 + 0.9 * near);
  // light from far away piles up just outside the horizon (Einstein ring)
  sky += mix(uTint, vec3(1.0), 0.5) * 0.25 * exp(-pow((rr - 1.55) * 3.2, 2.0)) * (0.6 + 0.4 * neb);
  float shadow = smoothstep(1.0, 0.94, rr);

  // ---- accretion disk, seen nearly edge-on ----
  float tilt = clamp(0.2 + m.y * 0.08, 0.1, 0.32);
  vec2 dq = vec2(pr.x, pr.y / tilt);
  float rin = 1.55, rout = mix(2.6, 4.3, intro);
  float dmask;
  vec3 disk = diskAt(dq, t, rin, rout, dmask);
  float dl = length(dq);
  float dop = 1.0 + 0.62 * (-dq.x / max(dl, 1e-3));
  disk *= dop * dop;
  disk = mix(disk, disk * vec3(0.85, 0.95, 1.15), clamp(-dq.x / max(dl, 1e-3), 0.0, 1.0) * 0.5);
  float part = infall(rot(-t * 0.5 / pow(max(dl, 0.6), 1.5)) * dq, uTime) * dmask * dop;
  disk += vec3(1.0, 0.92, 0.8) * part * 1.4;
  float front = smoothstep(0.02, -0.02, pr.y);

  // the far half of the disk, lensed up over the top of the shadow (and a thin image under it)
  float ang = atan(pr.y, pr.x);
  float over = smoothstep(-0.25, 0.85, pr.y / max(rr, 1e-3));
  float arcR = 1.0 + 0.55 * over;
  float arc = smoothstep(1.02, 1.12, rr) * (1.0 - smoothstep(arcR, arcR + 0.55 * over + 0.08, rr));
  vec2 aq = vec2(cos(ang), sin(ang)) * (rin + (rr - 1.0) * 2.4);
  float am;
  vec3 arcCol = diskAt(aq, t, rin, rout, am) * (0.35 + 0.65 * over) * (1.0 + 0.5 * (-pr.x / max(rr, 1e-3)));

  float ring = exp(-pow((rr - 1.035) / 0.03, 2.0));
  float halo = exp(-max(rr - 1.0, 0.0) * 1.1);

  vec3 col = sky * (1.0 - shadow);
  col += mix(uTint, uTint2, 0.3) * halo * 0.2 * intro;
  col += disk * (1.0 - front) * (1.0 - shadow) * intro;
  col += arcCol * arc * intro;
  col *= 1.0 - shadow * 0.985;
  col += vec3(1.0, 0.9, 0.78) * ring * (0.55 + 0.45 * sin(ang * 3.0 + t)) * 0.9 * intro;
  col += disk * front * intro;

  // keep the menu's left side calm for reading
  float side = smoothstep(-0.9, 0.25, uv.x - c.x + 0.9);
  col *= mix(0.55, 1.0, side);
  col = 1.0 - exp(-col * 1.35);
  vec2 v = gl_FragCoord.xy / uRes - 0.5;
  col *= 1.0 - dot(v, v) * 0.9;
  col += (h21(gl_FragCoord.xy + fract(uTime) * 91.0) - 0.5) * 0.016;
  o = vec4(max(col, 0.0) + vec3(0.006, 0.006, 0.011), 1.0);
}`;

const hex = (s: string) => { const n = parseInt(s.slice(1), 16); return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255]; };

export function VoidField({ tint, tint2 }: { tint: string; tint2: string }) {
  const ref = useRef<HTMLCanvasElement>(null);
  const tintRef = useRef({ a: hex(tint), b: hex(tint2) });
  tintRef.current.a = hex(tint);
  tintRef.current.b = hex(tint2);
  useEffect(() => {
    const canvas = ref.current!;
    const gl = canvas.getContext('webgl2', { antialias: false, alpha: false, powerPreference: 'low-power' });
    if (!gl) { canvas.classList.add('no-gl'); return; }
    const sh = (t: number, src: string) => { const s = gl.createShader(t)!; gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) console.warn(gl.getShaderInfoLog(s)); return s; };
    const prog = gl.createProgram()!;
    gl.attachShader(prog, sh(gl.VERTEX_SHADER, VS));
    gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) { canvas.classList.add('no-gl'); return; }
    gl.useProgram(prog);
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(prog, 'aPos');
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    const U = (n: string) => gl.getUniformLocation(prog, n);
    const uRes = U('uRes'), uTime = U('uTime'), uMouse = U('uMouse'), uTint = U('uTint'), uTint2 = U('uTint2'), uIntro = U('uIntro'), uCenter = U('uCenter'), uScale = U('uScale');
    const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    let mouse = [0.5, 0.5], target = [0.5, 0.5];
    const cur = { a: [...tintRef.current.a], b: [...tintRef.current.b] };
    const onMove = (e: PointerEvent) => { target = [e.clientX / window.innerWidth, 1 - e.clientY / window.innerHeight]; };
    window.addEventListener('pointermove', onMove, { passive: true });
    let raf = 0;
    let quality = 0.62; // render scale, lowered automatically on slow machines
    let slow = 0, frames = 0, last = performance.now();
    const t0 = performance.now();
    const frame = () => {
      raf = requestAnimationFrame(frame);
      if (document.hidden) return;
      const now = performance.now();
      const dt = now - last;
      last = now;
      frames++;
      if (frames > 30 && dt > 26) { if (++slow > 20 && quality > 0.34) { quality = Math.max(0.34, quality - 0.08); slow = 0; } } else slow = Math.max(0, slow - 1);
      const dpr = Math.min(1.5, window.devicePixelRatio || 1) * quality;
      const cw = canvas.clientWidth, ch = canvas.clientHeight;
      const w = Math.max(2, Math.round(cw * dpr)), h = Math.max(2, Math.round(ch * dpr));
      if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
      gl.viewport(0, 0, w, h);
      mouse = [mouse[0] + (target[0] - mouse[0]) * 0.035, mouse[1] + (target[1] - mouse[1]) * 0.035];
      for (let i = 0; i < 3; i++) { cur.a[i] += (tintRef.current.a[i] - cur.a[i]) * 0.04; cur.b[i] += (tintRef.current.b[i] - cur.b[i]) * 0.04; }
      const aspect = cw / Math.max(1, ch);
      // wide screens: the hole sits right of the content; phones: above the hero, smaller
      const wide = aspect > 1.15;
      const cx = wide ? Math.min(aspect * 0.5 - 0.34, 0.275 * aspect) : 0;
      const cy = wide ? 0.14 : 0.36;
      const scale = wide ? Math.min(1.0, 0.7 + aspect * 0.16) : 0.5;
      const secs = (now - t0) / 1000;
      gl.uniform2f(uRes, w, h);
      gl.uniform1f(uTime, reduce ? secs * 0.15 : secs);
      gl.uniform2f(uMouse, mouse[0], mouse[1]);
      gl.uniform3f(uTint, cur.a[0], cur.a[1], cur.a[2]);
      gl.uniform3f(uTint2, cur.b[0], cur.b[1], cur.b[2]);
      gl.uniform1f(uIntro, reduce ? 1 : Math.min(1, secs / 2.6));
      gl.uniform2f(uCenter, cx, cy);
      gl.uniform1f(uScale, scale);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    };
    raf = requestAnimationFrame(frame);
    return () => { cancelAnimationFrame(raf); window.removeEventListener('pointermove', onMove); gl.getExtension('WEBGL_lose_context')?.loseContext(); };
  }, []);
  return <canvas ref={ref} class="void-field" aria-hidden="true" />;
}
