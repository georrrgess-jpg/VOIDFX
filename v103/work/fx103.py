# ============================================================================ v103 — FOREVER: undertow toolkit (Dexter × Everlong)
# spliced into render103.py before main() by splice.py; the last definitions win, so this section owns the frame.
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

# ---------------------------------------------------------------------------- new transitions: sea spray, duct tape
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

_TP = {}
def tape_strip(w=1500, h=300, seed=1):
    key = (w, h, seed)
    if key in _TP: return _TP[key]
    rng = np.random.default_rng(seed); a = np.ones((h, w), np.float32)
    for side in (0, 1):                                                               # torn ends
        x0 = 0 if side == 0 else w - 40; prof = (np.cumsum(rng.normal(0, 4, h)) % 30)
        for y in range(h):
            if side == 0: a[y, :int(prof[y]) + 4] = 0
            else: a[y, w - int(prof[y]) - 4:] = 0
    yy = np.linspace(0, 1, h)[:, None]
    sheen = 0.30 + 0.28 * np.exp(-((yy - 0.28) / 0.10) ** 2) + 0.10 * np.exp(-((yy - 0.75) / 0.18) ** 2)        # silver, curved across the width
    weave = (np.sin(np.arange(w)[None, :] / 1.6) * 0.5 + 0.5) * 0.035 + (np.sin(np.arange(h)[:, None] / 1.8) * 0.5 + 0.5) * 0.03
    nz = _lowfreq((h, w), (6, 40), seed + 5) * 0.10
    crease = np.zeros((h, w), np.float32)
    for _ in range(9):                                                                # wrinkles where it was slapped on
        x0 = rng.uniform(80, w - 80); cv2.line(crease, (int(x0), 0), (int(x0 + rng.uniform(-60, 60)), h), float(rng.uniform(0.5, 1.0)), int(rng.integers(2, 5)), cv2.LINE_AA)
    crease = cv2.GaussianBlur(crease, (0, 0), 2.5)
    col = np.dstack([sheen + weave + nz + crease * 0.18 - np.roll(crease, 4, 1) * 0.12] * 3).astype(np.float32) * np.array([1.0, 1.0, 0.97], np.float32)
    col[:8] *= 0.7; col[-8:] *= 0.6
    _TP[key] = np.dstack([np.clip(col, 0, 1), cv2.GaussianBlur(a, (0, 0), 0.8)]).astype(np.float32); return _TP[key]

def tape_tr(A, B, j, f, sa, sb, pre=6, post=10):
    """two strips of duct tape slap across the lens (an X); ripped off, the next shot is underneath."""
    base = A if j < 0 else B
    lay = np.zeros((H, W, 4), np.float32)
    for i, (ang, y0, k0) in enumerate(((-18, H * 0.42, -6), (16, H * 0.56, -3))):
        k = j - k0
        if k < 0: continue
        if j < 0 or k < 3: x = W / 2 + (W * 1.2) * (1 - eout(clamp((k + 1) / 3, 0, 1), 2.5)); a = 1.0
        else: u = (j + 1) / post; x = W / 2 - (W * 1.6) * ein(u, 1.6) * (1 if i == 0 else -1); a = 1.0
        draw_sprite(lay, tape_strip(seed=i + 1), x, y0, 1.0, ang, 1.0, 0.0, a)
    sh = cv2.GaussianBlur(lay[..., 3], (0, 0), 10)[..., None] * 0.5
    o = base * (1 - np.roll(sh, 18, 0))
    return np.clip(o * (1 - lay[..., 3:4]) + lay[..., :3] * lay[..., 3:4], 0, 1)

TR2.update({"surface": (lambda A, B, j, f, sa, sb: surface_in(B, f, j), 0, int(E.T_SURFACE * FPS) + 20), "wave": (wave_tr, 8, 12),
            "tape": (tape_tr, 6, 10)})

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

