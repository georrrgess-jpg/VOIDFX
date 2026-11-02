"""Soundtrack for THE DARK PASSENGER — replicates the reference's sound setup.

1. MATRIX FUNK slowed again by R = 1.12644 with the pitch drop (vinyl-style), as in the reference (102.8 BPM).
2. Intro (edit 0 -> drop): band-limited 'through the wall' (high-pass 180 Hz, low-pass 3.2 kHz), like the
   reference's bass-less intro; a one-beat echo-out gap after the first phrase.
3. Drop: full-range music from the song's own re-entry after its break (orig half-beat 66).
4. Bang: the music stops dead after the hit on the final downbeat; only its reverb tail remains under the logo.
5. Sparse synthesized sound design: typing ticks, light-flicker buzz, riser, drop impact, whoosh, glitch bursts,
   panel slams, bang, logo shimmer. Loudness -12.5 LUFS, true peak checked after AAC encoding.
"""
import os, sys, math, subprocess
import numpy as np, scipy.io.wavfile as wf, scipy.signal as ss
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edl2 as E

SR = 48000
A = f"{E.ROOT}/v2/audio"
N = int(round(E.DUR_F / E.FPS * SR))
rng = np.random.default_rng(21)

def T(e): return int(round(E.te(e) * SR))

def slowed():
    p = f"{A}/song_slowed_48k.wav"
    if not os.path.exists(p):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{E.ROOT}/src/matrix_funk_slowed.mp3", "-af",
                        f"aresample=48000,asetrate={48000 / E.R:.6f},aresample=48000:resampler=soxr:precision=28",
                        "-c:a", "pcm_f32le", p], check=True)
    sr, x = wf.read(p); assert sr == SR
    return x.astype(np.float32)

def bq(x, kind, f, order=4):
    sos = ss.butter(order, f / (SR / 2), kind, output="sos")
    return ss.sosfilt(sos, x, axis=0).astype(np.float32)

def ir(decay, n=None, seed=1):
    n = n or int(decay * 4 * SR)
    r = np.random.default_rng(seed)
    t = np.arange(n) / SR
    L = r.standard_normal(n) * np.exp(-t / decay); Rr = r.standard_normal(n) * np.exp(-t / decay)
    L[:int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR)); Rr[:int(0.016 * SR)] *= np.linspace(0, 1, int(0.016 * SR))
    h = np.stack([L, Rr], 1).astype(np.float32)
    return bq(h, "low", 6000, 2) / np.sqrt(np.sum(h ** 2) / 2)

def conv(x, h):
    return np.stack([ss.fftconvolve(x[:, i], h[:, i])[:len(x)] for i in range(2)], 1).astype(np.float32)

def fade(n, kind="in"):
    r = np.sin(np.linspace(0, np.pi / 2, n)) ** 2
    return r if kind == "in" else r[::-1]

def place(out, sig, i):
    if sig.ndim == 1: sig = np.stack([sig, sig], 1)
    j = min(len(out), i + len(sig))
    if i < 0: sig = sig[-i:]; i = 0
    out[i:j] += sig[:j - i]

def noise(n, seed): return np.random.default_rng(seed).standard_normal(n).astype(np.float32)

def env_exp(n, tau, att=0.002):
    t = np.arange(n) / SR
    return (np.minimum(1, t / att) * np.exp(-t / tau)).astype(np.float32)

def db(x): return 10 ** (x / 20)

# ------------------------------------------------------------------ sfx
def impact(level=-8, sub=(68, 36), tau=0.75, crack=0.35, seed=3):
    n = int(2.2 * SR); t = np.arange(n) / SR
    f = sub[1] + (sub[0] - sub[1]) * np.exp(-t / 0.18)
    ph = 2 * np.pi * np.cumsum(f) / SR
    boom = np.sin(ph) * env_exp(n, tau, 0.003)
    c = bq(noise(n, seed), "high", 1800, 2) * env_exp(n, 0.035, 0.0005) * crack
    body = bq(noise(n, seed + 1), "band", np.array([120, 900]), 2) * env_exp(n, 0.12, 0.001) * 0.4
    y = boom + c + body
    return (y / np.abs(y).max() * db(level)).astype(np.float32)

