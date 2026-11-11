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
def cam_live(e): return 0 <= e < E.E_LOOP

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
def sun_draw(cx, cy, r, amt, rot=0.0, rays=1.0):
    """the sun as light (H, W, 3), drawn at quarter resolution: the disc, the glow, slowly turning rays."""
    dx = _GXQ - cx; dy = _GYQ - cy; d = np.sqrt(dx * dx + dy * dy)
    core = np.clip(1.25 - d / r, 0, 1) ** 1.4
    glow = np.exp(-(d / (r * 3.0)) ** 1.3) * 0.75 + np.exp(-(d / (r * 9.0)) ** 1.1) * 0.30
    ang = np.arctan2(dy, dx)
    ray = (0.5 + 0.5 * np.cos(ang * 12 + rot)) ** 10 * 0.65 + (0.5 + 0.5 * np.cos(ang * 7 - rot * 0.7 + 1.3)) ** 12 * 0.45
    ray = ray * np.exp(-d / (r * 6.5)) * np.clip(d / r - 0.8, 0, 1) * rays
    lay = core[..., None] * HOT * 1.5 + glow[..., None] * GOLD17 + ray[..., None] * (GOLD17 * 0.7 + HOT * 0.3)
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
        for sig, a_ in ((60, 1.0), (30, 0.62), (14, 0.30)):                                         # soft and puffy
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

def clouds(t, covmap, vx=90.0, lit=1.0, dark=0.0, tint=None, ox=0.0, soft=0.20):
    """clouds over the frame: (rgb, density) at full resolution. Density from a coverage map; the billows are shaded from
    the noise itself, lit from above right, darker in the bellies."""
    N = cloud_N(t, vx, ox)
    dens = np.clip((N - (0.80 - covmap)) / soft, 0, 1).astype(F32)
    Nb = cv2.GaussianBlur(N, (0, 0), 5.0)
    gy = cv2.Sobel(Nb, cv2.CV_32F, 0, 1, ksize=5) / 16; gx = cv2.Sobel(Nb, cv2.CV_32F, 1, 0, ksize=5) / 16
    shade = np.clip(0.55 + (Nb - 0.5) * 1.1 - gy * 9.0 + gx * 4.0, 0.15, 1.0) * lit * (1 - 0.55 * dark)
    hi = (np.array([0.97, 0.96, 0.94], F32) if tint is None else tint); lo = np.array([0.46, 0.47, 0.50], F32) * (1 - 0.5 * dark)
    rgb = shade[..., None] * hi + (1 - shade[..., None]) * lo
    return cv2.resize(rgb.astype(F32), (W, H), interpolation=cv2.INTER_LINEAR), cv2.resize(cv2.GaussianBlur(dens, (0, 0), 1.0), (W, H))

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
    e = e_of(f); g = smooth(clamp((e - 1.0) / 3.0, 0, 1))
    if g <= 0: return img
    sx, sy = W * 0.72, H * 0.20
    lay = sun_draw(sx, sy, 26 + 18 * g, 0.85 * g ** 1.4, rot=f * 0.02, rays=0.7)
    occ = cv2.GaussianBlur(np.clip((0.50 - lumf(img)) / 0.30, 0, 1), (0, 0), 6)               # the thick cloud in front of it
    return np.clip(img * (1 + 0.06 * g) + lay * (1 - 0.65 * occ)[..., None], 0, 1)

ANIMS = {"shine": a_shine, "rays": a_rays, "sunbreak": a_sunbreak}



# ---- helpers for the transitions ---------------------------------------------------------------------------------------
def live_keep(sa, sb, j, f, w, pad=1.25):
    """face_keep of whichever shot is on screen (its live frame, or its edge frame while it is held)."""
    if w < 0.5: return face_keep(sa, f if j < 0 else sa["f1"] - 1, pad)
    return face_keep(sb, f if j >= 0 else sb["f0"], pad)

def kmul(lay, k):
    return lay if isinstance(k, float) else lay * (k if lay.ndim == 3 else k[..., 0])

