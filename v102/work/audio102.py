"""[LET GO — Dexter × Tame Impala (voidfx v101) — ported from the v7 engine; rewrite the sound design below]
Benchmark notes: Soundtrack for HIM ALL ALONG (voidfx v7): Gunna "Him All Along" h528->h640 + Dexter (S1) lip-synced lines + forensic sound design.

Gunna's vocals step aside (instrumental stem) while Dexter says "A jar of blood. Dramatic. Cryptic. Playful. Could it
be him?", then return on "stay strong ... HIM ALL ALONG" into the drop. Every transition has its own sound; the edit
ends with a fast tape-stop into the pupil dive and loops into the magnifier opening. Built circularly, mastered on a
wrapped copy, AAC-checked. (Engine: v6 audio builder.)
"""
import os, sys, math, subprocess
import numpy as np, scipy.io.wavfile as wf, scipy.signal as ss
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/home/user/VOIDFX/v2/work")
import edl102 as E
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

# ------------------------------------------------------------------ v101 sounds
def crackle(dur, level=-24, seed=200, dens=0.08):
    """fire / burning-film crackle: sparse pops over a hiss bed."""
    n = I(dur); rng = np.random.default_rng(seed); y = bq(noise(n, seed), "band", np.array([2000, 9000]), 2) * 0.15
    pops = (rng.random(n) < dens * 0.004).astype(np.float32) * rng.uniform(0.3, 1, n).astype(np.float32)
    y = y + bq(np.convolve(pops, np.exp(-np.arange(80) / 12.0), "same"), "high", 900, 2) * 2.5
    return norm(y, level)

def projector(dur, level=-33, rate=24.0, seed=210, slow=None):
    """16 mm projector: claw / shutter clatter at the frame rate over a motor whir (slow=(t0, t1) winds it down)."""
    n = I(dur); t = np.arange(n) / SR; r = np.full(n, rate, np.float32)
    if slow is not None:
        a, b = slow; m = t >= a; r[m] = rate * np.clip(1 - (t[m] - a) / (b - a), 0.05, 1) ** 1.3
    ph = np.cumsum(r) / SR; frac = ph % 1.0
    click = np.exp(-frac / 0.06) * bq(noise(n, seed), "band", np.array([1200, 6000]), 2)
    thud = np.exp(-frac / 0.10) * np.sin(2 * np.pi * 140 * frac / max(rate, 1) * 24)
    whir = np.sin(2 * np.pi * np.cumsum(r * 4.5) / SR) * 0.25 + bq(noise(n, seed + 1), "band", np.array([200, 900]), 2) * 0.2
    return norm(click * 0.9 + thud * 0.25 + whir, level)

def rubber(dur=0.18, level=-24, seed=220):
    n = I(dur); q = np.arange(n) / SR; u = q / dur
    sq = np.sin(2 * np.pi * np.cumsum(420 + 900 * u ** 1.5 + 60 * np.sin(2 * np.pi * 31 * q)) / SR) * u ** 1.5
    return norm(sq * 0.7 + bq(noise(n, seed), "band", np.array([800, 3000]), 2) * 0.3 * u, level)

def snap(level=-15, seed=221):
    n = I(0.25); q = np.arange(n) / SR
    y = bq(noise(n, seed), "high", 2500, 2) * env_exp(n, 0.012, 0.0003) + np.sin(2 * np.pi * 95 * q) * env_exp(n, 0.06, 0.001) * 0.7
    return norm(y, level)

def cloth(dur=0.35, level=-24, seed=230):
    n = I(dur); u = np.arange(n) / n
    y = bq(noise(n, seed), "band", np.array([250, 2200]), 2) * np.sin(np.pi * u) ** 1.2 * (0.7 + 0.3 * np.random.default_rng(seed).random(n))
    return norm(y, level)

def bubbles(dur=0.6, level=-24, seed=240, n_=9):
    n = I(dur); y = np.zeros(n, np.float32); rng = np.random.default_rng(seed)
    for k in range(n_):
        i = I(rng.uniform(0, dur - 0.08)); m = I(0.07); tt = np.arange(m) / SR; f0 = rng.uniform(180, 520)
        y[i:i + m] += np.sin(2 * np.pi * np.cumsum(f0 * (1 + 2.5 * tt / 0.07)) / SR) * np.exp(-tt / 0.022) * rng.uniform(0.5, 1)
    return norm(y + 0.25 * bq(noise(n, seed + 1), "low", 300, 2) * np.sin(np.pi * np.arange(n) / n), level)