# ---- rev 3: the glass shatters (replaces the knife pass). The lens is glass: a hit low and to the side (never on
#      the face) cracks it, the cracks race across the glass, and on the beat the shards tumble toward the lens and fall away.
_GS = {}
def gshards(cx, cy, seed=73):
    key = (int(cx), int(cy), seed)
    if key in _GS: return _GS[key]
    rng = np.random.default_rng(seed); pts = [(cx, cy)]
    for i in range(120):
        r = (rng.random() ** 1.6) * 1500; a = rng.uniform(0, 2 * math.pi)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a) * 1.3
        if 0 <= x < W and 0 <= y < H: pts.append((x, y))
    for x in (0, W - 1):
        for y in np.linspace(0, H - 1, 8): pts.append((x, y))
    for y in (0, H - 1):
        for x in np.linspace(0, W - 1, 6): pts.append((x, y))
    sd = cv2.Subdiv2D((0, 0, W, H))
    for p_ in pts: sd.insert((float(min(W - 1, max(0, p_[0]))), float(min(H - 1, max(0, p_[1])))))
    facets, centers = sd.getVoronoiFacetList([])
    L = []; cr = np.zeros((H, W), np.uint8)
    for poly, c in zip(facets, centers):
        poly = np.array(poly, np.float32); poly[:, 0] = np.clip(poly[:, 0], 0, W - 1); poly[:, 1] = np.clip(poly[:, 1], 0, H - 1)
        x0, y0 = poly.min(0).astype(int); x1, y1 = poly.max(0).astype(int) + 1
        if x1 - x0 < 3 or y1 - y0 < 3: continue
        m = np.zeros((y1 - y0, x1 - x0), np.uint8); cv2.fillPoly(m, [(poly - [x0, y0]).astype(np.int32)], 255, cv2.LINE_AA)
        d = math.hypot(c[0] - cx, c[1] - cy) + 1
        L.append(dict(box=(x0, y0, x1, y1), mask=m.astype(np.float32) / 255, c=(float(c[0]), float(c[1])), v=((c[0] - cx) / d, (c[1] - cy) / d),
                      sp=rng.uniform(0.7, 1.3) * (1.5 - min(1.0, d / 1600)), w=rng.uniform(-16, 16), dz=rng.uniform(0.01, 0.04), delay=d / 1600 * 3.0))
        if d < 520: cv2.polylines(cr, [poly.astype(np.int32)], True, int(255 * (1 - d / 520) ** 0.7), 1, cv2.LINE_AA)   # shard edges only near the hit
    for i in range(14):                                                                # thin radial cracks from the hit
        a = i / 14 * 2 * math.pi + rng.uniform(-0.15, 0.15); r = rng.uniform(600, 2000); q = [(cx, cy)]
        for j in range(1, 12): rr = r * j / 11; aa = a + rng.uniform(-0.05, 0.05); q.append((cx + rr * math.cos(aa), cy + rr * math.sin(aa)))
        for j in range(len(q) - 1):
            cv2.line(cr, tuple(int(v) for v in q[j]), tuple(int(v) for v in q[j + 1]), int(255 * (1 - j / 11) ** 0.6), 2 if j < 3 else 1, cv2.LINE_AA)
    for R in (40, 85):
        cv2.circle(cr, (int(cx), int(cy)), R, 200, 1, cv2.LINE_AA)
    crf = cr.astype(np.float32) / 255
    dist = np.sqrt((_GX - cx) ** 2 + ((_GY - cy) / 1.3) ** 2)
    _GS[key] = (L, np.clip(crf * 0.85 + cv2.GaussianBlur(crf, (0, 0), 3) * 0.35, 0, 1), dist); return _GS[key]