def strip_pan(A, B, q, axis, rev=False, blur=170):
    """A and B as one strip, panned (a whip): axis 0 vertical, 1 horizontal; rev puts B first."""
    p = smooth(clamp(q, 0, 1)); sp = math.sin(math.pi * clamp(q, 0, 1))
    if axis == 0:
        strip = np.concatenate([B, A] if rev else [A, B], axis=0); y0 = int(round((1 - p) * H)) if rev else int(round(p * H))
        return hblur(np.ascontiguousarray(strip[y0:y0 + H]), 2 + blur * sp, vertical=True)
    strip = np.concatenate([B, A] if rev else [A, B], axis=1); x0 = int(round((1 - p) * W)) if rev else int(round(p * W))
    return hblur(np.ascontiguousarray(strip[:, x0:x0 + W]), 2 + blur * sp)

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
    x = (j + pre) / (pre + post - 1); env = math.sin(math.pi * clamp(x, 0, 1))
    w = smooth(clamp((x - 0.40) / 0.20, 0, 1)); base = A * (1 - w) + B * w
    o = god_rays(base, PERSON.get(f), W * (-0.1 + 1.2 * smooth(x)), -H * 0.10, 1.4 * env, 0.42)
    return np.clip(o * (1 + 0.08 * env), 0, 1)

# ---- BLOOM CUT: the light blooms (the sun about to rise) and the next shot comes out of it -------------------------------
def bloom_cut(A, B, j, f, sa, sb, pre=8, post=10):
    x = (j + pre) / (pre + post - 1); k = math.sin(math.pi * clamp(x, 0, 1))
    w = smooth(clamp((x - 0.38) / 0.24, 0, 1)); base = A * (1 - w) + B * w
    hi = np.clip(base - 0.45, 0, 1)
    bl = cv2.GaussianBlur(hi, (0, 0), 24) * 1.5 + cv2.GaussianBlur(hi, (0, 0), 6) * 0.5
    return np.clip(base * (1 - 0.10 * k) + bl * k * (GOLD17 * 0.5 + 0.5), 0, 1)

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
        p_ = bolt_points((0.0, -40.0), (0.0, H + 40.0), 1771, 0.10, 6).astype(F32); p_[:, 1] = np.maximum.accumulate(p_[:, 1]) + np.arange(len(p_)) * 1e-3; _BC["p"] = p_
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
    x = (j + pre) / (pre + post - 1); pk = math.exp(-((x - 0.45) / 0.14) ** 2)
    w = smooth(clamp((x - 0.40) / 0.12, 0, 1)); o = A * (1 - w) + B * w
    cy = H * 0.36
    st = (np.exp(-((_GY - cy) / (5 + 10 * pk)) ** 2) + 0.4 * np.exp(-((_GY - cy) / 90.0) ** 2)).astype(F32)
    addc(o, kmul(st, live_keep(sa, sb, j, f, w, 1.2)), GOLD17 * 0.6 + HOT * 0.4, 1.3 * pk)
    return np.clip(o * (1 - 0.10 * pk), 0, 1)

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
        for k in range(5):
            a = ang - 18 * ein(u, 2) * k / 4; w_ = cv2.warpAffine(A, cv2.getRotationMatrix2D(c, a, 1 + 0.12 * u), (W, H), borderMode=cv2.BORDER_REFLECT)
            acc = w_ if acc is None else acc + w_
        return np.clip(acc / 5, 0, 1)
    v = (j + 1) / post; fb = face_scr(sb, f) if sb.get("face") is not None else None
    c = (fb[0], fb[1]) if fb else (W / 2, H / 2); ang = -180 * (1 - eout(v, 2.6))
    acc = None
    for k in range(5):
        a = ang * (1 + 0.10 * k / 4 * (1 - v)); w_ = cv2.warpAffine(B, cv2.getRotationMatrix2D(c, a, 1 + 0.12 * (1 - v)), (W, H), borderMode=cv2.BORDER_REFLECT)
        acc = w_ if acc is None else acc + w_
    return np.clip(acc / 5, 0, 1)

