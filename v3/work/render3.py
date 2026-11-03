"""Renderer for SURPRISE — Doakes × Need It (voidfx v3, 1080x1920). Reads v3/work/edl3.py.

  python3 v3/work/render3.py prep                    # load + face-track every shot -> v3/work/tracks3.json
  python3 v3/work/render3.py stills NAME f1 f2 ...   # tiled stills -> v3/frames/NAME.jpg
  python3 v3/work/render3.py full f1 f2 ...          # full-res stills -> v3/frames/full_XXXX.jpg
  python3 v3/work/render3.py video OUTDIR            # final render (needs v3/audio/mix*.wav)
"""
import os, sys, json, math, bisect, subprocess
import numpy as np, cv2
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont
from scipy.interpolate import PchipInterpolator

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edl3 as E
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
    json.dump(out, open(f"{ROOT}/v3/work/tracks3.json", "w"))

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
        if s["n"] == "dex_still" and u > 0.75: z *= 1 + 0.12 * ein((u - 0.75) / 0.25, 2)
        ch = sh / z; cw = ch * 9 / 16
        if fa:
            cx, cy = fa[0], fa[1] + ch * (0.5 - 0.37)
        else:
            mc = s.get("cx", (sw / 2, sw / 2)); cx = mc[0] + (mc[1] - mc[0]) * smooth(u); cy = sh / 2
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
    else:
        sat = 1.08
        x = L + (x - L) * sat
        x = x + (1 - L) ** 2 * np.array([0.030, 0.018, -0.010], np.float32) + L ** 2 * np.array([-0.025, 0.006, 0.030], np.float32)
    if s.get("drain"):
        u = (f - s["f0"]) / max(1, s["f1"] - s["f0"]); d = smooth(u)
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

def render_shot(s, f, with_shake=True):
    img, t, u = source_img(s, f)
    if s.get("fit"): return render_fit(s, f, img, u, with_shake)
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

# ============================================================================ graphics
def caption(out, f):
    t = f / FPS
    for i, words in enumerate(E.CAPTIONS):
        t_in = E.d2e(i, words[0][1]) - 0.04; t_out = E.d2e(i, E.CAP_END[i]) + 0.10
        if not (t_in <= t < t_out): continue
        times = [E.d2e(i, w[1]) for w in words]
        cur = max([j for j, tw in enumerate(times) if tw <= t + 0.02], default=-1)
        lines, line = [], []
        fsz = 74
        maxw = 860
        for j, (w, _) in enumerate(words):
            test = " ".join(x for x, _ in line + [(w, 0)])
            if line and font(F_BLACK, fsz).getlength(test) > maxw:
                lines.append(line); line = []
            line.append((w, j))
        lines.append(line)
        y = 1250 - (len(lines) - 1) * 46
        a_all = clamp((t_out - t) / 0.10, 0, 1)
        sp = font(F_BLACK, fsz).getlength(" ")
        for ln in lines:
            widths = [font(F_BLACK, fsz).getlength(w) for w, _ in ln]
            x = W / 2 - (sum(widths) + sp * (len(ln) - 1)) / 2
            for (w, j), wd in zip(ln, widths):
                if j <= cur:
                    k = (t - times[j]) * FPS
                    pop = 1 + 0.18 * math.exp(-k / 3)
                    active = (j == cur)
                    col = RED if active else WHITE
                    m = text_mask(w, F_BLACK, int(fsz * pop))
                    lay = shadowed(m, col, blur=8, sa=0.85, stroke=6)
                    out = paste(out, lay, int(x + wd / 2 - lay.shape[1] / 2), int(y - lay.shape[0] / 2), a_all * clamp(k / 2 + 0.4, 0, 1))
                x += wd + sp
            y += 92
        # speaker chip
        spk = E.CAP_SPEAKER[i]
        m = text_mask(spk, F_MONO, 26, tracking=6)
        chip = np.zeros((m.shape[0] + 18, m.shape[1] + 34, 4), np.float32); chip[..., :3] = RED if spk == "DOAKES" else np.array([0.10, 0.10, 0.10], np.float32); chip[..., 3] = 0.92
        chip[9:9 + m.shape[0], 17:17 + m.shape[1], :3] = chip[9:9 + m.shape[0], 17:17 + m.shape[1], :3] * (1 - m[..., None]) + WHITE * m[..., None]
        out = paste(out, chip, int(W / 2 - chip.shape[1] / 2), int(1250 - (len(lines) - 1) * 46 - 120), a_all * clamp((t - t_in) / 0.12, 0, 1))
    return out

