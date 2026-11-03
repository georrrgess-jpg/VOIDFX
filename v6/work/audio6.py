"""Soundtrack for WARMPOP (voidfx v6): George Clanton "Warmpop" h416->h496 + Dexter's voice-over + VHS sound design.

Circular build: the tape starts (VCR clunk, motor spin-up, the song winds up to speed from static), Dexter's S5
voice-over (Demucs-isolated, cleaned, levelled, equal-power fades) rides the filtered build, the song's full mix
returns at the drop through the CRT, every transition has its own sound, "It... was me." is lip-synced, then the
tape rewinds (the song scrubs backwards), drops into static, and the static runs straight across the loop seam into
the next tape start. A tape-hiss bed runs through everything, including the wrap. Mastered on a wrapped copy.
"""
import os, sys, math, subprocess
import numpy as np, scipy.io.wavfile as wf, scipy.signal as ss
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/home/user/VOIDFX/v2/work")
import edl6 as E
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
    t = (np.arange(N + PRE) - PRE) / SR
    Ta, Tb = 0.12, 0.46                                            # spin-up (picture: static ends at frame 8)
    Ts = E.DUR - 40 / E.FPS; Tbrk = Ts + 0.06; Te = E.DUR - 8 / E.FPS   # rewind starts with the picture's REW
    r = np.ones_like(t)
    r[t < Ta] = 0
    m = (t >= Ta) & (t < Tb); r[m] = ((t[m] - Ta) / (Tb - Ta)) ** 1.4
    m = (t >= Ts) & (t < Tbrk); r[m] = 1 - (t[m] - Ts) / (Tbrk - Ts)
    m = (t >= Tbrk) & (t < Te); r[m] = -7.0 * ((t[m] - Tbrk) / (Te - Tbrk)) ** 1.3
    r[t >= Te] = 0
    p = np.cumsum(r) / SR; k1 = I(1.0) + PRE; p += (E.SONG_IN + 1.0) - p[k1]
    amp = np.ones_like(t)
    m = t < Tb; amp[m] = np.clip(np.abs(r[m]), 0, 1) ** 0.6
    m = (t >= Tbrk) & (t < Te); amp[m] = 0.55
    amp[t >= Te] = 0
    amp = np.convolve(amp, np.ones(240) / 240, "same").astype(np.float32)
    x = p * SR; i = np.clip(np.floor(x).astype(np.int64), 0, len(song) - 2); fr = (x - i)[:, None].astype(np.float32)
    song_lp = bq(song, "low", 2600, 4)
    out = song[i] * (1 - fr) + song[i + 1] * fr
    rw = (t >= Ts) & (t < Te + 0.01)
    rev = song_lp[i] * (1 - fr) + song_lp[i + 1] * fr
    out[rw] = bq(rev, "band", np.array([500, 7000]), 2)[rw] * 1.4
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
        seg = v[I(a):I(b)].mean(1)
        # levelling: slow RMS envelope -> gentle upward/downward correction (about 2:1 around the target)
        env = np.sqrt(np.convolve(seg ** 2, np.ones(I(0.08)) / I(0.08), "same")) + 1e-4
        g = np.clip((db(-20) / env) ** 0.5, db(-6), db(9)); g = np.convolve(g, np.ones(I(0.05)) / I(0.05), "same")
        seg = seg * g
        nf = I(0.035); seg[:nf] *= np.sin(np.linspace(0, np.pi / 2, nf)) ** 2; seg[-nf:] *= np.cos(np.linspace(0, np.pi / 2, nf)) ** 2
        env2 = np.sqrt(np.convolve(seg ** 2, np.ones(I(0.05)) / I(0.05), "same")); act = env2 > env2.max() * db(-24)
        seg = seg / (np.sqrt((seg[act] ** 2).mean()) + 1e-9) * db(-17.5 if k < 2 else -16.0)   # speech RMS target
        pk = np.abs(seg).max(); seg = np.tanh(seg / max(pk, 1e-9) * 1.4) / np.tanh(1.4) * pk if pk > db(-2) else seg
        place(vo, stereo(seg), at)
        d0, d1 = I(at) + PRE, I(at + (b - a)) + PRE
        duck[d0:d1] = 1.0 if k < 2 else 1.25
    wet = A2.conv(vo, A2.ir(0.45, seed=31)) * db(-17)            # small dreamy plate on the voice-over
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
    vo, duck = vo_track()
    mus = mus * db(-6.5 * np.clip(duck, 0, 1.3))[:, None]
    fx = np.zeros((N + PRE, 2), np.float32)
    # tape-hiss bed through everything (continues across the wrap), a little hum before the drop
    hiss = bq(noise(N + PRE, 90), "band", np.array([2500, 11000]), 2)
    hiss = np.stack([hiss, bq(noise(N + PRE, 91), "band", np.array([2500, 11000]), 2)], 1)
    fx += hiss / np.abs(hiss).max() * db(-44)
    n = I(E.th(E.HDROP)); tt = np.arange(n) / SR
    hum = (np.sin(2 * np.pi * 60 * tt) + 0.3 * np.sin(2 * np.pi * 180 * tt)) * np.minimum(1, (E.th(E.HDROP) - tt) / 0.3)
    place(fx, stereo(norm(hum, -42)), 0.0)
    # ---- loop seam + tape start: static (end -> start), clunk, motor spin-up
    t_static = E.DUR - 8 / E.FPS
    st_end = static_hiss(E.DUR - t_static + 0.01, -21, 1); nf = I(0.008)
    st_end[:nf] *= np.sin(np.linspace(0, np.pi / 2, nf))[:, None] ** 2
    place(fx, st_end, t_static)
    d0 = PRE / SR; st0 = static_hiss(d0 + 0.36, -21, 2); tt = np.arange(len(st0)) / SR - d0
    st0 *= np.where(tt < 0.18, 1.0, np.cos(np.clip((tt - 0.18) / 0.18, 0, 1) * np.pi / 2) ** 2)[:, None]   # tails off as the picture rolls in
    place(fx, st0, -d0)
    place(fx, stereo(vcr_clunk(-17)), 0.07)
    place(fx, stereo(motor(0.45, -29), 0.2), 0.10)
    # ---- every transition gets its own sound
    for s in E.SHOTS:
        tin, t0 = s.get("tin"), s["t0"]
        if tin == "vhs_roll":
            place(fx, stereo(scrub(0.22, -24, 20, 3500), -0.3), t0 - 5 / E.FPS)
            place(fx, A2.whoosh(0.30, -24, 21, False), t0 - 0.12)
        elif tin == "kaleido":
            place(fx, A2.whoosh(0.36, -20, 22 + int(t0), True), t0 - 0.16)
            place(fx, stereo(A2.shimmer(0.7, -30)), t0 - 0.05)
        elif tin == "rewind":
            place(fx, stereo(scrub(8 / E.FPS + 0.02, -20, 23 + int(t0)), 0.3), t0 - 8 / E.FPS)
            place(fx, stereo(vcr_clunk(-24, 24)), t0)
        elif tin == "flash":
            place(fx, stereo(flash_pop(-19, 25 + int(t0))), t0 - 0.16)
        elif tin == "tear":
            place(fx, stereo(A2.glitch_burst(0.16, -20, 26)), t0 - 0.02)
        elif tin == "crt":
            k0 = t0 - 54 / E.FPS
            place(fx, A2.whoosh(0.32, -23, 27, False), k0 - 0.02)                    # frame shrinks into the TV
            n = I(t0 - k0); tt = np.arange(n) / SR                                    # CRT hum + flyback whine
            crt = np.sin(2 * np.pi * 60 * tt) * 0.6 + 0.25 * np.sin(2 * np.pi * 120 * tt) + 0.05 * np.sin(2 * np.pi * 7800 * tt)
            crt = crt * np.minimum(1, tt / 0.1) * np.minimum(1, (t0 - k0 - tt) / 0.05)
            place(fx, stereo(norm(crt, -30)), k0)
            place(fx, A2.riser(t0 - k0 - 0.05, -20), k0)
            place(fx, A2.whoosh(0.22, -19, 28, True), t0 - 0.20)                      # dive into the screen
            place(fx, stereo(A2.impact(-13, (66, 34), 0.55, 0.3, 29)), t0)            # drop
            place(fx, stereo(degauss(-21)), t0 + 0.01)
            place(fx, stereo(A2.shimmer(1.2, -29)), t0 + 0.03)
        elif tin == "tiles":
            for d in range(13):
                place(fx, stereo(A2.tick(-31, d + int(t0)), -0.8 + 1.6 * d / 12), t0 + (d * 0.9 + 3) / E.FPS)
            place(fx, A2.whoosh(0.25, -27, 30, True), t0 - 0.02)
        elif tin == "neon_trace":
            place(fx, stereo(neon_buzz(0.38, -26)), t0)
            place(fx, stereo(A2.glitch_burst(0.08, -27, 31)), t0 + 0.02)
        elif tin == "ink":
            place(fx, stereo(drip(-16, 32)), t0 - 0.13)
            place(fx, A2.whoosh(0.35, -27, 33, False), t0 + 0.05)
        elif tin == "ripple":
            place(fx, stereo(bloop(-19, 34)), t0 - 4 / E.FPS)
            place(fx, A2.whoosh(0.28, -26, 35, True), t0 - 0.10)
        elif tin == "logo":                                            # neon sign buzzes on, fly through the 'o'
            place(fx, stereo(neon_buzz(12 / E.FPS + 0.1, -24, (0, 1, 0, 0, 1, 0, 1))), t0 - 12 / E.FPS)
            place(fx, A2.whoosh(0.36, -19, 42, True), t0 - 0.22)
            place(fx, stereo(A2.impact(-17, (74, 38), 0.35, 0.4, 43)), t0 + 0.02)
            place(fx, stereo(A2.shimmer(1.0, -28)), t0 + 0.05)
        elif tin == "eye_dive":                                        # dive into the pupil, heartbeat, aperture blades
            place(fx, A2.whoosh(0.34, -19, 60, False), t0 - 0.30)
            place(fx, stereo(rev(A2.impact(-22, (60, 30), 0.25, 0.1, 61))[-I(0.3):]), t0 - 0.30)
            place(fx, stereo(heartbeat(-15)), t0 - 0.04)
            place(fx, stereo(shutter_ticks(-23, 5, 0.025, 62), 0.3), t0 + 0.02)
            place(fx, stereo(A2.shimmer(0.8, -30)), t0 + 0.05)
        elif tin == "assemble":                                        # the dissolve, played backwards
            cr = crumble(0.42, -22, 63); place(fx, np.stack([cr[::-1, 1], cr[::-1, 0]], 1), t0)
            place(fx, stereo(A2.impact(-24, (90, 50), 0.15, 0.4, 64)), t0 + 24 / E.FPS)
            place(fx, stereo(A2.shimmer(0.6, -31)), t0 + 20 / E.FPS)
        elif tin == "polaroid":                                        # flash charge, shutter, print eject, toss
            place(fx, stereo(flash_pop(-18, 65)), t0 - 0.16)
            place(fx, stereo(shutter_ticks(-21, 2, 0.04, 66)), t0 - 0.01)
            n = I(0.22); tt = np.arange(n) / SR
            ej = np.sign(np.sin(2 * np.pi * 310 * tt)) * 0.3 + bq(noise(n, 67), "band", np.array([800, 3000]), 2)
            place(fx, stereo(norm(ej * np.sin(np.pi * tt / 0.22), -30), 0.3), t0 + 0.02)
            place(fx, A2.whoosh(0.3, -22, 68, True), t0 + 6 / E.FPS)
        elif tin == "facematch":
            place(fx, A2.whoosh(0.26, -21, 69, True), t0 - 0.20)
            place(fx, stereo(A2.impact(-22, (85, 45), 0.2, 0.5, 70)), t0)
            place(fx, stereo(A2.shimmer(0.5, -32)), t0 + 0.02)
        elif tin == "cube":                                            # the box turns and lands
            place(fx, A2.whoosh(0.32, -19, 71, True), t0 - 0.16)
            place(fx, stereo(A2.impact(-20, (70, 36), 0.3, 0.3, 72)), t0 + 8 / E.FPS)
            place(fx, stereo(A2.tick(-28, 73)), t0 + 8 / E.FPS)
        elif tin == "sun":                                             # the sun rises, the blinds rattle open
            place(fx, A2.riser(0.30, -22), t0 - 0.30)
            place(fx, stereo(chord_swell(-23)), t0 - 0.10)
            for i in range(7): place(fx, stereo(A2.tick(-31, 74 + i), -0.6 + 0.2 * i), t0 + 0.02 + 0.022 * i)
        elif tin == "slash":                                           # knife swish, steel ring, the halves part
            place(fx, stereo(swish(-16, 0.11, 75), 0.5), t0 - 5 / E.FPS)
            place(fx, stereo(metal_shing(-20)), t0 - 0.03)
            place(fx, stereo(A2.impact(-17, (75, 38), 0.3, 0.6, 76)), t0)
            place(fx, stereo(drip(-26, 77)[I(0.13):]), t0 + 0.04)
            place(fx, A2.whoosh(0.3, -24, 78, False), t0 + 0.02)
        elif tin == "burn":                                            # film catches fire
            place(fx, stereo(fire_whoosh(-19, 0.5, 79)), t0 - 10 / E.FPS)
            place(fx, stereo(A2.impact(-23, (60, 32), 0.25, 0.2, 80)), t0)
        elif tin == "lens":                                            # glint in the shades, dive through the glass
            place(fx, stereo(glass_chime(-25), 0.3), t0 - 12 / E.FPS)
            place(fx, A2.whoosh(0.30, -20, 81, True), t0 - 0.22)
            place(fx, stereo(A2.impact(-21, (95, 50), 0.15, 0.7, 82)), t0)
        elif tin == "shadow":                                          # darkness sucks in, light blooms out
            place(fx, stereo(rev(A2.impact(-17, (55, 28), 0.5, 0.2, 83))[-I(0.25):]), t0 - 0.25)
            place(fx, A2.whoosh(0.4, -24, 84, False), t0 - 0.2)
            place(fx, stereo(A2.shimmer(0.9, -28)), t0 + 0.04)
        elif tin == "filmstrip":                                       # projector rattle as the strip whips
            for i in range(9): place(fx, stereo(A2.tick(-29, 90 + i), -0.4 + 0.1 * i), t0 - 0.15 + 0.038 * i)
            place(fx, A2.whoosh(0.30, -21, 91, True), t0 - 0.15)
            place(fx, stereo(A2.impact(-24, (90, 48), 0.15, 0.5, 92)), t0 + 9 / E.FPS)
        elif tin == "peel":                                            # sticker peel: sticky crackle + paper flap
            n = I(0.30); tt = np.arange(n) / SR
            pl = bq(noise(n, 93), "band", np.array([1500, 7000]), 2) * (np.random.default_rng(94).random(n) > 0.93) * 3 + bq(noise(n, 95), "band", np.array([400, 2500]), 2) * 0.4
            place(fx, stereo(norm(pl * np.sin(np.pi * tt / 0.30), -23), 0.4), t0 - 8 / E.FPS)
            place(fx, A2.whoosh(0.26, -24, 96, True), t0 - 0.02)
        elif tin == "tv_off":                                          # finger-gun bang -> CRT power-off -> power-on
            tb = t0 - 14 / E.FPS
            n = I(0.4); tt = np.arange(n) / SR                         # stylised gunshot: snap + body + tail
            shot = bq(noise(n, 97), "high", 1200, 2) * env_exp(n, 0.02, 0.0002) + 0.6 * bq(noise(n, 104), "band", np.array([150, 1500]), 2) * env_exp(n, 0.09, 0.001)
            place(fx, np.stack([norm(shot, -13), np.roll(norm(shot, -13), 31)], 1), tb)
            place(fx, stereo(A2.impact(-15, (85, 40), 0.35, 0.7, 98)), tb)
            n = I(0.17); tt = np.arange(n) / SR
            off = np.sin(2 * np.pi * np.cumsum(9000 * np.exp(-tt / 0.05) + 120) / SR) * np.exp(-tt / 0.09)
            place(fx, stereo(norm(off, -24)), t0 - 10 / E.FPS)
            place(fx, stereo(A2.impact(-22, (60, 30), 0.2, 0.2, 99)), t0 - 2 / E.FPS)
            n = I(0.22); tt = np.arange(n) / SR
            on = np.sin(2 * np.pi * np.cumsum(80 + 900 * (tt / 0.22) ** 2) / SR) * np.sin(np.pi * tt / 0.22) + 0.3 * bq(noise(n, 100), "band", np.array([2000, 8000]), 2) * np.exp(-tt / 0.05)
            place(fx, stereo(norm(on, -25)), t0 + 0.01)
        elif tin == "pixel_sort":
            place(fx, melt_sweep(0.34, -20, 36), t0 - 8 / E.FPS)
            place(fx, stereo(A2.impact(-23, (80, 42), 0.22, 0.3, 37)), t0)
    # ---- VHS pause on the kill grin: clunk in, hum while held, clunk out
    for s_ in E.SHOTS:
        if s_.get("pause"):
            tp = s_["pause"] / E.FPS; tq = tp + 14 / E.FPS
            place(fx, stereo(vcr_clunk(-21, 101)), tp - 0.01); place(fx, stereo(vcr_clunk(-23, 102)), tq - 0.01)
            n = I(tq - tp); tt = np.arange(n) / SR
            hm = (np.sin(2 * np.pi * 60 * tt) + 0.4 * bq(noise(n, 103), "band", np.array([3000, 9000]), 2)) * np.minimum(1, np.minimum(tt, tq - tp - tt) / 0.02)
            place(fx, stereo(norm(hm, -32)), tp)
    # ---- vapor world -> reality tunes in behind Dexter after the drop (signal-lock chirps)
    td = E.th(E.HDROP)
    for i, (dt, fq) in enumerate(((14, 1800), (22, 2600), (30, 3400), (40, 5200))):
        n = I(0.05); tt = np.arange(n) / SR
        place(fx, stereo(norm(np.sin(2 * np.pi * fq * tt) * env_exp(n, 0.015, 0.001), -33), -0.4 + 0.25 * i), td + dt / E.FPS)
    # ---- vanish ("disappear myself"): crumble that follows the dissolve
    vs = [s_ for s_ in E.SHOTS if s_.get("vanish")]
    if vs:
        tv0 = E.VANISH_T0; tv1 = vs[0]["t1"] - 0.08
        place(fx, crumble(tv1 - tv0 + 0.25, -21, 38), tv0)
        place(fx, A2.riser(0.5, -30), tv0 - 0.5)
    # ---- captions: a soft tick as each word eases in; MIAMI sweep; neon words; glints on the montage downbeats
    for vi, words, s_end, emph, style in E.CAPS:
        a, b_, at = E.VO[vi]
        for j, (w, ws, ln) in enumerate(words): place(fx, stereo(soft_tick(-38, j), -0.3 + 0.12 * j), at + (ws - a))
        if style == "vanish":
            place(fx, crumble(0.5, -30, 39), at + (s_end - a) + 0.25 - 0.2)
    place(fx, stereo(A2.shimmer(0.9, -29)), E.th(E.HDROP) + 12 / E.FPS)
    for word, tw in E.END_CAP:
        place(fx, stereo(neon_buzz(0.32, -29 if word != "ME." else -26, (1, 0, 1, 0, 1, 1, 0, 1, 1, 1))), tw)
    for h in range(E.MONTAGE[0], E.MONTAGE[1], 8):
        if h != E.MONTAGE[0]: place(fx, stereo(ting(-35, h), 0.5 if h % 16 else -0.5), E.th(h))
    # ---- ending: the tape rewinds (the song scrubs backwards) -> static -> loop
    Ts = E.DUR - 40 / E.FPS
    place(fx, stereo(vcr_clunk(-22, 40)), Ts - 0.02)
    place(fx, stereo(scrub(32 / E.FPS, -22, 41, 6000), 0.0), Ts + 0.03)
    fx = np.tanh(fx * 1.3) / 1.3
    full = mus + vo + fx
    lead, mix = full[:PRE].copy(), full[PRE:].copy()
    th_ = np.linspace(0, np.pi / 2, PRE)[:, None]                    # circular join (static -> static, hiss -> hiss)
    mix[-PRE:] = mix[-PRE:] * np.cos(th_) + lead * np.sin(th_)
    raw = f"{AD}/mix_raw.wav"; wf.write(raw, SR, mix.astype(np.float32))
    Iraw, _ = measure(raw); gain = -13.0 - Iraw
    P2 = SR; wrapped = np.vstack([mix[-P2:], mix, mix[:P2]])
    wf.write(f"{AD}/mix_raw_wrapped.wav", SR, wrapped.astype(np.float32))
    tmp = f"{AD}/mix_wrapped_master.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{AD}/mix_raw_wrapped.wav", "-af", f"volume={gain:.2f}dB,aresample=192000,"
                    f"alimiter=limit={db(-3.0):.4f}:attack=3:release=60:level=disabled,aresample=48000:resampler=soxr", "-c:a", "pcm_f32le", tmp], check=True)
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
    print("rms: intro", round(lv(0.2, 0.9), 1), "VO", round(lv(1.0, 6.5), 1), "build", round(lv(7, 10.5), 1), "drop", round(lv(10.7, 22.5), 1),
          "it-was-me", round(lv(22.8, 25.4), 1), "rewind", round(lv(26.0, 26.5), 1), "static", round(lv(26.55, 26.66), 1))

if __name__ == "__main__":
    main()