def glass_scrape(dur=0.32, level=-26, seed=250):
    n = I(dur); u = np.arange(n) / n
    y = bq(noise(n, seed), "band", np.array([2500, 8000]), 2) * np.sin(np.pi * u) * (1 + 0.4 * np.sin(2 * np.pi * 37 * np.arange(n) / SR))
    return norm(y, level)

def paper_rip(dur=0.38, level=-18, seed=260):
    n = I(dur); rng = np.random.default_rng(seed); u = np.arange(n) / n
    y = bq(noise(n, seed), "band", np.array([600, 7000]), 2) * (rng.random(n) > 0.45) * (1 - u) ** 0.6 * np.minimum(1, u * 30)
    return norm(bq(y, "high", 400, 2), level)

def spin_whoosh(dur=0.32, level=-21, seed=270):
    w = A2.whoosh(dur, level, seed, True); n = len(w); q = np.arange(n) / SR
    return (w * (0.6 + 0.4 * np.sin(2 * np.pi * (6 + 20 * q / dur) * q))[:, None]).astype(np.float32)

def phaser_swirl(dur=0.7, level=-25, seed=280):
    n = I(dur); x = noise(n, seed); u = np.arange(n) / n; out = np.zeros(n, np.float32); blk = 512
    for i in range(0, n, blk):
        fc = 500 * 2 ** (3 * (0.5 + 0.5 * math.sin(2 * math.pi * 1.5 * u[i])))
        sos = ss.butter(2, [fc / 1.25 / (SR / 2), min(0.95, fc * 1.25 / (SR / 2))], "band", output="sos")
        seg = x[max(0, i - 2048):i + blk]; y_ = ss.sosfilt(sos, seg)[-min(blk, n - i):]; out[i:i + len(y_)] = y_
    return stereo(norm(out * np.sin(np.pi * u) ** 1.3, level), 0.0)

def whisper_shh(dur=0.45, level=-30, seed=290):
    n = I(dur); u = np.arange(n) / n
    y = bq(noise(n, seed), "band", np.array([2200, 7500]), 4) * np.sin(np.pi * np.minimum(1, u * 1.6)) ** 0.8 * (1 - u ** 3)
    return norm(y, level)

def thump(level=-27, f0=110, seed=300):
    n = I(0.2); q = np.arange(n) / SR
    return norm(np.sin(2 * np.pi * np.cumsum(f0 * (1 + 1.5 * np.exp(-q / 0.02))) / SR) * env_exp(n, 0.07, 0.001), level)

# ------------------------------------------------------------------ v102 sounds
def zap(dur=0.12, level=-26, seed=500, f0=2600):
    """an electric arc: buzzy noise bursts + a crackling square tone."""
    n = I(dur); q = np.arange(n) / SR; rng = np.random.default_rng(seed)
    gate = (rng.random(n // 64 + 1) > 0.35).repeat(64)[:n].astype(np.float32)
    buzz = np.sign(np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.3 * rng.standard_normal(n) * 0.05) + 120) / SR)) * 0.25
    y = (bq(noise(n, seed), "band", np.array([1500, 9000]), 2) + buzz) * gate * np.exp(-q / (dur * 0.6))
    return norm(y, level)

def hum(dur, level=-34, f=60, seed=510):
    n = I(dur); q = np.arange(n) / SR
    y = sum(np.sin(2 * np.pi * f * k * q) / k for k in (1, 2, 3, 5, 7)) + 0.3 * bq(noise(n, seed), "band", np.array([2000, 7000]), 2)
    return norm(y * np.minimum(1, q / 0.05) * np.minimum(1, (dur - q) / 0.05), level)

def swell(dur, level=-24, f0=80, f1=900, seed=520):
    n = I(dur); u = np.arange(n) / n
    y = np.sin(2 * np.pi * np.cumsum(f0 * (f1 / f0) ** u) / SR) * 0.6 + bq(noise(n, seed), "band", np.array([600, 5000]), 2) * 0.5 * u
    return norm(y * u ** 2, level)

