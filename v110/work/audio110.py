"""[SLEEPWALKER — Dexter × Sleepwalker (Slowed) (voidfx v110) — ported from the v109 engine; rewrite the sound design below]
Previous edit: [PHANTOM — Dexter × EsDeeKid & Rico Ace (voidfx v109) — ported from the v108 engine; rewrite the sound design below]
Previous edit: [DOOMSDAY (voidfx v108) — ported from the v107 engine; rewrite the sound design below]
Previous edit: [ALL CAPS — Dexter × Madvillain "All Caps" (voidfx v107) — ported from the v12 engine; rewrite the sound design below]
Previous edit: BLOOM (voidfx v12) soundtrack: see the v12 section near the end (music12, main).
Previous edit: [BOP — The Flash × DaBaby (voidfx v11) — ported from the v10 engine; rewrite the sound design below]
Previous edit: LET IT HAPPEN (voidfx v10) soundtrack. Tame Impala "Let It Happen" (radio edit) h392 -> h496 (94.32 -> 119.28 s):
the bass-less "whirlwind" breakdown, the drop on "...when it happens", "let it happen", the song's own gated stutter
(time freeze), "All this running around". The last 0.96 s is the song rewinding at speed from 118.3 s back to 94.32 s
(the loop: he outruns time and lands back at the start). Electrical crackles, speed passes and impacts sit only on
the moments that matter; the stutter's gaps get a clock tick. Built circularly, mastered on a wrapped copy,
measured after AAC. (Engine: v7-v9 audio builder.)
"""
import os, sys, math, subprocess
import numpy as np, scipy.io.wavfile as wf, scipy.signal as ss
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/home/user/VOIDFX/v2/work")
import edl110 as E
import audio2 as A2

SR = 48000; AD = f"{E.ROOT}/{E.VER}/audio"
N = int(round(E.DUR_F / E.FPS * SR))
PRE = 4800
def I(t): return int(round(t * SR))
db, bq, noise, env_exp = A2.db, A2.bq, A2.noise, A2.env_exp
FX_EVENTS = []                         # every effect main() places -> vN/audio/fx_events.json (read by the plan check; from audio12)
def place(out, sig, t):
    fr = sys._getframe(1)
    if "music" not in fr.f_code.co_name:
        ln = open(fr.f_code.co_filename).read().split("\n")[fr.f_lineno - 1].strip()[:140]
        FX_EVENTS.append([round(float(t), 3), round(len(sig) / SR, 3), round(float(20 * np.log10(np.abs(sig).max() + 1e-9)), 1), fr.f_code.co_name, fr.f_lineno, ln])
    A2.place(out, sig if sig.ndim == 2 else np.stack([sig, sig], 1), I(t) + PRE)
def _write_fx_events():
    if FX_EVENTS:
        import json; os.makedirs(AD, exist_ok=True); json.dump(FX_EVENTS, open(f"{AD}/fx_events.json", "w"))
import atexit; atexit.register(_write_fx_events)
def stereo(x, pan=0.0): return np.stack([x * (1 - 0.5 * pan), x * (1 + 0.5 * pan)], 1).astype(np.float32)
def norm(y, level): return (y / (np.abs(y).max() + 1e-9) * db(level)).astype(np.float32)
T = {s["n"]: s for s in E.SHOTS}

# ------------------------------------------------------------------ VHS / transition sounds
def static_hiss(dur, level=-22, seed=1):
    n = I(dur); x = noise(n, seed)
    x = bq(x, "band", np.array([900, 12000]), 2) + 0.35 * bq(noise(n, seed + 1), "low", 400, 2)
    x = x * (1 + 0.25 * np.sign(np.sin(2 * np.pi * 59.94 * np.arange(n) / SR)))      # field-rate buzz in the snow
    return stereo(norm(x, level), 0.0) * np.array([[1.0, 0.97]], np.float32)

def vcr_clunk(level=-17, seed=3):
    n = I(0.35); t = np.arange(n) / SR
    thump = np.sin(2 * np.pi * np.cumsum(90 * np.exp(-t / 0.05) + 45) / SR) * env_exp(n, 0.06, 0.001)
    click = bq(noise(n, seed), "band", np.array([1500, 6000]), 2) * env_exp(n, 0.008, 0.0002)
    click2 = np.roll(click, I(0.045)) * 0.6
    return norm(thump + 0.7 * click + click2, level)

def motor(dur=0.45, level=-28, seed=4):
    n = I(dur); t = np.arange(n) / SR; u = t / dur
    f = 40 + 140 * u ** 0.7
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.4 * np.sin(2 * np.pi * np.cumsum(2 * f) / SR)
    y = y + 0.3 * bq(noise(n, seed), "band", np.array([800, 3000]), 2)
    return norm(y * np.sin(np.pi * np.minimum(u * 1.6, 1)) ** 1.2 * (1 - u ** 4), level)

def scrub(dur=0.14, level=-21, seed=5, top=5000):
    """tape rewind squeal: noise through a rapidly wobbling band-pass + chirps."""
    n = I(dur); t = np.arange(n) / SR; x = noise(n, seed); out = np.zeros(n, np.float32); blk = 256
    for i in range(0, n, blk):
        fc = 1400 + (top - 1400) * (0.5 + 0.5 * math.sin(2 * math.pi * 22 * t[i])) * (0.6 + 0.4 * t[i] / dur)
        sos = ss.butter(2, [fc / 1.3 / (SR / 2), min(0.95, fc * 1.3 / (SR / 2))], "band", output="sos")
        seg = x[max(0, i - 1024):i + blk]; y = ss.sosfilt(sos, seg)[-min(blk, n - i):]; out[i:i + len(y)] = y
    chirp = np.sin(2 * np.pi * np.cumsum(2200 + 1800 * np.sin(2 * np.pi * 15 * t)) / SR) * 0.25
    e = np.minimum(1, t / 0.01) * np.minimum(1, (dur - t) / 0.01)
    return norm((out + chirp) * e, level)

def flash_pop(level=-19, seed=6):
    n = I(0.32); t = np.arange(n) / SR
    whine = np.sin(2 * np.pi * np.cumsum(3000 + 5000 * (t / 0.16)) / SR) * (t < 0.16) * (t / 0.16) ** 2 * 0.25
    pop = bq(noise(n, seed), "high", 1200, 2) * env_exp(n, 0.03, 0.0003) * (t >= 0.16)
    thud = np.sin(2 * np.pi * 70 * t) * env_exp(n, 0.07, 0.001) * (t >= 0.16) * 0.8
    return norm(whine + pop + thud, level)                        # pop lands 0.16 s in

def crumble(dur=0.85, level=-22, seed=7):
    """digital disintegration: bit-crushed grains sweeping left -> right (the blocks blow off to the right)."""
    n = I(dur); out = np.zeros((n, 2), np.float32); rng = np.random.default_rng(seed)
    for g in range(260):
        u = rng.uniform(0, 1) ** 0.8; i = int(u * (n - I(0.03))); m = I(rng.uniform(0.006, 0.02))
        f = rng.uniform(1200, 6500) * (1 - 0.4 * u); tt = np.arange(m) / SR
        y = np.sign(np.sin(2 * np.pi * f * tt)) * np.exp(-tt / (m / SR / 3)) * rng.uniform(0.3, 1.0)
        pan = -0.8 + 1.6 * u + rng.uniform(-0.2, 0.2)
        out[i:i + m, 0] += y * (1 - 0.5 * pan); out[i:i + m, 1] += y * (1 + 0.5 * pan)
    sweep = np.sin(2 * np.pi * np.cumsum(1800 * np.exp(-np.arange(n) / SR / 0.35) + 200) / SR) * np.sin(np.pi * np.arange(n) / n) * 0.25
    out += stereo(sweep.astype(np.float32))
    out = bq(out, "high", 300, 2)
    return out / (np.abs(out).max() + 1e-9) * db(level)

def drip(level=-17, seed=8):
    """blood drop: falling whistle -> plip -> splash -> low thud (impact at 0.13 s)."""
    n = I(0.7); t = np.arange(n) / SR; ti = 0.13
    fall = np.sin(2 * np.pi * np.cumsum(900 - 500 * np.clip(t / ti, 0, 1)) / SR) * (t < ti) * (t / ti) ** 3 * 0.12
    tp = np.clip(t - ti, 0, None)
    plip = np.sin(2 * np.pi * np.cumsum(np.where(t >= ti, 1500 * np.exp(-tp / 0.012) + 350, 0)) / SR) * np.exp(-tp / 0.03) * (t >= ti)
    splash = bq(noise(n, seed), "band", np.array([400, 4000]), 2) * np.exp(-tp / 0.08) * (t >= ti) * 0.5
    thud = np.sin(2 * np.pi * 55 * tp) * np.exp(-tp / 0.18) * (t >= ti) * 0.9
    return norm(fall + plip + splash + thud, level)

def bloop(level=-20, seed=9):
    n = I(0.5); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * np.cumsum(220 + 700 * (1 - np.exp(-t / 0.05))) / SR) * env_exp(n, 0.09, 0.002)
    rng = np.random.default_rng(seed)
    for j in range(6):
        i = I(0.08 + 0.05 * j + rng.uniform(0, 0.02)); m = I(0.03); tt = np.arange(m) / SR
        y[i:i + m] += np.sin(2 * np.pi * np.cumsum(600 + 1400 * tt / 0.03 + 200 * j) / SR) * np.exp(-tt / 0.01) * 0.35
    return norm(y, level)

def melt_sweep(dur=0.32, level=-21, seed=10):
    n = I(dur); u = np.arange(n) / n; x = noise(n, seed); out = np.zeros(n, np.float32); blk = 512
    for i in range(0, n, blk):
        fc = 6000 * (300 / 6000) ** u[i]
        sos = ss.butter(2, [fc / 1.5 / (SR / 2), min(0.95, fc * 1.5 / (SR / 2))], "band", output="sos")
        seg = x[max(0, i - 2048):i + blk]; y = ss.sosfilt(sos, seg)[-min(blk, n - i):]; out[i:i + len(y)] = y
    out = np.repeat(out[::12], 12)[:n]                             # sample-and-hold crunch
    return stereo(norm(out * np.sin(np.pi * u) ** 1.2, level), -0.2)

def degauss(level=-18):
    n = I(1.0); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * np.cumsum(62 - 18 * t) / SR) * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * t)) * env_exp(n, 0.35, 0.004)
    y = y + 0.4 * bq(noise(n, 11), "band", np.array([150, 900]), 2) * env_exp(n, 0.08, 0.001)
    return norm(y, level)

def neon_buzz(dur=0.4, level=-27, pattern=(1, 0, 1, 1, 0, 1, 1, 1)):
    n = I(dur); t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * 120 * k * t) / k for k in range(1, 10)) + 0.4 * bq(noise(n, 12), "band", np.array([2500, 8000]), 2)
    g = np.zeros(n, np.float32); fpf = SR / E.FPS
    for i, v in enumerate(pattern): g[int(i * fpf):int((i + 1) * fpf)] = v
    g[int(len(pattern) * fpf):] = 1.0
    g = np.convolve(g, np.ones(96) / 96, "same") * np.minimum(1, (dur - t) / 0.08)
    return norm(s * g, level)

def ting(level=-34, seed=0):
    n = I(0.35); t = np.arange(n) / SR; f = 3500 + 900 * (seed % 3)
    return norm((np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.5 * t)) * env_exp(n, 0.08, 0.001), level)

def soft_tick(level=-38, seed=0):
    n = I(0.03); y = bq(noise(n, 300 + seed), "band", np.array([3000, 9000]), 2) * env_exp(n, 0.006, 0.0005)
    return norm(y, level)

# ------------------------------------------------------------------ rev 2 transition sounds
def heartbeat(level=-16):
    n = I(0.5); t = np.arange(n) / SR; y = np.zeros(n, np.float32)
    for t0, a in ((0.0, 1.0), (0.17, 0.7)):
        tt = np.clip(t - t0, 0, None); y += a * np.sin(2 * np.pi * 52 * tt) * np.exp(-tt / 0.07) * (t >= t0)
    return norm(bq(y, "low", 200, 2), level)

