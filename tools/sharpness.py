"""Clip quality check (the owner's v105 note: "the quality of some of the clips"). Ranks every shot of an edit by how sharp it
will look in the 9:16 frame, so soft clips are swapped before the render, not noticed after it.

Usage:  python3 tools/sharpness.py N --src            # before rendering: the source crop of every shot in vN/work/edlN.py
        python3 tools/sharpness.py N                  # after rendering: the encoded vN/out/<slug>_voidfx_9x16.mp4

For each shot it reports:
  detail   fine detail relative to coarse structure (|L - blur 1.2| / |L - blur 8|) on the middle of the shot. It doesn't depend
           on brightness, so dark shots aren't penalised for being dark. Higher is sharper. Noise and grain raise it a little.
  upscale  how much the source crop is enlarged to fill 1080x1920 (1920 / (source height / zoom)). Every 720p pack needs about 2.8x
           at zoom 1.0; each step of zoom makes it worse.
  kbps     the pack's video bitrate. Under ~800 kb/s for 720p is heavily compressed (blocking and smeared detail).
Flags: SOFT when detail is in the bottom fifth of the edit (or, on the MP4, under 0.20; source-crop scores run lower, about 0.08-0.15,
so there only the ranking counts); ZOOM when the upscale is over 3.1x; LOWBIT when the pack
is under 800 kb/s. Fixes, in order: a sharper moment or pack for the same beat; less zoom; a shorter hold; a stronger
grade/grain (which hides softness better than sharpening).
"""
import sys, os, subprocess, json
import numpy as np, cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
n = sys.argv[1]; V = f"v{n}"; use_src = "--src" in sys.argv
sys.path.insert(0, f"{ROOT}/{V}/work")
E = __import__(f"edl{n}")

def detail(L):
    fine = np.abs(L - cv2.GaussianBlur(L, (0, 0), 1.2)).mean(); coarse = np.abs(L - cv2.GaussianBlur(L, (0, 0), 8)).mean()
    return fine / (coarse + 1e-4)

def kbps(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=bit_rate", "-of", "csv=p=0", path],
                       capture_output=True, text=True).stdout.strip()
    return int(r) / 1000 if r.isdigit() else float("nan")

def keys_at(keys, u):
    for (u0, v0), (u1, v1) in zip(keys, keys[1:]):
        if u0 <= u <= u1: return v0 + (v1 - v0) * (u - u0) / max(1e-6, u1 - u0)
    return keys[-1][1]

rows = []
if use_src:
    for s in E.SHOTS:
        path, fps, sw, sh = E.SRC[s["src"]]; vals = []
        for u in (0.35, 0.5, 0.65):
            t = keys_at(s["tmap"], u); z = keys_at(s.get("z", [(0, 1.0)]), u)
            fr = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                                capture_output=True).stdout
            if len(fr) < sw * sh: continue
            img = np.frombuffer(fr[:sw * sh], np.uint8).reshape(sh, sw).astype(np.float32) / 255
            ch = sh / z; cw = ch * 9 / 16; cx = s.get("cx", (sw / 2, sw / 2))[0] if s.get("face") is None else sw / 2
            x0 = int(max(0, min(sw - cw, cx - cw / 2))); crop = img[int((sh - ch) / 2):int((sh + ch) / 2), x0:int(x0 + cw)]
            vals.append(detail(cv2.resize(crop, (1080, 1920), interpolation=cv2.INTER_LANCZOS4)))
        z1 = max(v for _, v in s.get("z", [(0, 1.0)]))
        rows.append((s["n"], s["src"], float(np.median(vals)) if vals else float("nan"), 1920 / (sh / z1), kbps(path)))
else:
    mp4 = f"{ROOT}/{V}/out/{E.SLUG}_voidfx_9x16.mp4"; want = {}
    for s in E.SHOTS:
        L = s["f1"] - s["f0"]
        for f in range(s["f0"] + int(L * 0.35), s["f0"] + int(L * 0.65) + 1, 3): want[f] = s["n"]
    cap = cv2.VideoCapture(mp4); vals = {}; i = 0
    while True:
        ok, fr = cap.read()
        if not ok: break
        if i in want: vals.setdefault(want[i], []).append(detail(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255))
        i += 1
    for s in E.SHOTS:
        sh = E.SRC[s["src"]][3]; z1 = max(v for _, v in s.get("z", [(0, 1.0)]))
        rows.append((s["n"], s["src"], float(np.median(vals.get(s["n"], [np.nan]))), 1920 / (sh / z1), kbps(E.SRC[s["src"]][0])))

ds = np.array([r[2] for r in rows if r[2] == r[2]]); p20 = np.percentile(ds, 20) if len(ds) else 0
print(f"{V} clip quality ({'source crops' if use_src else 'encoded MP4'}), softest first\n  {'shot':12s} {'pack':5s} {'detail':>7s} {'upscale':>8s} {'kbps':>6s}  flags")
for r in sorted(rows, key=lambda r: r[2] if r[2] == r[2] else 9):
    fl = (["SOFT"] if (r[2] <= p20 or (not use_src and r[2] < 0.20)) else []) + (["ZOOM"] if r[3] > 3.1 else []) + (["LOWBIT"] if r[4] < 800 else [])
    print(f"  {r[0]:12s} {r[1]:5s} {r[2]:7.3f} {r[3]:7.2f}x {r[4]:6.0f}  {' '.join(fl)}")
json.dump([dict(shot=r[0], pack=r[1], detail=round(r[2], 3), upscale=round(r[3], 2), kbps=round(r[4])) for r in rows],
          open(f"{ROOT}/{V}/work/sharpness.json", "w"), indent=1)
