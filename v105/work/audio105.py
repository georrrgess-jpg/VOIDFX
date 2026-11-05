"""DRACULA — Dexter × Tame Impala "Dracula" (voidfx v105) soundtrack.
The song window h592 -> h680 (154.55 -> 177.51 s) in one pass, no splice, built circularly: the pre-roll before frame 0 is the
song's own lead-in, crossfaded under the end, so the loop plays straight through. No dialogue (the song's voice carries the text).
Sound design (key: B-flat minor, so the tonal sounds sit in it):
  DAY: a warm sea-air bed under the lead-in; a light sweep for every sun flare; whooshes, burn, slam, quarter-turn.
  SUNDOWN (k24-32): the sun sets in a descending glide (F5 -> F2) with a heartbeat under the song's drop-out bar and a reverse
  swell into the drop.
  THE DROP (k32): a sub impact and a burst of wings (hundreds of flaps across the stereo field) with a few high bat chirps;
  "DRACULA" breaks into bats (a second flutter).
  THE BLOOD MOON (k48): a low church-bell toll on B-flat as the moon iris opens.
  THE COFFIN (k64): a hinge creak, then the lid slams (a wood thud with its own resonances) and dust.
  THE SWARM (k68): wings crossing left to right.
  DAYBREAK (k84-88): an airy B-flat-minor chord swells as the sun burns the frame white; its tail wraps into frame 0.
Night bed: a low wind and a sub drone from the drop on. Mastered on a wrapped copy to -13 LUFS, measured after AAC.
(Engine: the v104 audio builder.)
"""
import os, sys, math, subprocess
import numpy as np, scipy.io.wavfile as wf, scipy.signal as ss
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/home/user/VOIDFX/v2/work")
import edl105 as E
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
    fx = fx104()
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
    def lv(a, b):
        x = m[I(a):I(min(b, E.DUR))]; return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
    print("rms: pickup", round(lv(0.0, 1.55), 1), "P1", round(lv(1.6, 5.8), 1), "P2", round(lv(5.9, 10.1), 1), "P3", round(lv(10.2, 14.4), 1),
          "P4", round(lv(14.5, 18.7), 1), "P5", round(lv(18.8, 22.9), 1))

# ------------------------------------------------------------------ v104
def music_track(song):
    t = (np.arange(N + PRE) - PRE) / SR
    def rd(src, pos):
        x = pos * SR; i = np.clip(np.floor(x).astype(np.int64), 0, len(src) - 2); fr = (x - i)[:, None].astype(np.float32)
        return src[i] * (1 - fr) + src[i + 1] * fr
    g = rd(song, E.st(E.H0) + t)                                                       # no splice: the whole clip, one pass
    g = g * np.clip((t + 0.02) / 0.02, 0, 1)[:, None]                                  # (the pre-roll is silence before the pickup)
    return g.astype(np.float32)