def shutter_ticks(level=-24, n_=4, gap=0.03, seed=50):
    n = I(gap * n_ + 0.05); y = np.zeros(n, np.float32)
    for i in range(n_):
        m = I(0.012); i0 = I(i * gap); y[i0:i0 + m] += bq(noise(m, seed + i), "band", np.array([2500, 9000]), 2) * env_exp(m, 0.003, 0.0002)
    return norm(y, level)

def metal_shing(level=-19, dur=0.7):
    n = I(dur); t = np.arange(n) / SR
    y = sum(a * np.sin(2 * np.pi * f * t + i) * np.exp(-t / d) for i, (f, a, d) in enumerate(((2137, 1.0, 0.30), (3411, 0.7, 0.22), (5233, 0.5, 0.16), (7810, 0.35, 0.10), (1290, 0.4, 0.25))))
    y = y * np.minimum(1, t / 0.002) + bq(noise(n, 51), "high", 4000, 2) * env_exp(n, 0.04, 0.0005) * 0.6
    return norm(y, level)

def swish(level=-18, dur=0.13, seed=52):
    n = I(dur); u = np.arange(n) / n; x = noise(n, seed); out = np.zeros(n, np.float32); blk = 256
    for i in range(0, n, blk):
        fc = 1500 * (9000 / 1500) ** u[i]
        sos = ss.butter(2, [fc / 1.4 / (SR / 2), min(0.95, fc * 1.4 / (SR / 2))], "band", output="sos")
        seg = x[max(0, i - 1024):i + blk]; y = ss.sosfilt(sos, seg)[-min(blk, n - i):]; out[i:i + len(y)] = y
    return norm(out * np.sin(np.pi * u) ** 0.8, level)

def chord_swell(level=-24, dur=0.9, freqs=(523.25, 659.25, 783.99, 1046.5)):
    n = I(dur); t = np.arange(n) / SR
    y = sum(np.sin(2 * np.pi * f * t + 0.3 * np.sin(2 * np.pi * 5 * t)) for f in freqs)
    return norm(y * np.minimum(1, t / 0.06) * np.exp(-t / (dur * 0.45)), level)

def glass_chime(level=-26):
    n = I(0.9); t = np.arange(n) / SR
    y = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / d) for f, a, d in ((1975, 1.0, 0.4), (3136, 0.6, 0.3), (4699, 0.4, 0.2), (2637, 0.5, 0.35)))
    return norm(y * np.minimum(1, t / 0.003), level)

def fire_whoosh(level=-20, dur=0.5, seed=53):
    n = I(dur); t = np.arange(n) / SR
    y = bq(noise(n, seed), "low", 1800, 2) * np.sin(np.pi * t / dur) ** 1.5
    rng = np.random.default_rng(seed); crk = np.zeros(n, np.float32)
    for _ in range(70):
        i = int(rng.uniform(0, 0.9) * n); m = I(0.003); crk[i:i + m] += rng.uniform(0.3, 1) * bq(noise(m, int(rng.integers(1e6))), "high", 2000, 2)
    return norm(y + 0.5 * crk, level)

def rev(x): return x[::-1].copy()

def measure(p):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", p, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(r.split("Integrated loudness:")[1].split("I:")[1].split("LUFS")[0]), float(r.split("True peak:")[1].split("Peak:")[1].split("dBFS")[0])

# ================================================================== v9 NIGHT BLOOM soundtrack
def song_read():
    if not os.path.exists(f"{AD}/song48.wav"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", E.SONG, "-ar", "48000", "-ac", "2", "-c:a", "pcm_f32le", f"{AD}/song48.wav"], check=True)
    if not os.path.exists(f"{AD}/inst48.wav"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{E.SONG_STEMS}/no_vocals.wav", "-ar", "48000", "-ac", "2", "-c:a", "pcm_f32le", f"{AD}/inst48.wav"], check=True)
    _, song = wf.read(f"{AD}/song48.wav"); _, inst = wf.read(f"{AD}/inst48.wav")
    return song.astype(np.float32), inst.astype(np.float32)

VOX_OUT = 147.42                       # song A's vocal ends after "...so really rich" -> instrumental stem to the splice
def music_track(song, inst):
    """segment A (breakdown -> silence -> drop) + segment B ("I swear I'm on a mission ... Yasmin"), spliced on the
    downbeat where the 4-bar instrumental cycle repeats; A's last 0.42 s is the instrumental stem (no cut-off word)."""
    n = N + PRE; out = np.zeros((n, 2), np.float32); tt = (np.arange(n) - PRE) / SR
    (a0, a1, at0), (b0, b1, bt0) = E.SONG_SEGS
    def take(src, s0, t_edit):
        x = (s0 + t_edit) * SR; i = np.clip(np.floor(x).astype(np.int64), 0, len(src) - 2); fr = (x - i)[:, None].astype(np.float32)
        return src[i] * (1 - fr) + src[i + 1] * fr
    tA = tt - at0; tB = np.clip(tt - bt0, 0, None)                                      # A runs into the pre-roll: the pad continues across the wrap
    A = take(song, a0, tA); Ai = take(inst, a0, tA); Bm = take(song, b0, tB)
    xf = I(0.012); sp = PRE + I(bt0)
    v_out = np.clip((VOX_OUT - (a0 + tt)) / 0.05, 0, 1)[:, None]                            # A's vocal out, 50 ms, on a breath
    A = A * v_out + Ai * (1 - v_out)
    th_ = np.linspace(0, np.pi / 2, xf)[:, None]
    out[:sp - xf] = A[:sp - xf]
    out[sp - xf:sp] = A[sp - xf:sp] * np.cos(th_) + Bm[sp - xf:sp] * np.sin(th_)
    out[sp:] = Bm[sp:]
    return out

def lowpass_sweep(x, t0, t1, f0, f1, back=None):
    """time-varying low-pass (block-wise), f0 -> f1 between t0 and t1 (edit s); back=(t2, t3) sweeps open again."""
    y = x.copy(); blk = 480; sos_state = None
    for i in range(PRE + I(t0) - blk * 4, len(x), blk):
        t = (i - PRE) / SR
        if t <= t1: u = clamp_((t - t0) / (t1 - t0)); fc = f0 * (f1 / f0) ** u
        elif back is None: fc = f1
        elif t > back[1]: break
        elif t < back[0]: fc = f1
        else: u = clamp_((t - back[0]) / (back[1] - back[0])); fc = f1 * (f0 / f1) ** u
        sos = ss.butter(2, min(0.95, fc / (SR / 2)), "low", output="sos")
        seg = x[max(0, i - 4096):i + blk]; z = ss.sosfilt(sos, seg, axis=0)[-min(blk, len(x) - i):]
        if t < t0: w = 0.0
        else: w = 1.0
        y[i:i + len(z)] = z * w + x[i:i + len(z)] * (1 - w)
    return y
def clamp_(u): return max(0.0, min(1.0, u))

def vo_track():
    vo = np.zeros((N + PRE, 2), np.float32); duck = np.zeros(N + PRE, np.float32)
    for k, (stem, s0, a, b, at) in enumerate(E.VO):
        sr, v = wf.read(stem); v = v.astype(np.float32)
        if np.abs(v).max() > 2: v /= 32768
        if sr != SR: v = ss.resample_poly(v, SR // 100, sr // 100, axis=0).astype(np.float32)
        v = bq(v, "high", 90, 2); v = bq(v, "low", 10500, 2)
        seg = v[I(a):I(b)].mean(1)
        env = np.sqrt(np.convolve(seg ** 2, np.ones(I(0.08)) / I(0.08), "same")) + 1e-4
        g = np.clip((db(-20) / env) ** 0.5, db(-6), db(9)); g = np.convolve(g, np.ones(I(0.05)) / I(0.05), "same")
        seg = seg * g
        nf = I(0.04); seg[:nf] *= np.sin(np.linspace(0, np.pi / 2, nf)) ** 2; seg[-nf:] *= np.cos(np.linspace(0, np.pi / 2, nf)) ** 2
        env2 = np.sqrt(np.convolve(seg ** 2, np.ones(I(0.05)) / I(0.05), "same")); act = env2 > env2.max() * db(-24)
        seg = seg / (np.sqrt((seg[act] ** 2).mean()) + 1e-9) * db(-16.0 if k == 0 else -15.0)
        pk = np.abs(seg).max(); seg = np.tanh(seg / max(pk, 1e-9) * 1.4) / np.tanh(1.4) * pk if pk > db(-2) else seg
        place(vo, stereo(seg), at)
        duck[I(at) + PRE:I(at + b - a) + PRE] = 1.0
    wet = A2.conv(vo, A2.ir(0.45, seed=31)) * db(-20)
    sm = np.convolve(duck, np.hanning(I(0.25)) / np.hanning(I(0.25)).sum(), "same")
    return vo + wet, sm

# ------------------------------------------------------------------ v9 sounds
def wind_gust(dur=0.9, level=-22, seed=600, pan=(-0.7, 0.7)):
    n = I(dur); u = np.arange(n) / n; x = noise(n, seed); out = np.zeros(n, np.float32); blk = 1024
    for i in range(0, n, blk):
        fc = 500 + 2500 * math.sin(math.pi * u[i]) ** 1.5
        sos = ss.butter(2, [fc / 2.2 / (SR / 2), min(0.95, fc * 2.2 / (SR / 2))], "band", output="sos")
        seg = x[max(0, i - 2048):i + blk]; y = ss.sosfilt(sos, seg)[-min(blk, n - i):]; out[i:i + len(y)] = y
    out = norm(out * np.sin(np.pi * u) ** 1.3, level); p = np.linspace(pan[0], pan[1], n)
    return np.stack([out * (1 - p) / 1.4, out * (1 + p) / 1.4], 1).astype(np.float32)

def petal_flutter(dur=0.7, level=-24, seed=610, count=70, spread=1.0):
    """many tiny paper-soft petal flaps, scattered in time and across the stereo field."""
    n = I(dur); out = np.zeros((n, 2), np.float32); rng = np.random.default_rng(seed)
    for _ in range(count):
        i = int(rng.uniform(0, 1) ** 1.4 * (n - I(0.05))); m = I(rng.uniform(0.012, 0.035)); tt = np.arange(m) / SR
        y = bq(noise(m, int(rng.integers(1e6))), "band", np.array([1500, 7000]), 2) * np.sin(np.pi * tt / (m / SR)) ** 2 * rng.uniform(0.3, 1)
        p = rng.uniform(-spread, spread); out[i:i + m, 0] += y * (1 - 0.5 * p); out[i:i + m, 1] += y * (1 + 0.5 * p)
    out = out * np.linspace(1, 0.4, n)[:, None]
    return out / (np.abs(out).max() + 1e-9) * db(level)

def leaves(dur=0.6, level=-23, seed=620):
    n = I(dur); u = np.arange(n) / n; x = bq(noise(n, seed), "band", np.array([1200, 9000]), 2)
    crk = (np.random.default_rng(seed + 1).random(n) > 0.86).astype(np.float32)
    y = x * (0.5 + 0.8 * crk) * np.sin(np.pi * u) ** 1.2
    p = np.linspace(0.8, -0.8, n); y = norm(y, level)
    return np.stack([y * (1 - p) / 1.4, y * (1 + p) / 1.4], 1).astype(np.float32)

def chimes(level=-30, seed=630, notes=(2093, 2637, 3136, 3951)):
    n = I(1.4); t = np.arange(n) / SR; y = np.zeros(n, np.float32)
    for k, f in enumerate(notes):
        t0 = 0.05 * k; tt = np.clip(t - t0, 0, None)
        y += (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2.01 * tt)) * np.exp(-tt / 0.45) * (t >= t0)
    return norm(y * np.minimum(1, t / 0.004), level)

def crickets(n, seed=640, level=-37):
    """a night-garden bed: two cricket voices (4.4 / 5.1 kHz trills) + air."""
    t = np.arange(n) / SR; y = np.zeros(n, np.float32)
    for f, rate, ph, a in ((4400, 2.6, 0.0, 1.0), (5120, 3.1, 1.3, 0.7)):
        gate = (np.sin(2 * np.pi * rate * t + ph) > 0.35).astype(np.float32)
        trill = (np.sin(2 * np.pi * 52 * t) > 0).astype(np.float32)
        g = np.convolve(gate * trill, np.ones(48) / 48, "same")
        y += a * np.sin(2 * np.pi * f * t) * g
    air = bq(noise(n, seed), "band", np.array([300, 2500]), 2) * 0.35
    return norm(y + air, level)

def click(level=-22, seed=650):
    n = I(0.04); y = bq(noise(n, seed), "band", np.array([2000, 9000]), 2) * env_exp(n, 0.004, 0.0002)
    return norm(y + np.sin(2 * np.pi * 900 * np.arange(n) / SR) * env_exp(n, 0.006) * 0.4, level)

def ring(dur=1.4, level=-40, f=7200):
    n = I(dur); t = np.arange(n) / SR
    return norm(np.sin(2 * np.pi * f * t) * np.minimum(1, t / 0.02) * np.exp(-t / (dur * 0.5)), level)

def rev_swell(dur=0.45, level=-24, seed=660):
    """breath-in: a reversed reverb swell that ends on the cut."""
    n = I(dur); x = bq(noise(n, seed), "band", np.array([400, 6000]), 2) * np.linspace(0, 1, n) ** 2.5
    x = A2.conv(np.stack([x, x], 1), A2.ir(0.6, seed=seed))[:n]
    x = x * np.linspace(0, 1, n)[:, None] ** 1.8
    return x / (np.abs(x).max() + 1e-9) * db(level)

def slat_rattle(level=-24, seed=670, n_=14, dur=0.16):
    n = I(dur + 0.05); y = np.zeros(n, np.float32); rng = np.random.default_rng(seed)
    for i in range(n_):
        i0 = I(dur * i / n_ + rng.uniform(0, 0.005)); m = I(0.01)
        y[i0:i0 + m] += bq(noise(m, seed + i), "band", np.array([1500, 6000]), 2) * env_exp(m, 0.002, 0.0002) * rng.uniform(0.5, 1)
    return norm(y, level)

def strobe_zap(level=-24, seed=680):
    n = I(0.09); t = np.arange(n) / SR
    y = np.sign(np.sin(2 * np.pi * 120 * t)) * env_exp(n, 0.02, 0.0005) * 0.5 + bq(noise(n, seed), "high", 3000, 2) * env_exp(n, 0.01, 0.0002)
    return norm(y, level)

def heartbeat(level=-16):
    n = I(0.5); t = np.arange(n) / SR; y = np.zeros(n, np.float32)
    for t0, a in ((0.0, 1.0), (0.17, 0.7)):
        tt = np.clip(t - t0, 0, None); y += a * np.sin(2 * np.pi * 52 * tt) * np.exp(-tt / 0.07) * (t >= t0)
    return norm(bq(y, "low", 200, 2), level)


# ================================================================== v10 LET IT HAPPEN
def crackle(dur=0.35, level=-26, seed=800, density=0.25, band=(1500, 9000)):
    n = I(dur); x = noise(n, seed); g = (np.random.default_rng(seed + 1).random(n) < density * 0.02).astype(np.float32)
    g = np.convolve(g, np.hanning(48), "same")
    y = bq(x, "band", np.array(band), 2) * np.clip(g * 3, 0, 1) + bq(noise(n, seed + 2), "band", np.array([3000, 12000]), 2) * 0.15
    e = np.minimum(1, np.arange(n) / I(0.01)) * np.minimum(1, (n - np.arange(n)) / I(0.06))
    return norm(y * e, level)

def zap(level=-24, seed=810, f0=3200, f1=600, dur=0.12):
    n = I(dur); t = np.arange(n) / SR; f = f0 * (f1 / f0) ** (t / dur)
    y = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * env_exp(n, dur * 0.4, 0.0005) * 0.5 + bq(noise(n, seed), "high", 2500, 2) * env_exp(n, 0.02, 0.0002)
    return norm(y, level)

def thunder(level=-14, seed=820, dur=1.3):
    n = I(dur); t = np.arange(n) / SR
    crack = bq(noise(n, seed), "high", 1500, 2) * env_exp(n, 0.05, 0.0003)
    roll = bq(noise(n, seed + 1), "low", 260, 2) * env_exp(n, 0.45, 0.02) * (1 + 0.5 * np.sin(2 * np.pi * 7 * t))
    return norm(crack * 1.2 + roll * 0.9, level)

def whine(dur=0.4, level=-26, f0=400, f1=4200):
    n = I(dur); t = np.arange(n) / SR; u = t / dur; f = f0 * (f1 / f0) ** (u ** 1.6)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(2 * np.pi * np.cumsum(2.01 * f) / SR)
    return norm(y * u ** 2 * np.minimum(1, (n - np.arange(n)) / I(0.01)), level)

def tick(level=-26, seed=830):
    n = I(0.05); y = bq(noise(n, seed), "band", np.array([2500, 7000]), 2) * env_exp(n, 0.005, 0.0002)
    y = y + np.sin(2 * np.pi * 1900 * np.arange(n) / SR) * env_exp(n, 0.012) * 0.6
    return norm(y, level)

# ------------------------------------------------------------------ rev 3 sounds
def buzz(dur=0.3, level=-24, f0=60, f1=220, seed=1300):
    """molecular vibration: a rising saw buzz with a fast tremolo."""
    n = I(dur); t = np.arange(n) / SR; u = t / dur; f = f0 * (f1 / f0) ** u
    ph = np.cumsum(f) / SR; y = 2 * (ph % 1) - 1
    y = y * (0.6 + 0.4 * np.sin(2 * np.pi * (18 + 40 * u) * t)) + 0.3 * bq(noise(n, seed), "band", np.array([2000, 7000]), 2)
    return norm(bq(y, "low", 4000, 2) * u ** 1.6, level)

def swirl(dur=0.6, level=-21, seed=1310, laps=1.0):
    """wind torn round in a circle: band noise whose pan circles L -> R -> L."""
    n = I(dur); u = np.arange(n) / n; x = noise(n, seed); out = np.zeros(n, np.float32); blk = 1024
    for i in range(0, n, blk):
        fc = 600 + 2600 * math.sin(math.pi * u[i]) ** 1.2
        sos = ss.butter(2, [fc / 2.0 / (SR / 2), min(0.95, fc * 2.0 / (SR / 2))], "band", output="sos")
        seg = x[max(0, i - 2048):i + blk]; y = ss.sosfilt(sos, seg)[-min(blk, n - i):]; out[i:i + len(y)] = y
    out = norm(out * np.sin(np.pi * u) ** 1.2, level); pn = np.sin(2 * np.pi * laps * u) * 0.85
    return np.stack([out * (1 - pn) / 1.4, out * (1 + pn) / 1.4], 1).astype(np.float32)

def glass(level=-19, seed=1320, dur=0.9, dull=False):
    """a pane breaking: the crack, the burst, then falling tinkles."""
    n = I(dur); t = np.arange(n) / SR; rng = np.random.default_rng(seed)
    crack = bq(noise(n, seed), "high", 2500, 2) * env_exp(n, 0.012, 0.0002)
    body = bq(noise(n, seed + 1), "band", np.array([1500, 9000]), 2) * env_exp(n, 0.12, 0.002) * 0.6
    tk = np.zeros(n, np.float32)
    for _ in range(40):
        i = int(rng.uniform(0.02, 0.85) ** 1.5 * n); m = I(0.08); tt_ = np.arange(min(m, n - i)) / SR; fq = rng.uniform(3000, 9000)
        tk[i:i + len(tt_)] += np.sin(2 * np.pi * fq * tt_) * np.exp(-tt_ / 0.02) * rng.uniform(0.2, 0.7)
    y = crack * 1.2 + body + tk * 0.5
    if dull: y = bq(y, "low", 2500, 2)
    return norm(y, level)

def sub_drop(level=-14, dur=0.7, f0=70, f1=28):
    n = I(dur); t = np.arange(n) / SR; f = f0 * (f1 / f0) ** (t / dur)
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (dur * 0.45)) * np.minimum(1, t / 0.004), level)

