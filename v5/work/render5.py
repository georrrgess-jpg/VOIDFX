"""Renderer for FASTEST — The Flash × Duvet (voidfx v5, 1080x1920). Reads v5/work/edl5.py.

  python3 v5/work/render5.py prep                    # load + face-track every shot -> v3/work/tracks3.json
  python3 v5/work/render5.py stills NAME f1 f2 ...   # tiled stills -> v3/frames/NAME.jpg
  python3 v5/work/render5.py full f1 f2 ...          # full-res stills -> v3/frames/full_XXXX.jpg
  python3 v5/work/render5.py video OUTDIR            # final render (needs v3/audio/mix*.wav)
"""
import os, sys, json, math, bisect, subprocess
import numpy as np, cv2
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont
from scipy.interpolate import PchipInterpolator

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edl5 as E
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
    json.dump(out, open(f"{ROOT}/v5/work/tracks5.json", "w"))

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
    np.savez_compressed(f"{ROOT}/v5/work/seg5.npz", **out)

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


def main():
    mode = sys.argv[1]
    load(); init_hits()
    if mode == "prep":
        prep_tracks(); prep_seg(); return
    RAW_TRK.update(json.load(open(f"{ROOT}/v5/work/tracks5.json")))
    z = np.load(f"{ROOT}/v5/work/seg5.npz"); SEG.update({k: z[k] for k in z.files})
    if mode == "stills":
        name = sys.argv[2]; frames = [int(a) for a in sys.argv[3:]]; ims = []
        for f in frames:
            im = cv2.resize(render(f), (270, 480), interpolation=cv2.INTER_AREA)
            cv2.putText(im, str(f), (5, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1, cv2.LINE_AA); ims.append(im)
        while len(ims) % 6: ims.append(np.zeros_like(ims[0]))
        cv2.imwrite(f"{ROOT}/v5/frames/{name}.jpg", np.vstack([np.hstack(ims[i:i + 6]) for i in range(0, len(ims), 6)]), [cv2.IMWRITE_JPEG_QUALITY, 88])
        return
    if mode == "full":
        for f in [int(a) for a in sys.argv[2:]]:
            cv2.imwrite(f"{ROOT}/v5/frames/full_{f:04d}.jpg", render(f), [cv2.IMWRITE_JPEG_QUALITY, 92])
        return
    if mode == "video":
        outdir = f"{ROOT}/{sys.argv[2]}"; os.makedirs(outdir, exist_ok=True)
        vf = "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p"
        tags = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-itsoffset", str(-1024 / 48000), "-i", f"{ROOT}/v5/audio/mix_preroll.wav", "-i", f"{ROOT}/v5/audio/mix.wav",
               "-map", "0:v", "-map", "1:a", "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-maxrate", "26M", "-bufsize", "52M",
               "-profile:v", "high", "-level", "4.2", "-g", "120", "-bf", "3", *tags, "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
               "-movflags", "+faststart", f"{outdir}/fastest_flash_voidfx_9x16.mp4",
               "-map", "0:v", "-map", "2:a", "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "11", "-profile:v", "high", "-level", "5.1",
               *tags, "-c:a", "pcm_s24le", "-ar", "48000", f"{outdir}/fastest_flash_voidfx_9x16_master.mov"]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        with Pool(4) as pool:
            for i, fr in enumerate(pool.imap(render, range(E.DUR_F), chunksize=4)):
                p.stdin.write(fr.tobytes())
                if i % 150 == 0: print(f"frame {i}/{E.DUR_F}", flush=True)
        p.stdin.close(); p.wait(); print("done", outdir, flush=True)

if __name__ == "__main__":
    main()