def thunder(level=-14, seed=530):
    n = I(1.4); q = np.arange(n) / SR
    crack = bq(noise(n, seed), "high", 1800, 2) * np.exp(-q / 0.025)
    body = bq(noise(n, seed + 1), "band", np.array([60, 700]), 2) * np.exp(-q / 0.45) * (1 + 0.5 * np.sin(2 * np.pi * 7 * q))
    return norm(crack * 1.4 + body, level)

def time_stop(dur=0.36, level=-24, seed=540):
    """a sucked-in reverse swell with a thin whine: time stopping."""
    n = I(dur); u = np.arange(n) / n
    rv = bq(noise(n, seed), "band", np.array([400, 6000]), 2) * u ** 3
    whine = np.sin(2 * np.pi * np.cumsum(5200 - 2600 * u) / SR) * 0.12 * np.sin(np.pi * u)
    return norm(rv + whine, level)

def doppler(dur=0.40, level=-18, seed=550):
    w = A2.whoosh(dur, level, seed, False); n = len(w); u = np.arange(n) / n
    return (w * np.stack([1.2 - u, 0.2 + u], 1)).astype(np.float32)

def rew_pos(t):
    s_ = np.clip((t - E.T_REW) / (E.DUR - E.T_REW), 0, 1)
    S = np.linspace(0, 1, 4001); C = np.concatenate([[0], np.cumsum(np.sin(np.pi * (S[1:] + S[:-1]) / 2) ** 1.5 * np.diff(S))])
    A = ((E.T_REW / (E.DUR - E.T_REW)) - 1) / C[-1]
    return np.maximum(0.0, E.T_REW - (E.DUR - E.T_REW) * (s_ + A * np.interp(s_, S, C)))

# ------------------------------------------------------------------ music
def music_track(song):
    """the window, the song's riser vocal swapped for the instrumental under Barry's line, the freeze (time stops), and the
    rewind: the song runs backwards with the picture (35x at its peak) and lands on the first sample (the loop)."""
    t = (np.arange(N + PRE) - PRE) / SR
    p = np.where(t < E.T_REW, t, rew_pos(t))                                         # edit time heard
    def rd(src, pos):
        x = pos * SR; i = np.clip(np.floor(x).astype(np.int64), 0, len(src) - 2); fr = (x - i)[:, None].astype(np.float32)
        return src[i] * (1 - fr) + src[i + 1] * fr
    pos = E.SONG_IN + p
    g = rd(song, pos)
    sr_, nv = wf.read(f"{E.SONG_VOX}/no_vocals.wav"); nv = nv.astype(np.float32)
    if np.abs(nv).max() > 2: nv /= 32768
    nv = ss.resample_poly(nv, 160, 147, axis=0).astype(np.float32)
    inst = rd(nv, pos - E.SONG_VOX_T0)
    a0, a1 = E.VOX_MUTE; xf = 0.06
    w = np.clip(np.minimum((t - a0) / xf + 0.5, (a1 - t) / xf + 0.5), 0, 1); w = (np.sin(w * np.pi / 2) ** 2)[:, None]
    g = g * (1 - w) + inst * w
    # the freeze: the world drains away under "power?" (low-pass sweep + dip), then the drop hits
    fz = np.clip((t - E.T_FREEZE) / (E.T_DROP - E.T_FREEZE), 0, 1) * (t < E.T_DROP)
    lp = bq(g, "low", 650, 2)
    g = g * (1 - 0.75 * fz[:, None]) + lp * 0.75 * fz[:, None]
    g = g * (1 - 0.35 * fz)[:, None]
    # the rewind: band-limited (it's 35x), with a short turn at each end
    rw = t >= E.T_REW
    if rw.any():
        song_lp = bq(bq(song, "low", 1400, 4), "high", 120, 2)
        rev = rd(song_lp, pos) * 1.2
        xr = np.clip((t - E.T_REW) / 0.03, 0, 1)[:, None]
        g = np.where(rw[:, None], g * (1 - xr) + rev * xr, g)
    return g.astype(np.float32)

