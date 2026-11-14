"""Face tracking for 9:16 reframing (YuNet).

Library use:  track(src_path, t0, t1, pick="dexter"|"largest"|"left"|"right"|(x_hint, y_hint)) ->
              dict(t=[...], cx, cy, w, h, eyes=[(lx,ly,rx,ry)], conf) per detected sample (source px),
              plus smoothed continuous functions via smooth_track().
CLI:          python3 v3/work/facetrack.py SRC t0 t1  -> prints a summary
"""
import os, sys, json, math
import numpy as np, cv2

ROOT = "/home/user/VOIDFX"
MODEL = f"{ROOT}/v3/models/face_detection_yunet_2023mar.onnx"
_DET = {}

def detector(w, h):
    k = (w, h)
    if k not in _DET:
        _DET[k] = cv2.FaceDetectorYN.create(MODEL, "", (w, h), 0.55, 0.3, 20)
    return _DET[k]

def detect(frame, scale=0.5):
    h, w = frame.shape[:2]
    sw, sh = int(w * scale), int(h * scale)
    s = cv2.resize(frame, (sw, sh), interpolation=cv2.INTER_AREA)
    # brighten dark night shots for detection only
    if s.mean() < 45:
        s = cv2.convertScaleAbs(s, alpha=2.2, beta=10)
    d = detector(sw, sh); d.setInputSize((sw, sh))
    _, faces = d.detect(s)
    out = []
    if faces is not None:
        for f in faces:
            x, y, fw, fh = f[:4] / scale
            lm = f[4:14] / scale
            out.append(dict(cx=float(x + fw / 2), cy=float(y + fh / 2), w=float(fw), h=float(fh), eyes=tuple(float(v) for v in lm[:4]), conf=float(f[14])))
    return out

def choose(faces, pick, prev=None):
    if not faces: return None
    if prev is not None:                                          # continuity first
        best = min(faces, key=lambda f: math.hypot(f["cx"] - prev["cx"], f["cy"] - prev["cy"]))
        if math.hypot(best["cx"] - prev["cx"], best["cy"] - prev["cy"]) < max(80, prev["w"] * 0.8):
            return best
    if pick == "left": return min(faces, key=lambda f: f["cx"])
    if pick == "right": return max(faces, key=lambda f: f["cx"])
    if isinstance(pick, (list, tuple)):
        return min(faces, key=lambda f: math.hypot(f["cx"] - pick[0], f["cy"] - pick[1]))
    return max(faces, key=lambda f: f["w"] * f["h"] * f["conf"])

def track(path, t0, t1, pick="largest", step=2):
    cap = cv2.VideoCapture(path); fps = cap.get(cv2.CAP_PROP_FPS)
    k0, k1 = int(t0 * fps), int(math.ceil(t1 * fps))
    cap.set(cv2.CAP_PROP_POS_FRAMES, k0)
    res = []; prev = None
    for k in range(k0, k1 + 1):
        ok, f = cap.read()
        if not ok: break
        if (k - k0) % step: continue
        c = choose(detect(f), pick, prev)
        if c is not None:
            prev = c; res.append(dict(t=k / fps, **c))
    return res

def smooth_track(res, t0, t1, n=200, sigma_s=0.12, fallback=(640, 300, 200)):
    """continuous (cx, cy, w) on a uniform time grid; gaps interpolated, ends held."""
    ts = np.linspace(t0, t1, n)
    if not res:
        return ts, np.full(n, fallback[0]), np.full(n, fallback[1]), np.full(n, fallback[2]), 0.0
    tt = np.array([r["t"] for r in res])
    out = []
    for key in ("cx", "cy", "w"):
        v = np.array([r[key] for r in res], np.float64)
        # median filter outliers
        if len(v) >= 5:
            vm = np.array([np.median(v[max(0, i - 2):i + 3]) for i in range(len(v))])
            v = np.where(np.abs(v - vm) > 0.35 * np.median([r["w"] for r in res]), vm, v)
        g = np.interp(ts, tt, v)
        dt = (t1 - t0) / (n - 1); sg = max(1, sigma_s / max(dt, 1e-6))
        k = np.exp(-0.5 * (np.arange(-3 * sg, 3 * sg + 1) / sg) ** 2); k /= k.sum()
        gp = np.pad(g, (len(k) // 2, len(k) // 2), mode="edge")
        out.append(np.convolve(gp, k, mode="valid")[:n])
    coverage = len(res) / max(1, (t1 - t0) * 30)
    return ts, out[0], out[1], out[2], coverage

if __name__ == "__main__":
    p, a, b = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
    pick = sys.argv[4] if len(sys.argv) > 4 else "largest"
    r = track(p, a, b, pick)
    print(len(r), "detections")
    for x in r[::max(1, len(r) // 10)]:
        print(f"t={x['t']:.2f} cx={x['cx']:.0f} cy={x['cy']:.0f} w={x['w']:.0f} conf={x['conf']:.2f}")