def vo_track():
    vo = np.zeros((N + PRE, 2), np.float32); duck = np.zeros(N + PRE, np.float32); stems = {}
    for key, (path, t0) in E.VO_STEMS.items():
        sr, v = wf.read(path); v = v.astype(np.float32)
        if np.abs(v).max() > 2: v /= 32768
        if sr != SR: v = ss.resample_poly(v, SR // 100, sr // 100, axis=0).astype(np.float32) if sr == 44100 else v
        v = bq(v, "high", 90, 2); v = bq(v, "low", 10500, 2); stems[key] = v
    for (key, a, b, at) in E.VO:
        seg = stems[key][I(a):I(b)].mean(1)
        env = np.sqrt(np.convolve(seg ** 2, np.ones(I(0.08)) / I(0.08), "same")) + 1e-4
        g = np.clip((db(-20) / env) ** 0.5, db(-6), db(9)); g = np.convolve(g, np.ones(I(0.05)) / I(0.05), "same"); seg = seg * g
        nf = I(0.05); seg[:nf] *= np.sin(np.linspace(0, np.pi / 2, nf)) ** 2; seg[-nf:] *= np.cos(np.linspace(0, np.pi / 2, nf)) ** 2
        env2 = np.sqrt(np.convolve(seg ** 2, np.ones(I(0.05)) / I(0.05), "same")); act = env2 > env2.max() * db(-24)
        seg = seg / (np.sqrt((seg[act] ** 2).mean()) + 1e-9) * db(-14.0)
        pk = np.abs(seg).max(); seg = np.tanh(seg / max(pk, 1e-9) * 1.4) / np.tanh(1.4) * pk if pk > db(-2) else seg
        place(vo, stereo(seg), at); duck[max(0, I(at - 0.06) + PRE):I(at + (b - a)) + PRE] = 1.0
    vo = vo + A2.conv(vo, A2.ir(0.9, seed=31)) * db(-17)                              # a long, dark room: his inner voice
    return vo, np.convolve(duck, np.hanning(I(0.25)) / np.hanning(I(0.25)).sum(), "same")

def bristle(dur=0.26, level=-21, seed=900):
    """a dry sumi brush dragged across paper: grainy band-passed noise with bristle flutter."""
    n_ = I(dur); q = np.arange(n_) / SR; rng = np.random.default_rng(seed)
    x = bq(noise(n_, seed), "band", np.array([900, 7000]), 2)
    flutter = 0.55 + 0.45 * (rng.random(n_ // 120 + 1).repeat(120)[:n_] > 0.35)
    return norm(x * flutter * np.sin(np.pi * q / dur) ** 0.7, level)

def ink_plink(level=-20, seed=910):
    n_ = I(0.35); q = np.arange(n_) / SR
    tone = np.sin(2 * np.pi * (900 + 1400 * np.exp(-q / 0.02)) * q) * np.exp(-q / 0.06)
    return norm(tone + bq(noise(n_, seed), "high", 3000, 2) * np.exp(-q / 0.004) * 0.4, level)

def wet_bloom(dur=0.7, level=-22, seed=920):
    n_ = I(dur); q = np.arange(n_) / SR
    x = bq(noise(n_, seed), "low", 700, 2) * np.minimum(1, q / 0.03) * np.exp(-q / (dur * 0.45))
    return norm(x, level)

def splat(level=-15, seed=930):
    n_ = I(0.45); q = np.arange(n_) / SR; rng = np.random.default_rng(seed)
    body = bq(noise(n_, seed), "band", np.array([250, 2500]), 2) * np.exp(-q / 0.05)
    flick = bq(noise(n_, seed + 1), "band", np.array([2500, 9000]), 2) * (rng.random(n_) > 0.985) * np.exp(-q / 0.18)
    return norm(body + flick * 1.5, level)

def drone_rise(dur, level=-22, seed=940):
    n_ = I(dur); q = np.arange(n_) / SR; f0 = 41 + 20 * (q / dur) ** 2
    x = np.sin(2 * np.pi * np.cumsum(f0) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(f0 * 2.01) / SR)
    air = bq(noise(n_, seed), "band", np.array([300, 1800]), 2) * 0.35
    return norm((x + air) * (q / dur) ** 1.5, level)

def fx104():
    n = N + PRE; fx = np.zeros((n, 2), np.float32)
    fx += stereo(norm(bq(noise(n, 90), "low", 200, 2), -48))                          # room tone (across the wrap)
    th = E.th
    # THE INK DROP: it forms (a wet creak on each synth note), lets go, falls, and lands on the bass entry
    for kn in (0, 3, 6): place(fx, stereo(norm(bq(noise(I(0.08), 950 + kn), "band", np.array([1500, 5000]), 2) * np.exp(-np.arange(I(0.08)) / SR / 0.02), -36)), th(kn))
    place(fx, stereo(ink_plink(-24, 951)), th(9)); place(fx, rev_swell(th(12) - th(9), -24, 952), th(9))
    place(fx, stereo(splat(-18, 953)), th(12) - 0.01); place(fx, stereo(wet_bloom(0.9, -20, 954)), th(12))
    place(fx, stereo(A2.impact(-17, (45, 24), 0.7, 0.2, 955)), th(12))
    for s_ in E.SHOTS:
        tin, t0 = s_.get("tin"), s_["t0"]
        if tin == "brush": place(fx, stereo(bristle(0.28, -21, 960 + int(t0 * 10)), 0.3 if s_["brush"].get("red") else -0.3), t0 - 5 / E.FPS)
        elif tin in ("whip", "whip_up", "tilt", "smear", "light_sweep"): place(fx, A2.whoosh(0.26, -22, 970 + int(t0 * 10), True), t0 - 6 / E.FPS)
        elif tin == "impact": place(fx, stereo(A2.impact(-17, (80, 40), 0.3, 1.0, 975)), t0)
        elif tin == "slam": place(fx, stereo(A2.impact(-21, (90, 50), 0.15, 0.8, 976)), t0); place(fx, A2.whoosh(0.18, -25, 977, True), t0 - 3 / E.FPS)
        elif tin == "spatter":                                                           # THE SPATTER
            place(fx, rev_swell(0.35, -22, 980), t0 - 0.35); place(fx, stereo(splat(-13, 981), 0.4), t0)
            place(fx, stereo(A2.impact(-14, (55, 28), 0.5, 0.4, 982)), t0)
            for i in range(5): place(fx, stereo(drip(-30 - 2 * i, 983 + i), 0.4 - 0.1 * i), t0 + 0.25 + 0.17 * i)
        elif tin == "strobe": place(fx, stereo(strobe_zap(-23, 990)), t0 - 3 / E.FPS); place(fx, stereo(strobe_zap(-26, 991)), t0 + 2 / E.FPS)
        elif tin == "facematch": place(fx, rev_swell(0.2, -24, 992), t0 - 0.2)
        elif tin == "burn": place(fx, stereo(fire_whoosh(-21, 0.5, 993)), t0 - 0.25); place(fx, stereo(A2.impact(-22, (70, 35), 0.2, 0.7, 994)), t0)
        elif tin == "ink_bleed": place(fx, rev_swell(0.30, -22, 995), t0 - 0.30); place(fx, stereo(wet_bloom(0.6, -21, 996)), t0)
        elif tin == "passenger": place(fx, stereo(A2.impact(-14, (40, 22), 0.8, 0.3, 997)), t0); place(fx, A2.whoosh(0.4, -22, 998, False), t0 + 0.02)
        elif tin == "logo_orig":
            place(fx, stereo(A2.impact(-21, (110, 60), 0.12, 0.7, 1001)), t0 - 0.20)
            place(fx, np.stack([A2.shimmer(0.9, -29)] * 2, 1), t0 - 0.15); place(fx, A2.whoosh(0.32, -22, 1002, True), t0 - 0.10)
        elif tin == "shutter": place(fx, stereo(shutter_ticks(-21, 3, 0.025, 1003)), t0 - 5 / E.FPS); place(fx, stereo(click(-19, 1004)), t0 - 0.01)
        elif tin == "lamp_on": place(fx, stereo(lamp_click(-19, 1005)), t0 - 0.01)
        elif tin == "wrap": place(fx, stereo(plastic_crinkle(0.4, -22, 1006), -0.2), t0 - 6 / E.FPS)
        elif tin == "torch_blind":
            place(fx, stereo(lamp_click(-21, 1007)), t0 - 9 / E.FPS); place(fx, rev_swell(0.16, -22, 1008), t0 - 0.16)
            place(fx, np.stack([A2.shimmer(0.6, -27)] * 2, 1), t0 - 0.02); place(fx, stereo(A2.impact(-18, (90, 45), 0.25, 0.9, 1009)), t0)
        elif tin == "pupil_dive":
            place(fx, rev_swell(0.30, -21, 1010), t0 - 0.30); place(fx, A2.whoosh(0.30, -21, 1011, True), t0 - 14 / E.FPS)
            place(fx, stereo(A2.impact(-16, (50, 26), 0.45, 0.6, 1012)), t0 - 0.02); place(fx, A2.whoosh(0.28, -25, 1013, False), t0 + 0.03)
        elif tin == "zipper":
            for k0, dur in ((t0 - 10 / E.FPS, 10 / E.FPS), (t0, 12 / E.FPS)):
                n_ = I(dur); q = np.arange(n_) / SR; rate = 90 + 160 * q / dur
                teeth = (np.sin(2 * np.pi * np.cumsum(rate) / SR) > 0.85).astype(np.float32)
                zz = bq(noise(n_, int(k0 * 100) + 7), "band", np.array([1500, 7000]), 2) * (0.3 + teeth) * np.sin(np.pi * q / dur) ** 0.5
                place(fx, stereo(norm(zz, -22), 0.2), k0)
    # rev 2: paper foley under the pickup, sub hits on the phrase starts, risers into P3 and P5
    n_ = I(th(12)); q = np.arange(n_) / SR; rng_ = np.random.default_rng(1030)
    rustle = bq(noise(n_, 1031), "band", np.array([600, 4000]), 2) * (rng_.random(n_) > 0.93) * np.minimum(1, q / 0.4)
    place(fx, stereo(norm(np.convolve(rustle, np.ones(40) / 40, "same"), -38), -0.2), 0.0)
    for k_ in (44, 108, 140): place(fx, stereo(A2.impact(-20, (42, 22), 0.6, 0.1, 1032 + k_)), th(k_) - 0.005)
    place(fx, rev_swell(th(76) - th(70), -24, 1040), th(70)); place(fx, rev_swell(th(140) - th(132), -23, 1041), th(132))
    for s_ in E.SHOTS:                                                                 # the rotations get a deep spin whoosh
        if s_.get("tin") in ("roll", "quarter_roll"):
            place(fx, A2.whoosh(0.45, -21, 1050 + int(s_["t0"] * 10), False), s_["t0"] - 0.24); place(fx, rev_swell(0.22, -25, 1060 + int(s_["t0"])), s_["t0"] - 0.22)
    # rev 3: the sketch draws itself (brush and pen scratches on the synth notes), the page turns, the swash, the passenger's light and eyes
    for i, kn in enumerate((0, 3, 6, 9)):
        n_ = I(0.32); q = np.arange(n_) / SR; rng_ = np.random.default_rng(1100 + i)
        scr = bq(noise(n_, 1110 + i), "band", np.array([2500, 9000]), 2) * (rng_.random(n_) > 0.6) * np.sin(np.pi * q / 0.32) ** 0.6
        place(fx, stereo(norm(scr, -33), -0.3 + 0.2 * i), th(kn) + 0.02)
    for s_ in E.SHOTS:
        if s_.get("tin") == "page_turn":
            t0 = s_["t0"]; n_ = I(0.30); q = np.arange(n_) / SR; rng_ = np.random.default_rng(1120)
            flip = bq(noise(n_, 1121), "band", np.array([800, 6000]), 2) * (0.4 + (rng_.random(n_) > 0.85)) * np.sin(np.pi * q / 0.30) ** 0.8
            place(fx, stereo(norm(flip, -21), 0.3), t0 - 6 / E.FPS); place(fx, A2.whoosh(0.28, -26, 1122, True), t0 - 4 / E.FPS)
        if s_.get("swash"): place(fx, stereo(bristle(0.30, -23, 1123), -0.2), th(s_["swash"]["k0"]))
    spp = next(x for x in E.SHOTS if x.get("passenger")); kp = spp["passenger"]
    place(fx, stereo(lamp_click(-18, 1130)), th(kp["k_rise"] - 0.6))                    # the light comes on behind him
    place(fx, stereo(fire_whoosh(-24, 0.4, 1131)), th(kp["k_rise"]) + 0.02)             # the embers catch
    place(fx, stereo(A2.impact(-17, (36, 20), 0.7, 0.1, 1132)), th(kp["k_rise"]))       # a sub drop under "DARK"
    # THE PASSENGER: a dark drone rises with the shadow, and a reverse swell pulls into the lunge
    sp = next(x for x in E.SHOTS if x.get("passenger")); pk = sp["passenger"]
    place(fx, stereo(drone_rise(th(sp["k1"]) - th(pk["k_rise"]), -22, 1020)), th(pk["k_rise"]))
    place(fx, rev_swell(th(sp["k1"]) - th(pk["k_lunge"]), -19, 1021), th(pk["k_lunge"]))
    # THE SILHOUETTE: a breath of air as the world goes to paper
    sw = next(x for x in E.SHOTS if x.get("window")); place(fx, rev_swell(0.5, -27, 1022), th(sw["window"]["k_in"]) + 0.05)
    # THE INK-OUT: the picture drains (reverse swell) and the drop lifts away (a reversed plink) as the loop closes
    so = next(x for x in E.SHOTS if x.get("ink_out")); k0 = so["ink_out"]["k0"]
    place(fx, rev_swell(th(E.K_END) - th(k0) - 0.05, -22, 1023), th(k0))
    place(fx, stereo(ink_plink(-25, 1024)[::-1].copy()), E.DUR - 0.36)
    return fx


# ------------------------------------------------------------------ v105 DRACULA
TAIL = 3 * SR                                                                          # sounds that ring past the end wrap into frame 0
def vo_track():
    return np.zeros((N + PRE, 2), np.float32), np.zeros(N + PRE, np.float32)

def wings(dur=0.8, level=-22, seed=1200, count=120, rate=(7, 11), pan=None, shape=None):
    """a flock of wing flaps: each bat beats at its own rate; leathery low-mid flaps scattered across the stereo field.
    pan=(a, b) sweeps the flock across the field; shape(u) is the density envelope over the sound."""
    n = I(dur); out = np.zeros((n, 2), np.float32); rng = np.random.default_rng(seed); u_all = np.arange(n) / n
    env = shape(u_all) if shape is not None else np.sin(np.pi * u_all) ** 0.8
    kern_n = I(0.028); kq = np.arange(kern_n) / kern_n
    for b in range(count):
        r = rng.uniform(*rate); t = rng.uniform(0, 1 / r); p0 = rng.uniform(-1, 1); amp = rng.uniform(0.25, 1.0)
        k = bq(noise(kern_n, seed * 7 + b), "band", np.array([rng.uniform(250, 500), rng.uniform(1800, 3200)]), 2) * np.sin(np.pi * kq) ** 2
        while t < dur - 0.03:
            i = I(t); a_ = env[min(i, n - 1)] * amp * rng.uniform(0.6, 1.0)
            if rng.random() < env[min(i, n - 1)] + 0.05:
                p = p0 * 0.5 + (pan[0] + (pan[1] - pan[0]) * t / dur) if pan else p0
                out[i:i + kern_n, 0] += k[:n - i] * a_ * (1 - 0.5 * p); out[i:i + kern_n, 1] += k[:n - i] * a_ * (1 + 0.5 * p)
            t += 1 / r * rng.uniform(0.9, 1.1)
    return out / (np.abs(out).max() + 1e-9) * db(level)

def bat_chirps(level=-31, seed=1210, n_=5, spread=0.35):
    """a few high, fast downward chirps (heard bats are higher than this; these are pitched for the ear)."""
    rng = np.random.default_rng(seed); out = np.zeros((I(spread + 0.05), 2), np.float32)
    for c in range(n_):
        m = I(rng.uniform(0.012, 0.022)); q = np.arange(m) / SR; f = rng.uniform(7500, 9500) - 3500 * q / q[-1]
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * q / q[-1]) ** 2; i = I(rng.uniform(0, spread)); p = rng.uniform(-0.8, 0.8)
        out[i:i + m, 0] += y * (1 - 0.5 * p); out[i:i + m, 1] += y * (1 + 0.5 * p)
    return out / (np.abs(out).max() + 1e-9) * db(level)

def toll(level=-24, f0=116.54, dur=4.0):
    """a church bell on B-flat: hum, prime, minor third, fifth, octave and the upper partials, each with its own decay."""
    n = I(dur); t = np.arange(n) / SR
    parts = [(0.5, 1.0, 3.2), (1.0, 0.8, 2.4), (1.19, 0.55, 1.8), (1.5, 0.35, 1.4), (2.0, 0.5, 1.1), (2.51, 0.25, 0.7), (3.01, 0.2, 0.5), (4.1, 0.12, 0.3)]
    y = sum(a * np.sin(2 * np.pi * f0 * r * t * (1 + 0.0007 * np.sin(2 * np.pi * 4.5 * t))) * np.exp(-t / d) for r, a, d in parts)
    y = y * np.minimum(1, t / 0.004) + bq(noise(n, 1220), "band", np.array([800, 4000]), 2) * env_exp(n, 0.015, 0.0005) * 0.3
    st_ = np.stack([y, np.roll(y, I(0.011))], 1)
    st_ = st_ + A2.conv(st_, A2.ir(2.2, seed=1221)) * db(-10)
    return (st_ / (np.abs(st_).max() + 1e-9) * db(level)).astype(np.float32)

def creak(dur=0.45, level=-24, seed=1230):
    """a coffin hinge: stick-slip pulses through the wood's resonances."""
    n = I(dur); q = np.arange(n) / SR; rng = np.random.default_rng(seed)
    rate = 55 + 70 * np.sin(np.pi * q / dur) + 25 * np.convolve(rng.standard_normal(n), np.ones(I(0.02)) / I(0.02), "same") * 8
    ph = np.cumsum(np.maximum(15, rate)) / SR; pulses = (np.diff(np.floor(ph), prepend=0) > 0).astype(np.float32)
    y = sum(bq(pulses, "band", np.array([f * 0.9, f * 1.1]), 2) * a for f, a in ((480, 1.0), (1050, 0.7), (2300, 0.35)))
    return norm(y * np.sin(np.pi * q / dur) ** 0.7, level)

def wood_thud(level=-15, seed=1240):
    """the lid lands: a heavy box slam with its wooden modes."""
    n = I(1.2); t = np.arange(n) / SR
    modes = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / d) for f, a, d in ((92, 1.0, 0.16), (163, 0.7, 0.10), (271, 0.5, 0.07), (447, 0.35, 0.05), (868, 0.2, 0.03)))
    y = modes * np.minimum(1, t / 0.0015) + bq(noise(n, seed), "band", np.array([1000, 6000]), 2) * env_exp(n, 0.012, 0.0003) * 0.5
    imp = A2.impact(level - 3, (60, 32), 0.45, 0.15, seed + 1); out = np.zeros(max(n, len(imp)), np.float32)
    out[:n] += norm(y, level); out[:len(imp)] += imp
    return out