def riser(dur, level=-17, seed=5):
    n = int(dur * SR); t = np.arange(n) / SR; u = t / dur
    x = noise(n, seed)
    out = np.zeros(n, np.float32); blk = 2048
    for i in range(0, n, blk):                               # swept band-pass, 350 Hz -> 7 kHz
        fc = 350 * (7000 / 350) ** (u[i] ** 1.6)
        sos = ss.butter(2, [fc / 1.6 / (SR / 2), min(0.95, fc * 1.6 / (SR / 2))], "band", output="sos")
        seg = x[max(0, i - 4096):i + blk]
        y = ss.sosfilt(sos, seg)[-min(blk, n - i):]
        out[i:i + len(y)] = y
    out *= (u ** 2.2) * db(level) / (np.abs(out).max() + 1e-9) * 1.0
    out[-int(0.004 * SR):] *= np.linspace(1, 0, int(0.004 * SR))
    return np.stack([out * 0.9, out], 1)

def whoosh(dur=0.32, level=-22, seed=7, up=True):
    n = int(dur * SR); u = np.arange(n) / n
    x = noise(n, seed); out = np.zeros(n, np.float32); blk = 1024
    for i in range(0, n, blk):
        fc = (300 * (3500 / 300) ** u[i]) if up else (3500 * (300 / 3500) ** u[i])
        sos = ss.butter(2, [fc / 1.5 / (SR / 2), min(0.95, fc * 1.5 / (SR / 2))], "band", output="sos")
        seg = x[max(0, i - 2048):i + blk]; y = ss.sosfilt(sos, seg)[-min(blk, n - i):]; out[i:i + len(y)] = y
    e = np.sin(np.pi * u) ** 1.5
    out = out * e; out = out / (np.abs(out).max() + 1e-9) * db(level)
    pan = np.linspace(-0.6, 0.6, n) if up else np.linspace(0.6, -0.6, n)
    return np.stack([out * (1 - pan) / 1.4, out * (1 + pan) / 1.4], 1)

def glitch_burst(dur=0.14, level=-21, seed=9):
    n = int(dur * SR); x = noise(n, seed)
    step = 24; x = np.repeat(x[::step], step)[:n]                          # sample-and-hold "bitcrush"
    gate = (np.floor(np.arange(n) / (0.012 * SR)) % 3 != 1).astype(np.float32)
    x = bq(x * gate, "band", np.array([500, 6000]), 2)
    x = x * env_exp(n, dur * 0.6, 0.001)
    return x / (np.abs(x).max() + 1e-9) * db(level)

def tick(level=-31, seed=0):
    n = int(0.03 * SR)
    x = bq(noise(n, 100 + seed), "band", np.array([1800, 7000]), 2) * env_exp(n, 0.006, 0.0003)
    th = np.sin(2 * np.pi * 180 * np.arange(n) / SR) * env_exp(n, 0.01) * 0.5
    y = x + th
    return y / (np.abs(y).max() + 1e-9) * db(level)

def buzz(dur, pattern, level=-26):
    n = int(dur * SR); t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * 120 * k * t) / k for k in range(1, 12))
    s = s + 0.3 * bq(noise(n, 13), "band", np.array([2000, 8000]), 2)
    g = np.zeros(n, np.float32); fpf = SR / E.FPS
    for i, v in enumerate(pattern):
        g[int(i * fpf):int((i + 1) * fpf)] = v
    g = np.convolve(g, np.ones(96) / 96, "same")
    y = s * g
    return y / (np.abs(y).max() + 1e-9) * db(level)

def shimmer(dur=1.8, level=-28):
    n = int(dur * SR); t = np.arange(n) / SR
    y = sum(np.sin(2 * np.pi * f * t + i) * np.exp(-t / (0.5 + 0.2 * i)) for i, f in enumerate([2349, 3136, 3951, 4699, 6272]))
    y = y * np.minimum(1, t / 0.05)
    return y / (np.abs(y).max() + 1e-9) * db(level)

