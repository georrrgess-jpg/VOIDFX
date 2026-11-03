"""Soundtrack for HIM ALL ALONG (voidfx v7): Gunna "Him All Along" h528->h640 + Dexter (S1) lip-synced lines + forensic sound design.

Gunna's vocals step aside (instrumental stem) while Dexter says "A jar of blood. Dramatic. Cryptic. Playful. Could it
be him?", then return on "stay strong ... HIM ALL ALONG" into the drop. Every transition has its own sound; the edit
ends with a fast tape-stop into the pupil dive and loops into the magnifier opening. Built circularly, mastered on a
wrapped copy, AAC-checked. (Engine: v6 audio builder.)
"""
import os, sys, math, subprocess
import numpy as np, scipy.io.wavfile as wf, scipy.signal as ss
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/home/user/VOIDFX/v2/work")
import edl7 as E
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

# ------------------------------------------------------------------ music: tape spin-up ... tape rewind
def music_track(song):
    """the song window; Gunna's vocal swapped for the instrumental stem under Dexter's lines; tape-stop into the pupil dive."""
    t = (np.arange(N + PRE) - PRE) / SR
    Ts, Te = E.DUR - 22 / E.FPS, E.DUR - 4 / E.FPS
    r = np.ones_like(t); m = (t >= Ts) & (t < Te); r[m] = (1 - (t[m] - Ts) / (Te - Ts)) ** 1.6; r[t >= Te] = 0
    p = np.cumsum(r) / SR; k1 = I(1.0) + PRE; p += (E.SONG_IN + 1.0) - p[k1]
    x = p * SR; i = np.clip(np.floor(x).astype(np.int64), 0, len(song) - 2); fr = (x - i)[:, None].astype(np.float32)
    out = song[i] * (1 - fr) + song[i + 1] * fr
    if not (getattr(E, "SONG_VOX", None) and getattr(E, "VOX_MUTE", None)): out_ = out
    else: out_ = None
    if out_ is not None:                                               # no vocal swap in this edit
        amp = np.ones_like(t); amp[t >= Te] = 0; m = (t >= Ts) & (t < Te); amp[m] = 0.35 + 0.65 * r[m]
        lp = bq(out, "low", 1800, 2); ww = np.clip((t - Ts) / (Te - Ts), 0, 1)[:, None]; out = out * (1 - ww) + lp * ww
        return (out * np.convolve(amp, np.ones(240) / 240, "same")[:, None]).astype(np.float32)
    # instrumental stem for the vocal-swap window
    sr_, nv = wf.read(f"{E.SONG_VOX}/no_vocals.wav"); nv = nv.astype(np.float32)
    if np.abs(nv).max() > 2: nv /= 32768
    nv = ss.resample_poly(nv, 160, 147, axis=0).astype(np.float32)
    xs = (p - E.SONG_VOX_T0) * SR; i2 = np.clip(np.floor(xs).astype(np.int64), 0, len(nv) - 2)
    inst = nv[i2] * (1 - fr) + nv[i2 + 1] * fr
    a0, a1 = E.VOX_MUTE; xf = 0.06
    w = np.clip(np.minimum((t - a0) / xf + 0.5, (a1 - t) / xf + 0.5), 0, 1)
    w = (np.sin(w * np.pi / 2) ** 2)[:, None]                                        # equal-power-ish swap
    out = out * (1 - w) + inst * w * 1.05
    amp = np.ones_like(t); amp[t >= Te] = 0
    m = (t >= Ts) & (t < Te); amp[m] = 0.35 + 0.65 * r[m]
    lp = bq(out, "low", 1800, 2); ww = np.clip((t - Ts) / (Te - Ts), 0, 1)[:, None]
    out = out * (1 - ww) + lp * ww
    amp = np.convolve(amp, np.ones(240) / 240, "same").astype(np.float32)
    return (out * amp[:, None]).astype(np.float32)

