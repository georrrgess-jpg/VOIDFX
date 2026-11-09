# ============================================================================ v15 — OUT OF TIME (The Flash × Eyedress "Jealous")
# The fastest man alive never has time. "I don't got time" x4 on the beat (the watch, the call, he runs); on the drum
# break TIME STOPS at the moment it all began (the S1 lab strike frozen mid-air, the camera stepping through it on the
# kick fill); on the return TIME RESTARTS (the frozen lightning discharges into his eyes). Then the jealousy he says he
# doesn't feel (Iris, the speed-off, the wind in her hair), EMBLEM CLOCK (the real S5 emblem's bolt lifted off and wound
# round like a clock hand; its sweep brings the next memory), and the loop (time stops once more and restarts on frame 0).
# Look VIOLET HOUR (lifted violet shadows, peach-gold highlights, the suit's red kept rich) with a soft dream bloom.
GOLDL = np.array([0.50, 0.80, 1.00], F32)                  # BGR gold light (lightning)
AMBR = np.array([0.30, 0.56, 1.00], F32)                   # BGR amber
HOT = np.array([0.92, 0.96, 1.00], F32)                    # BGR white-hot
VIO = np.array([0.62, 0.30, 0.46], F32)                    # BGR violet (shadows, haze)
PEACH = np.array([0.62, 0.78, 1.00], F32)                  # BGR peach (bloom)
CRIM = np.array([0.16, 0.12, 0.78], F32)
AMB = AMBR
GOLDW, GOLD2, GOLD, EMBER2 = HOT.copy(), AMBR.copy(), GOLDL.copy(), AMBR.copy()
JASW, JASG, JASY = HOT.copy(), AMBR.copy(), AMBR.copy()
if E.VER == "v15":
    for _s in E.SHOTS:
        _s.setdefault("target", 0.44)

def shift_img(img, dx, dy=0.0):
    M = np.float32([[1, 0, dx], [0, 1, dy]]); return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

