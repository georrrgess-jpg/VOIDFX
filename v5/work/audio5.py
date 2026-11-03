"""Soundtrack for FASTEST (voidfx v5): Duvet h208->h288 as a circular loop + speed-force sound design."""
import os, sys, math, subprocess
import numpy as np, scipy.io.wavfile as wf, scipy.signal as ss
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/home/user/VOIDFX/v2/work")
import edl5 as E
import audio2 as A2

SR = 48000; AD = f"{E.ROOT}/v5/audio"
N = int(round(E.DUR_F / E.FPS * SR))
PRE = 4800
def I(t): return int(round(t * SR))
db, bq, noise, env_exp = A2.db, A2.bq, A2.noise, A2.env_exp
def place(out, sig, t):
    A2.place(out, sig if sig.ndim == 2 else np.stack([sig, sig], 1), I(t) + PRE)
def stereo(x, pan=0.0): return np.stack([x * (1 - 0.5 * pan), x * (1 + 0.5 * pan)], 1).astype(np.float32)

def crack(level=-12, seed=1, tail=0.9):
    """lightning crack: sharp broadband snap + crackle + low rumble."""
    n = I(tail + 0.4); t = np.arange(n) / SR; rng = np.random.default_rng(seed)
    snap = bq(noise(n, seed), "high", 1500, 2) * env_exp(n, 0.018, 0.0003)
    crk = np.zeros(n, np.float32)
    for _ in range(40):
        i = int(rng.uniform(0, 0.25) * SR); m = int(0.004 * SR)
        crk[i:i + m] += rng.uniform(0.3, 1.0) * bq(noise(m, int(rng.integers(1e6))), "high", 2500, 2)
    rum = bq(noise(n, seed + 3), "low", 160, 2) * env_exp(n, tail * 0.5, 0.02) * 3.0
    y = snap + 0.5 * crk + rum
    y = y / np.abs(y).max() * db(level)
    return np.stack([y, np.roll(y, 23)], 1).astype(np.float32)

def zap(level=-20, seed=2, dur=0.25):
    n = I(dur); t = np.arange(n) / SR
    buzz = np.sign(np.sin(2 * np.pi * (120 + 60 * np.sin(2 * np.pi * 9 * t)) * t)) * 0.3 + bq(noise(n, seed), "band", np.array([1500, 7000]), 2)
    y = buzz * env_exp(n, dur * 0.4, 0.002)
    return y / np.abs(y).max() * db(level)

def shimmer_phase(level=-24, dur=0.5):
    n = I(dur); t = np.arange(n) / SR
    y = sum(np.sin(2 * np.pi * f * t + 3 * np.sin(2 * np.pi * 31 * t)) for f in (880, 1320, 1975))
    y = y * np.sin(np.pi * t / dur) ** 2
    return y / np.abs(y).max() * db(level)

def measure(p):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", p, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(r.split("Integrated loudness:")[1].split("I:")[1].split("LUFS")[0]), float(r.split("True peak:")[1].split("Peak:")[1].split("dBFS")[0])

def main():
    sr, song = wf.read(f"{AD}/song48.wav"); song = song.astype(np.float32)
    mus = np.zeros((N + PRE, 2), np.float32); fx = np.zeros((N + PRE, 2), np.float32)
    s0 = I(E.SONG_IN)
    mus[:] = song[s0 - PRE:s0 - PRE + N + PRE] * db(-1.5)            # includes the natural lead-in before edit 0
    T = {s["n"]: s for s in E.SHOTS}
    tin = lambda n: T[n]["t0"]
    # opening lightning strike (also what you hear on every loop)
    place(fx, crack(-11, 1, 1.0), 0.0)
    for s in E.SHOTS:
        t = s.get("tin")
        if t == "bolt_split": place(fx, crack(-14, 7 + int(s["t0"] * 10), 0.6), s["t0"] - 5 / E.FPS)
        elif t == "tunnel": place(fx, A2.whoosh(0.45, -19, 20, True), s["t0"] - 0.30); place(fx, stereo(A2.impact(-18, (60, 30), 0.5, 0.2, 21)), s["t0"])
        elif t == "phase": place(fx, stereo(shimmer_phase(-25, 0.45)), s["t0"] - 0.18)
        elif t == "flare": place(fx, A2.whoosh(0.35, -26, 22, False), s["t0"] - 0.15)
        elif t == "whip": place(fx, A2.whoosh(0.26, -21, 23 + int(s["t0"]), True), s["t0"] - 0.10)
        elif t == "zoomblur": place(fx, A2.whoosh(0.30, -21, 24, True), s["t0"] - 0.12)
        elif t == "roll": place(fx, A2.whoosh(0.30, -21, 25, False), s["t0"] - 0.12)
        elif t == "twirl": place(fx, A2.whoosh(0.34, -21, 26, True), s["t0"] - 0.12)
        elif t in ("flash", "cut_rgb"): place(fx, stereo(zap(-24, int(s["t0"] * 7), 0.18)), s["t0"])
        elif t == "dissolve": place(fx, A2.whoosh(0.5, -30, 27, False), s["t0"] - 0.2)
        elif t == "logo":
            place(fx, stereo(A2.impact(-19, (110, 60), 0.12, 0.7, 28)), s["t0"] - 0.20)
            place(fx, np.stack([A2.shimmer(0.9, -27)] * 2, 1), s["t0"] - 0.15)
            place(fx, A2.whoosh(0.32, -21, 29, True), s["t0"] - 0.10)
    for s in E.SHOTS:                                                # crackle under the arc shots
        if s.get("arcs"):
            t = s["t0"] + 0.1
            while t < s["t1"] - 0.1:
                place(fx, stereo(zap(-31, int(t * 100), 0.10), np.random.default_rng(int(t * 10)).uniform(-0.6, 0.6)), t); t += 0.27
    # final fly into the eye -> streak rush (rises into the loop's opening crack)
    fin = T["final_eye"]; place(fx, A2.whoosh(0.55, -19, 30, True)[::-1].copy(), E.DUR - 0.55)
    fx = np.tanh(fx * 1.3) / 1.3
    full = mus + fx
    lead, mix = full[:PRE].copy(), full[PRE:].copy()
    # circular: the window is exactly 10 bars, so the end flows musically into bar 26
    th_ = np.linspace(0, np.pi / 2, PRE)[:, None]
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
    print(f"raw {Iraw:.1f} -> {gain:+.1f} dB -> wav {I2:.1f} LUFS/{TP2:.1f} dBTP; AAC {I3:.1f} LUFS/{TP3:.1f} dBTP")
    mm = m.mean(1); loop = np.concatenate([mm[-24000:], mm[:24000]]); d = np.abs(np.diff(loop))
    print(f"loop seam step {d[23997:24003].max():.4f} vs local median {np.median(d[21600:26400]):.4f}")

if __name__ == "__main__":
    main()
