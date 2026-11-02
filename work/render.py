"""Renderer for THE MASK SLIPS. Reads work/edl.py only.

  python3 work/render.py prep                 # per-shot colour correction + blood-drop tracking -> work/prep.json
  python3 work/render.py stills [frames...]   # graded still frames -> frames/still_XXXX.jpg
  python3 work/render.py video OUTDIR [--preview] [--noeffects]
                                              # full render piped to ffmpeg (needs audio/mix.wav)

Pipeline per output frame: source frame(s) -> ROI -> chroma clean-up -> per-shot WB/exposure
-> shared look -> 9:16 warp (Lanczos) -> transition effects -> sharpen -> vignette -> grain
-> graphics/text -> 8-bit.
"""
import os, sys, json, math, subprocess, bisect
import numpy as np, cv2
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edl
from cropcheck import interp_keys, ease

ROOT = edl.ROOT
W, H, FPS = edl.W, edl.H, edl.FPS
TL = edl.timeline()
STARTS = [f0 for f0, _, _ in TL]
CACHE = {}
PREP = {}
ARGS = dict(effects=True, scale=1.0)

FONT_SUB = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"
FONT_SUB_B = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
FONT_MONO = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Medium.ttf"
DEEP_RED_BGR = (28, 22, 178)          # #B2161C

# ------------------------------------------------------------------ source access
def needed_frames():
    need = set()
    for f0, f1, s in TL:
        a = int(math.floor(s["a"] * FPS)) - 1
        b = int(math.ceil(s["b"] * FPS)) + 1
        need.update(range(max(0, a), b + 1))
    return need

def load_cache():
    need = needed_frames()
    cap = cv2.VideoCapture(edl.SRC)
    i, mx = 0, max(need)
    while i <= mx:
        ok, f = cap.read()
        if not ok:
            break
        if i in need:
            CACHE[i] = f
        i += 1
    cap.release()

def shot_at(fo):
    i = bisect.bisect_right(STARTS, fo) - 1
    return TL[i]

def src_pos(s, f0, f1, fo):
    """source position (in source frames) and local playback speed for output frame fo."""
    u = (fo - f0) / (f1 - f0)
    keys = s.get("tmap") or [(0.0, s["a"]), (1.0, s["b"])]
    for (u0, t0), (u1, t1) in zip(keys, keys[1:]):
        if u <= u1 or (u1 == keys[-1][0]):
            v = 0.0 if u1 == u0 else (u - u0) / (u1 - u0)
            v = min(max(v, 0.0), 1.0)
            speed = 0.0 if u1 == u0 else (t1 - t0) / ((u1 - u0) * (f1 - f0) / FPS)
            return (t0 + (t1 - t0) * v) * FPS, u, speed
    return keys[-1][1] * FPS, u, 0.0

def src_frame(s, sp, speed):
    lo = int(math.ceil(s["a"] * FPS)); hi = int(math.floor(s["b"] * FPS))
    if speed >= 0.9 or speed < 0.05:
        k = min(max(int(round(sp)), lo), hi)
        return CACHE[k].astype(np.float32)
    i0 = min(max(int(math.floor(sp)), lo), hi - 1); w = sp - i0
    w = min(max(w, 0.0), 1.0)
    return CACHE[i0].astype(np.float32) * (1 - w) + CACHE[i0 + 1].astype(np.float32) * w

# ------------------------------------------------------------------ colour
CURVE_X = np.array([0.0, 0.06, 0.18, 0.35, 0.50, 0.68, 0.85, 0.95, 1.0])
CURVE_Y = np.array([0.028, 0.055, 0.155, 0.335, 0.50, 0.695, 0.865, 0.94, 0.975])
from scipy.interpolate import PchipInterpolator
_LUT_X = np.linspace(0, 1, 2048, dtype=np.float32)
_LUT_Y = PchipInterpolator(CURVE_X, CURVE_Y)(_LUT_X).astype(np.float32)

