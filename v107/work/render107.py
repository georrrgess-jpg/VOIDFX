"""voidfx renderer (v8 WISH YOU WELL on the v7 engine; was: v6 engine, benchmark edit WARMPOP — Dexter × Warmpop, 1080x1920). Reads the edit's EDL only.

  python3 vN/work/renderN.py prep                    # decode + face-track every shot, MODNet mattes for seg=True shots
  python3 vN/work/renderN.py auto NAME               # review sheets around EVERY cut (no frame lists) -> vN/frames/NAME_*.jpg
  python3 vN/work/renderN.py stills NAME f1 f2 ...   # tiled stills of chosen frames -> vN/frames/NAME.jpg
  python3 vN/work/renderN.py full f1 f2 ...          # full-res stills -> vN/frames/full_XXXX.jpg
  python3 vN/work/renderN.py clip A B                # frames A..B as a 540x960 MP4 with sound (check a transition in motion)
  python3 vN/work/renderN.py preview                 # whole edit at 30 fps / 540x960 with sound (~half the final render time)
  python3 vN/work/renderN.py video OUTDIR            # final render: upload MP4 + master MOV (needs vN/audio/mix*.wav)
"""
import os, sys, json, math, bisect, subprocess
import numpy as np, cv2
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont
from scipy.interpolate import PchipInterpolator

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edl107 as E
import facetrack as FT

W, H, FPS = E.W, E.H, E.FPS
cv2.setNumThreads(1)
ROOT = E.ROOT
F_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
F_XB = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
F_BOLD = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
F_SB = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"
F_MONO = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf"
F_MONO_M = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Medium.ttf"
RED = np.array([0.16, 0.16, 0.90], np.float32)          # BGR signal red
WHITE = np.array([0.97, 0.97, 0.96], np.float32)

def clamp(v, a, b): return a if v < a else (b if v > b else v)
def smooth(u): u = clamp(u, 0.0, 1.0); return u * u * (3 - 2 * u)
def eout(u, p=3): u = clamp(u, 0.0, 1.0); return 1 - (1 - u) ** p
def ein(u, p=2): u = clamp(u, 0.0, 1.0); return u ** p
def keys_at(keys, u):
    keys = sorted(keys)
    if u <= keys[0][0]: return keys[0][1]
    for (u0, v0), (u1, v1) in zip(keys, keys[1:]):
        if u <= u1: return v0 + (v1 - v0) * smooth((u - u0) / max(1e-9, u1 - u0))
    return keys[-1][1]

SHOTS = E.SHOTS
STARTS = [s["f0"] for s in SHOTS]
def shot_at(f): return SHOTS[bisect.bisect_right(STARTS, f) - 1]
def by_name(n): return [s for s in SHOTS if s["n"] == n][0]
def prev_shot(s): i = SHOTS.index(s); return SHOTS[i - 1] if i > 0 else None

# ============================================================================ time maps
def tmap(s, u):
    if "_tm" not in s:
        ks = s["tmap"]; us = np.array([k[0] for k in ks]); ts = np.array([k[1] for k in ks])
        if len(ks) > 2 and len(set(us)) == len(us) and np.all(np.diff(ts) >= 0):
            s["_tm"] = PchipInterpolator(us, ts)
        else:
            s["_tm"] = lambda x, us=us, ts=ts: np.interp(x, us, ts)
    return float(s["_tm"](clamp(u, 0, 1)))

def src_time(s, f):
    n = max(1, s["f1"] - s["f0"]); u = (f - s["f0"]) / n
    t = tmap(s, u); du = 1.0 / n
    sp = abs(tmap(s, u + du) - tmap(s, u - du)) / ((min(u + du, 1) - max(u - du, 0)) * n / FPS + 1e-9)
    return t, u, sp

# ============================================================================ source frames
FR, UNIQ = {}, {}
def load():
    need = {}
    for s in SHOTS:
        if "src" not in s: continue
        fps = E.SRC[s["src"]][1]; ts = [k[1] for k in s["tmap"]]
        need.setdefault(s["src"], []).append((max(0, int(min(ts) * fps) - 3), int(math.ceil(max(ts) * fps)) + 3))
    for pk, rngs in need.items():
        cap = cv2.VideoCapture(E.SRC[pk][0]); rngs = sorted(rngs); merged = []
        for a, b in rngs:
            if merged and a <= merged[-1][1] + 20: merged[-1][1] = max(merged[-1][1], b)
            else: merged.append([a, b])
        for a, b in merged:
            cap.set(cv2.CAP_PROP_POS_FRAMES, a); prev = None
            for k in range(a, b + 1):
                ok, fr = cap.read()
                if not ok: break
                g = cv2.resize(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY), (160, 90), interpolation=cv2.INTER_AREA).astype(np.float32)
                if prev is None or np.mean(np.abs(g - prev)) > 0.12:     # drop exact repeats (pulldown)
                    FR[(pk, k)] = fr; UNIQ.setdefault(pk, []).append(k)
                prev = g
        UNIQ[pk] = sorted(set(UNIQ[pk]))
    print("loaded", {k: len(v) for k, v in UNIQ.items()}, flush=True)

_DIS = None
_FLOWC = {}
def flow_interp(pk, i0, i1, t):
    global _DIS
    if _DIS is None: _DIS = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    key = (pk, i0, i1)
    if key not in _FLOWC:
        g0 = cv2.cvtColor(FR[(pk, i0)], cv2.COLOR_BGR2GRAY); g1 = cv2.cvtColor(FR[(pk, i1)], cv2.COLOR_BGR2GRAY)
        _FLOWC.clear(); _FLOWC[key] = (_DIS.calc(g0, g1, None), _DIS.calc(g1, g0, None))
    F01, F10 = _FLOWC[key]
    h, w = F01.shape[:2]
    xs, ys = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    Ft0 = -(1 - t) * t * F01 + t * t * F10; Ft1 = (1 - t) * (1 - t) * F01 - t * (1 - t) * F10
    a = cv2.remap(FR[(pk, i0)], xs + Ft0[..., 0], ys + Ft0[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    b = cv2.remap(FR[(pk, i1)], xs + Ft1[..., 0], ys + Ft1[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return cv2.addWeighted(a, 1 - t, b, t, 0)

def sample(pk, ts, mode="hold"):
    fps = E.SRC[pk][1]; U = UNIQ[pk]; kf = ts * fps
    i = clamp(bisect.bisect_right(U, kf + 0.3) - 1, 0, len(U) - 1)
    if mode == "hold" or i >= len(U) - 1: return FR[(pk, U[i])]
    i0, i1 = U[i], U[i + 1]; a = clamp((kf - i0) / (i1 - i0), 0.0, 1.0)
    if a < 0.05: return FR[(pk, i0)]
    if a > 0.95: return FR[(pk, i1)]
    if mode == "blend": return cv2.addWeighted(FR[(pk, i0)], 1 - a, FR[(pk, i1)], a, 0)
    # a hard cut between the two source frames (e.g. a jump cut the shot detector missed): never interpolate across it
    d_ = np.abs(FR[(pk, i0)][::8, ::8].astype(np.float32) - FR[(pk, i1)][::8, ::8]).mean()
    if d_ > 14: return FR[(pk, i0)] if a < 0.5 else FR[(pk, i1)]
    # flow breaks on sudden lighting changes (police-light flashes): blend those pairs instead
    m0, m1 = FR[(pk, i0)][::8, ::8].mean(axis=(0, 1)), FR[(pk, i1)][::8, ::8].mean(axis=(0, 1))
    if np.abs(m0.astype(np.float32) - m1).max() > 6: return cv2.addWeighted(FR[(pk, i0)], 1 - a, FR[(pk, i1)], a, 0)
    return flow_interp(pk, i0, i1, a)

def source_img(s, f):
    t, u, sp = src_time(s, f)
    if sp > 1.7:                                                          # velocity: shutter blur
        K = int(min(7, max(3, round(sp * 2)))); span = 0.5 / FPS * sp; acc = None
        for j in range(K):
            fr = sample(s["src"], t + (j / (K - 1) - 0.5) * span).astype(np.float32)
            acc = fr if acc is None else acc + fr
        return (acc / K).astype(np.uint8), t, u
    return sample(s["src"], t, s.get("interp", "hold")), t, u

# ============================================================================ face tracks
TRK = {}
def prep_tracks():
    out = {}
    for s in SHOTS:
        if "src" not in s or s.get("face") is None: continue
        pk = s["src"]; fps = E.SRC[pk][1]
        ts = [k[1] for k in s["tmap"]]; a, b = min(ts) - 0.05, max(ts) + 0.05
        ks = [k for k in UNIQ[pk] if a * fps <= k <= b * fps]
        res, prev = [], None
        for k in ks[::max(1, len(ks) // 40)]:
            c = FT.choose(FT.detect(FR[(pk, k)]), s["face"] if s["face"] != "largest" else "largest", prev)
            if c is not None: prev = c; res.append(dict(t=k / fps, **c))
        out[s["n"]] = res
        print(f"  track {s['n']:12s} {len(res):3d} det", flush=True)
    json.dump(out, open(f"{ROOT}/{E.VER}/work/tracks{E.VER[1:]}.json", "w"))

def track_fn(s):
    n = s["n"]
    if n not in TRK:
        res = RAW_TRK.get(n, [])
        ts_ = [k[1] for k in s["tmap"]]; a, b = min(ts_) - 0.05, max(ts_) + 0.05
        if len(res) == 0:
            TRK[n] = None
        else:
            tt, cx, cy, fw, _ = FT.smooth_track(res, a, b + 1e-3, n=120, sigma_s=0.10)
            ey = np.array([[r["t"], *r["eyes"]] for r in res])
            TRK[n] = (tt, cx, cy, fw, ey)
    return TRK[n]
RAW_TRK = {}

def face_at(s, t):
    tr = track_fn(s)
    if tr is None: return None
    tt, cx, cy, fw, ey = tr
    eyes = tuple(float(np.interp(t, ey[:, 0], ey[:, i])) for i in range(1, 5))
    return float(np.interp(t, tt, cx)), float(np.interp(t, tt, cy)), float(np.interp(t, tt, fw)), eyes

# ============================================================================ person matting (MODNet)
SEG = {}
def prep_seg():
    import onnxruntime as ort
    sess = ort.InferenceSession(f"{ROOT}/v3/models/modnet/onnx/model.onnx", providers=["CPUExecutionProvider"])
    out = {}
    for s in SHOTS:
        if not s.get("seg"): continue
        pk = s["src"]; fps = E.SRC[pk][1]; ts = [k[1] for k in s["tmap"]]
        ks = [k for k in UNIQ[pk] if (min(ts) - 0.05) * fps <= k <= (max(ts) + 0.05) * fps]
        for k in ks:
            if f"{pk}_{k}" in out: continue
            img = cv2.cvtColor(FR[(pk, k)], cv2.COLOR_BGR2RGB).astype(np.float32)
            if img.mean() < 60: img = np.clip(img * 1.8, 0, 255)
            x = (cv2.resize(img, (672, 384), interpolation=cv2.INTER_AREA) - 127.5) / 127.5
            m = sess.run(None, {sess.get_inputs()[0].name: x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0, 0]
            out[f"{pk}_{k}"] = (np.clip(m, 0, 1) * 255).astype(np.uint8)
        print(f"  seg {s['n']:12s} {len(ks)} frames", flush=True)
    np.savez_compressed(f"{ROOT}/{E.VER}/work/seg{E.VER[1:]}.npz", **out)

def seg_mask(s, t):
    pk = s["src"]; fps = E.SRC[pk][1]; U = UNIQ[pk]
    i = clamp(bisect.bisect_right(U, t * fps + 0.3) - 1, 0, len(U) - 1)
    key = f"{pk}_{U[i]}"
    if key not in SEG: return np.zeros((384, 672), np.float32)
    m = SEG[key].astype(np.float32) / 255
    return cv2.GaussianBlur(m, (0, 0), 1.2)

# ============================================================================ framing
def beat_bounce(f):
    """subtle zoom pulse on every beat of the montage (1 beat = 2 half-beats)."""
    t = f / FPS
    if not (E.te(41) <= t < E.T_STOP): return 1.0
    h = (t - E.te(0)) / (E.HB) ; ph = (h % 2) * E.HB
    return 1 + 0.018 * math.exp(-ph / 0.09)

HITS = []      # (frame, amp px, tau frames)
def shake(f):
    dx = dy = rot = 0.0
    for fh, amp, tau in HITS:
        if fh <= f < fh + 6 * tau:
            k = f - fh; e = amp * math.exp(-k / tau)
            dx += e * math.sin(k * 2.3 + 0.4); dy += e * 0.8 * math.sin(k * 3.1 + 1.2); rot += e * 0.02 * math.sin(k * 1.7)
    return dx, dy, rot

def frame_geom(s, f, t, u):
    """returns crop centre (cx, cy), crop height ch (source px), rotation deg."""
    sw, sh = E.SRC[s["src"]][2], E.SRC[s["src"]][3]
    fa = face_at(s, t) if s.get("face") is not None else None
    if s.get("lock") and fa:
        # output face width = fw * W / cw, cw = ch*9/16, ch = sh/z  -> z = LOCKw * sh*9/16 / (fw * W)
        z = clamp(E.LOCK_FACE["w"] * sh * 9 / 16 / (fa[2] * W), 1.0, 2.2)
        ch = sh / z; cw = ch * 9 / 16
        cx = fa[0]; cy = fa[1] + ch * (0.5 - E.LOCK_FACE["y"] / H)
    else:
        z = keys_at(s.get("z", [(0, 1.0)]), u)
        ch = sh / z; cw = ch * 9 / 16
        if fa:
            cx, cy = fa[0], fa[1] + ch * (0.5 - 0.37)
            if s.get("face_x") is not None: cx = cx + cw * (0.5 - s["face_x"])          # off-centre framing (room for type)
        else:
            mc = s.get("cx", (sw / 2, sw / 2)); cx = mc[0] + (mc[1] - mc[0]) * smooth(u); cy = sh / 2
        if s.get("pan_to") and u > s["pan_to"][0]:
            v = smooth((u - s["pan_to"][0]) / (1 - s["pan_to"][0]))
            cx = cx + (s["pan_to"][1] - cx) * v; cy = cy + (s["pan_to"][2] - cy) * v
    k = f - s["f0"]
    ch /= (1 + s.get("bounce", 0.045 if s.get("look") == "cine" else 0.0) * math.exp(-k / 4.0)) * beat_bounce(f)
    cw = ch * 9 / 16
    cx = clamp(cx, cw / 2, sw - cw / 2); cy = clamp(cy, ch / 2, sh - ch / 2)
    return cx, cy, ch

# ============================================================================ grade
CORR = {}
def correction(s):
    if s["n"] in CORR: return CORR[s["n"]]
    t = tmap(s, 0.5); img = sample(s["src"], t).astype(np.float32) / 255
    L = img[..., 0] * 0.114 + img[..., 1] * 0.587 + img[..., 2] * 0.299
    fa = face_at(s, t) if s.get("face") is not None else None
    if fa:
        r = int(fa[2] * 0.3); x, y = int(fa[0]), int(fa[1])
        patch = L[max(0, y - r):y + r, max(0, x - r):x + r]; face = float(np.percentile(patch, 65)) if patch.size else float(L.mean())
    else:
        face = float(np.percentile(L, 70))
    target = 0.30 if s.get("look") == "night" else 0.44
    g = clamp(math.log(target) / math.log(clamp(face, 0.02, 0.97)), 0.62, 1.35)
    m = img.reshape(-1, 3).mean(0); gains = np.clip((m.mean() / (m + 1e-6)) ** (0.25 if s.get("look") == "cine" else 0.12), 0.88, 1.12)
    CORR[s["n"]] = (g, gains.astype(np.float32)); return CORR[s["n"]]

_LUT = None
def lut():
    global _LUT
    if _LUT is None:
        x = np.linspace(0, 1, 1024, dtype=np.float32)
        y = PchipInterpolator([0, .08, .25, .5, .75, .92, 1], [0.025, 0.06, 0.215, 0.5, 0.79, 0.94, 0.985])(x)
        _LUT = (x, y.astype(np.float32))
    return _LUT

def grade(img, s, f):
    g, gains = correction(s)
    x = np.clip(img * gains, 0, 1) ** g
    lx, ly = lut(); x = np.interp(x, lx, ly).astype(np.float32)
    L = (x[..., 0] * 0.114 + x[..., 1] * 0.587 + x[..., 2] * 0.299)[..., None]
    if s.get("look") == "night":
        sat = 0.80
        x = L + (x - L) * sat
        x = x + (1 - L) ** 2 * np.array([0.045, 0.020, -0.012], np.float32) + L ** 2 * np.array([0.0, 0.006, 0.02], np.float32)
        x = x * 0.97 + 0.012
    elif s.get("look") == "vapor":                       # pastel Miami VHS: violet-lifted blacks, peach/pink highs, cyan shadows
        sat = 1.06
        x = L + (x - L) * sat
        x = x * 0.90 + np.array([0.050, 0.012, 0.045], np.float32)
        x = x + (1 - L) ** 2 * np.array([0.050, 0.020, -0.005], np.float32) + L ** 1.8 * np.array([-0.030, 0.010, 0.060], np.float32)
    elif s.get("look") == "noir":                        # forensic noir: drained cold colour, teal-black shadows, blood red kept
        red = np.clip((x[..., 2] - np.maximum(x[..., 0], x[..., 1])) * 3.2, 0, 1)[..., None]
        sat = 0.40 + 0.80 * red
        x = L + (x - L) * sat
        x = x + (1 - L) ** 2.4 * np.array([0.040, 0.022, -0.012], np.float32) + L ** 1.6 * np.array([0.020, 0.010, -0.010], np.float32)
        x = x * 0.55 + (x * x * (3 - 2 * x)) * 0.45                                    # S-curve contrast
        x[..., 2:3] = x[..., 2:3] + red * 0.05
    elif s.get("look") == "nocturne":                    # sodium nocturne: indigo shadows (lifted, not crushed), sodium-amber highs, skin kept
        if s.get("ev"): x = np.clip(x * (2 ** s["ev"]), 0, 1); L = (x[..., 0] * 0.114 + x[..., 1] * 0.587 + x[..., 2] * 0.299)[..., None]
        sat = 0.90
        x = L + (x - L) * sat
        x = x * 0.93 + 0.022
        x = x + (1 - L) ** 2.0 * np.array([0.050, 0.014, -0.012], np.float32) + L ** 1.7 * np.array([-0.045, 0.012, 0.050], np.float32)
        x = x * 0.8 + (x * x * (3 - 2 * x)) * 0.2                                       # gentle S-curve only
    elif s.get("look") == "speed":                       # Flash: deep teal shadows, amber/gold highlights, rich reds
        sat = 1.14
        x = L + (x - L) * sat
        x = x + (1 - L) ** 2.2 * np.array([0.040, 0.022, -0.016], np.float32) + L ** 1.6 * np.array([-0.035, 0.010, 0.040], np.float32)
    else:
        sat = 1.08
        x = L + (x - L) * sat
        x = x + (1 - L) ** 2 * np.array([0.030, 0.018, -0.010], np.float32) + L ** 2 * np.array([-0.025, 0.006, 0.030], np.float32)
    if s.get("drain"):
        u = (f - s["f0"]) / max(1, s["f1"] - s["f0"]); a0, a1 = s["drain"]; d = smooth((u - a0) / (a1 - a0))
        L2 = (x[..., 0] * 0.114 + x[..., 1] * 0.587 + x[..., 2] * 0.299)[..., None]
        x = x + (L2 - x) * 0.85 * d; x = x * (1 - 0.25 * d)
    return np.clip(x, 0, 1)

# ============================================================================ shot render
def render_fit(s, f, img, u, with_shake):
    """whole source frame as a framed clipping over a blurred, darkened cover of itself."""
    g = grade(img.astype(np.float32) / 255, s, f)
    sh_, sw_ = g.shape[:2]
    cs = H / sh_; bg = cv2.resize(g, (int(sw_ * cs), H), interpolation=cv2.INTER_LINEAR)
    x0 = (bg.shape[1] - W) // 2; bg = cv2.GaussianBlur(bg[:, x0:x0 + W], (0, 0), 28) * 0.42
    z = keys_at(s.get("z", [(0, 1.0)]), u) * (1 + 0.06 * math.exp(-(f - s["f0"]) / 4.0))
    fw_ = int(W * 0.94 * z); fh_ = int(fw_ * sh_ / sw_)
    fg = cv2.resize(g, (fw_, fh_), interpolation=cv2.INTER_CUBIC)
    out = bg.copy(); dx, dy, _ = shake(f) if with_shake else (0, 0, 0)
    X, Y = int((W - fw_) / 2 + dx), int(H * 0.44 - fh_ / 2 + dy)
    m = np.zeros((H, W), np.float32); m[max(0, Y):Y + fh_, max(0, X):X + fw_] = 1
    out = out * (1 - 0.6 * cv2.GaussianBlur(np.roll(np.roll(m, 22, 0), 16, 1), (0, 0), 18)[..., None])
    b = 8; card = np.full((fh_ + 2 * b, fw_ + 2 * b, 3), 0.95, np.float32); card[b:b + fh_, b:b + fw_] = fg
    ya, xa = max(0, Y - b), max(0, X - b); yb, xb = min(H, Y - b + card.shape[0]), min(W, X - b + card.shape[1])
    out[ya:yb, xa:xb] = card[ya - (Y - b):yb - (Y - b), xa - (X - b):xb - (X - b)]
    return np.clip(out, 0, 1)

def render_shot(s, f, with_shake=True, want_mask=False):
    img, t, u = source_img(s, f)
    if s.get("fit"): return render_fit(s, f, img, u, with_shake)
    if want_mask:
        msk = seg_mask(s, t)
    cx, cy, ch = frame_geom(s, f, t, u)
    cw = ch * 9 / 16; sc = W / cw
    dx, dy, rot = shake(f) if with_shake else (0, 0, 0)
    m = 16
    x0 = int(max(0, cx - cw / 2 - m)); x1 = int(min(img.shape[1], cx + cw / 2 + m))
    y0 = int(max(0, cy - ch / 2 - m)); y1 = int(min(img.shape[0], cy + ch / 2 + m))
    roi = grade(img[y0:y1, x0:x1].astype(np.float32) / 255, s, f)
    th = math.radians(rot); co, si = math.cos(th) / sc, math.sin(th) / sc
    lx, ly = cx - x0, cy - y0
    M = np.float32([[co, -si, lx - co * (W / 2 + dx) + si * (H / 2 + dy)], [si, co, ly - si * (W / 2 + dx) - co * (H / 2 + dy)]])
    out = cv2.warpAffine(roi, M, (W, H), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)
    if want_mask:
        mr = cv2.resize(msk, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)[y0:y1, x0:x1]
        mw = cv2.warpAffine(mr, M, (W, H), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
        return np.clip(out, 0, 1), np.clip(mw, 0, 1)
    return np.clip(out, 0, 1)

def to_screen(s, f, x, y):
    """source px -> output px for shot s at frame f (no shake)."""
    t, u, _ = src_time(s, f); cx, cy, ch = frame_geom(s, f, t, u); sc = W / (ch * 9 / 16)
    return (x - cx) * sc + W / 2, (y - cy) * sc + H / 2, sc

# ============================================================================ generic helpers
def paste(out, rgba, x0, y0, a=1.0):
    h, w = rgba.shape[:2]
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xb <= xa or yb <= ya or a <= 0: return out
    sub = rgba[ya - y0:yb - y0, xa - x0:xb - x0]; al = sub[..., 3:4] * a
    out[ya:yb, xa:xb] = out[ya:yb, xa:xb] * (1 - al) + sub[..., :3] * al
    return out

_FONTS = {}
def font(p, s):
    if (p, s) not in _FONTS: _FONTS[(p, s)] = ImageFont.truetype(p, s)
    return _FONTS[(p, s)]

def text_mask(text, path, size, tracking=0, stroke=0):
    fnt = font(path, size)
    wdt = int(sum(fnt.getlength(c) + tracking for c in text) + 4 * stroke + 40); hgt = int(size * 1.32 + 4 * stroke + 20)
    im = Image.new("L", (wdt, hgt), 0); d = ImageDraw.Draw(im); x = 20 + 2 * stroke
    for c in text:
        d.text((x, 10 + 2 * stroke), c, font=fnt, fill=255, stroke_width=stroke, stroke_fill=255); x += fnt.getlength(c) + tracking
    m = np.asarray(im).astype(np.float32) / 255
    ys, xs = np.nonzero(m > 0.02)
    return m[max(0, ys.min() - 4):ys.max() + 5, max(0, xs.min() - 4):xs.max() + 5]

def rgba(mask, col):
    return np.dstack([np.ones_like(mask) * col[0], np.ones_like(mask) * col[1], np.ones_like(mask) * col[2], mask]).astype(np.float32)

def shadowed(mask, col, blur=10, sa=0.75, stroke=0, scol=(0.02, 0.02, 0.02)):
    pad = blur * 3 + stroke + 4
    m = np.pad(mask, pad)
    out = np.zeros(m.shape + (4,), np.float32)
    sh = cv2.GaussianBlur(m, (0, 0), blur) * sa
    out[..., 3] = sh
    if stroke:
        st = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * stroke + 1, 2 * stroke + 1)))
        a = st; out[..., :3] = out[..., :3] * (1 - a[..., None]) + np.array(scol, np.float32) * a[..., None]; out[..., 3] = np.maximum(out[..., 3], a)
    a = m; out[..., :3] = out[..., :3] * (1 - a[..., None]) + np.array(col, np.float32) * a[..., None]; out[..., 3] = np.maximum(out[..., 3], a)
    return out

def hblur(img, L, vertical=False):
    L = int(L)
    if L < 3: return img
    k = np.ones((L, 1) if vertical else (1, L), np.float32) / L
    return cv2.filter2D(img, -1, k, borderType=cv2.BORDER_REFLECT)

def rgb_split(img, d, vertical=False):
    d = int(round(d))
    if d == 0: return img
    o = img.copy(); ax = 0 if vertical else 1
    o[..., 2] = np.roll(img[..., 2], d, axis=ax); o[..., 0] = np.roll(img[..., 0], -d, axis=ax)
    return o

def zoom_about(img, px, py, s, rot=0.0):
    M = cv2.getRotationMatrix2D((px, py), rot, s)
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def radial_blur(img, px, py, s0, s1, n=6):
    acc = None
    for i in range(n):
        s = s0 + (s1 - s0) * i / (n - 1); w = zoom_about(img, px, py, s)
        acc = w if acc is None else acc + w
    return acc / n

def last_frame_of(s, back=1, with_shake=False):
    return render_shot(s, s["f1"] - back, with_shake)

# ============================================================================ transitions
# ---- shatter (gunshot)
_SH = {}
def shards():
    if "list" in _SH: return _SH["list"]
    rng = np.random.default_rng(41); cx, cy = W / 2, H * 0.40
    pts = [(cx, cy)]
    for i in range(110):
        r = (rng.random() ** 1.7) * 1300; a = rng.uniform(0, 2 * math.pi)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a) * 1.25
        if 0 <= x < W and 0 <= y < H: pts.append((x, y))
    for x in (0, W - 1):
        for y in np.linspace(0, H - 1, 7): pts.append((x, y))
    for y in (0, H - 1):
        for x in np.linspace(0, W - 1, 5): pts.append((x, y))
    sd = cv2.Subdiv2D((0, 0, W, H))
    for p in pts: sd.insert((float(min(W - 1, max(0, p[0]))), float(min(H - 1, max(0, p[1])))))
    facets, centers = sd.getVoronoiFacetList([])
    L = []
    for poly, c in zip(facets, centers):
        poly = np.array(poly, np.float32); poly[:, 0] = np.clip(poly[:, 0], 0, W - 1); poly[:, 1] = np.clip(poly[:, 1], 0, H - 1)
        x0, y0 = poly.min(0).astype(int); x1, y1 = poly.max(0).astype(int) + 1
        if x1 - x0 < 3 or y1 - y0 < 3: continue
        m = np.zeros((y1 - y0, x1 - x0), np.uint8); cv2.fillPoly(m, [(poly - [x0, y0]).astype(np.int32)], 255, cv2.LINE_AA)
        d = math.hypot(c[0] - cx, c[1] - cy) + 1; dirx, diry = (c[0] - cx) / d, (c[1] - cy) / d
        L.append(dict(poly=poly, box=(x0, y0, x1, y1), mask=m.astype(np.float32) / 255, c=(float(c[0]), float(c[1])),
                      v=(dirx, diry), sp=rng.uniform(0.7, 1.3) * (1.6 - min(1.0, d / 1400)), w=rng.uniform(-14, 14),
                      dz=rng.uniform(0.004, 0.02), delay=d / 1400 * 2.2))
    _SH["list"] = L; _SH["center"] = (cx, cy)
    return L

def crack_overlay(img, strength):
    """white glass cracks (shard edges near the impact + radial lines)."""
    if "cr" not in _SH:
        L = shards(); cx, cy = _SH["center"]
        m = np.zeros((H, W), np.uint8)
        for s in L:
            if math.hypot(s["c"][0] - cx, s["c"][1] - cy) < 900:
                cv2.polylines(m, [s["poly"].astype(np.int32)], True, 255, 2, cv2.LINE_AA)
        rng = np.random.default_rng(5)
        for i in range(16):
            a = i / 16 * 2 * math.pi + rng.uniform(-0.1, 0.1); r = rng.uniform(500, 1500)
            pts = [(cx, cy)]
            for j in range(1, 9):
                rr = r * j / 8; aa = a + rng.uniform(-0.06, 0.06)
                pts.append((cx + rr * math.cos(aa), cy + rr * math.sin(aa)))
            cv2.polylines(m, [np.array(pts, np.int32)], False, 255, 3, cv2.LINE_AA)
        cv2.circle(m, (int(cx), int(cy)), 26, 255, -1, cv2.LINE_AA)
        mf = m.astype(np.float32) / 255
        _SH["cr"] = np.clip(mf + cv2.GaussianBlur(mf, (0, 0), 6) * 0.9, 0, 1)
    c = _SH["cr"][..., None] * strength
    return img * (1 - c) + c * 0.98

def shatter(A, B, k):
    """A = frozen frame, B = incoming; k frames since the burst started."""
    out = B * (0.55 + 0.45 * clamp(k / 10, 0, 1))
    cx, cy = _SH["center"]
    for s in shards():
        kk = k - s["delay"]
        x0, y0, x1, y1 = s["box"]
        if kk <= 0:
            sub = A[y0:y1, x0:x1]; m = s["mask"][..., None]
            out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1 - m) + sub * m
            continue
        mv = 38 * s["sp"] * kk ** 1.45
        tx, ty = s["v"][0] * mv, s["v"][1] * mv + 1.2 * kk * kk
        sc = 1 + s["dz"] * kk * 3; ang = s["w"] * kk * 0.35
        a = clamp(1 - (kk - 6) / 8, 0, 1)
        if a <= 0: continue
        pcx, pcy = s["c"]
        M = cv2.getRotationMatrix2D((pcx, pcy), ang, sc); M[0, 2] += tx; M[1, 2] += ty
        pad = int(60 + mv * 1.6 + 40 * sc)
        X0, Y0 = max(0, int(pcx + tx) - (x1 - x0) // 2 - pad), max(0, int(pcy + ty) - (y1 - y0) // 2 - pad)
        X1, Y1 = min(W, int(pcx + tx) + (x1 - x0) // 2 + pad), min(H, int(pcy + ty) + (y1 - y0) // 2 + pad)
        if X1 <= X0 or Y1 <= Y0: continue
        M2 = M.copy(); M2[0, 2] -= X0; M2[1, 2] -= Y0
        mm = np.zeros((y1 - y0, x1 - x0), np.float32); mm[:] = s["mask"]
        # warp the shard (source region with its mask) into the destination window
        Ms = M2.copy(); Ms[0, 2] += M2[0, 0] * x0 + M2[0, 1] * y0; Ms[1, 2] += M2[1, 0] * x0 + M2[1, 1] * y0
        wi = cv2.warpAffine(A[y0:y1, x0:x1], Ms, (X1 - X0, Y1 - Y0), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
        wm = cv2.warpAffine(mm, Ms, (X1 - X0, Y1 - Y0), flags=cv2.INTER_LINEAR, borderValue=0)[..., None] * a
        edge = cv2.morphologyEx(wm[..., 0], cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))[..., None]
        shade = 0.9 + 0.25 * math.sin(math.radians(ang) * 3)
        out[Y0:Y1, X0:X1] = out[Y0:Y1, X0:X1] * (1 - wm) + np.clip(wi * shade + edge * 0.6, 0, 1) * wm
    return out

# ---- eye portal
def eye_point(s, f):
    t, u, _ = src_time(s, f); fa = face_at(s, t)
    if not fa: return W / 2, H * 0.4, 30
    lx, ly, rx, ry = fa[3]
    x, y, sc = to_screen(s, f, lx, ly)                 # the eye on the viewer's left
    return x, y, fa[2] * sc * 0.07

def eye_portal(out, f, s):
    fc = s["f0"]; k = f - fc; A_shot = prev_shot(s)
    if -7 <= k < 0:
        ex, ey, ir = eye_point(A_shot, f)
        u = (k + 7) / 7.0; sc = 1 + 9 * ein(u, 2.4)
        A = out
        Az = radial_blur(A, ex, ey, sc, sc * (1 + 0.08 * u), 5)
        # B appears inside the pupil (pupil is now at screen position ex,ey scaled)
        r = ir * sc * 0.9
        if r > 4:
            B = render_shot(s, fc, False)
            Bz = zoom_about(B, W / 2, H / 2, 0.35 + 0.65 * u * 0.4)
            Bz = cv2.warpAffine(Bz, np.float32([[1, 0, ex - W / 2], [0, 1, ey - H / 2]]), (W, H), borderMode=cv2.BORDER_REFLECT)
            yy, xx = np.ogrid[:H, :W]
            m = np.clip((r - np.sqrt((xx - ex) ** 2 + (yy - ey) ** 2)) / 3.0, 0, 1).astype(np.float32)[..., None]
            Az = Az * (1 - m) + Bz * m
        return Az
    if 0 <= k < 9:
        u = k / 9.0; sc = 1 + 1.6 * (1 - eout(u, 3))
        return radial_blur(out, W / 2, H / 2, sc * 1.06, sc, 5)
    return out

# ---- cube rotate (vertical axis)
def cube(A, B, u):
    """u: 0 -> 1 across the transition; A rotates away to the left, B comes in from the right."""
    th = u * math.pi / 2; d = W / 2; foc = 2600.0
    def proj(xs, zs):
        return [(W / 2 + x * foc / (foc + z), H / 2, foc / (foc + z)) for x, z in zip(xs, zs)]
    out = np.zeros((H, W, 3), np.float32)
    faces = []
    # face A at z=-d (front), spans x in [-d, d]; rotate by -th around y-axis at centre z=0
    for img, base in ((A, 0.0), (B, math.pi / 2)):
        a = -th + base
        x0, z0 = -d * math.cos(a) - (-d) * math.sin(a) * 0 , 0
        pts = []
        for xl in (-d, d):
            xr = xl * math.cos(a) + d * math.sin(a); zr = -xl * math.sin(a) + d * math.cos(a)
            zr = d - zr                      # camera distance offset (front face z=0)
            pts.append((xr, zr))
        (xa, za), (xb, zb) = pts
        if xb - xa <= 2: continue
        sa, sb = foc / (foc + za), foc / (foc + zb)
        quad = np.float32([[W / 2 + xa * sa, H / 2 - H / 2 * sa], [W / 2 + xb * sb, H / 2 - H / 2 * sb],
                           [W / 2 + xb * sb, H / 2 + H / 2 * sb], [W / 2 + xa * sa, H / 2 + H / 2 * sa]])
        src = np.float32([[0, 0], [W, 0], [W, H], [0, H]])
        Mp = cv2.getPerspectiveTransform(src, quad)
        wi = cv2.warpPerspective(img, Mp, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
        wm = cv2.warpPerspective(np.ones((H, W), np.float32), Mp, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)[..., None]
        shade = 0.45 + 0.55 * abs(math.cos(a))
        faces.append(((za + zb) / 2, wi * shade, wm))
    for _, wi, wm in sorted(faces, key=lambda x: -x[0]):
        out = out * (1 - wm) + wi * wm
    return out

# ---- datamosh
def datamosh(s, f):
    k = f - s["f0"]; A_shot = prev_shot(s)
    mosh = last_frame_of(A_shot)
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_FAST)
    prevB = cv2.resize(render_shot(s, s["f0"], False), (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    gy, gx = np.mgrid[0:H, 0:W].astype(np.float32)
    for j in range(1, k + 1):
        curB = cv2.resize(render_shot(s, s["f0"] + j, False), (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        g0 = cv2.cvtColor((prevB * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY); g1 = cv2.cvtColor((curB * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
        fl = dis.calc(g1, g0, None)                                    # where each current pixel came from
        fl = cv2.resize(fl, (W, H)) * 4 * 3.5
        fl += np.float32([30, 14])                                    # a little global drift for the smear
        mosh = cv2.remap(mosh, gx + fl[..., 0], gy + fl[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        prevB = curB
    B = render_shot(s, f, False)
    if k >= 6:
        u = (k - 6) / 5.0
        LB = B.mean(2, keepdims=True)
        m = np.clip((LB - (1 - 1.2 * u)) / 0.15, 0, 1)
        mosh = mosh * (1 - m) + B * m
    return rgb_split(mosh, 6 * (1 - clamp(k / 10, 0, 1)))

# ---- split slam (three horizontal bands)
def split_slam(A, B, k):
    out = A * 0.5
    n = 3
    for i in range(n):
        y0, y1 = int(i * H / n), int((i + 1) * H / n)
        kk = k - i * 1.2
        v = eout(clamp(kk / 7, 0, 1), 3)
        if v <= 0: continue
        sgn = 1 if i % 2 == 0 else -1
        dx = int(sgn * (1 - v) * W)
        band = np.roll(B[y0:y1], dx, axis=1)
        if dx > 0: band[:, :dx] = out[y0:y1, :dx]
        elif dx < 0: band[:, dx:] = out[y0:y1, dx:]
        if v < 1: band = hblur(band, 90 * (1 - v))
        out[y0:y1] = band
    for i in range(1, n):
        y = int(i * H / n); a = clamp(1 - (k - 7) / 4, 0, 1)
        out[y - 3:y + 3] = out[y - 3:y + 3] * (1 - a) + 0.97 * a
    return out

# ---- whip (horizontal)
def whip(out, f, s):
    k = f - s["f0"]
    if -4 <= k < 0:
        u = (k + 5) / 5.0; dx = -int(W * 0.35 * ein(u, 2))
        o = np.roll(out, dx, axis=1); return hblur(o, 30 + 260 * ein(u, 2))
    if 0 <= k < 6:
        u = k / 6.0; dx = int(W * 0.30 * (1 - eout(u, 2)))
        o = np.roll(out, dx, axis=1); return hblur(o, 280 * (1 - eout(u, 2)))
    return out

# ---- light leak burn
_LEAK = {}
def leak(out, f, fc):
    k = f - fc
    if not (-8 <= k < 10): return out
    if "g" not in _LEAK:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        _LEAK["xx"], _LEAK["yy"] = xx, yy
    xx, yy = _LEAK["xx"], _LEAK["yy"]
    u = (k + 8) / 18.0
    px = -350 + (W * 0.55 + 350) * u; py = H * (0.10 + 0.80 * u)
    r = np.sqrt(((xx - px) / 520) ** 2 + ((yy - py) / 900) ** 2)
    g = np.exp(-r * r * 1.6) * math.sin(math.pi * u) ** 0.8
    col = np.stack([0.15 + 0.2 * g, 0.45 + 0.4 * g, 1.0 * np.ones_like(g)], -1).astype(np.float32)   # warm orange-red
    hot = np.exp(-r * r * 9) * math.sin(math.pi * u) ** 2
    o = 1 - (1 - out) * (1 - col * g[..., None] * 0.85)           # screen
    return np.clip(o + hot[..., None] * 0.30, 0, 1)

# ---- polaroid flick
def polaroid(B, f, s):
    k = f - s["f0"]
    if k >= 20: return B
    A = last_frame_of(prev_shot(s))
    u1 = eout(clamp(k / 6, 0, 1), 3)                  # shrink into a card
    u2 = ein(clamp((k - 6) / 13, 0, 1), 2.2)          # fly off
    sc = 1 - 0.40 * u1
    bw = int(34 * sc); bb = int(150 * sc)
    cw, chh = int(W * sc), int(H * sc * 0.82)
    img = cv2.resize(A[int(H * 0.06):int(H * 0.06) + int(H * 0.82)], (cw, chh), interpolation=cv2.INTER_AREA)
    card = np.full((chh + bw + bb, cw + 2 * bw, 3), 0.95, np.float32)
    card[bw:bw + chh, bw:bw + cw] = img
    lab = text_mask("SUSPECT #1  —  D. MORGAN", F_MONO, max(14, int(46 * sc)), tracking=2)
    ly = bw + chh + (bb - lab.shape[0]) // 2; lx = (card.shape[1] - lab.shape[1]) // 2
    if lab.shape[1] < card.shape[1]:
        a = lab[..., None]; card[ly:ly + lab.shape[0], lx:lx + lab.shape[1]] = card[ly:ly + lab.shape[0], lx:lx + lab.shape[1]] * (1 - a) + np.array([0.12, 0.12, 0.16], np.float32) * a
    ang = -7 * u1 - 40 * u2
    tx = W / 2 + 900 * u2; ty = H / 2 - 1500 * u2 + 60 * u1
    ch_, cw_ = card.shape[:2]
    M = cv2.getRotationMatrix2D((cw_ / 2, ch_ / 2), ang, 1.0); M[0, 2] += tx - cw_ / 2; M[1, 2] += ty - ch_ / 2
    wc = cv2.warpAffine(card, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
    wm = cv2.warpAffine(np.ones(card.shape[:2], np.float32), M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    sh = cv2.GaussianBlur(np.roll(np.roll(wm, 28, 0), 18, 1), (0, 0), 22)[..., None] * 0.7
    base = B * (0.6 + 0.4 * u2)
    o = base * (1 - sh) ; wm = wm[..., None]
    if u2 > 0: wc = hblur(wc, 40 * u2)
    return o * (1 - wm) + wc * wm

# ---- vertical slide (push up)
def slide(out, f, s):
    k = f - s["f0"]
    if not (0 <= k < 8): return out
    A = last_frame_of(prev_shot(s)); u = eout(k / 8, 3)
    dy = int(H * (1 - u))
    res = np.vstack([A[H - dy:], out[:H - dy]]) if dy > 0 else out       # A pushed up, B rises from below
    return hblur(res, 90 * (1 - u), vertical=True)

# ---- glitch
def glitch(out, f, f0, seed=0, amp=1.0):
    k = f - f0
    if not (-2 <= k <= 3): return out
    rng = np.random.default_rng(1000 + f + seed); o = out.copy(); a = [0.5, 0.9, 1.0, 0.7, 0.4, 0.2][k + 2] * amp
    for _ in range(10):
        y = int(rng.integers(0, H - 80)); h = int(rng.integers(10, 120)); d = int(rng.integers(-160, 160) * a)
        o[y:y + h] = np.roll(o[y:y + h], d, axis=1)
    return rgb_split(o, 16 * a)

# ============================================================================ graphics (v4: smooth, eased)
CAP_Y = 1450
def word_layer(w, path, size, col, blur=0.0, shadow=0.75):
    m = text_mask(w, path, size)
    if blur > 0.3: m = cv2.GaussianBlur(m, (0, 0), blur)
    return shadowed(m, col, blur=9, sa=shadow)

def captions(out, f):
    """dialogue: words fade in, rise and de-blur; the line re-centres smoothly as each word arrives."""
    t = f / FPS
    fsz = 66
    starts = [E.d2e(di, ws[0][1]) - 0.03 for di, ws, _, _ in E.CAPTIONS]
    for idx, (di, words, s_end, emph) in enumerate(E.CAPTIONS):
        t_in = starts[idx]; t_out = E.d2e(di, s_end) + 0.18
        if idx + 1 < len(E.CAPTIONS) and starts[idx + 1] - t_out < 0.4: t_out = min(t_out, starts[idx + 1] - 0.02)
        if not (t_in <= t < t_out): continue
        kout = (t - (t_out - 6 / FPS)) * FPS
        a_line = 1.0 if kout < 0 else clamp(1 - kout / 6, 0, 1)
        y_line = CAP_Y - (10 * eout(kout / 6) if kout > 0 else 0)
        fnt = font(F_BOLD, fsz); sp = fnt.getlength(" ")
        vs = [eout(((t - E.d2e(di, ws)) * FPS + 1) / 9, 3) for _, ws in words]
        widths = [fnt.getlength(w) for w, _ in words]
        total = sum((wd + sp) * v for wd, v in zip(widths, vs)) - sp * (vs[-1] if vs else 0)
        x = W / 2 - max(total, 0) / 2
        for (w, ws), wd, v in zip(words, widths, vs):
            if v > 0.001:
                col = RED if w in emph else WHITE
                lay = word_layer(w, F_BOLD, fsz, col, blur=6 * (1 - v))
                out = paste(out, lay, int(x + wd / 2 - lay.shape[1] / 2), int(y_line + 22 * (1 - v) - lay.shape[0] / 2), v * a_line)
            x += (wd + sp) * v
    return out

_BHB = {}
def bhb_title(out, f, s, person):
    """BAY HARBOR (in front, top) / BUTCHER (behind his neck and shoulders); words land on Doakes's syllables."""
    t = f / FPS
    fsb = font(F_SB, 74); gap = fsb.getlength("   ")
    wb = sum(fsb.getlength(c) + 14 for c in "BAY"); wh = sum(fsb.getlength(c) + 14 for c in "HARBOR")
    x_bay = W / 2 - (wb + gap + wh) / 2; x_har = x_bay + wb + gap
    front = out.copy() * 0; front_a = np.zeros((H, W, 1), np.float32)
    behind = out.copy()
    for word, ws in E.BHB:
        k = (t - E.d2e(0, ws)) * FPS
        if k < -1: continue
        v = eout((k + 1) / 10, 3)
        if word == "BUTCHER":
            m = text_mask(word, F_BLACK, 196, tracking=-3 + int(24 * (1 - v)))
            if v < 1: m = cv2.GaussianBlur(m, (0, 0), 0.1 + 9 * (1 - v))
            sc = 1 + 0.10 * (1 - v)
            if sc > 1.002: m = cv2.resize(m, (int(m.shape[1] * sc), int(m.shape[0] * sc)), interpolation=cv2.INTER_LINEAR)
            L = shadowed(m, RED * 1.05, blur=16, sa=0.55)
            behind = paste(behind, L, int(W / 2 - L.shape[1] / 2), int(690 - L.shape[0] / 2), v)
        else:
            m = text_mask(word, F_SB, 74, tracking=14 + int(20 * (1 - v)))
            if v < 1: m = cv2.GaussianBlur(m, (0, 0), 0.1 + 6 * (1 - v))
            L = shadowed(m, WHITE, blur=10, sa=0.7)
            cx = x_bay + wb / 2 if word == "BAY" else x_har + wh / 2
            x0, y0 = int(cx - L.shape[1] / 2), int(300 + 14 * (1 - v) - L.shape[0] / 2)
            h_, w_ = L.shape[:2]; ya, xa = max(0, y0), max(0, x0); yb, xb = min(H, y0 + h_), min(W, x0 + w_)
            sub = L[ya - y0:yb - y0, xa - x0:xb - x0]
            front[ya:yb, xa:xb] = front[ya:yb, xa:xb] * (1 - sub[..., 3:4] * v) + sub[..., :3] * sub[..., 3:4] * v
            front_a[ya:yb, xa:xb] = np.maximum(front_a[ya:yb, xa:xb], sub[..., 3:4] * v)
    o = behind * (1 - person[..., None]) + PERSON_IMG[0] * person[..., None]
    return o * (1 - front_a) + front
PERSON_IMG = [None]

def scope_overlay(out, f, s):
    u = (f - s["f0"]) / max(1, s["f1"] - s["f0"]); k = f - s["f0"]
    R = W * (0.47 - 0.05 * smooth((u - 0.6) / 0.4))
    if k < 12: R *= eout(k / 12, 3)
    cx, cy = W / 2, H * 0.42
    yy, xx = np.ogrid[:H, :W]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2).astype(np.float32)
    inside = np.clip((R - d) / 4, 0, 1)[..., None]
    lens = np.clip(1 - ((d / max(R, 1)) ** 4) * 0.45, 0.4, 1)[..., None]
    img = out * lens
    ring = np.exp(-((d - R) / 5.0) ** 2)[..., None]
    o = img * inside + (1 - inside) * 0.012
    o = o + ring * np.array([0.25, 0.25, 0.30], np.float32) * 0.6
    # reticle: thin crosshair with a centre gap + mil-dots
    col = (0.06, 0.06, 0.75)
    g = int(R * 0.10); r = int(R)
    for (x0, y0, x1, y1) in ((int(cx - r), int(cy), int(cx - g), int(cy)), (int(cx + g), int(cy), int(cx + r), int(cy)),
                             (int(cx), int(cy - r), int(cx), int(cy - g)), (int(cx), int(cy + g), int(cx), int(cy + r))):
        cv2.line(o, (x0, y0), (x1, y1), (0.02, 0.02, 0.02), 4, cv2.LINE_AA); cv2.line(o, (x0, y0), (x1, y1), col, 2, cv2.LINE_AA)
    for i in range(1, 5):
        for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            cv2.circle(o, (int(cx + sx * g * (1 + i * 0.9)), int(cy + sy * g * (1 + i * 0.9))), 4, col, -1, cv2.LINE_AA)
    cv2.circle(o, (int(cx), int(cy)), 5, col, -1, cv2.LINE_AA)
    return np.clip(o, 0, 1)

def scope_sway(s, f):
    k = f - s["f0"]
    return 7 * math.sin(k * 0.045) + 3 * math.sin(k * 0.13), 6 * math.sin(k * 0.037 + 1.0) + 2 * math.sin(k * 0.11)

def lyric_layer(out, f, person=None):
    t = f / FPS
    for txt, s0, s1 in E.LYRICS:
        a0, a1 = E.s2e(s0), E.s2e(s1)
        if txt == "CAN'T GET CAUGHT": a1 = E.T_STOP + 0.28
        if txt == "BLEED IT": continue                          # drawn by draw_bleed()
        if not (a0 - 0.05 <= t < a1 + 0.16): continue
        k = (t - a0) * FPS; kout = (t - a1) * FPS
        fade = 1.0 if kout <= 0 else clamp(1 - kout / 9, 0, 1)
        if txt == "I NEED IT":                       # each word rises out of a mask line
            fsz = 150; fnt = font(F_BLACK, fsz); sp = fnt.getlength(" ")
            words = E.LYRIC_WORDS[txt]; widths = [fnt.getlength(w) for w, _ in words]
            x = W / 2 - (sum(widths) + sp * 2) / 2; y = 1430
            for (w, ws), wd in zip(words, widths):
                kk = (t - E.s2e(ws)) * FPS
                if kk > -1:
                    v = eout((kk + 1) / 10, 4)
                    L = word_layer(w, F_BLACK, fsz, RED if w == "NEED" else WHITE, blur=3 * (1 - v))
                    hh = L.shape[0]; dy = int(hh * 0.7 * (1 - v))
                    vis = L.copy(); vis[max(0, hh - dy):] = 0 if dy > 0 else vis[max(0, hh - dy):]
                    out = paste(out, np.roll(L, dy, axis=0) * (np.arange(hh)[:, None, None] >= dy), int(x + wd / 2 - L.shape[1] / 2), int(y - hh / 2), fade)
                x += wd + sp
        elif txt == "UNDEFEATED":                    # letters resolve from wide, soft tracking
            v = eout(k / 22, 3); tr = int(60 * (1 - v)) + 6
            m = text_mask(txt, F_XB, 96, tracking=tr)
            if v < 1: m = cv2.GaussianBlur(m, (0, 0), 0.1 + 8 * (1 - v))
            L = shadowed(m, WHITE, blur=10, sa=0.7)
            out = paste(out, L, int(W / 2 - L.shape[1] / 2), int(1640 - L.shape[0] / 2), fade * clamp(k / 6, 0, 1))
        elif txt == "BLEED IT":                      # heavy red, wave-distorted, then the shot cuts it
            m = text_mask(txt, F_BLACK, 190)
            hh, ww = m.shape; yy = np.arange(hh, dtype=np.float32)[:, None]; xx = np.arange(ww, dtype=np.float32)[None, :]
            amp = 5 * math.exp(-k / 6)
            m = cv2.remap(m, (xx + amp * np.sin(yy / 12 + k * 0.9)).astype(np.float32), np.repeat(yy, ww, 1).astype(np.float32), cv2.INTER_LINEAR)
            L = shadowed(m, RED, blur=14, sa=0.8)
            v = eout(k / 5, 3)
            out = paste(out, L, int(W / 2 - L.shape[1] / 2), int(1430 - L.shape[0] / 2), v)
        elif txt == "BULLETS":                       # flies in from the camera
            v = eout(k / 9, 3); sc = 1 + 2.2 * (1 - v)
            m = text_mask(txt, F_BLACK, 170, tracking=-2)
            if sc > 1.002: m = cv2.resize(m, (int(m.shape[1] * sc), int(m.shape[0] * sc)), interpolation=cv2.INTER_LINEAR)
            if v < 1: m = cv2.GaussianBlur(m, (0, 0), 0.1 + 12 * (1 - v))
            L = shadowed(m, WHITE, blur=12, sa=0.8)
            out = paste(out, L, int(W / 2 - L.shape[1] / 2), int(1420 - L.shape[0] / 2), fade * clamp(v * 1.4, 0, 1))
        elif txt == "I CAN'T SEE IT":                # a light bar sweeps across and leaves the letters behind
            m = text_mask(txt, F_XB, 100, tracking=8)
            hh, ww = m.shape; p = eout(k / 16, 2) * (ww + 160) - 80
            reveal = np.clip((p - np.arange(ww)[None, :]) / 60, 0, 1)
            bar = np.exp(-((np.arange(ww)[None, :] - p) / 18.0) ** 2) * (1 if p < ww + 40 else 0)
            L = shadowed(m * reveal, WHITE, blur=10, sa=0.7)
            x0, y0 = int(W / 2 - L.shape[1] / 2), int(1450 - L.shape[0] / 2)
            out = paste(out, L, x0, y0, fade)
            pad = (L.shape[1] - ww) // 2
            glow = np.zeros((L.shape[0], L.shape[1], 4), np.float32); glow[..., :3] = 1.0
            gb = np.zeros(L.shape[:2], np.float32); gb[pad:pad + hh, pad:pad + ww] = np.repeat(bar, hh, 0) * 0.9
            glow[..., 3] = cv2.GaussianBlur(gb, (0, 0), 6)
            out = paste(out, glow, x0, y0, fade)
        elif txt == "CAN'T GET CAUGHT":              # stacked, set behind Dexter
            yy0 = 1230
            for (w, ws), col, fsz in zip(E.LYRIC_WORDS[txt], (WHITE, WHITE, RED), (170, 170, 240)):
                kk = (t - E.s2e(ws)) * FPS
                if kk > -1:
                    v = eout((kk + 1) / 8, 3); sc = 1 + 0.35 * (1 - v)
                    m = text_mask(w, F_BLACK, int(fsz * sc), tracking=-2)
                    if v < 1: m = cv2.GaussianBlur(m, (0, 0), 0.1 + 6 * (1 - v))
                    L = shadowed(m, col, blur=12, sa=0.8)
                    out = paste(out, L, int(W / 2 - L.shape[1] / 2), int(yy0 + fsz * 0.55 - L.shape[0] / 2), v * fade)
                yy0 += int(fsz * 1.0)

    return out

# ---- voidfx logo: the single watermark appearance, as a fly-through-the-'o' transition
_LOGO = {}
def logo_assets():
    if "rgba" not in _LOGO:
        im = Image.open(f"{ROOT}/src/voidfx_logo.webp").convert("RGBA"); im = im.crop(im.getbbox())
        h = int(round(im.height * E.LOGO_W / im.width))
        a = np.asarray(im.resize((E.LOGO_W, h), Image.LANCZOS))[..., [2, 1, 0, 3]].astype(np.float32) / 255
        al = (a[..., 3] > 0.5).astype(np.uint8)
        # the 'o' counter: background pixels enclosed by the letter, around (645/1982, 327/523) of the crop
        sx, sy = int(645 / 1982 * E.LOGO_W), int(327 / 523 * h)
        inv = (1 - al).astype(np.uint8)
        n, lab = cv2.connectedComponents(inv)
        cm = (lab == lab[sy, sx]).astype(np.float32)
        _LOGO.update(rgba=a, counter=cv2.GaussianBlur(cm, (0, 0), 1.0), c=(sx, sy), h=h)
    return _LOGO

def logo_through(A, B, k):
    """k: frames relative to the cut (-12..+10). A = outgoing, B = incoming."""
    L = logo_assets(); lg = L["rgba"]; h = L["h"]
    X0, Y0 = (W - E.LOGO_W) // 2, int(H * 0.44 - h / 2)
    ccx, ccy = X0 + L["c"][0], Y0 + L["c"][1]
    if k < -6:                                                     # slam in
        v = eout((k + 12) / 6, 3); sc = 1.35 - 0.35 * v
    else:
        v = 1.0; sc = 1.0 * math.exp(4.2 * ein((k + 6) / 16, 2.2))   # fly into the counter
    M = cv2.getRotationMatrix2D((ccx, ccy), 0, sc)
    canvas = np.zeros((H, W, 4), np.float32); canvas[Y0:Y0 + h, X0:X0 + E.LOGO_W] = lg
    cnt = np.zeros((H, W), np.float32); cnt[Y0:Y0 + h, X0:X0 + E.LOGO_W] = L["counter"]
    lw = cv2.warpAffine(canvas, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    cw = cv2.warpAffine(cnt, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    if sc > 8: cw = np.maximum(cw, clamp((sc - 8) / 6, 0, 1))          # once the counter passes the screen, B fills
    cw = cw * v
    bgA = A * (0.45 if k >= -6 else 1 - 0.55 * v)
    Bz = zoom_about(B, ccx, ccy, 1.6 - 0.6 * clamp((sc - 1) / 30, 0, 1))
    out = bgA * (1 - cw[..., None]) + Bz * cw[..., None]
    if k >= -9:                                                    # sheen across the metal
        xs = np.arange(W)[None, :] + 0.5 * np.arange(H)[:, None]
        pos = ccx - 700 + 1400 * clamp((k + 9) / 10, 0, 1)
        band = np.exp(-((xs - pos) / 60.0) ** 2)[..., None]
        lw[..., :3] = np.clip(lw[..., :3] + band * 0.5, 0, 1)
    glow = cv2.GaussianBlur(lw[..., 3], (0, 0), 20)[..., None] * 0.35 * v
    out = out + glow * 0.8
    al = lw[..., 3:4] * v * clamp(1 - (sc - 6) / 6, 0, 1)        # the ring fades as we pass through it
    out = out * (1 - al) + lw[..., :3] * al
    if sc > 1.5: out = radial_blur(out, ccx, ccy, 1.0, 1.0 + 0.06 * min(1, sc / 10), 4)
    return np.clip(out, 0, 1)

# ---- through-the-photo
def photo_through(A, B, k, s, f):
    """k: -10..0 (last frames of the photos shot). The photo on the wall fills with B and the camera flies into it."""
    q = np.float32([to_screen(s, f, x, y)[:2] for x, y in s["photo"]])
    c = q.mean(0); u = (k + 10) / 10.0
    qw, qh = np.linalg.norm(q[1] - q[0]), np.linalg.norm(q[3] - q[0])
    s_end = max(W / qw, H / qh) * 1.15
    sc = math.exp(math.log(s_end) * ein(u, 2.0))
    Mz = cv2.getRotationMatrix2D((float(c[0]), float(c[1])), 0, sc); Mz[0, 2] += (W / 2 - c[0]) * ein(u, 2); Mz[1, 2] += (H / 2 - c[1]) * ein(u, 2)
    Az = cv2.warpAffine(A, Mz, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    qz = (np.hstack([q, np.ones((4, 1), np.float32)]) @ Mz.T).astype(np.float32)
    P = cv2.getPerspectiveTransform(np.float32([[0, 0], [W, 0], [W, H], [0, H]]), qz)
    Bq = cv2.warpPerspective(B, P, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
    mq = cv2.warpPerspective(np.ones((H, W), np.float32), P, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)[..., None]
    a = clamp(u * 2.5, 0, 1)
    out = Az * (1 - mq * a) + Bq * mq * a
    edge = cv2.morphologyEx(mq[..., 0], cv2.MORPH_GRADIENT, np.ones((9, 9), np.uint8))[..., None] * a * (1 - ein(u, 3))
    out = out * (1 - edge) + 0.95 * edge
    return radial_blur(out, W / 2, H / 2, 1.0, 1.0 + 0.05 * u, 4) if u > 0.3 else out

# ---- dark pass (fly into his shadow, come out of black)
def darkpass_out(img, k):          # k = -8..-1
    u = (k + 9) / 9.0; sc = 1 + 3.0 * ein(u, 2.2)
    o = radial_blur(img, W / 2, H * 0.60, sc, sc * (1 + 0.10 * u), 5)
    L = o.mean(2, keepdims=True); thr = 0.05 + 0.55 * ein(u, 1.6)
    return o * np.clip((L - thr) / 0.25, 0, 1) * (1 - 0.6 * u)
def darkpass_in(img, k):           # k = 0..8
    u = 1 - k / 9.0; sc = 1 + 1.4 * u * u
    o = radial_blur(img, W / 2, H * 0.42, sc * 1.05, sc, 5)
    return o * (1 - 0.85 * u * u)

# ---- roll (3D roll with motion blur)
def roll(img, ang0, ang1, z, n=5):
    acc = None
    for i in range(n):
        a = ang0 + (ang1 - ang0) * i / (n - 1)
        w = zoom_about(img, W / 2, H / 2, z, a)
        acc = w if acc is None else acc + w
    return acc / n

# ---- iris (open) and pupil (close) — the loop seam
def iris_open(img, f, s):
    k = f - s["f0"]
    if k >= 22: return img
    t, u, _ = src_time(s, f); fa = face_at(s, t)
    cx, cy = (to_screen(s, f, fa[0], fa[1])[:2] if fa else (W / 2, H * 0.4))
    r = (math.hypot(W, H) * 1.05) * ein(k / 22, 1.7)
    yy, xx = np.ogrid[:H, :W]
    m = np.clip((r - np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)) / 30.0, 0, 1).astype(np.float32)[..., None]
    z = 1 + 0.25 * (1 - eout(k / 22, 3))
    return zoom_about(img, cx, cy, z) * m

def pupil_close(img, f, s):
    kk = s["f1"] - f
    n = 34
    if kk > n: return img
    u = 1 - kk / n
    t, _, _ = src_time(s, f); fa = face_at(s, t)
    if fa:
        lx, ly, rx, ry = fa[3]; ex, ey, _ = to_screen(s, f, lx, ly)
    else:
        ex, ey = W / 2, H * 0.37
    sc = math.exp(3.3 * ein(u, 2.2))
    o = radial_blur(img, ex, ey, sc, sc * (1 + 0.05 * u), 5)
    o = cv2.warpAffine(o, np.float32([[1, 0, (W / 2 - ex) * ein(u, 2)], [0, 1, (H * 0.42 - ey) * ein(u, 2)]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    return o * (1 - ein(clamp((u - 0.55) / 0.45, 0, 1), 1.4))

# ============================================================================ v5 additions
# ---- BAY HARBOR BUTCHER: footage-in-letters knockout
_KO = {}
def ko_masks():
    if "m" in _KO: return _KO
    words = [w for w, _ in E.BHB]; ms = []
    for w in words:
        m = text_mask(w, F_BLACK, 200, tracking=-2)
        sc = min(940 / m.shape[1], 360 / m.shape[0])
        ms.append(cv2.resize(m, (int(m.shape[1] * sc), int(m.shape[0] * sc)), interpolation=cv2.INTER_AREA))
    gap = 26; tot = sum(m.shape[0] for m in ms) + gap * (len(ms) - 1); y = 880 - tot / 2
    full = []
    for m in ms:
        F = np.zeros((H, W), np.float32); x0 = int((W - m.shape[1]) / 2); y0 = int(y)
        F[y0:y0 + m.shape[0], x0:x0 + m.shape[1]] = m
        full.append((F, (W / 2, y0 + m.shape[0] / 2))); y += m.shape[0] + gap
    _KO["m"] = full; return _KO

def knockout(out, f, s):
    t = f / FPS
    times = [E.d2e(0, ws) for _, ws in E.BHB]
    t_on, t_exit, t_end = times[0] - 0.08, s["t1"] - 0.30, s["t1"]
    if not (t_on <= t < t_end): return out
    K = ko_masks()["m"]
    dark = clamp((t - t_on) / 0.10, 0, 1)
    ex = ein((t - t_exit) / (t_end - t_exit), 2.2) if t >= t_exit else 0.0
    inside = np.zeros((H, W), np.float32); red = np.zeros((H, W), np.float32)
    for i, ((F, (cx, cy)), ti) in enumerate(zip(K, times)):
        k = (t - ti) * FPS
        if k < -1: continue
        v = eout((k + 1) / 7, 3)
        sc = (1.30 - 0.30 * v) * (1 + 7.0 * ex)
        M = cv2.getRotationMatrix2D((cx, 880 if ex > 0 else cy), 0, sc)
        m = cv2.warpAffine(F, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
        if v < 1: m = cv2.GaussianBlur(m, (0, 0), 0.1 + 5 * (1 - v))
        m *= v
        inside = np.maximum(inside, m)
        if i == 2: red = np.maximum(red, m)
    if ex > 0: inside = np.maximum(inside, clamp((ex - 0.55) / 0.45, 0, 1))
    bg = cv2.GaussianBlur(out, (0, 0), 9) * (1 - 0.82 * dark * (1 - ex))
    fg = np.clip(zoom_about(out, W / 2, 880, 1.04) * 2.1, 0, 1) ** 0.8
    fg = fg * (1 - red[..., None]) + np.clip(fg.mean(2, keepdims=True) * np.array([0.30, 0.30, 1.45], np.float32) + np.array([0.02, 0.02, 0.18], np.float32), 0, 1) * red[..., None]
    o = bg * (1 - inside[..., None]) + fg * inside[..., None]
    edge = np.clip(cv2.dilate(inside, np.ones((5, 5), np.uint8)) - inside, 0, 1)[..., None] * (1 - ex)
    return np.clip(o * (1 - edge) + 0.92 * edge, 0, 1)

# ---- BLEED IT: outline draws in on "then I", fills with blood on "bleed", drips; baked into the shatter
_BL = {}
def bleed_assets():
    if "m" in _BL: return _BL
    m = text_mask("BLEED IT", F_BLACK, 200, tracking=-2)
    sc = 960 / m.shape[1]; m = cv2.resize(m, (960, int(m.shape[0] * sc)), interpolation=cv2.INTER_AREA)
    pad = 360; M = np.zeros((m.shape[0] + pad, m.shape[1] + 40), np.float32); M[:m.shape[0], 20:20 + m.shape[1]] = m
    al = (M > 0.5).astype(np.uint8)
    cols = np.where(al[:m.shape[0]].any(0))[0]; rng = np.random.default_rng(13)
    bottoms = {x: int(np.max(np.where(al[:m.shape[0], x])[0])) for x in cols}
    drips = [dict(x=int(x), y=bottoms[int(x)] - 4, w=int(rng.integers(7, 15)), L=int(rng.integers(60, 300)), d=float(rng.uniform(0, 10)))
             for x in sorted(rng.choice(cols, 14, replace=False))]
    _BL.update(m=M, h=m.shape[0], drips=drips, x0=(W - M.shape[1]) // 2, y0=int(1120 - m.shape[0] / 2))
    return _BL

def bleed_layer(t):
    """RGBA layer (W-cropped) of BLEED IT at edit time t, or None."""
    B = bleed_assets(); m = B["m"]; hh = B["h"]
    t_out = E.s2e(16.40); t_fill = E.s2e(16.78)
    if t < t_out: return None
    ko = (t - t_out) * FPS; kf = (t - t_fill) * FPS
    a_out = eout(ko / 8, 3)
    outline = np.clip(cv2.dilate(m, np.ones((7, 7), np.uint8)) - cv2.erode(m, np.ones((3, 3), np.uint8)), 0, 1) * a_out
    fill = np.zeros_like(m)
    if kf > 0:
        lvl = int(hh * eout(kf / 8, 2)); fill[:lvl] = m[:lvl]
        # wavy liquid front
        if lvl < hh:
            xs = np.arange(m.shape[1]); front = lvl + (6 * np.sin(xs / 23 + kf)).astype(int)
            yy = np.arange(m.shape[0])[:, None]; fill = np.where(yy < front[None, :], m, 0).astype(np.float32)
        dm = np.zeros(m.shape, np.uint8)
        for d in B["drips"]:
            L = int(d["L"] * eout((kf - 4 - d["d"]) / 26, 2))
            if L > 2:
                cv2.line(dm, (d["x"], d["y"]), (d["x"], d["y"] + L), 255, max(2, int(d["w"] * 0.7)), cv2.LINE_AA)
                cv2.circle(dm, (d["x"], d["y"] + L), int(d["w"] * 0.8) + 1, 255, -1, cv2.LINE_AA)
        fill = np.maximum(fill, dm.astype(np.float32) / 255)
    b = cv2.GaussianBlur(fill, (0, 0), 4)
    gy = cv2.Sobel(b, cv2.CV_32F, 0, 1, ksize=3); gx = cv2.Sobel(b, cv2.CV_32F, 1, 0, ksize=3)
    d = -(gx * -0.45 + gy * -0.85) * 6
    shade = np.clip(0.72 + 1.5 * d, 0.40, 1.15)
    spec = np.clip(d * 5 - 0.6, 0, 1) ** 4 * 0.6
    col = RED[None, None, :] * 0.85 * shade[..., None] + spec[..., None]
    col = col * fill[..., None] + WHITE * outline[..., None] * (1 - fill[..., None])
    al = np.maximum(fill, outline)
    sh = cv2.GaussianBlur(np.maximum(fill, outline), (0, 0), 14) * 0.7
    rgba = np.zeros(m.shape + (4,), np.float32); rgba[..., 3] = sh
    rgba[..., :3] = col * al[..., None] / np.maximum(np.maximum(al, sh)[..., None], 1e-4)
    rgba[..., 3] = np.maximum(al, sh)
    return rgba

def draw_bleed(out, t):
    L = bleed_layer(t)
    if L is None: return out
    B = bleed_assets()
    vg = np.zeros((H, W), np.float32); cv2.ellipse(vg, (W // 2, 1120), (620, 300), 0, 0, 360, 1.0, -1)
    vg = cv2.GaussianBlur(vg, (0, 0), 80)[..., None] * 0.55 * clamp((t - E.s2e(16.40)) * FPS / 8, 0, 1)
    out = out * (1 - vg)
    return paste(out, L, B["x0"], B["y0"])

# ---- matched-angle morph (dex_hate -> dex_right): optical-flow warp + blend
_DISM = None
def morph(A, B, v):
    global _DISM
    if _DISM is None: _DISM = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    a = cv2.cvtColor((cv2.resize(A, (W // 4, H // 4)) * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
    b = cv2.cvtColor((cv2.resize(B, (W // 4, H // 4)) * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
    Fab = cv2.resize(_DISM.calc(a, b, None), (W, H)) * 4; Fba = cv2.resize(_DISM.calc(b, a, None), (W, H)) * 4
    gy, gx = np.mgrid[0:H, 0:W].astype(np.float32)
    Aw = cv2.remap(A, gx - v * Fba[..., 0], gy - v * Fba[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    Bw = cv2.remap(B, gx - (1 - v) * Fab[..., 0], gy - (1 - v) * Fab[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    o = Aw * (1 - v) + Bw * v
    pulse = math.sin(math.pi * v) ** 1.5
    o = radial_blur(o, W / 2, H * 0.37, 1.0 + 0.04 * pulse, 1.0 + 0.10 * pulse, 5)
    return np.clip(o * (1 + 0.6 * pulse) + 0.32 * pulse, 0, 1)

# ---- knife slash
SL_C = (W * 0.5, H * 0.44); SL_ANG = math.radians(-62)
_SLG = {}
def slash_geom():
    if "d" not in _SLG:
        gy, gx = np.mgrid[0:H, 0:W].astype(np.float32)
        tx, ty = math.cos(SL_ANG), math.sin(SL_ANG); nx, ny = -ty, tx
        _SLG.update(d=(gx - SL_C[0]) * nx + (gy - SL_C[1]) * ny, a=(gx - SL_C[0]) * tx + (gy - SL_C[1]) * ty, t=(tx, ty), n=(nx, ny))
    return _SLG

def slash_out(A, kn):        # kn = -7..-1: the blade glint sweeps across
    G = slash_geom(); u = eout((kn + 8) / 6, 3)
    L = math.hypot(W, H) * 0.6; head = -L + 2 * L * u
    line = np.exp(-(G["d"] / 2.2) ** 2) * (G["a"] < head) * (G["a"] > head - 900)
    glow = np.exp(-(G["d"] / 18) ** 2) * (G["a"] < head) * (G["a"] > head - 900) * 0.6
    o = A * (1 - 0.15 * u)
    o = o + glow[..., None] * np.array([0.25, 0.25, 0.95], np.float32) + line[..., None] * 1.2
    if kn >= -2: o = o + np.exp(-(G["d"] / 3.0) ** 2)[..., None] * 0.9
    return np.clip(o, 0, 1)

def slash_in(A, B, k):       # k = 0..11: the two halves of A slide apart along the cut
    G = slash_geom(); u = eout(k / 11, 2.2)
    tx, ty = G["t"]; nx, ny = G["n"]
    sep = 30 + 900 * u; slide = 700 * u
    Bz = zoom_about(B, W / 2, H * 0.44, 1.18 - 0.18 * eout(k / 11, 3))
    o = Bz.copy()
    for side in (1, -1):
        dx = side * (nx * sep + tx * slide); dy = side * (ny * sep + ty * slide)
        Ah = cv2.warpAffine(A, np.float32([[1, 0, dx], [0, 1, dy]]), (W, H), borderValue=(0, 0, 0))
        m = (G["d"] * side > 0).astype(np.float32)
        mh = cv2.warpAffine(m, np.float32([[1, 0, dx], [0, 1, dy]]), (W, H), borderValue=0)
        if k < 6: Ah = cv2.filter2D(Ah, -1, np.ones((1, 15), np.float32) / 15) * 0.5 + Ah * 0.5
        edge = np.clip(cv2.morphologyEx(mh, cv2.MORPH_GRADIENT, np.ones((7, 7), np.uint8)), 0, 1)[..., None]
        o = o * (1 - mh[..., None]) + Ah * mh[..., None]
        o = o * (1 - edge) + np.array([0.20, 0.20, 0.95], np.float32) * edge * (1 - u) + o * edge * u
    if k < 4: o = np.clip(o + np.exp(-(G["d"] / (6 + 12 * k)) ** 2)[..., None] * (0.8 - 0.2 * k), 0, 1)
    return np.clip(o, 0, 1)


# ============================================================================ finishing
_GR = None
def grain(f, amt=0.018):
    global _GR
    if _GR is None:
        rng = np.random.default_rng(3)
        _GR = [cv2.resize(rng.standard_normal((H // 2, W // 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR) for _ in range(6)]
    return _GR[f % 6][..., None] * amt

_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.30 * np.clip(np.sqrt(((_xx - W / 2) / (W / 2)) ** 2 * 0.9 + ((_yy - H / 2) / (H / 2)) ** 2) / 1.3, 0, 1) ** 2.0)[..., None].astype(np.float32)
del _yy, _xx

def bloom(out, amt=0.22):
    small = cv2.resize(out, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi = cv2.GaussianBlur(np.clip(small - 0.62, 0, 1) * 2.2, (0, 0), 9)
    return np.clip(out + cv2.resize(hi, (W, H), interpolation=cv2.INTER_LINEAR) * amt, 0, 1)

# ============================================================================ frame
def nxt_of(s):
    i = SHOTS.index(s); return SHOTS[i + 1] if i + 1 < len(SHOTS) else None

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    person = None
    # ---- drop: muzzle flash, cracks, shatter (unchanged design)
    if s["n"] == "night_walk" and k < 26:
        if "frz" not in _SH:
            bs = by_name("barrel"); fz = sample("dk", 95.64).astype(np.float32) / 255
            t, u, _ = src_time(bs, bs["f1"] - 1); cx, cy, ch = frame_geom(bs, bs["f1"] - 1, t, u); cw = ch * 9 / 16
            M = np.float32([[W / cw, 0, -(cx - cw / 2) * W / cw], [0, H / ch, -(cy - ch / 2) * H / ch]])
            _SH["frz"] = np.clip(cv2.warpAffine(grade(fz, bs, bs["f1"] - 1), M, (W, H), flags=cv2.INTER_CUBIC) * 1.25, 0, 1)
            _SH["frz"] = draw_bleed(_SH["frz"], E.te(E.DROP_HB) - 0.5 / FPS)
        A = _SH["frz"]
        if k < 2: out = np.clip(A * (1 + 2.5 * (1 - k / 2)) + (1 - k / 2) * 0.6, 0, 1)
        elif k < 5: out = crack_overlay(A, clamp((k - 1) / 2, 0, 1))
        else:
            B = render_shot(s, f); shards(); out = shatter(crack_overlay(A, 1.0), B, k - 5)
            if k - 5 < 3: out = np.clip(out + (1 - (k - 5) / 3) * 0.35, 0, 1)
    else:
        if s.get("seg"):
            out, person = render_shot(s, f, want_mask=True)
        elif s.get("scope"):
            dx, dy = scope_sway(s, f); out = render_shot(s, f)
            out = cv2.warpAffine(out, np.float32([[1, 0, dx], [0, 1, dy]]), (W, H), borderMode=cv2.BORDER_REFLECT)
        else:
            out = render_shot(s, f)
        if s.get("morph_to"):
            B = render_shot(by_name(s["morph_to"]), by_name(s["morph_to"])["f0"], False)
            out = morph(out, B, smooth((k + 1) / (s["f1"] - s["f0"] + 1)))
        tin = s.get("tin"); tout = s.get("tout")
        P = prev_shot(s)
        # ---- incoming transitions
        if tin == "iris": out = iris_open(out, f, s)
        elif tin == "dissolve" and k < 9:
            A = last_frame_of(P); v = smooth(k / 9)
            out = A * (1 - v) + out * v
        elif tin == "scope_in" and k < 14:
            out = radial_blur(out, W / 2, H * 0.42, 1 + 0.8 * (1 - eout(k / 14)), 1 + 0.7 * (1 - eout(k / 14)), 5) * eout(k / 8, 2)
        elif tin == "darkpass" and k < 9: out = darkpass_in(out, k)
        elif tin == "eye": out = eye_portal(out, f, s)
        elif tin == "roll" and k < 9:
            u = 1 - k / 9; out = roll(out, -85 * u * u, -85 * max(0, u - 0.12) ** 2, 1 + 0.45 * u * u)
        elif tin == "logo" and k < 11:
            out = logo_through(last_frame_of(P), out, k)
        elif tin == "slash" and k < 12:
            out = slash_in(last_frame_of(P), out, k)
        elif tin == "cube" and k < 7:
            A = last_frame_of(P); out = cube(A, out, eout((k + 1) / 7, 2))
        elif tin == "photo" and k < 8:
            u = 1 - k / 8; out = radial_blur(out, W / 2, H / 2, 1 + 0.25 * u * u, 1 + 0.25 * max(0, u - 0.12) ** 2, 4)
        elif tin == "polaroid": out = polaroid(out, f, s)
        elif tin == "zoomblur" and k < 8:
            u = 1 - k / 8; out = radial_blur(out, W / 2, H * 0.42, 1 + 0.6 * u * u, 1 + 0.6 * max(0, u - 0.12) ** 2, 6)
        elif tin == "datamosh" and k < 11: out = datamosh(s, f)
        elif tin == "split" and k < 12: out = split_slam(last_frame_of(P), out, k)
        elif tin in ("flash", "cut_rgb") and k < 6:
            fl = [0.9, 0.5, 0.22, 0.08, 0, 0][k] if tin == "flash" else [0.4, 0.15, 0, 0, 0, 0][k]
            out = np.clip(out * (1 + 1.5 * fl) + fl * 0.45, 0, 1)
            out = rgb_split(out, (24 if tin == "cut_rgb" else 14) * math.exp(-k / 2))
            if tin == "flash": out = zoom_about(out, W / 2, H / 2, 1 + 0.08 * math.exp(-k / 2.5))
        # ---- outgoing transitions (start before the cut)
        if tout == "barrel" and kn >= -11:
            bx, by, _ = to_screen(s, f, *s["barrel"]); u = (kn + 12) / 12.0; sc = math.exp(3.4 * ein(u, 2.3))
            out = radial_blur(out, bx, by, sc, sc * (1 + 0.12 * u), 6)
            out = cv2.warpAffine(out, np.float32([[1, 0, (W / 2 - bx) * ein(u, 2)], [0, 1, (H * 0.42 - by) * ein(u, 2)]]), (W, H), borderMode=cv2.BORDER_REFLECT)
            out = out * (1 - ein(clamp((u - 0.5) / 0.5, 0, 1), 1.5))
        if tout == "darkpass" and kn >= -8: out = darkpass_out(out, kn)
        if tout == "slash" and kn >= -7: out = slash_out(out, kn)
        if tout == "eye" and kn >= -7: out = eye_portal(out, f, n_)
        if tout == "roll" and kn >= -6:
            u = (kn + 7) / 7; out = roll(out, 95 * ein(u, 2.2) - 14 * u, 95 * ein(u, 2.2), 1 + 0.45 * ein(u, 2))
        if tout == "logo" and kn >= -12:
            out = logo_through(out, render_shot(n_, n_["f0"], False), kn)
        if tout == "photo" and kn >= -10:
            out = photo_through(out, render_shot(n_, n_["f0"], False), kn, s, f)
        if tout == "zoomblur" and kn >= -5:
            u = (kn + 6) / 6; out = radial_blur(out, W / 2, H * 0.42, 1 + 0.6 * (u - 0.17) ** 2, 1 + 0.6 * u * u, 6)
        if tout == "whiteflash" and kn >= -5:
            u = (kn + 6) / 6; out = np.clip(out * (1 + 2.0 * u * u) + 0.5 * u ** 3, 0, 1)
        if tout == "pupil": out = pupil_close(out, f, s)
        if s.get("echo"):
            acc = out.copy(); wsum = 1.0
            for j, wgt in ((4, 0.30), (8, 0.16), (12, 0.08)):
                if f - j >= s["f0"]: acc = acc + render_shot(s, f - j) * wgt; wsum += wgt
            out = np.clip(acc / wsum * 1.05, 0, 1)
        if s.get("freeze"):
            u = k / max(1, s["f1"] - s["f0"]); L = out.mean(2, keepdims=True)
            out = out + (L - out) * (0.85 * eout(u * 2)); out = out * (1 - 0.25 * eout(u))
        if s.get("scope"): out = scope_overlay(out, f, s)
    # ---- graphics
    if s["n"] == "bhb_close" and person is not None:
        PERSON_IMG[0] = out.copy(); out = bhb_title(out, f, s, person)
    if s.get("knockout"): out = knockout(out, f, s)
    if E.s2e(16.40) <= f / FPS and f < E.fh(E.DROP_HB): out = draw_bleed(out, f / FPS)
    out = lyric_layer(out, f, None)
    out = captions(out, f)
    if s.get("look") == "cine": out = bloom(out, 0.22)
    out = out * VIG + grain(f, 0.020 if s.get("look") == "night" else 0.014)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)

# ============================================================================ v5: The Flash — speed-force toolkit
GOLD = np.array([0.30, 0.78, 1.00], np.float32)      # BGR lightning gold
EMBER = np.array([0.10, 0.38, 1.00], np.float32)     # BGR speed-force orange
ICE = np.array([1.00, 0.85, 0.55], np.float32)       # BGR cold blue spark

def bolt_points(p0, p1, seed, rough=0.22, depth=7):
    rng = np.random.default_rng(seed); pts = [np.array(p0, np.float32), np.array(p1, np.float32)]
    for d in range(depth):
        new = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            m = (a + b) / 2; v = b - a; n = np.array([-v[1], v[0]], np.float32)
            m = m + n * rng.normal(0, rough / (1.4 ** d))
            new += [m, b]
        pts = new
    return np.array(pts, np.float32)

def draw_bolt(img_shape, pts, seed, branch=4, width=3):
    """returns float mask (core) and glow for a bolt polyline with a few branches."""
    core = np.zeros(img_shape, np.uint8); rng = np.random.default_rng(seed + 99)
    cv2.polylines(core, [pts.astype(np.int32)], False, 255, width, cv2.LINE_AA)
    for j in range(branch):
        i = int(rng.integers(len(pts) // 6, len(pts) - 5)); p0 = pts[i]
        ang = rng.uniform(-1.2, 1.2) + math.atan2(*(pts[-1] - pts[0])[::-1])
        L = rng.uniform(80, 260); p1 = p0 + L * np.array([math.cos(ang), math.sin(ang)], np.float32)
        bp = bolt_points(p0, p1, seed + j * 7, 0.25, 5)
        cv2.polylines(core, [bp.astype(np.int32)], False, 200, max(1, width - 1), cv2.LINE_AA)
    c = core.astype(np.float32) / 255
    small = cv2.resize(c, (img_shape[1] // 4, img_shape[0] // 4), interpolation=cv2.INTER_AREA)
    glow = cv2.resize(cv2.GaussianBlur(small, (0, 0), 4) * 3.0 + cv2.GaussianBlur(small, (0, 0), 14) * 4.0,
                      (img_shape[1], img_shape[0]), interpolation=cv2.INTER_LINEAR)
    return c, np.clip(glow, 0, 1.5)

def add_light(out, core, glow, col=GOLD, a=1.0):
    return np.clip(out + glow[..., None] * col * 0.9 * a + core[..., None] * a * 1.2, 0, 1)

# ---- lightning-strike open (from black) — also the loop entry
_BO = {}
def bolt_open(img, k):
    if k >= 20: return img
    if "pts" not in _BO:
        _BO["pts"] = bolt_points((W * 0.62, -40), (W * 0.40, H + 40), 5, 0.20, 8)
        m = np.zeros((H, W), np.uint8); cv2.polylines(m, [_BO["pts"].astype(np.int32)], False, 255, 3)
        _BO["dist"] = cv2.distanceTransform(255 - m, cv2.DIST_L2, 5).astype(np.float32)
        _BO["core"], _BO["glow"] = draw_bolt((H, W), _BO["pts"], 5, 6, 4)
    if k < 2:
        o = np.zeros_like(img)
        return add_light(o, _BO["core"] * (k + 1) / 2, _BO["glow"] * (k + 1) / 2)
    r = 1600 * ein((k - 2) / 16, 1.7)
    m = np.clip((r - _BO["dist"]) / 40.0, 0, 1)[..., None]
    rim = np.clip(1 - np.abs(_BO["dist"] - r) / 30.0, 0, 1)[..., None] * (1 - clamp((k - 2) / 16, 0, 1))
    o = img * m + rim * EMBER * 0.9
    fl = max(0.0, 0.5 - (k - 2) * 0.12)
    o = add_light(o, _BO["core"], _BO["glow"], GOLD, clamp(1 - (k - 2) / 8, 0, 1))
    return np.clip(o + fl, 0, 1)

# ---- lightning split (A tears apart along a jagged bolt, B behind)
def bolt_split(A, B, k, seed=11):
    key = ("bs", seed)
    if key not in _BO:
        pts = bolt_points((W * 0.55, -40), (W * 0.45, H + 40), seed, 0.18, 8)
        poly = np.vstack([pts, [[-200, H + 40], [-200, -40]]]).astype(np.int32)
        left = np.zeros((H, W), np.uint8); cv2.fillPoly(left, [poly], 255)
        core, glow = draw_bolt((H, W), pts, seed, 5, 4)
        _BO[key] = (left.astype(np.float32) / 255, core, glow)
    left, core, glow = _BO[key]
    if k < 0:                                                    # kn -5..-1: the bolt strikes on A
        a = clamp((k + 6) / 5, 0, 1)
        return add_light(A * (1 - 0.15 * a), core, glow, GOLD, a)
    u = eout(k / 12, 2.4); sep = int(40 + 700 * u)
    Bz = zoom_about(B, W / 2, H * 0.44, 1.15 - 0.15 * eout(k / 12, 3))
    o = Bz.copy()
    for side, m in ((-1, left), (1, 1 - left)):
        M = np.float32([[1, 0, side * sep], [0, 1, 0]])
        Ah = cv2.warpAffine(A, M, (W, H), borderValue=(0, 0, 0)); mh = cv2.warpAffine(m, M, (W, H), borderValue=0)[..., None]
        o = o * (1 - mh) + Ah * mh
        cg = cv2.warpAffine(glow, M, (W, H)); o = np.clip(o + cg[..., None] * EMBER * 0.8 * (1 - u), 0, 1)
    return np.clip(o + max(0.0, 0.45 - 0.09 * k), 0, 1)

# ---- speed-force tunnel (fly through streaks of light)
_TUN = {}
def streak_layer(f, strength, cx=W / 2, cy=H * 0.45):
    if "pol" not in _TUN:
        rng = np.random.default_rng(3); R, A = 900, 720
        pol = np.zeros((A, R), np.float32)
        for _ in range(1400):
            a = int(rng.integers(0, A)); r0 = int(rng.uniform(20, R)); L = int(rng.uniform(60, 420)); wdt = int(rng.integers(1, 4))
            pol[a:a + wdt, r0:min(R, r0 + L)] += rng.uniform(0.25, 1.0)
        pol = cv2.GaussianBlur(pol, (0, 0), sigmaX=3.0, sigmaY=1.2)
        _TUN["pol"] = pol
        hue = rng.random(A) < 0.25
        _TUN["hue"] = hue
    pol = np.roll(_TUN["pol"], int(f * 37) % 900, axis=1)
    lin = cv2.warpPolar(pol, (W, H), (cx, cy), 1300, cv2.WARP_POLAR_LINEAR | cv2.WARP_INVERSE_MAP)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); rr = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    fall = np.clip(rr / 300, 0, 1)
    return np.clip(lin * fall * strength, 0, 1.5)

def tunnel(out, f, k, side):
    """side 'out': k=-10..-1 accelerate in; side 'in': k=0..11 decelerate out."""
    if side == "out":
        u = (k + 11) / 11.0; sc = 1 + 1.6 * ein(u, 2.2); st_ = ein(u, 1.5) * 0.85
    else:
        u = 1 - k / 12.0; sc = 1 + 1.2 * ein(u, 2.0); st_ = ein(u, 1.4) * 0.85
    o = radial_blur(out, W / 2, H * 0.45, sc, sc * (1 + 0.10 * u), 6)
    sl = streak_layer(f, st_)
    core = np.clip(sl - 0.6, 0, 1)[..., None]
    o = o * (1 - 0.35 * st_ / 1.4) + sl[..., None] * (GOLD * 0.75 + EMBER * 0.25) + core * 0.8 + (sl[..., None] * 0.30 * ICE if side == "in" else 0)
    if (side == "out" and k >= -2) or (side == "in" and k < 2):
        o = o + (0.55 if abs(k) < 1 else 0.3)
    return np.clip(o, 0, 1)

# ---- molecular phase (vibrate out / in)
def phase(img, f, amt):
    if amt <= 0.01: return img
    rng = np.random.default_rng(f * 13 + 1); acc = np.zeros_like(img)
    for j in range(4):
        dx, dy = rng.normal(0, 22 * amt, 2); M = np.float32([[1, 0, dx], [0, 1, dy]])
        acc += cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    o = acc / 4
    o = rgb_split(o, 18 * amt); o = o * (1 - 0.15 * amt) + np.clip(o - 0.55, 0, 1) * 1.4 * amt * GOLD
    return np.clip(o, 0, 1)

# ---- twirl (time vortex)
_TW = {}
def twirl(img, ang):
    if "g" not in _TW:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); cx, cy = W / 2, H * 0.45
        _TW.update(g=(xx - cx, yy - cy, np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2), cx, cy))
    dx, dy, r, cx, cy = _TW["g"]; th_ = ang * np.exp(-r / 520)
    c, s_ = np.cos(th_), np.sin(th_)
    return cv2.remap(img, (cx + dx * c - dy * s_).astype(np.float32), (cy + dx * s_ + dy * c).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

# ---- crawling arcs (electric accents on high-energy shots)
def arcs(out, f, s):
    rng = np.random.default_rng(f // 3 * 7 + 5)
    if rng.random() > 0.55: return out
    n = int(rng.integers(1, 3)); o = out
    for j in range(n):
        side = rng.integers(0, 4)
        if side == 0: p0 = (rng.uniform(0, W), -10); p1 = (p0[0] + rng.uniform(-300, 300), rng.uniform(200, 600))
        elif side == 1: p0 = (rng.uniform(0, W), H + 10); p1 = (p0[0] + rng.uniform(-300, 300), H - rng.uniform(200, 600))
        elif side == 2: p0 = (-10, rng.uniform(0, H)); p1 = (rng.uniform(150, 450), p0[1] + rng.uniform(-300, 300))
        else: p0 = (W + 10, rng.uniform(0, H)); p1 = (W - rng.uniform(150, 450), p0[1] + rng.uniform(-300, 300))
        pts = bolt_points(p0, p1, int(f // 3) * 11 + j, 0.25, 6)
        core, glow = draw_bolt((H, W), pts, int(f // 3) * 11 + j, 2, 2)
        o = add_light(o, core * 0.8, glow * 0.7, GOLD if (f // 3 + j) % 3 else ICE, 0.9)
    return o

# ---- final: fly into Barry's eye -> streaks collapse -> black (loop exit)
def eye_out(img, f, s):
    n = 30; kk = s["f1"] - f
    if kk > n: return img
    u = 1 - kk / n
    t, _, _ = src_time(s, f); fa = face_at(s, t)
    if fa: ex, ey, _ = to_screen(s, f, fa[3][0], fa[3][1])
    else: ex, ey = W / 2, H * 0.38
    sc = math.exp(3.0 * ein(u, 2.2))
    o = radial_blur(img, ex, ey, sc, sc * (1 + 0.06 * u), 5)
    o = cv2.warpAffine(o, np.float32([[1, 0, (W / 2 - ex) * ein(u, 2)], [0, 1, (H * 0.45 - ey) * ein(u, 2)]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    sl = streak_layer(f, 1.3 * math.sin(math.pi * clamp(u * 1.2, 0, 1)))
    o = np.clip(o + sl[..., None] * GOLD, 0, 1)
    return o * (1 - ein(clamp((u - 0.6) / 0.4, 0, 1), 1.3))

# ---- logo through the 'o', with a lightning arc tracing the letters
def logo_flash(A, B, k):
    o = logo_through(A, B, k)
    if -12 <= k < -3:
        L = logo_assets(); h = L["h"]; X0, Y0 = (W - E.LOGO_W) // 2, int(H * 0.44 - h / 2)
        al = (L["rgba"][..., 3] > 0.5).astype(np.uint8)
        edge = cv2.morphologyEx(al, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(np.float32)
        u = (k + 12) / 9.0; xs = np.arange(E.LOGO_W)[None, :]
        sweep = np.exp(-((xs - u * E.LOGO_W) / 90.0) ** 2) * edge
        full = np.zeros((H, W), np.float32); full[Y0:Y0 + h, X0:X0 + E.LOGO_W] = sweep
        g = cv2.GaussianBlur(full, (0, 0), 6) * 2
        o = np.clip(o + full[..., None] * 1.2 + g[..., None] * GOLD, 0, 1)
    return o

# ============================================================================ v5 typography
def title_card(out, f):
    t = f / FPS; T = E.TITLE
    if not (T["t_in"] <= t < T["t_out"] + 0.2): return out
    k = (t - T["t_in"]) * FPS; kout = (t - T["t_out"]) * FPS
    fade = 1.0 if kout <= 0 else clamp(1 - kout / 10, 0, 1)
    m = text_mask(T["text"], F_XB, 58, tracking=12)
    hh, ww = m.shape; p = eout(k / 30, 2) * (ww + 160) - 80
    reveal = np.clip((p - np.arange(ww)[None, :]) / 60, 0, 1)
    L = shadowed(m * reveal, WHITE, blur=10, sa=0.75)
    x0, y0 = int(W / 2 - L.shape[1] / 2), int(1500 - L.shape[0] / 2)
    out = paste(out, L, x0, y0, fade)
    pad = (L.shape[1] - ww) // 2
    bar = np.exp(-((np.arange(ww)[None, :] - p) / 16.0) ** 2) * (1 if p < ww + 40 else 0)
    gb = np.zeros(L.shape[:2], np.float32); gb[pad:pad + hh, pad:pad + ww] = np.repeat(bar, hh, 0)
    glow = np.zeros((L.shape[0], L.shape[1], 4), np.float32); glow[..., :3] = GOLD; glow[..., 3] = cv2.GaussianBlur(gb, (0, 0), 7)
    out = paste(out, glow, x0, y0, fade)
    # thin gold rule that draws out under the title
    rw = int(560 * eout((k - 10) / 24, 3))
    if rw > 2:
        y = y0 + L.shape[0] - 6; xa = W // 2 - rw // 2
        out[y:y + 3, xa:xa + rw] = out[y:y + 3, xa:xa + rw] * (1 - 0.9 * fade) + GOLD * 0.9 * fade
    return out

def lyric5(out, f):
    t = f / FPS
    for word, s0, s1, style in E.LYR:
        a0, a1 = E.s2e(s0), E.s2e(s1)
        if not (a0 - 0.03 <= t < a1 + 0.15): continue
        k = (t - a0) * FPS; kout = (t - a1) * FPS
        fade = 1.0 if kout <= 0 else clamp(1 - kout / 9, 0, 1)
        y = 1480; size = 150 if len(word) <= 7 else 120
        if style == "fall":                                   # letters drop in with gravity and settle
            fnt = font(F_BLACK, size); x = W / 2 - fnt.getlength(word) / 2
            for j, ch in enumerate(word):
                cw = fnt.getlength(ch); kk = k - j * 1.6
                if kk > -1:
                    v = clamp((kk + 1) / 10, 0, 1); dy = -260 * (1 - v) ** 2 + (14 * math.sin(v * math.pi * 2) * (1 - v) if v < 1 else 0)
                    L = shadowed(text_mask(ch, F_BLACK, size), WHITE, blur=10, sa=0.8)
                    if v < 1: L = hblur(L, 1) if False else L
                    out = paste(out, L, int(x + cw / 2 - L.shape[1] / 2), int(y + dy - L.shape[0] / 2), fade * clamp(v * 2, 0, 1))
                x += cw
        elif style == "fade":                                 # resolves, then dissolves into drifting sparks
            m = text_mask(word, F_BLACK, size, tracking=6)
            v = eout(k / 8, 3); mm = cv2.GaussianBlur(m, (0, 0), 0.1 + 6 * (1 - v))
            dur = (a1 - a0) * FPS
            if k > dur * 0.45:
                p = clamp((k - dur * 0.45) / (dur * 0.55), 0, 1)
                rng = np.random.default_rng(int(k)); noise_ = cv2.resize(np.random.default_rng(4).random((m.shape[0] // 4 + 1, m.shape[1] // 4 + 1)).astype(np.float32), (m.shape[1], m.shape[0]))
                mm = mm * np.clip((noise_ - p) / 0.12, 0, 1)
            L = shadowed(mm, WHITE, blur=10, sa=0.75)
            out = paste(out, L, int(W / 2 - L.shape[1] / 2), int(y - L.shape[0] / 2), fade * v)
        elif style == "drown":                                # rises through a ripple, cold blue tint
            m = text_mask(word, F_BLACK, size)
            hh, ww = m.shape; yy = np.arange(hh, dtype=np.float32)[:, None]; xx = np.arange(ww, dtype=np.float32)[None, :]
            amp = 10 * math.exp(-k / 18) + 2
            m = cv2.remap(m, (xx + amp * np.sin(yy / 9 + k * 0.5)).astype(np.float32), (yy + amp * 0.6 * np.sin(xx / 17 + k * 0.4)).astype(np.float32), cv2.INTER_LINEAR)
            v = eout(k / 12, 3)
            L = shadowed(m, np.array([1.0, 0.92, 0.78], np.float32), blur=12, sa=0.75)
            out = paste(out, L, int(W / 2 - L.shape[1] / 2), int(y + 60 * (1 - v) - L.shape[0] / 2), fade * v)
        elif style == "breathe":                              # slow inhale: scales up softly, gold glow pulse
            v = eout(k / 20, 2); sc = 0.92 + 0.12 * clamp(k / 90, 0, 1)
            m = text_mask(word, F_SB, int(170 * sc), tracking=int(30 - 14 * v))
            if v < 1: m = cv2.GaussianBlur(m, (0, 0), 0.1 + 8 * (1 - v))
            L = shadowed(m, WHITE, blur=14, sa=0.6)
            gl = np.zeros_like(L); gl[..., :3] = GOLD; gl[..., 3] = cv2.GaussianBlur(L[..., 3], (0, 0), 22) * (0.45 + 0.2 * math.sin(k * 0.12))
            x0, y0 = int(W / 2 - L.shape[1] / 2), int(y - L.shape[0] / 2)
            out = paste(out, gl, x0, y0, fade * v); out = paste(out, L, x0, y0, fade * v)
        elif style == "pre":                                  # soft lead-in line: words ease in one at a time
            fnt = font(F_SB, 54); words = word.upper().split(); sp = fnt.getlength("  ")
            wts = [s0 + j * 0.30 for j in range(len(words))]
            widths = [sum(fnt.getlength(c) + 10 for c in w_) for w_ in words]
            x = W / 2 - (sum(widths) + sp * (len(words) - 1)) / 2
            for w_, wt, wd in zip(words, wts, widths):
                kk = (t - E.s2e(wt)) * FPS
                if kk > -1:
                    v = eout((kk + 1) / 10, 3)
                    m = text_mask(w_, F_SB, 54, tracking=10)
                    if v < 1: m = cv2.GaussianBlur(m, (0, 0), 0.1 + 5 * (1 - v))
                    L = shadowed(m, WHITE * 0.92, blur=8, sa=0.7)
                    out = paste(out, L, int(x + wd / 2 - L.shape[1] / 2), int(1350 + 16 * (1 - v) - L.shape[0] / 2), v * fade * 0.95)
                x += wd + sp
        elif style == "glitch":                               # lands with an RGB tear that settles
            v = eout(k / 6, 3)
            m = text_mask(word, F_BLACK, size)
            L = shadowed(m, WHITE, blur=10, sa=0.8)
            x0, y0 = int(W / 2 - L.shape[1] / 2), int(y - L.shape[0] / 2)
            if k < 8:
                rng = np.random.default_rng(int(k) + 3); amt = 1 - k / 8
                for _ in range(4):
                    a_ = int(rng.integers(0, L.shape[0] - 20)); b_ = a_ + int(rng.integers(8, 30))
                    L[a_:b_] = np.roll(L[a_:b_], int(rng.integers(-60, 60) * amt), axis=1)
            out = paste(out, L, x0, y0, fade * v)
        elif style == "slam":                                 # LOST / IT / ALL stack, each slams on its word
            words = [("LOST", 86.92), ("IT", 87.68), ("ALL", 88.26)]; yy0 = 1330
            for w_, ws in words:
                kk = (t - E.s2e(ws)) * FPS
                if kk > -1:
                    v = eout((kk + 1) / 7, 3); sc = 1 + 0.45 * (1 - v)
                    m = text_mask(w_, F_BLACK, int(150 * sc))
                    if v < 1: m = cv2.GaussianBlur(m, (0, 0), 0.1 + 5 * (1 - v))
                    L = shadowed(m, GOLD if w_ == "ALL" else WHITE, blur=10, sa=0.8)
                    out = paste(out, L, int(W / 2 - L.shape[1] / 2), int(yy0 + 75 - L.shape[0] / 2), fade * v)
                yy0 += 150
        elif style == "streak":                               # zips in from the left with a speed trail
            v = eout(k / 9, 3)
            m = text_mask(word, F_BLACK, size, tracking=-2)
            L = shadowed(m, WHITE, blur=10, sa=0.8)
            dx = -900 * (1 - v)
            if v < 1:
                tr = L.copy(); tr[..., :3] = GOLD; tr = hblur(tr, 10 + 260 * (1 - v)); out = paste(out, tr, int(W / 2 - L.shape[1] / 2 + dx - 120 * (1 - v)), int(y - L.shape[0] / 2), fade * 0.8)
            out = paste(out, L, int(W / 2 - L.shape[1] / 2 + dx), int(y - L.shape[0] / 2), fade)
    return out

# ============================================================================ v5b: new transitions
EMB_C = (W / 2, H * 0.45); EMB_R = 300
_EM = {}
def emblem_assets():
    if "ring" in _EM: return _EM
    cx, cy = EMB_C; r = EMB_R
    ang = np.linspace(-math.pi / 2, 1.5 * math.pi, 400)
    ring = np.stack([cx + r * np.cos(ang), cy + r * np.sin(ang)], 1).astype(np.float32)
    P = np.array([(0.18, -0.92), (-0.46, 0.08), (-0.04, 0.08), (-0.20, 0.92), (0.48, -0.14), (0.05, -0.14)], np.float32)
    bolt = np.stack([cx + P[:, 0] * r, cy + P[:, 1] * r], 1)
    seg = np.vstack([bolt, bolt[:1]])
    dense = []
    for a, b in zip(seg, seg[1:]):
        n = int(np.linalg.norm(b - a) / 4) + 1
        dense += [a + (b - a) * i / n for i in range(n)]
    fill = np.zeros((H, W), np.uint8); cv2.fillPoly(fill, [bolt.astype(np.int32)], 255, cv2.LINE_AA)
    _EM.update(ring=ring, bolt=np.array(dense, np.float32), poly=bolt, fill=cv2.GaussianBlur(fill.astype(np.float32) / 255, (0, 0), 1.0))
    return _EM

def stroke_light(paths, prog, width=5):
    core = np.zeros((H, W), np.uint8)
    head = []
    for pts in paths:
        n = max(2, int(len(pts) * clamp(prog, 0, 1)))
        cv2.polylines(core, [pts[:n].astype(np.int32)], False, 255, width, cv2.LINE_AA)
        if prog < 1: head.append(pts[n - 1])
    c = core.astype(np.float32) / 255
    small = cv2.resize(c, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    glow = cv2.resize(cv2.GaussianBlur(small, (0, 0), 3) * 2.5 + cv2.GaussianBlur(small, (0, 0), 10) * 3.0, (W, H))
    for p in head:                                            # bright spark at the drawing tip
        cv2.circle(glow, (int(p[0]), int(p[1])), 18, 1.6, -1, cv2.LINE_AA)
    return c, np.clip(cv2.GaussianBlur(glow, (0, 0), 3), 0, 1.6)

def emblem_open(B, f, k):
    """k 0-22: emblem draws itself in electric gold; 22-28: bolt fills and flashes; 28-50: fly through the bolt into B."""
    if k >= 50: return B
    A = emblem_assets(); o = np.zeros_like(B)
    if k < 28:
        core, glow = stroke_light([A["ring"], A["bolt"]], eout(k / 22, 1.6))
        o = o + glow[..., None] * GOLD + core[..., None]
        if k >= 22:
            v = (k - 22) / 6; o = o + A["fill"][..., None] * (0.5 + 0.5 * v) * (WHITE * 0.7 + GOLD * 0.3)
        if k >= 8: o = arcs_around(o, f, A, 0.6)
        return np.clip(o, 0, 1)
    u = (k - 28) / 22.0; sc = math.exp(4.4 * ein(u, 2.2))
    bc = A["poly"].mean(0)
    M = cv2.getRotationMatrix2D((float(bc[0]), float(bc[1])), -8 * u, sc)
    m = cv2.warpAffine(A["fill"], M, (W, H), flags=cv2.INTER_LINEAR)
    if sc > 10: m = np.maximum(m, clamp((sc - 10) / 20, 0, 1))
    ringc, ringg = stroke_light([A["ring"]], 1.0)
    rg = cv2.warpAffine(ringg, M, (W, H)); rc = cv2.warpAffine(ringc, M, (W, H))
    Bz = zoom_about(B, W / 2, H * 0.45, 1.25 - 0.25 * eout(u, 2))
    edge = np.clip(cv2.morphologyEx(m, cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8)), 0, 1)
    o = Bz * m[..., None] + (rg[..., None] * GOLD + rc[..., None]) * (1 - u) * (1 - m[..., None])
    o = o + cv2.GaussianBlur(edge, (0, 0), 6)[..., None] * GOLD * 1.5 * (1 - u)
    if k < 32: o = o + m[..., None] * (32 - k) * 0.22 * (WHITE * 0.6 + GOLD * 0.4)   # the bolt itself flashes
    return np.clip(o, 0, 1)

def arcs_around(o, f, A, a):
    rng = np.random.default_rng(f // 2 * 3 + 1); cx, cy = EMB_C
    for j in range(2):
        t0 = rng.uniform(0, 2 * math.pi); t1 = t0 + rng.uniform(0.4, 1.0)
        p0 = (cx + (EMB_R + 8) * math.cos(t0), cy + (EMB_R + 8) * math.sin(t0)); p1 = (cx + (EMB_R + 60) * math.cos(t1), cy + (EMB_R + 60) * math.sin(t1))
        pts = bolt_points(p0, p1, f // 2 * 5 + j, 0.3, 5)
        core, glow = draw_bolt((H, W), pts, f // 2 * 5 + j, 1, 2)
        o = add_light(o, core, glow * 0.8, GOLD if j else ICE, a)
    return o

# ---- light-speed slit: frame collapses into a glowing line, next shot bursts open from it
def slit(img, closed, f):
    """closed 0 -> full frame, 1 -> a single line."""
    sy = max(0.004, 1 - ein(closed, 1.6)); sx = 1 + 0.35 * closed
    M = np.float32([[sx, 0, W / 2 * (1 - sx)], [0, sy, H * 0.5 * (1 - sy)]])
    o = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
    o = hblur(o, 4 + 160 * closed) * (1 + 1.4 * closed)
    yy = np.arange(H, dtype=np.float32)[:, None]; xx = np.arange(W, dtype=np.float32)[None, :]
    line = np.exp(-((yy - H * 0.5) / (2 + 6 * closed)) ** 2) * np.exp(-((xx - W / 2) / (W * (0.25 + 0.5 * closed))) ** 2)
    flare = np.exp(-((yy - H * 0.5) / 40) ** 2) * np.exp(-((xx - W / 2) / 260) ** 2) * closed
    return np.clip(o + (line[..., None] * 1.3 * closed + flare[..., None] * 0.7) * (WHITE * 0.5 + GOLD * 0.5), 0, 1)

# ---- speed afterimages: the shot arrives as converging time-remnants
def remnant(B, f, s, k, n=14):
    if k >= n: return B
    v = eout(k / n, 2.4); acc = B * (0.40 + 0.60 * v)
    cols = (np.array([0.20, 0.25, 1.0], np.float32), GOLD, np.array([0.25, 0.45, 1.0], np.float32), ICE)
    for j in range(4):
        d = (1 - v) * (j + 1) * 210 * (1 if j % 2 else -1)
        sh = cv2.warpAffine(B, np.float32([[1, 0, d], [0, 1, 0]]), (W, H), borderMode=cv2.BORDER_REFLECT)
        L = sh.mean(2, keepdims=True)
        acc = acc + L * cols[j] * 0.85 * (1 - v) / (1 + 0.35 * j)
    return np.clip(acc, 0, 1)

# ---- shockwave: a refracting ring of energy expands from the face and reveals the next shot
def shockwave(A, B, s, f, k, n=13):
    if k >= n: return B
    t, u, _ = src_time(s, f); fa = face_at(s, t)
    cx, cy = (to_screen(s, f, fa[0], fa[1])[:2] if fa else (W / 2, H * 0.42))
    R = 1700 * eout(k / n, 2.0)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); dx, dy = xx - cx, yy - cy; r = np.sqrt(dx * dx + dy * dy) + 1e-3
    band = np.exp(-((r - R) / 55.0) ** 2)
    disp = band * 45 * (1 - k / n)
    src = np.where((r < R)[..., None], B, A)
    o = cv2.remap(src.astype(np.float32), (xx - dx / r * disp).astype(np.float32), (yy - dy / r * disp).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    rim = np.exp(-((r - R) / 8.0) ** 2) + 0.4 * band
    return np.clip(o + rim[..., None] * (GOLD * 0.9 + WHITE * 0.3) * (1 - 0.6 * k / n), 0, 1)

def slit_end(img, f, s, n=20):
    kk = s["f1"] - f
    if kk > n: return img
    u = 1 - kk / n
    if u < 0.75: return slit(img, ein(u / 0.75, 1.3), f)
    v = (u - 0.75) / 0.25                                   # line -> spark -> black
    o = np.zeros_like(img); yy = np.arange(H, dtype=np.float32)[:, None]; xx = np.arange(W, dtype=np.float32)[None, :]
    wdt = W * 0.5 * (1 - v) + 6
    spark = np.exp(-((yy - H * 0.5) / 3) ** 2) * np.exp(-((xx - W / 2) / wdt) ** 2) * (1.6 - 1.4 * v)
    halo = np.exp(-(((yy - H * 0.5) / 60) ** 2 + ((xx - W / 2) / 60) ** 2)) * 0.8 * (1 - v)
    return np.clip(o + (spark + halo)[..., None] * (WHITE * 0.5 + GOLD * 0.5), 0, 1)


# ============================================================================ v5c: more transitions, graphics, lyric lockups
_GY, _GX = np.mgrid[0:H, 0:W].astype(np.float32)

def ring_wipe(A, B, k, n=13, c=(W / 2, H * 0.44)):
    if k >= n: return B
    u = eout(k / n, 2.2); R = 1700 * u
    r = np.sqrt((_GX - c[0]) ** 2 + (_GY - c[1]) ** 2)
    m = np.clip((R - r) / 6.0, 0, 1)[..., None]
    Bz = zoom_about(B, c[0], c[1], 1.25 - 0.25 * u)
    o = A * (1 - m) * (1 - 0.4 * u) + Bz * m
    rim = np.exp(-((r - R) / 7.0) ** 2) + 0.5 * np.exp(-((r - R) / 30.0) ** 2) + 0.25 * np.exp(-((r - R * 0.86) / 5.0) ** 2)
    return np.clip(o + rim[..., None] * (GOLD * 0.9 + WHITE * 0.25) * (1 - 0.5 * u), 0, 1)

_BW = {}
def bolt_wipe(A, B, k, n=12, seed=3):
    if k >= n: return B
    if seed not in _BW:
        pts = bolt_points((0, -40), (0, H + 40), seed, 0.16, 8); _BW[seed] = pts[:, 0] - pts[:, 0].mean(), pts[:, 1]
    bx, by = _BW[seed]; u = eout(k / n, 1.8); x0 = -150 + (W + 300) * u
    edge_x = np.interp(np.arange(H), by, bx + x0).astype(np.float32)[:, None]
    m = np.clip((edge_x - _GX) / 5.0, 0, 1)[..., None]                   # left of the bolt = B
    o = A * (1 - m) + B * m
    pts = np.stack([bx + x0, by], 1)
    core, glow = draw_bolt((H, W), pts, seed, 4, 4)
    return add_light(o, core, glow, GOLD, 1.0)

def prism(B, k, n=11):
    if k >= n: return B
    v = eout(k / n, 2.4); d = (1 - v) * 260
    o = np.zeros_like(B)
    for ch, (dx, dy) in zip(range(3), ((d, -d * 0.4), (0, d * 0.6), (-d, -d * 0.4))):
        M = cv2.getRotationMatrix2D((W / 2, H * 0.44), (1 - v) * (ch - 1) * 6, 1 + 0.2 * (1 - v)); M[0, 2] += dx; M[1, 2] += dy
        o[..., ch] = cv2.warpAffine(B[..., ch], M, (W, H), borderMode=cv2.BORDER_REFLECT)
    return np.clip(o + (1 - v) ** 2 * 0.25, 0, 1)

def smear(img, amt, f):
    if amt < 0.01: return img
    rng = np.random.default_rng(f * 3 + 7); o = img.copy()
    rows = cv2.resize(rng.random((48, 1)).astype(np.float32), (1, H), interpolation=cv2.INTER_NEAREST)[:, 0]
    for b in range(6):
        sel = (rows >= b / 6) & (rows < (b + 1) / 6)
        L = int(20 + 360 * amt * (0.4 + 0.6 * b / 5))
        sh = int(amt * 220 * (0.3 + 0.7 * b / 5))
        o[sel] = np.roll(hblur(img, L), sh, axis=1)[sel]
    return np.clip(o * (1 + 0.6 * amt) + np.clip(o - 0.6, 0, 1) * GOLD * amt, 0, 1)

# ---- ambient graphics
def embers(out, f, amount):
    if amount <= 0: return out
    rng = np.random.default_rng(77); n = int(90 * amount)
    x0 = rng.uniform(0, W, 200); y0 = rng.uniform(0, H, 200); sp = rng.uniform(2.5, 7, 200); ph = rng.uniform(0, 6.28, 200); sz = rng.uniform(1.2, 3.5, 200)
    lay = np.zeros((H // 2, W // 2), np.float32)
    for i in range(n):
        y = (y0[i] - f * sp[i]) % H; x = x0[i] + 30 * math.sin(f * 0.04 + ph[i])
        a = 0.5 + 0.5 * math.sin(f * 0.2 + ph[i])
        cv2.circle(lay, (int(x / 2), int(y / 2)), max(1, int(sz[i] / 2)), a, -1, cv2.LINE_AA)
    lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 1.2) * 2.0, (W, H))
    return np.clip(out + lay[..., None] * (GOLD * 0.8 + EMBER * 0.2) * 0.8, 0, 1)

def edge_lightning(out, f):
    h = (f / FPS) / E.HB + E.H0
    if h < 240: return out
    k = ((h - E.H0) % 4) * E.HB * FPS
    if k > 7: return out
    a = 1 - k / 7; o = out; seed = int((h - E.H0) // 4)
    for side in (0, 1):
        x = 18 if side == 0 else W - 18
        pts = bolt_points((x, -20), (x + (40 if side == 0 else -40), H + 20), seed * 2 + side, 0.05, 7)
        core, glow = draw_bolt((H, W), pts, seed * 2 + side, 3, 2)
        o = add_light(o, core * 0.8, glow * 0.7, GOLD, a * 0.9)
    return o

def light_streaks(out, f):
    rng = np.random.default_rng(f // 2); lay = np.zeros((H, W), np.float32)
    for _ in range(7):
        y = int(rng.uniform(100, H - 100)); L = int(rng.uniform(200, 700)); x = int(rng.uniform(-L, W))
        cv2.line(lay, (x, y), (x + L, y), float(rng.uniform(0.3, 1.0)), int(rng.integers(1, 3)), cv2.LINE_AA)
    lay = hblur(lay, 60) * 1.6
    return np.clip(out + lay[..., None] * GOLD * 0.7, 0, 1)

# ---- lyric lockups
CREAM = np.array([0.80, 0.93, 1.00], np.float32)           # BGR pale gold-white
def rich_word(mask, k_land, sweep=True, gold_edge=True):
    """detailed type: vertical gradient fill, gold edge, inner shade, soft glow, one light sweep after landing."""
    hh, ww = mask.shape; pad = 30
    m = np.pad(mask, pad); H2, W2 = m.shape
    grad = np.linspace(0, 1, H2, dtype=np.float32)[:, None, None]
    fill = WHITE * (1 - grad * 0.55) + CREAM * grad * 0.55
    inner = cv2.GaussianBlur(cv2.erode(m, np.ones((5, 5), np.uint8)), (0, 0), 3)
    fill = fill * (0.78 + 0.22 * inner[..., None])
    rgba = np.zeros((H2, W2, 4), np.float32)
    sh = cv2.GaussianBlur(m, (0, 0), 12) * 0.75
    rgba[..., 3] = sh
    if gold_edge:
        ed = np.clip(cv2.dilate(m, np.ones((5, 5), np.uint8)) - m, 0, 1)
        rgba[..., :3] = rgba[..., :3] * (1 - ed[..., None]) + GOLD * ed[..., None]; rgba[..., 3] = np.maximum(rgba[..., 3], ed)
    rgba[..., :3] = rgba[..., :3] * (1 - m[..., None]) + fill * m[..., None]; rgba[..., 3] = np.maximum(rgba[..., 3], m)
    if sweep and 0 <= k_land < 26:
        xs = np.arange(W2)[None, :] + 0.6 * np.arange(H2)[:, None]; pos = -120 + (W2 + 400) * (k_land / 26)
        band = np.exp(-((xs - pos) / 28.0) ** 2) * m
        rgba[..., :3] = np.clip(rgba[..., :3] + band[..., None] * 0.6, 0, 1)
    glow = np.zeros_like(rgba); glow[..., :3] = GOLD; glow[..., 3] = cv2.GaussianBlur(m, (0, 0), 20) * 0.35
    return glow, rgba

def lead_line(out, f, words, y, a_line):
    t = f / FPS; fnt = font(F_SB, 50); sp = fnt.getlength("  ")
    widths = [sum(fnt.getlength(c) + 12 for c in w) for w, _ in words]
    x = W / 2 - (sum(widths) + sp * (len(words) - 1)) / 2
    for (w, ws), wd in zip(words, widths):
        k = (t - E.s2e(ws)) * FPS
        if k > -1:
            v = eout((k + 1) / 10, 3)
            m = text_mask(w, F_SB, 50, tracking=12)
            if v < 1: m = cv2.GaussianBlur(m, (0, 0), 0.1 + 5 * (1 - v))
            L = shadowed(m, WHITE * 0.95, blur=8, sa=0.7)
            out = paste(out, L, int(x + wd / 2 - L.shape[1] / 2), int(y + 18 * (1 - v) - L.shape[0] / 2), v * a_line)
        x += wd + sp
    return out

def place_word(out, glow, rgba, cx, cy, a, sc=1.0, dx=0, dy=0):
    if a <= 0: return out
    if abs(sc - 1) > 0.003:
        glow = cv2.resize(glow, (int(glow.shape[1] * sc), int(glow.shape[0] * sc)), interpolation=cv2.INTER_LINEAR)
        rgba = cv2.resize(rgba, (int(rgba.shape[1] * sc), int(rgba.shape[0] * sc)), interpolation=cv2.INTER_LINEAR)
    x0, y0 = int(cx - rgba.shape[1] / 2 + dx), int(cy - rgba.shape[0] / 2 + dy)
    out = paste(out, glow, x0, y0, a); return paste(out, rgba, x0, y0, a)

def ecg(out, f, t0, t_end, y=1690):
    t = f / FPS
    if not (t0 <= t < t_end): return out
    p = clamp((t - t0) / 0.9, 0, 1); xs = np.arange(40, W - 40, 4)
    beat = lambda x: sum(math.exp(-((x - bx) / 10) ** 2) * (-90) + math.exp(-((x - bx - 18) / 14) ** 2) * 40 for bx in (W * 0.32, W * 0.68))
    pts = np.array([(x, y + beat(x)) for x in xs if x < 40 + p * (W - 80)], np.int32)
    fade = clamp((t_end - t) / 0.25, 0, 1)
    if len(pts) > 1:
        lay = np.zeros((H, W), np.float32); cv2.polylines(lay, [pts], False, 1.0, 3, cv2.LINE_AA)
        g = cv2.GaussianBlur(lay, (0, 0), 8) * 2.5
        out = np.clip(out + (lay[..., None] * WHITE * 0.8 + g[..., None] * GOLD) * fade * 0.9, 0, 1)
        hx, hy = pts[-1]
        if p < 1: cv2.circle(out, (int(hx), int(hy)), 7, tuple(float(c) for c in WHITE), -1, cv2.LINE_AA)
    return out

# ============================================================================ v5d: polish + new FALLING + landing bursts
def anamorphic(out, amt=0.30):
    """cinematic horizontal flare streaks from the brightest highlights (gold-tinted)."""
    small = cv2.resize(out, (W // 8, H // 8), interpolation=cv2.INTER_AREA)
    hi = np.clip(small.max(2) - 0.80, 0, 1) * 4.0
    st = cv2.GaussianBlur(hi, (0, 0), sigmaX=40, sigmaY=0.6)
    st = cv2.resize(st, (W, H), interpolation=cv2.INTER_LINEAR)
    return np.clip(out + st[..., None] * (GOLD * 0.6 + WHITE * 0.25) * amt, 0, 1)

_CA = {}
def edge_ca(out, amt=3.0):
    """subtle lens chromatic aberration growing toward the frame edges."""
    if "g" not in _CA:
        cx, cy = W / 2, H / 2; dx, dy = _GX - cx, _GY - cy; r = np.sqrt(dx * dx + dy * dy) / math.hypot(cx, cy)
        _CA["g"] = (dx * r ** 2, dy * r ** 2)
    dx, dy = _CA["g"]; o = out.copy(); s_ = amt / 400.0
    o[..., 2] = cv2.remap(out[..., 2], (_GX + dx * s_).astype(np.float32), (_GY + dy * s_).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    o[..., 0] = cv2.remap(out[..., 0], (_GX - dx * s_).astype(np.float32), (_GY - dy * s_).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return o

def spark_burst(out, cx, cy, k, seed, n=60, spread=420, col=None):
    """sparks fly out from (cx, cy) with gravity, k = frames since impact."""
    if k < 0 or k > 22: return out
    col = GOLD if col is None else col
    rng = np.random.default_rng(seed); lay = np.zeros((H // 2, W // 2), np.float32)
    for i in range(n):
        a = rng.uniform(math.pi * 1.05, math.pi * 1.95) if rng.random() < 0.8 else rng.uniform(0, math.pi * 2)
        sp = rng.uniform(0.4, 1.0) * spread / 14
        x = cx + math.cos(a) * sp * k; y = cy + math.sin(a) * sp * k + 1.4 * k * k
        x2 = x - math.cos(a) * sp * 1.6; y2 = y - (math.sin(a) * sp + 2.8 * k) * 1.6
        cv2.line(lay, (int(x2 / 2), int(y2 / 2)), (int(x / 2), int(y / 2)), float(1 - k / 22), 1, cv2.LINE_AA)
    lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 0.8) * 2.2, (W, H))
    return np.clip(out + lay[..., None] * col, 0, 1)

def land_ring(out, cx, cy, k, w=520):
    """flat elliptical shockwave under a landing word."""
    if k < 0 or k > 14: return out
    u = eout(k / 14, 2); a = (1 - k / 14)
    lay = np.zeros((H, W), np.float32)
    cv2.ellipse(lay, (int(cx), int(cy)), (int(60 + w * u), int(10 + 40 * u)), 0, 0, 360, 1.0, 3, cv2.LINE_AA)
    g = cv2.GaussianBlur(lay, (0, 0), 6) * 2
    return np.clip(out + (lay * 0.8 + g)[..., None] * GOLD * a, 0, 1)

def fall_word(out, f, kw, k, kout, fade, KY, size):
    """FALLING: plunges from above with a vertical light trail, slams down with squash + shockwave + sparks,
    holds with a heat shimmer, then the letters break loose and tumble away, spinning, with trails."""
    m = text_mask(kw, F_BLACK, size); hh, ww = m.shape
    land = 9                                                  # frames to land
    if k < land:                                              # the plunge
        u = ein((k + 1) / land, 2.2); dy = -300 * (1 - u)
        g, r = rich_word(m, -99)
        stretch = 1 + 0.6 * (1 - u)
        r2 = cv2.resize(r, (r.shape[1], int(r.shape[0] * stretch)), interpolation=cv2.INTER_LINEAR)
        trail = r2.copy(); trail[..., :3] = GOLD; trail = hblur(trail, int(10 + 120 * (1 - u)), vertical=True)
        out = paste(out, trail, int(W / 2 - trail.shape[1] / 2), int(KY + dy - trail.shape[0] * 0.9), 0.75 * fade)
        out = paste(out, r2, int(W / 2 - r2.shape[1] / 2), int(KY + dy - r2.shape[0] / 2), fade * clamp(u * 3, 0, 1))
        return out
    kl = k - land
    if kout <= -14:                                           # landed: squash/settle, impact FX, sweep
        sq = math.exp(-kl / 3.5) * math.cos(kl * 0.9)
        g, r = rich_word(m, kl - 2)
        sx, sy = 1 + 0.16 * sq, 1 - 0.20 * sq
        rr = cv2.resize(r, (int(r.shape[1] * sx), int(r.shape[0] * sy)), interpolation=cv2.INTER_LINEAR)
        gg = cv2.resize(g, (rr.shape[1], rr.shape[0]), interpolation=cv2.INTER_LINEAR)
        base = KY + hh / 2
        out = land_ring(out, W / 2, base + 8, kl)
        x0, y0 = int(W / 2 - rr.shape[1] / 2), int(base - rr.shape[0] + 30)
        out = paste(out, gg, x0, y0, fade); out = paste(out, rr, x0, y0, fade)
        out = spark_burst(out, W / 2, base, kl, 71, 70, 520)
        if kl < 5: out = np.clip(out + (5 - kl) * 0.03, 0, 1)
        return out
    # break loose and tumble, letter by letter (left to right), with spin and light trails
    ke0 = kout + 14; fnt = font(F_BLACK, size); x = W / 2 - fnt.getlength(kw) / 2
    for j, ch in enumerate(kw):
        cw = fnt.getlength(ch); ke = ke0 - j * 1.2
        g, r = rich_word(text_mask(ch, F_BLACK, size), 99)
        if ke <= 0:
            out = place_word(out, g, r, x + cw / 2, KY, fade)
        else:
            rng = np.random.default_rng(j * 13 + 5); rot = rng.uniform(-1, 1) * 70 * ke / 12
            dy = 2.6 * ke * ke; dx = rng.uniform(-6, 6) * ke
            M = cv2.getRotationMatrix2D((r.shape[1] / 2, r.shape[0] / 2), rot, 1.0)
            rr = cv2.warpAffine(r, M, (r.shape[1], r.shape[0]), borderValue=(0, 0, 0, 0))
            tr = rr.copy(); tr[..., :3] = EMBER * 0.6 + GOLD * 0.4; tr = hblur(tr, int(8 + 4 * ke), vertical=True)
            a = clamp(1 - ke / 22, 0, 1) * fade
            out = paste(out, tr, int(x + cw / 2 + dx - tr.shape[1] / 2), int(KY + dy - tr.shape[0] / 2 - 4 * ke), 0.6 * a)
            out = paste(out, rr, int(x + cw / 2 + dx - rr.shape[1] / 2), int(KY + dy - rr.shape[0] / 2), a)
        x += cw
    return out


_SCR = {}
def lyric_lockups(out, f):
    t = f / FPS; KY = 1500; LY = 1350
    for pre, key, style, s_end in E.PHRASES:
        t0 = E.s2e(pre[0][1]) - 0.05; t1 = E.s2e(s_end)
        if not (t0 <= t < t1 + 0.18): continue
        kout = (t - t1) * FPS; fade = 1.0 if kout <= 0 else clamp(1 - kout / 10, 0, 1)
        cyc = 1560 if style == "lost" else 1440
        if "scrim" not in _SCR: _SCR["scrim"] = {}
        if cyc not in _SCR["scrim"]:
            sc_ = np.zeros((H, W), np.float32); cv2.ellipse(sc_, (W // 2, cyc), (600, 300 if style == "lost" else 210), 0, 0, 360, 1.0, -1)
            _SCR["scrim"][cyc] = cv2.GaussianBlur(sc_, (0, 0), 90)[..., None]
        out = out * (1 - 0.45 * fade * clamp((t - t0) * FPS / 8, 0, 1) * _SCR["scrim"][cyc])
        out = lead_line(out, f, pre, 1250 if style == "lost" else LY, fade)
        kw = " ".join(w for w, _ in key); size = 150 if len(kw) <= 8 else 120
        k = (t - E.s2e(key[0][1])) * FPS
        if k < -1: continue
        dur = (t1 - E.s2e(key[0][1])) * FPS
        if style == "think":                                   # each word resolves from blur with wide tracking
            fnt = font(F_BLACK, 120); sp = fnt.getlength("  "); words = key
            widths = [fnt.getlength(w) for w, _ in words]; x = W / 2 - (sum(widths) + sp * (len(words) - 1)) / 2
            for (w, ws), wd in zip(words, widths):
                kk = (t - E.s2e(ws)) * FPS
                if kk > -1:
                    v = eout((kk + 1) / 12, 3); m = text_mask(w, F_BLACK, 120)
                    if v < 1: m = cv2.GaussianBlur(m, (0, 0), 0.1 + 8 * (1 - v))
                    g, r = rich_word(m, kk - 10)
                    out = place_word(out, g, r, x + wd / 2, KY, v * fade, 1 + 0.15 * (1 - v))
                x += wd + sp
        elif style == "fall":                                  # plunge -> slam -> tumble away
            out = fall_word(out, f, kw, k, kout, fade, KY, size)
        elif style == "fade":                                  # resolves, then dissolves into rising sparks
            m = text_mask(kw, F_BLACK, size, tracking=6); v = eout(k / 8, 3)
            p = clamp((k - dur * 0.40) / (dur * 0.55), 0, 1)
            if p > 0:
                nz = cv2.resize(np.random.default_rng(4).random((m.shape[0] // 5 + 1, m.shape[1] // 5 + 1)).astype(np.float32), (m.shape[1], m.shape[0]))
                edge = np.clip(1 - np.abs(nz - p) / 0.06, 0, 1) * m
                m = m * np.clip((nz - p) / 0.06, 0, 1)
            g, r = rich_word(cv2.GaussianBlur(m, (0, 0), 0.1 + 6 * (1 - v)), k - 10)
            out = place_word(out, g, r, W / 2, KY, v * fade)
            if p > 0:
                ys, xs = np.nonzero(edge > 0.5); rng = np.random.default_rng(int(k))
                lay = np.zeros((H, W), np.float32); ox, oy = W / 2 - m.shape[1] / 2, KY - m.shape[0] / 2
                for i in rng.choice(len(xs), min(len(xs), 120), replace=False) if len(xs) else []:
                    cv2.circle(lay, (int(ox + xs[i] + rng.normal(0, 8)), int(oy + ys[i] - rng.uniform(0, 90) * p)), 2, 1.0, -1, cv2.LINE_AA)
                out = np.clip(out + cv2.GaussianBlur(lay, (0, 0), 1.5)[..., None] * GOLD * 1.6 * fade, 0, 1)
        elif style == "drown":                                 # sinks through a ripple, cold tint, bubbles rise
            m = text_mask(kw, F_BLACK, size); hh, ww = m.shape
            yy = np.arange(hh, dtype=np.float32)[:, None]; xx = np.arange(ww, dtype=np.float32)[None, :]
            amp = 9 * math.exp(-k / 20) + 3
            m = cv2.remap(m, (xx + amp * np.sin(yy / 9 + k * 0.45)).astype(np.float32), (yy + amp * 0.6 * np.sin(xx / 17 + k * 0.35)).astype(np.float32), cv2.INTER_LINEAR)
            v = eout(k / 12, 3); sink = 50 * clamp(k / max(dur, 1), 0, 1)
            g, r = rich_word(m, k - 12, gold_edge=False)
            r[..., :3] = r[..., :3] * np.array([1.0, 0.92, 0.80], np.float32)
            out = place_word(out, g * 0.4, r, W / 2, KY + sink, v * fade, 1.0, 0, 60 * (1 - v))
            rng = np.random.default_rng(9)
            for i in range(26):
                bx = W / 2 + rng.uniform(-ww / 2, ww / 2); sp_ = rng.uniform(4, 9); st0 = rng.uniform(0, 20)
                by = KY + 60 - (k - st0) * sp_
                if k > st0 and by > KY - 260:
                    cv2.circle(out, (int(bx + 6 * math.sin(k * 0.2 + i)), int(by)), int(rng.uniform(3, 9)), tuple(float(c) for c in (WHITE * 0.85 * fade)), 2, cv2.LINE_AA)
        elif style == "breathe":                               # slow inhale + heartbeat line
            v = eout(k / 20, 2); sc = 0.94 + 0.10 * clamp(k / 90, 0, 1)
            m = text_mask(kw, F_SB, 170, tracking=int(34 - 18 * v))
            if v < 1: m = cv2.GaussianBlur(m, (0, 0), 0.1 + 8 * (1 - v))
            g, r = rich_word(m, k - 20, gold_edge=False)
            g[..., 3] *= 1.3 + 0.5 * math.sin(k * 0.12)
            out = place_word(out, g, r, W / 2, KY, v * fade, sc)
            out = ecg(out, f, E.s2e(key[0][1]), t1 + 0.1)
        if style in ("think", "hurt", "losing") and 0 <= k < 22:
            out = spark_burst(out, W / 2, KY + 70, k - 4, 90 + len(kw), 28, 300)
        if style == "hurt":                                    # lands, then cracks along a lightning fracture
            m = text_mask(kw, F_BLACK, size); hh, ww = m.shape; v = eout(k / 6, 3)
            g, r = rich_word(m, k - 6)
            kc = k - 14
            if kc <= 0:
                out = place_word(out, g, r, W / 2, KY, v * fade, 1 + 0.3 * (1 - v))
            else:
                sep = 14 * eout(kc / 8, 2); pad = 30
                pts = bolt_points((pad + ww * 0.52, 0), (pad + ww * 0.46, hh + 2 * pad), 61, 0.12, 6)
                poly = np.vstack([pts, [[-10, hh + 2 * pad], [-10, 0]]]).astype(np.int32)
                left = np.zeros(r.shape[:2], np.uint8); cv2.fillPoly(left, [poly], 1)
                for side, mm in ((-1, left), (1, 1 - left)):
                    rr = r.copy(); rr[..., 3] *= mm; gg = g.copy(); gg[..., 3] *= mm
                    out = place_word(out, gg, rr, W / 2, KY, fade, 1.0, side * sep, side * sep * 0.3)
                core, glow = draw_bolt((H, W), pts + np.float32([W / 2 - ww / 2 - pad, KY - hh / 2 - pad]), 61, 1, 3)
                out = add_light(out, core, glow, GOLD, fade * clamp(1 - kc / 30, 0.3, 1))
        elif style == "lost":                                  # LOST / IT / ALL stack, then scatter away
            yy0 = 1330
            for wi, (w, ws) in enumerate(key):
                kk = (t - E.s2e(ws)) * FPS
                if kk > -1:
                    v = eout((kk + 1) / 7, 3); m = text_mask(w, F_BLACK, 140)
                    if v < 1: m = cv2.GaussianBlur(m, (0, 0), 0.1 + 5 * (1 - v))
                    g, r = rich_word(m, kk - 7)
                    if w == "ALL": r[..., :3] = r[..., :3] * 0.7 + GOLD * 0.3 * (r[..., 3:4] > 0.5)
                    if kout > -10:                         # scatter: each word flies a different way
                        e_ = ein((kout + 10) / 18, 2); ang = (-0.6, 0.4, 1.3)[wi]
                        out = place_word(out, g, r, W / 2, yy0 + 70, fade * (1 - e_), 1 + 0.6 * e_, 700 * e_ * math.cos(ang), -500 * e_ * math.sin(ang))
                    else:
                        out = place_word(out, g, r, W / 2, yy0 + 70, v * fade, 1 + 0.4 * (1 - v))
                yy0 += 150
        elif style == "losing":                                # letters arrive, then are pulled away one by one
            fnt = font(F_BLACK, size); x = W / 2 - fnt.getlength(kw) / 2; n = len(kw)
            for j, ch in enumerate(kw):
                cw = fnt.getlength(ch); v = eout((k + 1 - j * 0.8) / 8, 3)
                pull = clamp((k - dur * 0.45 - (n - 1 - j) * 3) / 10, 0, 1)
                g, r = rich_word(text_mask(ch, F_BLACK, size), k - 10 - j)
                if pull > 0:
                    tr = r.copy(); tr[..., :3] = GOLD; tr = hblur(tr, 10 + 200 * pull)
                    out = paste(out, tr, int(x + cw / 2 - tr.shape[1] / 2 + 900 * ein(pull, 2) - 100), int(KY - tr.shape[0] / 2), fade * (1 - pull) * 0.8)
                out = place_word(out, g, r, x + cw / 2, KY, clamp(v, 0, 1) * fade * (1 - pull), 1.0, -600 * (1 - v) + 900 * ein(pull, 2))
                x += cw
    return out

# ============================================================================ v5 frame
def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    out = render_shot(s, f)
    tin = s.get("tin"); tout = s.get("tout"); P = prev_shot(s)
    # ---- incoming
    if tin == "bolt_open": out = bolt_open(out, k)
    elif tin == "emblem": out = emblem_open(out, f, k)
    elif tin == "slit" and k < 11: out = slit(out, 1 - eout(k / 11, 2.2), f)
    elif tin == "remnant": out = remnant(out, f, s, k)
    elif tin == "ring" and k < 13: out = ring_wipe(last_frame_of(P), out, k)
    elif tin == "bolt_wipe" and k < 12: out = bolt_wipe(last_frame_of(P), out, k, seed=3 + s["f0"] % 11)
    elif tin == "prism" and k < 11: out = prism(out, k)
    elif tin == "smear" and k < 10: out = smear(out, (1 - k / 10) ** 2, f)
    elif tin == "shockwave" and k < 13: out = shockwave(last_frame_of(P), out, s, f, k)
    elif tin == "flare": out = leak(out, f, s["f0"])
    elif tin == "phase" and k < 12:
        A = last_frame_of(P); v = smooth(k / 12)
        out = phase(A, f, 1 - v * 0.3) * (1 - v) + phase(out, f + 1, 1 - v) * v
    elif tin == "tunnel" and k < 12: out = tunnel(out, f, k, "in")
    elif tin == "bolt_split" and k < 13: out = bolt_split(last_frame_of(P), out, k, seed=11 + s["f0"] % 7)
    elif tin == "dissolve" and k < 12:
        A = last_frame_of(P); v = smooth(k / 12); out = A * (1 - v) + out * v
    elif tin == "whip": out = whip(out, f, s)
    elif tin == "logo" and k < 11: out = logo_flash(last_frame_of(P), out, k)
    elif tin == "zoomblur" and k < 8:
        u = 1 - k / 8; out = radial_blur(out, W / 2, H * 0.42, 1 + 0.6 * u * u, 1 + 0.6 * max(0, u - 0.12) ** 2, 6)
        out = np.clip(out + streak_layer(f, 0.8 * u)[..., None] * GOLD, 0, 1)
    elif tin == "roll" and k < 9:
        u = 1 - k / 9; out = roll(out, -85 * u * u, -85 * max(0, u - 0.12) ** 2, 1 + 0.45 * u * u)
    elif tin == "twirl" and k < 10:
        u = 1 - k / 10; out = radial_blur(twirl(out, -3.2 * u * u), W / 2, H * 0.45, 1.0, 1 + 0.1 * u, 4)
    elif tin in ("flash", "cut_rgb") and k < 6:
        fl = [0.9, 0.5, 0.22, 0.08, 0, 0][k] if tin == "flash" else [0.4, 0.15, 0, 0, 0, 0][k]
        out = np.clip(out * (1 + 1.5 * fl) + fl * 0.45 * GOLD, 0, 1)
        out = rgb_split(out, (24 if tin == "cut_rgb" else 14) * math.exp(-k / 2))
        if tin == "flash": out = zoom_about(out, W / 2, H / 2, 1 + 0.08 * math.exp(-k / 2.5))
    # ---- outgoing (start before the cut)
    if n_ is not None:
        nt = n_.get("tin")
        if tout == "tunnel" and kn >= -10: out = tunnel(out, f, kn, "out")
        if tout == "slit" and kn >= -9: out = slit(out, ein((kn + 10) / 10, 1.8), f)
        if nt == "bolt_split" and kn >= -5: out = bolt_split(out, None, kn, seed=11 + n_["f0"] % 7)
        if tout == "phase" and kn >= -10: out = phase(out, f, ein((kn + 11) / 11, 1.6))
        if nt == "whip" and kn >= -4: out = whip(out, f, n_)
        if nt == "zoomblur" and kn >= -5:
            u = (kn + 6) / 6; out = radial_blur(out, W / 2, H * 0.42, 1 + 0.6 * (u - 0.17) ** 2, 1 + 0.6 * u * u, 6)
        if nt == "roll" and kn >= -6:
            u = (kn + 7) / 7; out = roll(out, 95 * ein(u, 2.2) - 14 * u, 95 * ein(u, 2.2), 1 + 0.45 * ein(u, 2))
        if nt == "twirl" and kn >= -6:
            u = (kn + 7) / 7; out = radial_blur(twirl(out, 3.2 * ein(u, 2)), W / 2, H * 0.45, 1.0, 1 + 0.1 * u, 4)
        if tout == "logo" and kn >= -12: out = logo_flash(out, render_shot(n_, n_["f0"], False), kn)
        if nt == "flare" and kn >= -8: out = leak(out, f, n_["f0"])
        if nt == "smear" and kn >= -6: out = smear(out, ((kn + 7) / 7) ** 2, f)
        if nt == "prism" and kn >= -3: out = rgb_split(out, 30 * (kn + 4) / 4)
        if nt == "dissolve": pass
    if tout == "eye_out": out = eye_out(out, f, s)
    if tout == "slit_end": out = slit_end(lyric_lockups(out, f), f, s); s = dict(s, _lyr_done=True)
    if s.get("arcs"): out = arcs(out, f, s)
    if s.get("streaks"): out = light_streaks(out, f)
    out = edge_lightning(out, f)
    out = embers(out, f, 0.0 if f < 50 else (0.5 if f / FPS < E.th(240) else 1.0))
    # ---- type
    if not s.get("_lyr_done"): out = lyric_lockups(out, f)
    out = bloom(out, 0.26)
    out = anamorphic(out, 0.32)
    out = edge_ca(out, 3.0)
    out = out * VIG + grain(f, 0.014)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)

def beat_bounce(f):
    """zoom pulse on every beat from 'I am drowning' on (h240+), every 2 beats before."""
    t = f / FPS; h = t / E.HB + E.H0
    if h < 224: return 1.0
    per = 2 if h >= 240 else 4
    ph = ((h - E.H0) % per) * E.HB
    return 1 + (0.022 if h >= 240 else 0.012) * math.exp(-ph / 0.10)

def init_hits():
    HITS.clear()
    for h, a in ((224, 14), (240, 18), (248, 10), (256, 16), (264, 12), (268, 14), (272, 20), (280, 16)):
        HITS.append((E.fh(h), a, 4.5))


# ============================================================================ v6: WARMPOP — VHS Miami toolkit
PINK = np.array([0.72, 0.36, 1.00], np.float32)       # BGR hot pink
CYAN = np.array([1.00, 0.90, 0.30], np.float32)       # BGR cyan
PEACH = np.array([0.55, 0.70, 1.00], np.float32)
VIOLET = np.array([0.45, 0.10, 0.30], np.float32)
F_JP = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
F_BI = "/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf"
F_BLDI = "/usr/share/fonts/opentype/inter/InterDisplay-BoldItalic.otf"

def static_noise(f, amt=1.0):
    rng = np.random.default_rng(f * 31 + 7)
    n = rng.random((H // 4, W // 4)).astype(np.float32)
    n = cv2.resize(n, (W, H), interpolation=cv2.INTER_NEAREST)
    rows = (rng.random(H) < 0.08).astype(np.float32)[:, None] * 0.5
    g = np.clip(n * 0.85 + rows, 0, 1)
    return np.repeat(g[..., None], 3, axis=2) * amt

def tracking(out, f, amt):
    """VHS tracking errors: displaced horizontal bands, white tracking lines, chroma smear."""
    if amt <= 0.01: return out
    rng = np.random.default_rng(f * 17 + 3); o = out.copy()
    for _ in range(int(2 + 6 * amt)):
        y = int(rng.integers(0, H - 60)); h = int(rng.integers(6, 50)); d = int(rng.integers(-60, 60) * amt)
        o[y:y + h] = np.roll(o[y:y + h], d, axis=1)
    for _ in range(int(1 + 4 * amt)):
        y = int(rng.integers(0, H)); x0 = int(rng.integers(0, W // 2)); L = int(rng.integers(100, W))
        o[y:y + 2, x0:x0 + L] = o[y:y + 2, x0:x0 + L] * (1 - 0.8 * amt) + 0.9 * amt
    return rgb_split(o, 6 * amt)

_VHS = {}
def vhs(out, f, s_):
    """global VHS finish: chroma bleed, scanlines, tape grain, head-switching band at the bottom."""
    if "scan" not in _VHS:
        _VHS["scan"] = (1 - 0.06 * ((np.arange(H) % 3) == 0).astype(np.float32))[:, None, None]
    ycc = cv2.cvtColor((np.clip(out, 0, 1) * 255).astype(np.uint8), cv2.COLOR_BGR2YCrCb).astype(np.float32)
    for c in (1, 2):
        ch = np.roll(ycc[..., c], int(3 + 3 * s_), axis=1)
        ycc[..., c] = cv2.blur(ch, (int(9 + 10 * s_), 1))
    o = cv2.cvtColor(np.clip(ycc, 0, 255).astype(np.uint8), cv2.COLOR_YCrCb2BGR).astype(np.float32) / 255
    o = o * (1 - (1 - _VHS["scan"]) * s_)
    rng = np.random.default_rng(f * 5 + 1)
    hb = int(12 + 10 * s_); band = o[H - hb:].copy(); band = np.roll(band, int(rng.integers(8, 40)), axis=1)
    o[H - hb:] = band * 0.7 + rng.random((hb, W, 1)).astype(np.float32) * 0.25
    if rng.random() < 0.03 * (0.5 + s_):
        o = tracking(o, f, 0.25)
    return np.clip(o, 0, 1)

def osd(out, f, text, x=70, y=110, a=1.0, size=46):
    if a <= 0: return out
    m = text_mask(text, F_MONO, size, tracking=4)
    L = shadowed(m, WHITE, blur=3, sa=0.6)
    return paste(out, L, x, y, a)

# ---- tape load open (static -> roll -> picture) and rewind end (picture -> rewind -> static)  = loop seam
def tape_in(img, f, k):
    if k >= 30: return tracking(img, f, max(0.0, 0.35 - k / 120)) if k < 42 else img
    if k < 8: return static_noise(f)
    u = (k - 8) / 22.0
    roll = int((1 - eout(u, 2.5)) * H * 0.6)
    o = np.roll(img, -roll, axis=0)
    if roll > 0: o[H - roll:H - roll + 14] = 0.02
    o = tracking(o, f, 1 - u)
    return np.clip(o * (0.4 + 0.6 * u) + static_noise(f, 0.6 * (1 - u)), 0, 1)

def rewind_end(img, f, s):
    kk = s["f1"] - f; n = 40
    if kk > n: return img
    u = 1 - kk / n
    if kk <= 8: return static_noise(f)                        # matches the opening static exactly in style
    fr = max(s["f0"], int(f - (n - kk) * 7))                  # play the shot backwards at 8x
    o = render_shot(s, fr)
    o = tracking(o, f, 0.4 + 0.6 * u)
    o = o * (1 - 0.3 * u) + static_noise(f, 0.35 * u)
    return osd(np.clip(o, 0, 1), f, "◀◀ REW", a=1.0 if (f // 15) % 2 == 0 else 0.4)

def vhs_roll(A, B, k, f):
    """k=-5..-1: A rolls up; k=0..7: B rolls into place."""
    if k < 0:
        u = (k + 6) / 6.0; roll = int(ein(u, 2) * H * 0.5); o = np.roll(A, -roll, axis=0)
    else:
        u = 1 - k / 8.0; roll = int(ein(u, 2) * H * 0.5); o = np.roll(B, roll, axis=0)
    if roll > 0:
        y = (H - roll) % H if k < 0 else roll; o[max(0, y - 10):y + 10] = 0.03
    return tracking(o, f, 0.9 * u)

def tear(A, B, k, f, n=9):
    """VHS tape tear: the frame splits into sliding horizontal bands; B slides in band by band with chroma fringes."""
    u = k / n; rng = np.random.default_rng(1000 + k); o = B.copy(); y = 0
    while y < H:
        hgt = int(rng.integers(30, 140)); y1 = min(H, y + hgt)
        src = A if rng.random() > u * 1.25 else B
        dx = int((rng.uniform(-1, 1) * 220 + 160 * math.sin(y * 0.01 + k)) * (1 - u) ** 1.5)
        o[y:y1] = np.roll(src[y:y1], dx, axis=1)
        if rng.random() < 0.25 * (1 - u): o[y:y1] = np.clip(o[y:y1] * 1.3 + 0.08, 0, 1)
        y = y1
    o = rgb_split(o, 18 * (1 - u))
    return tracking(o, f, 0.8 * (1 - u))

# ---- voidfx logo as a neon sign: tubes flicker on over the outgoing shot, then the camera flies through the 'o'
_NEO = {}
def logo_neon(A, B, k, f):
    """k: -12..+10 around the cut (the only logo appearance in the edit)."""
    L = logo_assets(); h = L["h"]
    if "rgba" not in _NEO:
        al = (L["rgba"][..., 3] > 0.5).astype(np.uint8)
        tube = np.clip(cv2.dilate(al, np.ones((7, 7), np.uint8)) - cv2.erode(al, np.ones((7, 7), np.uint8)), 0, 1).astype(np.float32)
        core = cv2.erode(tube, np.ones((3, 3), np.uint8)).astype(np.float32)
        x = np.linspace(0, 1, E.LOGO_W, dtype=np.float32)[None, :, None]
        col = PINK * (1 - x) + CYAN * x
        rgba = np.zeros((h, E.LOGO_W, 4), np.float32)
        rgba[..., :3] = col * tube[..., None] * 0.95 + WHITE * core[..., None] * 0.85 + al[..., None] * 0.04
        rgba[..., 3] = np.maximum(tube, al * 0.45)
        glow = np.zeros_like(rgba); glow[..., :3] = col; glow[..., 3] = cv2.GaussianBlur(tube, (0, 0), 18) * 1.6
        _NEO.update(rgba=rgba, glow=glow)
    X0, Y0 = (W - E.LOGO_W) // 2, int(H * 0.63 - h / 2)        # below the face
    ccx, ccy = X0 + L["c"][0], Y0 + L["c"][1]
    flick = [0.0, 0.6, 0.1, 0.0, 0.8, 0.3, 1.0]
    v = flick[k + 12] if k < -5 else 1.0
    sc = 1.0 if k < -5 else math.exp(4.3 * ein((k + 5) / 15, 2.2))
    M = cv2.getRotationMatrix2D((ccx, ccy), 0, sc)
    def lay(img):
        c = np.zeros((H, W, 4), np.float32); c[Y0:Y0 + h, X0:X0 + E.LOGO_W] = img
        return cv2.warpAffine(c, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    lw, gw = lay(_NEO["rgba"]), lay(_NEO["glow"])
    cnt = np.zeros((H, W), np.float32); cnt[Y0:Y0 + h, X0:X0 + E.LOGO_W] = L["counter"]
    cw = cv2.warpAffine(cnt, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    if sc > 8: cw = np.maximum(cw, clamp((sc - 8) / 6, 0, 1))
    cw = cw * (1.0 if k >= -5 else 0.0)
    dim = 1 - 0.5 * clamp((k + 12) / 6, 0, 1)                     # the room darkens as the sign comes on
    Bz = zoom_about(B, ccx, ccy, 1.6 - 0.6 * clamp((sc - 1) / 30, 0, 1))
    out = A * dim * (1 - cw[..., None]) + Bz * cw[..., None]
    fade = v * clamp(1 - (sc - 6) / 6, 0, 1)
    out = out + gw[..., :3] * gw[..., 3:4] * 0.55 * fade
    al = lw[..., 3:4] * fade
    out = out * (1 - al) + lw[..., :3] * al
    if sc > 1.5: out = radial_blur(out, ccx, ccy, 1.0, 1.0 + 0.06 * min(1, sc / 10), 4)
    if k < -5: out = tracking(out, f, 0.25)
    return np.clip(out, 0, 1)

# ---- Dexter disappears into pixels ("disappear myself")
_VAN = {}
def vanish(out, person, f, t, t0, t1):
    """Dexter dissolves into pixel blocks that blow off to the right like dust; a clean plate is left behind."""
    if t < t0 or person is None: return out
    p = clamp((t - t0) / (t1 - t0), 0, 1.3)
    bs = 18; gh, gw = -(-H // bs), W // bs
    small = cv2.resize((out * 255).astype(np.uint8), (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    ms = cv2.resize(person, (W // 4, H // 4)); ms = (cv2.dilate((ms > 0.2).astype(np.uint8), np.ones((7, 7), np.uint8)) * 255)
    bg = cv2.inpaint(small, ms, 6, cv2.INPAINT_TELEA)
    bg = cv2.GaussianBlur(cv2.resize(bg, (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32) / 255, (0, 0), 2)
    if "thr" not in _VAN:
        rng = np.random.default_rng(3)
        thr = (rng.random((gh, gw)) * 0.45 + np.linspace(0.55, 0.0, gw)[None, :]).astype(np.float32)   # right side goes first
        _VAN.update(thr=thr, vx=rng.uniform(300, 820, (gh, gw)), vy=rng.uniform(-380, -40, (gh, gw)), ph=rng.uniform(0, 6.28, (gh, gw)),
                    tp=cv2.resize(thr, (gw * bs, gh * bs), interpolation=cv2.INTER_NEAREST)[:H, :W])
    thr, tp = _VAN["thr"], _VAN["tp"]
    keep = (tp > p).astype(np.float32) * person
    o = bg * (1 - keep[..., None]) + out * keep[..., None]
    kb = (keep > 0.5).astype(np.uint8)
    edge = cv2.GaussianBlur(cv2.morphologyEx(kb, cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8)).astype(np.float32), (0, 0), 1.5)
    front = np.clip(1 - np.abs(tp - p) / 0.10, 0, 1)                       # glow only along the dissolve front
    o = o + (edge * front)[..., None] * CYAN * 0.9
    cov = cv2.resize(person, (gw, gh), interpolation=cv2.INTER_AREA)
    col = cv2.resize(out, (gw, gh), interpolation=cv2.INTER_AREA)
    g = np.clip((p - thr) / 0.38, 0, 1)
    js, is_ = np.nonzero((cov > 0.3) & (g > 0) & (g < 1))
    for j, i in zip(js, is_):
        gg = float(g[j, i]); e = gg ** 1.5
        tint = PINK if (i + j) % 3 == 0 else (CYAN if (i + j) % 3 == 1 else WHITE)
        c = np.clip(col[j, i] * (1 - 0.6 * gg) + tint * (0.35 + 0.5 * gg), 0, 1)
        for lag, la in ((0.0, 1.0), (0.10, 0.45), (0.20, 0.2)):
            ee = max(e - lag, 0) if lag else e
            if lag and ee <= 0: continue
            x = i * bs + _VAN["vx"][j, i] * ee; y = j * bs + _VAN["vy"][j, i] * ee + 14 * math.sin(_VAN["ph"][j, i] + 9 * ee)
            sz = max(3, int(bs * (1 - 0.6 * gg) * (1 - 0.3 * (lag > 0)))); xi, yi = int(x), int(y)
            if xi < 0 or yi < 0 or xi + sz >= W or yi + sz >= H: continue
            a = (1 - gg) ** 0.6 * la * 0.95
            o[yi:yi + sz, xi:xi + sz] = o[yi:yi + sz, xi:xi + sz] * (1 - a) + c * a
    return np.clip(o, 0, 1)

# ---- kaleidoscope spin
_KAL = {}
def kaleido(img, a, rot, N=6, c=(W / 2, H * 0.42)):
    if a <= 0.01: return img
    if "g" not in _KAL:
        dx, dy = _GX - c[0], _GY - c[1]; _KAL["g"] = (np.sqrt(dx * dx + dy * dy), np.arctan2(dy, dx))
    r, th_ = _KAL["g"]; seg = 2 * math.pi / N
    t2 = np.abs(np.mod(th_ + rot, seg) - seg / 2)
    # full fold, then dissolve into it (an angle morph from unfolded to folded cannot be seamless)
    rr = r * (1 - 0.18 * a)                                          # slight pull-in as the mirrors close
    kal = cv2.remap(img, (c[0] + rr * np.cos(t2)).astype(np.float32), (c[1] + rr * np.sin(t2)).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    w = smooth(clamp(a * 1.25, 0, 1))
    return img * (1 - w) + kal * w

# ---- pixel-sort melt
_MELT = {}
def melt(A, B, u):
    if "v" not in _MELT:
        rng = np.random.default_rng(9); v = cv2.resize(rng.uniform(0.55, 1.0, (1, W // 6)).astype(np.float32), (W, 1), interpolation=cv2.INTER_NEAREST)
        _MELT["v"] = v
    v = _MELT["v"]; front = (ein(u, 1.6) * H * 1.35 * v)
    L = A.mean(2)
    sy = _GY - front * (0.25 + 0.75 * L)
    Am = cv2.remap(A, _GX, np.clip(sy, 0, H - 1).astype(np.float32), cv2.INTER_LINEAR)
    Am = cv2.blur(Am, (1, 25))
    inc = (_GY < front - 40).astype(np.float32)[..., None]
    edge = np.exp(-((_GY - front + 40) / 12) ** 2)[..., None]
    return np.clip(Am * (1 - inc) + B * inc + edge * PINK * 0.8, 0, 1)

# ---- CRT in a neon vapor world, fly through the screen
SCR = (220, 650, 640, 480)
_WORLD = {}
def palms_sil(img):
    """two palm-tree silhouettes standing on the horizon either side of the sun."""
    col = (0.10, 0.015, 0.075); rng = np.random.default_rng(31)
    for bx, hgt, lean in ((150, 520, 70), (930, 610, -90)):
        pts = [(bx + lean * (t_ ** 1.6), 1282 - hgt * t_) for t_ in np.linspace(0, 1, 40)]
        for i, (x, y) in enumerate(pts): cv2.circle(img, (int(x), int(y)), int(17 - 8 * i / 39), col, -1, cv2.LINE_AA)
        cx, cy = pts[-1]
        for fr in range(9):
            ang = math.radians(-170 + fr * 42 + rng.uniform(-8, 8)); Lf = rng.uniform(170, 250); dr = rng.uniform(0.5, 0.9)
            fp = [(cx + math.cos(ang) * Lf * t_, cy + math.sin(ang) * Lf * t_ + dr * Lf * t_ * t_ * 0.8) for t_ in np.linspace(0, 1, 18)]
            cv2.polylines(img, [np.int32(fp)], False, col, 9, cv2.LINE_AA)
            for i in range(2, 17):
                (px, py), (qx, qy) = fp[i], fp[i + 1]; dx, dy = qx - px, qy - py; nn = math.hypot(dx, dy) + 1e-6
                ll = 46 * (1 - i / 18) + 10
                for sg in (1, -1):
                    lx, ly = (dx * 0.5 - dy * 0.86 * sg) / nn, (dy * 0.5 + dx * 0.86 * sg) / nn
                    cv2.line(img, (int(px), int(py)), (int(px + lx * ll), int(py + ly * ll + 14)), col, 4, cv2.LINE_AA)
    return img

def vapor_world(f):
    if "sky" not in _WORLD:
        y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        sky = (1 - y) * np.array([0.30, 0.05, 0.12], np.float32) + y * np.array([0.55, 0.20, 0.80], np.float32)
        sun = np.zeros((H, W), np.float32); cv2.circle(sun, (W // 2, 1120), 330, 1.0, -1, cv2.LINE_AA)
        stripes = ((np.arange(H) - 1120) % 46 < (np.clip((np.arange(H) - 1000) / 330, 0, 1) * 22)).astype(np.float32)[:, None]
        sun = sun * (1 - stripes * (np.arange(H)[:, None] > 1000))
        sg = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        suncol = np.clip((1 - (sg * 1920 - 790) / 660), 0, 1) * np.array([0.35, 0.90, 1.0], np.float32) + np.clip((sg * 1920 - 790) / 660, 0, 1) * PINK
        img = sky * (1 - sun[..., None]) + suncol * sun[..., None]
        img = img + cv2.GaussianBlur(sun, (0, 0), 60)[..., None] * PINK * 0.35
        img = palms_sil(img)
        rng = np.random.default_rng(2)
        for _ in range(120):
            cv2.circle(img, (int(rng.uniform(0, W)), int(rng.uniform(0, 1000))), int(rng.integers(1, 3)), (0.9, 0.9, 1.0), -1, cv2.LINE_AA)
        _WORLD["sky"] = np.clip(img, 0, 1)
    img = _WORLD["sky"].copy(); hz = 1280
    img[hz:] = np.array([0.18, 0.02, 0.10], np.float32)
    lay = np.zeros((H, W), np.float32)
    for i in range(-14, 15):                                      # perspective lines
        cv2.line(lay, (W // 2 + i * 22, hz), (W // 2 + i * 260, H), 1.0, 2, cv2.LINE_AA)
    off = (f * 4) % 60
    for j in range(16):                                           # scrolling horizontal lines
        d = (j * 60 + off) / 960.0; y = int(hz + (H - hz) * d ** 2.2)
        cv2.line(lay, (0, y), (W, y), 1.0, 2, cv2.LINE_AA)
    g = cv2.GaussianBlur(lay, (0, 0), 5) * 2
    img = img + (lay[..., None] * 0.9 + g[..., None]) * PINK * (np.arange(H) >= hz)[:, None, None]
    cv2.line(img, (0, hz), (W, hz), tuple(float(c) for c in (PINK * 1.2)), 3, cv2.LINE_AA)
    return np.clip(img, 0, 1)

def crt_screen(content):
    x0, y0, w, h = SCR
    cy_ = int(H * 0.37 + 40); crop = content[cy_ - int(W * 0.375):cy_ + int(W * 0.375)]
    sc = cv2.resize(crop, (w, h), interpolation=cv2.INTER_AREA)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); nx, ny = (xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2); r2 = nx * nx + ny * ny
    sc = cv2.remap(sc, (w / 2 + nx * (1 - 0.06 * r2) * w / 2), (h / 2 + ny * (1 - 0.06 * r2) * h / 2), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    sc = sc * (1 - 0.18 * ((np.arange(h) % 4) < 2)[:, None, None]) * (1 - 0.35 * r2[..., None] ** 1.5)
    sc = sc + np.clip(0.18 - ny[..., None] * 0.1 - nx[..., None] * 0.05, 0, 0.2) * (ny < -0.2)[..., None]   # glass reflection
    return np.clip(sc, 0, 1)

def tv_layer(content, f):
    x0, y0, w, h = SCR; img = vapor_world(f)
    bx0, by0, bx1, by1 = x0 - 60, y0 - 60, x0 + w + 60, y0 + h + 150
    sh = np.zeros((H, W), np.float32); cv2.rectangle(sh, (bx0 + 30, by0 + 50), (bx1 + 30, by1 + 50), 1.0, -1)
    img = img * (1 - cv2.GaussianBlur(sh, (0, 0), 30)[..., None] * 0.6)
    cv2.rectangle(img, (bx0, by0), (bx1, by1), (0.20, 0.19, 0.21), -1, cv2.LINE_AA)
    cv2.rectangle(img, (bx0 + 6, by0 + 6), (bx1 - 6, by0 + 26), (0.30, 0.29, 0.31), -1)
    for i in range(3): cv2.circle(img, (bx1 - 70 - i * 50, by1 - 50), 14, (0.12, 0.12, 0.13), -1, cv2.LINE_AA)
    cv2.circle(img, (bx0 + 60, by1 - 50), 7, (0.2, 0.2, 1.0), -1, cv2.LINE_AA)
    img[y0:y0 + h, x0:x0 + w] = crt_screen(content)
    return img

def crt_through(A_fn, B_fn, f, kn):
    """kn -54..-1 before the drop: frame shrinks into a CRT in the vapor world, then the camera dives into the screen."""
    x0, y0, w, h = SCR; cx, cy = x0 + w / 2, y0 + h / 2
    if kn < -36:
        # the screen starts exactly over the face band of the full frame (width-filling), the rest of the frame is
        # wiped away into the TV bezel + vapor world, then the camera pulls back to reveal the set floating on the grid
        A = A_fn(); world = tv_layer(A, f)
        u = eout(clamp((kn + 48) / 12, 0, 1), 3); z0 = W / w; ty0 = H * 0.37 + 40
        zf = z0 * (1 - u) + 1.0 * u; px, py = W / 2 * (1 - u) + cx * u, ty0 * (1 - u) + cy * u
        M = np.float32([[zf, 0, px - zf * cx], [0, zf, py - zf * cy]])
        o = cv2.warpAffine(world, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        if kn < -48:                                                   # bezel closes in from top and bottom (6 frames)
            v = eout((kn + 54) / 6, 2); half = int((H / 2) * (1 - v) + (z0 * h / 2 + 4) * v)
            band = np.zeros((H, 1), np.float32); band[max(0, int(ty0) - half):int(ty0) + half] = 1
            band = band[:, :, None]
            o = A * band + o * (1 - band)
        return o
    if kn < -10:
        u = (kn + 36) / 26.0; content = A_fn() if kn < -16 else static_noise(f, 0.7) * 0.6 + B_fn() * 0.5
        world = tv_layer(content, f); zf = 1 + 0.25 * smooth(u)
        return zoom_about(world, cx, cy + 40 * math.sin(f * 0.08), zf)
    u = (kn + 11) / 11.0; zf = 1.25 * math.exp(math.log(H / h * 1.08 / 1.25) * ein(u, 2.0))
    world = tv_layer(B_fn(), f)
    o = radial_blur(world, cx, cy, zf, zf * (1 + 0.06 * u), 5)
    o = hyperspace(o, u, cx, cy)
    return np.clip(o + (u ** 4) * 0.5, 0, 1)

def crt_after(img, k):
    if k >= 12: return img
    u = 1 - k / 12.0
    yy = (np.arange(H) % 4 < 2).astype(np.float32)[:, None, None]
    o = img * (1 - 0.25 * u * yy); o = rgb_split(o, 14 * u)
    return np.clip(o + (0.45 if k < 2 else 0) * u, 0, 1)

def rewind_tr(s_prev, f, kn):
    """outgoing shot scrubs backwards fast with tracking noise (kn -8..-1)."""
    fr = max(s_prev["f0"], s_prev["f1"] - 1 - (kn + 9) * 6)
    o = render_shot(s_prev, fr)
    o = tracking(o, f, 0.8)
    return osd(o, f, "◀◀", a=0.9)

def tiles(A, B, k, n_x=5, n_y=9):
    """card flip: tiles turn over in a diagonal wave; each card's back face is a pastel gradient, edges catch neon light."""
    o = B * 0.18; tw, th2 = W // n_x, H // n_y
    for i in range(n_x):
        for j in range(n_y):
            d = (i + j) * 0.9; u = clamp((k - d) / 6, 0, 1)
            x0, y0 = i * tw, j * th2; x1, y1 = (W if i == n_x - 1 else x0 + tw), (H if j == n_y - 1 else y0 + th2)
            if u <= 0: o[y0:y1, x0:x1] = A[y0:y1, x0:x1]; continue
            if u >= 1: o[y0:y1, x0:x1] = B[y0:y1, x0:x1]; continue
            src = A if u < 0.5 else B; sx = abs(math.cos(math.pi * u)); sy = 1 + 0.08 * math.sin(math.pi * u)
            tile = src[y0:y1, x0:x1]; ww = max(2, int((x1 - x0) * sx)); hh = min(int((y1 - y0) * sy), y1 - y0 + 12)
            sq = cv2.resize(tile, (ww, hh), interpolation=cv2.INTER_LINEAR)
            g = np.linspace(1.15, 0.6, ww, dtype=np.float32)[None, :, None] if u < 0.5 else np.linspace(0.6, 1.15, ww, dtype=np.float32)[None, :, None]
            back = (PINK * (1 - np.linspace(0, 1, hh, dtype=np.float32)[:, None, None]) + CYAN * np.linspace(0, 1, hh, dtype=np.float32)[:, None, None])
            mix = clamp(1 - sx * 2.2, 0, 1)                       # near edge-on the card shows its glossy back
            sq = sq * g * (1 - mix) + back * mix * 0.85
            xs = x0 + ((x1 - x0) - ww) // 2; ys = y0 + ((y1 - y0) - hh) // 2; ya, yb = max(ys, 0), min(ys + hh, H)
            o[ya:yb, xs:xs + ww] = sq[ya - ys:yb - ys]
            o[ya:yb, xs:xs + 2] = WHITE * 0.9; o[ya:yb, xs + ww - 2:xs + ww] = (CYAN if (i + j) % 2 else PINK)
    return np.clip(o, 0, 1)

def neon_trace(A, B, Bmask, k, n=14):
    if k >= n + 6: return B
    m8 = (Bmask > 0.5).astype(np.uint8)
    cs, _ = cv2.findContours(m8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs: return B
    c = max(cs, key=cv2.contourArea)[:, 0, :]
    p = eout(k / n, 2); npts = max(2, int(len(c) * p))
    lay = np.zeros((H, W), np.float32)
    cv2.polylines(lay, [c[:npts].astype(np.int32)], False, 1.0, 5, cv2.LINE_AA)
    g = cv2.GaussianBlur(lay, (0, 0), 10) * 3
    inside = cv2.GaussianBlur(Bmask, (0, 0), 2)[..., None] * clamp((k - 4) / 8, 0, 1)
    outside = clamp((k - n) / 6, 0, 1)
    base = A * (1 - outside) * 0.35 + B * outside
    o = base * (1 - inside) + B * inside
    o = o + (lay[..., None] * WHITE + g[..., None] * PINK) * (1 - outside * 0.7)
    o = o + cv2.GaussianBlur(np.roll(lay, 8, axis=1), (0, 0), 6)[..., None] * CYAN * 0.8 * (1 - outside)
    return np.clip(o, 0, 1)

_INK = {}
def ink(A, B, k, f):
    """blood drop -> splat -> blood blooms across the frame -> the next shot is inside the blood."""
    c = (W / 2, H * 0.42)
    if "n" not in _INK:
        rng = np.random.default_rng(4); nz = cv2.resize(rng.random((24, 14)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        nz2 = cv2.resize(rng.random((96, 54)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        _INK["n"] = nz * 260 + nz2 * 60; _INK["r"] = np.sqrt((_GX - c[0]) ** 2 + (_GY - c[1]) ** 2)
    if k < 0:                                                   # the drop falls (kn -8..-1)
        u = (k + 9) / 9.0; y = -60 + (c[1] + 60) * ein(u, 2)
        o = A.copy(); lay = np.zeros((H, W), np.float32)
        cv2.ellipse(lay, (int(c[0]), int(y)), (16, int(22 + 20 * u)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
        lay = cv2.GaussianBlur(lay, (0, 0), 1.5)[..., None]
        return np.clip(o * (1 - lay) + RED * 0.9 * lay + cv2.GaussianBlur(lay[..., 0], (0, 0), 3)[..., None] * 0.15, 0, 1)
    R = 1900 * ein(clamp(k / 16, 0, 1), 1.4) + 30
    m = np.clip((R + _INK["n"] - _INK["r"]) / 25, 0, 1)
    rim = np.clip(1 - np.abs(R + _INK["n"] - _INK["r"]) / 45, 0, 1)
    reveal = clamp((k - 4) / 10, 0, 1)
    blood = RED * (0.55 + 0.25 * np.clip(_INK["n"] / 320, 0, 1))[..., None]
    inner = blood * (1 - reveal) + B * reveal
    o = A * (1 - m[..., None]) + inner * m[..., None]
    o = o * (1 - rim[..., None] * 0.6) + rim[..., None] * RED * 0.45
    if k < 10:                                                 # splatter droplets
        rng = np.random.default_rng(11)
        for _ in range(26):
            a = rng.uniform(0, 6.28); dd = rng.uniform(80, 420) * eout(k / 6, 2)
            cv2.circle(o, (int(c[0] + math.cos(a) * dd), int(c[1] + math.sin(a) * dd)), int(rng.uniform(4, 16)), tuple(float(v) for v in RED * 0.8), -1, cv2.LINE_AA)
    return np.clip(o, 0, 1)

def ripple(A, B, k, n=14, c=(W / 2, H * 0.45)):
    if k >= n: return B
    r = np.sqrt((_GX - c[0]) ** 2 + (_GY - c[1]) ** 2); u = k / n
    amp = 12 * (1 - u) ** 1.5; wav = np.sin(r / 38 - k * 0.9) * amp
    dx = (_GX - c[0]) / (r + 1) * wav; dy = (_GY - c[1]) / (r + 1) * wav
    Aw = cv2.remap(A, (_GX + dx).astype(np.float32), (_GY + dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    Bw = cv2.remap(B, (_GX + dx).astype(np.float32), (_GY + dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    R = 1700 * eout(u, 2); m = np.clip((R - r) / 80, 0, 1)[..., None]
    ring = np.exp(-((r - R) / 20) ** 2)[..., None]
    return np.clip(Aw * (1 - m) + Bw * m + ring * CYAN * 0.4, 0, 1)

def ripple_pre(A, kn):
    """gentle surface tremble before the drop hits the water (kn -4..-1)."""
    r = np.sqrt((_GX - W / 2) ** 2 + (_GY - H * 0.45) ** 2); amp = 3 + 2 * (kn + 4)
    wav = np.sin(r / 30 - kn * 1.3) * amp; dx = (_GX - W / 2) / (r + 1) * wav; dy = (_GY - H * 0.45) / (r + 1) * wav
    return cv2.remap(A, (_GX + dx).astype(np.float32), (_GY + dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def glints(out, f, k):
    """vaporwave sparkle glints on the brightest points (on montage downbeats)."""
    if k < 0 or k > 16: return out
    small = cv2.GaussianBlur(cv2.resize(out.mean(2), (W // 8, H // 8)), (0, 0), 1)
    pts = []; s2 = small.copy()
    for _ in range(3):
        y, x = np.unravel_index(np.argmax(s2), s2.shape); pts.append((x * 8 + 4, y * 8 + 4)); s2[max(0, y - 10):y + 10, max(0, x - 10):x + 10] = 0
    lay = np.zeros((H, W), np.float32); a = math.sin(math.pi * k / 16)
    for i, (x, y) in enumerate(pts):
        L = int((40 + 30 * i) * a); 
        cv2.line(lay, (x - L, y), (x + L, y), 1.0, 2, cv2.LINE_AA); cv2.line(lay, (x, y - L), (x, y + L), 1.0, 2, cv2.LINE_AA)
        cv2.circle(lay, (x, y), 4, 1.0, -1, cv2.LINE_AA)
    return np.clip(out + (lay[..., None] * WHITE + cv2.GaussianBlur(lay, (0, 0), 6)[..., None] * PINK * 2) * a * 0.9, 0, 1)

def pastel_leak(out, f, fc):
    k = f - fc
    if not (0 <= k < 30): return out
    u = k / 30.0; px = -300 + (W + 600) * u
    g = np.exp(-(((_GX - px) / 420) ** 2 + ((_GY - H * 0.3) / 900) ** 2)) * math.sin(math.pi * u)
    col = PINK * 0.6 + PEACH * 0.4
    return np.clip(1 - (1 - out) * (1 - g[..., None] * col * 0.55), 0, 1)

# ============================================================================ v6 typography
def retro_word(w, size, path, emph=False):
    m = text_mask(w, path, size)
    pad = 40; mm = np.pad(m, pad); h2, w2 = mm.shape
    rgba = np.zeros((h2, w2, 4), np.float32)
    for dxy, col in (((10, 8), PINK), ((-6, 5), CYAN)):        # retro offset echoes
        sh = np.roll(np.roll(mm, dxy[1], 0), dxy[0], 1)
        rgba[..., :3] = rgba[..., :3] * (1 - sh[..., None]) + col * sh[..., None]; rgba[..., 3] = np.maximum(rgba[..., 3], sh * 0.85)
    if emph:                                                   # chrome: sky -> white -> pink horizon
        y = np.linspace(0, 1, h2, dtype=np.float32)[:, None, None]
        fill = np.where(y < 0.52, CYAN * (1 - y * 1.6) + WHITE * (y * 1.6), PINK * 0.9 + WHITE * 0.1 * (1 - y))
        fill = np.clip(fill, 0, 1)
    else:
        fill = np.broadcast_to(WHITE, (h2, w2, 3))
    rgba[..., :3] = rgba[..., :3] * (1 - mm[..., None]) + fill * mm[..., None]; rgba[..., 3] = np.maximum(rgba[..., 3], mm)
    sh = cv2.GaussianBlur(mm, (0, 0), 10) * 0.65
    base = np.zeros_like(rgba); base[..., 3] = sh
    a1 = rgba[..., 3:4]; comb = base.copy(); comb[..., :3] = rgba[..., :3]; comb[..., 3:4] = np.maximum(a1, sh[..., None])
    comb[..., :3] = rgba[..., :3] * (a1 / np.maximum(comb[..., 3:4], 1e-4))
    return comb

def vo_captions(out, f):
    """two-line lockups: each word eases in (fade + rise + blur-to-sharp) on its spoken time; 'vanish' lines dissolve."""
    t = f / FPS; size = 78
    for vi, words, s_end, emph, style in E.CAPS:
        a, b_, at = E.VO[vi]
        def d2e(sx): return at + (sx - a)
        t_in = d2e(words[0][1]) - 0.05; t_out = d2e(s_end) + 0.25
        if not (t_in <= t < t_out + 0.6): continue
        kout = (t - t_out) * FPS; fade = 1.0 if (kout <= 0 or style == "vanish") else clamp(1 - kout / 10, 0, 1)
        path = F_BLDI; fnt = font(path, size); sp = fnt.getlength(" ")
        for ln in (0, 1):
            row = [(w, ws) for w, ws, l_ in words if l_ == ln]
            if not row: continue
            Y = E.CAP_Y[ln]
            vs = [eout(((t - d2e(ws)) * FPS + 1) / 12, 3) for _, ws in row]
            widths = [fnt.getlength(w) + 30 for w, _ in row]
            total = sum((wd + sp) * v for wd, v in zip(widths, vs)) - sp * vs[-1]
            x = W / 2 - max(total, 0) / 2
            pv = clamp((t - t_out + 0.2 - 0.12 * ln) / 0.5, 0, 1) if style == "vanish" else 0.0
            for wi, ((w, ws), wd, v) in enumerate(zip(row, widths, vs)):
                if v > 0.001:
                    L = retro_word(w, size, path, emph=w in emph)
                    if v < 1: L = cv2.GaussianBlur(L, (0, 0), 0.1 + 6 * (1 - v))
                    px, py = int(x + wd / 2 - L.shape[1] / 2), int(Y + 26 * (1 - v) - L.shape[0] / 2)
                    if pv > 0:
                        bs = 8; gh, gw = L.shape[0] // bs + 1, L.shape[1] // bs + 1
                        thr = cv2.resize(np.random.default_rng(len(w) + 7 * wi).random((gh, gw)).astype(np.float32) * 0.5 + np.linspace(0.5, 0, gw)[None, :],
                                         (gw * bs, gh * bs), interpolation=cv2.INTER_NEAREST)[:L.shape[0], :L.shape[1]]
                        gone = np.clip((pv - thr) / 0.3, 0, 1)
                        Lk = L.copy(); Lk[..., 3] *= (thr > pv)
                        out = paste(out, Lk, px, py, v)
                        for lag, la in ((0.0, 0.85), (0.12, 0.35)):
                            fl = L.copy(); ge = np.clip(gone - lag, 0, 1)
                            fl[..., 3] = L[..., 3] * (ge > 0) * (ge < 1) * la
                            fl[..., :3] = PINK if lag == 0 else CYAN
                            out = paste(out, cv2.warpAffine(fl, np.float32([[1, 0, 150 * pv], [0, 1, -50 * pv]]), (L.shape[1], L.shape[0])), px, py, 1 - pv * 0.7)
                    else:
                        out = paste(out, L, px, py, v * fade)
                x += (wd + sp) * v
    return out

JP = [(0, "私は多くの人を消してきた"), (1, "今度は私が消える番だ")]
def jp_sub(out, f):
    t = f / FPS
    for vi, txt in JP:
        a, b_, at = E.VO[vi]; t0 = at + 0.25; t1 = at + (b_ - a) + 0.15
        if not (t0 <= t < t1 + 0.25): continue
        v = eout((t - t0) * FPS / 14, 3); fade = 1.0 if t < t1 else clamp(1 - (t - t1) * FPS / 12, 0, 1)
        m = text_mask(txt, F_JP, 38, tracking=10)
        L = shadowed(m, PINK * 0.6 + WHITE * 0.4, blur=6, sa=0.7)
        out = paste(out, L, int(W / 2 - L.shape[1] / 2), int(1540 + 10 * (1 - v)), v * fade * 0.95)
    return out

def miami_title(out, f):
    fs = E.fh(E.HDROP); k = f - fs
    if not (2 <= k < 70): return out
    kk = k - 2; v = eout(kk / 12, 3); fade = clamp((70 - k) / 10, 0, 1)
    word = getattr(E, "DROP_TITLE", None)
    if not word: return out
    m = text_mask(word, F_BI, 230, tracking=6); hh, ww = m.shape
    y = np.linspace(0, 1, hh, dtype=np.float32)[:, None, None]
    fill = np.where(y < 0.55, CYAN * (1 - y * 1.5) + WHITE * np.clip(y * 1.8, 0, 1), PINK * (0.7 + 0.3 * y))
    fill = np.clip(fill, 0, 1)
    if kk > 10:
        xs = np.arange(ww)[None, :] + 0.5 * np.arange(hh)[:, None]; pos = -200 + (ww + 500) * clamp((kk - 10) / 28, 0, 1)
        fill = np.clip(fill + np.exp(-((xs - pos) / 40) ** 2)[..., None] * 0.7, 0, 1)
    ol = np.clip(cv2.dilate(m, np.ones((9, 9), np.uint8)) - m, 0, 1)
    rgba = np.zeros((hh, ww, 4), np.float32)
    rgba[..., :3] = PINK * ol[..., None] + fill * m[..., None]; rgba[..., 3] = np.maximum(m, ol)
    glow = np.zeros_like(rgba); glow[..., :3] = PINK; glow[..., 3] = cv2.GaussianBlur(np.maximum(m, ol), (0, 0), 24) * 0.6
    sx = 1 + 0.6 * (1 - v)
    rgba = cv2.resize(rgba, (int(ww * sx), hh)); glow = cv2.resize(glow, (int(ww * sx), hh))
    x0 = int(W / 2 - rgba.shape[1] / 2 - 700 * (1 - v)); y0 = 1380
    if v < 1: rgba = hblur(rgba, 10 + 200 * (1 - v))
    out = paste(out, glow, x0, y0, fade * v); out = paste(out, rgba, x0, y0, fade)
    return out

def neon_sign(out, f):
    """IT / WAS / ME. — neon tube lettering; each word eases in and flickers on with its spoken word."""
    t = f / FPS; t_end = E.DUR - 40 / FPS
    if not getattr(E, "END_CAP", None) or not (E.END_CAP[0][1] - 0.05 <= t < t_end): return out
    def tube_word(word, size):
        m = text_mask(word, F_BOLD, size, tracking=8)
        tube = np.clip(cv2.dilate(m, np.ones((7, 7), np.uint8)) - cv2.erode(m, np.ones((7, 7), np.uint8)), 0, 1)
        return tube, cv2.erode(tube, np.ones((3, 3), np.uint8))
    lay = {}
    (it_t, _), (was_t, _) = tube_word("IT", 130), tube_word("WAS", 130); gap = 46
    x_it = int(W / 2 - (it_t.shape[1] + gap + was_t.shape[1]) / 2)
    lay["IT"] = (x_it, 1270, 130, CYAN); lay["WAS"] = (x_it + it_t.shape[1] + gap, 1270, 130, CYAN)
    me_t, _ = tube_word("ME.", 190); lay["ME."] = (int(W / 2 - me_t.shape[1] / 2), 1420, 190, PINK)
    for word, tw in E.END_CAP:
        k = (t - tw) * FPS
        if k < 0: continue
        flick = [0.55, 0.15, 0.7, 0.3, 1, 0.55, 1, 1, 0.85, 1]; a = flick[int(k)] if k < len(flick) else (0.92 + 0.08 * math.sin(f * 1.7 + len(word)))
        v = eout(k / 14, 3); a *= v * clamp((t_end - t) * FPS / 8, 0, 1)
        x0, y, size, col = lay[word]; y = int(y + 26 * (1 - v))
        tube, core = tube_word(word, size)
        if v < 1: tube = cv2.GaussianBlur(tube, (0, 0), 0.1 + 5 * (1 - v)); core = cv2.GaussianBlur(core, (0, 0), 0.1 + 5 * (1 - v))
        rgba = np.zeros(tube.shape + (4,), np.float32)
        rgba[..., :3] = col * tube[..., None] * 0.9 + WHITE * core[..., None] * 0.9; rgba[..., 3] = tube
        glow = np.zeros_like(rgba); glow[..., :3] = col; glow[..., 3] = cv2.GaussianBlur(tube, (0, 0), 16) * 1.4
        out = paste(out, glow, x0, y, a); out = paste(out, rgba, x0, y, a)
    return out

# ============================================================================ v6 frame
def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999; t = f / FPS
    P = prev_shot(s); tin = s.get("tin"); tout = s.get("tout")
    person = None
    fr_ = pause_frame(s, f)
    if s.get("seg"): out, person = render_shot(s, fr_, want_mask=True)
    else: out = render_shot(s, fr_)
    if s.get("vapor_bg"): out = vapor_tune(out, person, k, f)
    if s.get("echo"): out = echo(out, s, f)
    if s.get("palms"): out = palm_shadow(out, f)
    if s.get("motes"): out = motes(out, f)
    out = pause_fx(out, s, f)
    if s.get("vanish"):
        tv0 = E.VANISH_T0
        out = vanish(out, person, f, t, tv0, s["t1"] - 0.08)
    # ---- incoming
    if tin in TR2 and k < TR2[tin][2]: out = TR2[tin][0](last_visible(P), out, k, f, P, s)
    elif tin == "tape_in": out = tape_in(out, f, k)
    elif tin == "vhs_roll" and k < 8: out = vhs_roll(None, out, k, f)
    elif tin == "kaleido" and k < 12: out = kaleido(out, 1 - eout(k / 12, 2), -1.2 * (1 - k / 12))
    elif tin == "pixel_sort" and k < 12: out = melt(last_frame_of(P), out, 0.55 + 0.45 * eout(k / 12, 2))
    elif tin == "crt": out = crt_after(out, k)
    elif tin == "tear" and k < 9: out = tear(last_frame_of(P), out, k, f)
    elif tin == "logo" and k < 11: out = logo_neon(last_frame_of(P), out, k, f)
    elif tin == "rewind" and k < 5: out = tracking(out, f, 0.6 * (1 - k / 5))
    elif tin == "tiles" and k < 20: out = tiles(last_frame_of(P), out, k)
    elif tin == "neon_trace" and k < 20:
        B, Bm = render_shot(s, f, want_mask=True); out = neon_trace(last_frame_of(P), B, Bm, k)
    elif tin == "ink" and k < 18: out = ink(last_frame_of(P), out, k, f)
    elif tin == "ripple" and k < 14: out = ripple(last_frame_of(P), out, k)
    elif tin == "flash" and k < 6:
        fl = [0.7, 0.4, 0.18, 0.06, 0, 0][k]; out = np.clip(out * (1 + 1.1 * fl) + fl * 0.25 * WHITE + fl * 0.12 * PINK, 0, 1); out = rgb_split(out, 14 * math.exp(-k / 2))
    # ---- outgoing (start before the cut)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, render_shot(n_, n_["f0"], False), kn, f, s, n_)
        if nt == "vhs_roll" and kn >= -5: out = vhs_roll(out, None, kn, f)
        if nt == "kaleido" and kn >= -8: out = kaleido(out, ein((kn + 9) / 9, 2), 1.4 * ein((kn + 9) / 9, 2))
        if nt == "pixel_sort" and kn >= -8: out = melt(out, render_shot(n_, n_["f0"], False), 0.55 * ein((kn + 9) / 9, 1.4))
        if tout == "crt" and kn >= -54:
            out = crt_through(lambda: render_shot(s, f), lambda: render_shot(n_, n_["f0"], False), f, kn)
        if nt == "rewind" and kn >= -8: out = rewind_tr(s, f, kn)
        if nt == "ink" and kn >= -8: out = ink(out, None, kn, f)
        if nt == "ripple" and kn >= -4: out = ripple_pre(out, kn)
        if nt == "logo" and kn >= -12: out = logo_neon(out, render_shot(n_, n_["f0"], False), kn, f)
    if tout == "rewind_end": out = rewind_end(out, f, s)
    # ---- graphics + type
    in_static = (f < 8) or (s.get("tout") == "rewind_end" and s["f1"] - f <= 8)
    if not in_static:
        out = vo_captions(out, f); out = miami_title(out, f); out = neon_spill(out, f); out = neon_sign(out, f)
        h = t / E.HB + E.H0
        if E.MONTAGE[0] <= h < E.MONTAGE[1]:
            kb = int(((h - E.H0) % 8) * E.HB * FPS)
            out = glints(out, f, kb); out = pastel_leak(out, f, f - kb)
        if f < 100: out = osd(out, f, "PLAY ▶", y=235, a=clamp((f - 10) / 6, 0, 1) * clamp((100 - f) / 10, 0, 1))
        out = bloom(out, 0.30); out = anamorphic(out, 0.22)
        out = vhs(out, f, 0.9 if t < E.th(E.HDROP) else 0.5)
        out = out * VIG + grain(f, 0.016)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)

def beat_bounce(f):
    t = f / FPS; h = t / E.HB + E.H0
    if not (E.MONTAGE[0] <= h < E.MONTAGE[1]): return 1.0
    ph = ((h - E.H0) % 2) * E.HB
    return 1 + 0.016 * math.exp(-ph / 0.10)

def init_hits():
    HITS.clear()
    for i, h in enumerate(range(E.MONTAGE[0], E.MONTAGE[1], 8)):
        a = (22, 10, 14, 10, 12)[min(i, 4)]
        HITS.append((E.fh(h), a, 4.5))

# ============================================================================ v6 rev 2 — new transitions + graphics
# every function: fn(A, B, j, f, sa, sb). j < 0: frames before the cut (A = outgoing live, B = incoming first frame);
# j >= 0: frames after the cut (A = outgoing last frame, B = incoming live).
_POLR = {}
def polar():
    if "r" not in _POLR:
        dx, dy = _GX - W / 2, _GY - H / 2
        _POLR["r"] = np.sqrt(dx * dx + dy * dy); _POLR["a"] = np.arctan2(dy, dx)
    return _POLR["r"], _POLR["a"]

def face_scr(s, f):
    """face centre, width and both eyes in output px for shot s at frame f (None without a track)."""
    t, u, _ = src_time(s, f); fa = face_at(s, t)
    if fa is None: return None
    x, y, sc = to_screen(s, f, fa[0], fa[1])
    e1 = to_screen(s, f, fa[3][0], fa[3][1])[:2]; e2 = to_screen(s, f, fa[3][2], fa[3][3])[:2]
    return x, y, fa[2] * sc, e1, e2

def neon_glow(lay, col, sig=10, k=1.6):
    return lay[..., None] * WHITE * 0.9 + cv2.GaussianBlur(lay, (0, 0), sig)[..., None] * col * k

# ---- 1. into his eye -> hexagonal camera aperture opens on the next shot
def aperture(r, rot, n=6):
    rr, aa = polar(); seg = 2 * math.pi / n
    a = np.mod(aa - rot, seg) - seg / 2
    sd = r * math.cos(math.pi / n) - rr * np.cos(a)            # signed distance to the hexagon edge (px)
    return sd

def eye_dive(A, B, j, f, sa, sb):
    if j < 0:
        u = (j + 15) / 15.0; fs = face_scr(sa, f)
        if fs is None: ex, ey, fw = W / 2, H * 0.37, 320.0
        else:
            e = min((fs[3], fs[4]), key=lambda q: abs(q[0] - W / 2)); ex, ey, fw = e[0], e[1], fs[2]
        Z = max(10.0, W / (0.16 * fw))
        sc = math.exp(math.log(Z) * ein(u, 2.4)); v = eout(clamp(u / 0.7, 0, 1), 2)
        M = cv2.getRotationMatrix2D((ex, ey), 4 * u, sc); M[0, 2] += (W / 2 - ex) * v; M[1, 2] += (H / 2 - ey) * v
        o = cv2.warpAffine(A, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        if sc > 1.4: o = radial_blur(o, W / 2, H / 2, 1.0, 1.0 + 0.07 * min(1.0, sc / 8), 6)
        rr, _ = polar(); pr = 1250 * ein(clamp((u - 0.58) / 0.42, 0, 1), 1.8)
        if pr > 1:                                                    # the pupil swallows the frame
            pm = np.clip((pr - rr) / 14, 0, 1)[..., None]
            ring = np.exp(-((rr - pr) / (10 + 0.05 * pr)) ** 2)[..., None]
            o = o * (1 - pm) + 0.008 * pm + ring * (PINK * 0.55 + CYAN * 0.45) * 0.9
        return np.clip(rgb_split(o, 12 * u), 0, 1)
    u = (j + 1) / 15.0
    sd = aperture(1150 * eout(u, 2.4), rot=1.2 * (1 - u))
    m = np.clip(sd / 3.0, 0, 1)[..., None]
    Bz = zoom_about(B, W / 2, H / 2, 1.3 - 0.3 * eout(u, 2))
    edge = np.exp(-(sd / 7) ** 2)[..., None]
    blades = np.clip(-sd / 900, 0, 1)[..., None]                    # faint blade shading outside the opening
    o = Bz * m + (1 - m) * (0.012 + 0.05 * blades * (PINK * 0.5 + CYAN * 0.5))
    o = o + edge * (CYAN * 0.6 + WHITE * 0.4) * (1 - u) * 1.2
    return np.clip(rgb_split(o, 10 * (1 - u)), 0, 1)

# ---- 2. reassemble: the next scene builds itself from flying pixel blocks (reverse of the dissolve)
_ASM = {}
def assemble(A, B, j, f, sa, sb, n=24):
    u = j / n; bs = 18; gh, gw = -(-H // bs), W // bs
    if "thr" not in _ASM:
        rng = np.random.default_rng(11)
        thr = (rng.random((gh, gw)) * 0.45 + np.linspace(0.55, 0.0, gw)[None, :]).astype(np.float32)
        _ASM.update(thr=thr, vx=rng.uniform(250, 900, (gh, gw)), vy=rng.uniform(-420, 160, (gh, gw)), ph=rng.uniform(0, 6.28, (gh, gw)))
    thr = _ASM["thr"]; g = np.clip((u * 1.3 - thr) / 0.42, 0, 1)
    landed = cv2.resize((g >= 1).astype(np.float32), (gw * bs, gh * bs), interpolation=cv2.INTER_NEAREST)[:H, :W]
    o = A * (1 - eout(u, 2)) * (1 - landed[..., None]) + B * landed[..., None]
    lb = (landed > 0.5).astype(np.uint8)
    edge = cv2.GaussianBlur(cv2.morphologyEx(lb, cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8)).astype(np.float32), (0, 0), 1.5)
    o = o + edge[..., None] * CYAN * 0.8 * (1 - u)
    col = cv2.resize(B, (gw, gh), interpolation=cv2.INTER_AREA)
    js, is_ = np.nonzero((g > 0) & (g < 1))
    for jj, ii in zip(js, is_):
        gg = float(g[jj, ii]); e = eout(gg, 2.2)
        x = ii * bs + _ASM["vx"][jj, ii] * (1 - e); y = jj * bs + _ASM["vy"][jj, ii] * (1 - e) + 16 * math.sin(_ASM["ph"][jj, ii] + 8 * e)
        sz = max(3, int(bs * (0.35 + 0.65 * e))); xi, yi = int(x), int(y)
        if xi < 0 or yi < 0 or xi + sz >= W or yi + sz >= H: continue
        tint = PINK if (ii + jj) % 3 == 0 else (CYAN if (ii + jj) % 3 == 1 else WHITE)
        c = np.clip(col[jj, ii] * (0.4 + 0.6 * gg) + tint * 0.5 * (1 - gg), 0, 1); a = 0.35 + 0.6 * gg
        o[yi:yi + sz, xi:xi + sz] = o[yi:yi + sz, xi:xi + sz] * (1 - a) + c * a
    return np.clip(o, 0, 1)

# ---- 3. polaroid: flash, the frame freezes into a print that is tossed away
_PLD = {}
def polaroid(A, B, j, f, sa, sb):
    if j < 0:
        fl = ein((j + 7) / 7.0, 3)
        return np.clip(A * (1 + 1.3 * fl) + 0.4 * fl, 0, 1)
    key = sa["n"]
    if _PLD.get("key") != key:
        b = 46; card = np.ones((H + b + 4 * b, W + 2 * b, 4), np.float32)
        card[..., :3] = np.array([0.93, 0.95, 0.96], np.float32)
        card[b:b + H, b:b + W, :3] = np.clip(A * 1.05 + 0.03, 0, 1)
        _PLD.update(key=key, card=card, b=b)
    card, b = _PLD["card"], _PLD["b"]; ch, cw = card.shape[:2]
    u1 = eout(clamp(j / 5.0, 0, 1), 3); u2 = ein(clamp((j - 6) / 10.0, 0, 1), 2.2)
    sc = 1.0 - 0.36 * u1 - 0.1 * u2; rot = -7 * u1 - 24 * u2
    cx, cy = W / 2 + 1250 * u2, H / 2 + 40 * u1 + 520 * u2
    M = cv2.getRotationMatrix2D((cw / 2, ch / 2 - 1.5 * b), rot, sc)   # rotate about the photo centre
    M[0, 2] += cx - cw / 2; M[1, 2] += cy - (ch / 2 - 1.5 * b)
    cd = cv2.warpAffine(card, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    al = cd[..., 3:4]
    shd = cv2.GaussianBlur(np.roll(np.roll(cd[..., 3], 34, 0), 26, 1), (0, 0), 22)[..., None] * 0.55
    Bz = zoom_about(B, W / 2, H / 2, 1.08 - 0.08 * eout(j / 16.0, 2))
    o = Bz * (1 - shd) * (1 - al) + cd[..., :3] * al
    fl = clamp(1 - j / 4.0, 0, 1)
    return np.clip(o + 0.5 * fl * al + 0.25 * fl, 0, 1)

# ---- 4. face-match morph: his face slides and scales onto his face in the next shot
def facematch(A, B, j, f, sa, sb):
    fa = face_scr(sa, sa["f1"] - 1); fb = face_scr(sb, sb["f0"])
    if fa is None or fb is None: fa = fb = (W / 2, H * 0.37, 300.0, None, None)
    mid = ((fa[0] + fb[0]) / 2, (fa[1] + fb[1]) / 2, math.sqrt(fa[2] * fb[2]))
    def sim(src, dst, v):
        x = src[0] + (dst[0] - src[0]) * v; y = src[1] + (dst[1] - src[1]) * v; w = src[2] * (dst[2] / src[2]) ** v
        s_ = w / src[2]; return np.float32([[s_, 0, x - s_ * src[0]], [0, s_, y - s_ * src[1]]])
    if j < 0:
        v = ein((j + 8) / 8.0, 2); o = cv2.warpAffine(A, sim(fa, mid, v), (W, H), borderMode=cv2.BORDER_REFLECT)
        o = radial_blur(o, mid[0], mid[1], 1.0, 1.0 + 0.05 * v, 5)
        if j >= -2:
            Bm = cv2.warpAffine(B, sim(fb, mid, 1.0), (W, H), borderMode=cv2.BORDER_REFLECT); w = 0.3 if j == -2 else 0.55
            o = o * (1 - w) + Bm * w
        fl = 0.35 * ein((j + 8) / 8.0, 3)
        return np.clip(rgb_split(o, 14 * v) + fl, 0, 1)
    v = eout((j + 1) / 8.0, 2); o = cv2.warpAffine(B, sim(fb, mid, 1 - v), (W, H), borderMode=cv2.BORDER_REFLECT)
    o = radial_blur(o, mid[0], mid[1], 1.0, 1.0 + 0.05 * (1 - v), 5)
    if j <= 1:
        Am = cv2.warpAffine(A, sim(fa, mid, 1.0), (W, H), borderMode=cv2.BORDER_REFLECT); w = 0.4 if j == 0 else 0.2
        o = o * (1 - w) + Am * w
    return np.clip(rgb_split(o, 14 * (1 - v)) + 0.3 * (1 - v) ** 2, 0, 1)

# ---- 5. 3D cube: the frame becomes a cube that turns over the vapor sunset world
def cube(A, B, j, f, sa, sb, n=9):
    u = clamp((j + n + 0.5) / (2 * n), 0, 1); th = math.radians(90 * smooth(u)); a = W / 2
    pull = math.sin(math.pi * u) * 0.75 * W; D = 2.0 * W
    def proj(p):
        x, y, z = p; xr = x * math.cos(th) + z * math.sin(th); zr = -x * math.sin(th) + z * math.cos(th)
        zw = zr + a + pull; return (W / 2 + D * xr / (zw + D), H / 2 + D * y / (zw + D)), (xr, y, zr + a + pull)
    hy = H / 2
    faces = [(A, [(-a, -hy, -a), (a, -hy, -a), (a, hy, -a), (-a, hy, -a)], (0, 0, -1)),
             (B, [(a, -hy, -a), (a, -hy, a), (a, hy, a), (a, hy, -a)], (1, 0, 0))]
    o = vapor_world(f) * 0.9; glow = np.zeros((H, W), np.float32)
    for img, cs, nrm in faces:
        P = [proj(c) for c in cs]; q = np.float32([p[0] for p in P])
        cxw = np.mean([p[1] for p in P], 0); nx = nrm[0] * math.cos(th) + nrm[2] * math.sin(th); nz = -nrm[0] * math.sin(th) + nrm[2] * math.cos(th)
        view = np.array([cxw[0], cxw[1], cxw[2] + D]); dot = nx * view[0] + nz * view[2]
        if dot >= 0: continue
        lit = 0.45 + 0.55 * abs(dot) / (np.linalg.norm(view) + 1e-6)
        Mp = cv2.getPerspectiveTransform(np.float32([[0, 0], [W, 0], [W, H], [0, H]]), q)
        wi = cv2.warpPerspective(img * lit, Mp, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
        wm = cv2.warpPerspective(np.ones((H, W), np.float32), Mp, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)[..., None]
        o = o * (1 - wm) + wi * wm
        cv2.polylines(glow, [q.astype(np.int32)], True, 1.0, 3, cv2.LINE_AA)
    o = o + neon_glow(glow, PINK * 0.6 + CYAN * 0.4, 9, 1.4) * math.sin(math.pi * u)
    return np.clip(o, 0, 1)

# ---- 6. through the sun: a striped retro sun rises, the camera flies through its stripes
def sun_through(A, B, j, f, sa, sb, n=10):
    u = clamp((j + n + 0.5) / (2 * n), 0, 1)
    rise = eout(clamp(u / 0.45, 0, 1), 2.5); fly = ein(clamp((u - 0.42) / 0.58, 0, 1), 2.2)
    R0 = W * 0.46; cy0 = H + R0 + 40 - (H + R0 + 40 - H * 0.52) * rise
    Z = math.exp(math.log(9.0) * fly); fx, fy = W / 2, cy0 + R0 * 0.55     # zoom about a point inside the stripes
    R = R0 * Z; cy = fy + (cy0 - fy) * Z; cx = fx
    yy = _GY; d = np.sqrt((_GX - cx) ** 2 + (yy - cy) ** 2)
    inside = np.clip((R - d) / 3.0, 0, 1)
    yt = cy - 0.12 * R; yn = np.clip((yy - yt) / (1.12 * R), 0, 1)
    period = 1.0 / 7; ph = np.mod(yn, period) / period
    gapf = np.clip(0.10 + 0.55 * yn + 1.15 * fly ** 1.4, 0, 1.05) * (yy > yt)
    gap = np.clip((gapf - ph) * 40, 0, 1) * (yy > yt)
    grad = np.clip((yy - (cy - R)) / (2 * R), 0, 1)[..., None]
    suncol = np.clip(np.array([0.30, 0.88, 1.0], np.float32) * (1 - grad) + np.array([0.70, 0.22, 1.0], np.float32) * grad, 0, 1)
    under = A if j < 0 else B
    bar = (inside * (1 - gap))[..., None]; hole = (inside * gap)[..., None]
    o = under * (1 - inside[..., None]) + suncol * bar + B * hole
    halo = cv2.GaussianBlur(cv2.resize(inside, (W // 4, H // 4)), (0, 0), 14)
    o = o + cv2.resize(halo, (W, H))[..., None] * PINK * 0.45 * (1 - inside[..., None]) * (1 - fly)
    return np.clip(o, 0, 1)

# ---- 7. knife slash: a blade streak cuts the frame, the halves slide apart
_SLX = {}
def slash(A, B, j, f, sa, sb):
    P0 = np.array([W * 0.52, H * 0.42]); dv = np.array([-0.45, 0.893]); nv = np.array([0.893, 0.45]); L = 1300
    side = (_GX - P0[0]) * nv[0] + (_GY - P0[1]) * nv[1]
    if j < 0:
        u = (j + 6) / 6.0; S = P0 - dv * L; Eend = S + dv * 2 * L * eout(u, 2.2)
        lay = np.zeros((H, W), np.float32)
        cv2.line(lay, tuple(int(v) for v in S), tuple(int(v) for v in Eend), 1.0, 4, cv2.LINE_AA)
        tail = S + dv * 2 * L * max(0.0, eout(u, 2.2) - 0.35)
        cv2.line(lay, tuple(int(v) for v in tail), tuple(int(v) for v in Eend), 1.0, 9, cv2.LINE_AA)
        o = A * (1 - 0.25 * u) + neon_glow(lay, np.array([0.35, 0.25, 1.0], np.float32), 12, 2.0)
        return np.clip(o, 0, 1)
    u = (j + 1) / 14.0; sep = 680 * eout(u, 2.2); slip = 160 * eout(u, 2)
    Bz = zoom_about(B, W / 2, H / 2, 1.14 - 0.14 * eout(u, 2)); o = Bz.copy(); rims = np.zeros((H, W), np.float32)
    for sg in (1, -1):
        dx, dy = sg * (nv * sep / 2 + dv * slip)
        M = cv2.getRotationMatrix2D((float(P0[0]), float(P0[1])), sg * 7 * eout(u, 2), 1.0); M[0, 2] += dx; M[1, 2] += dy
        half = cv2.warpAffine(A, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        m = np.clip(sg * side / 1.5 + 0.5, 0, 1).astype(np.float32); mw = cv2.warpAffine(m, M, (W, H), borderValue=0)
        fade = 1 - ein(clamp((u - 0.55) / 0.45, 0, 1), 1.5)
        o = o * (1 - mw[..., None] * fade) + half * mw[..., None] * fade
        sw = cv2.warpAffine(np.exp(-(side / 4) ** 2).astype(np.float32), M, (W, H), borderValue=0) * fade
        rims = np.maximum(rims, sw)
    o = o + neon_glow(rims, np.array([0.30, 0.20, 1.0], np.float32), 8, 1.5) * (1 - u)
    if "drops" not in _SLX:
        rng = np.random.default_rng(5); t_ = rng.uniform(-0.6, 0.6, 46)
        _SLX["drops"] = [(P0 + dv * L * t_[i], rng.uniform(-1, 1) * nv * rng.uniform(250, 700) + dv * rng.uniform(-200, 200), rng.uniform(3, 9)) for i in range(46)]
    tt = j / FPS
    for p, v, r in _SLX["drops"]:
        x = p[0] + v[0] * tt; y = p[1] + v[1] * tt + 1600 * tt * tt
        if 0 <= x < W and 0 <= y < H: cv2.circle(o, (int(x), int(y)), int(r * (1 - 0.5 * u)), (0.04, 0.02, 0.62), -1, cv2.LINE_AA)
    return np.clip(o, 0, 1)

# ---- 8. film burn: pastel burn holes eat through the frame
_BRN = {}
def burn(A, B, j, f, sa, sb, n_pre=10, n_post=8):
    if "n" not in _BRN:
        rng = np.random.default_rng(8); acc = np.zeros((H // 4, W // 4), np.float32)
        for oc, amp in ((6, 1.0), (14, 0.5), (34, 0.25), (80, 0.12)):
            acc += cv2.resize(rng.random((oc * 16 // 9, oc)).astype(np.float32), (W // 4, H // 4), interpolation=cv2.INTER_CUBIC) * amp
        acc = (acc - acc.min()) / (acc.max() - acc.min())
        yy, xx = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32)
        bias = np.sqrt((xx / (W / 4) - 0.85) ** 2 + (yy / (H / 4) - 0.25) ** 2)        # starts from the top-right light
        _BRN["n"] = np.clip(acc * 0.6 + bias * 0.55, 0, None)
        _BRN["n"] = (_BRN["n"] - _BRN["n"].min()) / (_BRN["n"].max() - _BRN["n"].min())
    u = clamp((j + n_pre + 0.5) / (n_pre + n_post), 0, 1); T = -0.05 + 1.15 * ein(u, 1.5)
    N = cv2.resize(_BRN["n"], (W, H), interpolation=cv2.INTER_CUBIC)
    burned = np.clip((T - 0.04 - N) / 0.02, 0, 1)
    band = np.clip(1 - np.abs(N - (T - 0.02)) / 0.05, 0, 1)
    scorch = np.clip(1 - (N - T) / 0.10, 0, 1) * (N > T)
    hot = np.clip(1 - np.abs(N - (T - 0.02)) / 0.02, 0, 1)
    base = A * (1 - 0.55 * scorch[..., None]) + np.array([0.05, 0.25, 0.55], np.float32) * 0.35 * scorch[..., None]
    o = base * (1 - burned[..., None]) + B * burned[..., None]
    fire = np.array([0.35, 0.65, 1.0], np.float32) * band[..., None] * 1.2 + WHITE * hot[..., None] * 0.9 + PINK * cv2.GaussianBlur(band, (0, 0), 12)[..., None] * 0.9
    o = o + fire * (1 - burned[..., None] * 0.6)
    return np.clip(o + 0.18 * burned.mean() * (1 - u) * np.array([0.6, 0.8, 1.0], np.float32), 0, 1)

# ---- 9. through the sunglasses: the next shot shows up in his lenses, the camera dives into one
def lens_through(A, B, j, f, sa, sb):
    def barrel(img, k_, cx=W / 2, cy=H / 2, rn=W * 0.7):
        dx, dy = (_GX - cx) / rn, (_GY - cy) / rn; r2 = dx * dx + dy * dy; s_ = 1 + k_ * r2
        return cv2.remap(img, (cx + dx * s_ * rn).astype(np.float32), (cy + dy * s_ * rn).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if j < 0:
        u = (j + 13) / 13.0; fs = face_scr(sa, f)
        dy_, kx, ky = sa.get("lens", (0.04, 0.21, 0.15))
        if fs is None: lenses = [((W / 2, H * 0.37), 120.0, 120.0 * ky / kx)]
        else: lenses = [((e[0], e[1] + dy_ * fs[2]), kx * fs[2], ky * fs[2]) for e in (fs[3], fs[4])]
        tgt = min(lenses, key=lambda L_: abs(L_[0][0] - W / 2))
        o = A.copy(); refl = barrel(B, 0.35); op = 0.9 * smooth(clamp(u / 0.45, 0, 1))
        for (lx, ly), rx, ry in lenses:
            m = np.zeros((H, W), np.float32); cv2.ellipse(m, (int(lx), int(ly)), (int(rx), int(ry)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
            m = cv2.GaussianBlur(m, (0, 0), 2)[..., None]
            s_ = 2.2 * rx / W; M = np.float32([[s_, 0, lx - s_ * W / 2], [0, s_, ly - s_ * 0.37 * H]])     # his face at the lens centre
            r_ = cv2.warpAffine(refl, M, (W, H), borderMode=cv2.BORDER_REFLECT)
            xs = (_GX - lx) / rx + (_GY - ly) / ry; spec = np.exp(-((xs - (-1.5 + 3.5 * u)) / 0.25) ** 2)[..., None] * 0.5
            o = o * (1 - m * op) + (r_ * (0.75 + 0.25 * CYAN) + spec) * m * op
        (lx, ly), rx, ry = tgt; Z = (W * 0.75) / rx
        sc = math.exp(math.log(Z) * ein(clamp((u - 0.25) / 0.75, 0, 1), 2.3)); v = ein(u, 1.4)
        Mz = cv2.getRotationMatrix2D((lx, ly), 0, sc); Mz[0, 2] += (W / 2 - lx) * v; Mz[1, 2] += (H / 2 - ly) * v
        o = cv2.warpAffine(o, Mz, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        if sc > 1.5: o = radial_blur(o, W / 2, H / 2, 1.0, 1.0 + 0.05 * min(1, sc / 8), 5)
        return np.clip(o, 0, 1)
    u = (j + 1) / 10.0; v = eout(u, 2); s_ = 1.36 + (1 - 1.36) * v; yp = H / 2 * (1 - v) + 0.37 * H * v
    o = barrel(B, 0.35 * (1 - v))
    o = cv2.warpAffine(o, np.float32([[s_, 0, W / 2 - s_ * W / 2], [0, s_, yp - s_ * 0.37 * H]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    _, kx, ky = sa.get("lens", (0.04, 0.21, 0.15))
    rx = W * 0.75 * (1 + 3.0 * eout(u, 2)); ry = rx * ky / kx
    d = ((_GX - W / 2) / rx) ** 2 + ((_GY - H / 2) / ry) ** 2
    rim = np.clip((d - 1) * 6, 0, 1)[..., None]
    o = o * (0.85 + 0.15 * CYAN * (1 - u)) * (1 - rim) + rim * 0.02
    return np.clip(o, 0, 1)

# ---- 10. shadow pass: darkness swallows the frame, the next shot emerges brightest-first
def shadow_pass(A, B, j, f, sa, sb):
    dark = np.array([0.05, 0.0, 0.035], np.float32)
    if j < 0:
        u = (j + 11) / 11.0; Lm = cv2.GaussianBlur(A.mean(2), (0, 0), 6); T = 0.04 + 0.95 * ein(u, 1.4)
        m = np.clip((T - Lm) / 0.04, 0, 1)[..., None]; edge = np.exp(-((Lm - T) / 0.012) ** 2)[..., None] * (u > 0.15)
        return np.clip(A * (1 - m) + dark * m + edge * (VIOLET * 0.6 + PINK * 0.4) * 0.45, 0, 1)
    u = (j + 1) / 13.0; Lm = cv2.GaussianBlur(B.mean(2), (0, 0), 4); T = 1.0 - 1.08 * eout(u, 2)
    m = np.clip((Lm - T) / 0.05, 0, 1)[..., None]; edge = np.exp(-((Lm - T) / 0.02) ** 2)[..., None]
    return np.clip(B * m + dark * (1 - m) + edge * (PINK * 0.6 + CYAN * 0.4) * (1 - u) * 1.2, 0, 1)

TR2 = {"eye_dive": (eye_dive, 14, 14), "assemble": (assemble, 0, 24), "polaroid": (polaroid, 6, 16), "facematch": (facematch, 7, 7),
       "cube": (cube, 9, 9), "sun": (sun_through, 10, 10), "slash": (slash, 5, 14), "burn": (burn, 10, 8),
       "lens": (lens_through, 12, 9), "shadow": (shadow_pass, 10, 12)}

# ---- graphics
def vapor_tune(out, person, k, f):
    """after the CRT drop, Dexter stands in the vapor world; reality tunes in behind him, scanline by scanline."""
    if k >= 46 or person is None: return out
    yw = H * eout(clamp((k - 14) / 30, 0, 1), 2.2)
    rows = (np.arange(H)[:, None] < yw).astype(np.float32)
    bg = vapor_world(f)
    real = rows[..., None]; p = np.clip(person * 1.15, 0, 1)[..., None]
    o = out * p + (out * real + bg * (1 - real)) * (1 - p)
    line = np.exp(-((np.arange(H) - yw) / 5.0) ** 2)[:, None, None] * (yw < H - 2)
    return np.clip(o + line * (CYAN * 0.7 + WHITE * 0.3) * (1 - p * 0.7), 0, 1)

_HYP = {}
def hyperspace(o, u, cx=W / 2, cy=H * 0.42):
    """light streaks rushing out of the CRT screen as the camera dives in (u 0..1)."""
    if "s" not in _HYP:
        rng = np.random.default_rng(4); _HYP["s"] = [(rng.uniform(0, 6.283), rng.uniform(0.0, 1.0), rng.uniform(0.6, 1.0), int(rng.integers(0, 2))) for _ in range(140)]
    lay_p = np.zeros((H, W), np.float32); lay_c = np.zeros((H, W), np.float32)
    for a, ph, br, c in _HYP["s"]:
        r0 = ((ph + u * 1.6) % 1.0) ** 2 * 1300; r1 = r0 + 60 + 900 * u * ((ph + u) % 1.0)
        p0 = (int(cx + r0 * math.cos(a)), int(cy + r0 * math.sin(a))); p1 = (int(cx + r1 * math.cos(a)), int(cy + r1 * math.sin(a)))
        cv2.line(lay_p if c else lay_c, p0, p1, br, 2, cv2.LINE_AA)
    g = u ** 1.5
    return np.clip(o + (neon_glow(lay_p, PINK, 6, 1.2) + neon_glow(lay_c, CYAN, 6, 1.2)) * g * 0.8, 0, 1)

_PALM = {}
def palm_shadow(out, f, strength=0.32):
    """soft palm-frond shadows swaying across the frame (light through the palms)."""
    hw, hh = W // 2, H // 2; pad = 300; CX, CY = hw + 170, -30
    if "g" not in _PALM:
        g = np.zeros((hh + 2 * pad, hw + 2 * pad), np.float32); rng = np.random.default_rng(6)
        cx, cy = CX + pad, CY + pad
        for fr in range(7):
            ang = math.radians(92 + fr * 21 + rng.uniform(-5, 5)); Lf = rng.uniform(560, 760); droop = rng.uniform(0.25, 0.55)
            pts = []
            for i in range(60):
                t_ = i / 59; px = cx + math.cos(ang) * Lf * t_; py = cy + math.sin(ang) * Lf * t_ + droop * Lf * t_ * t_ * 0.6
                pts.append((px, py))
            cv2.polylines(g, [np.int32(pts)], False, 1.0, 5, cv2.LINE_AA)
            for i in range(4, 59, 2):
                t_ = i / 59; (px, py), (qx, qy) = pts[i], pts[i + 1]
                dx, dy = qx - px, qy - py; nn = math.hypot(dx, dy) + 1e-6; dx, dy = dx / nn, dy / nn
                ll = (110 * (1 - t_) ** 0.6 + 25) * rng.uniform(0.85, 1.1)
                for sg in (1, -1):
                    ca, sa_ = math.cos(math.radians(62)), math.sin(math.radians(62)) * sg
                    lx, ly = dx * ca - dy * sa_, dx * sa_ + dy * ca
                    mid = (px + lx * ll * 0.5, py + ly * ll * 0.5 + 6); end = (px + lx * ll, py + ly * ll + 22)
                    cv2.polylines(g, [np.int32([(px, py), mid, end])], False, 1.0, 3, cv2.LINE_AA)
        _PALM["g"] = cv2.GaussianBlur(g, (0, 0), 4.5)
    g = _PALM["g"]; rot = 3.0 * math.sin(f * 0.035) + 1.2 * math.sin(f * 0.11 + 1)
    M = cv2.getRotationMatrix2D((CX + pad, CY + pad), rot, 1.0)
    sh = cv2.warpAffine(g, M, (g.shape[1], g.shape[0]))[pad:pad + hh, pad:pad + hw]
    sh = cv2.resize(np.clip(sh, 0, 1), (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
    return np.clip(out * (1 - strength * sh) + sh * strength * 0.3 * out * CYAN, 0, 1)

def echo(out, s, f):
    """VHS colour echo: two delayed copies trail behind in pink and cyan."""
    e1 = render_shot(s, max(s["f0"], f - 3)); e2 = render_shot(s, max(s["f0"], f - 7))
    return np.clip(out * 0.78 + e1 * (PINK * 0.6 + 0.4) * 0.16 + e2 * (CYAN * 0.6 + 0.4) * 0.10, 0, 1)

def last_visible(P):
    """last frame of shot P as it was seen (includes the pixel dissolve for the vanish shot)."""
    if P.get("vanish"):
        f = P["f1"] - 1; img, person = render_shot(P, f, want_mask=True)
        tv0 = E.VANISH_T0
        return vanish(img, person, f, f / FPS, tv0, P["t1"] - 0.08)
    if P.get("pause"): return render_shot(P, pause_frame(P, P["f1"] - 1))
    return last_frame_of(P)

# ============================================================================ v6 rev 3 — polish: transitions + graphics
# ---- film strip whip: the frame shrinks into a strip of film on a light table, whips to the next frame, zooms back in
_LBOX = {}
def lightbox():
    if "img" not in _LBOX:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2)
        base = np.clip(1.0 - d * 0.9, 0, 1)[..., None]
        _LBOX["img"] = np.clip(base * (WHITE * 0.75 + PINK * 0.25) + (1 - base) * VIOLET * 0.6, 0, 1).astype(np.float32)
    return _LBOX["img"]

def filmstrip(A, B, j, f, sa, sb, n=9):
    u = clamp((j + n + 0.5) / (2 * n), 0, 1)
    z = 1 - 0.42 * (smooth(clamp(u / 0.3, 0, 1)) - smooth(clamp((u - 0.7) / 0.3, 0, 1)))
    gap = 70.0; P = H + gap                                           # pitch in unzoomed px
    sc_u = smooth(clamp((u - 0.25) / 0.5, 0, 1)); scroll = P * sc_u
    vel = P * z * 3.0 / (2 * n) * clamp(1 - abs(u - 0.5) / 0.25, 0, 1) # strip speed in px per frame (peak)
    i_prev = SHOTS.index(sa) - 1; i_next = SHOTS.index(sb) + 1
    neigh = {-1: (last_frame_of(SHOTS[i_prev]) if i_prev >= 0 else A * 0.5), 0: A, 1: B,
             2: (render_shot(SHOTS[i_next], SHOTS[i_next]["f0"], False) if i_next < len(SHOTS) else B * 0.5)}
    o = lightbox().copy(); fw, fh = int(W * z), int(H * z); bw = int(95 * z)
    x0 = W // 2 - fw // 2; xs0, xs1 = max(0, x0 - bw), min(W, x0 + fw + bw)
    o[:, xs0:xs1] = np.array([0.05, 0.04, 0.06], np.float32)
    # sprocket holes (scroll with the strip)
    hp = 110 * z; off = (-scroll * z) % hp
    for y in np.arange(-hp + off, H + hp, hp):
        for xh in (x0 - bw + int(22 * z), x0 + fw + int(22 * z)):
            cv2.rectangle(o, (int(xh), int(y)), (int(xh + 50 * z), int(y + 62 * z)), tuple(float(c) for c in (WHITE * 0.85 + PINK * 0.15)), -1, cv2.LINE_AA)
    for i, img in neigh.items():
        cy = H / 2 + z * (i * P - scroll); y0 = int(cy - fh / 2)
        if y0 > H or y0 + fh < 0: continue
        fr = cv2.resize(img, (fw, fh), interpolation=cv2.INTER_AREA)
        ya, yb = max(0, y0), min(H, y0 + fh)
        o[ya:yb, x0:x0 + fw] = fr[ya - y0:yb - y0]
        ty = int(cy + fh / 2 + gap * z * 0.6)
        if 0 < ty < H:                                                # orange edge-code dashes between frames
            for q in range(4): cv2.rectangle(o, (int(x0 + 14 * z + q * 34 * z), ty - int(8 * z)), (int(x0 + 36 * z + q * 34 * z), ty), (0.25, 0.55, 1.0), -1)
    L = int(min(110, vel * 0.55))
    if L > 2: o = cv2.blur(o, (1, L))
    return np.clip(o, 0, 1)

# ---- sticker peel: the frame peels off from the bottom-right corner like a glossy pastel sticker
def peel(A, B, j, f, sa, sb, n=8):
    u = clamp((j + n + 0.5) / (2 * n), 0, 1)
    dv = np.array([-0.62, -0.785]); C = np.array([W + 40.0, H + 40.0])
    t = (_GX - C[0]) * dv[0] + (_GY - C[1]) * dv[1]
    diag = (W + 80) * 0.62 + (H + 80) * 0.785
    s = diag * 1.08 * ein(u, 1.35)
    qx = (_GX - 2 * (t - s) * dv[0]).astype(np.float32); qy = (_GY - 2 * (t - s) * dv[1]).astype(np.float32)
    flap_ok = ((t > s) & (t < 2 * s) & (qx >= 0) & (qx < W - 1) & (qy >= 0) & (qy < H - 1)).astype(np.float32)
    flap_ok = cv2.GaussianBlur(flap_ok, (0, 0), 1.0)[..., None]
    back = cv2.remap(A, qx, qy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    g = np.clip((t - s) / (s + 1e-3), 0, 1)[..., None]
    backside = np.clip(back * 0.22 + (PINK * (1 - g) + CYAN * g) * 0.55 + 0.18, 0, 1)
    spec = np.exp(-((t - s - 18) / 26) ** 2)[..., None] * 0.6         # glossy roll highlight at the fold
    revealed = np.clip((s - t) / 2.0, 0, 1)[..., None]
    shade_b = 1 - 0.45 * np.exp(-np.clip(s - t, 0, None) / 60)[..., None] * revealed
    shade_a = 1 - 0.35 * np.exp(-np.clip(t - 2 * s, 0, None) / 40)[..., None] * (t > 2 * s)[..., None] * (s > 5)
    o = B * shade_b * revealed + A * shade_a * (1 - revealed)
    o = o * (1 - flap_ok) + (backside + spec) * flap_ok
    return np.clip(o, 0, 1)

# ---- finger-gun bang -> CRT power-off; the next shot powers on
def muzzle_flash(o, k, x, y):
    if not (0 <= k < 5): return o
    a = [1.0, 0.75, 0.45, 0.2, 0.08][k]; lay = np.zeros((H, W), np.float32)
    for i in range(10):
        ang = i * math.pi / 5 + 0.3; L = (140 + 90 * (i % 2)) * (1 + 0.6 * k / 4)
        cv2.line(lay, (int(x), int(y)), (int(x + L * math.cos(ang)), int(y + L * math.sin(ang))), 1.0, 6 - (i % 2) * 3, cv2.LINE_AA)
    cv2.circle(lay, (int(x), int(y)), int(46 + 20 * k), 1.0, -1, cv2.LINE_AA)
    glow = cv2.GaussianBlur(lay, (0, 0), 22)
    o = o + (lay[..., None] * WHITE + glow[..., None] * (PINK * 0.7 + PEACH * 0.3) * 2.2) * a
    return np.clip(o + 0.25 * a, 0, 1)

def tv_off(A, B, j, f, sa, sb):
    if j < 0:
        mx, my = sa.get("muzzle", (W / 2, H * 0.45)); kb = j + 14
        if kb < 4:                                                    # bang: flash + kick
            o = zoom_about(A, mx, my, 1.0 + 0.05 * (1 - kb / 4)); o = rgb_split(o, 16 * (1 - kb / 4))
            return muzzle_flash(o, kb, mx, my)
        u = (kb - 4) / 10.0                                           # CRT power-off
        sy = max(0.004, 1 - ein(clamp(u / 0.6, 0, 1), 2.4)); sx = 1 - 0.995 * ein(clamp((u - 0.6) / 0.4, 0, 1), 2)
        img = np.clip(A * (1 + 2.5 * u) + 0.3 * u, 0, 1)
        M = np.float32([[sx, 0, W / 2 * (1 - sx)], [0, sy, H / 2 * (1 - sy)]])
        o = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_AREA, borderValue=(0, 0, 0))
        dot = np.exp(-(((_GX - W / 2) / (W * sx * 0.5 + 6)) ** 2 + ((_GY - H / 2) / (H * sy * 0.5 + 3)) ** 2))[..., None]
        return np.clip(o + dot * (WHITE * 0.6 + CYAN * 0.3) * u, 0, 1)
    u = (j + 1) / 12.0                                                # power on: dot -> line -> frame
    sx = 0.01 + 0.99 * eout(clamp(u / 0.35, 0, 1), 2)
    sy = 0.004 + 1.0 * eout(clamp((u - 0.3) / 0.55, 0, 1), 2.5); sy = sy + 0.04 * math.sin(math.pi * clamp((u - 0.75) / 0.25, 0, 1))
    img = np.clip(B * (1 + 1.5 * (1 - u)) + 0.15 * (1 - u), 0, 1)
    M = np.float32([[sx, 0, W / 2 * (1 - sx)], [0, sy, H / 2 * (1 - sy)]])
    o = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
    scan = (1 - 0.35 * (1 - u) * ((np.arange(H) % 4) < 2)[:, None, None])
    return np.clip(o * scan, 0, 1)

TR2.update({"filmstrip": (filmstrip, 9, 9), "peel": (peel, 8, 8), "tv_off": (tv_off, 14, 12)})

# ---- graphics
_MOTE = {}
def motes(out, f, amt=1.0):
    """pastel bokeh light specks drifting up through the sunny shots."""
    if "p" not in _MOTE:
        rng = np.random.default_rng(14)
        _MOTE["p"] = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(4, 13), rng.uniform(0.3, 1.0), rng.uniform(0, 6.28), int(rng.integers(0, 3))) for _ in range(46)]
    lays = [np.zeros((H // 4, W // 4), np.float32) for _ in range(3)]
    for x, y, r, b, ph, c in _MOTE["p"]:
        yy = (y - f * (0.8 + r * 0.12)) % (H + 80) - 40; xx = x + 26 * math.sin(f * 0.03 + ph)
        tw = 0.65 + 0.35 * math.sin(f * 0.21 + ph * 3)
        cv2.circle(lays[c], (int(xx / 4), int(yy / 4)), max(1, int(r / 4)), b * tw, -1, cv2.LINE_AA)
    o = out
    for lay, col in zip(lays, (PINK, PEACH, CYAN)):
        g = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 1.6), (W, H), interpolation=cv2.INTER_LINEAR)
        o = o + g[..., None] * col * 0.55 * amt
    return np.clip(o, 0, 1)

def pause_frame(s, f):
    """VHS pause: returns the frame index to render for shot s (holds PAUSE_N frames at s['pause'])."""
    p0 = s.get("pause")
    if p0 is None: return f
    if p0 <= f < p0 + PAUSE_N: return p0
    return f - PAUSE_N if f >= p0 + PAUSE_N else f
PAUSE_N = 14

def pause_fx(out, s, f):
    p0 = s.get("pause")
    if p0 is None or not (p0 <= f < p0 + PAUSE_N): return out
    k = f - p0; o = np.roll(out, 2 if k % 2 else -1, axis=0)
    rng = np.random.default_rng(900 + k); yb = int((H * 0.78 + k * 37) % H); hb = 46
    band = static_noise(f, 0.9)[yb:yb + hb] if yb + hb <= H else None
    if band is not None: o[yb:yb + hb] = o[yb:yb + hb] * 0.3 + band * 0.7
    o = o * 0.92 + 0.03
    return osd(o, f, "|| PAUSE", y=235, a=1.0 if (k // 6) % 2 == 0 else 0.55, size=52)

def neon_spill(out, f):
    """the neon words throw coloured light onto his face and shirt."""
    t = f / FPS; t_end = E.DUR - 40 / FPS
    if not getattr(E, "END_CAP", None) or not (E.END_CAP[0][1] <= t < t_end): return out
    lay_c = np.zeros((H // 8, W // 8), np.float32); lay_p = np.zeros_like(lay_c)
    for word, tw in E.END_CAP:
        k = (t - tw) * FPS
        if k < 0: continue
        a = eout(k / 14, 3) * clamp((t_end - t) * FPS / 8, 0, 1)
        if word == "ME.": cv2.rectangle(lay_p, (W // 8 // 2 - 22, 1420 // 8), (W // 8 // 2 + 22, 1610 // 8), a, -1)
        else:
            xc = W // 8 // 2 + (-14 if word == "IT" else 12); cv2.rectangle(lay_c, (xc - 12, 1270 // 8), (xc + 12, 1400 // 8), a, -1)
    gc = cv2.resize(cv2.GaussianBlur(lay_c, (0, 0), 22), (W, H)); gp = cv2.resize(cv2.GaussianBlur(lay_p, (0, 0), 22), (W, H))
    return np.clip(out + (gc[..., None] * CYAN + gp[..., None] * PINK) * 0.55 * out.mean(2, keepdims=True) * 2.2 + (gc[..., None] * CYAN + gp[..., None] * PINK) * 0.06, 0, 1)

# ============================================================================ v7 — HIM ALL ALONG: forensic-noir toolkit
UV = np.array([1.00, 0.80, 0.42], np.float32)        # luminol blue-white (BGR)
UVV = np.array([0.95, 0.28, 0.55], np.float32)       # UV-lamp violet
BLOOD = np.array([0.04, 0.03, 0.55], np.float32)
BLOOD_HI = np.array([0.10, 0.08, 0.95], np.float32)
TAPE_Y = np.array([0.05, 0.80, 0.98], np.float32)
F_DISP = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"

def barrel(img, k_, cx=W / 2, cy=H / 2, rn=W * 0.7):
    dx, dy = (_GX - cx) / rn, (_GY - cy) / rn; s_ = 1 + k_ * (dx * dx + dy * dy)
    return cv2.remap(img, (cx + dx * s_ * rn).astype(np.float32), (cy + dy * s_ * rn).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def lum(img): return img[..., 0] * 0.114 + img[..., 1] * 0.587 + img[..., 2] * 0.299

# ---- 1. open through the magnifying glass (loop start, from black)
def lens_frame(img, R=640.0, cy=H * 0.40, a=1.0):
    """look through a magnifying glass: sharp inside the lens, dark and blurred outside, with the glass rim."""
    rr = np.sqrt((_GX - W / 2) ** 2 + (_GY - cy) ** 2)
    m = np.clip((R - rr) / 5, 0, 1)[..., None]
    outside = cv2.GaussianBlur(cv2.resize(img, (W // 4, H // 4)), (0, 0), 6); outside = cv2.resize(outside, (W, H)) * 0.22
    inside = barrel(img, 0.18, W / 2, cy, R) * (1 - 0.35 * np.clip(rr / R, 0, 1) ** 4)[..., None]
    rim = np.exp(-((rr - R) / 14) ** 2)[..., None]; glint = np.exp(-((rr - R + 10) / 6) ** 2)[..., None] * np.clip(np.cos(np.arctan2(_GY - cy, _GX - W / 2) + 2.3), 0, 1)[..., None]
    o = inside * m + outside * (1 - m) + rim * (PINK * 0.45 + WHITE * 0.25) + glint * WHITE * 0.6
    return img * (1 - a) + np.clip(o, 0, 1) * a

def lens_open(A, B, j, f, sa, sb, n=16):
    u = (j + 1) / n
    if sb.get("lensframe"):
        R = 640 * eout(u, 2.6); return lens_frame(zoom_about(B, W / 2, H * 0.40, 1.25 - 0.25 * eout(u, 2)), max(R, 1.0)) * clamp(u * 4, 0, 1)
    rr, _ = polar(); R = 1250 * eout(u, 2.6)
    m = np.clip((R - rr) / 6, 0, 1)[..., None]
    Bz = barrel(zoom_about(B, W / 2, H / 2, 1.35 - 0.35 * eout(u, 2)), 0.35 * (1 - u))
    rim = np.exp(-((rr - R) / (9 + 0.04 * R)) ** 2)[..., None]
    return np.clip(Bz * m + rim * (WHITE * 0.55 + PINK * 0.35) * (1 - u ** 2), 0, 1)

# ---- 2. microscope: into his eye -> red blood cells -> out of the blood drop on the slide
_CELLS = {}
def micro_view(f, zoom, cy=H * 0.45):
    if "c" not in _CELLS:
        rng = np.random.default_rng(21)
        _CELLS["c"] = [(rng.uniform(-200, W + 200), rng.uniform(-200, H + 200), rng.uniform(30, 52), rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(0.85, 1.0)) for _ in range(150)]
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); _CELLS["rr"] = np.sqrt((xx - W / 2) ** 2 + (yy - cy) ** 2)
    o = np.empty((H, W, 3), np.float32); o[:] = np.array([0.74, 0.80, 0.93], np.float32)
    for x, y, r, vx, vy, sq in _CELLS["c"]:
        X = W / 2 + (x + vx * f * 0.8 - W / 2) * zoom; Y = cy + (y + vy * f * 0.8 - cy) * zoom; R = max(2, int(r * zoom))
        if -R < X < W + R and -R < Y < H + R:
            cv2.ellipse(o, (int(X), int(Y)), (R, int(R * sq)), 0, 0, 360, (0.20, 0.20, 0.72), -1, cv2.LINE_AA)
            cv2.ellipse(o, (int(X), int(Y)), (int(R * 0.55), int(R * 0.55 * sq)), 0, 0, 360, (0.40, 0.40, 0.84), -1, cv2.LINE_AA)
    o = cv2.GaussianBlur(o, (0, 0), 1.2)
    rr = _CELLS["rr"]; Rf = W * 0.47
    m = np.clip((Rf - rr) / 4, 0, 1)[..., None]; vg = (1 - 0.55 * np.clip(rr / Rf, 0, 1) ** 3)[..., None]
    o = o * vg * m
    cv2.line(o, (int(W / 2 - Rf), int(cy)), (int(W / 2 + Rf), int(cy)), (0.15, 0.15, 0.2), 2, cv2.LINE_AA)
    cv2.line(o, (int(W / 2), int(cy - Rf)), (int(W / 2), int(cy + Rf)), (0.15, 0.15, 0.2), 2, cv2.LINE_AA)
    for k in range(-8, 9):
        x = int(W / 2 + k * Rf / 9); L = 18 if k % 4 == 0 else 9
        cv2.line(o, (x, int(cy - L)), (x, int(cy + L)), (0.15, 0.15, 0.2), 2, cv2.LINE_AA)
    return np.clip(o, 0, 1), m

def microscope(A, B, j, f, sa, sb):
    if j < 0:
        u = (j + 12) / 12.0; fs = face_scr(sa, f)
        if fs is None: ex, ey = W / 2, H * 0.42
        else: ex, ey = min((fs[3], fs[4]), key=lambda q: abs(q[0] - W / 2))
        sc = math.exp(math.log(10) * ein(u, 2.4)); v = eout(clamp(u / 0.7, 0, 1), 2)
        M = cv2.getRotationMatrix2D((ex, ey), 0, sc); M[0, 2] += (W / 2 - ex) * v; M[1, 2] += (H * 0.45 - ey) * v
        o = cv2.warpAffine(A, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        if sc > 1.4: o = radial_blur(o, W / 2, H * 0.45, 1.0, 1.0 + 0.06 * min(1, sc / 6), 5)
        mv, mk = micro_view(f, 2.6 - 1.4 * u); w = smooth((u - 0.55) / 0.45)
        return np.clip(o * (1 - w) + mv * w, 0, 1)
    v = (j + 1) / 12.0
    px, py = sb.get("focus", (640, 380)); fx, fy, _ = to_screen(sb, f, px, py)
    Z = math.exp(math.log(9) * (1 - eout(v, 2.2)))
    M = cv2.getRotationMatrix2D((fx, fy), 0, Z); M[0, 2] += (W / 2 - fx) * (1 - eout(v, 2)); M[1, 2] += (H * 0.45 - fy) * (1 - eout(v, 2))
    Bz = cv2.warpAffine(B, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    mv, mk = micro_view(f, 1.2 + 2.0 * v); w = smooth(v / 0.5)
    rr = _CELLS["rr"]; Rc = W * 0.47 + 1300 * eout(clamp((v - 0.15) / 0.7, 0, 1), 2)
    circ = np.clip((Rc - rr) / 5, 0, 1)[..., None]
    inside = mv * (1 - w) + Bz * w
    return np.clip(inside * circ, 0, 1)

# ---- 3. steel doors close on "CLOSE", open into the next shot
_DOOR = {}
def door_panel():
    if "p" not in _DOOR:
        rng = np.random.default_rng(3); w2 = W // 2
        streak = cv2.resize(rng.random((H // 8, 1)).astype(np.float32), (w2, H), interpolation=cv2.INTER_LINEAR)
        streak = cv2.GaussianBlur(cv2.resize(rng.random((H, w2 // 6)).astype(np.float32), (w2, H)), (0, 0), 1.5) * 0.5 + streak * 0.5
        p = np.empty((H, w2, 3), np.float32); p[:] = np.array([0.15, 0.145, 0.14], np.float32)
        p = p * (0.75 + 0.5 * streak[..., None])
        p[:, -6:] = UV * 0.85; p[:, -14:-6] = p[:, -14:-6] * 0.5 + UV * 0.25           # lit inner edge
        for y in (180, H // 2, H - 180):
            cv2.circle(p, (40, y), 9, (0.30, 0.30, 0.30), -1, cv2.LINE_AA)
        cv2.rectangle(p, (w2 - 70, H // 2 - 120), (w2 - 46, H // 2 + 120), (0.32, 0.32, 0.33), -1)
        _DOOR["p"] = p
    return _DOOR["p"]

def doors(A, B, j, f, sa, sb):
    pnl = door_panel(); w2 = W // 2
    if j < 0:
        u = clamp((j + 38) / 16.0, 0, 1); th_ = math.radians(100 * (1 - ein(u, 2.2)))
        ks = j + 22
        if ks >= 0: th_ = math.radians(-3.0 * math.exp(-ks / 2.5) * math.sin(ks * 1.6))     # slam bounce
        base = A
    else:
        v = (j + 1) / 14.0; th_ = math.radians(108 * eout(v, 2.4)); base = zoom_about(B, W / 2, H / 2, 1.10 - 0.10 * eout(v, 2))
    o = base.copy(); c, s_ = math.cos(th_), math.sin(abs(th_)); sc = 1 + 0.35 * s_
    shade = 0.95 - 0.45 * s_
    for side in (0, 1):
        xf = w2 * c
        if side == 0: q = np.float32([[0, 0], [xf, H / 2 - H / 2 * sc], [xf, H / 2 + H / 2 * sc], [0, H]]); src = pnl
        else: q = np.float32([[W - xf, H / 2 - H / 2 * sc], [W, 0], [W, H], [W - xf, H / 2 + H / 2 * sc]]); src = pnl[:, ::-1].copy()
        if abs(xf) < 2: continue
        Mp = cv2.getPerspectiveTransform(np.float32([[0, 0], [w2, 0], [w2, H], [0, H]]) if side == 0 else np.float32([[0, 0], [w2, 0], [w2, H], [0, H]]), q)
        wi = cv2.warpPerspective(src * shade, Mp, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
        wm = cv2.warpPerspective(np.ones((H, w2), np.float32), Mp, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)[..., None]
        sh = cv2.GaussianBlur(wm[..., 0], (0, 0), 25)[..., None] * 0.5 * s_
        o = o * (1 - sh) * (1 - wm) + wi * wm
    return np.clip(o, 0, 1)

# ---- 4. redaction bars slam across, then wipe away onto the next shot
_RED = {}
def redact(A, B, j, f, sa, sb):
    if "bars" not in _RED:
        rng = np.random.default_rng(12); ys = [0]
        while ys[-1] < H: ys.append(ys[-1] + int(rng.uniform(190, 330)))
        _RED["bars"] = [(ys[i], min(H, ys[i + 1] + 4), i % 2, rng.uniform(0, 1)) for i in range(len(ys) - 1)]
        _RED["edge"] = cv2.GaussianBlur(rng.random((H, 40)).astype(np.float32), (0, 0), 3)
    o = (A if j < 0 else B).copy()
    for i, (y0, y1, side, r) in enumerate(_RED["bars"]):
        if j < 0: p = eout(clamp((j + 5 - i * 0.5) / 3.0, 0, 1), 3)
        else: p = 1 - ein(clamp((j - i * 0.8) / 5.0, 0, 1), 2)
        if p <= 0: continue
        L = int(W * p * 1.05)
        if side == 0: x0, x1 = 0, L
        else: x0, x1 = W - L, W
        if x1 <= x0: continue
        o[y0:y1, x0:x1] = np.array([0.025, 0.025, 0.03], np.float32) + 0.015 * (np.arange(y1 - y0) % 7 == 0)[:, None, None]
    return np.clip(o, 0, 1)

# ---- 5. UV luminol sweep: a blacklight beam sweeps across, blood fluoresces, the next shot is behind it
_SPAT = {}
def spatter_mask():
    if "m" not in _SPAT:
        rng = np.random.default_rng(31); m = np.zeros((H, W), np.float32)
        for _ in range(26):
            cx, cy = rng.uniform(80, W - 80), rng.uniform(150, H - 150); r = rng.uniform(10, 34)
            cv2.circle(m, (int(cx), int(cy)), int(r), 1.0, -1, cv2.LINE_AA)
            ang = rng.uniform(0, 6.28)
            for k in range(int(rng.integers(6, 16))):
                d = r + rng.uniform(5, 120); a2 = ang + rng.normal(0, 0.5)
                cv2.circle(m, (int(cx + d * math.cos(a2)), int(cy + d * math.sin(a2))), int(max(2, rng.uniform(2, 9) * (1 - d / 160))), 1.0, -1, cv2.LINE_AA)
            cv2.line(m, (int(cx), int(cy)), (int(cx + (r + 60) * math.cos(ang)), int(cy + (r + 60) * math.sin(ang))), 1.0, max(2, int(r / 3)), cv2.LINE_AA)
        _SPAT["m"] = cv2.GaussianBlur(m, (0, 0), 1.2)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); _SPAT["ang"] = np.degrees(np.arctan2(yy - (H + 200), xx + 250))
    return _SPAT["m"], _SPAT["ang"]

def uv_look(img):
    L = lum(img); g = np.clip((L - 0.42) * 2.4, 0, 1)
    return img * 0.10 + UVV * 0.08 + g[..., None] * UV * 0.55

def uv_sweep(A, B, j, f, sa, sb):
    sm, ang = spatter_mask(); u = clamp((j + 8.5) / 18, 0, 1)
    phi = -98 + 92 * smooth(u); d = ang - phi
    swept = np.clip(-d / 2.0, 0, 1)[..., None]; beam = np.exp(-(d / 6.0) ** 2)[..., None]
    wake = (np.exp(-np.clip(-d, 0, None) / 14.0) * (d < 0))[..., None]
    under = A if j < 0 else B
    Bs = B * (1 - wake * 0.85) + uv_look(B) * wake * 0.85
    o = under * (1 - swept) + Bs * swept
    o = o * (1 - beam * 0.6) + uv_look(o) * beam * 0.6 + beam * UVV * 0.55
    glow = (sm * np.clip(np.exp(-np.clip(-d, 0, None) / 22.0) * (d < 3), 0, 1))[..., None]
    o = o + glow * UV * 1.1 + cv2.GaussianBlur(glow[..., 0], (0, 0), 8)[..., None] * UV * 0.6
    return np.clip(o, 0, 1)

# ---- 6. fingerprint: ridges ripple out from the centre and the next shot appears between them
_FP = {}
def fingerprint(A, B, j, f, sa, sb):
    if "r" not in _FP:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); dx, dy = xx - W / 2, (yy - H * 0.42) / 1.25
        r = np.sqrt(dx * dx + dy * dy); th_ = np.arctan2(dy, dx)
        rng = np.random.default_rng(4); nz = cv2.resize(rng.random((24, 14)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        rw = r + 22 * np.sin(th_ * 3 + r / 90) + 12 * np.sin(th_ * 5 - r / 140) + nz * 40
        _FP["r"] = rw; _FP["ridge"] = 0.5 + 0.5 * np.cos(rw / 8.5)
    rw, rid = _FP["r"], _FP["ridge"]; u = clamp((j + 5.5) / 15, 0, 1); R = 1450 * ein(u, 1.3)
    m = np.clip((R - rw) / 40, 0, 1)
    m = np.clip(m + (rid > 0.55) * np.clip((R + 60 - rw) / 60, 0, 1) * (rw > R - 40), 0, 1)[..., None]
    band = (np.exp(-((rw - R) / 55) ** 2) * rid)[..., None]
    o = A * (1 - m) + B * m
    return np.clip(o + band * UV * 0.75, 0, 1)

# ---- 7. crime-scene tape snaps as the camera pushes through it
_TAPE = {}
def tape_strip():
    if "s" not in _TAPE:
        hgt, wid = 120, 2800; img = np.zeros((hgt, wid, 4), np.float32); img[..., :3] = TAPE_Y; img[..., 3] = 1
        m = text_mask("CRIME SCENE   DO NOT CROSS   ", F_DISP, 62, tracking=4)
        x = 0
        while x < wid:
            w_ = min(m.shape[1], wid - x); hh = min(m.shape[0], hgt)
            y0 = (hgt - hh) // 2; img[y0:y0 + hh, x:x + w_, :3] *= (1 - m[:hh, :w_, None] * 0.95)
            x += m.shape[1]
        img[6:12, :, :3] = img[6:12, :, :3] * 0.6 + 0.4; img[-12:-6, :, :3] *= 0.75
        _TAPE["s"] = img
    return _TAPE["s"]

def tape_snap(A, B, j, f, sa, sb):
    st_ = tape_strip(); hgt, wid = st_.shape[:2]; ang = -14
    def place(strip, cx, cy, rot, scale=1.0):
        M = cv2.getRotationMatrix2D((strip.shape[1] / 2, strip.shape[0] / 2), rot, scale); M[0, 2] += cx - strip.shape[1] / 2; M[1, 2] += cy - strip.shape[0] / 2
        return cv2.warpAffine(strip, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    if j < 0:
        u = (j + 7) / 7.0; cx = -wid / 2 + (W / 2 + wid / 2) * eout(u, 3)
        o = zoom_about(A, W / 2, H / 2, 1 + 0.08 * u)
        lay = place(st_, cx, H * 0.5, ang, 1 + 0.15 * u)
        sh = cv2.GaussianBlur(np.roll(lay[..., 3], 30, 0), (0, 0), 18)[..., None] * 0.45
        return np.clip(o * (1 - sh) * (1 - lay[..., 3:4]) + lay[..., :3] * lay[..., 3:4], 0, 1)
    v = (j + 1) / 10.0; e = eout(v, 2.2); o = zoom_about(B, W / 2, H / 2, 1.12 - 0.12 * eout(v, 2))
    half = wid // 2
    L_ = place(st_[:, :half], W / 2 - half / 2 * math.cos(math.radians(ang)) - 900 * e, H * 0.5 - 300 * e, ang + 35 * e, 1.15)
    R_ = place(st_[:, half:], W / 2 + half / 2 * math.cos(math.radians(ang)) + 900 * e, H * 0.5 + 320 * e, ang - 40 * e, 1.15)
    for lay in (L_, R_): o = o * (1 - lay[..., 3:4]) + lay[..., :3] * lay[..., 3:4]
    return np.clip(o + 0.3 * (1 - v) ** 3, 0, 1)

# ---- 8. string method: spatter stains shoot red strings to the point of origin — his face
_STR = {}
def strings(A, B, j, f, sa, sb):
    if "st" not in _STR:
        rng = np.random.default_rng(17)
        _STR["st"] = [(rng.uniform(60, W - 60), rng.choice([rng.uniform(250, 520), rng.uniform(1250, 1650)]), rng.uniform(12, 26)) for _ in range(9)]
    fb = face_scr(sb, sb["f0"]); O = (fb[0], fb[1]) if fb else (W / 2, H * 0.37)
    lay = np.zeros((H, W), np.float32); stain = np.zeros((H, W), np.float32)
    if j < 0:
        u = (j + 11) / 11.0; o = zoom_about(A, O[0], O[1], 1 + 0.12 * u); g = eout(clamp((u - 0.25) / 0.75, 0, 1), 1.6)
    else:
        u = 1.0; v = (j + 1) / 10.0; o = zoom_about(B, O[0], O[1], 1.22 - 0.22 * eout(v, 2)); g = 1.0
    for i, (x, y, r) in enumerate(_STR["st"]):
        a = eout(clamp(u / 0.3 - i * 0.06, 0, 1), 3)
        if a <= 0: continue
        cv2.circle(stain, (int(x), int(y)), int(r * a), 1.0, -1, cv2.LINE_AA)
        if g > 0:
            ex, ey = x + (O[0] - x) * g, y + (O[1] - y) * g
            cv2.line(lay, (int(x), int(y)), (int(ex), int(ey)), 1.0, 3, cv2.LINE_AA)
    fade = 1.0 if j < 0 else 1 - smooth((j - 3) / 6)
    o = o * (1 - stain[..., None] * 0.9) + stain[..., None] * BLOOD * 0.9
    o = o + (lay[..., None] * BLOOD_HI + cv2.GaussianBlur(lay, (0, 0), 6)[..., None] * BLOOD_HI * 0.9) * fade
    if j >= 0:                                                              # point of origin: a target ring on his face
        ring = np.zeros((H, W), np.float32); rad = int(90 + 140 * (1 - eout((j + 1) / 10, 2)))
        cv2.circle(ring, (int(O[0]), int(O[1])), rad, 1.0, 3, cv2.LINE_AA)
        o = o + neon_glow(ring, BLOOD_HI, 8, 1.2) * fade
    return np.clip(o, 0, 1)

# ---- 9. kill-room plastic (with the luminol title) and the rip into the drop
_PL = {}
def plastic_tex():
    """hanging kill-room plastic: a few soft vertical folds that sway, a couple of diagonal creases, faint sheen."""
    if "spec" not in _PL:
        rng = np.random.default_rng(9); yy = np.arange(H, dtype=np.float32)[:, None]; xx = np.arange(W, dtype=np.float32)[None, :]
        spec = np.zeros((H, W), np.float32)
        for _ in range(7):
            x0 = rng.uniform(60, W - 60); wd = rng.uniform(25, 70); amp = rng.uniform(0.35, 1.0); ph = rng.uniform(0, 6.28)
            xc = x0 + 28 * np.sin(yy / rng.uniform(280, 520) + ph)
            spec += amp * np.exp(-((xx - xc) / wd) ** 2)
        for _ in range(3):
            a = rng.uniform(-0.5, 0.5); y0 = rng.uniform(200, H - 200)
            spec += 0.35 * np.exp(-(((yy - y0) - a * (xx - W / 2)) / 10) ** 2)
        _PL["spec"] = (spec / spec.max()).astype(np.float32); _PL["fold"] = (0.97 + 0.06 * _PL["spec"]).astype(np.float32)
        rng2 = np.random.default_rng(5); tear = np.cumsum(rng2.normal(0, 6, H)).astype(np.float32); _PL["tear"] = tear - tear.mean()
    return _PL["spec"], _PL["fold"]

_LUM = {}
def luminol_word(word, size=230):
    if word not in _LUM:
        m = text_mask(word, F_DISP, size, tracking=10); m = cv2.resize(m, (int(m.shape[1] * 0.9), m.shape[0]))
        pad = 60; m = np.pad(m, ((10, pad), (10, 10))); rng = np.random.default_rng(len(word) * 7)
        hh, ww = m.shape; nz = cv2.GaussianBlur(rng.random((hh, ww)).astype(np.float32), (0, 0), 3)
        mm = np.clip(m * (0.75 + 0.5 * nz), 0, 1)                                     # smeared, uneven glow
        cols = np.nonzero(m[:hh - pad].sum(0) > 0)[0]
        for x in rng.choice(cols, size=min(len(cols), 9), replace=False):           # drips
            yb = np.nonzero(m[:, x] > 0.5)[0]
            if len(yb) == 0: continue
            y0 = yb.max(); L = int(rng.uniform(15, pad - 5)); cv2.line(mm, (int(x), int(y0)), (int(x), int(y0 + L)), 0.9, int(rng.integers(3, 7)), cv2.LINE_AA)
            cv2.circle(mm, (int(x), int(y0 + L)), 4, 0.9, -1, cv2.LINE_AA)
        _LUM[word] = mm.astype(np.float32)
    return _LUM[word]

LUM_Y = (1335, 1515)
def plastic_layer(out, f, s, title=True):
    """semi-transparent wrinkled kill-room plastic hanging in front of the camera, with HIM / ALL / ALONG in luminol."""
    t = f / FPS; a = smooth((t - (s["t0"] + 0.40)) / 0.45)
    if a <= 0: return out
    spec, fold = plastic_tex()
    yb = int(H * eout(a, 2.2))                                                       # the sheet is pulled down into frame
    milky = cv2.GaussianBlur(out, (0, 0), 5) * 0.74 * fold[..., None] + 0.07 + spec[..., None] * (WHITE * 0.16 + UV * 0.04)
    m = np.zeros((H, 1, 1), np.float32); m[:yb] = 1
    o = out * (1 - m) + milky * m
    if 0 < yb < H: o[max(0, yb - 3):yb + 3] = o[max(0, yb - 3):yb + 3] * 0.4 + 0.6
    if title:
        tx = [tw for tw in E.TEXT if tw["style"] == "luminol"]
        if tx:
            glow_lay = np.zeros((H, W), np.float32); ws_ = tx[0]["words"]; gap = 46
            for ln in sorted({l for _, _, l in ws_}):
                row = [(w_, wt) for w_, wt, l in ws_ if l == ln]; ims = [luminol_word(w_, 205) for w_, _ in row]
                x = int(W / 2 - (sum(m_.shape[1] for m_ in ims) + gap * (len(ims) - 1)) / 2)
                for (word, wt), mm in zip(row, ims):
                    k = (t - wt) * FPS; hh, ww = mm.shape; x0 = x; y0 = int(LUM_Y[ln] - hh / 2); x += ww + gap
                    if k < 0: continue
                    rev = np.clip((np.arange(ww)[None, :] - ww * (eout(k / 7, 2) * 1.3 - 0.15)) / -60, 0, 1)   # UV sweep reveals the word
                    w_ = mm * rev * (0.85 + 0.15 * math.sin(f * 0.9 + ln))
                    ya, xa = max(0, y0), max(0, x0); yb2, xb2 = min(H, y0 + hh), min(W, x0 + ww)
                    glow_lay[ya:yb2, xa:xb2] = np.maximum(glow_lay[ya:yb2, xa:xb2], w_[ya - y0:yb2 - y0, xa - x0:xb2 - x0])
            o = o * (1 - glow_lay[..., None] * 0.8) + glow_lay[..., None] * (UV * 0.75 + WHITE * 0.3)
            o = o + cv2.GaussianBlur(glow_lay, (0, 0), 16)[..., None] * UV * 0.8
    return np.clip(o, 0, 1)

def plastic_rip(A, B, j, f, sa, sb):
    if j < 0:
        u = (j + 5) / 5.0; return np.clip(zoom_about(A, W / 2, H * 0.5, 1 + 0.05 * ein(u, 2)) * (1 + 0.25 * u), 0, 1)
    plastic_tex(); tear = _PL["tear"]; v = (j + 1) / 16.0; e = eout(v, 2.6)
    gap = W * 1.25 * e; xs = W / 2 + tear                                            # jagged vertical tear line
    o = B.copy(); flash = 0.55 * (1 - v) ** 3
    o = np.clip(o * (1 + 0.6 * (1 - v) ** 2) + flash * BLOOD_HI * 0.6, 0, 1)
    for sg in (-1, 1):
        dx = sg * gap / 2; rot = sg * 6 * e
        M = cv2.getRotationMatrix2D((W / 2, 0), rot, 1.0); M[0, 2] += dx
        flap = cv2.warpAffine(A, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        side = ((_GX - xs[:, None]) * sg < 0).astype(np.float32)                   # left flap keeps x < tear
        sm = cv2.warpAffine(side, M, (W, H), borderValue=0)
        edge = cv2.warpAffine(np.exp(-((_GX - xs[:, None]) / 5) ** 2).astype(np.float32), M, (W, H), borderValue=0)
        fade = 1 - smooth((v - 0.7) / 0.3)
        o = o * (1 - sm[..., None] * fade) + flap * sm[..., None] * fade + edge[..., None] * WHITE * 0.7 * fade
    return np.clip(o, 0, 1)

# ---- 10. evidence board: the frame is a pinned photo; the camera follows the red string to the next one
_BRD = {}
def board_bg():
    if "b" not in _BRD:
        rng = np.random.default_rng(7); n = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 1.4)
        n2 = cv2.resize(rng.random((48, 27)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        _BRD["b"] = (np.array([0.10, 0.14, 0.20], np.float32) * (0.65 + 0.5 * n[..., None]) * (0.8 + 0.4 * n2[..., None])).astype(np.float32)
    return _BRD["b"]

def board(A, B, j, f, sa, sb, n=9):
    u = clamp((j + n + 0.5) / (2 * n), 0, 1); s0 = 0.34
    i0 = SHOTS.index(sa); extra = [last_frame_of(SHOTS[max(0, i0 - 2)]), last_frame_of(SHOTS[max(0, i0 - 4)])]
    P_ = [(A, (W * 0.30, H * 0.30), -5.0), (B, (W * 0.70, H * 0.69), 4.0), (extra[0], (W * 0.76, H * 0.24), 7.0), (extra[1], (W * 0.25, H * 0.76), -8.0)]
    if u < 0.5: w = smooth(u / 0.5); c0, r0 = P_[0][1], P_[0][2]; c = (c0[0] + (W / 2 - c0[0]) * w, c0[1] + (H / 2 - c0[1]) * w); rot = r0 * (1 - w); Z = (1 / s0) ** (1 - w)
    else: w = smooth((u - 0.5) / 0.5); c1, r1 = P_[1][1], P_[1][2]; c = (W / 2 + (c1[0] - W / 2) * w, H / 2 + (c1[1] - H / 2) * w); rot = r1 * w; Z = (1 / s0) ** w
    Mc = cv2.getRotationMatrix2D(c, rot, Z); Mc[0, 2] += W / 2 - c[0]; Mc[1, 2] += H / 2 - c[1]
    Mc3 = np.vstack([Mc, [0, 0, 1]])
    o = cv2.warpAffine(board_bg(), Mc, (W, H), borderMode=cv2.BORDER_REFLECT); pins = []
    for img, (px, py), r in P_[::-1]:
        b_ = 16; card = np.ones((H + 2 * b_, W + 2 * b_, 3), np.float32) * 0.92; card[b_:b_ + H, b_:b_ + W] = img
        Mp = cv2.getRotationMatrix2D((W / 2 + b_, H / 2 + b_), r, s0); Mp[0, 2] += px - (W / 2 + b_); Mp[1, 2] += py - (H / 2 + b_)
        M = (Mc3 @ np.vstack([Mp, [0, 0, 1]]))[:2]
        wi = cv2.warpAffine(card, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0)); wm = cv2.warpAffine(np.ones(card.shape[:2], np.float32), M, (W, H), borderValue=0)[..., None]
        sh = cv2.GaussianBlur(np.roll(np.roll(wm[..., 0], 18, 0), 14, 1), (0, 0), 14)[..., None] * 0.6
        o = o * (1 - sh) * (1 - wm) + wi * wm
        pins.append(Mc3 @ np.array([px, py - H * s0 * 0.46, 1]))
    lay = np.zeros((H, W), np.float32)
    for a_, b2 in ((0, 1), (1, 2), (1, 3), (0, 2)):
        pa, pb = pins[::-1][a_], pins[::-1][b2]; cv2.line(lay, (int(pa[0]), int(pa[1])), (int(pb[0]), int(pb[1])), 1.0, max(2, int(3 * Z / 2)), cv2.LINE_AA)
    o = o * (1 - lay[..., None]) + lay[..., None] * BLOOD_HI * 0.9
    for p in pins: cv2.circle(o, (int(p[0]), int(p[1])), max(4, int(9 * Z / 2.5)), (0.10, 0.10, 0.85), -1, cv2.LINE_AA)
    return np.clip(o, 0, 1)

# ---- 11. night-drive light streaks
_LST = {}
def lightstreak(A, B, j, f, sa, sb):
    if "s" not in _LST:
        rng = np.random.default_rng(23); _LST["s"] = [(rng.uniform(0, H), rng.uniform(0, 1), rng.uniform(2, 7), int(rng.integers(0, 3))) for _ in range(46)]
    u = clamp((j + 6.5) / 14, 0, 1); env = math.sin(math.pi * u) ** 1.5
    base = A if j < 0 else B; o = hblur(base, int(10 + 120 * env)) if env > 0.05 else base
    lay = [np.zeros((H, W), np.float32) for _ in range(2)]
    for y, ph, th_, c in _LST["s"]:
        x0 = ((ph + u * 2.2) % 1.4 - 0.2) * W; L = 300 + 1500 * env
        cv2.line(lay[0 if c else 1], (int(x0 - L), int(y)), (int(x0), int(y)), 1.0, int(th_), cv2.LINE_AA)
    st_ = hblur(np.stack(lay, -1), 60)
    o = o + (st_[..., 0:1] * BLOOD_HI * 1.4 + st_[..., 1:2] * (WHITE * 0.9 + PEACH * 0.3)) * env
    return np.clip(o + 0.16 * env ** 4, 0, 1)

# ---- 12. voidfx logo revealed by UV light (blacklight luminol), fly through the 'o'
_NUV = {}
def logo_uv(A, B, j, f, sa, sb):
    L = logo_assets(); h = L["h"]
    if "rgba" not in _NUV:
        al = (L["rgba"][..., 3] > 0.5).astype(np.uint8)
        tube = np.clip(cv2.dilate(al, np.ones((7, 7), np.uint8)) - cv2.erode(al, np.ones((7, 7), np.uint8)), 0, 1).astype(np.float32)
        fill = al.astype(np.float32) * 0.35
        rgba = np.zeros((h, E.LOGO_W, 4), np.float32); rgba[..., :3] = UV * np.maximum(tube, fill)[..., None] * 1.1 + WHITE * tube[..., None] * 0.3
        rgba[..., 3] = np.maximum(tube, fill); _NUV.update(rgba=rgba, glow=cv2.GaussianBlur(np.maximum(tube, fill), (0, 0), 18))
    X0, Y0 = (W - E.LOGO_W) // 2, int(H * 0.74 - h / 2); ccx, ccy = X0 + L["c"][0], Y0 + L["c"][1]
    sc = 1.0 if j < -5 else math.exp(4.3 * ein((j + 5) / 15, 2.2))
    rev = clamp((j + 13) / 7.0, 0, 1)                                                  # UV sweep reveals the logo left -> right
    M = cv2.getRotationMatrix2D((ccx, ccy), 0, sc)
    can = np.zeros((H, W, 4), np.float32); can[Y0:Y0 + h, X0:X0 + E.LOGO_W] = _NUV["rgba"]
    xr = (np.arange(W)[None, :] < X0 + E.LOGO_W * rev * 1.1).astype(np.float32)
    can[..., 3] *= xr; gl = np.zeros((H, W), np.float32); gl[Y0:Y0 + h, X0:X0 + E.LOGO_W] = _NUV["glow"]; gl *= xr[0]
    lw = cv2.warpAffine(can, M, (W, H), borderValue=(0, 0, 0, 0)); gw = cv2.warpAffine(gl, M, (W, H), borderValue=0)
    cnt = np.zeros((H, W), np.float32); cnt[Y0:Y0 + h, X0:X0 + E.LOGO_W] = L["counter"]
    cw = cv2.warpAffine(cnt, M, (W, H), borderValue=0)
    if sc > 8: cw = np.maximum(cw, clamp((sc - 8) / 6, 0, 1))
    cw = cw * (1.0 if j >= -5 else 0.0)
    dim = 1 - 0.55 * clamp((j + 12) / 6, 0, 1)
    Bz = zoom_about(B, ccx, ccy, 1.6 - 0.6 * clamp((sc - 1) / 30, 0, 1))
    base = (uv_look(A) * 0.6 + A * 0.4) * dim
    o = base * (1 - cw[..., None]) + Bz * cw[..., None]
    fade = clamp(1 - (sc - 6) / 6, 0, 1)
    o = o + gw[..., None] * UV * 0.7 * fade; al = lw[..., 3:4] * fade; o = o * (1 - al) + lw[..., :3] * al
    if j < -5:                                                                         # the UV lamp beam crossing the logo
        bx = X0 + E.LOGO_W * rev * 1.1; o = o + np.exp(-((_GX - bx) / 40) ** 2)[..., None] * UVV * 0.5
    if sc > 1.5: o = radial_blur(o, ccx, ccy, 1.0, 1.0 + 0.06 * min(1, sc / 10), 4)
    return np.clip(o, 0, 1)

# ---- 13. luminol negative strobe on the beat
def strobe(A, B, j, f, sa, sb):
    def neg(img): return np.clip((1 - lum(img))[..., None] ** 1.4 * UV, 0, 1)
    seq = {-6: "A", -5: "N", -4: "A", -3: "K", -2: "NA", -1: "W", 0: "W", 1: "NB", 2: "B", 3: "K", 4: "NB", 5: "B"}[j]
    if seq == "A": return A
    if seq in ("N", "NA"): return neg(A)
    if seq == "K": return np.zeros_like(A) + 0.01
    if seq == "W": return np.clip(A * 0.15 + 0.85, 0, 1) if j < 0 else np.clip(B * 0.25 + 0.75, 0, 1)
    if seq == "NB": return neg(B)
    return B

# ---- 14. the blood-slide box: the frame is the drop on a glass slide; the camera glides to the next slide
_SLB = {}
def slidebox(A, B, j, f, sa, sb, pre=10, post=14):
    if "wood" not in _SLB:
        rng = np.random.default_rng(13); g = cv2.resize(rng.random((H // 6, 6)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        grain_ = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 1.0)
        _SLB["wood"] = (np.array([0.05, 0.08, 0.20], np.float32) * (0.7 + 0.45 * g[..., None] + 0.12 * grain_[..., None])).astype(np.float32)
    u = clamp((j + pre + 0.5) / (pre + post), 0, 1); cut = pre / (pre + post)
    pitch = 330; sw_, sh_ = 900, 290; ia, ib = 0, 1; rd = 112                          # slide A at y=0, slide B one pitch below
    if u < cut: w = smooth(u / cut); Z = 11 ** (1 - w) * 1.0; cy = 0 + pitch * 0.5 * w
    else: w = smooth((u - cut) / (1 - cut)); Z = 11 ** w; cy = pitch * 0.5 + pitch * 0.5 * w
    Z = max(Z, 1.0)
    def to_s(x, y): return W / 2 + x * Z, H / 2 + (y - cy) * Z
    o = cv2.warpAffine(_SLB["wood"], np.float32([[Z * 0.25 + 0.75, 0, 0], [0, Z * 0.25 + 0.75, -cy * 0.4]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    for k in range(-3, 5):
        y = k * pitch; x0, y0 = to_s(-sw_ / 2, y - sh_ / 2); x1, y1 = to_s(sw_ / 2, y + sh_ / 2)
        if y1 < -50 or y0 > H + 50: continue
        sub = np.zeros((H, W), np.float32); cv2.rectangle(sub, (int(x0), int(y0)), (int(x1), int(y1)), 1.0, -1)
        o = o * (1 - sub[..., None] * 0.35) + sub[..., None] * np.array([0.75, 0.80, 0.78], np.float32) * 0.35
        cv2.rectangle(o, (int(x0), int(y0)), (int(x1), int(y1)), (0.85, 0.88, 0.86), max(1, int(2 * Z / 4)), cv2.LINE_AA)
        dx, dy = to_s(0, y); R = rd * Z
        if k in (ia, ib):
            src = A if k == ia else B; c_ = 1 - clamp((R - 500) / 700, 0, 1); s_ = (R / (rd * 11.0)) * (1 - c_) + (R / 520.0) * c_
            Mz = np.float32([[s_, 0, dx - s_ * W / 2], [0, s_, dy - s_ * H / 2]])
            con = cv2.warpAffine(src, Mz, (W, H), borderMode=cv2.BORDER_REFLECT)
            cm = np.zeros((H, W), np.float32); cv2.circle(cm, (int(dx), int(dy)), int(min(R, 4000)), 1.0, -1, cv2.LINE_AA)
            tint = clamp((rd * 11 - R) / (rd * 8), 0, 1)
            con = con * (1 - tint * 0.5) + BLOOD * tint * 0.5
            o = o * (1 - cm[..., None]) + con * cm[..., None]
        else:
            cv2.circle(o, (int(dx), int(dy)), int(R), (0.03, 0.02, 0.42), -1, cv2.LINE_AA)
            cv2.circle(o, (int(dx - R * 0.3), int(dy - R * 0.35)), max(2, int(R * 0.18)), (0.6, 0.6, 0.9), -1, cv2.LINE_AA)
    return np.clip(o, 0, 1)

TR2.update({"lens_open": (lens_open, 0, 16), "microscope": (microscope, 12, 12), "doors": (doors, 38, 14), "redact": (redact, 5, 9),
            "uv_sweep": (uv_sweep, 8, 10), "fingerprint": (fingerprint, 5, 10), "tape_snap": (tape_snap, 7, 10), "strings": (strings, 11, 10),
            "plastic_rip": (plastic_rip, 5, 16), "board": (board, 9, 9), "lightstreak": (lightstreak, 6, 8), "logo_uv": (logo_uv, 12, 10),
            "strobe": (strobe, 6, 6), "slidebox": (slidebox, 10, 14)})

# ---- 15. forensic scanner: a glowing scan line sweeps down, the next shot is scanned in above it
def scan(A, B, j, f, sa, sb, pre=6, post=9):
    u = clamp((j + pre + 0.5) / (pre + post), 0, 1); y = -40 + (H + 80) * smooth(u)
    rows = np.arange(H, dtype=np.float32)[:, None, None]
    above = (rows < y).astype(np.float32); near = np.exp(-((rows - y) / 70) ** 2)
    tint = np.exp(-np.clip(y - rows, 0, None) / 260)
    Bs = B * (1 - tint * 0.6) + uv_look(B) * tint * 0.6
    o = A * (1 - above) + Bs * above
    o = np.roll(o, 0, 1); disp = (near[..., 0] * 22).astype(np.int32)
    if y > 0 and y < H:
        y0, y1 = int(max(0, y - 60)), int(min(H, y + 60))
        for r_ in range(y0, y1, 3): o[r_:r_ + 3] = np.roll(o[r_:r_ + 3], int(disp[r_, 0]), 1)
    line = np.exp(-((rows - y) / 4) ** 2)
    return np.clip(o + line * (UV * 0.9 + WHITE * 0.4) + near * UV * 0.18, 0, 1)
TR2["scan"] = (scan, 6, 9)

def pupil_end(out, f, s, n=20):
    j = f - s["f1"]
    if j < -n: return out
    jj = int(round(-15 + (j + n) / (n - 1) * 14))                                    # map onto the eye-dive's 15-step dive
    o = eye_dive(out, None, min(-1, jj), f, s, None)
    return o * (1 - smooth((j + 5) / 4))                                              # last frames fall to black (loop seam)

# ---- graphics
def hud(out, f, a=0.45):
    """forensic viewfinder: corner brackets + a measuring ruler (act 1)."""
    lay = np.zeros((H, W), np.float32); L = 70; th_ = 3
    for (x, y, sx, sy) in ((70, 250, 1, 1), (W - 70, 250, -1, 1), (70, 1610, 1, -1), (W - 70, 1610, -1, -1)):
        cv2.line(lay, (x, y), (x + sx * L, y), 1.0, th_, cv2.LINE_AA); cv2.line(lay, (x, y), (x, y + sy * L), 1.0, th_, cv2.LINE_AA)
    off = (f * 2) % 30
    cv2.line(lay, (52, 430), (52, 1230), 0.7, 2, cv2.LINE_AA)
    for y in range(430 - off + 30, 1230, 30):
        cv2.line(lay, (52, y), (52 + (22 if (y + off) % 150 == 0 else 11), y), 0.7, 2, cv2.LINE_AA)
    return np.clip(out + lay[..., None] * UV * a, 0, 1)

_HIT = {}
def blood_hits(out, f):
    """a spatter lands on the edge of frame on each montage beat, then fades."""
    t = f / FPS; h = t / E.HB + E.H0
    if not (E.MONTAGE[0] <= h < E.MONTAGE[1] + 2): return out
    hb = int((h - E.MONTAGE[0]) // 4) * 4 + E.MONTAGE[0]; k = f - E.fh(hb)
    if k > 16: return out
    if hb not in _HIT:
        rng = np.random.default_rng(hb); m = np.zeros((H, W), np.float32); side = (hb // 4) % 3
        cx = [rng.uniform(40, 260), rng.uniform(W - 260, W - 40), rng.uniform(200, W - 200)][side]
        cy = rng.uniform(320, 1300) if side < 2 else rng.uniform(260, 420)
        ang = math.atan2(H * 0.4 - cy, W / 2 - cx) + rng.normal(0, 0.4); r = rng.uniform(16, 26)
        cv2.ellipse(m, (int(cx), int(cy)), (int(r * 1.5), int(r)), math.degrees(ang), 0, 360, 1.0, -1, cv2.LINE_AA)
        for _ in range(int(rng.integers(5, 9))):                                   # spines thrown in the travel direction
            a2 = ang + rng.normal(0, 0.35); L = rng.uniform(40, 150)
            cv2.line(m, (int(cx), int(cy)), (int(cx + L * math.cos(a2)), int(cy + L * math.sin(a2))), 1.0, int(rng.integers(2, 6)), cv2.LINE_AA)
            cv2.circle(m, (int(cx + (L + 10) * math.cos(a2)), int(cy + (L + 10) * math.sin(a2))), int(rng.integers(3, 8)), 1.0, -1, cv2.LINE_AA)
        for _ in range(40):                                                         # satellite mist
            a2 = ang + rng.normal(0, 0.9); d = rng.uniform(r, 230)
            cv2.circle(m, (int(cx + d * math.cos(a2)), int(cy + d * math.sin(a2))), int(max(1, rng.uniform(1, 5) * (1 - d / 260))), 1.0, -1, cv2.LINE_AA)
        _HIT[hb] = cv2.GaussianBlur(m, (0, 0), 0.8)
    a = (1 if k < 3 else math.exp(-(k - 3) / 6)) * 0.9; m = _HIT[hb][..., None] * a
    return np.clip(out * (1 - m) + m * BLOOD * 0.9 + m * (np.roll(_HIT[hb], -4, 0) - _HIT[hb] > 0.3)[..., None] * 0.25, 0, 1)

def finish_noir(out, f):
    L = lum(out); hi = np.clip(L - 0.62, 0, 1)
    small = cv2.resize(hi, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    halo = cv2.resize(cv2.GaussianBlur(small, (0, 0), 6), (W, H))[..., None]
    out = out + halo * (BLOOD_HI * 0.35 + WHITE * 0.10)                               # red halation
    out = rgb_split(out, 2)
    return np.clip(out * VIG * VIG ** 0.4 + grain(f, 0.020), 0, 1)

# ---- type
_TW = {}
def word_img(word, style, emph):
    key = (word, style, emph)
    if key in _TW: return _TW[key]
    if style in ("case", "confess0"):
        m = text_mask(word, F_MONO, 86, tracking=2); col = BLOOD_HI if emph else WHITE * 0.96
        L = shadowed(m, col, blur=9, sa=0.85)
    elif style in ("stamp", "doorsbig", "confess1"):
        size = {"stamp": 168, "doorsbig": 190, "confess1": 116}[style]
        m = text_mask(word, F_DISP, size, tracking=6); m = cv2.resize(m, (int(m.shape[1] * 0.9), m.shape[0]))
        col = BLOOD_HI if style != "doorsbig" else WHITE * 0.95
        if style == "stamp": col = WHITE * 0.97
        pad = 30; mm = np.pad(m, pad); hh, ww = mm.shape; L = np.zeros((hh, ww, 4), np.float32)
        echo = np.roll(np.roll(mm, 9, 0), 7, 1)
        L[..., :3] = BLOOD * echo[..., None]; L[..., 3] = echo * 0.95                  # blood-red offset echo
        L[..., :3] = L[..., :3] * (1 - mm[..., None]) + col * mm[..., None]; L[..., 3] = np.maximum(L[..., 3], mm)
        sh = cv2.GaussianBlur(mm, (0, 0), 12) * 0.7; L[..., 3] = np.maximum(L[..., 3], sh)
        if style == "confess1":
            for x in np.random.default_rng(len(word)).choice(np.nonzero(mm.sum(0))[0], 7, replace=False):
                ys = np.nonzero(mm[:, x] > 0.5)[0]
                if len(ys): cv2.line(L, (int(x), int(ys.max())), (int(x), int(min(hh - 2, ys.max() + np.random.default_rng(x).integers(8, pad)))), (*BLOOD_HI.tolist(), 1.0), 4, cv2.LINE_AA)
        if style == "doorsbig":
            L[..., :3] = L[..., :3] * (1 - mm[..., None]) + (WHITE * 0.8 + UV * 0.2) * mm[..., None]
    else:
        m = text_mask(word, F_MONO, 110, tracking=6); L = shadowed(m, WHITE * 0.96, blur=10, sa=0.85)
    _TW[key] = L; return L

def lay_words(out, f, words, y, style, emph, t_out, gap=None):
    t = f / FPS; imgs = [word_img(w, style, w in emph) for w, _ in words]
    sp = 26 if gap is None else gap
    vs = [eout(((t - wt) * FPS + 1) / 11, 3) for _, wt in words]
    total = sum((im.shape[1] + sp) * v for im, v in zip(imgs, vs)) - sp * vs[-1]
    x = W / 2 - max(total, 0) / 2; fade = 1.0 if t < t_out else clamp(1 - (t - t_out) * FPS / 8, 0, 1)
    for im, v in zip(imgs, vs):
        if v > 0.001:
            L = im if v >= 1 else cv2.GaussianBlur(im, (0, 0), 0.1 + 6 * (1 - v))
            if style in ("stamp", "confess1") and v < 1:                               # punch: scales down onto the frame
                s_ = 1 + 0.35 * (1 - v); L = cv2.resize(L, (int(L.shape[1] * s_), int(L.shape[0] * s_)))
            out = paste(out, L, int(x + im.shape[1] / 2 - L.shape[1] / 2), int(y + 28 * (1 - v) - L.shape[0] / 2), v * fade)
        x += (im.shape[1] + sp) * v
    return out, x

def text7(out, f):
    t = f / FPS
    for tx in getattr(E, "TEXT", []):
        st_ = tx["style"]; ws = tx["words"]; t0, t1 = ws[0][1] - 0.05, tx["end"]
        if st_ == "luminol" or not (t0 <= t < t1 + 0.2): continue
        if st_ == "case":
            for ln in (0, 1):
                row = [(w, wt) for w, wt, l_ in ws if l_ == ln]
                if row: out, xe = lay_words(out, f, row, E.CAP_Y[ln] if len({l for _, _, l in ws}) > 1 else 1420, "case", tx["emph"], t1)
            if t < t1 - 0.05 and int(t * 4) % 2 == 0:                                    # blinking case-file caret
                last_ln = max(l for w, wt, l in ws if wt <= t) if any(wt <= t for _, wt, _ in ws) else 0
                yc = (E.CAP_Y[last_ln] if len({l for _, _, l in ws}) > 1 else 1420)
                cv2.rectangle(out, (int(xe + 4), int(yc - 30)), (int(xe + 30), int(yc + 32)), tuple(float(c) for c in UV * 0.9), -1)
        elif st_ == "stamp":
            out, _ = lay_words(out, f, [(w, wt) for w, wt, _ in ws], 1430, "stamp", [], t1)
        elif st_ == "doors":
            (w0, ta, _), (w1, tb, _) = ws
            if t < tb: out, _ = lay_words(out, f, [(w0, ta)], 1420, "mono", [], tb - 0.30)   # OPEN clears as the lid falls; CLOSE is engraved on the lid
        elif st_ == "confess":
            r0 = [(w, wt) for w, wt, l in ws if l == 0]; r1 = [(w, wt) for w, wt, l in ws if l == 1]
            out, _ = lay_words(out, f, r0, 1300, "case", [], t1)
            out, _ = lay_words(out, f, r1, 1460, "confess1", [], t1, gap=34)
    return out

def last_visible(P):
    """last frame of shot P as it was seen (plastic + luminol title for the reveal shot)."""
    if P.get("plastic"):
        fr = P["f1"] - 1; return plastic_layer(render_shot(P, fr), fr, P)
    return last_frame_of(P)

# ============================================================================ v7 frame
def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999; t = f / FPS
    P = prev_shot(s); tin = s.get("tin"); tout = s.get("tout")
    out = render_shot(s, f)
    if s.get("plastic"): out = plastic_layer(out, f, s)
    if s.get("lensframe") and k >= (TR2[tin][2] if tin in TR2 else 0): out = lens_frame(cv2.GaussianBlur(out, (0, 0), 1.2))
    out = evidence_markers(out, f, s)
    if tin in TR2 and k < TR2[tin][2]: out = TR2[tin][0](last_visible(P) if P else out * 0, out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, render_shot(n_, n_["f0"], False), kn, f, s, n_)
    if tout == "pupil_end": out = pupil_end(out, f, s)
    h = t / E.HB + E.H0
    if h < E.HDROP and k >= (16 if tin == "lens_open" else 0): out = hud(out, f, 0.42 * clamp(k / 10, 0, 1) if tin == "lens_open" else 0.42)
    out = blood_hits(out, f)
    out = text7(out, f); out = case_stamp(out, f)
    out = finish_noir(out, f)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)

# ============================================================================ v7 rev 2 — new transitions + graphics
BRASS = np.array([0.22, 0.58, 0.82], np.float32)
WOOD = np.array([0.08, 0.15, 0.36], np.float32)

def _lowfreq(shape, cells, seed):
    rng = np.random.default_rng(seed); return cv2.resize(rng.random(cells).astype(np.float32), (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC)

# ---- 1. CLOSE: Dexter's rosewood blood-slide box slams shut on "close", reopens, the camera dives into a blood drop
_BOX = {}
def box_lid(engrave):
    """the lid's outer face: rosewood grain, brass corners + hinges, brass plate with CLOSE engraved (0..1)."""
    if "lid" not in _BOX:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        warp = _lowfreq((H, W), (12, 8), 3) * 60 + _lowfreq((H, W), (60, 30), 4) * 8
        g = 0.5 + 0.5 * np.sin((xx + warp * 0.6) / 5.0); g2 = 0.5 + 0.5 * np.sin((xx * 0.53 + warp * 1.3) / 2.2)
        fib = cv2.GaussianBlur(np.random.default_rng(6).random((H, W)).astype(np.float32), (0, 0), sigmaX=0.6, sigmaY=9)
        tone = 0.70 + 0.14 * g + 0.06 * g2 + 0.12 * (fib - 0.5) + 0.16 * (_lowfreq((H, W), (8, 5), 5) - 0.5)
        lid = WOOD * tone[..., None]
        lid = lid + np.clip(1 - np.abs((xx - W * 0.25) * 0.6 + (yy - H * 0.3) * 0.35) / 380, 0, 1)[..., None] * 0.10      # varnish sheen
        vg = np.clip(1 - (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) * 0.22, 0.6, 1)
        lid = lid * vg[..., None]
        for inset in (46, 58):                                                      # inlay lines
            cv2.rectangle(lid, (inset, inset), (W - inset, H - inset), tuple(float(c) for c in WOOD * 1.7), 2, cv2.LINE_AA)
        def brass_plate(x0, y0, x1, y1, r=10):
            m = np.zeros((H, W), np.float32); cv2.rectangle(m, (x0 + r, y0), (x1 - r, y1), 1, -1); cv2.rectangle(m, (x0, y0 + r), (x1, y1 - r), 1, -1)
            for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)): cv2.circle(m, (cx, cy), r, 1, -1, cv2.LINE_AA)
            grad = np.clip(1.15 - ((xx - x0) / max(1, x1 - x0)) * 0.25 - ((yy - y0) / max(1, y1 - y0)) * 0.35, 0.6, 1.2)
            return m, BRASS * grad[..., None]
        acc = lid.copy()
        for (x0, y0, x1, y1) in ((24, 24, 180, 60), (24, 24, 60, 180), (W - 180, 24, W - 24, 60), (W - 60, 24, W - 24, 180),
                                 (24, H - 60, 180, H - 24), (24, H - 180, 60, H - 24), (W - 180, H - 60, W - 24, H - 24), (W - 60, H - 180, W - 24, H - 24),
                                 (int(W * 0.22), 0, int(W * 0.34), 34), (int(W * 0.66), 0, int(W * 0.78), 34)):
            m, col = brass_plate(x0, y0, x1, y1, 6); acc = acc * (1 - m[..., None]) + col * m[..., None]
        px0, py0, px1, py1 = W // 2 - 360, int(H * 0.52) - 120, W // 2 + 360, int(H * 0.52) + 120
        sh = np.zeros((H, W), np.float32); cv2.rectangle(sh, (px0 + 10, py0 + 14), (px1 + 10, py1 + 14), 1, -1)
        acc = acc * (1 - cv2.GaussianBlur(sh, (0, 0), 10)[..., None] * 0.55)
        m, col = brass_plate(px0, py0, px1, py1, 18); acc = acc * (1 - m[..., None]) + col * m[..., None]
        cv2.rectangle(acc, (px0 + 14, py0 + 14), (px1 - 14, py1 - 14), tuple(float(c) for c in BRASS * 0.7), 2, cv2.LINE_AA)
        for sx, sy in ((px0 + 30, py0 + 30), (px1 - 30, py0 + 30), (px0 + 30, py1 - 30), (px1 - 30, py1 - 30)):
            cv2.circle(acc, (sx, sy), 9, tuple(float(c) for c in BRASS * 0.55), -1, cv2.LINE_AA); cv2.line(acc, (sx - 6, sy), (sx + 6, sy), (0.05, 0.08, 0.12), 2, cv2.LINE_AA)
        tm = text_mask("CLOSE", F_DISP, 150, tracking=22); th_, tw_ = tm.shape
        T = np.zeros((H, W), np.float32); ty, tx = (py0 + py1) // 2 - th_ // 2, W // 2 - tw_ // 2; T[ty:ty + th_, tx:tx + tw_] = tm
        _BOX.update(lid=np.clip(acc, 0, 1).astype(np.float32), text=T, plate=(px0, py0, px1, py1))
    lid = _BOX["lid"]
    if engrave <= 0: return lid
    T = _BOX["text"] * engrave
    hi = np.roll(T, 3, 0) * (1 - T)                                                  # lower lip catches light
    return np.clip(lid * (1 - T[..., None] * 0.80) + np.array([0.02, 0.04, 0.07], np.float32) * T[..., None] + hi[..., None] * BRASS * 0.5, 0, 1)

def box_interior():
    """open box: red velvet, a column of glass slides each with a blood drop; the middle drop sits at the frame centre."""
    if "in" not in _BOX:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        vel = np.array([0.05, 0.03, 0.30], np.float32) * (0.75 + 0.35 * _lowfreq((H, W), (120, 70), 8))[..., None]
        o = vel.copy(); rd = 95; sw, sh_ = 820, 210
        for i in range(-3, 4):
            cy = H // 2 + i * 262; x0, y0, x1, y1 = W // 2 - sw // 2, cy - sh_ // 2, W // 2 + sw // 2, cy + sh_ // 2
            cv2.rectangle(o, (x0 - 14, y0 - 16), (x1 + 14, y1 + 16), tuple(float(c) for c in WOOD * 0.8), -1)       # wooden slot
            sub = o[y0:y1, x0:x1]; o[y0:y1, x0:x1] = sub * 0.45 + np.array([0.80, 0.82, 0.80], np.float32) * 0.40   # glass
            cv2.rectangle(o, (x0, y0), (x1, y1), (0.95, 0.96, 0.95), 2, cv2.LINE_AA)
            cv2.rectangle(o, (x0 + 10, y0 + 12), (x0 + 170, y1 - 12), (0.88, 0.90, 0.90), -1)                     # label
            for k in range(3): cv2.line(o, (x0 + 24, y0 + 40 + k * 40), (x0 + 150 - k * 22, y0 + 40 + k * 40), (0.25, 0.25, 0.3), 3, cv2.LINE_AA)
            if i != 0:
                cv2.circle(o, (W // 2 + 60, cy), rd, (0.03, 0.02, 0.45), -1, cv2.LINE_AA)
                cv2.circle(o, (W // 2 + 60 - 30, cy - 34), 18, (0.55, 0.55, 0.95), -1, cv2.LINE_AA)
        _BOX["in"] = np.clip(o, 0, 1).astype(np.float32); _BOX["drop"] = (W // 2 + 60, H // 2, rd)
    return _BOX["in"], _BOX["drop"]

def lid_over(under, phi, img, shade=1.0):
    """composite the lid (hinged at the top of the frame) rotated phi (deg; 0 = closed, 90 = open/edge-on) over `under`."""
    p = math.radians(phi); D = 2.6 * H; s = D / (D - H * math.sin(p)); yb = H * math.cos(p) * s
    if yb < 2: return under
    q = np.float32([[0, 0], [W, 0], [W / 2 + W / 2 * s, yb], [W / 2 - W / 2 * s, yb]])
    Mp = cv2.getPerspectiveTransform(np.float32([[0, 0], [W, 0], [W, H], [0, H]]), q)
    li = cv2.warpPerspective(img * shade, Mp, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
    lm = cv2.warpPerspective(np.ones((H, W), np.float32), Mp, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)[..., None]
    shadow = np.clip(1 - (np.arange(H)[:, None] - yb) / 260, 0, 1)[..., None] * (np.arange(H)[:, None] > yb)[..., None] * 0.6
    return under * (1 - shadow) * (1 - lm) + li * lm

def slidebox_close(A, B, j, f, sa, sb):
    js = E.fe(E.CLOSE_T) - sb["f0"]
    if j < 0:
        if j < js - 11: return A
        if j < js:                                                                     # lid falls
            u = (j - (js - 11)) / 11.0; phi = 90 * (1 - ein(u, 2.2))
            return np.clip(lid_over(A, phi, box_lid(0), 0.75 + 0.25 * u), 0, 1)
        k = j - js; phi = 3.5 * math.exp(-k / 2.2) * abs(math.sin(k * 1.5))           # slam + bounce
        e = eout(clamp((k - 2) / 10, 0, 1), 2)
        lid = box_lid(e)
        if 2 <= k <= 16:                                                               # glint sweeps across the brass plate
            px0, py0, px1, py1 = _BOX["plate"]; gx = px0 - 100 + (px1 - px0 + 200) * (k - 2) / 14
            band = np.exp(-(((_GX - gx) + (_GY - py0) * 0.4) / 30) ** 2) * ((_GX > px0) & (_GX < px1) & (_GY > py0) & (_GY < py1))
            lid = np.clip(lid + band[..., None] * 0.55, 0, 1)
        o = lid_over(A, phi, lid) if phi > 0.2 else lid
        o = zoom_about(o, W / 2, H * 0.52, 1 + 0.035 * clamp(k / 30, 0, 1))
        dx_, dy_, _ = shake(f); o = cv2.warpAffine(o, np.float32([[1, 0, dx_], [0, 1, dy_]]), (W, H), borderMode=cv2.BORDER_REFLECT)
        if k < 6:                                                                      # dust puff along the seams
            puff = (np.exp(-(_GY / 40) ** 2) + np.exp(-((H - _GY) / 40) ** 2) + np.exp(-(_GX / 40) ** 2) + np.exp(-((W - _GX) / 40) ** 2))
            o = np.clip(o + puff[..., None] * 0.35 * (1 - k / 6), 0, 1)
        return o
    v = j + 1; inside, (dx, dy, rd) = box_interior()
    phi = 90 * eout(clamp(v / 6, 0, 1), 2)
    Z = math.exp(math.log(12.5) * ein(clamp((v - 3) / 13, 0, 1), 2.3))
    tx = dx + (W / 2 - dx) * clamp((Z - 1) / 11.5, 0, 1)                              # the drop drifts to the frame centre
    M = np.float32([[Z, 0, tx - Z * dx], [0, Z, dy - Z * dy]])
    o = cv2.warpAffine(inside, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    cx = M[0, 0] * dx + M[0, 2]; cy = M[1, 1] * dy + M[1, 2]; R = rd * Z
    s_ = R / 1150.0; Mz = np.float32([[s_, 0, cx - s_ * W / 2], [0, s_, cy - s_ * H / 2]])
    con = cv2.warpAffine(B, Mz, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    tint = clamp(1 - (Z - 1) / 9, 0, 1)
    con = con * (1 - 0.6 * tint) + np.array([0.03, 0.02, 0.45], np.float32) * 0.6 * tint
    cm = np.zeros((H, W), np.float32); cv2.circle(cm, (int(cx), int(cy)), int(min(R, 5000)), 1.0, -1, cv2.LINE_AA)
    o = o * (1 - cm[..., None]) + con * cm[..., None]
    if phi < 89.5: o = lid_over(o, phi, box_lid(1.0), 0.85)
    return np.clip(o, 0, 1)

# ---- 2. a drop of blood hits the lens and spreads; the next shot is seen through it, then the blood clears
_BL = {}
def blood_lens(A, B, j, f, sa, sb):
    if "n" not in _BL:
        rng = np.random.default_rng(44); ang = np.linspace(0, 2 * np.pi, 360, endpoint=False)
        prof = 1 + 0.18 * np.sin(ang * 3 + 1) + 0.10 * np.sin(ang * 7 + 2) + 0.06 * rng.standard_normal(360).cumsum() / 12
        _BL["prof"] = prof; _BL["a"] = np.arctan2(_GY - H * 0.42, _GX - W / 2); _BL["r"] = np.sqrt((_GX - W / 2) ** 2 + (_GY - H * 0.42) ** 2)
    r, a = _BL["r"], _BL["a"]; prof = np.interp(a, np.linspace(-np.pi, np.pi, 360, endpoint=False), _BL["prof"])
    if j < 0:                                                                          # the drop falls toward the lens
        u = (j + 9) / 9.0; y = -80 + (H * 0.42 + 80) * ein(u, 2.0); rr = 10 + 80 * ein(u, 2.5)
        o = A.copy(); cv2.ellipse(o, (W // 2, int(y)), (int(rr), int(rr * 1.25)), 0, 0, 360, (0.03, 0.02, 0.42), -1, cv2.LINE_AA)
        cv2.circle(o, (W // 2 - int(rr * 0.35), int(y - rr * 0.45)), max(2, int(rr * 0.22)), (0.6, 0.6, 1.0), -1, cv2.LINE_AA)
        return np.clip(o, 0, 1)
    v = (j + 1) / 18.0; R = 1500 * eout(clamp(v / 0.55, 0, 1), 2.2)
    m = np.clip((R * prof - r) / 10, 0, 1)[..., None]
    lensed = barrel(B, 0.25 * (1 - v), W / 2, H * 0.42, 900)
    tint = clamp(1 - (v - 0.35) / 0.65, 0, 1)
    inside = lensed * (1 - 0.65 * tint) + np.array([0.04, 0.03, 0.55], np.float32) * 0.65 * tint
    rim = np.exp(-((R * prof - r) / 18) ** 2)[..., None] * (1 - v)
    o = A * 0.6 * (1 - m) + inside * m + rim * np.array([0.02, 0.02, 0.30], np.float32)
    if v > 0.45:                                                                        # drips run down as it clears
        dr = np.zeros((H, W), np.float32); rng = np.random.default_rng(9)
        for x in rng.uniform(40, W - 40, 9):
            L_ = (v - 0.45) * rng.uniform(500, 1200); y0 = rng.uniform(100, 600)
            cv2.line(dr, (int(x), int(y0)), (int(x), int(y0 + L_)), 1.0, int(rng.integers(6, 14)), cv2.LINE_AA)
        o = o * (1 - dr[..., None] * 0.5 * tint) + dr[..., None] * np.array([0.03, 0.02, 0.40], np.float32) * 0.5 * tint
    return np.clip(o, 0, 1)

# ---- 3. HERO: the plastic stretches toward the camera, then bursts open in flaps with a blood spray (the drop)
_BU = {}
def burst(A, B, j, f, sa, sb, n_flaps=9):
    cx, cy = W / 2, H * 0.47; rr = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2)
    if j < 0:                                                                          # stretch / bulge
        u = (j + 19) / 19.0; k_ = 0.34 * ein(u, 1.8)                                    # centre-weighted bulge (title stays clean)
        g = 1 - k_ * np.exp(-(rr / 430) ** 2)
        o = cv2.remap(A, (cx + (_GX - cx) * g).astype(np.float32), (cy + (_GY - cy) * g).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        ring = np.exp(-((rr - (560 - 220 * u)) / 70) ** 2)[..., None] * ein(u, 1.5)   # tension highlight around the bulge
        o = o * (1 + 0.12 * ein(u, 2)) + ring * (WHITE * 0.22 + UV * 0.10) + np.exp(-(rr / (120 + 60 * u)) ** 2)[..., None] * 0.3 * ein(u, 3)
        if u > 0.7: o = zoom_about(o, cx + 6 * math.sin(j * 2.3), cy + 5 * math.cos(j * 3.1), 1.0)
        return np.clip(rgb_split(o, 10 * ein(u, 2)), 0, 1)
    if "seed" not in _BU:
        rng = np.random.default_rng(77)
        _BU["edges"] = np.sort(rng.uniform(0, 2 * np.pi, n_flaps)); _BU["drops"] = [(rng.uniform(0, 6.283), rng.uniform(2600, 5200), rng.uniform(5, 16), rng.uniform(0, 0.06)) for _ in range(60)]
        _BU["jag"] = rng.standard_normal(720).cumsum(); _BU["jag"] = (_BU["jag"] - _BU["jag"].mean()) / (np.abs(_BU["jag"]).max() + 1e-6); _BU["seed"] = 1
    v = (j + 1) / 18.0; a = np.mod(np.arctan2(_GY - cy, _GX - cx), 2 * np.pi)
    Rh = 1500 * eout(v, 2.4) * (1 + 0.16 * np.interp(a, np.linspace(0, 2 * np.pi, 720), _BU["jag"]))
    hole = np.clip((Rh - rr) / 6, 0, 1)
    o = zoom_about(B, cx, cy, 1.25 - 0.25 * eout(v, 2))
    shock = np.exp(-((rr - 1700 * eout(v, 1.6)) / 70) ** 2)[..., None] * (1 - v)
    o = np.clip(o * (1 + 0.8 * (1 - v) ** 3) + shock * (WHITE * 0.5 + BLOOD_HI * 0.5), 0, 1)
    edges = _BU["edges"]
    for i in range(len(edges)):
        a0, a1 = edges[i], edges[(i + 1) % len(edges)] + (2 * np.pi if i == len(edges) - 1 else 0); am = (a0 + a1) / 2
        inw = (np.mod(a - a0, 2 * np.pi) < np.mod(a1 - a0, 2 * np.pi)).astype(np.float32) * (1 - hole)
        d = 900 * ein(v, 1.6); sc = 1 + 0.9 * ein(v, 1.8); rot = 25 * v * (1 if i % 2 else -1)
        M = cv2.getRotationMatrix2D((cx, cy), rot, sc); M[0, 2] += d * math.cos(am); M[1, 2] += d * math.sin(am)
        fl = cv2.warpAffine(A * (1 - 0.35 * v), M, (W, H), borderMode=cv2.BORDER_CONSTANT)
        fm = cv2.warpAffine(inw, M, (W, H), borderValue=0)[..., None] * (1 - smooth((v - 0.55) / 0.45))
        edge = cv2.warpAffine(np.clip(cv2.morphologyEx((inw > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8)).astype(np.float32), 0, 1), M, (W, H), borderValue=0)[..., None]
        o = o * (1 - fm) + fl * fm + edge * fm * WHITE * 0.6
    for ang, sp, rad, dl in _BU["drops"]:                                              # blood spray toward the camera
        tt = (j + 1) / FPS - dl
        if tt <= 0: continue
        dist = 180 + sp * tt; x = cx + dist * math.cos(ang); y = cy + dist * math.sin(ang) + 900 * tt * tt; rr2 = rad * (0.6 + 2.5 * tt)
        if -80 < x < W + 80 and -80 < y < H + 80 and tt < 0.2:
            al = clamp(1 - tt / 0.2, 0, 1); lay = o.copy()
            cv2.ellipse(lay, (int(x), int(y)), (int(rr2 * 5), int(rr2)), math.degrees(ang), 0, 360, (0.03, 0.02, 0.50), -1, cv2.LINE_AA)
            o = o * (1 - al) + lay * al
    return np.clip(o, 0, 1)

# ---- 4. body-bag zipper: the bag zips shut over the frame, then unzips onto the next shot
_ZB = {}
def bag_tex():
    if "b" not in _ZB:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        folds = np.zeros((H, W), np.float32); rng = np.random.default_rng(15)
        for _ in range(10):
            a = rng.uniform(-0.8, 0.8); c = rng.uniform(-400, H + 400); wd = rng.uniform(20, 70)
            folds += rng.uniform(0.4, 1.0) * np.exp(-(((yy - c) - a * (xx - W / 2)) / wd) ** 2)
        _ZB["b"] = (np.array([0.035, 0.035, 0.04], np.float32) + folds[..., None] * 0.10 * WHITE).astype(np.float32)
    return _ZB["b"]

def zipper(A, B, j, f, sa, sb):
    bag = bag_tex(); pre = j < 0
    v = (j + 10) / 10.0 if pre else (j + 1) / 12.0
    ys = -80 + (H + 160) * eout(v, 1.6)
    yy = np.arange(H, dtype=np.float32)[:, None]
    hw = np.clip((yy - ys) * 0.42, 0, None) if pre else np.clip((ys - yy) * 0.42, 0, None)
    open_ = (np.abs(_GX - W / 2) < hw).astype(np.float32)
    o = bag * (1 - open_[..., None]) + (A if pre else B) * open_[..., None]
    o = o * (1 - 0.5 * (np.exp(-((np.abs(_GX - W / 2) - hw) / 26) ** 2) * (hw > 0))[..., None])   # bag edge shading
    lay = np.zeros((H, W), np.float32)
    for y in range(0, H, 14):                                                          # teeth: along the open edges + closed seam
        h_ = float(hw[y, 0])
        if h_ > 1:
            for sg in (-1, 1): cv2.rectangle(lay, (int(W / 2 + sg * h_ - 7), y), (int(W / 2 + sg * h_ + 7), y + 7), 1.0, -1)
        else: cv2.rectangle(lay, (W // 2 - 9 + (4 if (y // 14) % 2 else -4), y), (W // 2 + 9 + (4 if (y // 14) % 2 else -4), y + 7), 1.0, -1)
    o = o * (1 - lay[..., None]) + lay[..., None] * np.array([0.55, 0.56, 0.58], np.float32)
    if -60 < ys < H + 60:                                                              # the slider + pull tab
        cv2.rectangle(o, (W // 2 - 34, int(ys) - 46), (W // 2 + 34, int(ys) + 46), (0.62, 0.63, 0.66), -1, cv2.LINE_AA)
        cv2.rectangle(o, (W // 2 - 34, int(ys) - 46), (W // 2 + 34, int(ys) + 46), (0.9, 0.9, 0.92), 2, cv2.LINE_AA)
        cv2.rectangle(o, (W // 2 - 14, int(ys) + 40), (W // 2 + 14, int(ys) + 150), (0.5, 0.5, 0.53), -1, cv2.LINE_AA)
    return np.clip(o, 0, 1)

# ---- 5. M99: vision doubles, blurs and the eyelids close; they blink open on the next shot
def eyelids(img, openness):
    top = (H / 2 + 40) * (1 - openness); xn = (_GX - W / 2) / (W / 2)
    m = ((_GY < top * (1 - 0.18 * xn ** 2)) | (_GY > H - top * (1 - 0.18 * xn ** 2))).astype(np.float32)
    m = cv2.GaussianBlur(m, (0, 0), 14)[..., None]
    return img * (1 - m) + 0.01 * m

def m99(A, B, j, f, sa, sb):
    if j < 0:
        u = (j + 15) / 15.0; d = int(70 * u)
        o = 0.5 * np.roll(A, d, 1) + 0.5 * np.roll(A, -d, 1)
        o = cv2.GaussianBlur(o, (0, 0), 0.1 + 7 * u); L = lum(o)[..., None]; o = (L + (o - L) * (1 - 0.6 * u)) * (1 - 0.35 * u)
        op = 1 - ein(u, 1.6) + 0.25 * math.sin(math.pi * clamp((u - 0.3) / 0.35, 0, 1)) ** 2
        return np.clip(eyelids(o, clamp(op, 0, 1)), 0, 1)
    v = (j + 1) / 12.0
    op = np.interp(v, [0, 0.3, 0.45, 0.6, 1.0], [0.0, 0.55, 0.15, 0.4, 1.0])
    d = int(50 * (1 - v)); o = 0.5 * np.roll(B, d, 1) + 0.5 * np.roll(B, -d, 1)
    o = cv2.GaussianBlur(o, (0, 0), 0.1 + 6 * (1 - v))
    return np.clip(eyelids(o, op), 0, 1)

# ---- 6. the magnifying glass sweeps in over his face; inside it, his eye; the glass becomes the frame
def mag_sweep(A, B, j, f, sa, sb):
    R1, cy1 = 640.0, H * 0.40
    if j < 0:
        u = eout((j + 11) / 11.0, 2.4); cx = W + 460 + (W / 2 - W - 460) * u; cy = H + 420 + (cy1 - H - 420) * u; R = 360 + (R1 - 360) * u
    else:
        v = (j + 1) / 12.0; cx, cy, R = W / 2, cy1, R1
    rr = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2); m = np.clip((R - rr) / 5, 0, 1)[..., None]
    Bm = barrel(zoom_about(B, W / 2, cy1, 1.0), 0.18, W / 2, cy1, R1)
    Bm = cv2.warpAffine(Bm, np.float32([[1, 0, cx - W / 2], [0, 1, cy - cy1]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    if j < 0: outside = A
    else: outside = A * (1 - smooth(v)) + cv2.resize(cv2.GaussianBlur(cv2.resize(B, (W // 4, H // 4)), (0, 0), 6), (W, H)) * 0.22 * smooth(v)
    o = outside * (1 - m) + Bm * m
    rim = np.exp(-((rr - R) / 14) ** 2)[..., None]; o = o + rim * (PINK * 0.45 + WHITE * 0.25)
    hand = np.zeros((H, W), np.float32); ha = math.radians(52)
    p0 = (cx + (R + 10) * math.cos(ha), cy + (R + 10) * math.sin(ha)); p1 = (p0[0] + 700 * math.cos(ha), p0[1] + 700 * math.sin(ha))
    cv2.line(hand, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), 1.0, 64, cv2.LINE_AA)
    ha_a = 1.0 if j < 0 else 1 - smooth(v / 0.6)
    o = o * (1 - hand[..., None] * ha_a) + hand[..., None] * ha_a * np.array([0.16, 0.10, 0.30], np.float32)
    return np.clip(o, 0, 1)

def logo_orig(A, B, j, f, sa, sb):
    """the voidfx logo exactly as supplied (its own colours), flown through the 'o' — never restyled."""
    return logo_through(A, B, j)

TR2.update({"slidebox_close": (slidebox_close, 50, 16), "blood_lens": (blood_lens, 9, 18), "burst": (burst, 19, 18),
            "zipper": (zipper, 10, 12), "m99": (m99, 15, 12), "mag_sweep": (mag_sweep, 11, 12), "logo_orig": (logo_orig, 12, 11)})

# ---- graphics: crime-scene evidence markers drop in on the beat; the CASE CLOSED rubber stamp
_EM = {}
def evidence_markers(out, f, s):
    if not s.get("markers"): return out
    if "t" not in _EM:
        tiles = []
        for n in (1, 2, 3):
            tw, tht = 150, 170; t = np.zeros((tht, tw, 4), np.float32)
            pts = np.int32([[22, tht - 4], [tw - 22, tht - 4], [tw - 44, 8], [44, 8]]); m = np.zeros((tht, tw), np.float32); cv2.fillConvexPoly(m, pts, 1.0, cv2.LINE_AA)
            t[..., :3] = TAPE_Y * (0.85 + 0.15 * np.linspace(1, 0.7, tht)[:, None, None]); t[..., 3] = m
            nm = text_mask(str(n), F_DISP, 96); nh, nw = nm.shape; y0, x0 = (tht - nh) // 2 + 8, (tw - nw) // 2
            t[y0:y0 + nh, x0:x0 + nw, :3] *= (1 - nm[..., None] * 0.95)
            tiles.append(t)
        _EM["t"] = tiles
    pos = [(250, 1540), (560, 1610), (850, 1525)]; hbs = [s["f0"] + 4, E.fe(s["t0"] + 2 * E.HB), E.fe(s["t0"] + 4 * E.HB)]   # beats 0, +2, +4 half-beats
    for t_img, (x, y), fh_ in zip(_EM["t"], pos, hbs):
        k = f - fh_
        if k < 0: continue
        drop = 1 - eout(k / 7, 2.5); sq = 1 + 0.18 * math.exp(-max(0, k - 7) / 2.5) * math.sin(max(0, k - 7) * 1.7)
        yy = int(y - 260 * drop); im = cv2.resize(t_img, (int(t_img.shape[1] / sq), int(t_img.shape[0] * sq)))
        if drop > 0.05: im = cv2.GaussianBlur(im, (0, 0), 0.1 + 3 * drop)
        sh = np.zeros_like(im); sh[..., 3] = cv2.GaussianBlur(im[..., 3], (0, 0), 8) * 0.55 * (1 - drop)
        out = paste(out, sh, int(x - im.shape[1] / 2 + 14), int(yy - im.shape[0] + 10), 1.0)
        out = paste(out, im, int(x - im.shape[1] / 2), int(yy - im.shape[0]), clamp(k / 3, 0, 1))
    return out

_ST = {}
def case_stamp(out, f):
    tx = [t for t in E.TEXT if t["style"] == "casestamp"]
    if not tx: return out
    tx = tx[0]; t = f / FPS; t0 = tx["words"][0][1]; k = (t - t0) * FPS
    if k < 0 or t > tx["end"] + 0.15: return out
    if "s" not in _ST:
        tm = text_mask("CASE CLOSED", F_DISP, 112, tracking=10); pad = 46; hh, ww = tm.shape[0] + 2 * pad, tm.shape[1] + 2 * pad
        m = np.zeros((hh, ww), np.float32); m[pad:pad + tm.shape[0], pad:pad + tm.shape[1]] = tm
        cv2.rectangle(m, (8, 8), (ww - 9, hh - 9), 1.0, 9, cv2.LINE_AA); cv2.rectangle(m, (24, 24), (ww - 25, hh - 25), 1.0, 3, cv2.LINE_AA)
        rng = np.random.default_rng(6); n1 = cv2.GaussianBlur(rng.random((hh, ww)).astype(np.float32), (0, 0), 1.3)
        n2 = cv2.resize(rng.random((hh // 20 + 2, ww // 20 + 2)).astype(np.float32), (ww, hh), interpolation=cv2.INTER_CUBIC)
        m = m * np.clip((n1 * 0.6 + n2 * 0.6 - 0.12) * 2.8, 0, 1)                     # worn rubber-stamp ink
        rgba = np.zeros((hh, ww, 4), np.float32); rgba[..., :3] = np.array([0.08, 0.06, 0.78], np.float32); rgba[..., 3] = m * 0.97
        M = cv2.getRotationMatrix2D((ww / 2, hh / 2), 7, 1.0); big = int(max(hh, ww) * 1.05)
        M[0, 2] += (big - ww) / 2; M[1, 2] += (big - hh) / 2
        _ST["s"] = cv2.warpAffine(rgba, M, (big, big), borderValue=(0, 0, 0, 0))
        sc = min(1.0, 900 / _ST["s"].shape[1]); _ST["s"] = cv2.resize(_ST["s"], (int(_ST["s"].shape[1] * sc), int(_ST["s"].shape[0] * sc)))
    S_ = _ST["s"]; land = 6
    sc = 1 + 0.9 * (1 - eout(k / land, 3)) if k < land else 1 + 0.04 * math.exp(-(k - land) / 2) * math.sin((k - land) * 1.8)
    im = cv2.resize(S_, (int(S_.shape[1] * sc), int(S_.shape[0] * sc)))
    if k < land: im = cv2.GaussianBlur(im, (0, 0), 0.1 + 5 * (1 - k / land))
    a = eout(k / 4, 2) * (1.0 if t < tx["end"] else clamp(1 - (t - tx["end"]) * FPS / 8, 0, 1))
    y = 1440; out = paste(out, im, int(W / 2 - im.shape[1] / 2), int(y - im.shape[0] / 2), a)
    if land <= k < land + 10:                                                          # ink flecks on impact
        rng = np.random.default_rng(3); kk = k - land
        for _ in range(26):
            ang = rng.uniform(0, 6.28); d = rng.uniform(300, 520) + kk * 6
            x_, y_ = W / 2 + d * math.cos(ang), y + d * 0.45 * math.sin(ang)
            cv2.circle(out, (int(x_), int(y_)), int(rng.uniform(2, 6)), (0.10, 0.08, 0.72), -1, cv2.LINE_AA)
    return out

def init_hits():
    HITS.clear()
    for i, h in enumerate(range(E.MONTAGE[0], E.MONTAGE[1], 8)):
        a = (26, 10, 14, 10, 12)[min(i, 4)]; HITS.append((E.fh(h), a, 4.5))
    if getattr(E, "CLOSE_T", None) is not None: HITS.append((E.fe(E.CLOSE_T), 16, 3.5))   # lid slam
    st_ = [t for t in getattr(E, "TEXT", []) if t["style"] == "casestamp"]
    if st_: HITS.append((E.fe(st_[0]["words"][0][1]) + 6, 12, 3.0))                      # stamp lands

# ============================================================================ v8 — WISH YOU WELL: sodium-nocturne toolkit
SODIUM = np.array([0.22, 0.62, 1.00], np.float32)     # BGR sodium-vapour amber
INDIGO = np.array([0.30, 0.10, 0.04], np.float32)     # BGR deep indigo
BLOODR = np.array([0.05, 0.04, 0.62], np.float32)
WARMW = np.array([0.86, 0.93, 1.00], np.float32)
F_SERIF_I = "/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf"
F_SERIF_BI = "/usr/share/fonts/truetype/freefont/FreeSerifBoldItalic.ttf"
F_WIDE = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"
F_HEAVY = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"

def lum8(img): return img[..., 0] * 0.114 + img[..., 1] * 0.587 + img[..., 2] * 0.299

# ---- rain on glass: static beads + a few running drops, refracting (inverting) what's behind them
_RAIN = {}
def _drop_sprite(r):
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1].astype(np.float32); d = np.sqrt(xx * xx + yy * yy) / r
    m = np.clip((1 - d) * r / 1.5, 0, 1); nz = np.sqrt(np.clip(1 - d * d, 0, 1))
    return m, -xx / r * (1 - nz * 0.3), -yy / r * (1 - nz * 0.3)
def rain_maps(f, amt=1.0):
    if "beads" not in _RAIN:
        rng = np.random.default_rng(81)
        _RAIN["beads"] = [(rng.uniform(0, W), rng.uniform(0, H), int(rng.choice([3, 4, 5, 6, 8, 10, 13], p=[.25, .2, .18, .14, .1, .08, .05]))) for _ in range(520)]
        _RAIN["run"] = [(rng.uniform(40, W - 40), rng.uniform(-H, H), rng.uniform(5, 9), rng.uniform(2.5, 7.0), rng.uniform(0, 6.28)) for _ in range(16)]
        _RAIN["spr"] = {r: _drop_sprite(r) for r in range(2, 16)}
    m = np.zeros((H, W), np.float32); dx = np.zeros((H, W), np.float32); dy = np.zeros((H, W), np.float32)
    def put(x, y, r):
        r = int(max(2, min(15, r))); sm, sx, sy = _RAIN["spr"][r]; x0, y0 = int(x) - r, int(y) - r
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + 2 * r + 1), min(H, y0 + 2 * r + 1)
        if xb <= xa or yb <= ya: return
        s_ = (slice(ya - y0, yb - y0), slice(xa - x0, xb - x0)); w_ = sm[s_]
        m[ya:yb, xa:xb] = np.maximum(m[ya:yb, xa:xb], w_)
        dx[ya:yb, xa:xb] += sx[s_] * w_ * r * 2.2; dy[ya:yb, xa:xb] += sy[s_] * w_ * r * 2.2
    for (x, y, r) in _RAIN["beads"][:int(520 * amt)]: put(x, y, r)
    for (x, y0, r, v, ph) in _RAIN["run"][:int(16 * amt)]:
        v = max(1, round(v * E.DUR_F / (H + 300))) * (H + 300) / E.DUR_F
        y = (y0 + f * v) % (H + 300) - 150; xx = x + 6 * math.sin(2 * math.pi * f / E.DUR_F * 9 + ph)
        put(xx, y, r)
        for k in range(1, 9): put(xx - 0.4 * k, y - k * r * 0.9, max(2, r * 0.45))      # trail
    return m, dx, dy

def rain_glass(out, f, amt=1.0, focus=0.0):
    """rain on the windshield. focus 0 = scene in focus (drops soft), 1 = glass in focus (scene blurred)."""
    m, dx, dy = rain_maps(f, amt)
    if focus > 0.01:
        sb = cv2.GaussianBlur(cv2.resize(out, (W // 4, H // 4)), (0, 0), 1 + 7 * focus); out = out * (1 - focus) + cv2.resize(sb, (W, H)) * focus
    ref = cv2.remap(out, (_GX + dx).astype(np.float32), (_GY + dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    ref = cv2.GaussianBlur(ref, (0, 0), 1.2 + 2.5 * (1 - focus))
    mb = cv2.GaussianBlur(m, (0, 0), 0.6 + 2.0 * (1 - focus))[..., None]
    rim = np.clip(cv2.morphologyEx(m, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)), 0, 1)[..., None] * 0.25
    spec = np.clip(-dy * 0.06 - dx * 0.03, 0, 1)[..., None] * 0.18 * m[..., None]
    return np.clip(out * (1 - mb) + ref * mb * 1.05 - rim * 0.25 + spec * WARMW, 0, 1)

# ---- passing streetlights: warm diagonal light bands sweep across the frame on the half-beats
def sweeps(out, f, amt=1.0, phase=0.0):
    t = f / FPS; per = 2 * E.HB; u = ((t - phase) / per) % 1.0
    pos = -0.5 + 2.0 * u
    xs = (_GX / W) * 0.55 + (_GY / H) * 0.85
    band = np.exp(-((xs - pos) / 0.16) ** 2) * amt
    return np.clip(out * (1 + 0.55 * band[..., None]) + band[..., None] * SODIUM * 0.10, 0, 1)

# ---- night city bokeh behind the windshield (mirror composition)
_BK = {}
def city_bokeh(f):
    if "p" not in _BK:
        rng = np.random.default_rng(12)
        _BK["p"] = [(rng.uniform(-200, W + 200), rng.uniform(250, 1350), rng.uniform(40, 120), rng.choice([0, 0, 0, 1, 2]), rng.uniform(0.15, 0.6)) for _ in range(26)]
    lay = np.zeros((H // 4, W // 4, 3), np.float32)
    cols = (SODIUM, np.array([0.95, 0.80, 0.35], np.float32), np.array([0.25, 0.25, 0.95], np.float32))
    for x, y, r, c, b in _BK["p"]:
        spd = round((1.2 + r * 0.03) * E.DUR_F / (W + 400)) * (W + 400) / E.DUR_F       # whole wraps per loop -> seamless
        xx = (x - f * spd) % (W + 400) - 200
        cv2.circle(lay, (int(xx / 4), int(y / 4)), max(2, int(r / 4)), tuple(float(v) * b for v in cols[c]), -1, cv2.LINE_AA)
    lay = cv2.GaussianBlur(lay, (0, 0), 4.0)
    g = np.linspace(0.0, 1.0, H // 4, dtype=np.float32)[:, None, None]
    base = INDIGO * 0.22 * (1 - g) + np.array([0.04, 0.03, 0.03], np.float32) * g
    return cv2.resize(np.clip(base + lay * 0.45, 0, 1), (W, H), interpolation=cv2.INTER_LINEAR)

MIR = (110, 430, 970, 760)          # rear-view mirror rect in the composition (x0, y0, x1, y1)
def car_scene(f, light=1.0):
    """dark car interior at night: windshield with city bokeh + rain, the mirror's stem, dashboard glow at the bottom."""
    o = city_bokeh(f)
    o = rain_glass(o, f, 1.0, 0.45)
    for sg in (-1, 1):                                                                  # A-pillars
        xp = W / 2 + sg * (W * 0.62 - (_GY / H) * W * 0.18)
        pil = np.clip((sg * (_GX - xp)) / 6, 0, 1)[..., None]
        o = o * (1 - pil * 0.94) + pil * np.array([0.015, 0.015, 0.02], np.float32)
    o = sweeps(o, f, 0.7 * light, phase=0.10)
    dash = np.clip((_GY - 1560) / 360, 0, 1)[..., None]
    o = o * (1 - dash * 0.92) + dash * np.array([0.02, 0.02, 0.025], np.float32)
    glow = np.exp(-(((_GX - W * 0.30) / 260) ** 2 + ((_GY - 1640) / 50) ** 2))[..., None]
    o = o + glow * np.array([0.55, 0.45, 0.10], np.float32) * 0.35
    x0, y0, x1, y1 = MIR; cx = (x0 + x1) // 2
    cv2.rectangle(o, (cx - 22, 0), (cx + 22, y0 + 10), (0.03, 0.03, 0.035), -1, cv2.LINE_AA)       # stem
    return np.clip(o, 0, 1)

def rounded_mask(x0, y0, x1, y1, r):
    m = np.zeros((H, W), np.float32); r = int(max(1, min(r, (x1 - x0) / 2, (y1 - y0) / 2)))
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    cv2.rectangle(m, (x0 + r, y0), (x1 - r, y1), 1.0, -1); cv2.rectangle(m, (x0, y0 + r), (x1, y1 - r), 1.0, -1)
    for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)): cv2.circle(m, (cx, cy), r, 1.0, -1, cv2.LINE_AA)
    return cv2.GaussianBlur(m, (0, 0), 1.0)

def mirror_comp(content, f, u, lit=1.0):
    """u = 0: the rear-view mirror (content's eye line inside it) in the dark car; u = 1: the content full frame."""
    x0, y0, x1, y1 = MIR; e = u
    rx0 = x0 * (1 - e); ry0 = y0 * (1 - e); rx1 = x1 + (W - x1) * e; ry1 = y1 + (H - y1) * e
    rw, rh = rx1 - rx0, ry1 - ry0
    zc = rw / (x1 - x0); mcx, mcy = (x0 + x1) / 2, (y0 + y1) / 2
    car = car_scene(f, lit)
    if e > 0.001:
        M = cv2.getRotationMatrix2D((mcx, mcy), 0, zc); M[0, 2] += (rx0 + rx1) / 2 - mcx; M[1, 2] += (ry0 + ry1) / 2 - mcy
        car = cv2.warpAffine(car, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    sc = max(rw / W, 0.001); ey = H * 0.40                                              # content scale; eye line at 40% height
    cs = rw / W * (1 - e) * 1.55 + e * 1.0 if e < 1 else 1.0
    cs = max(cs, rw / W)
    Mc = np.float32([[cs, 0, (rx0 + rx1) / 2 - cs * W / 2], [0, cs, (ry0 + ry1) / 2 - cs * ey * (1 - e) - cs * (H / 2) * e + 0 * sc]])
    con = cv2.warpAffine(content, Mc, (W, H), borderMode=cv2.BORDER_REFLECT)
    con = con * (0.25 + 0.75 * lit)
    mm = rounded_mask(rx0, ry0, rx1, ry1, 60 * (1 - e) + 2)[..., None]
    o = car * (1 - mm) + con * mm
    if e < 0.98:                                                                          # bezel + glass reflection
        bz = np.clip(cv2.morphologyEx((mm[..., 0] > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((9, 9), np.uint8)).astype(np.float32), 0, 1)
        o = o * (1 - bz[..., None] * 0.85) + bz[..., None] * np.array([0.06, 0.06, 0.07], np.float32)
        refl = np.clip(1 - np.abs((_GX - rx0) / max(rw, 1) - (_GY - ry0) / max(rh, 1) * 0.6 - 0.15) / 0.08, 0, 1)[..., None] * mm * 0.10 * (1 - e)
        o = o + refl
    return np.clip(o, 0, 1)

def mirror_in(img, f, k, n=60):
    lit = clamp((k - 4) / 10, 0.15, 1.0)                                               # a streetlight comes up on the mirror
    if k >= n: return img
    u = ein(clamp((k - 22) / (n - 22), 0, 1), 2.4)
    o = mirror_comp(img, f, u, lit)
    if 22 <= k < n: o = radial_blur(o, W / 2, (MIR[1] + MIR[3]) / 2, 1.0, 1.0 + 0.05 * math.sin(math.pi * u), 4)
    return o

def mirror_out(img, f, s, n=22):
    j = f - s["f1"]
    if j < -n: return img
    u = 1 - eout(clamp((j + n) / (n - 4), 0, 1), 2.2)                                   # pull back into the mirror
    lit = clamp((-j - 1) / 8, 0.15, 1.0)                                               # the light leaves the mirror
    o = mirror_comp(img, f, u, lit)
    return o

# ---- transitions -------------------------------------------------------------------------------
def light_sweep(A, B, j, f, sa, sb, n=7):
    u = clamp((j + n + 0.5) / (2 * n), 0, 1); pos = -0.45 + 1.9 * ein(u, 1.2)
    xs = (_GX / W) * 0.55 + (_GY / H) * 0.85
    side = np.clip((pos - xs) / 0.05, 0, 1)[..., None]
    band = np.exp(-((xs - pos) / 0.11) ** 2)[..., None]
    o = A * (1 - side) + B * side
    return np.clip(o * (1 + 1.6 * band) + band * (SODIUM * 0.55 + WARMW * 0.25), 0, 1)

_WP = {}
def wiper(A, B, j, f, sa, sb, pre=8, post=10):
    u = clamp((j + pre + 0.5) / (pre + post), 0, 1); piv = (W * 0.10, H * 1.02); L = 2300
    ang = math.radians(-178 + 176 * ein(u, 1.5))
    a = np.degrees(np.arctan2(_GY - piv[1], _GX - piv[0]))
    swept = (a <= math.degrees(ang)).astype(np.float32)
    Ar = rain_glass(A, f, 1.0, 0.25)
    o = B * swept[..., None] + Ar * (1 - swept[..., None])                              # behind the blade: cleared, next shot
    d = np.abs(np.radians(a) - ang) * np.sqrt((_GX - piv[0]) ** 2 + (_GY - piv[1]) ** 2)
    blade = (np.exp(-(d / 9) ** 2) * (np.sqrt((_GX - piv[0]) ** 2 + (_GY - piv[1]) ** 2) < L))[..., None]
    spray = np.exp(-((d - 22) / 12) ** 2)[..., None] * (1 - swept[..., None]) * 0.5
    o = o * (1 - blade * 0.95) + blade * np.array([0.03, 0.03, 0.035], np.float32)
    o = o + np.exp(-((d - 8) / 2.5) ** 2)[..., None] * 0.25 + spray * WARMW * 0.25
    return np.clip(o, 0, 1)

def headlights(A, B, j, f, sa, sb, pre=12, post=14):
    if j < 0:
        u = (j + pre) / pre; base = A * (1 - 0.6 * u)
        cx, cy = W / 2, H * 0.47; sep = 140 + 520 * ein(u, 2.2); r = 16 + 150 * ein(u, 2.6)
    else:
        v = (j + 1) / post; base = B; cx, cy = W / 2, H * 0.47; sep = 400 + 600 * v; r = 126 * (1 - eout(v, 2)) + 1
    lay = np.zeros((H, W), np.float32)
    for sg in (-1, 1): cv2.circle(lay, (int(cx + sg * sep / 2), int(cy)), int(r), 1.0, -1, cv2.LINE_AA)
    core = cv2.GaussianBlur(lay, (0, 0), 3); glow = cv2.GaussianBlur(cv2.resize(lay, (W // 4, H // 4)), (0, 0), 10)
    glow = cv2.resize(glow, (W, H)) * 2.5
    streak = cv2.GaussianBlur(cv2.resize(lay, (W // 8, H // 8)), (0, 0), sigmaX=40, sigmaY=0.6); streak = cv2.resize(streak, (W, H)) * 2.2
    k_ = (ein((j + pre) / pre, 2) if j < 0 else (1 - eout((j + 1) / post, 1.6)))
    o = base + (core[..., None] * WARMW + glow[..., None] * WARMW * 0.6 + streak[..., None] * np.array([1.0, 0.85, 0.55], np.float32)) * (0.4 + 0.6 * k_)
    wash = 0.60 * math.exp(-((j + 0.5) / 1.3) ** 2)
    return np.clip(o * (1 - wash) + WARMW * wash, 0, 1)

def whip(A, B, j, f, sa, sb, pre=5, post=6, vertical=False):
    u = clamp((j + pre + 0.5) / (pre + post), 0, 1); s_ = 1 if not vertical else 1
    if j < 0: img, off = A, -ein((j + pre + 1) / (pre + 1), 2.2) * (H if vertical else W) * 0.9
    else: img, off = B, (1 - eout((j + 1) / post, 2.2)) * (H if vertical else W) * 0.9
    M = np.float32([[1, 0, 0 if vertical else off], [0, 1, off if vertical else 0]])
    o = cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    sp = abs(math.sin(math.pi * u)); o = hblur(o, 6 + 260 * sp, vertical=vertical)
    return np.clip(o * (1 + 0.15 * sp), 0, 1)

def whip_up(A, B, j, f, sa, sb): return whip(A, B, j, f, sa, sb, 5, 7, vertical=True)

_LL = {}
def light_leak(A, B, j, f, sa, sb, pre=8, post=10):
    if "n" not in _LL:
        rng = np.random.default_rng(55); acc = np.zeros((H // 8, W // 8), np.float32)
        for oc, amp in ((3, 1.0), (7, 0.5), (16, 0.25)):
            acc += cv2.resize(rng.random((oc * 16 // 9 + 1, oc)).astype(np.float32), (W // 8, H // 8), interpolation=cv2.INTER_CUBIC) * amp
        acc = (acc - acc.min()) / (acc.max() - acc.min()); _LL["n"] = cv2.resize(acc, (W, H), interpolation=cv2.INTER_CUBIC)
    u = clamp((j + pre + 0.5) / (pre + post), 0, 1); amt = math.sin(math.pi * u) ** 1.3
    edge = np.clip(1 - (_GX / W), 0, 1) * 0.6 + _LL["n"] * 0.7
    m = np.clip((edge - (1.25 - 0.80 * amt)) / 0.30, 0, 1)[..., None] * 0.8
    base = A if j < 0 else B
    col = SODIUM * 0.9 + np.array([0.0, -0.10, 0.0], np.float32) * (1 - _LL["n"][..., None]) + BLOODR * 0.25 * _LL["n"][..., None]
    return np.clip(base * (1 + 0.7 * m) + m * col * 0.55 * amt, 0, 1)

def wrap(A, B, j, f, sa, sb, pre=6, post=10):
    spec, fold = plastic_tex()
    u = clamp((j + pre + 0.5) / (pre + post), 0, 1); x = W * (1.15 - 2.3 * eout(u, 1.6))       # sheet sweeps right -> left
    base = A if j < 0 else B
    cover = np.clip((_GX - (x - W * 0.55)) / 40, 0, 1) * np.clip(((x + W * 0.55) - _GX) / 40, 0, 1)
    cover = cv2.warpAffine(cover.astype(np.float32), np.float32([[1, 0.08, 0], [0, 1, 0]]), (W, H), borderValue=0)[..., None]
    sh = np.roll(spec, int(x), 1)[..., None]
    milky = cv2.GaussianBlur(base, (0, 0), 6) * 0.68 + 0.10 + sh * (WARMW * 0.30)
    return np.clip(base * (1 - cover) + milky * cover, 0, 1)

def impact(A, B, j, f, sa, sb, pre=3, post=7):
    if j < 0: return np.clip(zoom_about(A, W / 2, H * 0.45, 1 + 0.04 * (j + pre + 1)), 0, 1)
    if j < 2:                                                                          # impact frame: high-contrast negative cut-out
        L = lum8(B); neg = np.clip((1 - L) ** 1.6, 0, 1)[..., None]
        return np.clip(neg * WARMW * 0.95 + (L > 0.55)[..., None] * BLOODR, 0, 1)
    v = (j - 1) / (post - 1); z = 1 + 0.09 * (1 - eout(v, 2.5))
    return np.clip(rgb_split(zoom_about(B, W / 2, H * 0.45, z), 10 * (1 - v)), 0, 1)

def rainfocus(A, B, j, f, sa, sb, pre=8, post=16):
    if j < 0:
        u = (j + pre + 1) / pre; return rain_glass(A, f, 1.0, ein(u, 1.4))
    v = (j + 1) / post; return rain_glass(B, f, 1.0, 1 - eout(v, 2.0))

def slam(A, B, j, f, sa, sb, post=5):
    i = SHOTS.index(sb); sg = 1 if i % 2 else -1
    v = (j + 1) / post; z = 1 + 0.07 * (1 - eout(v, 3)); rot = sg * 1.6 * (1 - eout(v, 3))
    o = zoom_about(B, W / 2 + sg * 20 * (1 - v), H * 0.45, z, rot)
    o = rgb_split(o, 8 * (1 - v))
    return np.clip(o * (1 + 0.35 * (1 - v) ** 3), 0, 1)

# ---- blood in water (the drop): the drop falls through the dark with Dexter refracted inside it ...
DROP_X, DROP_Y = W / 2, H * 0.60
def drop_fall(out, f, s):
    k = f - s["f0"]; n = s["f1"] - s["f0"]; u = k / max(1, n)
    fade = clamp(k / 18, 0, 1)
    base = out * (1 - 0.80 * fade)
    if k < 1: return base
    y = -160 + (DROP_Y + 160) * ein(clamp(u, 0, 1), 2.4); r = 70 + 30 * ein(u, 2); st = 1 + 0.45 * ein(u, 3)
    o = base.copy(); x0 = DROP_X
    yy, xx = _GY - y, _GX - x0
    # teardrop: circle below, tapering tail above
    dn = np.sqrt((xx / r) ** 2 + (yy / r) ** 2)
    tl = r * 1.25 * st
    tail = (yy < 0) & (yy > -tl - r * 0.2) & (np.abs(xx) < r * np.clip((yy + tl) / tl, 0, 1) ** 1.35 * np.clip(-yy / r, 0, 1) ** 0 )
    inside = ((dn < 1) | tail).astype(np.float32)
    inside = cv2.GaussianBlur(inside, (0, 0), 1.0)
    nxm = np.clip(xx / r, -1, 1); nym = np.clip(yy / r, -1, 1)
    src_img = out                                                                       # the scene (Dexter) refracted, upside down
    mx = (W / 2 - nxm * 520).astype(np.float32); my = (H * 0.38 - nym * 640).astype(np.float32)
    ref = cv2.remap(src_img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    tint = np.array([0.10, 0.08, 0.80], np.float32)
    body = ref * np.array([0.45, 0.42, 1.05], np.float32) * 0.95 + tint * 0.12
    edge = np.clip(dn - 0.75, 0, 1)[..., None] * 0.6
    o = o * (1 - inside[..., None]) + (body * (1 - edge) + BLOODR * 0.3 * edge) * inside[..., None]
    hi = np.exp(-(((xx + r * 0.35) / (r * 0.18)) ** 2 + ((yy + r * 0.40) / (r * 0.28)) ** 2))[..., None]
    o = o + hi * WARMW * 0.85 * inside[..., None]
    rim = np.exp(-((dn - 1) / 0.06) ** 2)[..., None] * (yy > 0)[..., None] * 0.35
    o = o + rim * np.array([0.2, 0.2, 0.9], np.float32)
    if u > 0.55:                                                                        # the dark water surface it will hit
        sv = clamp((u - 0.55) / 0.45, 0, 1); surf = np.exp(-((_GY - DROP_Y - r) / 5) ** 2)[..., None] * np.exp(-((_GX - x0) / 420) ** 2)[..., None]
        o = o + surf * WARMW * 0.10 * sv
    return np.clip(o, 0, 1)

# ... it hits the water on the drop: crown splash, rings, and blood blooming through the water reveals the next shot
_BW = {}
def bloom(A, B, j, f, sa, sb, post=26):
    if "w" not in _BW:
        rng = np.random.default_rng(7); W4, H4 = W // 4, H // 4
        def fbm(seed):
            r = np.random.default_rng(seed); acc = np.zeros((H4, W4), np.float32)
            for oc, amp in ((4, 1.0), (9, 0.5), (20, 0.25), (44, 0.12)):
                acc += cv2.resize(r.random((oc * 16 // 9 + 1, oc)).astype(np.float32), (W4, H4), interpolation=cv2.INTER_CUBIC) * amp
            return (acc - acc.min()) / (acc.max() - acc.min())
        _BW.update(w=fbm(1), wx=fbm(2) - 0.5, wy=fbm(3) - 0.5, d=[(rng.uniform(0, 6.283), rng.uniform(380, 900), rng.uniform(5, 13)) for _ in range(34)])
    v = (j + 1) / post; W4, H4 = W // 4, H // 4
    gy, gx = np.mgrid[0:H4, 0:W4].astype(np.float32); cx, cy = DROP_X / 4, DROP_Y / 4
    wx = gx + _BW["wx"] * 60 * (0.3 + v); wy = gy + _BW["wy"] * 60 * (0.3 + v)
    rr = np.sqrt((wx - cx) ** 2 + ((wy - cy) * 1.15) ** 2) / (W4 * 0.9)
    R = 0.08 + 1.25 * eout(clamp(v / 0.42, 0, 1), 2.2)                                   # the cloud spreads ...
    dens = np.clip((R - rr) / 0.18 + (_BW["w"] - 0.5) * 1.2, 0, 1)
    clear = smooth(clamp((v - 0.38) / 0.62, 0, 1))                                      # ... then thins and clears
    dens = dens * (1 - clear) ** 1.3 * np.clip(0.55 + _BW["w"] * 0.9, 0, 1.2)
    dens = cv2.resize(dens, (W, H), interpolation=cv2.INTER_CUBIC)[..., None]
    Bw = barrel(B, 0.10 * (1 - v), W / 2, H * 0.5, 900)
    Bw = cv2.remap(Bw, (_GX + np.sin(_GY / 40 + v * 9) * 6 * (1 - v)).astype(np.float32), _GY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    under = Bw * (1 - 0.55 * (1 - clear)) + np.array([0.08, 0.05, 0.28], np.float32) * 0.4 * (1 - clear)
    deep = np.array([0.02, 0.015, 0.26], np.float32); light = np.array([0.05, 0.04, 0.55], np.float32)
    dye = light * np.clip(dens * 1.4, 0, 1) * (1 - np.clip(dens - 0.6, 0, 1) * 1.5) + deep * np.clip(dens - 0.55, 0, 1) * 2.2
    a_ = np.clip(dens * 1.15, 0, 0.94)
    o = under * (1 - a_) + dye * a_ / np.maximum(a_, 1e-3) * a_
    rr_full = np.sqrt((_GX - DROP_X) ** 2 + ((_GY - DROP_Y) * 2.2) ** 2)
    for kk, sp in ((0, 900), (1, 650)):
        rad = sp * (v - kk * 0.08)
        if rad > 0: o = o + np.exp(-((rr_full - rad) / 10) ** 2)[..., None] * WARMW * 0.25 * (1 - v)
    tt = (j + 1) / FPS                                                                  # crown splash droplets
    for ang, sp, rad in _BW["d"]:
        x = DROP_X + sp * tt * math.cos(ang); y = DROP_Y - abs(sp * tt * math.sin(ang)) * 1.4 + 2600 * tt * tt
        if tt < 0.35 and 0 < x < W and 0 < y < H:
            cv2.circle(o, (int(x), int(y)), int(rad * (1 - tt / 0.4)), (0.05, 0.04, 0.60), -1, cv2.LINE_AA)
    flash = math.exp(-((j + 0.5) / 1.4) ** 2) * 0.35
    return np.clip(o + flash * WARMW * 0.5, 0, 1)

TR2.update({"light_sweep": (light_sweep, 7, 7), "wiper": (wiper, 8, 10), "headlights": (headlights, 12, 14), "whip": (whip, 5, 6),
            "whip_up": (whip_up, 5, 7), "light_leak": (light_leak, 8, 10), "wrap": (wrap, 6, 10), "impact": (impact, 3, 7),
            "rainfocus": (rainfocus, 8, 16), "slam": (slam, 0, 5), "bloom": (bloom, 0, 26)})

def lamp_on(A, B, j, f, sa, sb, pre=6, post=16):
    """a warm lamp clicks on: the frame drops to black, then a pool of light (with a filament flicker) blooms around his face."""
    if j < 0: return np.clip(A * (1 - ein((j + pre + 1) / pre, 1.5)), 0, 1)
    v = (j + 1) / post; fs = face_scr(sb, f); cx, cy = (fs[0], fs[1]) if fs else (W / 2, H * 0.37)
    flick = [0.0, 0.55, 0.15, 0.7, 0.45, 0.9][j] if j < 6 else 1.0
    R = 300 + 1500 * eout(v, 2.2)
    pool = np.exp(-(((_GX - cx) ** 2 + (_GY - cy) ** 2) / (R * R)))[..., None]
    o = B * np.clip(pool * 1.25, 0, 1) * flick + B * smooth((v - 0.55) / 0.45) * (1 - pool)
    return np.clip(o + pool * SODIUM * 0.10 * flick * (1 - v), 0, 1)
TR2["lamp_on"] = (lamp_on, 6, 16)

# ---- the "Darling," freeze composition: the world drains to indigo, Dexter stays lit (cutout + warm rim light)
def freeze_comp(out, person, f, s):
    t = f / FPS; t0 = s.get("freeze")
    if t0 is None or t < t0 - 0.05 or person is None: return out
    k = (t - t0) * FPS; e = eout(clamp(k / 10, 0, 1), 2)
    L = lum8(out)[..., None]; bg = (L * 0.55 + INDIGO * 0.55) * (1 - 0.35 * e) + out * 0.15
    p = np.clip(person * 1.1, 0, 1)[..., None]
    o = out * (1 - e) + (bg * (1 - p) + out * p) * e
    rim = np.clip(cv2.morphologyEx((person > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((7, 7), np.uint8)).astype(np.float32), 0, 1)
    rim = cv2.GaussianBlur(rim, (0, 0), 6)[..., None] * (_GX < W * 0.62)[..., None]
    o = o + rim * SODIUM * 0.55 * e
    fl = math.exp(-((k - 1) / 3) ** 2) * 0.35                                           # the freeze "click" of light
    return np.clip(o + fl * WARMW, 0, 1)

# ---- type ----------------------------------------------------------------------------------------
_TY = {}
def word_l(word, font_p, size, col, track=0, shadow=0.75, glow=None):
    key = (word, font_p, size, tuple(np.round(col, 3)), track, shadow, glow is None)
    if key in _TY: return _TY[key]
    m = text_mask(word, font_p, size, tracking=track); pad = 30; mm = np.pad(m, pad); hh, ww = mm.shape
    L = np.zeros((hh, ww, 4), np.float32); sh = cv2.GaussianBlur(mm, (0, 0), 10) * shadow
    L[..., :3] = col * mm[..., None]; L[..., 3] = np.maximum(mm, sh)
    L[..., :3] = L[..., :3] * (mm[..., None] / np.maximum(L[..., 3:4], 1e-4))
    if glow is not None:
        g = cv2.GaussianBlur(mm, (0, 0), 14) * 0.55; L[..., :3] = L[..., :3] + glow * g[..., None] * (1 - mm[..., None]); L[..., 3] = np.maximum(L[..., 3], g)
    _TY[key] = L; return L

def ease_word(out, L, x, y, v, a=1.0, rise=26):
    if v <= 0.001: return out
    Lb = L if v >= 1 else cv2.GaussianBlur(L, (0, 0), 0.1 + 6 * (1 - v))
    return paste(out, Lb, int(x - Lb.shape[1] / 2), int(y + rise * (1 - v) - Lb.shape[0] / 2), v * a)

def lyric_line(out, f, words, y, emph, t_out, quick=False):
    t = f / FPS; imgs = []
    for w, wt in words:
        if w in emph: imgs.append(word_l(w, F_SERIF_BI, 104, SODIUM * 0.95 + WARMW * 0.05, 0, 0.8, SODIUM))
        else: imgs.append(word_l(w, F_WIDE, 66, WARMW * 0.97, 9, 0.85))
    sp = 34; vs = [eout(((t - wt) * FPS + 1) / 11, 3) for _, wt in words]
    total = sum((im.shape[1] - 60 + sp) * v for im, v in zip(imgs, vs))
    x = W / 2 - total / 2; fade = 1.0 if t < t_out else clamp(1 - (t - t_out) * FPS / (3 if quick else 8), 0, 1)
    for im, v in zip(imgs, vs):
        wd = im.shape[1] - 60
        out = ease_word(out, im, x + wd / 2, y, v, fade)
        x += (wd + sp) * v
    return out

def behind_text(out, f, s, tx, person):
    """big words behind Dexter (his cutout is composited back over them), anchored to his head and drifting with it."""
    t = f / FPS; ws = tx["words"]; t_out = tx["end"]
    if not (ws[0][1] - 0.05 <= t < t_out + 0.2) or person is None: return out
    fs = face_scr(s, f); fx, fy = (fs[0], fs[1]) if fs else (W / 2, H * 0.37)
    lay = out.copy(); fade = 1.0 if t < t_out else clamp(1 - (t - t_out) * FPS / 8, 0, 1)
    if len(ws) == 1:
        w, wt, _ = ws[0]; L = word_l(w, F_SERIF_BI, 330, BLOODR * 0.9 + WARMW * 0.1, 0, 0.0, BLOODR)
        v = eout(((t - wt) * FPS + 1) / 14, 3); sc = 1 + 0.25 * (1 - v)
        Ls = cv2.resize(L, (int(L.shape[1] * sc), int(L.shape[0] * sc)))
        lay = ease_word(lay, Ls, W / 2 + (fx - W / 2) * 0.25, fy - 40, v, fade, rise=60)
    else:
        imgs = [word_l(w, F_HEAVY, 210 if w not in tx["emph"] else 250, (BLOODR * 0.9 + WARMW * 0.1) if w in tx["emph"] else WARMW * 0.95, 4, 0.0) for w, _, _ in ws]
        side = 1 if fx < W / 2 else -1                                                   # stack on the open side, tucked behind his head
        ys = [fy - 200 + 205 * i for i in range(len(ws))]
        for (w, wt, _), im, yy in zip(ws, imgs, ys):
            v = eout(((t - wt) * FPS + 1) / 12, 3); hw = (im.shape[1] - 60) / 2
            xc = clamp(W / 2 + side * W * 0.21, hw + 40, W - hw - 40)
            lay = ease_word(lay, im, xc, yy, v, fade, rise=40)
    p = np.clip(person * 1.15, 0, 1)[..., None]
    return lay * (1 - p) + out * p

def script_text(out, f, tx):
    """serif-italic write-on: a warm pen nib draws the words left to right."""
    t = f / FPS; (w, wt, _) = tx["words"][0]; t_out = tx["end"]
    if not (wt - 0.05 <= t < t_out + 0.25): return out
    big = w.startswith("Darling"); size = 150 if big else 108; col = (BLOODR * 0.85 + WARMW * 0.15) if big else WARMW * 0.96
    key = ("scr", w);
    if key not in _TY:
        m = text_mask(w, F_SERIF_I if not big else F_SERIF_BI, size, tracking=2); pad = 34; mm = np.pad(m, pad)
        _TY[key] = mm
    mm = _TY[key]; hh, ww = mm.shape
    dur = 0.55 if big else 0.75; p = clamp((t - wt) / dur, 0, 1); px = ww * (0.06 + 0.94 * eout(p, 1.4))
    rev = np.clip((px - np.arange(ww)[None, :]) / 26, 0, 1)
    vis = mm * rev; fade = 1.0 if t < t_out else clamp(1 - (t - t_out) * FPS / 12, 0, 1)
    L = np.zeros((hh, ww, 4), np.float32); sh = cv2.GaussianBlur(vis, (0, 0), 9) * 0.8
    L[..., :3] = col * vis[..., None]; L[..., 3] = np.maximum(vis, sh)
    L[..., :3] = L[..., :3] * (vis[..., None] / np.maximum(L[..., 3:4], 1e-4))
    if big:
        g = cv2.GaussianBlur(vis, (0, 0), 16) * 0.6; L[..., :3] += BLOODR * g[..., None] * (1 - vis[..., None]); L[..., 3] = np.maximum(L[..., 3], g)
    y = (tx.get("band", (1300, 1560))[0] + tx.get("band", (1300, 1560))[1]) / 2
    x0 = int(W / 2 - ww / 2); y0 = int(y - hh / 2 + 10 * (1 - eout(p, 2)))
    band = np.exp(-((_GY - y) / (hh * 0.9)) ** 2)[..., None] * 0.55 * fade * eout(clamp((t - wt) / 0.25, 0, 1), 2)
    out = out * (1 - band)                                                              # soft dark band keeps the script readable
    out = paste(out, L, x0, y0, fade)
    if p < 1:                                                                           # the pen nib
        cols = np.nonzero(mm[:, int(min(ww - 1, px))] > 0.3)[0]
        if len(cols):
            ny = y0 + int(cols.mean()); nx = x0 + int(px)
            nib = np.exp(-(((_GX - nx) / 10) ** 2 + ((_GY - ny) / 10) ** 2))[..., None]
            out = np.clip(out + nib * WARMW * 0.9 + cv2.GaussianBlur(nib[..., 0], (0, 0), 14)[..., None] * SODIUM * 0.6, 0, 1)
    return out

def hook_text(out, f, tx):
    """I DON'T / WISH YOU WELL — each word slams in on its syllable and stays across the cuts."""
    t = f / FPS; t_out = tx["end"]
    if not (tx["words"][0][1] - 0.03 <= t < t_out + 0.1): return out
    fade = 1.0 if t < t_out else clamp(1 - (t - t_out) * FPS / 5, 0, 1)
    for ln, y in ((0, 1320), (1, 1475)):
        row = [(w, wt) for w, wt, l in tx["words"] if l == ln]
        imgs = [word_l(w, F_SERIF_BI, 230, BLOODR * 0.92 + WARMW * 0.08, 0, 0.9, BLOODR) if w in tx["emph"] else word_l(w, F_HEAVY, 92, WARMW * 0.97, 5, 0.9) for w, _ in row]
        gap = 30; total = sum(im.shape[1] - 60 for im in imgs) + gap * (len(imgs) - 1); x = W / 2 - total / 2
        for (w, wt), im in zip(row, imgs):
            wd = im.shape[1] - 60; k = (t - wt) * FPS
            if k >= -1:
                v = eout((k + 1) / 5, 3); sc = 1 + 0.45 * (1 - v)
                Ls = im if sc <= 1.001 else cv2.resize(im, (int(im.shape[1] * sc), int(im.shape[0] * sc)))
                if v < 1: Ls = cv2.GaussianBlur(Ls, (0, 0), 0.1 + 4 * (1 - v))
                out = paste(out, Ls, int(x + wd / 2 - Ls.shape[1] / 2), int(y - Ls.shape[0] / 2), clamp(v * 1.4, 0, 1) * fade)
            x += wd + gap
    return out

def text8(out, f, s, person):
    for tx in E.TEXT:
        st_ = tx["style"]
        if st_ == "lyric":
            t = f / FPS; ws = tx["words"]
            if not (ws[0][1] - 0.05 <= t < tx["end"] + 0.2): continue
            lines = sorted({l for _, _, l in ws}); ys = (1385, 1490) if len(lines) > 1 else (1440,)
            for ln, y in zip(lines, ys):
                out = lyric_line(out, f, [(w, wt) for w, wt, l in ws if l == ln], y, tx["emph"], tx["end"], tx.get("quick_out", False))
        elif st_ == "script":
            if s.get("dropfall") and tx["words"][0][0].startswith("Darling"): continue
            out = script_text(out, f, tx)
        elif st_ == "hook": out = hook_text(out, f, tx)
    return out

# ---- finish: warm halation, soft anamorphic, grain, gentle vignette (no crushed blacks)
def finish8(out, f):
    small = cv2.resize(out, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi = np.clip(small.max(2) - 0.58, 0, 1)
    hal = cv2.resize(cv2.GaussianBlur(hi, (0, 0), 7), (W, H))[..., None]
    out = out + hal * (SODIUM * 0.40 + BLOODR * 0.12)
    out = anamorphic(out, 0.16)
    out = np.maximum(out, 0.018 + out * 0.0)                                            # keep a floor in the blacks
    return np.clip(out * (0.82 + 0.18 * VIG) + grain(f, 0.016), 0, 1)

def shot_first(S_):
    if S_.get("graphic") == "knife_roll": return knife_roll_scene(S_["f0"], S_)
    return render_shot(S_, S_["f0"], False)

def last_visible(P):
    fr = P["f1"] - 1
    if P.get("graphic") == "knife_roll": return knife_roll_scene(fr, P)
    if P.get("dropfall"):
        img = render_shot(P, fr); return drop_fall(img, fr, P)
    return last_frame_of(P)


# ============================================================================ v8 rev 2 — the kill kit, the knife pass, richer type
STEEL = np.array([0.62, 0.60, 0.58], np.float32)
LEATHER = np.array([0.06, 0.11, 0.21], np.float32)
_KS = {}
def knife_sprite(kind):
    """RGBA + blade mask of one knife, vertical, tip up (canvas 200 x 1000; blade y 40..620, handle 620..980)."""
    if kind in _KS: return _KS[kind]
    Wk, Hk = 200, 1000; cx = 100
    spec = {"chef": (124, 40, 1.6), "boning": (62, 120, 1.25), "cleaver": (156, 150, 6.0), "slicer": (84, 30, 2.2), "paring": (74, 300, 1.4)}[kind]
    bw, y_tip, sh = spec
    yb = 620; ts = np.linspace(0, 1, 160)
    ys = y_tip + (yb - y_tip) * ts
    xl = cx - bw / 2 + 0.15 * bw * (1 - ts) ** 2.0
    xr = cx + bw / 2 - 0.85 * bw * (1 - ts) ** sh
    if kind == "cleaver": xl = np.full_like(ts, cx - bw / 2); xr = np.full_like(ts, cx + bw / 2); ys[0] = y_tip
    poly = np.int32(np.vstack([np.stack([xl, ys], 1), np.stack([xr[::-1], ys[::-1]], 1)]))
    bm = np.zeros((Hk, Wk), np.float32); cv2.fillPoly(bm, [poly], 1.0, cv2.LINE_AA)
    yy, xx = np.mgrid[0:Hk, 0:Wk].astype(np.float32)
    rng = np.random.default_rng(len(kind) * 31)
    brushed = cv2.GaussianBlur(rng.random((Hk, Wk)).astype(np.float32), (0, 0), sigmaX=0.6, sigmaY=14)
    xr_y = np.interp(yy[:, 0], ys, xr)[:, None]; xl_y = np.interp(yy[:, 0], ys, xl)[:, None]
    rel = np.clip((xx - xl_y) / np.maximum(xr_y - xl_y, 1), 0, 1)                    # 0 spine .. 1 edge
    shade = 0.55 + 0.35 * np.exp(-((rel - 0.38) / 0.28) ** 2) + 0.10 * (brushed - 0.5)
    bevel = np.clip((rel - 0.80) / 0.20, 0, 1)
    env = 0.75 + 0.35 * np.exp(-((yy - 260) / 120) ** 2) - 0.25 * np.exp(-((yy - 470) / 70) ** 2)   # sky/street reflection bands
    col = STEEL[None, None, :] * (shade * env)[..., None] + bevel[..., None] * 0.22 + np.array([0.06, 0.03, -0.01], np.float32) * (1 - rel)[..., None]
    edge = np.exp(-((xx - xr_y) / 1.6) ** 2) * (yy > y_tip) * (yy < yb)
    col = col + edge[..., None] * 0.45
    rgba = np.zeros((Hk, Wk, 4), np.float32)
    rgba[..., :3] = col * bm[..., None]; rgba[..., 3] = bm
    hw = int(bw * 0.38 + 10) if kind != "cleaver" else 30
    hm = np.zeros((Hk, Wk), np.float32); cv2.rectangle(hm, (cx - hw, 650), (cx + hw, 975), 1.0, -1); hm = cv2.GaussianBlur(hm, (0, 0), 2)
    hsh = 0.04 + 0.10 * np.exp(-((xx - (cx - hw * 0.3)) / (hw * 0.5)) ** 2)
    rgba[..., :3] = rgba[..., :3] * (1 - hm[..., None]) + np.dstack([hsh, hsh, hsh * 1.1]) * hm[..., None]
    rgba[..., 3] = np.maximum(rgba[..., 3], hm)
    bol = np.zeros((Hk, Wk), np.float32); cv2.rectangle(bol, (cx - hw - 4, 618), (cx + hw + 4, 652), 1.0, -1)
    rgba[..., :3] = rgba[..., :3] * (1 - bol[..., None]) + (STEEL * 0.95)[None, None, :] * bol[..., None]; rgba[..., 3] = np.maximum(rgba[..., 3], bol)
    for ry in (720, 820, 920):
        cv2.circle(rgba, (cx, ry), 8, (0.75, 0.74, 0.72, 1.0), -1, cv2.LINE_AA)
    _KS[kind] = (rgba, bm, (edge * bm).astype(np.float32)); return _KS[kind]

KIT = ["boning", "slicer", "chef", "paring", "cleaver"]
ROLL = (70, 430, 1010, 1470)
def _slot_x(i): return ROLL[0] + (ROLL[2] - ROLL[0]) * (i + 0.5) / 5

_KR = {}
def roll_textures():
    if "seat" not in _KR:
        rng = np.random.default_rng(5)
        weave = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 0.8)
        seat = np.array([0.07, 0.055, 0.05], np.float32) * (0.75 + 0.45 * weave[..., None])
        for y in (300, 1650): cv2.line(seat, (0, y), (W, y + 40), (0.03, 0.025, 0.025), 6, cv2.LINE_AA)
        x0, y0, x1, y1 = ROLL
        lea = LEATHER * (0.80 + 0.35 * cv2.resize(rng.random((60, 34)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)[..., None])
        lea = lea * (0.92 + 0.12 * cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 1.2)[..., None])
        m = np.zeros((H, W), np.float32); cv2.rectangle(m, (x0, y0), (x1, y1), 1.0, -1)
        dash = np.zeros((H, W), np.float32)
        for k in range(x0 + 26, x1 - 26, 22): cv2.line(dash, (k, y0 + 24), (k + 12, y0 + 24), 1.0, 2, cv2.LINE_AA); cv2.line(dash, (k, y1 - 24), (k + 12, y1 - 24), 1.0, 2, cv2.LINE_AA)
        for i in range(1, 5):
            xs = int(x0 + (x1 - x0) * i / 5)
            for k in range(y0 + 40, y1 - 40, 22): cv2.line(dash, (xs, k), (xs, k + 12), 1.0, 2, cv2.LINE_AA)
        lea = lea + dash[..., None] * np.array([0.35, 0.45, 0.55], np.float32) * 0.55
        _KR.update(seat=seat.astype(np.float32), lea=lea.astype(np.float32), m=m)
    return _KR["seat"], _KR["lea"], _KR["m"]

def knife_roll_scene(f, s):
    """the kill kit on the passenger seat: the roll unrolls, streetlights glint up the blades on each 'ooh'."""
    k = f - s["f0"]; seat, lea, m = roll_textures(); x0, y0, x1, y1 = ROLL
    X = x0 + (x1 - x0 + 120) * eout(clamp((k - 2) / 34, 0, 1), 2.2)                  # unroll front
    rev = np.clip((X - _GX) / 3, 0, 1) * m
    o = seat * (1 - rev[..., None]) + lea * rev[..., None]
    cut_f = s["f1"]; lift0 = cut_f - 28
    for i, kind in enumerate(KIT):
        if i == 2 and f >= lift0: continue                                              # the chef's knife is in his hand now
        sp = knife_sprite(kind)[0]; cx = _slot_x(i); top = y0 + 50
        M = np.float32([[1, 0, cx - 100], [0, 1, top - 40]])
        lay = cv2.warpAffine(sp, M, (W, H), borderValue=(0, 0, 0, 0)); a = lay[..., 3:4] * rev[..., None]
        sh = cv2.GaussianBlur(lay[..., 3], (0, 0), 7)[..., None] * rev[..., None] * 0.55
        o = o * (1 - np.roll(np.roll(sh, 12, 0), 10, 1)) * (1 - a) + lay[..., :3] * a
        strap = np.zeros((H, W), np.float32); cv2.rectangle(strap, (int(cx - 70), 1120), (int(cx + 70), 1175), 1.0, -1)
        strap = strap * rev
        o = o * (1 - strap[..., None]) + strap[..., None] * LEATHER * 1.25
    gt = [E.s2e(17.52), E.s2e(18.04), E.s2e(18.56)]                                     # "ooh" "ooh" "yeah"
    for gi, (tg, ki) in enumerate(zip(gt, (0, 4, 2))):
        kk = (f / FPS - tg) * FPS
        if not (0 <= kk < 16) or (ki == 2 and f >= lift0): continue
        bm0 = knife_sprite(KIT[ki])[1]; M = np.float32([[1, 0, _slot_x(ki) - 100], [0, 1, y0 + 10]])
        bm = cv2.warpAffine(bm0, M, (W, H), borderValue=0) * rev
        pos = 1450 - 1100 * eout(kk / 14, 2)
        band = np.exp(-(((_GY - pos) + (_GX - _slot_x(ki)) * 0.6) / 40) ** 2) * bm
        o = o + band[..., None] * WARMW * 0.85
        if kk < 10:
            ty = int(y0 + 50 + 30); tx_ = int(_slot_x(ki) - 30)
            star = np.zeros((H, W), np.float32); a_ = 1 - kk / 10
            cv2.line(star, (tx_ - 60, ty), (tx_ + 60, ty), 1.0, 2, cv2.LINE_AA); cv2.line(star, (tx_, ty - 60), (tx_, ty + 60), 1.0, 2, cv2.LINE_AA)
            o = o + cv2.GaussianBlur(star, (0, 0), 2)[..., None] * WARMW * a_ * 1.4
    if X < x1 + 100:                                                                    # the rolled-up leather, still unrolling
        cyl = np.exp(-((_GX - X) / 48) ** 2) * ((_GY > y0 - 10) & (_GY < y1 + 10))
        shade = 0.45 + 0.75 * np.clip(1 - np.abs(_GX - X + 14) / 48, 0, 1)
        o = o * (1 - cyl[..., None]) + LEATHER[None, None, :] * (shade * cyl)[..., None] * 1.3
        shadow = np.clip(1 - (_GX - X - 30) / 90, 0, 1) * (_GX > X + 20) * ((_GY > y0) & (_GY < y1))
        o = o * (1 - shadow[..., None] * 0.5)
    o = sweeps(o, f, 0.9, phase=0.05)
    if f >= lift0:                                                                      # depth of field as the knife comes up
        dv = smooth((f - lift0) / 20)
        o = o * (1 - 0.45 * dv) + cv2.GaussianBlur(o, (0, 0), 1 + 8 * dv) * 0.45 * dv
    return np.clip(o, 0, 1)

def knife_pose(j, pre=28, post=14):
    """the chef's knife: lifts out of the roll (j -28..-16), whips out of frame right (-16..-9), then swings back across the
    lens as a giant mirror blade, crossing centre on the beat (j = 0)."""
    if j < -16:
        u = smooth((j + 28) / 12); return _slot_x(2), 760 - 140 * u, 1.0 + 0.5 * u, -15 * u
    if j < -9:
        u = ein((j + 16) / 7, 2.2); return _slot_x(2) + (W * 1.55 - _slot_x(2)) * u, 620 + 120 * u, 1.5 + 1.2 * u, -15 - 27 * u
    u = clamp((j + 9) / (9 + post), 0, 1)
    x = np.interp(u, [0, 0.25, 0.40, 0.55, 1.0], [W * 1.55, W * 0.95, W * 0.50, W * 0.05, -W * 1.2])
    return x, 740 + 260 * u, 2.7 + 0.5 * u, -42 - 6 * u

def knife_pass(A, B, j, f, sa, sb, pre=28, post=14):
    sp, spb, spe = knife_sprite("chef"); samples = []
    for d in np.linspace(-0.45, 0.45, 9):                                               # motion blur: 9 sub-frame samples
        cx, cy, sc, ang = knife_pose(j + d, pre, post)
        M = cv2.getRotationMatrix2D((100, 330), ang, sc); M[0, 2] += cx - 100; M[1, 2] += cy - 330
        samples.append((M, np.dstack([cv2.warpAffine(sp, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0)),
                                      cv2.warpAffine(spb, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)])))
    lay = sum(s_[1] for s_ in samples) / len(samples); M = samples[4][0]
    cx, cy, sc, ang = knife_pose(j, pre, post)
    ax = M[:, :2] @ np.array([0.0, 1.0]); ax = ax / (np.linalg.norm(ax) + 1e-9); nrm = np.array([-ax[1], ax[0]])
    if nrm[0] < 0: nrm = -nrm                                                            # normal pointing right: the swept side
    pc = M @ np.array([100.0, 330.0, 1.0])
    d = (_GX - pc[0]) * nrm[0] + (_GY - pc[1]) * nrm[1]
    passed = np.clip((d - 60) / 20, 0, 1) * (1.0 if j >= -9 else 0.0)                 # behind the swinging blade
    o = A * (1 - passed[..., None]) + B * passed[..., None]
    bm = lay[..., 4:5]; al = lay[..., 3:4]
    refl = zoom_about(cv2.flip(B, -1), W / 2, H / 2, 1.5)                                # a polished blade: inverted, magnified reflection
    refl = cv2.GaussianBlur(refl, (0, 0), 1.8); Lr = lum8(refl)[..., None]
    refl = (Lr * 0.75 + refl * 0.25) * np.array([1.05, 1.0, 0.92], np.float32)          # steel-tinted
    bands = 0.5 + 0.5 * np.cos((_GX * 0.6 + _GY * 0.8) / 55.0 + j * 0.9)                # anisotropic polish streaks
    blade = lay[..., :3] * 0.55 + refl * 0.45 * bm + (bands[..., None] * 0.18 - 0.05) * bm
    knife_rgb = lay[..., :3] * (1 - bm) + blade * bm / np.maximum(al, 1e-3) * al
    shadow = cv2.GaussianBlur(al[..., 0], (0, 0), 30)[..., None] * 0.45
    o = o * (1 - np.roll(np.roll(shadow, 40, 0), 30, 1)) * (1 - al) + knife_rgb
    hit = math.exp(-((j + 0.3) / 2.2) ** 2)                                             # the beat: a glint runs down the edge
    if hit > 0.02:
        edge = np.clip(cv2.GaussianBlur(cv2.warpAffine(spe, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0), (0, 0), 1.2) * 3, 0, 1)   # the cutting edge only
        st = cv2.GaussianBlur(cv2.resize(edge, (W // 8, H // 8), interpolation=cv2.INTER_AREA), (0, 0), sigmaX=30, sigmaY=1.2); st = cv2.resize(st, (W, H)) * 9
        o = o + (edge[..., None] * WARMW + st[..., None] * (SODIUM * 0.6 + WARMW * 0.4)) * hit
    return np.clip(o, 0, 1)

TR2["knife_pass"] = (knife_pass, 28, 14)

# ---- richer type --------------------------------------------------------------------------------------
_LT = {}
def letter_set(word, fp, size, track):
    """per-letter masks on a shared baseline: (pen origins, masks, mask x-offsets of the origin, total advance)."""
    key = (word, fp, size, track)
    if key in _LT: return _LT[key]
    fnt = font(fp, size); asc, desc = fnt.getmetrics(); Hc = asc + desc + 24
    xs, ims, offs = [], [], []; x = 0.0
    for c in word:
        adv = fnt.getlength(c)
        if c == " ": x += adv + track; continue
        bx0, by0, bx1, by1 = fnt.getbbox(c); ox = 12 - min(0, bx0)
        im = Image.new("L", (int(max(bx1, adv) - min(0, bx0) + 24), Hc), 0); ImageDraw.Draw(im).text((ox, 12), c, font=fnt, fill=255)
        xs.append(x); ims.append(np.asarray(im).astype(np.float32) / 255); offs.append(ox); x += adv + track
    _LT[key] = (xs, ims, offs, x - track); return _LT[key]

def letters_paste(out, word, fp, size, track, col, cx, cy, k, t_from_end=None, stagger=1.3, glow=None, fill=None, rise=22, a_all=1.0):
    """draw a word letter by letter (shared baseline): each letter fades + rises + sharpens with a stagger; optional exit."""
    xs, ims, offs, wd = letter_set(word, fp, size, track); x0 = cx - wd / 2
    for i, (xo, m, ox) in enumerate(zip(xs, ims, offs)):
        v = eout((k - i * stagger + 1) / 10, 3)
        if v <= 0.001: continue
        ex = 1.0; dy = 0.0
        if t_from_end is not None and t_from_end > 0:
            e_ = clamp((t_from_end - i * 0.8) / 7, 0, 1); ex = 1 - e_; dy = -14 * e_
        if ex <= 0.001: continue
        mm = m if v >= 1 else cv2.GaussianBlur(m, (0, 0), 0.1 + 4.5 * (1 - v))
        pad = 24; mp = np.pad(mm, pad); hh, ww = mp.shape
        L = np.zeros((hh, ww, 4), np.float32)
        c = col if fill is None else fill(hh, ww)
        L[..., :3] = c * mp[..., None]
        sh = cv2.GaussianBlur(mp, (0, 0), 7) * 0.75; L[..., 3] = np.maximum(mp, sh)
        L[..., :3] = L[..., :3] * (mp[..., None] / np.maximum(L[..., 3:4], 1e-4))
        if glow is not None:
            g = cv2.GaussianBlur(mp, (0, 0), 12) * 0.5; L[..., :3] += glow * g[..., None] * (1 - mp[..., None]); L[..., 3] = np.maximum(L[..., 3], g)
        out = paste(out, L, int(x0 + xo - ox - pad), int(cy - hh / 2 + rise * (1 - v) + dy), v * ex * a_all)
    return out

def sodium_fill(hh, ww):
    y = np.linspace(0, 1, hh, dtype=np.float32)[:, None, None]
    return np.clip(SODIUM * (1.15 - 0.45 * y) + WARMW * 0.15 * (1 - y), 0, 1) * np.ones((1, ww, 1), np.float32)

def lyric_line(out, f, words, y, emph, t_out, quick=False):
    """each word letter by letter; emphasis words in sodium serif italic with a light sweep and an underline that draws."""
    t = f / FPS; sp = 34; specs = []
    for w, wt in words:
        if w in emph: specs.append((w, wt, F_SERIF_BI, 104, 1, True))
        else: specs.append((w, wt, F_WIDE, 66, 9, False))
    widths = [letter_set(w, fp, sz, tr)[3] for w, _, fp, sz, tr, _ in specs]
    vs = [eout(((t - wt) * FPS + 1) / 11, 3) for _, wt, _, _, _, _ in specs]
    total = sum((wd + sp) * v for wd, v in zip(widths, vs)) - sp * (vs[-1] if vs else 0)
    x = W / 2 - total / 2; tend = (t - t_out) * FPS
    for (w, wt, fp, sz, tr, em), wd, v in zip(specs, widths, vs):
        k = (t - wt) * FPS
        if k >= -1:
            te_ = tend * (2.5 if quick else 1.0) if tend > 0 else None
            if em:
                out = letters_paste(out, w, fp, sz, tr, None, x + wd / 2, y, k, te_, 1.6, SODIUM, sodium_fill)
                if 4 < k < 20:                                                          # light sweep across the word
                    sx = x - 40 + (wd + 80) * (k - 4) / 16; band = np.exp(-(((_GX - sx) + (_GY - y) * 0.3) / 18) ** 2) * (np.abs(_GY - y) < 55)
                    out = np.clip(out + band[..., None] * WARMW * 0.55, 0, 1)
                ul = wd * eout(clamp((k - 6) / 12, 0, 1), 3) * (1 if te_ is None else clamp(1 - te_ / 6, 0, 1))
                if ul > 2: cv2.line(out, (int(x), int(y + 50)), (int(x + ul), int(y + 50)), tuple(float(c) for c in SODIUM), 3, cv2.LINE_AA)
            else:
                out = letters_paste(out, w, fp, sz, tr, WARMW * 0.97, x + wd / 2, y, k, te_, 1.2)
        x += (wd + sp) * v
    return out

def behind_text(out, f, s, tx, person):
    """big words set behind Dexter's cutout: each slides out from behind his head to its place, extruded, with a light
    sweep when it lands; a single word (WANT) grows behind him with a red gradient."""
    t = f / FPS; ws = tx["words"]; t_out = tx["end"]
    if not (ws[0][1] - 0.05 <= t < t_out + 0.2) or person is None: return out
    fs = face_scr(s, f); fx, fy = (fs[0], fs[1]) if fs else (W / 2, H * 0.37)
    lay = out.copy(); fade = 1.0 if t < t_out else clamp(1 - (t - t_out) * FPS / 8, 0, 1)
    def extruded(L, depth=8, col=None):
        base = np.zeros_like(L); acc = np.zeros_like(L)
        for dd in range(depth, 0, -2):
            sh = np.roll(np.roll(L, dd, 0), dd, 1).copy(); sh[..., :3] = (col if col is not None else np.array([0.05, 0.03, 0.10], np.float32)) * (0.5 + 0.5 * (1 - dd / depth))
            acc = acc * (1 - sh[..., 3:4]) + sh * sh[..., 3:4]; acc[..., 3:4] = np.maximum(acc[..., 3:4], sh[..., 3:4])
        acc[..., :3] = acc[..., :3] * (1 - L[..., 3:4]) + L[..., :3] * L[..., 3:4]; acc[..., 3:4] = np.maximum(acc[..., 3:4], L[..., 3:4])
        return acc
    if len(ws) == 1:
        w, wt, _ = ws[0]; k = (t - wt) * FPS
        m = text_mask(w, F_SERIF_BI, 330); pad = 30; mm = np.pad(m, pad); hh, ww = mm.shape
        g = np.linspace(0, 1, hh, dtype=np.float32)[:, None, None]
        L = np.zeros((hh, ww, 4), np.float32); L[..., :3] = (BLOODR * (0.65 + 0.7 * (1 - g)) + WARMW * 0.08 * (1 - g)) * mm[..., None]; L[..., 3] = mm
        if 6 < k < 26:
            sx = (k - 6) / 20 * (ww + 200) - 100; L[..., :3] += np.exp(-((np.arange(ww)[None, :] - sx + np.arange(hh)[:, None] * 0.4) / 30) ** 2)[..., None] * mm[..., None] * 0.5
        L = extruded(L, 10, np.array([0.02, 0.01, 0.18], np.float32))
        v = eout((k + 1) / 14, 3); sc = 1 + 0.25 * (1 - v)
        Ls = cv2.resize(L, (int(L.shape[1] * sc), int(L.shape[0] * sc)))
        if v < 1: Ls = cv2.GaussianBlur(Ls, (0, 0), 0.1 + 5 * (1 - v))
        lay = paste(lay, Ls, int(W / 2 + (fx - W / 2) * 0.25 - Ls.shape[1] / 2), int(fy - 40 - Ls.shape[0] / 2 + 60 * (1 - v)), v * fade)
    else:
        side = 1 if fx < W / 2 else -1; ys = [fy - 200 + 205 * i for i in range(len(ws))]
        for (w, wt, _), yy in zip(ws, ys):
            k = (t - wt) * FPS
            if k < -1: continue
            em = w in tx["emph"]
            m = text_mask(w, F_HEAVY, 250 if em else 210, tracking=4); pad = 30; mm = np.pad(m, pad); hh, ww = mm.shape
            L = np.zeros((hh, ww, 4), np.float32); L[..., :3] = ((BLOODR * 0.95 + WARMW * 0.05) if em else WARMW * 0.95) * mm[..., None]; L[..., 3] = mm
            if 8 < k < 26:
                sx = (k - 8) / 18 * (ww + 200) - 100
                L[..., :3] += np.exp(-((np.arange(ww)[None, :] - sx + np.arange(hh)[:, None] * 0.4) / 26) ** 2)[..., None] * mm[..., None] * 0.6
            L = extruded(L, 9)
            v = eout((k + 1) / 13, 3); hw = (ww - 60) / 2
            xt = clamp(W / 2 + side * W * 0.21, hw + 40, W - hw - 40); xc = fx + (xt - fx) * v          # slides out from behind his head
            if v < 1: L = hblur(L, 2 + 50 * (1 - v))
            sh = np.zeros_like(L); sh[..., 3] = cv2.GaussianBlur(L[..., 3], (0, 0), 14) * 0.55
            lay = paste(lay, sh, int(xc - ww / 2 + 18), int(yy - hh / 2 + 26), fade * clamp(v * 2, 0, 1))
            lay = paste(lay, L, int(xc - ww / 2), int(yy - hh / 2), fade * clamp(v * 2, 0, 1))
    p = np.clip(person * 1.15, 0, 1)[..., None]
    return lay * (1 - p) + out * p

def comma_geom():
    """where the comma of 'Darling,' ends on screen (the blood drop forms there)."""
    if "comma" in _TY: return _TY["comma"]
    m = text_mask("Darling,", F_SERIF_BI, 150, tracking=2); pad = 34; mm = np.pad(m, pad); hh, ww = mm.shape
    cols = np.nonzero(mm.sum(0) > 0.5)[0]; right = cols[cols > ww * 0.85]
    sub = mm[:, right.min():right.max() + 1]; ys_, xs_ = np.nonzero(sub > 0.5)
    tip = (right.min() + xs_[ys_.argmax()], ys_.max())
    tx = [t for t in E.TEXT if t["style"] == "script" and t["words"][0][0].startswith("Darling")][0]
    yc = (tx["band"][0] + tx["band"][1]) / 2
    _TY["comma"] = (W / 2 - ww / 2 + tip[0], yc - hh / 2 + tip[1]); return _TY["comma"]

def flourish(out, f, x0, x1, y, p, col, a=1.0):
    """a calligraphic swash drawn under a word (p 0..1)."""
    if p <= 0: return out
    ts = np.linspace(0, p, max(2, int(120 * p)))
    xs = x0 + (x1 - x0) * ts; ys = y + 18 * np.sin(ts * math.pi * 1.0) - 26 * ts ** 3 + 10 * np.sin(ts * 9) * (1 - ts)
    lay = np.zeros((H, W), np.float32)
    for i in range(len(ts) - 1):
        th_ = 1 + 4.5 * math.sin(math.pi * ts[i] / max(p, 1e-3) * 0.999) if p > 0 else 1
        cv2.line(lay, (int(xs[i]), int(ys[i])), (int(xs[i + 1]), int(ys[i + 1])), 1.0, max(1, int(th_)), cv2.LINE_AA)
    lay = cv2.GaussianBlur(lay, (0, 0), 0.8)
    return np.clip(out * (1 - lay[..., None] * a) + lay[..., None] * col * a, 0, 1)

def script_text(out, f, tx):
    """serif-italic write-on: a warm pen nib draws the words; ink settles from soft to sharp; 'Darling,' gets a swash."""
    t = f / FPS; (w, wt, _) = tx["words"][0]; t_out = tx["end"]
    if not (wt - 0.05 <= t < t_out + 0.25): return out
    big = w.startswith("Darling"); size = 150 if big else 108; col = (BLOODR * 0.85 + WARMW * 0.15) if big else WARMW * 0.96
    key = ("scr", w)
    if key not in _TY:
        m = text_mask(w, F_SERIF_I if not big else F_SERIF_BI, size, tracking=2); pad = 34; _TY[key] = np.pad(m, pad)
    mm = _TY[key]; hh, ww = mm.shape
    dur = 0.55 if big else 0.75; p = clamp((t - wt) / dur, 0, 1); px = ww * (0.06 + 0.94 * eout(p, 1.4))
    dist = px - np.arange(ww)[None, :]
    rev = np.clip(dist / 26, 0, 1); fresh = np.clip(1 - dist / 140, 0, 1) * (dist > 0)   # freshly written ink is soft
    vis_sharp = mm * rev; vis_soft = cv2.GaussianBlur(mm, (0, 0), 3.5) * rev
    vis = vis_sharp * (1 - fresh) + np.maximum(vis_sharp, vis_soft * 1.1) * fresh
    fade = 1.0 if t < t_out else clamp(1 - (t - t_out) * FPS / 12, 0, 1)
    L = np.zeros((hh, ww, 4), np.float32); sh = cv2.GaussianBlur(vis, (0, 0), 9) * 0.8
    L[..., :3] = col * vis[..., None]; L[..., 3] = np.maximum(vis, sh)
    L[..., :3] = L[..., :3] * (vis[..., None] / np.maximum(L[..., 3:4], 1e-4))
    if big:
        g = cv2.GaussianBlur(vis, (0, 0), 16) * 0.6; L[..., :3] += BLOODR * g[..., None] * (1 - vis[..., None]); L[..., 3] = np.maximum(L[..., 3], g)
        gy = np.linspace(0, 1, hh, dtype=np.float32)[:, None, None]                   # wet highlight on the top of the letters
        L[..., :3] += WARMW * 0.25 * np.clip(0.35 - gy, 0, 1) * vis[..., None]
    y = (tx.get("band", (1300, 1560))[0] + tx.get("band", (1300, 1560))[1]) / 2
    x0 = int(W / 2 - ww / 2); y0 = int(y - hh / 2 + 10 * (1 - eout(p, 2)))
    band = np.exp(-((_GY - y) / (hh * 0.9)) ** 2)[..., None] * 0.55 * fade * eout(clamp((t - wt) / 0.25, 0, 1), 2)
    out = out * (1 - band)
    out = paste(out, L, x0, y0, fade)
    if big:                                                                              # the swash under "Darling,"
        q = clamp((t - wt - dur * 0.85) / 0.45, 0, 1)
        out = flourish(out, f, x0 + ww * 0.12, x0 + ww * 0.80, y0 + hh * 0.86, eout(q, 2), BLOODR * 0.85 + WARMW * 0.1, fade)
    if p < 1:                                                                           # the pen nib
        cols = np.nonzero(mm[:, int(min(ww - 1, px))] > 0.3)[0]
        if len(cols):
            ny = y0 + int(cols.mean()); nx = x0 + int(px)
            nib = np.exp(-(((_GX - nx) / 10) ** 2 + ((_GY - ny) / 10) ** 2))[..., None]
            out = np.clip(out + nib * WARMW * 0.9 + cv2.GaussianBlur(nib[..., 0], (0, 0), 14)[..., None] * SODIUM * 0.6, 0, 1)
    return out

def blood_fill_word(out, word, size, cx, cy, k, a=1.0):
    """WELL fills with blood from the bottom (wavy meniscus), then drips run from the letters."""
    key = ("bw", word, size)
    if key not in _TY:
        m = text_mask(word, F_SERIF_BI, size); pad = 40; mm = np.pad(m, ((pad, 160), (pad, pad))); _TY[key] = mm
    mm = _TY[key]; hh, ww = mm.shape; xs = np.arange(ww)[None, :]; ys = np.arange(hh)[:, None]
    lvl = hh - 160 - (hh - 160) * eout(clamp(k / 12, 0, 1), 2) + 8 * np.sin(xs / 22 + k * 0.6)
    filled = mm * np.clip((ys - lvl) / 3, 0, 1)
    outline = np.clip(mm - cv2.erode(mm, np.ones((5, 5), np.uint8)), 0, 1)
    L = np.zeros((hh, ww, 4), np.float32)
    gy = np.clip((ys - (hh - 160) * 0.2) / ((hh - 160) * 0.8), 0, 1)[..., None]
    blood = np.array([0.03, 0.02, 0.48], np.float32) * (1 - gy) * 0.4 + np.array([0.06, 0.05, 0.78], np.float32) * (0.6 + 0.4 * gy)
    L[..., :3] = blood * filled[..., None] + WARMW * 0.9 * outline[..., None] * (1 - filled[..., None])
    L[..., 3] = np.maximum(filled, outline * 0.95)
    if k > 10:                                                                          # drips
        rng = np.random.default_rng(3); cols = np.nonzero(mm[:hh - 160].sum(0) > 2)[0]
        for xd in rng.choice(cols, 5, replace=False):
            yb = np.nonzero(mm[:hh - 160, xd] > 0.5)[0]
            if not len(yb): continue
            y0 = yb.max(); Ld = min(150, (k - 10) * rng.uniform(4, 9)); wdt = int(rng.integers(5, 10))
            cv2.line(L, (int(xd), int(y0)), (int(xd), int(y0 + Ld)), (0.05, 0.04, 0.62, 1.0), wdt, cv2.LINE_AA)
            cv2.circle(L, (int(xd), int(y0 + Ld)), wdt, (0.05, 0.04, 0.70, 1.0), -1, cv2.LINE_AA)
    hl = np.exp(-((ys - lvl - 6) / 4) ** 2) * filled * (k < 14)
    L[..., :3] += WARMW * 0.5 * hl[..., None]
    g = cv2.GaussianBlur(L[..., 3], (0, 0), 14) * 0.45; G = np.zeros_like(L); G[..., :3] = BLOODR; G[..., 3] = g
    out = paste(out, G, int(cx - ww / 2), int(cy - (hh - 160) / 2), a)
    v = eout((k + 1) / 5, 3); sc = 1 + 0.35 * (1 - v)
    Ls = L if sc <= 1.001 else cv2.resize(L, (int(ww * sc), int(hh * sc)))
    return paste(out, Ls, int(cx - Ls.shape[1] / 2), int(cy - (hh - 160) * sc / 2), a)

def hook_text(out, f, tx):
    """I DON'T WISH YOU — each word slams in on its syllable (white-hot then cooling, a shock ring); WELL fills with blood."""
    t = f / FPS; t_out = tx["end"]
    if not (tx["words"][0][1] - 0.03 <= t < t_out + 0.1): return out
    fade = 1.0 if t < t_out else clamp(1 - (t - t_out) * FPS / 5, 0, 1)
    row = [(w, wt) for w, wt, l in tx["words"] if l == 0]
    sets = [letter_set(w, F_HEAVY, 92, 5) for w, _ in row]; gap = 30
    total = sum(s_[3] for s_ in sets) + gap * (len(sets) - 1); x = W / 2 - total / 2; y = 1320
    for (w, wt), st_ in zip(row, sets):
        wd = st_[3]; k = (t - wt) * FPS
        if k >= -1:
            heat = math.exp(-max(k, 0) / 4); col = WARMW * (1 - heat) + np.array([1.0, 1.0, 1.0], np.float32) * heat
            out = letters_paste(out, w, F_HEAVY, 92, 5, col, x + wd / 2, y, k * 2.2, None, 0.6, SODIUM if heat > 0.2 else None, None, 30, fade)
            if 0 <= k < 10:
                r = 40 + 26 * k; ring = np.exp(-((np.sqrt((_GX - (x + wd / 2)) ** 2 + ((_GY - y) * 1.8) ** 2) - r) / 3) ** 2)
                out = np.clip(out + ring[..., None] * SODIUM * 0.5 * (1 - k / 10) * fade, 0, 1)
        x += wd + gap
    rule = clamp(sum(1 for _, wt in row if t >= wt) / max(1, len(row)), 0, 1)        # a thin rule grows as the line builds
    rw = total * eout(rule, 2);
    if rw > 2: cv2.line(out, (int(W / 2 - rw / 2), 1378), (int(W / 2 + rw / 2), 1378), tuple(float(c) * fade for c in SODIUM * 0.8), 2, cv2.LINE_AA)
    wl = [(w, wt) for w, wt, l in tx["words"] if l == 1]
    if wl and t >= wl[0][1] - 0.02:
        out = blood_fill_word(out, wl[0][0], 230, W / 2, 1480, (t - wl[0][1]) * FPS, fade)
    return out

def drop_fall(out, f, s):
    """the comma of 'Darling,' swells into a drop of blood, lets go, and falls in slow motion with Dexter refracted inside;
    the camera pushes toward it."""
    k = f - s["f0"]; n = s["f1"] - s["f0"]
    tx = [t for t in E.TEXT if t["style"] == "script" and t["words"][0][0].startswith("Darling")][0]
    out = script_text(out, f, tx)                                                       # the word lives in this layer here
    cx, cy0 = comma_geom(); yS = DROP_Y
    det = 26; u = clamp((k - det) / max(1, n - det), 0, 1)
    fade = clamp(k / 30, 0, 1)
    base = out * (1 - 0.72 * fade)
    if k < det:                                                                         # swelling at the comma, stretching
        g = eout(k / det, 2); r = 8 + 34 * g; y = cy0 + 10 + 38 * g; st = 1 + 0.9 * g
    else:
        r = 42 + 14 * u; y = cy0 + 48 + (yS - cy0 - 48) * ein(u, 2.3); st = 1.6 - 0.5 * u
    o = base.copy(); xx = _GX - cx; yy = _GY - y
    dn = np.sqrt((xx / r) ** 2 + (yy / (r * 1.06)) ** 2)
    tl = r * 1.6 * st
    tail = (yy < 0) & (yy > -tl) & (np.abs(xx) < r * np.clip((yy + tl) / tl, 0, 1) ** 1.4)
    if k < det:                                                                         # still attached: a neck back to the comma
        neck = (_GY > cy0 - 4) & (_GY < y) & (np.abs(xx) < 3 + 4 * (1 - k / det))
        tail = tail | neck
    inside = cv2.GaussianBlur(((dn < 1) | tail).astype(np.float32), (0, 0), 0.9)
    nxm = np.clip(xx / r, -1, 1); nym = np.clip(yy / r, -1, 1)
    mx = (W / 2 - nxm * 520).astype(np.float32); my = (H * 0.38 - nym * 640).astype(np.float32)
    ref = cv2.remap(out, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    body = ref * np.array([0.45, 0.42, 1.05], np.float32) * 0.95 + np.array([0.10, 0.08, 0.80], np.float32) * 0.12
    edge = np.clip(dn - 0.75, 0, 1)[..., None] * 0.6
    o = o * (1 - inside[..., None]) + (body * (1 - edge) + BLOODR * 0.3 * edge) * inside[..., None]
    hi = np.exp(-(((xx + r * 0.35) / (r * 0.18)) ** 2 + ((yy + r * 0.40) / (r * 0.28)) ** 2))[..., None]
    o = o + hi * WARMW * 0.85 * inside[..., None]
    surf = np.exp(-((_GY - yS - r) / 5) ** 2)[..., None] * np.exp(-((_GX - cx) / 420) ** 2)[..., None]
    o = o + surf * WARMW * 0.08 * u
    z = 1 + 0.55 * ein(u, 1.8)                                                          # push in on the impact point
    if z > 1.001:
        o = zoom_about(o, cx, yS, z)
        o = o * (1 - 0.0)
    return np.clip(o, 0, 1)

DROP_X, DROP_Y = W / 2, 1790.0                                                      # (v8 comma drop; unused in v9)

# ============================================================================ v8 frame
def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999; t = f / FPS
    P = prev_shot(s); tin = s.get("tin"); tout = s.get("tout")
    person = None
    if s.get("graphic") == "knife_roll": out = knife_roll_scene(f, s)
    elif s.get("seg"): out, person = render_shot(s, f, want_mask=True)
    else: out = render_shot(s, f)
    if s.get("sweeps"): out = sweeps(out, f, 0.8)
    if s.get("rain"): out = rain_glass(out, f, 0.7, 0.0)
    if s.get("freeze") is not None: out = freeze_comp(out, person, f, s)
    for tx in E.TEXT:
        if tx["style"] == "behind" and s.get("seg"): out = behind_text(out, f, s, tx, person)
    if s.get("dropfall"): out = drop_fall(out, f, s)
    if tin == "mirror_in": out = mirror_in(out, f, k)
    elif tin in TR2 and k < TR2[tin][2] and P is not None: out = TR2[tin][0](last_visible(P), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, shot_first(n_), kn, f, s, n_)
    if tout == "mirror_out": out = mirror_out(out, f, s)
    out = text8(out, f, s, person)
    out = finish8(out, f)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)

def init_hits():
    HITS.clear()
    for h in (88, 104, 128): HITS.append((E.fh(h), 10, 3.5))

# ============================================================================ v9 — NIGHT BLOOM: moonbloom toolkit
th, fh = E.th, E.fh
# A blood moon, jasmine-white petals in depth, violet night, moon-silver highlights, crimson for blood + the hook.
CRIMSON = np.array([0.10, 0.07, 0.80], np.float32)     # BGR blood crimson
JASMINE = np.array([0.90, 0.98, 1.00], np.float32)     # BGR jasmine white (a breath of cream)
MOONW = np.array([1.00, 0.97, 0.94], np.float32)       # BGR moon silver
VIOLET = np.array([0.22, 0.05, 0.13], np.float32)      # BGR violet night
SKYC = np.array([0.050, 0.016, 0.030], np.float32)     # BGR night sky

# ---- time maps: lin=True -> piecewise linear (a dead freeze on the song's silence), else the engine's PCHIP
_tmap0 = tmap
def tmap(s, u):
    if s.get("lin"):
        ks = s["tmap"]; return float(np.interp(clamp(u, 0, 1), [k[0] for k in ks], [k[1] for k in ks]))
    return _tmap0(s, u)

def beat_bounce(f):
    """a 1.5 % zoom pulse on every beat of the montage (the 808s), e34-e58 and the hook."""
    e = f / FPS / E.HB
    if not (34 <= e < 58 or 64 <= e < 70): return 1.0
    ph = (e % 2) * E.HB
    return 1 + 0.015 * math.exp(-ph / 0.08)

# ---- grade: MOONBLOOM
_LUT9 = None
def lut9():
    global _LUT9
    if _LUT9 is None:
        x = np.linspace(0, 1, 1024, dtype=np.float32)
        y = PchipInterpolator([0, .06, .20, .50, .78, .93, 1], [0.030, 0.058, 0.185, 0.475, 0.765, 0.895, 0.955])(x)
        _LUT9 = (x, y.astype(np.float32))
    return _LUT9

def corr9(s):
    key = "9:" + s["n"]
    if key in CORR: return CORR[key]
    t = tmap(s, 0.5); img = sample(s["src"], t).astype(np.float32) / 255
    L = img[..., 0] * 0.114 + img[..., 1] * 0.587 + img[..., 2] * 0.299
    fa = face_at(s, t) if s.get("face") is not None else None
    if fa:
        r = int(fa[2] * 0.3); x, y = int(fa[0]), int(fa[1])
        patch = L[max(0, y - r):y + r, max(0, x - r):x + r]; face = float(np.percentile(patch, 65)) if patch.size else float(L.mean())
    else:
        face = float(np.percentile(L, 75))
    g = clamp(math.log(s.get("target", 0.40)) / math.log(clamp(face, 0.02, 0.97)), 0.68, 1.30)
    m = img.reshape(-1, 3).mean(0); gains = np.clip((m.mean() / (m + 1e-6)) ** 0.10, 0.92, 1.08)
    CORR[key] = (g, gains.astype(np.float32)); return CORR[key]

_grade0 = grade
def grade(img, s, f):
    if s.get("look") != "moonbloom": return _grade0(img, s, f)
    g, gains = corr9(s)
    x = np.clip(img * gains, 0, 1) ** g
    if s.get("ev"): x = np.clip(x * 2 ** s["ev"], 0, 1)
    lx, ly = lut9(); x = np.interp(x, lx, ly).astype(np.float32)
    Bc, Gc, Rc = x[..., 0], x[..., 1], x[..., 2]
    L = (Bc * 0.114 + Gc * 0.587 + Rc * 0.299)[..., None]
    blood = np.clip((Rc - 1.55 * np.maximum(Gc, Bc)) * 4.0, 0, 1)[..., None]
    hue = (Rc - Gc) / (Rc + 1e-3)
    skin = (np.clip(1 - np.abs(hue - 0.22) / 0.20, 0, 1) * np.clip((Rc - Bc) * 6, 0, 1) * np.clip(L[..., 0] * 3, 0, 1))[..., None]
    sat = 0.68 + 0.24 * skin + 0.60 * blood
    x = L + (x - L) * sat
    sh = (1 - L) ** 2.2 * (1 - 0.6 * skin); hi = L ** 2.0 * (1 - 0.5 * skin)
    x = x + sh * np.array([0.062, -0.010, 0.030], np.float32) + hi * np.array([0.022, 0.010, -0.014], np.float32)
    x[..., 2:3] += blood * 0.04
    return np.clip(x, 0, 1)

# ---- finish: jasmine-white Pro-Mist bloom, a crimson halation edge, mist, grain, vignette (blacks lifted, never crushed)
def finish9(out, f):
    small = cv2.resize(out, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi = np.clip(small.max(2) - 0.55, 0, 1)
    b1 = cv2.GaussianBlur(hi, (0, 0), 5); b2 = cv2.GaussianBlur(hi, (0, 0), 18)
    out = out + cv2.resize(b1 * 0.50 + b2 * 0.60, (W, H))[..., None] * JASMINE * 0.42
    out = out + cv2.resize(np.clip(b2 - b1 * 0.8, 0, 1), (W, H))[..., None] * CRIMSON * 0.10
    out = out * 0.93 + cv2.resize(cv2.GaussianBlur(small, (0, 0), 10), (W, H)) * 0.07
    out = np.maximum(out, 0.020)
    return np.clip(out * (0.80 + 0.20 * VIG) + grain(f, 0.016), 0, 1)

# ---- the blood moon (a still: the source moon is static), drifting haze, faint stars
_MOON = {}
MOON_C = (548.0, 690.0); MOON_R0 = 285.0
def moon_assets():
    if "img" in _MOON: return _MOON
    cap = cv2.VideoCapture(E.SRC["p9"][0]); cap.set(cv2.CAP_PROP_POS_MSEC, 230.25 * 1000); ok, fr = cap.read(); cap.release()
    cx, cy, r = 576.6, 363.5, 242.0; Rc = int(r * 1.34)
    crop = fr[int(cy - Rc):int(cy + Rc), int(cx - Rc):int(cx + Rc)].astype(np.float32) / 255
    crop = np.clip((crop * np.array([0.60, 0.66, 1.06], np.float32)) ** 1.12 * 1.10, 0, 1)        # a blood moon
    rng = np.random.default_rng(17)
    g = (_GY / H)[..., None]
    sky = SKYC * (1.15 - 0.5 * g) + VIOLET * 0.05 * np.exp(-((_GY - MOON_C[1]) ** 2 + (_GX - MOON_C[0]) ** 2) / (2 * 520.0 ** 2))[..., None]
    st = np.zeros((H, W), np.float32)
    for _ in range(90):
        x, y = rng.uniform(0, W), rng.uniform(0, H * 0.95); st[int(y), int(x)] = rng.uniform(0.25, 0.9) ** 2
    st = cv2.GaussianBlur(st, (0, 0), 1.1) * 4.0
    sky = sky + st[..., None] * MOONW * 0.5
    noise_ = rng.standard_normal((H // 8, W // 2)).astype(np.float32)
    cl = sum(cv2.resize(cv2.GaussianBlur(noise_, (0, 0), s_), (W * 2, H), interpolation=cv2.INTER_CUBIC) * a for s_, a in ((14, 1.0), (6, 0.45), (2.5, 0.2)))
    cl = (cl - cl.mean()) / (cl.std() + 1e-6)
    _MOON.update(img=crop, r=r, Rc=Rc, sky=sky.astype(np.float32), cloud=cl.astype(np.float32))
    return _MOON

def moon_layer(cx, cy, R):
    M_ = moon_assets(); sc = R / M_["r"]; n = int(2 * M_["Rc"] * sc) | 1
    im = cv2.resize(M_["img"], (n, n), interpolation=cv2.INTER_AREA if sc < 1 else cv2.INTER_CUBIC)
    lay = np.zeros((H, W, 3), np.float32); x0, y0 = int(cx - n / 2), int(cy - n / 2)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + n), min(H, y0 + n)
    if xb > xa and yb > ya: lay[ya:yb, xa:xb] = im[ya - y0:yb - y0, xa - x0:xb - x0]
    return lay

def disc_mask(cx, cy, R, soft=2.0):
    return np.clip((R - np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2)) / soft + 0.5, 0, 1)

def moon_scene(f, s, t_override=None):
    M_ = moon_assets(); u = (f - s["f0"]) / max(1, s["f1"] - s["f0"]); t = f / FPS if t_override is None else t_override
    R = MOON_R0 * (1 + 0.06 * u); cx, cy = MOON_C[0], MOON_C[1] - 30 * u
    out = M_["sky"].copy() + moon_layer(cx, cy, R)
    dm = disc_mask(cx, cy, R, 3.0)
    halo = cv2.GaussianBlur(dm, (0, 0), 60)[..., None]
    out = out + halo * np.array([0.05, 0.10, 0.32], np.float32) * 0.9
    sh = int((t * 38) % (W)); cl = M_["cloud"][:, sh:sh + W]
    ca = np.clip((cl - 0.55) * 0.9, 0, 0.85)[..., None]
    lit = np.clip(cv2.GaussianBlur(dm, (0, 0), 120) * 2.2, 0, 1)[..., None]
    out = out * (1 - ca * 0.75) + ca * (SKYC * 1.6 + lit * np.array([0.10, 0.16, 0.36], np.float32))
    return np.clip(out, 0, 1)

def moon_disc_frame():
    """the edit's last frame: the drop of blood has become a crimson moon at the moon's place (frame 0 continues it)."""
    if "disc" in _MOON: return _MOON["disc"]
    M_ = moon_assets(); out = M_["sky"].copy()
    out = blood_disc(out, MOON_C[0], MOON_C[1], MOON_R0, gloss=0.0)
    dm = disc_mask(MOON_C[0], MOON_C[1], MOON_R0, 3.0); halo = cv2.GaussianBlur(dm, (0, 0), 60)[..., None]
    out = out + halo * np.array([0.05, 0.10, 0.32], np.float32) * 0.9
    _MOON["disc"] = np.clip(out, 0, 1); return _MOON["disc"]

def blood_disc(out, cx, cy, R, gloss=1.0, refr=None):
    """a glossy drop of blood seen from above: deep crimson body, darker rim, refraction, a specular highlight."""
    rr = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2); m = np.clip((R - rr) / 2.5 + 0.5, 0, 1)[..., None]
    q = np.clip(rr / max(R, 1), 0, 1)[..., None]
    body = CRIMSON * (0.95 - 0.45 * q ** 3) + np.array([0.0, 0.0, 0.10], np.float32) * (1 - q)
    if refr is not None: body = body * 0.78 + lum8(refr)[..., None] * np.array([0.03, 0.03, 0.30], np.float32)
    o = out * (1 - m) + body * m
    if gloss > 0:
        hx, hy = cx - 0.36 * R, cy - 0.40 * R
        sp = np.exp(-(((_GX - hx) / (0.20 * R + 1)) ** 2 + ((_GY - hy) / (0.11 * R + 1)) ** 2))[..., None]
        rim = np.exp(-((rr - R * 0.97) / (0.03 * R + 1.5)) ** 2)[..., None] * (_GY < cy)[..., None]
        o = o + (sp * 0.85 + rim * 0.25) * gloss * WHITE * m
    return o

def loop_in(out, f, k, n=16):
    """frame 0 continues the last frame: the crimson drop-moon gives way to the real blood moon."""
    v = smooth((k + 1) / n)
    return np.clip(moon_disc_frame() * (1 - v) + out * v, 0, 1)

# ---- jasmine petals: sprites, an ambient drifting field in depth (behind / in front of the person matte)
_PET = {}
def petal_sprites():
    if "list" in _PET: return _PET["list"]
    rng = np.random.default_rng(91); L_ = []
    for k in range(6):
        h, w = 120, 56
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); u = yy / (h - 1); v = (xx - (w - 1) / 2) / ((w - 1) / 2)
        prof = np.clip(np.sin(np.pi * np.clip(u, 0, 1) ** (0.75 + 0.1 * (k % 3))), 0, 1) * (0.78 + 0.2 * rng.random())
        tip = 1 - 0.25 * np.clip((u - 0.85) / 0.15, 0, 1)
        m = np.clip((prof * tip - np.abs(v + 0.08 * np.sin(np.pi * u) * (k % 2 * 2 - 1))) * 9, 0, 1)
        shade = 0.80 + 0.20 * np.clip(1 - np.abs(v), 0, 1) ** 0.6 - 0.10 * u + 0.05 * np.exp(-(v / 0.07) ** 2)
        col = JASMINE * shade[..., None]
        base = np.clip(1 - u / 0.25, 0, 1)[..., None]
        col = col * (1 - 0.35 * base) + np.array([0.62, 0.86, 0.80], np.float32) * 0.35 * base           # a green-cream heel
        a = m * (0.88 - 0.12 * np.abs(v))
        L_.append(np.dstack([col, a]).astype(np.float32))
    _PET["list"] = L_; return L_

def draw_sprite(acc, spr, x, y, sc, rot, flip=1.0, blur=0.0, alpha=1.0, stretch=1.0):
    """paste a sprite (RGBA, premult not assumed) centred at (x, y) into an RGBA accumulator (over)."""
    h, w = spr.shape[:2]; sx = sc * max(0.08, abs(flip)) * stretch; sy = sc
    R_ = max(h * sy, w * sx) * 0.75 + 6 + 3 * blur
    n = int(2 * R_) | 1
    if n < 5 or x < -R_ or x > W + R_ or y < -R_ or y > H + R_: return
    th_ = math.radians(rot); c, s_ = math.cos(th_), math.sin(th_)
    M = np.float32([[c * sx, -s_ * sy, 0], [s_ * sx, c * sy, 0]])
    M[0, 2] = n / 2 - (M[0, 0] * w / 2 + M[0, 1] * h / 2); M[1, 2] = n / 2 - (M[1, 0] * w / 2 + M[1, 1] * h / 2)
    pm = np.dstack([spr[..., :3] * spr[..., 3:4], spr[..., 3:4]])                       # premultiplied: no dark fringes
    tile = cv2.warpAffine(pm, M, (n, n), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    if blur > 0.6: tile = cv2.GaussianBlur(tile, (0, 0), blur)
    if flip < 0: tile[..., :3] *= 0.86                                                   # the back of the petal
    x0, y0 = int(x - n / 2), int(y - n / 2)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + n), min(H, y0 + n)
    if xb <= xa or yb <= ya: return
    t_ = tile[ya - y0:yb - y0, xa - x0:xb - x0]; a = t_[..., 3:4] * alpha
    sub = acc[ya:yb, xa:xb]
    sub[..., :3] = sub[..., :3] * (1 - a) + t_[..., :3] * alpha; sub[..., 3:4] = sub[..., 3:4] * (1 - a) + a

PET_N = 44
_PF = {}
def petal_params():
    if "p" in _PF: return _PF["p"]
    rng = np.random.default_rng(7); P_ = []
    for i in range(PET_N):
        z = rng.uniform(0.15, 1.0) ** 0.8
        P_.append(dict(z=z, x0=rng.uniform(0, 1), y0=rng.uniform(0, 1), ph=rng.uniform(0, 6.28), spin=rng.uniform(-70, 70),
                       fl=rng.uniform(1.2, 3.2), k=int(rng.integers(6)), rot0=rng.uniform(0, 360), on=rng.uniform(0, 1)))
    _PF["p"] = P_; return P_

def petal_density(f):
    s = shot_at(f); d = s.get("petals", 0.0); k = f - s["f0"]; P = prev_shot(s); n_ = nxt_of(s)
    if P is not None and k < 10: d = P.get("petals", 0.0) + (d - P.get("petals", 0.0)) * smooth((k + 1) / 10)
    if n_ is not None and n_["f0"] - f <= 6 and n_.get("tin") in ("bloom",): d = d
    return d

def petal_time(f):
    """the field's clock: it stops dead on the silence (the freeze) and holds until the bloom."""
    t = f / FPS; ts = th(E.E_SIL)
    if ts <= t < th(E.HDROP): return ts
    if t >= th(E.HDROP): return t - (th(E.HDROP) - ts)
    return t

def petals9(out, f, person=None):
    d = petal_density(f)
    if d <= 0.01: return out
    t = petal_time(f); spr = petal_sprites()
    back = np.zeros((H, W, 4), np.float32); front = np.zeros((H, W, 4), np.float32)
    frozen = th(E.E_SIL) <= f / FPS < th(E.HDROP)
    drift = (f / FPS - th(E.E_SIL)) if frozen else 0.0
    for p in sorted(petal_params(), key=lambda q: q["z"]):
        if p["on"] > d: continue
        z = p["z"]; sc = (0.18 + 0.95 * z ** 1.6)
        span_x, span_y = W + 400, H + 400
        x = (p["x0"] * span_x + (55 + 120 * z) * t + 40 * math.sin(0.7 * t + p["ph"])) % span_x - 200
        y = (p["y0"] * span_y + (70 + 150 * z) * t) % span_y - 200
        if frozen:                                                              # parallax creep while time stands still
            x = W / 2 + (x - W / 2) * (1 + 0.035 * z * drift); y = H * 0.45 + (y - H * 0.45) * (1 + 0.035 * z * drift)
        rot = p["rot0"] + p["spin"] * t; flip = math.cos(p["fl"] * t + p["ph"])
        blur = 0.0 if z < 0.62 else (z - 0.62) * 14
        al = 0.55 + 0.45 * z
        draw_sprite(back if z < 0.55 else front, spr[p["k"]], x, y, sc, rot, flip, blur, al)
    if person is not None:
        back *= (1 - np.clip(person * 1.15, 0, 1))[..., None]
    for lay in (back, front):
        out = out * (1 - lay[..., 3:4]) + lay[..., :3]
    return np.clip(out, 0, 1)

# ---- the freeze on the song's dead silence: time stops, the world drains to violet, Dexter stays lit (2.5-D parallax)
def freeze9(img, person, f, s):
    k = f - fh(E.E_SIL); e = eout(clamp((k + 1) / 7, 0, 1), 2)
    if person is not None:
        u0 = clamp((fh(s["freeze_e"]) - s["f0"]) / max(1, s["f1"] - s["f0"]), 0, 1)
        bg_s = dict(s); z_f = keys_at(s["z"], u0)
        bg_s["z"] = [(u0, z_f)] + [(q[0], z_f + (q[1] - z_f) * 0.30) for q in s["z"] if q[0] > u0]
        bg = render_shot(bg_s, f, with_shake=False)
        pm = cv2.GaussianBlur(np.clip(person * 1.2, 0, 1), (0, 0), 1.5)[..., None]
        img = bg * (1 - pm) + img * pm
    else:
        pm = np.zeros((H, W, 1), np.float32)
    L = lum8(img)[..., None]
    drained = L * 0.62 + VIOLET * L * 0.9 + VIOLET * 0.10
    o = img * (1 - e) + (drained * (1 - pm) + img * (0.92 + 0.10 * pm) * pm) * e
    if person is not None:
        gy, gx = np.gradient(cv2.GaussianBlur(person, (0, 0), 3))
        rim = np.clip(-(gx * 0.6 + gy * 0.8) * 9, 0, 1)[..., None]                        # moonlight from the upper left
        o = o + rim * MOONW * 0.55 * e
    flash = math.exp(-((k - 0.5) / 1.6) ** 2) * 0.22                                       # the freeze "click"
    return np.clip(o + flash * MOONW, 0, 1)

def freeze_seams(out, f, j, pre):
    """the bud's seams split open in the last frames of the silence: thin white light along six petal lines."""
    u = clamp((j + pre + 1) / pre, 0, 1); cx, cy = BLOOM_C
    rr = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2) + 1e-3; aa = np.arctan2(_GY - cy, _GX - cx)
    seg = 2 * math.pi / 6; a = np.mod(aa - BLOOM_A0, seg); da = np.minimum(a, seg - a) * rr
    L_ = 200 + 1600 * ein(u, 1.4)
    line = np.exp(-(da / (1.2 + 3.0 * u)) ** 2) * np.clip((L_ - rr) / 120, 0, 1)
    glow = cv2.GaussianBlur(line, (0, 0), 6 + 10 * u)
    bud = np.exp(-(rr / (60 + 140 * u)) ** 2) * u ** 2
    return np.clip(out + (line * 0.9 + glow * 1.2)[..., None] * JASMINE * u + bud[..., None] * JASMINE * 0.8, 0, 1)

# ---- transitions ------------------------------------------------------------------------------------------
BLOOM_C = (W / 2, H * 0.70); BLOOM_A0 = math.radians(-90 + 30)

def tilt(A, B, j, f, sa, sb, pre=12, post=16):
    """the camera tilts down from the moon to Dexter looking up at it: one vertical strip, eased, with motion blur."""
    n = pre + post; p = (j + pre + 0.5) / n; D = H * smooth(p) ** 1.0
    D = H * (0.5 - 0.5 * math.cos(math.pi * clamp(p, 0, 1)))
    sp = math.sin(math.pi * clamp(p, 0, 1)) * H * math.pi / n * 0.5
    canvas = np.zeros((H, W, 3), np.float32)
    Ay = -D; By = H - D
    MA = np.float32([[1, 0, 0], [0, 1, Ay]]); MB = np.float32([[1, 0, 0], [0, 1, By]])
    a_ = cv2.warpAffine(A, MA, (W, H), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    b_ = cv2.warpAffine(B, MB, (W, H), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    seam = np.clip((_GY - (By - 140)) / 280, 0, 1)[..., None]
    canvas = a_ * (1 - seam) + b_ * seam
    return np.clip(hblur(canvas, 1 + sp * 0.9, vertical=True), 0, 1)

_FOL = {}
def foliage_strip():
    if "rgba" in _FOL: return _FOL["rgba"]
    rng = np.random.default_rng(23); Ls = int(3.4 * W); h2, w2 = H // 2, Ls // 2
    acc = np.zeros((h2, w2, 4), np.float32)
    for i in range(900):
        x = rng.uniform(0, w2)
        core = W * 0.5 <= x <= W * 1.25                                               # the dense middle covers the frame at the cut
        if not core and rng.random() < 0.55: continue
        y = rng.uniform(-40, h2 + 40); L_ = rng.uniform(60, 190); Wd = L_ * rng.uniform(0.32, 0.5)
        lay = np.zeros((h2, w2), np.float32)
        cv2.ellipse(lay, (int(x), int(y)), (int(L_ / 2), int(Wd / 2)), rng.uniform(0, 180), 0, 360, 1.0, -1, cv2.LINE_AA)
        shade = rng.uniform(0.35, 1.0)
        col = np.array([0.020, 0.045, 0.030], np.float32) * shade + np.array([0.03, 0.02, 0.025], np.float32) * rng.random()
        a = lay[..., None]; acc[..., :3] = acc[..., :3] * (1 - a) + col * a; acc[..., 3:4] = np.maximum(acc[..., 3:4], a)
    for i in range(80):                                                                 # night-blooming jasmine stars
        x = rng.uniform(W * 0.25, W * 1.5); y = rng.uniform(0, h2); r = rng.uniform(10, 26); rot = rng.uniform(0, 72)
        lay = np.zeros((h2, w2), np.float32)
        for q in range(5):
            a_ = math.radians(rot + 72 * q)
            cv2.ellipse(lay, (int(x + 0.55 * r * math.cos(a_)), int(y + 0.55 * r * math.sin(a_))), (int(r * 0.55), int(r * 0.28)), math.degrees(a_), 0, 360, 1.0, -1, cv2.LINE_AA)
        a = lay[..., None] * 0.95; acc[..., :3] = acc[..., :3] * (1 - a) + JASMINE * 0.92 * a; acc[..., 3:4] = np.maximum(acc[..., 3:4], a)
    acc = cv2.GaussianBlur(acc, (0, 0), 5.5)
    acc[..., 3] = np.clip(acc[..., 3] * 1.25, 0, 1)
    _FOL["rgba"] = cv2.resize(acc, (Ls, H), interpolation=cv2.INTER_LINEAR); return _FOL["rgba"]

def foliage(A, B, j, f, sa, sb, pre=10, post=10):
    """the camera passes behind a jasmine bush: out-of-focus leaves and white blossoms sweep across the lens."""
    st_ = foliage_strip(); Ls = st_.shape[1]
    p = (j + pre + 0.5) / (pre + post); XL = W * 0.85 - p * (W * 0.85 + W * 1.75)
    base = A if j < 0 else B
    sub = np.zeros((H, W, 4), np.float32); x0 = int(XL)
    xa, xb = max(0, x0), min(W, x0 + Ls)
    if xb > xa: sub[:, xa:xb] = st_[:, xa - x0:xb - x0]
    sub = hblur(sub, 1 + 60 * math.sin(math.pi * clamp(p, 0, 1)))
    a = sub[..., 3:4]
    return np.clip(base * (1 - a) + sub[..., :3] * a, 0, 1)

def petal_gust(A, B, j, f, sa, sb, pre=12, post=14):
    """a gust of jasmine petals blows across the lens, densest on the cut."""
    p = (j + pre + 0.5) / (pre + post); spr = petal_sprites(); rng = np.random.default_rng(55)
    lay = np.zeros((H, W, 4), np.float32)
    for i in range(64):
        pc = rng.normal(0.5, 0.13); y = rng.uniform(-0.05, 1.05) * H; z = rng.uniform(0.3, 1.0)
        x = W * 0.5 + (p - pc) * W * (3.2 + 2.2 * z) + rng.uniform(-120, 120)
        draw_sprite(lay, spr[i % 6], x, y + 60 * math.sin(6 * p + i), 0.45 + 1.1 * z ** 2, rng.uniform(0, 360) + 220 * p,
                    math.cos(7 * p + i), blur=1 + 5 * z, alpha=0.80, stretch=1.0 + 2.2 * z)
    wash = math.exp(-((p - 0.5) / 0.12) ** 2) * 0.16
    base = A if j < 0 else B
    o = base * (1 - lay[..., 3:4]) + lay[..., :3]
    return np.clip(o + wash * JASMINE, 0, 1)

def bloom9(A, B, j, f, sa, sb, pre=18, post=24):
    """HERO (the drop): the frozen frame splits along six petal seams and blooms open toward the camera; the kill is
    inside the flower. Pre-roll: the seams split with light during the last 0.3 s of the silence."""
    if j < 0: return freeze_seams(A, f, j, pre)
    v = (j + 1) / post; cx, cy = BLOOM_C; A = freeze_seams(A, f, -1, pre)
    zb = 1.0 + 0.30 * (1 - eout(v, 2.2))
    Bz = zoom_about(B, cx, cy, zb)
    if v < 0.5: Bz = radial_blur(Bz, cx, cy, 1.0, 1.0 + 0.10 * (1 - v / 0.5), 5)
    out = Bz.copy()
    aa = np.arctan2(_GY - cy, _GX - cx); seg = 2 * math.pi / 6
    for i in range(6):
        a0 = BLOOM_A0 + i * seg; mid = a0 + seg / 2
        dd = np.mod(aa - a0, 2 * math.pi)
        m = (np.clip(dd * 160, 0, 1) * np.clip((seg - dd) * 160, 0, 1)).astype(np.float32)
        o_ = ein(v, 1.25)
        tx, ty = math.cos(mid) * 1500 * o_, math.sin(mid) * 1500 * o_
        sc = 1 + 1.1 * o_; rot = (14 if i % 2 else -14) * o_
        M = cv2.getRotationMatrix2D((cx, cy), rot, sc); M[0, 2] += tx; M[1, 2] += ty
        lit = np.clip(A * (1 + 0.9 * o_) + JASMINE * 0.55 * o_ ** 1.5, 0, 1)
        pet = cv2.warpAffine(np.dstack([lit, m]), M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
        edge = cv2.GaussianBlur(cv2.morphologyEx((pet[..., 3] > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8)).astype(np.float32), (0, 0), 3)
        al = pet[..., 3:4] * (1 - smooth((v - 0.45) / 0.45))
        out = out * (1 - al) + pet[..., :3] * al + edge[..., None] * JASMINE * 0.6 * (1 - v)
    rr = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2)
    heart = np.exp(-(rr / (120 + 900 * v)) ** 2)[..., None] * (1 - v) ** 2 * 0.9
    out = out + heart * JASMINE
    spr = petal_sprites(); rng = np.random.default_rng(77); lay = np.zeros((H, W, 4), np.float32)
    for i in range(46):                                                                  # petals burst out of the heart
        ang = rng.uniform(0, 6.283); spd = rng.uniform(500, 2600); z = rng.uniform(0.3, 1.0)
        r_ = spd * eout(v, 1.6) + 40; x = cx + math.cos(ang) * r_; y = cy + math.sin(ang) * r_
        draw_sprite(lay, spr[i % 6], x, y, 0.5 + 2.2 * z * (0.4 + v), math.degrees(ang) + 90 + 300 * v, math.cos(9 * v + i),
                    blur=1 + 7 * z, alpha=1 - smooth((v - 0.6) / 0.4), stretch=1 + 1.2 * (1 - v))
    out = out * (1 - lay[..., 3:4]) + lay[..., :3]
    return np.clip(out, 0, 1)

def strobe(A, B, j, f, sa, sb, pre=3, post=5):
    """deep-house strobe: two soft strobe hits across the cut (never full black / white)."""
    gains = {-3: 1.0, -2: 1.55, -1: 0.42, 0: 1.75, 1: 0.55, 2: 1.25, 3: 1.05, 4: 1.0}
    img = A if j < 0 else B; g = gains.get(j, 1.0)
    o = img * g
    if g > 1.2: o = o + (g - 1.2) * 0.35 * JASMINE
    return np.clip(o, 0, 1)

def torch_point(img):
    small = cv2.GaussianBlur(cv2.resize(lum8(img), (W // 8, H // 8)), (0, 0), 2)
    y, x = np.unravel_index(np.argmax(small), small.shape); return x * 8 + 4, y * 8 + 4

def beam(A, B, j, f, sa, sb, pre=8, post=11):
    """the flashlight swings into the lens: its beam whites out the frame; the next shot comes up brightest-first."""
    if j < 0:
        u = (j + pre + 1) / pre; px, py = torch_point(A)
        rr = np.sqrt((_GX - px) ** 2 + (_GY - py) ** 2); R = 60 + 2400 * ein(u, 2.2)
        cone = np.exp(-(rr / R) ** 2)[..., None]
        flare = cv2.GaussianBlur(np.exp(-((_GY - py) / 6) ** 2) * np.exp(-((_GX - px) / 600) ** 2), (0, 0), 3)[..., None] * u
        return np.clip(A + cone * (MOONW * 1.3) * ein(u, 1.3) + flare * MOONW * 0.6, 0, 1)
    v = (j + 1) / post; L = lum8(B)[..., None]
    reveal = np.clip((L - (1 - eout(v, 1.6)) * 1.05) * 5 + v * 1.2, 0, 1)
    white = (1 - eout(v, 1.8))
    return np.clip(B * reveal + MOONW * white * (1 - reveal * 0.5), 0, 1)

def blinds(A, B, j, f, sa, sb, pre=7, post=9):
    """venetian blinds: backlit slats rotate shut over the frame, then open on the next shot (staggered top->bottom)."""
    hs = 64.0; yl = np.mod(_GY, hs) - hs / 2; row = (_GY // hs) / (H / hs)
    if j < 0: ph = (j + pre + 1) / pre; base = A
    else: ph = 1 - (j + 1) / post; base = B
    ang = np.clip((ph * 1.35 - row * 0.35), 0, 1) * (math.pi / 2)
    half = (hs / 2) * np.sin(ang) + 0.5
    cov = np.clip((half - np.abs(yl)) * 1.2, 0, 1)
    tilt_ = np.clip(yl / np.maximum(half, 1), -1, 1)
    shade = 0.62 + 0.32 * np.cos(tilt_ * math.pi / 2) - 0.10 * tilt_
    slat = (shade[..., None] * np.array([0.50, 0.52, 0.55], np.float32)) * (0.70 + 0.30 * np.sin(ang))[..., None]
    gapl = np.exp(-((np.abs(yl) - half) / 1.6) ** 2) * np.sin(ang) ** 4                 # light leaking between the slats
    slat = slat + gapl[..., None] * MOONW * 0.6
    o = base * (1 - cov[..., None]) + slat * cov[..., None] + (gapl * (1 - cov))[..., None] * MOONW * 0.5
    return np.clip(o, 0, 1)

def roll(A, B, j, f, sa, sb, pre=8, post=9):
    """the world rolls over: the knife shot spins 90 deg with rotational blur and lands upside down on the floor."""
    if j < 0: u = (j + pre + 1) / pre; img, a0, a1 = A, 90 * ein(max(0, u - 0.18), 2.2), 90 * ein(u, 2.2)
    else: v = (j + 1) / post; img, a0, a1 = B, -90 * (1 - eout(max(0, v - 0.18), 2.2)), -90 * (1 - eout(v, 2.2))
    acc = None; n = 6
    for i in range(n):
        a = a0 + (a1 - a0) * i / (n - 1)
        w_ = zoom_about(img, W / 2, H / 2, 1.0 + 0.25 * abs(a) / 90, a)
        acc = w_ if acc is None else acc + w_
    return np.clip(acc / n, 0, 1)

def smear(A, B, j, f, sa, sb, pre=6, post=12):
    """step-printed smear (the song is "smeared, strobing"): the frame drags into long horizontal echoes, then settles."""
    if j < 0: u = (j + pre + 1) / pre; img = A; amt = ein(u, 1.6)
    else: v = (j + 1) / post; img = B; amt = 1 - eout(v, 1.8)
    acc = img.copy(); wsum = 1.0
    for i in range(1, 9):
        d = int(i * 34 * amt); wt = 0.82 ** i
        acc = acc + np.roll(img, d, 1) * wt; wsum += wt
    o = acc / wsum
    if j < 0 and u > 0.6: o = o * (1 - smooth((u - 0.6) / 0.4) * 0.5) + B * smooth((u - 0.6) / 0.4) * 0.5
    return np.clip(o * (1 + 0.25 * amt), 0, 1)

TR2.update({"tilt": (tilt, 12, 16), "foliage": (foliage, 10, 10), "petals": (petal_gust, 12, 14), "bloom": (bloom9, 18, 24),
            "strobe": (strobe, 3, 5), "beam": (beam, 8, 11), "blinds": (blinds, 7, 9), "roll": (roll, 8, 9), "smear": (smear, 6, 12)})

# ---- the loop: the drop of blood on the slide swells into the blood moon
DM_N = 30
def spot_screen(s, f):
    t, u, _ = src_time(s, f); img = sample(s["src"], t).astype(np.int16)
    x0, y0 = s["spot"]; r = 110
    sub = img[max(0, y0 - r):y0 + r, max(0, x0 - r):x0 + r]
    red = (sub[..., 2] - np.maximum(sub[..., 1], sub[..., 0])) > 55
    if red.sum() < 6: x, y, area = x0, y0, 200.0
    else:
        ys, xs = np.nonzero(red); x, y, area = xs.mean() + max(0, x0 - r), ys.mean() + max(0, y0 - r), float(red.sum())
    sx, sy, sc = to_screen(s, f, x, y)
    return sx, sy, math.sqrt(area / math.pi) * sc

def drop_moon(out, f, s):
    k = f - (s["f1"] - DM_N)
    if k < 0: return out
    u = (k + 1) / DM_N; sx, sy, rs = spot_screen(s, s["f1"] - DM_N)
    Z = math.exp(math.log(9.0) * ein(u, 2.0))
    cx = sx + (MOON_C[0] - sx) * smooth(u); cy = sy + (MOON_C[1] - sy) * smooth(u)
    M = cv2.getRotationMatrix2D((sx, sy), 0, Z); M[0, 2] += cx - sx; M[1, 2] += cy - sy
    z_ = cv2.warpAffine(out, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    z_ = radial_blur(z_, cx, cy, 1.0, 1.0 + 0.05 * math.sin(math.pi * u), 4)
    sky = moon_assets()["sky"]; dk = smooth((u - 0.35) / 0.65)
    bg = z_ * (1 - dk) + sky * dk
    R = max(rs * 1.2, 18) * Z; R = R + (MOON_R0 - R) * smooth((u - 0.2) / 0.8)
    o = blood_disc(bg, cx, cy, R, gloss=1 - smooth((u - 0.55) / 0.45), refr=z_)
    if u >= 1 - 1e-6: return moon_disc_frame()
    if u > 0.75:
        w_ = smooth((u - 0.75) / 0.25); o = o * (1 - w_) + moon_disc_frame() * w_
    return np.clip(o, 0, 1)

# ---- type: bold, high-contrast two-line captions; the NIGHT BLOOM / JASMINE hero title -----------------------------
F_CAP = F_BLACK
CAP_SCRIM = None
def cap_scrim(y0, y1, a):
    g = np.clip(1 - np.abs(_GY[:, :1] - (y0 + y1) / 2) / ((y1 - y0) / 2 + 160), 0, 1) ** 1.5
    return (1 - a * g)[..., None]

def text_cap(out, f, tx, person=None):
    t = f / FPS; words = tx["words"]; t_in = max(words[0][1], tx.get("from", -1))
    if t < t_in - 0.02 or t > tx["end"] + 0.01: return out
    big = tx.get("big"); sizes = (84, 110) if big else (76, 98); ys = (1372, 1490) if big else (1385, 1492)
    emph = tx.get("emph", []); fr = tx.get("from", -1)
    a_out = 1 - smooth((t - (tx["end"] - 0.16)) / 0.16)
    out = out * cap_scrim(ys[0] - 60, ys[1] + 60, 0.30 * a_out * smooth((t - t_in + 0.05) / 0.25))
    for ln in (0, 1):
        ws = [(w, max(wt, fr)) for w, wt, l in words if l == ln]
        if not ws: continue
        ims = [word_l(w, F_CAP, sizes[ln], CRIMSON * 1.05 if w in emph else WHITE, 1, 0.9, CRIMSON if w in emph else None) for w, _ in ws]
        gap = int(sizes[ln] * 0.28); widths = [im.shape[1] - 60 for im in ims]
        x = W / 2 - (sum(widths) + gap * (len(ims) - 1)) / 2
        for (w, wt), im, wd in zip(ws, ims, widths):
            v = eout(clamp((t - wt) / 0.17, 0, 1), 2.4)
            o_im = im if a_out > 0.98 else cv2.GaussianBlur(im, (0, 0), 0.1 + 5 * (1 - a_out))
            out = ease_word(out, o_im, x + wd / 2, ys[ln] - 14 * (1 - a_out), v, a_out, rise=28)
            x += wd + gap
    return out

def add_glow(out, x, y, r, amt, col):
    R_ = int(r * 2.6); xa, ya, xb, yb = max(0, int(x - R_)), max(0, int(y - R_)), min(W, int(x + R_)), min(H, int(y + R_))
    if xb <= xa or yb <= ya or amt <= 0: return out
    gy, gx = np.mgrid[ya:yb, xa:xb].astype(np.float32)
    out[ya:yb, xa:xb] += np.exp(-(((gx - x) ** 2 + (gy - y) ** 2) / (r * r)))[..., None] * col * amt
    return out

_HL = {}
def hero_letters(word, size, track=6):
    """letters on a shared baseline (v8 letter_set): [(char, mask cropped in x only, x-centre offset from the word centre)]."""
    key = (word, size, track)
    if key in _HL: return _HL[key]
    xs, ims, offs, wd = letter_set(word, F_CAP, size, track); out_ = []
    for c, xo, m, ox in zip([c for c in word if c != " "], xs, ims, offs):
        cols = np.nonzero(m.max(0) > 0.02)[0]
        if not len(cols): continue
        a, b = cols.min(), cols.max() + 1
        out_.append((c, m[:, a:b], xo - ox + (a + b) / 2 - wd / 2))
    _HL[key] = (out_, wd); return _HL[key]

def text_hero(out, f, tx, person=None):
    """NIGHT BLOOM / JASMINE: every letter blooms open from a point (scale, twist, blur -> sharp, a white flare behind
    it); JASMINE lands bigger, white-hot, then floods crimson from the bottom like blood; at the end the letters
    loosen into petals and blow away."""
    t = f / FPS; words = tx["words"]
    if t < words[0][1] - 0.02 or t > tx["end"] + 0.02: return out
    t_end = tx["end"]; spr = petal_sprites()
    out = out * cap_scrim(1250, 1620, 0.34 * (1 - smooth((t - t_end + 0.2) / 0.2)))
    lines = [("NIGHT BLOOM", 126, 1338, [w for w in words if w[2] == 0]), ("JASMINE", 182, 1520, [w for w in words if w[2] == 1])]
    lay = np.zeros((H, W, 4), np.float32)
    for text, size, yc, wl in lines:
        lets, _wd = hero_letters(text, size)
        starts = []
        if text == "NIGHT BLOOM":
            tN, tB = wl[0][1], wl[1][1]
            for i, (c, _, _) in enumerate(lets): starts.append(tN + 0.035 * i if i < 5 else tB + 0.035 * (i - 5))
        else:
            for i in range(len(lets)): starts.append(wl[0][1] + 0.03 * i)
        for i, (c, lm, xoff) in enumerate(lets):
            v = clamp((t - starts[i]) / 0.24, 0, 1)
            if v <= 0: continue
            ve = eout(v, 3.0); x = W / 2 + xoff; sc = 0.30 + 0.70 * ve + 0.06 * math.sin(math.pi * v) ; rot = (1 - ve) * (24 if i % 2 else -24)
            ex = clamp((t - (t_end - 0.30 + 0.018 * i)) / 0.26, 0, 1)                   # the exit: petals blow off the letters
            if ex >= 1: continue
            if text == "JASMINE":
                fill = eout(clamp((t - starts[i] - 0.12) / 0.32, 0, 1), 2.0)
                hh = lm.shape[0]; yy = np.linspace(1, 0, hh)[:, None]
                cmix = (yy < fill * 1.08).astype(np.float32); cmix = cv2.GaussianBlur(cmix, (0, 0), 3)
                col = np.broadcast_to(WHITE * (1 - cmix[..., None]) + CRIMSON * 1.08 * cmix[..., None], lm.shape + (3,)).copy()
            else:
                col = np.ones(lm.shape + (3,), np.float32) * WHITE
            pad = 26; lmp = np.pad(lm, pad); colp = np.pad(col, ((pad, pad), (pad, pad), (0, 0)), mode="edge")
            spr_l = np.dstack([colp, lmp]).astype(np.float32)
            draw_sprite(lay, spr_l, x, yc - 40 * ex, sc * (1 + 0.15 * ex), rot + 30 * ex * (1 if i % 2 else -1), 1.0,
                        (0.1 + 5 * (1 - ve) + 7 * ex) if (v < 1 or ex > 0) else 0.0, (1 - ex) * ve)
            fl = math.sin(math.pi * clamp(v / 0.7, 0, 1)) * 0.55
            if fl > 0.02: out = add_glow(out, x, yc, size * 0.55, fl * 0.35, JASMINE)
            if ex > 0:
                rng = np.random.default_rng(i * 13 + len(text))
                for q in range(3):
                    ang = rng.uniform(-2.6, -0.5); d = 260 * ex * rng.uniform(0.6, 1.4)
                    draw_sprite(lay, spr[(i + q) % 6], x + math.cos(ang) * d, yc + math.sin(ang) * d - 60 * ex, 0.35 + 0.3 * rng.random(),
                                rng.uniform(0, 360) + 400 * ex, math.cos(8 * ex + q), 1.0, math.sin(math.pi * ex))
    sh = cv2.GaussianBlur(lay[..., 3], (0, 0), 9)[..., None] * 0.65
    out = out * (1 - sh)
    out = out * (1 - lay[..., 3:4]) + lay[..., :3]
    return np.clip(out, 0, 1)

def text9(out, f, s, person=None):
    for tx in E.TEXT:
        if tx["style"] == "cap": out = text_cap(out, f, tx, person)
        elif tx["style"] == "hero": out = text_hero(out, f, tx, person)
    return out

# ---- montage accents: a soft strobe lift on every clap (beats 2 + 4) after the drop
CLAPS_E = [36, 40, 44, 48, 52, 56, 60, 62, 66, 68, 72]
def accents9(out, f):
    g = 0.0
    for ec in CLAPS_E:
        k = f - fh(ec)
        if 0 <= k < 10: g += 0.13 * math.exp(-k / 2.2)
    k = f - fh(E.HDROP)
    if 0 <= k < 14: g += 0.10 * math.exp(-k / 4)
    return out if g <= 0 else np.clip(out * (1 + g) + g * 0.10 * JASMINE, 0, 1)

# ---- shot pictures, the frame ----------------------------------------------------------------------------
def base9(s, f):
    person = None
    if s.get("graphic") == "moon": return moon_scene(f, s), None
    if s.get("seg"): img, person = render_shot(s, f, want_mask=True)
    else: img = render_shot(s, f)
    if s.get("freeze_e") is not None and f >= fh(s["freeze_e"]): img = freeze9(img, person, f, s)
    return img, person

_B9 = {}
def edge9(S_, which):
    key = (S_["n"], which)
    if key not in _B9:
        if len(_B9) > 6: _B9.clear()
        _B9[key] = base9(S_, S_["f0"] if which == "first" else S_["f1"] - 1)[0]
    return _B9[key]

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base9(s, f)
    if tin == "loop_in": out = loop_in(out, f, k) if k < 16 else out
    elif tin in TR2 and k < TR2[tin][2] and P is not None: out = TR2[tin][0](edge9(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge9(n_, "first"), kn, f, s, n_)
    if s.get("tout") == "drop_moon": out = drop_moon(out, f, s)
    if not (tin == "bloom" and k < 24): out = petals9(out, f, person)
    out = accents9(out, f)
    out = text9(out, f, s, person)
    out = finish9(out, f)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)

def init_hits():
    HITS.clear()
    if not hasattr(E, "E_SPLICE"): return                                             # (a new edit scaffolded from v9 sets its own hits)
    HITS.append((fh(E.HDROP), 16, 4.5)); HITS.append((fh(E.E_SPLICE), 7, 3.0)); HITS.append((fh(64), 11, 3.5))
    for e_ in (38, 42, 50): HITS.append((fh(e_), 6, 2.5))



# ============================================================================ v9 rev A — review pass 1 fixes
# moon: feathered, deeper blood moon, thin wisps; the loop goes THROUGH the drop of blood into the moon;
# fewer, larger petals that keep off his face; bold captions with a dark keyline; a petal-mosaic bloom (no starburst).

# ---- grade: less lavender on skin, more contrast, a slightly lower black floor
def lut9():
    global _LUT9
    if _LUT9 is None:
        x = np.linspace(0, 1, 1024, dtype=np.float32)
        y = PchipInterpolator([0, .06, .20, .50, .78, .93, 1], [0.022, 0.045, 0.165, 0.47, 0.775, 0.905, 0.958])(x)
        _LUT9 = (x, y.astype(np.float32))
    return _LUT9

def grade(img, s, f):
    if s.get("look") != "moonbloom": return _grade0(img, s, f)
    g, gains = corr9(s)
    x = np.clip(img * gains, 0, 1) ** g
    if s.get("ev"): x = np.clip(x * 2 ** s["ev"], 0, 1)
    lx, ly = lut9(); x = np.interp(x, lx, ly).astype(np.float32)
    Bc, Gc, Rc = x[..., 0], x[..., 1], x[..., 2]
    L = (Bc * 0.114 + Gc * 0.587 + Rc * 0.299)[..., None]
    blood = np.clip((Rc - 1.55 * np.maximum(Gc, Bc)) * 4.0, 0, 1)[..., None]
    hue = (Rc - Gc) / (Rc + 1e-3)
    skin = (np.clip(1 - np.abs(hue - 0.22) / 0.22, 0, 1) * np.clip((Rc - Bc) * 6, 0, 1) * np.clip(L[..., 0] * 3, 0, 1))[..., None]
    sat = 0.72 + 0.26 * skin + 0.60 * blood
    x = L + (x - L) * sat
    sh = (1 - L) ** 2.6 * (1 - 0.8 * skin); hi = L ** 2.0 * (1 - 0.6 * skin)
    x = x + sh * np.array([0.050, -0.008, 0.022], np.float32) + hi * np.array([0.018, 0.008, -0.012], np.float32)
    x = x + skin * L * np.array([-0.012, 0.002, 0.016], np.float32)                     # keep skin warm against the violet night
    x[..., 2:3] += blood * 0.04
    return np.clip(x, 0, 1)

# ---- the blood moon, rebuilt: feathered disc, deep orange-crimson, contrast; a zoomable layer; thin moonlit wisps
def moon_assets():
    if "img2" in _MOON: return _MOON
    cap = cv2.VideoCapture(E.SRC["p9"][0]); cap.set(cv2.CAP_PROP_POS_MSEC, 230.25 * 1000); ok, fr = cap.read(); cap.release()
    cx, cy, r = 576.6, 363.5, 242.0; Rc = int(r * 1.34)
    crop = fr[int(cy - Rc):int(cy + Rc), int(cx - Rc):int(cx + Rc)].astype(np.float32) / 255
    yy, xx = np.mgrid[0:crop.shape[0], 0:crop.shape[1]].astype(np.float32)
    d = np.sqrt((xx - Rc) ** 2 + (yy - Rc) ** 2); fm = np.clip((r * 1.005 - d) / (r * 0.035), 0, 1)[..., None]
    crop = crop * fm
    crop = np.clip((crop * np.array([0.50, 0.60, 1.00], np.float32) - 0.015) * 1.22, 0, 1) ** 1.08 * 0.86
    rng = np.random.default_rng(17); g = (_GY / H)[..., None]
    sky = SKYC * (1.10 - 0.55 * g)
    st = np.zeros((H, W), np.float32)
    for _ in range(110):
        x, y = rng.uniform(0, W), rng.uniform(0, H * 0.95); st[int(y), int(x)] = rng.uniform(0.2, 0.9) ** 2
    sky = sky + (cv2.GaussianBlur(st, (0, 0), 1.0) * 4.5)[..., None] * MOONW * 0.5
    nz = rng.standard_normal((H // 6, W // 3)).astype(np.float32)
    cl = cv2.resize(cv2.GaussianBlur(nz, (0, 0), 7), (W * 2, H), interpolation=cv2.INTER_CUBIC) + \
         0.35 * cv2.resize(cv2.GaussianBlur(nz[::-1].copy(), (0, 0), 2.5), (W * 2, H), interpolation=cv2.INTER_CUBIC)
    cl = (cl - cl.mean()) / (cl.std() + 1e-6)
    cl = cv2.resize(cv2.resize(cl, (W * 2, H // 3)), (W * 2, H))                          # stretched: long thin wisps
    _MOON.update(img2=crop, r=r, Rc=Rc, sky=sky.astype(np.float32), cloud=cl.astype(np.float32))
    _MOON.pop("disc", None)
    return _MOON

def moon_layer(cx, cy, R):
    M_ = moon_assets(); sc = R / M_["r"]; Rc = M_["Rc"]
    M = np.float32([[sc, 0, cx - sc * Rc], [0, sc, cy - sc * Rc]])
    return cv2.warpAffine(M_["img2"], M, (W, H), flags=cv2.INTER_CUBIC if sc > 1 else cv2.INTER_AREA, borderValue=(0, 0, 0))

def moon_scene(f, s, zoom=1.0):
    M_ = moon_assets(); u = (f - s["f0"]) / max(1, s["f1"] - s["f0"]); t = f / FPS
    R = MOON_R0 * (1 + 0.07 * u) * zoom; cx, cy = MOON_C[0], MOON_C[1] - 28 * u
    out = M_["sky"].copy() + moon_layer(cx, cy, R)
    dm = disc_mask(cx, cy, R, 3.0)
    halo = cv2.GaussianBlur(cv2.resize(dm, (W // 4, H // 4)), (0, 0), 16)
    out = out + cv2.resize(halo, (W, H))[..., None] * np.array([0.03, 0.07, 0.26], np.float32)
    sh = int((t * 30) % W); cl = M_["cloud"][:, sh:sh + W]
    ca = np.clip((cl - 0.9) * 0.55, 0, 0.42)[..., None]
    lit = np.clip(cv2.resize(cv2.GaussianBlur(cv2.resize(dm, (W // 4, H // 4)), (0, 0), 30), (W, H)) * 2.0, 0, 1)[..., None]
    out = out * (1 - ca * 0.6) + ca * (SKYC * 1.4 + lit * np.array([0.10, 0.16, 0.34], np.float32)) * 0.9
    return np.clip(out, 0, 1)

# ---- the loop: through the drop of blood on the slide into the blood moon (no drawn ball: a push into the real blood)
_ER = {}
def end_red():
    if "img" not in _ER:
        rr = np.sqrt((_GX - W / 2) ** 2 + (_GY - H * 0.47) ** 2)
        _ER["img"] = (CRIMSON * (0.42 + 0.30 * np.exp(-(rr / 760.0) ** 2))[..., None] + np.array([0.0, 0.0, 0.03], np.float32)).astype(np.float32)
    return _ER["img"]

DM_N = 28
def drop_moon(out, f, s):
    k = f - (s["f1"] - DM_N)
    if k < 0: return out
    u = (k + 1) / DM_N; sx, sy, rs = spot_screen(s, f)
    Z = math.exp(math.log(48.0) * ein(u, 2.3)); m_ = smooth(u)
    M = cv2.getRotationMatrix2D((sx, sy), 0, Z); M[0, 2] += (W / 2 - sx) * m_; M[1, 2] += (H * 0.47 - sy) * m_
    z_ = cv2.warpAffine(out, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    z_ = radial_blur(z_, W / 2, H * 0.47, 1.0, 1.0 + 0.16 * ein(u, 1.5), 5)
    L = lum8(z_)[..., None]; redd = CRIMSON * (0.30 + 0.9 * L)
    z_ = z_ * (1 - 0.6 * m_) + redd * 0.6 * m_
    tint = smooth((u - 0.5) / 0.5)
    return np.clip(z_ * (1 - tint) + end_red() * tint, 0, 1)

def loop_in(out, f, k, n=26):
    """frame 0 continues the last frame: out of the blood, the camera pulls back from inside the blood moon."""
    v = (k + 1) / n
    if v >= 1: return out
    s = shot_at(f); zoom = math.exp(math.log(14.0) * (1 - eout(v, 2.2)))
    mo = moon_scene(f, s, zoom)
    mo = radial_blur(mo, MOON_C[0], MOON_C[1], 1.0, 1.0 + 0.10 * (1 - v), 4)
    tint = 1 - smooth(v / 0.75)
    L = lum8(mo)[..., None]; mo = mo * (1 - 0.5 * tint) + CRIMSON * (0.35 + 0.8 * L) * 0.5 * tint
    return np.clip(mo * (1 - tint) + end_red() * tint, 0, 1)

def moon_disc_frame(): return end_red()

# ---- petals: fewer, larger, mostly far (behind him); the near ones are soft bokeh that keep clear of his face
PET_N = 24
def petal_sprites():
    if "list2" in _PET: return _PET["list2"]
    rng = np.random.default_rng(91); L_ = []
    for k in range(6):
        h, w = 170, 76
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); u = yy / (h - 1); v = (xx - (w - 1) / 2) / ((w - 1) / 2)
        bend = 0.10 * np.sin(np.pi * u) * (1 if k % 2 else -1)
        prof = (np.clip(np.sin(np.pi * np.clip(u, 0, 1) ** 0.62), 0, 1) ** 0.85) * (0.80 + 0.15 * rng.random())
        m = np.clip((prof - np.abs(v - bend)) * 10, 0, 1)
        shade = 0.78 + 0.22 * np.clip(1 - np.abs(v - bend), 0, 1) ** 0.5 - 0.10 * u + 0.06 * np.exp(-((v - bend) / 0.06) ** 2)
        col = JASMINE * shade[..., None]
        heel = np.clip(1 - u / 0.22, 0, 1)[..., None]
        col = col * (1 - 0.30 * heel) + np.array([0.60, 0.86, 0.82], np.float32) * 0.30 * heel
        L_.append(np.dstack([col, m * (0.92 - 0.10 * np.abs(v))]).astype(np.float32))
    _PET["list2"] = L_; return L_

def petal_params():
    if "p2" in _PF: return _PF["p2"]
    rng = np.random.default_rng(11); P_ = []
    for i in range(PET_N):
        z = rng.uniform(0.0, 1.0) ** 1.6 * 0.95 + 0.05
        P_.append(dict(z=z, x0=rng.uniform(0, 1), y0=rng.uniform(0, 1), ph=rng.uniform(0, 6.28), spin=rng.uniform(-45, 45),
                       fl=rng.uniform(0.9, 2.2), k=int(rng.integers(6)), rot0=rng.uniform(0, 360), on=rng.uniform(0, 1)))
    _PF["p2"] = P_; return P_

def petals9(out, f, person=None):
    d = petal_density(f)
    if d <= 0.01: return out
    t = petal_time(f); spr = petal_sprites(); s = shot_at(f)
    back = np.zeros((H, W, 4), np.float32); front = np.zeros((H, W, 4), np.float32)
    frozen = th(E.E_SIL) <= f / FPS < th(E.HDROP); drift = (f / FPS - th(E.E_SIL)) if frozen else 0.0
    fs = face_scr(s, f) if s.get("face") is not None and s.get("graphic") is None else None
    for p in sorted(petal_params(), key=lambda q: q["z"]):
        if p["on"] > d: continue
        z = p["z"]; sc = 0.22 + 0.85 * z ** 1.4
        span_x, span_y = W + 500, H + 500
        x = (p["x0"] * span_x + (25 + 50 * z) * t + 50 * math.sin(0.5 * t + p["ph"])) % span_x - 250
        y = (p["y0"] * span_y + (40 + 85 * z) * t) % span_y - 250
        if frozen:
            x = W / 2 + (x - W / 2) * (1 + 0.04 * z * drift); y = H * 0.45 + (y - H * 0.45) * (1 + 0.04 * z * drift)
        al = 0.50 + 0.40 * z; near = z >= 0.58
        if near and fs is not None:                                               # keep the soft near petals off his face
            dx, dy = (x - fs[0]) / (fs[2] * 0.55 + 1), (y - fs[1]) / (fs[2] * 0.75 + 1)
            al *= clamp((math.sqrt(dx * dx + dy * dy) - 0.85) / 0.4, 0, 1)
        if al <= 0.02: continue
        rot = p["rot0"] + p["spin"] * t; flip = math.cos(p["fl"] * t + p["ph"])
        draw_sprite(front if near else back, spr[p["k"]], x, y, sc, rot, flip, 0.0 if not near else 3 + (z - 0.58) * 22, al)
    if s.get("frame_petals"):                                                     # hero petals that frame (never cover) the face
        tl = max(0.0, min(t, th(E.E_SIL)) - s["t0"]); mir = s["n"] == "arthur"
        for i, (px, py, z) in enumerate(((110, 420, 0.7), (975, 330, 0.85), (70, 1250, 0.95), (1010, 1120, 0.75), (240, 1760, 1.0),
                                          (880, 1720, 0.8), (520, 90, 0.65), (40, 820, 0.6))):
            if mir: px, py = W - px, py + 60
            x = px + 14 * math.sin(0.6 * tl + i); y = py + (22 + 16 * z) * tl
            if frozen: x = W / 2 + (x - W / 2) * (1 + 0.05 * z * drift); y = H * 0.45 + (y - H * 0.45) * (1 + 0.05 * z * drift)
            draw_sprite(front, spr[i % 6], x, y, 0.35 + 0.75 * z, 40 * i + 18 * tl, math.cos(0.9 * tl + i), 1.0 + 7 * (z - 0.6), 0.75 * clamp((f - s["f0"]) / 12, 0, 1))
    if person is not None:
        back *= (1 - np.clip(person * 1.15, 0, 1))[..., None]
    for lay in (back, front):
        out = out * (1 - lay[..., 3:4]) + lay[..., :3]
    return np.clip(out, 0, 1)

# ---- footage: a gentle unsharp mask (720p sources upscaled ~2.7x), never on graphics
_base9_0 = base9
def base9(s, f):
    person = None
    if s.get("graphic") == "moon": return moon_scene(f, s), None
    if s.get("seg"): img, person = render_shot(s, f, want_mask=True)
    else: img = render_shot(s, f)
    img = np.clip(img + 0.45 * (img - cv2.GaussianBlur(img, (0, 0), 1.6)), 0, 1)
    if s.get("freeze_e") is not None and f >= fh(s["freeze_e"]): img = freeze9(img, person, f, s)
    return img, person

# ---- captions: heavy sans with a dark keyline + soft shadow; red emphasis that holds on any background; auto-fit
EMPH = np.array([0.20, 0.17, 1.00], np.float32)
_CW = {}
def cap_word(word, size, emph=False):
    key = (word, size, emph)
    if key in _CW: return _CW[key]
    m = text_mask(word, F_CAP, size, tracking=1); pad = 36; mm = np.pad(m, pad)
    k_ = max(3, int(size * 0.07)) | 1
    st_ = cv2.dilate(mm, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_, k_)))
    sh = np.roll(cv2.GaussianBlur(mm, (0, 0), size * 0.13), int(size * 0.05), 0) * 0.85
    a = np.maximum(np.maximum(mm, st_ * 0.92), sh)
    col = np.zeros(mm.shape + (3,), np.float32) + np.array([0.025, 0.018, 0.03], np.float32)
    face_c = EMPH if emph else WHITE
    col = col * (1 - mm[..., None]) + face_c * mm[..., None]
    if emph:
        g = cv2.GaussianBlur(mm, (0, 0), size * 0.18) * 0.55
        col = col + EMPH * g[..., None] * (1 - st_[..., None]) * 1.2; a = np.maximum(a, g)
    L = np.dstack([col, a]).astype(np.float32)
    _CW[key] = L; return L

def text_cap(out, f, tx, person=None):
    t = f / FPS; words = tx["words"]; t_in = max(words[0][1], tx.get("from", -1))
    if t < t_in - 0.02 or t > tx["end"] + 0.01: return out
    big = tx.get("big"); sizes = [92, 120] if big else [88, 114]; ys = (1368, 1492) if big else (1380, 1496)
    emph = tx.get("emph", []); fr = tx.get("from", -1)
    a_out = 1 - smooth((t - (tx["end"] - 0.16)) / 0.16)
    out = out * cap_scrim(ys[0] - 70, ys[1] + 70, 0.34 * a_out * smooth((t - t_in + 0.05) / 0.25))
    for ln in (0, 1):
        ws = [(w, max(wt, fr)) for w, wt, l in words if l == ln]
        if not ws: continue
        sz = sizes[ln]
        for _ in range(6):                                                         # auto-fit the line to 940 px
            ims = [cap_word(w, sz, w in emph) for w, _ in ws]
            gap = int(sz * 0.26); widths = [im.shape[1] - 72 for im in ims]
            tot = sum(widths) + gap * (len(ims) - 1)
            if tot <= 940: break
            sz = int(sz * 940 / tot) - 1
        x = W / 2 - tot / 2
        for (w, wt), im, wd in zip(ws, ims, widths):
            v = eout(clamp((t - wt) / 0.17, 0, 1), 2.4)
            o_im = im if a_out > 0.98 else cv2.GaussianBlur(im, (0, 0), 0.1 + 5 * (1 - a_out))
            out = ease_word(out, o_im, x + wd / 2, ys[ln] - 14 * (1 - a_out), v, a_out, rise=30)
            x += wd + gap
    return out

# ---- the foliage strip: feathered ends, moonlit leaf edges, a few jasmine clusters
def foliage_strip():
    if "rgba2" in _FOL: return _FOL["rgba2"]
    rng = np.random.default_rng(29); Ls = int(3.4 * W); h2, w2 = H // 2, Ls // 2
    acc = np.zeros((h2, w2, 4), np.float32)
    for i in range(650):
        x = rng.uniform(0, w2)
        core = W * 0.45 <= x <= W * 1.30
        if not core and rng.random() < 0.6: continue
        y = rng.uniform(-60, h2 + 60); L_ = rng.uniform(90, 240); Wd = L_ * rng.uniform(0.30, 0.46); ang = rng.uniform(0, 180)
        lay = np.zeros((h2, w2), np.float32)
        cv2.ellipse(lay, (int(x), int(y)), (int(L_ / 2), int(Wd / 2)), ang, 0, 360, 1.0, -1, cv2.LINE_AA)
        sh = rng.uniform(0.5, 1.0)
        col = np.array([0.030, 0.070, 0.040], np.float32) * sh
        a = lay[..., None]; acc[..., :3] = acc[..., :3] * (1 - a) + col * a; acc[..., 3:4] = np.maximum(acc[..., 3:4], a)
        rim = cv2.ellipse(np.zeros((h2, w2), np.float32), (int(x), int(y)), (int(L_ / 2), int(Wd / 2)), ang, 200, 300, 1.0, 3, cv2.LINE_AA)
        acc[..., :3] += rim[..., None] * np.array([0.10, 0.11, 0.09], np.float32) * rng.uniform(0.3, 1.0)
    for i in range(26):
        x = rng.uniform(W * 0.35, W * 1.4); y = rng.uniform(40, h2 - 40); r = rng.uniform(22, 44); rot = rng.uniform(0, 72)
        lay = np.zeros((h2, w2), np.float32)
        for q in range(5):
            a_ = math.radians(rot + 72 * q)
            cv2.ellipse(lay, (int(x + 0.6 * r * math.cos(a_)), int(y + 0.6 * r * math.sin(a_))), (int(r * 0.6), int(r * 0.30)), math.degrees(a_), 0, 360, 1.0, -1, cv2.LINE_AA)
        a = lay[..., None] * 0.95; acc[..., :3] = acc[..., :3] * (1 - a) + JASMINE * 0.85 * a; acc[..., 3:4] = np.maximum(acc[..., 3:4], a)
        cv2.circle(acc, (int(x), int(y)), int(r * 0.16), (0.30, 0.75, 0.90, 1.0), -1, cv2.LINE_AA)
    acc = cv2.GaussianBlur(acc, (0, 0), 7)
    acc[..., 3] = np.clip(acc[..., 3] * 1.3, 0, 1)
    xx = np.arange(w2, dtype=np.float32)[None, :]
    taper = np.clip(xx / (W * 0.30), 0, 1) * np.clip((w2 - xx) / (W * 0.30), 0, 1)
    acc[..., 3] *= taper
    _FOL["rgba2"] = cv2.resize(acc, (Ls, H), interpolation=cv2.INTER_LINEAR); return _FOL["rgba2"]

# ---- HERO: the frozen frame breaks into jasmine petals (petal-shaped cells of the image) that bloom out toward the lens
_BP = {}
def bloom_cells():
    if "lab" in _BP: return _BP
    rng = np.random.default_rng(5); cx, cy = BLOOM_C; pts = []
    for yy in np.arange(-60, H + 120, 168):
        for xx in np.arange(-60, W + 120, 132):
            pts.append((xx + rng.uniform(-40, 40) + (66 if int(yy / 168) % 2 else 0), yy + rng.uniform(-40, 40)))
    pts = np.array(pts, np.float32); n = len(pts)
    ang = np.arctan2(pts[:, 1] - cy, pts[:, 0] - cx) + rng.uniform(-0.5, 0.5, n)          # petals point away from the heart
    hs = 2; gy, gx = np.mgrid[0:H // hs, 0:W // hs].astype(np.float32); gy *= hs; gx *= hs
    best = np.full(gy.shape, 1e9, np.float32); lab = np.zeros(gy.shape, np.int32)
    for i, (px, py) in enumerate(pts):
        dx, dy = gx - px, gy - py; c, s_ = math.cos(ang[i]), math.sin(ang[i])
        a_ = dx * c + dy * s_; b_ = -dx * s_ + dy * c
        d = (a_ / 1.55) ** 2 + (b_ / 0.80) ** 2                                             # elongated cells: petal-like
        m = d < best; best[m] = d[m]; lab[m] = i
    lab = cv2.resize(lab.astype(np.float32), (W, H), interpolation=cv2.INTER_NEAREST).astype(np.int32)
    boxes = []
    for i in range(n):
        ys, xs = np.nonzero(lab == i)
        boxes.append((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1) if len(xs) else None)
    edges = cv2.morphologyEx(lab.astype(np.float32), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
    dist = np.sqrt((pts[:, 0] - cx) ** 2 + (pts[:, 1] - cy) ** 2)
    _BP.update(lab=lab, pts=pts, ang=ang, boxes=boxes, edges=cv2.GaussianBlur(edges.astype(np.float32), (0, 0), 1.2),
               delay=dist / dist.max() * 0.42 + rng.uniform(0, 0.08, n), spd=rng.uniform(0.6, 1.4, n), spin=rng.uniform(-260, 260, n),
               flip=rng.uniform(2.6, 4.2, n), sz=rng.uniform(1.55, 1.95, n))
    return _BP

def bloom9(A, B, j, f, sa, sb, pre=14, post=26):
    """HERO (the drop): the frozen frame bursts into jasmine petals from its heart outward; each petal carries its piece
    of the picture, tumbles toward the lens and shows its white back; the kill is behind them."""
    BP = bloom_cells(); cx, cy = BLOOM_C
    if j < 0:                                                                          # the bud swells with light
        u = clamp((j + pre + 1) / pre, 0, 1)
        rr = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2)
        swell = np.exp(-(rr / (500 + 900 * u)) ** 2)[..., None] * 0.20 * u ** 2
        return np.clip(zoom_about(A, cx, cy, 1 + 0.025 * ein(u, 2)) + swell * JASMINE, 0, 1)
    v = (j + 1) / post
    zb = 1.0 + 0.28 * (1 - eout(v, 2.2)); Bz = zoom_about(B, cx, cy, zb)
    if v < 0.45: Bz = radial_blur(Bz, cx, cy, 1.0, 1.0 + 0.09 * (1 - v / 0.45), 5)
    q = np.clip((v - BP["delay"]) / 0.50, 0, 1)
    still = cv2.GaussianBlur((q <= 0)[BP["lab"]].astype(np.float32), (0, 0), 3.0)[..., None]
    rr0 = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2)
    glow = (np.exp(-(rr0 / (350 + 1300 * v)) ** 2) * (1 - smooth(v / 0.55)))[..., None]          # light pours through the gaps
    out = (Bz + glow * JASMINE * 0.85) * (1 - still) + zoom_about(A, cx, cy, 1.025) * still
    lay = np.zeros((H, W, 4), np.float32); A2 = zoom_about(A, cx, cy, 1.025)
    for i in np.argsort(q):
        if q[i] <= 0 or BP["boxes"][i] is None: continue
        x0, y0, x1, y1 = BP["boxes"][i]; qi = q[i]
        pad = 14; x0, y0, x1, y1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)
        bw, bh = x1 - x0, y1 - y0; m = np.zeros((bh, bw), np.float32)
        ang = math.degrees(BP["ang"][i]); px, py = BP["pts"][i]
        cv2.ellipse(m, (int(px - x0), int(py - y0)), (int(76 * BP["sz"][i]), int(44 * BP["sz"][i])), ang, 0, 360, 1.0, -1, cv2.LINE_AA)
        m = cv2.GaussianBlur(m, (0, 0), 1.6)
        tex = np.clip(A2[y0:y1, x0:x1] * (1 + 1.4 * qi) + JASMINE * 0.35 * min(1, qi * 4), 0, 1)
        fl = math.cos(math.pi * min(1, qi * 1.6) * BP["flip"][i] / 2.6)
        if fl < 0:                                                                     # the white back of the petal
            gx_ = (np.arange(bw, dtype=np.float32)[None, :] - (px - x0)); gy_ = (np.arange(bh, dtype=np.float32)[:, None] - (py - y0))
            sh = 0.80 + 0.20 * np.exp(-(gx_ ** 2 + gy_ ** 2) / (2 * 50.0 ** 2))
            tex = tex * 0.18 + JASMINE * 0.84 * sh[..., None]
        spr = np.dstack([tex, m]).astype(np.float32)
        dx, dy = px - cx, py - cy; dn = math.hypot(dx, dy) + 1e-3
        travel = ein(qi, 1.7) * (650 + 950 * BP["spd"][i])
        x = (x0 + x1) / 2 + dx / dn * travel; y = (y0 + y1) / 2 + dy / dn * travel - 180 * ein(qi, 2)
        draw_sprite(lay, spr, x, y, 1 + 1.8 * ein(qi, 2.0), BP["spin"][i] * qi, fl, 0.5 + 9 * qi, 1 - smooth((qi - 0.62) / 0.38))
    out = out * (1 - lay[..., 3:4]) + lay[..., :3]
    rr = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2)
    out = out + np.exp(-(rr / (200 + 1100 * v)) ** 2)[..., None] * JASMINE * 0.30 * (1 - v) ** 2
    return np.clip(out, 0, 1)

def beam(A, B, j, f, sa, sb, pre=8, post=11):
    if j < 0:
        u = (j + pre + 1) / pre; px, py = torch_point(A)
        rr = np.sqrt((_GX - px) ** 2 + (_GY - py) ** 2); R = 60 + 2600 * ein(u, 2.0)
        cone = np.exp(-(rr / R) ** 2)[..., None]
        flare = cv2.GaussianBlur(np.exp(-((_GY - py) / 6) ** 2) * np.exp(-((_GX - px) / 650) ** 2), (0, 0), 3)[..., None] * u
        return np.clip(A + cone * MOONW * 1.6 * ein(u, 1.2) + flare * MOONW * 0.7, 0, 1)
    v = (j + 1) / post; L = lum8(B)[..., None]
    reveal = np.clip((L - (1 - eout(v, 1.4)) * 0.9) * 5 + v * 2.2, 0, 1)
    white = (1 - eout(v, 1.3))
    return np.clip(B * reveal + MOONW * 1.15 * white * (1 - reveal * 0.7), 0, 1)

TR2.update({"bloom": (bloom9, 14, 26), "beam": (beam, 8, 8)})

def shutter(A, B, j, f, sa, sb, pre=5, post=10):
    """the music stops dead: a camera shutter (six gunmetal blades) snaps shut over the outgoing shot and opens on the
    frozen one, like the photograph of a moment."""
    if j < 0: u = (j + pre + 1) / pre; img = A; r = 1200 * (1 - ein(u, 1.7)); rot = 0.55 * u
    else: v = (j + 1) / post; img = B; r = 1200 * eout(v, 2.3); rot = 0.55 + 0.5 * v
    sd = aperture(max(r, 0.0), rot); m = np.clip(sd / 2.0, 0, 1)[..., None]
    rr, aa = polar(); seg = 2 * math.pi / 6; a = np.mod(aa - rot, seg) / seg
    metal = (0.045 + 0.075 * a + 0.03 * np.clip(1 - rr / 1100, 0, 1))[..., None] * np.array([1.05, 1.0, 0.95], np.float32)
    seam = np.exp(-((a - 0.0) * seg * np.maximum(rr, 1) / 2.0) ** 2)[..., None] * 0.10
    edge = np.exp(-(sd / 3.0) ** 2)[..., None] * MOONW * 0.55
    o = img * m + (metal + seam) * (1 - m) + edge * (1 - m * 0.5)
    return np.clip(o, 0, 1)

TR2["shutter"] = (shutter, 5, 10)
LOOPIN_N = 26
def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base9(s, f)
    if tin == "loop_in": out = loop_in(out, f, k, LOOPIN_N) if k < LOOPIN_N else out
    elif tin in TR2 and k < TR2[tin][2] and P is not None: out = TR2[tin][0](edge9(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge9(n_, "first"), kn, f, s, n_)
    if s.get("tout") == "drop_moon": out = drop_moon(out, f, s)
    if not (tin == "bloom" and k < TR2["bloom"][2]): out = petals9(out, f, person)
    out = accents9(out, f)
    out = text9(out, f, s, person)
    out = finish9(out, f)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)

def spot_screen(s, f):
    t, u, _ = src_time(s, f); img = sample(s["src"], t).astype(np.int16)
    x0, y0 = s["spot"]; r = 110
    sub = img[max(0, y0 - r):y0 + r, max(0, x0 - r):x0 + r]
    red = ((sub[..., 2] - np.maximum(sub[..., 1], sub[..., 0])) > 90) & (sub[..., 2] > 120)
    if red.sum() < 6: x, y, area = x0, y0, 200.0
    else:
        ys, xs = np.nonzero(red); x, y, area = xs.mean() + max(0, x0 - r), ys.mean() + max(0, y0 - r), float(red.sum())
    sx, sy, sc = to_screen(s, f, x, y)
    return sx, sy, math.sqrt(area / math.pi) * sc


# ============================================================================ v10 — LET IT HAPPEN: prism-speed toolkit
# The Flash: graphite-slate shadows, rich suit crimson, white-gold lightning with bloom, a prismatic time-slice on the
# fastest moments. Lightning effects are tied to the footage: arcs crawl along his MODNet silhouette, bolts start and end
# at his tracked position, the drop goes through his own chest emblem.
th, fh = E.th, E.fh
GOLDW = np.array([0.62, 0.90, 1.00], np.float32)       # BGR white-gold lightning core
GOLD2 = np.array([0.18, 0.66, 1.00], np.float32)       # BGR deep gold
EMBER2 = np.array([0.08, 0.36, 1.00], np.float32)      # BGR speed-force orange
STEEL = np.array([0.62, 0.55, 0.50], np.float32)       # BGR frozen-time steel
SLATE = np.array([0.20, 0.15, 0.12], np.float32)       # BGR graphite-slate

# ---- grade: PRISM SPEED
_LUT10 = None
def lut10():
    global _LUT10
    if _LUT10 is None:
        x = np.linspace(0, 1, 1024, dtype=np.float32)
        y = PchipInterpolator([0, .05, .20, .50, .80, .94, 1], [0.018, 0.040, 0.170, 0.485, 0.800, 0.925, 0.970])(x)
        _LUT10 = (x, y.astype(np.float32))
    return _LUT10

_grade9 = grade
def grade(img, s, f):
    if s.get("look") != "prism": return _grade9(img, s, f)
    g, gains = corr9(s)
    x = np.clip(img * gains, 0, 1) ** g
    if s.get("ev"): x = np.clip(x * 2 ** s["ev"], 0, 1)
    lx, ly = lut10(); x = np.interp(x, lx, ly).astype(np.float32)
    Bc, Gc, Rc = x[..., 0], x[..., 1], x[..., 2]
    L = (Bc * 0.114 + Gc * 0.587 + Rc * 0.299)[..., None]
    red = np.clip((Rc - np.maximum(Gc, Bc) * 1.25) * 3.0, 0, 1)[..., None]                     # the suit
    light = np.clip((L - 0.62) * 3.0, 0, 1) * np.clip((Rc - Bc) * 3.0, 0, 1)[..., None]          # orange/gold lightning
    hue = (Rc - Gc) / (Rc + 1e-3)
    skin = (np.clip(1 - np.abs(hue - 0.22) / 0.22, 0, 1) * np.clip((Rc - Bc) * 6, 0, 1) * np.clip(L[..., 0] * 3, 0, 1))[..., None]
    sat = 0.78 + 0.30 * red + 0.25 * light + 0.18 * skin
    x = L + (x - L) * sat
    sh = (1 - L) ** 2.4 * (1 - 0.7 * skin) * (1 - red)
    x = x + sh * np.array([0.040, 0.012, -0.012], np.float32) + light * np.array([-0.02, 0.02, 0.03], np.float32)
    return np.clip(x, 0, 1)

def finish10(out, f):
    small = cv2.resize(out, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi = np.clip(small.max(2) - 0.62, 0, 1)
    b1 = cv2.GaussianBlur(hi, (0, 0), 4); b2 = cv2.GaussianBlur(hi, (0, 0), 16)
    out = out + cv2.resize(b1 * 0.45 + b2 * 0.55, (W, H))[..., None] * GOLD2 * 0.50
    out = anamorphic(out, 0.20)
    out = np.maximum(out, 0.016)
    return np.clip(out * (0.82 + 0.18 * VIG) + grain(f, 0.013), 0, 1)

# ---- lightning drawing (one canvas per frame, one glow pass)
def bolt_canvas():
    return np.zeros((H, W), np.uint8)

def put_bolt(cv, p0, p1, seed, width=3, rough=0.28, depth=6, branch=1, val=255):
    pts = bolt_points(p0, p1, seed, rough, depth)
    cv2.polylines(cv, [pts.astype(np.int32)], False, val, width, cv2.LINE_AA)
    rng = np.random.default_rng(seed + 7)
    for j in range(branch):
        i = int(rng.integers(len(pts) // 5, max(len(pts) // 5 + 1, len(pts) - 4))); q0 = pts[i]
        d = pts[-1] - pts[0]; ang = math.atan2(d[1], d[0]) + rng.uniform(-1.0, 1.0)
        L_ = np.linalg.norm(d) * rng.uniform(0.25, 0.5); q1 = q0 + L_ * np.array([math.cos(ang), math.sin(ang)], np.float32)
        cv2.polylines(cv, [bolt_points(q0, q1, seed + 31 + j, rough, depth - 2).astype(np.int32)], False, int(val * 0.7), max(1, width - 1), cv2.LINE_AA)
    return pts

def light_from(cv, a=1.0, col=None):
    c = cv.astype(np.float32) / 255
    small = cv2.resize(c, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    glow = cv2.resize(cv2.GaussianBlur(small, (0, 0), 3) * 2.6 + cv2.GaussianBlur(small, (0, 0), 11) * 3.4, (W, H), interpolation=cv2.INTER_LINEAR)
    col = GOLD2 if col is None else col
    return (np.clip(glow, 0, 1.6)[..., None] * col * 0.85 + c[..., None] * GOLDW * 1.15) * a

def subject_point(s, f, person=None):
    fs = face_scr(s, f) if s.get("face") is not None else None
    if fs: return fs[0], min(H * 0.92, fs[1] + fs[2] * 1.7)                          # chest, never the face
    if person is not None and person.max() > 0.3:
        ys, xs = np.nonzero(person[::8, ::8] > 0.5)
        if len(xs): return float(xs.mean() * 8), float(ys.mean() * 8)
    return W / 2, H * 0.5

def face_box(s, f):
    """(x0, x1, y_floor) of the face on screen; lightning stays below y_floor or outside x0..x1."""
    fs = face_scr(s, f) if s.get("face") is not None else None
    if not fs: return None
    return fs[0] - fs[2] * 0.75, fs[0] + fs[2] * 0.75, fs[1] + fs[2] * 0.85

def keep_off_face(pt, box):
    if box is None: return pt
    x, y = pt
    if box[0] < x < box[1] and y < box[2]: y = box[2]
    return (x, y)

# ---- the Speed Force crawling over his silhouette (arcs born on the matte edge)
_EDGE = {}
def edge_arcs(out, f, person, amt, seed0=0):
    if person is None or amt <= 0.01: return out
    pm = (person > 0.5).astype(np.uint8)
    if pm.sum() < 2000: return out
    edge = cv2.morphologyEx(pm[::4, ::4], cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
    ys, xs = np.nonzero(edge)
    if len(xs) < 10: return out
    rng = np.random.default_rng(f // 2 * 13 + seed0)
    n = int(2 + 5 * amt); cv = bolt_canvas()
    cy_, cx_ = ys.mean() * 4, xs.mean() * 4
    for k in range(n):
        i = int(rng.integers(len(xs))); x0, y0 = xs[i] * 4.0, ys[i] * 4.0
        dx, dy = x0 - cx_, y0 - cy_; dn = math.hypot(dx, dy) + 1e-3
        ang = math.atan2(dy, dx) + rng.uniform(-1.4, 1.4); L_ = rng.uniform(70, 210) * (0.6 + 0.6 * amt)
        x1, y1 = x0 + math.cos(ang) * L_, y0 + math.sin(ang) * L_
        put_bolt(cv, (x0, y0), (x1, y1), f // 2 * 101 + k + seed0, width=2 if rng.random() < 0.7 else 3, rough=0.30, depth=5, branch=int(rng.random() < 0.5))
    flick = 0.65 + 0.35 * math.sin(f * 1.7 + seed0)
    return np.clip(out + light_from(cv, amt * flick), 0, 1)

# ---- afterimages: the subject's own past positions (matte cutouts of earlier frames), tinted gold -> ember
def afterimages(out, s, f, person, amt, n=3, step=4):
    if person is None or amt <= 0.01: return out
    cur = np.clip(person * 1.2, 0, 1)[..., None]; acc = np.zeros_like(out); aacc = np.zeros(out.shape[:2] + (1,), np.float32)
    cols = (GOLDW, GOLD2, EMBER2)
    for k in range(1, n + 1):
        fk = f - k * step
        if fk < s["f0"]: break
        img_k, m_k = render_shot(s, fk, with_shake=False, want_mask=True)
        a = (0.55 / k ** 0.8) * amt; m = np.clip(m_k * 1.2, 0, 1)[..., None] * (1 - cur)
        L = lum8(img_k)[..., None]
        tint = img_k * 0.35 + L * cols[min(k - 1, 2)] * 0.9
        acc = acc + tint * m * a; aacc = aacc + m * a
    aacc = np.clip(aacc, 0, 0.85)
    return np.clip(out * (1 - aacc) + acc + out * 0, 0, 1)

# ---- prismatic time-slice: the three colour channels from three moments
def time_slice(s, f, img, amt, d=3, dx=0):
    if amt <= 0.01: return img
    a = render_shot(s, max(s["f0"], f - d), with_shake=False); b = render_shot(s, max(s["f0"], f - 2 * d), with_shake=False)
    o = img.copy()
    o[..., 1] = img[..., 1] * (1 - amt) + np.roll(a[..., 1], int(dx * amt), 1) * amt
    o[..., 0] = img[..., 0] * (1 - amt) + np.roll(b[..., 0], int(2 * dx * amt), 1) * amt
    return o

# ---- the frozen world: steel mono except Barry and the lightning, gold sparks hanging in the air
_SPK = {}
def spark_field():
    if "p" in _SPK: return _SPK["p"]
    rng = np.random.default_rng(23)
    _SPK["p"] = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.2, 1.0), rng.uniform(0, 6.28)) for _ in range(70)]
    return _SPK["p"]

def frozen_world(img, person, f, s, amt):
    if amt <= 0.01: return img
    L = lum8(img)[..., None]
    light = np.clip((L - 0.55) * 3.0, 0, 1) * np.clip((img[..., 2:3] - img[..., 0:1]) * 3.0, 0, 1)
    keep = np.clip(light * 1.2, 0, 1)                                        # only the lightning stays alive
    mono = L * STEEL * 1.05 + SLATE * 0.05
    o = img * keep + (img * (1 - amt) + mono * amt) * (1 - keep)
    k = f - s["f0"]; cv = np.zeros((H, W), np.float32)
    for (x, y, z, ph) in spark_field():
        xx = x + (x - W / 2) * 0.03 * z * k / 30; yy = y + (y - H / 2) * 0.03 * z * k / 30
        r = 1.2 + 2.8 * z
        cv2.circle(cv, (int(xx), int(yy)), int(r), 0.6 + 0.4 * z, -1, cv2.LINE_AA)
    sp = cv2.GaussianBlur(cv, (0, 0), 1.6) * 1.4 + cv2.GaussianBlur(cv, (0, 0), 7) * 1.2
    return np.clip(o + sp[..., None] * GOLD2 * amt * 0.8, 0, 1)

def is_frozen(s, f):
    if not s.get("frozen"): return 0.0
    t, u, sp = src_time(s, f)
    return 1.0 if sp < 0.05 else 0.0

# ---- transitions -------------------------------------------------------------------------------------------
def arc_link(A, B, j, f, sa, sb, pre=6, post=9):
    """a lightning arc leaps from him in the outgoing shot to him in the next; the cut hides in its flash."""
    pa = subject_point(sa, sa["f1"] - 1); pb = subject_point(sb, sb["f0"])
    if j < 0:
        u = (j + pre + 1) / pre; cv = bolt_canvas()
        side = 1 if pa[0] < W / 2 else -1
        tip = (pa[0] + (pb[0] - pa[0]) * ein(u, 1.4) + side * 380 * math.sin(math.pi * u), pa[1] + (pb[1] - pa[1]) * ein(u, 1.4) + 160 * math.sin(math.pi * u))
        bx = face_box(sa, f); tip = keep_off_face(tip, bx); pa = keep_off_face(pa, bx)
        put_bolt(cv, pa, tip, 900 + f, width=3, rough=0.18, depth=6, branch=1)
        return np.clip(A * (1 - 0.25 * u) + light_from(cv, 0.6 + 0.6 * u), 0, 1)
    v = (j + 1) / post; cv = bolt_canvas(); side = 1 if pa[0] < W / 2 else -1
    mid = ((pa[0] + pb[0]) / 2 + side * 380, (pa[1] + pb[1]) / 2 + 160)
    bx = face_box(sb, f); mid = keep_off_face(mid, bx); pb = keep_off_face(pb, bx); pa = keep_off_face(pa, bx)
    put_bolt(cv, pa, mid, 950 + f // 2, width=4, rough=0.22, depth=6, branch=2); put_bolt(cv, mid, pb, 960 + f // 2, width=4, rough=0.22, depth=6, branch=1)
    fl = (1 - eout(v, 2.0))
    return np.clip(B * (0.75 + 0.25 * v) + light_from(cv, 1.4 * fl) + fl * 0.18 * GOLD2, 0, 1)

def ignite(A, B, j, f, sa, sb, pre=8, post=10):
    """the room goes dark; then his eyes ignite and the lightning flares up around him, brightest first."""
    if j < 0: return np.clip(A * (1 - ein((j + pre + 1) / pre, 1.3) * 0.92), 0, 1)
    v = (j + 1) / post; L = lum8(B)[..., None]
    reveal = np.clip((L - (1 - eout(v, 1.6)) * 0.85) * 4 + v * 1.1, 0, 1)
    cv = bolt_canvas(); p = subject_point(sb, f)
    if j < 6:
        for k, dx in enumerate((-1, 1)):
            x0 = clamp(p[0] + dx * 400, 60, W - 60); put_bolt(cv, (x0 + dx * 40, -30), (x0, p[1] + 260), 970 + k + j, 3, 0.3, 6, 1)
    return np.clip(B * reveal + light_from(cv, (1 - v) * 1.2), 0, 1)

def emblem_shape(cx, cy, r):
    """the Flash emblem (ring + bolt) as masks, centred at (cx, cy) with radius r."""
    ring = np.zeros((H, W), np.float32); cv2.circle(ring, (int(cx), int(cy)), int(r), 1.0, max(2, int(r * 0.09)), cv2.LINE_AA)
    disc = np.zeros((H, W), np.float32); cv2.circle(disc, (int(cx), int(cy)), int(r), 1.0, -1, cv2.LINE_AA)
    P = np.array([(0.18, -0.92), (-0.46, 0.08), (-0.04, 0.08), (-0.20, 0.92), (0.48, -0.14), (0.05, -0.14)], np.float32)
    bolt = np.zeros((H, W), np.float32); cv2.fillPoly(bolt, [np.stack([cx + P[:, 0] * r, cy + P[:, 1] * r], 1).astype(np.int32)], 1.0, cv2.LINE_AA)
    return ring, disc, bolt

def emblem_gate(A, B, j, f, sa, sb, pre=20, post=22):
    """HERO 1 (the drop): his chest emblem flares, arcs crawl out across the suit, the camera dives into the bolt;
    on the drop the bolt becomes a gate and the next shot bursts through it."""
    def emb_at(fr):
        t_, _, _ = src_time(sa, fr); ks = sa["emblem"]
        return float(np.interp(t_, [q[0] for q in ks], [q[1] for q in ks])), float(np.interp(t_, [q[0] for q in ks], [q[2] for q in ks]))
    er = sa.get("emblem_r", 34)
    if j < 0:
        u = (j + pre + 1) / pre
        ex, ey = emb_at(f); cx, cy, sc = to_screen(sa, f, ex, ey); r = er * sc
        Z = math.exp(math.log(9.0) * ein(max(0, u - 0.45) / 0.55, 2.3))
        ring, disc, bolt = emblem_shape(cx, cy, r)
        glow = cv2.GaussianBlur(bolt + ring * 0.6, (0, 0), 6 + 18 * u)
        o = A + (bolt[..., None] * GOLDW * (0.4 + 1.2 * u) + glow[..., None] * GOLD2 * (0.6 + 1.8 * u)) * smooth(u / 0.4)
        cv = bolt_canvas()
        for k in range(int(2 + 6 * u)):                                              # arcs crawl outward over the suit
            a_ = (k * 2.39 + f * 0.7) % 6.283; L_ = r * (1.4 + 4.5 * u)
            put_bolt(cv, (cx + math.cos(a_) * r, cy + math.sin(a_) * r), (cx + math.cos(a_ + 0.3) * L_, cy + math.sin(a_ + 0.3) * L_ * 0.7),
                     1100 + k + f, 2, 0.3, 5, 1)
        o = o + light_from(cv, 0.5 + 0.7 * u)
        if Z > 1.01:
            o = zoom_about(np.clip(o, 0, 1), cx, cy, Z)
            o = radial_blur(o, cx, cy, 1.0, 1.0 + 0.06 * u, 4)
        return np.clip(o, 0, 1)
    v = (j + 1) / post
    ex, ey = emb_at(sa["f1"] - 1); cx, cy, sc = to_screen(sa, sa["f1"] - 1, ex, ey); r0 = er * sc * 9.0   # the emblem as it filled the screen
    Zo = 9.0 * math.exp(math.log(6.0) * ein(v, 1.4))                                # we keep diving into his chest
    outside = zoom_about(A, cx, cy, Zo); outside = radial_blur(outside, cx, cy, 1.0, 1.0 + 0.10 * (1 - v), 4)
    ring_, disc_, bolt_ = emblem_shape(cx, cy, er * sc * Zo)
    outside = outside + cv2.GaussianBlur(bolt_, (0, 0), 20)[..., None] * GOLD2 * 0.9 * (1 - v)
    gs = math.exp(math.log(7.0) * eout(v, 1.6))
    ring, disc, bolt = emblem_shape(cx, cy, r0 * gs * 0.55)
    m = cv2.GaussianBlur(bolt, (0, 0), 2.0)[..., None]
    if gs > 5: m = np.maximum(m, clamp((gs - 5) / 2, 0, 1))
    Bz = zoom_about(B, W / 2, H * 0.47, 1.0 + 0.32 * (1 - eout(v, 2.4)))
    if v < 0.5: Bz = radial_blur(Bz, W / 2, H * 0.47, 1.0, 1.0 + 0.12 * (1 - v / 0.5), 5)
    o = Bz * m + outside * (1 - m)
    edge = cv2.GaussianBlur(cv2.morphologyEx((m[..., 0] > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8)).astype(np.float32), (0, 0), 5)
    o = o + edge[..., None] * GOLDW * 1.6 * (1 - v)
    rr = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2); R = 200 + 1900 * eout(v, 1.6)
    o = o + np.exp(-((rr - R) / 26) ** 2)[..., None] * GOLDW * 0.8 * (1 - v)              # shockwave
    cv = bolt_canvas()
    for q in range(6):                                                                   # the bolt's edges spit arcs
        a_ = q * 1.047 + f * 0.4; L_ = r0 * gs * 0.6
        put_bolt(cv, (cx + math.cos(a_) * L_ * 0.3, cy + math.sin(a_) * L_ * 0.5), (cx + math.cos(a_) * L_ * 1.2, cy + math.sin(a_) * L_ * 1.4), 1150 + q + f, 3, 0.3, 6, 1)
    o = o + light_from(cv, 1.1 * (1 - v))
    return np.clip(o, 0, 1)

def ramp(A, B, j, f, sa, sb, pre=6, post=7):
    """speed-ramp match: the outgoing shot accelerates away (zoom + motion blur), the next decelerates in."""
    if j < 0:
        u = (j + pre + 1) / pre; z = 1 + 0.25 * ein(u, 2.2)
        o = zoom_about(A, W / 2, H * 0.45, z); o = hblur(o, 2 + 180 * ein(u, 2))
        return np.clip(o * (1 + 0.25 * u), 0, 1)
    v = (j + 1) / post; z = 1 + 0.22 * (1 - eout(v, 2.4))
    o = zoom_about(B, W / 2, H * 0.45, z); o = hblur(o, 2 + 160 * (1 - eout(v, 2)))
    return np.clip(o * (1 + 0.25 * (1 - v)), 0, 1)

def bolt_link(A, B, j, f, sa, sb, pre=7, post=9):
    """his thrown bolt keeps going: it tears across the cut and he is waiting at the other end."""
    p0 = (W * 0.40, H * 0.70); p1 = subject_point(sb, sb["f0"])
    if j < 0:
        u = (j + pre + 1) / pre; cv = bolt_canvas()
        tip = (p0[0] + (-120 - p0[0]) * ein(u, 1.3), p0[1] + (H * 0.66 - p0[1]) * u)
        put_bolt(cv, p0, tip, 1200 + f, 5, 0.22, 7, 3)
        return np.clip(A + light_from(cv, 1.3), 0, 1)
    v = (j + 1) / post; cv = bolt_canvas()
    put_bolt(cv, (W + 120, H * 0.66), (p1[0] + 120, p1[1] + 60), 1250 + f // 2, 5, 0.22, 7, 3)
    fl = 1 - eout(v, 1.8)
    return np.clip(B * (0.7 + 0.3 * v) + light_from(cv, 1.4 * fl) + fl * 0.15 * GOLD2, 0, 1)

def shock(A, B, j, f, sa, sb, pre=4, post=12):
    """an electric shockwave rings out of the scream and refracts the frame open onto it."""
    if j < 0:
        u = (j + pre + 1) / pre; return np.clip(zoom_about(A, W / 2, H * 0.45, 1 + 0.05 * u) * (1 + 0.3 * u), 0, 1)
    k = j; n = post
    p = subject_point(sb, f); cx, cy = p[0], p[1] - 150
    R = 1800 * eout((k + 1) / n, 2.0)
    dx, dy = _GX - cx, _GY - cy; r = np.sqrt(dx * dx + dy * dy) + 1e-3
    band = np.exp(-((r - R) / 60.0) ** 2); disp = band * 50 * (1 - k / n)
    src = np.where((r < R)[..., None], B, A)
    o = cv2.remap(src.astype(np.float32), (_GX - dx / r * disp).astype(np.float32), (_GY - dy / r * disp).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    rim = np.exp(-((r - R) / 9.0) ** 2) + 0.4 * band
    cv = bolt_canvas()
    for q in range(5):
        a_ = q * 1.256 + 0.3; put_bolt(cv, (cx + math.cos(a_) * R * 0.92, cy + math.sin(a_) * R * 0.92), (cx + math.cos(a_ + 0.25) * R * 1.05, cy + math.sin(a_ + 0.25) * R * 1.05), 1300 + q + k, 2, 0.3, 5, 0)
    return np.clip(o + rim[..., None] * GOLDW * 0.9 * (1 - 0.6 * k / n) + light_from(cv, 0.8 * (1 - k / n)), 0, 1)

def prism_cut(A, B, j, f, sa, sb, pre=4, post=8):
    """a prismatic cut: red switches to the next shot first, then green, then blue, each sliding (time-slice)."""
    n = pre + post; p = (j + pre + 0.5) / n
    o = np.zeros_like(A)
    for ch, (delay, dx) in enumerate(((0.35, -90), (0.15, 0), (0.0, 90))):         # BGR: blue last, red first
        q = smooth((p - delay) / 0.55)
        a = np.roll(A[..., ch], int(dx * q), 1); b = np.roll(B[..., ch], int(dx * (q - 1)), 1)
        o[..., ch] = a * (1 - q) + b * q
    return np.clip(o * (1 + 0.15 * math.sin(math.pi * p)), 0, 1)

def bolt_strike(A, B, j, f, sa, sb, pre=6, post=12):
    """lightning strikes: a bolt falls from the top of the frame onto him; white-gold flash; he is struck."""
    p = subject_point(sb, sb["f0"]); bxa = face_box(sa, sa["f1"] - 1); bxb = face_box(sb, sb["f0"])
    xs_ = max([p[0] + 300] + [b[1] + 60 for b in (bxa, bxb) if b is not None])
    p = (clamp(xs_, 120, W - 60), p[1] - 120)                                          # his shoulder, clear of both faces
    if j < 0:
        u = (j + pre + 1) / pre; cv = bolt_canvas()
        put_bolt(cv, (p[0] + 60, -40), (p[0] + 20 * (1 - u), -40 + (p[1] + 40) * ein(u, 1.6)), 1400 + f, 4, 0.12, 7, 1)
        return np.clip(A * (1 - 0.35 * u) + light_from(cv, 1.2), 0, 1)
    v = (j + 1) / post; cv = bolt_canvas()
    put_bolt(cv, (p[0] + 60, -40), p, 1450 + f // 2, 6, 0.12, 8, 2)
    fl = 1 - eout(v, 1.6)
    flash = np.exp(-(((_GX - p[0]) / 700) ** 2 + ((_GY - p[1]) / 900) ** 2))[..., None] * fl * 0.55
    return np.clip(B * (0.6 + 0.4 * v) + light_from(cv, 1.6 * fl) + flash * GOLDW, 0, 1)

def freeze_in(A, B, j, f, sa, sb, pre=4, post=10):
    """time stops: the colour drains out of the world in a wave from the centre while he stays lit."""
    if j < 0: return A
    v = (j + 1) / post; x = -80 + (W + 160) * eout(v, 1.6)
    keep = np.clip((_GX - x) / 120, 0, 1)[..., None]                                  # right of the line: time still moving
    alive = np.clip(hblur(B, 40) * 0.5 + B * 0.5 + 0.06 * GOLD2, 0, 1)
    o = B * (1 - keep) + alive * keep
    line = np.exp(-((_GX - x) / 4.0) ** 2)[..., None] + 0.4 * np.exp(-((_GX - x) / 30.0) ** 2)[..., None]
    return np.clip(o + line * GOLDW * 0.7 * (1 - v ** 3), 0, 1)

def jolt(A, B, j, f, sa, sb, pre=2, post=6):
    """a jolt in time: a 2-frame prismatic tear and a punch-in."""
    if j < 0: return np.clip(rgb_split(A, 18 * (j + pre + 1)), 0, 1)
    v = (j + 1) / post; o = zoom_about(B, W / 2, H * 0.45, 1 + 0.06 * (1 - v))
    return np.clip(rgb_split(o, 22 * (1 - v)), 0, 1)

def restart(A, B, j, f, sa, sb, pre=3, post=14):
    """time restarts on the second impact: a ring of colour and speed rushes out from him; the world moves again."""
    if j < 0: return np.clip(A * (1 - 0.25 * (j + pre + 1) / pre), 0, 1)
    v = (j + 1) / post; p = subject_point(sb, f)
    rr = np.sqrt((_GX - p[0]) ** 2 + (_GY - p[1]) ** 2); R = 450 + 1900 * eout(v, 1.7)
    inside = np.clip((R - rr) / 40, 0, 1)[..., None]
    L = lum8(B)[..., None]; mono = L * STEEL
    o = B * inside + mono * (1 - inside)
    o = o + np.exp(-((rr - R) / 30) ** 2)[..., None] * GOLDW * 1.1 * (1 - v)
    o = hblur(o, 2 + 120 * (1 - eout(v, 2)))
    return np.clip(o, 0, 1)

TR2.update({"arc_link": (arc_link, 6, 9), "ignite": (ignite, 8, 10), "emblem_gate": (emblem_gate, 20, 22), "ramp": (ramp, 6, 7),
            "bolt_link": (bolt_link, 7, 9), "shock": (shock, 4, 12), "prism_cut": (prism_cut, 4, 8), "bolt_strike": (bolt_strike, 6, 12),
            "freeze_in": (freeze_in, 4, 10), "jolt": (jolt, 2, 6), "restart": (restart, 3, 14)})

# ---- the run becomes light (from streak_e), then the whole edit rewinds back to the dark lab (the loop)
def light_streak(img, f, s):
    e0 = fh(s["streak_e"]); k = f - e0
    if k < 0: return img
    u = clamp((k + 1) / (s["f1"] - e0), 0, 1)
    o = hblur(img, 4 + 420 * ein(u, 1.8)) * (1 + 0.9 * u)
    sy = max(0.01, 1 - ein(clamp((u - 0.55) / 0.45, 0, 1), 1.5))
    if sy < 0.999:
        M = np.float32([[1 + 0.4 * (1 - sy), 0, -W * 0.2 * (1 - sy)], [0, sy, H * 0.47 * (1 - sy)]])
        o = cv2.warpAffine(o, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
    line = np.exp(-((_GY - H * 0.47) / (3 + 10 * u)) ** 2) * u ** 1.5
    return np.clip(o + line[..., None] * GOLDW * 1.4, 0, 1)

REW_PICK = None
def rewind_frame(f, s):
    """e100-e104: the edit plays backwards at ~25x through a streaked, prismatic time tunnel and lands on frame 0."""
    k = f - s["f0"]; n = s["f1"] - s["f0"]; u = (k + 1) / n
    tr = th(E.E_REW) * (1 - eout(u, 1.25))                     # edit time running backwards: 24.0 s -> 0
    fr = max(0, min(E.fe(tr), fh(E.E_REW) - 1))
    s2 = shot_at(fr); img, _ = base10(s2, fr)
    st_ = 0.35 + 0.65 * (1 - smooth((u - 0.55) / 0.45))          # ends at 0.35: frame 0 (rewind_in) continues it
    o = hblur(img, 2 + 300 * st_)
    o = np.clip(rgb_split(o, 40 * st_), 0, 1)
    tun = np.clip(np.sqrt(((_GX - W / 2) / (W * 0.6)) ** 2 + ((_GY - H * 0.47) / (H * 0.5)) ** 2), 0, 1)[..., None]
    tw = st_ * (1 - smooth((u - 0.55) / 0.40))                       # the tunnel is gone by the landing (frame 0 has none)
    o = o * (1 - 0.5 * tun * tw) + tun * tw * 0.25 * GOLD2
    if u < 0.12:                                                    # the line of light opens back into a picture
        sy = max(0.01, smooth(u / 0.12))
        M = np.float32([[1, 0, 0], [0, sy, H * 0.47 * (1 - sy)]])
        o = cv2.warpAffine(o, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
        o = o + np.exp(-((_GY - H * 0.47) / (3 + 40 * sy)) ** 2)[..., None] * GOLDW * (1 - sy)
    return np.clip(o, 0, 1), st_

def rewind_in(out, f, k, n=14):
    """frame 0 continues the rewind: the last streak and colour split settle onto the dark lab."""
    if k >= n: return out
    v = (k + 1) / n; st_ = 0.35 * (1 - eout(v, 1.6))
    o = hblur(out, 2 + 300 * st_)
    return np.clip(rgb_split(o, 40 * st_), 0, 1)

# ---- type: the approved v9 system, recoloured for the Flash (gold emphasis), plus Flash-specific moves ---------
EMPH = np.array([0.22, 0.80, 1.00], np.float32)          # lightning gold emphasis (cap_word reads EMPH)

def text_slam(out, f, tx):
    """IT / HAPPENS: HAPPENS slams in big, white-hot, arcs crackling off it; a ring of light under it; then a speed exit."""
    t = f / FPS; (w0, t0, _), (w1, t1, _) = tx["words"][0], tx["words"][1]
    if t < t0 - 0.02 or t > tx["end"] + 0.02: return out
    ex = smooth((t - (tx["end"] - 0.14)) / 0.14)
    out = out * cap_scrim(1250, 1640, 0.32 * (1 - ex))
    a = cap_word(w0, 92, False); v0 = eout(clamp((t - t0) / 0.15, 0, 1), 2.4)
    out = ease_word(out, a if ex < 0.02 else cv2.GaussianBlur(a, (0, 0), 0.1 + 8 * ex), W / 2 + 260 * ex, 1330, v0, 1 - ex, 26)
    if t >= t1 - 0.02:
        b = cap_word(w1, 176, True); v = clamp((t - t1) / 0.16, 0, 1)
        sc = 1.55 - 0.55 * eout(v, 3.0)
        bb = cv2.resize(b, (int(b.shape[1] * sc), int(b.shape[0] * sc)))
        if v < 1 or ex > 0: bb = cv2.GaussianBlur(bb, (0, 0), 0.1 + 6 * (1 - v) + 10 * ex)
        hot = clamp(1 - (t - t1) / 0.25, 0, 1)
        bb[..., :3] = bb[..., :3] * (1 - 0.6 * hot) + GOLDW * 0.6 * hot * (bb[..., 3:4] > 0.5)
        out = paste(out, bb, int(W / 2 - bb.shape[1] / 2 + 420 * ex ** 1.5), int(1500 - bb.shape[0] / 2), min(1, v * 1.5) * (1 - ex))
        if v > 0.2:
            cv = bolt_canvas(); hw = b.shape[1] / 2 - 40
            for q in range(3):
                x0 = W / 2 + (q - 1) * hw * 0.8; put_bolt(cv, (x0, 1415), (x0 + 60 * (q - 1), 1415 - 90 - 40 * ((f // 3 + q) % 2)), 1500 + q + f // 2, 2, 0.35, 4, 0)
            out = out + light_from(cv, 0.8 * (1 - ex) * (0.5 + 0.5 * hot))
            rr = np.sqrt(((_GX - W / 2) / 1.0) ** 2 + ((_GY - 1500) / 0.28) ** 2); R = 200 + 700 * eout(v, 1.8)
            out = out + np.exp(-((rr - R) / 14) ** 2)[..., None] * GOLDW * 0.6 * hot
    return np.clip(out, 0, 1)

def text_echo(out, f, tx):
    """WHEN IT / HAPPENS: each word arrives at speed with three gold afterimages that converge onto it."""
    t = f / FPS; words = tx["words"]
    if t < words[0][1] - 0.02 or t > tx["end"] + 0.02: return out
    ex = smooth((t - (tx["end"] - 0.14)) / 0.14); sizes = (90, 132); ys = (1360, 1490)
    out = out * cap_scrim(1250, 1600, 0.32 * (1 - ex))
    for ln in (0, 1):
        ws = [(w, wt) for w, wt, l in words if l == ln]
        ims = [cap_word(w, sizes[ln], w in tx.get("emph", [])) for w, _ in ws]
        gap = int(sizes[ln] * 0.26); widths = [im.shape[1] - 72 for im in ims]; tot = sum(widths) + gap * (len(ims) - 1)
        x = W / 2 - tot / 2
        for (w, wt), im, wd in zip(ws, ims, widths):
            v = clamp((t - wt) / 0.22, 0, 1)
            if v > 0:
                for k in (3, 2, 1):                                                    # afterimages, behind the word
                    d = (1 - eout(v, 2.2)) * 120 * k + 18 * k * (1 - ex)
                    gh = im.copy(); gh[..., :3] = GOLD2 * 0.7 + gh[..., :3] * 0.3; gh[..., 3] *= 0.45 / k
                    out = paste(out, gh, int(x + wd / 2 - gh.shape[1] / 2 - d), int(ys[ln] - gh.shape[0] / 2), (1 - ex) * clamp(v * 3, 0, 1) * (1 - 0.5 * eout(v, 2)))
                o_im = im if ex < 0.02 else cv2.GaussianBlur(im, (0, 0), 0.1 + 6 * ex)
                out = ease_word(out, o_im, x + wd / 2 + 300 * ex ** 1.5 - 160 * (1 - eout(v, 2.6)), ys[ln], eout(v, 2.4), 1 - ex, 0)
            x += wd + gap
    return out

def text_hero10(out, f, tx):
    """LET IT / HAPPEN: each letter is struck by its own bolt from above and blooms in white-hot; HAPPEN lands bigger and
    floods gold from the bottom; on the second "let it happen" the title pulses with lightning; it exits as speed streaks."""
    t = f / FPS; words = tx["words"]
    if t < words[0][1] - 0.02 or t > tx["end"] + 0.02: return out
    t_end = tx["end"]
    ex_all = smooth((t - (t_end - 0.20)) / 0.20)
    out = out * cap_scrim(1240, 1640, 0.36 * (1 - ex_all))
    lines = [("LET IT", 128, 1330, [w for w in words if w[2] == 0]), ("HAPPEN", 196, 1510, [w for w in words if w[2] == 1])]
    lay = np.zeros((H, W, 4), np.float32); cv = bolt_canvas()
    pulse = 0.0
    for tp in tx.get("pulses", []):
        if t >= tp: pulse = max(pulse, math.exp(-(t - tp) / 0.12))
    for text, size, yc, wl in lines:
        lets, _wd = hero_letters(text, size)
        if text == "LET IT":
            tL, tI = wl[0][1], wl[1][1]; starts = [tL + 0.04 * i if i < 3 else tI + 0.04 * (i - 3) for i in range(len(lets))]
        else:
            starts = [wl[0][1] + 0.035 * i for i in range(len(lets))]
        for i, (c, lm, xoff) in enumerate(lets):
            v = clamp((t - starts[i]) / 0.20, 0, 1)
            if v <= 0: continue
            ve = eout(v, 3.0); x = W / 2 + xoff
            if v < 0.6:                                                               # the bolt that strikes the letter
                put_bolt(cv, (x + 24, yc - size * 0.35 - 150), (x, yc - size * 0.35), 1600 + i * 7 + len(text) + int(v * 6), 3, 0.3, 5, 0)
            hot = clamp(1 - (t - starts[i]) / 0.30, 0, 1)
            if text == "HAPPEN":
                fill = eout(clamp((t - starts[i] - 0.10) / 0.35, 0, 1), 2.0); hh = lm.shape[0]; yy = np.linspace(1, 0, hh)[:, None]
                cmix = cv2.GaussianBlur((yy < fill * 1.08).astype(np.float32), (0, 0), 3)
                col = np.broadcast_to(WHITE * (1 - cmix[..., None]) + EMPH * 1.05 * cmix[..., None], lm.shape + (3,)).copy()
            else:
                col = np.ones(lm.shape + (3,), np.float32) * WHITE
            col = col * (1 - 0.7 * hot) + GOLDW * 0.9 * hot
            pad = 26; lmp = np.pad(lm, pad); colp = np.pad(col, ((pad, pad), (pad, pad), (0, 0)), mode="edge")
            k_ = max(3, int(size * 0.07)) | 1
            st_ = cv2.dilate(lmp, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_, k_)))
            colp = colp * lmp[..., None] + np.array([0.02, 0.02, 0.03], np.float32) * (1 - lmp[..., None])
            spr_l = np.dstack([colp, np.maximum(lmp, st_ * 0.9)]).astype(np.float32)
            exl = clamp((t - (t_end - 0.20 + 0.012 * i)) / 0.18, 0, 1)
            sc = (0.40 + 0.60 * ve + 0.08 * math.sin(math.pi * v)) * (1 + 0.04 * pulse)
            draw_sprite(lay, spr_l, x + 520 * exl ** 1.6, yc, sc, (1 - ve) * (18 if i % 2 else -18), 1.0,
                        (0.1 + 4 * (1 - ve) + 14 * exl) if (v < 1 or exl > 0) else 0.0, (1 - exl) * min(1, ve * 1.4), stretch=1 + 3.0 * exl)
            if hot > 0.02: out = add_glow(out, x, yc, size * 0.6, hot * 0.45, GOLDW)
    if pulse > 0.02:
        for q in range(4):
            x0 = W / 2 + (q - 1.5) * 220; put_bolt(cv, (x0, 1600), (x0 + 50, 1250), 1700 + q + f // 2, 2, 0.35, 5, 1)
    sh = cv2.GaussianBlur(lay[..., 3], (0, 0), 9)[..., None] * 0.6
    out = out * (1 - sh) + light_from(cv, 0.9 + 0.8 * pulse) * (1 - ex_all)
    out = out * (1 - lay[..., 3:4]) + lay[..., :3]
    return np.clip(out, 0, 1)

def text_speed(out, f, tx):
    """ALL THIS / RUNNING AROUND: the words run in from the right (with him), trailing gold afterimages, and settle."""
    t = f / FPS; words = tx["words"]
    if t < words[0][1] - 0.02 or t > tx["end"] + 0.02: return out
    ex = smooth((t - (tx["end"] - 0.12)) / 0.12); sizes = (92, 126); ys = (1350, 1480)
    out = out * cap_scrim(1240, 1600, 0.34 * (1 - ex))
    for ln in (0, 1):
        ws = [(w, wt) for w, wt, l in words if l == ln]
        sz = sizes[ln]
        for _ in range(5):
            ims = [cap_word(w, sz, w in tx.get("emph", [])) for w, _ in ws]
            gap = int(sz * 0.26); widths = [im.shape[1] - 72 for im in ims]; tot = sum(widths) + gap * (len(ims) - 1)
            if tot <= 960: break
            sz = int(sz * 960 / tot) - 1
        x = W / 2 - tot / 2
        for (w, wt), im, wd in zip(ws, ims, widths):
            v = clamp((t - wt) / 0.20, 0, 1)
            if v > 0:
                off = (1 - eout(v, 3.0)) * 700
                tr = im.copy(); tr[..., 3] *= 0.35 * (1 - v)
                trl = cv2.resize(tr, (int(tr.shape[1] * (1 + 2.5 * (1 - v))), tr.shape[0]))
                trl = cv2.GaussianBlur(trl, (0, 0), 0.1 + 8 * (1 - v))
                trl[..., :3] = GOLD2 * 0.8 + trl[..., :3] * 0.2
                out = paste(out, trl, int(x + wd / 2 + off), int(ys[ln] - trl.shape[0] / 2), 1 - ex)
                o_im = im if (v >= 1 and ex < 0.02) else cv2.GaussianBlur(im, (0, 0), 0.1 + 5 * (1 - v) + 6 * ex)
                out = ease_word(out, o_im, x + wd / 2 + off - 300 * ex, ys[ln], min(1, v * 1.6), 1 - ex, 0)
            x += wd + gap
    return out

def text10(out, f, s, rides):
    for tx in E.TEXT:
        if bool(tx.get("rides")) != rides: continue
        st_ = tx["style"]
        if st_ == "cap": out = text_cap(out, f, tx)
        elif st_ == "slam": out = text_slam(out, f, tx)
        elif st_ == "echo": out = text_echo(out, f, tx)
        elif st_ == "hero": out = text_hero10(out, f, tx)
        elif st_ == "speed": out = text_speed(out, f, tx)
    return out

# ---- shot pictures --------------------------------------------------------------------------------------------
def base10(s, f):
    person = None
    if s.get("seg"): img, person = render_shot(s, f, want_mask=True)
    else: img = render_shot(s, f)
    img = np.clip(img + 0.40 * (img - cv2.GaussianBlur(img, (0, 0), 1.5)), 0, 1)
    if s.get("frozen"):
        fz = is_frozen(s, f)
        if fz > 0: img = frozen_world(img, person, f, s, fz)
        else: img = np.clip(hblur(img, 30) * 0.5 + img * 0.5 + 0.06 * GOLD2, 0, 1)        # time lurches forward
    if s.get("trails"): img = afterimages(img, s, f, person, s["trails"])
    if s.get("arcs"): img = edge_arcs(img, f, person, s["arcs"])
    return img, person

_B10 = {}
def edge10(S_, which):
    key = (S_["n"], which)
    if key not in _B10:
        if len(_B10) > 6: _B10.clear()
        if S_.get("graphic") == "rewind": _B10[key] = rewind_frame(S_["f0"] if which == "first" else S_["f1"] - 1, S_)[0]
        else: _B10[key] = base10(S_, S_["f0"] if which == "first" else S_["f1"] - 1)[0]
    return _B10[key]

def accents10(out, f):
    g = 0.0
    for e_, a in ((E.HDROP, 0.16), (E.E_RUN, 0.14)):
        k = f - fh(e_)
        if 0 <= k < 16: g += a * math.exp(-k / 4.5)
    for e_ in E.STUT_HITS:
        k = f - fh(e_)
        if 0 <= k < 8: g += 0.07 * math.exp(-k / 2.5)
    return out if g <= 0 else np.clip(out * (1 + g) + g * 0.12 * GOLD2, 0, 1)

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    if s.get("graphic") == "rewind":
        out, _ = rewind_frame(f, s); person = None
    else:
        out, person = base10(s, f)
    out = text10(out, f, s, True)                                            # type that rides the transitions
    if s.get("streak_e") is not None: out = light_streak(out, f, s)
    if tin == "rewind_in": out = rewind_in(out, f, k)
    elif tin in TR2 and k < TR2[tin][2] and P is not None: out = TR2[tin][0](edge10(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge10(n_, "first"), kn, f, s, n_)
    out = accents10(out, f)
    out = text10(out, f, s, False)
    out = finish10(out, f)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)

def init_hits():
    HITS.clear()
    HITS.append((fh(E.HDROP), 18, 4.5)); HITS.append((fh(E.E_RUN), 14, 4.0))
    for e_ in E.STUT_HITS: HITS.append((fh(e_), 8, 2.5))
    for e_ in (38, 46, 68): HITS.append((fh(e_), 7, 2.5))


def beat_bounce(f):
    """a 1.5 % zoom pulse on every beat after the drop and in the run."""
    e = f / FPS / E.HB
    if not (E.HDROP <= e < E.E_STUT or E.E_RUN <= e < E.E_REW): return 1.0
    ph = (e % 2) * E.HB
    return 1 + 0.015 * math.exp(-ph / 0.08)


# ============================================================================ v10 rev 2 — no dead space
# Owner notes: more animations, graphics and transitions, no breathing room; the lit-up eyes shot replaced.
# New: speed slices and a chest-height lightning tear (transitions), CARRY OFF carried away by a whirlwind (type),
# Speed Force sparks in depth, beat-synced edge bolts, light sweeps on the bars, time-line ripples on the freeze hits,
# beat pulses through the cold open.

# ---- transitions -------------------------------------------------------------------------------------------
_SL = {}
def slice_bands():
    if "b" in _SL: return _SL["b"]
    rng = np.random.default_rng(31); y = 0; bands = []
    while y < H:
        h_ = int(rng.uniform(60, 170)); bands.append((y, min(H, y + h_), rng.uniform(0.0, 0.35), rng.uniform(0.8, 1.3))); y += h_
    _SL["b"] = bands; return bands

def slices(A, B, j, f, sa, sb, pre=6, post=9):
    """speed slices: the frame breaks into horizontal bands that rip sideways at different speeds; the next shot arrives
    band by band from the other side (with streak blur and a gold glint on each band's leading edge)."""
    p = (j + pre + 0.5) / (pre + post); o = np.zeros_like(A)
    for (y0, y1, d, spd) in slice_bands():
        q = clamp((p - d * 0.6) / (1 - 0.35) * spd, 0, 1); q = smooth(q)
        offA = int(-W * 1.1 * q); offB = int(W * 1.1 * (1 - q))
        band = np.zeros((y1 - y0, W, 3), np.float32)
        a = np.roll(A[y0:y1], offA, 1); b = np.roll(B[y0:y1], offB, 1)
        xs = np.arange(W)[None, :, None]
        ma = (xs < W + offA).astype(np.float32); mb = (xs >= offB).astype(np.float32)
        band = a * ma * (1 - mb) + b * mb + (1 - ma) * (1 - mb) * hblur(B[y0:y1], 120)
        blur = int(4 + 90 * math.sin(math.pi * q))
        band = hblur(band, blur)
        edge = np.exp(-((xs - offB) / 6.0) ** 2) * math.sin(math.pi * q)
        o[y0:y1] = np.clip(band + edge * GOLDW * 0.9, 0, 1)
    return o

def bolt_tear(A, B, j, f, sa, sb, pre=5, post=12):
    """a lightning bolt tears straight across his chest (never his face); the two halves fly apart; the next shot is behind."""
    bxa = face_box(sa, sa["f1"] - 1); cand = (bxa[2] + 50) if bxa else H * 0.62
    y_t = cand if cand < 1290 else 1665                                                # between jaw and caption, else below it
    key = ("tear", int(y_t))
    if key not in _SL:
        pts = bolt_points((-40, y_t), (W + 40, y_t + 30), 77, 0.10, 8)
        poly = np.vstack([pts, [[W + 40, -40], [-40, -40]]]).astype(np.int32)
        top = np.zeros((H, W), np.uint8); cv2.fillPoly(top, [poly], 255)
        _SL[key] = (pts, top.astype(np.float32) / 255)
    pts, top = _SL[key]
    cv = bolt_canvas(); cv2.polylines(cv, [pts.astype(np.int32)], False, 255, 4, cv2.LINE_AA)
    if j < 0:
        u = (j + pre + 1) / pre; n = max(2, int(len(pts) * ein(u, 1.2)))
        cv = bolt_canvas(); cv2.polylines(cv, [pts[:n].astype(np.int32)], False, 255, 4, cv2.LINE_AA)
        return np.clip(A + light_from(cv, 1.2), 0, 1)
    v = (j + 1) / post; sep = int(30 + 1100 * ein(v, 1.6))
    Bz = zoom_about(B, W / 2, H * 0.47, 1.18 - 0.18 * eout(v, 2.4)); o = Bz.copy()
    for side, m in ((-1, top), (1, 1 - top)):
        M = np.float32([[1, 0, 0], [0, 1, side * sep]])
        Ah = cv2.warpAffine(A, M, (W, H), borderValue=(0, 0, 0)); mh = cv2.warpAffine(m, M, (W, H), borderValue=0)[..., None]
        o = o * (1 - mh) + Ah * mh
        o = o + cv2.warpAffine(light_from(cv, 1.2 * (1 - v)), M, (W, H))
    return np.clip(o, 0, 1)

TR2.update({"slices": (slices, 6, 9), "bolt_tear": (bolt_tear, 5, 12)})

# ---- graphics ----------------------------------------------------------------------------------------------
_MOTE = {}
def mote_params():
    if "p" in _MOTE: return _MOTE["p"]
    rng = np.random.default_rng(57)
    _MOTE["p"] = [dict(x0=rng.uniform(0, 1), y0=rng.uniform(0, 1), z=rng.uniform(0.15, 1.0) ** 1.3, ph=rng.uniform(0, 6.28),
                       on=rng.uniform(0, 1)) for _ in range(46)]
    return _MOTE["p"]

def spark_motes(out, f, person, dens):
    """Speed Force sparks in depth: far ones drift behind him (matte), near ones are soft streaks in front."""
    if dens <= 0.01: return out
    t = f / FPS; back = np.zeros((H, W), np.float32); front = np.zeros((H, W), np.float32)
    for p in mote_params():
        if p["on"] > dens: continue
        z = p["z"]; spx = 90 + 420 * z; spy = -(30 + 140 * z)
        x = (p["x0"] * (W + 300) + spx * t + 30 * math.sin(2.1 * t + p["ph"])) % (W + 300) - 150
        y = (p["y0"] * (H + 300) + spy * t) % (H + 300) - 150
        L_ = int(6 + 46 * z); tw = 0.55 + 0.45 * math.sin(9 * t + p["ph"] * 3)
        tgt = front if z > 0.6 else back
        cv2.line(tgt, (int(x - L_), int(y + L_ * 0.3)), (int(x), int(y)), (0.5 + 0.5 * z) * tw, max(1, int(1 + 3 * z)), cv2.LINE_AA)
    if person is not None: back *= (1 - np.clip(person * 1.2, 0, 1))
    lay = back + cv2.GaussianBlur(front, (0, 0), 2.2) * 1.3
    glow = cv2.resize(cv2.GaussianBlur(cv2.resize(lay, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 3), (W, H))
    return np.clip(out + (lay[..., None] * GOLDW * 0.9 + glow[..., None] * GOLD2 * 1.6) * min(1, dens * 1.2), 0, 1)

def edge_bolts(out, f):
    """on every bar line of the cold open and the hook: lightning flickers down both frame edges (never the centre)."""
    e = f / FPS / E.HB
    if not (8 <= e < E.HDROP or 56 <= e < 68 or E.E_RUN <= e < E.E_REW): return out     # (not on bar 0: frame 0 = the rewind's landing)
    k = f - fh(int(e // 8) * 8)
    if k >= 9: return out
    a = [1.0, 0.4, 0.9, 0.2, 0.7, 0.3, 0.5, 0.15, 0.25][k]
    cv = bolt_canvas()
    for side, x0 in ((0, W * 0.05), (1, W * 0.95)):
        put_bolt(cv, (x0 + (side * 2 - 1) * 10, -30), (x0 - (side * 2 - 1) * 40, H * (0.45 + 0.25 * ((f // 9 + side) % 2))), 2000 + f // 9 * 3 + side, 2, 0.30, 6, 1)
    return np.clip(out + light_from(cv, a * 0.9), 0, 1)

def bar_sweep(out, f):
    """a diagonal band of gold light sweeps across on the bar lines of the cold open."""
    e = f / FPS / E.HB
    if not (8 <= e < E.HDROP - 2): return out
    k = f - fh(int(e // 8) * 8)
    if k >= 14: return out
    u = k / 13; pos = -400 + (W + 800) * ein(u, 1.3)
    d = (_GX + (_GY - H / 2) * 0.35) - pos
    band = np.exp(-(d / 70) ** 2) * 0.55 + np.exp(-(d / 240) ** 2) * 0.25
    return np.clip(out + band[..., None] * (GOLDW * 0.6 + GOLD2 * 0.4) * math.sin(math.pi * u) * 0.6, 0, 1)

def hit_ripple(out, f):
    """in the frozen stretch: each beat that jolts time forward sends a gold time-line across the frame."""
    for e_ in E.STUT_HITS:
        k = f - fh(e_)
        if 0 <= k < 8:
            x = -60 + (W + 120) * eout((k + 1) / 8, 1.5)
            line = np.exp(-((_GX - x) / 4.0) ** 2) + 0.35 * np.exp(-((_GX - x) / 40.0) ** 2)
            out = np.clip(out + line[..., None] * GOLDW * 0.75 * (1 - k / 8), 0, 1)
    return out

def beat_bounce(f):
    """zoom pulses: soft on every beat of the cold open, stronger after the drop and in the run."""
    e = f / FPS / E.HB; ph = (e % 2) * E.HB
    if 0 <= e < E.HDROP: return 1 + 0.010 * math.exp(-ph / 0.08)
    if E.HDROP <= e < E.E_STUT or E.E_RUN <= e < E.E_REW: return 1 + 0.016 * math.exp(-ph / 0.08)
    return 1.0

# ---- type: CARRY OFF, carried away by a whirlwind -------------------------------------------------------------
def text_carry(out, f, tx):
    """IT'S GONNA / CARRY OFF: the v9 caption build (keyline, gold emphasis); then a whirlwind lifts the letters off
    one by one and spirals them away up and to the right, trailing gold."""
    t = f / FPS; words = tx["words"]
    if t < words[0][1] - 0.02 or t > tx["end"] + 0.02: return out
    ex0 = tx["end"] - 0.55
    out = out * cap_scrim(1260, 1620, 0.32 * (1 - smooth((t - ex0 - 0.3) / 0.25)))
    sizes = (90, 120); ys = (1372, 1496)
    lay = np.zeros((H, W, 4), np.float32)
    vx, vy = W * 0.62 + 420 * max(0, t - ex0), 1420 - 520 * max(0, t - ex0)               # the vortex drifts up-right
    li = 0
    for ln in (0, 1):
        ws = [(w, wt) for w, wt, l in words if l == ln]
        text = " ".join(w for w, _ in ws)
        lets, wd = hero_letters(text, sizes[ln], 2)
        bounds = []; acc = 0
        for w, wt in ws: bounds.append((acc, acc + len(w), wt)); acc += len(w)
        for i, (c, lm, xoff) in enumerate(lets):
            wt = [b[2] for b in bounds if b[0] <= i < b[1]][0]
            v = eout(clamp((t - wt - 0.02 * i) / 0.17, 0, 1), 2.4)
            if v <= 0: continue
            emph = any(b[0] <= i < b[1] and ws[k][0] in tx.get("emph", []) for k, b in enumerate(bounds))
            col = EMPH if emph else WHITE
            pad = 30; lmp = np.pad(lm, pad); k_ = max(3, int(sizes[ln] * 0.07)) | 1
            st_ = cv2.dilate(lmp, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_, k_)))
            rgb = col * lmp[..., None] + np.array([0.02, 0.02, 0.03], np.float32) * (1 - lmp[..., None])
            spr = np.dstack([rgb, np.maximum(lmp, st_ * 0.9)]).astype(np.float32)
            x0, y0 = W / 2 + xoff, ys[ln] + 30 * (1 - v)
            w_ = clamp((t - (ex0 + 0.028 * li)) / 0.42, 0, 1); li += 1                    # the whirlwind takes it
            if w_ > 0:
                ang0 = math.atan2(y0 - vy, x0 - vx); r0 = math.hypot(x0 - vx, y0 - vy)
                ang = ang0 - 5.5 * ein(w_, 1.6); r = r0 * (1 - 0.85 * ein(w_, 1.4))
                x, y = vx + math.cos(ang) * r, vy + math.sin(ang) * r
                sc = 1 - 0.6 * w_; rot = 540 * ein(w_, 1.5); al = 1 - smooth((w_ - 0.55) / 0.45)
                draw_sprite(lay, spr, x, y, sc, rot, 1.0, 1 + 6 * w_, al)
                if w_ < 0.9: out = add_glow(out, x, y, 30, 0.25 * (1 - w_), GOLD2)
            else:
                draw_sprite(lay, spr, x0, y0, 1.0, 0.0, 1.0, (0.1 + 5 * (1 - v)) if v < 1 else 0.0, v)
    out = out * (1 - lay[..., 3:4]) + lay[..., :3]
    return np.clip(out, 0, 1)

_text10_0 = text10
def text10(out, f, s, rides):
    out = _text10_0(out, f, s, rides)
    if not rides:
        for tx in E.TEXT:
            if tx["style"] == "carry": out = text_carry(out, f, tx)
    return out

# ---- the frame (rev 2) -------------------------------------------------------------------------------------
_base10_0 = base10
def base10(s, f):
    img, person = _base10_0(s, f)
    if s.get("sparks"): img = spark_motes(img, f, person, s["sparks"])
    return img, person

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    if s.get("graphic") == "rewind":
        out, _ = rewind_frame(f, s); person = None
    else:
        out, person = base10(s, f)
    out = text10(out, f, s, True)
    if s.get("streak_e") is not None: out = light_streak(out, f, s)
    if tin == "rewind_in": out = rewind_in(out, f, k)
    elif tin in TR2 and k < TR2[tin][2] and P is not None: out = TR2[tin][0](edge10(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge10(n_, "first"), kn, f, s, n_)
    out = edge_bolts(out, f)
    out = bar_sweep(out, f)
    out = hit_ripple(out, f)
    out = accents10(out, f)
    out = text10(out, f, s, False)
    out = finish10(out, f)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


# ============================================================================ v10 rev 3 — the best Flash edit
# Owner notes: cooler transitions; more animations and graphics, each presented in its own way; smooth text that lands
# on the sung words; a more creative, higher-quality loop; best quality.
# New here:
#   picture   restored 2x source (Real-ESRGAN compact, tools/sr_prep.py) instead of a 2.7x cubic blow-up of 720p
#   transitions  PHASE (he vibrates through the frame), WHIRLWIND (the frame is carried off on "...carry OFF"),
#             LICHTENBERG (a branching lightning figure grows out of him; the next shot opens inside it),
#             the particle-accelerator WAVE after the emblem dive, LENS SHATTER (his thrown bolt hits the lens),
#             PERIMETER (he runs a lap of the frame and the picture changes behind him), FROZEN SHATTER (frozen time
#             cracks like glass and hangs in the air until the beat blows it away)
#   loop      the letters of AROUND run a ring that opens into the Speed Force; we fly back through the edit's own
#             moments (newest to oldest) and land on frame 0
#   graphics  the whirlwind (gold debris and pale wind orbiting him in depth, behind/in front via the matte),
#             lightning ribbons spiralling around him in 3-D
#   type      re-timed to the sung onsets; the whirlwind sentence complete (IT'S GONNA / CARRY OFF, then ALL THAT /
#             ISN'T BOUND: the wind takes every word but BOUND); AND charges up through its long note; AROUND runs the ring

T_OPEN = 23.85                                     # the ring of AROUND opens (edit s)
F_OPEN = E.fe(T_OPEN)

# ---- restored source: 2x bands from tools/sr_prep.py ------------------------------------------------------------
_SRI = {}
_SRC = {}
SR_USED = [False]
def sr_index():
    if "i" not in _SRI:
        p = f"{ROOT}/{E.VER}/sr/index.json"
        _SRI["i"] = json.load(open(p)) if os.path.exists(p) else {}
    return _SRI["i"]

def sr_band(pk, k):
    key = f"{pk}:{k}"; b = sr_index().get(key)
    if b is None: return None
    if key not in _SRC:
        if len(_SRC) > 40: _SRC.pop(next(iter(_SRC)))
        im = cv2.imread(f"{ROOT}/{E.VER}/sr/{pk}_{k:06d}.jpg")
        if im is None or im.shape[1] != 2 * (b[1] - b[0]): return None
        _SRC[key] = (b[0], im)
    return _SRC[key]

def src_weights(s, f):
    """the source frames (and weights) render_shot samples for frame f (mirrors source_img / sample)."""
    pk = s["src"]; fps = E.SRC[pk][1]; U = UNIQ[pk]
    t, u, sp = src_time(s, f)
    def idx(tt, mode):
        kf = tt * fps; i = clamp(bisect.bisect_right(U, kf + 0.3) - 1, 0, len(U) - 1)
        if mode == "hold" or i >= len(U) - 1: return [(U[i], 1.0)]
        i0, i1 = U[i], U[i + 1]; a = clamp((kf - i0) / (i1 - i0), 0.0, 1.0)
        if a < 0.05: return [(i0, 1.0)]
        if a > 0.95: return [(i1, 1.0)]
        if mode == "blend": return [(i0, 1 - a), (i1, a)]
        return None
    if sp > 1.7:
        K = int(min(7, max(3, round(sp * 2)))); span = 0.5 / FPS * sp; out_ = []
        for j in range(K):
            out_ += [(k, w / K) for k, w in idx(t + (j / (K - 1) - 0.5) * span, "hold")]
        return out_, t, u
    return idx(t, s.get("interp", "hold")), t, u

_render_shot_v = render_shot
def render_shot(s, f, with_shake=True, want_mask=False):
    SR_USED[0] = False
    if s.get("fit") or "src" not in s: return _render_shot_v(s, f, with_shake, want_mask)
    ws, t, u = src_weights(s, f)
    if not ws: return _render_shot_v(s, f, with_shake, want_mask)
    sw, sh_ = E.SRC[s["src"]][2], E.SRC[s["src"]][3]
    cx, cy, ch = frame_geom(s, f, t, u)
    cw = ch * 9 / 16; sc = W / cw
    dx, dy, rot = shake(f) if with_shake else (0, 0, 0)
    m = 16
    x0 = int(max(0, cx - cw / 2 - m)); x1 = int(min(sw, cx + cw / 2 + m))
    y0 = int(max(0, cy - ch / 2 - m)); y1 = int(min(sh_, cy + ch / 2 + m))
    roi = None
    for k, w in ws:
        b = sr_band(s["src"], k)
        if b is None or b[0] > x0 or b[0] + b[1].shape[1] // 2 < x1: return _render_shot_v(s, f, with_shake, want_mask)
        part = b[1][2 * y0:2 * y1, 2 * (x0 - b[0]):2 * (x1 - b[0])].astype(np.float32)
        roi = part * w if roi is None else roi + part * w
    roi = grade(roi / 255, s, f)
    th_ = math.radians(rot); co, si = math.cos(th_) / sc, math.sin(th_) / sc
    lx, ly = cx - x0, cy - y0
    M = np.float32([[co, -si, lx - co * (W / 2 + dx) + si * (H / 2 + dy)], [si, co, ly - si * (W / 2 + dx) - co * (H / 2 + dy)]])
    M2 = M * 2; M2[0, 2] += 0.5; M2[1, 2] += 0.5                                         # 2x band: sr = 2 * src + 0.5
    out = cv2.warpAffine(roi, M2, (W, H), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)
    SR_USED[0] = True
    if want_mask:
        msk = seg_mask(s, t)
        mr = cv2.resize(msk, (sw, sh_), interpolation=cv2.INTER_LINEAR)[y0:y1, x0:x1]
        mw = cv2.warpAffine(mr, M, (W, H), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
        return np.clip(out, 0, 1), np.clip(mw, 0, 1)
    return np.clip(out, 0, 1)

# ---- graphics: the whirlwind (cold open) ------------------------------------------------------------------------
_WP = {}
def wind_params():
    if "p" in _WP: return _WP["p"]
    rng = np.random.default_rng(91); P = []
    for i in range(120):
        kind = 0 if i < 88 else 1                                   # 0 = gold debris / sparks, 1 = pale wind
        P.append(dict(R=rng.uniform(240, 860), yo=rng.uniform(-0.55, 0.55), ph=rng.uniform(0, 6.283), w=rng.uniform(1.4, 3.0),
                      kind=kind, on=rng.uniform(0, 1), lift=rng.uniform(-40, 40),
                      L=rng.uniform(0.10, 0.32) if kind == 0 else rng.uniform(0.55, 1.10), sz=rng.uniform(0.6, 1.4)))
    _WP["p"] = P; return P

def wind_env(f):
    """the whirlwind builds through the cold open, swells on the bar lines, and is gone at the drop."""
    t = f / FPS
    if t >= th(E.HDROP): return 0.0
    e = t / E.HB; k = (e % 8) * E.HB
    return (0.55 + 0.45 * smooth(t / th(E.HDROP))) * (1 + 0.25 * math.exp(-k / 0.25))

def head_box(s, f, person):
    """(x0, x1, y_floor) of his head: the face track, else the top of the MODNet matte (masked / unlit faces)."""
    bx = face_box(s, f)
    if bx is not None: return bx
    if person is None: return None
    pm = person[::8, ::8] > 0.5; rows = np.nonzero(pm.sum(1) >= 5)[0]
    if not len(rows): return None
    xs = np.nonzero(pm[rows[0]:rows[0] + 40].any(0))[0]; cx = xs.mean() * 8 if len(xs) else W / 2
    return (cx - 290, cx + 290, rows[0] * 8 + 620)

def wind_layer(out, s, f, person, amt):
    a = amt * wind_env(f)
    if a <= 0.01: return out
    t = f / FPS; p = subject_point(s, f, person); cx, cy = p[0], p[1] - 150
    bx = head_box(s, f, person)
    if bx is not None: bx = (bx[0] - 60, bx[1] + 60, bx[2] + 40)
    back = np.zeros((H, W), np.float32); front = np.zeros((H, W), np.float32); pale = np.zeros((H, W), np.float32)
    for q in wind_params():
        if q["on"] > min(1.0, a * 1.15): continue
        th0 = q["ph"] + q["w"] * t; n = 6 if q["kind"] == 0 else 16
        angs = th0 - np.linspace(q["L"], 0, n)
        yb = cy + q["yo"] * 980 + q["lift"] * math.sin(t * 0.7 + q["ph"])
        xs = cx + q["R"] * np.cos(angs); ys = yb + q["R"] * 0.17 * np.sin(angs)
        d = math.sin(th0); dd = (d + 1) / 2                                             # 1 = nearest, in front of him
        if bx is not None and d > -0.2 and bx[0] < xs[-1] < bx[1] and ys[-1] < bx[2]: continue   # never across his face
        pts = np.stack([xs, ys], 1).astype(np.int32)
        if q["kind"] == 1:
            cv2.polylines(pale, [pts], False, 0.30 + 0.25 * dd, 2 if d > 0 else 1, cv2.LINE_AA)
        else:
            tgt = front if d > 0.15 else back
            cv2.polylines(tgt, [pts], False, 0.50 + 0.50 * dd, max(1, int(round((1.4 + 2.6 * dd) * q["sz"]))), cv2.LINE_AA)
    if person is not None:
        pm = np.clip(person * 1.3, 0, 1); back *= (1 - pm); pale *= (1 - 0.75 * pm)
    lay = back * 0.75 + cv2.GaussianBlur(front, (0, 0), 1.4) * 1.3
    glow = cv2.resize(cv2.GaussianBlur(cv2.resize(lay, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 3), (W, H))
    paleb = cv2.GaussianBlur(pale, (0, 0), 2.2)
    return np.clip(out + (lay[..., None] * GOLDW * 0.85 + glow[..., None] * GOLD2 * 1.3) * min(1.0, a * 1.15)
                   + paleb[..., None] * np.array([0.80, 0.84, 0.86], np.float32) * a * 0.45, 0, 1)

# ---- graphics: lightning ribbons spiralling around him in 3-D (behind him through the matte, in front over him) ---
def orbit_ribbons(out, s, f, person, amt):
    """two lightning ribbons spiral round him: behind his head and shoulders (hidden where the matte covers him) and
    across his chest in front; in front of him only below the chin."""
    if amt <= 0.01: return out
    t = f / FPS; bx = head_box(s, f, person); p = subject_point(s, f, person)
    if bx is not None:
        fw = (bx[1] - bx[0]) / 1.5; cx = (bx[0] + bx[1]) / 2; chin = bx[2]; y_top = chin - 1.6 * fw
    else:
        fw = 300.0; cx = p[0]; chin = p[1] - 260; y_top = chin
    R0 = clamp(0.95 * fw, 340, 600); y_bot = H + 120
    back = bolt_canvas(); front = bolt_canvas(); rng = np.random.default_rng(f // 2 * 17 + 3)
    for r_ in range(2):
        ns = 90; ss_ = np.linspace(0, 1, ns)
        ang = r_ * math.pi + t * 3.2 + ss_ * 2 * math.pi * 1.6
        R = R0 + 50 * np.sin(ss_ * 4.5 + t * 2.0 + r_)
        xs = cx + R * np.cos(ang) + rng.normal(0, 6, ns); ys = y_top + (y_bot - y_top) * ss_ + R * 0.14 * np.sin(ang) + rng.normal(0, 6, ns)
        d = np.sin(ang); head = (t * 1.6 + r_ * 0.5) % 1.0
        for i in range(ns - 1):
            if bx is not None and bx[0] - 40 < xs[i] < bx[1] + 40 and ys[i] < bx[2]: continue    # never across his face
            fr_ = d[i] > 0 and ys[i] > chin
            hb = math.exp(-((ss_[i] - head) / 0.06) ** 2)
            v = int(min(255, 150 + 60 * (d[i] + 1) / 2 + 110 * hb))
            cv2.line(front if fr_ else back, (int(xs[i]), int(ys[i])), (int(xs[i + 1]), int(ys[i + 1])), v, 3 if (fr_ or hb > 0.5) else 2, cv2.LINE_AA)
    if person is not None: back = (back.astype(np.float32) * (1 - np.clip(person * 1.4, 0, 1))).astype(np.uint8)
    fl = 0.8 + 0.2 * math.sin(f * 1.3)
    return np.clip(out + light_from(back, 0.75 * amt * fl) + light_from(front, 0.95 * amt * fl), 0, 1)

# ---- transitions ------------------------------------------------------------------------------------------------
def vib(img, amt, f, seed, n=4):
    """molecular vibration: n jittered copies, a row-wise shimmer, the colour channels pulled apart."""
    if amt < 0.6: return img
    rng = np.random.default_rng(f * 31 + seed); acc = np.zeros_like(img)
    for i in range(n):
        ddx, ddy = rng.normal(0, amt, 2)
        acc += cv2.warpAffine(img, np.float32([[1, 0, ddx], [0, 1, ddy * 0.5]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    acc /= n
    mx = (_GX + amt * 0.45 * np.sin(_GY * 0.11 + f * 2.3)).astype(np.float32)
    acc = cv2.remap(acc, mx, _GY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    o = acc.copy(); d = int(amt * 0.7)
    o[..., 2] = np.roll(acc[..., 2], d, 1); o[..., 0] = np.roll(acc[..., 0], -d, 1)
    return o

def edge_glow(img, amt):
    """every edge in the picture lights up gold (the molecules excited)."""
    if amt <= 0.01: return img
    L = lum8(cv2.resize(img, (W // 2, H // 2), interpolation=cv2.INTER_AREA))
    g = np.clip(np.abs(cv2.Laplacian(cv2.GaussianBlur(L, (0, 0), 1.2), cv2.CV_32F, ksize=3)) * 7, 0, 1)
    g = cv2.resize(cv2.GaussianBlur(g, (0, 0), 1.2), (W, H))
    return img + g[..., None] * (GOLDW * 0.6 + GOLD2 * 0.5) * amt

def phase_through(A, B, j, f, sa, sb, pre=10, post=12):
    """PHASE: he vibrates his molecules and passes through the frame: the picture shakes apart into chromatic copies,
    every edge lights up, the next shot shows through it for a few frames, then settles out of the vibration."""
    if j < 0:
        u = (j + pre + 1) / pre; amt = 1 + 30 * ein(u, 2.2)
        o = vib(zoom_about(A, W / 2, H * 0.45, 1 + 0.10 * ein(u, 2)), amt, f, 1)
        a = clamp((j + 4) / 4, 0, 1) * 0.5
        if a > 0: o = o * (1 - a) + vib(zoom_about(B, W / 2, H * 0.45, 1.14), amt, f, 2) * a
        return np.clip(edge_glow(o, 0.55 * u) * (1 + 0.25 * u), 0, 1)
    v = (j + 1) / post; amt = 31 * (1 - eout(v, 2.0))
    o = vib(zoom_about(B, W / 2, H * 0.45, 1 + 0.14 * (1 - eout(v, 2.2))), amt, f, 2)
    a = clamp(0.5 - j / 4 * 0.5, 0, 0.5)
    if a > 0: o = o * (1 - a) + vib(zoom_about(A, W / 2, H * 0.45, 1.12 + 0.05 * j), amt, f, 1) * a
    return np.clip(edge_glow(o, 0.55 * (1 - v)) * (1 + 0.25 * (1 - v)), 0, 1)

_TW = {}
def twist(img, cx, cy, T, zoom=1.0, n=1, spread=0.0):
    key = (int(cx), int(cy))
    if key not in _TW:
        dx, dy = _GX - cx, _GY - cy
        r = np.sqrt(dx * dx + dy * dy); _TW[key] = (r, np.arctan2(dy, dx), np.exp(-(r / 860.0) ** 1.5))
    r, th0, wgt = _TW[key]; acc = None; rr = r / zoom
    for i in range(n):
        a = th0 + (T - spread * i / max(1, n - 1)) * wgt
        w = cv2.remap(img, (cx + rr * np.cos(a)).astype(np.float32), (cy + rr * np.sin(a)).astype(np.float32), cv2.INTER_LINEAR,
                      borderMode=cv2.BORDER_REFLECT)
        acc = w if acc is None else acc + w
    return acc / n

def vortex_streaks(cx, cy, f, amt, seed=5):
    """wind and debris torn round the eye of the whirlwind."""
    cv = np.zeros((H, W), np.float32); rng = np.random.default_rng(seed); t = f / FPS
    for i in range(70):
        R = rng.uniform(90, 1000); ph = rng.uniform(0, 6.283); w = 9 + 10 * (300 / (R + 150))
        a0 = ph + w * t * (0.6 + amt); L_ = 0.25 + 0.9 * amt
        angs = a0 - np.linspace(L_, 0, 14)
        pts = np.stack([cx + R * np.cos(angs), cy + R * 0.82 * np.sin(angs)], 1).astype(np.int32)
        cv2.polylines(cv, [pts], False, rng.uniform(0.3, 1.0), 2 if R > 400 else 1, cv2.LINE_AA)
    return cv

def whirlwind(A, B, j, f, sa, sb, pre=12, post=14):
    """WHIRLWIND (on "...carry OFF"): the whirlwind carries the frame off. The picture twists into a spiral round the
    eye of the storm (angular blur, wind and gold debris torn round it); the next shot unwinds out of the same spin."""
    cx, cy = W / 2, H * 0.46
    if j < 0:
        u = (j + pre + 1) / pre; T = 4.4 * ein(u, 2.3)
        o = twist(A, cx, cy, T, 1 + 0.16 * ein(u, 2), n=1 + int(4 * u), spread=0.7 * u); amt = u
    else:
        v = (j + 1) / post; T = -4.4 * (1 - eout(v, 2.1))
        o = twist(B, cx, cy, T, 1 + 0.16 * (1 - eout(v, 2)), n=1 + int(4 * (1 - v)), spread=0.7 * (1 - v)); amt = 1 - v
    cv = vortex_streaks(cx, cy, f, amt)
    sl = cv2.GaussianBlur(cv, (0, 0), 1.3) * amt
    glow = cv2.resize(cv2.GaussianBlur(cv2.resize(sl, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 4), (W, H))
    eye = np.exp(-(((_GX - cx) / 260) ** 2 + ((_GY - cy) / 300) ** 2))[..., None] * 0.18 * amt
    return np.clip(o * (1 + 0.15 * amt) + sl[..., None] * np.array([0.85, 0.88, 0.90], np.float32) * 0.55 + glow[..., None] * GOLD2 * 0.9
                   + eye * GOLDW, 0, 1)

_LT = {}
def lich_tree(px, py, box, seed=5):
    """a Lichtenberg figure: branching discharge paths from (px, py); segments carry the time they are reached."""
    key = (int(px) // 8, int(py) // 8, seed)
    if key in _LT: return _LT[key]
    rng = np.random.default_rng(seed); segs = []; stack = []
    for k in range(7):
        stack.append((px, py, k / 7 * 2 * math.pi + rng.uniform(-0.25, 0.25), 0.0, 0, 4.0))
    while stack and len(segs) < 3500:
        x, y, a, t, gen, wd = stack.pop(); L = 0.0; lim = rng.uniform(650, 1400) / (1 + 0.55 * gen)
        while True:
            step = rng.uniform(12, 24); a += rng.normal(0, 0.30)
            nx, ny = x + math.cos(a) * step, y + math.sin(a) * step
            if not (-60 < nx < W + 60 and -60 < ny < H + 60): break
            if box is not None and box[0] < nx < box[1] and ny < box[2]: break          # the discharge stops at his face
            t2 = t + step * (1 + 0.25 * gen); segs.append((x, y, nx, ny, t2, wd)); x, y, t = nx, ny, t2; L += step
            if gen < 4 and rng.random() < 0.06: stack.append((x, y, a + rng.choice([-1, 1]) * rng.uniform(0.35, 1.0), t, gen + 1, max(1.0, wd * 0.62)))
            if L > lim: break
    arr = np.array(segs, np.float32); arr[:, 4] /= max(1.0, float(np.percentile(arr[:, 4], 97)))
    _LT[key] = arr; return arr

def lichtenberg(A, B, j, f, sa, sb, pre=10, post=14):
    """LICHTENBERG: a branching lightning figure grows out of his chest across the whole frame (stopping short of his
    face); the next shot opens inside the branches, the newest tips white-hot."""
    p = subject_point(sa, sa["f1"] - 1); box = face_box(sa, sa["f1"] - 1)
    if box is not None: box = (box[0] - 30, box[1] + 30, box[2] + 20)
    else: box = (p[0] - 230, p[0] + 230, p[1] - 340)
    p = (p[0], p[1] - 200)                                                              # from the emblem, not the belt                                    # masked: no face track, keep his head clear
    segs = lich_tree(p[0], p[1], box)
    n = pre + post; tau = (j + pre + 1) / n * 1.15
    cv = np.zeros((H, W), np.uint8); tips = np.zeros((H, W), np.uint8)
    vis = segs[segs[:, 4] <= tau]
    for wd in (4, 3, 2, 1):
        sel = vis[np.abs(vis[:, 5] - wd) < 0.75] if wd > 1 else vis[vis[:, 5] < 1.75]
        if len(sel):
            lines = sel[:, :4].reshape(-1, 2, 2).astype(np.int32)
            cv2.polylines(cv, list(lines), False, 255, max(1, int(wd * 0.75)), cv2.LINE_AA)
    new = vis[vis[:, 4] > tau - 0.08]
    if len(new): cv2.polylines(tips, list(new[:, :4].reshape(-1, 2, 2).astype(np.int32)), False, 255, 3, cv2.LINE_AA)
    def crisp(c, a):                                                                       # a sharp core, a modest glow
        c = c.astype(np.float32) / 255; sm = cv2.resize(c, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        g = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 2.5), (W, H)) * 1.6 + cv2.resize(cv2.GaussianBlur(sm, (0, 0), 9), (W, H)) * 1.2
        return (np.clip(g, 0, 1)[..., None] * GOLD2 * 0.55 + c[..., None] * GOLDW * 1.05) * a
    if j < 0:
        u = (j + pre + 1) / pre
        return np.clip(A * (1 - 0.30 * u) + crisp(cv, 0.8 + 0.3 * u) + crisp(tips, 0.8), 0, 1)
    v = (j + 1) / post
    dist = cv2.distanceTransform(255 - cv, cv2.DIST_L2, 3)
    R = 6 + 1100 * ein(v, 1.7)
    m = np.clip((R - dist) / 30.0, 0, 1)[..., None]
    o = B * m + A * (1 - m) * (1 - 0.3 * (1 - v))
    rim = np.exp(-((dist - R) / 10.0) ** 2)[..., None] * (1 - v)
    return np.clip(o + rim * GOLD2 * 0.7 + crisp(cv, 1.1 * (1 - v) ** 1.3) + crisp(tips, 0.8 * (1 - v)), 0, 1)

def drop_wave(out, f, s):
    """the particle-accelerator wave: as he bursts out of the emblem a refracting dome of dark matter rings out."""
    k = f - s["f0"] - 2
    if k < 0 or k > 30: return out
    v = k / 30; cx, cy = W / 2, H * 0.47
    R = 160 + 2000 * eout(v, 1.45)
    dx, dy = _GX - cx, _GY - cy; r = np.sqrt(dx * dx + dy * dy) + 1e-3
    band = np.exp(-((r - R) / 95.0) ** 2); disp = band * 70 * (1 - v)
    o = cv2.remap(out, (_GX - dx / r * disp).astype(np.float32), (_GY - dy / r * disp).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    o = rgb_split(o, 10 * (1 - v)) * band[..., None] + o * (1 - band[..., None])
    ins = (np.clip((R - r) / 220, 0, 1) * 0.18 * (1 - v))[..., None]
    o = o * (1 - ins) + ins * (lum8(o)[..., None] * np.array([0.95, 0.80, 0.66], np.float32) * 1.1)
    rim = np.exp(-((r - R) / 7.0) ** 2) * 0.9 + np.exp(-((r - R) / 40.0) ** 2) * 0.3
    return np.clip(o + rim[..., None] * GOLDW * (1 - v) ** 1.2, 0, 1)

# ---- glass: shards around an impact point (Voronoi, denser at the impact), electric cracks -------------------------
_GS = {}
def glass_shards(key, cx, cy, n=130, seed=7):
    if key in _GS: return _GS[key]
    rng = np.random.default_rng(seed); pts = [(cx, cy)]
    for i in range(n):
        r = (rng.random() ** 1.9) * 1700; a = rng.uniform(0, 2 * math.pi)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a) * 1.25
        if 0 <= x < W and 0 <= y < H: pts.append((x, y))
    for x in (0, W - 1):
        for y in np.linspace(0, H - 1, 8): pts.append((x, y))
    for y in (0, H - 1):
        for x in np.linspace(0, W - 1, 5): pts.append((x, y))
    sd = cv2.Subdiv2D((0, 0, W, H))
    for q in pts: sd.insert((float(min(W - 1, max(0, q[0]))), float(min(H - 1, max(0, q[1])))))
    facets, centers = sd.getVoronoiFacetList([]); L = []
    for poly, c in zip(facets, centers):
        poly = np.array(poly, np.float32); poly[:, 0] = np.clip(poly[:, 0], 0, W - 1); poly[:, 1] = np.clip(poly[:, 1], 0, H - 1)
        x0, y0 = poly.min(0).astype(int); x1, y1 = poly.max(0).astype(int) + 1
        if x1 - x0 < 3 or y1 - y0 < 3: continue
        m = np.zeros((y1 - y0, x1 - x0), np.uint8); cv2.fillPoly(m, [(poly - [x0, y0]).astype(np.int32)], 255, cv2.LINE_AA)
        d = math.hypot(c[0] - cx, c[1] - cy) + 1
        L.append(dict(poly=poly, box=(x0, y0, x1, y1), mask=m.astype(np.float32) / 255, c=(float(c[0]), float(c[1])), d=d,
                      v=((c[0] - cx) / d, (c[1] - cy) / d), sp=rng.uniform(0.7, 1.3), w=rng.uniform(-1, 1), dz=rng.uniform(0.5, 1.5)))
    L.sort(key=lambda s_: s_["dz"])
    cr = np.zeros((H, W), np.uint8)
    for s_ in L:
        if s_["d"] < 1200: cv2.polylines(cr, [s_["poly"].astype(np.int32)], True, int(255 * (1 - s_["d"] / 1300) ** 0.6), 2, cv2.LINE_AA)
    for i in range(18):
        a = i / 18 * 2 * math.pi + rng.uniform(-0.12, 0.12); qs = [(cx, cy)]; rr = 0
        for k in range(10):
            rr += rng.uniform(60, 150); a += rng.uniform(-0.08, 0.08); qs.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        cv2.polylines(cr, [np.array(qs, np.int32)], False, 255, 2, cv2.LINE_AA)
    cv2.circle(cr, (int(cx), int(cy)), 18, 255, -1, cv2.LINE_AA)
    _GS[key] = dict(L=L, crack=cr, c=(cx, cy)); return _GS[key]

def crack_reveal(G, u):
    """the cracks spread out from the impact (u 0..1)."""
    cx, cy = G["c"]; R = 40 + 1500 * u
    m = (np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2) < R).astype(np.uint8)
    return (G["crack"] * m).astype(np.uint8)

def draw_shards(A, base, G, prog, mode="fly"):
    """composite the shards of A over base. mode fly: they burst toward the lens; drift: they hang in frozen time."""
    out = base.copy(); cx, cy = G["c"]; glint = np.zeros((H, W), np.uint8)
    for s_ in G["L"]:
        x0, y0, x1, y1 = s_["box"]; pcx, pcy = s_["c"]
        if mode == "fly":
            q = clamp((prog - s_["d"] / 1700 * 0.30) / 0.70, 0, 1)
            mv = (60 + 1300 * ein(q, 1.7)) * s_["sp"] * q; sc = 1 + 2.4 * ein(q, 2.0) * s_["dz"]; ang = s_["w"] * 70 * q
            a = 1 - smooth((q - 0.55) / 0.45)
            tx, ty = s_["v"][0] * mv, s_["v"][1] * mv + 250 * q * q
        else:
            q = prog; mv = (14 + 110 * q) * s_["sp"] * min(1.0, 400 / s_["d"] + 0.35); sc = 1 + 0.10 * q * s_["dz"]; ang = s_["w"] * 9 * q
            a = 1.0; tx, ty = s_["v"][0] * mv, s_["v"][1] * mv
        if a <= 0.01: continue
        Mr = cv2.getRotationMatrix2D((pcx, pcy), ang, sc); Mr[0, 2] += tx; Mr[1, 2] += ty
        corners = np.array([[x0, y0, 1], [x1, y0, 1], [x0, y1, 1], [x1, y1, 1]], np.float32) @ Mr.T
        X0, Y0 = max(0, int(corners[:, 0].min()) - 2), max(0, int(corners[:, 1].min()) - 2)
        X1, Y1 = min(W, int(corners[:, 0].max()) + 3), min(H, int(corners[:, 1].max()) + 3)
        if X1 <= X0 or Y1 <= Y0: continue
        Mp = Mr.copy(); Mp[:, 2] += Mr[:, 0] * x0 + Mr[:, 1] * y0; Mp[0, 2] -= X0; Mp[1, 2] -= Y0
        patch = cv2.warpAffine(np.ascontiguousarray(A[y0:y1, x0:x1]), Mp, (X1 - X0, Y1 - Y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        mk = cv2.warpAffine(s_["mask"], Mp, (X1 - X0, Y1 - Y0), flags=cv2.INTER_LINEAR, borderValue=0)[..., None] * a
        sub = out[Y0:Y1, X0:X1]
        out[Y0:Y1, X0:X1] = sub * (1 - mk) + patch * (1 + 0.12 * (1 - q)) * mk
        pp = (np.hstack([s_["poly"], np.ones((len(s_["poly"]), 1), np.float32)]) @ Mr.T).astype(np.int32)
        cv2.polylines(glint, [pp], True, int(255 * a * (0.5 + 0.5 * s_["dz"] / 1.5)), 1, cv2.LINE_AA)
    return out, glint

def lens_shatter(A, B, j, f, sa, sb, pre=8, post=18):
    """LENS SHATTER: the lightning he throws comes at the camera, hits the lens; the glass cracks with electricity
    running through the cracks, then bursts toward us in shards and the next shot is behind it."""
    P = (330.0, 1180.0); G = glass_shards("lens", P[0], P[1], 130, 11)
    if j < 0:
        u = (j + pre + 1) / pre; cv = bolt_canvas()
        p0 = (-60.0, 1420.0); tip = (p0[0] + (P[0] - p0[0]) * ein(u, 1.5), p0[1] + (P[1] - p0[1]) * ein(u, 1.5))
        put_bolt(cv, p0, tip, 2400 + f, int(3 + 9 * u), 0.20, 7, 2)
        o = A * (1 - 0.2 * u) + light_from(cv, 1.0 + 0.8 * u)
        return np.clip(add_glow(o, tip[0], tip[1], 60 + 220 * u, 0.5 + 0.8 * u, GOLDW), 0, 1)
    v = (j + 1) / post
    if j < 4:                                                                             # the hit: flash, the cracks run out
        cr = crack_reveal(G, eout((j + 1) / 4, 1.5))
        fl = 1 - j / 4
        o = A * (1 - 0.15 * fl) + light_from(cr, 1.3) + cv2.GaussianBlur(cr.astype(np.float32) / 255, (0, 0), 1)[..., None] * GOLDW * 0.8
        o = add_glow(o, P[0], P[1], 380, 1.1 * fl, GOLDW)
        return np.clip(o, 0, 1)
    prog = (j - 3) / (post - 3)
    Bz = zoom_about(B, W / 2, H * 0.47, 1.10 - 0.10 * eout(prog, 2))
    Ac = np.clip(A + cv2.GaussianBlur(G["crack"].astype(np.float32) / 255, (0, 0), 1)[..., None] * GOLDW * 0.5, 0, 1)
    o, gl = draw_shards(Ac, Bz, G, prog, "fly")
    return np.clip(o + light_from(gl, 0.7 * (1 - prog)), 0, 1)

def perim_path():
    """the frame's perimeter (inset), clockwise from bottom centre: [(x, y, cumulative length)]."""
    if "pp" in _GS: return _GS["pp"]
    m = 46; pts = [(W / 2, H - m), (m, H - m), (m, m), (W - m, m), (W - m, H - m), (W / 2, H - m)]
    out_ = []; acc = 0.0
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        L = math.hypot(xb - xa, yb - ya); n = max(2, int(L / 8))
        for i in range(n):
            u = i / n; out_.append((xa + (xb - xa) * u, ya + (yb - ya) * u, acc + L * u))
        acc += L
    out_.append((W / 2, H - m, acc)); arr = np.array(out_, np.float32); _GS["pp"] = arr; return arr

def perim_maps():
    """per pixel: the lap position of its edge point (radial projection) and its depth in from the edge (0 edge, 1 centre)."""
    if "pm" in _GS: return _GS["pm"]
    pp = perim_path()
    CY = H * 0.64                                                                          # his chest: the wake closes there
    phi_p = (np.degrees(np.arctan2(pp[:, 1] - CY, pp[:, 0] - W / 2)) - 90) % 360; phi_p[0] = 0.0; phi_p[-1] = 360.0
    phi_p = np.maximum.accumulate(phi_p)
    phi = (np.degrees(np.arctan2(_GY - CY, _GX - W / 2)) - 90) % 360
    s_pix = np.interp(phi, phi_p, pp[:, 2]).astype(np.float32)
    rb = np.interp(phi, phi_p, np.hypot(pp[:, 0] - W / 2, pp[:, 1] - CY))
    din = np.clip(1 - np.hypot(_GX - W / 2, _GY - CY) / rb, 0, 1).astype(np.float32)
    _GS["pm"] = (s_pix, din); return _GS["pm"]

def perimeter(A, B, j, f, sa, sb, pre=8, post=14):
    """PERIMETER: he runs laps round the edge of the frame as a streak of lightning; the new picture fills in behind
    him as a spiral wake that closes on the centre (his own face arrives last, softly)."""
    pp = perim_path(); Ltot = float(pp[-1, 2]); kap = 0.45
    s_pix, din = perim_maps()
    p = (j + pre + 1) / (pre + post); sh_ = (1 + kap) * Ltot * 1.04 * (0.5 - 0.5 * math.cos(math.pi * p))
    front = s_pix + din * kap * Ltot
    soft = 60 + 260 * din
    m = cv2.GaussianBlur(np.clip((sh_ - front) / soft, 0, 1), (0, 0), 16)[..., None]
    o = B * m + A * (1 - m)
    edge = np.exp(-((sh_ - front) / (18 + 120 * din)) ** 2) * (1 - din) ** 0.7
    hs = sh_ % Ltot; i = int(np.searchsorted(pp[:, 2], hs)); i = min(i, len(pp) - 1); hx, hy = pp[i, 0], pp[i, 1]
    run = sh_ < (1 + kap) * Ltot                                                          # still running
    cv = bolt_canvas(); tail = 1100
    if run:
        ts = np.linspace(sh_ - tail, sh_, 90); ts = ts[ts > 0]
        if len(ts) > 1:
            xs = np.interp(ts % Ltot, pp[:, 2], pp[:, 0]); ys = np.interp(ts % Ltot, pp[:, 2], pp[:, 1])
            a_ = (ts - (sh_ - tail)) / tail
            for k in range(len(ts) - 1):
                if abs(xs[k + 1] - xs[k]) + abs(ys[k + 1] - ys[k]) > 200: continue
                cv2.line(cv, (int(xs[k]), int(ys[k])), (int(xs[k + 1]), int(ys[k + 1])), int(255 * a_[k] ** 1.3), int(3 + 22 * a_[k] ** 1.5), cv2.LINE_AA)
        for q in range(2):
            put_bolt(cv, (hx, hy), (hx + (W / 2 - hx) * (0.15 + 0.1 * q), hy + (H / 2 - hy) * (0.08 + 0.06 * q)), 2600 + f * 3 + q, 2, 0.35, 5, 1)
    a_env = math.sin(math.pi * clamp(p, 0, 1)) ** 0.6
    o = o + edge[..., None] * (GOLD2 * 0.55 + GOLDW * 0.25) * a_env + light_from(cv, 1.35)
    if run: o = add_glow(o, hx, hy, 90, 1.2, GOLDW)
    return np.clip(o, 0, 1)

def frozen_shatter(A, B, j, f, sa, sb, pre=6, post=41):
    """FROZEN SHATTER: in stopped time the frozen frame cracks like glass; the shards separate and hang in the air
    (the next frozen moment visible between them) and the beat that restarts time blows them away."""
    P = (330.0, 1240.0); G = glass_shards("frozen", P[0], P[1], 110, 23)
    if j < 0:
        u = (j + pre + 1) / pre; cr = crack_reveal(G, ein(u, 1.3) * 0.9)
        return np.clip(A + light_from(cr, 0.8) + cv2.GaussianBlur(cr.astype(np.float32) / 255, (0, 0), 1)[..., None] * GOLDW * 0.6, 0, 1)
    hit = fh(E.STUT_HITS[2]) - sb["f0"]                                                   # e84: time restarts
    Ac = np.clip(A + cv2.GaussianBlur(G["crack"].astype(np.float32) / 255, (0, 0), 1)[..., None] * GOLDW * 0.45, 0, 1)
    if j < hit - 1:
        o, gl = draw_shards(Ac, B, G, ein((j + 1) / (hit - 1), 0.8), "drift")
        return np.clip(o + light_from(gl, 0.95), 0, 1)
    q = (j - hit + 1) / (post - hit + 1)
    o, gl = draw_shards(Ac, B, G, 0.25 + 0.75 * q, "fly")
    return np.clip(o + light_from(gl, 0.6 * (1 - q)), 0, 1)

TR2.update({"phase": (phase_through, 10, 12), "whirlwind": (whirlwind, 12, 14), "lichtenberg": (lichtenberg, 10, 14),
            "lens_shatter": (lens_shatter, 8, 18), "perimeter": (perimeter, 8, 14), "frozen_shatter": (frozen_shatter, 6, 41)})

# ---- the loop: the ring opens into the Speed Force; we fly back through the edit's own moments to frame 0 --------
TUN_PANELS = [1330, 1215, 1120, 1010, 905, 790, 740, 700, 640, 520, 440, 300, 200, 130, 75]      # newest -> oldest
_TP = {}
def tunnel_panels():
    if "p" in _TP: return _TP["p"]
    P = []
    for fr in TUN_PANELS:
        s_ = shot_at(fr); img, _ = base10(s_, fr)
        P.append(cv2.resize(img, (432, 768), interpolation=cv2.INTER_AREA))
    full, _ = base10(SHOTS[0], 0)
    _TP["p"] = (P, full); return _TP["p"]

_SF = {}
def sf_grid():
    if "g" in _SF: return _SF["g"]
    dx, dy = _GX - W / 2, _GY - H / 2
    r = np.sqrt(dx * dx + dy * dy); rng = np.random.default_rng(13); nb = 900
    s1 = rng.random(nb) ** 7; s1 = np.convolve(np.concatenate([s1[-4:], s1, s1[:4]]), np.hanning(5) / 2.5, "same")[4:-4]
    _SF["g"] = (r, np.arctan2(dy, dx), np.log(r + 40), s1.astype(np.float32), rng.uniform(0, 1, nb).astype(np.float32), rng.random(nb).astype(np.float32))
    return _SF["g"]

def speedforce_bg(z, t):
    """the Speed Force: streaks of lightning rushing past along a turning tunnel; a bright far end."""
    r, th0, lr, s1, ph, col = sf_grid(); nb = len(s1)
    bi = ((((th0 + t * 0.9) % (2 * math.pi)) / (2 * math.pi)) * nb).astype(np.int32) % nb
    S = s1[bi]; m = (lr * 1.5 - z * 1.25 + ph[bi]) % 1.0
    I_ = S * (m ** 9) * 2.6 * np.clip(r / 240, 0, 1)
    C = col[bi][..., None]
    core = np.exp(-(r / 430) ** 2)[..., None]
    o = SLATE * 0.55 + core * (GOLDW * 0.55 + 0.25) + I_[..., None] * (GOLD2 * (C > 0.3) + np.array([1.0, 0.86, 0.62], np.float32) * (C <= 0.3) * 0.9)
    return o

Z_STEP, S_P = 0.62, 0.46
Z_F = 1.0 + Z_STEP * len(TUN_PANELS) + 0.9
def tun_u(f): return clamp((f - F_OPEN + 1) / (E.DUR_F - F_OPEN), 0, 1)
def tun_z(u): return (Z_F - 1.0) * (1 - (1 - u) ** 2.3)

def place_panel(o, img, d, X, Y, S, roll, a, border, glint):
    """a camera-facing panel at distance d (screen-centre units), alpha a; its border drawn into `border`."""
    pw = S * W / d; ph_ = pw * 16 / 9; cxp = W / 2 + X * (W / 2) / d; cyp = H / 2 + Y * (H / 2) / d
    if pw < 6 or cxp + pw < -50 or cxp - pw > W + 50 or cyp + ph_ < -50 or cyp - ph_ > H + 50: return o
    sc = pw / img.shape[1]
    M = cv2.getRotationMatrix2D((img.shape[1] / 2, img.shape[0] / 2), roll, sc); M[0, 2] += cxp - img.shape[1] / 2; M[1, 2] += cyp - img.shape[0] / 2
    R_ = int(math.hypot(pw, ph_) / 2) + 4
    X0, Y0, X1, Y1 = max(0, int(cxp) - R_), max(0, int(cyp) - R_), min(W, int(cxp) + R_), min(H, int(cyp) + R_)
    if X1 <= X0 or Y1 <= Y0: return o
    M2 = M.copy(); M2[0, 2] -= X0; M2[1, 2] -= Y0
    rgba_ = cv2.warpAffine(np.dstack([img, np.ones(img.shape[:2], np.float32)]), M2, (X1 - X0, Y1 - Y0), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    al = rgba_[..., 3:4] * a
    o[Y0:Y1, X0:X1] = o[Y0:Y1, X0:X1] * (1 - al) + rgba_[..., :3] * al
    cs = np.array([[0, 0, 1], [img.shape[1], 0, 1], [img.shape[1], img.shape[0], 1], [0, img.shape[0], 1]], np.float32) @ M.T
    cv2.polylines(border, [cs.astype(np.int32)], True, int(255 * glint * a), 3, cv2.LINE_AA)
    return o

def tunnel_frame(f):
    """from F_OPEN to the end: the Speed Force tunnel, the edit's moments flying past (newest first), frame 0 ahead."""
    u = tun_u(f); z = tun_z(u); t = (f - F_OPEN) / FPS
    spd = (tun_z(min(1, u + 0.02)) - z) / 0.02 / (Z_F - 1.0) / 2.3
    P, full = tunnel_panels()
    o = speedforce_bg(z, t).astype(np.float32)
    rings = bolt_canvas()
    for k in range(14):                                                                  # rings of light passing
        d = 0.6 + 0.95 * k - z % 0.95
        if 0.25 < d < 12:
            cv2.ellipse(rings, (W // 2, H // 2), (int(560 / d), int(990 / d)), 0, 0, 360, int(200 * clamp((12 - d) / 4, 0, 1)), 2, cv2.LINE_AA)
    o = o + light_from(rings, 0.45 * (1 - smooth((u - 0.70) / 0.25)))
    border = bolt_canvas()
    df = Z_F - z
    gf = 1.0 if u < 0.8 else 1 - 0.65 * smooth((u - 0.8) / 0.2)
    o = place_panel(o, full if df < 3.0 else cv2.resize(full, (432, 768), interpolation=cv2.INTER_AREA), df, 0, 0, 1.0, 0, clamp((14 - df) / 3, 0, 1), border, gf)
    for i in range(len(P) - 1, -1, -1):                                                   # far (old) first, near (new) last
        d = 1.0 + Z_STEP * (i + 1) - z
        if d < 0.22 or d > 11: continue
        a = clamp((10 - d) / 2.5, 0, 1) * clamp((d - 0.22) / 0.25, 0, 1)
        ang = i * 2.39996 + 0.7; rho = 0.98 + 0.12 * (i % 3)
        o = place_panel(o, P[i], d, math.cos(ang) * rho, math.sin(ang) * rho * 0.8, S_P, 6 if i % 2 else -6, a, border, 1.0)
    cv = bolt_canvas(); rng = np.random.default_rng(f // 2 * 7 + 1)
    for q in range(3 if u < 0.85 else 0):
        a0 = rng.uniform(0, 2 * math.pi); r0, r1 = rng.uniform(200, 380), rng.uniform(700, 1100)
        put_bolt(cv, (W / 2 + r0 * math.cos(a0), H / 2 + r0 * math.sin(a0) * 1.4), (W / 2 + r1 * math.cos(a0 + 0.25), H / 2 + r1 * math.sin(a0 + 0.25) * 1.4), 2700 + f + q, 2, 0.3, 6, 1)
    o = np.clip(o, 0, 1); dfin = Z_F - z                                                  # nothing in front of the landing panel
    o = o + light_from(cv, 0.7 * (1 - u) * (1 - smooth((u - 0.6) / 0.25))) + light_from(border, 0.9)
    if spd > 0.05: o = radial_blur(np.clip(o, 0, 1), W / 2, H / 2, 1.0, 1.0 + 0.05 * min(1.5, spd), 4)
    return np.clip(o, 0, 1)

def light_streak3(img, f, s):
    """the run becomes light: the picture smears into speed and brightens (no collapse: the ring opens in it)."""
    k = f - fh(s["streak_e"])
    if k < 0: return img
    u = clamp((k + 1) / (s["f1"] - fh(s["streak_e"])), 0, 1)
    return np.clip(hblur(img, 4 + 160 * ein(u, 1.6)) * (1 + 0.5 * u), 0, 1)

_RL = {}
def portal_R(t): return 40 + 1300 * ein(clamp((t - T_OPEN) / 0.50, 0, 1), 1.9)
def portal(out, f):
    """the ring of AROUND: a ring of lightning opens in the middle of the run and the Speed Force is inside it."""
    t = f / FPS
    if t < T_OPEN or t > T_OPEN + 0.52: return out
    R = portal_R(t); cx, cy = W / 2, H / 2
    if f >= fh(E.E_REW):
        if "run" not in _RL:
            rs = by_name("run"); _RL["run"] = light_streak3(edge10(rs, "last"), rs["f1"] - 1, rs)
        outside, inside = _RL["run"], out
    else:
        outside, inside = out, tunnel_frame(f)
    rr = np.sqrt((_GX - cx) ** 2 + ((_GY - cy) / 1.35) ** 2)
    band = np.exp(-((rr - R - 40) / 45.0) ** 2) * 36                                     # the space round the ring bends
    outside = cv2.remap(outside, (_GX - (_GX - cx) / (rr + 1) * band).astype(np.float32), (_GY - (_GY - cy) / (rr + 1) * band).astype(np.float32),
                        cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    m = np.clip((R - rr) / 8, 0, 1)[..., None]
    o = inside * m + outside * (1 - m)
    ring = np.exp(-((rr - R) / 5.0) ** 2) + 0.35 * np.exp(-((rr - R) / 26.0) ** 2)
    cv = bolt_canvas(); rng = np.random.default_rng(f * 3 + 5)
    for q in range(6):
        a0 = rng.uniform(0, 2 * math.pi); a1 = a0 + rng.uniform(0.3, 0.8)
        put_bolt(cv, (cx + R * math.cos(a0), cy + R * 1.35 * math.sin(a0)), (cx + R * math.cos(a1), cy + R * 1.35 * math.sin(a1)), 2800 + f + q, 2, 0.25, 5, 0)
    fade = 1 - smooth((t - T_OPEN - 0.40) / 0.12)
    return np.clip(o + (ring[..., None] * GOLDW * 1.1 + light_from(cv, 0.9)) * fade, 0, 1)

def tunnel_in(out, f, k, n=10):
    """frame 0: we have landed in the first shot; the panel's border glow and the speed settle."""
    if k >= n: return out
    v = k / n; g = 0.35 * (1 - smooth(v))
    border = bolt_canvas(); cv2.rectangle(border, (1, 1), (W - 2, H - 2), int(255 * g / 0.35), 3, cv2.LINE_AA)
    return np.clip(out + light_from(border, 0.9 * g / 0.35 * 0.35), 0, 1)

# ---- type -------------------------------------------------------------------------------------------------------
_LS = {}
def letter_sprite(lm, size, emph):
    """one letter in the approved caption construction: face colour, dark keyline, soft drop shadow, gold glow (emph)."""
    key = (id(lm), size, emph)
    if key in _LS: return _LS[key]
    pad = 36; mm = np.pad(lm, pad); k_ = max(3, int(size * 0.07)) | 1
    st_ = cv2.dilate(mm, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_, k_)))
    sh = np.roll(cv2.GaussianBlur(mm, (0, 0), size * 0.13), int(size * 0.05), 0) * 0.85
    a = np.maximum(np.maximum(mm, st_ * 0.92), sh)
    col = np.zeros(mm.shape + (3,), np.float32) + np.array([0.025, 0.018, 0.03], np.float32)
    col = col * (1 - mm[..., None]) + (EMPH if emph else WHITE) * mm[..., None]
    if emph:
        g = cv2.GaussianBlur(mm, (0, 0), size * 0.18) * 0.55
        col = col + EMPH * g[..., None] * (1 - st_[..., None]) * 1.2; a = np.maximum(a, g)
    spr = np.dstack([col, a]).astype(np.float32); _LS[key] = spr; return spr

def fit_line(text, size, maxw=940, track=2):
    for _ in range(6):
        lets, wd = hero_letters(text, size, track)
        if wd <= maxw: return lets, wd, size
        size = int(size * maxw / wd) - 1
    return lets, wd, size

def caption_letters(tx, sizes, ys):
    """[(letter sprite, x, y, word time, word, line, index)] for a two-line caption, laid out per letter."""
    words = tx["words"]; out_ = []
    for ln in (0, 1):
        ws = [(w, wt) for w, wt, l in words if l == ln]
        if not ws: continue
        lets, wd, sz = fit_line(" ".join(w for w, _ in ws), sizes[ln])
        bounds = []; acc = 0
        for w, wt in ws: bounds.append((acc, acc + len(w), wt, w)); acc += len(w)
        for i, (c, lm, xoff) in enumerate(lets):
            b = [b_ for b_ in bounds if b_[0] <= i < b_[1]][0]
            out_.append((letter_sprite(lm, sz, b[3] in tx.get("emph", [])), W / 2 + xoff, ys[ln], b[2], b[3], ln, i - b[0], sz))
    return out_

def text_carry3(out, f, tx):
    """IT'S GONNA / CARRY OFF: built word by word (fade, rise, blur to sharp); then the whirlwind lifts the letters off
    in reading order and spirals them away up and to the right, each with a short gold trail."""
    t = f / FPS; words = tx["words"]
    if t < words[0][1] - 0.02 or t > tx["end"] + 0.02: return out
    L = caption_letters(tx, (96, 140), (1368, 1500)); ex0 = tx["end"] - 0.55
    out = out * cap_scrim(1250, 1620, 0.32 * (1 - smooth((t - ex0 - 0.30) / 0.25)) * smooth((t - words[0][1] + 0.05) / 0.25))
    lay = np.zeros((H, W, 4), np.float32); vx0, vy0 = W * 0.70, 1180
    for n_, (spr, x0, y0, wt, w, ln, ci, sz) in enumerate(L):
        v = eout(clamp((t - wt - 0.012 * ci) / 0.18, 0, 1), 2.4)
        if v <= 0: continue
        w_ = clamp((t - (ex0 + 0.014 * n_)) / 0.30, 0, 1)
        if w_ <= 0:
            draw_sprite(lay, spr, x0, y0 + 28 * (1 - v), 1.0, 0.0, 1.0, (0.1 + 5 * (1 - v)) if v < 1 else 0.0, v); continue
        vx, vy = vx0 + 260 * w_, vy0 - 420 * w_
        ang0 = math.atan2(y0 - vy, x0 - vx); r0 = math.hypot(x0 - vx, y0 - vy)
        for g_, (dt, al) in enumerate(((0.0, 1.0), (0.05, 0.35), (0.10, 0.18))):          # the letter and its trail
            ww = max(0.0, w_ - dt)
            ang = ang0 - 5.2 * ein(ww, 1.7); r = r0 * (1 - 0.82 * ein(ww, 1.4))
            x, y = vx + math.cos(ang) * r, vy + math.sin(ang) * r
            a = (1 - smooth((ww - 0.55) / 0.45)) * al
            if a <= 0.01: continue
            sp = spr if g_ == 0 else np.dstack([spr[..., :3] * 0.2 + GOLD2 * 0.8, spr[..., 3:4]])
            draw_sprite(lay, sp, x, y, 1 - 0.55 * ww, 500 * ein(ww, 1.5), 1.0, 0.3 + 7 * ww + 3 * g_, a)
    out = out * (1 - lay[..., 3:4]) + lay[..., :3]
    return np.clip(out, 0, 1)

def text_bound(out, f, tx):
    """ALL THAT / ISN'T BOUND: the gust takes every word but BOUND (which locks in place with a flash), then BOUND is
    struck and bursts into sparks, clearing the way for AND."""
    t = f / FPS; words = tx["words"]
    if t < words[0][1] - 0.02 or t > tx["end"] + 0.02: return out
    L = caption_letters(tx, (96, 140), (1418, 1550)); t_end = tx["end"]; t_b = [wt for w, wt, _ in words if w == "BOUND"][0]
    out = out * cap_scrim(1300, 1670, 0.32 * (1 - smooth((t - t_end + 0.10) / 0.10)) * smooth((t - words[0][1] + 0.05) / 0.25))
    lay = np.zeros((H, W, 4), np.float32); gust0 = t_b + 0.10; cv = bolt_canvas()
    for n_, (spr, x0, y0, wt, w, ln, ci, sz) in enumerate(L):
        v = eout(clamp((t - wt - 0.012 * ci) / 0.18, 0, 1), 2.4)
        if v <= 0: continue
        if w != "BOUND":
            g = clamp((t - (gust0 + 0.012 * n_)) / 0.26, 0, 1)                          # blown off to the right
            if g > 0:
                x = x0 + 900 * ein(g, 2.0); y = y0 - 120 * ein(g, 1.5) + 30 * math.sin(n_ * 1.7) * g
                draw_sprite(lay, spr, x, y, 1 - 0.3 * g, (200 if n_ % 2 else -160) * ein(g, 1.6), 1.0, 0.3 + 9 * g, 1 - smooth((g - 0.4) / 0.6), stretch=1 + 1.2 * g)
                continue
            draw_sprite(lay, spr, x0, y0 + 28 * (1 - v), 1.0, 0.0, 1.0, (0.1 + 5 * (1 - v)) if v < 1 else 0.0, v)
        else:
            k = clamp((t - (t_end - 0.11)) / 0.11, 0, 1)                                   # struck: white-hot, bursts
            lock = math.exp(-max(0.0, t - (t_b + 0.18)) / 0.10) if t > t_b + 0.18 else 0.0
            sp = spr if k <= 0 else np.dstack([spr[..., :3] * (1 - k) + GOLDW * k, spr[..., 3:4]])
            draw_sprite(lay, sp, x0, y0 + 28 * (1 - v), (1 + 0.04 * lock) * (1 + 0.6 * k), 0.0, 1.0, (0.1 + 5 * (1 - v)) if v < 1 else 6 * k, v * (1 - k ** 1.5))
            if lock > 0.05 and ci == 2: out = add_glow(out, x0, y0, 260, 0.35 * lock, GOLD2)
            if 0 < k < 0.7 and ci in (0, 4): put_bolt(cv, (x0 + 40, y0 - 260), (x0, y0 - 40), 3000 + ci + f, 3, 0.3, 5, 0)
    out = out + light_from(cv, 1.2)
    out = out * (1 - lay[..., 3:4]) + lay[..., :3]
    return np.clip(out, 0, 1)

def text_charge(out, f, tx):
    """AND (the long held note): gold charge rises inside the letters as the build climbs, crackling at the top; WHEN
    lands bigger and white-hot. Both ride the emblem dive (drawn before the transition)."""
    t = f / FPS; words = tx["words"]
    if t < words[0][1] - 0.02 or t > tx["end"] + 0.02: return out
    (w0, t0, _), (w1, t1, _) = words[0], words[1]
    out = out * cap_scrim(1250, 1640, 0.32 * smooth((t - t0 + 0.05) / 0.25))
    lay = np.zeros((H, W, 4), np.float32); cv = bolt_canvas()
    lets, wd = hero_letters(w0, 124, 4); fill = smooth((t - t0 - 0.15) / (t1 - t0 - 0.10))
    for i, (c, lm, xoff) in enumerate(lets):
        v = eout(clamp((t - t0 - 0.03 * i) / 0.20, 0, 1), 2.4)
        if v <= 0: continue
        spr = letter_sprite(lm, 124, False).copy(); hh = spr.shape[0]
        yy = np.linspace(1, 0, hh)[:, None]; lvl = fill * 1.04
        mix = cv2.GaussianBlur((yy < lvl).astype(np.float32), (0, 0), 2)[..., None]
        face = np.pad(lm, 36)[..., None]
        line = np.exp(-((yy - lvl) / 0.02) ** 2)[..., None] * (0 < fill < 1)
        spr[..., :3] = spr[..., :3] * (1 - face * mix) + face * mix * EMPH * 1.05 + face * line * GOLDW * 0.9
        x = W / 2 + xoff
        draw_sprite(lay, spr, x, 1372 + 28 * (1 - v), 1.0, 0.0, 1.0, (0.1 + 5 * (1 - v)) if v < 1 else 0.0, v)
        if fill > 0.6 and (f // 2 + i) % 3 == 0:
            put_bolt(cv, (x - 20, 1372 - 52), (x + 30, 1372 - 52 - 40 - 50 * fill), 3100 + i + f // 2, 2, 0.35, 4, 0)
    out = out + light_from(cv, 0.7 * fill)
    if t >= t1 - 0.02:
        b = cap_word(w1, 168, True); v = clamp((t - t1) / 0.16, 0, 1); sc = 1.4 - 0.4 * eout(v, 3.0)
        bb = cv2.resize(b, (int(b.shape[1] * sc), int(b.shape[0] * sc)))
        if v < 1: bb = cv2.GaussianBlur(bb, (0, 0), 0.1 + 6 * (1 - v))
        hot = clamp(1 - (t - t1) / 0.25, 0, 1)
        bb[..., :3] = bb[..., :3] * (1 - 0.6 * hot) + GOLDW * 0.6 * hot * (bb[..., 3:4] > 0.5)
        out = paste(out, bb, int(W / 2 - bb.shape[1] / 2), int(1512 - bb.shape[0] / 2), min(1, v * 1.5))
    out = out * (1 - lay[..., 3:4]) + lay[..., :3]
    return np.clip(out, 0, 1)

def text_run3(out, f, tx):
    """ALL THIS / RUNNING AROUND: each word runs in from the right with a gold afterimage and settles (on its sung
    onset); then the letters of AROUND leap onto the ring and run round it as it opens into the Speed Force; the other
    words are pulled into the portal."""
    t = f / FPS; words = tx["words"]
    if t < words[0][1] - 0.02 or t > tx["end"] + 0.02: return out
    L = caption_letters(tx, (96, 132), (1360, 1486))
    t_suck, t_jump = T_OPEN + 0.08, T_OPEN + 0.08
    out = out * cap_scrim(1240, 1600, 0.34 * (1 - smooth((t - t_suck) / 0.12)) * smooth((t - words[0][1] + 0.05) / 0.25))
    lay = np.zeros((H, W, 4), np.float32)
    ar = [q for q in L if q[4] == "AROUND"]; nA = len(ar)
    for (spr, x0, y0, wt, w, ln, ci, sz) in L:
        v = clamp((t - wt - 0.010 * ci) / 0.20, 0, 1)
        if v <= 0: continue
        off = (1 - eout(v, 3.0)) * 700; x, y = x0 + off, y0
        if w == "AROUND" and t > t_jump:
            g = clamp((t - t_jump) / 0.13, 0, 1); ge = smooth(g)
            R = max(330.0, portal_R(t)); om = (t - t_jump) * 11.0
            a_ = math.pi / 2 - (ci - (nA - 1) / 2) * 0.40 - om                              # from the bottom of the ring
            rx, ry = W / 2 + R * math.cos(a_), H / 2 + R * 1.35 * math.sin(a_)
            x, y = x + (rx - x) * ge, y + (ry - y) * ge
            fade = 1 - smooth((t - (T_OPEN + 0.34)) / 0.12)
            for g_, dt in enumerate((0.0, 0.025, 0.05)):
                a2 = a_ + dt * 11.0 * ge
                xx = x if g_ == 0 else x0 + (W / 2 + R * math.cos(a2) - x0) * ge
                yy = y if g_ == 0 else y0 + (H / 2 + R * 1.35 * math.sin(a2) - y0) * ge
                sp = spr if g_ == 0 else np.dstack([spr[..., :3] * 0.2 + GOLD2 * 0.8, spr[..., 3:4]])
                draw_sprite(lay, sp, xx, yy, 1.0 - 0.15 * ge, math.degrees(a_ - math.pi / 2) * ge, 1.0, 0.2 + 2.5 * ge * g_ + 1.0 * ge, fade * (1.0, 0.4, 0.2)[g_])
            continue
        if t > t_suck:                                                                    # pulled into the portal
            s_ = clamp((t - t_suck) / 0.16, 0, 1)
            x, y = x + (W / 2 - x) * ein(s_, 1.8), y + (H / 2 - y) * ein(s_, 1.8)
            draw_sprite(lay, spr, x, y, 1 - 0.8 * s_, 0.0, 1.0, 0.3 + 8 * s_, 1 - s_); continue
        if v < 1:
            tr = np.dstack([spr[..., :3] * 0.2 + GOLD2 * 0.8, spr[..., 3:4]])
            draw_sprite(lay, tr, x + 90 * (1 - v), y, 1.0, 0.0, 1.0, 2 + 8 * (1 - v), 0.35 * (1 - v), stretch=1 + 2.0 * (1 - v))
        draw_sprite(lay, spr, x, y, 1.0, 0.0, 1.0, (0.1 + 5 * (1 - v)) if v < 1 else 0.0, min(1, v * 1.6))
    out = out * (1 - lay[..., 3:4]) + lay[..., :3]
    return np.clip(out, 0, 1)

def text10(out, f, s, rides):
    for tx in E.TEXT:
        if bool(tx.get("rides")) != rides: continue
        st_ = tx["style"]
        if st_ == "carry": out = text_carry3(out, f, tx)
        elif st_ == "bound": out = text_bound(out, f, tx)
        elif st_ == "charge": out = text_charge(out, f, tx)
        elif st_ == "slam": out = text_slam(out, f, tx)
        elif st_ == "echo": out = text_echo(out, f, tx)
        elif st_ == "hero": out = text_hero10(out, f, tx)
        elif st_ == "speed": out = text_run3(out, f, tx)
    return out

# ---- the frame (rev 3) ----------------------------------------------------------------------------------------
def base10(s, f):
    person = None
    if s.get("seg"): img, person = render_shot(s, f, want_mask=True)
    else: img = render_shot(s, f)
    k_usm = 0.16 if SR_USED[0] else 0.40                                                  # the restored source needs little
    img = np.clip(img + k_usm * (img - cv2.GaussianBlur(img, (0, 0), 1.5)), 0, 1)
    if s.get("frozen"):
        fz = is_frozen(s, f)
        if fz > 0: img = frozen_world(img, person, f, s, fz)
        else: img = np.clip(hblur(img, 30) * 0.5 + img * 0.5 + 0.06 * GOLD2, 0, 1)
    if s.get("trails"): img = afterimages(img, s, f, person, s["trails"])
    if s.get("arcs"): img = edge_arcs(img, f, person, s["arcs"])
    if s.get("wind"): img = wind_layer(img, s, f, person, s["wind"])
    if s.get("sparks"): img = spark_motes(img, f, person, s["sparks"])
    if s.get("orbit"): img = orbit_ribbons(img, s, f, person, s["orbit"])
    return img, person

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    if s.get("graphic") == "tunnel": out = tunnel_frame(f); person = None
    else: out, person = base10(s, f)
    out = text10(out, f, s, True)                                                      # type that rides the transitions
    if s.get("streak_e") is not None: out = light_streak3(out, f, s)
    if tin == "tunnel_in": out = tunnel_in(out, f, k)
    elif tin in TR2 and k < TR2[tin][2] and P is not None: out = TR2[tin][0](edge10(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge10(n_, "first"), kn, f, s, n_)
    out = portal(out, f)
    if s.get("wave"): out = drop_wave(out, f, s)
    out = edge_bolts(out, f)
    out = bar_sweep(out, f)
    out = hit_ripple(out, f)
    out = accents10(out, f)
    out = text10(out, f, s, False)
    out = finish10(out, f)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)



# ============================================================================ v10 rev 4
# Owner notes: replace the glass shatter in the frozen bullet scene with something unconventional and well thought;
# a new animation for IT'S GONNA / CARRY OFF; one brand-new animation somewhere in the edit.
#   TIME PARTICLES (replaces frozen_shatter): the frozen world comes apart into its own pixels from the edges in (he is
#       the last thing to go), the particles hang in the stopped air like the bullets do, then swirl back together as the
#       next frozen moment, rebuilding outward from his reaching hand and landing on the beat that restarts time.
#       Every particle is a pixel of the real footage (nothing drawn), and the rebuild order keeps faces whole longest.
#   CARRY OFF: a lightning runner streaks along each line and drops each word off in its wake on its sung onset; on
#       "carry off" the runner comes back and snatches the letters away with it.
#   BULLET TIME (new animation): in every frozen hold the camera glides through the frozen moment in 3-D: the people
#       move against the room with real parallax (depth from the MODNet matte and the floor), plus a slow dolly push.

# ---- TIME PARTICLES --------------------------------------------------------------------------------------------
PG = 6
_PT = {}
def part_grid():
    if "g" in _PT: return _PT["g"]
    ys, xs = np.mgrid[PG // 2:H:PG, PG // 2:W:PG]
    xs = xs.ravel().astype(np.float32); ys = ys.ravel().astype(np.float32); n = len(xs); rng = np.random.default_rng(77)
    ed = np.minimum(np.minimum(xs, W - xs) / (W / 2), np.minimum(ys, H - ys) / (H / 2))          # 0 at the frame edge
    _PT["g"] = dict(x=xs, y=ys, xi=xs.astype(np.int32), yi=ys.astype(np.int32), n=n, gw=W // PG, gh=H // PG,
                    z=rng.uniform(0.5, 1.6, n).astype(np.float32), ph=rng.uniform(0, 6.283, n).astype(np.float32),
                    jit=rng.random(n).astype(np.float32), ed=np.clip(ed, 0, 1).astype(np.float32),
                    V=(30 + 150 * rng.random(n) ** 1.5).astype(np.float32))
    return _PT["g"]

def part_plan(sa, sb):
    key = ("plan", sa["n"], sb["n"])
    if key in _PT: return _PT[key]
    G = part_grid(); x0, y0 = G["x"], G["y"]
    _, pa = base10(sa, sa["f1"] - 1)
    pam = pa[G["yi"], G["xi"]] if pa is not None else np.zeros(G["n"], np.float32)
    fx, fy = sb.get("pfocus", (W / 2, H * 0.6))
    rb = np.hypot(x0 - fx, y0 - fy); rb = rb / rb.max()
    td = -12 + 12 * G["ed"] ** 0.7 + 2.5 * G["jit"] + 5 * (pam > 0.5)                       # edges first, people last
    tr = 10.5 + 9.0 * rb ** 0.85 + 1.2 * G["jit"]                                            # the rebuild starts at his hand
    rx, ry = x0 - W / 2, y0 - H * 0.52; rr = np.hypot(rx, ry) + 1
    _PT[key] = dict(td=td.astype(np.float32), tr=tr.astype(np.float32), ux=(rx / rr).astype(np.float32), uy=(ry / rr).astype(np.float32),
                    rr=rr.astype(np.float32))
    return _PT[key]

def part_drift(G, P, k):
    """k frames after detaching: a burst outward that the frozen air slows to a hang, turning slowly round the frame
    centre, rising a little; near (large z) fragments travel further."""
    k = np.maximum(k, 0)
    dr = G["V"] * G["z"] * (1 - np.exp(-k / 6.0)) + 0.6 * k * G["z"]
    a = dr / (P["rr"] + 260) * 0.9                                                             # the slow vortex
    ca, sa_ = np.cos(a), np.sin(a)
    ox, oy = P["ux"] * (P["rr"] + dr), P["uy"] * (P["rr"] + dr)
    nx, ny = ox * ca - oy * sa_, ox * sa_ + oy * ca
    return nx - P["ux"] * P["rr"], ny - P["uy"] * P["rr"] - 0.8 * k * G["z"] + 4 * np.sin(G["ph"] + 0.15 * k) * (k > 0)

_VOID = {}
def part_void(f):
    if "v" not in _VOID:
        r = np.sqrt(((_GX - W / 2) / W) ** 2 + ((_GY - H * 0.55) / H) ** 2)
        _VOID["v"] = (SLATE * 0.40 + np.exp(-(r / 0.35) ** 2)[..., None] * (GOLD2 * 0.10 + STEEL * 0.06)).astype(np.float32)
    return _VOID["v"]

def part_pos(G, P, jj):
    td, tr = P["td"], P["tr"]
    q = np.clip((jj - tr) / 8.0, 0, 1); e = 1 - (1 - q) ** 2.4
    dx, dy = part_drift(G, P, jj - td)
    ret = q > 0
    if ret.any():
        rdx, rdy = part_drift(G, P, tr - td)
        th_ = 2.0 * (1 - e); c_, s_ = np.cos(th_), np.sin(th_)
        dx = np.where(ret, (rdx * c_ - rdy * s_) * (1 - e), dx); dy = np.where(ret, (rdx * s_ + rdy * c_) * (1 - e), dy)
    return G["x"] + dx, G["y"] + dy, q

def time_particles(A, B, j, f, sa, sb, pre=12, post=31):
    """TIME PARTICLES: the frozen moment breaks into fragments of its own pixels that burst apart and hang in the
    stopped air, then swirl back together as the next frozen moment (from his hand outward), landing on the beat
    that restarts time."""
    G = part_grid(); P = part_plan(sa, sb); jj = float(j)
    td, tr = P["td"], P["tr"]; tl = tr + 8.0
    att = jj < td; lan = jj >= tl; free = ~att & ~lan
    gw, gh = G["gw"], G["gh"]
    up = lambda m: cv2.resize(m.reshape(gh, gw).astype(np.float32), (W, H), interpolation=cv2.INTER_NEAREST)[..., None]
    attF, lanF = up(att), up(lan)
    out = A * attF + B * lanF + part_void(f) * (1 - attF - lanF)
    idx_f = np.nonzero(free)[0]
    if len(idx_f):
        px, py, q = part_pos(G, P, jj); px2, py2, _ = part_pos(G, P, jj - 0.5)
        xi, yi = G["xi"][idx_f], G["yi"][idx_f]; qf = q[idx_f]
        w = np.clip((qf - 0.15) / 0.6, 0, 1)[:, None]; w = w * w * (3 - 2 * w)
        col = A[yi, xi] * (1 - w) + B[yi, xi] * w
        tw = (np.sin(G["ph"][idx_f] * 7 + jj * 0.9) > 0.94) * (1 - qf) * 0.6                   # a few catch the light as they hang
        gl = (np.sin(np.pi * qf) * 0.35 + tw)[:, None]
        col = col + gl * (GOLD2 * 0.55 + GOLDW * 0.2)
        X = px[idx_f] / PG; Y = py[idx_f] / PG; X2 = px2[idx_f] / PG; Y2 = py2[idx_f] / PG
        fast = np.hypot(X - X2, Y - Y2) > 0.7
        big = G["z"][idx_f] > 1.3
        xs_ = [X, (X + X2)[fast] / 2, X2[fast], X[big] + 1, X[big], X[big] + 1]
        ys_ = [Y, (Y + Y2)[fast] / 2, Y2[fast], Y[big], Y[big] + 1, Y[big] + 1]
        cs_ = [col, col[fast] * 0.8, col[fast] * 0.6, col[big], col[big], col[big]]
        ix = np.concatenate(xs_).astype(np.int32); iy = np.concatenate(ys_).astype(np.int32); cc = np.concatenate(cs_)
        ok = (ix >= 0) & (ix < gw) & (iy >= 0) & (iy < gh)
        lin = iy[ok] * gw + ix[ok]; cc = cc[ok]
        cnt = np.bincount(lin, minlength=gw * gh).astype(np.float32)
        can = np.stack([np.bincount(lin, weights=cc[:, ch], minlength=gw * gh) for ch in range(3)], 1).astype(np.float32)
        can = can / np.maximum(cnt, 1)[:, None]
        cmask = (cnt > 0).reshape(gh, gw).astype(np.float32)
        cm = cv2.resize(cmask, (W, H), interpolation=cv2.INTER_NEAREST)[..., None]
        cu = cv2.resize(can.reshape(gh, gw, 3), (W, H), interpolation=cv2.INTER_NEAREST)
        cu = cu * (0.80 + 0.20 * cv2.resize(cv2.GaussianBlur(cmask, (0, 0), 0.6), (W, H))[..., None])        # a soft edge to each fragment
        out = out * (1 - cm) + cu * cm
        sp = cv2.resize(cmask * float(np.clip(0.55 - abs(jj - 8) / 30, 0.15, 0.55)), (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        out = out + cv2.resize(cv2.GaussianBlur(sp, (0, 0), 3), (W, H))[..., None] * GOLD2 * 0.30
    if jj >= post - 5: a = smooth((jj - (post - 5)) / 4); out = out * (1 - a) + B * a
    return np.clip(out, 0, 1)

TR2["time_particles"] = (time_particles, 12, 31)

# ---- BULLET TIME: the camera glides through each frozen hold in 3-D ---------------------------------------------
def holds_of(s):
    ks = s["tmap"]; return [(u0, u1) for (u0, t0), (u1, t1) in zip(ks, ks[1:]) if abs(t1 - t0) < 1e-6 and u1 > u0]

def bullet_cam(s, f):
    """the camera's lateral offset (-0.5..0.5 of the swing) and dolly push, accumulated over the shot's frozen holds."""
    hs = holds_of(s)
    if not hs: return 0.0, 0.0
    u = (f - s["f0"]) / max(1, s["f1"] - s["f0"]); acc = 0.0; push = 0.0
    for (u0, u1) in hs:
        v = smooth((u - u0) / (u1 - u0)); acc += v / len(hs); push += 0.03 * math.sin(math.pi * clamp((u - u0) / (u1 - u0), 0, 1))
    return acc - 0.5, push

_DP = {}
def bullet_time(img, person, s, f):
    if not (s.get("frozen") and holds_of(s)): return img
    off, push = bullet_cam(s, f); d = 1 if SHOTS.index(s) % 2 == 0 else -1
    cam = d * 220 * off
    if "floor" not in _DP: _DP["floor"] = (0.30 + 0.32 * (_GY / H) ** 1.4).astype(np.float32)
    dep = _DP["floor"] if person is None else _DP["floor"] + 0.55 * cv2.GaussianBlur(person, (0, 0), 16)
    zs = 1.07 + push * dep                                                                     # a margin, and the dolly
    mx = W / 2 + (_GX - W / 2) / zs - cam * (dep - 0.6)
    my = H * 0.55 + (_GY - H * 0.55) / zs
    return cv2.remap(img, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

_base10_r3 = base10
def base10(s, f):
    img, person = _base10_r3(s, f)
    if s.get("frozen"): img = bullet_time(img, person, s, f)
    return img, person

# ---- CARRY OFF: the runner drops the words off, then carries them off ----------------------------------------------
def runner_streak(cv, x_h, y, x_from, length=320, width=7):
    """a horizontal lightning streak whose head is at x_h, its tail fading back toward x_from."""
    x_t = max(x_from, x_h - length)
    if x_h - x_t < 4: return
    n = 24
    for i in range(n):
        a = (i + 1) / n; xa = x_t + (x_h - x_t) * i / n; xb = x_t + (x_h - x_t) * (i + 1) / n
        cv2.line(cv, (int(xa), int(y)), (int(xb), int(y)), int(255 * a ** 1.6), max(1, int(width * a)), cv2.LINE_AA)

def text_carry4(out, f, tx):
    """IT'S GONNA / CARRY OFF: a lightning runner streaks along the line and each word is left behind in its wake on its
    sung onset (stretched, blurred, then sharp); on "carry off" the runner comes back along both lines and snatches
    the letters away to the right."""
    t = f / FPS; words = tx["words"]
    if t < words[0][1] - 0.15 or t > tx["end"] + 0.02: return out
    L = caption_letters(tx, (96, 140), (1368, 1500))
    t_ex = tx["end"] - 0.44
    out = out * cap_scrim(1250, 1620, 0.32 * (1 - smooth((t - t_ex - 0.18) / 0.22)) * smooth((t - words[0][1] + 0.10) / 0.25))
    lay = np.zeros((H, W, 4), np.float32); cv = bolt_canvas()
    spans = {}
    for (spr, x0, y0, wt, w, ln, ci, sz) in L:
        a, b = spans.get((w, wt), (1e9, -1e9)); spans[(w, wt)] = (min(a, x0 - spr.shape[1] / 2 + 36), max(b, x0 + spr.shape[1] / 2 - 36))
    heads = {}
    for (w, wt), (a, b) in spans.items():                                                    # entry runs, one per word
        dur = 0.09 + 0.012 * len(w); u = (t - (wt - 0.07)) / dur
        heads[(w, wt)] = a - 70 + (b - a + 140) * ein(clamp(u, 0, 1), 1.2) if u > 0 else -1e9
        if 0 < u < 1.5:
            ln = [q[5] for q in L if q[4] == w and q[3] == wt][0]; y = (1368, 1500)[ln]
            fade = 1 - smooth((u - 1.0) / 0.5)
            cv_ = bolt_canvas(); runner_streak(cv_, heads[(w, wt)], y, a - 200, 340, 8)
            cv = np.maximum(cv, (cv_.astype(np.float32) * fade).astype(np.uint8))
            if u < 1.0: out = add_glow(out, heads[(w, wt)], y, 46, 0.9 * fade, GOLDW)
    ex_head = []
    for ln, (y, d0) in enumerate(((1368, 0.0), (1500, 0.08))):                              # the exit runs
        u = (t - (t_ex + d0)) / 0.18
        hx = -120 + (W + 360) * ein(clamp(u, 0, 1), 1.3) if u > 0 else -1e9; ex_head.append(hx)
        if 0 < u < 1.3:
            runner_streak(cv, hx, y, -200, 420, 9)
            if u < 1.0: out = add_glow(out, hx, y, 52, 0.9, GOLDW)
    for (spr, x0, y0, wt, w, ln, ci, sz) in L:
        hx = heads[(w, wt)]
        v = clamp((hx - x0) / 140.0, 0, 1)
        if v <= 0: continue
        ve = eout(v, 2.2)
        g = clamp((ex_head[ln] - x0) / 220.0, 0, 1)                                           # snatched by the runner
        if g > 0:
            ge = ein(g, 1.8)
            x = x0 + 1300 * ge; st_ = 1 + 3.2 * math.sin(math.pi * min(1.0, g * 1.2)) ** 0.8 + 2.0 * ge
            tr = np.dstack([spr[..., :3] * 0.2 + GOLD2 * 0.8, spr[..., 3:4]])
            draw_sprite(lay, tr, x - 70 * st_, y0, 1.0, 0.0, 1.0, 3 + 9 * g, 0.35 * (1 - g), stretch=st_ * 1.4)
            draw_sprite(lay, spr, x, y0, 1.0, 0.0, 1.0, 0.5 + 9 * g, 1 - smooth((g - 0.35) / 0.65), stretch=st_)
            continue
        draw_sprite(lay, spr, x0 + 34 * (1 - ve), y0, 1.0, 0.0, 1.0, (0.2 + 6 * (1 - ve)) if v < 1 else 0.0, min(1, v * 1.8), stretch=1 + 1.8 * (1 - ve))
    out = out + light_from(cv, 1.1)
    out = out * (1 - lay[..., 3:4]) + lay[..., :3]
    return np.clip(out, 0, 1)

_text10_r3 = text10
def text10(out, f, s, rides):
    if rides: return _text10_r3(out, f, s, rides)
    for tx in E.TEXT:
        if tx.get("rides"): continue
        st_ = tx["style"]
        if st_ == "carry": out = text_carry4(out, f, tx)
        elif st_ == "bound": out = text_bound(out, f, tx)
        elif st_ == "slam": out = text_slam(out, f, tx)
        elif st_ == "echo": out = text_echo(out, f, tx)
        elif st_ == "hero": out = text_hero10(out, f, tx)
        elif st_ == "speed": out = text_run3(out, f, tx)
    return out



# ============================================================================ v10 rev 5 — the motion pass
# Owner notes: "lacklustre… could use more animations and overall professionalism."
#   VELOCITY   every hook shot is time-remapped to the beat: a speed burst on each beat (with real shutter blur from
#              the source frames), smooth slow motion between (optical-flow in-betweens on the restored 2x source,
#              so 24p footage plays at a true 60 fps instead of stepping)
#   CAMERA     the camera moves with the music: a zoom punch and an alternating rotation kick on every beat of the
#              hook, zoom motion blur and a colour split on the hit frames (the type stays clean on top)
#   LIGHT      volumetric light rays pour out of the lightning (screen-space god rays from the brightest source)

# ---- velocity: optical-flow in-betweens on the restored bands ---------------------------------------------------
_FL = {}
_DIS5 = [None]
def flow_pair(pk, i0, i1):
    key = (pk, i0, i1)
    if key not in _FL:
        if len(_FL) > 8: _FL.pop(next(iter(_FL)))
        if _DIS5[0] is None: _DIS5[0] = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
        g0 = cv2.cvtColor(FR[(pk, i0)], cv2.COLOR_BGR2GRAY); g1 = cv2.cvtColor(FR[(pk, i1)], cv2.COLOR_BGR2GRAY)
        _FL[key] = (_DIS5[0].calc(g0, g1, None), _DIS5[0].calc(g1, g0, None))
    return _FL[key]

_GRD = {}
def sr_flow_part(pk, i0, i1, a, x0, x1, y0, y1):
    """the in-between frame at fraction a, built on the 2x bands with the low-res flow scaled up."""
    b0, b1 = sr_band(pk, i0), sr_band(pk, i1)
    for b in (b0, b1):
        if b is None or b[0] > x0 or b[0] + b[1].shape[1] // 2 < x1: return None
    F01, F10 = flow_pair(pk, i0, i1)
    f01, f10 = F01[y0:y1, x0:x1], F10[y0:y1, x0:x1]
    Ft0 = -(1 - a) * a * f01 + a * a * f10; Ft1 = (1 - a) * (1 - a) * f01 - a * (1 - a) * f10
    h2, w2 = 2 * (y1 - y0), 2 * (x1 - x0)
    if (w2, h2) not in _GRD:
        if len(_GRD) > 6: _GRD.clear()
        gx, gy = np.meshgrid(np.arange(w2, dtype=np.float32), np.arange(h2, dtype=np.float32)); _GRD[(w2, h2)] = (gx, gy)
    gx, gy = _GRD[(w2, h2)]; parts = []
    for (xo, im), Ft in ((b0, Ft0), (b1, Ft1)):
        F2 = cv2.resize(Ft, (w2, h2), interpolation=cv2.INTER_LINEAR) * 2
        parts.append(cv2.remap(im, gx + 2 * (x0 - xo) + F2[..., 0], gy + 2 * y0 + F2[..., 1], cv2.INTER_LINEAR,
                               borderMode=cv2.BORDER_REFLECT).astype(np.float32))
    return parts[0] * (1 - a) + parts[1] * a

def src_weights(s, f):
    """the source frames render_shot samples: [(frame, weight)] or [("flow", i0, i1, a)] (mirrors source_img/sample)."""
    pk = s["src"]; fps = E.SRC[pk][1]; U = UNIQ[pk]
    t, u, sp = src_time(s, f)
    def idx(tt, mode):
        kf = tt * fps; i = clamp(bisect.bisect_right(U, kf + 0.3) - 1, 0, len(U) - 1)
        if mode == "hold" or i >= len(U) - 1: return [(U[i], 1.0)]
        i0, i1 = U[i], U[i + 1]; a = clamp((kf - i0) / (i1 - i0), 0.0, 1.0)
        if a < 0.05: return [(i0, 1.0)]
        if a > 0.95: return [(i1, 1.0)]
        if mode == "blend": return [(i0, 1 - a), (i1, a)]
        A0, A1 = FR[(pk, i0)], FR[(pk, i1)]
        if np.abs(A0[::8, ::8].astype(np.float32) - A1[::8, ::8]).mean() > 14: return [(i0 if a < 0.5 else i1, 1.0)]
        m0, m1 = A0[::8, ::8].mean(axis=(0, 1)), A1[::8, ::8].mean(axis=(0, 1))
        if np.abs(m0.astype(np.float32) - m1).max() > 6: return [(i0, 1 - a), (i1, a)]
        return [("flow", i0, i1, a)]
    if sp > 1.7:
        K = int(min(7, max(3, round(sp * 2)))); span = 0.5 / FPS * sp; out_ = []
        for j in range(K):
            out_ += [(k, w / K) for k, w in idx(t + (j / (K - 1) - 0.5) * span, "hold")]
        return out_, t, u
    return idx(t, s.get("interp", "hold")), t, u

def render_shot(s, f, with_shake=True, want_mask=False):
    SR_USED[0] = False
    if s.get("fit") or "src" not in s: return _render_shot_v(s, f, with_shake, want_mask)
    ws, t, u = src_weights(s, f)
    if not ws: return _render_shot_v(s, f, with_shake, want_mask)
    sw, sh_ = E.SRC[s["src"]][2], E.SRC[s["src"]][3]
    cx, cy, ch = frame_geom(s, f, t, u)
    cw = ch * 9 / 16; sc = W / cw
    dx, dy, rot = shake(f) if with_shake else (0, 0, 0)
    m = 16
    x0 = int(max(0, cx - cw / 2 - m)); x1 = int(min(sw, cx + cw / 2 + m))
    y0 = int(max(0, cy - ch / 2 - m)); y1 = int(min(sh_, cy + ch / 2 + m))
    roi = None
    for ent in ws:
        if ent[0] == "flow":
            part = sr_flow_part(s["src"], ent[1], ent[2], ent[3], x0, x1, y0, y1); w = 1.0
            if part is None: return _render_shot_v(s, f, with_shake, want_mask)
        else:
            k, w = ent; b = sr_band(s["src"], k)
            if b is None or b[0] > x0 or b[0] + b[1].shape[1] // 2 < x1: return _render_shot_v(s, f, with_shake, want_mask)
            part = b[1][2 * y0:2 * y1, 2 * (x0 - b[0]):2 * (x1 - b[0])].astype(np.float32)
        roi = part * w if roi is None else roi + part * w
    roi = grade(roi / 255, s, f)
    th_ = math.radians(rot); co, si = math.cos(th_) / sc, math.sin(th_) / sc
    lx, ly = cx - x0, cy - y0
    M = np.float32([[co, -si, lx - co * (W / 2 + dx) + si * (H / 2 + dy)], [si, co, ly - si * (W / 2 + dx) - co * (H / 2 + dy)]])
    M2 = M * 2; M2[0, 2] += 0.5; M2[1, 2] += 0.5
    out = cv2.warpAffine(roi, M2, (W, H), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)
    SR_USED[0] = True
    if want_mask:
        msk = seg_mask(s, t)
        mr = cv2.resize(msk, (sw, sh_), interpolation=cv2.INTER_LINEAR)[y0:y1, x0:x1]
        mw = cv2.warpAffine(mr, M, (W, H), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
        return np.clip(out, 0, 1), np.clip(mw, 0, 1)
    return np.clip(out, 0, 1)

# ---- the camera moves with the music ----------------------------------------------------------------------------
def beat_phase(f):
    """(seconds since the last beat, beat index) and whether this is the hook / run (where the camera punches)."""
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    hook = E.HDROP + 1 <= e < E.E_STUT or E.E_RUN <= e < E.E_REW - 1
    return ph, bi, hook

def beat_bounce(f):
    """zoom punches: soft on every beat of the cold open, a hard punch on every beat of the hook and the run."""
    ph, bi, hook = beat_phase(f); e = f / FPS / E.HB
    if hook: return 1 + 0.060 * math.exp(-ph / 0.10)
    if 0 <= e < E.HDROP: return 1 + 0.010 * math.exp(-ph / 0.08)
    return 1.0

_shake_r4 = shake
def shake(f):
    dx, dy, rot = _shake_r4(f)
    ph, bi, hook = beat_phase(f)
    if hook: rot += (1.1 if bi % 2 else -1.1) * math.exp(-ph / 0.13)                       # a rotation kick per beat
    return dx, dy, rot

def beat_fx(out, f):
    """the hit frames: zoom motion blur and a colour split on the first frames after each beat of the hook."""
    ph, bi, hook = beat_phase(f)
    if not hook or ph > 0.06: return out
    k = math.exp(-ph / 0.025)
    o = radial_blur(out, W / 2, H * 0.46, 1.0, 1.0 + 0.045 * k, 4)
    return np.clip(rgb_split(o, 9 * k), 0, 1)

# ---- light rays from the lightning ------------------------------------------------------------------------------
def light_rays(out, f, amt):
    """screen-space god rays: the brightest warm light streams outward in shafts (quarter res, 20 samples)."""
    if amt <= 0.01: return out
    w4, h4 = W // 4, H // 4
    sm = cv2.resize(out, (w4, h4), interpolation=cv2.INTER_AREA)
    L = sm[..., 0] * 0.114 + sm[..., 1] * 0.587 + sm[..., 2] * 0.299
    m = np.clip((L - 0.60) * 3.0, 0, 1) * np.clip(0.4 + (sm[..., 2] - sm[..., 0]) * 2.0, 0, 1)
    tot = float(m.sum())
    if tot < 15: return out
    gy, gx = np.mgrid[0:h4, 0:w4].astype(np.float32)
    cx, cy = float((m * gx).sum() / tot), float((m * gy).sum() / tot)
    acc = np.zeros_like(m); wsum = 0.0
    for i in range(20):
        s_ = 1.0 + 0.045 * i; d = 0.90 ** i
        M = cv2.getRotationMatrix2D((cx, cy), 0, s_)
        acc += cv2.warpAffine(m, M, (w4, h4), flags=cv2.INTER_LINEAR, borderValue=0) * d; wsum += d
    acc = cv2.GaussianBlur(acc / wsum, (0, 0), 1.5)
    rays = cv2.resize(acc, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
    fl = 0.85 + 0.15 * math.sin(f * 0.9)
    cover = tot / (w4 * h4)                                                                 # already bright frames get less
    amt = amt * float(np.clip(1.25 - cover * 5.0, 0.25, 1.0))
    return np.clip(out + rays * (GOLD2 * 0.75 + GOLDW * 0.25) * amt * 0.9 * fl, 0, 1)

_base10_r4 = base10
def base10(s, f):
    img, person = _base10_r4(s, f)
    if s.get("rays"): img = light_rays(img, f, s["rays"])
    return img, person

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    if s.get("graphic") == "tunnel": out = tunnel_frame(f); person = None
    else: out, person = base10(s, f)
    out = text10(out, f, s, True)
    if s.get("streak_e") is not None: out = light_streak3(out, f, s)
    if tin == "tunnel_in": out = tunnel_in(out, f, k)
    elif tin in TR2 and k < TR2[tin][2] and P is not None: out = TR2[tin][0](edge10(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge10(n_, "first"), kn, f, s, n_)
    out = portal(out, f)
    if s.get("wave"): out = drop_wave(out, f, s)
    out = beat_fx(out, f)
    out = edge_bolts(out, f)
    out = bar_sweep(out, f)
    out = hit_ripple(out, f)
    out = accents10(out, f)
    out = text10(out, f, s, False)
    out = finish10(out, f)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)



# ============================================================================ v11 — BOP (The Flash × DaBaby): THE RIVAL
# Built on the v10 standard engine (restored-source sampler, velocity + optical flow, the beat camera, light rays,
# the v9 type construction). New here: the VOLTAGE / RIVAL grade, the red speedster's effects (red vibration, red arcs,
# red streak), the BOLT SPLIT drop (red against gold along a lightning-bolt seam), the emblem draw-on reveal, the Speed
# Force warp for the flight through fire, the whip, the dolly focus pull, the red loop, the LET'S GO and BOP titles.
REDW = np.array([0.62, 0.66, 1.00], np.float32)          # BGR hot red-white core
RED2 = np.array([0.10, 0.10, 0.95], np.float32)          # BGR rival red glow
TEALS = np.array([0.040, 0.020, -0.010], np.float32)     # BGR teal shadow push

def light_rgb(cv, a, core, glow):
    """lightning canvas (uint8) -> light layer: a sharp core + a two-radius glow, in any colour."""
    c = cv.astype(np.float32) / 255
    sm = cv2.resize(c, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    g = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 3) * 2.6 + cv2.GaussianBlur(sm, (0, 0), 11) * 3.4, (W, H), interpolation=cv2.INTER_LINEAR)
    return (np.clip(g, 0, 1.6)[..., None] * glow * 0.85 + c[..., None] * core * 1.15) * a

def is_rival(s): return s.get("look") == "rival"

# ---- grade: VOLTAGE (Barry) / RIVAL (the red speedster) -------------------------------------------------------
_LUT11 = {}
def lut11(k):
    if k not in _LUT11:
        x = np.linspace(0, 1, 1024, dtype=np.float32)
        pts = [0.012, 0.030, 0.150, 0.470, 0.805, 0.935, 0.975] if k == "voltage" else [0.010, 0.026, 0.135, 0.450, 0.790, 0.925, 0.970]
        _LUT11[k] = (x, PchipInterpolator([0, .05, .20, .50, .80, .94, 1], pts)(x).astype(np.float32))
    return _LUT11[k]

_grade_v10 = grade
def grade(img, s, f):
    lk = s.get("look")
    if lk not in ("voltage", "rival"): return _grade_v10(img, s, f)
    g, gains = corr9(s)
    x = np.clip(img * gains, 0, 1) ** g
    if s.get("ev"): x = np.clip(x * 2 ** s["ev"], 0, 1)
    lx, ly = lut11(lk); x = np.interp(x, lx, ly).astype(np.float32)
    Bc, Gc, Rc = x[..., 0], x[..., 1], x[..., 2]
    L = (Bc * 0.114 + Gc * 0.587 + Rc * 0.299)[..., None]
    red = np.clip((Rc - np.maximum(Gc, Bc) * 1.25) * 3.0, 0, 1)[..., None]
    light = np.clip((L - 0.62) * 3.0, 0, 1) * np.clip((Rc - Bc) * 3.0, 0, 1)[..., None]
    hue = (Rc - Gc) / (Rc + 1e-3)
    skin = (np.clip(1 - np.abs(hue - 0.22) / 0.22, 0, 1) * np.clip((Rc - Bc) * 6, 0, 1) * np.clip(L[..., 0] * 3, 0, 1))[..., None]
    sat = 0.84 + 0.32 * red + 0.25 * light + 0.10 * skin
    x = L + (x - L) * sat
    sh = (1 - L) ** 2.6 * (1 - 0.7 * skin) * (1 - red)
    hi = np.clip((L - 0.55) * 2.2, 0, 1) * (1 - skin * 0.6)
    if lk == "voltage":
        x = x + sh * TEALS + hi * np.array([-0.018, 0.010, 0.035], np.float32)
    else:                                                                   # the rival: red in the light, dark red shadows
        x = x + sh * np.array([0.000, -0.006, 0.022], np.float32) + hi * np.array([-0.030, -0.018, 0.045], np.float32)
        x = x * np.array([0.94, 0.95, 1.04], np.float32)
    return np.clip(x, 0, 1)

def finish11(out, f, s):
    rival = s is not None and is_rival(s)
    small = cv2.resize(out, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi_ = np.clip(small.max(2) - 0.64, 0, 1)
    b1 = cv2.GaussianBlur(hi_, (0, 0), 4); b2 = cv2.GaussianBlur(hi_, (0, 0), 16)
    out = out + cv2.resize(b1 * 0.45 + b2 * 0.55, (W, H))[..., None] * (RED2 if rival else GOLD2) * 0.48
    out = anamorphic(out, 0.18)
    out = np.maximum(out, 0.012)
    return np.clip(out * (0.80 + 0.20 * VIG) + grain(f, 0.012), 0, 1)

# ---- the red speedster's effects -------------------------------------------------------------------------------
def red_arcs(out, f, person, amt, seed0=0):
    """red lightning crawling on the rival's silhouette (born on the matte edge)."""
    if person is None or amt <= 0.01: return out
    pm = (person > 0.5).astype(np.uint8)
    if pm.sum() < 2000: return out
    edge = cv2.morphologyEx(pm[::4, ::4], cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
    ys, xs = np.nonzero(edge)
    if len(xs) < 10: return out
    rng = np.random.default_rng(f // 2 * 17 + seed0 + 5); cv = bolt_canvas(); cy_, cx_ = ys.mean() * 4, xs.mean() * 4
    for k in range(int(2 + 5 * amt)):
        i = int(rng.integers(len(xs))); x0, y0 = xs[i] * 4.0, ys[i] * 4.0
        ang = math.atan2(y0 - cy_, x0 - cx_) + rng.uniform(-1.4, 1.4); L_ = rng.uniform(70, 200) * (0.6 + 0.6 * amt)
        put_bolt(cv, (x0, y0), (x0 + math.cos(ang) * L_, y0 + math.sin(ang) * L_), f // 2 * 103 + k + seed0, 2, 0.32, 5, int(rng.random() < 0.5))
    return np.clip(out + light_rgb(cv, amt * (0.65 + 0.35 * math.sin(f * 1.9)), REDW, RED2), 0, 1)

def red_vibe(img, amt, f, seed=3):
    """the Reverse-Flash vibration: the picture shudders into red/ghost copies (his signature face blur)."""
    if amt < 0.5: return img
    o = vib(img, amt, f, seed, 3)
    tint = np.clip(o * np.array([0.80, 0.82, 1.15], np.float32), 0, 1)
    return tint * min(1.0, amt / 20) + o * (1 - min(1.0, amt / 20))

def red_phase(A, B, j, f, sa, sb, pre=10, post=12):
    """the beat: Wells' frame shudders in red (the Reverse-Flash vibration) and resolves into the red-eyed mask."""
    if j < 0:
        u = (j + pre + 1) / pre; amt = 1 + 26 * ein(u, 2.2)
        o = red_vibe(zoom_about(A, W / 2, H * 0.42, 1 + 0.08 * ein(u, 2)), amt, f, 1)
        a = clamp((j + 3) / 3, 0, 1) * 0.5
        if a > 0: o = o * (1 - a) + red_vibe(B, amt, f, 2) * a
        return np.clip(o * (1 + 0.2 * u), 0, 1)
    v = (j + 1) / post; amt = 26 * (1 - eout(v, 2.0))
    o = red_vibe(zoom_about(B, W / 2, H * 0.42, 1 + 0.10 * (1 - eout(v, 2.2))), amt, f, 2)
    return np.clip(o * (1 + 0.25 * (1 - v)), 0, 1)

def red_link(A, B, j, f, sa, sb, pre=6, post=10):
    """a red lightning arc leaps out of the mask and the cut hides in its flash (kept off both faces)."""
    pa = subject_point(sa, sa["f1"] - 1); pb = subject_point(sb, sb["f0"])
    side = 1 if pa[0] < W / 2 else -1
    if j < 0:
        u = (j + pre + 1) / pre; cv = bolt_canvas()
        tip = (pa[0] + side * 420 * ein(u, 1.3), pa[1] + 260 * u)
        put_bolt(cv, pa, tip, 3200 + f, 3, 0.22, 6, 1)
        return np.clip(A * (1 - 0.25 * u) + light_rgb(cv, 0.6 + 0.7 * u, REDW, RED2), 0, 1)
    v = (j + 1) / post; cv = bolt_canvas()
    mid = (W / 2 + side * 380, H * 0.70); bx = face_box(sb, f)
    pb = keep_off_face(pb, bx); mid = keep_off_face(mid, bx)
    put_bolt(cv, (W / 2 - side * 600, H * 0.78), mid, 3250 + f // 2, 4, 0.22, 6, 2); put_bolt(cv, mid, pb, 3260 + f // 2, 4, 0.22, 6, 1)
    fl = 1 - eout(v, 2.0)
    return np.clip(B * (0.75 + 0.25 * v) + light_rgb(cv, 1.3 * fl, REDW, RED2) + fl * 0.16 * RED2, 0, 1)

def red_slices(A, B, j, f, sa, sb, pre=6, post=9):
    """speed slices with red leading edges (the rival's lightning)."""
    o = slices(A, B, j, f, sa, sb, pre, post)
    p = (j + pre + 0.5) / (pre + post)
    return np.clip(o * np.array([0.92, 0.92, 1.0], np.float32) + 0.05 * math.sin(math.pi * p) * RED2, 0, 1)

def red_streak(A, B, j, f, sa, sb, pre=8, post=8):
    """the rival runs: a red lightning streak tears across the frame at chest height and the hero is behind it."""
    p = (j + pre + 1) / (pre + post); hx = -300 + (W + 600) * ein(p, 1.15)
    bx = face_box(sb, sb["f0"]); y = min(H * 0.90, max(H * 0.78, (bx[2] + 150) if bx else 0))      # below his chin
    m = np.clip((hx - _GX - 40) / 160, 0, 1)[..., None]                                   # B behind the head of the streak
    smear = hblur(A, 60 + 200 * math.sin(math.pi * p))
    wake = np.exp(-((_GY - y) / 300) ** 2)[..., None] * np.clip(1 - (hx - _GX) / 900, 0, 1)[..., None] * (_GX < hx)[..., None]
    o = B * m + (A * (1 - wake) + smear * wake) * (1 - m)
    cv = bolt_canvas(); x_t = max(-200, hx - 900)
    for i in range(30):
        a = (i + 1) / 30; xa = x_t + (hx - x_t) * i / 30; xb = x_t + (hx - x_t) * (i + 1) / 30
        yy = y + 18 * math.sin(i * 1.7 + f * 0.9)
        cv2.line(cv, (int(xa), int(yy)), (int(xb), int(yy)), int(255 * a ** 1.5), max(1, int(14 * a)), cv2.LINE_AA)
    put_bolt(cv, (hx - 160, y - 30), (hx + 10, y + 40), 3300 + f, 3, 0.35, 5, 1); put_bolt(cv, (hx - 220, y + 60), (hx - 20, y - 50), 3310 + f, 2, 0.35, 5, 0)
    o = o + light_rgb(cv, 1.3, REDW, RED2)
    return np.clip(add_glow(o, hx, y, 110, 0.9, REDW), 0, 1)

def dolly(A, B, j, f, sa, sb, pre=8, post=12):
    """the calm before the drop: a focus pull. A drifts out of focus as the camera eases in; B racks into focus."""
    if j < 0:
        u = (j + pre + 1) / pre
        o = cv2.GaussianBlur(zoom_about(A, W / 2, H * 0.40, 1 + 0.06 * ein(u, 2)), (0, 0), 0.1 + 14 * ein(u, 1.8))
        return np.clip(o * (1 - 0.15 * u), 0, 1)
    v = (j + 1) / post
    o = cv2.GaussianBlur(zoom_about(B, W / 2, H * 0.40, 1.06 - 0.06 * eout(v, 2.2)), (0, 0), 0.1 + 14 * (1 - eout(v, 2.0)))
    leak = np.exp(-(((_GX - W * 0.85) / 380) ** 2 + ((_GY - H * 0.25) / 700) ** 2))[..., None] * (1 - v) * 0.30
    return np.clip(o + leak * GOLD2, 0, 1)

# ---- THE DROP: the bolt split ----------------------------------------------------------------------------------
BOLT_N = np.array([(0.95, -0.06), (0.80, 0.42), (0.93, 0.42), (0.52, 1.06)], np.float32)   # the emblem's bolt, beside his face
def bolt_path(shift=0.0):
    pts = BOLT_N.copy(); pts[:, 0] = pts[:, 0] * W + shift; pts[:, 1] *= H
    out_ = []
    for a, b in zip(pts, pts[1:]):
        n = int(np.hypot(*(b - a)) / 10) + 1
        for i in range(n): out_.append(a + (b - a) * i / n)
    out_.append(pts[-1]); return np.array(out_, np.float32)

_BS = {}
def bolt_side(shift):
    """mask (1 = right of the bolt seam), soft, for a horizontal shift of the seam."""
    key = int(shift) // 4 * 4
    if key not in _BS:
        if len(_BS) > 24: _BS.clear()
        pp = bolt_path(key); poly = np.vstack([pp, [[W + 2000, H + 50], [W + 2000, -50]]]).astype(np.int32)
        m = np.zeros((H, W), np.uint8); cv2.fillPoly(m, [poly], 255, cv2.LINE_AA)
        _BS[key] = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 2.0)
    return _BS[key]

def bolt_split(A, B, j, f, sa, sb, pre=22, post=16):
    """BOLT SPLIT (the drop): a lightning-bolt seam cracks down the frame on "Let's go"; the left side goes the rival's
    red, the right side Barry's gold; on the drop the gold side breaks through, the seam sweeps across like the emblem's
    bolt and the drop shot is behind it, a shockwave ringing out."""
    pp = bolt_path(0)
    if j < 0:
        u = (j + pre + 1) / pre; n = max(2, int(len(pp) * ein(min(1, u * 1.4), 1.2)))
        cv = bolt_canvas(); cv2.polylines(cv, [pp[:n].astype(np.int32)], False, 255, int(3 + 5 * u), cv2.LINE_AA)
        rng = np.random.default_rng(f)
        for q in range(int(3 + 6 * u)):
            i = int(rng.integers(0, n)); x0, y0 = pp[i]
            put_bolt(cv, (x0, y0), (x0 + rng.uniform(-160, 160), y0 + rng.uniform(-120, 120)), 3400 + f * 7 + q, 2, 0.35, 5, 0)
        side = bolt_side(0)[..., None]
        red_ = A * np.array([0.72, 0.74, 1.10], np.float32); gold = A * np.array([0.80, 1.00, 1.15], np.float32)
        k = smooth(u / 0.6) * 0.75
        o = A * (1 - k) + (red_ * (1 - side) + gold * side) * k
        o = o + light_rgb(cv, 0.8 + 0.8 * u, GOLDW, GOLD2) * side + light_rgb(cv, 0.6 + 0.6 * u, REDW, RED2) * (1 - side)
        if u > 0.85: o = o + (u - 0.85) / 0.15 * 0.25                                    # the breath before the hit
        return np.clip(o, 0, 1)
    v = (j + 1) / post
    shift = -(W * 1.25) * eout(v, 1.6)                                                    # the seam sweeps left across the frame
    side = bolt_side(shift)[..., None]
    Bz = zoom_about(B, W / 2, H * 0.46, 1.0 + 0.16 * (1 - eout(v, 2.4)))
    Az = A * np.array([0.72, 0.74, 1.10], np.float32)
    o = Bz * side + Az * (1 - side)
    cv = bolt_canvas(); cv2.polylines(cv, [bolt_path(shift).astype(np.int32)], False, 255, 7, cv2.LINE_AA)
    o = o + light_rgb(cv, 1.6 * (1 - v) + 0.3, GOLDW, GOLD2)
    if j < 3: o = o + (1 - j / 3) * 0.30 * (GOLDW * 0.6 + 0.4)                            # the impact frame (brief, not a white-out)
    return np.clip(o, 0, 1)

# ---- the gold moves ---------------------------------------------------------------------------------------------
def whip(A, B, j, f, sa, sb, pre=6, post=8):
    """a whip pan: the frame flies out left in a smear of motion blur with a gold streak, the next shot lands from the right."""
    if j < 0:
        u = ein((j + pre + 1) / pre, 2.2); o = cv2.warpAffine(A, np.float32([[1, 0, -W * 0.55 * u], [0, 1, 0]]), (W, H), borderMode=cv2.BORDER_REFLECT)
        o = hblur(o, 4 + 260 * u)
    else:
        v = 1 - eout((j + 1) / post, 2.6); o = cv2.warpAffine(B, np.float32([[1, 0, W * 0.55 * v], [0, 1, 0]]), (W, H), borderMode=cv2.BORDER_REFLECT)
        o = hblur(o, 4 + 260 * v)
    a = math.exp(-((j + 0.5) / 4.0) ** 2)
    streak = np.exp(-((_GY - H * 0.55) / 10) ** 2) * 0.9 + np.exp(-((_GY - H * 0.55) / 90) ** 2) * 0.3
    return np.clip(o + streak[..., None] * GOLDW * a, 0, 1)

def speedforce_in(A, B, j, f, sa, sb, pre=10, post=14):
    """into the Speed Force: the frame is pulled into a radial tunnel of light and the next shot rushes out of it."""
    if j < 0:
        u = (j + pre + 1) / pre
        o = radial_blur(zoom_about(A, W / 2, H * 0.45, 1 + 0.35 * ein(u, 2.2)), W / 2, H * 0.45, 1.0, 1.0 + 0.18 * u, 5)
    else:
        v = (j + 1) / post
        o = radial_blur(zoom_about(B, W / 2, H * 0.45, 1 + 0.30 * (1 - eout(v, 2.4))), W / 2, H * 0.45, 1.0, 1.0 + 0.16 * (1 - v), 5)
    a = math.exp(-((j + 0.5) / 6.0) ** 2)
    return np.clip(speed_warp(o, f, 1.4 * a, (W / 2, H * 0.45)) + a * 0.18 * GOLDW, 0, 1)

_SW = {}
def speed_warp(out, f, amt, c=None):
    """the Speed Force: radial streaks of light rush past from the vanishing point, embers in depth."""
    if amt <= 0.01: return out
    cx, cy = c if c is not None else (W / 2, H * 0.45)
    if "p" not in _SW:
        rng = np.random.default_rng(71)
        _SW["p"] = [(rng.uniform(0, 2 * math.pi), rng.uniform(0, 1), rng.uniform(0.3, 1.0), rng.random()) for _ in range(140)]
    t = f / FPS; cv = np.zeros((H, W), np.float32)
    for (a, r0, z, kind) in _SW["p"]:
        r = ((r0 + t * (0.9 + 1.6 * z)) % 1.0) ** 1.8 * 1500 + 60
        L_ = 40 + 300 * z * (r / 1500)
        x0, y0 = cx + math.cos(a) * r, cy + math.sin(a) * r * 1.2; x1, y1 = cx + math.cos(a) * (r + L_), cy + math.sin(a) * (r + L_) * 1.2
        cv2.line(cv, (int(x0), int(y0)), (int(x1), int(y1)), (0.35 + 0.65 * z) * (0.6 if kind < 0.7 else 1.0), 1 + int(2 * z), cv2.LINE_AA)
    cv = cv2.GaussianBlur(cv, (0, 0), 1.2)
    glow = cv2.resize(cv2.GaussianBlur(cv2.resize(cv, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 3), (W, H))
    return np.clip(out + (cv[..., None] * GOLDW * 0.8 + glow[..., None] * GOLD2 * 1.5) * min(1.0, amt), 0, 1)

def emblem_flash(A, B, j, f, sa, sb, pre=12, post=12):
    """the emblem reveal: the Flash emblem draws itself in light over the frame (the ring traced round, the bolt
    slashed in), flares, and the next shot opens through the ring."""
    cx, cy, R = W / 2, 1690, 190                                         # drawn where his chest emblem will be (off the face)
    ring, disc, bolt = emblem_shape(cx, cy, R)
    if j < 0:
        u = (j + pre + 1) / pre; cv = bolt_canvas()
        ang = 360 * ein(min(1, u / 0.6), 1.3)
        cv2.ellipse(cv, (int(cx), int(cy)), (R, R), -90, 0, ang, 255, 8, cv2.LINE_AA)
        if u > 0.55:
            P = np.array([(0.18, -0.92), (-0.46, 0.08), (-0.04, 0.08), (-0.20, 0.92), (0.48, -0.14), (0.05, -0.14), (0.18, -0.92)], np.float32)
            k = clamp((u - 0.55) / 0.45, 0, 1); n = max(2, int(len(P) * k + 1))
            cv2.polylines(cv, [np.stack([cx + P[:n, 0] * R, cy + P[:n, 1] * R], 1).astype(np.int32)], False, 255, 6, cv2.LINE_AA)
        return np.clip(A * (1 - 0.35 * u) + light_from(cv, 1.0 + 0.6 * u), 0, 1)
    v = (j + 1) / post; s_ = 1 + 11 * ein(v, 2.0)
    ring, disc, bolt = emblem_shape(cx, cy, R * s_)
    m = cv2.GaussianBlur(disc, (0, 0), 3)[..., None]
    o = B * m + A * (1 - 0.5 * v) * (1 - m)
    edge = cv2.GaussianBlur(ring, (0, 0), 4)[..., None]
    return np.clip(o + edge * GOLDW * 1.4 * (1 - v) + (1 - eout(v, 3)) * 0.25 * GOLDW * (j < 2), 0, 1)

TR2.update({"red_phase": (red_phase, 10, 12), "red_link": (red_link, 6, 10), "red_slices": (red_slices, 6, 9),
            "red_streak": (red_streak, 8, 8), "dolly": (dolly, 8, 12), "bolt_split": (bolt_split, 22, 16),
            "gold_link": (arc_link, 6, 9), "whip": (whip, 6, 8), "speedforce_in": (speedforce_in, 10, 14),
            "emblem_flash": (emblem_flash, 12, 12)})

# ---- the loop: the red lightning snatches the last frame back to Harrison ------------------------------------
_LP = {}
def loop_frame0():
    if "w" not in _LP: _LP["w"], _ = base11(SHOTS[0], 0)
    return _LP["w"]

def loop_out(out, f):
    """from E_LOOP: a red streak circles the frame, the picture shudders in red, and the last frames are Harrison."""
    f0 = fh(E.E_LOOP); k = f - f0; n = E.DUR_F - f0
    if k < 0: return out
    u = (k + 1) / n
    amt = 3 + 22 * ein(u, 1.6)
    w0 = loop_frame0()
    blend = smooth((u - 0.55) / 0.45)
    o = red_vibe(out, amt, f, 5) * (1 - blend) + red_vibe(w0, amt * (1 - 0.6 * blend), f, 6) * blend
    hx = -300 + (W + 600) * ein(min(1, u * 1.6), 1.2); y = H * 0.86                       # along the bottom, off his face
    cv = bolt_canvas()
    if u < 0.7:
        put_bolt(cv, (hx - 500, y + 30), (hx, y - 10), 3500 + f, 6, 0.25, 7, 2)
    return np.clip(o + light_rgb(cv, 1.2, REDW, RED2), 0, 1)

def loop_in(out, f, k, n=14):
    """frame 0 continues the red shudder and settles on Harrison."""
    if k >= n: return out
    v = k / n; amt = 3 + 22 * 0.4 * (1 - smooth(v)) ** 1.2
    return red_vibe(out, amt * (1 - v) + 0.6, f, 6) if amt * (1 - v) > 0.6 else out

# ---- the time freeze: the world drains to steel, he stays in colour (alive=True) ------------------------------
_frozen_world_v10 = frozen_world
def frozen_world(img, person, f, s, amt):
    """the stopped moment: gold sparks hang in the air; the colour only partly drains (drain=), so he stays readable."""
    o = _frozen_world_v10(img, person, f, s, amt)
    d = s.get("drain")
    if d is None: return o
    return np.clip(img + (o - img) * d, 0, 1)

# ---- graphics in the frame -------------------------------------------------------------------------------------
def base11(s, f):
    img, person = base10(s, f)
    if s.get("red_arcs"): img = red_arcs(img, f, person, s["red_arcs"])
    if s.get("warp"): img = speed_warp(img, f, s["warp"] * (0.6 + 0.4 * beat_kick(f)), subject_point(s, f, person))
    return img, person

def beat_kick(f):
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; return math.exp(-ph / 0.12)

# ---- the camera moves with the music ---------------------------------------------------------------------------
def beat_phase(f):
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    hook = (E.HDROP + 1 <= e < E.E_LOOP) and not (50 <= e < 56)                       # not in the time freeze
    rival = E.E_BEAT <= e < E.E_DIP
    return ph, bi, hook, rival

def beat_bounce(f):
    ph, bi, hook, rival = beat_phase(f)
    if hook: return 1 + 0.055 * math.exp(-ph / 0.10)
    if rival: return 1 + 0.025 * math.exp(-ph / 0.09)
    return 1.0

_shake_v10 = _shake_r4
def shake(f):
    dx, dy, rot = _shake_v10(f)
    ph, bi, hook, rival = beat_phase(f)
    if hook: rot += (1.0 if bi % 2 else -1.0) * math.exp(-ph / 0.13)
    return dx, dy, rot

def beat_fx(out, f):
    ph, bi, hook, rival = beat_phase(f)
    if not hook or ph > 0.06: return out
    k = math.exp(-ph / 0.025)
    return np.clip(rgb_split(radial_blur(out, W / 2, H * 0.46, 1.0, 1.0 + 0.04 * k, 4), 8 * k), 0, 1)

_ramp_v10 = ramp
def ramp(A, B, j, f, sa, sb, pre=6, post=7):
    """the speed ramp, without the brightness lift (the fire shots are already hot)."""
    if j < 0:
        u = (j + pre + 1) / pre; z = 1 + 0.25 * ein(u, 2.2)
        return np.clip(hblur(zoom_about(A, W / 2, H * 0.45, z), 2 + 180 * ein(u, 2)), 0, 1)
    v = (j + 1) / post; z = 1 + 0.22 * (1 - eout(v, 2.4))
    return np.clip(hblur(zoom_about(B, W / 2, H * 0.45, z), 2 + 160 * (1 - eout(v, 2))), 0, 1)
TR2["ramp"] = (ramp, 6, 7)

def init_hits():
    HITS.clear()
    HITS.append((fh(E.HDROP), 20, 4.5)); HITS.append((fh(E.E_BEAT), 10, 3.0))

# ---- type: two designed words ----------------------------------------------------------------------------------
def text_letsgo(out, f, tx):
    """LET'S GO: LET'S eases in (fade, rise, blur to sharp); GO lands big and white-hot, struck by a gold bolt, its
    letters crackling; the pair rides the bolt split (drawn before the transition), so the drop tears it apart."""
    t = f / FPS; (w0, t0, _), (w1, t1, _) = tx["words"]
    if t < t0 - 0.02 or t > tx["end"] + 0.02: return out
    out = out * cap_scrim(1260, 1680, 0.36 * smooth((t - t0 + 0.05) / 0.25))
    a = cap_word(w0, 112, False); v0 = eout(clamp((t - t0) / 0.18, 0, 1), 2.4)
    out = ease_word(out, a, W / 2, 1330, v0, 1.0, 30)                                    # clear of his chin
    if t >= t1 - 0.02:
        b = cap_word(w1, 300, True); v = clamp((t - t1) / 0.16, 0, 1); sc = 1.5 - 0.5 * eout(v, 3.0)
        bb = cv2.resize(b, (int(b.shape[1] * sc), int(b.shape[0] * sc)))
        if v < 1: bb = cv2.GaussianBlur(bb, (0, 0), 0.1 + 6 * (1 - v))
        hot = clamp(1 - (t - t1) / 0.30, 0, 1)
        bb[..., :3] = bb[..., :3] * (1 - 0.6 * hot) + GOLDW * 0.6 * hot * (bb[..., 3:4] > 0.5)
        out = paste(out, bb, int(W / 2 - bb.shape[1] / 2), int(1515 - bb.shape[0] / 2), min(1, v * 1.5))
        cv = bolt_canvas()
        if v < 0.7: put_bolt(cv, (W / 2 + 60, 1200), (W / 2 - 10, 1405), 3600 + f, 4, 0.25, 6, 1)
        hw = b.shape[1] / 2 - 60
        for q in range(2):
            x0 = W / 2 + (q * 2 - 1) * hw * 0.7; put_bolt(cv, (x0, 1405), (x0 + 40 * (q * 2 - 1), 1340 - 30 * ((f // 3 + q) % 2)), 3610 + q + f // 2, 2, 0.35, 4, 0)
        out = out + light_from(cv, 0.9 * (0.5 + 0.5 * hot))
    return np.clip(out, 0, 1)

def text_bop(out, f, tx):
    """BOP: the three letters punch in one per sixteenth (scale bounce, blur to sharp); the O is the Flash emblem's
    ring with its bolt; on the beat after, it leaves in a gold speed smear."""
    t = f / FPS; (w0, t0, _), = tx["words"]
    if t < t0 - 0.02 or t > tx["end"] + 0.02: return out
    t_end = tx["end"]; ex = smooth((t - (t_end - 0.16)) / 0.16)
    out = out * cap_scrim(1180, 1640, 0.34 * (1 - ex) * smooth((t - t0 + 0.05) / 0.2))
    lets, wd = hero_letters("BOP", 250, 14); lay = np.zeros((H, W, 4), np.float32); yc = 1420; cv = bolt_canvas()
    for i, (c, lm, xoff) in enumerate(lets):
        v = clamp((t - t0 - 0.06 * i) / 0.16, 0, 1)
        if v <= 0: continue
        ve = eout(v, 3.0); x = W / 2 + xoff
        sc = (0.5 + 0.5 * ve + 0.12 * math.sin(math.pi * v)) * (1 + 0.04 * beat_kick(f))
        if c == "O":                                                                          # the emblem as the O
            Rr = lm.shape[0] * 0.47
            ring, disc, bolt = emblem_shape(x + 600 * ex ** 1.5, yc, Rr * sc)
            al = min(1, ve * 1.5) * (1 - ex)
            ringb = cv2.GaussianBlur(ring, (0, 0), 0.6 + 6 * (1 - ve) + 6 * ex)
            boltb = cv2.GaussianBlur(bolt, (0, 0), 0.6 + 6 * (1 - ve) + 6 * ex)
            k_ = cv2.dilate(np.maximum(ringb, boltb), np.ones((9, 9), np.uint8))
            out = out * (1 - k_[..., None] * 0.85 * al) + (ringb[..., None] * EMPH + boltb[..., None] * GOLDW) * al
            if v < 0.6: put_bolt(cv, (x + 30, yc - 260), (x, yc - Rr * 0.9), 3700 + f, 3, 0.3, 5, 0)
            continue
        spr = letter_sprite(lm, 250, True)
        draw_sprite(lay, spr, x + 600 * ex ** 1.5, yc + 30 * (1 - ve), sc, 0.0, 1.0, (0.1 + 5 * (1 - ve) + 10 * ex) if (v < 1 or ex > 0) else 0.0,
                    min(1, ve * 1.5) * (1 - ex), stretch=1 + 3.0 * ex)
    out = out + light_from(cv, 1.0)
    out = out * (1 - lay[..., 3:4]) + lay[..., :3]
    return np.clip(out, 0, 1)

def text11(out, f, s, rides):
    for tx in E.TEXT:
        if bool(tx.get("rides")) != rides: continue
        if tx["style"] == "letsgo": out = text_letsgo(out, f, tx)
        elif tx["style"] == "bop": out = text_bop(out, f, tx)
    return out

# ---- the frame -------------------------------------------------------------------------------------------------
_B11 = {}
def edge11(S_, which):
    key = (S_["n"], which)
    if key not in _B11:
        if len(_B11) > 6: _B11.clear()
        _B11[key] = base11(S_, S_["f0"] if which == "first" else S_["f1"] - 1)[0]
    return _B11[key]

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base11(s, f)
    out = text11(out, f, s, True)
    if tin == "loop_in": out = loop_in(out, f, k)
    elif tin in TR2 and k < TR2[tin][2] and P is not None:
        A = edge11(P, "last")
        if tin == "bolt_split": A = text11(A.copy(), P["f1"] - 1, P, True)                  # LET'S GO is torn by the seam
        out = TR2[tin][0](A, out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge11(n_, "first"), kn, f, s, n_)
    if s.get("wave"): out = drop_wave(out, f, s)
    out = beat_fx(out, f)
    out = loop_out(out, f)
    out = text11(out, f, s, False)
    late = f >= fh(E.E_LOOP) + 0.55 * (E.DUR_F - fh(E.E_LOOP))                              # the last frames are Harrison's
    out = finish11(out, f, SHOTS[0] if late else s)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)



# ============================================================================ v11 rev 2 — more of everything
# Owner notes: "a lot more animations, graphics, transitions… more sound effects… absolutely amazing."
# New transitions: RED EYE DIVE (into Eobard's glowing red eye, out of Barry's eye), STROBE ECHO (stroboscopic gold
# afterimages), BOLT TRACE (a bolt zig-zags across and the next shot burns in along it), HEAT HAZE (the fire's heat
# rises up the frame and carries the next shot in), CLASH (red and gold lightning collide on the new punch shot).
# New graphics: embers (red for the rival, orange off the fire), gold dust, speed particles in depth (through the
# matte), edge lightning on bar lines (red before the drop, gold after), light sweeps.

# ---- particles in depth ----------------------------------------------------------------------------------------
_PM11 = {}
def pm11(mode):
    if mode not in _PM11:
        rng = np.random.default_rng({"ember": 3, "dust": 5, "speed": 7, "fire": 9}[mode])
        n = {"ember": 70, "dust": 60, "speed": 54, "fire": 90}[mode]
        _PM11[mode] = [dict(x0=rng.uniform(0, 1), y0=rng.uniform(0, 1), z=rng.uniform(0.1, 1.0) ** 1.4, ph=rng.uniform(0, 6.283),
                            on=rng.uniform(0, 1), v=rng.uniform(0.6, 1.4)) for _ in range(n)]
    return _PM11[mode]

def motes11(out, f, person, dens, mode, rival=False, s=None):
    """ember: rising embers; fire: denser orange embers; dust: slow gold dust; speed: streaks rushing past in depth."""
    if dens <= 0.01: return out
    t = f / FPS; back = np.zeros((H, W), np.float32); front = np.zeros((H, W), np.float32)
    for p in pm11(mode):
        if p["on"] > dens: continue
        z = p["z"]; tgt = front if z > 0.62 else back
        if mode in ("ember", "fire"):
            sp = (110 + 300 * z) * p["v"] * (1.6 if mode == "fire" else 1.0)
            x = (p["x0"] * W + 40 * math.sin(1.3 * t + p["ph"]) + 25 * z * math.sin(3.1 * t + p["ph"] * 2)) % W
            y = (p["y0"] * (H + 200) - sp * t) % (H + 200) - 100
            r = 1.2 + 4.2 * z; tw = 0.55 + 0.45 * math.sin(7 * t + p["ph"] * 3)
            cv2.circle(tgt, (int(x), int(y)), max(1, int(r)), (0.55 + 0.45 * z) * tw, -1, cv2.LINE_AA)
            if z > 0.5: cv2.line(tgt, (int(x), int(y)), (int(x), int(y + r * 5)), 0.35 * tw, max(1, int(r * 0.6)), cv2.LINE_AA)
        elif mode == "dust":
            x = (p["x0"] * (W + 200) + (25 + 70 * z) * t * p["v"] + 30 * math.sin(0.8 * t + p["ph"])) % (W + 200) - 100
            y = (p["y0"] * (H + 200) - (15 + 40 * z) * t + 20 * math.sin(0.6 * t + p["ph"])) % (H + 200) - 100
            r = 1.0 + 3.0 * z; tw = 0.5 + 0.5 * math.sin(5 * t + p["ph"] * 2)
            cv2.circle(tgt, (int(x), int(y)), max(1, int(r)), (0.4 + 0.5 * z) * tw, -1, cv2.LINE_AA)
        else:                                                                                  # speed
            sp = (1400 + 3200 * z) * p["v"]; L_ = 80 + 520 * z
            x = (p["x0"] * (W + 1200) + sp * t) % (W + 1200) - 600; y = p["y0"] * H
            cv2.line(tgt, (int(x - L_), int(y)), (int(x), int(y)), 0.45 + 0.55 * z, max(1, int(1 + 3 * z)), cv2.LINE_AA)
    if person is not None: back *= (1 - np.clip(person * 1.3, 0, 1))
    hb = head_box(s, f, person) if s is not None else None
    if hb is not None:                                                                      # nothing in front of his face
        cxh, wh = (hb[0] + hb[1]) / 2, (hb[1] - hb[0]) / 2 + 40
        hm = np.clip(1 - np.maximum(np.abs(_GX - cxh) / wh, (_GY - (hb[2] - 2.2 * wh)) * 0 + np.clip((_GY - hb[2]) / 60, 0, 1) * 9), 0, 1)
        hm = cv2.GaussianBlur(hm.astype(np.float32), (0, 0), 25)
        front *= (1 - hm); back *= (1 - hm * (0.0 if person is not None else 1.0))
    lay = back * 0.8 + cv2.GaussianBlur(front, (0, 0), 1.8 + (2.0 if mode == "speed" else 0.0)) * 1.25
    glow = cv2.resize(cv2.GaussianBlur(cv2.resize(lay, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 3), (W, H))
    if mode == "ember" and rival: core, gl = REDW, RED2
    elif mode in ("ember", "fire"): core, gl = np.array([0.35, 0.75, 1.0], np.float32), EMBER2
    else: core, gl = GOLDW, GOLD2
    a = min(1.0, dens * 1.2) * (0.75 if mode == "dust" else 1.0)
    return np.clip(out + (lay[..., None] * core * 0.9 + glow[..., None] * gl * 1.5) * a, 0, 1)

# ---- bar-line graphics -----------------------------------------------------------------------------------------
EDGE11 = {8: "red", 16: "red", 40: "gold", 48: "gold", 72: "gold"}
SWEEP11 = (26, 44, 58)
def edge_bolts11(out, f):
    """lightning flickers down both frame edges on chosen bar lines (red before the drop, gold after); never the centre."""
    for e_, col in EDGE11.items():
        k = f - fh(e_)
        if not (0 <= k < 9): continue
        a = [1.0, 0.4, 0.9, 0.2, 0.7, 0.3, 0.5, 0.15, 0.25][k]; cv = bolt_canvas()
        for side, x0 in ((0, W * 0.05), (1, W * 0.95)):
            put_bolt(cv, (x0 + (side * 2 - 1) * 10, -30), (x0 - (side * 2 - 1) * 40, H * (0.45 + 0.25 * ((f // 9 + side) % 2))), 4000 + e_ * 7 + f // 9 * 3 + side, 2, 0.30, 6, 1)
        out = np.clip(out + (light_rgb(cv, a * 0.9, REDW, RED2) if col == "red" else light_from(cv, a * 0.9)), 0, 1)
    return out

def sweep11(out, f):
    """a diagonal band of white-gold light sweeps across the frame on chosen half-beats."""
    for e_ in SWEEP11:
        k = f - fh(e_)
        if not (0 <= k < 16): continue
        u = k / 15; pos = -400 + (W + 800) * ein(u, 1.3); d = (_GX + (_GY - H / 2) * 0.35) - pos
        band = np.exp(-(d / 70) ** 2) * 0.55 + np.exp(-(d / 240) ** 2) * 0.25
        out = np.clip(out + band[..., None] * (GOLDW * 0.6 + GOLD2 * 0.4) * math.sin(math.pi * u) * 0.55, 0, 1)
    return out

# ---- transitions -----------------------------------------------------------------------------------------------
_EYE11 = {}
def red_eye_point(sa):
    """the brightest red point (his glowing eye) in the outgoing shot's last frame, on screen."""
    if sa["n"] not in _EYE11:
        A = edge11(sa, "last"); r = A[..., 2] - np.maximum(A[..., 0], A[..., 1]) * 0.9
        r = cv2.GaussianBlur(r[: int(H * 0.7)], (0, 0), 6)
        y, x = np.unravel_index(int(np.argmax(r)), r.shape); _EYE11[sa["n"]] = (float(x), float(y))
    return _EYE11[sa["n"]]

def barry_eye(sb):
    f = sb["f0"]; t, u, _ = src_time(sb, f); fa = face_at(sb, t)
    if fa:
        if len(fa) > 3 and fa[3] is not None and len(fa[3]) >= 4:
            pts = [to_screen(sb, f, fa[3][0], fa[3][1])[:2], to_screen(sb, f, fa[3][2], fa[3][3])[:2]]
            return min(pts, key=lambda q: abs(q[0] - W / 2))
        x, y, _ = to_screen(sb, f, fa[0], fa[1]); return x, y
    return W / 2, H * 0.37

def red_eye_dive(A, B, j, f, sa, sb, pre=14, post=14):
    """RED EYE DIVE: the camera dives into the rival's glowing red eye until the frame is red light, then pulls out of
    Barry's eye on the other side (the answer)."""
    if j < 0:
        u = (j + pre + 1) / pre; ex, ey = red_eye_point(sa)
        Z = math.exp(math.log(16.0) * ein(u, 2.3))
        o = radial_blur(zoom_about(A, ex, ey, Z), ex, ey, 1.0, 1.0 + 0.10 * u, 5)
        r = 30 + 1100 * ein(u, 2.0)
        g = np.exp(-(((_GX - ex) ** 2 + (_GY - ey) ** 2) / (r * r)))[..., None]
        o = o + g * (RED2 * 1.4 + REDW * 0.4) * (0.4 + 1.2 * u)
        return np.clip(o * (1 - 0.25 * u) + 0.20 * u * RED2, 0, 1)
    v = (j + 1) / post; bx, by = barry_eye(sb)
    Z = math.exp(math.log(12.0) * (1 - eout(v, 2.2)))
    o = radial_blur(zoom_about(B, bx, by, Z), bx, by, 1.0, 1.0 + 0.09 * (1 - v), 5)
    k = (1 - v) ** 1.4
    red = np.clip(o * np.array([0.55, 0.55, 1.25], np.float32) + 0.25 * RED2, 0, 1)
    return np.clip(o * (1 - 0.8 * k) + red * 0.8 * k, 0, 1)

def gold_tint(img, a=0.8):
    L = lum8(img)[..., None]; return img * (1 - a) + (L * GOLD2 * 1.2 + L * GOLDW * 0.3) * a

def shiftx(img, dx):
    return cv2.warpAffine(img, np.float32([[1, 0, dx], [0, 1, 0]]), (W, H), borderMode=cv2.BORDER_REFLECT)

def strobe_echo(A, B, j, f, sa, sb, pre=8, post=10):
    """STROBE ECHO: he moves so fast the frame strobes: the picture snaps left leaving a trail of gold stroboscopic
    afterimages, and the next shot lands from the right with its own echoes collapsing into place."""
    if j < 0:
        u = (j + pre + 1) / pre; s = -W * 0.42 * ein(u, 2.0); gap = 70 + 120 * u
        o = shiftx(A, s)
        for k in range(4, 0, -1):
            a = 0.42 * u / k ** 0.8
            o = o * (1 - a) + gold_tint(shiftx(A, s + k * gap)) * a
        return np.clip(hblur(o, 2 + 60 * u), 0, 1)
    v = (j + 1) / post; s = W * 0.42 * (1 - eout(v, 2.4)); gap = (70 + 120 * (1 - v)) * (1 - v)
    o = shiftx(B, s)
    for k in range(4, 0, -1):
        a = 0.42 * (1 - v) / k ** 0.8
        o = o * (1 - a) + gold_tint(shiftx(B, s + k * gap)) * a
    return np.clip(hblur(o, 2 + 60 * (1 - v)), 0, 1)

_BT = {}
def trace_path():
    if "p" not in _BT:
        way = [(-60, 1150), (230, 1010), (420, 1250), (640, 1080), (850, 1330), (1140, 1190)]
        pts = [bolt_points(a, b, 900 + i, 0.18, 5) for i, (a, b) in enumerate(zip(way, way[1:]))]
        _BT["p"] = np.vstack(pts).astype(np.float32)
    return _BT["p"]

def bolt_trace(A, B, j, f, sa, sb, pre=10, post=14):
    """BOLT TRACE: a bolt zig-zags across the frame (below his face), and the next shot burns in along it, the
    edges glowing like embers."""
    pp = trace_path()
    if j < 0:
        u = (j + pre + 1) / pre; n = max(2, int(len(pp) * ein(u, 1.1)))
        cv = bolt_canvas(); cv2.polylines(cv, [pp[:n].astype(np.int32)], False, 255, 4, cv2.LINE_AA)
        hx, hy = pp[n - 1]
        o = A * (1 - 0.2 * u) + light_from(cv, 1.2)
        return np.clip(add_glow(o, hx, hy, 70, 1.0, GOLDW), 0, 1)
    v = (j + 1) / post
    if "d" not in _BT:
        cv = bolt_canvas(); cv2.polylines(cv, [pp.astype(np.int32)], False, 255, 3, cv2.LINE_AA)
        _BT["d"] = cv2.distanceTransform(255 - cv, cv2.DIST_L2, 3); _BT["cv"] = cv
    dist = _BT["d"]; R = 8 + 1500 * ein(v, 1.8)
    n_ = 0.5 + 0.5 * np.sin(_GX * 0.013 + _GY * 0.009 + f * 0.4)                            # a ragged burn edge
    m = np.clip((R - dist - 40 * n_) / 22.0, 0, 1)[..., None]
    o = B * m + A * (1 - m) * (1 - 0.3 * v)
    rim = np.exp(-((dist + 40 * n_ - R) / 14.0) ** 2)[..., None] * (1 - v)
    return np.clip(o + rim * (EMBER2 * 0.9 + GOLDW * 0.4) + light_from(_BT["cv"], 1.2 * (1 - v) ** 1.5), 0, 1)

def heat_haze(A, B, j, f, sa, sb, pre=10, post=12):
    """HEAT HAZE: the fire's heat rises up the frame: the picture shimmers and refracts, and the next shot is carried
    in behind a rising wall of heat with a glowing edge."""
    p = (j + pre + 1) / (pre + post); ye = H * (1.12 - 1.30 * smooth(p))
    wav = 70 * np.sin(_GX[:1] * 0.018 + f * 0.35) + 40 * np.sin(_GX[:1] * 0.047 - f * 0.5)
    edge = ye + wav
    amp = 22 * math.sin(math.pi * p)
    band = np.exp(-((_GY - edge) / 260.0) ** 2)
    mx = (_GX + (amp * (0.35 + band) * np.sin(_GY * 0.045 + f * 0.9))).astype(np.float32)
    my = (_GY + 12 * band * np.sin(_GX * 0.03 + f * 0.7)).astype(np.float32)
    Ar = cv2.remap(A, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    Br = cv2.remap(B, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    m = np.clip((_GY - edge) / 70.0, 0, 1)[..., None]
    o = Br * m + Ar * (1 - m)
    glow = np.exp(-((_GY - edge) / 40.0) ** 2)[..., None] * math.sin(math.pi * p)
    return np.clip(o + glow * (EMBER2 * 0.8 + GOLDW * 0.25), 0, 1)

_CL = {}
def clash_sparks():
    if "s" not in _CL:
        rng = np.random.default_rng(17)
        _CL["s"] = [(rng.uniform(0, 2 * math.pi), rng.uniform(400, 1500), rng.uniform(0.4, 1.0), rng.random() < 0.5) for _ in range(46)]
    return _CL["s"]

def clash(A, B, j, f, sa, sb, pre=10, post=14):
    """CLASH: a red bolt from the left and a gold bolt from the right race toward each other and collide; sparks of
    both colours burst out and the punch lands behind a refracting shockwave."""
    P = (W * 0.50, H * 0.64)
    if j < 0:
        u = (j + pre + 1) / pre; e = ein(u, 1.6)
        cr, cg = bolt_canvas(), bolt_canvas()
        put_bolt(cr, (-40, H * 0.50), (-40 + (P[0] + 40) * e, H * 0.50 + (P[1] - H * 0.50) * e), 4100 + f, 4, 0.22, 7, 2)
        put_bolt(cg, (W + 40, H * 0.80), (W + 40 - (W + 40 - P[0]) * e, H * 0.80 + (P[1] - H * 0.80) * e), 4150 + f, 4, 0.22, 7, 2)
        o = A * (1 - 0.3 * u) + light_rgb(cr, 1.2, REDW, RED2) + light_from(cg, 1.2)
        return np.clip(o, 0, 1)
    v = (j + 1) / post
    o = B.copy()
    dx, dy = _GX - P[0], _GY - P[1]; r = np.sqrt(dx * dx + dy * dy) + 1e-3; R = 80 + 1700 * eout(v, 1.5)
    band = np.exp(-((r - R) / 80.0) ** 2); disp = band * 55 * (1 - v)
    o = cv2.remap(o, (_GX - dx / r * disp).astype(np.float32), (_GY - dy / r * disp).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    o = o + np.exp(-((r - R) / 8.0) ** 2)[..., None] * GOLDW * 0.7 * (1 - v)
    cr, cg = bolt_canvas(), bolt_canvas()
    for (a, L_, s_, red) in clash_sparks():
        d0 = L_ * eout(v, 1.8) * s_; d1 = d0 + 40 + 120 * (1 - v)
        cv2.line(cr if red else cg, (int(P[0] + math.cos(a) * d0), int(P[1] + math.sin(a) * d0)),
                 (int(P[0] + math.cos(a) * d1), int(P[1] + math.sin(a) * d1)), int(255 * (1 - v)), 3, cv2.LINE_AA)
    o = o + light_rgb(cr, 1.0, REDW, RED2) + light_from(cg, 1.0)
    if j < 4: o = add_glow(o, P[0], P[1], 260, 1.2 * (1 - j / 4), GOLDW)
    return np.clip(o, 0, 1)

TR2.update({"red_eye_dive": (red_eye_dive, 14, 14), "strobe_echo": (strobe_echo, 8, 10), "bolt_trace": (bolt_trace, 10, 14),
            "heat_haze": (heat_haze, 10, 12), "clash": (clash, 10, 14)})

# ---- the frame (rev 2) -----------------------------------------------------------------------------------------
_base11_r1 = base11
def base11(s, f):
    img, person = _base11_r1(s, f)
    for mode in ("ember", "fire", "dust", "speed"):
        if s.get(mode): img = motes11(img, f, person, s[mode], mode, rival=is_rival(s), s=s)
    return img, person

_init_hits_r1 = init_hits
def init_hits():
    _init_hits_r1(); HITS.append((fh(74), 16, 4.0))

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base11(s, f)
    out = text11(out, f, s, True)
    if tin == "loop_in": out = loop_in(out, f, k)
    elif tin in TR2 and k < TR2[tin][2] and P is not None:
        A = edge11(P, "last")
        if tin == "bolt_split": A = text11(A.copy(), P["f1"] - 1, P, True)
        out = TR2[tin][0](A, out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge11(n_, "first"), kn, f, s, n_)
    if s.get("wave"): out = drop_wave(out, f, s)
    out = edge_bolts11(out, f)
    out = sweep11(out, f)
    out = beat_fx(out, f)
    out = loop_out(out, f)
    out = text11(out, f, s, False)
    late = f >= fh(E.E_LOOP) + 0.55 * (E.DUR_F - fh(E.E_LOOP))
    out = finish11(out, f, SHOTS[0] if late else s)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)



# ============================================================================ v11 rev 3 — REVERSE (the loop) + new beat moments
# Owner notes: a more creative loop with a cool graphic/animation; replace the parts where Barry just moves to the beat.
# THE LOOP, REVERSE (e82-e88): red lightning strikes Barry's chest emblem; the REAL emblem in the footage inverts into
#   the Reverse-Flash's (the cream disc turns black, the gold bolt and rim turn red, lit by the footage's own shading);
#   red lightning radiates out of it across his suit and the frame drains to the rival's red; the camera dives through
#   the reversed emblem and lands on Harrison Wells (frame 0) — the rivalry loops.
# NEW BEAT MOMENTS: AURA (the grin: silhouette rings pulse outward on every beat), REMNANTS (the smirk: time-remnant
#   copies split off sideways on each beat and snap back), CHARGE (the bar close-up: lightning gathers from the frame
#   edges into his chest before the Speed Force flight).
E_STRIKE, E_RADIATE, E_DIVE = 82, 84, 86

# ---- the chest emblem, found in the source frame and mapped to the screen -------------------------------------------
_EMB = {}
def emblem_src(s, t):
    """(x, y, r) of the Flash emblem in source px: the cream disc in the lower half of the frame."""
    pk = s["src"]; fps = E.SRC[pk][1]; U = UNIQ[pk]
    k = U[clamp(bisect.bisect_right(U, t * fps + 0.3) - 1, 0, len(U) - 1)]
    if k not in _EMB:
        img = FR[(pk, k)][400:720, 420:860].astype(np.float32) / 255
        L = img.mean(2); sat = img.max(2) - img.min(2)
        m = ((L > 0.62) & (sat < 0.22)).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))   # bridge the bolt
        n, lab, st, cen = cv2.connectedComponentsWithStats(m)
        if n < 2: _EMB[k] = None
        else:
            i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
            cs, _ = cv2.findContours((lab == i).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            pts = max(cs, key=len)[:, 0, :].astype(np.float64)
            pts = pts[(pts[:, 1] < 313) & (pts[:, 0] > 2) & (pts[:, 0] < 437)]                # drop the frame edges (the disc is cut there)
            if len(pts) < 20:
                a_ = st[i, cv2.CC_STAT_AREA]; _EMB[k] = (float(cen[i][0] + 420), float(cen[i][1] + 400), math.sqrt(a_ / math.pi) * 1.24)
            else:                                                                              # algebraic circle fit to the visible edge
                A_ = np.column_stack([pts[:, 0], pts[:, 1], np.ones(len(pts))]); b_ = -(pts[:, 0] ** 2 + pts[:, 1] ** 2)
                c_ = np.linalg.lstsq(A_, b_, rcond=None)[0]; xc, yc = -c_[0] / 2, -c_[1] / 2
                r_ = math.sqrt(max(1.0, xc * xc + yc * yc - c_[2]))
                _EMB[k] = (float(xc + 420), float(yc + 400), r_ * 1.13)                          # + the gold rim
    return _EMB[k]

def emblem_screen(s, f):
    t, u, _ = src_time(s, f); e = emblem_src(s, t)
    if e is None: return W / 2, H * 0.88, 110.0
    x, y, sc = to_screen(s, f, e[0], e[1]); return x, y, e[2] * sc

def reverse_emblem(out, cx, cy, R, p, f):
    """invert the emblem in place: the cream disc -> glossy black, the gold rim and bolt -> glowing red. p = wipe 0..1
    from the top-right (where the strike hits)."""
    x0, y0, x1, y1 = int(max(0, cx - R * 1.5)), int(max(0, cy - R * 1.5)), int(min(W, cx + R * 1.5)), int(min(H, cy + R * 1.5))
    if x1 <= x0 or y1 <= y0 or p <= 0: return out
    sub = out[y0:y1, x0:x1]; gy, gx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    rr = np.sqrt((gx - cx) ** 2 + (gy - cy) ** 2)
    disc = np.clip((R * 1.04 - rr) / 3.0, 0, 1)
    sx, sy = cx + R * 0.55, cy - R * 0.85
    wipe = np.clip((p * 2.6 * R - np.sqrt((gx - sx) ** 2 + (gy - sy) ** 2)) / 14.0, 0, 1)
    m = (disc * wipe)[..., None]
    L = sub.mean(2, keepdims=True); sat = sub.max(2, keepdims=True) - sub.min(2, keepdims=True)
    gold = np.clip((sat - 0.12) * 5, 0, 1) * np.clip((L - 0.20) * 3, 0, 1)
    dark = 0.018 + 0.10 * np.clip(L - 0.55, 0, 1) ** 1.5 * np.array([0.6, 0.6, 1.0], np.float32)      # glossy black, keeps the sheen
    redm = L * np.array([0.25, 0.22, 1.25], np.float32) * 1.25 + RED2 * 0.25
    new = dark * (1 - gold) + redm * gold
    sub2 = sub * (1 - m) + new * m
    glow = cv2.GaussianBlur((gold[..., 0] * m[..., 0]).astype(np.float32), (0, 0), 6)[..., None]
    edge = np.exp(-((np.sqrt((gx - sx) ** 2 + (gy - sy) ** 2) - p * 2.6 * R) / 5.0) ** 2)[..., None] * disc[..., None] * (p < 1)
    out[y0:y1, x0:x1] = np.clip(sub2 + glow * RED2 * 0.9 + edge * REDW * 0.9, 0, 1)
    return out

# ---- THE LOOP ----------------------------------------------------------------------------------------------------
_W0 = {}
def frame0_base():
    if "w" not in _W0: _W0["w"], _ = base11(SHOTS[0], 0)
    return _W0["w"]

_DV = {}
def dive_anchor(s):
    if "a" not in _DV: _DV["a"] = emblem_screen(s, fh(E_DIVE))
    return _DV["a"]

def reverse_loop(out, f, s, person):
    if s["n"] != "stare" or f < fh(E_STRIKE) - 10: return out
    cx, cy, R = emblem_screen(s, f) if f < fh(E_DIVE) else dive_anchor(s)
    if f < fh(E_STRIKE):                                                                    # red crackles creep in from the edges
        k = (f - fh(E_STRIKE) + 10) / 10; cv = bolt_canvas()
        for side in (0, 1):
            x0 = -20 if side == 0 else W + 20
            put_bolt(cv, (x0, H * (0.55 + 0.1 * side)), (x0 + (1 - 2 * side) * 260 * k, H * (0.62 + 0.08 * side)), 5000 + f + side, 2, 0.35, 5, 1)
        return np.clip(out + light_rgb(cv, 0.8 * k, REDW, RED2), 0, 1)
    if f < fh(E_RADIATE):                                                                   # the strike, the inversion
        k = f - fh(E_STRIKE); n = fh(E_RADIATE) - fh(E_STRIKE)
        p = ein(clamp((k - 3) / (n - 6), 0, 1), 1.3)
        out = reverse_emblem(out.copy(), cx, cy, R, p, f)
        cv = bolt_canvas()
        if k < 9:
            put_bolt(cv, (W + 30, H * 0.50), (cx + R * 0.55, cy - R * 0.85), 5100 + f, 5, 0.22, 7, 2)
        out = out + light_rgb(cv, 1.4, REDW, RED2)
        if k < 6: out = add_glow(out, cx + R * 0.5, cy - R * 0.8, 160, 1.0 * (1 - k / 6), REDW)
        rr = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2); Rw = R + 900 * eout(k / n, 1.6)
        out = out + np.exp(-((rr - Rw) / 9.0) ** 2)[..., None] * REDW * 0.6 * (1 - k / n)
        return np.clip(out, 0, 1)
    if f < fh(E_DIVE):                                                                      # the red radiates over him
        k = f - fh(E_RADIATE); n = fh(E_DIVE) - fh(E_RADIATE); u = k / n
        out = reverse_emblem(out.copy(), cx, cy, R, 1.0, f)
        rr = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2); Rw = R + 2300 * ein(u, 1.3)
        w = np.clip((Rw - rr) / 140, 0, 1)[..., None]
        L = lum8(out)[..., None]; red_ = L * np.array([0.30, 0.32, 1.12], np.float32) + 0.02 * RED2
        out = out * (1 - 0.65 * w) + red_ * 0.65 * w
        out = red_arcs(out, f, person, 0.9 * u + 0.3, 9)
        cv = bolt_canvas(); rng = np.random.default_rng(f // 2 * 5 + 1)
        for q in range(5):
            a = rng.uniform(-0.3, math.pi + 0.3); L_ = R * rng.uniform(1.6, 3.6) * (0.5 + u)
            put_bolt(cv, (cx + math.cos(a) * R, cy + math.sin(a) * R * 0.9), (cx + math.cos(a) * (R + L_), cy + math.sin(a) * (R + L_) * 0.9), 5200 + f // 2 * 7 + q, 3, 0.3, 6, 1)
        out = out + light_rgb(cv, 1.1, REDW, RED2)
        return np.clip(add_glow(out, cx, cy, R * 1.6, 0.35 + 0.35 * beat_kick(f), RED2), 0, 1)
    # the dive through the reversed emblem into Harrison (frame 0)
    k = f - fh(E_DIVE); n = E.DUR_F - 1 - fh(E_DIVE); q = clamp(k / n, 0, 1)
    out = reverse_emblem(out.copy(), cx, cy, R, 1.0, f)
    L = lum8(out)[..., None]; out = out * 0.35 + (L * np.array([0.30, 0.32, 1.12], np.float32)) * 0.65
    Z = math.exp(math.log(30.0) * ein(q, 2.2))
    o = zoom_about(out, cx, cy, Z)
    if q < 0.95: o = radial_blur(o, cx, cy, 1.0, 1.0 + 0.10 * math.sin(math.pi * q), 4)
    Rp = R * 0.86 * Z
    zi = 1.03 + 0.9 * (1 - smooth(q))
    inside = zoom_about(frame0_base(), W / 2, H * 0.45, zi)
    if q < 1: inside = radial_blur(inside, cx, cy, 1.0, 1.0 + 0.05 * (1 - q), 3)
    rr = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2)
    m = np.clip((Rp - rr) / 6.0, 0, 1)[..., None]
    o = inside * m + o * (1 - m)
    fade = 1 - smooth((Rp - 2300) / 600)
    ring = np.exp(-((rr - Rp) / (4 + 0.03 * Rp)) ** 2) + 0.4 * np.exp(-((rr - Rp) / (20 + 0.10 * Rp)) ** 2)
    o = o + ring[..., None] * (REDW * 0.9 + RED2 * 0.5) * fade
    if fade > 0.05 and Rp < 2600:
        cv = bolt_canvas(); rng = np.random.default_rng(f * 3 + 7)
        for qq in range(6):
            a0 = rng.uniform(0, 2 * math.pi); a1 = a0 + rng.uniform(0.25, 0.6)
            put_bolt(cv, (cx + Rp * math.cos(a0), cy + Rp * math.sin(a0)), (cx + Rp * math.cos(a1), cy + Rp * math.sin(a1)), 5300 + f + qq, 3, 0.25, 5, 0)
        o = o + light_rgb(cv, 1.0 * fade, REDW, RED2)
    return np.clip(o, 0, 1)

def loop_in(out, f, k, n=12):
    """frame 0 continues the dive's momentum: a last 3 % settle as the reversed emblem's ring passes off the frame."""
    if k >= n: return out
    v = k / n; zi = 1.0 + 0.03 * (1 - smooth(v))
    return zoom_about(out, W / 2, H * 0.45, zi)

_orbit_v10 = orbit_ribbons
def orbit_ribbons(out, s, f, person, amt):
    if s["n"] == "stare": amt = amt * (1 - smooth((f - fh(E_STRIKE) + 14) / 12))          # gold gives way to red
    return _orbit_v10(out, s, f, person, amt) if amt > 0.01 else out

# ---- AURA: silhouette rings pulse outward on every beat ---------------------------------------------------------
def aura_pulse(out, s, f, person, amt):
    if person is None or amt <= 0.01: return out
    pm = (cv2.resize(person, (W // 4, H // 4), interpolation=cv2.INTER_AREA) > 0.5).astype(np.uint8)
    if pm.sum() < 200: return out
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; cv = np.zeros((H // 4, W // 4), np.float32)
    for age, a0 in ((ph, 1.0), (ph + 2 * E.HB, 0.45)):
        if age > 0.9: continue
        r = 2 + int(42 * ein(min(1.0, age / 0.6), 1.4)); a = a0 * (1 - age / 0.9) ** 1.3
        d1 = cv2.dilate(pm, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
        r2 = max(0, r - 2); d2 = cv2.dilate(pm, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r2 + 1, 2 * r2 + 1)))
        cv += (d1 - d2).astype(np.float32) * a
    cv = cv2.GaussianBlur(cv, (0, 0), 0.8)
    big = cv2.resize(cv, (W, H), interpolation=cv2.INTER_LINEAR)
    glow = cv2.resize(cv2.GaussianBlur(cv, (0, 0), 4), (W, H))
    return np.clip(out + (big[..., None] * GOLDW * 0.9 + glow[..., None] * GOLD2 * 1.4) * amt, 0, 1)

# ---- REMNANTS: time-remnant copies split off sideways on each beat ---------------------------------------------
def time_remnants(out, s, f, person, amt):
    if person is None or amt <= 0.01: return out
    e = f / FPS / E.HB; ph = (e % 2) * E.HB
    off = 150 * math.exp(-ph / 0.16) + 14; a = (0.30 + 0.45 * math.exp(-ph / 0.20)) * amt
    pm = np.clip(person * 1.15, 0, 1)
    o = out.copy()
    for d, col in ((-off, GOLD2), (off, np.array([1.0, 0.85, 0.55], np.float32)), (-off * 2.1, EMBER2), (off * 2.1, GOLD2)):
        al = shiftx(pm[..., None].repeat(3, 2), d)[..., :1] * (a if abs(d) < off * 1.5 else a * 0.45)
        im = shiftx(out, d); L = lum8(im)[..., None]
        tint = im * 0.35 + L * col * 1.1
        o = o * (1 - al) + tint * al
    edge = cv2.GaussianBlur(cv2.morphologyEx((pm > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8)).astype(np.float32), (0, 0), 3)
    o = o * (1 - pm[..., None]) + out * pm[..., None]                                   # he stays on top, solid
    return np.clip(o + edge[..., None] * GOLDW * 0.5 * math.exp(-ph / 0.2) * amt, 0, 1)

# ---- CHARGE: lightning gathers from the frame edges into his chest ----------------------------------------------
def charge_up(out, s, f, person, amt):
    amt = amt * (1 - 0.6 * smooth((f - (s["f1"] - 18)) / 10))                              # the rift takes over
    if amt <= 0.01: return out
    u = (f - s["f0"]) / max(1, s["f1"] - s["f0"]); cx, cy = subject_point(s, f, person)
    bx = face_box(s, f); cy = max(cy, (bx[2] + 120) if bx else cy)
    cv = bolt_canvas(); rng = np.random.default_rng(f // 2 * 11 + 3)
    starts = [(-30, H * 0.62), (W + 30, H * 0.66), (-30, H * 0.86), (W + 30, H * 0.90), (W * 0.25, H + 30), (W * 0.78, H + 30)]
    nb = int(2 + 4 * u)
    for i, (x0, y0) in enumerate(starts[:nb]):
        reach = ein(clamp(u * 1.4 - i * 0.08, 0, 1), 1.2)
        x1, y1 = x0 + (cx - x0) * reach, y0 + (cy - y0) * reach
        put_bolt(cv, (x0, y0), (x1, y1), 5400 + i * 13 + f // 2, 2 + (u > 0.6), 0.28, 6, 1)
    t = f / FPS; dust = np.zeros((H // 2, W // 2), np.float32)
    for i in range(40):
        a0 = i * 2.39996; R0 = 900 * ((i * 0.618 + t * 0.9) % 1.0)
        r = R0 * (1 - 0.0); a = a0 + (900 - R0) / 300
        x, y = (cx + math.cos(a) * r) / 2, (cy + math.sin(a) * r * 0.9) / 2
        cv2.circle(dust, (int(x), int(y)), 1 + int(2 * (1 - R0 / 900)), 0.5 + 0.5 * (1 - R0 / 900), -1, cv2.LINE_AA)
    dust = cv2.resize(cv2.GaussianBlur(dust, (0, 0), 0.8), (W, H))
    o = out + light_from(cv, (0.7 + 0.6 * u) * amt) + dust[..., None] * GOLDW * 0.7 * amt
    return np.clip(add_glow(o, cx, cy, 90 + 160 * u, (0.25 + 0.75 * u ** 2) * amt, GOLDW), 0, 1)

_base11_r2 = base11
def base11(s, f):
    img, person = _base11_r2(s, f)
    if s.get("aura"): img = aura_pulse(img, s, f, person, s["aura"])
    if s.get("remnants"): img = time_remnants(img, s, f, person, s["remnants"])
    if s.get("charge"): img = charge_up(img, s, f, person, s["charge"])
    return img, person

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base11(s, f)
    out = text11(out, f, s, True)
    if tin == "loop_in": out = loop_in(out, f, k)
    elif tin in TR2 and k < TR2[tin][2] and P is not None:
        A = edge11(P, "last")
        if tin == "bolt_split": A = text11(A.copy(), P["f1"] - 1, P, True)
        out = TR2[tin][0](A, out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge11(n_, "first"), kn, f, s, n_)
    if s.get("wave"): out = drop_wave(out, f, s)
    out = edge_bolts11(out, f)
    out = sweep11(out, f)
    out = beat_fx(out, f)
    out = reverse_loop(out, f, s, person)
    out = text11(out, f, s, False)
    out = finish11(out, f, SHOTS[0] if f >= fh(E_RADIATE) + 8 else s)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)



# ============================================================================ v11 rev 4 — the emblem, the dive, THE RIFT
# Owner notes: polish the symbol, make it more detailed; the loop transition smoother and flashier; a new creative
# focal-point effect.
#   EMBLEM: a detailed Reverse-Flash emblem (bevelled crimson-metal rim with a groove and a neon line, glossy black disc
#     with a reflection, a bevelled red bolt with an emissive core and red light spill), lit to match the shot; the real
#     emblem FLIPS like a coin to reveal it (its edge visible, a flare at 90 degrees, a shockwave and sparks on landing).
#   DIVE: an anticipation pull-back, then an accelerating dive into the black disc with speed-matched motion blur, radial
#     light rays, chromatic fringes, sparks flying past and a red flare as the rim passes the camera; lands on frame 0.
#   THE RIFT (focal point, e64): after the charge-up he tears a lightning rift across the frame (below his face); the
#     Speed Force churns inside it, the frame's light spills out, the camera flies through, and the flight through fire
#     rushes out of the vanishing point.
E_DIVE = 85

# ---- the Reverse-Flash emblem ------------------------------------------------------------------------------------
_RFE = {}
def rf_emblem_base():
    if "base" in _RFE: return _RFE["base"]
    S = 768; R = 360.0; c = S / 2
    gy, gx = np.mgrid[0:S, 0:S].astype(np.float32); dx, dy = gx - c, gy - c; r = np.sqrt(dx * dx + dy * dy) + 1e-6
    Lv = np.array([-0.45, -0.65, 0.62], np.float32); Lv /= np.linalg.norm(Lv)
    Hv = Lv + np.array([0, 0, 1], np.float32); Hv /= np.linalg.norm(Hv)
    def shade(h):
        hy, hx = np.gradient(h)
        n = np.dstack([-hx, -hy, np.ones_like(h)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
        return np.clip(n @ Lv, 0, 1), np.clip(n @ Hv, 0, 1) ** 48
    ri, ro = 0.84 * R, R
    hr = np.where((r >= ri) & (r <= ro), np.sin(np.pi * (r - ri) / (ro - ri)), 0).astype(np.float32)
    dif_r, spe_r = shade(hr * 26)
    brushed = 0.04 * np.sin(np.arctan2(dy, dx) * 90)                                           # spun-metal rim
    rim = np.array([0.05, 0.05, 0.42], np.float32) * (0.30 + 0.95 * dif_r[..., None] + brushed[..., None]) \
        + spe_r[..., None] * np.array([0.85, 0.85, 1.0], np.float32) * 0.95
    blk = 0.014 + 0.035 * np.clip(1 - r / (0.83 * R), 0, 1)
    ref = np.exp(-((np.sqrt((gx - (c - 0.30 * R)) ** 2 + (gy - (c - 0.38 * R)) ** 2) - 0.70 * R) / (0.035 * R)) ** 2)
    ref *= np.clip(-(dx + dy) / (0.8 * R), 0, 1)
    inner = np.dstack([blk, blk, blk * 1.25]) + ref[..., None] * np.array([0.30, 0.28, 0.38], np.float32) * 0.40
    inner += (0.006 * np.sin(r * 0.55))[..., None]
    P = np.array([(0.18, -0.92), (-0.46, 0.08), (-0.04, 0.08), (-0.20, 0.92), (0.48, -0.14), (0.05, -0.14)], np.float32)
    poly = np.stack([c + P[:, 0] * 0.82 * R * 1.10, c + P[:, 1] * 0.82 * R * 1.10], 1)
    bm = np.zeros((S, S), np.uint8); cv2.fillPoly(bm, [(poly * 4).astype(np.int32)], 255, cv2.LINE_AA, shift=2)
    bmf = bm.astype(np.float32) / 255
    dt = cv2.distanceTransform((bmf > 0.5).astype(np.uint8), cv2.DIST_L2, 5)
    dif_b, spe_b = shade(np.clip(dt / 9.0, 0, 1) ** 0.6 * 14)
    core = np.clip((dt - 6) / 10, 0, 1)
    bolt = np.array([0.05, 0.07, 0.86], np.float32) * (0.35 + 0.9 * dif_b[..., None]) + spe_b[..., None] * np.array([0.75, 0.8, 1.0], np.float32) * 0.8 \
        + core[..., None] * np.array([0.30, 0.38, 1.0], np.float32) * 0.35
    outline = np.clip(cv2.dilate(bmf, np.ones((7, 7), np.uint8)) - bmf, 0, 1)
    spill = cv2.GaussianBlur(bmf, (0, 0), 22)
    col = np.where((r < ri)[..., None], inner + spill[..., None] * RED2 * 0.55, rim)
    groove = np.exp(-((r - 0.835 * R) / 2.2) ** 2); ghi = np.exp(-((r - 0.826 * R) / 1.4) ** 2)
    col = col * (1 - groove[..., None] * 0.8) + ghi[..., None] * np.array([0.35, 0.3, 0.6], np.float32) * 0.6
    col = col * (1 - outline[..., None]) + np.array([0.01, 0.0, 0.03], np.float32) * outline[..., None]
    col = col * (1 - bmf[..., None]) + bolt * bmf[..., None]
    col = col + np.exp(-((r - 0.845 * R) / 3.0) ** 2)[..., None] * RED2 * 0.45
    alpha = np.clip((R + 0.5 - r) / 1.5, 0, 1)
    _RFE["base"] = (np.clip(col, 0, 1.5).astype(np.float32), alpha.astype(np.float32), bmf, poly / S, R, S)
    return _RFE["base"]

def rf_emblem(Rpx):
    key = int(round(Rpx))
    if key not in _RFE:
        if len(_RFE) > 40: [_RFE.pop(k_) for k_ in list(_RFE) if k_ != "base"][:1]
        col, alpha, bmf, poly, R, S = rf_emblem_base(); n = max(8, int(round(S * key / R)))
        _RFE[key] = (cv2.resize(np.dstack([col, alpha]), (n, n), interpolation=cv2.INTER_AREA),
                     cv2.resize(bmf, (n, n), interpolation=cv2.INTER_AREA), poly * n)
    return _RFE[key]

def paste_rgba(out, rgba, cx, cy, sx=1.0, a=1.0):
    h, w = rgba.shape[:2]; nw = max(2, int(round(w * sx)))
    t = cv2.resize(rgba, (nw, h), interpolation=cv2.INTER_AREA) if nw != w else rgba
    x0, y0 = int(round(cx - nw / 2)), int(round(cy - h / 2))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + nw), min(H, y0 + h)
    if xb <= xa or yb <= ya: return out
    sub = t[ya - y0:yb - y0, xa - x0:xb - x0]; al = sub[..., 3:4] * a
    out[ya:yb, xa:xb] = out[ya:yb, xa:xb] * (1 - al) + sub[..., :3] * al
    return out

def light_match(out, cx, cy, R):
    """the shot's soft light over the emblem (from the real emblem's own luminance), as a gain map to multiply into it."""
    x0, y0, x1, y1 = int(max(0, cx - R)), int(max(0, cy - R)), int(min(W, cx + R)), int(min(H, cy + R))
    if x1 - x0 < 8 or y1 - y0 < 8: return 1.0
    L = cv2.GaussianBlur(lum8(out[y0:y1, x0:x1]), (0, 0), max(2, R * 0.4)); return float(np.clip(L.mean() / 0.62, 0.75, 1.2))

def coin_flip(out, cx, cy, R, theta, f):
    """the real emblem flips on its vertical axis like a coin; its back is the Reverse-Flash emblem."""
    hs = int(R * 1.45); x0, y0, x1, y1 = int(max(0, cx - hs)), int(max(0, cy - hs)), int(min(W, cx + hs)), int(min(H, cy + hs))
    if x1 - x0 < 16 or y1 - y0 < 16: return out
    crop = out[y0:y1, x0:x1].copy(); lcx, lcy = cx - x0, cy - y0
    gy, gx = np.mgrid[0:y1 - y0, 0:x1 - x0].astype(np.float32); rr = np.sqrt((gx - lcx) ** 2 + (gy - lcy) ** 2)
    disc = np.clip((R * 1.0 - rr) / 2.0, 0, 1)
    m = ((rr < R * 1.08) * 255).astype(np.uint8)
    h2, w2 = (y1 - y0) // 2, (x1 - x0) // 2
    inp = cv2.inpaint((cv2.resize(crop, (w2, h2)) * 255).astype(np.uint8), cv2.resize(m, (w2, h2)), 5, cv2.INPAINT_TELEA)
    inp = cv2.resize(inp.astype(np.float32) / 255, (x1 - x0, y1 - y0))
    mm = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 3)[..., None]
    base = crop * (1 - mm) + inp * mm
    th_ = math.radians(theta); sx = abs(math.cos(th_)); edge = 0.08 * R * abs(math.sin(th_)); side = 1 if math.sin(th_) >= 0 else -1
    if edge > 0.5:                                                                        # the coin's edge (its thickness)
        em = np.zeros(base.shape[:2], np.float32)
        cv2.ellipse(em, (int(lcx + side * edge * 0.5), int(lcy)), (max(1, int(sx * R + edge * 0.5)), int(R)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
        shade = 0.5 + 0.5 * np.clip((gy - lcy) / R * -1, -1, 1)
        ec = np.array([0.05, 0.05, 0.35], np.float32) * (0.4 + 0.6 * shade[..., None]) + np.exp(-((gy - (lcy - R * 0.55)) / 6) ** 2)[..., None] * 0.25
        base = base * (1 - em[..., None]) + ec * em[..., None]
    tile = base.copy()
    if theta < 90:                                                                        # the front: the real emblem, in place
        pad = np.dstack([crop, disc]).astype(np.float32)
    else:                                                                                 # the back: the Reverse-Flash emblem
        sp, _, _ = rf_emblem(R); rgba = sp.copy(); rgba[..., :3] *= light_match(out, cx, cy, R)
        pad = np.zeros((y1 - y0, x1 - x0, 4), np.float32)
        hh, ww = rgba.shape[:2]; px0, py0 = int(round(lcx - ww / 2)), int(round(lcy - hh / 2))
        xa, ya, xb, yb = max(0, px0), max(0, py0), min(x1 - x0, px0 + ww), min(y1 - y0, py0 + hh)
        if xb > xa and yb > ya: pad[ya:yb, xa:xb] = rgba[ya - py0:yb - py0, xa - px0:xb - px0]
    pad[..., :3] *= (0.55 + 0.45 * sx)                                                    # edge-on, it darkens
    nw = max(2, int(round((x1 - x0) * sx)))
    sq = cv2.resize(pad, (nw, y1 - y0), interpolation=cv2.INTER_AREA)
    ox = int(round(lcx - lcx * sx))
    xa, xb = max(0, ox), min(x1 - x0, ox + nw)
    if xb > xa:
        part = sq[:, xa - ox:xb - ox]; al = part[..., 3:4]
        tile[:, xa:xb] = tile[:, xa:xb] * (1 - al) + part[..., :3] * al
    out[y0:y1, x0:x1] = tile
    return out

def emblem_energy(out, cx, cy, R, f, amt):
    """the reversed emblem alive: a pulsing core, small red crackles along the bolt."""
    _, _, poly = rf_emblem(R); pts = poly - rf_emblem(R)[0].shape[0] / 2 + np.array([cx, cy], np.float32)
    cv = bolt_canvas(); rng = np.random.default_rng(f // 2 * 13 + 2)
    for q in range(3):
        i = int(rng.integers(len(pts))); a = pts[i]; b = pts[(i + 1) % len(pts)]; t0 = rng.uniform(0, 0.7)
        put_bolt(cv, tuple(a + (b - a) * t0), tuple(a + (b - a) * (t0 + 0.3) + rng.normal(0, R * 0.05, 2)), 6000 + f // 2 * 7 + q, 1, 0.4, 4, 0)
    o = out + light_rgb(cv, 0.9 * amt, REDW, RED2)
    return add_glow(o, cx, cy, R * 0.9, (0.25 + 0.30 * beat_kick(f)) * amt, RED2)

def star_flare(out, cx, cy, a, col):
    """an anamorphic star: a long horizontal streak and a shorter vertical one."""
    if a <= 0.01: return out
    hz = np.exp(-((_GY - cy) / 5.0) ** 2) * np.exp(-np.abs(_GX - cx) / 520.0)
    vt = np.exp(-((_GX - cx) / 4.0) ** 2) * np.exp(-np.abs(_GY - cy) / 300.0)
    return out + (hz + 0.6 * vt)[..., None] * col * a

def red_sparks(out, cx, cy, R, age, seed):
    if age < 0 or age > 22: return out
    rng = np.random.default_rng(seed); cv = bolt_canvas(); v = age / 22
    for i in range(36):
        a = rng.uniform(0, 2 * math.pi); sp = rng.uniform(0.5, 1.0)
        d0 = R * (1.0 + 2.6 * eout(v, 1.8) * sp); d1 = d0 + 18 + 60 * (1 - v)
        cv2.line(cv, (int(cx + math.cos(a) * d0), int(cy + math.sin(a) * d0 * 0.95)), (int(cx + math.cos(a) * d1), int(cy + math.sin(a) * d1 * 0.95)),
                 int(255 * (1 - v)), 2, cv2.LINE_AA)
    return out + light_rgb(cv, 1.0, REDW, RED2)

# ---- the loop, rebuilt ------------------------------------------------------------------------------------------
def red_drain(out, cx, cy, u):
    rr = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2); Rw = 120 + 2300 * ein(clamp(u, 0, 1), 1.3)
    w = np.clip((Rw - rr) / 140, 0, 1)[..., None]
    L = lum8(out)[..., None]; red_ = L * np.array([0.30, 0.32, 1.12], np.float32) + 0.02 * RED2
    return out * (1 - 0.65 * w) + red_ * 0.65 * w

def reverse_loop(out, f, s, person):
    if s["n"] != "stare" or f < fh(E_STRIKE) - 10: return out
    fs, fr, fd = fh(E_STRIKE), fh(E_RADIATE), fh(E_DIVE)
    cx, cy, R = emblem_screen(s, f) if f < fd else dive_anchor(s)
    if f < fs:                                                                              # red crackles creep in
        k = (f - fs + 10) / 10; cv = bolt_canvas()
        for side in (0, 1):
            x0 = -20 if side == 0 else W + 20
            put_bolt(cv, (x0, H * (0.55 + 0.1 * side)), (x0 + (1 - 2 * side) * 260 * k, H * (0.62 + 0.08 * side)), 5000 + f + side, 2, 0.35, 5, 1)
        return np.clip(out + light_rgb(cv, 0.8 * k, REDW, RED2), 0, 1)
    k = f - fs
    if f < fd:
        if k < 4: th_ = 0.0
        elif k < 17: th_ = 180 * smooth((k - 4) / 13)
        else: th_ = 180 + 14 * math.exp(-(k - 17) / 3.0) * math.sin((k - 17) * 1.5)
        if th_ < 0: th_ = -th_
        o = out.copy()
        if f >= fr: o = red_drain(o, cx, cy, (f - fr) / max(1, fd - fr) * 0.8 + 0.2 * clamp((f - fr) / 6, 0, 1))
        o = coin_flip(o, cx, cy, R, min(th_, 359.0), f)
        cv = bolt_canvas()
        if k < 9: put_bolt(cv, (W + 30, H * 0.50), (cx + R * 0.55, cy - R * 0.85), 5100 + f, 5, 0.22, 7, 2)
        o = o + light_rgb(cv, 1.4, REDW, RED2)
        if k < 6: o = add_glow(o, cx + R * 0.5, cy - R * 0.8, 160, 1.0 * (1 - k / 6), REDW)
        fl = math.exp(-((k - 10.5) / 1.8) ** 2)                                           # the flare as it turns edge-on
        o = add_glow(o, cx, cy, R * 2.0, 1.2 * fl, REDW); o = star_flare(o, cx, cy, 0.9 * fl, REDW * 0.7 + 0.3)
        if k >= 17:
            o = red_sparks(o, cx, cy, R, k - 17, 77)
            rr = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2); Rw = R + 1100 * eout(min(1, (k - 17) / 14), 1.6)
            o = o + np.exp(-((rr - Rw) / 9.0) ** 2)[..., None] * REDW * 0.7 * max(0, 1 - (k - 17) / 14)
            o = emblem_energy(o, cx, cy, R, f, clamp((k - 17) / 6, 0, 1))
        if f >= fr:
            u = (f - fr) / max(1, fd - fr)
            o = red_arcs(o, f, person, 0.6 + 0.4 * u, 9)
            cv = bolt_canvas(); rng = np.random.default_rng(f // 2 * 5 + 1)
            for q in range(5):
                a = rng.uniform(-0.3, math.pi + 0.3); L_ = R * rng.uniform(1.6, 3.6) * (0.6 + u)
                put_bolt(cv, (cx + math.cos(a) * R, cy + math.sin(a) * R * 0.9), (cx + math.cos(a) * (R + L_), cy + math.sin(a) * (R + L_) * 0.9), 5200 + f // 2 * 7 + q, 3, 0.3, 6, 1)
            o = o + light_rgb(cv, 1.1, REDW, RED2)
        return np.clip(o, 0, 1)
    # ---- THE DIVE: anticipation, then an accelerating plunge through the black disc onto frame 0
    k = f - fd; n = E.DUR_F - 1 - fd; q = clamp(k / n, 0, 1)
    base = red_drain(out.copy(), cx, cy, 1.0)
    sp, _, _ = rf_emblem(R); sp = sp.copy(); sp[..., :3] *= light_match(out, cx, cy, R)
    base = paste_rgba(base, sp, cx, cy)
    base = emblem_energy(base, cx, cy, R, f, 1.0 - q)
    def Zq(qq): return (1 - 0.06 * math.sin(math.pi * clamp(qq / 0.18, 0, 1))) * math.exp(math.log(34.0) * ein(clamp((qq - 0.10) / 0.90, 0, 1), 2.5))
    Z = Zq(q); spd = (math.log(Zq(min(1, q + 0.02))) - math.log(Zq(q))) / 0.02
    o = zoom_about(base, cx, cy, Z)
    bs = min(0.14, 0.012 * spd)
    if bs > 0.004: o = radial_blur(o, cx, cy, 1.0, 1.0 + bs, 5)
    cs = min(1.0, spd / 6)
    if cs > 0.02:                                                                          # chromatic fringe, radial
        o2 = o.copy(); o2[..., 2] = zoom_about(o, cx, cy, 1 + 0.012 * cs)[..., 2]; o2[..., 0] = zoom_about(o, cx, cy, 1 - 0.012 * cs)[..., 0]; o = o2
    rr = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2); ang = np.arctan2(_GY - cy, _GX - cx)
    if cs > 0.02:                                                                          # light rays streaming past
        rays = np.clip(np.sin(ang * 23 + 1.3) * np.sin(ang * 37 - f * 0.2), 0, 1) ** 6 * np.clip((rr - 80) / 600, 0, 1)
        o = o + rays[..., None] * (REDW * 0.5 + 0.15) * 0.55 * cs
    Rp = R * 0.80 * Z
    zi = 1.03 + 0.85 * (1 - smooth(q))
    inside = zoom_about(frame0_base(), W / 2, H * 0.45, zi)
    if q < 1: inside = radial_blur(inside, W / 2, H * 0.45, 1.0, 1.0 + 0.05 * (1 - q) ** 2, 3)
    tint = (1 - smooth(q / 0.92)) * 0.45
    if tint > 0.005: inside = inside * (1 - tint) + (lum8(inside)[..., None] * np.array([0.30, 0.32, 1.12], np.float32)) * tint
    m = np.clip((Rp - rr) / 6.0, 0, 1)[..., None]
    o = inside * m + o * (1 - m)
    diag = math.hypot(max(cx, W - cx), max(cy, H - cy))
    fade = 1 - smooth((Rp - diag) / (0.45 * diag))
    ring = np.exp(-((rr - Rp) / (4 + 0.03 * Rp)) ** 2) + 0.45 * np.exp(-((rr - Rp) / (20 + 0.10 * Rp)) ** 2)
    o = o + ring[..., None] * (REDW * 0.9 + RED2 * 0.5) * fade
    if fade > 0.05:
        cv = bolt_canvas(); rng = np.random.default_rng(f * 3 + 7)
        for qq in range(7):
            a0 = rng.uniform(0, 2 * math.pi); a1 = a0 + rng.uniform(0.25, 0.6)
            put_bolt(cv, (cx + Rp * math.cos(a0), cy + Rp * math.sin(a0)), (cx + Rp * math.cos(a1), cy + Rp * math.sin(a1)), 5300 + f + qq, 3, 0.25, 5, 0)
        o = o + light_rgb(cv, 1.0 * fade, REDW, RED2)
        o = red_sparks(o, cx, cy, Rp * 0.9, int(22 * q), 91)
    flash = math.exp(-((Rp - diag) / (0.30 * diag)) ** 2) * (1 - smooth((q - 0.86) / 0.12))   # the rim passes the lens
    if flash > 0.01: o = o * (1 - 0.08 * flash) + flash * (REDW * 0.16 + RED2 * 0.10 + 0.03)     # a red flare, not a white-out
    return np.clip(o, 0, 1)

def dive_anchor(s):
    if "a" not in _DV: _DV["a"] = emblem_screen(s, fh(E_DIVE))
    return _DV["a"]

# ---- THE RIFT (focal point): torn open across the frame, the Speed Force inside, flown through --------------------
_RT = {}
def rift_geom():
    if "g" in _RT: return _RT["g"]
    p0, p1 = (-80.0, H * 0.94), (W + 80.0, H * 0.60)
    pts = bolt_points(p0, p1, 4242, 0.09, 6).astype(np.float32)
    d = np.diff(pts, axis=0); seg = np.hypot(d[:, 0], d[:, 1]); s = np.concatenate([[0], np.cumsum(seg)]); s /= s[-1]
    tg = np.vstack([d, d[-1:]]); tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6
    nrm = np.stack([-tg[:, 1], tg[:, 0]], 1)
    i = int(np.argmin(np.abs(s - 0.5)))
    _RT["g"] = (pts, s, nrm, (float(pts[i, 0]), float(pts[i, 1]))); return _RT["g"]

def rift_mask(oa, f, grow=1.0):
    """the opening (full res, float): a jagged lens along the path, oa = how open, grow = how much of the length is torn."""
    pts, s, nrm, _ = rift_geom()
    w = oa * 390 * np.sin(np.pi * s) ** 0.7 * (0.82 + 0.18 * np.sin(s * 47 + f * 0.35)) * np.clip((grow - np.abs(s - 0.5) * 2) * 6, 0, 1)
    left = pts + nrm * (w / 2)[:, None]; right = pts - nrm * (w / 2)[:, None]
    poly = np.vstack([left, right[::-1]])
    m = np.zeros((H // 2, W // 2), np.uint8); cv2.fillPoly(m, [(poly * 2).astype(np.int32)], 255, cv2.LINE_AA, shift=2)
    return cv2.resize(m.astype(np.float32) / 255, (W, H), interpolation=cv2.INTER_LINEAR)

def sf_interior(f, z):
    t = f / FPS; o = speedforce_bg(z, t).astype(np.float32) * 1.25 + 0.04 * GOLD2
    cv = bolt_canvas(); rng = np.random.default_rng(f // 2 * 3 + 11)
    for q in range(4):
        a0 = rng.uniform(0, 2 * math.pi); r0, r1 = rng.uniform(120, 300), rng.uniform(600, 1100)
        put_bolt(cv, (W / 2 + r0 * math.cos(a0), H / 2 + r0 * math.sin(a0) * 1.4), (W / 2 + r1 * math.cos(a0 + 0.3), H / 2 + r1 * math.sin(a0 + 0.3) * 1.4), 6100 + f + q, 2, 0.3, 6, 1)
    return np.clip(o + light_from(cv, 0.8), 0, 1)

def rift_edges(m, f, amt):
    """white-gold glowing edges with electric crackles along the tear."""
    e = cv2.morphologyEx((m[::2, ::2] > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(np.float32)
    e = cv2.resize(e, (W, H), interpolation=cv2.INTER_LINEAR)
    core = cv2.GaussianBlur(e, (0, 0), 1.5); gl = cv2.resize(cv2.GaussianBlur(cv2.resize(e, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 5), (W, H))
    return (core[..., None] * GOLDW * 1.3 + gl[..., None] * GOLD2 * 2.2) * amt

def rift(A, B, j, f, sa, sb, pre=18, post=26):
    pts, s, nrm, Pc = rift_geom()
    if j < 0:
        u = (j + pre + 1) / pre
        grow = ein(clamp(u / 0.40, 0, 1), 1.2); oa = 0.06 + 0.94 * ein(clamp((u - 0.30) / 0.70, 0, 1), 1.5)
        m = rift_mask(oa, f, grow)
        inter = sf_interior(f, u * 0.6)
        spill = cv2.GaussianBlur(m[::4, ::4], (0, 0), 18); spill = cv2.resize(spill, (W, H))[..., None]
        o = A * (1 - m[..., None]) + inter * m[..., None] + spill * GOLD2 * 0.55 * oa + rift_edges(m, f, 0.6 + 0.6 * oa)
        cv = bolt_canvas(); rng = np.random.default_rng(f * 5 + 3)
        for q in range(int(3 + 5 * u)):
            i = int(rng.integers(len(pts))); side = 1 if rng.random() < 0.5 else -1
            p = pts[i]; a = p + nrm[i] * side * 40; b = a + nrm[i] * side * rng.uniform(60, 200) + rng.normal(0, 40, 2)
            if abs(s[i] - 0.5) * 2 < grow: put_bolt(cv, tuple(a), tuple(b), 6200 + f * 9 + q, 2, 0.35, 5, 0)
        return np.clip(o + light_from(cv, 0.9), 0, 1)
    v = (j + 1) / post
    if j < 12:                                                                              # fly through the tear
        Z = math.exp(math.log(10.0) * ein((j + 1) / 12, 2.0))
        m = rift_mask(1.0, f, 1.0); inter = sf_interior(f, 0.6 + j * 0.08)
        comp = A * (1 - m[..., None]) + inter * m[..., None] + rift_edges(m, f, 1.2)
        o = radial_blur(zoom_about(comp, Pc[0], Pc[1], Z), Pc[0], Pc[1], 1.0, 1.0 + 0.10 * math.sin(math.pi * min(1, (j + 1) / 12)), 5)
        inside_full = clamp((j - 8) / 4, 0, 1)
        if inside_full > 0: o = o * (1 - inside_full) + sf_interior(f, 0.6 + j * 0.08) * inside_full
        return np.clip(o, 0, 1)
    inter = sf_interior(f, 0.6 + j * 0.08)                                                  # the next shot rushes out of the vanishing point
    w = clamp((j - 12) / (post - 15), 0, 1); sB = 0.05 + 0.95 * ein(w, 2.4)
    Bz = zoom_about(B, W / 2, H * 0.45, sB)
    if w < 1: Bz = radial_blur(Bz, W / 2, H * 0.45, 1.0, 1.0 + 0.10 * (1 - w), 4)
    hw, hh = W / 2 * sB, H / 2 * sB
    box = np.clip(np.minimum(hw - np.abs(_GX - W / 2), hh - np.abs(_GY - H * 0.45)) / 6.0, 0, 1)[..., None]
    o = inter * (1 - box) + Bz * box
    rim = np.exp(-(np.minimum(np.abs(np.abs(_GX - W / 2) - hw), np.abs(np.abs(_GY - H * 0.45) - hh)) / 5.0) ** 2) * (np.abs(_GX - W / 2) <= hw + 6) * (np.abs(_GY - H * 0.45) <= hh + 6)
    o = o + rim[..., None] * GOLDW * 1.0 * (1 - w)
    if w >= 1: o = Bz
    return np.clip(o, 0, 1)

TR2["rift"] = (rift, 18, 26)



# ============================================================================ v12 — BLOOM (The Flash × fakemink): LIGHTNING BLOOM
# "Night blooming" = the night Barry was struck by lightning. Lightning leaves Lichtenberg figures ("lightning flowers"),
# so the hero asset is a five-petal LIGHTNING JASMINE (lightning edges, Lichtenberg veins, a pale-yellow heart) that runs
# bud -> bloom -> full bloom -> closing through the edit. Look NOCTURNE: indigo nights, the suit kept crimson, lightning in
# jasmine white over a cream glow. New here: the jasmine asset, STRIKE LINK, ECG BOLT, BUD IRIS, THE BLOOM, FULL BLOOM
# (behind him, light wrap), PETAL PASS, POLLEN BURST, the closing-bud dive onto frame 0, the NIGHT / BLOOM titles, beat
# moments (pollen, bokeh stars, bud pulse, petal echo, aura). Library transitions are restyled through the palette below.
JASW = np.array([0.94, 0.98, 1.00], np.float32)          # BGR jasmine white (lightning core)
JASG = np.array([0.66, 0.90, 1.00], np.float32)          # BGR cream glow
JASY = np.array([0.30, 0.82, 1.00], np.float32)          # BGR pale-yellow heart
INDIGO = np.array([0.060, 0.012, -0.012], np.float32)    # BGR shadow push
INK = np.array([0.045, 0.020, 0.020], np.float32)        # keyline
F32 = np.float32
# restyle the library (rule 4): every gold / red / ember light in the v4-v11 transitions now draws in the v12 palette
GOLDW, GOLD2, GOLD, EMBER2 = JASW.copy(), JASG.copy(), np.array([0.55, 0.88, 1.00], F32), np.array([0.45, 0.80, 1.00], F32)
REDW, RED2 = JASW.copy(), JASY.copy()
if E.VER == "v12":                                                                         # v12's own shots only
    for _s in E.SHOTS:
        _s["look"] = "nocturne"; _s.setdefault("target", 0.34)
E_SKY_NIGHT = {"sky": 1.05, "wake": 0.25, "crouch": 0.60}       # daylight / bright shots pushed into the night

def addc(out, lay, col, k=1.0):
    """out[..., c] += lay * col[c] * k, channel by channel (in place; out float32 HxWx3)."""
    t = np.empty(lay.shape, F32)
    for c in range(3):
        np.multiply(lay, float(col[c]) * k, out=t); out[..., c] += t
    return out

def mixm(A, B, m):
    """A * (1 - m) + B * m for a single-channel mask m."""
    o = np.empty(A.shape, F32)
    for c in range(3): o[..., c] = A[..., c] + (B[..., c] - A[..., c]) * m
    return o

# ---- grade: NOCTURNE -------------------------------------------------------------------------------------------
_LUTN = {}
def lutN():
    if "n" not in _LUTN:
        x = np.linspace(0, 1, 1024, dtype=np.float32)
        _LUTN["n"] = (x, PchipInterpolator([0, .05, .20, .50, .80, .94, 1], [0.008, 0.022, 0.120, 0.420, 0.775, 0.925, 0.972])(x).astype(np.float32))
    return _LUTN["n"]

_grade_pre12 = grade
def grade(img, s, f):
    if s.get("look") != "nocturne": return _grade_pre12(img, s, f)
    g, gains = corr9(s); ev = (s.get("ev") or 0) - 0.55 * E_SKY_NIGHT.get(s["n"], 0.0)
    lx, ly = lutN()
    if in_unit(img): x = apply_lut3(img, tone_lut(("noct", s["n"], round(ev, 3), float(g), tuple(float(v) for v in gains)), gains, g, ev, lx, ly))
    else:
        x = np.clip(img * gains, 0, 1) ** g
        if ev: x = np.clip(x * 2 ** ev, 0, 1)
        x = np.interp(x, lx, ly).astype(F32)
    B, G, R = (np.ascontiguousarray(x[..., c]) for c in range(3))
    L = B * 0.114 + G * 0.587 + R * 0.299
    gr = G / (R + 1e-3); warm = np.clip((R - B) * 3.0, 0, 1)
    red = np.clip((0.40 - gr) * 5.0, 0, 1) * warm * np.clip(R * 3, 0, 1)                    # crimson (the suit)
    tame = s.get("tame", 0.0)
    if tame: red = red * (1 - tame)                                                           # red light, not a suit
    orng = np.clip(1 - np.abs(gr - 0.58) / 0.20, 0, 1) * warm * np.clip((L - 0.15) * 3, 0, 1)
    if tame: orng = np.clip(orng + tame * np.clip((0.62 - gr) * 4, 0, 1) * warm * np.clip((L - 0.10) * 3, 0, 1), 0, 1)
    hue = (R - G) / (R + 1e-3)
    skin = np.clip(1 - np.abs(hue - 0.22) / 0.22, 0, 1) * np.clip((R - B) * 6, 0, 1) * np.clip(L * 3, 0, 1) * (1 - orng)
    hot = np.clip((L - 0.36) * 2.6, 0, 1) * np.clip(orng + 0.6 * warm * (1 - red), 0, 1) * (1 - skin)   # orange light -> cream
    sat = (0.78 + 0.34 * red + 0.14 * skin) * (1 - 0.55 * orng * (1 - skin))
    sh = (1 - L) ** 2.4 * (1 - 0.6 * skin) * (1 - 0.7 * red)
    mid = L * (1 - L) * (1 - skin) * (1 - red)
    nk = E_SKY_NIGHT.get(s["n"], 0.0)
    if nk: keep = np.clip((L - 0.66) * 4.0, 0, 1); dark = 1 - 0.58 * nk * (1 - keep)
    o = np.empty(x.shape, F32); cream = (0.80, 0.93, 1.00); pushm = (0.035, 0.0, -0.022)
    for c, P in enumerate((B, G, R)):
        v = L + (P - L) * sat
        v = v + (L * cream[c] - v) * (0.80 * hot)
        v = v + sh * INDIGO[c] * (1.0 + 0.6 * nk) + mid * pushm[c]
        if nk: v = v * dark + (1 - dark) * INDIGO[c] * 0.25
        o[..., c] = v
    return np.clip(o, 0, 1, out=o)

_FIN12 = {}
def finish12(out, f, s):
    if "v" not in _FIN12:
        grain(0, 0.011); _FIN12["v"] = np.repeat(0.70 + 0.30 * VIG, 3, axis=2)
        _FIN12["floor"] = np.array([0.018, 0.011, 0.009], F32)
    k = ("g", f % 6)
    if k not in _FIN12: _FIN12[k] = np.repeat(grain(f, 0.011), 3, axis=2)
    small = cv2.resize(out, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi_ = np.clip(small.max(2) - 0.60, 0, 1)
    bl = cv2.resize(cv2.GaussianBlur(hi_, (0, 0), 4) * 0.40 + cv2.GaussianBlur(hi_, (0, 0), 18) * 0.60, (W, H))
    o = out.copy(); addc(o, bl, JASG, 0.42)
    np.maximum(o, _FIN12["floor"], out=o)
    o *= _FIN12["v"]; o += _FIN12[k]
    return np.clip(o, 0, 1, out=o)

# ---- the LIGHTNING JASMINE (hero asset) ----------------------------------------------------------------------------
def petal_hw(s): return np.maximum(np.sin(np.pi * np.clip(s, 0, 1) ** 0.85), 0) ** 0.7 * (1 - 0.18 * s)

_JV = {}
def jas_veins(seed):
    """Lichtenberg veins per petal in petal-local coords (s along 0..1, v across in half-widths); col 4 = growth time."""
    if seed in _JV: return _JV[seed]
    rng = np.random.default_rng(seed); out = []
    for p in range(10):
        segs = []; stack = [(0.03, 0.0, 0.0, 0.0, 0)]
        while stack and len(segs) < 230:
            s_, v_, a_, t_, g_ = stack.pop(); n = 0
            while s_ < 0.95 and n < 70:
                n += 1; st = rng.uniform(0.022, 0.040); a_ = clamp(a_ + rng.normal(0, 0.38), -1.2, 1.2)
                s2 = s_ + st * math.cos(a_); v2 = v_ + st * math.sin(a_) * 2.4
                lim = float(petal_hw(s2)) * 0.86
                if abs(v2) > lim: v2 = math.copysign(lim, v2); a_ = -a_ * 0.5
                segs.append((s_, v_, s2, v2, t_ + st, g_)); s_, v_, t_ = s2, v2, t_ + st
                if g_ < 3 and rng.random() < 0.14: stack.append((s_, v_, a_ + rng.choice([-1, 1]) * rng.uniform(0.5, 1.1), t_, g_ + 1))
                if g_ > 0 and rng.random() < 0.06 * g_: break
        arr = np.array(segs, F32); arr[:, 4] /= max(1e-6, float(arr[:, 4].max())); out.append(arr)
    _JV[seed] = out; return out

_SS = np.linspace(0, 1, 26).astype(F32)
def jas_geom(cx, cy, R, open_u, rot, squash=1.0):
    """per petal: a function local (s, v) -> screen, plus its outline polygon; outer layer opens first."""
    ps = []
    for i in range(10):
        layer = i // 5
        u = clamp(open_u, -0.2, 1.15) if layer == 0 else clamp((open_u - 0.16) / 0.84, -0.2, 1.15)
        ue = eout(clamp(u, 0, 1), 2.2) + max(0.0, u - 1.0)                                      # a small spring past flat
        phi = (1 - ue) * math.radians(78)
        Lp = R * (1.0 if layer == 0 else 0.70); Wp = Lp * (0.34 if layer == 0 else 0.40)
        ca = max(0.18, math.cos(phi)); r0 = R * 0.09 * (0.7 + 0.3 * clamp(u, 0, 1))
        th = rot + (i % 5) * 2 * math.pi / 5 + layer * math.pi / 5
        tw = (1 - clamp(u, 0, 1)) * 0.65; wscale = Wp * (0.50 + 0.50 * clamp(u, 0, 1))
        def to_xy(s, v, th=th, Lp=Lp, ca=ca, r0=r0, tw=tw, wscale=wscale):
            d = r0 + s * Lp * ca; a = th + tw * s; acr = v * wscale
            return cx + d * np.cos(a) - acr * np.sin(a), cy + (d * np.sin(a) + acr * np.cos(a)) * squash
        hw = petal_hw(_SS)
        lx_, ly_ = to_xy(_SS, hw); rx_, ry_ = to_xy(_SS[::-1], -hw[::-1])
        poly = np.stack([np.concatenate([lx_, rx_]), np.concatenate([ly_, ry_])], 1).astype(F32)
        ps.append((to_xy, poly, layer, th))
    return ps

def jas_draw(cx, cy, R, open_u, rot, f, seed=7, squash=1.0, vein_u=None, edge_w=2, fill_only=False, max_gen=3):
    """the flower's line canvas (uint8: lightning edges, veins, stamens) and fill mask (float32 0..1)."""
    core = np.zeros((H, W), np.uint8); fill = np.zeros((H, W), F32)
    if R < 2: return core, fill
    vein_u = clamp(open_u, 0, 1) if vein_u is None else vein_u
    veins = jas_veins(seed); rng = np.random.default_rng(seed * 1000 + f // 2)
    for i, (to_xy, poly, layer, th) in enumerate(jas_geom(cx, cy, R, open_u, rot, squash)):
        cv2.fillPoly(fill, [poly.astype(np.int32)], 1.0 if layer == 0 else 0.85, cv2.LINE_AA)
        if fill_only: continue
        n = len(poly); nrm = np.zeros_like(poly)
        d = np.roll(poly, -1, 0) - np.roll(poly, 1, 0); nrm[:, 0], nrm[:, 1] = -d[:, 1], d[:, 0]
        nrm /= np.maximum(1e-3, np.linalg.norm(nrm, axis=1, keepdims=True))
        jit = poly + nrm * rng.normal(0, 0.010 * R, (n, 1)).astype(F32)
        cv2.polylines(core, [jit.astype(np.int32)], True, 255, max(1, edge_w - layer), cv2.LINE_AA)
        if R > 140 and vein_u > 0.02:
            sg = veins[i]; sg = sg[(sg[:, 4] <= vein_u) & (sg[:, 5] <= max_gen)]
            if len(sg):
                x0, y0 = to_xy(sg[:, 0], sg[:, 1]); x1, y1 = to_xy(sg[:, 2], sg[:, 3])
                lines = np.stack([x0, y0, x1, y1], 1).reshape(-1, 2, 2).astype(np.int32)
                thick = sg[:, 5] == 0
                if thick.any(): cv2.polylines(core, list(lines[thick]), False, 235, 2 if R > 400 else 1, cv2.LINE_AA)
                if (~thick).any(): cv2.polylines(core, list(lines[~thick]), False, 175, 1, cv2.LINE_AA)
    if not fill_only and R > 60:                                                           # stamens round the heart
        u = clamp(open_u, 0, 1)
        for k in range(8):
            a = rot * 0.5 + k * 2 * math.pi / 8 + 0.2; L_ = R * (0.10 + 0.13 * u)
            x1, y1 = cx + math.cos(a) * L_, cy + math.sin(a) * L_ * squash
            cv2.line(core, (int(cx), int(cy)), (int(x1), int(y1)), 200, 1, cv2.LINE_AA)
            cv2.circle(core, (int(x1), int(y1)), max(2, int(R * 0.012)), 255, -1, cv2.LINE_AA)
    return core, fill

_RG = {}
def radial_q(cx, cy, R):
    """quarter-res falloff exp(-d / R) around (cx, cy), full size."""
    gy, gx = _GY[::4, ::4], _GX[::4, ::4]
    d = np.sqrt((gx - cx) ** 2 + (gy - cy) ** 2)
    return cv2.resize(np.exp(-d / max(1.0, R)).astype(F32), (W, H))

def jas_light(core, fill, cx, cy, R, amt, heart=1.0):
    """the flower as light: a sharp lightning core with a cream glow, translucent glowing petals, the heart."""
    lay = light_rgb(core, amt, JASW, JASG)
    fq = cv2.resize(cv2.GaussianBlur(cv2.resize(fill, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 2), (W, H))
    fq *= 0.20 + 0.55 * radial_q(cx, cy, R * 0.55)
    addc(lay, fq, JASG, 0.42 * amt)
    if heart > 0:
        lay = add_glow(lay, cx, cy, max(20, R * 0.24), 0.75 * amt * heart, JASY)
        lay = add_glow(lay, cx, cy, max(8, R * 0.07), 0.95 * amt * heart, JASW)
    return lay

def behind(lay, person, wrap=0.6):
    """light drawn only behind the subject (rule 1) plus a light wrap on his near edge."""
    if person is None: return lay
    m = np.clip(person * 1.15, 0, 1); o = np.empty(lay.shape, F32)
    for c in range(3): o[..., c] = lay[..., c] * (1 - m)
    if wrap > 0:
        q = cv2.resize(lay.max(2), (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        g = cv2.resize(cv2.GaussianBlur(q, (0, 0), 6), (W, H))
        mq = cv2.resize(m, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        edge = cv2.resize(np.clip(mq - cv2.erode(mq, np.ones((5, 5), np.uint8)), 0, 1), (W, H))
        addc(o, np.clip(g * edge * 2.2, 0, 1.2), JASG, wrap)
    return o

# ---- the camera (v10/v11 beat camera, resting under the set pieces) --------------------------------------------
def beat_phase(f):
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    hook = (E.HDROP + 1 <= e < E.E_LOOP) and not (63 <= e < 70)                         # rests for FULL BLOOM
    rival = 1 <= e < E.HDROP - 2                                                          # soft pulses in the night
    return ph, bi, hook, rival

def beat_bounce(f):
    ph, bi, hook, rival = beat_phase(f)
    if hook: return 1 + 0.050 * math.exp(-ph / 0.10)
    if rival: return 1 + 0.018 * math.exp(-ph / 0.09)
    return 1.0

# ---- titles: NIGHT (grown by lightning) and BLOOM (the O's are jasmine flowers) ---------------------------------
_TX = {}
def title_mask(word, size, track):
    k = (word, size, track)
    if k not in _TX: _TX[k] = text_mask(word, F_BLACK, size, track)
    return _TX[k]

def put_title(out, m, x, y, a, glow=0.6, rise=0.0, blur=0.0, front=None):
    """the v9 construction in the v12 palette: dark keyline, soft shadow, jasmine-white fill, cream glow."""
    if a <= 0.01: return out
    if blur > 0.3: m = cv2.GaussianBlur(m, (0, 0), blur)
    h, w = m.shape; x0, y0 = int(x - w / 2), int(y - h / 2 - rise)
    pad = 40; M = np.pad(m, pad); hh, ww = M.shape
    xa, ya = x0 - pad, y0 - pad
    xb, yb = min(W, xa + ww), min(H, ya + hh); xa_, ya_ = max(0, xa), max(0, ya)
    if xb <= xa_ or yb <= ya_: return out
    sub = M[ya_ - ya:yb - ya, xa_ - xa:xb - xa]
    key = cv2.dilate(sub, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    sh = cv2.GaussianBlur(sub, (0, 0), 14)
    gl = cv2.GaussianBlur(sub, (0, 0), 10)
    o = out[ya_:yb, xa_:xb]
    o *= (1 - 0.55 * sh * a)[..., None]
    o[:] = o * (1 - (key * 0.85 * a)[..., None]) + INK * (key * 0.85 * a)[..., None]
    col = JASW * 0.97
    o[:] = o * (1 - (sub * a)[..., None]) + col * (sub * a)[..., None]
    o += (gl * glow * a)[..., None] * JASG * 0.55
    if front is not None:
        fr = np.pad(front, pad)[ya_ - ya:yb - ya, xa_ - xa:xb - xa]; o += (fr * a)[..., None] * JASW * 0.9
    return out

def text_night(out, f):
    t = f / FPS; t0, t1 = E.th(1), E.th(4.9)
    if not (t0 - 0.05 <= t <= t1 + 0.22): return out
    m = title_mask("NIGHT", 210, 26); h, w = m.shape
    u = clamp((t - t0) / 0.85, 0, 1); outu = clamp((t - t1) / 0.22, 0, 1)
    if "seeds" not in _TX:                                                                   # growth from lightning seeds
        rng = np.random.default_rng(12); sd = np.zeros_like(m, np.uint8)
        for k in range(5):
            cx_ = int(w * (0.1 + 0.2 * k)); ys = np.nonzero(m[:, cx_] > 0.5)[0]
            if len(ys): sd[ys[0], cx_] = 1; sd[ys[-1], min(w - 1, cx_ + 3)] = 1
        _TX["seeds"] = cv2.distanceTransform(1 - sd, cv2.DIST_L2, 5) / max(h, w)
        _TX["noise"] = cv2.GaussianBlur(rng.random(m.shape).astype(F32), (0, 0), 3)
    dist = _TX["seeds"] + _TX["noise"] * 0.06
    R_ = 0.95 * ein(u, 1.3)
    grow = np.clip((R_ - dist) / 0.03, 0, 1) * m
    front = np.clip(1 - np.abs(R_ - dist) / 0.012, 0, 1) * m * (1 - u) * 1.4
    a = (1 - outu) * smooth(u * 3)
    return put_title(out, grow, W / 2, H * 0.60, a, glow=0.9 * (1.2 - u * 0.5), rise=18 * (1 - eout(u)) + 30 * outu, blur=4 * outu, front=front)

def text_bloom(out, f):
    t = f / FPS; t0, t1 = E.th(32.5), E.th(34.95)
    if not (t0 <= t <= t1 + 0.2): return out
    outu = clamp((t - t1) / 0.2, 0, 1); a_all = 1 - outu
    size = 205; cap = int(size * 0.72); letters = "BLOOM"; adv = []
    for ch in letters: adv.append(cap * 1.05 if ch == "O" else title_mask(ch, size, 0).shape[1])
    gap = 26; total = sum(adv) + gap * 4; x = W / 2 - total / 2; y = H * 0.705
    for i, ch in enumerate(letters):
        tl = t - t0 - i * 0.07; u = clamp(tl / 0.42, 0, 1)
        if u <= 0: x += adv[i] + gap; continue
        cxl = x + adv[i] / 2
        if ch == "O":                                                                       # a lightning jasmine for O
            Rf = cap * 0.56 * (0.55 + 0.45 * eout(u, 2)); ou = eout(clamp(tl / 0.55, 0, 1), 2.4) * 1.04
            Rf = cap * 0.34 * (0.55 + 0.45 * eout(u, 2))
            core, fill = jas_draw(cxl, y, Rf, ou, -math.pi / 2 + i * 0.4 + tl * 0.6, f, seed=40 + i, edge_w=2, vein_u=0)
            rr = int(cap * 0.47 * (0.80 + 0.20 * eout(u, 3)))
            ring = np.zeros((2 * cap, 2 * cap), np.uint8); cv2.circle(ring, (cap, cap), rr, 255, int(cap * 0.19), cv2.LINE_AA)
            out = put_title(out, ring.astype(F32) / 255, cxl, y, a_all * smooth(u * 2), glow=0.6, blur=4 * (1 - u) + 4 * outu)
            out = out + jas_light(core, np.zeros_like(fill), cxl, y, Rf, 1.0 * a_all * smooth(u * 2), heart=0.8 * a_all)
        else:
            m = title_mask(ch, size, 0); sc = 0.78 + 0.22 * eout(u, 3)
            mm = cv2.resize(m, (max(1, int(m.shape[1] * sc)), max(1, int(m.shape[0] * sc))), interpolation=cv2.INTER_AREA)
            out = put_title(out, mm, cxl, y, a_all * smooth(u * 1.6), glow=0.8 - 0.4 * u, rise=-22 * (1 - eout(u)), blur=5 * (1 - u) + 4 * outu)
        x += adv[i] + gap
    return np.clip(out, 0, 1)

# ---- transitions ---------------------------------------------------------------------------------------------------
def chest_of(s, f, person=None):
    x, y = subject_point(s, f, person); return x, y

def strike_link(A, B, j, f, sa, sb, pre=6, post=8):
    """the sky's bolt keeps going through the cut and strikes him: the next shot opens along the bolt."""
    x0, y0 = W * 0.62, H * 0.42
    x1, y1 = chest_of(sb, sb["f0"])
    if j < 0:
        u = (j + pre + 1) / pre; cv = bolt_canvas()
        put_bolt(cv, (x0, y0), (x0 + (x1 - x0) * u, y0 + (y1 - y0) * u), 9100 + f // 2, 4, 0.30, 6, 2)
        return np.clip(A * (1 - 0.25 * u) + light_rgb(cv, 1.2, JASW, JASG), 0, 1)
    v = (j + 1) / post; cv = bolt_canvas()
    put_bolt(cv, (x0, -40), (x1, y1), 9200 + f // 2, 5, 0.30, 6, 3)
    for b_ in range(4):                                                                       # branches crack outward
        a_ = -0.9 + 0.6 * b_; put_bolt(cv, (x1, y1), (x1 + math.cos(a_) * 900, y1 + math.sin(a_) * 900 + 300), 9250 + b_, 3, 0.35, 5, 1)
    dist = cv2.distanceTransform(255 - cv, cv2.DIST_L2, 3)
    Rr = 30 + 1500 * eout(v, 1.8); m = np.clip((Rr - dist) / 18.0, 0, 1)
    o = mixm(A * 0.45, B, m)
    rim = np.exp(-((dist - Rr) / 6.0) ** 2) * (1 - v)
    addc(o, rim, JASW, 1.0)
    fl = 0.22 * math.exp(-j / 2.5)                                                        # a flare that keeps the picture
    return np.clip(o * (1 + fl) + light_rgb(cv, 1.3 * (1 - v) ** 0.8, JASW, JASG), 0, 1)

def ecg_trace(u, f, yc, amp):
    """heart-monitor trace from x=0 to x=u*W: flat with beats; returns int32 points."""
    xs = np.linspace(0, W * u, max(2, int(160 * u))); ys = np.full_like(xs, yc)
    for bx in (0.18, 0.48, 0.78):
        k = (xs / W - bx) / 0.02
        ys = ys - amp * (np.exp(-((k - 0.0) ** 2) * 6) - 0.45 * np.exp(-((k - 1.0) ** 2) * 5) + 0.25 * np.exp(-((k + 2.2) ** 2) * 2))
    return np.stack([xs, ys], 1).astype(np.int32)

def ecg_bolt(A, B, j, f, sa, sb, pre=8, post=9):
    """a heart-monitor trace crosses the frame; its beats turn to lightning and the frame tears open along it."""
    yc = H * 0.56; cv = bolt_canvas()
    if j < 0:
        u = (j + pre + 1) / pre
        cv2.polylines(cv, [ecg_trace(u, f, yc, 170)], False, 255, 3, cv2.LINE_AA)
        o = A * (1 - 0.30 * u)
        o = add_glow(o, W * u, ecg_trace(u, f, yc, 170)[-1][1], 40, 0.9, JASW)
        return np.clip(o + light_rgb(cv, 1.0, JASW, JASG), 0, 1)
    v = (j + 1) / post
    pts = ecg_trace(1.0, f, yc, 170 * (1 + 0.6 * v)).astype(F32)
    for k in range(0, len(pts) - 8, 8):                                                   # the trace turns to lightning
        put_bolt(cv, tuple(pts[k]), tuple(pts[k + 8]), 9300 + k + f // 2, 3, 0.35 * v + 0.05, 4, 0)
    band = np.zeros((H, W), F32); cv2.polylines(band, [pts.astype(np.int32)], False, 1.0, 3)
    dist = cv2.distanceTransform((1 - band).astype(np.uint8), cv2.DIST_L2, 3)
    Rr = 6 + 1100 * ein(v, 1.6); m = np.clip((Rr - dist) / 30.0, 0, 1)
    o = mixm(A * 0.6, B, m)
    edge = np.exp(-((dist - Rr) / 10.0) ** 2) * (1 - v)
    addc(o, edge, JASW, 0.9)
    return np.clip(o + light_rgb(cv, 1.1 * (1 - v), JASW, JASG), 0, 1)

def bud_iris(A, B, j, f, sa, sb, pre=6, post=10):
    """a lightning bud turns in the middle of the frame and opens like an iris onto the next shot."""
    cx, cy = W / 2, H * 0.46
    if j < 0:
        u = (j + pre + 1) / pre; R = 60 + 90 * u
        core, fill = jas_draw(cx, cy, R, 0.12 * u, f * 0.05, f, seed=21)
        return np.clip(A * (1 - 0.2 * u) + jas_light(core, fill, cx, cy, R, 1.0, 0.8), 0, 1)
    v = (j + 1) / post; R = 150 + 1500 * ein(v, 1.9)
    core, fill = jas_draw(cx, cy, R, 0.15 + 0.95 * eout(v, 2), f * 0.05, f, seed=21, vein_u=0.4)
    m = np.clip(cv2.GaussianBlur(fill, (0, 0), 3) * 1.4, 0, 1)
    o = mixm(A * (1 - 0.4 * v), B, m)
    return np.clip(o + jas_light(core, np.zeros_like(fill), cx, cy, R, 1.1 * (1 - v) ** 0.7, 0.6 * (1 - v)), 0, 1)

def eye_pos(s, f):
    x, y, _ = to_screen(s, f, 343, 288); return x, y

def bloom(A, B, j, f, sa, sb, pre=10, post=24):
    """THE BLOOM: a bud of lightning forms in his iris and bursts open into a lightning jasmine that fills the frame;
    the next shot is inside the petals; the petals' afterimages keep opening as the title blooms."""
    if j < 0:
        u = (j + pre + 1) / pre; ex, ey = eye_pos(sa, f)
        R = 26 + 150 * ein(u, 1.6)
        core, fill = jas_draw(ex, ey, R, 0.10 * u, f * 0.06, f, seed=33)
        dark = 1 - 0.45 * u * (1 - radial_q(ex, ey, 380))
        o = A * dark[..., None]
        o = o + jas_light(core, fill, ex, ey, R, 1.1 + 0.6 * u, 1.0 + u)
        return np.clip(o, 0, 1)
    ex, ey = eye_pos(sa, sa["f1"] - 1)
    v = (j + 1) / post; vo = clamp((j + 1) / 9, 0, 1)
    cx, cy = ex + (W / 2 - ex) * eout(vo, 2), ey + (H * 0.46 - ey) * eout(vo, 2)
    R = 176 + 1850 * ein(vo, 1.35); ou = 0.10 + 1.0 * eout(vo, 2.6)
    core, fill = jas_draw(cx, cy, R, ou, 0.4 + vo * 0.5, f, seed=33, vein_u=vo, max_gen=1 if R > 700 else 3)
    m = np.clip(cv2.GaussianBlur(fill, (0, 0), 4) * 1.5, 0, 1) if vo < 1 else np.ones((H, W), F32)
    o = mixm(A * (1 - 0.5 * vo), B, m)
    if j >= 6:                                                                               # afterimage petals + ring
        w_ = (j - 6) / (post - 6); R2 = 500 + 1400 * eout(w_, 2)
        c2, _ = jas_draw(W / 2, H * 0.46, R2, 1.0, 0.9 + w_ * 0.4, f, seed=34, vein_u=0)
        o = o + light_rgb(c2, 0.55 * (1 - w_) ** 1.5, JASW, JASG)
        ring = np.zeros((H, W), np.uint8); cv2.circle(ring, (W // 2, int(H * 0.46)), int(140 + 1200 * eout(w_, 2.2)), 255, 4, cv2.LINE_AA)
        o = o + light_rgb(ring, 0.7 * (1 - w_) ** 2, JASW, JASG)
    o = o + jas_light(core, fill * (1 - vo), cx, cy, R, 1.25 * (1 - v) ** 0.7, 1.4 * (1 - vo))
    fl = 0.28 * math.exp(-j / 2.0)
    return np.clip(o * (1 + fl), 0, 1)

def full_bloom_in(A, B, j, f, sa, sb, pre=6, post=6):
    """into the focal shot: the run ends in a radial burst, he is standing still inside a burst of light."""
    if j < 0:
        u = (j + pre + 1) / pre
        o = radial_blur(A, W / 2, H * 0.45, 1.0, 1.0 + 0.10 * u, 5)
        return np.clip(o * (1 + 0.20 * u), 0, 1)
    v = (j + 1) / post
    o = radial_blur(B, W / 2, H * 0.45, 1.0 + 0.08 * (1 - v), 1.0, 5)
    return np.clip(o * (1 + 0.25 * (1 - v) ** 2), 0, 1)

def petal_pass(A, B, j, f, sa, sb, pre=8, post=10):
    """the flower behind him lets go: its petals sweep toward the camera and past it; the next shot is behind them."""
    cx, cy = FB_C
    if j < 0:
        u = (j + pre + 1) / pre; R = FB_R * (1 + 0.6 * ein(u, 2))
        core, fill = jas_draw(cx, cy, R, 1.0 + 0.1 * u, FB_ROT + 0.6 * u, f, seed=55, vein_u=1.0, max_gen=1)
        lay = jas_light(core, fill * 0.3, cx, cy, R, 0.9, 0.5)
        return np.clip(A + behind(lay, PERSON.get(f), 0.6) * (1 - u) + lay * u * 0.6, 0, 1)
    v = (j + 1) / post; R = FB_R * 1.6 * math.exp(3.2 * ein(v, 1.6))
    core, fill = jas_draw(cx + (W / 2 - cx) * v, cy + (H / 2 - cy) * v, R, 1.1, FB_ROT + 0.6 + 1.2 * v, f, seed=55, vein_u=1.0, max_gen=1)
    m = np.clip(cv2.GaussianBlur(fill, (0, 0), 6) * 1.2, 0, 1)
    o = mixm(B, A * 0.35, m * (1 - v) ** 0.6)                                              # petals pass as dark glass
    return np.clip(o + light_rgb(core, 1.1 * (1 - v) ** 0.6, JASW, JASG), 0, 1)

_PB = {}
def pollen_burst(A, B, j, f, sa, sb, pre=6, post=8):
    """the frame breaks into drifting pollen of light that blows past and settles into the next shot."""
    if "p" not in _PB:
        rng = np.random.default_rng(71); n = 1600
        _PB["p"] = (rng.uniform(0, W, n), rng.uniform(0, H, n), rng.uniform(0.4, 1.0, n), rng.uniform(0, 6.28, n))
    px, py, z, ph = _PB["p"]; u = (j + pre + 1) / (pre + post)
    dx = (px - W / 2) * (0.9 * ein(u, 1.4)) * z + 60 * np.sin(ph + u * 6) * u
    dy = (py - H / 2) * (0.9 * ein(u, 1.4)) * z - 220 * u * z
    src = A if j < 0 else B
    lay = np.zeros((H // 2, W // 2), F32)
    xs = ((px + dx) / 2).astype(np.int32); ys = ((py + dy) / 2).astype(np.int32)
    ok = (xs >= 0) & (xs < W // 2) & (ys >= 0) & (ys < H // 2)
    for sh_ in (sa, sb):
        bx = face_box(sh_, f)
        if bx is not None: ok &= ~((xs * 2 > bx[0] - 40) & (xs * 2 < bx[1] + 40) & (ys * 2 < bx[2] + 40))
    for x_, y_, z_ in zip(xs[ok], ys[ok], z[ok]): cv2.circle(lay, (int(x_), int(y_)), 1 + int(2 * z_), float(z_), -1, cv2.LINE_AA)
    lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 0.8), (W, H)) * math.sin(math.pi * u)
    mix_ = smooth((j + pre * 0.5) / (pre * 0.5 + post * 0.7))
    base = A * (1 - mix_) + B * mix_
    o = base * (1 - 0.25 * math.sin(math.pi * u))
    return np.clip(addc(o, lay, JASG, 0.9), 0, 1)

def petal_whip(A, B, j, f, sa, sb, pre=5, post=6):
    o = _whip_lib(A, B, j, f, sa, sb)
    u = (j + pre + 1) / (pre + post); cv = bolt_canvas()
    for k in range(3):                                                                    # curved petal-shaped light arcs
        c = (int(W * (0.5 + 0.9 * (u - 0.5) * (1 + k * 0.3))), int(H * (0.30 + 0.20 * k)))
        cv2.ellipse(cv, c, (int(260 + 60 * k), int(70 + 20 * k)), -18 + k * 12, 200, 340, 255, 3, cv2.LINE_AA)
    return np.clip(o + light_rgb(cv, 0.9 * math.sin(math.pi * u), JASW, JASG), 0, 1)

_whip_lib = TR2["whip"][0]
TR2.update({"strike_link": (strike_link, 6, 8), "ecg_bolt": (ecg_bolt, 8, 9), "bud_iris": (bud_iris, 6, 10),
            "bloom": (bloom, 10, 24), "full_bloom": (full_bloom_in, 6, 6), "petal_pass": (petal_pass, 8, 10),
            "pollen_burst": (pollen_burst, 6, 8), "petal_whip": (petal_whip, 5, 6)})

# ---- rev 3: EMBLEM BLOOM and FRACTAL BURN ------------------------------------------------------------------------
_EMB = {}
def emblem_at(s, f):
    """his chest emblem on screen (x, y, r): a Hough circle on the source frame, mapped through the shot's camera."""
    key = (s["n"], f)
    if key in _EMB: return _EMB[key]
    t, u, _ = src_time(s, f); img = sample(s["src"], t)
    if img.dtype != np.uint8: img = np.clip(img * (255 if img.max() <= 1.5 else 1), 0, 255).astype(np.uint8)
    g = cv2.medianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 5); y0 = img.shape[0] // 3
    cs = cv2.HoughCircles(g[y0:], cv2.HOUGH_GRADIENT, 1.2, 80, param1=120, param2=40, minRadius=40, maxRadius=150)
    if cs is None: x, y = chest_of(s, f); res = (x, y, 150.0)
    else:
        cx, cy, r = cs[0][0]; X, Y, sc = to_screen(s, f, float(cx), float(cy) + y0); res = (X, Y, float(r) * sc)
    if len(_EMB) > 64: _EMB.clear()
    _EMB[key] = res; return res

def crack_canvas(cx, cy, r, u, f, n=5, rot=-math.pi / 2):
    cv = bolt_canvas()
    for k in range(n):
        a = rot + k * 2 * math.pi / n
        put_bolt(cv, (cx, cy), (cx + math.cos(a) * r * u, cy + math.sin(a) * r * u), 9700 + k + 7 * (f // 2), 2, 0.30, 4, 0)
    return cv

def emblem_bloom(A, B, j, f, sa, sb, pre=12, post=16):
    """EMBLEM BLOOM: the camera pushes onto his chest emblem, its rim lights, lightning cracks it into five petals; the
    petals peel open outward like a flower and the next shot is inside the emblem as we fly through it."""
    if j < 0:
        u = (j + pre + 1) / pre; ex, ey, er = emblem_at(sa, f)
        Z = 1 + 0.55 * ein(u, 2.2); o = zoom_about(A, ex, ey, Z)
        R = er * Z; ring = np.zeros((H, W), np.uint8); cv2.circle(ring, (int(ex), int(ey)), int(R), 255, 3, cv2.LINE_AA)
        lay = light_rgb(ring, 0.5 + 0.8 * u, JASW, JASG) + light_rgb(crack_canvas(ex, ey, R, ein(u, 1.5), f), 1.1 * u, JASW, JASG)
        return np.clip(o + lay, 0, 1)
    v = (j + 1) / post; ex, ey, er = emblem_at(sa, sa["f1"] - 1)
    Z0 = 1.55; Z = Z0 * math.exp(3.0 * ein(v, 1.6))
    px, py = ex + (W / 2 - ex) * smooth(v), ey + (H * 0.47 - ey) * smooth(v)
    outer = zoom_about(A, ex, ey, Z)
    M = np.float32([[1, 0, px - ex], [0, 1, py - ey]]); outer = cv2.warpAffine(outer, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    sb_ = 1.0 + 0.35 * (1 - eout(v, 2)); inner = zoom_about(B, W / 2, H * 0.47, sb_)
    R = er * Z0 * (1 + 2.2 * ein(v, 1.4)) * (1 + 0.15 * eout(v))                            # the opening widens
    hole = np.zeros((H, W), F32); cv2.circle(hole, (int(px), int(py)), int(R), 1.0, -1, cv2.LINE_AA)
    o = mixm(outer, inner, cv2.GaussianBlur(hole, (0, 0), 2))
    Rd = er * Z0                                                                              # the five petals of the disc
    disc = np.zeros((H, W), F32); cv2.circle(disc, (int(ex), int(ey)), int(Rd), 1.0, -1, cv2.LINE_AA)
    A0 = zoom_about(A, ex, ey, Z0); cv = bolt_canvas()
    for k in range(5):
        a0 = -math.pi / 2 + k * 2 * math.pi / 5; a1 = a0 + 2 * math.pi / 5; am = (a0 + a1) / 2
        wedge = np.zeros((H, W), F32)
        pts = [(ex, ey)] + [(ex + math.cos(a) * Rd * 1.02, ey + math.sin(a) * Rd * 1.02) for a in np.linspace(a0, a1, 12)]
        cv2.fillPoly(wedge, [np.array(pts, np.int32)], 1.0, cv2.LINE_AA); wedge *= disc
        d = R * 0.85 * eout(v, 1.6); rot = (25 if k % 2 else -25) * v; sc = 1 + 0.6 * v
        Mw = cv2.getRotationMatrix2D((ex, ey), rot, sc); Mw[0, 2] += math.cos(am) * d + (px - ex); Mw[1, 2] += math.sin(am) * d + (py - ey)
        wa = cv2.warpAffine(wedge, Mw, (W, H)) * (1 - v) ** 0.7
        tex = cv2.warpAffine(A0, Mw, (W, H), borderMode=cv2.BORDER_REFLECT)
        o = mixm(o, tex * (1 - 0.35 * v), wa)
        edge = cv2.morphologyEx((wa > 0.3).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
        cv = np.maximum(cv, edge * 255)
    lay = light_rgb(cv, 1.2 * (1 - v) ** 0.6, JASW, JASG)
    rim = np.zeros((H, W), np.uint8); cv2.circle(rim, (int(px), int(py)), int(R), 255, 3, cv2.LINE_AA)
    lay += light_rgb(rim, 0.9 * (1 - v), JASW, JASG)
    return np.clip(o + lay, 0, 1)

_FBN = {}
def fractal_burn(A, B, j, f, sa, sb, pre=8, post=18):
    """FRACTAL BURN: lightning burns a Lichtenberg figure into the frame (as it burns into wood): two discharges crawl in
    from the edges, embers glowing along the branches, the picture chars around them and burns through to the next shot."""
    if "t" not in _FBN:
        t1 = lich_tree(-20, H * 0.58, None, seed=41); t2 = lich_tree(W + 20, H * 0.40, None, seed=43)
        segs = np.concatenate([t1, t2]); _FBN["t"] = segs
        _FBN["n"] = cv2.resize(np.random.default_rng(5).random((H // 16, W // 16)).astype(F32), (W, H), interpolation=cv2.INTER_CUBIC)
    segs = _FBN["t"]; u = (j + pre + 1) / (pre + post)
    tau = 1.15 * ein(u, 1.25)
    vis = segs[segs[:, 4] <= tau]; cv = np.zeros((H, W), np.uint8)
    if len(vis):
        for wd in (4, 3, 2, 1):
            sel = vis[np.abs(vis[:, 5] - wd) < 0.75] if wd > 1 else vis[vis[:, 5] < 1.75]
            if len(sel): cv2.polylines(cv, list(sel[:, :4].reshape(-1, 2, 2).astype(np.int32)), False, 255, max(1, wd), cv2.LINE_AA)
    dist = cv2.distanceTransform(255 - cv, cv2.DIST_L2, 3) + _FBN["n"] * 18
    burn = max(0.0, (u - 0.22) / 0.78)
    rh = 2 + 820 * ein(burn, 2.3); rc = rh + 12 + 30 * (1 - burn)                           # the hole and its char ring
    hole = np.clip((rh - dist) / 5.0, 0, 1) if burn > 0 else np.zeros((H, W), F32)
    char = np.clip((rc - dist) / (rc - rh + 1e-3), 0, 1) * (1 - hole)
    src = A if j < 0 else A
    o = src * (1 - 0.72 * char)[..., None]
    o[..., 2] += char * 0.035; o[..., 1] += char * 0.012                                     # scorched brown
    o = mixm(o, B, hole)
    front = np.exp(-((dist - rh) / 4.0) ** 2) * (burn > 0) * (1 - 0.6 * burn)
    EMB_ = np.array([0.10, 0.48, 1.00], F32)
    addc(o, front, EMB_, 1.1); addc(o, front, JASW, 0.4)
    o = o + light_rgb(cv, 0.9 * (1 - burn) ** 2.6, JASW, JASG)
    return np.clip(o, 0, 1)

TR2.update({"emblem_bloom": (emblem_bloom, 12, 16), "fractal_burn": (fractal_burn, 8, 18)})

# ---- beat moments (one per "just moving" shot, each with its own sound) ---------------------------------------
def beat_age(f):
    e = f / FPS / E.HB; return (e % 2) * E.HB, int(e // 2)

def pollen_fx(out, s, f, person, amt):
    """POLLEN: on every beat a burst of light motes leaves his emblem along five petal paths, behind him."""
    ph, bi = beat_age(f); cx, cy = chest_of(s, f, person); lay = np.zeros((H // 2, W // 2), F32)
    for age, a0 in ((ph, 1.0), (ph + 2 * E.HB, 0.5)):
        if age > 0.9: continue
        for k in range(5):
            th = bi * 0.7 + k * 2 * math.pi / 5
            for m_ in range(14):
                r = (120 + 520 * eout(age / 0.9, 2)) * (0.45 + m_ / 24); a = th + 0.35 * math.sin(m_ * 0.9 + age * 4)
                x, y = (cx + math.cos(a) * r) / 2, (cy + math.sin(a) * r * 0.9 - 60 * age) / 2
                cv2.circle(lay, (int(x), int(y)), 1 + (m_ % 3 == 0), a0 * (1 - age / 0.9), -1, cv2.LINE_AA)
    lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 0.7), (W, H))
    l3 = np.zeros(out.shape, F32); addc(l3, lay, JASW, 1.1 * amt)
    l3 = add_glow(l3, cx, cy, 110, 0.35 * amt * math.exp(-ph / 0.15), JASY)
    return np.clip(out + behind(l3, person, 0.4), 0, 1)

def bokeh_stars(out, s, f, person, amt):
    """the street lights behind him bloom into five-point stars on the beat."""
    ph, bi = beat_age(f); pulse = math.exp(-ph / 0.18)
    q = cv2.resize(lum8(out), (W // 8, H // 8), interpolation=cv2.INTER_AREA)
    if person is not None: q = q * (1 - cv2.resize(np.clip(person * 1.3, 0, 1), (W // 8, H // 8)))
    pts = np.argwhere((q > 0.42) & (q == cv2.dilate(q, np.ones((7, 7), np.uint8))))[:10]
    cv = bolt_canvas()
    for (y, x) in pts:
        X, Y = x * 8 + 4, y * 8 + 4; Rr = 26 + 34 * pulse
        for k in range(5):
            a = -math.pi / 2 + k * 2 * math.pi / 5 + bi * 0.3
            cv2.line(cv, (X, Y), (int(X + math.cos(a) * Rr), int(Y + math.sin(a) * Rr)), 255, 2, cv2.LINE_AA)
    return np.clip(out + behind(light_rgb(cv, (0.35 + 0.65 * pulse) * amt, JASW, JASG), person, 0.0), 0, 1)

def bud_fx(out, s, f, person, amt):
    """BUD: a small lightning jasmine on his emblem opens a little on every beat and closes again."""
    ph, bi = beat_age(f); cx, cy = chest_of(s, f, person)
    ou = 0.22 + 0.45 * math.exp(-ph / 0.16); R = 70 + 50 * math.exp(-ph / 0.2)
    core, fill = jas_draw(cx, cy, R, ou, bi * 0.5 + f * 0.02, f, seed=88)
    return np.clip(out + jas_light(core, fill, cx, cy, R, 0.95 * amt, 0.9 * amt), 0, 1)

def storm_fx(img, s, f):
    """the sky shot: its own bolt pulled out of the clouds and lit in jasmine white; the clouds flicker on the kicks."""
    L = lum8(img); hp = np.clip((L - cv2.GaussianBlur(L, (0, 0), 7)) * 6.0 - 0.15, 0, 1) * np.clip((L - 0.22) * 4, 0, 1)
    cv = (np.clip(hp, 0, 1) * 255).astype(np.uint8)
    ph, bi = beat_age(f); fl = 0.10 * math.exp(-ph / 0.07) if bi % 2 == 0 else 0.0
    o = img * (1 + fl) + light_rgb(cv, 1.25, JASW, JASG)
    return np.clip(o, 0, 1)

def face_guard(orig, fx, s, f):
    """beat moments never touch his face: inside the tracked face ellipse (feathered) the shot keeps its own picture."""
    fs = face_scr(s, f) if s.get("face") is not None else None
    if not fs: return fx
    m = np.zeros((H // 4, W // 4), F32)
    cv2.ellipse(m, (int(fs[0] / 4), int(fs[1] / 4 + fs[2] * 0.02)), (int(fs[2] * 0.66 / 4), int(fs[2] * 0.92 / 4)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    m = cv2.resize(cv2.GaussianBlur(m, (0, 0), 4), (W, H))
    return mixm(fx, orig, m)

def base12(s, f):
    img, person = base11(s, f)
    if s["n"] == "sky": img = storm_fx(img, s, f)
    orig = img
    if s.get("pollen"): img = pollen_fx(img, s, f, person, s["pollen"])
    if s.get("stars"): img = bokeh_stars(img, s, f, person, s["stars"])
    if s.get("bud"): img = bud_fx(img, s, f, person, s["bud"])
    if s.get("echo"): img = time_remnants(img, s, f, person, s["echo"] * 0.8)
    if s.get("ring"): img = aura_pulse(img, s, f, person, s["ring"])
    if img is not orig and not s.get("bud"): img = face_guard(orig, img, s, f)
    if s["n"] == "full": img = full_bloom_fx(img, s, f, person)
    if s["n"] == "last": img = close_bud_fx(img, s, f, person)
    return img, person

# ---- FULL BLOOM (focal set piece, e64, the claps enter) ---------------------------------------------------------
FB_C = (W / 2, H * 0.31); FB_R = 660.0; FB_ROT = -math.pi / 2
def full_bloom_fx(out, s, f, person):
    """a seed of light rises behind him, a giant lightning jasmine unfolds behind him (masked, light wrap), its veins
    crawl out, it breathes on the claps; the scene darkens round it so the flower lights him."""
    k = f - s["f0"]; n = s["f1"] - s["f0"]; t = f / FPS
    cx, cy = FB_C
    if k < 14:                                                                               # a bolt rises behind him
        u = k / 14; cv = bolt_canvas()
        put_bolt(cv, (W * 0.46, -40), (W * 0.46 + (cx - W * 0.46) * eout(u, 2), -40 + (cy + 40) * eout(u, 2)), 9500 + f // 2, 4, 0.28, 6, 2)
        lay = light_rgb(cv, 1.2, JASW, JASG); lay = add_glow(lay, cx, cy, 120 * u, 0.9 * u, JASY)
        return np.clip(out * (1 - 0.25 * u) + behind(lay, person, 0.5), 0, 1)
    u = clamp((k - 14) / 36, 0, 1)
    clap = 0.0
    for ce in (E.HDROP + 35, E.HDROP + 39):                                                 # the claps (bar 16, j3 / j7)
        dk = t - E.th(ce)
        if 0 <= dk < 0.4: clap = max(clap, math.exp(-dk / 0.12))
    R = FB_R * (0.25 + 0.75 * eout(u, 2.2)) * (1 + 0.04 * clap)
    ou = 1.06 * eout(u, 2.4)
    core, fill = jas_draw(cx, cy, R, ou, FB_ROT + 0.10 * (k / n), f, seed=55, vein_u=clamp(u * 1.3, 0, 1), edge_w=3, max_gen=0)
    lay = jas_light(core, fill, cx, cy, R, 1.0 + 0.4 * clap, 1.0 + 0.5 * clap)
    fq = cv2.resize(cv2.GaussianBlur(cv2.resize(fill, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 3), (W, H))
    addc(lay, fq, JASG, 0.38 * (0.7 + 0.3 * clap))                                           # the petals glow as surfaces
    rays = radial_q(cx, cy, 650) * (0.25 + 0.2 * clap)                                       # its light fills the night
    addc(lay, rays, JASG, 0.6 * u)
    o = out * (1 - 0.30 * u)
    return np.clip(o + behind(lay, person, 0.8), 0, 1)

# ---- the loop: the bud closes on his emblem, the camera dives into it, inside is frame 0 -----------------------
_Z0 = {}
def frame0_prefinish():
    if "z" not in _Z0: _Z0["z"] = prefinish(0)
    return _Z0["z"]

def close_bud_fx(out, s, f, person):
    k = f - s["f0"]; n = s["f1"] - s["f0"]; cx, cy = chest_of(s, f, person)
    if k < 46:
        u = k / 46; ou = 0.28 * math.sin(math.pi * clamp(u * 1.3, 0, 1)) + 0.05
        R = 80 + 60 * u
        core, fill = jas_draw(cx, cy, R, ou, f * 0.03, f, seed=91)
        cv = bolt_canvas()
        for i in range(2): put_bolt(cv, (cx + (-1) ** i * 140, cy + 60), (cx, cy), 9600 + i + f // 2, 2, 0.35, 5, 0)
        return np.clip(out + jas_light(core, fill, cx, cy, R, 1.0, 0.9 + u) + light_rgb(cv, 0.7 * u, JASW, JASG), 0, 1)
    return out                                                                               # the dive is drawn in render()

def loop_dive(out, f, s):
    """frames k >= 46 of the last shot: anticipation pull-back, then an accelerating dive into the closed bud; its
    opening shows frame 0 (pre-finish), which fills the frame at scale 1.0 on the last frame."""
    k = f - s["f0"]; n = s["f1"] - s["f0"]
    if k < 46: return out
    bx, by = LOOP_C.get("c") or chest_of(s, s["f0"] + 45)
    LOOP_C["c"] = (bx, by)
    u = (k - 46) / (n - 1 - 46)                                                              # 0..1, 1 = last frame
    if u < 0.18: z = 1 - 0.05 * smooth(u / 0.18)                                            # pull back
    else: z = 0.95 * math.exp(math.log(30 / 0.95) * ein((u - 0.18) / 0.82, 1.8))
    w = smooth(u)                                                                             # the zoom centre drifts to the middle
    px, py = bx + (W / 2 - bx) * w, by + (H / 2 - by) * w
    o = zoom_about(out, bx, by, z) if z != 1 else out.copy()
    o = radial_blur(o, W / 2, H / 2, 1.0, 1.0 + 0.10 * ein(u, 1.5), 5) if u > 0.3 else o
    Rb = 140 * z                                                                             # the bud on screen
    core, fill = jas_draw(px, py, Rb, 0.06 + 0.3 * u, f * 0.03 + 2 * u, f, seed=91, vein_u=0.3)
    ap = np.zeros((H, W), F32); cv2.circle(ap, (int(px), int(py)), int(max(1, Rb * 0.32)), 1.0, -1, cv2.LINE_AA)
    ap = np.clip(cv2.GaussianBlur(ap, (0, 0), 3 + 10 * u), 0, 1) if u < 1 else np.ones((H, W), F32)
    Z0 = frame0_prefinish()
    if u >= 1: return Z0.copy()
    sc = z / 30.0                                                                            # the inside reaches 1.0 at the end
    M = np.float32([[sc, 0, px - sc * W / 2], [0, sc, py - sc * H / 2]])
    inner = cv2.warpAffine(Z0, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    o = mixm(o, inner, ap)
    return np.clip(o + jas_light(core, fill * (1 - ap) * 0.5, px, py, Rb, 1.2 * (1 - u ** 3), 1.2 * (1 - u)), 0, 1)
LOOP_C = {}

def loop_in12(out, f, k):
    """the first frames after the wrap: the last petals of the bud fly off the sky and fade (zero at frame 0)."""
    if k <= 0 or k > 16: return out
    u = k / 16; R = 900 + 900 * eout(u, 2)
    core, _ = jas_draw(W / 2, H / 2, R, 1.1, 1.0 + u, f, seed=91, vein_u=0)
    return np.clip(out + light_rgb(core, 0.5 * math.sin(math.pi * u) * (1 - u), JASW, JASG), 0, 1)

# ---- the frame ----------------------------------------------------------------------------------------------------
_B12 = {}
PERSON = {}
def edge12(S_, which):
    key = (S_["n"], which)
    if key not in _B12:
        if len(_B12) > 6: _B12.clear()
        _B12[key] = base12(S_, S_["f0"] if which == "first" else S_["f1"] - 1)[0]
    return _B12[key]

def prefinish(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base12(s, f)
    PERSON.clear(); PERSON[f] = person
    if tin == "loop_in": out = loop_in12(out, f, k)
    elif tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge12(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge12(n_, "first"), kn, f, s, n_)
    if s["n"] == "last": out = loop_dive(out, f, s)
    out = beat_fx(out, f)
    return np.clip(out, 0, 1)

FLASH_CAP = 0.40
def flash_governor(out):
    """flash discipline: a flare keeps the picture. Frames brighter than mean luma 0.40 are scaled down toward it
    (only flash frames reach it; every other frame is untouched)."""
    q = cv2.resize(out, (W // 8, H // 8), interpolation=cv2.INTER_AREA); m = float(lum8(q).mean())
    return out if m <= FLASH_CAP else out * (FLASH_CAP / m) ** 0.9

def render(f):
    s = shot_at(f); out = flash_governor(prefinish(f))
    fin_s = SHOTS[0] if (s["n"] == "last" and f - s["f0"] >= 46) else s
    return (np.clip(finish12(out, f, fin_s), 0, 1) * 255 + 0.5).astype(np.uint8)

# ============================================================================ v107 ALL CAPS (Dexter x Madvillain "All Caps")
# The edit's own section (above the pipeline v2 speed section). Last definition wins.
#   LOOK      TABLOID: newsprint cream highlights, ink blacks, slate blues, one spot red; a misregistered red plate,
#             paper grain and a fine screen in the shadows (finish107).
#   PRINT     halftone(): the press screen. The press flash prints the next shot as a newspaper photo; the front page's
#             photo is the next shot, and the dive resolves its dots into the footage.
#   molasses  "flows of hot molasses": a viscous sheet of blood pours down the lens (fingering front, a bead on its
#             edge, refraction, absorption, a glossy highlight), the next shot is under it, it drains with streaks.
#   headspin  "to headspin": the frame spins two turns about its centre (motion-blurred) onto the upside-down shot.
#   frontpage "took a few minutes to convince": the front page spins in (BAY HARBOR / BUTCHER), lands, and we dive into
#             its photo of him (the next shot).
#   stamp     "when you spell the man name": a strip of newsprint slaps on; D-E-X-T-E-R is stamped one letter per sung
#             word; the strip flies into the sky onto the real banner the plane tows (WE <3 DEXTER).
#   confetti  procedural paper confetti (lit, fluttering, depth of field): the pop into the parade and the loop
#             (it thickens over the lens on the bass drop-out bar and clears on frame 0).
INK = np.array([0.045, 0.040, 0.040], np.float32)       # BGR ink black
PAPER = np.array([0.84, 0.92, 0.96], np.float32)        # BGR newsprint cream
SPOT = np.array([0.13, 0.12, 0.80], np.float32)         # BGR spot red
SLATE = np.array([0.50, 0.42, 0.34], np.float32)        # BGR slate blue
BLOODC = np.array([0.03, 0.02, 0.30], np.float32)       # BGR deep blood body
EMPH = np.array([0.16, 0.16, 0.92], np.float32)         # caption emphasis: the spot red (cap_word reads EMPH)

# ---- the grade: TABLOID -------------------------------------------------------------------------------------------
_LUTT = {}
def lutt():
    if "t" not in _LUTT:
        x = np.linspace(0, 1, 1024, dtype=np.float32)
        _LUTT["t"] = (x, PchipInterpolator([0, .05, .18, .50, .80, .94, 1], [0.030, 0.040, 0.135, 0.47, 0.80, 0.915, 0.94])(x).astype(np.float32))
    return _LUTT["t"]

_grade_pre107 = grade
def grade(img, s, f):
    if s.get("look") != "tabloid": return _grade_pre107(img, s, f)
    g, gains = corr9(s); ev = s.get("ev") or 0; lx, ly = lutt()
    if in_unit(img):
        x = apply_lut3(img, tone_lut(("tab107", s["n"], ev, float(g), tuple(float(v) for v in gains)), gains, g, ev, lx, ly))
    else:
        x = np.interp(np.clip(np.clip(img * gains, 0, 1) ** g * 2 ** ev, 0, 1), lx, ly).astype(np.float32)
    Bc, Gc, Rc = (np.ascontiguousarray(x[..., c]) for c in range(3))
    L = Bc * 0.114 + Gc * 0.587 + Rc * 0.299
    red = np.clip((Rc - np.maximum(Gc, Bc) - s.get("redthr", 0.12)) * 3.2, 0, 1)          # strong reds survive as the spot colour
    skin = np.clip((Rc - Bc) * 2.2, 0, 1) * (1 - red)
    sat = 0.30 + 0.20 * skin + 0.85 * red
    hi = np.clip((L - 0.45) * 1.8, 0, 1)
    o = np.empty(x.shape, np.float32)
    for ch, P in enumerate((Bc, Gc, Rc)):
        v = L + (P - L) * sat
        v *= 1 + hi * (PAPER[ch] / 0.96 - 1) * 0.9                                         # paper cream in the light
        v += (1 - L) ** 3 * (0.012 if ch == 0 else 0.0)                                    # ink, a hair cool in the deepest black
        v += red * L * (SPOT[ch] / 0.80 - 1) * 0.25                                        # reds lean to the printing red
        o[..., ch] = v
    return np.clip(o, 0, 1, out=o)

# ---- the print: halftone screen ------------------------------------------------------------------------------------
_HT = {}
def ht_grid(pitch, ang):
    key = (round(pitch, 2), ang)
    if key not in _HT:
        if len(_HT) > 10: _HT.clear()
        a = math.radians(ang); u = (_GX * math.cos(a) + _GY * math.sin(a)) / pitch; v = (-_GX * math.sin(a) + _GY * math.cos(a)) / pitch
        du, dv = u - np.round(u), v - np.round(v); _HT[key] = np.sqrt(du * du + dv * dv).astype(np.float32)
    return _HT[key]

def halftone(img, pitch=9.0, ang=45, red_plate=True):
    """the image as a newspaper print: ink dots on newsprint (size by darkness, sampled per cell), reds on their own
    screen at 75 degrees."""
    r = ht_grid(pitch, ang); sm = cv2.GaussianBlur(img, (0, 0), pitch * 0.45)
    Lb = lum(sm); d = np.clip((1 - Lb) * 1.08 - 0.04, 0, 1)
    R = np.sqrt(d / math.pi) * 1.02; aa = 1.2 / pitch
    dot = np.clip((R - r) / aa + 0.5, 0, 1)
    o = PAPER * (1 - dot[..., None]) + INK * dot[..., None]
    if red_plate:
        red = np.clip((sm[..., 2] - np.maximum(sm[..., 0], sm[..., 1]) - 0.05) * 2.5, 0, 1)
        r2 = ht_grid(pitch, 75); dr = np.clip((np.sqrt(red / math.pi) * 1.02 - r2) / aa + 0.5, 0, 1) * (1 - dot)
        o = o * (1 - dr[..., None]) + SPOT * dr[..., None]
    return o.astype(np.float32)

# ---- the finish: misregistered red plate, paper grain, a fine screen in the shadows, vignette ------------------------
_PAPERTEX = {}
def paper_tex():
    if "p" not in _PAPERTEX:
        rng = np.random.default_rng(1070)
        fib = cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), 0.8)
        fib = fib + cv2.resize(cv2.GaussianBlur(rng.standard_normal((H // 6, W // 6)).astype(np.float32), (0, 0), 1.2), (W, H)) * 0.8
        fib = cv2.GaussianBlur(fib, (0, 0), sigmaX=2.2, sigmaY=0.6)                        # fibres run one way
        _PAPERTEX["p"] = (fib / (np.abs(fib).max() + 1e-6)).astype(np.float32)
    return _PAPERTEX["p"]

def finish107(out, f, s=None):
    Bc, Gc, Rc = out[..., 0], out[..., 1], out[..., 2]
    red = np.clip((Rc - np.maximum(Gc, Bc) - 0.06) * 2.0, 0, 1)
    ghost = np.roll(np.roll(red, 3, 1), 2, 0) * (1 - red) * 0.22                           # the red plate sits a few px off
    L = lum(out); scr = ht_grid(6.0, 45)
    dots = np.clip(1 - scr * 2.4, 0, 1) * np.clip((0.55 - L) * 1.6, 0, 1) * 0.07           # a fine screen in the shadows only
    pt = paper_tex(); g = grain(f, 0.011)[..., 0]; v = VIG[..., 0]
    o = np.empty(out.shape, np.float32)
    for ch in range(3):
        oc = o[..., ch]; np.copyto(oc, out[..., ch])
        oc += ghost * (SPOT[ch] - 0.55) * 0.6
        oc *= (1 - dots); oc *= (1 + pt * 0.022); oc *= v; oc += g
    return np.clip(o, 0, 1, out=o)

# ---- the beat camera: from e2 (frame 0 clean) to the loop; it rests through the spins, the front page and the match ---
def beat_phase(f):
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    hook = (E.E_BEAT <= e < E.E_LOOP - 1) and not (19 <= e < 23) and not (24 <= e < 28.5) and not (47 <= e < 50)
    return ph, bi, hook, False

# ---- smooth motion: where flow is refused (big frame-to-frame change), blend the two frames instead of holding one ----
def src_weights(s, f):
    """as the engine's, but a flow shot whose neighbours differ too much for clean flow blends them (motion-blur-like at
    60 fps) instead of holding one (24p judder). check_sources keeps every range inside one source shot."""
    pk = s["src"]; fps = E.SRC[pk][1]; U = UNIQ[pk]
    t, u, sp = src_time(s, f)
    def idx(tt, mode):
        kf = tt * fps; i = clamp(bisect.bisect_right(U, kf + 0.3) - 1, 0, len(U) - 1)
        if mode == "hold" or i >= len(U) - 1: return [(U[i], 1.0)]
        i0, i1 = U[i], U[i + 1]; a = clamp((kf - i0) / (i1 - i0), 0.0, 1.0)
        if a < 0.05: return [(i0, 1.0)]
        if a > 0.95: return [(i1, 1.0)]
        if mode == "blend": return [(i0, 1 - a), (i1, a)]
        A0, A1 = FR[(pk, i0)], FR[(pk, i1)]
        if np.abs(A0[::8, ::8].astype(np.float32) - A1[::8, ::8]).mean() > 14: return [(i0, 1 - a), (i1, a)]
        m0, m1 = A0[::8, ::8].mean(axis=(0, 1)), A1[::8, ::8].mean(axis=(0, 1))
        if np.abs(m0.astype(np.float32) - m1).max() > 6: return [(i0, 1 - a), (i1, a)]
        return [("flow", i0, i1, a)]
    if sp > 1.7:
        K = int(min(7, max(3, round(sp * 2)))); span = 0.5 / FPS * sp; out_ = []
        for j in range(K):
            out_ += [(k, w / K) for k, w in idx(t + (j / (K - 1) - 0.5) * span, "hold")]
        return out_, t, u
    return idx(t, s.get("interp", "hold")), t, u

# ---- base frame ---------------------------------------------------------------------------------------------------
def banner_geom(t):
    """the banner shot: the source cropped round the banner (tracked as it drifts left and up), scaled 1.2x so the whole
    banner fits the width; the sky is extended above and below."""
    x0 = 260.0 - 86.7 * (t - 326.05); y0 = -20.0 * (t - 326.05)
    return x0, y0, 1.2, 545.0

def banner_frame(s, f):
    t, u, _ = src_time(s, f); fr = sample(s["src"], t)
    img = fr.astype(np.float32) / 255 if fr.dtype != np.float32 else fr
    x0, y0, sc, yoff = banner_geom(t)
    M = np.float32([[sc, 0, -x0 * sc], [0, sc, yoff - y0 * sc]])
    o = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
    top, bot = img[4:60].reshape(-1, 3).mean(0), img[-60:-4].reshape(-1, 3).mean(0)          # extend the sky: its own top/bottom colour
    yy = (_GY[:, :1] - yoff) / (720 * sc)
    sky = np.where(yy < 0, top + (top - bot) * np.clip(-yy, 0, 1) * 0.15, bot - (top - bot) * np.clip(yy - 1, 0, 1) * 0.15).astype(np.float32)
    out_m = np.clip(np.maximum(-yy * 720 * sc, (yy - 1) * 720 * sc) / 40 + 0.5, 0, 1)        # 1 outside the source rows (soft edge)
    o = o * (1 - out_m[..., None]) + sky[:, None, :] * out_m[..., None]
    return np.clip(grade(np.clip(o, 0, 1), s, f), 0, 1)

def base107(s, f):
    if s.get("banner"): return banner_frame(s, f), None
    img, person = base12(s, f)
    if s.get("pop"): img = pop_behind(img, s, f, person)
    return img, person

_B107 = {}
def edge107(S_, which):
    key = (S_["n"], which)
    if key not in _B107:
        if len(_B107) > 6: _B107.clear()
        _B107[key] = base107(S_, S_["f0"] if which == "first" else S_["f1"] - 1)[0]
    return _B107[key]

# ---- PRESS FLASH: a press camera fires; the next shot is printed as a newspaper photo, then comes to life -------------
def press_flash(A, B, j, f, sa, sb, pre=4, post=18):
    if j < 0:
        u = (j + pre + 1) / pre
        return np.clip(A * (1 + 0.10 * u) + 0.03 * u, 0, 1)
    v = (j + 1) / post
    snap = edge107(sb, "first")
    pr = halftone(snap, 8.0)
    w = smooth((v - 0.30) / 0.55)                                                          # the print comes to life
    o = pr * (1 - w) + B * w
    if 0.15 < v < 0.85:                                                                    # dots shrink as it resolves
        o = o * 0.5 + (halftone(B, 8.0 - 5.0 * smooth((v - 0.15) / 0.7)) * (1 - w) + B * w) * 0.5
    fl = math.exp(-j / 1.8)                                                                # the flashbulb
    o = o + (PAPER * 0.9 + 0.08) * fl * 0.30
    return np.clip(o, 0, 1)
TR2["press_flash"] = (press_flash, 4, 18)

# ---- HOT MOLASSES: a viscous sheet of blood pours down the lens ---------------------------------------------------
_MOL = {}
def mol_fields():
    if "f" not in _MOL:
        rng = np.random.default_rng(1071); xs = np.arange(W // 4, dtype=np.float32)
        fing = np.zeros_like(xs)
        for _ in range(7):                                                                 # the fingers of the front
            c = rng.uniform(0, W // 4); w = rng.uniform(16, 40); a = rng.uniform(0.4, 1.0)
            fing += a * np.exp(-((xs - c) / w) ** 2)
        fing = fing / fing.max()
        wave = cv2.GaussianBlur(rng.standard_normal((H // 4 * 2, W // 4)).astype(np.float32), (0, 0), sigmaX=9, sigmaY=16)
        _MOL["f"] = (fing, cv2.GaussianBlur(fing[None, :], (0, 0), 10)[0], wave / (np.abs(wave).max() + 1e-6))
    return _MOL["f"]

def mol_thickness(q, f):
    """quarter-res thickness of the sheet at progress q (0 -> 1 over pre + post); the cut is at MOL_QC."""
    fing, fsoft, wave = mol_fields(); h4, w4 = H // 4, W // 4
    yy = np.arange(h4, dtype=np.float32)[:, None]
    qp = clamp(q / MOL_QC, 0, 1); qd = clamp((q - MOL_QC) / (1 - MOL_QC), 0, 1)
    front = (-0.15 + 1.32 * ein(qp, 1.45)) * h4 + fing[None, :] * 85 * min(1.0, qp * 1.5) * (1 - 0.7 * qd)   # pours; fingers lead
    top = (-0.06 + 1.42 * ein(qd, 1.35)) * h4 + (1 - fsoft[None, :]) * 40 * qd                               # drains from the top
    body = np.clip((front - yy) / 26, 0, 1) * np.clip((yy - top) / 26, 0, 1)
    bead = np.exp(-((front - yy - 11) / 9.0) ** 2) * 0.45 * (qp < 1)                       # the rounded bead on the front
    bead2 = np.exp(-((yy - top - 10) / 9.0) ** 2) * 0.35 * (qd > 0) * np.clip((front - yy) / 26, 0, 1)   # the meniscus on the draining edge
    off = int(f * 3.0) % h4                                                                # undulations slide down the sheet
    und = 1 + 0.28 * wave[h4 - off:2 * h4 - off]
    th_ = (body * (0.72 + 0.28 * (1 - qd)) * und + bead + bead2).astype(np.float32)
    return np.clip(th_, 0, 1.5)

MOL_PRE, MOL_POST = 36, 24
MOL_QC = MOL_PRE / (MOL_PRE + MOL_POST)
def molasses(A, B, j, f, sa, sb, pre=MOL_PRE, post=MOL_POST):
    q = (j + pre + 0.5) / (pre + post)
    t4 = mol_thickness(q, f)
    if t4.max() < 0.003: return B if j >= 0 else A
    T = cv2.resize(t4, (W, H), interpolation=cv2.INTER_CUBIC)
    gy, gx = np.gradient(cv2.GaussianBlur(t4, (0, 0), 1.6))
    gx = cv2.resize(gx, (W, H)); gy = cv2.resize(gy, (W, H))
    plate = A if j < 0 else B
    ref = cv2.remap(plate, _GX + gx * 300, _GY + gy * 300, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)   # refraction
    sig = np.array([3.0, 2.8, 0.75], np.float32)
    Tr = np.exp(-sig * T[..., None] * 1.6)                                                 # absorption: crimson, deepest where thick
    col = ref * Tr * np.array([0.55, 0.55, 1.0], np.float32) ** np.clip(T[..., None] * 3, 0, 1) + BLOODC * (1 - Tr[..., 2:3]) * 0.9
    nx, ny = -gx * 26, -gy * 26; nz = np.ones_like(nx); nn = np.sqrt(nx * nx + ny * ny + nz * nz)
    l = np.array([-0.45, -0.55, 0.70], np.float32); l /= np.linalg.norm(l); hv = l + np.array([0, 0, 1], np.float32); hv /= np.linalg.norm(hv)
    ndh = (nx * hv[0] + ny * hv[1] + nz * hv[2]) / nn
    spec = np.clip(ndh, 0, 1) ** 46 * 1.10 * np.clip(T * 4, 0, 1)                         # the gloss
    sheen = np.clip((nx * l[0] + ny * l[1] + nz * l[2]) / nn, 0, 1) ** 8 * 0.10 * np.clip(T * 3, 0, 1)
    o = col + (spec + sheen)[..., None] * np.array([0.92, 0.95, 1.0], np.float32)
    return np.clip(o, 0, 1)
TR2["molasses"] = (molasses, MOL_PRE, MOL_POST)

# ---- HEADSPIN: two turns about the centre, motion-blurred, onto the upside-down shot --------------------------------
def spin_img(img, ang, z, n=1, spread=0.0):
    acc = None
    for i in range(n):
        a = ang + (i / max(1, n - 1) - 0.5) * spread if n > 1 else ang
        M = cv2.getRotationMatrix2D((W / 2, H / 2), a, z)
        r = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        acc = r if acc is None else acc + r
    return acc / n

def headspin(A, B, j, f, sa, sb, pre=20, post=20):
    N = pre + post; q = (j + pre + 0.5) / N
    phi = 720 * q * q * (3 - 2 * q); dphi = 720 * 6 * q * (1 - q) / N                     # degrees, and per frame
    z = 1 + 0.30 * math.sin(math.pi * q)
    img = A if j < 0 else B; ang = -phi if j < 0 else -(phi - 720)
    n = int(clamp(dphi / 4, 1, 9))
    o = spin_img(img, ang, z, n, dphi)
    if dphi > 8: o = radial_blur(o, W / 2, H / 2, 1.0, 1.0 + 0.0025 * dphi, 4)
    return np.clip(o, 0, 1)
TR2["headspin"] = (headspin, 20, 20)

def flip(A, B, j, f, sa, sb, pre=5, post=9):
    """the upside-down shot rolls the rest of the way over into the grin."""
    if j < 0:
        u = (j + pre + 1) / pre; ang = 90 * ein(u, 2); return np.clip(spin_img(A, ang, 1 + 0.15 * u, 5, 18 * u), 0, 1)
    v = (j + 1) / post; ang = -90 * (1 - eout(v, 2.2))
    return np.clip(spin_img(B, ang, 1 + 0.15 * (1 - v), 5 if v < 0.6 else 1, 18 * (1 - v)), 0, 1)
TR2["flip"] = (flip, 5, 9)

# ---- THE FRONT PAGE: BAY HARBOR BUTCHER; the photo under it is him (the next shot) --------------------------------
F_MAST = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
F_BODY = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
F_CAPT = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
PHOTO = (56, 742, 456, 1453)                                                               # x0, y0, x1, y1 on the page (9:16)
def squeeze(m, sx): return cv2.resize(m, (max(1, int(m.shape[1] * sx)), m.shape[0]), interpolation=cv2.INTER_AREA)
def put_mask(canvas_a, m, x, y):
    h, w = m.shape; ys, xs = slice(max(0, y), min(H, y + h)), slice(max(0, x), min(W, x + w))
    canvas_a[ys, xs] = np.maximum(canvas_a[ys, xs], m[ys.start - y:ys.stop - y, xs.start - x:xs.stop - x])

_FP = {}
def page_layers():
    """(paper rgb, ink mask, red mask): the front page without its photo."""
    if "p" in _FP: return _FP["p"]
    rng = np.random.default_rng(1072)
    paper = np.empty((H, W, 3), np.float32); pt = paper_tex()
    for c in range(3): paper[..., c] = PAPER[c] * (1 + pt * 0.05)
    edge = np.clip(np.minimum(np.minimum(_GX, W - 1 - _GX), np.minimum(_GY, H - 1 - _GY)) / 90, 0, 1)
    paper *= (0.90 + 0.10 * edge)[..., None]
    ink = np.zeros((H, W), np.float32); red = np.zeros((H, W), np.float32)
    m = text_mask("MIAMI GAZETTE", F_MAST, 104); m = squeeze(m, min(1.0, 980 / m.shape[1])); put_mask(ink, m, int(W / 2 - m.shape[1] / 2), 52)
    cv2.line(ink, (40, 40), (W - 40, 40), 1.0, 3); cv2.line(ink, (40, 196), (W - 40, 196), 1.0, 3); cv2.line(ink, (40, 238), (W - 40, 238), 1.0, 1)
    m = text_mask("SPECIAL EDITION   ·   MIAMI, FLORIDA   ·   FINAL", F_SB, 26, tracking=2); put_mask(ink, m, int(W / 2 - m.shape[1] / 2), 204)
    m = text_mask("BAY HARBOR", F_BLACK, 210, tracking=-4); m = squeeze(m, 990 / m.shape[1]); put_mask(ink, m, int(W / 2 - m.shape[1] / 2), 252)
    m = text_mask("BUTCHER", F_BLACK, 250, tracking=-4); m = squeeze(m, 990 / m.shape[1]); put_mask(red, m, int(W / 2 - m.shape[1] / 2), 452)
    m = text_mask("INVESTIGATION STILL ONGOING", F_XB, 46, tracking=1); m = squeeze(m, min(1.0, 990 / m.shape[1])); put_mask(ink, m, int(W / 2 - m.shape[1] / 2), 676)
    cv2.rectangle(ink, (PHOTO[0] - 3, PHOTO[1] - 3), (PHOTO[2] + 3, PHOTO[3] + 3), 1.0, 2)
    m = text_mask("Blood spatter analyst Dexter Morgan", F_CAPT, 21); put_mask(ink, m, PHOTO[0], PHOTO[3] + 12)
    m = text_mask("at the scene, Tuesday.", F_CAPT, 21); put_mask(ink, m, PHOTO[0], PHOTO[3] + 40)
    words = ("the police said investigators were searching the bay for more remains as federal agents joined the case and the "
             "department declined to comment on reports that a suspect had been identified among the bodies recovered from the "
             "water off the marina residents gathered at the docks overnight while divers worked in shifts the medical examiner "
             "confirmed that the victims had been killed elsewhere and the killer remains at large").split()
    cols = [(496, 742, 752), (776, 742, 1032)]
    for (x0, y0, x1) in cols:
        y = y0; wi = int(rng.integers(len(words)))
        while y < 1830:
            line = []; wsum = 0
            while True:
                w = words[wi % len(words)]; wi += 1; tw = len(w) * 11 + 9
                if wsum + tw > (x1 - x0): break
                line.append(w); wsum += tw
            m = text_mask(" ".join(line), F_BODY, 21); put_mask(ink, squeeze(m, min(1.0, (x1 - x0) / m.shape[1])), x0, y)
            y += 29
            if rng.random() < 0.06: y += 22
        cv2.line(ink, (x1 + 12, 742), (x1 + 12, 1840), 0.8, 1)
    y = 1500
    while y < 1830:
        m = text_mask(" ".join(words[(y // 7) % 20:(y // 7) % 20 + 6]), F_BODY, 21); put_mask(ink, squeeze(m, min(1.0, 400 / m.shape[1])), PHOTO[0], y); y += 29
    _FP["p"] = (paper, ink, red); return _FP["p"]

def page_with_photo(photo):
    """the page, with photo (a full 1080x1920 frame) printed into the photo box as a halftone."""
    paper, ink, red = page_layers()
    pw, ph = PHOTO[2] - PHOTO[0], PHOTO[3] - PHOTO[1]
    small = cv2.resize(photo, (pw, ph), interpolation=cv2.INTER_AREA)
    pr = halftone(cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR), 9.0 * W / pw)  # screen at print scale
    pr = cv2.resize(pr, (pw, ph), interpolation=cv2.INTER_AREA)
    o = paper.copy(); o[PHOTO[1]:PHOTO[3], PHOTO[0]:PHOTO[2]] = pr * (0.97 + 0.03 * paper[PHOTO[1]:PHOTO[3], PHOTO[0]:PHOTO[2]] / PAPER)
    o = o * (1 - ink[..., None] * 0.94) + INK * ink[..., None] * 0.94
    o = o * (1 - red[..., None]) + SPOT * red[..., None]
    return o.astype(np.float32)

def frontpage(A, B, j, f, sa, sb, pre=82, post=28):
    PCX, PCY = (PHOTO[0] + PHOTO[2]) / 2, (PHOTO[1] + PHOTO[3]) / 2
    SDIVE = H / (PHOTO[3] - PHOTO[1])
    if j >= 0:                                                                             # the photo's dots resolve into him
        v = (j + 1) / post; pitch = 9.0 * SDIVE * (1 - eout(v, 1.6)) + 3.0
        w = smooth((v - 0.25) / 0.65)
        return np.clip(halftone(B, pitch) * (1 - w) + B * w, 0, 1)
    if "pg" not in _FP or _FP.get("pgk") != sb["n"]:
        _FP["pg"] = page_with_photo(edge107(sb, "first")); _FP["pgk"] = sb["n"]
    page = _FP["pg"]
    u = (j + pre + 1) / pre
    if u < 0.80:
        if u < 0.52:                                                                       # the classic spin-in
            w_ = eout(u / 0.52, 2.6); s_ = 0.04 + 0.86 * w_; rot = 3 * 360 * (1 - w_)
        else:                                                                              # it lands, settles, we push in
            w_ = (u - 0.52) / 0.28
            s_ = 0.90 + 0.05 * math.sin(math.pi * min(1, w_ * 2.2)) * math.exp(-w_ * 2) + 0.06 * w_; rot = 2.0 * math.exp(-w_ * 5) * math.cos(w_ * 12)
        M = cv2.getRotationMatrix2D((W / 2, H / 2), rot, s_)
    else:                                                                                  # the dive: his photo comes to fill the frame
        w_ = ein((u - 0.80) / 0.20, 2.2); s0 = 0.96; s_ = s0 * (SDIVE / s0) ** w_
        pcx0, pcy0 = W / 2 + (PCX - W / 2) * s0, H / 2 + (PCY - H / 2) * s0
        tcx, tcy = pcx0 + (W / 2 - pcx0) * w_, pcy0 + (H / 2 - pcy0) * w_
        M = np.float32([[s_, 0, tcx - PCX * s_], [0, s_, tcy - PCY * s_]])
    pa = cv2.warpAffine(np.dstack([page, np.ones((H, W), np.float32)]), M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    al = pa[..., 3:4]
    bg = A * (1 - 0.45 * min(1.0, u * 2.5))
    if u < 0.80:                                                                           # its shadow on the scene
        sh = cv2.GaussianBlur(np.roll(np.roll(pa[..., 3], 18, 0), 12, 1), (0, 0), 16) * 0.55
        bg = bg * (1 - sh[..., None])
    return np.clip(bg * (1 - al) + pa[..., :3] * al, 0, 1)
TR2["frontpage"] = (frontpage, 82, 28)

# ---- confetti: lit paper pieces, fluttering, with depth ------------------------------------------------------------
CONF_COLS = np.array([[0.13, 0.12, 0.80], [0.84, 0.92, 0.96], [0.84, 0.92, 0.96], [0.06, 0.05, 0.05], [0.50, 0.42, 0.34], [0.20, 0.20, 0.86]], np.float32)
def conf_set(seed, n, t_a, t_b, mode):
    """n pieces. mode 'rain': spawned above the frame between t_a and t_b; 'pop': all at t_a from a burst point."""
    rng = np.random.default_rng(seed)
    d = dict(t=rng.uniform(t_a, t_b, n) if mode == "rain" else np.full(n, t_a, np.float32),
             x=rng.uniform(-80, W + 80, n), y=rng.uniform(-300, -40, n),
             depth=rng.uniform(0, 1, n) ** 1.6, col=rng.integers(0, len(CONF_COLS), n),
             a0=rng.uniform(0, 360, n), wa=rng.uniform(-420, 420, n), b0=rng.uniform(0, 6.28, n), wb=rng.uniform(5, 16, n),
             sway=rng.uniform(10, 60, n), ws=rng.uniform(1.5, 4.0, n), ar=rng.uniform(0.35, 0.75, n),
             vx=rng.normal(0, 1, n), vy=rng.normal(0, 1, n))
    return d

def draw_confetti(out, t, d, mode="rain", origin=(W / 2, H * 0.3), cover=1.0, guard=None):
    tau = t - d["t"]; alive = tau >= 0
    if not alive.any(): return out
    near = d["depth"]; size = 14 + 150 * near ** 2.2                                       # near pieces are big and soft
    if mode == "rain":
        vfall = (260 + 900 * near) if mode == "rain" and cover < 2 else 0
        vfall = vfall * (2.6 if cover >= 1.5 else 1.0)
        px = d["x"] + d["sway"] * np.sin(d["ws"] * tau + d["b0"]); py = d["y"] + vfall * tau
    else:
        sp = 900 + 1500 * near; ex = 1 - np.exp(-tau * 3.2)
        px = origin[0] + d["vx"] * sp * 1.4 * ex / 3.2 + d["sway"] * np.sin(d["ws"] * tau + d["b0"])
        py = origin[1] + (np.abs(d["vy"]) * 0.8 + 0.25) * sp * 0.75 * ex / 3.2 + (180 + 500 * near) * np.maximum(0, tau - 0.15) ** 1.4 * 1.6
    vis = alive & (py > -260) & (py < H + 260) & (px > -260) & (px < W + 260)
    if not vis.any(): return out
    lay_far = np.zeros((H, W, 3), np.uint8); a_far = np.zeros((H, W), np.uint8)
    lay_near = np.zeros((H, W, 3), np.uint8); a_near = np.zeros((H, W), np.uint8)
    order = np.argsort(near)
    for i in order:
        if not vis[i]: continue
        sz = size[i] * (1.25 if cover >= 1.5 else 1.0); ang = math.radians(d["a0"][i] + d["wa"][i] * tau[i]); fl = math.cos(d["b0"][i] + d["wb"][i] * tau[i])
        hw, hh = sz * 0.5, sz * 0.5 * d["ar"][i] * max(0.08, abs(fl))
        ca, sa_ = math.cos(ang), math.sin(ang)
        pts = np.array([[px[i] + ca * dx - sa_ * dy, py[i] + sa_ * dx + ca * dy] for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))], np.float32)
        bright = 0.55 + 0.45 * abs(fl) + (0.55 if abs(fl) > 0.97 else 0.0)
        col = np.clip(CONF_COLS[d["col"][i]] * bright, 0, 1)
        far = near[i] < 0.55
        L_, A_ = (lay_far, a_far) if far else (lay_near, a_near)
        cv2.fillConvexPoly(L_, (pts * 4).astype(np.int32), tuple(int(c * 255) for c in col), cv2.LINE_AA, 2)
        cv2.fillConvexPoly(A_, (pts * 4).astype(np.int32), 255, cv2.LINE_AA, 2)
    o = out
    for L_, A_, blur in ((lay_far, a_far, 0.0), (lay_near, a_near, 2.4)):
        if not A_.any(): continue
        Lf = L_.astype(np.float32) / 255; Af = A_.astype(np.float32) / 255
        if blur: Lf = cv2.GaussianBlur(Lf, (0, 0), blur); Af = cv2.GaussianBlur(Af, (0, 0), blur)
        if guard is not None: Af = Af * guard
        o = o * (1 - Af[..., None]) + Lf * Af[..., None] * 1.0
    return o

def face_keep(s, f, grow=1.25):
    """1 everywhere except a feathered ellipse over the tracked face (particles never cross it)."""
    fs = face_scr(s, f) if s.get("face") is not None else None
    if not fs: return None
    m = np.zeros((H // 4, W // 4), np.float32)
    cv2.ellipse(m, (int(fs[0] / 4), int(fs[1] / 4)), (int(fs[2] * 0.62 * grow / 4), int(fs[2] * 0.85 * grow / 4)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    return 1 - cv2.resize(cv2.GaussianBlur(m, (0, 0), 5), (W, H))

POP_PRE = 24
def pop_set():
    if "pop" not in _FP: _FP["pop"] = conf_set(1073, 190, 0.0, 0.0, "pop")
    return _FP["pop"]

def confetti_pop(A, B, j, f, sa, sb, pre=POP_PRE, post=2):
    """the confetti bursts in the sky over the banner; after the cut it carries on behind him (pop_behind)."""
    if j >= 0: return B
    return np.clip(draw_confetti(A, (j + pre + 1) / FPS, pop_set(), "pop", (W * 0.5, H * 0.02)), 0, 1)

def pop_behind(img, s, f, person):
    """a confetti burst from the top of the frame, between him and the crowd (his matte keeps it off him)."""
    k = f - s["f0"]
    if k >= 70 or person is None: return img
    c = draw_confetti(img, (k + POP_PRE + 1) / FPS, pop_set(), "pop", (W * 0.5, H * 0.02))
    pm = np.clip(person * 1.1, 0, 1)[..., None]
    return img * pm + c * (1 - pm)
TR2["confetti_pop"] = (confetti_pop, POP_PRE, 2)

# ---- THE LOOP: the confetti thickens over the lens on the bass drop-out bar and clears on frame 0 ---------------------
LOOP_F0 = None
def loop_w(f):
    f0 = fh(E.E_LOOP); u = (f - f0 + 1) / (E.DUR_F - f0)
    return smooth((u - 0.38) / 0.24) if f >= f0 else 0.0

_LV = {}
def frame0_plate():
    if "b" not in _LV: _LV["b"] = base107(SHOTS[0], SHOTS[0]["f0"])[0]
    return _LV["b"]

def confetti_loop(out, f, s):
    f0 = fh(E.E_LOOP)
    if f < f0: return out
    t = (f - f0) / FPS; T = (E.DUR_F - f0) / FPS
    if "rain" not in _FP: _FP["rain"] = conf_set(1074, 1100, -0.6, T - 0.95, "rain")
    w = loop_w(f)
    under = out if w <= 0 else (frame0_plate() if w >= 1 else out * (1 - w) + frame0_plate() * w)
    u = (f - f0 + 1) / (E.DUR_F - f0); thick = math.sin(math.pi * clamp(u / 0.95, 0, 1)) ** 0.8
    under = under * (1 - 0.10 * thick)
    o = draw_confetti(under, t, _FP["rain"], "rain", cover=1.6)
    fade = smooth((t - (T - 0.40)) / 0.36)                                                 # the stragglers fade as frame 0 arrives
    return np.clip(o * (1 - fade) + under * fade, 0, 1)

# ---- the STAMP: the newsprint strip and D-E-X-T-E-R, then the strip becomes the banner in the sky -------------------
STRIP_C, STRIP_W, STRIP_H, STRIP_ROT = (540, 870), 1010, 250, -3.0
_ST = {}
def strip_tex():
    if "s" in _ST: return _ST["s"]
    rng = np.random.default_rng(1075); h, w = STRIP_H + 60, STRIP_W + 60
    pt = paper_tex()[:h, :w]
    rgb = np.empty((h, w, 3), np.float32)
    for c in range(3): rgb[..., c] = PAPER[c] * (1 + pt * 0.06)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    n1 = cv2.resize(rng.standard_normal((h // 6, w // 6)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    torn = np.minimum(np.minimum(xx - 30 - n1 * 5, w - 30 - xx + n1 * 5), np.minimum(yy - 30 - n1 * 3, h - 30 - yy - n1 * 3))
    a = np.clip(torn / 1.5 + 0.5, 0, 1)
    rgb *= (0.93 + 0.07 * np.clip(torn / 40, 0, 1))[..., None]                             # the edges a touch darker
    _ST["s"] = np.dstack([rgb, a]).astype(np.float32)
    lets, xs = [], []
    for c in "DEXTER":
        m = text_mask(c, F_BLACK, 205, tracking=0); lets.append(m)
    tot = sum(m.shape[1] for m in lets) + 26 * 5; x = w / 2 - tot / 2
    for m in lets: xs.append(x + m.shape[1] / 2); x += m.shape[1] + 26
    rgi = np.random.default_rng(1076)
    inks = []
    for m in lets:                                                                         # letterpress ink: uneven, a little bite
        sp = cv2.resize(rgi.random((m.shape[0] // 3 + 1, m.shape[1] // 3 + 1)).astype(np.float32), (m.shape[1], m.shape[0]))
        inks.append(np.clip(m * (0.82 + 0.18 * sp) * (1 - (sp < 0.06) * 0.6), 0, 1))
    _ST["lets"] = (inks, xs); return _ST["s"]

def strip_canvas(t, stamps):
    """the strip (rgba, its own pixel space) with the letters stamped by time t."""
    base = strip_tex().copy(); inks, xs = _ST["lets"]; h, w = base.shape[:2]
    for (wd, tw), m, xc in zip(stamps, inks, xs):
        k = (t - tw) * FPS
        if k < 0: continue
        v = clamp(k / 4.0, 0, 1)
        if v < 1:                                                                          # the stamp coming down
            sc = 1.9 - 0.9 * ein(v, 2.2); mm = cv2.resize(m, None, fx=sc, fy=sc); mm = cv2.GaussianBlur(mm, (0, 0), 0.1 + 6 * (1 - v)) * v
        else: mm = m
        hh, ww = mm.shape; x0 = int(xc - ww / 2); y0 = int(h / 2 - hh / 2 + 6)
        ys, xs_ = slice(max(0, y0), min(h, y0 + hh)), slice(max(0, x0), min(w, x0 + ww))
        sub = mm[ys.start - y0:ys.stop - y0, xs_.start - x0:xs_.stop - x0]
        if v >= 1:                                                                         # the deboss: pressed into the paper
            dm = cv2.GaussianBlur(sub, (0, 0), 2.0)
            sh = np.clip(np.roll(dm, 3, 0) - dm, 0, 1) * 0.35; hl = np.clip(np.roll(dm, -3, 0) - dm, 0, 1) * 0.10
            base[ys, xs_, :3] *= (1 - sh)[..., None]; base[ys, xs_, :3] += hl[..., None]
            spread = 1 + 0.10 * math.exp(-(k - 4) / 3)                                      # ink spreads at the hit, then settles
            sub = np.clip(sub * spread, 0, 1)
        base[ys, xs_, :3] = base[ys, xs_, :3] * (1 - sub[..., None]) + INK * sub[..., None]
    return base

def put_strip(out, rgba, cx, cy, sc, rot, a=1.0, shadow=0.45):
    h, w = rgba.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, sc); M[0, 2] += cx - w / 2; M[1, 2] += cy - h / 2
    pa = cv2.warpAffine(rgba, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    al = pa[..., 3:4] * a
    if shadow > 0:
        sh = cv2.GaussianBlur(np.roll(np.roll(pa[..., 3], 16, 0), 10, 1), (0, 0), 14) * shadow * a
        out = out * (1 - sh[..., None])
    return out * (1 - al) + pa[..., :3] * al

def banner_target():
    """where the banner's DEXTER sits on screen in the banner shot (centre, scale vs the strip, rotation)."""
    return (785.0, 980.0), 0.53, -4.1

def text_stamp(out, f, tx):
    t = f / FPS; stamps = [(w, wt) for w, wt, _ in tx["words"]]
    t_in = next(wt for tx_ in E.TEXT if tx_["style"] == "cap" for w_, wt, _ in tx_["words"] if w_ == "CAPS") - 0.02   # it slaps on with "CAPS"
    t_cut = E.th(48); t_end = t_cut + 0.80
    if t < t_in or t > t_end: return out
    rgba = strip_canvas(min(t, t_cut + 0.2), stamps)
    k = (t - t_in) * FPS; v = clamp(k / 5.0, 0, 1)
    sc = 1.28 - 0.28 * eout(v, 3) + (0.02 * math.sin(k * 0.9) * math.exp(-k / 6) if v >= 1 else 0)
    cx, cy = STRIP_C; rot = STRIP_ROT; a = min(1.0, k / 3.0); shake = 0.0
    for _, tw in stamps:                                                                   # each stamp shakes the strip
        dk = (t - tw) * FPS - 4
        if 0 <= dk < 8: shake = max(shake, 5 * math.exp(-dk / 2.5))
    cy += shake * math.sin(f * 2.1)
    if t > t_cut - 0.02:                                                                   # it flies into the sky onto the banner
        w_ = smooth((t - t_cut + 0.02) / 0.45)
        (bx, by), bs, br = banner_target()
        cx, cy = cx + (bx - cx) * w_, cy + (by - cy) * w_; sc = sc + (bs - sc) * w_; rot = rot + (br - rot) * w_
        a = a * (1 - smooth((t - t_cut - 0.42) / 0.36))
    return put_strip(out, rgba, cx, cy, sc, rot, a, 0.45 * (1 - smooth((t - t_cut) / 0.3)))

def text_cap(out, f, tx, person=None):
    """the v9 caption (the approved construction), with an optional per-caption ys=(line0, line1)."""
    t = f / FPS; words = tx["words"]; t_in = max(words[0][1], tx.get("from", -1))
    if t < t_in - 0.02 or t > tx["end"] + 0.01: return out
    big = tx.get("big"); sizes = [92, 120] if big else [88, 114]
    ys = tx.get("ys") or ((1368, 1492) if big else (1380, 1496))
    emph = tx.get("emph", []); fr = tx.get("from", -1)
    a_out = 1 - smooth((t - (tx["end"] - 0.16)) / 0.16)
    out = out * cap_scrim(ys[0] - 70, ys[1] + 70, 0.34 * a_out * smooth((t - t_in + 0.05) / 0.25))
    for ln in (0, 1):
        ws = [(w, max(wt, fr)) for w, wt, l in words if l == ln]
        if not ws: continue
        sz = sizes[ln]
        for _ in range(6):                                                                 # auto-fit the line to 940 px
            ims = [cap_word(w, sz, w in emph) for w, _ in ws]
            gap = int(sz * 0.26); widths = [im.shape[1] - 72 for im in ims]
            tot = sum(widths) + gap * (len(ims) - 1)
            if tot <= 940: break
            sz = int(sz * 940 / tot) - 1
        x = W / 2 - tot / 2
        for (w, wt), im, wd in zip(ws, ims, widths):
            v = eout(clamp((t - wt) / 0.17, 0, 1), 2.4)
            o_im = im if a_out > 0.98 else cv2.GaussianBlur(im, (0, 0), 0.1 + 5 * (1 - a_out))
            out = ease_word(out, o_im, x + wd / 2, ys[ln] - 14 * (1 - a_out), v, a_out, rise=30)
            x += wd + gap
    return out

def text107(out, f, s, rides):
    for tx in E.TEXT:
        if bool(tx.get("rides")) != rides: continue
        if tx["style"] == "cap": out = text_cap(out, f, tx, None)
        elif tx["style"] == "stamp": out = text_stamp(out, f, tx)
    return out

# ---- the frame ----------------------------------------------------------------------------------------------------
def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base107(s, f)
    out = text107(out, f, s, True)
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge107(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge107(n_, "first"), kn, f, s, n_)
    if s.get("tout") == "confetti_loop": out = confetti_loop(out, f, s)
    out = beat_fx(out, f)
    out = text107(out, f, s, False)
    out = flash_governor(out)
    return (np.clip(finish107(out, f, s), 0, 1) * 255 + 0.5).astype(np.uint8)

# ============================================================================ v107 rev 2 (owner notes; overrides above)
# ---- the camera rests through the break (the ending is smooth) and during the TV ------------------------------------
def beat_phase(f):
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    hook = (E.E_BEAT <= e < 54) and not (6.5 <= e < 9.7) and not (19 <= e < 23) and not (24 <= e < 28.5) and not (47 <= e < 50)
    return ph, bi, hook, False

# ---- SPECIAL REPORT: the shot is on a TV; the channel flips; we push back through the screen -------------------------
TV_W, TV_H = 860.0, 645.0                                                                  # the 4:3 screen at the TV's own scale
Z_FULL = W / TV_W                                                                          # the zoom where the screen fills the width
_TV = {}
def tv_assets():
    """(casing rgba at scale 1 around a screen centred on the frame, chyron rgba in screen pixels, scanlines)."""
    if "c" in _TV: return _TV["c"]
    bw, bh = 1000, 900; cx, cy = W / 2, H / 2 + 60                                          # the body: the screen sits high in it
    cas = np.zeros((H, W, 4), np.float32)
    body = np.zeros((H, W), np.float32)
    cv2.rectangle(body, (int(cx - bw / 2), int(cy - bh / 2 - 60)), (int(cx + bw / 2), int(cy + bh / 2 - 60)), 1.0, -1)
    body = cv2.GaussianBlur(body, (0, 0), 6); body = np.clip(body * 1.6 - 0.3, 0, 1)
    scr = np.zeros((H, W), np.float32)
    cv2.rectangle(scr, (int(W / 2 - TV_W / 2 + 22), int(H / 2 - TV_H / 2 + 22)), (int(W / 2 + TV_W / 2 - 22), int(H / 2 + TV_H / 2 - 22)), 1.0, -1)
    scr = np.clip(cv2.GaussianBlur(scr, (0, 0), 14) * 1.9 - 0.45, 0, 1)                    # rounded screen corners
    yy = (_GY - (cy - bh / 2 - 60)) / bh
    xx = (_GX - (cx - bw / 2)) / bw
    shade = 0.20 + 0.10 * (1 - np.clip(yy, 0, 1)) + 0.04 * np.sin(np.pi * np.clip(xx, 0, 1))   # lit from above and the front
    shade = shade + 0.16 * np.exp(-((_GY - (cy - bh / 2 - 54)) / 5) ** 2) + 0.06 * np.exp(-((_GX - (cx - bw / 2 + 6)) / 5) ** 2)   # edge highlights
    shade = shade - 0.06 * np.exp(-((_GY - (cy + bh / 2 - 66)) / 6) ** 2)                 # the bottom edge in shadow
    rim = np.exp(-((cv2.GaussianBlur(scr, (0, 0), 3) - 0.5) / 0.18) ** 2) * 0.16             # the bevel round the glass
    for c in range(3): cas[..., c] = shade * (0.95 + 0.05 * c) + rim
    led = np.exp(-(((_GX - (cx + bw / 2 - 90)) / 7) ** 2 + ((_GY - (cy + bh / 2 - 105)) / 7) ** 2))
    cas[..., :3] += led[..., None] * SPOT * 1.4
    for k in range(5): cv2.line(cas, (int(cx - bw / 2 + 70 + 34 * k), int(cy + bh / 2 - 112)), (int(cx - bw / 2 + 92 + 34 * k), int(cy + bh / 2 - 112)), (0.30, 0.30, 0.30, 1.0), 3, cv2.LINE_AA)
    cas[..., 3] = body * (1 - scr)
    cas[..., :3] *= cas[..., 3:4]
    sw, sh = int(TV_W), int(TV_H); ch = np.zeros((sh, sw, 4), np.float32)
    bar_y = int(sh * 0.74); cv2.rectangle(ch, (0, bar_y), (int(sw * 0.36), bar_y + 50), tuple(float(v) for v in SPOT) + (1.0,), -1)
    cv2.rectangle(ch, (int(sw * 0.36), bar_y), (sw, bar_y + 50), tuple(float(v) for v in PAPER) + (1.0,), -1)
    cv2.rectangle(ch, (0, bar_y + 50), (sw, bar_y + 92), tuple(float(v) for v in INK) + (0.92,), -1)
    def put_txt(word, font, size, col, x, y):
        m = text_mask(word, font, size, tracking=1); h_, w_ = m.shape; y0 = int(y - h_ / 2)
        sub = ch[y0:y0 + h_, x:x + w_]; mm = m[:sub.shape[0], :sub.shape[1]]
        sub[..., :3] = sub[..., :3] * (1 - mm[..., None]) + np.array(col, np.float32) * mm[..., None]; sub[..., 3] = np.maximum(sub[..., 3], mm)
    put_txt("SPECIAL REPORT", F_BLACK, 30, (0.97, 0.97, 0.97), 14, bar_y + 25)
    put_txt("BAY HARBOR BUTCHER STILL AT LARGE", F_BLACK, 28, tuple(float(v) for v in INK), int(sw * 0.36) + 14, bar_y + 25)
    put_txt("POLICE URGE RESIDENTS TO STAY ALERT · FBI JOINS INVESTIGATION", F_XB, 22, tuple(PAPER), 14, bar_y + 71)
    cv2.rectangle(ch, (22, 22), (110, 62), tuple(float(v) for v in SPOT) + (1.0,), -1); put_txt("LIVE", F_BLACK, 26, (0.97, 0.97, 0.97), 34, 42)
    scan = (1 - 0.10 * (np.arange(sh) % 3 == 0))[:, None].astype(np.float32)
    _TV["c"] = (cas, ch, scan, scr); return _TV["c"]

def tv_frame(content, Z, mask_h, chy, static, glow=1.0, f=0, scan_a=1.0, glass=1.0):
    """content (a full frame) on the TV: Z = zoom of the TV (Z_FULL: the screen is the frame's width); mask_h = the
    visible height of the screen window in output px (letterbox closing/opening); chy 0..1 chyron in; static 0..1."""
    cas, ch, scan, scr = tv_assets()
    k = Z / Z_FULL                                                                         # content scale: 1 at Z_FULL
    M = np.float32([[k, 0, W / 2 * (1 - k)], [0, k, H / 2 * (1 - k)]])
    c = cv2.warpAffine(content, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    sw, sh = TV_W * Z, TV_H * Z                                                            # the screen window
    win_h = min(mask_h, sh) if Z >= Z_FULL - 1e-3 else sh
    sc = cv2.warpAffine(scr, np.float32([[Z, 0, W / 2 * (1 - Z)], [0, Z, H / 2 * (1 - Z)]]), (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    if Z >= Z_FULL - 1e-3 and mask_h > sh:                                                 # still opening: a plain letterbox
        sc = np.clip((mask_h / 2 - np.abs(_GY - H / 2)) / 3, 0, 1).astype(np.float32)
    # the screen: scanlines, phosphor, the chyron, static, the glass
    scr_img = c.copy()
    if scan_a > 0:
        sl = cv2.resize(np.repeat(scan, int(TV_W), 1), None, fx=Z, fy=Z, interpolation=cv2.INTER_LINEAR)
        y0 = int(H / 2 - sl.shape[0] / 2); x0 = int(W / 2 - sl.shape[1] / 2)
        full = np.ones((H, W), np.float32); ys, xs = slice(max(0, y0), min(H, y0 + sl.shape[0])), slice(max(0, x0), min(W, x0 + sl.shape[1]))
        full[ys, xs] = sl[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0]
        scr_img = scr_img * (1 - scan_a + scan_a * full)[..., None]
    if chy > 0:
        Mc = np.float32([[Z, 0, W / 2 - TV_W * Z / 2 - (1 - eout(chy, 3)) * 400 * Z], [0, Z, H / 2 - TV_H * Z / 2]])
        cw = cv2.warpAffine(ch, Mc, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0)); a = cw[..., 3:4] * min(1.0, chy * 1.5)
        scr_img = scr_img * (1 - a) + cw[..., :3] * a
    if static > 0:
        rng = np.random.default_rng(f * 7 + 3); nz = cv2.resize(rng.random((H // 6, W // 6)).astype(np.float32), (W, H), interpolation=cv2.INTER_NEAREST)
        roll = 0.5 + 0.5 * np.sin((_GY / H * 3 + f * 0.37) * 2 * math.pi)
        stc = (nz * 0.75 + 0.15) * (0.75 + 0.25 * roll)
        scr_img = scr_img * (1 - static) + stc[..., None] * PAPER * static
    vig = 1 - 0.35 * glass * np.clip(((_GX - W / 2) / (sw / 2 + 1)) ** 2 + ((_GY - H / 2) / (sh / 2 + 1)) ** 2, 0, 1) ** 1.5
    refl = np.exp(-(((_GX - W / 2) * 0.6 + (_GY - H / 2 + sh * 0.25)) / (sw * 0.18 + 1)) ** 2) * 0.06 * glass   # a soft glass reflection (fades with the letterbox)
    scr_img = scr_img * vig[..., None] + refl[..., None]
    # the room: dark, lit by the screen
    room = np.zeros((H, W, 3), np.float32) + INK * 0.6
    lum_s = float(cv2.resize(c, (8, 8), interpolation=cv2.INTER_AREA).mean())
    gl = np.exp(-(((_GX - W / 2) / (sw * 1.05 + 1)) ** 2 + ((_GY - H / 2) / (sh * 1.5 + 1)) ** 2)) * (0.16 + 0.35 * lum_s) * glow
    room = room + gl[..., None] * PAPER
    casz = cv2.warpAffine(cas, np.float32([[Z, 0, W / 2 * (1 - Z)], [0, Z, H / 2 * (1 - Z)]]), (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    o = room * (1 - casz[..., 3:4]) + casz[..., :3]
    return np.clip(o * (1 - sc[..., None]) + scr_img * sc[..., None], 0, 1)

def broadcast(A, B, j, f, sa, sb, pre=36, post=36):
    Zmin = 0.92
    if j < 0:
        u = (j + pre + 1) / pre
        if u < 0.33:                                                                       # the picture closes into a TV image
            mh = H - (H - TV_H * Z_FULL) * smooth(u / 0.33)
            return tv_frame(A, Z_FULL, mh, 0.0, 0.0, f=f, scan_a=smooth(u / 0.33), glass=smooth(u / 0.33))
        w = smooth((u - 0.33) / 0.50); Z = Z_FULL + (Zmin - Z_FULL) * w                     # the TV pulls back into a dark room
        st = smooth((u - 0.86) / 0.14) * 0.85                                              # the channel starts to flip
        return tv_frame(A, Z, TV_H * Z, smooth((u - 0.30) / 0.30), st, f=f)
    v = (j + 1) / post
    st = 0.85 * (1 - smooth(v / 0.16))
    if v < 0.70:                                                                           # the new channel: him; we push in
        w = smooth((v - 0.14) / 0.56); Z = Zmin + (Z_FULL - Zmin) * w
        return tv_frame(B, Z, TV_H * Z, 1 - smooth((v - 0.20) / 0.30), st, f=f)
    w = smooth((v - 0.70) / 0.30); mh = TV_H * Z_FULL + (H - TV_H * Z_FULL) * w            # the screen opens to the frame
    return tv_frame(B, Z_FULL, mh, 0.0, 0.0, f=f, scan_a=1 - w, glass=1 - w)
TR2["broadcast"] = (broadcast, 36, 36)

# ---- HEADSPIN onto a centred shot: the turn decelerates about his face -------------------------------------------------
def spin_about(img, ang, z, cx, cy, n=1, spread=0.0):
    acc = None
    for i in range(n):
        a = ang + (i / max(1, n - 1) - 0.5) * spread if n > 1 else ang
        M = cv2.getRotationMatrix2D((cx, cy), a, z); M[0, 2] += W / 2 - cx; M[1, 2] += H / 2 - cy
        M[0, 2] += (cx - W / 2); M[1, 2] += (cy - H / 2)
        r = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        acc = r if acc is None else acc + r
    return acc / n

def headspin(A, B, j, f, sa, sb, pre=20, post=24):
    N = pre + post; q = (j + pre + 0.5) / N
    phi = 720 * q * q * (3 - 2 * q); dphi = 720 * 6 * q * (1 - q) / N
    z = 1 + 0.28 * math.sin(math.pi * q)
    if j < 0: img, ang, cx, cy = A, -phi, W / 2, H / 2
    else:
        fs = face_scr(sb, f) if sb.get("face") is not None else None
        cx, cy = (fs[0], fs[1]) if fs else (W / 2, H / 2); img, ang = B, -(phi - 720)
    n = int(clamp(dphi / 4, 1, 9))
    o = spin_about(img, ang, z, cx, cy, n, dphi)
    if dphi > 8: o = radial_blur(o, cx, cy, 1.0, 1.0 + 0.0025 * dphi, 4)
    return np.clip(o, 0, 1)
TR2["headspin"] = (headspin, 20, 24)

# ---- THE MASSES SPELL HIS NAME (the loop): the parade's confetti gathers into DEXTER, holds, bursts into frame 0 -----
NL_G0, NL_G1, NL_B = 58.4, 60.4, 62.3                                                       # edit half-beats: gather, formed, burst
_NL = {}
def name_targets():
    if "t" in _NL: return _NL["t"]
    m = text_mask("DEXTER", F_BLACK, 300, tracking=10); m = squeeze(m, 1000 / m.shape[1])
    h, w = m.shape; cx, cy = W / 2, 1110
    ys, xs = np.nonzero(m > 0.6); rng = np.random.default_rng(1077); n = 1050
    pick = rng.choice(len(xs), n, replace=False)
    tx = (xs[pick] - w / 2 + cx).astype(np.float32); ty = (ys[pick] - h / 2 + cy).astype(np.float32)
    side = np.where(rng.random(n) < 0.5, -1.0, 1.0).astype(np.float32)
    d = dict(tx=tx, ty=ty, side=side, x0=(W / 2 + side * rng.uniform(W * 0.62, W * 1.05, n)).astype(np.float32),
             y0=rng.uniform(820, 1650, n).astype(np.float32), vf=rng.uniform(380, 900, n).astype(np.float32),
             delay=rng.uniform(0, 0.28, n).astype(np.float32),
             size=rng.uniform(18, 32, n).astype(np.float32), ar=rng.uniform(0.40, 0.70, n).astype(np.float32),
             a0=rng.uniform(0, 360, n).astype(np.float32), wa=rng.uniform(-240, 240, n).astype(np.float32),
             b0=rng.uniform(0, 6.28, n).astype(np.float32), wb=rng.uniform(5, 13, n).astype(np.float32),
             col=rng.choice([1, 1, 2, 2, 1, 0, 0, 5], n), sw=rng.uniform(-1, 1, n).astype(np.float32),
             bv=rng.uniform(0.8, 1.3, n).astype(np.float32))
    _NL["t"] = d; return d

def draw_pieces(out, px, py, size, ang, flut, cols, alpha=None, blur_big=True):
    """lit paper pieces (fluttering quads), far/near layers; size in px, ang in radians, flut = cos of the flutter."""
    lay = [np.zeros((H, W, 3), np.uint8), np.zeros((H, W, 3), np.uint8)]; al = [np.zeros((H, W), np.uint8), np.zeros((H, W), np.uint8)]
    for i in np.argsort(size):
        x, y, sz = px[i], py[i], size[i]
        if x < -sz or x > W + sz or y < -sz or y > H + sz or (alpha is not None and alpha[i] < 0.02): continue
        hw, hh = sz * 0.5, sz * 0.5 * 0.55 * max(0.10, abs(flut[i]))
        ca, sa_ = math.cos(ang[i]), math.sin(ang[i])
        pts = np.array([[x + ca * dx - sa_ * dy, y + sa_ * dx + ca * dy] for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))], np.float32)
        bright = 0.60 + 0.40 * abs(flut[i]) + (0.45 if abs(flut[i]) > 0.97 else 0.0)
        col = np.clip(CONF_COLS[cols[i]] * bright, 0, 1); a8 = int(255 * (1.0 if alpha is None else alpha[i]))
        L = 1 if (blur_big and sz > 70) else 0
        cv2.fillConvexPoly(lay[L], (pts * 4).astype(np.int32), tuple(int(c * 255) for c in col), cv2.LINE_AA, 2)
        cv2.fillConvexPoly(al[L], (pts * 4).astype(np.int32), a8, cv2.LINE_AA, 2)
    o = out
    for L, bl in ((0, 0.0), (1, 3.0)):
        if not al[L].any(): continue
        Lf = lay[L].astype(np.float32) / 255; Af = al[L].astype(np.float32) / 255
        if bl: Lf = cv2.GaussianBlur(Lf, (0, 0), bl); Af = cv2.GaussianBlur(Af, (0, 0), bl)
        o = o * (1 - Af[..., None]) + Lf * Af[..., None]
    return o

def name_loop(out, f, s):
    t = f / FPS; e = t / E.HB
    if e < NL_G0 - 1.5: return out
    d = name_targets(); tg0, tg1, tb, T = E.th(NL_G0), E.th(NL_G1), E.th(NL_B), E.DUR
    # the pieces fall in from above the frame, then gather into the letters (staggered, with a curl)
    tf = t - (tg0 - 1.0)
    fx_ = d["x0"] - d["side"] * d["vf"] * 0.55 * tf; fy_ = d["y0"] + 60 * np.sin(1.7 * tf + d["b0"])     # drifting in from the sides
    w = np.clip((t - tg0 - d["delay"]) / (tg1 - tg0 - 0.28), 0, 1); we = w * w * (3 - 2 * w)
    curl = np.sin(np.pi * we) * 90 * d["sw"]
    px = fx_ + (d["tx"] - fx_) * we + curl; py = fy_ + (d["ty"] - fy_) * we
    ang = np.radians(d["a0"] + d["wa"] * t * (1 - 0.75 * we)); flut = np.cos(d["b0"] + d["wb"] * t)
    size = d["size"].copy(); alpha = None
    plate = out
    hold = smooth((t - tg0 - 0.3) / 0.5) * (1 - smooth((t - tb) / 0.25))
    if hold > 0:                                                                          # the parade steps back so the name reads
        soft = cv2.GaussianBlur(cv2.resize(out, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 2.5)
        plate = out * (1 - 0.45 * hold) + cv2.resize(soft, (W, H)) * (0.45 * hold)
        plate = plate * (1 - 0.30 * hold)
    if t >= tb:                                                                           # the burst: toward the lens and out
        b = clamp((t - tb) / (T - tb - 0.06), 0, 1); be = b ** 1.6
        dx, dy = d["tx"] - W / 2, d["ty"] - 1110
        px = d["tx"] + dx * 3.2 * be * d["bv"] + d["sw"] * 160 * be; py = d["ty"] + np.abs(dy) * 3.0 * be * d["bv"] + 260 * be
        size = d["size"] * (1 + 9 * be * d["bv"])
        alpha = np.clip(1 - (b - 0.55) / 0.40, 0, 1) * np.ones_like(size)
        wz = smooth((t - tb - 0.02) / 0.30)                                               # under it: frame 0
        if wz > 0: plate = plate * (1 - wz) + frame0_plate() * wz
    o = draw_pieces(plate, px, py, size, ang, flut, d["col"], alpha)
    if t > T - 0.08: o = o * 0 + frame0_plate() if t > T - 1.5 / FPS else o                 # the last frame is frame 0's picture
    return np.clip(o, 0, 1)

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base107(s, f)
    out = text107(out, f, s, True)
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge107(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge107(n_, "first"), kn, f, s, n_)
    if s.get("tout") == "name_loop": out = name_loop(out, f, s)
    out = beat_fx(out, f)
    out = text107(out, f, s, False)
    out = flash_governor(out)
    return (np.clip(finish107(out, f, s), 0, 1) * 255 + 0.5).astype(np.uint8)

# ============================================================================ v107 rev 3 (owner notes; overrides above)
# ---- DEXTER on the 16th grid: each letter lands ON its hit (the platen comes down in the 3 frames before) -------------
STAMP_DROP = 3
def strip_canvas(t, stamps):
    """the strip (rgba, its own pixel space) with the letters stamped by time t."""
    base = strip_tex().copy(); inks, xs = _ST["lets"]; h, w = base.shape[:2]
    for (wd, tw), m, xc in zip(stamps, inks, xs):
        k = (t - tw) * FPS + STAMP_DROP
        if k < 0: continue
        v = clamp(k / STAMP_DROP, 0, 1)
        if v < 1:                                                                          # the stamp coming down
            sc = 1.6 - 0.6 * ein(v, 2.0); mm = cv2.resize(m, None, fx=sc, fy=sc); mm = cv2.GaussianBlur(mm, (0, 0), 0.1 + 4 * (1 - v)) * (0.35 + 0.65 * v)
        else: mm = m
        hh, ww = mm.shape; x0 = int(xc - ww / 2); y0 = int(h / 2 - hh / 2 + 6)
        ys, xs_ = slice(max(0, y0), min(h, y0 + hh)), slice(max(0, x0), min(w, x0 + ww))
        sub = mm[ys.start - y0:ys.stop - y0, xs_.start - x0:xs_.stop - x0]
        if v >= 1:                                                                         # the deboss: pressed into the paper
            dm = cv2.GaussianBlur(sub, (0, 0), 2.0)
            sh = np.clip(np.roll(dm, 3, 0) - dm, 0, 1) * 0.35; hl = np.clip(np.roll(dm, -3, 0) - dm, 0, 1) * 0.10
            base[ys, xs_, :3] *= (1 - sh)[..., None]; base[ys, xs_, :3] += hl[..., None]
            sub = np.clip(sub * (1 + 0.10 * math.exp(-(k - STAMP_DROP) / 3)), 0, 1)           # ink spreads at the hit, then settles
        base[ys, xs_, :3] = base[ys, xs_, :3] * (1 - sub[..., None]) + INK * sub[..., None]
    return base

def text_stamp(out, f, tx):
    t = f / FPS; stamps = [(w, wt) for w, wt, _ in tx["words"]]
    t_in = next(wt for tx_ in E.TEXT if tx_["style"] == "cap" for w_, wt, _ in tx_["words"] if w_ == "CAPS") - 0.02   # it slaps on with "CAPS"
    t_cut = E.th(48); t_end = t_cut + 0.80
    if t < t_in or t > t_end: return out
    rgba = strip_canvas(min(t, t_cut + 0.2), stamps)
    k = (t - t_in) * FPS; v = clamp(k / 5.0, 0, 1)
    sc = 1.28 - 0.28 * eout(v, 3) + (0.02 * math.sin(k * 0.9) * math.exp(-k / 6) if v >= 1 else 0)
    cx, cy = STRIP_C; rot = STRIP_ROT; a = min(1.0, k / 3.0); shake = 0.0
    for _, tw in stamps:                                                                   # each hit shakes the strip
        dk = (t - tw) * FPS
        if 0 <= dk < 8: shake = max(shake, 5 * math.exp(-dk / 2.5))
    cy += shake * math.sin(f * 2.1)
    if t > t_cut - 0.02:                                                                   # it flies into the sky onto the banner
        w_ = smooth((t - t_cut + 0.02) / 0.45)
        (bx, by), bs, br = banner_target()
        cx, cy = cx + (bx - cx) * w_, cy + (by - cy) * w_; sc = sc + (bs - sc) * w_; rot = rot + (br - rot) * w_
        a = a * (1 - smooth((t - t_cut - 0.42) / 0.36))
    return put_strip(out, rgba, cx, cy, sc, rot, a, 0.45 * (1 - smooth((t - t_cut) / 0.3)))

# ---- SPATTER ANALYSIS (new graphic, the kill table): blood spatters across the lens, strings run back from every
# ---- stain along its flight line and lock on the beat at the POINT OF ORIGIN, where his face is about to appear --------
SP_F0, SP_STR, SP_LOCK = 99, 106, 124                                                      # the spatter, the strings, the lock (e6)
BLOOD_HI = np.array([0.08, 0.06, 0.66], np.float32); BLOOD_LO = np.array([0.02, 0.01, 0.20], np.float32)
STRING_C = np.array([0.17, 0.16, 0.93], np.float32)
_SP = {}
def sp_origin():
    if "o" not in _SP:
        sb = [s_ for s_ in SHOTS if s_["n"] == "shh"][0]; fs = face_scr(sb, sb["f0"])
        _SP["o"] = (float(fs[0]), float(fs[1])) if fs else (W / 2, 640.0)
    return _SP["o"]

def sp_geom():
    if "g" in _SP: return _SP["g"]
    ox, oy = sp_origin(); rng = np.random.default_rng(1077)
    spec = [(-160, 430, 24, 28), (-125, 360, 18, 40), (-75, 440, 22, 24), (-35, 330, 26, 35), (-5, 420, 16, 20),
            (30, 360, 20, 46), (70, 310, 15, 38), (110, 330, 14, 50), (150, 300, 17, 33), (175, 380, 21, 22)]
    drops = []
    for i, (th_, r, w, al) in enumerate(spec):
        w = w * 1.7; a = math.radians(th_); ux, uy = math.cos(a), math.sin(a); L = w / math.sin(math.radians(al))
        sats = list(zip(rng.uniform(1.15, 2.0, 3) * L, rng.uniform(2.6, 6.0, 3), rng.uniform(-0.25, 0.25, 3)))
        drops.append(dict(x=ox + r * ux, y=oy + r * uy, ux=ux, uy=uy, w=w, L=L, al=al, sats=sats,
                          t=SP_F0 + int(rng.integers(0, 6)), s=SP_STR + 2 * i, lab=i in (0, 3, 5, 8)))
    ang = rng.uniform(-math.pi, math.pi, 70); rr = rng.uniform(170, 560, 70)
    mist = [(ox + q * math.cos(a), oy + q * math.sin(a), rad, SP_F0 + int(dt)) for a, q, rad, dt in
            zip(ang, rr, rng.uniform(1.8, 4.8, 70), rng.integers(0, 7, 70)) if oy + q * math.sin(a) < 1200]
    _SP["g"] = (drops, mist); return _SP["g"]

def sp_text(key, txt, size, col):
    if key not in _SP: _SP[key] = shadowed(text_mask(txt, F_MONO, size), col, blur=4, sa=0.8)
    return _SP[key]

def paste_rgba(out, rg, x, y, a=1.0):
    h, w = rg.shape[:2]; x0, y0 = int(round(x)), int(round(y))
    ys, xs = slice(max(0, y0), min(H, y0 + h)), slice(max(0, x0), min(W, x0 + w))
    if ys.stop <= ys.start or xs.stop <= xs.start: return out
    sub = rg[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0]; al = sub[..., 3:4] * a
    out[ys, xs] = out[ys, xs] * (1 - al) + sub[..., :3] * al
    return out

SS = 16                                                                                    # cv2 sub-pixel shift (4 bits)
def P_(x, y): return (int(round(x * SS)), int(round(y * SS)))

def spatter_fx(img, f):
    if f < SP_F0: return img
    drops, mist = sp_geom(); ox, oy = sp_origin(); out = img.copy()
    # the blood on the lens: elongated stains (round head, body along the flight line, a tapering tail), satellites, mist
    m = np.zeros((H, W), np.uint8)
    for d in drops:
        if f < d["t"]: continue
        g = eout(clamp((f - d["t"] + 1) / 3.0, 0, 1), 2)
        L = d["w"] + (d["L"] - d["w"]) * g; ang = math.degrees(math.atan2(d["uy"], d["ux"]))
        cx, cy = d["x"] + d["ux"] * (L / 2 - d["w"] / 2), d["y"] + d["uy"] * (L / 2 - d["w"] / 2)
        cv2.ellipse(m, P_(cx, cy), P_(L / 2, d["w"] / 2), ang, 0, 360, 255, -1, cv2.LINE_AA, 4)
        tx_, ty_ = d["x"] + d["ux"] * (L - d["w"] * 0.6), d["y"] + d["uy"] * (L - d["w"] * 0.6)
        ex, ey = tx_ + d["ux"] * 0.55 * L * g, ty_ + d["uy"] * 0.55 * L * g; px_, py_ = -d["uy"], d["ux"]; hw = d["w"] * 0.30
        tri = np.array([P_(tx_ + px_ * hw, ty_ + py_ * hw), P_(tx_ - px_ * hw, ty_ - py_ * hw), P_(ex, ey)], np.int32)
        cv2.fillConvexPoly(m, tri, 255, cv2.LINE_AA, 4)
        for dd, rad, side in d["sats"]:
            sx, sy = d["x"] + (d["ux"] + side * px_) * dd * g, d["y"] + (d["uy"] + side * py_) * dd * g
            cv2.circle(m, P_(sx, sy), int(rad * SS), 255, -1, cv2.LINE_AA, 4)
    for x, y, rad, t_ in mist:
        if f >= t_: cv2.circle(m, P_(x, y), int(rad * SS), 255, -1, cv2.LINE_AA, 4)
    M = m.astype(np.float32) / 255
    inner = cv2.GaussianBlur(M, (0, 0), 3.0)
    col = BLOOD_LO + (BLOOD_HI - BLOOD_LO) * np.clip(inner * 1.3, 0, 1)[..., None]
    hgt = cv2.GaussianBlur(M, (0, 0), 2.2); gx = cv2.Sobel(hgt, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(hgt, cv2.CV_32F, 0, 1, ksize=3)
    spec = np.clip((-gx * 0.55 - gy * 0.85) * 2.4, 0, 1) ** 2 * M * 0.75
    out = out * (1 - M[..., None]) + col * M[..., None] + spec[..., None] * PAPER
    # the strings: taut red string from each stain's head back along its flight line (a pin at the stain)
    sm = np.zeros((H, W), np.uint8); sh = np.zeros((H, W), np.uint8); pins = []
    for d in drops:
        if f < d["s"]: continue
        p = eout(clamp((f - d["s"]) / 9.0, 0, 1), 2.2)
        ex, ey = d["x"] + (ox - d["x"]) * p, d["y"] + (oy - d["y"]) * p
        cv2.line(sm, P_(d["x"], d["y"]), P_(ex, ey), 255, 5, cv2.LINE_AA, 4)
        cv2.line(sh, P_(d["x"] + 4, d["y"] + 5), P_(ex + 4, ey + 5), 255, 5, cv2.LINE_AA, 4)
        pins.append(d)
    if pins:
        S_ = cv2.GaussianBlur(sh.astype(np.float32) / 255, (0, 0), 1.6) * 0.45
        out = out * (1 - S_[..., None])
        Sm = sm.astype(np.float32) / 255
        out = out * (1 - Sm[..., None]) + STRING_C * Sm[..., None]
        for d in pins:
            cv2.circle(out, P_(d["x"], d["y"]), 10 * SS, tuple(float(v) for v in INK), -1, cv2.LINE_AA, 4)
            cv2.circle(out, P_(d["x"] - 3, d["y"] - 3), 3 * SS, tuple(float(v) for v in PAPER), -1, cv2.LINE_AA, 4)
            if d["lab"]:                                                                   # the impact angle, read off the stain
                rg = sp_text(f"al{d['al']}", f"{d['al']}\u00b0", 46, PAPER)
                px_, py_ = -d["uy"], d["ux"]; side = 1 if (d["x"] + px_ * 40) > ox else -1
                lx = d["x"] + side * px_ * (d["w"] + 46) - rg.shape[1] / 2; ly = d["y"] + side * py_ * (d["w"] + 46) - rg.shape[0] / 2
                out = paste_rgba(out, rg, lx, ly, smooth((f - d["s"] - 2) / 5.0))
    # the lock: a ring with a crosshair at the point of origin, a pulse, and the tag
    if f >= SP_LOCK:
        q = f - SP_LOCK; sc = eout(clamp(q / 6.0, 0, 1), 3); r = 48 * (1.6 - 0.6 * sc)
        lay = np.zeros((H, W), np.uint8)
        cv2.circle(lay, P_(ox, oy), int(r * SS), 255, 5, cv2.LINE_AA, 4)
        for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            cv2.line(lay, P_(ox + ddx * (r + 8), oy + ddy * (r + 8)), P_(ox + ddx * (r + 32), oy + ddy * (r + 32)), 255, 5, cv2.LINE_AA, 4)
        tgx, tgy = ox + 40, oy - 440
        cv2.line(lay, P_(ox + r * 0.72, oy - r * 0.72), P_(tgx + 30, tgy + 80), 255, 3, cv2.LINE_AA, 4)
        La = lay.astype(np.float32) / 255 * sc
        out = out * (1 - La[..., None]) + PAPER * La[..., None]
        cv2.circle(out, P_(ox, oy), 9 * SS, tuple(float(v) for v in STRING_C), -1, cv2.LINE_AA, 4)
        if q < 12:                                                                         # the pulse
            pr = np.zeros((H, W), np.uint8); cv2.circle(pr, P_(ox, oy), int((r + 70 * eout(q / 12, 2)) * SS), 255, 2, cv2.LINE_AA, 4)
            out = out + (pr.astype(np.float32) / 255 * 0.6 * (1 - q / 12))[..., None] * PAPER
        n = int(clamp((q - 2) * 2.2, 0, 15))
        if n > 0:                                                                          # POINT OF ORIGIN, typed on a paper tag
            txt = "POINT OF ORIGIN"[:n]
            if "tagm" not in _SP: _SP["tagm"] = text_mask("POINT OF ORIGIN", F_MONO, 48)
            rg = shadowed(text_mask(txt, F_MONO, 48), INK, blur=1, sa=0.0)            # padded by 7 px
            tw_, th2 = _SP["tagm"].shape[1] + 28, _SP["tagm"].shape[0] + 18
            x0, y0 = int(tgx), int(tgy)
            out[y0 + 6:y0 + th2 + 6, x0 + 5:x0 + tw_ + 5] *= 0.55                          # the tag's shadow
            out[y0:y0 + th2, x0:x0 + tw_] = PAPER * 0.97
            out[y0 + th2 - 4:y0 + th2, x0:x0 + tw_] = STRING_C                              # a red rule under the type
            out = paste_rgba(out, rg, x0 + 14 - 7, y0 + 9 - 7, 1.0)
    return np.clip(out, 0, 1)

_base107_r2 = base107
def base107(s, f):
    img, person = _base107_r2(s, f)
    if s["n"] == "table": img = spatter_fx(img, f)
    return img, person

# ---- RORSCHACH (the 3 s transition): from the point of origin a blood-ink blot blooms, mirrored about the fold like an
# ---- inkblot card; inside it his face appears mirrored (both of him), the blot floods the frame, the mirrored half of the
# ---- card swings open on the fold and the real shot is underneath. Full frame: no bars, no box. ---------------------------
RO_PRE, RO_POST = 21, 30
RO_BLOBS = [(0, 0, 95), (0, 110, 70), (0, -120, 60), (45, -190, 30), (150, -60, 95), (280, -120, 80), (400, -190, 62),
            (500, -230, 42), (560, -170, 30), (200, 70, 80), (330, 60, 62), (440, 20, 48), (520, -40, 36), (260, 160, 42),
            (390, 140, 34), (55, 210, 34), (70, 270, 20), (610, -110, 18), (150, 300, 14)]
INKB = np.array([0.03, 0.02, 0.24], np.float32)
_RO = {}
def ro_grids():
    if "g" not in _RO:
        ox, oy = sp_origin(); rng = np.random.default_rng(1078)
        X, Y = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
        AX = np.abs(X - ox); DY = Y - oy
        n1 = cv2.resize(rng.random((H // 40 + 2, W // 40 + 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        n2 = cv2.resize(rng.random((H // 10 + 2, W // 10 + 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        nz = 0.6 * n1 + 0.4 * n2
        xi = np.clip(ox + AX, 0, W - 1).astype(np.int32); nz = nz[np.arange(H)[:, None], xi]    # symmetric about the fold
        mx = np.where(X > ox, 2 * ox - X, X).astype(np.float32)                                  # the mirror map
        _RO["g"] = (AX, DY, nz, mx, Y)
    return _RO["g"]

def ro_mask(grow, flood=0.0):
    AX, DY, nz, _, _ = ro_grids(); F = np.zeros((H, W), np.float32)
    for bx, by, r in RO_BLOBS:
        bx, by, r = bx * 0.72, by * 1.25, r * 0.85                                          # a card: it fits the frame
        dist = math.hypot(bx, by); g = eout(clamp((grow - dist / 700 * 0.55) / 0.45, 0, 1), 2.5)
        rr = r * g * (1 + 2.2 * ein(clamp(flood / 0.5, 0, 1), 1.6))
        if rr > 0.5: F += rr * rr / ((AX - bx) ** 2 + (DY - by) ** 2 + 1.0)
    if flood > 0:
        rc = 1450 * eout(clamp(flood / 0.5, 0, 1), 1.8); F += rc * rc / (AX ** 2 + DY ** 2 + 1.0)
    F = F * (0.86 + 0.28 * nz)
    return cv2.GaussianBlur((F > 1.0).astype(np.float32), (0, 0), 1.1)

def mirror(img):
    _, _, _, mx, Y = ro_grids()
    return cv2.remap(img, mx, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def ink_comp(A, content, m, clear):
    inner = cv2.GaussianBlur(m, (0, 0), 14); rim = np.clip((m - inner) * 3.2, 0, 1)
    dens = np.maximum(rim, 1 - clear) * m
    ins = content * (1 - 0.92 * dens[..., None]) + INKB * 0.92 * dens[..., None]
    hgt = cv2.GaussianBlur(m, (0, 0), 5.0); gx = cv2.Sobel(hgt, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(hgt, cv2.CV_32F, 0, 1, ksize=3)
    spec = np.clip((-gx * 0.55 - gy * 0.85) * 5.0, 0, 1) ** 2 * m * 0.55
    halo = np.clip(cv2.GaussianBlur(m, (0, 0), 3.0) - m, 0, 1) * 0.7                       # the ink bleeds into the paper
    out = A * (1 - halo[..., None]) * (1 - m[..., None]) + ins * m[..., None] + spec[..., None] * PAPER
    return np.clip(out, 0, 1)

def unfold(Bm, B, phi):
    """the mirrored half of the card (right of the fold) swings away on the fold; the real shot is underneath."""
    ox, _ = sp_origin(); D = 1700.0; s = W - ox
    if phi >= math.pi / 2 - 1e-3: return B
    Z = s * math.sin(phi); k = D / (D + Z); xf = ox + s * math.cos(phi) * k
    src = np.float32([[ox, 0], [W, 0], [W, H], [ox, H]]); dst = np.float32([[ox, 0], [xf, H / 2 - H / 2 * k], [xf, H / 2 + H / 2 * k], [ox, H]])
    Mp = cv2.getPerspectiveTransform(src, dst)
    pg = cv2.warpPerspective(Bm, Mp, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    pm = np.zeros((H, W), np.float32); pm[:, int(ox):] = 1
    pm = cv2.warpPerspective(pm, Mp, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    shade = 1 - 0.55 * math.sin(phi); pm = pm * (1 - smooth((phi - math.radians(55)) / math.radians(30)))   # gone before it is edge-on
    shadow = np.clip(1 - np.abs(np.arange(W, dtype=np.float32) - xf) / 160, 0, 1) * 0.35 * math.sin(phi)   # the card's shadow
    base = B * (1 - shadow[None, :, None] * (np.arange(W) > ox)[None, :, None])
    return np.clip(base * (1 - pm[..., None]) + pg * shade * pm[..., None], 0, 1)

def rorschach(A, B, j, f, sa, sb, pre=RO_PRE, post=RO_POST):
    if j < 0:
        u = (j + pre + 1) / pre
        m = ro_mask(u); return ink_comp(A, mirror(B), m, smooth((u - 0.10) / 0.55))
    v = (j + 1) / post; Bm = mirror(B)
    if v < 0.5:
        m = ro_mask(1.0, v); return ink_comp(A, Bm, m, 1.0)
    return unfold(Bm, B, math.pi / 2 * smooth((v - 0.5) / 0.45))
TR2["rorschach"] = (rorschach, RO_PRE, RO_POST)

# ============================================================================ v107 rev 4 (owner notes; overrides above)
# ---- the POINT OF ORIGIN piece is gone: the kill table plays clean and cuts to "shh" on the downbeat ------------------
base107 = _base107_r2                                                                       # no spatter analysis
def beat_phase(f):                                                                          # the beat camera punches the e8 cut again
    e = f / FPS / E.HB; ph = (e % 2) * E.HB; bi = int(e // 2)
    hook = (E.E_BEAT <= e < 54) and not (19 <= e < 23) and not (24 <= e < 28.5) and not (47 <= e < 50)
    return ph, bi, hook, False

# ---- PAGE TURN ("shh" -> the lab, replaces the redaction boxes): the frame is a page of the paper. It lifts at the
# ---- bottom-right corner and rolls over a cylinder; its back is newsprint with the picture showing through; it lies
# ---- over itself as it turns, casts a shadow on the lab shot underneath, and clears off the top-left corner. ------------
PT_PRE, PT_POST = 14, 12
_PT = {}
def pt_back():
    """the back of the page: newsprint (three columns of body type, rules) on the paper."""
    if "b" in _PT: return _PT["b"]
    paper, _, _ = page_layers(); ink = np.zeros((H, W), np.float32); rng = np.random.default_rng(1079)
    words = ("residents were told to lock their doors as the task force widened the search along the bay and the "
             "department asked anyone who saw a boat leave the marina after dark to call the tip line divers recovered "
             "more bags from the water on monday and the medical examiner said the work was careful and practised").split()
    cols = [(60, 352), (394, 686), (728, 1020)]
    for ci, (x0, x1) in enumerate(cols):
        y = 90 + (60 if ci == 1 else 0); wi = int(rng.integers(len(words)))
        while y < H - 90:
            if rng.random() < 0.05:
                m = text_mask(" ".join(words[wi % len(words):wi % len(words) + 3]).upper(), F_XB, 34); put_mask(ink, squeeze(m, min(1.0, (x1 - x0) / m.shape[1])), x0, y)
                y += 58; wi += 3; continue
            line = []; wsum = 0
            while True:
                w = words[wi % len(words)]; wi += 1; tw = len(w) * 11 + 9
                if wsum + tw > (x1 - x0): break
                line.append(w); wsum += tw
            m = text_mask(" ".join(line), F_BODY, 21); put_mask(ink, squeeze(m, min(1.0, (x1 - x0) / m.shape[1])), x0, y)
            y += 29
        if ci < 2: cv2.line(ink, (x1 + 21, 90), (x1 + 21, H - 90), 0.7, 1)
    cv2.line(ink, (60, 64), (W - 60, 64), 1.0, 2)
    _PT["b"] = (paper, ink); return _PT["b"]

def page_turn107(A, B, j, f, sa, sb, pre=PT_PRE, post=PT_POST):
    u = clamp((j + pre + 0.5) / (pre + post), 0, 1)
    d = np.array([-0.62, -0.785], np.float32); d /= np.linalg.norm(d)                       # from the bottom-right corner to the top-left
    s_ = (_GX - W) * d[0] + (_GY - H) * d[1]; smax = float(W * -d[0] + H * -d[1])
    R = 60 + 70 * u; c = (smax + 1.7 * R + 60) * (0.5 - 0.5 * math.cos(math.pi * u ** 1.15))  # the roll line, easing in and out
    def src(sig):                                                                            # screen point -> the page point at sigma
        return (_GX + (sig - s_) * d[0]).astype(np.float32), (_GY + (sig - s_) * d[1]).astype(np.float32)
    def inside(mx, my): return (mx >= 0) & (mx <= W - 1) & (my >= 0) & (my <= H - 1)
    paper, ink = pt_back()
    def back_at(mx, my, shade):
        pa = cv2.remap(paper, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        ik = cv2.remap(ink, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)[..., None]
        thru = cv2.remap(A, (W - 1 - mx).astype(np.float32), my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)   # show-through, mirrored
        b = pa * (1 - 0.10 * (1 - lum(thru))[..., None]) * (1 - ik * 0.88) + INK * ik * 0.88
        return b * shade[..., None]
    o = B.copy()
    # 1. the flat page (front) beyond the roll line
    flat = s_ > c
    o = np.where(flat[..., None], A, o)
    # 2. the rising quarter of the roll (front side, seen foreshortened)
    cyl = (s_ <= c) & (s_ >= c - R)
    th1 = np.arcsin(np.clip((c - s_) / R, 0, 1)); mx, my = src(c - R * th1); ok1 = cyl & inside(mx, my)
    fr = cv2.remap(A, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT) * (0.55 + 0.45 * np.cos(th1))[..., None]
    o = np.where(ok1[..., None], fr, o)
    # 3. the top half of the roll (its back, on top of the rising quarter)
    th2 = np.pi - th1; mx2, my2 = src(c - R * th2); ok2 = cyl & inside(mx2, my2)
    bk = back_at(mx2, my2, (0.80 + 0.22 * np.sin(th2)).astype(np.float32))
    o = np.where(ok2[..., None], bk, o)
    # 4. the turned-over part lying flat on top of the page (its back), beyond the roll line
    sig3 = 2 * c - np.pi * R - s_; mx3, my3 = src(sig3); ok3 = flat & (sig3 <= c - np.pi * R) & inside(mx3, my3)
    bk3 = back_at(mx3, my3, np.full((H, W), 0.93, np.float32))
    o = np.where(ok3[..., None], bk3, o)
    # shadows: the roll on the lab shot underneath, the flap's edge on the page
    uncov = s_ < c - R
    sh1 = np.exp(-np.clip((c - R) - s_, 0, None) / 46) * uncov * 0.55 * (c > 2)
    edge3 = ok3.astype(np.float32); sh2 = np.clip(cv2.GaussianBlur(edge3, (0, 0), 14) - edge3, 0, 1) * flat * (~ok3) * 0.9
    o = o * (1 - sh1[..., None]) * (1 - sh2[..., None])
    return np.clip(o, 0, 1)
TR2["page_turn107"] = (page_turn107, PT_PRE, PT_POST)

# ---- the colour split on the beat hits clamps at the frame edge (np.roll wrapped it: a cyan / magenta line on the edges)
def _shift_edge(ch, d, axis):
    if d == 0: return ch
    o = np.empty_like(ch); n = ch.shape[axis]; d = max(-n + 1, min(n - 1, d))
    src = [slice(None)] * ch.ndim; dst = [slice(None)] * ch.ndim; pad = [slice(None)] * ch.ndim; edge = [slice(None)] * ch.ndim
    if d > 0:
        dst[axis], src[axis], pad[axis], edge[axis] = slice(d, None), slice(0, n - d), slice(0, d), slice(0, 1)
    else:
        dst[axis], src[axis], pad[axis], edge[axis] = slice(0, n + d), slice(-d, None), slice(n + d, None), slice(n - 1, n)
    o[tuple(dst)] = ch[tuple(src)]; o[tuple(pad)] = ch[tuple(edge)]
    return o

def rgb_split(img, d, vertical=False):
    d = int(round(d))
    if d == 0: return img
    o = img.copy(); ax = 0 if vertical else 1
    o[..., 2] = _shift_edge(img[..., 2], d, ax); o[..., 0] = _shift_edge(img[..., 0], -d, ax)
    return o

# >>> pipeline v2: speed   (an edit's own sections go ABOVE this line: tools/splice_section.py)
# ============================================================================ pipeline v2: speed (WP2), same pictures
# Nothing in this section changes the look. Every item is checked against the shipped v11 frames with
# `python3 tools/golden.py 11 --check` (gate: max 2/255 per pixel, mean < 0.2/255). See sync/PIPELINE_V2_PLAN.md.
#   1. TONE LUT    the per-channel gain -> gamma -> exposure -> tone-curve chain of a grade becomes one 65,536-entry
#                  lookup per channel (np.interp on a full band cost ~280 ms; the lookup ~25 ms; error < 0.01/255).
#                  New edits: build their grade on `tone_lut` / `apply_lut3` (docs/TOOLKIT.md, pipeline v2).
#   2. STILL CACHE the unshaken shot renders that afterimages / time slices / transitions ask for are cached per worker
#                  (read-only arrays, so an in-place change to a cached frame fails loudly instead of corrupting it).
#   3. BLOCKS      workers render contiguous blocks that never cross a cut (render_blocks), so every per-worker cache
#                  (restored bands, flow pairs, edge frames, the still cache) hits; output order is unchanged.
_TLUT = {}
def tone_lut(key, gains, g, ev, lx, ly):
    """(3, 65536) table: clip(u * gain_c) ** g, then * 2 ** ev (clipped), then the tone curve (lx, ly); u = i / 65535."""
    if key not in _TLUT:
        if len(_TLUT) > 96: _TLUT.clear()
        u = np.arange(65536, dtype=np.float32) / 65535; tabs = []
        for c in range(3):
            x = np.clip(u * gains[c], 0, 1) ** g
            if ev: x = np.clip(x * 2 ** ev, 0, 1)
            tabs.append(np.interp(x, lx, ly).astype(np.float32))
        _TLUT[key] = np.stack(tabs)
    return _TLUT[key]

def apply_lut3(img, tab):
    """per-channel lookup of a float image in [0, 1] (quantised to 1/65535 before the lookup)."""
    q = np.clip(img, 0, 1); q *= 65535; q += 0.5; idx = q.astype(np.uint16)
    out = np.empty(img.shape, np.float32)
    for c in range(3): np.take(tab[c], idx[..., c], out=out[..., c])
    return out

def in_unit(img): return img.dtype == np.float32 and img.ndim == 3 and img.shape[2] == 3 and float(img.min()) >= 0.0 and float(img.max()) <= 1.0

_grade_v11_ref = grade
def grade(img, s, f):
    lk = s.get("look")
    if lk not in ("voltage", "rival") or not in_unit(img): return _grade_v11_ref(img, s, f)
    g, gains = corr9(s); ev = s.get("ev") or 0
    lx, ly = lut11(lk)
    x = apply_lut3(img, tone_lut((lk, s["n"], ev, float(g), tuple(float(v) for v in gains)), gains, g, ev, lx, ly))
    Bc, Gc, Rc = x[..., 0], x[..., 1], x[..., 2]                                         # from here: as the v11 grade
    L = (Bc * 0.114 + Gc * 0.587 + Rc * 0.299)[..., None]
    red = np.clip((Rc - np.maximum(Gc, Bc) * 1.25) * 3.0, 0, 1)[..., None]
    light = np.clip((L - 0.62) * 3.0, 0, 1) * np.clip((Rc - Bc) * 3.0, 0, 1)[..., None]
    hue = (Rc - Gc) / (Rc + 1e-3)
    skin = (np.clip(1 - np.abs(hue - 0.22) / 0.22, 0, 1) * np.clip((Rc - Bc) * 6, 0, 1) * np.clip(L[..., 0] * 3, 0, 1))[..., None]
    sat = 0.84 + 0.32 * red + 0.25 * light + 0.10 * skin
    x = L + (x - L) * sat
    sh = (1 - L) ** 2.6 * (1 - 0.7 * skin) * (1 - red)
    hi = np.clip((L - 0.55) * 2.2, 0, 1) * (1 - skin * 0.6)
    if lk == "voltage":
        x = x + sh * TEALS + hi * np.array([-0.018, 0.010, 0.035], np.float32)
    else:
        x = x + sh * np.array([0.000, -0.006, 0.022], np.float32) + hi * np.array([-0.030, -0.018, 0.045], np.float32)
        x = x * np.array([0.94, 0.95, 1.04], np.float32)
    return np.clip(x, 0, 1)

#   4. CHANNELS    numpy's `a[..., None] * colour` broadcast is ~3x slower than writing each channel; the hot effects
#                  (light layers, finish, anamorphic streaks, motes, the grade's last stage) write channels directly.
#   5. FACE MASK   motes11's blurred "nothing in front of his face" mask (a 78 ms full-frame blur, sigma 25, every frame)
#                  is built from 1-D blurs: the mask is a column profile times a row profile plus a few ramp rows, and
#                  a Gaussian blur of that is exact up to float rounding (max 7e-7).
F32 = np.float32
def mul3(a, col, k=1.0, out=None):
    """(a[..., None] * col) * k as an HxWx3 array, channel by channel (same values, faster)."""
    o = np.empty(a.shape + (3,), F32) if out is None else out
    for c in range(3):
        oc = o[..., c]; np.multiply(a, col[c], out=oc)
        if k != 1.0: oc *= k
    return o

def light_rgb(cv, a, core, glow):
    c = cv.astype(F32) / 255
    sm = cv2.resize(c, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    g = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 3) * 2.6 + cv2.GaussianBlur(sm, (0, 0), 11) * 3.4, (W, H), interpolation=cv2.INTER_LINEAR)
    np.clip(g, 0, 1.6, out=g)
    o = np.empty((H, W, 3), F32); t = np.empty((H, W), F32)
    for ch in range(3):
        np.multiply(g, glow[ch], out=t); t *= 0.85
        oc = o[..., ch]; np.multiply(c, core[ch], out=oc); oc *= 1.15; oc += t; oc *= a
    return o

def light_from(cv, a=1.0, col=None):
    c = cv.astype(F32) / 255
    small = cv2.resize(c, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    glow = cv2.resize(cv2.GaussianBlur(small, (0, 0), 3) * 2.6 + cv2.GaussianBlur(small, (0, 0), 11) * 3.4, (W, H), interpolation=cv2.INTER_LINEAR)
    col = GOLD2 if col is None else col
    np.clip(glow, 0, 1.6, out=glow)
    o = np.empty((H, W, 3), F32); t = np.empty((H, W), F32)
    for ch in range(3):
        np.multiply(glow, col[ch], out=t); t *= 0.85
        oc = o[..., ch]; np.multiply(c, GOLDW[ch], out=oc); oc *= 1.15; oc += t; oc *= a
    return o

_ANA_COL = (GOLD * 0.6 + WHITE * 0.25)
def anamorphic(out, amt=0.30):
    small = cv2.resize(out, (W // 8, H // 8), interpolation=cv2.INTER_AREA)
    hi = np.clip(small.max(2) - 0.80, 0, 1) * 4.0
    if not hi.any(): return np.clip(out, 0, 1)                                              # no highlights: no streaks
    st = cv2.GaussianBlur(hi, (0, 0), sigmaX=40, sigmaY=0.6)
    st = cv2.resize(st, (W, H), interpolation=cv2.INTER_LINEAR)
    o = np.empty(out.shape, F32); t = np.empty((H, W), F32)
    for ch in range(3):
        np.multiply(st, _ANA_COL[ch], out=t); t *= amt; np.add(out[..., ch], t, out=o[..., ch])
    return np.clip(o, 0, 1, out=o)

_FIN = {}
def _fin_planes(f):
    if "v3" not in _FIN:
        grain(0, 0.012)
        _FIN["v3"] = np.repeat(0.80 + 0.20 * VIG, 3, axis=2)
    k = ("g", f % 6)
    if k not in _FIN: _FIN[k] = np.repeat(grain(f, 0.012), 3, axis=2)
    return _FIN["v3"], _FIN[k]

def finish11(out, f, s):
    rival = s is not None and is_rival(s)
    small = cv2.resize(out, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi_ = np.clip(small.max(2) - 0.64, 0, 1)
    b1 = cv2.GaussianBlur(hi_, (0, 0), 4); b2 = cv2.GaussianBlur(hi_, (0, 0), 16)
    bl = cv2.resize(b1 * 0.45 + b2 * 0.55, (W, H))
    col = RED2 if rival else GOLD2
    o = np.empty(out.shape, F32); t = np.empty((H, W), F32)
    for ch in range(3):
        np.multiply(bl, col[ch], out=t); t *= 0.48; np.add(out[..., ch], t, out=o[..., ch])
    o = anamorphic(o, 0.18)
    np.maximum(o, 0.012, out=o)
    v3, g3 = _fin_planes(f)
    o *= v3; o += g3
    return np.clip(o, 0, 1, out=o)

_K25 = cv2.getGaussianKernel(201, 25, cv2.CV_32F); _K1 = np.ones((1, 1), F32)
def _blur1(v, axis, k):
    if axis == 1: return cv2.sepFilter2D(v[None, :], -1, k, _K1, borderType=cv2.BORDER_REFLECT_101)[0]
    return cv2.sepFilter2D(v[:, None], -1, _K1, k, borderType=cv2.BORDER_REFLECT_101)[:, 0]

def face_keepout(hb):
    """GaussianBlur(sigma 25) of motes11's head mask clip(1 - max(|x - cx| / w, ramp(y)), 0, 1), from 1-D blurs."""
    cxh, wh = (hb[0] + hb[1]) / 2, (hb[1] - hb[0]) / 2 + 40
    gx = _GX[0]; gy = _GY[:, 0]
    ax = np.abs(gx - cxh) / wh
    by = np.clip((gy - hb[2]) / 60, 0, 1) * 9
    A = np.clip(1 - ax, 0, 1).astype(F32)
    S = (by <= 0).astype(F32)
    out = _blur1(S, 0, _K25)[:, None] * _blur1(A, 1, _K25)[None, :]
    for r in np.nonzero((by > 0) & (by < 1))[0]:
        e = np.clip(1 - np.maximum(ax, by[r]), 0, 1).astype(F32)
        d = np.zeros(H, F32); d[r] = 1
        col = _blur1(d, 0, _K25); nz = np.nonzero(col)[0]
        if len(nz): out[nz[0]:nz[-1] + 1] += col[nz[0]:nz[-1] + 1, None] * _blur1(e, 1, _K25)[None, :]
    return out.astype(F32, copy=False)

def motes11(out, f, person, dens, mode, rival=False, s=None):
    """ember: rising embers; fire: denser orange embers; dust: slow gold dust; speed: streaks rushing past in depth."""
    if dens <= 0.01: return out
    t = f / FPS; back = np.zeros((H, W), np.float32); front = np.zeros((H, W), np.float32)
    for p in pm11(mode):
        if p["on"] > dens: continue
        z = p["z"]; tgt = front if z > 0.62 else back
        if mode in ("ember", "fire"):
            sp = (110 + 300 * z) * p["v"] * (1.6 if mode == "fire" else 1.0)
            x = (p["x0"] * W + 40 * math.sin(1.3 * t + p["ph"]) + 25 * z * math.sin(3.1 * t + p["ph"] * 2)) % W
            y = (p["y0"] * (H + 200) - sp * t) % (H + 200) - 100
            r = 1.2 + 4.2 * z; tw = 0.55 + 0.45 * math.sin(7 * t + p["ph"] * 3)
            cv2.circle(tgt, (int(x), int(y)), max(1, int(r)), (0.55 + 0.45 * z) * tw, -1, cv2.LINE_AA)
            if z > 0.5: cv2.line(tgt, (int(x), int(y)), (int(x), int(y + r * 5)), 0.35 * tw, max(1, int(r * 0.6)), cv2.LINE_AA)
        elif mode == "dust":
            x = (p["x0"] * (W + 200) + (25 + 70 * z) * t * p["v"] + 30 * math.sin(0.8 * t + p["ph"])) % (W + 200) - 100
            y = (p["y0"] * (H + 200) - (15 + 40 * z) * t + 20 * math.sin(0.6 * t + p["ph"])) % (H + 200) - 100
            r = 1.0 + 3.0 * z; tw = 0.5 + 0.5 * math.sin(5 * t + p["ph"] * 2)
            cv2.circle(tgt, (int(x), int(y)), max(1, int(r)), (0.4 + 0.5 * z) * tw, -1, cv2.LINE_AA)
        else:                                                                                  # speed
            sp = (1400 + 3200 * z) * p["v"]; L_ = 80 + 520 * z
            x = (p["x0"] * (W + 1200) + sp * t) % (W + 1200) - 600; y = p["y0"] * H
            cv2.line(tgt, (int(x - L_), int(y)), (int(x), int(y)), 0.45 + 0.55 * z, max(1, int(1 + 3 * z)), cv2.LINE_AA)
    if person is not None: back *= (1 - np.clip(person * 1.3, 0, 1))
    hb = head_box(s, f, person) if s is not None else None
    if hb is not None:                                                                      # nothing in front of his face
        hm = face_keepout(hb)
        front *= (1 - hm); back *= (1 - hm * (0.0 if person is not None else 1.0))
    lay = back * 0.8 + cv2.GaussianBlur(front, (0, 0), 1.8 + (2.0 if mode == "speed" else 0.0)) * 1.25
    glow = cv2.resize(cv2.GaussianBlur(cv2.resize(lay, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 3), (W, H))
    if mode == "ember" and rival: core, gl = REDW, RED2
    elif mode in ("ember", "fire"): core, gl = np.array([0.35, 0.75, 1.0], np.float32), EMBER2
    else: core, gl = GOLDW, GOLD2
    a = min(1.0, dens * 1.2) * (0.75 if mode == "dust" else 1.0)
    o = np.empty(out.shape, F32); t1 = np.empty((H, W), F32); t2 = np.empty((H, W), F32)
    for ch in range(3):
        np.multiply(lay, core[ch], out=t1); t1 *= 0.9; np.multiply(glow, gl[ch], out=t2); t2 *= 1.5; t1 += t2; t1 *= a
        np.add(out[..., ch], t1, out=o[..., ch])
    return np.clip(o, 0, 1, out=o)

_grade_v2a = grade
def grade(img, s, f):
    lk = s.get("look")
    if lk not in ("voltage", "rival") or not in_unit(img): return _grade_v11_ref(img, s, f)
    g, gains = corr9(s); ev = s.get("ev") or 0
    lx, ly = lut11(lk)
    x = apply_lut3(img, tone_lut((lk, s["n"], ev, float(g), tuple(float(v) for v in gains)), gains, g, ev, lx, ly))
    Bc, Gc, Rc = (np.ascontiguousarray(x[..., c]) for c in range(3))
    L = Bc * 0.114 + Gc * 0.587 + Rc * 0.299
    red = np.clip((Rc - np.maximum(Gc, Bc) * 1.25) * 3.0, 0, 1)
    d = Rc - Bc
    light = np.clip((L - 0.62) * 3.0, 0, 1) * np.clip(d * 3.0, 0, 1)
    hue = (Rc - Gc) / (Rc + 1e-3)
    skin = np.clip(1 - np.abs(hue - 0.22) / 0.22, 0, 1) * np.clip(d * 6, 0, 1) * np.clip(L * 3, 0, 1)
    sat = 0.84 + 0.32 * red + 0.25 * light + 0.10 * skin
    sh = (1 - L) ** 2.6 * (1 - 0.7 * skin) * (1 - red)
    hi = np.clip((L - 0.55) * 2.2, 0, 1) * (1 - skin * 0.6)
    if lk == "voltage": ts, hs, ks = TEALS, np.array([-0.018, 0.010, 0.035], F32), None
    else: ts, hs, ks = np.array([0.000, -0.006, 0.022], F32), np.array([-0.030, -0.018, 0.045], F32), np.array([0.94, 0.95, 1.04], F32)
    o = np.empty(x.shape, F32)
    for ch, P in enumerate((Bc, Gc, Rc)):
        v = L + (P - L) * sat
        v += sh * ts[ch]; v += hi * hs[ch]
        if ks is not None: v *= ks[ch]
        o[..., ch] = v
    return np.clip(o, 0, 1, out=o)


_STILL = {}
STILL_MAX = 18                                                                              # ~33 MB each with a matte
_render_shot_v2ref = render_shot
def render_shot(s, f, with_shake=True, want_mask=False):
    if with_shake: return _render_shot_v2ref(s, f, True, want_mask)
    key = (s["n"], f, bool(want_mask))
    hit = _STILL.pop(key, None)
    if hit is None:
        r = _render_shot_v2ref(s, f, False, want_mask)
        for a_ in (r if isinstance(r, tuple) else (r,)): a_.flags.writeable = False
        hit = (r, SR_USED[0])
        while len(_STILL) >= STILL_MAX: _STILL.pop(next(iter(_STILL)))
    _STILL[key] = hit                                                                       # most recent last
    SR_USED[0] = hit[1]
    return hit[0]

def frame_blocks(frames, size=36):
    """split a sorted frame list into contiguous runs that never cross a cut, at most `size` frames each."""
    out, cur = [], []
    for f in frames:
        if cur and (f != cur[-1] + 1 or shot_at(f) is not shot_at(cur[-1]) or len(cur) >= size): out.append(cur); cur = []
        cur.append(f)
    if cur: out.append(cur)
    return out

def _render_block(fs): return [render(f) for f in fs]

def render_blocks(pool, frames, size=36):
    """yield (frame, image) in the order given, each block rendered by one worker."""
    from collections import deque
    bl = frame_blocks(frames, size); q = deque()
    for fs in bl:                                                                           # at most 6 blocks in flight
        q.append((fs, pool.apply_async(_render_block, (fs,))))
        if len(q) >= 6: fs_, r = q.popleft(); yield from zip(fs_, r.get())
    while q: fs_, r = q.popleft(); yield from zip(fs_, r.get())


# <<< pipeline v2: speed

def main():
    mode = sys.argv[1]
    load(); init_hits()
    if mode == "prep":
        prep_tracks(); prep_seg(); return
    RAW_TRK.update(json.load(open(f"{ROOT}/{E.VER}/work/tracks{E.VER[1:]}.json")))
    z = np.load(f"{ROOT}/{E.VER}/work/seg{E.VER[1:]}.npz"); SEG.update({k: z[k] for k in z.files})
    if mode == "stills":
        name = sys.argv[2]; frames = [int(a) for a in sys.argv[3:]]; ims = []
        for f in frames:
            im = cv2.resize(render(f), (270, 480), interpolation=cv2.INTER_AREA)
            cv2.putText(im, str(f), (5, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1, cv2.LINE_AA); ims.append(im)
        while len(ims) % 6: ims.append(np.zeros_like(ims[0]))
        cv2.imwrite(f"{ROOT}/{E.VER}/frames/{name}.jpg", np.vstack([np.hstack(ims[i:i + 6]) for i in range(0, len(ims), 6)]), [cv2.IMWRITE_JPEG_QUALITY, 88])
        return
    if mode == "auto":                                                   # sheets around every cut, 6 cuts per sheet
        name = sys.argv[2]; offs = (-8, -4, -1, 0, 3, 8)
        cuts = [sh["f0"] for sh in SHOTS[1:]]
        for si in range(0, len(cuts), 6):
            frames = [min(E.DUR_F - 1, max(0, c + o)) for c in cuts[si:si + 6] for o in offs]
            with Pool(4) as pool: rend = pool.map(render, frames, chunksize=2)
            ims = []
            for f, r in zip(frames, rend):
                im = cv2.resize(r, (216, 384), interpolation=cv2.INTER_AREA)
                cv2.putText(im, str(f), (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA); ims.append(im)
            while len(ims) % 6: ims.append(np.zeros_like(ims[0]))
            out = f"{ROOT}/{E.VER}/frames/{name}_{si // 6 + 1}.jpg"
            cv2.imwrite(out, np.vstack([np.hstack(ims[i:i + 6]) for i in range(0, len(ims), 6)]), [cv2.IMWRITE_JPEG_QUALITY, 86]); print(out)
        return
    if mode in ("clip", "preview"):                                      # quick motion checks with sound
        a, b, step = (int(sys.argv[2]), int(sys.argv[3]), 1) if mode == "clip" else (0, E.DUR_F - 1, 2)
        a, b = max(0, a), min(E.DUR_F - 1, b)                            # stay inside the edit
        frames = list(range(a, b + 1, step)); fps_ = FPS // step
        out = f"{ROOT}/{E.VER}/frames/clip_{a}_{b}.mp4" if mode == "clip" else f"{ROOT}/{E.VER}/out/preview.mp4"
        os.makedirs(os.path.dirname(out), exist_ok=True)
        mix = f"{ROOT}/{E.VER}/audio/mix.wav"; aud = ["-ss", str(a / FPS), "-t", str(len(frames) * step / FPS), "-i", mix] if os.path.exists(mix) else []
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W // 2}x{H // 2}", "-r", str(fps_), "-i", "-", *aud,
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", *(["-c:a", "aac", "-b:a", "160k", "-shortest"] if aud else []), out]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        with Pool(4) as pool:
            for _, fr in render_blocks(pool, frames, 24):
                p.stdin.write(cv2.resize(fr, (W // 2, H // 2), interpolation=cv2.INTER_AREA).tobytes())
        p.stdin.close(); p.wait(); print(out); return
    if mode == "full":
        for f in [int(a) for a in sys.argv[2:]]:
            cv2.imwrite(f"{ROOT}/{E.VER}/frames/full_{f:04d}.jpg", render(f), [cv2.IMWRITE_JPEG_QUALITY, 92])
        return
    if mode == "video":
        outdir = f"{ROOT}/{sys.argv[2]}"; os.makedirs(outdir, exist_ok=True)
        vf = "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p"
        tags = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-itsoffset", str(-1024 / 48000), "-i", f"{ROOT}/{E.VER}/audio/mix_preroll.wav", "-i", f"{ROOT}/{E.VER}/audio/mix.wav",
               "-map", "0:v", "-map", "1:a", "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-maxrate", "26M", "-bufsize", "52M",
               "-profile:v", "high", "-level", "4.2", "-g", "120", "-bf", "3", *tags, "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
               "-movflags", "+faststart", f"{outdir}/{E.SLUG}_voidfx_9x16.mp4",
               "-map", "0:v", "-map", "2:a", "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "11", "-profile:v", "high", "-level", "5.1",
               *tags, "-c:a", "pcm_s24le", "-ar", "48000", f"{outdir}/{E.SLUG}_voidfx_9x16_master.mov"]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        with Pool(4) as pool:
            for i, (_, fr) in enumerate(render_blocks(pool, list(range(E.DUR_F)))):
                p.stdin.write(fr.tobytes())
                if i % 150 == 0: print(f"frame {i}/{E.DUR_F}", flush=True)
        p.stdin.close(); p.wait(); print("done", outdir, flush=True)

if __name__ == "__main__":
    main()