def name_tag(out, f, s):
    k = f - s["f0"]
    if not s.get("tag") or k > s["f1"] - s["f0"] - 2: return out
    t, u, _ = src_time(s, f); fa = face_at(s, t)
    if not fa: return out
    fx, fy, sc = to_screen(s, f, fa[0], fa[1]); fr = fa[2] * sc * 0.5
    ax, ay = fx + fr * 0.9, fy - fr * 0.95                      # anchor: just above-right of the head
    m = text_mask(s["tag"], F_MONO, 40, tracking=4)
    cw_, ch_ = m.shape[1] + 44, m.shape[0] + 26
    bx = clamp(ax + 60, 50, W - 50 - cw_); by = clamp(ay - 170, 300, H)
    p = eout(k / 7, 3)
    ex, ey = bx + 20, by + ch_
    cv2.line(out, (int(ax), int(ay)), (int(ax + (ex - ax) * p), int(ay + (ey - ay) * p)), tuple(float(c) for c in WHITE), 3, cv2.LINE_AA)
    cv2.circle(out, (int(ax), int(ay)), 8, tuple(float(c) for c in RED), -1, cv2.LINE_AA)
    if p >= 1:
        q = eout((k - 7) / 6, 3)
        chip = np.zeros((ch_, cw_, 4), np.float32); chip[..., :3] = 0.05; chip[..., 3] = 0.86
        chip[:, :8, :3] = RED; chip[:, :8, 3] = 1.0
        n = min(len(s["tag"]), max(0, int((k - 7) / 1.0)))
        mm = text_mask(s["tag"][:n], F_MONO, 40, tracking=4) if n else None
        if mm is not None:
            h_, w_ = mm.shape; chip[13:13 + h_, 26:26 + w_, :3] = chip[13:13 + h_, 26:26 + w_, :3] * (1 - mm[..., None]) + WHITE * mm[..., None]
        wv = max(1, int(cw_ * q)); chip = chip[:, :wv]
        out = paste(out, chip, int(bx), int(by))
    return out

