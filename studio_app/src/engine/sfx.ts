// Procedural sound effects, synthesised in the page (no sample library needed): whooshes, impacts,
// risers, sub drops and the rest. Deterministic, 48 kHz stereo.
import { SfxType } from '../state/types';

export const SFX_RATE = 48000;

export const SFX_INFO: Record<SfxType, { label: string; dur: number; hint: string }> = {
  whoosh: { label: 'Whoosh', dur: 0.9, hint: 'Air rush that peaks on the cut: whips, pushes, rolls' },
  swish: { label: 'Swish', dur: 0.35, hint: 'Short blade-like pass: slashes, quick wipes' },
  impact: { label: 'Impact', dur: 1.4, hint: 'Heavy hit with a low tail: drops, slams, the logo' },
  hit: { label: 'Hit', dur: 0.45, hint: 'Tight punch: impact frames, beat accents' },
  boom: { label: 'Boom', dur: 2.6, hint: 'Long sub boom for the biggest moment' },
  riser: { label: 'Riser', dur: 2.0, hint: 'Builds tension into a drop; ends on the hit' },
  subdrop: { label: 'Sub drop', dur: 1.3, hint: 'Pitch-falling sub under a drop' },
  reverse: { label: 'Reverse swell', dur: 1.2, hint: 'Sucks into the cut: shadows, burns, reveals' },
  glitch: { label: 'Glitch', dur: 0.5, hint: 'Digital stutter: glitch cuts' },
  shutter: { label: 'Shutter', dur: 0.25, hint: 'Camera shutter / blink' },
  tick: { label: 'Tick', dur: 0.08, hint: 'Small click: text and UI beats' },
  tapestop: { label: 'Tape stop', dur: 0.9, hint: 'Pitch slows to a stop: endings' },
  zap: { label: 'Electric zap', dur: 0.75, hint: 'Lightning crack and crackle: bolts, Speed Force hits' },
  glass: { label: 'Glass', dur: 1.2, hint: 'A crack, then shards tinkling: shatter, a lens breaking' },
  rip: { label: 'Rip', dur: 0.55, hint: 'Plastic or paper tearing: tears, plastic wrap' },
};

/** Seconds from a sound's start to its loudest point (a riser or reverse peaks at its end). */
export const SFX_PEAK: Record<SfxType, number> = { whoosh: 0.56, swish: 0.17, impact: 0.03, hit: 0.02, boom: 0.05, riser: 2.0, subdrop: 0.02, reverse: 1.18, glitch: 0.1, shutter: 0.12, tick: 0, tapestop: 0.1, zap: 0.08, glass: 0.01, rip: 0.12 };
/** Timeline time where a sound effect clip peaks. */
export const sfxPeakAt = (c: { start: number; in?: number; sfx?: SfxType }) => c.start - (c.in ?? 0) + (c.sfx ? SFX_PEAK[c.sfx] : 0);

function rng(seed: number) {
  let s = seed >>> 0;
  return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296 * 2 - 1; };
}

/** Simple state-variable filter, per sample, with time-varying cutoff. */
function svf() {
  let low = 0, band = 0;
  return (x: number, fc: number, q: number) => {
    const f = 2 * Math.sin(Math.PI * Math.min(0.45, fc / SFX_RATE));
    low += f * band;
    const high = x - low - q * band;
    band += f * high;
    return { low, band, high };
  };
}

const cache = new Map<SfxType, { L: Float32Array; R: Float32Array }>();