def dust(dur=0.6, level=-34, seed=1250):
    n = I(dur); q = np.arange(n) / SR; rng = np.random.default_rng(seed)
    y = bq(noise(n, seed), "band", np.array([2000, 9000]), 2) * (rng.random(n) > 0.97) * np.exp(-q / 0.25)
    return stereo(norm(np.convolve(y, np.ones(24) / 24, "same"), level))

def glide(dur, f0, f1, level=-26, seed=1260):
    """the sun sets: a pure tone (with its octave and a breath of air) gliding down."""
    n = I(dur); q = np.arange(n) / SR; u = q / dur; f = f0 * (f1 / f0) ** (u ** 1.3)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.35 * np.sin(2 * np.pi * np.cumsum(f * 2) / SR) + 0.15 * np.sin(2 * np.pi * np.cumsum(f * 3.01) / SR)
    air = bq(noise(n, seed), "band", np.array([1500, 6000]), 2) * 0.12
    e = np.minimum(1, u / 0.12) * (1 - u) ** 0.6
    st_ = np.stack([(y + air) * e, (np.roll(y, I(0.007)) + air) * e], 1)
    st_ = st_ + A2.conv(st_, A2.ir(1.2, seed=seed + 1)) * db(-12)
    return (st_ / (np.abs(st_).max() + 1e-9) * db(level)).astype(np.float32)