LOOKS = {   # sat, shadow tint (BGR add), highlight tint (BGR add), contrast blend
    "day":   dict(sat=0.90, sh=(0.010, 0.004, -0.008), hi=(-0.014, 0.002, 0.016), k=0.85),
    "room":  dict(sat=0.84, sh=(0.020, 0.008, -0.010), hi=(-0.008, 0.000, 0.012), k=1.0),
    "night": dict(sat=0.80, sh=(0.026, 0.010, -0.012), hi=(-0.004, 0.000, 0.008), k=1.0),
}
TARGET = {"day": 0.42, "room": 0.36, "night": 0.32}

def luma(img):
    return img[..., 0] * 0.114 + img[..., 1] * 0.587 + img[..., 2] * 0.299

def correction_for(s):
    """Partial grey-world WB + gamma so the face hits the look's target luminance."""
    k = int(round((s["a"] + s["b"]) / 2 * FPS))
    f = CACHE[k].astype(np.float32) / 255.0
    L = luma(f); m = (L > 0.05) & (L < 0.95)
    means = f[m].mean(0) if m.sum() > 1000 else f.reshape(-1, 3).mean(0)
    strength = s.get("wb", 0.45 if s["look"] == "day" else 0.3)
    gains = np.clip((means.mean() / means) ** strength, 0.86, 1.16)
    fx, fy, fr = s["face"]
    patch = f[max(0, fy - fr):fy + fr, max(0, fx - fr):fx + fr] * gains
    face = float(np.percentile(luma(patch), 65))      # skin, not hair / eye sockets
    target = TARGET[s["look"]]
    gamma = float(np.clip(math.log(target) / math.log(max(face, 0.02)), 0.72, 1.12))
    if "gamma" in s:
        gamma = float(s["gamma"])          # manual override (EDL)
    return dict(gains=gains.tolist(), gamma=gamma, face=face)

def chroma_clean(img8):
    """Soften 4:2:0/macroblock chroma noise only (luma untouched)."""
    ycc = cv2.cvtColor(img8, cv2.COLOR_BGR2YCrCb)
    ycc[..., 1] = cv2.GaussianBlur(ycc[..., 1], (0, 0), 1.2)
    ycc[..., 2] = cv2.GaussianBlur(ycc[..., 2], (0, 0), 1.2)
    return cv2.cvtColor(ycc, cv2.COLOR_YCrCb2BGR)

def grade(img, corr, look):
    """img float32 BGR 0..1 (ROI at source resolution)."""
    img = img * np.array(corr["gains"], np.float32)
    img = np.clip(img, 0, 1) ** corr["gamma"]
    lk = LOOKS[look]
    # tone curve on each channel, blended by look contrast
    c = np.interp(img, _LUT_X, _LUT_Y).astype(np.float32)
    img = img + (c - img) * lk["k"]
    Y = luma(img)[..., None]
    img = Y + (img - Y) * lk["sat"]
    # deep-red accent: blood-like reds (R >> G ~ B) get richer and slightly darker
    b, g, r = img[..., 0], img[..., 1], img[..., 2]
    red = np.clip(((r - np.maximum(g, b)) / (r + 1e-3) - 0.40) * 2.2, 0, 1) * np.clip(1 - np.abs(g - b) * 6, 0, 1)
    if red.max() > 0:
        Yr = luma(img)[..., None]
        boosted = Yr + (img - Yr) * 1.22
        boosted = boosted * np.array([0.90, 0.90, 0.97], np.float32)
        img = img + (boosted - img) * red[..., None]
    # split tone
    L = np.clip(luma(img), 0, 1)[..., None]
    img = img + ((1 - L) ** 2) * np.array(lk["sh"], np.float32) + (L ** 2) * np.array(lk["hi"], np.float32)
    return np.clip(img, 0, 1)

