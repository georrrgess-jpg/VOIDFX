"""[THE LESS YOU KNOW — Dexter × Tame Impala (voidfx v101) — ported from the v7 engine; rewrite the sound design below]
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
import edl101 as E
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

# ------------------------------------------------------------------ music
def music_track(song):
    """the window h7 -> h91, then the song's own intro pickup (h3 -> h7) for the last half bar, so the loop wraps into h7.
    the song's faint intro vocal is swapped for the instrumental stem under Dexter's line."""
    t = (np.arange(N + PRE) - PRE) / SR
    tb = E.th(E.H_BREAK)
    p = E.SONG_IN + t                                                                # song position (s) for the groove part
    pick = E.st(E.PICKUP_H) + (t - tb)                                               # song position of the pickup
    def rd(src, pos):
        x = pos * SR; i = np.clip(np.floor(x).astype(np.int64), 0, len(src) - 2); fr = (x - i)[:, None].astype(np.float32)
        return src[i] * (1 - fr) + src[i + 1] * fr
    g = rd(song, p); pk = rd(song, pick)
    sr_, nv = wf.read(f"{E.SONG_VOX}/no_vocals.wav"); nv = nv.astype(np.float32)
    if np.abs(nv).max() > 2: nv /= 32768
    nv = ss.resample_poly(nv, 160, 147, axis=0).astype(np.float32)
    inst = rd(nv, p - E.SONG_VOX_T0)
    a0, a1 = E.VOX_MUTE; xf = 0.08
    w = np.clip(np.minimum((t - a0) / xf + 0.5, (a1 - t) / xf + 0.5), 0, 1); w = (np.sin(w * np.pi / 2) ** 2)[:, None]
    g = g * (1 - w) + inst * w
    xb = 0.012                                                                       # 12 ms equal-power splice onto the pickup
    c = np.clip((t - tb) / xb + 0.5, 0, 1); c = c[:, None]
    out = g * np.cos(c * np.pi / 2) + pk * np.sin(c * np.pi / 2)
    # wrap: before t=0 (pre-roll) the pickup plays into the downbeat (circular)
    m = t < 0; out[m] = rd(song, E.SONG_IN + t[m])
    return out.astype(np.float32)

def vo_track():
    sr, v = wf.read(E.VO_STEM); v = v.astype(np.float32)
    if np.abs(v).max() > 2: v /= 32768
    v = ss.resample_poly(v, 160, 147, axis=0).astype(np.float32)
    v = bq(v, "high", 90, 2); v = bq(v, "low", 10500, 2)
    vo = np.zeros((N + PRE, 2), np.float32); duck = np.zeros(N + PRE, np.float32)
    for k, (a, b, at) in enumerate(E.VO):
        seg = v[I(a - E.VO_STEM_T0):I(b - E.VO_STEM_T0)].mean(1)
        env = np.sqrt(np.convolve(seg ** 2, np.ones(I(0.08)) / I(0.08), "same")) + 1e-4
        g = np.clip((db(-20) / env) ** 0.5, db(-6), db(9)); g = np.convolve(g, np.ones(I(0.05)) / I(0.05), "same"); seg = seg * g
        nf = I(0.04); seg[:nf] *= np.sin(np.linspace(0, np.pi / 2, nf)) ** 2; seg[-nf:] *= np.cos(np.linspace(0, np.pi / 2, nf)) ** 2
        env2 = np.sqrt(np.convolve(seg ** 2, np.ones(I(0.05)) / I(0.05), "same")); act = env2 > env2.max() * db(-24)
        seg = seg / (np.sqrt((seg[act] ** 2).mean()) + 1e-9) * db(-15.5)
        pk = np.abs(seg).max(); seg = np.tanh(seg / max(pk, 1e-9) * 1.4) / np.tanh(1.4) * pk if pk > db(-2) else seg
        place(vo, stereo(seg), at)
        d0, d1 = I(at - 0.06) + PRE, I(at + (b - a)) + PRE; duck[d0:d1] = 1.0
    vo = vo + A2.conv(vo, A2.ir(0.30, seed=31)) * db(-24)
    sm = np.convolve(duck, np.hanning(I(0.25)) / np.hanning(I(0.25)).sum(), "same")
    return vo, sm

def main():
    os.makedirs(AD, exist_ok=True)
    if not os.path.exists(f"{AD}/song48.wav"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", E.SONG, "-ar", "48000", "-ac", "2", "-c:a", "pcm_f32le", f"{AD}/song48.wav"], check=True)
    sr, song = wf.read(f"{AD}/song48.wav"); song = song.astype(np.float32)
    mus = music_track(song) * db(-1.0)
    vo, duck = vo_track()
    mus = mus * db(-5.5 * np.clip(duck, 0, 1))[:, None]
    fx = np.zeros((N + PRE, 2), np.float32); n = N + PRE; tt = np.arange(n) / SR
    # room tone + projector hum bed across the whole loop (also across the wrap)
    bed = bq(noise(n, 90), "low", 240, 2) + 0.12 * np.sin(2 * np.pi * 60 * tt) + 0.05 * np.sin(2 * np.pi * 120 * tt)
    fx += stereo(norm(bed, -42))
    # the projector runs through the cold open (it stalls on the drop), and again as the reel runs out
    pr = projector(E.T_DROP + 0.05, -35, slow=(E.T_DROP - 0.42, E.T_DROP + 0.02)); place(fx, stereo(pr, -0.2), 0.0)
    T = {s_["n"]: s_ for s_ in E.SHOTS}
    for s_ in E.SHOTS:
        tin, t0 = s_.get("tin"), s_["t0"]
        if tin == "projector_on":                                         # lamp strikes, motor spins up (the loop entry)
            place(fx, stereo(A2.impact(-26, (80, 45), 0.12, 0.6, 301)), t0 + 4 / E.FPS)
            place(fx, stereo(A2.tick(-24, 302)), t0 + 6 / E.FPS); place(fx, stereo(A2.tick(-27, 303)), t0 + 9 / E.FPS)
            place(fx, A2.whoosh(0.30, -30, 304, True), t0)
        elif tin == "latex":                                              # glove stretched -> snap
            place(fx, stereo(rubber(10 / E.FPS, -25), 0.3), t0 - 10 / E.FPS); place(fx, stereo(snap(-16), 0.2), t0)
        elif tin == "frameslip":                                          # the loop is lost: clatter burst, slip, clack
            place(fx, stereo(projector(0.30, -26, rate=48, seed=311)), t0 - 8 / E.FPS)
            place(fx, A2.whoosh(0.22, -25, 312, False), t0 - 3 / E.FPS); place(fx, stereo(A2.impact(-22, (150, 80), 0.06, 0.9, 313)), t0 + 7 / E.FPS)
        elif tin == "filmmelt":                                           # HERO: stall, sizzle, the film burns through on the bass drop
            place(fx, stereo(crackle(18 / E.FPS + 0.05, -27, 321, 0.06)), t0 - 18 / E.FPS)
            place(fx, stereo(crackle(0.9, -24, 322, 0.12), 0.1), t0 - 0.02)
            place(fx, stereo(A2.impact(-11, (55, 28), 0.7, 0.5, 323)), t0)
            n_ = I(0.6); q = np.arange(n_) / SR
            whoomp = bq(noise(n_, 324), "band", np.array([120, 1600]), 2) * np.minimum(1, q / 0.03) * np.exp(-q / 0.18)
            place(fx, stereo(norm(whoomp, -16)), t0 - 0.02); place(fx, A2.whoosh(0.4, -21, 325, True), t0 - 0.05)
        elif tin == "whip":
            place(fx, A2.whoosh(0.24, -19, 331, True), t0 - 6 / E.FPS)
        elif tin == "hooddark":                                           # the hood is pulled down over the lens
            place(fx, stereo(cloth(0.30, -22, 341), -0.2), t0 - 9 / E.FPS); place(fx, stereo(thump(-25, 80, 342)), t0)
            place(fx, stereo(cloth(0.25, -26, 343), 0.2), t0 + 2 / E.FPS)
        elif tin == "scalpel":
            place(fx, stereo(swish(-17, 0.11, 351), 0.5), t0 - 5 / E.FPS); place(fx, stereo(metal_shing(-22)), t0 - 0.03)
            place(fx, stereo(A2.impact(-20, (75, 38), 0.25, 0.6, 352)), t0)
        elif tin == "lavalamp":
            place(fx, stereo(bubbles(0.7, -22, 361), -0.2), t0 - 12 / E.FPS)
            place(fx, A2.whoosh(0.4, -27, 362, True), t0 - 0.15)
        elif tin == "slidewipe":
            place(fx, stereo(glass_scrape(0.33, -25, 371), 0.4), t0 - 9 / E.FPS); place(fx, stereo(glass_chime(-28), -0.4), t0 + 10 / E.FPS)
        elif tin == "newsspin":
            place(fx, spin_whoosh(0.26, -21, 381), t0); tl = t0 + 0.78 * 18 / E.FPS
            place(fx, stereo(A2.impact(-17, (95, 50), 0.15, 0.7, 382)), tl)
            n_ = I(0.09); q = np.arange(n_) / SR; place(fx, stereo(norm(bq(noise(n_, 383), "band", np.array([500, 5000]), 2) * np.exp(-q / 0.02), -18)), tl)
        elif tin == "papertear":
            place(fx, np.stack([paper_rip(0.40, -18, 391), np.roll(paper_rip(0.40, -18, 391), 60)], 1), t0 - 6 / E.FPS)
        elif tin == "logo_orig":
            place(fx, stereo(A2.impact(-20, (110, 60), 0.12, 0.7, 401)), t0 - 0.20)
            place(fx, np.stack([A2.shimmer(0.9, -28)] * 2, 1), t0 - 0.15); place(fx, A2.whoosh(0.32, -21, 402, True), t0 - 0.10)
        elif tin == "oilwheel":
            place(fx, phaser_swirl(0.75, -25, 411), t0 - 10 / E.FPS); place(fx, stereo(bubbles(0.4, -31, 412, 5)), t0)
        elif tin == "facematch":
            place(fx, A2.whoosh(0.26, -24, 421, False), t0 - 7 / E.FPS); place(fx, stereo(thump(-28, 70, 422)), t0)
    # the shh, the freeze on the break, the reel running out (into the projector start: loop)
    sh = T["shh"]; place(fx, stereo(whisper_shh(0.5, -31), 0.1), sh["t0"] + 0.30)
    tb = E.th(E.H_BREAK)
    place(fx, stereo(A2.impact(-19, (70, 36), 0.35, 0.4, 431)), tb); place(fx, stereo(A2.tick(-22, 432)), tb + 0.01)
    te_ = E.DUR - 30 / E.FPS
    place(fx, stereo(projector(E.DUR - te_ + 0.1, -27, rate=30, seed=433, slow=(0.25, 0.55))), te_)
    n_ = I(0.32); q = np.arange(n_) / SR                                              # the film tail flapping on the take-up reel
    flap = bq(noise(n_, 434), "band", np.array([400, 4000]), 2) * (np.sin(2 * np.pi * (14 + 8 * q / 0.32) * q) > 0.3)
    place(fx, stereo(norm(flap * np.sin(np.pi * q / 0.32), -27)), E.DUR - 0.36)
    # text: each word of the title lands on a bass note with a soft thump; BETTER. lands on the freeze
    for tx in E.TEXT:
        for k_, (w, wt, ln) in enumerate(tx["words"]):
            if tx["style"] == "title": place(fx, stereo(thump(-30, 120 + 10 * k_, 440 + k_), -0.3 + 0.2 * k_), wt + 6 / E.FPS)
            if tx["style"] == "better" and k_ == 1: place(fx, stereo(thump(-26, 90, 450)), wt + 6 / E.FPS)
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
    print("rms: open", round(lv(0.2, 4.0), 1), "line", round(lv(4.2, 8.1), 1), "drop", round(lv(8.3, 12), 1), "montage", round(lv(12, 21.4), 1),
          "break", round(lv(21.6, 22.4), 1))

if __name__ == "__main__":
    main()