def stamp(out, f, s):
    t = f / FPS; t0 = E.d2e(0, 18.02)
    if not (t0 <= t < s["t1"]): return out
    k = (t - t0) * FPS
    if "stamp" not in _SH:
        m1 = text_mask("BAY HARBOR", F_BLACK, 96, tracking=4); m2 = text_mask("BUTCHER", F_BLACK, 150, tracking=6)
        wd = max(m1.shape[1], m2.shape[1]) + 90; ht = m1.shape[0] + m2.shape[0] + 80
        m = np.zeros((ht, wd), np.float32)
        m[30:30 + m1.shape[0], (wd - m1.shape[1]) // 2:(wd - m1.shape[1]) // 2 + m1.shape[1]] = m1
        m[42 + m1.shape[0]:42 + m1.shape[0] + m2.shape[0], (wd - m2.shape[1]) // 2:(wd - m2.shape[1]) // 2 + m2.shape[1]] = m2
        cv2.rectangle(m, (6, 6), (wd - 7, ht - 7), 1.0, 9); cv2.rectangle(m, (20, 20), (wd - 21, ht - 21), 1.0, 3)
        rng = np.random.default_rng(9); nz = cv2.GaussianBlur(rng.random((ht, wd)).astype(np.float32), (0, 0), 1.4)
        m = m * np.clip((nz - 0.36) * 6, 0.25, 1.0)                                # worn ink
        M = cv2.getRotationMatrix2D((wd / 2, ht / 2), 8, 1.0)
        big = cv2.warpAffine(np.pad(m, 60), cv2.getRotationMatrix2D(((wd + 120) / 2, (ht + 120) / 2), 8, 1.0), (wd + 120, ht + 120))
        _SH["stamp"] = big
    m = _SH["stamp"]; sc = 1 + 0.9 * math.exp(-k / 2.2)
    mm = cv2.resize(m, (int(m.shape[1] * sc), int(m.shape[0] * sc)), interpolation=cv2.INTER_LINEAR)
    lay = np.dstack([np.full_like(mm, RED[0]), np.full_like(mm, RED[1]), np.full_like(mm, RED[2] * 0.95), mm * 0.92])
    a = clamp(k / 2, 0, 1)
    return paste(out, lay, int(W / 2 - lay.shape[1] / 2), int(1505 - lay.shape[0] / 2), a)

def reticle(out, f, s):
    t, u, _ = src_time(s, f); fa = face_at(s, t)
    if not fa: return out
    fx, fy, sc = to_screen(s, f, fa[0], fa[1]); fr = fa[2] * sc * 0.75
    k = f - s["f0"]
    if s["n"] == "dex_still": fr *= 1.0 - 0.35 * smooth(u)
    else: fr *= 1.0 + 0.6 * math.exp(-k / 5)
    a = clamp(k / 4, 0, 1)
    ov = np.zeros((H, W), np.float32)
    cv2.circle(ov, (int(fx), int(fy)), int(fr), 1.0, 3, cv2.LINE_AA)
    cv2.circle(ov, (int(fx), int(fy)), int(fr * 0.08), 1.0, -1, cv2.LINE_AA)
    rot = f * 0.04
    for i in range(4):
        aa = rot + i * math.pi / 2
        p1 = (int(fx + math.cos(aa) * fr * 0.78), int(fy + math.sin(aa) * fr * 0.78)); p2 = (int(fx + math.cos(aa) * fr * 1.22), int(fy + math.sin(aa) * fr * 1.22))
        cv2.line(ov, p1, p2, 1.0, 4, cv2.LINE_AA)
    for i in range(24):
        aa = -rot * 0.6 + i * math.pi / 12
        p1 = (int(fx + math.cos(aa) * fr * 1.30), int(fy + math.sin(aa) * fr * 1.30)); p2 = (int(fx + math.cos(aa) * fr * 1.36), int(fy + math.sin(aa) * fr * 1.36))
        cv2.line(ov, p1, p2, 1.0, 2, cv2.LINE_AA)
    blink = 1.0 if (k // 6) % 2 == 0 or s["n"] != "dex_still" else 0.6
    g = cv2.GaussianBlur(ov, (0, 0), 5) * 0.6
    m = np.clip(ov + g, 0, 1)[..., None] * a * blink * 0.95
    out = out * (1 - m) + RED * m
    lab = "TARGET LOCKED" if s["n"] == "dex_still" else "ACQUIRING"
    tm = text_mask(lab, F_MONO, 36, tracking=6)
    lay = shadowed(tm, RED, blur=5, sa=0.6)
    return paste(out, lay, int(fx - lay.shape[1] / 2), int(fy + fr * 1.45 + 10), a * blink)

# ---- lyric typography (song words -> edit time)
def lyric(out, f):
    t = f / FPS
    for txt, s0, s1 in E.LYRICS:
        a0, a1 = E.s2e(s0), E.s2e(s1)
        if txt == "CAN'T GET CAUGHT": a1 = E.T_STOP + 0.30
        if txt == "BLEED IT" and f >= E.fh(E.DROP_HB): continue
        if not (a0 - 0.02 <= t < a1 + 0.12): continue
        k = (t - a0) * FPS; kout = (t - a1) * FPS
        fade = clamp(1 - kout / 7, 0, 1) if kout > 0 else 1.0
        y = 1400
        if txt == "I NEED IT":                                   # letters drop in one by one
            fsz = 150; x = W / 2 - font(F_BLACK, fsz).getlength(txt) / 2
            for j, ch in enumerate(txt):
                cw = font(F_BLACK, fsz).getlength(ch)
                if ch != " ":
                    kk = k - j * 1.3
                    if kk > 0:
                        dy = -120 * (1 - eout(kk / 6, 3)); sc = 1 + 0.5 * math.exp(-kk / 2.5)
                        col = RED if j >= 2 and j <= 5 else WHITE
                        m = text_mask(ch, F_BLACK, int(fsz * sc))
                        lay = shadowed(m, col, blur=10, sa=0.85, stroke=5)
                        out = paste(out, lay, int(x + cw / 2 - lay.shape[1] / 2), int(y + dy - lay.shape[0] / 2), fade * clamp(kk / 2, 0, 1))
                x += cw
        elif txt == "UNDEFEATED":                                # outline that fills left -> right
            m = text_mask(txt, F_BLACK, 150, tracking=-2)
            sw = max(1, int(W * 0.86)); m = cv2.resize(m, (sw, int(m.shape[0] * sw / m.shape[1])), interpolation=cv2.INTER_AREA)
            ol = np.clip(cv2.dilate(m, np.ones((7, 7), np.uint8)) - cv2.erode(m, np.ones((3, 3), np.uint8)), 0, 1)
            fill = np.zeros_like(m); p = eout(k / ((a1 - a0) * FPS * 0.9), 2)
            fill[:, :int(m.shape[1] * p)] = m[:, :int(m.shape[1] * p)]
            lay = shadowed(np.maximum(ol, 0), WHITE, blur=10, sa=0.7)
            fl = shadowed(fill, WHITE, blur=2, sa=0.0)
            sc = 1 + 0.06 * (1 - eout(k / 20))
            x0 = int(W / 2 - lay.shape[1] / 2); y0 = int(y - lay.shape[0] / 2)
            out = paste(out, lay, x0, y0, fade * clamp(k / 3, 0, 1)); out = paste(out, fl, x0 + (lay.shape[1] - fl.shape[1]) // 2, y0 + (lay.shape[0] - fl.shape[0]) // 2, fade)
        elif txt == "BLEED IT":                                  # slices snap together, red
            m = text_mask(txt, F_BLACK, 200, tracking=-2)
            lay = shadowed(m, RED, blur=12, sa=0.85, stroke=6)
            n = 5; hh = lay.shape[0] // n; x0 = int(W / 2 - lay.shape[1] / 2); y0 = int(y - lay.shape[0] / 2)
            for i in range(n):
                off = (1 if i % 2 else -1) * 260 * (1 - eout(k / 7, 4)) * (1 + 0.3 * i)
                sl = lay[i * hh:(i + 1) * hh if i < n - 1 else lay.shape[0]]
                out = paste(out, sl, int(x0 + off), y0 + i * hh, fade * clamp(k / 2, 0, 1))
        elif txt == "BULLETS":                                   # impact punch
            sc = 1 + 1.2 * math.exp(-k / 2.0)
            m = text_mask(txt, F_BLACK, int(165 * sc), tracking=-2)
            lay = shadowed(m, WHITE, blur=12, sa=0.85, stroke=7)
            if k < 3: lay = hblur(lay, 40 * (1 - k / 3))
            out = paste(out, lay, int(W / 2 - lay.shape[1] / 2), int(y - lay.shape[0] / 2), fade)
            out = rgb_split(out, 10 * math.exp(-k / 3)) if k < 8 else out
        elif txt == "I CAN'T SEE IT":                            # defocus -> sharp, wide tracking
            tr = int(26 - 18 * eout(k / 18))
            m = text_mask(txt, F_XB, 104, tracking=tr)
            bl = 14 * (1 - eout(k / 10, 2))
            if bl > 0.5: m = cv2.GaussianBlur(m, (0, 0), bl)
            lay = shadowed(m, WHITE, blur=10, sa=0.75)
            out = paste(out, lay, int(W / 2 - lay.shape[1] / 2), int(y - lay.shape[0] / 2), fade * clamp(k / 6, 0, 1))
        elif txt == "CAN'T GET CAUGHT":                          # stacked slams on each word
            words = [("CAN'T", 27.40, WHITE, 170), ("GET", 27.66, WHITE, 170), ("CAUGHT", 27.74, RED, 230)]
            yy = 1180
            for w, ws, col, fsz in words:
                kk = (t - E.s2e(ws)) * FPS
                if kk >= 0:
                    sc = 1 + 0.6 * math.exp(-kk / 2.2)
                    m = text_mask(w, F_BLACK, int(fsz * sc), tracking=-2)
                    lay = shadowed(m, col, blur=10, sa=0.85, stroke=6)
                    if kk < 3: lay = hblur(lay, 30 * (1 - kk / 3))
                    out = paste(out, lay, int(W / 2 - lay.shape[1] / 2), int(yy + fsz * 0.55 - lay.shape[0] / 2), fade)
                yy += int(fsz * 1.02)
    return out

# ---- logo
_LOGO = {}
def logo_img(width):
    if width not in _LOGO:
        im = Image.open(f"{ROOT}/src/voidfx_logo.webp").convert("RGBA"); im = im.crop(im.getbbox())
        h = int(round(im.height * width / im.width))
        _LOGO[width] = np.asarray(im.resize((width, h), Image.LANCZOS))[..., [2, 1, 0, 3]].astype(np.float32) / 255
    return _LOGO[width]

def watermark(out, f):
    if f >= E.fe(E.T_LOGO): return out
    wm = E.WATERMARK; lg = logo_img(wm["width"]).copy()
    sh = np.zeros_like(lg); sh[..., 3] = cv2.GaussianBlur(lg[..., 3], (0, 0), 3) * 0.6
    x0 = (W - lg.shape[1]) // 2; y0 = wm["y"] - lg.shape[0] // 2
    out = paste(out, sh, x0 + 2, y0 + 3, wm["opacity"])
    return paste(out, lg, x0, y0, wm["opacity"])

def render_logo(f, s):
    k = f - s["f0"]; total = s["f1"] - s["f0"]
    out = np.zeros((H, W, 3), np.float32) + 0.012
    lg = logo_img(860); lh, lw = lg.shape[:2]
    x0, y0 = (W - lw) // 2, int(H * 0.47 - lh / 2)
    # scanline reveal: a bright line sweeps down; logo appears behind it
    p = eout(clamp((k - 2) / 18, 0, 1), 2)
    yl = int(lh * p)
    vis = lg.copy(); vis[yl:, :, 3] = 0
    sc = 1 + 0.04 * clamp(k / total, 0, 1)
    if k >= 2:
        g = np.zeros_like(vis); g[..., :3] = 0.85; g[..., 3] = cv2.GaussianBlur(vis[..., 3], (0, 0), 22) * 0.22
        out = paste(out, g, x0, y0)
        out = paste(out, vis, x0, y0)
        if p < 1:
            ly = y0 + yl
            line = np.exp(-((np.arange(H) - ly) / 3.0) ** 2)[:, None, None] * np.exp(-((np.arange(W) - W / 2) / (lw * 0.55)) ** 2)[None, :, None]
            out = np.clip(out + line * np.array([0.9, 0.9, 1.0], np.float32) * 1.2, 0, 1)
    if 22 <= k < 50:                                           # sheen
        u = (k - 22) / 28; xs = np.arange(W)[None, :] + 0.5 * np.arange(H)[:, None]
        pos = x0 - 300 + (lw + 900) * u
        band = np.exp(-((xs - pos) / 70.0) ** 2)[..., None]
        m = np.zeros((H, W, 1), np.float32); m[y0:y0 + lh, x0:x0 + lw, 0] = lg[..., 3]
        out = np.clip(out + band * m * 0.55, 0, 1)
    if k < 8: out = rgb_split(out, 10 * (1 - k / 8))
    if total - k < 8: out = out * clamp((total - k) / 8, 0, 1)
    return out

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
    hi = np.clip(small - 0.62, 0, 1) * 2.2
    hi = cv2.GaussianBlur(hi, (0, 0), 9)
    return np.clip(out + cv2.resize(hi, (W, H), interpolation=cv2.INTER_LINEAR) * amt, 0, 1)

# ============================================================================ frame
def render(f):
    s = shot_at(f); k = f - s["f0"]
    if s.get("kind") == "logo":
        out = render_logo(f, s)
        return (np.clip(out + grain(f, 0.012), 0, 1) * 255 + 0.5).astype(np.uint8)
    fD = E.fh(E.DROP_HB)
    # ---- the drop: muzzle flash, cracks, shatter
    if s["n"] == "barrel" or (s["n"] == "night_walk" and k < 26):
        if s["n"] == "barrel":
            out = render_shot(s, f)
        else:
            flash = render_shot(by_name("barrel"), by_name("barrel")["f1"] - 1, False)
            if "frz" not in _SH:
                fz = sample("dk", 95.64).astype(np.float32) / 255           # the real muzzle-flash frame
                bs = by_name("barrel"); t, u, _ = src_time(bs, bs["f1"] - 1); cx, cy, ch = frame_geom(bs, bs["f1"] - 1, t, u)
                cw = ch * 9 / 16; M = np.float32([[W / cw, 0, -(cx - cw / 2) * W / cw], [0, H / ch, -(cy - ch / 2) * H / ch]])
                _SH["frz"] = np.clip(cv2.warpAffine(grade(fz, bs, bs["f1"] - 1), M, (W, H), flags=cv2.INTER_CUBIC) * 1.25, 0, 1)
            A = _SH["frz"]
            if k < 2:
                out = np.clip(A * (1 + 2.5 * (1 - k / 2)) + (1 - k / 2) * 0.6, 0, 1)
            elif k < 5:
                out = crack_overlay(A, clamp((k - 1) / 2, 0, 1))
            else:
                B = render_shot(s, f)
                shards()
                A2 = crack_overlay(A, 1.0)
                out = shatter(A2, B, k - 5)
                if k - 5 < 3: out = np.clip(out + (1 - (k - 5) / 3) * 0.35, 0, 1)
    else:
        out = render_shot(s, f)
        tin = s.get("tin")
        if tin == "split" and k < 12:
            out = split_slam(last_frame_of(prev_shot(s)), out, k)
        elif tin == "eye":
            pass
        elif tin == "cube" and k < 7:
            A = last_frame_of(prev_shot(s)); u = eout((k + 1) / 7, 2)
            out = cube(A, out, u)
        elif tin == "datamosh" and k < 11:
            out = datamosh(s, f)
        elif tin == "whip":
            out = whip(out, f, s)
        elif tin == "leak":
            out = leak(out, f, s["f0"])
        elif tin == "polaroid":
            out = polaroid(out, f, s)
        elif tin == "zoomblur" and k < 8:
            u = 1 - k / 8; out = radial_blur(out, W / 2, H * 0.42, 1 + 0.5 * u * u, 1 + 0.5 * max(0, u - 0.12) ** 2, 6)
        elif tin == "slide":
            out = slide(out, f, s)
        elif tin in ("flash", "cut_rgb") and k < 6:
            fl = [0.85, 0.45, 0.2, 0.08, 0.0, 0.0][k] if tin == "flash" else [0.35, 0.12, 0.0, 0, 0, 0][k]
            out = np.clip(out * (1 + 1.5 * fl) + fl * 0.4, 0, 1)
            out = rgb_split(out, (22 if tin == "cut_rgb" else 12) * math.exp(-k / 2))
        elif tin == "glitch_in":
            out = glitch(out, f, s["f0"])
        elif tin == "flash_soft" and k < 6:
            out = np.clip(out + [0.5, 0.25, 0.1, 0.04, 0, 0][k], 0, 1)
        # outgoing side of transitions that start before the cut
        nxt = SHOTS[SHOTS.index(s) + 1] if SHOTS.index(s) + 1 < len(SHOTS) else None
        if nxt is not None:
            kn = f - nxt["f0"]
            if nxt.get("tin") == "eye" and kn >= -7: out = eye_portal(out, f, nxt)
            if nxt.get("tin") == "whip" and kn >= -4: out = whip(out, f, nxt)
            if nxt.get("tin") == "leak" and kn >= -8: out = leak(out, f, nxt["f0"])
            if nxt.get("tin") == "glitch_in" and kn >= -2: out = glitch(out, f, nxt["f0"])
            if nxt.get("tin") == "zoomblur" and kn >= -5:
                u = (kn + 6) / 6; out = radial_blur(out, W / 2, H * 0.42, 1 + 0.5 * (u - 0.17) ** 2, 1 + 0.5 * u * u, 6)
        if tin == "eye": out = eye_portal(out, f, s)
        if s.get("echo"):                                                   # motion echo trails
            acc = out.copy(); wsum = 1.0
            for j, wgt in ((4, 0.30), (8, 0.16), (12, 0.08)):
                if f - j >= s["f0"]:
                    e = render_shot(s, f - j); acc = acc + e * wgt; wsum += wgt
            out = np.clip(acc / wsum * 1.05, 0, 1)
        if s.get("freeze"):
            u = k / max(1, s["f1"] - s["f0"]); L = out.mean(2, keepdims=True)
            out = out + (L - out) * (0.85 * eout(u * 2)); out = out * (1 - 0.25 * eout(u))
    # ---- overlays
    if s.get("tag"): out = name_tag(out, f, s)
    if s.get("stamp"): out = stamp(out, f, s)
    if s.get("reticle"): out = reticle(out, f, s)
    out = lyric(out, f)
    out = caption(out, f)
    if s.get("look") == "cine" or s["n"] in ("night_walk",): out = bloom(out, 0.22)
    out = out * VIG + grain(f, 0.020 if s.get("look") == "night" else 0.014)
    out = watermark(np.clip(out, 0, 1), f)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)

def init_hits():
    HITS.clear()
    HITS.extend([(E.fh(41), 26, 6.0), (E.fe(E.s2e(18.42)), 14, 4.0), (by_name("attack")["f0"], 16, 4.0), (by_name("fight")["f0"], 18, 4.0),
                 (by_name("fingergun")["f0"], 10, 4.0), (E.fe(E.d2e(0, 18.02)), 12, 4.0), (by_name("doakes_gun")["f0"], 10, 4.0)])

def main():
    mode = sys.argv[1]
    load(); init_hits()
    if mode == "prep":
        prep_tracks(); return
    RAW_TRK.update(json.load(open(f"{ROOT}/v3/work/tracks3.json")))
    if mode == "stills":
        name = sys.argv[2]; frames = [int(a) for a in sys.argv[3:]]; ims = []
        for f in frames:
            im = cv2.resize(render(f), (270, 480), interpolation=cv2.INTER_AREA)
            cv2.putText(im, str(f), (5, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1, cv2.LINE_AA); ims.append(im)
        while len(ims) % 6: ims.append(np.zeros_like(ims[0]))
        cv2.imwrite(f"{ROOT}/v3/frames/{name}.jpg", np.vstack([np.hstack(ims[i:i + 6]) for i in range(0, len(ims), 6)]), [cv2.IMWRITE_JPEG_QUALITY, 88])
        return
    if mode == "full":
        for f in [int(a) for a in sys.argv[2:]]:
            cv2.imwrite(f"{ROOT}/v3/frames/full_{f:04d}.jpg", render(f), [cv2.IMWRITE_JPEG_QUALITY, 92])
        return
    if mode == "video":
        outdir = f"{ROOT}/{sys.argv[2]}"; os.makedirs(outdir, exist_ok=True)
        vf = "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p"
        tags = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-itsoffset", str(-1024 / 48000), "-i", f"{ROOT}/v3/audio/mix_preroll.wav", "-i", f"{ROOT}/v3/audio/mix.wav",
               "-map", "0:v", "-map", "1:a", "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-maxrate", "26M", "-bufsize", "52M",
               "-profile:v", "high", "-level", "4.2", "-g", "120", "-bf", "3", *tags, "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
               "-movflags", "+faststart", f"{outdir}/surprise_doakes_voidfx_9x16.mp4",
               "-map", "0:v", "-map", "2:a", "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "11", "-profile:v", "high", "-level", "5.1",
               *tags, "-c:a", "pcm_s24le", "-ar", "48000", f"{outdir}/surprise_doakes_voidfx_9x16_master.mov"]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        with Pool(4) as pool:
            for i, fr in enumerate(pool.imap(render, range(E.DUR_F), chunksize=4)):
                p.stdin.write(fr.tobytes())
                if i % 150 == 0: print(f"frame {i}/{E.DUR_F}", flush=True)
        p.stdin.close(); p.wait(); print("done", outdir, flush=True)

if __name__ == "__main__":
    main()