# ------------------------------------------------------------------ dialogue
def vo_track():
    if not getattr(E, "VO", None):                                   # music-only edit
        return np.zeros((N + PRE, 2), np.float32), np.zeros(N + PRE, np.float32)
    sr, v = wf.read(E.VO_STEM); v = v.astype(np.float32)
    if np.abs(v).max() > 2: v /= 32768
    v = ss.resample_poly(v, 160, 147, axis=0).astype(np.float32)
    v = bq(v, "high", 85, 2); v = bq(v, "low", 11000, 2)
    vo = np.zeros((N + PRE, 2), np.float32); duck = np.zeros(N + PRE, np.float32)
    for k, (a, b, at) in enumerate(E.VO):
        o_ = getattr(E, "VO_STEM_T0", 0.0); seg = v[I(a - o_):I(b - o_)].mean(1)
        # levelling: slow RMS envelope -> gentle upward/downward correction (about 2:1 around the target)
        env = np.sqrt(np.convolve(seg ** 2, np.ones(I(0.08)) / I(0.08), "same")) + 1e-4
        g = np.clip((db(-20) / env) ** 0.5, db(-6), db(9)); g = np.convolve(g, np.ones(I(0.05)) / I(0.05), "same")
        seg = seg * g
        nf = I(0.035); seg[:nf] *= np.sin(np.linspace(0, np.pi / 2, nf)) ** 2; seg[-nf:] *= np.cos(np.linspace(0, np.pi / 2, nf)) ** 2
        env2 = np.sqrt(np.convolve(seg ** 2, np.ones(I(0.05)) / I(0.05), "same")); act = env2 > env2.max() * db(-24)
        seg = seg / (np.sqrt((seg[act] ** 2).mean()) + 1e-9) * db(-16.5)              # speech RMS target
        pk = np.abs(seg).max(); seg = np.tanh(seg / max(pk, 1e-9) * 1.4) / np.tanh(1.4) * pk if pk > db(-2) else seg
        place(vo, stereo(seg), at)
        d0, d1 = I(at) + PRE, I(at + (b - a)) + PRE
        duck[d0:d1] = 0.7 if k < 5 else 1.25
    wet = A2.conv(vo, A2.ir(0.35, seed=31)) * db(-22)            # a touch of room on the dialogue
    vo = vo + wet
    # smooth duck envelope (120 ms attack / 300 ms release)
    sm = np.convolve(duck, np.hanning(I(0.25)) / np.hanning(I(0.25)).sum(), "same")
    return vo, sm