# ---- BLUE BLOOM (into the Speed Force): its blue light blooms out of the frame and he is inside it -----------------------
def blue_bloom(A, B, j, f, sa, sb, pre=10, post=12):
    x = (j + pre) / (pre + post - 1); k = math.sin(math.pi * clamp(x, 0, 1))
    w = smooth(clamp((x - 0.45) / 0.10, 0, 1)); base = A * (1 - w) + B * w                  # the swap under the peak
    pk = math.exp(-((x - 0.50) / 0.13) ** 2)
    hi = np.clip(base - 0.30, 0, 1)
    bl = cv2.GaussianBlur(hi, (0, 0), 30) * 1.8 + cv2.GaussianBlur(hi, (0, 0), 8) * 0.6
    d = np.sqrt(((_GX - W / 2) / W) ** 2 + ((_GY - H * 0.45) / H) ** 2).astype(F32)
    core = np.exp(-(d / (0.15 + 0.55 * k)) ** 2) * k
    o = base * (1 - 0.45 * pk) + bl * k * (SKYB * 0.7 + 0.3) + (SKYB * 0.55 + HOT * 0.10) * 0.45 * pk
    addc(o, core.astype(F32), SKYB * 0.6 + HOT * 0.4, 0.55)
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
    x = (j + pre) / (pre + post - 1); k = math.sin(math.pi * clamp(x, 0, 1))
    w = smooth(clamp((x - 0.40) / 0.20, 0, 1)); o = A * (1 - w) + B * w
    d = np.sqrt((_GX - W * 1.05) ** 2 + (_GY + H * 0.05) ** 2) / math.hypot(W, H)
    g = np.clip(1 - d / (0.25 + 0.75 * k), 0, 1).astype(F32) ** 1.6
    addc(o, kmul(g, live_keep(sa, sb, j, f, w, 1.2)), GOLD17 * 0.7 + HOT * 0.3, 0.75 * k)
    return np.clip(o * (1 - 0.08 * k), 0, 1)

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
        x0, x1 = k * W // 3, (k + 1) * W // 3; dy = int(round((H * 1.1) * p * (1 if k % 2 == 0 else -1) * (0.8 + 0.2 * k)))
        sl = np.roll(A[:, x0:x1], dy, axis=0)
        if dy > 0: sl[:dy] = B[:dy, x0:x1]
        elif dy < 0: sl[dy:] = B[dy:, x0:x1]
        o[:, x0:x1] = sl
    return np.clip(hblur(o, 2 + 140 * math.sin(math.pi * clamp(q, 0, 1)), vertical=True), 0, 1)

def punch_cut(A, B, j, f, sa, sb):
    return B



# ---- THE SUN (the focal piece, e32 -> e40): the sun rises behind him through his matte; its rays turn on every beat -------
def sun_path(e):
    u = clamp((e - E.E_SUN) / 8.0, 0, 1); p = smoother(u)
    return W * (0.98 - 0.04 * p), H * (0.58 - 0.16 * p), 44 + 26 * p, u                       # it rises from behind the hills

def sun_rot(e):
    """the rays turn a step on every beat (eased), and drift between."""
    eb = beat_e(e); n = (eb - E.E_SUN) / 2
    return 0.10 * (e - E.E_SUN) + 0.22 * (n + smooth(clamp((e - eb) * E.HB / 0.12, 0, 1)))

def sun_fx(img, person, s, f):
    e = e_of(f); sx, sy, r, u = sun_path(e)
    g = smooth(clamp((e - E.E_SUN) / 1.6, 0, 1))
    if g <= 0: return img
    pulse = math.exp(-((e - beat_e(e)) * E.HB) / 0.12)
    lay = sun_draw(sx, sy, r, g * (0.95 + 0.25 * pulse), sun_rot(e))
    pm = None if person is None else np.clip(person * 1.2, 0, 1)
    o = img * (1 - 0.05 * g)
    if pm is not None:
        o = o + lay * (1 - pm[..., None])                                                     # the sun is behind him
        rim = np.clip(pm - cv2.GaussianBlur(pm, (0, 0), 9), 0, 1) * 2.0                       # his edge catches it
        near = cv2.GaussianBlur(lumf(lay), (0, 0), 30)
        o = o + kmul((rim * np.clip(near * 3, 0, 1))[..., None] * GOLD17 * 0.9 * g, face_keep(s, f, 1.15))
    else: o = o + lay
    gh = ghosts_draw(sx, sy, g * (0.55 + 0.45 * smooth(clamp((e - 36) / 3, 0, 1))))
    return np.clip(o + kmul(gh, face_keep(s, f, 1.25)), 0, 1)

