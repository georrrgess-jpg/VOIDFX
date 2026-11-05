// Starter effects and graphics: a palette the owner can drop in and tweak, and worked examples of the
// custom-layer API. Opus writes its own for each edit; these only show what the tools can do.
import { BlendMode, GraphicReveal } from '../state/types';

export interface FxPreset {
  id: string;
  name: string;
  kind: 'shader' | 'graphic';
  hint: string;
  dur: number;
  blend: BlendMode;
  code?: string;
  svg?: string;
  gw?: number;
  glow?: number;
  reveal?: Partial<GraphicReveal>;
}

const radialLines = (() => {
  let d = '';
  for (let i = 0; i < 48; i++) {
    const a = (i / 48) * Math.PI * 2 + (i % 3) * 0.02;
    const r0 = 260 + ((i * 37) % 90), r1 = 500;
    d += `M${(500 + Math.cos(a) * r0).toFixed(1)} ${(500 + Math.sin(a) * r0).toFixed(1)}L${(500 + Math.cos(a) * r1).toFixed(1)} ${(500 + Math.sin(a) * r1).toFixed(1)}`;
  }
  return d;
})();

export const FX_PRESETS: FxPreset[] = [
  {
    id: 'lightning-arc', name: 'Lightning arc', kind: 'shader', blend: 'add', dur: 0.6,
    hint: 'A flickering forked arc around the anchor (move it with Position X/Y), pulsing on the beat.',
    code: `vec4 effect(vec2 uv, float t, float p) {
  vec2 q = toLocal(uv);
  float seed = floor(t * 14.0);
  float d = boltDist(q, vec2(-0.16, -0.42), vec2(0.14, 0.36), seed, 0.3);
  float d2 = boltDist(q, vec2(-0.02, -0.06), vec2(0.22, 0.12), seed + 3.0, 0.4);
  float core = glow(min(d, d2 + 0.004) - 0.002, 0.003);
  float halo = glow(d, 0.035) * 0.55 + glow(d2, 0.02) * 0.3;
  float life = smoothstep(0.0, 0.08, p) * smoothstep(1.0, 0.7, p) * (0.65 + 0.35 * step(0.3, hash11(floor(t * 24.0))));
  float a = (core + halo) * life * (0.7 + 0.3 * uBeat);
  return vec4(mix(vec3(1.0, 0.72, 0.18), vec3(1.0), clamp(core, 0.0, 1.0)), a);
}`,
  },
  {
    id: 'speed-force', name: 'Speed Force pull', kind: 'shader', blend: 'normal', dur: 0.7,
    hint: 'Warps the picture toward the anchor with golden energy streaks: a custom transition over a cut.',
    code: `vec4 effect(vec2 uv, float t, float p) {
  vec2 d = uv - uPos;
  float r = length(d * vec2(uAspect, 1.0));
  float k = 0.5 * sin(p * PI);
  vec3 col = vec3(0.0);
  for (int i = 0; i < 12; i++) { float f = float(i) / 11.0; col += frame(uPos + d * (1.0 - k * f * 0.35)); }
  col /= 12.0;
  float streak = fbm(vec2(atan(d.y, d.x) * 4.0, r * 6.0 - t * 9.0));
  col += vec3(1.0, 0.78, 0.3) * smoothstep(0.55, 0.9, streak) * k * 0.8;
  return vec4(col, 1.0);
}`,
  },
  {
    id: 'speed-streaks', name: 'Speed streaks', kind: 'shader', blend: 'add', dur: 1.0,
    hint: 'Light streaks racing across the frame; Rotation sets their direction.',
    code: `vec4 effect(vec2 uv, float t, float p) {
  vec2 q = rot2(-0.35 + uRot) * aspectUv(uv);
  float lane = floor(q.y * 70.0);
  float s = fract(q.x * 1.5 - t * (3.0 + hash11(lane) * 4.0) + hash11(lane + 3.0));
  float line = smoothstep(0.0, 0.02, s) * smoothstep(0.35, 0.0, s) * step(0.82, hash11(lane + 7.0));
  return vec4(vec3(1.0, 0.85, 0.5), line * 0.7 * sin(p * PI));
}`,
  },
  {
    id: 'edge-lightning', name: 'Electric edges', kind: 'shader', blend: 'add', dur: 0.8,
    hint: 'The outlines in the shot crackle with gold electricity, strongest on the beat.',
    code: `vec4 effect(vec2 uv, float t, float p) {
  float a = 0.0;
  for (int i = 0; i < 3; i++) {
    vec2 px = (2.0 + float(i) * 3.0) * vec2(1.0 / uAspect, 1.0) / 1080.0;
    float gx = luma(frame(uv + vec2(px.x, 0.0))) - luma(frame(uv - vec2(px.x, 0.0)));
    float gy = luma(frame(uv + vec2(0.0, px.y))) - luma(frame(uv - vec2(0.0, px.y)));
    a += smoothstep(0.06, 0.35, length(vec2(gx, gy))) * (1.0 - float(i) * 0.3);
  }
  float flick = 0.5 + 0.5 * noise(uv * vec2(30.0, 60.0) + floor(t * 20.0));
  a = clamp(a * 0.6, 0.0, 1.0) * flick * (0.5 + 0.5 * uBeat) * sin(p * PI);
  return vec4(mix(vec3(1.0, 0.75, 0.25), vec3(1.0), a * 0.5), a);
}`,
  },
  {
    id: 'ghost-echo', name: 'Ghost echo', kind: 'shader', blend: 'normal', dur: 0.8,
    hint: 'Warm afterimages of the whole frame trailing behind the motion; Rotation sets the direction.',
    code: `vec4 effect(vec2 uv, float t, float p) {
  float k = sin(p * PI);
  vec2 dir = vec2(cos(uRot), sin(uRot)) * 0.035 * k;
  vec3 base = frame(uv);
  vec3 col = base;
  for (int i = 1; i < 6; i++) {
    float f = float(i);
    col = max(col, frame(uv - dir * f) * vec3(1.0, 0.75, 0.35) * (1.0 - f / 6.0) * 0.9);
  }
  return vec4(mix(base, col, k), 1.0);
}`,
  },
  {
    id: 'beat-ring', name: 'Beat shockwave', kind: 'shader', blend: 'add', dur: 1.5,
    hint: 'An energy ring bursts from the anchor on every music beat.',
    code: `vec4 effect(vec2 uv, float t, float p) {
  vec2 q = toLocal(uv);
  float r = length(q);
  float age = uBeatAge;
  float ring = glow(abs(r - (0.05 + age * 0.9)) - 0.004, 0.012) * exp(-age * 3.5);
  float inner = glow(abs(r - (0.03 + age * 0.5)) - 0.002, 0.006) * exp(-age * 5.0) * 0.6;
  float n = fbm(vec2(atan(q.y, q.x) * 3.0, t * 2.0));
  float a = (ring * (0.6 + 0.6 * n) + inner) * sin(p * PI);
  return vec4(vec3(1.0, 0.8, 0.35), clamp(a, 0.0, 1.0));
}`,
  },
  {
    id: 'sparks', name: 'Rising sparks', kind: 'shader', blend: 'add', dur: 1.2,
    hint: 'Embers drifting up through the frame.',
    code: `vec4 effect(vec2 uv, float t, float p) {
  vec2 q = aspectUv(uv);
  float a = 0.0;
  for (int i = 0; i < 24; i++) {
    float f = float(i);
    float life = fract(t * (0.4 + hash11(f + 3.0) * 0.6) + hash11(f + 7.0));
    vec2 pos = vec2((hash11(f) - 0.5) * 0.6 + sin(life * 6.0 + f) * 0.02, 0.5 - life * 1.1);
    a += glow(length(q - pos) - 0.002, 0.004) * (1.0 - life);
  }
  return vec4(vec3(1.0, 0.7, 0.3), clamp(a, 0.0, 1.0) * sin(p * PI));
}`,
  },
  {
    id: 'chroma-punch', name: 'Chroma punch', kind: 'shader', blend: 'normal', dur: 0.35,
    hint: 'A quick zoom with a red-blue split: a hit frame on a beat.',
    code: `vec4 effect(vec2 uv, float t, float p) {
  float k = sin(p * PI);
  vec2 z = (uv - 0.5) * (1.0 - 0.06 * k) + 0.5;
  float s = 0.012 * k;
  return vec4(frame(z + vec2(s, 0.0)).r, frame(z).g, frame(z - vec2(s, 0.0)).b, 1.0);
}`,
  },
  {
    id: 'emblem', name: 'Lightning emblem', kind: 'graphic', blend: 'normal', dur: 1.4, gw: 0.5, glow: 0.7,
    reveal: { in: 'pop', out: 'flicker', inDur: 0.35, outDur: 0.3 },
    hint: 'A gold bolt in a ring, popping in with a glow.',
    svg: `<svg viewBox="0 0 400 400"><defs><radialGradient id="g"><stop offset="0" stop-color="#fff6c8"/><stop offset="1" stop-color="#ffb000"/></radialGradient></defs><circle cx="200" cy="200" r="180" fill="none" stroke="#ffd23f" stroke-width="18"/><path d="M230 40 L120 220 L195 220 L160 360 L290 160 L210 160 Z" fill="url(#g)" stroke="#fff" stroke-width="6" stroke-linejoin="round"/></svg>`,
  },
  {
    id: 'bolt', name: 'Bolt', kind: 'graphic', blend: 'add', dur: 0.5, gw: 0.35, glow: 0.9,
    reveal: { in: 'flicker', out: 'fade', inDur: 0.12, outDur: 0.25 },
    hint: 'A jagged lightning bolt with a white core.',
    svg: `<svg viewBox="0 0 200 600"><path d="M120 0 L70 210 L120 220 L40 420 L95 430 L30 600 L150 370 L100 360 L170 170 L115 160 L160 0 Z" fill="#ffe7a0" stroke="#ffb000" stroke-width="6" stroke-linejoin="round"/><path d="M128 20 L88 210 L130 220 L62 410 L108 420 L64 540" fill="none" stroke="#ffffff" stroke-width="7" stroke-linecap="round"/></svg>`,
  },
  {
    id: 'speed-burst', name: 'Speed lines', kind: 'graphic', blend: 'add', dur: 0.6, gw: 1.6, glow: 0.2,
    reveal: { in: 'pop', out: 'fade', inDur: 0.15, outDur: 0.3 },
    hint: 'Manga-style radial speed lines that frame a hit.',
    svg: `<svg viewBox="0 0 1000 1000"><path d="${radialLines}" stroke="#ffffff" stroke-opacity="0.85" stroke-width="5" stroke-linecap="round"/></svg>`,
  },
  {
    id: 'slide', name: 'Blood slide', kind: 'graphic', blend: 'normal', dur: 1.2, gw: 0.55, glow: 0.15,
    reveal: { in: 'pop', out: 'fade', inDur: 0.3, outDur: 0.25 },
    hint: 'A lit glass slide with a drop of blood (keep it off faces and motivated by the shot).',
    svg: `<svg viewBox="0 0 600 220"><defs><linearGradient id="gl" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e8f4ff" stop-opacity="0.55"/><stop offset="0.5" stop-color="#bcd6ea" stop-opacity="0.25"/><stop offset="1" stop-color="#ffffff" stop-opacity="0.5"/></linearGradient><radialGradient id="bd" cx="0.4" cy="0.35"><stop offset="0" stop-color="#ff4a4a"/><stop offset="0.6" stop-color="#a30010"/><stop offset="1" stop-color="#4a0006"/></radialGradient></defs><rect x="6" y="6" width="588" height="208" rx="10" fill="url(#gl)" stroke="#ffffff" stroke-opacity="0.7" stroke-width="3"/><rect x="20" y="20" width="120" height="180" rx="4" fill="#ffffff" fill-opacity="0.18"/><ellipse cx="340" cy="112" rx="70" ry="52" fill="url(#bd)"/><ellipse cx="318" cy="94" rx="18" ry="10" fill="#ffffff" fill-opacity="0.45"/></svg>`,
  },
];