def main():
    os.makedirs(AD, exist_ok=True)
    if not os.path.exists(f"{AD}/song48.wav"):                       # decode the song once (E.SONG)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", E.SONG, "-ar", "48000", "-ac", "2", "-c:a", "pcm_f32le", f"{AD}/song48.wav"], check=True)
    sr, song = wf.read(f"{AD}/song48.wav"); song = song.astype(np.float32)
    mus = music_track(song) * db(-1.5)
    for s_ in E.SHOTS:                                                 # M99: the world goes muffled while he's under
        if s_.get("tin") == "m99":
            a0, a1 = s_["t0"] - 15 / E.FPS, s_["t0"] + 12 / E.FPS
            tt = (np.arange(N + PRE) - PRE) / SR
            w = np.clip(np.minimum((tt - a0) / 0.12, (a1 - tt) / 0.15), 0, 1)[:, None]
            mus = mus * (1 - w) + bq(mus, "low", 700, 2) * w * 1.1
    vo, duck = vo_track()
    mus = mus * db(-6.5 * np.clip(duck, 0, 1.3))[:, None]
    fx = np.zeros((N + PRE, 2), np.float32)
    # dark room-tone drone (continues across the wrap) + a low heartbeat bed in act 1
    n = N + PRE; tt = np.arange(n) / SR
    drone = bq(noise(n, 90), "low", 220, 2) + 0.15 * np.sin(2 * np.pi * 41 * tt)
    fx += stereo(norm(drone, -40))
    for h in range(E.H0 + 8, E.HDROP - 8, 8): place(fx, stereo(heartbeat(-27)), E.th(h))
    # ---- every transition gets its own sound
    for s_ in E.SHOTS:
        tin, t0 = s_.get("tin"), s_["t0"]
        if tin == "lens_open":                                        # glass ring-in from black
            place(fx, stereo(glass_chime(-25)), t0 + 0.01); place(fx, A2.whoosh(0.30, -24, 60, True), t0)
        elif tin == "microscope":                                     # zoom servo + focus clicks + wet squelch
            n_ = I(0.40); q = np.arange(n_) / SR
            servo = np.sin(2 * np.pi * np.cumsum(300 + 900 * q / 0.4) / SR) * 0.3 + bq(noise(n_, 61), "band", np.array([800, 3000]), 2) * 0.5
            place(fx, stereo(norm(servo * np.sin(np.pi * q / 0.4), -27)), t0 - 0.30)
            place(fx, stereo(shutter_ticks(-26, 3, 0.05, 62)), t0 - 0.05)
            place(fx, A2.whoosh(0.28, -24, 63, False), t0 + 0.05)
        elif tin == "slidebox_close":                                 # rosewood lid: creak, slam on "close", latch, reopen, glass, dive
            tc = E.CLOSE_T
            n_ = I(0.20); q = np.arange(n_) / SR
            creak = np.sin(2 * np.pi * np.cumsum(180 + 70 * np.sin(2 * np.pi * 9 * q)) / SR) * np.sin(np.pi * q / 0.2)
            place(fx, stereo(norm(bq(creak, "band", np.array([120, 1800]), 2), -28)), tc - 0.20)
            place(fx, A2.whoosh(0.20, -24, 64, False), tc - 0.19)
            place(fx, stereo(A2.impact(-10, (58, 30), 0.45, 0.35, 65)), tc)                       # heavy wood slam
            n_ = I(0.12); q = np.arange(n_) / SR
            wood = bq(noise(n_, 66), "band", np.array([150, 1200]), 2) * np.exp(-q / 0.03)
            place(fx, stereo(norm(wood, -16)), tc)
            for k_ in range(6): place(fx, stereo(glass_chime(-33 - k_), -0.6 + 0.24 * k_), tc + 0.02 + 0.03 * k_)   # slides rattle inside
            place(fx, stereo(shutter_ticks(-25, 2, 0.05, 67)), tc + 0.30)                            # latch
            place(fx, stereo(norm(bq(creak[::-1].copy(), "band", np.array([150, 2200]), 2), -29)), t0 - 0.02)
            place(fx, stereo(glass_chime(-26), 0.3), t0 + 0.06); place(fx, A2.whoosh(0.30, -21, 68, True), t0 + 0.08)
            place(fx, stereo(bloop(-24, 69)), t0 + 0.24)                                            # into the drop
        elif tin == "uv_sweep":                                       # UV lamp hum + fluorescent buzz
            place(fx, stereo(neon_buzz(0.45, -27, (0, 1, 1, 0, 1, 1, 1, 1))), t0 - 8 / E.FPS)
            place(fx, A2.whoosh(0.34, -25, 71, True), t0 - 0.12)
        elif tin == "tape_snap":                                      # tape stretch -> snap
            n_ = I(0.14); q = np.arange(n_) / SR
            str_ = np.sin(2 * np.pi * np.cumsum(600 + 2400 * q / 0.14) / SR) * (q / 0.14) * 0.4 + bq(noise(n_, 74), "band", np.array([1000, 4000]), 2) * 0.5
            place(fx, stereo(norm(str_, -27)), t0 - 0.14)
            place(fx, stereo(A2.impact(-19, (110, 60), 0.10, 0.9, 75)), t0); place(fx, A2.whoosh(0.25, -24, 76, False), t0 + 0.02)
        elif tin == "blood_lens":                                     # a drop falls, splats on the lens, runs
            place(fx, stereo(drip(-15, 77)), t0 - 0.13)
            n_ = I(0.35); q = np.arange(n_) / SR
            sq = bq(noise(n_, 78), "band", np.array([300, 2500]), 2) * np.exp(-q / 0.09) * (1 + 0.5 * np.sin(2 * np.pi * 23 * q))
            place(fx, stereo(norm(sq, -22)), t0 + 0.02); place(fx, A2.whoosh(0.4, -27, 79, False), t0 + 0.12)
        elif tin == "burst":                                          # HERO: plastic stretches, bursts, blood spray, sub drop
            n_ = I(0.40); q = np.arange(n_) / SR
            stretch = bq(noise(n_, 80), "band", np.array([400, 2500]), 2) * (q / 0.4) ** 1.5 * (1 + 0.6 * np.sin(2 * np.pi * (8 + 30 * q) * q))
            place(fx, stereo(norm(stretch, -22)), t0 - 0.40)
            place(fx, A2.riser(0.8, -20), t0 - 0.8)
            n_ = I(0.55); q = np.arange(n_) / SR
            rip = bq(noise(n_, 81), "band", np.array([700, 9000]), 2) * (0.5 + 0.5 * (np.random.default_rng(82).random(n_) > 0.55)) * np.exp(-q / 0.16)
            place(fx, np.stack([norm(rip, -13), np.roll(norm(rip, -13), 50)], 1), t0)
            place(fx, stereo(A2.impact(-9, (52, 26), 0.8, 0.6, 83)), t0)
            n_ = I(0.6); q = np.arange(n_) / SR
            splash = bq(noise(n_, 84), "band", np.array([250, 3500]), 2) * np.exp(-q / 0.12)
            place(fx, np.stack([norm(splash, -19), np.roll(norm(splash, -19), 90)], 1), t0 + 0.03)
            place(fx, A2.whoosh(0.45, -18, 85, True), t0 + 0.01)
        elif tin == "slash":
            place(fx, stereo(swish(-16, 0.11, 86), 0.5), t0 - 5 / E.FPS); place(fx, stereo(metal_shing(-21)), t0 - 0.03)
            place(fx, stereo(A2.impact(-18, (75, 38), 0.3, 0.6, 87)), t0)
        elif tin == "board":                                          # pins + string pull
            place(fx, stereo(A2.tick(-25, 88), -0.4), t0 - 0.12); place(fx, stereo(A2.tick(-25, 89), 0.4), t0 + 0.05)
            place(fx, A2.whoosh(0.30, -22, 90, True), t0 - 0.15)
        elif tin == "zipper":                                         # body-bag zip shut, then unzip
            for k0, dur in ((t0 - 10 / E.FPS, 10 / E.FPS), (t0 + 0.0, 12 / E.FPS)):
                n_ = I(dur); q = np.arange(n_) / SR; rate = 90 + 160 * q / dur
                teeth = (np.sin(2 * np.pi * np.cumsum(rate) / SR) > 0.85).astype(np.float32)
                z = bq(noise(n_, int(k0 * 100)), "band", np.array([1500, 7000]), 2) * (0.3 + teeth) * np.sin(np.pi * q / dur) ** 0.5
                place(fx, stereo(norm(z, -22), 0.2), k0)
            place(fx, stereo(A2.impact(-24, (70, 40), 0.15, 0.3, 91)), t0 - 0.01)
        elif tin == "lightstreak":                                    # passing cars
            place(fx, A2.whoosh(0.45, -19, 92, True), t0 - 0.12); place(fx, A2.whoosh(0.35, -24, 93, False), t0 + 0.1)
        elif tin == "logo_orig":                                      # logo slam + fly through the 'o'
            place(fx, stereo(A2.impact(-19, (110, 60), 0.12, 0.7, 94)), t0 - 0.20)
            place(fx, np.stack([A2.shimmer(0.9, -27)] * 2, 1), t0 - 0.15); place(fx, A2.whoosh(0.32, -20, 95, True), t0 - 0.10)
        elif tin == "polaroid":
            place(fx, stereo(flash_pop(-18, 96)), t0 - 0.16); place(fx, stereo(shutter_ticks(-21, 2, 0.04, 97)), t0 - 0.01)
            place(fx, A2.whoosh(0.3, -23, 98, True), t0 + 6 / E.FPS)
        elif tin == "m99":                                            # sedative: heartbeat slows, low thump, breath in on waking
            place(fx, stereo(heartbeat(-15)), t0 - 0.24); place(fx, stereo(heartbeat(-19)), t0 + 0.02)
            place(fx, stereo(A2.impact(-17, (45, 25), 0.5, 0.0, 99)), t0 - 0.02)
            n_ = I(0.45); q = np.arange(n_) / SR
            br = bq(noise(n_, 100), "band", np.array([500, 3000]), 2) * np.sin(np.pi * q / 0.45) ** 2
            place(fx, stereo(norm(br, -27)), t0 + 0.06)
        elif tin == "strobe":                                         # flash bulbs on the beat
            for k_ in (-5, -2, 1, 4): place(fx, stereo(A2.impact(-22, (120, 70), 0.06, 0.9, 101 + k_)), t0 + k_ / E.FPS)
        elif tin == "scan":
            n_ = I(0.28); q = np.arange(n_) / SR
            sw_ = np.sin(2 * np.pi * np.cumsum(2400 - 1500 * q / 0.28) / SR) * np.sin(np.pi * q / 0.28) * 0.5 + bq(noise(n_, 106), "band", np.array([3000, 9000]), 2) * 0.3
            place(fx, stereo(norm(sw_, -26)), t0 - 6 / E.FPS)
        elif tin == "mag_sweep":                                      # the glass sweeps in
            place(fx, A2.whoosh(0.30, -21, 107, False), t0 - 0.20); place(fx, stereo(glass_chime(-25), -0.3), t0 + 0.02)
    # ---- graphics sounds: evidence markers clack down, plastic sheet rustles in, luminol hiss, blood hits splat, stamp thunk
    for s_ in E.SHOTS:
        if s_.get("markers"):
            for k_, tm in enumerate((s_["f0"] / E.FPS + 4 / E.FPS, s_["t0"] + 2 * E.HB, s_["t0"] + 4 * E.HB)):
                place(fx, stereo(A2.tick(-22, 120 + k_), -0.5 + 0.5 * k_), tm + 7 / E.FPS); place(fx, stereo(A2.impact(-29, (160, 90), 0.04, 0.6, 123 + k_)), tm + 7 / E.FPS)
        if s_.get("plastic"):
            n_ = I(0.5); q = np.arange(n_) / SR
            rus = bq(noise(n_, 126), "band", np.array([800, 6000]), 2) * (np.random.default_rng(127).random(n_) > 0.7) * np.sin(np.pi * q / 0.5)
            place(fx, stereo(norm(rus, -27), 0.2), s_["t0"] + 0.38)
    for tx in getattr(E, "TEXT", []):
        if tx["style"] == "luminol":
            for k_, (w, wt, ln) in enumerate(tx["words"]):
                n_ = I(0.18); q = np.arange(n_) / SR
                hiss = bq(noise(n_, 130 + k_), "high", 4000, 2) * np.sin(np.pi * q / 0.18)
                place(fx, stereo(norm(hiss, -29), -0.3 + 0.3 * k_), wt - 0.06)
        if tx["style"] == "casestamp":
            ts = tx["words"][0][1] + 6 / E.FPS
            place(fx, A2.whoosh(0.12, -26, 131, False), ts - 0.12)
            place(fx, stereo(A2.impact(-13, (95, 50), 0.12, 0.2, 132)), ts)
            n_ = I(0.08); q = np.arange(n_) / SR; place(fx, stereo(norm(bq(noise(n_, 133), "band", np.array([200, 1500]), 2) * np.exp(-q / 0.02), -17)), ts)
    for h in range(E.MONTAGE[0], E.MONTAGE[1], 4):                    # blood hits on the montage beats
        if h == E.MONTAGE[0]: continue
        n_ = I(0.14); q = np.arange(n_) / SR
        sp = bq(noise(n_, 140 + h), "band", np.array([400, 3000]), 2) * np.exp(-q / 0.035)
        place(fx, stereo(norm(sp, -31), 0.6 if (h // 4) % 2 else -0.6), E.th(h))
    # ---- typewriter keys on the case-note words, stamp hits on the single words, luminol shimmer, confession hit
    for tx in getattr(E, "TEXT", []):
        for k_, (w, wt, ln) in enumerate(tx["words"]):
            if tx["style"] == "case" or (tx["style"] == "doors" and k_ == 0): place(fx, stereo(A2.tick(-30, 110 + k_), -0.3 + 0.12 * k_), wt)
            elif tx["style"] == "luminol": place(fx, stereo(A2.shimmer(0.7, -29)), wt)
    # ---- ending: tape-stop into the pupil dive (heartbeat + suck-in), black -> loop into the magnifier
    place(fx, stereo(heartbeat(-17)), E.DUR - 0.62); place(fx, stereo(heartbeat(-19)), E.DUR - 0.30)
    place(fx, stereo(rev(A2.impact(-17, (60, 30), 0.3, 0.2, 130))[-I(0.35):]), E.DUR - 0.36)
    fx = np.tanh(fx * 1.3) / 1.3
    full = mus + vo + fx
    lead, mix = full[:PRE].copy(), full[PRE:].copy()
    th_ = np.linspace(0, np.pi / 2, PRE)[:, None]                    # circular join (drone -> drone)
    mix[-PRE:] = mix[-PRE:] * np.cos(th_) + lead * np.sin(th_)
    raw = f"{AD}/mix_raw.wav"; wf.write(raw, SR, mix.astype(np.float32))
    Iraw, _ = measure(raw); gain = -13.0 - Iraw
    P2 = SR; wrapped = np.vstack([mix[-P2:], mix, mix[:P2]])
    wf.write(f"{AD}/mix_raw_wrapped.wav", SR, wrapped.astype(np.float32))
    tmp = f"{AD}/mix_wrapped_master.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{AD}/mix_raw_wrapped.wav", "-af", f"volume={gain:.2f}dB,aresample=192000,"
                    f"alimiter=limit={db(-4.0):.4f}:attack=3:release=60:level=disabled,aresample=48000:resampler=soxr", "-c:a", "pcm_f32le", tmp], check=True)
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
    # levels per section for a sanity check
    def lv(a, b):
        x = m[I(min(a, E.DUR - 0.05)):I(min(b, E.DUR))]; return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9) if len(x) else float("nan")
    print("rms: act1", round(lv(0.3, 3.6), 1), "dexter", round(lv(3.8, 6.4), 1), "hook", round(lv(8.6, 11.0), 1), "drop", round(lv(11.1, 22.0), 1),
          "confess", round(lv(23.6, 25.2), 1), "tail", round(lv(25.6, 25.84), 1))

if __name__ == "__main__":
    main()