# ------------------------------------------------------------------ geometry
def view(s, u, fo):
    """crop centre/size in source px, including zoom keys and global punches/shake."""
    cx, cy, h = interp_keys(s["crop"], u)
    z = interp_keys(s["zoom"], u)[0]
    if ARGS["effects"]:
        for pf, amt, tau in PUNCHES:
            if fo >= pf:
                z *= 1 + amt * math.exp(-(fo - pf) / tau)
    h = h / z; w = h * 9 / 16
    dx = dy = 0.0
    if ARGS["effects"] and edl.fp(edl.DROP_P) <= fo < edl.fp(edl.DROP_P) + 10:
        t = (fo - edl.fp(edl.DROP_P)) / FPS
        env = math.exp(-t / 0.06)
        dx = 0.010 * w * env * math.sin(2 * math.pi * 23 * t)
        dy = 0.006 * w * env * math.sin(2 * math.pi * 17 * t + 1.3)
    cx = min(max(cx, w / 2), 1200 - w / 2) + dx
    cy = min(max(cy, h / 2), 720 - h / 2) + dy
    return cx, cy, w, h

DROP_F = edl.fp(edl.DROP_P)
PUNCHES = [  # (frame, amount, tau frames)
    (DROP_F, 0.0, 1),                      # placeholder (drop zoom handled by shot keys)
    (edl.fp(55), 0.045, 6.0),              # finger reaches lips on the last hit before the stop
    (edl.fp(39), 0.0, 1),                  # (victim POV punch handled by its zoom keys)
]

# ------------------------------------------------------------------ effects
def fx_frame(out, fo, s):
    if not ARGS["effects"]:
        return out
    # the breath before the drop (song's sub-gap ~ frames 475-479), then the flash
    if s["name"] == "from_dark":
        k = DROP_F - fo
        dip = {6: 0.10, 5: 0.24, 4: 0.36, 3: 0.42, 2: 0.36}.get(k, 0.0)
        out = out * (1 - dip)
        if k == 1:
            out = np.clip(out * 1.9, 0, 1)
    if "evidence_freeze" in s.get("fx", []):
        fz = edl.fp(edl.FREEZE_P)
        if fo >= fz:
            k = fo - fz
            Y = luma(out)[..., None]
            b, g, r = out[..., 0], out[..., 1], out[..., 2]
            red = np.clip(((r - np.maximum(g, b)) / (r + 1e-3) - 0.35) * 3, 0, 1)[..., None]
            ds = Y + (out - Y) * 0.55
            out = ds + (out - ds) * red                     # everything but the blood loses colour
            out = out * 0.94
            if k < 4:                                       # camera-shutter flash
                e = [0.42, 0.22, 0.10, 0.04][k]
                out = out * (1 - e) + e
    if DROP_F <= fo < DROP_F + 16:
        e = math.exp(-(fo - DROP_F) / 2.4)
        out = np.clip(out * (1 + 2.6 * e), 0, 1)
        out = out * (1 - 0.5 * e) + 0.5 * e * np.array([0.96, 0.97, 0.98], np.float32)
    if DROP_F + 2 <= fo < DROP_F + 11:                 # the mask cracks: held slice offsets + RGB split
        k = fo - DROP_F - 2
        amp = 1.0 if k < 3 else (0.5 if k < 6 else 0.22)
        bands = [(0.27, 0.335, 0.036), (0.585, 0.622, -0.026), (0.70, 0.716, 0.018)]
        for y0, y1, off in bands:
            a, b = int(y0 * H), int(y1 * H)
            d = int(off * W * amp)
            if d:
                out[a:b] = np.roll(out[a:b], d, axis=1)
                if d > 0: out[a:b, :d] = out[a:b, d:d + 1]
                else: out[a:b, d:] = out[a:b, d - 1:d]
        sp = int(round(7 * amp))
        if sp:
            out[..., 2] = np.roll(out[..., 2], sp, axis=1)
            out[..., 0] = np.roll(out[..., 0], -sp, axis=1)
    return out

# ------------------------------------------------------------------ finishing
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.sqrt(((_xx - W / 2) / (W / 2)) ** 2 * 0.8 + ((_yy - H / 2) / (H / 2)) ** 2)
VIGNETTE = (1 - 0.13 * np.clip(_r / 1.25, 0, 1) ** 2.4)[..., None].astype(np.float32)
del _yy, _xx, _r