def hum_rise(dur=1.2, level=-28, f0=110, f1=440):
    """the charge: a rising electrical hum with harmonics."""
    n = I(dur); t = np.arange(n) / SR; u = t / dur; f = f0 * (f1 / f0) ** (u ** 1.3)
    ph = np.cumsum(f) / SR
    y = sum(np.sin(2 * np.pi * k * ph) / k for k in range(1, 7)) * (0.8 + 0.2 * np.sin(2 * np.pi * 60 * t))
    return norm(y * u ** 1.5 * np.minimum(1, (dur - t) / 0.02), level)

def song_read10():
    if not os.path.exists(f"{AD}/song48.wav"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", E.SONG, "-ar", "48000", "-ac", "2", "-c:a", "pcm_f32le", f"{AD}/song48.wav"], check=True)
    _, song = wf.read(f"{AD}/song48.wav"); return song.astype(np.float32)

def music11(song):
    """the window straight (the pre-roll carries the intro across the wrap); the last half-beats tape-stop into the loop
    (the red lightning takes the frame back to Harrison): the song slows to a stop, then the intro talk starts again."""
    n = N + PRE; tt = (np.arange(n) - PRE) / SR
    t_ts = E.th(E.H1 - E.H0 - 2)                                            # tape stop over the last two half-beats
    pos = E.SONG_IN + tt
    m = tt >= t_ts
    if m.any():
        d = E.DUR - t_ts; u = np.clip((tt[m] - t_ts) / d, 0, 1)
        pos = pos.copy(); pos[m] = E.SONG_IN + t_ts + d * (u - u ** 2 / 2 * 1.0) * 1.0          # speed 1 -> 0 (linear)
    x = pos * SR; i = np.clip(np.floor(x).astype(np.int64), 0, len(song) - 2); fr = (x - i)[:, None].astype(np.float32)
    out = song[i] * (1 - fr) + song[i + 1] * fr
    if m.any():
        k0 = int(np.argmax(m)); seg = out[k0:].copy(); u = np.linspace(0, 1, len(seg))[:, None]
        seg = bq(seg, "low", 9000, 2) * (1 - 0.55 * u ** 1.5)                 # the tape loses its top and level
        out[k0:] = seg
    return out.astype(np.float32)

def main():
    os.makedirs(AD, exist_ok=True)
    song = song_read10()
    mus = music11(song) * db(-1.0)
    fx = np.zeros((N + PRE, 2), np.float32); n = N + PRE; tt = np.arange(n) / SR - PRE / SR; th = E.th
    fx += stereo(norm(bq(noise(n, 1790), "low", 140, 2) + 0.08 * np.sin(2 * np.pi * 44 * tt), -46))     # room tone, continuous
    for s_ in E.SHOTS:
        tin, t0 = s_.get("tin"), s_["t0"]
        if tin == "red_phase":                                   # the beat: the Reverse-Flash shudder
            place(fx, stereo(buzz(0.18, -24, 45, 140)), t0 - 0.17); place(fx, A2.whoosh(0.28, -25, 1801, True), t0 - 0.03)
            place(fx, stereo(crackle(0.30, -28, 1802, 0.8)), t0)
        elif tin == "red_link":
            place(fx, stereo(crackle(0.25, -25, 1803, 0.9), -0.3), t0 - 0.10); place(fx, stereo(zap(-27, 1804, 2400, 700, 0.10)), t0)
        elif tin == "red_slices":
            for q in range(4): place(fx, A2.whoosh(0.11, -28 - q, 1805 + q, q % 2 == 0), t0 - 0.09 + q * 0.035)
        elif tin == "red_streak":                                # the rival runs past
            place(fx, swirl(0.36, -21, 1810, 0.5), t0 - 0.14); place(fx, stereo(crackle(0.30, -26, 1811, 0.9)), t0 - 0.10)
        elif tin == "dolly":                                     # the breath before "Let's go"
            place(fx, rev_swell(0.42, -27, 1812), t0 - 0.40)
        elif tin == "bolt_split":                                # THE DROP: the seam cracks, then the gold breaks through
            cr = crackle(0.36, -22, 1813, 0.9) * np.linspace(0.3, 1.0, I(0.36)) ** 1.5
            place(fx, stereo(cr.astype(np.float32)), t0 - 0.37); place(fx, stereo(whine(0.36, -25, 500, 5200)), t0 - 0.36)
            place(fx, stereo(A2.impact(-10, (52, 28), 0.9, 0.55, 1814)), t0); place(fx, stereo(thunder(-17, 1815, 1.0)), t0)
            place(fx, stereo(sub_drop(-15, 0.8)), t0 + 0.03); place(fx, A2.whoosh(0.40, -21, 1816, True), t0 - 0.03)
        elif tin == "gold_link":
            place(fx, stereo(crackle(0.25, -26, 1817), 0.2), t0 - 0.10); place(fx, stereo(zap(-28, 1818, 2600, 900, 0.10)), t0)
        elif tin == "whip": place(fx, A2.whoosh(0.22, -22, 1819, True), t0 - 0.10)
        elif tin == "slices":
            for q in range(4): place(fx, A2.whoosh(0.11, -28 - q, 1820 + q, q % 2 == 0), t0 - 0.09 + q * 0.035)
        elif tin == "freeze_in":                                 # time stops (a reversed swell into a dead tick), then restarts
            sw = A2.whoosh(0.30, -27, 1825, False)[::-1].copy(); place(fx, sw, t0 - 0.30); place(fx, stereo(tick(-22, 1826)), t0 + th(2))
            place(fx, np.stack([A2.shimmer(0.45, -33)] * 2, 1), t0 + th(2))
        elif tin == "restart":
            place(fx, stereo(A2.impact(-15, (60, 32), 0.5, 0.5, 1827)), t0); place(fx, A2.whoosh(0.32, -23, 1828, True), t0 - 0.05)
        elif tin == "ignite":
            place(fx, stereo(whine(0.28, -30, 300, 1800)), t0 - 0.05); place(fx, stereo(crackle(0.40, -24, 1829, 0.5)), t0 + 0.02)
        elif tin == "speedforce_in":                             # into the Speed Force: a rising whine, a rush, a low rumble
            place(fx, stereo(whine(0.30, -24, 500, 5000)), t0 - 0.28); place(fx, A2.whoosh(0.5, -20, 1830, True), t0 - 0.06)
            rr = bq(noise(I(1.2), 1831), "low", 220, 2) * np.sin(np.pi * np.arange(I(1.2)) / I(1.2)) ** 1.5
            place(fx, stereo(norm(rr, -26)), t0)
        elif tin == "ramp": place(fx, A2.whoosh(0.22, -24, 1832, True), t0 - 0.10)
        elif tin == "red_eye_dive":                              # into the red eye: power-up whine, the red rush, a sub drop out of Barry's eye
            place(fx, stereo(whine(0.24, -25, 300, 2600)), t0 - 0.24); place(fx, A2.whoosh(0.40, -22, 1900, True), t0 - 0.12)
            place(fx, stereo(sub_drop(-17, 0.6, 90, 30)), t0); place(fx, rev_swell(0.25, -29, 1901), t0 - 0.25)
        elif tin == "strobe_echo":                               # stroboscopic: a stuttered run of short passes
            for q in range(5): place(fx, A2.whoosh(0.07, -27 - q, 1905 + q, True), t0 - 0.13 + q * 0.032)
            place(fx, stereo(zap(-30, 1910, 3000, 1200, 0.06)), t0)
        elif tin == "bolt_trace":                                # the bolt zig-zags across (panned L -> R), then the burn
            cr = crackle(0.30, -22, 1911, 0.95); n_ = len(cr); p_ = np.linspace(-0.9, 0.9, n_)
            place(fx, np.stack([cr * (1 - p_) / 1.4, cr * (1 + p_) / 1.4], 1).astype(np.float32), t0 - 0.16)
            place(fx, stereo(fire_whoosh(-25, 0.45, 1912)), t0)
        elif tin == "heat_haze":                                 # heat rising: a fire roar swelling up
            place(fx, stereo(fire_whoosh(-21, 0.6, 1913)), t0 - 0.20); place(fx, rev_swell(0.30, -28, 1914), t0 - 0.30)
        elif tin == "clash":                                     # red and gold collide: two zaps racing in, an impact, a thunder crack
            place(fx, stereo(zap(-24, 1915, 1500, 4200, 0.16), -0.7), t0 - 0.16); place(fx, stereo(zap(-24, 1916, 1700, 4600, 0.16), 0.7), t0 - 0.16)
            place(fx, stereo(A2.impact(-12, (60, 30), 0.6, 0.6, 1917)), t0); place(fx, stereo(thunder(-19, 1918, 0.9)), t0 + 0.01)
            place(fx, stereo(crackle(0.4, -25, 1919, 0.9)), t0 + 0.02)
        elif tin == "rift":                                      # THE RIFT: a crack, the tear ripping across, a deep whoom, the Speed Force roar, the arrival
            pre_, post_ = 18 / 60, 26 / 60
            place(fx, stereo(zap(-22, 2200, 5200, 900, 0.14)), t0 - pre_); place(fx, stereo(crackle(0.12, -22, 2201, 0.95)), t0 - pre_)
            n_ = I(pre_ - 0.02); q_ = np.arange(n_) / SR
            rip = bq(noise(n_, 2202), "band", np.array([500, 6000]), 2) * (np.random.default_rng(2203).random(n_) > 0.45) * np.linspace(0.4, 1.0, n_)
            p_ = np.linspace(-0.8, 0.8, n_); r_ = norm(rip, -21)
            place(fx, np.stack([r_ * (1 - p_) / 1.4, r_ * (1 + p_) / 1.4], 1).astype(np.float32), t0 - pre_ + 0.03)
            place(fx, rev_swell(0.35, -24, 2204), t0 - 0.35); place(fx, stereo(sub_drop(-14, 0.9, 60, 24)), t0)
            n_ = I(post_); q_ = np.arange(n_) / SR
            roar = bq(noise(n_, 2205), "band", np.array([180, 2600]), 2) * np.sin(np.pi * q_ / post_) ** 0.8
            place(fx, stereo(norm(roar, -21)), t0); place(fx, stereo(whine(post_, -25, 400, 4200)), t0)
            place(fx, A2.whoosh(0.35, -20, 2206, True), t0 + post_ - 0.25); place(fx, stereo(A2.impact(-15, (58, 30), 0.5, 0.5, 2207)), t0 + post_ - 0.05)
        elif tin == "emblem_flash":                              # the emblem draws itself, flares
            place(fx, np.stack([A2.shimmer(0.7, -29)] * 2, 1), t0 - 0.20); place(fx, stereo(A2.impact(-20, (100, 55), 0.15, 0.7, 1833)), t0)
    for e_ in list(range(34, 84, 2)):                                       # a quiet swish on each camera punch that isn't a cut
        if e_ in {s_["e0"] for s_ in E.SHOTS} or 50 <= e_ < 56: continue
        place(fx, A2.whoosh(0.12, -34, 1850 + e_, e_ % 4 == 0), th(e_) - 0.06)
    # rev 2: the cold open breathes red (a low crackle bed + a sub swell into the beat), edge lightning, sweeps, freeze ticks
    cw = np.clip(np.minimum((tt + PRE / SR) / 0.4, (th(E.HDROP) - tt) / 0.1), 0, 1) * (tt < th(E.HDROP))
    bed = np.pad(crackle(E.DUR + PRE / SR + 0.05, -40, 1920, 0.5), (0, n))[:n]
    fx += stereo(bed * cw, 0.0) * np.array([[1.0, 0.92]], np.float32)
    place(fx, rev_swell(0.9, -26, 1921), th(E.E_BEAT) - 0.9); place(fx, stereo(A2.impact(-20, (48, 26), 0.5, 0.3, 1922)), th(E.E_BEAT))
    place(fx, rev_swell(0.7, -25, 1923), th(E.HDROP) - 0.7)                                # the breath before the drop
    for e_ in (8, 16, 40, 48, 72):
        place(fx, np.stack([crackle(0.16, -29, 1930 + e_, 0.9), crackle(0.16, -30, 1980 + e_, 0.9)], 1), th(e_))
    for e_ in (80, 81):                                                                        # red crackles creeping in before the strike
        place(fx, np.stack([crackle(0.2, -31, 2150 + e_, 0.9), crackle(0.2, -33, 2160 + e_, 0.9)], 1), th(e_) + 0.1)
    for e_ in (26, 44, 58):
        n_ = I(0.26); q_ = np.arange(n_) / SR
        sh = sum(np.sin(2 * np.pi * fq * q_) for fq in (3136, 4186, 5274)) * np.sin(np.pi * q_ / 0.26) ** 2
        place(fx, stereo(norm(sh, -34), -0.5), th(e_) + 0.02)
    for e_ in (52, 53):                                                                        # the clock in frozen time
        place(fx, stereo(tick(-26, 1990 + e_)), th(e_))
    for e_, pan in ((42, -0.8), (46, 0.8), (64, 0.0)):                                        # speed passes on the runs and the flight
        place(fx, swirl(0.36, -27, 2000 + e_, 0.3), th(e_) + 0.12)
    n_ = I(0.8); q_ = np.arange(n_) / SR                                                       # the loop: a power-down whine under the tape stop
    pd = np.sin(2 * np.pi * np.cumsum(2600 * (180 / 2600) ** (q_ / 0.8)) / SR) * np.sin(np.pi * np.minimum(q_ / 0.8, 1)) ** 1.2
    place(fx, stereo(norm(pd, -32)), E.DUR - 0.82)
    for tx in E.TEXT:
        if tx["style"] == "letsgo":
            place(fx, stereo(zap(-25, 1860, 4200, 1300, 0.10)), tx["words"][1][1]); place(fx, stereo(crackle(0.3, -27, 1861, 0.7)), tx["words"][1][1])
        elif tx["style"] == "bop":
            for q in range(3): place(fx, stereo(A2.impact(-27, (120 + 30 * q, 70), 0.06, 0.8, 1862 + q), -0.3 + 0.3 * q), tx["words"][0][1] + 0.06 * q)
    # rev 3, REVERSE: the strike on his emblem, the inversion, the red radiating, the dive through it into Harrison
    t_s, t_r, t_d = th(82), th(84), th(85)
    # rev 4: the coin flip: a fast spin whir, a sizzle at edge-on, a metal ring + thump on landing, sparks
    place(fx, A2.whoosh(0.22, -24, 2210, True), t_s + 4 / 60); place(fx, stereo(zap(-26, 2211, 2600, 5200, 0.08)), t_s + 10 / 60)
    place(fx, stereo(metal_shing(-22, 0.8)), t_s + 17 / 60); place(fx, stereo(A2.impact(-21, (80, 45), 0.25, 0.6, 2212)), t_s + 17 / 60)
    place(fx, stereo(crackle(0.35, -27, 2213, 0.9)), t_s + 18 / 60)
    place(fx, rev_swell(0.25, -27, 2214), t_d - 0.25)                                          # the dive's anticipation
    place(fx, stereo(crackle(0.22, -23, 2215, 0.95)), t_d + 0.46); place(fx, stereo(zap(-24, 2216, 5000, 1200, 0.12)), t_d + 0.48)   # the rim passes
    place(fx, stereo(thunder(-18, 2100, 1.0)), t_s); place(fx, stereo(zap(-23, 2101, 4400, 500, 0.18)), t_s - 0.02)
    inv = rev(np.stack([A2.shimmer(0.42, -26)] * 2, 1)) if hasattr(A2, "shimmer") else None
    if inv is not None: place(fx, inv.astype(np.float32), t_r - 0.42)                         # the inversion: a reversed shimmer
    rb = rev(stereo(A2.impact(-20, (60, 30), 0.35, 0.4, 2102))); place(fx, rb.astype(np.float32), t_r - len(rb) / SR)
    cr = crackle(t_d - t_r, -23, 2103, 0.95) * np.linspace(0.4, 1.0, I(t_d - t_r)) ** 1.2
    place(fx, stereo(cr.astype(np.float32)), t_r); place(fx, stereo(buzz(t_d - t_r, -28, 45, 160)), t_r)
    place(fx, A2.whoosh(E.DUR - t_d, -20, 2104, True), t_d); place(fx, stereo(whine(E.DUR - t_d, -27, 300, 3800)), t_d)
    place(fx, stereo(A2.impact(-22, (55, 30), 0.30, 0.25, 2105)), 0.0)                       # the landing on Harrison (loop start)
    # rev 3, the new beat moments: AURA pulses (the grin), REMNANTS splitting (the smirk), the CHARGE (the bar)
    for e_ in (38, 40):
        place(fx, stereo(A2.impact(-27, (70, 40), 0.25, 0.1, 2110 + e_)), th(e_)); place(fx, np.stack([A2.shimmer(0.35, -33)] * 2, 1), th(e_))
    for e_ in (56, 58):
        place(fx, A2.whoosh(0.14, -27, 2120 + e_, True) * np.array([[1.0, 0.25]], np.float32), th(e_) - 0.03)
        place(fx, A2.whoosh(0.14, -27, 2130 + e_, True) * np.array([[0.25, 1.0]], np.float32), th(e_) - 0.01)
    place(fx, stereo(hum_rise(th(64) - th(60), -26, 90, 520)), th(60))
    chg = crackle(th(64) - th(60), -26, 2140, 0.8) * np.linspace(0.2, 1.0, I(th(64) - th(60))) ** 1.5
    place(fx, stereo(chg.astype(np.float32)), th(60))
    fx = np.tanh(fx * 1.2) / 1.2
    wf.write(f"{AD}/stem_music.wav", SR, mus[PRE:].astype(np.float32))                        # pipeline v2: tools/mixcheck.py
    wf.write(f"{AD}/stem_fx.wav", SR, fx[PRE:].astype(np.float32))
    full = mus + fx
    lead, mix = full[:PRE].copy(), full[PRE:].copy()
    th2 = np.linspace(0, np.pi / 2, PRE)[:, None]
    mix[-PRE:] = mix[-PRE:] * np.cos(th2) + lead * np.sin(th2)
    raw = f"{AD}/mix_raw.wav"; wf.write(raw, SR, mix.astype(np.float32))
    Iraw, _ = measure(raw); gain = -12.9 - Iraw
    P2 = SR; wrapped = np.vstack([mix[-P2:], mix, mix[:P2]])
    wf.write(f"{AD}/mix_raw_wrapped.wav", SR, wrapped.astype(np.float32))
    tmp = f"{AD}/mix_wrapped_master.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{AD}/mix_raw_wrapped.wav", "-af", f"volume={gain:.2f}dB,aresample=192000,"
                    f"alimiter=limit={db(-3.6):.4f}:attack=3:release=60:level=disabled,aresample=48000:resampler=soxr", "-c:a", "pcm_f32le", tmp], check=True)
    _, mw = wf.read(tmp); mw = mw.astype(np.float32)
    ref = wrapped[P2:P2 + SR, 0]; seg_ = mw[P2 - 2000:P2 + SR + 2000, 0]
    lag = int(np.argmax(np.correlate(seg_, ref, mode="valid"))) - 2000
    m = mw[P2 + lag:P2 + lag + N]
    out = f"{AD}/mix.wav"; wf.write(out, SR, (np.clip(m, -1, 1) * (2 ** 31 - 1)).astype(np.int32))
    wf.write(f"{AD}/mix_preroll.wav", SR, np.vstack([m[-1024:], m]).astype(np.float32))
    test = f"{AD}/aac_test.m4a"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-itsoffset", str(-1024 / SR), "-i", f"{AD}/mix_preroll.wav", "-c:a", "aac", "-b:a", "256k", test], check=True)
    I2, TP2 = measure(out); I3, TP3 = measure(test)
    print(f"lag {lag}; raw {Iraw:.1f} -> {gain:+.1f} dB -> wav {I2:.1f} LUFS/{TP2:.1f} dBTP; AAC {I3:.1f} LUFS/{TP3:.1f} dBTP")
    mm = m.mean(1); loop = np.concatenate([mm[-24000:], mm[:24000]]); d = np.abs(np.diff(loop))
    print(f"loop seam step {d[23997:24003].max():.4f} vs local median {np.median(d[21600:26400]):.4f}")


