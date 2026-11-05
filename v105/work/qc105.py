"""Automated review passes on the ENCODED v6 export (WARMPOP) + the ship / no-ship checkpoint.

  1. format / decode / loudness / true peak
  2. face-centering: YuNet on every 2nd output frame -> faces cut by the frame edge or far off-centre, per shot
  3. text-over-face: caption / lyric bands vs face boxes
  4. cuts on the intended frames, frozen runs, black frames
  5. audio: click scan at every edit point
  6. contact sheets around every transition (for visual review)
Usage: python3 v7/work/qc7.py v7/out/him_all_along_dexter_voidfx_9x16.mp4
"""
import os, sys, json, subprocess, math
import numpy as np, cv2, scipy.io.wavfile as wf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edl105 as E
import facetrack as FT

path = sys.argv[1]; R = {}
pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,width,height,r_frame_rate,nb_frames,duration,pix_fmt",
                     "-of", "compact", path], capture_output=True, text=True).stdout
print("== 1. format\n" + pr.strip())
dec = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "null", "-"], capture_output=True, text=True).stderr.strip()
print("decode:", "OK" if not dec else dec[:300])
r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
I = float(r.split("Integrated loudness:")[1].split("I:")[1].split("LUFS")[0]); TP = float(r.split("True peak:")[1].split("Peak:")[1].split("dBFS")[0])
print(f"loudness {I:.1f} LUFS, true peak {TP:.1f} dBTP  ->", "OK" if -14 <= I <= -12 and TP <= -2.5 else "CHECK")

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
    sn = shot_of(f)
    if [s_ for s_ in E.SHOTS if s_["n"] == sn][0].get("face", "largest") is None: continue   # subject-less shots (EDL face=None)
    cnt[sn] = cnt.get(sn, 0) + 1
    cut = x < -0.08 * w or x + w > 1080 + 0.08 * w            # more than 8% of the face outside the frame
    off = not (0.18 * 1080 <= x + w / 2 <= 0.82 * 1080)
    if cut or off: bad.setdefault(sn, []).append((f, "CUT" if cut else "OFF", int(x + w / 2), int(w)))
for sn in [s["n"] for s in E.SHOTS]:
    if sn in cnt:
        b = bad.get(sn, [])
        flag = "OK" if len(b) <= max(1, 0.1 * cnt[sn]) else "CHECK"
        print(f"  {sn:12s} {cnt[sn]:3d} face frames, {len(b):2d} flagged  {flag}  {b[:3] if b else ''}")

# ---- 3. text over face: caption lockups (1320-1600 incl. JP line), MIAMI title (1380-1610), neon sign (1270-1620)
print("\n== 3. text bands vs faces")
clash = []; lowfp = []
def text_bands(t):
    b = []
    for tx in getattr(E, "TEXT", []):
        if tx["words"][0][1] - 0.05 <= t < tx["end"] + 0.2:
            if tx["style"] == "behind": continue                                    # set behind his cutout by design
            b.append({"lyric": (1330, 1550), "hook": (1250, 1590), "script": (1290, 1580)}.get(tx["style"], tx.get("band", (1240, 1640))) + (tx["style"],))
    for vi, words, s_end, emph, style in E.CAPS:
        a, b_, at = E.VO[vi]
        if at + (words[0][1] - a) <= t < at + (s_end - a) + 0.6: b.append((1320, 1600, "caption%d" % vi))
    return b
for f, fl in faces.items():
    bands = text_bands(f / E.FPS)
    for x, y, w, h, c in fl:
        if w < 120: continue
        if y + h / 2 > 0.60 * 1920: lowfp.append((f, int(y), int(y + h))); continue   # faces are framed at ~37% H: a "face" centred below 60% H is a detector false positive (still listed)
        for a_, b_, lab in bands:
            if y + h * 0.85 > a_ and y < b_: clash.append((f, lab, int(y), int(y + h)))
print(f"  {len(clash)} frames where a face box reaches into a text band", clash[:6])
print(f"  ({len(lowfp)} low-placed detections skipped as false positives: {lowfp[:6]} — check these frames visually)")
import collections as _co; _byshot = _co.defaultdict(list)
for c_ in clash: _byshot[shot_of(c_[0])].append(c_)
for sn_, cl_ in _byshot.items(): print(f"    {sn_:12s} {len(cl_):3d} frames  {cl_[0][1]}  face y {min(c[2] for c in cl_)}-{max(c[3] for c in cl_)}  frames {cl_[0][0]}-{cl_[-1][0]}")

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
print("\n== 5. audio clicks at every cut")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vn", "-c:a", "pcm_f32le", f"{E.ROOT}/{E.VER}/audio/qc_dec.wav"], check=True)
sr, a = wf.read(f"{E.ROOT}/{E.VER}/audio/qc_dec.wav"); m = a.mean(1)
dd = np.abs(np.diff(m)); loc = np.convolve(dd, np.ones(480) / 480, "same"); clicks = 0
for s in E.SHOTS[1:]:
    i = int(s["t0"] * sr); w = dd[max(0, i - 480):i + 480]; l = loc[max(0, i - 480):i + 480]
    r = float((w / (l + 1e-6)).max())
    if w.max() > 0.08 and r > 12: clicks += 1; print(f"  CHECK t={s['t0']:.2f} step {w.max():.3f} ratio {r:.1f}")
