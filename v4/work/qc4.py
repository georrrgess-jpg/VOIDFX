"""Automated review passes on the ENCODED v3 export.

  1. format / decode / loudness / true peak
  2. face-centering: YuNet on every 2nd output frame -> faces cut by the frame edge or far off-centre, per shot
  3. text-over-face: caption / lyric bands vs face boxes
  4. cuts on the intended frames, frozen runs, black frames
  5. audio: click scan at every edit point
  6. contact sheets around every transition (for visual review)
Usage: python3 v3/work/qc3.py v3/out/surprise_doakes_voidfx_9x16.mp4
"""
import os, sys, json, subprocess, math
import numpy as np, cv2, scipy.io.wavfile as wf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edl4 as E
import facetrack as FT

path = sys.argv[1]; R = {}
pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,width,height,r_frame_rate,nb_frames,duration,pix_fmt",
                     "-of", "compact", path], capture_output=True, text=True).stdout
print("== 1. format\n" + pr.strip())
dec = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "null", "-"], capture_output=True, text=True).stderr.strip()
print("decode:", "OK" if not dec else dec[:300])
r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
I = float(r.split("Integrated loudness:")[1].split("I:")[1].split("LUFS")[0]); TP = float(r.split("True peak:")[1].split("Peak:")[1].split("dBFS")[0])
print(f"loudness {I:.1f} LUFS, true peak {TP:.1f} dBTP  ->", "OK" if -15 <= I <= -11 and TP <= -1.0 else "CHECK")

cap = cv2.VideoCapture(path); frames = []; small = []
det = cv2.FaceDetectorYN.create(FT.MODEL, "", (540, 960), 0.6, 0.3, 20)
faces = {}
k = 0
while True:
    ok, f = cap.read()
    if not ok: break
    s = cv2.resize(f, (540, 960), interpolation=cv2.INTER_AREA)
    small.append(cv2.cvtColor(cv2.resize(s, (90, 160)), cv2.COLOR_BGR2GRAY).astype(np.float32))
    frames.append(cv2.resize(s, (216, 384), interpolation=cv2.INTER_AREA))
    if k % 2 == 0:
        _, fc = det.detect(s)
        faces[k] = [] if fc is None else [tuple(float(v) * 2 for v in x[:4]) + (float(x[14]),) for x in fc]
    k += 1
n = len(frames)
print(f"frames decoded {n} (expected {E.DUR_F})")

# ---- 2. face centering
print("\n== 2. face-centering (faces >= 120 px wide; frame 1080 wide)")
STARTS = [s["f0"] for s in E.SHOTS]
def shot_of(f):
    import bisect
    return E.SHOTS[bisect.bisect_right(STARTS, f) - 1]["n"]
bad = {}; cnt = {}
for f, fl in faces.items():
    big = [x for x in fl if x[2] >= 120]
    if not big: continue
    x, y, w, h, c = max(big, key=lambda q: q[2] * q[3])
    sn = shot_of(f); cnt[sn] = cnt.get(sn, 0) + 1
    cut = x < -0.08 * w or x + w > 1080 + 0.08 * w            # more than 8% of the face outside the frame
    off = not (0.18 * 1080 <= x + w / 2 <= 0.82 * 1080)
    if cut or off: bad.setdefault(sn, []).append((f, "CUT" if cut else "OFF", int(x + w / 2), int(w)))
for sn in [s["n"] for s in E.SHOTS]:
    if sn in cnt:
        b = bad.get(sn, [])
        flag = "OK" if len(b) <= max(1, 0.1 * cnt[sn]) else "CHECK"
        print(f"  {sn:12s} {cnt[sn]:3d} face frames, {len(b):2d} flagged  {flag}  {b[:3] if b else ''}")

# ---- 3. text over face (caption band ~1400-1500, lyric band 1250-1750)
print("\n== 3. text bands vs faces")
clash = []
for f, fl in faces.items():
    t = f / E.FPS; bands = []
    for di, ws, s_end, _ in E.CAPTIONS:
        if E.d2e(di, ws[0][1]) <= t < E.d2e(di, s_end) + 0.2: bands.append((1400, 1500, "caption"))
    for txt, s0, s1 in E.LYRICS:
        if E.s2e(s0) <= t < E.s2e(s1) + 0.1: bands.append((1300, 1720, "lyric:" + txt))
    for x, y, w, h, c in fl:
        if w < 120: continue
        for a_, b_, lab in bands:
            if y + h * 0.85 > a_ and y < b_: clash.append((f, lab, int(y), int(y + h)))
