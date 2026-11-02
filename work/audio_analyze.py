"""Song map: band energies, onsets, tempo/beat grid, sections, self-similarity.

Usage: python3 work/audio_analyze.py audio/song_mono22k.wav
Writes work/song_map.json and frames/song_*.png diagnostic plots.
"""
import sys, json, os
import numpy as np, scipy.io.wavfile as wf, scipy.signal as ss
import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
sr, x = wf.read(sys.argv[1] if len(sys.argv) > 1 else "audio/song_mono22k.wav")
x = x.astype(np.float32) / 32768.0
N = 2048; H = 256                       # ~11.6 ms hop
f, t, Z = ss.stft(x, sr, nperseg=N, noverlap=N - H, boundary=None)
M = np.abs(Z)
logM = np.log1p(100 * M)
flux = np.maximum(0, np.diff(logM, axis=1))
def band(lo, hi):
    k = (f >= lo) & (f < hi)
    return k
bands = dict(sub=(20, 90), low=(90, 250), mid=(250, 2000), high=(2000, 11000))
energy = {b: 20 * np.log10(np.sqrt((M[band(*r)] ** 2).mean(0)) + 1e-9) for b, r in bands.items()}
onset = {b: np.concatenate([[0], flux[band(*r)].sum(0)]) for b, r in bands.items()}
on_all = np.concatenate([[0], flux.sum(0)])
fr = sr / H
tt = np.arange(len(on_all)) / fr

def norm(v):
    v = v - ss.medfilt(v, 31)
    v = np.maximum(v, 0)
    return v / (np.percentile(v, 99.5) + 1e-9)

env = norm(on_all)
# tempo via autocorrelation of onset envelope (40-200 BPM)
ac = np.correlate(env, env, mode="full")[len(env) - 1:]
lags = np.arange(len(ac)) / fr
valid = (lags > 60 / 200) & (lags < 60 / 40)
cands = ss.find_peaks(ac * valid)[0]
cands = sorted(cands, key=lambda k: -ac[k])[:8]
print("period candidates (s, bpm, strength):")
for k in cands:
    print(f"  {lags[k]:.4f}s {60 / lags[k]:6.2f} bpm  {ac[k] / ac[0]:.3f}")

# onset peaks
pk, props = ss.find_peaks(env, height=0.25, distance=int(0.12 * fr))
onsets = tt[pk]
strength = env[pk]
sub_env = norm(onset["sub"]); low_env = norm(onset["low"])
json.dump(dict(sr=sr, fr=fr, onsets=[round(float(a), 4) for a in onsets], strength=[round(float(s), 3) for s in strength],
               sub_onsets=[round(float(tt[k]), 4) for k in ss.find_peaks(sub_env, height=0.3, distance=int(0.15 * fr))[0]],
               ),
          open("work/song_onsets.json", "w"), indent=0)

# per-0.5 s band energy table
step = int(0.5 * fr)
print("\n  t    sub   low   mid  high  onsets")
rows = []
for i in range(0, len(tt) - step, step):
    e = {b: float(np.mean(energy[b][i:i + step])) for b in bands}
    n_on = int(((onsets >= tt[i]) & (onsets < tt[i] + 0.5)).sum())
    rows.append((tt[i], e))
    print(f"{tt[i]:6.1f} {e['sub']:5.0f} {e['low']:5.0f} {e['mid']:5.0f} {e['high']:5.0f}  {'*' * n_on}")

# plot: band energy + onsets, 1 px = 25 ms
W = int(len(tt) / fr / 0.025) + 1; Hh = 600
img = np.full((Hh, W, 3), 18, np.uint8)
cols = dict(sub=(60, 60, 255), low=(60, 200, 255), mid=(80, 255, 80), high=(255, 180, 80))
for bi, (b, c) in enumerate(cols.items()):
    e = energy[b]; xs = (tt / 0.025).astype(int)
    lo, hi = np.percentile(e, 2), np.percentile(e, 99.5)
    ys = (Hh * 0.55 - (e - lo) / (hi - lo + 1e-9) * Hh * 0.5).astype(int)
    pts = np.stack([xs, ys], 1)[::2].reshape(-1, 1, 2)
    cv2.polylines(img, [pts], False, c, 1, cv2.LINE_AA)
for a, s in zip(onsets, strength):
    xx = int(a / 0.025); cv2.line(img, (xx, Hh - 10), (xx, Hh - 10 - int(min(1.5, s) * 120)), (230, 230, 230), 1)
for sec in range(0, int(tt[-1]) + 1):
    xx = int(sec / 0.025)
    cv2.line(img, (xx, 0), (xx, 8 if sec % 5 else 20), (120, 120, 120), 1)
    if sec % 5 == 0:
        cv2.putText(img, f"{sec}", (xx + 2, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)
# split into 4 strips for readability
strips = np.array_split(img, 4, axis=1)
wmax = max(s.shape[1] for s in strips)
strips = [np.pad(s, ((0, 0), (0, wmax - s.shape[1]), (0, 0))) for s in strips]
cv2.imwrite("frames/song_map.png", np.vstack(strips))
np.save("work/song_env.npy", np.stack([tt, env, sub_env, low_env, energy['sub'], energy['low'], energy['mid'], energy['high']]))
print("saved")
