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
    m = img.reshape(-1, 3).mean(0); gains = np.clip((m.mean() / (m + 1e-6)) ** 0.10, 0.92, 1.08)
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
    x = L + (x - L) * (0.78 + 0.45 * red)                                             # drained, but blood stays red
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

# ---------------------------------------------------------------------------- THE SAMPLE (drop): scalpel cut, beads, slide press
CUT_P0 = np.array([W * 0.08, H * 0.60], np.float32); CUT_P1 = np.array([W * 0.92, H * 0.47], np.float32)
_SC = {}
def blade_sprite():
    if "b" in _SC: return _SC["b"]
    h, w = 120, 560; m = np.zeros((h, w), np.float32)
    blade = np.array([[0, 60], [60, 42], [230, 30], [330, 34], [372, 50], [372, 78], [300, 84], [150, 82], [40, 72]], np.int32)
    cv2.fillPoly(m, [blade], 1.0, cv2.LINE_AA)
    handle = np.zeros((h, w), np.float32); cv2.rectangle(handle, (372, 46), (556, 82), 1.0, -1, cv2.LINE_AA)
    a = np.maximum(m, handle); a = cv2.GaussianBlur(a, (0, 0), 0.8)
    yy = np.linspace(0, 1, h)[:, None]
    col = (STEELC * (0.55 + 0.45 * (1 - yy) ** 0.8)[..., None]) * m[..., None] + np.array([0.20, 0.20, 0.21], np.float32) * handle[..., None]
    spec = np.exp(-((np.arange(h)[:, None] - 46) / 3.5) ** 2) * m * 0.9
    col = col + spec[..., None]
    for x in range(390, 540, 18): cv2.line(col, (x, 50), (x, 78), (0.30, 0.30, 0.31), 2, cv2.LINE_AA)
    _SC["b"] = np.dstack([np.clip(col, 0, 1), a]).astype(np.float32); return _SC["b"]

def cut_progress(t):
    return clamp((t - (E.T_CUT - 0.10)) / 0.26, 0, 1)