/** Raw stereo samples of an effect (cached). */
export function sfxData(type: SfxType): { L: Float32Array; R: Float32Array } {
  const hit = cache.get(type);
  if (hit) return hit;
  const dur = SFX_INFO[type].dur;
  const n = Math.round(dur * SFX_RATE);
  const L = new Float32Array(n), R = new Float32Array(n);
  const rnd = rng(type.length * 7919 + type.charCodeAt(0));
  const fl = svf(), fr = svf();
  const T = (i: number) => i / SFX_RATE;
  for (let i = 0; i < n; i++) {
    const t = T(i), u = t / dur;
    let l = 0, r = 0;
    switch (type) {
      case 'whoosh': case 'swish': {
        const peak = type === 'whoosh' ? 0.62 : 0.5;
        const env = u < peak ? (u / peak) ** 2.2 : Math.exp(-(u - peak) * (type === 'whoosh' ? 9 : 14));
        const fc = 300 + 3800 * Math.sin(Math.PI * Math.min(1, u / (peak * 1.6)));
        const a = fl(rnd(), fc, 0.6).band, b = fr(rnd(), fc * 1.07, 0.6).band;
        const pan = -0.8 + 1.6 * u;
        l = a * env * (1 - pan) * 0.9; r = b * env * (1 + pan) * 0.9;
        break;
      }
      case 'impact': case 'hit': case 'boom': {
        const len = type === 'hit' ? 0.12 : type === 'boom' ? 1.1 : 0.45;
        const f0 = type === 'boom' ? 42 : type === 'hit' ? 70 : 55;
        const f = f0 + (type === 'hit' ? 160 : 90) * Math.exp(-t * 30);
        const body = Math.sin(2 * Math.PI * f * t + 2 * Math.sin(2 * Math.PI * 3 * t)) * Math.exp(-t / len);
        const noise = fl(rnd(), 2600 * Math.exp(-t * 6) + 200, 0.9).low * Math.exp(-t * (type === 'hit' ? 40 : 18));
        const v = body * 0.95 + noise * 0.8;
        l = v; r = v * 0.98 + fr(rnd(), 900, 1).band * 0.12 * Math.exp(-t * 8);
        break;
      }
      case 'riser': {
        const env = u ** 2.4;
        const fc = 400 + 7000 * u ** 2;
        const a = fl(rnd(), fc, 0.4).band, b = fr(rnd(), fc * 1.03, 0.4).band;
        const tone = Math.sin(2 * Math.PI * (110 * t + 260 * t * t / dur)) * 0.25;
        l = (a + tone) * env * 0.9; r = (b + tone) * env * 0.9;
        break;
      }
      case 'subdrop': {
        const f = 30 + 120 * Math.exp(-t * 3.2);
        const ph = 2 * Math.PI * (30 * t + (120 / 3.2) * (1 - Math.exp(-t * 3.2)));
        const v = Math.sin(ph) * Math.exp(-t / 0.9) * (1 - Math.exp(-t * 200));
        l = r = v * (f > 0 ? 1 : 0);
        break;
      }
      case 'reverse': {
        const env = u ** 3 * (u < 0.985 ? 1 : (1 - u) / 0.015);
        const a = fl(rnd(), 500 + 5000 * u, 0.5).band, b = fr(rnd(), 520 + 5200 * u, 0.5).band;
        const tone = Math.sin(2 * Math.PI * 220 * t) * 0.2;
        l = (a + tone) * env; r = (b + tone) * env;
        break;
      }
      case 'glitch': {
        const k = Math.floor(t * 38);
        const on = ((k * 2654435761) >>> 0) % 3 !== 0 ? 1 : 0;
        const crush = Math.round(rnd() * 3) / 3;
        const sq = Math.sign(Math.sin(2 * Math.PI * (300 + (k % 5) * 170) * t));
        const v = (crush * 0.5 + sq * 0.35) * on * Math.exp(-u * 2.5);
        l = v; r = (k % 2 ? v : -v) * 0.9;
        break;
      }
      case 'zap': {
        // a sharp crack, then crackle bursts and a fading electrical buzz
        const crack = fl(rnd(), 6000, 0.6).band * Math.exp(-t / 0.012) * 2.2;
        const k = Math.floor(t * 70);
        const burst = ((k * 2654435761) >>> 0) % 4 === 0 ? 1 : 0.15;
        const crackle = fl(rnd(), 3200 + 2400 * Math.exp(-t * 4), 0.75).band * burst * Math.exp(-t / 0.22) * 1.3;
        const buzz = (Math.sign(Math.sin(2 * Math.PI * 120 * t)) * 0.5 + Math.sin(2 * Math.PI * 240 * t) * 0.5) * Math.exp(-t / 0.3) * 0.25;
        const v = crack + crackle + buzz;
        l = v; r = crack + crackle * (k % 2 ? 0.85 : 1.1) + buzz * 0.9;
        break;
      }
      case 'shutter': {
        const c1 = Math.exp(-((t - 0.01) ** 2) / 0.000004), c2 = Math.exp(-((t - 0.11) ** 2) / 0.000006);
        const v = fl(rnd(), 4000, 0.7).band * (c1 + c2 * 0.8) * 3 + Math.sin(2 * Math.PI * 1800 * t) * (c1 + c2) * 0.3;
        l = r = v;
        break;
      }
      case 'tick': {
        const v = Math.sin(2 * Math.PI * 2400 * t) * Math.exp(-t * 90) + rnd() * Math.exp(-t * 300) * 0.4;
        l = r = v * 0.8;
        break;
      }
      case 'glass': {
        // a sharp crack, then bright resonant shards scattered over the tail
        let tink = 0;
        for (let k = 0; k < 14; k++) {
          const t0 = 0.012 + k * 0.034 + ((k * 7919) % 13) * 0.009;
          if (t < t0) continue;
          const dt = t - t0;
          tink += Math.sin(2 * Math.PI * (2600 + ((k * 1931) % 23) * 260) * dt) * Math.exp(-dt * (28 + (k % 5) * 9)) * (1 - k / 18);
        }
        const v = fl(rnd(), 6500, 0.5).high * Math.exp(-t * 55) * 1.6 + tink * 0.35 + rnd() * Math.exp(-t * 18) * 0.22;
        l = v * (0.9 + 0.1 * Math.sin(t * 40)); r = v * (0.9 - 0.1 * Math.sin(t * 37));
        break;
      }
      case 'rip': {
        // a tear: noise stuttering through a rising band filter
        const stutter = 0.55 + 0.45 * Math.sign(Math.sin(2 * Math.PI * (38 + 30 * u) * t));
        const env = Math.min(1, t / 0.02) * Math.exp(-Math.max(0, u - 0.6) * 9);
        const fc = 900 + 3200 * u;
        l = fl(rnd(), fc, 0.8).band * stutter * env * 1.4;
        r = fr(rnd(), fc * 1.1, 0.8).band * stutter * env * 1.4;
        break;
      }
      case 'tapestop': {
        const rate = Math.max(0, 1 - u) ** 1.6;
        const ph = 2 * Math.PI * 180 * (t - (t * u) / 2);
        const v = (Math.sin(ph) * 0.6 + Math.sin(ph * 2.01) * 0.25) * rate;
        l = r = v * (1 - Math.exp(-t * 80));
        break;
      }
    }
    L[i] = l; R[i] = r;
  }
  // normalise each effect to a -3 dBFS peak; the clip volume sets the level in the mix
  let pk = 0;
  for (let i = 0; i < n; i++) pk = Math.max(pk, Math.abs(L[i]), Math.abs(R[i]));
  const k = pk > 0 ? 0.707 / pk : 1;
  // 3 ms fade in/out so cuts never click
  const fade = Math.round(0.003 * SFX_RATE);
  for (let i = 0; i < n; i++) {
    const g = Math.min(1, i / fade, (n - 1 - i) / fade) * k;
    L[i] *= g; R[i] *= g;
  }
  const out = { L, R };
  cache.set(type, out);
  return out;
}

