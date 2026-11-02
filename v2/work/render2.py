"""Renderer for THE DARK PASSENGER (voidfx v2). Reads v2/work/edl2.py.

  python3 v2/work/render2.py stills OUTNAME f1 f2 ...     # stills -> v2/frames/OUTNAME.jpg (tiled)
  python3 v2/work/render2.py video OUTDIR [--preview]     # full render (needs v2/audio/mix*.wav)
"""
import os, sys, math, bisect, subprocess
import numpy as np, cv2
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.interpolate import PchipInterpolator

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edl2 as E

W, H, FPS = E.W, E.H, E.FPS
cv2.setNumThreads(1)
FONT_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT_XB = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
FONT_SB = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"
FONT_MONO = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Medium.ttf"
FONT_MONO_B = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf"
RED = np.array([0.10, 0.07, 0.74], np.float32)          # BGR deep blood red
PAPER, INK, MIDINK = 0.93, 0.035, 0.20

# ============================================================================ helpers
def clamp(v, a, b): return a if v < a else (b if v > b else v)
def smooth(u): u = clamp(u, 0.0, 1.0); return u * u * (3 - 2 * u)
def ease_out(u, p=3): u = clamp(u, 0.0, 1.0); return 1 - (1 - u) ** p
def ease_in(u, p=2): u = clamp(u, 0.0, 1.0); return u ** p
def sstep(a, b, x): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

def keys_at(keys, u):
    keys = sorted(keys)
    if u <= keys[0][0]: return keys[0][1]
    for (u0, v0), (u1, v1) in zip(keys, keys[1:]):
        if u <= u1: return v0 + (v1 - v0) * smooth((u - u0) / max(1e-9, u1 - u0))
    return keys[-1][1]

# ============================================================================ clips & time maps
CLIPS = E.CLIPS
for c in CLIPS:
    c["f0"], c["f1"] = E.fe(c["e0"]), E.fe(c["e1"])
STARTS = [c["f0"] for c in CLIPS]
for p in E.PANELS:
    p["f"] = E.fe(p["e"]); p["clip"]["f0"] = p["f"]; p["clip"]["f1"] = E.fe(72)

def tmap_fn(c):
    if "_tm" not in c:
        ks = c["tmap"]
        us = np.array([k[0] for k in ks]); ts = np.array([k[1] for k in ks])
        c["_tm"] = PchipInterpolator(us, ts) if len(ks) > 2 else (lambda u, a=ts[0], b=ts[-1]: a + (b - a) * np.asarray(u))
    return c["_tm"]

def clip_time(c, f):
    """source seconds at output frame f (may be outside clip -> clamped) and speed (src s per out s)."""
    n = max(1, c["f1"] - c["f0"])
    u = clamp((f - c["f0"]) / n, 0.0, 1.0)
    tm = tmap_fn(c)
    t = float(tm(u)); du = 1.0 / n
    t2 = float(tm(clamp(u + du, 0, 1))); t1 = float(tm(clamp(u - du, 0, 1)))
    speed = abs(t2 - t1) / ((min(u + du, 1) - max(u - du, 0)) * n / FPS + 1e-9)
    return t, u, speed

# ============================================================================ source frames
FR, UNIQ = {}, {}

def needed():
    need = {}
    allc = [c for c in CLIPS if "src" in c] + [p["clip"] for p in E.PANELS]
    for c in allc:
        P = E.PACKS[c["src"]]; ts = [k[1] for k in c["tmap"]]
        a = int(math.floor(min(ts) * P["fps"])) - 3; b = int(math.ceil(max(ts) * P["fps"])) + 3
        need.setdefault(c["src"], []).append((max(0, a), b))
    return need

def load():
    for pk, rngs in needed().items():
        P = E.PACKS[pk]; cap = cv2.VideoCapture(P["path"])
        rngs = sorted(rngs); merged = []
        for a, b in rngs:
            if merged and a <= merged[-1][1] + 30: merged[-1][1] = max(merged[-1][1], b)
            else: merged.append([a, b])
        for a, b in merged:
            cap.set(cv2.CAP_PROP_POS_FRAMES, a); prev = None
            for k in range(a, b + 1):
                ok, f = cap.read()
                if not ok: break
                g = cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (160, 90), interpolation=cv2.INTER_AREA).astype(np.float32)
                if prev is None or np.mean(np.abs(g - prev)) > 0.15:      # skip exact duplicate (pulldown) frames
                    FR[(pk, k)] = f
                    UNIQ.setdefault(pk, []).append(k)
                prev = g
        UNIQ[pk] = sorted(set(UNIQ[pk]))
    print("loaded", {k: len(v) for k, v in UNIQ.items()}, flush=True)

