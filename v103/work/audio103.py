"""[FOREVER — Dexter × Foo Fighters "Everlong" (voidfx v103) sound design. Ported head: [FOREVER — Dexter × Foo Fighters (voidfx v103) — ported from the v9 engine; rewrite the sound design below]
Previous edit: NIGHT BLOOM (voidfx v9) soundtrack. fakemink "Night, Blooming Jasmine": segment A h448->h506 (the filtered breakdown,
the song's own dead silence, the drop) + segment B h634->h650 ("I swear I'm on a mission / Night bloom jasmine, second
name Yasmin"), spliced on the downbeat where the 4-bar instrumental cycle repeats. Two Dexter lines (Demucs stems of p9):
"I had to evolve. It was the only way to survive." over the breakdown; "Hello, Arthur Mitchell." alone in the silence.
Night-garden crickets across the wrap, a sound for every transition, a low-pass "night closes" into the drop of blood.
Built circularly, mastered on a wrapped copy, measured after AAC. (Engine: v7/v8 audio builder.)
"""
import os, sys, math, subprocess
import numpy as np, scipy.io.wavfile as wf, scipy.signal as ss
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/home/user/VOIDFX/v2/work")
import edl103 as E
import audio2 as A2

SR = 48000; AD = f"{E.ROOT}/{E.VER}/audio"
N = int(round(E.DUR_F / E.FPS * SR))
PRE = 4800
def I(t): return int(round(t * SR))
db, bq, noise, env_exp = A2.db, A2.bq, A2.noise, A2.env_exp
def place(out, sig, t):
    A2.place(out, sig if sig.ndim == 2 else np.stack([sig, sig], 1), I(t) + PRE)
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


# ------------------------------------------------------------------ v103 sounds
def water_rumble(dur, level=-34, seed=700):
    n = I(dur); y = bq(noise(n, seed), "low", 180, 2) + 0.3 * bq(noise(n, seed + 1), "band", np.array([200, 700]), 2)
    return norm(y * (1 + 0.25 * np.sin(2 * np.pi * 0.35 * np.arange(n) / SR)), level)

def bubble_burst(dur=0.6, level=-24, seed=710, n_=10):
    n = I(dur); y = np.zeros(n, np.float32); rng = np.random.default_rng(seed)
    for k in range(n_):
        i = I(rng.uniform(0, dur - 0.08)); m = I(0.06); tt = np.arange(m) / SR; f0 = rng.uniform(250, 900)
        y[i:i + m] += np.sin(2 * np.pi * np.cumsum(f0 * (1 + 2.0 * tt / 0.06)) / SR) * np.exp(-tt / 0.018) * rng.uniform(0.5, 1)
    return norm(y, level)

def splash(level=-14, seed=720, dur=0.9):
    n = I(dur); q = np.arange(n) / SR
    y = bq(noise(n, seed), "band", np.array([300, 7000]), 2) * np.minimum(1, q / 0.01) * np.exp(-q / 0.22)
    y = y + np.sin(2 * np.pi * 70 * q) * np.exp(-q / 0.12) * 0.8
    return norm(y, level)

def surface_break(level=-18, seed=730):
    n = I(0.6); q = np.arange(n) / SR; u = q / 0.6
    y = bq(noise(n, seed), "band", np.array([500, 6000]), 2) * np.sin(np.pi * np.minimum(1, u * 2)) ** 2 * np.exp(-np.maximum(0, u - 0.5) * 6)
    return norm(y, level)

def glass_clack(level=-14, seed=740):
    n = I(0.35); q = np.arange(n) / SR
    tone = sum(np.sin(2 * np.pi * f * q) * np.exp(-q / d) for f, d in ((2350, 0.05), (3720, 0.035), (5100, 0.02)))
    hit = bq(noise(n, seed), "band", np.array([1500, 8000]), 2) * np.exp(-q / 0.006)
    return norm(tone * 0.6 + hit + np.sin(2 * np.pi * 120 * q) * np.exp(-q / 0.04) * 0.5, level)