print(f"  {len(clash)} frames where a face box reaches into a text band", clash[:6])

# ---- 4. cuts / frozen / black
print("\n== 4. cuts, frozen, black")
d = np.array([0] + [np.mean(np.abs(small[i] - small[i - 1])) for i in range(1, n)])
cuts = [s["f0"] for s in E.SHOTS[1:]]
med = np.array([np.median(d[max(1, i - 8):i + 8]) for i in range(n)])
found = [i for i in range(1, n) if d[i] > max(7, 2.5 * med[i])]
miss = [c for c in cuts if not any(abs(i - c) <= 1 for i in found)]
print("  intended cuts:", len(cuts), " not re-detected (transition-hidden or low contrast):", miss)
runs, rr = [], 0
for i in range(1, n):
    if d[i] < 0.05: rr += 1
    else:
        if rr >= 5: runs.append((i - rr, rr))
        rr = 0
print("  frozen runs >=5 frames:", runs)
lum = np.array([x.mean() for x in small]); print("  near-black frames:", [i for i in range(n) if lum[i] < 5][:20])

# ---- 5. audio clicks at edit points
print("\n== 5. audio clicks")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vn", "-c:a", "pcm_f32le", "/home/user/VOIDFX/v4/audio/qc_dec.wav"], check=True)
sr, a = wf.read("/home/user/VOIDFX/v4/audio/qc_dec.wav"); m = a.mean(1)
dd = np.abs(np.diff(m)); loc = np.convolve(dd, np.ones(480) / 480, "same")
edits = sorted(set([E.DIALOGUE[i][2] for i in range(len(E.DIALOGUE))] + [E.DIALOGUE[i][2] + E.DIALOGUE[i][1] - E.DIALOGUE[i][0] for i in range(len(E.DIALOGUE))] + [E.T_SONG, E.T_STOP, E.DUR - 0.01]))
for t in edits:
    i = int(t * sr); w = dd[max(0, i - 480):i + 480]; l = loc[max(0, i - 480):i + 480]
    ratio = float((w / (l + 1e-6)).max()) if len(w) else 0
    print(f"  t={t:6.2f}  max step {w.max():.4f}  local ratio {ratio:5.1f}  {'OK' if w.max() < 0.08 or ratio < 12 else 'CHECK'}")

# ---- 6. sheets
def sheet(name, ks, cols=10):
    ims = []
    for i in ks:
        im = frames[min(max(0, i), n - 1)].copy(); cv2.putText(im, str(i), (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1, cv2.LINE_AA); ims.append(im)
    while len(ims) % cols: ims.append(np.zeros_like(ims[0]))
    cv2.imwrite(f"{E.ROOT}/v4/frames/qc_{name}.jpg", np.vstack([np.hstack(ims[i:i + cols]) for i in range(0, len(ims), cols)]), [cv2.IMWRITE_JPEG_QUALITY, 85])
sheet("overview", list(range(0, n, 16)), cols=12)
tr = [s["f0"] for s in E.SHOTS if s.get("tin")]
sheet("transitions_a", [c + o for c in tr[:8] for o in (-4, -2, 0, 2, 4)], cols=10)
sheet("transitions_b", [c + o for c in tr[8:] for o in (-4, -2, 0, 2, 4)], cols=10)
sheet("drop", list(range(E.fh(41) - 4, E.fh(41) + 26, 2)), cols=10)
print("\nsheets written")

# ---- 7. loop seam
f_last = frames[-1].astype(np.float32); f_first = frames[0].astype(np.float32)
print(f"\n== 7. loop seam: last-frame luma {f_last.mean():.1f}, first-frame luma {f_first.mean():.1f}, diff {np.abs(f_last - f_first).mean():.2f}")
print(f"   audio: last 20 ms {20*np.log10(np.sqrt(np.mean(m[-960:]**2))+1e-9):.1f} dBFS, first 20 ms {20*np.log10(np.sqrt(np.mean(m[:960]**2))+1e-9):.1f} dBFS")