# ============================================================================ v12 — BLOOM (The Flash × fakemink)
# fakemink "Night Blooming Jasmine", song 18.71-42.05 s (bars 8-18): the instrumental groove, the vocal in at bar 12
# (THE BLOOM), the claps at bar 16 (FULL BLOOM). From 21.3 s the vocal stem fades out on a half-beat echo under the loop
# dive (the night closes), the instrumental runs on and wraps into bar 8 on the bar grid; the mix closes a little under
# a low-pass for the last half-second and opens again on frame 0. Effects are mixed against a loud master (rule 7).
from scipy.signal import resample_poly
def stems48():
    out = []
    for nm in ("no_vocals", "vocals"):
        sr_, x = wf.read(f"{E.SONG_STEMS}/{nm}.wav"); x = x.astype(np.float32) / (32768.0 if x.dtype == np.int16 else 1.0)
        out.append(resample_poly(x, 160, 147, axis=0).astype(np.float32))
    return out

def music12(song):
    n = N + PRE; tt = (np.arange(n) - PRE) / SR
    i0 = I(E.SONG_IN) - PRE; out = song[i0:i0 + n].copy()
    inst, voc = stems48(); k0 = I(E.SONG_IN - E.STEMS_T0) - PRE
    inst, voc = inst[k0:k0 + n], voc[k0:k0 + n]
    TV0, TV1, TV2 = 21.20, 21.30, 22.55
    g = np.clip((TV2 - tt) / (TV2 - TV1), 0, 1); g = np.where(tt < TV1, 1.0, np.sin(g * np.pi / 2) ** 2).astype(np.float32)[:, None]
    d = I(E.HB); echo = np.zeros_like(voc); echo[d:] = voc[:-d]
    g2 = np.clip((23.1 - tt) / (23.1 - TV1), 0, 1).astype(np.float32)[:, None] * (tt >= TV1)[:, None]
    stem_mix = inst + voc * g + bq(echo, "low", 3500, 1) * 0.38 * g2 * (1 - g)
    w = np.clip((tt - TV0) / (TV1 - TV0), 0, 1).astype(np.float32)[:, None]
    out = out * (1 - w) + stem_mix * w
    lp = np.clip((tt - (E.DUR - 0.45)) / 0.45, 0, 1).astype(np.float32)[:, None] * 0.7  # the night closes
    out = out * (1 - lp) + bq(out, "low", 2200, 2) * lp
    return out.astype(np.float32)