def finish(out, fo):
    blur = cv2.GaussianBlur(out, (0, 0), 1.3)
    out = out + (out - blur) * 0.30
    out = out * VIGNETTE
    # fine film-like grain: generated at 1/3 resolution (soft ~3 px clumps), mid-tone weighted, light
    rng = np.random.default_rng(1000 + fo)
    g = rng.standard_normal((H // 3, W // 3)).astype(np.float32)
    g = cv2.resize(g, (W, H), interpolation=cv2.INTER_CUBIC)
    L = np.clip(luma(np.clip(out, 0, 1)), 0, 1)
    wgt = np.clip(4 * L * (1 - L), 0.25, 1.0)
    out = out + (g * 0.010 * wgt)[..., None]
    return np.clip(out, 0, 1)

# ------------------------------------------------------------------ graphics
_FONTS = {}
def font(path, size):
    k = (path, size)
    if k not in _FONTS:
        _FONTS[k] = ImageFont.truetype(path, size)
    return _FONTS[k]

def composite_rgba(out, rgba, x0, y0):
    """alpha-composite an RGBA PIL image (RGB order) onto out (float BGR) at x0,y0."""
    a = np.asarray(rgba).astype(np.float32) / 255.0
    h, w = a.shape[:2]
    xa, ya = max(0, x0), max(0, y0); xb, yb = min(W, x0 + w), min(H, y0 + h)
    if xb <= xa or yb <= ya:
        return out
    sub = a[ya - y0:yb - y0, xa - x0:xb - x0]
    col = sub[..., [2, 1, 0]]; al = sub[..., 3:4]
    out[ya:yb, xa:xb] = out[ya:yb, xa:xb] * (1 - al) + col * al
    return out

def text_layer(parts, size, tracking=0, shadow=10, shadow_alpha=150):
    """parts: list of (text, fontpath, (r,g,b,a)). Returns RGBA image with soft shadow."""
    fs = [font(p, size) for _, p, _ in parts]
    widths = [f.getlength(t) + tracking * len(t) for (t, _, _), f in zip(parts, fs)]
    space = fs[0].getlength(" ")
    tw = int(sum(widths) + space * (len(parts) - 1)) + 4 * shadow
    th = int(size * 1.45) + 4 * shadow
    img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    sh = Image.new("L", (tw, th), 0)
    d = ImageDraw.Draw(img); ds = ImageDraw.Draw(sh)
    x = 2 * shadow; y = 2 * shadow
    for (t, _, col), f, wdt in zip(parts, fs, widths):
        if tracking:
            xx = x
            for ch in t:
                d.text((xx, y), ch, font=f, fill=col); ds.text((xx, y + 2), ch, font=f, fill=shadow_alpha)
                xx += f.getlength(ch) + tracking
        else:
            d.text((x, y), t, font=f, fill=col); ds.text((x, y + 2), t, font=f, fill=shadow_alpha)
        x += wdt + space
    sh = sh.filter(ImageFilter.GaussianBlur(shadow))
    base = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    base.putalpha(sh)
    return Image.alpha_composite(base, img)

SUB_SIZE = 64
SUB_COL = (246, 243, 236, 255)

def sub_words():
    """word -> edit onset (s)"""
    return [(w, t + edl.VO_SHIFT) for w, t in edl.VO["words"]]

def draw_subs(out, fo):
    t = fo / FPS
    words = dict(sub_words())
    for line in edl.SUBS:
        t_in = words[line["words"][0]]
        if not (t_in - 0.02 <= t < line["t_out"]):
            continue
        # fade the whole line out over the last 8 frames
        a_line = min(1.0, max(0.0, (line["t_out"] - t) / (8 / FPS)))
        parts = []
        for wd in line["words"]:
            on = words[wd]
            a = min(1.0, max(0.0, (t - on + 0.02) / (5 / FPS)))
            alpha = int(255 * a * a_line)
            p = FONT_SUB_B if wd in line["accent"] else FONT_SUB
            parts.append((wd, p, SUB_COL[:3] + (alpha,)))
        lay = text_layer(parts, SUB_SIZE, tracking=0, shadow=9, shadow_alpha=int(170 * a_line))
        # per-word rise is subtle: shift whole line 6px up during first word's fade-in
        rise = int(6 * (1 - min(1.0, (t - t_in) / (6 / FPS))))
        out = composite_rgba(out, lay, (W - lay.width) // 2, edl.SUB_Y - lay.height // 2 + rise)
        # deep-red accent: hairline under the accent word, drawn in over 5 frames
        for wd in line["accent"]:
            on = words[wd]
            if t >= on:
                prog = min(1.0, (t - on) / (5 / FPS))
                f_reg = font(FONT_SUB, SUB_SIZE); f_b = font(FONT_SUB_B, SUB_SIZE)
                sp = f_reg.getlength(" ")
                x = (W - lay.width) // 2 + 18
                for w2 in line["words"]:
                    fw = (f_b if w2 in line["accent"] else f_reg).getlength(w2)
                    if w2 == wd:
                        x0 = int(x); x1 = int(x + (fw - f_b.getlength(".")) * prog)
                        y = edl.SUB_Y + SUB_SIZE // 2 + 14 + rise
                        out[y - 1:y + 3, max(0, x0 - 1):x1 + 1] *= (1 - 0.55 * a_line)  # shadow
                        out[y - 2:y + 2, x0:x1] = np.array(DEEP_RED_BGR, np.float32)[::-1][::-1] / 255.0 * a_line + out[y - 2:y + 2, x0:x1] * (1 - a_line)
                    x += fw + sp
    return out

def draw_signature(out, fo):
    sg = edl.SIGNATURE
    if not sg["enabled"]:
        return out
    t = fo / FPS
    if not (sg["t_in"] <= t < sg["t_out"]):
        return out
    a = min(1.0, (t - sg["t_in"]) / (8 / FPS), (sg["t_out"] - t) / (8 / FPS))
    lay = text_layer([(sg["text"], FONT_SUB, (246, 243, 236, int(225 * a)))], 40, tracking=7, shadow=6, shadow_alpha=int(150 * a))
    return composite_rgba(out, lay, (W - lay.width) // 2, 1528 - lay.height // 2)

def draw_annotation(out, fo, s, u, view_rect):
    """forensic bracket around the tracked blood drop on the slide."""
    tr = PREP.get("drop_track", {})
    key = str(fo)
    if key not in tr:
        return out
    first = PREP["drop_first"]
    if fo < first:
        return out
    sx, sy, sr = tr[key]
    cx, cy, w, h = view_rect
    k = W / w
    ox = (sx - (cx - w / 2)) * k; oy = (sy - (cy - h / 2)) * k
    r = max(sr * k, 18)
    age = fo - first
    pr = min(1.0, age / 6.0)
    pe = 1 - (1 - pr) ** 3
    half = r * (1.9 + 0.9 * (1 - pe))
    ln = half * 0.42
    th = 5
    col = np.array(DEEP_RED_BGR, np.float32) / 255.0
    alpha = pe
    def hline(x0, x1, y):
        x0, x1 = int(min(x0, x1)), int(max(x0, x1)); y = int(y)
        out[max(0, y - th // 2):y + th // 2, max(0, x0):min(W, x1)] = out[max(0, y - th // 2):y + th // 2, max(0, x0):min(W, x1)] * (1 - alpha) + col * alpha
    def vline(x, y0, y1):
        y0, y1 = int(min(y0, y1)), int(max(y0, y1)); x = int(x)
        out[max(0, y0):min(H, y1), max(0, x - th // 2):x + th // 2] = out[max(0, y0):min(H, y1), max(0, x - th // 2):x + th // 2] * (1 - alpha) + col * alpha
    for sxn in (-1, 1):
        for syn in (-1, 1):
            X = ox + sxn * half; Y = oy + syn * half
            hline(X, X - sxn * ln, Y); vline(X, Y, Y - syn * ln)
    # label
    lay = text_layer([("EVIDENCE 01", FONT_MONO, (246, 243, 236, int(240 * alpha)))], 31, tracking=4, shadow=5, shadow_alpha=int(190 * alpha))
    lx = int(ox - half) - 10; ly = int(oy + half) + 4
    lx = min(lx, W - 170 - lay.width)
    out = composite_rgba(out, lay, lx, ly)
    return out

# ------------------------------------------------------------------ frame
def render(fo):
    f0, f1, s = shot_at(fo)
    s["_f0"], s["_f1"] = f0, f1
    sp, u, speed = src_pos(s, f0, f1, fo)
    src = src_frame(s, sp, speed)
    cx, cy, w, h = view(s, u, fo)
    # ROI with margin, graded at source resolution
    m = 12
    x0 = int(max(0, math.floor(cx - w / 2) - m)); x1 = int(min(1200, math.ceil(cx + w / 2) + m))
    y0 = int(max(0, math.floor(cy - h / 2) - m)); y1 = int(min(720, math.ceil(cy + h / 2) + m))
    roi = np.clip(src[y0:y1, x0:x1], 0, 255).astype(np.uint8)
    roi = chroma_clean(roi).astype(np.float32) / 255.0
    corr = PREP["corr"][str(s["pack"]) + ":" + s["look"]]
    roi = grade(roi, corr, s["look"])
    if "contrast" in s:                                   # per-shot extra contrast (murky sources)
        c = s["contrast"]; piv = float(np.median(luma(roi)))
        roi = np.clip((roi - piv) * c + piv, 0, 1)
    sc = w / W
    M = np.float32([[sc, 0, cx - w / 2 - x0], [0, sc, cy - h / 2 - y0]])
    out = cv2.warpAffine(roi, M, (W, H), flags=cv2.WARP_INVERSE_MAP | cv2.INTER_LANCZOS4,
                         borderMode=cv2.BORDER_REFLECT)
    out = np.clip(out, 0, 1)
    out = fx_frame(out, fo, s)
    out = finish(out, fo)
    if ARGS["effects"]:
        if "slide_annotation" in s.get("fx", []):
            out = draw_annotation(out, fo, s, u, (cx, cy, w, h))
        out = draw_signature(out, fo)
    out = draw_subs(out, fo)
    o8 = (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
    if ARGS["scale"] != 1.0:
        o8 = cv2.resize(o8, (int(W * ARGS["scale"]) // 2 * 2, int(H * ARGS["scale"]) // 2 * 2), interpolation=cv2.INTER_AREA)
    return o8

# ------------------------------------------------------------------ prep
def track_drop(s, f0, f1):
    """locate the round, saturated-red blood drop on the slide per output frame."""
    track = {}
    for fo in range(f0, f1):
        sp, u, speed = src_pos(s, f0, f1, fo)
        img = CACHE[int(round(sp))]
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h, sat, v = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
        m = (((h < 7) | (h > 172)) & (sat > 175) & (v > 70)).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        n, lab, st, ce = cv2.connectedComponentsWithStats(m)
        best = None
        for i in range(1, n):
            area, bw, bh = st[i, cv2.CC_STAT_AREA], st[i, cv2.CC_STAT_WIDTH], st[i, cv2.CC_STAT_HEIGHT]
            if area >= 150 and 0.6 < bw / max(1, bh) < 1.7 and 450 < ce[i][0] < 760:
                if best is None or area > st[best, cv2.CC_STAT_AREA]:
                    best = i
        if best is not None:
            bw, bh = st[best, cv2.CC_STAT_WIDTH], st[best, cv2.CC_STAT_HEIGHT]
            track[fo] = (float(ce[best][0]), float(ce[best][1]), float(max(bw, bh) / 2))
    keys = sorted(track)
    sm = {}
    for k in keys:
        nb = [track[j] for j in range(k - 2, k + 3) if j in track]
        sm[k] = tuple(float(np.mean([v[i] for v in nb])) for i in range(3))
    first = next((k for k in keys if all((k + j) in track for j in range(3))), None)
    sm = {str(k): v for k, v in sm.items() if first is not None and k >= first}
    return sm, first

def prep():
    load_cache()
    corr = {}
    for f0, f1, s in TL:
        key = str(s["pack"]) + ":" + s["look"]
        if key not in corr:
            corr[key] = correction_for(s)
            print(f"{s['name']:16s} face {corr[key]['face']:.3f} -> gamma {corr[key]['gamma']:.2f} gains {np.round(corr[key]['gains'], 3).tolist()}")
    out = dict(corr=corr)
    for f0, f1, s in TL:
        if "slide_annotation" in s.get("fx", []):
            tr, first = track_drop(s, f0, f1)
            freeze = edl.fp(edl.FREEZE_P)
            out["drop_track"] = tr; out["drop_seen"] = first; out["drop_first"] = max(first or freeze, freeze)
            print("blood drop first tracked at frame", first, "t=%.3f" % (first / FPS if first else -1), "frames tracked", len(tr))
    json.dump(out, open(os.path.join(ROOT, "work", f"prep_{edl.VARIANT}.json"), "w"), indent=1)

def init_worker():
    pass

def main():
    mode = sys.argv[1]
    if mode == "prep":
        prep(); return
    PREP.update(json.load(open(os.path.join(ROOT, "work", f"prep_{edl.VARIANT}.json"))))
    if "--noeffects" in sys.argv:
        ARGS["effects"] = False
    if mode == "stills":
        frames = [int(a) for a in sys.argv[2:] if a.lstrip("-").isdigit()]
        load_cache()
        for fo in frames:
            cv2.imwrite(os.path.join(ROOT, "frames", f"still_{fo:04d}.jpg"), render(fo), [cv2.IMWRITE_JPEG_QUALITY, 90])
        print("stills:", frames); return
    if mode == "video":
        outdir = os.path.join(ROOT, sys.argv[2]); os.makedirs(outdir, exist_ok=True)
        preview = "--preview" in sys.argv
        if preview:
            ARGS["scale"] = 0.5
        load_cache()
        n = edl.DUR_FRAMES
        ow, oh = (int(W * ARGS["scale"]) // 2 * 2, int(H * ARGS["scale"]) // 2 * 2)
        audio = os.path.join(ROOT, "audio", "mix.wav")
        vf = "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p"
        tags = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]
        pre = os.path.join(ROOT, "audio", "mix_preroll.wav")
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{ow}x{oh}", "-r", str(FPS), "-i", "-",
               "-itsoffset", str(-1024 / 48000), "-i", pre,          # 1: AAC source with hidden encoder pre-roll
               "-i", audio]                                          # 2: PCM source for the master
        if preview:
            cmd += ["-map", "0:v", "-map", "1:a", "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", *tags,
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", os.path.join(outdir, "preview.mp4")]
        else:
            cmd += ["-map", "0:v", "-map", "1:a", "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "19",
                    "-maxrate", "20M", "-bufsize", "40M",
                    "-profile:v", "high", "-level", "4.2", "-g", "120", "-bf", "3", *tags,
                    "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart",
                    os.path.join(outdir, "the_mask_slips_tiktok.mp4"),
                    "-map", "0:v", "-map", "2:a", "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "12",
                    "-profile:v", "high", "-level", "5.1", *tags,
                    "-c:a", "pcm_s24le", "-ar", "48000", os.path.join(outdir, "the_mask_slips_master.mov")]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        with Pool(4, initializer=init_worker) as pool:
            for i, fr in enumerate(pool.imap(render, range(n), chunksize=4)):
                p.stdin.write(fr.tobytes())
                if i % 120 == 0:
                    print(f"frame {i}/{n}", flush=True)
        p.stdin.close(); p.wait()
        print("done", outdir)

if __name__ == "__main__":
    main()
