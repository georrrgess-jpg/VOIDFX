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
import edl105 as E
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
            for fr in pool.imap(render, frames, chunksize=4):
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
               "-map", "0:v", "-map", "1:a", "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-maxrate", "16M", "-bufsize", "32M",
               "-profile:v", "high", "-level", "4.2", "-g", "120", "-bf", "3", *tags, "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
               "-movflags", "+faststart", f"{outdir}/{E.SLUG}_voidfx_9x16.mp4",
               "-map", "0:v", "-map", "2:a", "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "11", "-profile:v", "high", "-level", "5.1",
               *tags, "-c:a", "pcm_s24le", "-ar", "48000", f"{outdir}/{E.SLUG}_voidfx_9x16_master.mov"]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        with Pool(4) as pool:
            for i, fr in enumerate(pool.imap(render, range(E.DUR_F), chunksize=4)):
                p.stdin.write(fr.tobytes())
                if i % 150 == 0: print(f"frame {i}/{E.DUR_F}", flush=True)
        p.stdin.close(); p.wait(); print("done", outdir, flush=True)




























































# >>> v105 section (generated from fx105.py by splice.py)
# ============================================================================ v105 — DRACULA — Dexter × Tame Impala: toolkit from the v104 standard (restyle it)
# spliced into render105.py before main() by splice.py; the last definitions win, so this section owns the frame.
DEEP = np.array([0.075, 0.045, 0.012], np.float32)    # BGR deep Gulf water
TEAL = np.array([0.42, 0.33, 0.08], np.float32)       # BGR lit water
FOAM = np.array([0.93, 0.95, 0.92], np.float32)
BONE = np.array([0.86, 0.92, 0.95], np.float32)
BLOODC = np.array([0.05, 0.03, 0.62], np.float32)
BLOODH = np.array([0.30, 0.30, 1.00], np.float32)
STEELC = np.array([0.80, 0.80, 0.78], np.float32)
def kt(t): return t / E.HB                                                            # edit half-beats

# ---------------------------------------------------------------------------- grade: UNDERTOW
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
    g = clamp(math.log(s.get("target", 0.40)) / math.log(clamp(face, 0.02, 0.97)), 0.75, 1.30)
    m = img.reshape(-1, 3).mean(0); wb = s.get("wb", 0.10)
    gains = np.clip((m.mean() / (m + 1e-6)) ** wb, 1 - 0.8 * wb, 1 + 0.8 * wb)
    CORR[s["n"]] = (g, gains.astype(np.float32)); return CORR[s["n"]]

def grade(img, s, f):
    g, gains = correction(s)
    x = np.clip(img * gains, 0, 1) ** g
    lx, ly = lut(); x = np.interp(x, lx, ly).astype(np.float32)
    if s.get("dayfornight"):                                                          # bright daylight sea -> moonlit Gulf
        x = np.clip(x * 0.55, 0, 1) ** 1.25
        x = x * np.array([1.18, 1.0, 0.72], np.float32)
    B_, G_, R_ = x[..., 0], x[..., 1], x[..., 2]
    red = np.clip((R_ - np.maximum(G_, B_)) * 3.2, 0, 1)[..., None]
    L = (x[..., 0] * 0.114 + x[..., 1] * 0.587 + x[..., 2] * 0.299)[..., None]
    x = L + (x - L) * (0.78 + 0.45 * red) * (1 - s.get("desat", 0.0))              # drained, but blood stays red
    x = x + (1 - L) ** 2.4 * np.array([0.050, 0.032, -0.012], np.float32)            # deep teal-blue shadows
    x = x + L ** 1.8 * np.array([0.006, 0.010, 0.006], np.float32)                   # bone highlights
    x = x * 0.82 + (x * x * (3 - 2 * x)) * 0.18
    return np.clip(x * 0.975 + 0.012, 0, 1)

def beat_bounce(f): return 1.0

# ---------------------------------------------------------------------------- water: caustics, marine snow, bubbles, the deep
_CA3 = {}
def caustic_map(f, scale=1.0):
    """animated water caustics (bright filaments), quarter res -> full."""
    if "g" not in _CA3:
        yy, xx = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32); _CA3["g"] = (xx / 40.0, yy / 40.0)
    X, Y = _CA3["g"]; t = f / FPS
    acc = np.zeros_like(X)
    for i, (a, b, sp) in enumerate(((1.0, 0.6, 0.9), (-0.7, 1.1, 1.2), (0.4, -1.3, 0.7))):
        u = X * a * scale + Y * b * scale + t * sp + i
        w = np.sin(u * 2.1 + np.sin(X * 1.3 + t * 0.8 + i) * 1.2 + np.cos(Y * 1.1 - t * 0.6) * 1.1)
        acc += np.abs(w)
    c = np.clip(1.0 - acc / 3.0, 0, 1) ** 4
    return cv2.resize(cv2.GaussianBlur(c, (0, 0), 0.8), (W, H), interpolation=cv2.INTER_CUBIC)

def caustics(out, f, amt):
    c = caustic_map(f)[..., None]
    L = lum(out)[..., None]
    return np.clip(out + c * amt * (0.10 + 0.25 * L) * (TEAL * 0.6 + BONE * 0.4), 0, 1)

_SN = {}
def snow(out, f, amt=1.0, wrap=False):
    """marine snow: slow particulate in the water, in depth."""
    if "p" not in _SN:
        rng = np.random.default_rng(31); n = 140
        _SN["p"] = np.stack([rng.uniform(0, W, n), rng.uniform(0, H + 200, n), rng.uniform(0.3, 1.0, n), rng.uniform(0, 6.28, n), rng.integers(0, 2, n)], 1)
    t = (f % E.DUR_F) / FPS
    lay = np.zeros((H // 2, W // 2), np.float32); near = np.zeros((H // 2, W // 2), np.float32)
    for x, y, d, ph, zl in _SN["p"]:
        v = (H + 200) * 1 / E.DUR                                                     # one full drift per loop: wraps exactly at the seam
        Y = (y - v * t * (0.5 + 0.5 * d)) % (H + 200) - 100; X = x + 14 * math.sin(t * 0.7 + ph)
        if zl: cv2.circle(near, (int(X / 2), int(Y / 2)), 3, d, -1, cv2.LINE_AA)
        else: cv2.circle(lay, (int(X / 2), int(Y / 2)), 1, d, -1, cv2.LINE_AA)
    m = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 0.7) + cv2.GaussianBlur(near, (0, 0), 3.5) * 0.8, (W, H))
    return np.clip(out + m[..., None] * amt * 0.32 * (BONE * 0.7 + TEAL * 0.3), 0, 1)