def beep(level=-14, f=1000, dur=0.09):
    t = np.arange(I(dur)) / SR; y = np.sin(2 * np.pi * f * t) * np.minimum(1, t / 0.004) * np.exp(-t / 0.05)
    return (y / np.abs(y).max() * db(level)).astype(np.float32)

def WH(*a, **k): return A2.whoosh(*a, **k) * db(8)
def CR(*a, **k): return crackle(*a, **k) * db(6)
def ZP(*a, **k): return zap(*a, **k) * db(5)
def RS(*a, **k): return rev_swell(*a, **k) * db(6)
def GC(*a, **k): return glass_chime(*a, **k) * db(6)
def SH(*a, **k): return A2.shimmer(*a, **k) * db(4)
def TK(*a, **k): return tick(*a, **k) * db(6)

def main():
    os.makedirs(AD, exist_ok=True)
    song = song_read10()
    mus = music12(song) * db(-1.0)
    n = N + PRE; tt = np.arange(n) / SR - PRE / SR; th = E.th
    fx = np.zeros((n, 2), np.float32)
    fx += stereo(norm(bq(noise(n, 1790), "low", 140, 2) + 0.08 * np.sin(2 * np.pi * 44 * tt), -40))      # night air, continuous
    t0 = {s_["n"]: s_["t0"] for s_ in E.SHOTS}
    # ---- the landing on frame 0 and the storm
    place(fx, stereo(A2.impact(-6, (55, 30), 0.30, 0.25, 2201)), 0.0); place(fx, stereo(thunder(-10, 2202, 1.4)), 0.38)
    # ---- STRIKE LINK, ECG, sparks, the bud iris, the cortex, the eye
    place(fx, stereo(ZP(-8, 2220, 5200, 300, 0.22)), t0["strike"])
    place(fx, stereo(thunder(-6, 2221, 1.6)), t0["strike"]); place(fx, stereo(sub_drop(-8, 0.8)), t0["strike"] + 0.02)
    place(fx, stereo(beep(-12, 1000, 0.25)), t0["wake"] - 0.14); place(fx, stereo(ZP(-10, 2224, 4200, 500, 0.16)), t0["wake"])
    place(fx, stereo(ZP(-6, 2227, 3000, 700, 0.14), 0.6), t0["spark"])
    place(fx, stereo(CR(0.30, -13, 2235, 0.7)), t0["cortex"] - 0.10)                                       # the bud turns (no chime)
    place(fx, RS(0.45, -14, 2237), t0["eye"] - 0.42)
    cr = CR(0.40, -12, 2239, 0.95) * np.linspace(0.2, 1.0, I(0.40)) ** 1.6; place(fx, stereo(cr.astype(np.float32)), t0["bloomrun"] - 0.40)
    # ---- THE BLOOM (the vocal enters)
    tb_ = t0["bloomrun"]
    place(fx, stereo(A2.impact(-4, (52, 28), 0.9, 0.55, 2240)), tb_); place(fx, stereo(sub_drop(-6, 0.9, 64, 26)), tb_ + 0.02)
    place(fx, stereo(thunder(-8, 2241, 1.4)), tb_)
    # ---- the montage: a sound per transition and per beat moment
    place(fx, WH(0.26, -10, 2250, True) * np.array([[0.3, 1.0]], np.float32), t0["blue"] - 0.12)
    fb_ = CR(0.55, -10, 2251, 0.9) * np.linspace(0.4, 1.0, I(0.55)); place(fx, stereo(bq(fb_, "low", 5000, 1).astype(np.float32)), t0["street"] - 0.13)   # FRACTAL BURN: the burn
    place(fx, stereo(A2.impact(-12, (70, 40), 0.3, 0.15, 2252)), t0["street"] + 0.10)
    for q in range(5): place(fx, WH(0.07, -14 - q, 2260 + q, True), t0["crouch"] - 0.13 + q * 0.032)
    for q in range(4): place(fx, WH(0.11, -14 - q, 2270 + q, q % 2 == 0), t0["hood"] - 0.09 + q * 0.035)
    place(fx, stereo(ZP(-10, 2301, 2400, 400, 0.10)), t0["charge"] - 0.06)                                 # EMBLEM BLOOM: it cracks
    place(fx, stereo(A2.impact(-7, (60, 30), 0.5, 0.35, 2300)), t0["charge"]); place(fx, RS(0.25, -14, 2302), t0["charge"] - 0.22)
    place(fx, WH(0.30, -13, 2310, False), t0["s3night"] - 0.12)
    place(fx, WH(0.22, -10, 2320, True), t0["dash"] - 0.10)
    # ---- FULL BLOOM (the claps enter)
    tf = t0["full"]
    place(fx, RS(0.35, -12, 2330), tf - 0.33); place(fx, stereo(ZP(-10, 2331, 600, 5200, 0.25)), tf + 0.02)
    place(fx, stereo(A2.impact(-6, (50, 26), 0.9, 0.3, 2333)), tf + 0.28); place(fx, stereo(sub_drop(-8, 0.9, 60, 25)), tf + 0.30)
    place(fx, WH(0.50, -9, 2340, True), t0["s3mask"] - 0.18)
    place(fx, WH(0.30, -15, 2342, False), t0["last"] - 0.10)
    # ---- the loop: the bud closes, the dive, the landing on frame 0
    tl_ = t0["last"]
    td = tl_ + 46 / E.FPS
    place(fx, RS(E.DUR - td, -10, 2351), td); place(fx, WH(E.DUR - td, -9, 2352, True), td)
    fx = np.tanh(fx * 1.2) / 1.2
    wf.write(f"{AD}/stem_music.wav", SR, mus[PRE:].astype(np.float32))                        # pipeline v2: tools/mixcheck.py
    wf.write(f"{AD}/stem_fx.wav", SR, fx[PRE:].astype(np.float32))
    full = mus + fx
    lead, mix = full[:PRE].copy(), full[PRE:].copy()
    th2 = np.linspace(0, np.pi / 2, PRE)[:, None]
    mix[-PRE:] = mix[-PRE:] * np.cos(th2) + lead * np.sin(th2)
    raw = f"{AD}/mix_raw.wav"; wf.write(raw, SR, mix.astype(np.float32))
    Iraw, _ = measure(raw); gain = -12.9 - Iraw
    P2 = SR; wrapped = np.vstack([mix[-P2:], mix, mix[:P2]])
    wf.write(f"{AD}/mix_raw_wrapped.wav", SR, wrapped.astype(np.float32))
    tmp = f"{AD}/mix_wrapped_master.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{AD}/mix_raw_wrapped.wav", "-af", f"volume={gain:.2f}dB,aresample=192000,"
                    f"alimiter=limit={db(-3.6):.4f}:attack=3:release=60:level=disabled,aresample=48000:resampler=soxr", "-c:a", "pcm_f32le", tmp], check=True)
    _, mw = wf.read(tmp); mw = mw.astype(np.float32)
    ref = wrapped[P2:P2 + SR, 0]; seg_ = mw[P2 - 2000:P2 + SR + 2000, 0]
    lag = int(np.argmax(np.correlate(seg_, ref, mode="valid"))) - 2000
    m = mw[P2 + lag:P2 + lag + N]
    out = f"{AD}/mix.wav"; wf.write(out, SR, (np.clip(m, -1, 1) * (2 ** 31 - 1)).astype(np.int32))
    wf.write(f"{AD}/mix_preroll.wav", SR, np.vstack([m[-1024:], m]).astype(np.float32))
    test = f"{AD}/aac_test.m4a"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-itsoffset", str(-1024 / SR), "-i", f"{AD}/mix_preroll.wav", "-c:a", "aac", "-b:a", "256k", test], check=True)
    I2, TP2 = measure(out); I3, TP3 = measure(test)
    print(f"lag {lag}; raw {Iraw:.1f} -> {gain:+.1f} dB -> wav {I2:.1f} LUFS/{TP2:.1f} dBTP; AAC {I3:.1f} LUFS/{TP3:.1f} dBTP")
    mm = m.mean(1); loop = np.concatenate([mm[-24000:], mm[:24000]]); d = np.abs(np.diff(loop))
    print(f"loop seam step {d[23997:24003].max():.4f} vs local median {np.median(d[21600:26400]):.4f}")