def dawn_chord(dur, level=-24, freqs=(349.23, 466.16, 554.37, 698.46, 830.61, 932.33, 1108.73, 1396.91)):
    """daybreak: an airy B-flat-minor(9) chord that swells as the light burns in, with a high shimmer and air."""
    n = I(dur); t = np.arange(n) / SR; u = t / dur
    y = sum(np.sin(2 * np.pi * f * t + i * 1.7) * (1 + 0.3 * np.sin(2 * np.pi * (0.4 + 0.13 * i) * t)) / (1 + 0.15 * i) for i, f in enumerate(freqs))
    air = bq(noise(n, 1270), "band", np.array([3000, 11000]), 2) * 0.35
    e = u ** 1.8
    st_ = np.stack([(y + air) * e, (np.roll(y, I(0.013)) + air) * e], 1)
    st_ = st_ + A2.conv(st_, A2.ir(1.6, seed=1271)) * db(-9)
    return (st_ / (np.abs(st_).max() + 1e-9) * db(level)).astype(np.float32)

def light_sweep_snd(level=-24, seed=1280):
    """a sun flare crossing the lens: a bright airy whoosh with a glint on top."""
    w = A2.whoosh(0.34, level, seed, True); g = np.stack([A2.shimmer(0.5, level - 6)] * 2, 1)
    out = np.zeros((max(len(w), len(g) + I(0.12)), 2), np.float32); out[:len(w)] += w; out[I(0.12):I(0.12) + len(g)] += g
    return out

