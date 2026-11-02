"""QC on an ENCODED export: cut re-detection vs the EDL, frozen runs, black frames,
frame-by-frame sheets around the key moments, loop seam difference.

Usage: python3 work/qc.py path/to/video.mp4 [tag]
"""
import os, sys, json
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edl

path = sys.argv[1]; tag = sys.argv[2] if len(sys.argv) > 2 else "qc"
cap = cv2.VideoCapture(path)
frames = []
while True:
    ok, f = cap.read()
    if not ok:
        break
    frames.append(f)
n = len(frames)
small = [cv2.cvtColor(cv2.resize(f, (90, 160), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(np.float32) for f in frames]
d = np.array([0] + [np.mean(np.abs(small[i] - small[i - 1])) for i in range(1, n)])
print(f"frames decoded: {n} (expected {edl.DUR_FRAMES})")

# intended cuts
intended = [f0 for f0, _, _ in edl.timeline()][1:]
med = np.array([np.median(d[max(1, k - 8):k + 8]) for k in range(n)])
found = [k for k in range(1, n) if d[k] > max(10, 3.5 * med[k])]
print("intended cuts:", intended)
miss = []
for c in intended:
    near = [k for k in found if abs(k - c) <= 1]
    if not near:
        miss.append(c)
print("cuts not re-detected within +/-1 frame:", miss, "(low-contrast cuts can be missed; check visually)")
extra = [k for k in found if all(abs(k - c) > 1 for c in intended)]
print("extra detections (effects/flash):", extra)

# frozen runs (consecutive identical frames)
runs, r = [], 0
for k in range(1, n):
    if d[k] < 0.08:
        r += 1
    else:
        if r >= 3:
            runs.append((k - r, r))
        r = 0
print("frozen runs >=3 frames (start, length):", runs)
lum = np.array([s.mean() for s in small])
print("near-black frames (<12):", [k for k in range(n) if lum[k] < 12])
# loop seam
seam = np.mean(np.abs(small[0] - small[-1]))
print(f"loop seam diff last->first: {seam:.2f}; median consecutive diff: {np.median(d[1:]):.2f}")

def sheet(name, ks, cols=8, w=180):
    h = int(w * 16 / 9)
    ims = []
    for k in ks:
        im = cv2.resize(frames[k % n], (w, h), interpolation=cv2.INTER_AREA)
        cv2.putText(im, str(k % n), (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)
        ims.append(im)
    while len(ims) % cols:
        ims.append(np.zeros_like(ims[0]))
    cv2.imwrite(f"frames/{tag}_{name}.jpg", np.vstack([np.hstack(ims[i:i + cols]) for i in range(0, len(ims), cols)]),
                [cv2.IMWRITE_JPEG_QUALITY, 85])

D = edl.fp(edl.DROP_P)
sheet("drop", range(D - 8, D + 16))
sheet("freeze", range(edl.fp(edl.FREEZE_P) - 6, edl.fp(edl.FREEZE_P) + 10))
sheet("stop", list(range(1076, 1084)) + list(range(1096, 1104)) + list(range(edl.STOP_F - 4, edl.STOP_F + 4)))
sheet("loop", list(range(n - 12, n)) + list(range(0, 12)), cols=12, w=150)
sheet("cuts", [c + o for c in intended for o in (-1, 0)], cols=10, w=150)
json.dump(dict(diffs=d.tolist()), open(f"work/{tag}_diffs.json", "w"))