# ============================================================================ v107 — ALL CAPS (Dexter × Madvillain)
# Madvillain "All Caps" h176-h240 (60.92-82.86 s): the end of verse 1 and the beat break; the window wraps on the bar
# grid (the bass drops out in the last bar and returns on bar 1). Sound restraint (v106/v12 rules): one sound per
# ordinary transition or none, layered hits only at the set pieces (the molasses, the headspin, the front page, the six
# letterpress stamps, the banner, the confetti), nothing on beat moments, no chimes, nothing in the loop bar.
def music107(song):
    n = N + PRE; tt = (np.arange(n) - PRE) / SR
    x = (E.SONG_IN + tt) * SR; i = np.clip(np.floor(x).astype(np.int64), 0, len(song) - 2); fr = (x - i)[:, None].astype(np.float32)
    return (song[i] * (1 - fr) + song[i + 1] * fr).astype(np.float32)

def paper_slap(level, seed):
    n = I(0.35); q = np.arange(n) / SR
    y = bq(noise(n, seed), "band", np.array([500, 5000]), 2) * np.exp(-q / 0.035) + np.sin(2 * np.pi * 95 * q) * np.exp(-q / 0.06) * 0.8
    return norm(y, level)

def stamp_hit(level, seed):
    """letterpress: the platen comes down (a short scrape), the hit (a dull wooden-metal chunk, a low body), a little rattle."""
    n = I(0.45); q = np.arange(n) / SR; rng = np.random.default_rng(seed)
    body = np.sin(2 * np.pi * np.cumsum(70 + 60 * np.exp(-q / 0.03)) / SR) * np.exp(-q / 0.09)
    knock = bq(noise(n, seed), "band", np.array([600, 2600]), 2) * np.exp(-q / 0.018) * 1.4
    ring = sum(np.sin(2 * np.pi * f * q + rng.uniform(0, 6)) * np.exp(-q / d) for f, d in ((1180, 0.05), (1730, 0.035), (2650, 0.025))) * 0.10
    pre = np.zeros(n, np.float32)
    y = body + knock + ring
    return norm(y.astype(np.float32), level)

def pour(dur, level, seed):
    """thick liquid: a low gloopy roll with slow bubbles."""
    n = I(dur); q = np.arange(n) / SR; rng = np.random.default_rng(seed)
    y = bq(noise(n, seed), "band", np.array([60, 420]), 2) * (0.6 + 0.4 * np.sin(2 * np.pi * 5.5 * q + 1.0)) * np.sin(np.pi * np.minimum(q / dur * 1.2, 1)) ** 0.8
    for k in range(9):                                                                     # gloops
        t_ = rng.uniform(0.05, dur - 0.12); m = I(0.10); i0 = I(t_); qq = np.arange(m) / SR
        y[i0:i0 + m] += np.sin(2 * np.pi * np.cumsum(180 + 260 * qq / 0.10) / SR) * np.exp(-qq / 0.03) * rng.uniform(0.4, 0.9)
    return norm(y, level)

def splatter(level, seed):
    """blood hitting glass: a spray of short wet ticks, thinning out, over a soft low body."""
    n = I(0.32); q = np.arange(n) / SR; rng = np.random.default_rng(seed); y = np.zeros(n, np.float32)
    for k, (t_, a) in enumerate(zip(np.sort(rng.uniform(0, 0.085, 11)), rng.uniform(0.35, 1.0, 11))):
        m = I(0.03); i0 = I(t_); qq = np.arange(m) / SR
        y[i0:i0 + m] += (bq(noise(m, seed + k), "band", np.array([900 + 300 * k % 1500, 5200]), 2) * np.exp(-qq / 0.0045) * a * (1 - t_ / 0.12)).astype(np.float32)
    y += (np.sin(2 * np.pi * 85 * q) * np.exp(-q / 0.05) * 0.5 + bq(noise(n, seed + 99), "band", np.array([250, 1400]), 2) * np.exp(-q / 0.06) * 0.35).astype(np.float32)
    return norm(y, level)

def flutter(dur, level, seed, rate=14.0):
    n = I(dur); q = np.arange(n) / SR
    y = bq(noise(n, seed), "band", np.array([900, 6000]), 2) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * rate * q * (1 + q / dur)))) * np.sin(np.pi * q / dur) ** 0.7
    return norm(bq(y, "low", 7000, 1), level)

def main():
    os.makedirs(AD, exist_ok=True)
    song = song_read10()
    mus = music107(song) * db(-1.0)
    n = N + PRE; tt = np.arange(n) / SR - PRE / SR; th = E.th
    fx = np.zeros((n, 2), np.float32)
    fx += stereo(norm(bq(noise(n, 1790), "low", 140, 2) + 0.08 * np.sin(2 * np.pi * 44 * tt), -46))      # room tone, continuous
    t0 = {s_["n"]: s_["t0"] for s_ in E.SHOTS}
    # ---- the kill table: the plastic tears
    pl = crackle(0.32, -20, 3301, 0.95, (1200, 9000)); place(fx, stereo(pl, -0.3), t0["table"] - 0.10)
    place(fx, A2.whoosh(0.20, -24, 3302, True), t0["table"] - 0.08)
    # ---- SPATTER ANALYSIS: the spatter hits the lens (a wet burst); RORSCHACH: the blot blooms (a wet swell), a plop on
    # ---- the cut, the card swings open (a paper swish)
    # rev 4: the spatter analysis and the Rorschach are gone; the cut to "shh" is on the downbeat (no sound)
    # ---- the page turn: one paper flip
    place(fx, stereo(flutter(0.34, -20, 3305, 16.0), 0.35), t0["lab"] - 0.20)
    # ---- HOT MOLASSES: the pour swells, a thick glug at the cut, it drips as it drains
    tm = t0["hazmat"]
    place(fx, stereo(pour(0.85, -17, 3306)), tm - 0.62); place(fx, stereo(bloop(-18, 3307)), tm - 0.02)
    place(fx, stereo(A2.impact(-18, (55, 30), 0.35, 0.25, 3308)), tm); place(fx, stereo(drip(-22, 3309), 0.3), tm + 0.22)
    # ---- the robot: a servo clunk on the cut
    place(fx, stereo(vcr_clunk(-20, 3310)), t0["robot"] - 0.02)
    # ---- HEADSPIN: the spin circles the stereo field, a whoom at the turn, the landing
    th_ = t0["pillow"]
    place(fx, swirl(0.66, -15, 3311, 2.0), th_ - 0.34); place(fx, A2.whoosh(0.30, -18, 3312, True), th_ - 0.10)
    place(fx, stereo(sub_drop(-20, 0.45, 70, 32)), th_ + 0.30)
    place(fx, A2.whoosh(0.16, -24, 3313, False), t0["grin"] - 0.06)                       # the whip
    # ---- the loop: the crowd's confetti gathers into his name (a paper flutter), then bursts into frame 0
    place(fx, petal_flutter(1.30, -21, 3360, 140, 1.0), th(57.6))
    place(fx, A2.whoosh(0.42, -20, 3361, True), th(62.2))
    # ---- THE FRONT PAGE: it spins in fluttering, lands with a slap, we dive into the photo
    tp = th(24); tl = tp + 0.52 * (t0["con"] - tp)
    place(fx, stereo(flutter(tl - tp, -21, 3314, 12.0), 0.2), tp); place(fx, stereo(paper_slap(-15, 3315)), tl - 0.01)
    place(fx, A2.whoosh(0.32, -17, 3316, True), t0["con"] - 0.26)
    place(fx, A2.whoosh(0.16, -26, 3317, False), t0["doakes"] - 0.07)                      # whip
    # ---- the cage: the chain-link shakes
    place(fx, stereo(slat_rattle(-20, 3318, 16, 0.22)), t0["cage"] - 0.03); place(fx, stereo(A2.impact(-20, (65, 35), 0.25, 0.4, 3319)), t0["cage"])
    # ---- the zipper
    place(fx, stereo(shutter_ticks(-15, 16, 0.014, 3320), -0.2), t0["shame"] - 0.20)
    place(fx, stereo(A2.impact(-22, (60, 32), 0.25, 0.2, 3321)), t0["remember"])       # remember: a low thud
    # ---- ALL CAPS: the strip slaps on, D-E-X-T-E-R stamped one letter per sung word
    place(fx, A2.whoosh(0.20, -22, 3322, True), t0["parade"] - 0.08)
    caps = next(wt for tx in E.TEXT if tx["style"] == "cap" for w_, wt, _ in tx["words"] if w_ == "CAPS")
    place(fx, stereo(paper_slap(-14, 3323)), caps + 3 / E.FPS)
    for q, tx in enumerate([t for t in E.TEXT if t["style"] == "stamp"][0]["words"]):
        place(fx, stereo(stamp_hit(-12 - (0 if q == 5 else 1), 3330 + q), -0.5 + 0.2 * q), tx[1] - 0.004)     # rev 3: on the hit
    # ---- the strip flies into the sky onto the banner
    place(fx, A2.whoosh(0.50, -16, 3340, True), t0["banner"] - 0.05); place(fx, wind_gust(0.9, -22, 3341, (-0.5, 0.5)), t0["banner"])
    # ---- the parade: the confetti pops
    place(fx, stereo(flash_pop(-16, 3342)), t0["laugh"] - 0.40 - 0.16); place(fx, petal_flutter(1.1, -20, 3343, 90, 1.0), t0["laugh"] - 0.38)
    fx = fx * db(10.0)                                                                         # rule 7: a loud master (about -12 dBFS RMS)
    duck = np.zeros(N + PRE, np.float32)
    for t_h in (t0["hazmat"], t0["pillow"], caps): duck[I(t_h - 0.03) + PRE:I(t_h + 0.35) + PRE] = 1.0
    duck = np.convolve(duck, np.hanning(I(0.12)) / np.hanning(I(0.12)).sum(), "same")
    mus = mus * db(-3.0 * duck)[:, None]
    fx = np.tanh(fx * 1.2) / 1.2
    wf.write(f"{AD}/stem_music.wav", SR, mus[PRE:].astype(np.float32))
    wf.write(f"{AD}/stem_fx.wav", SR, fx[PRE:].astype(np.float32))
    full = mus + fx
    lead, mix = full[:PRE].copy(), full[PRE:].copy()
    th2 = np.linspace(0, np.pi / 2, PRE)[:, None]
    mix[-PRE:] = mix[-PRE:] * np.cos(th2) + lead * np.sin(th2)
    raw = f"{AD}/mix_raw.wav"; wf.write(raw, SR, mix.astype(np.float32))
    Iraw, _ = measure(raw); gain = -12.9 - Iraw
    P2 = SR; wrapped = np.vstack([mix[-P2:], mix, mix[:P2]])
    wf.write(f"{AD}/mix_raw_wrapped.wav", SR, wrapped.astype(np.float32))
    tmp = f"{AD}/mix_wrapped_master.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{AD}/mix_raw_wrapped.wav", "-af", f"volume={gain:.2f}dB,aresample=192000,"
                    f"alimiter=limit={db(-3.6):.4f}:attack=3:release=60:level=disabled,aresample=48000:resampler=soxr", "-c:a", "pcm_f32le", tmp], check=True)
    _, mw = wf.read(tmp); mw = mw.astype(np.float32)
    ref = wrapped[P2:P2 + SR, 0]; seg_ = mw[P2 - 2000:P2 + SR + 2000, 0]
    lag = int(np.argmax(np.correlate(seg_, ref, mode="valid"))) - 2000
    m = mw[P2 + lag:P2 + lag + N].copy()
    zf = 96                                                                                # v107: frame 0 is a loud kick; the AAC tail pads
    fade = np.sin(np.linspace(0, np.pi / 2, zf)) ** 2                                       # with ~2 ms of silence, so the wrap passes
    m[:zf] *= fade[:, None]; m[-zf:] *= fade[::-1, None]                                   # through zero (a 4 ms dip, no click)
    out = f"{AD}/mix.wav"; wf.write(out, SR, (np.clip(m, -1, 1) * (2 ** 31 - 1)).astype(np.int32))
    wf.write(f"{AD}/mix_preroll.wav", SR, np.vstack([m[-1024:], m]).astype(np.float32))
    test = f"{AD}/aac_test.m4a"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-itsoffset", str(-1024 / SR), "-i", f"{AD}/mix_preroll.wav", "-c:a", "aac", "-b:a", "256k", test], check=True)
    I2, TP2 = measure(out); I3, TP3 = measure(test)
    print(f"lag {lag}; raw {Iraw:.1f} -> {gain:+.1f} dB -> wav {I2:.1f} LUFS/{TP2:.1f} dBTP; AAC {I3:.1f} LUFS/{TP3:.1f} dBTP")
    mm = m.mean(1); loop = np.concatenate([mm[-24000:], mm[:24000]]); d = np.abs(np.diff(loop))
    print(f"loop seam step {d[23997:24003].max():.4f} vs local median {np.median(d[21600:26400]):.4f}")