def glass_shatter(A, B, j, f, sa, sb, pre=10, post=18):
    cx, cy = W * 0.26, H * 0.74
    L, crack, dist = gshards(cx, cy)
    if j < 0:                                                                          # the hit, and the cracks racing out across the glass
        u = (j + pre) / pre; R = 1900 * eout(u, 1.6)
        reveal = np.clip((R - dist) / 60, 0, 1) * crack
        o = cv2.remap(A, (_GX + reveal * 4).astype(np.float32), (_GY + reveal * 3).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        o = o * (1 - reveal[..., None] * 0.6) + reveal[..., None] * BONE * 0.85
        hit = np.exp(-dist / (22 + 14 * u))[..., None] * (1 - u * 0.7) * 0.8
        return np.clip(o + hit * BONE * 0.9, 0, 1)
    k = j + 1; out = B * (0.6 + 0.4 * clamp(k / 10, 0, 1))
    for s_ in L:
        kk = k - s_["delay"]; x0, y0, x1, y1 = s_["box"]
        if kk <= 0:
            m = s_["mask"][..., None]; sub = A[y0:y1, x0:x1] * (1 - 0.6 * crack[y0:y1, x0:x1, None]) + BONE * 0.85 * crack[y0:y1, x0:x1, None]
            out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1 - m) + sub * m
            continue
        mv = 30 * s_["sp"] * kk ** 1.35; tx, ty = s_["v"][0] * mv, s_["v"][1] * mv + 1.6 * kk * kk
        sc = 1 + s_["dz"] * kk * 2.5; ang = s_["w"] * kk * 0.4; a = clamp(1 - (kk - 7) / 8, 0, 1)
        if a <= 0: continue
        pcx, pcy = s_["c"]; M = cv2.getRotationMatrix2D((pcx, pcy), ang, sc); M[0, 2] += tx; M[1, 2] += ty
        pad = int(60 + mv * 1.6 + 60 * sc)
        X0, Y0 = max(0, int(pcx + tx) - (x1 - x0) // 2 - pad), max(0, int(pcy + ty) - (y1 - y0) // 2 - pad)
        X1, Y1 = min(W, int(pcx + tx) + (x1 - x0) // 2 + pad), min(H, int(pcy + ty) + (y1 - y0) // 2 + pad)
        if X1 <= X0 or Y1 <= Y0: continue
        Ms = M.copy(); Ms[0, 2] -= X0; Ms[1, 2] -= Y0; Ms[0, 2] += Ms[0, 0] * x0 + Ms[0, 1] * y0; Ms[1, 2] += Ms[1, 0] * x0 + Ms[1, 1] * y0
        wi = cv2.warpAffine(A[y0:y1, x0:x1], Ms, (X1 - X0, Y1 - Y0), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
        wm = cv2.warpAffine(s_["mask"], Ms, (X1 - X0, Y1 - Y0), flags=cv2.INTER_LINEAR, borderValue=0)[..., None] * a
        edge = cv2.morphologyEx(wm[..., 0], cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))[..., None]
        shade = 0.85 + 0.3 * math.sin(math.radians(ang) * 3 + s_["w"])                  # each shard catches the light differently
        out[Y0:Y1, X0:X1] = out[Y0:Y1, X0:X1] * (1 - wm) + np.clip(wi * shade * 0.9 + TEAL * 0.06 + edge * BONE * 0.9, 0, 1) * wm
    if k < 12:                                                                         # rev 4: fine glass dust glints from the hit (no red mist)
        rng = np.random.default_rng(17); lay = np.zeros((H // 2, W // 2), np.float32)
        for i in range(90):
            a_ = rng.uniform(-math.pi * 0.95, 0.15); sp = rng.uniform(300, 1300); r_ = rng.uniform(1, 3)
            x = cx + math.cos(a_) * sp * k / 60; y = cy + math.sin(a_) * sp * k / 60 + 500 * (k / 60) ** 2
            cv2.circle(lay, (int(x / 2), int(y / 2)), int(r_), 1.0, -1, cv2.LINE_AA)
        lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 0.8), (W, H))[..., None] * (1 - k / 12)
        out = out + BONE * lay * 0.8
    return np.clip(out, 0, 1)

TR2["glass_shatter"] = (glass_shatter, 10, 18)

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