const bufCache = new WeakMap<BaseAudioContext, Map<SfxType, AudioBuffer>>();
export function sfxBuffer(ctx: BaseAudioContext, type: SfxType): AudioBuffer {
  let m = bufCache.get(ctx);
  if (!m) { m = new Map(); bufCache.set(ctx, m); }
  let b = m.get(type);
  if (!b) {
    const d = sfxData(type);
    b = ctx.createBuffer(2, d.L.length, SFX_RATE);
    b.copyToChannel(d.L as Float32Array<ArrayBuffer>, 0);
    b.copyToChannel(d.R as Float32Array<ArrayBuffer>, 1);
    m.set(type, b);
  }
  return b;
}

/** Waveform peaks (100 per second) for the timeline. */
export function sfxPeaks(type: SfxType): Float32Array {
  const d = sfxData(type);
  const per = SFX_RATE / 100;
  const out = new Float32Array(Math.ceil(d.L.length / per));
  for (let i = 0; i < out.length; i++) {
    let pk = 0;
    for (let j = i * per; j < Math.min(d.L.length, (i + 1) * per); j++) pk = Math.max(pk, Math.abs(d.L[j]), Math.abs(d.R[j]));
    out[i] = pk;
  }
  return out;
}

/** The sound a transition gets when sounds are added automatically: [effect, offset from the cut]. */
export function soundsForTransition(type: string, dur: number): [SfxType, number][] {
  const h = dur / 2;
  if (type === 'logo') return [['riser', -h - 1.4], ['impact', -h + 0.3 * dur], ['whoosh', h - 0.62 * 0.9]];
  if (type.startsWith('whip') || type.startsWith('push') || type.startsWith('slide') || type === 'roll' || type === 'spin') return [['whoosh', -0.62 * 0.9]];
  if (type === 'slash' || type.startsWith('wipe') || type === 'iris') return [['swish', -0.17]];
  if (type === 'punch') return [['hit', -0.02]];
  if (type === 'bolt') return [['zap', -h + 0.12 * dur - 0.01]];
  if (type === 'flash' || type === 'dip_white') return [['impact', -0.03]];
  if (type === 'glitch') return [['glitch', -0.25]];
  if (type === 'blink') return [['shutter', -0.12]];
  if (type === 'shadow' || type === 'burn' || type === 'dip_black') return [['reverse', -1.18]];
  if (type === 'ink') return [['reverse', -0.9], ['hit', 0]];
  if (type === 'warp' || type.startsWith('zoom')) return [['whoosh', -0.56], ['subdrop', 0]];
  if (type === 'light_leak') return [['reverse', -0.8]];
  if (type.startsWith('cube')) return [['whoosh', -0.56], ['hit', h - 0.05]];
  if (type.startsWith('flip') || type === 'slices' || type === 'wiper' || type === 'light_sweep') return [['swish', -0.17]];
  if (type === 'shatter') return [['impact', -h + 0.28 * dur - 0.03], ['glass', -h + 0.28 * dur - 0.01]];
  if (type === 'blinds' || type === 'shutter') return [['shutter', -0.12]];
  if (type === 'ripple' || type === 'kaleido' || type === 'heat') return [['reverse', -1.0]];
  if (type === 'swirl') return [['whoosh', -0.56]];
  if (type === 'pixelate' || type === 'datamosh') return [['glitch', -0.25]];
  if (type === 'tear') return [['rip', -0.12]];
  if (type === 'dive') return [['whoosh', -0.56], ['subdrop', 0]];
  if (type === 'wash') return [['impact', -0.03]];
  return [['swish', -0.17]];
}