def ghost_iris(A, B, j, f, sa, sb, pre=30, post=26):
    """GHOST IRIS: one of the sun's lens ghosts swells into an iris; the next shot is inside it, and we go through."""
    x = (j + pre) / (pre + post - 1)
    sx, sy, r, _ = sun_path(e_of(sa["f1"] - 1)); gx, gy, gr, gcol, ga = ghost_pts(sx, sy)[1]
    G = smoother(clamp(x / 0.95, 0, 1)); D = math.hypot(W, H)
    R = gr * math.exp(math.log(D * 0.62 / gr) * G)
    cx, cy = gx + (W / 2 - gx) * G, gy + (H / 2 - gy) * G
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
def cloud_break(A, B, j, f, sa, sb, pre=40, post=24):
    t = f / FPS
    if j < 0:
        u = (j + pre + 1) / pre
        covmap = (1.05 * smooth(u) ** 1.6 - 0.50 + 0.70 * (_GXQ / W)).astype(F32)              # they roll in from the right
        rgb, dm = clouds(t, covmap, vx=-110.0, lit=0.95 - 0.30 * u, dark=0.55 * u)
        o = A * (1 - 0.22 * u)
        return np.clip(o * (1 - dm[..., None]) + rgb * dm[..., None], 0, 1)
    v = (j + 1) / post
    dist = np.sqrt(((_GXQ - W * 0.5) / W) ** 2 + ((_GYQ - H * 0.15) / H) ** 2 * 0.8) / 0.75
    covmap = (1.25 - 1.95 * eout(v, 2.0) + 0.9 * dist).astype(F32)                           # they part from the sun outward
    rgb, dm = clouds(t, covmap, vx=-110.0, lit=0.95 + 0.20 * (1 - v), dark=0.0)
    Bl = god_rays(B, PERSON.get(f), W * 0.5, H * 0.04, 1.1 * (1 - v) ** 0.7, 0.55)              # the sun behind him, through the gap
    rim = (dm * (1 - dm) * 4).astype(F32) * (1 - v)                                           # the silver lining
    o = Bl * (1 - dm[..., None]) + rgb * dm[..., None]
    addc(o, rim, HOT * 0.6 + GOLD17 * 0.4, 0.55)
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

