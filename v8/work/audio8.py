"""Soundtrack for WISH YOU WELL (voidfx v8): Brent Faiyaz "Wish You Well" (h64 -> h164 of the user's recording) + the
S1 pilot line "Tonight's the night." + night-drive sound design. Dead stop on the beat after "well"; its reverb tail and
the rain/car ambience carry across the wrap into the opening. Built circularly, mastered on a wrapped copy, AAC-checked.
(Engine: v7 audio builder.)
"""
import os, sys, math, subprocess
import numpy as np, scipy.io.wavfile as wf, scipy.signal as ss
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/home/user/VOIDFX/v2/work")
import edl8 as E
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
    """the song window, played straight; a dead stop on the beat after "well" (8 ms fade), no tape-stop."""
    t = (np.arange(N + PRE) - PRE) / SR
    x = (E.SONG_IN + t) * SR; i = np.clip(np.floor(x).astype(np.int64), 0, len(song) - 2); fr = (x - i)[:, None].astype(np.float32)
    out = song[i] * (1 - fr) + song[i + 1] * fr
    amp = np.clip((E.DUR - t) / 0.008, 0, 1) * np.clip(t / 0.015, 0, 1)                 # 15 ms in at the loop start, dead stop at the end
    return (out * amp[:, None]).astype(np.float32)

def rain_bed(n, seed=200):
    x = bq(noise(n, seed), "band", np.array([1500, 9000]), 2) * 0.6 + bq(noise(n, seed + 1), "low", 500, 2) * 0.4
    rng = np.random.default_rng(seed + 2); taps = np.zeros(n, np.float32)
    for _ in range(int(n / SR * 40)):
        k = int(rng.uniform(0, n - 300)); m = 200; taps[k:k + m] += bq(noise(m, int(rng.integers(1e6))), "high", 2500, 2) * np.exp(-np.arange(m) / 40) * rng.uniform(0.3, 1)
    return x + taps * 0.8

