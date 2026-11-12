# (v18 carries v17 MR. BLUE SKY's toolkit below, unchanged; the v18 CREEP section follows it.)
# ============================================================================ v17 — MR. BLUE SKY (The Flash × ELO "Mr. Blue Sky")
# After the storm. Frame 0 is storm clouds lit by lightning; on "Hey!" the sun breaks through (SUN BREAK) and he runs down
# the avenue through a sunny city, a new scene on every beat. THE SUN (the focal piece) rises behind him on "the sun
# shines brightly" and its lens flare's ghosts line up; one opens into the next shot (GHOST IRIS). "Where once was pity":
# a raindrop, the clouds gather and part (CLOUD BREAK) on "Mr. Blue Sky". The chorus: the real chest emblem glints and
# blazes into the sun (EMBLEM SUN). "Hide away for so long": the clouds roll back over the sun (CLOUD OVER) into frame 0.
# Look BLUE SKY: high-key, cerulean skies, sunny gold highlights, the suit's red rich, skin natural, a soft warm bloom.
HOT = np.array([0.94, 0.97, 1.00], F32)                    # BGR white-hot
GOLD17 = np.array([0.32, 0.74, 1.00], F32)                 # BGR sun gold
SKYB = np.array([1.00, 0.74, 0.34], F32)                   # BGR cerulean
WARM = np.array([0.46, 0.70, 1.00], F32)                   # BGR warm white
ROSE = np.array([0.62, 0.48, 1.00], F32)                   # BGR rose (a lens ghost)
TEAL17 = np.array([0.80, 0.86, 0.40], F32)                 # BGR teal-green (a lens ghost)
STORMC = np.array([0.82, 0.76, 0.70], F32)                 # BGR storm grey
CRIM17 = np.array([0.18, 0.14, 0.86], F32)
AMB = GOLD17; AMBR = GOLD17; TUNG = WARM; CYAN = SKYB; HALO = GOLD17
GOLDW, GOLD2, GOLD, EMBER2 = HOT.copy(), GOLD17.copy(), GOLD17.copy(), GOLD17.copy()
if E.VER == "v17":
    for _s in E.SHOTS:
        _s.setdefault("target", 0.47 if _s.get("look", "sky") == "sky" else 0.40)

