"""QC on an encoded v2 export: cuts vs EDL, frozen runs, black runs, frame sheets around key moments.
Usage: python3 v2/work/qc2.py video.mp4 TAG"""
import os, sys, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edl2 as E
path, tag = sys.argv[1], sys.argv[2]
cap = cv2.VideoCapture(path); fr = []
while True:
    ok, f = cap.read()
    if not ok: break
    h, w = f.shape[:2]
    fr.append(cv2.resize(f, (480, int(480 * h / w)), interpolation=cv2.INTER_AREA))   # keep memory small
n = len(fr)
sm = [cv2.cvtColor(cv2.resize(f, (160, 90), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(np.float32) for f in fr]
d = np.array([0] + [np.mean(np.abs(sm[i] - sm[i - 1])) for i in range(1, n)])
lum = np.array([s.mean() for s in sm])
print(f"frames {n} (expected {E.DUR_F}), size {w}x{h}")
cuts = [E.fe(c["e0"]) for c in E.CLIPS][1:]
med = np.array([np.median(d[max(1, k - 8):k + 8]) for k in range(n)])
found = [k for k in range(1, n) if d[k] > max(8, 2.5 * med[k])]
miss = [c for c in cuts if not any(abs(k - c) <= 1 for k in found)]
print("intended cuts:", cuts); print("not re-detected (+/-1):", miss)
runs, r = [], 0
for k in range(1, n):
    if d[k] < 0.05: r += 1
    else:
        if r >= 4: runs.append((k - r, r))
        r = 0
print("frozen runs >=4 (start,len):", runs)
blk = [k for k in range(n) if lum[k] < 4]
print("black frames:", len(blk), "->", blk[:12], "...", blk[-6:] if blk else "")
def sheet(name, ks, cols=8, tw=240):
    th = int(tw * h / w); ims = []
    for k in ks:
        im = cv2.resize(fr[min(k, n - 1)], (tw, th), interpolation=cv2.INTER_AREA)
        cv2.putText(im, str(k), (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 255), 1, cv2.LINE_AA); ims.append(im)
    while len(ims) % cols: ims.append(np.zeros_like(ims[0]))
    cv2.imwrite(f"{E.ROOT}/v2/frames/{tag}_{name}.jpg", np.vstack([np.hstack(ims[i:i + cols]) for i in range(0, len(ims), cols)]),
                [cv2.IMWRITE_JPEG_QUALITY, 85])
D = E.fe(32)
sheet("drop", range(D - 10, D + 14))
sheet("overview", list(range(0, n, 24)), cols=9, tw=210)
sheet("whip_slab", list(range(E.fe(38) - 6, E.fe(38) + 6)) + list(range(E.fe(48) - 6, E.fe(48) + 6)))
sheet("page_end", list(range(E.fe(70) - 2, E.fe(72) + 6, 2)) + list(range(E.fe(78), E.fe(80) + 8, 2)))
sheet("logo", list(range(E.fe(80), E.fe(88), 6)))
