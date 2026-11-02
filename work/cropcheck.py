"""Framing + timing check: for every EDL shot, 5 frames (u=0,.25,.5,.75,1) showing the
source with the 9:16 crop box and the resulting vertical crop.

Usage: python3 work/cropcheck.py [shot_name ...]   -> frames/cropcheck_XX.jpg
"""
import cv2, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edl

def ease(u):
    return u * u * (3 - 2 * u)

def interp_keys(keys, u):
    keys = sorted(keys, key=lambda k: k[0])
    if u <= keys[0][0]:
        return keys[0][1:]
    for k0, k1 in zip(keys, keys[1:]):
        if u <= k1[0]:
            v = ease((u - k0[0]) / max(1e-9, k1[0] - k0[0]))
            return tuple(a + (b - a) * v for a, b in zip(k0[1:], k1[1:]))
    return keys[-1][1:]

def crop_rect(s, u):
    cx, cy, h = interp_keys(s["crop"], u)
    z = interp_keys(s["zoom"], u)[0]
    h = h / z; w = h * 9 / 16
    cx = min(max(cx, w / 2), 1200 - w / 2); cy = min(max(cy, h / 2), 720 - h / 2)
    return cx, cy, w, h

if __name__ == "__main__":
    names = sys.argv[1:]
    cap = cv2.VideoCapture(edl.SRC)
    rows = []
    shots = [s for s in edl.SHOTS if not names or s["name"] in names]
    for s in shots:
        cells = []
        for u in (0, 0.25, 0.5, 0.75, 1.0):
            t = s["a"] + (s["b"] - s["a"]) * u
            k = int(round(t * 60)); k = min(k, int(round(s["b"] * 60)) - 1) if u == 1.0 else k
            cap.set(cv2.CAP_PROP_POS_FRAMES, k); ok, f = cap.read()
            cx, cy, w, h = crop_rect(s, u)
            x0, y0 = int(cx - w / 2), int(cy - h / 2)
            vert = cv2.resize(f[y0:y0 + int(h), x0:x0 + int(w)], (135, 240), interpolation=cv2.INTER_AREA)
            src = f.copy()
            cv2.rectangle(src, (x0, y0), (x0 + int(w), y0 + int(h)), (0, 255, 255), 3)
            fx, fy, fr = s["face"]
            cv2.circle(src, (fx, fy), fr, (0, 0, 255), 2)
            for gx in range(0, 1200, 100):
                cv2.line(src, (gx, 0), (gx, 12), (255, 255, 255), 2)
                cv2.putText(src, str(gx), (gx + 2, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            src = cv2.resize(src, (400, 240), interpolation=cv2.INTER_AREA)
            cv2.putText(src, f"{t:.2f}", (4, 232), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
            cells.append(np.hstack([src, vert]))
        row = np.hstack(cells)
        lab = np.zeros((26, row.shape[1], 3), np.uint8)
        cv2.putText(lab, f"{s['name']}  #{s['pack']}  {s['role'][:90]}", (6, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
        rows.append(np.vstack([lab, row]))
    for i in range(0, len(rows), 6):
        cv2.imwrite(f"frames/cropcheck_{i // 6:02d}.jpg", np.vstack(rows[i:i + 6]), [cv2.IMWRITE_JPEG_QUALITY, 82])
    print("written", (len(rows) + 5) // 6, "sheets")