def squelch(dur=0.30, level=-20, seed=750):
    n = I(dur); q = np.arange(n) / SR
    y = bq(noise(n, seed), "band", np.array([200, 1600]), 2) * np.exp(-q / (dur * 0.4)) * (1 + 0.7 * np.sin(2 * np.pi * (18 + 30 * q) * q))
    return norm(y, level)

def blade_draw(dur=0.30, level=-20, seed=760):
    n = I(dur); q = np.arange(n) / SR; u = q / dur
    ring_ = np.sin(2 * np.pi * 6200 * q) * 0.25 + np.sin(2 * np.pi * 8900 * q) * 0.15
    scrape = bq(noise(n, seed), "band", np.array([3000, 9000]), 2)
    return norm((scrape + ring_) * np.sin(np.pi * u) ** 0.7, level)

def tape_slap(level=-18, seed=770):
    n = I(0.12); q = np.arange(n) / SR
    return norm(bq(noise(n, seed), "band", np.array([300, 3000]), 2) * np.exp(-q / 0.02) + np.sin(2 * np.pi * 140 * q) * np.exp(-q / 0.03) * 0.6, level)

def tape_rip(dur=0.30, level=-17, seed=780):
    n = I(dur); rng = np.random.default_rng(seed); u = np.arange(n) / n
    y = bq(noise(n, seed), "band", np.array([800, 8000]), 2) * (rng.random(n) > 0.5) * (1 - u) ** 0.5 * np.minimum(1, u * 40)
    return norm(y, level)

def lamp_click(level=-20, seed=790):
    n = I(0.25); q = np.arange(n) / SR
    c = bq(noise(n, seed), "high", 2000, 2) * np.exp(-q / 0.004)
    hum_ = (np.sin(2 * np.pi * 120 * q) + 0.4 * np.sin(2 * np.pi * 240 * q)) * np.minimum(1, q / 0.05) * 0.12
    return norm(c + hum_, level)

def plastic_crinkle(dur=0.4, level=-22, seed=800):
    n = I(dur); rng = np.random.default_rng(seed)
    y = bq(noise(n, seed), "band", np.array([1500, 9000]), 2) * (rng.random(n) > 0.82) * np.sin(np.pi * np.arange(n) / n)
    return norm(bq(np.convolve(y, np.ones(30) / 30, "same"), "high", 900, 2), level)

def heart(level=-18):
    n = I(0.5); q = np.arange(n) / SR; y = np.zeros(n, np.float32)
    for t0, a in ((0.0, 1.0), (0.17, 0.7)):
        tt = np.clip(q - t0, 0, None); y += a * np.sin(2 * np.pi * 52 * tt) * np.exp(-tt / 0.07) * (q >= t0)
    return norm(bq(y, "low", 200, 2), level)

def glass_tinkles(dur, level=-34, seed=810, n_=24):
    n = I(dur); y = np.zeros((n, 2), np.float32); rng = np.random.default_rng(seed)
    for k in range(n_):
        i = I(rng.uniform(0, dur - 0.2)); m = I(0.18); q = np.arange(m) / SR; f0 = rng.uniform(2500, 6500)
        s_ = (np.sin(2 * np.pi * f0 * q) + 0.4 * np.sin(2 * np.pi * f0 * 1.51 * q)) * np.exp(-q / 0.05) * rng.uniform(0.4, 1)
        p_ = rng.uniform(-0.8, 0.8); y[i:i + m, 0] += s_ * (1 - 0.5 * p_); y[i:i + m, 1] += s_ * (1 + 0.5 * p_)
    return (y / (np.abs(y).max() + 1e-9) * db(level)).astype(np.float32)