def place_w(buf, sig, t):
    sig = sig if sig.ndim == 2 else np.stack([sig, sig], 1); A2.place(buf, sig, I(t) + PRE)

def cloth_whoosh(dur=0.36, level=-19, seed=1400):
    """a heavy cape swung past the lens: low-mid air with the cloth's own flutter, panned left to right."""
    n = I(dur); q = np.arange(n) / SR; u = q / dur
    x = bq(noise(n, seed), "band", np.array([140, 1400]), 2) * (0.75 + 0.25 * np.sin(2 * np.pi * 23 * q + 3 * np.sin(2 * np.pi * 4 * q)))
    x = x * np.sin(np.pi * u) ** 1.4 + bq(noise(n, seed + 1), "band", np.array([1500, 5000]), 2) * 0.25 * np.sin(np.pi * u) ** 3
    snap = np.zeros(n, np.float32); i0 = int(n * 0.62); m_ = I(0.04)
    snap[i0:i0 + m_] = bq(noise(m_, seed + 2), "band", np.array([300, 3000]), 2) * np.exp(-np.arange(m_) / SR / 0.012)
    y = norm(x + 1.6 * snap, level); pan = np.linspace(-0.8, 0.8, n)
    return np.stack([y * (1 - 0.5 * pan), y * (1 + 0.5 * pan)], 1).astype(np.float32)

