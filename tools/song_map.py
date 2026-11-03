"""Map a song for editing: half-beat grid, per-bar energy (low / high band), drops, and candidate edit windows.

Usage:  python3 tools/song_map.py SONG.mp3 [OUT_DIR] [--bpm 90]
Writes: OUT_DIR/song_map.json  {P (half-beat s), off (s), bpm, bars: [{bar, h, t, rms, low, high}], drops, windows}
Prints: bar table + the strongest section changes (where the full mix / bass comes back) + 20-27 s windows that are a
        whole number of bars and put a drop near 35-45 % of the edit (cold open -> drop -> montage -> ending).
"""
import sys, os, json, subprocess
import numpy as np, scipy.signal as ss

src = sys.argv[1]; out_dir = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "."
bpm_hint = float(sys.argv[sys.argv.index("--bpm") + 1]) if "--bpm" in sys.argv else None
SR = 22050; HOP = 256
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
x = np.frombuffer(raw, np.float32).copy(); dur = len(x) / SR

# ---- onset envelope (spectral flux)
f, t, Z = ss.stft(x, SR, nperseg=1024, noverlap=1024 - HOP); M = np.log1p(np.abs(Z) * 10)
flux = np.maximum(0, np.diff(M, axis=1)).sum(0); flux = flux - ss.medfilt(flux, 31); flux = np.maximum(flux, 0)
fps = SR / HOP; env = flux / (flux.std() + 1e-9)

# ---- tempo: autocorrelation peak in 70-180 BPM (beats), then refine the half-beat period + phase by comb fit
ac = np.correlate(env, env, "full")[len(env) - 1:]
lags = np.arange(len(ac)) / fps; ok = (lags > 60 / 180) & (lags < 60 / 70)
beat = lags[ok][np.argmax(ac[ok])] if bpm_hint is None else 60 / bpm_hint
best = (-1, 0, 0)
for P in np.linspace(beat / 2 * 0.985, beat / 2 * 1.015, 121):
    for off in np.linspace(0, P, 40, endpoint=False):
        idx = np.round((off + np.arange(0, dur - off, P)) * fps).astype(int); idx = idx[idx < len(env)]
        sc = env[idx].mean()
        if sc > best[0]: best = (sc, P, off)
_, P, off = best; bpm = 60 / (2 * P)

# ---- per-bar energy (4/4: one bar = 8 half-beats)
def band(lo, hi):
    sos = ss.butter(4, [lo / (SR / 2), min(0.99, hi / (SR / 2))], "band", output="sos"); return ss.sosfilt(sos, x)
lowx, highx = band(30, 150), band(4000, 10000)
bars = []; h = 0
while off + (h + 8) * P <= dur:
    a, b = int((off + h * P) * SR), int((off + (h + 8) * P) * SR)
    db = lambda s: float(20 * np.log10(np.sqrt(np.mean(s[a:b] ** 2)) + 1e-9))
    bars.append(dict(bar=h // 8, h=h, t=round(float(off + h * P), 2), rms=round(db(x), 1), low=round(db(lowx), 1), high=round(db(highx), 1))); h += 8
for i, br in enumerate(bars):
    p = bars[i - 1] if i else br
    br["jump"] = round(max(br["high"] - p["high"], br["low"] - p["low"], br["rms"] - p["rms"]), 1)
drops = sorted([b_ for b_ in bars if b_["jump"] >= 5], key=lambda q: -q["jump"])[:8]

# ---- candidate windows: whole bars, 20-27 s, drop at 35-45 % of the edit
wins = []
for d in drops:
    for nb in range(int(np.ceil(20 / (8 * P))), int(27.5 // (8 * P)) + 1):      # every whole-bar length that gives 20-27.5 s
        L = nb * 8 * P
        if not 20 <= L <= 27.5: continue
        for pre in range(2, nb):
            if 0.33 <= pre * 8 * P / L <= 0.47:
                h0 = d["h"] - pre * 8
                if h0 >= 0: wins.append(dict(h0=h0, h1=h0 + nb * 8, drop_h=d["h"], song_in=round(off + h0 * P, 3), dur=round(L, 2), drop_at=round(pre * 8 * P, 2), jump=d["jump"]))
wins.sort(key=lambda w: (-w["jump"], abs(w["dur"] - 25)))

print(f"tempo {bpm:.2f} BPM | half-beat P={P:.5f} s | offset {off:.4f} s | {len(bars)} bars | {dur:.1f} s")
print(" bar     t    rms   low  high  jump")
for b_ in bars: print(f"{b_['bar']:4d} {b_['t']:6.2f} {b_['rms']:6.1f} {b_['low']:5.1f} {b_['high']:5.1f} {b_['jump']:5.1f}{'  <-- section change' if b_['jump'] >= 5 else ''}")
print("\nbiggest section changes (bar, time, jump dB):", [(d['bar'], d['t'], d['jump']) for d in drops])
print("candidate windows (H0 -> H1 half-beats, song in, duration, drop at):")
for w in wins[:8]: print(f"  h{w['h0']}->h{w['h1']}  in {w['song_in']:7.2f}s  dur {w['dur']:5.2f}s  drop h{w['drop_h']} at {w['drop_at']:5.2f}s  (jump {w['jump']} dB)")
os.makedirs(out_dir, exist_ok=True)
json.dump(dict(P=float(P), off=float(off), bpm=float(bpm), bars=bars, drops=drops, windows=wins[:12]), open(f"{out_dir}/song_map.json", "w"), indent=1)