_DIS = None
_FLOW = {}
def flow_pair(pk, i0, i1):
    global _DIS
    key = (pk, i0, i1)
    if key not in _FLOW:
        if _DIS is None: _DIS = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
        g0 = cv2.resize(cv2.cvtColor(FR[(pk, i0)], cv2.COLOR_BGR2GRAY), None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        g1 = cv2.resize(cv2.cvtColor(FR[(pk, i1)], cv2.COLOR_BGR2GRAY), None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        F01 = _DIS.calc(g0, g1, None); F10 = _DIS.calc(g1, g0, None)
        h, w = FR[(pk, i0)].shape[:2]
        F01 = cv2.resize(F01, (w, h)) * 2; F10 = cv2.resize(F10, (w, h)) * 2
        if len(_FLOW) > 6: _FLOW.pop(next(iter(_FLOW)))
        _FLOW[key] = (F01, F10)
    return _FLOW[key]

_GRID = {}
def flow_interp(pk, i0, i1, t):
    F01, F10 = flow_pair(pk, i0, i1)
    h, w = F01.shape[:2]
    if (w, h) not in _GRID:
        xs, ys = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32)); _GRID[(w, h)] = (xs, ys)
    xs, ys = _GRID[(w, h)]
    Ft0 = -(1 - t) * t * F01 + t * t * F10
    Ft1 = (1 - t) * (1 - t) * F01 - t * (1 - t) * F10
    a = cv2.remap(FR[(pk, i0)], xs + Ft0[..., 0], ys + Ft0[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    b = cv2.remap(FR[(pk, i1)], xs + Ft1[..., 0], ys + Ft1[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return cv2.addWeighted(a, 1 - t, b, t, 0)

def sample(pk, ts, mode):
    fps = E.PACKS[pk]["fps"]; U = UNIQ[pk]
    kf = ts * fps
    i = bisect.bisect_right(U, kf + 0.3) - 1; i = clamp(i, 0, len(U) - 1)
    if mode == "hold" or i >= len(U) - 1:
        return FR[(pk, U[i])]
    i0, i1 = U[i], U[i + 1]
    a = clamp((kf - i0) / (i1 - i0), 0.0, 1.0)
    if a < 0.04: return FR[(pk, i0)]
    if a > 0.96: return FR[(pk, i1)]
    if mode == "blend": return cv2.addWeighted(FR[(pk, i0)], 1 - a, FR[(pk, i1)], a, 0)
    return flow_interp(pk, i0, i1, a)

def source_frame(c, f):
    t, u, speed = clip_time(c, f)
    pk = c["src"]
    if speed > 1.6:                       # velocity: real motion blur (180-degree shutter over the remap)
        K = int(min(9, max(3, round(speed * 2))))
        span = 0.5 / FPS * speed
        acc = None
        for j in range(K):
            fr = sample(pk, t + (j / (K - 1) - 0.5) * span, "hold").astype(np.float32)
            acc = fr if acc is None else acc + fr
        return (acc / K).astype(np.uint8), u, speed
    return sample(pk, t, c.get("interp", "hold")), u, speed

# ============================================================================ camera
def shake(f):
    dx = dy = 0.0
    for fh, amp, tau in ((E.fe(E.DROP_E), 24, 6.0), (E.fe(41), 12, 5.0), (E.fe(E.BANG_E), 30, 7.0), (E.fe(58), 10, 4.0), (E.fe(56), 8, 4.0)):
        if fh <= f < fh + 6 * tau:
            k = f - fh; env = amp * math.exp(-k / tau)
            dx += env * math.sin(k * 2.1 + 0.3); dy += env * 0.7 * math.sin(k * 2.9 + 1.7)
    return dx, dy

def camera(c, f, u, ow, oh):
    cam = c["cam"]
    cx = cam["c0"][0] + (cam["c1"][0] - cam["c0"][0]) * smooth(u)
    cy = cam["c0"][1] + (cam["c1"][1] - cam["c0"][1]) * smooth(u)
    z = keys_at(cam["zoom"], u); rot = 0.0
    b = c.get("bounce", 0)
    if b:
        k = f - c["f0"]
        z *= 1 + b * math.exp(-k / 4.5)
        sgn = 1 if (CLIPS.index(c) if c in CLIPS else 0) % 2 else -1
        rot = sgn * 1.8 * math.exp(-k / 6.0)
    if E.ORIENT == "v" and c in CLIPS:
        vx = E.VX.get(c["name"])
        if vx: cx = vx[0] + (vx[1] - vx[0]) * smooth(u)
        z = 1 + (z - 1) * 0.45
    if c.get("look") == "mono" and f < E.fe(E.DROP_E):                  # intro: camera breathes on each beat
        kb = (f - E.fe(2 * math.floor(f / (2 * E.E * FPS)))) 
        z *= 1 + 0.014 * math.exp(-max(0, kb) / 6.0)
    if c["name"] == "eyes_up" and f >= E.fe(30):                       # pre-drop push accelerates
        z *= 1 + 0.10 * ease_in((f - E.fe(30)) / (E.fe(32) - E.fe(30)), 2)
    return cx, cy, z, rot

def warp(img, pk, cx, cy, z, rot, ow, oh, sdx=0.0, sdy=0.0):
    sw, sh = E.PACKS[pk]["w"], E.PACKS[pk]["h"]
    s = max(ow / sw, oh / sh) * z * (1 + 0.02 * abs(rot) / 2)
    hw, hh = ow / (2 * s), oh / (2 * s)
    cx = clamp(cx, hw, sw - hw); cy = clamp(cy, hh, sh - hh)
    th = math.radians(rot); co, si = math.cos(th) / s, math.sin(th) / s
    M = np.float32([[co, -si, cx - co * (ow / 2 + sdx) + si * (oh / 2 + sdy)],
                    [si, co, cy - si * (ow / 2 + sdx) - co * (oh / 2 + sdy)]])
    return cv2.warpAffine(img, M, (ow, oh), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)

# ============================================================================ looks
CLAHE = cv2.createCLAHE(clipLimit=1.6, tileGridSize=(6, 6))
_SCREEN, _TEX = {}, {}
def screen(ow, oh, period=8.5):
    k = (ow, oh)
    if k not in _SCREEN:
        y, x = np.mgrid[0:oh, 0:ow].astype(np.float32)
        u = (x + y) / math.sqrt(2); v = (x - y) / math.sqrt(2)
        _SCREEN[k] = (0.5 + 0.25 * (np.cos(2 * np.pi * u / period) + np.cos(2 * np.pi * v / period))).astype(np.float32)
    return _SCREEN[k]

def newsprint(ow, oh):
    """procedural newspaper texture (luminance 0..1, 1 = paper)."""
    k = (ow, oh)
    if k not in _TEX:
        im = Image.new("L", (1920, 1080), 255); d = ImageDraw.Draw(im)
        rng = np.random.default_rng(3)
        fh = ImageFont.truetype(FONT_BLACK, 120); fb = ImageFont.truetype(FONT_SB, 22)
        d.text((60, 40), "BAY HARBOR BUTCHER", font=fh, fill=40)
        d.text((60, 175), "BODIES FOUND IN BAY  —  POLICE SEEK SERIAL KILLER", font=ImageFont.truetype(FONT_XB, 46), fill=60)
        words = "the of and to in police said victims miami bay harbor found investigation case evidence night body killer " \
                "detective department metro suspect scene blood witnesses search linked missing"
        words = words.split()
        for col in range(5):
            x0 = 60 + col * 370
            y = 260
            while y < 1060:
                line = " ".join(rng.choice(words) for _ in range(9))
                d.text((x0, y), line[:34], font=fb, fill=90); y += 30
        im = im.rotate(-6, resample=Image.BICUBIC, fillcolor=255)
        t = np.asarray(im).astype(np.float32) / 255
        _TEX[k] = cv2.resize(t, (ow, oh), interpolation=cv2.INTER_AREA)
    return _TEX[k]

def look_mono(img8, f):
    g = cv2.cvtColor(img8, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    g = np.clip((g - 0.04) / 0.90, 0, 1)
    g = g + (g * g * (3 - 2 * g) - g) * 0.85                              # S-curve
    out = np.repeat(g[..., None], 3, axis=2)
    out = out * np.array([1.02, 1.0, 0.975], np.float32) + (1 - g[..., None]) * np.array([0.012, 0.004, -0.004], np.float32)
    return np.clip(out, 0, 1)

def look_ink(img8, prm, f):
    oh, ow = img8.shape[:2]
    p = dict(t1=0.22, t2=0.55, gain=1.0, gamma=1.0, tex=0.0, lines=1.0, red=True)
    p.update(prm or {})
    gray = CLAHE.apply(cv2.cvtColor(img8, cv2.COLOR_BGR2GRAY))
    g = gray.astype(np.float32) / 255
    g = np.clip(g * p["gain"], 0, 1) ** p["gamma"]
    if p.get("flat", 0):                                                   # simplify busy textures (edge-preserving, half res)
        sm = cv2.resize(g, (ow // 2, oh // 2), interpolation=cv2.INTER_AREA)
        for _ in range(2):
            sm = cv2.bilateralFilter(sm, 9, p.get("flat_c", 0.10), p["flat"])
        g = cv2.resize(sm, (ow, oh), interpolation=cv2.INTER_LINEAR)
    gs = cv2.GaussianBlur(g, (0, 0), p.get("soft", 1.5))
    a = cv2.GaussianBlur(gs, (0, 0), 1.3); b = cv2.GaussianBlur(gs, (0, 0), 1.3 * 1.6)
    D = a - 0.985 * b
    lines = sstep(-0.020, -0.004, D)                                       # 0 on ink lines
    blk = sstep(p["t1"] - 0.025, p["t1"] + 0.025, gs)
    wht = sstep(p["t2"] - 0.025, p["t2"] + 0.025, gs)
    v = np.clip((gs - p["t1"]) / (p["t2"] - p["t1"]), 0, 1)
    ht = sstep(-0.10, 0.10, v - screen(ow, oh))
    mid = MIDINK + (PAPER - MIDINK) * ht
    val = INK * (1 - blk) + blk * (mid * (1 - wht) + PAPER * wht)
    val = val * (1 - p["lines"] * 0.82 * (1 - lines))
    if p["tex"] > 0:
        val = val * (1 - p["tex"] * (1 - newsprint(ow, oh)) * wht)
    out = np.repeat(val[..., None], 3, axis=2) * np.array([0.985, 1.0, 1.01], np.float32)
    if p["red"]:
        bf = img8.astype(np.float32)
        b_, g_, r_ = bf[..., 0], bf[..., 1], bf[..., 2]
        ratio_g = r_ / (g_ + 6); ratio_b = r_ / (b_ + 6)
        rg = p.get("red_rg", 2.35)
        m = sstep(rg - 0.22, rg, ratio_g) * sstep(2.3, 2.75, ratio_b) * sstep(55, 95, r_)   # blood (r/g>2), not skin (<1.75)
        m = cv2.GaussianBlur(m, (0, 0), 1.2)
        if m.max() > 0.05:
            out = out * (1 - m[..., None]) + m[..., None] * RED * (0.80 + 0.25 * val[..., None])
    return out

# ============================================================================ post / overlays
_GRAIN = None
def grain(f, amt):
    global _GRAIN
    if _GRAIN is None:
        rng = np.random.default_rng(11)
        _GRAIN = [cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), 0.7) for _ in range(6)]
    g = _GRAIN[f % 6]
    return np.roll(g, (f * 37) % 200, axis=(f % 2))[..., None] * amt

_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.sqrt(((_xx - W / 2) / (W / 2)) ** 2 + ((_yy - H / 2) / (H / 2)) ** 2)
VIG = (1 - 0.22 * np.clip(_r / 1.35, 0, 1) ** 2.2)[..., None].astype(np.float32)
del _yy, _xx, _r

def rgb_split(out, d):
    d = int(round(d))
    if d == 0: return out
    o = out.copy()
    o[..., 2] = np.roll(out[..., 2], d, axis=1); o[..., 0] = np.roll(out[..., 0], -d, axis=1)
    return o

def hblur(img, L):
    L = int(L)
    if L < 3: return img
    k = np.ones((1, L), np.float32) / L
    return cv2.filter2D(img, -1, k, borderType=cv2.BORDER_REFLECT)

_FONTS = {}
def font(p, s):
    if (p, s) not in _FONTS: _FONTS[(p, s)] = ImageFont.truetype(p, s)
    return _FONTS[(p, s)]

def paste_rgba(out, rgba, x0, y0, alpha=1.0):
    a = rgba.astype(np.float32) / 255.0 if rgba.dtype == np.uint8 else rgba
    h, w = a.shape[:2]
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(out.shape[1], x0 + w), min(out.shape[0], y0 + h)
    if xb <= xa or yb <= ya: return out
    s = a[ya - y0:yb - y0, xa - x0:xb - x0]
    al = s[..., 3:4] * alpha
    out[ya:yb, xa:xb] = out[ya:yb, xa:xb] * (1 - al) + s[..., :3] * al
    return out

def text_rgba(text, path, size, fill=(255, 255, 255), stroke=0, stroke_fill=(0, 0, 0), tracking=0, shadow=0):
    fnt = font(path, size)
    wdt = int(sum(fnt.getlength(ch) + tracking for ch in text)) + 4 * stroke + 2 * shadow + 20
    hgt = int(size * 1.35) + 4 * stroke + 2 * shadow + 10
    im = Image.new("RGBA", (wdt, hgt), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x = 2 * stroke + shadow + 10
    for ch in text:
        d.text((x, 2 * stroke + shadow), ch, font=fnt, fill=fill + (255,), stroke_width=stroke, stroke_fill=stroke_fill + (255,))
        x += fnt.getlength(ch) + tracking
    arr = np.asarray(im)[..., [2, 1, 0, 3]].copy()                      # to BGRA
    if shadow:
        al = arr[..., 3].astype(np.float32)
        sh = cv2.GaussianBlur(al, (0, 0), shadow) * 0.7
        base = np.zeros_like(arr); base[..., 3] = np.clip(sh, 0, 255).astype(np.uint8)
        a1 = arr[..., 3:4].astype(np.float32) / 255
        comb = base.astype(np.float32); comb[..., :3] = arr[..., :3] * a1
        comb[..., 3] = 255 * (a1[..., 0] + (1 - a1[..., 0]) * base[..., 3] / 255)
        comb[..., :3] = np.where(comb[..., 3:4] > 0, comb[..., :3] * 255 / np.maximum(comb[..., 3:4], 1), 0)
        arr = np.clip(comb, 0, 255).astype(np.uint8)
    return arr

# ---- logo
_LOGO = {}
def logo(width):
    if width not in _LOGO:
        im = Image.open(f"{E.ROOT}/src/voidfx_logo.webp").convert("RGBA")
        bbox = im.getbbox(); im = im.crop(bbox)
        h = int(round(im.height * width / im.width))
        arr = np.asarray(im.resize((width, h), Image.LANCZOS))[..., [2, 1, 0, 3]].copy()
        _LOGO[width] = arr
    return _LOGO[width]

def draw_watermark(out, f):
    if f >= E.fe(E.BANG_E): return out
    wm = E.WATERMARK; lg = logo(wm["width"]).astype(np.float32) / 255
    al = lg[..., 3]
    sh = cv2.GaussianBlur(al, (0, 0), 3) * 0.6
    x0 = W - wm["margin"][0] - lg.shape[1]; y0 = H - wm["margin"][1] - lg.shape[0]
    shadow = np.zeros_like(lg); shadow[..., 3] = sh
    out = paste_rgba(out, shadow, x0 + 2, y0 + 3, wm["opacity"])
    return paste_rgba(out, lg, x0, y0, wm["opacity"])

# ---- name card (intro)
def draw_namecard(out, f):
    nc = E.NAME_CARD; f_in, f_out = E.fe(nc["e_in"]), E.fe(nc["e_out"])
    if not (f_in <= f < f_out + 10): return out
    n1 = min(len(nc["line1"]), max(0, (f - f_in) // 2))
    f2 = E.fe(nc["e_in"] + 3)
    n2 = min(len(nc["line2"]), max(0, int((f - f2) / 1.2)))
    cursor = "▌" if (f // 8) % 2 == 0 else " "
    l1 = nc["line1"][:n1] + (cursor if n1 < len(nc["line1"]) else "")
    l2 = nc["line2"][:n2] + (cursor if 0 < n2 < len(nc["line2"]) or (f >= f2 and n2 == 0) else "")
    a = 1.0
    k = f - f_out
    lay1 = text_rgba(l1, FONT_SB, 60, tracking=7, shadow=4) if l1.strip() else None
    lay2 = text_rgba(l2, FONT_MONO, 29 if E.ORIENT == "h" else 23, fill=(215, 215, 215), tracking=3 if E.ORIENT == "h" else 2, shadow=3) if l2.strip() else None
    x0, y1, y2 = E.LAYOUT["namecard"]
    if k >= 0:                                                            # glitch out
        a = clamp(1 - k / 10, 0, 1)
        x0 += int((k % 3 - 1) * 26 * (k / 10 + 0.3))
    bar_h = int(96 * ease_out((f - f_in) / 12))
    out[y1 + 6:y1 + 6 + bar_h, x0 - 26:x0 - 21] = out[y1 + 6:y1 + 6 + bar_h, x0 - 26:x0 - 21] * (1 - 0.9 * a) + 0.95 * a
    if lay1 is not None: out = paste_rgba(out, lay1, x0 - 10, y1, a)
    if lay2 is not None: out = paste_rgba(out, lay2, x0 - 7, y2, a)
    return out

# ---- liquid blood shading (gloss + bevel + edge darkening) for any mask
def liquid(mask, sigma=5.0, spec=0.6, lift=0.0):
    b = cv2.GaussianBlur(mask, (0, 0), sigma)
    gx = cv2.Sobel(b, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(b, cv2.CV_32F, 0, 1, ksize=3)
    d = -(gx * -0.45 + gy * -0.85) * (sigma * 1.6)            # light from upper-left
    shade = np.clip(0.74 + 1.6 * d, 0.42, 1.18) + lift
    sp = np.clip(d * 5.0 - 0.55, 0, 1) ** 4.0 * spec
    inner = cv2.GaussianBlur(cv2.erode(mask, np.ones((5, 5), np.uint8)), (0, 0), sigma * 0.8)
    shade = shade * (0.70 + 0.30 * inner)
    col = RED[None, None, :] * shade[..., None] + sp[..., None] * np.array([0.78, 0.80, 0.95], np.float32)
    return np.clip(col, 0, 1)

def make_drips(al, n, seed, lmin=30, lmax=220, wmin=5, wmax=13):
    rng = np.random.default_rng(seed)
    cols = np.where((al > 200).any(0))[0]
    bottoms = {x: np.max(np.where(al[:, x] > 200)[0]) for x in cols}
    out = []
    for x in sorted(rng.choice(cols, n, replace=False)):
        out.append(dict(x=int(x), y=int(bottoms[x]) - 6, w=int(rng.integers(wmin, wmax)), L=int(rng.integers(lmin, lmax)),
                        d=float(rng.uniform(0, 14)), dur=float(rng.uniform(26, 60)), drop=bool(rng.random() < 0.3)))
    return out

def draw_drips(m, drips, k, speed=1.0, extra=0.0):
    """grow drips (neck + bulb) on uint8 mask m; detached droplets fall with gravity."""
    for d in drips:
        L = int(d["L"] * (ease_out((k * speed - d["d"]) / d["dur"], 2) + extra))
        if L > 2:
            x, y, w = d["x"], d["y"], d["w"]
            neck = max(2, int(w * 0.75))
            cv2.line(m, (x, y), (x, y + L), 255, neck, cv2.LINE_AA)
            cv2.circle(m, (x, y + L), int(w * 0.8) + 1, 255, -1, cv2.LINE_AA)
            cv2.circle(m, (x, y + 2), int(w * 1.1), 255, -1, cv2.LINE_AA)
            tf = k * speed - (d["d"] + d["dur"] * 0.8)
            if d["drop"] and tf > 0:                                   # a droplet breaks off and falls
                yy = int(y + L + 14 + 0.9 * tf * tf)
                if yy < m.shape[0] - 10: cv2.ellipse(m, (x, yy), (int(w * 0.6) + 1, int(w * 0.9) + 1), 0, 0, 360, 255, -1, cv2.LINE_AA)
    return m

_TITLE = {}
def title_base():
    if "base" not in _TITLE:
        lay = text_rgba(E.TITLE["text"], FONT_BLACK, 250, tracking=16)
        al = lay[..., 3]; hgt, wdt = al.shape; pad = 700
        mask = np.zeros((hgt + pad, wdt), np.uint8); mask[:hgt] = al
        _TITLE.update(base=mask, drips=make_drips(al, 22, 5), w=wdt, h=hgt + pad, th=hgt)
    return _TITLE

def title_rgba(k, f):
    T = title_base(); m = T["base"].copy()
    surge = 0.0
    f_pour = E.fe(30.6)
    if f >= f_pour:                                                     # drips surge as the blood starts to pour
        surge = 1.6 * ease_in((f - f_pour) / (E.fe(32) - f_pour), 1.5)
    m = draw_drips(m, T["drips"], k, 1.0, surge)
    a = m.astype(np.float32) / 255
    col = liquid(a, 4.0, 0.7)
    return np.dstack([col, a])

def draw_title(out, f):
    f_in, f_drop = E.fe(E.TITLE["e_in"]), E.fe(E.TITLE["e_drop"])
    if not (f_in <= f < f_drop): return out
    k = f - f_in
    cx, cy, tsc = E.LAYOUT["title"]
    rgba = title_rgba(k, f)
    sc = tsc * (1 + 0.28 * math.exp(-k / 3.0))
    rgba = cv2.resize(rgba, (int(rgba.shape[1] * sc), int(rgba.shape[0] * sc)), interpolation=cv2.INTER_AREA if sc < 1 else cv2.INTER_LINEAR)
    jx = jy = 0
    f30 = E.fe(30)
    if f >= f30:
        amp = 9 * ease_in((f - f30) / (f_drop - f30), 2)
        jx, jy = amp * math.sin(f * 2.7), amp * 0.6 * math.sin(f * 3.9)
    x0 = int(cx - rgba.shape[1] / 2 + jx); y0 = int(cy - _TITLE["th"] * sc / 2 + jy)
    a = clamp(k / 2, 0, 1)
    sh = np.zeros_like(rgba); sh[..., 3] = cv2.GaussianBlur(rgba[..., 3], (0, 0), 9) * 0.75
    out = paste_rgba(out, sh, x0 + int(10 * sc), y0 + int(14 * sc), a)              # soft drop shadow
    glow = np.zeros_like(rgba); glow[..., :3] = RED; glow[..., 3] = cv2.GaussianBlur(rgba[..., 3], (0, 0), 26) * 0.35
    out = paste_rgba(out, glow, x0, y0, a)
    out = paste_rgba(out, rgba, x0, y0, a)
    if f >= f30:
        out = rgb_split(out, 5 * ease_in((f - f30) / (f_drop - f30), 2))
    return out

# ---- the blood curtain: pours down over everything, then falls away to reveal the drop
_CUR = {}
def curtain_params():
    if not _CUR:
        rng = np.random.default_rng(77); N = 30 if E.ORIENT == "h" else 18
        st = []
        for i in range(N):
            st.append(dict(x=(i + 0.5) * W / N + rng.uniform(-0.3, 0.3) * W / N, w=W / N * rng.uniform(0.7, 1.4),
                           d=rng.uniform(0, 0.38), sp=rng.uniform(0.95, 1.3)))
        xs = np.arange(W, dtype=np.float32); tg = np.zeros(W, np.float32)
        for _ in range(16 if E.ORIENT == "h" else 10):
            xj = rng.uniform(0, W); wj = rng.uniform(14, 46); Lj = rng.uniform(60, 240)
            tg = np.maximum(tg, Lj * np.sqrt(np.clip(1 - ((xs - xj) / wj) ** 2, 0, 1)))
        _CUR.update(st=st, tongue=tg, xs=xs)
    return _CUR

def draw_blood(out, f):
    fp0, fd = E.fe(30.6), E.fe(32)
    if not (fp0 <= f < fd + 18): return out
    C = curtain_params()
    if f < fd:
        u = (f - fp0) / (fd - fp0)
        m = np.zeros((H // 2, W // 2), np.uint8)
        for s_ in C["st"]:
            v = clamp((u - s_["d"]) / (1 - s_["d"]), 0, 1)
            front = (H + 160) * ease_in(v, 1.5) * s_["sp"] / 2
            wd = s_["w"] * (0.30 + 1.35 * ease_in(v, 2.2)) / 2
            if front > 1:
                x = s_["x"] / 2
                cv2.rectangle(m, (int(x - wd / 2), 0), (int(x + wd / 2), int(front)), 255, -1)
                cv2.circle(m, (int(x), int(front)), int(wd * 0.62) + 1, 255, -1, cv2.LINE_AA)
        mask = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255
        if u > 0.86: mask = np.maximum(mask, (u - 0.86) / 0.14)
    else:
        k = f - fd; v = k / 17.0
        ytop = (H + 320) * ease_in(v, 2.0) - C["tongue"] * (1 - 0.4 * v) - 16 * np.sin(C["xs"] / 85 + k * 0.4)
        yy = np.arange(H, dtype=np.float32)[:, None]
        mask = np.clip((yy - ytop[None, :]) / 2.0, 0, 1)
    mask = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.0)
    col = liquid(mask, 7.0, 0.45)
    if "streak" not in _CUR:                                              # vertical flow streaks + depth gradient
        rng = np.random.default_rng(5)
        n1 = cv2.resize(rng.standard_normal((6, W // 6)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        n2 = cv2.resize(rng.standard_normal((24, W // 3)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        _CUR["streak"] = (0.06 * n1 + 0.03 * n2)
        _CUR["grad"] = np.linspace(1.04, 0.72, H, dtype=np.float32)[:, None]
    off = int((f - E.fe(30.6)) * 9) % H
    tex = 1 + np.roll(_CUR["streak"], off, axis=0)
    col = np.clip(col * (tex * _CUR["grad"])[..., None], 0, 1)
    hl = np.clip(np.roll(_CUR["streak"], off, axis=0) * 6 - 0.32, 0, 1) ** 2 * 0.10      # glossy sheen bands
    col = np.clip(col + hl[..., None] * np.array([0.6, 0.6, 0.8], np.float32), 0, 1)
    return out * (1 - mask[..., None]) + col * mask[..., None]

# ---- TONIGHT'S THE NIGHT: extruded comic lettering that builds up, then blasts out
_WORD = {}
def word_art(w, size):
    if (w, size) in _WORD: return _WORD[(w, size)]
    fnt = font(FONT_BLACK, size)
    tw = int(fnt.getlength(w) + 4 * len(w)) + 160; th = int(size * 1.4) + 160
    def mask(stroke, dx=0, dy=0):
        im = Image.new("L", (tw, th), 0); d = ImageDraw.Draw(im); x = 60 + dx
        for ch in w:
            d.text((x, 50 + dy), ch, font=fnt, fill=255, stroke_width=stroke, stroke_fill=255); x += fnt.getlength(ch) + 4
        return np.asarray(im).astype(np.float32) / 255
    fill = mask(0); s7 = mask(7); s16 = mask(16)
    ext = np.zeros_like(fill)
    for d_ in range(1, 15): ext = np.maximum(ext, np.roll(np.roll(s7, d_, 0), d_, 1))
    hs = np.roll(np.roll(s16, 30, 0), 26, 1)
    yy, xx = np.mgrid[0:th, 0:tw].astype(np.float32)
    dots = (0.5 + 0.25 * (np.cos(2 * np.pi * (xx + yy) / 1.414 / 9) + np.cos(2 * np.pi * (xx - yy) / 1.414 / 9))) > 0.5
    art = dict(fill=fill, s7=s7, s16=s16, ext=ext, hs=hs * dots, w=tw, h=th)
    if w == "NIGHT": art["drips"] = make_drips((fill * 255).astype(np.uint8), 9, 12, 20, 120, 6, 12)
    _WORD[(w, size)] = art
    return art

def word_rgba(w, size, k):
    A = word_art(w, size); th, tw = A["h"], A["w"]
    col = np.zeros((th, tw, 3), np.float32); al = np.zeros((th, tw), np.float32)
    def lay(m, c, a=1.0):
        nonlocal col, al
        m = m * a; col = col * (1 - m[..., None]) + np.array(c, np.float32) * m[..., None]; al = np.maximum(al, m)
    lay(A["hs"], (0.02, 0.02, 0.02), 0.9)                                 # halftone drop shadow
    lay(A["s16"], (0.97, 0.97, 0.96))                                     # sticker outline
    lay(A["ext"], (0.05, 0.05, 0.07) if w != "NIGHT" else (0.04, 0.03, 0.20))   # 3D extrusion
    lay(A["s7"], (0.02, 0.02, 0.02))                                      # ink stroke
    if w == "NIGHT":
        m = (A["fill"] * 255).astype(np.uint8); m = draw_drips(m, A["drips"], k, 1.6)
        mf = m.astype(np.float32) / 255
        face = liquid(mf, 3.0, 0.8, 0.08)
        col = col * (1 - mf[..., None]) + face * mf[..., None]; al = np.maximum(al, mf)
    else:
        g = np.linspace(1.0, 0.80, th, dtype=np.float32)[:, None, None] * np.array([0.97, 0.97, 0.95], np.float32)
        col = col * (1 - A["fill"][..., None]) + g * A["fill"][..., None]
        hl = np.clip(A["fill"] - np.roll(A["fill"], 5, 0), 0, 1)      # top-edge highlight
        col = np.clip(col + hl[..., None] * 0.04, 0, 1)
    return np.dstack([col, al])

def starburst(out, cx, cy, R, k, seed):
    if k >= 6: return out
    rng = np.random.default_rng(seed); n = 18
    ang = np.linspace(0, 2 * np.pi, 2 * n, endpoint=False) + rng.uniform(0, 0.3)
    rr = np.where(np.arange(2 * n) % 2 == 0, 1.0, 0.58) * R * (0.85 + 0.35 * ease_out(k / 4)) * rng.uniform(0.9, 1.1, 2 * n)
    pts = np.stack([cx + rr * np.cos(ang), cy + rr * 0.62 * np.sin(ang)], 1).astype(np.int32)
    m = np.zeros((H, W), np.uint8); cv2.fillPoly(m, [pts], 255, cv2.LINE_AA)
    a = (1 - k / 6) * 0.9
    mm = m.astype(np.float32)[..., None] / 255 * a
    edge = cv2.morphologyEx(m, cv2.MORPH_GRADIENT, np.ones((7, 7), np.uint8)).astype(np.float32)[..., None] / 255 * a
    return (out * (1 - mm) + 0.95 * mm) * (1 - edge) + 0.02 * edge

def draw_words(out, f):
    ws = E.WORDS; fend = E.fe(52); fexit = E.fe(51.45)
    for i, (w, e) in enumerate(ws):
        fw = E.fe(e)
        if not (fw <= f < fend): continue
        k = f - fw
        cx, cy, size = E.LAYOUT["words"][w]
        if k < 6: out = starburst(out, cx, cy, size * (2.3 if len(w) > 3 else 1.5), k, 40 + i)
    for i, (w, e) in enumerate(ws):
        fw = E.fe(e)
        if not (fw <= f < fend): continue
        k = f - fw
        cx, cy, size = E.LAYOUT["words"][w]
        lay = word_rgba(w, size, k)
        sc = 1 + 0.42 * math.exp(-k / 2.3)
        a = clamp(k / 1.5 + 0.34, 0, 1)
        if f >= fexit:                                                    # blast out toward the camera
            v = (f - fexit) / (fend - fexit); sc *= 1 + 0.9 * ease_in(v, 2); a *= 1 - ease_in(v, 1.5)
        jx = jy = 0.0
        for j, (w2, e2) in enumerate(ws):                                 # knock when a later word lands
            if j > i and f >= E.fe(e2):
                kk = f - E.fe(e2); jx += 14 * math.exp(-kk / 3) * math.sin(kk * 2.3); jy += 9 * math.exp(-kk / 3) * math.cos(kk * 3.1)
        if abs(sc - 1) > 0.002:
            lay = cv2.resize(lay, (int(lay.shape[1] * sc), int(lay.shape[0] * sc)), interpolation=cv2.INTER_LINEAR)
        if k < 4: lay = hblur(lay, 30 * (1 - k / 4))
        rot = [-5.0, 3.0, -2.0][i] + 1.5 * math.exp(-k / 5)
        M = cv2.getRotationMatrix2D((lay.shape[1] / 2, lay.shape[0] / 2), rot, 1.0)
        lay = cv2.warpAffine(lay, M, (lay.shape[1], lay.shape[0]), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
        out = paste_rgba(out, lay, int(cx - lay.shape[1] / 2 + jx), int(cy - lay.shape[0] / 2 + jy), a)
    return out

# ---- comic speed lines
def speed_lines(out, f, strength):
    if strength <= 0.02: return out
    rng = np.random.default_rng(f * 7 + 3)
    m = np.zeros((H // 2, W // 2), np.uint8)
    cx, cy = W / 4, H / 4; R = math.hypot(W / 4, H / 4) * 1.1
    for _ in range(90):
        a = rng.uniform(0, 2 * math.pi); r0 = R * rng.uniform(0.36, 0.72); wdt = rng.uniform(0.005, 0.022)
        p0 = (cx + r0 * math.cos(a), cy + r0 * math.sin(a))
        p1 = (cx + R * math.cos(a - wdt), cy + R * math.sin(a - wdt)); p2 = (cx + R * math.cos(a + wdt), cy + R * math.sin(a + wdt))
        cv2.fillPoly(m, [np.array([p0, p1, p2], np.int32)], 255, cv2.LINE_AA)
    mm = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32)[..., None] / 255 * strength
    return out * (1 - mm) + (1 - out) * mm            # streaks always contrast with what is under them

# ---- blood splatter bursts
_SPL = {}
def splat_rgba(size, seed):
    k = (size, seed)
    if k not in _SPL:
        rng = np.random.default_rng(seed * 31 + 7); S = size * 2
        m = np.zeros((S * 2, S * 2), np.uint8); c = S
        for _ in range(14):                                               # main body
            r = int(size * rng.uniform(0.18, 0.34)); d = size * rng.uniform(0, 0.16); a = rng.uniform(0, 6.28)
            cv2.circle(m, (int(c + d * math.cos(a)), int(c + d * math.sin(a))), r, 255, -1, cv2.LINE_AA)
        for _ in range(26):                                               # arms / streaks
            a = rng.uniform(0, 6.28); L = size * rng.uniform(0.35, 0.95); w = int(size * rng.uniform(0.02, 0.06))
            p1 = (int(c + L * math.cos(a)), int(c + L * math.sin(a)))
            cv2.line(m, (c, c), p1, 255, max(2, w), cv2.LINE_AA)
            cv2.circle(m, p1, int(w * rng.uniform(0.8, 1.6)), 255, -1, cv2.LINE_AA)
        for _ in range(70):                                               # droplets
            a = rng.uniform(0, 6.28); L = size * rng.uniform(0.4, 1.4) ** 1.0; r = max(2, int(size * rng.uniform(0.006, 0.03)))
            cv2.circle(m, (int(c + L * math.cos(a)), int(c + L * math.sin(a))), r, 255, -1, cv2.LINE_AA)
        m = cv2.resize(m, (S, S), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
        er = cv2.GaussianBlur(cv2.erode((m * 255).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(np.float32) / 255, (0, 0), 4)
        shade = 0.75 + 0.35 * er
        rgba = np.dstack([RED[0] * shade, RED[1] * shade, RED[2] * shade, m]).astype(np.float32)
        _SPL[k] = rgba
    return _SPL[k]

def draw_splats(out, f):
    for e, x, y, size, seed, life in E.SPLATS:
        f0 = E.fe(e); f1 = E.fe(e + life)
        if not (f0 <= f < f1): continue
        k = f - f0
        rgba = splat_rgba(size, seed)
        sc = 0.55 + 0.45 * ease_out(k / 3.0, 3)
        if sc < 0.999:
            rgba = cv2.resize(rgba, (int(rgba.shape[1] * sc), int(rgba.shape[0] * sc)), interpolation=cv2.INTER_LINEAR)
        a = clamp((f1 - f) / 8, 0, 1) * 0.92
        out = paste_rgba(out, rgba, int(x - rgba.shape[1] / 2), int(y - rgba.shape[0] / 2), a)
    return out

# ---- zoom-through / spin transitions (motion-blurred camera move across a cut)
def blur_xform(img, z0, z1, r0, r1, n=7):
    acc = None
    for i in range(n):
        t = i / (n - 1); z = z0 + (z1 - z0) * t; r = r0 + (r1 - r0) * t
        M = cv2.getRotationMatrix2D((W / 2, H / 2), r, z)
        w = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        acc = w if acc is None else acc + w
    return acc / n

def transition(out, f):
    for kind, e in E.TRANS:
        fc = E.fe(e); k = f - fc
        if -5 <= k < 7:
            if k < 0:                                   # outgoing accelerates into the cut
                u1 = (k + 6) / 6.0; u0 = u1 - 1 / 6.0; zs, rs = 0.6, 26.0
            else:                                       # incoming decelerates out of it
                u0 = 1 - k / 7.0; u1 = max(0.0, u0 - 1 / 7.0); zs, rs = 0.6, -26.0
            if kind == "zoom":
                return blur_xform(out, 1 + zs * u0 * u0, 1 + zs * u1 * u1, 0, 0)
            return blur_xform(out, 1 + 0.18 * u0 * u0, 1 + 0.18 * u1 * u1, rs * u0 * u0, rs * u1 * u1)
    return out

def transition2(out, f, c):
    for kind, e in E.TRANS2:
        fc = E.fe(e); k = f - fc
        if not (0 <= k < 9): continue
        outc = [x for x in CLIPS if x["f1"] == fc][0]
        A = clip_fx(render_clip(outc, outc["f1"] - 1, extra_shake=False), outc, outc["f1"] - 1)
        if kind == "slices":                                              # comic panel strips slam in, alternating
            n = 5; res = A * 0.55
            span = W if E.ORIENT == "h" else H
            for i in range(n):
                v = ease_out(clamp((k - i * 0.9) / 5.0, 0, 1), 3)
                if v <= 0: continue
                sgn = 1 if i % 2 else -1
                if E.ORIENT == "h":
                    x0, x1 = int(i * W / n), int((i + 1) * W / n); dy = int(sgn * (1 - v) * H)
                    band = np.roll(out[:, x0:x1], dy, axis=0)
                    if dy > 0: band[:dy] = res[:dy, x0:x1]
                    elif dy < 0: band[dy:] = res[dy:, x0:x1]
                    res[:, x0:x1] = band; res[:, max(0, x0 - 3):x0 + 3] = 0.95
                else:
                    y0, y1 = int(i * H / n), int((i + 1) * H / n); dx = int(sgn * (1 - v) * W)
                    band = np.roll(out[y0:y1], dx, axis=1)
                    if dx > 0: band[:, :dx] = res[y0:y1, :dx]
                    elif dx < 0: band[:, dx:] = res[y0:y1, dx:]
                    res[y0:y1] = band; res[max(0, y0 - 3):y0 + 3] = 0.95
            return res
        if kind == "inkbleed":                                            # the next shot bleeds in, darkest ink first
            Lb = cv2.GaussianBlur(out.mean(2), (0, 0), 3)
            thr = 1.12 * ease_out(k / 8.0, 2)
            m = np.clip((thr - Lb) / 0.07, 0, 1)
            edge = np.clip(m * (1 - m) * 4, 0, 1)[..., None]
            return (A * (1 - m[..., None]) + out * m[..., None]) * (1 - 0.85 * edge)
    return out

# ============================================================================ clip render
def render_clip(c, f, ow=W, oh=H, extra_shake=True):
    img, u, speed = source_frame(c, f)
    cx, cy, z, rot = camera(c, f, u, ow, oh)
    sdx, sdy = shake(f) if extra_shake else (0, 0)
    fx = c.get("fx", [])
    if "whip_in" in fx and f - c["f0"] < 7:
        sdx += -(1 - ease_out((f - c["f0"]) / 7, 2)) * 0.30 * ow
    if "whip_out" in fx and c["f1"] - f <= 6:
        sdx += ease_in((6 - (c["f1"] - f)) / 6, 2) * 0.35 * ow
    v = warp(img, c["src"], cx, cy, z, rot, ow, oh, sdx, sdy)
    out = look_mono(v, f) if c.get("look") == "mono" else look_ink(v, c.get("ink"), f)
    # directional blur for whips
    if "whip_in" in fx and f - c["f0"] < 7:
        out = hblur(out, 140 * (1 - (f - c["f0"]) / 7))
    if "whip_out" in fx and c["f1"] - f <= 6:
        out = hblur(out, 6 + 150 * ease_in((6 - (c["f1"] - f)) / 6, 2))
    return out

def clip_fx(out, c, f):
    fx = c.get("fx", []); k = f - c["f0"]
    if "flicker_out" in fx:
        pat = [1, .15, 1, .9, .05, 0, .7, .1, 0, 0, .35, 0] + [0] * 40
        out = out * pat[min(k, len(pat) - 1)]
    if "light_on" in fx and k < 9:
        out = out * [0, 0, .35, .05, .9, .45, 1.15, 1.05, 1.0][k]
    if "predrop_dark" in fx and f >= E.fe(30):
        kk = f - E.fe(30)
        out = out * clamp(1 - kk / 7, 0.0, 1.0)
    if "invert_hit" in fx:
        fm = E.fe(c["e0"] + 1) if c["name"] == "stick_charge" else c["f0"]
        if fm <= f < fm + 2: out = 1 - out
    if "strobe_end" in fx:
        fs = E.fe(78)
        if f >= fs:
            pat = [1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1]
            if pat[min(f - fs, len(pat) - 1)] == 0: out = out * 0.0
    return out

def glitch(out, f, f0, seed=0):
    k = f - f0
    if not (-2 <= k <= 3): return out
    rng = np.random.default_rng(1000 + f + seed)
    o = out.copy(); amp = [0.5, 0.9, 1.0, 0.7, 0.4, 0.2][k + 2]
    for _ in range(9):
        y = int(rng.integers(0, H - 40)); h = int(rng.integers(8, 90)); d = int(rng.integers(-180, 180) * amp)
        o[y:y + h] = np.roll(o[y:y + h], d, axis=1)
    for _ in range(5):
        y = int(rng.integers(0, H - 64)); x = int(rng.integers(0, W - 128))
        y2 = int(rng.integers(0, H - 64)); x2 = int(rng.integers(0, W - 128))
        o[y:y + 64, x:x + 128] = o[y2:y2 + 64, x2:x2 + 128]
    o = rgb_split(o, 14 * amp)
    if k == 0: o = 1 - o
    return o

# ============================================================================ composites
def render_page(c, f):
    page = np.full((H, W, 3), 0.035, np.float32) + (screen(W, H, 14.0) > 0.72)[..., None] * 0.05
    for p in E.PANELS:
        if f < p["f"]: continue
        poly = np.array(p["poly"], np.float32)
        x0, y0 = poly.min(0).astype(int); x1, y1 = poly.max(0).astype(int)
        pw, ph = x1 - x0, y1 - y0
        pc = p["clip"]; pc.setdefault("look", "ink"); pc.setdefault("bounce", 0.06)
        k = f - p["f"]
        img = render_clip(pc, f, pw, ph, extra_shake=False)
        if k < 3: img = img * (1 - [0.85, 0.5, 0.2][k]) + [0.85, 0.5, 0.2][k]
        mask = np.zeros((ph * 2, pw * 2), np.uint8)
        cv2.fillPoly(mask, [((poly - [x0, y0]) * 2).astype(np.int32)], 255)
        mask = cv2.resize(mask, (pw, ph), interpolation=cv2.INTER_AREA).astype(np.float32)[..., None] / 255
        sc = 1 + 0.10 * math.exp(-k / 3.0)
        cxp, cyp = (x0 + x1) / 2, (y0 + y1) / 2
        layer = np.zeros((H, W, 3), np.float32); al = np.zeros((H, W, 1), np.float32)
        layer[y0:y1, x0:x1] = img; al[y0:y1, x0:x1] = mask
        border = np.zeros((H, W), np.uint8)
        cv2.polylines(border, [poly.astype(np.int32)], True, 255, 7, cv2.LINE_AA)
        if abs(sc - 1) > 0.002:
            M = cv2.getRotationMatrix2D((cxp, cyp), 0, sc)
            layer = cv2.warpAffine(layer, M, (W, H)); al = cv2.warpAffine(al, M, (W, H))[..., None]
            border = cv2.warpAffine(border, M, (W, H))
        shd = cv2.GaussianBlur(np.roll(np.roll(al[..., 0], 16, 0), 14, 1), (0, 0), 8)[..., None]
        page = page * (1 - 0.7 * shd)
        page = page * (1 - al) + layer * al
        b = border.astype(np.float32)[..., None] / 255
        page = page * (1 - b) + 0.95 * b
        if p.get("caption") and k >= 4:
            cap = text_rgba(p["caption"], FONT_XB, 34, fill=(10, 10, 10), tracking=4)
            hh, ww = cap.shape[:2]
            bx, by = x0 + 34, y0 + 30
            a = clamp((k - 4) / 4, 0, 1)
            page[by:by + hh + 6, bx:bx + ww + 16] = page[by:by + hh + 6, bx:bx + ww + 16] * (1 - a) + 0.95 * a
            page = paste_rgba(page, cap, bx + 8, by + 6, a)
            cv2.rectangle(page, (bx, by), (bx + ww + 16, by + hh + 6), (0.02, 0.02, 0.02), 3)
    # page camera: slow push, then rush into panel 4
    z = 1 + 0.035 * (f - c["f0"]) / (c["f1"] - c["f0"])
    tx, ty = W / 2, H / 2
    fr = E.fe(70.6)
    if f >= fr:
        u = ease_in((f - fr) / (c["f1"] - fr), 3)
        z *= 1 + 1.6 * u
        rx, ry = E.LAYOUT["rush"]
        tx, ty = W / 2 + (rx - W / 2) * u, H / 2 + (ry - H / 2) * u
    sdx, sdy = shake(f)
    M = np.float32([[z, 0, W / 2 - z * tx + sdx], [0, z, H / 2 - z * ty + sdy]])
    page = cv2.warpAffine(page, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return page

def render_logo(c, f):
    k = f - c["f0"]
    if k < 3:                                                             # BANG: muzzle flash on the last frame
        fg = [x for x in CLIPS if x["name"] == "finger_gun"][0]
        out = render_clip(fg, fg["f1"] - 1)
        return out * (1 - [1.0, 0.8, 0.5][k]) + [1.0, 0.8, 0.5][k]
    out = np.full((H, W, 3), 0.0, np.float32)
    if k < 6: return out
    lg = logo(E.LAYOUT["logo"]).astype(np.float32) / 255
    lh, lw = lg.shape[:2]
    total = c["f1"] - c["f0"]
    sc = 1.0 + 0.045 * clamp((k - 18) / (total - 18), 0, 1)
    if abs(sc - 1) > 0.001:
        lg = cv2.resize(lg, (int(lw * sc), int(lh * sc)), interpolation=cv2.INTER_AREA if sc < 1 else cv2.INTER_LINEAR)
        lh, lw = lg.shape[:2]
    # glint
    if 24 <= k < 54:
        yy, xx = np.mgrid[0:lh, 0:lw].astype(np.float32)
        pos = -300 + (lw + 600) * ((k - 24) / 30)
        band = np.exp(-(((xx + 0.45 * yy) - pos) / 60.0) ** 2)
        lg[..., :3] = np.clip(lg[..., :3] + band[..., None] * 0.55, 0, 1)
    # soft glow behind
    glow = cv2.GaussianBlur(lg[..., 3], (0, 0), 28) * 0.16
    x0, y0 = (W - lw) // 2, (H - lh) // 2 - 10
    gl = np.zeros((lh, lw, 4), np.float32); gl[..., :3] = 0.85; gl[..., 3] = glow
    out = paste_rgba(out, gl, x0, y0)
    N = 6; sh = lh // N
    gout = total - k
    for i in range(N):
        sl = lg[i * sh:(i + 1) * sh if i < N - 1 else lh]
        u = clamp((k - 6 - i * 1.2) / 12, 0, 1)
        if u <= 0: continue
        e_ = ease_out(u, 4)
        dx = (1 if i % 2 else -1) * (1 - e_) * 1150
        vel = abs(dx - (1 if i % 2 else -1) * (1 - ease_out(clamp((k - 7 - i * 1.2) / 12, 0, 1), 4)) * 1150)
        if gout <= 8:
            dx += (1 if (i + gout) % 2 else -1) * (9 - gout) * 22
        s2 = hblur(sl, min(160, vel * 0.8))
        out = paste_rgba(out, s2, int(x0 + dx), y0 + i * sh, min(1.0, u * 3) * (clamp(gout / 8, 0, 1) if gout <= 8 else 1))
    # blood drips run off the logo and a red rule draws in under it
    if False:                                                             # logo drips removed (user request)
        al = (lg[..., 3] * 255).astype(np.uint8)
        if "ldrips" not in _LOGO:
            cols = np.where((al > 200).any(0))[0]; bt = np.array([np.max(np.where(al[:, x] > 200)[0]) for x in cols])
            cand = cols[bt >= np.percentile(bt, 92)]
            picks = [int(cand[len(cand) // 5]), int(cand[(4 * len(cand)) // 5])]
            _LOGO["ldrips"] = [dict(x=x, y=int(np.max(np.where(al[:, x] > 200)[0])) - 4, w=w, L=L, d=0.0, dur=30.0, drop=dr)
                               for x, w, L, dr in zip(picks, (16, 12), (150, 95), (True, False))]
        dm = np.zeros((lh + 240, lw), np.uint8)
        dm = draw_drips(dm, _LOGO["ldrips"], k - 22, 1.0)
        dmf = dm.astype(np.float32) / 255
        dl = np.dstack([liquid(dmf, 3.0, 0.7), dmf])
        out = paste_rgba(out, dl, x0, y0, clamp(gout / 8, 0, 1))
    if False:
        ln = int(lw * ease_out((k - 18) / 14, 3)); yl = y0 + lh + 28
        a = clamp(gout / 8, 0, 1)
        out[yl:yl + 5, x0:x0 + ln] = out[yl:yl + 5, x0:x0 + ln] * (1 - a) + RED * 0.9 * a
    if k < 14: out = rgb_split(out, 10 * (1 - k / 14))
    return out

# ============================================================================ frame
def clip_at(f):
    i = bisect.bisect_right(STARTS, f) - 1
    return CLIPS[i]

FLASH = [("blood_slide", 0.55), ("blood_slide", 0.6), (None, 0), ("hood_up", 0.85), ("hood_up", 0.9), (None, 0),
         ("finger_gun", 0.75), (None, 0)]

def render_flash(f):
    name, u = FLASH[f]
    if name is None:
        return np.zeros((H, W, 3), np.float32)
    c = [x for x in CLIPS if x["name"] == name][0]
    ff = int(c["f0"] + u * (c["f1"] - c["f0"]))
    out = render_clip(c, ff, extra_shake=False)
    out = rgb_split(out, 12 if f % 3 == 0 else 6)
    return glitch(out, 0, 0, seed=f) if f in (0, 4) else out

def render(f):
    c = clip_at(f)
    if f < len(FLASH):                                                    # flash-forward hook
        out = render_flash(f) * VIG
        out[:E.LETTERBOX] = 0; out[H - E.LETTERBOX:] = 0
        return (np.clip(draw_watermark(np.clip(out + grain(f, 0.03), 0, 1), f), 0, 1) * 255 + 0.5).astype(np.uint8)
    if c.get("kind") == "page":
        out = render_page(c, f)
    elif c.get("kind") == "logo":
        out = render_logo(c, f)
    else:
        out = render_clip(c, f)
        out = clip_fx(out, c, f)
        if "speed_lines" in c.get("fx", []):
            u = (f - c["f0"]) / max(1, c["f1"] - c["f0"])
            out = speed_lines(out, f, 0.75 * (1 - smooth(u / 0.7)))
        out = transition(out, f)
        out = transition2(out, f, c)
        # white slab wipe kill_room_knife -> over_victim
        if c["name"] in ("kill_room_knife", "over_victim"):
            fc = E.fe(48); k = f - fc
            if -5 <= k <= 4:
                inc = [x for x in CLIPS if x["name"] == "over_victim"][0]
                outc = [x for x in CLIPS if x["name"] == "kill_room_knife"][0]
                A = render_clip(outc, min(f, outc["f1"] - 1)); B = render_clip(inc, max(f, inc["f0"]))
                prog = (k + 5) / 10
                xs = np.arange(W, dtype=np.float32)[None, :] + 0.45 * (H - np.arange(H, dtype=np.float32))[:, None]
                lead = -500 + (W + 1100) * ease_in(prog, 1.4); trail = lead - 420
                inside = (xs < lead) & (xs > trail); passed = xs <= trail
                out = np.where(passed[..., None], B, A)
                out[inside] = 0.96
    # transitions & overlays
    for fg0 in (E.fe(53), E.fe(72)):
        out = glitch(out, f, fg0)
    fD = E.fe(E.DROP_E)
    if fD <= f < fD + 16:
        k = f - fD
        fl = [0.0, 0.0, 0.0, 0.25, 0.12, 0.05, 0.0][k] if k < 7 else 0
        out = np.clip(out * (1 + 2.5 * fl), 0, 1) * (1 - fl) + fl * 0.97
        out = rgb_split(out, 16 * math.exp(-k / 4.0))
    if f < E.fe(16) + 40:
        out = draw_namecard(out, f)
    if E.fe(48) <= f < E.fe(52):
        out = draw_words(out, f)
    if not (E.fe(32) <= f < E.fe(34)): out = draw_splats(out, f)
    # finishing
    look = c.get("look", "ink")
    if c.get("kind") != "logo":
        out = out * VIG
    out = out + grain(f, 0.030 if look == "mono" else 0.024)
    lb = E.LETTERBOX
    if f < fD:
        bars = lb
    else:
        bars = int(lb * (1 - ease_out((f - fD) / 7, 3)))
    if bars > 0:
        out[:bars] = 0; out[H - bars:] = 0
    out = draw_title(out, f)                       # drawn over the bars: the blood runs off the frame
    out = draw_blood(out, f)                       # the pour and the falling curtain
    if E.fe(32) <= f < E.fe(34): out = draw_splats(out, f)
    out = draw_watermark(np.clip(out, 0, 1), f)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)

def render_scaled(f):
    o = render(f)
    return cv2.resize(o, (W // 2, H // 2), interpolation=cv2.INTER_AREA) if SCALE != 1 else o

SCALE = 1

def main():
    global SCALE
    mode = sys.argv[1]
    load()
    if mode == "stills":
        name = sys.argv[2]; frames = [int(a) for a in sys.argv[3:]]
        ims = []
        for f in frames:
            im = cv2.resize(render(f), (480, 270) if E.ORIENT == "h" else (216, 384), interpolation=cv2.INTER_AREA)
            cv2.putText(im, str(f), (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
            ims.append(im)
        cols = 4
        while len(ims) % cols: ims.append(np.zeros_like(ims[0]))
        cv2.imwrite(f"{E.ROOT}/v2/frames/{name}.jpg", np.vstack([np.hstack(ims[i:i + cols]) for i in range(0, len(ims), cols)]),
                    [cv2.IMWRITE_JPEG_QUALITY, 88])
        return
    if mode == "full":                                                     # full-res single frames
        for f in [int(a) for a in sys.argv[2:]]:
            cv2.imwrite(f"{E.ROOT}/v2/frames/full_{f:04d}.jpg", render(f), [cv2.IMWRITE_JPEG_QUALITY, 92])
        return
    if mode == "video":
        outdir = f"{E.ROOT}/{sys.argv[2]}"; os.makedirs(outdir, exist_ok=True)
        preview = "--preview" in sys.argv
        SCALE = 0.5 if preview else 1
        ow, oh = (W // 2, H // 2) if preview else (W, H)
        n = E.DUR_F
        vf = "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p"
        tags = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]
        aud_pre = f"{E.ROOT}/v2/audio/mix_preroll.wav"; aud = f"{E.ROOT}/v2/audio/mix.wav"
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{ow}x{oh}", "-r", str(FPS), "-i", "-",
               "-itsoffset", str(-1024 / 48000), "-i", aud_pre, "-i", aud]
        if preview:
            cmd += ["-map", "0:v", "-map", "1:a", "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", *tags,
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", f"{outdir}/preview.mp4"]
        else:
            cmd += ["-map", "0:v", "-map", "1:a", "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                    "-maxrate", "24M", "-bufsize", "48M", "-profile:v", "high", "-level", "4.2", "-g", "120", "-bf", "3", *tags,
                    "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart",
                    f"{outdir}/the_dark_passenger_voidfx{'' if E.ORIENT == 'h' else '_9x16'}.mp4",
                    "-map", "0:v", "-map", "2:a", "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "11",
                    "-profile:v", "high", "-level", "5.1", *tags, "-c:a", "pcm_s24le", "-ar", "48000",
                    f"{outdir}/the_dark_passenger_voidfx{'' if E.ORIENT == 'h' else '_9x16'}_master.mov"]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        with Pool(4) as pool:
            for i, fr in enumerate(pool.imap(render_scaled, range(n), chunksize=6)):
                p.stdin.write(fr.tobytes())
                if i % 150 == 0: print(f"frame {i}/{n}", flush=True)
        p.stdin.close(); p.wait()
        print("done", outdir, flush=True)

if __name__ == "__main__":
    main()