# ------------------------------------------------------------------ music: the window with its splice; under water at both ends
def music_track(song):
    t = (np.arange(N + PRE) - PRE) / SR
    def rd(src, pos):
        x = pos * SR; i = np.clip(np.floor(x).astype(np.int64), 0, len(src) - 2); fr = (x - i)[:, None].astype(np.float32)
        return src[i] * (1 - fr) + src[i + 1] * fr
    tw = t                                                                             # the pre-roll is what leads into frame 0: the muffled bridge
    pa = E.st(E.H0) + tw; pb = E.st(E.H_SPL_IN) + (tw - E.T_SPLICE)
    a_ = rd(song, pa); b_ = rd(song, pb)
    c = np.clip((tw - E.T_SPLICE) / 0.012 + 0.5, 0, 1)[:, None]                       # 12 ms equal-power splice on the downbeat
    g = a_ * np.cos(c * np.pi / 2) + b_ * np.sin(c * np.pi / 2)
    sr_, nv = wf.read(f"{E.SONG_VOX}/no_vocals.wav"); nv = nv.astype(np.float32)
    if np.abs(nv).max() > 2: nv /= 32768
    nv = ss.resample_poly(nv, 160, 147, axis=0).astype(np.float32)
    inst = rd(nv, np.where(tw < E.T_SPLICE, pa, pb))
    a0, a1 = E.VOX_MUTE; xf = 0.08
    w = np.clip(np.minimum((tw - a0) / xf + 0.5, (a1 - tw) / xf + 0.5), 0, 1); w = (np.sin(w * np.pi / 2) ** 2)[:, None]
    g = g * (1 - w) + inst * w
    # under water: muffled at the start until the surface breaks, and again as the bag goes under (it wraps)
    lp = bq(bq(g, "low", 420, 2), "low", 420, 2) * 1.6
    uw = np.where(tw < E.T_SURFACE + 0.1, 1 - np.clip((tw - (E.T_SURFACE - 0.18)) / 0.22, 0, 1), np.clip((tw - E.T_SPLASH - 0.12) / 0.20, 0, 1))[:, None]
    g = g * (1 - uw) + lp * uw
    sink = np.clip((tw - E.T_SPLASH - 0.12) / (E.DUR - E.T_SPLASH - 0.12), 0, 1)[:, None]
    g = g * (1 - 0.80 * sink ** 0.8)
    return g.astype(np.float32)

def vo_track():
    sr, v = wf.read(E.VO_STEM); v = v.astype(np.float32)
    if np.abs(v).max() > 2: v /= 32768
    v = ss.resample_poly(v, 160, 147, axis=0).astype(np.float32)
    v = bq(v, "high", 90, 2); v = bq(v, "low", 10500, 2)
    vo = np.zeros((N + PRE, 2), np.float32); duck = np.zeros(N + PRE, np.float32)
    for (a, b, at) in E.VO:
        seg = v[I(a - E.VO_STEM_T0):I(b - E.VO_STEM_T0)].mean(1)
        env = np.sqrt(np.convolve(seg ** 2, np.ones(I(0.08)) / I(0.08), "same")) + 1e-4
        g = np.clip((db(-20) / env) ** 0.5, db(-6), db(9)); g = np.convolve(g, np.ones(I(0.05)) / I(0.05), "same"); seg = seg * g
        nf = I(0.04); seg[:nf] *= np.sin(np.linspace(0, np.pi / 2, nf)) ** 2; seg[-nf:] *= np.cos(np.linspace(0, np.pi / 2, nf)) ** 2
        env2 = np.sqrt(np.convolve(seg ** 2, np.ones(I(0.05)) / I(0.05), "same")); act = env2 > env2.max() * db(-24)
        seg = seg / (np.sqrt((seg[act] ** 2).mean()) + 1e-9) * db(-15.0)
        pk = np.abs(seg).max(); seg = np.tanh(seg / max(pk, 1e-9) * 1.4) / np.tanh(1.4) * pk if pk > db(-2) else seg
        place(vo, stereo(seg), at); duck[I(at - 0.05) + PRE:I(at + (b - a)) + PRE] = 1.0
    vo = vo + A2.conv(vo, A2.ir(0.45, seed=31)) * db(-20)                             # a little room: his inner voice
    return vo, np.convolve(duck, np.hanning(I(0.2)) / np.hanning(I(0.2)).sum(), "same")