def vo_track():
    sr, v = wf.read(E.VO_STEM); v = v.astype(np.float32)
    if np.abs(v).max() > 2: v /= 32768
    v = ss.resample_poly(v, 160, 147, axis=0).astype(np.float32)
    v = bq(v, "high", 100, 2); v = bq(v, "low", 10500, 2)
    vo = np.zeros((N + PRE, 2), np.float32); duck = np.zeros(N + PRE, np.float32)
    for k, (a, b, at) in enumerate(E.VO):
        seg = v[I(a - E.VO_STEM_T0):I(b - E.VO_STEM_T0)].mean(1)
        env = np.sqrt(np.convolve(seg ** 2, np.ones(I(0.08)) / I(0.08), "same")) + 1e-4
        g = np.clip((db(-20) / env) ** 0.5, db(-6), db(9)); g = np.convolve(g, np.ones(I(0.05)) / I(0.05), "same"); seg = seg * g
        nf = I(0.035); seg[:nf] *= np.sin(np.linspace(0, np.pi / 2, nf)) ** 2; seg[-nf:] *= np.cos(np.linspace(0, np.pi / 2, nf)) ** 2
        env2 = np.sqrt(np.convolve(seg ** 2, np.ones(I(0.05)) / I(0.05), "same")); act = env2 > env2.max() * db(-24)
        seg = seg / (np.sqrt((seg[act] ** 2).mean()) + 1e-9) * db(-14.5)
        pk = np.abs(seg).max(); seg = np.tanh(seg / max(pk, 1e-9) * 1.4) / np.tanh(1.4) * pk if pk > db(-2) else seg
        place(vo, stereo(seg), at)
        d0, d1 = I(at - 0.06) + PRE, I(at + (b - a)) + PRE; duck[d0:d1] = 1.0
    vo = vo + A2.conv(vo, A2.ir(0.25, seed=31)) * db(-26)
    sm = np.convolve(duck, np.hanning(I(0.2)) / np.hanning(I(0.2)).sum(), "same")
    return vo, sm