def emblem_sun(A, B, j, f, sa, sb, pre=62, post=22):
    N = pre + post - 1; x = (j + pre) / N
    ff = f if j < 0 else sa["f1"] - 1
    ex, ey, er = emb_pt(sa, ff)
    u = clamp((j + pre + 1) / pre, 0, 1)
    z = 1 + 0.30 * smooth(u); px_ = ex + (W / 2 - ex) * 0.30 * smooth(u); py_ = ey + (H * 0.55 - ey) * 0.30 * smooth(u)
    Az = cv2.warpAffine(A, np.float32([[z, 0, px_ - z * ex], [0, z, py_ - z * ey]]), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    EX, EY, ER = px_, py_, er * z
    fm = face_soft(sa, ff, 1.25)                                                               # a wide, soft guard: the glow fades before his face
    if fm is None: fkA = 1.0
    else:
        fw_ = cv2.warpAffine(fm[..., 0], np.float32([[z, 0, px_ - z * ex], [0, z, py_ - z * ey]]), (W, H), borderMode=cv2.BORDER_REPLICATE)
        fkA = (1 - 0.92 * cv2.GaussianBlur(fw_, (0, 0), 70))[..., None]
    gl = math.exp(-((u - 0.17) / 0.07) ** 2)                                                  # 1. a glint runs round the rim
    a_ = 0.3 + 2.4 * clamp((u - 0.05) / 0.25, 0, 1)
    addc(Az, star_glint(EX + ER * math.cos(a_), EY - ER * math.sin(a_), ER * 1.6, gl), HOT, 1.2)
    lit = smooth(clamp((u - 0.25) / 0.30, 0, 1))                                               # 2. it lights from within
    d = np.sqrt((_GX - EX) ** 2 + (_GY - EY) ** 2)
    disc = np.clip((ER * 0.96 - d) / 3 + 0.5, 0, 1).astype(F32)
    ring = np.exp(-((d - ER) / (3 + 0.06 * ER)) ** 2).astype(F32)
    addc(Az, disc, GOLD17 * 0.55 + HOT * 0.45, 0.45 * lit); addc(Az, ring, GOLD17, 0.9 * lit)
    T = smooth(clamp((x - 0.64) / 0.36, 0, 1))                                                 # 4. the camera rises after it
    if T > 0:
        strip = np.concatenate([B, Az], axis=0); y0 = int(round((1 - T) * H))
        o = hblur(np.ascontiguousarray(strip[y0:y0 + H]), 2 + 150 * math.sin(math.pi * T), vertical=True)
    else: o = Az
    ray = smooth(clamp((u - 0.55) / 0.35, 0, 1)) * (1 - smooth(clamp((x - 0.80) / 0.20, 0, 1)))   # 3. it throws rays: the sun
    if ray > 0.002:
        sx = EX + (W * 0.76 - EX) * T ** 0.7; sy = EY + (H * 0.15 - EY) * T                      # it rises into the sky
        lay = sun_draw(sx, sy, ER * (0.55 + 0.30 * ray) * (1 - 0.35 * T), ray * 1.0, rot=0.4 * x * 6)
        if not isinstance(fkA, float): lay = lay * (fkA * (1 - T) + T)
        o = o + lay
    return np.clip(o, 0, 1)

# ---- CLOUD OVER (the loop, e136 -> frame 0): the clouds roll back over the sun and they are frame 0's storm ----------------
def loop_fx(img, person, s, f):
    f0 = fh(E.E_LOOP); N = E.DUR_F - f0
    if f < f0: return img
    t = (f - f0) / N; tt = f / FPS
    sx, sy = W * 0.74, H * 0.10
    sv = 1 - smooth(clamp((t - 0.12) / 0.45, 0, 1))                                           # the sun, hiding away
    o = img
    if sv > 0.002:
        lay = sun_draw(sx, sy, 44, 0.85 * sv * smooth(clamp(t / 0.12, 0, 1)), rot=0.6 * t)
        o = img + (lay if person is None else lay * (1 - np.clip(person * 1.2, 0, 1)[..., None]))
    cov = 1.00 * smooth(clamp((t - 0.06) / 0.55, 0, 1)) - 0.45
    covmap = (cov + 0.55 * (1 - _GYQ / H) + 0.25 * (_GXQ / W)).astype(F32)                    # they come over from the top right
    rgb, dm = clouds(tt, covmap, vx=-130.0, lit=1.0 - 0.40 * t, dark=0.65 * t)
    o = o * (1 - 0.30 * t) * (1 - dm[..., None]) + rgb * dm[..., None]
    wv = smooth(clamp((t - 0.30) / 0.66, 0, 1))                                                # the storm of frame 0 comes through them
    if wv > 0.002: o = o * (1 - wv) + frame_virtual(f - E.DUR_F) * wv
    return np.clip(o, 0, 1)

def loop17(A, B, j, f, sa, sb):
    return B

TR2.update({"sun_burst": (sun_burst, 12, 16), "run_by": (run_by, 5, 7), "speed_zoom": (speed_zoom, 4, 7), "glint_sweep": (glint_sweep, 6, 6),
            "sky_whip": (sky_whip, 5, 6), "flare_cut": (flare_cut, 6, 8), "ray_rake": (ray_rake, 8, 8), "bloom_cut": (bloom_cut, 8, 10),
            "ghost_iris": (ghost_iris, 30, 26), "prism": (prism, 6, 8), "whip_pan": (whip_pan, 5, 6), "bolt_crack": (bolt_crack, 4, 8),
            "rain_ripple": (rain_ripple, 6, 12), "tilt_up": (tilt_up, 6, 8), "cloud_break": (cloud_break, 40, 24), "sun_whip": (sun_whip, 5, 6),
            "balloon_rise": (balloon_rise, 6, 8), "light_streak": (light_streak, 5, 7), "throw_whip": (throw_whip, 5, 7),
            "light_leak17": (light_leak17, 6, 8), "spin_roll": (spin_roll, 6, 10), "blue_bloom": (blue_bloom, 10, 12), "punch_cut": (punch_cut, 0, 1),
            "emblem_sun": (emblem_sun, 62, 22), "horizon_slide": (horizon_slide, 5, 7), "bokeh_rack": (bokeh_rack, 8, 10),
            "glare_wash": (glare_wash, 6, 8), "hide_peek": (hide_peek, 8, 8), "smear17": (smear17, 5, 6), "split_slide": (split_slide, 6, 8),
            "loop17": (loop17, 0, 1)})

# ---- the frame ----------------------------------------------------------------------------------------------------------
def base17(s, f):
    img, person = base11(s, f)
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
    f0 = fh(E.E_LOOP); mix = smoother((f - f0) / (E.DUR_F - f0)) if (s["n"] == "last" and f >= f0) else None
    return (np.clip(finish17(out, f, s, mix), 0, 1) * 255 + 0.5).astype(np.uint8)

