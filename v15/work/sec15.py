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
    return (0 <= e < E.E_STOP) or (E.HDROP <= e < 74)

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

def focus_rack15(A, B, j, f, sa, sb, pre=10, post=12):
    """FOCUS RACK: the lens racks out to bokeh, the next shot is found in the blur over 8 frames, and racks back in."""
    if j < 0:
        u = (j + pre) / pre; o = defocus(A, 50 * ein(u, 1.8))
        if j >= -8: o = mixm(o, defocus(B, 50), np.full((H, W), smooth((j + 9) / 9), F32))
        return o
    v = (j + 1) / post; return defocus(B, 50 * (1 - eout(v, 2.0)))

def whip_up15(A, B, j, f, sa, sb, pre=6, post=8):
    """WHIP UP: a clean tilt-whip upward with real vertical motion blur and one thin streak of light."""
    if j < 0: u = (j + pre) / pre; o = hblur(shift_img(A, 0, H * 0.45 * ein(u, 2.2)), 2 + 190 * ein(u, 2.0), vertical=True); k = ein(u, 1.5)
    else: v = (j + 1) / post; o = hblur(shift_img(B, 0, -H * 0.45 * (1 - eout(v, 2.2))), 2 + 170 * (1 - eout(v, 2.0)), vertical=True); k = 1 - eout(v, 1.6)
    band = np.exp(-((_GX[:1, :] - W * 0.86) / 4.0) ** 2) * k
    lay = np.zeros((H, W, 3), F32); addc(lay, np.repeat(band, H, 0), HOT, 0.6)
    return np.clip(o + lay, 0, 1)

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