_keys_at_pre16 = keys_at
_tmap_pre16 = tmap
_src_time_pre16 = src_time
_DK = {}
_B16 = {}
_HO = {}
_GXQ = (np.arange(W // 4, dtype=F32)[None, :] * 4 + 2).repeat(H // 4, 0)
_GYQ = (np.arange(H // 4, dtype=F32)[:, None] * 4 + 2).repeat(W // 4, 1)


def keys_at(keys, u):
    """LinZ keys (EDL) read as a straight line, valid outside 0..1: the roof's push keeps one speed across the wrap."""
    if getattr(keys, "linear", False):
        (u0, v0), (u1, v1) = keys[0], keys[-1]; return v0 + (v1 - v0) * (u - u0) / (u1 - u0)
    return _keys_at_pre16(keys, u)

def tmap(s, u):
    """tneg shots (the roof) read their source before u = 0 too (the tmap's first key sits at negative u): the loop's
    virtual frames show the real rooftop footage running on into frame 0, not a held frame."""
    if u < 0 and s.get("tneg"):
        ks = s["tmap"]; return float(np.interp(u, [k[0] for k in ks], [k[1] for k in ks]))
    return _tmap_pre16(s, u)

def src_time(s, f):
    """tneg shots: the speed estimate at negative u without the 0..1 clamp (it divided by ~0 there and the sampler
    smeared frames of another shot into the loop's virtual frames)."""
    if s.get("tneg") and f < s["f0"] + 2:
        n = max(1, s["f1"] - s["f0"]); u = (f - s["f0"]) / n; du = 1.0 / n
        return tmap(s, u), u, abs(tmap(s, u + du) - tmap(s, u - du)) / (2 * du * n / FPS)
    return _src_time_pre16(s, f)

def shift_img(img, dx, dy=0.0):
    M = np.float32([[1, 0, dx], [0, 1, dy]]); return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def defocus(img, r):
    if r < 0.6: return img
    if r < 6: return cv2.GaussianBlur(img, (0, 0), r / 2)
    q = 4; sm = cv2.resize(img, (W // q, H // q), interpolation=cv2.INTER_AREA)
    sm = sm + np.clip(sm - 0.58, 0, 1) * 2.2
    rr = int(math.ceil(r / q))
    if rr not in _DK:
        k = np.zeros((2 * rr + 1, 2 * rr + 1), F32); cv2.circle(k, (rr, rr), rr, 1.0, -1, cv2.LINE_AA); _DK[rr] = k / k.sum()
    return np.clip(cv2.resize(cv2.filter2D(sm, -1, _DK[rr]), (W, H), interpolation=cv2.INTER_LINEAR), 0, 1)

def defocus16(img, r):
    """defocus with no jump where the gaussian hands over to the bokeh disc."""
    if r < 0.6: return img
    g = cv2.GaussianBlur(img, (0, 0), r / 2)
    if r < 3: return g
    w = clamp((r - 3) / 6, 0, 1); return g * (1 - w) + defocus(img, max(r, 6.01)) * w

def shot_by(name):
    return next(s for s in SHOTS if s["n"] == name)

def e_of(f): return f / FPS / E.HB

def lumf(img): return img[..., 0] * 0.114 + img[..., 1] * 0.587 + img[..., 2] * 0.299

def init_hits():
    HITS.clear()

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

def face_soft(s, f, pad=1.0, q=4):
    """a soft ellipse over the face (1 on the face), for keeping graphics off it."""
    fs = face_scr(s, f) if s.get("face") is not None else None
    if not fs and s.get("face_hint"): fs = s["face_hint"]
    if not fs: return None
    m = np.zeros((H // q, W // q), F32)
    cv2.ellipse(m, (int(fs[0] / q), int(fs[1] / q)), (int(fs[2] * 0.95 * pad / q), int(fs[2] * 1.3 * pad / q)), 0, 0, 360, 1.0, -1)
    return cv2.resize(cv2.GaussianBlur(m, (0, 0), 12 / q), (W, H))[..., None]

def off_face(new, old, s, f, pad=1.0):
    m = face_soft(s, f, pad)
    return new if m is None else new * (1 - m) + old * m

def face_keep(s, f, pad=1.2):
    m = face_soft(s, f, pad)
    return 1.0 if m is None else (1 - m)

def body_only(person, s, f):
    """his matte below the chin (lightning is born on his shoulders and arms, never round his head)."""
    if person is None: return None
    fs = face_scr(s, f) if s.get("face") is not None else None
    if not fs: return person
    y0 = int(clamp(fs[1] + fs[2] * 1.05, 0, H)); p_ = person.copy(); p_[:y0] = 0; return p_

def hi_point(img, s=None, f=None, thr=0.70):
    """the centroid of the brightest light in a frame (off the face)."""
    q = 8; sm = cv2.resize(img, (W // q, H // q), interpolation=cv2.INTER_AREA); L = sm.max(2)
    m = np.clip((L - thr) / 0.2, 0, 1)
    if s is not None:
        fm = face_soft(s, f, 1.6, q)
        if fm is not None: m = m * (1 - cv2.resize(fm[..., 0], (W // q, H // q)))
    if m.sum() < 0.5: return W / 2, H * 0.45
    ys, xs = np.nonzero(m > 0.05); w_ = m[ys, xs]
    return float((xs * w_).sum() / w_.sum() * q + q / 2), float((ys * w_).sum() / w_.sum() * q + q / 2)

def frame_virtual(fv, with_person=False):
    s0 = SHOTS[0]; out, person = base17(s0, fv)
    return (out, person) if with_person else out

def home_cam(t):
    t = clamp(t, 0, 1); return t * t * t * (t * (6 * t - 15) + 10)

def soft_rect(cx, cy, hw, hh, fe):
    """1 inside the rect, a soft edge of width fe outside it (outward feather)."""
    dx = np.abs(_GX - cx) - hw; dy = np.abs(_GY - cy) - hh
    return (np.clip(1 - dx / fe, 0, 1) * np.clip(1 - dy / fe, 0, 1)).astype(F32)

def edge15(S_, which):
    key = (S_["n"], which)
    if key not in _B16:
        if len(_B16) > 8: _B16.clear()
        fr = S_["f0"] if which == "first" else S_["f1"] - 1
        _B16[key] = base17(S_, fr)
    return _B16[key][0]

def edge_person(S_, which):
    edge15(S_, which); return _B16[(S_["n"], which)][1]


def smoother(t):
    t = clamp(t, 0, 1); return t * t * t * (t * (6 * t - 15) + 10)

# ---- grade: BLUE SKY ---------------------------------------------------------------------------------------------------
LOOKS17 = {"sky": dict(sh=(0.026, 0.010, -0.010), hi=(-0.044, 0.008, 0.044), sat=1.04, skyk=0.45),
           "storm": dict(sh=(0.030, 0.014, 0.004), hi=(0.012, 0.004, -0.008), sat=0.50, skyk=0.0)}
E_EV17 = {}
_LUTS = {}
def lut17():
    if "n" not in _LUTS:
        x = np.linspace(0, 1, 1024, dtype=np.float32)
        _LUTS["n"] = (x, PchipInterpolator([0, .05, .20, .50, .80, .95, 1], [0.034, 0.062, 0.205, 0.520, 0.830, 0.950, 0.982])(x).astype(np.float32))
    return _LUTS["n"]

_grade_pre17 = grade
def grade(img, s, f):
    lk = s.get("look")
    if lk not in LOOKS17: return _grade_pre17(img, s, f)
    P_ = LOOKS17[lk]; g, gains = corr9(s); ev = (s.get("ev") or 0) + E_EV17.get(s["n"], 0.0)
    lx, ly = lut17()
    if in_unit(img): x = apply_lut3(img, tone_lut(("bs17", s["n"], round(ev, 3), float(g), tuple(float(v) for v in gains)), gains, g, ev, lx, ly))
    else:
        x = np.clip(img * gains, 0, 1) ** g
        if ev: x = np.clip(x * 2 ** ev, 0, 1)
        x = np.interp(x, lx, ly).astype(F32)
    B, G, R = (np.ascontiguousarray(x[..., c]) for c in range(3))
    L = B * 0.114 + G * 0.587 + R * 0.299
    hue = (R - G) / (R + 1e-3)
    skin = np.clip(1 - np.abs(hue - 0.22) / 0.22, 0, 1) * np.clip((R - B) * 6, 0, 1) * np.clip(L * 3, 0, 1)
    red = np.clip((R - np.maximum(G, B)) * 3.0 - 0.3, 0, 1) * (1 - skin)                      # the suit keeps its red
    sky = np.clip((B - np.maximum(R, G * 0.92)) * 5.0, 0, 1) * np.clip((L - 0.28) * 3, 0, 1)   # blue sky (and blue light)
    sat = (P_["sat"] + 0.06 * skin + 0.22 * red + P_["skyk"] * sky) * s.get("satk", 1.0)
    sh = (1 - L) ** 2.2 * (1 - 0.6 * skin); hi = np.clip((L - 0.55) / 0.45, 0, 1) ** 1.3 * (1 - sky)
    o = np.empty(x.shape, F32); push = (0.035, 0.004, -0.030)                                 # the sky leans cerulean
    for c, Pc in enumerate((B, G, R)):
        o[..., c] = L + (Pc - L) * sat + sh * P_["sh"][c] + hi * P_["hi"][c] + sky * P_["skyk"] * push[c]
    return np.clip(o, 0, 1, out=o)

# ---- the finish: a soft warm bloom round the light, a faint sun streak on the brightest points, fine grain --------------
_FIN = {}
def finish17(out, f, s, mix=None):
    if "v" not in _FIN:
        grain(0, 0.010); _FIN["v"] = np.repeat(0.86 + 0.14 * VIG, 3, axis=2)
    k = ("g", f % 6)
    if k not in _FIN: _FIN[k] = np.repeat(grain(f, 0.009), 3, axis=2)
    o = out
    m_ = mix if mix is not None else (1.0 if s.get("look") == "storm" else 0.0)              # 0 sunny, 1 storm
    small = cv2.resize(o, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    mx = small.max(2)
    hi_ = np.clip(mx - 0.66, 0, 1)
    bl = cv2.resize(cv2.GaussianBlur(hi_, (0, 0), 5) * 0.5 + cv2.GaussianBlur(hi_, (0, 0), 18) * 0.5, (W, H))
    addc(o, bl, GOLD17 * (1 - m_) + STORMC * m_, 0.34 * (1 - 0.6 * m_))                     # the warm bloom
    pt = np.clip(mx - 0.84, 0, 1) * 3.0
    st = cv2.resize(cv2.GaussianBlur(pt, (0, 0), sigmaX=28, sigmaY=0.5), (W, H))
    addc(o, st, (GOLD17 * 0.6 + HOT * 0.4) * (1 - m_) + SKYB * m_, 0.24)
    o *= _FIN["v"]; o += _FIN[k]
    return np.clip(o, 0, 1, out=o)

# ---- the beat camera: a punch on every beat (a kick on each), stronger on the half bar and the bar ----------------------
def beat_e(e): return 2 * math.floor(e / 2 + 1e-9)
def cam_live(e): return 1.0 <= e < E.E_LOOP                                                 # the first punch is on e2: frame 0 stays clean for the loop

def beat_bounce(f):
    e = e_of(f)
    if not cam_live(e): return 1.0
    eb = beat_e(e); dt = (e - eb) * E.HB
    amp = 0.036 if eb % 8 == 0 else (0.022 if eb % 4 == 0 else 0.012)
    return 1 + amp * math.exp(-dt / 0.075)

def beat_fx(out, f):
    e = e_of(f)
    if not cam_live(e): return out
    eb = beat_e(e); dt = (e - eb) * E.HB
    if eb % 4 != 0 or dt > 0.05: return out
    k = math.exp(-dt / 0.020)
    o = radial_blur(out, W / 2, H * 0.46, 1.0, 1.0 + 0.028 * k, 4)
    return np.clip(rgb_split(o, 4 * k) if eb % 8 == 0 else o, 0, 1)

# ---- THE SUN (the hero asset): a white-hot disc, a gold glow, rays that turn, its lens ghosts -----------------------------
def sun_draw(cx, cy, r, amt, rot=0.0, rays=1.0, wide=1.0):
    """the sun as a lens sees it (H, W, 3), drawn at quarter resolution: a white-hot disc with a soft limb, a layered bloom,
    six thin aperture spikes that turn with `rot`, a faint fan of atmosphere and a thin anamorphic streak."""
    dx = _GXQ - cx; dy = _GYQ - cy; d = np.sqrt(dx * dx + dy * dy)
    core = np.clip(1.12 - d / r, 0, 1) ** 0.7
    glow = np.exp(-(d / (r * 2.0)) ** 1.6) * 0.60 + (np.exp(-(d / (r * 6.5)) ** 1.2) * 0.30 + np.exp(-d / (r * 18.0)) * 0.10) * wide
    sp = np.zeros_like(d); th_ = 4.0 + 0.05 * r
    for k in range(3):                                                                         # a hexagonal aperture: three lines, six spikes
        a = rot + k * math.pi / 3
        perp = np.abs(dx * math.sin(a) - dy * math.cos(a))
        sp += np.exp(-(perp / th_) ** 2) * np.exp(-d / (r * (3.2 + 0.8 * k)))
    sp *= np.clip(d / r - 0.7, 0, 1)
    ang = np.arctan2(dy, dx)
    fan = (0.5 + 0.5 * np.cos(ang * 9 + rot * 0.5)) ** 3 * np.exp(-d / (r * 5.0)) * 0.10
    streak = np.exp(-(dy / (3.0 + 0.04 * r)) ** 2) * np.exp(-np.abs(dx) / (r * 11.0)) * 0.30
    lay = (core[..., None] * HOT * 1.6 + glow[..., None] * (GOLD17 * 0.65 + HOT * 0.35)
           + ((sp * 0.85 + fan) * rays)[..., None] * (HOT * 0.5 + GOLD17 * 0.5) + streak[..., None] * WARM)
    return cv2.resize((lay * amt).astype(F32), (W, H), interpolation=cv2.INTER_LINEAR)

GHOSTS = [(0.30, 26, GOLD17, 0.55), (0.55, 60, SKYB, 0.32), (0.85, 18, ROSE, 0.60), (1.15, 110, TEAL17, 0.22), (1.45, 40, GOLD17, 0.30)]
def ghost_pts(sx, sy):
    cx, cy = W / 2, H / 2
    return [(cx + (cx - sx) * k, cy + (cy - sy) * k, r, col, a) for k, r, col, a in GHOSTS]

def ghosts_draw(sx, sy, amt, grow=None):
    """the lens ghosts along the line from the sun through the frame's centre: soft discs with a brighter rim."""
    lay = np.zeros((H // 4, W // 4, 3), F32)
    for i, (gx, gy, r, col, a) in enumerate(ghost_pts(sx, sy)):
        if grow is not None and i == 1: continue
        d = np.sqrt((_GXQ - gx) ** 2 + (_GYQ - gy) ** 2)
        disc = np.clip((r - d) / (0.35 * r) + 0.5, 0, 1) * 0.55 + np.exp(-((d - r) / (0.10 * r + 2)) ** 2) * 0.45
        lay += disc[..., None] * col * a
    return cv2.resize(lay * amt, (W, H), interpolation=cv2.INTER_LINEAR)

# ---- clouds (the weather): a fixed fractal texture, advected; density from a coverage ------------------------------------
_CL = {}
def cloud_tex():
    if "t" not in _CL:
        rng = np.random.default_rng(1717); h, w = H // 4, W // 4 * 2
        acc = np.zeros((h, w), F32); amp = 1.0
        for sig, a_ in ((64, 1.0), (32, 0.55), (14, 0.30), (6, 0.15), (2.5, 0.07)):              # puffy, with cauliflower edges
            n = rng.standard_normal((h, w)).astype(F32); n = cv2.GaussianBlur(n, (0, 0), sig, borderType=cv2.BORDER_REFLECT)
            acc += a_ * n / (n.std() + 1e-6)
        acc = (acc - acc.min()) / (acc.max() - acc.min()); _CL["t"] = acc
    return _CL["t"]

def cloud_field(t, cover, vx=60.0, ox=0.0):
    """cloud density (H/4, W/4) in 0..1 for a coverage 0..1; the texture drifts sideways at vx px/s (smoothly, sub-pixel)."""
    T = cloud_tex(); w = W // 4
    off = (ox + vx * t) / 4.0; i0 = int(math.floor(off)) % w; fr = off - math.floor(off)
    a = np.roll(T, -i0, axis=1)[:, :w]; b = np.roll(T, -i0 - 1, axis=1)[:, :w]
    N = a * (1 - fr) + b * fr
    if cover <= 0: return np.zeros_like(N)
    thr = 0.80 - 1.00 * cover                                                                 # 0 -> a few wisps, 1 -> overcast
    return np.clip((N - thr) / 0.20, 0, 1)

def cloud_N(t, vx=90.0, ox=0.0):
    T = cloud_tex(); w = W // 4; off = (ox + vx * t) / 4.0; i0 = int(math.floor(off)) % w; fr = off - math.floor(off)
    return np.roll(T, -i0, axis=1)[:, :w] * (1 - fr) + np.roll(T, -i0 - 1, axis=1)[:, :w] * fr

def clouds(t, covmap, vx=90.0, lit=1.0, dark=0.0, tint=None, ox=0.0, soft=0.20, sun=(0.5, -0.3)):
    """clouds over the frame: (rgb, density) at full resolution. Density from a coverage map; lit like real cloud: the light
    comes from `sun` (a screen point, in frame units), so the side facing it is bright and the cloud behind thick cloud is
    in its shadow (blue-grey bellies); thin edges facing the light get a silver lining."""
    N = cloud_N(t, vx, ox)
    dens = np.clip((N - (0.80 - covmap)) / soft, 0, 1).astype(F32)
    hq, wq = dens.shape
    ldx, ldy = sun[0] * wq - wq / 2, sun[1] * hq - hq / 2; ln = math.hypot(ldx, ldy) + 1e-6; ldx, ldy = ldx / ln, ldy / ln
    db = cv2.GaussianBlur(dens, (0, 0), 3.0)
    od = np.zeros_like(db)
    for dd, wgt in ((3, 0.30), (7, 0.30), (13, 0.25), (22, 0.15)):                            # the cloud between it and the light
        od += wgt * cv2.warpAffine(db, np.float32([[1, 0, -ldx * dd], [0, 1, -ldy * dd]]), (wq, hq), borderMode=cv2.BORDER_REPLICATE)
    shade = np.exp(-2.4 * od) * (0.80 + 0.20 * (1 - db))                                      # self-shadowed: bright tops, dark bellies
    shade = np.clip((0.20 + 0.95 * shade) * lit * (1 - 0.50 * dark), 0, 1.15).astype(F32)
    lining = np.clip(dens * (1 - dens) * 4, 0, 1) * np.exp(-1.6 * od)                           # thin edges facing the light
    hi = (np.array([0.95, 0.97, 1.00], F32) if tint is None else tint)
    lo = np.array([0.60, 0.50, 0.42], F32) * (1 - 0.45 * dark)                                 # blue-grey shadow (BGR)
    rgb = shade[..., None] * hi + (1 - np.clip(shade, 0, 1)[..., None]) * lo + (lining * 0.35 * lit)[..., None] * (HOT * 0.6 + GOLD17 * 0.4)
    return cv2.resize(rgb.astype(F32), (W, H), interpolation=cv2.INTER_LINEAR), cv2.resize(cv2.GaussianBlur(dens, (0, 0), 0.8), (W, H))

# ---- in-shot animations (each motivated by its shot, kept off faces) ---------------------------------------------------
def a_shine(img, person, s, f):
    """SUNSHINE: the sun catches every bright edge as a four-point glint, breathing with the beat."""
    q = 4; sm = cv2.resize(img, (W // q, H // q), interpolation=cv2.INTER_AREA)
    hi = np.clip(sm.max(2) - 0.80, 0, 1) * 4.0
    e = e_of(f); pulse = 0.75 + 0.25 * math.exp(-((e - beat_e(e)) * E.HB) / 0.12)
    star = cv2.GaussianBlur(hi, (0, 0), sigmaX=22, sigmaY=0.8) + cv2.GaussianBlur(hi, (0, 0), sigmaX=0.8, sigmaY=22)
    lay = cv2.resize(star * 1.4 + cv2.GaussianBlur(hi, (0, 0), 6) * 0.8, (W, H))
    o = img.copy(); addc(o, lay.astype(F32), GOLD17 * 0.6 + HOT * 0.4, 0.55 * pulse)
    return off_face(np.clip(o, 0, 1), img, s, f, 1.2)

def god_rays(img, person, sx, sy, amt, src_thr=0.62, n=14):
    """light shafts from (sx, sy) through the bright parts of the frame, behind his matte."""
    q = 4; sm = cv2.resize(img, (W // q, H // q), interpolation=cv2.INTER_AREA)
    m = np.clip((lumf(sm) - src_thr) / 0.25, 0, 1)
    if person is not None: m = m * (1 - cv2.resize(np.clip(person * 1.3, 0, 1), (W // q, H // q)))
    acc = np.zeros_like(m); ws = 0.0
    for i in range(n):
        sc = 1.0 + 0.06 * i; d_ = 0.88 ** i
        acc += cv2.warpAffine(m, cv2.getRotationMatrix2D((sx / q, sy / q), 0, sc), (W // q, H // q), flags=cv2.INTER_LINEAR, borderValue=0) * d_; ws += d_
    rays = cv2.resize(cv2.GaussianBlur(acc / ws, (0, 0), 1.0), (W, H))
    if person is not None: rays = rays * (1 - np.clip(person * 1.2, 0, 1))
    o = img.copy(); addc(o, rays.astype(F32), GOLD17 * 0.7 + HOT * 0.3, amt)
    return o

def a_rays(img, person, s, f):
    """GOD RAYS: the sun is just above the frame; its shafts come down through the leaves behind him, turning slowly."""
    t = (f - s["f0"]) / FPS; e = e_of(f); pulse = 0.85 + 0.15 * math.exp(-((e - beat_e(e)) * E.HB) / 0.15)
    o = god_rays(img, person, W * (0.78 - 0.05 * t), -H * 0.06, 0.85 * pulse, 0.55)
    return off_face(np.clip(o, 0, 1), img, s, f, 1.1)

def a_sunbreak(img, person, s, f):
    """SUN BREAK (frame 0, the storm): from e1 the sun begins to burn through the clouds; the thick cloud still hides part
    of it (the frame's own dark cloud masks it), its rays come through the thin."""
    e = e_of(f); g = smooth(clamp((e - 0.4) / 3.0, 0, 1))
    if g <= 0: return img
    sx, sy = W * 0.72, H * 0.20
    lay = sun_draw(sx, sy, 26 + 18 * g, 0.85 * g ** 1.4, rot=f * 0.02, rays=0.7)
    occ = cv2.GaussianBlur(np.clip((0.50 - lumf(img)) / 0.30, 0, 1), (0, 0), 6)               # the thick cloud in front of it
    return np.clip(img * (1 + 0.06 * g) + lay * (1 - 0.65 * occ)[..., None], 0, 1)

_CRK = {}
def a_crackle(img, person, s, f):
    """CRACKLE: the suit charges in the sun: short gold arcs crawl over his shoulders and arms (his matte, below his chin),
    each living a few frames, stronger on the beat."""
    if person is None: return img
    body = body_only(person, s, f)
    if body is None: return img
    key = (s["n"], f // 3)
    q = 8; bq = cv2.resize(body, (W // q, H // q), interpolation=cv2.INTER_AREA)
    ys, xs = np.nonzero(bq > 0.6)
    if len(xs) < 20: return img
    e = e_of(f); pulse = 0.55 + 0.45 * math.exp(-((e - beat_e(e)) * E.HB) / 0.10)
    rng = np.random.default_rng(sum(ord(c_) for c_ in s["n"]) * 7919 + f // 3)                 # deterministic in every process
    cv = bolt_canvas()
    for k in range(4):
        i = int(rng.integers(len(xs))); p0 = (xs[i] * q + 4.0, ys[i] * q + 4.0)
        ang = rng.uniform(0, 2 * math.pi); L = rng.uniform(170, 320)
        p1 = (p0[0] + L * math.cos(ang), p0[1] + L * math.sin(ang))
        put_bolt(cv, p0, p1, 17800 + k + 13 * (f // 2), 3, 0.32, 6, 2, val=255)
    lt = light_rgb(cv, 1.25 * pulse, HOT, GOLD17)
    lt = lt * np.clip(cv2.GaussianBlur(body, (0, 0), 6) * 1.6, 0, 1)[..., None]                 # it stays on his suit
    return np.clip(img + kmul(lt, face_keep(s, f, 1.10)), 0, 1)

_MOT = {}
def a_motes(img, person, s, f):
    """MOTES: dust in the sunlight drifts through the air and catches the light (sub-pixel motion, a smooth twinkle)."""
    if "p" not in _MOT:
        rng = np.random.default_rng(1771)
        _MOT["p"] = (rng.uniform(0, W, 90), rng.uniform(0, H, 90), rng.uniform(3.0, 8.0, 90), rng.uniform(0, 6.28, 90), rng.uniform(-18, 18, 90), rng.uniform(-30, -8, 90))
    X0, Y0, rad, ph, vx, vy = _MOT["p"]; t = (f - s["f0"]) / FPS
    X = (X0 + vx * t + 9 * np.sin(0.9 * t + ph)) % W; Y = (Y0 + vy * t + 6 * np.cos(0.7 * t + ph)) % H
    beam = np.exp(-(((X * 0.6 + Y * 0.8) - (W * 0.6 * 0.9 + H * 0.8 * 0.2)) / 520.0) ** 2)      # brighter in the sunbeam
    br = (0.35 + 0.65 * (0.5 + 0.5 * np.sin(2.3 * t + ph * 3))) * (0.25 + 0.75 * beam)
    cv = np.zeros((H // 2, W // 2), np.uint8)
    for x_, y_, r_, b_ in zip(X, Y, rad, br):
        cv2.circle(cv, (int(x_ * 8), int(y_ * 8)), int(r_ * 8), int(255 * b_), -1, cv2.LINE_AA, shift=4)
    m = cv2.resize(cv.astype(F32) / 255, (W, H), interpolation=cv2.INTER_LINEAR)
    m = m * 0.8 + cv2.GaussianBlur(m, (0, 0), 5) * 1.6
    if person is not None: m = m * (1 - 0.6 * np.clip(person, 0, 1))                           # mostly in the air round him
    o = img.copy(); addc(o, kmul(m.astype(F32), face_keep(s, f, 1.1)), WARM * 0.7 + HOT * 0.3, 0.95)
    return np.clip(o, 0, 1)

ANIMS = {"shine": a_shine, "rays": a_rays, "sunbreak": a_sunbreak, "crackle": a_crackle, "motes": a_motes}



# ---- helpers for the transitions ---------------------------------------------------------------------------------------
def live_keep(sa, sb, j, f, w, pad=1.25):
    """face_keep of whichever shot is on screen (its live frame, or its edge frame while it is held)."""
    if w < 0.5: return face_keep(sa, f if j < 0 else sa["f1"] - 1, pad)
    return face_keep(sb, f if j >= 0 else sb["f0"], pad)

def kmul(lay, k):
    return lay if isinstance(k, float) else lay * (k if lay.ndim == 3 else k[..., 0])

def strip_pan(A, B, q, axis, rev=False, blur=170, ov=320):
    """A and B as one strip, panned (a whip): axis 0 vertical, 1 horizontal; rev puts B first. Mid-move the two meet in a
    feathered band (each side extended by its own mirror), which closes to nothing at both ends, so the first and last
    frames are pure A and pure B; the blur is a smooth box along the pan."""
    p = smooth(clamp(q, 0, 1)); sp = math.sin(math.pi * clamp(q, 0, 1))
    X, Y = (B, A) if rev else (A, B)
    if axis == 1: X, Y = np.ascontiguousarray(X.transpose(1, 0, 2)), np.ascontiguousarray(Y.transpose(1, 0, 2))
    n = X.shape[0]
    strip = np.concatenate([X, Y], axis=0)
    hw = int(ov * 0.5 * sp)
    if hw >= 2:
        r = np.arange(n - hw, n + hw)
        w = (0.5 - 0.5 * np.cos(np.linspace(0, math.pi, 2 * hw, dtype=F32)))[:, None, None]
        xe = np.where(r < n, r, 2 * n - 1 - r); ye = np.where(r >= n, r - n, n - 1 - r) if False else np.abs(r - n)
        strip[n - hw:n + hw] = X[np.clip(xe, 0, n - 1)] * (1 - w) + Y[np.clip(ye, 0, n - 1)] * w
    o0 = int(round((1 - p) * n)) if rev else int(round(p * n))
    view = np.ascontiguousarray(strip[o0:o0 + n])
    if axis == 1: view = np.ascontiguousarray(view.transpose(1, 0, 2))
    return hblur(view, 2 + blur * sp, vertical=(axis == 0))

# ---- SUN BURST (the storm -> the avenue): the sun behind the storm blazes out and the sunny avenue is under its light ----
SB_PT = (W * 0.72, H * 0.20)
def sun_burst(A, B, j, f, sa, sb, pre=12, post=16):
    x = (j + pre) / (pre + post - 1); sx, sy = SB_PT
    pk = math.exp(-((x - 0.42) / 0.15) ** 2)
    w = smooth(clamp((x - 0.36) / 0.14, 0, 1)); o = A * (1 - w) + B * w
    amt = (0.35 * smooth(clamp(x / 0.40, 0, 1)) + 1.0 * pk) * (1 - smooth(clamp((x - 0.55) / 0.45, 0, 1)))
    lay = sun_draw(sx, sy, 44 + 26 * pk, amt, rot=f * 0.02)
    gh = ghosts_draw(sx, sy, 0.55 * pk)
    o = o * (1 - 0.10 * pk) + lay + kmul(gh, live_keep(sa, sb, j, f, w))
    return np.clip(o, 0, 1)

# ---- RUN BY: he streaks past the lens, low; the cut is behind him ---------------------------------------------------------
def run_by(A, B, j, f, sa, sb, pre=5, post=7):
    q = (j + pre) / (pre + post - 1); x = -0.45 * W + 1.9 * W * ein(clamp(q, 0, 1), 1.3)
    cy = H * 0.72; hh = H * 0.13
    yy = (_GY - cy) / hh
    body = (np.exp(-yy ** 4) * np.clip((_GX - (x - W * 0.55)) / (W * 0.55), 0, 1) * np.clip((x + 60 - _GX) / 60, 0, 1)).astype(F32)
    w = smooth(clamp((q - 0.15) / 0.70, 0, 1)); under = A * (1 - w) + B * w
    kb = math.sin(math.pi * clamp(q, 0, 1)) ** 1.5
    o = mixm(under, hblur(under, 110), np.clip(np.maximum(body * 1.3, kb * 0.8), 0, 1).astype(F32))
    fk = live_keep(sa, sb, j, f, w, 1.3); body = kmul(body, fk)
    o = o * (1 - 0.5 * body[..., None]) + body[..., None] * (CRIM17 * 0.6 + GOLD17 * 0.4) * 0.8
    cv = bolt_canvas()
    for k_ in range(3):
        yk = cy + (k_ - 1) * hh * 0.45
        put_bolt(cv, (x - W * 0.6, yk + 20 * math.sin(f * 0.6 + k_)), (x, yk), 7700 + k_ + 5 * (f // 2), 1, 0.25, 4, 0)
    lt = light_rgb(cv, 0.8 * math.sin(math.pi * clamp(q, 0, 1)), HOT, GOLD17)
    return np.clip(o + kmul(lt, fk), 0, 1)

# ---- SPEED ZOOM: speed lines burst from the centre and the camera punches through into the next shot -------------------
_SL = {}
def speed_lines():
    if "l" not in _SL:
        rng = np.random.default_rng(1771); cv = np.zeros((H // 2, W // 2), F32); cx, cy = W / 4, H / 4 * 0.92
        for i in range(80):
            a = rng.uniform(0, 2 * math.pi); r0 = rng.uniform(120, 300) / 2; r1 = r0 + rng.uniform(250, 800) / 2
            cv2.line(cv, (int((cx + math.cos(a) * r0) * 4), int((cy + math.sin(a) * r0) * 4)), (int((cx + math.cos(a) * r1) * 4), int((cy + math.sin(a) * r1) * 4)),
                     float(rng.uniform(0.4, 1.0)), 1, cv2.LINE_AA, shift=2)
        _SL["l"] = cv2.resize(cv2.GaussianBlur(cv, (0, 0), 0.8), (W, H))
    return _SL["l"]

def speed_zoom(A, B, j, f, sa, sb, pre=4, post=7):
    cx, cy = W / 2, H * 0.46
    if j < 0:
        u = (j + pre + 1) / pre; o = radial_blur(zoom_about(A, cx, cy, 1 + 0.30 * ein(u, 2)), cx, cy, 1.0, 1.0 + 0.20 * ein(u, 1.6), 6); amt = ein(u, 1.5)
    else:
        v = (j + 1) / post; o = zoom_about(B, cx, cy, 1.25 - 0.25 * eout(v, 2.5)); k = 0.18 * (1 - eout(v, 2))
        if k > 0.004: o = radial_blur(o, cx, cy, 1.0, 1.0 + k, 6)
        amt = (1 - v) ** 2
    lay = kmul(zoom_about(speed_lines(), cx, cy, 1 + 0.4 * amt), live_keep(sa, sb, j, f, 0 if j < 0 else 1, 1.25))
    o = o.copy(); addc(o, lay.astype(F32), HOT * 0.6 + GOLD17 * 0.4, 0.9 * amt)
    return np.clip(o, 0, 1)

# ---- GLINT SWEEP: the sun runs along a diagonal like light along glass, and the next shot is behind it -------------------
def glint_sweep(A, B, j, f, sa, sb, pre=6, post=6):
    x = (j + pre) / (pre + post - 1)
    proj = ((_GX * 0.6 + _GY * 0.8) / (W * 0.6 + H * 0.8)).astype(F32); pos = -0.15 + 1.3 * smooth(x)
    m = np.clip((pos - proj) / 0.03 + 0.5, 0, 1).astype(F32)
    o = A * (1 - m[..., None]) + B * m[..., None]
    fk = live_keep(sa, sb, j, f, smooth(x), 1.2)
    band = kmul(np.exp(-((proj - pos) / 0.016) ** 2).astype(F32), fk); glow = kmul(np.exp(-((proj - pos) / 0.07) ** 2).astype(F32), fk)
    addc(o, band, HOT, 0.85); addc(o, glow, GOLD17, 0.40)
    return np.clip(o, 0, 1)

# ---- SKY WHIP (down from the sky into the street), TILT UP (up into the sky), WHIP PAN, SUN WHIP, THROW WHIP ------------
def sky_whip(A, B, j, f, sa, sb, pre=5, post=6):
    return np.clip(strip_pan(A, B, (j + pre) / (pre + post - 1), 0), 0, 1)

def tilt_up(A, B, j, f, sa, sb, pre=6, post=8):
    return np.clip(strip_pan(A, B, (j + pre) / (pre + post - 1), 0, rev=True, blur=150), 0, 1)

def whip_pan(A, B, j, f, sa, sb, pre=5, post=6):
    return np.clip(strip_pan(A, B, (j + pre) / (pre + post - 1), 1), 0, 1)

def sun_whip(A, B, j, f, sa, sb, pre=5, post=6):
    """SUN WHIP: a whip pan right to left; the sun's streak rides the seam."""
    q = (j + pre) / (pre + post - 1); o = strip_pan(A, B, q, 1, rev=True)
    seam = (1 - smooth(clamp(q, 0, 1))) * W
    st = (np.exp(-((_GX - seam) / 60.0) ** 2) * np.exp(-((_GY - H * 0.30) / 9.0) ** 2) + 0.35 * np.exp(-((_GX - seam) / 260.0) ** 2) * np.exp(-((_GY - H * 0.30) / 120.0) ** 2)).astype(F32)
    addc(o, st, GOLD17 * 0.6 + HOT * 0.4, 1.1 * math.sin(math.pi * clamp(q, 0, 1)))
    return np.clip(o, 0, 1)

def throw_whip(A, B, j, f, sa, sb, pre=5, post=7):
    """THROW WHIP (the ball game -> the laugh): the ball leaves his hand and the camera whips up after it."""
    q = (j + pre) / (pre + post - 1); o = strip_pan(A, B, q, 0, rev=True, blur=190)
    bx = W * (0.30 + 0.45 * q); by = H * (0.80 - 0.62 * q - 0.25 * math.sin(math.pi * q))
    ball = (np.exp(-(((_GX - bx) / 14.0) ** 2 + ((_GY - by) / 60.0) ** 2))).astype(F32) * math.sin(math.pi * clamp(q, 0, 1))
    addc(o, ball, HOT, 0.9)
    return np.clip(o, 0, 1)

# ---- FLARE CUT: the brightest light in the shot flares across the lens ---------------------------------------------------
def flare_cut(A, B, j, f, sa, sb, pre=6, post=8):
    x = (j + pre) / (pre + post - 1); env = math.sin(math.pi * clamp(x, 0, 1)) ** 0.9
    if _HO.get("fc_n") != sa["n"]: _HO["fc_n"] = sa["n"]; _HO["fc"] = hi_point(edge15(sa, "last"), sa, sa["f1"] - 1, 0.62)
    px, py = _HO["fc"]
    w = smooth(clamp((x - 0.42) / 0.16, 0, 1)); o = A * (1 - w) + B * w
    d2 = (_GX - px) ** 2 + (_GY - py) ** 2
    bloom = np.exp(-d2 / (2 * (60 + 260 * env) ** 2)).astype(F32)
    streak = (np.exp(-((_GY - py) / (6 + 8 * env)) ** 2) * np.exp(-np.abs(_GX - px) / (200 + 900 * env))).astype(F32)
    fk = live_keep(sa, sb, j, f, w, 1.2)
    addc(o, kmul(bloom, fk), HOT * 0.4 + GOLD17 * 0.6, 0.55 * env); addc(o, kmul(streak, fk), GOLD17 * 0.7 + 0.3, 0.75 * env)
    return np.clip(o, 0, 1)

# ---- RAY RAKE: the sun's shafts rake across the frame from above and the next shot is in them ----------------------------
def ray_rake(A, B, j, f, sa, sb, pre=8, post=8):
    """RAY RAKE: a shaft of sun rakes down across the frame; the next shot is lit behind it."""
    x = (j + pre) / (pre + post - 1); env = math.sin(math.pi * clamp(x, 0, 1))
    proj = _GX * 0.55 + _GY * 0.835; L1 = W * 0.55 + H * 0.835
    pos = -260 + (L1 + 520) * smooth(clamp(x, 0, 1))
    m = np.clip((pos - proj) / 90 + 0.5, 0, 1).astype(F32)
    base = A * (1 - m[..., None]) + B * m[..., None]
    o = god_rays(base, PERSON.get(f), W * (-0.1 + 0.7 * smooth(x)), -H * 0.10, 1.0 * env, 0.45)
    band = np.exp(-((proj - pos) / 110.0) ** 2).astype(F32)
    addc(o, kmul(band, live_keep(sa, sb, j, f, smooth(x), 1.2)), GOLD17 * 0.6 + HOT * 0.4, 0.55 * env)
    return np.clip(o, 0, 1)


# ---- BLOOM CUT: the light blooms (the sun about to rise) and the next shot comes out of it -------------------------------
def bloom_cut(A, B, j, f, sa, sb, pre=8, post=10):
    """BLOOM CUT: the light blooms where the sun is about to rise, and the next shot opens out of the bloom."""
    x = (j + pre) / (pre + post - 1); k = math.sin(math.pi * clamp(x, 0, 1))
    sx, sy, _, _ = sun_path(E.E_SUN)
    d = np.sqrt((_GX - sx) ** 2 + (_GY - sy) ** 2).astype(F32)
    R = math.hypot(W, H) * 1.05 * smooth(clamp((x - 0.12) / 0.80, 0, 1)) ** 1.25
    m = np.clip((R - d) / (30 + 0.14 * R) + 0.5, 0, 1).astype(F32)
    base = A * (1 - m[..., None]) + B * m[..., None]
    hi = np.clip(base - 0.45, 0, 1); bl = cv2.GaussianBlur(hi, (0, 0), 24) * 1.2
    o = base + bl * k * (GOLD17 * 0.5 + 0.5)
    rim = np.exp(-((d - R) / (24 + 0.06 * R)) ** 2).astype(F32)
    addc(o, kmul(rim, live_keep(sa, sb, j, f, smooth(x), 1.2)), GOLD17 * 0.6 + HOT * 0.4, 0.75 * k)
    return np.clip(o, 0, 1)


# ---- PRISM ("it's stopped raining"): the light splits into its colours, a rainbow runs through, they come back together --
def prism(A, B, j, f, sa, sb, pre=6, post=8):
    x = (j + pre) / (pre + post - 1); k = math.sin(math.pi * clamp(x, 0, 1))
    w = smooth(clamp((x - 0.42) / 0.16, 0, 1)); base = A * (1 - w) + B * w
    d = 24 * k; o = base.copy()
    o[..., 2] = shift_img(np.ascontiguousarray(base[..., 2]), d, -0.6 * d); o[..., 0] = shift_img(np.ascontiguousarray(base[..., 0]), -d, 0.6 * d)
    proj = ((_GX * 0.8 - _GY * 0.6 + H * 0.6) / (W * 0.8 + H * 0.6)).astype(F32); pos = -0.1 + 1.2 * smooth(x)
    ph = (proj - pos) / 0.09 * math.pi; env = np.exp(-((proj - pos) / 0.09) ** 2) * 0.30 * k
    bow = np.stack([0.5 + 0.5 * np.cos(ph), 0.5 + 0.5 * np.cos(ph - 2.1), 0.5 + 0.5 * np.cos(ph - 4.2)], 2).astype(F32) * env[..., None]
    return np.clip(o + kmul(bow, live_keep(sa, sb, j, f, w, 1.2)), 0, 1)

# ---- BOLT CRACK: a bolt cracks down the frame and the next shot breaks through along it, sweeping across -----------------
_BC = {}
def bolt_crack(A, B, j, f, sa, sb, pre=4, post=8):
    q = (j + pre) / (pre + post - 1)
    if "p" not in _BC:
        rng = np.random.default_rng(1771); ys = np.linspace(-40, H + 40, 10); xs_ = np.array([(1 if k % 2 else -1) * (70 + 30 * rng.random()) for k in range(10)])
        yy = np.arange(-40, H + 41, 8, dtype=F32); xx = np.interp(yy, ys, xs_) + rng.normal(0, 5, len(yy)); xx = cv2.GaussianBlur(xx.astype(F32)[None], (0, 0), 0.8)[0]
        _BC["p"] = np.stack([xx, yy], 1).astype(F32)
    pts = _BC["p"]; xs = W * 1.08 - W * 1.25 * smooth(q)
    off = np.interp(np.arange(H, dtype=F32), pts[:, 1], pts[:, 0]).astype(F32)
    m = np.clip((_GX - (xs + off)[:, None]) / 6 + 0.5, 0, 1).astype(F32)
    o = A * (1 - m[..., None]) + B * m[..., None]
    cv = bolt_canvas(); cv2.polylines(cv, [np.stack([pts[:, 0] + xs, pts[:, 1]], 1).astype(np.int32)], False, 255, 3, cv2.LINE_AA)
    lt = light_rgb(cv, math.sin(math.pi * clamp(q, 0, 1)) ** 0.5, HOT, GOLD17)
    return np.clip(o + kmul(lt, live_keep(sa, sb, j, f, smooth(q), 1.2)), 0, 1)

# ---- RAIN RIPPLE ("where once was pity"): the last raindrop lands; its ring runs out and the next shot is inside it -------
def rain_ripple(A, B, j, f, sa, sb, pre=6, post=12):
    px, py = W * 0.28, H * 0.74
    if j < 0:
        u = (j + pre + 1) / pre; dy = py - H * 0.9 * (1 - ein(u, 1.8))
        o = A.copy(); addc(o, np.exp(-((_GX - px) ** 2 / (2 * 7.0 ** 2) + (_GY - dy) ** 2 / (2 * 16.0 ** 2))).astype(F32), HOT, 0.9)
        return np.clip(o, 0, 1)
    v = (j + 1) / post; R = 30 + 1900 * eout(v, 2.2)
    d = np.sqrt((_GX - px) ** 2 + (_GY - py) ** 2)
    disp = 18 * (1 - v) * np.sin(2 * np.pi * (d - R) / 70.0) * np.exp(-((d - R) / 120.0) ** 2)
    disp = kmul(disp.astype(F32), face_keep(sb, f, 1.3))
    nx = (_GX + disp * (_GX - px) / (d + 1e-3)).astype(F32); ny = (_GY + disp * (_GY - py) / (d + 1e-3)).astype(F32)
    Aw = cv2.remap(A, nx, ny, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT); Bw = cv2.remap(B, nx, ny, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    m = np.clip((R - 60 - d) / 40 + 0.5, 0, 1).astype(F32)[..., None]
    o = Aw * (1 - m) + Bw * m
    addc(o, kmul(np.exp(-((d - R) / 10.0) ** 2).astype(F32) * (1 - v), face_keep(sb, f, 1.3)), HOT, 0.25)
    return np.clip(o, 0, 1)

# ---- BALLOON RISE (Flash Day): the day's balloons rise past the lens, out of focus, and it is the ball game behind them ----
_BAL = {}
def balloon_rise(A, B, j, f, sa, sb, pre=6, post=8):
    x = (j + pre) / (pre + post - 1)
    if "b" not in _BAL:
        rng = np.random.default_rng(1780); cols = [CRIM17, GOLD17, np.array([0.20, 0.55, 1.00], F32), np.array([0.85, 0.45, 0.25], F32)]
        _BAL["b"] = [(float(rng.uniform(-0.05, 1.05) * W), float(rng.uniform(0, 1)), float(rng.uniform(90, 190)), cols[i % 4]) for i in range(18)]
    w = smooth(clamp((x - 0.40) / 0.20, 0, 1)); o = A * (1 - w) + B * w
    lay = np.zeros((H // 4, W // 4, 3), F32); al = np.zeros((H // 4, W // 4), F32)
    for bx, ph, r, col in _BAL["b"]:
        by = H * (1.15 + 0.55 * ph) - H * 2.0 * ein(clamp(x, 0, 1), 1.2)
        m = np.zeros((H // 4, W // 4), F32)
        cv2.ellipse(m, (int(bx / 4 * 4), int(by / 4 * 4)), (int(r / 4 * 4), int(r * 1.18 / 4 * 4)), 0, 0, 360, 1.0, -1, cv2.LINE_AA, shift=2)
        hl = np.zeros_like(m); cv2.circle(hl, (int((bx - r * 0.35) / 4 * 4), int((by - r * 0.45) / 4 * 4)), int(r * 0.22 / 4 * 4), 1.0, -1, cv2.LINE_AA, shift=2)
        lay = lay * (1 - m[..., None]) + (col * (0.75 + 0.25 * m[..., None]) + hl[..., None] * 0.4) * m[..., None]; al = np.maximum(al, m)
    lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 11), (W, H)); al = cv2.resize(cv2.GaussianBlur(al, (0, 0), 11), (W, H)) * 0.70   # out of focus, close to the lens
    al = kmul(al, live_keep(sa, sb, j, f, w, 1.25))
    return np.clip(o * (1 - al[..., None]) + lay * al[..., None], 0, 1)

# ---- LIGHT STREAK: a sun streak flashes across the lens at the cut --------------------------------------------------------
def light_streak(A, B, j, f, sa, sb, pre=5, post=7):
    """LIGHT STREAK: a sun streak flashes across the lens, then opens like a slot onto the next shot."""
    x = (j + pre) / (pre + post - 1); pk = math.exp(-((x - 0.30) / 0.16) ** 2); k = math.sin(math.pi * clamp(x, 0, 1))
    cy = H * 0.36; dy = np.abs(_GY - cy).astype(F32)
    half = H * 1.05 * smooth(clamp((x - 0.30) / 0.45, 0, 1)) ** 1.2
    m = np.clip((half - dy) / (14 + 0.10 * half) + 0.5, 0, 1).astype(F32)
    o = A * (1 - m[..., None]) + B * m[..., None]
    st = (np.exp(-(dy / (5 + 10 * pk)) ** 2) * pk + 0.35 * np.exp(-(dy / 90.0) ** 2) * pk
          + np.exp(-((dy - half) / (10 + 0.04 * half)) ** 2) * k * 0.8).astype(F32)            # its two lit edges as it opens
    addc(o, kmul(st, live_keep(sa, sb, j, f, smooth(x), 1.2)), GOLD17 * 0.6 + HOT * 0.4, 1.1)
    return np.clip(o, 0, 1)


# ---- LIGHT LEAK: a warm leak of sun sweeps over the film and the next shot is under it ------------------------------------
def light_leak17(A, B, j, f, sa, sb, pre=6, post=8):
    x = (j + pre) / (pre + post - 1); k = math.sin(math.pi * clamp(x, 0, 1))
    w = smooth(clamp((x - 0.40) / 0.20, 0, 1)); o = A * (1 - w) + B * w
    cx = W * (-0.3 + 1.6 * x)
    lk = (np.exp(-(((_GX - cx) / 420.0) ** 2 + ((_GY - H * 0.3) / 900.0) ** 2)) * 0.9 + np.exp(-(((_GX - cx + 200) / 200.0) ** 2 + ((_GY - H * 0.6) / 400.0) ** 2)) * 0.6).astype(F32)
    addc(o, lk, np.array([0.20, 0.45, 1.00], F32), 0.75 * k); addc(o, lk ** 2, GOLD17, 0.35 * k)
    return np.clip(o, 0, 1)

# ---- SPIN ROLL (once): the camera rolls a full turn and lands on his face, centred ----------------------------------------
def spin_roll(A, B, j, f, sa, sb, pre=6, post=10):
    if j < 0:
        u = (j + pre + 1) / pre; ang = 180 * ein(u, 2.2); c = (W / 2, H / 2)
        acc = None
        for k in range(9):
            a = ang - 18 * ein(u, 2) * k / 8; w_ = cv2.warpAffine(A, cv2.getRotationMatrix2D(c, a, 1 + 0.12 * u), (W, H), borderMode=cv2.BORDER_REFLECT)
            acc = w_ if acc is None else acc + w_
        return np.clip(acc / 9, 0, 1)
    v = (j + 1) / post; fb = face_scr(sb, f) if sb.get("face") is not None else None
    c = (fb[0], fb[1]) if fb else (W / 2, H / 2); ang = -180 * (1 - eout(v, 2.6))
    acc = None
    for k in range(9):
        a = ang * (1 + 0.06 * k / 8 * (1 - v)); w_ = cv2.warpAffine(B, cv2.getRotationMatrix2D(c, a, 1 + 0.12 * (1 - v)), (W, H), borderMode=cv2.BORDER_REFLECT)
        acc = w_ if acc is None else acc + w_
    return np.clip(acc / 9, 0, 1)

# ---- BLUE BLOOM (into the Speed Force): its blue light blooms out of the frame and he is inside it -----------------------
def blue_bloom(A, B, j, f, sa, sb, pre=10, post=12):
    """BLUE BLOOM (into the Speed Force): a starburst of its blue light breaks out from his chest and he is inside it."""
    x = (j + pre) / (pre + post - 1); k = math.sin(math.pi * clamp(x, 0, 1))
    cx, cy = W / 2, H * 1.02                                                                   # from below the frame, off every face
    dx = _GX - cx; dy = _GY - cy; d = np.sqrt(dx * dx + dy * dy).astype(F32); a = np.arctan2(dy, dx)
    jag = (1 + 0.20 * (0.6 * np.sin(7 * a + 1.3 + 2 * x) + 0.4 * np.sin(13 * a + 0.4 - 3 * x))).astype(F32)
    R = H * 1.30 * smooth(clamp((x - 0.10) / 0.82, 0, 1)) ** 1.1
    de = d / jag
    m = np.clip((R - de) / (20 + 0.12 * R) + 0.5, 0, 1).astype(F32)
    o = A * (1 - m[..., None]) + B * m[..., None]
    rim = np.exp(-((de - R) / (22 + 0.05 * R)) ** 2).astype(F32)
    addc(o, kmul(rim, live_keep(sa, sb, j, f, smooth(x), 1.2)), SKYB * 0.65 + HOT * 0.35, 0.85 * k)
    hi = np.clip(o - 0.35, 0, 1); o = o + cv2.GaussianBlur(hi, (0, 0), 26) * (SKYB * 0.6 + 0.2) * 0.8 * k
    return np.clip(o, 0, 1)


# ---- HORIZON SLIDE (the leap -> the sea): the frame slides along the horizon, the next shot comes in faster behind it ----
def horizon_slide(A, B, j, f, sa, sb, pre=5, post=7):
    q = (j + pre) / (pre + post - 1); p = smooth(clamp(q, 0, 1)); sp = math.sin(math.pi * clamp(q, 0, 1))
    a = cv2.warpAffine(A, np.float32([[1, 0, -W * 0.6 * p], [0, 1, 0]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    b = cv2.warpAffine(B, np.float32([[1, 0, W * (1 - p)], [0, 1, 0]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    seam = W * (1 - p); m = np.clip((_GX - seam) / 30 + 0.5, 0, 1).astype(F32)[..., None]
    o = hblur(a * (1 - m) + b * m, 2 + 120 * sp)
    addc(o, np.exp(-((_GX - seam) / 40.0) ** 2).astype(F32), GOLD17, 0.6 * sp)
    return np.clip(o, 0, 1)

# ---- BOKEH RACK: the lens racks off into the sun's bokeh and finds the next face -----------------------------------------
def bokeh_rack(A, B, j, f, sa, sb, pre=8, post=10):
    x = (j + pre) / (pre + post - 1); r = 30 * math.sin(math.pi * clamp(x, 0, 1)) ** 1.3
    w = smooth(clamp((x - 0.35) / 0.30, 0, 1))
    return np.clip(defocus16(A, r) * (1 - w) + defocus16(B, r) * w, 0, 1)

# ---- GLARE WASH: the sun's glare washes in from the corner and the next shot is in it ------------------------------------
def glare_wash(A, B, j, f, sa, sb, pre=6, post=8):
    """GLARE WASH: the sun's glare floods in from the corner; the next shot is in the glare as it passes."""
    x = (j + pre) / (pre + post - 1); k = math.sin(math.pi * clamp(x, 0, 1))
    d = (np.sqrt((_GX - W * 1.08) ** 2 + (_GY + H * 0.06) ** 2)).astype(F32)
    xr = 0.5 + 0.5 * math.tanh((x - 0.5) * 4.0) / math.tanh(2.0)
    R = math.hypot(W, H) * 1.15 * xr
    m = np.clip((R - d) / 170 + 0.5, 0, 1).astype(F32)
    o = A * (1 - m[..., None]) + B * m[..., None]
    g = np.exp(-((d - R) / 260.0) ** 2).astype(F32) + 0.35 * np.clip(1 - d / (R + 1), 0, 1).astype(F32) * (1 - smooth(clamp((x - 0.6) / 0.4, 0, 1)))
    addc(o, kmul(g, live_keep(sa, sb, j, f, smooth(x), 1.2)), GOLD17 * 0.7 + HOT * 0.3, 0.60 * k)
    return np.clip(o, 0, 1)


# ---- HIDE PEEK ("hide away"): the frame slides away to the side and the next shot is behind it, peeking out --------------
def hide_peek(A, B, j, f, sa, sb, pre=8, post=8):
    q = (j + pre) / (pre + post - 1); p = smooth(clamp(q, 0, 1))
    a = cv2.warpAffine(A, np.float32([[1 - 0.08 * p, 0, -W * 1.05 * p + W * 0.04 * p], [0, 1 - 0.08 * p, H * 0.04 * p]]), (W, H), borderMode=cv2.BORDER_CONSTANT)
    ma = cv2.warpAffine(np.ones((H, W), F32), np.float32([[1 - 0.08 * p, 0, -W * 1.05 * p + W * 0.04 * p], [0, 1 - 0.08 * p, H * 0.04 * p]]), (W, H), borderMode=cv2.BORDER_CONSTANT)
    b = zoom_about(B, W * 0.7, H / 2, 1.06 - 0.06 * p)
    sh = cv2.GaussianBlur(ma, (0, 0), 30) * (1 - ma) * 0.35                                   # its soft shadow on the shot behind
    o = b * (1 - sh[..., None]) * (1 - ma[..., None]) + a * ma[..., None]
    return np.clip(o, 0, 1)

# ---- SMEAR: the run smears sideways and resolves into the next shot -------------------------------------------------------
def smear17(A, B, j, f, sa, sb, pre=5, post=6):
    q = (j + pre) / (pre + post - 1); sp = math.sin(math.pi * clamp(q, 0, 1))
    w = smooth(clamp((q - 0.40) / 0.20, 0, 1)); o = hblur(A * (1 - w) + B * w, 2 + 260 * sp)
    return np.clip(rgb_split(o, 6 * sp), 0, 1)

# ---- SPLIT SLIDE: the frame splits into three slices that slide away up and down; the next shot is behind ---------------
def split_slide(A, B, j, f, sa, sb, pre=6, post=8):
    q = (j + pre) / (pre + post - 1); p = smooth(clamp(q, 0, 1)); o = B.copy()
    for k in range(3):
        x0, x1 = k * W // 3, (k + 1) * W // 3; dy = int(round((H * 1.04) * p * (1 if k % 2 == 0 else -1) * (1.0 + 0.12 * k)))
        dy = max(-H, min(H, dy)); sl = np.roll(A[:, x0:x1], dy, axis=0)
        if dy > 0: sl[:dy] = B[:dy, x0:x1]
        elif dy < 0: sl[dy:] = B[dy:, x0:x1]
        o[:, x0:x1] = sl
    return np.clip(hblur(o, 2 + 140 * math.sin(math.pi * clamp(q, 0, 1)), vertical=True), 0, 1)

# ---- CUBE TURN (the leap -> the chest device): the frame is one face of a cube; it turns and the next shot is the face beside it
def _quad(img, pts):
    src = np.float32([[0, 0], [W, 0], [W, H], [0, H]])
    M = cv2.getPerspectiveTransform(src, np.float32(pts))
    o = cv2.warpPerspective(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    m = cv2.warpPerspective(np.ones((H, W), F32), M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    return o, m

def cube_turn(A, B, j, f, sa, sb, pre=6, post=10):
    q = (j + pre) / (pre + post - 1); p = smoother(clamp(q, 0, 1)); ang = p * math.pi / 2
    D = 2.2 * W; zc = W / 2                                                                    # the camera distance; the cube's half-width
    def proj(x3, y3, z3):
        s_ = D / (D + z3); return (W / 2 + x3 * s_, H / 2 + y3 * s_)
    def face(theta):
        c, s_ = math.cos(theta), math.sin(theta)                                               # a face at angle theta about the cube's axis
        xs = [(-W / 2) * c + zc * s_, (W / 2) * c + zc * s_]; zs = [-(-W / 2) * s_ + zc * c - zc, -(W / 2) * s_ + zc * c - zc]
        return [proj(xs[0], -H / 2, zs[0]), proj(xs[1], -H / 2, zs[1]), proj(xs[1], H / 2, zs[1]), proj(xs[0], H / 2, zs[0])], c
    pa, ca = face(-ang); pb, cb = face(math.pi / 2 - ang)
    o = np.zeros((H, W, 3), F32)
    if ca > 0.02:
        a_, ma = _quad(A, pa); o = o * (1 - ma[..., None]) + a_ * (0.55 + 0.45 * ca) * ma[..., None]
    if cb > 0.02:
        b_, mb = _quad(B, pb); o = o * (1 - mb[..., None]) + b_ * (0.55 + 0.45 * cb) * mb[..., None]
    behind_ = 1 - np.clip((cv2.GaussianBlur(((o.sum(2) > 0) * 1.0).astype(F32), (0, 0), 2)), 0, 1)
    bg = cv2.GaussianBlur(A * (1 - p) + B * p, (0, 0), 30) * 0.55                               # the space round the cube: the shots' own light
    o = o + bg * behind_[..., None]
    ex = pa[1][0]                                                                              # the shared edge (A's right = B's left)
    edge = np.exp(-((_GX - ex) / 5.0) ** 2).astype(F32) * math.sin(math.pi * clamp(q, 0, 1))    # the cube's edge catches the sun
    addc(o, kmul(edge, live_keep(sa, sb, j, f, p, 1.1)), GOLD17 * 0.6 + HOT * 0.4, 0.8)
    return np.clip(o, 0, 1)

# ---- PEEL ("hide away"): the frame peels away from the corner like a sticker; its paper back curls over, the next shot is under it
def peel17(A, B, j, f, sa, sb, pre=8, post=10):
    q = (j + pre) / (pre + post - 1); p = smooth(clamp(q, 0, 1))
    n = np.array([-0.62, -0.78], np.float32); n /= np.linalg.norm(n)                         # it peels from the bottom right toward the top left
    c0 = np.array([W, H], np.float32)
    L = abs(W * n[0]) + abs(H * n[1])
    dfold = L * 1.15 * p                                                                       # how far the fold has travelled
    s_ = ((_GX - c0[0]) * n[0] + (_GY - c0[1]) * n[1]) - dfold                                  # < 0: peeled (B shows); > 0: still A
    peeled = np.clip(0.5 - s_ / 2.0, 0, 1).astype(F32)
    o = A * (1 - peeled[..., None]) + B * peeled[..., None]
    sh_b = (np.exp(-np.maximum(-s_, 0) / 70.0) * peeled * 0.45).astype(F32)                   # the flap's shadow on the next shot
    o = o * (1 - sh_b[..., None])
    kc = 1.6                                                                                   # the curl foreshortens the flap
    rx = _GX - 2 * kc * s_ * n[0]; ry = _GY - 2 * kc * s_ * n[1]                               # where each flap point comes from (mirrored, curled)
    flap = ((s_ >= 0) & (rx >= 0) & (rx < W) & (ry >= 0) & (ry < H)).astype(F32)               # the curled-over flap: the peeled corner, reflected
    flap = cv2.GaussianBlur(flap, (0, 0), 1.0)
    curl = np.clip(s_ / (dfold / kc + 1e-3), 0, 1).astype(F32)
    paper = (np.array([0.93, 0.95, 0.97], F32) * (0.70 + 0.30 * curl[..., None]) - 0.10 * (1 - curl[..., None]))
    sh_a = (cv2.GaussianBlur(flap, (0, 0), 18) * (1 - flap) * 0.40).astype(F32)               # the flap's soft shadow on A
    o = o * (1 - sh_a[..., None])
    o = o * (1 - flap[..., None]) + paper * flap[..., None]
    hl = np.exp(-(s_ / 4.0) ** 2).astype(F32) * (p > 0.01)                                    # the fold's edge catches the light
    addc(o, hl, HOT, 0.35)
    return np.clip(o, 0, 1)

# ---- SONIC BOOM (the attention-grabber, e8): he breaks the barrier running at us; a vapour cone condenses round him and a
#      shock ring bursts out, bending the picture as it passes, and his view at speed is inside it ----------------------------
def sonic_boom(A, B, j, f, sa, sb, pre=14, post=18):
    t = f / FPS; cx, cy = W * 0.50, H * 0.70                                                    # on his chest, below his face
    d = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2).astype(F32); ang = np.arctan2(_GY - cy, _GX - cx)
    if j < 0:                                                                                  # the vapour cone condenses
        u = (j + pre + 1) / pre
        Rv = 120 + 260 * smooth(u)
        n = cv2.resize(cloud_N(t, 0.0, 400.0), (W, H))
        cone = np.clip((Rv * (0.85 + 0.30 * n) - d) / 60.0, 0, 1) * np.clip((d - Rv * 0.35) / 80.0, 0, 1)
        cone = (cone * (0.35 + 0.65 * n) * 0.75 * smooth(u)).astype(F32)
        fk_ = live_keep(sa, sb, j, f, 0, 1.25); cone = cone if isinstance(fk_, float) else cone * fk_[..., 0]
        Az = zoom_about(A, cx, cy, 1.0 + 0.10 * ein(u, 2.0))
        shake = 3.0 * u * math.sin(f * 2.7); Az = shift_img(Az, shake, -shake * 0.6)
        o = Az * (1 - cone[..., None] * 0.6) + cone[..., None] * HOT
        st = np.clip(np.sin(ang * 46 + 1.3) * 0.5 + 0.5, 0, 1) ** 12 * np.clip((d - 200) / 400, 0, 1) * 0.5 * u   # pressure streaks
        addc(o, kmul(st.astype(F32), live_keep(sa, sb, j, f, 0, 1.2)), HOT, 0.5)
        return np.clip(o, 0, 1)
    v = (j + 1) / post                                                                         # BOOM: the shock ring
    R = 40 + math.hypot(W, H) * 0.62 * eout(v, 2.2)
    wid = 26 + 90 * v
    band = np.exp(-((d - R) / wid) ** 2).astype(F32)
    disp = (band * 34 * (1 - v)).astype(F32)                                                   # the ring bends the picture (refraction)
    mx = (_GX + np.cos(ang) * disp).astype(F32); my = (_GY + np.sin(ang) * disp).astype(F32)
    inside = np.clip((R - d) / (8 + 20 * v) + 0.5, 0, 1).astype(F32)
    Bz = zoom_about(B, cx, cy, 1.0 + 0.22 * (1 - eout(v, 2.0)))
    Ao = zoom_about(A, cx, cy, 1.10 + 0.08 * v)
    base = Ao * (1 - inside[..., None]) + Bz * inside[..., None]
    o = cv2.remap(base, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    shake = 9.0 * math.exp(-v * 5) * math.sin(f * 3.1); o = shift_img(o, shake, shake * 0.7)
    vap = cv2.resize(cloud_N(t, 0.0, 900.0), (W, H))
    addc(o, kmul((band * (0.45 + 0.55 * vap) * (1 - v) ** 0.8).astype(F32), live_keep(sa, sb, j, f, 1.0, 1.2)), HOT, 0.85)   # the vapour on the ring
    o = o * (1 + 0.18 * math.exp(-v * 8))
    return np.clip(o, 0, 1)

# ---- ZIP (e68, "Mr. Blue Sky"): he zips out of the grey shot as a streak of lightning, and the next shot arrives behind it ---
_ZP = {}
def zip_plate(A, pm, key):
    if key not in _ZP:
        if len(_ZP) > 6: _ZP.clear()
        q = 4; sm = (np.clip(cv2.resize(A, (W // q, H // q), interpolation=cv2.INTER_AREA), 0, 1) * 255).astype(np.uint8)
        mq = (cv2.dilate((cv2.resize(pm, (W // q, H // q)) > 0.3).astype(np.uint8), np.ones((7, 7), np.uint8)) * 255)
        fill = cv2.inpaint(sm, mq, 6, cv2.INPAINT_TELEA).astype(F32) / 255
        _ZP[key] = cv2.resize(fill, (W, H), interpolation=cv2.INTER_LINEAR)
    return _ZP[key]

def zip17(A, B, j, f, sa, sb, pre=6, post=8):
    """ZIP: he's gone in a flash: the camera whips after him and a bolt of his lightning rides the seam between the shots."""
    q = (j + pre) / (pre + post - 1); p = smooth(clamp(q, 0, 1)); sp = math.sin(math.pi * clamp(q, 0, 1))
    o = strip_pan(A, B, q, 1, rev=False, blur=200, ov=360)
    seam = W * (1 - p)
    cv = bolt_canvas()
    for k in range(2):
        put_bolt(cv, (seam + 20 * k, -40), (seam - 30 + 40 * k, H + 40), 18500 + k + 3 * (f // 2), 4 - k, 0.12, 7, 2, val=int(255 * sp))
    lt = light_rgb(cv, 1.1, HOT, GOLD17)
    return np.clip(o + kmul(lt, live_keep(sa, sb, j, f, p, 1.1)), 0, 1)

# ---- CLOUD SHADOW ("where once was pity"): a cloud's shadow sweeps over the frame from the right; the next shot is under it
def cloud_shadow(A, B, j, f, sa, sb, pre=8, post=10):
    x = (j + pre) / (pre + post - 1); k = math.sin(math.pi * clamp(x, 0, 1))
    N = cv2.resize(cloud_N(f / FPS, -160.0), (W, H)); wob = (N - 0.5) * 260                    # the shadow's edge is a cloud's edge
    proj = (W - _GX) + 0.18 * _GY + wob; L1 = W + 0.18 * H
    pos = -350 + (L1 + 700) * smooth(clamp(x, 0, 1))
    m = np.clip((pos - proj) / 70 + 0.5, 0, 1).astype(F32)
    o = A * (1 - m[..., None]) + B * m[..., None]
    sh = (np.exp(-((proj - pos) / 210.0) ** 2) * 0.55 * k ** 0.6).astype(F32)               # the shadow itself: soft, the picture stays
    return np.clip(o * (1 - sh[..., None]) + (sh * 0.10)[..., None] * SKYB, 0, 1)

# ---- SUN OPEN ("Mr. Blue Sky"): he looks up into the sun; it opens from the top of the frame onto the next shot -----------
def sun_open(A, B, j, f, sa, sb, pre=8, post=10):
    x = (j + pre) / (pre + post - 1); k = math.sin(math.pi * clamp(x, 0, 1))
    x = 0.5 + 0.5 * math.tanh((x - 0.5) * 4.0) / math.tanh(2.0)                                  # it crosses the frame fast in the middle
    cx, cy = W * 0.5, -H * 0.04
    d = np.sqrt((_GX - cx) ** 2 + ((_GY - cy) * 0.85) ** 2).astype(F32)
    R = H * 1.25 * smooth(clamp((x - 0.08) / 0.84, 0, 1)) ** 1.2
    m = np.clip((R - d) / (24 + 0.10 * R) + 0.5, 0, 1).astype(F32)
    base = A * (1 - m[..., None]) + B * m[..., None]
    o = god_rays(base, PERSON.get(f), cx, cy, 0.9 * k, 0.50)
    rim = np.exp(-((d - R) / (20 + 0.05 * R)) ** 2).astype(F32)
    addc(o, kmul(rim, live_keep(sa, sb, j, f, smooth(x), 1.2)), GOLD17 * 0.55 + HOT * 0.45, 0.70 * k)
    return np.clip(o, 0, 1)

def punch_cut(A, B, j, f, sa, sb):
    return B



# ---- THE SUN (the focal piece, e32 -> e40): the sun rises behind him through his matte; its rays turn on every beat -------
def sun_path(e):
    u = clamp((e - E.E_SUN) / getattr(E, "SUN_LEN", 8), 0, 1); p = smoother(u)
    (x0, y0), (x1, y1) = getattr(E, "SUN_P", ((0.70, 0.60), (0.54, 0.12)))
    return W * (x0 + (x1 - x0) * p), H * (y0 + (y1 - y0) * p), 50 + 34 * p, u                 # it rises behind him, from his shoulder to behind his head

def sun_rot(e):
    """the rays turn a step on every beat (eased), and drift between."""
    eb = beat_e(e); n = (eb - E.E_SUN) / 2
    return 0.10 * (e - E.E_SUN) + 0.22 * (n + smooth(clamp((e - eb) * E.HB / 0.12, 0, 1)))

def sun_fx(img, person, s, f):
    e = e_of(f); sx, sy, r, u = sun_path(e)
    g = smooth(clamp((e - E.E_SUN) / 1.6, 0, 1))
    if g <= 0: return img
    pulse = math.exp(-((e - beat_e(e)) * E.HB) / 0.12)
    lay = sun_draw(sx, sy, r, g * (1.20 + 0.25 * pulse), sun_rot(e))
    pm = None if person is None else np.clip(person * 1.2, 0, 1)
    d_ = np.sqrt((_GX - sx) ** 2 + (_GY - sy) ** 2)
    expo = (1 - 0.42 * g * (1 - np.exp(-(d_ / (r * 6.0)) ** 2))).astype(F32)                # exposed for the sun: the sky deepens away from it
    tint = (np.exp(-(d_ / (r * 9.0)) ** 2) * 0.10 * g).astype(F32)
    bg = img * expo[..., None] + tint[..., None] * GOLD17
    o = bg if pm is None else img * pm[..., None] * (1 - 0.18 * g) + bg * (1 - pm[..., None])
    if pm is not None:
        o = o + lay * (1 - pm[..., None])                                                     # the sun is behind him
        rim = np.clip(pm - cv2.GaussianBlur(pm, (0, 0), 9), 0, 1) * 2.0                       # his edge catches it
        near = cv2.GaussianBlur(lumf(lay), (0, 0), 30)
        o = o + kmul((rim * np.clip(near * 3, 0, 1))[..., None] * GOLD17 * 0.9 * g, face_keep(s, f, 1.15))
    else: o = o + lay
    gh = ghosts_draw(sx, sy, g * (0.55 + 0.45 * smooth(clamp((e - E.E_SUN - 4) / 3, 0, 1))))
    return np.clip(o + kmul(gh, face_keep(s, f, 1.25)), 0, 1)

def ghost_iris(A, B, j, f, sa, sb, pre=30, post=26):
    """GHOST IRIS: one of the sun's lens ghosts swells into an iris; the next shot is inside it, and we go through."""
    x = (j + pre) / (pre + post - 1)
    sx, sy, r, _ = sun_path(e_of(sa["f1"] - 1)); gx, gy, gr, gcol, ga = ghost_pts(sx, sy)[1]
    G = smoother(clamp(x / 0.95, 0, 1)); D = math.hypot(W, H)
    R = gr * math.exp(math.log(D * 0.62 / gr) * G)
    cx, cy = gx + (W / 2 - gx) * G, gy + (H * 0.64 - gy) * G                                  # it opens on his chest, not his face
    d = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2)
    fe_ = (2 + 0.06 * R) * (1 - smooth(clamp((x - 0.80) / 0.20, 0, 1))) + 1e-3
    m = np.clip((R - d) / fe_, 0, 1).astype(F32)
    bs = clamp(2 * R / W, 0.06, 1.0)
    Bz = cv2.warpAffine(B, np.float32([[bs, 0, cx - bs * W / 2], [0, bs, cy - bs * H / 2]]), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT) if bs < 0.999 else B
    tint = 1 - smooth(clamp(x / 0.7, 0, 1))
    Bz = Bz * (1 - 0.25 * tint) + SKYB * 0.14 * tint                                          # seen through the ghost's tint
    o = A * (1 - m[..., None]) + Bz * m[..., None]
    rk = 1 - smooth(clamp((x - 0.7) / 0.3, 0, 1)); wr = 6 + 0.03 * R
    fk = live_keep(sa, sb, j, f, 0 if x < 0.5 else 1, 1.3)                                     # the rim never runs over a face
    addc(o, kmul((np.exp(-((d - R - wr) / wr) ** 2) * rk).astype(F32), fk), ROSE, 0.45)          # its chromatic rim
    addc(o, kmul((np.exp(-((d - R + wr) / wr) ** 2) * rk).astype(F32), fk), SKYB, 0.38)
    return np.clip(o, 0, 1)

# ---- CLOUD BREAK ("where once was pity" -> "Mr. Blue Sky"): the clouds roll in over him, then part with the sun behind ---
def _faceq(s_, f_, pad=1.3):
    fm = face_soft(s_, f_, pad)
    return None if fm is None else cv2.resize(fm[..., 0], (W // 4, H // 4), interpolation=cv2.INTER_AREA)

_STM = {}
def storm_tex(k):
    """the storm itself as the cloud: frame k of the opening storm, mirrored and pushed in (its building out of frame)."""
    k = int(clamp(round(k), 0, SHOTS[0]["f1"] - 1))
    if k not in _STM:
        if len(_STM) > 6: _STM.clear()
        img = base11(SHOTS[0], k)[0][:, ::-1]
        z = 1.35; cx, cy = W * 0.5, H * 0.25
        _STM[k] = cv2.warpAffine(np.ascontiguousarray(img), np.float32([[z, 0, cx - z * cx], [0, z, cy - z * cy]]), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return _STM[k]

def _cloud_mask(t, covmap, soft, vx=-110.0):
    N_ = cloud_N(t, vx)
    dq = np.clip((N_ - (0.80 - covmap)) / soft, 0, 1).astype(F32)
    return dq, cv2.resize(cv2.GaussianBlur(dq, (0, 0), 1.2), (W, H))[..., None], cv2.resize((dq * (1 - dq) * 4).astype(F32), (W, H))

def cloud_break(A, B, j, f, sa, sb, pre=28, post=24):
    """CLOUD BREAK ("where once was pity" -> "Mr. Blue Sky"): the storm of the opening rolls back in over him; on the word
    it parts from the sun outward, his face clearing first, and the sun's rays come through the gap."""
    t = f / FPS; stm = storm_tex(j + pre)
    if j < 0:
        u = (j + pre + 1) / pre
        covmap = (1.25 * smooth(u) ** 2.0 - 0.50 + 0.70 * (_GXQ / W)).astype(F32)              # it rolls in from the right
        fq = _faceq(sa, f); soft = 0.20 if fq is None else (0.20 + 0.25 * fq).astype(F32)      # its edge passes his face softly
        dq, dm, rim = _cloud_mask(t, covmap, soft)
        o = A * (1 - 0.25 * u) * (1 - dm) + stm * dm
        addc(o, rim * (1 - u), HOT, 0.22)                                                      # the last light on its edge
        return np.clip(o, 0, 1)
    v = (j + 1) / post
    dist = np.sqrt(((_GXQ - W * 0.5) / W) ** 2 + ((_GYQ - H * 0.15) / H) ** 2 * 0.8) / 0.75
    covmap = 1.30 - 2.00 * smooth(v) ** 0.9 + 0.55 * dist                                     # it parts from the sun outward
    fq = _faceq(sb, f)
    soft = 0.20 if fq is None else (0.20 + 0.25 * fq).astype(F32)                              # its edge passes his face softly
    dq, dm, rim = _cloud_mask(t, covmap.astype(F32), soft)
    Bl = god_rays(B, PERSON.get(f), W * 0.5, H * 0.04, 0.70 * (1 - v) ** 0.7, 0.55)             # the sun behind him, through the gap
    o = Bl * (1 - dm) + stm * dm
    addc(o, rim * (1 - v) ** 0.8, HOT * 0.6 + GOLD17 * 0.4, 0.60)                               # the silver lining
    return np.clip(o, 0, 1)

# ---- EMBLEM SUN (the chorus, e104 -> e112): the real chest emblem glints, lights from within, throws rays and becomes the sun;
#      the camera rises after it into the sky of the next shot -------------------------------------------------------------
def emb_pt(s, f):
    t, _, _ = src_time(s, f); T = E.EMB_TRACK; ts = [a_[0] for a_ in T]
    x, y, r = (float(np.interp(t, ts, [a_[i] for a_ in T])) for i in (1, 2, 3))
    X, Y, sc = to_screen(s, f, x, y); return X, Y, r * sc

def star_glint(cx, cy, size, amt, rot=0.3):
    c, s_ = math.cos(rot), math.sin(rot)
    u = (_GX - cx) * c + (_GY - cy) * s_; v = -(_GX - cx) * s_ + (_GY - cy) * c
    st = np.exp(-(u / size) ** 2 - (v / (size * 0.025)) ** 2) + np.exp(-(v / size) ** 2 - (u / (size * 0.025)) ** 2) + 1.5 * np.exp(-(u * u + v * v) / (size * 0.08) ** 2)
    return (st * amt).astype(F32)

_EMH = {}
def emb_hole(img, ex, ey, er, key):
    """his chest without the emblem: the hole filled from the suit round it (inpainted at quarter resolution), a soft
    shadow in the socket it leaves."""
    if key not in _EMH:
        if len(_EMH) > 4: _EMH.clear()
        q = 4; sm = (np.clip(cv2.resize(img, (W // q, H // q), interpolation=cv2.INTER_AREA), 0, 1) * 255).astype(np.uint8)
        m = np.zeros((H // q, W // q), np.uint8); cv2.circle(m, (int(round(ex / q)), int(round(ey / q))), int(er * 1.18 / q) + 2, 255, -1)
        fill = cv2.inpaint(sm, m, 7, cv2.INPAINT_TELEA).astype(F32) / 255
        _EMH[key] = cv2.GaussianBlur(cv2.resize(fill, (W, H), interpolation=cv2.INTER_LINEAR), (0, 0), 3)
    d = np.sqrt((_GX - ex) ** 2 + (_GY - ey) ** 2)
    hm = np.clip((er * 1.12 - d) / 5 + 0.5, 0, 1).astype(F32)[..., None]
    sock = (np.exp(-(d / (er * 0.9)) ** 2) * 0.35).astype(F32)[..., None]
    return img * (1 - hm) + _EMH[key] * (1 - sock) * hm

def emb_patch(img, ex, ey, er):
    """the real emblem as a sprite: its disc cut from the frame, with a soft alpha."""
    R = int(er * 1.10) + 3; x0, y0 = int(round(ex)) - R, int(round(ey)) - R
    pad = cv2.copyMakeBorder(img, R, R, R, R, cv2.BORDER_REFLECT)
    patch = pad[y0 + R:y0 + 3 * R, x0 + R:x0 + 3 * R].copy()
    yy, xx = np.mgrid[0:2 * R, 0:2 * R].astype(F32); d = np.sqrt((xx - R) ** 2 + (yy - R) ** 2)
    alpha = np.clip((er * 1.04 - d) / 1.6 + 0.5, 0, 1).astype(F32)
    return patch, alpha, R

def coin_back(R, er):
    """the back of the coin: plain gold, lit from above (never the front mirrored)."""
    yy, xx = np.mgrid[0:2 * R, 0:2 * R].astype(F32); d = np.sqrt((xx - R) ** 2 + (yy - R) ** 2) / er
    sh = np.clip(0.55 + 0.45 * (-(yy - R) / er) * 0.6 + 0.25 * (1 - d), 0.2, 1.1)
    rim = np.exp(-((d - 0.93) / 0.05) ** 2)
    return (sh[..., None] * GOLD17 * 0.85 + rim[..., None] * HOT * 0.5).astype(F32)

def put_sprite(o, patch, alpha, R, px, py, sx, sy):
    M = np.float32([[sx, 0, px - sx * R], [0, sy, py - sy * R]])
    P = cv2.warpAffine(patch, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    Am = cv2.warpAffine(alpha, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)[..., None]
    return o * (1 - Am) + P * Am, Am[..., 0]

def bez(p0, p1, p2, t):
    return ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])

def emblem_ignite(A, B, j, f, sa, sb, pre=62, post=40):
    """EMBLEM IGNITE (the chorus; EMBLEM SUN v2, after the owner's round-1 note on v1): the real chest emblem charges
    (lightning crawls round its rim), tears free of his chest on a tether of current and flips like a coin as it rises up
    the open side of the frame, clear of his face; face-on again, its bolt flares and the emblem ignites into the sun,
    throwing lightning down the side; the camera rises after it into the next shot, where it hangs in the sky."""
    t = f / FPS
    ff = f if j < 0 else sa["f1"] - 1
    ex, ey, er = emb_pt(sa, ff)
    u = clamp((j + pre + 1) / pre, 0, 1); v = clamp((j + 1) / post, 0, 1) if j >= 0 else 0.0
    z = 1 + 0.12 * smooth(clamp(u / 0.35, 0, 1))                                               # 1. push in on it
    px_ = ex + (W * 0.50 - ex) * 0.20 * smooth(clamp(u / 0.35, 0, 1)); py_ = ey + (H * 0.58 - ey) * 0.20 * smooth(clamp(u / 0.35, 0, 1))
    Mz = np.float32([[z, 0, px_ - z * ex], [0, z, py_ - z * ey]])
    Az = cv2.warpAffine(A, Mz, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    EX, EY, ER = px_, py_, er * z
    fm = face_soft(sa, ff, 0.62)                                                              # every light keeps off his face (the face itself)
    fk = 1.0 if fm is None else (1 - 0.95 * cv2.GaussianBlur(cv2.warpAffine(fm[..., 0], Mz, (W, H), borderMode=cv2.BORDER_REPLICATE), (0, 0), 10))
    fsc = face_scr(sa, ff) if sa.get("face") is not None else None
    fx_ = fsc[0] * z + px_ - z * ex if fsc else W * 0.5
    side = -1 if fx_ >= W * 0.45 else 1                                                        # the open side of the frame, away from his face
    TX = W * (0.20 if side < 0 else 0.80); TY = H * 0.21
    C1 = (TX + side * W * 0.02, EY - H * 0.05)                                                 # out to the side first, then up
    lift = smooth(clamp((u - 0.20) / 0.42, 0, 1))                                              # 2. it tears free and rises
    SX, SY = bez((EX, EY), C1, (TX, TY), lift)
    ign = smooth(clamp((u - 0.60) / 0.26, 0, 1))                                               # 3. face-on again, it ignites
    T = smooth(clamp((j + 9) / 21.0, 0, 1))                                                    # 4. the camera rises after it (j -9 .. 12)
    patch, alpha, R = emb_patch(Az, EX, EY, ER)
    base = emb_hole(Az, EX, EY, ER, (sa["n"], int(round(ff)))) if lift > 0.002 else Az.copy()
    o = base
    chg = smooth(clamp(u / 0.15, 0, 1)) * (1 - ign)
    cv = bolt_canvas()
    if chg > 0.01:
        for k in range(3):
            a0 = 0.6 + 2.1 * k + 4.0 * t; a1 = a0 + 1.1
            p0 = (SX + ER * 1.02 * math.cos(a0), SY + ER * 1.02 * math.sin(a0)); p1 = (SX + ER * 1.02 * math.cos(a1), SY + ER * 1.02 * math.sin(a1))
            put_bolt(cv, p0, p1, 17200 + k + 7 * (f // 2), 2, 0.30, 4, 0, val=int(255 * chg))
    tet = math.sin(math.pi * clamp((lift - 0.02) / 0.55, 0, 1))
    if tet > 0.02 and math.hypot(SX - EX, SY - EY) > ER * 0.8:
        for k in range(2): put_bolt(cv, (EX, EY), (SX, SY), 17300 + k + 5 * (f // 2), 2, 0.22, 5, 1, val=int(235 * tet))
    phi = 2 * math.pi * smooth(clamp((u - 0.22) / 0.36, 0, 1)); cphi = math.cos(phi)
    sc = 1.0 + 0.08 * lift
    if lift > 0.002:
        spr = patch if cphi >= 0 else coin_back(R, er * z)
        o, am = put_sprite(o, spr, alpha, R, SX, SY, sc * max(abs(cphi), 0.04), sc)
        rimc = np.exp(-((np.sqrt(((_GX - SX) / max(abs(cphi), 0.04)) ** 2 + (_GY - SY) ** 2) - ER * sc) / 3.0) ** 2).astype(F32)
        addc(o, rimc * (0.5 + 0.5 * lift) * (1 - ign), GOLD17, 0.6)
    if ign > 0.002:
        rs = ER * sc * 0.80
        sun = sun_draw(SX, SY, rs, 1.10 * ign, rot=0.6 * t + 1.2 * ign, rays=0.45, wide=0.45)
        dsk = np.clip((ER * sc * 1.05 - np.sqrt((_GX - SX) ** 2 + (_GY - SY) ** 2)) / 4 + 0.5, 0, 1).astype(F32)[..., None]
        keep = dsk if isinstance(fk, float) else (fk[..., None] + (1 - fk[..., None]) * dsk)
        if T <= 0: o = o + sun * keep
        angs = (1.65, 2.15, 2.75, 4.45) if side < 0 else (1.50, 1.00, 0.40, -1.30)               # down the open side, off his face
        for k, ang in enumerate(angs):
            L = math.hypot(W, H) * (0.30 + 0.25 * ign)
            q1 = (SX + L * math.cos(ang), SY + L * math.sin(ang))
            put_bolt(cv, (SX + rs * 1.1 * math.cos(ang), SY + rs * 1.1 * math.sin(ang)), q1, 17400 + 11 * k + 3 * (f // 2), 3, 0.30, 6, 2,
                     val=int(255 * ign * (0.6 + 0.4 * math.sin(f * 1.7 + k) ** 2) * (1 - T)))
    if cv.max() > 0:
        lt = light_rgb(cv, 1.0, HOT, GOLD17)
        o = o + kmul(lt, fk if isinstance(fk, float) else fk[..., None])
    o = np.clip(o, 0, 1)
    if T > 0:                                                                                  # 4. a feathered tilt up into B's sky
        o = strip_pan(o, B, T, 0, rev=True, blur=120, ov=420)
        sx2, sy2 = SX + (W * 0.76 - SX) * T ** 2.2, SY + (H * 0.15 - SY) * T                   # the sun rises with the camera, then crosses ...
        hang = 1 - smooth(clamp((v - 0.70) / 0.30, 0, 1))                                      # ... and hangs in the next shot's sky
        rs2 = ER * sc * 0.80
        d2 = np.sqrt((_GX - sx2) ** 2 + (_GY - sy2) ** 2)
        o = o * (1 - 0.40 * T * hang * (1 - np.exp(-(d2 / (rs2 * 2.5)) ** 2)))[..., None]       # exposed for the sun: the sky deepens round it
        sun2 = sun_draw(sx2, sy2, rs2, 1.15 * hang * max(ign, T), rot=0.6 * t + 1.2, rays=0.6, wide=0.6)
        if not isinstance(fk, float):                                                          # his face slides down with the old shot: keep the sun off it
            dy = int(round(smooth(T) * H)); fks = np.ones_like(fk)
            if dy < H: fks[dy:] = fk[:H - dy]
            dsk2 = np.clip((rs2 * 1.05 - d2) / 4 + 0.5, 0, 1).astype(F32)
            sun2 = sun2 * (fks + (1 - fks) * dsk2)[..., None]
        o = o + sun2
    return np.clip(o, 0, 1)

# ---- LIGHTNING STRIKE ("so long"): leaders creep down, then a real bolt strikes; the next shot burns in from its channel ---
_LS = {}
def strike_canvas(key, amt_main, amt_br, y_end=None):
    cv = bolt_canvas(); x0 = W * 0.17
    rng_seed = 17600
    pts = bolt_points((x0 - 50.0, -60.0), (x0 + 40.0, H * 0.70), rng_seed, 0.16, 7)
    if y_end is not None: pts = pts[pts[:, 1] <= y_end]
    if len(pts) > 1:
        cv2.polylines(cv, [pts.astype(np.int32)], False, int(255 * amt_main), 9, cv2.LINE_AA)
        rng = np.random.default_rng(key)
        for b in range(4):
            i = int(rng.integers(len(pts) // 6, max(len(pts) // 6 + 1, len(pts) - 6))); q0 = pts[i]
            ang = math.pi / 2 + rng.uniform(-0.9, 0.9) + (0.5 if b % 2 else -0.5)
            Lb = rng.uniform(120, 340); q1 = (q0[0] + Lb * math.cos(ang), q0[1] + Lb * math.sin(ang))
            cv2.polylines(cv, [bolt_points(tuple(q0), q1, rng_seed + 50 + b, 0.30, 5).astype(np.int32)], False, int(200 * amt_br), 3, cv2.LINE_AA)
    return cv, pts

def lightning_strike(A, B, j, f, sa, sb, pre=8, post=14):
    """LIGHTNING STRIKE: the storm comes back for the loop. The light dims, faint leaders creep down the sky, a real bolt
    strikes beside him (the frame flashes once, within the flash limit), re-strikes, and the next shot burns in outward
    from the bolt's channel."""
    x = (j + pre) / (pre + post - 1); xs = pre / (pre + post - 1)                              # it strikes on the cut
    if "d" not in _LS:                                                                         # from the main channel only (order-free)
        q = 4; cq = cv2.resize(strike_canvas(0, 1.0, 0.0)[0], (W // q, H // q), interpolation=cv2.INTER_AREA)
        dist = cv2.distanceTransform((cq < 40).astype(np.uint8), cv2.DIST_L2, 5) * q
        _LS["d"] = cv2.resize(dist.astype(F32), (W, H), interpolation=cv2.INTER_LINEAR)
    dim = 1 - 0.38 * smooth(clamp(x / xs, 0, 1))
    if x < xs:                                                                                 # the leaders
        cv, _ = strike_canvas(17610 + f // 2, 0.45, 0.5, y_end=H * (0.08 + 0.62 * x / xs))
        lt = light_rgb(cv, 0.8, HOT, SKYB * 0.6 + HOT * 0.4)
        return np.clip(A * dim + kmul(lt, live_keep(sa, sb, j, f, 0, 0.95)), 0, 1)
    y = x - xs
    b = math.exp(-y / 0.10) + 0.65 * math.exp(-((y - 0.20) / 0.035) ** 2)                      # the strike, and its re-strike
    cv, pts = strike_canvas(17620 + (f // 2) % 2, 1.0, 0.9)
    R = 60 + W * 2.0 * eout(clamp(y / 0.30, 0, 1), 1.6)
    m = np.clip((R - _LS["d"]) / (40 + 0.25 * R) + 0.5, 0, 1).astype(F32)
    Bd = B * (0.62 + 0.38 * smooth(clamp(y / 0.60, 0, 1)))                                     # the next shot comes up from the storm light
    o = A * dim * (1 - m[..., None]) + Bd * m[..., None]
    o = o * (1 + 0.30 * b) + (SKYB * 0.5 + HOT * 0.5) * 0.05 * b
    lt = light_rgb(cv, 1.8 * b + 0.35 * (1 - smooth(clamp(y / 0.7, 0, 1))), HOT, SKYB * 0.6 + HOT * 0.4)
    return np.clip(o + kmul(lt, live_keep(sa, sb, j, f, 1.0, 0.95)), 0, 1)

# ---- BOLT WINDOW: a Flash bolt flies at the lens with the next shot inside it, its edges alive with current ------------------
BOLTP = np.array([(0.05, -0.50), (0.30, -0.50), (0.10, -0.08), (0.28, -0.08), (-0.22, 0.50), (-0.04, 0.02), (-0.22, 0.02)], np.float32)
def bolt_window(A, B, j, f, sa, sb, pre=8, post=12):
    x = (j + pre) / (pre + post - 1); k = math.sin(math.pi * clamp(x, 0, 1))
    ax, ay = W * 0.50, H * 0.80                                                                # it flies in low at his chest, off his face
    anc = np.array([0.08, -0.05], np.float32)                                                  # the bolt's fattest point
    S = 260 * math.exp(math.log(30000 / 260) * ein(clamp(x / 0.88, 0, 1), 1.5))
    rot = -0.35 * (1 - smooth(x)); c, s_ = math.cos(rot), math.sin(rot)
    sqx = 0.55 + 0.45 * smooth(clamp(x / 0.35, 0, 1))                                          # it turns face-on as it comes
    P = (BOLTP - anc) * S; P[:, 0] *= sqx
    P = np.stack([ax + P[:, 0] * c - P[:, 1] * s_, ay + P[:, 0] * s_ + P[:, 1] * c], 1)
    m = np.zeros((H, W), F32); cv2.fillPoly(m, [(np.clip(P, -60000, 60000) * 16).astype(np.int32)], 1.0, cv2.LINE_AA, shift=4)
    m = cv2.GaussianBlur(m, (0, 0), 1.2)
    m = np.maximum(m, smooth(clamp((x - 0.86) / 0.12, 0, 1)))                                   # nothing of the old shot is left at its end
    Bz = zoom_about(B, ax, ay, 1.0 + 0.30 * (1 - smooth(x)))
    Az = zoom_about(A, ax, ay, 1.0 + 0.12 * smooth(x))
    o = Az * (1 - m[..., None]) + Bz * m[..., None]
    cv = bolt_canvas()
    cv2.polylines(cv, [(P * 16).astype(np.int32)], True, 255, 3, cv2.LINE_AA, shift=4)
    if S < 2600:
        for e_ in range(0, 7, 2):                                                              # current crawling along its edges
            put_bolt(cv, tuple(P[e_]), tuple(P[(e_ + 1) % 7]), 17700 + e_ + 5 * (f // 2), 1, 0.20, 4, 0, val=200)
    lt = light_rgb(cv, 0.9 * (1 - smooth(clamp((x - 0.75) / 0.25, 0, 1))), HOT, GOLD17)
    return np.clip(o + kmul(lt, live_keep(sa, sb, j, f, smooth(x), 1.25)), 0, 1)

# ---- CLOUD OVER (the loop, e136 -> frame 0): the clouds roll back over the sun and they are frame 0's storm ----------------
def loop_fx(img, person, s, f):
    """LIGHTNING ASCENT (the loop): the storm has come back; the suit charges (gold arcs build over him), and he answers it:
    a bolt launches from his chest straight up into the sky. The camera rises with it, past the clouds' edge, into the storm
    of frame 0, its light fading, and comes to rest exactly on frame 0."""
    f0 = fh(E.E_LOOP); N = E.DUR_F - f0
    if f < f0: return img
    t = (f - f0) / N; tt = f / FPS
    o = img
    chg = smooth(clamp((t - 0.06) / 0.30, 0, 1))                                               # 1. the charge
    cv = bolt_canvas()
    fs = face_scr(s, f) if s.get("face") is not None else s.get("face_hint")
    body = None
    if person is not None:
        body = person.copy()
        if fs: body[: int(min(H, fs[1] + fs[2] * 2.3))] = 0                                    # his chest and shoulders, well below the chin
    fk = face_keep(s, f, 1.5)
    if body is not None and chg > 0.01:
        q = 8; bq = cv2.resize(body, (W // q, H // q), interpolation=cv2.INTER_AREA)
        ys, xs = np.nonzero(bq > 0.6)
        if len(xs) > 20:
            rng = np.random.default_rng(1700 + f // 2)
            for k in range(2 + int(4 * chg)):
                i_ = int(rng.integers(len(xs))); p0 = (xs[i_] * q + 4.0, ys[i_] * q + 4.0)
                a_ = rng.uniform(-0.35, math.pi + 0.35); L = rng.uniform(140, 300)                 # sideways and down: never up toward his face
                put_bolt(cv, p0, (p0[0] + L * math.cos(a_), p0[1] + L * math.sin(a_)), 18300 + k + 7 * (f // 2), 3, 0.32, 6, 1, val=int(255 * chg))
    hx, hy = (fs[0], fs[1] + fs[2] * 2.6) if fs else (W * 0.45, H * 0.62)                      # his chest
    launch = smooth(clamp((t - 0.34) / 0.12, 0, 1))                                            # 2. the bolt launches upward
    if launch > 0.002:
        top = hy - (hy + 200) * launch
        sx_ = W * 0.84 if hx < W * 0.55 else W * 0.16                                          # from beside his shoulder, up past his head (never his face)
        for k in range(2):
            put_bolt(cv, (sx_, hy - 40), (sx_ + 30 * (1 - 2 * k), top), 18400 + k + 3 * (f // 2), 5 - 2 * k, 0.06, 7, 2, val=int(255 * (1 - 0.3 * k)))
    lt = light_rgb(cv, 1.0 + 0.6 * launch, HOT, GOLD17)
    o = o + kmul(lt, fk)
    o = o * (1 - 0.15 * chg * (1 - launch))                                                    # the light dims before he answers
    T = smooth(clamp((t - 0.40) / 0.60, 0, 1))                                                 # 3. the camera rises with it into frame 0
    if T > 0:
        storm = frame_virtual(f - E.DUR_F)
        o = strip_pan(np.clip(o, 0, 1), storm, T, 0, rev=True, blur=150, ov=520)
        glow = (1 - smooth(clamp((t - 0.55) / 0.35, 0, 1)))                                    # its light in the clouds, fading before frame 0
        if glow > 0.002:
            gx = W * 0.5; gy = H * (0.15 + 0.25 * (1 - T))
            d = np.sqrt((_GX - gx) ** 2 + (_GY - gy) ** 2)
            addc(o, (np.exp(-(d / 520.0) ** 2) * glow * T).astype(F32), HOT * 0.6 + GOLD17 * 0.4, 0.45)
        if t > 0.985: o = storm                                                                # exactly frame 0's own picture at the wrap
    return np.clip(o, 0, 1)

def loop17(A, B, j, f, sa, sb):
    return B

TR2.update({"sun_burst": (sun_burst, 12, 16), "run_by": (run_by, 5, 7), "speed_zoom": (speed_zoom, 4, 7), "glint_sweep": (glint_sweep, 6, 6),
            "sky_whip": (sky_whip, 5, 6), "flare_cut": (flare_cut, 6, 8), "ray_rake": (ray_rake, 8, 8), "bloom_cut": (bloom_cut, 8, 10),
            "ghost_iris": (ghost_iris, 30, 26), "prism": (prism, 6, 8), "whip_pan": (whip_pan, 5, 6), "bolt_crack": (bolt_crack, 4, 8),
            "rain_ripple": (rain_ripple, 6, 12), "tilt_up": (tilt_up, 6, 8), "cloud_break": (cloud_break, 28, 24), "sonic_boom": (sonic_boom, 14, 18), "zip17": (zip17, 6, 8), "cloud_shadow": (cloud_shadow, 8, 10), "sun_open": (sun_open, 8, 10), "sun_whip": (sun_whip, 5, 6),
            "balloon_rise": (balloon_rise, 6, 8), "light_streak": (light_streak, 5, 7), "throw_whip": (throw_whip, 5, 7),
            "light_leak17": (light_leak17, 6, 8), "spin_roll": (spin_roll, 6, 10), "blue_bloom": (blue_bloom, 10, 12), "punch_cut": (punch_cut, 0, 1),
            "emblem_ignite": (emblem_ignite, 62, 40), "cube_turn": (cube_turn, 6, 10), "peel17": (peel17, 8, 10), "lightning_strike": (lightning_strike, 8, 14), "bolt_window": (bolt_window, 8, 12), "horizon_slide": (horizon_slide, 5, 7), "bokeh_rack": (bokeh_rack, 8, 10),
            "glare_wash": (glare_wash, 6, 8), "hide_peek": (hide_peek, 8, 8), "smear17": (smear17, 5, 6), "split_slide": (split_slide, 6, 8),
            "loop17": (loop17, 0, 1)})

# ---- the frame ----------------------------------------------------------------------------------------------------------
def suit_red(img, person, s, f):
    """the Blitzkrieg pack's suit reads tan; give it back the suit's red: his matte, its tan and grey, cowl included; never
    the skin of his lower face, the white emblem with its bolt, or the gold lightning on his ears."""
    B_, G_, R_ = img[..., 0], img[..., 1], img[..., 2]
    L = B_ * 0.114 + G_ * 0.587 + R_ * 0.299
    hue = (R_ - G_) / (R_ + 1e-3); rb = R_ - B_
    gate = np.clip((hue + 0.02) / 0.10, 0, 1) * np.clip((0.88 - L) / 0.16, 0, 1) * np.clip((0.42 - rb) / 0.10, 0, 1) * np.clip((rb + 0.04) / 0.06, 0, 1)
    m = gate * (1.0 if person is None else np.clip(person * 1.3, 0, 1))
    q = 4
    fs = face_scr(s, f) if s.get("face") is not None else None
    if fs:                                                                                     # the skin: his lower face only
        sk = np.zeros((H // q, W // q), F32)
        cv2.ellipse(sk, (int(fs[0] / q), int((fs[1] + 0.22 * fs[2]) / q)), (int(fs[2] * 0.50 / q), int(fs[2] * 0.50 / q)), 0, 0, 360, 1.0, -1)
        m = m * (1 - cv2.resize(cv2.GaussianBlur(sk, (0, 0), 2.0), (W, H)))
    m = cv2.GaussianBlur(m.astype(F32), (0, 0), 1.5)[..., None] * s.get("suitred", 1.0)
    rec = np.stack([B_ * 0.50, G_ * 0.34, np.clip(R_ * 0.98 + 0.02, 0, 1)], axis=2)
    return img * (1 - m) + rec * m

def base17(s, f):
    img, person = base11(s, f)
    if s.get("suitred"): img = suit_red(img, person, s, f)
    if s.get("anim") in ANIMS: img = ANIMS[s["anim"]](img, person, s, f)
    n = s["n"]
    if n == "sun": img = sun_fx(img, person, s, f)
    elif n == "last": img = loop_fx(img, person, s, f)
    return img, person

PERSON = {}
def prefinish(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base17(s, f)
    PERSON.clear(); PERSON[f] = person
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge15(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge15(n_, "first"), kn, f, s, n_)
    return np.clip(out, 0, 1)

def render(f):
    s = shot_at(f); out = flash_governor(beat_fx(prefinish(f), f))
    f0 = fh(E.E_LOOP); mix = smoother(clamp(((f - f0) / (E.DUR_F - f0) - 0.40) / 0.60, 0, 1)) if (s["n"] == "last" and f >= f0) else None
    return (np.clip(finish17(out, f, s, mix), 0, 1) * 255 + 0.5).astype(np.uint8)



# ============================================================================ v18 — CREEP (The Flash × Radiohead "Creep")
# I WISH I WAS SPECIAL. Before the lightning Barry is an ordinary man in a cold, colourless world, and the only colour in
# it is the speedster's: a gold streak, a red suit. THE HOOK (frame 0): a gold streak tears past behind Barry on a night
# street and back across in front of him: the future Flash, running back in time. THE STRIKE (crunch 1): the lightning
# hits him and the colour floods out of it into the world along veins of current (COLOUR STRIKE). Crunch 2: he wakes on a
# heartbeat ring. THE DROP ("creep"): current climbs the frame and he is the Flash; the chorus in full colour. "What the
# hell am I doing here": the real emblem's bolt lifts off and flies at the lens, the Speed Force inside it (EMBLEM BOLT).
# THE TIME TEAR (the loop): he runs back in time and his lightning tears the frame open onto frame 0, where the streak
# behind Barry is him: the end causes the start.
GOLD18 = np.array([0.22, 0.68, 1.00], F32)                 # BGR electric gold
AMBER18 = np.array([0.10, 0.42, 1.00], F32)                # BGR amber (the lightning's heart)
COLDB = np.array([0.86, 0.74, 0.62], F32)                  # BGR the ordinary world's slate light
SFB = np.array([1.00, 0.82, 0.55], F32)                    # BGR Speed Force blue
if E.VER == "v18":
    for _s in E.SHOTS:
        _s.setdefault("target", 0.40 if _s.get("look") == "cold" else 0.44)
LOOKS17["colour"] = dict(sh=(0.024, 0.012, -0.012), hi=(-0.036, 0.006, 0.042), sat=1.10, skyk=0.10)
LOOKS17["cold"] = LOOKS17["colour"]; LOOKS17["strike"] = LOOKS17["colour"]
LOOKS17["force"] = dict(sh=(0.034, 0.014, -0.010), hi=(0.012, 0.008, 0.010), sat=1.06, skyk=0.45)

def fs3_of(s, f):
    """(x, y, size) of the face on screen, or the shot's hint, or None."""
    fs = face_scr(s, f) if s.get("face") is not None else None
    if fs: return fs[0], fs[1], fs[2]
    return s.get("face_hint")

# ---- ORDINARY: the cold look (from the colour grade, in screen space, so a transition can mix the two) ------------------
def red_mask(img):
    B_, G_, R_ = img[..., 0], img[..., 1], img[..., 2]
    hue = (R_ - G_) / (R_ + 1e-3)
    return (np.clip((hue - 0.52) / 0.14, 0, 1) * np.clip((R_ - np.maximum(G_, B_) - 0.10) / 0.12, 0, 1)).astype(F32)

def coldify(img, keep=None):
    """the ordinary world: the colour drained to a cold slate (a trace of it left), flatter blacks lifted toward blue;
    `keep` (0..1 per pixel) keeps the colour (the speedster's red)."""
    B_, G_, R_ = img[..., 0], img[..., 1], img[..., 2]
    L = B_ * 0.114 + G_ * 0.587 + R_ * 0.299
    sat = 0.16 if keep is None else 0.16 + 0.88 * keep
    sh = (1 - L) ** 2.0; hi = np.clip((L - 0.6) / 0.4, 0, 1)
    Lc = 0.022 + L * 0.94
    o = np.empty(img.shape, F32)
    for c, (Pc, ts, th_) in enumerate(zip((B_, G_, R_), (0.052, 0.018, -0.016), (0.020, 0.010, -0.008))):
        o[..., c] = Lc + (Pc - L) * sat + sh * ts + hi * th_
    return np.clip(o, 0, 1, out=o)

# ---- COLOUR STRIKE (crunch 1, e28 -> e32): the colour floods out of the lightning, along veins of current ---------------
_VEIN = {}
def vein_tex():
    """a fixed ridged fractal (H/4, W/4) in 0..1: thin bright ridges, the veins of the front."""
    if "t" not in _VEIN:
        rng = np.random.default_rng(1818); h, w = H // 4, W // 4; acc = np.zeros((h, w), F32)
        for sig, a_ in ((40, 1.0), (16, 0.6), (6, 0.35), (2.2, 0.18)):
            n = cv2.GaussianBlur(rng.standard_normal((h, w)).astype(F32), (0, 0), sig, borderType=cv2.BORDER_REFLECT)
            acc += a_ * n / (n.std() + 1e-6)
        acc = (acc - acc.min()) / (acc.max() - acc.min())
        _VEIN["t"] = acc; _VEIN["r"] = (1 - np.abs(2 * acc - 1)) ** 6                         # ridges
    return _VEIN["t"], _VEIN["r"]

def strike_mix(s, f, img):
    """(the colour's share M, the glowing veins at its front), full resolution."""
    e = e_of(f); q = 4
    sm = cv2.resize(img, (W // q, H // q), interpolation=cv2.INTER_AREA)
    L = lumf(sm); lit = np.clip((L - 0.55) / 0.25, 0, 1) * np.clip((sm[..., 2] - sm[..., 0] - 0.20) / 0.20, 0, 1)
    fs = fs3_of(s, f); cx, cy = (fs[0], fs[1] + fs[2] * 1.7) if fs else (W * 0.5, H * 0.55)
    d = np.sqrt((_GXQ - cx) ** 2 + (_GYQ - cy) ** 2)
    N, rid = vein_tex()
    g = smooth(clamp((e - E.E_STRIKE - 0.15) / 3.4, 0, 1))
    R = 2600 * g ** 1.25
    dd = d - (N - 0.5) * 420                                                                   # a branching, uneven front
    front = np.clip((R - dd) / 60 + 0.5, 0, 1)
    seed = cv2.GaussianBlur(lit, (0, 0), 3) * smooth(clamp((e - E.E_STRIKE) / 0.4, 0, 1))
    M = np.maximum(front, np.clip(seed * 1.6, 0, 1))
    fm = face_soft(s, f, 1.5, q)                                                               # it reaches his face as one soft wash, never a line across it
    if fm is not None:
        fq = cv2.resize(fm[..., 0], (W // q, H // q)); M = M * (1 - fq) + cv2.GaussianBlur(M, (0, 0), 40) * fq
    veins = np.exp(-((dd - R) / 70.0) ** 2) * (0.25 + 1.6 * rid) * (1 - smooth(clamp((g - 0.85) / 0.15, 0, 1))) * (g > 0)
    return (cv2.resize(M.astype(F32), (W, H), interpolation=cv2.INTER_LINEAR),
            cv2.resize(veins.astype(F32), (W, H), interpolation=cv2.INTER_LINEAR))

def colour_strike(img, person, s, f):
    M, veins = strike_mix(s, f, img)
    o = coldify(img) * (1 - M[..., None]) + img * M[..., None]
    addc(o, kmul(veins, face_keep(s, f, 0.9)), GOLD18 * 0.7 + HOT * 0.3, 0.9)
    return np.clip(o, 0, 1)

# ---- the beat camera: gentle in the verse, a punch on every beat in the chorus, resting for the loop --------------------
def cam_amp(e):
    if e < 1.0: return 0.0                                                                     # frame 0 stays clean for the loop
    if e < E.E_STRIKE: return 0.30
    if e < E.E_DROP: return 0.45
    if e < E.E_REST: return 1.0
    return 0.0

def beat_bounce(f):
    e = e_of(f); a = cam_amp(e)
    if a <= 0: return 1.0
    eb = beat_e(e); dt = (e - eb) * E.HB
    amp = (0.036 if eb % 8 == 0 else (0.022 if eb % 4 == 0 else 0.014)) * a
    return 1 + amp * math.exp(-dt / 0.080)

def beat_fx(out, f):
    e = e_of(f)
    if cam_amp(e) < 1.0: return out
    eb = beat_e(e); dt = (e - eb) * E.HB
    if eb % 4 != 0 or dt > 0.05: return out
    k = math.exp(-dt / 0.020)
    o = radial_blur(out, W / 2, H * 0.46, 1.0, 1.0 + 0.026 * k, 4)
    return np.clip(rgb_split(o, 4 * k) if eb % 8 == 0 else o, 0, 1)

# ---- THE TIME STREAK (the hero): the speedster's gold streak, its crackle, its afterglow, the embers it sheds -----------
def hook_pt(tau, fs):
    """the streak's head at time tau (s from frame 0) and whether it runs behind him. A: right -> left behind him at chest
    height; off frame it turns; B: back in front of him low, at his waist, curving up the open side and out of the top."""
    fx, fy, fw = fs
    yb = fy + fw * 0.10; yf = min(fy + fw * 3.9, H * 0.90)
    side = clamp(fx + fw * 2.0, W * 0.60, W - 80)
    if tau <= 0.36:
        u = (tau + 0.16) / 0.52
        return W + 260 - (W + 520) * u, yb + 90 * math.sin(math.pi * u) - 50 * u, True
    if tau <= 0.46:
        return -260.0, yb + (yf - yb) * (tau - 0.36) / 0.10, True
    u = clamp((tau - 0.46) / 0.66, 0, 1); u = u * u * (1.6 - 0.6 * u) if u < 1 else 1.0
    p0, p1, p2 = (-260.0, yf), (side + 140, yf + 40), (side - 40, -320.0)
    x, y = bez(p0, p1, p2, u); return x, y, False

HOOK_T = (-0.16, 1.12)
def streak_draw(s, f, person, img):
    """THE TIME STREAK, drawn into a frame of the street shot (f may be negative: the loop's virtual frames)."""
    tau = f / FPS; fi = int(math.floor(f))
    if tau < HOOK_T[0] - 0.02 or tau > HOOK_T[1] + 1.6: return img
    fs = fs3_of(s, f) or (W * 0.5, H * 0.40, 300.0)
    cvb, cvf = bolt_canvas(), bolt_canvas(); glb = np.zeros((H // 4, W // 4), F32); glf = np.zeros_like(glb)
    def seg(cv, gl, a, b, val, wid, glow):
        cv2.line(cv, (int(a[0] * 16), int(a[1] * 16)), (int(b[0] * 16), int(b[1] * 16)), int(val), wid, cv2.LINE_AA, shift=4)
        cv2.line(gl, (int(a[0] * 4), int(a[1] * 4)), (int(b[0] * 4), int(b[1] * 4)), float(glow), max(1, wid // 2), cv2.LINE_AA, shift=4)
    ts = np.linspace(tau - 0.95, tau, 96)
    pts = [hook_pt(clamp(t_, *HOOK_T), fs) for t_ in ts]
    for i in range(1, len(ts)):
        if ts[i] < HOOK_T[0] or ts[i - 1] > HOOK_T[1]: continue
        age = tau - ts[i]
        a, b = pts[i - 1], pts[i]
        if abs(b[0] - a[0]) + abs(b[1] - a[1]) < 0.5: continue
        if age < 0.28:                                                                         # the streak
            v = 255 * (1 - age / 0.28) ** 1.2; wid = int(4 + 18 * (1 - age / 0.28))
            seg(cvb if b[2] else cvf, glb if b[2] else glf, a, b, v, wid, 0.0)
        g_ = 0.55 * (1 - clamp(age / 0.95, 0, 1)) ** 2                                         # the ionised air it leaves
        seg(cvb if b[2] else cvf, glb if b[2] else glf, a, b, 0, 9, g_)
    hx, hy, hbeh = hook_pt(clamp(tau, *HOOK_T), fs)
    live = HOOK_T[0] <= tau <= HOOK_T[1]
    if live:                                                                                   # crackle round the head
        for k in range(3):
            i = len(ts) - 3 - 4 * k - (fi % 3)
            if i < 1: break
            a = pts[i]; L_ = 90 + 40 * k
            put_bolt(cvb if hbeh else cvf, (a[0], a[1]), (hx + 0.6 * L_ * math.cos(fi * 0.9 + k * 2.1), hy + 0.6 * L_ * math.sin(fi * 1.3 + k)),
                     18800 + k + 7 * (fi // 2), 2, 0.34, 5, 1, val=200)
    rng = np.random.default_rng(1888)                                                          # the embers it sheds (analytic paths)
    for k in range(46):
        te = HOOK_T[0] + k * (HOOK_T[1] - HOOK_T[0]) / 46; age = tau - te
        if age <= 0 or age > 1.1: continue
        ex, ey, eb = hook_pt(te, fs)
        vx = rng.uniform(-260, 260); vy = rng.uniform(-300, 60); r0 = rng.uniform(1.6, 3.6)
        px = ex + vx * age; py = ey + vy * age + 520 * age * age
        br = (1 - age / 1.1) ** 1.5 * (0.6 + 0.4 * math.sin(age * 23 + k))
        cv2.circle(cvb if eb else cvf, (int(px * 16), int(py * 16)), int(r0 * 16), int(255 * br), -1, cv2.LINE_AA, shift=4)
    o = img.copy()
    pm = np.clip(person * 1.25, 0, 1)[..., None] if person is not None else 0.0
    wk = cv2.resize(cv2.GaussianBlur(glb + glf, (0, 0), 10), (W, H))                          # the air it tears through: the street smears in its wake
    wk = np.clip(wk * 3.0, 0, 1)[..., None] * (1 - pm)
    if wk.max() > 0.01: o = o * (1 - wk) + hblur(o, 90) * wk
    for cv, gl, behind in ((cvb, glb, True), (cvf, glf, False)):
        if cv.max() == 0 and gl.max() == 0: continue
        lt = light_rgb(cv, 1.8, HOT, GOLD18)
        gw = cv2.resize(cv2.GaussianBlur(gl, (0, 0), 3) * 1.3 + cv2.GaussianBlur(gl, (0, 0), 12) * 2.0, (W, H))[..., None] * (GOLD18 * 0.8 + HOT * 0.2)
        lay = lt + gw
        if behind: o = o + kmul(lay * (1 - pm), face_keep(s, f, 0.9))
        else: o = o + kmul(lay, face_keep(s, f, 1.15))
    if live:                                                                                   # its light: on the street behind him, a rim on his edge
        d = np.sqrt((_GX - hx) ** 2 + (_GY - hy) ** 2)
        wash = np.exp(-(d / 420.0) ** 2).astype(F32)
        if person is not None:
            rim = np.clip(person - cv2.erode(person, np.ones((9, 9), np.uint8)), 0, 1) * np.exp(-(d / 700.0) ** 2)
            o = o + kmul((wash * 0.20 * (1 - pm[..., 0]))[..., None] * GOLD18, face_keep(s, f, 1.0)) + kmul((rim * 0.9).astype(F32), face_keep(s, f, 1.25))[..., None] * GOLD18
        else:
            o = o + (wash * 0.20)[..., None] * GOLD18
    return np.clip(o, 0, 1)

def a_hook(img, person, s, f):
    return streak_draw(s, f, person, img)

# ---- in-shot animations ---------------------------------------------------------------------------------------------------
def a_breath(img, person, s, f):
    """COLD AIR: a slow cold haze drifts low across the dusk behind him."""
    t = f / FPS; N = cv2.resize(cloud_N(t, 70.0, 300.0), (W, H))
    m = (np.clip((N - 0.45) / 0.35, 0, 1) * np.clip((_GY - H * 0.45) / (H * 0.4), 0, 1) * 0.32).astype(F32)
    if person is not None: m = m * (1 - np.clip(person * 1.3, 0, 1))
    return np.clip(img * (1 - m[..., None] * 0.4) + m[..., None] * COLDB * 0.55, 0, 1)

def a_lampdust(img, person, s, f):
    """LAMP DUST: dust turning slowly in the lamp's cone, catching its light (cold world: a pale light)."""
    if "lp" not in _MOT:
        rng = np.random.default_rng(1881)
        _MOT["lp"] = (rng.uniform(0, W, 70), rng.uniform(0, H * 0.75, 70), rng.uniform(2.5, 6.0, 70), rng.uniform(0, 6.28, 70), rng.uniform(-10, 10, 70), rng.uniform(-14, 6, 70))
    X0, Y0, rad, ph, vx, vy = _MOT["lp"]; t = (f - s["f0"]) / FPS
    if _HO.get("ld_n") != s["n"]: _HO["ld_n"] = s["n"]; _HO["ld"] = hi_point(base11(s, s["f0"])[0], s, s["f0"], 0.62)
    lx, ly = _HO["ld"]
    X = (X0 + vx * t + 7 * np.sin(0.8 * t + ph)) % W; Y = (Y0 + vy * t + 5 * np.cos(0.6 * t + ph)) % H
    cone = np.exp(-(((X - lx) / 300.0) ** 2 + ((Y - ly - 260) / 520.0) ** 2))
    br = (0.3 + 0.7 * (0.5 + 0.5 * np.sin(2.1 * t + ph * 3))) * (0.15 + 0.85 * cone)
    cv = np.zeros((H // 2, W // 2), np.uint8)
    for x_, y_, r_, b_ in zip(X, Y, rad, br):
        cv2.circle(cv, (int(x_ * 8), int(y_ * 8)), int(r_ * 8), int(255 * b_), -1, cv2.LINE_AA, shift=4)
    m = cv2.resize(cv.astype(F32) / 255, (W, H)); m = m * 0.8 + cv2.GaussianBlur(m, (0, 0), 5) * 1.4
    if person is not None: m = m * (1 - 0.7 * np.clip(person, 0, 1))
    o = img.copy(); addc(o, kmul(m.astype(F32), face_keep(s, f, 1.1)), COLDB * 0.5 + HOT * 0.5, 0.8)
    return np.clip(o, 0, 1)

_GL = {}
def a_gustleaves(img, person, s, f):
    """THE GUST: the wind the Flash left behind carries leaves and grit across behind her, blurred by their speed."""
    if "p" not in _GL:
        rng = np.random.default_rng(1882)
        _GL["p"] = (rng.uniform(-W, W, 40), rng.uniform(H * 0.15, H * 0.95, 40), rng.uniform(5, 13, 40), rng.uniform(900, 1700, 40), rng.uniform(0, 6.28, 40))
    X0, Y0, rad, sp, ph = _GL["p"]; t = (f - s["f0"]) / FPS
    k = math.exp(-t / 0.9)
    cv = np.zeros((H // 2, W // 2), F32)
    for x0, y0, r_, v_, p_ in zip(X0, Y0, rad, sp, ph):
        x_ = x0 + v_ * (t + 0.25); y_ = y0 + 40 * math.sin(3 * t + p_) - 60 * t
        if -60 < x_ < W + 60:
            cv2.ellipse(cv, (int(x_ * 8), int(y_ * 8)), (int(r_ * 8), int(r_ * 4)), math.degrees(p_ + 2 * t), 0, 360, 1.0, -1, cv2.LINE_AA, shift=4)
    m = cv2.resize(cv2.GaussianBlur(cv, (0, 0), sigmaX=10, sigmaY=1.0), (W, H)) * k
    if person is not None: m = m * (1 - np.clip(person * 1.3, 0, 1))
    m = kmul(m.astype(F32), face_keep(s, f, 1.2))
    return np.clip(img * (1 - 0.55 * m[..., None]) + m[..., None] * COLDB * 0.18, 0, 1)

def a_stormlight(img, person, s, f):
    """THE STORM OUTSIDE: lightning flickers through the window onto him from above; from e25 it builds (the strike)."""
    e = e_of(f); fl = 0.0
    for eh, a_ in ((24.0, 0.35), (25.6, 0.45), (26.5, 0.55), (27.15, 0.70), (27.6, 0.85)):
        dt = (e - eh) * E.HB
        if dt >= 0: fl += a_ * (math.exp(-dt / 0.05) + 0.5 * math.exp(-((dt - 0.11) / 0.03) ** 2))
    if fl < 0.01: return img
    g = np.clip(1.15 - _GY / (H * 1.05), 0, 1)[..., None] * (0.7 + 0.3 * np.clip(_GX / W, 0, 1))[..., None]
    o = img * (1 + 0.42 * fl * g) + (fl * 0.06) * g * (COLDB * 0.6 + HOT * 0.4)
    return np.clip(o, 0, 1)

_EMB = {}
def a_embers(img, person, s, f):
    """EMBERS: sparks from the lightning round him rise past, out of focus, off his face."""
    if "p" not in _EMB:
        rng = np.random.default_rng(1883)
        _EMB["p"] = (rng.uniform(0, W, 60), rng.uniform(0, H, 60), rng.uniform(2.0, 5.5, 60), rng.uniform(-60, 60, 60), rng.uniform(-420, -160, 60), rng.uniform(0, 6.28, 60))
    X0, Y0, rad, vx, vy, ph = _EMB["p"]; t = (f - s["f0"]) / FPS
    X = (X0 + vx * t + 20 * np.sin(4 * t + ph)) % W; Y = (Y0 + vy * t) % (H + 200) - 100
    cv = np.zeros((H // 2, W // 2), np.uint8)
    for x_, y_, r_, p_ in zip(X, Y, rad, ph):
        cv2.circle(cv, (int(x_ * 8), int(y_ * 8)), int(r_ * 8), int(255 * (0.55 + 0.45 * math.sin(9 * t + p_ * 3) ** 2)), -1, cv2.LINE_AA, shift=4)
    m = cv2.resize(cv.astype(F32) / 255, (W, H)); m = cv2.GaussianBlur(m, (0, 0), sigmaX=1.2, sigmaY=4) * 1.2 + cv2.GaussianBlur(m, (0, 0), 7) * 1.5
    o = img.copy(); addc(o, kmul(m.astype(F32), face_keep(s, f, 1.2)), AMBER18 * 0.6 + HOT * 0.4, 0.9)
    return np.clip(o, 0, 1)

def a_mist(img, person, s, f):
    """THE SPEED FORCE: its mist drifts behind him and lightning flickers inside it."""
    t = f / FPS; N = cv2.resize(cloud_N(t, -90.0, 700.0), (W, H))
    m = (np.clip((N - 0.40) / 0.40, 0, 1) * 0.30).astype(F32)
    pm = np.clip(person * 1.3, 0, 1) if person is not None else 0.0
    o = img + (m * (1 - pm))[..., None] * SFB * 0.35
    e = e_of(f)
    for k, eh in enumerate((64.6, 65.9, 66.8)):
        dt = (e - eh) * E.HB
        if 0 <= dt < 0.35:
            cv = bolt_canvas(); x0 = W * (0.80 if k % 2 == 0 else 0.15)
            put_bolt(cv, (x0, H * 0.10), (x0 + 120 * (1 - 2 * (k % 2)), H * 0.55), 18900 + k, 2, 0.32, 6, 2, val=int(255 * math.exp(-dt / 0.10)))
            lt = light_rgb(cv, 0.9, HOT, SFB * 0.6 + HOT * 0.4)
            o = o + kmul(lt, face_keep(s, f, 1.4)) * (1 - pm)[..., None] if person is not None else o + kmul(lt, face_keep(s, f, 1.4))
    return np.clip(o, 0, 1)

_BD = {}
def a_bokehdrift(img, person, s, f):
    """CITY LIGHTS: big soft bokeh drift behind her, slowly, warm."""
    if "p" not in _BD:
        rng = np.random.default_rng(1884)
        _BD["p"] = (rng.uniform(0, W, 16), rng.uniform(0, H * 0.7, 16), rng.uniform(40, 110, 16), rng.uniform(-25, 25, 16), rng.uniform(0, 6.28, 16))
    X0, Y0, rad, vx, ph = _BD["p"]; t = (f - s["f0"]) / FPS
    cv = np.zeros((H // 4, W // 4), F32)
    for x0, y0, r_, v_, p_ in zip(X0, Y0, rad, vx, ph):
        x_ = (x0 + v_ * t) % W; y_ = y0 + 12 * math.sin(0.7 * t + p_)
        cv2.circle(cv, (int(x_ * 4), int(y_ * 4)), int(r_ * 4 / 4), 0.25 + 0.15 * math.sin(1.3 * t + p_), -1, cv2.LINE_AA, shift=2)
    m = cv2.resize(cv2.GaussianBlur(cv, (0, 0), 1.5), (W, H))
    if person is not None: m = m * (1 - np.clip(person * 1.3, 0, 1))
    o = img.copy(); addc(o, kmul(m.astype(F32), face_keep(s, f, 1.3)), AMBER18 * 0.5 + HOT * 0.5, 0.55)
    return np.clip(o, 0, 1)

ANIMS.update({"hook": a_hook, "breath": a_breath, "lampdust": a_lampdust, "gustleaves": a_gustleaves, "stormlight": a_stormlight,
              "glare": a_shine, "embers": a_embers, "mist": a_mist, "bokehdrift": a_bokehdrift})

# ---- transitions ------------------------------------------------------------------------------------------------------------
def _x(j, pre, post): return (j + pre) / (pre + post - 1)

def bokeh_bloom(A, B, j, f, sa, sb, pre=8, post=12):
    """BOKEH BLOOM (the street -> the dusk): the street's lights swell into big soft discs that rise, and the dusk racks
    into focus behind them."""
    x = _x(j, pre, post); k = math.sin(math.pi * clamp(x, 0, 1)); r = 34 * k ** 1.2
    w = smooth(clamp((x - 0.28) / 0.48, 0, 1))
    a = defocus16(shift_img(A, 0, -60 * smooth(x)), r); b = defocus16(B, r)
    o = a * (1 - w) + b * w
    hi = np.clip(cv2.resize(cv2.resize(A, (W // 8, H // 8), interpolation=cv2.INTER_AREA).max(2), (W, H)) - 0.55, 0, 1)
    addc(o, kmul((cv2.GaussianBlur(shift_img(hi[..., None].repeat(3, 2), 0, -160 * smooth(x))[..., 0], (0, 0), 22) * 1.5 * k).astype(F32), live_keep(sa, sb, j, f, w, 1.2)), COLDB * 0.6 + HOT * 0.4, 0.6)
    return np.clip(o, 0, 1)

def window_glow(A, B, j, f, sa, sb, pre=6, post=10):
    """WINDOW GLOW (the dusk -> the lab): the lab's window light blooms in from where it is and the lab comes up in it."""
    x = _x(j, pre, post); k = math.sin(math.pi * clamp(x, 0, 1))
    if _HO.get("wg_n") != sb["n"]: _HO["wg_n"] = sb["n"]; _HO["wg"] = hi_point(edge15(sb, "first"), sb, sb["f0"], 0.62)
    px, py = _HO["wg"]
    d = np.sqrt((_GX - px) ** 2 + (_GY - py) ** 2)
    R = math.hypot(W, H) * 1.1 * smooth(clamp((x - 0.1) / 0.8, 0, 1)) ** 1.3
    m = np.clip((R - d) / (160 + 0.7 * R) + 0.5, 0, 1).astype(F32)
    o = A * (1 - m[..., None]) + B * m[..., None]
    glow = np.exp(-(d / (300 + 900 * k)) ** 2).astype(F32)
    addc(o, kmul(glow, live_keep(sa, sb, j, f, smooth(x), 1.2)), COLDB * 0.5 + HOT * 0.5, 0.45 * k)
    return np.clip(o, 0, 1)

def lamp_on(A, B, j, f, sa, sb, pre=6, post=14):
    """LAMP ON (the lab -> by the lamp): the light goes down, and the lamp in the next shot clicks on, flickers once, and
    its light fills the room."""
    if j < 0:
        u = (j + pre + 1) / pre; return np.clip(A * (1 - 0.45 * smooth(u)), 0, 1)
    v = (j + 1) / post
    if _HO.get("lo_n") != sb["n"]: _HO["lo_n"] = sb["n"]; _HO["lo"] = hi_point(B, sb, sb["f0"], 0.62)
    px, py = _HO["lo"]
    lvl = 0.55 + 0.45 * smooth(clamp(v / 0.75, 0, 1))
    if 0.18 < v < 0.30: lvl *= 0.80                                                            # the flicker
    d = np.sqrt((_GX - px) ** 2 + (_GY - py) ** 2)
    pool = np.exp(-(d / (260 + 520 * v)) ** 2).astype(F32)                                     # its light reaches out
    o = B * (lvl * (0.75 + 0.25 * pool[..., None]) + (1 - lvl) * pool[..., None] * 0.6)
    addc(o, kmul(np.exp(-(d / 90.0) ** 2).astype(F32), live_keep(sa, sb, j, f, 1, 1.2)), HOT * 0.5 + COLDB * 0.5, 0.5 * (1 - v))
    return np.clip(o, 0, 1)

def eyeline_whip(A, B, j, f, sa, sb, pre=5, post=7):
    """EYELINE WHIP: he looks at her; the camera whips along his look onto her."""
    return np.clip(strip_pan(A, B, _x(j, pre, post), 1, rev=True, blur=190), 0, 1)

def wind_gust(A, B, j, f, sa, sb, pre=6, post=10):
    """WIND GUST (Iris -> her hair blowing): the wind of something passing too fast to see sweeps across the frame; the
    picture streaks in it, and her hair is flying when it has gone."""
    x = _x(j, pre, post); k = math.sin(math.pi * clamp(x, 0, 1))
    pos = -0.3 * W + 1.6 * W * smooth(clamp(x, 0, 1))
    band = np.exp(-((_GX - pos) / 300.0) ** 2).astype(F32)
    m = np.clip((pos - _GX) / 160 + 0.5, 0, 1).astype(F32)
    o = A * (1 - m[..., None]) + B * m[..., None]
    sm = hblur(o, 2 + 220 * k)
    o = o * (1 - band[..., None]) + sm * band[..., None]
    gl = (np.exp(-((_GX - pos) / 40.0) ** 2) * np.exp(-((_GY - H * 0.62) / 60.0) ** 2)).astype(F32)   # a glint of gold in it
    addc(o, kmul(gl, live_keep(sa, sb, j, f, smooth(x), 1.3)), GOLD18, 0.35 * k)
    return np.clip(o, 0, 1)

def hair_whip(A, B, j, f, sa, sb, pre=5, post=7):
    """HAIR WHIP (her hair -> the masked Flash): her hair whips across the lens, out of focus, and it is the Flash behind it."""
    q = _x(j, pre, post); k = math.sin(math.pi * clamp(q, 0, 1))
    o = strip_pan(A, B, q, 1, rev=False, blur=200)
    return np.clip(rgb_split(o, 5 * k), 0, 1)

def colour_drain(A, B, j, f, sa, sb, pre=10, post=10):
    """COLOUR DRAIN (the Flash -> Barry alone): the suit's red, the one colour in the frame, drains down out of it like
    liquid, and he is Barry again, in the dark."""
    x = _x(j, pre, post)
    if j < 0:
        u = (j + pre + 1) / pre
        N = cv2.resize(cloud_N(0.0, 0.0, 1200.0), (W, H))
        front = -0.15 * H + 1.35 * H * smooth(u) + (N - 0.5) * 260
        m = np.clip((front - _GY) / 50 + 0.5, 0, 1).astype(F32)
        o = A * (1 - m[..., None]) + coldify(A) * m[..., None]
        drip = (np.exp(-((_GY - front) / 26.0) ** 2) * red_mask(A)).astype(F32)
        addc(o, drip, np.array([0.12, 0.10, 0.80], F32), 0.5)
        return np.clip(o, 0, 1)
    v = (j + 1) / post
    a = cv2.warpAffine(coldify(A), np.float32([[1, 0, 0], [0, 1, H * 0.35 * smooth(v)]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    b = cv2.warpAffine(B, np.float32([[1, 0, 0], [0, 1, -H * 0.10 * (1 - smooth(v))]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    w = smooth(clamp(v / 0.8, 0, 1))
    return np.clip(hblur(a * (1 - w) + b * w, 2 + 90 * math.sin(math.pi * v), vertical=True), 0, 1)

_SC = {}
def crack_canvas(amt, y_end=None, x0=None):
    x0 = W * 0.80 if x0 is None else x0
    cv = bolt_canvas(); pts = bolt_points((x0 + 60.0, -60.0), (x0 - 80.0, H * 0.78), 18610, 0.18, 7)
    if y_end is not None: pts = pts[pts[:, 1] <= y_end]
    if len(pts) > 1:
        cv2.polylines(cv, [pts.astype(np.int32)], False, int(255 * amt), 10, cv2.LINE_AA)
        for b in range(5):
            i = 4 + b * max(1, (len(pts) - 8) // 5)
            if i >= len(pts) - 1: break
            q0 = pts[i]; ang = math.pi / 2 + (0.8 if b % 2 else -0.9) * (0.5 + 0.1 * b)
            q1 = (q0[0] + 260 * math.cos(ang), q0[1] + 260 * math.sin(ang))
            cv2.polylines(cv, [bolt_points(tuple(q0), q1, 18650 + b, 0.30, 5).astype(np.int32)], False, int(200 * amt), 3, cv2.LINE_AA)
    return cv

def sky_crack(A, B, j, f, sa, sb, pre=10, post=14):
    """SKY CRACK (crunch 1): leaders creep down the side of the dark frame, the bolt strikes on the crunch beside him and
    the strike burns in outward from its channel."""
    x = _x(j, pre, post); xs = pre / (pre + post - 1)
    if "d" not in _SC:
        q = 4; cq = cv2.resize(crack_canvas(1.0), (W // q, H // q), interpolation=cv2.INTER_AREA)
        _SC["d"] = cv2.resize((cv2.distanceTransform((cq < 40).astype(np.uint8), cv2.DIST_L2, 5) * q).astype(F32), (W, H))
    fk = live_keep(sa, sb, j, f, 0 if j < 0 else 1, 0.95)
    if x < xs:
        cv = crack_canvas(0.45, y_end=H * (0.06 + 0.70 * x / xs))
        return np.clip(A * (1 - 0.30 * x / xs) + kmul(light_rgb(cv, 0.8, HOT, COLDB * 0.5 + HOT * 0.5), fk), 0, 1)
    y = x - xs; b = math.exp(-y / 0.10) + 0.6 * math.exp(-((y - 0.22) / 0.04) ** 2)
    R = 50 + W * 2.0 * eout(clamp(y / 0.32, 0, 1), 1.6)
    m = np.clip((R - _SC["d"]) / (40 + 0.25 * R) + 0.5, 0, 1).astype(F32)
    o = A * 0.7 * (1 - m[..., None]) + B * m[..., None]
    o = o * (1 + 0.28 * b)
    lt = light_rgb(crack_canvas(1.0), 1.6 * b + 0.3 * (1 - smooth(clamp(y / 0.7, 0, 1))), HOT, GOLD18 * 0.6 + HOT * 0.4)
    return np.clip(o + kmul(lt, fk), 0, 1)

def heartstart(A, B, j, f, sa, sb, pre=4, post=18):
    """HEARTSTART (crunch 2): the strike's light peaks; he gasps awake on a heartbeat: a ring of pressure runs out from his
    chest, bending the picture as it passes."""
    if j < 0:
        u = (j + pre + 1) / pre; return np.clip(A * (1 + 0.25 * u) + 0.04 * u * (GOLD18 * 0.5 + HOT * 0.5), 0, 1)
    v = (j + 1) / post
    fs = fs3_of(sb, sb["f0"]); cx, cy = (fs[0], fs[1] + fs[2] * 1.9) if fs else (W * 0.5, H * 0.66)
    d = np.sqrt((_GX - cx) ** 2 + (_GY - cy) ** 2).astype(F32); ang = np.arctan2(_GY - cy, _GX - cx)
    R = 30 + math.hypot(W, H) * 0.70 * eout(v, 2.0); wid = 30 + 80 * v
    band = np.exp(-((d - R) / wid) ** 2).astype(F32)
    disp = band * 28 * (1 - v)
    Bz = zoom_about(B, cx, cy, 1.0 + 0.10 * (1 - eout(v, 2.5)))
    o = cv2.remap(Bz, (_GX + np.cos(ang) * disp).astype(F32), (_GY + np.sin(ang) * disp).astype(F32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    addc(o, kmul((band * (1 - v) ** 1.2).astype(F32), live_keep(sa, sb, j, f, 1.0, 1.1)), GOLD18 * 0.5 + HOT * 0.5, 0.35)
    return np.clip(o * (1 + 0.12 * math.exp(-v * 6)), 0, 1)

def current_climb(A, B, j, f, sa, sb, pre=26, post=30):
    """CURRENT CLIMB (THE DROP, "creep"): a front of current climbs the frame from his feet; under it he is the Flash. It
    creeps up through "I'm a", reaches his chest on the drop, then races up out of the frame; sparks fly off it."""
    t = f / FPS
    if j < 0: u = (j + pre + 1) / pre; y = H * (1.04 - 0.40 * ein(u, 1.6))                    # creeping up to his chest by the drop
    else: v = (j + 1) / post; y = H * 0.64 - (H * 0.64 + 160) * eout(v, 1.8)
    N = cv2.resize(cloud_N(t * 3, 0.0, 300.0), (W, H)); yy = y + (N - 0.5) * 120
    m = np.clip((_GY - yy) / 30 + 0.5, 0, 1).astype(F32)
    if j >= 0:                                                                                 # the drop: a punch in
        k = math.exp(-((j + 1) / post) * 5); Bz = zoom_about(B, W / 2, H * 0.5, 1.0 + 0.10 * k)
        if k > 0.3: Bz = rgb_split(Bz, 6 * k)
    else: Bz = B
    o = A * (1 - m[..., None]) + Bz * m[..., None]
    above = np.clip((yy - _GY) / 220, 0, 1).astype(F32)                                        # its light on the picture still above it
    glow = (np.exp(-((_GY - yy) / 60.0) ** 2) + 0.35 * np.exp(-((_GY - yy) / 240.0) ** 2) * (1 - above)).astype(F32)
    cv = bolt_canvas()
    for k_ in range(5):
        xa = -60 + (W + 120) * k_ / 5; xb = xa + (W + 120) / 5
        put_bolt(cv, (xa, y + 30 * math.sin(f * 0.7 + k_)), (xb, y + 30 * math.sin(f * 0.9 + k_ + 1)), 18700 + k_ + 11 * (f // 2), 3, 0.30, 6, 1, val=235)
    rng = np.random.default_rng(1887 + f // 2)
    for k_ in range(26):
        sx = rng.uniform(0, W); L_ = rng.uniform(40, 160); a_ = -math.pi / 2 + rng.uniform(-0.6, 0.6)
        cv2.line(cv, (int(sx), int(y)), (int(sx + L_ * math.cos(a_)), int(y + L_ * math.sin(a_))), int(rng.uniform(120, 230)), 2, cv2.LINE_AA)
    fk = live_keep(sa, sb, j, f, 0 if j < 0 else 1, 1.05)
    lt = light_rgb(cv, 1.15, HOT, GOLD18)
    o = o + kmul(lt, fk)
    addc(o, kmul(glow, fk), GOLD18 * 0.7 + HOT * 0.3, 0.55)
    return np.clip(o, 0, 1)

def lightbar_streak(A, B, j, f, sa, sb, pre=5, post=7):
    """LIGHT BAR STREAK: the bar of light behind him stretches into a streak across the lens, and the run is in it."""
    q = _x(j, pre, post); k = math.sin(math.pi * clamp(q, 0, 1))
    if _HO.get("lb_n") != sa["n"]: _HO["lb_n"] = sa["n"]; _HO["lb"] = hi_point(edge15(sa, "last"), sa, sa["f1"] - 1, 0.62)
    px, py = _HO["lb"]
    o = strip_pan(A, B, q, 1, rev=True, blur=220)
    st = (np.exp(-((_GY - py) / (8 + 14 * k)) ** 2) * np.exp(-np.abs(_GX - px) / (300 + 1400 * k))).astype(F32)
    addc(o, kmul(st, live_keep(sa, sb, j, f, smooth(q), 1.15)), np.array([1.0, 0.85, 0.6], F32), 0.9 * k)
    return np.clip(o, 0, 1)

def spark_jump(A, B, j, f, sa, sb, pre=5, post=8):
    """SPARK JUMP: a spark leaps from the runner's lightning to the next shot's chest, and the cut is on its strike."""
    if _HO.get("sj_n") != sa["n"]: _HO["sj_n"] = sa["n"]; _HO["sj"] = hi_point(edge15(sa, "last"), sa, sa["f1"] - 1, 0.62)
    p0 = _HO["sj"]; fs = fs3_of(sb, sb["f0"]); p1 = (fs[0] + fs[2] * 0.3, fs[1] + fs[2] * 2.3) if fs else (W * 0.5, H * 0.66)
    cv = bolt_canvas()
    if j < 0:
        u = (j + pre + 1) / pre; tip = (p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u)
        put_bolt(cv, p0, tip, 18750 + f // 2, 3, 0.30, 6, 1, val=255)
        return np.clip(A + kmul(light_rgb(cv, 1.1, HOT, GOLD18), live_keep(sa, sb, j, f, 0, 1.05)), 0, 1)
    v = (j + 1) / post
    put_bolt(cv, p0, p1, 18760 + f // 2, 3, 0.30, 6, 2, val=int(255 * (1 - v)))
    o = zoom_about(B, p1[0], p1[1], 1 + 0.08 * (1 - eout(v, 2)))
    return np.clip(o * (1 + 0.15 * math.exp(-v * 6)) + kmul(light_rgb(cv, 1.2, HOT, GOLD18), live_keep(sa, sb, j, f, 1, 1.05)), 0, 1)

def arc_sweep(A, B, j, f, sa, sb, pre=6, post=8):
    """ARC SWEEP: an arm of lightning swings across the frame from the floor like a clock hand; the next shot is behind it.
    It passes his face fast and as one soft edge."""
    x = _x(j, pre, post); px, py = W * 0.5, H * 1.10
    ang = math.pi * (1.02 - 1.04 * smoother(clamp(x, 0, 1)))                                    # from the left to the right
    ca, sa_ = math.cos(ang), math.sin(ang)
    side = (_GX - px) * (-sa_) + (py - _GY) * ca                                               # signed distance from the arm
    m = np.clip(side / 90 + 0.5, 0, 1).astype(F32)
    o = A * m[..., None] + B * (1 - m[..., None])
    cv = bolt_canvas(); L_ = math.hypot(W, H) * 1.2
    put_bolt(cv, (px, py), (px + L_ * ca, py - L_ * sa_), 18780 + f // 2, 3, 0.10, 7, 2, val=int(255 * math.sin(math.pi * clamp(x, 0, 1))))
    return np.clip(o + kmul(light_rgb(cv, 1.0, HOT, GOLD18), live_keep(sa, sb, j, f, smooth(x), 1.2)), 0, 1)

def streak_carry(A, B, j, f, sa, sb, pre=6, post=8):
    """STREAK CARRY: he leaves the loft as a streak; the camera whips after it and the streak rides the seam into the
    next shot."""
    q = _x(j, pre, post); o = strip_pan(A, B, q, 1, rev=True, blur=200)
    seam = (1 - smooth(clamp(q, 0, 1))) * W; k = math.sin(math.pi * clamp(q, 0, 1))
    st = (np.exp(-((_GY - H * 0.58) / 10.0) ** 2) * np.exp(-np.abs(_GX - seam) / 380.0) + 0.4 * np.exp(-((_GY - H * 0.58) / 90.0) ** 2) * np.exp(-np.abs(_GX - seam) / 200.0)).astype(F32)
    addc(o, kmul(st, live_keep(sa, sb, j, f, smooth(q), 1.2)), AMBER18 * 0.6 + HOT * 0.4, 0.95 * k)
    return np.clip(o, 0, 1)

def glint_star(A, B, j, f, sa, sb, pre=6, post=8):
    """GLINT STAR: the sun catches the brightest edge in the frame (off his face), it flares into a star and the next shot
    is behind the flare."""
    x = _x(j, pre, post); k = math.sin(math.pi * clamp(x, 0, 1)) ** 1.2
    if _HO.get("gs_n") != sa["n"]: _HO["gs_n"] = sa["n"]; _HO["gs"] = hi_point(edge15(sa, "last"), sa, sa["f1"] - 1, 0.66)
    px, py = _HO["gs"]
    w = smooth(clamp((x - 0.28) / 0.44, 0, 1)); o = A * (1 - w) + B * w
    st = star_glint(px, py, 120 + 700 * k, 1.0, rot=0.35 + 0.4 * x)
    addc(o, kmul(st, live_keep(sa, sb, j, f, w, 1.2)), GOLD18 * 0.5 + HOT * 0.5, 0.8 * k)
    return np.clip(o, 0, 1)

def flicker_cut(A, B, j, f, sa, sb, pre=6, post=8):
    """FLICKER CUT: the corridor's tube light stutters, and when it comes back it is the next shot, lit by lightning."""
    if j < 0:
        u = (j + pre + 1) / pre; lv = 1.0 - 0.35 * (math.sin(u * math.pi * 3) ** 2) * u
        return np.clip(A * lv, 0, 1)
    v = (j + 1) / post; lv = 0.65 + 0.35 * smooth(clamp(v / 0.5, 0, 1))
    if 0.30 < v < 0.42: lv *= 0.85
    return np.clip(B * lv, 0, 1)

def mist_pass(A, B, j, f, sa, sb, pre=10, post=12):
    """MIST PASS: the Speed Force's mist rolls across the lens, and she is there as it thins."""
    x = _x(j, pre, post); k = math.sin(math.pi * clamp(x, 0, 1))
    N = cv2.resize(cloud_N(f / FPS, -260.0, 1500.0), (W, H))
    pos = 1.4 * W - 1.9 * W * smooth(clamp(x, 0, 1))
    cover = np.exp(-((_GX - pos) / 520.0) ** 2).astype(F32)
    dens = np.clip((N - 0.65 + 0.9 * cover * k) / 0.30, 0, 1).astype(F32) * 0.60
    w = smooth(clamp((x - 0.35) / 0.30, 0, 1)); base = defocus16(A, 10 * k) * (1 - w) + defocus16(B, 10 * k) * w
    return np.clip(base * (1 - dens[..., None]) + dens[..., None] * (SFB * 0.55 + HOT * 0.25), 0, 1)

def lamp_bloom(A, B, j, f, sa, sb, pre=8, post=10):
    """LAMP BLOOM: the street lamp behind her blooms gold and opens onto the run through time."""
    x = _x(j, pre, post); k = math.sin(math.pi * clamp(x, 0, 1))
    if _HO.get("lm_n") != sa["n"]: _HO["lm_n"] = sa["n"]; _HO["lm"] = hi_point(edge15(sa, "last"), sa, sa["f1"] - 1, 0.62)
    sx, sy = _HO["lm"]
    d = np.sqrt((_GX - sx) ** 2 + (_GY - sy) ** 2).astype(F32)
    R = math.hypot(W, H) * 1.1 * smooth(clamp((x - 0.12) / 0.80, 0, 1)) ** 1.25
    m = np.clip((R - d) / (30 + 0.14 * R) + 0.5, 0, 1).astype(F32)
    base = A * (1 - m[..., None]) + B * m[..., None]
    o = base + cv2.GaussianBlur(np.clip(base - 0.45, 0, 1), (0, 0), 24) * 1.2 * k * (GOLD18 * 0.5 + 0.5)
    rim = np.exp(-((d - R) / (24 + 0.06 * R)) ** 2).astype(F32)
    addc(o, kmul(rim, live_keep(sa, sb, j, f, smooth(x), 1.2)), GOLD18 * 0.6 + HOT * 0.4, 0.7 * k)
    return np.clip(o, 0, 1)

def lightning_whip(A, B, j, f, sa, sb, pre=5, post=7):
    """LIGHTNING WHIP: the camera whips with him, a bolt of his lightning on the seam."""
    q = _x(j, pre, post); p = smooth(clamp(q, 0, 1)); sp = math.sin(math.pi * clamp(q, 0, 1))
    o = strip_pan(A, B, q, 1, rev=True, blur=220, ov=360)
    seam = W * (1 - p); cv = bolt_canvas()
    for k in range(2):
        put_bolt(cv, (seam + 20 * k, -40), (seam - 30 + 40 * k, H + 40), 18790 + k + 3 * (f // 2), 4 - k, 0.12, 7, 2, val=int(255 * sp))
    return np.clip(o + kmul(light_rgb(cv, 1.1, HOT, GOLD18), live_keep(sa, sb, j, f, p, 1.1)), 0, 1)

# ---- EMBLEM BOLT (the signature, e61.5 -> e66): the real emblem's bolt lifts off the disc, spins, and flies at the lens;
#      the Speed Force is inside it --------------------------------------------------------------------------------------
_EB = {}
EMB_BOLT18 = np.array([(0.621, -1.192), (0.322, -0.390), (0.034, -0.258), (-0.243, 0.280), (0.062, 0.271), (-0.229, 0.449), (-0.689, 0.972),
                       (-0.469, 0.520), (-0.638, 0.486), (-0.299, 0.328), (-0.158, -0.068), (-0.441, -0.023), (-0.017, -0.215)], np.float32)
EMB_BOLT18 = np.stack([(EMB_BOLT18[:, 0] + 0.09) / 0.75, (EMB_BOLT18[:, 1] + 0.06) / 0.86], 1).astype(np.float32)
# the S4 emblem's bolt, traced by hand on flash_b_hq 83.2 s (checked on 82.6 and 83.7 s), in units of the white disc's
# half-width (x) and half-height (y) from the disc's centre: two left-pointing steps, tips past the rim at both ends.
EB_K = 100.0
def emb_bolt_field():
    """the bolt as a smooth field at 4x of a canonical size (EB_K px per unit), its 0.5 level the outline; the anchor (its
    fattest point) and the field's origin."""
    if "f" not in _EB:
        P = EMB_BOLT18 * EB_K; x0, y0 = P.min(0) - 20; x1, y1 = P.max(0) + 20
        Wf, Hf = int((x1 - x0) * 4), int((y1 - y0) * 4)
        up = np.zeros((Hf, Wf), F32); cv2.fillPoly(up, [((P - (x0, y0)) * 4 * 16).astype(np.int32)], 1.0, cv2.LINE_AA, shift=4)
        up = cv2.GaussianBlur(up, (0, 0), 2.0)
        dt = cv2.distanceTransform((up > 0.5).astype(np.uint8), cv2.DIST_L2, 5)
        ay, ax = np.unravel_index(int(np.argmax(dt)), dt.shape)
        _EB["f"] = (up, (ax / 4.0 + x0, ay / 4.0 + y0), (x0, y0))
    return _EB["f"]

def emb_disc(img, gx, gy, gr, key):
    """the real white disc of the emblem near a guess: (centre x, y, half-width, half-height) on screen."""
    if key in _EB: return _EB[key]
    if len(_EB) > 40: _EB.clear()
    R = int(gr * 1.5); x0, y0 = int(gx) - R, int(gy) - R
    x0c, y0c = max(0, x0), max(0, y0); x1c, y1c = min(W, x0 + 2 * R), min(H, y0 + 2 * R)
    c = img[y0c:y1c, x0c:x1c]
    L = lumf(c); sat = c.max(2) - c.min(2)
    wm = ((L > 0.55) & (sat < 0.16)).astype(np.uint8)
    n_, lab, st_, cen = cv2.connectedComponentsWithStats(wm, 8)
    keep = [i for i in range(1, n_) if st_[i, cv2.CC_STAT_AREA] > 0.04 * gr * gr]
    if not keep:
        r_ = (gx, gy, gr * 0.75, gr * 0.86)
    else:
        m = np.isin(lab, keep); ys, xs = np.nonzero(m)
        xa, xb = np.percentile(xs, [1, 99]); ya, yb = np.percentile(ys, [1, 99])
        r_ = (x0c + (xa + xb) / 2, y0c + (ya + yb) / 2, (xb - xa) / 2 * 1.14 + 2, (yb - ya) / 2 * 1.14 + 2)   # the white is inside the gold rim
    _EB[key] = r_
    return r_

def emblem_bolt(A, B, j, f, sa, sb, pre=50, post=34):
    """EMBLEM BOLT: the real chest emblem charges; its bolt (traced on the source, placed on the real disc found in every
    frame) lifts off the disc, spins once on the open side, turns face-on and flies at the lens; through it is the Speed
    Force, and it opens until there is nothing else. The socket it leaves is filled from the disc round it."""
    ff = f if j < 0 else sa["f1"] - 1
    gx, gy, gr = emb_pt(sa, ff)
    u = clamp((j + pre + 1) / pre, 0, 1); v = clamp((j + 1) / post, 0, 1) if j >= 0 else 0.0
    dcx0, dcy0, _, _ = emb_disc(A, gx, gy, gr, ("d0", ff))
    z = 1 + 0.14 * smooth(clamp(u / 0.4, 0, 1))
    px_, py_ = dcx0 + (W * 0.5 - dcx0) * 0.25 * smooth(clamp(u / 0.4, 0, 1)), dcy0 + (H * 0.60 - dcy0) * 0.25 * smooth(clamp(u / 0.4, 0, 1))
    Mz = np.float32([[z, 0, px_ - z * dcx0], [0, z, py_ - z * dcy0]])
    Az = cv2.warpAffine(A, Mz, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    EX, EY, HX, HY = emb_disc(Az, px_, py_, gr * z, ("dz", ff, round(z, 4)))
    up, (axp, ayp), (fx0, fy0) = emb_bolt_field()
    kx, ky = HX / EB_K, HY / EB_K
    fs = fs3_of(sa, ff); side = -1 if (fs and fs[0] > W * 0.5) else 1
    lift = smooth(clamp((u - 0.28) / 0.34, 0, 1))
    fly = 0.35 + 0.65 * ein(v, 1.3) if j >= 0 else 0.35 * ein(clamp((u - 0.60) / 0.40, 0, 1), 1.4)
    def warp_field(sx_, sy_, cx_, cy_):                                                        # the canonical point (axp, ayp) lands on (cx_, cy_)
        M = np.float32([[sx_ / 4, 0, cx_ - sx_ * (axp - fx0) - sx_ * fx0 + sx_ * fx0], [0, sy_ / 4, cy_ - sy_ * (ayp - fy0)]])
        M[0, 2] = cx_ - sx_ * (axp - fx0)
        return cv2.warpAffine(up, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    hx0, hy0 = EX + axp * kx, EY + ayp * ky                                                    # where the anchor sits on the disc
    o = Az
    if lift > 0.002:                                                                           # the socket it leaves, filled from the disc
        hole = np.clip((warp_field(kx, ky, hx0, hy0) - 0.2) * 4, 0, 1).astype(F32)
        hole = cv2.GaussianBlur(cv2.dilate(hole, np.ones((21, 21), np.uint8)), (0, 0), 2.5)
        key = ("fill", ff, round(z, 4))
        if key not in _EB:
            Rr = int(max(HX, HY) * 1.6); x0, y0 = int(EX) - Rr, int(EY) - Rr
            x0c, y0c, x1c, y1c = max(0, x0), max(0, y0), min(W, x0 + 2 * Rr), min(H, y0 + 2 * Rr)
            c8 = (np.clip(Az[y0c:y1c, x0c:x1c], 0, 1) * 255).astype(np.uint8)
            m8 = (hole[y0c:y1c, x0c:x1c] > 0.05).astype(np.uint8) * 255
            fl = cv2.inpaint(c8, m8, 5, cv2.INPAINT_TELEA).astype(F32) / 255
            cc = Az[y0c:y1c, x0c:x1c]; Lc = lumf(cc); satc = cc.max(2) - cc.min(2)
            wsel = (Lc > 0.55) & (satc < 0.16) & (m8 == 0)
            wcol = np.median(cc[wsel], axis=0) if wsel.any() else np.array([0.85, 0.86, 0.88], F32)
            yy_, xx_ = np.mgrid[y0c:y1c, x0c:x1c].astype(F32)
            de = np.sqrt(((xx_ - EX) / (HX * 0.86)) ** 2 + ((yy_ - EY) / (HY * 0.86)) ** 2)
            disc = np.clip((1.0 - de) / 0.04 + 0.5, 0, 1)[..., None]
            shade = (1.0 - 0.10 * np.clip((yy_ - EY) / HY, -1, 1) - 0.05 * np.clip((xx_ - EX) / HX, -1, 1))[..., None]   # the disc's own soft light
            fl = fl * (1 - disc) + (wcol * shade) * disc
            full = Az.copy(); full[y0c:y1c, x0c:x1c] = fl; _EB[key] = full
        k_ = hole[..., None] * smooth(clamp(lift / 0.12, 0, 1))
        o = o * (1 - k_) + _EB[key] * k_
    lx = hx0 + side * W * 0.24 * lift; ly = hy0 - H * 0.10 * lift
    tx, ty = W * 0.5, H * 0.74
    cxp = lx + (tx - lx) * smooth(clamp(fly / 0.5, 0, 1)); cyp = ly + (ty - ly) * smooth(clamp(fly / 0.5, 0, 1))
    phi = 2 * math.pi * smooth(clamp((u - 0.30) / 0.30, 0, 1)); sxs = max(abs(math.cos(phi)), 0.06)
    S = (1.0 + 0.5 * lift) * math.exp(math.log(70.0) * ein(clamp(fly, 0, 1), 1.8))
    fw_ = warp_field(kx * S * sxs, ky * S, cxp, cyp)
    kk = 7.0 * max(1.0, S / 3.0)
    m = np.clip((fw_ - 0.5) * kk + 0.5, 0, 1).astype(F32)
    if j >= 0: m = np.maximum(m, smooth(clamp((v - 0.80) / 0.20, 0, 1)))
    fmk = face_soft(sa, ff, 1.3)                                                               # it passes his face as one soft edge
    if fmk is not None and fly > 0.2: m = m * (1 - fmk[..., 0]) + cv2.GaussianBlur(m, (0, 0), 30) * fmk[..., 0]
    t = f / FPS
    if lift > 0.002 or j >= 0:
        Bz = zoom_about(B, cxp, cyp, 1.0 + 0.30 * (1 - smooth(fly)))
        inside = 1.0 if fly > 0.15 else smooth(fly / 0.15)
        gx_ = cv2.Sobel(fw_, cv2.CV_32F, 1, 0, ksize=3); gy_ = cv2.Sobel(fw_, cv2.CV_32F, 0, 1, ksize=3)
        sh_ = np.clip(0.62 + (-gx_ * 0.8 - gy_ * 0.9) * (4.0 / max(S, 1.0)) * math.cos(phi), 0.15, 1.4)[..., None]   # a bevel lit from the top left
        metal = np.array([0.10, 0.34, 0.55], F32) * (1 - np.clip(sh_ - 0.4, 0, 1)) + np.array([0.55, 0.86, 1.00], F32) * np.clip(sh_ - 0.4, 0, 1)
        spr = Bz * inside + metal * (1 + 0.5 * lift) * (1 - inside)                            # the gold bolt, then a window
        o = o * (1 - m[..., None]) + spr * m[..., None]
        edge = np.clip(1 - np.abs(fw_ - 0.5) * kk * 0.5, 0, 1).astype(F32)                     # its outline, alive with current
        fk = live_keep(sa, sb, j, f, 0 if j < 0 else 1, 1.1)
        addc(o, kmul(cv2.GaussianBlur(edge, (0, 0), 2 + 6 * fly), fk), GOLD18 * 0.6 + HOT * 0.4, 1.2 * (1 - smooth(clamp((v - 0.6) / 0.4, 0, 1))))
    else:
        chg = smooth(clamp(u / 0.25, 0, 1))
        addc(o, (np.clip((fw_ - 0.5) * 6 + 0.5, 0, 1) * 0.55 * chg * (0.75 + 0.25 * math.sin(t * 30))).astype(F32), GOLD18, 1.0)
    cv = bolt_canvas()                                                                          # current: round the rim, then a tether
    ER = max(HX, HY) * 1.12
    if u < 0.62:
        a_amt = smooth(clamp(u / 0.2, 0, 1))
        for k in range(3):
            a0 = 0.7 + 2.1 * k + 5.0 * t
            put_bolt(cv, (EX + HX * 1.1 * math.cos(a0), EY + HY * 1.1 * math.sin(a0)), (EX + HX * 1.1 * math.cos(a0 + 1.2), EY + HY * 1.1 * math.sin(a0 + 1.2)), 18820 + k + 7 * (f // 2), 2, 0.30, 4, 0, val=int(230 * a_amt))
    tet = math.sin(math.pi * clamp((lift - 0.05) / 0.6, 0, 1)) * (1 - smooth(fly / 0.3))
    if tet > 0.02 and math.hypot(cxp - EX, cyp - EY) > ER:
        put_bolt(cv, (EX, EY), (cxp, cyp), 18830 + 5 * (f // 2), 2, 0.25, 5, 1, val=int(230 * tet))
    if cv.max() > 0:
        o = o + kmul(light_rgb(cv, 1.0, HOT, GOLD18), live_keep(sa, sb, j, f, 0, 0.75))
    return np.clip(o, 0, 1)

# ---- THE TIME TEAR (the loop, e76 -> frame 0): he runs back in time; his lightning tears the frame open along a bolt, and
#      inside the tear is frame 0's street, where the streak behind Barry is him. It opens until it is frame 0 ------------
_TT = {}
def tear_profile():
    if "p" not in _TT:
        pts = bolt_points((-80.0, H * 0.54), (W + 80.0, H * 0.58), 18900, 0.10, 7)
        xs = np.arange(W, dtype=F32); yc = np.interp(xs, pts[:, 0], pts[:, 1]).astype(F32)
        rng = np.random.default_rng(1890); n1 = cv2.GaussianBlur(rng.standard_normal((1, W)).astype(F32), (0, 0), 36)[0]; n2 = cv2.GaussianBlur(rng.standard_normal((1, W)).astype(F32), (0, 0), 36)[0]
        _TT["p"] = (yc, n1 / (np.abs(n1).max() + 1e-6), n2 / (np.abs(n2).max() + 1e-6))
    return _TT["p"]

def loop_fx18(img, person, s, f):
    f0 = fh(E.E_LOOP); N = E.DUR_F - f0
    if f < f0: return img
    t = (f - f0) / N; tt = f / FPS
    o = img
    cv = bolt_canvas(); chg = smooth(clamp(t / 0.30, 0, 1))                                    # 1. the lightning builds and runs back
    for k in range(4):
        y_ = H * (0.62 + 0.07 * k) + 30 * math.sin(tt * 7 + k)
        put_bolt(cv, (W * (1.05 - 0.15 * k), y_), (W * (0.15 - 0.25 * chg), y_ + 40 * math.sin(k * 2.3)), 18950 + k + 7 * (f // 2), 3, 0.22, 6, 2, val=int(255 * (0.35 + 0.65 * chg)))
    o = hblur(o, 2 + 60 * chg)
    T = smoother(clamp((t - 0.28) / 0.72, 0, 1))                                              # 2. the tear opens
    if T <= 0:
        return np.clip(o + light_rgb(cv, 1.0, HOT, GOLD18), 0, 1)
    V = frame_virtual(f - E.DUR_F + (0.5 if f == E.DUR_F - 1 else 0.0))
    yc, n1, n2 = tear_profile()
    h = 2.7 * H * T ** 3.5
    top = (yc - h / 2 * (1 + 0.12 * n1))[None, :]; bot = (yc + h / 2 * (1 + 0.12 * n2))[None, :]
    inside = (np.clip((_GY - top) / 6 + 0.5, 0, 1) * np.clip((bot - _GY) / 6 + 0.5, 0, 1)).astype(F32)
    pa = h * 0.30                                                                              # the halves are pushed apart
    up_ = cv2.warpAffine(o, np.float32([[1, 0, 0], [0, 1, -pa]]), (W, H), borderMode=cv2.BORDER_REPLICATE)
    dn_ = cv2.warpAffine(o, np.float32([[1, 0, 0], [0, 1, pa]]), (W, H), borderMode=cv2.BORDER_REPLICATE)
    outside = np.where((_GY < yc[None, :])[..., None], up_, dn_)
    Vz = zoom_about(V, W / 2, H * 0.56, 1.0 + 0.10 * (1 - T) ** 2)
    o = outside * (1 - inside[..., None]) + Vz * inside[..., None]
    edge = (np.exp(-((_GY - top) / 9.0) ** 2) + np.exp(-((_GY - bot) / 9.0) ** 2)).astype(F32)
    glow = (np.exp(-((_GY - top) / 50.0) ** 2) + np.exp(-((_GY - bot) / 50.0) ** 2)).astype(F32)
    fade = 1 - smooth(clamp((t - 0.80) / 0.18, 0, 1))
    fm0 = face_soft(SHOTS[0], f - E.DUR_F, 1.2)                                                 # frame 0's face, inside the tear: no light crosses it
    fk0 = 1.0 if fm0 is None else (1 - fm0[..., 0] * inside)[..., None]
    addc(o, kmul((edge * fade).astype(F32), fk0), HOT * 0.6 + GOLD18 * 0.4, 1.1); addc(o, kmul((glow * fade).astype(F32), fk0), GOLD18, 0.45)
    cv2.polylines(cv, [np.stack([np.arange(0, W, 8), top[0, ::8]], 1).astype(np.int32)], False, int(200 * fade), 2, cv2.LINE_AA)
    cv2.polylines(cv, [np.stack([np.arange(0, W, 8), bot[0, ::8]], 1).astype(np.int32)], False, int(200 * fade), 2, cv2.LINE_AA)
    o = o + light_rgb(cv, 1.0, HOT, GOLD18) * (1 - inside[..., None])
    if t > 0.985: o = V
    return np.clip(o, 0, 1)

def loop18(A, B, j, f, sa, sb):
    return B

HERO_FN = streak_draw
TR2.update({"bokeh_bloom": (bokeh_bloom, 8, 12), "window_glow": (window_glow, 6, 10), "lamp_on": (lamp_on, 6, 14), "eyeline_whip": (eyeline_whip, 5, 7),
            "wind_gust": (wind_gust, 6, 10), "hair_whip": (hair_whip, 5, 7), "colour_drain": (colour_drain, 10, 10), "sky_crack": (sky_crack, 10, 14),
            "heartstart": (heartstart, 4, 18), "current_climb": (current_climb, 26, 30), "lightbar_streak": (lightbar_streak, 5, 7),
            "spark_jump": (spark_jump, 5, 8), "arc_sweep": (arc_sweep, 6, 8), "streak_carry": (streak_carry, 6, 8), "shades_glint": (glint_star, 6, 8),
            "flicker_cut": (flicker_cut, 6, 8), "mist_pass": (mist_pass, 10, 12), "lamp_bloom": (lamp_bloom, 8, 10), "lightning_whip": (lightning_whip, 5, 7),
            "emblem_bolt": (emblem_bolt, 50, 34), "loop18": (loop18, 0, 1)})

# ---- the frame --------------------------------------------------------------------------------------------------------------
def base18(s, f):
    img, person = base11(s, f)
    lk = s.get("look")
    if lk == "cold": img = coldify(img, red_mask(img) * s["keepred"] if s.get("keepred") else None)
    elif lk == "strike": img = colour_strike(img, person, s, f)
    if s.get("anim") in ANIMS: img = ANIMS[s["anim"]](img, person, s, f)
    if s["n"] == "timerun": img = loop_fx18(img, person, s, f)
    return img, person
base17 = base18

_FIN18 = {}
def finish18(out, f, s, mix=None):
    if "v" not in _FIN18:
        grain(0, 0.010); _FIN18["v"] = np.repeat(0.84 + 0.16 * VIG, 3, axis=2)
    k = ("g", f % 6)
    if k not in _FIN18: _FIN18[k] = np.repeat(grain(f, 0.010), 3, axis=2)
    lk = s.get("look")
    if mix is not None: m_ = mix
    elif lk == "cold": m_ = 1.0
    elif lk == "strike": m_ = 1 - smooth(clamp((e_of(f) - E.E_STRIKE - 0.15) / 3.4, 0, 1))
    else: m_ = 0.0
    o = out
    small = cv2.resize(o, (W // 4, H // 4), interpolation=cv2.INTER_AREA); mx = small.max(2)
    hi_ = np.clip(mx - 0.64, 0, 1)
    bl = cv2.resize(cv2.GaussianBlur(hi_, (0, 0), 5) * 0.5 + cv2.GaussianBlur(hi_, (0, 0), 18) * 0.5, (W, H))
    addc(o, bl, COLDB * m_ + (GOLD18 * 0.8 + HOT * 0.2) * (1 - m_), 0.22 * m_ + 0.34 * (1 - m_))
    o *= _FIN18["v"]; o += _FIN18[k]
    return np.clip(o, 0, 1, out=o)

def prefinish(f):
    s = shot_at(f); k = f - s["f0"]; n_ = nxt_of(s); kn = (f - n_["f0"]) if n_ else 999
    P = prev_shot(s); tin = s.get("tin")
    out, person = base18(s, f)
    PERSON.clear(); PERSON[f] = person
    if tin in TR2 and k < TR2[tin][2] and P is not None:
        out = TR2[tin][0](edge15(P, "last"), out, k, f, P, s)
    if n_ is not None:
        nt = n_.get("tin")
        if nt in TR2 and kn >= -TR2[nt][1]: out = TR2[nt][0](out, edge15(n_, "first"), kn, f, s, n_)
    return np.clip(out, 0, 1)

def render(f):
    s = shot_at(f); out = flash_governor(beat_fx(prefinish(f), f))
    f0 = fh(E.E_LOOP); mix = None
    if s["n"] == "timerun" and f >= f0: mix = 1.0 if f >= E.DUR_F - 2 else smoother(clamp(((f - f0) / (E.DUR_F - f0) - 0.28) / 0.72, 0, 1))
    return (np.clip(finish18(out, f, s, mix), 0, 1) * 255 + 0.5).astype(np.uint8)