_BB = {}
def bubbles_layer(f, density=1.0, src=None, rise=1.0):
    """rising bubbles: rings with a bright rim and a highlight. src=(x, y) streams them from a point."""
    if "p" not in _BB:
        rng = np.random.default_rng(57); n = 90
        _BB["p"] = np.stack([rng.uniform(0, W, n), rng.uniform(0, H + 300, n), rng.uniform(4, 22, n), rng.uniform(0, 6.28, n), rng.uniform(0.6, 1.4, n)], 1)
    t = (f % E.DUR_F) / FPS; lay = np.zeros((H // 2, W // 2), np.float32)
    for i, (x, y, r, ph, sp) in enumerate(_BB["p"]):
        if i > len(_BB["p"]) * density: break
        v = (H + 300) * round(2 * sp) / E.DUR * rise
        if src is not None:
            Y = src[1] - ((v * t + y) % 900); X = src[0] + (i % 9 - 4) * 14 + 22 * math.sin(t * 3 + ph) * (src[1] - Y) / 400
        else:
            Y = (y - v * t) % (H + 300) - 150; X = x + 18 * math.sin(t * 2.2 + ph)
        R = max(1, int(r / 2))
        cv2.circle(lay, (int(X / 2), int(Y / 2)), R, 0.9, max(1, R // 3), cv2.LINE_AA)
        cv2.circle(lay, (int(X / 2 - R * 0.35), int(Y / 2 - R * 0.35)), max(1, R // 3), 1.0, -1, cv2.LINE_AA)
    return cv2.resize(cv2.GaussianBlur(lay, (0, 0), 0.6), (W, H))

def rays(f, d):
    """god rays from the surface, swaying."""
    t = f / FPS; xs = (_GX - W / 2) + (_GY * 0.35)
    r = np.zeros((H, W), np.float32)
    for k, (a, w, sp) in enumerate(((0.0, 60, 0.4), (260, 90, 0.3), (-300, 70, 0.5), (520, 50, 0.35), (-560, 80, 0.45))):
        c = a + 120 * math.sin(t * sp + k)
        r += np.exp(-((xs - c) / w) ** 2) * (0.5 + 0.5 * math.sin(t * 1.3 + k * 2))
    return r * np.clip(1 - _GY / (H * (1.15 - 0.6 * d)), 0, 1) ** 1.5

def deep_water(f, d, above=None):
    """underwater at depth d (0 = just under the surface, 1 = deep). above = the world seen through the surface."""
    gy = (_GY / H)[..., None]
    base = DEEP * (1 - (1 - gy) * 0.9 * (1 - 0.8 * d)) + TEAL * (1 - gy) ** 2.2 * (1 - d) * 0.9
    o = np.broadcast_to(base, (H, W, 3)).copy()
    if above is not None and d < 0.98:                                                # Snell's window: the world above, refracted
        t = f / FPS
        dx = 9 * np.sin(_GY / 37 + t * 3.1) + 6 * np.sin(_GX / 53 - t * 2.3)
        dy = 7 * np.cos(_GX / 41 + t * 2.7)
        sc = 0.55 + 0.45 * (1 - d)
        mx = (W / 2 + (_GX - W / 2) / sc + dx).astype(np.float32); my = (H * 0.30 + (_GY - H * 0.30) / sc + dy).astype(np.float32)
        ab = cv2.remap(above, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        R = W * (0.35 + 0.65 * (1 - d) ** 1.4)
        win = np.clip((R - np.sqrt(((_GX - W / 2) * 0.85) ** 2 + ((_GY - H * 0.24) * 1.1) ** 2)) / 120, 0, 1)[..., None]
        ab = ab * np.array([1.0, 0.92, 0.70], np.float32) * (1 - 0.65 * d)
        o = o * (1 - win) + (ab * 0.85 + TEAL * 0.15) * win
    o = o + rays(f, d)[..., None] * (TEAL * 0.6 + BONE * 0.4) * 0.22 * (1 - 0.7 * d)
    o = o + bubbles_layer(f, 0.5)[..., None] * (BONE * 0.55 + TEAL * 0.3) * (0.6 + 0.4 * (1 - d))
    return np.clip(snow(o, f, 0.8), 0, 1)

# ---------------------------------------------------------------------------- THE GULF STREAM (loop): surfacing ... splash, sink
def surface_in(B, f, k):
    """frame 0..: rising from the deep toward the surface; the boat seen from below through the water; break the surface."""
    t = f / FPS; ks = E.T_SURFACE * FPS
    if t < E.T_SURFACE - 0.12:
        d = 1 - eout(t / (E.T_SURFACE - 0.12), 2.2)                                  # rise fast: he's visible through the water within a quarter second
        return deep_water(f, d, above=B)
    u = clamp((t - (E.T_SURFACE - 0.12)) / 0.30, 0, 1)                                # the waterline rushes down past the lens
    yl = H * (-0.15 + 1.35 * eout(u, 1.6))
    wave = 30 * np.sin(_GX / 90 + f * 0.9) + 12 * np.sin(_GX / 29 - f * 1.3)
    dist = _GY - (yl + wave)
    above = np.clip(-dist / 10 + 0.5, 0, 1)
    band = np.exp(-(dist / 55) ** 2)
    water = deep_water(f, 0.0, above=B)
    dy = 46 * band * np.sin(_GX / 47 + f * 0.6)
    Bm = cv2.remap(B, _GX, (_GY + dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    o = Bm * above[..., None] + water * (1 - above[..., None])
    o = o * (1 - 0.35 * band[..., None]) + band[..., None] * TEAL * 0.35 + np.exp(-(dist / 9) ** 2)[..., None] * BONE * 0.22
    return np.clip(lens_drops(o, f, 1 - u * 0.4), 0, 1)

_LD = {}
def lens_drops(img, f, amt):
    """water droplets on the lens just after the break: each refracts (and flips) what's behind it, and slides down."""
    if amt <= 0.01: return img
    if "d" not in _LD:
        rng = np.random.default_rng(5); _LD["d"] = [(rng.uniform(60, W - 60), rng.uniform(80, H - 80), rng.uniform(14, 46), rng.uniform(40, 220)) for _ in range(26)]
    t = f / FPS; o = img.copy()
    for x, y, r, v in _LD["d"]:
        Y = y + v * t; R = int(r)
        x0, y0, x1, y1 = int(x - R), int(Y - R), int(x + R), int(Y + R)
        if x0 < 0 or y0 < 0 or x1 >= W or y1 >= H: continue
        patch = cv2.flip(cv2.resize(img[max(0, y0 - R):y1 + R, max(0, x0 - R):x1 + R], (2 * R, 2 * R)), -1)
        m = np.zeros((2 * R, 2 * R), np.float32); cv2.circle(m, (R, R), R - 1, 1.0, -1, cv2.LINE_AA); m = cv2.GaussianBlur(m, (0, 0), 1.0)[..., None] * amt
        hl = np.zeros((2 * R, 2 * R), np.float32); cv2.circle(hl, (int(R * 0.65), int(R * 0.6)), max(1, R // 5), 1.0, -1, cv2.LINE_AA)
        o[y0:y0 + 2 * R, x0:x0 + 2 * R] = o[y0:y0 + 2 * R, x0:x0 + 2 * R] * (1 - m) + (patch * 0.9 + hl[..., None] * 0.6) * m
    return o

_BAG = {}
def bag_sprite():
    if "s" in _BAG: return _BAG["s"]
    h, w = 420, 200; m = np.zeros((h, w), np.float32)
    pts = np.array([[100, 8], [150, 40], [178, 130], [170, 260], [182, 360], [120, 410], [70, 404], [22, 350], [30, 240], [18, 120], [52, 34]], np.int32)
    cv2.fillPoly(m, [pts], 1.0, cv2.LINE_AA); m = cv2.GaussianBlur(m, (0, 0), 2.5)
    col = np.zeros((h, w, 3), np.float32) + np.array([0.035, 0.035, 0.03], np.float32)
    for y in (110, 230, 330):                                                         # ties
        cv2.line(col, (20, y), (180, y + 12), (0.14, 0.15, 0.15), 6, cv2.LINE_AA)
    sheen = np.exp(-((np.arange(w)[None, :] - 70) / 20.0) ** 2) * 0.10
    col = col + sheen[..., None]
    _BAG["s"] = np.dstack([col, m]).astype(np.float32); return _BAG["s"]

def sink_end(out, f, s):
    """the bag hits the water: splash, under we go, it sinks into the black (the loop seam is deep water)."""
    t = f / FPS; ts = E.T_SPLASH
    if t < ts - 0.05: return out
    bx, by = W * 0.52, H * 0.78
    if t < ts + 0.12:                                                                  # the splash: white water erupts up from below the frame
        k = (t - ts + 0.05) / 0.17; rng = np.random.default_rng(9); lay = np.zeros((H // 2, W // 2), np.float32)
        top = H * (1.05 - 0.55 * eout(k, 2.0))
        col = np.clip((_GY[::2, ::2] - top) / 120, 0, 1) * np.exp(-((_GX[::2, ::2] - bx) / (230 + 120 * k)) ** 2)
        lay += col * (0.6 + 0.4 * _lowfreq((H // 2, W // 2), (20, 12), 3))
        for i in range(140):
            a = rng.uniform(math.pi * 1.15, math.pi * 1.85); sp = rng.uniform(500, 1500)
            x = bx + math.cos(a) * sp * k * 0.5; y = H * 1.02 + math.sin(a) * sp * k * 0.9 + 700 * k * k
            x2 = x - math.cos(a) * 30; y2 = y - math.sin(a) * 30
            cv2.line(lay, (int(x / 2), int(y / 2)), (int(x2 / 2), int(y2 / 2)), float(rng.uniform(0.5, 1.0)), int(rng.uniform(1, 4)), cv2.LINE_AA)
        lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 1.4), (W, H))[..., None]
        return np.clip(out * (1 - lay * 0.8) + FOAM * lay * 0.95, 0, 1)
    u = clamp((t - ts - 0.12) / 0.20, 0, 1)                                            # plunge: the waterline rises past the lens
    end_d = clamp((t - ts - 0.12) / (E.DUR - ts - 0.12), 0, 1)
    d = 0.15 + 0.85 * smooth(end_d)
    water = deep_water(f, d, above=out if d < 0.6 else None)
    if u < 1:
        yl = H * (1.1 - 1.3 * eout(u, 1.8)); wave = 22 * np.sin(_GX / 60 - f * 1.1)
        below = (_GY > yl + wave).astype(np.float32)[..., None]
        fl = np.exp(-((_GY - yl - wave) / 16) ** 2)[..., None] * FOAM * 0.7
        water = out * (1 - below) + water * below + fl + bubbles_layer(f, 1.0)[..., None] * FOAM * 0.8 * (1 - u)
    lay = np.zeros((H, W, 4), np.float32); sp_ = bag_sprite()                          # the bag sinking away into the dark
    sc = 1.6 - 1.25 * smooth(end_d); y = H * (0.45 + 0.42 * smooth(end_d)); rot = 18 * smooth(end_d) - 8
    draw_sprite(lay, sp_, W * 0.5 + 40 * math.sin(end_d * 3), y, sc, rot, 1.0, 1.0 + 3 * end_d, 1 - 0.85 * smooth((end_d - 0.55) / 0.45))
    o = water * (1 - lay[..., 3:4]) + lay[..., :3] * lay[..., 3:4] * (1 - 0.6 * end_d) + water * lay[..., 3:4] * 0.6 * end_d
    b = bubbles_layer(f, 1.0, src=(W * 0.5, y - 150 * sc), rise=1.6)
    o = o + b[..., None] * BONE * 0.55 * (1 - 0.6 * end_d)
    return np.clip(o, 0, 1)

# ---------------------------------------------------------------------------- rev 4: THE RIP (drop). Kill-room plastic is pulled
#      over the lens as the build peaks; on the drop it tears open down the middle (plastic_rip) and the riff bursts through.
_PS = {}
def plastic_sheet(img, f, amt):
    """kill-room sheeting over the lens: milky diffusion, folds that sway with speculars, a slight refraction along the folds."""
    if amt <= 0.005: return img
    spec, fold = plastic_tex()
    sw = int(round(26 * math.sin(f * 0.045)))
    if sw not in _PS:
        if len(_PS) > 8: _PS.clear()
        sp = np.roll(spec, sw, 1); _PS[sw] = (sp, cv2.Sobel(sp, cv2.CV_32F, 1, 0, ksize=5) * 0.25)
    sp, gx = _PS[sw]
    o = cv2.remap(img, (_GX + gx * 16 * amt).astype(np.float32), _GY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    milky = cv2.GaussianBlur(o, (0, 0), 1.5 + 5 * amt) * (1 - 0.22 * amt) + (BONE * 0.07 + TEAL * 0.03) * amt
    o = o * (1 - 0.85 * amt) + milky * 0.85 * amt
    return np.clip(o + (sp ** 2)[..., None] * BONE * 0.42 * amt, 0, 1)

# ---------------------------------------------------------------------------- rev 4: THE EVIDENCE PHOTOS (hook). The ring flash fires,
#      the frame freezes into a crime-scene photograph and is tossed aside (left or right) onto the next shot.
_PH = {}
def photo103(A, B, j, f, sa, sb, side=1, pre=6, post=16):
    if j < 0:
        fl = ein((j + pre + 1) / (pre + 1), 3)
        return np.clip(A * (1 + 1.2 * fl) + (BONE * 0.30) * fl, 0, 1)
    key = sa["n"]
    if key not in _PH:
        b = 44; card = np.ones((H + 5 * b, W + 2 * b, 4), np.float32)
        card[..., :3] = np.array([0.90, 0.93, 0.94], np.float32)
        card[b:b + H, b:b + W, :3] = np.clip(A * 1.04 + 0.025, 0, 1)
        _PH[key] = (card, b)
    card, b = _PH[key]; ch, cw = card.shape[:2]
    u1 = eout(clamp(j / 5.0, 0, 1), 3); u2 = ein(clamp((j - 5) / 10.0, 0, 1), 2.2)
    sc = 1.0 - 0.34 * u1 - 0.1 * u2; rot = side * (-6 * u1 - 26 * u2)
    cx, cy = W / 2 + side * 1300 * u2, H / 2 + 30 * u1 + 560 * u2
    M = cv2.getRotationMatrix2D((cw / 2, ch / 2 - 2 * b), rot, sc)
    M[0, 2] += cx - cw / 2; M[1, 2] += cy - (ch / 2 - 2 * b)
    cd = cv2.warpAffine(card, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    al = cd[..., 3:4]
    shd = cv2.GaussianBlur(np.roll(np.roll(cd[..., 3], 34, 0), side * 26, 1), (0, 0), 22)[..., None] * 0.55
    Bz = zoom_about(B, W / 2, H / 2, 1.08 - 0.08 * eout(j / float(post), 2))
    o = Bz * (1 - shd) * (1 - al) + cd[..., :3] * al
    fl = clamp(1 - j / 4.0, 0, 1)
    return np.clip(o + 0.45 * fl * al + 0.22 * fl, 0, 1)

TR2.update({"photo": (lambda A, B, j, f, sa, sb: photo103(A, B, j, f, sa, sb, 1), 6, 16),
            "photo_l": (lambda A, B, j, f, sa, sb: photo103(A, B, j, f, sa, sb, -1), 6, 16)})

# ---------------------------------------------------------------------------- rev 4: graphics for the holds
def anam_flare(out, amt, f):
    """anamorphic lens flare: every hot light (lamp, flashlight, headlights) throws a long horizontal teal streak."""
    L = lum(out); hi = np.clip((L - 0.78) / 0.22, 0, 1) ** 2
    sm = cv2.resize(hi, (W // 8, H // 8), interpolation=cv2.INTER_AREA)
    streak = cv2.resize(cv2.GaussianBlur(sm, (0, 0), sigmaX=34, sigmaY=0.7), (W, H))
    glow = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 4), (W, H))
    fl = (0.92 + 0.08 * math.sin(f * 0.9)) * amt
    return np.clip(out + (np.clip(streak * 22, 0, 1.2)[..., None] * (TEAL * 0.9 + BONE * 0.35) + np.clip(glow * 3, 0, 1)[..., None] * BONE * 0.25) * fl, 0, 1)

def lamp_swing(out, f, s):
    """the kill-room lamp swings: its pool of light sways across the table."""
    t = f / FPS - s["t0"]
    cx = W / 2 + 190 * math.sin(2 * math.pi * t / 1.35); cy = H * 0.46 + 30 * math.cos(4 * math.pi * t / 1.35)
    m = 0.70 + 0.34 * np.exp(-(((_GX - cx) / 560) ** 2 + ((_GY - cy) / 760) ** 2))
    return np.clip(out * m[..., None], 0, 1)

def beat_fx(out, f):
    """the camera punches on the beat: a zoom kick (stronger on the downbeats, with a chromatic split), and in the build a
    softer heartbeat thump under the red pulse."""
    z = 0.0; ch = 0.0
    for k, a in E.BEAT_PUNCH:
        kk = f - E.fh(k)
        if a > 0 and 0 <= kk < 14:
            e = a * math.exp(-kk / 3.5); z = max(z, e)
            if a >= 0.9: ch = max(ch, e)
    for kb in E.PULSE_K:
        kk = f - E.fh(kb)
        if 0 <= kk < 12: z = max(z, 0.30 * math.exp(-kk / 3.0) * (1.0 if (kb // 2) % 2 == 0 else 0.6))
    if z < 0.01: return out
    o = zoom_about(out, W / 2, H * 0.42, 1 + 0.045 * z)
    if ch > 0.05: o = rgb_split(o, 9 * ch)
    return np.clip(o * (1 + 0.10 * z), 0, 1)

# ---------------------------------------------------------------------------- new transitions: sea spray
def wave_tr(A, B, j, f, sa, sb, pre=8, post=12):
    """a wave of sea spray washes across the lens (refraction, foam), leaving the next shot."""
    u = clamp((j + pre) / (pre + post), 0, 1); front = -300 + (W + 700) * eout(u, 1.6)
    X = _GX + (_GY - H / 2) * 0.35
    edge = front + 70 * np.sin(_GY / 160 + f * 0.25) + 28 * np.sin(_GY / 57 - f * 0.4)    # a rolling, rounded water front
    behind = np.clip((edge - X) / 45 + 0.5, 0, 1)
    band = np.exp(-((X - edge) / 170) ** 2)
    nz = band * (34 * np.sin(_GY / 90 + f * 0.30) + 12 * np.sin(_GY / 37 - f * 0.5))
    src = B * behind[..., None] + A * (1 - behind[..., None])
    o = cv2.remap(src, (_GX + nz).astype(np.float32), (_GY + nz * 0.5).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    o = cv2.GaussianBlur(o, (0, 0), 1.0) * band[..., None] * 0.5 + o * (1 - band[..., None] * 0.5)
    foam = np.clip(band * (0.35 + 0.65 * cv2.resize(_lowfreq((H // 4, W // 4), (30, 18), 7 + f // 3), (W, H))) - 0.25, 0, 1) * 1.4
    o = o * (1 - foam[..., None] * 0.5) + FOAM * 0.80 * foam[..., None] * 0.5
    return np.clip(lens_drops(o, f + 900, 0.8 * math.sin(math.pi * u)), 0, 1)        # spray left on the lens, sliding down

TR2.update({"surface": (lambda A, B, j, f, sa, sb: surface_in(B, f, j), 0, int(E.T_SURFACE * FPS) + 20), "wave": (wave_tr, 8, 12)})

# ---------------------------------------------------------------------------- text: v9 standard (captions) + a generic per-letter hero title
def drop_sprite(r=14):
    h, w = int(r * 3.2), int(r * 2.2); m = np.zeros((h, w), np.float32)
    cv2.circle(m, (w // 2, h - r - 2), r, 1.0, -1, cv2.LINE_AA)
    cv2.fillConvexPoly(m, np.array([[w // 2, 2], [w // 2 - r + 2, h - r - 2], [w // 2 + r - 2, h - r - 2]], np.int32), 1.0, cv2.LINE_AA)
    col = np.dstack([m * 0] * 3) + BLOODC; hl = np.zeros_like(m); cv2.circle(hl, (w // 2 - r // 3, h - r - r // 3), max(1, r // 4), 1.0, -1, cv2.LINE_AA)
    col = col + hl[..., None] * 0.5
    return np.dstack([np.clip(col, 0, 1), cv2.GaussianBlur(m, (0, 0), 0.7)]).astype(np.float32)

def bubble_sprite(r=14):
    n = r * 2 + 6; m = np.zeros((n, n), np.float32); cv2.circle(m, (n // 2, n // 2), r, 1.0, 2, cv2.LINE_AA)
    cv2.circle(m, (n // 2 - r // 3, n // 2 - r // 3), max(1, r // 4), 1.0, -1, cv2.LINE_AA)
    return np.dstack([np.dstack([m] * 3) * BONE, m * 0.9]).astype(np.float32)

def hero103(out, f, tx):
    """per-letter hero title (the v9 standard): each letter blooms open (scale, twist, blur -> sharp, a flare), staggered on
    its word; the last line lands bigger and floods red from the bottom like blood; the exit blows the letters away as
    the edit's own particles (blood droplets here, bubbles as FOREVER goes under)."""
    t = f / FPS; words = tx["words"]
    if t < words[0][1] - 0.02 or t > tx["end"] + 0.30: return out
    lines = tx["lines"]; nl = len(lines); t_end = tx["end"]
    sizes = [150, 196] if nl == 2 else [212]; ys = [1300, 1478] if nl == 2 else [1190]
    out = out * cap_scrim(ys[0] - 120, ys[-1] + 120, 0.36 * (1 - smooth((t - t_end + 0.1) / 0.3)))
    lay = np.zeros((H, W, 4), np.float32); spr = drop_sprite() if tx["exit"] == "blood" else bubble_sprite()
    for li, (text, size, yc) in enumerate(zip(lines, sizes, ys)):
        lets, wd = hero_letters(text, size)
        fit = min(1.0, 960 / max(1, wd))
        t0 = words[li][1]
        for i, (c, lm, xoff) in enumerate(lets):
            st_ = t0 + 0.035 * i; v = clamp((t - st_) / 0.24, 0, 1)
            if v <= 0: continue
            ve = eout(v, 3.0); x = W / 2 + xoff * fit
            sc = (0.30 + 0.70 * ve + 0.06 * math.sin(math.pi * v)) * fit; rot = (1 - ve) * (24 if i % 2 else -24)
            ex = clamp((t - (t_end - 0.05 + 0.020 * i)) / 0.30, 0, 1)
            if ex >= 1: continue
            last = li == nl - 1
            if last:
                fill = eout(clamp((t - st_ - 0.12) / 0.34, 0, 1), 2.0); hh = lm.shape[0]; yy = np.linspace(1, 0, hh)[:, None]
                cm = cv2.GaussianBlur((yy < fill * 1.08).astype(np.float32), (0, 0), 3)
                cm = np.broadcast_to(cm, lm.shape)
                col = WHITE * (1 - cm[..., None]) + EMPH * 1.0 * cm[..., None]
            else:
                col = np.ones(lm.shape + (3,), np.float32) * WHITE
            pad = 26; lmp = np.pad(lm, pad); colp = np.pad(col, ((pad, pad), (pad, pad), (0, 0)), mode="edge")
            k_ = max(3, int(size * 0.06)) | 1                                         # the dark keyline (as the captions)
            key = cv2.dilate(lmp, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_, k_)))
            rgb = colp * lmp[..., None] + np.array([0.02, 0.02, 0.025], np.float32) * (key - lmp)[..., None]
            spr_l = np.dstack([rgb, key]).astype(np.float32)
            drift = (40 * ex) if tx["exit"] == "blood" else (-70 * ex)
            draw_sprite(lay, spr_l, x, yc + drift, sc * (1 + 0.12 * ex), rot + 25 * ex * (1 if i % 2 else -1), 1.0,
                        (0.1 + 5 * (1 - ve) + 6 * ex) if (v < 1 or ex > 0) else 0.0, (1 - ex) * ve)
            fl = math.sin(math.pi * clamp(v / 0.7, 0, 1)) * 0.55
            if fl > 0.02: out = add_glow(out, x, yc, size * 0.5, fl * 0.30, BONE if not last else BLOODH)
            if ex > 0:                                                                # the letters blow away as the edit's own particles
                rng = np.random.default_rng(i * 13 + li * 7)
                for q in range(4):
                    if tx["exit"] == "blood":
                        px = x + rng.uniform(-40, 40) * fit + rng.uniform(-30, 30) * ex; py = yc + 80 * ex + 900 * ex * ex * rng.uniform(0.6, 1.2)
                        draw_sprite(lay, spr, px, py, 0.6 + 0.6 * rng.random(), rng.uniform(-10, 10), 1.0, 0.0, math.sin(math.pi * min(1, ex * 1.3)), 1.0)
                    else:
                        px = x + rng.uniform(-50, 50) * fit + 30 * math.sin(ex * 6 + q); py = yc - 200 * ex * rng.uniform(0.7, 1.5)
                        draw_sprite(lay, spr, px, py, 0.5 + 0.9 * rng.random(), 0, 1.0, 0.0, math.sin(math.pi * min(1, ex * 1.2)))
    sh = cv2.GaussianBlur(lay[..., 3], (0, 0), 9)[..., None] * 0.6
    out = out * (1 - sh)
    out = out * (1 - lay[..., 3:4]) + lay[..., :3] * lay[..., 3:4]
    return np.clip(out, 0, 1)

def text_cap103(out, f, tx):
    """the v9 standard caption (keyline, red emphasis, eased words, auto-fit), with a per-caption line position (ys)."""
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
        for _ in range(6):
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

def text103(out, f):
    for tx in E.TEXT:
        if tx["style"] == "cap": out = text_cap103(out, f, tx)
        elif tx["style"] == "hero": out = hero103(out, f, tx)
    return out

# ---------------------------------------------------------------------------- finish
def finish103(out, f):
    out = out + 0.22 * (out - cv2.GaussianBlur(out, (0, 0), 1.5))                      # gentle unsharp for the 720p upscale
    L = lum(out); hi = np.clip(L - 0.62, 0, 1)
    halo = cv2.resize(cv2.GaussianBlur(cv2.resize(hi, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 8), (W, H))[..., None]
    red = np.clip((out[..., 2] - np.maximum(out[..., 0], out[..., 1])) * 2, 0, 1)
    rh = cv2.resize(cv2.GaussianBlur(cv2.resize(red, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 6), (W, H))[..., None]
    out = out + halo * (TEAL * 0.30 + BONE * 0.12) + rh * BLOODC * 0.18                 # cyan halation on highlights, a red bloom on blood
    L = lum(out)[..., None]
    out = out + grain(f, 1.0) * (0.012 + 0.020 * L * (1 - L) * 2.5)
    return np.clip(out * VIG, 0, 1)

# ---------------------------------------------------------------------------- rev 2: more graphics + transitions
_PV = {}
def pulse_fx(out, f):
    """a heartbeat: the edges of the frame pulse blood-red on every beat of the build."""
    t = f / FPS; e = 0.0
    for kb in E.PULSE_K:
        k = f - E.fh(kb)
        if 0 <= k < 16: e = max(e, math.exp(-k / 4.5) * (1.0 if (kb // 2) % 2 == 0 else 0.6))
    if e < 0.02: return out
    if "m" not in _PV:
        r = np.sqrt(((_GX - W / 2) / (W * 0.62)) ** 2 + ((_GY - H * 0.45) / (H * 0.58)) ** 2)
        _PV["m"] = np.clip((r - 0.55) / 0.6, 0, 1)[..., None] ** 1.6
    m = _PV["m"] * 0.55 * e
    return np.clip(out * (1 - m) + (out * 0.3 + BLOODC * 0.9) * m, 0, 1)

_DROPS = {}
def water_drop(img, cx, y, r):
    """a clear drop of water: it shows the frame flipped and magnified inside it, a bright rim and a highlight."""
    hh, ww = int(r * 3.2), int(r * 2.2); x0, y0 = int(cx - ww / 2), int(y - hh + r + 2)
    if y0 + hh < 0 or y0 > H: return img
    if "m" not in _DROPS or _DROPS["r"] != r:
        m = np.zeros((hh, ww), np.float32); cv2.circle(m, (ww // 2, hh - r - 2), r, 1.0, -1, cv2.LINE_AA)
        cv2.fillConvexPoly(m, np.array([[ww // 2, 2], [ww // 2 - r + 2, hh - r - 2], [ww // 2 + r - 2, hh - r - 2]], np.int32), 1.0, cv2.LINE_AA)
        m = cv2.GaussianBlur(m, (0, 0), 0.8); rim = np.clip(cv2.morphologyEx(m, cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8)), 0, 1)
        hl = np.zeros_like(m); cv2.circle(hl, (ww // 2 - r // 3, hh - r - r // 3), max(2, r // 4), 1.0, -1, cv2.LINE_AA)
        _DROPS.update(m=m, rim=rim, hl=cv2.GaussianBlur(hl, (0, 0), 1.2), r=r)
    m, rim, hl = _DROPS["m"], _DROPS["rim"], _DROPS["hl"]
    ya, yb, xa, xb = max(0, y0), min(H, y0 + hh), max(0, x0), min(W, x0 + ww)
    if yb <= ya or xb <= xa: return img
    sl = (slice(ya - y0, yb - y0), slice(xa - x0, xb - x0))
    gx, gy = np.meshgrid(np.arange(xa, xb, dtype=np.float32), np.arange(ya, yb, dtype=np.float32))
    ccy = y0 + hh - r - 2
    lens = cv2.remap(img, (cx - (gx - cx) * 3.0).astype(np.float32), (ccy - (gy - ccy) * 3.0).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    o = img.copy(); mm = m[sl][..., None]
    o[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - mm) + (lens * 0.85 + TEAL * 0.06) * mm + rim[sl][..., None] * BONE * 0.55 + hl[sl][..., None] * BONE * 0.9
    return o

def ripple_tr(A, B, j, f, sa, sb, pre=9, post=16):
    """rev 4: a clear drop of water falls into the frame: it hits, rings run outward refracting the picture, and the next
    shot opens behind the rings (no blood)."""
    cx, cy = W * 0.20, H * 0.76                                                        # off to the side, by his shoulder: never on the face
    if j < 0:
        u = (j + pre) / pre; y = -120 + (cy + 120) * ein(u, 1.8)
        return np.clip(water_drop(A, cx, y, 44), 0, 1)
    v = (j + 1) / post; R = 2100 * eout(v, 1.7)
    rr = np.sqrt((_GX - cx) ** 2 + ((_GY - cy) * 1.0) ** 2) + 1e-3
    wav = np.sin((rr - R) / 16.0) * np.exp(-((rr - R) / 110.0) ** 2) * 26 * (1 - v) + np.sin((rr - R * 0.6) / 22.0) * np.exp(-((rr - R * 0.6) / 90.0) ** 2) * 12 * (1 - v)
    src = B * np.clip((R - rr) / 40, 0, 1)[..., None] + A * (1 - np.clip((R - rr) / 40, 0, 1)[..., None])
    o = cv2.remap(src, (_GX + (_GX - cx) / rr * wav).astype(np.float32), (_GY + (_GY - cy) / rr * wav).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    hl = np.exp(-((rr - R) / 7.0) ** 2) * (1 - v) + 0.5 * np.exp(-((rr - R * 0.6) / 6.0) ** 2) * (1 - v)
    splash_ = np.exp(-(rr / (60 + 260 * v)) ** 2)[..., None] * (1 - v) ** 2
    o = o + splash_ * BONE * 0.35 + hl[..., None] * BONE * 0.45
    return np.clip(o, 0, 1)

_BUB = {}
def bubbles_tr(A, B, j, f, sa, sb, pre=7, post=12):
    """a surge of rising bubbles sweeps up the frame; the next shot is behind them."""
    u = clamp((j + pre) / (pre + post), 0, 1); front = H + 260 - (H + 700) * eout(u, 1.5)
    wob = 40 * np.sin(_GX / 110 + f * 0.3)
    m = np.clip((_GY - (front + wob)) / 80 + 0.5, 0, 1)[..., None]
    o = B * m + A * (1 - m)
    if "p" not in _BUB:
        rng = np.random.default_rng(91); _BUB["p"] = np.stack([rng.uniform(0, W, 420), rng.uniform(-200, 420, 420), rng.uniform(5, 34, 420), rng.uniform(0, 6.28, 420)], 1)
    lay = np.zeros((H // 2, W // 2), np.float32); fill = np.zeros((H // 2, W // 2), np.float32)
    for x, dy, r, ph in _BUB["p"]:
        y = front + dy - 120 * u; X = x + 10 * math.sin(f * 0.4 + ph)
        if -40 < y < H + 40:
            R = max(1, int(r / 2)); cv2.circle(lay, (int(X / 2), int(y / 2)), R, 1.0, max(1, R // 4), cv2.LINE_AA)
            cv2.circle(fill, (int(X / 2), int(y / 2)), R, 1.0, -1, cv2.LINE_AA)
            cv2.circle(lay, (int(X / 2 - R * 0.35), int(y / 2 - R * 0.35)), max(1, R // 4), 1.0, -1, cv2.LINE_AA)
    lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 0.6), (W, H))[..., None]; fill = cv2.resize(fill, (W, H))[..., None]
    ref = cv2.remap(o, (_GX + 18 * fill[..., 0]).astype(np.float32), (_GY - 22 * fill[..., 0]).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    o = o * (1 - fill * 0.6) + ref * fill * 0.6 + fill * TEAL * 0.12 + lay * BONE * 0.75
    return np.clip(o, 0, 1)

def moon_glow(out, f):
    L = lum(out); hi = np.clip(L - 0.55, 0, 1)
    halo = cv2.resize(cv2.GaussianBlur(cv2.resize(hi, (W // 4, H // 4)), (0, 0), 14), (W, H))[..., None]
    return np.clip(out + halo * (BONE * 0.9 + TEAL * 0.3) * 1.2, 0, 1)

TR2.update({"ripple": (ripple_tr, 9, 16), "bubbles_up": (bubbles_tr, 7, 12)})

# ---- rev 5: two transitions for the riff (replace the glass shatter and the duct tape)
def pupil_dive(A, B, j, f, sa, sb, pre=14, post=14):
    """into his eye: the camera dives at his eye, the pupil swallows the frame, and a round iris opens on the next shot."""
    rr = np.sqrt((_GX - W / 2) ** 2 + (_GY - H / 2) ** 2)
    if j < 0:
        u = (j + pre + 1) / (pre + 1); fs = face_scr(sa, f)
        if fs is None: ex, ey, fw = W / 2, H * 0.37, 320.0
        else:
            e = min((fs[3], fs[4]), key=lambda q: abs(q[0] - W / 2)); ex, ey, fw = e[0], e[1], fs[2]
        Z = max(10.0, W / (0.16 * fw)); sc = math.exp(math.log(Z) * ein(u, 2.4)); v = eout(clamp(u / 0.7, 0, 1), 2)
        M = cv2.getRotationMatrix2D((ex, ey), 4 * u, sc); M[0, 2] += (W / 2 - ex) * v; M[1, 2] += (H / 2 - ey) * v
        o = cv2.warpAffine(A, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        if sc > 1.4: o = radial_blur(o, W / 2, H / 2, 1.0, 1.0 + 0.07 * min(1.0, sc / 8), 6)
        pr = 1250 * ein(clamp((u - 0.58) / 0.42, 0, 1), 1.8)
        if pr > 1:                                                                     # the pupil swallows the frame
            pm = np.clip((pr - rr) / 14, 0, 1)[..., None]; ring = np.exp(-((rr - pr) / (10 + 0.05 * pr)) ** 2)[..., None]
            o = o * (1 - pm) + DEEP * 0.12 * pm + ring * (TEAL * 0.9 + BONE * 0.35)
        return np.clip(rgb_split(o, 12 * u), 0, 1)
    u = (j + 1) / post; R = 1250 * eout(u, 2.4)                                       # a round iris opens on the next shot
    m = np.clip((R - rr) / 3.0, 0, 1)[..., None]
    Bz = zoom_about(B, W / 2, H / 2, 1.3 - 0.3 * eout(u, 2))
    Bz = cv2.remap(Bz, (W / 2 + (_GX - W / 2) * (1 - 0.10 * (1 - u) * (rr / max(R, 1)) ** 2)).astype(np.float32),
                   (H / 2 + (_GY - H / 2) * (1 - 0.10 * (1 - u) * (rr / max(R, 1)) ** 2)).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    edge = np.exp(-((rr - R) / 7) ** 2)[..., None]
    o = Bz * m + (1 - m) * DEEP * 0.12 + edge * (TEAL * 0.8 + BONE * 0.5) * (1 - u) * 1.2
    return np.clip(rgb_split(o, 10 * (1 - u)), 0, 1)

def torch_blind(A, B, j, f, sa, sb, pre=9, post=12):
    """the flashlight swings into the lens: its flare streaks out and whites out the frame; the next shot burns back in out
    of the glare, brightest parts first."""
    if j < 0:
        u = (j + pre + 1) / (pre + 1); px, py = torch_point(A)
        rr = np.sqrt((_GX - px) ** 2 + (_GY - py) ** 2); R = 60 + 2600 * ein(u, 2.0)
        cone = np.exp(-(rr / R) ** 2)[..., None] * ein(u, 1.2)
        streak = np.exp(-((_GY - py) / (6 + 30 * u)) ** 2) * np.exp(-((_GX - px) / (500 + 900 * u)) ** 2)
        o = A + cone * (BONE * 1.5 + TEAL * 0.2) + streak[..., None] * (TEAL * 0.9 + BONE * 0.6) * (0.5 + u)
        return np.clip(o, 0, 1)
    v = (j + 1) / post; L = lum(B)[..., None]
    reveal = np.clip((L - (1 - eout(v, 1.5)) * 0.85) * 5 + v * 2.4, 0, 1)
    white = 1 - eout(v, 1.8)
    sy = H * 0.5; streak = np.exp(-((_GY - sy) / (4 + 30 * (1 - v))) ** 2)[..., None] * (1 - v) ** 1.5
    g = np.clip(white * 1.6, 0, 1) * (1 - reveal) + white * 0.25 * reveal                  # glare: highlights burn through first, then it clears
    o = B * (1 - g) + (BONE * 1.1 + TEAL * 0.1) * g + streak * (TEAL * 0.8 + BONE * 0.5)
    return np.clip(o, 0, 1)

TR2.update({"pupil_dive": (pupil_dive, 14, 14), "torch_blind": (torch_blind, 9, 12)})

# ---------------------------------------------------------------------------- frame
def base103(s, f):
    out = render_shot(s, f)
    if s.get("caustics"): out = caustics(out, f, s["caustics"])
    if s.get("snow"): out = snow(out, f, 0.6)
    if s.get("rain"): out = rain_glass(out, f, 0.8, 0.0)
    if s.get("swing"): out = lamp_swing(out, f, s)
    if s.get("flare"): out = anam_flare(out, s["flare"], f)
    if s.get("plastic"):
        a0, a1 = s["plastic"]; out = plastic_sheet(out, f, 0.9 * smooth((f / FPS - a0) / (a1 - a0)))
    if s.get("moonglow"): out = moon_glow(out, f)
    # rev 3: no blood drips or spatter overlays; rev 4: no scalpel cut, blood beads, slides or slide archive
    return out

_E3 = {}
def edge103(S_, which):
    key = (S_["n"], which)
    if key not in _E3:
        if len(_E3) > 6: _E3.clear()
        fr = S_["f0"] if which == "first" else S_["f1"] - 1
        _E3[key] = base103(S_, fr) if which == "last" else render_shot(S_, fr, False)
    return _E3[key]

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out = base103(s, f)
    if tin == "surface" and k < TR2["surface"][2]: out = surface_in(out, f, k)
    elif s["n"] == "boat": out = lens_drops(out, f, clamp(1.4 - f / FPS / 1.3, 0, 0.6))
    elif tin in TR2 and k < TR2[tin][2] and P is not None: out = TR2[tin][0](edge103(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge103(n_, "first"), kn, f, s, n_)
    out = pulse_fx(out, f)                                                            # (rev 3: the drifting slides are gone)
    out = beat_fx(out, f)                                                             # rev 4: the camera punches on the beat
    out = text103(out, f)
    if s.get("sink"): out = sink_end(out, f, s)
    out = finish103(out, f)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)

def init_hits():
    HITS.clear()
    HITS.append((E.fh(E.HDROP), 20, 4.0))                                             # the plastic rips open on the drop
    for kb in range(E.HDROP + 8, E.K_SPL, 8): HITS.append((E.fh(kb), 8, 3.0))
    HITS.append((E.fe(E.T_SPLASH), 10, 3.0))

# ============================================================================ v104 — THE PASSENGER (SUMI ink look; overrides the FOREVER section above)
INK = np.array([0.060, 0.045, 0.040], np.float32)      # BGR ink-black, a blue cast (lifted: never crushed)
PAPER = np.array([0.835, 0.905, 0.945], np.float32)   # BGR ivory paper
INKRED = np.array([0.055, 0.040, 0.720], np.float32)  # red ink
INKRED_H = np.array([0.32, 0.34, 1.00], np.float32)

def grade(img, s, f):
    """SUMI: luminance mapped onto an ink -> paper ramp with a soft S; only strong reds survive, as red ink."""
    g, gains = correction(s)
    x = np.clip(img * gains, 0, 1) ** g
    B_, G_, R_ = x[..., 0], x[..., 1], x[..., 2]
    red = np.clip((R_ - np.maximum(G_, B_) - s.get("redthr", 0.22)) * 4.0, 0, 1)[..., None]
    L = np.clip(B_ * 0.114 + G_ * 0.587 + R_ * 0.299, 0, 1)
    Lc = L * 0.62 + (L * L * (3 - 2 * L)) * 0.38                                       # soft S, shadows and highlights protected
    mono = INK + (PAPER - INK) * Lc[..., None]
    rc = Lc[..., None] + (x - L[..., None]) * 1.30
    rc = np.clip(rc * np.array([0.80, 0.80, 1.0], np.float32), 0, 1)
    return np.clip(mono * (1 - red) + rc * red, 0, 1)

def unify(out):
    """after the library transitions: drop any stray hue (their own palettes), keep the red ink."""
    B_, G_, R_ = out[..., 0], out[..., 1], out[..., 2]; L = lum(out)[..., None]
    red = np.clip((R_ - np.maximum(G_, B_) - 0.10) * 4.0, 0, 1)[..., None]
    mono = INK + (PAPER - INK) * np.clip((L - 0.03) / 0.92, 0, 1)
    return np.clip(out * red + (mono * 0.85 + L * 0.15) * (1 - red), 0, 1)

# ---------------------------------------------------------------------------- ink fields (noise at quarter res)
_NZ = {}
def nz(seed, cells=(24, 14)):
    key = (seed, cells)
    if key not in _NZ:
        a = _lowfreq((H // 4, W // 4), cells, seed) * 0.55 + _lowfreq((H // 4, W // 4), (cells[0] * 3, cells[1] * 3), seed + 1) * 0.30 \
            + _lowfreq((H // 4, W // 4), (cells[0] * 9, cells[1] * 9), seed + 2) * 0.15
        _NZ[key] = cv2.resize(a.astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    return _NZ[key]

def bloom_field(cx, cy, R, seed, rough=0.45):
    """signed distance-ish field of an ink bloom of radius R at (cx, cy): < 0 inside. Fractal, fingered edge."""
    n1, n2 = nz(seed), nz(seed + 10, (60, 34))
    wx = _GX + (n1 - 0.5) * R * 0.5; wy = _GY + (n2 - 0.5) * R * 0.5                  # domain warp: tendrils
    d = np.sqrt((wx - cx) ** 2 + ((wy - cy) * 0.92) ** 2)
    return d - R * (1 + rough * (nz(seed + 20, (40, 22)) - 0.5))

def ink_edge(fld, w=14.0):
    """mask (inside = 1) with a feathered, fibrous edge, and the dark rim where ink pools at the boundary."""
    m = np.clip(-fld / w + 0.5, 0, 1)
    rim = np.exp(-((fld + w * 0.6) / (w * 1.6)) ** 2)
    return m, rim

_PP = {}
def paper(f=0):
    """the paper: ivory with fibres and a faint mottle."""
    if "p" not in _PP:
        rng = np.random.default_rng(41); fib = np.zeros((H, W), np.float32)
        for _ in range(900):
            x, y = rng.uniform(0, W), rng.uniform(0, H); a = rng.uniform(0, math.pi); L_ = rng.uniform(20, 90)
            cv2.line(fib, (int(x), int(y)), (int(x + L_ * math.cos(a)), int(y + L_ * math.sin(a))), float(rng.uniform(0.3, 1.0)), 1, cv2.LINE_AA)
        fib = cv2.GaussianBlur(fib, (0, 0), 0.7)
        mott = nz(51, (12, 7))
        _PP["p"] = np.clip(PAPER * (0.965 + 0.05 * mott[..., None]) - fib[..., None] * 0.035, 0, 1).astype(np.float32)
        _PP["fib"] = fib
    return _PP["p"]

def ink_drift(out, f, amt=1.0):
    """ink seeps through the shadows: slow tendrils that darken only the dark parts of the frame."""
    if amt <= 0: return out
    t = f / FPS; n = nz(61, (18, 10)); n2 = nz(62, (30, 16))
    sh = int(20 * t) % W; m = np.roll(n, sh, 1) * 0.6 + np.roll(n2, -int(14 * t) % H, 0) * 0.4
    m = np.clip((m - 0.52) * 3.0, 0, 1)
    L = lum(out)[..., None]
    k = m[..., None] * (1 - np.clip(L / 0.45, 0, 1)) ** 1.5 * 0.55 * amt
    return np.clip(out * (1 - k) + INK * k, 0, 1)

# ---------------------------------------------------------------------------- THE INK DROP (open + loop)
def drop_shape(r, stretch=1.0):
    h, w = int(r * 3.4 * stretch) + 8, int(r * 2.3) + 8; m = np.zeros((h, w), np.float32)
    cy = h - r - 4; cv2.circle(m, (w // 2, cy), r, 1.0, -1, cv2.LINE_AA)
    cv2.fillConvexPoly(m, np.array([[w // 2, 3], [w // 2 - int(r * 0.92), cy - int(r * 0.25)], [w // 2 + int(r * 0.92), cy - int(r * 0.25)]], np.int32), 1.0, cv2.LINE_AA)
    m = cv2.GaussianBlur(m, (0, 0), 1.0)
    hl = np.zeros_like(m); cv2.ellipse(hl, (w // 2 - r // 3, cy - r // 3), (max(2, r // 4), max(2, r // 3)), -30, 0, 360, 1.0, -1, cv2.LINE_AA)
    col = np.dstack([m * 0] * 3) + INK
    col = col + cv2.GaussianBlur(hl, (0, 0), 1.5)[..., None] * 0.55
    return np.dstack([np.clip(col, 0, 1), m]).astype(np.float32)

DROP_Y = H * 0.40                                                                      # where the drop lands (between his eyes' height, above the face centre)
def drop_at(f):
    """the drop's position, size and stretch over the pickup: forms at the top edge, swells on each synth note, falls."""
    k = f / FPS / E.HB
    if k < 9:                                                                          # hanging at the top, swelling on k0, 3, 6
        sw = sum(math.exp(-max(0, k - kn) / 0.8) * 0.12 for kn in (0, 3, 6) if k >= kn)
        r = 10 + 14 * (k / 9) ** 0.8; return W / 2, -r * 1.2 + 70 * (k / 9) ** 2, r * (1 + sw), 1.0 + 0.4 * (k / 9)
    u = clamp((k - 9) / 3.0, 0, 1)                                                     # falls k9 -> k12 (lands on the bass)
    y = 70 + (DROP_Y - 70) * u * u; return W / 2, y, 24, 1.0 + 1.6 * u

def open_paper(a=0.10):
    """the paper of the pickup: the first shot washed faintly into it (the loop drains back onto exactly this)."""
    if ("op", a) not in _PP:
        ghost = render_shot(E.SHOTS[1], E.SHOTS[1]["f0"], False); gL = lum(ghost)[..., None]
        _PP[("op", a)] = np.clip(paper() * (1 - a * (1 - gL)) + INK * a * (1 - gL) * 0.3, 0, 1).astype(np.float32)
    return _PP[("op", a)]

def ink_open(f, s):
    """pickup: paper, a ghost of the first shot washed into it, and the drop."""
    a = 0.10 + 0.05 * smooth(f / FPS / (12 * E.HB))
    o = open_paper(0.10) * (1 - smooth(f / FPS / (12 * E.HB))) + open_paper(0.15) * smooth(f / FPS / (12 * E.HB))
    x, y, r, stv = drop_at(f)
    lay = np.zeros((H, W, 4), np.float32); draw_sprite(lay, drop_shape(int(r)), x, y, 1.0, 0, 1.0, 0.0, 1.0, 1.0 / stv)
    sh = cv2.GaussianBlur(lay[..., 3], (0, 0), 10)[..., None] * 0.20
    o = o * (1 - np.roll(sh, 26, 0))
    return np.clip(o * (1 - lay[..., 3:4]) + lay[..., :3] * lay[..., 3:4], 0, 1)

def ink_bloom(A, B, j, f, sa, sb, post=30):
    """the drop hits on the bass: a crown of ink flies out, and the bloom spreads into him (the picture lives in the ink)."""
    u = (j + 1) / post; R = 2300 * eout(u, 1.9) + 30
    fld = bloom_field(W / 2, DROP_Y, R, 71); m, rim = ink_edge(fld, 10 + 30 * u)
    wet = (1 - u) ** 1.5
    inner = B * (1 - 0.35 * wet) + INK * 0.35 * wet
    o = A * (1 - m[..., None]) + inner * m[..., None]
    o = o * (1 - rim[..., None] * 0.75 * (1 - u * 0.6)) + INK * rim[..., None] * 0.75 * (1 - u * 0.6)
    if j < 10:                                                                         # the crown: droplets thrown out of the impact
        rng = np.random.default_rng(72); lay = np.zeros((H // 2, W // 2), np.float32); k = j + 1
        for i in range(70):
            a_ = rng.uniform(0, 2 * math.pi); sp = rng.uniform(400, 1500); r_ = rng.uniform(2, 7)
            x = W / 2 + math.cos(a_) * sp * k / 60; y = DROP_Y + math.sin(a_) * sp * k / 60 * 0.9 + 600 * (k / 60) ** 2
            cv2.ellipse(lay, (int(x / 2), int(y / 2)), (int(r_ * 1.6), int(r_)), math.degrees(a_), 0, 360, 1.0, -1, cv2.LINE_AA)
        lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 0.7), (W, H))[..., None] * (1 - k / 10) ** 0.5
        o = o * (1 - lay * 0.95) + INK * lay * 0.95
    return np.clip(o, 0, 1)

def ink_out(out, f, s):
    """the loop: the picture drains back into a single blob of ink, which pulls into a drop and lifts off the paper."""
    k0 = s["ink_out"]["k0"]; k = f / FPS / E.HB
    if k < k0: return out
    u = clamp((k - k0) / (E.K_END - 1.2 - k0), 0, 1)
    R = 2300 * (1 - ein(u, 1.4)) + 24
    fld = bloom_field(W / 2, DROP_Y, R, 81, rough=0.45 * (1 - u) + 0.05); m, rim = ink_edge(fld, 10 + 40 * (1 - u))
    pp = open_paper(0.10)
    o = pp * (1 - m[..., None]) + out * m[..., None]
    o = o * (1 - rim[..., None] * 0.7) + INK * rim[..., None] * 0.7
    if u > 0.82:                                                                       # the last blob becomes the drop and lifts away
        v = (u - 0.82) / 0.18; lay = np.zeros((H, W, 4), np.float32)
        y = DROP_Y - (DROP_Y + 120) * ein(v, 2.2)
        draw_sprite(lay, drop_shape(24), W / 2, y, 1.0, 180, 1.0, 0.0, 1.0, 1.0 / (1 + 1.4 * v))
        o = o * (1 - lay[..., 3:4]) + lay[..., :3] * lay[..., 3:4]
        o = pp * smooth(v * 1.5) + o * (1 - smooth(v * 1.5)) if v > 0.4 else o
        if v > 0.4: o = o * (1 - lay[..., 3:4]) + lay[..., :3] * lay[..., 3:4]
    return np.clip(o, 0, 1)

# ---------------------------------------------------------------------------- brush strokes
def brush_tr(A, B, j, f, sa, sb, pre=5, post=11):
    """a loaded sumi brush sweeps across the frame: a band of ink with a wet, ragged front and a dry, streaky tail; the
    next shot is under the paint behind it. brush=dict(ang, seed, red)."""
    p = sb.get("brush", {}); ang = math.radians(p.get("ang", -25)); seed = p.get("seed", 3); red = p.get("red", False)
    u = clamp((j + pre + 0.5) / (pre + post), 0, 1)
    ca, sa_ = math.cos(ang), math.sin(ang)
    s_ = (_GX - W / 2) * ca + (_GY - H / 2) * sa_; q = -(_GX - W / 2) * sa_ + (_GY - H / 2) * ca
    L = abs(W * ca) + abs(H * sa_); Wb = 560
    head = -L / 2 - 120 + (L + Wb + 240) * ein(u, 1.25)
    key = "b" + str(seed)
    if key not in _PP:
        rng = np.random.default_rng(seed); n = 4400
        prof = np.cumsum(rng.normal(0, 1, n)); prof = (prof - prof.mean()) / (prof.std() + 1e-6)
        dry = np.convolve(rng.random(n), np.ones(9) / 9, "same"); dry = (dry - dry.min()) / (dry.max() - dry.min() + 1e-6)
        streak = np.convolve(rng.random(n), np.ones(3) / 3, "same")
        _PP[key] = (prof.astype(np.float32), dry.astype(np.float32), streak.astype(np.float32))
    prof, dry, streak = _PP[key]
    qi = np.clip((q + 2200).astype(np.int32), 0, 4399)
    front = head + prof[qi] * 22
    tail = front - Wb * (0.45 + 0.55 * dry[qi])                                         # dry brush: the tail breaks up per bristle
    ahead = (s_ > front).astype(np.float32)[..., None]
    pos = np.clip((s_ - tail) / np.maximum(front - tail, 1), 0, 1)
    band = ((s_ <= front) & (s_ >= tail)).astype(np.float32)
    dens = band * pos ** 0.55 * (0.72 + 0.28 * streak[qi])
    dens = np.clip(dens + np.exp(-((s_ - front) / 7) ** 2) * 0.4, 0, 1)[..., None]
    col = INKRED if red else (PAPER * 0.97 if p.get("white") else INK)
    o = A * ahead + B * (1 - ahead)
    gloss = np.exp(-((s_ - front + 14) / 5) ** 2)[..., None] * 0.18 * (u < 0.97)
    return np.clip(o * (1 - dens * 0.96) + col * dens * 0.96 + gloss * PAPER, 0, 1)

def enso_tr(A, B, j, f, sa, sb, pre=10, post=12):
    """an enso: one brush circle is drawn around the frame's centre, the next shot appears inside it, then it opens out."""
    rr, aa = polar(); cy_off = 0
    if j < 0:
        u = (j + pre + 1) / (pre + 1); R0 = 330; Rw = 70
        sweep = ((aa + math.pi / 2) % (2 * math.pi)) / (2 * math.pi)                   # starts at 12 o'clock, clockwise
        drawn = (sweep < u).astype(np.float32)
        ring = np.exp(-((rr - R0) / Rw) ** 4) * drawn
        dry = 0.65 + 0.35 * np.sin(rr / 2.3 + nz(91, (40, 22)) * 9)
        tail = 1 - 0.6 * np.clip((u - sweep) * 6, 0, 1) * (sweep > u - 0.15)
        ink = np.clip(ring * dry * tail, 0, 1)[..., None]
        inside = np.clip((R0 - rr) / 8, 0, 1)[..., None] * smooth((u - 0.6) / 0.4)
        o = A * (1 - inside) + B * inside
        return np.clip(o * (1 - ink * 0.95) + INK * ink * 0.95, 0, 1)
    v = (j + 1) / post; R0 = 330 + 1700 * eout(v, 2.2); Rw = 70 * (1 + 2 * v)
    inside = np.clip((R0 - rr) / 10, 0, 1)[..., None]
    ring = np.exp(-((rr - R0) / Rw) ** 4)[..., None] * (1 - v)
    o = A * (1 - inside) + B * inside
    return np.clip(o * (1 - ring * 0.9) + INK * ring * 0.9, 0, 1)

# ---------------------------------------------------------------------------- ink bleed (phrase start): ink seeps in from several points and retracts
def ink_bleed(A, B, j, f, sa, sb, pre=12, post=14):
    pts = [(0.22, 0.20), (0.80, 0.33), (0.30, 0.78), (0.74, 0.86), (0.52, 0.50)]
    if j < 0: u = (j + pre + 1) / (pre + 1); R = 660 * ein(u, 1.6)                     # the blooms meet but leave gaps: never a dead black frame
    else: u = (j + 1) / post; R = 660 * (1 - eout(u, 1.8))
    fld = None
    for i, (px, py) in enumerate(pts):
        fl = bloom_field(W * px, H * py, R * (0.7 + 0.12 * i), 101 + i * 3, 0.55)
        fld = fl if fld is None else np.minimum(fld, fl)
    m, rim = ink_edge(fld, 16)
    base = A if j < 0 else B
    o = base * (1 - m[..., None]) + INK * m[..., None]
    o = o * (1 - rim[..., None] * 0.5) + INK * rim[..., None] * 0.5
    return np.clip(o, 0, 1)

# ---------------------------------------------------------------------------- THE SPATTER (P3): red ink on the lens, it hangs, then runs
_SP = {}
def spatter_layer(cx, cy, seed=17):
    key = (int(cx), int(cy), seed)
    if key in _SP: return _SP[key]
    rng = np.random.default_rng(seed); X, Y = cx / 2, cy / 2
    hh, ww = H // 2, W // 2; gy, gx = np.mgrid[0:hh, 0:ww].astype(np.float32)
    n1 = cv2.resize(nz(161, (40, 22)), (ww, hh)); n2 = cv2.resize(nz(162, (90, 50)), (ww, hh))
    d = np.sqrt((gx - X) ** 2 + ((gy - Y) * 1.15) ** 2)
    m = np.clip((52 * (1 + 0.55 * (n1 - 0.5) + 0.25 * (n2 - 0.5)) - d) / 2.0, 0, 1)   # the main splash: an organic body
    ang = np.arctan2(gy - Y, gx - X)
    fingers = np.clip((90 * (0.6 + 0.8 * (np.sin(ang * 9 + n1 * 6) * 0.5 + 0.5)) - d) / 2.0, 0, 1) * (np.abs(np.cos(ang)) > 0.2)
    m = np.maximum(m, fingers * (d < 95))
    drops = []
    for _ in range(70):                                                                 # spatter thrown left (and a little up/down): elongated drops with tails
        a = rng.uniform(math.pi * 0.72, math.pi * 1.20); dd = rng.uniform(70, 300); r = max(1.5, rng.uniform(2.5, 11) * (1 - dd / 380))
        x, y = X + math.cos(a) * dd, Y + math.sin(a) * dd * 0.8
        cv2.ellipse(m, (int(x), int(y)), (int(r * (1.3 + dd / 160)), int(r)), math.degrees(a), 0, 360, 1.0, -1, cv2.LINE_AA)
        cv2.line(m, (int(x), int(y)), (int(x + math.cos(a) * r * 3.2), int(y + math.sin(a) * r * 2.6)), 1.0, max(1, int(r / 3)), cv2.LINE_AA)
        if r > 5: drops.append((x * 2, y * 2, r * 2))
    for _ in range(220):                                                                # fine mist
        a = rng.uniform(math.pi * 0.6, math.pi * 1.35); dd = rng.uniform(40, 260)
        cv2.circle(m, (int(X + math.cos(a) * dd), int(Y + math.sin(a) * dd * 0.8)), 1, float(rng.uniform(0.5, 1)), -1, cv2.LINE_AA)
    drops.sort(key=lambda q: -q[2])
    big = [(X * 2 + rng.uniform(-60, 40), Y * 2 + rng.uniform(10, 60), rng.uniform(14, 22)) for _ in range(4)]
    m = cv2.resize(cv2.GaussianBlur(m, (0, 0), 0.8), (W, H))
    gx_ = cv2.Sobel(m, cv2.CV_32F, 1, 0, ksize=7); gy_ = cv2.Sobel(m, cv2.CV_32F, 0, 1, ksize=7)
    nrm = np.sqrt(gx_ ** 2 + gy_ ** 2) + 1e-6; spec = (np.clip((-gx_ * 0.5 - gy_ * 0.85) / nrm, 0, 1) ** 10) * np.clip(m * 1.5, 0, 1)
    _SP[key] = (m.astype(np.float32), spec.astype(np.float32), big + drops[:10]); return _SP[key]

def spatter_fx(out, f, s):
    p = s["spat"]; k = f / FPS / E.HB - p["k"]
    if k < 0: return out
    m, spec, drops = spatter_layer(W * p["x"], H * p["y"])
    grow = eout(clamp(k * 1.6, 0, 1), 3)                                                # it lands in a few frames
    run = clamp((k - 1.5) / 6.0, 0, 1)                                                  # then the heavy drops run down
    mm = m * grow
    if run > 0:
        rl = np.zeros((H // 2, W // 2), np.float32)
        for (x, y, r) in drops[:14]:
            ln = (60 + r * 9) * ein(run, 1.4)
            cv2.line(rl, (int(x / 2), int(y / 2)), (int(x / 2), int((y + ln) / 2)), 1.0, max(1, int(r / 5)), cv2.LINE_AA)
            cv2.circle(rl, (int(x / 2), int((y + ln) / 2)), max(1, int(r / 3.5)), 1.0, -1, cv2.LINE_AA)
        mm = np.maximum(mm, cv2.resize(cv2.GaussianBlur(rl, (0, 0), 0.8), (W, H)))
    fade = 1 - smooth((k - 7.0) / 1.0)
    mm = mm[..., None] * fade
    ref = cv2.remap(out, (_GX + mm[..., 0] * 10).astype(np.float32), (_GY + mm[..., 0] * 14).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    body = INKRED * (0.65 + 0.35 * np.clip(mm * 1.2, 0, 1)) + ref * 0.10
    o = out * (1 - mm * 0.92) + body * mm * 0.92
    return np.clip(o + spec[..., None] * fade * INKRED_H * 0.6, 0, 1)

def spatter_tr(A, B, j, f, sa, sb, post=4):
    """the cut on the downbeat: a two-frame red impact, then the shot (the spatter itself is spatter_fx on the shot)."""
    if j < 2:
        L = lum(B)[..., None]; return np.clip(INKRED * (0.4 + 0.8 * L) + (1 - L) * 0.02, 0, 1)
    return B

# ---------------------------------------------------------------------------- THE PASSENGER (P4): his ink shadow peels off, towers, lunges
def passenger_fx(f, s):
    p = s["passenger"]; k = f / FPS / E.HB
    img, msk = render_shot(s, f, True, True)
    if k < p["k_rise"]: return img
    u = clamp((k - p["k_rise"]) / (p["k_lunge"] - p["k_rise"]), 0, 1)                # rise (steps on the bass hits)
    v = clamp((k - p["k_lunge"]) / (s["k1"] - 0.6 - p["k_lunge"]), 0, 1)             # lunge
    body = msk * (_GY < H * p.get("cut_y", 1.0))                                        # him only (not the table he leans on)
    ys, xs = np.nonzero(body > 0.5)
    if len(xs) < 50: return img
    ax, ay = float(np.median(xs)), float(ys.max())                                     # anchored at his base
    sc = 1.02 + 0.30 * eout(u, 2.0) + 6.0 * ein(v, 2.4)                                # a little bigger than him, rising, then the lunge
    off = (-300 * eout(u, 2.0) - 60) * (1 - ein(v, 1.5)); lift = (-170 * eout(u, 2.0) - 30) * (1 - v)
    sway = 14 * math.sin(k * 0.9)
    M = np.float32([[sc, 0, ax - sc * ax + off + sway], [0, sc, ay - sc * ay + lift]])
    sh = cv2.warpAffine(body, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    sh = cv2.GaussianBlur(sh, (0, 0), 3 + 10 * v)
    n = nz(121, (40, 22)); fib = np.clip((sh - 0.15 - 0.35 * (n - 0.5)) * 3.0, 0, 1)    # fibrous ink edges
    wisp = np.clip((cv2.GaussianBlur(np.roll(sh, -int(40 + 60 * u), 0), (0, 0), 18) - 0.2) * 1.2, 0, 1) * (n > 0.5) * 0.5 * (1 - v)
    shadow = np.clip(np.maximum(fib, wisp), 0, 1)[..., None] * (0.25 + 0.75 * smooth(u * 3))
    redge = np.exp(-((fib - 0.5) / 0.16) ** 2)[..., None] * smooth(u * 3) * (1 - v) * (1 - msk[..., None]) * 0.75
    keep = msk[..., None] * (1 - smooth((v - 0.35) / 0.4))                              # he stays in front until the lunge swallows him
    wash = smooth(u * 2.5) * 0.88 * (1 - msk[..., None]) * (_GY < H * p.get("cut_y", 1.0))[..., None]   # behind him, the wall goes to paper
    img = img * (1 - wash) + paper() * wash
    o = img * (1 - shadow * (1 - keep) * 0.94) + INK * shadow * (1 - keep) * 0.94
    o = o * (1 - redge) + INKRED * redge                                                # rev 2: a red-ink edge on the figure
    return np.clip(o, 0, 1)

def passenger_tr(A, B, j, f, sa, sb, post=16):
    """out of the ink: the frame was swallowed by the shadow; the next shot surfaces through thinning, fibrous ink."""
    v = (j + 1) / post; R = 2300 * eout(v, 1.8) + 20
    fld = bloom_field(W / 2, H * 0.40, R, 131, 0.6); m, rim = ink_edge(fld, 20)
    o = INK * (1 - m[..., None]) + B * m[..., None]
    return np.clip(o * (1 - rim[..., None] * 0.6) + INK * rim[..., None] * 0.6, 0, 1)

# ---------------------------------------------------------------------------- THE SILHOUETTE (P5): his body is a window into the kill room
def silhouette_fx(f, s):
    p = s["window"]; k = f / FPS / E.HB
    img, msk = render_shot(s, f, True, True)
    a_in = smooth((k - p["k_in"] - 0.5) / 2.0); a_out = 1 - smooth((k - p["k_out"]) / 1.0)
    a = a_in * a_out
    if a <= 0.001: return img
    win = dict(n=s["n"] + "_win", src=p["src"], t0=s["t0"], t1=s["t1"], tmap=[(0, p["a"]), (1, p["a"] + (s["t1"] - s["t0"]))], look="sumi",
               z=[(0, 1.15), (1, 1.25)], face=None, cx=(640, 640), interp="hold", f0=s["f0"], f1=s["f1"])
    wimg = render_shot(win, f, False)
    n = nz(141, (40, 22)); m2 = np.clip((msk - 0.5 - 0.25 * (n - 0.5)) * 6, 0, 1)[..., None]
    rim = np.exp(-((msk - 0.45) / 0.12) ** 2)[..., None]
    outside = img * (1 - 0.85 * a) + paper() * 0.85 * a                               # the world goes to paper
    outside = outside * (1 - (1 - lum(img)[..., None]) * 0.25 * a)
    fs = face_scr(s, f)
    if fs is not None:                                                                  # his face stays; his body becomes the kill room
        fx_, fy_, fw_ = fs[0], fs[1], max(120.0, fs[2])
        fm = np.exp(-(((_GX - fx_) / (0.75 * fw_)) ** 2 + ((_GY - fy_) / (0.95 * fw_)) ** 2) ** 1.5)[..., None]
    else: fm = np.zeros((H, W, 1), np.float32)
    body = np.clip(wimg * 1.55, 0, 1) * (1 - fm) + img * fm
    inside = img * (1 - a) + body * a
    o = outside * (1 - m2) + inside * m2
    return np.clip(o * (1 - rim * 0.8 * a) + INK * rim * 0.8 * a, 0, 1)

def anam_flare104(out, amt, f):
    L = lum(out); hi = np.clip((L - 0.80) / 0.20, 0, 1) ** 2
    sm = cv2.resize(hi, (W // 8, H // 8), interpolation=cv2.INTER_AREA)
    streak = cv2.resize(cv2.GaussianBlur(sm, (0, 0), sigmaX=34, sigmaY=0.7), (W, H))
    glow = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 4), (W, H))
    fl = (0.92 + 0.08 * math.sin(f * 0.9)) * amt
    return np.clip(out + (np.clip(streak * 22, 0, 1.2)[..., None] * PAPER * 0.85 + np.clip(glow * 3, 0, 1)[..., None] * PAPER * 0.25) * fl, 0, 1)

TR2.update({"ink_bloom": (ink_bloom, 0, 30), "brush": (brush_tr, 4, 10), "enso": (enso_tr, 10, 12), "ink_bleed": (ink_bleed, 12, 14),
            "spatter": (spatter_tr, 0, 4), "passenger": (passenger_tr, 0, 16)})

# ---------------------------------------------------------------------------- finish + frame
def finish104(out, f):
    out = out + 0.18 * (out - cv2.GaussianBlur(out, (0, 0), 1.5))                      # gentle sharpen for the 720p upscale
    L = lum(out); hi = np.clip(L - 0.66, 0, 1)
    halo = cv2.resize(cv2.GaussianBlur(cv2.resize(hi, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 8), (W, H))[..., None]
    red = np.clip((out[..., 2] - np.maximum(out[..., 0], out[..., 1])) * 2, 0, 1)
    rh = cv2.resize(cv2.GaussianBlur(cv2.resize(red, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 6), (W, H))[..., None]
    out = out + halo * PAPER * 0.22 + rh * INKRED * 0.16                               # paper-white bloom, a red bloom on red ink
    paper(); fib = _PP["fib"][..., None]; L = lum(out)[..., None]
    out = out * (1 - fib * 0.05 * L)                                                    # the paper's fibres show in the highlights
    if "v" not in _PP:                                                                  # an ink-bled vignette: irregular, not a perfect oval
        r = np.sqrt(((_GX - W / 2) / (W * 0.62)) ** 2 + ((_GY - H * 0.46) / (H * 0.60)) ** 2)
        _PP["v"] = np.clip((r - 0.78 - 0.18 * (nz(151, (16, 9)) - 0.5)) / 0.35, 0, 1)[..., None] ** 1.4 * 0.55
    v = _PP["v"]; out = out * (1 - v) + INK * v
    L = lum(out)[..., None]
    return np.clip(out + grain(f, 1.0) * (0.010 + 0.018 * L * (1 - L) * 2.5), 0, 1)

def base104(s, f):
    if s.get("graphic") == "ink_open": return ink_open(f, s)
    if s.get("passenger"): out = passenger_fx(f, s)
    elif s.get("window"): out = silhouette_fx(f, s)
    else: out = render_shot(s, f)
    if s.get("flare"): out = anam_flare104(out, s["flare"], f)
    if s.get("spat"): out = spatter_fx(out, f, s)
    out = ink_drift(out, f, s.get("drift", 1.0))
    return out

_E4 = {}
def edge104(S_, which):
    key = (S_["n"], which)
    if key not in _E4:
        if len(_E4) > 6: _E4.clear()
        fr = S_["f0"] if which == "first" else S_["f1"] - 1
        _E4[key] = base104(S_, fr)
    return _E4[key]

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out = base104(s, f); logo = False
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge104(P, "last"), out, k, f, P, s); logo = logo or tin == "logo_orig"
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]:
            out = TR2[nt][0](out, edge104(n_, "first"), kn, f, s, n_); logo = logo or nt == "logo_orig"
    if s.get("ink_out"): out = ink_out(out, f, s)
    out = beat_fx(out, f)
    if not logo: out = unify(out)
    out = text103(out, f)
    out = finish104(out, f)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)

def init_hits():
    HITS.clear()
    for k_, a in ((12, 14), (44, 9), (76, 20), (108, 8), (112, 10), (120, 14), (140, 10)): HITS.append((E.fh(k_), a, 4.0))


# ============================================================================ v104 rev 2: more animation, graphics and polish
def beat_fx(out, f):
    """the camera punches on the sub-bass: a zoom kick with a short radial motion blur on the strong hits and a chromatic kick
    on the half-bars."""
    z = 0.0; ch = 0.0
    for k, a in E.BEAT_PUNCH:
        kk = f - E.fh(k)
        if a > 0 and 0 <= kk < 14:
            e = a * math.exp(-kk / 3.5); z = max(z, e)
            if a >= 0.9: ch = max(ch, e)
    if z < 0.01: return out
    o = zoom_about(out, W / 2, H * 0.42, 1 + 0.045 * z)
    if z > 0.45: o = radial_blur(o, W / 2, H * 0.42, 1.0, 1 + 0.030 * z, 4)
    if ch > 0.05: o = rgb_split(o, 9 * ch)
    return np.clip(o * (1 + 0.10 * z), 0, 1)

def cam_float(out, f, s):
    """a slow, breathing camera float on every hold, so no frame sits dead."""
    ph = (sum(map(ord, s["n"])) % 97) / 97 * 6.28; t = f / FPS
    px = W / 2 + 9 * math.sin(t * 1.3 + ph); py = H * 0.45 + 7 * math.cos(t * 1.1 + ph * 0.7)
    return zoom_about(out, px, py, 1.018, 0.22 * math.sin(t * 0.9 + ph))

def spin_fx(out, f, s):
    """the upside-down shot keeps turning: a slow roll through the hold (zoomed to cover the corners)."""
    a0, a1 = s["spin"]; u = clamp((f - s["f0"]) / max(1, s["f1"] - s["f0"]), 0, 1)
    return zoom_about(out, W / 2, H * 0.45, 1.13, a0 + (a1 - a0) * eout(u, 1.6))

def ghost_fx(out, f, s):
    """ink ghost trails: the last moments of the motion linger as darker echoes behind him."""
    a = s["ghost"]; f1, f2 = max(s["f0"], f - 3), max(s["f0"], f - 6)
    if f2 >= f: return out
    p1 = render_shot(s, f1, False); p2 = render_shot(s, f2, False)
    trail = cv2.GaussianBlur(np.minimum(p1, p2 * 1.03), (0, 0), 1.5) * 0.96 + INK * 0.04
    return np.clip(out * (1 - a) + np.minimum(out, trail) * a, 0, 1)

def quarter_roll(A, B, j, f, sa, sb, pre=7, post=9):
    """a quarter turn: the frame rolls 90 degrees into a rotational blur and the next shot rolls out of it upright."""
    if j < 0: u = (j + pre + 1) / (pre + 1); img = A; ang = 90 * ein(u, 2.2); z = 1 + 0.85 * ein(u, 2.0)
    else: v = (j + 1) / post; img = B; ang = -90 * (1 - eout(v, 2.2)); z = 1 + 0.85 * (1 - eout(v, 2.0))
    span = 10 * (1 - abs(ang) / 90 * 0) * min(1.0, abs(ang) / 30 + 0.2)
    acc = None
    for i in range(5):
        w_ = zoom_about(img, W / 2, H * 0.45, z, ang + (i - 2) / 2 * span)
        acc = w_ if acc is None else acc + w_
    return np.clip(acc / 5, 0, 1)

TR2["quarter_roll"] = (quarter_roll, 7, 9)

def edge_seep(o, f):
    """during the pickup, ink creeps in from the paper's corners (nothing at frame 0, so the loop still matches)."""
    k = f / FPS / E.HB; R = 330 * smooth(k / 12) ** 1.3
    if R < 2: return o
    fld = None
    for i, (cx, cy) in enumerate(((-40, -40), (W + 40, -40), (-40, H + 40), (W + 40, H + 40))):
        fl = bloom_field(cx, cy, R * (0.8 + 0.15 * i), 171 + i, 0.6)
        fld = fl if fld is None else np.minimum(fld, fl)
    m, rim = ink_edge(fld, 14)
    return np.clip(o * (1 - m[..., None] * 0.92) + INK * m[..., None] * 0.92 - rim[..., None] * 0.05, 0, 1)

_ink_open0 = ink_open
def ink_open(f, s):
    return edge_seep(_ink_open0(f, s), f)

_finish0 = finish104
def finish104(out, f):
    """the ink-bled vignette breathes in on each phrase start."""
    e = 0.0
    for p in E.PHR[1:]:
        kk = f - E.fh(p)
        if 0 <= kk < 40: e = max(e, math.exp(-kk / 9))
    if e > 0.02:
        paper(); r = np.sqrt(((_GX - W / 2) / (W * 0.62)) ** 2 + ((_GY - H * 0.46) / (H * 0.60)) ** 2)
        if "vb" not in _PP: _PP["vb"] = np.clip((r - 0.62 - 0.18 * (nz(151, (16, 9)) - 0.5)) / 0.35, 0, 1)[..., None] ** 1.4
        vb = _PP["vb"] * 0.45 * e; out = out * (1 - vb) + INK * vb
    return _finish0(out, f)

def base104(s, f):
    if s.get("graphic") == "ink_open": return ink_open(f, s)
    if s.get("passenger"): out = passenger_fx(f, s)
    elif s.get("window"): out = silhouette_fx(f, s)
    else: out = render_shot(s, f)
    if s.get("ghost"): out = ghost_fx(out, f, s)
    if s.get("flare"): out = anam_flare104(out, s["flare"], f)
    if s.get("spat"): out = spatter_fx(out, f, s)
    out = ink_drift(out, f, s.get("drift", 1.0))
    if s.get("spin"): out = spin_fx(out, f, s)
    else: out = cam_float(out, f, s)
    return out

# ============================================================================ v104 rev 3: a fuller opening, and THE PASSENGER rebuilt
# ---- the pickup: an ink sketch of him draws itself on the paper, stroke by stroke, on the synth notes
def sketch_layer():
    """line art of the first shot (edges of the graded frame, thickened and softened) + a light wash in the darkest areas."""
    if "sk" not in _PP:
        img = render_shot(E.SHOTS[1], E.SHOTS[1]["f0"], False); L = lum(img)
        L8 = (cv2.GaussianBlur(L, (0, 0), 1.6) * 255).astype(np.uint8)
        ed = cv2.Canny(L8, 18, 55).astype(np.float32) / 255
        ed = cv2.dilate(ed, np.ones((2, 2), np.uint8)); ed = cv2.GaussianBlur(ed, (0, 0), 1.1)
        n = nz(181, (30, 16)); ed = ed * (0.65 + 0.5 * n)                                 # brush pressure varies along the lines
        wash = cv2.GaussianBlur(np.clip((0.22 - L) / 0.20, 0, 1), (0, 0), 3) * 0.12
        order = np.clip(0.62 * (_GY / H) + 0.38 * nz(182, (14, 8)), 0, 1)               # roughly top to bottom, in patches (stroke order)
        _PP["sk"] = (np.clip(ed * 1.6, 0, 1).astype(np.float32), wash.astype(np.float32), order.astype(np.float32))
    return _PP["sk"]

def sketch_fx(o, f):
    k = f / FPS / E.HB
    prog = sum(eout(clamp((k - kn) / 2.6, 0, 1), 2.0) for kn in (0, 3, 6, 9)) / 4      # four strokes of progress, one per synth note
    if prog <= 0.001: return o
    ed, wash, order = sketch_layer()
    shown = np.clip((prog * 1.08 - order) / 0.05, 0, 1)
    wet = np.exp(-((prog * 1.08 - order) / 0.04) ** 2) * (prog < 0.995)                 # the freshly laid ink is darker for a moment
    a = (ed * 0.80 + wash * 0.6) * shown + ed * wet * 0.25
    return np.clip(o * (1 - a[..., None]) + INK * a[..., None], 0, 1)

_ink_open1 = ink_open
def ink_open(f, s):
    return sketch_fx(_ink_open1(f, s), f)

# ---- ink motes: specks of ink and paper dust drifting in depth (soft when near, sharp when far)
_MO = {}
def motes_fx(out, f, s):
    amt = s.get("motes", 0.0)
    if amt <= 0: return out
    key = s["n"]
    if key not in _MO:
        rng = np.random.default_rng(sum(map(ord, key)))
        _MO[key] = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.2, 1.0), rng.uniform(-25, 25), rng.uniform(-45, -10), rng.random() < 0.7) for _ in range(46)]
    t = f / FPS; dk = np.zeros((H // 2, W // 2), np.float32); lt = np.zeros((H // 2, W // 2), np.float32)
    for x, y, d, vx, vy, ink in _MO[key]:
        X = (x + vx * t * (0.4 + d)) % W; Y = (y + vy * t * (0.4 + d)) % H; r = max(1, int((1.5 + 7 * d ** 2) / 2))
        cv2.circle(dk if ink else lt, (int(X / 2), int(Y / 2)), r, 0.35 + 0.5 * (1 - d) if ink else 0.5, -1, cv2.LINE_AA)
    dk = cv2.resize(cv2.GaussianBlur(dk, (0, 0), 1.6), (W, H))[..., None] * amt; lt = cv2.resize(cv2.GaussianBlur(lt, (0, 0), 2.2), (W, H))[..., None] * amt
    return np.clip(out * (1 - dk * 0.8) + INK * dk * 0.8 + PAPER * lt * 0.35 * (1 - lum(out)[..., None]), 0, 1)

# ---- page turn: the frame turns over like a page of his sketchbook; its back is the paper
def page_turn(A, B, j, f, sa, sb, pre=6, post=11):
    u = clamp((j + pre + 0.5) / (pre + post), 0, 1)
    d = np.array([-0.62, -0.785], np.float32); d /= np.linalg.norm(d)                    # from the bottom-right corner toward the top-left
    s_ = (_GX - W) * d[0] + (_GY - H) * d[1]; smax = float(W * -d[0] + H * -d[1])
    p = smax * 1.12 * ein(u, 1.35)
    unc = s_ < p                                                                         # uncovered: the next page
    flap = (s_ >= p) & (s_ < 2 * p)                                                      # the turned page, lying over the old one
    o = np.where(unc[..., None], B, A)
    mx = _GX - 2 * (s_ - p) * d[0]; my = _GY - 2 * (s_ - p) * d[1]                       # mirror across the fold: the page's back
    inb = flap & (mx >= 0) & (mx < W) & (my >= 0) & (my < H)
    back = cv2.remap(A, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    q = np.clip((s_ - p) / np.maximum(p, 1), 0, 1)
    shade = (0.78 + 0.22 * np.exp(-(q / 0.12) ** 2) - 0.18 * q)[..., None]              # bright at the fold, falling off toward the edge
    backc = (paper() * 1.02 + (1 - lum(back))[..., None] * INK * 0.06) * shade           # paper, the old picture faintly showing through
    o = np.where(inb[..., None], backc, o)
    sh1 = np.exp(-np.clip(p - s_, 0, None) / 40)[..., None] * unc[..., None] * 0.55      # the page's shadow on the next shot
    sh2 = np.exp(-np.clip(s_ - 2 * p, 0, None) / 30)[..., None] * (s_ >= 2 * p)[..., None] * 0.35 * (p > 4)
    o = o * (1 - sh1) * (1 - sh2)
    o = o + (np.exp(-((s_ - p) / 3) ** 2) * (p > 4) * (p < smax))[..., None] * PAPER * 0.35
    return np.clip(o, 0, 1)

TR2["page_turn"] = (page_turn, 6, 11)

# ---- the swash: a black dry-brush stroke is laid behind ALONE. as it lands
def swash_fx(out, f, s):
    p = s["swash"]; k = f / FPS / E.HB
    if k < p["k0"] - 0.2 or k > p["k1"] + 1.5: return out
    u = clamp((k - p["k0"]) / 1.6, 0, 1); fade = 1 - smooth((k - p["k1"]) / 1.5)
    x0, x1 = W * 0.08, W * 0.92; yc = p["y"]; hgt = 210
    front = x0 + (x1 - x0 + 120) * eout(u, 2.2)
    if "sw" not in _PP:
        rng = np.random.default_rng(191); n = H
        prof = np.convolve(rng.normal(0, 1, n), np.ones(9) / 9, "same"); gaps = np.convolve(rng.random(n), np.ones(5) / 5, "same")
        _PP["sw"] = (prof.astype(np.float32), gaps.astype(np.float32))
    prof, gaps = _PP["sw"]
    yi = np.clip(_GY.astype(np.int32), 0, H - 1)
    top, bot = yc - hgt / 2 + prof[yi] * 6, yc + hgt / 2 + prof[yi] * 6
    inside = ((_GY > top) & (_GY < bot)).astype(np.float32)
    taper = np.clip(np.minimum((_GY - (yc - hgt / 2 - 20)) / 70, ((yc + hgt / 2 + 20) - _GY) / 70), 0, 1)
    dry = np.clip(1 - np.clip((_GX - (x1 - 200)) / 200, 0, 1) * (gaps[yi] > 0.45) * 1.4, 0, 1)   # the tail breaks into dry bristles
    head = np.clip((front - _GX) / 30, 0, 1) * np.clip((_GX - x0 + 30) / 60, 0, 1)
    m = (inside * taper * dry * head * 0.92 * fade)[..., None]
    sw_col = PAPER * (0.93 + 0.07 * nz(192, (50, 28)))[..., None]                      # an ivory stroke: red letters on white paint
    return np.clip(out * (1 - m) + sw_col * m, 0, 1)

# ---- THE PASSENGER, rebuilt: a hard light comes on behind him; his shadow is thrown on the paper wall, smoke rises off it,
#      two embers open in its head on "DARK"; the camera pushes in with a slow dutch tilt; the shadow turns to the lens and lunges.
def passenger_fx(f, s):
    p = s["passenger"]; k = f / FPS / E.HB; t = f / FPS
    img, msk = render_shot(s, f, True, True)
    if k < p["k_rise"] - 0.6: return img
    u = clamp((k - p["k_rise"]) / (p["k_lunge"] - p["k_rise"]), 0, 1)
    v = clamp((k - p["k_lunge"]) / (s["k1"] - 0.6 - p["k_lunge"]), 0, 1)
    on = smooth((k - p["k_rise"] + 0.6) / 0.9)                                           # the light comes on just before "DARK"
    cut = (_GY < H * p.get("cut_y", 1.0)).astype(np.float32)
    body = msk * cut
    ys, xs = np.nonzero(body > 0.5)
    if len(xs) < 50: return img
    ax, ay = float(np.median(xs)), float(ys.max())
    # the lit wall: paper, brightest where the light hits (behind and right of him), falling off into the corners
    lx, ly = ax + 160, H * 0.42
    fall = np.exp(-(((_GX - lx) / 1100) ** 2 + ((_GY - ly) / 1300) ** 2))
    wall = paper() * (0.70 + 0.34 * fall[..., None])
    wash = (on * 0.94 * (1 - msk) * cut)[..., None]
    lit = img * (1 - wash) + wall * wash
    rim = cv2.GaussianBlur(msk, (0, 0), 6) - msk                                        # the light catches the edge of him
    lit = lit + np.clip(-rim * 3, 0, 1)[..., None] * PAPER * 0.25 * on
    # his shadow on the wall: thrown up and to the left, breathing on the bass, a beat behind him
    br = 0.025 * sum(math.exp(-max(0, k - kb) / 1.2) for kb in (112, 116) if k >= kb)
    sc = 1.03 + 0.09 * eout(u, 2.0) + br
    off = -(390 + 60 * eout(u, 2.0)); lift = 70 - 20 * eout(u, 2.0); shear = -0.08 * eout(u, 2.0)   # beside him on the wall, its head in frame
    sway = 10 * math.sin(t * 2.1)
    M = np.float32([[sc, shear * sc, ax - sc * ax - shear * sc * ay + off + sway], [0, sc, ay - sc * ay + lift]])
    sh = cv2.warpAffine(body, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    sh = np.clip((cv2.GaussianBlur(sh, (0, 0), 2.2) - 0.5 - 0.10 * (nz(201, (60, 34)) - 0.5)) * 7 + 0.5, 0, 1)   # a crisp, organic edge
    # smoke: ink rising off the top of the shadow, drifting with time
    n1 = np.roll(nz(202, (26, 14)), -int(150 * t) % H, 0); n2 = np.roll(nz(203, (60, 34)), -int(240 * t) % H, 0)
    zone = np.clip(np.roll(cv2.GaussianBlur(sh, (0, 0), 22), -int(70 + 50 * u), 0) - sh * 0.6, 0, 1)
    smoke = np.clip(zone * 2.4 * np.clip((n1 * 0.7 + n2 * 0.3 - 0.42) * 3.2, 0, 1), 0, 1) * 0.85
    # the lunge: the shadow turns to the lens and swallows the frame (zoom-blurred toward us)
    hy = float(np.nonzero(sh > 0.5)[0].min()) if (sh > 0.5).any() else H * 0.2
    hx = float(np.median(np.nonzero(sh > 0.5)[1])) if (sh > 0.5).any() else W * 0.3
    zz = 1 + 7.0 * ein(v, 2.3)
    sh0 = sh
    fs = face_scr(s, f)
    if fs is not None:                                                                  # the lunge is centred between its eyes
        ex0, ey0 = fs[0], fs[1] - fs[2] * 0.10
        hx = M[0, 0] * ex0 + M[0, 1] * ey0 + M[0, 2]; hy = M[1, 0] * ex0 + M[1, 1] * ey0 + M[1, 2]
    pv = eout(v, 1.4); dxs, dys = (W / 2 - hx) * pv, (H * 0.36 - hy) * pv                # it pans to the centre as it comes at us
    M2 = np.float32([[zz, 0, hx * (1 - zz) + dxs], [0, zz, hy * (1 - zz) + dys]])
    if v > 0:
        sh = cv2.warpAffine(sh, M2, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
        sh = radial_blur(np.dstack([sh] * 3), W / 2, H * 0.36, 1.0, 1.10, 4)[..., 0]
        smoke = cv2.warpAffine(smoke, M2, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    shadow = np.clip(np.maximum(sh, smoke), 0, 1)[..., None] * (0.30 + 0.70 * smooth(u * 2.5 + v))
    keep = msk[..., None] * (1 - smooth((v - 0.30) / 0.45))
    o = lit * (1 - shadow * (1 - keep) * 0.96) + INK * shadow * (1 - keep) * 0.96
    redge = np.exp(-((sh - 0.5) / 0.14) ** 2)[..., None] * smooth(u * 3) * (1 - v) * (1 - msk[..., None]) * 0.65
    redge = redge * (_GY < H * p.get("cut_y", 1.0) - 40)[..., None]                    # (not along the shadow's cut-off base)
    o = o * (1 - redge) + INKRED * redge
    # the embers: two red eyes open in the shadow's head on "DARK"
    if fs is not None and v < 0.97:                                                     # the embers open on "DARK", and rush at the lens in the lunge
        ex, ey, ew = fs[0], fs[1] - fs[2] * 0.10, fs[2]
        sx = M[0, 0] * ex + M[0, 1] * ey + M[0, 2]; sy = M[1, 0] * ex + M[1, 1] * ey + M[1, 2]
        sx, sy = M2[0, 0] * sx + M2[0, 2], M2[1, 1] * sy + M2[1, 2]; esc = sc * zz
        op = eout(clamp((k - p["k_rise"] - 0.1) / 1.2, 0, 1), 2.0) * (1 - smooth((v - 0.80) / 0.17)) * (0.88 + 0.12 * math.sin(t * 17))
        if op > 0.01:
            lay = np.zeros((H, W), np.float32); dx = ew * 0.22 * esc
            for sgn in (-1, 1):
                cv2.ellipse(lay, (int(sx + sgn * dx), int(sy)), (max(2, int(ew * 0.075 * esc)), max(1, int(ew * 0.035 * esc * min(1, op * 1.2)))), 8, 0, 360, 1.0, -1, cv2.LINE_AA)
            lay = cv2.GaussianBlur(lay, (0, 0), 1.2 + 4 * v)[..., None] * op * ((sh0[..., None] > 0.3) * (1 - msk[..., None]) if v <= 0 else (1 - keep))
            glow = cv2.GaussianBlur(lay[..., 0], (0, 0), 14)[..., None] * 2.2
            o = o * (1 - lay) + INKRED_H * lay + INKRED * glow * 0.9
    # the camera: a slow push-in with a dutch tilt, a kick on the lunge
    return np.clip(zoom_about(o, W / 2, H * 0.42, 1 + 0.06 * eout(u, 1.6) + 0.04 * ein(v, 2), -2.4 * eout(u, 1.6) * (1 - v)), 0, 1)

_base104_r2 = base104
def base104(s, f):
    out = _base104_r2(s, f)
    if s.get("motes"): out = motes_fx(out, f, s)
    if s.get("swash"): out = swash_fx(out, f, s)
    return out

# ============================================================================ v105 — DRACULA: SUNDOWN (overrides the sections above)
CRIMSON = np.array([0.06, 0.04, 0.78], np.float32)    # BGR
CRIMSON_H = np.array([0.30, 0.32, 1.00], np.float32)
SUNC = np.array([0.55, 0.85, 1.00], np.float32)       # BGR warm sun
DUSKC = np.array([0.42, 0.40, 0.98], np.float32)      # BGR orange-magenta dusk
MOONS = np.array([0.98, 0.90, 0.80], np.float32)      # BGR cold moonlight
DAWNW = np.array([0.90, 0.96, 1.00], np.float32)      # BGR the white of the dawn (the loop seam)

def kof(f): return f / FPS / E.HB

# ---------------------------------------------------------------------------- the upscale pass: Lanczos on the 720p crop + noise-gated luma detail
def render_shot(s, f, with_shake=True, want_mask=False):
    img, t, u = source_img(s, f)
    if s.get("fit"): return render_fit(s, f, img, u, with_shake)
    if want_mask: msk = seg_mask(s, t)
    cx, cy, ch = frame_geom(s, f, t, u)
    cw = ch * 9 / 16; sc = W / cw
    dx, dy, rot = shake(f) if with_shake else (0, 0, 0)
    m = 16
    x0 = int(max(0, cx - cw / 2 - m)); x1 = int(min(img.shape[1], cx + cw / 2 + m))
    y0 = int(max(0, cy - ch / 2 - m)); y1 = int(min(img.shape[0], cy + ch / 2 + m))
    roi = grade(img[y0:y1, x0:x1].astype(np.float32) / 255, s, f)
    th_ = math.radians(rot); co, si = math.cos(th_) / sc, math.sin(th_) / sc
    lx, ly = cx - x0, cy - y0
    M = np.float32([[co, -si, lx - co * (W / 2 + dx) + si * (H / 2 + dy)], [si, co, ly - si * (W / 2 + dx) - co * (H / 2 + dy)]])
    out = cv2.warpAffine(roi, M, (W, H), flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)
    L = lum(out); d = L - cv2.GaussianBlur(L, (0, 0), 1.6)
    gate = np.clip((np.abs(d) - 0.006) / 0.02, 0, 1)                                    # recover edges, leave the noise alone
    out = out + (d * gate * 0.55)[..., None]
    if want_mask:
        mr = cv2.resize(msk, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)[y0:y1, x0:x1]
        mw = cv2.warpAffine(mr, M, (W, H), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
        return np.clip(out, 0, 1), np.clip(mw, 0, 1)
    return np.clip(out, 0, 1)

# ---------------------------------------------------------------------------- the grades: DAY postcard, DUSK, NIGHT crimson
def day_grade(x):
    L = lum(x)[..., None]
    x = L + (x - L) * 1.08
    x = x * np.array([0.90, 1.0, 1.07], np.float32)                                     # warm
    x = 0.045 + x * 0.93                                                                # bleached, lifted
    x = x + (1 - L) ** 3 * np.array([0.035, 0.030, -0.005], np.float32)                 # a little teal in the shadows
    return np.clip(x, 0, 1)

def night_grade(x, s):
    B_, G_, R_ = x[..., 0], x[..., 1], x[..., 2]
    red = np.clip((R_ - np.maximum(G_, B_) - s.get("redthr", 0.20)) * 4.0, 0, 1)[..., None]
    L = np.clip(lum(x), 0, 1); Lc = L * 0.55 + (L * L * (3 - 2 * L)) * 0.45
    cool = (0.016 + Lc * 0.97)[..., None] * np.array([1.08, 1.0, 0.90], np.float32)    # cold moonlit silver
    cool = cool + (1 - Lc[..., None]) ** 4 * CRIMSON * 0.05                              # a crimson breath in the deepest shadows
    rc = np.clip(Lc[..., None] + (x - L[..., None]) * 1.45, 0, 1) * np.array([0.75, 0.75, 1.05], np.float32)
    return np.clip(cool * (1 - red) + rc * red, 0, 1)

def dusk_u(s, f):
    k = kof(f)
    if s.get("daybreak"): return 1 - smooth((k - E.DAWN_K[0]) / (E.DAWN_K[1] - E.DAWN_K[0] - 1.0))   # night -> day
    return smooth((k - E.SUN_K[0]) / (E.SUN_K[1] - E.SUN_K[0]))                                         # day -> night

def grade(img, s, f):
    g, gains = correction(s)
    x = np.clip(img * gains, 0, 1) ** g
    if s.get("ev"): x = np.clip(x * 2 ** s["ev"], 0, 1)                                 # per-shot exposure (dark night sources)
    look = s.get("look", "night")
    if look == "day": o = day_grade(x)
    elif look == "night": o = night_grade(x, s)
    else:
        u = dusk_u(s, f); d = day_grade(x); n = night_grade(x, s)
        mid = math.sin(math.pi * u) ** 1.2
        o = d * (1 - u) + n * u
        L = lum(o)[..., None]
        o = np.clip(o * (1 - 0.55 * mid) + L * DUSKC * 1.25 * 0.55 * mid, 0, 1)                    # golden hour -> blood orange -> night
    if s.get("con"): o = o + (o * o * (3 - 2 * o) - o) * s["con"]                       # per-shot contrast (hazy sources)
    return np.clip(o, 0, 1)

# ---------------------------------------------------------------------------- the sun, with light rays and lens ghosts
def sun_fx(out, f, sx, sy, amt=1.0, col=SUNC, r=70.0, m=None):
    """the sun with light rays and lens ghosts. With his matte m, the sun and its rays sit BEHIND him: the disc is hidden where
    he covers it, the rays stream out of the sky around his edges, and the light wraps a warm rim onto the side of him nearest it."""
    if amt <= 0.01: return out
    L = lum(out); bright = np.clip((L - 0.62) / 0.38, 0, 1) ** 2
    sm = cv2.resize(bright, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    gy, gx = qgrid(4)
    d2 = (gx - sx / 4) ** 2 + (gy - sy / 4) ** 2
    disc = np.exp(-(d2 / (r / 4) ** 2))
    if m is not None:
        mq = cv2.resize(m, (W // 4, H // 4), interpolation=cv2.INTER_AREA); bg = 1 - mq
        vis = float((disc * bg).sum() / (disc.sum() + 1e-6))
        src = np.clip(sm * 0.6 * bg + disc * bg, 0, 1)
    else:
        mq = None; bg = 1.0; vis = 1.0; src = np.clip(sm * 0.6 + disc, 0, 1)
    acc = np.zeros_like(src)
    for i in range(10):                                                                  # rays: the bright sky streaked away from the sun
        sc = 1.0 + 0.045 * i; M = np.float32([[sc, 0, sx / 4 * (1 - sc)], [0, sc, sy / 4 * (1 - sc)]])
        acc += cv2.warpAffine(src, M, (W // 4, H // 4), flags=cv2.INTER_LINEAR) * (1 - i / 11)
    rays = cv2.resize(cv2.GaussianBlur(acc / 6.0, (0, 0), 1.5), (W, H))[..., None]
    glow = cv2.resize(cv2.GaussianBlur(disc * bg, (0, 0), 6), (W, H))[..., None]
    add = rays * col * 0.42 * amt + glow * col * 0.9 * amt
    if mq is not None:
        front = 1 - 0.78 * m[..., None]                                                  # a little of it scatters over him, most stays behind
        halo = np.exp(-(d2 / (r * 3.2 / 4) ** 2))
        wrap = cv2.GaussianBlur(bg * halo, (0, 0), 3.0) * mq                              # light wrap: the sun bleeds round his edge
        o = out + add * front + cv2.resize(wrap, (W, H))[..., None] * col * 1.1 * amt
    else:
        o = out + add
    ax, ay = W / 2 - sx, H / 2 - sy                                                      # lens ghosts along the axis through the centre
    for i, (pos, rr, a) in enumerate(((0.6, 46, 0.07), (1.15, 90, 0.05), (1.55, 34, 0.08), (1.9, 140, 0.035))):
        o = add_glow(o, W / 2 + ax * pos, H / 2 + ay * pos, rr, a * amt * vis, col * np.array([1.0, 0.85, 0.7], np.float32))
    return np.clip(o, 0, 1)

def sun_pos(s, f):
    """the sun of a day shot (frame 0's flares up as the loop lands in it), the setting sun at dusk, the rising sun at daybreak."""
    k = kof(f)
    if s.get("daybreak"):
        u = clamp((k - E.DAWN_K[0]) / 1.6, 0, 1); g = smooth((k - 85.0) / 2.3)
        return W * SUN_T[0], H * (SUN_T[1] + 0.17 * (1 - eout(u, 1.6))), 0.7 + 1.0 * g, 80 + 60 * g
    if s.get("look") == "dusk":
        u = clamp((k - E.SUN_K[0]) / (E.SUN_K[1] - E.SUN_K[0]), 0, 1)
        return W * (0.86 + 0.04 * u), H * (0.12 + 1.05 * ein(u, 1.7)), 1.0 - 0.6 * smooth((u - 0.75) / 0.25), 70 + 90 * u   # it sets down the right edge, off his face
    if s.get("sun"):
        b = math.exp(-f / 16.0) if s is E.SHOTS[0] else 0.0                             # the sun of frame 0 still blazing from the embers
        return W * s["sun"][0], H * s["sun"][1], 1.0 + 0.9 * b, 70 + 70 * b
    return None

# ---------------------------------------------------------------------------- bats: procedural silhouettes with flapping wings
_BAT = {}
def bat_sprite(phase, size=60, tone=0):
    """a flapping bat silhouette. tone 0: black with a cold moonlit top edge; 1: black, backlit crimson; 2: crimson (the letters'
    bats); 3: the great bat (fine crimson edge, wing bones in the membrane)."""
    q = int(round(math.log(max(4.0, size)) / math.log(1.10))); S_ = int(1.10 ** q)
    key = (int(phase * 8) % 8, S_, tone)
    if key in _BAT: return _BAT[key]
    w, h = S_ * 2 + 8, int(S_ * 1.2) + 8; m = np.zeros((h, w), np.float32); cx, cy = w / 2, h * 0.45
    bones = np.zeros_like(m)
    fl = math.sin(key[0] / 8 * 2 * math.pi)                                             # wing angle
    for sg in (-1, 1):
        tip = (cx + sg * S_ * 0.98, cy - S_ * 0.45 * fl - S_ * 0.05)
        elbow = (cx + sg * S_ * 0.45, cy - S_ * 0.30 * fl - S_ * 0.12)
        pts = [(cx + sg * 4, cy - S_ * 0.08), elbow, tip]; edge = []
        for i in range(4):                                                               # the scalloped trailing edge
            a = 1 - (i + 0.5) / 4; bx = cx + sg * S_ * 0.98 * a; by = cy + S_ * (0.10 + 0.18 * (i % 2)) - S_ * 0.35 * fl * a
            pts.append((bx, by)); edge.append((bx, by))
        pts.append((cx + sg * 4, cy + S_ * 0.12))
        cv2.fillPoly(m, [np.array(pts, np.int32)], 1.0, cv2.LINE_AA)
        if tone == 3:
            th_ = max(1, S_ // 70)
            cv2.line(bones, (int(cx + sg * 4), int(cy - S_ * 0.08)), (int(elbow[0]), int(elbow[1])), 1.0, th_ * 2, cv2.LINE_AA)
            for p in [tip] + edge[::2]: cv2.line(bones, (int(elbow[0]), int(elbow[1])), (int(p[0]), int(p[1])), 1.0, th_, cv2.LINE_AA)
    cv2.ellipse(m, (int(cx), int(cy)), (max(2, S_ // 9), max(3, S_ // 5)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)    # body
    cv2.circle(m, (int(cx), int(cy - S_ * 0.2)), max(2, S_ // 10), 1.0, -1, cv2.LINE_AA)                         # head
    for sg in (-1, 1): cv2.fillConvexPoly(m, np.array([(cx + sg * S_ * 0.03, cy - S_ * 0.26), (cx + sg * S_ * 0.09, cy - S_ * 0.40), (cx + sg * S_ * 0.10, cy - S_ * 0.22)], np.int32), 1.0, cv2.LINE_AA)
    m = cv2.GaussianBlur(m, (0, 0), 0.7)
    sh = max(1, S_ // (130 if tone == 3 else 18)); top = np.clip(m - np.roll(m, sh, 0), 0, 1)[..., None]   # the edge that faces the light above
    body, rim = {0: (np.array([0.030, 0.025, 0.030], np.float32), MOONS * 0.55), 1: (np.array([0.020, 0.012, 0.030], np.float32), CRIMSON_H * 0.85),
                 2: (CRIMSON * 0.40, CRIMSON_H), 3: (np.array([0.014, 0.010, 0.020], np.float32), CRIMSON_H * 0.25)}[tone]
    rgb = body + top * (rim - body)
    if tone == 3:                                                                        # the wing bones catch a little light through the membrane
        b_ = cv2.GaussianBlur(bones, (0, 0), 1.0)[..., None] * m[..., None]
        rgb = rgb + b_ * np.array([0.03, 0.03, 0.09], np.float32)
    _BAT[key] = np.dstack([rgb, m]).astype(np.float32); return _BAT[key]

def bats_layer(bats, t, tone=0):
    """bats = [(x, y, size, phase0, flap_hz, blur)], painted in the order given (far first); returns an RGBA layer."""
    lay = np.zeros((H, W, 4), np.float32)
    for x, y, sz, ph, hz, bl in bats:
        if x < -sz * 2 or x > W + sz * 2 or y < -sz * 2 or y > H + sz * 2 or sz < 4: continue
        spr = bat_sprite((ph + t * hz) % 1.0, min(260, sz), tone); s0 = spr.shape[1] / 2 - 4
        draw_sprite(lay, spr, x, y, sz / s0 if sz > 260 else 1.0, 0, 1.0, bl, 1.0)
    return lay

def bat_burst(A, B, j, f, sa, sb, pre=8, post=24):
    """THE DROP: night falls at once. A cloud of bats pours out of the dark sky toward the lens, blacks out the frame against a
    crimson flash and flies past the camera (near ones soft, far ones sharp) to reveal him."""
    tj = j / FPS; rng = np.random.default_rng(321); bats = []
    for i in range(460):
        X, Y = rng.normal(0, 0.55), rng.normal(-0.10, 0.70); ta = rng.uniform(-0.03, 0.27); ph, hz = rng.random(), rng.uniform(6, 10)
        z = 0.16 + 14.0 * (ta - tj)                                                      # depth: each bat passes the lens at its own time ta
        if z <= 0.16 or z > 6.0 or 62 / z < 11: continue
        q = clamp((z - 0.6) / 4.0, 0, 1)                                                 # far bats pour out of the sky above him, near ones fill the frame
        vx, vy = W * (0.50 + 0.06 * q), H * (0.46 - 0.34 * q)
        bats.append((z, vx + X * 700 / z, vy + Y * 700 / z, 62 / z, ph, hz, min(16.0, max(0.0, 2.0 / z - 0.9))))
    bats.sort(key=lambda b: -b[0])
    lay = bats_layer([b[1:] for b in bats], f / FPS, 1)
    if j < 0:
        u = (j + pre + 1) / (pre + 1); base = A * (1 - 0.55 * u) + CRIMSON * 0.18 * u
    else:
        fl = math.exp(-j / 9.0); base = B * (1 - 0.6 * fl) + CRIMSON * 0.85 * fl + CRIMSON_H * 0.30 * math.exp(-j / 2.5)
    return np.clip(base * (1 - lay[..., 3:4]) + lay[..., :3] * lay[..., 3:4], 0, 1)

def bat_swarm(A, B, j, f, sa, sb, pre=8, post=12):
    """a river of bats crosses the frame in depth (near ones big, fast and soft; far ones small and sharp); the next shot is behind it."""
    u = clamp((j + pre + 0.5) / (pre + post), 0, 1); t = f / FPS
    P = -1.6 + 4.5 * eout(u, 1.25)                                                       # where the column is (world units, 0 = centre)
    rng = np.random.default_rng(654); bats = []
    for i in range(150):
        z = rng.uniform(0.5, 2.2); off = rng.uniform(0, 1.0); yw = rng.normal(-0.05, 0.55); ph, hz = rng.random(), rng.uniform(6, 10)
        x = W / 2 + (P - off) * 900 / z; y = H * 0.45 + yw * 900 / z + 26 * math.sin(t * 7 + i)
        bats.append((z, x, y, 72 / z, ph, hz, min(10.0, max(0.0, 1.5 / z - 1.2)) + 0.3))
    bats.sort(key=lambda b: -b[0])
    lay = bats_layer([b[1:] for b in bats], t, 0)
    m = np.clip((W / 2 + (P - 0.5) * 900 - _GX) / 260, 0, 1)[..., None]                 # the cut rides the middle of the column
    o = A * (1 - m) + B * m
    xc = W / 2 + (P - 0.5) * 900; haze = np.exp(-((_GX - xc) / 420) ** 2)[..., None] * math.sin(math.pi * u)   # moonlight behind the column, so they read as silhouettes
    o = o * (1 - 0.25 * haze) + MOONS * 0.42 * haze
    return np.clip(o * (1 - lay[..., 3:4]) + lay[..., :3] * lay[..., 3:4], 0, 1)

# ---------------------------------------------------------------------------- THE BLOOD MOON
_MN = {}
def moon_tex():
    """a procedural blood moon: maria, craters with lit rims, limb darkening and the brighter edge of the Earth's shadow."""
    if "t" in _MN: return _MN["t"]
    S = 512; yy, xx = np.mgrid[0:S, 0:S].astype(np.float32); c = S / 2; R = S / 2 - 6
    nx, ny = (xx - c) / R, (yy - c) / R; r2 = nx ** 2 + ny ** 2
    a = np.clip((1 - np.sqrt(r2)) * R / 2.0, 0, 1); nzz = np.sqrt(np.clip(1 - r2, 0, 1))
    def fbm(cells, seed): return cv2.resize(np.random.default_rng(seed).random((cells, cells)).astype(np.float32), (S, S), interpolation=cv2.INTER_CUBIC)
    mar = fbm(4, 11) * 0.55 + fbm(8, 12) * 0.30 + fbm(16, 13) * 0.15
    alb = 0.80 - 0.34 * np.clip((mar - 0.50) * 3.5, 0, 1) + (fbm(48, 14) - 0.5) * 0.10 + (fbm(120, 15) - 0.5) * 0.06
    rng = np.random.default_rng(16)
    for i in range(70):                                                                  # craters: dark floor, lit upper-right rim, shadowed lower-left rim
        cx_, cy_ = rng.uniform(40, S - 40, 2); rr = rng.uniform(3, 9) * (1 + 3 * rng.random() ** 4)
        x0, x1, y0, y1 = int(max(0, cx_ - rr * 1.6)), int(min(S, cx_ + rr * 1.6)), int(max(0, cy_ - rr * 1.6)), int(min(S, cy_ + rr * 1.6))
        dx, dy = xx[y0:y1, x0:x1] - cx_, yy[y0:y1, x0:x1] - cy_; d = np.sqrt(dx ** 2 + dy ** 2) / rr
        side = (dx - dy) / (np.sqrt(dx ** 2 + dy ** 2) + 1e-3) * 0.707
        alb[y0:y1, x0:x1] += -0.07 * np.clip(1 - d, 0, 1) ** 0.5 + 0.10 * np.exp(-((d - 1.0) / 0.18) ** 2) * side
    for i in range(3):                                                                   # a few rays from a young crater
        ang = rng.uniform(0, 2 * math.pi); L_ = np.zeros((S, S), np.float32)
        cv2.line(L_, (330, 150), (int(330 + 260 * math.cos(ang)), int(150 + 260 * math.sin(ang))), 1.0, 3, cv2.LINE_AA)
        alb += cv2.GaussianBlur(L_, (0, 0), 3) * 0.05
    shade = (0.50 + 0.50 * nzz ** 0.55) * (0.62 + 0.38 * smooth_arr((nx - ny) * 0.55 + 0.45))
    tone = np.clip(alb * shade, 0, 1.2)[..., None]
    dark, mid, hi = np.array([0.02, 0.03, 0.22], np.float32), np.array([0.05, 0.12, 0.66], np.float32), np.array([0.30, 0.52, 1.00], np.float32)
    col = np.where(tone < 0.5, dark + (mid - dark) * (tone / 0.5), mid + (hi - mid) * np.clip((tone - 0.5) / 0.5, 0, 1))
    _MN["t"] = np.dstack([np.clip(col, 0, 1), a]).astype(np.float32); return _MN["t"]

def bloodmoon_fx(f, s):
    p = s["bloodmoon"]; k = kof(f); t = f / FPS
    img, msk = render_shot(s, f, True, True)
    u = eout(clamp((k - p["k0"]) / 2.2, 0, 1), 2.0)
    sky = np.zeros((H, W, 3), np.float32) + np.array([0.06, 0.025, 0.02], np.float32)
    sky = sky + (_GY / H)[..., None] * np.array([0.02, 0.01, 0.06], np.float32)
    R = 430; mx, my = W * 0.5, H * (1.15 - 0.85 * u) - 40 * smooth((k - p["k0"] - 2.2) / 4)
    lay = np.zeros((H, W, 4), np.float32); draw_sprite(lay, moon_tex(), mx, my, R * 2 / 512, 0, 1.0, 0.0, 1.0)
    pulse = 1 + 0.35 * math.exp(-max(0, k - 48.5) / 1.2) * (k >= 48.5)
    glow = cv2.GaussianBlur(lay[..., 3], (0, 0), 60)[..., None] * CRIMSON * 0.8 * pulse
    sky = sky * (1 - lay[..., 3:4]) + lay[..., :3] * lay[..., 3:4] * pulse + glow
    n = np.roll(nz(401, (20, 10)), int(30 * t), 1); cloud = np.clip((n - 0.55) * 2.5, 0, 1)[..., None] * 0.35
    sky = sky * (1 - cloud) + np.array([0.05, 0.03, 0.10], np.float32) * cloud
    rng = np.random.default_rng(402); bats = []
    for i in range(7):
        bx = (rng.uniform(-200, W) + 260 * t * rng.uniform(0.6, 1.2)) % (W + 400) - 200; by = my + rng.uniform(-R, R * 0.6)
        bats.append((bx, by, rng.uniform(22, 44), rng.random(), rng.uniform(6, 9), 0.4))
    bl = bats_layer(bats, t); sky = sky * (1 - bl[..., 3:4]) + bl[..., :3] * bl[..., 3:4]
    a = smooth((k - p["k0"]) / 0.8) * (1 - smooth((k - p["k1"] + 0.6) / 0.6))
    out = img * msk[..., None] + (img * (1 - a) + sky * a) * (1 - msk[..., None])
    rim = np.clip(cv2.GaussianBlur(msk, (0, 0), 5) - msk, 0, 1)[..., None] * a * 2.5     # the moon lights his edge
    return np.clip(out + rim * CRIMSON_H * 0.6, 0, 1)

def moon_iris(A, B, j, f, sa, sb, pre=6, post=12):
    rr = np.sqrt((_GX - W / 2) ** 2 + (_GY - H * 0.42) ** 2)
    if j < 0:
        u = (j + pre + 1) / (pre + 1); vg = np.clip((rr - 900 * (1 - 0.5 * u)) / 500, 0, 1)[..., None]
        return np.clip(A * (1 - vg * 0.9 * u) + CRIMSON * 0.15 * vg * u, 0, 1)
    v = (j + 1) / post; R = 1400 * eout(v, 2.2) + 10
    m = np.clip((R - rr) / 6, 0, 1)[..., None]; rim = np.exp(-((rr - R) / (10 + 30 * v)) ** 2)[..., None]
    return np.clip(B * m + A * 0.2 * (1 - m) + rim * CRIMSON_H * (1 - v) * 1.2, 0, 1)

# ---------------------------------------------------------------------------- THE COFFIN: a lid slams shut over him and opens on the next
_CF = {}
def coffin_lid():
    """a lacquered mahogany coffin lid, lit from a height map: a bevelled edge, a raised inner panel and a brass cross."""
    if "l" in _CF: return _CF["l"]
    w, h = int(W * 1.25), int(H * 1.12)
    pts = np.array([(w * 0.30, 0), (w * 0.70, 0), (w * 0.98, h * 0.26), (w * 0.82, h), (w * 0.18, h), (w * 0.02, h * 0.26)], np.float32)
    def poly_dist(p):
        mm = np.zeros((h, w), np.uint8); cv2.fillPoly(mm, [p.astype(np.int32)], 1, cv2.LINE_8)
        return cv2.distanceTransform(mm, cv2.DIST_L2, 5).astype(np.float32), mm
    d_out, m8 = poly_dist(pts)
    ctr = np.array([w / 2, h * 0.47], np.float32); inner = (pts - ctr) * 0.80 + ctr
    d_in, _ = poly_dist(inner)
    hgt = smooth_arr(d_out / 46) * 1.0 + smooth_arr(d_in / 30) * 0.55 - 0.35 * np.exp(-((d_in + 14) / 6) ** 2) * (d_out > 30)
    cr = np.zeros((h, w), np.float32); cxx, cyy, aw, al = int(w / 2), int(h * 0.36), int(w * 0.034), int(h * 0.15)   # the brass cross
    cv2.rectangle(cr, (cxx - aw, cyy - al), (cxx + aw, cyy + int(al * 1.35)), 1.0, -1); cv2.rectangle(cr, (cxx - int(al * 0.62), cyy - int(al * 0.55) - aw), (cxx + int(al * 0.62), cyy - int(al * 0.55) + aw), 1.0, -1)
    crd = cv2.distanceTransform((cr > 0.5).astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32)
    hgt = hgt + smooth_arr(crd / 10) * 0.35
    hs = cv2.GaussianBlur(hgt, (0, 0), 1.5) * 60
    gx = cv2.Sobel(hs, cv2.CV_32F, 1, 0, ksize=3) / 8; gy = cv2.Sobel(hs, cv2.CV_32F, 0, 1, ksize=3) / 8
    nrm = np.dstack([-gx, -gy, np.ones_like(gx)]); nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
    Lv = np.array([-0.45, -0.65, 0.62], np.float32); Lv /= np.linalg.norm(Lv)
    dif = np.clip(nrm @ Lv, 0, 1); Hv = Lv + np.array([0, 0, 1], np.float32); Hv /= np.linalg.norm(Hv)
    spec = np.clip(nrm @ Hv, 0, 1) ** 40
    rng = np.random.default_rng(501)
    warp = cv2.resize(rng.random((12, 6)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    rings = 0.5 + 0.5 * np.sin(np.arange(w, dtype=np.float32)[None, :] * 0.045 + warp * 3.0 + cv2.resize(rng.random((60, 30)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC) * 0.8)
    streak = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), sigmaX=1.2, sigmaY=30)
    wood = (0.70 + 0.12 * rings + 0.45 * (streak - 0.5))[..., None] * np.array([0.045, 0.075, 0.20], np.float32)   # dark lacquered mahogany
    brass = np.array([0.20, 0.52, 0.80], np.float32)
    isb = smooth_arr(crd / 2)[..., None]
    alb = wood * (1 - isb) + brass * 0.55 * isb
    coat = np.exp(-((np.arange(w, dtype=np.float32)[None, :] - w * 0.36 - (np.arange(h, dtype=np.float32)[:, None] - h * 0.5) * 0.25) / (w * 0.05)) ** 2)[..., None] * 0.07
    col = alb * (0.35 + 1.25 * dif[..., None]) + spec[..., None] * (0.55 + 0.6 * isb) * np.array([0.80, 0.88, 1.0], np.float32) + coat * (1 - isb)
    a = cv2.GaussianBlur(m8.astype(np.float32), (0, 0), 1.0)
    _CF["l"] = np.dstack([np.clip(col, 0, 1), a]).astype(np.float32); return _CF["l"]

def coffin_tr(A, B, j, f, sa, sb, pre=8, post=12):
    """the lid falls toward the lens and slams shut over him (the frame jolts, dust kicks up), then lifts away on the next shot."""
    lid = coffin_lid()
    if j < 0:
        u = (j + pre + 1) / (pre + 1); e = ein(u, 2.6); sc = 1.35 - 0.35 * e; y = H / 2 - H * 0.95 * (1 - e); base = A; darken = 0.55 * u
    else:
        v = (j + 1) / post; e = ein(clamp((v - 0.20) / 0.80, 0, 1), 2.0); sc = 1.0 + 0.25 * e; y = H / 2 + H * 1.15 * e; base = B; darken = 0.85 * (1 - v)
    jolt = 26 * math.exp(-max(0, j) / 2.0) * math.cos(max(0, j) * 2.4) if j >= 0 else 0.0
    lay = np.zeros((H, W, 4), np.float32); draw_sprite(lay, lid, W / 2, y + jolt, sc, 0, 1.0, 1.6 if j < -2 else 0.0, 1.0)
    sh = cv2.GaussianBlur(lay[..., 3], (0, 0), 40)[..., None] * 0.75
    o = base * (1 - darken) * (1 - sh)
    o = o * (1 - lay[..., 3:4]) + lay[..., :3] * lay[..., 3:4]
    if 0 <= j < 10:                                                                      # dust kicked up along the seam
        rng = np.random.default_rng(77); dl = np.zeros((H, W), np.float32); tt = (j + 1) / FPS
        for i in range(90):
            x0 = rng.uniform(0, W); y0 = rng.choice([rng.uniform(0, 60), rng.uniform(H - 60, H), rng.uniform(0, H)]); vx, vy = rng.normal(0, 260), rng.normal(-120, 160)
            cv2.circle(dl, (int(x0 + vx * tt), int(y0 + vy * tt)), int(rng.uniform(1, 3.5)), float(rng.uniform(0.3, 1.0)), -1, cv2.LINE_AA)
        dl = cv2.GaussianBlur(dl, (0, 0), 1.2)[..., None] * (1 - j / 10) * 0.7
        o = o + dl * MOONS * 0.6
    if 0 <= j < 2: o = o + 0.08 * (1 - j / 2)                                             # the slam
    return np.clip(o, 0, 1)

# ---------------------------------------------------------------------------- the sun flare sweep (a lens flare crosses the frame and whites it out for a moment)
def sun_flare_tr(A, B, j, f, sa, sb, pre=6, post=9):
    """a lens flare crosses the frame along the sun's height and whites it out for a moment."""
    u = clamp((j + pre + 0.5) / (pre + post), 0, 1); x = -200 + (W + 400) * eout(u, 1.4)
    sp = sun_pos(sb, sb["f0"]) or sun_pos(sa, sa["f1"] - 1); y = clamp(sp[1], H * 0.08, H * 0.92) if sp else H * 0.10
    base = A if j < 0 else B
    streak = np.exp(-((_GY - y) / (8 + 40 * math.sin(math.pi * u))) ** 2) * np.exp(-((_GX - x) / 900) ** 2)
    wash = math.sin(math.pi * u) ** 3 * 0.85
    o = base * (1 - wash) + DAWNW * wash + streak[..., None] * SUNC * 0.7
    for pos, rr, a in ((0.4, 60, 0.15), (0.75, 120, 0.08), (1.3, 40, 0.18)):
        o = add_glow(o, x + (W / 2 - x) * pos * 2, y + (H / 2 - y) * pos * 2, rr, a * math.sin(math.pi * u), SUNC)
    return np.clip(o, 0, 1)

TR2.update({"bat_burst": (bat_burst, 6, 24), "bat_swarm": (bat_swarm, 8, 12), "moon_iris": (moon_iris, 6, 12), "coffin": (coffin_tr, 8, 12),
            "sun_flare": (sun_flare_tr, 6, 9)})

# ---------------------------------------------------------------------------- fog, the opening white, daybreak
def fog_fx(out, f, amt):
    t = f / FPS; n = np.roll(nz(411, (14, 8)), int(40 * t) % W, 1) * 0.6 + np.roll(nz(412, (30, 16)), -int(25 * t) % W, 1) * 0.4
    m = np.clip((n - 0.40) * 1.8, 0, 1) * np.clip((_GY / H - 0.45) / 0.5, 0, 1) * amt * 0.45
    return np.clip(out * (1 - m[..., None]) + MOONS * 0.32 * m[..., None], 0, 1)

def dawn_white(out, f):
    """the white of the dawn with the sun low on the right."""
    o = np.broadcast_to(DAWNW, (H, W, 3)).copy()
    return sun_fx(o, f, W * SUN_DAWN[0], H * SUN_DAWN[1], 0.8, SUNC, 150)

def daybreak_fx(out, f, s, m=None):
    """DAYBREAK -> ASHES TO SUN: the sun comes up behind him, his edge catches fire (rim and embers), he burns away into embers
    that spiral into the sun, and the frame floods with light (the iris into frame 0 is in seam_out)."""
    k = kof(f); u = clamp((k - E.DAWN_K[0]) / (E.DAWN_K[1] - E.DAWN_K[0]), 0, 1)
    out = burn_fx(out, f, s, m, smooth((k - ASH["heat"]) / 1.0) * (1 - smooth((k - 86.4) / 0.8)))
    rise = np.clip(((_GY / H) - (1.05 - 0.9 * eout(u, 1.5))) / 0.35, 0, 1)[..., None]   # the light comes up from the horizon
    out = out * (1 - rise * 0.35 * u) + DAWNW * rise * 0.35 * u
    return np.clip(ashes_fx(out, f, s, m), 0, 1.6)

def opening_white(out, f):
    k = kof(f); w = SEAM_W * (1 - smooth(k / 1.8))                                       # the loop opens half in the same white, which burns off the boat
    if w <= 0.001: return out
    return np.clip(out * (1 - w) + dawn_white(out, f) * w, 0, 1)

# ---------------------------------------------------------------------------- DRACULA: the hero title whose letters burst into bats
def smooth_arr(u): u = np.clip(u, 0, 1); return u * u * (3 - 2 * u)

SUN_DAWN = (0.84, 0.22)                                                                  # the rising sun comes up behind his shoulder, off his face

SEAM_W = 0.0                                                                             # frame 0 is the clean boat shot now (the loop lands in its sun)

_F0 = {}

def seam_out(out, f):
    """the loop: when the last embers reach the sun it flares and its light bursts out over the whole frame (radial rays);
    under the flash the picture becomes frame 0 (the boat), and the light collapses back into the sun, which is frame 0's sun."""
    k = kof(f)
    if k < ASH["flash0"]: return out
    if "f0" not in _F0: _F0["f0"] = base105(E.SHOTS[0], 0)
    sx, sy = W * SUN_T[0], H * SUN_T[1]; t = f / FPS
    if k < ASH["flash1"]:
        v = clamp((k - ASH["flash0"]) / (ASH["flash1"] - ASH["flash0"]), 0, 1); base = np.clip(out, 0, 1); rad = 70 + 2600 * eout(v, 2.4)
    else:
        v = clamp((k - ASH["flash1"]) / (E.DAWN_K[1] - ASH["flash1"]), 0, 1); base = _F0["f0"]; rad = 100 + 2570 * (1 - ein(v, 2.4))
    rr = np.sqrt((_GX - sx) ** 2 + (_GY - sy) ** 2)
    L = smooth_arr(1 - (rr - rad * 0.45) / (rad * 0.55 + 1))[..., None]
    ang = np.arctan2(_GY - sy, _GX - sx)
    rays = ((0.5 + 0.5 * np.sin(ang * 23 + t * 1.5) * np.sin(ang * 9 - t)) ** 5)[..., None] * smooth_arr(1 - (rr - rad) / (rad * 0.8 + 1))[..., None]
    o = 1 - (1 - base) * (1 - LIGHT_G * 0.95 * L)                                         # screen the sunlight over the picture
    o = o + rays * SUNC * 0.30 * (1 - L)
    if k < ASH["flash1"]:                                                                # the shock ring of the flare as it bursts out
        ring = np.exp(-((rr - rad * 0.92) / (20 + rad * 0.06)) ** 2)[..., None]
        o = o + ring * (SUNC * 0.55 + WHITE * 0.25) * (1 - v)
    return np.clip(o, 0, 1)

def render(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin"); logo = False
    out = base105(s, f)
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge105(P, "last"), out, k, f, P, s); logo = logo or tin == "logo_orig"
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge105(n_, "first"), kn, f, s, n_); logo = logo or nt == "logo_orig"
    if s is E.SHOTS[0]: out = opening_white(out, f)
    if s is E.SHOTS[-1]: out = seam_out(out, f)
    out = beat_fx(out, f)
    out = text103(out, f)
    out = finish105(out, f, s.get("look", "night") == "night", logo)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)

_QG = {}

def qgrid(q=4):
    if q not in _QG: _QG[q] = np.mgrid[0:H // q, 0:W // q].astype(np.float32)
    return _QG[q]

def day_motes(out, f, s, m=None, sp=None):
    """sunlit dust: motes drifting in the warm air, brighter near the sun; far ones fine and sharp, near ones soft discs.
    With his matte they stay in the air behind and around him."""
    a = s.get("motes", 0.0)
    if not a: return out
    t = f / FPS; rng = np.random.default_rng(700 + int(s["k0"]))
    far = np.zeros((H // 2, W // 2), np.float32); near = np.zeros_like(far)
    for i in range(54):
        x0, y0, z = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.25, 1.0)
        vx, vy, w_, ph = rng.normal(10, 16), rng.uniform(-30, -8), rng.uniform(0.6, 1.5), rng.uniform(0, 6.3)
        x = (x0 + vx * t / z + 22 * math.sin(t * w_ + ph)) % W; y = (y0 + vy * t / z) % H
        tw = 0.55 + 0.45 * math.sin(t * rng.uniform(2.0, 5.0) + ph); b = tw * rng.uniform(0.45, 1.0)
        if z < 0.45: cv2.circle(near, (int(x / 2), int(y / 2)), int(rng.uniform(5, 11)), b * 0.45, -1, cv2.LINE_AA)
        else: cv2.circle(far, (int(x / 2), int(y / 2)), 1, b, -1, cv2.LINE_AA)
    lay = cv2.GaussianBlur(far, (0, 0), 0.8) * 1.6 + cv2.GaussianBlur(near, (0, 0), 3.0)
    lay = cv2.resize(lay, (W, H), interpolation=cv2.INTER_LINEAR)
    if sp is not None: lay = lay * (0.30 + 0.70 * np.exp(-(((_GX - sp[0]) ** 2 + (_GY - sp[1]) ** 2) / (0.75 * W) ** 2)))
    if m is not None: lay = lay * (1 - 0.85 * m)
    return np.clip(out + lay[..., None] * SUNC * 0.55 * a, 0, 1)

EMBER = np.array([0.18, 0.52, 1.00], np.float32)                                     # BGR hot orange

_EB = {}

def ember_points(s):
    """the background pixels just outside his silhouette (once per shot): where the embers lift off. Hair and shoulders weigh most."""
    if s["n"] not in _EB:
        _, m0 = render_shot(s, s["f0"] + 24, True, True)
        ring = np.clip(cv2.GaussianBlur(m0, (0, 0), 8) - m0, 0, 1)
        ys, xs = np.nonzero(ring > 0.05)
        keep = ys < H * 0.92; xs, ys = xs[keep], ys[keep]
        wgt = 1.0 + 2.5 * (ys < H * 0.40)                                               # more off his hair and shoulders
        _EB[s["n"]] = (xs, ys, wgt / wgt.sum())
    return _EB[s["n"]]

def burn_fx(out, f, s, m, heat):
    """he burns in the sunlight: a hot flickering rim on his edge and embers lifting off him into the light."""
    if heat <= 0.01 or m is None: return out
    t = (f - s["f0"]) / FPS
    inner = np.clip(m - cv2.GaussianBlur(m, (0, 0), 6), 0, 1); outer = np.clip(cv2.GaussianBlur(m, (0, 0), 14) - m, 0, 1)
    flick = 0.85 + 0.15 * math.sin(t * 31) * math.sin(t * 17 + 1)
    out = out + (inner * 3.2 + outer * 2.0)[..., None] * EMBER * heat * flick
    xs, ys, p = ember_points(s)
    if len(xs) == 0: return out
    rng = np.random.default_rng(881); core = np.zeros((H // 2, W // 2), np.float32); halo = np.zeros_like(core)
    picks = rng.choice(len(xs), 300, p=p)
    for i in range(300):
        idx = int(picks[i]); ts = rng.uniform(0.10, 0.95); life = rng.uniform(0.35, 0.85)
        vy, vx, w_, r_ = rng.uniform(200, 520), rng.normal(0, 70), rng.uniform(5, 11), rng.uniform(1.6, 4.2)
        age = t - ts
        if age < 0 or age > life: continue
        x = xs[idx] + vx * age + 20 * math.sin(age * w_ + i); y = ys[idx] - vy * age - 80 * age * age
        b = (1 - age / life) ** 1.1 * min(1.0, age / 0.05) * (0.6 + 0.4 * math.sin(age * 40 + i))
        cv2.circle(core, (int(x / 2), int(y / 2)), max(1, int(r_ / 2 + 0.5)), b, -1, cv2.LINE_AA)
        cv2.circle(halo, (int(x / 2), int(y / 2)), int(r_ * 3), b * 0.45, -1, cv2.LINE_AA)
    core = cv2.resize(cv2.GaussianBlur(core, (0, 0), 0.6), (W, H)); halo = cv2.resize(cv2.GaussianBlur(halo, (0, 0), 5), (W, H))
    return out + (core[..., None] * np.array([0.70, 0.90, 1.0], np.float32) * 1.6 + halo[..., None] * EMBER * 1.1) * heat

def cape_tr(A, B, j, f, sa, sb, pre=8, post=10):
    """a Dracula cape sweeps across the lens: black satin in broad moving folds with a soft sheen, a wide crimson lining
    turned out along its billowing leading edge, a soft shadow thrown ahead of it; the next shot is behind it."""
    u = clamp((j + pre + 0.5) / (pre + post), 0, 1); t = f / FPS
    e = u * u * (3 - 2 * u)
    yy = _GY / H; xl = -0.32 * W + 2.50 * W * e
    lead = xl + 0.24 * W * np.sin(np.pi * yy) ** 1.5 + 34 * np.sin(_GY * 0.0065 + t * 7) + 12 * np.sin(_GY * 0.019 - t * 11)
    trail = lead - 1.05 * W - 0.10 * W * np.sin(np.pi * yy)
    ahead = np.clip((_GX - lead) / 3 + 0.5, 0, 1); behind = np.clip((trail - _GX) / 3 + 0.5, 0, 1)
    cover = np.clip(1 - ahead - behind, 0, 1)
    dl = lead - _GX
    ph = dl * 0.0085 + 1.6 * np.sin(_GY * 0.0031 + t * 1.3) + 0.8 * np.sin(_GY * 0.0083 - t * 2.1)
    sh = 0.5 + 0.5 * np.sin(ph)                                                          # broad satin folds
    lumf = (0.010 + 0.075 * sh ** 2 + 0.20 * sh ** 9)[..., None]
    satin = lumf * np.array([1.10, 1.0, 1.0], np.float32) * 1.0
    lin = smooth_arr(1 - dl / 190) + smooth_arr(1 - (_GX - trail) / 60)                  # the lining, turned out along both edges
    lin = np.clip(lin, 0, 1)[..., None]
    lining = CRIMSON * (0.20 + 0.45 * sh[..., None] ** 2) + CRIMSON_H * 0.45 * sh[..., None] ** 10
    hem = np.exp(-(dl / 5.0) ** 2)[..., None] * CRIMSON_H * 0.5                         # the hem catches the light
    fabric = satin * (1 - lin) + lining * lin + hem
    fabric = cv2.GaussianBlur(fabric, (0, 0), sigmaX=10, sigmaY=0.1)                    # it's moving fast
    shadow = (np.clip(1 + dl / 200, 0, 1) * (dl < 0) * 0.6)[..., None]
    o = A * (1 - shadow) * ahead[..., None] + B * behind[..., None] + fabric * cover[..., None]
    return np.clip(o, 0, 1)

_MS = {}

def mist_field(seed, t, rise):
    """slow billows of mist: three octaves of soft value noise drifting upward at different speeds (quarter res), about 0..1."""
    h, w = H // 4, W // 4; acc = np.zeros((h, w), np.float32)
    for o, (cells, amp, sp) in enumerate(((3, 0.55, 1.0), (6, 0.30, 1.6), (12, 0.15, 2.4))):
        key = (seed, o)
        if key not in _MS:
            g = np.random.default_rng(seed * 10 + o).random((int(cells * 1.8) * 3, cells + 1)).astype(np.float32)
            _MS[key] = cv2.GaussianBlur(cv2.resize(g, (w, h * 3), interpolation=cv2.INTER_CUBIC), (0, 0), 2)
        st_ = int(t * rise * sp * h) % (h * 2)
        acc += _MS[key][st_:st_ + h] * amp
    return np.clip((acc - 0.22) / 0.56, 0, 1)

def mist_tr(A, B, j, f, sa, sb, pre=10, post=14):
    """Dracula turns to mist: the shot softens and drifts upward as it breaks into slow billows of silver mist, the frame
    fills with fog, and the next shot condenses out of the mist (from soft to sharp)."""
    u = clamp((j + pre + 0.5) / (pre + post), 0, 1); t = f / FPS
    n = cv2.resize(mist_field(77, t, 0.35), (W, H)); n2 = cv2.resize(mist_field(91, t, 0.25), (W, H))
    uA = clamp(u / 0.60, 0, 1); uB = clamp((u - 0.40) / 0.60, 0, 1)
    def soften(X, amt, dy):                                                              # a quarter-res blur, lifted upward
        q = cv2.resize(X.astype(np.float32), (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        if amt > 0.2: q = cv2.GaussianBlur(q, (0, 0), amt)
        q = cv2.resize(q, (W, H), interpolation=cv2.INTER_LINEAR)
        if abs(dy) > 0.5: q = np.roll(q, -int(dy), axis=0)
        return q
    As = soften(A, 7 * uA, 110 * uA ** 1.5) if uA > 0 else A
    A2_ = A * (1 - smooth(uA / 0.5)) + As * smooth(uA / 0.5)
    Bs = soften(B, 7 * (1 - uB), -40 * (1 - uB)) if uB < 1 else B
    B2_ = B * smooth((uB - 0.5) / 0.5) + Bs * (1 - smooth((uB - 0.5) / 0.5))
    vA = smooth_arr((n - 1.30 * uA + 0.30) / 0.45); vB = smooth_arr((n2 - 1.30 * (1 - uB) + 0.30) / 0.45)
    vB = vB * (1 - vA)
    fog = np.clip(1 - vA - vB, 0, 1)[..., None]
    billow = (0.6 * n + 0.4 * n2)[..., None]
    mistc = MOONS * (0.14 + 0.40 * billow ** 1.3) + CRIMSON * 0.05 * (_GY / H)[..., None]
    o = A2_ * vA[..., None] + B2_ * vB[..., None] + mistc * fog
    veil = math.sin(math.pi * u) ** 1.5 * 0.30                                          # drifting mist over everything at the peak
    return np.clip(o * (1 - veil * billow) + MOONS * 0.40 * veil * billow ** 1.5, 0, 1)

def bat_pass_tr(A, B, j, f, sa, sb, pre=7, post=9):
    """one great bat flies out of the dark straight through the lens: it comes out of the top-right, grows, beats its wings,
    fills the frame (the cut happens in its shadow) and dives out under the camera to reveal the next shot."""
    size = min(3200.0, 46 * 1.55 ** (j + pre)); g = min(1.0, size / 1100)
    x = W * (0.84 - 0.34 * g); y = H * (0.08 + 0.52 * g) + max(0, j) * H * 0.30
    spr = bat_sprite(((f / FPS) * 4.5) % 1.0, 260, 3); s0 = spr.shape[1] / 2 - 4
    sc = size / s0 / 4                                                                   # drawn at quarter res (it's soft when that close)
    pm = np.dstack([spr[..., :3] * spr[..., 3:4], spr[..., 3:4]])
    hs, ws = spr.shape[:2]
    M = np.float32([[sc, 0, x / 4 - sc * ws / 2], [0, sc, y / 4 - sc * hs / 2]])
    lay = cv2.warpAffine(pm, M, (W // 4, H // 4), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    bl = clamp((size - 300) / 220, 0, 10)
    if bl > 0.3: lay = cv2.GaussianBlur(lay, (0, 0), bl)
    lay = cv2.resize(lay, (W, H), interpolation=cv2.INTER_LINEAR)
    a = np.clip(lay[..., 3:4], 0, 1)
    base = A if j < 1 else B
    shade = 0.80 * math.exp(-((j - 0.5) / 1.5) ** 2)                                     # its shadow sweeps the frame as it passes
    o = base * (1 - shade) * (1 - a) + lay[..., :3]
    return np.clip(o, 0, 1)

TR2.update({"cape": (cape_tr, 8, 10), "mist": (mist_tr, 10, 14), "bat_pass": (bat_pass_tr, 7, 9)})

def hero105(out, f, tx):
    t = f / FPS; words = tx["words"]
    if t < words[0][1] - 0.02 or t > tx["end"] + 0.45: return out
    lines = tx["lines"]; nl = len(lines); t_end = tx["end"]
    sizes = [228] if nl == 1 else [150, 196]; ys = [1215] if nl == 1 else [1300, 1478]
    out = out * cap_scrim(ys[0] - 130, ys[-1] + 130, 0.38 * (1 - smooth((t - t_end + 0.1) / 0.3)))
    lay = np.zeros((H, W, 4), np.float32); bats = []
    for li, (text, size, yc) in enumerate(zip(lines, sizes, ys)):
        lets, wd = hero_letters(text, size); fit = min(1.0, 980 / max(1, wd)); t0 = words[li][1]
        for i, (c, lm, xoff) in enumerate(lets):
            st_ = t0 + 0.035 * i; v = clamp((t - st_) / 0.24, 0, 1)
            if v <= 0: continue
            ve = eout(v, 3.0); x = W / 2 + xoff * fit
            sc = (0.30 + 0.70 * ve + 0.06 * math.sin(math.pi * v)) * fit; rot = (1 - ve) * (24 if i % 2 else -24)
            ex = clamp((t - (t_end - 0.05 + 0.025 * i)) / 0.30, 0, 1)
            fill = eout(clamp((t - st_ - 0.12) / 0.34, 0, 1), 2.0); hh = lm.shape[0]; yy = np.linspace(1, 0, hh)[:, None]
            cm = np.broadcast_to(cv2.GaussianBlur((yy < fill * 1.08).astype(np.float32), (0, 0), 3), lm.shape)
            col = WHITE * (1 - cm[..., None]) + EMPH * cm[..., None]
            if ex < 1:
                pad = 26; lmp = np.pad(lm, pad); colp = np.pad(col, ((pad, pad), (pad, pad), (0, 0)), mode="edge")
                k_ = max(3, int(size * 0.06)) | 1
                key = cv2.dilate(lmp, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_, k_)))
                rgb = colp * lmp[..., None] + np.array([0.02, 0.02, 0.025], np.float32) * (key - lmp)[..., None]
                draw_sprite(lay, np.dstack([rgb, key]).astype(np.float32), x, yc - 30 * ex, sc * (1 + 0.15 * ex), rot, 1.0,
                            (0.1 + 5 * (1 - ve) + 6 * ex) if (v < 1 or ex > 0) else 0.0, (1 - ex) * ve)
                fl = math.sin(math.pi * clamp(v / 0.7, 0, 1)) * 0.55
                if fl > 0.02: out = add_glow(out, x, yc, size * 0.5, fl * 0.30, CRIMSON_H)
            if ex > 0:                                                                   # each letter breaks into bats that fly off
                rng = np.random.default_rng(i * 17 + li * 5)
                side = -1 if x < W / 2 else 1                                                # they scatter outward, away from his face
                for q in range(5):
                    a = rng.uniform(-0.45, 0.25); sp = rng.uniform(900, 1900); tt = ex * 0.45
                    if ex >= 0.98: continue
                    bats.append((x + side * math.cos(a) * sp * tt + rng.uniform(-30, 30), yc + math.sin(a) * sp * tt + rng.uniform(-20, 20),
                                 rng.uniform(36, 62) * (1 + 0.8 * ex), rng.random(), rng.uniform(7, 10), 0.3 + 3 * ex))
    if bats:
        bl = bats_layer(bats, t, 2); lay[..., :3] = lay[..., :3] * (1 - bl[..., 3:4]) + bl[..., :3] * bl[..., 3:4]; lay[..., 3:4] = np.maximum(lay[..., 3:4], bl[..., 3:4])
    sh = cv2.GaussianBlur(lay[..., 3], (0, 0), 9)[..., None] * 0.6
    out = out * (1 - sh)
    return np.clip(out * (1 - lay[..., 3:4]) + lay[..., :3] * lay[..., 3:4], 0, 1)

def text103(out, f):
    for tx in E.TEXT:
        if tx["style"] == "cap": out = text_cap103(out, f, tx)
        elif tx["style"] == "hero": out = hero105(out, f, tx)
    return out

# ---------------------------------------------------------------------------- finish + frame
def finish105(out, f, night, logo=False):
    L = lum(out); hi = np.clip(L - 0.64, 0, 1)
    if not logo:                                                                         # the logo keeps its own colours: no halo or red bloom on it
        halo = cv2.resize(cv2.GaussianBlur(cv2.resize(hi, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 8), (W, H))[..., None]
        red = np.clip((out[..., 2] - np.maximum(out[..., 0], out[..., 1])) * 2, 0, 1)
        rh = cv2.resize(cv2.GaussianBlur(cv2.resize(red, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 6), (W, H))[..., None]
        out = out + halo * (MOONS * 0.20 if night else SUNC * 0.26) + rh * CRIMSON * 0.18
    L = lum(out)[..., None]
    out = out + grain(f, 1.0) * (0.010 + 0.018 * L * (1 - L) * 2.5)
    return np.clip(out * VIG, 0, 1)

# ---------------------------------------------------------------------------- rev 3
def eclipse_tr(A, B, j, f, sa, sb, pre=10, post=14):
    """the sun goes out: the moon's black disc slides across the frame with a blazing, streaming corona; the next shot (night)
    is inside it. A diamond-ring flash fires on its rim as it centres, then the disc swells until night fills the frame."""
    u = clamp((j + pre + 0.5) / (pre + post), 0, 1); t = f / FPS
    e1 = eout(clamp(u / 0.55, 0, 1), 2.2)
    cx = -0.60 * W + 1.10 * W * e1; cy = H * 0.40
    R = 0.62 * W + 1.30 * H * ein(clamp((u - 0.50) / 0.50, 0, 1), 2.0)
    rr = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2)
    inside = np.clip((R - rr) / 2.5 + 0.5, 0, 1)[..., None]
    ang = np.arctan2(_GY - cy, _GX - cx)
    streak = 0.55 + 0.45 * np.sin(ang * 13 + t * 2.0) * np.sin(ang * 7 - t * 1.3)        # corona streamers
    d = np.clip(rr - R, 0, None)
    corona = (np.exp(-d / (16 + 34 * streak)) * (0.55 + 0.45 * streak) * (rr >= R - 2))[..., None]
    dim = 0.12 + 0.55 * e1                                                               # the world dims as the light goes
    o = A * (1 - dim) * (1 - inside) + B * inside
    o = o + corona * (WHITE * 0.55 + SUNC * 0.45) * (1 - 0.7 * ein(clamp((u - 0.55) / 0.45, 0, 1), 1.5))
    dr = math.exp(-((u - 0.47) / 0.07) ** 2)                                              # the diamond ring
    if dr > 0.02:
        px, py = cx + R * 0.92, cy - R * 0.39
        o = add_glow(o, px, py, 55, 1.5 * dr, WHITE); o = add_glow(o, px, py, 260, 0.55 * dr, SUNC)
        sh_ = (np.exp(-((_GY - py) / 5) ** 2) * np.exp(-((_GX - px) / 560) ** 2) + np.exp(-((_GX - px) / 4) ** 2) * np.exp(-((_GY - py) / 300) ** 2) * 0.6) * dr
        o = o + sh_[..., None] * (WHITE * 0.6 + SUNC * 0.4)
    return np.clip(o, 0, 1)

def gather_bats(out, f, s, m):
    """bats begin to gather in the darkening sky behind him: a few far silhouettes at first, more toward the drop."""
    if m is None: return out
    k = kof(f); g = clamp((k - s["k0"]) / (s["k1"] - s["k0"]), 0, 1); t = f / FPS
    rng = np.random.default_rng(910); nf = 3 + 30 * g ** 1.4
    lay = np.zeros((H, W, 4), np.float32)
    for i in range(34):
        x0, y0 = rng.uniform(-100, W + 100), rng.uniform(0.03 * H, 0.42 * H); sp = rng.uniform(70, 190) * (1 if rng.random() < 0.6 else -1)
        sz, ph, hz = rng.uniform(16, 38), rng.random(), rng.uniform(7, 11)
        a = clamp(nf - i, 0, 1)
        if a <= 0: continue
        x = (x0 + sp * t) % (W + 200) - 100; y = y0 + 20 * math.sin(t * 2.3 + i)
        draw_sprite(lay, bat_sprite((ph + t * hz) % 1.0, sz, 0), x, y, 1.0, 0, 1.0, 0.4, a)
    a_ = lay[..., 3:4] * (1 - m[..., None])
    return np.clip(out * (1 - a_) + lay[..., :3] * a_, 0, 1)

def rim_fx(out, f, s, m):
    """a crimson backlight on his edge (night shots)."""
    a = s.get("rim", 0.0)
    if not a or m is None: return out
    inner = np.clip(m - cv2.GaussianBlur(m, (0, 0), 5), 0, 1); glow = np.clip(cv2.GaussianBlur(m, (0, 0), 18) - m, 0, 1)
    pul = 0.85 + 0.15 * math.sin(f / FPS * 6.0)
    return np.clip(out + (inner * 1.5 + glow * 0.8)[..., None] * CRIMSON_H * 0.55 * a * pul, 0, 1)

SUN_T = (0.78, 0.13)                                                                     # the sun of frame 0 (the boat): the finale's embers fly into it

ASH = dict(heat=83.5, r0=84.3, r1=86.5, arrive=86.95, flash0=86.75, flash1=87.25)

LIGHT_G = np.clip(DAWNW * 0.62 + SUNC * 0.40, 0, 1)

_AS = {}

def ash_setup(s):
    """once: the burn order over his silhouette (edges facing the sun first, the core last, a ragged paper-burn edge) and the
    ember particles."""
    if "R" in _AS: return _AS
    f_r = E.fh(ASH["r0"]); img, m0 = render_shot(s, f_r, True, True)
    mb = (m0 > 0.5).astype(np.uint8)
    dn = cv2.distanceTransform(mb, cv2.DIST_L2, 5).astype(np.float32); dn = dn / (np.percentile(dn[mb > 0], 99) + 1e-6)
    rng0 = np.random.default_rng(431)
    noise = (cv2.resize(rng0.random((24, 14)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC) * 0.6
             + cv2.resize(rng0.random((90, 52)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC) * 0.4)
    o = 0.46 * np.clip(dn, 0, 1) + 0.30 * (1 - _GX / W) + 0.12 * (_GY / H) + 0.20 * noise
    lo, hi = np.percentile(o[mb > 0], 2), np.percentile(o[mb > 0], 98)
    on = np.clip((o - lo) / (hi - lo + 1e-6), 0, 1)
    _AS["R"] = ASH["r0"] + (ASH["r1"] - ASH["r0"]) * on                                  # release time (k) for every pixel
    ys, xs = np.nonzero(mb); rng = np.random.default_rng(432); N = 3000
    pick = rng.choice(len(xs), N, replace=len(xs) < N)
    px, py = xs[pick].astype(np.float32), ys[pick].astype(np.float32)
    kr = _AS["R"][ys[pick], xs[pick]]
    _AS.update(px=px, py=py, col=np.clip(img[ys[pick], xs[pick]].astype(np.float32), 0, 1), kr=kr,
               ka=np.minimum(kr + rng.uniform(0.7, 1.4, N), ASH["arrive"]), vx=rng.uniform(-110, 110, N).astype(np.float32),
               vy=rng.uniform(140, 380, N).astype(np.float32), ph=rng.uniform(0, 6.3, N).astype(np.float32),
               th0=rng.uniform(0, 6.3, N).astype(np.float32), rho=rng.uniform(40, 230, N).astype(np.float32))
    return _AS

def clean_plate(out, m):
    """the street behind him, guessed: each row continues the background on either side of him (the street, the hedge line and
    the sky are horizontal), smoothed, with a little texture. Rows he fills completely take the nearest row that shows the street."""
    q = cv2.resize(np.clip(out, 0, 1), (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    bg = (cv2.resize(m, (W // 4, H // 4), interpolation=cv2.INTER_AREA) < 0.15).astype(np.float32)
    cnt = bg.sum(1); rows = (q * bg[..., None]).sum(1) / np.maximum(cnt, 1)[:, None]
    good = cnt > 6; idx = np.arange(len(cnt))
    if good.any():
        for c in range(3): rows[:, c] = np.interp(idx, idx[good], rows[good, c])
    rows = cv2.GaussianBlur(rows[:, None, :], (0, 0), sigmaX=0.1, sigmaY=4)[:, 0, :]
    pl = np.repeat(rows[:, None, :], W // 4, axis=1)
    tex = cv2.GaussianBlur(q, (0, 0), 6) - cv2.GaussianBlur(q, (0, 0), 20)               # a breath of the frame's own texture
    pl = np.clip(pl + tex * 0.3, 0, 1)
    return cv2.GaussianBlur(cv2.resize(pl, (W, H), interpolation=cv2.INTER_LINEAR), (0, 0), 3) * 0.9

def ash_body(out, f, s, m):
    """the paper burn on his body (runs before the sun is drawn, so the sun only sees the street where he has gone): a
    charred edge, then a thin glowing line, then the street behind him."""
    k = kof(f)
    if k < ASH["r0"] - 0.15 or m is None: return out
    R = ash_setup(s)["R"]; d = k - R
    mh = cv2.dilate(np.clip(m * 1.8 - 0.15, 0, 1), np.ones((7, 7), np.uint8))          # a hard matte, a little wide: no ghost of his edge
    char = mh * smooth_arr((d + 0.13) / 0.10)                                            # it chars just ahead of the flame
    rel = mh * smooth_arr(d / 0.035)                                                     # what has burnt away
    front = m * np.exp(-((d - 0.01) / 0.03) ** 2)                                        # the thin burning line
    out = out * (1 - 0.70 * char[..., None] * (1 - rel[..., None]))
    if rel.max() > 0.001: out = out * (1 - rel[..., None]) + clean_plate(out, m) * rel[..., None]
    halo = cv2.GaussianBlur(front, (0, 0), 6)
    return out + front[..., None] * (EMBER * 2.4 + np.array([0.25, 0.45, 0.55], np.float32)) + halo[..., None] * EMBER * 1.2

def ashes_fx(out, f, s, m):
    """ASHES TO SUN: he burns away like paper (a charred edge, a thin glowing line, the street behind showing through), from the
    side facing the sun inward; every burnt piece becomes an ember that drifts up and spirals into the sun."""
    k = kof(f)
    if k < ASH["r0"] - 0.15 or m is None: return out
    A_ = ash_setup(s)
    alive = (k > A_["kr"]) & (k < A_["ka"])
    if alive.any():
        kr, ka = A_["kr"][alive], A_["ka"][alive]
        sP = np.clip((k - kr) / (ka - kr), 0, 1); tau = (k - kr) * E.HB
        dx = A_["px"][alive] + A_["vx"][alive] * tau + 26 * np.sin(5 * tau + A_["ph"][alive])
        dy = A_["py"][alive] - A_["vy"][alive] * tau - 90 * tau * tau
        th_ = A_["th0"][alive] + 7.0 * sP; rho = A_["rho"][alive] * (1 - sP) ** 1.4
        tx, ty = W * SUN_T[0] + rho * np.cos(th_), H * SUN_T[1] + rho * np.sin(th_)
        e = sP ** 1.7 * (3 - 2 * sP)
        x = dx * (1 - e) + tx * e; y = dy * (1 - e) + ty * e
        h1 = np.clip(sP * 3, 0, 1)[:, None]; h2 = np.clip((sP - 0.6) / 0.4, 0, 1)[:, None]
        col = A_["col"][alive] * 1.4 * (1 - h1) + EMBER * 1.6 * h1
        col = col * (1 - h2) + (WHITE * 0.7 + SUNC * 0.5) * 1.5 * h2
        b = (np.clip((k - kr) / 0.05, 0, 1) * (0.7 + 0.6 * sP))[:, None]
        xi, yi = (x / 2).astype(np.int32), (y / 2).astype(np.int32)
        ok = (xi >= 0) & (xi < W // 2) & (yi >= 0) & (yi < H // 2)
        buf = np.zeros((H // 2, W // 2, 3), np.float32)
        np.add.at(buf, (yi[ok], xi[ok]), col[ok] * b[ok])
        core = cv2.GaussianBlur(buf, (0, 0), 0.7); glow = cv2.GaussianBlur(buf, (0, 0), 4.0)
        out = out + cv2.resize(core * 1.3 + glow * 3.0, (W, H), interpolation=cv2.INTER_LINEAR)
    return out

TR2.update({"eclipse": (eclipse_tr, 10, 14)})

def card_flip(A, B, j, f, sa, sb, pre=9, post=11):
    """a sunny card flip: the frame turns over in 3D around its vertical axis (a slight bow, a hot specular glint as it passes
    edge-on to the sun) against the bright blurred sky of both shots; the next shot is on its back."""
    u = clamp((j + pre + 0.5) / (pre + post), 0, 1); e = u * u * (3 - 2 * u); th = e * math.pi
    face = A if th < math.pi / 2 else B
    ang = th if th < math.pi / 2 else th - math.pi
    sky = cv2.resize(cv2.GaussianBlur(cv2.resize((A + B) * 0.5, (W // 8, H // 8), interpolation=cv2.INTER_AREA), (0, 0), 6), (W, H))
    sky = np.clip(sky * 0.55 + SUNC * 0.42, 0, 1)
    sc = 0.86 + 0.14 * abs(math.cos(th)) ** 0.5                                          # it pulls back a little as it turns
    foc = 2400.0; c, s_ = math.cos(ang), math.sin(ang)
    pts = []
    for (x, y) in ((-W / 2, -H / 2), (W / 2, -H / 2), (W / 2, H / 2), (-W / 2, H / 2)):
        X, Z = x * c * sc, x * s_ * sc; Y = y * sc
        p = foc / (foc + Z); pts.append((W / 2 + X * p, H / 2 + Y * p))
    M = cv2.getPerspectiveTransform(np.float32([(0, 0), (W, 0), (W, H), (0, H)]), np.float32(pts))
    card = cv2.warpPerspective(face.astype(np.float32), M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
    msk = cv2.warpPerspective(np.ones((H, W), np.float32), M, (W, H), flags=cv2.INTER_LINEAR)[..., None]
    shade = 0.75 + 0.25 * abs(math.cos(ang))
    glint = math.exp(-((abs(ang) - 1.25) / 0.18) ** 2)                                  # it catches the sun as it turns edge-on
    card = card * shade + glint * 0.45 * SUNC
    sh = cv2.GaussianBlur(msk[..., 0], (0, 0), 30)[..., None] * 0.35
    o = sky * (1 - sh) * (1 - msk) + card * msk
    return np.clip(o, 0, 1)

_PF2 = {}
def palm_frond(seed, L=900):
    """a palm frond silhouette (RGBA, dark green-black): a curved spine with long drooping leaflets."""
    if seed in _PF2: return _PF2[seed]
    rng = np.random.default_rng(seed); w, h = int(L * 1.25), int(L * 0.75); m = np.zeros((h, w), np.float32)
    sp = [(w * 0.04 + L * q, h * 0.30 + L * 0.32 * q * q - L * 0.05 * math.sin(q * 3)) for q in np.linspace(0, 1, 40)]
    cv2.polylines(m, [np.array(sp, np.int32)], False, 1.0, max(3, L // 90), cv2.LINE_AA)
    for i in range(2, 38):
        x0, y0 = sp[i]; dx, dy = sp[i + 1][0] - sp[i - 1][0], sp[i + 1][1] - sp[i - 1][1]; n_ = math.hypot(dx, dy) + 1e-6
        for side in (-1, 1):
            ll = L * (0.30 + 0.12 * math.sin(i / 38 * math.pi)) * rng.uniform(0.8, 1.1) * (1 - 0.6 * (i / 38) ** 3)
            a0 = math.atan2(dy, dx) + side * rng.uniform(0.55, 0.9)
            tip = (x0 + ll * math.cos(a0), y0 + ll * math.sin(a0) + ll * 0.35)
            mid = ((x0 + tip[0]) / 2 + side * 6, (y0 + tip[1]) / 2)
            wdt = max(2, int(L / 70))
            poly = np.array([(x0, y0), (mid[0] - wdt * (-dy / n_), mid[1] - wdt * (dx / n_)), tip, (mid[0] + wdt * (-dy / n_), mid[1] + wdt * (dx / n_))], np.int32)
            cv2.fillPoly(m, [poly], 1.0, cv2.LINE_AA)
    rgb = np.zeros((h, w, 3), np.float32) + np.array([0.04, 0.07, 0.05], np.float32)
    _PF2[seed] = np.dstack([rgb, cv2.GaussianBlur(m, (0, 0), 0.8)]).astype(np.float32); return _PF2[seed]

def palm_sweep(A, B, j, f, sa, sb, pre=9, post=11):
    """palm fronds sweep past the lens against the sun (near ones big and soft, far ones sharp); in their shadow the next shot
    comes in, warm light flickering through the leaves."""
    u = clamp((j + pre + 0.5) / (pre + post), 0, 1); t = f / FPS
    lay = np.zeros((H, W, 4), np.float32)
    for i, (seed, z, y0, flip) in enumerate(((11, 0.55, 0.20, 1), (12, 0.75, 0.62, -1), (13, 0.42, 0.88, 1), (14, 0.9, 0.40, -1), (15, 0.5, 0.05, -1))):
        fr = palm_frond(seed)
        x = (-0.9 * W + 3.6 * W * eout(clamp(u * 1.18 - i * 0.03, 0, 1), 1.3)) * (1 / z) * 0.55 + W * 0.2
        y = H * y0 + 40 * math.sin(t * 3 + i)
        sc = 1.25 / z; rot = 18 * math.sin(t * 2 + i) + (8 if flip > 0 else -8)
        draw_sprite(lay, fr, x, y, sc, rot, flip, clamp((0.8 - z) * 14, 0, 9), 1.0)
    a = lay[..., 3:4]
    cov = clamp(math.sin(math.pi * u) * 1.2, 0, 1)
    mix = smooth(clamp((u - 0.35) / 0.3, 0, 1))
    base = A * (1 - mix) + B * mix
    dapple = cv2.resize(cv2.GaussianBlur(cv2.resize(a, (W // 8, H // 8), interpolation=cv2.INTER_AREA), (0, 0), 3), (W, H))
    base = base * (1 - 0.35 * dapple[..., None] * cov) + SUNC * 0.10 * (1 - dapple[..., None]) * cov
    return np.clip(base * (1 - a) + lay[..., :3] * a, 0, 1)

TR2.update({"card_flip": (card_flip, 9, 11), "palm_sweep": (palm_sweep, 9, 11)})

def base105(s, f):
    sp = sun_pos(s, f); m = None
    if s.get("bloodmoon"): out = bloodmoon_fx(f, s)
    elif s.get("seg") and (sp is not None or s.get("daybreak") or s.get("rim") or s.get("gather")): out, m = render_shot(s, f, True, True)
    else: out = render_shot(s, f)
    if s.get("ghost"): out = ghost_fx(out, f, s)
    if s.get("gather"): out = gather_bats(out, f, s, m)
    ms = m
    if s.get("daybreak") and m is not None and kof(f) > ASH["r0"] - 0.2:               # he burns first, and the sun only sees what is left of him
        out = ash_body(out, f, s, m)
        ms = m * (1 - smooth_arr((kof(f) - ash_setup(s)["R"]) / 0.035)) * (kof(f) < ASH["r1"] + 0.1)
    if sp is not None: out = sun_fx(out, f, sp[0], sp[1], sp[2], SUNC if s.get("look") == "day" else SUNC * 0.6 + DUSKC * 0.5, sp[3], ms)
    if s.get("motes"): out = day_motes(out, f, s, ms, sp)
    if s.get("rim"): out = rim_fx(out, f, s, m)
    if s.get("flare"): out = anam_flare(out, s["flare"], f)
    if s.get("fog"): out = fog_fx(out, f, s["fog"])
    if s.get("daybreak"): out = daybreak_fx(out, f, s, ms)
    if s.get("spin"): out = spin_fx(out, f, s)
    else: out = cam_float(out, f, s)
    return out

# ---------------------------------------------------------------------------- rev 2 transitions: the cape, the mist, the great bat

_E5 = {}
def edge105(S_, which):
    key = (S_["n"], which)
    if key not in _E5:
        if len(_E5) > 6: _E5.clear()
        fr = S_["f0"] if which == "first" else S_["f1"] - 1
        _E5[key] = base105(S_, fr)
    return _E5[key]

def init_hits():
    HITS.clear()
    for k_, a in ((32, 22), (48, 12), (64, 18), (12, 6), (60, 8)): HITS.append((E.fh(k_), a, 4.0))

# <<< v105 section

if __name__ == "__main__":
    main()