def beads(img, f, grow, line_open=1.0, smear_u=0.0):
    """the cut opens, blood beads well up along it (glossy)."""
    t = f / FPS; pr = cut_progress(t); P0, P1 = CUT_P0, CUT_P1
    if pr <= 0: return img
    d = P1 - P0; L = np.linalg.norm(d); dn = d / L; nn = np.array([-dn[1], dn[0]], np.float32)
    s_ = (_GX - P0[0]) * dn[0] + (_GY - P0[1]) * dn[1]; q = (_GX - P0[0]) * nn[0] + (_GY - P0[1]) * nn[1]
    along = np.clip(s_ / L, -1, 2)
    on = ((along >= 0) & (along <= pr)).astype(np.float32)
    gap = np.exp(-(q / (1.5 + 2.5 * line_open)) ** 2) * on
    disp = np.sign(q) * 3 * line_open * np.exp(-np.abs(q) / 14) * on
    o = cv2.remap(img, (_GX + disp * nn[0]).astype(np.float32), (_GY + disp * nn[1]).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    o = o * (1 - gap[..., None] * 0.85) + BLOODC * 0.6 * gap[..., None]
    if grow > 0:
        rng = np.random.default_rng(14); fld = np.zeros((H // 2, W // 2), np.float32)
        for i in range(30):
            a = rng.uniform(0.02, 0.98)
            if a > pr: continue
            c = P0 + d * a + nn * rng.normal(0, 3)
            r = (12 + 24 * rng.random()) * grow * (1 + 0.5 * smear_u)
            cv2.circle(fld, (int(c[0] / 2), int(c[1] / 2)), max(1, int(r / 2)), 1.0, -1, cv2.LINE_AA)
            if rng.random() < 0.35 * grow:                                             # a bead that runs
                cv2.line(fld, (int(c[0] / 2), int(c[1] / 2)), (int(c[0] / 2), int((c[1] + 90 * grow * rng.random()) / 2)), 1.0, max(1, int(r / 5)), cv2.LINE_AA)
        fld = cv2.GaussianBlur(fld, (0, 0), 2.2); fld = cv2.resize(fld, (W, H)); m = np.clip((fld - 0.40) * 5, 0, 1)
        gx_ = cv2.Sobel(fld, cv2.CV_32F, 1, 0, ksize=7); gy_ = cv2.Sobel(fld, cv2.CV_32F, 0, 1, ksize=7)
        nrm = np.sqrt(gx_ ** 2 + gy_ ** 2) + 1e-6; light = np.clip((-gx_ * 0.5 - gy_ * 0.85) / nrm, 0, 1)
        spec = (light ** 12) * m * np.clip(fld * 2, 0, 1)
        body = BLOODC * (0.55 + 0.55 * np.clip(fld, 0, 1))[..., None]
        o = o * (1 - m[..., None]) + body * m[..., None] + spec[..., None] * 0.85 * BONE
        o = o * (1 - 0.35 * np.clip(np.roll(m, 6, 0) - m, 0, 1))[..., None]          # a thin shadow under each bead
    return np.clip(o, 0, 1)

def scalpel_fx(out, f, s):
    t = f / FPS; pr = cut_progress(t)
    if t < E.T_CUT - 0.40: return out
    grow = smooth((t - E.T_CUT - 0.10) / 0.35)
    out = beads(out, f, grow)
    if t < E.T_CUT + 0.30:                                                            # the blade: enters, draws the cut, leaves
        d = CUT_P1 - CUT_P0; ang = math.degrees(math.atan2(d[1], d[0]))
        if t < E.T_CUT - 0.10: u = (t - (E.T_CUT - 0.40)) / 0.30; pos = CUT_P0 - d * 0.35 * (1 - eout(u, 2)); a = eout(u, 2)
        elif pr < 1: pos = CUT_P0 + d * pr; a = 1.0
        else: u = (t - (E.T_CUT + 0.16)) / 0.14; pos = CUT_P1 + d * 0.5 * ein(clamp(u, 0, 1), 2); a = 1 - clamp(u, 0, 1)
        lay = np.zeros((H, W, 4), np.float32); spr = blade_sprite()
        draw_sprite(lay, spr, pos[0] + math.cos(math.radians(ang)) * 330, pos[1] + math.sin(math.radians(ang)) * 330 - 55, 1.45, ang + 4, 1.0, 0.0, a)
        sh = cv2.GaussianBlur(lay[..., 3], (0, 0), 14)[..., None] * 0.45
        out = out * (1 - np.roll(sh, 30, 0)) * 1.0
        out = out * (1 - lay[..., 3:4]) + lay[..., :3] * lay[..., 3:4]
        gx = pos[0]; gyy = pos[1]                                                     # glint where the blade meets skin
        if 0 < pr < 1: out = add_glow(out, gx, gyy, 40, 0.8, BONE)
    return np.clip(out, 0, 1)

_SL = {}
def slide_glass(w, h):
    key = (w, h)
    if key in _SL: return _SL[key]
    a = np.zeros((h, w), np.float32); cv2.rectangle(a, (0, 0), (w - 1, h - 1), 1.0, -1)
    edge = np.zeros((h, w), np.float32); cv2.rectangle(edge, (2, 2), (w - 3, h - 3), 1.0, 6, cv2.LINE_AA)
    frost = np.zeros((h, w), np.float32); frost[:, int(w * 0.80):] = 1.0
    nz = _lowfreq((h, w), (8, 20), 77) * 0.3 + 0.7
    _SL[key] = (a, cv2.GaussianBlur(edge, (0, 0), 1.2), frost * nz); return _SL[key]

def sample_tr(A, B, j, f, sa, sb, pre=8, post=24):
    """HERO (drop): the slide slams onto the lens and squashes the blood into a smear; then it lifts away into the riff."""
    ang = 8.5
    if j < 0:                                                                         # the slide descends (its shadow over the beads)
        u = (j + pre) / pre; sc = 1.9 - 0.9 * eout(u, 2.2)
        o = A * (1 - 0.35 * u)
        return np.clip(slide_draw(o, f, sc, ang, 0.0, None, u * 0.9), 0, 1)
    if j < 9:                                                                         # contact: the blood spreads under the glass
        v = eout((j + 1) / 9, 2.2)
        A2_ = beads(A, f, 1.0, 1.0, v)
        return np.clip(slide_draw(A2_, f, 1.0, ang, v, None, 1.0), 0, 1)
    u = (j - 8) / (post - 8)                                                          # lift away: up and out, the smear goes with it
    sc = 1.0 + 0.5 * ein(u, 1.6); dy = -H * 0.85 * ein(u, 1.8); dx = W * 0.35 * ein(u, 1.8); rot = ang + 22 * ein(u, 1.5)
    o = B
    return np.clip(slide_draw(o, f, sc, rot, 1.0, (dx, dy), 1 - ein(clamp((u - 0.7) / 0.3, 0, 1), 1)), 0, 1)

_SM = {}
def slide_draw(img, f, sc, ang, smear, off=None, alpha=1.0):
    """a microscope slide, fully on screen: thick glass edges, a sheen, the frosted label end; smear = squashed blood under it."""
    gw, gh = int(W * 0.98 * sc), int(W * 0.98 * sc / 2.8)
    a, edge, frost = slide_glass(gw, gh)
    cx, cy = W * 0.50 + (off[0] if off else 0), H * 0.535 + (off[1] if off else 0)
    M = cv2.getRotationMatrix2D((gw / 2, gh / 2), ang, 1.0); M[0, 2] += cx - gw / 2; M[1, 2] += cy - gh / 2
    def wp(m): return cv2.warpAffine(m, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    A_ = wp(a)[..., None] * alpha; E_ = wp(edge)[..., None] * alpha; F_ = wp(frost)[..., None] * alpha
    sh = cv2.GaussianBlur(np.roll(np.roll(A_[..., 0], 24, 0), 16, 1), (0, 0), 18)[..., None] * 0.45 * (1 - A_)
    o = img * (1 - sh)
    Mi = cv2.invertAffineTransform(M)
    lx = Mi[0, 0] * _GX + Mi[0, 1] * _GY + Mi[0, 2]; ly = Mi[1, 0] * _GX + Mi[1, 1] * _GY + Mi[1, 2]
    sheen = np.exp(-(((lx - ly * 1.4) - gw * 0.30) / (gw * 0.05)) ** 2)[..., None] * A_ * 0.22
    o = o * (1 - A_ * 0.10) + A_ * 0.06 * TEAL + sheen * BONE
    if smear > 0:                                                                     # the squashed blood: a glossy liquid film with viscous fingers
        if "n" not in _SM: _SM["n"] = _lowfreq((H // 2, W // 2), (30, 18), 81) * 0.7 + _lowfreq((H // 2, W // 2), (90, 50), 82) * 0.3
        nz = cv2.resize(_SM["n"], (W, H))
        ang_ = np.arctan2((ly - gh * 0.5) / gh, (lx - gw * 0.40) / gw)
        r = np.sqrt(((lx - gw * 0.40) / (gw * 0.34)) ** 2 + ((ly - gh * 0.5) / (gh * 0.40)) ** 2)
        fing = 0.10 * np.sin(ang_ * 11 + nz * 4) + 0.14 * (nz - 0.5)
        R = smear * (1.0 + fing)
        m = np.clip((R - r) * 30, 0, 1)[..., None] * A_
        thick = np.clip((R - r) * 3, 0, 1)[..., None]
        ref = cv2.remap(img, (_GX + (nz - 0.5) * 24).astype(np.float32), (_GY + (nz - 0.5) * 18).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        blood = ref * 0.12 * (1 - thick) + BLOODC * (0.55 + 0.45 * thick)
        o = o * (1 - m) + blood * m
        o = o + np.exp(-((R - r) * 14) ** 2)[..., None] * A_ * BLOODH * 0.30            # the bright meniscus edge
        o = o + sheen * m * 1.6
    o = o * (1 - F_ * 0.6) + BONE * 0.78 * F_ * 0.6                                    # frosted label end
    o = o + E_ * BONE * 0.85
    return o

# ---------------------------------------------------------------------------- THE ARCHIVE (hook): into the drop, a corridor of slides
def pushin_fx(out, f, s):
    t = f / FPS
    if t < E.ARCH_IN: return out
    if "spot" not in _AR:
        sx, sy, sr = spot_screen(s, E.fe(E.ARCH_IN)); _AR["spot"] = (sx, sy, max(30.0, sr))
    sx, sy, sr = _AR["spot"]; u = clamp((t - E.ARCH_IN) / (E.ARCH_FLY - E.ARCH_IN), 0, 1)
    z = math.exp(3.3 * ein(u, 2.2))
    o = zoom_about(out, sx, sy, z, 0)
    o = radial_blur(o, W / 2, H / 2, 1.0, 1.0 + 0.10 * u, 5) if u > 0.2 else o
    red = smooth((u - 0.55) / 0.45)
    return np.clip(o * (1 - red) + (o * 0.25 + BLOODC * 0.9) * red, 0, 1)

_AR = {}
def archive_slides():
    if "p" in _AR: return _AR["p"]
    rng = np.random.default_rng(66); P = []
    for i in range(160):
        z = rng.uniform(2.0, 60.0); ang = rng.uniform(0, 2 * math.pi); rad = rng.uniform(1.6, 3.4)
        P.append((math.cos(ang) * rad, math.sin(ang) * rad * 1.5, z, rng.uniform(-20, 20), rng.uniform(0.7, 1.0), rng.uniform(0.15, 0.9)))
    _AR["p"] = P; return P

def archive_frame(f):
    """fly down an endless corridor of his blood slides (perspective quads in a ring), fog into teal-black."""
    t = f / FPS; u = clamp((t - E.ARCH_FLY) / (E.ARCH_END - E.ARCH_FLY), 0, 1)
    camz = 26.0 * (u ** 0.85); foc = W * 0.9
    o = np.broadcast_to(DEEP * 1.1, (H, W, 3)).copy()
    o = o + np.exp(-(((_GX - W / 2) / (W * 0.6)) ** 2 + ((_GY - H * 0.45) / (H * 0.45)) ** 2))[..., None] * TEAL * 0.25
    lay = np.zeros((H, W, 3), np.float32); al = np.zeros((H, W), np.float32)
    items = []
    for x, y, z, rot, br, dpos in archive_slides():
        zz = (z - camz) % 60.0
        if zz < 0.8: continue
        items.append((zz, x, y, rot, br, dpos))
    items.sort(key=lambda r: -r[0])
    for zz, x, y, rot, br, dpos in items:
        sx, sy = W / 2 + foc * x / zz, H * 0.45 + foc * y / zz
        hw, hh = foc * 0.75 / zz, foc * 0.27 / zz
        if hw < 2 or sx < -hw * 2 or sx > W + hw * 2 or sy < -hw * 2 or sy > H + hw * 2: continue
        fog = math.exp(-zz / 18.0)
        c, s_ = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        pts = np.array([[sx + (-hw) * c - (-hh) * s_, sy + (-hw) * s_ + (-hh) * c], [sx + hw * c - (-hh) * s_, sy + hw * s_ + (-hh) * c],
                        [sx + hw * c - hh * s_, sy + hw * s_ + hh * c], [sx + (-hw) * c - hh * s_, sy + (-hw) * s_ + hh * c]], np.int32)
        cv2.fillConvexPoly(lay, pts, tuple(float(v) for v in (BONE * 0.10 + TEAL * 0.10) * fog * br), cv2.LINE_AA)
        cv2.fillConvexPoly(al, pts, 0.55 * fog, cv2.LINE_AA)
        cv2.polylines(lay, [pts], True, tuple(float(v) for v in BONE * 0.85 * fog * br), max(1, int(3 * fog + 1)), cv2.LINE_AA)
        cv2.polylines(al, [pts], True, 1.0 * fog, max(1, int(3 * fog + 1)), cv2.LINE_AA)
        dx_ = (dpos - 0.5) * hw * 1.2                                                 # the drop of blood, with its highlight
        dc = (int(sx + dx_ * c), int(sy + dx_ * s_)); R = max(1, int(hh * 0.62))
        cv2.circle(lay, dc, R, tuple(float(v) for v in BLOODC * 1.1 * fog), -1, cv2.LINE_AA); cv2.circle(al, dc, R, 1.0 * fog, -1, cv2.LINE_AA)
        cv2.circle(lay, (dc[0] - R // 3, dc[1] - R // 3), max(1, R // 4), tuple(float(v) for v in BONE * 0.6 * fog), -1, cv2.LINE_AA)
        fx0 = int(sx + hw * 0.62 * c); fy0 = int(sy + hw * 0.62 * s_)                 # frosted label end
        cv2.circle(lay, (fx0, fy0), max(1, int(hh * 0.5)), tuple(float(v) for v in BONE * 0.25 * fog), -1, cv2.LINE_AA)
    lay = cv2.GaussianBlur(lay, (0, 0), 0.7); al = np.clip(cv2.GaussianBlur(al, (0, 0), 0.7), 0, 1)
    o = o * (1 - al[..., None] * 0.6) + lay
    o = o + cv2.GaussianBlur(lay, (0, 0), 12) * 0.8                                    # glow of the glass edges
    return np.clip(snow(o, f, 0.6), 0, 1)

def drop_out(A, B, j, f, sa, sb, post=16):
    """out of the red drop into the corridor: a drop-shaped aperture opens."""
    v = eout((j + 1) / post, 2.0); R = 1400 * v
    rr = np.sqrt((_GX - W / 2) ** 2 + ((_GY - H * 0.45) * 0.8) ** 2)
    m = np.clip((R - rr) / 30, 0, 1)[..., None]
    red = (BLOODC * 0.9 + A * 0.1) * (1 - v * 0.3)
    rim = np.exp(-((rr - R) / 22) ** 2)[..., None] * BLOODH * 0.6
    return np.clip(B * m + red * (1 - m) + rim, 0, 1)

def through_slide(A, B, j, f, sa, sb, pre=18, post=12):
    """one slide flies up to the lens; through its drop, the boat."""
    if j < 0:
        u = (j + pre) / pre; zz = 6.0 - 5.3 * ein(u, 1.7); foc = W * 0.9
        hw, hh = foc * 0.75 / zz, foc * 0.27 / zz
        o = A.copy(); lay = np.zeros((H, W, 3), np.float32); al = np.zeros((H, W), np.float32)
        cx, cy = W / 2, H * 0.45
        pts = np.array([[cx - hw, cy - hh], [cx + hw, cy - hh], [cx + hw, cy + hh], [cx - hw, cy + hh]], np.int32)
        cv2.fillConvexPoly(al, pts, 0.5, cv2.LINE_AA); cv2.polylines(lay, [pts], True, tuple(float(v) for v in BONE * 0.9), 4, cv2.LINE_AA)
        R = hh * 0.62 * (1 + 2.5 * ein(u, 3)); dm = np.clip((R - np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2)) / 3, 0, 1)[..., None]
        Bz = zoom_about(B, W / 2, H * 0.45, 0.6 + 0.4 * ein(u, 2))
        o = o * (1 - al[..., None] * 0.5) + lay
        drop = Bz * np.array([0.55, 0.55, 0.95], np.float32)                           # the boat, seen through blood-tinted glass
        o = o * (1 - dm) + drop * dm + np.exp(-((np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2) - R) / 6) ** 2)[..., None] * BLOODH * 0.5
        return np.clip(o, 0, 1)
    v = eout((j + 1) / post, 2.0)
    return np.clip(B * (1 - 0.35 * (1 - v)) + (1 - v) * BLOODC * 0.35, 0, 1)

def archive_shot(f, s):
    return archive_frame(f)

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
            "sample": (sample_tr, 8, 24), "tape": (tape_tr, 6, 10), "drop_out": (drop_out, 0, 16), "through_slide": (through_slide, 18, 12)})

# ---------------------------------------------------------------------------- graphics: blood spatter on the riff's downbeats
_HT = {}
def spatter_hits(out, f):
    t = f / FPS; k = kt(t)
    if not (E.HDROP + 4 <= k < E.K_SPL): return out
    kb = int((k - E.HDROP) // 4) * 4 + E.HDROP; kk = f - E.fh(kb)
    if kk > 14 or kb == E.HDROP: return out
    if kb not in _HT:
        rng = np.random.default_rng(kb); m = np.zeros((H, W), np.float32); side = (kb // 4) % 3
        cx = [rng.uniform(40, 240), rng.uniform(W - 240, W - 40), rng.uniform(200, W - 200)][side]
        cy = rng.uniform(300, 1250) if side < 2 else rng.uniform(220, 380)
        ang = math.atan2(H * 0.4 - cy, W / 2 - cx) + rng.normal(0, 0.4); r = rng.uniform(16, 26)
        cv2.ellipse(m, (int(cx), int(cy)), (int(r * 1.5), int(r)), math.degrees(ang), 0, 360, 1.0, -1, cv2.LINE_AA)
        for _ in range(int(rng.integers(5, 9))):
            a2 = ang + rng.normal(0, 0.35); L = rng.uniform(40, 160)
            cv2.line(m, (int(cx), int(cy)), (int(cx + L * math.cos(a2)), int(cy + L * math.sin(a2))), 1.0, int(rng.integers(2, 6)), cv2.LINE_AA)
            cv2.circle(m, (int(cx + (L + 10) * math.cos(a2)), int(cy + (L + 10) * math.sin(a2))), int(rng.integers(3, 8)), 1.0, -1, cv2.LINE_AA)
        for _ in range(40):
            a2 = ang + rng.normal(0, 0.9); d = rng.uniform(r, 230)
            cv2.circle(m, (int(cx + d * math.cos(a2)), int(cy + d * math.sin(a2))), int(max(1, rng.uniform(1, 5) * (1 - d / 260))), 1.0, -1, cv2.LINE_AA)
        _HT[kb] = cv2.GaussianBlur(m, (0, 0), 0.8)
    a = (1 if kk < 3 else math.exp(-(kk - 3) / 5)) * 0.92; m = _HT[kb][..., None] * a
    return np.clip(out * (1 - m) + m * BLOODC * 0.95 + m * (np.roll(_HT[kb], -4, 0) - _HT[kb] > 0.3)[..., None] * 0.25, 0, 1)

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

def text103(out, f):
    for tx in E.TEXT:
        if tx["style"] == "cap": out = text_cap(out, f, tx)
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

# ---------------------------------------------------------------------------- frame
def base103(s, f):
    if s.get("graphic") == "archive": return archive_frame(f)
    out = render_shot(s, f)
    if s.get("caustics"): out = caustics(out, f, s["caustics"])
    if s.get("snow"): out = snow(out, f, 0.6)
    if s.get("rain"): out = rain_glass(out, f, 0.8, 0.0)
    if s.get("scalpel"): out = scalpel_fx(out, f, s)
    if s.get("pushin"): out = pushin_fx(out, f, s)
    if s.get("spatter"): out = spatter_hits(out, f)
    return out

_E3 = {}
def edge103(S_, which):
    key = (S_["n"], which)
    if key not in _E3:
        if len(_E3) > 6: _E3.clear()
        fr = S_["f0"] if which == "first" else S_["f1"] - 1
        _E3[key] = base103(S_, fr) if S_.get("graphic") or which == "last" else render_shot(S_, fr, False)
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
    out = text103(out, f)
    if s.get("sink"): out = sink_end(out, f, s)
    out = finish103(out, f)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)

def init_hits():
    HITS.clear()
    HITS.append((E.fh(E.HDROP), 18, 4.0))                                             # the slide slams
    for kb in range(E.HDROP + 8, E.K_SPL, 8): HITS.append((E.fh(kb), 8, 3.0))
    HITS.append((E.fe(E.T_SPLASH), 10, 3.0))