def main():
    os.makedirs(AD, exist_ok=True)
    if not os.path.exists(f"{AD}/song48.wav"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", E.SONG, "-ar", "48000", "-ac", "2", "-c:a", "pcm_f32le", f"{AD}/song48.wav"], check=True)
    sr, song = wf.read(f"{AD}/song48.wav"); song = song.astype(np.float32)
    mus = music_track(song) * db(-1.0)
    vo, duck = vo_track()
    mus = mus * db(-6.0 * np.clip(duck, 0, 1))[:, None]
    fx = np.zeros((N + PRE, 2), np.float32); n = N + PRE; tt = np.arange(n) / SR
    fx += stereo(norm(bq(noise(n, 90), "low", 200, 2) + 0.10 * np.sin(2 * np.pi * 60 * tt), -44))      # room tone (also across the wrap)
    # electricity builds through the cold open: a crackle bed that grows into the riser, gone on the drop
    cb = crackle(E.T_DROP, -30, 501, 0.10); ramp = np.clip(np.arange(len(cb)) / len(cb), 0, 1) ** 1.5
    place(fx, stereo(cb * (0.35 + 0.65 * ramp)), 0.0)
    for c in E.CHOPS:
        if c < E.th(732): place(fx, stereo(zap(0.06, -34, int(c * 100)), 0.2), c)                         # the eye sparks
    T = {s_["n"]: s_ for s_ in E.SHOTS}
    for s_ in E.SHOTS:
        tin, t0 = s_.get("tin"), s_["t0"]
        if tin == "rewind_in":
            place(fx, stereo(zap(0.10, -28, 601), 0.0), t0)
        elif tin == "bolt_link":
            place(fx, stereo(zap(8 / E.FPS, -26, 611), 0.1), t0 - 8 / E.FPS)
            place(fx, stereo(A2.impact(-22, (120, 60), 0.12, 0.9, 612)), t0); place(fx, A2.whoosh(0.28, -26, 613, True), t0)
        elif tin == "overcharge":
            place(fx, stereo(swell(10 / E.FPS + 0.05, -24, 70, 1200, 621)), t0 - 10 / E.FPS)
            place(fx, stereo(zap(0.16, -24, 622)), t0 - 0.02)
        elif tin == "whip":
            place(fx, A2.whoosh(0.24, -22, 631, True), t0 - 6 / E.FPS); place(fx, stereo(zap(0.08, -30, 632), 0.4), t0)
        elif tin == "strike":                                                                # HERO
            place(fx, stereo(time_stop(E.T_DROP - E.T_FREEZE, -22)), E.T_FREEZE)
            place(fx, stereo(zap(6 / E.FPS, -22, 641)), t0 - 6 / E.FPS)
            place(fx, stereo(thunder(-13, 642)), t0); place(fx, stereo(A2.impact(-13, (50, 26), 0.7, 0.4, 643)), t0)
        elif tin == "emblem":
            place(fx, stereo(hum(12 / E.FPS, -28, 120, 651)), t0 - 12 / E.FPS); place(fx, stereo(zap(0.14, -25, 652), -0.2), t0 - 8 / E.FPS)
            place(fx, A2.whoosh(0.34, -22, 653, True), t0)
        elif tin == "remnant":
            place(fx, np.stack([A2.shimmer(0.4, -30)] * 2, 1), t0); place(fx, A2.whoosh(0.22, -27, 661, False), t0)
        elif tin == "passby":
            place(fx, doppler(0.42, -18, 671), t0 - 6 / E.FPS)
        elif tin == "bolt_split":
            place(fx, stereo(zap(5 / E.FPS, -26, 681)), t0 - 5 / E.FPS); place(fx, stereo(A2.impact(-21, (110, 60), 0.10, 1.0, 682)), t0)
        elif tin == "smear":
            place(fx, A2.whoosh(0.20, -25, 691, True), t0 - 5 / E.FPS)
        elif tin == "logo_orig":
            place(fx, stereo(A2.impact(-21, (110, 60), 0.12, 0.7, 701)), t0 - 0.20)
            place(fx, np.stack([A2.shimmer(0.9, -29)] * 2, 1), t0 - 0.15); place(fx, A2.whoosh(0.32, -22, 702, True), t0 - 0.10)
        elif tin == "impact":
            place(fx, stereo(A2.impact(-16, (70, 36), 0.35, 1.0, 711)), t0); place(fx, stereo(zap(0.10, -24, 712)), t0)
        elif tin == "shockwave":
            place(fx, A2.whoosh(0.40, -21, 721, True), t0); place(fx, stereo(A2.impact(-22, (60, 30), 0.5, 0.2, 722)), t0)
    # LET / GO: an electric snap on each word (the drop's kicks carry the weight)
    for tx in E.TEXT:
        if tx["style"] == "title":
            for k_, (w, wt, ln) in enumerate(tx["words"]): place(fx, stereo(zap(0.12, -24, 730 + k_), -0.3 + 0.6 * k_), wt)
    # lightning crackle on the shots with lightning crawling over him
    for nm in ("charge", "charged", "eyes", "final_run"):
        s_ = T[nm]; place(fx, stereo(crackle(s_["t1"] - s_["t0"], -33, 740 + len(nm), 0.08), 0.2), s_["t0"])
    # the rewind: tape scrub + streaks + crackle, rising into the seam
    rdur = E.DUR - E.T_REW
    place(fx, stereo(scrub(rdur, -24, 751, 6000), 0.0), E.T_REW)
    place(fx, A2.whoosh(rdur, -24, 752, False), E.T_REW)
    place(fx, stereo(crackle(rdur, -30, 753, 0.15)), E.T_REW)
    fx = np.tanh(fx * 1.3) / 1.3
    full = mus + vo + fx
    lead, mix = full[:PRE].copy(), full[PRE:].copy()
    th_ = np.linspace(0, np.pi / 2, PRE)[:, None]
    mix[-PRE:] = mix[-PRE:] * np.cos(th_) + lead * np.sin(th_)                       # circular join
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
    def lv(a, b):
        x = m[I(a):I(min(b, E.DUR))]; return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
    print("rms: breakdown", round(lv(0.2, 5.8), 1), "riser+line", round(lv(5.9, 8.4), 1), "freeze", round(lv(8.45, 8.75), 1), "drop", round(lv(8.8, 14), 1),
          "montage", round(lv(14, 22.3), 1), "rewind", round(lv(22.35, 23.4), 1))

if __name__ == "__main__":
    main()