# ============================================================================ v108 — DOOMSDAY (Dexter × MF DOOM)
# MF DOOM "Doomsday" h208-h280 (65.64-88.29 s; the drum-stem grid). The drums and bass drop out under "turn H2O to
# cognac" (e18-e22) and slam back on "DOOMSDAY" with SPECIMEN's impact. Sound restraint (v106/v12/v13): about a dozen
# events, layered only at the set pieces (the plastic, the slide, the frost, the pour), nothing on beat moments, no chimes,
# no drones, a quiet loop bar.
def stems4(n):
    out = {}
    for nm in ("drums", "bass", "other", "vocals"):
        sr_, x = wf.read(f"{E.SONG_STEMS}/{nm}.wav"); x = x.astype(np.float32) / (32768.0 if x.dtype == np.int16 else 1.0)
        if x.ndim == 1: x = np.stack([x, x], 1)
        if sr_ != SR: x = resample_poly(x, SR, sr_, axis=0).astype(np.float32)
        out[nm] = x
    return out

def music108(song):
    n = N + PRE; tt = (np.arange(n) - PRE) / SR
    x = (E.SONG_IN + tt) * SR; i = np.clip(np.floor(x).astype(np.int64), 0, len(song) - 2); fr = (x - i)[:, None].astype(np.float32)
    mix = (song[i] * (1 - fr) + song[i + 1] * fr).astype(np.float32)
    st_ = stems4(n); k0 = I(E.SONG_IN - E.STEMS_T0) - PRE
    seg = {k: v[k0:k0 + n] for k, v in st_.items()}
    t0, t1 = E.th(18), E.th(22) - 0.006                                                    # the drop-out, back on the downbeat
    thin = seg["vocals"] + bq(seg["other"], "high", 260, 2) * 0.85
    lp = np.clip((tt - t0) / (t1 - t0), 0, 1)                                              # the sample thins out toward the drop
    thin = thin * (1 - 0.35 * lp[:, None]) + bq(thin, "low", 1800, 2) * 0.35 * lp[:, None]
    w = np.clip(np.minimum((tt - t0) / 0.012, (t1 - tt) / 0.006), 0, 1).astype(np.float32)[:, None]
    return (mix * (1 - w) + thin * 1.15 * w).astype(np.float32)

def creak(dur, level, seed):
    """plastic under tension: a dry, rising stick-slip crackle with a low body."""
    n = I(dur); q = np.arange(n) / SR; rng = np.random.default_rng(seed); y = np.zeros(n, np.float32)
    k = 0; t_ = 0.0
    while t_ < dur - 0.01:
        i0 = I(t_); m = min(I(0.012), n - i0); qq = np.arange(m) / SR
        if m > 16: y[i0:i0 + m] += (bq(noise(m, seed + k), "band", np.array([1400, 7000]), 2) * np.exp(-qq / 0.003) * rng.uniform(0.3, 1.0)).astype(np.float32)
        t_ += rng.uniform(0.008, 0.035) * (1.2 - 0.8 * t_ / dur); k += 1
    y += (bq(noise(n, seed + 99), "band", np.array([180, 900]), 2) * 0.25).astype(np.float32)
    return norm(y * np.minimum(1, q / dur * 1.6).astype(np.float32), level)

def snap(level, seed):
    """the plastic lets go: a sharp crack, a fast airy tail."""
    n = I(0.30); q = np.arange(n) / SR
    y = bq(noise(n, seed), "band", np.array([1500, 11000]), 2) * np.exp(-q / 0.010) * 1.6 + bq(noise(n, seed + 1), "band", np.array([400, 3000]), 2) * np.exp(-q / 0.06) * 0.35
    y = y + np.sin(2 * np.pi * 110 * q) * np.exp(-q / 0.03) * 0.4
    return norm(y.astype(np.float32), level)

def glass_tick(level, seed):
    """a slide set down on glass: a tiny bright tick and a short glassy ring (no chime: damped in 60 ms)."""
    n = I(0.12); q = np.arange(n) / SR; rng = np.random.default_rng(seed)
    y = bq(noise(n, seed), "band", np.array([2500, 9000]), 2) * np.exp(-q / 0.0025) * 1.2
    y = y + sum(np.sin(2 * np.pi * f * q + rng.uniform(0, 6)) * np.exp(-q / 0.018) for f in (3150, 4870, 6620)) * 0.25
    return norm(y.astype(np.float32), level)

def ice(dur, level, seed):
    """frost forming: a fine, brittle crackle that thickens."""
    y = crackle(dur, level, seed, 0.55, (3000, 12000)); n = len(y)
    return (y * np.linspace(0.3, 1.0, n) ** 1.3).astype(np.float32)

def main108():
    os.makedirs(AD, exist_ok=True)
    song = song_read10()
    if np.abs(song).max() > 2.0: song = song / 32768.0                                     # song_prep wrote song48.wav as 16-bit
    mus = music108(song) * db(-1.0)
    n = N + PRE; tt = np.arange(n) / SR - PRE / SR; th = E.th
    fx = np.zeros((n, 2), np.float32)
    fx += stereo(norm(bq(noise(n, 1890), "low", 140, 2) + 0.08 * np.sin(2 * np.pi * 44 * tt), -46))      # room tone, continuous
    t0 = {s_["n"]: s_["t0"] for s_ in E.SHOTS}; F = E.FPS
    # ---- SURFACE: the sheet is pulled over (a soft swish), it stretches (the creak), it lets go (the snap) and peels
    ts = t0["release"]
    place(fx, stereo(creak(0.40, -17, 3802), -0.2), ts - 21 / F)
    place(fx, stereo(snap(-13, 3803), 0.25), ts + 4 / F)
    # ---- the drop-out: one reverse swell into DOOMSDAY; SPECIMEN: the glass tick at entry, the bass impact on the reveal
    td = t0["reveal"]
    place(fx, RS(0.55, -15, 3810), td - 0.55)
    place(fx, stereo(glass_tick(-16, 3811), 0.3), td - 16 / F)
    place(fx, stereo(A2.impact(-5, (52, 28), 0.85, 0.30, 3812)), td); place(fx, stereo(sub_drop(-7, 0.9, 62, 26)), td + 0.01)
    # ---- the womb: the blood pours (the v107 pour), a thick glug at the cut
    tw = t0["womb"]
    place(fx, stereo(pour(0.60, -18, 3820)), tw - 0.40); place(fx, stereo(bloop(-19, 3821)), tw - 0.01)
    # ---- the ice truck: frost forms (a brittle crackle), a soft crack on the cut
    tb = t0["brother"]
    place(fx, stereo(ice(0.30, -18, 3830), -0.3), tb - 0.27)
    # ---- the tomb: the roll (a low whoosh); the photo (a shutter); into his eye; the zipper on "bagged"
    place(fx, leaves(0.45, -19, 3847), t0["day2"] - 0.24)                                            # rev 2: the fronds sweep past
    place(fx, stereo(pour(0.55, -21, 3844)), t0["syringe"] - 0.30)                                  # rev 1: the water turns (diffusion)
    place(fx, A2.whoosh(0.22, -20, 3843, False) * np.array([[1.0, 0.6]], np.float32), t0["bagged"] - 0.12)   # the wiper
    # ---- the loop: the last drop falls toward the lens (a soft airy fall); frame 0 is quiet
    place(fx, A2.whoosh(0.30, -19, 3845, False), t0["lookup"] - 0.20); place(fx, stereo(bloop(-22, 3846)), t0["lookup"] + 0.05)   # under the surface
    tl = th(68.6)
    place(fx, A2.whoosh(E.DUR - tl - 0.08, -17, 3850, True) * np.array([[0.7, 1.0]], np.float32), tl)
    fx = fx * db(10.0)                                                                         # rule 7: DOOM's master is loud
    duck = np.zeros(N + PRE, np.float32)
    for t_h in (td, ts + 4 / F): duck[I(t_h - 0.03) + PRE:I(t_h + 0.35) + PRE] = 1.0
    duck = np.convolve(duck, np.hanning(I(0.12)) / np.hanning(I(0.12)).sum(), "same")
    mus = mus * db(-3.0 * duck)[:, None]
    fx = np.tanh(fx * 1.2) / 1.2
    wf.write(f"{AD}/stem_music.wav", SR, mus[PRE:].astype(np.float32))
    wf.write(f"{AD}/stem_fx.wav", SR, fx[PRE:].astype(np.float32))
    full = mus + fx
    lead, mix = full[:PRE].copy(), full[PRE:].copy()
    th2 = np.linspace(0, np.pi / 2, PRE)[:, None]
    mix[-PRE:] = mix[-PRE:] * np.cos(th2) + lead * np.sin(th2)
    raw = f"{AD}/mix_raw.wav"; wf.write(raw, SR, mix.astype(np.float32))
    Iraw, _ = measure(raw); gain = -12.9 - Iraw
    P2 = SR; wrapped = np.vstack([mix[-P2:], mix, mix[:P2]])
    wf.write(f"{AD}/mix_raw_wrapped.wav", SR, wrapped.astype(np.float32))
    tmp = f"{AD}/mix_wrapped_master.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{AD}/mix_raw_wrapped.wav", "-af", f"volume={gain:.2f}dB,aresample=192000,"
                    f"alimiter=limit={db(-3.6):.4f}:attack=3:release=60:level=disabled,aresample=48000:resampler=soxr", "-c:a", "pcm_f32le", tmp], check=True)
    _, mw = wf.read(tmp); mw = mw.astype(np.float32)
    ref = wrapped[P2:P2 + SR, 0]; seg_ = mw[P2 - 2000:P2 + SR + 2000, 0]
    lag = int(np.argmax(np.correlate(seg_, ref, mode="valid"))) - 2000
    m = mw[P2 + lag:P2 + lag + N].copy()
    out = f"{AD}/mix.wav"; wf.write(out, SR, (np.clip(m, -1, 1) * (2 ** 31 - 1)).astype(np.int32))
    wf.write(f"{AD}/mix_preroll.wav", SR, np.vstack([m[-1024:], m]).astype(np.float32))
    test = f"{AD}/aac_test.m4a"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-itsoffset", str(-1024 / SR), "-i", f"{AD}/mix_preroll.wav", "-c:a", "aac", "-b:a", "256k", test], check=True)
    I2, TP2 = measure(out); I3, TP3 = measure(test)
    print(f"lag {lag}; raw {Iraw:.1f} -> {gain:+.1f} dB -> wav {I2:.1f} LUFS/{TP2:.1f} dBTP; AAC {I3:.1f} LUFS/{TP3:.1f} dBTP")
    mm = m.mean(1); loop = np.concatenate([mm[-24000:], mm[:24000]]); d = np.abs(np.diff(loop))
    print(f"loop seam step {d[23997:24003].max():.4f} vs local median {np.median(d[21600:26400]):.4f}")
