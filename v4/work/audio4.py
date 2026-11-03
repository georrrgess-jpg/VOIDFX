"""Soundtrack for SURPRISE v4: continuous Doakes exchange -> Need It -> tape stop -> Doakes line -> into the pupil (loops)."""
import os, sys, math, subprocess
import numpy as np, scipy.io.wavfile as wf, scipy.signal as ss
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/home/user/VOIDFX/v2/work")
import edl4 as E
import audio2 as A2                      # synth helpers (impact, whoosh, riser, glitch_burst, shimmer, ir, conv ...)

SR = 48000; AD = f"{E.ROOT}/v4/audio"
N = int(round(E.DUR * SR))
def I(t): return int(round(t * SR))
db = A2.db; bq = A2.bq; noise = A2.noise; env_exp = A2.env_exp

PRE = 4800          # timeline starts PRE samples before edit 0: that audio is the natural lead-in to the loop start
def place(out, sig, t):
    A2.place(out, sig if sig.ndim == 2 else np.stack([sig, sig], 1), I(t) + PRE)

def stereo(x, pan=0.0):
    return np.stack([x * (1 - 0.5 * pan), x * (1 + 0.5 * pan)], 1).astype(np.float32)

def blip(f0=1800, dur=0.05, level=-30):
    n = I(dur); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f0 * t) * env_exp(n, dur * 0.35, 0.001)
    return y / np.abs(y).max() * db(level)

def gunshot(level=-4):
    n = I(1.6); t = np.arange(n) / SR
    crack = bq(noise(n, 501), "high", 900, 2) * env_exp(n, 0.012, 0.0002)
    body = bq(noise(n, 502), "band", np.array([150, 2500]), 2) * env_exp(n, 0.06, 0.0005)
    thump = np.sin(2 * np.pi * np.cumsum(55 + 90 * np.exp(-t / 0.03)) / SR) * env_exp(n, 0.18, 0.001)
    y = 1.0 * crack + 0.8 * body + 0.9 * thump
    y = y / np.abs(y).max()
    tail = A2.conv(np.stack([y, y], 1), A2.ir(0.9, seed=11))[:, :] * 0.35
    out = np.stack([y, y], 1) + tail
    return (out / np.abs(out).max() * db(level)).astype(np.float32)

def glass(level=-11, seed=7):
    n = I(1.4); t = np.arange(n) / SR; rng = np.random.default_rng(seed)
    y = np.zeros(n, np.float32)
    for i in range(70):                                         # many tiny glass pieces
        t0 = rng.uniform(0, 0.55) ** 1.6; f = rng.uniform(2500, 9500); a = rng.uniform(0.2, 1.0) * (1 - t0 * 1.2)
        i0 = I(t0); m = n - i0
        tt = np.arange(m) / SR
        y[i0:] += a * np.sin(2 * np.pi * f * tt + rng.uniform(0, 6)) * np.exp(-tt / rng.uniform(0.02, 0.09))
    burst = bq(noise(n, seed + 1), "high", 2500, 2) * env_exp(n, 0.08, 0.0005) * 2.5
    y = y + burst
    y = y / np.abs(y).max() * db(level)
    L = y; R = np.roll(y, 37)
    return np.stack([L, R], 1).astype(np.float32)

def shutter(level=-18):
    n = I(0.12); y = np.zeros(n, np.float32)
    for t0, a in ((0.0, 1.0), (0.045, 0.7)):
        i0 = I(t0); m = I(0.03)
        y[i0:i0 + m] += a * bq(noise(m, int(t0 * 1000) + 3), "band", np.array([1500, 7000]), 2) * env_exp(m, 0.006, 0.0002)
    return y / np.abs(y).max() * db(level)

def drone(dur, level=-30):
    n = I(dur); t = np.arange(n) / SR
    y = sum(ss.sawtooth(2 * np.pi * f * t) for f in (55.0, 55.4, 82.4)) / 3
    y = bq(y, "low", 240, 2) + 0.25 * bq(noise(n, 77), "band", np.array([200, 900]), 2)
    swell = np.minimum(1, t / 0.8) * (0.55 + 0.45 * (t / dur) ** 2)
    y = y * swell
    return y / np.abs(y).max() * db(level)

def heartbeat(level=-14):
    n = I(0.5); t = np.arange(n) / SR; y = np.zeros(n)
    for t0, a in ((0, 1.0), (0.17, 0.7)):
        i0 = I(t0); m = n - i0; tt = np.arange(m) / SR
        y[i0:] += a * np.sin(2 * np.pi * (48 + 30 * np.exp(-tt / 0.02)) * tt) * np.exp(-tt / 0.07) * np.minimum(1, tt / 0.004)
    return y / np.abs(y).max() * db(level)

