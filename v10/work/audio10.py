"""LET IT HAPPEN (voidfx v10) soundtrack. Tame Impala "Let It Happen" (radio edit) h392 -> h496 (94.32 -> 119.28 s):
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
import edl10 as E
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

def music10(song):
    """the window straight; the pre-roll carries the breakdown across the wrap; after "around" (e101) the song rewinds
    at speed back to 94.32 s (decelerating as it lands, like the picture's flight back to frame 0), then the loop.
    rev 3: an equal-power 12 ms crossfade from the forward song into the rewind (no repeated samples at the join)."""
    n = N + PRE; tt = (np.arange(n) - PRE) / SR; t_rew = E.th(E.E_REW + 1); xf = 0.012; t0r = t_rew - xf
    def take(pos):
        x = pos * SR; i = np.clip(np.floor(x).astype(np.int64), 0, len(song) - 2); fr = (x - i)[:, None].astype(np.float32)
        return song[i] * (1 - fr) + song[i + 1] * fr
    fwd = take(E.SONG_IN + tt)
    u = np.clip((tt - t0r) / (E.DUR - t0r), 0, 1); eo = 1 - (1 - u) ** 1.25
    xr = ((E.SONG_IN + t0r) - t0r * eo) * SR                                            # the rewind, box-filtered over
    Pc = np.vstack([np.zeros((1, 2)), np.cumsum(song.astype(np.float64), 0)])           # each output sample's span (no aliasing)
    def integ(x):
        i = np.clip(np.floor(x).astype(np.int64), 0, len(song) - 1); return Pc[i] + song[i].astype(np.float64) * (x - i)[:, None]
    xa = np.concatenate([[xr[0]], xr[:-1]]); d = xr - xa; big = np.abs(d) > 1.0
    rew = take(xr / SR)
    rew[big] = ((integ(xr[big]) - integ(xa[big])) / d[big][:, None]).astype(np.float32)
    rew = bq(rew, "low", 6000, 2)
    g = 0.55 + 0.45 * np.clip(1 - (tt - t_rew) / 0.04, 0, 1)                         # down to 0.55 over 40 ms
    w = np.clip((tt - t0r) / xf, 0, 1)[:, None]
    return (fwd * np.cos(w * np.pi / 2) + rew * g[:, None] * np.sin(w * np.pi / 2)).astype(np.float32)

def main():
    os.makedirs(AD, exist_ok=True)
    song = song_read10()
    mus = music10(song) * db(-1.0)
    fx = np.zeros((N + PRE, 2), np.float32); n = N + PRE; tt = np.arange(n) / SR - PRE / SR; th = E.th
    fx += stereo(norm(bq(noise(n, 790), "low", 140, 2) + 0.08 * np.sin(2 * np.pi * 44 * tt), -44))
    # a low electrical crackle bed where the Speed Force crawls over him (cold open, the run)
    cw = np.zeros(n, np.float32)
    for a0, a1, lv in ((-PRE / SR, th(32), 1.0), (th(88), th(100), 0.9)):
        cw = np.maximum(cw, np.clip(np.minimum((tt - a0) / 0.4, (a1 - tt) / 0.08), 0, 1) * lv)
    bed = crackle(E.DUR + PRE / SR + 0.05, -36, 840, 0.6)[:n]
    bed = np.pad(bed, (0, n - len(bed)))
    fx += stereo(bed * cw, 0.0) * np.array([[1.0, 0.9]], np.float32)
    for s_ in E.SHOTS:
        tin, t0 = s_.get("tin"), s_["t0"]
        if tin == "slices":                                       # bands rip past: a rippled run of short whooshes
            for q in range(5): place(fx, A2.whoosh(0.12, -27 - q, 990 + q, q % 2 == 0), t0 - 0.10 + q * 0.035)
        elif tin == "bolt_tear":                                  # a crack across his chest, then the frame rips open
            place(fx, stereo(crackle(0.12, -23, 995, 0.9)), t0 - 5 / 60); place(fx, stereo(zap(-22, 996, 2800, 400, 0.14)), t0)
            n_ = I(0.35); q_ = np.arange(n_) / SR
            rip = bq(noise(n_, 997), "band", np.array([600, 5000]), 2) * np.exp(-q_ / 0.10) * (np.random.default_rng(998).random(n_) > 0.5)
            place(fx, stereo(norm(rip, -24)), t0 + 0.01)
        elif tin == "arc_link":
            place(fx, stereo(crackle(0.30, -24, 850 + int(t0 * 10)), 0.2), t0 - 0.10); place(fx, stereo(zap(-27, 851, 2600, 900, 0.10)), t0)
        elif tin == "ignite":
            place(fx, stereo(whine(0.30, -30, 300, 1800)), t0 - 0.05); place(fx, stereo(crackle(0.45, -23, 860, 0.5)), t0 + 0.02)
        elif tin == "emblem_gate":                               # THE DROP: charge whine -> crack -> sub boom -> rush through the bolt
            place(fx, stereo(whine(0.36, -24, 500, 5200)), t0 - 0.36); place(fx, stereo(crackle(0.36, -25, 861, 0.7)), t0 - 0.36)
            place(fx, stereo(A2.impact(-9, (50, 26), 0.9, 0.5, 862)), t0)
            place(fx, stereo(thunder(-17, 863, 1.0)), t0); place(fx, A2.whoosh(0.45, -20, 864, True), t0 - 0.03)
            place(fx, stereo(sub_drop(-15, 0.8)), t0 + 0.04)                                  # the particle-accelerator wave
        elif tin == "ramp": place(fx, A2.whoosh(0.22, -24, 870 + int(t0), True), t0 - 0.10)
        elif tin == "bolt_link":                                 # the thrown bolt tears across the stereo field
            n_ = I(0.32); y = crackle(0.32, -20, 875, 0.9); p_ = np.linspace(0.9, -0.9, n_)
            place(fx, np.stack([y * (1 - p_) / 1.4, y * (1 + p_) / 1.4], 1).astype(np.float32), t0 - 7 / 60)
            place(fx, stereo(zap(-22, 876, 3600, 500, 0.16)), t0)
        elif tin == "shock": place(fx, stereo(A2.impact(-18, (70, 40), 0.30, 0.6, 880)), t0); place(fx, stereo(crackle(0.4, -25, 881, 0.6)), t0 + 0.02)
        elif tin == "prism_cut": place(fx, stereo(zap(-27, 885, 1800, 4800, 0.10), -0.3), t0 - 0.03)
        elif tin == "logo_orig":
            place(fx, stereo(A2.impact(-21, (110, 60), 0.12, 0.7, 890)), t0 - 0.20)
            place(fx, np.stack([A2.shimmer(0.9, -30)] * 2, 1), t0 - 0.15); place(fx, A2.whoosh(0.32, -22, 891, True), t0 - 0.10)
        elif tin == "bolt_strike": place(fx, stereo(thunder(-15, 895, 1.4)), t0 - 0.02); place(fx, stereo(zap(-24, 896, 4000, 300, 0.2)), t0 - 0.06)
        elif tin == "freeze_in":                                 # time stops: a reverse swell into a dead tick
            sw = A2.whoosh(0.35, -27, 900, False)[::-1].copy(); place(fx, sw, t0 - 0.35); place(fx, stereo(tick(-22, 901)), t0)
        elif tin == "jolt": place(fx, stereo(zap(-26, 905, 2200, 700, 0.08)), t0)
        elif tin == "phase":                                     # he vibrates through: a rising buzz, a phased whoom
            place(fx, stereo(buzz(0.18, -23)), t0 - 0.17); place(fx, A2.whoosh(0.30, -24, 1330, True), t0 - 0.04)
        elif tin == "whirlwind":                                 # the frame is carried off: wind torn round once
            place(fx, swirl(0.62, -20, 1331, 1.0), t0 - 0.24); place(fx, A2.whoosh(0.25, -25, 1332, False), t0 - 0.08)
        elif tin == "lichtenberg":                               # the figure branches out with a sizzle, then a snap
            cr = crackle(0.40, -23, 1333, 0.9) * np.linspace(0.3, 1.0, I(0.40)) ** 1.5
            place(fx, stereo(cr.astype(np.float32)), t0 - 0.17); place(fx, stereo(zap(-24, 1334, 3600, 700, 0.12)), t0)
        elif tin == "lens_shatter":                              # the bolt comes at us, hits the glass, the glass bursts
            place(fx, stereo(whine(0.14, -24, 900, 5200)), t0 - 0.14); place(fx, stereo(glass(-17, 1335, 1.0)), t0)
            place(fx, stereo(A2.impact(-17, (90, 45), 0.20, 0.6, 1336)), t0); place(fx, A2.whoosh(0.30, -23, 1337, True), t0 + 0.06)
        elif tin == "perimeter":                                 # a lap of the frame: the pass circles the stereo field
            place(fx, swirl(0.40, -21, 1338, 1.3), t0 - 0.14); place(fx, stereo(crackle(0.35, -27, 1339, 0.8)), t0 - 0.12)
        elif tin == "time_particles":                            # the moment comes apart into grains, hangs, rebuilds on the hit
            th_hit = th(E.STUT_HITS[2])
            place(fx, crumble(0.55, -23, 1400), t0 - 0.20)
            place(fx, np.stack([A2.shimmer(0.45, -31)] * 2, 1), t0 + 0.02)
            rb = crumble(0.42, -22, 1401)[::-1].copy() * np.linspace(0.4, 1.0, I(0.42))[:, None] ** 1.5
            place(fx, rb.astype(np.float32), th_hit - 0.42); place(fx, stereo(A2.impact(-19, (75, 40), 0.25, 0.5, 1402)), th_hit)
        elif tin == "frozen_shatter":                            # in stopped time a dull crack; the beat blows the shards away
            place(fx, stereo(glass(-22, 1340, 0.6, dull=True)), t0 - 0.02)
            th_hit = th(E.STUT_HITS[2]); place(fx, stereo(glass(-19, 1341, 0.8)), th_hit); place(fx, A2.whoosh(0.3, -24, 1342, True), th_hit - 0.05)
        elif tin == "restart":                                   # time restarts on the second impact
            place(fx, stereo(A2.impact(-12, (55, 28), 0.7, 0.5, 910)), t0); place(fx, A2.whoosh(0.4, -21, 911, True), t0 - 0.05)
            place(fx, stereo(crackle(0.5, -23, 912, 0.7)), t0 + 0.03)
    for e_ in E.STUT_GAPS: place(fx, stereo(tick(-25, 920 + e_)), th(e_) + 0.01)      # the clock in frozen time
    cut_e = {s_["e0"] for s_ in E.SHOTS}
    for e_ in list(range(34, 74, 2)) + list(range(90, 99, 2)):                            # rev 5: a swish on each camera punch
        if e_ in cut_e or e_ in (56, 58): continue
        place(fx, A2.whoosh(0.12, -33, 1500 + e_, e_ % 4 == 0), th(e_) - 0.06)
    for e0_ in (74, 78, 86):                                                              # bullet time: the camera glides
        n_ = I(0.46); q_ = np.arange(n_) / SR
        air = bq(noise(n_, 1440 + e0_), "band", np.array([250, 1800]), 2) * np.sin(np.pi * q_ / 0.46) ** 2
        pn = np.linspace(-0.6, 0.6, n_) * (1 if e0_ != 78 else -1)
        a_ = norm(air, -33); place(fx, np.stack([a_ * (1 - pn) / 1.3, a_ * (1 + pn) / 1.3], 1).astype(np.float32), th(e0_) + 0.01)
    for e_ in E.STUT_HITS: place(fx, stereo(zap(-31, 925 + e_, 2400, 900, 0.08), 0.4), th(e_))   # the time-line ripple
    # edge bolts on the bar lines (cold open, the hook, the run) and the gold sweeps of the cold open: soft, under the song
    for e_ in list(range(8, 32, 8)) + [56, 64, 88, 96]:
        place(fx, np.stack([crackle(0.16, -31, 1000 + e_, 0.9), crackle(0.16, -32, 1100 + e_, 0.9)], 1), th(e_))
    for e_ in range(8, 30, 8):
        n_ = I(0.24); q_ = np.arange(n_) / SR
        sh = sum(np.sin(2 * np.pi * fq * q_) for fq in (3136, 4186, 5274)) * np.sin(np.pi * q_ / 0.24) ** 2
        place(fx, stereo(norm(sh, -36), -0.5), th(e_) + 0.02)
    # type: the bolts striking LET IT / HAPPEN, the HAPPENS slam, the echo, the run-in words
    for tx in E.TEXT:
        if tx["style"] == "carry":                                # the runner drops each word off, then carries them off
            def zip_(dur, lv, seed):
                y = swirl(dur, lv, seed, 0.25); return y
            for k_, (w, wt, ln) in enumerate(tx["words"]):
                place(fx, zip_(0.16, -27, 1410 + k_), wt - 0.10); place(fx, stereo(crackle(0.08, -33, 1420 + k_, 0.9), 0.3), wt - 0.02)
            for k_, d0 in enumerate((0.0, 0.08)):
                place(fx, zip_(0.22, -24, 1430 + k_), tx["end"] - 0.44 + d0 - 0.04)
            place(fx, stereo(crackle(0.25, -29, 1432, 0.9)), tx["end"] - 0.42)
        if tx["style"] == "bound":                                # the gust takes the words; BOUND is struck
            tb = [wt for w, wt, _ in tx["words"] if w == "BOUND"][0]
            place(fx, wind_gust(0.45, -26, 1350, (-0.4, 0.9)), tb + 0.08); place(fx, stereo(zap(-27, 1351, 3800, 900, 0.10)), tx["end"] - 0.11)
        if tx["style"] == "charge":                               # AND charges up through its long note
            (w0, t0_, _), (w1, t1_, _) = tx["words"]
            place(fx, stereo(hum_rise(t1_ - t0_ - 0.1, -29)), t0_ + 0.1); place(fx, stereo(zap(-25, 1352, 4200, 1200, 0.10)), t1_)
        if tx["style"] == "hero":
            for k_, (w, wt, ln) in enumerate(tx["words"]):
                for q in range(len(w)): place(fx, stereo(zap(-31, 930 + k_ * 10 + q, 3800, 1500, 0.05), -0.5 + 0.2 * q), wt + 0.04 * q)
            for tp in tx.get("pulses", []): place(fx, stereo(crackle(0.25, -27, 950 + int(tp * 10), 0.8)), tp)
        elif tx["style"] == "slam":
            place(fx, stereo(A2.impact(-20, (90, 50), 0.15, 0.7, 960)), tx["words"][1][1]); place(fx, stereo(crackle(0.3, -27, 961, 0.6)), tx["words"][1][1])
        elif tx["style"] == "echo":
            for k_, (w, wt, ln) in enumerate(tx["words"]): place(fx, A2.whoosh(0.14, -31, 965 + k_, True), wt - 0.08)
        elif tx["style"] == "speed":
            for k_, (w, wt, ln) in enumerate(tx["words"]): place(fx, A2.whoosh(0.16, -30, 970 + k_, False), wt - 0.08)
    # the run becomes light: a rising whine into the line; the rewind: a tunnel rush + a landing thump at the wrap
    place(fx, stereo(whine(0.95, -24, 600, 6000)), th(E.E_REW) - 0.95); place(fx, A2.whoosh(0.6, -22, 980, True), th(E.E_REW) - 0.5)
    T_OPEN = 23.85
    place(fx, stereo(crackle(0.30, -24, 1360, 0.9)), T_OPEN - 0.02); place(fx, stereo(zap(-25, 1361, 1500, 5200, 0.14)), T_OPEN)
    place(fx, swirl(0.42, -22, 1362, 1.5), T_OPEN + 0.06)                                 # the letters run the ring
    for q in range(9):                                                                     # the edit's moments rush past
        place(fx, A2.whoosh(0.10, -31 + q * 0.4, 1370 + q, q % 2 == 0), th(E.E_REW) + 0.03 + q * 0.085)
    rw = bq(noise(I(0.96), 981), "band", np.array([400, 5000]), 2) * np.linspace(1, 0.2, I(0.96)) ** 1.2
    place(fx, stereo(norm(rw, -28)), th(E.E_REW))
    place(fx, stereo(A2.impact(-24, (60, 34), 0.25, 0.2, 982)), E.DUR - 0.01)
    fx = np.tanh(fx * 1.2) / 1.2
    full = mus + fx
    lead, mix = full[:PRE].copy(), full[PRE:].copy()
    th2 = np.linspace(0, np.pi / 2, PRE)[:, None]
    mix[-PRE:] = mix[-PRE:] * np.cos(th2) + lead * np.sin(th2)
    raw = f"{AD}/mix_raw.wav"; wf.write(raw, SR, mix.astype(np.float32))
    Iraw, _ = measure(raw); gain = -12.7 - Iraw
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
    def lv(a, b):
        x = m[I(a):I(min(b, E.DUR))]; return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9) if len(x) else float("nan")
    print("rms: breakdown", round(lv(0.2, 7.5), 1), "drop", round(lv(7.8, 17.5), 1), "stutter", round(lv(17.8, 21.0), 1), "run", round(lv(21.2, 23.9), 1), "rewind", round(lv(24.05, 24.9), 1))
    k0 = I(th(E.E_REW + 1)); dd = np.abs(np.diff(mm[k0 - 2400:k0 + 2400]))
    print(f"rewind join step {dd[2395:2405].max():.4f} vs local median {np.median(dd):.4f}")

if __name__ == "__main__":
    main()