def mist_breath(dur=0.55, level=-22, seed=1410):
    """turning to mist: an airy breath that swells and drifts, with a low hollow whoom under it."""
    n = I(dur); q = np.arange(n) / SR; u = q / dur
    air = bq(noise(n, seed), "band", np.array([700, 6500]), 2) * np.sin(np.pi * u) ** 1.2
    whoom = np.sin(2 * np.pi * np.cumsum(70 - 25 * u) / SR) * np.sin(np.pi * u) ** 2 * 0.6
    st_ = np.stack([air + whoom, np.roll(air, I(0.009)) + whoom], 1)
    st_ = st_ + A2.conv(st_, A2.ir(1.0, seed=seed + 1)) * db(-8)
    return (st_ / (np.abs(st_).max() + 1e-9) * db(level)).astype(np.float32)

def big_wings(level=-18, seed=1420, n_=3, rate=4.5):
    """the great bat: a few heavy, leathery wingbeats getting louder as it nears."""
    dur = n_ / rate + 0.2; n = I(dur); out = np.zeros(n, np.float32)
    for k in range(n_):
        m_ = I(0.11); kq = np.arange(m_) / m_; i0 = I(k / rate)
        beat = bq(noise(m_, seed + k), "band", np.array([90, 1100]), 2) * np.sin(np.pi * kq) ** 1.5 * (0.45 + 0.55 * (k + 1) / n_)
        out[i0:i0 + m_] += beat
    return stereo(norm(out, level))

def crackle(dur=1.6, level=-26, seed=1430):
    """embers: a sizzle and fine crackle that build as the light takes him."""
    n = I(dur); u = np.arange(n) / n; rng = np.random.default_rng(seed)
    sz = bq(noise(n, seed), "band", np.array([3000, 9000]), 2) * 0.25 * u ** 1.5
    ck = np.zeros(n, np.float32)
    for _ in range(int(220 * dur)):
        i = int(rng.uniform(0, 1) ** 0.6 * (n - I(0.004))); m_ = I(rng.uniform(0.001, 0.004))
        ck[i:i + m_] += rng.uniform(0.2, 1) * bq(noise(m_, int(rng.integers(1e6))), "high", 1800, 2)
    y = sz + ck * u ** 0.8
    st_ = np.stack([y, np.roll(y, I(0.004))], 1)
    return (st_ / (np.abs(st_).max() + 1e-9) * db(level)).astype(np.float32)