def pass_by(dur=0.9, level=-20, seed=210):
    """a car passing: filtered noise swelling and sweeping in pan + pitch."""
    n = I(dur); q = np.arange(n) / n; x = noise(n, seed); out = np.zeros(n, np.float32); blk = 1024
    for k in range(0, n, blk):
        fc = 500 + 2600 * np.exp(-((q[k] - 0.5) / 0.18) ** 2)
        sos = ss.butter(2, [fc / 1.8 / (SR / 2), min(0.95, fc * 1.8 / (SR / 2))], "band", output="sos")
        seg = x[max(0, k - 2048):k + blk]; y = ss.sosfilt(sos, seg)[-min(blk, n - k):]; out[k:k + len(y)] = y
    env = np.exp(-((q - 0.5) / 0.22) ** 2); out = out * env / (np.abs(out * env).max() + 1e-9) * db(level)
    pan = np.linspace(-0.85, 0.85, n)
    return np.stack([out * (1 - pan) / 1.3, out * (1 + pan) / 1.3], 1).astype(np.float32)

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
    vo, duck = vo_track()
    mus = mus * db(-4.0 * np.clip(duck, 0, 1.3))[:, None]
    fx = np.zeros((N + PRE, 2), np.float32); n = N + PRE; tt = np.arange(n) / SR - PRE / SR
    # beds: low room tone everywhere (crosses the wrap); rain + car interior in the car sections
    drone = bq(noise(n, 190), "low", 180, 2) + 0.12 * np.sin(2 * np.pi * 38 * tt)
    fx += stereo(norm(drone, -42))
    rb = rain_bed(n); road = bq(noise(n, 220), "low", 140, 2) * (1 + 0.15 * np.sin(2 * np.pi * 0.7 * tt))
    car_w = np.zeros(n, np.float32)
    for a0, a1 in ((-PRE / SR, E.th(80) + 0.15), (E.th(128) - 0.10, E.th(136) + 0.10), (E.DUR - 0.45, E.DUR + 1)):
        car_w = np.maximum(car_w, np.clip(np.minimum((tt - a0) / 0.12, (a1 - tt) / 0.20), 0, 1))
    fx += stereo(norm(rb, -31) * car_w * 0.9 + norm(road, -36) * car_w)
    # ---- every transition gets its own sound
    T = {s_["n"]: s_ for s_ in E.SHOTS}
    for s_ in E.SHOTS:
        tin, t0 = s_.get("tin"), s_["t0"]
        if tin == "mirror_in":                                       # streetlight hum comes up on the mirror, push into it
            place(fx, stereo(neon_buzz(0.5, -34, (0, 0, 1, 1, 1, 1))), 0.07)
            place(fx, A2.whoosh(0.55, -26, 300, True), 22 / E.FPS); place(fx, stereo(glass_chime(-33)), 0.55)
        elif tin == "light_sweep": place(fx, pass_by(0.8, -22, 301), t0 - 0.40)
        elif tin == "wiper":                                         # wiper thunk + rubber squeak across the glass
            place(fx, stereo(A2.impact(-27, (110, 70), 0.06, 0.3, 302)), t0 - 8 / E.FPS)
            n_ = I(0.30); q = np.arange(n_) / SR
            sq = np.sin(2 * np.pi * np.cumsum(900 + 500 * np.sin(np.pi * q / 0.3)) / SR) * 0.25 + bq(noise(n_, 303), "band", np.array([1500, 5000]), 2) * 0.6
            place(fx, stereo(norm(sq * np.sin(np.pi * q / 0.30) ** 0.6, -27), 0.3), t0 - 6 / E.FPS)
        elif tin == "knife_pass":                                    # the beat returns: the knife is drawn, whips out, swings across
            n_ = I(0.32); q = np.arange(n_) / SR                                       # draw: steel scraping out of leather
            scr = bq(noise(n_, 400), "band", np.array([2500, 9000]), 2) * np.sin(np.pi * q / 0.32) ** 0.7
            ring = sum(np.sin(2 * np.pi * fq * q) * np.exp(-q / d) for fq, d in ((2350, 0.25), (3720, 0.18), (5900, 0.12)))
            place(fx, stereo(norm(scr + 0.35 * ring, -24), 0.3), t0 - 28 / E.FPS)
            place(fx, A2.whoosh(0.16, -24, 401, True), t0 - 16 / E.FPS)                 # whips out of frame
            place(fx, A2.whoosh(0.22, -18, 402, False), t0 - 9 / E.FPS)                 # the swing
            n_ = I(1.3); q = np.arange(n_) / SR                                        # the hit: a long steel ring + sub
            hit = sum(a_ * np.sin(2 * np.pi * fq * q) * np.exp(-q / d) for fq, a_, d in ((1830, 1.0, 0.55), (2911, 0.7, 0.40), (4420, 0.5, 0.28), (6890, 0.3, 0.15)))
            place(fx, stereo(norm(hit * np.minimum(1, q / 0.002), -20), -0.2), t0)
            place(fx, stereo(A2.impact(-14, (68, 34), 0.40, 0.5, 403)), t0)
        elif tin == "whip": place(fx, A2.whoosh(0.22, -21, 306, True), t0 - 0.10)
        elif tin == "facematch": place(fx, A2.whoosh(0.30, -24, 307, False), t0 - 0.14); place(fx, stereo(A2.impact(-25, (85, 45), 0.18, 0.4, 308)), t0)
        elif tin == "light_leak": place(fx, stereo(chord_swell(-30, 0.8, (440, 554.37, 659.25))), t0 - 0.12); place(fx, A2.whoosh(0.35, -27, 309, True), t0 - 0.15)
        elif tin == "whip_up": place(fx, A2.whoosh(0.24, -21, 310, True), t0 - 0.11)
        elif tin == "logo_orig":
            place(fx, stereo(A2.impact(-20, (110, 60), 0.12, 0.7, 311)), t0 - 0.20)
            place(fx, np.stack([A2.shimmer(0.9, -29)] * 2, 1), t0 - 0.15); place(fx, A2.whoosh(0.32, -21, 312, True), t0 - 0.10)
        elif tin == "wrap":                                          # plastic sheeting sweeps the lens
            n_ = I(0.40); q = np.arange(n_) / SR
            cr = bq(noise(n_, 313), "band", np.array([900, 7000]), 2) * (np.random.default_rng(314).random(n_) > 0.75) * np.sin(np.pi * q / 0.4)
            place(fx, stereo(norm(cr, -25), -0.2), t0 - 6 / E.FPS)
        elif tin == "impact":
            place(fx, stereo(A2.impact(-15, (65, 32), 0.30, 0.8, 315)), t0); place(fx, stereo(swish(-22, 0.09, 316)), t0 - 0.06)
        elif tin == "rainfocus":                                     # the rain swells as the glass comes into focus
            n_ = I(0.6); q = np.arange(n_) / SR; sw_ = rain_bed(n_, 317) * np.sin(np.pi * q / 0.6) ** 1.5
            place(fx, stereo(norm(sw_, -24)), t0 - 0.25)
        elif tin == "lamp_on":                                       # a lamp switch clicks, the filament hums up
            place(fx, stereo(A2.tick(-22, 390)), t0 - 0.02)
            n_ = I(0.5); q = np.arange(n_) / SR; hm = (np.sin(2 * np.pi * 120 * q) + 0.4 * np.sin(2 * np.pi * 240 * q)) * np.minimum(1, q / 0.05) * np.exp(-q / 0.3)
            place(fx, stereo(norm(hm, -33)), t0)
        elif tin == "shadow":
            place(fx, stereo(rev(A2.impact(-20, (55, 28), 0.5, 0.2, 318))[-I(0.25):]), t0 - 0.25); place(fx, A2.whoosh(0.4, -27, 319, False), t0 - 0.2)
        elif tin == "bloom":                                         # the drop hits the water: sub boom, bloop, splash, underwater swell
            place(fx, stereo(A2.impact(-9, (48, 24), 0.9, 0.3, 320)), t0)
            place(fx, stereo(bloop(-17, 321)), t0 - 0.01)
            n_ = I(0.7); q = np.arange(n_) / SR
            spl = bq(noise(n_, 322), "band", np.array([300, 4500]), 2) * np.exp(-q / 0.10)
            place(fx, np.stack([norm(spl, -18), np.roll(norm(spl, -18), 70)], 1), t0 + 0.01)
            uw = bq(noise(I(1.0), 323), "low", 400, 2) * np.sin(np.pi * np.arange(I(1.0)) / I(1.0)) ** 1.5
            place(fx, stereo(norm(uw, -26)), t0 + 0.05)
        elif tin == "slam":                                          # one hit per syllable of "I don't wish you well"
            i_ = E.SHOTS.index(s_); pan = 0.5 if i_ % 2 else -0.5
            place(fx, stereo(A2.impact(-21 if s_["n"] != "well" else -16, (90, 48), 0.12, 0.6, 330 + i_), pan * 0.4), t0)
    # ---- the kill kit: leather unrolls, knives settle, a steel ring as the streetlight glints up each blade
    for s_ in E.SHOTS:
        if s_.get("graphic") == "knife_roll":
            t0 = s_["t0"]; n_ = I(0.6); q = np.arange(n_) / SR
            lea = bq(noise(n_, 410), "band", np.array([300, 3000]), 2) * (0.6 + 0.4 * (np.random.default_rng(411).random(n_) > 0.8)) * np.sin(np.pi * q / 0.6) ** 0.8
            place(fx, stereo(norm(lea, -25), -0.3), t0 + 0.04)
            for k_ in range(5): place(fx, stereo(A2.tick(-31, 412 + k_), -0.6 + 0.3 * k_), t0 + 0.12 + 0.09 * k_)
            for k_, tg in enumerate((17.52, 18.04, 18.56)):
                n_ = I(0.9); q = np.arange(n_) / SR; fq0 = (3150, 2650, 3550)[k_]
                tg_ = sum(a_ * np.sin(2 * np.pi * fq0 * r_ * q) * np.exp(-q / d) for r_, a_, d in ((1.0, 1.0, 0.35), (1.51, 0.5, 0.22), (2.33, 0.3, 0.12)))
                place(fx, stereo(norm(tg_ * np.minimum(1, q / 0.002), -31), (-0.5, 0.5, 0.0)[k_]), E.s2e(tg))
    # ---- graphics / text: the freeze click on "Darling," + pen scratch; the drop's slow fall + heartbeat; the end
    dt = E.DARLING_T
    place(fx, stereo(shutter_ticks(-22, 2, 0.05, 340)), dt - 0.02); place(fx, stereo(glass_chime(-30)), dt + 0.02)
    for k_ in range(9):
        n_ = I(0.05); place(fx, stereo(norm(bq(noise(n_, 341 + k_), "band", np.array([2500, 8000]), 2) * np.sin(np.pi * np.arange(n_) / n_), -36), -0.4 + 0.1 * k_), dt + 0.04 + k_ * 0.06)
    tv = E.VO[0][2]
    for k_ in range(10):
        n_ = I(0.05); place(fx, stereo(norm(bq(noise(n_, 351 + k_), "band", np.array([2500, 8000]), 2) * np.sin(np.pi * np.arange(n_) / n_), -38), -0.4 + 0.08 * k_), tv + 0.02 + k_ * 0.075)
    d0 = T["drop"]["t0"]; d1 = T["drop"]["t1"]
    n_ = I(0.45); q = np.arange(n_) / SR                                               # the drop swells on the comma ... and lets go
    visc = np.sin(2 * np.pi * np.cumsum(180 + 120 * q / 0.45) / SR) * 0.3 * np.sin(np.pi * q / 0.45)
    place(fx, stereo(norm(visc, -36)), d0)
    place(fx, stereo(drip(-24, 415)[I(0.13):]), d0 + 26 / E.FPS)
    n_ = I(d1 - d0); q = np.arange(n_) / SR; u = q / (d1 - d0)
    fall = np.sin(2 * np.pi * np.cumsum(420 - 300 * u ** 1.5) / SR) * 0.2 * u ** 2 + bq(noise(n_, 360), "band", np.array([200, 1200]), 2) * u ** 3 * 0.5
    place(fx, stereo(norm(fall, -28)), d0)
    place(fx, stereo(heartbeat(-20)), d0 + 0.15); place(fx, stereo(heartbeat(-18)), d0 + 0.95)
    for k_, wt in enumerate([wt for tx in E.TEXT if tx["style"] == "behind" for _, wt, _ in tx["words"]]):
        place(fx, A2.whoosh(0.16, -30, 370 + k_, True), wt - 0.08)
    # dead stop: the last beat's reverb tail wraps into the opening (under the rain), + the mirror pull-back
    ir_ = A2.ir(1.1, seed=380); last = mus[PRE + I(E.DUR - 0.30):PRE + I(E.DUR)]
    tail = A2.conv(np.vstack([last, np.zeros((I(1.6), 2), np.float32)]), ir_) * db(-11)
    tail = bq(tail, "low", 2600, 2); tail[:I(0.30)] = 0
    tail = tail[I(0.30):]; place(fx, tail, -PRE / SR)
    place(fx, A2.whoosh(0.40, -25, 381, False), E.DUR - 0.40); place(fx, stereo(glass_chime(-34)), E.DUR - 0.05)
    fx = np.tanh(fx * 1.3) / 1.3
    full = mus + vo + fx
    lead, mix = full[:PRE].copy(), full[PRE:].copy()
    th_ = np.linspace(0, np.pi / 2, PRE)[:, None]                    # circular join (drone -> drone)
    mix[-PRE:] = mix[-PRE:] * np.cos(th_) + lead * np.sin(th_)
    raw = f"{AD}/mix_raw.wav"; wf.write(raw, SR, mix.astype(np.float32))
    Iraw, _ = measure(raw); gain = -12.6 - Iraw
    P2 = SR; wrapped = np.vstack([mix[-P2:], mix, mix[:P2]])
    wf.write(f"{AD}/mix_raw_wrapped.wav", SR, wrapped.astype(np.float32))
    tmp = f"{AD}/mix_wrapped_master.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{AD}/mix_raw_wrapped.wav", "-af", f"volume={gain:.2f}dB,aresample=192000,"
                    f"alimiter=limit={db(-3.4):.4f}:attack=3:release=60:level=disabled,aresample=48000:resampler=soxr", "-c:a", "pcm_f32le", tmp], check=True)
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
    print("rms: lead-in", round(lv(0.3, 5.0), 1), "beat", round(lv(5.3, 13.8), 1), "break", round(lv(14.0, 19.0), 1), "drop", round(lv(19.15, 21.6), 1))

if __name__ == "__main__":
    main()