main = main108


# ============================================================================ v109 — PHANTOM
# EsDeeKid & Rico Ace "Phantom" h24-h80 (10.48-34.48 s, 70 BPM). The song drops by itself at e6 (13.05 s). About a dozen
# events, layered only at the set pieces: the flashlight click, the materialise (a reverse swell, the impact on the drop),
# the title's breath, the phone buzz on "tantrum", the tape, the vanish, under the surface, the pour, the loop's mist.
def main109():
    os.makedirs(AD, exist_ok=True)
    song = song_read10()
    if np.abs(song).max() > 2.0: song = song / 32768.0
    mus = music107(song) * db(-1.0)
    n = N + PRE; tt = np.arange(n) / SR - PRE / SR; th = E.th
    fx = np.zeros((n, 2), np.float32)
    fx += stereo(norm(bq(noise(n, 1990), "low", 140, 2) + 0.08 * np.sin(2 * np.pi * 44 * tt), -46))
    t0 = {s_["n"]: s_["t0"] for s_ in E.SHOTS}; F = E.FPS
    place(fx, stereo(click(-16, 3901), 0.3), t0["flash"] - 4 / F)                                      # the flashlight
    td = t0["drop"]
    place(fx, RS(0.70, -14, 3902), td - 0.70)                                                           # MATERIALISE
    place(fx, stereo(A2.impact(-5, (50, 26), 0.9, 0.3, 3903)), td); place(fx, stereo(sub_drop(-7, 0.9, 60, 25)), td + 0.01)
    place(fx, A2.whoosh(0.50, -20, 3904, True) * np.array([[0.8, 1.0]], np.float32), th(10.2))        # PHANTOM condenses
    place(fx, stereo(buzz(0.30, -18, 90, 180, 3905), 0.2), t0["walk"] - 0.12)                        # the phone's tantrum
    place(fx, A2.whoosh(0.34, -19, 3912, True), t0["anthem"] - 0.26)                                  # rev 1: we pass through him
    place(fx, A2.whoosh(0.45, -19, 3907, True), t0["hall"] - 0.25)                                    # the vanish
    place(fx, A2.whoosh(0.62, -17, 3914, True), t0["hunt"] - 0.50)                                    # rev 3: THE PHANTOM'S TRAIL dives
    place(fx, stereo(fire_whoosh(-18, 0.75, 3913)), t0["hammer"] - 0.48)                               # rev 2: the photo catches, the frame burns
    tl = th(53.0); place(fx, A2.whoosh(E.DUR - tl - 0.05, -18, 3911, True), tl)                       # rev 1: THE GUST
    fx = fx * db(10.0)
    duck = np.zeros(N + PRE, np.float32); duck[I(td - 0.03) + PRE:I(td + 0.35) + PRE] = 1.0
    duck = np.convolve(duck, np.hanning(I(0.12)) / np.hanning(I(0.12)).sum(), "same")
    mus = mus * db(-3.0 * duck)[:, None]
    fx = np.tanh(fx * 1.2) / 1.2
    wf.write(f"{AD}/stem_music.wav", SR, mus[PRE:].astype(np.float32)); wf.write(f"{AD}/stem_fx.wav", SR, fx[PRE:].astype(np.float32))
    full = mus + fx; lead, mix = full[:PRE].copy(), full[PRE:].copy()
    th2 = np.linspace(0, np.pi / 2, PRE)[:, None]; mix[-PRE:] = mix[-PRE:] * np.cos(th2) + lead * np.sin(th2)
    raw = f"{AD}/mix_raw.wav"; wf.write(raw, SR, mix.astype(np.float32))
    Iraw, _ = measure(raw); gain = -12.9 - Iraw
    P2 = SR; wrapped = np.vstack([mix[-P2:], mix, mix[:P2]]); wf.write(f"{AD}/mix_raw_wrapped.wav", SR, wrapped.astype(np.float32))
    tmp = f"{AD}/mix_wrapped_master.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{AD}/mix_raw_wrapped.wav", "-af", f"volume={gain:.2f}dB,aresample=192000,"
                    f"alimiter=limit={db(-3.6):.4f}:attack=3:release=60:level=disabled,aresample=48000:resampler=soxr", "-c:a", "pcm_f32le", tmp], check=True)
    _, mw = wf.read(tmp); mw = mw.astype(np.float32)
    ref = wrapped[P2:P2 + SR, 0]; seg_ = mw[P2 - 2000:P2 + SR + 2000, 0]
    lag = int(np.argmax(np.correlate(seg_, ref, mode="valid"))) - 2000
    m = mw[P2 + lag:P2 + lag + N].copy()
    zf = 96; fade = np.sin(np.linspace(0, np.pi / 2, zf)) ** 2; m[:zf] *= fade[:, None]; m[-zf:] *= fade[::-1, None]
    out = f"{AD}/mix.wav"; wf.write(out, SR, (np.clip(m, -1, 1) * (2 ** 31 - 1)).astype(np.int32))
    wf.write(f"{AD}/mix_preroll.wav", SR, np.vstack([m[-1024:], m]).astype(np.float32))
    test = f"{AD}/aac_test.m4a"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-itsoffset", str(-1024 / SR), "-i", f"{AD}/mix_preroll.wav", "-c:a", "aac", "-b:a", "256k", test], check=True)
    I2, TP2 = measure(out); I3, TP3 = measure(test)
    print(f"lag {lag}; raw {Iraw:.1f} -> {gain:+.1f} dB -> wav {I2:.1f} LUFS/{TP2:.1f} dBTP; AAC {I3:.1f} LUFS/{TP3:.1f} dBTP")
    mm = m.mean(1); loop = np.concatenate([mm[-24000:], mm[:24000]]); d = np.abs(np.diff(loop))
    print(f"loop seam step {d[23997:24003].max():.4f} vs local median {np.median(d[21600:26400]):.4f}")
def main110():
    os.makedirs(AD, exist_ok=True)
    song = song_read10()
    if np.abs(song).max() > 2.0: song = song / 32768.0
    mus = music107(song) * db(-1.0)
    n = N + PRE; tt = np.arange(n) / SR - PRE / SR; th = E.th
    fx = np.zeros((n, 2), np.float32)
    fx += stereo(norm(bq(noise(n, 1990), "low", 140, 2) + 0.08 * np.sin(2 * np.pi * 44 * tt), -46))
    t0 = {s_["n"]: s_["t0"] for s_ in E.SHOTS}; F = E.FPS
    td = E.th(E.HDROP)                                                                                 # the drop (the power surges)
    place(fx, stereo(neon_buzz(0.45, -24)), E.th(10.2) - 0.02)                                        # the tube lights on "I'm"
    place(fx, stereo(rev(hum_rise(0.85, -20, 90, 330))), t0["fog"] - 0.32)                            # the brownout: the power dies
    place(fx, stereo(hum_rise(1.05, -21, 70, 260)), td - 1.05)                                        # the fan spins up: the power surges back
    place(fx, stereo(A2.impact(-6, (50, 26), 0.9, 0.3, 4102)), td); place(fx, stereo(sub_drop(-8, 0.8, 62, 26)), td + 0.01)
    place(fx, A2.whoosh(0.55, -18, 4103, True), t0["warm"] - 0.48)                                   # THE BARREL
    place(fx, A2.whoosh(0.70, -22, 4104, True), t0["bloodwall"] - 0.55)                                # rev 2: the swinging light carries the blood room in
    place(fx, stereo(scrub(0.16, -20, 4106, 4500)), t0["dark"] - 0.06)                                # rev 1: the print tears
    ti = E.th(74.6) + 0.36 * (E.DUR - E.th(74.6))                                                     # rev 1: THE DRIP lands
    place(fx, stereo(drip(-16, 4107)), ti - 0.01)
    fx = fx * db(10.0)
    duck = np.zeros(N + PRE, np.float32); duck[I(td - 0.03) + PRE:I(td + 0.35) + PRE] = 1.0
    duck = np.convolve(duck, np.hanning(I(0.12)) / np.hanning(I(0.12)).sum(), "same")
    mus = mus * db(-3.0 * duck)[:, None]
    fx = np.tanh(fx * 1.2) / 1.2
    wf.write(f"{AD}/stem_music.wav", SR, mus[PRE:].astype(np.float32)); wf.write(f"{AD}/stem_fx.wav", SR, fx[PRE:].astype(np.float32))
    full = mus + fx; lead, mix = full[:PRE].copy(), full[PRE:].copy()
    th2 = np.linspace(0, np.pi / 2, PRE)[:, None]; mix[-PRE:] = mix[-PRE:] * np.cos(th2) + lead * np.sin(th2)
    raw = f"{AD}/mix_raw.wav"; wf.write(raw, SR, mix.astype(np.float32))
    Iraw, _ = measure(raw); gain = -12.9 - Iraw
    P2 = SR; wrapped = np.vstack([mix[-P2:], mix, mix[:P2]]); wf.write(f"{AD}/mix_raw_wrapped.wav", SR, wrapped.astype(np.float32))
    tmp = f"{AD}/mix_wrapped_master.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{AD}/mix_raw_wrapped.wav", "-af", f"volume={gain:.2f}dB,aresample=192000,"
                    f"alimiter=limit={db(-3.6):.4f}:attack=3:release=60:level=disabled,aresample=48000:resampler=soxr", "-c:a", "pcm_f32le", tmp], check=True)
    _, mw = wf.read(tmp); mw = mw.astype(np.float32)
    ref = wrapped[P2:P2 + SR, 0]; seg_ = mw[P2 - 2000:P2 + SR + 2000, 0]
    lag = int(np.argmax(np.correlate(seg_, ref, mode="valid"))) - 2000
    m = mw[P2 + lag:P2 + lag + N].copy()
    zf = 96; fade = np.sin(np.linspace(0, np.pi / 2, zf)) ** 2; m[:zf] *= fade[:, None]; m[-zf:] *= fade[::-1, None]
    out = f"{AD}/mix.wav"; wf.write(out, SR, (np.clip(m, -1, 1) * (2 ** 31 - 1)).astype(np.int32))
    wf.write(f"{AD}/mix_preroll.wav", SR, np.vstack([m[-1024:], m]).astype(np.float32))
    test = f"{AD}/aac_test.m4a"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-itsoffset", str(-1024 / SR), "-i", f"{AD}/mix_preroll.wav", "-c:a", "aac", "-b:a", "256k", test], check=True)
    I2, TP2 = measure(out); I3, TP3 = measure(test)
    print(f"lag {lag}; raw {Iraw:.1f} -> {gain:+.1f} dB -> wav {I2:.1f} LUFS/{TP2:.1f} dBTP; AAC {I3:.1f} LUFS/{TP3:.1f} dBTP")
    mm = m.mean(1); loop = np.concatenate([mm[-24000:], mm[:24000]]); d = np.abs(np.diff(loop))
    print(f"loop seam step {d[23997:24003].max():.4f} vs local median {np.median(d[21600:26400]):.4f}")
main = main110


if __name__ == "__main__":
    main()