def fx105():
    n = N + PRE + TAIL; fx = np.zeros((n, 2), np.float32); th = E.th; t32 = th(32)
    tt = (np.arange(n) - PRE) / SR
    sea = bq(noise(n, 1300), "low", 900, 2) * (0.75 + 0.25 * np.sin(2 * np.pi * tt / 2.6))           # DAY: sea air, fading at sunset
    day = np.clip(1 - (tt - th(24)) / (t32 - th(24)), 0, 1) * (tt < t32)
    fx += stereo(norm(sea * day, -40), 0.0)
    wind = bq(noise(n, 1301), "band", np.array([120, 700]), 2) * (0.7 + 0.3 * np.sin(2 * np.pi * tt / 3.7))   # NIGHT: a low wind and a sub drone
    night = np.clip((tt - t32) / 0.4, 0, 1) * np.clip((th(86.5) - tt) / 1.0, 0, 1)
    drone = np.sin(2 * np.pi * 58.27 * tt) * 0.6 + np.sin(2 * np.pi * 116.54 * tt + 0.5) * 0.25
    fx += np.stack([norm(wind * night, -39), norm(np.roll(wind, 4000) * night, -39)], 1) + stereo(norm(drone * night, -37))
    fx += stereo(norm(bq(noise(n, 90), "low", 200, 2), -50))                          # room tone (across the wrap)
    for s_ in E.SHOTS:
        tin, t0 = s_.get("tin"), s_["t0"]
        if tin == "sun_flare": place_w(fx, light_sweep_snd(-20, 1310 + int(t0 * 10)), t0 - 0.17)
        elif tin in ("whip", "whip_up", "tilt", "smear"): place_w(fx, A2.whoosh(0.26, -22, 1320 + int(t0 * 10), tin != "whip_up" or True), t0 - 6 / E.FPS)
        elif tin == "light_sweep": place_w(fx, light_sweep_snd(-21, 1325), t0 - 0.15)
        elif tin == "impact": place_w(fx, stereo(A2.impact(-17, (80, 40), 0.3, 1.0, 1330)), t0)
        elif tin == "slam": place_w(fx, stereo(A2.impact(-21, (90, 50), 0.15, 0.8, 1331)), t0); place_w(fx, A2.whoosh(0.18, -25, 1332, True), t0 - 3 / E.FPS)
        elif tin == "burn": place_w(fx, stereo(fire_whoosh(-21, 0.5, 1333)), t0 - 0.25); place_w(fx, stereo(A2.impact(-22, (70, 35), 0.2, 0.7, 1334)), t0)
        elif tin == "strobe": place_w(fx, stereo(strobe_zap(-23, 1335)), t0 - 3 / E.FPS); place_w(fx, stereo(strobe_zap(-26, 1336)), t0 + 2 / E.FPS)
        elif tin == "facematch": place_w(fx, rev_swell(0.2, -24, 1337), t0 - 0.2)
        elif tin == "logo_orig":
            place_w(fx, stereo(A2.impact(-21, (110, 60), 0.12, 0.7, 1338)), t0 - 0.20)
            place_w(fx, np.stack([A2.shimmer(0.9, -29)] * 2, 1), t0 - 0.15); place_w(fx, A2.whoosh(0.32, -22, 1339, True), t0 - 0.10)
        elif tin == "shutter": place_w(fx, stereo(shutter_ticks(-21, 3, 0.025, 1340)), t0 - 5 / E.FPS); place_w(fx, stereo(click(-19, 1341)), t0 - 0.01)
        elif tin == "lamp_on": place_w(fx, stereo(lamp_click(-19, 1342)), t0 - 0.01); place_w(fx, rev_swell(0.25, -27, 1343), t0 - 0.25)
        elif tin == "torch_blind":
            place_w(fx, stereo(lamp_click(-21, 1344)), t0 - 9 / E.FPS); place_w(fx, rev_swell(0.16, -22, 1345), t0 - 0.16)
            place_w(fx, np.stack([A2.shimmer(0.6, -27)] * 2, 1), t0 - 0.02); place_w(fx, stereo(A2.impact(-18, (90, 45), 0.25, 0.9, 1346)), t0)
        elif tin == "pupil_dive":
            place_w(fx, rev_swell(0.30, -21, 1347), t0 - 0.30); place_w(fx, A2.whoosh(0.30, -21, 1348, True), t0 - 14 / E.FPS)
            place_w(fx, stereo(A2.impact(-16, (50, 26), 0.45, 0.6, 1349)), t0 - 0.02); place_w(fx, A2.whoosh(0.28, -25, 1350, False), t0 + 0.03)
        elif tin == "zipper":
            for k0, dur in ((t0 - 10 / E.FPS, 10 / E.FPS), (t0, 12 / E.FPS)):
                n_ = I(dur); q = np.arange(n_) / SR; rate = 90 + 160 * q / dur
                teeth = (np.sin(2 * np.pi * np.cumsum(rate) / SR) > 0.85).astype(np.float32)
                zz = bq(noise(n_, int(k0 * 100) + 7), "band", np.array([1500, 7000]), 2) * (0.3 + teeth) * np.sin(np.pi * q / dur) ** 0.5
                place_w(fx, stereo(norm(zz, -22), 0.2), k0)
        elif tin in ("roll", "quarter_roll"):
            place_w(fx, A2.whoosh(0.45, -21, 1351 + int(t0 * 10), False), t0 - 0.24); place_w(fx, rev_swell(0.22, -25, 1352 + int(t0)), t0 - 0.22)
        elif tin == "bat_burst":                                                         # THE DROP
            place_w(fx, rev_swell(0.42, -20, 1360), t0 - 0.42)
            place_w(fx, stereo(A2.impact(-13, (46, 24), 0.9, 0.5, 1361)), t0 - 0.005)
            place_w(fx, wings(0.75, -19, 1362, 160, (8, 13), shape=lambda u: np.clip(u / 0.12, 0, 1) * (1 - u) ** 1.4), t0 - 0.13)
            place_w(fx, bat_chirps(-30, 1363, 6, 0.4), t0 + 0.04)
        elif tin == "bat_swarm":
            place_w(fx, wings(0.55, -17, 1364, 90, (8, 12), pan=(-0.9, 0.9)), t0 - 8 / E.FPS); place_w(fx, bat_chirps(-33, 1365, 3, 0.25), t0)
        elif tin == "moon_iris":                                                         # THE BLOOD MOON
            place_w(fx, rev_swell(0.30, -24, 1366), t0 - 0.30); place_w(fx, toll(-22), t0 - 0.01)
            place_w(fx, stereo(A2.impact(-19, (40, 22), 0.9, 0.1, 1367)), t0)
        elif tin == "eclipse":                                                           # the sun goes out
            place_w(fx, rev_swell(0.30, -22, 1460), t0 - 0.30); place_w(fx, stereo(A2.impact(-17, (44, 24), 1.0, 0.05, 1461)), t0 - 0.02)
            place_w(fx, np.stack([A2.shimmer(1.1, -24)] * 2, 1), t0); place_w(fx, toll(-27, 116.54, 2.5), t0 + 0.02)
        elif tin == "card_flip":                                                         # the card turns over
            place_w(fx, A2.whoosh(0.30, -17, 1462, True), t0 - 9 / E.FPS); place_w(fx, stereo(click(-20, 1463)), t0 - 0.005)
        elif tin == "palm_sweep":                                                        # palm fronds past the lens
            place_w(fx, leaves(0.45, -15, 1464), t0 - 9 / E.FPS); place_w(fx, A2.whoosh(0.26, -19, 1465, False), t0 - 6 / E.FPS)
        elif tin == "cape":                                                              # the cape sweeps the lens
            place_w(fx, cloth_whoosh(0.36, -12, 1440), t0 - 8 / E.FPS)
        elif tin == "mist":                                                              # he turns to mist
            place_w(fx, mist_breath(0.62, -18, 1441), t0 - 10 / E.FPS); place_w(fx, rev_swell(0.3, -26, 1442), t0 - 0.3)
        elif tin == "bat_pass":                                                          # the great bat flies through the lens
            place_w(fx, big_wings(-13, 1443, 3, 4.5), t0 - 0.62); place_w(fx, A2.whoosh(0.30, -16, 1444, False), t0 - 0.10)
            place_w(fx, bat_chirps(-29, 1445, 2, 0.08), t0 - 0.16); place_w(fx, stereo(A2.impact(-22, (60, 32), 0.3, 0.3, 1446)), t0)
        elif tin == "coffin":                                                            # THE COFFIN
            place_w(fx, stereo(creak(0.30, -21, 1368), -0.3), t0 - 0.36); place_w(fx, A2.whoosh(0.16, -24, 1369, False), t0 - 8 / E.FPS)
            place_w(fx, stereo(wood_thud(-14, 1370)), t0 - 0.004); place_w(fx, dust(0.6, -33, 1371), t0 + 0.02)
            place_w(fx, A2.whoosh(0.22, -27, 1372, True), t0 + 0.06)
    # SUNDOWN: the sun goes down in a glide across the song's drop-out bar, a heartbeat under it
    place_w(fx, glide(th(31.6) - th(24), 698.46, 87.31, -27), th(24))
    for kb in (26.0, 26.6, 28.0, 28.6, 30.0, 30.6): place_w(fx, stereo(heartbeat(-21 if kb % 2 == 0 else -24)), th(kb))
    # "DRACULA" breaks into bats as the title leaves
    hero = next(x for x in E.TEXT if x["style"] == "hero"); place_w(fx, wings(0.45, -21, 1380, 40, (9, 12), shape=lambda u: np.clip(u / 0.1, 0, 1) * (1 - u)), hero["end"] - 0.05)
    # sub hits on the phrase starts
    for k_ in (48, 64): place_w(fx, stereo(A2.impact(-21, (42, 22), 0.6, 0.1, 1390 + k_)), th(k_) - 0.005)
    # ASHES TO SUN: he burns (crackle and a paper-burn hiss), the embers rise into the sun (a riser), the sun flares (a bright
    # impact and shimmer), the light collapses back into it (a reverse swell) and the loop lands on frame 0 with a warm bloom
    place_w(fx, crackle(th(86.8) - th(83.6), -16, 1450), th(83.6))
    n_ = I(th(86.5) - th(84.3)); q = np.arange(n_) / SR
    hiss = bq(noise(n_, 1451), "band", np.array([2500, 9000]), 2) * np.sin(np.pi * q / q[-1]) ** 0.7
    place_w(fx, stereo(norm(hiss, -22), -0.2), th(84.3))
    place_w(fx, A2.riser(th(86.75) - th(85.2), -16, 1452), th(85.2))
    place_w(fx, stereo(A2.impact(-17, (90, 50), 0.5, 0.25, 1453)), th(86.75)); place_w(fx, np.stack([A2.shimmer(1.4, -22)] * 2, 1), th(86.75))
    place_w(fx, rev_swell(E.DUR - th(87.25), -19, 1454), th(87.25))
    place_w(fx, dawn_chord(th(88) - th(83.5), -20), th(83.5))
    place_w(fx, stereo(A2.impact(-21, (60, 34), 1.2, 0.0, 1455)), E.DUR - 0.004)            # the warm bloom as the sun of frame 0 lands (wraps)
    place_w(fx, np.stack([A2.shimmer(1.6, -27)] * 2, 1), E.DUR - 0.02)
    over = fx[N + PRE:]; fx = fx[:N + PRE]; fx[PRE:PRE + len(over)] += over         # wrap the tail into the start of the loop
    return fx