def eye_iris15(A, B, j, f, sa, sb, pre=12, post=14):
    """EYE IRIS: the lightning in his eyes forks outward, then a ring of lightning opens from his pupil with Iris inside."""
    if j < 0:
        u = (j + pre) / pre; px, py = eye_pos15(sa, f); Z = 1 + 0.45 * ein(u, 2.0); A2 = zoom_about(A, px, py, Z)
        Ri = 30 * Z; Lr = Ri + 520 * ein(u, 1.5); cv = bolt_canvas()
        for k in range(9):
            a = 2 * math.pi * k / 9 + 0.25 * math.sin(f * 0.07 + k)
            put_bolt(cv, (px + Ri * math.cos(a), py + Ri * math.sin(a)), (px + Lr * math.cos(a), py + Lr * math.sin(a)), 9300 + k + 9 * (f // 2), 2, 0.30, 5, 1)
        o = A2
        if u > 0.6:
            Rr = Ri * (1 + 5 * ein((u - 0.6) / 0.4, 2.0))
            m = disc_mask(px, py, Rr, 3); o = mixm(A2, zoom_about(B, px, py, 1.3), m)
            cv = np.maximum(cv, light_ring(px, py, Rr, f))
        return np.clip(o + light_rgb(cv, 0.35 + 0.6 * u, HOT, AMB), 0, 1)
    v = (j + 1) / post; px, py = eye_pos15(sa, sa["f1"] - 1)
    cx, cy = px + (W / 2 - px) * smooth(v), py + (H / 2 - py) * smooth(v)
    Rr = 30 * 1.45 * 6 + 2300 * ein(v, 1.8)
    A2 = zoom_about(A, px, py, 1.45 * (1 + 0.4 * v))
    o = mixm(A2, zoom_about(B, cx, cy, 1.0 + 0.3 * (1 - eout(v, 2.0))), disc_mask(cx, cy, Rr, 3))
    return np.clip(o + light_rgb(light_ring(cx, cy, Rr, f, 3, 4), 0.9 * (1 - v) ** 1.2, HOT, AMB), 0, 1)

def time_slice15(A, B, j, f, sa, sb, pre=6, post=10):
    """TIME SLICE: the frame comes apart into tall slivers that slide out in a wave, each a moment later than its
    neighbour (time smeared across the frame), and the next shot slides in behind them; gold seams between them."""
    q = (j + pre) / (pre + post); n = 12; sw = W / n
    Ab = hblur(A, 60, vertical=True); Bb = hblur(B, 60, vertical=True)
    o = np.empty_like(A); seam = np.zeros((H, W), F32)
    for i in range(n):
        x0, x1 = int(i * sw), int((i + 1) * sw); d = 0.40 * i / (n - 1)
        p = eout(clamp((q - d) / 0.55, 0, 1), 2.4); sp = 4 * p * (1 - p)
        dy = int(-H * p) if i % 2 == 0 else int(H * p)
        Ai = (Ab if sp > 0.3 else A)[:, x0:x1]; Bi = (Bb if sp > 0.3 else B)[:, x0:x1]
        col = np.roll(np.concatenate([Ai, Bi], 0) if dy < 0 else np.concatenate([Bi, Ai], 0), dy, axis=0)
        o[:, x0:x1] = col[:H] if dy < 0 else col[H:]
        if 0 < p < 1: seam[:, max(0, x0 - 1):x0 + 2] = sp
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

def panel_run15(A, B, j, f, sa, sb, pre=8, post=12):
    """PANEL RUN: three panels run out in alternate directions, one after another; the next shot runs in behind them."""
    q = (j + pre) / (pre + post); n = 3; pw = W / n
    o = np.empty_like(A); seam = np.zeros((H, W), F32)
    for i in range(n):
        x0, x1 = int(i * pw), int((i + 1) * pw); p = eout(clamp((q - 0.12 * i) / 0.62, 0, 1), 2.6)
        d = 1 if i % 2 == 0 else -1; off = int(d * H * p); sp = 4 * p * (1 - p)
        Ai = hblur(A[:, x0:x1], 2 + 50 * sp, vertical=True) if sp > 0.2 else A[:, x0:x1]
        Bi = hblur(B[:, x0:x1], 2 + 50 * sp, vertical=True) if sp > 0.2 else B[:, x0:x1]
        st_ = np.concatenate([Ai, Bi], 0) if d < 0 else np.concatenate([Bi, Ai], 0)
        st_ = np.roll(st_, off, axis=0); o[:, x0:x1] = st_[:H] if d < 0 else st_[H:]
        if 0 < p < 1 and i > 0: seam[:, x0 - 1:x0 + 2] = sp
    return np.clip(o + light_rgb((seam * 255).astype(np.uint8), 0.8, HOT, AMB), 0, 1)

# ---- VIBRATE (the watch -> the call): the frame buzzes like a phone ringing, three pulses, the call under the last -------
def vibrate(A, B, j, f, sa, sb, pre=12, post=8):
    """VIBRATE: a call comes in: the picture buzzes three times like a phone on a table (a fast side-to-side shake with a
    ghost of itself), and the call is underneath the third buzz."""
    k = j + pre; n = pre + post
    pulses = [(0, 4), (6, 4), (11, 6)]                                                        # (start, length) in frames from -pre
    amp = 0.0
    for a_, l_ in pulses:
        if a_ <= k < a_ + l_: amp = math.sin(math.pi * (k - a_ + 0.5) / l_)
    w = smooth(clamp((k - 11) / 4, 0, 1))                                                     # the call comes in under the last buzz
    base = A * (1 - w) + B * w if 0 < w < 1 else (A if w <= 0 else B)
    if amp <= 0: return base
    dx = 16 * amp * (1 if (f % 2) else -1)
    g1 = shift_img(base, dx); g2 = shift_img(base, -dx * 0.6)
    o = g1 * 0.62 + g2 * 0.38
    return np.clip(hblur(o, 2 + 10 * amp), 0, 1)

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
    fb = face_box(sa, f) if (j < 0 and sa.get("face") is not None) else None
    xs = W * 0.22 if (fb is None or (fb[0] + fb[1]) / 2 > W / 2) else W * 0.78
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
    """the frozen frame, his matte, and a clean plate behind him (for the parallax)."""
    if "img" not in _ST:
        img, person = base11(s, s["f0"])
        m = np.clip(person if person is not None else np.zeros((H, W), F32), 0, 1).astype(F32)
        q = 4; sm = (np.clip(cv2.resize(img, (W // q, H // q), interpolation=cv2.INTER_AREA), 0, 1) * 255).astype(np.uint8)
        mk = (cv2.dilate(cv2.resize(m, (W // q, H // q)), np.ones((5, 5), np.uint8)) > 0.2).astype(np.uint8) * 255
        plate = cv2.resize(cv2.inpaint(sm, mk, 9, cv2.INPAINT_TELEA).astype(F32) / 255, (W, H), interpolation=cv2.INTER_LINEAR)
        mm = cv2.GaussianBlur(m, (0, 0), 1.2)[..., None]
        _ST["img"], _ST["m"], _ST["plate"] = img, mm, img * mm + plate * (1 - mm)
        _ST["plate"] = plate
        fs = face_scr(s, s["f0"]) if s.get("face") is not None else None
        _ST["fc"] = (fs[0], fs[1] + fs[2] * 0.9) if fs else (W / 2, H * 0.55)             # the camera's pivot: his chest
        q8 = cv2.GaussianBlur(cv2.resize(lum8(img), (W // 8, H // 8), interpolation=cv2.INTER_AREA), (0, 0), 2)
        fm = np.zeros_like(q8)
        if fs: cv2.ellipse(fm, (int(fs[0] / 8), int(fs[1] / 8)), (int(fs[2] * 0.9 / 8), int(fs[2] * 1.2 / 8)), 0, 0, 360, 1.0, -1)
        hotq = np.clip(q8 - 0.80, 0, 1) * (1 - fm); ys, xs = np.nonzero(hotq > 0.02)
        if len(xs): w_ = hotq[ys, xs]; _ST["sp"] = (float((xs * w_).sum() / w_.sum() * 8 + 4), float((ys * w_).sum() / w_.sum() * 8 + 4))
        else: _ST["sp"] = (W * 0.2, H * 0.2)                                                   # the strike point: the frozen bolts
        fmf = cv2.GaussianBlur(cv2.resize(fm, (W, H)), (0, 0), 30); _ST["fmask"] = np.clip(fmf * 1.5, 0, 1)
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

def fill_step(e):
    """the frozen world steps on each kick of the fill: a quick push that settles (stop-motion through the moment)."""
    z = 0.0
    for ek in E.FILL:
        if e >= ek: z += 0.010 * eout(clamp((e - ek) / 0.35, 0, 1), 3.0)
    return z

def fill_pulse(e):
    p = 0.0
    for ek in E.FILL:
        d = (e - ek) * E.HB
        if d >= 0: p = max(p, math.exp(-d / 0.10))
    return p

def still_fx(s, f):
    """THE STILL: time stops at the moment of the S1 strike. The frame is frozen; the camera drifts through it and steps
    on each kick of the drum fill (stop motion), with his figure moving against the room behind (parallax); the drops of
    the chemicals and the sparks hang in the air at three depths; the colour is drained but the lightning stays hot and
    pulses on each kick; in the last beat the frozen lightning starts to crackle."""
    L = still_layers(s); e = e_of(f); k = f - s["f0"]; n = s["f1"] - s["f0"]
    u = k / max(1, n - 1); cx, cy = L["fc"]
    z = 1.0 + 0.045 * u + fill_step(e)
    zb = 1.0 + (z - 1) * 0.55; dx = -18 * smooth(u)
    bg = zoom_about(shift_img(L["plate"], dx * 0.5), cx, cy, zb)
    fg = zoom_about(shift_img(L["img"], dx), cx, cy, z); m = zoom_about(shift_img(L["m"], dx), cx, cy, z)
    if m.ndim == 2: m = m[..., None]
    o = bg * (1 - m) + fg * m
    lum = lum8(o); hot = np.clip((lum - 0.62) / 0.25, 0, 1)[..., None]                       # the lightning stays hot
    gray = lum[..., None] * np.array([1.10, 0.99, 0.90], F32)                                 # time stopped: cool and still
    drain = 0.66 * smooth(clamp(k / 10, 0, 1))
    o = o * (1 - drain * (1 - hot)) + gray * (drain * (1 - hot)) + VIO * 0.045 * drain
    pl = fill_pulse(e); o = o * (1 + 0.16 * pl * hot)
    # the suspended drops and sparks
    q4 = np.zeros((H // 2, W // 2), F32); qs = np.zeros((H // 2, W // 2), F32); t = k / FPS
    fb = face_box(s, s["f0"]) if s.get("face") is not None else None
    for (x, y, d, r, kind, ph) in still_particles():
        zz = 1 + (z - 1) / d; px = cx + (x - cx) * zz + dx / d + 3 * math.sin(t * 0.7 + ph); py = cy + (y - cy) * zz + 2 * t / d
        if fb and fb[0] - 30 < px < fb[1] + 30 and py < fb[2] + 40 and d > 0.7: continue      # nothing hangs in front of his face
        rr = max(1.0, r * zz * 0.5)
        if kind: cv2.circle(qs, (int(px * 2), int(py * 2)), int(rr * 2), 1.0, -1, cv2.LINE_AA, shift=2)
        else:                                                                                  # a drop: a pale lens with a bright point
            cv2.circle(q4, (int(px * 2), int(py * 2)), int(rr * 3.0), 0.55, -1, cv2.LINE_AA, shift=2)
            cv2.circle(qs, (int((px - rr * 0.3) * 2), int((py - rr * 0.3) * 2)), max(1, int(rr * 0.9)), 0.9, -1, cv2.LINE_AA, shift=2)
    dro = cv2.resize(cv2.GaussianBlur(q4, (0, 0), 0.8), (W, H)); spk = cv2.resize(cv2.GaussianBlur(qs, (0, 0), 0.6), (W, H))
    addc(o, dro, np.array([0.95, 0.85, 0.92], F32), 0.40); addc(o, cv2.GaussianBlur(spk, (0, 0), 5), AMBR, 0.9 * (0.6 + 0.4 * pl)); addc(o, spk, HOT, 0.9)
    if e > 39.2:                                                                               # the frozen lightning starts to crackle
        cr = (e - 39.2) / 0.8; fl = 0.5 + 0.5 * math.sin(f * 2.3)
        o = o * (1 + 0.20 * cr * fl * hot) ; o = radial_blur(o, cx, cy, 1.0, 1.0 + 0.03 * cr, 4)
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
def time_restart(A, B, j, f, sa, sb, pre=6, post=16):
    """TIME RESTARTS: the frozen lightning flares and discharges; a shockwave ring bends the picture as it races out from
    the strike, and behind it time is moving again: his eyes, full of lightning, in full colour."""
    L = still_layers(sa); cx, cy = L["sp"]
    if j < 0:
        u = (j + pre) / pre
        return np.clip(radial_blur(A, cx, cy, 1.0, 1.0 + 0.10 * ein(u, 2.0), 6) * (1 + 0.20 * ein(u, 2.0) * (1 - L["fmask"][..., None])), 0, 1)
    v = (j + 1) / post; R = 160 + 2600 * eout(v, 2.2)
    d = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2) + 1e-3
    env = np.exp(-((d - R) / 90) ** 2); disp = 38 * env * (1 - v)
    mx = (_GX - (_GX - cx) / d * disp).astype(F32); my = (_GY - (_GY - cy) / d * disp).astype(F32)
    Aw = cv2.remap(A, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    Bz = zoom_about(B, W / 2, H * 0.4, 1.0 + 0.10 * (1 - eout(v, 2.0)))
    Bw = cv2.remap(Bz, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    m = np.clip((R - d) / 220 + 0.5, 0, 1).astype(F32)
    o = mixm(Aw, Bw, m)
    fb = face_box(sb, sb["f0"]) if sb.get("face") is not None else None
    keep = np.ones((H, W), F32)
    if fb: keep = 1 - np.clip(((np.abs(_GX - (fb[0] + fb[1]) / 2) < (fb[1] - fb[0]) * 0.75) & (_GY < fb[2] + 80)).astype(F32), 0, 1)
    keep = cv2.GaussianBlur(keep, (0, 0), 25)
    lay = np.zeros((H, W, 3), F32); fr = np.exp(-((d - R) / 16) ** 2) * (1 - v) ** 0.8 * keep
    addc(lay, fr, HOT, 0.45); addc(lay, cv2.GaussianBlur(fr.astype(F32), (0, 0), 18), AMBR, 0.7)
    return np.clip(o + lay, 0, 1)

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
    """the real bolt lifted off the emblem: its gold pixels (inside 1.55 R; the gold rim left in place except where the
    bolt's tips cross it), and the emblem with the bolt filled in from its own white disc and the suit around it."""
    m_ = 1.6 * R; x0, y0, x1, y1 = max(0, int(ex - m_)), max(0, int(ey - m_)), min(W, int(ex + m_) + 1), min(H, int(ey + m_) + 1)
    sub = np.clip(A[y0:y1, x0:x1], 0, 1); Bc, Gc, Rc = sub[..., 0], sub[..., 1], sub[..., 2]
    gx, gy = _GX[y0:y1, x0:x1] - ex, _GY[y0:y1, x0:x1] - ey; rho = np.sqrt(gx * gx + gy * gy) / R
    mx_, mn_ = sub.max(2), sub.min(2)
    white = (mn_ > 0.55) & (mx_ - mn_ < 0.20)
    gold = (Rc > 0.30) & (Gc / (Rc + 1e-3) > 0.48) & (Rc - Bc > 0.06)
    ax = np.array([E.EMB15_TIP[0], E.EMB15_TIP[1]], F32); ax /= np.linalg.norm(ax)
    dax = np.abs(gx * ax[1] - gy * ax[0]) / R                                                  # distance to the bolt's axis
    inner = (rho < 0.84) & ~white                                                              # in the disc: anything that isn't the white face
    tips = (rho >= 0.84) & (rho < 1.55) & gold & (dax < 0.30)                                  # beyond it: the gold tips along the axis
    mk = (inner | tips).astype(np.uint8)
    mk = cv2.morphologyEx(mk, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)); mk = cv2.dilate(mk, np.ones((3, 3), np.uint8))
    filled = cv2.inpaint((sub * 255).astype(np.uint8), mk * 255, 5, cv2.INPAINT_TELEA).astype(F32) / 255
    alpha = cv2.GaussianBlur(mk.astype(F32), (0, 0), 0.8)
    return (x0, y0, x1, y1), filled, np.dstack([sub, alpha])

def ec_cam(sa, f, P_):
    ex, ey, er = emb15_screen(sa, f); s_ = 1 + 1.25 * P_
    tx, ty = ex + (W / 2 - ex) * smooth(P_), ey + (H * 0.52 - ey) * smooth(P_)
    return np.float32([[s_, 0, tx - s_ * ex], [0, s_, ty - s_ * ey]]), ex, ey, er, tx, ty, s_

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
        v = (j + 1) / post; s2 = 1 + 1.6 * ein(v, 1.6); M = M.copy(); M[:, :2] *= s2; M[0, 2] = tx - s_ * s2 * ex; M[1, 2] = ty - s_ * s2 * ey; s_ = s_ * s2
    (x0, y0, x1, y1), filled, bolt = bolt_lift(A, ex, ey, er)
    Af = A.copy(); Af[y0:y1, x0:x1] = filled
    lift = smooth(clamp(u / 0.12, 0, 1))
    Ac = cv2.warpAffine(Af if lift > 0 else A, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    # the hand's angle: ticks on the kicks (30 deg each), then winding, then the sweep
    e = e_of(f_); th = 0.0
    e0 = (sa["f1"] - pre) / FPS / E.HB; e1 = e0 + 0.40 * pre / FPS / E.HB
    for ek in [x for x in np.arange(math.floor(e0), e1 + 0.01, 0.5) if (x % 8) in E.KICKS and e0 <= x <= e1]:
        if e >= ek: th += 30 * eout(clamp((e - ek) * E.HB / 0.10, 0, 1), 3)
    wu = clamp((u - 0.40) / 0.38, 0, 1); th += 540 * ein(wu, 2.2)                                # winding
    sw = clamp((u - 0.78) / 0.22, 0, 1) if j < 0 else 1.0
    if j >= 0: sw_post = (j + 1) / post
    else: sw_post = 0.0
    sweep = 360 * (0.62 * smooth(sw) + 0.38 * smooth(sw_post))                                  # the reveal sweep
    th_total = th + sweep
    # the bolt, rotated about the emblem centre, through the camera
    bw = np.zeros((H, W, 4), F32); bw[y0:y1, x0:x1] = bolt
    Rm = cv2.getRotationMatrix2D((ex, ey), -th_total, 1.0)
    Mt = np.vstack([M, [0, 0, 1]]) @ np.vstack([Rm, [0, 0, 1]])
    bc = cv2.warpAffine(bw, Mt[:2].astype(F32), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
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
            cv2.line(cvm, (int(p0[0] * 4), int(p0[1] * 4)), (int(p1[0] * 4), int(p1[1] * 4)), 255, max(1, int(R_s / 60)), cv2.LINE_AA, shift=2)
        mk_face = disc_mask(tx, ty, R_s * 0.92, 2) * (1 - (m if sweep > 0 else 0))
        o = np.clip(o + light_rgb(cvm, 0.55 * am, GOLDL, AMBR), 0, 1)
        o = o + mk_face[..., None] * PEACH * 0.10 * am
    o = o * (1 - bc[..., 3:4] * lift) + bc[..., :3] * bc[..., 3:4] * lift
    return np.clip(o, 0, 1)

# ---- the loop: the last memory stops once more, then restarts on frame 0 -----------------------------------------------
LOOP_N = 30
def frame_virtual(fv):
    s0 = SHOTS[0]; out, _ = base15(s0, fv)
    return out

def loop_out(img, f, s):
    """THE LOOP: on "know" the last memory stops (the drain and the hush of the still) and then time restarts: the
    shockwave races out and frame 0 (the watch, the next "I don't got time") is behind it at the wrap."""
    k = f - (s["f1"] - LOOP_N)
    if k < 0: return img
    u = k / (LOOP_N - 1)
    a = smooth(clamp(u / 0.35, 0, 1))
    lum = lum8(img)[..., None]; o = img * (1 - 0.55 * a) + lum * np.array([1.04, 0.98, 0.96], F32) * 0.55 * a
    v = clamp((u - 0.40) / 0.60, 0, 1)
    if v <= 0: return o
    under = frame_virtual(f - E.DUR_F); cx, cy = W * 0.5, H * 1.02
    R = 40 + 2300 * eout(v, 1.8); d = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2) + 1e-3
    env = np.exp(-((d - R) / 90) ** 2); disp = 34 * env * (1 - v)
    mx = (_GX - (_GX - cx) / d * disp).astype(F32); my = (_GY - (_GY - cy) / d * disp).astype(F32)
    ow = cv2.remap(o, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    m = np.clip((R - d) / 60 + 0.5, 0, 1).astype(F32); res = mixm(ow, under, m)
    fr = np.exp(-((d - R) / 40) ** 2) * (1 - v) ** 1.2
    lay = np.zeros((H, W, 3), F32); addc(lay, cv2.GaussianBlur(fr.astype(F32), (0, 0), 24), PEACH, 0.35)
    res = np.clip(res + lay, 0, 1)
    if v >= 1: return under
    return res

def loop_in15(out, f, k):
    return out

TR2.update({"vibrate": (vibrate, 12, 8), "streak_pass": (streak_pass, 5, 7), "time_slice15": (time_slice15, 6, 10),
            "edge_current15": (edge_current15, 10, 14), "whip_up15": (whip_up15, 6, 8), "light_leak15": (light_leak15, 10, 12),
            "strike_cut": (strike_cut, 6, 8), "time_stop": (time_stop, 4, 14), "time_restart": (time_restart, 6, 16),
            "eye_iris15": (eye_iris15, 12, 14), "speed_whip15": (speed_whip15, 5, 7), "wind_gust": (wind_gust, 6, 10),
            "focus_rack15": (focus_rack15, 10, 12), "emblem_clock": (emblem_clock, EC_PRE, EC_POST), "afterimage15": (afterimage15, 10, 10),
            "panel_run15": (panel_run15, 8, 12), "loop_in15": ((lambda A, B, j, f, sa, sb: B), 0, 1)})

# ---- the frame ----------------------------------------------------------------------------------------------------------
def timepiece_draw(out, *a, **k):
    """(the hero: the timepiece, drawn by emblem_clock's marks and the stopped-time pieces)"""
    return out

def base15(s, f):
    if s["n"] == "still": return still_fx(s, f), None
    img, person = base11(s, f)
    if s["n"] == "alone": img = loop_out(img, f, s)
    return img, person

_B15 = {}
def edge15(S_, which):
    key = (S_["n"], which)
    if key not in _B15:
        if len(_B15) > 8: _B15.clear()
        fr = S_["f0"] if which == "first" else S_["f1"] - 1
        if S_["n"] == "still": _B15[key] = still_fx(S_, fr)
        else: _B15[key] = base11(S_, fr)[0]
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