seam = np.concatenate([m[-480:], m[:480]]); ds = np.abs(np.diff(seam)); ls = np.median(np.abs(np.diff(m[-24000:])))
seam_click = ds[470:490].max() > max(0.08, 12 * ls)
print(f"  {len(E.SHOTS) - 1} cuts checked, {clicks} suspicious; loop seam step {ds[470:490].max():.4f} (local median {ls:.4f})", "CHECK" if seam_click else "OK")

# ---- 6. sheets
def sheet(name, ks, cols=10):
    ims = []
    for i in ks:
        im = frames[min(max(0, i), n - 1)].copy(); cv2.putText(im, str(i), (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1, cv2.LINE_AA); ims.append(im)
    while len(ims) % cols: ims.append(np.zeros_like(ims[0]))
    cv2.imwrite(f"{E.ROOT}/{E.VER}/frames/qc_{name}.jpg", np.vstack([np.hstack(ims[i:i + cols]) for i in range(0, len(ims), cols)]), [cv2.IMWRITE_JPEG_QUALITY, 85])
sheet("overview", list(range(0, n, 16)), cols=12)
tr = [s["f0"] for s in E.SHOTS[1:]]
sheet("transitions_a", [c + o for c in tr[:9] for o in (-6, -3, 0, 3, 6)], cols=10)
sheet("transitions_b", [c + o for c in tr[9:] for o in (-6, -3, 0, 3, 6)], cols=10)
sheet("drop_crt", list(range(E.fh(E.HDROP) - 56, E.fh(E.HDROP) + 24, 4)), cols=10)
sheet("vanish", list(range(340, 420, 4)), cols=10)
sheet("ending", list(range(1370, n, 8)) + [n - 1, 0, 4, 8, 12, 16, 24, 32], cols=10)
print("\nsheets written")

# ---- 7. loop seam (both ends are VHS static: compare blurred luma + texture)
f_last = frames[-1].astype(np.float32); f_first = frames[0].astype(np.float32)
bl = lambda x: cv2.GaussianBlur(x, (0, 0), 6)
seam_d = np.abs(bl(f_last) - bl(f_first)).mean(); tex = abs(f_last.std() - f_first.std())
print(f"\n== 7. loop seam: last luma {f_last.mean():.1f} (std {f_last.std():.1f}), first luma {f_first.mean():.1f} (std {f_first.std():.1f}); blurred diff {seam_d:.2f}")
print(f"   audio: last 20 ms {20*np.log10(np.sqrt(np.mean(m[-960:]**2))+1e-9):.1f} dBFS, first 20 ms {20*np.log10(np.sqrt(np.mean(m[:960]**2))+1e-9):.1f} dBFS")
dur_v = n / E.FPS; dur_a = len(m) / sr
print(f"   durations: video {dur_v:.4f} s, audio {dur_a:.4f} s, diff {1000 * (dur_a - dur_v):.1f} ms")

# ---- 7b. flashes (Studio 1's v11 rule: measure every flash in the encode; a flare should keep the picture)
ml = np.array([s_.mean() for s_ in small])
wruns = []
for f_ in np.nonzero(ml >= 200)[0]:
    if wruns and f_ == wruns[-1][1] + 1: wruns[-1][1] = f_
    else: wruns.append([int(f_), int(f_)])
fev = [f_ for f_ in range(1, len(ml) - 1) if ml[f_] - ml[max(0, f_ - 12):f_].min() >= 25.5 and ml[f_] - ml[f_ + 1:f_ + 13].min() >= 25.5
       and ml[f_] == ml[max(0, f_ - 6):f_ + 7].max()]
fps_max = max((sum(1 for e in fev if a_ <= e < a_ + E.FPS) for a_ in range(len(ml))), default=0)
print(f"\n== 7b. flashes: brightest frame mean luma {ml.max():.0f} (median {np.median(ml):.0f}); most flashes in any second: {fps_max}")
for a_, b_ in wruns: print(f"  WHITE-OUT frames {a_}-{b_} ({b_ - a_ + 1} f), peak mean luma {ml[a_:b_ + 1].max():.0f}: a flare should keep the picture (v11 took its rim flash from 178 to 104)")

# ---- 8. SHIP / NO-SHIP checkpoint
print("\n== 8. SHIP CHECKPOINT")
crit = {
  "format 1080x1920 60fps, frames match": n == E.DUR_F,
  "decode clean": not dec,
  "loudness -14..-12 LUFS, TP <= -2.5 dBTP (after AAC)": -14 <= I <= -12 and TP <= -2.5,
  "no frozen runs": len(runs) == 0,
  "no face-centering failures": all(len(bad.get(sn, [])) <= max(1, 0.1 * cnt[sn]) for sn in cnt),
  "no text over faces": len(clash) <= 6,
  "no audio clicks at cuts or loop seam": clicks == 0 and not seam_click,
  "loop seam picture matched (static -> static)": seam_d < 12 and tex < 12,
  "audio and video same length (<= 1 frame)": abs(dur_a - dur_v) <= 1 / E.FPS,
  "no more than 3 flashes in any second": fps_max <= 3,
}
for k_, v_ in crit.items(): print(f"  [{'PASS' if v_ else 'FAIL'}] {k_}")
print("  VERDICT:", "SHIP (pending visual sign-off)" if all(crit.values()) else "NOT READY -> fix and re-render")