# ------------------------------------------------------------------ build
def measure(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    return (float(r.split("Integrated loudness:")[1].split("I:")[1].split("LUFS")[0]),
            float(r.split("True peak:")[1].split("Peak:")[1].split("dBFS")[0]))

def main():
    song = slowed()
    S0 = int(round(E.orig_t(0) * E.R * SR)) - int(0.006 * SR)
    seg = song[S0:S0 + N + SR].copy()
    mus = np.zeros((N, 2), np.float32)
    d0 = T(E.DROP_E)
    # --- intro: lightly filtered (not muffled), opening smoothly to full range into the drop
    PR = SR                                                                  # filter 1 s of lead-in so it starts settled
    lead = song[S0 - PR:S0 + d0 + 4800]
    lite = bq(bq(lead, "high", 95, 2), "low", 7500, 2)[PR:] * db(-0.8)
    fullb = lead[PR:]
    w = np.zeros(len(lite), np.float32)                                      # 0 = lightly filtered, 1 = full
    a_, b_ = T(24), d0
    w[a_:b_] = np.sin(np.linspace(0, np.pi / 2, b_ - a_)) ** 2; w[b_:] = 1
    intro = lite * np.sqrt(1 - w)[:, None] + fullb * np.sqrt(w)[:, None]   # equal-power open-up
    g0, g1 = T(E.GAP_E[0]), T(E.GAP_E[1])
    gate = np.ones(len(intro), np.float32)
    nf = int(0.060 * SR); floor = db(-12)                                   # soft dip, not a hard cut
    gate[g0:g0 + nf] = floor + (1 - floor) * fade(nf, "out"); gate[g0 + nf:g1 - nf] = floor
    gate[g1 - nf:g1] = floor + (1 - floor) * fade(nf, "in")
    dry = intro * gate[:, None]
    wet = conv(dry, ir(0.42, seed=2))
    wl = np.full(len(intro), 0.08, np.float32)
    wl[g0 - nf:g1] = 0.30                                                    # echo tail fills the dip
    wl[g1:g1 + int(0.25 * SR)] = np.linspace(0.30, 0.08, int(0.25 * SR))
    wl[T(28):d0] = np.linspace(0.08, 0.0, d0 - T(28)); wl[d0:] = 0
    intro_mix = dry + wet * wl[:, None]
    xf = int(0.004 * SR)
    mus[:d0] = intro_mix[:d0]
    # --- drop: full range (4 ms crossfade on the downbeat)
    full = seg[:N].copy()
    b0 = T(E.BANG_E) + int(0.20 * SR)                                       # let the final downbeat hit ring
    full[:d0 - xf] = 0; full[d0 - xf:d0] *= fade(xf)[:, None]
    mus[d0 - xf:d0] *= fade(xf, "out")[:, None]
    TS = int(0.42 * SR)                                                  # tape-stop: playback speed ramps 1 -> 0
    t = np.arange(TS) / SR; pos = b0 + (t - t * t / (2 * TS / SR)) * SR
    src = seg[:b0 + TS + 10]
    ts_sig = np.stack([np.interp(pos, np.arange(len(src)), src[:, i]) for i in range(2)], 1).astype(np.float32)
    ts_sig *= (np.linspace(1, 0, TS) ** 0.6)[:, None]
    ts_sig = bq(ts_sig, "low", 9000, 2)
    full[b0:] = 0; full[b0:b0 + TS] = ts_sig[:max(0, min(TS, N - b0))]
    mus += full
    tail = conv(full[b0 - int(0.35 * SR):b0 + TS], ir(0.8, seed=4))
    place(mus, tail * 0.45, b0 - int(0.35 * SR))
    # --- sound design
    fx = np.zeros((N, 2), np.float32)
    f2s = lambda f: int(round(f / E.FPS * SR))
    # typing ticks (name card)
    nc = E.NAME_CARD; fi = E.fe(nc["e_in"]); f2 = E.fe(nc["e_in"] + 3)
    for i in range(1, len(nc["line1"]) + 1):
        pass
    for i in range(1, len(nc["line2"]) + 1, 2):
        pass
    # light flicker buzz (matches the picture pattern)
    pat = [1, .15, 1, .9, .05, 0, .7, .1, 0, 0, .35, 0, 0, 0]
    place(fx, bq(buzz(len(pat) / E.FPS + 0.05, pat, -37), "low", 5000, 2), g0)
    place(fx, bq(buzz(9 / E.FPS, [0, 0, .35, .05, .9, .45, 1, .6, .2], -39), "low", 5000, 2), g1)
    # title slam, riser, drop
    place(fx, impact(-17, (90, 45), 0.35, 0.25, 31), T(E.TITLE["e_in"]))
    rz = riser(E.te(E.DROP_E) - E.te(28), -19)
    place(fx, rz, d0 - len(rz))
    place(fx, impact(-7, (70, 36), 0.9, 0.45, 3), d0)
    # blood pour: low rumble + bubbling liquid noise swelling under the curtain, then a downward splash on the reveal
    p0 = T(30.6); n = d0 - p0
    t = np.arange(n) / SR; u = t / t[-1]
    liq = bq(noise(n, 300), "band", np.array([180, 1400]), 2)
    am = 0.65 + 0.35 * np.abs(np.sin(2 * np.pi * (9 + 5 * u) * t + 3 * np.sin(2 * np.pi * 3.1 * t)))
    rum = np.sin(2 * np.pi * np.cumsum(38 + 14 * u) / SR) * 0.8
    pour = (liq * am / (np.abs(liq).max() + 1e-9) + rum * 0.5) * (u ** 1.3)
    pour = pour / (np.abs(pour).max() + 1e-9) * db(-19)
    place(fx, np.stack([pour * 0.95, pour], 1), p0)
    place(fx, whoosh(0.32, -22, 33, False), d0 + int(0.03 * SR))
    # word thuds (NIGHT heavier)
    for w_, e_ in E.WORDS:
        place(fx, impact(-15 if w_ == "NIGHT" else -19, (95, 48), 0.22, 0.45, 50 + e_), T(e_))
    place(fx, whoosh(0.26, -24, 71, True), T(51.45))
    # two-clip transitions
    for kind, e_ in E.TRANS2:
        place(fx, whoosh(0.28 if kind == "slices" else 0.40, -24, 80 + e_, kind == "slices"), T(e_) - int(0.12 * SR))
    place(fx, bq(glitch_burst(0.15, -29, 4), "low", 6000, 2), int(0.004 * SR))                                 # flash-forward hook
    # whip whoosh, glitches, panel slams
    place(fx, whoosh(0.30, -21, 7, True), T(38) - int(0.17 * SR))
    for e in (53, 72):
        place(fx, bq(glitch_burst(0.13, -25, 9 + e), "low", 7000, 2), T(e) - int(0.035 * SR))
    for i, p in enumerate(E.PANELS):
        place(fx, impact(-23, (110, 60), 0.12, 0.5, 40 + i), T(p["e"]))
    # transition whooshes (peak lands on the cut) and splat hits
    for kind, e in E.TRANS:
        w = whoosh(0.30 if kind == "zoom" else 0.36, -24, 60 + e, kind == "zoom")
        place(fx, w, T(e) - int(0.17 * SR))
    for e, x, y, size, seed, life in E.SPLATS:
        n = int(0.16 * SR)
        sp = bq(noise(n, 200 + seed), "band", np.array([150, 1800]), 2) * env_exp(n, 0.045, 0.001)
        sp = sp / np.abs(sp).max() * db(-24)
        pan = (x / E.W) * 2 - 1
        place(fx, np.stack([sp * (1 - 0.5 * pan), sp * (1 + 0.5 * pan)], 1), T(e) + int(0.01 * SR))
    # bang + logo
    place(fx, impact(-5, (75, 32), 1.3, 0.7, 77), T(E.BANG_E))
    place(fx, conv(np.stack([impact(-12, (75, 32), 1.3, 0.7, 77)] * 2, 1), ir(1.1, seed=8)) * 0.4, T(E.BANG_E))
    lg0 = T(E.BANG_E) + f2s(6)
    place(fx, whoosh(0.34, -24, 17, False), lg0 - int(0.05 * SR))
    place(fx, np.stack([shimmer(1.9, -29)] * 2, 1) * np.array([0.8, 1.0]), T(E.BANG_E) + f2s(24))
    for j, kf in ():                                                          # (logo drips removed)
        n = int(0.18 * SR); tt = np.arange(n) / SR
        pl = np.sin(2 * np.pi * np.cumsum(1500 * np.exp(-tt / 0.03) + 420) / SR) * env_exp(n, 0.05, 0.001)
        place(fx, np.stack([pl * (0.9 - 0.3 * j), pl * (0.6 + 0.3 * j)], 1) * db(-30), T(E.BANG_E) + f2s(kf))
    fx = np.tanh(fx * 1.4) / 1.4                                          # soft-saturate the fx bus so hits stay smooth
    # duck the music 2.5 dB under the two biggest impacts (drop, bang) for 120 ms
    duck = np.ones(N, np.float32)
    for i0 in (d0, T(E.BANG_E)):
        n = int(0.30 * SR); env = 1 - (1 - db(-2.5)) * np.exp(-np.arange(n) / (0.12 * SR))
        duck[i0:i0 + n] = np.minimum(duck[i0:i0 + n], env[:len(duck[i0:i0 + n])])
    mix = mus * duck[:, None] + fx
    # 2 ms ramps at the file edges
    r = int(0.002 * SR); mix[:r] *= np.linspace(0, 1, r)[:, None]; mix[-r:] *= np.linspace(1, 0, r)[:, None]
    raw = f"{A}/mix_raw.wav"; wf.write(raw, SR, mix.astype(np.float32))
    I, TP = measure(raw)
    gain = -12.5 - I
    out = f"{A}/mix.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af",
                    f"volume={gain:.2f}dB,aresample=192000,alimiter=limit={db(-3.0):.4f}:attack=3:release=60:level=disabled,"
                    "aresample=48000:resampler=soxr", "-c:a", "pcm_s24le", out], check=True)
    # AAC encoder pre-roll (hidden by an edit list in the mp4): 1024 samples of the song's own lead-in
    sr_, m = wf.read(out); m = m.astype(np.float32) / 2 ** 31
    pre = song[S0 - 1024:S0] * db(gain)
    pre = bq(bq(pre, "high", 95, 2), "low", 7500, 2) * db(-0.8)
    pre[:256] *= np.linspace(0, 1, 256)[:, None]
    wf.write(f"{A}/mix_preroll.wav", SR, np.vstack([pre, m]).astype(np.float32))
    test = f"{A}/mix_aac_test.m4a"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-itsoffset", str(-1024 / SR), "-i", f"{A}/mix_preroll.wav",
                    "-c:a", "aac", "-b:a", "256k", test], check=True)
    I2, TP2 = measure(out); I3, TP3 = measure(test)
    print(f"raw {I:.1f} LUFS -> {gain:+.1f} dB -> wav {I2:.1f} LUFS / {TP2:.1f} dBTP; AAC {I3:.1f} LUFS / {TP3:.1f} dBTP")
    # section levels
    mm = m.mean(1)
    for lab, a, b in (("intro", 0, E.te(14)), ("gap", E.te(14), E.te(16)), ("intro2", E.te(16), E.te(32)),
                      ("drop", E.te(32), E.te(48)), ("late", E.te(64), E.te(80)), ("logo", E.te(80) + 0.6, E.te(88))):
        x = mm[int(a * SR):int(b * SR)]
        print(f"  {lab:7s} {20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9):6.1f} dBFS RMS")

if __name__ == "__main__":
    main()