def tape_stop(sig, dur=0.40):
    n = I(dur); t = np.arange(n) / SR
    pos = (t - t * t / (2 * dur)) * SR
    out = np.stack([np.interp(pos, np.arange(len(sig)), sig[:, c]) for c in range(2)], 1).astype(np.float32)
    out *= (np.linspace(1, 0, n) ** 0.6)[:, None]
    return bq(out, "low", 8000, 2)

def measure(p):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", p, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(r.split("Integrated loudness:")[1].split("I:")[1].split("LUFS")[0]), float(r.split("True peak:")[1].split("Peak:")[1].split("dBFS")[0])

def main():
    sr, dk = wf.read(f"{AD}/doakes48k.wav"); dk = dk.astype(np.float32)
    sr, song = wf.read(f"{AD}/song48.wav"); song = song.astype(np.float32)
    dia = np.zeros((N + PRE, 2), np.float32); mus = np.zeros((N + PRE, 2), np.float32); fx = np.zeros((N + PRE, 2), np.float32)
    # ---- dialogue: one continuous take (0-4.30), J-cut into Dexter's reply, closing line; 40 ms equal-power edges
    for i, (a, b, at) in enumerate(E.DIALOGUE):
        lead_in = PRE if i == 0 else 0                           # line 1 also fills the loop lead-in
        seg = dk[I(a) - lead_in:I(b)].copy()
        seg = bq(seg, "high", 75, 2)
        bqp, aqp = ss.iirpeak(3000 / (SR / 2), 1.0); seg = seg + 0.22 * ss.lfilter(bqp, aqp, seg, axis=0).astype(np.float32)
        env = np.sqrt(np.convolve(seg.mean(1) ** 2, np.ones(960) / 960, "same")); act = env > env.max() * 0.12
        g_ = db(-14.0) / (np.sqrt(np.mean(seg.mean(1)[act] ** 2)) + 1e-9); seg *= g_
        if i == 0: g0 = g_
        nf = I(0.040); ramp = np.sin(np.linspace(0, np.pi / 2, nf)) ** 2
        if i != 0: seg[:nf] *= ramp[:, None]                      # edit 0 starts at full level: it continues the loop
        seg[-nf:] *= ramp[::-1, None]
        place(dia, seg, at - (0.02 if i == 1 else 0.0) - lead_in / SR)
    # ---- cold-open bed: low drone (continuous under both lines) + riser into the white flash
    place(fx, stereo(drone(E.T_SONG + 0.85, -32)), -0.80)          # starts before 0 so it is already at level
    # loop seam: the scene's own room tone (src 15.62-16.20, the gap before "Jesus") fades in under the last 0.58 s,
    # processed like line 1, so the wrap from 25.00 -> 0.00 is the same ambience continuing
    rt = dk[I(15.62):I(16.20)].copy(); rt = bq(rt, "high", 75, 2)
    bqp, aqp = ss.iirpeak(3000 / (SR / 2), 1.0); rt = rt + 0.22 * ss.lfilter(bqp, aqp, rt, axis=0).astype(np.float32)
    rt *= g0; nf = I(0.30); rt[:nf] *= (np.sin(np.linspace(0, np.pi / 2, nf)) ** 2)[:, None]
    place(dia, rt, E.DUR - len(rt) / SR)
    place(fx, A2.riser(1.30, -21), E.T_SONG - 1.30)
    place(fx, A2.whoosh(0.40, -25, 70, True)[::-1].copy(), 0.0)                               # iris opens (inhale)
    # BAY / HARBOR / BUTCHER: a deep thud under each word of the knockout title, a whoosh as it flies apart
    for j, (w, ws) in enumerate(E.BHB):
        place(fx, stereo(A2.impact(-20 + 2 * j, (70 - 8 * j, 38), 0.35, 0.2, 90 + j)), E.d2e(0, ws))
    place(fx, A2.whoosh(0.32, -24, 93, True), [x for x in E.SHOTS if x["n"] == "bhb_close"][0]["t1"] - 0.30)
    # bridge morph: a soft reversed swell under the light bloom
    br = [x for x in E.SHOTS if x["n"] == "bridge"][0]
    place(fx, A2.whoosh(br["t1"] - br["t0"] + 0.1, -27, 94, True)[::-1].copy(), br["t0"] - 0.05)
    # ---- song
    s0, s1 = I(E.SONG_IN), I(E.st(E.SONG_OUT_HB)) + I(0.01)
    sg = song[s0:s1].copy() * db(-2.5)
    nf = I(0.008); sg[:nf] *= np.linspace(0, 1, nf)[:, None]
    place(mus, sg, E.T_SONG)
    ts_ = tape_stop(song[s1 - 10:s1 + I(0.6)] * db(-2.5), 0.42)
    place(mus, ts_, E.T_SONG + (s1 - s0) / SR)
    tail = A2.conv(song[s1 - I(0.3):s1] * db(-2.5), A2.ir(0.8, seed=4)) * 0.4
    place(mus, tail, E.T_SONG + (s1 - s0) / SR - 0.3)
    # ---- sound design (every transition has a sound)
    T = {s["n"]: s for s in E.SHOTS}
    def tin(n): return T[n]["t0"]
    place(fx, stereo(A2.impact(-9, (70, 34), 0.8, 0.5, 22)), E.T_SONG)                      # white flash / song entry
    sk = A2.whoosh(0.55, -21, 71, False); place(fx, sk[::-1].copy(), tin("scope") - 0.55)   # sucked through the barrel
    place(fx, stereo(A2.impact(-19, (55, 30), 0.5, 0.15, 72)), tin("scope"))                # emerge: low thud
    for j in range(3): place(fx, stereo(blip(1900 + 400 * j, 0.03, -33)), tin("scope") + 0.10 + 0.06 * j)   # focus clicks
    t, step = E.te(37), 0.42
    while t < E.te(40.5) - 0.05:                                                             # lock-on beeps accelerate
        place(fx, stereo(blip(2900, 0.04, -31)), t); t += step; step = max(0.10, step * 0.80)
    place(fx, stereo(blip(3400, 0.18, -29)), E.te(40.5) - 0.02)
    for h in (38, 39, 40): place(fx, stereo(heartbeat(-13)), E.te(h))
    # BLEED IT: wet fill + three drips
    n = I(0.35); tt = np.arange(n) / SR
    wet = bq(noise(n, 95), "band", np.array([200, 1200]), 2) * np.exp(-tt / 0.12) * (0.6 + 0.4 * np.sin(2 * np.pi * 14 * tt))
    place(fx, stereo(wet / np.abs(wet).max() * db(-26)), E.s2e(16.78))
    for j in range(3):
        m_ = I(0.12); tq = np.arange(m_) / SR
        pl = np.sin(2 * np.pi * np.cumsum(1300 * np.exp(-tq / 0.025) + 380) / SR) * env_exp(m_, 0.04, 0.001)
        place(fx, stereo(pl * db(-31), 0.4 - 0.4 * j), E.s2e(16.78) + 0.10 + 0.07 * j)
    D = E.te(E.DROP_HB)
    place(fx, gunshot(-3), D - 0.004)
    place(fx, glass(-10, 7), D + 5 / E.FPS)
    place(fx, stereo(A2.impact(-8, (60, 30), 1.0, 0.3, 23)), D)
    place(fx, bq(A2.whoosh(0.34, -20, 73, False), "low", 2500, 2), tin("turn") - 0.15)       # dark pass (low)
    place(fx, A2.whoosh(0.32, -22, 33, False)[::-1].copy(), tin("hood") - 0.30)              # eye portal suck
    place(fx, A2.whoosh(0.30, -21, 34, True), tin("choke") - 0.12)                           # roll
    for n in ("attack", "fight", "fingergun"):
        place(fx, stereo(A2.impact(-17, (95, 50), 0.15, 0.6, 40 + len(n))), tin(n))
    place(fx, stereo(A2.impact(-18, (110, 60), 0.12, 0.7, 74)), tin("boat") - 0.20)          # logo slams in
    place(fx, np.stack([A2.shimmer(0.9, -27)] * 2, 1), tin("boat") - 0.15)                   # metal sheen
    place(fx, A2.whoosh(0.32, -21, 75, True), tin("boat") - 0.10)                            # through the 'o'
    # knife slash: blade "shing" (swept metallic ring) + split whoosh
    n = I(0.5); tt = np.arange(n) / SR
    ring = sum(np.sin(2 * np.pi * f0 * tt * (1 + 0.15 * tt)) * np.exp(-tt / (0.10 + 0.03 * j)) for j, f0 in enumerate((3200, 4700, 6900, 8800)))
    hiss = bq(noise(n, 81), "band", np.array([3000, 11000]), 2) * np.exp(-tt / 0.05)
    shing = (ring / 4 + 0.8 * hiss) * np.minimum(1, tt / 0.003); shing = shing / np.abs(shing).max() * db(-19)
    place(fx, np.stack([shing * np.linspace(1.3, 0.6, n), shing * np.linspace(0.6, 1.3, n)], 1), tin("photos") - 7 / E.FPS)
    place(fx, A2.whoosh(0.30, -21, 35, True), tin("photos") - 0.04)
    place(fx, stereo(A2.impact(-20, (100, 55), 0.10, 0.6, 82)), tin("photos"))
    place(fx, stereo(shutter(-19)), tin("lamp") - 0.16); place(fx, A2.whoosh(0.28, -22, 76, True), tin("lamp") - 0.14)
    place(fx, stereo(shutter(-17)), tin("lock1")); place(fx, A2.whoosh(0.28, -25, 36, True), tin("lock1") + 0.08)
    for n in ("lock2", "lock3", "lock4"):
        place(fx, stereo(A2.impact(-22, (120, 70), 0.06, 0.7, 50 + len(n))), tin(n))
    place(fx, A2.whoosh(0.30, -22, 37, True), tin("tackle") - 0.10)
    place(fx, stereo(bq(A2.glitch_burst(0.18, -23, 9), "low", 7000, 2)), tin("icecream") - 0.02)   # datamosh
    place(fx, A2.whoosh(0.26, -23, 38, False), tin("fingergun") - 0.05)                      # split slam
    place(fx, stereo(A2.impact(-18, (90, 45), 0.2, 0.4, 61)), E.s2e(18.42))                 # BULLETS
    place(fx, stereo(A2.impact(-16, (80, 40), 0.3, 0.45, 62)), E.s2e(27.74))                 # CAUGHT
    place(fx, A2.whoosh(0.40, -24, 39, False), E.T_STOP - 0.05)                             # freeze
    place(fx, stereo(drone(E.DUR - E.T_STOP + 0.85, -32)[I(0.80):]), E.T_STOP)
    pk = A2.whoosh(0.55, -21, 77, True); place(fx, pk[::-1].copy(), E.DUR - 0.55)            # into the pupil -> loops
    fx = np.tanh(fx * 1.3) / 1.3
    # duck music under the drop impact
    duck = np.ones(N + PRE, np.float32); i0 = I(D) + PRE; n = I(0.35)
    duck[i0:i0 + n] = 1 - (1 - db(-3)) * np.exp(-np.arange(n) / (0.15 * SR))
    full = dia + mus * duck[:, None] + fx
    lead, mix = full[:PRE].copy(), full[PRE:].copy()
    # circular seam: the last PRE samples crossfade into the lead-in of edit 0, so sample N-1 flows into sample 0
    th = np.linspace(0, np.pi / 2, PRE)[:, None]                 # constant-power (signals are uncorrelated)
    mix[-PRE:] = mix[-PRE:] * np.cos(th) + lead * np.sin(th)
    # (no edge fades: the end and start are matched so the TikTok loop is continuous)
    raw = f"{AD}/mix_raw.wav"; wf.write(raw, SR, mix.astype(np.float32))
    Iraw, _ = measure(raw); gain = -13.0 - Iraw
    out = f"{AD}/mix.wav"
    # master a circularly padded copy (1 s of tail before, 1 s of head after) so the limiter/resampler
    # are already settled at both ends of the loop, then trim back to exactly N samples
    P2 = SR; wrapped = np.vstack([mix[-P2:], mix, mix[:P2]])
    rawp = f"{AD}/mix_raw_wrapped.wav"; wf.write(rawp, SR, wrapped.astype(np.float32))
    tmp = f"{AD}/mix_wrapped_master.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", rawp, "-af", f"volume={gain:.2f}dB,aresample=192000,"
                    f"alimiter=limit={db(-3.0):.4f}:attack=3:release=60:level=disabled,aresample=48000:resampler=soxr",
                    "-c:a", "pcm_f32le", tmp], check=True)
    sr_, mw = wf.read(tmp); mw = mw.astype(np.float32)
    # locate the trim point by cross-correlating against the unmastered signal (filters add a small delay)
    ref = wrapped[P2:P2 + SR, 0]; seg_ = mw[P2 - 2000:P2 + SR + 2000, 0]
    lag = int(np.argmax(np.correlate(seg_, ref, mode="valid"))) - 2000
    m = mw[P2 + lag:P2 + lag + N]
    wf.write(out, SR, (np.clip(m, -1, 1) * (2 ** 31 - 1)).astype(np.int32))
    pre = m[-1024:].copy()                                  # AAC encoder pre-roll = the loop's own tail
    wf.write(f"{AD}/mix_preroll.wav", SR, np.vstack([pre, m]).astype(np.float32))
    test = f"{AD}/aac_test.m4a"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-itsoffset", str(-1024 / SR), "-i", f"{AD}/mix_preroll.wav", "-c:a", "aac", "-b:a", "256k", test], check=True)
    I2, TP2 = measure(out); I3, TP3 = measure(test)
    print(f"raw {Iraw:.1f} -> gain {gain:+.1f} -> wav {I2:.1f} LUFS/{TP2:.1f} dBTP; AAC {I3:.1f} LUFS/{TP3:.1f} dBTP")
    mm = m.mean(1)
    for lab, a, b in (("dialogue", 0, E.T_SONG), ("build", E.T_SONG, D), ("montage", D, E.T_STOP), ("outro line", 22.70, 24.62), ("loop seam", E.DUR - 0.3, E.DUR)):
        x = mm[I(a):I(b)]; print(f"  {lab:11s} {20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9):6.1f} dBFS RMS")

if __name__ == "__main__":
    main()