def main():
    os.makedirs(AD, exist_ok=True)
    if not os.path.exists(f"{AD}/song48.wav"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", E.SONG, "-ar", "48000", "-ac", "2", "-c:a", "pcm_f32le", f"{AD}/song48.wav"], check=True)
    sr, song = wf.read(f"{AD}/song48.wav"); song = song.astype(np.float32)
    mus = music_track(song) * db(-1.0)
    vo, duck = vo_track()
    mus = mus * db(-4.0 * np.clip(duck, 0, 1))[:, None]
    fx = np.zeros((N + PRE, 2), np.float32); n = N + PRE
    fx += stereo(norm(bq(noise(n, 90), "low", 200, 2), -46))                          # room tone (across the wrap)
    tt = (np.arange(n) - PRE) / SR; tw = np.mod(tt, E.DUR)
    uw = np.where(tw < E.T_SURFACE, 1.0, np.clip((tw - E.T_SPLASH - 0.12) / 0.2, 0, 1))      # the underwater rumble (wraps)
    fx += stereo(water_rumble((n) / SR + 0.01, -30, 701)[:n] * uw)
    place(fx, stereo(bubble_burst(0.9, -28, 711, 8)), 0.05)
    T = {s_["n"]: s_ for s_ in E.SHOTS}
    for s_ in E.SHOTS:
        tin, t0 = s_.get("tin"), s_["t0"]
        if tin == "surface":
            place(fx, stereo(surface_break(-18)), E.T_SURFACE - 0.14); place(fx, stereo(splash(-24, 721, 0.5)), E.T_SURFACE - 0.02)
        elif tin == "wave":
            place(fx, A2.whoosh(0.45, -22, 731, True), t0 - 8 / E.FPS); place(fx, stereo(splash(-25, 732, 0.6), 0.3), t0 - 0.02)
        elif tin == "lamp_on":
            place(fx, stereo(lamp_click(-19)), t0 - 0.01)
        elif tin == "wrap":
            place(fx, stereo(plastic_crinkle(0.45, -21, 741), -0.2), t0 - 6 / E.FPS)
        elif tin == "light_sweep":
            place(fx, A2.whoosh(0.30, -25, 742, True), t0 - 7 / E.FPS)
        elif tin == "sample":                                                          # HERO: the slide slams on the drop
            place(fx, A2.riser(0.7, -23), t0 - 0.7)
            place(fx, stereo(glass_clack(-13)), t0); place(fx, stereo(A2.impact(-12, (55, 28), 0.6, 0.3, 743)), t0)
            place(fx, stereo(squelch(0.30, -19, 744)), t0 + 0.02); place(fx, A2.whoosh(0.35, -22, 745, True), t0 + 9 / E.FPS)
        elif tin == "impact":
            place(fx, stereo(A2.impact(-17, (80, 40), 0.3, 1.0, 751)), t0)
        elif tin == "knife_pass":
            place(fx, stereo(swish(-18, 0.14, 752), 0.4), t0 - 0.10); place(fx, stereo(metal_shing(-22)), t0)
        elif tin == "whip":
            place(fx, A2.whoosh(0.22, -21, 753, True), t0 - 5 / E.FPS)
        elif tin == "tape":
            place(fx, stereo(tape_slap(-18, 761), -0.3), t0 - 6 / E.FPS + 0.03); place(fx, stereo(tape_slap(-19, 762), 0.3), t0 - 3 / E.FPS + 0.03)
            place(fx, stereo(tape_rip(0.32, -17, 763)), t0 + 0.04)
        elif tin == "logo_orig":
            place(fx, stereo(A2.impact(-21, (110, 60), 0.12, 0.7, 771)), t0 - 0.20)
            place(fx, np.stack([A2.shimmer(0.9, -29)] * 2, 1), t0 - 0.15); place(fx, A2.whoosh(0.32, -22, 772, True), t0 - 0.10)
        elif tin == "rainfocus":
            place(fx, stereo(norm(bq(noise(I(1.2), 781), "band", np.array([2000, 8000]), 2) * (np.random.default_rng(782).random(I(1.2)) > 0.9), -34)), t0 - 0.15)
        elif tin == "blood_lens":
            place(fx, stereo(drip(-17, 783)), t0 - 0.13); place(fx, stereo(squelch(0.25, -24, 784)), t0 + 0.02)
        elif tin == "drop_out":
            place(fx, stereo(heart(-18)), E.ARCH_IN + 0.05); place(fx, stereo(heart(-17)), E.ARCH_IN + 0.55)
            place(fx, stereo(bloop(-20, 785)), t0 - 0.05); place(fx, A2.whoosh(0.5, -22, 786, True), t0)
            place(fx, glass_tinkles(E.ARCH_END - t0, -33, 787), t0 + 0.1)
        elif tin == "through_slide":
            place(fx, stereo(glass_clack(-24, 788)), t0 - 0.02); place(fx, A2.whoosh(0.35, -23, 789, False), t0 - 18 / E.FPS)
    # the scalpel draws the cut; beads well up
    place(fx, stereo(blade_draw(0.30, -20)), E.T_CUT - 0.10); place(fx, stereo(squelch(0.4, -27, 790)), E.T_CUT + 0.15)
    # text: soft hits on the hero titles' lines
    for tx in E.TEXT:
        if tx["style"] == "hero":
            for k_, (w, wt, ln) in enumerate(tx["words"]): place(fx, stereo(A2.impact(-26, (90, 50), 0.10, 0.6, 800 + k_)), wt)
    # the burial: the bag hits the water, under we go, bubbles
    place(fx, stereo(splash(-13, 811)), E.T_SPLASH - 0.03)
    place(fx, stereo(bubble_burst(E.DUR - E.T_SPLASH - 0.1, -24, 812, 16)), E.T_SPLASH + 0.12)
    place(fx, stereo(A2.impact(-22, (45, 25), 0.6, 0.0, 813)), E.T_SPLASH + 0.12)
    fx = np.tanh(fx * 1.3) / 1.3
    full = mus + vo + fx
    lead, mix = full[:PRE].copy(), full[PRE:].copy()
    th_ = np.linspace(0, np.pi / 2, PRE)[:, None]
    mix[-PRE:] = mix[-PRE:] * np.cos(th_) + lead * np.sin(th_)
    raw = f"{AD}/mix_raw.wav"; wf.write(raw, SR, mix.astype(np.float32))
    Iraw, _ = measure(raw); gain = -13.0 - Iraw
    P2 = SR; wrapped = np.vstack([mix[-P2:], mix, mix[:P2]])
    wf.write(f"{AD}/mix_raw_wrapped.wav", SR, wrapped.astype(np.float32))
    tmp = f"{AD}/mix_wrapped_master.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{AD}/mix_raw_wrapped.wav", "-af", f"volume={gain:.2f}dB,aresample=192000,"
                    f"alimiter=limit={db(-4.2):.4f}:attack=3:release=60:level=disabled,aresample=48000:resampler=soxr", "-c:a", "pcm_f32le", tmp], check=True)
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
    sp = I(E.T_SPLICE); print(f"splice step {np.abs(np.diff(mm[sp - 50:sp + 50])).max():.4f} vs local median {np.median(np.abs(np.diff(mm[sp - 4800:sp + 4800]))):.4f}")
    def lv(a, b):
        x = m[I(a):I(min(b, E.DUR))]; return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
    print("rms: underwater", round(lv(0.0, 1.0), 1), "VO", round(lv(2.0, 3.8), 1), "build", round(lv(5, 10.5), 1), "drop", round(lv(10.7, 15), 1),
          "hook", round(lv(17, 24.5), 1), "sink", round(lv(25.0, 25.8), 1))

if __name__ == "__main__":
    main()