def main():
    os.makedirs(AD, exist_ok=True)
    if not os.path.exists(f"{AD}/song48.wav"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", E.SONG, "-ar", "48000", "-ac", "2", "-c:a", "pcm_f32le", f"{AD}/song48.wav"], check=True)
    sr, song = wf.read(f"{AD}/song48.wav"); song = song.astype(np.float32)
    mus = music_track(song) * db(-1.0)
    vo, duck = vo_track()
    fx = fx105() * db(9.0)                                                             # the song is mastered loud: the design sits ~8-10 dB under it
    fx = np.tanh(fx * 1.3) / 1.3
    duck = np.zeros(N + PRE, np.float32)                                               # the music gives way for the big hits
    for k_ in (32, 48, 64): duck[I(E.th(k_) - 0.03) + PRE:I(E.th(k_) + 0.30) + PRE] = 1.0
    duck = np.convolve(duck, np.hanning(I(0.12)) / np.hanning(I(0.12)).sum(), "same")
    mus = mus * db(-3.0 * duck)[:, None]
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
    def lv(a, b):
        x = m[I(a):I(min(b, E.DUR))]; return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
    th = E.th
    print("rms: verse", round(lv(0, th(24)), 1), "sundown", round(lv(th(24), th(32)), 1), "drop", round(lv(th(32), th(48)), 1),
          "moon", round(lv(th(48), th(64)), 1), "coffin", round(lv(th(64), th(84)), 1), "daybreak", round(lv(th(84), E.DUR), 1))

if __name__ == "__main__":
    main()