_DK = {}
def defocus(img, r):
    if r < 0.6: return img
    if r < 6: return cv2.GaussianBlur(img, (0, 0), r / 2)
    q = 4; sm = cv2.resize(img, (W // q, H // q), interpolation=cv2.INTER_AREA)
    sm = sm + np.clip(sm - 0.58, 0, 1) * 2.2
    rr = int(math.ceil(r / q))
    if rr not in _DK:
        k = np.zeros((2 * rr + 1, 2 * rr + 1), F32); cv2.circle(k, (rr, rr), rr, 1.0, -1, cv2.LINE_AA); _DK[rr] = k / k.sum()
    return np.clip(cv2.resize(cv2.filter2D(sm, -1, _DK[rr]), (W, H), interpolation=cv2.INTER_LINEAR), 0, 1)

def shot_by(name):
    return next(s for s in SHOTS if s["n"] == name)

def e_of(f): return f / FPS / E.HB

# ---- grade: VIOLET HOUR -----------------------------------------------------------------------------------------------
_LUTS = {}
def lutV():
    if "v" not in _LUTS:
        x = np.linspace(0, 1, 1024, dtype=np.float32)
        _LUTS["v"] = (x, PchipInterpolator([0, .05, .20, .50, .80, .95, 1], [0.040, 0.068, 0.200, 0.500, 0.805, 0.935, 0.975])(x).astype(np.float32))
    return _LUTS["v"]

E_BRIGHT15 = {"still": 0.0, "strike": 0.05, "alone": -0.05, "blue": -0.05}
_grade_pre15 = grade
def grade(img, s, f):
    if s.get("look") != "violet": return _grade_pre15(img, s, f)
    g, gains = corr9(s); ev = (s.get("ev") or 0) - 0.45 * E_BRIGHT15.get(s["n"], 0.0)
    lx, ly = lutV()
    if in_unit(img): x = apply_lut3(img, tone_lut(("vio", s["n"], round(ev, 3), float(g), tuple(float(v) for v in gains)), gains, g, ev, lx, ly))
    else:
        x = np.clip(img * gains, 0, 1) ** g
        if ev: x = np.clip(x * 2 ** ev, 0, 1)
        x = np.interp(x, lx, ly).astype(F32)
    B, G, R = (np.ascontiguousarray(x[..., c]) for c in range(3))
    L = B * 0.114 + G * 0.587 + R * 0.299
    hue = (R - G) / (R + 1e-3)
    skin = np.clip(1 - np.abs(hue - 0.22) / 0.22, 0, 1) * np.clip((R - B) * 6, 0, 1) * np.clip(L * 3, 0, 1)
    red = np.clip((R - np.maximum(G, B)) * 3.0 - 0.3, 0, 1) * (1 - skin)                      # the suit keeps its red
    sat = (0.86 + 0.10 * skin + 0.18 * red) * s.get("satk", 1.0)
    sh = (1 - L) ** 2.2; hi = np.clip((L - 0.55) / 0.45, 0, 1) ** 1.4
    shw = (0.055, -0.004, 0.030)                                                              # shadows to violet (BGR)
    hiw = (-0.030, 0.008, 0.032)                                                              # highlights to peach-gold
    o = np.empty(x.shape, F32)
    for c, P in enumerate((B, G, R)):
        o[..., c] = L + (P - L) * sat + sh * shw[c] + hi * hiw[c]
    return np.clip(o, 0, 1, out=o)

# ---- the finish: a soft dream bloom, a faint lens fringe at the edges, fine grain --------------------------------------
_FIN = {}
def _periodic(f, cyc, ph=0.0):
    return math.sin(2 * math.pi * cyc * (f % E.DUR_F) / E.DUR_F + ph)

def edge_w():
    if "ew" not in _FIN:
        r = np.sqrt(((_GX - W / 2) / (W / 2)) ** 2 + ((_GY - H / 2) / (H / 2)) ** 2)
        _FIN["ew"] = np.clip((r - 0.55) / 0.6, 0, 1).astype(F32)[..., None]
    return _FIN["ew"]

def finish15(out, f, s):
    if "v" not in _FIN:
        grain(0, 0.012); _FIN["v"] = np.repeat(0.78 + 0.22 * VIG, 3, axis=2)
    k = ("g", f % 6)
    if k not in _FIN: _FIN[k] = np.repeat(grain(f, 0.011), 3, axis=2)
    o = out
    small = cv2.resize(o, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi_ = np.clip(small.max(2) - 0.62, 0, 1)
    bl = cv2.resize(cv2.GaussianBlur(hi_, (0, 0), 6) * 0.55 + cv2.GaussianBlur(hi_, (0, 0), 22) * 0.45, (W, H))
    addc(o, bl, PEACH, 0.34)                                                                    # the dream bloom
    lift = cv2.resize(cv2.GaussianBlur(small.mean(2), (0, 0), 30), (W, H))
    addc(o, (1 - np.clip(lift * 2.2, 0, 1)) * 0.5, VIO, 0.045)                                  # a violet haze in the darks
    ew = edge_w()                                                                                # a faint lens fringe at the edges
    if True:
        sR = cv2.warpAffine(np.ascontiguousarray(o[..., 2]), np.float32([[1.004, 0, -0.004 * W / 2], [0, 1.004, -0.004 * H / 2]]), (W, H), borderMode=cv2.BORDER_REFLECT)
        sB = cv2.warpAffine(np.ascontiguousarray(o[..., 0]), np.float32([[0.996, 0, 0.004 * W / 2], [0, 0.996, 0.004 * H / 2]]), (W, H), borderMode=cv2.BORDER_REFLECT)
        o[..., 2] = o[..., 2] * (1 - ew[..., 0]) + sR * ew[..., 0]; o[..., 0] = o[..., 0] * (1 - ew[..., 0]) + sB * ew[..., 0]
    o *= _FIN["v"]; o += _FIN[k]
    return np.clip(o, 0, 1, out=o)

# ---- the beat camera: a punch on every kick of the groove (none in the frozen bar and the last shot) -----------------
def last_kick(e):
    """the last strong / soft kick at or before edit half-beat e: (e of the kick, strength)."""
    b = math.floor(e / 8) * 8; best = None
    for bb in (b, b - 8):
        for k in E.KICKS:
            ek = bb + k
            if ek <= e + 1e-6 and (best is None or ek > best[0]): best = (ek, 1.0)
        for k in E.KICKS_SOFT:
            ek = bb + k
            if ek <= e + 1e-6 and (best is None or ek > best[0]): best = (ek, 0.45)
    return best

def cam_live(e):
    return (0.5 <= e < E.E_STOP) or (E.HDROP <= e < 74)              # no punch on frame 0 (the loop lands on it)

def beat_bounce(f):
    e = e_of(f)
    if not cam_live(e): return 1.0
    ek, st_ = last_kick(e); dt = (e - ek) * E.HB
    amp = (0.045 if e >= E.HDROP else 0.030) * st_
    return 1 + amp * math.exp(-dt / 0.085)

def beat_fx(out, f):
    e = e_of(f)
    if not cam_live(e): return out
    ek, st_ = last_kick(e); dt = (e - ek) * E.HB
    if st_ < 1 or dt > 0.05: return out
    k = math.exp(-dt / 0.022) * (1.0 if e >= E.HDROP else 0.6)
    o = radial_blur(out, W / 2, H * 0.46, 1.0, 1.0 + 0.035 * k, 4)
    return np.clip(rgb_split(o, 6 * k) if e >= E.HDROP else o, 0, 1)

def init_hits():
    HITS.clear()

# ---- smoothness: flow on the 24p/30p shots, a per-shot limit for the fast ones (v13) ------------------------------------
def src_weights(s, f):
    pk = s["src"]; fps = E.SRC[pk][1]; U = UNIQ[pk]
    t, u, sp = src_time(s, f); thr = s.get("flowmax", 14)
    def idx(tt, mode):
        kf = tt * fps; i = clamp(bisect.bisect_right(U, kf + 0.3) - 1, 0, len(U) - 1)
        if mode == "hold" or i >= len(U) - 1: return [(U[i], 1.0)]
        i0, i1 = U[i], U[i + 1]; a = clamp((kf - i0) / (i1 - i0), 0.0, 1.0)
        if a < 0.05: return [(i0, 1.0)]
        if a > 0.95: return [(i1, 1.0)]
        if mode == "blend": return [(i0, 1 - a), (i1, a)]
        A0, A1 = FR[(pk, i0)], FR[(pk, i1)]
        if np.abs(A0[::8, ::8].astype(np.float32) - A1[::8, ::8]).mean() > thr:
            if s.get("flowfall") == "blend": return [(i0, 1 - a), (i1, a)]
            return [(i0 if a < 0.5 else i1, 1.0)]
        m0, m1 = A0[::8, ::8].mean(axis=(0, 1)), A1[::8, ::8].mean(axis=(0, 1))
        if np.abs(m0.astype(np.float32) - m1).max() > 6: return [(i0, 1 - a), (i1, a)]
        return [("flow", i0, i1, a)]
    if sp > 1.7:
        K = int(min(7, max(3, round(sp * 2)))); span = 0.5 / FPS * sp; out_ = []
        for j in range(K):
            out_ += [(k, w / K) for k, w in idx(t + (j / (K - 1) - 0.5) * span, "hold")]
        return out_, t, u
    return idx(t, s.get("interp", "hold")), t, u

# ---- ported (v13 / v14), restyled in the v15 palette --------------------------------------------------------------------
def edge_map(img):
    g = cv2.cvtColor((np.clip(img, 0, 1) * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
    g = cv2.GaussianBlur(cv2.resize(g, (W // 2, H // 2), interpolation=cv2.INTER_AREA), (0, 0), 1.6)
    return cv2.resize(cv2.Canny(g, 38, 105), (W, H), interpolation=cv2.INTER_LINEAR)

_CUR = {}
def crop_frac15(c, oy, ox, h, w):
    M = np.float32([[1, 0, -ox], [0, 1, -oy]])
    return cv2.warpAffine(c, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def current_mask(f):
    if "n" not in _CUR:
        rng = np.random.default_rng(31)
        _CUR["n"] = cv2.GaussianBlur(rng.random((H // 4 + 200, W // 4 + 200)).astype(F32), (0, 0), 6)
    nz = _CUR["n"]; off = (f * 1.7) % 180
    c = crop_frac15(nz, off, off * 0.6, H // 4, W // 4)
    c = (c - c.mean()) / (c.std() + 1e-6)
    return cv2.resize(np.clip(0.5 + 0.5 * np.sin(c * 5.0 + f * 0.35), 0, 1), (W, H))

def edge_current15(A, B, j, f, sa, sb, pre=10, post=14):
    """EDGE CURRENT: the picture goes dark and its own outlines carry a crawling current; they morph into the next shot's."""
    cur = 0.4 + 0.6 * current_mask(f)
    if j < 0:
        u = (j + pre) / pre; eA = edge_map(A).astype(F32)
        e = eA if u < 0.6 else eA * (1 - (u - 0.6) / 0.4) + edge_map(B).astype(F32) * ((u - 0.6) / 0.4)
        base = A * (1 - 0.80 * ein(u, 1.4)); amp = 1.2 * ein(u, 1.1)
    else:
        v = (j + 1) / post; e = edge_map(B).astype(F32)
        base = B * (0.20 + 0.80 * eout(v, 1.8)); amp = 1.2 * (1 - eout(v, 1.4))
    return np.clip(base + light_rgb(np.clip(e * cur, 0, 255).astype(np.uint8), amp, HOT, AMB), 0, 1)

def defocus15(img, r):
    """defocus without the jump where the engine's defocus switches from a gaussian to the bokeh disc (at r 6)."""
    if r < 0.6: return img
    g = cv2.GaussianBlur(img, (0, 0), r / 2)
    if r < 3: return g
    w = clamp((r - 3) / 6, 0, 1); return g * (1 - w) + defocus(img, max(r, 6.01)) * w

def focus_rack15(A, B, j, f, sa, sb, pre=10, post=12):
    """FOCUS RACK: the lens racks out to bokeh, the next shot is found in the blur over 8 frames, and racks back in."""
    if j < 0:
        u = (j + pre) / pre; o = defocus15(A, 50 * ein(u, 1.8))
        if j >= -8: o = mixm(o, defocus15(B, 50), np.full((H, W), smooth((j + 9) / 9), F32))
        return o
    v = (j + 1) / post; return defocus15(B, 50 * (1 - smooth(v)))

def whip_up15(A, B, j, f, sa, sb, pre=6, post=8):
    """WHIP UP: a clean tilt-whip upward with real vertical motion blur."""
    if j < 0: u = (j + pre) / pre; o = hblur(shift_img(A, 0, H * 0.45 * ein(u, 2.2)), 2 + 190 * ein(u, 2.0), vertical=True)
    else: v = (j + 1) / post; o = hblur(shift_img(B, 0, -H * 0.45 * (1 - eout(v, 2.2))), 2 + 170 * (1 - eout(v, 2.0)), vertical=True)
    return np.clip(o, 0, 1)

def speed_whip15(A, B, j, f, sa, sb, pre=5, post=7):
    """SPEED WHIP: a real whip pan across the two shots laid side by side (from her to him), with motion blur."""
    q = (j + pre) / (pre + post - 1); p = smooth(clamp(q, 0, 1))
    strip = np.concatenate([A, B], axis=1); x0 = int(round(p * W))
    o = np.ascontiguousarray(strip[:, x0:x0 + W]); sp = math.sin(math.pi * clamp(q, 0, 1))
    o = hblur(o, 2 + 150 * sp)
    xs = np.exp(-((_GX[:1, :] - W * 0.5) / 360.0) ** 2)
    band = np.exp(-((_GY[:, :1] - H * 0.80) / 12.0) ** 2) * xs * sp
    lay = np.zeros((H, W, 3), F32); addc(lay, band, HOT, 0.30); addc(lay, np.exp(-((_GY[:, :1] - H * 0.80) / 50.0) ** 2) * xs * sp, AMBR, 0.16)
    return np.clip(o + lay, 0, 1)

def eye_pos15(s, f):
    fs = face_scr(s, f)
    if fs is None: return W / 2, H * 0.36
    e = min((fs[3], fs[4]), key=lambda q: abs(q[0] - W / 2)); return e[0], e[1]

def light_ring(cx, cy, R, f, seed=0, w=3):
    cv = bolt_canvas(); th = np.linspace(0, 2 * math.pi, 180)
    rr = R * (1 + 0.025 * np.sin(th * 13 + f * 0.9 + seed) + 0.015 * np.sin(th * 31 - f * 1.7))
    cv2.polylines(cv, [(np.stack([cx + rr * np.cos(th), cy + rr * np.sin(th)], 1) * 4).astype(np.int32)], True, 255, w, cv2.LINE_AA, shift=2)
    return cv

def disc_mask(cx, cy, r, soft=2.0):
    m = np.zeros((H, W), F32)
    if r > 0.5: cv2.circle(m, (int(round(cx * 4)), int(round(cy * 4))), int(round(r * 4)), 1.0, -1, cv2.LINE_AA, shift=2)
    return cv2.GaussianBlur(m, (0, 0), soft) if soft > 0 else m

def place15(img, ax, ay, tx, ty, sc):
    """img scaled by sc about its point (ax, ay), which lands on (tx, ty)."""
    M = np.float32([[sc, 0, tx - sc * ax], [0, sc, ty - sc * ay]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

def eye_iris15(A, B, j, f, sa, sb, pre=12, post=14):
    """EYE IRIS: the lightning in his eye flickers round the iris (never past the socket), the pupil opens like an
    aperture with Iris inside it, upright and face-on, and the opening takes the frame as she comes to full size."""
    bf = face_scr(sb, sb["f0"]) if sb.get("face") is not None else None
    bx, by = (bf[0], bf[1]) if bf else (W / 2, H * 0.4)
    if j < 0:
        u = (j + pre) / pre; px, py = eye_pos15(sa, f); Z = 1 + 0.45 * ein(u, 2.0); A2 = zoom_about(A, px, py, Z)
        Ri = 26 * Z; cv = bolt_canvas()
        for k in range(6):
            a = 2 * math.pi * k / 6 + 0.3 * math.sin(f * 0.07 + k); r1 = Ri * (1.25 + 1.1 * ein(u, 1.5))
            put_bolt(cv, (px + Ri * 0.55 * math.cos(a), py + Ri * 0.55 * math.sin(a)), (px + r1 * math.cos(a), py + r1 * math.sin(a)), 9300 + k + 9 * (f // 2), 1, 0.30, 4, 0)
        o = A2
        if u > 0.55:
            w = ein((u - 0.55) / 0.45, 2.0); Rr = Ri * 0.7 * (1 + 4 * w)
            o = mixm(A2, place15(B, bx, by, px, py, 0.22 + 0.25 * w), disc_mask(px, py, Rr, 3))
            cv = np.maximum(cv, light_ring(px, py, Rr, f, 0, 2))
        return np.clip(o + light_rgb(cv, 0.30 + 0.5 * u, HOT, AMB), 0, 1)
    v = (j + 1) / post; px, py = eye_pos15(sa, sa["f1"] - 1)
    cx, cy = px + (bx - px) * smooth(v), py + (by - py) * smooth(v)
    Rr = 26 * 1.45 * 0.7 * 5 + 2300 * ein(v, 1.8); sc = 0.47 + 0.53 * eout(v, 3.5)
    o = mixm(zoom_about(A, px, py, 1.45 * (1 + 0.4 * v)), place15(B, bx, by, cx, cy, sc), disc_mask(cx, cy, Rr, 3))
    return np.clip(o + light_rgb(light_ring(cx, cy, Rr, f, 3, 3), 0.8 * (1 - v) ** 1.2, HOT, AMB), 0, 1)

def time_slice15(A, B, j, f, sa, sb, pre=6, post=10):
    """TIME SLICE: the frame comes apart into tall slivers that slide out in a wave, each a moment later than its
    neighbour (time smeared across the frame), and the next shot slides in behind them; gold seams between them. The
    slivers over a face move as one, so no seam ever splits a face."""
    q = (j + pre) / (pre + post); n = 12; sw = W / n
    fbs = [b_ for b_ in (face_box(sa, sa["f1"] - 1) if sa.get("face") is not None else None,
                         face_box(sb, sb["f0"]) if sb.get("face") is not None else None) if b_]
    cuts = [int(i * sw) for i in range(1, n) if not any(b_[0] - 24 < i * sw < b_[1] + 24 for b_ in fbs)]
    xs = [0] + cuts + [W]
    o = np.empty_like(A); seam = np.zeros((H, W), F32)
    for i in range(len(xs) - 1):
        x0, x1 = xs[i], xs[i + 1]; d = 0.40 * ((x0 + x1) / 2 / W)
        p = eout(clamp((q - d) / 0.55, 0, 1), 2.4); sp = 4 * p * (1 - p)
        dy = int(round(-H * p)) if i % 2 == 0 else int(round(H * p))
        Ai = hblur(A[:, x0:x1], 2 + 70 * sp, vertical=True); Bi = hblur(B[:, x0:x1], 2 + 70 * sp, vertical=True)
        col = np.roll(np.concatenate([Ai, Bi], 0) if dy < 0 else np.concatenate([Bi, Ai], 0), dy, axis=0)
        o[:, x0:x1] = col[:H] if dy < 0 else col[H:]
        if 0 < p < 1 and x0 > 0: seam[:, max(0, x0 - 1):x0 + 2] = sp
    return np.clip(o + light_rgb((seam * 255).astype(np.uint8), 0.7, HOT, AMB), 0, 1)

def afterimage15(A, B, j, f, sa, sb, pre=10, post=10):
    """AFTERIMAGE: the speedster leaves copies of himself behind (crimson to gold); the next shot comes up through them."""
    m = PERSON.get(f)
    if j >= 0:
        v = (j + 1) / post; return np.clip(mixm(A, B, np.full((H, W), smooth(v * 2.5), F32)), 0, 1)
    u = (j + pre) / pre; img = A; step = -90 * ein(u, 1.4); a0 = ein(u, 1.2)
    fig = img * (np.clip(m * 1.3, 0, 1)[..., None] if m is not None else 0.6)
    o = img.copy()
    for k in range(1, 5):
        c = shift_img(fig, step * k); w_ = 0.50 * a0 * (1 - k / 5)
        tint = CRIM * (1 - k / 4) + AMB * (k / 4)
        L = lum8(c); addc(o, L * w_, tint, 1.5)
    if j >= -3: o = mixm(o, B, np.full((H, W), (j + 4) / 4.0 * 0.5, F32))
    return np.clip(o, 0, 1)

def light_leak15(A, B, j, f, sa, sb, pre=10, post=12):
    """LIGHT LEAK: a peach-violet leak floods in from the edge of the lens and the shots cross under its peak."""
    q = (j + pre) / (pre + post); pk = math.sin(math.pi * q)
    mix = smooth((q - 0.35) / 0.30); o = A * (1 - mix) + B * mix
    q4 = np.zeros((H // 4, W // 4), F32)
    for (x0, y0, x1, y1, r, a) in ((1.25, 0.10, 0.55, 0.30, 0.48, 1.0), (-0.25, 0.85, 0.40, 0.62, 0.36, 0.7)):
        x = (x0 + (x1 - x0) * q) * W / 4; y = (y0 + (y1 - y0) * q) * H / 4
        cv2.circle(q4, (int(x), int(y)), int(r * W / 4), a, -1)
    lk = cv2.resize(cv2.GaussianBlur(q4, (0, 0), 40), (W, H))
    lay = np.zeros((H, W, 3), F32); addc(lay, lk, VIO, 0.55 * pk); addc(lay, lk ** 2, PEACH, 0.60 * pk)
    return np.clip(o * (1 + 0.10 * pk) + lay * np.clip(1.1 - lum8(o), 0.2, 1)[..., None], 0, 1)

def card_quad(a_deg, F=2.1 * W):
    """the frame as a card turned a_deg about its vertical centre line, in perspective: its four corners on screen."""
    a = math.radians(a_deg); out = []
    for x, y in ((-W / 2, -H / 2), (W / 2, -H / 2), (W / 2, H / 2), (-W / 2, H / 2)):
        xr, zr = x * math.cos(a), x * math.sin(a); k = F / (F + zr); out.append((W / 2 + xr * k, H / 2 + y * k))
    return np.float32(out)

def turn_away(A, B, j, f, sa, sb, pre=7, post=11):
    """TURN AWAY ("do whatever you want"): he turns his back on her: in the wind of his leaving the frame turns away like
    a card about its centre line, edge-on on the kick, and on its other side he is already running."""
    x0 = pre / (pre + post - 1); x = (j + pre) / (pre + post - 1)                               # exactly 1 on its last frame
    g = 0.5 * ein(x / x0, 2.0) if x < x0 else 0.5 + 0.5 * eout((x - x0) / (1 - x0), 2.2)
    ang = 180 * g; card, a = (A, ang) if ang < 90 else (B, ang - 180)
    src = np.float32([(0, 0), (W, 0), (W, H), (0, H)]); Hm = cv2.getPerspectiveTransform(src, card_quad(a))
    cw = cv2.warpPerspective(card, Hm, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    m = cv2.warpPerspective(np.ones((H, W), F32), Hm, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)[..., None]
    bg = zoom_about(defocus(B, 28), W / 2, H / 2, 1.12) * 0.62 + VIO * 0.05                       # the street beyond, out of focus
    o = bg * (1 - m) + cw * m
    edge = np.clip(cv2.GaussianBlur(m[..., 0], (0, 0), 1.6) - m[..., 0] * 0.0, 0, 1) * (1 - m[..., 0])
    addc(o, edge, PEACH, 0.6 * math.sin(math.radians(min(90, abs(a)))))                         # the card's edge catches the light
    sp = 180 * (0.5 * 2 * (x / x0) / x0 if x < x0 else 0.5 * 2.2 * (1 - (x - x0) / (1 - x0)) ** 1.2 / (1 - x0)) / (pre + post)
    return np.clip(hblur(o, 2 + 3.0 * sp), 0, 1)

def pendulum(A, B, j, f, sa, sb, pre=8, post=16):
    """PENDULUM: the frame hangs like a clock's pendulum from a pivot far above it: it swings out on the kick and the
    next shot swings in on the same rod, runs past centre and settles back (a damped swing), his run already going."""
    PV = (W / 2, -2.5 * H); D = 2 * math.degrees(math.atan((W / 2) / (3.5 * H)))                 # a frame's width at its foot
    def swing(x):
        return 1.10 * smooth(x / 0.72) if x < 0.72 else 1.10 - 0.10 * smooth((x - 0.72) / 0.28)
    x = (j + pre) / (pre + post - 1); p = swing(x)                                             # exactly 1 on its last frame
    dp = (swing(min(1, x + 0.25 / (pre + post))) - swing(max(0, x - 0.25 / (pre + post)))) * D       # degrees in half a frame
    K = int(clamp(abs(dp) / 0.35, 0, 6)) + 1
    bg = zoom_about(defocus(B, 22), W / 2, H / 2, 1.10) * 0.8
    accA = np.zeros((H, W, 4), F32); accB = np.zeros((H, W, 4), F32)
    A4 = np.dstack([A, np.ones((H, W), F32)]); B4 = np.dstack([B, np.ones((H, W), F32)])
    for i in range(K):
        pi_ = p if K == 1 else p + dp / D * (i / (K - 1) - 0.5)
        phA = -D * pi_; phB = phA + D * (1 + 0.45 * (1 - clamp(pi_, 0, 1)))
        for img4, ph, acc in ((A4, phA, accA), (B4, phB, accB)):
            M = cv2.getRotationMatrix2D(PV, ph, 1.0)
            w = cv2.warpAffine(img4, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
            w[..., :3] *= w[..., 3:4]; acc += w
    accA /= K; accB /= K
    o = bg * (1 - accA[..., 3:4]) + accA[..., :3]
    sh = cv2.GaussianBlur(accB[..., 3], (0, 0), 22); sh = np.roll(sh, -14, axis=1) * (1 - accB[..., 3])   # B's shadow on A
    o = o * (1 - 0.22 * sh[..., None])
    return np.clip(o * (1 - accB[..., 3:4]) + accB[..., :3], 0, 1)

# ---- VIBRATE (the watch -> the call): the frame buzzes like a phone ringing, three pulses, the call under the last -------
def vibrate(A, B, j, f, sa, sb, pre=12, post=8):
    """VIBRATE: a call comes in: the picture buzzes three times like a phone on a table (a quick, smooth side-to-side shake
    at 12 Hz with motion blur: one picture, no ghosts), and the call is there on the cut, under the blur of the third buzz."""
    k = j + pre
    pulses = [(0, 4), (6, 4), (11, 6)]                                                        # (start, length) in frames from -pre
    amp = 0.0
    for a_, l_ in pulses:
        if a_ <= k < a_ + l_: amp = math.sin(math.pi * (k - a_ + 0.5) / l_)
    base = A if j < 0 else B
    if amp <= 0: return base
    w_ = 2 * math.pi * 12.0 / FPS; dx = 15 * amp * math.sin(w_ * k); vx = abs(15 * amp * math.cos(w_ * k) * w_)
    return np.clip(hblur(shift_img(base, dx), 3 + 2.2 * vx + 6 * amp), 0, 1)

# ---- STREAK PASS (the call -> he runs): the Flash streaks past the lens; the cut is behind him -------------------------
def streak_pass(A, B, j, f, sa, sb, pre=5, post=7):
    """STREAK PASS: a red-gold blur (him, at speed) crosses in front of the lens left to right, low (chest height, never
    the faces); the shot changes behind it; lightning filaments trail."""
    q = (j + pre) / (pre + post - 1); x = -0.45 * W + 1.9 * W * ein(clamp(q, 0, 1), 1.3)
    cy = H * 0.62; hh = H * 0.30
    yy = (_GY - cy) / hh; body = np.exp(-yy ** 4) * np.clip((_GX - (x - W * 0.55)) / (W * 0.55), 0, 1) * np.clip((x + 60 - _GX) / 60, 0, 1)
    body = body.astype(F32)
    under = mixm(A, B, np.clip((x - _GX) / 80 + 0.5, 0, 1).astype(F32))
    sm = hblur(under, 120)
    o = mixm(under, sm, np.clip(body * 1.4, 0, 1))
    col = CRIM * 0.55 + AMBR * 0.45
    o = o * (1 - 0.55 * body[..., None]) + body[..., None] * col * 0.75
    cv = bolt_canvas()
    for k_ in range(3):
        yk = cy + (k_ - 1) * hh * 0.45
        put_bolt(cv, (x - W * 0.6, yk + 20 * math.sin(f * 0.6 + k_)), (x, yk), 8800 + k_ + 5 * (f // 2), 1, 0.25, 4, 0)
    return np.clip(o + light_rgb(cv, 0.8 * math.sin(math.pi * clamp(q, 0, 1)), HOT, AMB), 0, 1)

# ---- STRIKE CUT (into the lab strike): a bolt strikes down beside him; the lab is under its light -----------------------
def strike_cut(A, B, j, f, sa, sb, pre=6, post=8):
    """STRIKE CUT: lightning strikes down through the frame beside him (never on his face); under its flash the picture
    becomes the S1 lab, where the strike that started it all is already happening."""
    fcs = [(b_[0] + b_[1]) / 2 for b_ in (face_box(sa, sa["f1"] - 1) if sa.get("face") is not None else None,
                                          face_box(sb, sb["f0"]) if sb.get("face") is not None else None) if b_]
    xs = max((W * 0.16, W * 0.84), key=lambda x_: min([abs(x_ - c_) for c_ in fcs] or [0]))     # the side away from both faces
    q = (j + pre) / (pre + post); pk = math.exp(-((q - 0.42) / 0.16) ** 2)
    cv = bolt_canvas()
    if q < 0.75:
        L = clamp(q / 0.40, 0, 1)
        put_bolt(cv, (xs + 60 * math.sin(f), -20), (xs - 40, -20 + (H + 40) * L), 7700 + 3 * (f // 2), 3, 0.32, 7, 2)
    w = smooth(clamp((q - 0.36) / 0.14, 0, 1)); o = A * (1 - w) + B * w
    return np.clip(o * (1 + 0.25 * pk) + light_rgb(cv, 1.0 + 0.6 * pk, HOT, AMB), 0, 1)

# ---- THE STILL (the drum break): time stops on the S1 lab strike --------------------------------------------------------
_ST = {}
def still_layers(s):
    """the frozen frame taken apart in depth: the room (him and the bolts painted out), the frozen bolts as their own
    light, and him (his matte, with its edge for the rim light); the strike point, his chest (the camera's pivot) and
    his face (kept clear of everything)."""
    if "img" not in _ST:
        img, person = base11(s, s["f0"])
        m = np.clip(person if person is not None else np.zeros((H, W), F32), 0, 1).astype(F32)
        lum = lum8(img); q = 4
        fs = face_scr(s, s["f0"]) if s.get("face") is not None else None
        if not fs and s.get("face_hint"): fs = s["face_hint"]
        fm = np.zeros((H, W), F32)
        if fs: cv2.ellipse(fm, (int(fs[0]), int(fs[1])), (int(fs[2] * 0.9), int(fs[2] * 1.2)), 0, 0, 360, 1.0, -1)
        _ST["fmask"] = np.clip(cv2.GaussianBlur(fm, (0, 0), 30) * 1.5, 0, 1)
        mdil = cv2.dilate((m > 0.3).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(F32)
        core = cv2.GaussianBlur(np.clip((lum - 0.70) / 0.20, 0, 1) * (1 - mdil), (0, 0), 1.0)    # the bolts' cores, off him
        _ST["bolt"] = (img * core[..., None]).astype(F32); _ST["bolt_a"] = core.astype(F32)
        mk = ((cv2.resize(mdil, (W // q, H // q)) > 0.2) | (cv2.resize(core, (W // q, H // q)) > 0.06)).astype(np.uint8)
        mk = cv2.dilate(mk, np.ones((3, 3), np.uint8)) * 255
        sm = (np.clip(cv2.resize(img, (W // q, H // q), interpolation=cv2.INTER_AREA), 0, 1) * 255).astype(np.uint8)
        pl = cv2.resize(cv2.inpaint(sm, mk, 9, cv2.INPAINT_TELEA).astype(F32) / 255, (W, H), interpolation=cv2.INTER_LINEAR)
        mkf = cv2.GaussianBlur(cv2.resize(mk.astype(F32) / 255, (W, H)), (0, 0), 5)[..., None]
        _ST["plate"] = (img * (1 - mkf) + pl * mkf).astype(F32)                                   # the room, bolts and him painted out
        _ST["img"] = img; _ST["m"] = cv2.GaussianBlur(m, (0, 0), 1.2)[..., None]
        _ST["edge"] = cv2.GaussianBlur(cv2.morphologyEx((m > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((7, 7), np.uint8)).astype(F32), (0, 0), 3)
        _ST["fc"] = (fs[0], fs[1] + fs[2] * 0.9) if fs else (W / 2, H * 0.55)                     # the camera's pivot: his chest
        c8 = core[::8, ::8] * (1 - fm[::8, ::8]); ys, xs = np.nonzero(c8 > 0.1)
        if len(xs): w_ = c8[ys, xs]; _ST["sp"] = (float((xs * w_).sum() / w_.sum() * 8 + 4), float((ys * w_).sum() / w_.sum() * 8 + 4))
        else: _ST["sp"] = (W * 0.8, H * 0.2)                                                    # the strike point: the frozen bolts
    return _ST

_PT = {}
def still_particles(n=170, seed=1515):
    """suspended droplets of the chemicals and sparks: (x, y) on screen, depth (0.4 near .. 1.6 far), size, kind."""
    if "p" not in _PT:
        rng = np.random.default_rng(seed); p = []
        for i in range(n):
            d = rng.uniform(0.35, 1.7)
            p.append((rng.uniform(-60, W + 60), rng.uniform(-60, H + 60), d, rng.uniform(3.0, 9.0) / d, int(rng.random() < 0.45), rng.uniform(0, 6.28)))
        _PT["p"] = p
    return _PT["p"]

STILL_X = [32, -28, 26, -22, 18, -14, 10, -6, 0]                                                # where the camera steps to on each kick
def still_cam(e):
    """the bullet-time camera: on each kick of the drum fill it steps to a new place in the frozen moment (alternating
    sides, a little closer each time) in 0.13 s, and drifts slowly between the steps. (dx at his depth in px, zoom)."""
    x = 0.0; z = 0.0; prev = 0.0
    for i, ek in enumerate(E.FILL):
        if e < ek: break
        w = eout(clamp((e - ek) * E.HB / 0.10, 0, 1), 3.0)
        x += (STILL_X[i] - prev) * w; z += (0.028 if i % 2 == 0 else -0.016) * w; prev = STILL_X[i]
    u = clamp((e - E.FILL[0]) / 8, 0, 1)
    return x + 6 * math.sin(2 * math.pi * 0.5 * u), 1.0 + z + 0.004 * u

def fill_pulse(e):
    p = 0.0
    for ek in E.FILL:
        d = (e - ek) * E.HB
        if d >= 0: p = max(p, math.exp(-d / 0.10))
    return p

def lens_drop(o, x, y, r, sp, blur=0.0):
    """a hanging drop of the chemicals as a real little lens: the scene behind it seen through it, upside down and
    magnified, a darker fresnel rim, a specular highlight, and the strike's gold caught on the side facing the bolts."""
    x0, y0, x1, y1 = int(x - r - 2), int(y - r - 2), int(x + r + 3), int(y + r + 3)
    if x1 <= 0 or y1 <= 0 or x0 >= W or y0 >= H or r < 3: return
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    gx, gy = np.meshgrid(np.arange(xa, xb, dtype=F32), np.arange(ya, yb, dtype=F32))
    dx, dy = gx - x, gy - y; rho = np.sqrt(dx * dx + dy * dy) / r
    mx = np.clip(x - dx * 0.55 * (1 + 0.6 * rho ** 2), 0, W - 1).astype(F32); my = np.clip(y - dy * 0.55 * (1 + 0.6 * rho ** 2), 0, H - 1).astype(F32)
    inside = cv2.remap(o, mx, my, cv2.INTER_LINEAR) * (0.82 + 0.25 * (1 - rho ** 3))[..., None]
    a = np.clip((1.0 - rho) * r / 1.2, 0, 1)[..., None]
    ang = math.atan2(sp[1] - y, sp[0] - x); gl = np.clip(1 - np.abs(rho - 0.82) / 0.12, 0, 1) * np.clip(np.cos(np.arctan2(dy, dx) - ang), 0, 1) ** 2
    hx, hy = x - 0.38 * r, y - 0.40 * r; spec = np.exp(-(((gx - hx) ** 2 + (gy - hy) ** 2) / (0.13 * r) ** 2))
    patch = inside + gl[..., None] * AMBR * 0.9 + spec[..., None] * 0.9
    if blur > 0.5: patch = cv2.GaussianBlur(patch, (0, 0), blur); a = cv2.GaussianBlur(a, (0, 0), blur)[..., None] if a.ndim == 3 and a.shape[2] == 1 else a
    sub = o[ya:yb, xa:xb]; o[ya:yb, xa:xb] = sub * (1 - a) + patch * a

def still_fx(s, f):
    """THE STILL (bullet time): time stops at the moment the bolt hits him, his hand thrown up against it. The frozen
    moment is taken apart in depth (the room, the frozen bolts, him, the hanging drops) and the camera steps through it
    on each kick of the drum fill, the layers sliding against each other; the room drains to a cold steel grey while the
    bolts stay molten gold, throw rays through the room behind him and rim his edge; the drops of the chemicals hang
    in the air as real little lenses; in the last beat the frozen lightning starts to tremble and crackle."""
    L = still_layers(s); e = e_of(f); k = f - s["f0"]; cx, cy = W / 2, H / 2; t = k / FPS          # pivot: the frame centre (matches the strike's end)
    dx, zc = still_cam(e); Z0 = 1.06
    def tf(img, p):
        return zoom_about(shift_img(img, dx * p), cx, cy, Z0 * (1 + (zc - 1) * p))
    a = 0.68 * smooth(clamp(k / 10, 0, 1)); pl = fill_pulse(e)
    def drain(img):
        lum = lum8(img)[..., None]
        g = lum * np.array([1.22, 1.02, 0.80], F32) * (1 - lum) + lum * np.array([1.0, 0.98, 0.95], F32) * lum   # steel: teal shadows, silver highs
        o_ = img * (1 - a) + g * a
        return np.clip((o_ - 0.40) * (1 + 0.32 * a) + 0.40, 0, 1)
    tr = 0.0
    if e > 38.9: tr = smooth((e - 38.9) / 1.1)                                                   # the frozen lightning trembles
    jit = tr * 2.2 * math.sin(2 * math.pi * 12 * t)
    P = drain(tf(L["plate"], 0.45)) * (1 - a * (0.20 + 0.9 * (1 - VIG)))                     # the room sinks back, darker at the edges
    Bl = zoom_about(shift_img(L["bolt"], dx * 0.75 + jit), cx, cy, Z0 * (1 + (zc - 1) * 0.75))
    Ba = lum8(Bl)
    M = tf(L["m"][..., 0], 1.0)[..., None]; Hm = drain(tf(L["img"], 1.0))
    fmk = tf(L["fmask"], 1.0)[..., None]
    # the bolts and their glow, behind him
    Bg = lum8(Bl)[..., None] * AMBR * 0.95                                                       # molten gold
    glow = cv2.GaussianBlur(Bg, (0, 0), 16); wide = cv2.GaussianBlur(Bg, (0, 0), 90)
    o = P * (1 - np.clip(lum8(Bl)[..., None] * 1.5, 0, 0.8)) + (Bg * (0.95 + 0.45 * pl + 0.4 * tr * (0.5 + 0.5 * math.sin(f * 2.3))) + glow * (0.55 + 0.4 * pl)) * (1 - M)
    o = o + wide * 1.5 * (1 - fmk)                                                              # the bolts' warm light falls through the room
    # god rays streaming out of the frozen bolts through the room (behind him, never on his face)
    q = 4; bq = cv2.resize(Ba, (W // q, H // q), interpolation=cv2.INTER_AREA)
    sx, sy = L["sp"]; zb = Z0 * (1 + (zc - 1) * 0.75); sxq, syq = (cx + (sx + dx * 0.75 - cx) * zb) / q, (cy + (sy - cy) * zb) / q
    acc = np.zeros_like(bq); ws = 0.0
    for i in range(16):
        M_ = cv2.getRotationMatrix2D((sxq, syq), 0, 1.0 + 0.05 * i); d_ = 0.88 ** i
        acc += cv2.warpAffine(bq, M_, (W // q, H // q), flags=cv2.INTER_LINEAR, borderValue=0) * d_; ws += d_
    rays = cv2.resize(cv2.GaussianBlur(acc / ws, (0, 0), 1.2), (W, H))[..., None]
    o = o + rays * AMBR * (1.35 + 0.6 * pl) * (1 - M) * (1 - fmk)
    # him, with the bolts' light wrapping round his edge (not his face)
    rim = tf(L["edge"], 1.0)[..., None] * cv2.GaussianBlur(Ba, (0, 0), 40)[..., None] * 3.0 * (1 - fmk)
    o = o * (1 - M) + Hm * M + rim * HOT * (0.6 + 0.4 * pl)
    o = np.clip(o, 0, 1)
    # the hanging drops and sparks (three depths, parallax; never in front of his face)
    fb = face_box(s, s["f0"]) if s.get("face") is not None else None
    if not fb and s.get("face_hint"): h_ = s["face_hint"]; fb = (h_[0] - h_[2] * 0.75, h_[0] + h_[2] * 0.75, h_[1] + h_[2] * 0.85)
    if fb: fb = (cx + (fb[0] - cx) * Z0 * zc + dx, cx + (fb[1] - cx) * Z0 * zc + dx, cy + (fb[2] - cy) * Z0 * zc)
    q4 = np.zeros((H // 2, W // 2), F32); qs = np.zeros((H // 2, W // 2), F32); lens = []
    for (x, y, d, r, kind, ph) in still_particles():
        p_ = 1.0 / d; zz = Z0 * (1 + (zc - 1) * p_)
        px = cx + (x - cx) * zz + dx * p_ + 8 * math.sin(t * 1.1 + ph) + tr * 1.5 * math.sin(2 * math.pi * 11 * t + ph)
        py = cy + (y - cy) * zz + 10 * t / d
        if fb and fb[0] - 50 < px < fb[1] + 50 and py < fb[2] + 60: continue                  # nothing hangs in front of his face
        rr = max(1.0, r * zz * 0.5)
        if kind: cv2.circle(qs, (int(px * 2), int(py * 2)), int(rr * 2), 1.0, -1, cv2.LINE_AA, shift=2)
        elif d < 0.80 and len(lens) < 4: lens.append((px, py, rr * 3.0, d))
        else: cv2.circle(q4, (int(px * 2), int(py * 2)), int(rr * 3.0), 0.55, -1, cv2.LINE_AA, shift=2)
    dro = cv2.resize(cv2.GaussianBlur(q4, (0, 0), 0.8), (W, H)); spk = cv2.resize(cv2.GaussianBlur(qs, (0, 0), 0.6), (W, H))
    addc(o, dro, np.array([0.95, 0.88, 0.92], F32), 0.40); addc(o, cv2.GaussianBlur(spk, (0, 0), 5), AMBR, 0.9 * (0.6 + 0.4 * pl)); addc(o, spk, HOT, 0.9)
    for (px, py, rr, d) in sorted(lens, key=lambda q_: -q_[3]):
        if fb and fb[0] - 60 < px < fb[1] + 60 and py < fb[2] + 70: continue
        lens_drop(o, px, py, rr, (sx, sy), blur=max(0.0, (0.55 - d) * 12))
    # the step: a burst of motion blur along the camera's move
    v = still_cam(e + 0.06)[0] - still_cam(e - 0.06)[0]
    if abs(v) > 1.5: o = hblur(o, 2 + abs(v) * 1.6)
    return np.clip(o, 0, 1)

def time_stop(A, B, j, f, sa, sb, pre=4, post=14):
    """TIME STOPS: on the first kick of the break the freeze spreads out from the strike as a ring: behind it the colour
    drains and everything hangs still (the still's own frames do the rest)."""
    if j < 0: return A
    v = (j + 1) / post; L = still_layers(sb); cx, cy = L["sp"]
    R = 60 + 2600 * eout(v, 2.0)
    d = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2)
    m = np.clip((R - d) / 320 + 0.5, 0, 1).astype(F32)                                         # the stillness spreads out from the bolts
    full = edge15(shot_by("strike"), "last")
    return np.clip(mixm(full, B, m), 0, 1)

# ---- TIME RESTARTS (the return): the frozen lightning discharges; a shockwave carries his eyes in -----------------------
def time_restart(A, B, j, f, sa, sb, pre=14, post=24):
    """TIME RESTARTS: the frozen lightning discharges: the bolts flare and spill their light through the room (never on
    his face) and the whole frozen moment is pulled into the strike; at the peak of that pull time is moving again, and
    his eyes, full of lightning, come out of it as the colour floods back."""
    L = still_layers(sa); cx, cy = L["sp"]; nf = (1 - L["fmask"])[..., None]
    if j < 0:
        u = (j + pre) / pre
        lum = lum8(A); hot = np.clip((lum - 0.62) / 0.25, 0, 1)[..., None] * nf
        glow = cv2.GaussianBlur(hot[..., 0], (0, 0), 8 + 46 * u)[..., None] * nf
        o = A * (1 + 2.2 * ein(u, 1.4) * hot) + glow * AMBR * (1.9 * ein(u, 1.3))                  # from nothing: no step at its start
        return np.clip(radial_blur(np.clip(o, 0, 1), cx, cy, 1.0, 1.0 + 0.16 * ein(u, 2.4), 7), 0, 1)
    v = (j + 1) / post; k = 0.16 * (1 - eout(v, 2.2))
    Bz = zoom_about(B, W / 2, H * 0.42, 1.0 + 0.07 * (1 - eout(v, 2.0)))
    lumB = lum8(Bz)[..., None]; sat = smooth(clamp(v / 0.55, 0, 1))
    Bc = Bz * sat + lumB * np.array([1.08, 0.99, 0.92], F32) * (1 - sat)                         # the colour floods back
    w = smooth(clamp((j + 1) / 6, 0, 1))
    if w < 1:
        Ab = edge15(sa, "last"); lumA = lum8(Ab); hotA = np.clip((lumA - 0.62) / 0.25, 0, 1)[..., None] * nf
        Ab = np.clip(Ab * (1 + 2.2 * hotA) + cv2.GaussianBlur(hotA[..., 0], (0, 0), 54)[..., None] * nf * AMBR * 1.9, 0, 1)
        Bc = Ab * (1 - w) + Bc * w
    o = radial_blur(Bc, W / 2, H * 0.42, 1.0, 1.0 + k, 7) if k > 0.004 else Bc
    return np.clip(o + AMBR * 0.18 * (1 - eout(v, 1.6)), 0, 1)

# ---- WIND GUST (he tears off -> her hair blows): the wind of his passing carries the next shot in -----------------------
def wind_gust(A, B, j, f, sa, sb, pre=6, post=10):
    """WIND GUST: the wind of his passing: the picture is shoved sideways in the direction he ran, smeared and buffeted
    (turbulent air), with grit streaking across, and her shot is carried in on the same gust, her hair still blowing."""
    q = (j + pre) / (pre + post - 1); p = smooth(clamp(q, 0, 1)); sp = math.sin(math.pi * clamp(q, 0, 1))
    strip = np.concatenate([B, A], axis=1); x0 = int(round((1 - p) * W))
    o = np.ascontiguousarray(strip[:, x0:x0 + W])
    if sp > 0.05:
        wob = (np.sin(_GY[:, :1] / 37.0 + f * 0.9) * 14 + np.sin(_GY[:, :1] / 11.0 - f * 1.3) * 5) * sp
        mx = (_GX + wob).astype(F32); my = _GY.astype(F32)
        o = cv2.remap(o, np.ascontiguousarray(np.broadcast_to(mx, (H, W))).astype(F32), my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        o = hblur(o, 2 + 130 * sp)
    rng = np.random.default_rng(4400 + f); q2 = np.zeros((H // 2, W // 2), F32)
    for _ in range(int(40 * sp)):
        y = rng.uniform(0, H // 2); x = rng.uniform(0, W // 2); L_ = rng.uniform(30, 120) * sp
        cv2.line(q2, (int(x * 4), int(y * 4)), (int((x + L_) * 4), int(y * 4)), float(rng.uniform(0.3, 0.8)), 1, cv2.LINE_AA, shift=2)
    lay = np.zeros((H, W, 3), F32); addc(lay, cv2.resize(cv2.GaussianBlur(q2, (0, 0), 0.8), (W, H)), PEACH, 0.35)
    return np.clip(o + lay, 0, 1)

# ---- EMBLEM CLOCK (the emblem transition; the signature): the real S5 bolt lifted off and wound like a clock hand -------
EC_PRE, EC_POST = 80, 22
def emb15_src(t):
    T = E.EMB15_TRACK; ts = [a_[0] for a_ in T]
    return float(np.interp(t, ts, [a_[1] for a_ in T])), float(np.interp(t, ts, [a_[2] for a_ in T]))

def emb15_screen(s, f):
    t, _, _ = src_time(s, f); x, y = emb15_src(t); X, Y, sc = to_screen(s, f, x, y); return X, Y, E.EMB15_R * sc

def bolt_lift(A, ex, ey, R):
    """the real bolt lifted off the emblem: the traced polygon (EMB15_BOLT; outside the disc only the bolt's own gold, not
    the suit or the black rim it crosses), and the emblem with the bolt filled in from its own white disc and the suit."""
    m_ = 1.6 * R; x0, y0, x1, y1 = max(0, int(ex - m_)), max(0, int(ey - m_)), min(W, int(ex + m_) + 1), min(H, int(ey + m_) + 1)
    sub = np.clip(A[y0:y1, x0:x1], 0, 1); Bc, Gc, Rc = sub[..., 0], sub[..., 1], sub[..., 2]
    gx, gy = _GX[y0:y1, x0:x1] - ex, _GY[y0:y1, x0:x1] - ey; rho = np.sqrt(gx * gx + gy * gy) / R
    poly = np.array([(ex + x * R - x0, ey + y * R - y0) for x, y in E.EMB15_BOLT], F32)
    mk = np.zeros(sub.shape[:2], np.uint8); cv2.fillPoly(mk, [np.int32(np.round(poly * 4))], 255, cv2.LINE_AA, shift=2)
    mkf = mk.astype(F32) / 255
    suit = (Rc > 0.22) & (Gc / (Rc + 1e-3) < 0.45); dark = sub.max(2) < 0.16
    mkf = mkf * (1 - ((rho > 0.86) & (suit | dark)).astype(F32))
    hole = cv2.dilate((mk > 40).astype(np.uint8), np.ones((9, 9), np.uint8))
    tel = cv2.inpaint((sub * 255).astype(np.uint8), hole * 255, 5, cv2.INPAINT_TELEA).astype(F32) / 255
    wd = ((rho < 0.82) & (sub.min(2) > 0.5) & (hole == 0)).astype(F32); sg = 0.12 * R              # the white face, smoothly
    den = cv2.GaussianBlur(wd, (0, 0), sg); disc = cv2.GaussianBlur(sub * wd[..., None], (0, 0), sg) / np.maximum(den, 1e-3)[..., None]
    ins = (np.clip((0.86 - rho) / 0.05, 0, 1) * np.clip(den / 0.05, 0, 1))[..., None]
    filled = np.where(hole[..., None] > 0, tel * (1 - ins) + disc * ins, sub).astype(F32)
    alpha = cv2.GaussianBlur(mkf, (0, 0), 0.7)
    return (x0, y0, x1, y1), filled, np.dstack([sub, alpha])

def ec_cam(sa, f, P_):
    ex, ey, er = emb15_screen(sa, f); s_ = 1 + 1.25 * P_
    tx, ty = ex + (W / 2 - ex) * smooth(P_), ey + (H * 0.52 - ey) * smooth(P_)
    return np.float32([[s_, 0, tx - s_ * ex], [0, s_, ty - s_ * ey]]), ex, ey, er, tx, ty, s_

def ec_theta(sa, jj, pre=EC_PRE, post=EC_POST):
    """the hand's angle at transition time jj (fractional frames from the cut): ticks on the kicks (30 deg each), then the
    winding, then the reveal sweep. Returns (angle, sweep so far, post progress)."""
    if jj < 0: u = (jj + pre) / pre; e = e_of(sa["f1"] + jj)
    else: u = 1.0; e = e_of(sa["f1"] - 1)
    th = 0.0; e0 = (sa["f1"] - pre) / FPS / E.HB; e1 = e0 + 0.40 * pre / FPS / E.HB
    for ek in [x for x in np.arange(math.floor(e0), e1 + 0.01, 0.5) if (x % 8) in E.KICKS and e0 <= x <= e1]:
        if e >= ek: th += 30 * eout(clamp((e - ek) * E.HB / 0.10, 0, 1), 3)
    th += 540 * ein(clamp((u - 0.40) / 0.38, 0, 1), 2.2)                                         # winding
    sw = clamp((u - 0.78) / 0.22, 0, 1) if jj < 0 else 1.0
    sw_post = clamp((jj + 1) / post, 0, 1) if jj >= 0 else 0.0
    sweep = 360 * (0.62 * smooth(sw) + 0.38 * smooth(sw_post))                                    # the reveal sweep
    return th + sweep, sweep, sw_post

def emblem_clock(A, B, j, f, sa, sb, pre=EC_PRE, post=EC_POST):
    """EMBLEM CLOCK: the emblem is the clock. Its real gold bolt lifts off the white disc and ticks round on the kicks like
    a clock hand; the camera pushes in on it, twelve gold marks come up round the face and the hand winds faster; then one
    full sweep: everything behind the hand is the next memory, and we are through."""
    if j < 0:
        u = (j + pre) / pre; f_ = f
    else:
        u = 1.0; f_ = sa["f1"] - 1
    P_ = smooth(clamp((u - 0.20) / 0.62, 0, 1)) if j < 0 else 1.0
    M, ex, ey, er, tx, ty, s_ = ec_cam(sa, f_, P_)
    if j >= 0:
        v = (j + 1) / post; s2 = 1 + 0.9 * ein(v, 1.6); M = M.copy(); M[:, :2] *= s2; M[0, 2] = tx - s_ * s2 * ex; M[1, 2] = ty - s_ * s2 * ey; s_ = s_ * s2
    (x0, y0, x1, y1), filled, bolt = bolt_lift(A, ex, ey, er)
    Af = A.copy(); Af[y0:y1, x0:x1] = filled
    lift = smooth(clamp(u / 0.12, 0, 1))
    Ac = cv2.warpAffine(Af if lift > 0 else A, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    th_total, sweep, sw_post = ec_theta(sa, j, pre, post)
    # the bolt, rotated about the emblem centre, through the camera, with a 180-degree shutter's rotational blur
    bw = np.zeros((H, W, 4), F32); bw[y0:y1, x0:x1] = bolt; bw[..., :3] *= bw[..., 3:4]
    t_a, t_b = ec_theta(sa, j - 0.25, pre, post)[0], ec_theta(sa, j + 0.25, pre, post)[0]
    K = int(clamp(abs(t_b - t_a) / 2.5, 0, 12)) + 1; bc = np.zeros((H, W, 4), F32)
    for i in range(K):
        th_i = th_total if K == 1 else t_a + (t_b - t_a) * i / (K - 1)
        Rm = cv2.getRotationMatrix2D((ex, ey), -th_i, 1.0)
        Mt = np.vstack([M, [0, 0, 1]]) @ np.vstack([Rm, [0, 0, 1]])
        bc += cv2.warpAffine(bw, Mt[:2].astype(F32), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    bc /= K
    R_s = er * s_
    # the reveal behind the hand (a clock wipe from the pivot)
    o = Ac
    if sweep > 0:
        ang = (np.degrees(np.arctan2(_GY - ty, _GX - tx)) - E.EMB15_TIP_DEG - (th_total - sweep)) % 360
        m = np.clip((sweep - ang) / 4 + 0.5, 0, 1).astype(F32) * (sweep > 0)
        if sweep >= 359.5: m[:] = 1
        o = mixm(Ac, B, m)
        a_lead = math.radians(E.EMB15_TIP_DEG + th_total)
        d_perp = np.abs((_GX - tx) * math.sin(a_lead) - (_GY - ty) * math.cos(a_lead))
        along = ((_GX - tx) * math.cos(a_lead) + (_GY - ty) * math.sin(a_lead)) > 0
        blade = (np.exp(-(d_perp / 5.0) ** 2) * along).astype(F32) * (1 - (sw_post if j >= 0 else 0))
        addc(o, blade, HOT, 0.9); addc(o, cv2.GaussianBlur(blade, (0, 0), 14), AMBR, 0.9)
    # the twelve marks and the glow of the face
    if 0.30 < u and (j < 0 or sw_post < 1):
        cvm = bolt_canvas(); am = smooth(clamp((u - 0.30) / 0.25, 0, 1)) * (1 - (sw_post if j >= 0 else 0))
        for i in range(12):
            a = math.radians(i * 30)
            p0 = (tx + math.cos(a) * R_s * 0.74, ty + math.sin(a) * R_s * 0.74); p1 = (tx + math.cos(a) * R_s * 0.84, ty + math.sin(a) * R_s * 0.84)
            cv2.line(cvm, (int(p0[0] * 4), int(p0[1] * 4)), (int(p1[0] * 4), int(p1[1] * 4)), 255, max(2, int(R_s / (28 if i % 3 == 0 else 45))), cv2.LINE_AA, shift=2)
        mk_face = disc_mask(tx, ty, R_s * 0.92, 2) * (1 - (m if sweep > 0 else 0))
        o = np.clip(o + light_rgb(cvm, 0.95 * am, GOLDL, AMBR), 0, 1)
        o = o + mk_face[..., None] * PEACH * 0.10 * am
    if j >= 0: lift *= 1 - smooth(clamp(((j + 1) / post) / 0.65, 0, 1))                       # the hand passes the lens and is gone
    o = o * (1 - bc[..., 3:4] * lift) + bc[..., :3] * lift
    return np.clip(o, 0, 1)

# ---- the loop: time stops once more on the e76 kick, then REWIND flies back past the edit's memories into frame 0 --------
F_STOP = int(round(E.LOOP_E0 * E.HB * FPS)); F_REW = int(round(E.LOOP_E1 * E.HB * FPS))
LOOP_N = E.DUR_F - F_STOP
def frame_virtual(fv):
    s0 = SHOTS[0]; out, _ = base15(s0, fv)
    return out

_LC = {}
def rew_card(name):
    """a memory for the rewind: the shot's own picture at its middle (the emblem before its clock starts)."""
    if name not in _LC:
        s_ = shot_by(name); fm = (s_["f0"] + s_["f1"]) // 2
        if name == "emblem": fm = s_["f0"] + 14
        _LC[name] = np.clip(base15(s_, fm)[0], 0, 1).astype(F32)
    return _LC[name]

def stopped(img, s, f, a):
    """time stopped: the colour drains to the cool grey of the drum break, the lights in the lenses stay, and the drops
    and sparks hang in the air again (never in front of his face)."""
    lum = lum8(img); hot = np.clip((lum - 0.70) / 0.2, 0, 1)[..., None]
    gray = lum[..., None] * np.array([1.10, 0.99, 0.90], F32)
    o = img * (1 - 0.62 * a * (1 - hot)) + gray * (0.62 * a * (1 - hot)) + VIO * 0.045 * a
    if a <= 0.01: return o
    fb = face_box(s, f) if s.get("face") is not None else None; t = (f - F_STOP) / FPS
    q4 = np.zeros((H // 2, W // 2), F32); qs = np.zeros((H // 2, W // 2), F32)
    for (x, y, d, r, kind, ph) in still_particles():
        px = x + 9 * math.sin(t * 1.1 + ph) - 18 * t / d; py = y + 14 * t / d
        if fb and fb[0] - 40 < px < fb[1] + 40 and py < fb[2] + 50: continue
        rr = max(1.0, r * 0.5)
        if kind: cv2.circle(qs, (int(px * 2), int(py * 2)), int(rr * 2), 1.0, -1, cv2.LINE_AA, shift=2)
        else: cv2.circle(q4, (int(px * 2), int(py * 2)), int(rr * 3.0), 0.55, -1, cv2.LINE_AA, shift=2)
    dro = cv2.resize(cv2.GaussianBlur(q4, (0, 0), 0.8), (W, H)); spk = cv2.resize(cv2.GaussianBlur(qs, (0, 0), 0.6), (W, H))
    addc(o, dro, np.array([0.95, 0.85, 0.92], F32), 0.40 * a); addc(o, cv2.GaussianBlur(spk, (0, 0), 5), AMBR, 0.7 * a); addc(o, spk, HOT, 0.7 * a)
    return np.clip(o, 0, 1)

def rew_cam(t):
    """the camera's travel down the corridor (0 at the start, 1 at the end): starts from rest and lands at rest."""
    t = clamp(t, 0, 1); return t * t * t * (t * (6 * t - 15) + 10)

_RBG = {}
def rew_bg():
    """the corridor's own light: deep violet at the walls, a warm peach glow down at the far end where frame 0 waits."""
    if "bg" not in _RBG:
        r = np.sqrt((_GX - W / 2) ** 2 + ((_GY - H / 2) * 0.75) ** 2) / W
        g = np.exp(-(r / 0.42) ** 2)[..., None]
        _RBG["bg"] = (np.array([0.16, 0.06, 0.11], F32) * (1 - g) + np.array([0.42, 0.52, 0.72], F32) * g).astype(F32)
    return _RBG["bg"]

def rew_quad(X, Y, z, c, yaw, pitch):
    """the four screen corners of a frame-sized card centred at (X, Y, z) (screen widths), turned by yaw/pitch."""
    hw, hh = 0.5, 0.5 * H / W; out = []
    for x, y in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)):
        x1, z1 = x * math.cos(yaw), x * math.sin(yaw)
        y2, z2 = y * math.cos(pitch), z1 + y * math.sin(pitch)
        d = z + z2 - c
        if d < 0.06: return None
        out.append((W / 2 + (X + x1) / d * W, H / 2 + (Y + y2) / d * W))
    return np.float32(out)

def loop_out(img, f, s):
    """THE LOOP (REWIND): on the e76 kick time stops once more (the colour drains, the drops hang, the lenses hold their
    light). Then it runs backwards: the camera flies forward through the frozen moment into a corridor of the edit's
    memories, hung along the walls in perspective and turned toward us (the fire, the emblem, Iris, his eyes, the
    strike, the run, newest first), a gold thread of time spiralling along the walls and the frozen sparks streaming
    past as light; at the far end, visible all the way, frame 0 grows, settles and fills the frame: the next "I don't
    got time"."""
    if f < F_REW: return img
    o = img
    t = (f - F_REW) / (E.DUR_F - 1 - F_REW)
    under = frame_virtual(f - E.DUR_F)
    if t >= 1: return under
    names = E.REW_CARDS; N = len(names) + 1; D = 0.85; zN = 1 + N * D; cE = zN - 1
    c = cE * rew_cam(t); c_prev = cE * rew_cam(t - 1.0 / (E.DUR_F - 1 - F_REW))
    end = smooth(clamp((t - 0.72) / 0.28, 0, 1))
    w_end = smooth(clamp((t - 0.40) / 0.45, 0, 1))                                             # the walls: the last moment stretched, then frame 0's own light
    walls = zoom_about(defocus(o, 34), W / 2, H / 2, 1.0 + 2.2 * rew_cam(t)) * np.array([1.05, 0.80, 0.85], F32) * 0.55
    if w_end > 0: walls = walls * (1 - w_end) + zoom_about(defocus(under, 26), W / 2, H / 2, 1.20 - 0.16 * rew_cam(t)) * 0.85 * w_end
    out = walls * 0.75 + rew_bg() * 0.40
    # the gold thread of time spiralling along the corridor walls
    cv = np.zeros((H // 2, W // 2), np.uint8); pts = []
    for i in range(240):
        sl = i / 239 * (N + 0.4); zz = 1 + sl * D
        if zz - c < 0.10: continue
        th_ = math.radians(200 - 62 * sl); rad = 1.15 - 0.53 * smooth(clamp((sl - (N - 1.2)) / 1.2, 0, 1))
        d = zz - c; pts.append((W / 2 + rad * math.sin(th_) / d * W, H / 2 + rad * 1.25 * math.cos(th_) / d * W, d))
    for (x0, y0, d0), (x1, y1, d1) in zip(pts[:-1], pts[1:]):
        if max(abs(x0 - x1), abs(y0 - y1)) > 600: continue
        cv2.line(cv, (int(x0 * 2), int(y0 * 2)), (int(x1 * 2), int(y1 * 2)), 255, max(1, int(3.2 / d0)), cv2.LINE_AA, shift=2)
    out = np.clip(out + light_from(cv2.resize(cv, (W, H)), 0.85 * (1 - end)), 0, 1)
    # the memories (far to near), then frame 0 at the far end
    cards = [(zN, under, 0.0, 0.0, 0.0, 0.0)]
    for i, nm in enumerate(names, 1):
        th_ = math.radians(200 - 62 * i); X, Y = 0.92 * math.sin(th_), 1.25 * math.cos(th_)
        cards.append((1 + i * D, rew_card(nm), X, Y, -0.38 * X, 0.22 * Y))
    ones = np.ones((H, W), F32); src = np.float32([(0, 0), (W, 0), (W, H), (0, H)])
    for z, im, X, Y, yaw, pitch in sorted(cards, key=lambda q_: -q_[0]):
        quad = rew_quad(X, Y, z, c, yaw, pitch)
        if quad is None: continue
        d = z - c
        if X == 0 and Y == 0 and abs(d - 1) < 1e-6: out = im.copy(); continue
        Hm = cv2.getPerspectiveTransform(src, quad)
        ci = cv2.warpPerspective(im, Hm, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        m = cv2.warpPerspective(ones, Hm, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        fog = clamp((d - 2.0) / 5.0, 0, 0.55)
        if fog > 0: ci = ci * (1 - fog) + rew_bg() * fog
        al = clamp((d - 0.06) / 0.25, 0, 1)
        halo = cv2.GaussianBlur(m, (0, 0), 18) * (1 - m)
        rim = np.clip(cv2.GaussianBlur(m, (0, 0), 2.0) - m, 0, 1) * 1.8
        g_ = (1 - end) if (X == 0 and Y == 0) else 1.0
        out = out * (1 - (halo * 0.35 * al)[..., None]) + (halo * 0.35 * al)[..., None] * PEACH * 0.6 * g_
        out = out * (1 - (m * al)[..., None]) + ci * (m * al)[..., None]
        addc(out, rim * al * g_, PEACH, 0.6)
    # the frozen moment we fly through (nearest of all): it opens around us and is gone
    sc0 = 1.0 / max(0.05, 1 - c)
    if sc0 < 3.5:
        a0 = 1 - smooth(clamp((sc0 - 1) / 0.75, 0, 1))
        if a0 > 0.002:
            o0 = radial_blur(o, W / 2, H / 2, sc0, sc0 * (1 + 0.22 * clamp(sc0 - 1, 0, 1)), 7)          # it streaks past as we go through
            out = out * (1 - a0) + o0 * a0
    # the sparks of the freeze stream past as light
    rng = np.random.default_rng(1515); sp = np.zeros((H // 2, W // 2), F32); fa = 1 - smooth(clamp((t - 0.62) / 0.30, 0, 1))
    if fa > 0.01:
        for i in range(150):
            r_, a_, z0 = rng.uniform(0.25, 1.6), rng.uniform(0, 2 * math.pi), rng.uniform(0, 7)
            d1 = ((z0 - c) % 7.0) + 0.08; d0 = d1 + (c - c_prev)
            if d0 > 7.0: continue
            x1, y1 = W / 2 + r_ * math.cos(a_) / d1 * W, H / 2 + r_ * 1.2 * math.sin(a_) / d1 * W
            x0, y0 = W / 2 + r_ * math.cos(a_) / d0 * W, H / 2 + r_ * 1.2 * math.sin(a_) / d0 * W
            cv2.line(sp, (int(x0 * 2), int(y0 * 2)), (int(x1 * 2), int(y1 * 2)), min(1.0, 0.35 / d1 + 0.2), max(1, int(2.5 / d1)), cv2.LINE_AA, shift=2)
        sp = cv2.resize(cv2.GaussianBlur(sp, (0, 0), 0.8), (W, H))[..., None] * fa
        out = np.clip(out + sp * HOT * 0.8 + cv2.GaussianBlur(sp[..., 0], (0, 0), 5)[..., None] * AMBR * 0.8, 0, 1)
    v = (rew_cam(t + 0.02) - rew_cam(t - 0.02)) / 0.04
    k = 0.035 * v * (1 - end)
    if k > 0.002: out = radial_blur(out, W / 2, H / 2, 1.0, 1.0 + k, int(clamp(6 + k * 260, 6, 16)))   # enough samples: no stepped combs
    return np.clip(out, 0, 1)

def loop_in15(out, f, k):
    return out

TR2.update({"vibrate": (vibrate, 12, 8), "streak_pass": (streak_pass, 5, 7), "time_slice15": (time_slice15, 6, 10),
            "edge_current15": (edge_current15, 10, 14), "whip_up15": (whip_up15, 6, 8), "light_leak15": (light_leak15, 10, 12),
            "strike_cut": (strike_cut, 6, 8), "time_stop": (time_stop, 4, 14), "time_restart": (time_restart, 14, 24),
            "eye_iris15": (eye_iris15, 12, 14), "speed_whip15": (speed_whip15, 5, 7), "wind_gust": (wind_gust, 6, 10),
            "focus_rack15": (focus_rack15, 10, 12), "emblem_clock": (emblem_clock, EC_PRE, EC_POST), "afterimage15": (afterimage15, 10, 10),
            "turn_away": (turn_away, 7, 11), "pendulum": (pendulum, 8, 16), "loop_in15": ((lambda A, B, j, f, sa, sb: B), 0, 1)})

# ---- the frame ----------------------------------------------------------------------------------------------------------
def timepiece_draw(out, *a, **k):
    """(the hero: the timepiece, drawn by emblem_clock's marks and the stopped-time pieces)"""
    return out

# ---- in-shot animations (round 2: "blank space" filled; each one motivated by its shot, none on a face) -------------
def face_soft(s, f, pad=1.0, q=4):
    """a soft ellipse over the face (1 on the face), for keeping animations off it."""
    fs = face_scr(s, f) if s.get("face") is not None else None
    if not fs and s.get("face_hint"): fs = s["face_hint"]                                       # a profile YuNet can't see
    if not fs: return None
    m = np.zeros((H // q, W // q), F32)
    cv2.ellipse(m, (int(fs[0] / q), int(fs[1] / q)), (int(fs[2] * 0.95 * pad / q), int(fs[2] * 1.3 * pad / q)), 0, 0, 360, 1.0, -1)
    return cv2.resize(cv2.GaussianBlur(m, (0, 0), 12 / q), (W, H))[..., None]

def off_face(new, old, s, f, pad=1.0):
    m = face_soft(s, f, pad)
    return new if m is None else new * (1 - m) + old * m

def body_only(person, s, f):
    """his matte below the chin (arcs are born on his shoulders and arms, never round his head)."""
    if person is None: return None
    fs = face_scr(s, f) if s.get("face") is not None else None
    if not fs: return person
    y0 = int(clamp(fs[1] + fs[2] * 1.05, 0, H)); p_ = person.copy(); p_[:y0] = 0; return p_

def a_bokeh(img, person, s, f):
    """HER WORLD: warm out-of-focus lights drift up slowly behind Iris (her warm life against his cold run)."""
    rng = np.random.default_rng(4245); t = f / FPS; lay = np.zeros((H // 2, W // 2), F32)
    for i in range(22):
        x0, y0, r, sp, ph = rng.uniform(0, W), rng.uniform(0, H * 0.6), rng.uniform(26, 84), rng.uniform(18, 46), rng.uniform(0, 6.28)
        x = x0 + 24 * math.sin(t * 0.7 + ph); y = (y0 - sp * t) % (H * 0.62 + 120) - 80
        a = 0.35 + 0.35 * math.sin(t * 1.3 + ph * 2)
        cv2.circle(lay, (int(x / 2 * 4), int(y / 2 * 4)), int(r / 2 * 4), a, -1, cv2.LINE_AA, shift=2)
    lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 2.2), (W, H))[..., None]
    pm = np.clip(person * 1.1, 0, 1)[..., None] if person is not None else 0
    u = (f - s["f0"]) / max(1, s["f1"] - s["f0"]); amt = 1.10 * smooth(clamp(u / 0.20, 0, 1))
    return np.clip(img + lay * (1 - pm) * (PEACH * 0.8 + AMBR * 0.2) * amt, 0, 1)

def a_urge(img, person, s, f):
    """THE URGE: lightning gathers on him while he looks at her (his shoulders, his arms), stronger to the end."""
    u = (f - s["f0"]) / max(1, s["f1"] - s["f0"])
    bo = body_only(person, s, f)
    o = edge_arcs(img, f, bo, 0.8 + 1.8 * ein(u, 1.2), 1501)
    o = edge_arcs(o, f + 1, bo, 0.6 + 1.6 * ein(u, 1.2), 1511)
    o = edge_arcs(o, f + 2, bo, 0.4 + 1.4 * ein(u, 1.2), 1521)
    if bo is not None:                                                                          # his outline starts to glow
        eg = cv2.GaussianBlur(cv2.morphologyEx((bo > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8)).astype(F32), (0, 0), 6)[..., None]
        o = o + eg * AMBR * 1.6 * ein(u, 1.3)
    return off_face(o, img, s, f, 1.15)

def a_grit(img, person, s, f):
    """THE GUST: grit and dust in the wind of his passing streak through her shot (behind her, and a few blurred
    grains in front of the lens), fading as the gust goes by."""
    u = (f - s["f0"]) / max(1, s["f1"] - s["f0"]); amt = 1 - 0.7 * smooth(u)
    rng = np.random.default_rng(5353); t = f / FPS
    back = np.zeros((H // 2, W // 2), F32); front = np.zeros((H // 2, W // 2), F32)
    for i in range(110):
        x0, y0, sp, L, ph = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(900, 1900), rng.uniform(20, 70), rng.uniform(0, 6.28)
        x = (x0 + sp * t) % (W + 200) - 100; y = y0 + 30 * math.sin(t * 3 + ph)
        near = i < 9
        cv = front if near else back
        cv2.line(cv, (int((x - L * (2.2 if near else 1)) / 2 * 4), int(y / 2 * 4)), (int(x / 2 * 4), int(y / 2 * 4)), 0.9 if near else 0.6,
                 3 if near else 1, cv2.LINE_AA, shift=2)
    back = cv2.resize(cv2.GaussianBlur(back, (0, 0), 0.7), (W, H))[..., None]
    front = cv2.resize(cv2.GaussianBlur(front, (0, 0), 3.5), (W, H))[..., None]
    pm = np.clip(person * 1.1, 0, 1)[..., None] if person is not None else 0
    col = np.array([0.80, 0.86, 0.92], F32)
    o = img + back * (1 - pm) * col * 0.95 * amt
    return off_face(np.clip(o + front * col * 0.55 * amt, 0, 1), img, s, f, 1.2)

def a_shout(img, person, s, f):
    """THE SHOUT: on the kick the lightning bursts off him (arcs from his edge) and sparks are thrown outward."""
    e = e_of(f); kk = [x for x in np.arange(math.floor(e_of(s["f0"])), e + 0.01, 0.5) if (x % 8) in E.KICKS and x <= e]
    age = (e - kk[-1]) * E.HB if kk else 9.0; amt = 0.35 + 0.9 * math.exp(-age / 0.16)
    o = edge_arcs(img, f, body_only(person, s, f), amt * 1.3, 1601)
    cx, cy = subject_point(s, f, person); rng = np.random.default_rng(1601 + (f // 3)); cv = np.zeros((H // 2, W // 2), F32)
    for i in range(26):
        a_ = rng.uniform(0, 2 * math.pi); r0 = rng.uniform(80, 200) + 900 * age; r1 = r0 + rng.uniform(40, 130)
        cv2.line(cv, (int((cx + math.cos(a_) * r0) * 2), int((cy + math.sin(a_) * r0) * 2)), (int((cx + math.cos(a_) * r1) * 2), int((cy + math.sin(a_) * r1) * 2)),
                 1.0, 2, cv2.LINE_AA, shift=2)
    sp = cv2.resize(cv2.GaussianBlur(cv, (0, 0), 0.8), (W, H))[..., None] * math.exp(-age / 0.22)
    o = edge_arcs(o, f + 1, body_only(person, s, f), amt, 1611)
    return off_face(np.clip(o + sp * HOT * 1.8 + cv2.GaussianBlur(sp[..., 0], (0, 0), 6)[..., None] * AMBR * 2.0, 0, 1), img, s, f, 1.2)

def a_embers(img, person, s, f):
    """THROUGH THE FIRE: embers of the explosion stream past the lens (sharp ones in the fire, big soft ones close)."""
    rng = np.random.default_rng(7373); t = f / FPS; cv = np.zeros((H // 2, W // 2), F32); nr = np.zeros((H // 2, W // 2), F32)
    for i in range(95):
        x0, y0, sp, ph = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(500, 1400), rng.uniform(0, 6.28)
        near = i < 10; L = (80 if near else 30) * sp / 900
        x = (x0 + sp * t) % (W + 300) - 150; y = y0 - 90 * t + 20 * math.sin(t * 2 + ph)
        cv2.line(nr if near else cv, (int((x - L) * 2), int(y * 2)), (int(x * 2), int(y * 2)), 1.0, 7 if near else 2, cv2.LINE_AA, shift=2)
    cv = cv2.resize(cv2.GaussianBlur(cv, (0, 0), 0.7), (W, H))[..., None]; nr = cv2.resize(cv2.GaussianBlur(nr, (0, 0), 5), (W, H))[..., None]
    dark = np.clip(1.15 - lum8(img), 0.25, 1.0)[..., None]                                       # embers read against the smoke
    o = img * (1 - 0.35 * np.clip(cv * 2, 0, 1)) + (cv * HOT * 1.6 + cv2.GaussianBlur(cv[..., 0], (0, 0), 4)[..., None] * AMBR * 1.8) * dark + nr * AMBR * 1.0
    return off_face(np.clip(o, 0, 1), img, s, f, 1.25)

def a_flares(img, person, s, f):
    """STREETLIGHTS: the street lights behind him throw long anamorphic streaks across the lens."""
    q = 8; sm = cv2.resize(img, (W // q, H // q), interpolation=cv2.INTER_AREA)
    hi = np.clip(sm.max(2) - 0.58, 0, 1) * 3.0
    st = cv2.resize(cv2.GaussianBlur(hi, (0, 0), sigmaX=34, sigmaY=0.7) * 6.0, (W, H))[..., None]
    core = cv2.resize(cv2.GaussianBlur(hi, (0, 0), sigmaX=10, sigmaY=0.5) * 3.0, (W, H))[..., None]
    o = img + st * np.array([1.00, 0.62, 0.55], F32) * 0.55 + core * np.array([1.0, 0.9, 0.85], F32) * 0.35
    return off_face(np.clip(o, 0, 1), img, s, f, 1.25)

def a_current(img, person, s, f):
    """SUIT CURRENT: lightning crawls over the suit's edges."""
    return off_face(edge_arcs(img, f, body_only(person, s, f), 0.8, 1701), img, s, f, 1.15)

def a_remnants(img, person, s, f):
    """TIME REMNANTS: on each beat gold copies of him split off sideways, left behind in time as he runs on."""
    return time_remnants(img, s, f, person, 0.85)

ANIMS = {"bokeh": a_bokeh, "urge": a_urge, "grit": a_grit, "shout": a_shout, "embers": a_embers, "flares": a_flares,
         "current": a_current, "remnants": a_remnants}

# ---- PHONE FLARE (the call -> the night city): the phone's light flares into the lens and the city burns in ------------
def phone_point(s, f, img):
    """the phone's lit screen: the bluest bright pixels in the frame."""
    q = 8; sm = cv2.resize(img, (W // q, H // q), interpolation=cv2.INTER_AREA)
    m = np.clip((sm[..., 0] - np.maximum(sm[..., 1], sm[..., 2]) - 0.08) * 6, 0, 1) * np.clip((sm[..., 0] - 0.35) * 4, 0, 1)
    if m.sum() < 0.5: return W * 0.25, H * 0.42
    ys, xs = np.nonzero(m > 0.05); w_ = m[ys, xs]; return float((xs * w_).sum() / w_.sum() * q + q / 2), float((ys * w_).sum() / w_.sum() * q + q / 2)

def phone_flare(A, B, j, f, sa, sb, pre=8, post=12):
    """PHONE FLARE: the call connects: the phone's blue light swells and flares across the lens (a long anamorphic
    streak, a cold bloom), and the night city burns in under it, its lights first, out of focus, then him."""
    x = (j + pre) / (pre + post - 1); pk = math.exp(-((x - 0.42) / 0.20) ** 2)
    px, py = phone_point(sa, sa["f1"] - 1, edge15(sa, "last"))
    d2 = (_GX - px) ** 2 + ((_GY - py) * 1.0) ** 2
    bloom = np.exp(-d2 / (2 * (90 + 520 * pk) ** 2)).astype(F32)
    streak = np.exp(-((_GY - py) / (5 + 10 * pk)) ** 2).astype(F32) * np.exp(-np.abs(_GX - px) / (300 + 900 * pk)).astype(F32)
    w = smooth(clamp((x - 0.32) / 0.22, 0, 1))
    if w < 1: Ad = A if x < 0.2 else defocus15(A, 30 * ein(clamp((x - 0.15) / 0.3, 0, 1)))
    Bd = defocus15(B, 34 * (1 - smooth(clamp((x - 0.35) / 0.65, 0, 1))))
    o = Bd if w >= 1 else Ad * (1 - w) + Bd * w
    cold = np.array([1.00, 0.72, 0.45], F32)
    wide = np.exp(-d2 / (2 * (300 + 900 * pk) ** 2)).astype(F32)
    return np.clip(o + bloom[..., None] * cold * 0.50 * pk + wide[..., None] * cold * 0.22 * pk, 0, 1)

# ---- DUST CLOUD (her hair in his wind -> the trail): the dust he kicks up rolls across the frame and clears onto the trail
def smooth_arr(x): return x * x * (3 - 2 * x)

def dust_field(f, q=4):
    """billowing dust: two octaves of large soft noise drifting with the wind (advected, never wrapping in the edit)."""
    key = ("dust",)
    if key not in _DUSTC:
        rng = np.random.default_rng(909)
        _DUSTC[key] = [cv2.GaussianBlur(rng.random((H // q + 120, W // q * 3)).astype(F32), (0, 0), s_) for s_ in (34, 14)]
        _DUSTC[key] = [(n_ - n_.mean()) / (n_.std() + 1e-6) for n_ in _DUSTC[key]]
    t = f / FPS; o = np.zeros((H // q, W // q), F32)
    for i, (n_, wgt, sp) in enumerate(zip(_DUSTC[key], (0.75, 0.25), (150, 230))):
        x0 = int((40 * 60 - sp * t / q) % (n_.shape[1] - W // q)); y0 = 60 + int(14 * math.sin(t * 1.3 + i))
        o += n_[y0:y0 + H // q, x0:x0 + W // q] * wgt
    return o
_DUSTC = {}

def dust_cloud(A, B, j, f, sa, sb, pre=14, post=12):
    """DUST CLOUD: the dust his run kicked up rolls in on the wind from the side he ran to, billowing over her (puffs,
    lit warm from above, streaked by the wind), and thins out onto the trail he left down the path."""
    x = (j + pre) / (pre + post - 1); q = 4
    n = dust_field(f, q); gx = np.linspace(0, 1, W // q, dtype=F32)[None, :]
    front = -0.5 + 2.1 * smooth(clamp(x / 0.62, 0, 1)); clear = smooth(clamp((x - 0.55) / 0.45, 0, 1))
    raw = (front - gx) * 3.2 + n * 0.9                                                           # a front that rolls in, billowing at its edge
    dens = smooth_arr(np.clip(raw, 0, 1)) * (1 - clear) * 0.93 * smooth(x / 0.12)                # exactly 0 at both ends
    dens = cv2.blur(dens, (9, 1))                                                               # streaked by the wind
    lit = np.clip(0.50 - 0.11 * cv2.Sobel(n, cv2.CV_32F, 0, 1, ksize=5) - 0.06 * cv2.Sobel(n, cv2.CV_32F, 1, 0, ksize=5), 0.12, 1.0)
    dens = cv2.resize(cv2.GaussianBlur(dens, (0, 0), 1.5), (W, H))[..., None]
    lit = cv2.resize(cv2.GaussianBlur(lit, (0, 0), 2), (W, H))[..., None]
    dust = np.array([0.70, 0.76, 0.82], F32) * (0.55 + 0.65 * lit)
    w = smooth(clamp((x - 0.46) / 0.20, 0, 1)); base = A * (1 - w) + B * w if 0 < w < 1 else (A if w <= 0 else B)
    return np.clip(base * (1 - dens) + dust * dens, 0, 1)

def freefall(A, B, j, f, sa, sb, pre=6, post=10):
    """FREEFALL (the S5 suit at night -> the city from above): he steps off the roof: the frame drops away beneath us
    like a card falling, tipping as it goes, and we fall after it toward the city far below, rushing in out of the blur."""
    x = (j + pre) / (pre + post - 1); fa = ein(clamp(x / 0.72, 0, 1), 2.1)
    dy = H * 1.12 * fa; rot = 5.0 * fa; v = 2.1 * H * 1.12 * (clamp(x / 0.72, 0, 1) ** 1.1) / 0.72 / (pre + post)
    M = cv2.getRotationMatrix2D((W / 2, H * 0.2), rot, 1.0); M[1, 2] += dy
    A4 = cv2.warpAffine(np.dstack([A, np.ones((H, W), F32)]), M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    if v > 2: A4 = hblur(A4, 2 + v * 0.8, vertical=True)
    zb = 1.0 + 0.28 * (1 - eout(x, 2.2)); Bz = zoom_about(B, W / 2, H / 2, zb)
    kb = 0.10 * (1 - eout(x, 2.0)); Bz = radial_blur(Bz, W / 2, H / 2, 1.0, 1.0 + kb, 8) if kb > 0.004 else Bz
    Bz = Bz * (0.72 + 0.28 * smooth(x))
    sh = np.roll(cv2.GaussianBlur(A4[..., 3], (0, 0), 26), -30, axis=0)[..., None] * (1 - A4[..., 3:4])   # the falling frame's shadow
    o = Bz * (1 - 0.35 * sh)
    return np.clip(o * (1 - A4[..., 3:4]) + A4[..., :3], 0, 1)

TR2.update({"phone_flare": (phone_flare, 8, 12), "dust_cloud": (dust_cloud, 14, 12)})
TR2.update({"freefall": (freefall, 6, 10)})

# ---- IGNITION (the cold close-up -> through the fire): one ember catches and burns the frame open onto the fire ------
_IGN = {}
def ign_noise(q=4):
    """the burn's fixed paper-like grain (three octaves): the front's shape comes from it, so the edge moves smoothly."""
    if "n" not in _IGN:
        rng = np.random.default_rng(2727); acc = np.zeros((H // q, W // q), F32)
        for s_, w_ in ((38, 0.6), (14, 0.3), (5, 0.1)):
            n_ = cv2.GaussianBlur(rng.random((H // q, W // q)).astype(F32), (0, 0), s_); acc += (n_ - n_.mean()) / (n_.std() + 1e-6) * w_
        _IGN["n"] = acc
    return _IGN["n"]

IGN_P = (0.20, 0.86)                                                                       # where it catches (his shoulder, far from his face)
def ign_R(x):
    """the burn front's reach (in frame heights) at transition time x: nothing while the ember glows, then it spreads."""
    return 1.60 * smooth(clamp((x - 0.27) / 0.62, 0, 1)) ** 1.10

def ignition(A, B, j, f, sa, sb, pre=20, post=28):
    """IGNITION: in the cold close-up a single ember catches on his shoulder: it glows, pulses on the beat and flares (the
    focal point). Then it burns the frame open: a white-hot front with an orange glow and a scorched rim spreads out
    from it, embers peel off the edge, and through the hole is the real fire he flies through. The front goes round his
    face and takes it last, under a warm flash (no edge ever crosses a face)."""
    q = 4; x = (j + pre) / (pre + post - 1); px, py = W * IGN_P[0], H * IGN_P[1]
    gx, gy = np.meshgrid(np.arange(W // q, dtype=F32) * q, np.arange(H // q, dtype=F32) * q)
    d = np.sqrt((gx - px) ** 2 + (gy - py) ** 2) / H
    fmA = face_soft(sa, sa["f1"] - 1, 0.85, q); fmB = face_soft(sb, sb["f0"], 1.0, q)          # the face itself (an extreme close-up: not the frame)
    fq = np.zeros((H // q, W // q), F32)
    for fm_ in (fmA, fmB):
        if fm_ is not None: fq = np.maximum(fq, cv2.resize(fm_[..., 0], (W // q, H // q)))
    nz = ign_noise(q); fs_ = np.clip(fq * 1.5, 0, 1)
    D = d * (1 + 0.30 * nz * (1 - fs_)) + 0.20 * fq                                           # no holes in a face: one soft edge passes over it
    R = ign_R(x)
    burned = np.clip((R - D) / (0.012 + 0.06 * fs_), 0, 1)
    front = np.exp(-((D - R) / 0.010) ** 2) * (R > 0.002)
    char = np.clip((R + 0.030 - D) / 0.020, 0, 1) * (1 - burned) * smooth(R / 0.03) * (1 - np.clip(fq * 1.6, 0, 1))   # no scorch before it burns, none on a face
    heat = np.exp(-np.clip(D - R, 0, None) / 0.07) * (R > 0.002) * (1 - burned)
    up = lambda m_: cv2.resize(m_.astype(F32), (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
    burned, front, char, heat, fu = up(burned), up(front), up(char), up(heat), up(fq)
    o = A * (1 - 0.55 * char) * (1 + heat * np.array([0.05, 0.25, 0.55], F32))           # scorched rim, warmed paper ahead of it
    o = o * (1 - burned) + B * burned
    w = smooth(clamp((x - 0.72) / 0.22, 0, 1))                                             # whatever is left goes under a warm flash
    if w > 0: o = o * (1 - w) + B * w
    front = front * (1 - np.clip(fu * 1.6, 0, 1)) * (1 - w)                                 # the white-hot line never runs over a face
    flash = math.exp(-((x - 0.82) / 0.08) ** 2) * 0.20
    o = o + front * HOT * 1.1 + up(cv2.GaussianBlur(front[::q, ::q, 0], (0, 0), 3)) * AMBR * 1.2 + AMBR * flash
    # the ember: the focal point (glows, pulses on the kick, flares, then becomes the front)
    g = smooth(clamp(x / 0.10, 0, 1)) * (1 - smooth(clamp((x - 0.38) / 0.12, 0, 1)))
    if g > 0.002:
        e = e_of(f); kk = [k_ for k_ in (71.0, 71.5) if e >= k_]; pls = math.exp(-((e - kk[-1]) * E.HB) / 0.12) if kk else 0.0
        r_ = 3 + 6 * smooth(clamp(x / 0.30, 0, 1)) + 5 * pls
        dd = (_GX - px) ** 2 + (_GY - py) ** 2
        core = np.exp(-dd / (2 * r_ ** 2)); bloom = np.exp(-dd / (2 * (r_ * 9) ** 2))
        streak = np.exp(-((_GY - py) / (2.2 + r_ * 0.25)) ** 2) * np.exp(-np.abs(_GX - px) / (60 + 220 * g))
        o = o + (core[..., None] * HOT * 1.6 + bloom[..., None] * AMBR * 0.75 + streak[..., None] * AMBR * 0.55) * g * (1 + 0.6 * pls)
    # embers peeling off the burning edge (each on its own smooth path)
    if 0.30 < x < 1.0:
        rng = np.random.default_rng(2828); cv = np.zeros((H // 2, W // 2), F32)
        for i in range(70):
            ts, a_, sp, up_ = rng.uniform(0.30, 0.80), rng.uniform(-math.pi, 0.4), rng.uniform(0.10, 0.35), rng.uniform(0.15, 0.45)
            age = x - ts
            if age < 0 or age > 0.22: continue
            r0 = ign_R(ts) * H * 0.92; sx_, sy_ = px + math.cos(a_) * r0, py + math.sin(a_) * r0
            ex_ = sx_ + math.cos(a_) * sp * H * age; ey_ = sy_ + math.sin(a_) * sp * H * age - up_ * H * age * age * 4
            ex0 = sx_ + math.cos(a_) * sp * H * max(0, age - 0.02); ey0 = sy_ + math.sin(a_) * sp * H * max(0, age - 0.02) - up_ * H * max(0, age - 0.02) ** 2 * 4
            al = (1 - age / 0.22) ** 1.5
            cv2.line(cv, (int(ex0 * 2), int(ey0 * 2)), (int(ex_ * 2), int(ey_ * 2)), al, 2, cv2.LINE_AA, shift=2)
        cv = cv2.resize(cv2.GaussianBlur(cv, (0, 0), 0.8), (W, H))[..., None] * (1 - np.clip(fu * 1.6, 0, 1))
        o = o + cv * HOT * 1.2 + cv2.GaussianBlur(cv[..., 0], (0, 0), 5)[..., None] * AMBR * 1.3
    return np.clip(o, 0, 1)

TR2.update({"ignition": (ignition, 20, 28)})

def base15(s, f):
    if s["n"] == "still": return still_fx(s, f), None
    img, person = base11(s, f)
    if s.get("expo"): img = 1 - (1 - np.clip(img, 0, 1)) ** s["expo"]                         # a dark source lifted (the night city)
    if s.get("anim") in ANIMS: img = ANIMS[s["anim"]](img, person, s, f)
    if s["n"] == "alone": img = loop_out(img, f, s)
    return img, person

_B15 = {}
def edge15(S_, which):
    key = (S_["n"], which)
    if key not in _B15:
        if len(_B15) > 8: _B15.clear()
        fr = S_["f0"] if which == "first" else S_["f1"] - 1
        if S_["n"] == "still": _B15[key] = still_fx(S_, fr)
        else: _B15[key] = base15(S_, fr)[0]                                                   # with the shot's own animation
    return _B15[key]

PERSON = {}
def prefinish(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base15(s, f)
    PERSON.clear(); PERSON[f] = person
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge15(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge15(n_, "first"), kn, f, s, n_)
    return np.clip(out, 0, 1)

def render(f):
    s = shot_at(f); out = flash_governor(beat_fx(prefinish(f), f))
    fin_s = SHOTS[0] if (s["n"] == "alone" and f >= s["f1"] - 1) else s
    return (np.clip(finish15(out, f, fin_s), 0, 1) * 255 + 0.5).astype(np.uint8)
