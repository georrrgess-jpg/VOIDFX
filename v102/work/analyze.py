"""Footage analysis: cadence, shot detection, per-shot stats, contact sheets.

Usage: python3 work/analyze.py src/scenepack.mp4
Writes: work/shots.json, work/diffs.npy, frames/sheet_XX.jpg
"""
import cv2, json, sys, os
import numpy as np

SRC = sys.argv[1]; TAG = sys.argv[2]
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

cap = cv2.VideoCapture(SRC)
fps = cap.get(cv2.CAP_PROP_FPS)
n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

small = []      # 96x58 gray for diffs
luma = []       # mean luma
hist = []       # coarse colour hist for cut confirmation
prev = None
diffs = []
i = 0
while True:
    ok, f = cap.read()
    if not ok:
        break
    s = cv2.resize(f, (96, 58), interpolation=cv2.INTER_AREA)
    g = cv2.cvtColor(s, cv2.COLOR_BGR2GRAY).astype(np.float32)
    hsv = cv2.cvtColor(s, cv2.COLOR_BGR2HSV)
    h = cv2.calcHist([hsv], [0, 1, 2], None, [8, 4, 4], [0, 180, 0, 256, 0, 256]).flatten()
    h /= h.sum() + 1e-9
    luma.append(float(g.mean()))
    if prev is not None:
        diffs.append(float(np.mean(np.abs(g - prev[0]))))
        hist.append(float(0.5 * np.abs(h - prev[1]).sum()))
    else:
        diffs.append(0.0); hist.append(0.0)
    prev = (g, h)
    i += 1
cap.release()
n = i
d = np.array(diffs); hd = np.array(hist); L = np.array(luma)
np.save(f"v102/work/diffs_{TAG}.npy", np.stack([d, hd, L]))

# cadence: near-repeat frames
rep = (d[1:] < 0.6).mean()
print(f"frames={n} fps={fps:.3f} size={W}x{H} near-repeat ratio={rep:.3f}")

# cut detection: big diff relative to local median AND histogram change
cuts = [0]
med = np.array([np.median(d[max(1, k - 15):k + 15]) for k in range(n)])
for k in range(1, n):
    if d[k] > max(14.0, 4.0 * med[k]) and hd[k] > 0.25:
        if k - cuts[-1] >= 6:
            cuts.append(k)
        elif d[k] > d[cuts[-1]]:
            cuts[-1] = k
cuts.append(n)

shots = []
for si in range(len(cuts) - 1):
    a, b = cuts[si], cuts[si + 1]  # [a, b)
    seg = d[a + 1:b] if b - a > 1 else np.array([0.0])
    shots.append(dict(id=si, start=a, end=b - 1, t0=round(a / fps, 3), t1=round((b - 1) / fps, 3),
                      dur=round((b - a) / fps, 3), luma=round(float(L[a:b].mean()), 1),
                      motion=round(float(np.mean(seg)), 2),
                      repeat=round(float((seg < 0.6).mean()), 2)))
json.dump(dict(src=SRC, fps=fps, n=n, W=W, H=H, shots=shots), open(f"v102/work/shots_{TAG}.json", "w"), indent=1)
print(f"shots={len(shots)}")
blacks = [s["id"] for s in shots if s["luma"] < 12]
print("very dark shots:", blacks)

# contact sheets: 10 shots per sheet, 3 thumbs each (15/50/85%)
cap = cv2.VideoCapture(SRC)
TW, TH = 320, 192
os.makedirs("frames", exist_ok=True)
font = cv2.FONT_HERSHEY_SIMPLEX
def grab(k):
    cap.set(cv2.CAP_PROP_POS_FRAMES, k)
    ok, f = cap.read()
    return f if ok else np.zeros((H, W, 3), np.uint8)
per = 10
for sh0 in range(0, len(shots), per):
    rows = []
    for s in shots[sh0:sh0 + per]:
        thumbs = []
        for p in (0.15, 0.5, 0.85):
            k = int(s["start"] + p * (s["end"] - s["start"]))
            t = cv2.resize(grab(k), (TW, TH), interpolation=cv2.INTER_AREA)
            cv2.putText(t, f"{k/fps:.2f}s", (4, TH - 6), font, 0.45, (0, 255, 255), 1, cv2.LINE_AA)
            thumbs.append(t)
        lab = np.zeros((TH, 150, 3), np.uint8)
        cv2.putText(lab, f"#{s['id']}", (6, 34), font, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(lab, f"{s['t0']:.2f}-{s['t1']:.2f}", (6, 66), font, 0.45, (200, 200, 200), 1, cv2.LINE_AA)
        cv2.putText(lab, f"dur {s['dur']:.2f}s", (6, 90), font, 0.45, (200, 200, 200), 1, cv2.LINE_AA)
        cv2.putText(lab, f"mot {s['motion']} L{s['luma']:.0f}", (6, 114), font, 0.42, (160, 160, 160), 1, cv2.LINE_AA)
        rows.append(np.hstack([lab] + thumbs))
    while len(rows) < per:
        rows.append(np.zeros_like(rows[0]))
    sheet = np.vstack(rows)
    cv2.imwrite(f"v102/frames/{TAG}_sheet_{sh0 // per:02d}.jpg", sheet, [cv2.IMWRITE_JPEG_QUALITY, 85])
print("sheets written")
